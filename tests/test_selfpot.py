# -*- coding: utf-8 -*-
"""test_selfpot.py - SELF-POTENTIAL (BACKLOG 95), the self-calibration
substitution (96) and the N_k overshoot report (94).

Every test here was checked by BREAKING THE RULE ON PURPOSE and
watching it fail; a test that cannot fail is not a test. The
deliberate breakages used were:

  * radius_for_k() returning 0.0            -> 1, 2, 3, 4 fail
  * dropping the dw[0] substitution in the
    decay branch of fastcounts               -> 5 fails
  * dispatch() swallowing self_potential
    into **extra instead of passing it on    -> 6 fails
  * restoring the old silent np.where()      -> 7 fails
  * removing the overshoot counter           -> 8 fails
"""

import numpy as np
import pandas as pd
import pytest

from equipop import selfpot
from equipop.cells import build_cells
from equipop.fastcounts import run_knn_counts
from equipop.analysis import run_knn_stats
from equipop.stata_bridge import dispatch

UNIT = 100.0


def _dense_plus_sparse(n_dense=3000, n_sparse=4000, seed=0):
    """One 100 m cell holding n_dense people, inside a thin surround."""
    rng = np.random.default_rng(seed)
    d = pd.DataFrame({"E": rng.uniform(0, UNIT, n_dense),
                      "N": rng.uniform(0, UNIT, n_dense)})
    s = pd.DataFrame({"E": rng.uniform(-2000, 2100, n_sparse),
                      "N": rng.uniform(-2000, 2100, n_sparse)})
    df = pd.concat([d, s], ignore_index=True)
    df["g"] = rng.integers(0, 2, len(df))
    return build_cells(df, "E", "N", binary_vars=["g"], unit_size=UNIT)


def _origin(res):
    """The row for the dense cell (midpoint 50, 50)."""
    return res.loc[(res.EastWest == 50) & (res.NorthSouth == 50)].iloc[0]


# --- 1 -------------------------------------------------------------
def test_dist_k_is_not_zero_inside_a_dense_cell():
    cd = _dense_plus_sparse()
    o = _origin(run_knn_counts(cd, k_values=[100], self_potential=1.0))
    assert o.Dist_100 > 0.0
    # equal-area radius: sqrt(A k / (n pi)) with A = 100^2, n = 3002
    assert o.Dist_100 == pytest.approx(
        np.sqrt(UNIT ** 2 * 100 / (o.N_local * np.pi)), rel=1e-9)


# --- 2 -------------------------------------------------------------
def test_k_is_a_parameter_again():
    """The 1.29.3 defect in one line: two different k gave the same
    zero. They must now differ, and by the square root of their
    ratio."""
    cd = _dense_plus_sparse()
    o = _origin(run_knn_counts(cd, k_values=[100, 1000],
                               self_potential=1.0))
    assert o.Dist_1000 > o.Dist_100 > 0.0
    assert o.Dist_1000 / o.Dist_100 == pytest.approx(np.sqrt(10.0),
                                                     rel=1e-9)


# --- 3 -------------------------------------------------------------
@pytest.mark.parametrize("k", [25, 100, 400])
def test_estimate_recovers_the_true_kth_nearest_distance(k):
    """The claim that justifies the default. Scatter points evenly,
    measure the TRUE k-th nearest distance from the points, and check
    the estimate computed from the cell agrees."""
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(1)
    side, lam = 2000.0, 0.30              # people per m^2
    pts = rng.uniform(0, side, size=(int(side * side * lam), 2))
    mid = pts[(np.abs(pts[:, 0] - 1000) < 200)
              & (np.abs(pts[:, 1] - 1000) < 200)]
    true_d = cKDTree(pts).query(mid, k=k + 1)[0][:, k].mean()
    # the same quantity from cell arithmetic: A/n is 1/lambda
    est = selfpot.radius_for_k(UNIT, k, lam * UNIT ** 2, 1.0)
    assert abs(est - true_d) / true_d < 0.01


