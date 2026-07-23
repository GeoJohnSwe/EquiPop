# -*- coding: utf-8 -*-
"""
EquiPop.pyt - EquiPop for ArcGIS Pro. Python 3 / Pro only.

THE DISCIPLINE (same as the Stata bridge): this file is GLUE ONLY.
Every computation lives in the pip-installed `equipop` package, where
the automatic test suite guards it; the toolbox merely moves arrays
between ArcGIS and the package. The glue itself is validated against
a simulated arcpy before every release.

Install (once): ArcGIS Pro -> Package Manager -> clone the default
environment, activate the clone, then in its Python Command Prompt:
    pip install equipop
Add this .pyt to any project via Catalog -> Toolboxes -> Add Toolbox.
Full walk-through in ARCGIS_GUIDE.md next to this file.

Tools:
  1 Counts & Shares  - k / radius neighbourhoods, group shares,
                       decay; barriers (point/line/polygon/raster/
                       table) and DEM as DISTANCE INGREDIENTS
  2 Value Statistics - selectable statistics of numeric fields
                       among the k nearest PERSONS (full-population
                       aware)

v1.16 GIS INPUT REWORK: both machines share one loader. Spatial
inputs are read FROM GEOMETRY (no X/Y attribute columns needed,
ever); plain tables get guessed-but-overridable X and Y fields;
degree CRS refused loudly; line/polygon/raster barriers map to every
grid cell they genuinely touch. Results append to point layers as
row-aligned double fields (Null where coordinates are missing);
table inputs write a NEW output table.
"""

import numpy as np

import arcpy

_COORD_AUTO = "Auto (geometry if present)"
_COORD_GEOM = "Feature geometry"
_COORD_ATTR = "Attribute fields"
_COORD_CHOICES = [_COORD_AUTO, _COORD_GEOM, _COORD_ATTR]
_AGG_CHOICES = ["additive (sum)", "max", "min", "mean"]
_MEASURES = ["mean", "median", "gini", "sd", "variance", "se", "min",
             "max", "count", "sum", "range", "percentiles"]
_MEASURE_KEY = {"variance": "var"}


# ----------------------------------------------------------- shared glue
def _field(name):
    """ArcGIS-safe field name."""
    out = "".join(ch if ch.isalnum() else "_" for ch in str(name))
    return (out[:60] or "X")


def _agg_key(text):
    t = (text or "").strip().lower()
    return "sum" if (not t or t.startswith("additive")) else t


def _kind(desc):
    """point / line / polygon / raster / table - what did Pro hand
    us? (multipoint counts as point-like for barriers only)."""
    shp = str(getattr(desc, "shapeType", "") or "")
    if shp:
        return {"Point": "point", "Multipoint": "multipoint",
                "Polyline": "line", "Polygon": "polygon"}.get(
                    shp, shp.lower())
    if "raster" in str(getattr(desc, "dataType", "")).lower():
        return "raster"
    return "table"


def _check_metric(desc, what):
    """Degrees are refused LOUDLY - EquiPop distances are metres."""
    sr = getattr(desc, "spatialReference", None)
    if sr is not None and str(getattr(sr, "type", "")) == "Geographic":
        raise arcpy.ExecuteError(
            f"{what} is in a GEOGRAPHIC coordinate system "
            f"({getattr(sr, 'name', 'degrees')}) - EquiPop needs "
            "metres. Project it to a metric CRS (e.g. SWEREF 99 TM) "
            "and run again.")
    return sr


def _table_fields(value):
    return [f.name for f in arcpy.ListFields(value)]


