# -*- coding: utf-8 -*-
"""test_selfrule.py - IS THE ORIGIN ITS OWN NEIGHBOUR? (BACKLOG 290).

The rule John ruled on in 1.47: two options, i=j (include, the default
and what every published EquiPop number used) and i!=j (exclude, the
w_ii = 0 convention spatial regression requires).

Every test here was checked by BREAKING THE RULE ON PURPOSE and
watching it fail; a test that cannot fail is not a test. The
deliberate breakages used were:

  * selfrule.DEFAULT set to EXCLUDE            -> 1, 2 fail
  * resolve() accepting any string             -> 3 fails
  * the `keep` mask in fastcounts._solve
    forced to None                             -> 4, 5, 8, 10 fail
  * the mask built as `position != 0` instead
    of `idx != origin`                         -> 6 fails
  * the slow engine still seeding sum_all with
    local_all under exclude                    -> 7 fails
  * _walk's `ni != oi` filter removed          -> 9 fails
  * selfrule.message() returning ""            -> 11 fails
  * the crossing-ring `_ring()` mask dropped   -> 12 fails
"""

import numpy as np
import pandas as pd
import pytest

from equipop import selfrule
from equipop.cells import CellData
from equipop.fastcounts import run_knn_counts
from equipop.analysis import run_knn, run_knn_stats

UNIT = 100.0


def _scatter(n=260, span=18, seed=5, dupes=True):
    """Cells on a coarse lattice. `dupes` leaves REPEATED COORDINATES
    in, which is the case that tells an index-matched mask apart from
    one that trusts position 0."""
    rng = np.random.default_rng(seed)
    E = rng.integers(0, span, n).astype(float) * UNIT
    N = rng.integers(0, span, n).astype(float) * UNIT
    if not dupes:                      # collapse to unique coordinates
        seen, keep = set(), []
        for i, (e, m) in enumerate(zip(E, N)):
            if (e, m) not in seen:
                seen.add((e, m))
                keep.append(i)
        E, N = E[keep], N[keep]
    pop = rng.integers(1, 30, len(E)).astype(float)
    grp = np.minimum(pop, rng.integers(0, 20, len(E)).astype(float))
    return E, N, pop, grp


def _cd(E, N, pop, grp, **kw):
    return CellData(E=E, N=N, n=pop, binary_sums={"g": grp},
                    unit_size=UNIT, **kw)


def _brute(E, N, pop, grp, k, drop):
    """Whole-ring k-NN written independently of both engines."""
    n = len(E)
    NK, TK, RK = np.zeros(n), np.zeros(n), np.zeros(n)
    for i in range(n):
        d = np.hypot(E - E[i], N - N[i])
        m = np.ones(n, bool)
        if drop:
            m[i] = False
        o = np.argsort(d[m], kind="stable")
        dd, pp, gg = d[m][o], pop[m][o], grp[m][o]
        c = np.cumsum(pp)
        pos = int(np.searchsorted(c, k))
        pos = min(pos, len(c) - 1)
        take = dd <= dd[pos] + 1e-9          # ring-atomic: all ties
        NK[i], TK[i] = pp[take].sum(), gg[take].sum()
        RK[i] = TK[i] / NK[i] if NK[i] > 0 else np.nan
    return NK, TK, RK


# --- 1, 2: the default is the published rule and did not move --------

def test_the_default_is_to_include_the_origin():
    assert selfrule.DEFAULT == selfrule.INCLUDE
    assert selfrule.resolve(None) == selfrule.INCLUDE


def test_saying_nothing_gives_exactly_what_include_gives():
    """John's ruling: the default must keep reproducing the published
    literature. A silent flip would invalidate every EquiPop result in
    print, Osth/Clark/Malmberg (2015) included."""
    E, N, pop, grp = _scatter()
    cd = _cd(E, N, pop, grp)
    quiet = run_knn_counts(cd, k_values=[20, 60], report=False)
    named = run_knn_counts(cd, k_values=[20, 60], report=False,
                           self_rule="include")
    for c in ("N_20", "T_g_20", "R_g_20", "Dist_20", "N_60", "R_g_60"):
        assert np.allclose(quiet[c], named[c], equal_nan=True), c