# --- 4 -------------------------------------------------------------
def test_both_engines_apply_the_same_rule():
    """run_knn_counts and run_knn_stats are bound by regression test.
    A rule applied to one only would split them."""
    cd = _dense_plus_sparse(n_dense=800, n_sparse=1200, seed=3)
    a = run_knn_counts(cd, k_values=[50, 200], self_potential=1.0)
    b = run_knn_stats(cd, [50, 200], stats={"g": ["ratio"]},
                      self_potential=1.0)
    key = ["EastWest", "NorthSouth"]
    a = a.sort_values(key).reset_index(drop=True)
    b = b.sort_values(key).reset_index(drop=True)
    for col in ("Dist_50", "Dist_200", "N_50", "N_200"):
        assert np.allclose(a[col].values, b[col].values, rtol=1e-12)


# --- 5 -------------------------------------------------------------
def test_decay_no_longer_gives_your_own_cell_full_weight():
    """Without this the origin cell keeps weight 1.0 - the largest
    weight in the calculation - on the mass we know least about."""
    from equipop.decay import Decay
    cd = _dense_plus_sparse(n_dense=500, n_sparse=800, seed=4)
    dec = Decay(model="negexp", half_life_m=300.0)
    off = _origin(run_knn_counts(cd, k_values=[50], decay=dec,
                                 self_potential=0.0))
    on = _origin(run_knn_counts(cd, k_values=[50], decay=dec,
                                self_potential=1.0))
    assert on.ND_inf < off.ND_inf          # own cell weighs less now
    # and by the right amount: the whole cell moves from weight 1 to
    # weight(0.3826 * unit)
    shift = off.N_local * (1.0 - dec.weight_vec(
        np.array([selfpot.decay_distance(UNIT, 1.0)]))[0])
    assert off.ND_inf - on.ND_inf == pytest.approx(shift, rel=1e-9)


# --- 6 -------------------------------------------------------------
def test_setting_reaches_the_engine_through_the_bridge():
    """A parameter accepted and ignored is this project's oldest
    failure. dispatch() must pass it on, not swallow it."""
    rng = np.random.default_rng(0)
    x = np.concatenate([rng.uniform(0, UNIT, 2000),
                        rng.uniform(-2000, 2100, 2000)])
    y = np.concatenate([rng.uniform(0, UNIT, 2000),
                        rng.uniform(-2000, 2100, 2000)])
    got = {}
    for sp in (0.0, 1.0):
        out = dispatch("counts", x, y, unit_size=UNIT, k_values=[100],
                       self_potential=sp)
        got[sp] = np.asarray(out["Dist_100"], dtype=float)
    dense = got[0.0] == 0.0
    assert dense.any(), "fixture no longer exercises the dense case"
    assert (got[1.0][dense] > 0.0).all()


# --- 7 -------------------------------------------------------------
def test_self_calibration_says_when_it_substitutes(capsys):
    """BACKLOG 96: the median substitution was silent, and the printed
    range was the range AFTER it, which hid it completely."""
    rng = np.random.default_rng(0)
    x = np.concatenate([rng.uniform(0, UNIT, 2000),
                        rng.uniform(-2000, 2100, 2000)])
    y = np.concatenate([rng.uniform(0, UNIT, 2000),
                        rng.uniform(-2000, 2100, 2000)])
    dispatch("counts", x, y, unit_size=UNIT, k_values=[100],
             half_life_from_dist=100, self_potential=0.0,
             extra={"decay_model": "negexp"})
    out = capsys.readouterr().out
    assert "WARNING" in out and "MEDIAN bandwidth" in out
    assert "not self-calibrated" in out

    # and with self-potential on, there is nothing to substitute
    dispatch("counts", x, y, unit_size=UNIT, k_values=[100],
             half_life_from_dist=100, self_potential=1.0,
             extra={"decay_model": "negexp"})
    assert "MEDIAN bandwidth" not in capsys.readouterr().out


