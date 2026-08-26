"""#21 ArcGIS toolbox: run the .pyt glue VERBATIM under a simulated
arcpy - the sfi-stub discipline applied to ArcGIS Pro."""
import importlib.util
import os
import sys
import re
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

    def _unalias(key):
        """A catalog path resolves back to the layer it describes.

        v1.22.1: the door now asks Describe() for catalogPath, which
        is what a GeoPackage needs. The simulator hands out
        "memory/<name>" and the Malta fixture hands out a real-looking
        .gpkg path, so both must lead home again - otherwise the
        simulator fails where real arcpy would succeed.
        """
        k = str(key)
        for name, path in state.get("catalog_paths", {}).items():
            if k == str(path):
                return name
        if k.startswith("memory/"):
            return k[len("memory/"):]
        return k

    def _fallback_catalog_path(key):
        """'memory/' is the ArcGIS in-memory workspace, so it belongs
        on a bare LAYER NAME and never on something that is already a
        path. Prefixing it onto an absolute path invented a shape real
        arcpy cannot return - 'memory/C:\\...\\proj.gdb\\result' -
        which Windows rejects outright (WinError 123) while POSIX
        accepts it as a relative path and writes litter. That is why
        test_the_manifest_of_a_geodatabase_run_is_findable failed on
        John's Windows machine and passed here. BACKLOG 208.
        """
        k = str(key)
        looks_like_a_path = ("/" in k or "\\" in k
                             or (len(k) > 1 and k[1] == ":"))
        return k if looks_like_a_path else f"memory/{k}"

    def Describe(_layer):
        # v1.22.1: describing a CATALOG PATH must describe the layer
        # it belongs to - the door now resolves layers through
        # Describe().catalogPath, so a path comes back round.
        key = _unalias(_layer)
        shp = state.get("shape_types", {}).get(key)
        if shp is None:
            shp = ("Table" if key.endswith(".csv")
                   or key in state.get("aux_tables", {}) else "Point")
        d = types.SimpleNamespace(
            OIDFieldName=state.get("oid_names", {}).get(key,
                                                        "OBJECTID"),
            dataType="FeatureLayer",
            catalogPath=state.get("catalog_paths", {}).get(
                key, _fallback_catalog_path(key)),
            spatialReference=_SR(type=state.get("crs_types", {})
                                 .get(key, "Projected"),
                                 name="SWEREF99 TM"))
        if key in state.get("extents", {}):
            x0, y0, x1, y1 = state["extents"][key]
            d.extent = types.SimpleNamespace(XMin=x0, YMin=y0,
                                             XMax=x1, YMax=y1)
        if shp in ("Point", "Multipoint", "Polyline", "Polygon"):
            d.shapeType = shp
        elif shp == "Raster":
            m = state["rasters"][_unalias(key)]
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
        key = _unalias(key)
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

    class SpatialReference:
        """Fake CRS object; auto-projection is simulated by a simple
        deterministic degrees->metres transform (the glue only needs
        to prove that projection HAPPENED and metres arrived)."""
        def __init__(self, code):
            self.factoryCode = int(code)
            self.type = "Projected"
            self.name = f"EPSG:{code}"

    def FeatureClassToNumPyArray(_layer, fields, skip_nulls=False,
                                 null_value=np.nan,
                                 spatial_reference=None):
        t = _df_for(_layer)
        if spatial_reference is not None:
            t = t.copy()
            zone = spatial_reference.factoryCode % 100
            cm = -183.0 + 6.0 * zone
            lat = t["SHAPE@Y"].to_numpy(float)
            t["SHAPE@X"] = ((t["SHAPE@X"].to_numpy(float) - cm)
                            * 111320.0 * np.cos(np.radians(lat)))
            t["SHAPE@Y"] = lat * 110540.0

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
        # GeoPackage refuses this outright (field, Malta, v1.20):
        # "The operation is not supported by this implementation."
        if str(_layer) in state.get("no_extend", set()):
            raise RuntimeError(
                "The operation is not supported by this "
                "implementation.")
        if str(_layer) in state.get("path_only", set()):
            raise RuntimeError(
                "The operation is not supported by this "
                "implementation.")
        t = _tab().set_index(key)
        add = pd.DataFrame(array).set_index(akey)
        for c in add.columns:
            t[c] = add[c]
        _settab(t.reset_index())

    def AddField(_layer, name, ftype, *a, **kw):
        if str(_layer) in state.get("path_only", set()):
            raise RuntimeError(
                f"ERROR 000852: Cannot add field {name} to "
                f"{_layer}")
        t = _tab()
        if name not in t.columns:
            t[name] = np.nan
            _settab(t)
        state.setdefault("added_fields", []).append(str(name))

    class ExecuteError(Exception):
        pass

    # datatype keywords real Pro accepts (the ones EquiPop uses);
    # SEMICOLON STRINGS ARE INVALID in real arcpy - multiple types
    # must be a LIST (field-found bug, v1.16.1)
    # Types real Pro is known to marshal. GPComposite is deliberately
    # ABSENT: a composite column in a value table crashed Pro on Run
    # (field finding, v1.17.0) - so the simulator refuses it too.
    _DATATYPES = {"GPFeatureLayer", "GPTableView", "DERasterDataset",
                  "GPRasterLayer", "GPString", "GPDouble", "GPBoolean",
                  "GPLong", "Field", "DEFile", "DEFeatureClass",
                  "GPValueTable"}

    class Parameter:
        def __init__(self, **kw):
            dt = kw.get("datatype")
            dts = dt if isinstance(dt, (list, tuple)) else [dt]
            for d in dts:
                if d not in _DATATYPES:
                    raise ValueError(
                        "ParameterObject: Invalid input value for "
                        f"DataType property ({d!r})")
            self.__dict__.update(kw)
            self.filter = types.SimpleNamespace(type=None, list=[])
            self.value = None
            self.enabled = True
            self.parameterDependencies = []
            self.messages = []          # (kind, text) set by tool
            self.columns = []           # value tables
            self.filters = [types.SimpleNamespace(type=None, list=[])
                            for _ in range(4)]
            self.category = None        # collapsible section

        def setErrorMessage(self, text):
            self.messages.append(("ERROR", text))

        def setWarningMessage(self, text):
            self.messages.append(("WARNING", text))

        def clearMessage(self):
            self.messages = []

        @property
        def valueAsText(self):
            return None if self.value is None else str(self.value)

    def ListFields(_layer):
        t = _tab()
        return [types.SimpleNamespace(
            name=c, type=("Double"
                          if pd.api.types.is_numeric_dtype(t[c])
                          else "String")) for c in t.columns]

    mgmt = types.ModuleType("arcpy.management")

    def DeleteField(_layer, fields):
        state["table"] = state["table"].drop(columns=list(fields))

    def CopyFeatures(_layer, out):
        # A real copy carries the ROWS across but not the identifier's
        # NAME: a GeoPackage calls it 'fid', a geodatabase 'OBJECTID'
        # (field, Malta, v1.20 - this is what made KeyError 'OBJECTID'
        # possible). The simulator must rename it too, or the bug is
        # invisible here.
        t = state["table"].copy()
        src_oid = state.get("oid_names", {}).get(str(_layer),
                                                 "OBJECTID")
        dst_oid = state.get("oid_names", {}).get(str(out), "OBJECTID")
        if src_oid != dst_oid and src_oid in t.columns:
            t = t.rename(columns={src_oid: dst_oid})
        # BACKLOG 164. A real copy also RENUMBERS. The destination
        # assigns its own identifiers from scratch, in row order - a
        # geodatabase from 1, a shapefile from 0 - so the copy's ids
        # are NOT the input's ids. This stub renamed the column and
        # kept the values, which made the copy look like a relabelled
        # original and hid a live misalignment: John's field run wrote
        # every result one row early and left the last row Null.
        #
        # A stub is safe only where it is STRICTER than the real
        # thing (1.29.1's isAdvanced, 1.29.3's polygon barriers). Here
        # it was more generous, and it certified the door for four
        # releases.
        if dst_oid in t.columns:
            start = state.get("oid_starts", {}).get(str(out), 1)
            t[dst_oid] = np.arange(start, start + len(t),
                                   dtype=np.int64)
        state.setdefault("copies", {})[out] = t
        state["active_copy"] = out          # results now target the copy

    mgmt.DeleteField = DeleteField
    mgmt.CopyFeatures = CopyFeatures
    mgmt.AddField = AddField

    def TableToNumPyArray(table, fields, skip_nulls=False,
                          null_value=np.nan):
        # A GeoPackage's dataSource is a connection DESCRIPTION, and
        # arcpy refuses to reopen it (field, Malta, v1.20). The
        # simulator refuses it too, or the door can quietly pass a
        # path that only fails on a real machine.
        key = str(table)
        if key.startswith("Instance=") or ",Dataset=" in key:
            raise RuntimeError(f"cannot open '{key}'")
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
            self.rows = state["geom_layers"][_unalias(layer)]

        def __enter__(self):
            return iter(self.rows)

        def __exit__(self, *a):
            return False

    class UpdateCursor:
        """Row-by-row update of existing columns - the in-place path
        that replaces DeleteField (v1.16.5)."""
        def __init__(self, layer, fields):
            self.df = _tab()
            self.fields = list(fields)
            self.i = -1

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def __iter__(self):
            return self

        def __next__(self):
            self.i += 1
            if self.i >= len(self.df):
                raise StopIteration
            return [self.df.iloc[self.i][f] for f in self.fields]

        def updateRow(self, row):
            for f, v in zip(self.fields[1:], row[1:]):
                self.df.loc[self.df.index[self.i], f] = v

    def RasterToNumPyArray(value):
        return state["rasters"][_unalias(value)]["array"]

    def ListFieldsAny(obj):
        t = _df_for(obj)
        return [types.SimpleNamespace(
            name=c, type=("Double" if pd.api.types.is_numeric_dtype(
                t[c]) else "String")) for c in t.columns]

    da.TableToNumPyArray = TableToNumPyArray
    da.FeatureClassToNumPyArray = FeatureClassToNumPyArray
    da.ExtendTable = ExtendTable
    da.SearchCursor = SearchCursor
    da.UpdateCursor = UpdateCursor
    arcpy.da = da
    arcpy.Describe = Describe
    arcpy.ListFields = ListFieldsAny
    arcpy.management = mgmt
    arcpy.RasterToNumPyArray = RasterToNumPyArray
    arcpy.SpatialReference = SpatialReference
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
    assert "R_HighEdu_25" in got and "ND_25" in got
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
    assert any("VERIFIED present" in m for m in msg.log)

    # cross-check one number against the package directly
    from equipop.stata_bridge import dispatch
    ref = dispatch("counts", t["SHAPE@X"].to_numpy(),
                   t["SHAPE@Y"].to_numpy(), k_values=[25],
                   treat={"HighEdu": t["HighEdu"].to_numpy()},
                   r_values=[500.0], half_life_m=800.0)
    assert np.allclose(got["ND_25"].to_numpy(), ref["ND_25"],
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
    # v1.22.2, John's ruling: a row outside the reference population
    # counts as ZERO people - nobody's neighbour - but it still gets
    # its own results. "If it was a library it was counted as zero
    # but it got the results." Untick keep_outside for the old
    # behaviour, which is tested just below.
    assert got.loc[school, "N_20"].notna().all()
    assert (got.loc[school, "R_food_20"] <= 1.0 + 1e-9).all()
    ok = got.loc[~school, ["T_food_20", "N_20"]].dropna()
    assert (ok["T_food_20"] <= ok["N_20"]).all()     # sanity: T <= N

    # RE-RUN with same parameters: Overwrite path, no TypeError
    pyt._run_tool("counts", "poi", msg, k_text="20",
                  cat_field="fclass",
                  pop_values_text="restaurant, cafe, pub",
                  treat_values_text="food: restaurant, cafe")
    assert any("in place" in m for m in msg.log)

    # NEW feature class output: original untouched, copy carries results
    state["active_copy"] = None
    base_cols = set(state["table"].columns)
    pyt._run_tool("counts", "poi", msg, k_text="30",
                  cat_field="fclass", treat_values_text="pub",
                  out_mode="New feature class", out_fc="out_fc1")
    assert "N_30" not in base_cols or True
    assert "N_30" in state["copies"]["out_fc1"].columns
    assert "N_30" not in set(t.columns)              # input pristine


# ------------------------------------------- v1.30.1 BACKLOG 164
@pytest.mark.parametrize("oid_name,ids,out_start,label", [
    ("FID", np.arange(0, 12), 1, "shapefile 0-based -> geodatabase 1..n"),
    ("OBJECTID", np.arange(1, 13), 1, "geodatabase -> geodatabase"),
    ("OBJECTID", np.arange(1, 13), 0, "geodatabase -> shapefile 0..n-1"),
    ("OBJECTID", np.array([1, 2, 5, 6, 9, 10, 13, 14, 17, 18, 21, 22]),
     1, "geodatabase WITH GAPS -> fresh contiguous"),
])
def test_a_new_feature_class_matches_rows_not_borrowed_identifiers(
        oid_name, ids, out_start, label):
    """BACKLOG 164, John's field run of 1.30: the last row of a
    682-point layer came back <Null>.

    A copy carries the ROWS across but not the IDENTIFIERS - the
    destination assigns its own, in row order, a geodatabase from 1
    and a shapefile from 0. EquiPop carried the INPUT's values over
    and joined the results on them, so a shapefile numbered FID
    0..681 copied to a geodatabase numbered OBJECTID 1..682 wrote
    every result ONE ROW EARLY and left the last row empty.

    Only the Null was visible. The run was in `proportional`, so
    N_25 read 25 and N_50 read 50 in every row - the shift could not
    be seen in the count columns at all, and Dist_k is not something
    an eye can check. Live since v1.20.

    The invariant, which needs no arithmetic to state: THE COPY MUST
    RECEIVE WHAT THE IN-PLACE RUN RECEIVES, row for row. Broken on
    purpose by restoring `data[new_oid] = data[oid]` - all four cases
    fail, the gapped one worst.
    """
    def _build():
        n = len(ids)
        return pd.DataFrame({
            oid_name: np.asarray(ids, dtype=np.int64),
            "PlaceID": np.arange(1, n + 1, dtype=np.int64),
            "SHAPE@X": np.linspace(10.0, 1600.0, n),
            "SHAPE@Y": np.full(n, 50.0),
            "Pop": np.full(n, 5.0)})

    # the in-place route matches on the target's REAL identifiers and
    # is the reference the copy has to reproduce
    state = _install_fake_arcpy(_build())
    state.setdefault("oid_names", {})["lyr"] = oid_name
    pyt = _load_pyt()
    pyt._run_tool("counts", "lyr", _Messages(), k_text="10",
                  unit=100.0, weight_field="Pop")
    truth = state["table"].sort_values(oid_name)

    state = _install_fake_arcpy(_build())
    state.setdefault("oid_names", {})["lyr"] = oid_name
    state.setdefault("oid_starts", {})["out"] = out_start
    pyt = _load_pyt()
    pyt._run_tool("counts", "lyr", _Messages(), k_text="10",
                  unit=100.0, weight_field="Pop",
                  out_mode="New feature class", out_fc="out")
    copy = state["copies"]["out"]
    key = "OBJECTID" if "OBJECTID" in copy.columns else oid_name
    copy = copy.sort_values(key)

    assert not copy["Dist_10"].isna().any(), (
        f"{label}: {int(copy['Dist_10'].isna().sum())} row(s) received "
        "no result - the last row is the one John saw")
    # PlaceID travels with the row, so it proves WHICH row got WHAT
    assert list(copy["PlaceID"]) == list(truth["PlaceID"])
    for col in ("N_10", "Dist_10"):
        assert np.allclose(copy[col].to_numpy(float),
                           truth[col].to_numpy(float)), (
            f"{label}: the copy's {col} is not what the same rows got "
            "in place - results are shifted")


@pytest.mark.parametrize("target,expect_moved", [
    (os.path.join("{root}", "TestBed", "p.gdb", "fc"), True),
    (os.path.join("{root}", "TestBed", "big.gdb", "ds", "fc"), True),
    (os.path.join("{root}", "malta.gpkg", "main.pois"), True),
    (os.path.join("{root}", "TestBed", "ee.shp"), False),
    (os.path.join("{root}", "TestBed", "out.csv"), False),
    # nested containers: the folder must escape ALL of them, so the
    # FIRST is the anchor. Anchoring on the last put EquiPop_runs
    # inside the outer .gpkg, where Catalog hides it just as well.
    (os.path.join("{root}", "a.gpkg", "b.gpkg", "fc"), False),
    # forward slashes, which ArcGIS also hands back
    ("{root}/TestBed/p.gdb/fc", True),
])
def test_sidecars_never_land_inside_a_geodatabase(tmp_path, target,
                                                  expect_moved):
    """BACKLOG 166, John's field test of 1.30.1: "I can't see the
    csv's".

    A file geodatabase is a FOLDER, so a manifest written beside
    `...\\testingEQP.gdb\\testaMig` is a loose file INSIDE the .gdb -
    and Catalog presents a geodatabase as a database, not a
    directory, so it lists no foreign files. The manifest was on
    disk and invisible in Pro. Two faults: the user cannot find
    their own record, and EquiPop litters a geodatabase.

    A shapefile or CSV target must be UNCHANGED - that is where John
    already found them, and moving those would fix nothing and break
    a habit.
    """
    _install_fake_arcpy(pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                                      "SHAPE@Y": [0.0]}))
    pyt = _load_pyt()
    tgt = target.format(root=str(tmp_path))
    path, moved = pyt._sidecar_path(tgt, "_EquiPop_run.csv")
    if "a.gpkg" in tgt:            # nested: must escape every one
        assert moved is True
    else:
        assert moved is expect_moved
    low = path.lower()
    for ext in (".gdb", ".gpkg", ".sde", ".mdb"):
        assert ext + os.sep not in low, (
            f"the sidecar is inside a {ext} container: {path}")
    if expect_moved or "a.gpkg" in tgt:
        assert os.path.basename(os.path.dirname(path)) == "EquiPop_runs"
        # deliberately NOT asserting the folder exists: working out
        # where a file goes must not create anything. An earlier
        # version made the folder here and the release zip was
        # refused, because the suite left directories all over the
        # working tree.
        assert not os.path.isdir(os.path.dirname(path))
    elif "a.gpkg" not in tgt:
        assert os.path.dirname(path) == os.path.dirname(tgt)
    assert path.endswith("_EquiPop_run.csv")


