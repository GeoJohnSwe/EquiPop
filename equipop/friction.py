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
                 count_group_col: str = "count_group",
                 clip_margin: float = 5000.0,
                 max_graph_gb: float = 8.0):
        u = int(unit_size)
        self.unit_size = float(unit_size)

        # --- v1.16.6: guard, then CLIP, then build -------------------
        # Guard for the impossible (units that cannot belong to the
        # same map), clip the merely large (a national barrier layer
        # against a small study area), stay silent about the slightly
        # off (a lake reaching past the edge is normal).
        px0, px1 = float(pop["x"].min()), float(pop["x"].max())
        py0, py1 = float(pop["y"].min()), float(pop["y"].max())
        pw, ph = max(px1 - px0, u), max(py1 - py0, u)
        if fr is not None and len(fr):
            fx0, fx1 = float(fr["x"].min()), float(fr["x"].max())
            fy0, fy1 = float(fr["y"].min()), float(fr["y"].max())
            fw, fh = max(fx1 - fx0, u), max(fy1 - fy0, u)
            # separation between the two boxes (0 when they overlap);
            # measured, not area-based, so a line of points or a
            # barrier just outside the study area stays legitimate
            gap_x = max(0.0, max(px0, fx0) - min(px1, fx1))
            gap_y = max(0.0, max(py0, fy0) - min(py1, fy1))
            gap = float(np.hypot(gap_x, gap_y))
            scale = max(pw, ph)
            ratio = max(pw / fw, fw / pw, ph / fh, fh / ph)
            if gap > 100.0 * scale or ratio > 1000.0:
                raise ValueError(
                    "[friction] the barrier data and the population "
                    "do not belong to the same map:\n"
                    f"    population spans {pw:,.0f} x {ph:,.0f} m "
                    f"around ({px0:,.0f}, {py0:,.0f})\n"
                    f"    friction   spans {fw:,.0f} x {fh:,.0f} m "
                    f"around ({fx0:,.0f}, {fy0:,.0f})\n"
                    "Are they in the SAME coordinate system? Degrees "
                    "mixed with metres produce exactly this. Nothing "
                    "was computed.")
            # clip: friction is only relevant within reach of people
            margin = float(max(clip_margin, 2 * u))
            keep = ((fr["x"] >= px0 - margin) & (fr["x"] <= px1 + margin)
                    & (fr["y"] >= py0 - margin) & (fr["y"] <= py1 + margin))
            if not bool(keep.all()):
                dropped = int((~keep).sum())
                fr = fr[keep]
                print(f"[friction] {dropped} friction cells lie beyond "
                      f"the population extent (+{margin:,.0f} m) and "
                      "were clipped away - they cannot affect any "
                      "result")
                if not len(fr):
                    fr = None

        xs = [pop["x"]] + ([fr["x"]] if fr is not None else [])
        ys = [pop["y"]] + ([fr["y"]] if fr is not None else [])
        x0 = int(min(s.min() for s in xs)); x1 = int(max(s.max() for s in xs))
        y0 = int(min(s.min() for s in ys)); y1 = int(max(s.max() for s in ys))
        self.x0, self.y0 = x0, y0
        self.nx = (x1 - x0) // u + 1
        self.ny = (y1 - y0) // u + 1
        n = self.nx * self.ny
        need_gb = n * 8 * 8 / 1e9          # 8 edges x int64 per cell
        print(f"[friction] grid domain {self.nx} x {self.ny} = {n} "
              f"cells (~{need_gb:.1f} GB for the movement graph)")
        if need_gb > float(max_graph_gb):
            raise ValueError(
                f"[friction] this study area needs about {need_gb:.1f} "
                f"GB for the movement graph (limit {max_graph_gb:g} "
                "GB). The effort engines grid the WHOLE bounding box, "
                "empty ground included. Fixes: a smaller study area, "
                f"or a bigger cell size (at {2 * u} m it would need "
                f"~{need_gb / 4:.1f} GB). Nothing was computed.")

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


# ===================================================================
# v1.15.0 - features_to_friction: line/polygon features (rivers,
# rail, slow zones) -> additive friction cells at unit_size. Lives
# in the package so every door (ArcGIS, QGIS-future, Python, Stata)
# shares one tested rasterizer.
# ===================================================================

