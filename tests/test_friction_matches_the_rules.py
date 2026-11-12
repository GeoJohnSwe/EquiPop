# -*- coding: utf-8 -*-
"""BACKLOG 479-481: the effort engines apply the rules the radial
engines already had.

Found in the code review of 1.63.7 (10 November 2026). Three fixes
made to the radial engines over the years never reached
friction._count_from_grid, which the friction and the slope engine
share - the crossing-ring arithmetic exists in five copies, and this
is the copy the fixes missed:

  191 (v1.40.4)  Dist_k fell as k rose: stepping out of the origin
                 cell, the interpolation started from the cell's
                 CENTRE instead of from its own radius.
  304 (v1.47.7)  Dist_k = 0: a share of a cell arrives as 6.999...9
                 and `>= k` is then false.
  168 (v1.32)    A missing group value stayed in the share's
                 denominator.

And one of its own: two rows in one cell (479).

No barriers are used here. Without them the effort engine's first two
rings - the origin cell, then its neighbours - are the radial
engine's, when the neighbours are laid out so that both engines put
them in one ring (the four cells sharing an edge). So the radial
engine is the answer key, not a number worked out for this test.
"""
import contextlib
import io

import numpy as np
import pandas as pd
import pytest

from equipop import overshoot
from equipop.friction import run_knn_friction
from equipop.stata_bridge import dispatch, knn_to_rows

UNIT = 100.0


def _quiet(fn, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **kw)


def _plus(centre=50, arm=10):
    """A plus: one cell of `centre` people and the four cells sharing
    an edge with it, `arm` people each. One row per person."""
    cells = [(50.0, 50.0, centre), (150.0, 50.0, arm), (-50.0, 50.0, arm),
             (50.0, 150.0, arm), (50.0, -50.0, arm)]
    x = np.concatenate([np.full(n, cx) for cx, cy, n in cells])
    y = np.concatenate([np.full(n, cy) for cx, cy, n in cells])
    return x, y


def _both(k_values, **kw):
    x, y = _plus()
    f = _quiet(dispatch, "friction", x, y, k_values=k_values,
               unit_size=UNIT, **kw)
    r = _quiet(knn_to_rows, x, y, k_values, unit_size=UNIT, **kw)
    return f, r


# ------------------------------------------------------------- 191
@pytest.mark.parametrize("mode", ["proportional", "whole"])
@pytest.mark.parametrize("sp", [1.0, 2 ** -0.5, 0.0])
def test_the_distance_never_falls_as_k_rises(mode, sp):
    """BROKEN WITH: overshoot.radius(dist_m, ...) in the crossing
    branch, without _interp_base - at the centre cell Dist_50 is the
    cell's own radius and Dist_55 comes out far below it."""
    ks = [10, 25, 40, 50, 51, 55, 60, 70, 85, 90]
    f, _ = _both(ks, overshoot_mode=mode, self_potential=sp)
    d = np.column_stack([f[f"Dist_{k}"] for k in ks])
    assert np.isfinite(d).all()
    falls = np.diff(d, axis=1) < -1e-9
    assert not falls.any(), (
        f"Dist falls as k rises ({mode}, self-potential {sp:g}): "
        f"{d[falls.any(axis=1)][0]}")


@pytest.mark.parametrize("mode", ["proportional", "whole"])
@pytest.mark.parametrize("sp", [1.0, 2 ** -0.5, 0.0])
def test_the_effort_engine_is_the_radial_engine_without_barriers(mode, sp):
    """N and Dist for every person in the plus, at k inside the own
    cell, at the step out of it, and inside the first ring.
    BROKEN WITH: either of the two distance faults (191, 304)."""
    ks = [7, 25, 50, 55, 60]
    f, r = _both(ks, overshoot_mode=mode, self_potential=sp)
    x, _ = _plus()
    centre = np.arange(50)             # the 50 people of the centre
    for k in ks:
        assert np.allclose(f[f"N_{k}"][centre], r[f"N_{k}"][centre]), k
        assert np.allclose(f[f"Dist_{k}"][centre],
                           r[f"Dist_{k}"][centre]), (
            k, f[f"Dist_{k}"][0], r[f"Dist_{k}"][0])


