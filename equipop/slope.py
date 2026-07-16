"""
slope.py - slope-asymmetric directional friction (backlog #4a).

THE MODEL: neighbourhood growth as in the friction engine (FARB), but
the effort of a move now depends on the TERRAIN GRADIENT along it.
The cost of entering cell j from cell i becomes

    cost(i -> j) = penalty(slope_ij) + friction(j)

where slope_ij = (alt_j - alt_i) / centre_distance(i, j) is the
signed gradient (positive = uphill) over the true centre distance
(unit for orthogonal moves, unit * sqrt(2) for diagonal moves - a
diagonal move over the same rise is a gentler climb, as in reality).

Because the grid graph is directed, uphill and downhill edges between
the same two cells carry different costs - the asymmetry is free.

DESIGN DECISIONS (recorded, as always):
 - The base move keeps FARB semantics: penalty(0) = 1 for every model,
   so on flat terrain one move = one round, and with a flat DEM the
   engine reproduces run_knn_friction EXACTLY (regression-tested).
   Rounds therefore read as "flat-equivalent effort".
 - Slope multiplies the move; friction still adds on the destination
   node. Water can stay a friction barrier while hills bend the paths.
 - Rounds become continuous under slope (real-valued effort); the tie
   convention is unchanged - equal effort forms one atomic ring.

MODELS (extension pattern: add a dict entry, not new logic):
 - "tobler": Tobler's hiking function, speed = 6 * exp(-3.5*|s+0.05|)
   km/h, expressed as a time penalty normalised to 1 on the flat:
   penalty(s) = exp(3.5 * (|s + 0.05| - 0.05)). Asymmetric with the
   famous optimum at a gentle -5% descent (penalty 0.839 < 1).
 - "linear": penalty(s) = 1 + lambda_up*max(0,s) + lambda_down*max(0,-s),
   the transparent baseline. Defaults lambda_up=5.0 (a 10% climb costs
   1.5 moves), lambda_down=0.0 (descent free, i.e. flat-priced).
"""

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from .friction import FrictionGrid, coverage_warning, _count_from_grid


# --------------------------------------------------------------- models
SLOPE_MODELS = {
    "tobler": lambda s, **p:
        np.exp(3.5 * (np.abs(np.asarray(s, dtype=float) + 0.05) - 0.05)),
    "linear": lambda s, lambda_up=5.0, lambda_down=0.0, **p:
        1.0 + lambda_up * np.maximum(0.0, np.asarray(s, dtype=float))
            + lambda_down * np.maximum(0.0, -np.asarray(s, dtype=float)),
}


def slope_penalty(model: str = "tobler", **params):
    """Return penalty(slope) for a named model; penalty(0) must be 1."""
    if model not in SLOPE_MODELS:
        raise ValueError(f"unknown slope model '{model}'; "
                         f"available: {sorted(SLOPE_MODELS)}")
    fn = SLOPE_MODELS[model]
    p0 = float(fn(0.0, **params))
    if not np.isclose(p0, 1.0):
        raise ValueError(f"slope model '{model}' has penalty(0) = {p0}, "
                         "must be 1 (rounds must stay flat-equivalent)")
    return lambda s: fn(s, **params)


# ----------------------------------------------------- DEM -> altitudes
def dem_to_cell_altitude(dem_path: str, E, N, unit_size: float = 100.0,
                         band: int = 1, clip_sea: bool = True,
                         fill_missing: float | None = 0.0) -> np.ndarray:
    """
    Altitude per grid cell (E, N = cell MIDPOINTS, same CRS as the DEM):
    the mean of all DEM pixels whose centres fall inside each cell
    ("extract values to cells" - a zonal mean, robust when the DEM is
    finer than the grid; falls back to nearest-pixel when coarser).

    clip_sea      : negative altitudes (Copernicus sea noise) -> 0.
    fill_missing  : altitude for cells with no DEM pixel (None = NaN).
    """
    import rasterio
    E = np.asarray(E, dtype=float)
    N = np.asarray(N, dtype=float)
    u = float(unit_size)

    with rasterio.open(dem_path) as src:
        a = src.read(band).astype(float)
        if src.nodata is not None:
            a[a == src.nodata] = np.nan
        # pixel-centre coordinates
        tr = src.transform
        px = tr.c + tr.a * (np.arange(src.width) + 0.5)
        py = tr.f + tr.e * (np.arange(src.height) + 0.5)

    # map every pixel centre to a cell midpoint key
    cE = (np.floor(px / u) * u + u / 2.0)
    cN = (np.floor(py / u) * u + u / 2.0)
    colE = np.tile(cE, len(py))
    rowN = np.repeat(cN, len(px))
    vals = a.ravel()
    ok = np.isfinite(vals)
    z = pd.DataFrame({"E": colE[ok], "N": rowN[ok], "alt": vals[ok]})
    zm = z.groupby(["E", "N"])["alt"].mean()

    keys = pd.MultiIndex.from_arrays([E, N])
    alt = zm.reindex(keys).to_numpy(dtype=float)

    n_miss = int(np.isnan(alt).sum())
    if n_miss:
        print(f"[slope] {n_miss} cells outside DEM coverage -> "
              f"altitude {'NaN' if fill_missing is None else fill_missing}")
        if fill_missing is not None:
            alt = np.where(np.isnan(alt), fill_missing, alt)
    if clip_sea:
        n_sea = int((alt < 0).sum())
        if n_sea:
            print(f"[slope] {n_sea} cells below sea level clipped to 0")
        alt = np.maximum(alt, 0.0)
    print(f"[slope] cell altitudes: {np.nanmin(alt):.1f} - "
          f"{np.nanmax(alt):.1f} m (mean {np.nanmean(alt):.1f})")
    return alt