# --- 3: a wrong name costs nothing ----------------------------------

def test_an_unknown_rule_is_refused_before_anything_is_computed():
    with pytest.raises(ValueError, match="selfrule"):
        selfrule.resolve("sometimes")


@pytest.mark.parametrize("spelling,want", [
    ("i=j", selfrule.INCLUDE), ("i==j", selfrule.INCLUDE),
    ("INCLUDE", selfrule.INCLUDE), ("with_self", selfrule.INCLUDE),
    ("i!=j", selfrule.EXCLUDE), ("i ne j", selfrule.EXCLUDE),
    ("drop_self", selfrule.EXCLUDE), ("EXCLUDE", selfrule.EXCLUDE),
])
def test_the_spellings_people_actually_reach_for(spelling, want):
    """John wrote 'i=j or i ne j'; the Tartu slides write w_ii = 0; an
    early draft used drop_self. All three arrive at the same place."""
    assert selfrule.resolve(spelling) == want


# --- 4, 5, 6: the fast engine against an independent reference -------

@pytest.mark.parametrize("k", [10, 40, 150])
@pytest.mark.parametrize("rule,drop", [("include", False),
                                       ("exclude", True)])
def test_the_fast_engine_matches_a_brute_force_reference(k, rule, drop):
    E, N, pop, grp = _scatter()
    got = run_knn_counts(_cd(E, N, pop, grp), k_values=[k], report=False,
                         overshoot_mode="whole", self_rule=rule)
    bN, bT, bR = _brute(E, N, pop, grp, k, drop)
    assert np.allclose(got[f"N_{k}"], bN)
    assert np.allclose(got[f"T_g_{k}"], bT)
    assert np.allclose(got[f"R_g_{k}"], bR, equal_nan=True)


def test_the_mask_follows_the_origin_not_the_first_column():
    """WITH REPEATED COORDINATES, the origin is not reliably the first
    neighbour the tree returns. A mask built on position 0 removes
    somebody else's people and nothing looks wrong - N_k is still
    plausible, the share is still between 0 and 1. Only a reference
    that knows WHICH cell to drop can catch it."""
    E, N, pop, grp = _scatter(dupes=True)
    # the fixture must actually contain the case being tested
    assert len(set(zip(E.tolist(), N.tolist()))) < len(E)
    got = run_knn_counts(_cd(E, N, pop, grp), k_values=[15], report=False,
                         overshoot_mode="whole", self_rule="exclude")
    bN, bT, bR = _brute(E, N, pop, grp, 15, True)
    assert np.allclose(got["N_15"], bN)
    assert np.allclose(got["R_g_15"], bR, equal_nan=True)


# --- 7, 9: the other two engines say the same thing ------------------

@pytest.mark.parametrize("rule", ["include", "exclude"])
@pytest.mark.parametrize("osm", ["whole", "proportional"])
def test_the_slow_engine_agrees_with_the_fast_one(rule, osm):
    """The two engines disagreeing is this project's oldest class of
    defect. A new rule must not reopen it."""
    E, N, pop, grp = _scatter(dupes=False)
    cells = pd.DataFrame({"E_grid": E, "N_grid": N, "FullPop": pop,
                          "Treatment": grp, "id": np.arange(len(E))})
    slow = run_knn(cells, k_values=[20, 70], unit_size=UNIT,
                   max_radius_units=60, overshoot_mode=osm,
                   self_rule=rule).sort_values("Id")
    fast = run_knn_counts(_cd(E, N, pop, grp, ), k_values=[20, 70],
                          report=False, overshoot_mode=osm,
                          self_rule=rule)
    for k in (20, 70):
        assert np.allclose(slow[f"N_{k}"].values, fast[f"N_{k}"].values)
        assert np.allclose(slow[f"R_{k}"].values,
                           fast[f"R_g_{k}"].values, equal_nan=True)
        assert np.allclose(slow[f"Dist_{k}"].values,
                           fast[f"Dist_{k}"].values, equal_nan=True)