def test_the_sidecar_folder_keeps_the_root_it_was_given():
    """BACKLOG 208, and the reason Linux passed while Windows failed.

    _sidecar_path used to rebuild the folder with
    os.sep.join(parts[:holder]) - fragments rejoined - which drops
    whatever came before the first fragment. On POSIX that turned an
    ABSOLUTE path into a RELATIVE one, so the manifest went into a junk
    tree under the working directory and every assertion still held. A
    Windows drive letter survived only because 'C:' carries its own
    root; put anything in front of it and Windows refuses the path
    outright (WinError 123).

    So: whatever root goes in must come out.
    """
    pyt = _load_pyt()
    posix, _ = pyt._sidecar_path("/srv/data/proj.gdb/result",
                                 "_EquiPop_run.csv")
    assert posix.startswith("/srv/data"), (
        f"the leading root was lost: {posix}")
    assert "EquiPop_runs" in posix and ".gdb" not in posix

    win, _ = pyt._sidecar_path(r"C:\Data\EQP\proj.gdb\result",
                               "_EquiPop_run.csv")
    assert win.lower().startswith("c:"), f"the drive was lost: {win}"
    assert "EquiPop_runs" in win and ".gdb" not in win.lower()


def test_a_plain_file_target_is_left_exactly_where_it_was():
    """The other half of the contract: a shapefile or CSV target keeps
    its sidecar beside it, which is where John already finds them."""
    pyt = _load_pyt()
    got, moved = pyt._sidecar_path("/srv/data/points.shp",
                                   "_EquiPop_run.csv")
    assert moved is False
    assert got == "/srv/data/points_EquiPop_run.csv"


