# -*- coding: utf-8 -*-
"""test_batched_engine.py - the fast engine solving whole chunks of
origins at once (v1.61.1), and saying how far it has got.

John, 19 October, after Turkey at 700 m with k = 5,000 and 9,000 sat
silent in the neighbourhood search: "a progress line would make wonder
- also in the other machines" and "rewriting to handle several origins
at the same time would be great as long as we do not alter the
results". So the test of the rewrite is the OLD engine: the same
table, bit for bit, over every setting the batched path takes - and
the same log.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import contextlib
import io
import itertools
import time

import numpy as np
import pandas as pd
import pytest

import equipop.fastcounts as FC
from equipop.cells import CellData, build_cells


def _cells(seed, n=3000, frac=False, labels=False):
    rng = np.random.default_rng(seed)
    x = rng.integers(0, 60, n) * 100.0 + 50
    y = rng.integers(0, 40, n) * 100.0 + 50
    x[:40] = rng.integers(200, 260, 40) * 100.0 + 50    # a thin outpost
    w = rng.random(n) * 3 if frac else rng.integers(0, 4, n).astype(float)
    df = pd.DataFrame({"x": x, "y": y, "w": w,
                       "g1": rng.integers(0, 2, n).astype(float),
                       "g2": rng.random(n),
                       "lab": [f"c{int(a)}_{int(b)}" for a, b in zip(x, y)]})
    df.loc[rng.random(n) < 0.05, "g2"] = np.nan
    with contextlib.redirect_stdout(io.StringIO()):
        return build_cells(df, "x", "y", binary_vars=["g1", "g2"],
                           unit_size=100.0, weights="w",
                           label_col="lab" if labels else None)


def _both(cd, monkeypatch, **kw):
    out = {}
    for batched in (False, True):
        monkeypatch.setattr(FC, "BATCHED", batched)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = FC.run_knn_counts(cd, seed=1, **kw)
        said = [ln for ln in buf.getvalue().splitlines()
                if "to go in this pass" not in ln]
        out[batched] = (res, said)
    return out


# --------------------------------------------- the same table, exactly
CASES = list(itertools.product(
    [1, 2], ["proportional", "whole"], ["include", "exclude"],
    [False, True], [[5], [7, 40, 200]], [None, 9]))


@pytest.mark.parametrize("seed, mode, rule, frac, ks, m", CASES)
def test_batched_gives_the_per_origin_table_bit_for_bit(
        monkeypatch, seed, mode, rule, frac, ks, m):
    """Whole and proportional overshoot, the origin included or not,
    whole and fractional people, one k and three, the density's own
    window and a window of nine cells (which forces the ladder and
    cuts rings at the window's edge): every column, every row, exactly
    - and the same log.

    BROKEN WITH: the ring start found without the running maximum (the
    wrong 'before'); the ring cut at the window's edge not handed
    back; and the self-potential radius not applied (Dist_k left at
    0). (i!=j inside the crossing ring needs cells sharing the
    origin's place, which build_cells never makes - the break-check
    found this test blind to it; the next-but-one test covers it.)"""
    cd = _cells(seed, frac=frac)
    got = _both(cd, monkeypatch, k_values=ks, m_neighbors=m,
                overshoot_mode=mode, self_rule=rule)
    pd.testing.assert_frame_equal(got[False][0], got[True][0],
                                  check_exact=True)
    assert got[False][1] == got[True][1]


def test_labels_and_long_rings(monkeypatch):
    """Cell labels carry through; and a crossing ring longer than the
    reproduced order covers is summed by numpy itself - the same table.
    (The limit is lowered to 3 so that a great many rings are 'long'.)

    BROKEN WITH: long rows left out of the row sums (left at 0)."""
    monkeypatch.setattr(FC, "_BATCH_RING_MAX", 3)
    cd = _cells(4, labels=True)
    got = _both(cd, monkeypatch, k_values=[6, 60], m_neighbors=None)
    pd.testing.assert_frame_equal(got[False][0], got[True][0],
                                  check_exact=True)
    assert got[True][0]["CellId"].iloc[0].startswith("c")


def test_ring_sums_are_added_in_numpys_own_order():
    """The batched ring sums must be np.sum's, not merely close to it -
    1,000 pixels of 0.1 summed left to right make 99.9999999999986,
    and np.sum makes 100.00000000000001.

    BROKEN WITH: the eight running sums combined in another order; and
    with the short rows added right to left."""
    rng = np.random.default_rng(3)
    lengths = list(range(1, 129)) * 4
    P = np.zeros((len(lengths), 130))
    for i, n in enumerate(lengths):
        a = (np.full(n, 0.1) if i % 4 == 0
             else rng.random(n) * 10.0 ** rng.integers(-3, 4))
        P[i, :n] = a
    got = FC.rowsum_like_numpy(P, np.array(lengths))
    want = np.array([P[i, :n].sum() for i, n in enumerate(lengths)])
    assert np.array_equal(got, want)
    long = rng.random((3, 400))
    assert np.array_equal(FC.rowsum_like_numpy(long, np.array([129, 300,
                                                                400])),
                          [long[0, :129].sum(), long[1, :300].sum(),
                           long[2].sum()])


# ------------------------------------------------------------- speed
def _lattice(n_side, seed=0):
    rng = np.random.default_rng(seed)
    xx, yy = np.meshgrid(np.arange(n_side), np.arange(n_side))
    n = xx.size
    pop = rng.lognormal(3, 1, n)
    g = pop * rng.random(n)
    return CellData(E=(xx.ravel() * 100 + 50).astype(np.int64),
                    N=(yy.ravel() * 100 + 50).astype(np.int64),
                    n=pop, binary_sums={"g": g},
                    binary_valid={"g": pop.copy()}, unit_size=100.0)


def test_batched_is_much_faster(monkeypatch):
    """25,600 origins, two k: the batched pass in a fraction of the
    per-origin time (about a fifth, measured).

    BROKEN WITH: BATCHED = False as the default."""
    cd = _lattice(160)
    took = {}
    for batched in (True, False):
        if not batched:
            monkeypatch.setattr(FC, "BATCHED", False)
        t = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            FC.run_knn_counts(cd, [500, 3000], seed=1)
        took[batched] = time.time() - t
    assert took[True] < 0.6 * took[False], took


# ---------------------------------------------------------- progress
def test_a_long_pass_says_how_far_it_has_got():
    """John: "a progress line would make wonder". One line per tenth of
    the origins, with the time so far and an estimate of the rest -
    and none for a run too short to wait for.

    BROKEN WITH: the progress line removed."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        FC.run_knn_counts(_lattice(160), [500], seed=1, chunk=2048)
    lines = [ln for ln in buf.getvalue().splitlines()
             if "origins (" in ln and "to go in this pass" in ln]
    assert 5 <= len(lines) <= 10, lines
    assert "25,600 origins" in lines[0]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        FC.run_knn_counts(_lattice(40), [500], seed=1)
    assert "to go in this pass" not in buf.getvalue()


@pytest.mark.parametrize("rule", ["exclude", "include"])
def test_cells_sharing_the_origins_place(monkeypatch, rule):
    """Two cells on the same coordinates - what a merged pair of
    datasets or a hand-built CellData can hold. Under i!=j the origin
    sits in the crossing ring at distance 0 with its twin, and must be
    left out of that ring's share too; build_cells never makes such
    twins, so the main test cannot reach this.

    BROKEN WITH: i!=j ignored inside the crossing ring."""
    rng = np.random.default_rng(9)
    base = _lattice(30, seed=9)
    twins = rng.choice(len(base), 200, replace=False)
    cd = CellData(E=np.r_[base.E, base.E[twins]],
                  N=np.r_[base.N, base.N[twins]],
                  n=np.r_[base.n, base.n[twins] * 3],
                  binary_sums={"g": np.r_[base.binary_sums["g"],
                                          base.binary_sums["g"][twins]]},
                  binary_valid={"g": np.r_[base.binary_valid["g"],
                                           base.binary_valid["g"][twins]]},
                  unit_size=100.0)
    got = _both(cd, monkeypatch, k_values=[30, 90, 400],
                overshoot_mode="proportional", self_rule=rule)
    pd.testing.assert_frame_equal(got[False][0], got[True][0],
                                  check_exact=True)


# ------------------- v1.61.2: decay, radii, `sampled` - every setting
from equipop.decay import Decay                          # noqa: E402

MORE = list(itertools.product(
    [1, 2], ["proportional", "whole", "sampled"], ["include", "exclude"],
    [False, True], [None, 9]))


@pytest.mark.parametrize("seed, mode, rule, decayed, m", MORE)
def test_decay_radii_and_sampled_bit_for_bit(monkeypatch, seed, mode,
                                             rule, decayed, m):
    """John: "Please add the speed up for the other run types as well".
    k and radii together, with and without a distance decay, under all
    three overshoot rules: the per-origin table, exactly.

    BROKEN WITH: the sampled order drawn without the origin in its key;
    the decay weight left out of the crossing ring; a radius share
    taken over everybody instead of over those with a usable value;
    and the radius position counted with '<' instead of '<=' (500 m is
    a lattice distance, so a cell sits exactly on it)."""
    cd = _cells(seed, frac=True)
    got = _both(cd, monkeypatch, k_values=[7, 40], r_values=[200.0, 500.0],
                m_neighbors=m, overshoot_mode=mode, self_rule=rule,
                decay=(Decay(model="negexp", half_life_m=300.0)
                       if decayed else None))
    pd.testing.assert_frame_equal(got[False][0], got[True][0],
                                  check_exact=True)
    assert got[False][1] == got[True][1]


def test_radii_alone_bit_for_bit(monkeypatch):
    """No k at all - only radii - also takes the batched path, and an
    origin whose window does not reach the largest radius is widened.

    BROKEN WITH: the window's reach not checked against the largest
    radius."""
    cd = _cells(5, frac=True)
    got = _both(cd, monkeypatch, r_values=[150.0, 400.0], m_neighbors=9)
    pd.testing.assert_frame_equal(got[False][0], got[True][0],
                                  check_exact=True)


@pytest.mark.parametrize("mode", ["sampled", "proportional"])
def test_decay_and_sampled_are_faster_too(monkeypatch, mode):
    """BROKEN WITH: decay sent back to the per-origin path."""
    cd = _lattice(120)
    dec = Decay(model="negexp", half_life_m=400.0)
    took = {}
    for batched in (True, False):
        if not batched:
            monkeypatch.setattr(FC, "BATCHED", False)
        t = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            FC.run_knn_counts(cd, [500, 3000], r_values=[800.0], decay=dec,
                              overshoot_mode=mode, seed=1)
        took[batched] = time.time() - t
    assert took[True] < 0.6 * took[False], took
