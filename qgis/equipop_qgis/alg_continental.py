# -*- coding: utf-8 -*-
"""
alg_continental.py - the QGIS door onto a folder of rasters.

BACKLOG 38. Deliberately THIN. Every decision about what a
continental run means lives in equipop.doors.continental.run_folder,
which the ArcGIS tool calls with the same arguments - John's ruling,
"one ring to rule them all, and different doors that can use it". The
doors in this project have drifted apart three times, and every time
it was because a rule lived in two places.

So what is genuinely QGIS's own here, and all this file adds: turning
Processing parameters into keyword arguments, and turning the result
table into a QgsFeatureSink.

Parameter names match the ArcGIS toolbox on purpose, so the shared
help explains both screens with identical words.
"""
from qgis.core import (QgsCoordinateReferenceSystem, QgsFeature, QgsField,
                       QgsFields, QgsGeometry, QgsPointXY,
                       QgsProcessingException,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString, QgsWkbTypes)
from qgis.PyQt.QtCore import QMetaType

from .base import EquipopAlgorithm

#: v1.47.7, BACKLOG 298. How much of a feature a cell has to hold.
#: Order fixed: the DEFAULT is "each class once", John's ruling.
JOIN_MODES = [
    "centroid only - the feature's midpoint, one cell",
    "each class once - any cell the feature genuinely touches",
    "length or share - metres of line, or fraction of cell covered",
]
JOIN_VALUES = ["centroid", "class", "measure"]

#: What happens when several charges land in one cell. Additive is
#: the barrier model's default since it began: a river crossed at a
#: railway costs both.
JOIN_COMBINE = [
    "add them up (a river AND a railway cost both)",
    "keep the largest",
    "keep the smallest",
    "average them",
]
JOIN_AGG = ["sum", "max", "min", "mean"]


