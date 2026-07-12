"""
hex.py - hexagonal grids (backlog item 3, the X/Y/Z of the original spec).

CONVERT path: points are binned into a pointy-top hexagon tessellation
of user-chosen size, where `hex_size` is the width across flats - the
natural analogue of the square grid's unit_size (a 100 m hexagon and a
100 m square have the same midpoint-to-midpoint distance to their
lateral neighbours).

Internally, hexagons are indexed with AXIAL coordinates (q, r); the
third cube coordinate is implicit (s = -q-r), satisfying q+r+s = 0 -
the X/Y/Z of the specification. Assignment uses exact cube rounding.

The result is a standard CellData whose E/N are the hexagon CENTRE
coordinates (metric), and whose CellId is "q|r". This means the whole
radial statistics engine (run_knn_stats) works UNCHANGED - only the
binning geometry differs. (The 6-neighbour graph for hexagonal
FRICTION growth is a separate, future addition.)
"""

import numpy as np
import pandas as pd

from .cells import CellData


def _axial_from_xy(x, y, size):
    """Fractional axial coordinates for pointy-top hexagons of
    circumradius `size`."""
    q = (np.sqrt(3) / 3 * x - y / 3) / size
    r = (2 / 3 * y) / size
    return q, r


def _cube_round(qf, rf):
    """Exact cube rounding (Amit Patel's canonical algorithm)."""
    xf, zf = qf, rf
    yf = -xf - zf
    x, y, z = np.round(xf), np.round(yf), np.round(zf)
    dx, dy, dz = np.abs(x - xf), np.abs(y - yf), np.abs(z - zf)
    fix_x = (dx > dy) & (dx > dz)
    fix_z = ~fix_x & (dz > dy)
    x = np.where(fix_x, -y - z, x)
    z = np.where(fix_z, -x - y, z)
    return x.astype(np.int64), z.astype(np.int64)      # (q, r)


def _center_from_axial(q, r, size):
    cx = size * np.sqrt(3) * (q + r / 2.0)
    cy = size * 1.5 * r
    return cx, cy


def build_hex_cells(
    df: pd.DataFrame,
    e_col: str,
    n_col: str,
    hex_size: float = 100.0,
    binary_vars: list[str] | None = None,
    value_vars: list[str] | None = None,
) -> CellData:
    """
    Aggregate individual/point rows into hexagon cells.

    hex_size : width across flats in metres (lateral centre-to-centre
               distance), the hexagonal analogue of unit_size.

    Returns CellData with hexagon centres as E/N (floats), individual
    counts, binary sums and value arrays exactly like build_cells();
    CellId carries the axial index "q|r".
    """
    binary_vars = binary_vars or []
    value_vars = value_vars or []
    size = hex_size / np.sqrt(3)          # circumradius from flat width
    d = df.copy()
    for c in [e_col, n_col] + binary_vars + value_vars:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    bad = d[e_col].isna() | d[n_col].isna()
    if bad.any():
        print(f"[hex] WARNING: {bad.sum()} rows with missing coordinates "
              f"dropped.")
        d = d[~bad]

    qf, rf = _axial_from_xy(d[e_col].to_numpy(), d[n_col].to_numpy(), size)
    q, r = _cube_round(qf, rf)
    d["_q"], d["_r"] = q, r

    groups = d.groupby(["_q", "_r"], sort=True)
    Q, R, n = [], [], []
    bsums = {v: [] for v in binary_vars}
    varrs = {v: [] for v in value_vars}
    labels = []
    for (qq, rr), g in groups:
        Q.append(qq); R.append(rr); n.append(len(g))
        labels.append(f"{qq}|{rr}")
        for v in binary_vars:
            bsums[v].append(g[v].sum())
        for v in value_vars:
            varrs[v].append(g[v].dropna().to_numpy(dtype=float))

    Q, R = np.array(Q), np.array(R)
    cx, cy = _center_from_axial(Q, R, size)
    cd = CellData(
        E=cx, N=cy, n=np.array(n, dtype=np.int64),
        binary_sums={v: np.array(a, dtype=float) for v, a in bsums.items()},
        value_arrays=varrs, unit_size=hex_size, labels=labels)
    print(f"[hex] {len(d)} points -> {len(cd)} hexagons "
          f"(width {hex_size} m, global N = {cd.n.sum()})")
    return cd
