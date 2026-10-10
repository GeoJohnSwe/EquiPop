# -*- coding: utf-8 -*-
"""make_sthlp.py - Stata's help file, from the same text as every
other door.

BACKLOG 175. `help equipop` failed until 1.36 - the first thing a
Stata user types, and there was nothing to find.

The text is NOT written here. It comes from equipop/doors/help.py,
which ArcGIS Pro reads through make_help_xml.py and QGIS reads at run
time for shortHelpString. One source, four doors. When projection
lands, its sentences are written once in help.py and appear in the
Stata help, the Pro panel and the QGIS dialog together - which is the
condition John set when he ruled help ahead of projection.

Stata help is SMCL, not markdown. Run:

    python tools/make_sthlp.py            # writes stata/equipop.sthlp
    python tools/make_sthlp.py --check    # exit 1 if out of date
"""
import argparse
import os
import re
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from equipop.doors.help import HELP          # noqa: E402
from equipop import __version__              # noqa: E402

OUT = os.path.join(ROOT, "stata", "equipop.sthlp")

# Stata option -> the key its explanation lives under in help.py.
# A Stata option with no entry is a test failure, not a silent gap.
OPTION_HELP = {
    "x(varname)": "xfield",
    "y(varname)": "yfield",
    "treat(varlist)": "treat",
    "k(numlist)": "k",
    "r(numlist)": "r",
    "unit(#)": "unit",
    "pop(varname)": "pop",
    "prefix(string)": None,
    "selfpot(#)": "selfpot",
    "originrule(string)": "originrule",
    "treatmode(string)": None,
    "missing(numlist)": "missingcodes",
    "decay(string)": "decaymodel",
    "halflife(#)": None,
    "halflifevar(varname)": None,
    "bins(#)": None,
    "calibration(string)": None,
    "selfpotname(string)": None,
    "overshoot(string)": "overshoot",
    "project": None,
    "epsg(#)": None,
    "replace": None,
}

# Written here, not inherited. Two reasons a sentence lives here:
# the option has no counterpart box in a GIS dialog (prefix, replace),
# or the shared sentence carries GIS wording that is meaningless in
# Stata - x and y in the dialogs are qualified by "only for tables or
# attribute mode", because a GIS layer may carry geometry instead.
# A Stata dataset never does. Shared text where it is genuinely
# shared; door-specific text where pretending otherwise would mislead.
STATA_ONLY = {
    "x(varname)":
        "The easting, in metres or another metric unit. Longitude in "
        "degrees is accepted with the -project- option, which converts "
        "it first. Rows with a missing coordinate receive missing "
        "results rather than stopping the command.",
    "y(varname)":
        "The northing, on the same system as x(); or latitude in "
        "degrees, with -project-.",
    "halflife(#)":
        "A distance, in the same units as your coordinates, that "
        "anchors the decay curve. WHAT IT MEANS is set by "
        "calibration(): by default, half of all trips are shorter than "
        "this - so a median commute from a survey goes straight in. "
        "Required by decay(), unless halflifevar() gives one per place "
        "instead.",
    "halflifevar(varname)":
        "A variable holding each place's own half-life, so bandwidth "
        "varies across the map - wide in the countryside, tight in a "
        "city. Places are grouped into bins() bands of similar "
        "bandwidth and each band is run once, because running every "
        "distinct value separately would be needlessly slow.",
    "bins(#)":
        "How many bands of similar bandwidth halflifevar() is grouped "
        "into. More bands follow the variation more closely and take "
        "longer. Ignored without halflifevar(). Default 10.",
    "calibration(string)":
        "What the halflife() distance MEANS. halflife, the default: "
        "half of all trips are shorter than it - use this for a survey "
        "median. halfprob: a neighbour at that distance counts half as "
        "much. Östh, Lyhagen and Reggiani (2016) name both readings and "
        "advocate the first, which old EquiPop used; versions 1.30 to "
        "1.47 had silently switched to the second. The two give the "
        "same result for decay(negexp), so the choice only matters for "
        "the other models. decay(power) has no half-life - its curve "
        "never encloses a finite area, so no median exists - and uses "
        "halfprob whatever you ask, saying so. Both betas are printed, "
        "so the difference is visible whichever you choose.",
    "selfpotname(string)":
        "How far a place is from itself - the same three choices the "
        "QGIS and ArcGIS versions offer, by name rather than by "
        "number. none means no distance at all, and Dist_k can then "
        "come out as zero. median means half of what your own cell "
        "holds is nearer than this. full is the radius at which the "
        "cell's own people are reached, and is the default. "
        "selfpot(#) still takes any number between 0 and 1 if you "
        "want one.",
    "treatmode(string)":
        "What the treat() variables contain. counts (the default) "
        "means each one holds the NUMBER OF PEOPLE of that group at "
        "the point, which is how census and register data normally "
        "arrive, and how the GIS versions of EquiPop read it - it "
        "needs a population, from pop() or [fweight=]. flags means "
        "each one holds 0 or 1, a share of the row's own population, "
        "which is the older Stata convention. "
        "Getting this wrong cannot pass silently: a group larger than "
        "the population containing it is refused, with a message "
        "naming which setting to use.",
    "project":
        "Projects x() and y() from longitude and latitude in degrees "
        "to metres, using the UTM zone the data sits in, before "
        "anything is counted. The run reports which zone it used and "
        "returns it in r(epsg) and r(crs). "
        "Distances computed on unprojected degrees are not distances: "
        "a degree of longitude is shorter than a degree of latitude "
        "everywhere except the equator - by a quarter at 41 degrees, "
        "by half at 60 - so neighbourhoods come out stretched and the "
        "k nearest neighbours are not the nearest k. Without this "
        "option, coordinates that look like degrees raise a warning "
        "and are otherwise left alone. "
        "One zone is used for the whole dataset. If you already "
        "project your own data, you do not need this: pass the "
        "projected coordinates and leave it off.",
    "epsg(#)":
        "Chooses the projection -project- uses, instead of letting it "
        "pick the zone from the data. WGS84 UTM only: 32601-32660 "
        "north of the equator, 32701-32760 south. Requires -project-.",
    "prefix(string)":
        "Prepends a string to every new variable name, so several "
        "runs can live side by side in one dataset. prefix(a_) turns "
        "N_25 into a_N_25.",
    "replace":
        "Drops the result variables this run is about to create "
        "before creating them. Without it the command stops rather "
        "than overwriting silently.",
}