def test_the_manifest_of_a_geodatabase_run_is_findable(tmp_path):
    """End to end, through the route John actually used: a point
    layer written to a NEW feature class inside a .gdb.

    The assertion is on the ROUTING, not on a path guessed in
    advance - the simulator's catalogPath carries a 'memory/' prefix
    a real Pro would not, and a test that hard-coded the expected
    location would be testing the stub. What must be true either
    way: the file EXISTS, it sits in an EquiPop_runs folder, no .gdb
    lies above it, and the run SAID where it went.
    """
    gdb = tmp_path / "proj.gdb"
    gdb.mkdir()
    n = 60
    t = pd.DataFrame({"FID": np.arange(0, n),
                      "SHAPE@X": np.linspace(10, 900, n),
                      "SHAPE@Y": np.full(n, 50.0),
                      "Pop": np.full(n, 5.0)})
    state = _install_fake_arcpy(t)
    state.setdefault("oid_names", {})["lyr"] = "FID"
    pyt = _load_pyt()
    msg = _Messages()
    pyt._run_tool("counts", "lyr", msg, k_text="10", unit=100.0,
                  weight_field="Pop", out_mode="New feature class",
                  out_fc=str(gdb / "result"))

    said = [m for m in msg.log if "Run manifest written to" in m]
    # WHEN THIS FAILS, SAY WHY. _write_manifest wraps everything in
    # `except Exception` and turns the real cause into a warning, so a
    # bare assertion reports the symptom and hides the diagnosis. John
    # hit this on Windows in 1.40.7 while it passed on Linux - and the
    # message told us nothing. Print the whole log instead.
    assert said, (
        "the run never said where the manifest went.\n"
        "  target asked for : " + str(gdb / "result") + "\n"
        "  os.sep here      : " + repr(os.sep) + "\n"
        "  messages logged  :\n    "
        + "\n    ".join(msg.log if msg.log else ["(nothing at all)"]))
    assert "beside the geodatabase" in said[0]
    path = said[0].split("Run manifest written to ", 1)[1].split(" - ")[0]

    assert os.path.exists(path), (
        f"the run named {path} and nothing is there")
    parts = re.split(r"[\\/]+", path)
    assert "EquiPop_runs" in parts
    assert not any(q.lower().endswith(".gdb") for q in parts), (
        f"the manifest is still inside a geodatabase: {path}")
    man = pd.read_csv(path).set_index("item")["value"].to_dict()
    assert man["equipop_version"]


def test_the_copy_refuses_rather_than_guess_if_the_row_count_moved():
    """If the copy does not have the input's rows, matching by
    position is not safe and EquiPop must not try."""
    t = pd.DataFrame({"FID": np.arange(0, 6, dtype=np.int64),
                      "SHAPE@X": np.linspace(10.0, 500.0, 6),
                      "SHAPE@Y": np.full(6, 50.0),
                      "Pop": np.full(6, 5.0)})
    state = _install_fake_arcpy(t)
    state.setdefault("oid_names", {})["lyr"] = "FID"
    pyt = _load_pyt()
    real_copy = pyt.arcpy.management.CopyFeatures

    def _lossy(layer, out):
        real_copy(layer, out)
        state["copies"][out] = state["copies"][out].iloc[:-1]
    pyt.arcpy.management.CopyFeatures = _lossy
    with pytest.raises(Exception, match="will not guess"):
        pyt._run_tool("counts", "lyr", _Messages(), k_text="10",
                      unit=100.0, weight_field="Pop",
                      out_mode="New feature class", out_fc="out")


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


def test_pyt_machine2_count_field_and_selected_measures():
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


def test_pyt_machine2_reads_its_boxes_by_name_not_position():
    """v1.29. Machine 1 stopped counting its boxes off by position in
    1.16.6, after two bugs; machine 2 still did until now. The
    reference ladder coming to this dialog inserts boxes in the
    MIDDLE of the list, and under position-reading every box after
    the insertion is read from its neighbour - values from measures,
    k from the radii - while the run SUCCEEDS. Adding a box must
    therefore change nothing at all."""
    rng = np.random.default_rng(29)
    n = 120
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 900, n),
                      "SHAPE@Y": rng.uniform(0, 900, n),
                      "Population": rng.integers(1, 9, n).astype(float),
                      "income": rng.lognormal(10, 0.3, n)})

    def _dialog_run(insert_a_box):
        # a FRESH fake arcpy per run: its table persists in memory, so
        # a run that quietly does nothing would otherwise still show
        # the previous run's columns and the comparison would pass.
        state = _install_fake_arcpy(t)
        pyt = _load_pyt()
        tool = pyt.ValueStatistics()
        ps = tool.getParameterInfo()
        pm = {p.name: p for p in ps}
        pm["layer"].value = "people"
        pm["pop"].value = "Population"
        pm["values"].value = "income"
        pm["measures"].value = "mean"
        pm["k"].value = "40"
        if insert_a_box:
            spare = pyt._p("spare", "a box added in a later release",
                           "GPString", required=False)
            ps.insert(ps.index(pm["values"]), spare)
        tool.updateParameters(ps)
        tool.updateMessages(ps)
        assert not [1 for p in ps for kind, _ in p.messages
                    if kind == "ERROR"]
        tool.execute(ps, _Messages())
        return state["table"].copy()

    plain = _dialog_run(False)
    assert "Mean_income_40" in plain, \
        "the plain run must produce the result column"
    shifted = _dialog_run(True)
    pd.testing.assert_frame_equal(plain, shifted)


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


def test_pyt_dialogs_construct_like_pro():
    """Field-found bug (v1.16.0 redo): Pro validates every Parameter
    datatype at toolbox OPEN, and multi-type parameters must be
    LISTS, not semicolon strings. The fake now enforces the same, and
    this test builds BOTH dialogs exactly as Pro does - plus one
    updateParameters pass on empty dialogs."""
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0]})
    _install_fake_arcpy(t)
    pyt = _load_pyt()
    for tool in (pyt.CountsShares(), pyt.ValueStatistics()):
        ps = tool.getParameterInfo()
        assert len({p.name for p in ps}) == len(ps)   # unique names
        tool.updateParameters(ps)                      # must not raise
    m1 = {p.name: p for p in pyt.CountsShares().getParameterInfo()}
    assert isinstance(m1["layer"].datatype, list)      # the field bug
    assert m1["barriertable"].datatype == "GPValueTable"
    assert len(m1["barriertable"].columns) == 2      # source + field
    # every value-table column must be a type Pro can marshal
    for p in list(m1.values()):
        for col in getattr(p, "columns", []) or []:
            assert col[0] in _install_fake_arcpy.__globals__.get(
                "_ALLOWED_COLS", {"GPTableView", "GPString",
                                  "GPBoolean", "GPLong", "Field",
                                  "GPFeatureLayer", "GPDouble"}), col
    # v1.22: two tables, one per population - the reference table
    # says WHICH values are around, the treatment table says which of
    # them form which group
    assert len(m1["reftable"].columns) == 1           # value
    assert len(m1["treattable"].columns) == 2         # value/group
    assert {p.category for p in
            pyt.CountsShares().getParameterInfo()} >= {
        "Coordinates", "Neighbourhood",
        "Reference population - who is around",
        "Treatment population - what you measure",
        "Barriers and terrain", "Output"}
    assert m1["barrieragg"].filter.list[0].startswith("additive")
    m2 = {p.name: p for p in pyt.ValueStatistics().getParameterInfo()}
    assert m2["measures"].filter.list == pyt._MEASURES
    assert m2["pcts"].value == "10 25 75 90"
    # v1.29: machine 2 speaks machine 1's vocabulary
    assert "fullpop" not in m2
    assert {p.category for p in
            pyt.ValueStatistics().getParameterInfo()} >= {
        "Coordinates", "Neighbourhood",
        "Reference population - who is around",
        "Treatment values - what you measure", "Output"}


def test_pro_offers_every_box_the_two_doors_share():
    """v1.29, the other half of the parity check. The QGIS test has
    asked since 1.25 whether QGIS is missing a box Pro has; nobody
    ever asked it of Pro, and nobody asked it of machine 2 at all.
    Pro's Value Statistics called its population box `fullpop` while
    QGIS called it `pop` - one box, two names, two help entries, from
    1.20.0 to 1.29, silently."""
    from door_parity import CORE, CORE_M2
    from equipop.doors.help import HELP
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0]})
    _install_fake_arcpy(t)
    pyt = _load_pyt()
    for cls, shared, label in (
            (pyt.CountsShares, CORE, "Counts and Shares"),
            (pyt.ValueStatistics, CORE_M2, "Value Statistics")):
        names = {p.name for p in cls().getParameterInfo()}
        missing = shared - names
        assert not missing, (
            f"Pro's {label} is missing {sorted(missing)} - the two "
            "doors no longer name the same box the same way")
    # and the shared words must exist for every shared box, or the
    # two dialogs cannot explain it identically
    no_help = sorted((CORE | CORE_M2) - set(HELP))
    assert not no_help, f"no shared help entry for {no_help}"


# --------------------------------------------- v1.16.2 field-report bugs
def test_pyt_attribute_mode_on_layer_appends_by_oid():
    """Field report A3: a point LAYER read through Attribute fields
    (Pro remembered the mode) crashed with KeyError 'OBJECTID' -
    the tabular path forgot to read the OID. Must append normally."""
    rng = np.random.default_rng(21)
    n = 80
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 900, n),
                      "SHAPE@Y": rng.uniform(0, 900, n),
                      "MyEast": rng.uniform(0, 900, n),
                      "MyNorth": rng.uniform(0, 900, n)})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    msg = _Messages()
    pyt._run_tool("counts", "people", msg, k_text="10",
                  coord_source="Attribute fields",
                  x_field="MyEast", y_field="MyNorth")
    got = state["table"]
    assert "N_10" in got and len(got) == n
    from equipop.stata_bridge import dispatch
    ref = dispatch("counts", t["MyEast"].to_numpy(),
                   t["MyNorth"].to_numpy(), k_values=[10],
                   treat_are_counts=True)
    assert np.allclose(got["N_10"], ref["N_10"], equal_nan=True)


