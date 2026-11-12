*! equipop_run v1.64.1  -  ONE command, the whole toolbox (since EquiPop 1.6).
*! Syntax:
*!   equipop_run [if] [in], engine(counts|stats|friction|slope|fca|lisa)
*!       x() y() [...]
*! Engines and their options:
*!   counts   : treat(varlist) k(numlist) r(numlist) [weight()]
*!   stats    : values(varlist) k(numlist) r(numlist) [stats(string)]
*!   friction : treat(varname) k(numlist) tau(numlist) [friction(path)]
*!   slope    : treat(varname) k(numlist) tau(numlist) dem(path)
*!              [model(tobler|linear) roundtrip]
*!   fca      : demandvar(varname) supply(path.csv/.dta/.sav)
*!              [supplycol(name) method(2sfca|3sfca)] and ONE reach:
*!              halflife(#) | reach(r) rfca(#) | reach(k) kfca(#)
*!              -> A, J
*!   lisa     : values(varname) [k(#) = weight-knn, wperm(#)]
*!              -> LISA_<v>_Ii, LISA_<v>_quad (1=HH 2=LL 3=HL 4=LH),
*!                 LISA_<v>_p  (on cell means, loud)
*! Common: unit(#) weight(varname) treatmode(counts|flags) replace
*!         overshoot(whole|proportional) originrule(include|exclude)
*!         (the last two: counts, stats, friction, slope)
*! [if] [in] choose the rows that GET results; everybody still counts
*! as a neighbour, as in -equipop-.
*! All results come back ROW-ALIGNED as new variables; r(varlist)
*! names them.

program define equipop_run, rclass
    version 17
    * BACKLOG 487, John's ruling of 11 November 2026: "bring it up to
    * level with equipop". Four things -equipop- had and this command
    * did not: [if] [in]; returned results; overshoot() and
    * originrule(); and refusals in the words of its own options.
    syntax [if] [in], ENGINE(string) X(varname numeric)              ///
        Y(varname numeric)                                           ///
        [TREAT(varlist numeric) VALUES(varlist numeric) ///
         STATS(string) K(numlist integer >0) R(numlist >0) ///
         TAU(numlist >0) Unit(real 100) Weight(varname numeric) ///
         DEM(string) MODEL(string) ROUNDtrip FRICTION(string) ///
         DEMANDvar(varname numeric) SUPPLY(string) ///
         SUPPLYCOL(string) SUPPLYX(string) SUPPLYY(string) ///
         HALFlife(real 0) REACH(string) METHOD(string) ///
         KFCA(real 0) RFCA(real 0) WPERM(real 199) ///
         SELFpot(real 1) TREATMODE(string) OVERshoot(string) ///
         ORIGINrule(string) REPLACE]

    * ---- the sample (BACKLOG 487) -------------------------------
    * The rule is -equipop-'s, word for word: [if] and [in] restrict
    * the ROWS THAT GET RESULTS. They do not restrict who counts as a
    * neighbour - -equipop_run if urban==1- computes for urban rows,
    * and rural people still fill their neighbourhoods. novarlist: a
    * row with a missing value keeps its place; what a missing value
    * means is the engine's business, not marksample's.
    marksample touse, novarlist

    * ---- the options that were TYPED (BACKLOG 490) ---------------
    * Recorded here, before any default is filled in below, so the
    * Python half can refuse an option this engine does not read:
    * model(linear) with engine(counts), halflife() outside fca, r()
    * with friction. Each used to run, with a clean log, without the
    * option. The table of who reads what is in equipop/stata_bridge.py
    * (RUN_OPTIONS), where the test suite can run it.
    local eqp_given ""
    foreach eqp_o in treat treatmode values stats k r tau weight dem ///
        model roundtrip friction demandvar supply supplycol supplyx ///
        supplyy reach method overshoot originrule {
        if `"``eqp_o''"' != "" local eqp_given "`eqp_given' `eqp_o'"
    }
    if `halflife' != 0 local eqp_given "`eqp_given' halflife"
    if `kfca' != 0     local eqp_given "`eqp_given' kfca"
    if `rfca' != 0     local eqp_given "`eqp_given' rfca"
    if `wperm' != 199  local eqp_given "`eqp_given' wperm"
    if `selfpot' != 1  local eqp_given "`eqp_given' selfpot"

    * See equipop_knn.ado. selfpot(0) reproduces
    * pre-1.29.5 numbers exactly, in every engine.
    if `selfpot' < 0 | `selfpot' > 1 {
        display as error "selfpot() must lie between 0 and 1"
        exit 198
    }
    * BACKLOG 451, v1.63.1 (review of 1.63.0). unit(-1) reached the
    * engine and came back as a plausible table on a grid that does not
    * exist; unit(0) and unit(.) stopped inside Python. -equipop- has
    * refused these since 1.29.8; this command never did. missing()
    * first: Stata's . compares GREATER than every number, so a bare
    * <= 0 lets it through.
    if missing(`unit') | `unit' <= 0 {
        display as error "unit() is the cell size and must be a " ///
            "number greater than zero"
        exit 198
    }
    * wperm() is a COUNT of permutations: refused, not truncated, when
    * it is not a whole number of at least one (the same rule theta(k)
    * applies to its shuffles since 1.62.1). Zero would report p = 1
    * for every cell, which is not a p-value of anything.
    if missing(`wperm') | `wperm' < 1 | `wperm' != int(`wperm') {
        display as error "wperm() is the number of permutations for " ///
            "the LISA p-values and must be a whole number of 1 or " ///
            "more (default 199)"
        exit 198
    }

    * ---- the engine, and what it cannot run without (BACKLOG 487)
    * Until 1.63.8 none of this was checked here. The engine refused
    * in ITS words ("give k_values and/or r_values"), a slope run
    * without dem() died inside the raster library, fca without
    * demandvar() was a KeyError, and stats without values() ran and
    * returned counts.
    if !inlist("`engine'", "counts", "stats", "friction", "slope", "fca", "lisa") {
        display as error "engine() must be counts, stats, friction, " ///
            "slope, fca or lisa"
        exit 198
    }
    if inlist("`engine'", "counts", "stats") & "`k'`r'" == "" {
        display as error "engine(`engine') needs k(), r() or both"
        exit 198
    }
    if "`engine'" == "stats" & "`values'" == "" {
        display as error "engine(stats) needs values() - the " ///
            "variables whose mean, median and spread are wanted"
        exit 198
    }
    if inlist("`engine'", "friction", "slope") & "`k'`tau'" == "" {
        display as error "engine(`engine') needs k(), tau() or both"
        exit 198
    }
    if "`engine'" == "slope" & `"`dem'"' == "" {
        display as error "engine(slope) needs dem() - the elevation " ///
            "raster the slopes are read from"
        exit 198
    }
    if "`engine'" == "lisa" & `: word count `values'' != 1 {
        display as error "engine(lisa) needs exactly one variable " ///
            "in values()"
        exit 198
    }
    if "`engine'" == "fca" {
        if "`demandvar'" == "" {
            display as error "engine(fca) needs demandvar() - the " ///
                "demand at each observation"
            exit 198
        }
        if `"`supply'"' == "" {
            display as error "engine(fca) needs supply() - the file " ///
                "of facilities (.csv, .dta or .sav)"
            exit 198
        }
        * ONE reach, and the option that goes with it. reach(decay)
        * is the default, so a bare -engine(fca)- needs halflife() -
        * and until 1.63.8 was told so as "reach='decay' needs a
        * decay". A catchment by radius or by the k nearest needs no
        * half-life at all.
        if !inlist("`reach'", "", "decay", "r", "k") {
            display as error "reach() must be decay, r or k"
            exit 198
        }
        if inlist("`reach'", "", "decay") & `halflife' <= 0 {
            display as error "engine(fca) with reach(decay), the " ///
                "default, needs halflife(#): the distance in " ///
                "metres at which a facility counts half"
            display as text "  For a fixed catchment say reach(r) " ///
                "rfca(#); for the k nearest, reach(k) kfca(#). " ///
                "Neither needs a half-life."
            exit 198
        }
        if "`reach'" == "r" & `rfca' <= 0 {
            display as error "reach(r) needs rfca(#), the catchment " ///
                "radius in metres"
            exit 198
        }
        if "`reach'" == "k" & `kfca' <= 0 {
            display as error "reach(k) needs kfca(#), how much " ///
                "supply the catchment grows to hold"
            exit 198
        }
        if !inlist("`method'", "", "2sfca", "3sfca") {
            display as error "method() must be 2sfca or 3sfca"
            exit 198
        }
    }
    * a file that is named has to be there
    foreach eqp_f in dem friction supply {
        if `"``eqp_f''"' != "" {
            confirm file `"``eqp_f''"'
        }
    }

    * ---- what treat() CONTAINS (BACKLOG 475) --------------------
    * The same rule as -equipop-, which is what the help has always
    * promised ("the count and share of each treatment, as equipop").
    * Until 1.63.7 this command never said which rule it wanted, so
    * the engine applied the old one - treat() as a 0/1 flag, MULTIPLIED
    * by weight() - while -equipop- has read treat() as the number of
    * people in the group since 1.37.1 (BACKLOG 179). The same data
    * gave two different shares from the two commands. It only shows
    * with weight(): without it the two rules are the same sum.
    local treatmode_given = cond("`treatmode'" != "", 1, 0)
    if "`treatmode'" == "" local treatmode "counts"
    if !inlist("`treatmode'", "counts", "flags") {
        display as error "treatmode() must be counts or flags"
        display as text "  counts - treat() holds the NUMBER OF " ///
            "PEOPLE of the group at this point (the default)"
        display as text "  flags  - treat() holds 0 or 1, a share " ///
            "of the row's population"
        exit 198
    }
    if "`treat'" != "" & "`weight'" != "" & !`treatmode_given' ///
        & inlist("`engine'", "counts", "friction", "slope") {
        display as text "[equipop_run] treat() is read as the " ///
            "NUMBER OF PEOPLE in the group, as -equipop- reads it."
        display as text "  Until 1.63.7 this command multiplied " ///
            "treat() by weight() instead. For that reading - treat() " ///
            "is 0 or 1 - say treatmode(flags)."
    }

    * ---- the overshoot and the origin rule (BACKLOG 487) --------
    * The same two options as -equipop-, the same words, the same
    * refusals - for the four engines that count a neighbourhood. On
    * the other two they are refused: an option that is accepted and
    * does nothing is how a wrong analysis gets a clean log.
    local counting = inlist("`engine'", "counts", "stats", "friction", "slope")
    if "`overshoot'" != "" & !`counting' {
        display as error "overshoot() does not apply to engine(`engine')"
        exit 198
    }
    if "`originrule'" != "" & !`counting' {
        display as error "originrule() does not apply to engine(`engine')"
        exit 198
    }
    if "`overshoot'" == "sampled" {
        display as error "overshoot(sampled) is not available in Stata"
        display as text "  It exists to reproduce older versions of " ///
            "EquiPop, and it draws cells in a random order, so a run " ///
            "cannot be repeated exactly without carrying a seed."
        display as text "  Use overshoot(proportional) for the " ///
            "expected value of it, or run it in QGIS or ArcGIS Pro."
        exit 198
    }
    if !inlist("`overshoot'", "", "whole", "proportional") {
        display as error "overshoot() must be whole or proportional"
        exit 198
    }
    if `"`originrule'"' == "i=j" | `"`originrule'"' == "i==j" local originrule "include"
    if `"`originrule'"' == "i!=j" | `"`originrule'"' == "i ne j" local originrule "exclude"
    if !inlist(`"`originrule'"', "", "include", "exclude") {
        display as error "originrule() must be include or exclude"
        display as text "  include (the default) counts the origin's " ///
            "own cell as part of its neighbourhood, as every " ///
            "published EquiPop result does."
        display as text "  exclude leaves it out - the w(ii)=0 " ///
            "convention that spatial regression needs. Results " ///
            "under the two are NOT comparable."
        exit 198
    }

    if "`model'" == ""     local model "tobler"
    if "`reach'" == ""     local reach "decay"
    if "`method'" == ""    local method "2sfca"
    if "`supplyx'" == ""   local supplyx "x"
    if "`supplyy'" == ""   local supplyy "y"
    if "`supplycol'" == "" local supplycol "supply"
    local rt = cond("`roundtrip'" != "", "1", "0")
    local rep = cond("`replace'" != "", "1", "0")

    * BACKLOG 476. dem(), friction() and supply() are FILE NAMES, and
    * they are no longer pasted into the line below. Pasted, a Windows
    * path became Python source: C:\data\new.csv has a newline in it
    * (\n), C:\temp a tab, and C:\Users stops the command with a
    * SyntaxError about a truncated escape. The three are handed over
    * empty here and the Python reads the macros themselves.
    * Every argument BY NAME, as -equipop- has done since 1.34.
    python: _equipop_run(engine="`engine'", xv="`x'", yv="`y'",       ///
        treatv="`treat'", valuesv="`values'", statss="`stats'",       ///
        ks="`k'", rs="`r'", taus="`tau'", unit=`unit', wv="`weight'", ///
        dem="", model="`model'", rt=`rt', fricf="",                   ///
        demv="`demandvar'", supf="", supcol="`supplycol'",            ///
        supx="`supplyx'", supy="`supplyy'", hl=`halflife',            ///
        reach="`reach'", method="`method'", kfca=`kfca',              ///
        rfca=`rfca', rep=`rep', selfpot=`selfpot', wperm=`wperm',     ///
        treatmode="`treatmode'", touse="`touse'",                     ///
        overshoot="`overshoot'", originrule="`originrule'")

    * ---- returned results (BACKLOG 487) -------------------------
    * As -equipop-: r(varlist) is the one that changes how the
    * command can be used - -regress y `r(varlist)'- and loops over
    * several k stop needing hand-written variable names.
    local created "`eqp_run_varlist'"
    quietly count if `touse'
    local n_origins = r(N)
    local n_missing = 0
    if "`created'" != "" {
        local first : word 1 of `created'
        quietly count if missing(`first') & `touse'
        local n_missing = r(N)
    }
    display as result "equipop_run: engine `engine' - "            ///
        "`: word count `created'' new variables, "                  ///
        "`n_origins' rows in sample, `n_missing' without results"

    return local cmd      "equipop_run"
    return local cmdline  `"equipop_run `0'"'
    return local engine   "`engine'"
    return local varlist  "`created'"
    return local treat    "`treat'"
    return local values   "`values'"
    return local k        "`k'"
    return local r        "`r'"
    return local tau      "`tau'"
    return scalar unit      = `unit'
    return scalar selfpot   = `selfpot'
    return scalar N_origins = `n_origins'
    return scalar N_missing = `n_missing'
    * the two settings that move every k-based number: what RAN, so
    * an option left out returns the default that was applied
    if `counting' {
        return local overshoot  "`eqp_run_overshoot'"
        return local originrule "`eqp_run_originrule'"
    }
