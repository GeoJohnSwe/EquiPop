#!/usr/bin/env python3
"""
run_osm_friction.py - OSM lines to friction values on the lattice.

WHERE TO RUN IT. There is NO QGIS TOOL FOR THIS YET - the engine
works and nothing wraps it. So run it in QGIS's own Python console
(Plugins > Python Console), or from the OSGeo4W Shell, or from the
Anaconda Prompt. All three have geopandas available if EquiPop's
extras are installed.

    python run_osm_friction.py ^
        --roads  "C:\\path\\burundi-latest-free.shp.zip" ^
        --like   "C:\\path\\rasters\\BDI_fetched" ^
        --gpkg   "C:\\path\\out\\bdi_friction.gpkg"

WHAT IT DOES, AND WHAT IT DOES NOT. It divides every road between the
cells it crosses, adds up the metres of each class in each cell, and
names the longest class there. It sets no friction VALUES - those are
yours, and `--groups` takes a small text file mapping classes to
groups so you can say what an "eatery" or a "major road" is.

THE UNIT IS THE MEASURE. "The longest stretch in the cell" has no
meaning without the cell, so the lattice comes from your raster
folder and the answer is a property of that grid.
"""
import argparse
import json
import sys


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Reduce OSM lines to per-class length per cell.")
    ap.add_argument("--roads", required=True,
                    help="a shapefile, a .shp.zip, or a GeoPackage")
    ap.add_argument("--layer", default=None,
                    help="which layer, if the file holds several")
    ap.add_argument("--like", required=True,
                    help="the raster FOLDER whose lattice to use")
    ap.add_argument("--class-col", default="fclass")
    ap.add_argument("--groups", default=None,
                    help="a JSON file: {\"major\": [\"motorway\", "
                         "\"trunk\"], ...}")
    ap.add_argument("--areas", action="store_true",
                    help="treat the features as polygons and report "
                         "the SHARE of each cell instead of length")
    ap.add_argument("--gpkg", default=None)
    ap.add_argument("--csv", default=None)
    a = ap.parse_args(argv)

    try:
        import geopandas as gpd
    except ImportError:
        raise SystemExit(
            "This needs geopandas:\n"
            "  conda install -c conda-forge geopandas\n"
            "or  python -m pip install --user geopandas")

    from equipop.latticejoin import lattice_of
    from equipop.vectorjoin import (VectorJoinError, areas_to_cells,
                                    lines_to_cells)

    lat = lattice_of(a.like)
    print(f"[lattice] {lat['crs']}, cell "
          f"{abs(lat['a']):g} x {abs(lat['e']):g}, from {lat['from']}")

    gdf = gpd.read_file(a.roads, layer=a.layer)
    print(f"[read] {len(gdf):,} feature(s), "
          f"{gdf.geometry.geom_type.iloc[0]}, {gdf.crs}")

    groups = None
    if a.groups:
        with open(a.groups, encoding="utf-8") as f:
            groups = json.load(f)
        print(f"[groups] {len(groups)} group(s): "
              + ", ".join(sorted(groups)))

    try:
        fn = areas_to_cells if a.areas else lines_to_cells
        got = fn(gdf, lat, class_col=a.class_col, groups=groups)
    except VectorJoinError as exc:
        raise SystemExit(f"\nRefused: {exc}")

    if a.csv:
        got.to_csv(a.csv, index=False)
        print(f"\n[out] {a.csv}  ({len(got):,} rows)")
    if a.gpkg:
        # THE CELL CENTRES, so QGIS can draw it. The lattice indices
        # travel too - they are what a later join matches on, and a
        # CSV of numbers with no geometry is hard to look at.
        from shapely.geometry import Point
        xs = lat["c"] + (got["gx"] + 0.5) * lat["a"]
        ys = lat["f"] + (got["gy"] + 0.5) * lat["e"]
        out = gpd.GeoDataFrame(got.copy(),
                               geometry=[Point(x, y)
                                         for x, y in zip(xs, ys)],
                               crs=lat["crs"])
        out.to_file(a.gpkg, driver="GPKG")
        print(f"\n[out] {a.gpkg}  ({len(out):,} cells)")
        print("      Drag it into QGIS and style by 'length_top' for "
              "the dominant class,")
        print("      or graduate 'length_total' for road density.")
    if not (a.csv or a.gpkg):
        print("\nNothing written. Add --gpkg FILE or --csv FILE.")
        print(got.head(10).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
