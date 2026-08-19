*! EquiPop 1.40.7 - a test pass over stata_test_data.dta
*!
*! WHAT CHANGED IN 1.40.5, and why it matters:
*!   Until now this file STATED its invariants and did not ENFORCE
*!   them. A wrong number printed itself and the run carried on, so
*!   the pass could only fail in front of somebody reading closely.
*!   Every stated property is now a CHECK with a verdict, and the
*!   file refuses to finish quietly if any check failed.
*!
*! HOW TO READ THE OUTPUT
*!   Every check prints one line beginning [ok] or [FAIL].
*!   The last thing the pass prints is a VERDICT with a count.
*!   If you send us only one thing, send the whole log; if you can
*!   send only one screen, send the verdict.
*!
*! A FAILING CHECK DOES NOT STOP THE PASS. Each block is trapped, so
*! one broken thing cannot hide the other twenty-two. A single run
*! gives the complete picture.
*!
*! WHAT THIS DATA IS: 10,892 points on a metric grid (X 503-537 km,
*! Y 442-484 km - about 34 by 42 km). LowEdu, HighEdu, TheoEdu and
*! VocaEdu are 0/1 MARKERS, not counts. ValCount is a count per point,
*! 0-98, mean 45.5. ValFloat is continuous, 0-23,254.
*! NINE rows have no coordinates. They receive missing results, and
*! block 1 checks that they do.
*!
*! READ THIS BEFORE BLOCK 7: because the education variables are 0/1
*! markers, any run that ALSO supplies a population needs
*! treatmode(flags). Block 7 runs both settings side by side so the
*! size of the error is visible.
*!
*! WHERE THE EXPECTED NUMBERS COME FROM: every threshold below was
*! measured against this dataset through equipop/stata_bridge.py, the
*! same code the .ado calls. They are not guesses and they are not
*! carried over from an earlier version of this file.

version 17
clear all
set more off


* ==================================================================
* CONFIGURATION - the only part of this file you edit
* ==================================================================
* Put the full path to stata_test_data.dta between the quotes below.
* Leave it EMPTY and the pass looks for the file in the current
* working directory instead - type  pwd  to see where that is.
* This works the same way on Windows and on a Mac.

global EQP_DATA ""

* The release this pass was written for. The pass checks the engine
* against it, because the .ado files and the Python engine are
* updated by two different mechanisms, and a half-update is the most
* common support problem this project has.

global EQP_EXPECT "1.40.7"

* ------------------------------------------------------------------
* Nothing below here needs editing.
* ------------------------------------------------------------------

if "$EQP_DATA" == "" global EQP_DATA "stata_test_data.dta"

capture confirm file "$EQP_DATA"
if _rc {
    display as error "=================================================="
    display as error "STOP: the test data was not found."
    display as error "Looked for: $EQP_DATA"
    display as error ""
    display as error "Set EQP_DATA at the top of this file to the full"
    display as error "path of stata_test_data.dta, or change directory"
    display as error "to the folder holding it. Type  pwd  to see where"
    display as error "Stata is looking now."
    display as error "=================================================="
    exit 601
}

global EQP_RUN = 0
global EQP_BAD = 0
global EQP_ENGINE ""

capture program drop eqpcheck
program define eqpcheck
    version 17
    args ok label
    if "`ok'" == "" | "`ok'" == "." local ok = 0
    global EQP_RUN = $EQP_RUN + 1
    if (`ok') {
        display as text "   [ok]   `label'"
    }
    else {
        global EQP_BAD = $EQP_BAD + 1
        display as error "   [FAIL] `label'"
    }
end

display as text ""
display as text "=================================================="
display as text "EquiPop field pass, expecting version $EQP_EXPECT"
display as text "data: $EQP_DATA"
display as text "=================================================="