_SMCL_BRACES = str.maketrans({"{": "{c -(}", "}": "{c )-}"})


def _smcl_escape(text):
    """SMCL treats { and } as markup, so a LITERAL brace is escaped.

    BACKLOG 330. This was two chained .replace() calls, and the
    second one ate the first one's output: `{` became `{c -(}`, whose
    closing brace the second replace then turned into `{c )-}`, so
    every escaped brace shipped as `{c -({c )-}` - not the directive
    for a brace, and mangled again by the line wrapper, which is free
    to break inside it. Five of them were in the help file Kit Baum
    read for the SSC submission.

    str.translate does it in ONE pass and never re-scans what it has
    written, which is the property the chained replaces lacked.
    """
    return text.translate(_SMCL_BRACES)


def _smcl(text, width=72, indent=""):
    """Wrap text that IS SMCL - {cmd:...}, {help ...} - unescaped.

    BACKLOG 330. _wrap escapes braces, which is right for prose out
    of help.py and wrong for markup written here: the "See also" line
    had been asking for a clickable {help python} since the generator
    was written and shipping the words instead. Two jobs, two
    functions, so the choice has to be made deliberately.

    The wrapper is told not to break inside a directive - Stata reads
    `{cmd:python\\nquery}` as markup that never closes.
    """
    out, line = [], indent
    for tok in _smcl_tokens(text):
        if line.strip() and len(line) + len(tok) + 1 > width:
            out.append(line)
            line = indent + tok
        else:
            line = (line + " " + tok) if line.strip() else line + tok
    if line.strip():
        out.append(line)
    return "\n".join(out)


def _smcl_tokens(text):
    """Words, except that a {...} directive is one unbreakable word."""
    toks, buf, depth = [], "", 0
    for ch in text:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        if ch.isspace() and depth == 0:
            if buf:
                toks.append(buf)
                buf = ""
            continue
        buf += ch
    if buf:
        toks.append(buf)
    return toks


def _wrap(text, width=72, indent=""):
    return "\n".join(textwrap.wrap(_smcl_escape(text), width=width,
                                   initial_indent=indent,
                                   subsequent_indent=indent))


