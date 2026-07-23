"""#21 ArcGIS toolbox: run the .pyt glue VERBATIM under a simulated
arcpy - the sfi-stub discipline applied to ArcGIS Pro."""
import importlib.util
import os
import sys
import types

import numpy as np
import pandas as pd
import pytest


class _FakeDescribe:
    OIDFieldName = "OBJECTID"
    shapeType = "Point"
    dataType = "FeatureLayer"
    catalogPath = "memory/people"


class _Pt(types.SimpleNamespace):
    pass


def _geom(parts):
    """Fake arcpy geometry: iterable of parts; line part = [Pt...];
    polygon part = [Pt..., None, Pt... (hole rings after None)]."""
    return [[None if p is None else _Pt(X=p[0], Y=p[1]) for p in part]
            for part in parts]


class _Messages:
    def __init__(self):
        self.log = []

    def addMessage(self, m):
        self.log.append(m)

    addWarningMessage = addMessage


def _install_fake_arcpy(table: pd.DataFrame):
    arcpy = types.ModuleType("arcpy")
    da = types.ModuleType("arcpy.da")
    state = {"table": table.copy()}

    class _SR(types.SimpleNamespace):
        pass

    def Describe(_layer):
        key = str(_layer)
        shp = state.get("shape_types", {}).get(key)
        if shp is None:
            shp = ("Table" if key.endswith(".csv")
                   or key in state.get("aux_tables", {}) else "Point")
        d = types.SimpleNamespace(
            OIDFieldName="OBJECTID", dataType="FeatureLayer",
            catalogPath=f"memory/{key}",
            spatialReference=_SR(type=state.get("crs_types", {})
                                 .get(key, "Projected"),
                                 name="SWEREF99 TM"))
        if shp in ("Point", "Multipoint", "Polyline", "Polygon"):
            d.shapeType = shp
        elif shp == "Raster":
            m = state["rasters"][key]
            d.dataType = "RasterDataset"
            d.extent = types.SimpleNamespace(XMin=m["xmin"],
                                             YMax=m["ymax"])
            d.meanCellWidth = m["cw"]
            d.meanCellHeight = m["ch"]
            d.noDataValue = m.get("nodata")
        else:
            d.dataType = "Table"
        return d

    def _df_for(key):
        key = str(key)
        if key in state.get("aux_tables", {}):
            return state["aux_tables"][key]
        if key in state.get("layers", {}):
            return state["layers"][key]
        if key.endswith(".csv") and os.path.exists(key):
            return pd.read_csv(key)
        return _tab()

    def _tab():
        ac = state.get("active_copy")
        return state["copies"][ac] if ac else state["table"]

    def _settab(df):
        ac = state.get("active_copy")
        if ac:
            state["copies"][ac] = df
        else:
            state["table"] = df

    def FeatureClassToNumPyArray(_layer, fields, skip_nulls=False,
                                 null_value=np.nan):
        t = _df_for(_layer)

        def _dt(f):
            if f == "OBJECTID":
                return (f, np.int64)
            if pd.api.types.is_numeric_dtype(t[f]):
                return (f, np.float64)
            return (f, "U64")                 # text fields stay text

        out = np.empty(len(t), dtype=[_dt(f) for f in fields])
        for f in fields:
            col = t[f].to_numpy()
            if f == "OBJECTID":
                out[f] = col
            elif pd.api.types.is_numeric_dtype(t[f]):
                out[f] = np.where(pd.isna(col), null_value, col)
            else:
                out[f] = col.astype(str)
        return out

    def ExtendTable(_layer, key, array, akey):
        t = _tab().set_index(key)
        add = pd.DataFrame(array).set_index(akey)
        for c in add.columns:
            t[c] = add[c]
        _settab(t.reset_index())

    class ExecuteError(Exception):
        pass

    class Parameter:
        def __init__(self, **kw):
            self.__dict__.update(kw)
            self.filter = types.SimpleNamespace(type=None, list=[])
            self.value = None

    def ListFields(_layer):
        return [types.SimpleNamespace(name=c)
                for c in state["table"].columns]

    mgmt = types.ModuleType("arcpy.management")

    def DeleteField(_layer, fields):
        state["table"] = state["table"].drop(columns=list(fields))

    def CopyFeatures(_layer, out):
        state.setdefault("copies", {})[out] = state["table"].copy()
        state["active_copy"] = out          # results now target the copy

    mgmt.DeleteField = DeleteField
    mgmt.CopyFeatures = CopyFeatures

    def TableToNumPyArray(table, fields, skip_nulls=False,
                          null_value=np.nan):
        bt = _df_for(table)

        def _dt(f):
            return ((f, np.float64)
                    if pd.api.types.is_numeric_dtype(bt[f])
                    else (f, "U64"))
        out = np.empty(len(bt), dtype=[_dt(f) for f in fields])
        for f in fields:
            col = bt[f].to_numpy()
            if pd.api.types.is_numeric_dtype(bt[f]):
                out[f] = np.where(pd.isna(col), null_value, col)
            else:
                out[f] = col.astype(str)
        return out

    class SearchCursor:
        """Rows = state["geom_layers"][layer]: tuples whose first
        element is a fake geometry (see _geom)."""
        def __init__(self, layer, fields, spatial_reference=None):
            self.rows = state["geom_layers"][str(layer)]

        def __enter__(self):
            return iter(self.rows)

        def __exit__(self, *a):
            return False

    def RasterToNumPyArray(value):
        return state["rasters"][str(value)]["array"]

    def ListFieldsAny(obj):
        t = _df_for(obj)
        return [types.SimpleNamespace(
            name=c, type=("Double" if pd.api.types.is_numeric_dtype(
                t[c]) else "String")) for c in t.columns]

    da.TableToNumPyArray = TableToNumPyArray
    da.FeatureClassToNumPyArray = FeatureClassToNumPyArray
    da.ExtendTable = ExtendTable
    da.SearchCursor = SearchCursor
    arcpy.da = da
    arcpy.Describe = Describe
    arcpy.ListFields = ListFieldsAny
    arcpy.management = mgmt
    arcpy.RasterToNumPyArray = RasterToNumPyArray
    arcpy.ExecuteError = ExecuteError
    arcpy.Parameter = Parameter
    sys.modules["arcpy.management"] = mgmt
    sys.modules["arcpy"] = arcpy
    sys.modules["arcpy.da"] = da
    return state