* ==================================================================
* 0. The environment. If this block is unhappy, stop and fix it
*    before reading anything below - every later number depends on
*    the engine being the one this pass was written against.
* ==================================================================
capture noisily {
    equipop doctor
}
local rc = _rc
local ok = (`rc' == 0)
eqpcheck `ok' "block 0: equipop doctor ran without error"

capture python: from sfi import Macro; import equipop; Macro.setGlobal("EQP_ENGINE", equipop.__version__)
if "$EQP_ENGINE" == "" {
    eqpcheck 0 "block 0: could not read the engine version from Python"
}
else {
    display as text "   engine reports version $EQP_ENGINE"
    local ok = ("$EQP_ENGINE" == "$EQP_EXPECT")
    eqpcheck `ok' "block 0: engine version matches $EQP_EXPECT"
}


* ==================================================================
* 1. The simplest possible run. No weight, so every point is one
*    person and k is a number of POINTS.
*    EXPECT: N_100 exactly 100; Dist_100 strictly positive; and the
*    nine rows without coordinates receiving missing results rather
*    than a wrong answer.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop, x(X_local) y(Y_local) k(100)
    summarize N_100 Dist_100

    count if abs(N_100 - 100) > 0.000001 & !missing(N_100)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 1: N_100 is exactly 100 on every row that got one"

    count if Dist_100 <= 0 & !missing(Dist_100)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 1: Dist_100 is strictly positive"

    count if missing(N_100)
    local nmiss = r(N)
    display "   rows with missing N_100: `nmiss'"
    count if missing(X_local) | missing(Y_local)
    local nocoord = r(N)
    local ok = (`nmiss' == `nocoord')
    eqpcheck `ok' "block 1: missing results appear exactly where coordinates are missing"
}
local rc = _rc
if `rc' eqpcheck 0 "block 1 stopped with Stata error r(`rc')"


* ==================================================================
* 2. Several k at once. One pass, three neighbourhoods.
*    EXPECT: each N exact, and Dist_50 <= Dist_100 <= Dist_400 on
*    EVERY row. A larger neighbourhood cannot have a smaller radius;
*    when it did, that was BACKLOG 191, and this ordering is what
*    caught it.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop, x(X_local) y(Y_local) k(50 100 400)
    summarize N_50 N_100 N_400 Dist_50 Dist_100 Dist_400

    count if (abs(N_50-50) > 0.000001 | abs(N_100-100) > 0.000001 ///
        | abs(N_400-400) > 0.000001) & !missing(N_50)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 2: N_50, N_100 and N_400 are all exact"

    count if (Dist_100 < Dist_50 | Dist_400 < Dist_100) ///
        & !missing(Dist_50) & !missing(Dist_400)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 2: Dist rises with k on every row"
}
local rc = _rc
if `rc' eqpcheck 0 "block 2 stopped with Stata error r(`rc')"


* ==================================================================
* 3. A fixed radius instead of a fixed population.
*    EXPECT: N_r1000 VARIES a great deal - that is the whole point of
*    the method. A fixed radius holds different numbers of people in
*    the town centre and in the countryside; a fixed k does not. On
*    this data the standard deviation is around 1,250 people.
*    A larger radius can never hold fewer people.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop, x(X_local) y(Y_local) r(1000 2000)
    summarize N_r1000 N_r2000

    summarize N_r1000
    local sd = r(sd)
    display "   sd(N_r1000) = " %9.1f `sd'
    local ok = (`sd' > 100)
    eqpcheck `ok' "block 3: N_r1000 varies across places, as a fixed radius must"

    count if N_r2000 < N_r1000 & !missing(N_r1000) & !missing(N_r2000)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 3: the wider radius never holds fewer people"
}
local rc = _rc
if `rc' eqpcheck 0 "block 3 stopped with Stata error r(`rc')"


