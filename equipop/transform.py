"""
transform.py - projection and grid snapping.

Two jobs:
1. project_to_metric(): WGS84 lat/long -> metric coordinates (e.g. EPSG:25832)
2. snap_to_grid():      metric coordinates -> grid-cell midpoints

Original coordinates are always kept; new columns are added, never replaced.
"""

import math
import pandas as pd
from pyproj import Transformer, CRS


def suggest_utm_epsg(lat: float, lon: float) -> int:
    """
    Suggest a UTM EPSG code from a representative lat/long point
    (e.g. the centroid of your data).

    Northern hemisphere -> 326xx, southern -> 327xx, where xx is the UTM zone.
    Example: Berlin (52.5 N, 13.4 E) -> zone 33 -> EPSG:32633.
    Note: for official European work you may prefer the ETRS89 equivalents
    (EPSG:25832 / 25833) - pass those explicitly instead.
    """
    zone = int((lon + 180) / 6) + 1
    return (32600 if lat >= 0 else 32700) + zone


def project_to_metric(
    df: pd.DataFrame,
    lat_col: str = "latitude_wgs84",
    lon_col: str = "longitude_wgs84",
    target_epsg: int | None = None,
    source_epsg: int = 4326,
) -> pd.DataFrame:
    """
    Add projected metric coordinates to a DataFrame.

    Parameters
    ----------
    df : DataFrame with latitude/longitude columns.
    lat_col, lon_col : names of those columns.
    target_epsg : EPSG code to project to (e.g. 25832).
                  If None, a UTM zone is suggested from the data centroid.
    source_epsg : EPSG of the input coordinates (default 4326 = WGS84).

    Returns
    -------
    A copy of df with new columns: 'easting_m', 'northing_m',
    plus 'source_crs' and 'target_crs' strings.
    """
    df = df.copy()

    if target_epsg is None:
        target_epsg = suggest_utm_epsg(df[lat_col].mean(), df[lon_col].mean())
        print(f"[transform] No EPSG given - suggesting EPSG:{target_epsg} "
              f"({CRS.from_epsg(target_epsg).name})")

    # always_xy=True means input order is (longitude, latitude)
    transformer = Transformer.from_crs(source_epsg, target_epsg, always_xy=True)
    easting, northing = transformer.transform(
        df[lon_col].to_numpy(), df[lat_col].to_numpy()
    )

    df["easting_m"] = easting
    df["northing_m"] = northing
    df["source_crs"] = f"EPSG:{source_epsg}"
    df["target_crs"] = f"EPSG:{target_epsg}"
    return df


def snap_to_grid(
    df: pd.DataFrame,
    unit_size: float,
    easting_col: str = "easting_m",
    northing_col: str = "northing_m",
) -> pd.DataFrame:
    """
    Snap metric coordinates to grid-cell MIDPOINTS.

    A grid with unit_size = 100 has midpoints at 50, 150, 250, ...
    so a point at easting 788450.417 snaps to 788450
    (floor(788450.417 / 100) * 100 + 50 = 788450).

    Adds columns 'E_grid' and 'N_grid' (integers).
    """
    df = df.copy()
    half = unit_size / 2.0

    def snap(v: float) -> int:
        return int(math.floor(v / unit_size) * unit_size + half)

    df["E_grid"] = df[easting_col].apply(snap)
    df["N_grid"] = df[northing_col].apply(snap)
    return df


def aggregate_to_cells(
    df: pd.DataFrame,
    value_cols: list[str],
    id_col: str | None = None,
) -> pd.DataFrame:
    """
    Aggregate rows that share the same grid midpoint.

    value_cols are SUMMED (population counts, treatment counts, ...).
    If id_col is given, the ids are kept as a comma-joined string so that
    output can be matched back to the original records.
    """
    agg: dict = {c: "sum" for c in value_cols}
    if id_col:
        agg[id_col] = lambda s: ",".join(s.astype(str))
    out = df.groupby(["E_grid", "N_grid"], as_index=False).agg(agg)
    return out
