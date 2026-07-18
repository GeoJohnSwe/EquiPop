"""#14 autocorrelation: PySAL esda cross-validation + known answers."""
import numpy as np
import pandas as pd
import pytest

from equipop.autocorr import (build_weights, morans_i, local_morans,
                              local_g, getis_g, autocorr_profile)


def _grid(nx=15, ny=15):
    gx, gy = np.meshgrid(np.arange(nx), np.arange(ny), indexing="ij")
    return (gx.ravel() * 100.0 + 50), (gy.ravel() * 100.0 + 50)


def _esda_W(E, N, k=8):
    libpysal = pytest.importorskip("libpysal")
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = libpysal.weights.KNN.from_array(np.c_[E, N], k=k)
        w.transform = "r"
    return w


def test_morans_i_matches_esda():
    esda = pytest.importorskip("esda")
    E, N = _grid()
    rng = np.random.default_rng(7)
    y = 0.02 * E + rng.normal(0, 30, len(E))       # gradient + noise
    ours = morans_i(y, build_weights(E, N, "knn", k=8),
                    permutations=99)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        theirs = esda.Moran(y, _esda_W(E, N), permutations=99)
    assert np.isclose(ours["I"], theirs.I, atol=5e-3)   # tie-ring vs strict-k
    assert np.isclose(ours["EI"], theirs.EI)


def test_local_morans_matches_esda():
    esda = pytest.importorskip("esda")
    E, N = _grid(12, 12)
    rng = np.random.default_rng(3)
    y = np.where(E < 600, 10, 0) + rng.normal(0, 2, len(E))
    W = build_weights(E, N, "r", r=150.0)          # rook+queen band
    ours = local_morans(y, W, permutations=99)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import libpysal
        w = libpysal.weights.DistanceBand.from_array(
            np.c_[E, N], threshold=150.0, binary=True)
        w.transform = "r"
        theirs = esda.Moran_Local(y, w, permutations=99)
    assert np.allclose(ours["Ii"], theirs.Is, atol=1e-9)


def test_local_g_star_matches_esda():
    esda = pytest.importorskip("esda")
    E, N = _grid(12, 12)
    rng = np.random.default_rng(5)
    y = rng.uniform(0, 10, len(E)); y[:20] += 15   # a hot corner
    W = build_weights(E, N, "r", r=150.0, row_standardize=False)
    ours = local_g(y, W, star=True)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import libpysal
        w = libpysal.weights.DistanceBand.from_array(
            np.c_[E, N], threshold=150.0, binary=True)
        theirs = esda.G_Local(y, w, transform="B", star=True)
    assert np.allclose(ours, theirs.Zs, atol=1e-8)


def test_known_answer_signs():
    E, N = _grid(14, 14)
    gx = (E - 50) / 100
    gy = (N - 50) / 100
    W = build_weights(E, N, "knn", k=8)
    W_rook = build_weights(E, N, "r", r=110.0)     # orthogonal only
    checker = ((gx + gy) % 2).astype(float)        # perfect dispersion
    grad = gx.astype(float)                        # perfect clustering
    rng = np.random.default_rng(11)
    noise = rng.normal(size=len(E))
    i_c = morans_i(checker, W_rook, permutations=99)["I"]
    i_g = morans_i(grad, W, permutations=99)["I"]
    i_n = morans_i(noise, W, permutations=199)
    assert i_c < -0.5 and i_g > 0.8
    assert abs(i_n["I"]) < 0.1 and i_n["p"] > 0.01
    g = getis_g(grad, build_weights(E, N, "r", r=150,
                                    row_standardize=False))["G"]
    assert np.isfinite(g)


def test_profile_and_smell_warning(capsys):
    from equipop.datasets import load
    from equipop.cells import CellData
    from equipop.fastcounts import run_knn_counts
    g = load("gridby"); p = g["people"]
    cd = CellData(E=p.x.to_numpy(), N=p.y.to_numpy(),
                  n=p.count_all.to_numpy(),
                  binary_sums={"g": p.count_group.to_numpy()},
                  value_arrays={}, unit_size=100.0)
    out = run_knn_counts(cd, [50, 400])
    prof = autocorr_profile(out, ["R_g_50", "R_g_400"], k=8,
                            permutations=49)
    txt = capsys.readouterr().out
    assert "ALREADY-SMOOTHED" in txt                # the loud warning
    assert (prof.I > 0.5).all()                     # smoothed => high I
    assert prof.I.iloc[1] > prof.I.iloc[0]          # rises with k