# ------------------------------------------------------------- 304
def test_a_share_of_a_dense_cell_is_not_zero_metres_away():
    """157 people in one cell, k = 7, proportional. The 7 arrive as a
    share of the cell - and FIRST: that share must still be the float
    that is not quite 7, or this test tests nothing.

    BROKEN WITH: `n_k >= k` without the tolerance - Dist_7 is 0.0."""
    wt, taken = overshoot.ring_weights(
        overshoot.PROPORTIONAL, 7, 0.0, np.array([157.0]),
        np.array([1], dtype=np.uint64), seed=1, origin_id=1)
    assert taken < 7.0, "the fixture no longer produces the rounding"
    assert taken == pytest.approx(7.0)

    x = np.concatenate([np.full(157, 50.0), np.full(20, 950.0)])
    y = np.concatenate([np.full(157, 50.0), np.full(20, 50.0)])
    f = _quiet(dispatch, "friction", x, y, k_values=[7], unit_size=UNIT,
               overshoot_mode="proportional")
    r = _quiet(knn_to_rows, x, y, [7], unit_size=UNIT,
               overshoot_mode="proportional")
    dense = slice(0, 157)
    assert (f["Dist_7"][dense] > 0).all(), f["Dist_7"][0]
    assert np.allclose(f["Dist_7"][dense], r["Dist_7"][dense])
    # the closed form: the radius within which 7 of the 157 stand
    assert f["Dist_7"][0] == pytest.approx(
        np.sqrt(UNIT ** 2 * 7 / (157 * np.pi)))


# ------------------------------------------------------------- 168
def test_a_missing_group_value_leaves_the_denominator():
    """John's ruling on 168: of 10 people, 2 with an unknown group
    value and 4 in the group, the share is 4 / 8, never 4 / 10.
    BROKEN WITH: R = T / N in the effort engine (0.400)."""
    x = np.full(10, 50.0)
    y = np.full(10, 50.0)
    grp = np.array([1, 1, 1, 1, 0, 0, 0, 0, -9, -9], float)
    f = _quiet(dispatch, "friction", x, y, k_values=[10], unit_size=UNIT,
               treat={"g": grp}, missing_codes=[-9], overshoot_mode="whole")
    r = _quiet(dispatch, "counts", x, y, k_values=[10], unit_size=UNIT,
               treat={"g": grp}, missing_codes=[-9], overshoot_mode="whole")
    assert np.allclose(r["R_g_10"], 0.5)
    assert np.allclose(f["N_10"], 10.0)         # still 10 neighbours
    assert np.allclose(f["T_g_10"], 4.0)
    assert np.allclose(f["R_g_10"], 0.5), f["R_g_10"][0]
    # with nothing missing the share is what it always was
    clean = _quiet(dispatch, "friction", x, y, k_values=[10],
                   unit_size=UNIT, overshoot_mode="whole",
                   treat={"g": np.where(grp < 0, 0.0, grp)})
    assert np.allclose(clean["R_g_10"], 0.4)


def test_the_denominator_follows_the_share_of_a_crossing_cell():
    """Proportional: the cell that crosses k gives a share of its
    usable people, as it gives a share of its group."""
    x = np.concatenate([np.full(4, 50.0), np.full(10, 150.0)])
    y = np.full(14, 50.0)
    grp = np.r_[[1, 1, 0, 0], [1, 1, 1, 1, 0, 0, 0, 0, -9, -9]].astype(float)
    f = _quiet(dispatch, "friction", x, y, k_values=[9], unit_size=UNIT,
               treat={"g": grp}, missing_codes=[-9],
               overshoot_mode="proportional")
    # origin in the first cell: its own 4 (2 in the group), then 5 of
    # the next cell's 10: half of its 4 in the group, half of its 8
    # usable people
    assert f["N_9"][0] == pytest.approx(9.0)
    assert f["T_g_9"][0] == pytest.approx(2 + 0.5 * 4)
    assert f["R_g_9"][0] == pytest.approx((2 + 2) / (4 + 0.5 * 8))


