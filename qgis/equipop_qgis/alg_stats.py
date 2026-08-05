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
                       QgsProcessingParameterString,
                       QgsProcessingParameterMatrix)

import numpy as np

from .base import EquipopAlgorithm

MEASURES = ["mean", "median", "gini", "min", "max", "sd"]


from .alg_counts import OUTSIDE_MODES, REF_MODES


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
        # v1.29.2: machine 1's ladder, same names, same words. The
        # REFERENCE side only - machine 2's treatment is a set of
        # numbers, so there is nothing to choose there (John's ruling).
        self.add(QgsProcessingParameterEnum(
            "refmode", "1 \u25b8 REFERENCE POPULATION - how is it "
            "defined?", options=REF_MODES, defaultValue=0))
        self.add(QgsProcessingParameterField(
            "pop", "1a \u25b8 ...count field - how many each row "
            "stands for (people, jobs, dwellings)",
            parentLayerParameterName="layer",
            type=QgsProcessingParameterField.Numeric, optional=True))
        self.add(QgsProcessingParameterField(
            "catfield", "1b \u25b8 ...type field - the column holding "
            "the kind of each object",
            parentLayerParameterName="layer", optional=True))
        self.add(QgsProcessingParameterMatrix(
            "reftable", "1c \u25b8 ...types to INCLUDE in the "
            "reference population, one per row",
            headers=["Type"], optional=True))
        self.add(QgsProcessingParameterEnum(
            "keepoutside", "1d \u25b8 ...rows whose type is NOT "
            "included", options=OUTSIDE_MODES, defaultValue=0))
        self.add(QgsProcessingParameterField(
            "values", "2 \u25b8 TREATMENT VALUES - the numeric fields "
            "to measure (income, rent, age)",
            parentLayerParameterName="layer",
            type=QgsProcessingParameterField.Numeric,
            allowMultiple=True))
        self.add(QgsProcessingParameterEnum(
            "measures", "2a \u25b8 ...measures to calculate",
            options=MEASURES,
            allowMultiple=True, defaultValue=[0, 1, 2]))
        self.add(QgsProcessingParameterString(
            "pcts", "2b \u25b8 ...percentiles, space separated "
            "(e.g. 10 25 75 90)",
            optional=True))
        self.add(QgsProcessingParameterString(
            "k", "3 \u25b8 k - neighbourhood sizes in people, space "
            "separated",
            defaultValue="400", optional=True))
        self.add(QgsProcessingParameterString(
            "r", "3a \u25b8 ...or radii in metres, space separated",
            optional=True))
        self.add(QgsProcessingParameterNumber(
            "unit", "Cell size in metres - bigger cells mean fewer "
            "origins and faster runs", defaultValue=100.0,
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

        vals = self.parameterAsStrings(parameters, "values", context)
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
        pop = (self.parameterAsStrings(parameters, "pop", context) or
               [None])[0]

        names = predict_result_fields(
            "stats", k_text, r_text, "", [], vals, wanted,
            decaying=False, efforting=False)
        self.check_target(parameters, names, feedback)

        with stage(ch, "reading input"):
            pts = self.read_points(
                source, feedback,
                (self.parameterAsStrings(parameters, "xfield", context)
                 or [None])[0],
                (self.parameterAsStrings(parameters, "yfield", context)
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
        # v1.29.2, the ladder's third rung. John's rule, unchanged:
        # a row outside the reference population weighs ZERO - it is
        # nobody's neighbour and contributes to no statistic - but it
        # still gets its own results. Zeroing the weight is the whole
        # mechanism; machine 2 already weights everything by it, so
        # no engine change is needed.
        refmode = (self.parameterAsEnums(parameters, "refmode",
                                         context) or [0])[0]
        catfield = (self.parameterAsStrings(parameters, "catfield",
                                           context) or [None])[0]
        if refmode == 2 and catfield:
            from equipop.categorical import categories_to_binary
            wanted = [str(v).strip() for v in
                      (self.parameterAsMatrix(parameters, "reftable",
                                              context) or [])
                      if str(v).strip()]
            mask, _ = categories_to_binary(
                pts.data[catfield], {}, pop_values=wanted or None)
            base = (np.nan_to_num(np.asarray(pts.data[pop], float))
                    if pop else np.ones(len(mask)))
            outside = int((~mask).sum())
            if (self.parameterAsEnums(parameters, "keepoutside",
                                      context) or [0])[0] == 0:
                kw["weight"] = base * mask
                if outside:
                    ch.info(
                        f"{outside} row(s) are outside the reference "
                        "population: they count as zero, so they are "
                        "nobody's neighbour and enter no statistic - "
                        "but they still get their own results.")
            else:
                kw["weight"] = base * mask
                pts.data["x"] = np.where(mask, pts.data["x"], np.nan)
                pts.data["y"] = np.where(mask, pts.data["y"], np.nan)
                if outside:
                    ch.info(f"{outside} row(s) are outside the "
                            "reference population and are DROPPED: "
                            "they get Null results.")
            ch.info(f"Reference population: {int(mask.sum())} rows.")

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
