# -*- coding: utf-8 -*-
"""test_wstats.py - BACKLOG 118, the arithmetic half.

The claim this file has to establish before anything is allowed to
use equipop/wstats.py:

    FOR WHOLE-NUMBER WEIGHTS IT RETURNS WHAT THE EXPANSION RETURNS.

If that holds, replacing the expansion is a refactor with a proof and
nothing John has published moves. If it does not hold, every median
EquiPop has ever reported is up for renegotiation. So the test is a
brute-force comparison against the shipped `value_stat` over
thousands of random neighbourhoods, not a handful of examples.

The second half checks the behaviour that is genuinely NEW -
fractional weights - where there is nothing to compare against and
the properties have to be stated directly.
"""
import math

import numpy as np
import pytest

from equipop.stats import value_stat
from equipop.wstats import prepare, weighted_quantile, weighted_stat

STATS = ["mean", "median", "sd", "se", "var", "gini", "min", "max",
         "count", "sum", "range", "p10", "p25", "p50", "p75", "p90",
         "p97.5"]


def _expand(v, w):
    return np.repeat(np.asarray(v, float), np.asarray(w, int))


# ============================================ the constraint
@pytest.mark.parametrize("stat", STATS)
def test_whole_weights_reproduce_the_expansion(stat):
    """Thousands of random neighbourhoods, every statistic.

    Tolerance is 1e-12 RELATIVE, which is floating-point noise rather
    than slack: the two routes sum the same numbers in a different
    order, and nothing here is allowed to differ by more than that.
    """
    rng = np.random.default_rng(1180 + len(stat))
    worst = 0.0
    for _ in range(1200):
        m = int(rng.integers(1, 12))
        v = np.round(rng.uniform(1, 200_000, m), 2)
        w = rng.integers(1, 60, m).astype(float)
        if np.allclose(v, v[0]):
            # every value identical: the true spread is exactly zero
            # and the EXPANSION returns floating-point noise instead.
            # Pinned separately in the test below - excluded here so
            # the tolerance stays honest for every other case.
            continue
        a = value_stat(stat, _expand(v, w))
        b = weighted_stat(stat, v, w)
        if np.isnan(a) and np.isnan(b):
            continue
        worst = max(worst, abs(a - b) / max(abs(a), 1.0))
    assert worst < 1e-12, (
        f"{stat}: worst relative difference {worst:.3e} - the weighted "
        "route no longer agrees with the expansion it replaces")


def test_where_they_differ_the_expansion_is_the_wrong_one():
    """The one family of cases that exceeds the tolerance above, kept
    here because it is a FINDING rather than a defect.

    55 copies of a single value have a standard deviation of exactly
    zero. The expansion returns about 1.2e-10 - noise from summing 55
    large identical floats and subtracting their mean. The weighted
    route returns 0. It is more accurate than the code it replaces,
    and that is worth pinning so nobody 'fixes' it back.
    """
    v, w = np.array([199800.95]), np.array([55.0])
    assert weighted_stat("sd", v, w) == 0.0
    assert weighted_stat("var", v, w) == 0.0
    assert value_stat("sd", _expand(v, w)) > 0.0     # the noise


def test_ddof_is_on_people_not_on_distinct_values():
    """sd/se/var divide by N-1 where N is the POPULATION, not by the
    number of distinct values minus one. Equal weights hide the
    difference completely, which is why this case is deliberately
    unequal."""
    v = np.array([10.0, 20.0, 30.0])
    w = np.array([1.0, 1.0, 98.0])
    assert weighted_stat("var", v, w) == pytest.approx(
        value_stat("var", _expand(v, w)))
    # and the naive reading - ddof over 3 distinct values - is far off
    naive = float(np.var(v, ddof=1))
    assert abs(weighted_stat("var", v, w) - naive) > 1.0


# ============================================ the new behaviour
def test_a_quantile_never_goes_backwards():
    rng = np.random.default_rng(4)
    for _ in range(200):
        m = int(rng.integers(2, 10))
        v = rng.uniform(0, 1000, m)
        w = rng.uniform(0.05, 40, m)          # fractional throughout
        qs = np.linspace(0, 1, 41)
        got = [weighted_quantile(v, w, q) for q in qs]
        assert all(b >= a - 1e-9 for a, b in zip(got, got[1:])), \
            "the weighted quantile is not monotone in q"
        assert min(got) >= v.min() - 1e-9
        assert max(got) <= v.max() + 1e-9


