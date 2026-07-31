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

v1.18 SHARED CORE: the parts every door needs - the help text, the
forwarding of the package's printed voice into the pane, the result
column names, and the coordinate rules - moved into the package
(equipop.doors) so the QGIS, R and SPSS doors inherit them instead
of rebuilding them. This file kept its behaviour exactly; it now
calls the shared versions. It declares _CONTRACT below: if the
installed package outgrows it, the door says so and names the fix.
The package is still imported LAZILY, inside functions, so the
toolbox opens in Pro even when equipop is not installed.

v1.16 GIS INPUT REWORK: both machines share one loader. Spatial
inputs are read FROM GEOMETRY (no X/Y attribute columns needed,
ever); plain tables get guessed-but-overridable X and Y fields;
degree CRS refused loudly; line/polygon/raster barriers map to every
grid cell they genuinely touch. Results append to point layers as
row-aligned double fields (Null where coordinates are missing);
table inputs write a NEW output table.
"""

import time

import numpy as np

import arcpy

# The shared core this toolbox was built against (equipop.doors).
# If the package is upgraded past it, the door says so and names the
# fix instead of failing somewhere obscure.
_CONTRACT = 1
_MISSING = (
    "The EquiPop Python package is not installed in this ArcGIS Pro "
    "environment. Clone the default environment (Package Manager), "
    "activate the clone, and in its Python Command Prompt run:  "
    "pip install equipop")


def _too_old(found):
    return (
        f"This toolbox needs EquiPop 1.18.0 or later, but the package "
        f"installed in this ArcGIS Pro environment is {found}, which "
        "has no equipop.doors module. The toolbox files were replaced "
        "and the package was not. In the Python Command Prompt of "
        "this environment run:  pip install --upgrade equipop  "
        "then close and reopen ArcGIS Pro.")


def _doors(strict=True):
    """The shared core, or a loud refusal. Imported lazily on
    purpose: the toolbox must still OPEN in Pro when the package is
    absent, so that the dialogs can explain themselves rather than
    the toolbox simply failing to appear.

    The two ways this goes wrong are told apart, because they have
    different fixes and the wrong message sends people hunting: the
    package may be missing entirely, or it may be present but older
    than this toolbox - the likely case, since the package is
    upgraded by pip while the toolbox files are replaced by hand."""
    try:
        import equipop.doors as D
    except Exception:
        try:
            import equipop
            found = getattr(equipop, "__version__", "of unknown version")
        except Exception:
            found = None
        if strict:
            raise arcpy.ExecuteError(
                _MISSING if found is None else _too_old(found))
        return None
    if not getattr(_doors, "_checked", False):
        try:
            D.require(_CONTRACT,
                      door="this EquiPop toolbox (EquiPop.pyt)",
                      files="EquiPop.pyt and its two .pyt.xml files")
        except D.DoorError as e:
            if strict:
                raise arcpy.ExecuteError(str(e))
            return None
        _doors._checked = True
    return D


def _channel(messages):
    from equipop.doors.report import Channel
    return Channel.from_arcpy(messages)


def _speaking(messages):
    """Everything the package prints inside this block reaches Pro's
    message pane, line by line (v1.16.4: a 94-minute run was
    completely silent)."""
    from equipop.doors.report import speaking
    _doors()
    return speaking(_channel(messages))


def _hms(sec):
    from equipop.doors.report import hms
    return hms(sec)


def _stage(messages, label, store=None):
    """Time one stage and report it, so a long run says WHERE the
    time went instead of only how long it took in total."""
    from equipop.doors.report import stage
    return stage(_channel(messages), label, store)


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
    from equipop.doors.fields import safe_field_name
    return safe_field_name(name)


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


def _utm_advice(desc):
    """Suggest the metric CRS that FITS the data: computed UTM zone
    from the layer's own extent (degrees), SWEREF only over Sweden
    (field-test finding: Anatolian data got Swedish advice)."""
    try:
        e = desc.extent
        lon = (float(e.XMin) + float(e.XMax)) / 2.0
        lat = (float(e.YMin) + float(e.YMax)) / 2.0
        if 10.0 <= lon <= 25.0 and 55.0 <= lat <= 70.0:
            return "SWEREF 99 TM (EPSG:3006)"
        z = min(max(int((lon + 180.0) // 6) + 1, 1), 60)
        if lat >= 0:
            return f"WGS 84 / UTM zone {z}N (EPSG:{32600 + z})"
        return f"WGS 84 / UTM zone {z}S (EPSG:{32700 + z})"
    except Exception:
        return "the local UTM zone"


def _geographic_text(desc, what):
    sr = getattr(desc, "spatialReference", None)
    if sr is not None and str(getattr(sr, "type", "")) == "Geographic":
        return (f"{what} is in a GEOGRAPHIC coordinate system "
                f"({getattr(sr, 'name', 'degrees')}) - EquiPop needs "
                f"metres. Project it first - for this data "
                f"{_utm_advice(desc)} fits (Geoprocessing > Project) "
                "- and run again.")
    return None


def _epsg_from_advice(desc):
    """The EPSG code behind _utm_advice(), for auto-projection."""
    a = _utm_advice(desc)
    for tok in a.replace("(", " ").replace(")", " ").split():
        if tok.startswith("EPSG:"):
            try:
                return int(tok.split(":")[1])
            except ValueError:
                return None
    return None


def _check_metric(desc, what, auto_project=False):
    """Degrees are refused LOUDLY - EquiPop distances are metres -
    unless the user ticked auto-projection, in which case a LAYER is
    read in the fitting metric CRS instead (v1.16.3). Tables always
    refuse: their numbers carry no CRS to project from."""
    txt = _geographic_text(desc, what)
    if txt:
        if auto_project and getattr(desc, "shapeType", None):
            return arcpy.SpatialReference(_epsg_from_advice(desc))
        raise arcpy.ExecuteError(txt)
    return getattr(desc, "spatialReference", None)


def _table_fields(value):
    return [f.name for f in arcpy.ListFields(value)]


def _utm_from_lonlat(lon, lat):
    """Fitting metric CRS straight from coordinate VALUES - the table
    path has no CRS object to ask (field-test gap: degree tables were
    refused without a suggestion)."""
    from equipop.doors.loader import metric_crs_hint
    return metric_crs_hint(lon, lat)


def _sample_lonlat(value, gx, gy):
    try:
        a = arcpy.da.TableToNumPyArray(value, [gx, gy],
                                       skip_nulls=False,
                                       null_value=np.nan)
        return (float(np.nanmedian(np.asarray(a[gx], float))),
                float(np.nanmedian(np.asarray(a[gy], float))))
    except Exception:
        return (None, None)


def _resolve_xy_fields(value, xf, yf, context):
    """User choice first; package guess second; loud advice third.
    Never tells the user to rename columns."""
    D = _doors()
    from equipop.doors.loader import resolve_xy_fields
    try:
        return resolve_xy_fields(
            _table_fields(value), xf, yf, context,
            sample_lonlat=lambda gx, gy: _sample_lonlat(value, gx, gy))
    except D.DoorError as e:
        raise arcpy.ExecuteError(str(e))


def _check_fields_exist(layer, fields, context):
    """Every field box must hold a REAL field of this layer. Typing a
    number (a k value in a field box - the '55' field-test error) or
    a leftover name from another layer is caught here with advice,
    instead of arcpy's bare "Cannot find field"."""
    D = _doors()
    from equipop.doors.loader import check_fields_exist
    try:
        have = list(_table_fields(layer))
    except Exception:
        return
    try:
        check_fields_exist(have, fields, context)
    except D.DoorError as e:
        raise arcpy.ExecuteError(str(e))


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
                context="input", auto_project=False):
    """THE SHARED LOADER (v1.16): one behaviour for both machines.
    Returns the door contract object (equipop.doors.loader.
    PointInput), which still unpacks as (kind, data dict incl.
    'x'/'y', oid name or None) - so every door hands the engines the
    same thing while the reading stays arcpy's business."""
    _doors()
    from equipop.doors.loader import PointInput
    desc = arcpy.Describe(layer)
    kind = _kind(desc)
    src = coord_source or _COORD_AUTO
    extra = [f for f in extra_fields if f]
    _check_fields_exist(layer, extra, f"The {context}")
    _check_metric(desc, f"The {context}", auto_project)

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
        sr_used = _check_metric(desc, f"The {context}", auto_project)
        _read_input.last_sr = sr_used
        proj = (sr_used is not None
                and str(getattr(desc.spatialReference, "type", ""))
                == "Geographic")
        arr = arcpy.da.FeatureClassToNumPyArray(
            layer, [oid, "SHAPE@X", "SHAPE@Y"] + extra,
            skip_nulls=False, null_value=np.nan,
            spatial_reference=sr_used) if proj else \
            arcpy.da.FeatureClassToNumPyArray(
                layer, [oid, "SHAPE@X", "SHAPE@Y"] + extra,
                skip_nulls=False, null_value=np.nan)
        if proj:
            messages.addWarningMessage(
                f"Input was in degrees - AUTO-PROJECTED to "
                f"{_utm_advice(desc)} for this analysis. The input "
                "data itself is untouched; distances are metres in "
                "that projection.")
        data = {f: arr[f] for f in arr.dtype.names}
        data["x"] = np.asarray(arr["SHAPE@X"], float)
        data["y"] = np.asarray(arr["SHAPE@Y"], float)
        sr_name = getattr(sr_used, "name", None) or getattr(
            getattr(desc, "spatialReference", None), "name", "unknown")
        sr_code = getattr(sr_used, "factoryCode", None) or getattr(
            getattr(desc, "spatialReference", None), "factoryCode", 0)
        _read_input.last_crs_text = (
            f"{sr_name}" + (f" (EPSG:{sr_code})" if sr_code else ""))
        messages.addMessage(
            f"Coordinates read from feature geometry "
            f"({len(data['x'])} points). Working CRS: "
            f"{_read_input.last_crs_text} - all distances are metres "
            "in this projection.")
        return PointInput("point", data, oid,
                          crs_text=_read_input.last_crs_text,
                          note="feature geometry")

    # tabular path (a real table, or the user insisted on fields)
    xf, yf, how = _resolve_xy_fields(layer, xf, yf,
                                     f"The {context}")
    oid = desc.OIDFieldName if kind != "table" else None
    read = [xf, yf] + extra + ([oid] if oid and oid not in
                               ([xf, yf] + extra) else [])
    arr = arcpy.da.TableToNumPyArray(layer, read,
                                     skip_nulls=False,
                                     null_value=np.nan)
    data = {f: arr[f] for f in arr.dtype.names}
    data["x"] = _numeric(arr[xf], xf, f"The {context}")
    data["y"] = _numeric(arr[yf], yf, f"The {context}")
    messages.addMessage(
        f"Coordinates from attribute fields: X = '{xf}', Y = '{yf}'"
        f" ({how}). X is the easting, Y the northing.")
    return PointInput("table" if kind == "table" else "point",
                      data, oid,
                      crs_text=getattr(_read_input, "last_crs_text",
                                       "unknown"),
                      note=f"attribute fields ({how})")


