"""
stata_bridge.py - the pure-Python side of the Stata integration.

Design: everything computable lives HERE (tested by pytest, no Stata
required); the .ado file's python block only moves arrays across the
sfi boundary and calls knn_to_rows(). That keeps the untestable-
outside-Stata surface to a few lines.

The contract that makes the Stata round trip work: results come back
ROW-ALIGNED to the input observations (one value per individual, the
spec's "disaggregated outfile"), so the ado can store them straight
into the dataset in memory and the user can `regress` immediately.
Rows with missing coordinates receive missing values.
"""

import numpy as np
import pandas as pd

from .cells import build_cells
from .fastcounts import run_knn_counts


def _binned_decay_counts(cd, cells, k_values, r_values, decay,
                         half_life, n_bins, decay_eps, m_neighbors,
                         n_rows, valid):
    """VARIABLE-BANDWIDTH decay (v1.17): each row carries its own
    half-life - an estimated median travel distance, a group
    potential, or the row's own Dist_k (urban form setting the
    bandwidth).

    A cell may hold people with different bandwidths, so the pass is
    run once per QUANTILE BIN of the half-life, restricted to the
    cells that actually contain that bin's people (`origins=`), with
    the bin's own Decay. Destination mass and the tree stay global,
    so every pass is exact; only the kernel differs. Cost is
    dominated by the widest bin, because the truncation radius
    scales with the half-life.
    """
    from .decay import Decay
    h = np.asarray(half_life, float)
    hv = h[np.asarray(valid)]
    if not np.isfinite(hv).all() or (hv <= 0).any():
        raise ValueError("[decay] the half-life field holds missing, "
                         "zero or negative values - every row needs a "
                         "positive bandwidth in metres")
    n_bins = max(1, int(n_bins))
    uniq = np.unique(hv)
    if len(uniq) <= n_bins:
        # few distinct bandwidths (a group potential, say): each one
        # gets its OWN pass - no approximation at all
        idx = np.searchsorted(uniq, hv)
    else:
        cuts = np.unique(np.quantile(
            hv, np.linspace(0.0, 1.0, n_bins + 1)[1:-1]))
        idx = np.searchsorted(cuts, hv, side="right")
    # quantile cuts can skip labels; make the bins consecutive so
    # row -> frame alignment cannot slip
    _, idx = np.unique(idx, return_inverse=True)
    cell_e = np.asarray(cells["_E"])
    cell_n = np.asarray(cells["_N"])
    key_to_pos = {(e, n): i for i, (e, n) in
                  enumerate(zip(cd.E, cd.N))}
    frames = []
    print(f"[decay] variable bandwidth: {len(np.unique(idx))} bins "
          f"over half-lives {hv.min():,.0f}-{hv.max():,.0f} m")
    for b in range(idx.max() + 1):
        sel = idx == b
        hb = float(np.median(hv[sel]))
        origins = sorted({key_to_pos[(e, n)] for e, n in
                          zip(cell_e[sel], cell_n[sel])
                          if (e, n) in key_to_pos})
        # build a FRESH Decay: beta is derived in __post_init__, so
        # mutating half_life_m on a copy would leave the old kernel
        dec_b = Decay(model=decay.model, half_life_m=hb,
                      gamma=getattr(decay, "gamma", None))
        print(f"[decay]   bin {int(b) + 1}: half-life {hb:,.0f} m, "
              f"{int(sel.sum())} rows, {len(origins)} origin cells")
        part = run_knn_counts(cd, k_values, decay_eps=decay_eps,
                              m_neighbors=m_neighbors,
                              r_values=r_values, decay=dec_b,
                              origins=np.asarray(origins, int))
        part = part.set_index(["EastWest", "NorthSouth"])
        frames.append((sel, part))
    # Rows of a bin read THAT bin's pass. A cell holding people of
    # two bandwidths legitimately yields two different decayed sums -
    # one per person - which a single cell-indexed frame cannot say,
    # so the bins travel separately to the row mapping.
    row_bin = np.asarray(idx, int)
    parts = [f[1] for f in frames]
    # non-decay columns (N, Dist, T, R) are identical across bins -
    # the union of the passes covers every cell, so any occurrence
    # serves as the base frame
    base = pd.concat(parts)
    base = base[~base.index.duplicated(keep="first")]
    return parts, row_bin, base


