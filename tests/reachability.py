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


#: BACKLOG 333. A RULING. No door, on purpose, by a decision - John's
#: or a structural one. There is nothing to watch, so nothing is
#: checked beyond the reason being worth reading.
def ruled_out(why, item=None):
    return ("none", why, item, None)


#: BACKLOG 333. A GAP. No door YET, and `absent` is the WITNESS: a
#: (file, symbol) pair that must stay absent while the gap is real,
#: so the entry can ANNOUNCE ITS OWN OBSOLESCENCE the moment somebody
#: builds the door.
#:
#: WHY THIS EXISTS. Until 1.49.3 both cases were one `no_door(why,
#: item)` naming no file and no symbol - so nothing about them was
#: verified. test_1 walks `entry[0] == "door"`, which catches a door
#: that DISAPPEARS and can never notice one that APPEARS. The matrix
#: could therefore only be wrong in one direction, and it was the
#: expensive direction: a false "no door" tells a future session to
#: build something that already exists.
#:
#: IT HAD ALREADY HAPPENED, to the entry this file was written for.
#: "vector to lattice join" declared no door in QGIS - "reachable
#: only from run_osm_friction.py" - while BOTH GUIs had had a
#: joinlayer box since 1.47.6, the same release that wrote the claim.
#: Claude read that entry as current and nearly recommended building
#: a door that was already there.
#:
#: CHOOSING A WITNESS. It must be something that CANNOT be absent once
#: the door exists, and must not appear for any other reason. A dialog
#: BOX NAME or a registration import is usually right; an engine
#: function usually is not, because the same engine serves several
#: capabilities - paths_to_cells is called by machine 1's barrier
#: charging as well as by the lattice join, which is exactly the
#: conflation this file's docstring warns about.
def not_yet(why, item, absent):
    assert isinstance(absent, tuple) and len(absent) == 2, (
        "a gap needs a (file, symbol) witness - if there is nothing "
        "that would necessarily appear when the door is built, the "
        "entry is a ruling and not a gap, so say so with ruled_out()")
    return ("none", why, item, absent)