def _resolve_xy_fields(value, xf, yf, context):
    """User choice first; package guess second; loud advice third.
    Never tells the user to rename columns."""
    from equipop.io import guess_xy_fields
    if xf and yf:
        return xf, yf, "chosen"
    gx, gy, deg = guess_xy_fields(_table_fields(value), context)
    if deg:
        raise arcpy.ExecuteError(
            f"{context}: '{gx}'/'{gy}' look like DEGREES (lon/lat) - "
            "EquiPop needs metres. Project the data to a metric CRS "
            "first.")
    if gx and gy:
        return gx, gy, "guessed"
    raise arcpy.ExecuteError(
        f"{context}: could not guess the coordinate columns among "
        f"{_table_fields(value)} - pick the X field (easting) and "
        "Y field (northing) in the dialog. No renaming needed.")


def _numeric(arr, field, context):
    a = np.asarray(arr, dtype=object)
    try:
        return np.asarray(arr, float)
    except (TypeError, ValueError):
        pass
    out = np.full(len(a), np.nan)
    bad = 0
    for i, v in enumerate(a):
        try:
            out[i] = float(v)
        except (TypeError, ValueError):
            bad += 1
    if bad == len(a):
        raise arcpy.ExecuteError(
            f"{context}: field '{field}' is not numeric - pick a "
            "numeric field.")
    return out


def _read_input(layer, coord_source, xf, yf, extra_fields, messages,
                context="input"):
    """THE SHARED LOADER (v1.16): one behaviour for both machines.
    Returns (kind, data dict incl. 'x'/'y', oid name or None)."""
    desc = arcpy.Describe(layer)
    kind = _kind(desc)
    src = coord_source or _COORD_AUTO
    _check_metric(desc, f"The {context}")
    extra = [f for f in extra_fields if f]

    if kind == "table" and src == _COORD_GEOM:
        raise arcpy.ExecuteError(
            f"The {context} is a plain table - it has no geometry. "
            "Choose Auto or Attribute fields.")
    use_geom = kind != "table" and src in (_COORD_AUTO, _COORD_GEOM)

    if use_geom:
        if kind != "point":
            raise arcpy.ExecuteError(
                f"The {context} layer is {kind.upper()} geometry - "
                "this machine analyses POINTS (one per person/place)."
                " Lines and polygons belong in the barrier input.")
        oid = desc.OIDFieldName
        if str(getattr(desc, "dataType", "")).lower().startswith(
                "shape") or str(getattr(desc, "catalogPath", "")
                                ).endswith(".shp"):
            messages.addWarningMessage(
                "Shapefile input: field names truncate to 10 "
                "characters - a file geodatabase layer is strongly "
                "recommended.")
        arr = arcpy.da.FeatureClassToNumPyArray(
            layer, [oid, "SHAPE@X", "SHAPE@Y"] + extra,
            skip_nulls=False, null_value=np.nan)
        data = {f: arr[f] for f in arr.dtype.names}
        data["x"] = np.asarray(arr["SHAPE@X"], float)
        data["y"] = np.asarray(arr["SHAPE@Y"], float)
        messages.addMessage(f"Coordinates read from feature geometry "
                            f"({len(data['x'])} points).")
        return "point", data, oid

    # tabular path (a real table, or the user insisted on fields)
    xf, yf, how = _resolve_xy_fields(layer, xf, yf,
                                     f"The {context}")
    arr = arcpy.da.TableToNumPyArray(layer, [xf, yf] + extra,
                                     skip_nulls=False,
                                     null_value=np.nan)
    data = {f: arr[f] for f in arr.dtype.names}
    data["x"] = _numeric(arr[xf], xf, f"The {context}")
    data["y"] = _numeric(arr[yf], yf, f"The {context}")
    messages.addMessage(
        f"Coordinates from attribute fields: X = '{xf}', Y = '{yf}'"
        f" ({how}). X is the easting, Y the northing.")
    return ("table" if kind == "table" else "point"), data, \
        (desc.OIDFieldName if kind != "table" else None)