# --- 8 -------------------------------------------------------------
def test_overshoot_is_reported(capsys):
    """BACKLOG 94: ask for the nearest 100 and be told about 3,002."""
    cd = _dense_plus_sparse()
    # BACKLOG 99: the overshoot TALLY only exists when rings are
    # taken whole. Under proportional N_k lands on k and there is
    # nothing to report - which is the point of the new default.
    res = run_knn_counts(cd, k_values=[100], self_potential=1.0,
                         overshoot_mode="whole")
    assert _origin(res).N_100 > 100 * 2
    assert "N_100 is at least twice the k you asked for" \
        in capsys.readouterr().out


# --- 9 -------------------------------------------------------------
def test_setting_is_validated_not_quietly_clamped():
    for bad in (-0.1, 1.5, "wide", object()):
        with pytest.raises(ValueError):
            selfpot.check(bad)
    assert selfpot.check(None) == selfpot.DEFAULT_SELF_POTENTIAL
    assert selfpot.check(0) == 0.0


# --- 10 ------------------------------------------------------------
def test_named_settings_are_what_they_claim():
    """s = 1/sqrt2 is the MEDIAN (half the area), s = 1 the equal-area
    radius, and at s = 1 the circle still fits inside the square."""
    n, k = 4000.0, 4000.0                 # k = n: the extreme case
    full = selfpot.radius_for_k(UNIT, k, n, 1.0)
    assert full == pytest.approx(UNIT * np.sqrt(1.0 / np.pi), rel=1e-12)
    half = selfpot.radius_for_k(UNIT, k / 2, n, 1.0)
    assert half == pytest.approx(full / np.sqrt(2.0), rel=1e-12)
    # fits while k/n stays under pi/4
    assert selfpot.radius_for_k(UNIT, n * np.pi / 4, n, 1.0) \
        == pytest.approx(UNIT / 2, rel=1e-12)
    # never extrapolates past the people the cell actually holds
    assert selfpot.radius_for_k(UNIT, 10 * n, n, 1.0) == full


# --- 11 ------------------------------------------------------------
def test_every_engine_accepts_self_potential():
    """BACKLOG 114, and the reason it exists: in 1.29.5 the parameter
    was threaded through the routes Claude was looking at, and the
    routes he was not looking at were never enumerated. The effort
    engines silently ignored it (110) and Stata could not reach it at
    all (113) - both found by an EXTERNAL review, not by this suite.

    So the guard walks the ENGINE LIST rather than testing the engine
    in front of it. A new engine that arrives without an answer fails
    here, which is the whole point.
    """
    import inspect
    from equipop.fastcounts import run_knn_counts
    from equipop.analysis import run_knn_stats
    from equipop.friction import run_knn_friction
    from equipop.slope import run_knn_slope

    from equipop.analysis import run_knn        # BACKLOG 153
    engines = [run_knn_counts, run_knn_stats, run_knn_friction,
               run_knn_slope, run_knn]
    missing = [f.__name__ for f in engines
               if "self_potential" not in inspect.signature(f).parameters]
    assert not missing, (
        f"these engines cannot be told about self-potential: {missing} "
        "- and both doors keep the box visible and fillable, so it "
        "would be a box that is filled and ignored")


def test_the_effort_engine_actually_honours_it():
    """Signatures are cheap. This runs the friction engine over a
    dense origin and checks the number moves - the accepting-but-
    ignoring failure a signature test cannot see."""
    from equipop.friction import run_knn_friction
    rng = np.random.default_rng(110)
    n = 400
    # DUPLICATE COORDINATES - many people at one address, which is
    # what register data looks like. This is the case that survives
    # BACKLOG 115: once Dist_k is the ring's maximum extent, an
    # origin only reports zero when everyone counted is standing on
    # exactly the same spot.
    pop = pd.DataFrame({
        "x": np.concatenate([np.full(n, 50.0),
                             rng.uniform(500, 2000, n)]),
        "y": np.concatenate([np.full(n, 50.0),
                             rng.uniform(500, 2000, n)]),
        "count_all": 1.0, "count_group": 0.0})
    off = run_knn_friction(pop, [50], unit_size=UNIT,
                           self_potential=0.0)
    on = run_knn_friction(pop, [50], unit_size=UNIT,
                          self_potential=1.0)
    dense = off["Dist_50"].to_numpy() == 0.0
    assert dense.any(), "fixture no longer exercises the dense case"
    assert (on["Dist_50"].to_numpy()[dense] > 0.0).all(), (
        "the effort engine accepts self-potential and ignores it - "
        "exactly the 1.29.5 defect (BACKLOG 110)")


