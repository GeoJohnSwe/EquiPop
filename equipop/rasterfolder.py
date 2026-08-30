"""
rasterfolder.py - load a FOLDER of rasters into one point table.

BACKLOG 206. Written to John's rule, and the rule is about geometry
rather than filenames:

    rasters of DIFFERENT GROUND do not overlap  -> they become ROWS
    rasters of the SAME GROUND do overlap       -> they become COLUMNS

That is measurable, so the merge never depends on a naming convention
and will survive WorldPop renaming everything. Filenames are used ONLY
to LABEL the columns, because a wrong label is cosmetic and visible
while a wrong merge is silent and corrupts the data.

AND THE TEST IS DATA OVERLAP, NOT EXTENT OVERLAP. Burundi and Rwanda
share a bounding box over 1.4 million cells and do not share ONE pixel
carrying data in both. An extent-based merge would call them the same
ground and add two countries into a single column.

ZEROS ARE KEPT (John, explicitly). A pixel holding no women aged 15-19
may hold three men, so the point set is the UNION over every raster and
a layer with nothing there contributes a real 0.0, not an absence. The
old rasters_to_points() decided the point set from whichever variable
came first, which silently deleted exactly those pixels.

Usage:
    from equipop.rasterfolder import load_folder
    pts, man = load_folder("Africa/")            # every raster in it
    pts, man = load_folder(["Africa/", "Europe/"])
    pts, man = load_folder("Africa/", sum_cohorts=True)   # one column
"""

from __future__ import annotations

import os
import re
import glob as _glob

import numpy as np
import pandas as pd



# --------------------------------------------------------------- names
# A REGISTRY, not a hard-coded rule. When the convention moves on, this
# gains an entry and nothing about the spatial behaviour changes.
CONVENTIONS: dict[str, str] = {
    # bdi_f_15_2020_CN_100m_R2025A_v1
    # bdi_f_00_2026_CN_1km_R2025A_UA_v1     <- John's real download
    #
    # ONLY THE FOUR LABEL FIELDS ARE PINNED. Everything after the year
    # is provenance - constrained/unconstrained, resolution, release,
    # UN-adjustment, version - and WorldPop varies it freely.
    # The first version of this spelled the whole tail out, built from
    # the four sample files Claude happened to have, and then failed on
    # ALL 120 of John's real ones: it demanded `\d+m` where the files
    # said `1km`, and had no slot at all for the `UA` token. A REGISTRY
    # BUILT FROM ONE SAMPLE IS NOT A REGISTRY.
    # Two files differing only in that tail - CN against UA, say - now
    # take the SAME label, overlap on the same ground and are REFUSED
    # by the safety net further down. That is correct: constrained and
    # UN-adjusted must not be mixed in one run.
    "worldpop_r2025a": (
        r"^(?P<iso3>[a-z]{3})_(?P<sex>[fmt])_(?P<age>\d+)"
        r"_(?P<year>\d{4})(?:_(?P<provenance>.+))?$"),
    # bdi_f_15_2020
    "worldpop_legacy": (
        r"^(?P<iso3>[a-z]{3})_(?P<sex>[fmt])_(?P<age>\d+)_(?P<year>\d{4})$"),
}

# The cohort fields, in the order they are joined into a column label.
# iso3 is deliberately ABSENT: different countries are different GROUND
# and become rows, so they must not change the column name.
LABEL_FIELDS = ("sex", "age", "year")


def age_band(start: int) -> tuple[int, int | None]:
    """WorldPop age bands are NOT all five years wide (John).

    0 is under-one on its own, 1 covers 1-4, then five-year bands, and
    the last one is open-ended - 90 means 90 and over. Returns
    (first_year, last_year), with None for an open band.
    """
    start = int(start)
    if start == 0:
        return (0, 0)
    if start == 1:
        return (1, 4)
    if start >= 90:
        return (90, None)
    return (start, start + 4)


def band_width(start: int) -> int | None:
    """Years covered, or None where the band is open-ended.

    Cohorts can always be SUMMED - people are people. They must NOT be
    averaged or differenced across bands without this, because a band
    holding one year and a band holding five are not comparable rates.
    None means: refuse, do not guess.
    """
    lo, hi = age_band(start)
    return None if hi is None else hi - lo + 1