# ------------------------------------------------------------- 479
def _people(flags, far=950.0):
    """One row per person: len(flags) people in one cell, one more
    far away. The form this module's own tests have always fed the
    engine."""
    n = len(flags)
    return pd.DataFrame({"x": [50.0] * n + [far], "y": [50.0] * (n + 1),
                         "count_all": 1.0,
                         "count_group": list(map(float, flags)) + [0.0]})


@pytest.mark.parametrize("flags", [[1, 0, 0], [0, 0, 1], [1, 1, 0],
                                   [0, 1, 0]])
def test_each_row_keeps_its_own_group_value(flags):
    """Three people in one cell. Measured on 1.63.7: flags 1, 0, 0
    gave NO T_ column, and 0, 0, 1 gave T = 3 - every row was read
    with the LAST row's flag.

    BROKEN WITH: cg = grid.count_group[grid.pop_idx] (the node's
    value) in _count_from_grid."""
    out = _quiet(run_knn_friction, _people(flags), [3], unit_size=UNIT,
                 overshoot_mode="whole")
    assert "T_3" in out, "the group was lost altogether"
    assert list(out["N_3"][:3]) == [3.0] * 3
    assert list(out["T_3"][:3]) == [float(sum(flags))] * 3
    assert np.allclose(out["R_3"][:3], sum(flags) / 3.0)


def test_rows_of_different_size_in_one_cell_add_up():
    """Nine people: a cell given as two rows (2 and 3) and a cell of
    4. Measured on 1.63.7: both rows of the first cell were read as 3,
    so N_5 was 6 and the whole map added up to 10.
    BROKEN WITH: ca = grid.count_all[grid.pop_idx]."""
    pop = pd.DataFrame({"x": [50.0, 50.0, 150.0], "y": [50.0, 50.0, 50.0],
                        "count_all": [2.0, 3.0, 4.0],
                        "count_group": [1.0, 0.0, 2.0]})
    out = _quiet(run_knn_friction, pop, [5, 9], unit_size=UNIT,
                 overshoot_mode="whole")
    assert list(out["N_5"]) == [5.0, 5.0, 9.0]
    assert list(out["SumN"]) == [9.0, 9.0, 9.0]
    assert list(out["T_5"]) == [1.0, 1.0, 3.0]
    # and it is the answer one row per cell gives
    one = pop.groupby(["x", "y"], as_index=False).sum()
    ref = _quiet(run_knn_friction, one, [5, 9], unit_size=UNIT,
                 overshoot_mode="whole")
    assert list(ref["N_5"]) == [5.0, 9.0] and list(ref["T_5"]) == [1.0, 3.0]


def test_the_origin_rule_leaves_out_the_whole_cell():
    """exclude is "not counting you or anyone sharing your cell". With
    one row per person it dropped only the origin's own row.
    BROKEN WITH: `ci != oi` in the drop_self branch - N_2 for a person
    in the cell of three is their two cell-mates, at no distance."""
    pop = _people([0, 0, 0], far=150.0)
    more = pd.DataFrame({"x": [250.0, 250.0], "y": [50.0, 50.0],
                         "count_all": 1.0, "count_group": 0.0})
    pop = pd.concat([pop, more], ignore_index=True)
    out = _quiet(run_knn_friction, pop, [2], unit_size=UNIT,
                 overshoot_mode="whole", self_rule="exclude")
    # from the cell of three: nobody of its own, so the 1 at 100 m and
    # then the 2 at 200 m - a whole ring, so N_2 is 3
    assert list(out["N_2"][:3]) == [3.0] * 3
    assert np.allclose(out["Dist_2"][:3], 200.0)
    one = pop.groupby(["x", "y"], as_index=False).sum()
    ref = _quiet(run_knn_friction, one, [2], unit_size=UNIT,
                 overshoot_mode="whole", self_rule="exclude")
    assert ref["N_2"][0] == 3.0 and ref["Dist_2"][0] == 200.0
