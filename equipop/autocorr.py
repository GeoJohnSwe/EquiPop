"""
autocorr.py - spatial autocorrelation (#14): Moran's I and Getis-Ord
G, global and local, with weights born from the neighbourhood menu
and the multiscalar-profile pattern of the rest of the package.

WEIGHTS from our own engines' logic:
  build_weights(E, N, mode="knn", k=8)      k nearest cells, ATOMIC
                                            tie ring included
  build_weights(..., mode="r", r=500)       distance band
  build_weights(..., mode="decay", decay=)  decay-weighted (any of the
                                            five half-life families)
Row-standardised by default (each row sums to 1).

STATISTICS:
  morans_i(y, W)       global I, analytic E[I] and z, permutation p
  local_morans(y, W)   LISA: I_i, HH/LL/HL/LH quadrant, conditional-
                       permutation p per cell
  getis_g(y, W)        global G (binary weights recommended)
  local_g(y, W)        Gi* (star: the cell itself included)
  autocorr_profile(df, cols, ...)  one I (and optional G) per scale -
                       the multiscalar profile, e.g. over R_g_50,
                       R_g_400, R_g_1600

THE LOUD WARNING (printed whenever a column smells like R_*_k):
autocorrelating an EquiPop context column measures the autocorrelation
of an ALREADY-SMOOTHED surface - overlapping neighbourhoods induce
correlation BY CONSTRUCTION. Legitimate and often exactly what you
want (how far does the smoothed structure reach?), but it is not the
autocorrelation of the raw process. Know which one you are testing.
"""

import re

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree


# ------------------------------------------------------------- weights
def build_weights(E, N, mode: str = "knn", k: int = 8,
                  r: float | None = None, decay=None,
                  row_standardize: bool = True,
                  tie_tol: float = 1e-6) -> csr_matrix:
    """Sparse spatial weights among cells (self excluded)."""
    pts = np.c_[np.asarray(E, float), np.asarray(N, float)]
    n = len(pts)
    tree = cKDTree(pts)

    rows, cols, vals = [], [], []
    if mode == "knn":
        dd, ii = tree.query(pts, k=min(k + 1, n))
        for i in range(n):
            d_k = dd[i, -1]                       # kth neighbour dist
            idx = tree.query_ball_point(pts[i], d_k + tie_tol)
            idx = [j for j in idx if j != i]      # atomic tie ring
            rows += [i] * len(idx); cols += idx; vals += [1.0] * len(idx)
    elif mode == "r":
        if r is None:
            raise ValueError("mode='r' needs r")
        for i, idx in enumerate(tree.query_ball_point(pts, r)):
            idx = [j for j in idx if j != i]
            rows += [i] * len(idx); cols += idx; vals += [1.0] * len(idx)
    elif mode == "decay":
        if decay is None:
            raise ValueError("mode='decay' needs a Decay")
        trunc = decay.truncation_radius(1e-6)
        for i, idx in enumerate(tree.query_ball_point(pts, trunc)):
            idx = np.array([j for j in idx if j != i])
            if len(idx) == 0:
                continue
            d = np.hypot(*(pts[idx] - pts[i]).T)
            w = decay.weight_vec(d)
            rows += [i] * len(idx); cols += list(idx); vals += list(w)
    else:
        raise ValueError(f"unknown mode '{mode}'")

    W = csr_matrix((vals, (rows, cols)), shape=(n, n))
    isolates = int((W.getnnz(axis=1) == 0).sum())
    if isolates:
        print(f"[autocorr] {isolates} isolate cells (no neighbours) - "
              "their local statistics are undefined (NaN)")
    if row_standardize:
        s = np.asarray(W.sum(axis=1)).ravel()
        s[s == 0] = 1.0
        W = csr_matrix(W.multiply(1.0 / s[:, None]))
    print(f"[autocorr] W: {n} cells, mode='{mode}', "
          f"{W.nnz} links, row-standardised={row_standardize}")
    return W


def _smell_check(name: str):
    if re.match(r"^(R|RD)_.+_(r?\d|inf)", str(name)):
        print(f"[autocorr] NOTE: '{name}' looks like an EquiPop context "
              "column - you are measuring the autocorrelation of an "
              "ALREADY-SMOOTHED surface (overlapping neighbourhoods "
              "correlate by construction). Often intended; know it.")