def totals_overlap_parts(labels) -> list:
    """Which 't' labels duplicate an 'f'/'m' pair already present.

    WorldPop ships TOTALS ALONGSIDE THEIR PARTS. In John's Burundi
    download, f_00 holds 224,972 and m_00 holds 229,148, and t_00 holds
    exactly 454,120 - the sum. Adding every column together therefore
    counts everybody TWICE, and nothing about the numbers looks wrong
    afterwards: the map is simply twice as populous.

    Returns the offending 't' labels, so the caller can refuse by name.
    """
    have = set(labels)
    clash = []
    for lab in labels:
        parts = str(lab).split("_")
        if len(parts) >= 2 and parts[0] == "t":
            rest = "_".join(parts[1:])
            if f"f_{rest}" in have and f"m_{rest}" in have:
                clash.append(lab)
    return sorted(clash)


def parse_name(stem: str, convention: str | None = None) -> dict:
    """Filename stem -> fields. Never raises; degrades to the stem."""
    names = [convention] if convention else list(CONVENTIONS)
    for nm in names:
        m = re.match(CONVENTIONS[nm], stem)
        if m:
            d = m.groupdict()
            d["_convention"] = nm
            return d
    return {"_convention": None}


def _label(stem: str, fields: dict) -> str:
    """The column name. Falls back to the stem, which is always safe."""
    parts = [fields[f] for f in LABEL_FIELDS if fields.get(f)]
    return "_".join(parts) if parts else stem


# ---------------------------------------------------------------- load
def _tif_paths(folders) -> list[str]:
    if isinstance(folders, (str, os.PathLike)):
        folders = [folders]
    out: list[str] = []
    for f in folders:
        f = str(f)
        if os.path.isdir(f):
            for ext in ("*.tif", "*.tiff", "*.TIF"):
                out += _glob.glob(os.path.join(f, "**", ext), recursive=True)
        else:
            out += _glob.glob(f)
    return sorted(set(out))


