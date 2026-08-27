"""
continental.py - a folder of rasters to a finished run, once.

BACKLOG 38. `bigrun` has been built and regression-tested since
v1.16.8 and was reachable only by hand-assembling a CellData.
`rasterfolder.load_folder` then gave the raster path a front door.
This is the piece between them, and it exists so that the QGIS tool
and the Pro tool are THIN - John's ruling: "one ring to rule them
all, and different doors that can use it".

Everything a door has to decide is decided HERE: which column holds
the people, whether the extent wants a tiled run, what the numbers
mean, what to refuse. A door supplies boxes and a channel; it does
not supply judgement. The doors have drifted apart three times in
this project's history and every time it was because a rule lived in
two places.

    from equipop.doors.continental import run_folder
    man = run_folder("Africa", k_values=[1000], unit_size=1000.0)

Nothing here imports QGIS or arcpy, so it is testable without either.
"""

from __future__ import annotations

import os
import time

# BACKLOG 78: no heavy import at module level. The doors load this
# file while their host is starting up.


class ContinentalError(Exception):
    """Refused before anything ran, with the reason in plain words."""


# How many cells before an untiled run is a bad idea. Not a hard
# limit - the untiled path holds every origin's results in memory at
# once, and past roughly this many that is a gamble on the machine
# rather than on the method. Measured shape, not a guess: Burundi +
# Rwanda at 1 km is 46,317 cells and runs untiled in about 10 s.
TILE_ADVISED_CELLS = 400_000


def to_output_crs(table, from_epsg, to_epsg):
    """Cell centres from the WORKING projection into the OUTPUT one.

    John: "the raster has an in-data projection, perhaps we should
    depict in the same format? it ought to be easy to place correctly
    (I can reproject so it works, but this is a nuisance)."

    THE ANALYSIS MUST BE IN METRES - k is a number of people and a
    radius is a distance - but nothing says the OUTPUT must be. Writing
    in the source CRS puts the layer where the rasters were, with no
    reprojection step for the user.

    And the metric coordinates are a trap on their own: UTM SOUTHERN
    zones carry a FALSE NORTHING OF 10,000,000 m, so Burundi comes out
    at northing ~9,779,000. On a European basemap that reads as the
    far north, which is why John's result drew west of Norway even
    with the project set to the layer's own EPSG:32735.

    Returns (easting, northing) arrays in `to_epsg`. EastWest and
    NorthSouth stay as they were - they are the ANALYSIS coordinates
    and several columns are derived from them.
    """
    import numpy as np

    e = table["EastWest"].to_numpy(dtype=float)
    n = table["NorthSouth"].to_numpy(dtype=float)
    if not to_epsg or int(to_epsg) == int(from_epsg or 0):
        return e, n
    from pyproj import Transformer
    tr = Transformer.from_crs(f"EPSG:{int(from_epsg)}",
                              f"EPSG:{int(to_epsg)}", always_xy=True)
    x, y = tr.transform(e, n)
    return np.asarray(x, dtype=float), np.asarray(y, dtype=float)


def check_folders(folders):
    """Refuse a folder that is not there, in words, and say what to
    point at.

    Shared because MACHINE 4 READS THE LABELS BEFORE THE SPINE RUNS -
    it has to, to show which columns an index will use - so without
    this it reached load_folder first and a bare FileNotFoundError
    escaped past every door's handler.
    """
    if isinstance(folders, (str, os.PathLike)):
        folders = [folders]
    folders = [str(f) for f in folders]
    missing = [f for f in folders if not os.path.isdir(f)]
    if missing:
        raise ContinentalError(
            "Not a folder: " + "; ".join(missing) +
            ". Point this at the folder holding the .tif files - "
            "subfolders are searched too, so a country-per-folder "
            "download can stay as it is.")
    return folders


def _plural(n, one, many=None):
    return one if n == 1 else (many or one + "s")


