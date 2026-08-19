*! EquiPop 1.40.3 - a test pass over stata_test_data.dta
*!
*! Twenty runs. Each block reloads the data, so any block can be run
*! on its own and nothing carries over from the one before.
*!
*! WHAT THIS DATA IS: 10,892 points on a metric grid (X 503-537 km,
*! Y 442-484 km - about 34 by 42 km). LowEdu, HighEdu, TheoEdu and
*! VocaEdu are 0/1 MARKERS, not counts. ValCount is a count per point,
*! 0-98, mean 45.5. ValFloat is continuous, 0-23,254.
*!
*! READ THIS BEFORE BLOCK 7: because the education variables are 0/1
*! markers, any run that ALSO supplies a population needs
*! treatmode(flags). Blocks 6 and 7 are the same run with the two
*! settings, so you can see the difference for yourself.
*!
*! Each block says what to look at. Where a number is predictable it
*! is written down, so a wrong answer is visible rather than merely
*! plausible.

version 17
clear all
set more off

local DATA "C:\Data\EQP\ForGit\equipop_dev_pkg\stata\stata_test_data.dta"


* ==================================================================
* 0. The environment. Run this first; if it is unhappy, stop here.
* ==================================================================
equipop doctor


* ==================================================================
* 1. The simplest possible run. No weight, so every point is one
*    person and k is a number of POINTS.
*    LOOK FOR: N_100 = 100 exactly. Dist_100 positive everywhere.
* ==================================================================
use "`DATA'", clear
equipop, x(X_local) y(Y_local) k(100)
summarize N_100 Dist_100


* ==================================================================
* 2. Several k at once. One pass, three neighbourhoods.
*    LOOK FOR: N rises with k; Dist_50 < Dist_100 < Dist_400 for
*    every row. If any row breaks that ordering, something is wrong.
* ==================================================================
use "`DATA'", clear
equipop, x(X_local) y(Y_local) k(50 100 400)
summarize N_50 N_100 N_400 Dist_50 Dist_100 Dist_400
count if Dist_100 < Dist_50 | Dist_400 < Dist_100


* ==================================================================
* 3. A fixed radius instead of a fixed population.
*    LOOK FOR: N_r1000 VARIES a lot - that is the whole point of the
*    method. A fixed radius holds different numbers of people in the
*    town centre and the countryside; a fixed k does not.
* ==================================================================
use "`DATA'", clear
equipop, x(X_local) y(Y_local) r(1000 2000)
summarize N_r1000 N_r2000


* ==================================================================
* 4. Both at once - k and r in the same run.
*    LOOK FOR: four new columns, and N_r2000 far more variable than
*    N_200.
* ==================================================================
use "`DATA'", clear
equipop, x(X_local) y(Y_local) k(200) r(2000)
summarize N_200 N_r2000


* ==================================================================
* 5. A population weight. Now k is a number of PEOPLE, not points.
*    LOOK FOR: N_200 = 200 people, reached in FEWER points than
*    before, so Dist_200 is SMALLER than the Dist_200 an unweighted
*    run would give.
* ==================================================================
use "`DATA'", clear
equipop [fweight=ValCount], x(X_local) y(Y_local) k(200)
summarize N_200 Dist_200


* ==================================================================
* 6. A 0/1 marker read as a marker - THE CORRECT SETTING for this
*    data when a weight is present.
*    LOOK FOR: R_HighEdu_200 between 0 and 1, and its mean somewhere
*    near 0.19, which is the share of points marked HighEdu.
* ==================================================================
use "`DATA'", clear
equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) ///
    treat(HighEdu) treatmode(flags)
summarize N_200 T_HighEdu_200 R_HighEdu_200


* ==================================================================
* 7. THE SAME RUN with the default treatmode(counts). This is the
*    trap this dataset sets, and nothing refuses it.
*    LOOK FOR: T_HighEdu_200 is now a count of POINTS while N_200 is
*    a count of PEOPLE, so R_HighEdu_200 comes out far too small -
*    roughly a factor of 45, the mean people per point. Compare the
*    two means from blocks 6 and 7 side by side.
*    This is worth seeing once, so the shape of the error is
*    recognisable if it ever turns up in real work.
* ==================================================================
use "`DATA'", clear
equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) ///
    treat(HighEdu)
