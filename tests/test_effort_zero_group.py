# -*- coding: utf-8 -*-
"""BACKLOG 488: a group that was ASKED FOR keeps its T_ and R_ columns
in the friction and slope engines, even where it holds nobody.

Found by the independent review of 1.64.0 (11 November 2026). The
effort engines decided from the VALUES whether a group had been asked
for (v1.26.1: no treatment, no T_/R_). A group asked for and empty -
a rare group, one year, one region - came back without its columns,
where the counts engine returns them as zeros. So a loop over groups
or years got a different set of columns each time, and with Stata's
-replace- (473) or a GIS overwrite, the previous run's T_ and R_ stayed
beside the new results, looking current.

All three doors reach the effort engines through dispatch(), so the
tests stand there, plus one through the QGIS door to show the columns
arrive in a layer.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

from equipop import stata_bridge as sb
from equipop.friction import run_knn_friction

X = np.array([0.0, 100.0, 200.0, 300.0])
Y = np.zeros(4)
FLAT = pd.DataFrame({"x": X, "y": Y, "alt": np.zeros(4)})


def _go(engine, treat, **kw):
    if engine == "slope":
        kw["dem"] = FLAT
    return sb.dispatch(engine, X, Y, treat=treat, **kw)


def _tr(cols):
    return sorted(c for c in cols if c.startswith(("T_", "R_")))


@pytest.mark.parametrize("engine", ["friction", "slope"])
def test_an_empty_group_keeps_its_columns_like_counts(engine):
    """BROKEN WITH: _count_from_grid deciding from the values alone -
    friction and slope return N_2, Dist_2, Rounds_2 and nothing for g."""
    treat = {"g": np.zeros(4)}
    counts = sb.dispatch("counts", X, Y, treat=treat, k_values=[2])
    effort = _go(engine, treat, k_values=[2])
    assert _tr(effort) == _tr(counts) == ["R_g_2", "T_g_2"]
    assert np.all(effort["T_g_2"] == 0) and np.all(effort["R_g_2"] == 0)


@pytest.mark.parametrize("engine", ["friction", "slope"])
def test_an_empty_group_keeps_its_effort_budget_columns(engine):
    out = _go(engine, {"g": np.zeros(4)}, k_values=[2], tau_values=[3.0])
    assert {"T_g_tau3", "R_g_tau3"} <= set(out)
    assert np.all(out["T_g_tau3"] == 0)


@pytest.mark.parametrize("engine", ["friction", "slope"])
def test_an_empty_group_beside_a_full_one(engine):
    out = _go(engine, {"g": np.zeros(4), "h": np.array([1.0, 0, 1, 0])},
              k_values=[2])
    assert _tr(out) == ["R_g_2", "R_h_2", "T_g_2", "T_h_2"]
    assert out["T_h_2"].sum() > 0          # the full one is counted


@pytest.mark.parametrize("engine", ["friction", "slope"])
def test_no_group_asked_still_gives_no_group_columns(engine):
    """v1.26.1 stays: an empty QUESTION answers no T_ or R_."""
    assert _tr(_go(engine, None, k_values=[2], tau_values=[3.0])) == []


def test_a_direct_call_that_does_not_say_reads_the_values_as_before():
    """run_knn_friction's own callers are told nothing new: without
    treatment= the values decide, as since v1.26.1. Saying it wins."""
    pop = pd.DataFrame({"x": X, "y": Y, "count_all": np.ones(4),
                        "count_group": np.zeros(4)})
    plain = run_knn_friction(pop, [2])
    assert _tr(plain) == []
    asked = run_knn_friction(pop, [2], treatment=True)
    assert _tr(asked) == ["R_2", "T_2"]
    told_none = run_knn_friction(pop.assign(count_group=1.0), [2],
                                 treatment=False)
    assert _tr(told_none) == []


def test_the_qgis_door_writes_the_empty_groups_columns():
    """Through a door: a barrier run with a count field of zeros."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for p in (os.path.join(root, "tests"), os.path.join(root, "qgis")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import qgis_stub
    qgis_stub.install()
    from equipop_qgis.alg_counts import CountsAndShares
    from test_qgis_door import _line_of_points, _river_source, _run
    pts = _line_of_points().assign(none_here=0.0)
    out, _ = _run(CountsAndShares, qgis_stub.source_from(pts),
                  refmode=[1], pop="pop", treatmode=[1],
                  treat=["none_here"], k="4", barrier=_river_source(),
                  barrierfield="cost")
    assert {"T_none_here_4", "R_none_here_4"} <= set(out.columns), \
        list(out.columns)
