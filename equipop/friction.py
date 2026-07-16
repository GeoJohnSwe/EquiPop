"""
friction.py - the friction growth model (EquiPop Flow / FARB core).

THE MODEL (Östh & Türk 2020, ch. 22): neighbourhood growth proceeds
from each origin to its eight surrounding cells, one 'round' per move.
A cell with friction value f sits out f extra rounds before it is
included (and before its own neighbours can be reached through it):

    included_round(neighbour) = included_round(cell) + 1 + friction(neighbour)

Friction 0 = free passage; higher = later inclusion. Neighbourhoods
therefore grow fast along low-friction paths and refuse to jump
across barriers (water, motorways) unless waiting out the delay.

IMPLEMENTATION: this is mathematically a shortest-path problem with
node weights, so we solve it exactly with Dijkstra on the grid graph
(scipy, C speed) rather than simulating rounds in Python. Cells are
then counted in order of their included-round; equal rounds form an
atomic 'ring' (same tie convention as the radial engine).

DEFAULT FRICTION for cells absent from the friction file is a user
decision (default_friction parameter). 0 means: unlisted land is
free, and the friction file lists BARRIERS (water, big roads). The
opposite convention (file lists fast roads, everything else slow)
is used in some studies - then set default_friction to the max.
"""

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra


def load_friction_table(
    path: str,
    x_col: str, y_col: str, friction_col: str,
    sep: str = "\t",
    combine: str = "sum",
) -> pd.DataFrame:
    """
    Load a friction file and clean it:
      - coordinates far outside the plausible range of the OTHER
        coordinates are dropped with a warning (malformed rows)
      - duplicated cells are combined: 'sum' (default, per spec -
        overlapping layers add up), 'max' or 'min'
    Returns a DataFrame with columns x, y, friction.
    """
    fr = pd.read_csv(path, sep=sep)
    fr = fr.rename(columns={x_col: "x", y_col: "y", friction_col: "friction"})
    fr = fr[["x", "y", "friction"]].copy()
    for c in fr.columns:
        fr[c] = pd.to_numeric(fr[c], errors="coerce")

    # crude malformed-coordinate detection: robust range fencing
    def fence(s):
        q1, q3 = s.quantile([0.01, 0.99])
        span = q3 - q1
        return (s < q1 - 5 * span) | (s > q3 + 5 * span)

    bad = fence(fr["x"]) | fence(fr["y"]) | fr.isna().any(axis=1)
    if bad.any():
        print(f"[friction] WARNING: dropping {bad.sum()} rows with "
              f"malformed/missing coordinates:")
        print(fr[bad].to_string(index=False))
        fr = fr[~bad]

    dups = fr.duplicated(["x", "y"]).sum()
    if dups:
        print(f"[friction] {dups} duplicated cells combined with "
              f"'{combine}' (overlapping layers).")
        fr = fr.groupby(["x", "y"], as_index=False)["friction"].agg(combine)

    print(f"[friction] {len(fr)} friction cells, values: "
          f"{sorted(fr['friction'].unique())}")
    return fr


def coverage_warning(pop_xy: pd.DataFrame, fr_xy: pd.DataFrame,
                     threshold: float = 0.80):
    """Spec section 12: warn if support data covers too little of the
    analysis extent (bounding-box overlap)."""
    px0, px1 = pop_xy["x"].min(), pop_xy["x"].max()
    py0, py1 = pop_xy["y"].min(), pop_xy["y"].max()
    fx0, fx1 = fr_xy["x"].min(), fr_xy["x"].max()
    fy0, fy1 = fr_xy["y"].min(), fr_xy["y"].max()
    ox = max(0, min(fx1, px1) - max(fx0, px0))
    oy = max(0, min(fy1, py1) - max(fy0, py0))
    area = (px1 - px0) * (py1 - py0)
    if area == 0:
        return 1.0        # degenerate extent (e.g. tiny synthetic tests)
    cov = (ox * oy) / area
    if cov < threshold:
        print(f"[friction] WARNING: friction data bounding box covers only "
              f"{cov*100:.1f}% of the analysis extent "
              f"(threshold {threshold*100:.0f}%). Cells outside receive "
              f"the default friction.")
    else:
        print(f"[friction] friction covers {cov*100:.1f}% of analysis extent.")
    return cov


