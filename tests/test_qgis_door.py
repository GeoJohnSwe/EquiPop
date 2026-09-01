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

import numpy as np
import pandas as pd
import pytest

from pathlib import Path  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "qgis"))

import qgis_stub                                    # noqa: E402

qgis_stub.install()

from qgis.core import (QgsProcessingException,      # noqa: E402
                       QgsProcessingFeedback)
from qgis.core import QgsProcessingParameterDefinition  # noqa: E402
from equipop_qgis.alg_counts import (CountsAndShares,  # noqa: E402
                                     OVERSHOOT_VALUES)
from equipop_qgis.alg_stats import ValueStatistics   # noqa: E402
from equipop_qgis.provider import EquipopProvider    # noqa: E402
from equipop.doors.reference import (SPEC, compare,  # noqa: E402
                                     explain)

#: Which entry of the door's own dropdown carries the mode the answer
#: key was generated under. Looked up rather than written as a number:
#: a reordered menu would otherwise silently run a different mode and
#: the test would report a conformance failure instead of a menu edit.
_OVERSHOOT_IDX = OVERSHOOT_VALUES.index(SPEC["overshoot"])


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
    # BACKLOG 38 added the third tool. Sorted, because the order the
    # provider happens to register them in is not the contract.
    assert sorted(a.name() for a in prov.algorithms()) == [
        "continentalrasters", "countsandshares", "spatialdatafetch",
        "spatialdemography", "valuestatistics"]
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


def test_the_two_doors_explain_the_same_box_the_same_way():
    """Student parity, made testable. The contract is not that the
    two dialogs use identical WIDGETS - Pro has a barrier value
    table where QGIS has a layer and a field - but that every box in
    either door draws its words from the one shared help source. A
    name with no entry there would be explained twice, differently,
    or not at all."""
    from equipop.doors.help import HELP
    for cls in (CountsAndShares, ValueStatistics):
        alg = cls()
        alg.initAlgorithm()
        for p in alg.parameterDefinitions():
            if p.name() == alg.OUT:
                continue
            assert p.name() in HELP, (
                f"{cls.__name__}: '{p.name()}' has no entry in "
                "equipop.doors.help, so the two doors cannot explain "
                "it with the same words")


def test_the_help_page_is_built_from_the_shared_summary():
    from equipop.doors.help import summary_for
    alg = CountsAndShares()
    assert summary_for("CountsShares")[:40] in alg.shortHelpString()


# -------------------------------------------------- conformance
@pytest.fixture(scope="module")
def door_output():
    """Both tools run over Gridby exactly as the reference spec
    describes, and merged the way a user would end up with them.

    BACKLOG 99. The overshoot mode is NAMED here, from the spec,
    rather than left to whatever each machine defaults to. That is
    the whole shape of the item: the answer key is pinned to one
    mode, so a door can only be judged against it once the door can
    say which mode it ran. Before the box existed this test failed on
    2287 of 2360 rows and there was no way to make it pass without
    either moving the key or hiding the change.
    """
    counts, _ = _run(CountsAndShares, qgis_stub.gridby_source(),
                     refmode=[1], pop=SPEC["weight"],
                     treatmode=[1], treat=["count_group"],
                     k="400", r="800", unit=SPEC["unit_size"],
                     overshoot=[_OVERSHOOT_IDX])
    stats, _ = _run(ValueStatistics, qgis_stub.gridby_source(),
                    pop=SPEC["weight"], values=["count_group"],
                    measures=[0, 1, 2], k="400", r="",
                    unit=SPEC["unit_size"],
                    overshoot=[_OVERSHOOT_IDX])
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
    out, fb = _run(CountsAndShares, src, refmode=[1], pop="pop", k="2")
    said = " ".join(fb.info)
    assert "degrees" in said and "reprojected" in said
    assert "not changed" in said
    assert len(out) == 4


def test_a_table_without_geometry_uses_the_shared_coordinate_rules():
    t = pd.DataFrame({"East_RT90": [0.0, 100, 200, 300],
                      "North_RT90": [0.0, 0, 100, 100],
                      "pop": [1.0, 1, 1, 1]})
    src = qgis_stub.source_from(t, geometry=False)
    out, fb = _run(CountsAndShares, src, refmode=[1], pop="pop", k="2")
    assert "guessed" in " ".join(fb.info)
    assert len(out) == 4


def test_an_empty_layer_is_refused_in_qgis_currency():
    src = qgis_stub.source_from(
        pd.DataFrame({"x": [], "y": [], "pop": []}))
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, src, refmode=[1], pop="pop", k="2")
    assert "no features" in str(e.value)


def test_asking_for_no_neighbourhood_is_refused():
    src = qgis_stub.source_from(
        pd.DataFrame({"x": [0.0, 1], "y": [0.0, 1], "pop": [1.0, 1]}))
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, src, refmode=[1], pop="pop", k="", r="")
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
             treatmode=[1], treat=["some_long_group_name"], k="2",
             outfc="/tmp/results.shp")
    msg = str(e.value)
    assert "SHAPEFILE" in msg and "GeoPackage" in msg
    assert "geodatabase" not in msg


def test_the_pane_hears_the_engines_own_voice():
    """The package prints; QGIS shows only what is pushed to it. The
    shared reporter is the join."""
    src = qgis_stub.gridby_source()
    _, fb = _run(CountsAndShares, src, refmode=[1], pop="count_all", k="400")
    said = " ".join(fb.info)
    assert "[fast]" in said or "[cells]" in said
    assert "[time] calculating" in said


# ------------------------------------------- categories & decay
def test_a_text_category_field_survives_being_read():
    """Forcing every column to a number turned a POI-type field into
    NaN, so every group matched nothing. Numbers as numbers, text as
    text."""
    t = pd.DataFrame({"x": [0.0, 100, 200, 300], "y": [0.0] * 4,
                      "fclass": ["cafe", "bench", "cafe", "atm"]})
    src = qgis_stub.source_from(t)
    alg = CountsAndShares()
    alg.initAlgorithm()
    pts = alg.read_points(src, QgsProcessingFeedback())
    assert list(pts.data["fclass"]) == ["cafe", "bench", "cafe", "atm"]


