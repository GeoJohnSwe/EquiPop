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

# What the dropdown shows when the package cannot be read. NOT a
# guess at the engine's models - one honest option, and the person
# gets the real sentence the moment they press Run (v1.29.2).
DECAY_FALLBACK = ["no decay"]


def _decay_choices():
    """From the ENGINE, never from memory (v1.28): the old list
    offered 'gauss' and 'linear', neither of which exists.

    Never raises (v1.29.2). This used to be called at MODULE level,
    so a package older than the plugin killed the whole plugin at
    import - before QGIS had an algorithm to attach a message to,
    and therefore before any of the guards written for exactly that
    situation could speak. John, field, 1.29.0: plugin 1.29.0 on
    package 1.27.0 gave a bare traceback and no EquiPop at all,
    while `check_versions()` sat inside processAlgorithm with the
    explanation already written in it.
    """
    try:
        from equipop.doors.decaynames import choices
        return choices()
    except Exception:
        return list(DECAY_FALLBACK)

# The same ladder as the ArcGIS door, in the same order. QGIS has no
# collapsible sections and no dependable greying, so here the ladder
# shows through ORDER and WORDING instead.
# BACKLOG 105. This wording is DUPLICATED - the canonical copy lives
# in equipop/doors/rungs.py - and it cannot be imported from there,
# because of BACKLOG 78: QGIS imports a plugin at STARTUP, so a
# module-level `import equipop` kills the whole plugin when the
# package is missing or old, before there is any algorithm to attach
# an explanatory message to. A guard downstream of its own failure is
# not a guard.
# So the duplication stays and is PINNED INSTEAD: test_rungs.py reads
# both copies and fails on any drift. Change rungs.py, not this.
# BACKLOG 104: each rung NAMES the box it reads, because QGIS cannot
# grey the others out. Those hints are this door's ONE addition.
REF_MODES = ["every point counts as one",
             "a field holds the count (fill 1a)",
             "only selected types, with a count field "
             "(fill 1a, 1b and 1c)"]
TREAT_MODES = ["not measuring one - distances and counts only",
               "one column per group, counts inside (fill 2a)",
               "types from a type field, grouped (fill 2b and 2c)"]
OUTSIDE_MODES = ["give them results, counting as zero",
                 "leave their results Null"]
AGG_MODES = ["additive (costs add up)", "max", "min", "mean"]
SELFPOT_MODES = [
    "0 - no distance at all; Dist_k can come out as zero",
    "0.71 - the median: half of what your cell holds is nearer than this",
    "1 - the radius at which k of it is reached (recommended)",
]
SELFPOT_VALUES = [0.0, 2 ** -0.5, 1.0]
# BACKLOG 99. Duplicated from equipop/doors/rungs.py and pinned by
# test_rungs.py, for the reason given above - a door may not import
# the package to learn what its own dropdowns say.
OVERSHOOT_MODES = [
    "whole ring - every cell at that distance",
    "proportional share - the same fraction of each cell",
    "sampled, seeded - whole cells, one at a time",
]
OVERSHOOT_VALUES = ["whole", "proportional", "sampled"]

import numpy as np

from .base import EquipopAlgorithm


