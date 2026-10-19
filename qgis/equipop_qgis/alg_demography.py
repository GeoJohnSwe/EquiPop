# -*- coding: utf-8 -*-
"""
alg_demography.py - MACHINE 4's QGIS door: spatial demography.

John's ruling that this is its OWN machine: machine 3 turns rasters
into points, machine 4 asks a demographic question of them. Keeping
them apart keeps machine 3 honest - it does one thing at continental
scale - and gives the demography somewhere to grow.

THIN, like machine 3's door. Every decision about what an index means
lives in equipop.doors.demography, which any door can call. What is
QGIS's own here: turning tick-boxes into a list of index names, and
turning the result table into a layer.

SEVERAL INDICES IN ONE PASS (John's preference). At continental scale
the cost is loading the rasters, projecting the points and building
the tree - identical whichever index you want. Four indices one at a
time is four of those.
"""
from qgis.core import (QgsCoordinateReferenceSystem, QgsFeature, QgsField,
                       QgsFields, QgsGeometry, QgsPointXY,
                       QgsProcessing, QgsProcessingException,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterMatrix,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString, QgsWkbTypes)
from qgis.PyQt.QtCore import QMetaType

from .base import EquipopAlgorithm


# THE TICK-BOX LIST IS WRITTEN DOWN HERE, NOT READ FROM THE PACKAGE.
# initAlgorithm() runs while QGIS is building the dialog, and a plugin
# must still LOAD when equipop is absent or a release behind - that is
# the whole point of test_the_plugin_still_loads_when_the_package_is_
# missing, which this door broke. Reading INDICES there turned a
# missing package from a sentence into a traceback at startup.
# tests/test_qgis_continental.py pins this list against the package's
# own, so the two cannot drift.
INDEX_NAMES = ["ageing_index", "child_woman_ratio", "dependency_ratio",
               "sex_ratio"]
INDEX_LABELS = ["Ageing index", "Child-woman ratio",
                "Dependency ratio", "Sex ratio"]

# THE TABLE OPENS SHOWING THE TRUTH (John: "the design choices are
# hard - should be based on factual values, not user entered"). One
# row per index, pre-filled with that index's OWN ages, so nothing has
# to be typed or remembered: you edit a value that is already correct.
# Written down rather than read from the package, for the same reason
# as INDEX_NAMES - initAlgorithm runs while QGIS builds the dialog and
# the plugin must load without equipop. A test pins every cell against
# the package's own definitions.
INDEX_ROWS = [
    "Ageing index",      "65-",      "0-14",
    "Child-woman ratio", "0-4",      "f:15-49",
    "Dependency ratio",  "0-14,65-", "15-64",
    "Sex ratio",         "m:",       "f:",
]


# v1.60.0, BACKLOG 416. RATES AND LIFE EXPECTANCY, read from each
# neighbourhood's age pyramid against its nation's (doors/vital.py).
# Written down for the same reason as INDEX_NAMES, and pinned against
# vital.MEASURES by tests/test_vital_doors.py. The three marked
# UNRELIABLE are computed on John's request and say so here, in the
# log and in the field descriptions.
RATE_NAMES = ["life_expectancy_60", "life_expectancy_50",
              "life_expectancy_30", "life_expectancy_0",
              "total_fertility_rate", "crude_birth_rate",
              "crude_death_rate"]
RATE_LABELS = ["Life expectancy at 60",
               "Life expectancy at 50 (UNRELIABLE)",
               "Life expectancy at 30 (UNRELIABLE)",
               "Life expectancy at birth (UNRELIABLE)",
               "Total fertility rate", "Crude birth rate",
               "Crude death rate"]
RATE_SEXES = ["both", "women", "men"]
RATE_SEX_LABELS = ["Both sexes", "Women", "Men"]
# v1.61.0, John: whose nation a neighbourhood's people are read
# against. The engine's VITAL_REFERENCES, in this order - a test pins it.
RATE_REFS = ["own", "cell"]
RATE_REF_LABELS = ["Each person's own country (pools across a border)",
                   "The country of the neighbourhood's cell"]


def _index_names():
    """Sorted so the tick-box order is stable between QGIS sessions."""
    return list(INDEX_NAMES)