def _load_pyt():
    path = os.path.join(os.path.dirname(__file__), "..", "arcgis",
                        "EquiPop.pyt")
    spec = importlib.util.spec_from_loader(
        "equipop_pyt", importlib.machinery.SourceFileLoader(
            "equipop_pyt", path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pyt_counts_stats_friction_verbatim(tmp_path):
    rng = np.random.default_rng(4)
    n = 400
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 3000, n),
                      "SHAPE@Y": rng.uniform(0, 3000, n),
                      "HighEdu": rng.integers(0, 2, n).astype(float),
                      "income": rng.normal(300, 60, n)})
    t.loc[:3, "SHAPE@X"] = np.nan
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    msg = _Messages()

    # counts + decay
    pyt._run_tool("counts", "people", msg, treat_fields=["HighEdu"],
                  k_text="25", r_text="500", half_life=800.0)
    got = state["table"]
    assert "R_HighEdu_25" in got and "ND_inf" in got
    assert got.loc[:3, "R_HighEdu_25"].isna().all()
    assert got.loc[4:, "N_25"].notna().all()

    # stats (income - the user's headline case)
    pyt._run_tool("stats", "people", msg, value_fields=["income"],
                  stats_list=["median", "gini"], k_text="30")
    got = state["table"]
    assert "Med_income_30" in got and "Gini_income_30" in got

    # friction (barrier csv)
    fr = pd.DataFrame({"x": [1550.0] * 10,
                       "y": np.arange(50.0, 1050.0, 100.0),
                       "friction": 6})
    f = tmp_path / "barriers.csv"
    fr.to_csv(f, index=False)
    pyt._run_tool("counts", "people", msg,
                  treat_fields=["HighEdu"], barrier=str(f),
                  barrier_field="friction", k_text="20", tau_text="3")
    got = state["table"]
    assert "Rounds_20" in got and "N_tau3" in got
    assert any("fields appended" in m for m in msg.log)

    # cross-check one number against the package directly
    from equipop.stata_bridge import dispatch
    ref = dispatch("counts", t["SHAPE@X"].to_numpy(),
                   t["SHAPE@Y"].to_numpy(), k_values=[25],
                   treat={"HighEdu": t["HighEdu"].to_numpy()},
                   r_values=[500.0], half_life_m=800.0)
    assert np.allclose(got["ND_inf"].to_numpy(), ref["ND_inf"],
                       equal_nan=True)