class CountsAndShares(EquipopAlgorithm):

    EQP_TOOL = "CountsShares"
    OUT = "outfc"

    def name(self):
        return "countsandshares"

    # WRITTEN DOWN, NOT IMPORTED. displayName runs while QGIS
    # builds the toolbox, so importing the package here would
    # kill the whole plugin when equipop is missing - BACKLOG
    # 218, reintroduced and caught the same day. A test pins
    # this against doors/help.LABELS so it cannot drift.
    EQP_LABEL = "1. Counts and Shares (k / radius / decay)"

    def displayName(self):
        return self.EQP_LABEL

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
        # BACKLOG 104: 2a used to be the type field, which serves
        # RUNG 2, while the rung-1 box sat last as 2d. Pick rung 1 and
        # the box you needed was behind three that did not apply.
        # The PARAMETER NAMES are unchanged, so saved models and
        # scripts keep working - only the labels moved.
        self.add(QgsProcessingParameterField(
            "treat", "2a \u25b8 ...group count fields - one column "
            "per group, holding TOTALS, never averages",
            parentLayerParameterName="layer",
            type=QgsProcessingParameterField.Numeric,
            allowMultiple=True, optional=True))
        self.add(QgsProcessingParameterField(
            "treatcatfield", "2b \u25b8 ...type field for the groups "
            "(usually the same column - choose it here too)",
            parentLayerParameterName="layer", optional=True))
        self.add(QgsProcessingParameterMatrix(
            "treattable", "2c \u25b8 ...groups: one row per type - "
            "the type, and the group name it joins",
            headers=["Type", "Group name"], optional=True))
        self.add(QgsProcessingParameterString(
            "restgroup", "2d \u25b8 ...name a group for every OTHER "
            "type (optional; for example: other)", optional=True))

        self.add(QgsProcessingParameterString(
            "k", "3 \u25b8 k - neighbourhood sizes in people, space "
            "separated", defaultValue="400", optional=True))
        self.add(QgsProcessingParameterString(
            "r", "3a \u25b8 ...or radii in metres, space separated",
            optional=True))

        self.add(QgsProcessingParameterEnum(
            "model", "4 \u25b8 distance decay",
            options=_decay_choices(), defaultValue=0))
        self.add(QgsProcessingParameterNumber(
            "halflife", "4a \u25b8 ...half-life in metres (the "
            "distance at which weight halves)", defaultValue=0.0,
            optional=True,
            type=QgsProcessingParameterNumber.Double))

        # --- barriers and terrain: distance becomes EFFORT ---------
        # The whole block goes into QGIS's Advanced area (v1.28,
        # John): six boxes that most runs never touch, and the
        # largest single source of clutter in a flat list. The help
        # panel says where they went, because unlike Pro's collapsed
        # section - which still shows its name - Advanced does not
        # advertise what is inside, and a student would never
        # discover the effort engine exists.
        self.add(QgsProcessingParameterFeatureSource(
            "barrier", "5 \u25b8 barrier layer - a river, railway or "
            "lake that costs effort to cross (optional)",
            [QgsProcessing.TypeVectorAnyGeometry], optional=True),
            advanced=True)
        self.add(QgsProcessingParameterField(
            "barrierfield", "5a \u25b8 ...its friction field - the "
            "crossing cost in rounds (positive deters, negative "
            "carries: 3 is a river, -0.9 a motorway)",
            parentLayerParameterName="barrier", optional=True),
            advanced=True)
        self.add(QgsProcessingParameterRasterLayer(
            "barrierraster", "5b \u25b8 ...or a friction RASTER "
            "(cost per cell; NoData or zero = free)", optional=True),
            advanced=True)
        self.add(QgsProcessingParameterRasterLayer(
            "dem", "5c \u25b8 ...and/or an elevation raster, so "
            "SLOPE costs effort", optional=True), advanced=True)
        self.add(QgsProcessingParameterString(
            "tau", "5d \u25b8 effort budgets, space separated - how "
            "many rounds each person may spend (gives N_tau columns)",
            optional=True), advanced=True)
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
            "unit", "Cell size in map units, whole numbers only - "
            "bigger cells mean fewer origins and faster runs", defaultValue=100.0,
            type=QgsProcessingParameterNumber.Double), advanced=True)
        # BACKLOG 141: a three-way choice, not a free number. The
        # wording is duplicated from equipop/doors/rungs.py and
        # pinned by test_rungs.py - see the note above on 105/78 for
        # why it cannot be imported.
        self.add(QgsProcessingParameterEnum(
            "selfpot", "Self-potential - the distance to what is "
            "LOCAL, inside your own cell", options=SELFPOT_MODES,
            defaultValue=2), advanced=True)
        # BACKLOG 99. Defaults to PROPORTIONAL, which is the engine's
        # default from 1.30 - so a door that says nothing and a door
        # that says 'proportional' agree, and the box reports the
        # truth rather than a second opinion.
        self.add(QgsProcessingParameterEnum(
            "overshoot", "The ring that crosses k", 
            options=OVERSHOOT_MODES, defaultValue=1), advanced=True)
        # BACKLOG 99. The seed used to matter only to permutations,
        # so QGIS never offered it; under 'sampled' it DECIDES THE
        # ANSWER, which makes it an analytical box by door_parity's
        # own rule. Empty means one is drawn and printed.
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
        from .base import check_versions
        check_versions(ch)
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
        treats = self.parameterAsStrings(parameters, "treat", context)

        from equipop.doors.decaynames import (curve_in_plain_numbers,
                                               model_from_choice)
        model = model_from_choice(_decay_choices()[
            (self.parameterAsEnums(parameters, "model", context)
             or [0])[0]])
        half = self.parameterAsDouble(parameters, "halflife", context)
        decaying = model is not None and half > 0

        names = predict_result_fields(
            "counts", k_text, r_text, "", treats, [], [],
            decaying=decaying, efforting=False)
        self.check_target(parameters, names, feedback)

        with stage(ch, "reading input"):
            pts = self.read_points(
                source, feedback,
                (self.parameterAsStrings(parameters, "xfield", context)
                 or [None])[0],
                (self.parameterAsStrings(parameters, "yfield", context)
                 or [None])[0])

        # BACKLOG 99. The mode is passed EXPLICITLY, never left to
        # the engine's default: a door that says nothing cannot be
        # conformance-checked against a named mode, which is the
        # whole reason both doors failed the answer key in 1.30.
        overshoot_mode = OVERSHOOT_VALUES[
            (self.parameterAsEnums(parameters, "overshoot",
                                   context) or [1])[0]]
        seed = self.optional_int(parameters, "seed")
        kw = dict(unit_size=float(unit), treat_are_counts=True,
                  overshoot_mode=overshoot_mode, seed=seed,
                  self_potential=SELFPOT_VALUES[
                      (self.parameterAsEnums(parameters, "selfpot",
                                             context) or [2])[0]])
        if decaying:
            kw["decay_model"] = model
            kw["half_life_m"] = float(half)
            eps = self.parameterAsDouble(parameters, "decayeps",
                                         context)
            kw["decay_eps"] = float(eps) if eps > 0 else 1e-6
            ch.info(curve_in_plain_numbers(model, half))
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
        catfield = (self.parameterAsStrings(parameters, "catfield",
                                           context) or [None])[0]
        # v1.29.3, BACKLOG 85. The two ladders are INDEPENDENT - that
        # is what separating reference from treatment was for in
        # 1.22.0 - but this whole block used to be nested inside
        # `refmode == 2`, so choosing "every point counts as one" for
        # the REFERENCE silently switched the TREATMENT grouping off.
        # John, field, 3.42.1: refmode=0 with treatmode=2 produced
        # N_223 and Dist_223 and nothing else, with no message at
        # all. Pro was always right - it hands both modes to the
        # shared engine and lets _run_tool decide; QGIS reimplemented
        # the logic locally and coupled them.
        treatmode = (self.parameterAsEnums(parameters, "treatmode",
                                           context) or [0])[0]
        from .base import matrix_cells
        pop_vals = [c for c in matrix_cells(self, parameters,
                                            "reftable", context) if c]

        # ------------------------------------------------ BACKLOG 104
        # A ladder whose rungs read different boxes, in a dialog that
        # cannot grey the others out, must SAY when a box is being
        # ignored and REFUSE when the box a rung needs is empty. Only
        # the reftable case below was ever written; John lost a field
        # run to the treatment half in 1.29.5.
        from equipop.doors import rungs
        rest_txt = self.parameterAsString(parameters, "restgroup",
                                          context).strip()
        tcat = (self.parameterAsStrings(parameters, "treatcatfield",
                                        context) or [None])[0]
        tmat = [c for c in matrix_cells(self, parameters, "treattable",
                                        context) if c]

        if refmode == 1 and not pop:
            raise QgsProcessingException(rungs.missing(
                "box 1a, the count field", "the reference population",
                REF_MODES[1]))
        if refmode == 2 and not catfield:
            raise QgsProcessingException(rungs.missing(
                "box 1b, the type field", "the reference population",
                REF_MODES[2]))
        if catfield and refmode != 2:
            ch.info(rungs.ignored("Box 1b, the type field",
                                  "the reference population",
                                  REF_MODES[refmode]))
        if pop_vals and refmode != 2:
            ch.info(rungs.ignored("Box 1c, the list of reference types",
                                  "the reference population",
                                  REF_MODES[refmode]))
            pop_vals = []

        # BACKLOG 144: refuse names that differ only in case
        # BEFORE computing - GIS field names ignore case, so they
        # cannot both become columns and the write dies eight
        # seconds in.
        from equipop.doors.fields import refuse_case_clashes
        try:
            refuse_case_clashes(
                [r for r in tmat[1::2] if r] + ([rest_txt] if rest_txt
                                                else []),
                "Two group names")
            refuse_case_clashes(treats, "Two group count fields")
        except ValueError as e:
            raise QgsProcessingException(str(e))

        if treatmode == 1 and not treats:
            raise QgsProcessingException(rungs.missing(
                "box 2a, the group count fields",
                "the treatment population", TREAT_MODES[1]))
        if treatmode == 2 and not (tcat or catfield):
            raise QgsProcessingException(rungs.missing(
                "box 2b, the type field for the groups (or box 1b, "
                "which it falls back to)",
                "the treatment population", TREAT_MODES[2]))
        if treatmode != 2:
            for box, filled in (("Box 2b, the type field for the groups",
                                 bool(tcat)),
                                ("Box 2c, the group table", bool(tmat)),
                                ("Box 2d, the name for every other type",
                                 bool(rest_txt))):
                if filled:
                    ch.info(rungs.ignored(box,
                                          "the treatment population",
                                          TREAT_MODES[treatmode]))
        if treats and treatmode == 0:
            # honoured anyway, and saying so beats silently dropping
            # the columns that saved models already depend on
            ch.info(rungs.working_anyway(
                "Box 2a, the group count fields",
                "the treatment population", TREAT_MODES[0],
                TREAT_MODES[1]))

        restricting = refmode == 2 and bool(catfield)
        grouping = treatmode == 2
        if restricting or grouping:
            from equipop.categorical import categories_to_binary
            groups = self._groups_from_matrix(
                matrix_cells(self, parameters, "treattable",
                             context)) if grouping else {}
            tcatf = (self.parameterAsStrings(parameters,
                                            "treatcatfield", context)
                     or [None])[0] or catfield
            rest = self.parameterAsString(parameters, "restgroup",
                                          context).strip()
            pop_mask = (categories_to_binary(
                pts.data[catfield], {},
                pop_values=pop_vals or None)[0] if restricting
                else np.ones(pts.n, bool))
            cat_treats = {}
            if grouping:
                if not tcatf:
                    raise QgsProcessingException(
                        "The treatment ladder is on 'types from a "
                        "type field, grouped', but no type field was "
                        "given (box 2a).")
                _, cat_treats = categories_to_binary(
                    pts.data[tcatf], groups,
                    pop_values=pop_vals or None,
                    rest_group=rest or None, rest_in_population=None)
                if not cat_treats:
                    raise QgsProcessingException(
                        "The treatment ladder is on 'types from a "
                        "type field, grouped', but no groups came "
                        f"out of '{tcatf}'. Box 2b needs one row per "
                        "type, with the group name beside it - "
                        "otherwise there is nothing to count and the "
                        "run would produce distances only.")
            tvf = pop
            if cat_treats and tvf:
                tcol = np.nan_to_num(pts.data[tvf].astype(float))
                cat_treats = {g: v * tcol
                              for g, v in cat_treats.items()}
                ch.info(self._units_note(tvf, pop))
            elif cat_treats:
                ch.info("No value field given, so every row counts as "
                        "one: the shares are shares of PLACES.")
            if cat_treats:
                kw.setdefault("treat", {}).update(cat_treats)
            outside = int((~pop_mask).sum()) if restricting else 0
            # one definition of "how many people is this row", used by
            # BOTH keepoutside routes (BACKLOG 108)
            base = (pts.data[pop].astype(float) if pop
                    else np.ones(pts.n))
            if (self.parameterAsEnums(parameters, "keepoutside",
                                      context) or [0])[0] == 0:
                # John's rule: outside the reference population means
                # zero people - nobody's neighbour - but the row
                # still gets its own results.
                kw["weight"] = np.nan_to_num(base) * pop_mask
                if outside:
                    ch.info(f"{outside} row(s) are outside the "
                            "reference population: they count as "
                            "zero people, but still get their own "
                            "results.")
            else:
                # BACKLOG 108. This used to be `pop_mask.astype(float)`
                # - the MASK, not the count - so every included row
                # counted as ONE and the population field was thrown
                # away, silently. Two included rows carrying 10 and 1
                # people gave N_5 = 2 here and 11 on the branch above.
                # Entered in 1.21, published from 1.21 to 1.29.3.
                # alg_stats.py had it right all along, which is what
                # BACKLOG 120 is about: the logic is duplicated.
                kw["weight"] = np.nan_to_num(base) * pop_mask
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
            field = (self.parameterAsStrings(parameters, "barrierfield",
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