summarize N_200 T_HighEdu_200 R_HighEdu_200


* ==================================================================
* 8. No weight at all, so points ARE people and a 0/1 marker IS a
*    count of one. Here treatmode(counts) is right.
*    LOOK FOR: R_HighEdu_200 mean near 0.19 again - matching block 6,
*    by a different route.
* ==================================================================
use "`DATA'", clear
equipop, x(X_local) y(Y_local) k(200) treat(HighEdu)
summarize N_200 T_HighEdu_200 R_HighEdu_200


* ==================================================================
* 9. Four groups at once.
*    LOOK FOR: twelve new columns. The four shares should sum to
*    about 0.86 - LowEdu, HighEdu, TheoEdu and VocaEdu do not cover
*    everybody.
* ==================================================================
use "`DATA'", clear
equipop, x(X_local) y(Y_local) k(200) ///
    treat(LowEdu HighEdu TheoEdu VocaEdu)
gen shares = R_LowEdu_200 + R_HighEdu_200 + R_TheoEdu_200 + R_VocaEdu_200
summarize shares


* ==================================================================
* 10. pop() instead of [fweight=]. fweight needs whole numbers;
*     pop() takes fractions.
*     LOOK FOR: the same answer as block 5. If these differ, the two
*     routes into the same idea have drifted apart.
* ==================================================================
use "`DATA'", clear
equipop, x(X_local) y(Y_local) k(200) pop(ValCount)
summarize N_200 Dist_200


* ==================================================================
* 11. The self-potential ladder - how far a place is from ITSELF.
*     Three rungs, three prefixes, one dataset, so they can be
*     compared row by row.
*     LOOK FOR: Dist rises from none to median to full. With none,
*     some rows can show Dist = 0.
* ==================================================================
use "`DATA'", clear
equipop [fweight=ValCount], x(X_local) y(Y_local) k(100) ///
    selfpotname(none) prefix(a_)
equipop [fweight=ValCount], x(X_local) y(Y_local) k(100) ///
    selfpotname(median) prefix(b_)
equipop [fweight=ValCount], x(X_local) y(Y_local) k(100) ///
    selfpotname(full) prefix(c_)
summarize a_Dist_100 b_Dist_100 c_Dist_100
count if a_Dist_100 == 0


* ==================================================================
* 12. The free number, for anything between the rungs.
*     LOOK FOR: Dist_100 between the none and median results above.
* ==================================================================
use "`DATA'", clear
equipop [fweight=ValCount], x(X_local) y(Y_local) k(100) selfpot(0.4)
summarize Dist_100


* ==================================================================
* 13. The overshoot - what to do with the ring of points that
*     crosses k. Two modes, compared row by row.
*     LOOK FOR: whole gives N_200 >= 200, often more. proportional
*     gives exactly 200. Under proportional, Dist is interpolated
*     inside the crossing ring, so it is slightly SMALLER.
* ==================================================================
use "`DATA'", clear
equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) ///
    overshoot(whole) prefix(w_)
equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) ///
    overshoot(proportional) prefix(p_)
summarize w_N_200 p_N_200 w_Dist_200 p_Dist_200


* ==================================================================
* 14. The mode that is NOT available here, asked for by name.
*     LOOK FOR: a refusal that explains itself and points at QGIS or
*     ArcGIS Pro. It should NOT be silently ignored.
* ==================================================================
use "`DATA'", clear
capture equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) ///
    overshoot(sampled)
display "return code was: " _rc


* ==================================================================
* 15. DECAY - a fixed bandwidth. This is the one to look at hardest.
*     LOOK FOR, and all three matter:
*       N_300 is exactly 300 - the decay does NOT choose the
*         neighbourhood;
*       Dist_300 is identical to a run without decay - the decay does
*         NOT move the radius;
*       ND_300 is SMALLER than 300 - the decayed population.
* ==================================================================
use "`DATA'", clear
equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) prefix(plain_)
equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
    decay(negexp) halflife(800) prefix(dec_)
summarize plain_N_300 dec_N_300 plain_Dist_300 dec_Dist_300 dec_ND_300
count if abs(plain_Dist_300 - dec_Dist_300) > 0.000001
count if dec_ND_300 > dec_N_300