def load_folder(folders, compose: dict | None = None,
                keep_index: bool = False,
                convention: str | None = None,
                labels: dict[str, str] | None = None,
                pattern: str | None = None,
                sum_cohorts: bool = False,
                keep_zero: bool = False) -> tuple[pd.DataFrame, dict]:
    """Every raster under `folders` as ONE point table.

    labels    : explicit {filename_stem: column_name}, the manual
                override for when the names are hopeless.
    pattern   : your own regex with named groups, tried before the
                registry. This is the escape hatch when the convention
                moves on and nobody has added it to CONVENTIONS yet.
    sum_cohorts : one 'pop' column instead of one per cohort. Kept as
                separate columns by DEFAULT, because summing afterwards
                is one line and un-summing is impossible.
    keep_zero : also keep pixels that are zero in EVERY layer. Off by
                default - a pixel empty everywhere carries no
                information - but zeros in SOME layer are always kept.

    Returns (points, manifest). points has lon, lat and one column per
    label; a layer with no data at a pixel contributes 0.0 there.
    """
    # RASTERIO IS IMPORTED HERE, NOT AT THE TOP OF THE FILE.
    # BACKLOG 234. It was a module-level import, so merely IMPORTING
    # equipop.rasterfolder failed without it - and the verify line in
    # INSTALL.md does exactly that, so John's Stata install reported a
    # traceback when the install was perfectly correct. raster.py,
    # slope.py and latticejoin.py all defer it into the function that
    # reads a file; this module alone did not.
    try:
        import rasterio
    except ImportError as e:                        # pragma: no cover
        raise ImportError(
            "Reading a folder of rasters needs rasterio: "
            "pip install rasterio") from e

    paths = _tif_paths(folders)
    if not paths:
        raise FileNotFoundError(f"No rasters found under {folders}")
    if pattern:
        CONVENTIONS["_user"] = pattern

    ref = None
    frames, seen = [], {}
    man: dict = {"files": {}, "labels": {}, "unparsed": []}

    for p in paths:
        stem = os.path.splitext(os.path.basename(p))[0]
        fields = parse_name(stem, "_user" if pattern else convention)
        lab = (labels or {}).get(stem) or _label(stem, fields)
        if fields["_convention"] is None:
            man["unparsed"].append(stem)

        with rasterio.open(p) as r:
            t, nod = r.transform, r.nodata
            if ref is None:
                ref = {"a": t.a, "e": t.e, "c": t.c, "f": t.f,
                       "crs": str(r.crs), "first": stem}
            elif str(r.crs) != ref["crs"]:
                # BACKLOG 239, external review of 1.43, and a RELEASE
                # BLOCKER for worldwide work. The lattice check below
                # compares pixel size and origin - both PURE NUMBERS -
                # and says nothing about which world those numbers
                # describe. Two rasters whose transforms agree
                # numerically were merged as if they occupied the same
                # ground, and the manifest then reported ONE crs, so
                # the run's own provenance record hid it.
                # 30.0 in EPSG:4326 is a longitude in Burundi; 30.0 in
                # EPSG:3857 is thirty METRES from Greenwich. Roughly
                # 3,300 km apart, stacked into one cell, silently.
                raise ValueError(
                    f"{stem} is in {r.crs}, but the first raster read "
                    f"({ref['first']}) is in {ref['crs']}. Their pixel "
                    "coordinates are numbers in DIFFERENT WORLDS and "
                    "cannot be combined - a longitude and a Mercator "
                    "metre are not the same 30.0. Reproject them to a "
                    "common CRS first, or load them as separate runs.")
            elif abs(t.a - ref["a"]) > 1e-12 or abs(t.e - ref["e"]) > 1e-12:
                raise ValueError(
                    f"{stem}: pixel size {t.a} does not match the first "
                    f"raster's {ref['a']}. Rasters must share a lattice; "
                    "resampling here would destroy the very detail the "
                    "method exists to keep.")
            arr = r.read(1).astype("float64")

        # global lattice indices, RELATIVE to the first raster - exact
        # whenever the rasters share a lattice, which is checked below.
        ox = (t.c - ref["c"]) / ref["a"]
        oy = (t.f - ref["f"]) / ref["e"]
        if abs(ox - round(ox)) > 0.01 or abs(oy - round(oy)) > 0.01:
            raise ValueError(
                f"{stem}: its origin is {ox:.3f} pixels from the first "
                "raster's, not a whole number. These rasters do not "
                "share a lattice.")

        arr = np.where(np.isfinite(arr) & (arr != nod), arr, 0.0)
        rows, cols = np.nonzero(arr > 0)
        gx = cols + int(round(ox))
        gy = rows + int(round(oy))
        frames.append(pd.DataFrame({
            "gx": gx, "gy": gy, "_lab": lab, "_val": arr[rows, cols],
            # BACKLOG 215, John: "the iso/country identifier should be
            # ROW and not column". Countries already stacked as rows -
            # that was right - but the country did not survive to the
            # point table at all, so it could not be selected on in
            # QGIS or Pro. It is well defined per point because
            # countries share no data pixel; categorical so that
            # eleven million rows cost almost nothing.
            "_iso": pd.Categorical([fields.get("iso3") or ""]
                                   * int(rows.size))}))
        man["files"][stem] = {"label": lab, "pixels": int(rows.size),
                              "total": float(arr[rows, cols].sum()),
                              "convention": fields["_convention"],
                              "iso3": fields.get("iso3")}
        seen.setdefault(lab, []).append(stem)
        print(f"[folder] {stem}: {rows.size:,} pixels, "
              f"{arr[rows, cols].sum():,.1f} -> column '{lab}'")
        del arr

    long = pd.concat(frames, ignore_index=True)
    del frames

    # THE SAFETY NET. Two files sharing a LABEL claim to be the same
    # cohort on different ground, so they must never both hold data at
    # one pixel - if they do, a straight merge double-counts.
    dup = long.duplicated(subset=["gx", "gy", "_lab"], keep=False)
    if dup.any():
        bad = long.loc[dup, "_lab"].unique()[:3]
        raise ValueError(
            f"{int(dup.sum()):,} pixels carry data in TWO rasters sharing "
            f"a label ({', '.join(map(str, bad))}). They overlap on the "
            "same ground, so they are not different geographies and "
            "cannot simply be concatenated - give them distinct labels, "
            "or clip them first.")

    # the country per point, before `long` is released
    iso = (long.loc[long["_iso"].astype(str) != "", ["gx", "gy", "_iso"]]
           .drop_duplicates(subset=["gx", "gy"]))

    pts = (long.pivot(index=["gx", "gy"], columns="_lab", values="_val")
           .fillna(0.0)                    # John: KEEP THE ZEROS
           .reset_index())
    pts.columns.name = None
    del long

    if len(iso):
        pts = pts.merge(iso, on=["gx", "gy"], how="left")
        # A MERGE DROPS THE CATEGORICAL back to object/str, which
        # quietly undoes the whole reason for using one - a
        # continental run is tens of millions of rows. Restore it,
        # and let the test that measures it keep us honest.
        pts["iso3"] = pts.pop("_iso").astype("category")

    # COMPOSE: named sums of existing columns, e.g. "everyone under
    # five" = f_00 + f_01 + m_00 + m_01. Machine 4 needs these and so
    # will anyone building an index by hand. Done here so the sum is
    # made once, from the columns as loaded.
    for name, parts in (compose or {}).items():
        missing = [c for c in parts if c not in pts.columns]
        if missing:
            raise ValueError(
                f"Cannot build {name!r}: no such column(s) "
                f"{', '.join(missing)}.")
        pts[name] = pts[list(parts)].sum(axis=1)
        print(f"[folder] {name} = {len(parts)} columns, "
              f"{pts[name].sum():,.1f} people")

    if not keep_zero:
        # iso3 is a LABEL, not a measurement. Every other place that
        # walks the columns had to learn the same thing.
        vals = [c for c in pts.columns
                if c not in ("gx", "gy", "iso3", "lon", "lat")]
        pts = pts.loc[pts[vals].to_numpy().sum(axis=1) > 0].copy()

    pts["lon"] = ref["c"] + (pts["gx"] + 0.5) * ref["a"]
    pts["lat"] = ref["f"] + (pts["gy"] + 0.5) * ref["e"]
    front = ["lon", "lat"] + (["iso3"] if "iso3" in pts.columns else [])
    # keep_index: carry the INTEGER LATTICE INDICES out with the
    # points, so a layer snapped to the same grid joins EXACTLY rather
    # than by distance (BACKLOG 220). Off by default, because they are
    # machinery and most callers only want coordinates.
    if keep_index:
        front += ["gx", "gy"]
    cols = front + [c for c in pts.columns
                    if c not in ("gx", "gy", "lon", "lat", "iso3")]
    pts = pts[cols].reset_index(drop=True)

    if sum_cohorts:
        lab_cols = [c for c in pts.columns
                    if c not in ("lon", "lat", "iso3")]
        both = totals_overlap_parts(lab_cols)
        if both:
            raise ValueError(
                f"This folder holds TOTALS as well as their parts - "
                f"{len(both)} of them, such as {both[0]!r}, which is "
                f"exactly {both[0].replace('t_', 'f_', 1)} plus "
                f"{both[0].replace('t_', 'm_', 1)}. Adding every column "
                "together would count everybody twice. Choose one set: "
                "either keep only the t_ files, or keep only the f_ and "
                "m_ files, and point this at that folder.")
        pts["pop"] = pts[lab_cols].sum(axis=1)
        keep = ["lon", "lat"] + (["iso3"] if "iso3" in pts.columns else [])
        pts = pts[keep + ["pop"]]

    man["labels"] = seen
    man["crs"] = ref["crs"]
    man["points"] = int(len(pts))
    print(f"[folder] {len(paths)} raster(s) -> {len(pts):,} points, "
          f"{len(man['labels'])} column(s), CRS {ref['crs']}")
    if man["unparsed"]:
        print(f"[folder] {len(man['unparsed'])} filename(s) did not match "
              "any known convention - column named from the filename. "
              "Pass labels={...} or pattern=r'...' to name them yourself.")
    return pts, man


