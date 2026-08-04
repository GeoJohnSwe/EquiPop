# -*- coding: utf-8 -*-
"""
barriers.py - barriers and terrain, QGIS side.

A barrier turns plain distance into EFFORT: a river, a railway, a
lake or a steep slope makes the people on the other side farther
away in rounds rather than in metres. The engine that does this is
shared and already tested; what QGIS has to supply is the geometry,
read its own way.

That is the whole of this file. `points_to_friction`,
`paths_to_friction` and `raster_to_friction` take plain coordinate
lists and numbers - no arcpy, no PyQGIS - so the barrier arithmetic
is identical in both doors by construction, not by care.

One QGIS-specific duty: reprojecting. A barrier layer may be in a
different CRS from the points, and every coordinate must arrive in
the working CRS of the run or the barrier lands in the wrong place -
silently, and plausibly.
"""
import numpy as np

from qgis.core import (QgsCoordinateTransform, QgsProcessingException,
                       QgsProject, QgsWkbTypes)


def _transform(layer_crs, working_crs):
    """None when no reprojection is needed."""
    if (layer_crs is None or working_crs is None
            or layer_crs.authid() == working_crs.authid()):
        return None
    return QgsCoordinateTransform(layer_crs, working_crs,
                                  QgsProject.instance()
                                  .transformContext())


def _is_kind(source, wanted):
    try:
        geom_type = QgsWkbTypes.geometryType(source.wkbType())
    except Exception:
        return False
    return geom_type == wanted


def _value(feature, names, field, label):
    i = names.index(field) if field in names else -1
    if i < 0:
        raise QgsProcessingException(
            f"{label}: '{field}' is not a field of this layer.")
    v = feature.attributes()[i]
    try:
        return float(v)
    except (TypeError, ValueError):
        return np.nan


def barrier_to_friction(source, friction_field, unit, agg, channel,
                        working_crs=None, label="Barrier layer"):
    """One barrier layer -> a friction table the engine understands.

    Routes by WHAT the layer is, exactly as the ArcGIS door does:
    points get charged to the cell they sit in, lines and polygons to
    every cell their length or area actually touches.
    """
    from equipop.friction import points_to_friction, paths_to_friction

    if not friction_field:
        raise QgsProcessingException(
            f"{label}: choose the numeric friction field - the "
            "crossing cost, in rounds. A river that costs 3 means "
            "crossing it is as much effort as three cells of open "
            "ground.")

    names = source.fields().names()
    feats = list(source.getFeatures())
    if not feats:
        raise QgsProcessingException(f"{label}: no features.")

    tr = _transform(source.sourceCrs(), working_crs)
    if tr is not None:
        channel.info(
            f"{label}: reprojected from "
            f"{source.sourceCrs().authid()} to the working CRS for "
            "this run.")

    if _is_kind(source, 0):                      # points
        xs, ys, vs = [], [], []
        for f in feats:
            g = f.geometry()
            if g is None or g.isEmpty():
                continue
            if tr is not None:
                g.transform(tr)
            p = g.asPoint()
            xs.append(p.x())
            ys.append(p.y())
            vs.append(_value(f, names, friction_field, label))
        x = np.asarray(xs, float)
        y = np.asarray(ys, float)
        v = np.asarray(vs, float)
        ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(v)
        if (~ok).any():
            channel.warning(
                f"{label}: {int((~ok).sum())} point(s) with missing "
                "coordinates or friction were dropped.")
        try:
            fr = points_to_friction(x[ok], y[ok], v[ok],
                                    unit_size=float(unit), agg=agg)
        except ValueError as exc:
            raise QgsProcessingException(f"{label}: {exc}")
        channel.info(f"{label}: {len(fr)} friction cells from "
                     f"{int(ok.sum())} points (overlap rule: {agg}).")
        return fr

    features, values, bad = [], [], 0
    for f in feats:
        g = f.geometry()
        if g is None or g.isEmpty():
            bad += 1
            continue
        if tr is not None:
            g.transform(tr)
        parts = _paths_of(g)
        if not parts:
            bad += 1
            continue
        # the engine wants each feature as {"type": ..., "parts": ...}
        # so it knows whether to charge cells by LENGTH (a line) or by
        # AREA (a polygon) - the two are charged differently and
        # getting it wrong is silent
        kind = ("line"
                if QgsWkbTypes.geometryType(g.wkbType()) == 1
                else "polygon")
        features.append({"type": kind, "parts": parts})
        values.append(_value(f, names, friction_field, label))
    if bad:
        channel.warning(f"{label}: {bad} feature(s) with no usable "
                        "geometry were dropped.")
    if not features:
        raise QgsProcessingException(
            f"{label}: no usable geometry found.")
    _extent_check(features, values, unit, label, channel)
    try:
        fr = paths_to_friction(features, values,
                               unit_size=float(unit), agg=agg)
    except ValueError as exc:
        raise QgsProcessingException(f"{label}: {exc}")
    channel.info(f"{label}: {len(fr)} friction cells from "
                 f"{len(features)} feature(s) (overlap rule: {agg}).")
    return fr


