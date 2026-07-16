"""
fastcounts.py - vectorised counts-only k-NN engine (the fast path).

For the common case - aggregated counts, ratio output, no value
arrays - this engine replaces the per-origin Python loop with
KD-tree neighbour queries and cumulative sums over whole chunks of
origins at once. Same mathematics and the SAME ring-atomic tie
convention as run_knn_stats (verified by regression test); one to
two orders of magnitude faster on large datasets.

Use run_knn_stats when you need median/Gini/etc. of value variables;
use run_knn_counts for counts and ratios at scale.
"""

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from .cells import CellData


def _lab(x) -> str:
    """Compact numeric label: 500 -> '500', 2.5 -> '2.5'."""
    return f"{x:g}"


def run_knn_counts(cd: CellData, k_values: list[int] | None = None,
                   m_neighbors: int = 4096,
                   chunk: int = 4096,
                   r_values: list[float] | None = None,
                   decay=None, decay_eps: float = 1e-6) -> pd.DataFrame:
    """
    k-NN counts/ratios for every cell in cd, vectorised.

    m_neighbors : how many nearest CELLS are fetched per origin in the
        fast pass. Origins whose cumulative population within
        m_neighbors cells does not reach max(k) are automatically
        re-run against all cells (exact, slower) - the parameter
        affects speed only, never results.

    Output columns: CellId, EastWest, NorthSouth, N_local,
    <var>_local, and per k: N_k, T_<var>_k, R_<var>_k, Dist_k,
    plus SumN and MaxDistance.
    """
    k_values = sorted(k_values or [])
    r_values = sorted(r_values or [])
    kmax = k_values[-1] if k_values else 0
    rmax = r_values[-1] if r_values else 0.0
    trunc = decay.truncation_radius(decay_eps) if decay is not None else 0.0
    if not (k_values or r_values or decay):
        raise ValueError("give k_values, r_values and/or decay")
    n_cells = len(cd)
    m = min(m_neighbors, n_cells)
    pts = np.c_[cd.E.astype(float), cd.N.astype(float)]
    tree = cKDTree(pts)
    bvars = list(cd.binary_sums)
    pop = cd.n.astype(float)
    grp = {v: cd.binary_sums[v].astype(float) for v in bvars}

    modes = []
    if k_values: modes.append(f"k = {k_values}")
    if r_values: modes.append(f"r = {r_values} m")
    if decay is not None:
        modes.append(f"decayed sum (trunc {trunc:,.0f} m at eps {decay_eps})")
    print(f"[fast] {n_cells} cells, {' | '.join(modes)}, "
          f"fast pass with m = {m} neighbour cells")
    rows = []
    stragglers = 0

    def _solve(dist, idx, oi_range):
        nonlocal stragglers
        # dist, idx: (C, m) sorted by distance (self included at 0)
        cpop = np.cumsum(pop[idx], axis=1)
        cgrp = {v: np.cumsum(grp[v][idx], axis=1) for v in bvars}
        for r, oi in enumerate(oi_range):
            covered = dist[r, -1]
            if ((cpop[r, -1] < kmax or covered < rmax or covered < trunc)
                    and dist.shape[1] < n_cells):
                stragglers += 1
                d2, i2 = tree.query(pts[oi], k=n_cells)
                _solve(d2[None, :], i2[None, :], [oi])
                continue
            rec = {"CellId": cd.labels[oi] if cd.labels else oi,
                   "EastWest": round(float(cd.E[oi]), 2),
                   "NorthSouth": round(float(cd.N[oi]), 2),
                   "N_local": float(pop[oi])}
            for v in bvars:
                rec[f"{v}_local"] = float(grp[v][oi])
            dd, cp = dist[r], cpop[r]
            last = 0
            for k in k_values:
                pos = int(np.searchsorted(cp, k))
                if pos >= len(cp):
                    pos = len(cp) - 1          # unreached: partial
                else:                          # ring-atomic extension
                    while pos + 1 < len(dd) and dd[pos + 1] - dd[pos] < 1e-6:
                        pos += 1
                rec[f"N_{k}"] = cp[pos]
                for v in bvars:
                    rec[f"T_{v}_{k}"] = cgrp[v][r][pos]
                    rec[f"R_{v}_{k}"] = cgrp[v][r][pos] / cp[pos]
                rec[f"Dist_{k}"] = float(dd[pos])
                last = pos
            for rv in r_values:            # radius: all cells within rv,
                pos = int(np.searchsorted(dd, rv, side="right")) - 1
                lab = _lab(rv)             # included wholly (no ties by
                rec[f"N_r{lab}"] = cp[pos]  # construction)
                for v in bvars:
                    rec[f"T_{v}_r{lab}"] = cgrp[v][r][pos]
                    rec[f"R_{v}_r{lab}"] = (cgrp[v][r][pos] / cp[pos]
                                            if cp[pos] > 0 else np.nan)
                last = max(last, pos)
            if decay is not None:          # unbounded decayed sum,
                pos = int(np.searchsorted(dd, trunc, side="right"))
                w = decay.weight_vec(dd[:pos])
                pw = pop[idx[r, :pos]] * w
                nd = float(pw.sum())
                rec["ND_inf"] = nd
                for v in bvars:
                    td = float((grp[v][idx[r, :pos]] * w).sum())
                    rec[f"TD_{v}_inf"] = td
                    rec[f"RD_{v}_inf"] = td / nd if nd > 0 else np.nan
                last = max(last, pos - 1)
            rec["SumN"] = cp[last]
            rec["MaxDistance"] = float(dd[last])
            rows.append(rec)

    for start in range(0, n_cells, chunk):
        sel = np.arange(start, min(start + chunk, n_cells))
        dist, idx = tree.query(pts[sel], k=m, workers=-1)
        _solve(dist, idx, sel)
    if stragglers:
        print(f"[fast] {stragglers} sparse origins exact-solved "
              f"against all cells")
    return pd.DataFrame(rows)