def _poi_table():
    return pd.DataFrame({
        "x": np.linspace(0, 1100, 12), "y": np.zeros(12),
        "fclass": ["fastfood", "restaurant", "bench", "library",
                   "cafe", "bench", "fastfood", "atm",
                   "restaurant", "postbox", "cafe", "bench"]})


# v1.22: two tables. The REFERENCE table says who is around; the
# TREATMENT table says which of them form which group.
EATING = ["fastfood", "restaurant", "cafe"]
TREAT_ROWS = ["fastfood", "fastfood",
              "restaurant", "eating",
              "cafe", "eating"]


def test_listing_the_reference_narrows_the_denominator():
    """Fast food per EATING PLACE: the reference table names the
    eating places, so benches and postboxes are not in it."""
    out, _ = _run(CountsAndShares, qgis_stub.source_from(_poi_table()),
                  k="4", refmode=[2], catfield="fclass", reftable=EATING,
                  treatmode=[2], treattable=TREAT_ROWS)
    assert out["R_fastfood_4"].max() == pytest.approx(0.5)


def test_an_empty_reference_table_means_everything():
    """Fast food per POI: John's Europe-wide run. Leaving the
    reference table empty is the whole difference - no tick to
    misread."""
    out, _ = _run(CountsAndShares, qgis_stub.source_from(_poi_table()),
                  k="4", refmode=[2], catfield="fclass", reftable=[],
                  treatmode=[2], treattable=TREAT_ROWS,
                  restgroup="other")
    assert out["R_fastfood_4"].max() < 0.5
    assert "T_other_4" in out.columns


def test_the_two_denominators_really_do_differ():
    """Same data, same rows, two correct answers - and the only
    difference is whether the reference table was filled in."""
    strict, _ = _run(CountsAndShares,
                     qgis_stub.source_from(_poi_table()), k="4",
                     refmode=[2], catfield="fclass", reftable=EATING,
                     treatmode=[2], treattable=TREAT_ROWS)
    broad, _ = _run(CountsAndShares,
                    qgis_stub.source_from(_poi_table()), k="4",
                    refmode=[2], catfield="fclass", reftable=[],
                    treatmode=[2], treattable=TREAT_ROWS)
    assert strict["R_fastfood_4"].mean() > broad["R_fastfood_4"].mean()


def test_decay_is_explained_in_plain_numbers():
    """The naming pass, applied: say what the curve DOES before what
    it is called."""
    out, fb = _run(CountsAndShares, qgis_stub.gridby_source(),
                   refmode=[1], pop="count_all", k="400", model=[1],
                   halflife=500.0)
    said = " ".join(fb.info)
    # v1.28: the curve is now printed in plain numbers, from the
    # engine's own weight function rather than an assumed shape
    assert "at 500 m 50%" in said
    assert "at 1,000 m 25%" in said
    assert "ND_400" in out.columns


def test_every_offered_decay_model_exists_in_the_engine():
    """John, field: the dropdown offered 'gauss' and 'linear'.
    Neither exists - they were written from memory. A door that
    offers a model the engine has never heard of either crashes or
    silently substitutes another."""
    from equipop.decay import MODELS
    from equipop.doors.decaynames import (choices, model_from_choice,
                                          NO_DECAY)
    offered = choices()
    assert offered[0] == NO_DECAY
    for label in offered[1:]:
        name = model_from_choice(label)
        assert name in MODELS, f"'{label}' is not an engine model"
    assert len(offered) == len(MODELS) + 1


def test_the_gaussian_is_offered_under_its_real_name():
    """John asked for a Gaussian. It exists - as expnormal - and was
    missing from the list that invented 'gauss'."""
    from equipop.doors.decaynames import choices
    labels = " ".join(choices())
    assert "expnormal" in labels and "Gaussian" in labels
    assert "gauss (" not in labels and "linear" not in labels


# --------------------------------- parity, BOTH directions (v1.25)
# The one-way check missed a real gap: 1.23.0 gave Pro a `refmode`
# ladder and the QGIS edit only half-applied, so the reference
# section had no ladder there at all. Every QGIS name existed in Pro,
# so the old test passed. A door can fall behind as easily as it can
# drift ahead.
# v1.29: the lists moved to tests/door_parity.py so the SAME words
# are checked against Pro as against QGIS. Machine 2 joined them -
# it had never been checked at all, and had been out of step since
# 1.20.0 without a single test noticing.
from door_parity import CORE, CORE_M2


def _qgis_names(cls=None):
    alg = (cls or CountsAndShares)()
    alg.initAlgorithm()
    return {p.name() for p in alg.parameterDefinitions()}


def test_qgis_has_every_core_box_that_pro_has():
    missing = CORE - _qgis_names()
    assert not missing, (
        f"the QGIS door is missing {sorted(missing)} - a box added to "
        "Pro was not carried across")


def test_qgis_machine2_has_every_core_box_that_pro_has():
    missing = CORE_M2 - _qgis_names(ValueStatistics)
    assert not missing, (
        f"QGIS Value Statistics is missing {sorted(missing)} - the "
        "second machine fell behind, which is how `fullpop`/`pop` "
        "went unnoticed for nine releases")


def test_the_ladder_is_present_in_qgis_too():
    alg = CountsAndShares()
    alg.initAlgorithm()
    pm = {p.name(): p for p in alg.parameterDefinitions()}
    assert len(pm["refmode"].options) == 3
    assert len(pm["treatmode"].options) == 3
    assert len(pm["keepoutside"].options) == 2


def _advanced_names(alg):
    """Which boxes sit in QGIS's Advanced area.

    v1.29.1: these tests used to ask the parameter directly, with a
    method PyQGIS has never had - the stub invented it. Reading the
    FLAG is the only way, and it is the same way base.py writes it.
    """
    return {p.name() for p in alg.parameterDefinitions()
            if bool(p.flags()
                    & QgsProcessingParameterDefinition.FlagAdvanced)}


def test_the_rarely_touched_boxes_are_in_the_advanced_area():
    """QGIS has no sections; this is the one grouping it offers."""
    alg = CountsAndShares()
    alg.initAlgorithm()
    adv = _advanced_names(alg)
    assert {"unit", "decayeps", "xfield", "yfield"} <= adv
    assert "refmode" not in adv and "k" not in adv