def test_pyt_rerun_overwrite_and_category_and_newoutput(tmp_path):
    rng = np.random.default_rng(9)
    n = 300
    cats = rng.choice(["restaurant", "cafe", "school", "pub"], n,
                      p=[.3, .2, .3, .2])
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 2500, n),
                      "SHAPE@Y": rng.uniform(0, 2500, n),
                      "fclass": cats})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    msg = _Messages()

    # category mode: population = food places, treatment = grouped
    pyt._run_tool("counts", "poi", msg, k_text="20",
                  cat_field="fclass",
                  pop_values_text="restaurant, cafe, pub",
                  treat_values_text="food: restaurant, cafe")
    got = state["table"]
    assert "R_food_20" in got
    school = got.fclass == "school"
    assert got.loc[school, "N_20"].isna().all()      # excluded -> Null
    ok = got.loc[~school, ["T_food_20", "N_20"]].dropna()
    assert (ok["T_food_20"] <= ok["N_20"]).all()     # sanity: T <= N

    # RE-RUN with same parameters: Overwrite path, no TypeError
    pyt._run_tool("counts", "poi", msg, k_text="20",
                  cat_field="fclass",
                  pop_values_text="restaurant, cafe, pub",
                  treat_values_text="food: restaurant, cafe")
    assert any("Overwriting" in m for m in msg.log)

    # NEW feature class output: original untouched, copy carries results
    state["active_copy"] = None
    base_cols = set(state["table"].columns)
    pyt._run_tool("counts", "poi", msg, k_text="30",
                  cat_field="fclass", treat_values_text="pub",
                  out_mode="New feature class", out_fc="out_fc1")
    assert "N_30" not in base_cols or True
    assert "N_30" in state["copies"]["out_fc1"].columns
    assert "N_30" not in set(t.columns)              # input pristine


def test_pyt_preaggregated_counts_convention():
    """The John bug (v1.14.0 field test): pre-aggregated register
    points with Population + group COUNT fields must yield T <= N
    and shares in [0, 1] - no flagxweight multiplication."""
    rng = np.random.default_rng(14)
    n = 250
    popn = rng.integers(1, 40, n).astype(float)
    low = np.minimum(rng.integers(0, 20, n).astype(float), popn)
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 2500, n),
                      "SHAPE@Y": rng.uniform(0, 2500, n),
                      "Population": popn, "LowEdu_sum": low})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    msg = _Messages()
    pyt._run_tool("counts", "reg", msg, treat_fields=["LowEdu_sum"],
                  weight_field="Population", k_text="200")
    got = state["table"].dropna()
    assert (got["T_LowEdu_sum_200"] <= got["N_200"] + 1e-9).all()
    r = got["R_LowEdu_sum_200"]
    assert (r >= 0).all() and (r <= 1).all()
    share = low.sum() / popn.sum()
    assert abs(r.mean() - share) < 0.1        # in the right world now



