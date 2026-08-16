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
        "The easting. Must be metric - projected coordinates, not "
        "degrees. Rows with a missing coordinate receive missing "
        "results rather than stopping the command.",
    "y(varname)":
        "The northing, on the same metric system as x().",
    "prefix(string)":
        "Prepends a string to every new variable name, so several "
        "runs can live side by side in one dataset. prefix(a_) turns "
        "N_25 into a_N_25.",
    "replace":
        "Drops the result variables this run is about to create "
        "before creating them. Without it the command stops rather "
        "than overwriting silently.",
}


def _smcl_escape(text):
    """SMCL treats { and } as markup."""
    return text.replace("{", "{c -(}").replace("}", "{c )-}")


def _wrap(text, width=72, indent=""):
    return "\n".join(textwrap.wrap(_smcl_escape(text), width=width,
                                   initial_indent=indent,
                                   subsequent_indent=indent))


def option_text(opt):
    """The sentences for one option, from the shared source."""
    if opt in STATA_ONLY:
        return STATA_ONLY[opt]
    key = OPTION_HELP.get(opt)
    if key is None:
        raise KeyError(f"no help mapped for Stata option {opt!r}")
    if key not in HELP:
        raise KeyError(
            f"Stata option {opt!r} maps to help key {key!r}, which is "
            f"not in equipop/doors/help.py")
    return HELP[key]


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
    add("{synoptset 24 tabbed}{...}")
    add("{synopthdr}")
    add("{synoptline}")
    add("{syntab:Required}")
    for opt in ("x(varname)", "y(varname)"):
        add("{synopt:{opt %s}}%s{p_end}" % (opt, _first_line(opt)))
    add("{syntab:Neighbourhood}")
    for opt in ("k(numlist)", "r(numlist)", "unit(#)", "selfpot(#)"):
        add("{synopt:{opt %s}}%s{p_end}" % (opt, _first_line(opt)))
    add("{syntab:Population}")
    for opt in ("treat(varlist)", "pop(varname)"):
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
    add(_wrap(
        "equipop needs Python. See {help python} and, for the "
        "installation, the file TESTING_STATA.md in the EquiPop "
        "distribution. Note that Stata and Anaconda do not mix: use "
        "a plain python.org Python for Stata."))
    add("")
    add("{marker options}{...}")
    add("{title:Options}")
    add("")
    for opt in OPTION_HELP:
        add("{phang}")
        add("{opt %s} %s" % (opt, _smcl_escape(option_text(opt))))
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
            ("r(N_missing)", "rows that received no result")):
        add("{synopt:{cmd:%s}}%s{p_end}" % (nm, desc))
    add("{p2col 5 20 24 2: Macros}{p_end}")
    for nm, desc in (
            ("r(cmd)", "equipop"),
            ("r(cmdline)", "command as typed"),
            ("r(varlist)", "names of the variables created"),
            ("r(treat)", "treatment variables used"),
            ("r(k)", "k values requested"),
            ("r(r)", "radii requested")):
        add("{synopt:{cmd:%s}}%s{p_end}" % (nm, desc))
    add("{p2colreset}{...}")
    add("")
    add("{pstd}")
    add(_wrap(
        "r(varlist) is the useful one: it hands back the names just "
        "created, so a regression or a loop need not repeat them."))
    add("")
    add("{marker examples}{...}")
    add("{title:Examples}")
    add("")
    add("{phang}{cmd:. equipop, x(X_local) y(Y_local) k(50)}{p_end}")
    add("{phang}{cmd:. equipop, x(X_local) y(Y_local) "
        "treat(HighEdu) k(25 50 200) unit(100)}{p_end}")
    add("{phang}{cmd:. equipop if urban==1, x(X) y(Y) "
        "treat(HighEdu) k(50) replace}{p_end}")
    add("{phang}{cmd:. equipop [fweight=pop], x(X) y(Y) "
        "treat(HighEdu) k(50)}{p_end}")
    add("{phang}{cmd:. regress income `r(varlist)'}{p_end}")
    add("")
    add("{marker author}{...}")
    add("{title:Author}")
    add("")
    add("{pstd}John Osth, OsloMet. {browse "
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
