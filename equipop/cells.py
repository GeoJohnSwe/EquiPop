"""
cells.py - build cell-level data from INDIVIDUAL-level rows.

This is the entry point for "tier 3" data: one row per individual,
where several individuals may share the same coordinate. The builder
aggregates them into grid cells while keeping, per cell:

  - n            : the individual count (this is what k counts!)
  - binary sums  : one running sum per binary variable (0/1)
  - value arrays : the raw individual values per continuous variable
                   (needed for exact median / Gini at k-level)

Missing handling (spec section 12):
  - rows with missing coordinates are DROPPED with a printed warning
  - missing values in a continuous variable: the individual still
    counts towards k, but contributes no value to that variable's
    statistics (a separate valid-n is reported as Nv_<var>_<k>)
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field


@dataclass
class CellData:
    """Aggregated per-cell data ready for run_knn_stats()."""
    E: np.ndarray                 # cell midpoint eastings  (m cells)
    N: np.ndarray                 # cell midpoint northings
    n: np.ndarray                 # individuals per cell
    binary_sums: dict = field(default_factory=dict)   # var -> array (m,)
    value_arrays: dict = field(default_factory=dict)  # var -> list of arrays
    unit_size: float = 100.0
    labels: list | None = None    # optional per-cell ID/label (e.g. place, year)

    def __len__(self):
        return len(self.n)


def build_cells(
    df: pd.DataFrame,
    e_col: str,
    n_col: str,
    binary_vars: list[str] | None = None,
    value_vars: list[str] | None = None,
    unit_size: float = 100.0,
    snap: bool = True,
    label_col: str | None = None,
) -> CellData:
    """
    Aggregate an individual-level DataFrame into CellData.

    Parameters
    ----------
    df : one row per individual.
    e_col, n_col : METRIC coordinate columns (already projected).
    binary_vars : 0/1 columns (each becomes a treatment with exact
                  count-based statistics).
    value_vars : continuous columns (individual values are stored
                 per cell for exact median/Gini/etc.).
    unit_size : grid size in metres.
    snap : snap coordinates to grid midpoints. Idempotent - if the
           data is already midpoint-snapped (like 100m register data
           ending in ...50), snapping changes nothing.
    label_col : optional ID column carried through to the output
           (e.g. a place code or a year). If a cell contains SEVERAL
           distinct labels they are joined with '|' and a warning is
           printed - a good ID should be constant within a cell.
    """
    binary_vars = binary_vars or []
    value_vars = value_vars or []
    df = df.copy()

    # --- coerce to numeric; blanks become NaN ---
    for c in [e_col, n_col] + binary_vars + value_vars:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # --- missing coordinates: drop with warning (spec 12) ---
    bad = df[e_col].isna() | df[n_col].isna()
    if bad.any():
        print(f"[cells] WARNING: {bad.sum()} of {len(df)} rows have "
              f"missing coordinates and are dropped.")
        df = df[~bad]

    # --- snap to grid midpoints ---
    if snap:
        half = unit_size / 2.0
        df["_E"] = (np.floor(df[e_col] / unit_size) * unit_size + half).astype(int)
        df["_N"] = (np.floor(df[n_col] / unit_size) * unit_size + half).astype(int)
    else:
        df["_E"] = df[e_col].astype(int)
        df["_N"] = df[n_col].astype(int)

    # --- report missing values in analysis variables ---
    for v in value_vars:
        miss = df[v].isna().sum()
        if miss:
            print(f"[cells] note: '{v}' has {miss} missing values - these "
                  f"individuals count towards k but not towards {v} statistics.")

    # --- aggregate ---
    groups = df.groupby(["_E", "_N"], sort=True)
    E, N, n = [], [], []
    bsums = {v: [] for v in binary_vars}
    varrs = {v: [] for v in value_vars}
    labels = [] if label_col else None
    mixed = 0

    for (e, nn), g in groups:
        E.append(e)
        N.append(nn)
        n.append(len(g))
        for v in binary_vars:
            bsums[v].append(g[v].sum())
        for v in value_vars:
            varrs[v].append(g[v].dropna().to_numpy(dtype=float))
        if label_col:
            uniq = g[label_col].astype(str).unique()
            if len(uniq) > 1:
                mixed += 1
            labels.append("|".join(sorted(uniq)))

    if label_col and mixed:
        print(f"[cells] WARNING: {mixed} cells contain several distinct "
              f"'{label_col}' values (joined with '|'). A good cell ID "
              f"should be constant within a cell.")

    cd = CellData(
        E=np.array(E, dtype=np.int64),
        N=np.array(N, dtype=np.int64),
        n=np.array(n, dtype=np.int64),
        binary_sums={v: np.array(a, dtype=float) for v, a in bsums.items()},
        value_arrays=varrs,
        unit_size=unit_size,
        labels=labels,
    )
    print(f"[cells] {len(df)} individuals -> {len(cd)} cells "
          f"(unit {unit_size} m, global N = {cd.n.sum()})")
    return cd
