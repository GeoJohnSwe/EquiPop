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

import hashlib

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
    # BACKLOG 158. WHAT SHAPE THE CELLS ARE, because `unit_size` alone
    # does not say: it is a square's SIDE and a hexagon's WIDTH ACROSS
    # FLATS, and those enclose different areas. The self-potential
    # radius is area-based, so hex cells were being charged a square's
    # 10,000 m2 where they hold 8,660 - a 7.46% overstatement that
    # nothing could see, because the number arrived through a field
    # named for a length. Defaults to "square", which is every caller
    # before 1.52 and an exact identity for them. See selfpot.SHAPES.
    cell_shape: str = "square"
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

    def fingerprint(self) -> str:
        """A short digest of the DATA this table holds.

        BACKLOG 344, external review of 1.51 (finding F3). A resumable
        run has to answer one question before it skips any finished
        work: is the data on disk the data being asked about? Counting
        cells cannot answer it. Reproduced on two 9-cell tables with
        identical geometry and different populations - 10 people per
        cell, then 20 - where resuming the second against the first's
        folder returned the FIRST run's numbers, reported success, and
        left a manifest whose recorded parameters matched perfectly,
        because `n_cells` and `unit_size` were all it recorded. A
        three-day continental run is exactly where nobody will notice.

        Everything the counting engine reads goes in: the coordinates,
        the population, and each treatment's totals and observed
        denominators - in a fixed order, as raw little-endian float64
        bytes, so the digest does not depend on dict ordering or on
        how the arrays were typed. VALUE ARRAYS ARE NOT INCLUDED: the
        counts engine never reads them, and hashing a per-person list
        at continental scale would cost more than the run it guards.
        Any future engine that reads them owes this method a line.
        """
        h = hashlib.md5()
        h.update(f"equipop-cells-1|{float(self.unit_size)!r}|"
                 f"{len(self.n)}".encode())
        for arr in (self.E, self.N, self.n):
            h.update(np.ascontiguousarray(arr, dtype="<f8").tobytes())
        for bag_name, bag in (("binary_sums", self.binary_sums),
                              ("binary_valid", self.binary_valid)):
            for v in sorted(bag):
                h.update(f"|{bag_name}|{v}|".encode())
                h.update(np.ascontiguousarray(bag[v],
                                              dtype="<f8").tobytes())
        if self.labels is not None:
            h.update(b"|labels|")
            h.update("\x1f".join("" if x is None else str(x)
                                 for x in self.labels).encode())
        return h.hexdigest()


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

    # --- the WEIGHT column, BACKLOG 343 ---
    # A weight is a number of people, so it is coerced like every
    # other number and judged before anything sums it. Two silent
    # failures this closes: a weight column arriving as text summed to
    # nonsense or to zero, and a blank or negative weight reaching
    # `value_weights`, where np.bincount turns one NaN into a NaN
    # statistic for every neighbourhood that touches the cell. Blank
    # means NOBODY (John's rule since 1.22.2 - the row still gets its
    # own results); negative means a sentinel nobody declared, and
    # that is refused rather than quietly read as a population.
    if weights is not None:
        if weights not in df.columns:
            raise ValueError(
                f"[cells] weights='{weights}' is not a column - found "
                f"{list(df.columns)}")
        wv = pd.to_numeric(df[weights], errors="coerce")
        neg = wv < 0
        if bool(neg.any()):
            # BACKLOG 351. Same two causes as the bridge's
            # validate_weight, named in the same order, because this
            # is the other door onto the same mistake - rasterfolder
            # hands a raster's own column straight in, and a raster's
            # NoData is frequently -9999.
            raise ValueError(
                f"[cells] '{weights}' goes down to {float(wv.min()):g} "
                f"at {int(neg.sum())} row(s), and k counts PEOPLE, so "
                f"a neighbourhood cannot be grown against a negative "
                f"population.\n"
                f"  NO DATA: blank it, or declare it as a missing code "
                f"- those rows then hold nobody and still get their "
                f"own results.\n"
                f"  A CHANGE or net migration, legitimately negative: "
                f"that is a MEASUREMENT, not a population. Pass it as "
                f"a value_vars column and keep the headcount in "
                f"weights=.")
        blank = ~np.isfinite(wv)
        if bool(blank.any()):
            print(f"[cells] note: '{weights}' is missing at "
                  f"{int(blank.sum())} of {len(df)} rows - those rows "
                  f"hold nobody, are nobody's neighbour, and still get "
                  f"their own results.")
        df[weights] = wv.where(~blank, 0.0)

    # --- missing coordinates: drop with warning (spec 12) ---
    # BACKLOG 381, v1.53.3. This said `.isna()`, which is True only for
    # NaN and None. An INFINITE or non-numeric coordinate passed it and
    # reached the .astype(int) twelve lines below, where pandas refuses
    # with "Cannot convert non-finite values (NA or inf) to integer ...
    # cast to Int64" - a message about pandas dtypes handed to somebody
    # who typed a coordinate. The ANSWER was never wrong, but the voice
    # was not EquiPop's.
    # The right predicate was already in this function, eight lines
    # above, on the weight column: `blank = ~np.isfinite(wv)`.
    # A NON-NUMERIC coordinate is NOT this release's fix: the loop at
    # the top of this function already runs to_numeric(errors=
    # "coerce") over both coordinate columns, so text has become NaN
    # long before here. The first draft of this change re-coerced them
    # and a test claimed credit for behaviour that predates it - the
    # break-check is what exposed that, by removing the new coercion
    # and watching the test pass anyway.
    bad = pd.Series(~(np.isfinite(df[e_col].to_numpy(float))
                      & np.isfinite(df[n_col].to_numpy(float))),
                    index=df.index)
    if bad.any():
        print(f"[cells] WARNING: {bad.sum()} of {len(df)} rows have "
              f"missing or non-finite coordinates and are dropped.")
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
    if r_values:
        e, n = np.asarray(cd.E, float), np.asarray(cd.N, float)
        area = max((e.max() - e.min()) * (n.max() - n.min()),
                   float(cd.unit_size) ** 2)
        dens = n_cells / area                      # cells per m^2
        for r in r_values:
            need = max(need, np.pi * float(r) ** 2 * dens)
    # BACKLOG 307. `trunc_m` USED TO BE IN THAT LOOP, sizing the
    # window to the decay TRUNCATION RADIUS on the reasoning that "a
    # DECAYED sum must reach its truncation distance". That was true
    # until BACKLOG 185 removed the unbounded sums (ND_inf and its
    # siblings) in v1.40: the decayed totals are now accumulated to
    # THE RAW k OR RADIUS, exactly like the plain ones, so nothing
    # reads past k any more.
    #
    # The deferral test in fastcounts was corrected then. THIS WAS
    # NOT, so every decay run still fetched a window sized for a
    # distance it would never look at. On LA County at half-life
    # 2000 m and eps 1e-3 the truncation radius is about 20 km, and
    # the window came out at 11,159 cells where 697 satisfied k=800 -
    # 138 seconds against 14, all of it fetching neighbours nobody
    # would read.
    #
    # Found by John, who asked why a decay run's TIME should depend on
    # the half-life at all when the neighbourhood is fixed by k. It
    # should not, and now it does not.
    _ = trunc_m                       # kept in the signature: callers
                                      # pass it, and a decayed run may
                                      # want it again if an unbounded
                                      # sum ever returns.
    return int(min(n_cells, max(64, round(safety * need))))