* ==================================================================
* 4. Both at once - k and r in the same run.
*     EXPECT THREE new columns, not four. CORRECTED IN 1.40.6, after
*     the 1.40.5 field run failed this check on John's machine.
*
*     The reason is the whole shape of the method. The two machines
*     are INVERSES of one another:
*        k asks for a number of PEOPLE, and the distance you must
*          travel to reach them is the ANSWER - so Dist_200 exists;
*        r gives the DISTANCE, and the number of people inside it is
*          the answer - so there is nothing left for a Dist_r2000 to
*          report. It could only ever hold 2000, the number you
*          typed in yourself.
*     So k(200) r(2000) yields N_200, Dist_200 and N_r2000. The
*     contract is stated at equipop/stata_bridge.py line 355:
*     r_values -> N_r<r>, T_<v>_r<r>, R_<v>_r<r>.
*
*     The 1.40.5 check asked for a fourth column because the wording
*     "four new columns" was carried across from an older version of
*     this file and never measured - the exact fault this file's own
*     header warns about. The engine was right; the pass was wrong.
*     ALSO EXPECT: N_r2000 far more variable than N_200, which is
*     fixed by construction.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop, x(X_local) y(Y_local) k(200) r(2000)
    summarize N_200 N_r2000

    capture confirm variable N_200 Dist_200 N_r2000
    local ok = (_rc == 0)
    eqpcheck `ok' "block 4: k and r together produce N_200, Dist_200 and N_r2000"

    capture confirm variable Dist_r2000
    if _rc {
        display "   no Dist_r2000, as designed - a radius is an input, not an answer"
    }
    else {
        display "   NOTE: Dist_r2000 now exists. That is a change of contract,"
        display "   not a failure. Tell Claude, and see BACKLOG 203."
    }

    summarize N_200
    local sdk = r(sd)
    summarize N_r2000
    local sdr = r(sd)
    display "   sd(N_200) = " %9.4f `sdk' "    sd(N_r2000) = " %9.1f `sdr'
    local ok = (`sdr' > `sdk')
    eqpcheck `ok' "block 4: the fixed radius varies more than the fixed k"
}
local rc = _rc
if `rc' eqpcheck 0 "block 4 stopped with Stata error r(`rc')"


* ==================================================================
* 5. A population weight. Now k is a number of PEOPLE, not points.
*    Both runs are done here, so the comparison is row by row rather
*    than a memory of the block before.
*    EXPECT: N_200 is 200 PEOPLE, reached in far fewer points, so the
*    weighted Dist_200 is SMALLER than the unweighted one on every
*    row. On this data the means are roughly 65 m against 1,142 m.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop, x(X_local) y(Y_local) k(200) prefix(pts_)
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) prefix(ppl_)
    summarize pts_N_200 ppl_N_200 pts_Dist_200 ppl_Dist_200

    count if abs(ppl_N_200 - 200) > 0.000001 & !missing(ppl_N_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 5: the weighted run reaches exactly 200 people"

    count if ppl_Dist_200 > pts_Dist_200 + 0.000000001 ///
        & !missing(ppl_Dist_200) & !missing(pts_Dist_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 5: 200 people are never further away than 200 points"
}
local rc = _rc
if `rc' eqpcheck 0 "block 5 stopped with Stata error r(`rc')"


* ==================================================================
* 6. A 0/1 marker read as a marker - THE CORRECT SETTING for this
*    data when a weight is present.
*    EXPECT: R_HighEdu_200 inside [0,1] everywhere, mean about 0.21.
*    Note that 0.21 is NOT the share of POINTS marked HighEdu, which
*    is 0.19: this share weights each point by the people standing on
*    it, and marked points here are slightly more populous.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) ///
        treat(HighEdu) treatmode(flags)
    summarize N_200 T_HighEdu_200 R_HighEdu_200

    count if (R_HighEdu_200 < 0 | R_HighEdu_200 > 1) & !missing(R_HighEdu_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 6: the share stays inside 0 and 1"

    count if T_HighEdu_200 > N_200 + 0.000001 & !missing(T_HighEdu_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 6: the group is never larger than the neighbourhood holding it"

    summarize R_HighEdu_200, meanonly
    local m = r(mean)
    display "   mean R_HighEdu_200 = " %8.4f `m'
    local ok = (`m' > 0.15 & `m' < 0.27)
    eqpcheck `ok' "block 6: mean share is in the expected range around 0.21"
}
local rc = _rc
if `rc' eqpcheck 0 "block 6 stopped with Stata error r(`rc')"


* ==================================================================
* 7. THE TRAP THIS DATASET SETS, measured rather than described.
*    treatmode(counts) is the default and is RIGHT when treat() holds
*    people. Here it does not: HighEdu is a 0/1 marker, so under
*    counts the numerator counts POINTS while N_200 counts PEOPLE.
*    The share is then wrong by roughly the mean people per point.
*    EXPECT: the flags share is about 47 times the counts share.
*    Nothing refuses this, because a marker of 0 or 1 is a perfectly
*    possible person count - which is why it is worth seeing once, so
*    the shape of the error is recognisable in real work.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) ///
        treat(HighEdu) treatmode(flags) prefix(f_)
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) ///
        treat(HighEdu) prefix(c_)
    summarize f_R_HighEdu_200 c_R_HighEdu_200

    summarize f_R_HighEdu_200, meanonly
    local mf = r(mean)
    summarize c_R_HighEdu_200, meanonly
    local mc = r(mean)
    local ratio = `mf' / `mc'
    display "   flags mean " %9.5f `mf' "    counts mean " %9.5f `mc'
    display "   ratio = " %8.2f `ratio' "   (mean people per point is 45.5)"
    local ok = (`ratio' > 35 & `ratio' < 60)
    eqpcheck `ok' "block 7: the wrong setting understates the share by about 47x"
}
local rc = _rc
if `rc' eqpcheck 0 "block 7 stopped with Stata error r(`rc')"


