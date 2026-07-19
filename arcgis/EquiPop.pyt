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
              friction_table=None, unit=100.0):
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

    fields = [oid, "SHAPE@X", "SHAPE@Y"] + list(treat_fields) \
        + list(value_fields) + ([weight_field] if weight_field else [])
    arr = arcpy.da.FeatureClassToNumPyArray(
        layer, fields, skip_nulls=False, null_value=np.nan)
    x = np.asarray(arr["SHAPE@X"], float)
    y = np.asarray(arr["SHAPE@Y"], float)
    n_missing = int((~(np.isfinite(x) & np.isfinite(y))).sum())
    if n_missing:
        messages.addMessage(f"{n_missing} rows with missing coordinates"
                            " -> Null results (EquiPop convention).")

    kw = dict(unit_size=float(unit))
    kw["k_values"] = [int(t) for t in k_text.split()] or None
    kw["r_values"] = [float(t) for t in r_text.split()] or None
    if tau_text:
        kw["tau_values"] = [float(t) for t in tau_text.split()]
    if treat_fields:
        kw["treat"] = {f: np.asarray(arr[f], float) for f in treat_fields}
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
    arcpy.da.ExtendTable(layer, oid, out, str(oid))
    messages.addMessage(f"EquiPop: {len(res)} fields appended "
                        f"({', '.join(_field(c) for c in res)}).")


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
        self.description = ("Egocentric neighbourhoods: N, group T/R "
                            "shares, Dist; optional decayed sums.")

    def getParameterInfo(self):
        ps = [_p("layer", "Point layer (people)", "GPFeatureLayer"),
              _p("treat", "Group fields (0/1 or counts)", "Field",
                 required=False, multiValue=True),
              _p("weight", "Weight field (persons per row)", "Field",
                 required=False),
              _p("k", "k values (space-separated, e.g. 200 1600)",
                 "GPString", required=False),
              _p("r", "Radii in metres (e.g. 500 1000)", "GPString",
                 required=False),
              _p("halflife", "Decay half-life in metres (0 = off)",
                 "GPDouble", required=False),
              _p("model", "Decay model", "GPString", required=False),
              _p("unit", "Cell size (m)", "GPDouble", required=False)]
        for f in (1, 2):
            ps[f].parameterDependencies = ["layer"]
        ps[6].filter.type = "ValueList"
        ps[6].filter.list = ["negexp", "expnormal", "expsqrt",
                             "lognormal", "power"]
        ps[6].value = "negexp"
        ps[7].value = 100.0
        return ps

    def execute(self, parameters, messages):
        v = [p.valueAsText or "" for p in parameters]
        _run_tool("counts", parameters[0].value, messages,
                  treat_fields=[f for f in v[1].split(";") if f],
                  weight_field=v[2] or None, k_text=v[3], r_text=v[4],
                  half_life=float(v[5] or 0), decay_model=v[6] or
                  "negexp", unit=float(v[7] or 100))


class ValueStatistics:
    def __init__(self):
        self.label = "2. Value Statistics (income among the k nearest)"
        self.description = ("Mean / median / Gini of numeric fields "
                            "in each egocentric neighbourhood.")

    def getParameterInfo(self):
        ps = [_p("layer", "Point layer (people)", "GPFeatureLayer"),
              _p("values", "Value fields (e.g. income)", "Field",
                 multiValue=True),
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
        self.label = "3. Friction Effort (rivers and barriers)"
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
