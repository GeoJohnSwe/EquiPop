# -*- coding: utf-8 -*-
"""reachability.py - WHAT CAN A PERSON ACTUALLY REACH, AND FROM WHERE?

John's request, session 12, after five things were found in one
session that were built, tested, and reachable by nobody:

    inventory.py         shipped 1.45.0, no door of any kind
    vectorjoin.py        only from a script the sdist did not carry
    RunLog (meta.py)     backlog item 2, called by nothing
    the Pro help sidecars  generated, tested, never shipped
    make_help_xml.py     shipped since 1.44.4, could not run where

EVERY ONE PASSED ITS TESTS. The suite asked whether the thing worked
and never whether anyone could get to it. This file asks the second
question.

WHY IT IS DECLARED RATHER THAN DERIVED. The first attempt grepped
each door for the engine function it calls. It was wrong in BOTH
directions: it reported machine 1 as absent from QGIS and Pro,
because both reach it through `stata_bridge.dispatch` rather than by
name, and it reported the lattice join as present in QGIS because
`alg_continental.py` imports `join_to_points` for something else
entirely. A matrix that guesses is worse than none - it would have
said the doors were fine.

So the truth is WRITTEN DOWN HERE and the test CHECKS THE WRITING:
every piece of evidence must still exist in the file it names, and
every module in the package must appear somewhere below. A new
capability cannot be added without either naming its doors or
recording, in words, why it has none.

THE HONEST PART IS `NO_DOOR`. It is not a failure state. Plenty of
things legitimately have no GUI - John ruled in session 12 that
machine 2 needs no Stata door because Stata does weighted statistics
natively and better. What is NOT allowed is silence. Each NO_DOOR
carries a reason and, where one exists, a backlog number.
"""

#: A door the capability can be reached from, and the proof.
#: (file, symbol) - the test fails if the symbol leaves the file, so
#: the matrix cannot quietly go stale the way the priority list did.
def door(path, symbol):
    return ("door", path, symbol)


#: No door, on purpose or not yet. `why` is prose, `item` is the
#: backlog number if one exists.
def no_door(why, item=None):
    return ("none", why, item)


def same_as(other_door, extra=""):
    """No door, for the SAME reason another door has none.

    Written as a reference the test RESOLVES, not as the words "As
    QGIS" - which is what the first draft used and which tells a
    future session nothing it can act on. The resolved reason is what
    gets checked, so a cross-reference cannot be a way of writing
    less than a reason.
    """
    return ("same", other_door, extra)


PYTHON = door("equipop/__init__.py", "__all__")

#: The three GUI/command doors all funnel through one dispatcher, so
#: naming it is the honest evidence for machines 1 and 2 - a test
#: that looked for `run_knn_counts` in alg_counts.py would find
#: nothing and be wrong.
DISPATCH = "equipop/stata_bridge.py"

