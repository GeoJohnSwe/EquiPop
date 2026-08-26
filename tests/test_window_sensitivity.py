"""BACKLOG 207 - the answer must not depend on the search window.

THE DEFECT. `ring_bounds()` walks forward with `while hi + 1 < n`,
where n is the size of the FETCHED WINDOW rather than the size of the
ring. A crossing ring that ran off the edge of the window was treated
as complete: its share was measured against whichever part happened to
fit, and the radius and every group share came out wrong.

WHY NOTHING NOTICED. Under proportional overshoot the walk takes
exactly enough of the ring to reach k, so N_k is exactly k however much
of the ring is present. The count guard cannot see it. The v1.16.4
ladder cannot see it either - that only re-solves origins which FAIL TO
REACH k, and these reached it.

WHY IT NEEDED A LATTICE. The first attempt at a synthetic reproduction
used random points and XPASSED. Random coordinates never tie, so every
"ring" holds one cell and cannot be cut. WorldPop is a lattice; rings
there are large. That is the whole reason this hid.
"""
from __future__ import annotations

import io
import contextlib

import numpy as np
import pandas as pd
import pytest

from equipop.cells import build_cells
from equipop.fastcounts import run_knn_counts


def _lattice(half=8, pop=None):
    """One cell per lattice point, so distance ties are exact."""
    xs, ys = np.meshgrid(np.arange(-half, half + 1) * 100.0,
                         np.arange(-half, half + 1) * 100.0)
    n = xs.size
    return pd.DataFrame({"x": xs.ravel(), "y": ys.ravel(),
                         "pop": np.ones(n) if pop is None else pop})


def _run(cd, ks, m):
    with contextlib.redirect_stdout(io.StringIO()):
        r = run_knn_counts(cd, ks, m_neighbors=m)
    return r.sort_values(["EastWest", "NorthSouth"]).reset_index(drop=True)


@pytest.fixture(scope="module")
def flat():
    return build_cells(_lattice(), "x", "y", unit_size=100.0,
                       weights="pop")


def test_the_ring_this_pins_really_is_cut_by_these_windows(flat):
    """If the case stops being a cut ring, the tests below prove nothing.

    k=11 on a one-person lattice crosses in the FOUR cells at 200 m,
    which sit at indices 9-12. A window of 11 or 12 slices it; 13
    completes it.
    """
    c = int(np.argmin((flat.E - 50) ** 2 + (flat.N - 50) ** 2))
    d = np.sort(np.hypot(flat.E - flat.E[c], flat.N - flat.N[c]))
    u, cnt = np.unique(np.round(d, 6), return_counts=True)
    assert cnt[3] == 4 and abs(u[3] - 200.0) < 1e-6, (
        "the 200 m ring is no longer four cells - re-derive the case")
    assert cnt[:3].sum() == 9 < 11 < cnt[:4].sum() == 13


@pytest.mark.parametrize("m", [11, 12, 13, 14, 17, 64, 256])
def test_the_radius_does_not_depend_on_the_window(flat, m):
    ref = _run(flat, [11], 256)
    got = _run(flat, [11], m)
    d = np.abs(got["Dist_11"].to_numpy(float)
               - ref["Dist_11"].to_numpy(float))
    assert np.nanmax(d) < 1e-9, (
        f"window {m} moved the radius by {np.nanmax(d):.4f} m. Before "
        "the fix a window of 11 gave 200.0 m where the converged "
        "answer is 173.2 m.")


def test_the_count_was_never_the_symptom(flat):
    """N_k is exactly k at every window, before the fix and after.

    Kept because it is the reason the defect survived: a guard on the
    count could not have caught this, and a future guard should not be
    expected to.
    """
    for m in (11, 12, 13, 64):
        got = _run(flat, [11], m)
        n = got["N_11"].to_numpy(float)
        assert np.allclose(n[np.isfinite(n)], 11.0)


def test_a_group_share_does_not_depend_on_the_window_either():
    """The truncated ring fed grp_k as well as the distance.

    Measured on Burundi + Rwanda before the fix: a cross-border share
    read 0.043 where the converged answer was 0.065 - a third of the
    value - while N_k stayed exact.
    """
    df = _lattice()
    # a group that varies sharply across the lattice, so the
    # composition of a crossing ring genuinely differs
    df["grp"] = (df["x"] > 0).astype(float)
    cd = build_cells(df, "x", "y", unit_size=100.0,
                     binary_vars=["grp"], weights="pop")
    ref = _run(cd, [11], 256)
    for m in (11, 12, 13, 17, 64):
        got = _run(cd, [11], m)
        d = np.abs(got["R_grp_11"].to_numpy(float)
                   - ref["R_grp_11"].to_numpy(float))
        assert np.nanmax(d) < 1e-9, (
            f"window {m} moved a group share by {np.nanmax(d):.5f}")


def test_fractional_weights_are_window_independent_too():
    """WorldPop weights are fractional; the ring share is a float sum."""
    rng = np.random.default_rng(3)
    df = _lattice()
    df["pop"] = rng.uniform(0.2, 3.0, len(df))
    cd = build_cells(df, "x", "y", unit_size=100.0, weights="pop")
    ref = _run(cd, [20], 256)
    for m in (11, 13, 24, 64):
        got = _run(cd, [20], m)
        d = np.abs(got["Dist_20"].to_numpy(float)
                   - ref["Dist_20"].to_numpy(float))
        assert np.nanmax(d) < 1e-9, f"window {m} moved Dist_20"
