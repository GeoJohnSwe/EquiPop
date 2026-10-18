# -*- coding: utf-8 -*-
"""
alg_catalogue.py - MACHINE 5's new QGIS door: LOOK, SELECT, FETCH.

BACKLOG 414, v1.58.0. Tool 5 asked for a table of settings in each
provider's own words, and John spent a session learning what to type.
This replaces typing with SELECTING, using the one tool every QGIS
user already has for choosing rows - the attribute table:

  5a / 5b  list what exists, as a table with one row per downloadable
           thing (a GeoTIFF, a shapefile layer, a layer of a .pbf) and
           the same columns for both providers. Nothing is downloaded.
  (you)    open the table and select the rows you want - by hand, or
           with Select by Expression, e.g. "sex" = 'f' AND "year" = 2020
  5c       fetch the selected rows into a folder, with the manifest and
           a recipe (the rows, as a CSV you can fetch again).

THIN, like every door: what a catalogue row means lives in
equipop/doors/catalogue.py and fetchrows.py. What is QGIS's own here
is the boxes, the table, and the "Selected features only" tick that
QGIS puts on every feature-source box by itself.

Labels and option lists are WRITTEN DOWN, not imported: QGIS builds
the toolbox before any tool runs, and an `import equipop` there kills
the whole plugin when the package is absent (BACKLOG 218). Tests pin
each list against the package's own.
"""
from qgis.core import (QgsFeature, QgsField, QgsFields, QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString, QgsWkbTypes)
from qgis.PyQt.QtCore import QMetaType

from .base import EquipopAlgorithm

#: catalogue.COLUMNS, as QGIS field types. A test pins the two.
COLUMNS = [
    ("provider", "str"), ("theme", "str"), ("series", "str"),
    ("place", "str"), ("place_code", "str"), ("year", "int"),
    ("date", "str"), ("layer", "str"), ("sex", "str"),
    ("age_from", "int"), ("age_to", "int"), ("resolution", "str"),
    ("format", "str"), ("crs", "str"), ("size_mb", "float"),
    ("size_is", "str"), ("file", "str"), ("url", "str"),
    ("inside", "str"), ("md5_url", "str"), ("licence", "str"),
    ("citation", "str"), ("doi", "str"), ("source_page", "str"),
    ("record_id", "str"), ("note", "str"),
]
_QT = {"str": QMetaType.Type.QString, "int": QMetaType.Type.Int,
       "float": QMetaType.Type.Double}

#: catalogue.WP_THEMES keys, in dropdown order.
WP_THEMES = ["age_sex", "population"]
WP_THEME_LABELS = [
    "Age and sex - one file per sex and age band (0, 1-4, 5-9 ... 90+): "
    "40 per country and year",
    "Total population only - ONE file per country and year, not split "
    "by age or sex",
]
WP_RESOLUTIONS = ["1km", "100m"]
WP_RESOLUTION_LABELS = [
    "1 km - small: Sweden is about 2 MB a file",
    "100 m - large: Sweden is about 47 MB a file",
]

#: catalogue.GF_THEMES keys, in dropdown order.
OSM_THEMES = ["buildings", "roads", "railways", "pois", "places",
              "landuse", "water", "natural", "transport", "traffic",
              "worship", "protected", "admin"]
OSM_THEME_LABELS = [
    "buildings", "roads", "railways",
    "pois - shops, schools, services (points and areas)",
    "places - towns, villages, suburbs", "landuse", "water and waterways",
    "natural", "transport - stops and stations", "traffic",
    "worship - places of worship", "protected areas",
    "admin - administrative areas",
]


class _Catalogue(EquipopAlgorithm):
    """What 5a and 5b share: the table they write."""

    def _write_table(self, parameters, context, rows, ch):
        fields = QgsFields()
        for nm, kind in COLUMNS:
            fields.append(QgsField(nm, _QT[kind]))
        sink, dest = self.parameterAsSink(
            parameters, "CATALOGUE", context, fields,
            QgsWkbTypes.NoGeometry)
        if sink is None:
            raise QgsProcessingException(
                "No output was created - choose where the catalogue "
                "table goes (a temporary layer is the easiest).")
        written = 0
        for r in rows:
            f = QgsFeature(fields)
            f.setAttributes([r.get(nm) for nm, _ in COLUMNS])
            if sink.addFeature(f) is not False:
                written += 1
        if written != len(rows):
            raise QgsProcessingException(
                f"The output kept only {written} of {len(rows)} rows. "
                "Leave it as a temporary layer, or save as GeoPackage.")
        ch.info("NEXT: open this table (right-click > Open Attribute "
                "Table), select the rows you want - by hand, or with "
                "Select by Expression - and run 5c with 'Selected "
                "features only' ticked.")
        return {"CATALOGUE": dest}


