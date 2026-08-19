"""
analysis.py - the radial k-NN engine (Phase 1 + decay).

Core idea (from the EquiPop papers): on a uniform grid, the relative
distances from ANY origin cell to its surrounding cells are always the
same. So we compute ONE list of cell-offsets sorted by distance, and
reuse it for every origin. Cells at identical distance form a "ring".

Decay: when a Decay object is passed, every neighbour's contribution
is ALSO accumulated multiplied by weight(distance). The k-thresholds
are still defined by the RAW (unweighted) counts - the decayed values
are simply recorded at the same moment, exactly as in the original
EquiPop ("decayed variables use the same k-values as the non-decaying
variables"). Decayed counts are therefore always <= raw counts.

Output naming - two schemes, chosen with naming="short" | "legacy":

  short (default)   legacy (original EquiPop)
  ---------------   -------------------------------
  N_50              IntervalSumCountAll_50
  T_50              IntervalSumCountGroup_50
  R_50              IntervalRatio_50
  Dist_50           IntervalDistance_50
  ND_50             IntervalSumCountAllDecay_50
  TD_50             IntervalSumCountGroupDecay_50
  RD_50             IntervalRatioDecay_50

(N = count of all, T = treatment, R = ratio, D = decayed.)
"""

import math
import numpy as np
from scipy.spatial import cKDTree
import pandas as pd
from itertools import groupby

from . import overshoot, selfpot
from .decay import Decay


# ---------------------------------------------------------------- naming
NAMES = {
    "short": {
        "N": "N_{k}", "T": "T_{k}", "R": "R_{k}", "Dist": "Dist_{k}",
        "ND": "ND_{k}", "TD": "TD_{k}", "RD": "RD_{k}",
    },
    "legacy": {
        "N": "IntervalSumCountAll_{k}",
        "T": "IntervalSumCountGroup_{k}",
        "R": "IntervalRatio_{k}",
        "Dist": "IntervalDistance_{k}",
        "ND": "IntervalSumCountAllDecay_{k}",
        "TD": "IntervalSumCountGroupDecay_{k}",
        "RD": "IntervalRatioDecay_{k}",
    },
}


def build_distance_rings(max_radius_units: int):
    """
    Pre-compute all cell offsets (dx, dy) within max_radius_units,
    grouped into 'rings' of identical distance, sorted by distance.
    The origin (0, 0) is excluded - it is counted first, separately.

    Returns a list of (distance_in_units, [(dx, dy), ...]).
    """
    offsets = []
    for dx in range(-max_radius_units, max_radius_units + 1):
        for dy in range(-max_radius_units, max_radius_units + 1):
            if dx == 0 and dy == 0:
                continue
            d = math.hypot(dx, dy)
            if d <= max_radius_units:
                offsets.append((d, dx, dy))
    offsets.sort(key=lambda t: t[0])
    return [(dist, [(dx, dy) for _, dx, dy in grp])
            for dist, grp in groupby(offsets, key=lambda t: t[0])]


def _interp_base(dist_m, unit_size, sp, ring_dist_m):
    """Where a crossing ring's area-linear interpolation STARTS.

    BACKLOG 191. dist_m is the distance out to everything already
    counted. When that is still zero the mass counted so far is the
    origin's OWN cell - and its people are not standing on the origin.
    They are spread through the cell and reached by the equal-area
    radius s*unit/sqrt(pi), which is exactly what the in-cell formula
    returns at k = n. Interpolating from 0 instead made Dist_k FALL as
    k rose, by up to 18 m on John's field data.

    It must be applied HERE and not by raising dist_m itself: a
    dist_m of 0.0 is also the SENTINEL meaning "the neighbourhood is
    still inside the origin cell", which selects the k-scaled in-cell
    estimate. Raising it destroyed that signal and made two engines
    disagree - caught by the parity test, which is what it is for.
    """
    if dist_m > 0.0 or sp <= 0.0:
        return dist_m
    return min(selfpot.radius_for_k(unit_size, 1.0, 1.0, sp),
               float(ring_dist_m))