* ==================================================================
* 8. No weight at all, so points ARE people and a 0/1 marker IS a
*    count of one. Here treatmode(counts) is the right setting.
*    EXPECT: mean R_HighEdu_200 about 0.18. This is CLOSE TO but not
*    equal to block 6's 0.21, and the difference is real rather than
*    numerical: block 6 weights every point by its population, this
*    block weights every point equally. Two different questions -
*    what share of the PEOPLE around me, and what share of the PLACES
*    around me - with two different answers.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop, x(X_local) y(Y_local) k(200) treat(HighEdu)
    summarize N_200 T_HighEdu_200 R_HighEdu_200

    summarize R_HighEdu_200, meanonly
    local m = r(mean)
    display "   mean R_HighEdu_200 = " %8.4f `m'
    local ok = (`m' > 0.13 & `m' < 0.24)
    eqpcheck `ok' "block 8: unweighted mean share is in the expected range around 0.18"

    count if (R_HighEdu_200 < 0 | R_HighEdu_200 > 1) & !missing(R_HighEdu_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 8: the share stays inside 0 and 1"
}
local rc = _rc
if `rc' eqpcheck 0 "block 8 stopped with Stata error r(`rc')"


* ==================================================================
* 9. Four groups at once.
*    EXPECT: twelve new columns, every share inside [0,1], and the
*    four shares summing to about 0.86 - LowEdu, HighEdu, TheoEdu and
*    VocaEdu do not cover everybody, so the sum must be below 1 and
*    must not be close to it.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop, x(X_local) y(Y_local) k(200) ///
        treat(LowEdu HighEdu TheoEdu VocaEdu)
    generate shares = R_LowEdu_200 + R_HighEdu_200 + R_TheoEdu_200 ///
        + R_VocaEdu_200
    summarize shares

    count if (shares < 0 | shares > 1) & !missing(shares)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 9: the four shares together never exceed 1"

    summarize shares, meanonly
    local m = r(mean)
    display "   mean of the four shares = " %8.4f `m'
    local ok = (`m' > 0.80 & `m' < 0.90)
    eqpcheck `ok' "block 9: the four groups cover about 86 percent of people"
}
local rc = _rc
if `rc' eqpcheck 0 "block 9 stopped with Stata error r(`rc')"


* ==================================================================
* 10. pop() instead of [fweight=]. fweight needs whole numbers;
*     pop() takes fractions. Both routes run here, so the answer is
*     compared row by row.
*     EXPECT: identical. If these ever differ, two routes into the
*     same idea have drifted apart.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) prefix(fw_)
    equipop, x(X_local) y(Y_local) k(200) pop(ValCount) prefix(pp_)
    summarize fw_N_200 pp_N_200 fw_Dist_200 pp_Dist_200

    count if abs(fw_N_200 - pp_N_200) > 0.000001 ///
        & !missing(fw_N_200) & !missing(pp_N_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 10: fweight and pop() agree on the population"

    count if abs(fw_Dist_200 - pp_Dist_200) > 0.000001 ///
        & !missing(fw_Dist_200) & !missing(pp_Dist_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 10: fweight and pop() agree on the distance"
}
local rc = _rc
if `rc' eqpcheck 0 "block 10 stopped with Stata error r(`rc')"


* ==================================================================
* 11 AND 12, now one block. The self-potential ladder - how far a
*     place is from ITSELF - together with the free number that sits
*     between the rungs. These were two blocks until 1.40.5, which
*     meant the free number could only be compared against a rung by
*     remembering the block before. Four runs, one dataset, compared
*     row by row. There is deliberately no block 12.
*     EXPECT: none <= 0.4 <= median <= full on EVERY row.
*     WORTH KNOWING: with a weight and k=100, 100 people are usually
*     found inside the origin cell itself, so most rows report a very
*     small distance and the self-potential is doing most of the
*     work. That is the situation this setting exists for.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(100) ///
        selfpotname(none) prefix(a_)
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(100) ///
        selfpot(0.4) prefix(b_)
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(100) ///
        selfpotname(median) prefix(c_)
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(100) ///
        selfpotname(full) prefix(d_)
    summarize a_Dist_100 b_Dist_100 c_Dist_100 d_Dist_100

    count if a_Dist_100 > b_Dist_100 + 0.000000001 & !missing(a_Dist_100)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 11: none is never further than 0.4"

    count if b_Dist_100 > c_Dist_100 + 0.000000001 & !missing(b_Dist_100)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 11: 0.4 is never further than the median rung"

    count if c_Dist_100 > d_Dist_100 + 0.000000001 & !missing(c_Dist_100)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 11: the median rung is never further than full"

    count if a_Dist_100 == 0 & !missing(a_Dist_100)
    display "   rows resolving inside the origin cell at selfpot none: " r(N)
}
local rc = _rc
if `rc' eqpcheck 0 "block 11 stopped with Stata error r(`rc')"