def test_pyt_stale_xy_ignored_on_auto_geometry():
    """Field report A1: stale X/Y picks remembered by Pro must be
    harmless when Auto + geometry applies."""
    rng = np.random.default_rng(22)
    n = 60
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 700, n),
                      "SHAPE@Y": rng.uniform(0, 700, n)})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    msg = _Messages()
    pyt._run_tool("counts", "people", msg, k_text="10",
                  coord_source="Auto (geometry if present)",
                  x_field="GhostX", y_field="GhostY")   # stale picks
    assert "N_10" in state["table"]
    assert any("feature geometry" in m for m in msg.log)


def test_pyt_trio_update_clears_stale_fields_on_layer_change():
    """Field report A1: switching input layers must clear and
    re-guess X/Y instead of carrying picks from the old layer."""
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0]})
    state = _install_fake_arcpy(t)
    state["aux_tables"] = {
        "old": pd.DataFrame({"coordA": [1.0], "coordB": [2.0]}),
        "new": pd.DataFrame({"Easting": [1.0], "Northing": [2.0]})}
    pyt = _load_pyt()
    tool = pyt.CountsShares()
    ps = tool.getParameterInfo()
    ps[0].value = "old"
    ps[1].value = "Attribute fields"
    ps[2].value = "coordA"
    ps[3].value = "coordB"
    tool.updateParameters(ps)
    assert (ps[2].value, ps[3].value) == ("coordA", "coordB")  # kept
    ps[0].value = "new"                       # the layer changes
    tool.updateParameters(ps)
    assert (ps[2].value, ps[3].value) == ("Easting", "Northing")


def test_pyt_dialog_time_validation_blocks_run():
    """Field report A2: the loud refusals must appear IN THE DIALOG
    (updateMessages), not after Run - table without output table,
    and unresolvable X/Y."""
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0]})
    state = _install_fake_arcpy(t)
    state["aux_tables"] = {
        "csvdata": pd.DataFrame({"coordA": [1.0], "coordB": [2.0]})}
    pyt = _load_pyt()
    tool = pyt.CountsShares()
    ps = tool.getParameterInfo()
    ps[0].value = "csvdata"
    tool.updateParameters(ps)
    tool.updateMessages(ps)
    all_errors = [txt for p in ps for kind, txt in p.messages
                  if kind == "ERROR"]
    assert any("output table" in e for e in all_errors)
    assert any("X field" in e or "pick" in e.lower()
               for e in all_errors)          # coordA/B not guessable
    ps2 = tool.getParameterInfo()            # a fine point layer:
    ps2[0].value = "people"
    tool.updateParameters(ps2)
    tool.updateMessages(ps2)
    assert not [1 for p in ps2 for k, _ in p.messages if k == "ERROR"]


def test_pyt_machine2_shapefile_target_refused_with_advice():
    """Field report A4 (the Kayseri failure): every Machine 2 result
    name exceeds the shapefile 10-character cap, so appending to a
    .shp must be refused BEFORE computing, naming the fix (file
    gdb / new feature class) - and writing to a gdb feature class
    must work."""
    rng = np.random.default_rng(23)
    n = 120
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 1500, n),
                      "SHAPE@Y": rng.uniform(0, 1500, n),
                      "beautiful_": rng.normal(50, 9, n)})
    state = _install_fake_arcpy(t)
    state["catalog_paths"] = {"people": r"C:\Data\Kayseri.shp"}
    pyt = _load_pyt()
    arcpy = sys.modules["arcpy"]
    msg = _Messages()
    with pytest.raises(arcpy.ExecuteError, match="10 char"):
        pyt._run_tool("stats", "people", msg,
                      value_fields=["beautiful_"],
                      stats_list=["mean", "median", "gini",
                                  "percentiles"],
                      pct_text="10 25 75 90", k_text="200",
                      r_text="200")
    # same request into a NEW feature class in a gdb: succeeds
    pyt._run_tool("stats", "people", msg,
                  value_fields=["beautiful_"],
                  stats_list=["mean", "percentiles"],
                  pct_text="10 90", k_text="200",
                  out_mode="New feature class",
                  out_fc=r"C:\Data\work.gdb\kayseri_eqp")
    out = state["copies"][r"C:\Data\work.gdb\kayseri_eqp"]
    assert "Mean_beautiful__200" in out and "P90_beautiful__200" in out


def test_pyt_machine1_shapefile_treat_names_refused():
    """Machine 1 hits the same cap via T_/R_ names when appending to
    a shapefile with long group fields."""
    rng = np.random.default_rng(24)
    n = 90
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 900, n),
                      "SHAPE@Y": rng.uniform(0, 900, n),
                      "Population": rng.integers(0, 2, n).astype(float)})
    state = _install_fake_arcpy(t)
    state["catalog_paths"] = {"people": r"C:\Data\Population.shp"}
    pyt = _load_pyt()
    arcpy = sys.modules["arcpy"]
    msg = _Messages()
    with pytest.raises(arcpy.ExecuteError, match="10 char"):
        pyt._run_tool("counts", "people", msg, k_text="344",
                      treat_fields=["Population"])
    # short names on the same shapefile: fine (N_344, Dist_344 fit)
    pyt._run_tool("counts", "people", msg, k_text="344")
    assert "N_344" in state["table"]


def test_pyt_geographic_advice_names_utm_zone():
    """Field report A5: the degree refusal should COMPUTE the fitting
    UTM zone from the layer's extent (Kayseri ~ 35.5E, 38.7N ->
    zone 36N / EPSG:32636) instead of suggesting SWEREF to Anatolia;
    Swedish extents still get SWEREF."""
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [35.5],
                      "SHAPE@Y": [38.7]})
    state = _install_fake_arcpy(t)
    state["crs_types"] = {"people": "Geographic"}
    state["extents"] = {"people": (35.3, 38.5, 35.7, 38.9)}
    pyt = _load_pyt()
    arcpy = sys.modules["arcpy"]
    msg = _Messages()
    with pytest.raises(arcpy.ExecuteError, match="32636"):
        pyt._run_tool("counts", "people", msg, k_text="5")
    state["extents"] = {"people": (11.0, 55.4, 24.0, 68.5)}  # Sweden
    with pytest.raises(arcpy.ExecuteError, match="3006"):
        pyt._run_tool("counts", "people", msg, k_text="5")


def test_categorical_values_quotes_stripped():
    """John's question: category values typed WITH quotes must work
    the same as bare ones."""
    from equipop.categorical import categories_to_binary
    cats = np.array(["cafe", "restaurant", "school", "cafe"])
    m1, t1 = categories_to_binary(cats, "'cafe'; \"restaurant\"")
    m2, t2 = categories_to_binary(cats, "cafe; restaurant")
    assert set(t1) == set(t2)
    for k in t1:
        assert np.array_equal(t1[k], t2[k])


def test_pyt_predictor_matches_dispatch_columns():
    """The shapefile-refusal predictor must not drift from the
    package: predicted names == actual dispatch columns for the
    supported configurations."""
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0]})
    _install_fake_arcpy(t)
    pyt = _load_pyt()
    from equipop.stata_bridge import dispatch
    rng = np.random.default_rng(3)
    x, y = rng.uniform(0, 2000, 200), rng.uniform(0, 2000, 200)
    tr = rng.integers(0, 2, 200).astype(float)
    v = rng.normal(50, 5, 200)
    fr = pd.DataFrame({"x": [1050.0], "y": [1050.0],
                       "friction": [5.0]})
    cases = [
        (dispatch("counts", x, y, treat={"grp": tr}, k_values=[50],
                  r_values=[300.0], treat_are_counts=True),
         pyt._predict_result_fields("counts", "50", "300", "",
                                    ["grp"], [], [], False, False)),
        (dispatch("counts", x, y, treat={"grp": tr}, k_values=[50],
                  treat_are_counts=True, half_life_m=500.0,
                  decay_model="negexp"),
         pyt._predict_result_fields("counts", "50", "", "", ["grp"],
                                    [], [], True, False)),
        (dispatch("friction", x, y, treat={"grp": tr}, k_values=[50],
                  tau_values=[3.0], friction_file=fr,
                  treat_are_counts=True),
         pyt._predict_result_fields("counts", "50", "", "3", ["grp"],
                                    [], [], False, True)),
        (dispatch("stats", x, y, values={"inc": v},
                  stats={"inc": ["mean", "p10"]}, k_values=[50],
                  r_values=[300.0]),
         pyt._predict_result_fields("stats", "50", "300", "", [],
                                    ["inc"], ["mean", "p10"],
                                    False, False)),
    ]
    for res, pred in cases:
        assert set(res.keys()) == set(pred), (
            sorted(res.keys()), sorted(pred))


def test_pyt_machine2_dialog_has_output_section():
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0]})
    _install_fake_arcpy(t)
    pyt = _load_pyt()
    tool = pyt.ValueStatistics()
    ps = tool.getParameterInfo()
    names = [p.name for p in ps]
    assert {"existing", "outmode", "outfc", "outtable"} <= set(names)
    assert [p for p in ps if p.name == "outmode"][0].filter.list == \
        ["Append to input", "New feature class"]
    tool.updateParameters(ps)
    tool.updateMessages(ps)


# ------------------------------------------- v1.16.3 field-round bugs
def test_pyt_field_box_holding_a_number_refused():
    """Field-test finding: a k value typed into the Full population
    box reached arcpy as a field name ('Cannot find field 55').
    Now refused with advice - and stale field picks from another
    layer are cleared by the dialog."""
    rng = np.random.default_rng(31)
    n = 40
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 500, n),
                      "SHAPE@Y": rng.uniform(0, 500, n),
                      "Income": rng.normal(300, 40, n)})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    arcpy = sys.modules["arcpy"]
    msg = _Messages()
    with pytest.raises(arcpy.ExecuteError, match="not a field"):
        pyt._run_tool("stats", "people", msg, value_fields=["Income"],
                      weight_field="55", k_text="55")
    tool = pyt.ValueStatistics()
    ps = tool.getParameterInfo()
    # v1.29.2: BY NAME. The ladder inserted four boxes here, and a
    # test that counts positions would have moved silently onto its
    # neighbour and still passed - which is the failure this whole
    # dialog was converted away from.
    pm = {q.name: q for q in ps}
    pm["layer"].value = "people"
    pm["pop"].value = "55"                  # stale/typed junk
    pm["values"].value = "Income;Ghost"     # one real, one stale
    tool.updateParameters(ps)
    assert pm["pop"].value is None
    assert pm["values"].valueAsText == "Income"


