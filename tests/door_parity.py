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
        "decayeps", "xfield", "yfield"}

# machine 2 - Value Statistics (list added v1.29). `pop` is the
# reference population; `values` the treatment fields measured over
# it. No ladder here yet - that is a later release, deliberately.
CORE_M2 = {"layer", "xfield", "yfield", "pop", "values", "measures",
           "pcts", "k", "r", "unit"}