def _paths_of(geom):
    """Every part of a line or polygon as a list of (x, y).

    Multipart matters: a river arrives as one feature with many
    parts, and taking only the first would leave most of it
    unguarded - which would look like a working barrier while
    quietly leaking.
    """
    parts = []
    try:
        if geom.isMultipart():
            if QgsWkbTypes.geometryType(geom.wkbType()) == 1:
                for line in geom.asMultiPolyline():
                    if len(line) >= 2:
                        parts.append([(p.x(), p.y()) for p in line])
            else:
                for poly in geom.asMultiPolygon():
                    for ring in poly:
                        if len(ring) >= 3:
                            parts.append([(p.x(), p.y())
                                          for p in ring])
        else:
            if QgsWkbTypes.geometryType(geom.wkbType()) == 1:
                line = geom.asPolyline()
                if len(line) >= 2:
                    parts.append([(p.x(), p.y()) for p in line])
            else:
                for ring in geom.asPolygon():
                    if len(ring) >= 3:
                        parts.append([(p.x(), p.y()) for p in ring])
    except Exception as exc:
        raise QgsProcessingException(
            f"Could not read the barrier geometry ({exc}).")
    return parts


def raster_to_friction_layer(raster_layer, unit, channel,
                             label="Friction raster"):
    """A raster of costs -> friction cells, sampled at analysis-cell
    midpoints by the shared engine."""
    from equipop.friction import raster_to_friction
    if raster_layer is None:
        return None
    try:
        provider = raster_layer.dataProvider()
        block = provider.block(1, raster_layer.extent(),
                               raster_layer.width(),
                               raster_layer.height())
        arr = np.array([[block.value(r, c)
                         for c in range(raster_layer.width())]
                        for r in range(raster_layer.height())],
                       dtype=float)
        ext = raster_layer.extent()
        cw = ext.width() / raster_layer.width()
        ch_ = ext.height() / raster_layer.height()
        nodata = provider.sourceNoDataValue(1)
    except Exception as exc:
        raise QgsProcessingException(
            f"{label}: could not read the raster ({exc}).")
    fr = raster_to_friction(arr, float(ext.xMinimum()),
                            float(ext.yMaximum()), float(cw),
                            float(ch_), unit_size=float(unit),
                            nodata=nodata)
    channel.info(f"{label}: sampled at analysis-cell midpoints -> "
                 f"{len(fr)} friction cells (NoData or zero = free).")
    return fr