end

python:
# BACKLOG 460. STATA READS EVERY LINE OF THIS BLOCK BEFORE PYTHON DOES,
# comments and strings included, and expands Stata macros in it: a
# backtick with an apostrophe later on the same line is a local macro,
# backtick-colon is a macro FUNCTION, and a dollar sign before a name is
# a global. 1.63.2 quoted the doctor between backticks in a comment that
# also held the word Apple's; Stata tried to run ": Stata had picked
# Apple" as a macro function, answered "Stata not allowed" and printed
# the rest of the block (John's first Windows run, 5 November 2026).
# Write commands as -equipop doctor-, never between backticks.
# tests/test_stata_block_without_numpy.py reads the blocks as Stata does.
from sfi import Data, Macro, SFIToolkit
import sys
# BACKLOG 459. No numpy or equipop import at load time: Stata runs this
# block when it loads the file, and a failed import there gives r(7102)
# with a traceback instead of a sentence. They are imported where they
# are used, and a failure says what to do.
#
# Review of 1.63.2, F4: on Python 3.10 (engine 1.61.0 at most) say so
# once per Stata session. Own names on purpose: this block and
# equipop.ado's run in the same Python namespace, so a function called
# _python_note_once here would replace that file's version.
_RUN_PY_NOTED = []


def _run_python_note_once():
    if sys.version_info[:2] == (3, 10) and not _RUN_PY_NOTED:
        _RUN_PY_NOTED.append(True)
        SFIToolkit.displayln(
            "{txt}Note: Stata is using Python 3.10. The newest EquiPop "
            "engine for it is 1.61.0;")
        SFIToolkit.displayln(
            "{txt}   later engines need Python 3.11 or newer. -equipop "
            "doctor- says how to move.")