def features_to_friction(features, value_field: str = "friction",
                         unit_size: float = 100.0,
                         default_value: float | None = None,
                         agg: str = "sum"):
    """
    features : path to a vector file (shp/gpkg/geojson) or a
        GeoDataFrame of LINE and/or POLYGON features.
    value_field : column holding each feature's friction value; if
        absent and default_value is given, every feature costs that.
    Returns DataFrame(x, y, friction) of cell MIDPOINTS whose cell
    square the feature touches. Overlapping features stack
    ADDITIVELY (river + railway in one cell = both costs).
    """
    try:
        import geopandas as gpd
        from shapely.geometry import box
    except ImportError:
        raise ImportError("[friction] features_to_friction needs "
                          "geopandas: pip install geopandas")
    gdf = features if hasattr(features, "geometry") \
        else gpd.read_file(features)
    if value_field in gdf.columns:
        vals = gdf[value_field].astype(float).to_numpy()
    elif default_value is not None:
        vals = np.full(len(gdf), float(default_value))
        print(f"[friction] no '{value_field}' column - every feature "
              f"costs {default_value}")
    else:
        raise ValueError(f"[friction] features need a '{value_field}' "
                         "column or a default_value")
    if (vals < 0).any():
        raise ValueError("[friction] negative friction values - "
                         "speedups are not supported (yet); costs "
                         "must be >= 0")
    u = float(unit_size)
    acc: dict[tuple[float, float], list] = {}
    n_cells = 0
    for geom, v in zip(gdf.geometry, vals):
        if geom is None or geom.is_empty:
            continue
        # zero-measure contact (corner/edge kiss) costs nothing:
        # positive LENGTH for line features, positive AREA for
        # polygon features (a polygon touching a cell only along its
        # boundary has zero presence there; latent charge found by
        # the numpy-twin cross-check in v1.16)
        is_line = geom.geom_type in ("LineString", "MultiLineString",
                                     "LinearRing")
        x0, y0, x1, y1 = geom.bounds
        i0, i1 = int(np.floor(x0 / u)), int(np.floor(x1 / u))
        j0, j1 = int(np.floor(y0 / u)), int(np.floor(y1 / u))
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                cell = box(i * u, j * u, (i + 1) * u, (j + 1) * u)
                inter = geom.intersection(cell)
                if not inter.is_empty and (
                        getattr(inter, "length", 0.0) > 1e-9
                        if is_line else
                        getattr(inter, "area", 0.0) > 1e-9):
                    key = (i * u + u / 2, j * u + u / 2)
                    acc.setdefault(key, []).append(float(v))
                    n_cells += 1
    out = _agg_cells(acc, agg)
    print(f"[friction] {len(gdf)} features -> {len(out)} friction "
          f"cells at {u:g} m (additive"
          f"{'' if n_cells == len(out) else ', overlaps stacked'})")
    return out


# ---------------------------------------------- v1.16: GIS input rework
_AGG_FUNCS = {"sum": sum, "max": max, "min": min,
              "mean": lambda v: sum(v) / len(v)}


def _agg_cells(acc: dict, agg: str) -> pd.DataFrame:
    """acc maps cell midpoint -> list of feature values; combine per
    the overlap rule. 'sum' (ADDITIVE, the EquiPop default since the
    barrier model began: river + railway = both costs) or max / min /
    mean when overlap should not stack."""
    if agg not in _AGG_FUNCS:
        raise ValueError(f"[friction] unknown overlap rule '{agg}' - "
                         f"use one of {list(_AGG_FUNCS)}")
    f = _AGG_FUNCS[agg]
    out = pd.DataFrame([(k[0], k[1], float(f(v)))
                        for k, v in acc.items()],
                       columns=["x", "y", "friction"])
    n_multi = sum(1 for v in acc.values() if len(v) > 1)
    if n_multi:
        print(f"[friction] {n_multi} cells hit by several features - "
              f"overlap rule '{agg}' applied")
    return out


def _clip_len(x1, y1, x2, y2, X0, Y0, X1, Y1):
    """Length of segment (x1,y1)-(x2,y2) inside the CLOSED box
    [X0,X1]x[Y0,Y1] (Liang-Barsky parametric clip)."""
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - X0), (dx, X1 - x1),
                 (-dy, y1 - Y0), (dy, Y1 - y1)):
        if p == 0.0:
            if q < 0.0:
                return 0.0
        else:
            t = q / p
            if p < 0.0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return 0.0
    return (t1 - t0) * float(np.hypot(dx, dy))


def _ring_area(pts):
    """Signed shoelace area of a ring of (x, y) points."""
    if len(pts) < 3:
        return 0.0
    a = np.asarray(pts, float)
    x, y = a[:, 0], a[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1))
                       - np.dot(y, np.roll(x, -1)))