# ------------------------------------------------------- to the engine
def _warn_aliasing(pts, unit_size, say=print):
    """Say so when the analysis grid beats against the source lattice."""
    import math

    if len(pts) < 2 or unit_size is None or unit_size <= 0:
        return
    lon = pts["lon"].to_numpy(dtype=float)
    lat = pts["lat"].to_numpy(dtype=float)
    step = np.unique(np.round(np.diff(np.unique(np.round(lon, 9))), 9))
    step = step[step > 0]
    if not step.size:
        return
    deg = float(step.min())
    if deg > 5.0:                       # already metres, not degrees
        src = deg
    else:
        mid = float(np.nanmedian(lat))
        src = deg * math.pi / 180 * 6378137.0 * math.cos(math.radians(mid))
    if src <= 0:
        return

    ratio = unit_size / src
    if ratio < 0.999:
        return                          # finer than the source: no merging
    frac = ratio - math.floor(ratio)
    if frac < 0.02 or frac > 0.98:
        return                          # a whole number of sources per cell
    swing = 1.0 / math.floor(ratio)
    if swing < 0.25:
        return                          # 10 or 11 per cell: not visible
    beat = src / min(frac, 1 - frac)
    say(f"[folder] WARNING: the source pixels are about {src:.0f} m "
        f"here and the analysis grid is {unit_size:g} m, so most cells "
        f"take {math.floor(ratio):.0f} source pixel(s) and some take "
        f"{math.floor(ratio)+1:.0f}. Those cells hold about "
        f"{swing*100:.0f}% more people, which shows as REGULAR BANDS "
        f"in Dist_k roughly every {beat/1000:.1f} km. It is an artefact "
        "of the re-binning, not of the data. Set the cell size to the "
        f"source spacing or finer - {src:.0f} m or less - and it goes "
        "away.")


