"""
access.py - access potential and the opportunity horizon (#15).

THE IDEA: with distance decay, access to opportunities from a point is
the Hansen (1959) potential

    A(x) = sum_j  w(d(x, j)) * mass_j

Nearby area is small (few opportunities), far area is heavily decayed;
between them, with uniform opportunity density, the marginal access
arriving from distance r follows r * w(r) - for negexp a Gamma(2)
density - peaking at the OPPORTUNITY HORIZON r* (= h/ln 2 for negexp).

THREE TOOLS:

- potential_surface(mass, decay, ...): A(x) for EVERY grid midpoint in
  the domain, populated or not, via FFT convolution. On a regular grid
  the pairwise midpoint distances are exactly the kernel offsets, so
  the FFT result is EXACT (to float precision) up to the eps
  truncation of the kernel - no approximation, no iterations. The same
  function computes the POI-PLACEMENT SURPLUS: pass population as the
  mass, and A(x) is the access gained by everyone if a new opportunity
  opens at x (the reverse potential). Competition effects (a new POI
  stealing catchment) are deliberately out of scope here - that is the
  FCA family (backlog #11).

- opportunity_horizon(decay): the distance from which the most access
  arrives (argmax of r * w(r)); analytic h/ln2 ~ 1.4427h for negexp,
  numeric for every model.

- effort_potential(...): the potential with Euclidean distance
  replaced by FRICTION/SLOPE EFFORT (optionally round-trip) - access
  that respects hills and barriers. The decay half-life is then in
  EFFORT ROUNDS, not metres (stated loudly at run time).
"""

import numpy as np
import pandas as pd

from .decay import Decay


# ------------------------------------------------------------- horizon
def opportunity_horizon(decay: Decay, r_max: float | None = None,
                        n: int = 200_000) -> float:
    """Distance r* from which the most access arrives under uniform
    opportunity density: argmax of r * w(r). Analytic for negexp
    (1/|beta| = half_life/ln2); numeric argmax for every model."""
    if decay.model == "negexp" and decay.gamma is None:
        return -1.0 / decay.beta
    if decay.model == "power" and decay.gamma is not None:
        # analytic for the shifted power: argmax of r*(1+s*r)^(-g)
        # exists only for g > 1 (heavier tails: access keeps arriving
        # from ever farther out - the horizon is infinite, loudly).
        g = float(decay.gamma)
        if g <= 1.0:
            print("[access] power gamma <= 1: r*w(r) has no interior "
                  "maximum - the opportunity horizon is INFINITE")
            return np.inf
        s = (2.0 ** (1.0 / g) - 1.0) / decay.half_life_m
        return 1.0 / (s * (g - 1.0))
    r_max = r_max or decay.truncation_radius(1e-9)
    r = np.linspace(0.0, r_max, n)                 # coarse pass
    r0 = r[np.argmax(r * decay.weight_vec(r))]
    step = r_max / (n - 1)                         # fine pass around r0
    rf = np.linspace(max(0.0, r0 - 2 * step), r0 + 2 * step, n)
    return float(rf[np.argmax(rf * decay.weight_vec(rf))])


# ------------------------------------------------- FFT potential field
def potential_surface(mass: pd.DataFrame, decay: Decay,
                      unit_size: float = 100.0,
                      x_col: str = "x", y_col: str = "y",
                      mass_col: str = "mass",
                      eps: float = 1e-6,
                      pad_cells: int | None = None) -> pd.DataFrame:
    """
    Hansen access potential A(x) = sum_j w(d) * mass_j for EVERY grid
    midpoint in the (padded) bounding box of the mass cells.

    mass : DataFrame of cell midpoints (x_col, y_col) and mass_col -
           opportunities (POIs, jobs, beds ...) for an ACCESS surface,
           or population for a POI-PLACEMENT SURPLUS surface.
    pad_cells : extra empty cells around the bbox (default: kernel
           radius, so no reachable midpoint is cut off).

    Exact-by-construction: grid-to-grid distances ARE the kernel
    offsets; truncation at weight < eps is the only cutoff (printed).
    """
    from scipy.signal import fftconvolve

    u = float(unit_size)
    half = u / 2.0
    E = (np.floor(mass[x_col].to_numpy(float) / u) * u + half)
    N = (np.floor(mass[y_col].to_numpy(float) / u) * u + half)
    m = mass[mass_col].to_numpy(float)

    trunc = decay.truncation_radius(eps)
    kr = int(np.ceil(trunc / u))               # kernel radius in cells
    pad = kr if pad_cells is None else int(pad_cells)

    x0, y0 = E.min() - pad * u, N.min() - pad * u
    nx = int(round((E.max() - E.min()) / u)) + 1 + 2 * pad
    ny = int(round((N.max() - N.min()) / u)) + 1 + 2 * pad
    gi = np.round((E - x0) / u).astype(int)
    gj = np.round((N - y0) / u).astype(int)
    grid = np.zeros((nx, ny))
    np.add.at(grid, (gi, gj), m)

    off = np.arange(-kr, kr + 1) * u
    dx, dy = np.meshgrid(off, off, indexing="ij")
    kern = decay.weight_vec(np.hypot(dx, dy))
    kern[kern < eps] = 0.0

    print(f"[access] surface {nx} x {ny} cells, kernel radius {kr} "
          f"cells ({trunc:,.0f} m at eps {eps:g}), FFT convolution")
    A = fftconvolve(grid, kern, mode="same")
    A[A < 0] = 0.0                              # FFT float dust

    gx, gy = np.meshgrid(np.arange(nx), np.arange(ny), indexing="ij")
    out = pd.DataFrame({"x": x0 + gx.ravel() * u,
                        "y": y0 + gy.ravel() * u,
                        "potential": A.ravel()})
    print(f"[access] peak potential {out.potential.max():,.2f} | "
          f"opportunity horizon r* = "
          f"{opportunity_horizon(decay):,.0f} (same units as decay)")
    return out