def same_as(other_door, extra=""):
    """No door, for the SAME reason another door has none.

    Written as a reference the test RESOLVES, not as the words "As
    QGIS" - which is what the first draft used and which tells a
    future session nothing it can act on. The resolved reason is what
    gets checked, so a cross-reference cannot be a way of writing
    less than a reason.

    BACKLOG 333: a reference may only land on a RULING. A reason can
    be shared; a WITNESS cannot, because a witness names one door's
    file. Pro borrowing QGIS's gap would assert something about a
    QGIS file and prove nothing about Pro - which is how the lattice
    join came to claim no Pro door while Pro had one. A door missing
    in two places for the same reason needs two witnesses.
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
        "stata": ruled_out(
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
        "stata": ruled_out(
            "A continental raster run writes a feature class and is "
            "measured in hours; Stata is not where anyone would "
            "start one. No demand recorded."),
    },
    "machine 4 - spatial demography": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_demography.py", "demography"),
        "pro": door("arcgis/EquiPop.pyt", "SpatialDemography"),
        "stata": ruled_out(
            "As machine 3: a demographic raster run writes a feature "
            "class and is measured in hours. Stata is not where "
            "anyone would start one, and no demand is recorded."),
    },
    "machine 5 - fetching": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_fetch.py", "plan_fetch"),
        "pro": not_yet(
            "Pro has four machines and this is not one of them. The "
            "gap is real and known; it widens every release that "
            "adds a provider.", 288,
            # a Pro fetch tool must reach the same planner the QGIS
            # door does, so the name cannot be absent once it exists
            absent=("arcgis/EquiPop.pyt", "plan_fetch")),
        "stata": ruled_out("Downloading is not a Stata activity."),
        "runner": door("run_fetch.py", "plan_fetch"),
    },

    # ------------------------------------------- distance ingredients
    "friction and barriers": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_counts.py", "barrier"),
        "pro": door("arcgis/EquiPop.pyt", "barrier"),
        "stata": ruled_out(
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
        "stata": ruled_out(
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
        "stata": ruled_out(
            "Reading a folder of GIS files to see which share a "
            "lattice is a GIS question, and the same reasoning that "
            "closed 296 applies. The JSON it writes is plain text "
            "that Stata can read if anyone ever needs to.", 269),
    },
    "vector to lattice join (OSM roads, polygons)": {
        # BACKLOG 333. THIS ROW WAS THE FALSE ONE, and it is why the
        # witness exists. It read "The headline engine of 1.46.0 and
        # 1.46.1 has no GUI. Reachable only from run_osm_friction.py"
        # - and 299 gave Pro a join box and 298 gave QGIS three
        # fidelities, both in 1.47.6, THE SAME RELEASE that wrote the
        # claim. Nothing could contradict it, so it stood for three
        # releases and reached the backlog's "what next" head as "the
        # two finished engines with NO DOOR".
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_continental.py",
                     "joinlayer"),
        "pro": door("arcgis/EquiPop.pyt", "joinlayer"),
        "stata": ruled_out(
            "A vector layer put on a raster lattice is a GIS "
            "operation on GIS inputs, so the reasoning that closed "
            "296 for friction and terrain applies unchanged. The "
            "result reaches Stata as the point table machine 3 "
            "writes.", 296),
        "runner": door("run_osm_friction.py", "lines_to_cells"),
    },
    "run provenance": {
        # BACKLOG 293, DONE v1.50.0. Every door records a run now, and
        # the record is built BY THE ENGINE from the arguments it was
        # given - so a setting added to dispatch() appears in the
        # record the same day with no door touched. That is the
        # property Pro's hand-written manifest never had, and it is
        # why `overshoot` moved every k-based number from 1.30 and
        # was recorded nowhere until 1.47.
        #
        # AND THIS ROW IS WHERE 333's WITNESS PROVED ITSELF: the three
        # gaps below fired the moment the doors were wired, in the
        # same session that added the mechanism. An hour earlier they
        # would have gone on claiming the capability was unreachable.
        "python": door("equipop/stata_bridge.py", "provenance"),
        "qgis": door("qgis/equipop_qgis/base.py", "write_provenance"),
        "pro": door("arcgis/EquiPop.pyt", "_EquiPop_run.csv"),
        "stata": door("stata/equipop.ado", "eqp_provenance"),
        # John's ruling, session 12, and it is what shipped: a
        # PRINTED NOTE rather than a sidecar, because a Stata run
        # writes variables into memory and may produce no file at
        # all - and because `log using` is where a Stata user's
        # reproducibility already lives. The values also come back in
        # r(overshoot), r(originrule) and r(provenance), so a do-file
        # can CHECK them rather than a human reading the log.
    },

    # --------------------------------- library work, no door expected
    "segregation profile": {
        "python": PYTHON,
        "qgis": ruled_out(
            "A profile is a curve over many k, not a column on a "
            "layer, so a GIS dialog is the wrong shape for it. The "
            "doors already produce the R_ columns it is computed "
            "from, and Stata or Python draws the curve."),
        "pro": same_as("qgis"),
        "stata": same_as("qgis", "and Stata draws curves well"),
    },
    "spatial autocorrelation": {
        "python": PYTHON,
        "qgis": ruled_out(
            "Moran's I and Getis-Ord over an EquiPop neighbourhood. "
            "No GUI demand recorded; the Tartu work drives it from "
            "Python and Stata."),
        "pro": same_as("qgis"),
        "stata": door("stata/equipop.ado", "knn_to_rows"),
    },
    "accessibility and FCA": {
        "python": PYTHON,
        # BACKLOG 333, found while auditing: three identical
        # one-liners, each just long enough to pass the 25-character
        # check and each saying nothing a future session could act
        # on. kFCA has been in the engine since 1.12.0. "No demand
        # recorded" is the honest part and is kept; what is added is
        # a witness, so the row stops being true the moment a door
        # appears.
        "qgis": not_yet(
            "No demand recorded. Two-step floating catchment areas "
            "have been in the engine since 1.12.0 and nobody has "
            "asked for a dialog; the doors already produce the "
            "neighbourhood the ratio is computed over.", None,
            absent=("qgis/equipop_qgis/provider.py", "alg_access")),
        "pro": not_yet(
            "No demand recorded, as in QGIS. A Pro tool would be a "
            "seventh machine and the fetch gap (288) is the one that "
            "widens.", None,
            absent=("arcgis/EquiPop.pyt", "two_step_fca")),
        "stata": ruled_out(
            "A catchment ratio over a k-neighbourhood is arithmetic "
            "Stata does natively once EquiPop has handed it the "
            "neighbourhood - the same division of labour John ruled "
            "on for machine 2.", 205),
    },
    "hex cells": {
        "python": PYTHON,
        # BACKLOG 158, FIXED v1.52.0 - and the reason this row gave for
        # offering hexes nowhere went with it. The entry USED to read
        # "its self-potential uses a SQUARE cell's area, overstating
        # the radius by 7.5% - so it should not be offered at a door
        # until that is fixed". It is fixed: CellData carries the cell
        # shape, selfpot derives area and mean intra-cell distance from
        # it, and a hex run's in-cell radii fell by exactly 7.46%.
        #
        # So this stops being a RULING and becomes a GAP, which is the
        # distinction 333 built: a ruling needs no witness because
        # nobody intends to close it, and a gap names what would appear
        # if somebody did. The witness is the box itself - a `hexsize`
        # parameter in the QGIS algorithm - so the day one is added,
        # this entry fails and has to be updated rather than quietly
        # going stale, which is the whole point of the mechanism.
        "qgis": not_yet(
            "Square cells only at every door. The engine half is now "
            "correct (158), so this is a dialog decision rather than a "
            "correctness blocker: a hex box needs a size in width "
            "across flats, and the two GIS doors would have to agree "
            "on the wording.", 158,
            absent=("qgis/equipop_qgis/alg_counts.py", "hexsize")),
        "pro": not_yet(
            "Square cells only at every door - see the QGIS row. Pro "
            "would need the same box, and door_parity would then hold "
            "the two to one wording.", 158,
            absent=("arcgis/EquiPop.pyt", "hexsize")),
        "stata": ruled_out(
            "A Stata user hands over coordinates and gets variables "
            "back; the cell grid is EquiPop's internal construction "
            "and hexagons would be one more thing to explain for no "
            "gain the GIS doors do not give better. Offered there "
            "first if anywhere.", 158),
    },
    "tiled, resumable big runs": {
        "python": PYTHON,
        "qgis": door("qgis/equipop_qgis/alg_continental.py", "tiles"),
        "pro": door("arcgis/EquiPop.pyt", "tiles"),
        "stata": ruled_out("Machine 3 has no Stata door either."),
    },
    # BACKLOG 385. A capability and not machinery: "what cell size
    # does this data want?" is a question a person asks, and John
    # asked it. Declared with four witnesses because the matrix is the
    # step that was missing when inventory.py and vectorjoin.py
    # shipped unreachable - and an ADVISORY is the easiest thing in
    # the project to ship unreachable, since every door calls it
    # inside `except Exception: pass`.
    "unit-size advice (what cell size does this data want?)": {
        "python": door("equipop/__init__.py", "advise_unit"),
        "qgis": door("qgis/equipop_qgis/alg_counts.py", "_unit_advice"),
        "pro": door("arcgis/EquiPop.pyt", "_unit_advice"),
        "stata": door("stata/equipop.ado", "_equipop_unit"),
    },
    "diagnostics (the doctor)": {
        "python": PYTHON,
        # BACKLOG 333: this was `pro: same_as("qgis")`, and a
        # reference cannot carry a witness - it would assert
        # something about a QGIS file and prove nothing about Pro,
        # which is exactly how the lattice join came to claim a
        # missing Pro door it had. Two gaps, two witnesses.
        "qgis": not_yet(
            "A user whose QGIS door is broken cannot run the thing "
            "that would say why - the plugin needs the package to "
            "load at all, so the diagnostic has to live where the "
            "failure does not.", 128,
            absent=("qgis/equipop_qgis/provider.py", "alg_doctor")),
        "pro": not_yet(
            "As QGIS, and for the same reason: the toolbox imports "
            "the package, so a doctor inside it cannot report the "
            "case where importing is what fails. Stata's works "
            "because the ado reaches Python without reaching "
            "equipop first.", 128,
            absent=("arcgis/EquiPop.pyt", "doctor")),
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
    # BACKLOG 320. Machinery, not a capability: reading a number a
    # person typed, whatever their machine calls a decimal point.
    # Both GIS doors call it, which is the point - Pro had its own
    # copy since 1.16.7 and QGIS had none, so a Norwegian student
    # typing 500,5 met a raw Python error.
    "doors.numbers",
    # BACKLOG 337. Machinery, not a capability: the numeric part of a
    # result column's name. Declared because the matrix asked - this
    # is the fourth new module it has stopped from shipping
    # undeclared, after inventory, vectorjoin and doors.numbers.
    # Both GIS doors, Stata and the name PREDICTION all call it, which
    # is the point: four formatters for one label gave one radius four
    # different column names across four doors.
    "labels",
    "doors.help", "doors.report", "doors.fields", "doors.loader",
    "doors.rungs", "doors.registry", "doors.reference",
    "doors.decaynames", "doors.demography", "doors.continental",
    "doors.fetching", "doors.inventory",
    # BACKLOG 385. Listed here like every other module - see the note
    # below on what this set actually means - AND carrying a row of
    # its own in MATRIX, because the cell size a study uses is
    # something a person asks about rather than machinery they never
    # see. It is the fifth new module this check has stopped from
    # shipping undeclared, after inventory, vectorjoin, doors.numbers
    # and labels.
    "unitsize",
}

#: WHAT THIS SET MEANS, because the name says less than it does.
#: test_4 checks every module in the package against INTERNAL and
#: nothing else, so EVERY module belongs here, capability or not; a
#: capability then ALSO gets a row in MATRIX naming its four doors.
#:
#: The assertion used to offer "either ... or", which was not true of
#: the code underneath it: a module given a MATRIX row and left out of
#: here still failed, with a message telling the author they had
#: already done enough. A guard whose instructions do not match its
#: behaviour is the same defect this file exists to catch, one level
#: up - so the wording was corrected rather than the check loosened.
