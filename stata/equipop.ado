*! equipop v1.44.3  -  k-nearest neighbour context variables via EquiPop
*! Machine 1 (Counts and Shares). Adds, per requested k:
*!   N_<k>, Dist_<k>, and per treatment variable v: T_<v>_<k>, R_<v>_<k>
*! row-aligned to the dataset in memory. Radii r() give the same
*! columns named _r<r>. treat() is optional; without it you get the
*! neighbourhood size and reach alone.
*!
*! Requires Stata 17+, Python configured (python query), and the
*! Python package installed in THAT Python. See help equipop.
*!
*! Behaves like a Stata command: [if] [in], native [fweight=],
*! returned results in r(), and prefix(). -equipop doctor- reports on
*! the Python itself; -equipop setup- installs or updates the engine.

program define equipop, rclass
    version 17

    * ---- -equipop doctor- --------------------------------------
    * A read-only report on the Python Stata is using
    * and the libraries EquiPop needs. This is the FIRST thing the
    * program does, for two reasons: it has to work on a machine
    * where nothing else does, and it must not be made to supply
    * x() and y(), which the syntax line below makes mandatory.
    *
    * The two failures it exists for both happen BEFORE any EquiPop
    * code is reached, so neither can produce an EquiPop error: a
    * library built for the wrong processor, and
    * two copies of one maths library in a process (Stata plus
    * Anaconda on Windows, 1.35).
    gettoken eqp_sub eqp_rest : 0, parse(" ,")
    if `"`eqp_sub'"' == "doctor" {
        _equipop_doctor
        exit
    }
    if `"`eqp_sub'"' == "setup" {
        _equipop_setup `eqp_rest'
        exit
    }

    * A bare word that is not a subcommand. Without this it falls
    * through to the syntax line below, Stata reads it as a variable
    * list, and the user is told "varlist not allowed" - which is true
    * and useless. John hit this in the field running -equipop setup-
    * against an .ado that predated the subcommand.
    *
    * The test is safe because every REAL first token is punctuation
    * or a Stata keyword: a comma, an [fweight=...], -if- or -in-.
    * A bare alphabetic word can only be a mistaken subcommand.
    if regexm(`"`eqp_sub'"', "^[a-zA-Z][a-zA-Z0-9_]*$")               ///
       & !inlist(`"`eqp_sub'"', "if", "in") {
        display as error `"unknown subcommand: `eqp_sub'"'
        display as text "  equipop doctor  - report on the Python " ///
            "this Stata is using"
        display as text "  equipop setup   - install or update the " ///
            "calculating engine"
        display as text ""
        display as text "  If you typed one of those and Stata does " ///
            "not know it, the"
        display as text "  command files here are older than the " ///
            "subcommand. Update them:"
        display as text `"     net install equipop, from("https://raw.githubusercontent.com/GeoJohnSwe/EquiPop/main/stata") replace"'
        display as text "  and then restart Stata."
        display as text ""
        display as text "  To analyse data, the variables go in " ///
            "options, after a comma:"
        display as text "     equipop, x(X) y(Y) k(25)"
        exit 198
    }

    syntax [fweight] [if] [in], X(varname numeric) Y(varname numeric) ///
           [TREAT(varlist numeric) ///
            K(numlist integer >0) R(numlist >0) ///
            Unit(real 100) POP(varname numeric) PREFIX(string) ///
            SELFpot(real 1) PROJect EPSG(integer 0) ///
            TREATmode(string) MISSing(numlist) ///
            DECAY(string) HALFlife(real 0) HALFlifevar(varname numeric) ///
            SELFPOTName(string) ///
            BINS(integer 10) OVERshoot(string) REPLACE]

    * ---- projection -------------------------------------------
    * Design rule: a professional spatial analyst has their
    * own routines and does not need this. It is for the economist or
    * statistician who has lat/long and has never been asked to think
    * past it - for whom being forced to project first is a blocker
    * that stops them using the method at all.
    *
    * So: one automatic, defensible choice, and the run SAYS which one
    * it made. epsg() is the escape hatch for anyone who wants a
    * particular zone.
    if `epsg' != 0 & "`project'" == "" {
        display as error "epsg() sets which projection to use, so it " ///
            "needs -project- as well"
        exit 198
    }

    * ---- the sample -------------------------------------------
    * Design rule: [if] and [in] restrict the ROWS THAT GET
    * RESULTS. They do NOT restrict who counts as a neighbour - that
    * is the reference-population ladder's job and it is a different
    * question. `equipop if urban==1` computes for urban origins,
    * and rural people still fill their neighbourhoods.
    *
    * novarlist matters: without it marksample also drops any row
    * with a missing value among the variables, which would quietly
    * shrink the population. Missing handling is EquiPop's own
    * and the two must not fight. The rule is: use
    * Stata's own commands where we can, not where it jeopardises
    * our code - this is the seam between the two.
    * zeroweight matters for the same reason. Without it, marksample
    * drops every row whose [fweight=] is 0 - and in John's field data
    * that was 109 places with no residents, which then received no
    * results at all while pop() gave them results. A place with no
    * people still HAS a neighbourhood around it, and the two routes
    * into the same idea must not disagree at the boundary. John's
    * ruling, 1.40.4: "they shall have results". It is the same
    * principle as a case blanked by missing() - it is still the
    * placeholder for results, it just contributes nothing itself.
    marksample touse, novarlist zeroweight

    * ---- weights ----------------------------------------------
    * fweight is the honest Stata reading of an EquiPop weight:
    * "this row stands for N identical observations" IS a population
    * count in a cell. Stata validates it for us. But fweight demands
    * whole numbers and EquiPop supports fractional population on
    * purpose (WorldPop; machine 2 taking part of a cell), so pop()
    * remains for that case.
    local wvar ""
    if "`weight'" != "" {
        if "`pop'" != "" {
            display as error "give either [fweight=varname] or " ///
                "pop(varname), not both - they mean the same thing"
            exit 198
        }
        local wvar = trim(subinstr("`exp'", "=", "", 1))
    }
    else if "`pop'" != "" {
        local wvar "`pop'"
    }

    * ---- distance decay ----------------------------------------
    * Words, not numbers, throughout: a do-file read
    * six months later has to say what it did.
    if "`decay'" != "" {
        * The five the engine actually implements. The door may not
        * import the package to learn its own vocabulary (78/105), so
        * this list is duplicated on purpose and pinned by
        * tests/test_stata_boxes.py against equipop.decay.MODELS.
        if !inlist("`decay'", "negexp", "expnormal", "expsqrt",       ///
                   "lognormal", "power") {
            display as error "decay() must be negexp, expnormal, " ///
                "expsqrt, lognormal or power"
            exit 198
        }
        if `halflife' <= 0 & "`halflifevar'" == "" {
            display as error "decay() needs a half-life: the distance " ///
                "at which a neighbour counts half as much"
            display as text "  halflife(#)      one distance for " ///
                "everybody, in map units"
            display as text "  halflifevar(var) a variable, so each " ///
                "place carries its own bandwidth"
            exit 198
        }
        if `halflife' > 0 & "`halflifevar'" != "" {
            display as error "give halflife() or halflifevar(), " ///
                "not both"
            exit 198
        }
    }
    else if `halflife' > 0 | "`halflifevar'" != "" {
        display as error "halflife() sets the bandwidth for decay(), " ///
            "so it needs decay() as well"
        exit 198
    }

    * ---- the overshoot: the ring of cells that crosses k ---------
    * `sampled` is REFUSED BY NAME rather than ignored.
    * John's reason: it exists only to reproduce old EquiPop versions,
    * so it is not a Stata concern at all. Refusing it by name also
    * drops the need for a seed option, since sampled is the one mode
    * that makes a run irreproducible without one.
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

    * ---- what treat() CONTAINS ---------------------------------
    * The help and both GIS doors said treat() holds the group's
    * PERSON COUNT, while the bridge applied the legacy 0/1-flag rule.
    * A user who followed the help got a group three times larger than
    * the neighbourhood containing it. Counts are the default now,
    * matching the help and the GIS doors; flags stay available by
    * name so nothing already written breaks.
    if "`treatmode'" == "" local treatmode "counts"
    if !inlist("`treatmode'", "counts", "flags") {
        display as error "treatmode() must be counts or flags"
        display as text "  counts - treat() holds the NUMBER OF " ///
            "PEOPLE of the group at this point (the default)"
        display as text "  flags  - treat() holds 0 or 1, a share " ///
            "of the row's population"
        exit 198
    }

    * ---- cell size ---------------------------------------------
    * Fractional cell sizes are REFUSED, because the core
    * converts cell centres to integers - a requested 2.5 gives centres
    * 1, 3, 6, so the spacings come out 2 and 3 and neither is 2.5.
    * QGIS and Pro have refused this since 1.29.8. Stata did not, and
    * a rule enforced at some doors and not others is how 172 happened.
    * The rule itself lives in the package, so a fourth door inherits
    * it rather than reimplementing it.
    if `unit' <= 0 {
        display as error "unit() is the cell size and must be " ///
            "greater than zero"
        exit 198
    }
    if `unit' != int(`unit') {
        display as error "unit() must be a whole number - the cell " ///
            "grid is built on integer centres, so a fractional size " ///
            "would not give evenly spaced cells"
        exit 198
    }

    * ---- self-potential: three rungs, or any number between ------
    * The GIS doors offer three named rungs. Stata kept a bare number,
    * which is how the doors drifted apart. Both now work: the names
    * are the ladder, the number is the escape hatch, and the engine
    * still receives a float either way.
    if "`selfpotname'" != "" {
        if "`selfpotname'" == "none"       local selfpot = 0
        if "`selfpotname'" == "median"     local selfpot = 1/sqrt(2)
        if "`selfpotname'" == "full"       local selfpot = 1
        if !inlist("`selfpotname'", "none", "median", "full") {
            display as error "selfpotname() must be none, median or full"
            display as text "  none   - no distance at all; Dist_k " ///
                "can come out as zero"
            display as text "  median - half of what your cell holds " ///
                "is nearer than this"
            display as text "  full   - the radius at which k of it " ///
                "is reached (the default)"
            exit 198
        }
    }
    if `selfpot' < 0 | `selfpot' > 1 {
        display as error "selfpot() must lie between 0 and 1"
        exit 198
    }
    if "`k'" == "" & "`r'" == "" {
        display as error "give k() and/or r()"
        exit 198
    }
    if "`prefix'" != "" {
        capture confirm name `prefix'N_1
        if _rc {
            display as error "prefix() must begin a legal Stata " ///
                "variable name"
            exit 198
        }
    }

    * ---- drop what we are about to write ----------------------
    if "`replace'" != "" {
        if "`k'" != "" {
            foreach kk of numlist `k' {
                capture drop `prefix'N_`kk'
                capture drop `prefix'Dist_`kk'
                * treat() became optional in 1.36, and an empty
                * -varlist- loop is a syntax error, not an empty loop.
                * So -equipop, x() y() k(25) replace- failed on exactly
                * the combination that ruling created.
                if "`treat'" != "" {
                    foreach v of varlist `treat' {
                        capture drop `prefix'T_`v'_`kk'
                        capture drop `prefix'R_`v'_`kk'
                    }
                }
            }
        }
        if "`r'" != "" {
            foreach rr of numlist `r' {
                * `rl' is the underscore-safe name -
                * r=1.5 becomes r1_5, because a dot cannot appear in
                * a Stata variable name.
                local rl : subinstr local rr "." "_", all
                capture drop `prefix'N_r`rl'
                if "`treat'" != "" {
                    foreach v of varlist `treat' {
                        capture drop `prefix'T_`v'_r`rl'
                        capture drop `prefix'R_`v'_r`rl'
                    }
                }
            }
        }
    }

    * Every option is passed BY NAME, and the receiving
    * function is keyword-only. Up to v1.34 this was a positional
    * call, and that is how the door broke for eleven releases: an
    * option was added to the syntax line and to the call, and the
    * def never heard of it. A named call cannot be got wrong by
    * ORDER and names a mistake out loud. Same medicine as 169.
    python: _equipop_machine1(x="`x'", y="`y'", treat="`treat'",     ///
        k="`k'", r="`r'", unit=`unit', weight="`wvar'",              ///
        selfpot=`selfpot', touse="`touse'", prefix="`prefix'",       ///
        project="`project'", epsg=`epsg', treatmode="`treatmode'",  ///
        missing="`missing'", decay="`decay'", halflife=`halflife',   ///
        halflifevar="`halflifevar'", bins=`bins',                    ///
        overshoot="`overshoot'")

    * ---- returned results -------------------------------------
    * r(varlist) is the one that changes how the
    * command can be used: -regress y `r(varlist)'- and loops over
    * several k stop needing hand-written variable names.
    local created "`eqp_varlist'"
    quietly count if `touse'
    local n_origins = r(N)
    local n_missing = 0
    if "`created'" != "" {
        local first : word 1 of `created'
        quietly count if missing(`first') & `touse'
        local n_missing = r(N)
    }

    display as result "equipop: done - " ///
        "`: word count `created'' new variables, " ///
        "`n_origins' rows in sample, `n_missing' without results"

    return local cmd     "equipop"
    return local cmdline `"equipop `0'"'
    return local varlist "`created'"
    return local treat   "`treat'"
    return local k       "`k'"
    return local r       "`r'"
    return scalar unit      = `unit'
    return scalar selfpot   = `selfpot'
    return scalar N_origins = `n_origins'
    return scalar N_missing = `n_missing'
    if "`eqp_crs'" != "" {
        return local crs "`eqp_crs'"
        return scalar epsg = `eqp_epsg'
    }
end


* -equipop doctor- lives in its own program so that it carries no
* syntax of its own and can be called before anything is parsed.
* -equipop setup- installs the calculating engine into the Python
* Stata is using. The .ado files arrive by net install; the engine
* only ever arrives by pip, and getting it into the RIGHT Python is
* the step that goes wrong. This does it from inside Stata, so the
* interpreter cannot be guessed at.
program define _equipop_setup
    version 17
    syntax [, REPAIR]
    python: _equipop_setup_py("`repair'")
end

program define _equipop_doctor
    version 17
    * The .ado files' own version, so the doctor can notice when the
    * commands and the Python engine have drifted apart - the single
    * most frequent field failure this project has. This is a SEVENTH
    * place a version string lives; tests/test_stata_ado.py asserts it
    * against line 1 of this file and against pyproject.toml.
    local eqp_ado_version "1.44.3"
    python: _equipop_doctor_py("`eqp_ado_version'")
end

version 17
python:
# --- thin sfi glue; all computation lives in equipop.stata_bridge ----
# Keep this block as SMALL as possible. Code in here can only be run
# by Stata, so the Python test suite cannot reach it - which is how
# and 173 survive. Everything that can live in the package does.
# What must stay here is READ by tests/test_stata_ado.py.
from sfi import Data, Macro, SFIToolkit
import sys
import numpy as np


def _wrap_for_stata(text, width=72):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


def _decay_spec(model, half_life):
    """Build the engine's Decay object, or None for no decay.

    A variable bandwidth passes its own half-life per row, so the
    single number here is only the fixed case; the engine takes the
    model from this object either way.
    """
    if not model:
        return None
    from equipop.decay import Decay
    return Decay(model=model,
                 half_life_m=(float(half_life) if half_life > 0
                              else 1.0))


def _col(v):
    a = np.array(Data.get(v), dtype=float)
    a[a > 8.9e307] = np.nan          # Stata missings arrive huge
    return a


def _equipop_machine1(*, x, y, treat, k="", r="", unit=100.0,
                      weight="", selfpot=1.0, touse="", prefix="",
                      project="", epsg=0, treatmode="counts",
                      missing="", decay="", halflife=0.0,
                      halflifevar="", bins=10, overshoot=""):
    # KEYWORD-ONLY on purpose: a positional call raises TypeError
    # rather than quietly meaning something else.
    try:
        from equipop.stata_bridge import (knn_to_rows, to_stata_values,
                                          project_for_stata,
                                          degrees_warning,
                                          zone_span_warning)
    except ImportError:
        SFIToolkit.errprintln(
            "equipop is not installed in Stata's Python. Check which "
            "Python with -python query-, then install into THAT one. "
            "See help equipop.")
        SFIToolkit.error(198)
        return

    xs, ys = _col(x), _col(y)

    # Projection happens HERE, on the way in: the engine below receives
    # metric coordinates and knows nothing about degrees.
    if project:
        try:
            east, north, code, crs = project_for_stata(
                xs, ys, epsg=(int(epsg) or None))
        except Exception as exc:
            SFIToolkit.errprintln(str(exc).splitlines()[0])
            SFIToolkit.error(198)
            return
        # Computed on the DEGREES, so it must happen before xs and ys
        # are replaced by the projected values.
        span_note = zone_span_warning(xs, ys, epsg=code)
        xs, ys = east, north
        print(f"equipop: projected to {crs}")
        if span_note:
            SFIToolkit.displayln("")
            for line in _wrap_for_stata(span_note):
                SFIToolkit.displayln(line)
            SFIToolkit.displayln("")
        Macro.setLocal("eqp_epsg", str(code))
        Macro.setLocal("eqp_crs", crs)
    else:
        warning = degrees_warning(xs, ys)
        if warning:
            SFIToolkit.displayln("")
            for line in _wrap_for_stata(warning):
                SFIToolkit.displayln(line)
            SFIToolkit.displayln("")

    treats = {v: _col(v) for v in treat.split()} if treat.strip() else None
    ks = [int(t) for t in k.split()] or None
    rs = [float(t) for t in r.split()] or None
    w = _col(weight) if weight else None

    # A refusal from the bridge is a MESSAGE, not a traceback. An
    # uncaught exception here shows a Python stack to a Stata user,
    # who cannot act on it and cannot tell our fault from theirs.
    try:
        res = knn_to_rows(xs, ys, ks, treat=treats, weight=w,
                          unit_size=float(unit), r_values=rs,
                          self_potential=float(selfpot),
                          treat_are_counts=(treatmode != "flags"),
                          missing_codes=[float(c)
                                         for c in missing.split()],
                          decay=_decay_spec(decay, halflife),
                          decay_half_life=(_col(halflifevar)
                                           if halflifevar else None),
                          decay_bins=int(bins),
                          overshoot_mode=(overshoot or None))
    except ValueError as exc:
        for line in _wrap_for_stata(str(exc)):
            SFIToolkit.errprintln(line)
        SFIToolkit.error(198)
        return

    # [if] [in]: computed for everyone, REPORTED for the sample.
    keep = _col(touse) > 0 if touse else None

    existing = [Data.getVarName(i) for i in range(Data.getVarCount())]

    # PREFLIGHT. Every intended name is
    # checked BEFORE any variable is created. Until 1.38 the check ran
    # inside the writing loop, so a collision or an over-long name on
    # the tenth variable left nine already in the dataset - a run that
    # stopped with an error and changed the data anyway. prefix() was
    # only tested against "N_1", which proves nothing about
    # T_<longvariablename>_100.
    wanted = [prefix + name for name in res]
    problems = []
    for name in wanted:
        if len(name) > 32:
            problems.append(
                f"{name} is {len(name)} characters - Stata allows 32. "
                f"Use a shorter prefix() or shorter treatment variable "
                f"names.")
        elif name in existing:
            problems.append(
                f"{name} already exists - use option replace")
    seen = set()
    for name in wanted:
        if name in seen:
            problems.append(f"{name} would be created twice")
        seen.add(name)
    if problems:
        SFIToolkit.errprintln("no variables were created:")
        for line in problems[:10]:
            for part in _wrap_for_stata("  " + line):
                SFIToolkit.errprintln(part)
        if len(problems) > 10:
            SFIToolkit.errprintln(f"  ... and {len(problems) - 10} more")
        SFIToolkit.error(110)
        return

    made = []
    for name, arr in res.items():
        name = prefix + name
        vals = np.asarray(arr, dtype=float)
        if keep is not None:
            vals = np.where(keep, vals, np.nan)
        Data.addVarDouble(name)
        Data.store(name, None, to_stata_values(vals))
        made.append(name)

    Macro.setLocal("eqp_varlist", " ".join(made))


def _equipop_setup_py(repair=""):
    # Standard library ONLY, and deliberately so: this runs BEFORE the
    # package exists, on a machine where the whole point is that
    # nothing is installed yet. It must not import the thing it is
    # about to install.
    import subprocess
    import sys

    args = ["--user", "--upgrade"]
    if repair:
        # The Mac case, and the Anaconda case: the libraries are
        # present but built for the wrong processor, or shadowed by
        # another copy. --no-cache-dir is not decoration - without it
        # pip reuses the wrong wheel it already downloaded and the
        # repair appears not to work.
        args += ["--force-reinstall", "--no-cache-dir",
                 "--only-binary=:all:", "numpy", "scipy", "pandas"]
    args.append("equipop")
    cmd = [sys.executable, "-m", "pip", "install"] + args

    print("EquiPop setup")
    print("  installing into the Python Stata is using:")
    print("     " + sys.executable)
    print("  command:")
    print("     " + " ".join(cmd))
    print("")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as exc:
        print("  could not run pip at all: " + str(exc).splitlines()[0])
        return
    tail = (p.stdout or "").strip().splitlines()[-12:]
    for line in tail:
        print("  " + line)
    if p.returncode != 0:
        print("")
        print("  PIP FAILED. The message above is pip's own:")
        for line in (p.stderr or "").strip().splitlines()[-8:]:
            print("     " + line)
        print("  If it mentions an externally managed environment, "
              "this is")
        print("  Apple's or the system's own Python and is not ours to "
              "change.")
        print("  Install a plain Python from python.org, point Stata at "
              "it with")
        print("     python set exec \"THE_PATH_TO_THAT_PYTHON\", "
              "permanently")
        print("  restart Stata, and run -equipop setup- again.")
        return

    print("")
    print("  Done. Now QUIT STATA COMPLETELY, start it again, and run:")
    print("     equipop doctor")
    # NOT run here on purpose. Python starts once per Stata session and
    # keeps whatever it loaded first, so after an upgrade the doctor
    # would report the version that is still in memory - the OLD one -
    # and say everything matches when it does not.


def _equipop_doctor_py(ado_version=""):
    # The report prints itself, line by line, flushing as it goes.
    # That is deliberate: if a compiled library takes the whole Stata
    # process down mid-report - which is what a second copy of the
    # maths library does on Windows - the lines already on screen are
    # the only evidence there will be.
    #
    # Since 1.37 the package no longer loads numpy, pandas or scipy on
    # import, so this report can still be produced on a machine where
    # those three are exactly what is broken. That was not possible
    # before, and it is the case the doctor was written for.
    try:
        from equipop.doctor import run
    except Exception as exc:
        print("EquiPop doctor could not load the package:")
        print("   " + str(exc).splitlines()[0])
        print("   Python running Stata: " + sys.executable)
        print("   Install equipop into THAT Python, then restart Stata.")
        return
    run(ado_version=ado_version)
end