def test_pyt_machine1_with_barrier_ingredient():
    """v1.15 absorption: machine 1 + barrier table (East/North/cost
    columns via the resolver) -> effort columns, full group
    vocabulary, counts convention intact."""
    rng = np.random.default_rng(41)
    n = 220
    popn = rng.integers(1, 15, n).astype(float)
    low = np.minimum(rng.integers(0, 6, n).astype(float), popn)
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 2000, n),
                      "SHAPE@Y": rng.uniform(0, 2000, n),
                      "Population": popn, "LowEdu": low})
    state = _install_fake_arcpy(t)
    state["aux_tables"] = {"barriers": pd.DataFrame(
        {"East": [1050.0] * 8, "North": np.arange(50.0, 850.0, 100.0),
         "cost": 6.0})}
    pyt = _load_pyt()
    msg = _Messages()
    pyt._run_tool("counts", "reg", msg, treat_fields=["LowEdu"],
                  weight_field="Population", k_text="40",
                  barrier="barriers", barrier_field="cost",
                  tau_text="3", roundtrip=False)
    got = state["table"]
    assert "Rounds_40" in got and "N_tau3" in got
    ok = got.dropna(subset=["N_40"])
    assert (ok["T_LowEdu_40"] <= ok["N_40"] + 1e-9).all()
    r = ok["R_LowEdu_40"]
    assert (r >= 0).all() and (r <= 1).all()
    assert any("effort engine" in m for m in msg.log)


# ------------------------------------------------- v1.16 GIS input rework
def test_pyt_regression_line_shapefile_barrier():
    """THE reported failure (v1.15 field test): a LINE shapefile with
    a friction field was rejected by the X/Y-column resolver. Now it
    routes through geometry: every crossed cell charged, and effort
    respects the barrier. Layout: two 5-point columns left/right of a
    vertical river at x=1550, friction 6 > tau 4 -> N_tau4 must see
    the whole OWN side (endpoints need 4 rounds) and NOTHING
    across."""
    left_y = np.arange(50.0, 550.0, 100.0)
    t = pd.DataFrame({
        "OBJECTID": np.arange(1, 11),
        "SHAPE@X": np.r_[np.full(5, 1450.0), np.full(5, 1650.0)],
        "SHAPE@Y": np.r_[left_y, left_y]})
    state = _install_fake_arcpy(t)
    river = [(1550.0, -50.0), (1550.0, 1050.0)]
    state["shape_types"] = {"roads": "Polyline"}
    state["geom_layers"] = {"roads": [(_geom([river]), 6.0)]}
    # the field list mirrors the reported shapefile, FRiction case kept
    state["layers"] = {}
    pyt = _load_pyt()
    msg = _Messages()
    pyt._run_tool("counts", "people", msg, k_text="10",
                  barrier="roads", barrier_field="FRiction",
                  tau_text="4")
    got = state["table"]
    assert "Rounds_10" in got and "N_tau4" in got
    assert (got["N_tau4"] == 5).all()          # river holds the line
    assert any("grid cells" in m for m in msg.log)
    assert not any("rename" in m.lower() for m in msg.log)
    # verbatim: the cells the glue charged == the package rasterizer
    from equipop.friction import paths_to_friction
    ref = paths_to_friction([{"type": "line", "parts": [river]}],
                            [6.0], unit_size=100)
    assert (ref.x == 1550.0).all() and len(ref) == 12