class WorldPopCatalogue(_Catalogue):
    """5a. What WorldPop has, one row per GeoTIFF."""

    EQP_TOOL = "WorldPopCatalogue"
    EQP_LABEL = "5a. WorldPop - what is there? (lists, downloads nothing)"

    def name(self):
        return "worldpopcatalogue"

    def displayName(self):
        return self.EQP_LABEL

    def initAlgorithm(self, config=None):
        self.add(QgsProcessingParameterEnum(
            "wp_theme", "1a. What", options=list(WP_THEME_LABELS),
            defaultValue=0))
        self.add(QgsProcessingParameterString(
            "wp_places", "1b. Countries - names or three-letter codes, "
                         "separated by commas (Sweden, KEN, Burundi)"))
        self.add(QgsProcessingParameterString(
            "wp_years", "1c. Years - such as 2015, 2020 or 2010-2020. "
                        "Empty: every year there is", optional=True))
        self.add(QgsProcessingParameterEnum(
            "wp_resolution", "1d. Resolution",
            options=list(WP_RESOLUTION_LABELS), defaultValue=0))
        # v1.58.2 (John, 16 Oct): OUT OF ADVANCED. Reading the dropdown,
        # "Population" looked like the age-sex files plus totals. It is
        # not - it is one file of everyone - and the totals that DO sit
        # beside the bands were hidden under Advanced, where nobody
        # looking for them would see them.
        self.add(QgsProcessingParameterBoolean(
            "wp_totals", "1e. Age and sex: also list the totals - both "
                         "sexes per band (t_), and all ages per sex "
                         "(T_F, T_M; 100 m only)", defaultValue=False))
        self.add(QgsProcessingParameterBoolean(
            "wp_exact", "2a. Measure every file's size (one request "
                        "each; otherwise one per country and year)",
            defaultValue=False), advanced=True)
        self.add(QgsProcessingParameterFeatureSink(
            "CATALOGUE", "WorldPop catalogue", type=QgsProcessing.TypeVector))

    def processAlgorithm(self, parameters, context, feedback):
        from .base import check_versions
        ch = self.channel(feedback)
        check_versions(ch)            # before importing 1.58's modules
        from equipop.doors.catalogue import browse_worldpop
        from equipop.doors.fetching import FetchError
        places = self.parameterAsString(parameters, "wp_places",
                                        context).strip()
        if not places:
            raise QgsProcessingException(
                "Box 1b: name at least one country - Sweden, or SWE.")
        try:
            rows = browse_worldpop(
                WP_THEMES[self.parameterAsEnum(parameters, "wp_theme",
                                               context)],
                places,
                self.parameterAsString(parameters, "wp_years", context),
                WP_RESOLUTIONS[self.parameterAsEnum(
                    parameters, "wp_resolution", context)],
                include_totals=self.parameterAsBool(parameters,
                                                    "wp_totals", context),
                exact_sizes=self.parameterAsBool(parameters, "wp_exact",
                                                 context),
                say=ch.info)
        except FetchError as e:
            raise QgsProcessingException(str(e))
        return self._write_table(parameters, context, rows, ch)


class OsmCatalogue(_Catalogue):
    """5b. What Geofabrik has, one row per layer."""

    EQP_TOOL = "OsmCatalogue"
    EQP_LABEL = ("5b. OpenStreetMap (Geofabrik) - what is there? "
                 "(lists, downloads nothing)")

    def name(self):
        return "osmcatalogue"

    def displayName(self):
        return self.EQP_LABEL

    def initAlgorithm(self, config=None):
        self.add(QgsProcessingParameterString(
            "osm_places", "1a. Regions - names, two-letter codes or "
                          "Geofabrik ids, separated by commas (Sweden, "
                          "KE, bayern)"))
        self.add(QgsProcessingParameterEnum(
            "osm_layers", "1b. Layers", options=list(OSM_THEME_LABELS),
            allowMultiple=True, defaultValue=[0]))
        self.add(QgsProcessingParameterString(
            "osm_years", "1c. Past years, as 1 January extracts - such as "
                         "2018, 2022. Empty: today's extract only",
            optional=True))
        self.add(QgsProcessingParameterBoolean(
            "osm_latest", "1d. With years: also list today's extract",
            defaultValue=True))
        self.add(QgsProcessingParameterFeatureSink(
            "CATALOGUE", "OpenStreetMap catalogue",
            type=QgsProcessing.TypeVector))

    def processAlgorithm(self, parameters, context, feedback):
        from .base import check_versions
        ch = self.channel(feedback)
        check_versions(ch)            # before importing 1.58's modules
        from equipop.doors.catalogue import browse_geofabrik
        from equipop.doors.fetching import FetchError
        places = self.parameterAsString(parameters, "osm_places",
                                        context).strip()
        if not places:
            raise QgsProcessingException(
                "Box 1a: name at least one region - Sweden, KE, bayern.")
        picked = self.parameterAsEnums(parameters, "osm_layers", context)
        if not picked:
            raise QgsProcessingException("Box 1b: tick at least one layer.")
        try:
            rows = browse_geofabrik(
                places, [OSM_THEMES[i] for i in picked],
                self.parameterAsString(parameters, "osm_years", context),
                latest=self.parameterAsBool(parameters, "osm_latest",
                                            context),
                say=ch.info)
        except FetchError as e:
            raise QgsProcessingException(str(e))
        return self._write_table(parameters, context, rows, ch)