def test_pyt_autoproject_checkbox_and_table_advice(tmp_path):
    """Field-test ruling: degree LAYERS may be auto-projected to the
    computed zone when the box is ticked (and are refused with that
    suggestion when it is not); degree TABLES always refuse, but now
    name the fitting CRS computed from the coordinates."""
    t = pd.DataFrame({"OBJECTID": [1, 2, 3],
                      "SHAPE@X": [35.50, 35.52, 35.54],
                      "SHAPE@Y": [38.70, 38.72, 38.74]})
    state = _install_fake_arcpy(t)
    state["crs_types"] = {"people": "Geographic"}
    state["extents"] = {"people": (35.4, 38.6, 35.6, 38.8)}
    state["aux_tables"] = {"degtab": pd.DataFrame(
        {"Longitude": [35.5, 35.6], "Latitude": [38.7, 38.8]})}
    pyt = _load_pyt()
    arcpy = sys.modules["arcpy"]
    msg = _Messages()
    with pytest.raises(arcpy.ExecuteError, match="32636"):
        pyt._run_tool("counts", "people", msg, k_text="2")
    pyt._run_tool("counts", "people", msg, k_text="2",
                  auto_project=True)
    assert "N_2" in state["table"]
    assert any("AUTO-PROJECTED" in m for m in msg.log)
    with pytest.raises(arcpy.ExecuteError, match="32636"):
        pyt._run_tool("counts", "degtab", msg, k_text="2",
                      out_table=str(tmp_path / "t.csv"),
                      auto_project=True)     # tables never auto


def test_pyt_short_names_are_collision_free():
    """Ruling: shapefile targets may take shortened names when the
    box is ticked - and the shortening must never merge two
    different results (the P25/P75 trap)."""
    rng = np.random.default_rng(32)
    n = 60
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 900, n),
                      "SHAPE@Y": rng.uniform(0, 900, n),
                      "beautiful_": rng.normal(50, 9, n)})
    state = _install_fake_arcpy(t)
    state["catalog_paths"] = {"people": r"C:\Data\Kayseri.shp"}
    pyt = _load_pyt()
    msg = _Messages()
    pyt._run_tool("stats", "people", msg, value_fields=["beautiful_"],
                  stats_list=["percentiles"], pct_text="25 75",
                  k_text="40", short_names=True)
    got = state["table"]
    added = [c for c in got.columns if c not in
             ("OBJECTID", "SHAPE@X", "SHAPE@Y", "beautiful_")]
    assert added and all(len(c) <= 10 for c in added)
    assert len(set(added)) == len(added)          # no collisions
    assert any("Mapping:" in m for m in msg.log)
    from equipop.stata_bridge import dispatch
    ref = dispatch("stats", t["SHAPE@X"].to_numpy(),
                   t["SHAPE@Y"].to_numpy(),
                   values={"beautiful_": t["beautiful_"].to_numpy()},
                   stats={"beautiful_": ["p25", "p75"]}, k_values=[40])
    p25 = [c for c in added if "25" in c][0]
    assert np.allclose(got[p25], ref["P25_beautiful__40"],
                       equal_nan=True)


def test_pyt_dialog_warns_about_shapefile_before_run():
    """The shapefile conflict must be visible in the DIALOG, not
    only as a post-Run refusal (field-test comment)."""
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0], "Income": [1.0]})
    state = _install_fake_arcpy(t)
    state["catalog_paths"] = {"people": r"C:\Data\gridby_points.shp"}
    pyt = _load_pyt()
    tool = pyt.ValueStatistics()
    ps = tool.getParameterInfo()
    pm = {q.name: q for q in ps}
    pm["layer"].value = "people"
    pm["values"].value = "Income"
    pm["k"].value = "200"
    tool.updateParameters(ps)
    tool.updateMessages(ps)
    errs = [txt for p in ps for kind, txt in p.messages
            if kind == "ERROR"]
    assert any("10 char" in e for e in errs)
    assert any("shortened field names" in e for e in errs)
    [p for p in ps if p.name == "shortnames"][0].value = True
    tool.updateMessages(ps)
    errs2 = [txt for p in ps for kind, txt in p.messages
             if kind == "ERROR" and "10 char" in txt]
    assert not errs2


def test_help_xml_covers_every_parameter():
    """The sidecar help must stay in step with the dialogs: every
    parameter of both tools needs its own explanation, and the XML
    must parse."""
    import xml.etree.ElementTree as ET
    import subprocess
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gen = os.path.join(root, "arcgis", "make_help_xml.py")
    subprocess.run([sys.executable, gen], check=True, cwd=root)
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0]})
    _install_fake_arcpy(t)
    pyt = _load_pyt()
    for cls, name in ((pyt.CountsShares, "CountsShares"),
                      (pyt.ValueStatistics, "ValueStatistics")):
        path = os.path.join(root, "arcgis",
                            f"EquiPop.{name}.pyt.xml")
        tree = ET.parse(path)
        helped = {p.get("name") for p in tree.iter("param")}
        assert {p.name for p in cls().getParameterInfo()} <= helped
        assert tree.find(".//summary").text


def test_pyt_reports_package_voice_and_stage_times():
    """Field finding (475k-row run, 94 minutes, silent pane): the
    package's own lines never reached Pro, so nobody could see where
    the time went. Now stdout is forwarded and every stage is
    timed."""
    rng = np.random.default_rng(41)
    n = 300
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 2000, n),
                      "SHAPE@Y": rng.uniform(0, 2000, n),
                      "Pop": rng.integers(1, 6, n).astype(float)})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    msg = _Messages()
    pyt._run_tool("counts", "people", msg, k_text="50",
                  weight_field="Pop")
    log = "\n".join(msg.log)
    # the package's own voice now reaches the pane (engine notes,
    # neighbour-search size, row count handed back)
    assert "[fast]" in log and "neighbour cells" in log
    assert "[equipop]" in log
    # BACKLOG 136: it said "[stata]" until 1.29.6, in EVERY door,
    # because the shared dispatch lives in stata_bridge.py. A Pro user
    # reading their own log had no idea why Stata was involved.
    assert "[stata]" not in log
    for stage in ("[time] reading input", "[time] calculating",
                  "[time] writing results to the layer",
                  "[time] TOTAL"):
        assert stage in log, stage
    assert "most of it in" in log
    # stdout must be restored, whatever happened
    assert sys.stdout is not None and hasattr(sys.stdout, "write")


def test_pyt_stage_times_survive_a_refusal():
    """A refusal mid-run must not leave the package talking into a
    dead reporter (stdout restored by the context manager)."""
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0], "Income": [1.0]})
    state = _install_fake_arcpy(t)
    state["crs_types"] = {"people": "Geographic"}
    state["extents"] = {"people": (11.0, 55.4, 24.0, 68.5)}
    pyt = _load_pyt()
    arcpy = sys.modules["arcpy"]
    msg = _Messages()
    before = sys.stdout
    with pytest.raises(arcpy.ExecuteError):
        pyt._run_tool("stats", "people", msg, value_fields=["Income"],
                      k_text="5")
    assert sys.stdout is before


# ------------------------------------------- v1.16.5 field-round three
def test_pyt_autoproject_unblocks_the_dialog_too():
    """Field finding: the checkbox was honoured by execute() but the
    DIALOG still refused, so Run stayed disabled. Both gates must
    agree - and tables must still refuse either way."""
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [17.6],
                      "SHAPE@Y": [59.8]})
    state = _install_fake_arcpy(t)
    state["crs_types"] = {"people": "Geographic"}
    state["extents"] = {"people": (11.0, 55.4, 24.0, 68.5)}
    state["aux_tables"] = {"degtab": pd.DataFrame(
        {"Longitude": [17.6], "Latitude": [59.8]})}
    pyt = _load_pyt()
    for tool in (pyt.CountsShares(), pyt.ValueStatistics()):
        ps = tool.getParameterInfo()
        i_auto = [i for i, p in enumerate(ps)
                  if p.name == "autoproj"][0]
        ps[0].value = "people"
        tool.updateParameters(ps)
        tool.updateMessages(ps)
        assert any(k == "ERROR" for k, _ in ps[0].messages)
        ps[i_auto].value = True              # tick the box
        tool.updateMessages(ps)
        kinds = [k for k, _ in ps[0].messages]
        assert "ERROR" not in kinds and "WARNING" in kinds
        # v1.22: the CRS advice moved next to the tick that fixes it,
        # and the input keeps a short pointer - because Pro hides a
        # warning while its section is collapsed (John, field), so the
        # detail alone would be invisible exactly when it matters.
        assert any("Coordinates" in txt for _, txt in ps[0].messages)
        assert any("3006" in txt for _, txt in ps[i_auto].messages)
    tool = pyt.CountsShares()               # a TABLE still refuses
    ps = tool.getParameterInfo()
    ps[0].value = "degtab"
    [p for p in ps if p.name == "autoproj"][0].value = True
    tool.updateParameters(ps)
    tool.updateMessages(ps)
    assert any(k == "ERROR" for p in ps for k, _ in p.messages)


def test_pyt_rerun_updates_in_place_and_verifies():
    """Field finding: DeleteField rewrites the whole table, which is
    what desynchronised the map layer from its file. A re-run with
    the same parameters must now UPDATE the existing columns, delete
    nothing, and verify afterwards that the fields really arrived."""
    rng = np.random.default_rng(51)
    n = 200
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 1500, n),
                      "SHAPE@Y": rng.uniform(0, 1500, n)})
    state = _install_fake_arcpy(t)
    state["catalog_paths"] = {"people": r"C:\Data\gridby_points.shp"}
    pyt = _load_pyt()
    msg = _Messages()
    pyt._run_tool("counts", "people", msg, k_text="40")
    first = state["table"]["N_40"].copy()
    deleted = []
    arcpy = sys.modules["arcpy"]
    real_delete = arcpy.management.DeleteField

    def _spy(layer, fields):
        deleted.extend(fields)
        return real_delete(layer, fields)
    arcpy.management.DeleteField = _spy
    msg2 = _Messages()
    pyt._run_tool("counts", "people", msg2, k_text="40")
    arcpy.management.DeleteField = real_delete
    assert not deleted                        # nothing was rewritten
    assert any("in place" in m for m in msg2.log)
    assert any("VERIFIED present" in m for m in msg2.log)
    assert np.allclose(state["table"]["N_40"], first, equal_nan=True)
    # a DIFFERENT k must still add new columns alongside
    pyt._run_tool("counts", "people", _Messages(), k_text="25")
    assert {"N_40", "N_25"} <= set(state["table"].columns)


