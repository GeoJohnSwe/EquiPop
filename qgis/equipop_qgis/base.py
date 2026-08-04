# -*- coding: utf-8 -*-
"""
base.py - what both QGIS algorithms share.

Almost nothing here is new. The help text, the reporting, the result
column names and the coordinate rules all come from equipop.doors,
which the ArcGIS door already uses - that is what the shared core was
built for in 1.18.0. What is genuinely QGIS's own is reading features
from a QgsFeatureSource and writing them to a QgsFeatureSink, and
that is all this file really adds.

Parameter names deliberately MATCH the ArcGIS toolbox: `layer`, `k`,
`pop`, `treat`, `unit` and so on. The shared help is keyed by
parameter name, so identical names mean both doors explain
themselves with identical words - which is the point for teaching,
where a QGIS student and a Pro student should recognise each other's
screens.
"""
from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsFeature, QgsField,
                       QgsFields, QgsProcessingAlgorithm,
                       QgsProcessingException, QgsProject)
from qgis.PyQt.QtCore import QVariant

import numpy as np

CONTRACT = 1


def _doors():
    """The shared core, or a refusal that names the fix. QGIS reaches
    the package through its own Python (the OSGeo4W shell), which is
    a different environment from the one most users install into, so
    this failure is worth explaining properly."""
    try:
        import equipop.doors as D
    except Exception:
        try:
            import equipop
            found = getattr(equipop, "__version__", "unknown")
        except Exception:
            raise QgsProcessingException(
                "The EquiPop Python package is not installed in the "
                "Python that QGIS uses. Open the OSGeo4W Shell (or "
                "the QGIS Python console) and run:  "
                "python -m pip install equipop")
        raise QgsProcessingException(
            f"This plugin needs EquiPop 1.18.0 or later; the package "
            f"in QGIS's Python is {found}, which has no equipop.doors "
            "module. Run:  python -m pip install --upgrade equipop")
    try:
        D.require(CONTRACT, door="the EquiPop QGIS plugin",
                  files="the plugin folder")
    except D.DoorError as e:
        raise QgsProcessingException(str(e))
    return D


def check_versions(channel):
    """Say when the two halves are from different releases.

    The contract number only changes when something STRUCTURAL does,
    so an older package can sit quietly under a newer plugin and run
    with old behaviour - which cost an exchange when a fix that lived
    in the package looked like it had not worked (John, v1.26.1).
    A mismatch is not an error; it is worth one line.
    """
    try:
        import equipop
        from . import __version__ as plugin_version
        pkg = getattr(equipop, "__version__", "unknown")
        if pkg != plugin_version:
            channel.warning(
                f"The EquiPop plugin is version {plugin_version} but "
                f"the equipop package in QGIS's Python is {pkg}. They "
                "usually ship together - if something behaves as it "
                "did before an update, run:  python -m pip install "
                "--upgrade equipop  and restart QGIS.")
    except Exception:
        pass