def _barrier_frame(value, friction_field, agg, unit, main_sr,
                   bxf, byf, messages):
    """Geometry-aware barrier ingredient (v1.16): route by WHAT the
    input is - never through an X/Y-column resolver for spatial
    data. Returns DataFrame(x, y, friction) ready for the engine."""
    import pandas as pd
    from equipop.friction import (points_to_friction, paths_to_friction,
                                  raster_to_friction)
    desc = arcpy.Describe(value)
    kind = _kind(desc)
    aggk = _agg_key(agg)

    if kind == "raster":
        low = arcpy.RasterToNumPyArray(value)
        ext = desc.extent
        fr = raster_to_friction(
            low, float(ext.XMin), float(ext.YMax),
            float(desc.meanCellWidth), float(desc.meanCellHeight),
            unit_size=float(unit),
            nodata=getattr(desc, "noDataValue", None))
        messages.addMessage(
            f"Barrier raster sampled at analysis-cell midpoints -> "
            f"{len(fr)} friction cells (NoData/zero = free).")
        return fr

    if kind == "table":
        if not friction_field:
            raise arcpy.ExecuteError(
                "Barrier table: pick the friction value field.")
        bxf, byf, how = _resolve_xy_fields(value, bxf, byf,
                                           "The barrier table")
        arr = arcpy.da.TableToNumPyArray(
            value, [bxf, byf, friction_field], skip_nulls=False,
            null_value=np.nan)
        fr = points_to_friction(
            _numeric(arr[bxf], bxf, "The barrier table"),
            _numeric(arr[byf], byf, "The barrier table"),
            _numeric(arr[friction_field], friction_field,
                     "The barrier table"),
            unit_size=float(unit), agg=aggk)
        messages.addMessage(
            f"Barrier table: X = '{bxf}', Y = '{byf}' ({how}), "
            f"friction = '{friction_field}' -> {len(fr)} cells "
            f"(overlap rule: {aggk}).")
        return fr

    _check_metric(desc, "The barrier layer")
    if not friction_field:
        raise arcpy.ExecuteError(
            "Barrier layer: pick the numeric friction value field "
            "(crossing cost in rounds).")

    if kind in ("point", "multipoint"):
        arr = arcpy.da.FeatureClassToNumPyArray(
            value, ["SHAPE@X", "SHAPE@Y", friction_field],
            skip_nulls=False, null_value=np.nan)
        xs = np.asarray(arr["SHAPE@X"], float)
        ys = np.asarray(arr["SHAPE@Y"], float)
        vs = _numeric(arr[friction_field], friction_field,
                      "The barrier layer")
        ok = np.isfinite(xs) & np.isfinite(ys) & np.isfinite(vs)
        if (~ok).any():
            messages.addWarningMessage(
                f"{int((~ok).sum())} barrier points with missing "
                "coordinates or friction dropped.")
        fr = points_to_friction(xs[ok], ys[ok], vs[ok],
                                unit_size=float(unit), agg=aggk)
        messages.addMessage(f"Barrier points -> {len(fr)} cells "
                            f"(overlap rule: {aggk}).")
        return fr

    if kind in ("line", "polygon"):
        feats, vals, n_bad = [], [], 0
        with arcpy.da.SearchCursor(
                value, ["SHAPE@", friction_field],
                spatial_reference=main_sr) as cur:
            for row in cur:
                geom, v = row[0], row[1]
                if geom is None:
                    n_bad += 1
                    continue
                parts = []
                for part in geom:            # MULTIPART: all parts
                    if kind == "line":
                        pts = [(p.X, p.Y) for p in part
                               if p is not None]
                        if len(pts) >= 2:
                            parts.append(pts)
                    else:                    # rings split on None
                        rings, ring = [], []
                        for p in part:
                            if p is None:
                                rings.append(ring)
                                ring = []
                            else:
                                ring.append((p.X, p.Y))
                        if ring:
                            rings.append(ring)
                        rings = [r for r in rings if len(r) >= 3]
                        if rings:
                            parts.append(rings)
                if not parts:
                    n_bad += 1
                    continue
                feats.append({"type": kind, "parts": parts})
                try:
                    vals.append(float(v))
                except (TypeError, ValueError):
                    raise arcpy.ExecuteError(
                        f"The barrier layer: field '{friction_field}'"
                        " has non-numeric or missing values - fix or "
                        "filter them first.")
        if n_bad:
            messages.addWarningMessage(
                f"{n_bad} empty/invalid barrier geometries skipped.")
        if not feats:
            raise arcpy.ExecuteError(
                "The barrier layer holds no usable geometries "
                "(empty selection?).")
        fr = paths_to_friction(feats, vals, unit_size=float(unit),
                               agg=aggk)
        messages.addMessage(
            f"Barrier {kind}s: {len(feats)} features -> {len(fr)} "
            f"grid cells (EVERY cell genuinely crossed/covered; "
            f"overlap rule: {aggk}).")
        return fr

    raise arcpy.ExecuteError(
        f"Barrier input of type '{kind}' is not supported - use a "
        "point/line/polygon layer, a table, or a raster.")