def knn_to_rows(x, y, k_values=None, treat: dict | None = None,
                weight=None, unit_size: float = 100.0,
                m_neighbors: int | None = None,
                decay_eps: float = 1e-6,
                r_values=None, decay=None,
                treat_are_counts: bool = False,
                decay_half_life=None, decay_bins: int = 10) -> dict:
    """
    k-NN counts/ratios for individual-level rows, returned row-aligned.

    Parameters
    ----------
    x, y      : 1-D arrays of metric coordinates (one row = one
                individual or one weighted record).
    k_values  : list of k thresholds (optional if r_values given).
    r_values  : optional metric radii -> N_r<r>, T_<v>_r<r>, R_<v>_r<r>.
    treat     : {name: 1-D array} of numeric treatment variables
                (0/1 per individual, or counts if weighted rows).
    weight    : optional 1-D array - population represented by each
                row (default 1 per row).
    unit_size : grid size in metres.

    Returns
    -------
    dict {column_name: 1-D float array, same length as x} with, per k:
      N_<k>, Dist_<k>, and per treatment v: T_<v>_<k>, R_<v>_<k>.
    Rows with missing coordinates get NaN throughout.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n_rows = len(x)
    treat = treat or {}
    w = (np.ones(n_rows) if weight is None
         else np.asarray(weight, dtype=float))

    df = pd.DataFrame({"_x": x, "_y": y, "_w": w})
    for name, arr in treat.items():
        df[name] = np.asarray(arr, dtype=float)
    # Two conventions, explicit since v1.14.1 (the ArcGIS field-test
    # bug): treat_are_counts=False (legacy, Stata) -> treat is a 0/1
    # FLAG on a weighted row, contribution = flag * weight.
    # treat_are_counts=True (GIS door) -> treat IS the group's person
    # COUNT at the point; weight is the TOTAL count; no multiplication.
    for name in treat:
        if not treat_are_counts:
            df[name] = df[name] * df["_w"]
    if treat_are_counts and weight is not None:
        for name in treat:
            over = int((df[name] > df["_w"]).sum())
            if over:
                print(f"[bridge] WARNING: '{name}' exceeds the "
                      f"population at {over} points - group counts "
                      "larger than totals is a data error.")

    valid = df["_x"].notna() & df["_y"].notna()
    dv = df[valid]

    # individuals -> cells (weights become cell population)
    cells = dv.copy()
    half = unit_size / 2.0
    cells["_E"] = (np.floor(cells["_x"] / unit_size) * unit_size
                   + half).astype(np.int64)
    cells["_N"] = (np.floor(cells["_y"] / unit_size) * unit_size
                   + half).astype(np.int64)
    agg = {"_w": "sum", **{v: "sum" for v in treat}}
    g = cells.groupby(["_E", "_N"], as_index=False).agg(agg)

    from .cells import CellData
    cd = CellData(E=g["_E"].to_numpy(), N=g["_N"].to_numpy(),
                  n=g["_w"].to_numpy(),
                  binary_sums={v: g[v].to_numpy(float) for v in treat},
                  value_arrays={}, unit_size=unit_size)
    k_values = sorted(k_values or [])
    r_values = sorted(r_values or [])
    if treat and weight is None and not treat_are_counts:
        for _v, _a in treat.items():
            _fin = _a[np.isfinite(_a)]
            if len(_fin) and np.nanmax(_fin) > 1:
                print(f"[bridge] HINT: group '{_v}' holds COUNTS "
                      "(values > 1) but no population/weight field is "
                      "set - N will count ROWS while T sums persons, "
                      "so shares can exceed 1. Set the Population "
                      "field (weight) to the total-persons column.")
                break
    bin_frames = bin_of_row = None
    if decay is not None and decay_half_life is not None:
        bin_frames, bin_of_row, base = _binned_decay_counts(
            cd, cells, k_values, r_values, decay, decay_half_life,
            decay_bins, decay_eps, m_neighbors, n_rows, valid)
        res = base.reset_index()
    else:
        res = run_knn_counts(cd, k_values, decay_eps=decay_eps,
                             m_neighbors=m_neighbors,
                             r_values=r_values, decay=decay)

    # map cell results back to every individual row
    res = res.set_index(["EastWest", "NorthSouth"])
    keys = list(zip(cells["_E"], cells["_N"]))
    labs = [f"r{r:g}" for r in r_values]
    out_cols = ([f"N_{k}" for k in k_values + labs]
                + [f"Dist_{k}" for k in k_values]
                + [f"T_{v}_{k}" for v in treat for k in k_values + labs]
                + [f"R_{v}_{k}" for v in treat for k in k_values + labs])
    if decay is not None:                    # unbounded decayed sums
        out_cols += [c for c in ("ND_inf",)
                     + tuple(f"TD_{v}_inf" for v in treat)
                     + tuple(f"RD_{v}_inf" for v in treat)
                     if c in res.columns]
    out = {}
    vidx = np.flatnonzero(valid.to_numpy())
    decay_cols = {c for c in out_cols
                  if c.endswith("_inf") or c == "ND_inf"}
    for c in out_cols:
        col = np.full(n_rows, np.nan)
        if bin_frames is not None and c in decay_cols:
            # each row reads the pass run with ITS OWN bandwidth
            vals = np.full(len(vidx), np.nan)
            for b, frame in enumerate(bin_frames):
                m = bin_of_row == b
                if not m.any():
                    continue
                kk = [keys[i] for i in np.flatnonzero(m)]
                vals[m] = frame.loc[kk, c].to_numpy(dtype=float)
            col[vidx] = vals
        else:
            col[vidx] = res.loc[keys, c].to_numpy(dtype=float)
        out[c] = col
    n_miss = n_rows - len(vidx)
    if n_miss:
        print(f"[stata] {n_miss} rows with missing coordinates -> "
              f"missing results")
    print(f"[stata] returning {len(out)} new variables for "
          f"{n_rows} observations")
    return out


# =====================================================================
# #17 - THE DISPATCHER: one row-alignment layer for every engine.
# dispatch(engine, x, y, ...) -> dict of row-aligned arrays, so the
# single ado equipop_run.ado can expose the whole toolbox to Stata.
# =====================================================================

def _snap(x, y, unit):
    half = unit / 2.0
    E = (np.floor(np.asarray(x, float) / unit) * unit + half)
    N = (np.floor(np.asarray(y, float) / unit) * unit + half)
    return E.astype(np.int64), N.astype(np.int64)


def _map_back(res, keys, cols, valid, n_rows):
    """Cell-level frame -> row-aligned dict (NaN for invalid rows)."""
    res = res.set_index(["EastWest", "NorthSouth"]) \
        if "EastWest" in res.columns else res.set_index(["x", "y"])
    vidx = np.flatnonzero(valid)
    out = {}
    for c in cols:
        col = np.full(n_rows, np.nan)
        col[vidx] = res.loc[keys, c].to_numpy(dtype=float)
        out[c] = col
    return out


def dispatch(engine: str, x, y, unit_size: float = 100.0,
             treat: dict | None = None, weight=None,
             k_values=None, r_values=None, tau_values=None,
             # stats engine:
             values: dict | None = None, stats: dict | None = None,
             # slope / friction:
             dem: str | None = None, model: str = "tobler",
             roundtrip: bool = False, friction_file: str | None = None,
             # fca:
             supply_file: str | None = None, demand_arr=None,
             supply_x: str = "x", supply_y: str = "y",
             supply_col: str = "supply", half_life_m: float | None = None,
             reach: str = "decay", method: str = "2sfca",
             k_fca: float | None = None, r_fca: float | None = None,
             decay_eps: float = 1e-6,
             half_life_field=None, half_life_from_dist=None,
             decay_bins: int = 10,
             **extra) -> dict:
    """
    One entry point, five engines, row-aligned results:

    engine="counts"   -> knn_to_rows (k/r, multiple treatments, weight)
    engine="stats"    -> run_knn_stats (values+stats dicts, k/r)
    engine="friction" -> run_knn_friction (k/tau, one treat, fr file)
    engine="slope"    -> run_knn_slope (k/tau, DEM, model, roundtrip)
    engine="fca"      -> fca (demand = the rows; supply from a FILE;
                         returns A and J mapped to rows)

    Everything computable is here (pytest-covered); the ado only moves
    arrays over sfi and calls this.
    """
    x = np.asarray(x, float); y = np.asarray(y, float)
    n_rows = len(x)
    valid = np.isfinite(x) & np.isfinite(y)

    if engine == "counts":
        dec = None
        if half_life_m or half_life_field is not None \
                or half_life_from_dist:
            from .decay import Decay
            # with a variable bandwidth the half-life here is only a
            # placeholder - every bin builds its own kernel
            dec = Decay(model=extra.get("decay_model", "negexp"),
                        half_life_m=float(half_life_m or 1000.0),
                        gamma=extra.get("gamma"))
        hl = half_life_field
        if hl is None and half_life_from_dist and dec is not None:
            # SELF-CALIBRATING bandwidth (v1.17): each row's own
            # Dist_k - the radius it needed to gather k persons -
            # becomes its half-life, so urban form sets the
            # bandwidth instead of an assumed distance. Computed by a
            # plain k-run first, then fed back as the kernel.
            k0 = int(half_life_from_dist)
            first = knn_to_rows(x, y, [k0], weight=weight,
                                unit_size=unit_size,
                                treat_are_counts=extra.get(
                                    "treat_are_counts", False))
            hl = first[f"Dist_{k0}"]
            good = np.isfinite(hl) & (hl > 0)
            if not good.any():
                raise ValueError(
                    f"[decay] self-calibration needs Dist_{k0}, but no "
                    "row got a usable radius")
            hl = np.where(good, hl, np.nanmedian(hl[good]))
            print(f"[decay] self-calibrated bandwidth from Dist_{k0}: "
                  f"{np.nanmin(hl):,.0f}-{np.nanmax(hl):,.0f} m "
                  f"(median {np.nanmedian(hl):,.0f} m)")
        return knn_to_rows(x, y, k_values, treat=treat, weight=weight,
                           unit_size=unit_size, r_values=r_values,
                           decay=dec, decay_eps=decay_eps,
                           decay_half_life=hl, decay_bins=decay_bins,
                           treat_are_counts=extra.get(
                               "treat_are_counts", False))

    if engine == "stats":
        from .analysis import run_knn_stats
        values = values or {}
        df = pd.DataFrame({"_x": x, "_y": y})
        for v, arr in values.items():
            a = np.asarray(arr, float)
            a = np.where(a > 8.9e307, np.nan, a)
            df[v] = a
        if weight is not None:
            # v1.16 FULL-POPULATION field: each row carries this many
            # persons; k is measured against PERSONS, and every value
            # statistic weights by population - implemented EXACTLY by
            # expanding rows to persons (median/Gini/percentiles come
            # out weighted by construction). Rows with missing or
            # non-positive population are excluded (Null results).
            w = np.asarray(weight, float)
            w = np.where(w > 8.9e307, np.nan, w)
            rep = np.where(np.isfinite(w) & (w > 0),
                           np.round(w), 0).astype(np.int64)
            valid = valid & (rep > 0)
            df["_rep"] = rep
        dv = df[valid]
        E, N = _snap(dv["_x"], dv["_y"], unit_size)   # per INPUT row
        if weight is not None:
            n_persons = int(dv["_rep"].sum())
            skipped = len(df) - len(dv)
            print(f"[stata] full population: {len(dv)} of {len(df)} "
                  f"rows carry a usable count -> {n_persons} persons "
                  f"(k counts PERSONS)")
            if skipped:
                print(f"[stata] {skipped} row(s) have no count (empty "
                      "or zero) and take no part in the k-search - "
                      "they still receive their own results")
            dv = dv.loc[dv.index.repeat(dv["_rep"])] \
                   .drop(columns="_rep").reset_index(drop=True)
        cd = build_cells(dv, "_x", "_y", value_vars=list(values),
                         unit_size=unit_size)
        st = run_knn_stats(cd, k_values=k_values, r_values=r_values,
                           stats=stats or {v: ["mean", "median", "gini"]
                                           for v in values})
        from .stats import stat_prefix
        req = stats or {v: ["mean", "median", "gini"] for v in values}
        allowed = {"N", "Nv", "Dist"} | {
            stat_prefix(s) for ss in req.values() for s in ss}
        cols = [c for c in st.columns
                if c.split("_")[0] in allowed]
        return _map_back(st, list(zip(E, N)), cols, valid, n_rows)

    if engine in ("friction", "slope"):
        from .io import read_table, resolve_xy_columns
        w = np.ones(n_rows) if weight is None else np.asarray(weight,
                                                              float)
        counts_mode = extra.pop("treat_are_counts", False)
        fr = friction_file
        if isinstance(fr, str) and fr:
            fr = read_table(fr)
        if fr is not None:
            fr = resolve_xy_columns(fr, context="barrier table")
            if "friction" not in fr.columns:
                cand = [c for c in fr.columns
                        if c.lower().startswith("frict")
                        or c.lower() in ("cost", "value", "weight")]
                if not cand:
                    raise ValueError(
                        "[bridge] barrier table needs a friction "
                        f"value column - found {list(fr.columns)}")
                print(f"[bridge] barrier table: using '{cand[0]}' "
                      "as friction")
                fr = fr.rename(columns={cand[0]: "friction"})
        groups = (list(treat.items()) if treat
                  else [(None, np.zeros(n_rows))])
        E = N = None
        merged = None
        for gname, garr in groups:
            tr = np.asarray(garr, float)
            cg = np.where(tr > 8.9e307, 0, tr)
            if not counts_mode:
                cg = cg * w
            df = pd.DataFrame({"x": x, "y": y, "count_all": w,
                               "count_group": cg})
            dv = df[valid]
            if E is None:
                E, N = _snap(dv["x"], dv["y"], unit_size)
            pop = (dv.assign(x=E.astype(float), y=N.astype(float))
                   .groupby(["x", "y"], as_index=False).sum())
            if engine == "slope":
                from .slope import run_knn_slope
                res = run_knn_slope(pop, k_values or [], altitude=dem,
                                    model=model, fr=fr,
                                    unit_size=unit_size,
                                    tau_values=tau_values,
                                    roundtrip=roundtrip, **extra)
            else:
                from .friction import run_knn_friction
                res = run_knn_friction(pop, k_values or [], fr=fr,
                                       unit_size=unit_size,
                                       tau_values=tau_values)
            if gname is not None:
                res = res.rename(columns={
                    c: (f"T_{gname}_{c[2:]}" if c.startswith("T_")
                        else f"R_{gname}_{c[2:]}")
                    for c in res.columns
                    if c.startswith(("T_", "R_"))})
            if merged is None:
                merged = res
            else:
                # v1.26.1: a run with NO treatment produces no T_/R_
                # columns at all, so take only what is actually there
                keep = [c for c in res.columns
                        if c.startswith(("T_", "R_"))
                        and c in res.columns]
                key = res.columns[:2].tolist()
                if keep:
                    merged = merged.merge(res[key + keep], on=key)
        cols = [c for c in merged.columns if c.split("_")[0]
                in ("N", "T", "R", "Dist", "Rounds")]
        return _map_back(merged, list(zip(E, N)), cols, valid, n_rows)

    if engine == "fca":
        from .fca import fca
        from .decay import Decay
        try:
            from .io import read_table
            sup = read_table(supply_file)
        except Exception:
            sup = (pd.read_csv(supply_file) if supply_file.endswith(".csv")
                   else pd.read_stata(supply_file))
        sup = sup.rename(columns={supply_x: "x", supply_y: "y"})
        d_arr = np.asarray(demand_arr, float)
        d_arr = np.where(d_arr > 8.9e307, np.nan, d_arr)
        df = pd.DataFrame({"x": x, "y": y, "_D": d_arr})
        ok = valid & np.isfinite(df["_D"])
        dv = df[ok]
        E, N = _snap(dv["x"], dv["y"], unit_size)
        dem_cells = (dv.assign(x=E.astype(float), y=N.astype(float))
                     .groupby(["x", "y"], as_index=False).sum())
        dec = (Decay(model="negexp", half_life_m=half_life_m)
               if half_life_m else None)
        d_out, _ = fca(dem_cells, sup, "_D", supply_col, decay=dec,
                       reach=reach, method=method, k=k_fca, r=r_fca)
        return _map_back(d_out, list(zip(E, N)), ["A", "J"],
                         ok.to_numpy() if hasattr(ok, "to_numpy") else ok,
                         n_rows)

    if engine == "lisa":
        from .autocorr import build_weights, local_morans
        vals = values or {}
        if len(vals) != 1:
            raise ValueError("engine='lisa' wants exactly one value "
                             "column in values=")
        vname, arr = next(iter(vals.items()))
        a = np.asarray(arr, float)
        a = np.where(a > 8.9e307, np.nan, a)
        df = pd.DataFrame({"x": x, "y": y, "v": a})
        ok = valid & np.isfinite(df["v"])
        dv = df[ok]
        E, N = _snap(dv["x"], dv["y"], unit_size)
        cells = (dv.assign(E=E, N=N).groupby(["E", "N"], as_index=False)
                 .agg(v=("v", "mean"), n=("v", "size")))
        if (cells["n"] > 1).any():
            print(f"[stata] {int((cells.n > 1).sum())} cells hold "
                  "several rows - LISA runs on CELL MEANS (loudly)")
        W = build_weights(cells["E"], cells["N"], mode="knn",
                          k=int(extra.get("w_k", 8)))
        res = local_morans(cells["v"], W,
                           permutations=int(extra.get("permutations",
                                                      199)))
        res["quadcode"] = res["quad"].map(
            {"HH": 1, "LL": 2, "HL": 3, "LH": 4}).astype(float)
        res["EastWest"] = cells["E"].to_numpy()
        res["NorthSouth"] = cells["N"].to_numpy()
        out = _map_back(res, list(zip(E, N)),
                        ["Ii", "quadcode", "p"], ok.to_numpy()
                        if hasattr(ok, "to_numpy") else ok, n_rows)
        return {f"LISA_{vname}_Ii": out["Ii"],
                f"LISA_{vname}_quad": out["quadcode"],
                f"LISA_{vname}_p": out["p"]}

    raise ValueError(f"unknown engine '{engine}' - use counts / stats "
                     "/ friction / slope / fca / lisa")
