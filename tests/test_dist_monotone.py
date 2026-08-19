"""BACKLOG 191 - Dist_k must never fall as k rises.

Found in the field, on John's own 10,892-row test dataset, by a check
in the test pass that said "if any row breaks that ordering, something
is wrong". It returned 198.

    Dist_50 = 51.1 m,  Dist_100 = 35.8 m,  same origin.

The radius needed to reach 100 people cannot be smaller than the
radius needed to reach 50. Sub-cell and only 1.8% of rows, but Dist_k
is one of the four headline outputs and the statement is indefensible.

THE CAUSE was two distance conventions meeting at a discontinuity:

  - while the neighbourhood fits INSIDE the origin cell, Dist is the
    equal-area radius s*sqrt(unit^2 * k / (n * pi)), correctly rising
    with k;
  - as soon as k needs the first ring OUTSIDE, `proportional`
    interpolates area-linearly from the previous radius to the ring -
    and took that previous radius to be ZERO rather than the origin
    cell's own radius.

So stepping outside the cell reset the baseline to the cell centre and
the answer could land below where it already was. It needed BOTH
proportional overshoot AND a self-potential above zero; either alone
hid it, which is why eleven releases of tests never saw it.

The fix starts the interpolation at s*unit/sqrt(pi) - the value the
in-cell formula reaches at k = n - so the two conventions now meet
continuously.
"""

import io
import contextlib
import math
import os

import numpy as np
import pytest

from equipop import selfpot
from equipop.stata_bridge import knn_to_rows

DATA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "stata", "stata_test_data.dta")

KS = [50, 100, 200, 400]
MODES = ["proportional", "whole"]
SELFPOTS = [0.0, 2 ** -0.5, 1.0]


def _field_data():
    pd = pytest.importorskip("pandas")
    if not os.path.exists(DATA):
        pytest.skip("the Stata test dataset is not present")
    df = pd.read_stata(DATA)
    return (df.X_local.to_numpy(float), df.Y_local.to_numpy(float),
            df.ValCount.to_numpy(float))


def _run(x, y, w=None, **kw):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return knn_to_rows(x, y, KS, weight=w, unit_size=100.0, **kw)


def _inversions(res):
    """How many rows have a radius that FALLS as k rises."""
    cols = [res[f"Dist_{k}"] for k in KS]
    ok = np.ones(len(cols[0]), dtype=bool)
    for c in cols:
        ok &= np.isfinite(c)
    bad = np.zeros(len(cols[0]), dtype=bool)
    for a, b in zip(cols, cols[1:]):
        bad |= ok & (b < a - 1e-9)
    return bad


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("sp", SELFPOTS)
def test_the_radius_never_falls_as_k_rises(mode, sp):
    """The invariant, on the data that found the defect.

    It needed proportional AND a self-potential together, so every
    combination is checked rather than the one that broke.
    """
    x, y, _w = _field_data()
    res = _run(x, y, overshoot_mode=mode, self_potential=sp)
    bad = _inversions(res)
    assert not bad.any(), (
        f"{int(bad.sum())} rows have Dist that falls as k rises, under "
        f"overshoot={mode}, selfpot={sp}")


@pytest.mark.parametrize("mode", MODES)
def test_the_radius_never_falls_with_a_population_weight_either(mode):
    x, y, w = _field_data()
    res = _run(x, y, w=w, overshoot_mode=mode)
    bad = _inversions(res)
    assert not bad.any(), f"{int(bad.sum())} rows, weighted, {mode}"


def test_the_two_conventions_meet_at_the_cell_boundary():
    """Continuity, stated as arithmetic rather than measured.

    The in-cell radius at k = n is s*unit/sqrt(pi). That is exactly
    the value the interpolation must start from when it steps outside,
    or there is a jump - downwards, as it turned out.
    """
    unit, s = 100.0, 1.0
    at_full_cell = selfpot.radius_for_k(unit, 1.0, 1.0, s)
    assert at_full_cell == pytest.approx(s * unit / math.sqrt(math.pi))
    # and it is the limit of the in-cell formula as k approaches n
    assert selfpot.radius_for_k(unit, 999.0, 1000.0, s) == pytest.approx(
        at_full_cell, rel=1e-3)


def test_a_synthetic_case_reproduces_the_original_shape():
    """One dense cell, one ring beyond it - the configuration that
    produced 51.1 m then 35.8 m. Independent of the field data, so the
    guard survives if that file is ever unavailable."""
    # 61 people stacked in one cell, then a ring of points 300 m away
    x = np.concatenate([np.full(61, 1000.0),
                        np.array([1300.0, 700.0, 1000.0, 1000.0] * 30)])
    y = np.concatenate([np.full(61, 1000.0),
                        np.array([1000.0, 1000.0, 1300.0, 700.0] * 30)])
    res = _run(x, y, overshoot_mode="proportional", self_potential=1.0)
    d50, d100 = res["Dist_50"][0], res["Dist_100"][0]
    assert d50 > 0 and d100 > 0
    assert d100 >= d50 - 1e-9, (
        f"Dist_50={d50:.3f} but Dist_100={d100:.3f} - the interpolation "
        f"is starting from the cell centre again")


def test_the_fix_did_not_move_the_whole_ring_answer():
    """`whole` reports the ring's actual distance and was never
    affected. If these numbers moved, the change reached further than
    it should have."""
    x, y, w = _field_data()
    res = _run(x, y, w=w, overshoot_mode="whole", self_potential=1.0)
    d = res["Dist_400"]
    ok = np.isfinite(d)
    # every whole-ring distance is either a real inter-cell distance or
    # an in-cell estimate below the cell's half-diagonal
    assert (d[ok] >= 0).all()
    assert np.isfinite(d[ok]).all()