MATRIX = {
    # ---------------------------------------------------- the machines
    "machine 1 - counts and shares": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_counts.py", "dispatch"),
        "pro": door("arcgis/EquiPop.pyt", "dispatch"),
        "stata": door("stata/equipop.ado", "knn_to_rows"),
    },
    "machine 2 - value statistics": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_stats.py", "dispatch"),
        "pro": door("arcgis/EquiPop.pyt", "ValueStatistics"),
        "stata": no_door(
            "RULED OUT by John, session 12. Stata computes weighted "
            "means, medians, percentiles and Ginis natively and "
            "better than we would; what it cannot do is BUILD THE "
            "NEIGHBOURHOOD. So EquiPop hands Stata the neighbourhood "
            "and Stata does the statistics on it. Each tool does the "
            "part it is good at. Reopens if a measure appears that "
            "Stata cannot express over a k-neighbourhood.", 205),
    },
    "machine 3 - continental rasters": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_continental.py", "run_folder"),
        "pro": door("arcgis/EquiPop.pyt", "ContinentalRasters"),
        "stata": no_door(
            "A continental raster run writes a feature class and is "
            "measured in hours; Stata is not where anyone would "
            "start one. No demand recorded."),
    },
    "machine 4 - spatial demography": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_demography.py", "demography"),
        "pro": door("arcgis/EquiPop.pyt", "SpatialDemography"),
        "stata": no_door(
            "As machine 3: a demographic raster run writes a feature "
            "class and is measured in hours. Stata is not where "
            "anyone would start one, and no demand is recorded."),
    },
    "machine 5 - fetching": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_fetch.py", "plan_fetch"),
        "pro": no_door(
            "Pro has four machines and this is not one of them. The "
            "gap is real and known; it widens every release that "
            "adds a provider.", 288),
        "stata": no_door("Downloading is not a Stata activity."),
        "runner": door("run_fetch.py", "plan_fetch"),
    },

    # ------------------------------------------- distance ingredients
    "friction and barriers": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_counts.py", "barrier"),
        "pro": door("arcgis/EquiPop.pyt", "barrier"),
        "stata": no_door(
            "RULED OUT by John, session 12: \"those are GIS features, "
            "and not needed in statistics\". Barriers and terrain are "
            "about how a landscape is crossed, which is a question "
            "you ask of a map and not of a dataset in memory. The "
            "BRIDGE can do it - stata_bridge takes engine='friction' "
            "with a friction_file - so this is a door deliberately "
            "not built, not a capability missing.", 296),
    },
    "slope and terrain": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_counts.py", "dem"),
        "pro": door("arcgis/EquiPop.pyt", "dem"),
        "stata": no_door(
            "RULED OUT with friction, session 12, for the same "
            "reason: a DEM is a GIS input and a walking model is a "
            "statement about terrain, neither of which belongs in a "
            "statistics package. stata_bridge takes engine='slope' "
            "and the Stata command deliberately does not.", 296),
    },
    "distance decay": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_counts.py", "decay"),
        "pro": door("arcgis/EquiPop.pyt", "decay"),
        "stata": door("stata/equipop.ado", "decay"),
    },

    # ------------------------------------------------ the settings
    "overshoot - the ring that crosses k": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_counts.py", "overshoot"),
        "pro": door("arcgis/EquiPop.pyt", "overshoot"),
        "stata": door("stata/equipop.ado", "OVERshoot"),
    },
    "self-potential": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_counts.py", "selfpot"),
        "pro": door("arcgis/EquiPop.pyt", "selfpot"),
        "stata": door("stata/equipop.ado", "SELFpot"),
    },
    "origin rule - is a place its own neighbour": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_counts.py", "originrule"),
        "pro": door("arcgis/EquiPop.pyt", "originrule"),
        "stata": door("stata/equipop.ado", "ORIGINrule"),
    },

    # ------------------------------------- built, and hard to get to
    "folder inventory": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_inventory.py", "inventory"),
        "pro": door("arcgis/EquiPop.pyt", "FolderInventory"),
        "stata": no_door(
            "Reading a folder of GIS files to see which share a "
            "lattice is a GIS question, and the same reasoning that "
            "closed 296 applies. The JSON it writes is plain text "
            "that Stata can read if anyone ever needs to.", 269),
    },
    "vector to lattice join (OSM roads, polygons)": {
        "python": PYTHON,
        "qgis": no_door(
            "The headline engine of 1.46.0 and 1.46.1 has no GUI. "
            "Reachable only from run_osm_friction.py - which the "
            "source archive did not carry until 1.47.0, so for two "
            "releases it was reachable by nobody at all.", 283),
        "pro": same_as("qgis"),
        "stata": same_as("qgis"),
        "runner": door("run_osm_friction.py", "lines_to_cells"),
    },
    "run provenance": {
        "python": no_door(
            "RunLog exists in meta.py, is exported in __all__, and is "
            "called by nothing and tested by nothing. It is BACKLOG "
            "ITEM 2.", 293),
        "qgis": no_door(
            "QGIS writes no record of the settings a run used, "
            "though it has an output to sit beside exactly as Pro "
            "does. Pro's field list is the specification.", 293),
        "pro": door("arcgis/EquiPop.pyt", "_EquiPop_run.csv"),
        "stata": no_door(
            "Nothing recorded. John's ruling, session 12: a PRINTED "
            "NOTE rather than a sidecar, because a Stata run writes "
            "variables into memory and may produce no file at all - "
            "and because `log using` is where a Stata user's "
            "reproducibility already lives. Values to be returned in "
            "r() as well, so a do-file can check them rather than a "
            "human reading the log.", 293),
    },

    # --------------------------------- library work, no door expected
    "segregation profile": {
        "python": PYTHON,
        "qgis": no_door(
            "A profile is a curve over many k, not a column on a "
            "layer, so a GIS dialog is the wrong shape for it. The "
            "doors already produce the R_ columns it is computed "
            "from, and Stata or Python draws the curve."),
        "pro": same_as("qgis"),
        "stata": same_as("qgis", "and Stata draws curves well"),
    },
    "spatial autocorrelation": {
        "python": PYTHON,
        "qgis": no_door(
            "Moran's I and Getis-Ord over an EquiPop neighbourhood. "
            "No GUI demand recorded; the Tartu work drives it from "
            "Python and Stata."),
        "pro": same_as("qgis"),
        "stata": door("stata/equipop.ado", "knn_to_rows"),
    },
    "accessibility and FCA": {
        "python": PYTHON,
        "qgis": no_door("No door. No demand recorded."),
        "pro": no_door("No door. No demand recorded."),
        "stata": no_door("No door. No demand recorded."),
    },
    "hex cells": {
        "python": PYTHON,
        "qgis": no_door(
            "Square cells only at every door. Hex exists in the "
            "package and its self-potential uses a SQUARE cell's "
            "area, overstating the radius by 7.5% - so it should not "
            "be offered at a door until that is fixed.", 158),
        "pro": same_as("qgis"),
        "stata": same_as("qgis"),
    },
    "tiled, resumable big runs": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_continental.py", "tiles"),
        "pro": door("arcgis/EquiPop.pyt", "tiles"),
        "stata": no_door("Machine 3 has no Stata door either."),
    },
    "diagnostics (the doctor)": {
        "python": PYTHON,
        "qgis": no_door(
            "A user whose QGIS door is broken cannot run the thing "
            "that would say why. Same in Pro.", 128),
        "pro": same_as("qgis"),
        "stata": door("stata/equipop.ado", "setup"),
    },
}

#: Doors a capability may name. `runner` is a script at the
#: repository root and is a WEAKER door than a dialog - it requires
#: Python, and it does not appear in any menu.
DOORS = ("python", "qgis", "pro", "stata", "runner")

#: Modules that are internal machinery rather than a capability a
#: person would ask for. Listed so the completeness check can tell
#: "not a capability" from "a capability nobody declared".
INTERNAL = {
    "analysis", "fastcounts", "cells", "stats", "wstats", "overshoot",
    "selfpot", "selfrule", "decay", "categorical", "projection",
    "transform", "utm", "io", "raster", "rasterfolder", "latticejoin",
    "friction", "slope", "stata_bridge", "meta", "gridby", "datasets",
    "area", "viz", "doctor", "fetch", "segregation", "autocorr",
    "access", "fca", "hex", "bigrun", "vectorjoin", "inventory",
    "doors.help", "doors.report", "doors.fields", "doors.loader",
    "doors.rungs", "doors.registry", "doors.reference",
    "doors.decaynames", "doors.demography", "doors.continental",
    "doors.fetching", "doors.inventory",
}