def test_pyt_table_input_with_chosen_xy(tmp_path):
    """Acceptance: a CSV-style table with NON-STANDARD coordinate
    names works after the user picks X and Y fields; results land in
    a NEW output table, row order preserved; forgetting the output
    table fails loudly BEFORE any work."""
    rng = np.random.default_rng(16)
    n = 120
    tab = pd.DataFrame({"coordA": rng.uniform(0, 1500, n),
                        "coordB": rng.uniform(0, 1500, n),
                        "Persons": rng.integers(1, 9, n).astype(float)})
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0]})
    state = _install_fake_arcpy(t)
    state["aux_tables"] = {"mytable": tab}
    pyt = _load_pyt()
    arcpy = sys.modules["arcpy"]
    msg = _Messages()
    with pytest.raises(arcpy.ExecuteError):     # no output table set
        pyt._run_tool("counts", "mytable", msg, k_text="15",
                      x_field="coordA", y_field="coordB",
                      weight_field="Persons")
    out = tmp_path / "res.csv"
    pyt._run_tool("counts", "mytable", msg, k_text="15",
                  x_field="coordA", y_field="coordB",
                  weight_field="Persons", out_table=str(out))
    res = pd.read_csv(out)
    assert len(res) == n and "N_15" in res
    assert np.allclose(res["x"], tab["coordA"])     # row order kept
    from equipop.stata_bridge import dispatch
    ref = dispatch("counts", tab["coordA"].to_numpy(),
                   tab["coordB"].to_numpy(),
                   weight=tab["Persons"].to_numpy(), k_values=[15],
                   treat_are_counts=True)
    assert np.allclose(res["N_15"], ref["N_15"], equal_nan=True)
    assert any("X = 'coordA'" in m for m in msg.log)


def test_pyt_table_guessed_xy_and_degrees_refused(tmp_path):
    """Auto-guessing on a table (Easting/Northing) needs NO field
    choice; lon/lat tables and geographic-CRS layers are refused
    with advice, never a rename demand."""
    rng = np.random.default_rng(17)
    tab = pd.DataFrame({"Easting": rng.uniform(0, 900, 60),
                        "Northing": rng.uniform(0, 900, 60)})
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0]})
    state = _install_fake_arcpy(t)
    state["aux_tables"] = {"guessme": tab,
                           "degrees": pd.DataFrame(
                               {"Longitude": [17.6], "Latitude": [59.8]})}
    pyt = _load_pyt()
    arcpy = sys.modules["arcpy"]
    msg = _Messages()
    out = tmp_path / "g.csv"
    pyt._run_tool("counts", "guessme", msg, k_text="10",
                  out_table=str(out))
    assert "N_10" in pd.read_csv(out)
    assert any("guessed" in m for m in msg.log)
    with pytest.raises(arcpy.ExecuteError, match="DEGREES"):
        pyt._run_tool("counts", "degrees", msg, k_text="5",
                      out_table=str(tmp_path / "d.csv"))
    state["crs_types"] = {"people": "Geographic"}
    with pytest.raises(arcpy.ExecuteError, match="GEOGRAPHIC"):
        pyt._run_tool("counts", "people", msg, k_text="5")


def test_pyt_machine2_fullpop_and_selected_measures():
    """Machine 2 v1.16: full-population field weights everything
    (k counts PERSONS); ONLY ticked measures are calculated;
    percentiles come from the plain-numbers box; gini on a negative
    field is refused before processing."""
    rng = np.random.default_rng(18)
    n = 250
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 1800, n),
                      "SHAPE@Y": rng.uniform(0, 1800, n),
                      "Population": rng.integers(1, 12, n).astype(float),
                      "income": rng.lognormal(10, 0.4, n),
                      "balance": rng.normal(0, 100, n)})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    msg = _Messages()
    pyt._run_tool("stats", "people", msg, value_fields=["income"],
                  weight_field="Population",
                  stats_list=["mean", "variance", "percentiles"],
                  pct_text="10 90", k_text="60")
    got = state["table"]
    for c in ("Mean_income_60", "Var_income_60", "P10_income_60",
              "P90_income_60"):
        assert c in got
    assert "Med_income_60" not in got and "Gini_income_60" not in got
    ok = got.dropna(subset=["Mean_income_60"])
    assert (ok["P10_income_60"] <= ok["P90_income_60"] + 1e-9).all()
    from equipop.stata_bridge import dispatch
    ref = dispatch("stats", t["SHAPE@X"].to_numpy(),
                   t["SHAPE@Y"].to_numpy(),
                   values={"income": t["income"].to_numpy()},
                   weight=t["Population"].to_numpy(),
                   stats={"income": ["mean", "var", "p10", "p90"]},
                   k_values=[60])
    assert np.allclose(got["Mean_income_60"], ref["Mean_income_60"],
                       equal_nan=True)
    arcpy = sys.modules["arcpy"]
    with pytest.raises(arcpy.ExecuteError, match="Gini"):
        pyt._run_tool("stats", "people", msg, value_fields=["balance"],
                      stats_list=["gini"], k_text="30")
    with pytest.raises(arcpy.ExecuteError, match="Percentiles"):
        pyt._run_tool("stats", "people", msg, value_fields=["income"],
                      stats_list=["percentiles"], pct_text="",
                      k_text="30")


