"""
latticejoin.py - put a POINT LAYER onto the raster lattice.

BACKLOG 220. John's idea, narrowed.

QGIS ALREADY COUNTS POINTS IN CELLS AND DOES IT WELL, so this is not
a reimplementation of that. THE HARD PART IS THE LATTICE. EquiPop
knows the exact grid the demographic points sit on - the one
rasterfolder built from the rasters' own transform - and QGIS does
not. A join done outside is a spatial join with tolerances, and at
cell boundaries you cannot say which cell a supermarket landed in.
Here the answer is exact, because the grid is ours.

AND THE POINT OF IT IS NOT THE COUNT. Once supermarkets are on the
lattice, "how many supermarkets in this cell" is almost always zero
and almost never the question. The question is HOW MANY AMONG THE k
NEAREST PEOPLE - which is two-step floating catchment area, and
equipop/fca.py already has it: fca(), fca_segments(),
fca_propensity(), all tested. Demographics are the demand side, these
are the supply side, and the neighbourhood is the same k in both.

So the output of this module is shaped to go straight into fca():
a frame with x, y and a supply column.

    from equipop.latticejoin import snap_to_lattice
    supply = snap_to_lattice(lon, lat, like="Africa/", name="shops")
    # -> lon, lat, gx, gy, shops   with one row per OCCUPIED cell
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class LatticeError(Exception):
    """Refused before anything ran, with the reason in plain words."""


def lattice_of(folders):
    """The grid a folder of rasters defines: origin, pixel, CRS.

    Read from the FIRST raster, exactly as rasterfolder does, so a
    join lands on the same integer indices the points carry.
    """
    from .rasterfolder import _tif_paths

    try:
        import rasterio
    except ImportError as e:                       # pragma: no cover
        raise LatticeError("Reading a raster lattice needs rasterio: "
                           "pip install rasterio") from e

    paths = _tif_paths(folders)
    if not paths:
        raise LatticeError(
            f"No rasters found under {folders}, so there is no lattice "
            "to snap to. Point this at the same folder the points came "
            "from.")
    with rasterio.open(paths[0]) as r:
        t = r.transform
        return {"c": t.c, "f": t.f, "a": t.a, "e": t.e,
                "crs": str(r.crs), "from": paths[0]}


def snap_to_lattice(x, y, *, like=None, lattice=None, values=None,
                    name="count", how="count"):
    """Count or sum a set of points onto the raster lattice.

    x, y     : coordinates IN THE LATTICE'S OWN CRS - degrees for
              WorldPop. Reprojecting is the door's job, not this
              function's, because only the door knows what the layer
              was in. THE CRS IS RETURNED BY lattice_of() AND MUST BE
              CHECKED: a coordinate is a pair of numbers and carries
              no world with it, so passing metres to a degree lattice
              lands everything in one cell near the origin without a
              word of complaint. BACKLOG 239 was the same mistake one
              level up, where two rasters with numerically identical
              transforms were merged across 3,300 km.
    like    : the raster folder whose grid to use; or pass `lattice`.
    values  : a value per point, when how='sum'. Ignored for 'count'.
    how     : 'count' - how many points fell in the cell
              'sum'   - the total of `values` in the cell

    Returns one row per OCCUPIED cell: lon, lat (cell centres), gx, gy
    (the integer lattice indices, so it joins to a point table exactly
    and not by distance), and the named column.

    EMPTY CELLS ARE NOT LISTED. A supermarket layer touches a
    vanishing fraction of a continent, and a row of zeros for every
    other cell would be tens of millions of rows saying nothing. Join
    it to the point table and fill with 0 there - which is the same
    rule the raster loader uses for a layer with nothing at a pixel.
    """
    if how not in ("count", "sum"):
        raise LatticeError(
            f"how must be 'count' or 'sum'; got {how!r}.")
    if lattice is None:
        if like is None:
            raise LatticeError(
                "Which lattice? Pass like='<the raster folder>' so the "
                "join lands on the same grid as the points.")
        lattice = lattice_of(like)

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.shape != y.shape:
        raise LatticeError(
            f"{x.size} x values against {y.size} y values.")
    if how == "sum":
        if values is None:
            raise LatticeError(
                "how='sum' needs a value per point - which field is "
                "being added up?")
        v = np.asarray(values, dtype=float)
        if v.shape != x.shape:
            raise LatticeError(
                f"{v.size} values against {x.size} points.")
    else:
        v = np.ones(x.shape, dtype=float)

    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(v)
    if not ok.any():
        raise LatticeError(
            "No usable coordinates - every point is missing an x, a y "
            "or a value.")

    # THE SAME ARITHMETIC rasterfolder USES, so the indices match.
    # floor, not round: a cell owns [origin, origin+pixel), and
    # rounding would give a point on a boundary to whichever cell it
    # is nearer the centre of, which is not the same rule the raster
    # reader applied to its own pixels.
    gx = np.floor((x[ok] - lattice["c"]) / lattice["a"]).astype(np.int64)
    gy = np.floor((y[ok] - lattice["f"]) / lattice["e"]).astype(np.int64)

    got = (pd.DataFrame({"gx": gx, "gy": gy, name: v[ok]})
           .groupby(["gx", "gy"], as_index=False)[name].sum())

    got["lon"] = lattice["c"] + (got["gx"] + 0.5) * lattice["a"]
    got["lat"] = lattice["f"] + (got["gy"] + 0.5) * lattice["e"]
    dropped = int((~ok).sum())
    print(f"[lattice] {int(ok.sum()):,} of {x.size:,} points -> "
          f"{len(got):,} occupied cells"
          + (f" ({dropped:,} had no usable coordinate)" if dropped else ""))
    return got[["lon", "lat", "gx", "gy", name]]


def join_to_points(points, snapped, name, fill=0.0):
    """Put a snapped layer onto an existing point table.

    Joins on the INTEGER LATTICE INDICES, never on distance, so a
    supermarket is either in a cell or it is not - no tolerance, no
    nearly. Cells the layer never touched get `fill`, which is a real
    0.0 and not an absence, the same rule the raster loader follows.
    """
    if "gx" not in points.columns or "gy" not in points.columns:
        raise LatticeError(
            "These points carry no lattice indices, so they cannot be "
            "joined exactly. Use a point table from machine 3 with "
            "keep_index=True, or join on coordinates yourself and "
            "accept the tolerance.")
    out = points.merge(snapped[["gx", "gy", name]], on=["gx", "gy"],
                       how="left")
    out[name] = out[name].fillna(fill)
    return out
