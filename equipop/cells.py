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
    # BACKLOG 168. Persons in the cell whose value for that variable
    # is USABLE. Equal to `n` unless missing codes were declared, so
    # nothing moves for anyone not using them. It exists because of
    # John's ruling: a share is estimated from the part that was
    # OBSERVED, not diluted by cases whose value nobody knows. Of 400
    # people with 60 of unknown group the denominator is 340, never
    # 400 - dividing by 400 quietly assumes those 60 were not in the
    # group.
    binary_valid: dict = field(default_factory=dict)  # var -> array (m,)
    value_arrays: dict = field(default_factory=dict)  # var -> list of arrays
    # BACKLOG 118, v1.41. Optional per-entry WEIGHTS alongside
    # value_arrays: var -> list of arrays, one weight per value.
    # EMPTY unless build_cells(weights=...) was given something, so
    # every existing caller is untouched and every existing answer is
    # unchanged - when it is empty the engine counts entries, exactly
    # as it always has.
    # It exists because WorldPop counts are FRACTIONAL. The old route
    # into a weighted statistic was to REPEAT each row `weight` times,
    # and you cannot repeat somebody 0.4 times: np.round() sent that
    # cell to zero and dropped it from the population. Measured on
    # John's rasters, that deleted 50.5% of the people - 39% in
    # Rwanda, 69% in Denmark, so the loss grew with latitude and any
    # Europe-against-Africa comparison was biased by construction.
    value_weights: dict = field(default_factory=dict)  # var -> list of arrays
    unit_size: float = 100.0
    labels: list | None = None    # optional per-cell ID/label (e.g. place, year)

    def __len__(self):
        return len(self.n)

    def valid_for(self, v):
        """Persons whose value for `v` is usable, per cell.

        BACKLOG 168. Falls back to the full population when nothing
        was declared missing - which is every CellData built before
        1.32 and every run without missing codes - so the denominator
        is unchanged unless the user asked for it to change.
        """
        got = self.binary_valid.get(v)
        return self.n.astype(float) if got is None else got


def build_cells(
    df: pd.DataFrame,
    e_col: str,
    n_col: str,
    binary_vars: list[str] | None = None,
    value_vars: list[str] | None = None,
    unit_size: float = 100.0,
    snap: bool = True,
    label_col: str | None = None,
    missing_codes=None,
    weights: str | None = None,
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
    # BACKLOG 168, John's ruling: a declared code IS missing.
    #
    # "The sentinels are likely what I would refer to as missing
    # values that have representations (usually different depending
    # on the cause for missing) - the cause is unimportant, but the
    # possibility to dismiss/exclude those values would be of
    # importance."
    #
    # So the codes are converted HERE, at the door, and every path
    # downstream already knows what missing means. No new concept
    # reaches the engines - which is the whole design, because the
    # engines are where a new concept would be expensive to trust.
    #
    # Not cosmetic: John's Bristol County extract carries the Census
    # sentinel -666666666 in 64 of 1074 rows for median household
    # income. Left alone a neighbourhood mean lands near minus forty
    # million, and it lands there quietly.
    if missing_codes:
        codes = [float(c) for c in missing_codes]
        for v in list(value_vars) + list(binary_vars):
            if v not in df.columns:
                continue
            col = pd.to_numeric(df[v], errors="coerce")
            hit = col.isin(codes)
            if bool(hit.any()):
                print(f"[cells] '{v}': {int(hit.sum())} values matched "
                      f"a declared missing code - those cases still "
                      "count as people towards k and still receive "
                      "results, but contribute nothing of their own.")
            df[v] = col.where(~hit)

    for v in value_vars:
        miss = df[v].isna().sum()
        if miss:
            print(f"[cells] note: '{v}' has {miss} missing values - these "
                  f"individuals count towards k but not towards {v} statistics.")

    # --- aggregate ---
    groups = df.groupby(["_E", "_N"], sort=True)
    E, N, n = [], [], []
    bsums = {v: [] for v in binary_vars}
    bvalid = {v: [] for v in binary_vars}
    varrs = {v: [] for v in value_vars}
    vwts = {v: [] for v in value_vars} if weights is not None else {}
    labels = [] if label_col else None
    mixed = 0

    for (e, nn), g in groups:
        E.append(e)
        N.append(nn)
        n.append(float(g[weights].sum()) if weights is not None else len(g))
        for v in binary_vars:
            if weights is None:
                bsums[v].append(g[v].sum())
                bvalid[v].append(int(g[v].notna().sum()))
            else:
                w = g[weights]
                bsums[v].append(float((g[v].fillna(0) * w).sum()))
                bvalid[v].append(float(w[g[v].notna()].sum()))
        for v in value_vars:
            keep = g[v].notna()
            varrs[v].append(g.loc[keep, v].to_numpy(dtype=float))
            if weights is not None:
                vwts[v].append(g.loc[keep, weights].to_numpy(dtype=float))
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
        n=np.array(n, dtype=float if weights is not None else np.int64),
        binary_sums={v: np.array(a, dtype=float) for v, a in bsums.items()},
        binary_valid={v: np.array(a, dtype=float)
                      for v, a in bvalid.items()},
        value_arrays=varrs,
        value_weights=vwts,
        unit_size=unit_size,
        labels=labels,
    )
    print(f"[cells] {len(df)} individuals -> {len(cd)} cells "
          f"(unit {unit_size} m, global N = {cd.n.sum()})")
    return cd


def auto_m_neighbors(cd, k_values=None, r_values=None,
                     safety: float = 3.0,
                     trunc_m: float = 0.0) -> int:
    """How many nearest CELLS an origin must fetch to satisfy the
    largest k (or radius) - the tuning knob of the fast engines
    (v1.16.3). Under-estimates are harmless: both engines recompute
    such origins exactly, so this affects SPEED ONLY.

    k needs k/mean_persons_per_cell cells; a radius needs the cells
    inside its disc at the observed cell density.
    """
    n_cells = len(cd)
    if n_cells <= 64:
        return n_cells
    mean_n = max(float(np.sum(cd.n)) / n_cells, 1e-9)
    need = max((float(k) / mean_n for k in (k_values or [])),
               default=0.0)
    if r_values or trunc_m:
        e, n = np.asarray(cd.E, float), np.asarray(cd.N, float)
        area = max((e.max() - e.min()) * (n.max() - n.min()),
                   float(cd.unit_size) ** 2)
        dens = n_cells / area                      # cells per m^2
        for r in (list(r_values or []) + ([trunc_m] if trunc_m else [])):
            # a DECAYED sum must reach its truncation distance, which
            # is usually far beyond what k needs - ignoring it made
            # every origin climb the ladder twice (field-test v1.16.5)
            need = max(need, np.pi * float(r) ** 2 * dens)
    return int(min(n_cells, max(64, round(safety * need))))
