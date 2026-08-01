"""The QGIS door, against a simulated PyQGIS.

Same doctrine as the ArcGIS suite: this proves LOGIC. Only QGIS on a
real machine proves behaviour, and the ArcGIS round showed that the
gap between those two is where all the interesting bugs live.

The test that matters most is the conformance one. Gridby's planted
truths say a door is sane; the shared reference says two doors
AGREE - which is what a student needs, since a QGIS class and a Pro
class should not get different numbers from the same town.
"""
import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "qgis"))

import qgis_stub                                    # noqa: E402

qgis_stub.install()

from qgis.core import (QgsProcessingException,      # noqa: E402
                       QgsProcessingFeedback)
from equipop_qgis.alg_counts import CountsAndShares  # noqa: E402
from equipop_qgis.alg_stats import ValueStatistics   # noqa: E402
from equipop_qgis.provider import EquipopProvider    # noqa: E402
from equipop.doors.reference import (SPEC, compare,  # noqa: E402
                                     explain)


def _run(alg_cls, source, **params):
    alg = alg_cls()
    alg.initAlgorithm()
    p = {"layer": source, "unit": 100.0, "outfc": "memory:out"}
    p.update(params)
    fb = QgsProcessingFeedback()
    alg.processAlgorithm(p, None, fb)
    return p["_sinks"]["outfc"].to_frame(), fb


# ------------------------------------------------------ the plugin
def test_the_provider_offers_both_tools():
    prov = EquipopProvider()
    prov.loadAlgorithms()
    assert [a.name() for a in prov.algorithms()] == \
        ["countsandshares", "valuestatistics"]
    assert prov.id() == "equipop"


def test_every_parameter_carries_the_shared_explanation():
    """The QGIS mirror of the ArcGIS help test. A parameter with no
    entry in equipop.doors.help is a release blocker in BOTH doors -
    which is the whole reason the text lives in one place."""
    from equipop.doors.help import missing_help
    for cls in (CountsAndShares, ValueStatistics):
        alg = cls()
        alg.initAlgorithm()
        names = [p.name() for p in alg.parameterDefinitions()]
        assert not missing_help(names), \
            f"{cls.__name__}: no help for {missing_help(names)}"


def test_the_two_doors_use_the_same_parameter_names():
    """Student parity, made testable: a name that matches means the
    same box is explained with the same words in Pro and in QGIS."""
    src = open(os.path.join(ROOT, "arcgis", "EquiPop.pyt")).read()
    for cls in (CountsAndShares, ValueStatistics):
        alg = cls()
        alg.initAlgorithm()
        for p in alg.parameterDefinitions():
            assert f'"{p.name()}"' in src, (
                f"QGIS uses a parameter name '{p.name()}' that the "
                "ArcGIS toolbox does not - the two doors would then "
                "explain the same idea with different words")


def test_the_help_page_is_built_from_the_shared_summary():
    from equipop.doors.help import summary_for
    alg = CountsAndShares()
    assert summary_for("CountsShares")[:40] in alg.shortHelpString()


# -------------------------------------------------- conformance
@pytest.fixture(scope="module")
def door_output():
    """Both tools run over Gridby exactly as the reference spec
    describes, and merged the way a user would end up with them."""
    counts, _ = _run(CountsAndShares, qgis_stub.gridby_source(),
                     pop=SPEC["weight"], treat=["count_group"],
                     k="400", r="800", unit=SPEC["unit_size"])
    stats, _ = _run(ValueStatistics, qgis_stub.gridby_source(),
                    pop=SPEC["weight"], values=["count_group"],
                    measures=[0, 1, 2], k="400", r="",
                    unit=SPEC["unit_size"])
    dup = [c for c in stats.columns
           if c in counts.columns and c not in ("x", "y")]
    return counts.merge(stats.drop(columns=dup), on=["x", "y"])