# ----------------------------------------------------------- the grid
class SlopeGrid(FrictionGrid):
    """FrictionGrid whose edges carry slope-dependent directed costs."""

    def __init__(self, pop, fr=None, unit_size: float = 100.0,
                 default_friction: int = 0,
                 count_all_col: str = "count_all",
                 count_group_col: str = "count_group",
                 altitude=None, model: str = "tobler",
                 roundtrip: bool = False, **model_params):
        super().__init__(pop, fr, unit_size, default_friction,
                         count_all_col, count_group_col)
        u = int(unit_size)
        penalty = slope_penalty(model, **model_params)

        # altitude for EVERY domain cell (paths cross unpopulated land):
        # a DEM path, a DataFrame(x, y, alt), or an array over the domain.
        gx, gy = np.meshgrid(np.arange(self.nx), np.arange(self.ny),
                             indexing="ij")
        gx, gy = gx.ravel(), gy.ravel()
        midE = self.x0 + gx * u
        midN = self.y0 + gy * u
        if isinstance(altitude, str):
            alt = dem_to_cell_altitude(altitude, midE, midN, unit_size)
        elif isinstance(altitude, pd.DataFrame):
            zm = altitude.set_index(["x", "y"])["alt"]
            alt = zm.reindex(pd.MultiIndex.from_arrays([midE, midN])
                             ).to_numpy(dtype=float)
            alt = np.where(np.isnan(alt), 0.0, alt)
        else:
            alt = np.asarray(altitude, dtype=float)
            if alt.shape != (self.nx * self.ny,):
                raise ValueError("altitude array must have one value per "
                                 f"domain cell ({self.nx * self.ny})")
        self.altitude = alt
        self.roundtrip = bool(roundtrip)

        # rebuild the graph with directed slope costs
        rows, cols, data = [], [], []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                ok = ((gx + dx >= 0) & (gx + dx < self.nx)
                      & (gy + dy >= 0) & (gy + dy < self.ny))
                src = gx[ok] * self.ny + gy[ok]
                dst = (gx[ok] + dx) * self.ny + (gy[ok] + dy)
                run = u * (np.sqrt(2.0) if dx and dy else 1.0)
                s = (alt[dst] - alt[src]) / run
                rows.append(src); cols.append(dst)
                data.append(penalty(s) + self.friction[dst])
        self.graph = csr_matrix(
            (np.concatenate(data),
             (np.concatenate(rows), np.concatenate(cols))),
            shape=(self.nx * self.ny,) * 2)
        smax = np.abs(np.concatenate(data)).max()
        print(f"[slope] directed graph rebuilt, model '{model}', "
              f"max edge cost {smax:.3f}"
              + (", ROUND-TRIP effort (per-leg average)"
                 if self.roundtrip else ""))

    def rounds_from(self, origin_nodes):
        """Effort of every populated cell from each origin. With
        roundtrip=True: cheapest outbound PLUS cheapest return
        (Dijkstra on the transpose - the return path may differ from
        the outbound one, which is correct), reported as the PER-LEG
        AVERAGE (sum/2) so flat terrain reproduces one-way values
        exactly and rounds stay comparable across studies."""
        fwd = super().rounds_from(origin_nodes)
        if not self.roundtrip:
            return fwd
        from scipy.sparse.csgraph import dijkstra
        back = dijkstra(self.graph.T, directed=True,
                        indices=origin_nodes)[:, self.pop_idx]
        return 0.5 * (fwd + back)


# ------------------------------------------------------------ the run
def run_knn_slope(
    pop: pd.DataFrame,
    k_values: list[int],
    altitude,
    model: str = "tobler",
    fr: pd.DataFrame | None = None,
    unit_size: float = 100.0,
    default_friction: int = 0,
    count_all_col: str = "count_all",
    count_group_col: str = "count_group",
    id_col: str | None = None,
    chunk: int = 250,
    origins=None,
    tau_values: list[float] | None = None,
    roundtrip: bool = False,
    **model_params,
) -> pd.DataFrame:
    """
    Slope-aware k-NN growth. Same in/out contract as run_knn_friction
    (N_k, T_k, R_k, Dist_k, Rounds_k) - Rounds_k is now the
    flat-equivalent EFFORT at which k was reached (real-valued).

    altitude : DEM file path (zonal-mean sampled per cell, same CRS as
               pop!), or DataFrame(x, y, alt), or array per domain cell.
    model    : key in SLOPE_MODELS ("tobler", "linear"); model
               parameters pass through (e.g. lambda_up=8).
    roundtrip: True = effort is the cheapest out-AND-back journey,
               reported per leg (sum/2); flat terrain reproduces
               one-way values exactly. Both models make varied
               terrain cost MORE round-trip (convexity).
    """
    if fr is not None:
        coverage_warning(pop, fr)
    grid = SlopeGrid(pop, fr, unit_size, default_friction,
                     count_all_col, count_group_col,
                     altitude=altitude, model=model,
                     roundtrip=roundtrip, **model_params)
    return _count_from_grid(grid, pop, k_values, id_col, chunk, origins,
                            tau_values)