class SpatialDemography(EquipopAlgorithm):
    # BACKLOG 378. k is this door's only neighbourhood box,
    # so there is no either-or to check - but a k that will
    # not parse still has to be refused before Run.
    R_BOX = "-none-"
    K_IS_REQUIRED = True

    """Demographic indices over k-neighbourhoods, from a raster folder."""

    EQP_TOOL = "SpatialDemography"

    def name(self):
        return "spatialdemography"

    # WRITTEN DOWN, NOT IMPORTED. displayName runs while QGIS
    # builds the toolbox, so importing the package here would
    # kill the whole plugin when equipop is missing - BACKLOG
    # 218, reintroduced and caught the same day. A test pins
    # this against doors/help.LABELS so it cannot drift.
    EQP_LABEL = "4. Spatial Demographic Analysis"

    def displayName(self):
        return self.EQP_LABEL

    def initAlgorithm(self, config=None):
        names = _index_names()
        self._names = names
        self.add(QgsProcessingParameterFile(
            "folder", "1a. Folder of population rasters (.tif)",
            behavior=QgsProcessingParameterFile.Folder, optional=True))
        # v1.60.1, John: "machine 4 only takes rasters - we should make
        # it possible to use the curated raster-to-point files as
        # well". The points machine 3 made ARE the folder, read once.
        self.add(QgsProcessingParameterFeatureSource(
            "points", "1a. ...or the point layer machine 3 made from "
                      "such a folder (instead of the folder)",
            [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVector],
            optional=True))
        self.add(QgsProcessingParameterEnum(
            "indices", "1b. Which indices (tick several - they cost "
                       "one pass, not one each)",
            options=list(INDEX_LABELS),
            allowMultiple=True, defaultValue=[0], optional=True))
        self.add(QgsProcessingParameterString(
            "k", "1c. Neighbourhood sizes, in PEOPLE (e.g. 1000)",
            defaultValue="1000"))
        self.add(QgsProcessingParameterNumber(
            "unit", "1d. Analysis cell size, in metres",
            type=QgsProcessingParameterNumber.Double,
            defaultValue=1000.0, minValue=0.000001))
        self.add(QgsProcessingParameterEnum(
            "rates", "1e. Rates and life expectancy - MODEL-BASED, read "
                     "from the age pyramid against the nation's (tick "
                     "several)",
            options=list(RATE_LABELS), allowMultiple=True,
            defaultValue=[], optional=True))
        self.add(QgsProcessingParameterString(
            "year", "2a. Which year (blank = the only one present)",
            optional=True), advanced=True)
        self.add(QgsProcessingParameterCrs(
            "crs", "2b. Projection to work in (blank = suggested)",
            optional=True), advanced=True)
        # EDIT EACH MEASURE SEPARATELY (John). The earlier boxes
        # applied to ONE index and refused if several were ticked -
        # which defeated the whole point, because "restricting to women
        # in fertile ages will not fly in the other measures". A TABLE
        # gives every index its own row, so four can run in one
        # traverse with four different age settings. His own
        # suggestion, and the right one: QGIS has the widget already.
        # Blank rows, and indices absent from the table, keep the
        # measure's own definition.
        self.add(QgsProcessingParameterMatrix(
            "settings",
            "2c. Change a measure - one row per index you want to "
            "alter. Ages as '0-4', '65-', or 'f:15-49'. Leave a cell "
            "empty to keep that half as it is.",
            headers=["Index", "Numerator ages", "Denominator ages"],
            defaultValue=list(INDEX_ROWS),
            numberRows=len(INDEX_NAMES), hasFixedNumberRows=True,
            optional=True), advanced=True)
        self.add(QgsProcessingParameterEnum(
            "ratesex", "2d. Life tables and death rate for",
            options=list(RATE_SEX_LABELS), defaultValue=0),
            advanced=True)
        self.add(QgsProcessingParameterEnum(
            "rateref", "2e. Read the rates against",
            options=list(RATE_REF_LABELS), defaultValue=0),
            advanced=True)
        # v1.61.0, John: "please add also an opportunity to split a run
        # into tiles for Q and Pro" - merged regions are coming.
        self.add(QgsProcessingParameterFolderDestination(
            "tiles", "2f. Folder for a TILED, resumable run "
                     "(blank = run in memory)",
            optional=True), advanced=True)
        self.add(QgsProcessingParameterCrs(
            "outcrs", "2g. Write the output in (blank = the same "
                      "projection the rasters were in)",
            optional=True), advanced=True)
        self.add(QgsProcessingParameterFeatureSink(
            "OUTPUT", "Demographic indices"))

    # -----------------------------------------------------------------
    def processAlgorithm(self, parameters, context, feedback):
        from equipop.doors.continental import ContinentalError
        from equipop.doors.demography import DemographyError, run_indices

        from .base import check_versions

        ch = self.channel(feedback)
        check_versions(ch)

        names = _index_names()
        picked = [names[i] for i in
                  self.parameterAsEnums(parameters, "indices", context)]
        rates = [RATE_NAMES[i] for i in
                 self.parameterAsEnums(parameters, "rates", context)]
        if not picked and not rates:
            raise QgsProcessingException(
                "Boxes 1b and 1e: tick at least one index or rate.")
        sex = RATE_SEXES[self.parameterAsEnum(parameters, "ratesex",
                                              context)]
        rule = RATE_REFS[self.parameterAsEnum(parameters, "rateref",
                                              context)]
        # an optional FolderDestination left alone arrives as the
        # literal TEMPORARY_OUTPUT (machine 3 learnt this first)
        tiles = (self.parameterAsString(parameters, "tiles",
                                        context) or "").strip()
        if tiles in ("", "TEMPORARY_OUTPUT"):
            tiles = None

        folder = (self.parameterAsFile(parameters, "folder", context)
                  or "").strip()
        source = self.parameterAsSource(parameters, "points", context)
        if bool(folder) == (source is not None):
            raise QgsProcessingException(
                "Box 1a: give EITHER the folder of rasters OR the point "
                "layer machine 3 made from one"
                + (" - not both." if folder else "."))
        points = points_crs = None
        if source is not None:
            points, points_crs = _points_table(source)
            folder = None
        ks = self._numbers(self.parameterAsString(parameters, "k",
                                                  context), "1c")
        unit = self.parameterAsDouble(parameters, "unit", context)
        year = (self.parameterAsString(parameters, "year",
                                       context) or "").strip() or None

        # Editing the columns only makes sense for ONE index - with
        # several ticked there is no way to say which they belong to.
        over = self._settings(parameters, context, picked, ch)

        epsg = None
        crs = self.parameterAsCrs(parameters, "crs", context)
        if crs is not None and crs.isValid():
            if crs.isGeographic():
                raise QgsProcessingException(
                    "That projection is in degrees. Neighbourhood work "
                    "needs metres - leave the box blank and one will "
                    "be suggested from the data.")
            code = crs.authid()
            if code.upper().startswith("EPSG:"):
                epsg = int(code.split(":", 1)[1])

        try:
            man = run_indices(folder, picked, k_values=ks,
                              unit_size=unit, year=year, epsg=epsg,
                              overrides=over or None, channel=ch,
                              vital=rates, vital_sex=sex,
                              vital_reference=rule, out_dir=tiles,
                              points=points, points_crs=points_crs)
        except (DemographyError, ContinentalError, ValueError) as exc:
            # The engine refuses in plain words. Do not add to them.
            raise QgsProcessingException(str(exc))

        if tiles:
            from equipop.bigrun import load_tiled
            table = load_tiled(tiles)
        else:
            table = man["results"]
        return {"OUTPUT": self._write(table, man, parameters,
                                      context, feedback)}

    # -----------------------------------------------------------------
    def _settings(self, parameters, context, picked, ch=None):
        """The per-index table -> {index: {"numerator_ages": ...}}.

        Rows come back flat, three cells at a time, because that is
        how QgsProcessingParameterMatrix hands them over.
        """
        from equipop.doors.demography import INDICES, parse_spec

        # AN UNTOUCHED CELL IS PyQGIS's NULL and str(NULL) is the
        # four characters 'NULL'. The SAME fault as machine 5's
        # settings table (BACKLOG 265), found here only when the
        # simulator stopped being kinder than QGIS - which means this
        # tool would have refused an untouched box 2c on John's
        # machine too, and nobody had tried it yet.
        from .base import matrix_cells
        flat = matrix_cells(self, parameters,
                            "settings", context)
        if not flat:
            return {}
        if len(flat) % 3:
            raise QgsProcessingException(
                f"Box 2c has {len(flat)} cells, which is not a whole "
                "number of rows of three (index, numerator ages, "
                "denominator ages).")

        by_label = {v["label"].lower(): k for k, v in INDICES.items()}
        by_label.update({k.lower(): k for k in INDICES})
        out = {}
        for i in range(0, len(flat), 3):
            name, nages, dages = flat[i:i + 3]
            if not name and not nages and not dages:
                continue
            key = by_label.get(name.lower())
            if key is None:
                raise QgsProcessingException(
                    f"Box 2c names an index I do not have: {name!r}. "
                    "Use one of: "
                    + "; ".join(INDICES[k]["label"] for k in
                                sorted(INDICES)))
            if key not in picked:
                # The table now opens PRE-FILLED with every index, so
                # rows for unticked ones are normal and must not be an
                # error. Say so only if the row was actually edited.
                default = dict(zip(INDEX_NAMES,
                                   [INDEX_ROWS[i:i + 3]
                                    for i in range(0, len(INDEX_ROWS), 3)]
                                   ))[key][1:]
                if [nages, dages] != list(default) and ch:
                    ch.warning(
                        f"Box 2c changes {INDICES[key]['label']}, which "
                        "is not ticked in box 1b - the row was ignored.")
                continue
            row = {}
            for cell, half in ((nages, "numerator_ages"),
                               (dages, "denominator_ages")):
                if cell:
                    try:
                        parse_spec(cell)       # refuse here, by name
                    except Exception as exc:
                        raise QgsProcessingException(
                            f"Box 2c, {INDICES[key]['label']}: "
                            f"{exc}")
                    row[half] = cell
            if row:
                out[key] = row
        return out

    def _columns(self, parameters, box, context):
        """A comma-separated list of column names, or nothing.

        Read through parameterAsString like every other text box in
        this toolbox - an earlier version reached into `parameters`
        directly and carried a pointless import with it, which the
        simulator refused and which would have been dead weight in
        QGIS too.
        """
        raw = self.parameterAsString(parameters, box, context) or ""
        return [c.strip() for c in raw.replace(";", ",").split(",")
                if c.strip()]

    @staticmethod
    def _numbers(text, box):
        """k values from a box, through the ONE reader.

        BACKLOG 377, v1.53.2. This was a fifth open-coded k parser -
        `int(float(piece))`, duplicated verbatim in alg_continental
        and alg_demography - and it silently truncated: '1.000'
        became ONE PERSON and `.replace(",", " ")` turned '1,000'
        into the two values 1 and 0. equipop.doors.numbers exists so
        that cannot happen, and its own docstring says so.
        """
        from equipop.doors.numbers import intlist, BadNumber
        try:
            out = intlist(text)
        except BadNumber as bad:
            raise QgsProcessingException(f"Box {box}: {bad}")
        if not out:
            raise QgsProcessingException(
                f"Box {box}: give at least one neighbourhood size.")
        return out

    def _write(self, table, man, parameters, context, feedback):
        import pandas.api.types as pdt

        cols = [c for c in table.columns
                if c not in ("EastWest", "NorthSouth", "CellId")]
        text_cols = {c for c in cols if not pdt.is_numeric_dtype(table[c])}
        fields = QgsFields()
        fields.append(QgsField("CellId", QMetaType.Type.Int))
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
        # QgsWkbTypes.Point - see the note in alg_continental.py.
        sink, dest = self.parameterAsSink(parameters, "OUTPUT", context,
                                          fields, QgsWkbTypes.Point, crs)
        if sink is None:
            raise QgsProcessingException("Nowhere to write the results to.")

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