def _clip_ring(pts, X0, Y0, X1, Y1):
    """Sutherland-Hodgman clip of one ring against the box (zero-
    width bridges possible; the shoelace area stays exact)."""
    def clip_edge(poly, inside, cross):
        out = []
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            ia, ib = inside(a), inside(b)
            if ia:
                out.append(a)
                if not ib:
                    out.append(cross(a, b))
            elif ib:
                out.append(cross(a, b))
        return out

    def xcross(bound):
        def f(a, b):
            t = (bound - a[0]) / (b[0] - a[0])
            return (bound, a[1] + t * (b[1] - a[1]))
        return f

    def ycross(bound):
        def f(a, b):
            t = (bound - a[1]) / (b[1] - a[1])
            return (a[0] + t * (b[0] - a[0]), bound)
        return f

    poly = list(pts)
    for inside, cross in (
            (lambda p: p[0] >= X0, xcross(X0)),
            (lambda p: p[0] <= X1, xcross(X1)),
            (lambda p: p[1] >= Y0, ycross(Y0)),
            (lambda p: p[1] <= Y1, ycross(Y1))):
        if not poly:
            return []
        poly = clip_edge(poly, inside, cross)
    return poly


def paths_to_friction(features, values=None, unit_size: float = 100.0,
                      default_value: float | None = None,
                      agg: str = "sum") -> pd.DataFrame:
    """
    Geopandas-FREE geometry-to-grid: coordinate paths -> friction
    cells, for hosts whose Python cannot grow geopandas (the ArcGIS
    Pro clone). Validated cell-for-cell against features_to_friction.
    Conventions shared by both: a cell is charged when the feature's
    presence has positive measure (length for lines, area for
    polygons); corner/edge kisses free; one feature charges a cell
    at most ONCE; overlap combined per `agg` (sum = additive default).

    features : list of dicts:
        {"type": "line",    "parts": [[(x, y), ...], ...]}
        {"type": "polygon", "parts": [[exterior_ring, hole_ring, ...],
                                      ...]}
        (first ring per part = exterior, later rings = holes; the
        arcpy part convention).
    Returns DataFrame(x, y, friction) of charged cell MIDPOINTS.
    """
    n = len(features)
    if values is not None:
        vals = np.asarray(values, float)
        if len(vals) != n:
            raise ValueError(f"[friction] {n} features but "
                             f"{len(vals)} values")
    elif default_value is not None:
        vals = np.full(n, float(default_value))
        print(f"[friction] no values given - every feature costs "
              f"{default_value}")
    else:
        raise ValueError("[friction] paths_to_friction needs values "
                         "or a default_value")
    if np.isnan(vals).any():
        raise ValueError("[friction] missing (null) friction values - "
                         "fill or filter the value field first")
    if (vals < 0).any():
        raise ValueError("[friction] negative friction values - "
                         "speedups are not supported (yet); costs "
                         "must be >= 0")
    u = float(unit_size)
    acc: dict[tuple[float, float], list] = {}
    for feat, v in zip(features, vals):
        gtype = str(feat.get("type", "line")).lower()
        parts = feat.get("parts") or []
        measure: dict[tuple[int, int], float] = {}
        if gtype.startswith("line"):
            for part in parts:
                pts = [(float(p[0]), float(p[1])) for p in part
                       if p is not None]
                for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
                    i0 = int(np.floor(min(x1, x2) / u))
                    i1 = int(np.floor(max(x1, x2) / u))
                    j0 = int(np.floor(min(y1, y2) / u))
                    j1 = int(np.floor(max(y1, y2) / u))
                    for i in range(i0, i1 + 1):
                        for j in range(j0, j1 + 1):
                            L = _clip_len(x1, y1, x2, y2, i * u,
                                          j * u, (i + 1) * u,
                                          (j + 1) * u)
                            if L > 0.0:
                                measure[(i, j)] = measure.get(
                                    (i, j), 0.0) + L
        elif gtype.startswith("poly"):
            for part in parts:
                rings = [[(float(p[0]), float(p[1])) for p in ring
                          if p is not None] for ring in part]
                rings = [r for r in rings if len(r) >= 3]
                if not rings:
                    continue
                for ri, ring in enumerate(rings):
                    a = _ring_area(ring)
                    if (ri == 0 and a < 0) or (ri > 0 and a > 0):
                        rings[ri] = ring[::-1]     # ext +, holes -
                allp = np.asarray([p for r in rings for p in r], float)
                i0 = int(np.floor(allp[:, 0].min() / u))
                i1 = int(np.floor(allp[:, 0].max() / u))
                j0 = int(np.floor(allp[:, 1].min() / u))
                j1 = int(np.floor(allp[:, 1].max() / u))
                for i in range(i0, i1 + 1):
                    for j in range(j0, j1 + 1):
                        A = 0.0
                        for ring in rings:
                            A += _ring_area(_clip_ring(
                                ring, i * u, j * u, (i + 1) * u,
                                (j + 1) * u))
                        if A > 0.0:
                            measure[(i, j)] = measure.get(
                                (i, j), 0.0) + A
        else:
            raise ValueError(f"[friction] unknown feature type "
                             f"'{gtype}' - line or polygon")
        for (i, j), m in measure.items():
            if m > 1e-9:
                acc.setdefault((i * u + u / 2, j * u + u / 2),
                               []).append(float(v))
    out = _agg_cells(acc, agg)
    print(f"[friction] {n} features -> {len(out)} friction cells at "
          f"{u:g} m (overlap rule: {agg})")
    return out


