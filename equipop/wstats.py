# -*- coding: utf-8 -*-
"""wstats.py - value statistics from (value, weight) pairs.

BACKLOG 118. Today EquiPop computes a median by EXPANSION: a cell
holding 40 people whose median household income is $62,000 becomes 40
copies of 62000, and an ordinary median is taken over the result.
That is simple, correct, and has two costs that have now both come
due:

  * WEIGHTS MUST BE WHOLE. You cannot repeat a value 0.4 times, so
    `proportional` - the default overshoot mode since 1.30 - is
    REFUSED wherever a median, percentile or Gini is asked for
    (machine 2 in both doors, and the reason it defaults to `whole`).
  * IT DOES NOT SCALE. WorldPop counts are fractional and a 1 km
    African run would try to materialise on the order of a billion
    rows. That is the hard blocker on BACKLOG 38, the continental
    machine, which is John's destination for this software.

This module computes the same numbers straight from the pairs.

THE CONSTRAINT THAT MAKES IT SAFE
---------------------------------
For WHOLE-NUMBER weights every function here returns EXACTLY what the
expansion returns - not nearly, exactly, to the last bit where the
arithmetic allows it. That is not an aspiration, it is what
test_wstats.py checks against `equipop.stats.value_stat` over
thousands of random cases.

So this is a refactor with a proof, not a change of meaning. Nothing
John has already published moves. Fractional weights are then the one
genuinely new behaviour, and they only arise where the old code
refused to answer at all.

WHAT A QUANTILE MEANS HERE - John's ruling, 1.31
------------------------------------------------
Interpolated, not stepped. His reason is the good one: it is what
EquiPop ALREADY does for an even number of observations, where the
median is the average of the two middle values. That average IS a
linear interpolation, so interpolating everywhere is the consistent
generalisation rather than a new convention.

It also keeps the promise `proportional` was introduced to make. That
mode exists to stop a neighbourhood jumping as a whole ring is
swallowed; a stepped median would put the jump straight back into the
statistic, one observed value to the next.

The cost, stated plainly because the help text has to state it: an
interpolated median can return a figure no household reports. For
income that is ordinary. For a coded or categorical variable it is
not, and the manual says so.
"""
from __future__ import annotations

import math

import numpy as np

from .stats import is_percentile

__all__ = ["weighted_stat", "weighted_stats",
           "weighted_quantile", "prepare"]


def prepare(values, weights):
    """Sort, drop what cannot contribute, return (v, w, cumulative).

    Rows are dropped when the VALUE is missing - John's ruling on
    missing-value codes, 1.31: a declared code becomes missing at the
    door, and a case with a missing value still counts as a person
    towards k, still receives results, and simply contributes nothing
    of its own. Zero and negative weights go too: a cell holding
    nobody has no opinion.
    """
    v = np.asarray(values, dtype=float).ravel()
    w = np.asarray(weights, dtype=float).ravel()
    if v.shape != w.shape:
        raise ValueError(
            f"[wstats] {v.size} values against {w.size} weights - "
            "these must be row-aligned pairs. Nothing was computed.")
    ok = np.isfinite(v) & np.isfinite(w) & (w > 0)
    v, w = v[ok], w[ok]
    if v.size == 0:
        return v, w, w
    order = np.argsort(v, kind="mergesort")   # stable: ties keep order
    v, w = v[order], w[order]
    return v, w, np.cumsum(w)


def weighted_quantile(values, weights, q: float) -> float:
    """The q-th quantile (q in [0, 1]) of a weighted sample.

    Reproduces numpy's default `method="linear"` on the expanded
    array whenever the weights are whole numbers.

    HOW, and why it is written this way. Think of the expansion laid
    out in sorted order and indexed 0 .. N-1. A value v_j with weight
    w_j occupies the indices [C_{j-1}, C_j - 1], where C is the
    running total. numpy asks for the position h = (N-1) * q and
    interpolates linearly between neighbouring indices. So the whole
    job is a piecewise-linear map from index to value: flat across
    each value's own block, sloping across the single index of gap
    between one block's last row and the next block's first.

    FRACTIONAL WEIGHTS need one guard. A weight below 1 makes a
    block's last index fall BEFORE its first, which would hand
    np.interp a non-monotone x and produce silent nonsense. The knots
    are therefore forced non-decreasing. Weights below 1 arise only
    for a nearly-empty cell or a very small ring share; the common
    case under `proportional` is a fraction of a populated cell,
    which is still well above 1.
    """
    v, w, cum = prepare(values, weights)
    return _quantile_prepared(v, w, cum, q)