def _ref(value):
    """arcpy is inconsistent: Describe() and cursors accept a Layer
    OBJECT, while RasterToNumPyArray insists on a path or a Raster
    (v1.16.7 field finding: 'Expected a Raster instance or path
    name'). Normalise to something every call accepts."""
    if value is None or isinstance(value, str):
        return value
    for attr in ("value", "catalogPath", "dataSource"):
        v = getattr(value, attr, None)
        if isinstance(v, str) and v:
            return v
    try:
        return str(value)
    except Exception:
        return value


def _raster_payload(value, messages):
    """Read a raster HERE (arcpy) and hand the package plain numbers.
    The package must never open GIS files itself - installing
    rasterio into a Pro clone means two GDALs fighting over DLLs
    (field-test finding: ModuleNotFoundError 'rasterio')."""
    src = _ref(value)
    d = arcpy.Describe(src)
    _check_metric(d, "The elevation raster")
    arr = arcpy.RasterToNumPyArray(src)
    ext = d.extent
    pay = {"array": np.asarray(arr, float),
           "x_min": float(ext.XMin), "y_max": float(ext.YMax),
           "cell_w": float(d.meanCellWidth),
           "cell_h": float(d.meanCellHeight),
           "nodata": getattr(d, "noDataValue", None)}
    messages.addMessage(
        f"Elevation raster read by ArcGIS: {pay['array'].shape[0]} x "
        f"{pay['array'].shape[1]} pixels at {pay['cell_w']:g} m.")
    return pay


def _barrier_frame(value, friction_field, agg, unit, main_sr,
                   bxf, byf, messages):
    """Geometry-aware barrier ingredient (v1.16): route by WHAT the
    input is - never through an X/Y-column resolver for spatial
    data. Returns DataFrame(x, y, friction) ready for the engine."""
    import pandas as pd
    from equipop.friction import (points_to_friction, paths_to_friction,
                                  raster_to_friction)
    value = _ref(value)
    desc = arcpy.Describe(value)
    kind = _kind(desc)
    aggk = _agg_key(agg)

    if kind == "raster":
        low = arcpy.RasterToNumPyArray(_ref(value))
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


def _predict_result_fields(engine, k_text, r_text, tau_text,
                           treat_names, value_fields, stats_wanted,
                           decaying, efforting):
    """The columns a run WILL produce (validated against dispatch in
    the simulator suite) - so shapefile targets can be refused
    BEFORE the computation, not after (field-test finding A4).

    Runs at DIALOG time as well as at run time. With the package
    missing there is nothing to predict from, and an empty list
    simply means no pre-check; the run itself still refuses loudly.
    A half-working dialog is more use than one that will not open."""
    if _doors(strict=False) is None:
        return []
    from equipop.doors.fields import predict_result_fields
    return predict_result_fields(engine, k_text, r_text, tau_text,
                                 treat_names, value_fields,
                                 stats_wanted, decaying, efforting)