@pytest.mark.parametrize("rule", ["include", "exclude"])
def test_the_statistics_engine_agrees_too(rule):
    E, N, pop, grp = _scatter(dupes=False, n=200, span=14)
    rng = np.random.default_rng(1)
    vals = [rng.normal(50, 10, int(c)) for c in pop]
    cd = CellData(E=E, N=N, n=pop, binary_sums={"g": grp},
                  value_arrays={"inc": vals}, unit_size=UNIT)
    st = run_knn_stats(cd, k_values=[25], stats={"g": ["ratio"],
                       "inc": ["mean"]}, overshoot_mode="whole",
                       self_rule=rule)
    fc = run_knn_counts(cd, k_values=[25], report=False,
                        overshoot_mode="whole", self_rule=rule)
    assert np.allclose(st["N_25"].values, fc["N_25"].values)
    assert np.allclose(st["R_g_25"].values, fc["R_g_25"].values,
                       equal_nan=True)


# --- 8: what exclusion does, and does not, touch ---------------------

def test_the_cells_own_counts_are_not_touched_by_the_rule():
    """N_local and <var>_local describe THE CELL, not the
    neighbourhood. A rule about neighbourhoods must leave them
    alone."""
    E, N, pop, grp = _scatter()
    cd = _cd(E, N, pop, grp)
    a = run_knn_counts(cd, k_values=[30], report=False, self_rule="include")
    b = run_knn_counts(cd, k_values=[30], report=False, self_rule="exclude")
    assert np.allclose(a["N_local"], b["N_local"])
    assert np.allclose(a["g_local"], b["g_local"])
    assert np.allclose(a["N_local"], pop)


def test_an_origin_with_nobody_near_it_counts_nobody():
    """One cell far from the rest. Under i!=j it has no neighbours
    within reach, so the honest answer is zero people and an UNDEFINED
    share - not a share invented from its own residents."""
    E = np.array([0.0, 100.0, 200.0, 90000.0])
    N = np.array([0.0, 0.0, 0.0, 90000.0])
    pop = np.array([10.0, 10.0, 10.0, 500.0])
    grp = np.array([1.0, 2.0, 3.0, 400.0])
    cd = _cd(E, N, pop, grp)
    inc = run_knn_counts(cd, k_values=[50], report=False,
                         self_rule="include")
    exc = run_knn_counts(cd, k_values=[50], report=False,
                         self_rule="exclude")
    # the remote origin is the last row
    assert inc["R_g_50"].iloc[-1] == pytest.approx(0.8)   # its own 400/500
    assert exc["N_50"].iloc[-1] < 50                      # never reaches k
    assert exc["R_g_50"].iloc[-1] != pytest.approx(0.8)


def test_excluding_hits_a_concentrated_group_hardest():
    """The finding from CaliData2010, reproduced in miniature. A group
    clustered into a few cells has its own cell as a large part of its
    measured isolation; a group spread evenly does not. So the shift
    from excluding the origin is NOT uniform across groups, and that
    asymmetry is the substantive reason the option exists."""
    rng = np.random.default_rng(4)
    E, N, pop = [], [], []
    clustered, spread = [], []
    for ex in range(20):
        for ny in range(20):
            E.append(ex * UNIT)
            N.append(ny * UNIT)
            p = float(rng.integers(20, 40))
            pop.append(p)
            # clustered: everyone in a 3x3 corner. spread: everywhere.
            clustered.append(p * 0.9 if (ex < 3 and ny < 3) else 0.0)
            spread.append(p * 0.25)
    E = np.array(E); N = np.array(N); pop = np.array(pop)
    cd = CellData(E=E, N=N, n=pop,
                  binary_sums={"clustered": np.array(clustered),
                               "spread": np.array(spread)},
                  unit_size=UNIT)
    out = {}
    for rule in ("include", "exclude"):
        r = run_knn_counts(cd, k_values=[60], report=False, self_rule=rule)
        for v in ("clustered", "spread"):
            w = np.asarray(cd.binary_sums[v], dtype=float)
            sh = r[f"R_{v}_60"].values
            ok = np.isfinite(sh) & (w > 0)
            out[(rule, v)] = (w[ok] * sh[ok]).sum() / w[ok].sum()
    d_clustered = out[("include", "clustered")] - out[("exclude", "clustered")]
    d_spread = out[("include", "spread")] - out[("exclude", "spread")]
    assert d_clustered > 0, "excluding self should lower measured isolation"
    assert d_clustered > 3 * d_spread, (
        f"clustered moved {d_clustered:.4f}, spread {d_spread:.4f} - the "
        "asymmetry this option exists for did not appear")