* ==================================================================
* 13. The overshoot - what to do with the ring of points that crosses
*     k. Two modes, compared row by row.
*     EXPECT: whole gives N_200 >= 200, and on this data the mean is
*     about 999, because a cell here holds around 45 people and whole
*     mode takes the entire crossing ring. proportional gives exactly
*     200 and interpolates Dist inside that ring, so its distance is
*     never the larger of the two.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) ///
        overshoot(whole) prefix(w_)
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) ///
        overshoot(proportional) prefix(p_)
    summarize w_N_200 p_N_200 w_Dist_200 p_Dist_200

    count if w_N_200 < 200 - 0.000001 & !missing(w_N_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 13: whole overshoot never falls short of k"

    count if abs(p_N_200 - 200) > 0.000001 & !missing(p_N_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 13: proportional overshoot lands exactly on k"

    count if p_Dist_200 > w_Dist_200 + 0.000000001 ///
        & !missing(p_Dist_200) & !missing(w_Dist_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 13: the interpolated distance is never the larger one"
}
local rc = _rc
if `rc' eqpcheck 0 "block 13 stopped with Stata error r(`rc')"


* ==================================================================
* 14. The mode that is NOT available here, asked for by name.
*     EXPECT: a refusal that explains itself and points at QGIS or
*     ArcGIS Pro, and a non-zero return code. It must NOT be silently
*     ignored, because an ignored overshoot mode gives a plausible
*     answer to a question nobody asked.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
}
capture equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) ///
    overshoot(sampled)
local rc = _rc
display "   return code was: `rc'"
local ok = (`rc' != 0)
eqpcheck `ok' "block 14: overshoot(sampled) is refused, not ignored"


* ==================================================================
* 15. DECAY - a fixed bandwidth. This is the one to look at hardest,
*     because it is where the MEANING of the output was wrong until
*     1.40 while the numbers still looked plausible.
*     EXPECT, and all three matter:
*       N_300 is exactly 300 - decay does NOT choose the
*         neighbourhood;
*       Dist_300 is IDENTICAL to a run without decay - decay does NOT
*         move the radius;
*       ND_300 is strictly SMALLER than 300 - the same 300 people,
*         each counted for less the further away they stand. On this
*         data the mean is about 284.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) prefix(plain_)
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
        decay(negexp) halflife(800) prefix(dec_)
    summarize plain_N_300 dec_N_300 plain_Dist_300 dec_Dist_300 dec_ND_300

    count if abs(dec_N_300 - 300) > 0.000001 & !missing(dec_N_300)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 15: decay leaves k alone - N_300 is still exactly 300"

    count if abs(plain_Dist_300 - dec_Dist_300) > 0.000001 ///
        & !missing(plain_Dist_300) & !missing(dec_Dist_300)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 15: decay leaves the radius alone - Dist_300 is unchanged"

    count if dec_ND_300 >= dec_N_300 - 0.000000001 & !missing(dec_ND_300)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 15: the decayed total is strictly below the raw total"
}
local rc = _rc
if `rc' eqpcheck 0 "block 15 stopped with Stata error r(`rc')"