def _shorten_names(names, cap: int = 10):
    """Collision-free abbreviation for shapefile targets (opt-in).
    Keeps the statistic prefix and the suffix (k/radius) - the parts
    that distinguish results - and uniquifies by construction, so
    P25_income_400 and P75_income_400 can never collapse into one
    field. Returns {original: short}."""
    from equipop.doors.fields import shorten_names
    return shorten_names(names, cap)


def _refuse_shp_overflow(target, names, messages=None):
    """dBASE (shapefile) field names cap at 10 characters - refuse
    with the fix instead of failing after minutes of compute."""
    if _doors(strict=False) is None:
        return None
    from equipop.doors.fields import refuse_short_target
    return refuse_short_target(target, names)


def _categories_from_table(rows, cat_values, messages):
    """Value-table rows -> (population values, {group: [values]}).

    Columns: category value | group name | in population? The grid
    retires the ';' / ',' / ':' syntax that produced a group called
    'shop, school' matching nothing (field test, v1.16.8).
    """
    pop_vals, groups = [], {}
    known = set(cat_values or [])
    unknown = []
    for row in rows:
        val = row[0] if row else ""
        grp = row[1] if len(row) > 1 else ""
        inpop = (row[2] if len(row) > 2 else "true").strip().lower()
        if not val:
            continue
        if known and val not in known:
            unknown.append(val)
        if inpop not in ("false", "no", "0", "n"):
            pop_vals.append(val)
        if grp:
            groups.setdefault(grp, []).append(val)
    if unknown:
        raise arcpy.ExecuteError(
            f"These values are not in the category field: "
            f"{', '.join(unknown[:6])}. The field holds: "
            f"{', '.join(sorted(known)[:12])}"
            + ("..." if len(known) > 12 else ""))
    empty = [g for g, vs in groups.items() if not vs]
    if empty:
        raise arcpy.ExecuteError(
            f"Group(s) {', '.join(empty)} have no values - a group "
            "that matches nothing would only produce columns of "
            "zeros.")
    messages.addMessage(
        f"Categories: population = "
        f"{', '.join(pop_vals) if pop_vals else '(all rows)'}; "
        + "; ".join(f"{g} = {', '.join(v)}" for g, v in groups.items())
        if groups else "no groups")
    return pop_vals, groups


