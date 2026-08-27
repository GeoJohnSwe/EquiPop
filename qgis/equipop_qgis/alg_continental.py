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
        self.add(QgsProcessingParameterFeatureSource(
            "joinlayer", "2e. A point layer to put on the same grid "
                         "(shops, clinics, stops...)",
            types=[0], optional=True), advanced=True)
        self.add(QgsProcessingParameterField(
            "joinfield", "2f. Which field to add up (blank = count "
                         "the points)",
            parentLayerParameterName="joinlayer", optional=True),
            advanced=True)
        self.add(QgsProcessingParameterString(
            "joinname", "2g. Name for the new column",
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
            man.setdefault("projection", {})["epsg"] = 4326
        elif tiles:
            from equipop.bigrun import load_tiled
            table = load_tiled(tiles)
        else:
            table = man["results"]

        return {"OUTPUT": self._write(table, man, parameters, context,
                                      feedback)}

    # -----------------------------------------------------------------
    def _join(self, parameters, context, man, ch):
        """Snap an optional point layer onto the raster lattice."""
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

        field = (self.parameterAsString(parameters, "joinfield",
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
                "That layer has no usable point geometry.")

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
