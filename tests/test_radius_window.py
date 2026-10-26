# -*- coding: utf-8 -*-
"""test_radius_window.py - a radius must not depend on the search
window either (v1.61.4, BACKLOG 430 and 431).

External review of 1.61.3, 23 October 2026: "When the last fetched
neighbour is exactly on a requested radius and its equal-distance ring
continues beyond the search window, the fast counts engine accepts the
truncated ring instead of widening the search." Six cells in a cross,
r = 100 m: N_r100 = 3 with a three-cell window, 5 exhaustively - while
the documentation says m_neighbors "affects speed only, never results".

Both engine paths had it, so the bit-for-bit comparison between them
could not see it: they agreed on the wrong answer. Measured before the
fix on a 100 m lattice: the automatic window never met it for radii of
300 m to 2 km; the tiled runs' fixed window of 4,096 cells did, at
4.5 km, for 24 of 8,100 cells near the edge, short by up to 0.17%.

test_window_sensitivity.py is the k-ring twin of this file. Its
"radius" test is about Dist_k - the reach of a k-neighbourhood - and
never looked at N_r, which is why this hid beside it.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import contextlib
import io
import warnings

import numpy as np
import pandas as pd
import pytest

import equipop.fastcounts as FC
from equipop.cells import CellData
from equipop.decay import Decay


def _cross():
    """The reviewer's six cells: an origin, four at 100 m, one far."""
    E = np.array([0, -100, 100, 0, 0, 1000.0])
    N = np.array([0, 0, 0, -100, 100, 1000.0])
    return CellData(E=E, N=N, n=np.ones(6), binary_sums={"t": np.ones(6)},
                    binary_valid={"t": np.ones(6)}, unit_size=100.0)


def _lattice(half=12, seed=3):
    """A full 100 m lattice with whole people, so sums are exact and
    every ring of equal distances is complete in the data."""
    rng = np.random.default_rng(seed)
    xs, ys = np.meshgrid(np.arange(-half, half + 1) * 100.0,
                         np.arange(-half, half + 1) * 100.0)
    n = xs.size
    pop = rng.integers(1, 9, n).astype(float)
    t = np.floor(pop * rng.random(n))
    return CellData(E=xs.ravel(), N=ys.ravel(), n=pop,
                    binary_sums={"t": t}, binary_valid={"t": pop.copy()},
                    unit_size=100.0)


def _run(cd, monkeypatch, batched, m, **kw):
    monkeypatch.setattr(FC, "BATCHED", batched)
    with contextlib.redirect_stdout(io.StringIO()):
        r = FC.run_knn_counts(cd, m_neighbors=m, seed=1, **kw)
    return r.sort_values(["EastWest", "NorthSouth"]).reset_index(drop=True)


@pytest.mark.parametrize("batched", [True, False])
@pytest.mark.parametrize("m", [2, 3, 4, 5])
@pytest.mark.parametrize("rule", ["include", "exclude"])
def test_a_window_that_ends_on_the_radius_is_widened(monkeypatch, batched,
                                                     m, rule):
    """The reviewer's reproduction, on both paths, every short window
    and both origin rules: the same counts as the whole map.

    BROKEN WITH: `covered <= rmax` back to `<`, in _solve and in
    _solve_batch."""
    cd = _cross()
    short = _run(cd, monkeypatch, batched, m, r_values=[100.0],
                 self_rule=rule)
    whole = _run(cd, monkeypatch, batched, 6, r_values=[100.0],
                 self_rule=rule)
    assert short["N_r100"].tolist() == whole["N_r100"].tolist()
    assert whole.loc[(whole.EastWest == 0) & (whole.NorthSouth == 0),
                     "N_r100"].item() == (5 if rule == "include" else 4)


# (radius, window) pairs where the window ends INSIDE the ring at
# exactly that radius on this lattice: 1 + 4 cells at 100 m, then
# 4 at 141 m and 4 at 200 m - so a window of 3 cuts the 100 m ring
# and a window of 10 cuts the 200 m ring.
CUTS = [(100.0, 3), (200.0, 10)]


def test_these_windows_really_end_on_the_radius():
    """The case this file pins must exist, or the matrix below proves
    nothing. Re-derive it if the lattice changes."""
    from scipy.spatial import cKDTree
    cd = _lattice()
    pts = np.column_stack([cd.E, cd.N])
    centre = int(np.argmin(np.hypot(cd.E, cd.N)))
    for r, m in CUTS:
        d, _ = cKDTree(pts).query(pts[centre], k=m)
        whole = np.hypot(cd.E - cd.E[centre], cd.N - cd.N[centre])
        assert d[-1] == r, (r, m, d)
        assert (whole <= r).sum() > m, "the ring is not cut"