def _run_tool(engine, layer, messages, treat_fields=(), value_fields=(),
              weight_field=None, k_text="", r_text="", tau_text="",
              stats_list=(), pct_text="", half_life=0.0,
              decay_model="negexp", unit=100.0,
              coord_source=None, x_field=None, y_field=None,
              barrier=None, barrier_field=None, barrier_agg="",
              barrier_x=None, barrier_y=None,
              cat_field=None, pop_values_text="", treat_values_text="",
              existing="Overwrite", out_mode="Append to input",
              out_fc=None, out_table=None, extra_dem=None,
              roundtrip=False):
    """The single glue path both machines share (stub-validated)."""
    import pandas as pd
    from equipop.stata_bridge import dispatch

    extra = list(treat_fields) + list(value_fields) \
        + ([weight_field] if weight_field else []) \
        + ([cat_field] if cat_field else [])
    kind, data, oid = _read_input(layer, coord_source, x_field,
                                  y_field, extra, messages)

    if kind == "table":
        if not out_table:
            raise arcpy.ExecuteError(
                "Table input has no feature class to append to - "
                "set the output table (.csv). The results arrive "
                "there with your coordinates.")
    elif out_mode.startswith("New"):
        if not out_fc:
            raise arcpy.ExecuteError("New feature class chosen - "
                                     "please set the output name/path.")
        arcpy.management.CopyFeatures(layer, out_fc)
        messages.addMessage(f"Copied input to {out_fc}; results go "
                            "there, input untouched.")
        layer = out_fc
        oid = arcpy.Describe(layer).OIDFieldName

    x, y = data["x"], data["y"]
    n_missing = int((~(np.isfinite(x) & np.isfinite(y))).sum())
    if n_missing:
        messages.addMessage(f"{n_missing} rows with missing coordinates"
                            " -> Null results (EquiPop convention).")

    if cat_field:
        from equipop.categorical import categories_to_binary
        pop_vals = [v.strip() for v in pop_values_text.replace(";", ",")
                    .split(",") if v.strip()] or None
        pop_mask, cat_treats = categories_to_binary(
            np.asarray(data[cat_field]), treat_values_text or "",
            pop_values=pop_vals)
        x = np.where(pop_mask, x, np.nan)
        y = np.where(pop_mask, y, np.nan)
        messages.addMessage(
            f"Category mode: population {int(pop_mask.sum())} rows; "
            f"treatments: {', '.join(cat_treats) or '(none)'}")

    kw = dict(unit_size=float(unit))
    kw["k_values"] = [int(t) for t in k_text.split()] or None
    kw["r_values"] = [float(t) for t in r_text.split()] or None
    if tau_text:
        kw["tau_values"] = [float(t) for t in tau_text.split()]
    if treat_fields:
        kw["treat"] = {f: _numeric(data[f], f, "Input")
                       for f in treat_fields}
    if cat_field and cat_treats:
        kw.setdefault("treat", {}).update(cat_treats)
    if weight_field:
        kw["weight"] = _numeric(data[weight_field], weight_field,
                                "Input")

    if engine == "counts":
        kw["treat_are_counts"] = True
        fr_df = None
        if barrier is not None:
            main_sr = getattr(arcpy.Describe(layer),
                              "spatialReference", None)
            fr_df = _barrier_frame(barrier, barrier_field, barrier_agg,
                                   unit, main_sr, barrier_x, barrier_y,
                                   messages)
        if fr_df is not None or extra_dem:
            engine = "slope" if extra_dem else "friction"
            messages.addMessage(
                f"Distance ingredients: "
                f"{'barriers ' if fr_df is not None else ''}"
                f"{'terrain' if extra_dem else ''} -> effort engine "
                "(runtime grows with data; Rounds/N_tau columns "
                "replace/join Dist).")
            if fr_df is not None:
                kw["friction_file"] = fr_df
            if extra_dem:
                kw["dem"] = str(extra_dem)
            kw["roundtrip"] = bool(roundtrip)
            kw.pop("r_values", None)      # r on effort: not defined
            if half_life and half_life > 0:
                messages.addWarningMessage(
                    "Decay over effort is not available - decay "
                    "ignored for this run (backlogged).")
                half_life = 0.0
    if engine == "counts" and half_life and half_life > 0:
        kw["half_life_m"] = float(half_life)
        kw["decay_model"] = decay_model

    if engine == "stats":
        vals = {f: _numeric(data[f], f, "Input")
                for f in value_fields}
        kw["values"] = vals
        wanted = []
        for m in stats_list:
            m = m.strip().lower()
            if not m:
                continue
            if m == "percentiles":
                qs = [q for q in (pct_text or "").replace(",", " ")
                      .split() if q]
                if not qs:
                    raise arcpy.ExecuteError(
                        "Percentiles ticked but none given - enter "
                        "plain numbers like: 10 25 75 90")
                wanted += [f"p{q}" for q in qs]
            else:
                wanted.append(_MEASURE_KEY.get(m, m))
        wanted = wanted or ["mean", "median", "gini"]
        if "gini" in wanted:
            for f, a in vals.items():
                if np.nanmin(a) < 0 if np.isfinite(a).any() else False:
                    raise arcpy.ExecuteError(
                        f"Gini is not defined for negative values and "
                        f"field '{f}' has some - untick Gini or use "
                        "a non-negative field.")
        kw["stats"] = {f: wanted for f in vals}
        messages.addMessage("Measures: " + " ".join(wanted) +
                            " (only these are calculated).")

    res = dispatch(engine, x, y, **kw)

    if kind == "table":
        out_df = pd.DataFrame({k: v for k, v in data.items()
                               if k in ("x", "y")})
        for c, v in res.items():
            out_df[_field(c)] = v
        out_df.to_csv(out_table, index=False)
        messages.addMessage(
            f"EquiPop: {len(res)} result columns written with x/y to "
            f"{out_table} ({len(out_df)} rows, row order preserved).")
        return

    dtype = [(str(oid), np.int64)] + [(_field(c), np.float64)
                                      for c in res]
    out = np.empty(len(x), dtype=dtype)
    out[str(oid)] = np.asarray(data[oid], np.int64)
    for c, v in res.items():
        out[_field(c)] = v
    existing_names = {f.name for f in arcpy.ListFields(layer)}
    clash = [c for c in (_field(c) for c in res) if c in existing_names]
    if clash and existing.startswith("Overwrite"):
        messages.addMessage(f"Overwriting {len(clash)} existing "
                            f"EquiPop fields.")
        arcpy.management.DeleteField(layer, clash)
    elif clash:
        raise arcpy.ExecuteError(
            f"Result fields already exist ({', '.join(clash[:4])}...). "
            "Choose Overwrite, or write to a new feature class.")
    arcpy.da.ExtendTable(layer, oid, out, str(oid))
    messages.addMessage(f"EquiPop: {len(res)} fields appended "
                        f"({', '.join(_field(c) for c in res)}).")
    if any(c.startswith("Dist_") for c in res):
        messages.addMessage("Note: Dist_k is in METRES - it is the "
                            "radius each point needed to gather its k "
                            "people (k fixes population, the radius "
                            "floats). Not an error - a finding.")


