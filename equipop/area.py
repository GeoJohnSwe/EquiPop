"""
area.py - area-based output (backlog item 9): bring overlapping
bespoke-neighbourhood results back to fixed geographies that policy
audiences grasp.

DELIBERATE DESIGN, stated for reviewers: values are collected
overlappingly with k and then SUMMARISED per area - this is
"individualised context, reported per area", not a recomputation of
areal statistics. The precedent is the block-level illustration of
EquiPop output in Östh, Clark & Malmberg (2015, fig. 1).

Three alternatives, one function:
  Alt 1  by = a COLUMN NAME already on the output (belonging ID,
         e.g. a municipality code carried through CellId/merge).
  Alt 2  by = a POLYGON FILE path (shp/gpkg): origin cells are
         point-in-polygon assigned (geopandas sjoin); `id_field`
         names the polygon attribute to aggregate by. `points_epsg`
         must be given if it differs from the polygons' CRS.
  Alt 3  by = a NUMBER: a coarser grid size (e.g. 1000 for 1 km
         super-cells over 100 m results), anchored at the minimum
         X/Y of the data.
"""

import numpy as np
import pandas as pd


def aggregate_output(
    df: pd.DataFrame,
    by,
    columns: list[str] | None = None,
    how: str = "wmean",
    weight_col: str = "N_local",
    id_field: str | None = None,
    points_epsg: int | None = None,
    x_col: str = "EastWest",
    y_col: str = "NorthSouth",
) -> pd.DataFrame:
    """
    Aggregate k-NN output to areas. See module docstring for the three
    `by` alternatives.

    columns : which output columns to aggregate (default: all R_*,
              Mean_*, Med_*, Gini_*, SD_* columns found).
    how     : 'wmean' population-weighted mean (weights = weight_col,
              typically the origin population), 'mean', or 'median'.
    Returns one row per area with the aggregated columns, the number
    of origin cells, and the summed weight.
    """
    df = df.copy()
    if columns is None:
        columns = [c for c in df.columns if c.split("_")[0] in
                   ("R", "Mean", "Med", "Gini", "SD", "Ratio")]
        if not columns:
            raise ValueError("No aggregatable columns found - pass "
                             "columns=[...] explicitly.")

    # ---- resolve `by` into a per-row area label ----
    if isinstance(by, (int, float)):                       # Alt 3
        u = float(by)
        x0, y0 = df[x_col].min(), df[y_col].min()
        df["_area"] = (
            "SG" + (np.floor((df[x_col] - x0) / u)).astype(int).astype(str)
            + "_" + (np.floor((df[y_col] - y0) / u)).astype(int).astype(str))
        label = f"supergrid_{int(u)}m"
    elif isinstance(by, str) and by in df.columns:         # Alt 1
        df["_area"] = df[by]
        label = by
    elif isinstance(by, str):                              # Alt 2: file
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError("Polygon aggregation needs geopandas.")
        polys = gpd.read_file(by)
        if id_field is None:
            raise ValueError("Give id_field=<polygon attribute>.")
        pts = gpd.GeoDataFrame(
            df[[x_col, y_col]],
            geometry=gpd.points_from_xy(df[x_col], df[y_col]),
            crs=f"EPSG:{points_epsg}" if points_epsg else polys.crs)
        if points_epsg and pts.crs != polys.crs:
            pts = pts.to_crs(polys.crs)
            print(f"[area] points reprojected EPSG:{points_epsg} -> "
                  f"{polys.crs.to_epsg()} for the join")
        joined = gpd.sjoin(pts, polys[[id_field, "geometry"]],
                           how="left", predicate="within")
        df["_area"] = joined[id_field].to_numpy()
        unmatched = df["_area"].isna().sum()
        if unmatched:
            print(f"[area] WARNING: {unmatched} origin cells fall outside "
                  f"all polygons (dropped from area output).")
            df = df[df["_area"].notna()]
        label = id_field
    else:
        raise ValueError("`by` must be a column name, a polygon file "
                         "path, or a super-grid size in metres.")

    # ---- aggregate ----
    w = df[weight_col].to_numpy(float)
    out_rows = []
    for area, g in df.groupby("_area"):
        gw = g[weight_col].to_numpy(float)
        row = {label: area, "n_origin_cells": len(g),
               weight_col + "_sum": gw.sum()}
        for c in columns:
            v = g[c].to_numpy(float)
            ok = np.isfinite(v)
            if not ok.any():
                row[c] = np.nan
            elif how == "wmean":
                row[c] = np.average(v[ok], weights=gw[ok]) \
                    if gw[ok].sum() > 0 else np.nan
            elif how == "mean":
                row[c] = v[ok].mean()
            elif how == "median":
                row[c] = np.median(v[ok])
        out_rows.append(row)
    out = pd.DataFrame(out_rows)
    print(f"[area] {len(df)} origin cells -> {len(out)} areas "
          f"('{label}', how={how})")
    return out