class ContinentalRasters(EquipopAlgorithm):
    """A folder of population rasters, straight to k-neighbourhoods."""

    # The key into equipop.doors.help, so this tool and the Pro tool
    # explain themselves with IDENTICAL words. base.py reads it.
    EQP_TOOL = "ContinentalRasters"

    def name(self):
        return "continentalrasters"

    # WRITTEN DOWN, NOT IMPORTED. displayName runs while QGIS
    # builds the toolbox, so importing the package here would
    # kill the whole plugin when equipop is missing - BACKLOG
    # 218, reintroduced and caught the same day. A test pins
    # this against doors/help.LABELS so it cannot drift.
    EQP_LABEL = "3. Raster Data Curation"

    def displayName(self):
        return self.EQP_LABEL

    def initAlgorithm(self, config=None):
        self.add(QgsProcessingParameterFile(
            "folder", "1a. Folder of population rasters (.tif)",
            behavior=QgsProcessingParameterFile.Folder))
        self.add(QgsProcessingParameterString(
            "k", "1b. Neighbourhood sizes, in PEOPLE "
                 "(blank = just give me the points)",
            defaultValue="", optional=True))
        self.add(QgsProcessingParameterNumber(
            "unit", "1c. Analysis cell size, in metres",
            type=QgsProcessingParameterNumber.Double,
            defaultValue=1000.0, minValue=0.000001))
        self.add(QgsProcessingParameterCrs(
            "crs", "2a. Projection to work in (blank = suggested)",
            optional=True), advanced=True)
        self.add(QgsProcessingParameterString(
            "weight", "2b. Which people define the neighbourhood - "
                      "'total', 'sexes', or one column name",
            optional=True), advanced=True)
        self.add(QgsProcessingParameterBoolean(
            "sumcohorts", "2c. Add all cohorts into one population",
            defaultValue=False), advanced=True)
        self.add(QgsProcessingParameterString(
            "pattern", "2d. Your own filename pattern (blank = the "
                       "known conventions)",
            optional=True), advanced=True)
        self.add(QgsProcessingParameterFolderDestination(
            "tiles", "3a. Folder for a TILED, resumable run "
                     "(blank = run in memory)",
            optional=True), advanced=True)
        # WIDE OR LONG (John). Wide is what the analysis runs on and
        # what scales - 11.5 million points x 60 cohorts would be 690
        # MILLION rows long. Long is the tidier shape to read, so it
        # is offered, not imposed.
        # BACKLOG 220/238 (John): "facilitate for the integration of
        # shapefiles - i.e. points can have values that can populate
        # raster grids > merges to the generated points."
        # QGIS already counts points in cells and does it well. THE
        # HARD PART IS THE LATTICE: EquiPop knows the exact grid the
        # raster points sit on and QGIS does not, so a join done
        # outside is approximate at cell boundaries. Here it is exact,
        # because the grid is ours.
        # v1.47.7: POINTS, LINES OR POLYGONS. types=[0] meant points
        # only, and every non-point layer was silently reduced to its
        # centroid - which for a 2.1-million-feature road network puts
        # a whole street in whichever cell its midpoint happened to
        # land in.
        self.add(QgsProcessingParameterFeatureSource(
            "joinlayer", "2e. A layer to put on the same grid - "
                         "points, roads, land use, water...",
            optional=True), advanced=True)
        self.add(QgsProcessingParameterEnum(
            "joinhow", "2f. How a feature charges a cell",
            options=JOIN_MODES, defaultValue=1, optional=True),
            advanced=True)
        self.add(QgsProcessingParameterField(
            "joinclass", "2g. The class field (fclass, highway, "
                         "landuse) - needed for 'each class once'",
            parentLayerParameterName="joinlayer", optional=True),
            advanced=True)
        self.add(QgsProcessingParameterField(
            "joinfield", "2h. The value field you prepared (blank = "
                         "1 per charge)",
            parentLayerParameterName="joinlayer", optional=True),
            advanced=True)
        self.add(QgsProcessingParameterEnum(
            "joincombine", "2i. When several charges land in one cell",
            options=JOIN_COMBINE, defaultValue=0, optional=True),
            advanced=True)
        self.add(QgsProcessingParameterString(
            "joinname", "2j. Name for the new column",
            defaultValue="joined", optional=True), advanced=True)
        self.add(QgsProcessingParameterEnum(
            "shape", "3c. Table shape",
            options=["Wide - one column per cohort",
                     "Long - one row per point per cohort"],
            defaultValue=0), advanced=True)
        self.add(QgsProcessingParameterCrs(
            "outcrs", "3b. Write the output in (blank = the same "
                      "projection the rasters were in)",
            optional=True), advanced=True)
        self.add(QgsProcessingParameterFeatureSink(
            "OUTPUT", "Neighbourhood results"))

    # -----------------------------------------------------------------
    def processAlgorithm(self, parameters, context, feedback):
        from equipop.doors.continental import ContinentalError, run_folder

        from .base import check_versions

        ch = self.channel(feedback)
        # A MODULE FUNCTION, not a method. Claude wrote
        # self.check_versions(ch) from a hurried reading of base.py and
        # QGIS reported it on John's first run. alg_counts.py had the
        # right form four lines into its own processAlgorithm.
        check_versions(ch)

        folder = self.parameterAsFile(parameters, "folder", context)
        # A BLANK k IS NOT AN ERROR: it means "just give me the
        # points" - the rasters as one point layer, every cohort a
        # field. John's folder has sixty populations and none of them
        # is "the" one, so demanding a k before producing anything
        # made the useful first step impossible.
        k_text = (self.parameterAsString(parameters, "k",
                                         context) or "").strip()
        ks = self._numbers(k_text, "k") if k_text else []
        unit = self.parameterAsDouble(parameters, "unit", context)
        weight = (self.parameterAsString(parameters, "weight",
                                         context) or "").strip() or None
        pattern = (self.parameterAsString(parameters, "pattern",
                                          context) or "").strip() or None
        summed = self.parameterAsBool(parameters, "sumcohorts", context)
        # An optional FolderDestination left alone does not arrive as
        # "" - QGIS fills it with the literal string TEMPORARY_OUTPUT.
        # Taken at face value that would write the tiles into a folder
        # of that name, silently. Blank means: run in memory.
        tiles = (self.parameterAsString(parameters, "tiles",
                                        context) or "").strip()
        if tiles in ("", "TEMPORARY_OUTPUT"):
            tiles = None

        epsg = None
        crs = self.parameterAsCrs(parameters, "crs", context)
        if crs is not None and crs.isValid():
            if crs.isGeographic():
                raise QgsProcessingException(
                    "That projection is in degrees. Neighbourhood work "
                    "needs metres - leave the box blank and one will be "
                    "suggested from the data.")
            code = crs.authid()
            if code.upper().startswith("EPSG:"):
                epsg = int(code.split(":", 1)[1])

        try:
            man = run_folder(folder, k_values=ks, unit_size=unit,
                             epsg=epsg, weight=weight,
                             sum_cohorts=summed, pattern=pattern,
                             out_dir=tiles, channel=ch)
        except (ContinentalError, ValueError) as exc:
            # The spine refuses in plain words. Do not add to them.
            # ValueError is here because the LOADER refuses that way -
            # John's first real folder raised one and QGIS printed a
            # Python traceback where a sentence belonged.
            raise QgsProcessingException(str(exc))

        man = self._join(parameters, context, man, ch)

        if "points_table" in man:
            if self.parameterAsEnum(parameters, "shape", context) == 1:
                from equipop.rasterfolder import to_long
                man["points_table"] = to_long(man["points_table"])
                ch.info("Long shape: one row per point per cohort, "
                        "with the cohort named in its own column.")
            table = man["points_table"].rename(
                columns={"lon": "EastWest", "lat": "NorthSouth"})
            # STAMP THE FOLDER'S OWN CRS, not 4326. The points-only
            # path wrote 4326 whatever the rasters were, so a folder
            # of GHSL Mollweide or UTM produced a layer labelled with
            # a CRS it was not in - and it would draw in the wrong
            # part of the world (BACKLOG 277, review finding 4).
            src = str(man.get("crs") or "EPSG:4326")
            code = (int(src.split(":", 1)[1])
                    if src.upper().startswith("EPSG:")
                    and src.split(":", 1)[1].isdigit() else None)
            if code is None:
                ch.warning(
                    f"The rasters are in {src!r}, which is not a plain "
                    "EPSG code. The output layer carries no CRS - set "
                    "it by hand before using the coordinates.")
            man.setdefault("projection", {})["epsg"] = code
        elif tiles:
            from equipop.bigrun import load_tiled
            table = load_tiled(tiles)
        else:
            table = man["results"]

        return {"OUTPUT": self._write(table, man, parameters, context,
                                      feedback)}

    # -----------------------------------------------------------------
    def _join(self, parameters, context, man, ch):
        """Put a vector layer onto the raster lattice.

        v1.47.7, BACKLOG 298. Until now this took the CENTROID of
        every feature, which is right for shops and stops and badly
        wrong for a road network: a street crossing forty cells was
        counted once, wherever its midpoint fell.

        NO GEOPANDAS. The door reads geometries through QGIS's own
        API into plain coordinate lists, and friction.feature_cells
        does the clipping - it is explicitly geopandas-free, written
        for the Pro clone that cannot grow it. The lattice join was
        about to be designed around geopandas as an accepted
        dependency before anyone checked.
        """
        src = self.parameterAsSource(parameters, "joinlayer", context)
        if src is None:
            return man
        from equipop.latticejoin import (join_to_points, lattice_of,
                                         snap_to_lattice)

        table = man.get("points_table")
        if table is None or "gx" not in table.columns:
            raise QgsProcessingException(
                "The lattice join needs the point table, so leave box "
                "1b (neighbourhood sizes) empty. Run the join first, "
                "then feed the result to machine 1.")

        how = JOIN_VALUES[(self.parameterAsEnums(
            parameters, "joinhow", context) or [1])[0]]
        agg = JOIN_AGG[(self.parameterAsEnums(
            parameters, "joincombine", context) or [0])[0]]
        field = (self.parameterAsString(parameters, "joinfield",
                                        context) or "").strip()
        klass = (self.parameterAsString(parameters, "joinclass",
                                        context) or "").strip()
        name = (self.parameterAsString(parameters, "joinname",
                                       context) or "joined").strip()
        lat = lattice_of(self.parameterAsFile(parameters, "folder",
                                              context))
        # THE LAYER MUST BE IN THE LATTICE'S OWN CRS. Reprojecting is
        # the door's job - only the door knows what the layer was in.
        from qgis.core import (QgsCoordinateReferenceSystem,
                               QgsCoordinateTransform, QgsProject)
        want = QgsCoordinateReferenceSystem(lat["crs"])
        tr = (QgsCoordinateTransform(src.sourceCrs(), want,
                                     QgsProject.instance())
              if src.sourceCrs() != want else None)

        # A POINT HAS NO LENGTH AND NO AREA, so the three rules
        # coincide for it: a point is in a cell or it is not, which is
        # what "centroid" means. Demanding a class field for a layer
        # of bus stops would be a box asking a question the geometry
        # cannot answer - and it broke every existing point join the
        # moment the default changed. Detected, not asked.
        from qgis.core import QgsWkbTypes as _W
        if _W.geometryType(src.wkbType()) == _W.PointGeometry:
            if how != "centroid":
                ch.info(
                    "That layer is points, so each feature falls in "
                    "exactly one cell - the three rules in box 2f "
                    "mean the same thing here and 'centroid only' "
                    "was used.")
            how = "centroid"

        # WHAT MACHINE 6 IS FOR. If an inventory sits beside the data,
        # read it and say what the class vocabulary looks like - so a
        # user preparing a value field knows how many classes they
        # have to cover before they discover a gap in the output.
        _report_inventory(src, klass, ch)

        if how == "class" and not klass:
            raise QgsProcessingException(
                "Box 2f is set to 'each class once', so box 2g needs "
                "the class field - fclass on an OSM layer. Without "
                "one there is nothing to collapse on, and every "
                "SEGMENT would be charged separately: OSM cuts one "
                "street into many records wherever a tag changes, so "
                "a junction with five pieces of the same road would "
                "cost five times.")

        if how == "centroid":
            return self._join_centroid(src, tr, field, name, lat,
                                       table, man, ch,
                                       join_to_points, snap_to_lattice)
        return self._join_shapes(src, tr, how, agg, field, klass, name,
                                 lat, table, man, ch, join_to_points)

    # -----------------------------------------------------------------
    def _join_centroid(self, src, tr, field, name, lat, table, man, ch,
                       join_to_points, snap_to_lattice):
        """The rule this box had before 1.47.7 - kept, because for
        shops, clinics and bus stops a centroid IS the feature."""
        xs, ys, vals = [], [], []
        for f in src.getFeatures():
            g = f.geometry()
            if g is None or g.isEmpty():
                continue
            pt = g.centroid().asPoint()
            if tr is not None:
                pt = tr.transform(pt)
            xs.append(pt.x())
            ys.append(pt.y())
            if field:
                v = f[field]
                vals.append(float(v) if v is not None else 0.0)
        if not xs:
            raise QgsProcessingException(
                "That layer has no usable geometry.")
        snapped = snap_to_lattice(
            xs, ys, lattice=lat, name=name,
            values=vals if field else None,
            how="sum" if field else "count")
        man["points_table"] = join_to_points(table, snapped, name)
        ch.info(f"{len(xs):,} features -> {len(snapped):,} cells, "
                f"column {name!r}. Joined on the LATTICE INDEX, not by "
                "distance, so a feature is either in a cell or it is "
                "not - and cells the layer never touched carry a real "
                "0.0, the same rule the rasters follow.")
        return man

    # -----------------------------------------------------------------
    def _join_shapes(self, src, tr, how, agg, field, klass, name, lat,
                     table, man, ch, join_to_points):
        """Lines and polygons, cut at the cell boundaries.

        Geometries are read through QGIS into plain coordinate lists -
        the `parts` shape friction.feature_cells expects - so nothing
        here needs shapely or geopandas.
        """
        import numpy as np
        import pandas as pd

        from equipop.vectorjoin import VectorJoinError, paths_to_cells

        feats, vals, classes, skipped = [], [], [], 0
        for f in src.getFeatures():
            g = f.geometry()
            if g is None or g.isEmpty():
                continue
            if tr is not None:
                g = _transformed(g, tr)
            shape = _geometry_parts(g)
            if shape is None:
                skipped += 1
                continue
            feats.append(shape)
            if field:
                v = f[field]
                # A NULL is not a zero, and the engine refuses NaN. The
                # convention John set: 0 leaves an additive run
                # unchanged, 1 leaves a multiplicative one unchanged.
                vals.append(1.0 if v is None else float(v))
            else:
                vals.append(1.0)
            if klass:
                c = f[klass]
                classes.append("" if c is None else str(c))
        if not feats:
            raise QgsProcessingException(
                "That layer has no usable line or polygon geometry. "
                "For a point layer choose 'centroid only' in box 2f.")
        if skipped:
            ch.warning(f"{skipped:,} feature(s) had a geometry this "
                       "join cannot use and were left out.")
        if klass and classes:
            # WHICH CLASSES ACTUALLY GOT CHARGED, and what each was
            # worth. A value field that misses a class is silent
            # otherwise: the cells still get a number, just the wrong
            # one, and nothing says which class was left at 1.
            worth = {}
            for c, v in zip(classes, vals):
                worth.setdefault(c, set()).add(round(float(v), 6))
            bits = ", ".join(
                f"{c}={'/'.join(str(x) for x in sorted(w))}"
                for c, w in sorted(worth.items())[:20])
            more = "" if len(worth) <= 20 else f" (+{len(worth) - 20} more)"
            ch.info(f"{len(worth)} class(es) charged: {bits}{more}")
            if not field:
                ch.warning(
                    "No value field, so every class is worth 1 - this "
                    "COUNTS classes rather than weighing them. Prepare "
                    "a numeric field on the layer to give each class "
                    "its own cost.")
            split = [c for c, w in worth.items() if len(w) > 1]
            if split:
                ch.warning(
                    f"{len(split)} class(es) carry MORE THAN ONE value "
                    f"in the value field ({', '.join(sorted(split)[:5])}"
                    + (" ..." if len(split) > 5 else "")
                    + "). Under 'each class once' only the first "
                    "feature of a class in a cell is charged, so which "
                    "value wins depends on the order the features come "
                    "in. Give each class ONE value, or use 'length or "
                    "share'.")

        # INTO LATTICE SPACE, and this is the whole trick.
        # feature_cells cuts on a UNIT GRID ANCHORED AT ZERO, while a
        # raster lattice has an arbitrary origin and a negative e
        # (north-up). Rather than generalise a hundred lines of
        # clipping - and risk it drifting from the barrier path that
        # shares it - the COORDINATES are transformed so the lattice
        # becomes that unit grid: x' = (x - c)/a, y' = (y - f)/e.
        # Cell (i, j) in that space IS (gx, gy), so the join needs no
        # second piece of index arithmetic to get wrong.
        c, f_, a, e = (float(lat["c"]), float(lat["f"]),
                       float(lat["a"]), float(lat["e"]))
        for shape in feats:
            if shape["type"] == "line":
                shape["parts"] = [[((x - c) / a, (y - f_) / e)
                                   for x, y in part]
                                  for part in shape["parts"]]
            else:
                shape["parts"] = [[[((x - c) / a, (y - f_) / e)
                                    for x, y in ring]
                                   for ring in part]
                                  for part in shape["parts"]]

        try:
            charged = paths_to_cells(
                feats, vals, classes=classes or None, unit_size=1.0,
                fidelity=how, agg=agg)
        except VectorJoinError as exc:
            raise QgsProcessingException(str(exc)) from exc

        # A cell is 1x1 in lattice space, so a clipped polygon area IS
        # the SHARE of the cell covered - which is the number wanted -
        # and a clipped line length is in CELL WIDTHS. Converted to
        # metres only when that is meaningful: square pixels in a
        # projected CRS. WorldPop is in degrees, where a "length" is
        # not a distance at all, so it stays in cell widths and the
        # log says which.
        units = ""
        if how == "measure":
            metric = (not QgsCoordinateReferenceSystem(
                lat["crs"]).isGeographic())
            square = abs(abs(a) - abs(e)) < 1e-12
            if metric and square and _is_line_layer(feats):
                charged["value"] = charged["value"] * abs(a)
                units = " (metres)"
            elif _is_line_layer(feats):
                units = " (cell widths - the lattice is not metric)"
            else:
                units = " (share of the cell, 0 to 1)"

        snapped = pd.DataFrame({
            "gx": np.floor(charged["x"]).astype("int64"),
            "gy": np.floor(charged["y"]).astype("int64"),
            name: charged["value"].astype(float)})
        man["points_table"] = join_to_points(table, snapped, name)
        rule = ("every cell each CLASS genuinely touches, once"
                if how == "class" else
                f"how much of each cell the features occupy{units}")
        ch.info(f"{len(feats):,} features -> {len(snapped):,} cells, "
                f"column {name!r}. Charged on {rule}, combined with "
                f"'{agg}'. Joined on the LATTICE INDEX, not by "
                "distance, so cells the layer never touched carry a "
                "real 0.0 - the same rule the rasters follow.")
        return man

    @staticmethod
    def _numbers(text, box):
        """'100 1000' or '100, 1000' -> [100, 1000], or refuse by name."""
        out = []
        for piece in str(text).replace(",", " ").split():
            try:
                out.append(int(float(piece)))
            except ValueError:
                raise QgsProcessingException(
                    f"Box {box}: '{piece}' is not a number. Give one or "
                    "more whole numbers of people, separated by spaces.")
        if not out:
            raise QgsProcessingException(
                f"Box {box}: give at least one neighbourhood size, or "
                "leave it blank for the point table.")
        return out

    def _write(self, table, man, parameters, context, feedback):
        """The results table as points in the working projection."""
        cols = [c for c in table.columns
                if c not in ("EastWest", "NorthSouth", "CellId")]
        fields = QgsFields()
        # QMetaType.Type.Double, not QMetaType.Double. QGIS 3.38 moved
        # field types from QVariant::Type down into QMetaType::Type and
        # base.py:450 already had it right; Claude dropped the '.Type'.
        fields.append(QgsField("CellId", QMetaType.Type.Int))
        # NOT EVERY COLUMN IS A NUMBER. iso3 is text, and this writer
        # cast the lot to float - the third place in the codebase to
        # assume that anything which is not a coordinate is a
        # measurement. Decide per column instead of per position.
        import pandas.api.types as pdt
        text_cols = {c for c in cols
                     if not pdt.is_numeric_dtype(table[c])}
        for c in cols:
            fields.append(QgsField(
                c[:63], QMetaType.Type.QString if c in text_cols
                else QMetaType.Type.Double))

        # WHERE THE LAYER IS DRAWN. The analysis runs in metres, but
        # the output need not: UTM southern zones carry a false
        # northing of 10,000,000 m, so Burundi lands at northing
        # ~9,779,000 and draws off the north of a European basemap -
        # which is exactly what John saw, WITH the project already set
        # to the layer's own EPSG. Writing in the rasters' own CRS puts
        # it where the rasters were, with nothing for the user to redo.
        from equipop.doors.continental import to_output_crs

        work = (man.get("projection") or {}).get("epsg")
        want = self.parameterAsCrs(parameters, "outcrs", context)
        if want is not None and getattr(want, "isValid", lambda: False)():
            code = want.authid()
            out_epsg = (int(code.split(":", 1)[1])
                        if code.upper().startswith("EPSG:") else work)
        else:
            src = str(man.get("crs") or "")
            out_epsg = (int(src.split(":", 1)[1])
                        if src.upper().startswith("EPSG:") else work)
        gx, gy = to_output_crs(table, work, out_epsg)
        crs = QgsCoordinateReferenceSystem(f"EPSG:{out_epsg}")
        # QgsWkbTypes.Point, NOT the number 2. Two numberings live in
        # QgsWkbTypes: GEOMETRY types (Point=0) and WKB types
        # (Point=1). The 2 written here meant POLYGON, and PyQGIS
        # refuses a bare int anyway - "argument 5 has unexpected type
        # 'int'". John hit it after a 10.8 second continental run had
        # already succeeded, on the last line before the layer was
        # written. The simulator used to accept anything; it does not
        # now.
        sink, dest = self.parameterAsSink(
            parameters, "OUTPUT", context, fields,
            QgsWkbTypes.Point, crs)
        if sink is None:
            raise QgsProcessingException(
                "Nowhere to write the results to.")

        e = list(gx)
        n = list(gy)
        ids = (table["CellId"].tolist() if "CellId" in table.columns
               else list(range(len(table))))
        block = [table[c].tolist() for c in cols]
        for i in range(len(table)):
            if feedback.isCanceled():
                break
            f = QgsFeature(fields)
            f.setGeometry(QgsGeometry.fromPointXY(
                QgsPointXY(float(e[i]), float(n[i]))))
            f.setAttributes(
                [int(ids[i])]
                + [(str(col[i]) if c in text_cols else float(col[i]))
                   for c, col in zip(cols, block)])
            sink.addFeature(f)
        return dest


