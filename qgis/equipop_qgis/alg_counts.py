# -*- coding: utf-8 -*-
"""
alg_counts.py - Counts and Shares, QGIS side.

The same tool as machine 1 in the ArcGIS toolbox, with the same
parameter names, the same explanations and the same engine. The
numbers are checked against the shared Gridby reference, so a QGIS
student and a Pro student get the same answers out of the same town.
"""
from qgis.core import (QgsProcessing, QgsProcessingException,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterMatrix,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString)

DECAY_MODELS = ["no decay", "negexp", "gauss", "linear"]

# The same ladder as the ArcGIS door, in the same order. QGIS has no
# collapsible sections and no dependable greying, so here the ladder
# shows through ORDER and WORDING instead.
REF_MODES = ["every point counts as one",
             "a field holds the count",
             "only selected types, with a count field"]
TREAT_MODES = ["not measuring one - distances and counts only",
               "one column per group, counts inside",
               "types from a type field, grouped"]
OUTSIDE_MODES = ["give them results, counting as zero",
                 "leave their results Null"]

import numpy as np

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
            "pop", "REFERENCE POPULATION - how much does each row "
            "count? A field holding people (or guests, jobs, "
            "revenue). Leave empty and every row counts as one.", parentLayerParameterName="layer",
            type=QgsProcessingParameterField.Numeric, optional=True))
        self.add(QgsProcessingParameterField(
            "treat", "...group count fields - one column per group, "
            "holding TOTALS, never averages",
            parentLayerParameterName="layer",
            type=QgsProcessingParameterField.Numeric,
            allowMultiple=True, optional=True))
        self.add(QgsProcessingParameterString(
            "k", "k - neighbourhood sizes in people, space separated",
            defaultValue="400", optional=True))
        self.add(QgsProcessingParameterString(
            "r", "Radii in metres, space separated", optional=True))
        # --- groups from a category field -------------------------
        self.add(QgsProcessingParameterField(
            "catfield", "...type field - the column holding the kind "
            "of each object",
            parentLayerParameterName="layer", optional=True))
        self.add(QgsProcessingParameterMatrix(
            "reftable", "...types to INCLUDE in the reference "
            "population, one per row",
            headers=["Type"], optional=True))
        self.add(QgsProcessingParameterEnum(
            "keepoutside", "...rows whose type is NOT included",
            options=OUTSIDE_MODES, defaultValue=0))
        self.add(QgsProcessingParameterEnum(
            "treatmode", "TREATMENT POPULATION - how is it defined? "
            "(no count field: k belongs to the reference population, "
            "so the treatment is counted in the same units)",
            options=TREAT_MODES, defaultValue=0))
        self.add(QgsProcessingParameterField(
            "treatcatfield", "...type field for the groups (usually "
            "the same column - choose it here too)",
            parentLayerParameterName="layer", optional=True))
        self.add(QgsProcessingParameterMatrix(
            "treattable", "...groups: one row per type - the type, "
            "and the group name it joins",
            headers=["Type", "Group name"], optional=True))
        self.add(QgsProcessingParameterString(
            "restgroup", "...name a group for every OTHER value "
            "(optional; for example: other)", optional=True))

        # --- distance decay ---------------------------------------
        self.add(QgsProcessingParameterEnum(
            "model", "Distance decay", options=DECAY_MODELS,
            defaultValue=0))
        self.add(QgsProcessingParameterNumber(
            "halflife", "Half-life in metres (the distance at which "
            "weight halves)", defaultValue=0.0, optional=True,
            type=QgsProcessingParameterNumber.Double))
        self.add(QgsProcessingParameterNumber(
            "decayeps", "Ignore weights below this (truncation)",
            defaultValue=1e-6, optional=True,
            type=QgsProcessingParameterNumber.Double))

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

        model = DECAY_MODELS[(self.parameterAsEnums(
            parameters, "model", context) or [0])[0]]
        half = self.parameterAsDouble(parameters, "halflife", context)
        decaying = model != "no decay" and half > 0

        names = predict_result_fields(
            "counts", k_text, r_text, "", treats, [], [],
            decaying=decaying, efforting=False)
        self.check_target(parameters, names, feedback)

        with stage(ch, "reading input"):
            pts = self.read_points(
                source, feedback,
                (self.parameterAsFields(parameters, "xfield", context)
                 or [None])[0],
                (self.parameterAsFields(parameters, "yfield", context)
                 or [None])[0])

        kw = dict(unit_size=float(unit), treat_are_counts=True)
        if decaying:
            kw["decay_model"] = model
            kw["half_life_m"] = float(half)
            eps = self.parameterAsDouble(parameters, "decayeps",
                                         context)
            kw["decay_eps"] = float(eps) if eps > 0 else 1e-6
            ch.info(self._decay_in_plain_numbers(model, half))
        if k_text:
            kw["k_values"] = [int(v) for v in k_text.split()]
        if r_text:
            kw["r_values"] = [float(v) for v in r_text.split()]
        if pop:
            kw["weight"] = pts.data[pop]
        if treats:
            kw["treat"] = {t: pts.data[t] for t in treats}

        catfield = (self.parameterAsFields(parameters, "catfield",
                                           context) or [None])[0]
        if catfield:
            from equipop.categorical import categories_to_binary
            pop_vals = [str(v).strip() for v in
                        (self.parameterAsMatrix(parameters, "reftable",
                                                context) or [])
                        if str(v).strip()]
            groups = self._groups_from_matrix(
                self.parameterAsMatrix(parameters, "treattable",
                                       context))
            tcatf = (self.parameterAsFields(parameters,
                                            "treatcatfield", context)
                     or [None])[0] or catfield
            rest = self.parameterAsString(parameters, "restgroup",
                                          context).strip()
            pop_mask, _ = categories_to_binary(
                pts.data[catfield], {}, pop_values=pop_vals or None)
            _, cat_treats = categories_to_binary(
                pts.data[tcatf], groups,
                pop_values=pop_vals or None,
                rest_group=rest or None, rest_in_population=None)
            tvf = pop
            if tvf:
                tcol = np.nan_to_num(pts.data[tvf].astype(float))
                cat_treats = {g: v * tcol
                              for g, v in cat_treats.items()}
                ch.info(self._units_note(tvf, pop))
            else:
                ch.info("No value field given, so every row counts as "
                        "one: the shares are shares of PLACES.")
            kw.setdefault("treat", {}).update(cat_treats)
            outside = int((~pop_mask).sum())
            if (self.parameterAsEnums(parameters, "keepoutside",
                                      context) or [0])[0] == 0:
                # John's rule: outside the reference population means
                # zero people - nobody's neighbour - but the row
                # still gets its own results.
                base = (pts.data[pop].astype(float) if pop
                        else np.ones(pts.n))
                kw["weight"] = np.nan_to_num(base) * pop_mask
                if outside:
                    ch.info(f"{outside} row(s) are outside the "
                            "reference population: they count as "
                            "zero people, but still get their own "
                            "results.")
            else:
                kw["weight"] = pop_mask.astype(float)
                keep = pop_mask.astype(bool)
                pts.data["x"] = np.where(keep, pts.data["x"], np.nan)
                pts.data["y"] = np.where(keep, pts.data["y"], np.nan)
                if outside:
                    ch.info(f"{outside} row(s) are outside the "
                            "reference population and are DROPPED.")

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

    # ---------------------------------------------------------------
    @staticmethod
    def _groups_from_matrix(rows):
        """QGIS hands a matrix back as ONE FLAT LIST: value, group,
        value, group... Rows sharing a group name merge, exactly as
        in the ArcGIS door."""
        groups = {}
        flat = list(rows or [])
        for i in range(0, len(flat) - 1, 2):
            val = str(flat[i] or "").strip()
            grp = str(flat[i + 1] or "").strip()
            if val and grp:
                groups.setdefault(grp, []).append(val)
        return groups

    @staticmethod
    def _units_note(tvf, pop):
        if pop and tvf != pop:
            return (f"The treatment population is counted in '{tvf}' "
                    f"while the reference is counted in '{pop}' - the "
                    "R_ columns are a RATIO of two different things, "
                    "not a share, and can go above 1.")
        return (f"Treatment population counted in '{tvf}', the same "
                "units as the reference - so every R_ column is a "
                "share between 0 and 1.")

    @staticmethod
    def _decay_in_plain_numbers(model, half):
        """Say what the curve DOES, not only what it is called - the
        naming pass John asked for: plain words first."""
        h = float(half)
        return (f"Distance decay ({model}): weight halves every "
                f"{h:g} m - at {h:g} m a person counts half, at "
                f"{2 * h:g} m a quarter, at {3 * h:g} m an eighth.")
