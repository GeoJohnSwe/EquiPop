*! equipop v1.54.4  -  k-nearest neighbour context variables via EquiPop
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
    * Fractional cell sizes are REFUSED, because the core
    * converts cell centres to integers - a requested 2.5 gives centres
    * 1, 3, 6, so the spacings come out 2 and 3 and neither is 2.5.
    * QGIS and Pro have refused this since 1.29.8. Stata did not, and
    * a rule enforced at some doors and not others is how 172 happened.
    * The rule itself lives in the package, so a fourth door inherits
    * it rather than reimplementing it.
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
                * BACKLOG 336, MARINA'S PULL REQUEST. The decay
                * outputs were never dropped, so a second decay() run
                * with -replace- failed and told the user to "use
                * option replace" - which they had.
                if "`decay'" != "" {
                    capture drop `prefix'ND_`kk'
                }
                * treat() became optional in 1.36, and an empty
                * -varlist- loop is a syntax error, not an empty loop.
                * So -equipop, x() y() k(25) replace- failed on exactly
                * the combination that ruling created.
                if "`treat'" != "" {
                    foreach v of varlist `treat' {
                        capture drop `prefix'T_`v'_`kk'
                        capture drop `prefix'R_`v'_`kk'
                        if "`decay'" != "" {        /* 336 */
                            capture drop `prefix'TD_`v'_`kk'
                            capture drop `prefix'RD_`v'_`kk'
                        }
                    }
                }
            }
        }
        if "`r'" != "" {
            foreach rr of numlist `r' {
                * `rl' is the underscore-safe name -
                * r=1.5 becomes r1_5, because a dot cannot appear in
                * a Stata variable name.
                * BACKLOG 337: this subinstr was RIGHT and the engine
                * was wrong - it produced N_r1.5 while this looked for
                * N_r1_5, so the two halves of one file disagreed.
                * equipop/labels.py now names the column this way at
                * the source, so the engine and this list agree.
                local rl : subinstr local rr "." "_", all
                capture drop `prefix'N_r`rl'
                if "`decay'" != "" {                /* 336 */
                    capture drop `prefix'ND_r`rl'
                }
                if "`treat'" != "" {
                    foreach v of varlist `treat' {
                        capture drop `prefix'T_`v'_r`rl'
                        capture drop `prefix'R_`v'_r`rl'
                        if "`decay'" != "" {        /* 336 */
                            capture drop `prefix'TD_`v'_r`rl'
                            capture drop `prefix'RD_`v'_r`rl'
                        }
                    }
                }
            }
        }
    }

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
        calibration="`calibration'", unit_was_set=`unit_was_set')

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
    local eqp_ado_version "1.54.4"

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
    local eqp_ado_version "1.54.4"
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

    Printed so it lands in a `log using` file - John's ruling on Stata
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
    a = np.array(Data.get(v), dtype=float)
    a[a > 8.9e307] = np.nan          # Stata missings arrive huge
    return a


def _equipop_machine1(*, x, y, treat, k="", r="", unit=100.0,
                      weight="", selfpot=1.0, touse="", prefix="",
                      project="", epsg=0, treatmode="counts",
                      missing="", decay="", halflife=0.0,
                      halflifevar="", bins=10, overshoot="",
                      originrule="", calibration="", unit_was_set=""):
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
    for name in wanted:
        if len(name) > 32:
            problems.append(
                f"{name} is {len(name)} characters and cannot be "
                f"shortened - prefix() and the k suffix already take "
                f"{len(name) - len(name.rpartition('_')[0]) + len(prefix)}"
                " of the 32. Use a shorter prefix().")
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
            print("  This is Apple's or the system's own Python and is "
                  "not ours to change.")
            print("  Install a plain Python from python.org, point "
                  "Stata at it with")
            print("     python set exec \"THE_PATH_TO_THAT_PYTHON\", "
                  "permanently")
            print("  restart Stata, and run -equipop setup- again.")
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
                  "Python is 3.10 or newer:")
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
        return Characteristic.getDta(_UNIT_CHAR) or "", ""
    except Exception as exc:
        return "", str(exc).splitlines()[0] if str(exc) else type(exc).__name__


def _unit_cache_put(text):
    """Store it, and say why if we could not. Never raises."""
    try:
        from sfi import Characteristic
        Characteristic.setDta(_UNIT_CHAR, text)
        return ""
    except Exception as exc:
        return str(exc).splitlines()[0] if str(exc) else type(exc).__name__


def _equipop_unit_py():
    """-equipop unit-: report the cell size this data wants.

    BACKLOG 385. Thin on purpose. Reads two columns, asks the engine,
    prints what it is handed, stores the answer on the dataset.
    """
    try:
        from equipop import unitsize
    except ImportError:
        SFIToolkit.errprintln(
            "equipop is not installed in Stata's Python. Check which "
            "Python with -python query-, then install into THAT one. "
            "See help equipop.")
        SFIToolkit.error(198)
        return
    except Exception as exc:
        # An engine too old to carry the module at all. Say which
        # version is needed rather than showing an ImportError for a
        # name the user has never heard of.
        SFIToolkit.errprintln(
            "this engine has no unit-size advisory - it arrived in "
            "EquiPop 1.54.0. Run -equipop setup, replace- to update "
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
    # Review F1. Without this, `r(unit)' is missing under exclude and
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
    try:
        from equipop.doctor import run
    except Exception as exc:
        print("EquiPop doctor could not load the package:")
        print("   " + str(exc).splitlines()[0])
        print("   Python running Stata: " + sys.executable)
        print("   Install equipop into THAT Python, then restart Stata.")
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
        run(ado_version=ado_version)
        print("")
        print(f"  (this engine is too old to be told which engine the "
              f"commands need:")
        print(f"   they need {min_engine} or newer, and the lines above "
              f"could not check it.")
        print("   Any version remark above compares two RELEASE "
              "numbers, which move for")
        print("   different reasons - `equipop setup` brings the engine "
              "up to date.)")
end