def test_the_labels_carry_their_step_number():
    """QGIS builds one flat list, so the grouping has to live in the
    wording."""
    alg = CountsAndShares()
    alg.initAlgorithm()
    pm = {p.name(): p.description() for p in
          alg.parameterDefinitions()}
    assert pm["refmode"].startswith("1 ")
    assert pm["pop"].startswith("1a ")
    assert pm["treatmode"].startswith("2 ")
    assert pm["k"].startswith("3 ")


def test_each_rung_names_a_box_that_exists_and_is_the_right_one():
    """BACKLOG 104. Each rung's text now says which box to fill -
    "(fill 2a)". That promise is only worth making if it is kept, and
    it silently stops being kept the moment anyone reorders the
    labels. So: read the box out of the rung's OWN words, find the
    box wearing that letter, and check it is the box the rung
    actually reads.

    Before 1.29.5 this test would have failed on its face: rung 1 of
    the treatment ladder reads `treat`, and `treat` was labelled 2d,
    sitting behind three boxes that served rung 2. That ordering cost
    John a field run.
    """
    import re
    from equipop_qgis.alg_counts import REF_MODES, TREAT_MODES
    alg = CountsAndShares()
    alg.initAlgorithm()
    by_letter = {}
    for prm in alg.parameterDefinitions():
        m = re.match(r"^(\d[a-d]) ", prm.description())
        if m:
            by_letter[m.group(1)] = prm.name()

    reads = {                       # rung -> the box it truly reads
        ("ref", 1): {"1a": "pop"},
        ("ref", 2): {"1a": "pop", "1b": "catfield", "1c": "reftable"},
        ("treat", 1): {"2a": "treat"},
        ("treat", 2): {"2b": "treatcatfield", "2c": "treattable"},
    }
    for ladder, modes in (("ref", REF_MODES), ("treat", TREAT_MODES)):
        for rung, text in enumerate(modes):
            letters = re.findall(r"\d[a-d]", text)
            if not letters:
                continue
            expected = reads[(ladder, rung)]
            assert set(letters) == set(expected), (
                f"{ladder} rung {rung} says 'fill {letters}' but "
                f"actually reads {sorted(expected)}")
            for letter in letters:
                assert by_letter.get(letter) == expected[letter], (
                    f"{ladder} rung {rung} points at box {letter}, "
                    f"which is '{by_letter.get(letter)}' - but that "
                    f"rung reads '{expected[letter]}'")


def test_the_default_run_needs_only_a_layer_and_a_k():
    """Rung 1 of both ladders: every point counts as one, no
    treatment. The simplest question EquiPop answers."""
    out, _ = _run(CountsAndShares, qgis_stub.gridby_source(), k="50")
    assert "N_50" in out.columns and "Dist_50" in out.columns


# ------------------------------- barriers and terrain (v1.26)
def _river_source():
    """A vertical line at x = 450, costing 5 rounds to cross."""
    import qgis_stub as Q
    from qgis.core import QgsGeometry
    t = pd.DataFrame({"cost": [5.0]})
    src = Q.source_from(t, geometry=False)

    class _WithGeom(type(src)):
        pass
    feats = list(src.getFeatures())
    geom = QgsGeometry.fromParts([[(450.0, -100.0), (450.0, 900.0)]],
                                 wkb=2)
    feats[0].setGeometry(geom)
    src.getFeatures = lambda *a: iter(feats)
    src.wkbType = lambda: 2
    return src


def _line_of_points(n=12, step=100.0):
    return pd.DataFrame({"x": np.arange(n) * step,
                         "y": np.zeros(n),
                         "pop": np.ones(n)})


def test_a_barrier_switches_the_run_to_the_effort_engine():
    src = qgis_stub.source_from(_line_of_points())
    out, fb = _run(CountsAndShares, src, refmode=[1], pop="pop",
                   k="4", barrier=_river_source(),
                   barrierfield="cost", tau="3")
    said = " ".join(fb.info)
    assert "EFFORT engine" in said
    assert "friction cells" in said
    assert any(c.startswith("Rounds_") or c.startswith("N_tau")
               for c in out.columns), list(out.columns)


def test_a_barrier_actually_separates_the_two_sides():
    """The point of a barrier: people across the river are farther
    away in ROUNDS than their metres suggest."""
    src = qgis_stub.source_from(_line_of_points())
    with_river, _ = _run(CountsAndShares, src, refmode=[1], pop="pop",
                         k="4", barrier=_river_source(),
                         barrierfield="cost")
    plain, _ = _run(CountsAndShares,
                    qgis_stub.source_from(_line_of_points()),
                    refmode=[1], pop="pop", k="4")
    assert not with_river.equals(plain), \
        "the barrier changed nothing - it is not reaching the engine"


def test_a_barrier_without_a_friction_field_is_refused_kindly():
    src = qgis_stub.source_from(_line_of_points())
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, src, refmode=[1], pop="pop", k="4",
             barrier=_river_source())
    msg = str(e.value)
    assert "friction field" in msg and "rounds" in msg


def test_a_friction_raster_is_read_and_reported():
    import qgis_stub as Q
    grid = np.zeros((10, 10))
    grid[:, 4] = 5.0                      # a wall of cost
    src = qgis_stub.source_from(_line_of_points())
    out, fb = _run(CountsAndShares, src, refmode=[1], pop="pop",
                   k="4",
                   barrierraster=Q.FakeRasterLayer(grid, xmin=0.0,
                                                   ymax=1000.0))
    assert "friction cells" in " ".join(fb.info)
    assert len(out) == 12


def test_an_elevation_raster_turns_slope_into_effort():
    import qgis_stub as Q
    hill = np.tile(np.arange(10.0) * 20.0, (10, 1))
    src = qgis_stub.source_from(_line_of_points())
    out, fb = _run(CountsAndShares, src, refmode=[1], pop="pop",
                   k="4", dem=Q.FakeRasterLayer(hill, xmin=0.0,
                                                ymax=1000.0))
    said = " ".join(fb.info)
    assert "Elevation raster read" in said
    assert "EFFORT engine" in said


def test_decay_is_refused_over_effort_rather_than_quietly_wrong():
    src = qgis_stub.source_from(_line_of_points())
    _, fb = _run(CountsAndShares, src, refmode=[1], pop="pop", k="4",
                 barrier=_river_source(), barrierfield="cost",
                 model=[1], halflife=300.0)
    assert any("Decay over effort is not available" in w
               for w in fb.warnings)


