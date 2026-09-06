"""
inventory.py - WHAT IS IN A FOLDER, so a merge can be exact.

John: "could we generate a short meta text saved with each download
specifying the contents ... then the mergers can use the meta data for
dropdown menus, and the user can spend quality time on other matters."

TWO DIFFERENT OBJECTS, AND ONLY ONE BELONGS TO MACHINE 5.

The MANIFEST (equipop_fetch.json) records PROVENANCE - what was
fetched, from where, when, under which licence, with which checksum.
Machine 5 writes it and MUST NOT open the files, because opening them
is analysis and the standing rule is that a fetcher downloads and
stops (HANDOVER 13 section 3c).

The INVENTORY (equipop_inventory.json, this file) records CONTENTS -
layers, fields, CRS, geometry, extent, and the distinct values of the
columns you would actually group on. That needs the files READ, so it
belongs on the analysis side and is written once, by machine 3, the
first time a folder is seen.

THE LATTICE IS THE POINT. Two folders on the same lattice join by
integer index and the result is exact. Different lattices force a
decision - resample, or refuse - and BACKLOG 239 exists because that
decision was once made silently, merging rasters 3,300 km apart.
So the inventory GROUPS FILES BY LATTICE and says which sets can be
combined without a resample.

IT DEGRADES RATHER THAN FAILING. No rasterio, no raster detail; no
geopandas, no vector detail; an unreadable file is recorded WITH ITS
ERROR rather than skipped, because a file silently missing from an
inventory is worse than one listed as unreadable.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

INVENTORY = "equipop_inventory.json"

# Columns worth listing the distinct values of. OSM's fclass is the
# reason this exists: John groups cafe/restaurant/fast_food into
# "eateries" and needs to see what is actually present.
CLASS_COLUMNS = ("fclass", "class", "type", "category", "code",
                 "highway", "amenity", "landuse", "natural")

# A class column with more distinct values than this is an identifier,
# not a classification, and listing it would bury the useful ones.
MAX_CLASSES = 60


def _utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lattice_key(crs, transform, decimals=9):
    """A grid's identity: CRS, pixel size, and the origin's OFFSET
    within one pixel.

    NOT the origin itself. Two rasters covering different areas of the
    same grid have different origins and are still the same lattice -
    what matters is whether their cell boundaries coincide, which is
    the origin modulo the pixel size.
    """
    a, e = float(transform[0]), float(transform[4])
    c, f = float(transform[2]), float(transform[5])
    ox = round(c % a, decimals) if a else 0.0
    oy = round(f % e, decimals) if e else 0.0
    return (f"{crs}|{round(a, decimals)}x{round(e, decimals)}"
            f"|{ox},{oy}")


# ---------------------------------------------------------- rasters
def _raster(path):
    import rasterio
    with rasterio.open(path) as r:
        t = r.transform
        return {
            "kind": "raster",
            "crs": str(r.crs) if r.crs else None,
            "width": r.width, "height": r.height,
            "bands": r.count,
            "pixel_size": [abs(t[0]), abs(t[4])],
            "origin": [t[2], t[5]],
            "nodata": (None if r.nodata is None else float(r.nodata)),
            "dtype": str(r.dtypes[0]),
            "bounds": [float(x) for x in r.bounds],
            "lattice": lattice_key(r.crs, t),
        }


# ---------------------------------------------------------- vectors
def _vector(path, deep=True):
    """Layers, fields and - the useful part - the distinct values of
    any classification column.

    Reads the CLASS COLUMN ONLY, never the geometry, so a 700 MB
    country extract is inventoried without loading it.
    """
    import pyogrio

    out = []
    try:
        layers = [l[0] for l in pyogrio.list_layers(path)]
    except Exception:
        layers = [None]

    for layer in layers:
        info = pyogrio.read_info(path, layer=layer)
        # `fields` IS A NUMPY ARRAY, so `x or []` evaluates its
        # truthiness and raises "the truth value of an array with more
        # than one element is ambiguous". Claude wrote `or []` from
        # habit without reading what read_info returns - and because
        # unreadable files are RECORDED rather than skipped, the error
        # was there to find instead of two files quietly vanishing.
        raw = info.get("fields")
        fields = [] if raw is None else [str(x) for x in raw]
        entry = {
            "kind": "vector",
            "layer": layer,
            "crs": str(info.get("crs")) if info.get("crs") else None,
            "geometry": info.get("geometry_type"),
            "features": int(info.get("features") or 0),
            "fields": fields,
            "bounds": (None if info.get("total_bounds") is None
                       else [float(x) for x in info["total_bounds"]]),
        }
        if deep:
            classes = {}
            for col in CLASS_COLUMNS:
                if col not in fields:
                    continue
                try:
                    got = pyogrio.read_dataframe(
                        path, layer=layer, columns=[col],
                        read_geometry=False)
                    vals = sorted(
                        {str(v) for v in got[col].dropna().unique()})
                except Exception as exc:            # pragma: no cover
                    entry.setdefault("warnings", []).append(
                        f"could not read {col}: {exc}")
                    continue
                if len(vals) > MAX_CLASSES:
                    # AN IDENTIFIER, NOT A CLASSIFICATION. Listing
                    # 40,000 street names would bury fclass.
                    classes[col] = {
                        "distinct": len(vals),
                        "note": "too many to list - this looks like "
                                "an identifier, not a class"}
                else:
                    classes[col] = {"distinct": len(vals),
                                    "values": vals}
            if classes:
                entry["classes"] = classes
        out.append(entry)
    return out


# -------------------------------------------------------------- run
def inventory(folder, say=print, deep=True, write=True):
    """Describe a folder's contents. Reads; changes nothing."""
    folder = str(folder)
    if not os.path.isdir(folder):
        raise ValueError(f"Not a folder: {folder}")

    files, warnings = [], []
    have_rio = have_pyogrio = True
    try:
        import rasterio                             # noqa: F401
    except ImportError:
        have_rio = False
        warnings.append("rasterio is not installed - rasters are "
                        "listed by name only.")
    try:
        import pyogrio                              # noqa: F401
    except ImportError:
        have_pyogrio = False
        warnings.append("pyogrio is not installed - vector files are "
                        "listed by name only. pip install pyogrio")

    RAST = (".tif", ".tiff", ".vrt", ".img", ".asc")
    VECT = (".shp", ".gpkg", ".geojson", ".json", ".zip", ".gdb",
            ".fgb", ".parquet")

    for root, _dirs, names in os.walk(folder):
        for n in sorted(names):
            if n in (INVENTORY, "equipop_fetch.json"):
                continue
            path = os.path.join(root, n)
            rel = os.path.relpath(path, folder)
            low = n.lower()
            base = {"file": rel,
                    "bytes": os.path.getsize(path)}
            try:
                if low.endswith(RAST) and have_rio:
                    files.append({**base, **_raster(path)})
                elif low.endswith(VECT) and have_pyogrio:
                    for v in _vector(path, deep=deep):
                        files.append({**base, **v})
                else:
                    files.append({**base, "kind": "other"})
            except Exception as exc:
                # RECORDED, NOT SKIPPED. A file missing from an
                # inventory without explanation is worse than one
                # listed as unreadable.
                files.append({**base, "kind": "unreadable",
                              "error": f"{type(exc).__name__}: {exc}"})

    # WHICH FILES SHARE A GRID - the reason this exists.
    lattices = {}
    for f in files:
        if f.get("lattice"):
            lattices.setdefault(f["lattice"], []).append(f["file"])

    from .. import __version__
    inv = {"made_by": f"EquiPop {__version__}", "made_utc": _utc(),
           "folder": os.path.abspath(folder), "files": files,
           "lattices": lattices, "warnings": warnings}

    if write:
        with open(os.path.join(folder, INVENTORY), "w",
                  encoding="utf-8") as fh:
            json.dump(inv, fh, indent=2, ensure_ascii=False)

    kinds = {}
    for f in files:
        kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
    say(f"[inventory] {len(files)} item(s): "
        + ", ".join(f"{v} {k}" for k, v in sorted(kinds.items())))
    if lattices:
        say(f"[inventory] {len(lattices)} lattice(s):")
        for key, members in lattices.items():
            say(f"    {len(members)} file(s) on {key}")
        if len(lattices) > 1:
            say("[inventory] MORE THAN ONE LATTICE. Files on different "
                "grids cannot be merged by index - one set must be "
                "resampled, or kept separate.")
    for w in warnings:
        say(f"[inventory] {w}")
    return inv


def read_inventory(folder):
    p = os.path.join(str(folder), INVENTORY)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def classes_in(folder, column="fclass"):
    """Every distinct value of a class column, across the folder.

    What a grouping tool needs to populate a dropdown - and it comes
    from THE USER'S OWN DATA rather than a list written from
    documentation, which is how the WorldPop naming registry failed on
    all 120 of John's files (BACKLOG 211).
    """
    inv = read_inventory(folder)
    if inv is None:
        raise ValueError(
            f"No {INVENTORY} in {folder}. Run inventory() first.")
    out = {}
    for f in inv["files"]:
        got = (f.get("classes") or {}).get(column)
        if got and "values" in got:
            out.setdefault(f["file"], {})[f.get("layer")] = got["values"]
    return out
