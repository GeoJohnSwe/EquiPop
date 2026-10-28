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
    # BACKLOG 409, v1.57.0. ADDITIVE SUMS: one column per name, one row
    # per cell, each the (weighted) sum of some per-person quantity
    # over the cell's people. run_knn_stats adds them up over each
    # neighbourhood exactly as it adds up the people - a crossing ring
    # contributes the same share of them - and writes the totals as
    # columns `{name}_{k}`. Nothing a user asks for directly reads
    # them: they exist so that a between/within split costs four sums
    # per group, not a sorted statistic per group (see decompose.py).
    # None unless build_cells(sum_vars=...) was given something, so
    # every other run is untouched.
    sum_matrix: np.ndarray | None = None
    sum_names: list = field(default_factory=list)

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
        h = hashlib.md5(usedforsecurity=False)
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


def exact_coords(a) -> np.ndarray:
    """Coordinates as EXACT numbers: int64 when every value is whole,
    float64 otherwise. Never truncated.

    v1.62.1, external review of 1.62.0. Snapped midpoints were cast
    with .astype(int), which truncates toward ZERO. With an odd cell
    size every midpoint ends in .5, so the cells either side of 0 moved
    in opposite directions: at 1 m, points at -0.25 and +0.25 became
    ONE cell at 0 holding both; at 3 m the two centres were recorded
    2 m apart. Even sizes (100 m, 1 km) have whole midpoints and come
    back as integers exactly as before, so no such run changes.
    """
    a = np.asarray(a, dtype=float)
    r = np.round(a)
    if a.size == 0 or np.array_equal(r, a):
        return r.astype(np.int64)
    return a


def check_unit_size(unit_size) -> float:
    """The cell size as a float: finite and greater than zero, or a
    ValueError in words.

    v1.63.1, BACKLOG 451 (review of 1.63.0). Every door checks the size
    it is given, but the package itself did not: -1 through the bridge
    ran and returned N_1 = 1, Dist_1 = 0 for every row - a plausible
    table on a grid that does not exist - and 0, NaN and infinity
    escaped as a KeyError from deep inside. Checked here, where every
    square grid is built (grid_midpoints), and at the bridge's front
    door, so a Python caller and any future door inherit it."""
    try:
        u = float(unit_size)
    except (TypeError, ValueError):
        raise ValueError(
            f"[cells] the cell size must be a number; got {unit_size!r}"
        ) from None
    if not (np.isfinite(u) and u > 0):
        raise ValueError(
            f"[cells] the cell size must be a finite number greater "
            f"than 0; got {unit_size!r}. It is the width of the grid "
            "the neighbourhoods are built on.")
    return u


def grid_midpoints(v, unit_size) -> np.ndarray:
    """Each value's cell MIDPOINT on a square grid of `unit_size`
    (cells [k*u, (k+1)*u), midpoint k*u + u/2), exact - see
    exact_coords. The one rule every square-grid path uses: build_cells,
    snap_to_grid, the Stata bridge and theta_profile."""
    u = check_unit_size(unit_size)
    v = np.asarray(v, dtype=float)
    return exact_coords(np.floor(v / u) * u + u / 2.0)


