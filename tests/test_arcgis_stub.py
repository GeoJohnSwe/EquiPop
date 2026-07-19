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

    def FeatureClassToNumPyArray(_layer, fields, skip_nulls=False,
                                 null_value=np.nan):
        t = state["table"]
        dtype = [(f, np.float64) if f != "OBJECTID" else (f, np.int64)
                 for f in fields]
        out = np.empty(len(t), dtype=dtype)
        for f in fields:
            col = t[f].to_numpy()
            out[f] = np.where(pd.isna(col), null_value, col) \
                if f != "OBJECTID" else col
        return out

    def ExtendTable(_layer, key, array, akey):
        t = state["table"].set_index(key)
        add = pd.DataFrame(array).set_index(akey)
        for c in add.columns:
            t[c] = add[c]
        state["table"] = t.reset_index()

    class ExecuteError(Exception):
        pass

    class Parameter:
        def __init__(self, **kw):
            self.__dict__.update(kw)
            self.filter = types.SimpleNamespace(type=None, list=[])
            self.value = None

    da.FeatureClassToNumPyArray = FeatureClassToNumPyArray
    da.ExtendTable = ExtendTable
    arcpy.da = da
    arcpy.Describe = Describe
    arcpy.ExecuteError = ExecuteError
    arcpy.Parameter = Parameter
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