* ==================================================================
* 16. A shorter half-life decays harder.
*     LOOK FOR: ND_300 with halflife 300 is smaller than ND_300 with
*     halflife 2000, on every row. N_300 is 300 in both.
* ==================================================================
use "`DATA'", clear
equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
    decay(negexp) halflife(300) prefix(sharp_)
equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
    decay(negexp) halflife(2000) prefix(broad_)
summarize sharp_ND_300 broad_ND_300
count if sharp_ND_300 > broad_ND_300


* ==================================================================
* 17. A different curve. power falls fast and then very slowly, so
*     distant people never quite stop counting.
*     LOOK FOR: at the same half-life, power keeps MORE mass than
*     negexp - so power's ND_300 is the larger of the two.
* ==================================================================
use "`DATA'", clear
equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
    decay(negexp) halflife(800) prefix(ne_)
equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
    decay(power) halflife(800) prefix(pw_)
summarize ne_ND_300 pw_ND_300


* ==================================================================
* 18. Decay on a treatment group as well - the decayed share.
*     LOOK FOR: TD below T, ND below N, and RD close to R but not
*     identical. RD differs from R only where the group sits at a
*     different distance from the origin than everybody else - which
*     is exactly the segregation signal.
* ==================================================================
use "`DATA'", clear
equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
    treat(HighEdu) treatmode(flags) decay(negexp) halflife(800)
summarize N_300 ND_300 T_HighEdu_300 TD_HighEdu_300 ///
    R_HighEdu_300 RD_HighEdu_300


* ==================================================================
* 19. A VARIABLE bandwidth - each place carries its own half-life,
*     tight where people are dense and broad where they are sparse.
*     The bandwidth comes from an UNWEIGHTED k=400 run: that radius
*     has real spread (roughly 100 m to 18 km here) and no zeros,
*     because 400 points never fit inside one cell. A bandwidth taken
*     from a weighted k=100 run is almost all zeros on this data -
*     most origins resolve inside their own cell - and flooring it
*     collapses every row into a single bin, which tests nothing.
*     LOOK FOR: the log should report SEVERAL bins, not one. And
*     ND_300 below N_300 on every row.
* ==================================================================
use "`DATA'", clear
equipop, x(X_local) y(Y_local) k(400) prefix(d_)
gen bandwidth = d_Dist_400
summarize bandwidth, detail
equipop [fweight=ValCount], x(X_local) y(Y_local) k(300) ///
    decay(negexp) halflifevar(bandwidth) bins(8)
summarize N_300 ND_300
count if ND_300 > N_300


* ==================================================================
* 20. Missing-value codes, on a variable that actually has a
*     sentinel. ValFloat is continuous and holds 0 where the value is
*     unknown; declaring it means those places still count as PEOPLE
*     towards k and still receive their own results, but contribute
*     nothing of their own - and the share divides by the people
*     actually observed.
*     Do NOT do this to a 0/1 marker like HighEdu: there 0 is a real
*     category, and declaring it missing blanks 81% of the data.
*     Also shows [if], which restricts the ROWS THAT GET RESULTS, not
*     the people who count as neighbours.
*     LOOK FOR: the run reports how many values were blanked; rows
*     outside the [if] have missing results; and the neighbourhoods
*     of the rows inside it still reach across them.
* ==================================================================
use "`DATA'", clear
count if ValFloat == 0
equipop [fweight=ValCount] if X_local > 520000, ///
    x(X_local) y(Y_local) k(200) treat(ValFloat) missing(0)
summarize N_200 T_ValFloat_200 R_ValFloat_200
count if missing(N_200)


* ==================================================================
* 21. Two refusals that should be refusals. Neither should run.
*     LOOK FOR: a clear message each time, and a non-zero return
*     code. project on data that is ALREADY metric must not silently
*     mangle it; a fractional cell size must not be silently rounded.
* ==================================================================
use "`DATA'", clear
capture equipop, x(X_local) y(Y_local) k(200) project
display "project on metric data, return code: " _rc

capture equipop, x(X_local) y(Y_local) k(200) unit(2.5)
display "fractional cell size, return code: " _rc


* ==================================================================
* 22. What comes back in r(). Useful when scripting a batch.
* ==================================================================
use "`DATA'", clear
equipop [fweight=ValCount], x(X_local) y(Y_local) k(200) ///
    treat(HighEdu) treatmode(flags)
return list


display as text ""
display as text "Test pass complete."
