# -*- coding: utf-8 -*-
"""
alg_stats.py - Value Statistics, QGIS side.

Machine 2 of the ArcGIS toolbox: not who is around a point, but what
the values around it look like - mean, median, Gini, percentiles over
the k nearest people.
"""
from qgis.core import (QgsProcessing, QgsProcessingException,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString)

from .base import EquipopAlgorithm

MEASURES = ["mean", "median", "gini", "min", "max", "sd"]


class ValueStatistics(EquipopAlgorithm):

    EQP_TOOL = "ValueStatistics"
    OUT = "outfc"

    def name(self):
        return "valuestatistics"

    def displayName(self):
        return "2. Value Statistics (k / radius)"

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
            "pop", "Population field (people per row)",
            parentLayerParameterName="layer",
            type=QgsProcessingParameterField.Numeric, optional=True))
        self.add(QgsProcessingParameterField(
            "values", "Value fields to summarise",
            parentLayerParameterName="layer",
            type=QgsProcessingParameterField.Numeric,
            allowMultiple=True))
        self.add(QgsProcessingParameterEnum(
            "measures", "Measures", options=MEASURES,
            allowMultiple=True, defaultValue=[0, 1, 2]))
        self.add(QgsProcessingParameterString(
            "pcts", "Percentiles, space separated (e.g. 10 25 75 90)",
            optional=True))
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

        vals = self.parameterAsFields(parameters, "values", context)
        if not vals:
            raise QgsProcessingException(
                "Choose at least one value field to summarise - this "
                "tool describes the VALUES around each point.")

        wanted = [MEASURES[i] for i in
                  self.parameterAsEnums(parameters, "measures", context)]
        pcts = self.parameterAsString(parameters, "pcts", context).split()
        wanted += [f"p{p}" for p in pcts]
        wanted = wanted or ["mean", "median", "gini"]

        k_text = self.parameterAsString(parameters, "k", context).strip()
        r_text = self.parameterAsString(parameters, "r", context).strip()
        if not k_text and not r_text:
            raise QgsProcessingException(
                "Give at least one k (a number of people) or one "
                "radius in metres.")
        unit = self.parameterAsDouble(parameters, "unit", context) or 100.0
        pop = (self.parameterAsFields(parameters, "pop", context) or
               [None])[0]

        names = predict_result_fields(
            "stats", k_text, r_text, "", [], vals, wanted,
            decaying=False, efforting=False)
        self.check_target(parameters, names, feedback)

        with stage(ch, "reading input"):
            pts = self.read_points(
                source, feedback,
                (self.parameterAsFields(parameters, "xfield", context)
                 or [None])[0],
                (self.parameterAsFields(parameters, "yfield", context)
                 or [None])[0])

        kw = dict(unit_size=float(unit),
                  values={v: pts.data[v] for v in vals},
                  stats={v: wanted for v in vals})
        if k_text:
            kw["k_values"] = [int(v) for v in k_text.split()]
        if r_text:
            kw["r_values"] = [float(v) for v in r_text.split()]
        if pop:
            kw["weight"] = pts.data[pop]

        ch.info(f"Calculating (stats engine, {pts.n} rows, cell size "
                f"{float(unit):g} m). Measures: " + " ".join(wanted))
        with stage(ch, "calculating"), speaking(ch):
            res = dispatch("stats", pts.data["x"], pts.data["y"], **kw)

        order = [n for n in names if n in res] + \
                [n for n in res if n not in names]
        with stage(ch, "writing output"):
            dest = self.write(parameters, context, source, res, order,
                              feedback)
        return {self.OUT: dest}