def _transformed(geom, tr):
    """A copy of the geometry in the lattice's CRS."""
    g = QgsGeometry(geom)
    g.transform(tr)
    return g


def _geometry_parts(g):
    """A QGIS geometry as friction.feature_cells' `parts` shape.

    Lines  -> {"type": "line",    "parts": [[(x, y), ...], ...]}
    Areas  -> {"type": "polygon", "parts": [[ring, hole, ...], ...]}
    Points -> None (they belong on the centroid path).
    """
    from qgis.core import QgsWkbTypes as W

    t = W.geometryType(g.wkbType())
    if t == W.LineGeometry:
        parts = (g.asMultiPolyline() if g.isMultipart()
                 else [g.asPolyline()])
        parts = [[(p.x(), p.y()) for p in part]
                 for part in parts if part and len(part) >= 2]
        return {"type": "line", "parts": parts} if parts else None
    if t == W.PolygonGeometry:
        parts = (g.asMultiPolygon() if g.isMultipart()
                 else [g.asPolygon()])
        out = []
        for part in parts:
            rings = [[(p.x(), p.y()) for p in ring]
                     for ring in part if ring and len(ring) >= 3]
            if rings:
                out.append(rings)
        return {"type": "polygon", "parts": out} if out else None
    return None


def _is_line_layer(feats):
    return bool(feats) and feats[0]["type"] == "line"