def test_a_multipart_barrier_uses_every_part():
    """A river arrives as ONE feature with many parts. Taking only
    the first would look like a working barrier while quietly
    leaking."""
    from equipop_qgis.barriers import _paths_of
    from qgis.core import QgsGeometry
    g = QgsGeometry.fromParts([[(0.0, 0.0), (0.0, 100.0)],
                               [(50.0, 0.0), (50.0, 100.0)]], wkb=2)
    parts = _paths_of(g)
    assert len(parts) == 2


# ------------------- Malta, John's barrier day (v1.26.1)
def _degree_roads(n=200):
    """Roads in DEGREES, as OSM data arrives - the exact shape of
    John's failure."""
    import qgis_stub as Q
    from qgis.core import QgsGeometry
    t = pd.DataFrame({"friction": [3.0] * n})
    src = Q.source_from(t, crs="EPSG:4326", geometry=False)
    feats = list(src.getFeatures())
    for i, f in enumerate(feats):
        y0 = 35.85 + i * 0.0005
        f.setGeometry(QgsGeometry.fromParts(
            [[(14.40, y0), (14.55, y0)]], wkb=2))
    src.getFeatures = lambda *a: iter(feats)
    src.wkbType = lambda: 2
    src.featureCount = lambda: n
    return src


def test_a_barrier_left_in_degrees_is_refused_not_computed():
    """John, field: 40,678 Maltese roads produced ONE friction cell,
    the run finished in 0.1 s, and 8,730 rows were filled with
    confident nonsense. The CRS bug is fixed - but the deeper fault
    was that nothing objected to an absurd result, so this guards
    the class rather than the instance."""
    from equipop_qgis.barriers import check_plausible
    import pandas as _pd
    collapsed = _pd.DataFrame({"x": [0.0], "y": [0.0],
                               "friction": [3.0]})
    ch = QgsProcessingFeedback()
    with pytest.raises(QgsProcessingException) as e:
        check_plausible(collapsed, 40678,
                        (np.array([450000.0, 460000.0]),
                         np.array([3960000.0, 3970000.0])),
                        100.0, "Barrier layer",
                        CountsAndShares.channel(ch))
    msg = str(e.value)
    assert "40678 features produced only 1 friction cell" in msg
    assert "DEGREES" in msg and "CRS" in msg


def test_a_barrier_somewhere_else_entirely_is_refused():
    from equipop_qgis.barriers import check_plausible
    import pandas as _pd
    elsewhere = _pd.DataFrame({"x": np.arange(300) * 100.0,
                               "y": np.zeros(300),
                               "friction": np.full(300, 3.0)})
    ch = QgsProcessingFeedback()
    with pytest.raises(QgsProcessingException) as e:
        check_plausible(elsewhere, 300,
                        (np.array([9e6, 9.1e6]), np.array([4e6, 4.1e6])),
                        100.0, "Barrier layer",
                        CountsAndShares.channel(ch))
    assert "nowhere near the points" in str(e.value)


def test_a_sane_barrier_passes_and_says_so():
    from equipop_qgis.barriers import check_plausible
    import pandas as _pd
    fr = _pd.DataFrame({"x": np.arange(300) * 100.0,
                        "y": np.zeros(300),
                        "friction": np.full(300, 3.0)})
    fb = QgsProcessingFeedback()
    check_plausible(fr, 300, (np.arange(20) * 100.0, np.zeros(20)),
                    100.0, "Barrier layer",
                    CountsAndShares.channel(fb))
    assert any("looks sane" in m for m in fb.info)


def test_the_barrier_is_reprojected_to_the_WORKING_crs():
    """The bug itself: points in degrees are reprojected for the run,
    so the barrier must be compared against the CRS the run WORKS in,
    not the one the layer arrived in. Comparing degrees with degrees
    concluded 'no transform needed' and left the roads unprojected."""
    t = pd.DataFrame({"x": [13.0, 13.01, 13.02, 13.03],
                      "y": [57.7, 57.71, 57.72, 57.73],
                      "pop": [1.0, 1, 1, 1]})
    src = qgis_stub.source_from(t, crs="EPSG:4326")
    alg = CountsAndShares()
    alg.initAlgorithm()
    alg.read_points(src, QgsProcessingFeedback())
    assert alg.working_crs.authid() != "EPSG:4326", \
        "the working CRS is still the arrival CRS - a barrier would " \
        "not be reprojected and would collapse into one cell"
    assert not alg.working_crs.isGeographic()


def test_no_treatment_means_no_empty_treatment_columns():
    """John, field: a run with no treatment came back with T_40 and
    R_40 - columns of nothing that look like results. The counts
    engine had always been right here; the effort engine had not, so
    the two disagreed about what an empty question answers."""
    src = qgis_stub.source_from(_line_of_points())
    out, _ = _run(CountsAndShares, src, refmode=[1], pop="pop",
                  k="4", barrier=_river_source(),
                  barrierfield="cost")
    stray = [c for c in out.columns
             if c.startswith(("T_", "R_"))]
    assert not stray, f"invented treatment columns: {stray}"
    assert "Rounds_4" in out.columns


def test_a_named_group_still_gets_its_columns_over_effort():
    src = qgis_stub.source_from(
        pd.DataFrame({"x": np.arange(12) * 100.0,
                      "y": np.zeros(12), "pop": np.ones(12),
                      "grp": np.r_[np.ones(6), np.zeros(6)]}))
    out, _ = _run(CountsAndShares, src, refmode=[1], pop="pop",
                  treatmode=[1], treat=["grp"], k="4",
                  barrier=_river_source(), barrierfield="cost")
    assert "T_grp_4" in out.columns and "R_grp_4" in out.columns


