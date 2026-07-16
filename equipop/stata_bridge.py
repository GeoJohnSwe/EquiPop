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