def _report_inventory(src, klass, ch):
    """Say what machine 6 knows about this layer, if anything.

    BACKLOG 269/298. The inventory records the distinct values of
    exactly the columns a join groups on, and writing it is the whole
    reason machine 6 exists. Reading it here is what makes the two
    machines one workflow rather than two tools that happen to share
    a folder.
    """
    import os

    try:
        path = src.sourceName() if hasattr(src, "sourceName") else ""
    except Exception:                                # pragma: no cover
        path = ""
    folder = os.path.dirname(str(path)) if path else ""
    if not folder or not os.path.isdir(folder):
        return
    try:
        from equipop.doors.inventory import read_inventory
        got = read_inventory(folder)
    except Exception:                                # pragma: no cover
        return
    if not got:
        return
    base = os.path.basename(str(path))
    for rec in got.get("files", []):
        if os.path.basename(rec.get("file", "")) != base:
            continue
        classes = rec.get("classes") or {}
        if not classes:
            return
        if klass and klass in classes:
            info = classes[klass] or {}
            vals = info.get("values")
            n = info.get("distinct")
            shown = (", ".join(map(str, vals[:15]))
                     + (" ..." if vals and len(vals) > 15 else "")
                     ) if vals else info.get("note", "")
            ch.info(f"[inventory] {klass} has {n} distinct value(s) "
                    f"here: {shown}")
        else:
            ch.info("[inventory] this layer has class column(s): "
                    + ", ".join(classes))
        return