class FrictionGrid:
    """
    The gridded study area as a graph, ready for per-origin
    friction-aware growth. Built once, reused for all origins.
    """

    def __init__(self, pop: pd.DataFrame, fr: pd.DataFrame | None,
                 unit_size: float = 100.0, default_friction: int = 0,
                 count_all_col: str = "count_all",
                 count_group_col: str = "count_group"):
        u = int(unit_size)
        self.unit_size = float(unit_size)

        # --- grid domain: bounding box of population + friction cells ---
        xs = [pop["x"]] + ([fr["x"]] if fr is not None else [])
        ys = [pop["y"]] + ([fr["y"]] if fr is not None else [])
        x0 = int(min(s.min() for s in xs)); x1 = int(max(s.max() for s in xs))
        y0 = int(min(s.min() for s in ys)); y1 = int(max(s.max() for s in ys))
        self.x0, self.y0 = x0, y0
        self.nx = (x1 - x0) // u + 1
        self.ny = (y1 - y0) // u + 1
        n = self.nx * self.ny
        print(f"[friction] grid domain {self.nx} x {self.ny} = {n} cells")

        def idx(x, y):
            return (((np.asarray(x) - x0) // u) * self.ny
                    + ((np.asarray(y) - y0) // u)).astype(np.int64)

        # --- per-node arrays ---
        self.friction = np.full(n, default_friction, dtype=np.int64)
        if fr is not None:
            self.friction[idx(fr["x"], fr["y"])] = fr["friction"].astype(int)

        self.count_all = np.zeros(n)
        self.count_group = np.zeros(n)
        pi = idx(pop["x"], pop["y"])
        self.count_all[pi] = pop[count_all_col].to_numpy()
        self.count_group[pi] = pop[count_group_col].to_numpy()
        self.pop_idx = np.asarray(pi)          # node index of populated cells
        self.pop_x = pop["x"].to_numpy()
        self.pop_y = pop["y"].to_numpy()

        # --- graph: 8-neighbour moves; entering node j costs 1+friction(j) ---
        rows, cols, data = [], [], []
        gx, gy = np.meshgrid(np.arange(self.nx), np.arange(self.ny),
                             indexing="ij")
        gx, gy = gx.ravel(), gy.ravel()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                ok = ((gx + dx >= 0) & (gx + dx < self.nx)
                      & (gy + dy >= 0) & (gy + dy < self.ny))
                src = gx[ok] * self.ny + gy[ok]
                dst = (gx[ok] + dx) * self.ny + (gy[ok] + dy)
                rows.append(src); cols.append(dst)
                data.append(1 + self.friction[dst])
        self.graph = csr_matrix(
            (np.concatenate(data),
             (np.concatenate(rows), np.concatenate(cols))),
            shape=(n, n))

    def rounds_from(self, origin_nodes: np.ndarray) -> np.ndarray:
        """Included-round of EVERY populated cell from each origin
        (chunk of origins), via Dijkstra. Shape: (len(origins), n_pop)."""
        d = dijkstra(self.graph, directed=True, indices=origin_nodes)
        return d[:, self.pop_idx]


def _count_from_grid(grid, pop, k_values, id_col, chunk, origins=None,
                     tau_values=None):
    """Shared origin loop: count cells in included-round order from a
    prepared grid (FrictionGrid or SlopeGrid). Tie convention: equal
    rounds form one atomic ring, as everywhere in EquiPop.

    origins : optional array of ROW indices into pop - compute results
    only for these origins (destination mass stays complete). Serves
    origin-subset workflows (validation subsamples, kFCA, backlog #11)."""
    k_values = sorted(k_values or [])
    tau_values = sorted(tau_values or [])
    if not (k_values or tau_values):
        raise ValueError("give k_values and/or tau_values")
    n_pop = len(grid.pop_idx)
    origins = np.arange(n_pop) if origins is None else np.asarray(origins)
    n_org = len(origins)
    ca, cg = grid.count_all[grid.pop_idx], grid.count_group[grid.pop_idx]
    results = []

    for start in range(0, n_org, chunk):
        sel = slice(start, min(start + chunk, n_org))
        rounds = grid.rounds_from(grid.pop_idx[origins[sel]])

        for r_i, oi in enumerate(origins[sel.start:sel.stop]):
            rr = rounds[r_i]
            order = np.argsort(rr, kind="stable")
            rec = {
                "Id": pop[id_col].iloc[oi] if id_col else oi,
                "EastWest": int(grid.pop_x[oi]),
                "NorthSouth": int(grid.pop_y[oi]),
                "CountAllLocal": ca[oi],
                "CountGroupLocal": cg[oi],
            }
            sum_all = sum_grp = 0.0
            dist_m = rounds_now = 0.0
            pending = list(k_values)
            pending_tau = list(tau_values)

            def rec_tau(tv):     # effort isochrone: everything within tv
                lab = f"tau{tv:g}"
                rec[f"N_{lab}"] = sum_all
                rec[f"T_{lab}"] = sum_grp
                rec[f"R_{lab}"] = (sum_grp / sum_all if sum_all
                                   else np.nan)

            j = 0
            while j < n_pop and (pending or pending_tau):
                r0 = rr[order[j]]
                if not np.isfinite(r0):
                    break
                while pending_tau and pending_tau[0] < r0 - 1e-9:
                    rec_tau(pending_tau.pop(0))
                ring = []
                while j < n_pop and rr[order[j]] == r0:
                    ring.append(order[j]); j += 1
                for ci in ring:
                    sum_all += ca[ci]; sum_grp += cg[ci]
                # distance to the LAST cell of the ring (any tie member)
                dist_m = float(np.hypot(grid.pop_x[ring[-1]] - grid.pop_x[oi],
                                        grid.pop_y[ring[-1]] - grid.pop_y[oi]))
                rounds_now = float(r0)
                while pending and sum_all >= pending[0]:
                    k = pending.pop(0)
                    rec[f"N_{k}"] = sum_all
                    rec[f"T_{k}"] = sum_grp
                    rec[f"R_{k}"] = sum_grp / sum_all
                    rec[f"Dist_{k}"] = dist_m
                    rec[f"Rounds_{k}"] = rounds_now
            for tv in pending_tau:  # isochrone swallows all reachable
                rec_tau(tv)
            for k in pending:      # unreached: partial (spec section 12)
                rec[f"N_{k}"] = sum_all
                rec[f"T_{k}"] = sum_grp
                rec[f"R_{k}"] = sum_grp / sum_all if sum_all else np.nan
                rec[f"Dist_{k}"] = dist_m
                rec[f"Rounds_{k}"] = rounds_now
            rec["SumN"] = sum_all
            rec["MaxDistance"] = dist_m
            results.append(rec)
        print(f"[friction] {min(start+chunk, n_org)}/{n_org} origins done")

    out = pd.DataFrame(results)
    fixed = ["Id", "EastWest", "NorthSouth", "CountAllLocal",
             "CountGroupLocal", "SumN", "MaxDistance"]
    per_k = [f"{p}_{k}" for k in k_values
             for p in ("N", "T", "R", "Dist", "Rounds")]
    per_tau = [f"{p}_tau{tv:g}" for tv in tau_values for p in ("N", "T", "R")]
    return out[fixed + per_k + per_tau]


def run_knn_friction(
    pop: pd.DataFrame,
    k_values: list[int],
    fr: pd.DataFrame | None = None,
    unit_size: float = 100.0,
    default_friction: int = 0,
    count_all_col: str = "count_all",
    count_group_col: str = "count_group",
    id_col: str | None = None,
    chunk: int = 250,
    origins=None,
    tau_values: list[float] | None = None,
) -> pd.DataFrame:
    """
    Friction-aware k-NN for aggregated cell data.

    pop : DataFrame with columns x, y (cell coordinates, any consistent
          convention), count_all_col, count_group_col.
    fr  : friction DataFrame (x, y, friction) on the SAME coordinate
          convention and grid, e.g. from load_friction_table(). None
          runs the model with uniform friction = default_friction
          (which with 0 reproduces radial-like growth in rounds space).

    Output: same standard columns as run_knn (short naming):
    Id, EastWest, NorthSouth, CountAllLocal, CountGroupLocal,
    N_k, T_k, R_k, Dist_k, plus Rounds_k (the friction-adjusted
    round at which k was reached - the friction analogue of distance).
    Dist_k remains the straight-line Cartesian distance to the cell
    where k was reached, as in the original EquiPop output.
    """
    if fr is not None:
        coverage_warning(pop, fr)
    grid = FrictionGrid(pop, fr, unit_size, default_friction,
                        count_all_col, count_group_col)

    if fr is not None:
        coverage_warning(pop, fr)
    grid = FrictionGrid(pop, fr, unit_size, default_friction,
                        count_all_col, count_group_col)
    return _count_from_grid(grid, pop, k_values, id_col, chunk, origins,
                            tau_values)
