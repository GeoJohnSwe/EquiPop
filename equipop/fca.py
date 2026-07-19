"""
fca.py - floating catchment accessibility (#11): kFCA / 2SFCA / 3SFCA
with the neighbourhood-definition menu as reach modes, match-table
segmentation, and optional doubly-constrained balancing.

THE FAMILY in EquiPop terms: supply cells (jobs, doctors, beds ...)
and demand cells (workers, patients ...) meet through a weight matrix
W_ij built from any reach mode of the menu:

  reach="decay"  unbounded decayed weights (eps-truncated)  [Hansen-ish]
  reach="r"      classic catchment: d <= r (optionally * decay)
  reach="k"      kFCA: each catchment GROWS until it contains k units
                 of the opposite side's MASS (k persons around a
                 workplace, k jobs around a home) - fixed-population
                 catchments, the EquiPop signature; equidistant cells
                 enter wholly (tie convention). Optionally * decay.
  reach="effort" weights from SLOPE/FRICTION effort (optionally
                 round-trip); decay half-life is then in ROUNDS.

METHODS:
  method="2sfca"  R_j = S_j / sum_i W_ij D_i ;  A_i = sum_j W_ij R_j
  method="3sfca"  demand splits itself first (selection weights
                  G_ij = W_ij / sum_j' W_ij'), then as above with
                  G*W in both steps (Wan et al. 2012 logic).
  balance=n > 0   doubly-constrained (Wilson) balancing instead:
                  iterate a_i = 1/sum_j b_j S_j W_ij,
                          b_j = 1/sum_i a_i D_i W_ij   n times (or to
                  tol); COMPETITION-ADJUSTED access A_i = 1/a_i and
                  supply congestion C_j = 1/b_j are returned; implied
                  flows F_ij = a_i D_i W_ij b_j S_j then reproduce
                  both margins (checked and reported loudly).

A_i units: opposite-side mass per unit of own-side mass experienced
at i (jobs per worker, GP-equivalents per person) - comparable across
segments and reaches.
"""

import numpy as np
import pandas as pd


# ------------------------------------------------------------ weights
def _dist_matrix(dx, dy, sx, sy, chunk=4000):
    """Euclidean demand x supply distances, chunked rows."""
    out = np.empty((len(dx), len(sx)))
    for a in range(0, len(dx), chunk):
        b = min(a + chunk, len(dx))
        out[a:b] = np.hypot(dx[a:b, None] - sx[None, :],
                            dy[a:b, None] - sy[None, :])
    return out


def _k_mask(D, mass_other, k):
    """kFCA catchment per row of distance matrix D: include nearest
    columns until cumulated mass_other >= k; EQUIDISTANT columns enter
    wholly (tie convention). Returns boolean mask."""
    order = np.argsort(D, axis=1, kind="stable")
    mask = np.zeros(D.shape, dtype=bool)
    for i in range(D.shape[0]):
        o = order[i]
        cum = np.cumsum(mass_other[o])
        pos = int(np.searchsorted(cum, k, side="left"))
        pos = min(pos, len(o) - 1)
        d_star = D[i, o[pos]]
        mask[i] = D[i] <= d_star + 1e-6          # atomic tie ring
    return mask