# ------------------------------- facilitators (v1.27, John)
def test_a_facilitator_pulls_distant_people_closer():
    """The accessibility counterpart to a barrier. Entering a cell
    costs 1 + friction, so -0.9 makes a cell a tenth of the usual
    effort - a motorway. B is farther in metres and nearer in
    ROUNDS, so it joins the neighbourhood ahead of A."""
    from equipop.friction import points_to_friction
    from equipop.stata_bridge import dispatch
    x = np.array([0.0, 150.0, 0.0])
    y = np.array([0.0, 0.0, 350.0])
    w = np.ones(3)
    ys = np.arange(0.0, 400.0, 50.0)
    road = points_to_friction(np.zeros(len(ys)), ys,
                              np.full(len(ys), -0.9), unit_size=50.0)
    plain = dispatch("counts", x, y, unit_size=50.0, k_values=[2],
                     weight=w)
    fast = dispatch("friction", x, y, unit_size=50.0, k_values=[2],
                    weight=w, friction_file=road)
    assert np.asarray(plain["Dist_2"])[0] == pytest.approx(150.0)
    assert np.asarray(fast["Dist_2"])[0] == pytest.approx(350.0)
    assert np.asarray(fast["Rounds_2"])[0] < 1.0


def test_fractional_friction_is_not_truncated():
    """It was: the friction grid held INTEGERS, so -0.9 became 0 and
    the facilitator was accepted and silently ignored. Barriers were
    unaffected because whole numbers survive truncation, which is
    why it went unnoticed."""
    from equipop.friction import points_to_friction
    from equipop.stata_bridge import dispatch
    x = np.array([0.0, 100.0, 200.0])
    y = np.zeros(3)
    ys = np.zeros(3)
    road = points_to_friction(np.array([0.0, 100.0, 200.0]), ys,
                              np.full(3, -0.75), unit_size=50.0)
    res = dispatch("friction", x, y, unit_size=50.0, k_values=[3],
                   weight=np.ones(3), friction_file=road)
    rounds = float(np.asarray(res["Rounds_3"])[0])
    # four steps at 0.25 each, not four steps at 1 each: a truncated
    # grid would give a whole number
    assert rounds < 3.0, f"friction was truncated: Rounds_3 = {rounds}"
    assert rounds != round(rounds), "looks like an integer grid"


@pytest.mark.parametrize("value", [-1.0, -1.5, -20.0])
def test_free_movement_is_refused_with_the_floor_named(value):
    """-1 makes a cell free, which is not a neighbourhood: k could
    be gathered from anywhere at no cost."""
    from equipop.friction import points_to_friction
    with pytest.raises(ValueError) as e:
        points_to_friction(np.zeros(3), np.arange(3.0) * 50,
                           np.full(3, value), unit_size=50.0)
    msg = str(e.value)
    assert "-1 is the floor" in msg
    assert "-0.5 halves" in msg and "facilitator" in msg


# ------------------------------- refusals that read (v1.27)
def test_a_line_layer_as_INPUT_is_refused_in_words():
    """John, field: choosing the roads layer as the input gave a raw
    TypeError from deep inside the reader."""
    import qgis_stub as Q
    from qgis.core import QgsGeometry
    t = pd.DataFrame({"friction": [3.0, 3.0]})
    src = Q.source_from(t, geometry=False)
    feats = list(src.getFeatures())
    for f in feats:
        f.setGeometry(QgsGeometry.fromParts(
            [[(0.0, 0.0), (100.0, 0.0)]], wkb=2))
    src.getFeatures = lambda *a: iter(feats)
    src.wkbType = lambda: 2
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, src, k="2")
    msg = str(e.value)
    assert "measures what is around POINTS" in msg
    assert "lines" in msg and "BARRIER box" in msg


def test_a_barrier_smaller_than_one_cell_is_refused_before_the_engine():
    """Malta's roads against Sweden's POIs: the geographic problem
    must be reported before the engine complains about values."""
    from equipop_qgis.barriers import _extent_check
    feats = [{"type": "line",
              "parts": [[(14.40, 35.85), (14.55, 35.90)]]}]
    with pytest.raises(QgsProcessingException) as e:
        _extent_check(feats, [3.0], 100.0, "Barrier layer",
                      CountsAndShares.channel(QgsProcessingFeedback()))
    assert "less than one 100 m cell" in str(e.value)
    assert "DEGREES" in str(e.value)


def test_a_version_mismatch_is_mentioned_once():
    from equipop_qgis.base import check_versions
    fb = QgsProcessingFeedback()
    import equipop_qgis
    real = equipop_qgis.__version__
    try:
        equipop_qgis.__version__ = "9.9.9"
        check_versions(CountsAndShares.channel(fb))
    finally:
        equipop_qgis.__version__ = real
    said = " ".join(fb.warnings)
    # 9.9.9 makes the PLUGIN the newer half, so the advice is to
    # install the matching WHEEL. It used to say "pip install
    # --upgrade equipop" whichever half was ahead, which is useless
    # when the plugin came from a zip: pip only sees published
    # releases (BACKLOG 249).
    assert "9.9.9" in said
    # BOTH routes, because the message cannot know what is published.
    assert ".whl" in said and "--upgrade" in said


def test_the_barrier_block_lives_under_advanced():
    """v1.28, John: six boxes most runs never touch were the largest
    source of clutter in a flat list."""
    alg = CountsAndShares()
    alg.initAlgorithm()
    adv = _advanced_names(alg)
    assert {"barrier", "barrierfield", "barrierraster", "dem", "tau",
            "roundtrip", "barrieragg"} <= adv
    everyday = {p.name() for p in
                alg.parameterDefinitions()} - adv
    assert {"refmode", "treatmode", "k", "model"} <= everyday


def test_the_help_says_where_the_effort_engine_went():
    """Pro's collapsed section still shows its name; QGIS's Advanced
    area does not, so the help has to say it."""
    alg = CountsAndShares()
    alg.initAlgorithm()
    text = alg.shortHelpString()
    assert "Advanced parameters" in text
    assert "barriers and terrain" in text.lower()


# ------------------------- v1.29.2: the door opens with nothing behind it
_QGIS_NO_PACKAGE = r'''
import os, sys
ROOT = r"{root}"
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "qgis"))
import qgis_stub
qgis_stub.install()

# make `equipop` genuinely unimportable, as on a machine where pip
# was never run
for m in [m for m in sys.modules if m.split(".")[0] == "equipop"]:
    del sys.modules[m]


class _Block:
    def find_spec(self, name, path=None, target=None):
        if name == "equipop" or name.startswith("equipop."):
            raise ImportError("no equipop here")
        return None


sys.meta_path.insert(0, _Block())

# the plugin must still IMPORT, register both algorithms, and build
# its dialogs - the explanation belongs at Run, not at load
from equipop_qgis.provider import EquipopProvider
prov = EquipopProvider()
prov.loadAlgorithms()
names = sorted(a.name() for a in prov._algs)
assert sorted(names) == ["continentalrasters", "countsandshares",
                         "spatialdatafetch", "spatialdemography",
                         "valuestatistics"], names
for alg in prov._algs:
    alg.initAlgorithm()
    assert alg.parameterDefinitions(), "no boxes built"
    txt = alg.shortHelpString()
    assert "pip install" in txt, txt[:200]
print("OK")
'''