def _p(name, display, dtype, **kw):
    p = arcpy.Parameter(name=name, displayName=display,
                        datatype=dtype, parameterType=kw.pop(
                            "required", True) and "Required" or "Optional",
                        direction="Input")
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _coord_trio(ps, dep="layer"):
    """The shared coordinate-source parameters (v1.16)."""
    a = _p("coordsrc", "Coordinate source", "GPString", required=False)
    a.filter.type = "ValueList"
    a.filter.list = _COORD_CHOICES
    a.value = _COORD_AUTO
    bx = _p("xfield", "X field (easting) - tables/attribute mode",
            "Field", required=False)
    by = _p("yfield", "Y field (northing) - tables/attribute mode",
            "Field", required=False)
    bx.parameterDependencies = [dep]
    by.parameterDependencies = [dep]
    ps += [a, bx, by]


def _trio_update(parameters, i_layer, i_src, i_x, i_y):
    """Enable X/Y selectors when they matter; preguess once."""
    src = parameters[i_src].valueAsText or _COORD_AUTO
    is_attr = src == _COORD_ATTR
    val = parameters[i_layer].value
    is_table = False
    if val is not None:
        try:
            is_table = _kind(arcpy.Describe(val)) == "table"
        except Exception:
            pass
    on = is_attr or is_table
    parameters[i_x].enabled = on
    parameters[i_y].enabled = on
    if on and val is not None and not parameters[i_x].valueAsText \
            and not parameters[i_y].valueAsText:
        try:
            from equipop.io import guess_xy_fields
            gx, gy, deg = guess_xy_fields(_table_fields(val))
            if gx and gy and not deg:
                parameters[i_x].value = gx
                parameters[i_y].value = gy
        except Exception:
            pass


