# -*- coding: utf-8 -*-
"""
EquiPop.pyt - EquiPop for ArcGIS Pro (#21). Python 3 / Pro only.

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
                       optional distance decay (unbounded sums)
  2 Value Statistics - mean / median / Gini of numeric fields
                       (income!) among the k nearest
  3 Friction Effort  - rounds and effort isochrones over a barrier
                       table (rivers, cuttings)

All results are appended to the input layer as new double fields,
row-aligned; rows with missing coordinates receive Null.
"""

import numpy as np

import arcpy


# ----------------------------------------------------------- shared glue
def _field(name):
    """ArcGIS-safe field name."""
    out = "".join(ch if ch.isalnum() else "_" for ch in str(name))
    return (out[:60] or "X")


def _run_tool(engine, layer, messages, treat_fields=(), value_fields=(),
              weight_field=None, k_text="", r_text="", tau_text="",
              stats_text="", half_life=0.0, decay_model="negexp",
              friction_table=None, unit=100.0,
              cat_field=None, pop_values_text="", treat_values_text="",
              existing="Overwrite", out_mode="Append to input",
              out_fc=None):
    """The single glue path all three tools share (stub-validated)."""
    from equipop.stata_bridge import dispatch

    desc = arcpy.Describe(layer)
    oid = desc.OIDFieldName
    if getattr(desc, "shapeType", "") != "Point":
        raise arcpy.ExecuteError("EquiPop needs a POINT layer "
                                 "(one point per person/row).")
    if str(getattr(desc, "dataType", "")).lower().startswith("shape") or \
            str(getattr(desc, "catalogPath", "")).endswith(".shp"):
        messages.addWarningMessage(
            "Shapefile input: field names truncate to 10 characters - "
            "a file geodatabase layer is strongly recommended.")

    if out_mode.startswith("New"):
        if not out_fc:
            raise arcpy.ExecuteError("New feature class chosen - "
                                     "please set the output name/path.")
        arcpy.management.CopyFeatures(layer, out_fc)
        messages.addMessage(f"Copied input to {out_fc}; results go "
                            "there, input untouched.")
        layer = out_fc
        desc = arcpy.Describe(layer)
        oid = desc.OIDFieldName

    fields = [oid, "SHAPE@X", "SHAPE@Y"] + list(treat_fields) \
        + list(value_fields) + ([weight_field] if weight_field else []) \
        + ([cat_field] if cat_field else [])
    arr = arcpy.da.FeatureClassToNumPyArray(
        layer, fields, skip_nulls=False, null_value=np.nan)
    x = np.asarray(arr["SHAPE@X"], float)
    y = np.asarray(arr["SHAPE@Y"], float)
    n_missing = int((~(np.isfinite(x) & np.isfinite(y))).sum())
    if n_missing:
        messages.addMessage(f"{n_missing} rows with missing coordinates"
                            " -> Null results (EquiPop convention).")

    if cat_field:
        from equipop.categorical import categories_to_binary
        pop_vals = [v.strip() for v in pop_values_text.replace(";", ",")
                    .split(",") if v.strip()] or None
        pop_mask, cat_treats = categories_to_binary(
            np.asarray(arr[cat_field]), treat_values_text or "",
            pop_values=pop_vals)
        x = np.where(pop_mask, x, np.nan)   # excluded rows -> Null,
        y = np.where(pop_mask, y, np.nan)   # the standard convention
        messages.addMessage(
            f"Category mode: population {int(pop_mask.sum())} rows; "
            f"treatments: {', '.join(cat_treats) or '(none)'}")

    kw = dict(unit_size=float(unit))
    kw["k_values"] = [int(t) for t in k_text.split()] or None
    kw["r_values"] = [float(t) for t in r_text.split()] or None
    if tau_text:
        kw["tau_values"] = [float(t) for t in tau_text.split()]
    if treat_fields:
        kw["treat"] = {f: np.asarray(arr[f], float) for f in treat_fields}
    if cat_field and cat_treats:
        kw.setdefault("treat", {}).update(cat_treats)
    if weight_field:
        kw["weight"] = np.asarray(arr[weight_field], float)
    if engine == "counts" and half_life and half_life > 0:
        kw["half_life_m"] = float(half_life)
        kw["decay_model"] = decay_model
    if engine == "stats":
        vals = {f: np.asarray(arr[f], float) for f in value_fields}
        kw["values"] = vals
        wanted = stats_text.split() or ["mean", "median", "gini"]
        kw["stats"] = {f: wanted for f in vals}
    if engine == "friction" and friction_table:
        kw["friction_file"] = str(friction_table)

    res = dispatch(engine, x, y, **kw)

    dtype = [(str(oid), np.int64)] + [(_field(c), np.float64)
                                      for c in res]
    out = np.empty(len(x), dtype=dtype)
    out[str(oid)] = np.asarray(arr[oid], np.int64)
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


class Toolbox:
    def __init__(self):
        self.label = "EquiPop"
        self.alias = "equipop"
        self.tools = [CountsShares, ValueStatistics, FrictionEffort]


