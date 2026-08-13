"""#12 neighbourhood definition menu: r / tau / decayed-sum / area."""
import numpy as np
import pandas as pd

from equipop.cells import CellData, build_cells
from equipop.fastcounts import run_knn_counts
from equipop.analysis import run_knn_stats
from equipop.friction import run_knn_friction
from equipop.decay import Decay
from equipop.area import area_stats
from equipop.stata_bridge import knn_to_rows
from equipop.segregation import seg_profile

U = 100.0


def _cells(n=120, seed=11):
    rng = np.random.default_rng(seed)
    E = rng.integers(0, 30, n) * U + U / 2
    N = rng.integers(0, 30, n) * U + U / 2
    pop = rng.integers(1, 9, n)
    key = pd.DataFrame({"E": E, "N": N, "n": pop.astype(float),
                        "t": rng.binomial(pop, 0.3).astype(float)})
    key = key.groupby(["E", "N"], as_index=False).sum()
    return CellData(E=key.E.to_numpy(), N=key.N.to_numpy(),
                    n=key.n.to_numpy(), binary_sums={"t": key.t.to_numpy()},
                    value_arrays={}, unit_size=U)


def test_radius_fast_vs_brute():
    cd = _cells()
    rs = [250.0, 900.0, 1e6]              # small, medium, whole-world
    out = run_knn_counts(cd, k_values=None, r_values=rs)
    pts = np.c_[cd.E, cd.N]
    for i in range(len(cd)):
        d = np.hypot(pts[:, 0] - cd.E[i], pts[:, 1] - cd.N[i])
        for r in rs:
            m = d <= r
            lab = f"{r:g}"
            assert np.isclose(out.loc[i, f"N_r{lab}"], cd.n[m].sum())
            assert np.isclose(out.loc[i, f"T_t_r{lab}"],
                              cd.binary_sums["t"][m].sum())
    # whole-world radius must equal the global totals
    assert np.allclose(out["N_r1e+06"], cd.n.sum())


def test_radius_stats_engine_matches_fast():
    rng = np.random.default_rng(5)
    n = 400
    df = pd.DataFrame({"x": rng.integers(0, 25, n) * U + U / 2,
                       "y": rng.integers(0, 25, n) * U + U / 2,
                       "g": rng.integers(0, 2, n).astype(float),
                       "v": rng.normal(100, 20, n)})
    cd = build_cells(df, "x", "y", binary_vars=["g"], value_vars=["v"],
                     unit_size=U)
    st = run_knn_stats(cd, k_values=[50], r_values=[400.0],
                       stats={"g": ["ratio"], "v": ["mean"]})
    fa = run_knn_counts(cd, k_values=[50], r_values=[400.0])
    merged = st.merge(fa, on=["EastWest", "NorthSouth"],
                      suffixes=("_s", "_f"))
    assert np.allclose(merged["N_r400_s"], merged["N_r400_f"])
    assert np.allclose(merged["R_g_r400_s"], merged["T_g_r400"]
                       / merged["N_r400_f"])
    # brute-force the mean within radius for one origin
    e0, n0 = cd.E[0], cd.N[0]
    d = np.hypot(df.x - e0, df.y - n0)
    # distances are cell-based: recompute from snapped coords
    dcell = np.hypot(cd.E - e0, cd.N - n0)
    take = dcell <= 400.0
    vals = np.concatenate([cd.value_arrays["v"][i]
                           for i in np.flatnonzero(take)])
    assert np.isclose(st.loc[0, "Mean_v_r400"], vals.mean())


def test_tau_flat_grid_is_octile_disc():
    """Flat friction: a tau budget reaches the OCTILE disc.

    BACKLOG 139. This test used to be called
    test_tau_flat_grid_is_chebyshev and asserted 9 and 25 - the square
    3x3 and 5x5 balls - because every move cost 1 whatever its length.
    That was the defect, pinned here as if it were the specification.

    A diagonal step covers sqrt(2) cell widths and now costs sqrt(2),
    so a budget of 1 round buys the four rooks and NOT the corners.
    The reachable set is the disc, not the square.

    The honest limit: an 8-neighbour graph cannot travel in a straight
    line, only in 45 and 90 degree steps, so its shortest path is
    OCTILE - max + (sqrt(2)-1)*min - which overstates true Euclidean
    distance by up to 8.2%, at 22.5 degrees off an axis, and by zero
    along an axis or a perfect diagonal.
    """
    nx = 11
    E, N = np.meshgrid(np.arange(nx) * U + U / 2,
                       np.arange(nx) * U + U / 2, indexing="ij")
    pop = pd.DataFrame({"x": E.ravel(), "y": N.ravel(),
                        "count_all": 1.0, "count_group": 0.0})
    out = run_knn_friction(pop, k_values=[], tau_values=[1, 2],
                           unit_size=U).set_index(["EastWest",
                                                   "NorthSouth"])
    centre = (int(5 * U + U / 2), int(5 * U + U / 2))
    corner = (int(U / 2), int(U / 2))
    # centre: the octile disc - origin + 4 rooks at 1.0; then + 4
    # diagonals at sqrt(2) + 4 rooks at 2.0
    assert out.loc[centre, "N_tau1"] == 5
    assert out.loc[centre, "N_tau2"] == 13
    # corner: the same disc clipped to a quadrant
    assert out.loc[corner, "N_tau1"] == 3
    assert out.loc[corner, "N_tau2"] == 6

    # and the rule itself, independently of the numbers above: every
    # cell inside the budget is one the octile metric admits.
    root2 = 2.0 ** 0.5
    for tau in (1, 2):
        want = sum(1 for dx in range(-5, 6) for dy in range(-5, 6)
                   if max(abs(dx), abs(dy))
                   + (root2 - 1) * min(abs(dx), abs(dy)) <= tau + 1e-9)
        assert out.loc[centre, f"N_tau{tau}"] == want