#: BACKLOG 338. A SENTENCE TO APPEND, not a replacement.
#:
#: Marina's pull request added `overshoot(string)` to STATA_ONLY to
#: record that `sampled` is refused in Stata - which is true and worth
#: saying. But STATA_ONLY REPLACES the shared text, and the shared
#: text is shared on purpose: OPTION_HELP maps each Stata option to a
#: key in equipop/doors/help.py so that a QGIS student and a Stata
#: student read the same words about the same box. A second copy of a
#: paragraph is exactly how BACKLOG 105's wording drifted - Pro said
#: "additive (sum)" where QGIS said "additive (costs add up)" - and
#: that is a permanent duplication only because a QGIS plugin may not
#: import the package at load time. Here there is no such constraint.
#:
#: So a door-specific FACT is appended to the shared explanation
#: instead of overriding it. Use this when the box means the same
#: thing everywhere and only its availability differs.
STATA_EXTRA = {
    # JOHN, 10 OCTOBER 2026. The shared text now describes the loop -
    # run, read the note, set the size, run again - and the one thing
    # it cannot carry is the Stata spelling, because the same
    # paragraph is read in QGIS and Pro where there is no command to
    # type. This is the door-specific FACT that belongs here.
    "unit(#)":
        "IN STATA you can also ask without running the analysis at "
        "all: -equipop unit xvar yvar, k(100)- prints the whole "
        "table in a second or so and changes nothing, so it is safe "
        "to try before committing to a long run. It takes the same "
        "[fweight=] or pop() as a run, and -help equipop- documents "
        "its own options and r() results. A run that does not set "
        "unit() prints the short version of the same advice when it "
        "finishes.",
    "overshoot(string)":
        "NOT AVAILABLE IN STATA: overshoot(sampled) returns an error "
        "pointing you to overshoot(proportional), or to QGIS and "
        "ArcGIS Pro, which do implement it - sampled needs a seeded "
        "draw over whole cells, and the Stata door does not carry "
        "one.",
}


def option_text(opt):
    """The sentences for one option, from the shared source."""
    if opt in STATA_ONLY:
        return STATA_ONLY[opt]
    extra = STATA_EXTRA.get(opt, "")
    key = OPTION_HELP.get(opt)
    if key is None:
        raise KeyError(f"no help mapped for Stata option {opt!r}")
    if key not in HELP:
        raise KeyError(
            f"Stata option {opt!r} maps to help key {key!r}, which is "
            f"not in equipop/doors/help.py")
    # A PARAGRAPH BREAK, not a space. A door-specific fact is a
    # different thought from the shared explanation, and running them
    # together made unit(#)'s second paragraph a wall. The options
    # loop in build() turns each break into its own {phang2}.
    return HELP[key] + (("\n\n" + extra) if extra else "")