def _col(v):
    import numpy as np
    a = np.array(Data.get(v), dtype=float)
    a[a > 8.9e307] = np.nan
    return a

# ---- which options each engine READS (BACKLOG 490) ----------------
# Found by the independent review of 1.64.0. equipop_run declares every
# engine's options in one syntax line, so model(linear) was accepted by
# engine(counts), halflife(500) by engine(counts) - no decay, no word -
# and r(500) by engine(friction), which counts by k and tau only. Each
# ran, with a clean log, without the option. That is the fault John
# ruled against for ArcGIS Pro on the same day (486): an option that
# is accepted and does nothing is how a wrong analysis gets a clean
# log. The table sits beside the syntax line it describes, and in
# this block it works with any engine version; the suite runs it
# (tests/test_stata_run_options.py).
_RUN_OPTIONS = {
    "treat": ("counts", "friction", "slope"),
    "treatmode": ("counts", "friction", "slope"),
    "values": ("stats", "lisa"),
    "stats": ("stats",),
    "k": ("counts", "stats", "friction", "slope", "lisa"),
    "r": ("counts", "stats"),
    "tau": ("friction", "slope"),
    "weight": ("counts", "stats", "friction", "slope"),
    "selfpot": ("counts", "stats", "friction", "slope"),
    "overshoot": ("counts", "stats", "friction", "slope"),
    "originrule": ("counts", "stats", "friction", "slope"),
    "friction": ("friction", "slope"),
    "dem": ("slope",),
    "model": ("slope",),
    "roundtrip": ("slope",),
    "demandvar": ("fca",),
    "supply": ("fca",),
    "supplycol": ("fca",),
    "supplyx": ("fca",),
    "supplyy": ("fca",),
    "halflife": ("fca",),
    "reach": ("fca",),
    "method": ("fca",),
    "kfca": ("fca",),
    "rfca": ("fca",),
    "wperm": ("lisa",),
}