* ==================================================================
* 16. A shorter half-life decays harder.
*     EXPECT: ND_300 at half-life 300 below ND_300 at half-life 2000
*     on EVERY row, with the same model. Means about 261 and 293.
*     N_300 stays 300 in both, since only the weighting changed.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
        decay(negexp) halflife(300) prefix(sharp_)
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
        decay(negexp) halflife(2000) prefix(broad_)
    summarize sharp_ND_300 broad_ND_300 sharp_N_300 broad_N_300

    count if sharp_ND_300 > broad_ND_300 + 0.000000001 ///
        & !missing(sharp_ND_300) & !missing(broad_ND_300)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 16: the shorter half-life keeps less on every row"

    count if abs(sharp_N_300 - 300) > 0.000001 & !missing(sharp_N_300)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 16: changing the bandwidth did not change k"
}
local rc = _rc
if `rc' eqpcheck 0 "block 16 stopped with Stata error r(`rc')"


* ==================================================================
* 17. A DIFFERENT CURVE, and the thing about it that is easy to get
*     backwards. CORRECTED IN 1.40.5: the previous version of this
*     block asserted the opposite, and nobody had ever computed it.
*
*     Both models are 0.5 at the half-life BY CONSTRUCTION, so that
*     distance is where they cross. Their shapes differ either side
*     of it. With a half-life of 800 m:
*        negexp  at   50 m = 0.958,   at 3200 m = 0.063
*        power   at   50 m = 0.665,   at 3200 m = 0.433
*     power is the HARSHER curve inside the half-life and the gentler
*     one outside it. "Distant places never quite stop counting" is a
*     statement about the TAIL, and it does not by itself say which
*     model keeps more mass.
*
*     Which one keeps more depends on where the NEIGHBOURHOOD sits
*     relative to the bandwidth you chose. Here a k=300 neighbourhood
*     has a median radius of 48 m against a half-life of 800 m, so it
*     lies almost entirely on the side where power cuts harder.
*     EXPECT: on every row whose whole neighbourhood is inside the
*     half-life, power's ND_300 is BELOW negexp's. On this data that
*     is 10,743 rows, with no exceptions.
*     The reverse is NOT a clean rule and is not asserted: Dist is the
*     distance to the FURTHEST neighbour, so a row can reach past the
*     half-life while most of its 300 people are still well inside.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
        decay(negexp) halflife(800) prefix(ne_)
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
        decay(power) halflife(800) prefix(pw_)
    summarize ne_ND_300 pw_ND_300 ne_Dist_300

    count if ne_Dist_300 < 800 & !missing(ne_Dist_300)
    local inside = r(N)
    display "   rows whose whole neighbourhood is inside the half-life: `inside'"
    local ok = (`inside' > 1000)
    eqpcheck `ok' "block 17: there are enough inside-bandwidth rows to test"

    count if ne_Dist_300 < 800 & pw_ND_300 >= ne_ND_300 ///
        & !missing(pw_ND_300) & !missing(ne_ND_300)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 17: inside the half-life, power keeps less than negexp"

    count if abs(ne_Dist_300 - pw_Dist_300) > 0.000001 ///
        & !missing(ne_Dist_300) & !missing(pw_Dist_300)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 17: changing the model did not move the radius"
}
local rc = _rc
if `rc' eqpcheck 0 "block 17 stopped with Stata error r(`rc')"


* ==================================================================
* 18. Decay on a treatment group as well - the decayed share.
*     EXPECT: TD below T, ND below N, RD inside [0,1].
*     AND THE POINT OF THE BLOCK: RD equals R exactly on most rows
*     here, and differs by as much as 0.27 on others. That is not a
*     fault. Where every neighbour stands at the same distance - and
*     on this data most neighbourhoods resolve inside the origin cell
*     - the decay weight is a constant that CANCELS in the ratio
*     TD/ND. RD moves away from R only where the group sits at a
*     DIFFERENT distance profile from the population around it, which
*     is precisely the segregation signal the measure exists to find.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
        treat(HighEdu) treatmode(flags) decay(negexp) halflife(800)
    summarize N_300 ND_300 T_HighEdu_300 TD_HighEdu_300 ///
        R_HighEdu_300 RD_HighEdu_300

    count if TD_HighEdu_300 > T_HighEdu_300 + 0.000000001 ///
        & !missing(TD_HighEdu_300)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 18: the decayed group total never exceeds the raw one"

    count if ND_300 > N_300 + 0.000000001 & !missing(ND_300)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 18: the decayed population never exceeds the raw one"

    count if (RD_HighEdu_300 < 0 | RD_HighEdu_300 > 1) ///
        & !missing(RD_HighEdu_300)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 18: the decayed share stays inside 0 and 1"

    count if abs(RD_HighEdu_300 - R_HighEdu_300) > 0.001 ///
        & !missing(RD_HighEdu_300) & !missing(R_HighEdu_300)
    local moved = r(N)
    display "   rows where the decayed share differs from the raw share: `moved'"
    local ok = (`moved' > 0)
    eqpcheck `ok' "block 18: the decayed share moves somewhere - the measure is live"
}
local rc = _rc
if `rc' eqpcheck 0 "block 18 stopped with Stata error r(`rc')"