def _collect_barriers(rows, agg, unit, main_sr, messages):
    """Several barrier sources -> ONE friction frame (v1.17). Each
    source is read by its own route (lines, polygons, points, table,
    raster); the overlap rule then combines whatever lands in the
    same cell - which is what finally makes additive stacking
    reachable: a river, a railway AND a lake in one run."""
    from equipop.friction import _agg_cells
    parts = []
    for row in rows:
        src = row[0]
        fld = row[1] if len(row) > 1 else None
        parts.append(_barrier_frame(src, fld or None, agg, unit,
                                    main_sr, None, None, messages))
    acc: dict = {}
    for p in parts:
        for xx, yy, ff in zip(p["x"], p["y"], p["friction"]):
            acc.setdefault((float(xx), float(yy))
                           , []).append(float(ff))
    out = _agg_cells(acc, _agg_key(agg))
    messages.addMessage(
        f"{len(parts)} barrier sources -> {len(out)} friction cells "
        f"(overlap rule: {_agg_key(agg)}).")
    return out


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
              roundtrip=False, auto_project=False,
              short_names=False, decay_eps: float = 1e-6,
              cat_rows=None, barrier_rows=None,
              groups_count="persons", half_life_field=None,
              half_life_from_dist=None, decay_bins: int = 10,
              seed=None):
    """The single glue path both machines share (stub-validated)."""
    import pandas as pd
    from equipop.stata_bridge import dispatch

    extra = list(treat_fields) + list(value_fields) \
        + ([weight_field] if weight_field else []) \
        + ([cat_field] if cat_field else []) \
        + ([half_life_field] if half_life_field else [])
    t_all = time.time()
    stages = []
    with _stage(messages, "reading input", stages), _speaking(messages):
        kind, data, oid = _read_input(layer, coord_source, x_field,
                                      y_field, extra, messages,
                                      auto_project=auto_project)

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
        if cat_rows:
            known = sorted({str(v).strip()
                            for v in np.asarray(data[cat_field])
                            if str(v).strip()})
            pop_vals, groups = _categories_from_table(
                cat_rows, known, messages)
            pop_mask, cat_treats = categories_to_binary(
                np.asarray(data[cat_field]), groups,
                pop_values=pop_vals or None)
        else:
            pop_vals = [v.strip() for v in
                        pop_values_text.replace(";", ",").split(",")
                        if v.strip()] or None
            pop_mask, cat_treats = categories_to_binary(
                np.asarray(data[cat_field]), treat_values_text or "",
                pop_values=pop_vals)
        if str(groups_count).startswith("person") and weight_field:
            # v1.17 ruling: with a population field set, category
            # groups count PERSONS, so every share has the same
            # denominator as N (field test: 4 places over 140 persons)
            wcol = _numeric(data[weight_field], weight_field, "Input")
            cat_treats = {g: v * np.nan_to_num(wcol)
                          for g, v in cat_treats.items()}
            messages.addMessage(
                "Category groups count PERSONS (weighted by "
                f"'{weight_field}') - shares are persons/persons.")
        else:
            messages.addMessage(
                "Category groups count PLACES (rows).")
        x = np.where(pop_mask, x, np.nan)
        y = np.where(pop_mask, y, np.nan)
        messages.addMessage(
            f"Category mode: population {int(pop_mask.sum())} rows; "
            f"treatments: {', '.join(cat_treats) or '(none)'}")

    treat_names = list(treat_fields) + (list(cat_treats)
                                        if cat_field else [])
    if kind != "table":
        target = (out_fc if out_mode.startswith("New") and out_fc
                  else getattr(arcpy.Describe(layer), "catalogPath",
                               ""))
        wanted_pred = []
        if engine == "stats":
            for m in stats_list:
                m = (m or "").strip().lower()
                if m == "percentiles":
                    wanted_pred += [f"p{q}" for q in
                                    (pct_text or "").replace(",", " ")
                                    .split()]
                elif m:
                    wanted_pred.append(_MEASURE_KEY.get(m, m))
        txt = None if short_names else _refuse_shp_overflow(
            target, _predict_result_fields(
            engine, k_text, r_text, tau_text, treat_names,
            list(value_fields),
            wanted_pred or ["mean", "median", "gini"],
            decaying=bool(half_life), efforting=bool(
                barrier is not None or extra_dem)))
        if txt:
            raise arcpy.ExecuteError(txt)

    kw = dict(unit_size=float(unit))
    kw["k_values"] = [int(round(v)) for v in _numlist(k_text)] or None
    kw["r_values"] = _numlist(r_text) or None
    if tau_text:
        kw["tau_values"] = _numlist(tau_text)
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
        if barrier_rows:
            main_sr = getattr(_read_input, "last_sr", None) or \
                getattr(arcpy.Describe(layer), "spatialReference", None)
            with _stage(messages, "building barriers", stages), \
                    _speaking(messages):
                fr_df = _collect_barriers(barrier_rows, barrier_agg,
                                          unit, main_sr, messages)
        elif barrier is not None:
            # the CRS the POINTS were read in - not the layer's stored
            # one. Under auto-projection those differ, and handing the
            # barrier reader the stored (degree) CRS produced a grid
            # domain spanning metres-to-degrees: 290 million cells and
            # a 17 GiB allocation error (field test v1.16.5).
            main_sr = getattr(_read_input, "last_sr", None) or \
                getattr(arcpy.Describe(layer), "spatialReference", None)
            with _stage(messages, "building barriers", stages), \
                    _speaking(messages):
                fr_df = _barrier_frame(barrier, barrier_field,
                                       barrier_agg, unit, main_sr,
                                       barrier_x, barrier_y, messages)
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
                with _stage(messages, "reading elevation raster",
                            stages):
                    kw["dem"] = _raster_payload(extra_dem, messages)
            kw["roundtrip"] = bool(roundtrip)
            kw.pop("r_values", None)      # r on effort: not defined
            if half_life and half_life > 0:
                messages.addWarningMessage(
                    "Decay over effort is not available - decay "
                    "ignored for this run (backlogged).")
                half_life = 0.0
    if engine == "counts" and half_life_field:
        _check_fields_exist(layer, [half_life_field], "The input")
        kw["half_life_field"] = _numeric(
            data[half_life_field], half_life_field, "Input")
        kw["decay_bins"] = int(decay_bins or 10)
        messages.addMessage(
            f"Variable bandwidth: half-life from '{half_life_field}' "
            f"({np.nanmin(kw['half_life_field']):,.0f}-"
            f"{np.nanmax(kw['half_life_field']):,.0f} m), "
            f"{kw['decay_bins']} bins.")
    elif engine == "counts" and half_life_from_dist:
        kw["half_life_from_dist"] = int(half_life_from_dist)
        kw["decay_bins"] = int(decay_bins or 10)
        messages.addMessage(
            f"Self-calibrating bandwidth: each point's own "
            f"Dist_{int(half_life_from_dist)} becomes its half-life, "
            "so urban form sets the kernel.")
    if seed is not None:
        kw["seed"] = int(seed)
    if engine == "counts" and half_life and half_life > 0:
        kw["half_life_m"] = float(half_life)
        kw["decay_model"] = decay_model
        kw["decay_eps"] = float(decay_eps)
        messages.addMessage(
            f"Distance decay: {decay_model}, half-life "
            f"{float(half_life):g} m, cutoff {float(decay_eps):g} - "
            "the truncation distance is reported by the engine below "
            "(a bigger cutoff means a smaller search and a faster "
            "run).")

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

    messages.addMessage(
        f"Calculating ({engine} engine, {len(x)} rows, cell size "
        f"{float(unit):g} m). Progress and engine notes follow; "
        "bigger cells mean fewer origins and faster runs.")
    with _stage(messages, "calculating", stages), _speaking(messages):
        res = dispatch(engine, x, y, **kw)

    if kind == "table":
        with _stage(messages, "writing output table", stages):
            out_df = pd.DataFrame({k: v for k, v in data.items()
                                   if k in ("x", "y")})
            for c, v in res.items():
                out_df[_field(c)] = v
            out_df.to_csv(out_table, index=False)
        messages.addMessage(
            f"EquiPop: {len(res)} result columns written with x/y to "
            f"{out_table} ({len(out_df)} rows, row order preserved).")
        _write_manifest(out_table, _manifest_rows(
            engine, layer, unit, k_text, r_text, tau_text, stats_list,
            pct_text, half_life, decay_model, decay_eps, barrier,
            barrier_field, barrier_agg, auto_project, len(x),
            list(res), stages, time.time() - t_all), messages)
        messages.addMessage("[time] TOTAL: " + _hms(time.time()
                                                    - t_all))
        return

    names = {c: _field(c) for c in res}
    cat = getattr(arcpy.Describe(layer), "catalogPath", "")
    txt = _refuse_shp_overflow(cat, list(names.values()))
    if txt and not short_names:    # safety net: exact names
        raise arcpy.ExecuteError(txt)
    if txt and short_names:
        short = _shorten_names(list(names.values()))
        messages.addWarningMessage(
            "Shapefile target: result names shortened to 10 "
            "characters (collision-free). Mapping: "
            + "; ".join(f"{k} -> {v}" for k, v in short.items()))
        names = {c: short[n] for c, n in names.items()}
        try:    # a mapping that lives only in a run log is useless
            import csv as _csv
            side = str(cat).rsplit(".", 1)[0] + "_EquiPop_fields.csv"
            with open(side, "w", newline="", encoding="utf-8") as fh:
                w = _csv.writer(fh)
                w.writerow(["full_name", "shapefile_name"])
                for k, v in short.items():
                    w.writerow([k, v])
            messages.addMessage(f"Name mapping also saved to {side}")
        except Exception as exc:
            messages.addWarningMessage(
                f"Could not save the name mapping next to the "
                f"output ({exc}) - it is printed above.")
    dtype = [(str(oid), np.int64)] + [(names[c], np.float64)
                                      for c in res]
    out = np.empty(len(x), dtype=dtype)
    out[str(oid)] = np.asarray(data[oid], np.int64)
    for c, v in res.items():
        out[names[c]] = v
    flds = {f.name: f for f in arcpy.ListFields(layer)}
    clash = [c for c in names.values() if c in flds]
    if clash and not existing.startswith("Overwrite"):
        raise arcpy.ExecuteError(
            f"Result fields already exist ({', '.join(clash[:4])}...). "
            "Choose Overwrite, or write to a new feature class.")
    reusable = [c for c in clash
                if str(getattr(flds[c], "type", "")).lower()
                in ("double", "single", "float")]
    stale = [c for c in clash if c not in reusable]
    if reusable:
        # v1.16.5: UPDATE the existing columns instead of deleting
        # them. DeleteField rewrites the entire table, which is both
        # the slowest step there is AND what desynchronises a map
        # layer from its own file (field-test: symbology offering
        # fields the table no longer had).
        messages.addMessage(
            f"Updating {len(reusable)} existing EquiPop fields in "
            "place - no schema change, so the layer and its file stay "
            "in step.")
        back = {names[c]: c for c in res}
        with _stage(messages, "updating existing fields", stages):
            pos = {o: i for i, o in enumerate(
                np.asarray(data[oid], np.int64))}
            last = None
            for attempt in range(3):        # locks are often transient
                try:
                    with arcpy.da.UpdateCursor(
                            layer, [str(oid)] + reusable) as cur:
                        for row in cur:
                            i = pos.get(int(row[0]))
                            if i is None:
                                continue
                            for j, nm in enumerate(reusable, start=1):
                                row[j] = float(res[back[nm]][i])
                            cur.updateRow(row)
                    last = None
                    break
                except RuntimeError as exc:
                    last = exc
                    if "lock" not in str(exc).lower():
                        raise
                    time.sleep(1.5)
                    messages.addWarningMessage(
                        f"Could not get a write lock (attempt "
                        f"{attempt + 1}/3) - retrying...")
            if last is not None:
                raise arcpy.ExecuteError(
                    "Cannot get a write lock on the target, so the "
                    "existing EquiPop fields cannot be updated. "
                    "Something else is holding the data: an open "
                    "ATTRIBUTE TABLE for this layer, an active edit "
                    "session, the file open in another program, or "
                    "a sync client (OneDrive) touching it. Close "
                    "those and run again - or choose Output = New "
                    "feature class, which writes somewhere fresh and "
                    "needs no lock on the input. Nothing was "
                    "changed.")
    if stale:
        messages.addWarningMessage(
            f"{len(stale)} existing fields have the wrong type and "
            "must be replaced - this rewrites the table; if the "
            "layer is open in a map, remove and re-add it afterwards: "
            + ", ".join(stale[:6]))
        with _stage(messages, "deleting mistyped fields", stages):
            arcpy.management.DeleteField(layer, stale)
    fresh = [c for c in names.values() if c not in reusable]
    if fresh:
        keep = [str(oid)] + fresh
        sub = out[[c for c in out.dtype.names if c in keep]]
        with _stage(messages, "writing results to the layer", stages):
            arcpy.da.ExtendTable(layer, oid, sub, str(oid))
    after = {f.name for f in arcpy.ListFields(layer)}
    missing = [c for c in names.values() if c not in after]
    where = _catalog_of(layer) or str(layer)
    if missing:
        messages.addWarningMessage(
            f"{len(missing)} result fields are NOT in the target "
            f"after writing ({', '.join(missing[:6])}). The dataset "
            f"written to was: {where}. If your map shows something "
            "else, that is the mismatch - check the layer's source.")
    else:
        messages.addMessage(
            f"EquiPop: {len(res)} fields written and VERIFIED present "
            f"in {where} ({', '.join(names.values())}).")
    _write_manifest(_catalog_of(layer) or out_fc, _manifest_rows(
        engine, layer, unit, k_text, r_text, tau_text, stats_list,
        pct_text, half_life, decay_model, decay_eps, barrier,
        barrier_field, barrier_agg, auto_project, len(x),
        list(names.values()), stages, time.time() - t_all), messages)
    if stages:
        slow = max(stages, key=lambda p: p[1])
        messages.addMessage(
            "[time] TOTAL: " + _hms(time.time() - t_all)
            + f" - most of it in '{slow[0]}' ({_hms(slow[1])}).")
    if any(c.startswith("Dist_") for c in res):
        messages.addMessage("Note: Dist_k is in METRES - it is the "
                            "radius each point needed to gather its k "
                            "people (k fixes population, the radius "
                            "floats). Not an error - a finding.")