def points_to_friction(x, y, values, unit_size: float = 100.0,
                       agg: str = "sum") -> pd.DataFrame:
    """Point features / tabular rows -> friction cells: each point
    snaps to its cell; several points in one cell combine per the
    overlap rule (sum = additive default). NaN coordinates or values
    are refused loudly - fix the data, don't guess."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    v = np.asarray(values, float)
    if len(x) != len(y) or len(x) != len(v):
        raise ValueError("[friction] x, y and values must be equal "
                         "length")
    bad = ~(np.isfinite(x) & np.isfinite(y) & np.isfinite(v))
    if bad.any():
        raise ValueError(f"[friction] {int(bad.sum())} rows with "
                         "missing coordinates or friction values - "
                         "fill or filter them first")
    if (v < 0).any():
        raise ValueError("[friction] negative friction values - "
                         "costs must be >= 0")
    u = float(unit_size)
    acc: dict[tuple[float, float], list] = {}
    for xi, yi, vi in zip(x, y, v):
        key = (np.floor(xi / u) * u + u / 2,
               np.floor(yi / u) * u + u / 2)
        acc.setdefault(key, []).append(float(vi))
    out = _agg_cells(acc, agg)
    print(f"[friction] {len(x)} points -> {len(out)} friction cells "
          f"at {u:g} m (overlap rule: {agg})")
    return out


def raster_to_friction(arr, x_min: float, y_max: float,
                       cell_w: float, cell_h: float,
                       unit_size: float = 100.0,
                       nodata=None) -> pd.DataFrame:
    """Georeferenced raster -> friction cells by CELL-MIDPOINT
    sampling (the extract-values-to-points idea): every analysis
    cell whose midpoint falls inside the raster reads the pixel
    under that midpoint (nearest, no interpolation). NoData and
    zero pixels charge nothing.

    arr : 2-D array, row 0 = TOP of the raster (the GIS convention);
    x_min, y_max : coordinates of the raster's upper-left corner;
    cell_w, cell_h : pixel size in metres (both positive).
    """
    a = np.asarray(arr, float)
    if a.ndim != 2:
        raise ValueError("[friction] raster must be a single band "
                         f"(2-D), got shape {a.shape}")
    if nodata is not None:
        a = np.where(a == nodata, np.nan, a)
    u = float(unit_size)
    nrow, ncol = a.shape
    x_max = x_min + ncol * cell_w
    y_min = y_max - nrow * cell_h
    i0 = int(np.floor(x_min / u))
    i1 = int(np.floor((x_max - 1e-9) / u))
    j0 = int(np.floor(y_min / u))
    j1 = int(np.floor((y_max - 1e-9) / u))
    xs, ys, fs = [], [], []
    for i in range(i0, i1 + 1):
        mx = i * u + u / 2
        if not (x_min <= mx < x_max):
            continue
        col = int((mx - x_min) / cell_w)
        for j in range(j0, j1 + 1):
            my = j * u + u / 2
            if not (y_min < my <= y_max):
                continue
            row = int((y_max - my) / cell_h)
            val = a[row, col]
            if np.isfinite(val) and val > 0:
                xs.append(mx); ys.append(my); fs.append(float(val))
    if fs and min(fs) < 0:
        raise ValueError("[friction] negative friction values in the "
                         "raster - costs must be >= 0")
    out = pd.DataFrame({"x": xs, "y": ys, "friction": fs})
    print(f"[friction] raster {nrow}x{ncol} px -> {len(out)} friction "
          f"cells at {u:g} m (midpoint sampling; NoData/zero free)")
    return out
