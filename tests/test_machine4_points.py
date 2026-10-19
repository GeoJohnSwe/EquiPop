# -*- coding: utf-8 -*-
"""test_machine4_points.py - machine 4 from the points machine 3 made,
not only from the rasters (v1.60.1).

John, 18 October: "machine 4 only takes rasters - we should make it
possible to use the curated raster-to-point files as well". The folder
and machine 3's point table are the same people, so the same run from
either must give the same numbers - that is the test.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
pytest.importorskip("rasterio")

import test_vital_machine4 as M4                     # noqa: E402
from equipop.doors.continental import run_folder     # noqa: E402
from equipop.doors.demography import run_indices     # noqa: E402
from equipop.rasterfolder import load_points         # noqa: E402

RUN = dict(k_values=[3000], unit_size=1000.0, epsg=32737)


@pytest.fixture(scope="module")
def made(tmp_path_factory):
    folder = M4.make_folder(tmp_path_factory.mktemp("pts"))
    man = run_folder(str(folder), k_values=[])        # machine 3, no k
    # as the doors write it: EastWest/NorthSouth, iso3, every cohort
    table = man["points_table"].rename(columns={"lon": "EastWest",
                                                "lat": "NorthSouth"})
    return str(folder), table, man["crs"]


def _in_utm(table, crs):
    """The same layer after someone saved it in UTM 37S."""
    from pyproj import Transformer
    t = Transformer.from_crs(crs, "EPSG:32737", always_xy=True)
    x, y = t.transform(table["EastWest"].to_numpy(float),
                       table["NorthSouth"].to_numpy(float))
    return table.assign(EastWest=x, NorthSouth=y)


AS_WRITTEN, IN_UTM = "as machine 3 wrote it", "saved in UTM"


def _layer(table, crs, how):
    return ((table, crs) if how == AS_WRITTEN
            else (_in_utm(table, crs), "EPSG:32737"))


def _same(a, b, cols):
    a = a.sort_values(["EastWest", "NorthSouth"]).reset_index(drop=True)
    b = b.sort_values(["EastWest", "NorthSouth"]).reset_index(drop=True)
    for c in cols:
        assert np.allclose(a[c], b[c], equal_nan=True), c


def test_the_points_give_what_the_folder_gives(made):
    """An index and the rates, from the folder and from machine 3's
    table of it: the same numbers.

    BROKEN WITH: folder_to_cells ignoring points= (it then reads the
    folder argument, None, and refuses)."""
    folder, table, crs = made
    a = run_indices(folder, ["child_woman_ratio"],
                    vital=["life_expectancy_60", "total_fertility_rate"],
                    **RUN)["results"]
    b = run_indices(None, ["child_woman_ratio"],
                    vital=["life_expectancy_60", "total_fertility_rate"],
                    points=table, points_crs=crs, **RUN)["results"]
    _same(a, b, ["cwr_3000", "e60_3000", "TFR_3000", "Dist_3000"])


def test_a_layer_saved_in_another_projection_gives_the_same(made):
    """Someone saves machine 3's layer in UTM before using it. Its own
    coordinate system travels with it, and the answers do not change.

    BROKEN WITH: load_source dropping points_crs (metres are then
    refused)."""
    folder, table, crs = made
    a = run_indices(folder, ["child_woman_ratio"], **RUN)["results"]
    t, c = _layer(table, crs, IN_UTM)
    b = run_indices(None, ["child_woman_ratio"], points=t, points_crs=c,
                    **RUN)["results"]
    _same(a, b, ["cwr_3000", "Dist_3000"])


def test_the_long_shape_is_turned_back(made):
    """Machine 3 can write one row per point per cohort. That table
    works too.

    BROKEN WITH: the pivot of the long shape removed (it then has no
    cohort columns and is refused); and with every other field kept as
    part of what makes a point (a row number per row then makes each
    row a point of its own - a table read from a file carries one)."""
    from equipop.rasterfolder import to_long
    folder, table, crs = made
    wide = table.rename(columns={"EastWest": "lon", "NorthSouth": "lat"})
    long = to_long(wide)
    long["OBJECTID"] = np.arange(1, len(long) + 1)
    pts, _m = load_points(long, crs)
    assert {"f_00_2020", "m_90_2020", "iso3"} <= set(pts.columns)
    assert len(pts) == len(table)
    a = wide.sort_values(["lon", "lat"]).reset_index(drop=True)
    b = pts.sort_values(["lon", "lat"]).reset_index(drop=True)
    assert np.allclose(a["f_15_2020"], b["f_15_2020"])


def test_a_table_without_cohorts_is_refused_in_words():
    """A table made with 'Add all cohorts into one population' has only
    'pop'.

    BROKEN WITH: the cohort check removed (a KeyError later instead)."""
    with pytest.raises(ValueError, match="no cohort fields"):
        load_points(pd.DataFrame({"EastWest": [36.1], "NorthSouth": [-1.1],
                                  "pop": [10.0]}), "EPSG:4326")


def test_an_empty_table_is_refused_in_words():
    """BROKEN WITH: the empty check removed (numpy's 'zero-size array'
    instead)."""
    with pytest.raises(ValueError, match="empty"):
        load_points(pd.DataFrame({"EastWest": [], "NorthSouth": [],
                                  "f_00_2020": []}), None)


def test_metres_without_a_crs_are_refused():
    """Degrees can be recognised; metres cannot be placed without
    knowing their projection.

    BROKEN WITH: every coordinate taken as degrees when no CRS came."""
    t = pd.DataFrame({"EastWest": [500000.0], "NorthSouth": [6500000.0],
                      "f_00_2020": [3.0]})
    with pytest.raises(ValueError, match="not degrees"):
        load_points(t, None)
    pts, man = load_points(t.assign(EastWest=18.0, NorthSouth=59.0), None)
    assert man["crs"] == "EPSG:4326"


# ------------------------------------------------------------ the doors
def _qgis_run(**params):
    sys.path.insert(0, str(ROOT / "qgis"))
    import qgis_stub
    qgis_stub.install()
    from equipop_qgis.alg_demography import SpatialDemography
    import test_vital_doors as VD
    alg = SpatialDemography()
    alg.initAlgorithm()
    p = {"folder": "", "indices": [1], "rates": [0], "ratesex": 0,
         "k": "3000", "unit": 1000.0, "year": "", "crs": None,
         "outcrs": None, "settings": [], "OUTPUT": "memory:"}
    p.update(params)
    alg.processAlgorithm(p, {}, VD._Feedback())
    return p["_sinks"]["OUTPUT"].to_frame()


@pytest.mark.parametrize("how", [AS_WRITTEN, IN_UTM])
def test_qgis_takes_machine_3s_point_layer(made, how):
    """The point layer - in degrees as machine 3 wrote it, or saved in
    UTM - gives the same child-woman ratio and e60 as the folder.

    BROKEN WITH: the QGIS door passing points=None; and with the
    layer's CRS not passed on (the UTM layer is then refused)."""
    import qgis_stub
    folder, table, crs = made
    t, c = _layer(table, crs, how)
    lyr = t.rename(columns={"EastWest": "x", "NorthSouth": "y"})
    src = qgis_stub._Source(lyr, crs=c, geometry=True)
    a = _qgis_run(folder=folder)
    b = _qgis_run(points=src)
    a = a.sort_values(["cwr_3000", "e60_3000"]).reset_index(drop=True)
    b = b.sort_values(["cwr_3000", "e60_3000"]).reset_index(drop=True)
    assert np.allclose(a["cwr_3000"], b["cwr_3000"])
    assert np.allclose(a["e60_3000"], b["e60_3000"], equal_nan=True)


