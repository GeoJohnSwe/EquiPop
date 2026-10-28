# -*- coding: utf-8 -*-
"""Every cell its own identity (v1.63.0, BACKLOG 444).

`sampled` admits the cells of the crossing ring in a random order keyed
on each cell's identity (overshoot.order_within_ring). Until 1.62.1 the
engines named a cell round(midpoint / cell size). Midpoints sit at
k + 0.5 cell widths and Python and numpy round halves to EVEN, so 1.5
and 2.5 both became 2: columns and rows came in pairs, and each 2 x 2
block of cells shared one identity.

What that did, measured on the town below (a 3 x 3 of ten people each,
k = 65, so the crossing ring is the mirror pair at sqrt(5) cells):

  - all forty seeds gave the SAME answer in every engine - the tie was
    broken by the order the engine listed the cells, a fixed direction,
    which is what John ruled out when he made the order random;
  - and the engines did not agree: the fast counts engine took one
    cell of the pair, the stats, friction and slope engines the other.

grid_identity now counts centres in HALF cell widths,
round(2 * centre / size): a square's midpoint is an odd number of them,
a hexagon's centre a whole number across and sqrt(3) * row up, so every
cell has its own name, square or hexagonal, at any size. (floor(), the
fix first proposed, mends squares but leaves 15% of hexagons sharing.)
Each test's docstring names what it was BROKEN WITH.
"""
from __future__ import annotations

import io
from contextlib import redirect_stdout

import numpy as np
import pandas as pd
import pytest

from equipop import overshoot
from equipop.overshoot import cell_identity, grid_identity
from equipop.stata_bridge import dispatch

SIZES = [100.0, 1000.0, 3.0, 1.0, 2.5, 0.25, 0.1]


def _midpoints(unit, lo=-20, hi=20):
    k = np.arange(lo, hi)
    return (k + 0.5) * unit


@pytest.mark.parametrize("unit", SIZES)
def test_every_cell_of_a_block_has_its_own_identity(unit):
    """A 40 x 40 block either side of zero: 1600 cells, 1600 names.

    BROKEN WITH: grid_identity back on round(centre / size) (each
    2 x 2 block shares one name: 400 names for 1600 cells)."""
    m = _midpoints(unit)
    e, n = np.meshgrid(m, m)
    ids = grid_identity(e.ravel(), n.ravel(), unit)
    assert len(np.unique(ids)) == e.size


@pytest.mark.parametrize("unit", SIZES)
def test_the_name_is_the_cell_not_the_arithmetic(unit):
    """The ring engines reach a cell by stepping from the origin
    (e0 + dx * step); the fast engine reads its midpoint from the cell
    table. Both must name it the same, however the floats fall.

    BROKEN WITH: int() in place of round() in grid_identity (cuts
    toward zero: 2 * centre / size lands a hair under the odd number
    as often as over it, and the stepped cells take the even one
    below)."""
    m = _midpoints(unit)
    e0 = m[0]
    stepped = np.array([e0 + i * unit for i in range(len(m))])
    assert (grid_identity(stepped, stepped, unit)
            == grid_identity(m, m, unit)).all()
    # and the columns either side of zero are two columns
    assert grid_identity(-unit / 2, 0.0, unit) != \
        grid_identity(unit / 2, 0.0, unit)


def test_every_hexagon_has_its_own_identity():
    """Hexagon centres (hex.py) sit half a width apart across and
    sqrt(3)/2 widths up; `sampled` names them with the same function.

    BROKEN WITH: floor(centre / size) in grid_identity - the fix first
    proposed for 444, which mends squares and leaves 15% of hexagons
    sharing a name."""
    import contextlib
    import io

    from equipop.hex import build_hex_cells
    rng = np.random.default_rng(1)
    for size in (100.0, 2.5):
        df = pd.DataFrame({"x": rng.uniform(-20, 20, 20000) * size,
                           "y": rng.uniform(-20, 20, 20000) * size,
                           "g": 1.0})
        with contextlib.redirect_stdout(io.StringIO()):
            cd = build_hex_cells(df, "x", "y", binary_vars=["g"],
                                 hex_size=size)
        ids = grid_identity(cd.E, cd.N, size)
        assert len(np.unique(ids)) == len(cd.E) > 1000, size


def test_mirror_images_are_told_apart():
    """(1, 2) and (2, 1) - the pair this file is about.

    BROKEN WITH: cell_identity made symmetric (e and n mixed the same
    way and XORed)."""
    assert cell_identity(1, 2) != cell_identity(2, 1)
    assert grid_identity(150.0, 250.0, 100) != \
        grid_identity(250.0, 150.0, 100)


# ---- the draw itself, through every engine that samples -------------

ENGINES = ["counts", "stats", "friction", "slope"]
X = [100.0 * i + 50 for i in range(3) for _ in range(3)]
Y = [100.0 * j + 50 for _ in range(3) for j in range(3)]
G = [float(i) for i in range(9)]       # which cell came in shows here


def _draw(engine, seed, tmp_path):
    kw = dict(unit_size=100.0, weight=[10.0] * 9, k_values=[65],
              overshoot_mode=overshoot.SAMPLED, seed=seed)
    if engine == "stats":
        kw.update(values={"v": G}, stats={"v": ["mean"]})
    else:
        kw.update(treat={"g": G}, treat_are_counts=True)
    if engine == "slope":
        p = tmp_path / "dem.csv"
        if not p.exists():
            pd.DataFrame({"x": X, "y": Y, "z": 0.0}).to_csv(p, index=False)
        kw["dem"] = str(p)
    if engine == "friction":
        p = tmp_path / "fr.csv"
        if not p.exists():
            pd.DataFrame({"x": X, "y": Y, "friction": 0.0}).to_csv(
                p, index=False)
        kw["friction_file"] = str(p)
    with redirect_stdout(io.StringIO()):
        out = dispatch(engine, X, Y, **kw)
    # The origin is the first cell. 60 people sit nearer than the pair
    # at sqrt(5); k = 65 admits one whole cell of it: g = 5 or g = 7.
    assert float(np.asarray(out["N_65"])[0]) == 70.0
    # The nearer six cells carry g = 0, 1, 2, 3, 4, 6: 16 between them.
    if engine == "stats":       # ten people a cell, each with v = g
        got = float(np.asarray(out["Mean_v_65"])[0]) * 70.0 / 10.0
    else:
        got = float(np.asarray(out["T_g_65"])[0])
    pick = round(got) - 16
    assert pick in (5, 7), got
    return pick


@pytest.mark.parametrize("engine", ENGINES)
def test_a_tie_across_a_diagonal_is_drawn_not_listed(engine, tmp_path):
    """Forty seeds must not all pick the same cell of the pair.

    BROKEN WITH: grid_identity back on round(centre / size) - every
    seed then took the cell the engine happened to list first."""
    picks = {_draw(engine, s, tmp_path) for s in range(1, 41)}
    assert picks == {5, 7}, (engine, picks)


def test_the_engines_draw_the_same_cell(tmp_path):
    """One seed, one draw - in all four engines.

    BROKEN WITH: grid_identity back on round(centre / size) (the
    counts engine took g = 7 where the other three took g = 5)."""
    for s in range(1, 11):
        picks = {e: _draw(e, s, tmp_path) for e in ENGINES}
        assert len(set(picks.values())) == 1, (s, picks)