class CountsShares:
    def __init__(self):
        self.label = "1. Counts and Shares (k / radius / decay)"
        self.description = (
            "Egocentric neighbourhoods around every point. OUTPUT "
            "FIELDS: N_k = persons among the k nearest (whole squares "
            "enter, so slightly above k is honest); T_<g>_k and "
            "R_<g>_k = group count and share; Dist_k = the RADIUS in "
            "metres that the k-search needed (k fixes population, "
            "geography floats); N_r### = persons within the radius. "
            "DATA SHAPES: one point per PERSON (group fields are 0/1, "
            "leave Population empty) or one point per PLACE carrying "
            "many persons (set Population = total-persons field; group "
            "fields then hold group COUNTS). Coordinates must be "
            "METRIC (metres, e.g. SWEREF 99), not degrees.")

    def getParameterInfo(self):
        ps = [_p("layer", "Point layer (people or places)",
                 "GPFeatureLayer"),
              _p("pop", "Population field - total persons at this "
                 "point (empty if each point is one person)", "Field",
                 required=False),
              _p("treat", "Group count fields - persons per group at "
                 "this point (0/1 if points are individuals)", "Field",
                 required=False, multiValue=True),
              _p("k", "k values (space-separated, e.g. 200 1600)",
                 "GPString", required=False),
              _p("r", "Radii in metres (e.g. 500 1000)", "GPString",
                 required=False),
              _p("model", "Distance decay", "GPString", required=False),
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
              _p("existing", "If result fields already exist",
                 "GPString", required=False),
              _p("outmode", "Output", "GPString", required=False),
              _p("outfc", "New feature class (name/path)",
                 "DEFeatureClass", required=False),
              _p("unit", "Cell size (m)", "GPDouble", required=False)]
        for i in (1, 2, 7):
            ps[i].parameterDependencies = ["layer"]
        ps[5].filter.type = "ValueList"
        ps[5].filter.list = ["no decay", "negexp", "expnormal",
                             "expsqrt", "lognormal", "power"]
        ps[5].value = "no decay"
        ps[10].filter.type = "ValueList"
        ps[10].filter.list = ["Overwrite", "Stop with a message"]
        ps[10].value = "Overwrite"
        ps[11].filter.type = "ValueList"
        ps[11].filter.list = ["Append to input", "New feature class"]
        ps[11].value = "Append to input"
        ps[13].value = 100.0
        return ps

    def updateParameters(self, parameters):
        parameters[6].enabled = (parameters[5].valueAsText
                                 not in (None, "", "no decay"))
        parameters[12].enabled = (parameters[11].valueAsText
                                  == "New feature class")
        return

    def execute(self, parameters, messages):
        v = [p.valueAsText or "" for p in parameters]
        model = v[5] or "no decay"
        _run_tool("counts", parameters[0].value, messages,
                  weight_field=v[1] or None,
                  treat_fields=[f for f in v[2].split(";") if f],
                  k_text=v[3], r_text=v[4],
                  half_life=float(v[6] or 0) if model != "no decay"
                  else 0.0,
                  decay_model=model if model != "no decay" else
                  "negexp",
                  cat_field=v[7] or None, pop_values_text=v[8],
                  treat_values_text=v[9], existing=v[10] or
                  "Overwrite", out_mode=v[11] or "Append to input",
                  out_fc=v[12] or None, unit=float(v[13] or 100))


class ValueStatistics:
    def __init__(self):
        self.label = "2. Value Statistics (numeric fields among the k nearest)"
        self.description = (
            "Mean / median / Gini / SD of any NUMERIC fields (income, "
            "rent, age...) computed among each point's k nearest "
            "persons. Output: Mean_<f>_k, Med_<f>_k, Gini_<f>_k plus "
            "Nv_<f>_k = how many of the k had a usable value (the "
            "honesty column - a median on 30 valid values is a "
            "rumour). Missing values still count as NEIGHBOURS but "
            "contribute no value, the register convention.")

    def getParameterInfo(self):
        ps = [_p("layer", "Point layer (people)", "GPFeatureLayer"),
              _p("values", "Numeric value fields (e.g. income, rent, "
                 "age)", "Field", multiValue=True),
              _p("stats", "Statistics (space-separated)", "GPString",
                 required=False),
              _p("k", "k values", "GPString"),
              _p("r", "Radii in metres", "GPString", required=False),
              _p("unit", "Cell size (m)", "GPDouble", required=False)]
        ps[1].parameterDependencies = ["layer"]
        ps[2].value = "mean median gini"
        ps[5].value = 100.0
        return ps

    def execute(self, parameters, messages):
        v = [p.valueAsText or "" for p in parameters]
        _run_tool("stats", parameters[0].value, messages,
                  value_fields=[f for f in v[1].split(";") if f],
                  stats_text=v[2], k_text=v[3], r_text=v[4],
                  unit=float(v[5] or 100))


class FrictionEffort:
    def __init__(self):
        self.label = "3. Effort and Isochrones (friction barriers)"
        self.description = ("Rounds to reach k people and effort "
                            "isochrones, over a barrier table with "
                            "x, y, friction columns.")

    def getParameterInfo(self):
        ps = [_p("layer", "Point layer (people)", "GPFeatureLayer"),
              _p("treat", "Group field (0/1)", "Field", required=False),
              _p("friction", "Barrier table (csv with x,y,friction)",
                 "DEFile"),
              _p("k", "k values", "GPString", required=False),
              _p("tau", "Effort budgets in rounds (e.g. 3 8)",
                 "GPString", required=False),
              _p("unit", "Cell size (m)", "GPDouble", required=False)]
        ps[1].parameterDependencies = ["layer"]
        ps[5].value = 100.0
        return ps

    def execute(self, parameters, messages):
        v = [p.valueAsText or "" for p in parameters]
        _run_tool("friction", parameters[0].value, messages,
                  treat_fields=[v[1]] if v[1] else [],
                  friction_table=v[2], k_text=v[3], tau_text=v[4],
                  unit=float(v[5] or 100))