* ==================================================================
* 19. A VARIABLE bandwidth - each place carries its own half-life,
*     tight where people are dense and broad where they are sparse.
*     The bandwidth comes from an UNWEIGHTED k=400 run: that radius
*     has real spread (about 98 m to 18 km here) and no zeros,
*     because 400 points never fit inside one cell. A bandwidth taken
*     from a weighted k=100 run is almost all zeros on this data and
*     collapses every row into a single bin, which tests nothing.
*     EXPECT: the log reports 8 bins, not one; the bandwidth has no
*     zeros; ND_300 stays below N_300 everywhere.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop, x(X_local) y(Y_local) k(400) prefix(d_)
    generate bandwidth = d_Dist_400
    summarize bandwidth, detail

    count if bandwidth <= 0 & !missing(bandwidth)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 19: every place has a usable bandwidth of its own"

    summarize bandwidth
    local sd = r(sd)
    local ok = (`sd' > 100)
    eqpcheck `ok' "block 19: the bandwidth genuinely varies between places"

    equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
        decay(negexp) halflifevar(bandwidth) bins(8)
    summarize N_300 ND_300

    count if ND_300 >= N_300 - 0.000000001 & !missing(ND_300)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 19: the variable-bandwidth decayed total stays below the raw one"
}
local rc = _rc
if `rc' eqpcheck 0 "block 19 stopped with Stata error r(`rc')"