class Toolbox:
    def __init__(self):
        self.label = "EquiPop"
        self.alias = "equipop"
        self.tools = [CountsShares, ValueStatistics]
        # two machines, one shared loader (v1.16). Friction/slope
        # stay DISTANCE INGREDIENTS on machine 1, not tools.


class CountsShares:
    def __init__(self):
        self.label = "1. Counts and Shares (k / radius / decay)"
        self.description = (
            "Egocentric neighbourhoods around every point. OUTPUT "
            "FIELDS: N_k = persons among the k nearest (whole squares "
            "enter, so slightly above k is honest); T_<g>_k and "
            "R_<g>_k = group count and share; Dist_k = the RADIUS in "
            "metres that the k-search needed; N_r### = persons within "
            "the radius. INPUT: a point layer (coordinates come from "
            "the GEOMETRY - no X/Y columns needed) or a plain table "
            "(X/Y fields guessed, always overridable). BARRIERS: "
            "point/line/polygon layers, tables or rasters - every "
            "grid cell a feature genuinely crosses/covers is charged "
            "its friction value. Coordinates must be METRIC.")

    def getParameterInfo(self):
        ps = [_p("layer", "Input points (layer) or table",
                 "GPFeatureLayer;GPTableView")]
        _coord_trio(ps)
        ps += [_p("pop", "Population field - total persons at this "
                  "point (empty if each point is one person)", "Field",
                  required=False),
               _p("treat", "Group count fields - persons per group at "
                  "this point (0/1 if points are individuals)", "Field",
                  required=False, multiValue=True),
               _p("k", "k values (space-separated, e.g. 200 1600)",
                  "GPString", required=False),
               _p("r", "Radii in metres (e.g. 500 1000)", "GPString",
                  required=False),
               _p("model", "Distance decay", "GPString",
                  required=False),
               _p("halflife", "Decay half-life in metres", "GPDouble",
                  required=False),
               _p("catfield", "Category field (e.g. fclass) - builds "
                  "population and groups from VALUES instead",
                  "Field", required=False),
               _p("popvalues", "Category values forming the population "
                  "(comma-separated; empty = all rows)", "GPString",
                  required=False),
               _p("treatvalues", "Treatment categories - 'restaurant; "
                  "cafe' or grouped 'food: restaurant, cafe'",
                  "GPString", required=False),
               _p("barrier", "Distance ingredient: barriers (point/"
                  "line/polygon layer, table, or raster)",
                  "GPFeatureLayer;GPTableView;DERasterDataset",
                  required=False),
               _p("barrierfield", "Barrier friction field (crossing "
                  "cost in rounds)", "Field", required=False),
               _p("barrieragg", "Barrier overlap rule (features "
                  "sharing a cell)", "GPString", required=False),
               _p("barrierx", "Barrier X field (tabular barriers)",
                  "Field", required=False),
               _p("barriery", "Barrier Y field (tabular barriers)",
                  "Field", required=False),
               _p("dem", "Distance ingredient: elevation raster (DEM)",
                  "DEFile", required=False),
               _p("tau", "Effort budgets in rounds (e.g. 3 8)",
                  "GPString", required=False),
               _p("roundtrip", "Round trip (journey home included)",
                  "GPBoolean", required=False),
               _p("existing", "If result fields already exist",
                  "GPString", required=False),
               _p("outmode", "Output", "GPString", required=False),
               _p("outfc", "New feature class (name/path)",
                  "DEFeatureClass", required=False),
               _p("outtable", "Output table (.csv) - for TABLE inputs",
                  "DEFile", required=False),
               _p("unit", "Cell size (m)", "GPDouble", required=False)]
        for i in (4, 5, 10):
            ps[i].parameterDependencies = ["layer"]
        for i in (14, 16, 17):
            ps[i].parameterDependencies = ["barrier"]
        ps[8].filter.type = "ValueList"
        ps[8].filter.list = ["no decay", "negexp", "expnormal",
                             "expsqrt", "lognormal", "power"]
        ps[8].value = "no decay"
        ps[15].filter.type = "ValueList"
        ps[15].filter.list = _AGG_CHOICES
        ps[15].value = _AGG_CHOICES[0]
        ps[21].filter.type = "ValueList"
        ps[21].filter.list = ["Overwrite", "Stop with a message"]
        ps[21].value = "Overwrite"
        ps[22].filter.type = "ValueList"
        ps[22].filter.list = ["Append to input", "New feature class"]
        ps[22].value = "Append to input"
        ps[24].direction = "Output"
        ps[25].value = 100.0
        return ps

    def updateParameters(self, parameters):
        _trio_update(parameters, 0, 1, 2, 3)
        parameters[9].enabled = (parameters[8].valueAsText
                                 not in (None, "", "no decay"))
        bar = parameters[13].value
        bar_on = bar is not None
        for i in (14, 15):
            parameters[i].enabled = bar_on
        bar_table = False
        if bar_on:
            try:
                bar_table = _kind(arcpy.Describe(bar)) == "table"
            except Exception:
                pass
        parameters[16].enabled = bar_table
        parameters[17].enabled = bar_table
        ing = bar_on or bool(parameters[18].valueAsText)
        parameters[19].enabled = ing          # tau
        parameters[20].enabled = ing          # roundtrip
        parameters[23].enabled = (parameters[22].valueAsText
                                  == "New feature class")
        return

    def execute(self, parameters, messages):
        v = [p.valueAsText or "" for p in parameters]
        model = v[8] or "no decay"
        _run_tool("counts", parameters[0].value, messages,
                  coord_source=v[1] or None,
                  x_field=v[2] or None, y_field=v[3] or None,
                  weight_field=v[4] or None,
                  treat_fields=[f for f in v[5].split(";") if f],
                  k_text=v[6], r_text=v[7],
                  half_life=float(v[9] or 0) if model != "no decay"
                  else 0.0,
                  decay_model=model if model != "no decay" else
                  "negexp",
                  cat_field=v[10] or None, pop_values_text=v[11],
                  treat_values_text=v[12],
                  barrier=parameters[13].value or None,
                  barrier_field=v[14] or None, barrier_agg=v[15],
                  barrier_x=v[16] or None, barrier_y=v[17] or None,
                  extra_dem=v[18] or None, tau_text=v[19],
                  roundtrip=(v[20] or "").lower() in
                  ("true", "1", "yes"),
                  existing=v[21] or "Overwrite",
                  out_mode=v[22] or "Append to input",
                  out_fc=v[23] or None, out_table=v[24] or None,
                  unit=float(v[25] or 100))