# --- 11: the choice must never be invisible --------------------------

def test_a_run_says_which_rule_it_used(capsys):
    """The means barely move - on Gridby the share was identical to
    three decimals under both rules at every k - so a reader CANNOT
    TELL from the numbers. If the run does not say, the result is
    unreproducible the moment it is copied into a paper."""
    E, N, pop, grp = _scatter(n=80, span=8)
    cd = _cd(E, N, pop, grp)
    run_knn_counts(cd, k_values=[20], report=True, self_rule="exclude")
    said = capsys.readouterr().out
    assert "EXCLUDED" in said
    assert "i!=j" in said
    assert "NOT comparable" in said

    run_knn_counts(cd, k_values=[20], report=True, self_rule="include")
    said = capsys.readouterr().out
    assert "INCLUDED" in said


def test_self_potential_is_reported_as_having_no_effect(capsys):
    """Passing both is not an error, but silently ignoring one would
    be. BACKLOG 95's self-potential places the ORIGIN'S OWN people;
    under i!=j there are none to place."""
    E, N, pop, grp = _scatter(n=80, span=8)
    run_knn_counts(_cd(E, N, pop, grp), k_values=[20], report=True,
                   self_rule="exclude", self_potential=1.0)
    said = capsys.readouterr().out
    assert "self-potential has no effect" in said
    assert "not ignored silently" in said


# --- 12: the crossing ring is not a way back in ----------------------

def test_a_share_of_the_origin_is_still_the_origin():
    """Under `proportional` the ring that crosses k contributes a
    FRACTION of its cells. If the origin sits in that ring and the
    ring path forgets the rule, part of the origin walks back into a
    neighbourhood it was excluded from.

    TWO EARLIER VERSIONS OF THIS TEST COULD NOT FAIL, and both are
    worth recording because the reasons differ.

    (1) The origin was never IN the crossing ring. Rings are groups of
    EQUAL DISTANCE, the origin sits at distance 0, and with its mass
    removed the crossing happens further out. The origin can only be
    in the crossing ring when ANOTHER CELL SHARES ITS COORDINATES -
    then distance 0 holds real mass and the ring at 0 is where k is
    crossed.

    (2) Asserting on the SHARE could not catch an unmasked `rpop`.
    The ring fraction f scales the group total and the denominator
    ALIKE, so R is invariant to it, and `proportional` pins N_k to k
    by construction. Only the group TOTAL moves: with the origin's
    100 people wrongly inside the ring total, f falls from 30/50 to
    30/150 and T_g falls from 15 to 5 while N_30 stays exactly 30 and
    R_g stays exactly 0.5. A share and a count that both look right
    while the total is a third of what it should be.
    """
    E = np.array([0.0, 0.0, 100.0, 200.0])      # rows 0 and 1 co-located
    N = np.zeros(4)
    pop = np.array([100.0, 50.0, 50.0, 50.0])
    grp = np.array([100.0, 25.0, 0.0, 0.0])     # origin holds 100 of it
    cd = _cd(E, N, pop, grp)
    exc = run_knn_counts(cd, k_values=[30], report=False,
                         overshoot_mode="proportional", self_rule="exclude")
    assert exc["N_30"].iloc[0] == pytest.approx(30.0)
    assert exc["T_g_30"].iloc[0] == pytest.approx(15.0)
    assert exc["R_g_30"].iloc[0] == pytest.approx(0.5)
    inc = run_knn_counts(cd, k_values=[30], report=False,
                         overshoot_mode="proportional", self_rule="include")
    assert inc["R_g_30"].iloc[0] > 0.5          # its own 100 pull it up