def _points_table(source):
    """The point layer machine 3 wrote, as a table for the engine.

    Coordinates from the geometry, IN THE LAYER'S OWN CRS - the engine
    projects them exactly as it projects a folder's pixels, so the two
    routes give the same answer. A layer without geometry (a CSV of
    machine 3's table) is read through its EastWest/NorthSouth fields.
    Only iso3 and the cohort fields go on; the engine says what it
    left out.
    """
    import re

    import numpy as np
    import pandas as pd
    names = list(source.fields().names())
    keep = [n for n in names
            if n in ("iso3", "cohort", "population", "EastWest",
                     "NorthSouth")
            or re.match(r"^[fmt]_\d+_\d{4}$", n)]
    where = {n: names.index(n) for n in keep}
    cols = {n: [] for n in keep}
    xs, ys, any_geom = [], [], False
    for f in source.getFeatures():
        attrs = f.attributes()
        for n, i in where.items():
            cols[n].append(_plain(attrs[i]))
        g = f.geometry() if f.hasGeometry() else None
        if g is not None and not g.isEmpty():
            # A layer saved through another format can come back as
            # MultiPoint, which asPoint() refuses even with one part;
            # the centroid of one point is that point.
            p = (g.centroid() if g.isMultipart() else g).asPoint()
            xs.append(p.x())
            ys.append(p.y())
            any_geom = True
        else:
            xs.append(np.nan)
            ys.append(np.nan)
    table = pd.DataFrame(cols)
    if any_geom:
        table["EastWest"], table["NorthSouth"] = xs, ys
    # not read, but named in the log by the engine (review of 1.60.1)
    table.attrs["fields_not_used"] = [n for n in names if n not in keep]
    crs = source.sourceCrs()
    code = crs.authid() if crs is not None and crs.isValid() else ""
    if crs is not None and crs.isValid() and (
            not code or code.upper().startswith("USER:")):
        # a custom projection has no code the engine can look up;
        # its definition travels instead
        code = getattr(crs, "toWkt", lambda: "")() or code
    return table, (code or None)


def _plain(v):
    """A QGIS attribute as plain Python: NULL becomes None."""
    try:
        if v is None or (hasattr(v, "isNull") and v.isNull()):
            return None
    except Exception:                                 # pragma: no cover
        pass
    return v
