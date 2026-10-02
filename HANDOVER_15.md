# HANDOVER 15

*Session 12. Where 14 ended at **1.46.4**, this ends at **1.51.0**:
1,342 tests, SIX machines in QGIS and five in Pro, complete in-dialog
help in Pro for the first time, one analytical choice validated
against a published paper rather than against itself, a test that
asks whether anybody can reach any of it, the published
distance-decay method restored after twelve releases of silent
departure - and **equipop published on the SSC archive**, which is
the distribution the Stata Journal paper needs and the first time
this project has had a release it cannot quietly amend.*

*Amended through 1.50.0 rather than superseded: same session. Read
section 0 first - four of the last five releases were field findings,
none of them from the backlog, and three were about the project
telling a user something untrue. 1.50.0 is the exception: three items
chosen FROM the backlog, and the first thing they found was that the
backlog's own head was pointing at finished work.*

---

## 0b. 1.51.0 - THE FIRST PULL REQUEST FROM OUTSIDE

Marina (GitHub `lizardie`) opened PR #1 while preparing the Stata
Journal submission. **Four findings, all real, all reproduced here
before anything was taken.** Read this section before touching the
Stata door or the radius path.

**ONE OF THEM WAS MINE, FROM THE DAY BEFORE.** Her `equipop.pkg`
declares the examples and the dataset with `f`; 1.50.0's BACKLOG 330
used `g`, on my belief that `g` meant "ancillary". It does not: `g` is
PLATFORM-SPECIFIC, `g PLATFORMNAME sourcefile targetfile`, for shipping
a different compiled plugin per OS. Stata would have read
`equipop_example.do` as a platform name with no files after it and
**those three files would not have installed at all**. `f` is right -
Stata routes a file by its EXTENSION, installing .ado/.sthlp and
fetching .do/.dta with `net get`, which is what `all` performs.
**And the test I wrote beside that change validated the bug**: it
walked the `g` lines and checked the file existed, which it did.

**THE DEEP ONE: FOUR FORMATTERS FOR ONE LABEL.** A radius becomes part
of a column name, and four places formatted that number - fastcounts.
_lab, analysis's suffix, stata_bridge's labs, and doors/fields._fmt_num
- three with `f"{x:g}"` and one with `str(int(f))`. `:g` carries six
significant digits and goes exponential, so:

| door | r(1000000) gave |
|---|---|
| Python | `N_r1e+06` |
| ArcGIS Pro | `N_r1e_06` (sanitised, unreadable) |
| QGIS | `N_r1e+06` |
| Stata | **crash** - illegal variable name |

and the PREDICTION promised `N_r1000000`, in a function whose
docstring says it is "validated against the real dispatch ... and does
not drift into a guess". Two radii agreeing to six digits also
collapsed into ONE column, silently, because the engine's output is a
dict. `equipop/labels.py` is now the one formatter, used by the engine
AND the prediction, fixing it at the source rather than sanitising at
an output boundary. **Every radius anybody has used keeps its name.**

**WHERE I DID NOT FOLLOW HER, AND WHY IT GENERALISES.** Her fix raises
ValueError for a label that is not a legal STATA name, inside
knn_to_rows and dispatch - so every door, Python included, is refused
`r(1000000)` because of a Stata rule, and test_menu uses 1e6
deliberately as the whole-world radius. **A door's constraint must not
be enforced in the engine**; dispatch says so in its own comment about
missing codes. The same reasoning applies to her help additions: she
put `r()` and `overshoot()` into STATA_ONLY, which REPLACES the shared
text that makes all three doors explain a box the same way. A
door-specific fact is now APPENDED (STATA_EXTRA) instead.

**AND I REPEATED ONE OF HER CLAIMS WITHOUT CHECKING IT.** My review
told John that `r()` and `overshoot()` "had no help entry at all".
They had one, through OPTION_HELP into equipop/doors/help.py. I had
verified her three code findings by reproducing them and took the
documentation claim on trust because it was adjacent to three true
things. **Verify the boring claims too.**

**THE SUITE WAS PINNING THE BUG**, which is the other lesson here:
test_menu asserted the column `N_r1e+06` - a name no Stata variable
and no shapefile field may have - and computed the expected name with
the same `:g` the code used. A test that derives the expected name the
way the code does cannot catch a naming fault. Spell the name out.