def test_qgis_wants_one_or_the_other(made):
    """BROKEN WITH: the either-or check removed (the folder silently
    wins)."""
    import qgis_stub
    from qgis.core import QgsProcessingException
    folder, table, crs = made
    lyr = table.rename(columns={"EastWest": "x", "NorthSouth": "y"})
    src = qgis_stub._Source(lyr, crs=crs, geometry=True)
    with pytest.raises(QgsProcessingException, match="not both"):
        _qgis_run(folder=folder, points=src)
    with pytest.raises(QgsProcessingException, match="EITHER"):
        _qgis_run(folder="")


@pytest.mark.parametrize("how", [AS_WRITTEN, IN_UTM])
def test_pro_takes_machine_3s_point_layer(made, tmp_path, how):
    """Pro reads the layer's geometry, fields and coordinate system and
    gives the folder's answers - in degrees as machine 3 wrote it, or
    saved in UTM.

    BROKEN WITH: Pro's door passing points=None; and with the layer's
    coordinate system not passed on (the UTM layer is then refused)."""
    import test_arcgis_continental as AC
    folder, table, crs = made
    pyt, tool, state = AC._tool("SpatialDemography")
    t, c = _layer(table, crs, how)
    lyr = t.rename(columns={"EastWest": "SHAPE@X",
                            "NorthSouth": "SHAPE@Y"})
    lyr["iso3"] = lyr["iso3"].astype(str)
    state.setdefault("layers", {})["m3points"] = lyr
    state.setdefault("crs_codes", {})["m3points"] = int(c.split(":")[1])
    state.setdefault("crs_types", {})["m3points"] = (
        "Geographic" if how == AS_WRITTEN else "Projected")
    out_a, out_b = str(tmp_path / "a.shp"), str(tmp_path / "b.shp")
    tool.execute(AC._params(tool, folder=folder, indices="Child-woman "
                            "ratio", rates="Life expectancy at 60",
                            k="3000", unit=1000.0, out=out_a),
                 AC._Messages())
    tool.execute(AC._params(tool, points="m3points", indices="Child-"
                            "woman ratio", rates="Life expectancy at 60",
                            k="3000", unit=1000.0, out=out_b),
                 AC._Messages())
    a = state["written"][out_a]["table"].sort_values("cwr_3000")
    b = state["written"][out_b]["table"].sort_values("cwr_3000")
    assert np.allclose(a["cwr_3000"], b["cwr_3000"])
    assert np.allclose(a["e60_3000"], b["e60_3000"], equal_nan=True)