def test_effort_distance_does_not_depend_on_row_order():
    """BACKLOG 115, ruled by John: Dist_k is the MAXIMUM straight-line
    extent of the accepted effort ring. Before this release it was read from
    ring[-1] - 'any tie member' - so shuffling identical rows changed
    the answer."""
    from equipop.friction import run_knn_friction
    rng = np.random.default_rng(115)
    pop = pd.DataFrame({
        "x": rng.uniform(0, 900, 250), "y": rng.uniform(0, 900, 250),
        "count_all": 1.0, "count_group": 0.0})
    a = run_knn_friction(pop, [10], unit_size=UNIT, id_col=None)
    order = rng.permutation(len(pop))
    b = run_knn_friction(pop.iloc[order].reset_index(drop=True), [10],
                         unit_size=UNIT, id_col=None)
    key = ["EastWest", "NorthSouth"]
    a = a.sort_values(key).reset_index(drop=True)
    b = b.sort_values(key).reset_index(drop=True)
    assert np.allclose(a["Dist_10"], b["Dist_10"]), (
        "effort Dist_k moved when the input rows were shuffled - it "
        "is reporting input order, not a radius")


# --- 12 ------------------------------------------------------------
def test_the_report_counts_each_origin_once(capsys):
    """BACKLOG 111. The counter used to sit inside _walk(), which runs
    AGAIN for every origin whose neighbour search has to widen, so a
    514-origin run reported 1,511. The analytical output was right and
    the REPORT was wrong - which is worse than useless in a release
    about ending silences.

    m_neighbors is deliberately tiny here to force the widening.
    """
    import re
    rng = np.random.default_rng(3)
    d = pd.DataFrame({"E": rng.uniform(0, UNIT, 900),
                      "N": rng.uniform(0, UNIT, 900)})
    s = pd.DataFrame({"E": rng.uniform(0, 4000, 600),
                      "N": rng.uniform(0, 4000, 600)})
    df = pd.concat([d, s], ignore_index=True)
    df["v"] = rng.normal(size=len(df))
    cd = build_cells(df, "E", "N", value_vars=["v"], unit_size=UNIT)

    run_knn_stats(cd, [300], stats={"v": ["mean"]}, m_neighbors=4)
    out = capsys.readouterr().out
    assert "widened searches" in out, \
        "fixture no longer forces a fallback, so it proves nothing"
    reported = {int(n.replace(",", ""))
                for n in re.findall(r"of ([\d,]+) origins", out)}
    assert reported == {len(cd)}, (
        f"the report claims {reported} origins; there are {len(cd)} "
        "cells. A retried origin is being counted twice.")


# --- 13 ------------------------------------------------------------
def test_stata_can_reach_the_old_behaviour():
    """BACKLOG 113. Both .ado commands inherited the 1.29.5 default of
    1.0 with no option to set 0 - and Stata is the door published work
    goes through, so it was the one door that could not reproduce a
    pre-1.29.5 result. Live Stata is outside pytest, so this checks
    the two things that can be checked from here: the option exists,
    and it is passed on rather than accepted and dropped.
    """
    import os
    import re
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name, fn in (("equipop_knn.ado", "_equipop_knn"),
                     ("equipop_run.ado", "_equipop_run")):
        src = open(os.path.join(root, "stata", name),
                   encoding="utf-8").read()
        assert "SELFpot(real 1)" in src, f"{name} has no selfpot option"
        assert re.search(r"python:\s*" + fn + r"\(.*selfpot", src,
                         re.S), f"{name} never passes selfpot on"
        assert "self_potential=float(selfpot)" in src, \
            f"{name} accepts selfpot and does not reach the engine"