def _manifest_rows(engine, layer, unit, k_text, r_text, tau_text,
                   stats_list, pct_text, half_life, decay_model,
                   decay_eps, barrier, barrier_field, barrier_agg,
                   auto_project, n_rows, out_fields, stages, total):
    import datetime
    try:
        import equipop
        ver = equipop.__version__
    except Exception:
        ver = "unknown"
    rows = [
        ("equipop_version", ver),
        ("run_utc", datetime.datetime.now(
            datetime.timezone.utc).isoformat(timespec="seconds")),
        ("engine", engine),
        ("input", _catalog_of(layer) or str(layer)),
        ("working_crs", getattr(_read_input, "last_crs_text",
                                "unknown")),
        ("auto_projected", bool(auto_project)),
        ("cell_size_m", unit),
        ("k_values", k_text), ("radii_m", r_text),
        ("effort_budgets_tau", tau_text),
        ("decay_model", decay_model if half_life else "no decay"),
        ("decay_half_life_m", half_life or ""),
        ("decay_cutoff_eps", decay_eps if half_life else ""),
        ("measures", ";".join(stats_list) if stats_list else ""),
        ("percentiles", pct_text if stats_list else ""),
        ("barrier_source", _catalog_of(barrier) if barrier
         is not None else ""),
        ("barrier_field", barrier_field or ""),
        ("barrier_overlap_rule", _agg_key(barrier_agg)
         if barrier is not None else ""),
        ("rows_analysed", n_rows),
        ("result_fields", ";".join(out_fields)),
        ("total_seconds", round(float(total), 1)),
    ]
    rows += [(f"time_{lbl.replace(' ', '_')}_seconds", round(dt, 1))
             for lbl, dt in stages]
    return rows


def _write_manifest(target, rows, messages):
    """One small CSV per run beside the output: which EquiPop, which
    CRS (and whether it was auto-projected), which parameters, how
    many rows and cells, how long. Results should still be
    reproducible a year later without archaeology (John's C# runs
    kept a metadata text file - same idea, more complete)."""
    if not target:
        return
    try:
        import csv as _csv
        base = str(target)
        for ext in (".shp", ".csv", ".gdb"):
            if base.lower().endswith(ext):
                base = base[: -len(ext)]
        path = base + "_EquiPop_run.csv"
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = _csv.writer(fh)
            w.writerow(["item", "value"])
            for k, v in rows:
                w.writerow([k, "" if v is None else str(v)])
        messages.addMessage(f"Run manifest written to {path}")
    except Exception as exc:
        messages.addWarningMessage(
            f"Could not write the run manifest ({exc}).")


def _vt_rows(param):
    """Rows of a value table as lists of plain strings (v1.17).
    Pro hands back a list of lists whose members may be Value
    objects, so everything is normalised through _ref/str."""
    v = getattr(param, "value", None)
    if not v:
        return []
    out = []
    for row in v:
        cells = row if isinstance(row, (list, tuple)) else [row]
        out.append([("" if c is None else str(_ref(c))).strip()
                    for c in cells])
    return [r for r in out if any(r)]


def _distinct_values(layer, field, cap: int = 200):
    """The values a category field actually holds - so the dialog can
    OFFER them instead of asking the user to spell them (v1.17)."""
    if not (layer is not None and field):
        return []
    try:
        arr = arcpy.da.TableToNumPyArray(_ref(layer), [field],
                                         skip_nulls=False,
                                         null_value=-9999)
        vals = []
        seen = set()
        for v in arr[field]:
            t = str(v).strip()
            if t and t not in seen:
                seen.add(t)
                vals.append(t)
            if len(vals) >= cap:
                break
        return sorted(vals)
    except Exception:
        return []


