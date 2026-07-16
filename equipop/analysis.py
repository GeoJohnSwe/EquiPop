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
import pandas as pd
from itertools import groupby

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

        rec: dict = {
            "Id": getattr(row, id_col) if id_col else None,
            "EastWest": e0,
            "NorthSouth": n0,
            "CountAllLocal": local_all,
            "CountGroupLocal": local_grp,
        }

        # running totals - raw and (optionally) decay-weighted
        sum_all, sum_grp, dist_m = local_all, local_grp, 0.0
        d_all, d_grp = local_all, local_grp   # weight(0) = 1
        pending = list(k_values)

        def record(k: int):
            """Write all per-k output columns at the current state."""
            rec[col("N", k)] = sum_all
            rec[col("T", k)] = sum_grp
            rec[col("R", k)] = sum_grp / sum_all if sum_all else np.nan
            rec[col("Dist", k)] = dist_m
            if decay:
                rec[col("ND", k)] = d_all
                rec[col("TD", k)] = d_grp
                rec[col("RD", k)] = d_grp / d_all if d_all else np.nan

        # thresholds already satisfied inside the origin cell
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
                for dx, dy in offsets:
                    cell = lookup.get((e0 + dx * step, n0 + dy * step))
                    if cell:
                        ring_all += cell[0]
                        ring_grp += cell[1]
                if ring_all == 0:
                    continue
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
from .stats import BINARY_STATS, VALUE_STATS, PREFIX


def run_knn_stats(
    cd: CellData,
    k_values: list[int],
    stats: dict[str, list[str]],
    max_radius_units: int | None = None,
    r_values: list[float] | None = None,
) -> pd.DataFrame:
    """
    Radial k-NN analysis with user-selected statistics per variable.

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

    bin_vars = [v for v in stats if v in cd.binary_sums]
    val_vars = [v for v in stats if v in cd.value_arrays]
    unknown = [v for v in stats if v not in bin_vars + val_vars]
    if unknown:
        raise ValueError(f"Variables {unknown} were not declared in "
                         f"build_cells(binary_vars=..., value_vars=...).")
    for v in bin_vars:
        for s in stats[v]:
            if s not in BINARY_STATS:
                raise ValueError(f"Unknown binary statistic '{s}' for {v}. "
                                 f"Available: {list(BINARY_STATS)}")
    for v in val_vars:
        for s in stats[v]:
            if s not in VALUE_STATS:
                raise ValueError(f"Unknown value statistic '{s}' for {v}. "
                                 f"Available: {list(VALUE_STATS)}")

    m = len(cd)
    print(f"[stats] {m} cells, k = {k_values}" +
          (f", r = {r_values} m" if r_values else ""))
    print(f"[stats] binary vars: {bin_vars} | value vars: {val_vars}")

    results = []
    Ef, Nf = cd.E.astype(float), cd.N.astype(float)

    for oi in range(m):
        e0, n0 = cd.E[oi], cd.N[oi]

        # distances from this origin to ALL populated cells (vectorised)
        dist = np.hypot(Ef - e0, Nf - n0)
        order = np.argsort(dist, kind="stable")

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
        val_chunks = {v: [] for v in val_vars}
        dist_m = 0.0
        pending = list(k_values)
        pending_r = list(r_values)

        def record(k, suffix=None, with_dist=True):
            suffix = f"{k}" if suffix is None else suffix
            rec[f"N_{suffix}"] = sum_n
            if with_dist:
                rec[f"Dist_{suffix}"] = dist_m
            for v in bin_vars:
                for s in stats[v]:
                    rec[f"{PREFIX[s]}_{v}_{suffix}"] = BINARY_STATS[s](sum_n, bin_t[v])
            for v in val_vars:
                x = (np.concatenate(val_chunks[v])
                     if val_chunks[v] else np.empty(0))
                rec[f"Nv_{v}_{suffix}"] = len(x)
                for s in stats[v]:
                    rec[f"{PREFIX[s]}_{v}_{suffix}"] = VALUE_STATS[s](x)

        # walk cells in distance order, atomically per equal-distance ring
        def record_r(rv):
            record(rv, suffix=f"r{rv:g}", with_dist=False)

        j = 0
        while j < m and (pending or pending_r):
            d = dist[order[j]]
            while pending_r and pending_r[0] < d - 1e-9:
                record_r(pending_r.pop(0))   # radius closes BEFORE this ring
            if max_radius_units is not None and d > max_radius_units * cd.unit_size:
                break
            # gather the full ring of cells at this exact distance
            ring = []
            while j < m and dist[order[j]] - d < 1e-6:
                ring.append(order[j])
                j += 1
            for ci in ring:
                sum_n += float(cd.n[ci])
                for v in bin_vars:
                    bin_t[v] += cd.binary_sums[v][ci]
                for v in val_vars:
                    a = cd.value_arrays[v][ci]
                    if len(a):
                        val_chunks[v].append(a)
            dist_m = float(d)
            while pending and sum_n >= pending[0]:
                record(pending.pop(0))

        for k in pending:          # unreached: partial results
            record(k)
        for rv in pending_r:       # radius reaches beyond data: whole set
            record_r(rv)
        rec["SumN"] = sum_n
        rec["MaxDistance"] = dist_m
        results.append(rec)

    return pd.DataFrame(results)