class ValueStatistics:
    def __init__(self):
        self.label = "2. Value Statistics (numeric fields among the k nearest)"
        self.description = (
            "Selectable statistics of any NUMERIC fields (income, "
            "rent, age...) among each point's k nearest PERSONS. "
            "Tick the measures you want - only those are calculated. "
            "FULL POPULATION field: if each point carries several "
            "persons, k counts PERSONS and every statistic weights "
            "by population (rows are expanded exactly). Output "
            "columns like Mean_<f>_k, Med_<f>_k, P90_<f>_k, plus "
            "Nv_<f>_k = how many neighbours had a usable value (the "
            "honesty column). Input: point layer (geometry) or plain "
            "table (X/Y guessed, overridable).")

    def getParameterInfo(self):
        ps = [_p("layer", "Input points (layer) or table",
                 "GPFeatureLayer;GPTableView")]
        _coord_trio(ps)
        ps += [_p("fullpop", "Full population field - persons per "
                  "point (empty = one each); k is measured against "
                  "this", "Field", required=False),
               _p("values", "Numeric value fields (e.g. income, rent, "
                  "age)", "Field", multiValue=True),
               _p("measures", "Measures to calculate", "GPString",
                  multiValue=True, required=False),
               _p("pcts", "Percentiles (plain numbers, e.g. 10 25 75 "
                  "90)", "GPString", required=False),
               _p("k", "k values", "GPString"),
               _p("r", "Radii in metres", "GPString", required=False),
               _p("outtable", "Output table (.csv) - for TABLE inputs",
                  "DEFile", required=False),
               _p("unit", "Cell size (m)", "GPDouble", required=False)]
        ps[4].parameterDependencies = ["layer"]
        ps[5].parameterDependencies = ["layer"]
        ps[6].filter.type = "ValueList"
        ps[6].filter.list = _MEASURES
        ps[6].value = "mean;median;gini"
        ps[7].value = "10 25 75 90"
        ps[10].direction = "Output"
        ps[11].value = 100.0
        return ps

    def updateParameters(self, parameters):
        _trio_update(parameters, 0, 1, 2, 3)
        chosen = (parameters[6].valueAsText or "").lower()
        parameters[7].enabled = "percentiles" in chosen
        return

    def execute(self, parameters, messages):
        v = [p.valueAsText or "" for p in parameters]
        _run_tool("stats", parameters[0].value, messages,
                  coord_source=v[1] or None,
                  x_field=v[2] or None, y_field=v[3] or None,
                  weight_field=v[4] or None,
                  value_fields=[f for f in v[5].split(";") if f],
                  stats_list=[m.strip("' ") for m in v[6].split(";")
                              if m.strip("' ")],
                  pct_text=v[7],
                  k_text=v[8], r_text=v[9],
                  out_table=v[10] or None,
                  unit=float(v[11] or 100))