def split_sum_name(var: str, code: int) -> str:
    """The name of `var`'s sum over the people with group code `code`
    (build_cells(sum_by=...)). The ONE place this is spelled."""
    return f"{var}#{int(code)}"


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
    sum_vars: list[str] | None = None,
    sum_by: str | None = None,
    sum_levels: int = 0,
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
    sum_vars : columns whose per-cell (weighted) SUMS the engine should
           carry - see CellData.sum_matrix. A blank counts as zero.
    sum_by, sum_levels : optionally SPLIT each of those sums by a
           column of integer codes 0 .. sum_levels-1 (-1 = in no
           group, contributes to none). Each sum var then becomes
           `sum_levels` sums, named by split_sum_name(var, code). Done
           inside one bincount, so a run with twenty groups holds no
           more per-person data than a run with one.
    """
    binary_vars = binary_vars or []
    value_vars = value_vars or []
    sum_vars = list(sum_vars or [])
    df = df.copy()

    # --- coerce to numeric; blanks become NaN ---
    for c in [e_col, n_col] + binary_vars + value_vars + sum_vars:
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
    # v1.62.1: EXACT midpoints (grid_midpoints) - an odd cell size
    # used to merge the two cells either side of 0. Unsnapped
    # coordinates are kept as given, not truncated.
    if snap:
        df["_E"] = grid_midpoints(df[e_col], unit_size)
        df["_N"] = grid_midpoints(df[n_col], unit_size)
    else:
        df["_E"] = exact_coords(df[e_col])
        df["_N"] = exact_coords(df[n_col])

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

    # (v1.55.0's `quiet_missing` is gone with the per-group sub-fields
    # it silenced - BACKLOG 409. Additive sums have no missing values:
    # a person outside a group contributes zero to its sums.)
    for v in value_vars:
        miss = df[v].isna().sum()
        if miss:
            print(f"[cells] note: '{v}' has {miss} missing values - these "
                  f"individuals count towards k but not towards {v} statistics.")

    # --- aggregate ---
    # ONE VECTORISED PASS (v1.60.3). This walked the cells in Python
    # and, in each, ran four pandas operations per group - about
    # 0.3 ms per cell and group. Harmless for a town; John's Turkey at
    # 1 km with machine 4's rates is ~450,000 cells x 32 groups, which
    # sat silent for well over an hour after the projection line
    # (19 October). Every number here is a per-cell SUM: the rows are
    # sorted by cell once (stably, so each cell keeps its own row
    # order) and each sum is one np.add.reduceat over the cells'
    # segments. NOT bincount, which adds strictly left to right: 1000
    # pixels of 0.1 then make 99.9999999999986, and a cell holding
    # exactly k people reads as short of it (test_unitsize caught
    # that). The value arrays are the same sorted rows, split at the
    # boundaries. tests/test_review_1_60_1 checks all of it against
    # the old loop.
    groups = df.groupby(["_E", "_N"], sort=True)
    gi = groups.ngroup().to_numpy()
    keys = groups.size().index
    m_cells = len(keys)
    E = exact_coords(keys.get_level_values(0).to_numpy(float))
    N = exact_coords(keys.get_level_values(1).to_numpy(float))
    order = np.argsort(gi, kind="stable")          # row order kept
    g_sorted = gi[order]
    starts = (np.flatnonzero(np.r_[True, g_sorted[1:] != g_sorted[:-1]])
              if len(gi) else np.zeros(0, dtype=np.int64))

    def per_cell(x):
        if not m_cells:
            return np.zeros(0)
        return np.add.reduceat(np.asarray(x, float)[order], starts)

    wcol = (df[weights].to_numpy(float) if weights is not None else None)
    n = (per_cell(wcol) if weights is not None
         else np.bincount(gi, minlength=m_cells).astype(np.int64))
    bsums, bvalid = {}, {}
    for v in binary_vars:
        col = df[v].to_numpy(float)
        ok = ~np.isnan(col)
        # a blank contributes nothing; an infinity is NOT made finite
        val = np.where(ok, col, 0.0)
        if weights is None:
            bsums[v] = per_cell(val)
            bvalid[v] = np.bincount(gi[ok], minlength=m_cells)
        else:
            bsums[v] = per_cell(val * wcol)
            bvalid[v] = per_cell(np.where(ok, wcol, 0.0))
    varrs = {}
    vwts = {}
    if value_vars:
        for v in value_vars:
            col = df[v].to_numpy(float)[order]
            ok = ~np.isnan(col)
            cuts = np.searchsorted(g_sorted[ok], np.arange(1, m_cells))
            varrs[v] = (np.split(col[ok], cuts) if m_cells else [])
            if weights is not None:
                vwts[v] = (np.split(wcol[order][ok], cuts) if m_cells
                           else [])
    labels = None
    mixed = 0
    if label_col:
        u = (pd.DataFrame({"g": gi,
                           "l": df[label_col].astype(str).to_numpy()})
             .drop_duplicates().sort_values(["g", "l"], kind="stable"))
        per = np.bincount(u["g"].to_numpy(), minlength=m_cells)
        mixed = int((per > 1).sum())
        joined = u.groupby("g", sort=True)["l"].agg("|".join) if mixed \
            else u.set_index("g")["l"]
        labels = joined.reindex(range(m_cells)).tolist()

    if label_col and mixed:
        print(f"[cells] WARNING: {mixed} cells contain several distinct "
              f"'{label_col}' values (joined with '|'). A good cell ID "
              f"should be constant within a cell.")

    # BACKLOG 409: the additive sums, in ONE vectorised pass - a cell's
    # number is its group's position in the same sorted order the loop
    # above walked, so row i of the matrix is cell i.
    sum_matrix, sum_names = None, list(sum_vars)
    if sum_vars:
        if wcol is None:
            wcol = np.ones(len(df))
        if sum_by is None:
            n_lev, code = 1, np.zeros(len(df), dtype=np.int64)
        else:
            n_lev = int(sum_levels)
            raw = pd.to_numeric(df[sum_by], errors="coerce").to_numpy(float)
            if n_lev < 1 or not np.isfinite(raw).all() \
                    or (raw != np.round(raw)).any() \
                    or raw.min(initial=0) < -1 or raw.max(initial=0) >= n_lev:
                raise ValueError(
                    f"[cells] sum_by='{sum_by}' must hold whole codes from "
                    f"-1 to {n_lev - 1}.")
            code = raw.astype(np.int64)
            sum_names = [split_sum_name(v, i) for v in sum_vars
                         for i in range(n_lev)]
        keep = code >= 0
        slot = gi[keep] * n_lev + code[keep]
        blocks = []
        for v in sum_vars:
            col = df[v].to_numpy(float)
            # blank -> 0; an infinity is NOT made finite (nan_to_num
            # would turn it into 1.8e308 and hide it)
            col = np.where(np.isnan(col), 0.0, col)
            blocks.append(np.bincount(
                slot, weights=(col * wcol)[keep],
                minlength=m_cells * n_lev).reshape(m_cells, n_lev))
        sum_matrix = np.concatenate(blocks, axis=1)

    cd = CellData(
        # v1.62.1: exact - integers for every even cell size, as before
        E=exact_coords(E),
        N=exact_coords(N),
        n=np.array(n, dtype=float if weights is not None else np.int64),
        binary_sums={v: np.array(a, dtype=float) for v, a in bsums.items()},
        binary_valid={v: np.array(a, dtype=float)
                      for v, a in bvalid.items()},
        value_arrays=varrs,
        value_weights=vwts,
        unit_size=unit_size,
        labels=labels,
        sum_matrix=sum_matrix,
        sum_names=sum_names,
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
