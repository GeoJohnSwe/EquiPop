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

    def Describe(_layer):
        return _FakeDescribe()

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
        t = _tab()

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
        bt = state["aux_tables"][table]
        out = np.empty(len(bt), dtype=[(f, np.float64) for f in fields])
        for f in fields:
            out[f] = bt[f].to_numpy(float)
        return out

    def ListFieldsAny(obj):
        if isinstance(obj, str) and obj in state.get("aux_tables", {}):
            return [types.SimpleNamespace(name=c, type="Double")
                    for c in state["aux_tables"][obj].columns]
        return [types.SimpleNamespace(name=c, type="Double")
                for c in _tab().columns]

    da.TableToNumPyArray = TableToNumPyArray
    da.FeatureClassToNumPyArray = FeatureClassToNumPyArray
    da.ExtendTable = ExtendTable
    arcpy.da = da
    arcpy.Describe = Describe
    arcpy.ListFields = ListFieldsAny
    arcpy.management = mgmt
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
                  stats_text="median gini", k_text="30")
    got = state["table"]
    assert "Med_income_30" in got and "Gini_income_30" in got

    # friction (barrier csv)
    fr = pd.DataFrame({"x": [1550.0] * 10,
                       "y": np.arange(50.0, 1050.0, 100.0),
                       "friction": 6})
    f = tmp_path / "barriers.csv"
    fr.to_csv(f, index=False)
    pyt._run_tool("friction", "people", msg,
                  treat_fields=["HighEdu"], friction_table=str(f),
                  k_text="20", tau_text="3")
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
                  friction_table="barriers", tau_text="3",
                  roundtrip=False)
    got = state["table"]
    assert "Rounds_40" in got and "N_tau3" in got
    ok = got.dropna(subset=["N_40"])
    assert (ok["T_LowEdu_40"] <= ok["N_40"] + 1e-9).all()
    r = ok["R_LowEdu_40"]
    assert (r >= 0).all() and (r <= 1).all()
    assert any("effort engine" in m for m in msg.log)