@pytest.mark.parametrize("batched", [True, False])
@pytest.mark.parametrize("r, m", CUTS)
@pytest.mark.parametrize("with_k", [False, True])
@pytest.mark.parametrize("rule", ["include", "exclude"])
@pytest.mark.parametrize("decayed", [False, True])
def test_radius_results_do_not_depend_on_the_window(monkeypatch, batched,
                                                    r, m, with_k, rule,
                                                    decayed):
    """Radius alone and beside a k, both origin rules, plain and
    decayed, both paths: a window that ends on the radius gives the
    whole map's answer, column by column.

    BROKEN WITH: the same `<` restored, which leaves every interior
    cell of the lattice short."""
    cd = _lattice()
    kw = dict(r_values=[r], self_rule=rule,
              k_values=[2] if with_k else None,
              decay=(Decay(model="negexp", half_life_m=150.0)
                     if decayed else None))
    short = _run(cd, monkeypatch, batched, m, **kw)
    whole = _run(cd, monkeypatch, batched, len(cd.E), **kw)
    lab = int(r)
    cols = [c for c in whole.columns if c.endswith(f"_r{lab}")]
    assert f"N_r{lab}" in cols and f"R_t_r{lab}" in cols
    for c in cols:
        assert np.allclose(short[c].to_numpy(float),
                           whole[c].to_numpy(float),
                           rtol=1e-12, atol=0, equal_nan=True), c


def test_a_tiled_run_agrees_with_the_whole_map(tmp_path):
    """Tiled runs pass a FIXED window (4,096 cells by default), which is
    where the fault showed on a real-sized grid. A small window here
    puts the same edge on the 200 m ring.

    BROKEN WITH: the `<` restored in _solve_batch (the tiled default
    path)."""
    pytest.importorskip("pyarrow")
    from equipop.bigrun import load_tiled, run_knn_counts_tiled
    cd = _lattice()
    out = str(tmp_path / "tiles")
    with contextlib.redirect_stdout(io.StringIO()):
        run_knn_counts_tiled(cd, r_values=[200.0], out_dir=out,
                             tile_m=800.0, m_neighbors=10)
        tiled = load_tiled(out)
        whole = FC.run_knn_counts(cd, r_values=[200.0],
                                  m_neighbors=len(cd.E))
    key = ["EastWest", "NorthSouth"]
    tiled = tiled.sort_values(key).reset_index(drop=True)
    whole = whole.sort_values(key).reset_index(drop=True)
    assert np.array_equal(tiled["N_r200"].to_numpy(float),
                          whole["N_r200"].to_numpy(float))


# --------------------------------- BACKLOG 431: a share with no denominator
@pytest.mark.parametrize("batched", [True, False])
def test_no_usable_value_gives_nan_and_no_warning(monkeypatch, batched):
    """People present, none with a usable value for `t`: the radius
    share is NaN - and computing it raises no RuntimeWarning. The 1.61.3
    suite printed 37 of these, all from this line.

    BROKEN WITH: the per-origin share guarded on the total population
    again (cp) instead of its own denominator."""
    cd = _lattice(half=4)
    valid = cd.binary_valid["t"].copy()
    valid[np.abs(cd.E) + np.abs(cd.N) <= 300] = 0.0   # a hole
    sums = cd.binary_sums["t"].copy()
    sums[valid == 0] = 0.0
    hole = CellData(E=cd.E, N=cd.N, n=cd.n, binary_sums={"t": sums},
                    binary_valid={"t": valid}, unit_size=100.0)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        r = _run(hole, monkeypatch, batched, None, r_values=[100.0])
    centre = (r.EastWest == 0) & (r.NorthSouth == 0)
    assert r.loc[centre, "N_r100"].item() > 0
    assert np.isnan(r.loc[centre, "R_t_r100"].item())


# ------------------------------------------- the jenkspy fallback, tested
def test_maps_fall_back_to_quantiles_without_jenkspy(monkeypatch, capsys):
    """jenkspy has no Python 3.15 build yet. Without it, natural breaks
    become quantiles - and the map says so.

    BROKEN WITH: the ImportError no longer caught."""
    pytest.importorskip("matplotlib")
    import sys
    from equipop import viz
    monkeypatch.setitem(sys.modules, "jenkspy", None)  # import fails
    v = np.random.default_rng(1).lognormal(0, 1, 500)
    got = viz.class_bounds(v, "jenks", 5)
    assert np.array_equal(got, viz.class_bounds(v, "quantiles", 5))
    assert "falling back to quantiles" in capsys.readouterr().out