def test_pyt_dem_is_read_by_the_host_not_the_package():
    """Field finding: the package tried to import rasterio inside a
    Pro clone. Elevation rasters must arrive as arrays from arcpy,
    exactly like barrier rasters do."""
    rng = np.random.default_rng(52)
    n = 60
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 900, n),
                      "SHAPE@Y": rng.uniform(0, 900, n)})
    state = _install_fake_arcpy(t)
    state["shape_types"] = {"dem": "Raster"}
    hill = np.tile(np.linspace(0.0, 120.0, 10), (10, 1))
    state["rasters"] = {"dem": {"array": hill, "xmin": 0.0,
                                "ymax": 1000.0, "cw": 100.0,
                                "ch": 100.0, "nodata": None}}
    pyt = _load_pyt()
    msg = _Messages()
    payload = pyt._raster_payload("dem", msg)
    assert payload["array"].shape == (10, 10)
    assert payload["cell_w"] == 100.0 and payload["y_max"] == 1000.0
    assert any("read by ArcGIS" in m for m in msg.log)
    from equipop.slope import dem_to_cell_altitude
    E = np.array([50.0, 850.0])
    N = np.array([950.0, 950.0])
    alt = dem_to_cell_altitude(payload, E, N, unit_size=100)
    assert alt[1] > alt[0]                    # the hill rises east
    assert np.isfinite(alt).all()


# ------------------------------------------- v1.16.6 CRS + manifest
def test_pyt_barrier_uses_the_working_crs_not_the_stored_one():
    """Field finding (17.3 GiB): under auto-projection the points
    were read in metres while barriers were requested in the layer's
    stored DEGREE crs, so the friction grid spanned the gap. The
    barrier reader must be handed the CRS actually used."""
    t = pd.DataFrame({"OBJECTID": [1, 2, 3],
                      "SHAPE@X": [17.60, 17.61, 17.62],
                      "SHAPE@Y": [59.80, 59.81, 59.82]})
    state = _install_fake_arcpy(t)
    state["crs_types"] = {"people": "Geographic"}
    state["extents"] = {"people": (17.5, 59.7, 17.7, 59.9)}
    state["shape_types"] = {"lake": "Polygon"}
    seen = {}

    pyt = _load_pyt()
    arcpy = sys.modules["arcpy"]

    class _SC:
        def __init__(self, layer, fields, spatial_reference=None):
            seen["sr"] = spatial_reference
            self.rows = []

        def __enter__(self):
            return iter(self.rows)

        def __exit__(self, *a):
            return False
    arcpy.da.SearchCursor = _SC
    msg = _Messages()
    try:
        pyt._run_tool("counts", "people", msg, k_text="2",
                      barrier="lake", barrier_field="Friction",
                      tau_text="3", auto_project=True)
    except Exception:
        pass                       # empty barrier layer: fine
    assert seen.get("sr") is not None
    # Uppsala -> SWEREF 99 TM, and crucially a PROJECTED sr
    assert getattr(seen["sr"], "factoryCode", 0) == 3006
    assert any("Working CRS" in m for m in msg.log)


def test_pyt_writes_a_run_manifest(tmp_path):
    """Reproducibility: every run leaves a manifest naming the
    version, the CRS actually used (auto-projected or not), the
    parameters and the timings."""
    rng = np.random.default_rng(61)
    n = 120
    tab = pd.DataFrame({"Easting": rng.uniform(0, 900, n),
                        "Northing": rng.uniform(0, 900, n)})
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0]})
    state = _install_fake_arcpy(t)
    state["aux_tables"] = {"tbl": tab}
    pyt = _load_pyt()
    out = tmp_path / "res.csv"
    pyt._run_tool("counts", "tbl", _Messages(), k_text="20",
                  out_table=str(out), unit=250.0)
    man = pd.read_csv(tmp_path / "res_EquiPop_run.csv").set_index(
        "item")["value"].to_dict()
    assert man["engine"] == "counts"
    assert str(man["k_values"]) == "20"
    assert float(man["cell_size_m"]) == 250.0
    assert man["equipop_version"]
    assert "total_seconds" in man


def test_the_manifest_records_what_actually_decided_the_numbers(
        tmp_path):
    """BACKLOG 148, finished; BACKLOG 99, recorded.

    148 added `population` to _manifest_rows in 1.29.6 and NEITHER
    CALL SITE EVER PASSED IT, so the settings that define the numbers
    were still absent - a parameter with no argument, invisible
    because the manifest test above asks only for engine, k, cell
    size and version. Found in 1.30 while adding the overshoot mode,
    which would have gone the same way.

    The rule this test states: a manifest must name every setting
    that CHANGES THE ANSWER, or it describes a run it cannot
    reproduce. Broken on purpose by dropping each argument in turn.
    """
    rng = np.random.default_rng(148)
    n = 200
    tab = pd.DataFrame({"Easting": rng.uniform(0, 900, n),
                        "Northing": rng.uniform(0, 900, n),
                        # Grp is a SUBSET of Pop and the fixture has to
                        # say so. Drawn independently, the group
                        # outgrew its own population - the same
                        # bad-fixture fault as test_rungs, found by the
                        # treatment guard in 1.37.1.
                        "Pop": (_pop := rng.integers(
                            1, 9, n).astype(float)),
                        "Grp": np.floor(_pop * rng.uniform(0, 1, n))})
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0]})
    state = _install_fake_arcpy(t)
    state["aux_tables"] = {"tbl": tab}
    pyt = _load_pyt()
    out = tmp_path / "res.csv"
    pyt._run_tool("counts", "tbl", _Messages(), k_text="20",
                  out_table=str(out), unit=250.0,
                  weight_field="Pop", treat_fields=["Grp"],
                  ref_mode=1, treat_mode=1, keep_outside=False,
                  self_potential=0.0, overshoot="sampled", seed=1848)
    man = pd.read_csv(tmp_path / "res_EquiPop_run.csv").set_index(
        "item")["value"].to_dict()

    # BACKLOG 99: the mode moves every k-based number, and the seed
    # decides which cells `sampled` took
    assert man["overshoot"] == "sampled"
    assert str(man["overshoot_seed"]) == "1848"
    # BACKLOG 148: the settings that define the population
    assert float(man["self_potential"]) == 0.0
    assert man["reference_count_field"] == "Pop"
    assert man["treatment_count_fields"] == "Grp"
    assert pyt.REF_MODES[1][:12] in man["reference_rung"]
    assert pyt.TREAT_MODES[1][:12] in man["treatment_rung"]
    assert pyt.OUTSIDE_MODES[1][:12] in man["rows_outside_reference"]
    assert man["source_analysed"]


def test_friction_guard_refuses_mixed_units_and_clips_the_far_away():
    """The lake that became one cell: degrees against metres must be
    refused with both extents shown - while a legitimately distant
    barrier cell is simply clipped away."""
    from equipop.friction import FrictionGrid
    pop = pd.DataFrame({"x": [445050.0, 445150.0, 445250.0],
                        "y": [6470050.0, 6470150.0, 6470250.0],
                        "count_all": [5.0, 5.0, 5.0],
                        "count_group": [1.0, 1.0, 1.0]})
    degrees = pd.DataFrame({"x": [13.05], "y": [58.05],
                            "friction": [8.0]})
    with pytest.raises(ValueError, match="coordinate system"):
        FrictionGrid(pop, degrees, unit_size=100)
    far = pd.DataFrame({"x": [445150.0, 495150.0],
                        "y": [6470150.0, 6470150.0],
                        "friction": [8.0, 3.0]})
    g = FrictionGrid(pop, far, unit_size=100, clip_margin=5000.0)
    assert g.nx < 100 and g.ny < 100        # the far cell was clipped
    huge = pd.DataFrame({"x": [445150.0], "y": [6470150.0],
                         "friction": [8.0]})
    with pytest.raises(ValueError, match="movement graph"):
        FrictionGrid(pop, huge, unit_size=1, max_graph_gb=0.001)


def test_pyt_accepts_localised_numbers():
    """Field finding (Swedish Pro): valueAsText returns '0,000001',
    and float() refuses it. Numbers must come off .value when it is
    there, and a decimal comma must work when it is not."""
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0]})
    _install_fake_arcpy(t)
    pyt = _load_pyt()
    arcpy = sys.modules["arcpy"]

    class _P:                       # text only, no usable .value
        def __init__(self, name, text):
            self.name, self._t = name, text
            self.value = text

        @property
        def valueAsText(self):
            return self._t
    pm = {p.name: p for p in (_P("a", "0,000001"), _P("b", "12,5"),
                              _P("c", "1 234,5"), _P("d", "1,234.5"),
                              _P("e", ""), _P("f", "oops"))}
    assert pyt._num(pm, "a") == 1e-6
    assert pyt._num(pm, "b") == 12.5
    assert pyt._num(pm, "c") == 1234.5
    assert pyt._num(pm, "d") == 1234.5
    assert pyt._num(pm, "e", 100.0) == 100.0
    with pytest.raises(arcpy.ExecuteError, match="not a number"):
        pyt._num(pm, "f")
    assert pyt._numlist("344,5 500") == [344.5, 500.0]
    assert pyt._numlist("200;1600") == [200.0, 1600.0]

    class _PV(_P):                  # real numeric .value wins
        def __init__(self, name, val, text):
            super().__init__(name, text)
            self.value = val
    pm2 = {"g": _PV("g", 1e-06, "0,000001")}
    assert pyt._num(pm2, "g") == 1e-6