def _byname(parameters):
    """Parameters by NAME, not position. Inserting one parameter used
    to shift every index after it (v1.16.6 - it has caused two bugs
    already); names cannot slip."""
    return {p.name: p for p in parameters}


def _txt(pm, name, default=""):
    p = pm.get(name)
    return (p.valueAsText or default) if p is not None else default


def _flag(pm, name):
    return str(_txt(pm, name)).lower() in ("true", "1", "yes")


def _num(pm, name, default=None):
    """Numbers from a dialog box, locale-proof (v1.16.7).

    Pro renders numbers in the USER's locale, so valueAsText returns
    '0,000001' on a Swedish machine and float() refuses it. The real
    value is on .value; the text is only a fallback, and there a
    lone comma is a decimal comma while several commas are thousands
    separators."""
    p = pm.get(name)
    if p is None:
        return default
    v = getattr(p, "value", None)
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    return _to_float(p.valueAsText, default)


def _to_float(text, default=None):
    t = str(text or "").strip()
    if not t:
        return default
    t = t.replace("\u00a0", "").replace(" ", "")
    if "," in t and "." in t:              # 1,234.56 -> 1234.56
        t = t.replace(",", "")
    elif t.count(",") == 1:                # 12,5 -> 12.5
        t = t.replace(",", ".")
    else:
        t = t.replace(",", "")
    try:
        return float(t)
    except ValueError:
        raise arcpy.ExecuteError(
            f"'{text}' is not a number. Use digits only - a decimal "
            "comma or point both work, e.g. 12,5 or 12.5.")


def _numlist(text):
    """A space/semicolon separated list of numbers, locale-proof:
    '344,5 500' and '344.5;500' both give [344.5, 500.0]."""
    out = []
    for tok in str(text or "").replace(";", " ").split():
        v = _to_float(tok)
        if v is not None:
            out.append(v)
    return out


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
    """Enable X/Y selectors when they matter; preguess; and CLEAR
    stale picks that Pro remembered from a previous layer (field-
    test finding: 'it seems to remember... a refresh will be
    needed')."""
    src = parameters[i_src].valueAsText or _COORD_AUTO
    is_attr = src == _COORD_ATTR
    val = parameters[i_layer].value
    is_table = False
    if val is not None:
        try:
            is_table = _kind(arcpy.Describe(val)) == "table"
        except Exception:
            pass
        try:
            names = set(_table_fields(val))
            for i in (i_x, i_y):
                pv = parameters[i].valueAsText
                if pv and pv not in names:
                    parameters[i].value = None    # stale: other layer
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


def _catalog_of(value):
    try:
        return getattr(arcpy.Describe(value), "catalogPath", "") or ""
    except Exception:
        return ""


def _clear_stale_fields(parameters, i_layer, idxs):
    """Field boxes remembered by Pro from ANOTHER layer are cleared
    (v1.16.3) - the coordinate trio got this in 1.16.2, every other
    field box gets it now."""
    val = parameters[i_layer].value
    if val is None:
        return
    try:
        have = set(_table_fields(val))
    except Exception:
        return
    for i in idxs:
        txt = parameters[i].valueAsText
        if not txt:
            continue
        picks = [p.strip("' ") for p in txt.split(";") if p.strip("' ")]
        keep = [p for p in picks if p in have]
        if len(keep) != len(picks):
            parameters[i].value = ";".join(keep) if keep else None