def run_folder(folders, *, k_values=None, r_values=None,
               compose=None,
               unit_size=1000.0, epsg=None, weight=None, groups=None,
               sum_cohorts=False, keep_zero=False, out_dir=None,
               tile_m=50_000.0, convention=None, labels=None,
               pattern=None, channel=None):
    """Load a folder of rasters, build the cells, run the neighbourhoods.

    folders    : one folder, or several. Subfolders are included, so a
                 country-per-folder download works as it arrives -
                 verified on a bdi/rwa/dnk tree against the same files
                 laid out flat, identical to the row.
    k_values   : neighbourhood sizes in PEOPLE.
    unit_size  : analysis cell size in METRES.
    weight     : which column holds the people. Only needed when the
                 folder yields more than one cohort column.
    groups     : cohort columns to carry as treatment groups.
    out_dir    : run TILED and write parquet there. Resumable.
    channel    : a doors.report.Channel, or None for plain printing.

    Returns the manifest dict, with 'results' when untiled.
    """
    from .report import speaking
    from ..rasterfolder import folder_to_cells

    say = channel.info if channel is not None else print
    warn = channel.warning if channel is not None else print

    # NO k MEANS: JUST GIVE ME THE POINTS (John). The rasters as one
    # point table, countries merged onto one lattice, every cohort a
    # field, zeros kept - useful on its own and the thing you look at
    # before deciding anything. It needs no weight, because nothing is
    # being counted yet. Demanding a k first was imposing a shape his
    # data does not have: with sixty cohorts there is no single
    # population, and asking which column holds "the people" has no
    # answer until somebody says what they are measuring.
    points_only = not k_values and not r_values
    for k in (k_values or []):
        if k is None or k <= 0:
            raise ContinentalError(
                f"k must be a positive number of people; got {k!r}.")
    if unit_size is None or unit_size <= 0:
        raise ContinentalError(
            f"The cell size must be a positive number of metres; got "
            f"{unit_size!r}.")

    folders = check_folders(folders)

    t0 = time.time()
    if points_only:
        from ..rasterfolder import load_folder
        with (speaking(channel) if channel is not None else _null()):
            # keep_index=True so the LATTICE JOIN can attach a point
            # layer exactly (BACKLOG 238). The indices are machinery,
            # but the points path is the one a join consumes and they
            # cost two integer columns.
            pts, man = load_folder(
                folders, sum_cohorts=sum_cohorts, keep_zero=keep_zero,
                keep_index=True, convention=convention, labels=labels,
                pattern=pattern)
        man["points_table"] = pts
        man["seconds_loading"] = round(time.time() - t0, 1)
        cols = [c for c in pts.columns if c not in ("lon", "lat")]
        say(f"{len(man['files'])} {_plural(len(man['files']), 'raster')} "
            f"-> {len(pts):,} points, {len(cols)} "
            f"{_plural(len(cols), 'field')}, in degrees (EPSG:4326).")
        say("No k was asked for, so this is the point table itself - "
            "every cohort a field, the countries stacked as rows, and "
            "a real 0.0 wherever a layer had nothing there. Give a k "
            "to run neighbourhoods on it.")
        return man

    ctx = speaking(channel) if channel is not None else _null()
    with ctx:
        cd, man = folder_to_cells(
            folders, weight=weight, unit_size=unit_size, epsg=epsg,
            groups=groups, compose=compose, sum_cohorts=sum_cohorts,
            keep_zero=keep_zero, convention=convention,
            labels=labels, pattern=pattern)
    man["seconds_loading"] = round(time.time() - t0, 1)

    n_cells = len(cd)
    say(f"{len(man['files'])} {_plural(len(man['files']), 'raster')} "
        f"-> {man['points']:,} points -> {n_cells:,} cells of "
        f"{unit_size:g} m, holding {cd.n.sum():,.1f} people.")
    if man["unparsed"]:
        warn(f"{len(man['unparsed'])} filename(s) did not match a known "
             "naming convention, so their columns are named from the "
             "filename. Pass your own pattern if that matters.")

    # A TILED RUN IS NOT A DIFFERENT ANSWER. bigrun keeps ONE cell
    # table and ONE tree and tiles only the ORIGINS, so there are no
    # halos and no seams; test_tiled_equals_untiled_exactly pins that.
    # It exists for the scale at which holding every origin's results
    # at once stops being sensible, not to trade accuracy for size.
    if out_dir is None and n_cells > TILE_ADVISED_CELLS:
        warn(f"{n_cells:,} cells is a large untiled run. Giving an "
             "output folder would tile it - same answers, written out "
             "as it goes, and resumable if it stops.")

    t1 = time.time()
    with (speaking(channel) if channel is not None else _null()):
        if out_dir is not None:
            from ..bigrun import run_knn_counts_tiled
            run = run_knn_counts_tiled(cd, k_values=list(k_values or []),
                                       out_dir=out_dir, tile_m=tile_m)
            man["tiles"] = len(run.get("tiles", []))
            man["out_dir"] = out_dir
        else:
            from ..fastcounts import run_knn_counts
            man["results"] = run_knn_counts(
                cd, list(k_values or []), r_values=list(r_values or [])
                or None)
    man["seconds_running"] = round(time.time() - t1, 1)
    man["cells"] = n_cells
    man["unit_size"] = float(unit_size)
    man["k_values"] = list(k_values or [])

    if out_dir is not None:
        say(f"Tiled run finished: {man['tiles']} "
            f"{_plural(man['tiles'], 'tile')} in {out_dir} "
            f"({man['seconds_running']} s). Read it back with "
            "equipop.bigrun.load_tiled.")
    else:
        say(f"Finished in {man['seconds_running']} s, "
            f"{len(man['results']):,} origin rows.")

    # BACKLOG 207 was fixed in this engine, and every continental
    # number produced before it came from one that had the defect.
    say("Dist_k is the radius each origin needed to gather its k "
        "people - k fixes the population and the radius floats. That "
        "variation IS the density of the place, not an error.")
    return man


class _null:
    """A do-nothing context, so the no-channel path stays one branch."""

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
