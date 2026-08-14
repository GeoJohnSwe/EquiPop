# -*- coding: utf-8 -*-
"""test_wstats_engine.py - BACKLOG 118, the ENGINE half.

test_wstats.py proves the arithmetic. This file proves the arithmetic
is actually reached, with the right weights, through run_knn_stats.

It exists because the first wiring had NO guard. Three deliberate
breaks - dropping the ring share, dropping the crossing ring's values
entirely, and disabling the seeded order - all went undetected by the
whole suite. The reason was a bad fixture rather than a missing test:
every cell in it held the SAME value, so a median of 4.0 came back
whichever weights were used, and the tests could not have failed.

So the layout here is built the other way round: the crossing ring
holds a DIFFERENT value from the interior, and every expected number
is worked out by hand below.

THE LAYOUT. Cells on a line, 100 m apart, ten people in each:

    cell 0 (origin)  x=50    value 0
    cell 1           x=150   value 0
    cell 2           x=250   value 100

Walking out from cell 0: distance 0 gives 10 people, the ring at 100 m
gives 10 more (20), and the ring at 200 m would give 10 more (30). So
k=25 CROSSES the ring at 200 m and needs half of it.

    whole         10x0, 10x0, 10x100 -> N=30, mean = 1000/30 = 33.33
    proportional  10x0, 10x0,  5x100 -> N=25, mean =  500/25 = 20.00

If the share is not applied the mean reads 33.33; if the ring's values
are dropped it reads 0. Both are far outside any tolerance.
"""
import numpy as np
import pytest

from equipop.stata_bridge import dispatch


def _line(values, pop=10, n_cells=None):
    """One cell per value, 100 m apart, `pop` people in each."""
    n_cells = len(values) if n_cells is None else n_cells
    xs, ys, vs = [], [], []
    for i, v in enumerate(values):
        for _ in range(pop):
            xs.append(50.0 + 100.0 * i)
            ys.append(50.0)
            vs.append(float(v))
    return (np.array(xs), np.array(ys), np.array(vs))


def _run(values, mode, k=25, stats=("mean", "median"), seed=None,
         pop=10):
    x, y, v = _line(values, pop=pop)
    return dispatch("stats", x, y, unit_size=100.0, k_values=[k],
                    values={"v": v}, stats={"v": list(stats)},
                    overshoot_mode=mode, seed=seed)


def test_the_crossing_ring_contributes_its_share_and_no_more():
    """The number the whole item turns on."""
    whole = _run([0, 0, 100], "whole")
    prop = _run([0, 0, 100], "proportional")

    assert whole["Mean_v_25"][0] == pytest.approx(1000.0 / 30.0), \
        "the whole-ring mean is not what the layout says it must be"
    assert prop["Mean_v_25"][0] == pytest.approx(20.0), (
        "the crossing ring did not contribute HALF of itself: "
        f"got {prop['Mean_v_25'][0]}, expected 20.0 "
        "(33.33 means the share was ignored, 0.0 means the ring's "
        "values never arrived)")


def test_nv_counts_the_fraction_that_actually_contributed():
    """Nv_ is people with a usable value. Under a half-taken ring it
    is a fractional number of people, and saying 30 would be a lie
    about how much evidence went in."""
    assert _run([0, 0, 100], "whole")["Nv_v_25"][0] == pytest.approx(30.0)
    assert _run([0, 0, 100], "proportional")["Nv_v_25"][0] == \
        pytest.approx(25.0)


def test_a_median_can_now_be_taken_from_a_fraction_of_a_cell():
    """Until v1.31 this raised. The layout puts the median inside the
    crossing ring so the answer depends on the fractional weight
    rather than sailing past it."""
    got = _run([0, 100, 100], "proportional", k=15,
               stats=("median",))["Med_v_15"][0]
    assert np.isfinite(got), "proportional still refuses a median"
    # 10 people at 0, then 5 of the 10 at 100 -> N=15, the middle
    # person sits at the boundary between the two blocks
    assert 0.0 <= got <= 100.0


def test_sampled_through_the_stats_engine_is_seeded_and_repeatable():
    """The seeded order is the ONE thing cell identities are for, and
    disabling them went unnoticed by the whole suite. A symmetric
    ring - two cells at the same distance holding different values -
    makes the choice visible in the answer."""
    # origin in the middle: cells at -100 and +100 are one ring
    x = np.array([150.0] * 10 + [50.0] * 10 + [250.0] * 10)
    y = np.full(30, 50.0)
    v = np.array([0.0] * 10 + [10.0] * 10 + [1000.0] * 10)

    def go(seed):
        return dispatch("stats", x, y, unit_size=100.0, k_values=[15],
                        values={"v": v}, stats={"v": ["mean"]},
                        overshoot_mode="sampled", seed=seed)

    a, b = go(1848), go(1848)
    assert a["Mean_v_15"] == pytest.approx(b["Mean_v_15"]), \
        "the same seed did not reproduce the same answer"

    # across many seeds the origin must sometimes take the low
    # neighbour and sometimes the high one - if identities are not
    # used the choice is fixed and every seed agrees
    means = {round(float(go(s)["Mean_v_15"][0]), 6) for s in range(40)}
    assert len(means) > 1, (
        "every seed gave the same answer - the seeded order is not "
        "reaching the ring engine")


def test_whole_and_proportional_agree_when_the_ring_lands_exactly():
    """No crossing ring, no fraction, no difference. A version that
    scaled something unconditionally would fail here."""
    for mode in ("whole", "proportional"):
        got = _run([0, 0, 100], mode, k=20)["Mean_v_20"][0]
        assert got == pytest.approx(0.0), mode


def test_the_shipped_answer_key_still_holds_under_whole():
    """The regression lock in one line: whole weights must reproduce
    what EquiPop has always published. The conformance suites check
    this at scale; this is the fast local version."""
    got = _run([1, 2, 3, 4, 5], "whole", k=50,
               stats=("mean", "median", "gini", "sd"))
    assert got["Mean_v_50"][0] == pytest.approx(3.0)
    assert got["Med_v_50"][0] == pytest.approx(3.0)