def _shared_messages(parameters, i_layer, i_src, i_x, i_y,
                     i_outtable, i_autoproj=None):
    """Dialog-time (pre-Run) validation shared by both machines: the
    loud refusals appear as red X:es IN the dialog (field-test
    finding A2), not as tracebacks after Run."""
    for p in parameters:
        try:
            p.clearMessage()
        except Exception:
            pass
    val = parameters[i_layer].value
    if val is None:
        return
    try:
        desc = arcpy.Describe(val)
        kind = _kind(desc)
    except Exception:
        return
    txt = _geographic_text(desc, "The input")
    if txt:
        auto_on = (i_autoproj is not None
                   and str(parameters[i_autoproj].valueAsText or "")
                   .lower() in ("true", "1", "yes"))
        # A ticked auto-project box must UNBLOCK the dialog - the
        # execution path honoured it while validation still refused,
        # so Run stayed greyed out (field-test finding).
        if auto_on and getattr(desc, "shapeType", None):
            parameters[i_layer].setWarningMessage(
                "Input is in degrees - it will be AUTO-PROJECTED to "
                f"{_utm_advice(desc)} for this analysis. The stored "
                "data is not modified.")
        else:
            parameters[i_layer].setErrorMessage(txt)
    src = parameters[i_src].valueAsText or _COORD_AUTO
    if kind == "table" and not (parameters[i_outtable].valueAsText):
        parameters[i_outtable].setErrorMessage(
            "Table input has no feature class to append to - set the "
            "output table (.csv). The results arrive there with your "
            "coordinates.")
    if kind == "table" or src == _COORD_ATTR:
        xf = parameters[i_x].valueAsText
        yf = parameters[i_y].valueAsText
        if not (xf and yf):
            gx = gy = None
            deg = False
            try:
                from equipop.io import guess_xy_fields
                gx, gy, deg = guess_xy_fields(_table_fields(val))
            except Exception:
                pass
            if deg:
                parameters[i_layer].setErrorMessage(
                    f"'{gx}'/'{gy}' look like DEGREES (lon/lat) - "
                    "EquiPop needs metres. Project the data first.")
            elif not (gx and gy):
                if not xf:
                    parameters[i_x].setErrorMessage(
                        "Pick the X field (easting) - the coordinate "
                        "columns could not be guessed. No renaming "
                        "needed.")
                if not yf:
                    parameters[i_y].setErrorMessage(
                        "Pick the Y field (northing).")


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
                 ["GPFeatureLayer", "GPTableView"])]
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
               _p("halflife", "Decay half-life in metres (one value "
                  "for everybody)", "GPDouble", required=False),
               _p("hlfield", "OR: half-life from a field - each point "
                  "keeps its own bandwidth (estimated median "
                  "distance, group potential...)", "Field",
                  required=False),
               _p("hlfromdist", "OR: self-calibrating - use each "
                  "point's own Dist_k as its half-life (enter the k "
                  "to calibrate on; urban form sets the bandwidth)",
                  "GPLong", required=False),
               _p("hlbins", "Bandwidth bins (variable half-life "
                  "only; more bins = finer, slower)", "GPLong",
                  required=False),
               _p("decayeps", "Decay cutoff - ignore weights below "
                  "this (smaller = wider search = slower; the "
                  "truncation distance is reported in the messages)",
                  "GPDouble", required=False),
               _p("catfield", "Category field (codes or names) - "
                  "builds population and groups from its VALUES",
                  "Field", required=False),
               _p("cattable", "Categories: one row per value - which "
                  "group it belongs to, and whether it counts as "
                  "population", "GPValueTable", required=False),
               _p("groupscount", "Category groups count", "GPString",
                  required=False),
               _p("barriertable", "Barriers: one row per point/line/"
                  "polygon layer or table of cells, with the field "
                  "holding its friction", "GPValueTable",
                  required=False),
               _p("barrierrasters", "Barrier rasters (cell value = "
                  "friction); combined with the rows above by the "
                  "same overlap rule", "DERasterDataset",
                  required=False, multiValue=True),
               _p("barrieragg", "Barrier overlap rule (features "
                  "sharing a cell)", "GPString", required=False),

               _p("dem", "Distance ingredient: elevation raster (DEM)",
                  ["DERasterDataset", "GPRasterLayer"],
                  required=False),
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
               _p("unit", "Cell size (m)", "GPDouble", required=False),
               _p("autoproj", "Auto-project degree data to a suitable "
                  "metric CRS (layers only - the fitting UTM zone is "
                  "computed from the data; input untouched)",
                  "GPBoolean", required=False),
               _p("shortnames", "Allow shortened field names when the "
                  "target is a shapefile (10-character cap; names "
                  "stay collision-free and the mapping is printed)",
                  "GPBoolean", required=False),
               _p("seed", "Random seed (only matters where "
                  "permutations are used; recorded in the manifest)",
                  "GPLong", required=False)]
        pm = _byname(ps)
        for nm in ("pop", "treat", "catfield"):
            pm[nm].parameterDependencies = ["layer"]
        pm["cattable"].columns = [["GPString", "Category value"],
                                  ["GPString", "Group name"],
                                  ["GPBoolean", "In population?"]]
        # v1.17.1: a GPComposite column took ArcGIS Pro down on Run
        # (the value table is serialised even when empty). Only
        # plain, long-supported column types here; rasters get their
        # own parameter below.
        pm["barriertable"].columns = [
            ["GPTableView", "Barrier layer or table"],
            ["Field", "Friction field"]]     # dropdown per row
        pm["groupscount"].filter.type = "ValueList"
        pm["groupscount"].filter.list = ["persons (weighted by the "
                                         "population field)",
                                         "places (rows)"]
        pm["groupscount"].value = "persons (weighted by the " \
                                  "population field)"
        pm["hlfield"].parameterDependencies = ["layer"]
        pm["hlbins"].value = 10
        # v1.17: collapsible sections instead of 29 boxes at once
        SECTION = {
            "coordsrc": "Coordinates", "xfield": "Coordinates",
            "yfield": "Coordinates", "autoproj": "Coordinates",
            "k": "Neighbourhood", "r": "Neighbourhood",
            "unit": "Neighbourhood", "model": "Neighbourhood",
            "halflife": "Neighbourhood", "hlfield": "Neighbourhood",
            "hlfromdist": "Neighbourhood", "hlbins": "Neighbourhood",
            "decayeps": "Neighbourhood",
            "pop": "Groups", "treat": "Groups",
            "catfield": "Groups", "cattable": "Groups",
            "groupscount": "Groups",
            "barriertable": "Barriers and terrain",
            "barrierrasters": "Barriers and terrain",
            "barrieragg": "Barriers and terrain",
            "dem": "Barriers and terrain", "tau": "Barriers and terrain",
            "roundtrip": "Barriers and terrain",
            "existing": "Output", "outmode": "Output",
            "outfc": "Output", "outtable": "Output",
            "shortnames": "Output", "seed": "Advanced",
        }
        for nm, cat in SECTION.items():
            if nm in pm:
                pm[nm].category = cat
        pm["model"].filter.type = "ValueList"
        pm["model"].filter.list = ["no decay", "negexp", "expnormal",
                                   "expsqrt", "lognormal", "power"]
        pm["model"].value = "no decay"
        pm["decayeps"].value = 1e-6
        pm["barrieragg"].filter.type = "ValueList"
        pm["barrieragg"].filter.list = _AGG_CHOICES
        pm["barrieragg"].value = _AGG_CHOICES[0]
        pm["existing"].filter.type = "ValueList"
        pm["existing"].filter.list = ["Overwrite", "Stop with a message"]
        pm["existing"].value = "Overwrite"
        pm["outmode"].filter.type = "ValueList"
        pm["outmode"].filter.list = ["Append to input",
                                     "New feature class"]
        pm["outmode"].value = "Append to input"
        pm["outtable"].direction = "Output"
        pm["unit"].value = 100.0
        return ps

    def updateParameters(self, parameters):
        pm = _byname(parameters)
        _trio_update(parameters, 0, 1, 2, 3)
        # offer the category field's OWN values in the table's first
        # column, so nothing has to be spelled by hand (v1.17.3)
        cat = _txt(pm, "catfield")
        tbl = pm.get("cattable")
        if cat and tbl is not None:
            vals = _distinct_values(pm["layer"].value, cat)
            try:
                if vals and getattr(tbl, "filters", None):
                    tbl.filters[0].type = "ValueList"
                    tbl.filters[0].list = vals
            except Exception:
                pass
        _clear_stale_fields(parameters, 0, [i for i, p in
                                            enumerate(parameters)
                                            if p.name in
                                            ("pop", "treat",
                                             "catfield")])
        decaying = _txt(pm, "model", "no decay") not in ("", "no decay")
        pm["halflife"].enabled = decaying
        pm["decayeps"].enabled = decaying
        bar_on = bool(_vt_rows(pm["barriertable"])
                      or _txt(pm, "barrierrasters"))
        pm["barrieragg"].enabled = bar_on
        ing = bar_on or bool(_txt(pm, "dem"))
        pm["tau"].enabled = ing
        pm["roundtrip"].enabled = ing
        pm["outfc"].enabled = _txt(pm, "outmode") == "New feature class"
        return

    def updateMessages(self, parameters):
        pm = _byname(parameters)
        idx = {p.name: i for i, p in enumerate(parameters)}
        _shared_messages(parameters, 0, 1, 2, 3, idx["outtable"],
                         idx["autoproj"])
        target = (_txt(pm, "outfc")
                  if _txt(pm, "outmode").startswith("New")
                  and _txt(pm, "outfc")
                  else _catalog_of(pm["layer"].value))
        if not _flag(pm, "shortnames"):
            txt = _refuse_shp_overflow(target, _predict_result_fields(
                "counts", _txt(pm, "k"), _txt(pm, "r"), _txt(pm, "tau"),
                [f for f in _txt(pm, "treat").split(";") if f], [], [],
                bool(_txt(pm, "halflife")
                     and _txt(pm, "model", "no decay") != "no decay"),
                bool(_vt_rows(pm["barriertable"])
                     or _txt(pm, "barrierrasters")
                     or _txt(pm, "dem"))))
            if txt:
                pm["outmode"].setErrorMessage(
                    txt + " Or tick 'Allow shortened field names'.")
        return

    def execute(self, parameters, messages):
        pm = _byname(parameters)
        model = _txt(pm, "model", "no decay")
        decaying = model not in ("", "no decay")
        _run_tool("counts", pm["layer"].value, messages,
                  coord_source=_txt(pm, "coordsrc") or None,
                  x_field=_txt(pm, "xfield") or None,
                  y_field=_txt(pm, "yfield") or None,
                  weight_field=_txt(pm, "pop") or None,
                  treat_fields=[f for f in _txt(pm, "treat").split(";")
                                if f],
                  k_text=_txt(pm, "k"), r_text=_txt(pm, "r"),
                  half_life=(_num(pm, "halflife", 0.0) or 0.0)
                  if decaying else 0.0,
                  decay_model=model if decaying else "negexp",
                  decay_eps=_num(pm, "decayeps", 1e-6) or 1e-6,
                  half_life_field=_txt(pm, "hlfield") or None,
                  half_life_from_dist=_num(pm, "hlfromdist") or None,
                  decay_bins=int(_num(pm, "hlbins", 10) or 10),
                  seed=_num(pm, "seed"),
                  cat_field=_txt(pm, "catfield") or None,
                  cat_rows=_vt_rows(pm["cattable"]),
                  groups_count=_txt(pm, "groupscount", "persons"),
                  barrier_rows=(_vt_rows(pm["barriertable"])
                                + [[r, None] for r in
                                   (_txt(pm, "barrierrasters")
                                    .split(";")) if r.strip()]),
                  barrier_agg=_txt(pm, "barrieragg"),
                  extra_dem=_ref(pm["dem"].value) or None,
                  tau_text=_txt(pm, "tau"),
                  roundtrip=_flag(pm, "roundtrip"),
                  existing=_txt(pm, "existing", "Overwrite"),
                  out_mode=_txt(pm, "outmode", "Append to input"),
                  out_fc=_txt(pm, "outfc") or None,
                  out_table=_txt(pm, "outtable") or None,
                  unit=_num(pm, "unit", 100.0) or 100.0,
                  auto_project=_flag(pm, "autoproj"),
                  short_names=_flag(pm, "shortnames"))


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
                 ["GPFeatureLayer", "GPTableView"])]
        _coord_trio(ps)
        ps += [_p("fullpop", "Full population field - persons per "
                  "point (empty = one each); k is measured against "
                  "this", "Field", required=False),
               _p("values", "Numeric value fields (e.g. income, rent, "
                  "age)", "Field", multiValue=True),
               _p("measures", "Measures to calculate (none ticked = "
                  "mean, median, gini)", "GPString",
                  multiValue=True, required=False),
               _p("pcts", "Percentiles (plain numbers, e.g. 10 25 75 "
                  "90)", "GPString", required=False),
               _p("k", "k values", "GPString"),
               _p("r", "Radii in metres", "GPString", required=False),
               _p("existing", "If result fields already exist",
                  "GPString", required=False),
               _p("outmode", "Output", "GPString", required=False),
               _p("outfc", "New feature class (name/path - use a "
                  "file geodatabase for unlimited field names)",
                  "DEFeatureClass", required=False),
               _p("outtable", "Output table (.csv) - for TABLE inputs",
                  "DEFile", required=False),
               _p("unit", "Cell size (m)", "GPDouble", required=False),
               _p("autoproj", "Auto-project degree data to a suitable "
                  "metric CRS (layers only - the fitting UTM zone is "
                  "computed from the data; input untouched)",
                  "GPBoolean", required=False),
               _p("shortnames", "Allow shortened field names when the "
                  "target is a shapefile (10-character cap; names "
                  "stay collision-free and the mapping is printed)",
                  "GPBoolean", required=False)]
        ps[4].parameterDependencies = ["layer"]
        ps[5].parameterDependencies = ["layer"]
        ps[6].filter.type = "ValueList"
        ps[6].filter.list = _MEASURES
        ps[6].value = "mean;median;gini"
        ps[7].value = "10 25 75 90"
        pm2 = _byname(ps)
        for nm, cat in {"coordsrc": "Coordinates",
                        "xfield": "Coordinates",
                        "yfield": "Coordinates",
                        "autoproj": "Coordinates",
                        "k": "Neighbourhood", "r": "Neighbourhood",
                        "unit": "Neighbourhood",
                        "fullpop": "Values and measures",
                        "values": "Values and measures",
                        "measures": "Values and measures",
                        "pcts": "Values and measures",
                        "existing": "Output", "outmode": "Output",
                        "outfc": "Output", "outtable": "Output",
                        "shortnames": "Output"}.items():
            if nm in pm2:
                pm2[nm].category = cat
        # v1.17: no preset value on the measures list - Pro merged the
        # default with new ticks, so unticking mean/median/gini did
        # not take effect (field finding). Empty now MEANS the
        # default trio, stated in the label.
        ps[6].value = None
        ps[10].filter.type = "ValueList"
        ps[10].filter.list = ["Overwrite", "Stop with a message"]
        ps[10].value = "Overwrite"
        ps[11].filter.type = "ValueList"
        ps[11].filter.list = ["Append to input", "New feature class"]
        ps[11].value = "Append to input"
        ps[13].direction = "Output"
        ps[14].value = 100.0
        return ps

    def updateParameters(self, parameters):
        _trio_update(parameters, 0, 1, 2, 3)
        _clear_stale_fields(parameters, 0, (4, 5))
        chosen = (parameters[6].valueAsText or "").lower()
        parameters[7].enabled = "percentiles" in chosen
        parameters[12].enabled = (parameters[11].valueAsText
                                  == "New feature class")
        return

    def updateMessages(self, parameters):
        _shared_messages(parameters, 0, 1, 2, 3, 13, 15)
        v = [p.valueAsText or "" for p in parameters]
        target = (v[12] if v[11].startswith("New") and v[12]
                  else _catalog_of(parameters[0].value))
        wanted = []
        for mtxt in [m.strip("' ") for m in v[6].split(";") if m]:
            ml = mtxt.lower()
            if ml == "percentiles":
                wanted += [f"p{q}" for q in
                           (v[7] or "").replace(",", " ").split()]
            elif ml:
                wanted.append(_MEASURE_KEY.get(ml, ml))
        if not (v[16] or "").lower() in ("true", "1", "yes"):
            txt = _refuse_shp_overflow(target, _predict_result_fields(
                "stats", v[8], v[9], "", [],
                [f for f in v[5].split(";") if f],
                wanted or ["mean", "median", "gini"], False, False))
            if txt:
                parameters[11].setErrorMessage(txt + " Or tick "
                                               "'Allow shortened "
                                               "field names'.")
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
                  existing=v[10] or "Overwrite",
                  out_mode=v[11] or "Append to input",
                  out_fc=v[12] or None,
                  out_table=v[13] or None,
                  unit=_num({p.name: p for p in parameters}, "unit",
                            100.0) or 100.0,
                  auto_project=(v[15] or "").lower() in
                  ("true", "1", "yes"),
                  short_names=(v[16] or "").lower() in
                  ("true", "1", "yes"))