# what to do instead, where there is something better than "leave it
# out": (option, engine) - or (option, None) for every engine
_RUN_OPTION_HINTS = {
    ("r", "friction"): "friction and slope count by k() and tau(), "
                       "not by distance",
    ("r", "slope"): "friction and slope count by k() and tau(), "
                    "not by distance",
    ("r", "fca"): "fca takes its own reach: reach(r) rfca(#)",
    ("k", "fca"): "fca takes its own reach: reach(k) kfca(#)",
    ("halflife", None): "outside fca, equipop_run has no distance "
                        "decay - equipop has, with decay() and "
                        "halflife()",
    ("dem", "friction"): "terrain is engine(slope)",
    ("model", "friction"): "the walking model belongs to engine(slope)",
    ("roundtrip", "friction"): "the return journey belongs to "
                               "engine(slope)",
    ("tau", None): "a budget of effort exists only for friction and "
                   "slope",
    ("treat", "fca"): "fca reads its demand from demandvar()",
    ("weight", "fca"): "fca reads its demand from demandvar()",
}


def _run_engines_text(engines):
    named = [f"engine({e})" for e in engines]
    if len(named) == 1:
        return f"only {named[0]} reads it"
    return f"{', '.join(named[:-1])} and {named[-1]} read it"


def _run_options_not_read(engine, given):
    """The equipop_run options in given that engine does not read,
    as one sentence each - empty when every option given is read.

    given is the options the user TYPED (the ado records them before
    it fills in any default), as names or one space-separated string.
    """
    if isinstance(given, str):
        given = given.split()
    given = [g for g in given if g]
    lines = []
    for opt in given:
        readers = _RUN_OPTIONS.get(opt)
        if readers is None or engine in readers:
            continue
        hint = (_RUN_OPTION_HINTS.get((opt, engine))
                or _RUN_OPTION_HINTS.get((opt, None)))
        lines.append(
            f"{opt}() does nothing with engine({engine}): "
            f"{_run_engines_text(readers)}. Leave it out"
            + (f" ({hint})." if hint else "."))
    if ("treatmode" in given and "treat" not in given
            and engine in _RUN_OPTIONS["treatmode"]):
        lines.append("treatmode() says how to read treat(), and no "
                     "treat() was given. Leave it out, or name the "
                     "group variables in treat().")
    return lines