def run_knn(
    cells: pd.DataFrame,
    k_values: list[int],
    count_all_col: str = "FullPop",
    count_group_col: str = "Treatment",
    unit_size: float = 100.0,
    max_radius_units: int = 500,
    id_col: str | None = "id",
    tie_mode: str = "ring",
    decay: Decay | None = None,
    naming: str = "short",
    seed: int | None = None,
    self_potential: float = selfpot.DEFAULT_SELF_POTENTIAL,
    overshoot_mode: str | None = None,
) -> pd.DataFrame:
    """
    Radial k-NN analysis for every populated cell.

    Parameters
    ----------
    cells : DataFrame with one row per grid cell ('E_grid', 'N_grid',
            a total-count column, a treatment-count column).
    k_values : the k thresholds, e.g. [50, 100, 200, 400, 800].
    unit_size : grid size in metres.
    max_radius_units : search limit in grid units; unreached ks get
            partial results (mirrors original EquiPop behaviour).
    tie_mode : "ring" (default) adds all equidistant cells before
            checking thresholds; "sequential" checks after every
            single cell (original EquiPop, order-dependent).
    decay : a Decay object, e.g. Decay(half_life_m=8000), or None.
    naming : "short" (N_50, T_50, R_50, ...) or
             "legacy" (IntervalSumCountAll_50, ...).
    self_potential : how far away what is LOCAL - what the origin's own
            cell already holds - is treated as being, 0 to 1 (BACKLOG
            95, and 153). RULED by John, 1.29.7: this engine gets the
            SAME rule as run_knn_counts and run_knn_stats, so "two
            engines, one mathematics" is true again. Until then this
            function put its own cell at distance zero and reported
            Dist_k = 0 wherever one cell already held k - while the
            newer engines reported the equal-area radius for the same
            data. The manuals teach with THIS function, so a reader
            following them got one number and the QGIS door gave
            another.
    seed : only used with tie_mode="sequential": shuffles the (otherwise
           arbitrary) within-ring visiting order reproducibly. Record it
           in the run's metadata log. None keeps the construction order.

    Returns
    -------
    One row per origin cell. Fixed columns: Id, EastWest, NorthSouth,
    CountAllLocal, CountGroupLocal, SumCountAll, SumCountGroup, Ratio,
    MaxDistance. Per-k columns as per the chosen naming scheme.
    """
    k_values = sorted(k_values)
    bad = [k for k in k_values if k <= 0]
    if bad:
        raise ValueError(
            f"[k] k must be a POSITIVE number of people; got {bad}. "
            "k=0 asks for nobody, and every mode then answers "
            "differently about a neighbourhood that does not exist. "
            "Found by John's hand check, 1.30. Nothing was computed.")
    osm = overshoot.resolve(overshoot_mode)
    _seed_given = seed is not None
    os_seed = int(seed) if _seed_given else overshoot.draw_seed()
    if osm == overshoot.SAMPLED:
        print(overshoot.seed_message(os_seed, _seed_given))
    sp = selfpot.check(self_potential)          # BACKLOG 153
    nm = NAMES[naming]

    def col(kind: str, k: int) -> str:
        return nm[kind].format(k=k)

    # ---- fast lookup: (E, N) -> (count_all, count_group) ----
    lookup: dict[tuple[int, int], tuple[float, float]] = {}
    for row in cells.itertuples(index=False):
        key = (int(getattr(row, "E_grid")), int(getattr(row, "N_grid")))
        lookup[key] = (float(getattr(row, count_all_col)),
                       float(getattr(row, count_group_col)))

    print(f"[analysis] {len(lookup)} populated cells, k = {k_values}, "
          f"unit = {unit_size} m")
    if decay:
        print(f"[analysis] decay active: {decay.describe()}")
    rings = build_distance_rings(max_radius_units)
    if tie_mode == "sequential" and seed is not None:
        rng = np.random.default_rng(seed)
        rings = [(d, list(rng.permutation(np.array(offs, dtype=object))))
                 for d, offs in rings]
        print(f"[analysis] sequential tie order shuffled with seed {seed}")
    print(f"[analysis] {len(rings)} distance rings ready")

    results = []
    step = int(unit_size)

    for row in cells.itertuples(index=False):
        e0 = int(getattr(row, "E_grid"))
        n0 = int(getattr(row, "N_grid"))
        local_all, local_grp = lookup[(e0, n0)]
        origin_ident = int(overshoot.cell_identity(
            round(e0 / step), round(n0 / step)))

        rec: dict = {
            "Id": getattr(row, id_col) if id_col else None,
            "EastWest": e0,
            "NorthSouth": n0,
            "CountAllLocal": local_all,
            "CountGroupLocal": local_grp,
        }

        # running totals - raw and (optionally) decay-weighted
        sum_all, sum_grp, dist_m = local_all, local_grp, 0.0
        # BACKLOG 153: the origin's own people are not standing on the
        # origin. Charge them the mean intra-cell distance, exactly as
        # run_knn_counts does, or they keep weight 1.0 - the largest
        # weight in the calculation - on the mass we know least about.
        _w0 = (decay.weight(selfpot.decay_distance(unit_size, sp))
               if decay and sp > 0 else 1.0)
        d_all, d_grp = local_all * _w0, local_grp * _w0
        pending = list(k_values)

        def record(k: int, n=None, t=None, d=None):
            """Write all per-k output columns at the current state.

            BACKLOG 99: n, t and d override the running totals so a
            PARTIAL ring can be recorded without the running totals
            having taken the whole of it. Left as None the behaviour
            is exactly as before."""
            n = sum_all if n is None else n
            t = sum_grp if t is None else t
            rec[col("N", k)] = n
            rec[col("T", k)] = t
            rec[col("R", k)] = t / n if n else np.nan
            d_k = dist_m if d is None else d
            if d_k <= 0.0 and n >= k:
                # the whole neighbourhood IS the origin cell, so the
                # radius is not zero - it is unmeasured (BACKLOG 153)
                # the share reported is `n`; the equal-area radius
                # needs the people actually STANDING in the cell
                d_k = selfpot.radius_for_k(unit_size, k,
                                           float(sum_all), sp)
            rec[col("Dist", k)] = d_k
            if decay:
                rec[col("ND", k)] = d_all
                rec[col("TD", k)] = d_grp
                rec[col("RD", k)] = d_grp / d_all if d_all else np.nan

        # thresholds already satisfied inside the origin cell.
        # BACKLOG 99: the origin cell is a RING TOO - a ring of one -
        # and a k smaller than its own population takes a share of it,
        # exactly as the fast engine does by treating it as ring 1.
        # Handling it as a whole cell here was the two engines'
        # remaining disagreement under `proportional`.
        if osm != overshoot.WHOLE:
            _oid = np.array([origin_ident], dtype=np.uint64)
            _opop = np.array([local_all], dtype=float)
            while pending and local_all >= pending[0]:
                k = pending.pop(0)
                wt, taken = overshoot.ring_weights(
                    osm, k, 0.0, _opop, _oid,
                    seed=os_seed, origin_id=origin_ident)
                record(k, n=taken, t=local_grp * float(wt[0]), d=0.0)
        while pending and sum_all >= pending[0]:
            record(pending.pop(0))

        # --- expand ring by ring ---
        for dist_units, offsets in rings:
            if not pending:
                break
            ring_dist_m = dist_units * unit_size
            w = decay.weight(ring_dist_m) if decay else 1.0

            if tie_mode == "sequential":
                for dx, dy in offsets:
                    cell = lookup.get((e0 + dx * step, n0 + dy * step))
                    if not cell:
                        continue
                    sum_all += cell[0]
                    sum_grp += cell[1]
                    d_all += cell[0] * w
                    d_grp += cell[1] * w
                    dist_m = ring_dist_m
                    while pending and sum_all >= pending[0]:
                        record(pending.pop(0))
            else:  # "ring" - atomic per equidistant ring
                ring_all = ring_grp = 0.0
                r_pop, r_grp, r_ids = [], [], []
                for dx, dy in offsets:
                    ex, ny = e0 + dx * step, n0 + dy * step
                    cell = lookup.get((ex, ny))
                    if cell:
                        ring_all += cell[0]
                        ring_grp += cell[1]
                        r_pop.append(cell[0])
                        r_grp.append(cell[1])
                        r_ids.append(overshoot.cell_identity(
                            round(ex / step), round(ny / step)))
                if ring_all == 0:
                    continue
                # BACKLOG 99: any k this ring CROSSES takes only a
                # share of it. Recorded BEFORE the running totals
                # swallow the whole ring - under `whole` the share is
                # 1.0 and the two are identical.
                if osm != overshoot.WHOLE:
                    r_pop_a = np.asarray(r_pop, dtype=float)
                    r_grp_a = np.asarray(r_grp, dtype=float)
                    r_ids_a = np.asarray(r_ids, dtype=np.uint64)
                    while pending and sum_all + ring_all >= pending[0]:
                        k = pending.pop(0)
                        wt, taken = overshoot.ring_weights(
                            osm, k, sum_all, r_pop_a, r_ids_a,
                            seed=os_seed, origin_id=int(origin_ident))
                        f = taken / ring_all if ring_all else 1.0
                        record(k,
                               n=sum_all + taken,
                               t=sum_grp + float((r_grp_a * wt).sum()),
                               d=float(overshoot.radius(
                                   _interp_base(dist_m, unit_size, sp,
                                                ring_dist_m),
                                   ring_dist_m, f)))
                sum_all += ring_all
                sum_grp += ring_grp
                d_all += ring_all * w
                d_grp += ring_grp * w
                dist_m = ring_dist_m
                while pending and sum_all >= pending[0]:
                    record(pending.pop(0))

        # unreached thresholds: partial results (spec, section 12)
        for k in pending:
            record(k)

        rec["SumCountAll"] = sum_all
        rec["SumCountGroup"] = sum_grp
        rec["Ratio"] = sum_grp / sum_all if sum_all else np.nan
        rec["MaxDistance"] = dist_m
        results.append(rec)

    out = pd.DataFrame(results)
    fixed = ["Id", "EastWest", "NorthSouth", "CountAllLocal",
             "CountGroupLocal", "SumCountAll", "SumCountGroup",
             "Ratio", "MaxDistance"]
    kinds = ["N", "T", "R", "Dist"] + (["ND", "TD", "RD"] if decay else [])
    per_k = [col(kind, k) for k in k_values for kind in kinds]
    return out[fixed + per_k]


