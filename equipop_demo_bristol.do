*! EquiPop 1.41.1 - Bristol County, Rhode Island: the argument in one run
*!
*! FOR THE PRESENTATION. Six short sections. Each one prints a small
*! number of figures you can read straight off the screen.
*!
*! Every EXPECT figure below was measured against THIS dataset through
*! equipop/stata_bridge.py, the same code the .ado calls, before this
*! file was written. If a number on your screen differs from the number
*! in the comment beside it, something has changed and it is worth
*! knowing before you are standing up.
*!
*! THE DATA: 1,074 census blocks, Bristol County RI, 2022. Population
*! 50,793 - a real block-level count. The ACS attributes are NOT block
*! level: they are BLOCK GROUP estimates, 37 of them, back-filled onto
*! the blocks. Section 2 shows what that does if you forget it.
*!
*! NEEDS pyproj, because section 3 projects. Run  equipop doctor  first
*! if you are unsure; it says so plainly.

version 17
clear all
set more off


* ==================================================================
* CONFIGURATION - the only line you edit
* ==================================================================
* Full path to BristolCounty2022.dta. Leave it EMPTY and the script
* looks in the current working directory - type  pwd  to see where.

global BRIS ""

if "$BRIS" == "" global BRIS "BristolCounty2022.dta"

capture confirm file "$BRIS"
if _rc {
    display as error "STOP: BristolCounty2022.dta not found."
    display as error "Looked for: $BRIS"
    display as error "Set BRIS at the top of this file, or change directory"
    display as error "to the folder holding it. Type  pwd  to see where."
    exit 601
}

use "$BRIS", clear


* ==================================================================
* 1. THE GEOGRAPHY YOU ARE HANDED
* ==================================================================
* Three nested containers, and only the smallest one has a real count
* of people in it.
* EXPECT: 1,074 blocks | 37 block groups | 11 tracts | 50,793 people
*         113 blocks hold nobody at all - and they still get results,
*         because "how many people are near this empty place" is a
*         perfectly good question.

display as text _n "--- 1. the geography ---"
count
display "blocks                 : " r(N)
quietly levelsof block_group_geoid, local(bgs)
display "block groups           : " `: word count `bgs''
quietly levelsof tract_code, local(trs)
display "tracts                 : " `: word count `trs''
quietly summarize population
display "people (block counts)  : " %12.0fc r(sum)
count if population == 0
display "blocks with nobody      : " r(N)


* ==================================================================
* 2. WHY THE SOURCE GEOGRAPHY IS THE PROBLEM
* ==================================================================
* B02001_E001 is the ACS population total. It is measured for the 37
* BLOCK GROUPS and repeated onto every block inside each one. Add it up
* across blocks and you count each block group about thirty times over.
* EXPECT: 50,658 across block groups | 1,582,709 across blocks
*         - a county of fifty thousand people apparently holding one
*         and a half million.
*
* THIS IS NOT A FAULT IN THE DATA. It is what an areal unit IS: a
* container whose value belongs to the container, not to the things
* inside it. Everything downstream inherits that - and a neighbourhood
* drawn as "the block group I happen to fall in" inherits it too.

display as text _n "--- 2. the back-fill, made visible ---"
quietly summarize B02001_E001
display "summed over 1,074 blocks       : " %14.0fc r(sum)
preserve
    quietly bysort block_group_geoid: keep if _n == 1
    quietly summarize B02001_E001
    display "summed over 37 block groups    : " %14.0fc r(sum)
restore
display "census block count, for comparison: " as result "50,793"


* ==================================================================
* 3. PROJECTION - the beginner's door
* ==================================================================
* The coordinates arrive as degrees. Nearest-neighbour work needs
* metres, and the command will do it rather than making you find a
* projection first. NOTE THE ORDER: x() is LONGITUDE, y() is LATITUDE.
* Degrees are only replaced on the way IN - your dataset keeps them,
* so you can run this as many times as you like.
* EXPECT: equipop: projected to UTM zone 19N (EPSG:32619)
*         r(epsg) = 32619
* The county is about 10.6 km east-west and 14.9 km north-south.

display as text _n "--- 3. projection ---"
equipop, x(centroid_longitude) y(centroid_latitude) k(1000) ///
    pop(population) project prefix(prj_)
display "r(epsg) = " r(epsg)
display "r(crs)  = " r(crs)


* ==================================================================
* 4. THE BESPOKE NEIGHBOURHOOD - the same SIZE everywhere, a
*    different SHAPE everywhere
* ==================================================================
* k is a number of PEOPLE, so every block gets a neighbourhood holding
* the same population. What varies is how far you must travel to find
* them - and that variation IS the density of the place.
* EXPECT: N exactly 300 / 1,000 / 3,000 on every block, and
*         Dist_300   mean   338 m   median   286 m   max 2,768 m
*         Dist_1000  mean   638 m   median   563 m   max 2,942 m
*         Dist_3000  mean 1,172 m   median 1,104 m   max 3,223 m
*
* THE NUMBER TO HOLD ON TO: the mean k=1000 radius is 638 m. The mean
* block group here covers 1.69 km2 - a circle of radius 733 m. So a
* thousand-person neighbourhood is about the size of a block group.
* The difference is not the size. It is that this one is centred on
* the person and that one is centred on a boundary.

display as text _n "--- 4. how far to reach k people ---"
equipop, x(centroid_longitude) y(centroid_latitude) ///
    k(300 1000 3000) pop(population) project
summarize N_300 N_1000 N_3000 Dist_300 Dist_1000 Dist_3000