def _engine_takes_unit(unit):
    """BACKLOG 445, v1.63.0. A FRACTIONAL unit() needs engine 1.63.0 or
    newer: an older one rounds it somewhere (output coordinates, the
    effort engines' grid) and either stops with a lookup error or runs
    at the rounded size. eqp_min_engine stays where it is - a whole
    size loses nothing on an older engine (BACKLOG 331/385) - so the
    one case that needs the newer engine is refused here, in words.
    tests/test_fractional_cells.py runs this against a stand-in old
    engine. The same function is in equipop.ado."""
    u = float(unit)
    if u == int(u):
        return True
    try:
        from equipop import __version__ as eng
    except Exception:
        eng = "unknown"
    # leading digits of the first three parts; no regex, because a
    # backslash in an ado's python block is one more thing to escape
    nums = []
    for part in str(eng).split(".")[:3]:
        d = ""
        for ch in part:
            if not ch.isdigit():
                break
            d += ch
        nums.append(int(d) if d else -1)
    if len(nums) == 3 and tuple(nums) >= (1, 63, 0):
        return True
    SFIToolkit.errprintln(
        f"unit({u:g}): a fractional cell size needs the EquiPop engine "
        f"1.63.0 or newer, and this Python has {eng}. Run -equipop "
        "setup- to update it, or give a whole number.")
    return False


