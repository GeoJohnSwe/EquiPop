# -*- coding: utf-8 -*-
"""test_vectorjoin_free.py - the GEOPANDAS-FREE join, tested WITHOUT it.

paths_to_cells() and friction.feature_cells() were written so that the
lattice join needs no geopandas - it was nearly adopted as a
dependency before anyone checked whether the package already did the
job (BACKLOG 298). That property is worth nothing unless something
exercises it in an environment that does not have geopandas.

test_vectorjoin.py cannot: it calls pytest.importorskip("geopandas")
at module level, so EVERY test in it - including any added for the
free path - is skipped on exactly the machine where the freedom
matters. A test that only runs when the dependency is present cannot
show that the dependency is unnecessary.

THIS FILE IMPORTS NEITHER geopandas NOR shapely, and it must stay that
way.
"""
import pytest

from equipop.vectorjoin import VectorJoinError, paths_to_cells

def _line(y):
    return {"type": "line", "parts": [[(10.0, y), (90.0, y)]]}


def test_a_negative_value_is_a_facilitator_not_an_error():
    """JOHN'S EXERCISE 3, and the best argument in the course for why
    friction is a per-question choice rather than a property of the
    map: a motorway BLOCKS WALKING and CARRIES REGIONAL TRAFFIC. Same
    feature, opposite signs, depending on what is asked.

    The value field is the student's to prepare, so nothing stops them
    writing a negative - and nothing had ever tested one.
    """
    feats = [_line(10), _line(20), _line(40)]
    classes = ["motorway", "motorway", "residential"]

    walking = paths_to_cells(feats, [8.0, 8.0, 1.0], classes=classes,
                             unit_size=100.0, fidelity="class",
                             agg="sum")
    assert walking["value"].iloc[0] == pytest.approx(9.0)

    regional = paths_to_cells(feats, [-5.0, -5.0, 1.0], classes=classes,
                              unit_size=100.0, fidelity="class",
                              agg="sum")
    assert regional["value"].iloc[0] == pytest.approx(-4.0)


def test_a_cell_that_nets_to_zero_is_still_a_charged_cell():
    """+5 and -5 in one cell sum to 0. The row must SURVIVE: a cell
    whose charges cancel is not a cell nothing touched, even though
    both read 0.0 - and for friction they mean the same thing, which
    is why this is a note in the exercise rather than a defect."""
    out = paths_to_cells([_line(10), _line(40)], [5.0, -5.0],
                         classes=["motorway", "residential"],
                         unit_size=100.0, fidelity="class", agg="sum")
    assert len(out) == 1
    assert out["value"].iloc[0] == pytest.approx(0.0)


def test_this_file_does_not_reach_for_geopandas():
    """The guard on the guard. If somebody adds a geopandas import to
    this file - or moves these tests back into test_vectorjoin.py,
    which importorskips it at module level - the free path stops being
    checked on machines that do not have it, and nothing would say so.

    READ WITH ast, NOT BY STRING SEARCH. The first version scanned the
    source for "import geopandas" and failed on its own list of banned
    words, which is a small lesson about checking for a name by
    looking for its letters.
    """
    import ast
    import os

    tree = ast.parse(open(os.path.abspath(__file__),
                          encoding="utf-8").read())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    for banned in ("geopandas", "shapely", "pyogrio"):
        assert banned not in imported, (
            f"this file imports {banned}. It exists to prove the "
            "lattice join does not need it, and an import here means "
            "the free path is only tested where the dependency is "
            "already present")
