"""#17 dispatcher: one row-alignment layer, five engines."""
import numpy as np
import pandas as pd

from equipop.stata_bridge import dispatch, knn_to_rows


def _pts(n=400, seed=8):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, 3000, n); y = rng.uniform(0, 3000, n)
    x[:3] = np.nan                       # missing coordinates kept
    return x, y, rng


def test_dispatch_counts_equals_knn_to_rows():
    x, y, rng = _pts()
    g = rng.integers(0, 2, len(x)).astype(float)
    a = dispatch("counts", x, y, k_values=[25], r_values=[500.0],
                 treat={"g": g})
    b = knn_to_rows(x, y, [25], treat={"g": g}, r_values=[500.0])
    for c in b:
        assert np.allclose(a[c], b[c], equal_nan=True)


def test_dispatch_stats_row_alignment():
    x, y, rng = _pts()
    v = rng.normal(50, 10, len(x))
    out = dispatch("stats", x, y, k_values=[30],
                   values={"v": v}, stats={"v": ["mean"]})
    assert len(out["Mean_v_30"]) == len(x)
    assert np.isnan(out["Mean_v_30"][:3]).all()      # missing coords
    assert np.isfinite(out["Mean_v_30"][3:]).all()
    # rows sharing a cell share the value
    E = np.floor(x[3:] / 100); N = np.floor(y[3:] / 100)
    df = pd.DataFrame({"E": E, "N": N, "m": out["Mean_v_30"][3:]})
    assert (df.groupby(["E", "N"])["m"].nunique() == 1).all()


def test_dispatch_slope_flat_equals_friction():
    x, y, rng = _pts(150, seed=2)
    g = rng.integers(0, 2, len(x)).astype(float)
    # domain size for the zeros altitude array: infer via one call
    fr_out = dispatch("friction", x, y, k_values=[10], tau_values=[3],
                      treat={"g": g})
    ok = np.isfinite(x)
    E = np.floor(x[ok] / 100); N = np.floor(y[ok] / 100)
    nx = int(E.max() - E.min()) + 1; ny = int(N.max() - N.min()) + 1
    sl_out = dispatch("slope", x, y, k_values=[10], tau_values=[3],
                      treat={"g": g}, dem=np.zeros(nx * ny),
                      roundtrip=True)
    for c in ("Rounds_10", "N_10", "N_tau3", "R_g_tau3"):  # named
        # group columns since v1.15 (multi-group friction)
        assert np.allclose(sl_out[c], fr_out[c], equal_nan=True), c


def test_dispatch_fca_matches_direct(tmp_path):
    from equipop.fca import fca
    from equipop.decay import Decay
    x, y, rng = _pts(300, seed=5)
    d = rng.uniform(1, 5, len(x))
    sup = pd.DataFrame({"x": rng.uniform(0, 3000, 40),
                        "y": rng.uniform(0, 3000, 40),
                        "jobs": rng.uniform(1, 20, 40)})
    f = tmp_path / "supply.csv"; sup.to_csv(f, index=False)
    out = dispatch("fca", x, y, demand_arr=d, supply_file=str(f),
                   supply_col="jobs", half_life_m=800.0)
    assert len(out["A"]) == len(x) and np.isnan(out["A"][:3]).all()
    # direct run on the same cells must agree
    ok = np.isfinite(x)
    E = (np.floor(x[ok] / 100) * 100 + 50).astype(float)
    N = (np.floor(y[ok] / 100) * 100 + 50).astype(float)
    cells = (pd.DataFrame({"x": E, "y": N, "_D": d[ok]})
             .groupby(["x", "y"], as_index=False).sum())
    dd, _ = fca(cells, sup, "_D", "jobs",
                decay=Decay(model="negexp", half_life_m=800.0))
    ref = dd.set_index(["x", "y"])["A"]
    got = out["A"][ok]
    assert np.allclose(got, ref.loc[list(zip(E, N))].to_numpy(), rtol=1e-12)