def test_the_median_moves_smoothly_as_a_ring_is_swallowed():
    """John's ruling, made checkable.

    This is the whole reason for choosing interpolation over a step.
    `proportional` exists to stop a neighbourhood jumping as the ring
    that crosses k is taken; the statistic has to inherit that, or
    the jump is merely moved from the count into the median.

    A far-away ring is admitted with a share rising from 0 to 1. The
    median must travel without a single jump. Under a STEP median it
    would move in one leap from one observed value to another - the
    largest step below is about 0.1 on a scale spanning 100.
    """
    inner_v = np.arange(10, 60, 10.0)          # 10..50
    inner_w = np.full(5, 20.0)
    ring_v = np.array([110.0, 120.0])

    def _step_median(v, w):
        """The alternative John rejected: the first value whose
        cumulative weight reaches half. Here only to be compared
        against - it is what the code must NOT do."""
        o = np.argsort(v)
        v, w = np.asarray(v)[o], np.asarray(w)[o]
        c = np.cumsum(w)
        return float(v[np.searchsorted(c, c[-1] / 2.0)])

    interp, step = [], []
    for f in np.linspace(0.0, 1.0, 2001):
        v = np.concatenate([inner_v, ring_v])
        w = np.concatenate([inner_w, np.full(2, 20.0 * f)])
        interp.append(weighted_stat("median", v, w))
        step.append(_step_median(v, w))

    biggest_interp = max(abs(b - a) for a, b in zip(interp, interp[1:]))
    biggest_step = max(abs(b - a) for a, b in zip(step, step[1:]))
    assert biggest_step >= 9.9, (
        "the comparison is broken: a step median should leap a whole "
        "value gap and did not")
    assert biggest_interp < biggest_step / 5.0, (
        f"the median moved in jumps of {biggest_interp:.3f} against "
        f"the step median's {biggest_step:.3f} - that is not an "
        "interpolation")


def test_a_fraction_of_every_cell_is_not_the_same_as_fewer_cells():
    """Scaling ALL weights by the same factor changes nothing (it is
    the same distribution), while scaling only the crossing ring
    does. A version that quietly normalised everything would pass the
    first and fail the second."""
    v = np.array([1.0, 2.0, 3.0, 100.0])
    w = np.array([10.0, 10.0, 10.0, 10.0])
    for s in ("median", "mean", "gini", "p25"):
        assert weighted_stat(s, v, w) == pytest.approx(
            weighted_stat(s, v, w * 0.37)), f"{s} is not scale-free"
    part = np.array([10.0, 10.0, 10.0, 2.0])
    assert weighted_stat("mean", v, part) < weighted_stat("mean", v, w)


def test_fractional_weights_agree_where_they_happen_to_be_whole():
    """A share that lands on a whole number of people must give the
    same answer as asking for that many people directly - the two
    routes must not have drifted apart."""
    rng = np.random.default_rng(9)
    for _ in range(300):
        m = int(rng.integers(2, 8))
        v = np.round(rng.uniform(1, 5000, m), 3)
        w = rng.integers(2, 30, m).astype(float)
        f = 0.5
        scaled = w * f
        if not np.allclose(scaled, np.round(scaled)):
            continue
        for s in ("median", "mean", "gini", "sd", "p90"):
            a = value_stat(s, _expand(v, scaled))
            b = weighted_stat(s, v, scaled)
            if np.isnan(a) and np.isnan(b):
                continue
            assert a == pytest.approx(b, rel=1e-12, abs=1e-9), s


# ============================================ the edges
def test_missing_values_drop_out_and_zero_weights_do_too():
    """John's ruling on missing-value codes: a declared code becomes
    missing at the door, and a case with a missing value contributes
    NOTHING of its own while still being a person and still receiving
    results. Here that is just: it must not reach the arithmetic."""
    v = np.array([10.0, np.nan, 30.0, 40.0])
    w = np.array([5.0, 500.0, 5.0, 0.0])
    vv, ww, _ = prepare(v, w)
    assert list(vv) == [10.0, 30.0]
    assert weighted_stat("mean", v, w) == pytest.approx(20.0)
    assert weighted_stat("count", v, w) == 10.0


def test_nothing_to_measure_is_not_an_answer_of_zero():
    for s in ("mean", "median", "sd", "gini", "p50", "min"):
        assert math.isnan(weighted_stat(s, [], []))
        assert math.isnan(weighted_stat(s, [np.nan], [4.0]))
    assert weighted_stat("sum", [], []) == 0.0
    assert weighted_stat("count", [], []) == 0.0


def test_one_person_has_no_spread_and_still_has_a_median():
    assert weighted_stat("median", [42.0], [1.0]) == 42.0
    assert weighted_stat("median", [42.0], [0.3]) == 42.0
    assert math.isnan(weighted_stat("sd", [42.0], [1.0]))


def test_mismatched_pairs_are_refused_by_name():
    with pytest.raises(ValueError, match="row-aligned pairs"):
        weighted_stat("mean", [1.0, 2.0], [1.0])