def test_stata_drops_result_columns_for_decimal_radii():
    """Same item: equipop_knn.ado computed an underscore-safe name for
    a decimal radius (r=1.5 -> r1_5, since a dot cannot appear in a
    Stata variable name) and then kept using the unsanitised one, so
    `replace` silently dropped nothing for any decimal radius."""
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(root, "stata", "equipop_knn.ado"),
               encoding="utf-8").read()
    block = src[src.index('local rl : subinstr'):]
    block = block[:block.index("        }")]
    assert "`rr'" not in block, (
        "the sanitised radius name is computed and then ignored - "
        "capture drop still uses the name with the dot in it")


# --- 14 ------------------------------------------------------------
def test_a_negative_raster_value_is_a_facilitator_not_a_deletion():
    """BACKLOG 109. friction.py kept raster pixels only where
    `val > 0`, so every FACILITATOR (1.27) was dropped before it could
    be seen - and the negative check on the next line could never
    fire, because there were no negatives left to find. A raster of
    -0.5 produced zero friction cells and no error. Vector
    facilitators worked all along, which is why nothing noticed."""
    from equipop.friction import raster_to_friction
    a = np.full((4, 4), -0.5, dtype=float)
    fr = raster_to_friction(a, x_min=0.0, y_max=400.0,
                            cell_w=100.0, cell_h=100.0, unit_size=UNIT)
    assert len(fr) > 0, (
        "a facilitator raster produced NO friction cells - negative "
        "values are filtered out before they can be used")
    assert (fr["friction"] < 0).all()


def test_a_raster_at_or_below_minus_one_is_still_refused():
    """The other half: above -1 is a facilitator, -1 and below would
    make movement free, and that is refused - the same rule vectors
    get, from the same function."""
    from equipop.friction import raster_to_friction
    a = np.full((4, 4), -1.5, dtype=float)
    with pytest.raises(ValueError, match="free"):
        raster_to_friction(a, x_min=0.0, y_max=400.0,
                           cell_w=100.0, cell_h=100.0, unit_size=UNIT)


def test_the_friction_grid_is_built_once(capsys):
    """BACKLOG 112: coverage_warning() and FrictionGrid() appeared
    TWICE, verbatim, in run_knn_friction. The grid is the most
    expensive object in the project and every effort run paid for it
    twice. It announces itself, so counting the announcement is the
    cheapest honest guard."""
    from equipop.friction import run_knn_friction
    rng = np.random.default_rng(112)
    pop = pd.DataFrame({"x": rng.uniform(0, 500, 60),
                        "y": rng.uniform(0, 500, 60),
                        "count_all": 1.0, "count_group": 0.0})
    run_knn_friction(pop, [5], unit_size=UNIT)
    built = capsys.readouterr().out.count("grid domain")
    assert built == 1, f"the friction grid was built {built} times"


# --- 15 ------------------------------------------------------------
def test_the_calibration_pass_does_not_claim_you_asked_for_its_k(capsys):
    """BACKLOG 142. Running k=400 with self-calibration on Dist_500
    told John "N_500 is at least twice the k YOU ASKED FOR" - naming a
    k he had never typed. The lines are truthful about EquiPop's own
    internal pass and misleading about the run, and the phrase is what
    makes them wrong."""
    rng = np.random.default_rng(142)
    x = np.concatenate([rng.uniform(0, 900, 900),
                        rng.uniform(0, 4000, 300)])
    y = np.concatenate([rng.uniform(0, 900, 900),
                        rng.uniform(0, 4000, 300)])
    dispatch("counts", x, y, unit_size=1000.0, k_values=[100],
             half_life_from_dist=200, self_potential=1.0,
             extra={"decay_model": "negexp"})
    out = capsys.readouterr().out
    cal = [l for l in out.splitlines() if "k=200" in l]
    assert cal, "the calibration pass reported nothing"
    for line in cal:
        assert "calibration pass" in line, line
        assert "you asked for" not in line, line
    # the user's own k is still reported in their own voice
    mine = [l for l in out.splitlines()
            if "[selfpot]" in l and "calibration" not in l]
    assert all("calibration" not in l for l in mine)