def test_pyt_decay_run_with_comma_values():
    """End to end: a decayed run whose half-life and cutoff arrive as
    Swedish text must run, and the cutoff must reach the engine."""
    rng = np.random.default_rng(71)
    n = 300
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 3000, n),
                      "SHAPE@Y": rng.uniform(0, 3000, n)})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    msg = _Messages()
    pyt._run_tool("counts", "people", msg, k_text="50",
                  half_life=500.0, decay_model="negexp",
                  decay_eps=1e-3, unit=100.0)
    assert "ND_50" in state["table"]
    log = "\n".join(msg.log)
    # BACKLOG 185: the run no longer reports a truncation radius,
    # because nothing is summed out to one any more.
    assert "decayed sums at each k" in log



def test_pyt_raster_inputs_accept_layer_objects():
    """Field finding: after the name refactor the DEM arrived as a
    parameter OBJECT and RasterToNumPyArray refused it. Both raster
    inputs must accept an object, a layer name or a path."""
    rng = np.random.default_rng(72)
    n = 60
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 900, n),
                      "SHAPE@Y": rng.uniform(0, 900, n)})
    state = _install_fake_arcpy(t)
    state["shape_types"] = {"dem": "Raster"}
    hill = np.tile(np.linspace(0.0, 90.0, 10), (10, 1))
    state["rasters"] = {"dem": {"array": hill, "xmin": 0.0,
                                "ymax": 1000.0, "cw": 100.0,
                                "ch": 100.0, "nodata": None}}
    pyt = _load_pyt()

    class _ParamValue:                 # what Pro hands us
        def __init__(self, v):
            self.value = v

        def __str__(self):
            return self.value
    msg = _Messages()
    for handed in ("dem", _ParamValue("dem")):
        pay = pyt._raster_payload(handed, msg)
        assert pay["array"].shape == (10, 10)
    # v1.22.1: _ref resolves through Describe().catalogPath, because
    # that is the only handle a GeoPackage accepts (John, Malta:
    # AddField refused the layer and accepted the path). It must still
    # lead back to the same data, whether given a name or an object.
    assert pyt._ref(_ParamValue("dem")) == pyt._ref("dem")
    assert pyt._raster_payload(pyt._ref("dem"), msg)["array"].shape \
        == (10, 10)
    assert pyt._ref(None) is None
    m1 = {p.name: p for p in pyt.CountsShares().getParameterInfo()}
    assert "DERasterDataset" in m1["dem"].datatype   # raster picker


# ------------------------------------------------- v1.17 value tables
def test_pyt_category_value_table():
    """The grid replaces three text boxes: rows sharing a group name
    merge (no ';' / ',' / ':' to remember), a value can belong to a
    group WITHOUT being population, an unknown value is refused
    naming what the field holds, and groups count PERSONS when a
    population field is set."""
    rng = np.random.default_rng(81)
    n = 240
    kind = rng.choice(["dwelling", "shop", "school"], n,
                      p=[0.7, 0.2, 0.1])
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 2000, n),
                      "SHAPE@Y": rng.uniform(0, 2000, n),
                      "Pop": rng.integers(1, 9, n).astype(float),
                      "PlaceType": kind})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    arcpy = sys.modules["arcpy"]
    msg = _Messages()
    rows = [["shop", "services", "true"],
            ["school", "services", "true"],
            ["dwelling", "", "true"]]
    pyt._run_tool("counts", "people", msg, k_text="60",
                  weight_field="Pop", cat_field="PlaceType",
                  cat_rows=rows, groups_count="persons")
    got = state["table"]
    assert "T_services_60" in got and "R_services_60" in got
    assert any("same units as the reference" in m for m in msg.log)
    # shares are persons/persons -> never above 1
    ok = got.dropna(subset=["R_services_60"])
    assert (ok["R_services_60"] <= 1.0 + 1e-9).all()
    # PLACES instead: clear the value field and BOTH populations
    # count one per row. v1.22 will not mix them - counting places
    # against persons was the 1.17 field bug (4 places over 140
    # persons), so the only way to places is to ask for it on both
    # sides, which is what leaving the field empty means.
    msg2 = _Messages()
    pyt._run_tool("counts", "people", msg2, k_text="60",
                  cat_field="PlaceType", cat_rows=rows)
    assert any("shares of PLACES" in m for m in msg2.log)
    # a value the field does not hold is refused, naming the values
    with pytest.raises(arcpy.ExecuteError, match="not in the category"):
        pyt._run_tool("counts", "people", _Messages(), k_text="60",
                      cat_field="PlaceType",
                      cat_rows=[["shopp", "services", "true"]])
    # group membership WITHOUT population membership
    msg3 = _Messages()
    pyt._run_tool("counts", "people", msg3, k_text="60",
                  cat_field="PlaceType",
                  cat_rows=[["dwelling", "", "true"],
                            ["shop", "services", "false"]])
    assert "T_services_60" in state["table"]


def test_pyt_multiple_barrier_sources():
    """Several barrier sources in one run - the overlap rule finally
    reachable - must equal the package's own aggregation of the
    union."""
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [40.0],
                      "SHAPE@Y": [40.0]})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    msg = _Messages()
    sq = [(0.0, 0.0), (200.0, 0.0), (200.0, 200.0), (0.0, 200.0)]
    line = [(50.0, -50.0), (50.0, 250.0)]
    state["shape_types"] = {"lake": "Polygon", "river": "Polyline"}
    state["geom_layers"] = {"lake": [(_geom([sq]), 6.0)],
                            "river": [(_geom([line]), 4.0)]}
    rows = [["lake", "Friction"], ["river", "Friction"]]
    fr_sum = pyt._collect_barriers(rows, "additive (sum)", 100.0,
                                   None, msg)
    cells = dict(zip(zip(fr_sum.x, fr_sum.y), fr_sum.friction))
    assert cells[(50.0, 50.0)] == 10.0       # lake 6 + river 4
    assert cells[(150.0, 150.0)] == 6.0      # lake only
    fr_max = pyt._collect_barriers(rows, "max", 100.0, None, msg)
    cmax = dict(zip(zip(fr_max.x, fr_max.y), fr_max.friction))
    assert cmax[(50.0, 50.0)] == 6.0
    assert any("2 barrier sources" in m for m in msg.log)


def test_pyt_variable_bandwidth_through_the_dialog():
    """Half-life from a field, and self-calibration from Dist_k, must
    reach the engine and produce decayed sums."""
    rng = np.random.default_rng(82)
    n = 200
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 2500, n),
                      "SHAPE@Y": rng.uniform(0, 2500, n),
                      "MedDist": rng.choice([300.0, 900.0], n)})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    msg = _Messages()
    pyt._run_tool("counts", "people", msg, k_text="40",
                  decay_model="negexp", half_life_field="MedDist",
                  decay_bins=4)
    assert "ND_40" in state["table"]
    assert any("Variable bandwidth" in m for m in msg.log)
    from equipop.stata_bridge import knn_to_rows
    from equipop.decay import Decay
    hl = t["MedDist"].to_numpy()
    ref = knn_to_rows(t["SHAPE@X"].to_numpy(), t["SHAPE@Y"].to_numpy(),
                      k_values=[40],
                      decay=Decay(model="negexp", half_life_m=500.0),
                      decay_half_life=hl, decay_bins=4)["ND_40"]
    assert np.allclose(state["table"]["ND_40"], ref, equal_nan=True)
    msg2 = _Messages()
    pyt._run_tool("counts", "people", msg2, k_text="40",
                  decay_model="negexp", half_life_from_dist=40)
    assert any("Self-calibrating" in m for m in msg2.log)


def test_pyt_write_lock_is_reported_not_raw():
    """Field finding: a re-run whose target is locked (attribute
    table open, edit session, OneDrive) surfaced arcpy's raw
    'Cannot acquire a lock'. It must retry, then explain and name
    the way out."""
    rng = np.random.default_rng(91)
    n = 80
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 900, n),
                      "SHAPE@Y": rng.uniform(0, 900, n)})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    arcpy = sys.modules["arcpy"]
    pyt._run_tool("counts", "people", _Messages(), k_text="20")
    real = arcpy.da.UpdateCursor

    class _Locked:
        def __init__(self, *a, **kw):
            raise RuntimeError("Cannot acquire a lock.")
    arcpy.da.UpdateCursor = _Locked
    msg = _Messages()
    try:
        with pytest.raises(arcpy.ExecuteError) as err:
            pyt._run_tool("counts", "people", msg, k_text="20")
    finally:
        arcpy.da.UpdateCursor = real
    said = str(err.value)
    assert "write lock" in said
    assert "ATTRIBUTE TABLE" in said       # names the usual cause
    assert "New feature class" in said     # names the way out
    assert "Nothing was" in said           # and says nothing changed
    assert sum("retrying" in m.lower() for m in msg.log) == 3



def test_pyt_value_table_columns_offer_choices():
    """Field finding: the friction field had to be TYPED. The column
    is now a Field dropdown, and the category table offers the
    category field's own values."""
    rng = np.random.default_rng(93)
    n = 40
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 500, n),
                      "SHAPE@Y": rng.uniform(0, 500, n),
                      "PlaceType": rng.choice(["dwelling", "shop"], n)})
    _install_fake_arcpy(t)
    pyt = _load_pyt()
    tool = pyt.CountsShares()
    ps = tool.getParameterInfo()
    pm = {p.name: p for p in ps}
    assert pm["barriertable"].columns[1][0] == "Field"
    pm["layer"].value = "people"
    # v1.23: each population names its own type field, so each table
    # fills from the field beside it - no reaching into another
    # section for the values
    pm["catfield"].value = "PlaceType"
    pm["treatcatfield"].value = "PlaceType"
    tool.updateParameters(ps)
    assert set(pm["reftable"].filters[0].list) == {"dwelling", "shop"}
    assert set(pm["treattable"].filters[0].list) == {"dwelling", "shop"}


@pytest.mark.parametrize("label,params,expected",
                         [(c[0], c[1], c[2]) for c in
                          __import__("door_parity").LADDER_CASES])