def to_long(pts, value_name="population", key_name="cohort"):
    """A wide point table as one row per point per cohort.

    John: "I would assume we should have one column for the population,
    and possibly indicators of iso-code and treatment belonging - and
    not a wide dataset ... it would be good to have the option of
    making the dataset wide or long."

    Long is the tidier shape and the right one to look at. It is the
    WRONG one at continental scale: a wide table of 11.5 million
    points and 60 cohorts becomes 690 MILLION ROWS, which is why wide
    is what the analysis runs on. Offered as a choice, not a default.
    """
    keep = [c for c in ("lon", "lat", "iso3", "gx", "gy")
            if c in pts.columns]
    value_cols = [c for c in pts.columns if c not in keep]
    if not value_cols:
        return pts.copy()
    out = pts.melt(id_vars=keep, value_vars=value_cols,
                   var_name=key_name, value_name=value_name)
    return out.sort_values(keep[:2] + [key_name]).reset_index(drop=True)


def folder_to_cells(folders, weight: str | None = None,
                    compose: dict | None = None,
                    unit_size: float = 100.0,
                    epsg: int | None = None,
                    groups: list[str] | None = None,
                    **kw):
    """A folder of rasters straight to a CellData, ready for bigrun.

    BACKLOG 38. `bigrun` has been built and regression-tested since
    v1.16.8 and has never been reachable from the raster path - it
    could only be driven by hand-assembling a CellData. This is the
    wire.

    weight : the column holding PEOPLE. Defaults to the only value
             column when there is one, and refuses to guess otherwise.
    groups : cohort columns to carry as TREATMENT groups, so the run
             returns their share of each neighbourhood. They are
             weighted counts of people, which is what treat() means.
    epsg   : force a projection. Otherwise suggest_projection() picks
             one and its warnings are printed rather than swallowed.

    Returns (CellData, manifest). The manifest gains 'projection'.
    """
    from .cells import build_cells
    from .projection import suggest_projection

    pts, man = load_folder(folders, compose=compose, **kw)
    value_cols = [c for c in pts.columns
                  if c not in ("lon", "lat", "iso3")]

    # WEIGHT MAY BE A WORD (John, on his real download): "it asks for
    # the population, but all are populations". With sixty cohorts
    # there is no single column holding the people - the population is
    # their SUM, and which sum depends on which slices you have.
    #   'total'  sum the t_ columns   - ages are disjoint, so this is
    #                                   everybody, counted once
    #   'sexes'  sum the f_ and m_    - the same people by the other
    #                                   route
    # Mixing the two would double-count and is refused below.
    if isinstance(weight, str) and weight.lower() in ("total", "sexes"):
        want = "t_" if weight.lower() == "total" else ("f_", "m_")
        picked = [c for c in value_cols if c.startswith(want)]
        if not picked:
            raise ValueError(
                f"No {weight} columns here. Found: {value_cols[:6]}"
                f"{' ...' if len(value_cols) > 6 else ''}")
        pts["_people"] = pts[picked].sum(axis=1)
        print(f"[folder] weight '{weight}' = the sum of {len(picked)} "
              f"columns, {pts['_people'].sum():,.0f} people")
        weight = "_people"
    elif weight is None:
        if len(value_cols) != 1:
            raise ValueError(
                "Which people should define the neighbourhood? This "
                f"folder holds {len(value_cols)} population columns and "
                "k is a number of PEOPLE, so something has to say which "
                "ones.\n"
                "  weight='total'  - everybody, summed from the t_ "
                "columns (ages do not overlap, so nobody is counted "
                "twice)\n"
                "  weight='sexes'  - everybody, summed from f_ and m_ "
                "instead\n"
                "  weight='t_15_2026'  - or name one column, to make "
                "that cohort the population\n"
                f"Columns found: {', '.join(value_cols[:8])}"
                f"{' ...' if len(value_cols) > 8 else ''}")
        weight = value_cols[0]

    # ALIASING BETWEEN THE SOURCE LATTICE AND THE ANALYSIS GRID.
    # John's stripes. WorldPop "1 km" is 30 arc-seconds, which at 2 S
    # is 927 m - NOT 1000. Binning a 927 m lattice onto a 1000 m grid
    # gives most cells ONE source pixel and every thirteenth TWO, so
    # those cells hold twice the population of their neighbours. Dist_k
    # is driven by local density, so the doubles appear as regular
    # bands of shorter distances - a moire visible right across a
    # continent, and neither a data fault nor an arithmetic one.
    # WORST WHEN unit IS JUST ABOVE THE SOURCE SPACING, because the
    # count then alternates between 1 and 2 - a 100% density swing. At
    # unit = 10x the source it is 10 or 11, a 10% swing, invisible.
    _warn_aliasing(pts, unit_size, say=print)

    adv = suggest_projection(pts)
    if epsg is None:
        epsg = adv.epsg
    print(f"[folder] projection: EPSG:{epsg} - {adv.name}")
    print(f"[folder]   {adv.rationale}")
    for w in adv.warnings:
        print(f"[folder]   WARNING: {w}")
    if adv.tiled_run_recommended:
        print("[folder]   this extent wants a TILED run: see "
              "equipop.bigrun.run_knn_counts_tiled")

    from pyproj import Transformer
    tr = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    x, y = tr.transform(pts["lon"].to_numpy(), pts["lat"].to_numpy())
    pts["_x"], pts["_y"] = x, y

    # A GROUP COLUMN IS MULTIPLIED BY THE WEIGHT inside build_cells
    # (cells.py: bsums = sum(g[v] * w)), because a group is normally a
    # 0/1 marker and the weight turns it into people. A COMPOSED GROUP
    # IS ALREADY A HEADCOUNT, so handing it over as it stands would
    # multiply children by the total population. Convert to the share
    # of the weight, which the multiplication then turns back into the
    # count it started as.
    for gname in (groups or []):
        if gname in pts.columns and gname != weight:
            w = pts[weight].to_numpy(dtype=float)
            import numpy as _np
            pts[gname] = _np.where(w > 0,
                                   pts[gname].to_numpy(dtype=float) / w,
                                   0.0)

    cd = build_cells(pts, "_x", "_y", unit_size=unit_size,
                     binary_vars=groups or None, weights=weight)
    man["projection"] = {"epsg": int(epsg), "name": adv.name,
                         "warnings": list(adv.warnings)}
    man["weight_column"] = weight
    print(f"[folder] {len(pts):,} points -> {len(cd):,} cells of "
          f"{unit_size:g} m, holding {cd.n.sum():,.1f} people")
    return cd, man