# ======================================================================
#  run_knn_stats - k-NN with per-variable statistics (tiers 1-3)
# ======================================================================
from .cells import CellData
from .wstats import weighted_stats
from .stats import (BINARY_STATS, VALUE_STATS, PREFIX,
                    check_gini_input,
                    value_stat, stat_prefix, is_percentile)


def run_knn_stats(
    cd: CellData,
    k_values: list[int],
    stats: dict[str, list[str]],
    max_radius_units: int | None = None,
    r_values: list[float] | None = None,
    m_neighbors: int | None = None,
    overshoot_mode: str | None = None,
    seed: int | None = None,
    self_potential: float = selfpot.DEFAULT_SELF_POTENTIAL,
) -> pd.DataFrame:
    """
    Radial k-NN analysis with user-selected statistics per variable.

    self_potential : how far away your OWN cell's people are, 0 to 1
    (v1.29.5, BACKLOG 95). Must match run_knn_counts exactly - the two
    engines are bound by regression test. See equipop/selfpot.py.

    The user switches statistics on per FUNCTION (applied to all k),
    exactly as requested:

        stats = {
            "HighEdu": ["ratio", "sd", "se", "entropy", "gini"],  # binary
            "ForvInk": ["mean", "median", "sd", "se", "gini"],    # value
        }

    Whether a variable is binary (tier 1, exact from counts) or
    continuous (tiers 2/3, from stored individual values) is decided
    by how it was declared in build_cells().

    Engine note: this function uses a distance-sort core rather than
    the ring-expansion core of run_knn(). For the radial (no-friction)
    model the two are MATHEMATICALLY IDENTICAL - cells at equal
    distance are still processed as one atomic ring - but the sort
    core is much faster when populated cells are sparse. The
    ring-expansion core remains the basis for the future friction
    model, where visiting order genuinely depends on the path.

    Output columns
    --------------
    EastWest, NorthSouth, N_local, plus per k:
      N_{k}, Dist_{k},
      per binary var+stat:  e.g. R_HighEdu_{k}, Gini_HighEdu_{k}
      per value  var+stat:  e.g. Mean_ForvInk_{k}, Med_ForvInk_{k}
      per value  var:       Nv_{var}_{k} (count of valid values)
    Unreached k-levels receive partial results, as in run_knn().
    """
    k_values = sorted(k_values or [])
    r_values = sorted(r_values or [])
    if not (k_values or r_values):
        raise ValueError("give k_values and/or r_values")
    osm = overshoot.resolve(overshoot_mode)
    _seed_given = seed is not None
    os_seed = int(seed) if _seed_given else overshoot.draw_seed()
    if osm == overshoot.SAMPLED:
        print(overshoot.seed_message(os_seed, _seed_given))
    bad = [k for k in k_values if k <= 0]
    if bad:
        raise ValueError(
            f"[k] k must be a POSITIVE number of people; got {bad}. "
            "k=0 asks for nobody, and every mode then answers "
            "differently about a neighbourhood that does not exist - "
            "the whole-ring rule returns the origin cell, a "
            "proportional share returns zero people and an undefined "
            "R. Found by John's hand check, 1.30. Nothing was "
            "computed.")

    bin_vars = [v for v in stats if v in cd.binary_sums]
    val_vars = [v for v in stats if v in cd.value_arrays]
    unknown = [v for v in stats if v not in bin_vars + val_vars]
    if unknown:
        raise ValueError(f"Variables {unknown} were not declared in "
                         f"build_cells(binary_vars=..., value_vars=...).")
    # BACKLOG 118, v1.31: the refusal that stood here is GONE.
    #
    # It read: a quarter of a boundary cell has no median. That was
    # true of the IMPLEMENTATION, not of the mathematics - value
    # statistics were computed by repeating each person, and you
    # cannot repeat somebody 0.4 times. equipop/wstats.py computes
    # them from (value, weight) pairs, where a weight of 0.4 is
    # ordinary, so `proportional` is answerable here now.
    #
    # Both machines can therefore share ONE default, and the line
    # machine 2 printed on every run - naming its mode and machine
    # 1's - has nothing left to warn about.
    for v in bin_vars:
        for s in stats[v]:
            if s not in BINARY_STATS:
                raise ValueError(f"Unknown binary statistic '{s}' for {v}. "
                                 f"Available: {list(BINARY_STATS)}")
    for v in val_vars:
        for s in stats[v]:
            if s not in VALUE_STATS and not is_percentile(s):
                raise ValueError(f"Unknown value statistic '{s}' for {v}. "
                                 f"Available: {list(VALUE_STATS)} "
                                 "plus percentiles like p10/p97.5")

    sp = selfpot.check(self_potential)
    # BACKLOG 154, John's ruling: refuse a Gini over negative values,
    # everywhere. ArcGIS Pro has refused it for years; the core and
    # the QGIS path did not, and QGIS has Gini in its DEFAULT list -
    # so the same data was refused through one door and accepted
    # through another. Checked HERE because every door and the Python
    # API reach statistics through this function, and because the
    # per-neighbourhood inner loop is no place to raise.
    for _v, _asked in (stats or {}).items():
        if "gini" in _asked and _v in cd.value_arrays:
            _flat = [a for a in cd.value_arrays[_v] if a is not None
                     and len(a)]
            if _flat:
                check_gini_input(np.concatenate(_flat), f"'{_v}'")
    # BACKLOG 118. One pass, per cell: the expanded per-person array
    # becomes (distinct value, how many people hold it). Lossless, and
    # it is what lets a crossing ring contribute a SHARE of a cell -
    # multiply the counts by the share and the arithmetic carries on.
    #
    # NOTE what this does NOT yet fix: the expansion itself still
    # happens upstream, where counts become persons. That is the half
    # of 118 that unblocks continental runs, and it is a change to the
    # whole pipeline rather than to this function.
    val_pairs = {}
    for v in val_vars:
        per_cell = []
        for a in cd.value_arrays[v]:
            if a is None or len(a) == 0:
                per_cell.append((np.empty(0), np.empty(0)))
            else:
                u, c = np.unique(np.asarray(a, dtype=float),
                                 return_counts=True)
                per_cell.append((u, c.astype(float)))
        val_pairs[v] = per_cell

    tally = {"selfpot": {}, "over": {}, "origins": 0}
    scratch = {"selfpot": {}, "over": {}}      # BACKLOG 111

    m = len(cd)
    print(f"[stats] {m} cells, k = {k_values}" +
          (f", r = {r_values} m" if r_values else ""))
    print(f"[stats] binary vars: {bin_vars} | value vars: {val_vars}")

    results = []
    Ef, Nf = cd.E.astype(float), cd.N.astype(float)

    # ---------------------------------------------- v1.16.3 fast path
    # Sorting every cell for every origin is quadratic (measured: cells
    # x2 -> time x2.7). Instead fetch the m nearest CELLS from a
    # KD-tree, exactly as the counts engine does, and walk those. An
    # origin whose k (or radius) is NOT resolved strictly inside that
    # neighbourhood - including the tie-ring case - is recomputed
    # against all cells, so results are bit-for-bit the exhaustive
    # ones. m affects SPEED ONLY, never numbers.
    if m_neighbors is None:            # auto-tuned from k / radius
        from .cells import auto_m_neighbors
        m_neighbors = auto_m_neighbors(cd, k_values, r_values)
    mm = int(min(max(m_neighbors, 1), m))
    tree = cKDTree(np.c_[Ef, Nf]) if mm < m else None
    o_chunk = max(1, min(512, m))
    fallbacks = 0

    def _walk(oi, nd, ni, exhaustive):
        """One origin over the neighbour list (sorted by distance).
        Returns (record, trustworthy) - trustworthy is False when a
        result had to be taken from the final, possibly incomplete
        ring of an m-limited neighbourhood."""
        e0, n0 = cd.E[oi], cd.N[oi]
        d_last = float(nd[-1]) if len(nd) else 0.0
        touched_last = False

        # BACKLOG 111: this counter used to live here, inside _walk,
        # which runs AGAIN for every origin whose search has to
        # widen - 514 real origins were reported as 1,511. The single
        # acceptance point is _store, so the counting happens there
        # and _walk only fills this scratch.
        scratch["selfpot"] = {}
        scratch["over"] = {}
        _oid = int(overshoot.cell_identity(round(float(e0) / cd.unit_size),
                                           round(float(n0) / cd.unit_size)))
        rec: dict = {"EastWest": round(float(e0), 2),
                     "NorthSouth": round(float(n0), 2),
                     "N_local": float(cd.n[oi])}
        if cd.labels is not None:
            rec["CellId"] = cd.labels[oi]
        for v in bin_vars:
            rec[f"{v}_local"] = float(cd.binary_sums[v][oi])

        # running state
        sum_n = 0.0
        bin_t = {v: 0.0 for v in bin_vars}
        # BACKLOG 168: the denominator John ruled on - people whose
        # value is OBSERVED, not everybody present.
        bin_ok = {v: 0.0 for v in bin_vars}
        val_chunks = {v: [] for v in val_vars}
        dist_m = 0.0
        pending = list(k_values)
        pending_r = list(r_values)

        def record(k, suffix=None, with_dist=True, partial=None):
            """BACKLOG 99: `partial` carries a SHARE of the crossing
            ring - what to report instead of the running totals, which
            have not swallowed that ring yet. None = as before."""
            suffix = f"{k}" if suffix is None else suffix
            n_use = sum_n if partial is None else partial["n"]
            t_use = bin_t if partial is None else partial["t"]
            rec[f"N_{suffix}"] = n_use
            if with_dist:
                d_k = dist_m if partial is None else partial["d"]
                if d_k <= 0.0 and n_use >= k:
                    # whole neighbourhood inside the origin cell
                    # (BACKLOG 95) - same rule as the fast engine
                    # the equal-area radius needs the people STANDING
                    # in the cell, not the share reported
                    _pop = (float(sum_n) if partial is None
                            else float(partial["cellpop"]))
                    d_k = selfpot.radius_for_k(cd.unit_size, k, _pop, sp)
                    scratch["selfpot"][k] = \
                        scratch["selfpot"].get(k, 0) + 1
                if n_use >= 2 * k:                      # BACKLOG 94
                    scratch["over"][k] = scratch["over"].get(k, 0) + 1
                rec[f"Dist_{suffix}"] = d_k
            for v in bin_vars:
                d_use = (bin_ok[v] if partial is None
                         else partial["ok"][v])
                for s in stats[v]:
                    rec[f"{PREFIX[s]}_{v}_{suffix}"] = \
                        BINARY_STATS[s](d_use, t_use[v])
            for v in val_vars:
                chunks = list(val_chunks[v])
                if partial is not None:
                    chunks += partial["vals"][v]
                if chunks:
                    vv = np.concatenate([c[0] for c in chunks])
                    ww = np.concatenate([c[1] for c in chunks])
                else:
                    vv = ww = np.empty(0)
                # Nv_ is PEOPLE with a usable value, as it always was -
                # now a sum of weights rather than a length, so a
                # fractional ring reports the fraction it contributed.
                rec[f"Nv_{v}_{suffix}"] = float(ww.sum())
                got = weighted_stats(stats[v], vv, ww)
                for s in stats[v]:
                    rec[f"{stat_prefix(s)}_{v}_{suffix}"] = got[s]

        # walk cells in distance order, atomically per equal-distance ring
        def record_r(rv):
            record(rv, suffix=f"r{rv:g}", with_dist=False)

        j = 0
        n_nb = len(nd)
        while j < n_nb and (pending or pending_r):
            d = float(nd[j])
            while pending_r and pending_r[0] < d - 1e-9:
                record_r(pending_r.pop(0))   # radius closes BEFORE this ring
            if max_radius_units is not None and d > max_radius_units * cd.unit_size:
                break
            # gather the full ring of cells at this exact distance
            ring = []
            while j < n_nb and float(nd[j]) - d < 1e-6:
                ring.append(int(ni[j]))
                j += 1
            if not exhaustive and abs(d - d_last) < 1e-6:
                touched_last = True     # ring may be cut by the m limit
            # BACKLOG 99: this engine walks its own neighbour list and
            # needs the same rule as the other four, or machine 2
            # answers differently from machine 1 on the same data.
            ring_n = float(sum(float(cd.n[ci]) for ci in ring))
            if osm != overshoot.WHOLE and ring_n > 0:
                r_pop = np.array([float(cd.n[ci]) for ci in ring])
                # BACKLOG 118, v1.31. Cell identities are the seeded
                # order's business and NOTHING else looks at them -
                # ring_weights uses them under `sampled` alone. They
                # were being hashed for every crossing ring in every
                # mode, which was 40% of a profiled `proportional`
                # run doing nothing at all. Measured, not guessed:
                # the cost only became visible once machine 2 stopped
                # falling back to `whole` and the path ran for real.
                r_ids = (overshoot.cell_identity(
                    np.round(np.array([cd.E[ci] for ci in ring])
                             / cd.unit_size),
                    np.round(np.array([cd.N[ci] for ci in ring])
                             / cd.unit_size))
                    if osm == overshoot.SAMPLED else None)
                while pending and sum_n + ring_n >= pending[0]:
                    k = pending.pop(0)
                    wt, taken = overshoot.ring_weights(
                        osm, k, sum_n, r_pop, r_ids,
                        seed=os_seed, origin_id=_oid)
                    f = taken / ring_n if ring_n else 1.0
                    _partial = {
                        "n": sum_n + taken,
                        "t": {v: bin_t[v] + float(sum(
                            cd.binary_sums[v][ci] * w
                            for ci, w in zip(ring, wt)))
                            for v in bin_vars},
                        "d": float(overshoot.radius(
                            _interp_base(dist_m, cd.unit_size, sp,
                                         float(d)), float(d), f)),
                        "cellpop": sum_n + ring_n,
                        "ok": {v: bin_ok[v] + float(sum(
                            cd.valid_for(v)[ci] * w
                            for ci, w in zip(ring, wt)))
                            for v in bin_vars},
                        # BACKLOG 118: the same per-cell share the
                        # binary sums get, applied to the value
                        # weights. `whole` gives w = 1 and nothing
                        # changes; `proportional` gives the fraction.
                        "vals": {v: [(val_pairs[v][ci][0],
                                      val_pairs[v][ci][1] * w)
                                     for ci, w in zip(ring, wt)
                                     if len(val_pairs[v][ci][0])]
                                 for v in val_vars}}
                    record(k, partial=_partial)
            for ci in ring:
                sum_n += float(cd.n[ci])
                for v in bin_vars:
                    bin_t[v] += cd.binary_sums[v][ci]
                    bin_ok[v] += cd.valid_for(v)[ci]
                for v in val_vars:
                    pair = val_pairs[v][ci]
                    if len(pair[0]):
                        val_chunks[v].append(pair)
            dist_m = float(d)
            while pending and sum_n >= pending[0]:
                record(pending.pop(0))

        unresolved = bool(pending or pending_r)
        for k in pending:          # unreached: partial results
            record(k)
        for rv in pending_r:       # radius reaches beyond data: whole set
            record_r(rv)
        rec["SumN"] = sum_n
        rec["MaxDistance"] = dist_m
        # trustworthy unless an m-limited neighbourhood ran out or the
        # answer came from its final (possibly truncated) ring
        return rec, exhaustive or not (unresolved or touched_last)

    # v1.16.3 memory shape: one Python dict per origin costs ~10x
    # what the numbers need (422k origins were enough to thrash a
    # 3 GB box). Records are copied into preallocated columns as they
    # are produced; the dict path stays as a fallback if a record
    # ever carries an unexpected key.
    cols_out: dict = {}
    order_out: list = []
    fell_back = False

    def _store(i, rec):
        nonlocal fell_back
        tally["origins"] += 1                  # BACKLOG 111: once,
        for key in ("selfpot", "over"):        # and only on ACCEPTANCE
            for kk, vv in scratch[key].items():
                tally[key][kk] = tally[key].get(kk, 0) + vv
        if not cols_out and not fell_back:
            for kk, vv in rec.items():
                order_out.append(kk)
                cols_out[kk] = (np.empty(m, dtype=object)
                                if isinstance(vv, str)
                                else np.full(m, np.nan))
        if fell_back or set(rec) != set(cols_out):
            if not fell_back:                 # first mismatch: unwind
                fell_back = True
                results.extend(
                    {k2: cols_out[k2][j] for k2 in order_out}
                    for j in range(i))
                cols_out.clear()
            results.append(rec)
            return
        for kk, vv in rec.items():
            cols_out[kk][i] = vv

    # --------------------------------------------- v1.16.4 the LADDER
    # Same lesson as the counts engine: an origin too thin to reach k
    # inside its neighbourhood used to be re-sorted against ALL cells.
    # Widen the search x8 for exactly those origins instead; only the
    # final rung, rarely reached, is the full set. Numbers identical.
    todo = np.arange(m) if tree is not None else None
    m_now = mm
    done = 0
    if tree is None:
        for oi in range(m):
            dist = np.hypot(Ef - cd.E[oi], Nf - cd.N[oi])
            order = np.argsort(dist, kind="stable")
            rec, _ = _walk(oi, dist[order], order, True)
            _store(oi, rec)
            done += 1
            if m > 20000 and done % 20480 == 0:
                print(f"[stats] {done}/{m} origins done", flush=True)
    else:
        while len(todo):
            nxt = []
            c_now = max(1, min(o_chunk, int(2e6 // max(m_now, 1))))
            for start in range(0, len(todo), c_now):
                sel = todo[start:min(start + c_now, len(todo))]
                nds, nis = tree.query(np.c_[Ef[sel], Nf[sel]],
                                      k=m_now, workers=-1)
                if m_now == 1:
                    nds, nis = nds[:, None], nis[:, None]
                for r, oi in enumerate(sel):
                    rec, ok = _walk(int(oi), nds[r], nis[r],
                                    m_now >= m)
                    if ok:
                        _store(int(oi), rec)
                        done += 1
                    else:
                        nxt.append(int(oi))
                if m > 20000 and done % 20480 < c_now:
                    print(f"[stats] {done}/{m} origins done",
                          flush=True)
            if not nxt or m_now >= m:
                break
            fallbacks += len(nxt)
            m_now = int(min(m, max(m_now * 8, 64)))
            print(f"[stats] {len(nxt)} sparse origins need a wider "
                  f"search - retrying those with m = {m_now}"
                  + (" (all cells)" if m_now >= m else ""), flush=True)
            todo = np.asarray(nxt)

    if tree is not None:
        print(f"[stats] fast pass with m = {mm} neighbour cells"
              + (f"; {fallbacks} widened searches"
                 if fallbacks else ""))
    from .fastcounts import report_selfpot
    report_selfpot(tally, k_values, sp)
    if cols_out and not fell_back:
        return pd.DataFrame({k: cols_out[k] for k in order_out})
    return pd.DataFrame(results)