class FetchSelected(EquipopAlgorithm):
    """5c. Download the selected catalogue rows into a folder."""

    EQP_TOOL = "FetchSelected"
    EQP_LABEL = "5c. Fetch the rows you selected (downloads into a folder)"

    def name(self):
        return "fetchselected"

    def displayName(self):
        return self.EQP_LABEL

    def initAlgorithm(self, config=None):
        self.add(QgsProcessingParameterFeatureSource(
            "rows", "1. The catalogue table from 5a or 5b (or a saved "
                    "equipop_recipe.csv) - tick 'Selected features only'",
            [QgsProcessing.TypeVector]))
        self.add(QgsProcessingParameterNumber(
            "max_mb", "2. Size limit in MB - stop if the selection, or "
                      "what arrives, is larger (0: no limit)",
            type=QgsProcessingParameterNumber.Double, defaultValue=5000,
            minValue=0))
        self.add(QgsProcessingParameterBoolean(
            "keep_pbf", "3. Keep the OpenStreetMap .pbf after its layers "
                        "are written out", defaultValue=True),
                 advanced=True)
        self.add(QgsProcessingParameterFolderDestination(
            "FOLDER", "Folder to fetch into"))

    def processAlgorithm(self, parameters, context, feedback):
        from .base import check_versions
        ch = self.channel(feedback)
        check_versions(ch)            # before importing 1.58's modules
        from equipop.doors.fetching import FetchError
        from equipop.doors.fetchrows import fetch_rows
        source = self.parameterAsSource(parameters, "rows", context)
        if source is None:
            raise QgsProcessingException("Box 1: choose the catalogue "
                                         "table.")
        names = list(source.fields().names())
        gone = [c for c in ("provider", "url", "file") if c not in names]
        if gone:
            raise QgsProcessingException(
                f"This table has no {', '.join(gone)} column, so it is not "
                "a catalogue. Make one with 5a or 5b, or load an "
                "equipop_recipe.csv.")
        rows = [dict(zip(names, (_plain(v) for v in f.attributes())))
                for f in source.getFeatures()]
        folder = self.parameterAsString(parameters, "FOLDER", context)
        if not folder.strip():
            raise QgsProcessingException("Choose a folder to fetch into.")
        if _qgis_temporary(folder):
            # QGIS's default for a folder box is a temporary folder it
            # deletes when it closes: gigabytes fetched there are gone
            # by tomorrow, with the manifest that said what they were.
            raise QgsProcessingException(
                f"The folder box points at {folder}, a TEMPORARY folder "
                "that QGIS deletes when it closes. Choose a folder of "
                "your own. Nothing was downloaded.")
        max_mb = self.parameterAsDouble(parameters, "max_mb", context)

        def say(line):
            # CANCEL BETWEEN STEPS (a .pbf being written out, say);
            # inside a download it is `cancelled` below, asked after
            # every 1 MiB (v1.59.2). run_fetch records what has arrived
            # before it re-raises, so a cancelled job leaves a manifest
            # that a later run recognises rather than refuses.
            if feedback.isCanceled():
                raise QgsProcessingException(
                    "Cancelled. What had arrived is recorded in "
                    "equipop_fetch.json, so running again continues.")
            ch.info(line)
        try:
            fetch_rows(rows, folder, say=say, max_mb=max_mb or None,
                       keep_pbf=self.parameterAsBool(parameters, "keep_pbf",
                                                     context),
                       cancelled=feedback.isCanceled)
        except FetchError as e:
            raise QgsProcessingException(str(e))
        return {"FOLDER": folder}


def _qgis_temporary(folder):
    """Is this QGIS's own temporary output folder (processing_*)?"""
    import os
    import tempfile
    p = os.path.abspath(folder)
    tmp = os.path.abspath(tempfile.gettempdir())
    return (p.startswith(tmp + os.sep)
            and any(part.startswith("processing_")
                    for part in p[len(tmp) + 1:].split(os.sep)))


def _plain(v):
    """A QGIS attribute as plain Python: NULL becomes None."""
    try:
        if v is None or (hasattr(v, "isNull") and v.isNull()):
            return None
    except Exception:                                 # pragma: no cover
        pass
    return v