def build():
    v = __version__
    L = []
    add = L.append
    add("{smcl}")
    add("{* *! version %s}{...}" % v)
    add("{vieweralsosee \"[R] regress\" \"help regress\"}{...}")
    add("{viewerjumpto \"Syntax\" \"equipop##syntax\"}{...}")
    add("{viewerjumpto \"Description\" \"equipop##description\"}{...}")
    add("{viewerjumpto \"Options\" \"equipop##options\"}{...}")
    add("{viewerjumpto \"Stored results\" \"equipop##results\"}{...}")
    add("{viewerjumpto \"Diagnostics\" \"equipop##diagnostics\"}{...}")
    add("{viewerjumpto \"Examples\" \"equipop##examples\"}{...}")
    add("")
    add("{title:Title}")
    add("")
    add("{phang}")
    add("{bf:equipop} {hline 2} k-nearest neighbour context "
        "variables (EquiPop %s)" % v)
    add("")
    add("{marker syntax}{...}")
    add("{title:Syntax}")
    add("")
    add("{p 8 17 2}")
    add("{cmd:equipop}")
    add("{weight}")
    add("{ifin}")
    add("{cmd:,} {opt x(varname)} {opt y(varname)}")
    add("[{it:options}]")
    add("")
    add("{pstd}")
    add("Report on the Python this Stata is using, and on the "
        "libraries EquiPop needs. Reads nothing and changes nothing.")
    add("")
    add("{p 8 17 2}")
    add("{cmd:equipop doctor}")
    add("")
    add("{pstd}")
    add("Install or update the calculating engine, into the Python "
        "this Stata is using. Add {cmd:repair} when a library is "
        "present but will not load.")
    add("")
    add("{p 8 17 2}")
    add("{cmd:equipop setup} [{cmd:, repair}]")
    add("")
    # John's field report, 10 October 2026: he typed `equipop help`
    # and was told it was an unknown subcommand. Stata's convention is
    # `help equipop`, and both work now - so both are documented, or
    # the test that derives this list from the dispatch fails.
    add("{pstd}")
    add(_wrap(
        "Open this help file. Stata's own convention is "
        "`help equipop`, and that still works; `equipop help` is "
        "accepted because it is what somebody types when a "
        "subcommand has just been refused."))
    add("")
    add("{p 8 17 2}")
    add("{cmd:equipop help}")
    add("")
    # BACKLOG 385. The third subcommand, and its text is HELP's
    # "unitadvice" rather than written here - the condition John set
    # when he ruled help ahead of projection was one source, four
    # doors, and a subcommand documented only in Stata would break it.
    add("{pstd}")
    # ONE add(), as every other paragraph in this file does.
    #
    # This was `for line in _wrap(...): add(line)` - and `_wrap`
    # returns ONE STRING of joined lines, so iterating it yielded
    # CHARACTERS. The generated help carried 746 consecutive
    # one-character lines and `help equipop` was unreadable from the
    # unit-advice paragraph onward, in both Stata archives.
    #
    # `--check` did not catch it because it compares the malformed
    # output against the malformed generator and finds them in
    # agreement. Nor did my own inspection: I grepped the output for
    # the strings I expected, and a grep cannot tell that a paragraph
    # has been spread one character per line, because every character
    # is still there. The test that catches it is in
    # tests/test_packaging.py and is about the SHAPE of the file.
    add(_wrap(HELP["unitadvice"]))
    add("")
    add("{p 8 17 2}")
    add("{cmd:equipop unit} {it:xvar} {it:yvar} {ifin} "
        "[{cmd:fweight}{cmd:=}{it:varname}]")
    add("[{cmd:,} {opt pop(varname)} {opt k(numlist)} "
        "{opt cand:idates(numlist)} {opt tol:erance(#)} "
        "{opt originrule(string)} {opt nocache}]")
    add("")
    # Review finding 1. Three options appeared in the syntax line
    # above and were explained nowhere - the options section below is
    # built from OPTION_HELP, which is the RUN's option list, so an
    # option belonging only to the subcommand had no route into it.
    # A test now requires every option named in this syntax line to
    # have text somewhere in the file.
    add("{pstd}")
    # PLAIN PROSE, no SMCL. `_wrap` escapes braces - correctly, that
    # is its contract and a test pins it - so markup written in here
    # reaches the user as the literal text `{c -(}cmd:...{c )-}`.
    # Caught by checking the SHIPPED file rather than the generator.
    add(_wrap(
        "Options for equipop unit alone. pop() or [fweight=] "
        "gives the population each row stands for, exactly as on a "
        "run. k() takes a numlist and the advice is reported per k, "
        "because the answer depends on it; without k() the report "
        "says it is advising for k=100. candidates() replaces the "
        "ladder of cell sizes tried - the size you are currently "
        "using is always added to it, so your own row is always "
        "there. tolerance() is the share of people whose radius may "
        "be estimated rather than measured before a size is "
        "rejected; the default 0.01 means fewer than one answer in a "
        "hundred. originrule() decides whether the criterion applies "
        "at all rather than merely labelling the output - under "
        "exclude an origin's own cell is never its whole "
        "neighbourhood, so no size is recommended and the report "
        "says why. nocache recomputes instead of reading the advice "
        "stored on the dataset."))
    add("")
    add("{synoptset 24 tabbed}{...}")
    add("{synopthdr}")
    add("{synoptline}")
    add("{syntab:Required}")
    for opt in ("x(varname)", "y(varname)"):
        add("{synopt:{opt %s}}%s{p_end}" % (opt, _first_line(opt)))
    add("{syntab:Neighbourhood}")
    for opt in ("k(numlist)", "r(numlist)", "unit(#)", "selfpot(#)",
                "originrule(string)"):
        add("{synopt:{opt %s}}%s{p_end}" % (opt, _first_line(opt)))
    add("{syntab:Population}")
    for opt in ("treat(varlist)", "pop(varname)"):
        add("{synopt:{opt %s}}%s{p_end}" % (opt, _first_line(opt)))
    add("{synopt:{opt treatmode(string)}}%s{p_end}"
        % _first_line("treatmode(string)"))
    add("{synopt:{opt missing(numlist)}}%s{p_end}"
        % _first_line("missing(numlist)"))
    add("{syntab:Distance weighting}")
    for opt in ("decay(string)", "halflife(#)", "halflifevar(varname)",
                "bins(#)", "calibration(string)", "overshoot(string)",
                "selfpotname(string)"):
        add("{synopt:{opt %s}}%s{p_end}" % (opt, _first_line(opt)))
    add("{syntab:Coordinates}")
    for opt in ("project", "epsg(#)"):
        add("{synopt:{opt %s}}%s{p_end}" % (opt, _first_line(opt)))
    add("{syntab:Output}")
    for opt in ("prefix(string)", "replace"):
        add("{synopt:{opt %s}}%s{p_end}" % (opt, _first_line(opt)))
    add("{synoptline}")
    add("{p2colreset}{...}")
    add("{p 4 6 2}")
    add("{cmd:fweight}s are allowed; see {help weight}. A weight "
        "says how many people the row stands for.")
    add("{p_end}")
    add("")
    add("{marker description}{...}")
    add("{title:Description}")
    add("")
    add("{pstd}")
    add(_wrap(
        "equipop builds, for every observation, the neighbourhood of "
        "its k nearest neighbours measured in PEOPLE rather than in "
        "rows, and reports what that neighbourhood contains. "
        "Neighbourhoods are individual and overlapping, so they cut "
        "across administrative boundaries instead of being bound by "
        "them."))
    add("")
    add("{pstd}")
    add(_wrap(
        "For each k it adds N_k, the population actually gathered, "
        "and Dist_k, the distance travelled to gather it. For each "
        "variable in treat() it adds T_var_k, the count of that "
        "group inside the neighbourhood, and R_var_k, that count as "
        "a share of the observed population. Radii in r() give the "
        "same columns, named _r<radius>. treat() is optional: "
        "without it you get neighbourhood size and reach alone."))
    add("")
    add("{pstd}")
    add(_wrap(
        "Coordinates must be metric. Rows with missing coordinates "
        "receive missing results rather than stopping the command. "
        "if and in restrict which rows RECEIVE results; every row "
        "still counts as a neighbour to others."))
    add("")
    add("{pstd}")
    # BACKLOG 330: _smcl, not _wrap - {help python} is meant to be a
    # LINK. And the pointer went to TESTING_STATA.md, which has not
    # existed outside stata/historical/ since 1.36: a help file that
    # names a missing file is worse than one that names none, and
    # this one is on SSC now.
    add(_smcl(
        "equipop needs Python. See {help python}, the file "
        "README_STATA.md in the EquiPop distribution for the "
        "installation, and {cmd:equipop doctor}, which reports the "
        "Python Stata is actually using and whether the libraries "
        "load in it. Note that Stata and Anaconda do not mix: use a "
        "plain python.org Python for Stata."))
    add("")
    add("{marker options}{...}")
    add("{title:Options}")
    add("")
    for opt in OPTION_HELP:
        # A BLANK LINE IN THE SHARED TEXT IS A PARAGRAPH BREAK, and
        # each paragraph needs its own SMCL block or the second one
        # renders flush-left, outside the option's indent. Added when
        # unit(#) grew a second paragraph (John, 10 October 2026); it
        # applies to every option that ever gains one.
        paras = [p.strip() for p in option_text(opt).split("\n\n")
                 if p.strip()]
        add("{phang}")
        add("{opt %s} %s" % (opt, _smcl_escape(paras[0])))
        add("{p_end}")
        for extra in paras[1:]:
            add("")
            # {phang2} indents a continuation under the option name,
            # which is what a reader expects of a second paragraph
            # about the same box.
            add("{phang2}")
            add(_smcl_escape(extra))
            add("{p_end}")
        add("")
    add("{marker results}{...}")
    add("{title:Stored results}")
    add("")
    add("{pstd}{cmd:equipop} stores the following in {cmd:r()}:")
    add("")
    add("{synoptset 20 tabbed}{...}")
    add("{p2col 5 20 24 2: Scalars}{p_end}")
    for nm, desc in (
            ("r(unit)", "cell size in metres"),
            ("r(selfpot)", "self-potential used"),
            ("r(N_origins)", "rows in the sample"),
            ("r(N_missing)", "rows that received no result"),
            ("r(halflife)", "half-life distance, with decay()"),
            ("r(beta)", "decay parameter actually used")):
        add("{synopt:{cmd:%s}}%s{p_end}" % (nm, desc))
    add("{p2col 5 20 24 2: Macros}{p_end}")
    for nm, desc in (
            ("r(cmd)", "equipop"),
            ("r(cmdline)", "command as typed"),
            ("r(varlist)", "names of the variables created"),
            ("r(treat)", "treatment variables used"),
            ("r(k)", "k values requested"),
            ("r(r)", "radii requested"),
            ("r(decay)", "decay model, with decay()"),
            ("r(calibration)", "half-life or half-probability, as APPLIED")):
        add("{synopt:{cmd:%s}}%s{p_end}" % (nm, desc))
    add("{p2colreset}{...}")
    add("")
    # BACKLOG 385. The subcommand's own r(), listed separately because
    # it is a different command and sharing one table would suggest a
    # run returns these too.
    add("{pstd}{cmd:equipop unit} stores the following in {cmd:r()}:")
    add("")
    add("{synoptset 20 tabbed}{...}")
    add("{p2col 5 20 24 2: Scalars}{p_end}")
    for nm, desc in (
            ("r(unit)", "the RECOMMENDED cell size for the first k, "
                        "in metres - missing if no candidate serves it"),
            ("r(cells)", "cells that size would make"),
            ("r(estimated)", "share of people whose radius would be "
                             "estimated at that size"),
            ("r(tolerance)", "the share treated as acceptable"),
            ("r(N)", "points with usable coordinates"),
            ("r(people)", "population those points carry"),
            # Review finding 1. This exists SO a script can tell the
            # two reasons r(unit) is missing apart, and it was
            # returned by the ado and documented nowhere - which
            # makes it unusable for the one job it has.
            ("r(applies)",
             "1 if the criterion applies to the origin rule in "
             "force, 0 under originrule(exclude) where an origin's "
             "own cell is never its whole neighbourhood. r(unit) is "
             "missing both when no size serves k and when the "
             "criterion does not apply, so this is what tells them "
             "apart")):
        add("{synopt:{cmd:%s}}%s{p_end}" % (nm, desc))
    add("{p2col 5 20 24 2: Macros}{p_end}")
    for nm, desc in (
            # Found by the test below the moment it was written:
            # these two differ for the subcommand (r(cmd) is
            # "equipop unit", not "equipop") and were listed only
            # under the run.
            ("r(cmd)", "equipop unit"),
            ("r(cmdline)", "subcommand as typed"),
            ("r(k)", "k values the advice is about"),
            ("r(originrule)", "the origin rule in force"),
            ("r(fingerprint)", "digest of the coordinates advised on")):
        add("{synopt:{cmd:%s}}%s{p_end}" % (nm, desc))
    add("{p2col 5 20 24 2: Matrices}{p_end}")
    add("{synopt:{cmd:r(advice)}}one row per candidate size: "
        "unit, cells, thin, then sat/shcells/shpeople per k{p_end}")
    add("{p2colreset}{...}")
    add("")
    add("{pstd}")
    add(_wrap(
        "r(unit) is a recommendation and nothing more - EquiPop never "
        "sets the cell size for you. Two runs on the same data would "
        "otherwise be able to use different sizes without saying so, "
        "and a published figure would depend on a heuristic that "
        "might change between versions. If you want the recommended "
        "size, pass it yourself: unit(`r(unit)')."))
    add("")
    add("{pstd}")
    add(_wrap(
        "r(varlist) is the useful one: it hands back the names just "
        "created, so a regression or a loop need not repeat them."))
    add("")
    add("{marker diagnostics}{...}")
    add("{title:Diagnostics}")
    add("")
    add("{pstd}")
    add(_wrap(
        "equipop runs its calculations in Python, so it depends on the "
        "Python that Stata is configured to use and on three libraries "
        "inside it: numpy, pandas and scipy. When something is wrong "
        "there, the failure happens before any EquiPop code is reached "
        "and the error message will not mention EquiPop."))
    add("")
    add("{phang}{cmd:. equipop setup}{p_end}")
    add("")
    add("{pstd}")
    add(_smcl(
        "installs the engine into the Python Stata is using, so it "
        "cannot land in a different one. Add {cmd:repair} - "
        "{cmd:equipop setup, repair} - to reinstall numpy, scipy and "
        "pandas as well, which is the fix when a library is installed "
        "but refuses to load. Restart Stata afterwards: Stata starts "
        "Python once per session and keeps what it first loaded."))
    add("")
    add("{phang}{cmd:. equipop doctor}{p_end}")
    add("")
    add("{pstd}")
    add(_wrap(
        "prints which Python is in use, which processor it is built "
        "for, and the state of every library - present, absent, or "
        "installed but refusing to load. Two cases it names directly: "
        "a library built for a different processor than the Python "
        "loading it (common on Apple Silicon, where an Intel package "
        "sits in the user folder), and a package installed into a "
        "different Python than the one Stata uses."))
    add("")
    add("{pstd}")
    add(_wrap(
        "Install into the Python whose path the report prints, and "
        "restart Stata afterwards: Stata starts Python once per "
        "session and keeps the packages it first loaded."))
    add("")
    add("{pstd}")
    add(_smcl(
        "See also {help python}, and {cmd:python query}, which reports "
        "Stata's own view of the same interpreter."))
    add("")
    add("{marker examples}{...}")
    add("{title:Examples}")
    add("")
    # BACKLOG 330. The package installs two worked do-files and a test
    # dataset and the help had never said so, which left the paper as
    # the only place they were named - and the paper named them by the
    # filenames SSC then changed. findfile is given because an SSC
    # install files them under PLUS and not in the user's folder,
    # so `do equipop_showcase` alone does not find them.
    add("{pstd}")
    add(_smcl(
        "Two worked do-files and a test dataset install with the "
        "package if you ask for them - {cmd:ssc install equipop, all} "
        "- and Stata will tell you where they went:"))
    add("")
    add("{phang}{cmd:. findfile equipop_example.do}{p_end}")
    add("{phang}{cmd:. do \"`r(fn)'\"}{p_end}")
    add("")
    # BACKLOG 338, Marina's PR: say what the examples RUN ON - the
    # help named no variables, so a reader could not try them. Her
    # version used stata_test_data.dta and `use stata_test_data,
    # clear`; both changed in 1.49.3 (Baum renamed the file, and an
    # SSC install puts it under PLUS rather than in the working
    # directory, so findfile is what locates it).
    add("{pstd}")
    add(_smcl(
        "The examples run on {cmd:equipop_test_data.dta}: {cmd:ID}, "
        "{cmd:X_local}, {cmd:Y_local}, four 0/1 education markers "
        "({cmd:LowEdu}, {cmd:HighEdu}, {cmd:TheoEdu}, "
        "{cmd:VocaEdu}), a continuous {cmd:ValFloat} with missings by "
        "design, and a count {cmd:ValCount}. Load it the same way:"))
    add("")
    add("{phang}{cmd:. findfile equipop_test_data.dta}{p_end}")
    add("{phang}{cmd:. use \"`r(fn)'\", clear}{p_end}")
    add("")
    add("{pstd}")
    add(_smcl(
        "{cmd:equipop_example.do} is the short round trip; "
        "{cmd:equipop_showcase.do} runs every function in turn with "
        "the expected numbers in comments, against "
        "{cmd:equipop_test_data.dta}. Both locate the data with "
        "{help findfile}, so they run from anywhere."))
    add("")
    add("{phang}{cmd:. equipop setup}{p_end}")
    add("{phang}{cmd:. equipop doctor}{p_end}")
    add("")
    # BACKLOG 338, Marina's PR: say what the examples RUN ON. Her
    # version named stata_test_data.dta and `use stata_test_data,
    # clear`; both changed in 1.49.3 - C. F. Baum renamed the file on
    # the archive, and an SSC install puts it under PLUS rather than
    # in the working directory, so findfile is what finds it.
    add(_smcl(
        "The examples below run on {cmd:equipop_test_data.dta}, which "
        "installs with the package: {cmd:ID}, {cmd:X_local}, "
        "{cmd:Y_local}, four 0/1 education markers ({cmd:LowEdu}, "
        "{cmd:HighEdu}, {cmd:TheoEdu}, {cmd:VocaEdu}), a continuous "
        "{cmd:ValFloat} with missings by design, and a count "
        "{cmd:ValCount}."))
    add("")
    add("{phang}{cmd:. findfile equipop_test_data.dta}{p_end}")
    add("{phang}{cmd:. use \"`r(fn)\'\", clear}{p_end}")
    add("")
    add("{phang}{cmd:. equipop, x(X_local) y(Y_local) k(50)}{p_end}")
    add("{phang}{cmd:. equipop, x(X_local) y(Y_local) "
        "treat(HighEdu) k(25 50 200) unit(100)}{p_end}")
    add("{phang}{cmd:. equipop if urban==1, x(X) y(Y) "
        "treat(HighEdu) k(50) replace}{p_end}")
    add("")
    add("{pstd}A reference population - counts per row rather than one "
        "row per person:{p_end}")
    add("{phang}{cmd:. equipop, x(X) y(Y) pop(totalpop) "
        "treat(university) k(500 1000)}{p_end}")
    add("{pstd}{cmd:pop()} takes FRACTIONAL counts, which is what "
        "gridded population needs. {cmd:[fweight=]} means the same "
        "thing and lets Stata validate it, but demands whole numbers "
        "- give one or the other, never both:{p_end}")
    add("{phang}{cmd:. equipop [fweight=households], x(X) y(Y) "
        "treat(renting) k(200)}{p_end}")
    add("")
    add("{pstd}Self-potential - whether an origin counts itself. The "
        "default keeps it, which is right when a row is a place; "
        "{cmd:selfpot(0)} drops it, which is right when a row is a "
        "person and you are asking about their surroundings:{p_end}")
    add("{phang}{cmd:. equipop, x(X) y(Y) treat(unemployed) k(100) "
        "selfpot(0)}{p_end}")
    add("")
    add("{pstd}Distance decay - near neighbours weigh more than far "
        "ones. {cmd:half(m)} is the distance at which a neighbour "
        "counts half:{p_end}")
    add("{phang}{cmd:. equipop, x(X) y(Y) treat(HighEdu) k(1000) "
        "decay(negexp) half(500)}{p_end}")
    add("{phang}{cmd:. equipop, x(X) y(Y) treat(HighEdu) k(1000) "
        "decay(lognormal) half(2000)}{p_end}")
    add("")
    add("{pstd}Overshoot - what to do with the ring that carries the "
        "neighbourhood past k. {cmd:whole} takes the whole ring, so N "
        "exceeds k; {cmd:proportional} takes the same fraction of "
        "every cell in it, so N equals k exactly. The difference is "
        "largest where this work matters most - small k, large cells, "
        "and at boundaries:{p_end}")
    add("{phang}{cmd:. equipop, x(X) y(Y) treat(HighEdu) k(100) "
        "overshoot(proportional)}{p_end}")
    add("")
    add("{pstd}The new variables are named in {cmd:r(varlist)}, so "
        "they can be used directly:{p_end}")
    add("{phang}{cmd:. regress income `r(varlist)'}{p_end}")
    add("")
    add("{marker author}{...}")
    add("{title:Author}")
    add("")
    add("{pstd}John Östh, OsloMet. {browse "
        "\"https://github.com/GeoJohnSwe/EquiPop\"}{p_end}")
    return "\n".join(L) + "\n"


def _first_line(opt):
    """The one-line form for the syntax table."""
    t = re.split(r"(?<=[.;])\s", option_text(opt))[0]
    t = _smcl_escape(t.strip())
    return t if len(t) <= 60 else t[:57].rsplit(" ", 1)[0] + "..."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = build()
    if args.check:
        current = (open(OUT, encoding="utf-8").read()
                   if os.path.exists(OUT) else "")
        if current != text:
            print("stata/equipop.sthlp is out of date - run "
                  "python tools/make_sthlp.py")
            return 1
        print("stata/equipop.sthlp is current")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {OUT} ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