quietly summarize land_area_m2
local bgarea = r(sum) / 37
display _n "county land area          : " %8.1f `=r(sum)/1000000' " km2"
display "mean block group         : " %8.2f `=`bgarea'/1000000' " km2"
display "  ...as an equal circle  : " %8.0f `=sqrt(`bgarea'/_pi)' " m radius"
quietly summarize Dist_1000
display "mean k=1000 radius       : " %8.0f r(mean) " m"


* ==================================================================
* 5. DISTANCE DECAY - the same thousand people, counted for less the
*    further away they stand
* ==================================================================
* Decay does NOT choose the neighbourhood and does NOT move its edge.
* It weights the people inside it. Watch three things:
*   N_1000    stays exactly 1,000
*   Dist_1000 is IDENTICAL to section 4 - to the last decimal
*   ND_1000   falls to about 754
* EXPECT: ND_1000 mean 753.8, min 185.9. Dist unchanged, difference 0.
* The half-life is 1,000 m, chosen to sit near the block-group radius
* of 733 m so the weighting is comparable to the unit being replaced.

display as text _n "--- 5. decay ---"
equipop, x(centroid_longitude) y(centroid_latitude) k(1000) ///
    pop(population) project decay(negexp) halflife(1000) prefix(dec_)
summarize dec_N_1000 dec_ND_1000 dec_Dist_1000

count if abs(dec_Dist_1000 - Dist_1000) > 0.000001
display "blocks whose radius moved when decay was applied: " as result r(N) ///
    as text "   (it should be none)"


* ==================================================================
* 6. THE ARGUMENT
* ==================================================================
* A context measure, two ways, on the same people.
*
* THE TREATMENT. The ACS race table is a block-group total, so it
* cannot go into treat() as it stands - see section 2. What CAN is a
* block-level estimate: apply the block group's RATE to the block's own
* census count. That is a headcount, in the same units as the
* population, and it can never exceed the people actually standing
* there - which is what treat() requires and what the command checks.
* EXPECT: 4,492 estimated non-white residents of 50,793 - 8.8 per cent.
*
* treatmode() is left at its default, counts, and that is CORRECT here
* because NonWhite really is a number of people. It would be wrong if
* NonWhite were a 0/1 marker - see block 7 of equipop_test_pass.do,
* which measures how far wrong.

display as text _n "--- 6. the argument ---"
generate bg_share = 1 - B02001_E002 / B02001_E001
generate NonWhite = population * bg_share
quietly summarize NonWhite
display "estimated non-white residents : " %10.0fc r(sum) "  of 50,793"

equipop, x(centroid_longitude) y(centroid_latitude) k(1000) ///
    pop(population) project treat(NonWhite) prefix(eq_)

* EXPECT: eq_R_NonWhite_1000 mean .0886, min .0088, max .4183
summarize bg_share eq_R_NonWhite_1000

* How many different answers does each measure give to 1,074 blocks?
* EXPECT: 37 against 889.
quietly levelsof bg_share, local(v1)
display _n "distinct values, block group  : " `: word count `v1''
quietly egen eq_tag = group(eq_R_NonWhite_1000)
quietly summarize eq_tag
display "distinct values, EquiPop      : " r(max)

* Inside ONE block group, the block-group measure cannot vary at all.
* The neighbourhood measure does, because the neighbourhoods reach
* across the boundary and pick up different people.
* EXPECT: mean spread .0764, median .0672, max .2219
bysort block_group_geoid: egen eq_lo = min(eq_R_NonWhite_1000)
bysort block_group_geoid: egen eq_hi = max(eq_R_NonWhite_1000)
generate eq_spread = eq_hi - eq_lo
quietly bysort block_group_geoid: keep if _n == 1
display _n "within a single block group, the EquiPop share spans:"
summarize eq_spread
display "the block-group share spans exactly 0, by construction"

* And how far does a block's real context sit from the label it was
* given? EXPECT: 395 blocks differ by more than .02, 152 by more than
* .05, 25 by more than .10, and the largest gap is .2908.
use "$BRIS", clear
quietly generate bg_share = 1 - B02001_E002 / B02001_E001
quietly generate NonWhite = population * bg_share
quietly equipop, x(centroid_longitude) y(centroid_latitude) k(1000) ///
    pop(population) project treat(NonWhite) prefix(eq_)
generate gap = abs(eq_R_NonWhite_1000 - bg_share)
display _n "blocks whose measured context differs from their block group:"
foreach t in 0.02 0.05 0.10 {
    quietly count if gap > `t' & !missing(gap)
    display "   by more than `t' : " %5.0f r(N) " of 1,074"
}
quietly summarize gap
display "   largest gap        : " %8.4f r(max)


* ==================================================================
* THE CAVEAT THAT BELONGS ON THE SLIDE
* ==================================================================
* Say this before somebody in the audience says it for you.
*
* The attribute varies at BLOCK GROUP resolution - 37 values - and has
* been back-filled onto 1,074 blocks. So the within-block-group
* variation shown in section 6 comes from the NEIGHBOURHOODS crossing
* boundaries, not from any finer knowledge of who lives where. This
* method cannot invent detail the source data does not contain.
*
* What it can do is stop the boundary from deciding the answer. Two
* households on opposite sides of a block-group line are neighbours,
* and the source geography is obliged to call them strangers. That is
* the claim, and it is enough.
*
* If a Gini or any other inequality measure goes on a slide from this
* dataset, the same caution applies twice over: it would measure
* dispersion between 37 area medians, not between households, and it
* will understate household inequality accordingly.

display as text _n "=================================================="
display as text "Bristol County run complete."
display as text "Compare each figure against the EXPECT comment above it."
display as text "=================================================="
