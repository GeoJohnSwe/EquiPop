*! equipop v1.64.1  -  k-nearest neighbour context variables via EquiPop
*! Machine 1 (Counts and Shares). Adds, per requested k:
*!   N_<k>, Dist_<k>, and per treatment variable v: T_<v>_<k>, R_<v>_<k>
*! row-aligned to the dataset in memory. Radii r() give the same
*! columns named _r<r>. treat() is optional; without it you get the
*! neighbourhood size and reach alone.
*!
*! Requires Stata 17+, Python 3.11+ configured (python query), and the
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
    * ---- -equipop help- (JOHN'S FIELD REPORT, 10 OCTOBER 2026) --
    * He typed `equipop help' and got `unknown subcommand: help' with
    * a list that did not include it - the one word a confused user
    * reaches for, refused by the thing they were asking for help
    * about. Stata's own convention is `help equipop', which is why
    * this was never written; it is also not what somebody types when
    * the command has just told them they got a subcommand wrong.
    * One line, and the error it replaces was the worst-timed message
    * in the program.
    if `"`eqp_sub'"' == "help" {
        * CAPTURED, because a partial install is the case this would
        * otherwise fail confusingly in: the .ado files present and
        * equipop.sthlp missing gives Stata's own "help for equipop
        * not found", which reads as though the command is not
        * installed at all. The remedy is the same net install line
        * the unknown-subcommand branch prints, so say so.
        capture help equipop
        if _rc {
            display as error "the help file is not installed - " ///
                "equipop.sthlp is missing"
            display as text "  The commands are here and their help " ///
                "is not, which means a partial"
            display as text "  install. Reinstall both:"
            display as text "     ssc install equipop, replace"
            display as text "  or, for the development version:"
            display as text `"     net install equipop, from("https://raw.githubusercontent.com/GeoJohnSwe/EquiPop/main/stata") replace"'
            exit 601
        }
        exit
    }
    if `"`eqp_sub'"' == "doctor" {
        _equipop_doctor
        exit
    }
    if `"`eqp_sub'"' == "setup" {
        _equipop_setup `eqp_rest'
        exit
    }
    * ---- -equipop unit- (BACKLOG 385) --------------------------
    * John, 9 October 2026: "is there a cheap way to determine the
    * average nearest neighbour or similar - that would enable us to
    * recommend a unit size?" A read-only report, like the doctor, and
    * like the doctor it must not be made to supply the mandatory
    * options of a real run. It changes NOTHING: the unit stays
    * whatever the user sets or inherits.
    if `"`eqp_sub'"' == "unit" {
        _equipop_unit `eqp_rest'
        * A subcommand of an rclass program has to hand its own r()
        * up, or the caller sees an empty r() and the documented
        * results do not exist. -return add- is the whole mechanism.
        return add
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
        display as text "  equipop unit    - what cell size does " ///
            "this data want?"
        display as text "  equipop help    - open this command's " ///
            "help file"
        display as text ""
        display as text "  If you typed one of those and Stata does " ///
            "not know it, the"
        display as text "  command files here are older than the " ///
            "subcommand. Update them:"
        * v1.48.2. THIS USED TO NAME A RAW GITHUB URL ONLY, and it is
        * printed at the exact moment a confused user is reading
        * carefully. SSC is where a Stata user expects to update from,
        * and adoupdate only knows about packages installed from a
        * site - so SSC goes first. The GitHub line stays as the
        * development route, and as the answer while an SSC update is
        * still propagating.
        display as text "     ssc install equipop, replace"
        display as text "  or, for the development version:"
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
            Unit(string) POP(varname numeric) PREFIX(string) ///
            SELFpot(real 1) PROJect EPSG(integer 0) ///
            TREATmode(string) MISSing(numlist) ///
            DECAY(string) HALFlife(real 0) HALFlifevar(varname numeric) ///
            SELFPOTName(string) ///
            BINS(integer 10) OVERshoot(string) ///
            ORIGINrule(string) CALibration(string) REPLACE]

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

    * ---- what the half-life MEANS  (BACKLOG 317) ---------------
    * Östh, Lyhagen and Reggiani (2016) name two readings and
    * advocate the first; old EquiPop used it, and 1.30-1.47 had
    * silently switched to the second. halflife is the default again.
    *   halflife  half of all trips are shorter than halflife()
    *             - use for a survey median
    *   halfprob  a neighbour at halflife() counts half as much
    * They coincide for negexp. power has no half-life, only halfprob.
    local calibration = lower(strtrim("`calibration'"))
    if "`calibration'" != "" {
        if "`decay'" == "" {
            display as error "calibration() says what halflife() " ///
                "means, so it needs decay() as well"
            exit 198
        }
        if inlist("`calibration'", "halflife", "half-life", "hl", "life", "median") {
            local calibration "half-life"
        }
        else if inlist("`calibration'", "halfprob", "half-probability", "hp", "probability") {
            local calibration "half-probability"
        }
        else {
            display as error "calibration() must be halflife or halfprob"
            display as text "  halflife  half of all trips are shorter " ///
                "than halflife() - use for a survey median (default)"
            display as text "  halfprob  a neighbour at halflife() " ///
                "counts half as much"
            exit 198
        }
    }
    else if "`decay'" != "" {
        local calibration "half-life"
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

    * ---- is the origin its own neighbour? (BACKLOG 290) ----------
    * John's ruling, 1.47: two rules, and `include` stays the default
    * because it is the rule EVERY PUBLISHED EquiPop number used -
    * his own 2015 Geographical Analysis paper included. Flipping it
    * silently would change results with no message saying why.
    *
    * Accepted here in the two spellings a Stata user reaches for.
    * "i=j" cannot be typed as an option value without quoting, so
    * the words are what the help documents.
    * ONE READER, called by the subcommand too (review F1). The
    * aliases and the refusal used to live here only, so
    * `equipop unit' accepted any string at all - and after 1.54.1
    * the rule decides whether the advisory applies, so a typo would
    * have silently selected the include criterion.
    _equipop_originrule `"`originrule'"'
    local originrule "`s(rule)'"

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
    * Any size above zero, fractions included (BACKLOG 445, 1.63.0).
    * From 1.29.8 to 1.62.1 a fractional size was REFUSED here and in
    * QGIS and Pro, because the core turned cell centres into whole
    * numbers - a requested 2.5 gave centres 1, 3, 6. Centres are now
    * exact and no engine rounds a size, so the same town in 2.5 m
    * cells gives what it gives in 100 m cells, scaled. The rule is
    * the same at every door, as 172 taught.
    * BACKLOG 385. unit() used to be -Unit(real 100)-, which cannot
    * tell `unit(100)' from a user who said nothing: both arrive as
    * 100. The unit-size advisory has to know the difference, because
    * a size the user CHOSE is theirs and a size they merely inherited
    * is worth a word. So the option is read as a string and defaulted
    * here, where the fact can be recorded. `r(unit)' is unchanged.
    local unit_was_set 1
    if `"`unit'"' == "" {
        local unit_was_set 0
        local unit 100
    }
    else {
        capture confirm number `unit'
        if _rc {
            display as error "unit() is the cell size in metres and " ///
                "must be a number"
            exit 198
        }
    }
    * missing() first (BACKLOG 451): Stata's . compares GREATER than
    * every number, so a bare <= 0 lets unit(.) through.
    if missing(`unit') | `unit' <= 0 {
        display as error "unit() is the cell size and must be " ///
            "greater than zero"
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

    * ---- replace: NOTHING IS DROPPED HERE (BACKLOG 473) ---------
    * Until 1.63.7 this block ran -capture drop- on every name the run
    * was about to write, before computing anything. Two faults:
    *
    * ABBREVIATION. With -set varabbrev on-, Stata's default, -drop
    * N_100- deletes N_1000 when no N_100 exists - it reads the name
    * as an abbreviation. So -equipop ..., k(100) replace- on a dataset
    * holding the results of k(1000) deleted N_1000 and Dist_1000, and
    * a treat() variable could take a user's own variables with it
    * (T_Age_25 is an abbreviation of T_Age_250).
    *
    * ORDER. The old results were gone before the new ones existed, so
    * a run that stopped - a refused option, a full disk, Break - left
    * the dataset with neither.
    *
    * The Python half now replaces: after the engine has answered, it
    * drops EXACTLY the variables it is about to write, by position in
    * the dataset, and only those that exist under that very name.
    * (The blocks about decay and r() that stood here - BACKLOG 336,
    * 337 - guessed the engine's names; the engine's own list cannot
    * be guessed wrong.)

    * ---- WARN ABOUT LONG NAMES BEFORE COMPUTING ANYTHING -------
    * John's run finished 646,766 cells, three widened passes and two
    * k values before stopping on a 33-character name. The engine
    * cannot be reached from here to know every column it will make,
    * but the LONGEST one is predictable: prefix + the longest treat
    * variable + "_" + the largest k. Saying so first costs nothing
    * and saves the run.
    if "`treat'" != "" {
        local _longest = 0
        foreach v of varlist `treat' {
            if length("`v'") > `_longest' local _longest = length("`v'")
        }
        * BACKLOG 335, MARINA'S PULL REQUEST. `foreach ... of numlist`
        * with an EMPTY argument is a syntax error in Stata, not an
        * empty loop - so -equipop, x() y() r(500) treat(HighEdu)- died
        * with "invalid numlist has too few elements" before computing
        * anything. A radius-only run with a treatment, which is an
        * ordinary thing to ask for.
        * THE GUARD ALREADY EXISTED FORTY LINES ABOVE, in the replace
        * drop block, with a comment explaining this exact property.
        * The rule was written down in this file and not applied below
        * it - the same shape as the version invariant that sat in a
        * comment three files from the code ignoring it (BACKLOG 330).
        local _bigk = 0
        if "`k'" != "" {
            foreach kk of numlist `k' {
                if `kk' > `_bigk' local _bigk = `kk'
            }
        }
        local _need = length("`prefix'") + 2 + `_longest' ///
            + 1 + length("`_bigk'")
        if `_need' > 32 {
            display as text "[equipop] names will exceed Stata's 32 " ///
                "characters (about `_need') and will be SHORTENED - " ///
                "every rename is listed when the variables are made."
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
        overshoot="`overshoot'", originrule="`originrule'",           ///
        calibration="`calibration'", unit_was_set=`unit_was_set',    ///
        replace="`replace'")

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
    * BACKLOG 317: which kernel actually ran, so a do-file can check
    * it rather than a reader having to trust the log. calibration is
    * what was APPLIED - power asked for halflife still reports
    * half-probability, because that is what it used.
    if "`decay'" != "" {
        return local decay       "`decay'"
        return local calibration "`eqp_calibration'"
        return scalar halflife   = `halflife'
        return scalar beta       = `eqp_beta'
    }
    return scalar N_origins = `n_origins'
    return scalar N_missing = `n_missing'
    * BACKLOG 293. The two settings that move every k-based number and
    * were recorded NOWHERE until now - overshoot since 1.30, the
    * origin rule since 1.47. The EFFECTIVE value, so an unset option
    * returns the default that actually ran rather than an empty
    * string. r(provenance) is the run id printed in the note above,
    * so a log and a do-file can be matched to each other.
    return local overshoot   "`eqp_overshoot'"
    return local originrule  "`eqp_originrule'"
    return local provenance  "`eqp_provenance'"
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
    * BACKLOG 196. The ado's own version, for the record and for the
    * doctor. Maintained by tools/bump_version.py, which replaces
    * every line matching this pattern - so this string and the
    * doctor's below always agree.
    local eqp_ado_version "1.64.1"

    * BACKLOG 332. THE ENGINE FLOOR IS NOT THE ADO'S VERSION, and
    * tying the two together was the whole fault. Setup used to ask
    * pip for `equipop>=`the line above, which says "the engine must
    * be as new as this release" - and that is not a dependency, it is
    * a release number pretending to be one. Two consequences, both
    * real:
    *
    *   1.49.2 touched the ArcGIS toolbox and nothing else, and
    *   silently raised the Stata engine floor to 1.49.2. The commands
    *   did not need it.
    *
    *   And whenever the commands reach SSC before the engine reaches
    *   PyPI, pip is asked for a version that does not exist and the
    *   install FAILS OUTRIGHT - at the first instruction in the
    *   paper, for every new reader.
    *
    * THE HONEST FLOOR IS THE OLDEST ENGINE THAT SATISFIES THE CALLS
    * THIS FILE MAKES. It is maintained BY HAND - bump_version.py must
    * never touch it - and raised only when the commands start calling
    * something new, and only after that engine is on PyPI. Then the
    * floor can never name an engine that is not there.
    *
    * WHAT SETS IT TODAY, newest requirement last:
    *   equipop.stata_bridge   knn_to_rows, to_stata_values,
    *                          project_for_stata, degrees_warning,
    *                          zone_span_warning        - long-standing
    *   equipop.doctor.run(ado_version=)                - 1.40.1
    *   equipop.decay.Decay(calibration=)               - 1.48.0
    * So: 1.48.0. If you add a call to something newer, raise this AND
    * say which call did it. tests/test_stata_python_block.py checks
    * that every name this file imports from the engine still exists.
    local eqp_min_engine "1.48.0"
    python: _equipop_setup_py("`repair'", "`eqp_ado_version'", "`eqp_min_engine'")
    * AND A FAILURE IS NOW A FAILURE. It used to print "PIP FAILED"
    * and return normally, so a scripted or institutional install had
    * no code to act on.
    if "`eqp_setup_failed'" != "" {
        exit 601
    }
end

program define _equipop_doctor
    version 17
    * The .ado files' own version, so the doctor can notice when the
    * commands and the Python engine have drifted apart - the single
    * most frequent field failure this project has. This is a SEVENTH
    * place a version string lives; tests/test_stata_ado.py asserts it
    * against line 1 of this file and against pyproject.toml.
    local eqp_ado_version "1.64.1"
    * BACKLOG 332. The floor is what the doctor should JUDGE against;
    * the two version numbers are only there to be shown. Keep this
    * string identical to the one in _equipop_setup above - a test
    * asserts it, because a floor that setup and the doctor disagree
    * about is worse than no floor.
    local eqp_min_engine "1.48.0"
    * BACKLOG 385, A DELIBERATE DECISION NOT TO RAISE THIS. The
    * commands now call equipop.unitsize, which is new in 1.54.0 - and
    * the floor stays at 1.48.0 anyway, for the reason already written
    * three lines above the r() block in the main program: an ado must
    * never break on an engine older than itself when the only loss is
    * a line of the report. On a 1.53.4 engine machine 1 is perfect
    * and the advisory is simply absent, because every door calls it
    * inside a catch; `equipop unit' says in one sentence which
    * version it needs. Raising the floor would instead make the
    * doctor scold every user whose engine predates an ADVISORY, and
    * make `equipop setup' demand a version PyPI may not have yet -
    * which is BACKLOG 331 exactly.
    python: _equipop_doctor_py("`eqp_ado_version'", "`eqp_min_engine'")
end

* ---- -equipop unit- (BACKLOG 385) ------------------------------
* "knowing the unit size is a battle between computing time and
* detail" - John, 9 October 2026. This is the scoreboard for that
* battle, and nothing more: it reports and it never sets.
*
* THE WHOLE CALCULATION IS IN THE ENGINE (equipop/unitsize.py). This
* program reads two variables and prints what it is handed. A door
* that computes its own numbers is a door that can disagree with the
* other three, which this project has now shipped five times -
* BACKLOG 353, 368, 373, 380.
* ---- one origin-rule reader for every entry point --------------
* Review F1. sreturn rather than a macro, so the caller cannot read a
* stale value when the helper exits early.
program define _equipop_originrule, sclass
    version 17
    args raw
    sreturn clear
    local rule `"`raw'"'
    * The two spellings a Stata user reaches for. "i=j" cannot be
    * typed as an option value without quoting, so the words are what
    * the help documents.
    if `"`rule'"' == "i=j" | `"`rule'"' == "i==j"   local rule "include"
    if `"`rule'"' == "i!=j" | `"`rule'"' == "i ne j" local rule "exclude"
    if !inlist(`"`rule'"', "", "include", "exclude") {
        display as error "originrule() must be include or exclude"
        display as text "  include (the default) counts the origin's " ///
            "own cell as part of its neighbourhood, as every " ///
            "published EquiPop result does."
        display as text "  exclude leaves it out - the w(ii)=0 " ///
            "convention that spatial regression needs. Results " ///
            "under the two are NOT comparable."
        exit 198
    }
    sreturn local rule "`rule'"
end

program define _equipop_unit, rclass
    version 17
    syntax varlist(min=2 max=2 numeric) [fweight] [if] [in] ///
        [, POP(varname numeric) K(numlist integer >0) ///
           CANDidates(numlist >0) TOLerance(real 0.01) ///
           ORIGINrule(string) NOCACHE]

    * [fweight=var] AND pop(var) BOTH, resolved into one name exactly
    * as the main command does it, and for the reason in the note
    * beside that code: a Stata user whose data is already fweighted
    * must not have to learn a second spelling to ask a question
    * about it.
    *
    * FOUND BY WRITING THE FIELD DO-FILE, not by reading the code.
    * Block 23 uses the fweight form because that is how every other
    * example in this project is written, and the first version of
    * this syntax line took no weight at all - so the block would
    * have died on `weights not allowed' in John's hands.
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

    gettoken eqp_x eqp_y : varlist
    marksample touse
    markout `touse' `eqp_x' `eqp_y' `wvar'
    quietly count if `touse'
    if r(N) == 0 {
        display as error "no observations with usable coordinates"
        exit 2000
    }

    * The k the advice is ABOUT. There is no useful default here that
    * is not a guess, and the whole point is that the answer depends
    * on k - so 100 is named out loud rather than assumed in silence.
    if "`k'" == "" {
        local k 100
        display as text "(no k() given - advising for k=100; " ///
            "k() takes a numlist)"
    }
    if `tolerance' <= 0 | `tolerance' >= 1 {
        display as error "tolerance() is a share between 0 and 1 - " ///
            "the default 0.01 means 'fewer than one answer in a " ///
            "hundred is estimated rather than measured'"
        exit 198
    }
    * The shared reader, so a typo is refused here exactly as it is
    * on a run - and after 1.54.1 that matters more than it did,
    * because the rule decides whether this criterion applies at all
    * rather than just labelling the output (review F1).
    _equipop_originrule `"`originrule'"'
    local originrule "`s(rule)'"
    if "`originrule'" == "" local originrule "include"

    python: _equipop_unit_py()

    return local cmd      "equipop unit"
    return local cmdline  `"equipop unit `0'"'
    return local k        "`k'"
    return local originrule "`originrule'"
    return scalar tolerance = `tolerance'
    return scalar N         = `eqp_u_points'
    return scalar people    = `eqp_u_people'
    * r(unit) is the RECOMMENDATION for the first k - the one number
    * somebody will want in a loop. Missing when no candidate size
    * serves that k, which is a real answer and not a failure.
    return scalar unit      = `eqp_u_rec'
    return scalar cells     = `eqp_u_cells'
    return scalar estimated = `eqp_u_est'
    return local fingerprint "`eqp_u_fp'"
    * 1 when the saturation criterion applies to the rule in force, 0
    * under originrule(exclude) where it cannot. r(unit) is missing in
    * both the "too dense for any size" case and this one, so without
    * this a script cannot tell them apart (review F1).
    return scalar applies = `eqp_u_applies'
    * Named r(advice) and not r(table): -table- is a Stata command and
    * a matrix called r(table) is, by universal convention, the
    * coefficient table of an estimation command. Borrowing that name
    * for something else would be a trap for every user who knows it.
    return matrix advice = eqp_advice
end

version 17
python:
# --- thin sfi glue; all computation lives in equipop.stata_bridge ----
# Keep this block as SMALL as possible. Everything that can live in
# the package does.
#
# BACKLOG 331. This comment used to end "Code in here can only be run
# by Stata, so the Python test suite cannot reach it - which is how
# and 173 survive", and that sentence was both true and expensive:
# every guard in `equipop setup` was verified by GREPPING THIS FILE
# FOR STRINGS, which is how the 1.48.2 ensurepip test came to assert
# nothing and how a whole branch of pip advice could point the wrong
# way for a release.
#
# It is no longer true. tests/test_stata_python_block.py EXECUTES this
# block with `sfi` stubbed - which works only because everything here
# is standard library, as the setup function's own comment requires -
# and calls these functions with pip's real output, reading the advice
# back from what was PRINTED. Keep it that way: an import of numpy,
# pandas or the equipop package at the top of a setup path would put
# this block back out of reach and take its tests with it.
#
# tests/test_stata_ado.py still READS the file, for the Stata half -
# the syntax line, the macros, the option names - which no stub can
# exercise.
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
# BACKLOG 459. NO import of numpy HERE, whatever the comment above has
# not stopped before. Stata runs this block when it LOADS the file, so
# an import that fails here fails every subcommand at once - doctor and
# setup included, the two written for the machine where it fails. Kit
# Baum, testing the SSC submission of 1.63.1 on a Mac, got
#     ModuleNotFoundError: No module named 'numpy'
#     (error occurred while loading equipop.ado)  r(7102);
# from -equipop doctor-: Stata had picked Apple's own Python 3.9.6.
# numpy is now imported inside the two functions that compute, and
# tests/test_stata_block_without_numpy.py loads this block with numpy,
# pandas, scipy and equipop hidden.


# BACKLOG 459. The engine's floor is Python 3.11 (pyproject's
# requires-python; tests/test_stata_block_without_numpy.py keeps the
# two equal). On 3.10 pip still finds engine 1.61.0, the last that
# allowed it, and these commands run on it (their floor is
# eqp_min_engine), so 3.10 is a legacy path: a warning, once per Stata
# session on an ordinary run, and the run goes on. Below 3.10 pip finds
# no engine at all and this release's code would not import, so the
# only useful thing is to say what to do. Standard library only.
_PY_ENGINE_FLOOR = (3, 11)
_PY_FLOOR_TEXT = ".".join(str(p) for p in _PY_ENGINE_FLOOR)
_PY_LAST_ENGINE = {(3, 10): "1.61.0"}
# Review of 1.63.2, F4. A list rather than a flag so no -global- is
# needed. Stata keeps one Python per session, so this lasts exactly as
# long as the warning should be remembered.
_PY_NOTED = []

# BACKLOG 461. THE WHOLE WAY OUT, IN WORDS, AND A LOOK FOR A PYTHON THAT
# IS ALREADY THERE. After 1.63.2 the advice to a user on Apple's 3.9 was
# "install Python 3.11 or newer from python.org" and four lines of
# Stata - correct, and too little for someone who has never installed
# a Python (John, 6 November 2026: "if we lose Mac users because of
# their unexperience with python - I think it is our loss"). Two
# changes. FIRST, many machines already have a usable Python that
# Stata simply did not pick, so the places installers put Python are
# searched, each Python found is started and asked what it is, and the
# best one is named with the exact line to type. SECOND, when there is
# none, the steps say which page to open, which button to press, what
# the installer will ask and the exact path to type afterwards.
#
# Never suggested: Apple's own (too old, and on a Mac without the
# developer tools /usr/bin/python3 opens an installer dialog instead of
# running, so it is not even started); Anaconda and its relatives
# (README_STATA.md: two copies of the maths library close Stata);
# Pythons that belong to another program (ArcGIS Pro, QGIS) and the
# Windows Store shortcuts (starting one can open the Store). A Python
# that pip may not install into - Homebrew's, a Linux distribution's,
# "externally managed" - is suggested through a virtual environment of
# EquiPop's own, made from it.
#
# The version to install when there is nothing: 3.13. python.org still
# has ordinary installers for it on Mac and Windows (on Windows 3.14
# and newer are offered through a new install manager), the scientific
# libraries support it for years, and its install path is fixed, so
# the line to type can be given exactly.
_PY_GET = "3.13"
# One search per Stata session: it starts every Python it finds.
_PY_FOUND = []
# Started at most, so a machine with dozens of environments does not
# keep the doctor waiting.
_PY_PROBE_MAX = 12
# What a found Python is asked. Built with chr(10): a backslash in this
# block is one more thing Stata could read before Python does.
_PY_PROBE = chr(10).join([
    "import os, platform, struct, sys, sysconfig",
    "v = sys.version_info",
    "venv = sys.prefix != getattr(sys, 'base_prefix', sys.prefix)",
    "shared = bool(sysconfig.get_config_var('Py_ENABLE_SHARED')",
    "              or sysconfig.get_config_var('PYTHONFRAMEWORK')",
    "              or os.name == 'nt')",
    "em = (not venv) and os.path.exists(os.path.join(",
    "    sysconfig.get_path('stdlib'), 'EXTERNALLY-MANAGED'))",
    "try:",
    "    from importlib.metadata import version",
    "    eng = version('equipop')",
    "except Exception:",
    "    eng = ''",
    "print('EQP|%d.%d.%d|%d|%d|%d|%d|%s|%s' % (v[0], v[1], v[2],",
    "      shared, em, venv, struct.calcsize('P') * 8,",
    "      platform.machine(), eng))",
])
# (piece of the path, lower case) -> why it is not suggested. Checked
# before anything is started.
_PY_PASSED_OVER = [
    ("anaconda", "Anaconda - Stata and Anaconda do not mix"),
    ("miniconda", "Anaconda - Stata and Anaconda do not mix"),
    ("miniforge", "Anaconda - Stata and Anaconda do not mix"),
    ("mambaforge", "Anaconda - Stata and Anaconda do not mix"),
    ("windowsapps", "a Windows Store shortcut"),
    ("arcgis", "belongs to ArcGIS Pro"),
    ("qgis", "belongs to QGIS"),
    ("osgeo4w", "belongs to QGIS"),
    ("/library/developer/", "Apple's own Python, too old"),
    ("xcode.app", "Apple's own Python, too old"),
]


def _python_level():
    """'ok', 'warn' or 'stop' for the Python Stata is using. Cheap."""
    ver = sys.version_info[:2]
    if ver >= _PY_ENGINE_FLOOR:
        return "ok"
    if ver in _PY_LAST_ENGINE:
        return "warn"
    return "stop"


def _python_problem():
    """(level, the lines that say what is wrong) - no search."""
    level = _python_level()
    if level == "ok":
        return "ok", []
    have = ".".join(str(p) for p in sys.version_info[:3])
    exe = sys.executable or "(unknown)"
    if level == "warn":
        last = _PY_LAST_ENGINE[tuple(sys.version_info[:2])]
        return "warn", [
            f"Stata is using Python {have}. The newest EquiPop engine "
            f"for it is {last}:",
            "   these commands run on it, but later engines need "
            f"Python {_PY_FLOOR_TEXT} or newer.",
            "   Python 3.10 itself stopped receiving fixes in October "
            "2026.",
        ]
    lines = [
        f"EquiPop needs Python {_PY_FLOOR_TEXT} or newer, and Stata is "
        f"using Python {have}:",
        "   " + exe,
    ]
    if sys.platform == "darwin" and (
            "CommandLineTools" in exe or "Xcode" in exe
            or exe.startswith("/usr/bin/")):
        # BACKLOG 461: no longer "install a newer Python beside it" -
        # the search below may well find one already there.
        lines += [
            "   That is the Python that comes with Apple's developer "
            "tools. Leave it",
            "   alone; Stata only needs to be pointed at a newer one.",
        ]
    return "stop", lines


def _python_check(min_engine="", advise=True):
    """('ok' | 'warn' | 'stop', lines to print) for this Python: what
    is wrong and, with advise, what to do about it."""
    level, lines = _python_problem()
    if level == "ok" or not advise:
        return level, lines
    return level, lines + _python_advice(min_engine)


# ---- BACKLOG 461: the search ------------------------------------------
def _py_home():
    import os
    return os.path.expanduser("~")


def _py_is_windows():
    return sys.platform.startswith("win")


def _py_own_venv():
    """The folder EquiPop's own virtual environment is made in."""
    import os
    return os.path.join(_py_home(), "equipop-python")


def _py_venv_python(venv):
    import os
    if _py_is_windows():
        return os.path.join(venv, "Scripts", "python.exe")
    return os.path.join(venv, "bin", "python")


def _python_patterns():
    """Where installers put Python on this platform, as glob patterns,
    EquiPop's own environment first. Conda's places are listed only so
    the report can say why they were passed over."""
    import os
    j, home = os.path.join, _py_home()
    own = _py_venv_python(_py_own_venv())
    conda = ["anaconda3", "miniconda3", "miniforge3", "mambaforge"]
    if sys.platform == "darwin":
        return ([own,
                 "/usr/local/bin/python3.1[0-9]",              # python.org
                 "/opt/homebrew/bin/python3.1[0-9]",           # Homebrew
                 "/Library/Frameworks/Python.framework/Versions/"
                 "3.*/bin/python3.1[0-9]",
                 j(home, ".pyenv", "versions", "3.*", "bin", "python3"),
                 j(home, ".local", "share", "uv", "python", "cpython-3.*",
                   "bin", "python3")]
                + [j(home, c, "bin", "python") for c in conda]
                + [j(home, "opt", "anaconda3", "bin", "python"),
                   "/opt/anaconda3/bin/python", "/opt/miniconda3/bin/python"])
    if _py_is_windows():
        env = os.environ.get
        local = env("LOCALAPPDATA") or j(home, "AppData", "Local")
        progs = env("ProgramFiles") or j("C:" + os.sep, "Program Files")
        return ([own,
                 j(local, "Programs", "Python", "Python3*", "python.exe"),
                 j(local, "Python", "pythoncore-3.*", "python.exe"),
                 j(progs, "Python3*", "python.exe"),
                 j("C:" + os.sep, "Python3*", "python.exe")]
                + [j(home, c, "python.exe") for c in conda]
                + [j(env("ProgramData") or "", c, "python.exe")
                   for c in conda if env("ProgramData")])
    return ([own,
             "/usr/bin/python3.1[0-9]",
             "/usr/local/bin/python3.1[0-9]",
             j(home, ".pyenv", "versions", "3.*", "bin", "python3"),
             j(home, ".local", "share", "uv", "python", "cpython-3.*",
               "bin", "python3")]
            + [j(home, c, "bin", "python") for c in conda])


def _python_registry():
    """Windows: the Pythons python.org's installers registered (PEP
    514). Empty anywhere else, and on any error."""
    try:
        import winreg
    except ImportError:
        return []
    import os
    out = []
    root = chr(92).join(["Software", "Python", "PythonCore"])
    view = winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0)
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            key = winreg.OpenKey(hive, root, 0, view)
        except OSError:
            continue
        i = 0
        while i < 100:
            try:
                tag = winreg.EnumKey(key, i)
            except OSError:
                break
            i += 1
            try:
                sub = winreg.OpenKey(key, tag + chr(92) + "InstallPath",
                                     0, view)
            except OSError:
                continue
            try:
                out.append(winreg.QueryValueEx(sub, "ExecutablePath")[0])
            except OSError:
                try:
                    out.append(os.path.join(
                        winreg.QueryValueEx(sub, "")[0], "python.exe"))
                except OSError:
                    pass
    return out


def _python_candidates():
    """Paths that may be a Python. Cheap: nothing is started here."""
    import glob
    import shutil
    paths = []
    for pattern in _python_patterns():
        paths += sorted(glob.glob(pattern), reverse=True)
    paths += _python_registry()
    for name in ("python3.13", "python3.12", "python3.14", "python3.11",
                 "python3.15", "python3"):
        hit = shutil.which(name)
        if hit:
            paths.append(hit)
    return paths


def _python_passed_over(path):
    """Why a path is not even started, or ''."""
    low = path.lower().replace(chr(92), "/")
    for piece, why in _PY_PASSED_OVER:
        if piece in low:
            return why
    if sys.platform == "darwin" and low.startswith("/usr/bin/"):
        return "Apple's own Python, too old"
    if "/.pyenv/shims/" in low:
        return "a pyenv shortcut"
    return ""


def _probe_python(path):
    """Start one Python and ask it about itself. None if it will not
    say. -E: Stata's own Python settings must not leak into it."""
    import subprocess
    try:
        p = subprocess.run(
            [path, "-E", "-c", _PY_PROBE], capture_output=True, text=True,
            timeout=20,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:
        return None
    for line in (p.stdout or "").splitlines():
        f = line.strip().split("|")
        if f[0] != "EQP" or len(f) != 8:
            continue
        try:
            return {"version": tuple(int(x) for x in f[1].split(".")),
                    "shared": f[2] == "1", "managed": f[3] == "1",
                    "venv": f[4] == "1", "bits": int(f[5]),
                    "machine": f[6], "engine": f[7]}
        except ValueError:
            return None
    return None


def _py_vtext(info):
    return ".".join(str(p) for p in info["version"])


def _py_numbers(text):
    """Leading digits of the first three parts of a version string."""
    nums = []
    for part in str(text).split(".")[:3]:
        d = ""
        for ch in part:
            if not ch.isdigit():
                break
            d += ch
        nums.append(int(d) if d else -1)
    return tuple(nums)


def _py_has_engine(info, min_engine):
    """The EquiPop engine installed in that Python, if it is new enough
    for these commands; '' otherwise."""
    eng = info.get("engine") or ""
    if not eng:
        return ""
    if min_engine and _py_numbers(eng) < _py_numbers(min_engine):
        return ""
    return eng


def _python_unusable(info):
    """Why a Python that started cannot serve Stata, or ''."""
    import platform
    v = info["version"]
    if v[:2] < (3, 10):
        return "too old"
    if v[:2] < _PY_ENGINE_FLOOR:
        last = _PY_LAST_ENGINE.get(tuple(v[:2]), "")
        return "too old for the current engine" + (
            f" (only {last})" if last else "")
    if info["bits"] != 64:
        return "32-bit; Stata needs a 64-bit Python"
    if not info["shared"]:
        return "built without the shared library Stata loads"
    if sys.platform == "darwin":
        mine = platform.machine()
        if info["machine"] and mine and info["machine"] != mine:
            return (f"built for {info['machine']}, and this Stata runs "
                    f"on {mine}")
    return ""


def _find_pythons():
    """[(path, info or None, why not)] for every Python found, once per
    Stata session. 'why not' is '' for one EquiPop can use."""
    if _PY_FOUND:
        return _PY_FOUND[0]
    import os
    here = os.path.realpath(sys.executable) if sys.executable else ""
    seen, found, started = set(), [], 0
    for path in _python_candidates():
        if not path or not os.path.isfile(path):
            continue
        # A virtual environment's python is a link to its base, so the
        # base's real path cannot tell the two apart: key it by place.
        envdir = os.path.dirname(os.path.dirname(os.path.abspath(path)))
        if os.path.isfile(os.path.join(envdir, "pyvenv.cfg")):
            key = os.path.abspath(path)
        else:
            key = os.path.realpath(path)
        if key in seen or key == here:
            continue
        seen.add(key)
        why = _python_passed_over(path)
        if why:
            found.append((path, None, why))
            continue
        if started >= _PY_PROBE_MAX:
            continue
        started += 1
        info = _probe_python(path)
        if info is None:
            found.append((path, None, "did not start"))
        else:
            found.append((path, info, _python_unusable(info)))
    _PY_FOUND.append(found)
    return found


def _python_ranked(found, min_engine=""):
    """The usable ones, best first: one that already has the engine,
    then one pip may install into, then the newest."""
    ok = [(p, i) for p, i, why in found if not why and i]
    ok.sort(key=lambda pi: (0 if _py_has_engine(pi[1], min_engine) else 1,
                            1 if pi[1]["managed"] else 0,
                            tuple(-x for x in pi[1]["version"][:2])))
    return ok


# ---- BACKLOG 461: the steps --------------------------------------------
def _py_step_restart(n):
    how = " (Cmd-Q)" if sys.platform == "darwin" else ""
    return [
        f"  {n}. Quit Stata completely{how} and start it again.",
        "     Python is already running in this session, and Stata will "
        "not switch",
        "     to another Python once it has started.",
    ]


def _py_step_set(n, exe, search=False):
    lines = [f"  {n}. In the new session, BEFORE equipop or any other "
             "Python command, type:"]
    if search:
        lines += ["        python search",
                  "     The new Python should be in the list. Then type:"]
    return lines + [f'        set python_exec "{exe}", permanently']


def _py_step_setup(n, engine=""):
    if engine:
        return [
            f"  {n}. That Python already has the EquiPop engine "
            f"({engine}), so equipop setup",
            "     is not needed. Type:",
            "        equipop doctor",
            "     It should now report no problem with the Python.",
        ]
    return [
        f"  {n}. Then type:",
        "        equipop setup",
        "     It installs the EquiPop engine and the libraries it needs "
        "(numpy,",
        "     pandas, scipy and pyproj) into that Python. It needs the "
        "internet",
        "     and takes a minute or two.",
        f"  {n + 1}. Quit Stata and start it again once more, and type:",
        "        equipop doctor",
        "     It should now report no problem with the Python.",
    ]


def _py_steps_venv(base, intro=True):
    """For a Python pip may not install into: a virtual environment of
    EquiPop's own, made from it."""
    import os
    venv = _py_own_venv()
    exe = _py_venv_python(venv)
    real = os.path.realpath(base).lower()
    owner = ("Homebrew" if "homebrew" in real or "/cellar/" in real
             else "the operating system")
    term = ("Terminal (in Applications > Utilities)"
            if sys.platform == "darwin" else "a terminal")
    lines = []
    if intro:
        lines += [
            f"It belongs to {owner}, which does not let other programs "
            "install into it,",
            "so EquiPop gets a Python of its own made from it (a virtual "
            "environment).",
        ]
    return lines + [
        "What to do (a few minutes, once):",
        f"  1. Open {term} and type this line:",
        f'        "{base}" -m venv "{venv}"',
    ] + _py_step_restart(2) + _py_step_set(3, exe) + _py_step_setup(4)


def _py_steps_install():
    """Nothing usable on this computer: which Python to get, from where,
    and the exact line to type once it is there."""
    import os
    import platform
    head = [
        f"No Python {_PY_FLOOR_TEXT} or newer that Stata can use was "
        "found on this computer,",
        "so one has to be installed. What to do (about ten minutes, "
        "once):",
    ]
    if sys.platform == "darwin":
        exe = (f"/Library/Frameworks/Python.framework/Versions/{_PY_GET}"
               f"/bin/python{_PY_GET}")
        return head + [
            f"  1. Download Python {_PY_GET} from python.org. Open this "
            "page in a browser:",
            "        https://www.python.org/downloads/macos/",
            f'     find the newest "Python {_PY_GET}" release in the list '
            "and click",
            '     "Download macOS installer".',
            "  2. Open the downloaded .pkg file and click Continue, Agree "
            "and Install.",
            "     It asks for your Mac password; that is normal. When it "
            "has finished,",
            "     close the Finder window it opens.",
        ] + (_py_step_restart(3) + _py_step_set(4, exe, search=True)
             + _py_step_setup(5))
    if _py_is_windows():
        arm = platform.machine().upper() in ("ARM64", "AARCH64")
        folder = "Python" + _PY_GET.replace(".", "") + ("-arm64" if arm
                                                        else "")
        local = (os.environ.get("LOCALAPPDATA")
                 or os.path.join(_py_home(), "AppData", "Local"))
        exe = os.path.join(local, "Programs", "Python", folder,
                           "python.exe")
        button = ("Download Windows installer (ARM64)" if arm
                  else "Download Windows installer (64-bit)")
        return head + [
            f"  1. Download Python {_PY_GET} from python.org. Open this "
            "page in a browser:",
            "        https://www.python.org/downloads/windows/",
            f'     find the newest "Python {_PY_GET}" release in the list '
            "and click",
            f'     "{button}".',
            "  2. Run the downloaded file. If you are not an administrator "
            "on this",
            '     computer, untick "Use admin privileges when installing '
            'py.exe" on its',
            '     first screen. Then click "Install Now".',
        ] + (_py_step_restart(3) + _py_step_set(4, exe, search=True)
             + _py_step_setup(5))
    venv = _py_own_venv()
    return head + [
        f"  1. Install Python {_PY_FLOOR_TEXT} or newer and its venv "
        "module with the",
        "     system's package manager, for example on Ubuntu or Debian:",
        "        sudo apt install python3 python3-venv",
        f"     and check in a terminal that  python3 --version  says "
        f"{_PY_FLOOR_TEXT} or newer.",
        "  2. Make a Python of EquiPop's own for Stata, in a terminal:",
        f'        python3 -m venv "{venv}"',
    ] + (_py_step_restart(3) + _py_step_set(4, _py_venv_python(venv))
         + _py_step_setup(5))


def _python_advice(min_engine=""):
    """What to do, after the problem has been stated: the best Python
    already on this computer with the exact steps to move Stata to it,
    or the steps to install one. Then, for whoever reads the report
    later, every other Python found and why it was not chosen."""
    found = _find_pythons()
    ranked = _python_ranked(found, min_engine)
    lines = [""]
    chosen = ""
    if ranked:
        chosen, info = ranked[0]
        lines += [
            "GOOD NEWS: this computer already has a Python that EquiPop "
            "can use:",
            f"   Python {_py_vtext(info)}   {chosen}",
        ]
        if info["managed"]:
            lines += _py_steps_venv(chosen)
        else:
            lines += ["What to do (a few minutes, once):"]
            lines += (_py_step_restart(1) + _py_step_set(2, chosen)
                      + _py_step_setup(3, _py_has_engine(info,
                                                         min_engine)))
    else:
        lines += _py_steps_install()
    others = [(p, i, w) for p, i, w in found if p != chosen]
    if others:
        lines += ["", "Other Pythons on this computer:"]
        for p, i, w in others[:8]:
            if not w:
                w = ("would also do, through a virtual environment"
                     if i["managed"] else "would also do")
            lines.append("   " + p)
            lines.append("      " + (f"Python {_py_vtext(i)}: " if i
                                     else "") + w)
        if len(others) > 8:
            lines.append(f"   and {len(others) - 8} more")
    return lines


def _python_tell(min_engine=""):
    """Doctor and setup: what is wrong, then the search, then what to
    do - printed as it goes, because the search starts every Python it
    finds and can take a few seconds. Returns the level."""
    level, lines = _python_problem()
    for line in lines:
        print(line)
    if level == "ok":
        return level
    print("")
    print("Looking for other Pythons on this computer ...")
    try:
        sys.stdout.flush()
    except Exception:
        pass
    for line in _python_advice(min_engine)[1:]:
        print(line)
    return level


def _python_note_once():
    """Review of 1.63.2, F4: the check for an ordinary run.

    'stop' and its lines - the problem and the whole way out - go back
    to the caller, which refuses the run. 'warn' (Python 3.10) is shown
    here, in short, the first time in a Stata session and never again
    in it: the run works, and a warning on every call would be noise.
    The doctor and setup show it whole. Only 'stop' searches the
    computer (BACKLOG 461); a run that goes on is not kept waiting.
    """
    level = _python_level()
    if level == "stop":
        return _python_check()
    if level == "warn" and not _PY_NOTED:
        _PY_NOTED.append(True)
        lines = _python_problem()[1]
        SFIToolkit.displayln("{txt}Note: " + lines[0])
        for line in lines[1:3]:
            SFIToolkit.displayln("{txt}" + line)
        SFIToolkit.displayln("{txt}   -equipop doctor- says how to move "
                             "Stata to a newer Python.")
    return level, []


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


def _decay_spec(model, half_life, calibration=""):
    """Build the engine's Decay object, or None for no decay.

    A variable bandwidth passes its own half-life per row, so the
    single number here is only the fixed case; the engine takes the
    model AND THE CALIBRATION from this object either way - the bin
    loop copies both (BACKLOG 317).
    """
    if not model:
        return None
    from equipop.decay import Decay
    return Decay(model=model,
                 half_life_m=(float(half_life) if half_life > 0
                              else 1.0),
                 calibration=calibration or None)


def _report_calibration(dec, halflife, halflifevar):
    """Say which kernel runs, and show BOTH betas (BACKLOG 317).

    Printed so it lands in a -log using- file - John's ruling on Stata
    provenance - and handed back as locals so the ado can return them.
    Showing both betas makes the difference between the two readings
    visible even to a user who never set calibration().
    """
    SFIToolkit.displayln(
        "{txt}decay: {res}" + dec.model + "{txt}, calibration "
        "{res}" + dec.calibration)
    if halflifevar:
        SFIToolkit.displayln(
            "{txt}  the half-life varies by row ({res}" + halflifevar +
            "{txt}); every bin uses " + dec.calibration + ".")
    elif halflife and halflife > 0:
        hl, hp = dec.both_betas()
        SFIToolkit.displayln(
            "{txt}  at halflife({res}%g{txt}):" % float(halflife))
        if hl is None:
            SFIToolkit.displayln(
                "{txt}    half-life         {res}not defined{txt} - "
                "power has no median")
        else:
            SFIToolkit.displayln(
                "{txt}    half-life         beta = {res}%.6g" % hl
                + ("{txt}   <- used" if dec.calibration == "half-life"
                   else ""))
        SFIToolkit.displayln(
            "{txt}    half-probability  beta = {res}%.6g" % hp
            + ("{txt}   <- used" if dec.calibration == "half-probability"
               else ""))
    Macro.setLocal("eqp_calibration", dec.calibration)
    Macro.setLocal("eqp_beta", repr(float(dec.beta)))


def _col(v):
    import numpy as np                # BACKLOG 459: here, not at load
    a = np.array(Data.get(v), dtype=float)
    a[a > 8.9e307] = np.nan          # Stata missings arrive huge
    return a


def _engine_takes_unit(unit):
    """BACKLOG 445, v1.63.0. A FRACTIONAL unit() needs engine 1.63.0 or
    newer: an older one rounds it somewhere (output coordinates, the
    effort engines' grid) and either stops with a lookup error or runs
    at the rounded size. eqp_min_engine stays where it is - a whole
    size loses nothing on an older engine (BACKLOG 331/385) - so the
    one case that needs the newer engine is refused here, in words.
    tests/test_fractional_cells.py runs this against a stand-in old
    engine. The same function is in equipop_run.ado."""
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


def _drop_exactly(names):
    """Drop these variables and no others (BACKLOG 473).

    By POSITION in the dataset, highest first, and only a variable
    whose name IS the name asked for. Stata's own -drop- reads a name
    that does not exist as an abbreviation of one that does, which is
    how -replace- came to delete N_1000 when asked about N_100. A
    position cannot be abbreviated. Should this Stata's sfi have no
    dropVar, the fallback is Stata's -drop- under -novarabbrev-, on a
    name already known to exist in full.
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


def _equipop_machine1(*, x, y, treat, k="", r="", unit=100.0,
                      weight="", selfpot=1.0, touse="", prefix="",
                      project="", epsg=0, treatmode="counts",
                      missing="", decay="", halflife=0.0,
                      halflifevar="", bins=10, overshoot="",
                      originrule="", calibration="", unit_was_set="",
                      replace=""):
    # KEYWORD-ONLY on purpose: a positional call raises TypeError
    # rather than quietly meaning something else.
    level, py_lines = _python_note_once()           # BACKLOG 459
    if level == "stop":
        for line in py_lines:
            SFIToolkit.errprintln(line)
        SFIToolkit.error(198)
        return
    try:
        import numpy as np                          # BACKLOG 459
        from equipop.stata_bridge import (knn_to_rows, to_stata_values,
                                          project_for_stata,
                                          degrees_warning,
                                          zone_span_warning)
    except ImportError as exc:
        SFIToolkit.errprintln(
            "the EquiPop engine cannot be loaded in the Python Stata "
            "is using:")
        SFIToolkit.errprintln("   " + (sys.executable or "(unknown)"))
        SFIToolkit.errprintln("   " + str(exc).splitlines()[0])
        SFIToolkit.errprintln(
            "Run -equipop setup-, restart Stata, then -equipop doctor-. "
            "See help equipop.")
        SFIToolkit.error(198)
        return
    if not _engine_takes_unit(unit):
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
        dec = _decay_spec(decay, halflife, calibration)
        if dec is not None:
            _report_calibration(dec, halflife, halflifevar)
        # BACKLOG 293. The arguments are assembled as a DICT first so
        # that the provenance note below is built from the SAME object
        # the engine was called with. Listing them twice is how a
        # record comes to describe a run that did not happen.
        _call = dict(unit_size=float(unit), r_values=rs,
                     self_potential=float(selfpot),
                     treat_are_counts=(treatmode != "flags"),
                     missing_codes=[float(c)
                                    for c in missing.split()],
                     decay=dec,
                     decay_half_life=(_col(halflifevar)
                                      if halflifevar else None),
                     decay_bins=int(bins),
                     overshoot_mode=(overshoot or None),
                     self_rule=(originrule or None))
        res = knn_to_rows(xs, ys, ks, treat=treats, weight=w, **_call)
    except ValueError as exc:
        for line in _wrap_for_stata(str(exc)):
            SFIToolkit.errprintln(line)
        SFIToolkit.error(198)
        return

    # BACKLOG 293. PROVENANCE, John's ruling: a PRINTED NOTE rather
    # than a sidecar, because a Stata run writes variables into memory
    # and may produce no file at all, and because `log using` is where
    # a Stata user's reproducibility already lives. The values also go
    # back in r() so a do-file can CHECK them instead of a human
    # reading the log.
    #
    # THE EFFECTIVE MODE, not the typed one. An empty overshoot() or
    # originrule() means "the engine's default applies", and the
    # record has to say which default that was - otherwise the two
    # settings that moved every number since 1.30 are recorded as
    # blank, which is how they came to be recorded nowhere at all.
    # TWO BLOCKS, AND THE SPLIT IS DELIBERATE. The r() values need
    # only overshoot.DEFAULT (1.30) and selfrule.DEFAULT (1.47), both
    # of which any engine this ado will meet already has. The printed
    # note needs equipop.meta.record, which is new in 1.50.0 - so it
    # degrades to one line on an older engine rather than forcing
    # eqp_min_engine up and making `equipop setup` demand a version
    # nobody has yet (BACKLOG 332). A note is a convenience; an
    # install that cannot complete is not.
    from equipop.overshoot import DEFAULT as _OVER_DEFAULT
    from equipop.selfrule import DEFAULT as _ORIG_DEFAULT
    _eff_over = overshoot or _OVER_DEFAULT
    _eff_orig = originrule or _ORIG_DEFAULT
    Macro.setLocal("eqp_overshoot", str(_eff_over))
    Macro.setLocal("eqp_originrule", str(_eff_orig))
    try:
        from equipop.meta import record, render_settings
        _rl = record("counts", len(xs),
                     dict(_call, k_values=ks, treat=treats, weight=w,
                          overshoot_mode=_eff_over,
                          self_rule=_eff_orig))
        _rl.set_data(output_columns=len(res))
        for _line in render_settings(_rl.doc):
            SFIToolkit.displayln("{txt}" + _line)
        Macro.setLocal("eqp_provenance", _rl.doc["run"]["id"])
    except Exception as _exc:
        # A provenance failure must never lose a finished analysis.
        SFIToolkit.displayln(
            "{txt}(the run note needs engine 1.50.0 or newer: "
            + str(_exc).splitlines()[0] + ")")

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

    # SHORTEN RATHER THAN REFUSE. John's run finished 646,766 cells,
    # three widened passes and both k values, and THEN stopped because
    # T_h72004_africanamericanalone_100 is 33 characters. The
    # arithmetic was done; only the label was too long. Refusing
    # threw away the work and told him to rename his data.
    # WHAT IS SHORTENED IS THE MIDDLE. The prefix says which measure
    # it is and the tail says which k - both carry meaning and both
    # are short. The variable's own name is the only part with room.
    # EVERY RENAME IS ANNOUNCED. A silently renamed column is how
    # somebody publishes the wrong variable.
    def _shorten(full, taken):
        if len(full) <= 32:
            return full
        head, _, tail = full.rpartition("_")
        tail = "_" + tail
        room = 32 - len(prefix) - len(tail)
        if room < 3:
            return None                 # prefix and k alone too long
        stem = head[len(prefix):]
        cand = prefix + stem[:room] + tail
        n = 0
        while cand in taken:
            n += 1
            mark = str(n)
            cand = prefix + stem[:room - len(mark)] + mark + tail
            if n > 99:
                return None
        return cand

    renamed, taken, final, use = [], set(existing), [], {}
    for key, full in zip(res, wanted):
        got = _shorten(full, taken)
        if got is not None and got != full:
            renamed.append((full, got))
        final.append(got if got is not None else full)
        # THE MAPPING MUST REACH THE WRITER. The first version of
        # this computed the shortened names, ANNOUNCED them, and then
        # the writing loop rebuilt the name from res and created the
        # ORIGINAL - so Stata refused with "invalid varname" after
        # the rename had been printed. The names were right on screen
        # and wrong in the data.
        use[key] = got if got is not None else full
        if got is not None:
            taken.add(got)
    if renamed:
        SFIToolkit.displayln("")
        SFIToolkit.displayln("{txt}[equipop] Stata allows 32 "
                             "characters, so these were shortened:")
        for was, now in renamed:
            SFIToolkit.displayln(f"{{txt}}    {was} -> {now}")
        SFIToolkit.displayln("{txt}[equipop] the prefix and the k are "
                             "kept; only the variable name is cut.")
    wanted = final

    problems = []
    dropping = []                                 # BACKLOG 473
    for name in wanted:
        if len(name) > 32:
            problems.append(
                f"{name} is {len(name)} characters and cannot be "
                f"shortened - prefix() and the k suffix already take "
                f"{len(name) - len(name.rpartition('_')[0]) + len(prefix)}"
                " of the 32. Use a shorter prefix().")
        elif name in existing:
            if replace:
                dropping.append(name)             # BACKLOG 473
            else:
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

    # BACKLOG 473: replace, here and only now - the engine has
    # answered and every name has passed the checks above.
    _drop_exactly(dropping)

    made = []
    for key, arr in res.items():
        name = use[key]
        vals = np.asarray(arr, dtype=float)
        if keep is not None:
            vals = np.where(keep, vals, np.nan)
        Data.addVarDouble(name)
        Data.store(name, None, to_stata_values(vals))
        made.append(name)

    Macro.setLocal("eqp_varlist", " ".join(made))

    # ---- the unit-size advisory (BACKLOG 385) ----------------------
    # LAST, so it is the final thing on screen: a note about the grid
    # is worth nothing if it scrolls away above the results.
    #
    # It runs on every machine-1 run because it is FREE: measured
    # against a real run on the same data, the advisory is 0.3% of
    # build_cells plus the kNN search, at both 20,000 and 60,000
    # individuals, and the ratio holds because the advisory is nine
    # linear passes while the run builds a tree and searches it.
    #
    # xs/ys/w are the full reference population on purpose. `if`/`in`
    # restricts which ROWS get values, not who counts as a neighbour,
    # so the advisory has to be about the same people the engine used.
    #
    # Wrapped, and silent on failure: an ADVISORY must never be the
    # reason a finished run fails to return its results. The variables
    # are already in memory by this point.
    try:
        from equipop import unitsize

        adv = unitsize.advise_unit(xs, ys, w, k_values=(ks or [100]),
                                   current=float(unit),
                                   self_rule=(originrule or "include"))
        for line in unitsize.advise_on_run(
                adv, unit=float(unit),
                unit_was_set=bool(unit_was_set)):
            SFIToolkit.displayln("{txt}" + line)
    except Exception:
        pass


def _equipop_setup_py(repair="", ado_version="", min_engine=""):
    # Standard library ONLY, and deliberately so: this runs BEFORE the
    # package exists, on a machine where the whole point is that
    # nothing is installed yet. It must not import the thing it is
    # about to install.
    import subprocess
    import sys

    # BACKLOG 459. Before pip, not after it: below 3.10 pip can only
    # answer "no matching distribution", which reads as a network
    # problem. On 3.10 it will install engine 1.61.0, and saying so
    # first means the version the doctor reports is not a surprise.
    # BACKLOG 461: and then the whole way out, the search included.
    if _python_level() != "ok":
        print("EquiPop setup")
        level = _python_tell(min_engine)
        if level == "stop":
            Macro.setLocal("eqp_setup_failed", "1")
            return
        _PY_NOTED.append(True)        # shown whole; runs need not repeat it
        print("")

    # BACKLOG 319. --user IS REFUSED INSIDE A VIRTUAL ENVIRONMENT:
    # "Can not perform a '--user' install. User site-packages are not
    # visible in this virtualenv." A colleague on a Mac had pointed
    # Stata at ~/StataPython/bin/python - a venv made for Stata, which
    # is a sensible thing to do - and setup would have failed on
    # exactly the users careful enough to do that. In a venv the
    # ordinary install IS the user install, so --user is not merely
    # unnecessary, it is wrong.
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    args = ["--upgrade"] if in_venv else ["--user", "--upgrade"]
    if repair:
        # The Mac case, and the Anaconda case: the libraries are
        # present but built for the wrong processor, or shadowed by
        # another copy. --no-cache-dir is not decoration - without it
        # pip reuses the wrong wheel it already downloaded and the
        # repair appears not to work.
        args += ["--force-reinstall", "--no-cache-dir",
                 "--only-binary=:all:", "numpy", "scipy", "pandas"]
    # BACKLOG 196, corrected by 332. A FLOOR, NOT A PIN, and not the
    # ADO'S VERSION EITHER. Unpinned, a 1.40 command file could pull
    # whatever PyPI has today. Pinned exactly, an older ado could
    # never receive a bug-fixed engine. Pinned to the ado's own
    # release number - which is what 196 actually built - the floor
    # names an engine that may not exist, and pip then refuses to
    # install anything at all.
    # THE REAL INVARIANT, stated properly: the ado is the CALLER and
    # the engine is the LIBRARY, so the library must be at least as
    # new as THE OLDEST VERSION THAT SATISFIES THE CALLER'S CALLS.
    # That is a fact about the code, maintained by hand beside the
    # list of what sets it, and it only ever names something already
    # published.
    # THIS MATTERS MORE FROM SSC THAN IT DID FROM GITHUB. There the
    # two arrived together from one set of instructions; on SSC they
    # sit on separate update tracks - adoupdate for the commands,
    # `equipop setup` for the engine - so drift is the normal state
    # rather than an accident.
    floor = min_engine or ado_version       # older ado: no floor sent
    if floor:
        args.append("equipop>=" + floor)
    else:
        args.append("equipop")
    cmd = [sys.executable, "-m", "pip", "install"] + args

    print("EquiPop setup")
    if ado_version:
        print("  these command files are version " + ado_version)
    if floor:
        print("  the oldest engine they can run on is " + floor +
              ", so the engine asked for is equipop>=" + floor)
    if in_venv:
        print("  this Python is a virtual environment, so --user is "
              "not used")
    print("  installing into the Python Stata is using:")
    print("     " + sys.executable)
    print("  command:")
    print("     " + " ".join(cmd))
    print("")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as exc:
        print("  could not run pip at all: " + str(exc).splitlines()[0])
        Macro.setLocal("eqp_setup_failed", "1")      # BACKLOG 196
        return
    tail = (p.stdout or "").strip().splitlines()[-12:]
    for line in tail:
        print("  " + line)
    if p.returncode != 0:
        print("")
        Macro.setLocal("eqp_setup_failed", "1")      # BACKLOG 196
        print("  PIP FAILED. The message above is pip's own:")
        for line in (p.stderr or "").strip().splitlines()[-8:]:
            print("     " + line)
        # BACKLOG 319. THIS USED TO PRINT THE SAME ADVICE WHATEVER PIP
        # SAID. For "No module named pip" it sent the user to replace
        # their entire Python when the fix is one line, and they
        # believed it, because the message sounded certain. Advise on
        # WHAT PIP ACTUALLY SAID, and when it says something we do not
        # recognise, quote it and stop rather than guess.
        low = ((p.stderr or "") + (p.stdout or "")).lower()
        if "no module named pip" in low:
            print("  That Python has no pip. It is otherwise fine, and "
                  "one line fixes it:")
            print("     " + sys.executable + " -m ensurepip --upgrade")
            print("  Run that in a Terminal or Command Prompt, then run "
                  "-equipop setup- again.")
            print("  If THAT says there is no ensurepip either, the "
                  "Python was built")
            print("  without it - install a plain Python from "
                  "python.org instead.")
        elif "externally managed" in low:
            # BACKLOG 461. This said "install a plain Python from
            # python.org, point Stata at it, restart" - the order the
            # review of 1.63.2 (F1) ruled out, and a new Python for a
            # user who already has a perfectly good one. A virtual
            # environment made from it is all it takes.
            print("  This Python belongs to Homebrew or to the operating "
                  "system, which do")
            print("  not let other programs install into it. EquiPop can "
                  "still use it,")
            print("  through a Python of its own made from it (a virtual "
                  "environment).")
            for line in _py_steps_venv(sys.executable, intro=False):
                print("  " + line)
        elif "--user" in low and ("virtualenv" in low or "venv" in low):
            print("  That Python is a virtual environment, which "
                  "refuses a --user install.")
            print("  This version should not have asked for one - "
                  "please report it. Meanwhile:")
            print("     " + sys.executable + " -m pip install --upgrade "
                  "equipop")
        elif floor and ("equipop>=" + floor).lower() in low:
            # BACKLOG 331. THE ENGINE WE ASKED FOR DOES NOT EXIST YET,
            # which is OUR release-ordering mistake and not the user's
            # problem to debug. It happens when the command files
            # reach SSC before the engine reaches PyPI: setup asks for
            # equipop>=<ado version>, pip finds nothing that new, and
            # the install fails outright - not a warning, a hard stop
            # for every new user.
            #
            # Until now this fell into the branch below and was told
            # to check the network and the Python version. Both fine;
            # neither the cause. That is BACKLOG 319's fault exactly -
            # confident advice pointing the wrong way - and it was
            # written in the same release that fixed 319.
            print("  THIS IS OUR MISTAKE, NOT YOURS. These command "
                  "files ask for an engine")
            print("     equipop>=" + floor)
            print("  and no engine that new has been published to "
                  "PyPI yet, so pip has")
            print("  nothing to install. The two halves are released "
                  "separately and the")
            print("  engine is supposed to go first.")
            print("")
            print("  What works meanwhile - take the newest engine "
                  "there is:")
            print("     " + sys.executable + " -m pip install "
                  "--upgrade equipop")
            print("  Then restart Stata and run -equipop doctor-. It "
                  "will tell you the")
            print("  engine is older than the commands. Most things "
                  "will work; if a")
            print("  command stops with ImportError, that is the gap, "
                  "and it is worth")
            print("  reporting at "
                  "https://github.com/GeoJohnSwe/EquiPop/issues")
        elif "no matching distribution" in low or "could not find" in low:
            print("  pip could not reach PyPI, or could not find a "
                  "build for this Python.")
            print("  Check the network and any proxy, and that this "
                  "Python is 3.11 or newer:")
            print("     " + sys.executable + " --version")
        else:
            print("  We do not recognise that message, so we will not "
                  "guess at it.")
            print("  It is pip's own, and it is the thing to search for "
                  "or to send on.")
        return

    print("")
    print("  Done. Now QUIT STATA COMPLETELY, start it again, and run:")
    print("     equipop doctor")
    # NOT run here on purpose. Python starts once per Stata session and
    # keeps whatever it loaded first, so after an upgrade the doctor
    # would report the version that is still in memory - the OLD one -
    # and say everything matches when it does not.


_UNIT_CHAR = "equipop_unitsize"


def _unit_cache_get():
    """The cached advice string, or ("", why-not). Best effort.

    `char _dta[]` is the right home: it travels with the data, it
    survives -save-, and it is thrown away by -clear-, which is
    exactly the lifetime a fact about this dataset should have.

    SFI's Characteristic class is imported HERE, not at the top of the
    block, for the same reason numpy's absence must not take the
    doctor down with it: the doctor exists to work on a machine where
    nothing else does, and a top-level import of a name some sfi
    version lacks would break the whole block - setup and doctor
    included - rather than just this one subcommand.
    """
    try:
        from sfi import Characteristic
        # BACKLOG 474: getDtaChar. This called getDta, which sfi does
        # not have, so every -equipop unit- recounted and then said
        # the advice could not be stored. The old name is tried last,
        # in case some sfi does carry it.
        get = getattr(Characteristic, "getDtaChar", None)
        if get is None:
            get = getattr(Characteristic, "getDta")
        return get(_UNIT_CHAR) or "", ""
    except Exception as exc:
        return "", str(exc).splitlines()[0] if str(exc) else type(exc).__name__


def _unit_cache_put(text):
    """Store it, and say why if we could not. Never raises."""
    try:
        from sfi import Characteristic
        put = getattr(Characteristic, "setDtaChar", None)
        if put is None:                              # BACKLOG 474
            put = getattr(Characteristic, "setDta")
        put(_UNIT_CHAR, text)
        return ""
    except Exception as exc:
        return str(exc).splitlines()[0] if str(exc) else type(exc).__name__


def _equipop_unit_py():
    """-equipop unit-: report the cell size this data wants.

    BACKLOG 385. Thin on purpose. Reads two columns, asks the engine,
    prints what it is handed, stores the answer on the dataset.
    """
    # Review of 1.63.2, F2. This subcommand never passes through
    # machine 1, so it checks the Python itself, first: on 3.9 "install
    # into THAT one" below is advice that cannot work.
    level, py_lines = _python_note_once()
    if level == "stop":
        for line in py_lines:
            SFIToolkit.errprintln(line)
        SFIToolkit.error(198)
        return
    try:
        from equipop import unitsize
    except ImportError:
        SFIToolkit.errprintln(
            "equipop is not installed in Stata's Python. Check which "
            "Python with -python query-, then install into THAT one "
            "with -equipop setup-. See help equipop.")
        SFIToolkit.error(198)
        return
    except Exception as exc:
        # An engine too old to carry the module at all. Say which
        # version is needed rather than showing an ImportError for a
        # name the user has never heard of.
        SFIToolkit.errprintln(
            "this engine has no unit-size advisory - it arrived in "
            "EquiPop 1.54.0. Run -equipop setup- to update "
            f"it. ({exc})")
        SFIToolkit.error(198)
        return

    gl = Macro.getLocal
    touse = _col(gl("touse"))
    keep = touse > 0
    x = _col(gl("eqp_x"))[keep]
    y = _col(gl("eqp_y"))[keep]
    # `wvar`, not `pop`: the ado resolves [fweight=var] and pop(var)
    # into one name, so reading pop() here would find an empty macro
    # whenever the weight was given the fweight way, hand the engine
    # None, and advise on an UNWEIGHTED population - a complete,
    # plausible, silently wrong table, with nothing raised for the
    # door's catch to even be involved in.
    pop = gl("wvar")
    w = _col(pop)[keep] if pop else None

    ks = [int(v) for v in gl("k").split()]
    cands = [float(v) for v in gl("candidates").split()] or None
    tol = float(gl("tolerance"))
    rule = gl("originrule") or "include"

    # The cache. MEASURED before it was built: 16 s on ten million
    # rows against 0.55 s to fingerprint them, and 0.07 s on a hundred
    # thousand - so it matters on big data and is harmless on small,
    # which is where John asked for it.
    fp = unitsize.fingerprint_points(x, y, w)
    cached_text, why_no_cache = _unit_cache_get()
    advice = None
    # ONE KEY FOR THE WHOLE REQUEST (review F2). This used to pass
    # the fingerprint, the k list and the tolerance as three separate
    # optional checks and name neither the candidate ladder nor the
    # origin rule - so asking for different candidates, or the other
    # rule, was reported as a cache HIT and answered with the old
    # table. request_key is built from the same resolved ladder
    # advise_unit uses, and unpack_advice now REQUIRES it.
    req = unitsize.request_key(fingerprint=fp, k_values=ks,
                               tolerance=tol, candidates=cands,
                               self_rule=rule)
    if not gl("nocache"):
        advice = unitsize.unpack_advice(cached_text, req)
    from_cache = advice is not None
    if advice is None:
        advice = unitsize.advise_unit(x, y, w, k_values=ks,
                                      candidates=cands, tolerance=tol,
                                      self_rule=rule)

    for line in unitsize.format_advice(advice):
        SFIToolkit.displayln("{txt}" + line)
    if from_cache:
        SFIToolkit.displayln(
            "{txt}  (read from this dataset's stored advice - the "
            "coordinates have not changed. nocache forces a recount.)")
    elif why_no_cache:
        # NOT silent. A cache that quietly never works is this
        # project's most repeated bug - a thing that exists and the
        # path cannot reach it, five releases running (BACKLOG 353,
        # 368, 373, 380). If it is not working the user hears so.
        SFIToolkit.displayln(
            "{txt}  (not stored on the dataset - this Stata's sfi "
            f"would not take a characteristic: {why_no_cache})")
    else:
        packed = unitsize.pack_advice(advice)
        if len(packed) <= unitsize.MAX_PACKED:
            failed = _unit_cache_put(packed)
            if failed:
                SFIToolkit.displayln(
                    "{txt}  (not stored on the dataset: " + failed + ")")

    first = advice["k_values"][0]
    rec = advice["recommended"][first]
    row = None
    if rec is not None:
        row = next(r for r in advice["rows"] if r["unit"] == rec)
    Macro.setLocal("eqp_u_points", str(advice["points"]))
    Macro.setLocal("eqp_u_people", repr(float(advice["people"])))
    # A missing recommendation is a MISSING VALUE in Stata, not a
    # zero: "no size serves this k" and "a unit of zero metres" must
    # not arrive as the same number in a do-file.
    Macro.setLocal("eqp_u_rec", "." if rec is None else repr(float(rec)))
    Macro.setLocal("eqp_u_cells",
                   "." if row is None else str(row["cells"]))
    Macro.setLocal("eqp_u_est", "." if row is None
                   else repr(float(row["share_people"][first])))
    Macro.setLocal("eqp_u_fp", advice["fingerprint"])
    # Review F1. Without this, r(unit) is missing under exclude and
    # a do-file cannot tell WHY - "no size serves this k because the
    # population is too dense" and "this criterion does not apply to
    # the rule you are running" are different answers that both
    # arrive as a full stop.
    Macro.setLocal("eqp_u_applies",
                   "1" if advice.get("applies", True) else "0")

    vals, cols, rownames = unitsize.advice_matrix(advice)
    from sfi import Matrix
    Matrix.store("eqp_advice", vals)
    Matrix.setColNames("eqp_advice", cols)
    Matrix.setRowNames("eqp_advice", rownames)


def _equipop_doctor_py(ado_version="", min_engine=""):
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
    #
    # BACKLOG 459. THE PYTHON ITSELF IS CHECKED FIRST. Below 3.10 no
    # engine can be installed at all, so "install equipop into THAT
    # Python" was advice that could only fail; the report now says
    # which Python to get instead.
    # BACKLOG 461: and it looks for a better one on this computer.
    if _python_level() != "ok":
        print("EQUIPOP - the Python Stata is using")
        level = _python_tell(min_engine)
        print("")
        if level == "stop":
            return
        _PY_NOTED.append(True)        # shown whole; runs need not repeat it
    try:
        from equipop.doctor import run
    except Exception as exc:
        print("EquiPop doctor could not load the package:")
        print("   " + str(exc).splitlines()[0])
        print("   Python running Stata: " + sys.executable)
        print("   Install it into THAT Python with -equipop setup-, "
              "then restart Stata.")
        return
    # BACKLOG 332. min_engine is newer than the argument list of
    # every engine before 1.49.3, and those engines are installed on
    # real machines. Passing it to one of them raises TypeError, so
    # the call falls back - an ado must never break on an engine older
    # than itself when the only loss is a line of the report.
    # ASKED, NOT CAUGHT. This was
    #
    #     try:    run(ado_version=..., min_engine=...)
    #     except TypeError: run(ado_version=...)
    #
    # and `run()` did not accept min_engine AT ALL until 1.54.4 - so
    # the TypeError fired on every single doctor run, the fallback
    # reported with no floor, and BACKLOG 332's floor check was dead
    # from this door for six releases. A blanket `except TypeError`
    # around a call cannot tell a missing parameter from a TypeError
    # raised deep inside the report, and it degraded in silence
    # either way, which is why nobody found out.
    #
    # Inspecting the signature asks the question directly, and when
    # the answer is no the report SAYS the floor could not be
    # checked. A silent degrade is the thing to avoid here, not the
    # old engine.
    import inspect
    try:
        takes_floor = "min_engine" in inspect.signature(run).parameters
    except Exception:
        takes_floor = False
    if takes_floor:
        run(ado_version=ado_version, min_engine=min_engine)
    else:
        # BEFORE the report, not after - John, 10 October 2026, second
        # round: "where did I go wrong during installation?" He had
        # not. The report's own release-number remark says the
        # combination "does break", and the note correcting it was
        # printed after the VERDICT, pages below. **A correction read
        # after the alarm is read too late.**
        #
        # AND IT STATES THE CONCLUSION, by calling the engine's own
        # floor function rather than restating the comparison here.
        # One source: the words are the same ones a current engine
        # prints, which is the whole point of 332.
        said = []
        try:
            import equipop as _eqp
            from equipop.doctor import _lines_floor
            said = _lines_floor(min_engine, _eqp.__version__)
        except Exception:
            said = []
        # TWO COHERENT BRANCHES. The first version printed "this
        # engine is too old to say" and then, unconditionally, "so it
        # is checked here instead" - which contradicts the line above
        # it (external review of 1.54.5, residual 1). An engine old
        # enough to lack `_lines_floor` cannot be compared against at
        # all, and saying so is different from saying the answer.
        print("EQUIPOP - what these commands need")
        if said:
            for _line in said:
                print(_line)
            print("  This engine cannot be told the requirement, so "
                  "it is checked here instead.")
        else:
            print(f"  needs engine : {min_engine} or newer - and this "
                  f"engine is too old")
            print("  to compare itself against it, so the requirement "
                  "is UNCHECKED either way.")
        print("  ANY VERSION REMARK BELOW COMPARES TWO RELEASE "
              "NUMBERS, which move for")
        print("  different reasons - read this line, not that one. "
              "`equipop setup` updates")
        print("  the engine and the remark goes away.")
        print("")
        run(ado_version=ado_version)
end