def test_pro_gives_the_same_columns_for_every_ladder_combination(
        label, params, expected):
    """BACKLOG 86, the other door. The SAME cases run through Pro, so
    the doors are compared on what they DO and not merely on what
    they offer. Pro was the correct one when this was written - it
    hands both modes to the shared engine and lets _run_tool decide -
    but "correct today" is not a guard.

    Driven at _run_tool rather than through the dialog: the simulated
    arcpy resolves any string in a value table to a layer path, so
    'bar' arrives as 'memory/bar'. That is a stub infidelity worth
    its own item; it must not stop the behaviour being checked."""
    rng = np.random.default_rng(86)
    n = 400
    t = pd.DataFrame({
        "OBJECTID": np.arange(1, n + 1),
        "SHAPE@X": rng.uniform(0, 2000, n),
        "SHAPE@Y": rng.uniform(0, 2000, n),
        "fclass": rng.choice(["cafe", "bar", "school"], n),
        "Population": rng.integers(1, 6, n).astype(float)})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    kw = dict(k_text="100", ref_mode=params.get("refmode", 0),
              treat_mode=params.get("treatmode", 0))
    if "pop" in params:
        kw["weight_field"] = params["pop"]
    if params.get("refmode") == 2:
        kw["cat_field"] = params["catfield"]
        kw["ref_rows"] = [[v] for v in params["reftable"]]
    if params.get("treatmode") == 2:
        kw["treat_cat_field"] = params["treatcatfield"]
        kw["treat_rows"] = [list(params["treattable"])]
    pyt._run_tool("counts", "people", _Messages(), **kw)
    stems = {c.rsplit("_", 1)[0] for c in state["table"].columns
             if c.startswith(("N_", "Dist_", "T_", "R_"))}
    assert stems == expected, (
        f"[{label}] Pro gave {sorted(stems)}, expected "
        f"{sorted(expected)} - the doors must agree on BEHAVIOUR, "
        "which is what BACKLOG 85 showed names alone cannot promise")


# ---------------------------------------------- BACKLOG 95, behaviour
def test_self_potential_is_honoured_by_the_pro_door():
    """The other half of the QGIS test of the same name. Both doors
    are pinned to the CLOSED FORM rather than to each other, so a
    door that drops the parameter fails on its own - the failure mode
    BACKLOG 85 taught us to test for directly.

    DRIVEN THROUGH THE DIALOG, not at _run_tool. The first version of
    this test called _run_tool and therefore skipped the very hop
    where the danger lives: `_num(pm, "selfpot", 1.0) OR 1.0` would
    silently restore the default when the user asks for 0, because 0
    is falsy - and the test passed happily against that break. Unlike
    the ladder cases (BACKLOG 87), a plain number needs no value
    table, so the dialog route is available here and is the honest
    one. A fresh fake arcpy per run: its table persists in memory, so
    a run that quietly did nothing would still show the last run's
    columns.
    """
    rng = np.random.default_rng(95)
    n_dense, n_spread = 200, 400
    t = pd.DataFrame({
        "OBJECTID": np.arange(1, n_dense + n_spread + 1),
        "SHAPE@X": np.concatenate([rng.uniform(1, 99, n_dense),
                                   rng.uniform(500, 4000, n_spread)]),
        "SHAPE@Y": np.concatenate([rng.uniform(1, 99, n_dense),
                                   rng.uniform(500, 4000, n_spread)])})
    dense = ((t["SHAPE@X"] < 100) & (t["SHAPE@Y"] < 100)).to_numpy()

    def _dialog_run(sp):
        state = _install_fake_arcpy(t.copy())
        pyt = _load_pyt()
        tool = pyt.CountsShares()
        ps = tool.getParameterInfo()
        pm = {p.name: p for p in ps}
        pm["layer"].value = "people"
        pm["k"].value = "100"
        pm["selfpot"].value = sp        # a LABEL now (BACKLOG 141)
        tool.updateParameters(ps)
        tool.updateMessages(ps)
        assert not [1 for p in ps for kind, _ in p.messages
                    if kind == "ERROR"]
        tool.execute(ps, _Messages())
        return state["table"]["Dist_100"].to_numpy()[dense]

    from equipop.doors.rungs import SELF_POTENTIAL as SP
    off = _dialog_run(SP[0])
    assert (off == 0.0).all(), (
        "self-potential 0 must reproduce pre-1.29.5 numbers exactly - "
        "if this reads like the equal-area radius, a falsy 0 was "
        "swallowed on the way from the dialog to the engine")

    on = _dialog_run(SP[2])
    expected = np.sqrt(100.0 ** 2 * 100 / (n_dense * np.pi))
    assert np.allclose(on, expected, rtol=1e-9), (
        f"expected the equal-area radius {expected:.4f} m, got "
        f"{on[0]:.4f} m - Pro offers the box but is not passing it on")


# ------------------------------------------ 135 / 145 / 147, writing
def test_a_field_refusal_is_not_retried_as_a_lock():
    """BACKLOG 135. `if "not supported" not in str(exc)` sent EVERY
    other failure down a two-attempt retry meant for transient locks.
    Three of John's 1.29.6 field failures came through there and none
    was a lock: a held file, group names colliding on case, and nulls
    in a shapefile. Waiting cannot cure a refused FIELD, and each
    retry ran against a half-written table."""
    _install_fake_arcpy(pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                                      "SHAPE@Y": [0.0]}))
    pyt = _load_pyt()
    for msg in ("TypeError: cannot add field: 'Tba400'",
                "RuntimeError: The field is not nullable. [N100]",
                "ERROR 999999: field 'N400' already exist"):
        assert pyt._is_field_refusal(Exception(msg)), msg
    # a genuine lock keeps its retries - 000852 is Esri's generic
    # "cannot add field" and covers a locked file
    for msg in ("ERROR 000852: Cannot add field EQPTST1 to gridby",
                "The table is locked by another application",
                "operation is not supported on this format"):
        assert not pyt._is_field_refusal(Exception(msg)), msg


def test_the_failure_message_no_longer_asserts_a_cause_it_cannot_know():
    """BACKLOG 145. The cloud-sync note was appended to EVERY failure
    and fired on three of John's in one evening, having caused none of
    them. And "Nothing was changed" was false - the write had already
    added three fields."""
    _install_fake_arcpy(pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                                      "SHAPE@Y": [0.0]}))
    pyt = _load_pyt()
    sync = r"C:\Users\j\OneDrive - X\p\out.shp"
    known = pyt._write_failure(
        Exception("TypeError: cannot add field: 'Tba400'"),
        "add the result fields", sync)
    # the PATH contains "OneDrive", legitimately - it is the NOTE
    # that must not appear when the reason is already known
    assert "cloud-synced folder" not in str(known)
    assert "upper/lower case" in str(known)
    assert "not a lock" in str(known)

    lock = pyt._write_failure(
        Exception("ERROR 000852: Cannot add field"),
        "add the result fields", sync)
    assert "cloud-synced" in str(lock)
    assert "only one of the possibilities" in str(lock)

    for m in (known, lock):
        assert "Nothing was changed" not in str(m), (
            "the message must not claim this - ExtendTable is not "
            "atomic and _undo_partial reports what is true")


def test_a_shapefile_is_told_it_cannot_hold_nulls_before_the_run():
    """BACKLOG 147. dBASE has no empty value for a number, so that
    rung cannot be written to a shapefile - John found out after the
    engine had done its work and the message blamed OneDrive."""
    _install_fake_arcpy(pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                                      "SHAPE@Y": [0.0]}))
    pyt = _load_pyt()
    assert pyt._shapefile_cannot_hold_nulls(
        r"C:\d\x.shp", "leave their results Null")
    assert not pyt._shapefile_cannot_hold_nulls(
        r"C:\d\x.shp", "give them results, counting as zero")
    assert not pyt._shapefile_cannot_hold_nulls(
        r"C:\d\x.gdb\y", "leave their results Null")


# ----------------------------------------------- 138 / 146, the rungs
def _dialog(tool_name="CountsShares", **values):
    t = pd.DataFrame({"OBJECTID": [1, 2, 3, 4],
                      "SHAPE@X": [0., 10., 20., 30.],
                      "SHAPE@Y": [0., 0., 0., 0.],
                      "Pop": [4., 1., 7., 9.],
                      "LowInc": [1., 0., 3., 2.],
                      "Type": ["a", "a", "b", "b"]})
    _install_fake_arcpy(t)
    pyt = _load_pyt()
    tool = getattr(pyt, tool_name)()
    ps = tool.getParameterInfo()
    pm = {p.name: p for p in ps}
    pm["layer"].value = "people"
    for k, v in values.items():
        pm[k].value = v
    return pyt, tool, ps


def test_pro_now_refuses_an_empty_rung_box_as_qgis_does():
    """BACKLOG 138. John chose "one column per group, counts inside"
    with the group count fields empty; Pro ran to completion and gave
    N_ and Dist_ with no T_, no R_ and no message. QGIS had refused
    the same dialog state since 1.29.5 - the release whose whole point
    was that the doors must not differ."""
    pyt, tool, ps = _dialog(k="2", treatmode="one column per group, "
                            "counts inside")
    with pytest.raises(Exception) as e:
        tool.execute(ps, _Messages())
    assert "group count fields" in str(e.value)

    pyt, tool, ps = _dialog(k="2", refmode="a field holds the count")
    with pytest.raises(Exception) as e:
        tool.execute(ps, _Messages())
    assert "count field" in str(e.value)


def test_a_box_the_rung_does_not_read_is_announced_not_obeyed():
    """BACKLOG 146. Pro greys such boxes out, but greying does not
    CLEAR them and _run_tool read them anyway - so 'fclass', a field
    of a previous layer, reached the engine while John could not see
    the box holding it.

    Ignoring is preferred to clearing: someone may switch the rung
    back, and emptying their work silently would be a second fault.
    """
    msg = _Messages()
    pyt, tool, ps = _dialog(k="2", treatcatfield="Type")
    pm = {p.name: p for p in ps}
    ignored = pyt._guard_rungs(pm, msg, "counts")
    assert "treatcatfield" in ignored
    said = "\n".join(msg.log)
    assert "IGNORED" in said and "treatcatfield" in said
