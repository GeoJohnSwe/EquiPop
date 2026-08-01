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
        # --- groups from a category field -------------------------
        self.add(QgsProcessingParameterField(
            "catfield", "Category field (codes or names) - builds "
            "population and groups from its VALUES",
            parentLayerParameterName="layer", optional=True))
        self.add(QgsProcessingParameterMatrix(
            "cattable", "Categories: one row per value - value, group "
            "name, and 1 or 0 for whether it counts as population",
            headers=["Category value", "Group name", "In population?"],
            optional=True))
        self.add(QgsProcessingParameterString(
            "restgroup", "Put every OTHER value in this group "
            "(optional)", optional=True))
        self.add(QgsProcessingParameterBoolean(
            "restinpop", "...and count those other values as "
            "population too", defaultValue=True))

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
            rows = self.parameterAsMatrix(parameters, "cattable",
                                          context)
            pop_vals, groups = self._groups_from_matrix(rows)
            rest = self.parameterAsString(parameters, "restgroup",
                                          context).strip()
            pop_mask, cat_treats = categories_to_binary(
                pts.data[catfield], groups,
                pop_values=pop_vals or None,
                rest_group=rest or None,
                rest_in_population=self.parameterAsBool(
                    parameters, "restinpop", context))
            kw.setdefault("treat", {}).update(cat_treats)
            if pop is None:
                kw["weight"] = pop_mask.astype(float)

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
        """QGIS hands a matrix back as one flat list: value, group,
        in-population, value, group, in-population... Rows sharing a
        group name merge, exactly as in the ArcGIS door."""
        pop_vals, groups = [], {}
        flat = list(rows or [])
        for i in range(0, len(flat) - 2, 3):
            val = str(flat[i] or "").strip()
            grp = str(flat[i + 1] or "").strip()
            inpop = str(flat[i + 2] if flat[i + 2] is not None
                        else "1").strip().lower()
            if not val:
                continue
            if inpop not in ("false", "no", "0", "n", ""):
                pop_vals.append(val)
            if grp:
                groups.setdefault(grp, []).append(val)
        return pop_vals, groups

    @staticmethod
    def _decay_in_plain_numbers(model, half):
        """Say what the curve DOES, not only what it is called - the
        naming pass John asked for: plain words first."""
        h = float(half)
        return (f"Distance decay ({model}): weight halves every "
                f"{h:g} m - at {h:g} m a person counts half, at "
                f"{2 * h:g} m a quarter, at {3 * h:g} m an eighth.")