* ==================================================================
* 20. MISSING-VALUE CODES. REBUILT IN 1.40.5.
*
*     The previous version declared missing(0) on ValFloat and fed it
*     to treat(). The guard was right to refuse that, and the refusal
*     halted the pass here - which is why blocks 21 and 22 have never
*     run in the field at all. ValFloat is a CONTINUOUS magnitude
*     running to 23,254, while the population at a point tops out at
*     98. treat() holds a number of PEOPLE, and a share is only a
*     share when numerator and denominator are counted in the same
*     units. A magnitude divided by a headcount is not bounded by one
*     and is not a share of anything. A continuous measure belongs in
*     machine 2 - mean, median, quantiles, Gini over the
*     neighbourhood - not in treat().
*
*     So this block now builds a genuine COUNT column. Grp is half
*     the population at each point, which can never exceed it, and
*     every twelfth row carries the sentinel -999 meaning NO DATA.
*     Every twelfth is deliberate rather than random, so the count is
*     identical on every machine and every Stata version.
*
*     EXPECT: exactly 907 sentinel rows; the run reports how many
*     values it blanked; blanked places still count as PEOPLE towards
*     k and still receive their own results; and the share divides by
*     the people actually OBSERVED, so it sits just under 0.5 rather
*     than being dragged down by the blanked cases. Mean about 0.494.
*     Also shows [if], which restricts the ROWS THAT GET RESULTS, not
*     the people who count as neighbours.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    generate Grp = floor(ValCount / 2)
    replace Grp = -999 if mod(ID, 12) == 0

    count if Grp == -999
    local nsent = r(N)
    display "   sentinel rows: `nsent'"
    local ok = (`nsent' == 907)
    eqpcheck `ok' "block 20: the synthetic sentinel lands on exactly 907 rows"

    equipop [fweight=ValCount] if X_local > 520000 & !missing(X_local), ///
        x(X_local) y(Y_local) k(200) treat(Grp) missing(-999)
    summarize N_200 T_Grp_200 R_Grp_200

    count if abs(N_200 - 200) > 0.000001 & !missing(N_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 20: blanked cases still count as people towards k"

    count if (R_Grp_200 < 0 | R_Grp_200 > 1) & !missing(R_Grp_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 20: the share stays inside 0 and 1"

    count if T_Grp_200 > N_200 + 0.000001 & !missing(T_Grp_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 20: the group never exceeds the neighbourhood"

    summarize R_Grp_200, meanonly
    local m = r(mean)
    display "   mean R_Grp_200 = " %8.4f `m' "   (denominator is the OBSERVED people)"
    local ok = (`m' > 0.44 & `m' < 0.52)
    eqpcheck `ok' "block 20: the share divides by the observed part, landing near 0.494"

    count if X_local <= 520000 & !missing(N_200)
    local ok = (r(N) == 0)
    eqpcheck `ok' "block 20: rows outside the [if] received no results"
}
local rc = _rc
if `rc' eqpcheck 0 "block 20 stopped with Stata error r(`rc')"


* ==================================================================
* 21. THREE refusals that must stay refusals. None of these should
*     run. A guard that stops guarding is invisible in the answer,
*     because the answer still looks like an answer - which is why
*     each return code is CHECKED here rather than printed.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    generate Grp = floor(ValCount / 2)
    replace Grp = -999 if mod(ID, 12) == 0
}
local rc = _rc
if `rc' eqpcheck 0 "block 21 could not prepare its data, r(`rc')"

capture equipop, x(X_local) y(Y_local) k(200) project
local rc = _rc
display "   project on metric data, return code: `rc'"
local ok = (`rc' != 0)
eqpcheck `ok' "block 21: project on already-metric data is refused"

capture equipop, x(X_local) y(Y_local) k(200) unit(2.5)
local rc = _rc
display "   fractional cell size, return code: `rc'"
local ok = (`rc' != 0)
eqpcheck `ok' "block 21: a fractional cell size is refused, not rounded"

capture equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) treat(Grp)
local rc = _rc
display "   undeclared -999 in treat(), return code: `rc'"
local ok = (`rc' != 0)
eqpcheck `ok' "block 21: an undeclared negative sentinel in treat() is refused"


* ==================================================================
* 22. What comes back in r(). Useful when scripting a batch, and the
*     only block that checks the command reports on itself.
* ==================================================================
capture noisily {
    use "$EQP_DATA", clear
    equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) ///
        treat(HighEdu) treatmode(flags)
    return list

    local rk "`r(k)'"
    local rvars "`r(varlist)'"
    local rorig = r(N_origins)

    local ok = ("`rk'" == "200")
    eqpcheck `ok' "block 22: r(k) reports the k that was asked for"

    local ok = ("`rvars'" != "")
    eqpcheck `ok' "block 22: r(varlist) names the variables that were created"

    local ok = (`rorig' > 0)
    eqpcheck `ok' "block 22: r(N_origins) reports a positive number of origins"
}
local rc = _rc
if `rc' eqpcheck 0 "block 22 stopped with Stata error r(`rc')"


* ==================================================================
* THE VERDICT
* ==================================================================
* The number of checks is PINNED. If fewer run than expected, a block
* died before reaching its checks and the reason is above in this log.

global EQP_EXPECT_CHECKS = 57

display as text ""
display as text "=================================================="
display as text "EquiPop field pass - VERDICT"
display as text "  version expected : $EQP_EXPECT"
display as text "  engine reported  : $EQP_ENGINE"
display as text "  checks run       : $EQP_RUN   (expected $EQP_EXPECT_CHECKS)"
display as text "  checks failed    : $EQP_BAD"
display as text "=================================================="

if $EQP_RUN != $EQP_EXPECT_CHECKS {
    display as error "INCOMPLETE: $EQP_RUN checks ran, $EQP_EXPECT_CHECKS were expected."
    display as error "A block stopped early. Search this log for [FAIL] and for"
    display as error "the word error, and send the whole log back."
    exit 9
}

if $EQP_BAD > 0 {
    display as error "FAILED: $EQP_BAD of $EQP_RUN checks did not pass."
    display as error "Search this log for [FAIL] and send the whole log back."
    exit 9
}

display as result "PASSED: all $EQP_RUN checks."
display as text "Save this log. It is the evidence that this release ran."