**WHAT HER PR GIVES US THAT WE CANNOT GET HERE**: a committed log of
`PASSED: all 57 checks` on StataNow 19.5 MP. The first real-Stata
verification by anyone but John, and one of the four SSC checks.
`varabbrev` does not appear in it, so Baum's specific check is still
open.

**STILL TO DECIDE** (left alone deliberately): her `CHANGELOG.md`
would be a third place history lives, after MANUAL.md's table and this
backlog; and her branch releases its fixes as v1.49.2, which this line
already used for the table-to-feature-class work - the fixes were
folded into 1.51.0 instead, so no version is claimed twice.

---

## 0a. 1.50.0 - THREE BACKLOG ITEMS, AND WHAT CHOOSING THEM EXPOSED

**THE PRIORITY LIST WAS STALE FOR THE SECOND TIME.** It said "Now:
the Machine 5 browser arc" - 18 of those 21 items are struck, finished
across 1.44.2 to 1.46.2 - and it said the OSM lattice join and
doors/inventory.py had no doors, when both have had doors in both GUIs
since 1.47.6. Item 269's own entry says "DOORS DONE v1.47.6", THE SAME
RELEASE that wrote the claim. **Checking the code before recommending
is the whole lesson**; the list was assembled from item numbers.

**333 - A `no_door` ENTRY COULD NOT FAIL.** tests/reachability.py was
built in 1.47.6 to catch exactly this class of thing, and `test_1`
walks `entry[0] == "door"`: it verifies POSITIVE claims, so a door
that disappears is caught and a door that APPEARS is never noticed.
The matrix could only be wrong in one direction and it was the
expensive one - a false "no door" tells the next session to build
something that exists. Fixed by forcing the distinction: `ruled_out`
(a decision, no witness) or `not_yet(why, item, absent=(file,
symbol))` - a GAP that names what must stay absent and so announces
its own obsolescence. `no_door` is GONE as a name on purpose; leaving
a catch-all would have let the blind spot back in on the next entry.
**Restoring the exact 1.47.6 claim now fails the suite.** The audit of
all 26 entries also found three identical one-liners ("No door. No
demand recorded.", 28 characters, just past the 25-character minimum)
and a `same_as` that would have borrowed another door's witness.

**293 - AND THE DIAGNOSIS IN THE ITEM WAS WRONG IN A USEFUL WAY.**
"Analysis runs have no provenance record" was not quite true: **Pro
had one**, since 1.26. So the real state was TWO IMPLEMENTATIONS OF
ONE JOB with the dead one in the package and the live one in a door -
and the live one was HAND-MAINTAINED, which is why `overshoot` moved
every k-based number from 1.30 and appeared in no record until 1.47.
**So the fix is not "write a record".** It is that the record comes
from the engine's own arguments: `dispatch(..., provenance=runlog)`
fills it from `dict(locals())` at entry, the arguments AS BOUND,
defaults included. A parameter added to the engine appears in the
record the same day with no door touched, and a test walks dispatch's
own signature and fails if one is missing. QGIS gained a sidecar where
it wrote nothing; Pro's existing CSV gained the engine's rows under an
`engine.` prefix rather than a second file; Stata prints the note and
returns r(overshoot)/r(originrule)/r(provenance) as the EFFECTIVE
values.

**AND 333's WITNESS CAUGHT 293's OWN WORK AN HOUR LATER.** The three
`not_yet` entries for run provenance fired the moment the doors were
wired. That is the mechanism doing the job it was built for, inside
one session.

**237 - THE FIXTURE IS PUBLISHED NOW, SO IT WAS PROVED LOSSLESS FIRST.**
`ValFloat` was a Stata `double` under a name saying float. Every one of
its 9,166 present values is a whole number, the largest 23,254, and
float32 is exact to 16,777,216 - so the change moved NOT ONE PINNED
NUMBER and the showcase's `Nv 167.30 | Mean 1815.23 | Med 1248.10 |
Gini .5806` still stands. tools/make_test_data.py refuses to run if
either fact stops being true. All nine variables had EMPTY LABELS,
found while doing it; labelling them is a better cure for a misleading
name than renaming, which would break four files and every student's
notes. **The names and values are untouched and one question is
John's**: ValFloat demonstrates a CONTINUOUS measure and holds only
integers, so fractional values would teach it better - but they would
want `double` storage, which is the opposite of what he asked for, and
they would diverge from the SSC copy.

**THE SHAPE OF ALL THREE.** Each was a thing that described the
project to itself and had gone wrong: a priority list, a reachability
matrix, a provenance record, a dataset's own variable names. None of
them is code a user runs, and all four had drifted because **nothing
checks a description**. Every one now has a test that fails when the
description stops being true.

---

## 0. THE LAST FOUR RELEASES, AND WHAT THEY HAVE IN COMMON

1.49.0 to 1.49.3 came from John in ArcGIS Pro and Kit Baum on SSC.
**Not one came from the backlog**, and three of the four were cases
of EquiPop saying something false to a user who then believed it.

**1.49.2 - FIXING A VALIDATOR DOES NOT BUILD A FEATURE (329).** 1.49.1
stopped the dialog refusing a table input that wanted a new feature
class. John's next run met the same sentence from forty lines deeper,
and the cause was not a duplicated check: `_run_tool` read
`if kind == "table": ... elif out_mode.startswith("New")`, so for a
table input the second branch was unreachable. **The capability had
never existed, only the refusal** - and the 327 test could not have
caught it, because it called updateMessages and stopped there. A
validator test certifies the validator.

**1.49.3 - THREE VOICES CALLING A CORRECT INSTALL A FAULT (330).**
Kit followed the paper exactly and `equipop doctor` told him he had a
VERSION MISMATCH. He did not. Commands from SSC with a newer engine
from pip is what `equipop setup` ASKS FOR - it installs
`equipop>=<floor>` - so the package shipped an installer that creates
a state and a diagnostic that calls that state a fault. The same
equality test was in equipop_test_pass.do, where it failed a check on
a correct install, and in SSC_SUBMISSION.md, which told the submitter
to make "the doctor's mismatch message current". It was current. It
was wrong.

**AND THE ANSWER WAS ALREADY WRITTEN DOWN.** The comment beside the
pip call, put there for 196 in 1.48.2, says: *"doctor then reports a
mismatch that SETUP CREATED... the library must be at least as new as
the caller."* Correct, recorded, eleven releases old, and the
diagnostic three files away was never told. **Nothing connects a
comment to the code that should obey it** - prose is a door like any
other, and two doors disagreeing is this project's oldest shape.

**1.49.3 - THE FLOOR WAS A RELEASE NUMBER PRETENDING TO BE A
DEPENDENCY (331, 332).** John asked whether shipping ado 1.49.3 against
engine 1.49.1 would conflict. It does worse: setup asked pip for
`equipop>=<the ado's own version>`, so a release reaching SSC before
PyPI makes the install fail OUTRIGHT - at the first instruction in the
paper. And 1.49.2, which touched only the ArcGIS toolbox, had silently
raised the Stata engine requirement. `eqp_min_engine` is now a
hand-maintained constant holding *the oldest engine that satisfies the
calls the ado makes* (1.48.0, set by `Decay(calibration=)`), listed
with its reasons, never touched by bump_version.py, and the doctor
judges THAT rather than two release numbers.
**RELEASE ORDER IS NOW A WRITTEN PRECONDITION: PyPI before SSC.**
Anything fixed in `equipop/` - the doctor's whole report, for instance
- does not exist for the user until PyPI has it, so an ado-only update
looks like no fix at all.

**THE .ADO'S PYTHON BLOCK IS TESTABLE NOW, and this matters for every
future session.** Its own comment said *"Code in here can only be run
by Stata, so the Python test suite cannot reach it"* - which is why
every guard in `equipop setup` was verified by GREPPING THE FILE FOR
STRINGS. tests/test_stata_python_block.py stubs `sfi`, EXECUTES the
block, and feeds the real functions pip's real output. **That works
only because everything in the setup path is standard library, as its
own comment requires. An import of numpy, pandas or equipop on a setup
path puts the block back out of reach and takes its tests with it.**

**SMALLER, BOTH FOUND BY EDITING SOMETHING ELSE:** every escaped brace
in the Stata help had shipped malformed since the generator was
written - two chained `.replace()` calls, the second eating the
first's output - and five were in the file Kit read; and five
paragraphs were being brace-escaped when they wanted LIVE markup, so
`{help python}` had always rendered as the words rather than the link.
BACKLOG 320's byte-order-mark fix had also covered the two sidecar
CSVs and missed the RESULTS csv, the one a student opens in Excel.

**AND THE SIXTH UNFALSIFIABLE TEST OF THE WEEK WAS MINE.** The
output-side check for broken SMCL could not fail once the five
paragraphs moved off the escaper: nothing reached it with a brace any
more, so breaking the function again changed no shipped byte and the
test passed over the restored bug. Pinned by a unit test of its own.
**Break-checking is not optional in this project.** Six of these in
one week, every one caught by breaking the fix and none by the suite.

## AND THE ONE AFTER IT - TWO DOORS, ONE JOB, DIFFERENT RULES

**Three findings now share one shape, and no guard can see it.**

- **306**: John's ruling that a cell is charged once per CLASS went to
  machine 3's join in 1.47.4 and never to machine 1's barrier, which
  kept charging per FEATURE. On downtown LA that is cell costs of 1
  to 166 where the table tops out at 8.
- **320**: Pro had a locale-proof number reader from 1.16.7 - found on
  a Swedish machine - and QGIS never got one, because the code sat in
  the .pyt instead of in the package. A Norwegian student typing
  `500,5` met a raw Python error.
- **324**: 316 was written about Pro's overwrite-or-stop box. Nobody
  asked what QGIS does with a repeated name: it appended a DUPLICATE
  FIELD and left OGR to sort it out.

**THE REACHABILITY MATRIX CANNOT CATCH THIS.** It lists capabilities
against doors - whether a thing can be reached - and says nothing
about two code paths that do one job by different rules. Every one of
these was found by a person noticing, not by a test.

**So when a rule is ruled on, ask which OTHER path implements the same
idea.** Shared logic goes in `equipop/doors/`, never in a door.

## THE MOST IMPORTANT THING IN THIS FILE - 1.48.0, BACKLOG 317

**A half-life distance means two different things, and EquiPop had
quietly swapped one for the other.** Read this before touching decay.

- **Half-life**: half of all trips are shorter than the distance. What
  a survey median commute means. Östh, Lyhagen and Reggiani (2016,
  EJTIR 16(2)) advocate it and old EquiPop used it.
- **Half-probability**: a neighbour at that distance counts half as
  much. Versions 1.30-1.47 used this for EVERY model, unrecorded.

They coincide only for `negexp`. 1.48.0 makes half-life the default
again (John's ruling), offers the choice only for `expnormal`,
`expsqrt` and `lognormal`, and keeps `power` on half-probability
because its area never converges.

**The paper's log-normal was wrong.** It set erf = 0.5, which is the
three-quarter point once the log-space integral runs from minus
infinity; its two published roots put 75% and 25% of the area before
the median. The corrected half-life is solved exactly on `ln(d+1)`.
John accepted the correction. Whether it goes anywhere public is his.

**"Area" means the 1-D area on the x/y diagram**, as in the paper. On
a disc the coincidence moves to the Gaussian. Recorded, deliberately
not built.

**A test had encoded the departure**: it asserted weight(h) = 0.5 for
every model, defining half-life AS half-probability. It is now two
tests plus one that integrates the area. If you find yourself wanting
`weight(h) == 0.5` back for all models, that is the old mistake.

**318, found building it**: Pro dropped the decay MODEL whenever the
half-life came from a field, and ran `negexp`. Fixed; tested.

**THIS FILE IS LATE AND THAT IS THE FIRST LESSON.** BACKLOG 289 was
written in this session, recording John's ruling on the lost
handovers 9 and 10, and it says: *"From 14 onward the handover enters
the repository root in the same act as the release."* Four releases
then shipped without one — 1.47.0, .1, .2 and the rebuilds between —
until John asked why the delivery looked short. The rule was written,
the lesson was recorded, and the behaviour did not follow. Write this
file BEFORE building the artefacts, not after.

---

## 1. WHAT EXISTS NOW THAT DID NOT

**The origin rule (BACKLOG 290).** EquiPop has always counted a
location's own residents among its nearest neighbours; `autocorr.
build_weights()` has always excluded them. Two definitions of
"neighbourhood" in one package, both called that. There is now one
choice at every door: `include` (i=j, the default) or `exclude`
(i≠j, the w_ii = 0 convention spatial regression requires). New
module `equipop/selfrule.py`, wired through all three engines, both
QGIS algorithms, both Pro tools and Stata's `originrule()`.

**Complete ArcGIS Pro help.** Machines 3 and 4 had no sidecar file at
all, so their '?' pages read "There is no description for this item"
in every release. Thirteen missing parameter entries were the whole
cause. All four tools now generate; **five files travel to Pro, not
three**.

**Eight download defects fixed (BACKLOG 291)**, each confirmed in
this tree before being changed, each with a test that fails when the
old behaviour is restored.

**The backlog's head is current.** It had stopped at item 164, so
items 165–299 — three machines, the registry, every provider, the OSM
work — had never entered the ordered list. Rewritten, with a rule
written into it: struck items leave the list.

**Machine 6, *What is in this folder?*,** in QGIS and Pro. The engine
shipped in 1.45.0, marked DONE, reachable from nowhere for two
releases. One row per file, class vocabularies, and which rasters
share a lattice.

**Roads and land use join the lattice (298).** Machine 3's join took
the CENTROID of every feature. Three fidelities now, default *each
class once* - John's model, and the refinement that makes it work on
OSM, where one street is many records.

**tests/reachability.py** - one row per capability, one column per
door, every gap carrying a reason. See §3.

---

## 2. THE VALIDATION THIS RELEASE RESTS ON

John ran `CaliData2010` — his own five-county Los Angeles blocks, the
data behind Östh, Clark and Malmberg (2015) — in Stata, weighted by
the group, over 78,208 populated blocks:

    2014 software   mean 0.2752264  sd 0.2464846  min 0.0004955
    EquiPop 1.47    mean 0.2752264  sd 0.2464846  min 0.0004955
    same, i≠j       mean 0.2378486  sd 0.2482518  min 0.0000000

**Identical to seven decimals on four statistics.** Almost nothing
else in this project is checked against anything but itself.

**THE MINIMUM IS WHAT PROVES IT IS A COMPUTATION AND NOT A COPY**, and
that mattered: an exact seven-digit match is also what a copied column
looks like, and 1.46.3 and 1.46.4 were both naming-and-writing faults
in this same path. Under i=j a block holding any African American
residents *cannot* score zero, because its own people are inside its
own neighbourhood. Under i≠j it can hold them and have none among its
neighbours. No copy produces that.

Also confirmed on the same data: under the default `proportional`
mode, N at k=100 is exactly 100 for every block (to 1.4×10⁻¹⁴), which
matches the 2014 convention. Under `whole` it ranges to 7,636. Worth
stating in any write-up.

---

## 3. THE PATTERN THIS SESSION IS ABOUT

**SIX things were built, tested, and unreachable** - five found by
accident, one by the tool written to find them.

1. `doors/inventory.py` (269, shipped 1.45.0) — no GUI, no runner.
2. `vectorjoin.py` (280/282) — reachable only from a script that the
   source archive did not carry.
3. `RunLog` in `meta.py` — **backlog item 2**, complete, exported in
   `__all__`, called by nothing and tested by nothing. Still open as
   293.
4. The Pro help sidecars — generated, checked by a test, and never
   shipped to anyone.
5. `make_help_xml.py` — one of the five Pro files since 1.44.4, and
   until 1.47.11 it could not run from the folder it ships to.

Number 5 is the one to remember. It was offered to John as the
ten-second escape hatch from an untested change, he tried it, and it
failed on the first line. **The recovery path for a known risk was
itself unreachable, which is what made the risk feel acceptable.**

6. The Stata command's friction and slope options - the BRIDGE
   supports `engine="friction"` and `engine="slope"`; `equipop.ado`
   mentions neither. Found by tests/reachability.py within a minute
   of its first run, IN CLAUDE'S OWN DECLARATION of the matrix, which
   claimed a Stata door from memory. Ruled out by John (296): those
   are GIS questions.

Every one of these passed its tests. The tests asked whether the
thing worked, never whether anyone could get to it.

**THE ANSWER IS tests/reachability.py**, and the check that matters
is not the matrix but the LAST of its five guards: every module in
the package must appear, either as a capability with its doors or in
INTERNAL as machinery. A new module now forces the question. That
single test would have caught all five of the accidental finds.

It is DECLARED, not derived, and the first attempt proved why: a grep
of each door for the engine function it calls was wrong in BOTH
directions - machine 1 read as absent from QGIS and Pro (they reach
it through stata_bridge.dispatch), and the lattice join read as
present (alg_continental imports join_to_points for something else).
A matrix that guesses is worse than none; that one said the doors
were fine.

---

## 4. TESTS THAT COULD NOT FAIL

The house practice from `test_selfpot.py` — break the thing on
purpose, watch the test fail — caught **two of this session's own
tests** that were green and worthless.

The crossing-ring test was wrong twice, for different reasons:

- First, the origin was never *in* the crossing ring. Rings are
  equal-distance groups, the origin sits at distance 0, and with its
  mass removed the crossing moves outward. It can only be in that ring
  when another cell **shares its coordinates**.
- Then, with the fixture fixed, asserting on the **share** still could
  not catch an unmasked ring total: the ring fraction scales numerator
  and denominator alike, and `proportional` pins N to k by
  construction. Only T moves — 15 to 5 — while N_30 stays exactly 30
  and R stays exactly 0.5.

A share and a count that both look right while the total is a third of
what it should be. Run the breakage check on every new guard; it is
not a formality.

**SIX MORE IN THE FOUR RELEASES AFTER THAT, and the count is the
point - this is the project's most frequent single defect.** Every one
was caught by breaking the fix; none by the suite.

| release | the test | why it could not fail |
|---|---|---|
| 1.48.2 | ensurepip advice | asserted the WORD appeared in the file; disabling the branch that prints it still passed |
| 1.49.0 | two 306 tests | grepped for strings that survived the break |
| 1.49.1 | the 327 dialog test | read `pm["outtable"].message`; the simulator stores `(kind, text)` in `.messages` and has no `.message`, so the assertion read an always-empty attribute |
| 1.49.2 | the 327 test again, differently | it called `updateMessages` and stopped, so it certified the VALIDATOR and could not see that the execution path had no such capability at all |
| 1.49.3 | my own SMCL output check | once the five markup paragraphs moved off the escaper, nothing reached it with a brace, so breaking the escaper changed no shipped byte |
| 1.49.3 | the reachability matrix itself (333) | a `no_door` entry names no file and no symbol, so nothing verifies it |

**THE SHAPES TO WATCH FOR**, since they recur:
1. **Asserting a string exists in a file.** Passes while the code that
   uses it is dead. Call the code instead - which is why the .ado's
   python block is now executed by tests rather than grepped.
2. **Reading an attribute the stub does not have.** Always empty, so
   `assert X in thing.attr` is `assert X in ""` and fails loudly on a
   WORKING fix - or, worse, `not in` passes forever.
3. **Testing the layer the fix touched** instead of the behaviour the
   user asked for. The validator test is the pure case.
4. **An assertion with no counter-example left in the system.** Mine:
   nothing could reach the escaper any more, so no change to it could
   be observed. If you cannot describe the input that would make the
   test fail, it is not a test.

---

## 4b. TWO STREAMS BESIDE THE CODE, FROM SESSION 12

**TEACHING.md** and **PROPOSALS.md**, at the repository root, each
carrying a version line a test checks against pyproject.toml.

WHY THEY EXIST AT ALL, rather than living in conversation: this
project loses things between sessions. The priority list stopped at
item 164 for eleven releases; item 257 asked for samples already
supplied; five capabilities shipped that nobody could reach. A stream
that is not written down is a stream that will be rediscovered.

**Teaching is not a by-product - it is the best acceptance test here.**
Session 12 proved it twice in one afternoon: John's CaliData2010 run
validated the origin rule against a PUBLISHED PAPER, and his Swedish
OSM folder found two defects no fixture would have shown. Both came
from USING the software the way a stranger will.

**The proposal is a question put to the code.** HORIZON-HLTH-2027-01-
ENVHLTH-02, John coordinating. The dates moved - opens 29 Oct 2026,
closes 17 Feb 2027, four months earlier than he remembered - so check
the portal, not any file. EquiPop is a WORK PACKAGE there, not the
proposal.

EVERY HANDOVER FROM 16 ONWARD should carry two lines on where each
stands. Both files say what only John can decide; neither is started.

## 5. WHAT IS OPEN

**299 — Pro's join box still takes the centroid only.** 298 gave
QGIS three fidelities and left Pro with one, so the two GIS doors now
disagree about what a box DOES. door_parity does not catch it: both
doors have a box called `joinlayer`; only its behaviour differs. The
engine is shared and geopandas-free, so this is dialog work. Recorded
the moment it was created rather than found later.

**FIVE SIMULATOR GAPS IN ONE RELEASE**, all real API the stub had
never needed: QMetaType.Type.LongLong, the DETable datatype,
QgsWkbTypes.NoGeometry, a line/polygon source, and - the worst pair -
QgsCoordinateReferenceSystem without __eq__ and QgsGeometry without a
copy constructor. Those two COMPOUNDED: identical EPSG:4326 objects
compared unequal, so every join built a transform it did not need,
and that needless reprojection turned every line into an empty
geometry. The door then reported "no usable line or polygon geometry"
about a layer full of them. A confident, wrong error message,
produced entirely by the thing meant to catch wrong behaviour. When a
door looks broken in a way that makes no sense, SUSPECT THE
SIMULATOR.

**THE BACKLOG HEAD WENT STALE A SECOND TIME, and part of it was
false on the day it was written.** Corrected in 1.49.3. It said "Now:
the Machine 5 browser arc" - 18 of those 21 items are struck, finished
across 1.44.2 to 1.46.2, and what remains is not browser work. It also
said the OSM lattice join and doors/inventory.py had no doors; **both
have had doors in both GUIs since 1.47.6**, and item 269's own entry
says "DOORS DONE v1.47.6" - the same release that wrote the claim. The
rewrite that existed to stop a stale index carried a stale claim into
its own first paragraph, because it was assembled from item numbers
rather than checked against the code.

**AND tests/reachability.py STILL DECLARES BOTH AS `no_door` (333).**
This is the important one. `test_1` walks `entry[0] == "door"` and
verifies the named symbol is still in the named file, so a door that
DISAPPEARS is caught. A `no_door` names no file and no symbol, so
**nothing about it is verified and a door that APPEARS is never
noticed.** The matrix can only be wrong in one direction, and it is the
direction that costs a release: a false "no door" tells a future
session to build something that exists. I nearly recommended exactly
that as the next piece of work. The guard built to catch unreachable
capabilities has an assertion of the same shape as the six tests that
could not fail. Proposed fix in 333: separate a RULING (needs no
witness) from a GAP (carries the file and symbol that must stay
absent, so it can announce its own obsolescence), then audit every
existing entry - this one was found by accident, so the rest are
unaudited by definition.

**Next, after 333:** 293 (RunLog / no provenance for analysis runs -
oldest open item, and it is BACKLOG item 2), then 118's upstream half
(the statistics path still expands rows into persons), 119 (resume
compares parameters but not content).

**237 IS NOW PUBLISHED.** `equipop_test_data.dta` - renamed from
stata_test_data.dta by Kit Baum, because SSC's filename space is flat -
has a `ValFloat` that is not stored as float, and it now ships to every
SSC user who types `ssc install equipop, all`, alongside the paper.
Still not a correctness fault; the arithmetic reads values, not storage
types. But it teaches the wrong thing in the file a reader inspects
first, and touching it invalidates the pinned EXPECT numbers in
equipop_test_pass.do, so it needs a dataset regeneration pass and a
re-pin in the same release.

**THE SSC RELEASE LEFT FOUR CHECKS THAT NEED A REAL STATA** and are
John's, not ours: `set varabbrev off` through equipop_test_pass.do, the
reserved-word check, a clean-machine install, and whether the help file
renders. None can be done here. SSC_SUBMISSION.md holds the list.

**BACKLOG 34, still open and now precisely characterised** for the
first time in thirty releases. Its headline is WRONG: summary and
usage render fine. What is empty is the per-parameter **Explanation
column** of the '?' page, for machines 1 and 2, even where the text is
present in the XML and renders perfectly in the dialog flyout. Two
changes in 1.47.0 may bear on it — `SyncOnce=FALSE` and escaped `<p>`
paragraphs — and **neither is validated**. `make_help_xml.py --plain`
undoes the second in ten seconds. The question that closes this item:
does the Explanation column on tool 1 or 2 now carry text?

**Waiting on John, not on code:** 224 and 232 need the exact inputs
and output table from a run where the symptom appears; 210 needs a
ruling on zip vs loose; 216 is a methodological exercise; 257 is
paused by him.

**Ruled out, recorded so they are not raised again:** 203 — a radius
run reports no distance, and that is the design.

---

## 6. THINGS A FRESH SESSION WILL GET WRONG

**Reading a stale note as current.** Item 257's "STILL NEEDED" list
caused a round trip asking John for three samples he had already
supplied. Item 43's open copy caused a wrong question about the
CITATION.cff, which is a mechanical test-pinned bump and not an
author's decision. Item 45 described a symptom that had gone and
missed one that was there. **When an item is the basis for a
question, check it against the code first.**

**Mis-attributing a finding to the item that has been waiting for it.**
John sent a screenshot of an empty Pro flyout; it was recorded as
BACKLOG 34's long-awaited field cycle. It was not — 34 says in its own
second sentence that the per-parameter comments *do* work. It was a
stale sidecar. **A finding that arrives looking exactly like the one an
item has waited years for deserves more suspicion, not less.**

**Trusting a bench measurement over a field one.** Claude's own run
gave 0.2765 and −13.4%, measured with the neighbour search capped at
48 cells. The same measurement reported a median per-block difference
of 0.00000 alongside an index off by 0.0013 — the signature of a cap,
not of a real difference — and it was read as a real difference
anyway. **Field numbers replace bench numbers, and a bench number
should carry its cap.**

**Concluding about all history from the present state.** "The sidecars
were never shipped" was said on the strength of the current MANIFEST,
sdist and delivery. John had them.

**Inventing a rule from an incomplete list.** The first format check
carried magic bytes per extension and refused anything absent from it
— which broke twenty tests and would have refused `.csv`, `.json`,
`.pbf`, `.shp`. Narrowed to the one failure actually observed. This is
how the four-years-stale WorldPop docs and GHSL's prose-only CRS
constraint both hurt this project.

**Building the provenance system inside another item.** There is
nowhere to record `overshoot` or `originrule` because `RunLog` is
dead. That is 293, with its own release. Adding it to the origin-rule
work would have been exactly the scope creep that produced
engines-without-doors.

**Forgetting that John is not a Python programmer.** He runs QGIS,
ArcGIS Pro and Stata, and reads research. "Run this from the
repository root" was written to someone with no repository; a shell
command was pasted into Pro's Python window, reasonably. Say **where**
a command is typed, not only what it is.

**Handing him a release without checking that it can be installed.**
1.49.3: the whole 330 fix was built, the version bumped and the letter
to Kit written before anyone asked what was actually on PyPI. It was
1.49.1, so `equipop setup` would have failed outright for every new
reader of the paper. **He caught it, in one sentence, after I had
declared the work finished.** The check is one command - `pip index
versions equipop` - and `pip install --dry-run "equipop>=X"` proves it
either way in two seconds. Assume nothing about what is published.

**Fixing the thing you can see instead of the thing that was asked
for.** 329 twice over: the dialog check was fixed, the error recurred
from the execution path, and my first reading of that was "there is a
second copy of the check" - there was no second copy, there was no
capability at all. **When a fix does not take, ask what the user was
trying to DO, not where else the message lives.**

**Assuming a comment is obeyed by the code near it.** 196's comment
stated the correct version invariant in 1.48.2 and three files were
built against the wrong one anyway. Prose in this repository is
documentation, not enforcement. If a rule matters, it needs a test -
and if a rule is already written down somewhere and violated, that is
worth saying out loud rather than quietly correcting, because it means
the rule had no owner.

**Trusting a subagent's finding without checking it.** A delegated
search reported the lattice-join reachability claim as stale, which was
correct and useful - and it was verified against the source before it
reached John, because a finding put to him carries this session's
authority, not the subagent's. Do the same every time.