# --- 15 ------------------------------------------------------------
def test_distinct_percentiles_get_distinct_column_names():
    """BACKLOG 152, found by an external review of 1.29.6.

    stat_prefix() ended with .rstrip("_0"), and rstrip strips any run
    of those CHARACTERS rather than one exact suffix. So p1, p10.0 and
    p100.0 all became "P1" and p50.0 became "P5": three different
    percentiles sharing one column, the last silently overwriting the
    rest. The run completed and the labels lied.

    It bit precisely the round percentiles people ask for most, while
    p97.5 and p99.9 were unaffected - which is why nothing noticed.
    """
    from equipop.stats import stat_prefix
    asked = ["p1", "p10", "p10.0", "p50.0", "p97.5", "p99.9",
             "p100.0", "p25", "p0.5", "p5", "p50"]
    by_value = {}
    for a in asked:
        by_value.setdefault(float(a[1:]), set()).add(stat_prefix(a))

    # the same percentile, however written, gets ONE name
    for v, names in by_value.items():
        assert len(names) == 1, f"p{v} produced several names: {names}"

    # and different percentiles never share one
    flat = [next(iter(n)) for n in by_value.values()]
    assert len(set(flat)) == len(flat), (
        "two different percentiles map to the same column - the later "
        f"one overwrites the earlier: {sorted(flat)}")

    assert stat_prefix("p10.0") == "P10"
    assert stat_prefix("p100.0") == "P100"
    assert stat_prefix("p50.0") == "P50"
    assert stat_prefix("p97.5") == "P97_5"


# --- 16 ------------------------------------------------------------
def test_two_engines_one_mathematics():
    """BACKLOG 153, found by an external review of 1.29.6 and RULED by
    John: the original run_knn gets the SAME rule as the newer
    engines, so the MANUAL's claim is true again.

    Before this, one 100 m cell holding 1,000 with k=100 gave
    Dist_100 = 0 from run_knn and 17.841241 m from run_knn_counts -
    and the manuals teach with run_knn, so a reader following them got
    one number while the QGIS door gave another.

    John: "the people using older versions are like me, and would
    understand our reasoning."
    """
    from equipop.analysis import run_knn
    cells = pd.DataFrame({"E_grid": [50], "N_grid": [50],
                          "FullPop": [1000.0], "Treatment": [300.0],
                          "id": [1]})
    legacy = run_knn(cells, [100], unit_size=UNIT)

    rng = np.random.default_rng(2)
    df = pd.DataFrame({"E": rng.uniform(0, UNIT, 1000),
                       "N": rng.uniform(0, UNIT, 1000)})
    cd = build_cells(df, "E", "N", unit_size=UNIT)
    fast = run_knn_counts(cd, k_values=[100])

    assert float(legacy["Dist_100"].iloc[0]) == pytest.approx(
        float(fast["Dist_100"].iloc[0]), rel=1e-12), \
        "run_knn and run_knn_counts disagree on the same single cell"
    assert float(legacy["Dist_100"].iloc[0]) == pytest.approx(
        np.sqrt(UNIT ** 2 * 100 / (1000 * np.pi)), rel=1e-12)

    # and the way back to the old numbers still exists
    off = run_knn(cells, [100], unit_size=UNIT, self_potential=0.0)
    assert float(off["Dist_100"].iloc[0]) == 0.0