def test_pro_wants_one_or_the_other(made):
    """Said in the dialog the moment both boxes are filled, and refused
    at Run if neither or both are.

    BROKEN WITH: Pro's either-or check removed from execute (the
    folder silently wins), and separately with the updateMessages
    check removed (no word until Run)."""
    import test_arcgis_continental as AC
    folder, table, crs = made
    pyt, tool, state = AC._tool("SpatialDemography")
    lyr = table.rename(columns={"EastWest": "SHAPE@X",
                                "NorthSouth": "SHAPE@Y"})
    state.setdefault("layers", {})["m3points"] = lyr
    both = AC._params(tool, folder=folder, points="m3points", k="3000",
                      out="C:/x/b.shp")
    tool.updateMessages(both)
    pm = {p.name: p for p in both}
    assert any("not both" in t for k, t in pm["points"].messages
               if k == "ERROR")
    with pytest.raises(pyt.arcpy.ExecuteError, match="not both"):
        tool.execute(both, AC._Messages())
    one = AC._params(tool, folder=folder, k="3000", out="C:/x/a.shp")
    tool.updateMessages(one)
    assert not {p.name: p for p in one}["points"].messages
    none = AC._params(tool, k="3000", out="C:/x/n.shp")
    with pytest.raises(pyt.arcpy.ExecuteError, match="EITHER"):
        tool.execute(none, AC._Messages())


def test_pro_names_an_esri_projection_so_pyproj_finds_it():
    """World Mollweide is ESRI:54009; there is no EPSG:54009, so the
    layer's factoryCode alone would leave the engine unable to place
    the points.

    BROKEN WITH: the code always sent as 'EPSG:<code>'."""
    import types
    import test_arcgis_continental as AC
    pyt, _tool, _state = AC._tool("SpatialDemography")
    sr = types.SimpleNamespace
    assert pyt._pyproj_crs(sr(factoryCode=4326)) == "EPSG:4326"
    assert pyt._pyproj_crs(sr(factoryCode=54009)) == "ESRI:54009"
    assert pyt._pyproj_crs(sr(factoryCode=0)) is None
