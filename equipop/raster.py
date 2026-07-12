"""
raster.py - GeoTIFF/raster in-data (WorldPop-style and general).

Turns one or several rasters into the point table the rest of the
library consumes. The typical WorldPop pattern:

    from equipop.raster import rasters_to_points

    df = rasters_to_points(
        {"pop": "malta/mlt_t_*_2020_*.tif",          # sum of all cohorts
         "old": "malta/mlt_t_{65,70,75,80,85,90}_*.tif"},
        )                                             # -> lon, lat, pop, old

Each key becomes a column holding the SUM of all rasters matching its
pattern (glob syntax; {a,b} alternatives supported). Nodata is masked;
only pixels where the FIRST variable is > 0 are returned. All rasters
must share grid and CRS (checked).

Reprojection/snapping then proceeds exactly as for point data:
project_to_metric -> snap_to_grid -> aggregate. Note that reprojecting
lat/long pixels onto a metric grid makes some pixels share a cell -
mass is conserved by summing (verify with the printed totals).
"""

import glob as _glob
import re
import numpy as np
import pandas as pd

try:
    import rasterio
    from rasterio.transform import xy as _xy
except ImportError as e:                              # helpful message
    raise ImportError("The raster module needs rasterio: "
                      "pip install rasterio") from e


def _expand(pattern: str) -> list[str]:
    """glob with {a,b,c} alternative expansion."""
    m = re.search(r"\{([^}]*)\}", pattern)
    if not m:
        return sorted(_glob.glob(pattern))
    out = []
    for alt in m.group(1).split(","):
        out += _expand(pattern[:m.start()] + alt + pattern[m.end():])
    return sorted(set(out))


def _read_sum(paths: list[str], ref_meta: dict | None):
    total = None
    for p in paths:
        with rasterio.open(p) as r:
            meta = dict(crs=str(r.crs), transform=tuple(r.transform),
                        shape=(r.height, r.width))
            if ref_meta is None:
                ref_meta = meta
            elif meta != ref_meta:
                raise ValueError(f"{p} has a different grid/CRS than the "
                                 f"first raster - all rasters must match.")
            a = r.read(1).astype(float)
            if r.nodata is not None:
                a[a == r.nodata] = 0.0
            total = a if total is None else total + a
    return total, ref_meta


def rasters_to_points(variables: dict[str, str],
                      keep_zero: bool = False) -> pd.DataFrame:
    """
    variables : {column_name: glob_pattern}. Each column is the SUM of
                all matching rasters.
    keep_zero : if False (default), only pixels where the FIRST variable
                is > 0 are returned.

    Returns a DataFrame with lon, lat (pixel centres, raster CRS) and
    one column per variable, plus prints per-variable totals so mass
    conservation can be verified after regridding.
    """
    meta = None
    grids = {}
    for name, pattern in variables.items():
        paths = _expand(pattern)
        if not paths:
            raise FileNotFoundError(f"No rasters match: {pattern}")
        grids[name], meta = _read_sum(paths, meta)
        print(f"[raster] {name}: {len(paths)} file(s), total "
              f"{grids[name].sum():,.1f}")
    print(f"[raster] CRS {meta['crs']}, {meta['shape'][1]} x "
          f"{meta['shape'][0]} pixels")

    first = next(iter(grids.values()))
    if keep_zero:
        rows, cols = np.nonzero(np.isfinite(first))
    else:
        rows, cols = np.nonzero(first > 0)
    from affine import Affine
    T = Affine(*meta["transform"][:6])
    lon, lat = _xy(T, rows, cols)
    out = pd.DataFrame({"lon": lon, "lat": lat})
    for name, g in grids.items():
        out[name] = g[rows, cols]
    print(f"[raster] {len(out)} pixels extracted")
    if str(meta["crs"]).upper() not in ("EPSG:4326",):
        print(f"[raster] note: raster CRS is {meta['crs']} - if already "
              f"metric, skip project_to_metric and rename lon/lat.")
    return out