# ------------------------------------------------------------------
# Area-based statistics: the third neighbourhood family (k / r / AREA)
# ------------------------------------------------------------------
from .stats import (BINARY_STATS, VALUE_STATS, PREFIX,
                    value_stat, stat_prefix, is_percentile)


def area_stats(df, area_col: str,
               binary_vars: list[str] | None = None,
               value_vars: list[str] | None = None,
               stats: dict | None = None,
               weight_col: str | None = None):
    """
    Per-AREA statistics from individual-level rows: the administrative
    member of the neighbourhood-definition menu (k fixes population,
    r fixes geometry, AREA fixes administration).

    df          : individual rows; area_col holds the belonging ID
                  (municipality code etc. - use assign_zones() first
                  if you start from polygons).
    binary_vars : 0/1 group variables -> T_<v>, R_<v> per area.
    value_vars  : continuous variables -> Mean/Med/Gini/... + Nv_<v>.
    stats       : per-variable statistic lists as in run_knn_stats;
                  defaults: binary ["ratio"], value ["mean","median","gini"].
    weight_col  : persons represented per row (aggregated in-data).
                  Applies to N and binary T/R; VALUE statistics are
                  computed over rows unweighted (weighted quantiles
                  are a recorded backlog item - loud, not silent).

    NO Dist_/Rounds_ columns exist here - areas do not expand, so
    there is nothing to measure; the columns are honestly absent.
    Rows with missing area ID are excluded LOUDLY and reported.
    """
    import numpy as np
    import pandas as pd
    binary_vars = binary_vars or []
    value_vars = value_vars or []
    stats = stats or {}
    for v in binary_vars:
        stats.setdefault(v, ["ratio"])
    for v in value_vars:
        stats.setdefault(v, ["mean", "median", "gini"])

    unassigned = df[area_col].isna()
    if unassigned.any():
        print(f"[area] {int(unassigned.sum())} rows with no {area_col} "
              "excluded (outside all areas?) - the Stockholm precedent: "
              "check, do not panic")
    d = df[~unassigned]
    w = (d[weight_col].to_numpy(float) if weight_col
         else np.ones(len(d)))

    out = []
    for aid, g in d.groupby(area_col, sort=True):
        gw = (g[weight_col].to_numpy(float) if weight_col
              else np.ones(len(g)))
        rec = {"AreaId": aid, "N": float(gw.sum())}
        for v in binary_vars:
            t = float((g[v].to_numpy(float) * gw).sum())
            rec[f"T_{v}"] = t
            for s in stats[v]:
                rec[f"{PREFIX[s]}_{v}"] = BINARY_STATS[s](rec["N"], t)
        for v in value_vars:
            x = g[v].to_numpy(float)
            x = x[np.isfinite(x)]
            rec[f"Nv_{v}"] = int(len(x))
            for s in stats[v]:
                rec[f"{stat_prefix(s)}_{v}"] = value_stat(s, x)
        out.append(rec)
    res = pd.DataFrame(out)
    print(f"[area] {len(res)} areas, N total = {res['N'].sum():,.0f}")
    return res
