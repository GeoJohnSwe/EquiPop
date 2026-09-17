"""
vectorjoin.py - VECTOR FEATURES REDUCED TO VALUES ON THE LATTICE.

The missing half of John's OSM plan. Points already land on the grid
(latticejoin); lines and polygons did not, and LINES ARE WHAT FRICTION
NEEDS: `features_to_friction()`, `load_friction_table()` and
`run_knn_friction()` have existed for months waiting for this input.

WHAT THIS IS AND IS NOT
-----------------------
EquiPop reduces geometry to VALUES ON A LATTICE. It is not becoming a
GIS. Intersect, within and buffer as general operations belong in
QGIS, which does them better; what EquiPop adds is the lattice and the
k-neighbourhood. If this file grows spatial predicates for their own
sake, that boundary is gone.

THE UNIT IS THE MEASURE. John: "if we declare that the longest road
stretch in the unit defines the friction value we need to know WHERE
it is the longest". Quite so - "longest" is meaningless without a
cell, so friction is a property of THE CELL, not of the road. The
same aliasing rule applies as everywhere else: choose a unit at or
below the source spacing.

CLASSES COME FROM THE DATA. The groups a user works with - cafe plus
restaurant plus fast_food as "eateries" - are a DEFINITION they
supply. The values available to group are read from their own extract
by the inventory, never from a schema document: that is how the
WorldPop naming registry failed on all 120 of John's files.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["lines_to_cells", "areas_to_cells", "apply_groups",
           "VectorJoinError"]


class VectorJoinError(Exception):
    """Refused, with the reason in plain words."""


def apply_groups(values, groups):
    """Map many class values onto few group names.

    `groups` is {group: [value, ...]}. A value in no group keeps its
    own name, so nothing vanishes silently - a class disappearing
    from a classification is this project's signature fault.
    """
    lookup = {}
    for name, members in (groups or {}).items():
        for m in members:
            if m in lookup and lookup[m] != name:
                raise VectorJoinError(
                    f"{m!r} is in two groups: {lookup[m]!r} and "
                    f"{name!r}. A value belongs to one group, or the "
                    "totals count it twice.")
            lookup[m] = name
    return pd.Series(values).map(lambda v: lookup.get(v, v))


from pyproj import CRS as _CRS


def _lattice(like):
    """The grid a set of features is being reduced onto."""
    from .latticejoin import lattice_of
    if isinstance(like, dict):
        return like
    return lattice_of(like)


def lines_to_cells(gdf, like, class_col="fclass", groups=None,
                   name="length", say=print):
    """LENGTH of each class within each cell.

    The friction input. A road crossing four cells contributes its
    length in each - so the answer is a property of the CELL, which is
    what "the longest stretch in the unit" requires.

    Returns one row per occupied cell with one column per class,
    holding metres, plus `<name>_total` and `<name>_top` - the class
    with the greatest length there, which is the longest-wins friction
    rule stated directly.
    """
    try:
        import geopandas as gpd
        from shapely.geometry import box
    except ImportError as e:                        # pragma: no cover
        raise VectorJoinError(
            "Reducing lines to cells needs geopandas: "
            "pip install geopandas") from e

    lat = _lattice(like)
    if gdf.crs is None:
        raise VectorJoinError(
            "The features carry NO coordinate system, so they cannot "
            "be placed on the lattice. Assign one first.")
    if str(gdf.crs) != str(lat["crs"]):
        say(f"[vector] reprojecting features {gdf.crs} -> {lat['crs']}")
        gdf = gdf.to_crs(lat["crs"])

    if class_col not in gdf.columns:
        raise VectorJoinError(
            f"No {class_col!r} column. The layer has: "
            + ", ".join(map(str, gdf.columns[:12])))

    work = gdf[[class_col, "geometry"]].copy()
    work[class_col] = apply_groups(work[class_col].astype(str), groups)

    # CUT EVERY FEATURE AT THE CELL BOUNDARIES. A road is not assigned
    # to one cell - it is DIVIDED between the cells it crosses, which
    # is the only way "length within this cell" means anything.
    a, e = float(lat["a"]), float(lat["e"])
    c, f = float(lat["c"]), float(lat["f"])
    minx, miny, maxx, maxy = work.total_bounds
    gx0, gx1 = int(np.floor((minx - c) / a)), int(np.ceil((maxx - c) / a))
    gy0, gy1 = (int(np.floor((maxy - f) / e)),
                int(np.ceil((miny - f) / e)))
    n_cells = (gx1 - gx0 + 1) * (gy1 - gy0 + 1)
    if n_cells > 4_000_000:
        raise VectorJoinError(
            f"That extent covers {n_cells:,} cells at this lattice, "
            "which will not finish in reasonable time. Clip the "
            "features, or use a coarser grid.")

    cells, rows = [], []
    for gx in range(gx0, gx1 + 1):
        x0 = c + gx * a
        for gy in range(gy0, gy1 + 1):
            y0 = f + gy * e
            cells.append((gx, gy))
            rows.append(box(min(x0, x0 + a), min(y0, y0 + e),
                            max(x0, x0 + a), max(y0, y0 + e)))
    grid = gpd.GeoDataFrame(
        {"gx": [g[0] for g in cells], "gy": [g[1] for g in cells]},
        geometry=rows, crs=lat["crs"])

    cut = gpd.overlay(work, grid, how="intersection",
                      keep_geom_type=True)
    if cut.empty:
        raise VectorJoinError(
            "No feature falls on this lattice. Are they the same "
            "part of the world?")
    # LENGTH IN A GEOGRAPHIC CRS IS DEGREES, NOT METRES. WorldPop's
    # lattice is EPSG:4326, so a 1 km road measured 0.009 and every
    # friction value would have been wrong - and geopandas WARNED,
    # into a log nobody was reading (BACKLOG 282). Measure on the
    # ellipsoid instead, which is exact and needs no projection
    # choice.
    if _CRS.from_user_input(lat["crs"]).is_geographic:
        from pyproj import Geod
        geod = Geod(ellps="WGS84")
        cut["_m"] = [geod.geometry_length(g) for g in cut.geometry]
        say("[vector] the lattice is geographic, so lengths are "
            "measured ON THE ELLIPSOID and reported in metres.")
    else:
        cut["_m"] = cut.geometry.length

    wide = (cut.groupby(["gx", "gy", class_col])["_m"].sum()
            .unstack(fill_value=0.0).reset_index())
    value_cols = [x for x in wide.columns if x not in ("gx", "gy")]
    wide[f"{name}_total"] = wide[value_cols].sum(axis=1)
    wide[f"{name}_top"] = wide[value_cols].idxmax(axis=1)

    say(f"[vector] {len(work):,} line(s) -> {len(wide):,} cells, "
        f"{len(value_cols)} class(es): "
        + ", ".join(map(str, value_cols[:8]))
        + (" ..." if len(value_cols) > 8 else ""))
    say(f"[vector] lengths are metres WITHIN EACH CELL, so "
        f"'{name}_top' is the longest-stretch-wins rule. A cell is "
        f"{abs(a):g} x {abs(e):g} in {lat['crs']}.")
    return wide


def _grid_for(work, lat, gpd):
    """The cells a set of features touches, as polygons."""
    from shapely.geometry import box
    a, e = float(lat["a"]), float(lat["e"])
    c, f = float(lat["c"]), float(lat["f"])
    minx, miny, maxx, maxy = work.total_bounds
    gx0, gx1 = int(np.floor((minx - c) / a)), int(np.ceil((maxx - c) / a))
    gy0, gy1 = (int(np.floor((maxy - f) / e)),
                int(np.ceil((miny - f) / e)))
    n = (gx1 - gx0 + 1) * (gy1 - gy0 + 1)
    if n > 4_000_000:
        raise VectorJoinError(
            f"That extent covers {n:,} cells at this lattice, which "
            "will not finish in reasonable time. Clip the features, "
            "or use a coarser grid.")
    cells, rows = [], []
    for gx in range(gx0, gx1 + 1):
        x0 = c + gx * a
        for gy in range(gy0, gy1 + 1):
            y0 = f + gy * e
            cells.append((gx, gy))
            rows.append(box(min(x0, x0 + a), min(y0, y0 + e),
                            max(x0, x0 + a), max(y0, y0 + e)))
    return gpd.GeoDataFrame(
        {"gx": [g[0] for g in cells], "gy": [g[1] for g in cells]},
        geometry=rows, crs=lat["crs"]), abs(a * e)


def areas_to_cells(gdf, like, class_col="fclass", groups=None,
                   name="cover", say=print):
    """SHARE of each cell covered by each class, 0 to 1.

    Water and buildings are coverage and barriers rather than
    friction, so a FRACTION is what a barrier rule needs - raw area
    would depend on the cell size and stop being comparable between
    runs.
    """
    try:
        import geopandas as gpd
    except ImportError as e:                        # pragma: no cover
        raise VectorJoinError(
            "Reducing polygons to cells needs geopandas: "
            "pip install geopandas") from e

    lat = _lattice(like)
    if gdf.crs is None:
        raise VectorJoinError(
            "The features carry NO coordinate system, so they cannot "
            "be placed on the lattice. Assign one first.")
    if str(gdf.crs) != str(lat["crs"]):
        say(f"[vector] reprojecting features {gdf.crs} -> {lat['crs']}")
        gdf = gdf.to_crs(lat["crs"])
    if class_col not in gdf.columns:
        raise VectorJoinError(
            f"No {class_col!r} column. The layer has: "
            + ", ".join(map(str, gdf.columns[:12])))

    work = gdf[[class_col, "geometry"]].copy()
    work[class_col] = apply_groups(work[class_col].astype(str), groups)
    grid, cell_area = _grid_for(work, lat, gpd)

    cut = gpd.overlay(work, grid, how="intersection",
                      keep_geom_type=True)
    if cut.empty:
        raise VectorJoinError(
            "No feature falls on this lattice. Are they the same "
            "part of the world?")
    # AREA IN A GEOGRAPHIC CRS IS SQUARE DEGREES. Same fault as the
    # lengths; a share would come out right only by accident, because
    # BOTH the part and the whole are wrong by the same factor - but
    # only near the equator, and not at all once cells vary with
    # latitude.
    if _CRS.from_user_input(lat["crs"]).is_geographic:
        from pyproj import Geod
        geod = Geod(ellps="WGS84")
        cut["_a"] = [abs(geod.geometry_area_perimeter(g)[0])
                     for g in cut.geometry]
    else:
        cut["_a"] = cut.geometry.area
    wide = (cut.groupby(["gx", "gy", class_col])["_a"].sum()
            .unstack(fill_value=0.0).reset_index())
    value_cols = [x for x in wide.columns if x not in ("gx", "gy")]
    # THE CELL'S OWN AREA, PER CELL. On a geographic lattice a cell
    # shrinks towards the poles, so one figure for the whole grid
    # would make the share wrong everywhere except the middle - a
    # 30 arc-second cell is 860,000 m2 at the equator and 440,000 at
    # 60 degrees. Measured per cell rather than assumed.
    if _CRS.from_user_input(lat["crs"]).is_geographic:
        from pyproj import Geod
        geod = Geod(ellps="WGS84")
        own = {(g.gx, g.gy): abs(geod.geometry_area_perimeter(
            g.geometry)[0]) for g in grid.itertuples()}
        denom = wide.apply(lambda r: own[(r["gx"], r["gy"])], axis=1)
    else:
        denom = cell_area
    for col in value_cols:
        # A SHARE, not an area. Overlapping polygons of one class
        # could exceed the cell, so it is clipped at 1.
        wide[col] = (wide[col] / denom).clip(upper=1.0)
    wide[f"{name}_any"] = wide[value_cols].max(axis=1)
    say(f"[vector] {len(work):,} polygon(s) -> {len(wide):,} cells, "
        f"{len(value_cols)} class(es). Values are the SHARE of each "
        "cell covered, 0 to 1.")
    return wide


# ======================================================================
# v1.47.10 - VECTOR ONTO THE LATTICE, John's model (BACKLOG 298)
# ======================================================================

#: How much of a feature a cell has to hold before it counts.
PRESENCE = "presence"     # any positive overlap; one FEATURE, once
CLASS = "class"           # any positive overlap; one CLASS, once
MEASURE = "measure"       # length in metres, or area in m2
FIDELITIES = (PRESENCE, CLASS, MEASURE)

#: John's ruling, session 12: class present, as the default.
DEFAULT_FIDELITY = CLASS


def paths_to_cells(features, values, classes=None, unit_size=100.0,
                   fidelity=DEFAULT_FIDELITY, agg="sum"):
    """Charge each cell for the vector features that occupy it.

    THE MODEL IS JOHN'S, session 12, and it is about BARRIERS rather
    than composition. A barrier's cost is the cost of CROSSING it: a
    river that clips a corner still has to be crossed, and a river
    running corner to corner is crossed once too. So presence, not
    length, is the honest measure for friction - and length-weighting
    would be the wrong rule wearing the clothes of precision.

    WHY `class` AND NOT `presence` IS THE DEFAULT. OSM cuts one street
    into many records wherever a tag changes - a speed limit, a
    bridge, a name. John's Swedish extract holds 2,139,630 road
    features, and his own screenshot shows `unclassified` three times
    and `trunk_link` twice within one junction, all one street. Under
    `presence` a cell containing five segments of one street is
    charged five times, so the friction would be partly a fact about
    HOW THE DATA WAS CUT rather than about the geography - worst in
    cities, where segmentation is densest and where the artefact
    would matter most. Under `class` a motorway crossing a cell in
    forty pieces counts once.

    `measure` keeps the length or area instead. It is the only
    defensible rule for a COMPOSITION question - what share of this
    cell is forest - and the wrong one for a barrier.

    THE VALUE COMES FROM A FIELD THE USER PREPARED, not from a table
    in a dialog: John's ruling, and it keeps the vocabulary problem
    where the vocabulary is. Missing values are the caller's to fill;
    the convention that goes with `agg` is 0 for additive and 1 for
    multiplicative, both meaning "no effect".

    features : as friction.paths_to_friction - dicts of
        {"type": "line"|"polygon", "parts": [...]}.
    values   : one number per feature, from that field.
    classes  : one label per feature. REQUIRED for fidelity="class",
        because there is nothing to collapse on without it.

    Returns DataFrame(x, y, value) of charged cell MIDPOINTS.
    """
    import numpy as np
    import pandas as pd

    from .friction import _agg_cells, feature_cells

    fid = str(fidelity).strip().lower()
    if fid not in FIDELITIES:
        raise VectorJoinError(
            f"[vectorjoin] '{fidelity}' is not one of "
            f"{', '.join(FIDELITIES)}.")
    n = len(features)
    vals = np.asarray(values, float)
    if len(vals) != n:
        raise VectorJoinError(
            f"[vectorjoin] {n} features but {len(vals)} values")
    if np.isnan(vals).any():
        raise VectorJoinError(
            "[vectorjoin] missing values in the value field. Fill "
            "them first - 0 leaves an additive run unchanged, 1 "
            "leaves a multiplicative one unchanged - because a "
            "silent 0 and a real 0 must not look alike.")
    if fid == CLASS:
        if classes is None:
            raise VectorJoinError(
                "[vectorjoin] fidelity='class' needs a class per "
                "feature. Without one there is nothing to collapse "
                "on, and the result would be per-feature counting "
                "under another name.")
        if len(classes) != n:
            raise VectorJoinError(
                f"[vectorjoin] {n} features but {len(classes)} "
                "classes")

    acc: dict = {}
    seen: dict = {}                 # (cell, class) already charged
    u = float(unit_size)
    for idx in range(n):
        cells = feature_cells(features[idx], u)
        for (i, j), m in cells.items():
            if m <= 1e-9:           # corner and edge kisses are free
                continue
            mid = (i * u + u / 2, j * u + u / 2)
            if fid == CLASS:
                key = (mid, str(classes[idx]))
                if key in seen:
                    continue        # THE COLLAPSE: one class, once
                seen[key] = True
            acc.setdefault(mid, []).append(
                float(m) if fid == MEASURE else float(vals[idx]))
    out = _agg_cells(acc, agg)
    return out.rename(columns={"friction": "value"})