def test_decay_sum_exact():
    """Still exact - but the origin cell's own people are no longer
    standing on the origin (v1.29.5, BACKLOG 95). They are charged the
    mean intra-cell distance, so their weight is below 1.0."""
    from equipop import selfpot
    cd = _cells(n=80, seed=2)
    dec = Decay(model="negexp", half_life_m=500.0)
    out = run_knn_counts(cd, decay=dec, decay_eps=1e-9)
    pts = np.c_[cd.E, cd.N]
    d_self = selfpot.decay_distance(cd.unit_size, 1.0)
    assert d_self > 0.0                    # the rule is actually on
    for i in [0, 7, 40]:
        d = np.hypot(pts[:, 0] - cd.E[i], pts[:, 1] - cd.N[i])
        d[i] = d_self                      # your own cell, spread out
        w = dec.weight_vec(d)
        assert np.isclose(out.loc[i, "ND_inf"], (w * cd.n).sum(),
                          rtol=1e-9)
        assert np.isclose(out.loc[i, "TD_t_inf"],
                          (w * cd.binary_sums["t"]).sum(), rtol=1e-9)


def test_self_potential_zero_reproduces_pre_1_29_4():
    """Anyone with published numbers can get them back exactly by
    setting self-potential to 0. If this drifts, old work cannot be
    reproduced - so it is asserted, not assumed."""
    cd = _cells(n=80, seed=2)
    dec = Decay(model="negexp", half_life_m=500.0)
    out = run_knn_counts(cd, decay=dec, decay_eps=1e-9,
                         self_potential=0.0)
    pts = np.c_[cd.E, cd.N]
    for i in [0, 7, 40]:
        d = np.hypot(pts[:, 0] - cd.E[i], pts[:, 1] - cd.N[i])
        w = dec.weight_vec(d)              # origin at 0 -> weight 1.0
        assert np.isclose(out.loc[i, "ND_inf"], (w * cd.n).sum(),
                          rtol=1e-9)


def test_area_stats_known_answer():
    df = pd.DataFrame({
        "kom": ["A", "A", "A", "B", "B", np.nan],
        "grp": [1, 0, 1, 0, 1, 1],
        "inc": [100.0, 200.0, np.nan, 50.0, 150.0, 999.0],
        "w":   [2.0, 1.0, 1.0, 3.0, 1.0, 1.0]})
    res = area_stats(df, "kom", binary_vars=["grp"], value_vars=["inc"],
                     weight_col="w").set_index("AreaId")
    # A: N=4 (2+1+1), T=2*1+1*0+1*1=3, R=0.75 ; valid inc = [100,200]
    assert res.loc["A", "N"] == 4 and res.loc["A", "T_grp"] == 3
    assert np.isclose(res.loc["A", "R_grp"], 0.75)
    assert res.loc["A", "Nv_inc"] == 2
    assert np.isclose(res.loc["A", "Mean_inc"], 150.0)
    assert np.isclose(res.loc["A", "Med_inc"], 150.0)
    # B: N=4, T=1, R=0.25; the NaN-area row is excluded
    assert np.isclose(res.loc["B", "R_grp"], 0.25)
    assert len(res) == 2
    # no expansion columns in area mode - honestly absent
    assert not any(c.startswith(("Dist", "Rounds")) for c in res.columns)


def test_bridge_r_values_row_aligned():
    rng = np.random.default_rng(9)
    n = 300
    x = rng.uniform(0, 2000, n); y = rng.uniform(0, 2000, n)
    g = rng.integers(0, 2, n).astype(float)
    res = knn_to_rows(x, y, k_values=[20], r_values=[500.0],
                      treat={"g": g})
    assert "R_g_r500" in res and len(res["R_g_r500"]) == n
    assert np.isfinite(res["N_r500"]).all()
    assert (res["N_r500"] >= 1).all()          # self always within r


def test_seg_profile_accepts_r_labels():
    cd = _cells()
    out = run_knn_counts(cd, k_values=[30], r_values=[600.0])
    prof = seg_profile(out, [30, "r600"], n_col="N_{k}", t_col="T_t_{k}",
                       local_all="N_local", local_grp="t_local")
    assert len(prof) == 3 and np.isfinite(prof["SI"]).all()