def test_the_plugin_still_loads_when_the_package_is_missing():
    """v1.29.2, BACKLOG 78. QGIS imports a plugin at STARTUP. Until
    now alg_counts.py called _decay_choices() at module level, so a
    missing or OLD package killed the import - and with it the whole
    plugin, before QGIS had an algorithm to attach a message to. Every
    guard written for exactly that situation (check_versions, the
    DoorError contract, the 'install equipop' sentence) lives inside
    processAlgorithm and could never run. A guard downstream of its
    own failure is not a guard.

    Pro learned this in 1.16 and has had this test since; the QGIS
    door never inherited it, and it cost John an hour in the field.

    Separate interpreter, because it must make equipop genuinely
    unimportable."""
    import subprocess
    out = subprocess.run(
        [sys.executable, "-c", _QGIS_NO_PACKAGE.replace("{root}", ROOT)],
        capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr[-2000:]
    assert "OK" in out.stdout


_QGIS_OLD_PACKAGE = r'''
import os, sys
ROOT = r"{root}"
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "qgis"))
import qgis_stub
qgis_stub.install()

for m in [m for m in sys.modules if m.split(".")[0] == "equipop"]:
    del sys.modules[m]


class _Old:
    """An equipop that IS installed but predates decaynames - John's
    machine on 2026-08-05: plugin 1.29.0, package 1.27.0."""

    def find_spec(self, name, path=None, target=None):
        if name == "equipop.doors.decaynames":
            raise ImportError(
                "No module named 'equipop.doors.decaynames'")
        return None


sys.meta_path.insert(0, _Old())

from equipop_qgis.provider import EquipopProvider
prov = EquipopProvider()
prov.loadAlgorithms()
assert len(prov._algs) == 5, prov._algs
for alg in prov._algs:
    alg.initAlgorithm()
    assert alg.parameterDefinitions(), "no boxes built"
# the rest of the package still works, so the words are still there
assert "neighbourhood" in prov._algs[0].shortHelpString().lower()
print("OK")
'''


def test_the_plugin_still_loads_when_the_package_is_a_release_behind():
    """v1.29.2, BACKLOG 78 - the exact shape of John's field failure.

    A package that is INSTALLED but older than the plugin is the
    common case, not the rare one: the plugin folder is replaced by
    hand while pip is a separate step that is easy to forget. It is
    also the harder case, because `import equipop` succeeds and only
    the newest module inside it is absent, so a naive check for the
    package finds one and reports all well.

    The plugin must load anyway. An out-of-date half is a sentence,
    never a traceback."""
    import subprocess
    out = subprocess.run(
        [sys.executable, "-c", _QGIS_OLD_PACKAGE.replace("{root}", ROOT)],
        capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr[-2000:]
    assert "OK" in out.stdout


# ------------------------------ v1.29.2: machine 2's reference ladder
def _mixed_town(n=600):
    """Half residents, half workplaces, with clearly different
    incomes - so a restriction that fails to bite is obvious."""
    rng = np.random.default_rng(292)
    kind = np.where(np.arange(n) % 2 == 0, "resident", "workplace")
    return pd.DataFrame({
        "x": rng.uniform(0, 3000, n),
        "y": rng.uniform(0, 3000, n),
        "kind": kind,
        "Income": np.where(kind == "resident", 200.0, 900.0),
        "People": np.where(kind == "resident", 4.0, 1.0),
    })


def test_machine2_ladder_restricts_who_is_around():
    """BACKLOG 76. Machine 2 could not restrict its reference
    population at all: every row was automatically in it. "The mean
    income of the nearest 400 RESIDENTS" in a layer that also holds
    workplaces was impossible.

    Rung 3 makes it possible, and John's rule decides the rest: a row
    outside the reference population weighs ZERO - it enters no
    statistic - but it STILL GETS ITS OWN RESULTS. Zeros stay
    invisible and are placeholders for output only (John, 1.29.2).
    """
    t = _mixed_town()
    src = qgis_stub._Source(t, "EPSG:3006")

    everyone, _ = _run(ValueStatistics, src, pop="People",
                       values=["Income"], measures=[0], k="100")
    residents, fb = _run(ValueStatistics, src, pop="People",
                         values=["Income"], measures=[0], k="100",
                         refmode=2, catfield="kind",
                         reftable=["resident"], keepoutside=0)

    col = "Mean_Income_100"
    assert col in everyone and col in residents

    # unrestricted: a blend of 200 and 900. restricted: residents only.
    assert everyone[col].mean() > 300, "workplaces should pull it up"
    assert abs(residents[col].mean() - 200.0) < 1e-6, (
        "with only residents in the reference population every mean "
        f"must be 200; got {residents[col].mean()}")

    # ...and the excluded rows are still THERE as rows
    assert len(residents) == len(t), "rows outside must not be dropped"

    # ...and BACKLOG 83: a non-member still gets its own results.
    # A workplace weighs zero and enters nobody's statistic, but it
    # may still ask what is around IT - and what is around it is
    # residents, so it reads 200 like everyone else. Machine 1 has
    # always done this; machine 2 dropped such rows until v1.29.2,
    # because expanding rows by their count makes a zero-count row
    # vanish. ORIGIN and MEMBER are now separate sets.
    outside = (t["kind"] == "workplace").to_numpy()
    assert residents[col][outside].notna().all(), (
        "a workplace is nobody's neighbour, but it still gets to ask "
        "what is around IT (John's rule, 1.22.2)")
    assert abs(residents[col][outside].mean() - 200.0) < 1e-6, (
        "a non-member sees the same residents everyone else sees")

    # the Null half of the same choice: keepoutside=1 drops them
    dropped, _ = _run(ValueStatistics, src, pop="People",
                      values=["Income"], measures=[0], k="100",
                      refmode=2, catfield="kind",
                      reftable=["resident"], keepoutside=1)
    assert dropped[col][outside].isna().all(), (
        "'leave their results Null' must still mean Null - the "
        "choice is the user's (John's ruling, BACKLOG 83)")
    assert dropped[col][~outside].notna().all(), (
        "...but members keep their results either way")


def test_a_polygon_barrier_reaches_the_engine_in_one_piece():
    """v1.29.3, John's field crash on gridby_lake_polygon.shp:
    "'float' object is not subscriptable" in paths_to_friction.

    The engine wants LINES as points per part and POLYGONS as RINGS
    per part - a polygon may have holes, and it is charged by AREA
    as outer ring minus inner ones. barriers.py flattened polygons to
    a bare list of rings, so `for ring in part` walked the POINTS of
    one ring and p[0] met a float.

    It survived because the QGIS tests had NO polygon barrier at all.
    The simulator was right this time; nobody asked it the question.
    BACKLOG 67 said in as many words that QGIS barriers were
    simulator-proved only - this is what that meant.
    """
    from equipop_qgis.barriers import _paths_of

    square = [qgis_stub.QgsPointXY(0, 0), qgis_stub.QgsPointXY(0, 300),
              qgis_stub.QgsPointXY(300, 300), qgis_stub.QgsPointXY(300, 0),
              qgis_stub.QgsPointXY(0, 0)]
    poly = qgis_stub.QgsGeometry.fromPolygonXY([square])
    parts = _paths_of(poly)

    assert len(parts) == 1, "one polygon, one part"
    ring = parts[0][0]
    assert isinstance(ring, list) and isinstance(ring[0], tuple), (
        "a polygon part must hold RINGS of (x, y) - flattening it to "
        "a list of points is the field crash")
    assert len(ring) >= 4

    # ...and the engine accepts it
    from equipop.friction import paths_to_friction
    fr = paths_to_friction([{"type": "polygon", "parts": parts}],
                           [5.0], 100.0)
    assert len(fr) > 0, "the lake should charge some cells"

    # a LINE must keep the flat shape - the two are different
    line = qgis_stub.QgsGeometry.fromPolylineXY(
        [qgis_stub.QgsPointXY(0, 0), qgis_stub.QgsPointXY(500, 0)])
    lparts = _paths_of(line)
    assert isinstance(lparts[0][0], tuple), \
        "a line part is points, not rings"


@pytest.mark.parametrize("label,params,expected",
                         [(c[0], c[1], c[2]) for c in
                          __import__("door_parity").LADDER_CASES])
def test_every_ladder_combination_produces_the_columns_it_should(
        label, params, expected):
    """BACKLOG 86. Names were checked; behaviour never was.

    QGIS nested the treatment ladder inside the reference ladder, so
    `refmode=0` with `treatmode=2` quietly produced distances only -
    no T_, no R_, no message (John, field, 3.42.1). Both doors
    offered the same boxes throughout, which is all door_parity.py
    could see.

    Every rung combination must yield the columns it promises. A
    combination nobody lists is a combination nobody checks."""
    rng = np.random.default_rng(86)
    n = 400
    t = pd.DataFrame({
        "x": rng.uniform(0, 2000, n), "y": rng.uniform(0, 2000, n),
        "fclass": rng.choice(["cafe", "bar", "school"], n),
        "Population": rng.integers(1, 6, n).astype(float)})
    src = qgis_stub._Source(t, "EPSG:32633")
    got, _ = _run(CountsAndShares, src, k="100", **params)
    stems = {c.rsplit("_", 1)[0] for c in got.columns
             if c.startswith(("N_", "Dist_", "T_", "R_"))}
    assert stems == expected, (
        f"[{label}] expected {sorted(expected)}, got {sorted(stems)} "
        "- the two ladders are independent, so a reference rung must "
        "never switch the treatment side off")


def test_no_deprecated_qgis_api_is_called():
    """BACKLOG 84. QGIS 3.42 warned on every one of John's runs:
    parameterAsFields() (deprecated 3.40, use parameterAsStrings) and
    the older typed QgsField constructor (QMetaType since 3.38).
    Warnings, not errors - until QGIS removes them, at which point
    the door stops opening exactly as it did on 2026-08-05.

    Note what NO tool of ours could see: stub_audit.py checks that a
    method EXISTS, and a deprecated method exists perfectly well. The
    simulator cannot represent "this works but is dying" at all. The
    guard that found these was John reading the QGIS log."""
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    door = os.path.join(os.path.dirname(here), "qgis", "equipop_qgis")
    gone = {"parameterAsFields": "use parameterAsStrings (3.32+)",
            "QVariant.Double": "use QMetaType.Type.Double (3.38+)",
            "QVariant.String": "use QMetaType.Type.QString (3.38+)"}
    bad = []
    for f in sorted(os.listdir(door)):
        if not f.endswith(".py"):
            continue
        for i, line in enumerate(open(os.path.join(door, f),
                                      encoding="utf-8"), 1):
            code = line.split("#")[0]
            for name, why in gone.items():
                if name in code:
                    bad.append(f"{f}:{i} {name} - {why}")
    assert not bad, "deprecated QGIS API in use:\n  " + "\n  ".join(bad)


def test_the_declared_minimum_matches_the_api_actually_used():
    """v1.29.3. The 1.29.3 build shipped with the minimum still at
    3.28 while the code had already moved to QMetaType (3.38) and
    parameterAsStrings (3.32) - caught by checking the artifact after
    staging, not by any test. A promise in metadata.txt that the code
    cannot keep is a plugin that installs and then fails."""
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    meta = os.path.join(os.path.dirname(here), "qgis", "equipop_qgis",
                        "metadata.txt")
    line = [l for l in open(meta, encoding="utf-8")
            if l.startswith("qgisMinimumVersion")]
    assert line, "no qgisMinimumVersion declared"
    got = tuple(int(x) for x in line[0].split("=")[1].strip().split("."))
    assert got >= (3, 38), (
        f"declared minimum {got} is below 3.38, but the door uses "
        "QMetaType field types (3.38) and parameterAsStrings (3.32)")


# ---------------------------------------------- BACKLOG 95, behaviour
def _dense_cell_source(n_dense=200, n_spread=400, seed=95):
    """200 people inside ONE 100 m cell, so k=100 is satisfied without
    leaving it - the case where Dist_k used to be zero."""
    rng = np.random.default_rng(seed)
    t = pd.DataFrame({
        "x": np.concatenate([rng.uniform(1, 99, n_dense),
                             rng.uniform(500, 4000, n_spread)]),
        "y": np.concatenate([rng.uniform(1, 99, n_dense),
                             rng.uniform(500, 4000, n_spread)])})
    return qgis_stub._Source(t, "EPSG:32633"), n_dense


def test_self_potential_is_honoured_by_the_qgis_door():
    """BACKLOG 95, and the lesson of 85: offering a box is not
    honouring it. door_parity.py compares NAMES, and LADDER_CASES
    compares COLUMNS - self-potential changes neither, it changes
    NUMBERS. So it is checked here against the closed form, in both
    doors separately, or it could be dropped on one side in silence.
    """
    src, n_dense = _dense_cell_source()

    # BACKLOG 141: a three-way ENUM now, not a free number.
    # Index 0 = none, 2 = the equal-area radius (the default).
    off, _ = _run(CountsAndShares, src, k="100", selfpot=[0])
    dense_off = off.loc[(off["x"] < 100) & (off["y"] < 100), "Dist_100"]
    assert len(dense_off) == n_dense
    assert (dense_off == 0.0).all(), \
        "self-potential 0 must reproduce pre-1.29.5 numbers exactly"

    on, _ = _run(CountsAndShares, src, k="100", selfpot=[2])
    dense_on = on.loc[(on["x"] < 100) & (on["y"] < 100), "Dist_100"]
    expected = np.sqrt(100.0 ** 2 * 100 / (n_dense * np.pi))
    assert np.allclose(dense_on, expected, rtol=1e-9), (
        f"expected the equal-area radius {expected:.4f} m, got "
        f"{dense_on.iloc[0]:.4f} m - the box is offered but not "
        "reaching the engine")

    # and the setting must not disturb origins that never needed it
    far = ~((on["x"] < 100) & (on["y"] < 100))
    assert np.allclose(off.loc[far, "Dist_100"],
                       on.loc[far, "Dist_100"], rtol=1e-12)


# ---------------------------------------------------------------------
# BACKLOG 237. The two doors had DRIFTED on three of four tool names -
# Pro still said "3. Continental run from a folder of rasters" long
# after QGIS was renamed, and machines 1 and 2 differed in their
# parenthetical. door_parity.py checked parameter NAMES but never
# LABELS, so nothing noticed. A name in two places drifts exactly like
# a rule in two places.
# ---------------------------------------------------------------------
def test_the_two_doors_call_every_tool_the_same_thing():
    from equipop.doors.help import LABELS
    from equipop_qgis.alg_continental import ContinentalRasters
    from equipop_qgis.alg_counts import CountsAndShares
    from equipop_qgis.alg_demography import SpatialDemography
    from equipop_qgis.alg_stats import ValueStatistics

    qgis = {"CountsShares": CountsAndShares().displayName(),
            "ValueStatistics": ValueStatistics().displayName(),
            "ContinentalRasters": ContinentalRasters().displayName(),
            "SpatialDemography": SpatialDemography().displayName()}
    for key, name in qgis.items():
        assert name == LABELS[key], (
            f"QGIS calls it {name!r}, the shared list says "
            f"{LABELS[key]!r}")

    pyt = (Path(ROOT) / "arcgis" / "EquiPop.pyt").read_text(encoding="utf-8")
    for key, name in LABELS.items():
        assert f'self.label = "{name}"' in pyt, (
            f"ArcGIS Pro does not call {key} {name!r}")


def test_the_label_is_written_down_and_not_imported():
    """displayName runs while QGIS BUILDS THE TOOLBOX, so importing the
    package there kills the plugin when equipop is absent - BACKLOG
    218, reintroduced while fixing 237 and caught the same day. The
    test above pins the written-down value against the package, which
    is how it can be both safe and correct.
    """
    import re
    for f in ("alg_counts.py", "alg_stats.py", "alg_continental.py",
              "alg_demography.py"):
        src = (Path(ROOT) / "qgis" / "equipop_qgis" / f).read_text(
            encoding="utf-8")
        m = re.search(r"def displayName\(self\):\n(?:.*\n)*?        return .*",
                      src)
        assert m and "import" not in m.group(0), (
            f"{f}: displayName must not import anything")


def test_the_version_advice_depends_on_WHICH_half_is_newer():
    """BACKLOG 249. The message always said "pip install --upgrade
    equipop", which is useless when the PLUGIN is ahead: pip only sees
    PUBLISHED releases, and a plugin installed from a zip is normally
    newer than anything on PyPI. John followed that advice across
    three versions and pip correctly fetched the newest release each
    time - never the one he had.
    """
    from equipop_qgis.base import _newer
    assert _newer("1.44.0", "1.43.4")
    assert not _newer("1.43.4", "1.44.0")
    # and NUMERICALLY, not as text: "1.44.0" < "1.5.0" as strings,
    # which would give exactly the wrong advice at the next bump
    assert _newer("1.44.0", "1.5.0")
    assert not _newer("1.5.0", "1.44.0")


def test_the_mismatch_message_offers_BOTH_routes():
    """BACKLOG 249, corrected. Claude first made this say "install the
    wheel" whenever the plugin was ahead, assuming a newer plugin
    meant an unpublished build - and was WRONG on the very case that
    prompted it: 1.44.0 was on PyPI all along.

    The message cannot know what is published, so it offers both and
    names John's ACTUAL problem first: `pip install equipop` does
    nothing when any version is already present.
    """
    from equipop_qgis.base import check_versions

    class Ch:
        def __init__(self):
            self.said = []

        def info(self, m):
            self.said.append(str(m))

        def warning(self, m):
            self.said.append(str(m))

    import equipop
    import equipop_qgis
    was = (equipop.__version__, equipop_qgis.__version__)
    try:
        equipop.__version__, equipop_qgis.__version__ = "1.43.4", "1.44.0"
        ch = Ch()
        check_versions(ch)
        said = " ".join(ch.said)
        assert "--upgrade" in said, "the published route"
        assert ".whl" in said, "the local-build route"
        assert "plain `pip install` does nothing" in said, (
            "name the thing that actually happened")
        assert "plugin is ahead" in said
    finally:
        equipop.__version__, equipop_qgis.__version__ = was
