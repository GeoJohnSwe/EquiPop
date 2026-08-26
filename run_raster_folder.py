#!/usr/bin/env python3
"""
run_raster_folder.py - point it at a folder of rasters and it does the rest.

Nothing here is new machinery; it is a front door onto
equipop.rasterfolder so you do not have to write Python to try it.

EXAMPLES
    python run_raster_folder.py Africa
    python run_raster_folder.py Africa Europe --unit 1000
    python run_raster_folder.py Africa --unit 1000 --k 100 1000 --out run_africa

WHAT IT PRINTS is the same running commentary the library prints, plus a
summary at the end. Nothing is written unless you pass --out.
"""
from __future__ import annotations

import argparse
import os
import sys
import time


def main() -> int:
    p = argparse.ArgumentParser(
        description="Load a folder of rasters into EquiPop.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    p.add_argument("folders", nargs="+",
                   help="one or more folders holding .tif rasters")
    p.add_argument("--unit", type=float, default=1000.0,
                   help="cell size in METRES for the analysis grid "
                        "(default 1000; use 100 for fine work, but a "
                        "continent at 100 m is a very large run)")
    p.add_argument("--k", type=int, nargs="*", default=None,
                   help="neighbourhood sizes in PEOPLE, e.g. --k 100 1000. "
                        "Omit to stop after building the cells.")
    p.add_argument("--epsg", type=int, default=None,
                   help="force a projection; otherwise one is suggested")
    p.add_argument("--weight", default=None,
                   help="which column holds the people (only needed when "
                        "there is more than one)")
    p.add_argument("--sum", action="store_true", dest="sum_cohorts",
                   help="add all cohorts into one 'pop' column")
    p.add_argument("--keep-zero", action="store_true",
                   help="also keep pixels that are zero in EVERY layer")
    p.add_argument("--out", default=None,
                   help="folder for a TILED run. Needs --k. Resumable: "
                        "run it again on the same folder to continue.")
    p.add_argument("--tile-m", type=float, default=50000.0,
                   help="tile size in metres for --out (default 50000)")
    a = p.parse_args()

    for f in a.folders:
        if not os.path.isdir(f):
            print(f"STOP: not a folder: {f}", file=sys.stderr)
            return 2

    try:
        from equipop.rasterfolder import folder_to_cells
    except ImportError as e:
        print(f"STOP: {e}\n\nInstall the extras first:\n"
              "    python -m pip install rasterio pyarrow", file=sys.stderr)
        return 2

    t0 = time.time()
    cd, man = folder_to_cells(a.folders, weight=a.weight, unit_size=a.unit,
                              epsg=a.epsg, sum_cohorts=a.sum_cohorts,
                              keep_zero=a.keep_zero)
    print(f"\n--- cells built in {time.time() - t0:.1f}s ---")
    print(f"    rasters   : {len(man['files'])}")
    print(f"    columns   : {', '.join(man['labels'])}")
    print(f"    points    : {man['points']:,}")
    print(f"    cells     : {len(cd):,} of {a.unit:g} m")
    print(f"    people    : {cd.n.sum():,.1f}")
    print(f"    weight col: {man['weight_column']}")
    print(f"    projection: EPSG:{man['projection']['epsg']}")
    for w in man["projection"]["warnings"]:
        print(f"    WARNING   : {w}")
    if man["unparsed"]:
        print(f"    {len(man['unparsed'])} filename(s) not recognised - "
              "columns named from the filename")

    if not a.k:
        print("\nNo --k given, so stopping here. Add e.g. --k 100 1000 "
              "to run the neighbourhoods.")
        return 0

    if a.out:
        from equipop.bigrun import run_knn_counts_tiled
        t1 = time.time()
        m = run_knn_counts_tiled(cd, k_values=a.k, out_dir=a.out,
                                 tile_m=a.tile_m)
        print(f"\n--- tiled run in {time.time() - t1:.1f}s, "
              f"{len(m['tiles'])} tiles -> {a.out} ---")
        print("    read it back with:")
        print("        from equipop.bigrun import load_tiled")
        print(f"        df = load_tiled({a.out!r})")
    else:
        from equipop.fastcounts import run_knn_counts
        t1 = time.time()
        res = run_knn_counts(cd, a.k)
        print(f"\n--- run in {time.time() - t1:.1f}s ---")
        cols = [c for c in res.columns
                if c.startswith(("N_", "Dist_", "T_", "R_"))]
        print(res[cols].describe().T[["count", "mean", "min", "max"]]
              .to_string())
        print("\nNothing was written. Pass --out FOLDER for a tiled, "
              "resumable run that saves its results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