class EquipopAlgorithm(QgsProcessingAlgorithm):
    """Everything both tools do the same way."""

    def group(self):
        return "EquiPop"

    def groupId(self):
        return "equipop"

    def createInstance(self):
        return type(self)()

    # -- help, from the one shared source ------------------------
    @staticmethod
    def help_for(name):
        from equipop.doors.help import help_for
        return help_for(name)

    def shortHelpString(self):
        """QGIS keeps help in the algorithm class - there is no
        sidecar XML as in Pro - but the WORDS are the same words."""
        from equipop.doors.help import summary_for, usage_for
        tool = self.EQP_TOOL
        return f"<p>{summary_for(tool)}</p><p>{usage_for(tool)}</p>"

    def add(self, param, advanced=False):
        """Add a parameter, attach its shared explanation, and
        optionally tuck it into QGIS's Advanced area.

        QGIS Processing builds ONE flat list - there are no
        collapsible sections as in Pro, and no dependable greying.
        The single grouping it does offer is the "Advanced
        parameters" area, so the boxes most runs never touch go
        there and the everyday list stays short (v1.25, John).

        setHelp() feeds the tooltip that appears when the cursor
        rests on a box - which is as close as QGIS gets to Pro's
        per-parameter help, and it comes from the same shared source
        so both doors explain a box in the same words.
        """
        try:
            param.setHelp(self.help_for(param.name()))
        except Exception:
            pass
        if advanced:
            try:
                from qgis.core import QgsProcessingParameterDefinition
                param.setFlags(
                    param.flags()
                    | QgsProcessingParameterDefinition.FlagAdvanced)
            except Exception:
                pass
        self.addParameter(param)
        return param

    # -- speaking ------------------------------------------------
    @staticmethod
    def channel(feedback):
        from equipop.doors.report import Channel
        return Channel.from_qgis(feedback)

    # -- reading -------------------------------------------------
    def read_points(self, source, feedback, xfield=None, yfield=None):
        """Coordinates out of a QGIS source, by the shared rules.

        Geometry wins over attributes, as in the ArcGIS door.
        Geographic coordinates are reprojected rather than refused -
        QGIS makes that easy (QgsCoordinateTransform), so there is no
        reason to send the user away to project the layer first.
        """
        D = _doors()
        from equipop.doors.loader import (PointInput, resolve_xy_fields,
                                          metric_crs_hint)
        ch = self.channel(feedback)
        names = source.fields().names()
        feats = list(source.getFeatures())
        if not feats:
            raise QgsProcessingException(
                "The input layer has no features.")

        if feats[0].hasGeometry():
            try:
                from qgis.core import QgsWkbTypes
                gt = QgsWkbTypes.geometryType(source.wkbType())
            except Exception:
                gt = 0
            if gt != 0:
                kind = {1: "lines", 2: "polygons"}.get(gt, "that shape")
                raise QgsProcessingException(
                    f"This tool measures what is around POINTS, and "
                    f"the layer you chose holds {kind}. Use a point "
                    "layer for the input - a roads or boundaries "
                    "layer belongs in the BARRIER box instead, where "
                    "it turns distance into effort.")
        has_geom = feats[0].hasGeometry()
        crs = source.sourceCrs()
        note, crs_text = "", crs.description() or crs.authid()
        # v1.26.1: remember the CRS the run actually WORKS in, not
        # the one the layer arrived in. A barrier compared against
        # the arrival CRS is left unprojected when both are degrees -
        # and 40,678 Maltese roads then collapse into a single 100 m
        # cell, silently and plausibly (John, field).
        self.working_crs = crs

        if has_geom:
            tr = None
            if crs.isGeographic():
                target = self._metric_target(feats, crs)
                tr = QgsCoordinateTransform(
                    crs, target, QgsProject.instance().transformContext())
                crs_text = target.description() or target.authid()
                self.working_crs = target
                ch.info(
                    f"The layer is in degrees ({crs.authid()}); EquiPop "
                    f"needs metres, so coordinates are reprojected to "
                    f"{crs_text} for this run. The layer itself is not "
                    "changed.")
            xs, ys = [], []
            for f in feats:
                g = f.geometry()
                if g is None or g.isEmpty():
                    xs.append(np.nan)
                    ys.append(np.nan)
                    continue
                if tr is not None:
                    g.transform(tr)
                p = g.asPoint()
                xs.append(p.x())
                ys.append(p.y())
            note = "feature geometry"
            data = {"x": np.asarray(xs, float),
                    "y": np.asarray(ys, float)}
        else:
            try:
                xf, yf, how = resolve_xy_fields(
                    names, xfield, yfield, "The input table")
            except D.DoorError as e:
                raise QgsProcessingException(str(e))
            data = {"x": self._column(feats, names, xf),
                    "y": self._column(feats, names, yf)}
            note = f"attribute fields ({how}): X = '{xf}', Y = '{yf}'"
            ch.info(f"Coordinates from {note}. X is the easting, "
                    "Y the northing.")

        for n in names:
            if n not in data:
                data[n] = self._column(feats, names, n)

        if has_geom:
            ch.info(f"Coordinates read from feature geometry "
                    f"({len(feats)} points). Working CRS: {crs_text} - "
                    "all distances are metres in this projection.")
        self._features = feats
        return PointInput("point" if has_geom else "table", data,
                          id_field=None, crs_text=crs_text, note=note)

    @staticmethod
    def _metric_target(feats, crs):
        """Name a metric CRS from the coordinates themselves, using
        the same rule the ArcGIS door uses for tables."""
        from equipop.doors.loader import metric_crs_hint
        for f in feats:
            g = f.geometry()
            if g is not None and not g.isEmpty():
                p = g.asPoint()
                hint = metric_crs_hint(p.x(), p.y())
                code = hint.split("EPSG:")[-1].rstrip(")") \
                    if "EPSG:" in hint else "3006"
                return QgsCoordinateReferenceSystem(f"EPSG:{code}")
        return QgsCoordinateReferenceSystem("EPSG:3006")

    @staticmethod
    def _column(feats, names, name):
        """Numbers as numbers, text as text.

        Forcing everything to float turned a category field of POI
        types into a column of NaN, so every group matched nothing -
        found while adding the category table, and invisible until a
        TEXT field was read. Coordinates and counts are numeric;
        `fclass` is not, and must survive as itself.
        """
        i = names.index(name)
        raw = [f.attributes()[i] for f in feats]
        out = np.empty(len(raw), float)
        for j, v in enumerate(raw):
            try:
                out[j] = float(v)
            except (TypeError, ValueError):
                out[j] = np.nan
        if len(raw) and np.isnan(out).all() and any(
                v is not None and str(v).strip() for v in raw):
            return np.asarray([("" if v is None else str(v).strip())
                               for v in raw])
        return out

    # -- writing -------------------------------------------------
    @staticmethod
    def in_sync_folder(path):
        low = str(path).lower()
        return any(m in low for m in ("onedrive", "dropbox",
                                      "google drive", "sharepoint",
                                      "icloud", "box sync"))

    def check_target(self, parameters, names, feedback):
        """The ten-character trap, in QGIS clothing: a shapefile
        output caps field names at ten characters, and here a
        GeoPackage plays the roomy role a file geodatabase plays in
        Pro. Same shared rule, different neighbour."""
        from equipop.doors.fields import refuse_short_target
        target = str(parameters.get(self.OUT) or "")
        text = refuse_short_target(target, names,
                                   container="a GeoPackage (.gpkg)")
        if text:
            raise QgsProcessingException(text)
        if self.in_sync_folder(target):
            self.channel(feedback).warning(
                "This output is inside a cloud-synced folder "
                "(OneDrive, Dropbox). Sync clients alter files that "
                "are meant to stay locked while GIS software writes "
                "them, which shows up as mysterious write failures. "
                "An ordinary local folder is safer.")

    def write(self, parameters, context, source, result, order,
              feedback):
        """Original columns, then the results, row for row."""
        out_fields = QgsFields()
        for f in source.fields():
            out_fields.append(f)
        for name in order:
            out_fields.append(QgsField(name, QVariant.Double))

        sink, dest = self.parameterAsSink(
            parameters, self.OUT, context, out_fields,
            source.wkbType(), source.sourceCrs())
        if sink is None:
            raise QgsProcessingException(
                "No output was created - choose a destination for the "
                "results.")

        n = len(self._features)
        for i, f in enumerate(self._features):
            nf = QgsFeature(out_fields)
            if f.hasGeometry():
                nf.setGeometry(f.geometry())
            vals = list(f.attributes())
            for name in order:
                v = result[name][i]
                vals.append(None if v is None or
                            (isinstance(v, float) and np.isnan(v))
                            else float(v))
            nf.setAttributes(vals)
            sink.addFeature(nf)
            if n and i % 5000 == 0:
                feedback.setProgress(100.0 * i / n)
        self.channel(feedback).info(
            f"Wrote {n} rows with {len(order)} new columns: "
            + ", ".join(order))
        return dest
