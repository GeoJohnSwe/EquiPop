# -*- coding: utf-8 -*-
"""
alg_counts.py - Counts and Shares, QGIS side.

The same tool as machine 1 in the ArcGIS toolbox, with the same
parameter names, the same explanations and the same engine. The
numbers are checked against the shared Gridby reference, so a QGIS
student and a Pro student get the same answers out of the same town.
"""
from qgis.core import (QgsProcessing, QgsProcessingException,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString)

from .base import EquipopAlgorithm


class CountsAndShares(EquipopAlgorithm):

    EQP_TOOL = "CountsShares"
    OUT = "outfc"

    def name(self):
        return "countsandshares"

    def displayName(self):
        return "1. Counts and Shares (k / radius)"

    def initAlgorithm(self, config=None):
        self.add(QgsProcessingParameterFeatureSource(
            "layer", "Input points or table",
            [QgsProcessing.TypeVectorAnyGeometry]))
        self.add(QgsProcessingParameterField(
            "xfield", "X field (easting) - only for tables without "
            "geometry", parentLayerParameterName="layer",
            type=QgsProcessingParameterField.Numeric, optional=True))
        self.add(QgsProcessingParameterField(
            "yfield", "Y field (northing) - only for tables without "
            "geometry", parentLayerParameterName="layer",
            type=QgsProcessingParameterField.Numeric, optional=True))
        self.add(QgsProcessingParameterField(
            "pop", "Population field (people per row; leave empty if "
            "one row is one person)", parentLayerParameterName="layer",
            type=QgsProcessingParameterField.Numeric, optional=True))
        self.add(QgsProcessingParameterField(
            "treat", "Group fields (counts of the group in each row)",
            parentLayerParameterName="layer",
            type=QgsProcessingParameterField.Numeric,
            allowMultiple=True, optional=True))
        self.add(QgsProcessingParameterString(
            "k", "k - neighbourhood sizes in people, space separated",
            defaultValue="400", optional=True))
        self.add(QgsProcessingParameterString(
            "r", "Radii in metres, space separated", optional=True))
        self.add(QgsProcessingParameterNumber(
            "unit", "Cell size in metres", defaultValue=100.0,
            type=QgsProcessingParameterNumber.Double))
        self.add(QgsProcessingParameterFeatureSink(
            self.OUT, "Results"))

    def processAlgorithm(self, parameters, context, feedback):
        from equipop.doors.fields import predict_result_fields
        from equipop.doors.report import speaking, stage
        from equipop.stata_bridge import dispatch

        ch = self.channel(feedback)
        source = self.parameterAsSource(parameters, "layer", context)
        if source is None:
            raise QgsProcessingException("No input layer was given.")

        k_text = self.parameterAsString(parameters, "k", context).strip()
        r_text = self.parameterAsString(parameters, "r", context).strip()
        if not k_text and not r_text:
            raise QgsProcessingException(
                "Give at least one k (a number of people) or one "
                "radius in metres - otherwise there is no "
                "neighbourhood to measure.")
        unit = self.parameterAsDouble(parameters, "unit", context) or 100.0
        pop = (self.parameterAsFields(parameters, "pop", context) or
               [None])[0]
        treats = self.parameterAsFields(parameters, "treat", context)

        names = predict_result_fields(
            "counts", k_text, r_text, "", treats, [], [],
            decaying=False, efforting=False)
        self.check_target(parameters, names, feedback)

        with stage(ch, "reading input"):
            pts = self.read_points(
                source, feedback,
                (self.parameterAsFields(parameters, "xfield", context)
                 or [None])[0],
                (self.parameterAsFields(parameters, "yfield", context)
                 or [None])[0])

        kw = dict(unit_size=float(unit), treat_are_counts=True)
        if k_text:
            kw["k_values"] = [int(v) for v in k_text.split()]
        if r_text:
            kw["r_values"] = [float(v) for v in r_text.split()]
        if pop:
            kw["weight"] = pts.data[pop]
        if treats:
            kw["treat"] = {t: pts.data[t] for t in treats}

        ch.info(f"Calculating (counts engine, {pts.n} rows, cell size "
                f"{float(unit):g} m).")
        with stage(ch, "calculating"), speaking(ch):
            res = dispatch("counts", pts.data["x"], pts.data["y"], **kw)

        order = [n for n in names if n in res] + \
                [n for n in res if n not in names]
        with stage(ch, "writing output"):
            dest = self.write(parameters, context, source, res, order,
                              feedback)
        return {self.OUT: dest}
