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

# BACKLOG 103: QGIS offered six of these while Pro offered twelve,
# and door_parity.py could not see it because both doors have a box
# CALLED "measures" (BACKLOG 105). The engine has computed all of
# them since 1.16; only this list was short. Order and wording follow
# Pro's _MEASURES so the two doors read alike.
MEASURES = ["mean", "median", "gini", "sd", "variance", "se",
            "min", "max", "count", "sum", "range"]
# Pro calls it "variance"; equipop/stats.py calls it "var". One name
# for the user, one for the engine, mapped in exactly one place.
MEASURE_KEY = {"variance": "var"}


from .alg_counts import (OUTSIDE_MODES, OVERSHOOT_MODES,  # noqa: F401
                         OVERSHOOT_VALUES, REF_MODES,
                         SELFPOT_MODES, SELFPOT_VALUES)
# REF_MODES carries its "(fill 1a)" hints from alg_counts, so machine
# 1 and machine 2 cannot start describing the same ladder differently
# (BACKLOG 104/105).


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
            "unit", "Cell size in map units, whole numbers only - "
            "bigger cells mean fewer origins and faster runs", defaultValue=100.0,
            type=QgsProcessingParameterNumber.Double))
        # BACKLOG 141: a three-way choice, not a free number. The
        # wording is duplicated from equipop/doors/rungs.py and
        # pinned by test_rungs.py - see the note above on 105/78 for
        # why it cannot be imported.
        self.add(QgsProcessingParameterEnum(
            "selfpot", "Self-potential - the distance to what is "
            "LOCAL, inside your own cell", options=SELFPOT_MODES,
            defaultValue=2), advanced=True)
        # BACKLOG 118, v1.31: the same default as machine 1. This box
        # defaulted to `whole` while a fraction of a cell had no
        # median; weighted statistics gave it one, so the two machines
        # agree again and a student running both over one dataset gets
        # one answer instead of two.
        self.add(QgsProcessingParameterEnum(
            "overshoot", "The ring that crosses k",
            options=OVERSHOOT_MODES, defaultValue=1), advanced=True)
        self.add(QgsProcessingParameterNumber(
            "seed", "Seed - only used by 'sampled' and by "
            "permutations; empty draws one and prints it",
            optional=True,
            type=QgsProcessingParameterNumber.Integer), advanced=True)
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

        wanted = [MEASURE_KEY.get(MEASURES[i], MEASURES[i]) for i in
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
        # BACKLOG 116: this read `... or 100.0`, so a cell size of
        # ZERO - a real thing a user can type - was silently replaced
        # by 100 m and the run went ahead at a scale nobody chose.
        # The same idiom nearly ate a deliberate self-potential of 0
        # in Pro. Any parameter whose zero is MEANINGFUL, or whose
        # zero is nonsense, must be refused rather than substituted.
        unit = self.parameterAsDouble(parameters, "unit", context)
        if unit is None or unit != unit:            # unset or NaN
            unit = 100.0
        # BACKLOG 155 + 160: a WHOLE number of MAP UNITS, refused
        # rather than rounded - six modules round differently, so 2.5
        # gives cells of uneven width. And "map units", not "metres":
        # nothing here knows the CRS is metric (160).
        if unit <= 0 or abs(unit - round(unit)) > 1e-9:
            raise QgsProcessingException(
                f"Cell size must be a WHOLE number of map units "
                f"greater than 0; got {unit:g}. Fractional sizes are "
                "rounded differently by different parts of EquiPop, "
                "so they are refused rather than silently changed.")
        unit = float(round(unit))
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

        # BACKLOG 99, named explicitly as in machine 1. The note that
        # stood here - warning that the two machines used different
        # modes - retired with BACKLOG 118: they no longer do.
        overshoot_mode = OVERSHOOT_VALUES[
            (self.parameterAsEnums(parameters, "overshoot",
                                   context) or [1])[0]]
        seed = self.optional_int(parameters, "seed")
        kw = dict(unit_size=float(unit),
                  overshoot_mode=overshoot_mode, seed=seed,
                  self_potential=SELFPOT_VALUES[
                      (self.parameterAsEnums(parameters, "selfpot",
                                             context) or [2])[0]],
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

        # BACKLOG 104, the same three-part fix as machine 1: this
        # block used to read `refmode == 2 and catfield` and do
        # NOTHING AT ALL when the type field was missing - the exact
        # silence that cost John a field run in the other door.
        from equipop.doors import rungs
        ref_rows = [str(v).strip() for v in
                    (self.parameterAsMatrix(parameters, "reftable",
                                            context) or [])
                    if str(v).strip()]
        if refmode == 1 and not pop:
            raise QgsProcessingException(rungs.missing(
                "box 1a, the count field", "the reference population",
                REF_MODES[1]))
        if refmode == 2 and not catfield:
            raise QgsProcessingException(rungs.missing(
                "box 1b, the type field", "the reference population",
                REF_MODES[2]))
        if refmode != 2:
            for box, filled in (("Box 1b, the type field",
                                 bool(catfield)),
                                ("Box 1c, the list of reference types",
                                 bool(ref_rows))):
                if filled:
                    ch.info(rungs.ignored(box,
                                          "the reference population",
                                          REF_MODES[refmode]))

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
