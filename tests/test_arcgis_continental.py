"""MACHINES 3 AND 4 IN ARCGIS PRO, EXECUTED.

BACKLOG 235. Both tools were written months apart and left OUT of
`self.tools`, because the arcpy simulator could not exercise a
DEFolder box or NumPyArrayToFeatureClass — so nothing had ever run
them, and registering an untested tool puts it in front of users on
the strength of a reading.

The QGIS twins shipped with three wiring faults that 682 passing tests
could not see, because nothing called processAlgorithm. These call
execute() from the first commit.

John installed 1.41.2 into Pro successfully with his own method, so
the engine side is proven on a real machine. What has never run on one
is the toolbox.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
rasterio = pytest.importorskip("rasterio")
from rasterio.transform import from_origin            # noqa: E402

from test_arcgis_stub import (_install_fake_arcpy,     # noqa: E402
                              _load_pyt, _Messages)
from equipop.doors.demography import BAND_STARTS, INDICES  # noqa: E402

import pandas as pd                                    # noqa: E402


@pytest.fixture(scope="module")
def folder():
    """Two countries, a real-shaped pyramid, fractional counts."""
    px = 1.0 / 1200
    d = tempfile.mkdtemp()
    rng = np.random.default_rng(23)
    shape = (40, 40)
    for iso, off in (("bdi", 0.0), ("rwa", 0.04)):
        for sex in ("f", "m"):
            for age in BAND_STARTS:
                a = (rng.random(shape)
                     * max(0.2, 3.0 - age / 30.0)).astype("float32")
                with rasterio.open(
                        os.path.join(d, f"{iso}_{sex}_{age:02d}_2026"
                                        "_CN_1km_R2025A_UA_v1.tif"),
                        "w", driver="GTiff", height=shape[0],
                        width=shape[1], count=1, dtype="float32",
                        crs="EPSG:4326", nodata=-99999.0,
                        transform=from_origin(30.0 + off,
                                              -2.0 + shape[0] * px,
                                              px, px)) as o:
                    o.write(a, 1)
    return d


def _tool(name):
    # THE FAKE ARCPY MUST EXIST BEFORE THE .pyt LOADS - the toolbox
    # does `import arcpy` at the top. Claude had the two calls the
    # wrong way round and all thirteen tests failed with
    # ModuleNotFoundError, which is the right failure for the wrong
    # reason.
    state = _install_fake_arcpy(pd.DataFrame({"x": [0.0], "y": [0.0]}))
    pyt = _load_pyt()
    return pyt, getattr(pyt, name)(), state


def _pyt():
    _install_fake_arcpy(pd.DataFrame({"x": [0.0], "y": [0.0]}))
    return _load_pyt()


def _params(tool, **vals):
    ps = tool.getParameterInfo()
    by = {p.name: p for p in ps}
    for k, v in vals.items():
        # valueAsText is a read-only PROPERTY derived from value, in
        # the simulator and in real arcpy. Setting it is not how a
        # dialog works; setting `value` is.
        by[k].value = v
    return ps


# --------------------------------------------------- the toolbox itself
def test_the_toolbox_offers_all_four_tools():
    pyt = _pyt()
    names = [t.__name__ for t in pyt.Toolbox().tools]
    assert names == ["CountsShares", "ValueStatistics",
                     "ContinentalRasters", "SpatialDemography"], names


def test_every_registered_tool_can_be_constructed():
    """A tool that raises in __init__ takes the whole toolbox down."""
    pyt = _pyt()
    for cls in pyt.Toolbox().tools:
        t = cls()
        assert t.label and t.description


def test_every_registered_tool_builds_its_dialog():
    """getParameterInfo runs when Pro opens the toolbox."""
    pyt = _pyt()
    for cls in pyt.Toolbox().tools:
        ps = cls().getParameterInfo()
        assert ps and all(p.name for p in ps)


def test_the_index_list_matches_the_package():
    """It is written down in the .pyt so the toolbox opens without
    equipop installed - which means it can drift. Pin it."""
    pyt = _pyt()
    ps = pyt.SpatialDemography().getParameterInfo()
    listed = [p for p in ps if p.name == "indices"][0].filter.list
    assert listed == [INDICES[n]["label"] for n in sorted(INDICES)]


# ------------------------------------------------------ machine 3 runs
def test_machine_3_runs_and_writes(folder, tmp_path):
    pyt, tool, state = _tool("ContinentalRasters")
    out = str(tmp_path / "out.shp")
    msg = _Messages()
    tool.execute(_params(tool, folder=folder, k="500", unit=1000.0,
                         weight="sexes", out=out), msg)
    assert str(out) in state.get("written", {}), msg.log[-6:]
    got = state["written"][str(out)]["table"]
    assert len(got) > 0
    assert any(c.startswith("N_500") for c in got.columns)


def test_machine_3_writes_in_the_rasters_own_projection(folder, tmp_path):
    """The false-northing trap: a metric layer lands off the top of a
    European basemap (BACKLOG 227)."""
    pyt, tool, state = _tool("ContinentalRasters")
    out = str(tmp_path / "crs.shp")
    tool.execute(_params(tool, folder=folder, k="500", unit=1000.0,
                         weight="sexes", out=out), _Messages())
    w = state["written"][str(out)]
    assert w["xy"] == ("EastWest", "NorthSouth")
    e = w["table"]["EastWest"].to_numpy(float)
    assert -180 < e.min() and e.max() < 180, (
        "coordinates look like metres; the layer should be in the "
        "rasters' own geographic CRS")


# ------------------------------------------------------ machine 4 runs
def test_machine_4_runs_one_index(folder, tmp_path):
    pyt, tool, state = _tool("SpatialDemography")
    out = str(tmp_path / "dem.shp")
    msg = _Messages()
    tool.execute(_params(tool, folder=folder,
                         indices="Child-woman ratio", k="500",
                         unit=1000.0, out=out), msg)
    got = state["written"][str(out)]["table"]
    assert any(c.startswith("cwr_500") for c in got.columns), \
        list(got.columns)


def test_machine_4_runs_several_in_one_pass(folder, tmp_path):
    pyt, tool, state = _tool("SpatialDemography")
    out = str(tmp_path / "many.shp")
    msg = _Messages()
    tool.execute(_params(tool, folder=folder,
                         indices="Child-woman ratio;Ageing index",
                         k="500", unit=1000.0, out=out), msg)
    got = state["written"][str(out)]["table"]
    assert any(c.startswith("cwr_500") for c in got.columns)
    assert any(c.startswith("age_500") for c in got.columns)
    said = " ".join(msg.log)
    assert "2 indices" in said


def test_machine_4_shows_the_columns_before_computing(folder, tmp_path):
    pyt, tool, state = _tool("SpatialDemography")
    tool.execute(_params(tool, folder=folder,
                         indices="Child-woman ratio", k="500",
                         unit=1000.0, out=str(tmp_path / "p.shp")),
                 msg := _Messages())
    said = " ".join(msg.log)
    assert "on top" in said and "divided by" in said
    assert "f_15_2026" in said


# ---------------------------------------------------------- refusals
def test_an_unknown_index_is_refused_by_name(folder, tmp_path):
    pyt, tool, _ = _tool("SpatialDemography")
    with pytest.raises(Exception, match="No such index"):
        tool.execute(_params(tool, folder=folder,
                             indices="Total fertility rate", k="500",
                             unit=1000.0, out=str(tmp_path / "x.shp")),
                     _Messages())


def test_no_index_is_refused(folder, tmp_path):
    pyt, tool, _ = _tool("SpatialDemography")
    with pytest.raises(Exception, match="at least one"):
        tool.execute(_params(tool, folder=folder, indices="", k="500",
                             unit=1000.0, out=str(tmp_path / "x.shp")),
                     _Messages())


def test_a_k_that_is_not_a_number_is_refused(folder, tmp_path):
    pyt, tool, _ = _tool("SpatialDemography")
    with pytest.raises(Exception, match="not a number"):
        tool.execute(_params(tool, folder=folder,
                             indices="Ageing index", k="lots",
                             unit=1000.0, out=str(tmp_path / "x.shp")),
                     _Messages())


def test_a_folder_that_is_not_there_is_refused_in_plain_words(tmp_path):
    pyt, tool, _ = _tool("ContinentalRasters")
    with pytest.raises(Exception, match="Not a folder"):
        tool.execute(_params(tool, folder="/no/such/place", k="500",
                             unit=1000.0, weight="sexes",
                             out=str(tmp_path / "x.shp")),
                     _Messages())


def test_pro_offers_the_same_pre_filled_measure_table_as_qgis():
    """John: "In Pro, these options are not available > they should".

    Same table, same cells, same meaning - and every cell reproduces
    the measure's own definition, so it opens showing the truth rather
    than asking the user to type from memory.
    """
    # Read the QGIS door as TEXT - importing it would need the QGIS
    # simulator, and this test lives on the arcpy side.
    import ast
    qsrc = (ROOT / "qgis" / "equipop_qgis"
            / "alg_demography.py").read_text(encoding="utf-8")
    qrows = next(ast.literal_eval(n.value)
                 for n in ast.parse(qsrc).body
                 if isinstance(n, ast.Assign)
                 and getattr(n.targets[0], "id", "") == "INDEX_ROWS")
    pyt = _pyt()
    assert list(pyt.INDEX_ROWS) == list(qrows), (
        "the two doors show different measure tables")

    ps = pyt.SpatialDemography().getParameterInfo()
    tab = [p for p in ps if p.name == "settings"][0]
    assert [c[1] for c in tab.columns] == ["Index", "Numerator ages",
                                           "Denominator ages"]
    assert len(tab.value) == 4


def test_pro_honours_an_edited_measure(folder, tmp_path):
    pyt, tool, state = _tool("SpatialDemography")
    ps = _params(tool, folder=folder, indices="Child-woman ratio",
                 k="500", unit=1000.0, out=str(tmp_path / "e.shp"))
    by = {p.name: p for p in ps}
    rows = [list(r) for r in (pyt.INDEX_ROWS[i:i + 3]
                              for i in range(0, len(pyt.INDEX_ROWS), 3))]
    rows[1][2] = "f:15-44"                      # child-woman, edited
    by["settings"].value = rows
    msg = _Messages()
    tool.execute(ps, msg)
    said = " ".join(msg.log)
    plan_lines = [l for l in msg.log if l.startswith("   divided by")]
    assert plan_lines and "f_40_2026" in plan_lines[-1]
    assert "f_45_2026" not in plan_lines[-1], plan_lines[-1]


def test_the_two_doors_agree_on_every_tool_name():
    """BACKLOG 237 - they had drifted on three of four."""
    from equipop.doors.help import LABELS
    pyt = _pyt()
    for cls in pyt.Toolbox().tools:
        label = cls().label
        assert label in LABELS.values(), (
            f"Pro calls a tool {label!r}, which is not in the shared list")