def test_dispatch_lisa_matches_direct():
    from equipop.autocorr import build_weights, local_morans
    x, y, rng = _pts(500, seed=12)
    v = 0.01 * np.nan_to_num(x) + rng.normal(0, 3, len(x))
    out = dispatch("lisa", x, y, values={"v": v}, w_k=8,
                   permutations=49)
    assert len(out["LISA_v_Ii"]) == len(x)
    assert np.isnan(out["LISA_v_Ii"][:3]).all()
    ok = np.isfinite(x)
    E = (np.floor(x[ok] / 100) * 100 + 50).astype(int)
    N = (np.floor(y[ok] / 100) * 100 + 50).astype(int)
    cells = (pd.DataFrame({"E": E, "N": N, "v": v[ok]})
             .groupby(["E", "N"], as_index=False)["v"].mean())
    W = build_weights(cells.E, cells.N, "knn", k=8)
    ref = local_morans(cells.v, W, permutations=9)
    got = pd.DataFrame({"E": E, "N": N,
                        "Ii": out["LISA_v_Ii"][ok]}).drop_duplicates(
        ["E", "N"]).sort_values(["E", "N"])
    assert np.allclose(got.Ii.to_numpy(),
                       ref.assign(E=cells.E, N=cells.N)
                       .sort_values(["E", "N"]).Ii.to_numpy(),
                       rtol=1e-9)


def test_dispatch_counts_decay_matches_direct():
    from equipop.cells import build_cells
    from equipop.fastcounts import run_knn_counts
    from equipop.decay import Decay
    x, y, rng = _pts(300, seed=17)
    g = rng.integers(0, 2, len(x)).astype(float)
    out = dispatch("counts", x, y, k_values=[25], treat={"g": g},
                   half_life_m=800.0)
    assert "ND_inf" in out and "RD_g_inf" in out
    ok = np.isfinite(x)
    df = pd.DataFrame({"x": x[ok], "y": y[ok], "g": g[ok]})
    cd = build_cells(df, "x", "y", binary_vars=["g"], unit_size=100)
    ref = run_knn_counts(cd, [25],
                         decay=Decay(model="negexp", half_life_m=800.0))
    E = (np.floor(x[ok]/100)*100+50); N = (np.floor(y[ok]/100)*100+50)
    r = ref.set_index(["EastWest", "NorthSouth"])
    assert np.allclose(out["ND_inf"][ok],
                       r.loc[list(zip(E, N))]["ND_inf"].to_numpy(),
                       rtol=1e-10)


def test_dispatch_friction_multigroup_resolver_and_counts(tmp_path):
    """v1.15: barrier columns East/North + value col 'cost' resolve;
    TWO groups in one call; counts convention respected."""
    rng = np.random.default_rng(31)
    n = 200
    x = rng.uniform(0, 2000, n); y = rng.uniform(0, 2000, n)
    popn = rng.integers(1, 20, n).astype(float)
    a = np.minimum(rng.integers(0, 8, n).astype(float), popn)
    b = popn - a
    fr = pd.DataFrame({"East": [1050.0] * 8,
                       "North": np.arange(50.0, 850.0, 100.0),
                       "cost": 5})
    f = tmp_path / "barriers.txt"
    fr.to_csv(f, sep="\t", index=False)          # tab-separated txt
    out = dispatch("friction", x, y, k_values=[30], tau_values=[3],
                   treat={"grpA": a, "grpB": b}, weight=popn,
                   treat_are_counts=True, friction_file=str(f))
    ok = np.isfinite(out["N_30"])
    assert (out["T_grpA_30"][ok] <= out["N_30"][ok] + 1e-9).all()
    assert (out["T_grpB_30"][ok] <= out["N_30"][ok] + 1e-9).all()
    s = out["T_grpA_30"][ok] + out["T_grpB_30"][ok]
    assert np.allclose(s, out["N_30"][ok])       # A + B = everyone
    r = out["R_grpA_tau3"][ok]
    assert np.nanmax(r) <= 1 + 1e-9
