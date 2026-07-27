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
                   m_neighbors: int | None = None,
                   chunk: int = 4096,
                   r_values: list[float] | None = None,
                   decay=None, decay_eps: float = 1e-6,
                   origins=None) -> pd.DataFrame:
    """
    k-NN counts/ratios for every cell in cd, vectorised.

    origins : optional array of CELL indices - compute results only
        for these origins; the tree and destination mass stay GLOBAL,
        so per-origin results are exactly those of a full run (the
        tile-and-flush substrate, #18).
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
    if m_neighbors is None:            # auto-tuned (v1.16.3/.6)
        from .cells import auto_m_neighbors
        m_neighbors = auto_m_neighbors(cd, k_values, r_values,
                                       trunc_m=trunc)
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
    rows_by_oi: dict = {}
    stragglers = 0

    def _solve(dist, idx, oi_range):
        """Fill in every origin this neighbourhood can settle; hand
        back the ones that need a WIDER search (v1.16.4 ladder - see
        the loop below)."""
        unsat = []
        # dist, idx: (C, m) sorted by distance (self included at 0)
        cpop = np.cumsum(pop[idx], axis=1)
        cgrp = {v: np.cumsum(grp[v][idx], axis=1) for v in bvars}
        for r, oi in enumerate(oi_range):
            covered = dist[r, -1]
            if ((cpop[r, -1] < kmax or covered < rmax or covered < trunc)
                    and dist.shape[1] < n_cells):
                unsat.append(oi)
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
            rows_by_oi[oi] = rec
        return unsat

    origins = np.arange(n_cells) if origins is None \
        else np.asarray(origins)
    # --------------------------------------------- v1.16.4 the LADDER
    # Thin-population origins cannot reach k inside the neighbourhood
    # the density suggested. Until now each one was re-solved against
    # ALL cells - and in a country with both cities and wilderness
    # that single cliff dominated the run (a field run: 64,966 such
    # origins, 1 h 46 min of the 1 h 51 min total). Now the search
    # widens x8 at a time for exactly those origins, which is a few
    # thousand cells rather than half a million, and only the last
    # step - if it is ever reached - is the full set. Results are
    # unchanged either way: the walk still ends inside a complete
    # neighbourhood.
    todo = origins
    m_now = m
    while len(todo):
        nxt = []
        c_now = max(1, min(chunk, int(4e6 // max(m_now, 1))))
        for start in range(0, len(todo), c_now):
            sel = todo[start:min(start + c_now, len(todo))]
            dist, idx = tree.query(pts[sel], k=m_now, workers=-1)
            if m_now == 1:
                dist, idx = dist[:, None], idx[:, None]
            nxt.extend(_solve(dist, idx, sel))
        if not nxt or m_now >= n_cells:
            break
        stragglers += len(nxt)
        m_now = int(min(n_cells, max(m_now * 8, 64)))
        print(f"[fast] {len(nxt)} sparse origins need a wider search "
              f"- retrying those with m = {m_now}"
              + (" (all cells)" if m_now >= n_cells else ""))
        todo = np.asarray(nxt)
    if stragglers:
        print(f"[fast] {stragglers} widened searches in total "
              "(results identical, only the route differs)")
    return pd.DataFrame([rows_by_oi[o] for o in origins])