# ------------------------------------------------- effort-based access
def effort_potential(pop: pd.DataFrame, mass: pd.DataFrame,
                     decay_effort: Decay,
                     altitude=None, model: str = "tobler",
                     roundtrip: bool = True,
                     fr: pd.DataFrame | None = None,
                     unit_size: float = 100.0,
                     origins=None, chunk: int = 250,
                     mass_col: str = "mass",
                     **model_params) -> pd.DataFrame:
    """
    Access potential over FRICTION/SLOPE EFFORT instead of Euclidean
    distance: A_i = sum_j w(effort_ij) * mass_j, with effort from the
    slope engine (roundtrip=True: cheapest out-and-back, per-leg
    average - "you must also come home").

    pop  : cells DataFrame (x, y, count_all[, count_group]) - defines
           the domain and the origins.
    mass : cells DataFrame (x, y, mass_col) of opportunities; snapped
           onto the same grid; mass outside the pop domain is dropped
           loudly.
    decay_effort : Decay whose half-life is in EFFORT ROUNDS.

    Returns one row per origin: x, y, A (and Rounds-to-horizon later
    generations may add). origins= subsets as in run_knn_slope.
    """
    from .slope import SlopeGrid

    print(f"[access] EFFORT potential: decay half-life is in ROUNDS "
          f"(flat-equivalent moves), not metres")
    if "count_group" not in pop.columns:
        pop = pop.assign(count_group=0.0)
    grid = SlopeGrid(pop, fr, unit_size, 0, "count_all", "count_group",
                     altitude=altitude, model=model,
                     roundtrip=roundtrip, **model_params)

    # snap mass onto the domain's nodes
    u = int(unit_size)
    mi = (((np.floor(mass["x"].to_numpy(float) / u) * u + u / 2)
           - grid.x0) // u).astype(np.int64)
    mj = (((np.floor(mass["y"].to_numpy(float) / u) * u + u / 2)
           - grid.y0) // u).astype(np.int64)
    ok = (mi >= 0) & (mi < grid.nx) & (mj >= 0) & (mj < grid.ny)
    if (~ok).any():
        print(f"[access] {(~ok).sum()} mass cells outside the pop "
              "domain dropped (loudly)")
    nodes = np.asarray(mi[ok] * grid.ny + mj[ok])
    mvals = mass[mass_col].to_numpy(float)[ok]
    node_mass = np.zeros(grid.nx * grid.ny)
    np.add.at(node_mass, nodes, mvals)
    mass_nodes = np.flatnonzero(node_mass > 0)
    mass_m = node_mass[mass_nodes]

    n_pop = len(grid.pop_idx)
    origins = np.arange(n_pop) if origins is None \
        else np.asarray(origins)
    rows = []
    from scipy.sparse.csgraph import dijkstra
    for start in range(0, len(origins), chunk):
        sel = origins[start:min(start + chunk, len(origins))]
        eff = dijkstra(grid.graph, directed=True,
                       indices=grid.pop_idx[sel])[:, mass_nodes]
        if roundtrip:
            back = dijkstra(grid.graph.T, directed=True,
                            indices=grid.pop_idx[sel])[:, mass_nodes]
            eff = 0.5 * (eff + back)
        w = np.where(np.isfinite(eff),
                     decay_effort.weight_vec(np.where(
                         np.isfinite(eff), eff, 0.0)), 0.0)
        A = w @ mass_m
        for r_i, oi in enumerate(sel):
            rows.append({"x": float(grid.pop_x[oi]),
                         "y": float(grid.pop_y[oi]),
                         "A": float(A[r_i])})
        print(f"[access] {min(start+chunk, len(origins))}"
              f"/{len(origins)} origins done")
    return pd.DataFrame(rows)
