# -*- coding: utf-8 -*-
"""The external review of 1.63.0 (26 October 2026): the cell-size and
permutation guards (BACKLOG 451). The segregation findings (448-450,
452) are in tests/test_segregation_weighting.py, beside the rest of the
profile's tests.

Each finding was reproduced before it was fixed (scratchpad
review1630/verify.py). Each test's docstring names what it was BROKEN
WITH, and each was.
"""
from __future__ import annotations

import contextlib
import io
import os
import re

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAD_SIZES = [-1.0, 0.0, float("nan"), float("inf"), "x"]


def _quiet(f, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return f(*a, **k)


@pytest.mark.parametrize("unit", BAD_SIZES)
def test_the_bridge_refuses_a_cell_size_that_is_not_one(unit):
    """Reproduced: unit_size=-1 through dispatch ran and returned
    N_1 = 1, Dist_1 = 0 for both rows - plausible, and meaningless -
    while 0, NaN and infinity escaped as a KeyError from inside.

    BROKEN WITH: the check at dispatch's front door removed AND
    grid_midpoints' own check removed (either one alone still stops
    it - that is the point of having both)."""
    from equipop.stata_bridge import dispatch
    with pytest.raises(ValueError, match="cell size must be"):
        _quiet(dispatch, "counts", np.array([10.0, 250.0]),
               np.array([10.0, 30.0]), unit_size=unit, k_values=[1])


@pytest.mark.parametrize("unit", BAD_SIZES)
def test_every_grid_builder_refuses_it_too(unit):
    """The package's own builders, for Python callers and future doors:
    the square grid, the effort grid and the hexagons.

    BROKEN WITH: grid_midpoints' check removed (build_cells and
    snap_to_grid then build on it); FrictionGrid's; build_hex_cells'."""
    from equipop.cells import build_cells, grid_midpoints
    from equipop.friction import FrictionGrid
    from equipop.hex import build_hex_cells
    df = pd.DataFrame({"x": [10.0, 250.0], "y": [10.0, 30.0], "g": 1.0})
    with pytest.raises(ValueError, match="cell size must be"):
        grid_midpoints([10.0], unit)
    with pytest.raises(ValueError, match="cell size must be"):
        _quiet(build_cells, df, "x", "y", binary_vars=["g"],
               unit_size=unit)
    pop = pd.DataFrame({"x": [50.0, 150.0], "y": [50.0, 50.0],
                        "count_all": 1.0, "count_group": 0.0})
    with pytest.raises(ValueError, match="cell size must be"):
        _quiet(FrictionGrid, pop, None, unit_size=unit)
    with pytest.raises(ValueError, match="cell size must be"):
        _quiet(build_hex_cells, df, "x", "y", binary_vars=["g"],
               hex_size=unit)


def test_a_good_size_still_passes_as_given():
    """BROKEN WITH: check_unit_size rounding (2.5 back to 2)."""
    from equipop.cells import check_unit_size
    assert check_unit_size(2.5) == 2.5
    assert check_unit_size("100") == 100.0


def _run_program():
    t = open(os.path.join(ROOT, "stata", "equipop_run.ado"),
             encoding="utf-8").read()
    start = t.index("program define equipop_run")
    return t[start:t.index("\nend", start)]


def _guard(body, pattern):
    m = re.search(pattern, body)
    assert m, pattern
    tail = body[m.end():m.end() + 400]
    assert "display as error" in tail and "exit 198" in tail, pattern
    # and it is checked BEFORE Python is called
    assert m.start() < body.index("python: _equipop_run("), pattern


def test_equipop_run_refuses_a_missing_zero_or_negative_unit():
    """Reproduced: equipop_run checked only selfpot() before Python, and
    its Python accepted any whole number - 0 and -1 included.

    BROKEN WITH: the guard removed, or missing() dropped from it (Stata's
    . compares greater than every number, so `unit' <= 0 lets it by)."""
    _guard(_run_program(),
           r"if\s+missing\(`unit'\)\s*\|\s*`unit'\s*<=\s*0\s*\{")


def test_equipop_run_refuses_a_permutation_count_that_is_not_one():
    """Reproduced: WPERM(real 199) reached Python as int(wperm), so 99.5
    became 99 without a word and -5 reached the engine.

    BROKEN WITH: the whole-number test dropped from the wperm() guard
    (a fractional count is truncated again)."""
    body = _run_program()
    _guard(body, r"if\s+missing\(`wperm'\)\s*\|\s*`wperm'\s*<\s*1\s*\|"
                 r"\s*`wperm'\s*!=\s*int\(`wperm'\)\s*\{")