def _effort_matrix(demand, supply, altitude, model, roundtrip,
                   unit_size, fr, chunk, **model_params):
    """Demand x supply EFFORT matrix from the slope engine (round-trip
    optional). Domain spans both sides; supply cells carry zero pop."""
    from .slope import SlopeGrid
    from scipy.sparse.csgraph import dijkstra

    dom = pd.concat([
        demand.rename(columns={demand.columns[0]: "x",
                               demand.columns[1]: "y"})[["x", "y"]]
        .assign(count_all=1.0),
        supply.rename(columns={supply.columns[0]: "x",
                               supply.columns[1]: "y"})[["x", "y"]]
        .assign(count_all=1.0)]).groupby(["x", "y"],
                                         as_index=False).sum()
    dom["count_group"] = 0.0
    grid = SlopeGrid(dom, fr, unit_size, 0, "count_all", "count_group",
                     altitude=altitude, model=model,
                     roundtrip=roundtrip, **model_params)
    u = int(unit_size)

    def nodes_of(df):
        i = (((np.floor(df.iloc[:, 0].to_numpy(float) / u) * u + u / 2)
              - grid.x0) // u).astype(np.int64)
        j = (((np.floor(df.iloc[:, 1].to_numpy(float) / u) * u + u / 2)
              - grid.y0) // u).astype(np.int64)
        return np.asarray(i * grid.ny + j)

    dn, sn = nodes_of(demand), nodes_of(supply)
    E = np.empty((len(dn), len(sn)))
    for a in range(0, len(dn), chunk):
        b = min(a + chunk, len(dn))
        eff = dijkstra(grid.graph, directed=True, indices=dn[a:b])
        if roundtrip:
            back = dijkstra(grid.graph.T, directed=True,
                            indices=dn[a:b])
            eff = 0.5 * (eff + back)
        E[a:b] = eff[:, sn]
        print(f"[fca] effort rows {b}/{len(dn)}")
    return E


def _weights(demand, supply, decay, reach, r, k, eps,
             effort_kw) -> np.ndarray:
    dx = demand.iloc[:, 0].to_numpy(float)
    dy = demand.iloc[:, 1].to_numpy(float)
    sx = supply.iloc[:, 0].to_numpy(float)
    sy = supply.iloc[:, 1].to_numpy(float)

    if reach == "effort":
        E = _effort_matrix(demand, supply, **effort_kw)
        if decay is None:
            raise ValueError("reach='effort' needs a decay whose "
                             "half-life is in ROUNDS")
        print("[fca] effort reach: decay half-life read in ROUNDS")
        W = np.where(np.isfinite(E),
                     decay.weight_vec(np.where(np.isfinite(E), E, 0.0)),
                     0.0)
        return W

    D = _dist_matrix(dx, dy, sx, sy)
    if reach == "decay":
        if decay is None:
            raise ValueError("reach='decay' needs a decay")
        W = decay.weight_vec(D)
        W[W < eps] = 0.0
    elif reach == "r":
        if r is None:
            raise ValueError("reach='r' needs r")
        W = (D <= r).astype(float)
        if decay is not None:
            W *= decay.weight_vec(D)
    elif reach == "k":
        if k is None:
            raise ValueError("reach='k' needs k")
        d_mass = demand["_D"].to_numpy()
        s_mass = supply["_S"].to_numpy()
        m_d = _k_mask(D, s_mass, k)          # homes gather k jobs
        m_s = _k_mask(D.T, d_mass, k).T      # workplaces gather k people
        W = (m_d | m_s).astype(float)        # inside either catchment
        if decay is not None:
            W *= decay.weight_vec(D)
    else:
        raise ValueError(f"unknown reach '{reach}'")
    return W


# ---------------------------------------------------------------- fca
def fca(demand: pd.DataFrame, supply: pd.DataFrame,
        demand_col: str, supply_col: str,
        decay=None, reach: str = "decay",
        r: float | None = None, k: float | None = None,
        method: str = "2sfca", balance: int = 0, tol: float = 1e-10,
        x_col: str = "x", y_col: str = "y", eps: float = 1e-6,
        # effort-reach extras:
        altitude=None, model: str = "tobler", roundtrip: bool = True,
        unit_size: float = 100.0, fr=None, chunk: int = 500,
        **model_params):
    """
    Floating catchment accessibility. Returns (demand_out, supply_out):
    demand_out gains A (access: supply per unit demand experienced),
    supply_out gains R (supply-to-demand ratio) - or, when balance>0,
    A = 1/a_i (competition-adjusted) and C = 1/b_j (congestion).
    Zero-weight rows get A = 0 loudly counted, never NaN-hidden.
    """
    dem = demand[[x_col, y_col, demand_col]].copy()
    sup = supply[[x_col, y_col, supply_col]].copy()
    dem["_D"] = dem[demand_col].astype(float)
    sup["_S"] = sup[supply_col].astype(float)

    W = _weights(dem, sup, decay, reach, r, k, eps,
                 dict(altitude=altitude, model=model,
                      roundtrip=roundtrip, unit_size=unit_size,
                      fr=fr, chunk=chunk, **model_params))
    Dm = dem["_D"].to_numpy()
    Sm = sup["_S"].to_numpy()
    print(f"[fca] {len(dem)} demand x {len(sup)} supply cells, "
          f"reach='{reach}', method="
          f"{'balanced' if balance else method}, "
          f"nonzero weights {(W > 0).mean():.1%}")

    if balance > 0:
        # doubly-constrained flows require SUM(D) == SUM(S); real
        # markets never oblige, so the SUPPLY margin is scaled to the
        # demand total INSIDE the flow model (loudly) - reported A
        # uses UNSCALED supply, so units stay jobs-per-worker.
        sf = Dm.sum() / max(Sm.sum(), 1e-300)
        if abs(sf - 1.0) > 1e-12:
            print(f"[fca] margins imbalanced (S/D = {1/sf:.4f}): "
                  f"supply scaled by {sf:.4f} for the flow model only")
        Sb = Sm * sf
        a = np.ones(len(dem))
        b = np.ones(len(sup))
        for it in range(balance):
            a_new = 1.0 / np.maximum((W * (b * Sb)[None, :]).sum(1),
                                     1e-300)
            b_new = 1.0 / np.maximum((W * (a_new * Dm)[:, None]).sum(0),
                                     1e-300)
            delta = max(np.abs(a_new - a).max(), np.abs(b_new - b).max())
            a, b = a_new, b_new
            if delta < tol:
                break
        F = (a * Dm)[:, None] * W * (b * Sb)[None, :]
        row_err = np.abs(F.sum(1) - Dm)[Dm > 0].max() if (Dm > 0).any() else 0
        col_err = np.abs(F.sum(0) - Sb)[Sb > 0].max() if (Sb > 0).any() else 0
        print(f"[fca] balancing: {it + 1} iterations, delta {delta:.2e}, "
              f"margin errors row {row_err:.2e} col {col_err:.2e}"
              + ("" if delta < tol else " - NOT fully converged, "
                 "raise balance="))
        # GAUGE FIXING: (a, b) are identified only up to a scalar
        # (a->ca, b->b/c leaves every flow unchanged), so raw 1/a has
        # arbitrary scale. Convention: demand-weighted mean A equals
        # the global (unscaled) S/D, and supply-weighted mean C = 1.
        A_raw = np.where(Dm > 0, 1.0 / (a * sf), 0.0)
        target = Sm.sum() / max(Dm.sum(), 1e-300)
        wmean = np.average(A_raw[Dm > 0], weights=Dm[Dm > 0]) \
            if (Dm > 0).any() else 1.0
        A = A_raw * (target / max(wmean, 1e-300))
        C_raw = np.where(Sm > 0, 1.0 / b, 0.0)
        cmean = np.average(C_raw[Sm > 0], weights=Sm[Sm > 0]) \
            if (Sm > 0).any() else 1.0
        C = C_raw / max(cmean, 1e-300)
        print(f"[fca] gauge fixed: demand-weighted mean A = "
              f"{target:.4f} (global S/D), supply-weighted mean C = 1")
        demand_out = demand.copy(); demand_out["A"] = A
        supply_out = supply.copy(); supply_out["C"] = C
        return demand_out, supply_out

    J = W @ Sm          # step-1 potential: decayed supply, competition-blind
    G = None
    if method == "3sfca":
        rows = W.sum(1, keepdims=True)
        G = np.divide(W, rows, out=np.zeros_like(W), where=rows > 0)
        W = G * W
    elif method != "2sfca":
        raise ValueError(f"unknown method '{method}'")

    denom = (W * Dm[:, None]).sum(0)
    R = np.divide(Sm, denom, out=np.zeros_like(Sm), where=denom > 0)
    starved = int(((denom <= 0) & (Sm > 0)).sum())
    if starved:
        print(f"[fca] {starved} supply cells reach no demand -> R = 0")
    A = W @ R
    orphans = int(((W.sum(1) <= 0) & (Dm > 0)).sum())
    if orphans:
        print(f"[fca] {orphans} demand cells reach no supply -> A = 0")

    demand_out = demand.copy(); demand_out["A"] = A
    demand_out["J"] = J   # step-1 potential; J/A = effective decayed
                          # competitor mass faced (units: workers)
    supply_out = supply.copy(); supply_out["R"] = R
    print(f"[fca] A: mean {A[Dm > 0].mean():.4f}, "
          f"p10 {np.percentile(A[Dm > 0], 10):.4f}, "
          f"p90 {np.percentile(A[Dm > 0], 90):.4f} "
          f"(global S/D = {Sm.sum() / max(Dm.sum(), 1e-300):.4f})")
    return demand_out, supply_out


# ------------------------------------------------- match-table runner
def fca_segments(demand: pd.DataFrame, supply: pd.DataFrame,
                 segments: list[dict], **kw):
    """
    Orchestrator: one fca() per match-table row, results side by side.

    segments = [{"name": "low",  "demand_col": "LowEdu_workers",
                 "supply_col": "LowEdu_jobs", ...per-segment overrides},
                {"name": "all",  "demand_col": "Working_sum",
                 "supply_col": "Jobs"}]

    Returns (demand_out with A_<name> columns, supply_out with
    R_<name> or C_<name> columns). Segment overrides win over **kw
    (e.g. a different k or decay per segment).
    """
    demand_out = demand.copy()
    supply_out = supply.copy()
    for seg in segments:
        seg = dict(seg)
        name = seg.pop("name")
        args = {**kw, **seg}
        print(f"[fca] === segment '{name}' ===")
        d_res, s_res = fca(demand, supply, **args)
        demand_out[f"A_{name}"] = d_res["A"].to_numpy()
        if "J" in d_res:
            demand_out[f"J_{name}"] = d_res["J"].to_numpy()
        rc = "C" if args.get("balance", 0) else "R"
        supply_out[f"{rc}_{name}"] = s_res[rc].to_numpy()
    return demand_out, supply_out


# =====================================================================
# #16 - PROPENSITY MATCH-TABLE FCA: from binary segments to
# probabilistic competition. Two modes:
#   GROUP mode: demand groups g with propensity matrix M[g][c] over
#     supply categories c (rows = search allocation, sum to 1).
#   CELL mode: per-cell propensity columns (spatially varying M -
#     "propensity fields", estimator (f)).
# Math (2SFCA logic throughout, one pass, no iteration):
#   P_j^c = sum_i w_ij * sum_g M[g,c] D_i^g      (pressure on c at j)
#   R_j^c = S_j^c / P_j^c                        (competed-for supply)
#   A_i^g = sum_c M[g,c] * sum_j w_ij R_j^c      (group access at i)
#   J_i^g = sum_c M[g,c] * sum_j w_ij S_j^c      (competition-blind)
# Identity M with groups == categories reproduces fca_segments
# EXACTLY (regression-tested).
# =====================================================================

def fca_propensity(demand: pd.DataFrame, supply: pd.DataFrame,
                   M, demand_cols, supply_cols,
                   decay=None, reach: str = "decay",
                   r: float | None = None, k: float | None = None,
                   x_col: str = "x", y_col: str = "y",
                   cell_propensity: bool = False,
                   demand_total: str | None = None,
                   eps: float = 1e-6):
    """
    GROUP mode (cell_propensity=False):
      demand_cols : {group: column of group demand} e.g.
                    {"low": "LowEdu_sum", "other": "Other_sum"}
      supply_cols : {category: column} e.g. {"lowjob": "LowEdu_jobs",
                    "otherjob": "Other_jobs"}
      M : DataFrame (index=groups, columns=categories) of search
          propensities. Rows are LOUDLY normalized to sum to 1.
      -> demand gains A_<g>, J_<g>; supply gains R_<c>.

    CELL mode (cell_propensity=True, estimator (f)):
      demand_total : column of total searchers per cell.
      demand_cols  : {category: propensity column} - per-cell vectors
                     (your regression predictions averaged to cells;
                     strip area effects - geography belongs HERE).
      -> demand gains A, J; supply gains R_<c>.
    """
    dem = demand.copy()
    sup = supply.copy()
    dem["_D"] = 1.0; sup["_S"] = 1.0          # placeholders for _weights
    W = _weights(dem.rename(columns={x_col: "x", y_col: "y"}),
                 sup.rename(columns={x_col: "x", y_col: "y"}),
                 decay, reach, r, k, eps, {})
    cats = list(supply_cols)
    S = np.column_stack([sup[supply_cols[c]].to_numpy(float)
                         for c in cats])                    # (ns, C)

    if cell_propensity:
        if demand_total is None:
            raise ValueError("cell mode needs demand_total")
        D = dem[demand_total].to_numpy(float)               # (nd,)
        P = np.column_stack([dem[demand_cols[c]].to_numpy(float)
                             for c in cats])                # (nd, C)
        rs = P.sum(1, keepdims=True)
        if not np.allclose(rs[rs[:, 0] > 0], 1.0, atol=1e-6):
            print("[fca] cell propensities do not sum to 1 -> "
                  "normalizing rows LOUDLY (zero rows stay zero)")
            P = np.divide(P, rs, out=np.zeros_like(P), where=rs > 0)
        press = W.T @ (P * D[:, None])                      # (ns, C)
        R = np.divide(S, press, out=np.zeros_like(S), where=press > 0)
        WR = W @ R                                          # (nd, C)
        WS = W @ S
        out_d = demand.copy()
        out_d["A"] = (P * WR).sum(1)
        out_d["J"] = (P * WS).sum(1)
        out_s = supply.copy()
        for ci, c in enumerate(cats):
            out_s[f"R_{c}"] = R[:, ci]
        print(f"[fca] propensity (CELL mode): {len(cats)} categories, "
              f"A mean {out_d['A'].mean():.4f}")
        return out_d, out_s

    groups = list(demand_cols)
    Mdf = pd.DataFrame(M) if not isinstance(M, pd.DataFrame) else M
    Mm = Mdf.loc[groups, cats].to_numpy(float)              # (G, C)
    rs = Mm.sum(1, keepdims=True)
    if not np.allclose(rs, 1.0, atol=1e-9):
        print(f"[fca] M rows sum to {rs.ravel().round(4)} -> "
              "normalizing to 1 LOUDLY (search allocation convention)")
        Mm = Mm / rs
    D = np.column_stack([dem[demand_cols[g]].to_numpy(float)
                         for g in groups])                  # (nd, G)
    press = W.T @ (D @ Mm)                                  # (ns, C)
    R = np.divide(S, press, out=np.zeros_like(S), where=press > 0)
    WR = W @ R
    WS = W @ S
    out_d = demand.copy()
    for gi, g in enumerate(groups):
        out_d[f"A_{g}"] = WR @ Mm[gi]
        out_d[f"J_{g}"] = WS @ Mm[gi]
    out_s = supply.copy()
    for ci, c in enumerate(cats):
        out_s[f"R_{c}"] = R[:, ci]
    print(f"[fca] propensity (GROUP mode): {len(groups)} groups x "
          f"{len(cats)} categories; A means "
          + ", ".join(f"{g}={out_d[f'A_{g}'][D[:,gi]>0].mean():.3f}"
                      for gi, g in enumerate(groups)))
    return out_d, out_s
