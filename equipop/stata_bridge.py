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


def knn_to_rows(x, y, k_values=None, treat: dict | None = None,
                weight=None, unit_size: float = 100.0,
                m_neighbors: int = 4096,
                r_values=None) -> dict:
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
    # treatment contribution = value * weight (0/1 * 1 in the plain case)
    for name in treat:
        df[name] = df[name] * df["_w"]

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
    res = run_knn_counts(cd, k_values, m_neighbors=m_neighbors,
                         r_values=r_values)

    # map cell results back to every individual row
    res = res.set_index(["EastWest", "NorthSouth"])
    keys = list(zip(cells["_E"], cells["_N"]))
    labs = [f"r{r:g}" for r in r_values]
    out_cols = ([f"N_{k}" for k in k_values + labs]
                + [f"Dist_{k}" for k in k_values]
                + [f"T_{v}_{k}" for v in treat for k in k_values + labs]
                + [f"R_{v}_{k}" for v in treat for k in k_values + labs])
    out = {}
    vidx = np.flatnonzero(valid.to_numpy())
    for c in out_cols:
        col = np.full(n_rows, np.nan)
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
        return knn_to_rows(x, y, k_values, treat=treat, weight=weight,
                           unit_size=unit_size, r_values=r_values)

    if engine == "stats":
        from .analysis import run_knn_stats
        values = values or {}
        df = pd.DataFrame({"_x": x, "_y": y})
        for v, arr in values.items():
            a = np.asarray(arr, float)
            a = np.where(a > 8.9e307, np.nan, a)
            df[v] = a
        dv = df[valid]
        cd = build_cells(dv, "_x", "_y", value_vars=list(values),
                         unit_size=unit_size)
        st = run_knn_stats(cd, k_values=k_values, r_values=r_values,
                           stats=stats or {v: ["mean", "median", "gini"]
                                           for v in values})
        E, N = _snap(dv["_x"], dv["_y"], unit_size)
        cols = [c for c in st.columns
                if c.split("_")[0] in ("N", "Nv", "Dist", "Mean", "Med",
                                       "Gini", "SD", "SE", "R", "T")]
        return _map_back(st, list(zip(E, N)), cols, valid, n_rows)

    if engine in ("friction", "slope"):
        from .io import read_table
        tr = (np.zeros(n_rows) if not treat
              else np.asarray(next(iter(treat.values())), float))
        w = np.ones(n_rows) if weight is None else np.asarray(weight, float)
        df = pd.DataFrame({"x": x, "y": y, "count_all": w,
                           "count_group": np.where(tr > 8.9e307, 0, tr) * w})
        dv = df[valid]
        E, N = _snap(dv["x"], dv["y"], unit_size)
        pop = (dv.assign(x=E.astype(float) , y=N.astype(float))
               .groupby(["x", "y"], as_index=False).sum())
        fr = read_table(friction_file) if friction_file else None
        if engine == "slope":
            from .slope import run_knn_slope
            res = run_knn_slope(pop, k_values or [], altitude=dem,
                                model=model, fr=fr, unit_size=unit_size,
                                tau_values=tau_values,
                                roundtrip=roundtrip, **extra)
        else:
            from .friction import run_knn_friction
            res = run_knn_friction(pop, k_values or [], fr=fr,
                                   unit_size=unit_size,
                                   tau_values=tau_values)
        cols = [c for c in res.columns if c.split("_")[0]
                in ("N", "T", "R", "Dist", "Rounds")]
        return _map_back(res, list(zip(E, N)), cols, valid, n_rows)

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

    raise ValueError(f"unknown engine '{engine}' - use counts / stats "
                     "/ friction / slope / fca")
