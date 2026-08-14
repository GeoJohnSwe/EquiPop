"""
rungs.py - one wording, every door, for the commonest way a run
quietly does nothing.

THE PROBLEM. Boxes 1 and 2 are LADDERS: each rung reads a different
box below it. Pro can grey out the boxes a rung does not use; QGIS
Processing cannot. So in QGIS a box that belongs to another rung sits
there looking perfectly fillable, and filling it does nothing at all.

John, in the field on 1.29.5, chose treatment rung 1 ("one column per
group, counts inside") and filled box 2a, which served rung 2. The run
produced N_100 and Dist_100, no T_, no R_, and NO MESSAGE. The boxes
had been ordered by letter rather than by rung, so the box he needed
was LAST, behind three that did not apply. (BACKLOG 104.)

Three things answer it, and this module is the third:
  1. the rung's own text names the box it needs - "(fill 2a)";
  2. the boxes are ordered so each rung's boxes follow it;
  3. and when a box is filled that the current rung ignores, or a
     rung's box is left empty, SOMETHING IS SAID.

The wording lives here so the two doors cannot describe the same
mistake in two different ways - the same reason HELP does.
"""

CANNOT_GREY = ("QGIS cannot grey a box out the way Pro does, so this "
               "notice is the only warning you get.")


def ignored(box: str, chooser: str, rung: str) -> str:
    """A box is filled that the chosen rung does not read."""
    return (f"{box} is filled, but {chooser} is on '{rung}', which "
            f"does not read it - the box is IGNORED. {CANNOT_GREY}")


def missing(box: str, chooser: str, rung: str) -> str:
    """A rung was chosen but the box it needs is empty. This is
    refused rather than warned: a run that cannot answer the question
    asked of it should not quietly answer a different one."""
    return (f"{chooser} is on '{rung}', which needs {box} - but that "
            "box is empty. Fill it, or choose a different rung.")


def working_anyway(box: str, chooser: str, rung: str, instead: str) -> str:
    """A box is filled that the chosen rung does not claim, but the
    engine honours it regardless. Say so rather than change it: saved
    models rely on the current behaviour, and silently dropping their
    columns would be a worse fault than the untidiness."""
    return (f"{box} is filled while {chooser} is on '{rung}'. It IS "
            f"being used, and you will get results from it - but "
            f"choose '{instead}' to say so plainly.")


# ===================================================================
# THE LADDER WORDING ITSELF (BACKLOG 105).
#
# Until 1.29.5 each door kept its own copy of these lists. They had
# already drifted - Pro said "additive (sum)" where QGIS said
# "additive (costs add up)", and QGIS offered six statistics where Pro
# offered twelve (BACKLOG 103). Nothing objected, because
# door_parity.py compares the NAMES of boxes and both doors have a box
# called "measures". A test comparing two hand-maintained lists would
# only have detected the drift; keeping ONE list removes it.
#
# QGIS adds "(fill 2a)" hints on top, because QGIS Processing cannot
# grey a box out and Pro can. That is the ONLY difference either door
# is allowed to introduce, and with_hints() is the only way to do it.
# ===================================================================

REFERENCE = ["every point counts as one",
             "a field holds the count",
             "only selected types, with a count field"]

TREATMENT = ["not measuring one - distances and counts only",
             "one column per group, counts inside",
             "types from a type field, grouped"]

OUTSIDE = ["give them results, counting as zero",
           "leave their results Null"]

# "costs add up" rather than Pro's old "(sum)": these are EFFORT
# costs, and a reader who has not met the effort engine needs the
# longer words more than a reader who has needs the shorter ones.
AGGREGATION = ["additive (costs add up)", "max", "min", "mean"]

# The engine computes all of these (equipop/stats.py). Percentiles are
# not here: both doors take them as free text in their own box, and
# Pro additionally lists "percentiles" as a toggle for that box.
MEASURES = ["mean", "median", "gini", "sd", "variance", "se",
            "min", "max", "count", "sum", "range"]

# One name for the user, one for the engine, mapped in one place.
MEASURE_KEY = {"variance": "var"}


def with_hints(modes: list[str], hints: dict[int, str]) -> list[str]:
    """QGIS only: name the box each rung reads.

    Pro greys out the boxes a rung does not use, so it needs no hint
    and must not carry one - the hint names a QGIS box letter, which
    means nothing in Pro's sectioned dialog.
    """
    return [f"{m} ({hints[i]})" if i in hints else m
            for i, m in enumerate(modes)]


# BACKLOG 141. Self-potential was a free-text number from 0 to 1.
# John: "we don't need a textbox where erronous values could be
# entered". A three-way choice removes the decision without discarding
# 0.71, the MEDIAN, which was his own suggestion in the design round.
#
# Safe to change now and not later: 1.29.5 was never published, so no
# saved model anywhere holds selfpot as a number. After a release, a
# stored 1.0 would silently be reread as choice index 1 - the median -
# which is the class of failure this project exists to end.
#
# The ENGINE parameter stays a float, so the Python and Stata routes
# keep the full range and selfpot.check() still guards them.
SELF_POTENTIAL = [
    "0 - no distance at all; Dist_k can come out as zero",
    "0.71 - the median: half of what your cell holds is nearer than this",
    "1 - the radius at which k of it is reached (recommended)",
]
SELF_POTENTIAL_VALUES = [0.0, 2 ** -0.5, 1.0]
SELF_POTENTIAL_DEFAULT = 2          # the equal-area radius