def _extent_check(features, values, unit, label, channel):
    """Look at WHERE the barrier is before asking the engine to grind
    it (v1.27).

    John gave Malta's roads as a barrier for Sweden's POIs. The
    plausibility check would have said so plainly - but the engine's
    own value validation ran first and complained about something
    else entirely, so the useful message never appeared. Cheap
    checks go first.
    """
    import numpy as _np
    xs = [p[0] for feat in features for part in feat["parts"]
          for p in part]
    ys = [p[1] for feat in features for part in feat["parts"]
          for p in part]
    if not xs:
        return
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    if span < float(unit):
        raise QgsProcessingException(
            f"{label}: the whole barrier spans {span:,.1f} m, which "
            f"is less than one {unit:g} m cell. It cannot block "
            "anything. The usual cause is a barrier still in DEGREES "
            "while the analysis runs in metres - check its "
            "coordinate system.")


def check_plausible(fr, n_features, points_xy, unit, label,
                    channel):
    """Refuse a friction surface that cannot be right (v1.26.1).

    Malta, John's field test: 40,678 roads produced ONE friction
    cell, the run finished in 0.1 s, and 8,730 rows were filled with
    confident nonsense. The cause was a CRS mistake, but the deeper
    fault was that nothing objected to an absurd result.

    Two checks, both cheap and both about ORDERS OF MAGNITUDE rather
    than exactness:

      * a great many features collapsing into almost no cells means
        the barrier is in the wrong units - degrees against metres
        is the usual reason;
      * a barrier whose cells lie nowhere near the points cannot
        block anything, so it is either the wrong layer or the wrong
        projection.

    A wrong barrier is worse than no barrier: no barrier is visibly
    absent, while a wrong one looks like it worked.
    """
    import numpy as _np
    if fr is None or not len(fr):
        return
    n_cells = len(fr)
    if n_features >= 50 and n_cells <= max(2, n_features // 1000):
        raise QgsProcessingException(
            f"{label}: {n_features} features produced only "
            f"{n_cells} friction cell(s) at a cell size of {unit:g} "
            "m. That cannot be right - the barrier has almost no "
            "extent in the working coordinate system. The usual "
            "cause is a barrier layer in DEGREES while the analysis "
            "runs in metres: whole countries then fall inside a "
            "single cell. Check the barrier layer's CRS, or project "
            "it to the same metric system as the points.")

    x, y = points_xy
    fx = _np.asarray(fr["x"], float)
    fy = _np.asarray(fr["y"], float)
    px = _np.asarray(x, float)
    py = _np.asarray(y, float)
    px = px[_np.isfinite(px)]
    py = py[_np.isfinite(py)]
    if not len(px) or not len(fx):
        return
    pad = 50.0 * float(unit)
    overlaps = (fx.max() >= px.min() - pad and fx.min() <= px.max() + pad
                and fy.max() >= py.min() - pad
                and fy.min() <= py.max() + pad)
    if not overlaps:
        raise QgsProcessingException(
            f"{label}: the barrier lies nowhere near the points. The "
            f"barrier spans x {fx.min():,.0f}-{fx.max():,.0f}, "
            f"y {fy.min():,.0f}-{fy.max():,.0f}, while the points "
            f"span x {px.min():,.0f}-{px.max():,.0f}, "
            f"y {py.min():,.0f}-{py.max():,.0f}. Nothing would be "
            "blocked. Check that the barrier is the layer you meant "
            "and that its coordinate system matches.")
    channel.info(
        f"{label}: {n_cells} friction cells from {n_features} "
        f"feature(s), overlapping the points - looks sane.")


def merge_friction(tables, agg, channel):
    """Several barrier sources into one surface.

    Multi-source barriers were the point of the 1.17 value tables: a
    river AND a railway AND a lake, given together. The overlap rule
    decides what happens where two of them cross the same cell.
    """
    tables = [t for t in tables if t is not None and len(t)]
    if not tables:
        return None
    if len(tables) == 1:
        return tables[0]
    from equipop.friction import _agg_cells
    import pandas as pd
    merged = _agg_cells(pd.concat(tables, ignore_index=True), agg)
    channel.info(f"{len(tables)} barrier sources merged into "
                 f"{len(merged)} friction cells (overlap rule: "
                 f"{agg}).")
    return merged