def _run_drop_exactly(names):
    """Drop these variables and no others (BACKLOG 473).

    By POSITION in the dataset, highest first, and only a variable
    whose name IS the name asked for. Stata's own -drop- reads a name
    that does not exist as an abbreviation of one that does: asked to
    drop N_200 on a dataset holding N_2000, it deletes N_2000. A
    position cannot be abbreviated. Should this Stata's sfi have no
    dropVar, the fallback is -drop- under -novarabbrev-, on a name
    already known to exist in full. (Own name on purpose: this block
    shares a Python namespace with equipop.ado's.)
    """
    have = [Data.getVarName(i) for i in range(Data.getVarCount())]
    where = sorted({have.index(n) for n in names if n in have},
                   reverse=True)
    for i in where:
        try:
            Data.dropVar(i)
        except Exception:
            # have[i] exists under exactly this name, and Stata takes
            # an exact name before any abbreviation - so even a plain
            # -drop- cannot reach another variable here
            try:
                SFIToolkit.stata("novarabbrev drop " + have[i])
            except Exception:
                SFIToolkit.stata("drop " + have[i])


def _equipop_run(*, engine, xv, yv, treatv="", valuesv="", statss="",
                 ks="", rs="", taus="", unit=100.0, wv="", dem="",
                 model="tobler", rt=0, fricf="", demv="", supf="",
                 supcol="supply", supx="x", supy="y", hl=0.0,
                 reach="decay", method="2sfca", kfca=0.0, rfca=0.0,
                 rep=0, selfpot=1.0, wperm=199, treatmode="counts",
                 touse="", overshoot="", originrule="", given=None):
    # KEYWORD-ONLY on purpose (BACKLOG 476): twenty-eight values in a
    # row is how an option comes to arrive in its neighbour's place.
    _run_python_note_once()
    # The three FILE NAMES come from the macros, not from the call:
    # see the note at the python: line above. A caller that does pass
    # one (the tests) is taken at its word.
    dem = dem or Macro.getLocal("dem")
    fricf = fricf or Macro.getLocal("friction")
    supf = supf or Macro.getLocal("supply")
    try:
        import numpy                                    # BACKLOG 459
        from equipop.stata_bridge import dispatch, to_stata_values
    except ImportError as exc:
        ver = ".".join(str(p) for p in sys.version_info[:3])
        SFIToolkit.errprintln(
            "the EquiPop engine cannot be loaded in the Python Stata is "
            f"using (Python {ver}):")
        SFIToolkit.errprintln("   " + (sys.executable or "(unknown)"))
        SFIToolkit.errprintln("   " + str(exc).splitlines()[0])
        SFIToolkit.errprintln(
            "EquiPop needs Python 3.11 or newer with the engine "
            "installed. Run -equipop doctor- for what to do.")
        SFIToolkit.error(198)
        return
    if not _engine_takes_unit(unit):
        SFIToolkit.error(198)
        return
    # BACKLOG 490: an option this engine does not read is refused, not
    # ignored. The options typed come from the macro the Stata half
    # filled before any default; a caller that passes them (the tests)
    # is taken at its word.
    if given is None:
        given = Macro.getLocal("eqp_given")
    unread = _run_options_not_read(engine, given)
    if unread:
        SFIToolkit.errprintln("equipop_run: nothing was computed -")
        for line in unread:
            SFIToolkit.errprintln("  " + line)
        SFIToolkit.error(198)
        return
    kw = dict(unit_size=float(unit),
              self_potential=float(selfpot))
    kw["k_values"] = [int(t) for t in ks.split()] or None
    kw["r_values"] = [float(t) for t in rs.split()] or None
    kw["tau_values"] = [float(t) for t in taus.split()] or None
    if treatv:
        kw["treat"] = {v: _col(v) for v in treatv.split()}
        if engine in ("counts", "friction", "slope"):
            # BACKLOG 475: said, not left to the engine's old default
            kw["treat_are_counts"] = (treatmode != "flags")
    if wv:
        kw["weight"] = _col(wv)
    # BACKLOG 487: the two rules, for the engines that count a
    # neighbourhood. Left out, the engine's own default applies - and
    # the default is what is handed back in r().
    counting = engine in ("counts", "stats", "friction", "slope")
    if counting and overshoot:
        kw["overshoot_mode"] = overshoot
    if counting and originrule:
        kw["self_rule"] = originrule
    if engine == "lisa":
        vals = {v: _col(v) for v in valuesv.split()}
        kw["values"] = vals
        kw["w_k"] = int(ks.split()[0]) if ks.split() else 8
        kw["k_values"] = None
        kw["permutations"] = int(wperm)
    if engine == "stats":
        vals = {v: _col(v) for v in valuesv.split()}
        kw["values"] = vals
        wanted = statss.split() if statss else ["mean", "median", "gini"]
        kw["stats"] = {v: wanted for v in vals}
    if engine in ("friction", "slope"):
        kw["friction_file"] = fricf or None
        if engine == "slope":
            kw["dem"] = dem
            kw["model"] = model
            kw["roundtrip"] = bool(rt)
    if engine == "fca":
        kw["demand_arr"] = _col(demv)
        kw["supply_file"] = supf
        kw["supply_col"] = supcol
        kw["supply_x"], kw["supply_y"] = supx, supy
        kw["half_life_m"] = hl if hl > 0 else None
        kw["reach"], kw["method"] = reach, method
        kw["k_fca"] = kfca if kfca > 0 else None
        kw["r_fca"] = rfca if rfca > 0 else None

    # A refusal from the engine is a MESSAGE, not a traceback - the
    # same rule -equipop- has followed since 1.38.
    try:
        res = dispatch(engine, _col(xv), _col(yv), **kw)
    except ValueError as exc:
        for line in str(exc).splitlines():
            SFIToolkit.errprintln(line)
        SFIToolkit.error(198)
        return

    # BACKLOG 473. EVERY NAME IS CHECKED BEFORE ANY VARIABLE IS MADE.
    # The check used to be Stata's own refusal inside the writing loop,
    # so an existing name on the third variable left the first two in
    # the dataset: a command that stopped with an error and changed
    # the data anyway.
    safe_names = [name.replace(".", "_") for name in res]
    have = [Data.getVarName(i) for i in range(Data.getVarCount())]
    problems = []
    for safe in safe_names:
        if len(safe) > 32:
            problems.append(
                f"{safe} is {len(safe)} characters; Stata allows 32. "
                "Shorten the variable name it is built from.")
        elif safe in have and not rep:
            problems.append(f"{safe} already exists - use option replace")
    for safe in sorted(set(safe_names)):
        if safe_names.count(safe) > 1:
            problems.append(f"{safe} would be created twice")
    if problems:
        SFIToolkit.errprintln("no variables were created:")
        for line in problems[:10]:
            SFIToolkit.errprintln("  " + line)
        if len(problems) > 10:
            SFIToolkit.errprintln(f"  ... and {len(problems) - 10} more")
        SFIToolkit.error(110)
        return
    # replace: exactly these, and only now that the engine has answered
    _run_drop_exactly([n for n in safe_names if n in have])
    # BACKLOG 487. [if] [in]: computed for everyone, REPORTED for the
    # sample - the rule of -equipop-. A row outside the sample is
    # still somebody's neighbour; it just receives no result.
    keep = _col(touse) > 0 if touse else None
    for safe, arr in zip(safe_names, res.values()):
        vals = numpy.asarray(arr, dtype=float)
        if keep is not None:
            vals = numpy.where(keep, vals, numpy.nan)
        Data.addVarDouble(safe)
        # Stata refuses
        # None for a missing number. It had simply never been reached
        # here either, because it needs a missing RESULT to appear.
        Data.store(safe, None, to_stata_values(vals))
    # what the Stata half returns in r()
    Macro.setLocal("eqp_run_varlist", " ".join(safe_names))
    if counting:
        from equipop.overshoot import DEFAULT as _OVER_DEFAULT
        from equipop.selfrule import DEFAULT as _ORIG_DEFAULT
        Macro.setLocal("eqp_run_overshoot", str(overshoot or _OVER_DEFAULT))
        Macro.setLocal("eqp_run_originrule",
                       str(originrule or _ORIG_DEFAULT))
end
