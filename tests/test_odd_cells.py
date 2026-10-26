# -*- coding: utf-8 -*-
"""Odd cell sizes across zero (v1.62.1, external review of 1.62.0).

Snapped midpoints were cast with .astype(int), which truncates toward
ZERO. With an odd cell size every midpoint ends in .5, so the cells
either side of 0 moved in opposite directions: at 1 m, points at -0.25
and +0.25 became ONE cell holding both; at 3 m the two centres were
recorded 2 m apart. Every square-grid path had it - build_cells,
snap_to_grid (the ring engine's input), the Stata bridge twice - and
theta_profile copied it. Even sizes were never affected, and still
give integer coordinates.

THE TEST THAT CANNOT BE FOOLED: a grid result must not change when the
whole map is moved by a whole number of cells. Data straddling 0 and
the same data moved far from it must give identical neighbourhoods.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import contextlib
import io

import numpy as np
import pandas as pd
import pytest

from equipop.cells import build_cells, exact_coords, grid_midpoints
from equipop.transform import aggregate_to_cells, snap_to_grid
import equipop.fastcounts as FC
from equipop import stata_bridge as SB
from equipop.analysis import run_knn

SIZES = [1, 3, 25, 100]


def _quiet(f, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return f(*a, **k)


def _four(u):
    """One point in each quadrant, a quarter cell from both axes."""
    q = u / 4
    return pd.DataFrame({"x": [-q, q, -q, q], "y": [-q, -q, q, q],
                         "n": 1.0})


@pytest.mark.parametrize("u", SIZES)
def test_four_quadrants_are_four_cells_one_cell_apart(u):
    """BROKEN WITH: build_cells' snap back on .astype(int)."""
    cd = _quiet(build_cells, _four(u), "x", "y", unit_size=float(u))
    assert len(cd.E) == 4 and list(cd.n) == [1, 1, 1, 1]
    assert sorted(set(np.asarray(cd.E, float))) == [-u / 2, u / 2]
    assert sorted(set(np.asarray(cd.N, float))) == [-u / 2, u / 2]


@pytest.mark.parametrize("u", SIZES)
def test_every_snapping_path_gives_the_same_exact_midpoints(u):
    """build_cells, snap_to_grid and the Stata bridge agree, exactly.

    BROKEN WITH: the Stata bridge's _snap back on .astype(np.int64)."""
    df = _four(u)
    want = [-u / 2, u / 2, -u / 2, u / 2]
    s = snap_to_grid(df, unit_size=float(u), easting_col="x",
                     northing_col="y")
    assert list(np.asarray(s.E_grid, float)) == want
    E, _N = SB._snap(df.x, df.y, float(u))
    assert list(np.asarray(E, float)) == want
    assert list(np.asarray(grid_midpoints(df.x, u), float)) == want


def test_even_sizes_keep_integer_coordinates():
    """Nothing about a 100 m or 1 km run changes: whole midpoints come
    back as int64, as they always did.

    BROKEN WITH: exact_coords always returning floats."""
    for u in (2, 100, 1000):
        g = grid_midpoints([-1234.5, 0.0, 98765.4], u)
        assert g.dtype == np.int64
    assert grid_midpoints([0.2], 3).dtype == np.float64
    assert exact_coords([]).dtype == np.int64


def _town(u, shift):
    rng = np.random.default_rng(11)
    n = 400
    x = rng.uniform(-6 * u, 6 * u, n) + shift
    y = rng.uniform(-6 * u, 6 * u, n) + shift
    return pd.DataFrame({"x": x, "y": y, "g": (rng.random(n) < .3) * 1.0,
                         "n": 1.0})


def _order(res):
    return res.sort_values(["EastWest", "NorthSouth"]).reset_index(
        drop=True)


@pytest.mark.parametrize("u", [1, 3, 25])
def test_the_fast_engine_does_not_see_where_zero_is(u):
    """The same town straddling 0 and moved 10,000 cells away: every
    count, share and distance identical.

    BROKEN WITH: build_cells' snap back on .astype(int) (cells either
    side of 0 merge, so the town at 0 has fewer cells)."""
    out = []
    for shift in (0.0, 10_000.0 * u):
        cd = _quiet(build_cells, _town(u, shift), "x", "y",
                    binary_vars=["g"], unit_size=float(u))
        r = _quiet(FC.run_knn_counts, cd, k_values=[5, 30], seed=1)
        out.append(_order(r))
    a, b = out
    assert len(a) == len(b)
    for c in ("N_5", "R_g_5", "Dist_5", "N_30", "R_g_30", "Dist_30"):
        assert np.allclose(a[c], b[c], rtol=1e-9, atol=1e-9), c


@pytest.mark.parametrize("u", [1, 3])
def test_the_stata_route_does_not_see_where_zero_is(u):
    """knn_to_rows - what `equipop` in Stata calls - row by row.

    BROKEN WITH: the bridge's cell snap back on .astype(np.int64)."""
    got = []
    for shift in (0.0, 10_000.0 * u):
        t = _town(u, shift)
        r = _quiet(SB.knn_to_rows, t.x.to_numpy(), t.y.to_numpy(), [5, 30],
                   treat={"g": t.g.to_numpy()}, unit_size=float(u))
        got.append(r)
    for c in ("N_5", "R_g_5", "N_30", "R_g_30"):
        assert np.allclose(got[0][c], got[1][c], rtol=1e-9), c


@pytest.mark.parametrize("u", [1, 3])
def test_the_ring_engine_does_not_see_where_zero_is(u):
    """run_knn, fed by snap_to_grid and aggregate_to_cells.

    BROKEN WITH: run_knn's lookup keyed on int() again."""
    got = []
    for shift in (0.0, 10_000.0 * u):
        t = _town(u, shift).rename(columns={"n": "FullPop", "g": "Treatment"})
        s = snap_to_grid(t, unit_size=float(u), easting_col="x",
                         northing_col="y")
        cells = aggregate_to_cells(s, ["FullPop", "Treatment"])
        r = _quiet(run_knn, cells, [5, 30], unit_size=float(u),
                   id_col=None, max_radius_units=60)
        got.append(_order(r))
    a, b = got
    assert len(a) == len(b)
    num = [c for c in a.columns if c not in ("Id", "EastWest", "NorthSouth")
           and pd.api.types.is_numeric_dtype(a[c])]
    for c in num:
        assert np.allclose(a[c].to_numpy(float), b[c].to_numpy(float),
                           rtol=1e-9, atol=1e-9, equal_nan=True), c