def test_the_qgis_door_matches_the_shared_reference(door_output):
    """THE test. A door is finished when this passes."""
    rep = compare(door_output)
    assert rep["ok"], explain(rep)
    assert rep["rows_compared"] == 2360


def test_the_door_keeps_the_original_columns(door_output):
    assert {"count_all", "count_group"} <= set(door_output.columns)


def test_the_door_recovers_gridbys_planted_gradient(door_output):
    west = door_output.loc[door_output.x < 1000,
                           "R_count_group_400"].mean()
    east = door_output.loc[door_output.x > 5000,
                           "R_count_group_400"].mean()
    assert west < 0.18 and east > 0.50


# ------------------------------------------------ reading input
def test_degrees_are_reprojected_rather_than_refused():
    """QGIS makes this easy, so there is no reason to send the user
    away to project the layer first - which is what the ArcGIS door
    must do for a table with no CRS to speak of."""
    t = pd.DataFrame({"x": [13.0, 13.01, 13.02, 13.03],
                      "y": [57.7, 57.71, 57.72, 57.73],
                      "pop": [1.0, 1, 1, 1]})
    src = qgis_stub.source_from(t, crs="EPSG:4326")
    out, fb = _run(CountsAndShares, src, pop="pop", k="2")
    said = " ".join(fb.info)
    assert "degrees" in said and "reprojected" in said
    assert "not changed" in said
    assert len(out) == 4


def test_a_table_without_geometry_uses_the_shared_coordinate_rules():
    t = pd.DataFrame({"East_RT90": [0.0, 100, 200, 300],
                      "North_RT90": [0.0, 0, 100, 100],
                      "pop": [1.0, 1, 1, 1]})
    src = qgis_stub.source_from(t, geometry=False)
    out, fb = _run(CountsAndShares, src, pop="pop", k="2")
    assert "guessed" in " ".join(fb.info)
    assert len(out) == 4


def test_an_empty_layer_is_refused_in_qgis_currency():
    src = qgis_stub.source_from(
        pd.DataFrame({"x": [], "y": [], "pop": []}))
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, src, pop="pop", k="2")
    assert "no features" in str(e.value)


def test_asking_for_no_neighbourhood_is_refused():
    src = qgis_stub.source_from(
        pd.DataFrame({"x": [0.0, 1], "y": [0.0, 1], "pop": [1.0, 1]}))
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, src, pop="pop", k="", r="")
    assert "at least one k" in str(e.value)


def test_value_statistics_insists_on_a_value_field():
    src = qgis_stub.source_from(
        pd.DataFrame({"x": [0.0, 1], "y": [0.0, 1], "v": [1.0, 2]}))
    with pytest.raises(QgsProcessingException) as e:
        _run(ValueStatistics, src, values=[], k="2")
    assert "at least one value field" in str(e.value)


# ------------------------------------------------ writing output
def test_a_shapefile_target_is_refused_naming_a_geopackage():
    """The ten-character trap follows the shapefile into QGIS. Same
    shared rule as Pro; only the roomy neighbour changes name."""
    src = qgis_stub.source_from(
        pd.DataFrame({"x": [0.0, 1, 2], "y": [0.0, 1, 2],
                      "pop": [1.0, 1, 1],
                      "some_long_group_name": [1.0, 0, 1]}))
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, src, pop="pop",
             treat=["some_long_group_name"], k="2",
             outfc="/tmp/results.shp")
    msg = str(e.value)
    assert "SHAPEFILE" in msg and "GeoPackage" in msg
    assert "geodatabase" not in msg


def test_the_pane_hears_the_engines_own_voice():
    """The package prints; QGIS shows only what is pushed to it. The
    shared reporter is the join."""
    src = qgis_stub.gridby_source()
    _, fb = _run(CountsAndShares, src, pop="count_all", k="400")
    said = " ".join(fb.info)
    assert "[fast]" in said or "[cells]" in said
    assert "[time] calculating" in said