# ===================================================================
# BACKLOG 99. THE OVERSHOOT - the ring that crosses k.
#
# The reasoning, the measurements and the three modes live in
# equipop/overshoot.py; this is only what the DIALOGS say, kept here
# for the same reason every other menu is (105/78): neither door may
# import the package to find out what its own dropdowns read, so the
# duplication is pinned by test_rungs.py instead of removed.
#
# The labels name the mode FIRST, in the engine's own word, because
# that word is what the run message, the manifest and the manual all
# use. A user who reads "proportional share" in a message must be
# able to find it in the box without translating.
#
# TWO DEFAULTS, and the difference is not an oversight.
# Machine 1 defaults to `proportional` - John's ruling, 1.30, and the
# whole point of the item. Machine 2 defaults to `whole`, because a
# quarter of a cell has no median, no percentile and no Gini: the
# core REFUSES proportional there until weighted statistics land
# (BACKLOG 118). Machine 2 still OFFERS all three, so the choice is
# visible and starts working by itself when 118 lands, and so that
# picking it gets the core's refusal - which names 118 - rather than
# an absence that explains nothing.
# ===================================================================

OVERSHOOT = [
    "whole ring - every cell at that distance",
    "proportional share - the same fraction of each cell",
    "sampled, seeded - whole cells, one at a time",
]
#: The engine's own words, in the same order. These are what reach
#: run_knn / run_knn_counts / run_knn_stats as `overshoot_mode`.
OVERSHOOT_VALUES = ["whole", "proportional", "sampled"]
OVERSHOOT_DEFAULT = 1               # proportional - BOTH machines
# v1.31, BACKLOG 118: machine 2 used to default to `whole`
# because a quarter of a cell had no median. It has one now -
# weighted statistics compute from (value, weight) pairs - so
# the two machines agree again and this alias exists only so
# that a door which asks for the machine-2 default still gets
# an answer. If they ever diverge again it should be for a new
# reason, recorded here.
OVERSHOOT_DEFAULT_M2 = OVERSHOOT_DEFAULT


def overshoot_note(mode: str) -> str:
    """RETIRED in v1.31 and kept as a stub on purpose.

    BACKLOG 118 removed the reason for it: machine 2 can take a
    fraction of a cell now, so both machines share one default and
    there is no divergence to warn about. The function stays so that
    an older door - a saved Pro toolbox, a plugin somebody has not
    updated - calls something harmless rather than dying on an
    AttributeError. It returns nothing, and the doors no longer call
    it.
    """
    return ""


# ===================================================================
# BACKLOG 155 + 160. Cell size is a WHOLE NUMBER OF MAP UNITS.
#
# 155: fractional sizes were accepted and then rounded differently by
# each module - ask for 2.5 and the centres came out 1, 3, 6, spacings
# of 2 and 3. build_cells casts centres to int; analysis, friction,
# slope, access and fca each take int(unit_size) separately. Six
# modules would have to agree forever. John ruled: whole values.
#
# 160: but NOT whole METRES, which is what every label said. John:
# "I hope we are not forcing the cells to a metric only specificity -
# for me it could be any kind of metrics (as long as we don't do
# decimals)." He is right, and it was worse than a naming preference:
# nothing anywhere ever read the projected CRS's LINEAR UNIT. The only
# check is `type == "Geographic"`, so a US State Plane layer in survey
# feet passes every test and is then told its cell size and its Dist_k
# are in metres - wrong by 3.28.
#
# The engine is linear-unit agnostic and always was. Only the LABELS
# claimed otherwise. So: say the unit the working CRS actually uses,
# and never warn about it - John, 1.29.7: "no need to warn - the users
# will understand."
# ===================================================================

def unit_name(crs_unit: str | None) -> str:
    """A readable name for the working CRS's linear unit."""
    u = str(crs_unit or "").strip().lower()
    if not u:
        return "map units"
    if u.startswith("met") or u in {"m", "metre", "meter"}:
        return "metres"
    if "foot" in u or "feet" in u or u in {"ft", "ftus", "us_ft"}:
        return "US survey feet" if "us" in u or "survey" in u else "feet"
    return str(crs_unit)


def cell_size_label(crs_unit: str | None = None) -> str:
    """The cell-size box label, naming the real unit."""
    return (f"Cell size in {unit_name(crs_unit)} - bigger cells mean "
            "fewer origins and faster runs (whole numbers only)")


def check_cell_size(value, crs_unit: str | None = None) -> float:
    """Whole map units, greater than zero. Refuses rather than
    rounding, because six modules round differently (155)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"cell size must be a number, got {value!r}")
    if not v > 0:
        raise ValueError(
            f"Cell size must be greater than 0 {unit_name(crs_unit)}; "
            f"got {v:g}. It is the grid the neighbourhoods are built "
            "on, so there is no sensible zero.")
    if abs(v - round(v)) > 1e-9:
        raise ValueError(
            f"Cell size must be a WHOLE number of "
            f"{unit_name(crs_unit)}; got {v:g}. Fractional sizes are "
            "rounded differently by different parts of EquiPop - "
            f"{v:g} would give cells of uneven width - so they are "
            "refused rather than silently changed.")
    return float(round(v))
