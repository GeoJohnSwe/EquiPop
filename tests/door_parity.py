# -*- coding: utf-8 -*-
"""door_parity.py - the boxes both GIS doors must offer, named once.

Why this file exists (v1.29). The both-ways parity check added in
1.25 lived inside the QGIS test and covered MACHINE 1 only. Machine 2
was checked for one thing only - that every box had some help text -
which passes happily when the two doors call the SAME box by
DIFFERENT names. And they did: Pro's Value Statistics said `fullpop`
where QGIS said `pop`, from 1.20.0 until 1.29, and the shared help
carried both entries with different words. Nothing objected, which is
this project's oldest failure.

So the list lives here, outside either door, and BOTH doors are
checked against it. A list kept inside one door's test can only ever
say what that door already does.

These are the ANALYTICAL boxes - what the tool asks about the world.
Output plumbing (where results go, what to do with existing columns,
shortened names) is host-specific by design and deliberately absent:
Pro writes to a feature class or a table, QGIS to a sink.
"""

# machine 1 - Counts and Shares (list added v1.25)
CORE = {"layer", "pop", "treat", "k", "r", "unit", "catfield",
        "reftable", "treattable", "restgroup", "refmode", "treatmode",
        "treatcatfield", "keepoutside", "model", "halflife",
        "decayeps", "xfield", "yfield",
        # v1.29.5, BACKLOG 95 - an ENGINE parameter, so both doors
        "selfpot"}

# machine 2 - Value Statistics (list added v1.29). `pop` is the
# reference population; `values` the treatment fields measured over
# it. No ladder here yet - that is a later release, deliberately.
CORE_M2 = {"layer", "xfield", "yfield", "pop", "values", "measures",
           "pcts", "k", "r", "unit",
           # v1.29.2, the ladder: machine 2 can now restrict WHO is
           # around, the same three rungs and the same words as
           # machine 1. Reference side only - the treatment here is a
           # set of numbers, so there is nothing to choose.
           "refmode", "catfield", "reftable", "keepoutside",
           "selfpot"}


# v1.29.3, BACKLOG 86: parity of BEHAVIOUR, not just of names.
#
# The lists above ask whether both doors offer the same boxes. They
# cannot ask whether the same boxes DO the same thing, and that is
# how BACKLOG 85 survived: QGIS nested the treatment ladder inside
# the reference ladder, so both doors offered `treatmode` and only
# one of them honoured it. Names agreed perfectly while the answers
# differed - silently, with no message and two columns missing.
#
# Each case is a set of dialog choices that must give the SAME
# result columns through either door. Add a case whenever a rung,
# mode or switch is added; a combination nobody lists is a
# combination nobody checks.
LADDER_CASES = [
    ("plain counts", dict(refmode=0, treatmode=0), {"N", "Dist"}),
    ("groups, reference on rung 1",
     dict(refmode=0, treatmode=2, treatcatfield="fclass",
          treattable=["bar", "social"]),
     {"N", "Dist", "T_social", "R_social"}),
    ("groups, reference on rung 2",
     dict(refmode=1, pop="Population", treatmode=2,
          treatcatfield="fclass", treattable=["bar", "social"]),
     {"N", "Dist", "T_social", "R_social"}),
    ("groups, reference on rung 3",
     dict(refmode=2, catfield="fclass", reftable=["cafe", "bar"],
          treatmode=2, treatcatfield="fclass",
          treattable=["bar", "social"]),
     {"N", "Dist", "T_social", "R_social"}),
]