# -------------------------------------------------------------- global
def morans_i(y, W: csr_matrix, permutations: int = 999,
             seed: int | None = 1848, name: str | None = None) -> dict:
    if name:
        _smell_check(name)
    y = np.asarray(y, float)
    ok = np.isfinite(y)
    if not ok.all():
        print(f"[autocorr] {int((~ok).sum())} non-finite values -> "
              "mean-imputed for I (report your basis!)")
        y = np.where(ok, y, np.nanmean(y))
    z = y - y.mean()
    s0 = W.sum()
    n = len(y)
    I = (n / s0) * float(z @ (W @ z)) / float(z @ z)
    EI = -1.0 / (n - 1)

    rng = np.random.default_rng(seed)
    sims = np.empty(permutations)
    for p in range(permutations):
        zp = rng.permutation(z)
        sims[p] = (n / s0) * float(zp @ (W @ zp)) / float(zp @ zp)
    p_sim = (1 + np.sum(sims >= I if I >= EI else sims <= I)) \
        / (permutations + 1)
    zscore = (I - sims.mean()) / sims.std(ddof=1)
    print(f"[autocorr] Moran's I = {I:.4f} (E[I] = {EI:.4f}), "
          f"z = {zscore:.2f}, p_perm = {p_sim:.4f} "
          f"({permutations} permutations)")
    return {"I": I, "EI": EI, "z": zscore, "p": p_sim, "sims": sims}


def getis_g(y, W: csr_matrix, name: str | None = None) -> dict:
    """Global G - use binary (non-standardised) weights."""
    if name:
        _smell_check(name)
    y = np.asarray(y, float)
    num = float(y @ (W @ y))
    den = y.sum() ** 2 - float(y @ y)
    G = num / den if den else np.nan
    print(f"[autocorr] global G = {G:.6f}")
    return {"G": G}


# --------------------------------------------------------------- local
def local_morans(y, W: csr_matrix, permutations: int = 999,
                 seed: int | None = 1848,
                 name: str | None = None) -> pd.DataFrame:
    """LISA per cell: Ii, quadrant (HH/LL/HL/LH), conditional-
    permutation pseudo p."""
    if name:
        _smell_check(name)
    y = np.asarray(y, float)
    n = len(y)
    z = (y - np.nanmean(y))
    m2 = float(np.nansum(z * z)) / (n - 1)   # esda convention (n-1)
    lag = W @ np.where(np.isfinite(z), z, 0.0)
    Ii = (z / m2) * lag
    quad = np.where(z >= 0, np.where(lag >= 0, "HH", "HL"),
                    np.where(lag >= 0, "LH", "LL"))

    rng = np.random.default_rng(seed)
    W = W.tocsr()
    p = np.full(n, np.nan)
    others = np.arange(n)
    zf = np.where(np.isfinite(z), z, 0.0)
    for i in range(n):
        nb = W.indices[W.indptr[i]:W.indptr[i + 1]]
        wv = W.data[W.indptr[i]:W.indptr[i + 1]]
        if len(nb) == 0 or not np.isfinite(z[i]):
            continue
        pool = np.delete(zf, i)
        draws = rng.choice(pool, size=(permutations, len(nb)))
        sims = (z[i] / m2) * (draws @ wv)
        extreme = np.sum(sims >= Ii[i]) if Ii[i] >= 0 \
            else np.sum(sims <= Ii[i])
        p[i] = (1 + extreme) / (permutations + 1)
    print(f"[autocorr] LISA: {n} cells, quadrants "
          f"{pd.Series(quad).value_counts().to_dict()}, "
          f"{int((p < 0.05).sum())} cells with p < 0.05")
    return pd.DataFrame({"Ii": Ii, "quad": quad, "p": p})


def local_g(y, W: csr_matrix, star: bool = True,
            name: str | None = None) -> np.ndarray:
    """Getis-Ord Gi (star=True includes the cell itself): z-scored."""
    if name:
        _smell_check(name)
    y = np.asarray(y, float)
    n = len(y)
    W = W.tolil(copy=True)
    if star:
        W.setdiag(1.0)
    W = W.tocsr()
    wsum = np.asarray(W.sum(axis=1)).ravel()
    w2 = np.asarray(W.multiply(W).sum(axis=1)).ravel()
    ybar, s = y.mean(), y.std(ddof=0)
    num = (W @ y) - wsum * ybar
    den = s * np.sqrt((n * w2 - wsum ** 2) / (n - 1))
    g = np.divide(num, den, out=np.full(n, np.nan), where=den > 0)
    print(f"[autocorr] Gi{'*' if star else ''}: "
          f"{int((np.abs(g) > 1.96).sum())} cells beyond |z| = 1.96")
    return g


# ------------------------------------------------------------- profile
def autocorr_profile(df: pd.DataFrame, cols: list[str], E_col="EastWest",
                     N_col="NorthSouth", mode="knn", k=8, r=None,
                     decay=None, permutations: int = 999,
                     seed: int | None = 1848) -> pd.DataFrame:
    """Moran's I per column - the multiscalar profile (one row per
    scale, e.g. cols=[R_g_50, R_g_400, R_g_1600])."""
    W = build_weights(df[E_col], df[N_col], mode=mode, k=k, r=r,
                      decay=decay)
    rows = []
    for c in cols:
        res = morans_i(df[c], W, permutations=permutations, seed=seed,
                       name=c)
        rows.append({"column": c, "I": res["I"], "z": res["z"],
                     "p": res["p"]})
    return pd.DataFrame(rows)
