# -*- coding: utf-8 -*-
"""
alg_counts.py - Counts and Shares, QGIS side.

The same tool as machine 1 in the ArcGIS toolbox, with the same
parameter names, the same explanations and the same engine. The
numbers are checked against the shared Gridby reference, so a QGIS
student and a Pro student get the same answers out of the same town.
"""
from qgis.core import (QgsProcessing, QgsProcessingException,
                       QgsProcessingParameterRasterLayer,
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
AGG_MODES = ["additive (costs add up)", "max", "min", "mean"]

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
            type=QgsProcessingParameterField.Numeric, optional=True),
            advanced=True)
        self.add(QgsProcessingParameterField(
            "yfield", "Y field (northing) - only for tables without "
            "geometry", parentLayerParameterName="layer",
            type=QgsProcessingParameterField.Numeric, optional=True),
            advanced=True)
        self.add(QgsProcessingParameterEnum(
            "refmode", "1 \u25b8 REFERENCE POPULATION - how is it "
            "defined?", options=REF_MODES, defaultValue=0))
        self.add(QgsProcessingParameterField(
            "pop", "1a \u25b8 ...count field - how many people (or "
            "guests, jobs) each row stands for",
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

        self.add(QgsProcessingParameterEnum(
            "treatmode", "2 \u25b8 TREATMENT POPULATION - how is it "
            "defined? (no count field: k belongs to the reference "
            "population, so the treatment is counted in the same "
            "units)", options=TREAT_MODES, defaultValue=0))
        self.add(QgsProcessingParameterField(
            "treatcatfield", "2a \u25b8 ...type field for the groups "
            "(usually the same column - choose it here too)",
            parentLayerParameterName="layer", optional=True))
        self.add(QgsProcessingParameterMatrix(
            "treattable", "2b \u25b8 ...groups: one row per type - "
            "the type, and the group name it joins",
            headers=["Type", "Group name"], optional=True))
        self.add(QgsProcessingParameterString(
            "restgroup", "2c \u25b8 ...name a group for every OTHER "
            "type (optional; for example: other)", optional=True))
        self.add(QgsProcessingParameterField(
            "treat", "2d \u25b8 ...group count fields - one column "
            "per group, holding TOTALS, never averages",
            parentLayerParameterName="layer",
            type=QgsProcessingParameterField.Numeric,
            allowMultiple=True, optional=True))

        self.add(QgsProcessingParameterString(
            "k", "3 \u25b8 k - neighbourhood sizes in people, space "
            "separated", defaultValue="400", optional=True))
        self.add(QgsProcessingParameterString(
            "r", "3a \u25b8 ...or radii in metres, space separated",
            optional=True))

        self.add(QgsProcessingParameterEnum(
            "model", "4 \u25b8 distance decay", options=DECAY_MODELS,
            defaultValue=0))
        self.add(QgsProcessingParameterNumber(
            "halflife", "4a \u25b8 ...half-life in metres (the "
            "distance at which weight halves)", defaultValue=0.0,
            optional=True,
            type=QgsProcessingParameterNumber.Double))

        # --- barriers and terrain: distance becomes EFFORT ---------
        self.add(QgsProcessingParameterFeatureSource(
            "barrier", "5 \u25b8 barrier layer - a river, railway or "
            "lake that costs effort to cross (optional)",
            [QgsProcessing.TypeVectorAnyGeometry], optional=True))
        self.add(QgsProcessingParameterField(
            "barrierfield", "5a \u25b8 ...its friction field - the "
            "crossing cost in rounds",
            parentLayerParameterName="barrier", optional=True))
        self.add(QgsProcessingParameterRasterLayer(
            "barrierraster", "5b \u25b8 ...or a friction RASTER "
            "(cost per cell; NoData or zero = free)", optional=True))
        self.add(QgsProcessingParameterRasterLayer(
            "dem", "5c \u25b8 ...and/or an elevation raster, so "
            "SLOPE costs effort", optional=True))
        self.add(QgsProcessingParameterString(
            "tau", "5d \u25b8 effort budgets, space separated - how "
            "many rounds each person may spend (gives N_tau columns)",
            optional=True))
        self.add(QgsProcessingParameterBoolean(
            "roundtrip", "5e \u25b8 charge the return journey too "
            "(there and back)", defaultValue=False), advanced=True)
        self.add(QgsProcessingParameterEnum(
            "barrieragg", "5f \u25b8 where barriers overlap",
            options=AGG_MODES, defaultValue=0), advanced=True)

        # Rarely touched: into QGIS's Advanced area, so the everyday
        # list stays short (v1.25, John - QGIS has no sections, and
        # this is the one grouping it does offer).
        self.add(QgsProcessingParameterNumber(
            "decayeps", "Ignore decay weights below this "
            "(truncation)", defaultValue=1e-6, optional=True,
            type=QgsProcessingParameterNumber.Double), advanced=True)
        self.add(QgsProcessingParameterNumber(
            "unit", "Cell size in metres - bigger cells mean fewer "
            "origins and faster runs", defaultValue=100.0,
            type=QgsProcessingParameterNumber.Double), advanced=True)
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

        refmode = (self.parameterAsEnums(parameters, "refmode",
                                         context) or [0])[0]
        if refmode == 0:
            pop = None            # every point counts as one
        catfield = (self.parameterAsFields(parameters, "catfield",
                                           context) or [None])[0]
        if refmode == 2 and catfield:
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

        fr, dem_payload = self._effort_ingredients(
            parameters, context, ch, unit,
            getattr(self, "working_crs", source.sourceCrs()),
            points_xy=(pts.data["x"], pts.data["y"]))
        engine = "counts"
        if fr is not None or dem_payload is not None:
            # a different ENGINE, not just an extra argument: effort
            # is walked in rounds over a cost surface, which is a
            # different calculation from counting by distance
            engine = "slope" if dem_payload is not None else "friction"
            ch.info(
                "Distance ingredients given, so this run uses the "
                "EFFORT engine: neighbours are farther away in ROUNDS "
                "rather than metres. It takes longer, and Rounds / "
                "N_tau columns join or replace Dist.")
            if fr is not None:
                kw["friction_file"] = fr
            if dem_payload is not None:
                kw["dem"] = dem_payload
            kw["roundtrip"] = self.parameterAsBool(
                parameters, "roundtrip", context)
            kw.pop("r_values", None)     # a radius over effort is
            tau = self.parameterAsString(  # not defined
                parameters, "tau", context).strip()
            if tau:
                kw["tau_values"] = [float(v) for v in tau.split()]
            if decaying:
                ch.warning(
                    "Decay over effort is not available, so decay is "
                    "ignored for this run.")
                for key in ("decay_model", "half_life_m", "decay_eps"):
                    kw.pop(key, None)

        ch.info(f"Calculating ({engine} engine, {pts.n} rows, cell "
                f"size {float(unit):g} m).")
        with stage(ch, "calculating"), speaking(ch):
            res = dispatch(engine, pts.data["x"], pts.data["y"], **kw)

        order = [n for n in names if n in res] + \
                [n for n in res if n not in names]
        with stage(ch, "writing output"):
            dest = self.write(parameters, context, source, res, order,
                              feedback)
        return {self.OUT: dest}

    # ---------------------------------------------------------------
    def _effort_ingredients(self, parameters, context, ch, unit,
                            working_crs, points_xy=None):
        """Barriers and terrain, read the QGIS way and handed to the
        shared engine (v1.26). Returns (friction table or None, DEM
        payload or None)."""
        from .barriers import (barrier_to_friction, check_plausible,
                               merge_friction,
                               raster_to_friction_layer)
        agg = ["sum", "max", "min", "mean"][
            (self.parameterAsEnums(parameters, "barrieragg", context)
             or [0])[0]]
        tables = []
        vec = self.parameterAsSource(parameters, "barrier", context)
        if vec is not None:
            field = (self.parameterAsFields(parameters, "barrierfield",
                                            context) or [None])[0]
            table = barrier_to_friction(vec, field, unit, agg, ch,
                                        working_crs)
            if points_xy is not None:
                check_plausible(table, vec.featureCount(), points_xy,
                                float(unit), "Barrier layer", ch)
            tables.append(table)
        rast = self.parameterAsRasterLayer(parameters, "barrierraster",
                                           context)
        if rast is not None:
            tables.append(raster_to_friction_layer(rast, unit, ch))
        fr = merge_friction(tables, agg, ch)

        dem_layer = self.parameterAsRasterLayer(parameters, "dem",
                                                context)
        dem = None
        if dem_layer is not None:
            dem = self._dem_payload(dem_layer, ch)
        return fr, dem

    @staticmethod
    def _dem_payload(layer, ch):
        """Elevation as an array plus its geo-reference - the same
        shape the ArcGIS door hands over, so the slope engine cannot
        tell the doors apart."""
        import numpy as _np
        try:
            p = layer.dataProvider()
            block = p.block(1, layer.extent(), layer.width(),
                            layer.height())
            arr = _np.array([[block.value(r, c)
                              for c in range(layer.width())]
                             for r in range(layer.height())],
                            dtype=float)
            ext = layer.extent()
            # the key names are the engine's, not ours - the ArcGIS
            # door hands over exactly this shape, so the slope engine
            # cannot tell the two doors apart
            payload = {"array": arr,
                       "x_min": float(ext.xMinimum()),
                       "y_max": float(ext.yMaximum()),
                       "cell_w": ext.width() / layer.width(),
                       "cell_h": ext.height() / layer.height(),
                       "nodata": p.sourceNoDataValue(1)}
        except Exception as exc:
            raise QgsProcessingException(
                f"Could not read the elevation raster ({exc}).")
        ch.info(f"Elevation raster read: {arr.shape[0]} x "
                f"{arr.shape[1]} cells - slope will cost effort.")
        return payload

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