def _quantile_prepared(v, w, cum, q: float) -> float:
    if v.size == 0:
        return float("nan")
    if v.size == 1:
        return float(v[0])
    n = float(cum[-1])
    if n <= 0:
        return float("nan")
    if n <= 1:
        # less than one person between them: no spread to speak of,
        # and (N-1) would go negative. Report the weighted mean, which
        # is what a single observation's quantile is anyway.
        return float(np.dot(v, w) / n)

    h = (n - 1.0) * float(q)
    lo = cum - w                     # first index of each block
    hi = cum - 1.0                   # last index of each block
    hi = np.maximum(hi, lo)          # see FRACTIONAL WEIGHTS above
    knots = np.empty(2 * v.size, dtype=float)
    knots[0::2], knots[1::2] = lo, hi
    np.maximum.accumulate(knots, out=knots)
    vals = np.repeat(v, 2)
    return float(np.interp(h, knots, vals))


def _weighted_gini(v, w, cum) -> float:
    """Gini over a weighted sample, matching the expanded formula.

    The expanded version (equipop.stats.gini_sorted) is
        G = 2 * sum(i * x_i) / (n * S)  -  (n + 1) / n
    over 1-based sorted x. Each value v_j owns the expanded ranks
    C_{j-1}+1 .. C_j, and those consecutive integers sum in closed
    form, so the whole thing collapses to one pass over the pairs.

    WHAT THIS IS A GINI *OF*, because it matters and the manual says
    so: inequality BETWEEN cell values, weighted by population.
    Inequality WITHIN a cell is invisible to it. Where the value is
    itself an area median - a block-group median income repeated to
    its blocks, say - this measures dispersion between those medians
    and will understate household inequality substantially. That is
    a property of the input, not of the estimator, and 1.31 warns
    when it detects it.
    """
    n = float(cum[-1])
    s = float(np.dot(v, w))
    if n <= 0 or s <= 0:
        return float("nan")
    lo = cum - w
    # sum of the ranks C_{j-1}+1 .. C_j  =  (C_j(C_j+1) - lo(lo+1)) / 2
    rank_sum = (cum * (cum + 1.0) - lo * (lo + 1.0)) / 2.0
    return float(2.0 * np.dot(v, rank_sum) / (n * s) - (n + 1.0) / n)


def weighted_stats(names, values, weights) -> dict:
    """Several statistics over ONE neighbourhood, sorting once.

    Sorting is the expensive part, and asking for a mean, a median
    and a Gini through weighted_stat() sorts the same pairs three
    times. The first wiring of BACKLOG 118 did exactly that and made
    the test suite 2.5x slower - unacceptable in a tool whose whole
    direction of travel is bigger runs, so the engine calls this
    instead.
    """
    v, w, cum = prepare(values, weights)
    return {s: _stat_prepared(s, v, w, cum) for s in names}


def weighted_stat(s: str, values, weights) -> float:
    """One value statistic by name, from (value, weight) pairs.

    Same names as equipop.stats.value_stat, same meanings, same
    answers for whole-number weights.
    """
    v, w, cum = prepare(values, weights)
    return _stat_prepared(s, v, w, cum)


def _stat_prepared(s: str, v, w, cum) -> float:
    """The body, over pairs already sorted and accumulated."""
    nv = v.size
    if is_percentile(s):
        return _quantile_prepared(v, w, cum, float(s[1:]) / 100.0)
    if nv == 0:
        # `sum` and `count` are the two statistics with a meaningful
        # answer for an empty set. Everything else is unknown, and
        # unknown must not be reported as zero.
        return 0.0 if s in ("sum", "count") else float("nan")

    n = float(cum[-1])
    if s == "count":
        return n
    if s == "sum":
        return float(np.dot(v, w))
    if s == "min":
        return float(v[0])
    if s == "max":
        return float(v[-1])
    if s == "range":
        return float(v[-1] - v[0])
    if s == "mean":
        return float(np.dot(v, w) / n)
    if s == "median":
        return _quantile_prepared(v, w, cum, 0.5)
    if s == "gini":
        return _weighted_gini(v, w, cum)
    if s in ("sd", "se", "var"):
        # ddof=1 on the EXPANDED sample: divide by N-1, not by
        # (number of distinct values) - 1. Getting this wrong would
        # pass every test with equal weights and fail everywhere else.
        if n <= 1:
            return float("nan")
        mean = float(np.dot(v, w) / n)
        var = float(np.dot(w, (v - mean) ** 2) / (n - 1.0))
        if s == "var":
            return var
        sd = math.sqrt(max(var, 0.0))
        return sd if s == "sd" else sd / math.sqrt(n)
    raise KeyError(s)