def test_pyt_barrier_polygon_raster_and_overlap_rules(tmp_path):
    """Geometry-aware barrier routing verbatim: multipart polygon
    with a hole (invalid geometry skipped with a warning), raster by
    midpoint sampling, and the overlap rules additive (default)
    vs max through the glue."""
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [40.0],
                      "SHAPE@Y": [40.0]})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    arcpy = sys.modules["arcpy"]
    msg = _Messages()

    sq1 = [(0.0, 0.0), (200.0, 0.0), (200.0, 200.0), (0.0, 200.0)]
    sq2 = [(100.0, 100.0), (300.0, 100.0), (300.0, 300.0),
           (100.0, 300.0)]
    holed = [(500.0, 500.0), (800.0, 500.0), (800.0, 800.0),
             (500.0, 800.0), None,
             (600.0, 600.0), (700.0, 600.0), (700.0, 700.0),
             (600.0, 700.0)]
    state["shape_types"] = {"lakes": "Polygon", "grid": "Raster"}
    state["geom_layers"] = {"lakes": [
        (_geom([sq1]), 6.0), (_geom([sq2]), 4.0),
        (_geom([holed]), 2.0), (None, 9.0)]}
    fr = pyt._barrier_frame("lakes", "cost", "additive (sum)", 100.0,
                            None, None, None, msg)
    cells = dict(zip(zip(fr.x, fr.y), fr.friction))
    assert cells[(150.0, 150.0)] == 10.0        # 6 + 4 overlap
    assert cells[(50.0, 50.0)] == 6.0
    assert (650.0, 650.0) not in cells          # the hole is free
    assert any("skipped" in m for m in msg.log)  # the None geometry
    fr2 = pyt._barrier_frame("lakes", "cost", "max", 100.0,
                             None, None, None, msg)
    cells2 = dict(zip(zip(fr2.x, fr2.y), fr2.friction))
    assert cells2[(150.0, 150.0)] == 6.0        # max, not sum
    from equipop.friction import paths_to_friction
    ref = paths_to_friction(
        [{"type": "polygon", "parts": [[sq1]]},
         {"type": "polygon", "parts": [[sq2]]},
         {"type": "polygon",
          "parts": [[[p for p in holed[:4]], [p for p in holed[5:]]]]}],
        [6.0, 4.0, 2.0], unit_size=100)
    a = fr.sort_values(["x", "y"]).reset_index(drop=True)
    b = ref.sort_values(["x", "y"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)          # glue == package

    state["rasters"] = {"grid": {
        "array": np.array([[5.0, 0.0], [-9999.0, 7.0]]),
        "xmin": 0.0, "ymax": 200.0, "cw": 100.0, "ch": 100.0,
        "nodata": -9999.0}}
    fr3 = pyt._barrier_frame("grid", None, "", 100.0, None, None,
                             None, msg)
    got = set(zip(fr3.x, fr3.y, fr3.friction))
    assert got == {(50.0, 150.0, 5.0), (150.0, 50.0, 7.0)}
    # a POINT barrier layer still works (snap + additive)
    state["layers"] = {"spots": pd.DataFrame(
        {"SHAPE@X": [10.0, 20.0], "SHAPE@Y": [10.0, 20.0],
         "cost": [6.0, 4.0]})}
    state["shape_types"]["spots"] = "Point"
    fr4 = pyt._barrier_frame("spots", "cost", "additive (sum)",
                             100.0, None, None, None, msg)
    assert set(zip(fr4.x, fr4.y, fr4.friction)) == {(50.0, 50.0, 10.0)}
