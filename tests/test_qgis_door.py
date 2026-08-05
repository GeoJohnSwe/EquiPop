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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "qgis"))

import qgis_stub                                    # noqa: E402

qgis_stub.install()

from qgis.core import (QgsProcessingException,      # noqa: E402
                       QgsProcessingFeedback)
from qgis.core import QgsProcessingParameterDefinition  # noqa: E402
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
    describes, and merged the way a user would end up with them."""
    counts, _ = _run(CountsAndShares, qgis_stub.gridby_source(),
                     refmode=[1], pop=SPEC["weight"],
                     treatmode=[1], treat=["count_group"],
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
    assert "ND_inf" in out.columns


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
    assert pm["treattable"].startswith("2b ")
    assert pm["k"].startswith("3 ")


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
    assert "9.9.9" in said and "pip install --upgrade equipop" in said


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