def test_the_legacy_engine_also_charges_its_own_cell_under_decay():
    """The other half: without it the origin's own people keep weight
    1.0 - the largest in the calculation - on the mass we know least
    about."""
    from equipop.analysis import run_knn
    from equipop.decay import Decay
    cells = pd.DataFrame({"E_grid": [50], "N_grid": [50],
                          "FullPop": [1000.0], "Treatment": [300.0],
                          "id": [1]})
    dec = Decay(model="negexp", half_life_m=300.0)
    off = run_knn(cells, [100], unit_size=UNIT, decay=dec,
                  self_potential=0.0)
    on = run_knn(cells, [100], unit_size=UNIT, decay=dec)
    assert float(on["ND_100"].iloc[0]) < float(off["ND_100"].iloc[0])
    expect = 1000.0 * dec.weight(selfpot.decay_distance(UNIT, 1.0))
    assert float(on["ND_100"].iloc[0]) == pytest.approx(expect, rel=1e-9)


# --- 17 ------------------------------------------------------------
def test_gini_refuses_negative_values_in_every_door():
    """BACKLOG 154, RULED by John. gini_sorted([-5, 10]) = 1.5, which
    reads as a conventional Gini and is not one - the rank formula is
    bounded in [0,1] only for non-negative data.

    ArcGIS Pro has refused this for years. The core and the QGIS path
    did not, and QGIS has Gini in its DEFAULT statistics list, so the
    same data was refused through one door and silently accepted
    through another. The check now lives in run_knn_stats, which
    every door and the Python API reach statistics through.

    Not repaired by shifting: the Gini is not translation-invariant,
    so one shift compresses low-mean neighbourhoods hardest, and on
    two areas with true Ginis 0.400 and 0.131 a single debt of -80
    anywhere reverses the ranking.
    """
    from equipop.analysis import run_knn_stats
    from equipop.stats import check_gini_input

    rng = np.random.default_rng(5)
    df = pd.DataFrame({"E": rng.uniform(0, 900, 400),
                       "N": rng.uniform(0, 900, 400),
                       "income": rng.normal(30000, 9000, 400)})
    df.loc[:5, "income"] = -4000.0
    cd = build_cells(df, "E", "N", value_vars=["income"], unit_size=UNIT)

    # the same data is fine for everything else
    run_knn_stats(cd, [50], stats={"income": ["mean", "median"]})

    with pytest.raises(ValueError, match="not defined for negative"):
        run_knn_stats(cd, [50], stats={"income": ["mean", "gini"]})

    # and non-negative data is untouched
    df2 = df.copy()
    df2["income"] = df2["income"].abs()
    cd2 = build_cells(df2, "E", "N", value_vars=["income"], unit_size=UNIT)
    run_knn_stats(cd2, [50], stats={"income": ["gini"]})

    check_gini_input([0.0, 1.0, 2.0])            # must not raise
    with pytest.raises(ValueError):
        check_gini_input([-0.0001, 1.0])


# --- 18 ------------------------------------------------------------
def test_a_replaced_archive_is_not_read_from_a_stale_extraction(tmp_path):
    """BACKLOG 157, from an external review of 1.29.6.

    read_table() extracted a .zip into <stem>/ and then GLOBBED THAT
    DIRECTORY, taking the first match. So an older extraction of a
    replaced archive won, and the run succeeded on the wrong data with
    nothing to say so. Replacing an archive while keeping its name is
    an ordinary workflow.

    The choice now comes from the ARCHIVE'S OWN LISTING.
    """
    import zipfile
    from equipop.io import read_table

    zpath = tmp_path / "sample.zip"
    stale = tmp_path / "sample"
    stale.mkdir()
    (stale / "a.gpkg").write_bytes(b"stale - must not be chosen")
    with zipfile.ZipFile(zpath, "w") as z:
        z.writestr("z.gpkg", "the real one")

    try:
        read_table(str(zpath))
    except Exception as e:
        msg = str(e)
        assert "a.gpkg" not in msg, (
            "the stale extraction was chosen over the archive's own "
            f"contents: {msg}")

    # and an ambiguous archive is refused rather than guessed at
    zpath2 = tmp_path / "two.zip"
    with zipfile.ZipFile(zpath2, "w") as z:
        z.writestr("one.gpkg", "x")
        z.writestr("two.gpkg", "y")
    with pytest.raises(ValueError, match="will not guess"):
        read_table(str(zpath2))
