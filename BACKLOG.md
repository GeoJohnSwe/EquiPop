# EquiPop — Backlog

**Order (John's instruction, 1.19; done at last in 1.29.0):**
still-to-do at the TOP in priority order, done items at the
BOTTOM. The top of this file should answer "what next?" without
reading the rest of it. Claude proposes the order with a short
reason each; John overrules freely and often should.

Workflow unchanged: suggestions are appended without altering
code. When we decide to batch, items are implemented, validated,
moved to the manual's version history, and struck here.

*1.29.0 also merged five duplicate rows. "Machine 2 vocabulary"
had been re-added four times as 56, 60, 64 and 69 (and once more
as 75), each time as if new, because it always lost to whatever
arrived that week - which is exactly what an unordered file
costs. 71 and 74 were the same duplication. Items 38/42/43/45/49
appeared twice; the weaker copy is gone.*

## What next — in priority order

*Rewritten 1.52.0, and the rewrite is itself the point. **The rule for
this list is that an entry which is struck LEAVES it** - written at the
top since 1.29.0, and broken every single time, because striking an
item and updating the index are two actions and only the first feels
like finishing. By 1.51.2 the list carried six struck entries, two
items numbered 3 and two numbered 4, and a reader had to scroll past
four releases of completed work to reach a plan. The corrections those
entries carried are worth keeping and are now in the detail below,
where done work lives; what is left here is a plan.*

*This index has gone stale FOUR times - at 1.47.6 (it stopped at item
164 for eleven releases), at 1.49.3 (the Machine 5 arc, with a claim
that was false the day it was written), at 1.51.1 (four items done and
still being asked for, which the external review pointed at), and at
1.52.0 (this). It is the one document nothing in the suite checks.
**If you are reading this at the start of a session, check two or
three of its claims against the code before trusting any of them** -
that is how the last three staleness findings were made.*

### Now — a release gate on real hosts
1. **128, 80, 87, 198–199, 288** — small recorded end-to-end runs in
   live QGIS and ArcGIS Pro, matching plugin/engine version checks,
   cancellation, and a copyable diagnostic. **The oldest unaddressed
   item on this list, and the only one of the original seven left.**
   It needs John's machines: Claude can build the harness and the
   diagnostic, and cannot run the hosts. Worth saying plainly, because
   part of why it has stayed at the top is that the half that closes
   it is not Claude's to do.

### Next — the exposome arc, now that machine 4 tiles
**365 AND 363 ARE BOTH CLOSED** in 1.53.4, which is the item this
list had at the head of the exposome arc for four releases. A
continental demographic index now has a supported route: the tiles
already carried T_num/T_den per origin, so it is a per-tile post-pass
with memory bounded at one tile. **That changes what PROPOSALS.md may
claim** - Europe-wide dependency ratios are no longer the piece the
software cannot do at scale, and the standing warning not to promise
them is retired. What is still true: the tiled index is float32,
because machine 3 stores tiles that way and says so in its manifest.

2. **349** — the continental door exposes none of the five engine
   options the tiled wrapper takes (345), nor `decay` on either
   branch, and it is now the LAST thing between a continental run and
   the full engine. A uniform gap, so nothing is inconsistent - but
   `originrule(exclude)`, the w(ii)=0 convention spatial regression
   requires, is unreachable from a continental run, and the 13.6%
   figure session 12 measured is a published number a continental user
   cannot reproduce. Cheaper than it looks: `run_index` forwards
   `**kw`, so machine 4 comes free once `run_folder`'s signature
   grows, and machine 3 has no Stata door, so it is two dialogs.
3. **hex cells at the GIS doors** — 158 removed the correctness
   blocker in 1.52.0, so this is now a dialog decision rather than a
   defect. `tests/reachability.py` holds it as a GAP with a witness in
   each door's file, so the entry fails the day a box is added.
4. **102 + 42** — QGIS variable bandwidth and its explanation.
5. **117 + 120** — shared validation and construction, as those paths
   are touched. 120 is confined to machine 1; machines 3, 4 and 5 have
   none of it, so it gates changes to counts and nothing else.
6. **134, 132** — a golden dataset per host; a public ArcGIS Online
   item.

### Housekeeping, worth pairing with a release rather than owning one
7. **101** — the suite writes run manifests into the working
   directory, and seven such files have been committed to the public
   repository for over a year. The test-side fix is Claude's; the
   `git rm -r --cached` is John's. **350** found the same shape in the
   release zip and fixed the tool; `.gitignore` now covers `build/`,
   but whether those files are tracked still needs one look.
10. **299** — Pro's join box still takes the centroid only, where QGIS
   offers three fidelities. Two doors disagreeing about what one box
   DOES, which door_parity cannot see because both have the box.

### Waiting on John, not on code
- **224, 232** — need the exact inputs, versions, choices and output
  table from a run where the symptom appears. No speculative
  arithmetic. (291's addFeature fix removes ONE possible mechanism;
  it does not diagnose either.)
- **210** — zip rasters measured 3.5x slower and the penalty does not
  amortise. Needs a ruling on which wins when a folder holds both.
- **216** — vital-event rasters, and the circularity caveat already
  recorded there. A methodological exercise, not a menu entry.
- **257** — PAUSED by John, session 12. Four providers work; a fifth
  is capability, not a gap.
- **321** — expected counts under a supplied rate schedule.
- **Marina's `CHANGELOG.md`**, whether to adopt it; and the
  `set varabbrev off` run, which is the one outstanding SSC check.

### Ruled out, recorded so they are not raised again
- **203** — a radius run reports no distance. That is the design.
- **100** — see 203.
- **205** — a Stata door for machine 2. Stata does weighted statistics
  natively and better; what it cannot do is build the neighbourhood.

## Still to do — detail, in the order above

- ~~95~~ | DONE v1.29.5 | SELF-POTENTIAL, shipped. equipop/selfpot.py holds the rule once so the two engines cannot drift; both apply it; both doors offer `selfpot` and BOTH ARE CHECKED ON VALUES, not names. Default 1.0, John's ruling. Guards broken on purpose six ways before being trusted - including the Pro one, whose FIRST version passed against a deliberate break because it drove _run_tool and skipped the dialog hop where `or 1.0` eats a falsy 0. Rewritten through execute(). s=0 reproduces pre-1.29.5 numbers exactly, asserted not assumed.

- ~~96~~ | DONE v1.29.5 | Fixed by 95 and made loud. The substitution now prints a WARNING with the count and percentage, and the reported bandwidth range is the range BEFORE substitution - it used to be after, which hid it completely. Field check: 6,000 rows with a dense block, s=0 -> 'WARNING: 3,000 of 6,000 rows (50.0%) ... given the MEDIAN bandwidth (632 m)'; s=1 -> no warning, and the dense block becomes its own bin at a 10 m half-life instead of hiding in a 632 m bin.

- 349 | open v1.51.1 | THE CONTINENTAL DOOR DOES NOT OFFER THE FIVE
  ENGINE OPTIONS THE TILED WRAPPER NOW TAKES.
  345 threaded self_potential, overshoot_mode, self_rule, seed and
  decay_eps through run_knn_counts_tiled, because fingerprinting an
  option that cannot be varied would have been theatre. `run_folder`
  still accepts none of them, ON EITHER BRANCH - so nothing is
  inconsistent between tiled and untiled, which is why this is not a
  correctness fix and did not go into 1.51.1.
  WHAT IT COSTS TO CLOSE: four door dialogs, shared help text through
  doors/help.py (not a second copy - see 105 and 338), door-parity
  entries, and the box-changes-the-answer tests that 99 and 341
  established as the standard for a new option. The untiled branch
  also forwards no `decay`, so a continental run cannot ask for
  distance decay at all; that belongs in the same piece of work.
  WHY IT MATTERS: `originrule(exclude)` is the w_ii = 0 convention
  spatial regression requires, and a continental run is exactly the
  scale at which somebody wants it. Session 12 measured what the rule
  does on coarse units - 13.6% on African American isolation at
  k=100 - so this is not a preference, it is a published number that
  a continental user cannot currently reproduce.

- 101 | open v1.29.5 | THE TEST SUITE WRITES FILES INTO THE WORKING
  DIRECTORY. Found by Claude while staging 1.29.5: a clean clone had
  five stray CSVs after a run, named things like
  "C:\Data\Kayseri_EquiPop_run.csv" - one filename, backslashes and
  all. They are RUN MANIFESTS. test_arcgis_stub.py reproduces John's
  Kayseri field failure with a literal catalog path r"C:\Data\
  Kayseri.shp", the manifest writer puts a sidecar beside the output
  it derives, and on Linux the whole Windows path collapses into one
  odd name in the CWD. Harmless there. ON WINDOWS IT WOULD WRITE
  INTO A REAL C:\Data\ FOLDER - John's own machine, outside any
  tmp_path, every time he runs the suite. Not a shipped-code fault
  and deliberately not fixed in 1.29.5 (a three-item release stays a
  three-item release), but tests should write to tmp_path only.
  WORSE THAN FIRST LOGGED: seven of these files are COMMITTED to
  main - C__/Data/ (5 files, committed in 1.29.3),
  Instance=C_/Data/ (1 file, 1.22 - that name is a database
  CONNECTION STRING, so a test pointed at a GeoPackage made a
  directory out of it) and segregation_profile_HighEdu.csv
  (1.5.1). They have been in the public repository for a year.
  Removing them is `git rm -r --cached` on those paths, John's
  to run. Confirmed still reproducing: a freshly unpacked 1.29.5
  zip grew the same five files again after one test run.

- ~~104~~ | DONE v1.29.5 | All three parts shipped, ruled by John. Rungs name their boxes; box 2 reordered so the rung-1 box is FIRST (parameter names untouched, so saved models survive); and the notices exist in BOTH machines - machine 2 had the same silence, reading `refmode == 2 and catfield` and doing nothing at all when the field was missing. Wording shared in equipop/doors/rungs.py. Guarded by a test that reads the box letter out of the rung's OWN text and checks it points at the box that rung really reads - so the promise cannot lapse when someone reorders labels. Five deliberate breakages, all caught.

- ~~103~~ | DONE v1.29.5 | QGIS machine 2 now offers all eleven, in Pro's order and wording, with variance mapped to the engine's `var` in exactly one place. Guarded by a test that compares the two doors' MENU CONTENTS - a first instalment of 105 - and by one that checks every offered measure is one the engine can actually compute.

- 102 | open v1.29.5 | QGIS HAS NO BANDWIDTH BOXES AT ALL. Pro
  offers hlfield, hlfromdist and hlbins; QGIS offers only a fixed
  half-life in metres. So the SELF-CALIBRATING BANDWIDTH - the
  headline feature of 1.17 - has never been reachable from the door
  John teaches with, and BACKLOG 96 could only ever be seen through
  Pro or Python. Noticed by John, 1.29.5, reading the test manual.
  The three boxes are ANALYTICAL, not output plumbing, so by
  door_parity.py's own stated rule they belong in CORE - and they
  are not there, which is why nothing has ever objected. Travels
  with 42, which says the manual has never described the feature
  either.

- ~~105~~ | DONE v1.29.5 | Pinned rather than shared, and the reason is worth keeping. The obvious fix - import the wording from equipop/doors/rungs.py - WAS TRIED AND REVERTED: it broke BACKLOG 78, because QGIS imports a plugin at STARTUP and a module-level `import equipop` kills the whole plugin when the package is missing or old, before there is any algorithm to attach an explanatory message to. Pro learned the same in 1.16. So NEITHER DOOR MAY REACH INTO THE PACKAGE to find out what its own dropdowns say, and the duplication is permanent. rungs.py now holds the canonical wording and test_rungs.py reads all three copies and fails on drift - proved by drifting each in turn. Two real divergences were found and closed on the way: Pro said "additive (sum)" where QGIS said "additive (costs add up)" (QGIS's wording won - these are EFFORT costs), and the measures menus differed, which was 103.

- 106 | open v1.29.5 | NO DECAY IN MACHINE 2, and it is ENGINE work,
  not a door gap: run_knn_stats takes no decay at all while
  run_knn_counts does. Raised by John, 1.29.5, asking whether it
  would be easy. It is not. A decayed count is a weighted sum, but
  a decayed MEDIAN, PERCENTILE or GINI needs weighted versions of
  those statistics - different mathematics, not plumbing - and the
  weighted sd and se need an honest denominator, which is the
  EFFECTIVE SAMPLE SIZE of 97. So 106 and 97 are one job.

- ~~107~~ | DONE v1.40.5 | MANIFEST.in now lists the demo scripts, and
  the FIELD PASS with them. Found by the archive check rather than by
  looking: the unpacked 1.40.5 .tar.gz failed 11 tests because
  tests/test_field_pass.py reads equipop_test_pass.do and the archive
  did not carry it. The instrument the whole release is about had
  never travelled in a source archive. The test is now also the guard
  - an archive missing the do-file cannot pass its own suite.
- 107 | open v1.29.5 | MANIFEST.in OMITS THE DEMO SCRIPTS.
  demo_berlin.py, demo_malta_worldpop.py and demo_stats_sweden.py
  sit at the repository root; MANIFEST.in grafts examples/ and
  docs/ but never mentions them, so they have been missing from
  every published sdist. Found by Claude while building the 1.29.5
  full zip. Same shape as the two omissions already recorded in
  that file's own comments.

- ~~108~~ | DONE v1.29.5 | Both keepoutside routes now use count * mask. Reproduced before and after: two included rows carrying 10 and 1 people gave N_5 = [11, 11] and [2, 2]; both routes now give [11, 11]. The guard did NOT exist - breaking the fix on purpose changed nothing - so two were written: one pinning the numbers, one asserting the invariant that what happens to rows OUTSIDE the reference population cannot change the numbers for rows inside it.

- ~~109~~ | DONE v1.29.5 | `val > 0` became `val != 0`, and the unreachable check became _check_cost_range(), the same function vectors use. Facilitators survive; -1 and below is still refused. Guarded both ways, with no rasterio needed - raster_to_friction takes an array.

- ~~110~~ | DONE v1.29.5 | Threaded into _count_from_grid, which friction AND slope share, so both engines answered at once; then through run_knn_friction, run_knn_slope and both bridge branches. Note what 115 did to this: once Dist_k is the ring's MAXIMUM extent, an effort origin only reports zero when everyone counted stands on the same spot - which is what register data looks like, so the fixture uses duplicate coordinates.

- ~~111~~ | DONE v1.29.5 | The counter moved from _walk() to _store(), the single acceptance point, with a scratch dict merged only when a record is accepted. 514 origins now report as 514. Like 108, no guard existed; one was written that forces a fallback and parses the printed number.

- ~~112~~ | DONE v1.29.5 | One construction. Guarded by counting the grid's own announcement, which is the cheapest honest check.

- ~~113~~ | DONE v1.29.5 | selfpot() added to both commands with range validation, passed through to knn_to_rows and dispatch. The decimal-radius bug fixed in the same edit: `rl` was computed and then ignored, so `replace` silently dropped nothing for r=1.5. Live Stata is outside pytest, so the guards read the .ado text: the option exists, it is passed on, and it reaches the engine.

- ~~114~~ | DONE v1.29.5 | Two guards. One walks the ENGINE LIST and fails when any engine cannot be told about self-potential - a new engine arriving without an answer fails here. The other runs the effort engine and checks the number moves, because a signature test cannot see accepting-and-ignoring.

- ~~115~~ | DONE v1.29.5 | Dist_k is the MAXIMUM straight-line extent of the accepted effort ring, John's ruling. Guarded by shuffling the input rows and requiring the same answer.

- ~~116~~ | DONE v1.29.5 | The narrow sweep. `parameterAsDouble(...) or 100.0` in BOTH QGIS machines meant a cell size of ZERO was silently replaced by 100 m and the run went ahead at a scale nobody chose; Pro had the same on unit and hlbins. All refuse now, in the doors and again in _run_tool. Guarded twice: once on behaviour, once by banning the idiom textually on the parameters where zero is meaningful or nonsense.

- 117 | open v1.29.5 | A SHARED VALIDATED RUN SPECIFICATION. Counts
  may be negative, which breaks the monotonic cumulative sum the
  counts engine searchsorts against. Group counts above population
  only warn. k, radii, cell size and decay truncation have no
  consistent positive/finite check. Decay accepts a negative
  half-life or zero gamma until the arithmetic fails or weights grow
  with distance. Segregation does not refuse global shares of
  exactly 0 or 1. One validated spec, used by the package and every
  door, refusing rather than substituting.

- 118 | open v1.29.5 | WEIGHTED VALUE STATISTICS EXPAND ROWS INTO
  PERSONS. stata_bridge.py rounds each weight and repeats the row
  that many times before computing statistics. A row standing for a
  million people becomes a million rows. BLOCKER FOR 38, not merely
  a risk: WorldPop counts are FRACTIONAL, so rounding is a second
  silent error (a cell holding 0.4 people becomes 0), and a 1 km
  African run would try to materialise on the order of a billion
  rows before the engine starts. Needs exact weighted median,
  percentile, Gini, mean, variance and valid-count on values plus
  weights.

- 119 | open v1.29.5 | RESUME CAN MIX RESULTS FROM DIFFERENT RUNS.
  bigrun.py loads any manifest.json and skips every named tile that
  already exists, without comparing the current k, radii, decay,
  cell size, tile size, dtype or INPUT against the manifest it
  already wrote. Reusing an output directory after changing anything
  mixes stale and new tiles while appearing to resume. Cheaper than
  it looks: the manifest already records the parameters; it needs a
  comparison, a refusal, and an input fingerprint. Same item: the
  "exactly the untiled result" claim should say that results are
  STORED as float32 - the computation is exact, the storage is not.

- 120 | open v1.29.5 | POPULATION AND TREATMENT CONSTRUCTION IS
  DUPLICATED IN BOTH GIS DOORS, against the project's own rule that
  doors move data and the package calculates. 108 exists precisely
  because of it: one door was fixed and the other was not. Compare
  alg_counts.py with the equivalent block in EquiPop.pyt.
  RAISED IN PRIORITY by the distribution review (133): four doors
  are planned, possibly five with R. Every one of them is another
  copy of this logic and another place for the next 108 to hide, so
  this is now a PREREQUISITE for any new door, not a tidy-up.

- ~~121~~ | DONE v1.29.5 | README_QGIS.md's "What is not here yet" had been telling users that decay, barriers, terrain and grouping were absent from QGIS; three of the four arrived releases ago, so it was sending people to ArcGIS for things sitting in front of them. Rewritten to say what IS present and to name the one real gap (102, variable bandwidth). MANUAL.md no longer calls itself 0.3.1 while carrying history to 1.29.5; MANUAL_BEGINNER.md and FUNCTION_MATRIX.md are now version-free by intention rather than stale; and equipop/__init__.py no longer says "no friction, no decay yet".

- 122 | ~~RULED OUT~~ v1.29.5 | A DISCLOSURE-CONTROL PROFILE for
  register data (minimum k, suppression of N_local and thin
  results). Raised by the external review; RULED OUT by John,
  1.29.5: "access to restricted or sensitive data means having
  agreed to ethical protocols already - so no need for extra
  caution". Recorded rather than deleted, because it is a good
  question that will be asked again.

- 123 | open v1.29.5 | RUN METADATA RECORDS ABSOLUTE PATHS AND
  MACHINE DETAILS. RunLog and the ArcGIS manifests store input
  paths, barrier catalog paths and OS information, so sharing a
  manifest may disclose usernames, institutional folder structure,
  project names and dataset locations. Distinct from 122: this is
  about what leaves the machine in a file meant to aid
  reproducibility.

- 124 | open v1.29.5 | fetch() CACHES BY FILENAME ONLY, not URL or
  checksum, so two different URLs sharing a basename silently reuse
  the wrong file - a real hazard for the continental data path,
  where WorldPop filenames repeat across countries and years. Same
  item: ZIP reading and fetching extract whole archives into
  persistent directories with no file-count or size limit.

- 125 | open v1.29.5 | QGIS RUNS CANNOT BE CANCELLED. There is no
  call to feedback.isCanceled() anywhere in the door, and progress
  only moves while the output is being written. A continental run in
  a dialog that cannot be stopped is not usable; this belongs before
  38's GUI work.

- 126 | open v1.29.5 | A TEXT CATEGORY IS LOST WHENEVER ANY VALUE IN
  THE COLUMN PARSES AS A NUMBER. _convert() in base.py keeps strings
  only if EVERY value fails numeric conversion, so a column holding
  "1" and "cafe" becomes numeric-plus-NaN and the category is gone.

- 127 | open v1.29.5 | QGIS VALUE STATISTICS does not call the
  package/plugin version-mismatch warning that Counts and Shares
  does, and shadows the variable `wanted` between the selected
  measures and the selected reference categories, so its "Measures:"
  log line can describe the wrong thing. The calculation is safe -
  the stats dict is built before the shadowing - but it is fragile.

- ~~151~~ | DONE v1.29.6 | PRO PASSED THE DECAY DROPDOWN'S LABEL TO
  THE ENGINE. John, Pro field test of 1.29.6:
      ValueError: Unknown decay model 'negexp (steady decline - the
      classic; each extra kilometre costs the same proportion)'.
      Available: ['negexp', 'expnormal', 'expsqrt', 'lognormal',
      'power'].
  decaynames.model_from_choice() exists for exactly this and QGIS has
  used it since 1.28. Pro filled its dropdown from the same shared
  choices() and then handed the whole label to Decay().
  WHY IT SURVIVED SO LONG: it fires only when someone PICKS a model.
  Leaving the box alone falls through to the "negexp" default, so
  every earlier decay run - including John's self-calibrating
  bandwidth tests two days ago - worked. NOT a 1.29.6 regression;
  it has been there since Pro gained the dropdown.
  Fixed via a shared _decay_model() helper with a BACKLOG 78 safe
  fallback, so a missing core still cannot kill the toolbox at
  import. Guarded two ways: every label the dropdown offers must map
  to a model the ENGINE has, and Pro must not read the box raw.
  The shape is 105 and 143 again: a shared module exists, one door
  uses it, the other does not, and nothing compares them.

- ~~152~~ | DONE v1.29.7 | The prefix is built from a normalised number and a trailing ".0" removed as a whole, never character by character. p1->P1, p10.0->P10, p50.0->P50, p100.0->P100, p97.5->P97_5. Guarded: the same percentile however written gets ONE name, and different percentiles never share one.

- ~~153~~ | DONE v1.29.8 | RULED by John: teach the original engine the same rule, "so that 'two engines, one mathematics' is true again. The people using older versions are like me, and would understand our reasoning." run_knn now takes self_potential with the same default and applies BOTH halves - the equal-area radius when the whole neighbourhood is the origin cell, and the mean intra-cell distance in the decay weighting. Verified on the reviewer's own fixture: one 100 m cell holding 1,000, k=100, both engines now give 17.841241 m where run_knn gave 0. self_potential=0 still reproduces the old numbers exactly. AND 114 IS WIDENED: it now walks every PUBLIC entry point rather than the engine list, which is how run_knn escaped it. The find recorded here stands and belongs to 99: tie_mode="sequential" with a seed is the SAMPLED overshoot John asked for, already implemented in this engine since the beginning. Read it before designing option 3.

- ~~154~~ | DONE v1.29.8 | Pro's rule promoted into the core, in run_knn_stats - the one place every door and the Python API reach statistics through, and not the per-neighbourhood inner loop. The same data still runs for mean and median; only the Gini is refused, naming the variable. check_gini_input() carries the reasoning, including the measurement that killed the shift-by-minimum idea.

- ~~162~~ | DONE v1.30 | A SECOND CONFORMANCE KEY, under the mode
  users actually get. The shipped key is pinned to `whole` and has
  to be - it asks for a mean, a median and a Gini, and
  `proportional` refuses those until 118. But from 1.30 the DEFAULT
  is proportional, so the key certified both doors under a mode most
  runs will never use, and the mode nearly every run WILL use was
  checked by nothing. equipop/data/gridby_reference_proportional.csv
  ships beside the first: counts, shares and distances only,
  generated under `proportional`, both doors held to it.
  WHAT IS EXACT FOLLOWS THE MODE, and this is not a relaxation.
  Under `whole` T_k is a number of PEOPLE and 270 against 271 is
  wrong rather than imprecise. Under `proportional` it is a FRACTION
  of people reached by multiplying, and holding an estimate to
  bit-equality asserts more than the mathematics claims. N_k stays
  exact both ways - proportional makes it exactly k by construction,
  and the shipped key reads 400 in all 2360 rows, which is the
  mode's defining property made checkable. reference.py now takes a
  KEY NAME rather than a path, so a third is one entry in KEYS.

- ~~163~~ | DONE v1.30 | BACKLOG 148 WAS HALF-SHIPPED, found while
  adding the overshoot to the manifest. 1.29.6 added `population`
  and `source` to _manifest_rows, wrote the reasoning into the
  docstring - and NEITHER CALL SITE EVER PASSED THEM. So the
  settings that define the numbers were still absent from every
  manifest, and 148's own complaint (Claude could not use two of
  John's manifests to settle which of his runs had differed) was
  still true after the fix. Invisible because the manifest test
  asked for engine, k, cell size and version only.
  A default argument is the easiest place in this codebase for a
  feature to disappear. The manifest now records both ladders, the
  count and type fields, the keepoutside rung, self-potential, the
  overshoot mode, the seed and the source analysed - and a test
  reads them back, broken three ways on purpose.

- ~~164~~ | DONE v1.30.1 | A NEW FEATURE CLASS RECEIVED EVERY
  RESULT ONE ROW EARLY. John's field test of 1.30, 682 points: the
  last row came back <Null>. It is not an off-by-one in a range - it
  is a JOIN ON THE WRONG KEY, and the missing row was the only
  visible part of it.
  A copy carries the ROWS across but NOT the identifiers. The
  destination assigns its own, from scratch, in row order - a
  geodatabase from 1, a shapefile from 0. `_run_tool` carried the
  INPUT's values over (`data[new_oid] = data[oid]`) and joined the
  results on them. John's input was numbered FID 0..681 and the copy
  OBJECTID 1..682, so every result landed one row early and the last
  row had nothing left to receive.
  WHY NOBODY SAW IT, INCLUDING JOHN, WHO WAS LOOKING: the run was in
  `proportional`, which makes N_k exactly k - so N_25 read 25 and
  N_50 read 50 in EVERY row and the shift was invisible in the count
  columns. Dist_k was shifted and no eye can check a distance. Live
  since v1.20.
  A WORSE CASE HAD NO MESSAGE AT ALL: a geodatabase input whose
  OBJECTIDs have GAPS from deleted rows, copied to a fresh contiguous
  1..n. Same name, so the rename branch never ran and nothing was
  printed; measured on a 12-row layer with gaps, SIX rows received
  nothing and the rest were scrambled.
  AND THE MESSAGE WAS THE REASSURANCE THAT HID IT. It said results
  were "matched on row order, which the copy preserves". They were
  matched on VALUES. The fix makes the sentence true rather than
  deleting it: the copy's own identifiers are read back IN ROW ORDER
  and used, and a row-count change is REFUSED rather than guessed at.
  THE SIMULATOR WAS WHY THIS COULD NOT BE REPRODUCED. Its
  CopyFeatures renamed the identifier and KEPT THE VALUES, so a copy
  looked like a relabelled original. Three clean reproduction
  attempts came back green before the stub was fixed. A stub is safe
  only where it is STRICTER than the real thing - 1.29.1's
  isAdvanced, 1.29.3's polygon barriers, and now this. It is the
  THIRD time the simulator has certified a door that could not run,
  and the second time it hid a silent wrong answer rather than a
  crash.

- ~~165~~ | DONE v1.30.2 | PRO WARNED ABOUT THE INPUT WHEN THE
  TRUNCATION BELONGS TO THE TARGET. John, field, 1.30.1: a shapefile
  read, a geodatabase written, and "a file geodatabase layer is
  strongly recommended" printed anyway - then N_33, Dist_33,
  T_LowInc_33 and R_LowInc_33 were written in full, because nothing
  was ever going to truncate. He asked whether it was a known item.
  It was not.
  The warning fired in _read_input on the INPUT's format. Ten
  characters is a property of the TARGET. Pro already had a correct
  target-based message, so the input one was both redundant and
  wrong; it now fires once, after the target is settled, and only
  when the target is a shapefile.
  QGIS HAS ALWAYS GOT THIS RIGHT - check_target() asks about the
  target - so Pro was the odd door out. BACKLOG 103's shape again:
  the doors disagreeing about when to speak.
  A warning that cannot come true teaches people to ignore warnings,
  which is the real cost. Guarded both ways: disabling it fails, and
  so does making it unconditional. NOTE the first guard was written
  AFTER a deliberate break went uncaught - the fix had shipped into
  the tree with no test at all.

- ~~166~~ | DONE v1.30.2 | THE RUN MANIFEST WAS INVISIBLE FOR
  GEODATABASE OUTPUT. John, field, 1.30.1: "I am puzzled ... I can't
  see the csv's". A file geodatabase is a FOLDER, so a sidecar
  written beside `...\testingEQP.gdb\testaMig` is a loose file
  INSIDE the .gdb - and ArcGIS Catalog presents a geodatabase as a
  database rather than a directory, listing no foreign files. The
  manifest was on disk the whole time; only Windows Explorer would
  show it, which John confirmed.
  Two faults in one: the user cannot find their own record of a run,
  and EquiPop drops litter inside a geodatabase. Same shape as the
  `malta.gpkg\malta.gpkg\...csv` files in BACKLOG 101's litter.
  FIXED for .gdb, .gpkg, .sde and .mdb: sidecars go to an
  EquiPop_runs folder BESIDE the container, and the run says so
  rather than leaving the user to search. John's ruling on the
  folder - a manifest per run would otherwise scatter through the
  project folder. SHAPEFILE AND CSV TARGETS ARE UNCHANGED: they land
  beside the file, which is where he already found them, and moving
  them would fix nothing while breaking a habit.
  Not pursued, John's call: making the file visible to Catalog by
  writing .txt instead. Writing into a geodatabase is the thing worth
  stopping, not the extension.

- ~~167~~ | DONE v1.30.2 | THE STUB AUDIT WAS AUDITING A DOOR NOBODY
  RUNS. tools/stub_audit.py carried a SURFACE list regenerated for
  v1.29.1 and never moved since. Measured against what the QGIS door
  actually calls today: TWELVE classes unchecked, including
  QgsProcessingParameterNumber - the class the 1.30 SEED BOX is built
  from - four constants unchecked, among them .Integer and .Double,
  which is precisely the FlagAdvanced 1-vs-2 shape the value
  comparison was added for, and one method, parameterAsStrings.
  So John's clean run of 13 Aug (QGIS 3.42.1, 63 checks, 0 gaps, 0
  skipped) certified the 1.29.1 door honestly and the 1.30 door not
  at all. Surface regenerated: 31 classes, 78 checks, nothing the
  door uses left out. The constant VALUES are taken from the stub
  itself rather than written from memory - a wrong snapshot would
  hand John a false alarm on his own machine, which is a worse
  failure than a gap.
  Zero-check entries were removed rather than left to pad the count:
  a class listed with no methods and no constants is fake coverage.
  Also hardened: the script died with AttributeError where Qgis was
  absent, which made it impossible to smoke-test before sending.

- 118 | STATS ENGINE DONE v1.31, UPSTREAM EXPANSION REMAINS | WEIGHTED
  STATISTICS WITHOUT PERSON EXPANSION. equipop/wstats.py computes
  mean, median, percentiles, sd, se, var, gini, min, max, sum, count
  and range straight from (value, weight) pairs.
  THE CONSTRAINT THAT MAKES IT SAFE, and it holds: for WHOLE-NUMBER
  weights it returns what the expansion returns, checked over ~20,000
  random neighbourhoods per statistic at 1e-12 relative. So this is a
  refactor with a proof and nothing published moves.
  ONE FAMILY OF CASES DIFFERS, AND THE OLD CODE IS THE WRONG ONE: 55
  copies of a single value have a standard deviation of exactly zero;
  the expansion returns ~1.2e-10 of noise from summing 55 large
  identical floats, the weighted route returns 0. Pinned so nobody
  restores the noise in the name of agreement.
  JOHN'S RULING, quantiles are INTERPOLATED not stepped, and his
  reason is the good one: EquiPop already averages the two middle
  values for an even count, which IS a linear interpolation, so
  interpolating everywhere is the consistent generalisation rather
  than a new convention. It also keeps the promise `proportional` was
  introduced to make - a stepped median would move the jump out of
  the count and into the statistic. Guarded by comparing against a
  step median on the same data: as a ring is swallowed the step
  version leaps a whole value gap while the interpolated one does not.
  WIRED v1.31. run_knn_stats compresses each cell's expanded array to
  (distinct value, how many people hold it) in one pass, and the
  crossing ring's weights are multiplied by the same per-cell share
  the binary sums already got. THE REFUSAL IS GONE, both machines
  share one default again, and the line machine 2 printed on every
  run is retired to a stub that returns "" - an older saved toolbox
  calls something harmless rather than dying.
  THE FIRST WIRING HAD NO GUARD AT ALL. Three deliberate breaks -
  dropping the ring share, dropping the crossing ring's values,
  disabling the seeded order - ALL PASSED the whole suite. The cause
  was the fixture, not a missing test: every cell in it held the same
  value, so the median came back 4.0 whatever the weights were and
  the tests could not have failed. tests/test_wstats_engine.py builds
  the layout the other way round, with the ring holding a different
  value from the interior and every expected number worked out by
  hand. All four breaks now caught.
  AND IT FOUND A 40% WASTE. Profiling the newly-live `proportional`
  path showed cell_identity/_mix64 taking 40% of the run. Those
  hashes name cells for the SEEDED ORDER and nothing else reads them
  - ring_weights uses them under `sampled` alone - yet they were
  computed for every crossing ring in every mode. Only visible once
  machine 2 stopped falling back to `whole` and the code ran for
  real. Suite 207s -> 79s, which is faster than before 118 landed.
  STILL TO DO: the expansion UPSTREAM, where counts become persons.
  That is the half that unblocks BACKLOG 38, and it is a change to
  the whole pipeline rather than to one function.
  WHAT IT UNBLOCKS: BACKLOG 38, the continental machine - WorldPop
  counts are fractional and a 1 km African run would try to
  materialise on the order of a billion rows - and `proportional` for
  value statistics, which is three complaints closed by one item.

- 174/175 | DONE v1.36 | THE STATA COMMAND BECOMES A STATA COMMAND.
  John asked, in his own words, whether the Stata functions match
  Stata coding convention. They did not. Six gaps were found; four
  are closed here and two were already closed by his rulings.
  1. [if] [in] - ABSENT. Every Stata command that touches data takes
     them. RULED: they restrict the rows that RECEIVE results, not
     who counts as a neighbour. `equipop if urban==1` computes for
     urban origins and rural people still fill neighbourhoods. This
     is NOT the reference-population ladder, which is a separate
     option answering the other question. Implemented with
     `marksample touse, novarlist`. NOVARLIST IS THE POINT: the
     default also marks out rows with a missing value among the
     variables, which would silently shrink the reference
     population, and missing handling is EquiPop's own (168). John's
     rule was "use Stata's own commands where we can, not where it
     jeopardises our code" - this is exactly that seam.
  2. weight() FOUGHT STATA'S OWN WEIGHT SYNTAX. fweight means "this
     row stands for N identical observations", which IS an EquiPop
     population weight, and Stata validates it. But fweight demands
     whole numbers and EquiPop supports fractional population on
     purpose, so pop() stays for that case. Mutually exclusive, each
     error naming the other. weight() REMOVED - the door could not
     run for eleven releases (172), so there were no working
     do-files to protect. That window closes the moment users appear.
  3. NOTHING WAS RETURNED. Now rclass, with r(cmd), r(cmdline),
     r(varlist), r(treat), r(k), r(r), r(unit), r(selfpot),
     r(N_origins), r(N_missing). r(varlist) is the one that changes
     how the command can be used.
  4. `help equipop` FAILED. See 175 below.
  5. marksample - closed by (1).
  6. Fixed variable names - prefix() added.
  Also: treat() is OPTIONAL, rung 0 of the treatment ladder.

- 185 | DONE v1.40 | THE DECAY PRODUCED THE WRONG DECAYED
  MEASURE. John, on reading 1.39: "The decay uses distances to decay
  reference and treatment population, it doesn't affect distance. So
  there is no need for an extra distance measure - what is interesting
  is ... the decayed sum of reference and treatment populations at k.
  However - and just to be clear - the k-values should aim for a
  NON-DECAYED k. i.e. if k=300 is requested, the 300 nearest
  population is the right call - the decayed populations should be
  reported and are always (as long as the beta has the right sign) be
  smaller than k".
  THE WANTED SEMANTICS ALREADY EXIST, IN THE CLASSIC ENGINE. The
  docstring of analysis.py states them in the original EquiPop's own
  words: "the k-thresholds are still defined by the RAW (unweighted)
  counts - the decayed values are simply recorded at the same moment
  ... Decayed counts are therefore always <= raw counts." It emits
  ND_{k}, TD_{k}, RD_{k} (NAMES at analysis.py:45).
  THE STATA PATH USES THE FAST ENGINE, WHICH DOES SOMETHING ELSE.
  fastcounts.py:217-235 accumulates over the TRUNCATION radius, not to
  the k position, and emits ND_inf / TD_<v>_inf / RD_<v>_inf - an
  unbounded decayed potential over everybody. A legitimate measure,
  but not this method's, and not what was asked for.
  THE FIX, and it is contained: the k loop in fastcounts already holds
  everything needed. Build cumulative DECAYED arrays alongside cp and
  cgrp - cumsum(pop_sorted * w) with the same selfpot adjustment to
  dw[0] that BACKLOG 95 requires - and read them at the same `pos` the
  raw counts use. THE OVERSHOOT RING IS THE CARE POINT: when the ring
  is split, the decayed sum must take the same per-cell fractions `w`
  that grp_k[v] takes at fastcounts.py:171-181, or the raw and decayed
  numbers will describe different neighbourhoods.
  THE INVARIANT IS THE TEST, and John supplied it: with a decreasing
  decay, ND_k <= N_k ALWAYS, and TD <= T. That is a guard no correct
  run can trip - the same shape as 179's.
  Note that this is an ENGINE change, so it lands at every door, not
  just Stata. QGIS and Pro get it too.

- 198 | OPEN | A QGIS INSTALLER, THE SAME TWO STEPS AS STATA. John,
  after the Stata installer worked: can we do this for QGIS on
  Windows and Mac? Yes, and better than Install-from-ZIP.
  HALF ONE, the `net install` equivalent: a PLUGIN REPOSITORY. QGIS
  reads a plugins.xml from any URL added under Plugins > Manage and
  Install Plugins > Settings > Add repository. Host it on GitHub
  pointing at the plugin zip and EquiPop appears in the Plugin
  Manager like any official plugin - INCLUDING UPDATE NOTICES, which
  Install-from-ZIP never gives. One URL paste, once.
  HALF TWO, the `equipop setup` equivalent: a Processing algorithm or
  menu action inside the plugin that runs pip against sys.executable
  from inside QGIS, so it cannot target the wrong Python. The plugin
  is installed first, so the chicken-and-egg resolves exactly as it
  does in Stata.
  --no-deps IS NOT OPTIONAL HERE, and this is the part that could
  break somebody's QGIS. QGIS's Python is a MANAGED scientific stack -
  OSGeo4W on Windows, the app bundle on macOS - and letting pip
  upgrade numpy inside it can break QGIS itself. Install equipop
  alone and leave the stack untouched. Also --user for write
  permission, and a restart, since QGIS caches imports too.
  FIX THE CONTRADICTION WHILE THERE: qgis/README_QGIS.md still
  recommends an ordinary dependency-resolving pip upgrade while the
  testing guide correctly says --no-deps matters. Same class as 182 -
  instructions are part of the release.

- 199 | OPEN, AFTER THE CONFERENCE | ARCGIS PRO CANNOT HAVE AN
  INSTALLER, AND THAT IS ESRI'S DESIGN, NOT OURS. The .pyt toolbox is
  one file and trivial to distribute. The ENGINE cannot be installed,
  because Pro's `arcgispro-py3` conda environment is READ-ONLY until
  the user clones it in the Package Manager. No installer can get
  round that. The best available is the Pro half of BACKLOG 128:
  a doctor that DETECTS the default un-cloned environment and says
  "clone it in Package Manager, then run this again". Detect and
  instruct rather than install. --no-deps applies there too, since
  the conda env already carries numpy, pandas and scipy.

- 200 | OPEN, SCOPED | AN R VERSION OF MACHINE 1. John asked how much
  effort. MEASURED, not guessed - machine 1 is NOT the 9,674-line
  package:
      fastcounts.py  400   the engine
      overshoot.py   436
      cells.py       225
      decay.py       145
      selfpot.py     110
      utm.py         377   projection, already dependency-free
      ---------------------
      core         ~1,700 lines
  Every piece maps onto something R does well. Cell building is
  data.table. The k-nearest search is RANN::nn2 or dbscan::kNN, and
  the fast engine's own approach - m nearest cells, cumulative sums,
  widened retry - translates almost line for line. The overshoot
  ring, self-potential, decay and missing codes are pure arithmetic.
  utm.py ports as transcription, not research, precisely because we
  wrote it ourselves rather than calling pyproj.
  NATIVE R, NOT reticulate. A wrapper would inherit every
  Python-environment problem of this session, and the audience least
  able to repair a broken interpreter is exactly the audience for a
  stats-package port. Same argument that produced utm.py.
  THE CODE IS NOT THE COST; PROVING IT AGREES IS. tests/
  test_conformance.py already exists and exists for this: "a student
  in QGIS and a student in ArcGIS Pro should get the same numbers out
  of the same town, and small disagreements are exactly the kind
  neither would notice." An R port validated against that stored
  reference is an afternoon of checking.
  ESTIMATE, AND IT IS CONDITIONAL: after BACKLOG 195 (Stata into
  parity, with a shared conformance route), roughly a FORTNIGHT of
  focused work for machine 1 - engine, projection, conformance.
  Attempted BEFORE that, do not estimate: the expensive part would be
  establishing what "correct" means for a fourth door.
  CRAN is its own Kit Baum with its own weeks; remotes::
  install_github() works the day it is pushed, exactly like
  net install.

- ~~193~~ | DONE v1.40.5 | THE FIELD PASS NOW ENFORCES ITS
  INVARIANTS. Every stated property is a check with an [ok]/[FAIL]
  verdict; 57 of them, and the count is PINNED, so a block that dies
  before reaching its checks is caught by the tally even when nothing
  raised an error. Each block is wrapped so one failure cannot hide the
  other twenty-two - a field round trip costs a day, and a run must
  therefore return the complete picture, not the first problem. Every
  expected refusal reads its own return code. The pass exits 9 on any
  failure. The data path ships EMPTY with a fallback to the working
  directory and a confirm-file check, so a Mac is not blocked by
  somebody else's C: drive. tests/test_field_pass.py parses the
  do-file and refuses a block with no check, a refusal whose _rc is
  never read, a stale pinned count, a returned hard-coded path, and a
  version stamp that has drifted; all six guards were broken on
  purpose and all six caught it. Block 20 rebuilt on a synthetic count
  column with a -999 sentinel on every twelfth row - deliberate, not
  random, so the count is 907 on every machine. Blocks 11 and 12
  merged so the free self-potential number is compared against the
  rungs in the same dataset rather than across a block boundary.
  STILL JOHN'S: save the Stata log as a release artifact.
  (superseded detail below)
- 193-original | THE FIELD PASS STATES ITS INVARIANTS BUT DOES
  NOT ENFORCE THEM. External review of 1.40.4. equipop_test_pass.do
  has no assert and no exit: a failed property prints a number and the
  run continues. The distance-order count can be non-zero, a refusal
  can silently fail to happen, and the pass still reaches its final
  line. It found 191 only because a human read the number.
  ALSO: block 20 is invalid and HALTS the pass - ValFloat is
  continuous, so after missing(0) 5,645 of 5,838 values exceed their
  population and the treatment guard refuses, correctly. A continuous
  measure belongs in machine 2, not treat(). Build a synthetic COUNT
  column with a -999 sentinel.
  ALSO: the header says 1.40.3 and "Twenty runs" for a 22-block
  1.40.4 delivery, and the data path is hard-coded.
  FIX: assert r(N) == 0 after each count; capture _rc immediately
  after each expected refusal and fail if it did not occur; a checked
  configuration line for the path; pin the version and run count; and
  SAVE THE STATA LOG AS A RELEASE ARTIFACT so "field-tested" has
  durable evidence.

- ~~201~~ | DONE v1.40.5 | BLOCK 17 ASSERTED THE DECAY MODELS IN THE
  WRONG ORDER, AND NOBODY HAD EVER COMPUTED IT. The block said that at
  the same half-life `power` keeps MORE mass than `negexp`, so its
  ND_300 would be the larger. Measured on stata_test_data.dta at
  half-life 800 m: negexp ND_300 averages 283.6 and power 199.9, and
  power is the smaller on 10,839 of 10,883 rows. The reasoning error
  is worth recording because the shipped help text is CORRECT and was
  not the source: "power falls quickly and then very slowly, so
  distant places never quite stop counting" describes the TAIL. Both
  models are 0.5 at the half-life by construction, so that distance is
  where they CROSS - power is the harsher curve inside the bandwidth
  and the gentler one outside it. At half-life 800 m, negexp gives
  0.958 at 50 m and 0.063 at 3,200 m; power gives 0.665 and 0.433.
  Which model keeps more mass therefore depends on where the
  NEIGHBOURHOOD sits relative to the bandwidth, and here a k=300
  neighbourhood has a median radius of 48 m against a half-life of
  800 m, so it lies almost entirely on the side where power cuts
  harder. The block now asserts the one-sided rule that is
  exceptionless - inside the half-life, power keeps less - and says
  in the text why the reverse is NOT asserted: Dist is the distance to
  the FURTHEST neighbour, so a row can reach past the bandwidth while
  most of its 300 people are still well inside it. Only 44 of the 140
  rows reaching past 800 m have power above negexp, which is why the
  reverse would have been a flaky check. LESSON, and it is finding 14
  again: a stated invariant nobody has computed is a belief, not a
  guard. Both engines agree, so this was never a code defect - the
  expectation was wrong.

- ~~202~~ | DONE v1.40.6 | BLOCK 4 ASKED FOR A COLUMN THAT HAS NEVER
  EXISTED. Found by John's 1.40.5 field run on Windows - the first
  time this pass has ever been able to fail. `k(200) r(2000)` returns
  THREE columns, not four: N_200, Dist_200, N_r2000. There is no
  Dist_r2000 and there should not be. The two machines are inverses:
  k asks for PEOPLE and the distance is the answer; r gives the
  DISTANCE and the people are the answer, so a Dist_r could only hold
  the number the user typed. The contract is stated at
  equipop/stata_bridge.py line 355 and the engine has always honoured
  it. The wording "four new columns" was carried across from the
  pre-1.40.5 file and turned into an assertion without being measured
  - the exact fault the rebuilt file's own header warns about, three
  paragraphs above the block that committed it. THE MECHANISM WORKED
  EXACTLY AS DESIGNED: the block was trapped, so the failure did not
  stop the run; 57 of 57 checks still executed; the tally proved
  nothing had been skipped; and the verdict named the count. A
  do-file-only fix, so the Stata freeze holds.

- 203 | ~~RULED OUT~~ SESSION 12 | SHOULD A RADIUS RUN REPORT A
  DISTANCE AT ALL? 202 establishes that Dist_r would be the constant
  the user typed, which is useless. But two OTHER distances inside a
  fixed radius are not constant and are not currently offered:
  the MEAN distance to the N_r people found, and the distance to the
  FURTHEST one actually included, which is <= r and varies. Both are
  real descriptions of how the population sits inside the circle, and
  the second is the natural companion to Dist_k. Not a defect and not
  urgent - a method question, and John's to rule on. Do not build
  before he does.
  JOHN'S RULING, SESSION 12, BOTH HALVES REFUSED: "radius is radius
  and good enough so let us not persue neither (a) or (b)".
  SO A RADIUS RUN REPORTS NO DISTANCE, AND THAT IS THE DESIGN, not an
  omission. The next session to notice the asymmetry - k gives
  Dist_k, r gives nothing - should read this entry and stop, rather
  than raise it a third time.
  THE ARGUMENTS THAT DID NOT WIN, recorded so they are not rebuilt
  from scratch. (a) was nearly free: the engine already computes the
  position of the last included cell and discards the distance, so
  the maximum is one lookup already in hand, and it is the SAME
  STATISTIC as Dist_k under 115 - the maximum extent of the accepted
  ring - with the stopping rule swapped from k people to r metres.
  (b) was not: a population-weighted running total of distance
  through the inner loop of both engines, both doors and Stata, and
  it is CELL-RESOLUTION DEPENDENT in a way a maximum is not -
  everyone in a cell shares one distance, so the 225 aliasing rides
  in the mean and mostly not in the max, and the self-potential
  radius would have to be honoured or the mean moves with cell size.
  None of that outweighed the ruling, and the ruling is the shorter
  answer: the radius IS the neighbourhood definition, and a run does
  not owe a second description of it.

- ~~204~~ | DONE v1.40.7 | equipop_showcase.do CRASHED AT SECTION 6 AND
  HAD DONE FOR MANY RELEASES. Found because John ran the wrong file by
  accident. `Data.store(c, None, [v if isfinite(v) else None ...])` -
  Stata refuses None for a numeric and raises "the specified value
  should be a numeric value". THIS IS BACKLOG 173, whose fix,
  to_stata_values(), has been in equipop_run.ado since 1.40.1; the
  showcase simply never adopted it. TWO crash sites, not one, so
  sections 7 AND 8 had never run in Stata at all - which means their
  EXPECT numbers had never been compared against anything. All of them
  are now measured. Also fixed: section 4 demonstrated pop() with a
  0/1 marker and NO treatmode(flags), so it produced .0044 where its
  own comment expected .2076 - a live instance of the 47x trap sitting
  in the file we hand to new users. Every other EXPECT was stale too,
  mostly because the default overshoot changed from whole to
  proportional: N_200 read 228.88 and is 200. The file called itself
  "EquiPop 1.1". LESSON: nothing tested this file because nothing READ
  it. tests/test_field_pass.py now walks EVERY shipped .do file,
  refuses the None-store pattern, and compiles every `python:` block;
  both guards were broken on purpose and both caught it.

- 205 | ~~RULED OUT~~ SESSION 12 | THE STATA COMMAND CANNOT REACH MACHINE 2 AT
  ALL. There is no stats() or values() option in equipop.ado's syntax
  line - mean, median, quantiles and Gini over a neighbourhood are
  unreachable from Stata except by hand-written python: blocks, which
  is exactly why section 6 of the showcase exists and exactly why it
  was able to rot unnoticed. THIS ALSO EXPLAINS BLOCK 20 OF THE FIELD
  PASS: whoever wrote treat(ValFloat) missing(0) was not being
  careless, they were reaching for the only handle the door offers. A
  user with a continuous variable has nowhere correct to put it. QGIS
  and Pro both expose machine 2. Sizeable, and NOT for this week.
  JOHN'S RULING, SESSION 12: "machine 2 door from stata is not
  necessary (at least for now) since stata is a statistics software
  we can rely on the built in functions instead."
  THE REASONING IS BETTER THAN THE FEATURE. Machine 2 computes
  weighted means, medians, percentiles and Ginis over a
  neighbourhood. Stata computes weighted statistics natively and
  better than we will - `summarize [aweight=]`, `_pctile`, `ineqdeco`
  - and what it CANNOT do is build the neighbourhood. So the right
  division is: EquiPop hands Stata the neighbourhood (N_k, T_k, R_k,
  Dist_k) and Stata does the statistics on it. That is not a gap
  being tolerated; it is each tool doing the part it is good at.
  "AT LEAST FOR NOW" IS THE OPERATIVE PHRASE. If a measure arrives
  that Stata cannot express over a k-neighbourhood, this reopens.
  NOTE FOR ANYONE COUNTING DOORS: machine 2 therefore has three doors
  (Python, QGIS, Pro) BY DESIGN and not by omission. A reachability
  check must record the ruling, or it will report this as a hole
  every time it runs.


- ~~118~~ | HALF DONE, engine side | FRACTIONAL WEIGHTS NO LONGER
  ROUND. build_cells(weights=...) carries a weight column into
  CellData.value_weights, and run_knn_stats sums weights per distinct
  value instead of counting rows. Empty by default, so nothing moves
  for any existing caller. MEASURED ON JOHN'S WORLDPOP RASTERS, and
  three DIFFERENT quantities were being conflated - the first version
  of the test asserted the wrong one and failed, correctly:
      places lost   people in them   net mass
      Burundi 85.0%      52.9%         40.1%
      Rwanda  78.2%      39.3%         28.5%
      Austria 98.3%      66.5%         60.1%
      Denmark 98.1%      69.1%         58.6%
  THE FIRST COLUMN IS THE ONE THAT MATTERS and it is the worst: a
  pixel rounding to zero stops being an origin AND stops being
  anybody's neighbour, so the map loses the location, not just the
  headcount. In Denmark that is 98% of occupied pixels. Net mass
  UNDERSTATES the damage because round-ups compensate. And every
  measure worsens with latitude, so Europe-against-Africa was biased
  by construction. STILL OPEN: stata_bridge.py:738 still expands rows
  into persons. That is the Stata door only - the continental path
  goes through build_cells and run_knn_stats directly and is now
  unblocked. Rewiring the door changes behaviour for existing Stata
  users, so it wants its own session and its own release.

- ~~206~~ | DONE, engine side | A FOLDER OF RASTERS, MERGED BY
  GEOMETRY RATHER THAN BY NAME. equipop/rasterfolder.py. John's rule:
  different ground does not overlap and becomes ROWS; the same ground
  does overlap and becomes COLUMNS. That is measurable, so the merge
  survives WorldPop renaming everything, and filenames only LABEL the
  columns - a wrong label is cosmetic and visible, a wrong merge is
  silent. THE TEST IS DATA OVERLAP, NOT EXTENT: Burundi and Rwanda
  share a bounding box over 1.4M cells and not ONE pixel carrying data
  in both. Naming degrades in three tiers - a registry of known
  conventions, then a user regex or explicit dict, then the filename
  stem - and says out loud when it fell through. Verified on all four
  real rasters: 11,562,095 points, one column f_15_2020, latitude
  -4.469 to 57.750, mass conserved exactly at 1,721,880.
  ZEROS ARE KEPT (John): the point set is the UNION over every layer,
  so a pixel with no women aged 15-19 but three men survives with a
  real 0.0. raster.py had the same defect - it chose the point set
  from whichever variable was listed FIRST - and is fixed too.
  Age bands are NOT all five years: 0 is under-one alone, 1 covers
  1-4, then fives, then an open 90+. band_width() returns None for the
  open band, so cohorts can be summed but never averaged across bands
  without the widths. REMAINING: the GUI on top, in the Q and Pro
  doors, over this one function.

- ~~207~~ | DONE | A CROSSING RING CUT BY THE WINDOW EDGE WAS TREATED
  AS A COMPLETE RING. Not a distance defect - a NEIGHBOURHOOD
  COMPOSITION defect, which showed in the radius AND in every group
  share built from that ring.
  MECHANISM, one line: overshoot.ring_bounds() walks forward with
  `while hi + 1 < n`, where n is the size of the FETCHED WINDOW, not
  the size of the ring. A ring running off the edge stopped there and
  was believed.
  WHY NOTHING NOTICED: under proportional overshoot the walk takes
  exactly enough of the ring to reach k, so N_k is EXACTLY k however
  much of the ring is present. The count guard cannot see it. The
  v1.16.4 ladder cannot either - it re-solves origins that FAIL TO
  REACH k, and these reached it.
  MEASURED, before the fix:
    lattice, 1 person per cell, 4-cell ring at 200 m -
      window 11 -> Dist_11 200.00 (2 of 4 cells seen)
      window 12 -> 182.57 (3 of 4)
      window 13 -> 173.21 (complete). N_11 exactly 11 throughout.
    Burundi + Rwanda, 1 km, k=1000 - 249 of 46,317 origins moved,
      max 168.79 m.
    Burundi + Rwanda fixture, 500 m, cross-border share - 16 origins
      moved, worst 0.043 against a converged 0.065, a THIRD of the
      value, with N_500 exact.
  NOT MONOTONE IN m: 34 rows moved at m=32, 426 at 64, 33 at 128. What
  matters is whether the window edge happens to fall inside a ring, not
  how wide it is - so there is no safe constant and a bigger default
  would not have fixed it. Detection was the only route.
  THE FIX: if the ring crossing any requested k reaches the last
  fetched cell, hand the origin to the ladder, which already exists for
  the other reason. After it, every window from 32 to 2048 agrees
  exactly on both radius and share. Cost is visible and self-limiting:
  8,745 of 8,798 origins widened at m=32, 291 at m=128, none at 512.
  John's ruling - continental and possibly global, so correctness over
  speed.
  WHY THE FIRST REPRODUCTION FAILED: it used RANDOM POINTS, which never
  tie, so every "ring" was one cell and could not be cut. WorldPop is a
  LATTICE. Reading the mechanism first and then building the case
  deliberately took one attempt; guessing at data took none anywhere.
  Pinned by tests/test_window_sensitivity.py - 11 tests, 4 of which
  fail on the old code naming the exact drift.

- ~~207b~~ | DONE | THE SUITE DEMANDED OPTIONAL LIBRARIES AND FAILED
  RATHER THAN SKIPPING. John installed the working tree on a clean
  Windows venv - the exact instruction Claude gave him - and got four
  reds. THREE were Claude's incomplete install line: the suite needs
  openpyxl to read the Book's Berlin .xlsx and matplotlib for
  map_output, and neither is a requirement of the engine.
  equipop/__init__.py already has _EXTRAS precisely so an absent
  optional library raises a NAMED, helpful ImportError, and
  test_names_resolve_even_when_an_optional_library_is_absent pins that
  behaviour - but two tests treated the designed ImportError as a
  failure. They now accept it and keep failing on the real target, a
  WRONG MODULE NAME in _LAZY, which surfaces as AttributeError. The
  Berlin test uses pytest.importorskip.
  AND THE FIX WAS PARTIAL AT FIRST: test_every_public_name_still_
  resolves has TWO loops over _LAZY and only the first was repaired, so
  the suite came back red for the identical reason. Finding 27 again -
  fix the whole file, not the first hit.
  Verified in a clean venv WITHOUT either library: 654 passed, 13
  skipped, nothing failed; and 656 passed, 11 skipped where both are
  present.

- ~~208~~ | DONE | THE ARCGIS RUN MANIFEST WAS NOT WRITTEN ON WINDOWS,
  AND WAS WRITTEN TO THE WRONG PLACE ON LINUX. Diagnosed from John's
  machine once the test was made to print its own message log:
     Could not write the run manifest ([WinError 123] Felaktig syntax
     for filnamn...: 'memory\\C:')
  TWO faults, and the second is the one that matters.
  (1) SIMULATOR. tests/test_arcgis_stub.py's Describe() fell back to
  f"memory/{key}" for anything not in catalog_paths. 'memory/' is the
  ArcGIS in-memory workspace and belongs on a bare LAYER NAME; put in
  front of an absolute path it invents a shape real arcpy cannot
  return. Now only applied to names that are not already paths.
  (2) PRODUCT, and it was silent. _sidecar_path rebuilt the output
  folder with os.sep.join(parts[:holder]) - fragments rejoined - which
  drops whatever preceded the first fragment. On POSIX a leading '/'
  VANISHED and an absolute path quietly became a relative one, so the
  manifest landed in a junk tree under the working directory and every
  assertion in the test still held. A Windows drive letter survived
  only by luck, because 'C:' carries its own root. It now SLICES THE
  ORIGINAL STRING, keeping root, drive and separators exactly.
  THE LESSON: the Linux run was not passing, it was failing quietly in
  a way the assertions could not see. Finding 33 the other way up - a
  green test can be as wrong as a red one, and the platform difference
  was the only thing that made it visible.
  Pinned by test_the_sidecar_folder_keeps_the_root_it_was_given, which
  was reverted against the old code and caught it.

- ~~38~~ | HALF DONE | THE CONTINENTAL PATH HAS A DOOR. bigrun had
  been built and regression-tested since v1.16.8 and was reachable
  only by hand-assembling a CellData.
  THE SPINE: equipop/doors/continental.py, run_folder(). Every
  decision a door would otherwise make lives here - which column holds
  the people, whether the extent wants tiling, what to refuse, what to
  say. John's ruling: "one ring to rule them all, and different doors
  that can use it". The doors have drifted three times in this
  project and every time a rule lived in two places. 15 tests, none
  needing QGIS or arcpy.
  QGIS: DONE AND REGISTERED. qgis/equipop_qgis/alg_continental.py,
  third tool in the provider. The stub gained
  QgsProcessingParameterFile/Crs/FolderDestination and the two readers
  they need. Shared help written under "ContinentalRasters" in
  doors/help.py, so both doors describe it in identical words.
  PRO: WRITTEN, NOT REGISTERED. The class sits in EquiPop.pyt on the
  same run_folder with the same arguments, but self.tools does NOT
  list it, and the reason is in a comment there: the arcpy simulator
  cannot exercise a DEFolder box or NumPyArrayToFeatureClass, so
  NOTHING IN THIS REPOSITORY HAS EVER RUN IT. Registering it would put
  an untested tool in front of users on the strength of a reading, and
  a reading is what has been wrong repeatedly this week - 207 twice,
  208, the manifest, the partial _LAZY repair. Extend
  tests/test_arcgis_stub.py first, THEN add it to self.tools.
  A COUNTRY-PER-FOLDER TREE WORKS AS IT ARRIVES (John's question).
  _tif_paths already recurses; verified against the same files laid
  out flat - 267,632 points either way, identical to the row, and the
  countries read from the filenames. AND IT CORRECTS AN EARLIER
  SUGGESTION OF CLAUDE'S: the proposed tier-3 fallback "subfolder name
  becomes the group" would have broken exactly this layout, turning
  bdi/ and rwa/ into two columns when they are one cohort on different
  ground. Not built. Do not build it.

- ~~209~~ | DONE | THE QGIS CONTINENTAL DOOR SHIPPED WITH THREE
  WIRING FAULTS AND NOTHING IN THE SUITE COULD SEE ANY OF THEM,
  BECAUSE NOTHING EVER RAN IT. John found the first on his first
  click, in QGIS 3.42.1 / Python 3.12.9.
  (1) `self.check_versions(ch)` -> AttributeError. It is a MODULE
      function in base.py, not a method. alg_counts.py has the right
      form four lines into its own processAlgorithm; Claude wrote the
      call from a reading instead of from the working example.
  (2) `tiles` arrived as the literal string "TEMPORARY_OUTPUT". An
      optional FolderDestination left untouched does not come through
      empty, so a blank box would have written tiles into a folder of
      that name, silently. Visible in John's own log line and missed.
  (3) `QMetaType.Double` -> AttributeError. QGIS 3.38 moved field
      types into QMetaType::Type; base.py:450 already had
      QMetaType.Type.Double and Claude dropped the '.Type'.
  THE REAL DEFECT IS THE SECOND SENTENCE. The spine's 15 tests call
  run_folder directly and the provider tests only CONSTRUCT the
  algorithm, so the whole of processAlgorithm was unexercised. Faults
  1 and 3 are one-line typos that any execution would have caught.
  tests/test_qgis_continental.py now EXECUTES processAlgorithm against
  the simulator - 9 tests, and it found fault 3 before John did.
  Finding 28 again: prefer a test that RUNS the thing to one that
  asserts about it. And the doctrine at the top of test_qgis_door.py
  said it already - "this proves LOGIC. Only QGIS on a real machine
  proves behaviour, and the gap between those two is where all the
  interesting bugs live."

- 210 | OPEN, SMALL | READ RASTERS FROM INSIDE A ZIP. John asked; GDAL
  /vsizip/ does it and rasterio inherits it. MEASURED on the fixture:
  byte-identical data (57,666.8 people both ways) at about 3.5x the
  time, and the cost is DECOMPRESSION not opening - five opens without
  reading pixels cost 0.002 s, with reading 0.021 s. So it does not
  amortise: a one-off continental pass is worth it, repeated runs over
  the same folder are not. ~15 lines in _tif_paths, enumerating
  members and handing back /vsizip/ paths; everything downstream is
  unchanged. DEFERRED by Claude until John's QGIS test is finished -
  changing the engine underneath a test in progress muddies what the
  test says. Ask John whether zip or loose wins when a folder holds
  both.

- ~~211~~ | DONE | A REGISTRY BUILT FROM ONE SAMPLE IS NOT A REGISTRY.
  John pointed the QGIS door at his real Burundi + Rwanda download -
  120 rasters - and ALL 120 NAMES FELL THROUGH the "known convention".
  Claude wrote that pattern against the four sample files he happened
  to have, every one of them `..._CN_100m_R2025A_v1`. The real bulk
  download is `..._CN_1km_R2025A_UA_v1`: the pattern demanded `\d+m`
  where the file says `1km`, and had no slot at all for `UA`.
  THE CONSEQUENCE WAS NOT COSMETIC. With no parse, each file was
  labelled from its own filename INCLUDING THE COUNTRY, so bdi_f_15
  and rwa_f_15 became TWO columns instead of one - the country leaking
  into the label is exactly what the design forbids - and 60 cohorts
  became 120 columns. folder_to_cells then refused, correctly, because
  it could not tell which of 120 columns held the people.
  FIX: only the four LABEL fields are pinned - iso3, sex, age, year.
  Everything after the year is provenance and WorldPop varies it
  freely. A file differing only in that tail now takes the SAME label,
  overlaps on the same ground and is refused by the existing guard,
  which is right: constrained and UN-adjusted are two estimates of the
  same people and must not be mixed.
  Tested against John's ACTUAL filenames, copied verbatim from his log.

- ~~212~~ | DONE | WORLDPOP SHIPS TOTALS ALONGSIDE THEIR PARTS, AND
  SUMMING THEM COUNTED EVERYBODY TWICE. From John's own log: bdi age
  00 has f 224,972 and m 229,148, and t is EXACTLY 454,120. His folder
  holds f, m AND t for every age. sum_cohorts=True would have added
  all three, and nothing about the result would have looked wrong -
  the map would simply have been twice as populous.
  totals_overlap_parts() now finds every t_ label whose f_ and m_ are
  both present, and summing such a folder is REFUSED by name, telling
  the user to keep one set or the other. Loading them as separate
  columns is still fine, because as columns they are three honest
  measurements.

- ~~213~~ | DONE | A LOADER REFUSAL REACHED THE USER AS A TRACEBACK.
  The QGIS door caught ContinentalError only; rasterfolder refuses
  with ValueError, so John got a Python stack where a sentence
  belonged. Now caught too.

- ~~214~~ | DONE | "IT ASKS FOR THE POPULATION, BUT ALL ARE
  POPULATIONS" - John, on his real 120-raster download. THE TOOL WAS
  IMPOSING A SHAPE HIS DATA DOES NOT HAVE. folder_to_cells demanded a
  single `weight` column before it would do anything, and his folder
  holds SIXTY population columns of which none is "the" one.
  TWO THINGS WERE CONFLATED, and John separated them: "what are we
  generating - if the answer is a point-file with the coordinates and
  values listed we are at a good place for a start".
    A. THE POINT TABLE. 53,636 points, 60 fields, two countries on one
       lattice, zeros kept. Needs NO k and NO weight, because nothing
       is being counted yet. Useful on its own and the natural thing
       to look at before deciding anything. It was IMPOSSIBLE before.
       A blank k box now produces exactly this.
    B. THE NEIGHBOURHOOD RUN. This genuinely needs a weight, because k
       is a number of PEOPLE and something must say which.
  AND THE WEIGHT IS USUALLY NOT A COLUMN. With sixty cohorts the
  population is their SUM. weight now accepts a WORD:
    'total' - sum the t_ columns. Ages are disjoint, so everybody once.
    'sexes' - sum f_ and m_. The same people by the other route.
    or a column name, to make one cohort the population.
  The refusal now names those three choices instead of listing sixty
  column names and no way forward.
  METHOD NOTE for the doors: the natural EquiPop shape here is WEIGHT
  = EVERYBODY, GROUPS = THE COHORTS - "of the 1000 nearest people, how
  many are women aged 15-19". The weight is not one of the sixty.
  LESSON: the refusal was correct and useless. It said what was
  missing and nothing about what to do, and it took the user asking
  "what are we generating?" to show that the question itself was
  wrong.

- ~~215~~ | DONE | THE COUNTRY NEVER REACHED THE POINT TABLE. John:
  "the iso/country identifier should be ROW and not column ... the user
  can choose to load one country or load several to treat as one
  geography (Iso can then be a matter for selection in Q and eventually
  Pro)". He was half right and the half he spotted was the useful one:
  countries were ALREADY rows - 120 rasters gave 60 columns - but the
  manifest knew iso3 per FILE and the points carried none, so it could
  not be selected on in QGIS at all.
  Now a categorical `iso3` field, well defined per point because the
  countries share no data pixel. Categorical because a continental run
  is tens of millions of rows.
  THREE PLACES ASSUMED EVERY NON-COORDINATE COLUMN IS A MEASUREMENT,
  and each surfaced only when tested:
    the keep-zero filter tried to SUM it        -> TypeError
    a merge silently dropped the categorical    -> back to str, undoing
        the whole point; caught by the test that measures the dtype
    the QGIS writer cast every field to float   -> "could not convert
        string to float: dnk"
  That is the shape to remember, not the individual fixes: adding one
  LABEL column to a table of measurements breaks every loop that
  selected columns by what they are NOT.

- 216 | OPEN, RESEARCHED | VITAL-EVENT RASTERS EXIST AND SIT ON THE
  SAME LATTICE - AND THERE IS A CIRCULARITY TRAP. WorldPop publishes
  Births and Pregnancies at 0.000833333 decimal degrees, WGS84 - the
  same grid family as the age-sex rasters - so they would load as
  COLUMNS with no new machinery. Two practical notes: their filenames
  are a different convention entirely (AZE2010adjustedBirths.tif,
  BEN2010pregnancies.tif - upper-case ISO3, no separators), one cheap
  registry entry; and the Africa/LAC birth archive is 30 arc seconds
  (~1 km), so resolution varies by product and region and the lattice
  check will catch a mismatch.
  THE TRAP, and it is the important part: WorldPop DERIVES births from
  the population surfaces using age-specific fertility rates from
  surveys and UN statistics. So births / women-15-49 partly reproduces
  the ASFRs used to build the births. The national total is right
  (UN-adjusted); the SPATIAL variation would largely be the
  distribution of women of childbearing age, not fertility behaviour.
  Fine for service planning - how many births near this clinic, which
  is what the product is for. Close to circular for inferring where
  fertility is higher.
  JOHN'S TWO-YEAR COHORT ROUTE IS STRONGER and ALREADY WORKS: the year
  is part of the label, so f_15_2020 and f_15_2026 are two columns on
  the same points and cohort change is arithmetic on the table.
  Verified.

- ~~217~~ | DONE, QGIS | MACHINE 4: SPATIAL DEMOGRAPHY.
  John's ruling that it is its own machine - machine 3 turns rasters
  into points, machine 4 asks a demographic question of them.
  equipop/doors/demography.py. Four indices, all of them a RATIO OF
  TWO GROUPS over the same neighbourhood:
    child-woman ratio   under-5 / women 15-49
    dependency ratio    (under-15 + 65+) / 15-64
    ageing index        65+ / under-15
    sex ratio           men / women
  NOT WHAT WORLDPOP ALREADY PUBLISHES. Their gridded Dependency Ratio
  is computed from EACH CELL'S OWN age structure; this is over the k
  nearest thousand people. Theirs describes a cell, ours describes the
  population a person is among - and a ratio over a bespoke
  neighbourhood inherits nothing from an administrative unit, which is
  the whole argument.
  THE IRREGULAR BANDS ARE THE TRAP AND ARE TESTED AS SUCH. 0 is
  under-one alone, 1 covers 1-4, then fives, 90 is open. Every
  selector works in BAND STARTS, never arithmetic on the age number:
  15-49 gives 15,20,...,45 and must not slide into 50; under-five is
  TWO bands and taking only '0' would miss four fifths of the
  children; 15-64 must not collect the open 90+.
  f/m/t IS HANDLED: t is exactly f+m, so the parts are used when
  present and the totals only when they are not.
  THE CONVERSION THAT NEARLY WENT WRONG: build_cells MULTIPLIES a
  group column by the weight, because a group is normally a 0/1
  marker. A COMPOSED group is already a headcount, so passing it
  unconverted would have multiplied children by the total population -
  roughly 500x too large and entirely plausible-looking. folder_to_
  cells now converts a composed group to the share of the weight,
  which the multiplication turns back into the count. Pinned by
  test_the_halves_are_HEADCOUNTS_not_shares.
  VERIFIED END TO END on a two-country pyramid: of 500 people, 94.5
  children under five and 110.2 women 15-49, ratio 0.86, N exactly
  500.
  REMAINING: the QGIS tool. plan() is deliberately separable from
  run_index() so a door can show the suggested columns and let the
  user add or remove them - John's design.
  RATE MEASURES STAY OUT. TFR, ASFR, CBR, CDR, LE need vital events;
  an age-sex folder carries stock. Tested by absence.

- ~~218~~ | DONE | MACHINE 4'S QGIS DOOR - and it broke the PLUGIN
  before it broke itself. initAlgorithm() imported the package to
  build its tick-box list. That runs while QGIS constructs the dialog,
  so with equipop absent the whole plugin died at startup - turning
  "install equipop" from a sentence into a traceback, which
  test_the_plugin_still_loads_when_the_package_is_missing exists to
  prevent and which the other three tools survive. The list is now
  written down in the door, and a test pins it against the package's
  own so the two cannot drift.
  SEVERAL INDICES IN ONE PASS (John's preference). At continental
  scale the cost is loading the rasters, projecting the points and
  building the tree, and that is identical whichever index is wanted -
  so four indices one at a time is four of those. run_indices()
  composes every numerator and denominator, carries them all as
  groups, and divides pairwise afterwards. Verified: four indices, one
  [cells] line, one fast pass.
  TWO MORE FOUND BY EXECUTING IT rather than constructing it:
    a pointless `from qgis.core import QgsProcessingContext` inside a
      helper - refused by the simulator, dead weight in QGIS;
    MACHINE 4 BYPASSED THE SPINE'S FOLDER CHECK, because it reads the
      labels BEFORE running in order to show which columns an index
      will use. A bare FileNotFoundError escaped past every door's
      handler. check_folders() is now shared and called first.
  AND ONE OF CLAUDE'S TESTS WAS WRONG AGAIN: the one-pass test counted
  a phrase printed by BOTH the loader and the spine, and failed on a
  run that was perfectly correct. It counts "[cells]" now.

- 219 | OPEN, JOHN'S RULING RECORDED | NO RESTRICTION ON WHAT MAY BE A
  WEIGHT. Claude proposed refusing a weight column that is not a
  headcount - k is a number of PEOPLE, so weighting by elevation gives
  "the 1000 nearest metres of altitude", which runs and produces a
  plausible meaningless map. JOHN RULED AGAINST: "there might be
  rasters that have an odd composition that still are valid to run -
  users of EquiPop are mostly academics, and would understand the
  problems". Recorded rather than built. The run already SAYS which
  column it used as the population, which is the provenance without
  the paternalism. Revisit only if a real user is bitten.

- ~~220~~ | DONE, engine side | THE LATTICE JOIN. John's idea, and Claude's
  narrowing of it. QGIS already counts points in cells and does it
  well; rebuilding that would duplicate mature tooling. THE HARD PART
  IS THE LATTICE: EquiPop knows the exact grid the demographic points
  sit on and QGIS does not, so a join done outside is approximate at
  cell boundaries. The sharp capability is "snap this layer to MY
  lattice and count or sum it" - one operation, using the grid we
  already own.
  AND THE REFRAMING THAT MATTERS: once supermarkets are on the
  lattice, "how many in this cell" is almost always zero and almost
  never the question. The question is how many among the k nearest
  people - which is 2SFCA, and equipop/fca.py ALREADY HAS IT: fca(),
  fca_segments(), fca_propensity(), tested. Demographics are the
  demand side, POIs the supply side, same k in both. So this is not a
  new machine; it is the missing INPUT to one already built and never
  driven at continental scale.
  John: "the lattice join solution is well suggested - and yes I would
  like to integrate it".

- ~~220b~~ | DONE, engine | equipop/latticejoin.py.
  snap_to_lattice() counts or sums a point layer onto the grid the
  rasters define; join_to_points() puts it on a machine 3 table by the
  INTEGER LATTICE INDICES, never by distance. load_folder gained
  keep_index= to carry those indices out. Verified: 40 real cell
  centres snapped and every one returned to its OWN cell; totals
  preserved; untouched cells a real 0.0 rather than an absence, the
  same rule the raster loader uses.
  ONLY OCCUPIED CELLS ARE RETURNED. A supermarket layer touches a
  vanishing fraction of a continent; a row of zeros for every other
  cell would be tens of millions of rows saying nothing.
  THE HONEST LIMIT, found by a test of Claude's that failed and was
  right to: a coordinate built as origin + 100*pixel divides back to
  99.999999999999, because adding a small offset to a number near 29
  degrees and subtracting it again loses bits. So a point within one
  floating-point ULP OF A CELL EDGE may fall either side, whatever
  rounding rule is used, and NO ROUNDING CHOICE REMOVES IT. What IS
  guaranteed and tested: points anywhere inside a cell land together,
  and adjacent cells stay distinct. Real coordinates are never on an
  edge. A test now pins the caveat so nobody later "fixes" it and
  believes they have.
  SHAPED FOR fca(): the output renames to x, y, <supply> and goes
  straight in. Demographics are the demand side, this is the supply
  side, same k in both.
  REMAINING: the QGIS door - reading a vector layer, reprojecting it
  to the raster CRS, and handing over coordinates. And fca() itself
  has never been driven at continental scale.

- ~~221~~ | DONE | THE SIMULATOR WAS MORE PERMISSIVE THAN THE THING IT
  SIMULATES, AND SO CERTIFIED A CALL QGIS REJECTS. John's run computed
  46,071 origins and TWO indices in 10.8 s and then died on the last
  line before the layer was written:
     TypeError: parameterAsSink(): argument 5 has unexpected type 'int'
  BOTH continental doors passed a literal `2` as the geometry. Two
  numberings live in QgsWkbTypes - GEOMETRY types (Point=0, Line=1,
  Polygon=2) and WKB types (Point=1, LineString=2, Polygon=3) - so the
  2 meant POLYGON in the numbering that matters, and PyQGIS refuses a
  bare int regardless. base.py had it right all along by passing
  source.wkbType(); the new doors had no source layer and Claude wrote
  a number instead of finding the constant.
  THE DEFECT WAS THE STUB. tests/qgis_stub.py accepted anything, so 12
  door tests passed against a call that cannot work. Tightening it to
  refuse a bare int reproduced John's failure immediately.
  AND TIGHTENING IT EXPOSED THE STUB'S OPPOSITE ERROR: its fake layer
  returned a plain int from wkbType(), so the new check rejected
  base.py's CORRECT call - 44 tests red. The simulator was wrong in
  both directions at once, permissive where it should refuse and
  unrealistic where it should be faithful.
  LESSON, and it is the sharpest form of finding 33: a simulator that
  is more forgiving than reality does not merely fail to catch bugs -
  it ACTIVELY CERTIFIES them. Every green test against it was a lie
  about this call. When a door works under the stub and fails in QGIS,
  suspect the stub before the door.

- ~~222~~ | DONE | THE OUTPUT DID NOT EXPLAIN ITSELF. John, on his
  first real result: "I have no explanation to what the field names
  are representing". Quite right - T_age_num_1000, R_age_den_1000,
  SumN and MaxDistance are unreadable unless you wrote the code.
  explain_fields() now prints one line per field at the end of every
  machine 4 run, including which cohorts each half added up, which
  column IS the answer (marked >>>), and which two are diagnostics of
  the SEARCH rather than results - SumN is the population of the whole
  fetched window and MaxDistance the distance to its furthest cell;
  neither is an answer and both had been sitting in the table looking
  like one.

- ~~223~~ | DONE, and the STUB was blind to it | THE SINK'S CRS WAS
  ACCEPTED AND THROWN AWAY. tests/qgis_stub.py's _Sink took `crs` and
  stored nothing, so NO TEST HAD EVER CHECKED which projection a door
  stamps on its output - and a layer with the wrong one lands in the
  wrong part of the world while looking perfectly healthy. John's
  Burundi result drew north of Sweden.
  The sink now keeps crs and wkb, and two tests check that the layer
  carries the projection the run chose and that the coordinates are
  metres in it. Verified on a Burundi-shaped folder: EPSG:32736,
  coordinates 166,500 / 9,778,500 - correct for UTM 36S at 2 S.
  SO THE ENGINE WAS RIGHT. The remaining suspect is the QGIS PROJECT
  CRS: a layer in UTM 36S drawn in a project set to SWEREF 99 (EPSG
  3009, from John's Swedish work) is reprojected into a transverse
  Mercator far outside its zone of validity, which puts it nowhere
  sensible and can distort it out of existence when zoomed. The run
  now states the layer's EPSG in words and says where to check.
  THIS IS 221 AGAIN, SAME FILE, SAME WEEK: the simulator was not
  merely permissive, it was INCOMPLETE - it discarded the very
  argument whose misuse causes the most visible failure a GIS tool
  can have.

- 224 | OPEN, WATCHING | N_1000 READ 2000 in John's attribute
  table. It should be exactly k by construction. Could NOT be
  reproduced here on a folder shaped like his - f, m AND t, two
  countries, 1 km - where N_1000 comes out 1000.0 on every row. The
  screenshot is from a run whose log Claude has not seen, and the
  GeoPackage has held at least four differently-named tables across
  sessions. JOHN, LATER: "in the latter versions, it correctly
  assigns N - I will keep it under observation". So it is not
  reproducible on either machine now. LEFT OPEN DELIBERATELY rather
  than closed: an intermittent wrong N is worse than a repeatable
  one, and 225 was found in the SAME DATA, where cells holding TWO
  source pixels behave unlike their neighbours. If it returns, look
  there first. Do not change arithmetic on the strength of a
  screenshot.

- ~~225~~ | DONE | THE ANALYSIS GRID BEAT AGAINST THE SOURCE LATTICE
  AND STRIPED A CONTINENT. John mapped Dist_k at k=1000, 2000 and 4000
  and every map carried regular bands. Neither a data fault nor an
  arithmetic one - the RE-BINNING between them.
  WorldPop "1 km" is 30 ARC-SECONDS: at 2 S that is 927.7 m tall and
  927.1 m wide, NOT 1000. Binned onto a 1000 m grid the ratio is
  1.079, so most cells take ONE source pixel and every ~13th takes
  TWO. Those cells hold twice the population; Dist_k follows local
  density; the doubles band every 11.8 km - which is the stripe
  spacing in his images.
  WORST WHEN unit IS JUST ABOVE THE SOURCE SPACING, because the count
  alternates 1 and 2 - a 100% density swing. At ten times the source
  it is 10 or 11, a 10% swing, invisible. He landed on very nearly the
  worst possible value.
  AND CLAUDE'S OWN GUIDE TOLD HIM TO: "1000 m is a sensible
  continental start" - true for the 100 m rasters Claude built and
  tested against, actively harmful for his 1 km ones. Written from one
  dataset, exactly like the naming registry in 211. A REGISTRY, A
  DEFAULT AND A THRESHOLD ARE THE SAME MISTAKE WHEN THEY COME FROM ONE
  SAMPLE. The guide is corrected.
  _warn_aliasing() measures the source spacing from the points
  themselves at the data's own latitude, and names the density swing
  and the beat period in KILOMETRES - the thing he actually saw.
  Quiet at or below the source spacing, at exact multiples, and where
  the swing is under 25%.

- ~~226~~ | DONE | THE TOOLS ARE NAMED FOR THEIR OUTPUT NOW, NOT THEIR
  INPUT. John: "Machines 3 and 4 are too similar - I do not really
  follow - now we do all in machine 4, why do we need machine 3?".
  Both were called "from a folder of rasters" - the INPUT, identical -
  so the toolbox gave no way to choose between them.
    3. Raster Data Curation
    4. Spatial Demographic Analysis
  The k box in 3 defaults to BLANK, so its default behaviour really is
  curation; the neighbourhood run is a shortcut so a continental job
  need not write eleven million points to disk and read them back for
  Dist_k.
  AND THE ANSWER TO "why do we need 3": its output is an ORDINARY
  EQUIPOP POINT LAYER, so it feeds machines 1 and 2. Machine 4 gives
  four ratios; machine 3 gives WorldPop data the rest of the software.

- ~~227~~ | DONE | THE OUTPUT IS WRITTEN IN THE RASTERS' OWN
  PROJECTION NOW. John: "the crs is odd nonetheless - new map (with no
  history) suggests this placement (west of Norway) ... perhaps we
  should depict in the same format? I can reproject so it works, but
  this is a nuisance."
  AND CLAUDE'S EARLIER DIAGNOSIS WAS WRONG. He said "set the QGIS
  project CRS to the layer's" - John's screenshot then showed the
  project ALREADY at EPSG:32735, the layer's own, and it still drew
  west of Norway. The real cause: UTM SOUTHERN ZONES CARRY A FALSE
  NORTHING OF 10,000,000 m, so Burundi comes out at northing
  ~9,779,000, which on a European basemap reads as the far north, and
  the extent sits outside zone 35's valid range so everything
  distorts. Nothing about the project CRS could have fixed that.
  The analysis still runs in METRES - k is people and a radius is a
  distance - but the OUTPUT need not, and now defaults to the CRS the
  rasters were in. Box 3b/2e overrides it for anyone who wants metres.
  EastWest/NorthSouth stay as the ANALYSIS coordinates; only the
  geometry moves.
  LESSON: Claude gave confident diagnostic advice from a plausible
  story and John's own screenshot refuted it. The false northing was
  discoverable from the numbers in hand - 9,778,500 is not a latitude
  anyone in Africa should see - and was not looked at.

- ~~228~~ | DONE | A MEASURE CAN BE EDITED IN ITS OWN TERMS. John: "we
  should allow for alterations of the measurement settings - please
  make it possible to accept or edit the measures (for instance the
  age settings)". The column-list boxes technically allowed it, but
  moving a boundary five years meant typing eleven column names -
  transcription, not editing.
  parse_spec() now reads a half of an index the way it is spoken:
    '0-4'      ages 0 to 4, whichever sexes the index uses
    'f:15-49'  women only
    '65-'      open ended
    'fm:20-39' both sexes, a closed range
  THE IRREGULAR BANDS STILL HOLD: 'f:15-44' stops at band 40 and does
  not reach into 45-49, because the selection works in band starts.
  Malformed input is refused by name and the refusal SHOWS THE FORM
  THAT WORKS. The outright column-list boxes remain underneath, for
  anything a range cannot express.

- ~~229~~ | DONE | EACH MEASURE CAN NOW BE ALTERED SEPARATELY, IN ONE
  RUN. John: "yes, they work BUT it also means I cannot run different
  demographic indicators at the same time, since restricting to women
  in fertile ages will not fly in the other measures". Exactly right,
  and it defeated the point of the tool - several indices in ONE
  traverse was the reason to build it, and the edit boxes forced you
  back to one at a time.
  HIS OWN SUGGESTED SOLUTION was the right one: the "creation options"
  widget from an unrelated QGIS tool - a Name/Value table. QGIS has
  it as QgsProcessingParameterMatrix and alg_counts.py already used
  it, so there was a working pattern to copy rather than invent.
  Box 2c is now a table: one row per index, with numerator and
  denominator ages. Blank cells and absent indices keep the measure's
  own definition. Verified: ageing index at '70-' and child-woman
  ratio at 'f:15-44' in the SAME run, each honoured, neither leaking
  into the other. A row naming an unticked index, an unknown index, a
  malformed range or a ragged table is refused by name.

- ~~230~~ | DONE | WIDE OR LONG. John: "I would assume we should have
  one column for the population, and possibly indicators of iso-code
  and treatment belonging - and not a wide dataset ... it would be
  good to have the option". to_long() gives lon, lat, iso3, cohort,
  population.
  OFFERED, NOT IMPOSED, and the reason is scale: 11.5 million points
  by 60 cohorts is 690 MILLION rows long, which is why the analysis
  runs on the wide table. Box 3c, wide by default.

- ~~231~~ | DONE | THE SIMULATOR LACKED parameterAsEnum. It had only
  the PLURAL parameterAsEnums, for allowMultiple, so a door using the
  ordinary single-choice reader failed under test while being correct
  in QGIS. THE SAME INCOMPLETENESS AS THE SINK'S CRS (223) and the
  bare-int sink (221) - three in one file in one week. THE STUB IS NOW
  THE MOST DANGEROUS FILE IN THE REPOSITORY: every door test is only
  as true as its imitation, and it has been wrong in both directions -
  too permissive, too incomplete, and unfaithful.

- 232 | OPEN, NEEDS THE LOG | TICKING "add all cohorts" GAVE NULLS.
  John, on machine 3 box 2c: "I get null values in all but one value
  containing field - and I don't see the point of this". His image
  shows one populated column NAMED AFTER A FULL RASTER FILENAME
  (bdi_f_00_2026_CN_1km_R2025A_UA_v1) and the rest NULL.
  THAT NAME IS THE CLUE AND IT DOES NOT MATCH THIS ENGINE: since 211
  the columns are labels like f_00_2026, and sum_cohorts collapses
  them to a single 'pop'. A full filename means either an older engine
  or - more likely - A REUSED GEOPACKAGE TABLE, whose schema is the
  union of every run ever written to it, with old columns surviving as
  NULL. He has written at least six differently-named tables into
  bingobango.gpkg across these sessions.
  ALSO UNEXPLAINED: his folder holds f, m AND t, so sum_cohorts should
  have been REFUSED outright by 212's double-count guard. It was not.
  NEXT STEP IS THE LOG for that specific run, and a write to a FRESH
  table name. Do not change the summing on the strength of a
  screenshot - 224 is still open for the same reason.

- ~~233~~ | DONE | CITATION.cff PARSED AS YAML AND WAS INVALID CFF.
  John added two conference presentations through the GitHub browser -
  the right way to do it, needing no tools - and the result was
  well-formed YAML that the CFF schema rejects in two places:
    type: presentation   NOT in the CFF 1.2.0 enum. 'slides' and
                         'conference-paper' are; 'presentation' is the
                         natural English word and is not.
    conference: "..."    conference is an ENTITY, like location and
                         institution, and cannot be a bare string.
  NEITHER SHOWS UP AS AN ERROR ANYWHERE. GitHub simply stops
  rendering the "Cite this repository" button and nobody notices until
  somebody tries to cite the software. Confirmed with cffconvert, the
  reference implementation, before and after.
  tests/test_citation.py now checks the SCHEMA and not just the
  syntax: the type enum and the entity-shaped fields are checked
  WITHOUT cffconvert, so a bare install is still protected, and the
  full validator runs when it is present. All three failure modes -
  bad type, string conference, hand-edited version - were
  reintroduced deliberately and all three were caught.
  THE SHAPE OF THIS IS FAMILIAR: a file that only fails SOMEWHERE
  ELSE, silently. Same family as the run manifest (208), the sink CRS
  (223) and the aliasing (225). If nothing in the repository reads a
  file, nothing in the repository defends it.

- ~~234~~ | DONE | A MODULE-LEVEL rasterio IMPORT MADE A CORRECT
  INSTALL LOOK BROKEN. John installed 1.41.1 into Stata's Python -
  successfully, as the traceback's own path shows - and the verify
  line returned an ImportError, because rasterfolder imported rasterio
  AT MODULE LEVEL and the verify line imports rasterfolder.
  raster.py, slope.py and latticejoin.py all defer it into the
  function that reads a file. rasterfolder did not; raster.py did not
  either, and that one predates this session. Both now defer.
  THE VERIFY LINE IN INSTALL.md WAS ALSO WRONG: it used rasterfolder
  precisely BECAUSE it is new, but that made it depend on an optional
  library. It now uses doors.demography, equally new and pure Python.
  AND THE TEST THAT PROVED THE FIX PROVED NOTHING AT FIRST. Claude's
  first hook used find_module, REMOVED IN PYTHON 3.12, so it hid
  nothing, rasterio imported normally, and the check reported success
  on a file that had not even been written. There is now a
  test_the_hiding_hook_really_hides guarding the other four, because a
  test harness that silently does nothing is worse than no test.
  FOUR FAILED EDITS BEFORE THE FIFTH LANDED, all from asserting on
  text Claude had not read: wrong indentation, wrong line numbers, an
  over-clever guard that tripped on an unrelated except clause, and an
  anchor string that did not exist. The file was read properly only
  after the fourth. READ THE LINES, THEN EDIT THEM.

- ~~235~~ | DONE | MACHINES 3 AND 4 ARE IN ARCGIS PRO. They had been
  written and left OUT of self.tools because the arcpy simulator could
  not exercise a DEFolder box or NumPyArrayToFeatureClass, so nothing
  had ever run them. The simulator now covers both, plus
  GPCoordinateSystem, arcpy.Exists and management.Delete, and
  tests/test_arcgis_continental.py EXECUTES both tools - 13 tests.
  MACHINE 4 HAD NO PRO TOOL AT ALL. Claude registered
  SpatialDemography before checking, and the class did not exist; only
  ContinentalRasters had ever been written. It exists now, on the same
  run_indices() the QGIS door calls.
  AND THE TWO DOORS HAD DRIFTED, which is the finding. The
  false-northing fix (227) went into the QGIS writer and was never
  carried to Pro, so machine 3 in Pro would have written METRIC
  coordinates - and a UTM southern zone carries a false northing of
  10,000,000 m, which lands the layer off the top of a European
  basemap. THAT IS EXACTLY THE FAILURE JOHN REPORTED IN QGIS, waiting
  to happen again in the other door. Both now share to_output_crs().
  The whole reason for the shared spine is that a rule in two places
  drifts; this was a rule that had escaped INTO the doors.
  Four faults found by executing: the fake arcpy must be installed
  BEFORE the .pyt loads; valueAsText is a read-only property and a
  dialog sets `value`; Claude's own Exists() assumed a state key that
  is not always created; and the machine 3 test omitted the weight box
  and was correctly refused by the tool.

- ~~236~~ | DONE | JOHN'S ARCGIS PRO INSTALL METHOD, and it is better
  than four sets of instructions Claude gave from documentation. Run
  in PRO'S OWN PYTHON WINDOW - no shell, so it cannot be the wrong
  interpreter:
      import sys, os, subprocess
      py  = os.path.join(sys.exec_prefix, "python.exe")
      env = dict(os.environ, PYTHONNOUSERSITE="1")
      subprocess.run([py, "-m", "pip", "install", ...], env=env)
  PYTHONNOUSERSITE="1" IS THE CRUCIAL PART: without it pip may install
  into %APPDATA%\Python, which PRO DOES NOT READ, so the install
  succeeds and Pro still cannot see the package. That was the
  hypothesis Claude could not act on and John simply solved.
  sys.exec_prefix finds the interpreter without anyone knowing the
  path. INSTALL.md now carries this as the Pro method and the
  shell-based instructions are gone.
  GENERAL LESSON: THE HOST'S OWN PYTHON WINDOW BEATS ANY EXTERNAL
  SHELL, because it cannot be the wrong interpreter - and choosing the
  wrong prompt caused every install failure in this project's history,
  in all three hosts.

- ~~237~~ | DONE | THE TWO DOORS HAD DRIFTED ON THREE OF FOUR TOOL
  NAMES. Pro still said "3. Continental run from a folder of rasters"
  long after QGIS was renamed, and machines 1 and 2 differed in their
  parenthetical. door_parity.py checked parameter NAMES but never
  LABELS, so nothing noticed. A NAME IN TWO PLACES DRIFTS EXACTLY LIKE
  A RULE IN TWO PLACES.
  doors/help.LABELS is now the one list; both doors are pinned against
  it by test_the_two_doors_call_every_tool_the_same_thing.
  AND FIXING IT REINTRODUCED BACKLOG 218 WITHIN THE HOUR. Claude made
  displayName() import the package - and displayName runs while QGIS
  BUILDS THE TOOLBOX, so the plugin would die at startup with equipop
  absent. The existing test passed only because NOTHING CALLS
  displayName. The label is written down in each door and pinned
  against the package instead, and a second test forbids any import in
  displayName.

- ~~238~~ | DONE | BOX 2c OPENS SHOWING THE TRUTH. John: "the design
  choices are hard - should be based on factual values, not user
  entered". The settings table was free text, so an index name and an
  age range both had to be typed from memory.
  It now opens PRE-FILLED, one row per index, with that index's OWN
  ages - '65-' / '0-14' for the ageing index, '0-4' / 'f:15-49' for
  the child-woman ratio. You edit a value that is already correct.
  test_the_table_opens_showing_the_REAL_measures proves every shown
  cell REPRODUCES the built-in definition, so the display cannot
  quietly disagree with what the tool computes.
  Two gaps surfaced: parse_spec could not read TWO ranges, which the
  dependency ratio's numerator needs ("0-14,65-"); and a table that is
  always populated must IGNORE rows for unticked indices rather than
  refuse them - it says so only when such a row was actually edited.
  PRO HAS THE SAME TABLE, from the same written-down rows, pinned
  across the two doors by reading the QGIS source rather than
  importing it.

- ~~239~~ | DONE | MACHINE 3 JOINS A POINT LAYER ONTO THE RASTER
  LATTICE. John: "facilitate for the integration of shapefiles - i.e.
  points can have values that can populate raster grids > merges to
  the generated points". The engine existed since 220 and had no door.
  Boxes 2e/2f/2g: a point layer, an optional field to SUM (blank
  counts the points), and a column name. The door reprojects the layer
  into the lattice's CRS - only the door knows what the layer was in -
  and the join is on the INTEGER LATTICE INDEX, never by distance, so
  a feature is either in a cell or it is not. Cells the layer never
  touched carry a real 0.0, the same rule the rasters follow.
  It needs the POINT TABLE, so box 1b must be empty; asking for it
  during a k-run is refused with that fix named. load_folder's points
  path now carries keep_index=True for this.
  TWO MORE SIMULATOR GAPS: QgsGeometry had no centroid() and no
  isEmpty(), both of which real PyQGIS has - so a door taking the
  centroid of an input feature, which is how a POLYGON layer would
  join, failed under test while being correct in QGIS. That file has
  now been wrong in this way five times.

- ~~237~~ | DONE v1.50.0 | equipop_test_data.dta HAS TWO
  MISLEADING VARIABLE NAMES. John, from the field: ValFloat is not
  float and should be; ValCount holds counts.
  The names teach the wrong thing. The showcase and the field pass
  both use ValFloat to demonstrate a CONTINUOUS measure - that is the
  whole point of Block 20, which was corrected in 1.40.5 because a
  continuous measure had been put through treat() - so a variable
  called ValFloat that is not stored as float undercuts the lesson
  every time somebody inspects the data.
  NOT URGENT AND NOT A CORRECTNESS FAULT: the arithmetic reads the
  values, not the storage type. Do it with the next dataset
  regeneration rather than on its own, because the file is a fixture
  and touching it invalidates pinned EXPECT numbers in
  equipop_test_pass.do - check those in the same pass.
  THE STAKES ROSE BEFORE IT WAS DONE. The file is now published: it
  reaches every SSC user who types `ssc install equipop, all`, beside
  the paper, and it is the first thing a reader inspects. It is also
  the file C. F. Baum renamed, which is how it came back into view.
  DONE v1.50.0, and the regeneration was PROVED LOSSLESS BEFORE A
  PUBLISHED FIXTURE WAS TOUCHED - which is the only reason it was safe
  to do at all. ValFloat was declared Stata `double` (type 'd'). All
  9,166 of its present values are whole numbers, the largest is
  23,254, and float32 holds integers exactly to 16,777,216, so the
  round trip is exact and NOT ONE PINNED NUMBER MOVED. The showcase's
  `Nv 167.30 | Mean 1815.23 | Med 1248.10 | Gini .5806` still stands.
  tools/make_test_data.py refuses to run if either of those two facts
  stops being true.
  AND ALL NINE VARIABLES HAD EMPTY LABELS, found while doing it. In
  Stata the label is where meaning lives, so with none the NAME has to
  carry it - which is how a name that lies does real damage. Labelling
  them is a better cure for "misleading" than renaming: a rename would
  break equipop_showcase.do, equipop_test_pass.do, the paper's
  variable list and every student's notes, for a fault this item's own
  text calls minor. ValCount's label says what it is NOT - "a count,
  0-98 - not a 0/1 marker and not a magnitude" - because the
  ValFloat/ValCount pair is the confusion the item was raised about,
  and block 20 of the field pass was INVALID FOR A RELEASE because of
  exactly that mix-up (1.40.5).
  THE NAMES AND THE VALUES ARE UNTOUCHED, AND ONE QUESTION IS LEFT FOR
  JOHN. ValFloat exists to demonstrate a CONTINUOUS measure - that is
  the whole point of block 20 - and every value in it is a whole
  number. Genuinely fractional values would teach the lesson better.
  They would also want `double` storage to be worth having, which is
  the OPPOSITE of what John asked for here, and they would change the
  one pinned EXPECT line and diverge from the copy now hosted on SSC.
  So: storage fixed as instructed, pedagogy recorded, his ruling.
  Measured for whoever picks it up: ValFloat has 9,166 present values,
  1,726 missing by design, 3,527 distinct, range 0-23,254, and
  test_dist_monotone.py uses ValCount rather than ValFloat, so the
  Python suite pins nothing that fractional values would move.

- ~~238~~ | DONE | A REFUSAL NAMED A CHARACTER THE USER NEVER TYPED.
  External review of 1.43: 'fm:0-14,65-' was refused. Correct, and the
  cause is one character. parse_spec re-parses each half of a comma
  range by REBUILDING the sex prefix, and it joined the sexes with
  '/', producing 'f/m:0-14'. '/' is not a sex, so the message said
  "'/' is not a sex" about an input containing no slash.
  A comma range therefore worked WITHOUT a sex and failed WITH one -
  which is why nothing caught it: the dependency ratio's own default
  needs no sex prefix.
  A test now asserts the SHAPE of the fault, not only the instance: a
  refusal must never quote a character absent from the input, because
  that sends the reader hunting for a typo they did not make.
  AND THE TEMPLATE CLAUDE GAVE JOHN WAS WRONG. MEASURES_TEMPLATE.md
  said to write '0-14 plus 65-'. That syntax was never supported; the
  comma form always was. Corrected, with a note saying so - the
  document was written from intention rather than from the code.

- ~~239~~ | DONE, WAS A RELEASE BLOCKER | RASTERS IN DIFFERENT
  COORDINATE SYSTEMS WERE MERGED SILENTLY. Found by the external
  review of 1.43, reproduced here, and WORSE THAN REPORTED.
  The lattice check compared pixel size and origin. Both are PURE
  NUMBERS and say nothing about which world those numbers describe.
  `ref` even STORED the first raster's crs and never compared it.
  30.0 in EPSG:4326 is a longitude in Burundi; 30.0 in EPSG:3857 is
  thirty METRES from Greenwich. About 3,300 km apart, stacked into one
  cell, without a word.
  WORSE THAN REPORTED: the manifest then reported ONE crs - the first
  raster's - so the run's own provenance record HID the mixture. A
  reader had no way to discover it afterwards.
  AND THE EXISTING OVERLAP GUARD MADE IT LOOK LIKE SOMETHING ELSE.
  With the same label on both files it fired and complained about
  labels overlapping "on the same ground" - which is precisely the
  confusion, stated as a fact. With different labels nothing fired at
  all.
  Now refused, naming BOTH files and BOTH systems and saying what to
  do. The check runs BEFORE the lattice check on purpose: pixel size
  is the symptom and the coordinate system is the cause, and a user
  told only about pixel size will resample and make it worse.
  latticejoin has the same exposure one level up - a coordinate is a
  pair of numbers and carries no world with it - and cannot detect it,
  so lattice_of() reports its CRS for the caller to check and a test
  records what metres-against-degrees actually does.
  CLAUDE PREDICTED THAT WOULD COLLAPSE EVERYTHING INTO ONE CELL. It
  does not: it gives lattice indices in the hundreds of millions and
  longitudes off the planet, which is the LOUDER failure and the
  better one. The prediction was wrong and the test records the
  observed behaviour, not the guess.

- 240 | HALF DONE, engine + runner | MACHINE 5: FETCHING. Built to
  John's ruling and the standing rule in HANDOVER 13 section 3c -
  download into a folder, write a MANIFEST, and STOP. A test asserts
  the module never imports the engine, because the moment it does the
  rule is broken and reproducibility goes with it.
  THE PUBLISHED WORLDPOP DOCS ARE STALE AND BUILDING FROM THEM WOULD
  HAVE FAILED ON JOHN'S MACHINE. The 2022 pages list FOUR projects;
  the live API returns EIGHTEEN, and age_structures - the one this
  project needs - is not in the docs at all. The docs show
  ftp://ftp.worldpop.org.uk download URLs; the live API returns
  https://data.worldpop.org, and JOHN'S FTP IS BLOCKED. Both were
  caught only because he pasted two real responses, which are now
  committed as fixtures and are what the tests run against.
  PROVENANCE COMES FROM THE PROVIDER: the API returns doi, citation
  and licence per record, so the manifest states what WorldPop says
  rather than what EquiPop assumed.
  REFUSES TO OVERWRITE, and distinguishes two cases: a file already
  present whose checksum MATCHES is reused and reported; one whose
  checksum DIFFERS stops the run and is named, because whatever was
  computed from it was computed from THAT file.
  verify_folder() re-checks a folder against its manifest, which is
  the point of recording checksums - a year later it answers "is this
  the same data the paper used" without trusting a filename.
  CLAUDE CANNOT TEST THE DOWNLOAD LEG. Every WorldPop host is 403 from
  the sandbox - hub, data and www, all verified. So the transport is
  two small functions, everything else is tested with John's captured
  JSON, and the runner ASKS FIRST: it lists what it would fetch and
  stops unless --go is passed.
  AND CLAUDE'S OWN STAND-IN WAS TOO LOOSE AT FIRST: it matched URLs by
  fragment and ignored ?iso3=, so a request for a nonexistent country
  returned Burundi's records and a correct refusal looked like a bug.
  Same fault as the QGIS simulator accepting a bare int for a WKB type
  (221) - a stand-in looser than the real thing certifies the wrong
  behaviour.
  REMAINING: the QGIS door (John: QGIS first, Pro later), and the
  first real fetch, which only John can run.

- ~~241~~ | DONE | A RUNNER WAS SHIPPED WITHOUT THE MODULE IT DRIVES.
  run_fetch.py was delivered importing equipop.doors.fetching, which
  existed in the working tree and in NO WHEEL - 1.43.1 was built
  before it. John's first command was ModuleNotFoundError.
  "It works in my tree" IS NOT SHIPPING. The standing delivery rule
  (HANDOVER 13 section 3b) says four artefacts every session and it
  was followed - but the artefacts were built BEFORE the new module,
  and nothing checked that the loose files handed over alongside them
  could actually run against what was built.
  test_every_module_a_shipped_runner_imports_is_in_the_wheel now walks
  every top-level run_*.py, extracts its equipop imports, and checks
  the package provides each one. Verified by hiding fetching.py, which
  makes it fail, and restoring it, which makes it pass.
  AND THE TEST ITSELF FAILED FIRST, on ROOT.glob - ROOT is a str in
  test_packaging.py, not a Path. Claude assumed the type instead of
  reading the file. Fourth time this session that an edit was written
  against unread text.

- ~~242~~ | DONE | A CATEGORY LIST OFFERED A CHOICE THAT CANNOT BE
  MADE. John ran `--project pop` and the refusal correctly listed 17
  categories - constrained against unconstrained, 100 m against 1 km,
  three release generations - which is exactly right, because they are
  DIFFERENT DATASETS and picking one silently would have been the
  wrong kindness.
  But the first line was BLANK: a catalogue entry whose alias is empty
  and whose name is a bare DOI stub, WP00643. It cannot be passed to
  --category, so listing it is worse than a shorter list. Entries
  without a usable alias are now dropped.
  WORTH REMEMBERING FOR OTHER PROVIDERS: a public catalogue contains
  rows that are not offers. The adapter's job is to present only what
  the user can act on.

- ~~243~~ | DONE | THE TOOL CONTRADICTED ITSELF IN TWO CONSECUTIVE
  LINES. A --go run printed "NOTHING HAS BEEN DOWNLOADED. Pass this
  plan to run_fetch..." and then downloaded on the next line, because
  plan_fetch said it unconditionally and the runner called plan then
  run. Visible in John's own output.
  Harmless to the data and corrosive to trust: a reader who sees a
  tool say something false about itself stops reading its output, and
  this project's tools say a great deal that matters - the aliasing
  warning, the Dist_k sentence, the field guide.
  plan_fetch now takes will_download and says "Downloading now"
  instead.

- ~~244~~ | DONE, IT WORKS END TO END | MACHINE 5 PROVEN ON REAL DATA.
  John fetched 60 age-sex rasters for Burundi 2026 and the SHA-256 of
  a fetched file matched his hand-downloaded copy EXACTLY:
  54c1f80d6de2c6c484db4d8a3f438fe3dc18a0f0a0e809e421096d4c0bfad111.
  Not "looks right" - the same bytes.
  THE VERIFIER WAS SEEN TO FIRE. He appended a byte to one file and
  --verify reported 59 unchanged, 1 CHANGED, naming it. A guard that
  has only ever said "fine" is not a guard.
  THE REUSE PATH WORKS: deleting one file and re-running gave "1
  downloaded, 59 already present" - recognised by checksum, not
  re-downloaded.
  CATEGORY NAMING IS REGULAR: G2_{CN|UC|MOS}_Age_{R25A|R24B}_{100m|1km}.
  A friendlier shorthand is possible later. NOTE THAT THE ALIAS IS
  MORE TRUSTWORTHY THAN THE NAME: G2_CN_Age_R25A_100m is described as
  "Individual countries" while G2_UC_Age_R24B_100m says
  "Unconstrained" - the CN prefix survived into R2025A but the word
  dropped out of the description. The manifest records both.
  AND THE YEAR FILTER MATTERS MORE THAN IT LOOKS: R2025A spans
  2015-2030, so without --year one country would have offered ~960
  files instead of 60.

- ~~245~~ | DONE | "HOW TO OPEN IN Q?" - a fair question with no good
  answer. A tiled run writes PARQUET TILES, which are TABLES, not a
  spatial format: QGIS reads them only through the GDAL Parquet driver
  and even then they carry no geometry, so a user must build points
  from columns by hand. The runner said "read it back with
  load_tiled(...)", which is advice for a programmer.
  run_raster_folder.py now takes --csv FILE and prints the three
  things QGIS asks for: X field, Y field, and THE CRS. The CRS line
  matters more than it looks - the coordinates are METRES in the
  working projection and a UTM southern zone carries a false northing
  of 10,000,000 m, so read as anything else the layer lands off the
  top of the world, which is exactly what happened to John's first
  machine 4 result (227).
  TWO OF CLAUDE'S OWN TEST ERRORS, both familiar: ROOT assumed to
  exist in a file that only defines FIX - THIRD time this session an
  edit was written against unread text - and exact float equality
  asserted on a CSV, where one row of 3,162 returns 5.7e-14 from 500
  after a round trip through text. The values were right and the test
  was wrong.

- ~~246~~ | DONE | MACHINE 5 HAS A QGIS DOOR, and it is the first
  tool in the toolbox that produces NO LAYER. That is the standing
  rule made visible: it writes a FOLDER, because a tool that both
  downloads and analyses makes every result taken through it
  unreproducible offline. A test forbids the module from referencing
  the engine or a FeatureSink at all.
  DOWNLOAD IS OFF BY DEFAULT. Run it once to see what would be
  fetched; tick the box to fetch. An empty dataset box LISTS the
  datasets rather than refusing - an empty box should be a question,
  not a dead end. A temporary output folder is refused for a real
  download, because it would be deleted and the manifest with it, and
  the manifest is what makes the download citable.
  FOUND BY EXECUTING IT: run_fetch bound its transport as a DEFAULT
  ARGUMENT, captured when the function is defined - so a test that
  believed it had replaced the network went to the REAL network and
  got a 403. The transport is now late-bound everywhere, which is
  also what a future provider adapter will need.

- ~~247~~ | DONE | GEOPACKAGE FROM THE COMMAND LINE, and QGIS already
  had it. John asked for a csv/GeoPackage choice in the doors - but
  machines 3 and 4 write to a QgsProcessingParameterFeatureSink, whose
  [...] button already offers GeoPackage, Shapefile, GeoJSON, CSV or a
  temporary layer, chosen per run; Pro's DEFeatureClass does the same.
  The gap was the RUNNER, which only wrote CSV. --gpkg added.
  THE REAL ADVANTAGE IS NOT FILE SIZE: a GeoPackage CARRIES ITS OWN
  CRS. A CSV is numbers, so QGIS must be TOLD the projection and can
  be told wrongly - and a UTM southern zone's false northing of
  10,000,000 m then puts the layer off the top of the world, which is
  what happened in 227. A GeoPackage cannot be misread that way.

- ~~248~~ | DONE | ASKING WHAT IS AVAILABLE WAS TREATED AS A FAILURE.
  Machine 5's box says "leave blank to list them". John left it blank,
  the list printed correctly - all 18 datasets - and then the tool
  RAISED, so QGIS painted the run red and reported "Execution failed
  after 0.29 seconds" after doing exactly what the label invited.
  A blank box is a QUESTION. Both the dataset and the version box now
  answer it and finish cleanly. The version listing also says WHY
  there is no default: they are different datasets - constrained or
  not, 100 m or 1 km, different releases - not different formats.

- ~~249~~ | DONE | THE VERSION WARNING GAVE ADVICE THAT CANNOT WORK,
  THREE TIMES. It always said "run: python -m pip install --upgrade
  equipop". That is useless when the PLUGIN is the newer half, which
  it normally is during development: a plugin installed from a zip is
  ahead of anything published, and PIP ONLY SEES PUBLISHED RELEASES.
  John followed it across 1.42, 1.43.2 and 1.44 - pip correctly
  fetched the newest release each time, which was never the one he
  had, and he reported it three times as "I don't seem to get a new
  version".
  CLAUDE'S FIRST FIX WAS ALSO WRONG, AND WRONG ON THE VERY CASE THAT
  PROMPTED IT. He made the message say "install the wheel" whenever
  the plugin was ahead, ASSUMING a newer plugin means an unpublished
  build - and asserted to John that "1.44.0 is not on PyPI" without
  checking. IT WAS. John said so, and PyPI confirmed it.
  JOHN'S ACTUAL PROBLEM WAS SIMPLER and visible in his own screenshot:
  he ran `python -m pip install equipop` WITHOUT --upgrade, and pip
  replied "Requirement already satisfied ... (1.43.4)". Plain pip
  install does nothing when any version is present.
  THE MESSAGE CANNOT KNOW WHAT IS PUBLISHED, so it now offers BOTH
  routes and names the real cause first: --upgrade for a published
  release, saying explicitly that plain install does nothing; the
  wheel for a local build; and a closing line for the case where pip
  says it is already up to date.
  THE LESSON IS THE ASSERTION, NOT THE MESSAGE. Checking PyPI takes
  one call and Claude had done exactly that check twice before in
  this same session.
  AND THE COMPARISON IS NUMERIC, NOT TEXTUAL. As strings "1.44.0" <
  "1.5.0", so a string compare would have given exactly the wrong
  advice at the next minor bump - a bug scheduled for a future date.

- ~~250~~ | DONE | A LIST OF CHOICES THE USER COULD NOT TYPE BACK.
  John left both boxes blank, was shown "bic Individual countries",
  typed exactly that, and was refused. Entirely reasonable: the line
  LOOKS like one string, and nothing said which half was the answer.
  His own fix, and the right one: NUMBER THEM. The listing now puts
  the alias in its own column and numbers every line, and resolve()
  accepts the NUMBER, the alias, or THE WHOLE LINE PASTED BACK -
  because pasting back what you were just shown is the most natural
  thing a user can do and it should not be an error.
  A number out of range says how many there are; an unknown name
  reprints the numbered list rather than a bare refusal.

- ~~251~~ | DONE | "CHECK THE ISO3 CODE AND THE YEAR" WHEN THE CODE
  WAS FINE. John's log: births/bic for BDI in 2001 refused with advice
  to check both, sending him hunting for a country that was correct.
  THE ANSWER WAS ALREADY IN HAND - the records for BDI had been
  fetched and their years discarded. Now the two cases are separated:
  a country with nothing at all is told the code should be the
  three-letter one; a country whose YEAR is wrong is shown THE YEARS
  IT DOES HAVE.
  THE PATTERN, worth remembering for every refusal in this project: if
  the code already knows the right answer, a refusal that only names
  the problem is a wasted trip.

- ~~252~~ | DONE | THE NUMBER WE ASKED FOR WAS SENT STRAIGHT TO THE
  PROVIDER. John typed 5, as invited, and got "Could not list the
  versions of '5': HTTP Error 500". The door listed that dataset's
  versions using the RAW BOX TEXT, so it requested /rest/data/5.
  plan_fetch resolves numbers - but only AFTER the door had already
  used the unresolved value. The door now resolves first.
  THE SHAPE: a convenience added in one layer (numbers) was not known
  to the layer above it, which had its own reason to use the value.
  Adding a friendly input format means finding EVERY place the value
  is consumed, not just the one that validates it.
  And box 1c stayed empty for John not because listing was broken but
  because the run DIED before reaching it - one fault presenting as
  two.

- ~~253~~ | DONE | A REFUSAL OFFERED A CHOICE FROM AN EMPTY LIST.
  dahi records carry no popyear, so the year filter removed
  everything and the message read "The years it does have: BDI:"
  followed by nothing. Now a product with no years says so and tells
  the user to CLEAR the year box; a mixed set says "no year recorded"
  beside the country it applies to.
  253 IS 251 UNDERSPECIFIED. That fix assumed a wrong year meant
  OTHER years existed. It did not check the case where there are
  none, so a good improvement produced a nonsensical message one day
  later.

- ~~254~~ | DONE, IN THE TREE, NOT RELEASED | A GLOBAL PRODUCT WAS
  BLAMED ON THE COUNTRY CODE. John picked version 5 of `pop` -
  G2_MOS_POP_R25A_1km, "Global mosaics" - asked for BDI, and was told
  "Check the ISO3 code - it is the three-letter one, such as BDI". His
  code was BDI. A global mosaic holds no single country and never
  will.
  THE CATALOGUE SAYS WHICH IS WHICH in plain words - "Global
  mosaics", "Whole Continent", "Individual countries" - and the code
  was not reading it. is_per_country() now does, and the refusal names
  the offending product, says why it can never work, and LISTS THE
  PER-COUNTRY VERSIONS. His two-step becomes one.
  THIRD TIME IN THREE DAYS a refusal has blamed the wrong thing: 251
  (the year, when the code was fine), 253 (the year box, when there
  were no years), and now the code when the product was global. THE
  PATTERN IS ALWAYS THE SAME - the information needed to give the
  right answer was already in hand and was not consulted.

- 255 | OPEN, WON'T FIX AS ASKED | "COULD WE LOOK FOR AVAILABILITY AT
  ALL SETTINGS AND NOT JUST THE FIRST?" John, after hitting a global
  product and then, one step later, an unavailable year.
  PARTLY IMPOSSIBLE: the checks are DEPENDENT, not parallel. The
  category list cannot be fetched until the dataset resolves; the
  years cannot be known until the country's records are fetched; and
  the records cannot be fetched from a global product at all. So
  "check everything at once" cannot be done in general.
  WHAT WAS DONE INSTEAD, and it covers his actual case: 254 removes
  the two-step by naming the per-country versions in the same
  refusal. Left open in case a second instance appears with a
  different shape - if it does, the answer is probably to report the
  independent checks together (dataset, category, country code) and
  leave the dependent ones sequential.

- ~~256~~ | DONE | THE FETCHING SPINE NO LONGER KNOWS WHAT A COUNTRY
  IS. plan_fetch took project, category, iso3 and year as fixed
  keyword arguments - WORLDPOP'S SHAPE, BAKED INTO THE MACHINE. GHSL
  is tiled globally and has no iso3; Overture has no year; HDX has
  neither. A rule shaped by one case and found when the second
  arrives is this project's most repeated mistake (211 the naming
  registry, 225 the cell-size default, 208 the manifest path), so this
  time it was loosened BEFORE the second adapter, on John's ruling.
  An adapter now declares FIELDS and implements plan(choices) ->
  (entries, described). The spine does only what is common: refuse an
  unknown provider, check declared fields are present, build the plan,
  say what would happen. A test asserts the words iso3, popyear and
  country DO NOT APPEAR in plan_fetch at all.
  THE PROOF IS A FAKE SECOND PROVIDER shaped nothing like WorldPop -
  releases and tiles, no countries, no years - and it immediately
  found a leak the refactor had missed: run_fetch still named
  plan["iso3"] and plan["year"] when writing the manifest, so any
  other provider raised KeyError. The manifest now records whatever
  the adapter described.
  A FIELD MAY CARRY ITS OWN WORDING. Moving the required-field check
  up a layer replaced "Which country? Give one or more ISO3 codes,
  such as BDI" with "worldpop needs iso3 - Countries (ISO3)" - correct
  and worse. Generalising a check must not cost the user the better
  message.
  DELIBERATELY NOT DONE: the QGIS door still has five fixed boxes
  matching WorldPop. Designing generic boxes for providers that do not
  exist yet would be the SAME MISTAKE IN REVERSE - a shape invented
  from imagination rather than from a second real case. It waits for
  adapter number two.

- 257 | OPEN, PAUSED BY JOHN, SESSION 12 | THE NEXT FETCH ADAPTERS.
  Written up in PROVIDERS_PLAN.md rather than left in a conversation,
  because the WorldPop docs turned out FOUR YEARS STALE and building
  from a half-remembered web page is how that happens.
  PAUSED, session 12: "let us wait with the providers for now". Four
  providers work; a fifth is capability, not a gap. Nothing here is
  blocked on anything - it resumes when John says so.
  TWO FINDINGS WORTH KNOWING BEFORE ANY CODE:
  (a) MOST GHSL PRODUCTS ARE MOLLWEIDE (ESRI:54009) AND WORLDPOP IS
  WGS84. Put both in one folder and the loader REFUSES them - which is
  BACKLOG 239 working exactly as intended. But POP, BUILT-S and
  BUILT-V are ALSO published in WGS84 at 3 and 30 arc-seconds, the
  same grid family as WorldPop, so the two CAN share a folder if the
  WGS84 variants are chosen. Whether the origins actually align is a
  measurement nobody has made. The adapter should default to WGS84 and
  say why.
  (b) GEOFABRIK PUBLISHES .md5 SIDECARS, so a fetch can be verified
  against WHAT THE PUBLISHER SAYS THE FILE IS, not merely against what
  we happened to receive. That is stronger provenance than anything
  else on the list, including WorldPop, and the adapter should use it.
  GHSL HAS NO API - a predictable HTTPS tree under jeodpp.jrc.ec.
  europa.eu and citations only on the web page, so the DOIs must be
  written INTO the adapter and can therefore go stale.
  GEOFABRIK IS TWO JOBS, NOT ONE: EquiPop cannot read .osm.pbf. Try
  the .gpkg.zip format plus the lattice join before adding pyrosm or
  pyosmium as a dependency.
  ~~STILL NEEDED: one directory listing from the GHSL tree, one HDX
  package_search response, and one feature from Geofabrik's
  index-v1-nogeom.json (the file is ~1 MB, which is why pasting it
  whole failed).~~
  ALL THREE WERE OBTAINED AND THIS LINE WENT STALE. GHSL's URL was
  confirmed against a real directory read on 2026-09-02 and the date
  is in ghsl.json's `confirmed_against`; HDX was confirmed against a
  real package_search response for Sweden (261); Geofabrik's index
  was confirmed from the real file John supplied (259, 262). The line
  was written before 260-262 landed and nobody struck it.
  IT THEN COST A ROUND TRIP: session 12 read it and asked John for
  three samples he had already supplied. A STALE "STILL NEEDED" IS
  WORSE THAN NO LIST - it reads as current, and the reader has no way
  to tell. Same shape as PROVIDER_NAMES = ["worldpop"] (263) and the
  "what next" list that stops at 164: a note written once and true
  once.
  WHAT IS ACTUALLY UNKNOWN is different in kind and none of it is a
  sample anyone can send: whether EOG nightlights requires a free
  account (unconfirmed, and a login is what John wanted to avoid),
  Copernicus requires registration, and Overture is not a file
  download at all - global GeoParquet queried over the network, with
  no artefact to checksum unless one is defined. That last is a
  design decision and belongs last.

- ~~258~~ | DONE | SEPARATE THE SITE-SPECIFIC
  KNOWLEDGE FROM THE TOOL. John: "relying on http is tough of course
  if they change the content structure all will need to be
  reinstalled ... what if the site specific instructions could be
  separated from the tool - so that if the user is running an old tool
  and it doesn't work - just retrieving site specific instructions
  from GIT would be enough - is that a dumb thought?"
  NOT DUMB. IT IS THE PATTERN, and this project already has the
  evidence: BACKLOG 211, the WorldPop naming registry, was written
  from four sample files and failed on all 120 of John's real ones. It
  was DATA baked into CODE, so fixing it needed a release, a build, a
  PyPI upload and three host installs. As an external registry it
  would have been a one-line edit pushed to GitHub, and John's next
  run would have worked.
  THE SEAM IS CLEAN. The MECHANISM is stable - fetch, checksum,
  manifest, refuse to overwrite. The SITE KNOWLEDGE is volatile - URL
  patterns, field names, which products exist, naming conventions.
  Volatile things belong in data, stable things in code.
  THREE CONDITIONS, and the first is not negotiable:
  (a) DATA ONLY, NEVER CODE. URL templates and field declarations, no
      Python, no eval. A tool that people install into QGIS must not
      execute instructions fetched over the network.
  (b) A BUNDLED COPY IS THE FALLBACK. The remote is an UPDATE, not a
      dependency. Offline, the tool works with what it shipped with.
  (c) THE MANIFEST RECORDS WHICH REGISTRY VERSION WAS USED. Otherwise
      a fetch becomes unreproducible in a NEW way - "which rules were
      in force?" - and reproducibility is the whole reason machine 5
      exists.
  Pin to a tag or record the commit, never a bare branch.

- 259 | OPEN | THE GEOFABRIK INDEX, CONFIRMED FROM THE REAL FILE (John
  supplied all 700 pages). properties: id, parent, name, urls,
  iso3166-1:alpha2, iso3166-2. urls keys: pbf, shp, pbf-internal,
  history, taginfo, updates.
  TWO CORRECTIONS TO PROVIDERS_PLAN.md, WRITTEN ONE DAY EARLIER FROM A
  SEARCH SNIPPET:
  (a) THERE IS NO gpkg. The snippet listed .gpkg.zip among Geofabrik's
      formats; the actual index offers pbf and shp only. The
      no-new-dependency route is therefore the SHAPEFILE ZIP, which
      QGIS and GDAL read natively - the route survives, for a
      different reason than the one written down. DOCUMENTATION
      DESCRIBED THE DATA AND THE DATA DISAGREED, for the second time
      in this workstream after WorldPop's four-year-stale pages.
  (b) iso3166-1:alpha2 CONTAINS "NA" - NAMIBIA. pandas reads that as
      NaN by default, so Namibia vanishes silently from any country
      list. Demonstrated: read_csv turns ['SE','NA','NO'] into
      ['SE', nan, 'NO']. Use keep_default_na=False, or do not use
      pandas for this file. A country disappearing without a word is
      exactly this project's signature fault.

- ~~260~~ | DONE | THE PROVIDER REGISTRY, AND GHSL AS ITS FIRST
  ENTRY. equipop/providers/*.json, loaded by doors/registry.py.
  GHSL IS NOW ENTIRELY DATA - no code at all. The URL, the DOI, the
  citation and the licence obligations all come from a JSON file that
  can be corrected and pushed without a release. Verified against the
  real server: GHS_POP_GLOBE_R2023A/GHS_POP_E2020_GLOBE_R2023A_4326_
  30ss/V1-0/..._V1_0.zip, built from the definition and matching
  character for character.
  RULE ONE IS ENFORCED, NOT DOCUMENTED. _check_safe() refuses any
  definition containing __, import, eval, exec, lambda, os. or
  subprocess, and a test runs it over every BUNDLED file - the rule
  applies to what SHIPS, not only to what is loaded. EquiPop is
  installed inside QGIS and ArcGIS Pro; a tool that executed
  instructions fetched over the network would be a remote code
  execution hole in a research instrument.
  RULE TWO: definitions live INSIDE the package, so they travel in the
  wheel. Claude first put them beside it, which would have shipped
  them to nobody - the same fault as run_fetch.py importing a module
  no wheel contained (241).
  RULE THREE: registry_version reaches the manifest, both at the top
  and per file. Without it a fetch is unreproducible in a NEW way -
  which rules were in force when this ran?
  A BROKEN DEFINITION IS SKIPPED AND NAMED, not fatal, for the same
  reason the QGIS plugin loads when equipop is absent.
  THREE FAULTS FOUND BY RUNNING IT, all of them the generalisation
  overruling the thing it generalised:
    the spine checked `required` BEFORE the adapter applied its own
      defaults, so a definition that supplied one was refused for not
      supplying it;
    resolve() read "2020" as "the 2020th option" - the numbering
      convenience from 250 colliding with a field whose choices ARE
      numbers. A value that IS a choice now wins;
    a QGIS test patched `projects` onto EVERY provider, and a
      TemplateProvider has no catalogue to list. The test assumed
      every provider looks like the first one, which is exactly what
      256 was done to remove.

- ~~261~~ | DONE | HDX IS THE THIRD PROVIDER, and its real response
  broke an assumption written down one day earlier.
  A CODE adapter, not a registry entry: a search must be issued and a
  dataset chosen, so it cannot be NAMED from the user's choices. That
  is the split the registry was designed around and it held.
  EVERY RESOURCE CARRIES AN MD5 IN `hash`. Like Geofabrik, a download
  can be verified against WHAT THE PUBLISHER SAYS THE FILE IS. Two of
  three providers now offer this; WorldPop offers nothing of the kind.
  THE ASSUMPTION IT BROKE: PROVIDERS_PLAN.md said the manifest would
  record may_redistribute and share_alike per source. FOR HDX THAT IS
  OFTEN UNKNOWABLE - the IATI dataset returns license_id "hdx-other",
  title "Other", and PROSE pointing at a web page. Those fields are
  now None when unresolved, the prose is carried verbatim, and the run
  SAYS SO before fetching. Guessing "probably CC-BY" would have been
  worse than admitting ignorance, and would have been exactly the kind
  of plausible wrong answer this project keeps finding.
  A KNOWN licence IS resolved: cc-by, cc-by-sa, odc-odbl and the rest
  map to obligations; anything else is left undecided on purpose.
  ONE DATASET MAY HOLD SEVERAL FILES, unlike GHSL where one set of
  choices names one file - which is why the entries list, not a single
  entry, is the unit.

- ~~262~~ | DONE | GEOFABRIK IS THE FOURTH PROVIDER. Structure
  confirmed against the real index-v1.json - all 700 pages, supplied
  by John as a PDF after two plain pastes arrived empty.
  ANY LEVEL IS DOWNLOADABLE, which is what John asked for: an empty
  region box lists the continents, and a continent, a country or a
  sub-region can each be named directly. A near miss suggests the real
  one - 'swed' offers 'sweden'.
  ODbL, AND IT IS THE FIRST SOURCE WITH SHARE-ALIKE. Recorded in the
  manifest AND said out loud before every fetch, because EquiPop
  exists to produce published derived surfaces and a share-alike
  obligation may travel to them.
  THE .md5 SIDECAR is recorded, so a download can be checked against
  what GEOFABRIK says the file is. Three of four providers now offer a
  publisher checksum; WorldPop still offers none.
  NO gpkg, contradicting a search snippet - the real index has pbf and
  shp only, so the no-new-dependency route is the SHAPEFILE ZIP.
  NAMIBIA IS PINNED BY A TEST. Its iso3166-1:alpha2 is "NA", which
  pandas turns into NaN by default; a country vanishing from a country
  list without a word is this project's signature fault.
  AND A THIRD TIME THE GENERALISATION OVERRULED THE THING IT
  GENERALISED: the spine's required-field check fired before the
  adapter could LIST the continents, so an empty box got a generic
  message instead of the picker. Fields may now declare
  lists_when_empty.

- ~~263~~ | DONE | THE QGIS DOOR OFFERED ONE PROVIDER OUT OF FOUR.
  John installed 1.44.5 and reported "still only worldpop". He had
  missed nothing: PROVIDER_NAMES was ["worldpop"], written down in the
  door when there was one provider and never updated.
  THE SAME FAULT AS THE NAMING REGISTRY (211) - a list written from
  what existed at the time - except THIS ONE WAS CREATED KNOWINGLY, to
  keep the package out of initAlgorithm (218), and then forgotten.
  Hard-coding for a good reason still needs a test that notices when
  the world moves; there is one now, and it checks both directions.
  AND ADDING THE NAMES ALONE WOULD HAVE GIVEN HIM A BROKEN DIALOG.
  Boxes called Dataset, Version, Countries and Year are WORLDPOP'S
  VOCABULARY: GHSL asks for product, release, epoch, crs, res;
  Geofabrik for a region; HDX for a country group and a dataset.
  So the four boxes became ONE SETTINGS TABLE, driven by the FIELDS
  every adapter already declares. Leave it empty and the tool lists
  exactly what the chosen provider asks for, with labels and whether
  each is required - asking is not failing (248). A test asserts the
  door contains no provider's vocabulary at all.
  THIS IS THE DESIGN THAT WAS DELIBERATELY DEFERRED IN 256: generic
  boxes were not invented for imagined providers, they were written
  once four real ones existed and their needs were known. That was the
  right call - the shape the table took could not have been guessed
  from WorldPop alone.
  Verified by driving GHSL and Geofabrik through the same door,
  including the ODbL share-alike warning reaching the user.

- ~~264~~ | DONE | "LEAVE IT EMPTY TO SEE THE OPTIONS" COULD NEVER BE
  ACCEPTED. John left the settings table empty on ALL FOUR providers
  and got the same refusal every time: "Box 1b has 1 cells, which is
  not a whole number of rows of two".
  AN UNTOUCHED QGIS MATRIX IS [''], NOT []. A list holding one empty
  string - and a None parameter comes back the same way. The evenness
  check therefore saw ONE cell and refused before the listing could
  run, so the invitation printed on the box was impossible to take up.
  THE SIMULATOR RETURNED [] AND SO EVERY TEST PASSED. THIRD TIME
  tests/qgis_stub.py HAS BEEN MORE FORGIVING THAN QGIS - 221 accepted
  a bare int for a WKB type, 223 accepted and DISCARDED the sink's
  CRS, 231 lacked parameterAsEnum entirely. Every one of them let a
  door ship broken with a green suite.
  THE STUB IS STILL THE MOST DANGEROUS FILE IN THIS REPOSITORY. Every
  door test is only as true as its imitation, and the imitation has
  now been wrong four times in four different ways.
  Fixed in both places: the stub returns [''] as QGIS does, and the
  door drops trailing blanks and treats an all-blank table as no
  table. Tested with [''], [], None, ['',''] and ['  '], across all
  four providers, plus a real table with a trailing blank row - and a
  genuinely ragged table is still refused, because the check had to
  survive being made tolerant. Reverting the fix fails eight of them.

- ~~265~~ | DONE | AN UNTOUCHED MATRIX CELL IS PyQGIS's NULL, AND
  str(NULL) IS THE FOUR CHARACTERS 'NULL'. Not an empty string, not
  None. John reported the same refusal TWICE, on all four providers:
  "Box 1b has 1 cells". The first fix handled "" and None and missed
  this, so his second report was the same error against a release that
  was supposed to have fixed it.
  THE SIMULATOR RETURNED "" AND THEN [] AND WAS WRONG BOTH TIMES.
  FIFTH FIDELITY FAILURE in tests/qgis_stub.py - after a bare int
  accepted for a WKB type (221), the sink's CRS accepted and DISCARDED
  (223), parameterAsEnum missing entirely (231), and [] for an empty
  matrix (264). Every one let a door ship broken with a green suite.
  MAKING THE SIMULATOR HONEST FOUND TWO MORE LIVE FAULTS IMMEDIATELY.
  Machine 4's index table and machine 1's reference and treatment
  tables read a matrix their own way and each handled "" and missed
  NULL - so all THREE tools would have refused an untouched table on
  John's machine, in three different messages, and only machine 5's
  had ever been tried.
  ONE READER NOW, base.matrix_cells(), used by all three. The fault
  appeared three times independently because the reading was written
  three times.
  AND THE SHARED HELPER BROKE MACHINE 4 ON ITS FIRST OUTING: it
  dropped trailing blanks, which suits a TWO-column table and
  destroys a THREE-column one, where "Ageing index / 70- / blank" is a
  complete row. Length is preserved now and each door checks its own
  width. FOURTH TIME a generalisation has overruled the thing it
  generalised - 256 the defaults, 250 the numbering, 262 the listing,
  and now this.

- ~~266~~ | DONE | THE LISTING GAVE FIELD NAMES AND NO VALUES. John:
  "how should the user know what to enter - I have field names
  (possibly) but I don't have the alternatives."
  AND IT WAS WORSE THAN INCOMPLETE. Three GHSL fields - release, crs,
  res - have DEFAULTS and were announced as "(required)". That is not
  a gap, it is a FALSE STATEMENT, and it sent him hunting for values
  he could have omitted. The definition knew both the defaults and the
  allowed values and printed neither.
  The listing now shows every allowed value, what each MEANS where the
  definition explains it - "4326 WGS84 degrees, the same family as
  WorldPop" and "54009 will NOT mix" - which of the fields have
  defaults and can be left out, and a COPYABLE EXAMPLE holding only
  what must be filled, because an optional field in a worked example
  reads as compulsory.
  WHAT WAS ASKED FOR AND CANNOT BE DONE, said plainly rather than
  quietly dropped: a Processing matrix's default is fixed when the
  DIALOG IS BUILT, before a provider is chosen, so the table cannot
  pre-populate; and its widget is plain free text, so there are no
  per-cell dropdowns. The listing has to carry the information
  instead.
  AND THE SETTINGS TABLE HAD QUIETLY BROKEN WORLDPOP'S OWN LISTING.
  "Leave the dataset blank to see the list" was unreachable, because
  the spine's required-check refused before the adapter could list.
  project and category are marked lists_when_empty now. A feature
  removed by accident during a redesign, noticed only because someone
  asked a different question about the same screen.

- ~~267~~ | DONE | HANDOVER 14 WRITTEN. HANDOVER 13 ended at 1.41.0
  and the tree is at 1.44.9 - eighteen releases, 57 backlog items
  closed, 12 open. Machines 3, 4 and 5, the provider registry and four
  providers all arrived after 13 was written, so a fresh session
  reading 13 would have been badly misled about what exists.
  ITS CENTRE IS THE FOUR PATTERNS THAT REPEATED, because they cost
  more than any single defect and EVERY ONE RECURRED AFTER BEING
  WRITTEN DOWN:
    the simulator kinder than QGIS - FIVE times
    a generalisation overruling what it generalised - FOUR times
    a refusal blaming the wrong thing - THREE times
    a rule written from one sample - THREE times
  Writing them down is demonstrably not sufficient. Each needs a test
  that fires, and 14 says so rather than repeating the advice that
  already failed.
  ALSO RECORDED: handovers 9 and 10 have never been in the tree. 13
  flagged it and they are still absent, so two sessions exist only in
  downloads if at all.

- ~~268~~ | DONE | FOUR FAILED ATTEMPTS IN ONE SITTING, FOUR
  SEPARATE FAULTS, ALL CLAUDE'S. John: "the messages are not fully
  helpful and somewhat confusing ... it is unclear if I should enter
  'product Which layer (required)' as Setting. And see year - first
  asked for then rejecting it later."
  (a) THE KEY AND ITS LABEL DISAGREED. The field was named `epoch` and
  LABELLED "Year", and its refusal said "Which year?" - the label's
  word for a key that did not exist. He typed `year`, which was the
  only sensible move, and was refused. Renamed to `year` IN THE
  DEFINITION, one line of JSON and no code, which is exactly what the
  registry was built for. WorldPop already used `year`, so one word
  across providers beats matching JRC's own vocabulary.
  (b) 'Product' WAS REFUSED FOR A CAPITAL LETTER. A setting name is
  not data. Matched case-insensitively now.
  (c) '1' WAS REFUSED WITH NO HELP - and he typed it because options
  are NUMBERED everywhere else in this tool. Unknown settings now
  SUGGEST the nearest, matching on the label too, so "year" would have
  found "epoch" even before the rename.
  (d) THE LAYOUT LEANED ON ALIGNMENT. "product   Which layer
  (REQUIRED)" gave no clue where the Setting column ended - and QGIS's
  log COLLAPSES whitespace, so the two columns became one sentence.
  Names and values are QUOTED now, which survives any mangling, and a
  test asserts the listing still reads correctly with all whitespace
  collapsed.
  THE PATTERN: every one of these is the tool describing itself in
  words that do not match what it will accept. A message is part of
  the interface and must be tested against the shape the user
  actually sees, not the shape it has in the source.

- ~~269~~ | ENGINE DONE v1.45.0, DOORS DONE v1.47.6 | THE INVENTORY:
  WHAT IS IN A FOLDER.
  IT WAS MARKED DONE FOR TWO RELEASES WHILE REACHABLE FROM NOWHERE.
  No GUI, no runner, no Stata - only by writing Python, which the
  person this project is built for does not do. "DONE" meant the
  engine worked. It is the first of the five unreachable things found
  in session 12 and the reason tests/reachability.py now exists: the
  suite asked whether the thing worked and never whether anyone could
  get to it.
  v1.47.6 gives it TWO DOORS. "6. What is in this folder? (reads,
  changes nothing)" in QGIS and in Pro - numbered 6 because machine 5
  is fetching and this reads a folder already on disk. One row per
  file or layer, and the LATTICE COLUMN is the point: a folder
  holding more than one lattice says so loudly.
  THE TEST THAT MATTERS IS test_4. Three rasters, same CRS, same cell
  size, one offset by HALF A CELL - indistinguishable in any file
  listing, and merging them by index silently misaligns every value.
  BACKLOG 239 is the version of that which merged rasters 3,300 km
  apart.
  THREE SPARSE-SIMULATOR GAPS FOUND BUILDING IT, all real API the
  stub had never needed: QMetaType.Type.LongLong, the DETable
  datatype, QgsWkbTypes.NoGeometry. Every EquiPop output until now
  carried points, so a table with NO GEOMETRY had never been asked
  for. Same family as the polygon barrier of 1.29.3: a sparse
  simulator does not fail loudly, it narrows what a door may ask and
  the narrowing reads as a mistake in the door.
  AND make_help_xml.py's TOOL LIST WENT STALE A THIRD TIME - 294
  replaced two names with four one release ago, and a fifth tool made
  it wrong again at once. It reads Toolbox().tools now.
  CLAUDE WROTE _rows() FROM MEMORY of what an inventory ought to look
  like - nested layers, rec["path"], rec["pixel_x"] - when the
  package returns FLAT records with rec["file"] and a two-element
  rec["pixel_size"]. The engine was thirty lines away.
  ORIGINAL ENTRY: John's idea -
  save a short description with each download so a later merge can
  offer dropdowns instead of making the user hunt.
  TWO OBJECTS, AND ONLY ONE IS MACHINE 5'S. The MANIFEST records
  PROVENANCE and machine 5 writes it WITHOUT OPENING ANYTHING,
  because a fetcher downloads and stops. The INVENTORY records
  CONTENTS - layers, fields, CRS, geometry, extent, class values -
  which needs the files READ, so it belongs on the analysis side.
  Putting it in machine 5 would have broken the standing rule for
  convenience.
  THE LATTICE IS THE POINT. Files are grouped by grid identity, and
  the key is the CRS, the pixel size, and THE ORIGIN MODULO THE PIXEL
  SIZE - not the origin, because two rasters covering different areas
  of one grid are the same lattice. More than one lattice is said out
  loud, because merging across grids needs a decision and BACKLOG 239
  exists from one being made silently.
  CLASS VALUES COME FROM THE DATA, NOT FROM DOCUMENTATION. fclass and
  its kin are read from the user's own extract, so the grouping
  dropdown is right for Sweden and right for Burundi without a list
  written from a schema PDF - the fault that broke the WorldPop naming
  registry on all 120 of John's files (211). A column with more than
  60 distinct values is reported as an identifier rather than listed,
  so street names cannot bury fclass.
  IT READS THE CLASS COLUMN ONLY, never the geometry, so a country
  extract is inventoried without loading it.
  AN UNREADABLE FILE IS RECORDED WITH ITS ERROR, not skipped - and
  that is how Claude's own bug was found rather than losing two
  shapefiles silently: pyogrio returns `fields` as a NUMPY ARRAY, so
  `info.get("fields") or []` evaluates an array's truthiness and
  raises. Written from habit without reading what read_info returns.

- ~~270~~ | DONE | THE DROPDOWN SAID NOTHING. John: "the info in the
  dropbox looks like spelling errors". Quite so - worldpop, ghsl, hdx,
  geofabrik are internal keys, shown raw, saying nothing about what
  they hold. Labelled now, WITH THE LICENCE, because Geofabrik's
  share-alike obligation matters BEFORE the download and is the one
  thing that can follow a published result home.

- ~~271~~ | DONE | GEOFABRIK DEFAULTS TO SHAPEFILE, NOT pbf. John:
  "the file format when opening is very slow - 10 s just to open".
  GDAL builds a temporary index database the first time it opens a
  .osm.pbf, and pays it again on every open. THE FIX IS NOT TO
  OPTIMISE THE OPEN - it is not to use that format. The free
  shapefile zip is already split into thematic layers carrying
  fclass, opens in a second, and needs no new dependency: pyogrio,
  which geopandas already uses.
  DECIDED AGAINST pyrosm and pyosmium (new dependencies) and against
  osgeo (present in QGIS, ABSENT in Stata's Python and standalone).

- ~~272~~ | DONE, HIGH | GRID INDICES WERE ADDED TO THE POPULATION.
  External review of 1.44.10, with an exact reproduction. This is
  JOHN'S BACKLOG 232, which he reported weeks ago and Claude twice
  failed to reproduce - because he never combined sum_cohorts with
  keep_index, and the reproduction needs both.
  A 2x2 grid holding 10 people per cell returned [10, 11, 11, 12] -
  44 people instead of 40. On a continental grid an index DWARFS the
  population it corrupts.
  THE RULE WAS WRITTEN THREE TIMES as "everything except lon, lat,
  iso3". keep_index later added gx and gy, and one of the three was
  not updated. AN EXCLUSION LIST IS A PROMISE ABOUT EVERY COLUMN THAT
  WILL EVER EXIST, and it was broken by the next column added. One
  definition now, used three times.
  The sum also DROPPED gx and gy afterwards, so the sum option and the
  exact lattice join could not be used together - fixed as well.
  Pinned with and without indices, on a larger grid, and with two
  countries.

- ~~273~~ | DONE, HIGH | A RESULT THAT DEPENDED ON WHICH OTHER FILES
  WERE PRESENT. The selected year filtered the numerator and
  denominator, but the REFERENCE POPULATION summed the f_ and m_
  columns of EVERY year in the folder. Analysing 2020 changed once
  2030 had also been downloaded: measured here, mean Dist 34.60 m
  against 24.37 m - a 30% change in the neighbourhood - with the
  selected year's data identical. The review measured radii moving up
  to 55 m and the sex ratio by 0.073.
  THE YEAR WAS NEVER PASSED DOWN. run_indices knew it, used it to
  pick cohorts, and did not give it to the loader; run_folder and
  load_folder did not accept it at all - so machine 3's own door
  could not confine a year either. Wired through all three.
  The run now SAYS when it leaves columns out, because that is a
  decision the user must see.
  PERMANENT REGRESSION TEST, as the review asks: "adding an unrelated
  year leaves this year's output unchanged", for two indices. THIS IS
  THE ONLY KIND OF DEFECT THAT MAKES A PUBLISHED COMPARISON WRONG FOR
  A REASON NOBODY CAN SEE IN THE OUTPUT.
  AND CLAUDE ASSUMED A KEY NAME AGAIN while writing the test -
  INDICES entries have `code`, not `short`. Third time this session an
  edit was written against unread structure.

- ~~274~~ | DONE, HIGH | A FILENAME COLLISION ATTRIBUTED OLD BYTES TO
  A NEW SOURCE. Review finding 5, reproduced. Reuse matched on
  BASENAME ALONE: fetching productB/population.tif after productA's
  kept A's bytes on disk and wrote B's URL into the manifest. ONLY A
  WAS EVER DOWNLOADED, and the manifest said otherwise.
  Reuse now requires the RECORDED URL to match the requested one, and
  an existing file with no manifest entry is refused rather than
  adopted - attributing it to the requested URL would invent a
  provenance that was never observed.

- ~~275~~ | DONE, HIGH | A SECOND FETCH ERASED THE FIRST'S PROVENANCE.
  Review finding 6. The manifest was rewritten with only the current
  plan, so fetching a second country left the first files on disk and
  REMOVED THEIR ENTRIES.
  THE CONSEQUENCE IS THE POINT: tampering with the forgotten file then
  verified as "1 unchanged, 0 CHANGED, 0 missing". THE VERIFIER SAID
  ALL WAS WELL ABOUT A FOLDER IT HAD FORGOTTEN HALF OF - and machine 3
  reads the whole folder regardless, so the untracked file is analysed
  anyway.
  The manifest ACCUMULATES now, keeps a per-fetch history, and is
  written ATOMICALLY so an interrupted write cannot destroy the
  provenance of everything already fetched. verify_folder also reports
  UNTRACKED files, because a file nobody fetched still reaches the
  analysis.

- ~~276~~ | DONE, HIGH | A RESUMED RUN SILENTLY RETURNED AN EARLIER
  ANALYSIS. Review finding 7, reproduced: k=100, then k=200 into the
  same folder. THE SECOND CALL COMPLETED SUCCESSFULLY and returned
  N_100, with no N_200 column and no warning.
  Tiles were skipped on FILENAME AND EXISTENCE ALONE. The manifest had
  RECORDED the parameters all along and nothing ever read them - the
  identity existed and was ignored.
  Resume now compares the full run identity - k, radii, decay, tile
  size, dtype, unit size, cell count - and refuses a mismatch by name,
  saying which parameter differs and what each side holds. A matching
  resume still works, and a test guards that too, because a check
  must not break the feature it protects.
  A RUN THAT SILENTLY ANSWERS AN EARLIER QUESTION IS THE WORST KIND OF
  WRONG: nothing in the output says so, and the columns look
  plausible.

- ~~277~~ | DONE, HIGH | THE GEOGRAPHIC CONTRACT WAS ONLY PARTLY
  ENFORCED. Review finding 4. BACKLOG 239 closed the mixed-CRS hole;
  three more remained, and one produced COORDINATES THAT WERE SIMPLY
  WRONG.
  A raster with NO CRS was accepted and recorded as the string
  "None" - now refused, because guessing would place the result
  somewhere plausible and wrong.
  A ROTATED raster was accepted and ITS ROTATION DISCARDED. The true
  first centre was 30.000500, -1.997000 and EquiPop returned
  30.000417, -1.997083. Not missing metadata - an arithmetic error,
  silent, in every coordinate. Now refused, with the QGIS menu path
  for warping it north-up.
  A PROJECTED folder was accepted and then reprojected AS IF IT WERE
  DEGREES, because three places assumed EPSG:4326: the transform
  source, the QGIS points-only stamp, and the field message. GHSL's
  Mollweide and any UTM folder are legitimate inputs, so the fix is
  not to refuse them but to USE THE FOLDER'S OWN CRS - and to skip
  suggest_projection entirely, since it reads lon and lat as degrees
  and refuses anything beyond +/-90.
  CLAUDE INVENTED A HELPER THAT DID NOT EXIST while fixing this
  (_cells_from) and had to undo it. Writing code against a function
  never checked for is the same fault as editing text never read.

- ~~278~~ | DONE | CHECKSUMS WERE RECORDED MORE STRONGLY THAN THEY
  WERE VERIFIED. Review finding 8. HDX's publisher_md5 and
  Geofabrik's .md5 sidecar were attached to every entry and NEVER
  CHECKED - so the manifest promised more than it had established. A
  local SHA-256 says what bytes are here; it says nothing about
  whether they are the right ones.
  A deliberately wrong publisher MD5 was accepted. A transport
  declaring 1,000 bytes and returning 5 had those five PROMOTED to
  the final file.
  Both refused now, and the bad file REMOVED rather than left. The
  transport checks Content-Length and cleans up its .part on any
  failure - the QGIS message had been claiming nothing partial was
  kept while .part files were being left behind.
  THE SIZE IS MEASURED FROM DISK, not taken from the transport's own
  report. Comparing a transport against the number it supplied would
  always agree with itself - the first version of this fix did
  exactly that and passed.

- ~~279~~ | DONE, HIGH - LAST OF THE REVIEW'S HIGHS | AN INCOMPLETE
  MEASURE WORE A COMPLETE MEASURE'S NAME. Review finding 3. The
  planner checked each side had AT LEAST ONE matching column, never
  that the bands the measure NEEDS are present.
  A folder holding f_00, f_15 and f_65 was accepted as a DEPENDENCY
  RATIO and computed (under-one + 65-69) / 15-19, keeping the general
  label and the general explanation. THE ARITHMETIC WAS RIGHT AND THE
  NAME WAS A LIE - the hardest kind of fault to see, because nothing
  is wrong with the number, only with what it is called.
  Refused now, naming EVERY missing band. A deliberately restricted
  study stays legitimate through allow_incomplete=True, and is then
  RECORDED on the plan, so it is CHOSEN rather than arrived at by
  absence.
  THE MOVED BOUNDARY, the second half of the finding: asking for 0-17
  selects whole bands 0 to 14 and drops ages 15, 16 and 17. Whole
  bands are right for banded data; discovering it in a footnote is
  not. The plan now carries asked-versus-covers per side and the run
  says "the boundary moved". IT ALSO REVEALED THAT 18-64 COVERS
  20-64, which nobody had noticed.
  AND CLAUDE WROTE THE BAND RULE OUT A SECOND TIME. expected_bands
  first had its own loop, and it DISAGREED with columns_for: 0-17 gave
  five bands in one and four in the other, so the completeness check
  would have demanded a band the selector never picks. Both use
  _bands_from now. ONE RULE WRITTEN TWICE IS EXACTLY HOW 272 HAPPENED,
  three days ago, in the same file's neighbour.

- ~~280~~ | DONE | LINES AND POLYGONS REACH THE LATTICE. The missing
  half of John's OSM plan: points already landed on the grid, lines
  and polygons did not, and LINES ARE WHAT FRICTION NEEDS -
  features_to_friction(), load_friction_table() and run_knn_friction()
  have existed for months waiting for exactly this input.
  A ROAD IS DIVIDED BETWEEN THE CELLS IT CROSSES, not assigned to one.
  250 m spanning three cells appears as 50 + 100 + 100, and total
  length is conserved to floating point - the property that matters,
  because anything lost at a boundary is lost invisibly.
  THE UNIT IS THE MEASURE, which is John's own observation: "if we
  declare that the longest road stretch in the unit defines the
  friction value we need to know WHERE it is the longest". So
  length_top is the longest-wins rule stated directly, and it is
  computed PER CELL - a class can win in one cell and lose in the
  next.
  POLYGONS REPORT A SHARE, 0 to 1, not an area: water and buildings
  are coverage and barriers rather than friction, and a raw area would
  depend on the cell size and stop being comparable between runs.
  GROUPING IS A DEFINITION THE USER SUPPLIES - cafe plus restaurant
  plus fast_food as "eateries" - and an UNGROUPED value keeps its own
  name, because a class vanishing from a classification is this
  project's signature fault. A value in two groups is refused, since
  the totals would count it twice.
  THE BOUNDARY IS HELD: EquiPop reduces geometry to VALUES ON A
  LATTICE and is not becoming a GIS. Intersect, within and buffer as
  general operations stay in QGIS.
  CLAUDE PREDICTED A REFUSAL THAT CANNOT HAPPEN: features on a distant
  lattice origin are not "elsewhere" - the grid is built AROUND them,
  so the origin only shifts the INDICES. The test now records that,
  which matters more than the refusal would have: the indices are what
  a join matches on, so the same road on two lattice origins joins to
  nothing.

- 281 | OPEN, NEXT VERSION, MINOR | "Value: many" DOES NOT SAY WHICH
  COLUMN IT MEANS. John, testing geofabrik: every other line quotes
  its name - Setting 'region', Value 'POP' - but a field whose options
  come from a live catalogue prints "Value: many - give this setting
  alone and run to see the list", with no quotes and no column named.
  He worked it out and said so anyway, which is the useful kind of
  report: HE COULD READ IT AND STILL FOUND IT UNCLEAR.
  The fix is to keep the same shape as the quoted lines - name the
  Value column explicitly - so the listing reads the same way whether
  the options are known in advance or fetched.

- ~~282~~ | DONE | LENGTH IN A GEOGRAPHIC CRS IS DEGREES, NOT METRES.
  Found while writing John's test instructions, which is the only
  reason it was found at all: 1.46.0 shipped a day earlier with a
  docstring promising metres.
  WORLDPOP'S LATTICE IS EPSG:4326, so the case that matters most was
  the broken one - a 1 km road measured 0.009, and every friction
  value derived from it would have been wrong by a factor of about
  100,000. GEOPANDAS WARNED, into a log nobody was reading.
  Lengths and areas are now measured ON THE ELLIPSOID when the
  lattice is geographic, which is exact and needs no projection
  choice. 1001.3 m for that road.
  AND THE CELL'S OWN AREA IS MEASURED PER CELL, because a 30
  arc-second cell is 860,000 m2 at the equator and 440,000 at 60
  degrees - one figure for the grid would have made every share wrong
  except in the middle. Pinned at the equator AND at 60 N, which is
  the test that would have caught a single global value.
  THE PATTERN: the tests used a PROJECTED lattice throughout, because
  that is what the friction machinery expects - and the real data is
  geographic. A test suite that never uses the shape of the actual
  input is a suite that agrees with itself.

- ~~283~~ | DONE | A RUNNABLE RECIPE FOR THE OSM WORK, and it says
  where to run it: THERE IS NO QGIS TOOL FOR THIS YET. The engine
  works and nothing wraps it, so run_osm_friction.py drives it from
  the QGIS Python console, the OSGeo4W Shell or Anaconda.
  Written and RUN end to end here on data shaped like John's -
  WorldPop 1 km rasters plus a Geofabrik-style roads layer over the
  same ground - before being handed over. 60 roads, 194 cells, seven
  classes.
  equipop/providers/osm_road_groups.json ships the group defaults
  John asked for, with illustrative friction values and a note saying
  plainly that NOBODY HAS CALIBRATED THEM and that a published result
  needs his own. Seven OSM classes collapse to five groups.

- ~~284~~ | DONE | "THE LOG IS NOT GIVING ME ENOUGH INFO TO EVEN
  DOWNLOAD WHAT I DOWNLOADED BEFORE." John, after SEVEN failed
  attempts in five minutes on a fetch he had already done.
  THE TOOL SAID "No such dataset: None". None is not a value he
  typed - it is the ABSENCE of a row he did not know to add, printed
  as though it were his mistake. It now says "No dataset was given.
  Add a row with 'project' in the Setting column", and lists the
  choices.
  AND IT NAMED THE DESCRIPTION, NOT THE KEY: "add a row with
  'dataset'" when the setting is called `project`. THE SAME FAULT AS
  268, where he was told the field was "Year" and the key was
  `epoch`. A message must use the words the tool accepts, and this is
  the second time that rule has been broken in the same file.
  HIS FIFTH ATTEMPT HAD THE RIGHT VALUE IN THE WRONG BOX -
  age_structures, a DATASET, placed in the version row - and the tool
  KNEW it was a dataset and refused without saying so. It now says
  which row it belongs in.
  TWO OF CLAUDE'S OWN GUARDS CAUGHT HIM WHILE FIXING IT. The door's
  no-provider-vocabulary test fired TWICE - once for naming WorldPop's
  fields in the check, once for naming them in the COMMENT explaining
  the first fix. And osm_road_groups.json, shipped a day earlier into
  equipop/providers/, was picked up by the registry loader as a
  malformed provider definition. providers/ is for provider
  definitions; it moved to equipop/tables/.

- ~~285~~ | DONE | A 33-CHARACTER NAME THREW AWAY A COMPLETED RUN.
  John: 646,766 cells, three widened passes, both k values - and then
  "T_h72004_africanamericanalone_100 is 33 characters - Stata allows
  32. Use a shorter prefix() or shorter treatment variable names."
  THE ARITHMETIC WAS DONE. Only the label was too long, and the tool
  answered by discarding the work and telling him to rename his data.
  Names are SHORTENED now, and what is cut is THE MIDDLE: the prefix
  says which measure and the tail says which k, both carry meaning and
  both are short. His four names fit at exactly 32 with the k intact.
  COLLISIONS ARE CHECKED and a disambiguating digit added, because two
  long names can truncate to the same thing. EVERY RENAME IS
  ANNOUNCED - a silently renamed column is how somebody publishes the
  wrong variable.
  AND A WARNING NOW COMES BEFORE THE COMPUTATION. The ado cannot know
  every column the engine will make, but the LONGEST is predictable -
  prefix, the longest treat variable, and the largest k - so it says
  so first. A ten-minute run must not die at the labelling step.

- ~~286~~ | DONE | THE HELP'S EXAMPLES, and one of them was wrong.
  John asked for pop(), self-potential, decay and overshoot. Written -
  and CLAUDE WROTE overshoot(shares) FROM MEMORY. The real values are
  `whole` and `proportional`; `sampled` exists in the engine and is
  NOT offered by the Stata door. A user copying the help would have
  been refused by the command the help documents.
  He also asked what [fweight=] is FOR when pop() exists. They mean
  the same thing - "this row stands for N identical observations" IS a
  population count - and the command refuses both together. fweight
  demands WHOLE NUMBERS and pop() takes fractional counts, which is
  what gridded population needs. Now said in the help rather than
  discoverable only from the source.
  TWO TESTS NOW CHECK EVERY EXAMPLE: every option against the syntax
  line, and every VALUE against the inlist() the command validates
  with. The second is the one that would have caught this.

- ~~287~~ | DONE | THE RENAME WAS ANNOUNCED AND NOT APPLIED. One
  release after 285. The names were shortened correctly, PRINTED TO
  JOHN correctly - twelve of them, exactly right - and then the
  writing loop rebuilt each name from `res` and created the ORIGINAL.
  Stata refused with "invalid varname" AFTER the rename had been
  shown on screen.
  THE NAMES WERE RIGHT ON SCREEN AND WRONG IN THE DATA, which is the
  worst arrangement of the two: the log said the problem was solved.
  A mapping was computed and never carried to the point of use. That
  is the same shape as BACKLOG 252 - the number resolved in one layer
  and consumed raw in another - and as 272, where one rule was written
  three times and one copy went stale.
  THE TESTS NOW EXECUTE THE SHIPPED BLOCK rather than reading it. The
  broken version passed every reading test it had, because the
  announcement was correct; only the writer was wrong. Reverting the
  fix fails them.
  72 names checked at once, three prefixes, eight k values: all within
  32, all distinct, short names untouched, the k always preserved.

- ~~288~~ | DONE, JOHN'S RULING | BATCH RELEASES TO WHEN HE WILL
  TEST. He asked whether the last few days had been "limited progress
  and a lot of repair". Counted honestly: 6 new capabilities, 8 real
  defects found by external review, 6 reports from his own use, and
  SEVEN REPAIRS OF WORK SHIPPED DAYS EARLIER - three of them the same
  issue twice.
  The delivery rule says four artefacts per SESSION. Claude had been
  reading it as per MESSAGE, which put John on an install treadmill.
  264+265 and 285+287 would each have been one round trip.
  AND THE DIAGNOSIS, which matters more than the rule: five of the
  seven had ONE CAUSE - the test never met the real shape. The stub
  returned [] where QGIS returns NULL. The vector tests used a
  projected lattice and the data is geographic. The Stata tests READ
  the naming code instead of running it. A suite that never meets the
  real input is a suite that agrees with itself.
  Both written into HANDOVER 14 as standing rules.
  THE EXTERNAL REVIEW WORK WAS NOT CHURN and the record should say so:
  grid indices added to the population, a result that changed
  depending on which other files were on disk, a resumed run silently
  returning an earlier analysis. Those were producing wrong numbers
  before this week.

- ~~289~~ | DONE, JOHN'S RULING | HANDOVERS 9 AND 10 ARE GONE, AND THE
  GAP IS NOW RECORDED. Asked in HANDOVER 13, asked again in HANDOVER
  14 §5b, ruled by John in session 12: "record the gap".
  Written into HANDOVER 14 §5b, which is where a future session will
  look when it counts the files and finds 6, 7, 8, 11, 12, 13, 14. The
  jump is not a bad unzip and not a missing delivery - those two
  handovers were written and never committed.
  THE BACKLOG IS THE RECORD FOR THAT STRETCH and it is continuous
  across it, item numbers included, because items were appended as
  they arose regardless of which session was writing. Nothing else
  survives from 9 and 10.
  THE LESSON IS THE REASON TO WRITE IT DOWN RATHER THAN DROP THE
  QUESTION: a handover that is delivered but not committed does not
  exist. Two sessions of reasoning were lost to a step that takes a
  minute. From 14 onward the handover enters the repository root in
  the same act as the release.
  AND THE VERY NEXT RELEASE BROKE THAT RULE. Session 12 wrote this
  entry and then shipped 1.47.0, .1 and .2 with no HANDOVER_15,
  until John noticed the delivery was short. WRITE THE HANDOVER
  BEFORE BUILDING THE ARTEFACTS - it is the only ordering in which
  forgetting is impossible, and "in the same act as the release" was
  too vague to be followed by the session that wrote it.

- ~~290~~ | DONE v1.47.6 | IS THE ORIGIN ITS OWN NEIGHBOUR? John's
  ruling: two rules, i=j and i!=j, and `include` STAYS THE DEFAULT.
  THE PACKAGE ALREADY HELD TWO ANSWERS and called both "the
  neighbourhood". autocorr.build_weights() has always excluded self -
  its diagonal sums to exactly 0.0 - while the counting machines have
  always included it, with selfpot.py existing precisely because the
  origin's people sit at distance 0. The Tartu slides say "self is
  never its own neighbour", which was true of the estimator and false
  of every other machine.
  CONFIRMED IN THE FIELD BY JOHN, session 12, and this is the
  anchor the release turns on. Run in Stata on CaliData2010 over
  78,208 populated blocks of five-county Los Angeles, weighted by the
  group, against the R_ column the 2014 software left in the file:
      2014 software  mean 0.2752264  sd 0.2464846  min 0.0004955
      EquiPop 1.47   mean 0.2752264  sd 0.2464846  min 0.0004955
      same, i!=j     mean 0.2378486  sd 0.2482518  min 0.0000000
  IDENTICAL TO SEVEN DECIMALS on four statistics. Figure 4 of the
  2015 paper reads ~0.28. Excluding the origin lowers the index
  13.6%.
  THE MINIMUM IS WHAT PROVES IT IS A COMPUTATION AND NOT A COPY. An
  exact seven-digit match is also what a copied column looks like,
  and 1.46.3 and 1.46.4 were both naming-and-writing faults in this
  same path - names right on screen, wrong in the data - so the match
  alone was not enough to bank. Under i=j a block with any African
  American residents CANNOT score zero, because its own people are in
  its own neighbourhood; under i!=j it can hold them and have none
  among its neighbours, and that is a true zero. No copy produces
  that.
  CLAUDE'S OWN FIGURES WERE WRONG AND THE EVIDENCE WAS IN THEM. The
  bench run said 0.2765 and -13.4%, measured with the neighbour
  search capped at 48 cells, which never reaches k for remote blocks.
  The same measurement reported a median per-block difference of
  0.00000 alongside an index off by 0.0013 - which is the signature
  of a cap, not of a real difference - and it was read as a real
  difference anyway. FIELD NUMBERS REPLACE BENCH NUMBERS wherever
  both exist, and a bench number should carry its cap.
  THE SHIFT IS NOT UNIFORM AND THAT IS THE POINT. Minority members
  live disproportionately where their group is concentrated, so their
  own block is a large part of their measured isolation; for a 63%
  majority the neighbourhood is White either way.
  IT ALSO BENDS THE SCALE PROFILE, which is the more serious finding.
  Across k = 100, 200, 400, 800: African American isolation falls
  0.0240 with the origin in and 0.0037 with it out - SIX TIMES LESS
  DECLINE. Over that range the origin block shrinks from roughly all
  of the neighbourhood to about a seventh, so most of the slope at
  small k is THE ORIGIN BLOCK BEING DILUTED, not the surroundings
  changing. Mean block population there is 113 and 35.6% of blocks
  hold 100 or more, so at k=100 the "hundred nearest neighbours" IS
  the origin block for over a third of the region. None of this
  touches the 2015 paper's macroscale conclusions - by k=6,400 the
  origin block is negligible - but it qualifies the microscale end.
  A THIRD RULE WAS DESIGNED, TESTED AND DROPPED: remove one AVERAGE
  resident, n-1 and t - t/n. It preserves the cell's balance exactly
  (10 people of whom 1 treated give 0.1000, not 1/9 = 0.1111), it IS
  the expectation of suppressing a random individual (0.0999 over
  200,000 draws), and the same formula collapses correctly on
  individual rows where n=1 and the row vanishes. Dropped because it
  does nothing: on the LA blocks it moved isolation from 0.2765 to
  0.2764. Removing one person from a unit of 113 is noise - the
  contamination is your CELL-MATES, not you. Recorded so the next
  session finds the measurement instead of repeating the work.
  SHIPPED IN: equipop/selfrule.py, all three engines, both QGIS
  algorithms, both Pro tools, Stata's originrule(), doors/help.py.
  Named `originrule` in the doors rather than `selfrule` because
  Stata already has SELFpot and SELFPOTName and a third self... option
  risked an abbreviation clash that cannot be tested from here.
  TWO OF ITS OWN TESTS COULD NOT FAIL and the house practice caught
  both. The crossing-ring test was wrong twice: first the origin was
  never IN the crossing ring (rings are equal-distance groups, the
  origin sits at 0, and with its mass removed the crossing moves
  outward - it can only be in that ring when another cell SHARES ITS
  COORDINATES); then, with the fixture fixed, asserting on the SHARE
  still could not catch an unmasked ring total, because the ring
  fraction scales numerator and denominator alike and `proportional`
  pins N_k to k by construction. Only T moves - 15 to 5 - while N_30
  stays exactly 30 and R_g stays exactly 0.5. A share and a count
  that both look right while the total is a third of what it should
  be. Both reasons are in the test's docstring.

- ~~291~~ | DONE v1.47.6 | THE DOWNLOAD DEFECTS FROM THE EXTERNAL
  REVIEW OF 1.46.4. Eight claims were checked against this tree
  before anything was changed; all eight held and ONE WAS WORSE THAN
  REPORTED.
  THE MD5 SIDECAR. `md5_url` appeared exactly TWICE in 1.46.4: the
  line that wrote it, and a comment above the checksum block claiming
  BACKLOG 278 had fixed it. Nothing ever read it. 278 covered HDX,
  which supplies publisher_md5 inline, and left Geofabrik entirely
  unverified while the comment read as though both were done - so
  every Geofabrik file in every manifest since then carried a
  provenance record STRONGER THAN ITS EVIDENCE. Now fetched, parsed
  (`<32 hex>  name`, several lines, optional `*`), checked, and the
  outcome recorded per file as publisher_check.
  THE OTHERS, each with a test that fails when the old behaviour is
  restored: HDX asked rows=100 with no `start` and stopped, so
  Turkey's 175 datasets could not be reached past 100 - Sweden has 98
  and fitted, which is why a Sweden-only fixture kept it invisible;
  the manifest was written only after the LAST entry, so a failure at
  file 2 left file 1 with no provenance and a retry then refused it;
  untracked files were compared by BASENAME, so nested/a.tif hid
  behind a tracked a.tif - the one thing a verify exists to notice;
  an HTTP 200 carrying an HTML sign-in page was checksummed,
  manifested and reported as done; WorldPop's suffix filter ran
  endswith() against the WHOLE URL, discarding a valid
  `...tif?download=1` with no message.
  A SECOND DEFECT FROM THE SAME QUERY STRING, found while fixing the
  first: os.path.basename() of the whole URL produced a file named
  `swe_pop.tif?download=1` - refused outright by Windows, and on
  Linux a file no importer recognises by extension.
  THE FORMAT CHECK WAS NARROWED AFTER BEING WRITTEN. The first
  version carried a magic-bytes table per extension and refused
  anything that did not match. It broke twenty existing tests and,
  worse, would have refused .csv, .json, .pbf, .shp and whatever the
  next provider serves. Inventing a rule from an incomplete list is
  how the four-years-stale WorldPop docs and GHSL's prose-only CRS
  constraint both hurt this project. It now catches only the failure
  actually observed - a web page where a file should be - and leaves
  truncation and corruption to the declared length and the publisher
  checksum, which are the right instruments for those.
  ALSO: qgis/base.py discarded addFeature()'s return value and then
  reported the INTENDED row count, so a run that wrote fewer rows
  than it was given announced complete success. The simulator always
  returned True, so the one thing that could have caught it agreed
  with the code; tests/qgis_stub.py can now refuse a row. This is ONE
  MECHANISM that could produce the unexplained output complaints in
  224 and 232. It is not a diagnosis of them - those still need
  John's logs - but it can no longer be the answer.

- ~~292~~ | DONE v1.47.6 | THE SOURCE ARCHIVE SHIPPED NO RUNNERS.
  run_fetch.py, run_raster_folder.py and run_osm_friction.py were all
  absent from equipop-1.46.4.tar.gz. MANIFEST.in had gained
  `include demo_*.py` for BACKLOG 107 and nothing for the runners, so
  the miss its own comments describe three times happened a FOURTH.
  IT MATTERED MOST FOR run_osm_friction.py. BACKLOG 283 records that
  it is THE ONLY WAY to reach the OSM lattice engine, because no door
  wraps it - so the source archive carried the headline feature of
  1.46.0 and 1.46.1 with no way to run it.
  Fixed by one line, and guarded by a test that reads the run_*.py
  files OFF DISK, so a runner added later is covered without anyone
  remembering to come back.
  A SECOND THING THE ARCHIVE NEVER CARRIED, found the same way when
  John's Pro tooltip came back empty: arcgis/EquiPop.<Tool>.pyt.xml,
  the sidecars Pro reads for the comment beside every parameter box.
  Never in MANIFEST.in, never in an sdist, never in a delivery. They
  are build outputs, so they are kept OUT of the repository (45) and
  put INTO the archive - both statements are correct and the
  distinction is the point. See 34.
  AND THE GUIDE THAT TELLS PEOPLE WHICH FILES TO KEEP WAS WRONG.
  arcgis/ARCGIS_GUIDE.md said "Keep these FOUR files together" and
  then listed THREE, under a heading stamped v1.16.8, and told the
  reader that "Two tools appear" when four do. A user following it
  replaces the toolbox and keeps the sidecars, which is EXACTLY what
  happened to John at 1.47.6. The instruction, not the packaging, is
  what produced the empty box.

- ~~295~~ | DONE v1.47.6 | make_help_xml.py COULD NOT BE RUN WHERE IT
  IS SHIPPED. It has been one of the five Pro files since 1.44.4 and
  it imports test_arcgis_stub, which lives in the repository's tests/
  directory and is NOT one of the five. ModuleNotFoundError,
  immediately, every time, for the whole life of the delivery.
  FOUND BECAUSE THE INSURANCE WAS UNINSURED. 1.47.6 wrote the Pro
  parameter comments as escaped HTML on an untested hypothesis (34)
  and offered `--plain` as the ten-second way back. John pasted the
  command, it failed, and only then did anyone check whether it could
  have worked. It could not. THE ESCAPE HATCH FOR AN UNTESTED CHANGE
  WAS ITSELF UNTESTED - which is worse than the change, because it
  was the reason the change felt safe to ship.
  He also pasted it into Pro's embedded Python WINDOW rather than the
  Python Command Prompt, which is a separate and entirely reasonable
  mistake: the guide said "run this from the repository root" to
  somebody who has no repository.
  FIXED by falling back to REAL arcpy, which is what Pro's Python
  Command Prompt has, so the script now runs in the two places it is
  ever run from and says so when it is in neither. The guide gives
  both invocations and names the window that is not a prompt.
  FOURTH INSTANCE THIS SESSION of shipped-but-unreachable, after
  inventory.py, vectorjoin.py and RunLog (293). The first three were
  capabilities nobody could get to. THIS ONE WAS THE RECOVERY PATH
  FOR A KNOWN RISK, which makes it the one worth remembering.

- ~~294~~ | DONE v1.47.6 | MACHINES 3 AND 4 HAD NO HELP TEXT AT ALL,
  IN ANY DOOR. ContinentalRasters and SpatialDemography are
  registered in the Pro toolbox and executed by the suite, and
  THIRTEEN of their parameters had no entry in doors/help.py: folder,
  crs, weight, sumcohorts, pattern, tiles, out, indices, year,
  settings.
  THAT IS WHY make_help_xml.py COVERED ONLY TWO OF THE FOUR TOOLS. It
  refuses to write a sidecar with a gap in it - correctly - so rather
  than a partial file it produced none, and both tools showed "There
  is no description for this item", "There is no usage for this tool"
  and "There is no explanation for this parameter" against every box,
  in every release.
  THEIR SUMMARY AND USAGE TEXT EXISTED THE WHOLE TIME - 738 and 436
  characters for machine 3, 580 and 447 for machine 4, sitting in
  help.py and reaching the Pro dialog's own description. It could not
  reach the '?' page for want of a file that thirteen missing
  parameter entries prevented being written. A whole tool's
  documentation held back by the smallest part of it.
  CLOSED BY JOHN'S SCREENSHOT, session 12. He sent the '?' page for
  machine 3 as evidence that the panel text was "mostly missing" -
  which it was, and for this reason rather than for BACKLOG 34's.
  THE FIX: thirteen entries in the house style, grounded in what the
  parameters actually do rather than in their dialog labels, and all
  four tools added to make_help_xml.py. FIVE files now travel to Pro,
  not three. The guard counts REGISTERED TOOLS from the toolbox
  rather than expecting a number, so a fifth machine cannot ship
  unhelped the way these two did.

- ~~295b~~ | DONE v1.47.6 | THE REACHABILITY MATRIX. John's request,
  session 12: "can a person get to this, and from which door?" - and
  his memory of a functions-by-doors table from the early Stata work.
  THAT TABLE DOES NOT SURVIVE. Every .md in the tree was searched;
  the MANUAL narrates door parity at length and no matrix exists.
  tests/door_parity.py is its living descendant - it holds the BOX
  NAMES both GIS doors must offer, and it has earned itself twice
  this session - but it compares two doors to each other and cannot
  see a capability with no door at all.
  SO: tests/reachability.py, one row per capability and one column
  per door, every cell either evidence or an explicit reason. Five
  checks, each verified by breaking it: a door's evidence must still
  exist in the file it names; a capability must be reachable from
  somewhere; a missing door must give a reason longer than a shrug; a
  cited backlog number must exist; AND EVERY MODULE IN THE PACKAGE
  MUST APPEAR - as a capability with doors, or in INTERNAL as
  machinery. That last is the one that would have caught all five of
  this session's finds.
  IT IS DECLARED, NOT DERIVED, AND THE FIRST ATTEMPT PROVED WHY. A
  grep of each door for the engine function it calls was WRONG IN
  BOTH DIRECTIONS: machine 1 showed as absent from QGIS and Pro,
  because both reach it through stata_bridge.dispatch rather than by
  name, and the lattice join showed as PRESENT in QGIS because
  alg_continental.py imports join_to_points for something else. A
  matrix that guesses is worse than none - that one said the doors
  were fine.
  IT FOUND 296 WITHIN A MINUTE, in Claude's own declaration, and
  refused a same_as reference pointing at a door that exists.
  20 capabilities, 30 declared gaps, every one with a reason.
  Read it with: pytest tests/test_reachability.py -s -k report

- ~~297~~ | DONE v1.47.6 | TWO DEFECTS JOHN'S REAL OSM FOLDER FOUND,
  neither of which any fixture would have shown.
  (a) A SHAPEFILE IS ONE THING IN FIVE FILES. His Swedish extract
  inventoried as 109 rows, of which 91 were .cpg, .dbf, .prj, .shx
  and .lock - eighteen of each - burying the eighteen layers that
  were the answer. Sidecars are now folded into their .shp row and
  counted in a `sidecars` column. A .dbf is only folded away when its
  .shp is PRESENT; alone it is a vector with no geometry, because
  John notes it sometimes holds the data and can be rebuilt.
  (b) THE HEADLINE FEATURE WAS SILENTLY OPTIONAL. Reading the class
  values - the fclass vocabulary, the entire point of this tool on an
  OSM folder - went through pyogrio.read_dataframe, WHICH NEEDS
  GEOPANDAS even with read_geometry=False. Without it the values
  vanished into a per-record `warnings` key that no door displayed,
  so a folder inventoried with no fclass column at all and nothing
  said why. They now come through pyogrio's Arrow reader, which needs
  only pyarrow; geopandas is a fallback rather than the way in.
  THAT SECOND ONE MATTERS BEYOND THIS TOOL. The lattice-join door was
  about to be designed around geopandas as an accepted dependency,
  with a loud refusal and an install line, on the strength of machine
  3's rasterio precedent. It turns out the dependency was never
  needed: friction.paths_to_friction is explicitly "geopandas-FREE",
  written for the Pro clone that cannot grow it. A DEPENDENCY WAS
  ABOUT TO BE ADOPTED BECAUSE NOBODY CHECKED WHETHER THE PACKAGE
  ALREADY DID THE JOB WITHOUT IT.
  AND A LATTICE COLUMN THAT IS EMPTY FOR EVERY ROW. Machine 6 was
  built around "which files share a grid", which is right for
  machine 3's rasters and vacuous for OSM: John's folder reported 0
  lattices, because only rasters have one. The column stays - it is
  the point for rasters - but the tool is not only for them.

- ~~298~~ | DONE v1.47.6 | VECTOR ONTO THE LATTICE, John's model.
  MACHINE 3 ALREADY JOINED VECTOR TO THE RASTER GRID and took the
  CENTROID of every feature - right for shops and stops, badly wrong
  for a road network: a street crossing forty cells was counted once,
  wherever its midpoint fell. The box also declared types=[0], so a
  line layer could not even be chosen.
  JOHN'S MODEL, session 12: presence, not length. A barrier's cost is
  the cost of CROSSING it - a river that clips a corner still has to
  be crossed, and one running corner to corner is crossed once too -
  so length-weighting would be the wrong rule wearing the clothes of
  precision. Values come from A FIELD THE USER PREPARES IN GIS, not
  from a table in the dialog, which keeps the vocabulary where the
  vocabulary is.
  THE REFINEMENT THAT MADE IT WORK: each CLASS once, not each
  FEATURE. OSM cuts one street into many records wherever a tag
  changes; John's Swedish extract holds 2,139,630 road features and
  his screenshot shows `unclassified` three times and `trunk_link`
  twice inside ONE JUNCTION, all one street. Charged per feature that
  junction costs 7; charged per class it costs 3, which is the number
  John wrote by hand. Per-feature would have made the friction partly
  a fact about how the data was cut - worst in cities, where
  segmentation is densest.
  THREE FIDELITIES, user's choice, class-present the default: centroid
  only, each class once, length or share. Plus add / largest /
  smallest / average for what happens when charges meet.
  NO GEOPANDAS, AND THAT WAS NEARLY MISSED. The door was about to be
  designed around geopandas as an accepted dependency, justified by
  machine 3's rasterio precedent, with a loud refusal and an install
  line. friction.paths_to_friction is explicitly "geopandas-FREE",
  written for the Pro clone that cannot grow it. A DEPENDENCY WAS
  ABOUT TO BE ADOPTED BECAUSE NOBODY CHECKED WHETHER THE PACKAGE
  ALREADY DID THE JOB WITHOUT IT. The hundred lines of Liang-Barsky
  clipping are now EXTRACTED as friction.feature_cells and shared,
  rather than written a second time - BACKLOG 120's standing lesson.
  THE LATTICE-SPACE TRICK. feature_cells cuts on a unit grid anchored
  at zero; a raster lattice has an arbitrary origin and a negative e.
  Rather than generalise the clipping and risk it drifting from the
  barrier path that shares it, the COORDINATES are transformed so the
  lattice becomes that unit grid. Cell (i, j) then IS (gx, gy), and a
  clipped polygon area IS the share of the cell.
  POINTS ARE DETECTED, NOT ASKED ABOUT. A point has no length and no
  area, so the three rules coincide; demanding a class field for a
  layer of bus stops would be a box asking a question the geometry
  cannot answer. It also broke every existing point join the moment
  the default changed, which is how it was found.
  MACHINE 3 NOW READS THE INVENTORY machine 6 writes, reports which
  classes were charged and what each was worth, and warns when one
  class carries two values - because under class-collapse only the
  first feature in a cell is charged, so which value wins would
  otherwise depend on feature order.
  TWO COMPOUNDING SIMULATOR GAPS FOUND HERE, the most consequential
  of the five this release. QgsCoordinateReferenceSystem had no
  __eq__, so two identical EPSG:4326 objects compared UNEQUAL and
  every join built a transform it did not need; then QgsGeometry(other)
  was not a copy constructor, so that needless reprojection turned
  every line into an empty geometry and the door reported "no usable
  line or polygon geometry" about a layer full of them. A confident,
  wrong error message, produced entirely by the thing meant to catch
  wrong behaviour.

- ~~299~~ | DONE v1.47.6, RECORD CORRECTED BY JOHN | PRO'S
  MACHINE 3 HAD NO JOIN BOX AT ALL.
  THE FIRST VERSION OF THIS ENTRY SAID "Pro's join box still takes
  the centroid only", which implies a box exists. It does not.
  ContinentalRasters in the toolbox has NINE parameters - folder, k,
  unit, crs, weight, sumcohorts, pattern, tiles, out - and not one of
  them is a layer to join. John opened the dialog on his first test
  and asked; the answer took one grep.
  CLAUDE WROTE THE ENTRY FROM THE QGIS DOOR'S SHAPE, assuming the two
  machines matched because they are the same machine. Same fault as
  _rows(), as lat["pixel"], and as the Stata friction door in the
  reachability matrix: FOUR TIMES THIS SESSION a claim was written
  from what the code OUGHT to look like with the answer a grep away.
  The matrix caught one of those. It could not catch this one,
  because a reason is prose and prose is not checked.
  WHAT IS ACTUALLY TRUE: the join is QGIS-only and always has been.
  298 gave QGIS three fidelities; Pro has zero, so the gap is a whole
  capability rather than a difference of behaviour. The engine is
  shared and geopandas-free, so this is dialog work - the layer box,
  four settings, the geometry reader, the point auto-detection.
  door_parity does not catch it because the box is absent from BOTH
  its CORE lists; it was never part of the shared contract.
  FIXED IN v1.47.6. Six boxes, worded identically to QGIS and pinned
  by a test that compares the two modules' lists directly. The arcpy
  geometry reader was EXTRACTED from the barrier path, which had done
  multipart lines and polygon-rings-split-on-None since 1.15 and was
  about to be written a second time - BACKLOG 120 again. _mode()
  learned a `default` argument, because machine 3's join defaults to
  rung 1 and an unset box would otherwise have fallen silently to
  rung 0 and taken the centroid.
  AND THE FIRST ATTEMPT AT THE PARAMETERS DID NOTHING. The edit used
  replace() WITHOUT AN ASSERT against an anchor that did not match,
  so it reported success and changed nothing; the boxes were absent
  until the test asked the toolbox what it actually had. Assert the
  anchor, then check the result - not one or the other.

- ~~307~~ | DONE v1.47.9 | A DECAY RUN'S TIME DEPENDED ON THE
  HALF-LIFE, WHICH IT SHOULD NOT. John, session 12, reading the
  exercise-3 timings: "the time difference worries me".
  HE WAS RIGHT AND THE REASONING IS HIS. The neighbourhood is fixed
  by PLAIN k - reach 800 actual people - and decay only re-weights
  what is inside it. So the work is the same whatever the half-life.
  auto_m_neighbors still sized the fetch window from the decay
  TRUNCATION RADIUS, carrying a comment that said "a DECAYED sum must
  reach its truncation distance". That was TRUE UNTIL BACKLOG 185
  removed the unbounded sums (ND_inf and siblings) in v1.40. After
  that nothing reads past k - and fastcounts' deferral test was
  corrected at the time. THE WINDOW SIZING WAS NOT, and nothing
  compared the two.
  MEASURED ON LA COUNTY, half-life 2000 m, eps 1e-3: truncation
  radius about 20 km, window 11,159 cells where 697 satisfied k=800.
  138 seconds against 14, every second of it fetching neighbours that
  would never be read.
  AFTER: 9.5 s at half-life 2000 m and 9.8 s at 500 m - the time no
  longer depends on the half-life at all - and EVERY NUMBER
  IDENTICAL. RD 0.3109, R 0.3105, ND median 753.6 before and after.
  ALSO CONFIRMED, because John asked: N_k stays EXACTLY k, ND_k is
  the decayed sum over those same people and never exceeds it, and
  RD - R has mean -0.00014 with sd 0.011 - so decay is very slightly
  NEGATIVE on average, which is the opposite of the naive
  expectation, and moves individual blocks by about a percentage
  point either way. Both now have tests.
  THE SHAPE: a fix landed in one place and a second place kept the
  old assumption alive in a COMMENT that read as a justification.
  185 corrected the consumer and left the producer.

- ~~309~~ | DONE v1.47.10 | THE FIELD VERIFICATION READ A CACHED
  SCHEMA AND REPORTED RESULTS MISSING THAT WERE THERE. John, teaching:
  "the run is successful, but there is no data appended... BUT when I
  remove the file and reimport it - the material has been generated".
  arcpy.ListFields() reads a CACHED field list. On a GeoPackage or
  SQLite workspace Pro caches hard enough that fields written seconds
  earlier are invisible, so the run announced "7 result fields are NOT
  in the target" about seven fields that were all present.
  A WRONG VERIFICATION IS WORSE THAN NONE. It tells a user their
  results are missing when they are not, and the obvious next move is
  to run the whole thing again - 5 minutes 24 seconds, in this case.
  FIXED: ClearWorkspaceCache first, then read the fields from the
  CATALOG PATH rather than the layer object, which carries its own
  stale view. And when the target is NOT a file geodatabase the
  warning now says the fields may well be there and how to confirm,
  instead of implying failure.
  THE GEOPACKAGE ITSELF IS SOUND, checked rather than assumed:
  gpkg_contents with data_type 'features', the geometry column
  registered as POINT in EPSG:26945, an rtree spatial index and the
  extension registered. John noticed it "missing the typical icon in
  ArcCatalog" - the tell is the `main.` prefix Pro puts on the layer
  name, which is how it names tables in a GENERIC SQLITE workspace.
  Pro is not treating it as a GeoPackage feature class at all, and
  that explains the icon, the five-minute write and the cache.
  THE TEACHING MATERIAL NOW SAYS SO: read from the GeoPackage, write
  to a file geodatabase. 48 seconds against 5 minutes on the same
  data.

- ~~310~~ | DONE v1.47.11 | catalogPath POINTED AT A DATASET THAT
  DOES NOT EXIST, AND WE HANDED IT STRAIGHT TO ExtendTable. Confirmed
  by John at the Pro prompt: ListFeatureClasses on his GeoPackage
  returns ['main.la_blocks'], and Describe("la_blocks_1") raises
  OSError "does not exist". Yet the layer in his map is called
  main.la_blocks_1 - the _1 appended on the FIRST drag, against no
  duplicate - and Describe(layer).catalogPath follows the LAYER name.
  Pro opens a GeoPackage as a GENERIC SQLITE workspace (the `main.`
  prefix is the tell) and this is one of the consequences.
  TRUST, THEN VERIFY. catalogPath stays the first choice - for a
  GeoPackage it is the only workable form, which 1.22.1 established
  the hard way - but a path arcpy.Exists denies is not an answer.
  Three recovery routes, each independently tested: the dataSource
  connection string, which carries Dataset=main.la_blocks, the one
  fact catalogPath got wrong; stripping a trailing _N; and asking the
  workspace, accepting only a SINGLE unambiguous match.
  AND "cannot open" IS NO LONGER A LOCK. It matched none of the lock
  patterns yet John got the full lock message - attribute tables, edit
  sessions, OneDrive - after a five-minute run. Missing target is now
  its own case.
  THREE OWN GOALS WRITING THE FIX, all the same shape: a test that
  passed through the WRONG ROUTE (two recovery paths, one fixture, so
  deleting either left it green); os.path.dirname, which does not
  split Windows paths on the Linux test machine, so the whole recovery
  was dead and invisible; and then `import ntpath as os` followed by
  os.path.dirname, an AttributeError swallowed by the same broad
  except. A BROAD `except` TURNED A BUG INTO A PLAUSIBLE RESULT three
  times in one fix.

- ~~311~~ | DONE v1.47.11 | AN UNREADABLE LAYER EMPTIED THE FIELD
  BOXES, AND THE TOOL THEN BLAMED THE USER. John filled the dialog,
  pressed Run, and was told "the treatment population ... needs the
  group count fields - but that box is empty". It was empty because
  we had cleared it between his filling it and his pressing Run.
  _clear_stale_fields drops field picks Pro remembered from ANOTHER
  layer, by comparing them against the layer's field list. It guarded
  the case where reading RAISES - and treated an EMPTY LIST as "none
  of these fields exist" rather than "I could not read this layer".
  ListFields returns [] rather than raising for a layer Pro cannot
  resolve (310), so the except never fired.
  NOT READABLE IS NOT NOT-PRESENT. Nothing is cleared when the layer
  cannot be enumerated.
  THIS IS PROBABLY ALSO THE VANISHING k VALUES of 305, which were
  recorded as unexplained.
  THE FAMILY, NOW THREE DEEP AND WORTH AN AXIOM: 309 read a stale
  schema and said the fields were not written; 310 read a bad path
  and said something was holding the data; 311 read an empty field
  list and said the user's choices were invalid. EVERY TIME A FAILED
  OR EMPTY READ WAS REPORTED AS A DEFINITIVE FACT ABOUT THE USER'S
  DATA. The engine was right in all three. A READ THAT FAILS TELLS
  YOU ABOUT THE READ, NOT ABOUT THE DATA.

- ~~312~~ | DONE v1.47.12 | AN EMPTY FRICTION VALUE NOW MEANS NO
  OBSTACLE. John's ruling, after hitting it on 735,098 OSM roads with
  six classes filled: "perhaps we should allow missing values and
  assign these the default = 0 value automatically".
  He is right and the old strictness was the wrong trade. Friction is
  additive and a cell costs 1 + friction, so 0 is UNAMBIGUOUSLY
  "nothing here" - and requiring seven hundred thousand features to
  say so was a tax charged for a purity that helped nobody.
  THE CASE THE STRICTNESS WAS REALLY PROTECTING AGAINST IS KEPT, and
  it is Claude's addition rather than John's: create the field, forget
  to populate it, run. Every value empty, every value 0, NO BARRIER AT
  ALL - and the tool reports "barrier applied", takes its several
  minutes, and returns exactly what a plain run returns. ALL-EMPTY IS
  REFUSED; some-empty is filled and counted.
  AND THE RUN NOW SAYS WHAT IT CHARGED: the distinct values found and
  how many features carry each, so a typo or a missed class is visible
  BEFORE the several minutes rather than after.
  THE MESSAGE WAS ALSO MISLEADING. "non-numeric or missing values"
  led John to ask whether floats were forbidden. They are not - -0.9
  is a motorway. It now names which fault it found and says fractions
  are fine.
  A MISSING COORDINATE STAYS FATAL. A point with no place is not a
  barrier anywhere.

- ~~313~~ | DONE v1.47.12 | TWO COORDINATE-SYSTEM GUARDS, John's
  rulings. "vector projected on read, DEM should not, add a loud
  error to that; no crs should not be silent - a loud error there".
  VECTORS ALREADY DID THE RIGHT THING and nobody knew: the barrier
  reader passes spatial_reference=main_sr to the cursor, so arcpy
  converts on read, exactly. That is why it is right for vectors and
  wrong for rasters - transforming a coordinate is exact, resampling
  a raster is not.
  THE DEM NOW REFUSES a coordinate system that differs from the
  analysis. Reprojecting a raster means choosing a resampling method
  and a cell size and accepting interpolation error, and a slope
  computed from a resampled DEM is not the slope of the original.
  That is an analytical decision disguised as a formatting step and
  it is the user's, not ours.
  AN UNDEFINED COORDINATE SYSTEM IS REFUSED rather than assumed.
  arcpy's spatial_reference= can only TRANSFORM; it cannot invent a
  source. A dataset with no .prj has its numbers passed through
  untouched to land wherever they land, and NOTHING DOWNSTREAM CAN
  DETECT IT - which is the whole argument for refusing.
  ON DATUMS, which John asked about: a CRS has a datum (where the
  earth is anchored) and a projection (how it is flattened).
  Transforming between different datums has several published
  methods. NAD83 to WGS84 differ by about a metre; NAD27 to NAD83 by
  up to a hundred, which would put a barrier a block away. Silent is
  fine when the datums match and not when they differ - naming the
  transformation used is the remaining piece, and is NOT built here.

- ~~314~~ | DONE v1.47.12 | THE TOOLBOX NOW SAYS ITS OWN VERSION, AND
  SHOUTS WHEN IT DISAGREES WITH THE PACKAGE.
  Pro CACHES .pyt MODULES. Replacing the file does not replace what
  runs; only a full restart reloads it. John lost most of an evening
  to that: the file on disk had the 311 fix, the module in memory did
  not, and THE ONLY WAY EITHER OF US COULD TELL WAS BY COUNTING LINES
  IN A TRACEBACK - 3503 against 3617.
  The manifest has always recorded the PACKAGE version and never the
  TOOLBOX version, and this entire episode is the gap between those
  two. Every run now opens with both, and warns loudly when they
  differ, naming the restart as the fix.
  THE GUIDE SAID "remove the toolbox from the project and add it
  again, OR restart Pro". The "or" is wrong: removing and re-adding
  does NOT reload a cached module. Tightened.

- ~~315~~ | DONE v1.47.12 | THE BUMP TOOL WAS FALSIFYING THE HISTORY
  IT PASSED OVER - and it is the tool written six items ago to stop a
  different kind of drift.
  It did a blanket string replace of the old version with the new
  across every file. A code comment written during 1.47.4 saying
  "v1.47.4, BACKLOG 299" became 1.47.5, then .6, and by 1.47.11 the
  toolbox claimed item 299 landed in 1.47.11 when it landed in
  1.47.6.
  BACKLOG.md AND MANUAL.md WERE ALREADY EXCLUDED FOR EXACTLY THIS
  REASON - "historical version numbers are facts about the past" -
  and the same reasoning was never applied to CODE COMMENTS, which
  are full of them. WORSE THAN THE ORIGINAL PROBLEM, because the
  backlog drift was visible and this was not.
  Now targeted: eleven declaration sites, each with a pattern that
  matches the declaration and nothing else, and it REPORTS A
  DECLARATION IT COULD NOT FIND rather than passing over it.
  The two falsified comments were repaired from the backlog's own
  record, which is the only surviving account of when each item
  actually landed.

- ~~318~~ | DONE v1.48.0, FOUND BUILDING 317 | PRO DROPPED THE DECAY
  MODEL WHENEVER THE HALF-LIFE CAME FROM A FIELD.
  _run_tool forwarded decay_model into the engine's keywords ONLY when
  a fixed half-life was given. A half-life taken from a field
  (hlfield) or from each point's own Dist_k (hlfromdist) went down a
  different branch that never set it - so the engine fell back to its
  default and RAN NEGEXP, whatever model the user had chosen, with
  nothing in the messages to say so.
  PROVED BEFORE FIXING: expsqrt through a half-life field gave exactly
  the negexp result (0.354512 both), and 0.358794 once the model was
  passed.
  FOUND ONLY BECAUSE 317 NEEDED THE SAME FORWARDING. Adding the
  calibration meant asking where the model travels, and the variable
  branches turned out not to carry it at all.
  THE SHAPE IS NOW FAMILIAR: 307 fetched a window sized for a setting
  that no longer applied, the 317 bin loop would have dropped the
  calibration had it not been caught, and here the model itself was
  dropped. A SETTING HONOURED ON ONE ROUTE AND LOST ON ANOTHER. The
  fix sets model and calibration once, for every route that decays,
  instead of per branch.
  PRO ONLY. Stata passes the whole Decay object, so the model rides
  with it; QGIS has no variable half-life. It had no test at all -
  now it has one, and breaking the fix fails it.

- ~~317~~ | DONE v1.48.0 | HALF-LIFE vs
  HALF-PROBABILITY: CURRENT EquiPop SILENTLY DEPARTED FROM THE
  PUBLISHED METHOD, AND THE PUBLISHED LOG-NORMAL WAS WRONG.
  John had carried this for several sessions: "it has been bugging
  me". Settled in session 12 against the paper itself - Östh, Lyhagen
  and Reggiani (2016), EJTIR 16(2):344-363, which old EquiPop
  implemented.

  THE TWO READINGS, named in the paper's own Appendix D:
    HALF-LIFE (HLM)        the median splits the 1-D AREA under the
                           decay curve in half. THE PAPER ADVOCATES
                           THIS, and old EquiPop used it.
    HALF-PROBABILITY (HPM) the weight is 0.5 at the median. CURRENT
                           EquiPop does this, for every model.
  They coincide ONLY for the exponential. For the other models current
  EquiPop does not replicate old EquiPop - a departure nobody chose
  and nobody recorded.
  CLAUDE GOT THIS WRONG ONCE ON THE WAY: before the paper arrived it
  told John that w(h)=0.5 "already implements your median
  calibration". Appendix D shows that is the reading the paper
  considered and set aside.

  VERIFIED AGAINST THE PAPER: all five published betas reproduce
  Table 1 to the last printed digit (m = 6010 m). Then the test the
  method rests on - share of the 1-D area before the median:
      exponential   50.00%   correct
      exp-normal    50.00%   correct
      exp-sqrt      50.00%   correct
      log-normal +  75.00%   NOT a half-life
      log-normal -  25.00%   NOT a half-life

  THE LOG-NORMAL ERROR, and it is easy to see how it happened. For the
  exp-normal the integral starts at x = 0, the CENTRE of a half-
  Gaussian, so the area share is erf(.) directly and erf = 0.5 IS the
  half point. That logic was carried to the log-normal - but there
  u = ln x sends x = 0 to u = -infinity, the integral starts at the
  FAR LEFT of a full Gaussian, and the share is (1+erf)/2. Setting
  erf = 0.5 finds the THREE-QUARTER point; the +/- gives its mirror at
  one quarter. The half point is erf = 0, which has ONE root:
      beta = -1 / (2 ln m)            (exact, for ln(d))
  The plus/minus pair were never two solutions to the half-life
  problem; they are the quartiles either side of it.
  THE EMPIRICAL RESULTS STAND. Log-normal (plus) had the best
  correlation in both datasets (0.631, 0.737): a good kernel, just a
  three-quarter-life rather than a half-life one. The paper's case for
  half-life models does not rest on the log-normal.

  JOHN'S DECISIONS, session 12:
    - DEFAULT: HALF-LIFE. It is what the paper advocates, it matches
      what users actually hold - a median from a survey - and it
      restores what old EquiPop did.
    - THE CHOICE APPEARS ONLY WHEN IT MATTERS. For negexp (the
      default) the two readings give the same beta, so no box. It
      appears when a user DELIBERATELY picks expnormal, expsqrt or
      lognormal - someone already making a methodological choice.
    - THE QUESTION, verbatim, as agreed:
          Your distance is...
          half of all trips are shorter than this
              (half-life - use for a survey median)
          a neighbour at this distance counts half as much
              (half-probability)
    - LOG-NORMAL: THE CORRECTED FORM, not the published roots.
    - LOG-NORMAL USES ln(d+1), as now. ln(d) puts the weight at zero
      when d = 0; the +1 avoids that.
    - POWER: EXCLUDED FROM HALF-LIFE. Its area diverges for any
      beta > -1 - the paper says so too - so no median exists.

  THE FORMULAS TO BUILD (half-life, 1-D area, m the median):
      negexp      beta = ln(0.5) / m                 (= half-prob)
      expnormal   beta = -( erfinv(0.5) / m )^2      erfinv(0.5) =
                                                     0.4769362762
      expsqrt     beta = -s / sqrt(m),   s = 1.678346990
                  s solves (1+s)e^(-s) = 0.5 exactly; the paper's
                  1.67835 is this, correctly rounded
      lognormal   SOLVE NUMERICALLY with ln(d+1). The closed form
                  -1/(2 ln(m+1)) is exact only for ln(d); with the +1
                  the log-space integral starts at 0, not -infinity.
                  Measured error of the closed form: 0.94% at
                  m = 100 m, 0.32% at 500 m, 0.07% at 6010 m. Use it
                  as the root-finder's starting guess, never as the
                  answer.
      power       not defined - refuse, and say why.

  AND ALWAYS: REPORT BOTH BETAS in the run messages, so the difference
  is visible even to a user who kept the default.

  RELEASE NOTE REQUIRED. For expnormal, expsqrt and lognormal,
  results CHANGE from current versions. Say so plainly: the current
  behaviour was itself an unrecorded departure from the published
  method, so this restores the record rather than breaking it - but
  anyone who ran those models on 1.30-1.47 needs to know.

  BUILT, v1.48.0: engine (decay.py, both tables, the exact
  log-normal solver on math.erf, power forced to half-probability with
  a message); Stata (calibration(halflife|halfprob), both betas in the
  log, r(decay) r(calibration) r(halflife) r(beta), the help file in
  synopsis, options and stored results); QGIS (the box beside the
  half-life, guarded so a missing package cannot kill the plugin);
  Pro (greyed unless expnormal, expsqrt or lognormal). The bin loop
  now copies the calibration, and has a test. halflife()'s own help
  text in both Stata and QGIS said "the distance at which a neighbour
  counts half as much" - the half-probability meaning, WRONG under the
  new default - and was rewritten.
  THE TEST THAT HAD ENCODED THE DEPARTURE. test_decay_half_life_
  property asserted weight(h) == 0.5 for EVERY model: it defined
  half-life AS half-probability, and would have failed any attempt to
  restore the published method. Split into one test per reading, plus
  one that checks each half-life by INTEGRATING the area rather than
  trusting the formula - since the published formula was itself wrong.
  Six fixes, each broken deliberately; each failed a test.

  RECORDED, NOT BUILT - THE DISC. All of the above is the 1-D area
  (the x/y diagram), as in the paper. On the DISC, where a ring at
  distance d has circumference 2*pi*d, the coincidence MOVES: there
  it is the Gaussian (expnormal) whose half-probability equals its
  half-life, not the exponential. There is a real argument that an
  OBSERVED median commute corresponds to the disc - trips reach real
  ground, and ground grows with d - but it only holds if
  opportunities are spread evenly, which they never are. A third
  option would make the tool harder to use for a distinction few
  users could act on. Kept as a methodological note.

- ~~319~~ | DONE v1.48.1 |
  `equipop setup` FAILS IN A VIRTUAL ENVIRONMENT, AND ITS MESSAGE
  GIVES THE WRONG ADVICE WHEN PIP IS MISSING.
  Stata was pointed at /Users/<name>/StataPython/bin/python - a
  virtual environment made for Stata, which is a sensible thing to do.
  Setup ran `python -m pip install --user --upgrade equipop` and got
  "No module named pip". TWO DEFECTS, both in _equipop_setup_py:
  (a) THE MESSAGE ANSWERED A QUESTION PIP DID NOT ASK. Whatever pip
      said, setup printed the SAME advice: if it mentions an externally
      managed environment, install a plain Python from python.org. For
      "No module named pip" that sends the user to replace their whole
      Python when the fix is one line: `python -m ensurepip --upgrade`.
  (b) `--user` IS ALWAYS PASSED, AND A VIRTUAL ENVIRONMENT REFUSES IT:
      "Can not perform a '--user' install. User site-packages are not
      visible in this virtualenv." So even after pip is fixed, setup
      fails again - on precisely the users careful enough to give Stata
      its own environment.
  REPRODUCED EXACTLY before recording: a venv made --without-pip gives
  her error; ensurepip fixes it; --user then fails as above; installing
  WITHOUT --user succeeds and `import equipop` reports 1.48.0. equipop
  1.48.0 is on PyPI, so the plain install is all that is needed.
  THE FIX: detect a virtual environment (sys.prefix != sys.base_prefix)
  and drop --user there; and read pip's stderr and advise on WHAT IT
  SAID - "No module named pip" -> ensurepip; "externally managed" ->
  the python.org advice; anything else -> quote pip without guessing.
  THE FAMILY: the same shape as 309-311 - a failure reported as if it
  were a different, more familiar failure. A message that guesses is
  worse than one that quotes, because it is believed.
  BUILT v1.48.1: a virtual environment is detected and --user dropped
  there, with a line saying so; and the failure now dispatches on what
  pip SAID - no module named pip -> ensurepip with the exact command;
  externally managed -> the python.org route; a --user refusal inside
  a venv -> named as such; no matching distribution -> network, proxy
  and Python version. ANYTHING ELSE IS QUOTED AND LEFT ALONE, with
  "we do not recognise that message, so we will not guess at it".
  The first version of the test only checked that the word ensurepip
  appeared, so disabling the branch that offers it still passed; it
  now pins the dispatch itself.

- ~~320~~ | DONE v1.48.1 |
  NORWEGIAN MACHINES: THE LOCALE FIX WENT TO PRO AND NEVER TO QGIS,
  AND THE CSVs WE WRITE ARE UNREADABLE IN A NORWEGIAN EXCEL.
  John, after the LA County lecture: everyone got it working, but the
  students whose machines were set to Norwegian hit "some issues".

  (a) QGIS PARSES TYPED NUMBERS WITH BARE int() AND float().
      alg_counts.py: k_values uses int(v), r_values and tau_values use
      float(v), straight on the text the user typed. A student typing
      a radius as 500,5 - which is how a Norwegian keyboard and a
      Norwegian Windows write it - gets the raw Python message
      "could not convert string to float: '500,5'", with nothing
      saying that a decimal comma is the problem.
      PRO HAS BEEN PROTECTED SINCE 1.16.7, when this was found on a
      SWEDISH machine: _to_float and _numlist take 12,5 and 12.5 alike
      and explain themselves when they cannot. THE FIX WAS NEVER
      CARRIED ACROSS - a door-parity gap of exactly the kind
      test_door_parity exists to catch, which it did not, because it
      compares which BOXES the doors offer and not how they READ them.
      Fix: move _to_float/_numlist into equipop/doors/ so both doors
      call one implementation, and extend the parity test to parsing.

  (b) THE CSVs ARE UTF-8 WITHOUT A BOM. _EquiPop_run.csv and
      _EquiPop_fields.csv are both written encoding="utf-8". Excel on
      Windows, with no BOM, falls back to the ANSI codepage, so a path
      or field name holding ae/oe/aa renders as mojibake - verified
      against cp1252, "andel_fodt_i_Norge" comes out
      "andel_fXdt_i_Norge" with the vowel replaced. One-word fix:
      encoding="utf-8-sig".

  (c) THE CSV DELIMITER IS A COMMA, and Excel splits on the SYSTEM
      list separator, a semicolon on a Norwegian machine, so even with
      the BOM the file opens as one column. No fix is free: a
      semicolon breaks English Excel and a "sep=," first line breaks
      every programmatic reader. Probably keep the comma and say so in
      the message. JOHN'S CALL.

  WHAT IS NOT AT FAULT, checked: dates - the manifest writes ISO UTC,
  which no locale touches. Pro's own numeric boxes are Pro's to parse.
  Python's float() and str() are locale-independent by language
  design, so nothing in the engine is exposed.
  NOT CHECKED, WORTH TESTING: field names carrying ae/oe/aa through
  the shapefile 10-character shortener, where the DBF encoding is a
  separate question from the CSV one.
  BUILT v1.48.1: (a) equipop/doors/numbers.py now holds ONE reader -
  to_float, to_int, numlist, intlist - and both doors call it. QGIS
  raises QgsProcessingException with the message; Pro wraps it as
  arcpy.ExecuteError, keeping a local fallback so the toolbox still
  works against an older package. to_int REFUSES a fractional k
  rather than rounding it, because a silently rounded k is a wrong
  answer that looks right. (b) both CSVs are utf-8-sig.
  (c) THE DELIMITER STAYS A COMMA - John's ruling: Excel's import
  wizard covers it, and the encoding was the real fault.
  THE PARITY TEST NOW COVERS PARSING, not only which boxes exist -
  it reads alg_counts.py and fails if bare int()/float() on typed
  text returns.
  AND THE REACHABILITY MATRIX CAUGHT THE NEW MODULE UNPROMPTED,
  exactly as it was built to: doors.numbers had to be declared before
  the suite would pass. That is the guard written after inventory.py
  and vectorjoin.py shipped with no way to reach them, working on its
  own author.

- ~~400~~ | DONE v1.54.3, JOHN'S FIELD REPORT, 10 OCTOBER 2026 | THE
  ONE WORD A CONFUSED USER TYPES, REFUSED BY THE THING THEY WERE
  ASKING ABOUT.
  He sent two things in one message: the doctor's clean verdict, and
  ```
  . equipop help
  unknown subcommand: help
    equipop doctor  - report on the Python this Stata is using
    equipop setup   - install or update the calculating engine
  ```
  `equipop help` was never a subcommand, because Stata's convention is
  `help equipop` - which is true, and is also not what anybody types
  the moment a subcommand has just been refused. **The worst-timed
  error message in the program.** One line of dispatch.
  THE CAPTURE MATTERS AS MUCH AS THE BRANCH. A partial install - the
  .ado files present and equipop.sthlp missing - makes Stata answer
  "help for equipop not found", which reads as though the command
  itself is absent. Captured, the message names the real cause and
  gives the same reinstall lines the unknown-subcommand branch prints.
  **AND MY TEST FOR THAT LIST WAS WORTHLESS.** It asserted
  `"equipop unit" in text` over the whole .ado - which matches the
  DISPATCH BRANCH, so the help line could have been deleted and the
  test would still pass. John's paste is a list that names two
  subcommands out of three. The list is now DERIVED FROM THE DISPATCH
  and checked inside the unknown-subcommand block, so a fourth
  subcommand is covered the day it is written.
  Break-check then found a THIRD place the same omission can live:
  deleting `equipop help` from the generated syntax section changed
  nothing, because that test only reads the .ado. A companion test
  now requires every dispatched subcommand to appear in
  `help equipop` too. **Three places, one derivation.**
  THE DOCTOR'S VERDICT GOT TWO LINES while I was there, and the pair
  he sent is the reason: a user told `machine 1 can run in this
  Python.` has nowhere obvious to go next, and `machine 1` is this
  project's vocabulary rather than a Stata user's. It now says what
  machine 1 is and names `help equipop` and `equipop unit` - printed
  ONLY when there is nothing to fix, so it never competes with a real
  diagnosis, which a test asserts.

- ~~395~~ | DONE v1.54.2, SECOND EXTERNAL REVIEW, FINDING 1 | `help
  equipop` WAS 746 LINES OF ONE CHARACTER EACH, AND I HAD LOOKED AT
  THE FILE.
  `_wrap()` returns ONE STRING of joined lines. Every other call site
  in make_sthlp.py does `add(_wrap(...))`; mine was
  `for line in _wrap(...): add(line)`, which iterates the string and
  yields CHARACTERS. The generated help carried 816 one-character or
  blank lines out of 1,103, and `help equipop` was unreadable from the
  unit-advice paragraph onward - **in both the SSC submission and the
  net-install archive.** A release blocker, and it shipped in the
  1.54.0 and 1.54.1 bundles.
  **FOUR THINGS FAILED TO CATCH IT, and each is worth knowing:**
  - `make_sthlp.py --check` compares the malformed output against the
    malformed generator and reports the file current. A currency check
    cannot see a defect that is in the generator.
  - `test_the_help_file_holds_no_broken_smcl` counts braces per line;
    a line holding one letter has none.
  - the paragraph's own words are all present, in order, so **any grep
    for its content succeeds.**
  - and I did grep it. I checked that the strings I expected were
    there and never looked at the SHAPE of the file. `wrote ... (1103
    lines)` was printed to me twice and I had no correct version to
    compare it against - it is 385 lines now.
  THE TEST: for every paragraph make_sthlp takes from HELP by name,
  the whitespace-normalised text must appear in the whitespace-
  normalised output. "What" split one letter per line normalises to
  "W h a t" and does not match. General over every HELP entry, not
  just the one that broke. Plus a direct shape check - no run of more
  than three one-character lines.
  TWO MORE DOCUMENTATION GAPS came with it, both found by writing the
  tests rather than by reading: `r(applies)` was returned by the ado
  and documented nowhere, which makes it useless for the one job it
  has; and `candidates()`, `tolerance()` and `nocache` appeared in the
  syntax line and were explained nowhere, because the options section
  is built from OPTION_HELP - the RUN's option list - so a
  subcommand-only option had no route into it.
  **THE STRONGEST OF THE NEW TESTS DERIVES THE DOCUMENTED `r()` NAMES
  FROM THE ADO'S OWN RETURN STATEMENTS**, in both directions. It found
  `r(cmd)` and `r(cmdline)` missing too, the moment it was written -
  the third and fourth undocumented results in the same block.

- ~~396~~ | DONE v1.54.2, SECOND EXTERNAL REVIEW, FINDING 2 | HALF OF
  393'S FIX WAS A FIX.
  393 made rasterio's DECLARED requirements a recorded fixture.
  `_absent()` still forced only the named packages absent and passed
  every other lookup to the live environment - so the answer still
  depended on what happened to be installed. The fixture declares
  `click-plugins`; on a machine without it the doctor correctly
  reported FOUR missing dependencies where the test expected three,
  and two historical-case tests failed again on a defect that was not
  there. **The same class of error, in the fix for that class of
  error, one release later.**
  A COMPLETE FAKE INSTALLED SET now: everything in the fixture is
  present unless named in `gone`, and a lookup for anything in
  neither list **raises** rather than falling through. A silent
  fall-through is how this came back a second time, so it is no longer
  silent.
  VERIFIED BY SIMULATING BOTH HALVES of the reviewer's environment -
  rasterio declaring no cligj/attrs/pyparsing/click-plugins AND
  click-plugins uninstalled - under which all 37 doctor tests pass.

- ~~397~~ | DONE v1.54.2, SECOND EXTERNAL REVIEW, FINDING 3 | A
  FRACTIONAL k WAS SILENTLY TRUNCATED BY THE PUBLIC ADVISORY.
  `_resolve_ks` did `int(k)`, so `k_values=[100.9]` came back as
  advice labelled k=100 with nothing said. **The project already has a
  rule about this**: the shared door reader refuses a non-whole k
  because k counts PEOPLE and quietly rounding a count of people
  produces a plausible wrong answer (320, 371). The new public
  function undid a rule the typed doors enforce - and its own comment
  claimed it validated what the engine would refuse.
  `100.0` IS ACCEPTED, `100.9` IS NOT. A Python caller writing 100.0
  means 100; the door reader is stricter about the typed string
  "100.0" because a decimal point a human put into a count is a fact
  about the human, which is a different question from this one.
  A BOOL IS NOW REFUSED. `k_values=[True]` was accepted as k=1,
  because bool is an int subclass - nobody's intention, and the sort
  of value that arrives from a mis-indexed array. `nan` and `inf` were
  raising raw ValueError and OverflowError from `int()`; they get
  EquiPop's message now.
  One resolver, used by `advise_unit` AND `request_key`, so 100 and
  100.0 cannot be the same advice under two different cache keys.

- ~~398~~ | DONE v1.54.2, SECOND EXTERNAL REVIEW, FINDING 4 | THE
  SCHEME CHECK SAT BELOW THE CACHE LOOKUP.
  394 put `_check_scheme` inside `fetch()`'s download branch. The
  cache check comes first and builds its destination from the URL's
  BASENAME - so with `payload.bin` already in the work directory,
  `fetch("file:///etc/payload.bin", wd)` printed `[fetch] cached` and
  returned the path. Nothing forbidden is read in that case, so it is
  not the local-file-copy risk itself; it is worse as a CONTRACT,
  because the caller is handed an unrelated file and believes it holds
  that URL's content.
  **AND MY TEST COULD NOT HAVE CAUGHT IT.** It asserted over the AST
  that every function containing `urlopen` also contains
  `_check_scheme` - which proves PRESENCE and says nothing about
  POSITION. Ordering is a behavioural property and needs a
  behavioural test: the new one primes the cache, calls fetch with a
  forbidden scheme, and also checks that a refused call leaves no
  work directory behind.
  THE GENERAL LESSON, and it applies to several tests written in this
  session: **an AST or source-text assertion can prove that something
  is there and never that it runs first.** Where ordering is the
  property, the test has to execute the path.

- ~~399~~ | DONE v1.54.2, SECOND EXTERNAL REVIEW, FINDING 5 | THE
  CACHE VALIDATED THE QUESTION AND NOT THE ANSWER.
  389's key covers the REQUEST - fingerprint, k values, tolerance,
  ladder, rule - and says nothing about the stored result. Measured:
  editing `recommended` to 999999, a cell count to -42 or a share to
  7.5 (750%) was accepted and returned.
  **THE WORST CASE IS `applies`.** Flipped to false under `include` it
  delivers the 388 defect straight out of a cache - the exact thing
  CACHE_VERSION 2 was bumped to keep out - and flipped to true under
  `exclude` it puts include-rule columns back onto an exclude report.
  Two fields that must agree, with nothing requiring them to.
  `_advice_is_coherent` now checks what `advise_unit` guarantees on
  the way out: the rule is known, `applies` is DERIVED from it, the k
  maps match `k_values`, shares are finite and within 0-1, saturated
  cells do not exceed the cell count, an exclude payload carries
  absences and never numbers, and **the recommendation follows from
  the shares it was supposedly derived from** - the coarsest size
  within tolerance, or none.
  AND THE 1.54.1 NOTE WAS WRONG TO IMPLY A SECURITY BOUNDARY. Anybody
  who can edit a dataset characteristic can recompute whatever we
  store beside it. This is corruption and version-skew detection, and
  the claim is now that a payload which does not describe a coherent
  answer to the request is refused. **The reviewer was right that the
  guarantee was broader than the protection; the fix narrows the words
  and widens the protection.**

- ~~388~~ | DONE v1.54.1, EXTERNAL REVIEW F1 | `originrule(exclude)`
  WAS SHOWN INCLUDE-RULE ADVICE, AND I HAD WRITTEN DOWN WHY THAT WAS
  WRONG BEFORE SHIPPING IT.
  `advise_unit` took `self_rule` and used it as a LABEL ONLY. The
  numbers were computed identically under either rule; the report then
  announced "Assumes originrule(exclude)" over include-rule counts and
  a footnote below said those counts do not apply. All three
  ordinary-run doors pass the user's real rule in, so an exclude run
  was told `100.0% of people are in a cell that already holds k` - and
  given a recommendation derived from it.
  **THE PART THAT MAKES THIS MINE RATHER THAN AN OVERSIGHT.** 385's
  own module docstring says the criterion "IS ONLY TRUE UNDER THE
  `include` ORIGIN RULE", and `tests/test_unitsize.py` ASSERTED the
  engine differs under exclude. The knowledge was written down, tested
  and then not used by the code path. That is 353, 368, 373 and 380 -
  the four releases before 1.54.0 - committed again in the release
  whose own handover section is about them.
  **MEASURED, AND IT IS STRONGER THAN THE REVIEW SAID.** Not
  "unreliable under exclude": fastcounts drops the origin's WHOLE CELL
  (`keep = idx != oi_range`, fastcounts.py:164), so the saturated
  count is STRUCTURALLY ZERO. Checked on four shapes, including one
  where a single cell holds every person and k=1000 - include reports
  1 saturated origin, exclude reports 0. The advisory was predicting a
  phenomenon that cannot occur.
  **AND A CORRECT EXCLUDE CRITERION DOES NOT EXIST IN THE CHEAP
  FORM.** I guessed one: under exclude, a huge neighbouring cell
  should serve every k, so Dist_k would stop varying. MEASURED AND THE
  GUESS WAS WRONG - with a 10,000-person cell 100 m away, Dist_k came
  back 57.02, 62.17 and 81.19 for k=100, 1000 and 5000, because the
  engine spreads a cell's population across its area. So k keeps its
  meaning under exclude at every cell size, and there is nothing to
  warn about. Good news stated as such rather than as a limitation.
  THE FIX: the rule now DECIDES whether the criterion applies.
  `applies` is in the advice dict; under exclude the per-k fields are
  **None rather than 0** (a zero reads as a measurement, and the next
  step is to pick the coarsest size on the strength of it), the k
  columns are not printed, no size is recommended, and a note says
  why. The cost and resolution-floor columns stay, because they are
  about the GRID and hold under either rule. `r(applies)` is new, so a
  do-file can tell "too dense for any size" from "this criterion does
  not apply" - both of which arrive as a missing `r(unit)`.
  AND THE RULE IS VALIDATED EVERYWHERE. It used to be a free string in
  the subcommand, so `originrule(inclde)` would have silently selected
  the exclude branch. One `_equipop_originrule` reader now serves the
  main command and the subcommand, carrying the `i=j` / `i!=j` aliases
  and the refusal that previously existed in one place only.

- ~~389~~ | DONE v1.54.1, EXTERNAL REVIEW F2 | THE CACHE ANSWERED A
  DIFFERENT QUESTION AND REPORTED A HIT.
  `unpack_advice` validated the format version, the data fingerprint,
  the k values and the tolerance - and NOT the candidate ladder or the
  origin rule. Reproduced: advice cached for candidates 25 and 50
  under include was returned to a request for candidates 1,000 and
  5,000 under exclude, with the old two rows and the old label, and
  the user was told "read from this dataset's stored advice".
  **THE RELEASE NOTE SAID "EVERY WAY OF BEING STALE RETURNS A MISS."**
  It was false, and the reason nobody noticed is in the test: my own
  `test_a_stale_cache_misses_rather_than_lying` checked three of the
  five components and called that every. A test named after a property
  it only partly checks is worse than no test, because it answers the
  question for the next reader.
  **FIXED STRUCTURALLY, AFTER THE FIRST FIX WAS WRONG.** The first
  attempt added `candidates` and `self_rule` as optional keyword
  arguments - and an optional check is one a caller can forget, which
  would restore the same silent stale hit by a different route and is
  the exact shape of 353/368/373/380. The request is now ONE value
  from `request_key()`, `unpack_advice` REQUIRES it positionally, and
  omitting it raises TypeError. Both sides build the key through the
  same two resolvers `advise_unit` uses, so a key cannot describe a
  differently-normalised request than the advice it validates; and the
  key is re-derived from the stored advice on read, so a hand-edited
  payload cannot pass by carrying a matching key field.
  CACHE_VERSION is 2, so no v1 string already saved in a .dta can be
  read back - a v1 advice has no `applies` field and would be treated
  as applying, which is 388 arriving out of a cache.

- ~~390~~ | DONE v1.54.1, EXTERNAL REVIEW F3 | THE DEGREE WARNING WAS
  BUILT AND THEN THROWN AWAY.
  `advise_on_run` appends the degree-envelope note to `out` at the
  top, and three later branches returned a FRESH EMPTY LIST: when the
  chosen unit is not on the ladder, when it does not saturate, and
  when there is nothing better to recommend. Measured: degree-like
  coordinates with a safe current unit gave a full report carrying the
  warning and an `advise_on_run` returning zero lines.
  **AND THOSE ARE THE BRANCHES WHERE IT MATTERS MOST**, which is the
  part worth remembering. They are the quiet ones - nothing else is
  printed - so the note was not competing with other output, it was
  the only output there would have been. `return out` in all four
  places, and a parametrised test per branch.
  THE SHAPE: a warning assembled in a variable and discarded by a
  later `return []` is invisible to every test that checks the full
  report, because the full report is produced by a different function.
  Worth looking for wherever two functions share a message.

- ~~391~~ | DONE v1.54.1, EXTERNAL REVIEW F4 | A PUBLIC FUNCTION THAT
  ACCEPTED INPUTS THE ENGINE REFUSES.
  `advise_unit` took anything: a negative population, a zero total, a
  tolerance of 5.0, an origin rule of "banana", and a candidate size
  of `inf`. An advisory that accepts inputs the engine refuses is
  advice about a run that cannot happen.
  MEASURED, each one:
  - weights `[10, -9]` in two cells -> total population 1, saturated
    population 10, so `share_people` came out **10.0 - one thousand
    percent** - and that was compared against the tolerance to choose
    a cell size. `build_cells` has refused a negative population since
    1.22.2 with a reason; now this refuses it in the same terms.
  - a tolerance of 5.0 means every candidate passes, so `max(good)`
    names the coarsest size on the ladder every time: a confident
    recommendation to use 5,000 m cells, from a threshold that cannot
    bind.
  - `float("inf") > 0` is **True**, so inf passed the candidate filter
    and produced a table row at an infinite cell size, sorting last
    and therefore eligible to be recommended as "coarsest". `isfinite`
    is the test that was meant. Zero, negative and nan were already
    filtered, which is why this one survived review by eye.
  - a zero total population divides every share by nothing.

- ~~392~~ | DONE v1.54.1, EXTERNAL REVIEW F5 | THE VERSION BUMPER
  REWROTE EVERY LINE ENDING ON WINDOWS.
  `bump_version.py` read and wrote in text mode with Python's default
  newline handling. The sources are LF; on Windows each write converts
  them to CRLF, so a release operation there rewrites EVERY LINE of
  all ten declared files - the 4,932-line ArcGIS toolbox included -
  and `test_the_version_bump_survives_a_round_trip` reports all ten as
  changed. Nothing analytical moves; the cost is whole-file diffs and
  merge conflicts at exactly the moment a release is being reviewed.
  `newline=""` on both the read and the write, so the round trip is
  byte-for-byte whatever the file already uses.
  THE TEST PROBLEM IS THE INTERESTING PART: the existing round-trip
  test was CORRECT and was failing on Windows for the right reason -
  it just never ran there. So the new test does the half that is
  measurable anywhere (with `newline=""` a CRLF file round-trips; with
  universal newlines it does not) and asserts the write side
  structurally over the AST, with its limit stated in the docstring
  rather than implied.

- ~~393~~ | DONE v1.54.1, EXTERNAL REVIEW F6 | MY OWN TEST COUNT WAS
  NOT A PORTABLE CLAIM.
  Three doctor tests made `cligj` absent and expected the doctor to
  name it - which works only while rasterio DECLARES cligj. Rasterio
  1.5.2 does not; the reviewer's environment has 1.5.2 and mine has
  1.4.4, so three tests failed for them and passed for me. **"1,588
  tests pass" was true about rasterio 1.4.4 and I reported it as a
  fact about the release.**
  THE DEFECT IS USING THE INSTALLED PACKAGE AS BOTH FIXTURE AND
  SUBJECT. The behaviour under test is EquiPop's - does it name every
  missing dependency, does it quote a constraint, does it count them -
  and none of that should move when a third party edits its packaging.
  The requirement list is now a recorded fixture, and the strings are
  the real ones from John's machine on 6 October, so the field
  evidence is preserved rather than mocked away.
  VERIFIED BY SIMULATING THE REVIEWER'S ENVIRONMENT: with rasterio
  patched to drop cligj, attrs, pyparsing and click-plugins, all 37
  doctor tests pass; and the counterfactual holds - under that
  simulation the live-metadata scan returns `[]`, so the old
  assertion failed on a defect that was not there.
  A COMPATIBILITY TEST KEEPS THE REAL PACKAGE IN VIEW, asserting only
  what is true of any version: the scan returns a subset of what is
  actually declared, skips environment markers, and never produces an
  empty package name. The risk of a supplied fixture is that it drifts
  from reality and every test passes about a world that no longer
  exists; that test is the guard against it.
  **FOR FUTURE RELEASE NOTES: a test count is an environment
  measurement, not a property of the release.** Say which environment,
  or do not say the number.

- ~~394~~ | DONE v1.54.1, EXTERNAL REVIEW H1 | DOWNLOADER SCHEMES, AND
  AN MD5 FLAG THAT TURNED OUT TO MATTER.
  A static scan flagged unrestricted `urlopen()` at three sites. No
  exploit was demonstrated and none is needed to justify the fix:
  `urlopen` accepts `file://`, and a bare path with no scheme it reads
  as a LOCAL FILE, so a mistyped or pasted string could make `fetch()`
  copy something off the machine and print `[fetch] saved ...` as if
  it had downloaded it. One `_check_scheme` reader, called by all
  three paths, http(s) only - one WorldPop mirror still serves plain
  http, so that stays allowed.
  THE MD5 HALF WAS WORTH MORE THAN THE SCANNER THOUGHT. Every md5 here
  is non-adversarial - cache identity, change detection, or comparing
  against a publisher-supplied md5 - so `usedforsecurity=False` is the
  honest declaration. It is also FUNCTIONAL: on a FIPS-enabled host
  `hashlib.md5()` RAISES, so `cells.fingerprint()`, the tile manifests
  and the unit-size cache key would all crash on an institutional
  machine configured that way - a plausible partner machine in a
  consortium. Checked before touching it that the digest VALUE is
  unchanged (identical for empty, short and 2,560-byte payloads and
  for incremental updates), because bigrun verifies stored tile
  checksums on every read and a different digest would make every
  existing tiled run on John's disks fail verification.

- ~~387~~ | DONE v1.54.0, MADE AND CAUGHT WHILE CUTTING 1.54.0 | I
  EDITED FILES WHILE A BREAK-CHECK HELD A SNAPSHOT OF THEM.
  `breakcheck_doors.py` reads every target file once, then for each
  break writes a modified copy, runs the suite, and writes the
  original back - with a final restore in a `finally`. Correct, and it
  means **the script's snapshot wins over anything edited while it
  runs.** I ran it in the background and kept working: four edits to
  `stata/equipop.ado` - the fweight block, the `markout`, the
  `gl("wvar")` read and the `unit_was_set=` argument at the call site
  - were silently reverted by its next restore.
  AND KILLING IT LEFT A BREAK APPLIED, the same end state as 384's
  SIGPIPE: `pkill` interrupted a break between write and restore.
  **THIS IS 352 AND 384 FOR THE THIRD TIME**, in the same family and
  the same session that recorded 384. 352 was `| head -4` killing
  bump_version mid-write; 384 was `| head -14` killing a break-check
  before its final restore; this is neither a pipe nor a signal but
  the identical hazard - **a script that mutates the tree owns the
  tree while it runs.**
  THE RULE, extended from 384's: a script that mutates the tree is
  never piped, AND nothing else touches those files until it has
  finished. If there is other work to do, do it on files the script
  does not list - the documents, the backlog - or wait.
  HOW IT WAS CAUGHT: a test, within a minute, for the second time -
  `test_the_subcommand_takes_a_WEIGHT_both_ways_and_reads_it` failed
  on an assertion I had written minutes earlier precisely because the
  behaviour it checks is invisible at run time. Which is the argument
  for writing that kind of test: the lost edit was the one whose
  absence would have produced a plausible, complete, silently
  unweighted table.
  AND A SECOND LESSON FROM THE SAME HOUR, about break-checks
  themselves: **a break anchor that is not unique reports a false
  SURVIVED.** Verifying the weight test, I wrote a quick script whose
  anchor - the "not both - they mean the same thing" refusal - exists
  TWICE in equipop.ado, once in the main command and once in the new
  subcommand. `src.replace(find, repl, 1)` took the first, broke the
  main command's copy, and the subcommand's test passed: reported as
  a gap in the test when it was a gap in the script. The standing
  break-check scripts assert `src.count(find) == 1` for exactly this
  reason; the ad-hoc one did not. Anchored on the last occurrence
  instead, the break was caught at once.
  **An ad-hoc break-check needs the same uniqueness assertion as a
  standing one, because a false SURVIVED sends you to rewrite a test
  that was already correct.**

- 386 | open v1.54.0, FOUND WHILE BUILDING 385 | THE UNIT-SIZE
  ADVICE HAS NO STANDALONE DOOR IN QGIS OR PRO.
  Stata got `equipop unit`, a read-only subcommand a user can run
  before committing to anything, and Python has
  `equipop.advise_unit`. At both GIS doors the advice arrives ONLY
  attached to a finished machine-1 run - so to get a cheap answer
  about what cell size to use, a GIS user has to pay for the
  expensive run first, at whatever size they were already unsure
  about. The advisory itself costs 0.07 s on 100,000 rows; the run it
  is currently bolted to can take hours.
  Declared as a `door` in the reachability matrix rather than a gap,
  and that is correct as far as it goes: the capability IS reachable
  at all four doors. The asymmetry is in WHEN, and the matrix has no
  vocabulary for that - worth knowing when reading the row.
  WHAT IT COSTS TO CLOSE: a QGIS algorithm registered in
  `provider.py` and a Pro tool in `EquiPop.pyt`, both thin - two
  input fields, an optional population field, a k numlist, and the
  table printed to the log or the messages. The text already exists
  in `doors/help.py` under `unitadvice`, so no second copy. Pro would
  need a sixth help XML sidecar from `make_help_xml.py`.
  NOT URGENT: a GIS user sees the cell size in a box and gets the
  advice after their first run, which is the point at which they
  would reconsider anyway. Recorded so a future session does not
  rediscover it, and because the dialog wording is John's call.

- ~~385~~ | DONE v1.54.0, JOHN'S QUESTION, 9 OCTOBER 2026 | WHAT CELL
  SIZE DOES THIS DATA WANT?
  *"in all machines we assume that the unit size of grid should be 100
  - it has a visual setting in GIS, but in stata it has to be claimed
  with unit() to change. I wonder - is there a cheap way to determine
  the average nearest neighbour or similar - that would enable us to
  recommend a unit size? ... This is not an easy task to settle - in
  many gis cases, you will have many things close, and others a great
  distances - knowing the unit size is a battle between computing
  time and detail."*
  **THE CRITERION IS NOT NEAREST-NEIGHBOUR SPACING.** That says when
  cells start being EMPTY; it does not say when the answer stops
  being an answer. There is a precise threshold for that and this
  file already named it, in 95: once a cell holds >= k people, the
  whole neighbourhood IS the origin cell, `Dist_k` comes from
  `selfpot.radius_for_k` rather than from the data, and **k has
  stopped being a parameter** - k=200 and k=2000 return the same
  number. So the question has an exact answer: at each candidate
  size, how many cells already hold k, and how many people live in
  them.
  **MEASURED AGAINST THE ENGINE, not derived on paper.** The claim is
  that `count(cell population >= k)` equals the figure fastcounts
  reports after a run as `[selfpot] k=N: the whole neighbourhood was
  the origin cell for X of Y origins`. Checked by RUNNING the engine
  and parsing its own message, on three shapes - one dense cell among
  sparse, four cells at four densities, and population as a WEIGHT
  rather than a row count - with the boundary values of k in each. It
  agrees exactly. It is also only true under `originrule(include)`:
  under `exclude` the origin's own mass is removed before the search,
  so measured, the advisory predicts 1 and the engine reports 0. The
  report says which rule it assumed.
  **BOTH SHARES ARE PRINTED, because they answer different questions
  and differ by an order of magnitude.** On the Denmark fixture 1% of
  cells can hold 40% of the people. The engine's own message counts
  ORIGINS, so a reader has to be able to reconcile the two, and the
  recommendation uses the PEOPLE share because a study is about
  people.
  **TWO THINGS THE OBVIOUS IMPLEMENTATION GETS WRONG**, both found by
  break-check and both measured rather than argued:
  - the `>= k - 1e-9` slack is load-bearing for a SECOND reason
    beyond 304's. A WorldPop pixel carries a FRACTIONAL population,
    so a cell total is an accumulated float sum: 1,000 pixels of 0.1
    come to 99.9999999999986, short of 100 by 1.4e-12. Without the
    slack the advisory reports 0 saturated cells where the engine
    reports 1 - on exactly the data EquiPop is usually pointed at.
  - the two grid indices are paired into one key, and the multiplier
    has to be MEASURED. A fixed 1000 collides on a 120 km by 300 m
    strip - an ordinary extent: 1,201 cells become 1,200, the largest
    population reads 2.0 where every real cell holds 1.0, and k=2
    goes from 0 saturated cells to 1. A recommendation off the back
    of a hash collision. Checked against `build_cells`, which grids
    by pandas group-by and pairs nothing.
  **NO SINGLE RECOMMENDED NUMBER, AND NO DEFAULT IS CHANGED.** John's
  own objection is the reason for the first: density is heterogeneous,
  so one unit cannot be right everywhere, and a single number would
  hide the variation that makes the question hard. What the user gets
  is the trade-off. The second is 116's rule - reported, never
  substituted: if EquiPop chose the unit, two runs on the same data
  could silently use different ones and a published figure would
  depend on a heuristic that might change between versions.
  **THE CACHE JOHN ASKED FOR, AND THE MEASUREMENT THAT JUSTIFIES
  IT.** `advise_unit` costs 0.07 s on 100,000 rows, 0.84 s on a
  million and 16 s on ten million - nine linear passes, and
  `np.add.at` is already the fastest of the three groupings tried
  (bincount and argsort+reduceat are both slower at 10M). The
  fingerprint that validates a cache costs 0.55 s, so the cache earns
  its place on big data and is pointless on small. It lives in
  `char _dta[equipop_unitsize]`, which travels with the data,
  survives `save` and dies with `clear` - the right lifetime for a
  fact about this dataset. Keyed on a digest of the COORDINATES, not
  a path or a row count, because that is 344: a resumed run returned
  the first run's numbers since counting rows could not tell two
  tables apart. Every way of being stale returns a miss.
  **ON AN ORDINARY RUN IT IS USUALLY SILENT**, and it runs on every
  machine-1 run because it is free: measured against a real run on
  the same data, 0.3% of `build_cells` plus the kNN search, at both
  20,000 and 60,000 individuals. It speaks when the user did not set
  a unit and a different one would do, or when they DID set one and
  it saturates - with their own number. Otherwise nothing, because a
  note printed after every run is noise and noise is how a real
  warning gets missed.
  **`Unit(real 100)` HAD TO GO.** It delivers 100 both when the user
  typed `unit(100)` and when they said nothing, so the advisory could
  not tell a choice from a default and would have nagged everybody or
  nobody. Read as a string, defaulted in the body where the fact can
  be recorded. `r(unit)` unchanged.
  WHAT SHIPPED: `equipop/unitsize.py`; `equipop unit xvar yvar` as a
  third subcommand beside `doctor` and `setup`, with `r(unit)`,
  `r(cells)`, `r(estimated)`, `r(tolerance)`, `r(N)`, `r(people)`,
  `r(k)`, `r(originrule)`, `r(fingerprint)` and the matrix
  `r(advice)` - named `advice` and not `table` because `r(table)` is
  by universal Stata convention an estimation command's coefficient
  table; the advisory on a run at all three GUI/command doors; the
  text in `doors/help.py` so one source still serves four doors.
  THE TEST THAT MATTERS: every door calls the advisory inside
  `except Exception: pass`, which is right - the output is already
  written and an advisory must never turn a finished run into an
  error - and is also a machine for hiding a mistake forever. A
  single mistyped keyword would mean no door ever printed anything
  and no test failed. So `tests/test_unitsize_doors.py` BINDS every
  call site's keywords against the live signature, and checks that
  both of Pro's two exits pass through the advisory. That is 353,
  368, 373 and 380 turned into a test instead of a lesson.

- ~~384~~ | DONE v1.53.3, MADE AND CAUGHT WHILE CUTTING 1.53.3 | I
  KILLED MY OWN BREAK-CHECK WITH `| head` AGAIN.
  `python bc153.py | head -14` - SIGPIPE kills the script once head
  has its lines, so the FINAL `restore()` never ran and
  alg_continental.py was left carrying the `383-join-silent` break.
  The suite caught it inside a minute, as a test failure that read
  like a real regression.
  **THIS IS BACKLOG 352, IN THE SAME SESSION THAT RECORDED IT.** 352
  is `| head -4` killing bump_version.py mid-write and leaving the
  repository half-versioned. The entry is forty screens up in this
  same file. Knowing a hazard and writing it down did not stop me
  reaching for the same shortcut on a different script.
  THE RULE, now stated so it is not a memory: a script that MUTATES
  THE TREE is never piped. Redirect to a file and read the file.
  `> bc153.log 2>&1; cat bc153.log` costs one line.
  Two further breaks had gone stale in the same script - anchors into
  a function I had since simplified - and the script reported them as
  NOT APPLIED rather than passing silently, which is the one thing
  that worked as designed.

- ~~383~~ | DONE v1.53.3, THE 380 AUDIT | TWO SILENT DROPS THAT MADE
  A REPORTED COUNT UNRECONCILABLE.
  Both GUIs had a `continue` on null geometry sitting ABOVE the mask
  that exists to count dropped features, so the warning printed
  afterwards undercounted and the figure could not be matched against
  the user's own layer. A user with 12,000 shops is told about 11,998
  and has no way to find out why.
  qgis/barriers.py point branch: `continue` -> append NaN, so the
  `ok = isfinite(x) & isfinite(y) & isfinite(v)` eight lines below -
  which was always correct - does the counting and the reporting.
  alg_continental's centroid join: counted and reported at the drop
  site, because there a NaN would flow into the lattice join and the
  message belongs to the join layer rather than to points.
  THE ASYMMETRY IS THE TELL: two lines further on in the same
  function, an UNSUPPORTED GEOMETRY TYPE was already counted. One
  kind of drop was reported and another hidden, side by side.

- ~~382~~ | DONE v1.53.3, THE 380 AUDIT | THE ENGINE TRUSTED THE
  DOORS.
  `run_knn_stats` had 150 lines of validation - k, statistic names,
  variable declarations, Gini negativity - and nothing about whether
  a cell has a POSITION. Every door masks non-finite coordinates
  before calling (in QGIS that is also how `keep_outside` is
  implemented), so this was reachable only from the Python API.
  Reached, it printed "[stats] 3 cells, k = [2]", built a distance
  vector that was NaN throughout, sorted it in whatever order numpy
  produced, and died on `int(nan)` with a bare numpy message - after
  announcing that it was proceeding.
  `fastcounts` is already strict here BY ACCIDENT: scipy's cKDTree
  refuses non-finite input. So the counts engine was protected and
  the stats engine was not, for no reason anybody chose.
  **353's LESSON APPLIED ON PURPOSE**: a convention honoured at four
  doors is still worth guarding in the engine, because the engine is
  what a script calls. The refusal names the count and says what to
  do - mask with isfinite before build_cells, or read through a door.

- ~~381~~ | DONE v1.53.3, THE 380 AUDIT | `.isna()` AND `.notna()`
  WHERE `isfinite` WAS MEANT, AND SOMEBODY ELSE'S VOICE REFUSING.
  Two places tested coordinates for NaN-or-None when they meant
  finite, so an INFINITE coordinate passed and reached an
  `.astype(int)`, where pandas refuses with *"Cannot convert
  non-finite values (NA or inf) to integer ... cast to Int64"* - a
  sentence about pandas dtypes shown to somebody who typed a
  coordinate.
  **MEASURED, AND IT CORRECTS A CLAIM I MADE EARLIER IN THE AUDIT.**
  I first recorded this as a SILENT WRONG ANSWER, on the grounds that
  `np.array([inf]).astype(np.int64)` gives INT64_MIN - a cell
  9.2e18 m away. That is true of raw numpy and NOT of the pandas path
  these two actually take: pandas raises. **Nothing was silently
  wrong; the answer was right and the voice was not EquiPop's.** The
  audit over-claimed and the measurement corrected it, which is the
  reason for the rule about measuring before recording.
  cells.py: the right predicate was eight lines above, on the weight
  column (`blank = ~np.isfinite(wv)`).
  stata_bridge.py: `dispatch()` has used `np.isfinite(x) &
  np.isfinite(y)` for releases and the COUNTS branch is the one path
  that does not go through it - it re-derived a weaker mask of its
  own. The correct predicate existed in the same file and this path
  could not reach it: **380's shape, inside 380's own release.**
  AND A FALSE CLAIM OF MY OWN, CAUGHT BY THE BREAK-CHECK. My first
  version re-coerced the coordinate columns with
  to_numeric(errors="coerce") and a test took credit for handling
  non-numeric coordinates. Removing the coercion changed nothing:
  build_cells already coerces both columns at the TOP of the
  function, 200 lines earlier. The coercion came out and the test's
  docstring now says what it actually covers. A test that takes
  credit for a change it cannot see is how a suite comes to look more
  thorough than it is.

- ~~380~~ | DONE v1.53.3, JOHN'S FIELD FINDING | THE CONVENTION WAS
  ANNOUNCED IN THE SAME FUNCTION THAT COULD NOT REACH IT.
      ValueError: cannot create NumPyArray. geometry type found
  from `arcpy.da.FeatureClassToNumPyArray` on a layer holding NULL
  GEOMETRY, 8 October 2026. Forty lines below the failing call, in
  the same function:
      n_missing = int((~(np.isfinite(x) & np.isfinite(y))).sum())
      if n_missing: ... "-> Null results (EquiPop convention)."
  and `skip_nulls=False, null_value=np.nan` was passed DELIBERATELY
  so those rows would survive as NaN and land there. The QGIS door
  does it by hand and gets it right - `if g is None or g.isEmpty():
  xs.append(np.nan)`. **So the convention was implemented in the
  engine, named in its own message, honoured by one GUI, and
  unreachable from the other.** Fourth release running of that shape:
  353 a guard unreachable from the path that could trip it, 368 a
  hint classified and never rendered, 373 a parse fixed downstream of
  the parse that breaks.
  JOHN'S WORKAROUND WAS SELECTING THE NON-NULL FEATURES, which works
  and is NOT the same answer: those rows vanish from the output
  instead of being present-and-Null. For the scenario comparison he
  wants this for, present-and-Null is the one that matters - two runs
  stay row-aligned, so a difference is a difference in the answer and
  not a change of denominator. It is `keep_zero` from 1.53.0 one
  layer up.
  `_read_columns` keeps the fast reader and falls back to a cursor
  only when it refuses, because FeatureClassToNumPyArray is far
  quicker on millions of rows. **IT FALLS BACK ON ANY FAILURE AND
  NEVER ON THE MESSAGE TEXT**: `if "geometry type" in str(exc)` would
  break the day Esri rewords it, and 1.51.2 was already bitten by
  tests that matched a phrase of the messages that release improved.
  That also covers the neighbouring arcpy limitation for free -
  `null_value` does not apply to TEXT fields, so a null in a category
  column can kill the same call for an entirely different reason.
  **MY FIRST FIX WENT INTO `_read_input` ONLY, AND WAS INCOMPLETE.**
  A subagent audit of the property across the whole codebase found
  the SAME defect at two more call sites - the barrier table and the
  barrier point layer - each with a correct `isfinite` mask three or
  four lines below a fast read that dies first. The regression test I
  had written scanned only `_read_input`, so it could not have caught
  them. The scan is module-wide now, and ALLOWS BY PROPERTY rather
  than by name: a direct read is fine if it is inside a `try` (the
  caller degrades) or reads an OBJECTID only (never null). The first
  draft listed function names and every one of them was a guess the
  test then corrected - a name list also goes stale on a rename,
  which is how the reachability matrix went wrong in 333.
  TWO SIMULATOR FAULTS FOUND IN PASSING, and both mattered:
  the QGIS stub built a point from NaN ordinates instead of an EMPTY
  geometry, so every test that believed it was exercising null
  geometry was exercising a point at NaN and the reader's
  `g.isEmpty()` branch had never been run by anything; and the sink
  could not read back an output feature with no geometry, which is
  exactly what the convention writes. **A simulator that cannot
  produce the input cannot test the handling.**
  AND THE TEST THAT GUARDED THE CORRECT DOOR WAS WATCHING ITS TEXT.
  My first version asserted `re.search(r"g is None or g\.isEmpty\(\)")`
  against the QGIS source, and a break that kept the condition while
  turning `xs.append(np.nan)` into `continue` sailed past it - 370's
  finding again, the mechanism watched and the consequence ignored.
  Behavioural now, through the real reader, plus a test that the two
  GUIs give the SAME answer for the same unlocatable row.
  15 breaks, all caught, "never failed under any break: none".
  **CONFIRMED IN THE FIELD, 8 October 2026**, on the layer that
  produced the traceback: John ran it with the null-geometry features
  LEFT IN and it completed. That is the half of this finding the
  simulator could not establish - the stub is this project's own code,
  so the tests proved the fallback and could never prove that arcpy
  fails where he saw it fail, nor that a cursor succeeds against a
  real geodatabase. It does. Recorded because the entry otherwise
  ends by saying the last word is his, and a later session would have
  no way to learn that it came.

- ~~379~~ | DONE v1.53.2, JOHN'S MACHINE | THE PROPERTY TEST FOUND
  TWO COPIES I HAD NOT.
  The release began with FIVE k parsers counted by hand. The test
  written to forbid a sixth found a sixth and a seventh immediately -
  `int(float(piece))` inside Pro's ContinentalRasters.execute and
  again in SpatialDemography.execute. I had read both files that
  morning and not seen them.
  **THAT IS THE ARGUMENT FOR PROPERTY TESTS IN ONE LINE.** A per-door
  test asserts what its author already knows about; a property test
  asks the codebase. 370 made the same case for tags last release and
  this is the first time the method paid out on code I had just
  edited.
  THREE OF MY OWN BREAKS THEN FOUND THREE HOLES IN MY OWN TESTS,
  which is the second half of the discipline and the more
  uncomfortable half:
  - Deleting `NEEDS_A_NEIGHBOURHOOD = True` from alg_stats reproduced
    JOHN'S EXACT BUG and the whole suite stayed green. The test
    checked that the shared hook existed and that no door had its own
    copy, and never that a door DECLARED it needed a neighbourhood.
    It now runs the real hook with both boxes empty.
  - Restoring alg_stats' bare `[int(v) for v in k_text.split()]`
    broke nothing: my ast scan looked for a call nested inside int(),
    and the bare form passes a plain name. The scan now also refuses
    int()/float() applied over a `.split()`.
  - `test_the_engines_own_refusal_is_still_there` had never failed
    under any break, because I never broke analysis.py.
  Final: 19 breaks, all caught, "never failed under any break: none".

- ~~378~~ | DONE v1.53.2, JOHN'S MACHINE, THE ONE THAT PRODUCED THE
  TRACEBACK | 305's GUARD WENT INTO ONE DOOR OF FOUR, AND A SPACE
  WALKED PAST IT.
      ValueError: give k_values and/or r_values
  BACKLOG 305 added "give me k or r" to the DIALOG in 1.47.11, after
  John hit that same engine refusal while teaching. It went into
  CountsShares in Pro and alg_counts in QGIS, by hand, and into
  neither of the other two doors that reach the same refusal.
  ValueStatistics had no such check at all - eighteen months - which
  is why machine 2 answered with a traceback naming `k_values`, an
  argument nobody typed, from a dialog that had reported nothing
  wrong.
  **AND THE DOOR THAT HAD THE GUARD COULD BE WALKED PAST.** It read
  `if not _txt(pm, "k") and not _txt(pm, "r")`, and `_txt` does not
  strip. Pro's `Required` asks whether a box holds A VALUE, and a
  space IS a value - so one space satisfied Pro, satisfied the guard,
  and reached the engine as None. Measured: `" "`, a non-breaking
  space, a tab, `";"` and `"; ;"` all did it. `is_blank()` is the
  question every door asks now.
  THE CHECK LIVES IN EquipopAlgorithm FOR QGIS, so a new algorithm
  gets it by existing rather than by somebody remembering; Pro has no
  base class, so there the property is asserted against the source -
  a class with a k box must have an updateMessages that calls
  `_k_or_r_message`, and all four do.
  THREE SHAPES, because the doors genuinely differ and flattening
  them puts a wrong message in front of somebody: machines 1 and 2
  take k OR r; machine 4 requires k and has no radius; machine 3
  takes k and a BLANK k is a real choice, meaning the point table.
  Also caught here: `1 500` in a RADIUS box reads as radii of 1 m and
  500 m, both positive, so nothing downstream can refuse it - a 1 m
  neighbourhood holds almost nobody. Same typo as k=1, in the box
  John's ruling deliberately left permissive, so it is warned about
  rather than reinterpreted.

- ~~377~~ | DONE v1.53.2, JOHN'S MACHINE | SEVEN WAYS TO READ A k BOX,
  AND THE CORRECT ONE WAS REACHED FROM ONE DOOR.
  equipop/doors/numbers.py exists so that reading a typed number is
  written once. Its docstring says so. `to_int` has said *"a silently
  rounded k is a wrong answer that looks right"* since 1.47. Counted
  at the start of this release:
    1. doors.numbers.intlist      - correct; QGIS counts only
    2. .pyt `int(round(_numlist))` - Pro counts and stats
    3. alg_stats `[int(v) for v in k_text.split()]`
    4. alg_continental._numbers   - `int(float(piece))`
    5. alg_demography._numbers    - a verbatim copy of 4
    6. Pro ContinentalRasters.execute - `int(float(piece))`
    7. Pro SpatialDemography.execute  - a verbatim copy of 6
  Six of the seven truncated silently, which is precisely what the
  one correct reader was written to refuse. 6 and 7 were found by the
  property test, not by me (379).
  **THIS IS 354 AND 368 AGAIN AND THE COUNT IS NOW THE POINT.** 354
  was four copies of the measurement rule, 368 two copies of the hint
  rendering, this is seven copies of the k rule - three consecutive
  releases of the same defect in different files. The shared module
  being present and documented did not prevent any of them; what
  prevents the eighth is a test that fails when a copy appears.

- ~~376~~ | DONE v1.53.2, JOHN'S MACHINE | ONE FILE, ONE CHARACTER,
  TWO MEANINGS.
      to_float('1 000')  -> 1000.0     the space is a thousands separator
      numlist('1 000')   -> [1.0, 0.0] the space is a list separator
  Both in doors/numbers.py, which is the module whose whole purpose is
  that there is one answer. The correct single-value reader was
  destroyed by its own list wrapper, and '1 000' in a k box became
  k=1 and k=0 and then refused with "got [0]" - a sentence about a
  number the user never typed.
  **THE AMBIGUITY IS REAL AND IS NOT RESOLVED SILENTLY.** '200 100'
  IS two k values; nothing in the text distinguishes it from '1 000'.
  So the split stays, and `thousands_hint()` adds the suggestion to a
  refusal that was already justified - gated behind a zero in the k
  list, or a radius under 10 m, so it never reaches a user whose
  input was fine. A loose suggestion with a tight gate, said out loud
  in the docstring so nobody tightens the wrong half.

- ~~375~~ | DONE v1.53.2, JOHN'S RULING | '1,000' PEOPLE WAS ONE
  PERSON, AND THE RUN FINISHED.
      k typed as '1,000'  -> k = 1    writes Mean_income_1
      k typed as '1.000'  -> k = 1
      k typed as '10,000' -> k = 10
  No refusal, no warning, columns written. The only evidence is a
  name like `Mean_income_1` where `Mean_income_1000` was expected,
  which reads as plausible unless you are looking for it. **A WRONG
  ANSWER THAT COMPLETES IS WORSE THAN THE TRACEBACK THAT STARTED THIS
  INVESTIGATION**, and John found the traceback first by luck.
  THE CAUSE IS A GOOD FIX ONE NOTCH TOO WIDE. BACKLOG 320 made both
  GUIs share one locale-proof reader so they could not drift - right
  for a DISTANCE, where 500,5 metres is a real measurement a
  Norwegian keyboard produces, and wrong for a COUNT OF PEOPLE, where
  1,000 means one thousand in every notation anybody types. k is
  coerced with int() immediately, so a fractional k is meaningless by
  construction - which is the signal that tells the two apart.
  JOHN'S RULING, 7 October 2026: *"yes - in the next round we should
  refuse 1,000 - and good to keep it for radii"*. Refusing is the
  honest half; interpreting guesses at intent, and the alternative
  reading of '1,6' is one and a half people. The message suggests
  without deciding.
  TWO MISTAKES, TWO MESSAGES, which the first draft got wrong: a
  thousands separator ('1,000') and a decimal ('1,6') are different
  errors, and "write 1000" is nonsense advice for the second. The
  test is the thousands PATTERN - three digits after the separator -
  and NOT what `_clean()` makes of the text, because _clean is the
  function that misreads it. My first version asked _clean and
  advised *"if you meant 1, write 1"* for an input of '1,000'.
  A COMMA STILL SEPARATES VALUES when it is not between digits.
  Machines 3 and 4 have accepted '300, 500' since they were written
  and test_qgis_continental asserts it - that test is what caught the
  shared reader forbidding it, so the fix for one real defect would
  have removed a real documented capability. A count cannot have a
  decimal at all, which is exactly what frees the comma up.

- ~~374~~ | DONE v1.53.2, JOHN'S MACHINE | 337's "ONE FORMATTER"
  COVERED THE RADIUS AND LEFT k.
  BACKLOG 337 made field-name PREDICTION and the engine share one
  formatter, and the comment above `_fmt_num` says so. The line below
  it read
      ks = [t for t in (k_text or "").split()]
  so k was never parsed at all. For k='1.000' the prediction promised
  `N_1_000` while the engine made `N_1`: the shapefile-overflow
  refusal, the "fields already exist" check and the user's own
  preview all named columns the run would not produce. The prediction
  now parses with the ENGINE'S OWN readers, so the two agree by
  construction rather than by a test comparing them.

- ~~373~~ | DONE v1.53.2, JOHN'S MACHINE, AND THE ONE THAT NAMES THE
  PATTERN | THE FIX WAS PLACED AFTER THE FAILURE.
  BACKLOG 320 exists to stop `could not convert string to float:
  '500,5'` reaching a user. It added a locale-proof parse to
  alg_counts at line 445. Field-name prediction, at line 395, had
  ALREADY touched the same text with a bare `float()` through
  labels.numeric_tag - so a decimal-comma radius produced **that
  exact message, from 50 lines above 320's fix, in both QGIS doors**,
  measured. 320 was never fixed; it was fixed in the second half of
  one function, behind an earlier parse that failed first.
  IN PRO IT IS WORSE: prediction runs inside `updateMessages`, so a
  radius typed '500,5' crashed THE DIALOG'S VALIDATION CALLBACK while
  the user was still typing, in both Pro doors. Measured through the
  simulator.
  **THE THIRD CONSECUTIVE RELEASE OF THIS SHAPE.** 353 was a guard
  unreachable from the path that could trip it. 368 was a hint
  classified and never rendered. This is a parse fixed downstream of
  the parse that breaks. All three passed their tests. The rule worth
  writing on the wall: **when you fix how an input is handled, start
  at the EARLIEST point a door touches it, not at the line you happen
  to be reading.**
  numeric_tag is locale-proof now as well, though its callers no
  longer hand it text - it is the last common point before a column
  name, so a future caller must not be able to bring that message
  back.

- ~~372~~ | DONE v1.53.2, JOHN'S MACHINE | 320's OWN DEFECT, STILL
  LIVE IN THE SIBLING DOOR.
  doors/numbers.py's docstring describes the bug it was created for:
  "alg_counts read k, radii and tau with bare int() and float()
  straight on the typed text". alg_stats, written from the same
  template, still did:
      kw["k_values"] = [int(v) for v in k_text.split()]
      kw["r_values"] = [float(v) for v in r_text.split()]
  So the Norwegian student's radius of 500,5 that 320 was opened for
  produced the raw Python message in machine 2 while machine 1 had
  been protected since 1.47. A door-parity test does not catch it,
  for the reason 320's own docstring already gives: parity compares
  which BOXES exist, not how they are READ.

- ~~371~~ | DONE v1.53.1, JOHN'S MACHINE | A TRUE VERDICT THAT READ AS
  "ALL FINE".
  His report ended `machine 1 can run in this Python.` on the line
  after `rasterio : BROKEN`. The sentence is CORRECT - machine 1 needs
  none of the six optional libraries - and it is the last thing on
  screen, which makes it the thing a user remembers. Rasters are most
  of what he does. The verdict still answers the machine-1 question
  and then names any optional library that is INSTALLED BUT BROKEN,
  with the capability lost.
  AN ABSENT LIBRARY IS DELIBERATELY NOT MENTIONED THERE. The OPTIONAL
  heading already promises that "absent only means the feature is
  unavailable", and a verdict grumbling about every library a user
  chose not to install would make a healthy machine look faulty and
  teach them to stop reading it. absent is a choice; BROKEN is a
  fault. A test pins each half, because `!=ok` instead of `==BROKEN`
  is a one-character way to lose the distinction.

- ~~370~~ | DONE v1.53.1, JOHN'S MACHINE | THE TEST THAT WATCHED THE
  MECHANISM AND NOT THE CONSEQUENCE.
  `test_a_windows_dll_failure_is_recognised_separately` asserted
  `tag == "DLL"` and passed for its whole life while nothing on earth
  printed a DLL hint (368). It is not a test that COULD NOT fail -
  break the classifier and it fails - it is a test watching the wrong
  half of the mechanism. The suite knew the tag was computed and had
  no opinion about whether a human ever read it.
  **THE FIX IS A PROPERTY, NOT ANOTHER CASE.** Testing tags one at a
  time is what hid this: a tag with no renderer is invisible to a
  per-tag test. `test_every_tag_that_can_be_classified_has_something_
  to_say` scrapes the tags `_describe_failure` can return and asserts
  each produces output, so a new tag with no hint fails on the day it
  is written. The old test stays - classification is worth pinning -
  but it is no longer the only thing watching.
  This is the eighth entry on the project's own list of ways a test
  can be worthless, and the first one that is not "the test cannot
  fail": **the test can fail, and still not be watching the thing
  that matters.** 20 breaks applied across the file; every test
  function fails under at least one, including the seven that existed
  before.

- ~~369~~ | DONE v1.53.1, JOHN'S MACHINE, AND THE ROOT CAUSE NOBODY
  WAS LOOKING AT | A HALF-DELETED PACKAGE, ANNOUNCED FIVE TIMES AND
  READ AS NOISE.
      WARNING: Ignoring invalid distribution ~yproj
  pip printed that line five times in one install and it is the most
  useful line in the output. When pip cannot delete a directory on
  Windows it RENAMES it with a `~` prefix and carries on, so `~yproj`
  is the corpse of a `pyproj` uninstall that never finished - usually
  because a running Python, QGIS, Pro or an antivirus scanner held a
  file open.
  **THAT INTERRUPTED RUN IS WHY FOUR DEPENDENCIES WENT MISSING AT
  ONCE** rather than four separate accidents, which is the question
  367 could describe and not explain. It was visible from inside
  Python the entire time: one `os.listdir` of site-packages. The
  doctor exists to explain broken machines and was not looking at the
  directory the breakage was sitting in.
  LEFTOVERS is printed BEFORE the libraries, for this file's standing
  reason: the cause above the symptom, and anything that cannot crash
  above anything that imports. Silent on a clean machine, because a
  section that appears when there is nothing to report is a section
  users learn to skip - and then it goes unread on the one machine
  where it matters. Named, never removed: the first line of the report
  promises nothing is changed, and this is the one directory where a
  guessed deletion is unaffordable, from a command run to ASK A
  QUESTION.

- ~~368~~ | DONE v1.53.1, JOHN'S MACHINE | A CASE CLASSIFIED, TESTED,
  AND NEVER PRINTED - FOR EIGHTEEN RELEASES.
  `_describe_failure` has returned a `"DLL"` tag since 1.35 and
  `report()` rendered `if tag == "ARCH"` and nothing else. **On
  Windows "DLL load failed" is the single most likely way rasterio,
  geopandas and pyproj fail**, so the case that most needed advice was
  the one case with none - on the platform where every one of this
  project's users is.
  AND THE RENDERING WAS WRITTEN TWICE: the same `if tag == "ARCH"`
  open-coded in the REQUIRED loop and again in OPTIONAL. That is
  **354's lesson arriving one release later in a different file** - a
  rule written twice is a rule that gets extended once, and here it
  was extended zero times in two places. `_hint_lines(lib, tag)` is
  the one renderer now and both sections read it, so adding a tag is
  one edit in one place. A test fails if `report()` formats a hint
  itself again.
  The DLL hint says what the ARCH hint could not: close every Python,
  QGIS and Pro window first, because a file held open is how the
  half-installed state happens, and `where gdal*.dll` names the
  conda or OSGeo4W copy that is usually supplying the wrong library.

- ~~367~~ | DONE v1.53.1, JOHN'S MACHINE, AND THE ONE THAT COST HIM
  THREE EXCHANGES | THE FIRST MISSING MODULE IS THE WRONG UNIT OF
  TRUTH.
      rasterio     : BROKEN  No module named 'click'
  Correct, and it took three round trips to become useful. He
  installed click; pip then said rasterio also wanted `attrs`,
  `cligj` and `pyparsing`. The doctor had a remedy for a processor
  mismatch and NONE for a missing dependency, which is the commonest
  cause of exactly that line - so the diagnosis was right and the user
  was left nowhere to go. Same shape as the negative-population
  message in 1.51.2, which is why it was taken the day he asked.
  **THE COUNT IS ITSELF THE DIAGNOSIS.** One missing package is an
  accident; four is an interrupted pip run (369). Reporting one hid
  the distinction that explains the machine.
  `_missing_requirements` reads the library's own declared metadata
  and names EVERY dependency that is not installed, with one install
  command. Keyed on the DISTRIBUTION through importlib.metadata, not
  on an import: importing is what is already failing, and the import
  name often differs from the distribution name (`click-plugins`
  imports as `click_plugins`), which would make it a guessing game.
  Standard library since 3.8, and it reads metadata rather than
  importing, so asking the question cannot trigger the failure being
  diagnosed - which the module docstring's no-third-party-imports rule
  demands.
  **THE CONSTRAINT IS QUOTED, AND THAT IS NOT COSMETIC.**
  `pip install cligj>=0.5` pasted into cmd.exe REDIRECTS: the shell
  eats `>`, writes a file called `=0.5` into whatever directory the
  user is standing in, and hands pip a bare `cligj`. The advice would
  appear to work while installing an unconstrained version. A bare
  name is left unquoted so the common case still reads like something
  a human would type.
  A requirement carrying an environment marker is SKIPPED, not
  guessed at - evaluating markers needs `packaging`, which this file
  must not import, and accusing a user of a package their platform
  does not want is worse than silence. Same rule as `_as_numbers`: go
  quiet rather than guess. And a ModuleNotFoundError naming something
  the library does not declare gets the reason line and NO
  explanation, which is the surviving intent of the test this change
  amended.
  ONE OF MY OWN NEW TESTS WAS WRONG RATHER THAN THE CODE: I asserted
  the advice prose contained the word "pyproj" when it never had
  reason to. Same category as the two break-check predictions I got
  wrong in the 1.53.0 review, and the second time in two releases that
  my expectation, not the suite, was the thing at fault.

- ~~366~~ | DONE v1.53.0, THE 1.52 REVIEW, JOHN'S RULING | THE INDICES
  ARE BARE RATIOS AND NOW SAY SO.
  John: "keep the bare ratios." Kept - no number moves. What changes
  is that the field guide names the convention: a sex ratio is
  conventionally men per 100 women and a child-woman ratio children
  per 1,000, so a column reading 0.968 is read as 1% by anybody who
  expects 97. The `about` text implies per-one ("per woman", "per
  person of working age") and never reaches the attribute table.

- ~~365~~ | DONE v1.53.4, JOHN: "WORTH PERSUING A SOLUTION" | MACHINE
  4 CAN BE RUN TILED, AND THE CAPABILITY WAS SMALL BECAUSE THE SHAPE
  WAS RIGHT.
  364 made a tiled demographic run refuse up front instead of dying
  after the work. **MEASURED BEFORE BUILDING ANYTHING**, as this
  entry asked: a tiled machine-3 run with `groups=["num","den"]`
  already writes `T_num_k` AND `T_den_k` into EVERY tile - 9 tiles,
  both halves present in all of them - and the index is nothing but
  their ratio per origin. So the capability is a PER-TILE POST-PASS
  with memory bounded at one tile, which is the whole point of
  tiling, rather than a new engine.
  `bigrun.map_tiles(out_dir, fn)` is the primitive, and two of its
  three design decisions are the ones that would have been got wrong:
  **THE MANIFEST IS WRITTEN PER TILE, NOT AT THE END.**
  `load_tiled(verify=True)` checks every md5, so a pass that rewrote
  all the tiles and then wrote one manifest would, if interrupted,
  leave a finished continental run in which EVERY tile fails its
  checksum - days of compute unreadable because a post-pass was
  killed. Progressive, an interrupt leaves a run that still READS and
  is merely missing the column on the tiles not reached. Tested by
  raising on the second tile.
  **AND THE md5 IS VERIFIED BEFORE THE READ.** Rewriting a tile
  computes a FRESH checksum, so a post-pass over an already-corrupt
  tile would launder the corruption into a manifest that agrees with
  it from then on, and load_tiled's guard would never fire again. The
  one chance to notice is before the read. Tested by corrupting four
  bytes of a tile.
  **AND THE NEW COLUMN HONOURS THE MANIFEST'S DECLARED dtype.** The
  first version did not: the counts were float32 as declared and the
  index came out float64, because np.where on float64 returns
  float64, so the manifest became a lie about its own tiles. The
  manifest's honesty is a property of the RUN DIRECTORY, not of
  whoever is calling, which is why map_tiles enforces it.
  **ONE ARITHMETIC, AND THE COUNT WAS NOTICED BEFORE THE CODE WAS
  WRITTEN.** run_index and run_indices each built the column names and
  the ratio inline - `T_num_{k}` against `T_{code}_num_{k}` - so there
  were already TWO copies, and giving each a tiled branch would have
  made FOUR. `index_triples` names them and `apply_index` divides,
  once; the in-memory and tiled branches agree BY CONSTRUCTION. That
  is 354 (four copies of the measurement rule), 368 (two of the hint
  rendering) and 377 (seven k readers) not happening a fourth time.
  **THE DIFFERENCE FROM AN IN-MEMORY RUN IS float32 TILE STORAGE AND
  NOTHING ELSE**, measured: machine 3 has stored tiles as float32
  since it was written and its manifest declares it, so the tiled
  index is float32(float32(T_num)/float32(T_den)), which is
  BIT-IDENTICAL to recomputing it that way from the in-memory counts.
  Max relative difference against the float64 answer over 1,980
  origins: 1.3e-07, float32 epsilon.
  TWO SMALLER THINGS. run_indices adds ALL the indices in ONE read
  and write per tile - reading eleven million rows four times to add
  four columns would undo the reason for tiling. And np.where
  evaluates both branches, so a zero denominator made numpy print
  "invalid value encountered in divide" into the user's log for a
  value that is then discarded; silenced where it is meaningless,
  because a warning nobody can act on teaches them to distrust the
  output.

- ~~363~~ | DONE v1.53.4, JOHN'S RULING | AGE BANDS ABOVE 90 FOLD INTO
  90+, AND THE RUN SAYS SO.
  John, 8 October 2026: *"I think we should fold into 90+ - but note
  to user in output if found in the run."*
  **FOLDED ONLY INTO A SIDE THAT ACTUALLY REACHES THE TOP BAND**,
  which is the trap in the ruling as stated. A folder's f_95 belongs
  in an ageing index's numerator, which is 65 and over and
  open-ended. It does NOT belong in a children's numerator, and a
  fold that ignored the side's own range would put centenarians among
  the under-fives - a wrong answer no message would mention, because
  the note would be busy reporting that the fold had happened.
  **THE NOTE MOVED TO WHERE BOTH SIDES ARE KNOWN.** 362 wired it to
  the numerator alone, reasoning that the note is about the FOLDER so
  saying it twice per index would say it eight times for four
  indices. True - and the ruling turned the hole that left from
  cosmetic into substantive: all four built-in indices happen to carry
  the open-ended side on top, but num_spec/den_spec are
  user-overridable, so an index whose DENOMINATOR reaches the top band
  folded cohorts into it and said NOTHING. A fold nobody is told about
  is precisely what the ruling exists to prevent. `above_top_note`
  is asked once, with both specs, and gives one message: the fold
  where anything folds, and 362's original exclusion warning where
  neither side reaches the top.
  WHAT THE NOTE HAS TO SAY, and why it is not optional: folding is
  the right answer and it still CHANGES WHAT 90+ MEANS in whatever is
  published. It becomes the folder's own top, open above 100 rather
  than above 90, and a reader comparing two studies can only learn
  that from the run's own output.

- ~~362~~ | DONE v1.53.0, THE 1.52 REVIEW | A COHORT THE TABLE DOES
  NOT KNOW WAS DROPPED IN SILENCE.
  `columns_for` selected on `int(age) in wanted` and anything else
  fell through. So a folder carrying f_95/f_100 had those people
  excluded from every index while `weight='sexes'` still counted them
  in the reference population - that picks columns by the f_/m_ PREFIX
  alone - and `restricted` reported None. The ageing index came out
  biased down by exactly the oldest cohorts. Verified: sex_ratio over
  a folder with 95 and 100 selected bands 0..90 and said nothing.
  John asked what there was for him to rule here, and the answer is
  that the SILENCE needed no ruling and the remedy does: 363.

- ~~361~~ | DONE v1.53.0, THE 1.52 REVIEW | A FOLDER MISSING ONE SEX
  PASSED THE COMPLETENESS CHECK UNFLAGGED.
  346 closed the BAND dimension: a side is complete only when every
  sex it covers carries every band it covers. It took the SEX SET as
  given - and that set is derived from what is PRESENT, by pick_sex,
  so the absence of a sex could never be a gap. A women-only folder
  produced an "Ageing index", labelled "People 65 and over per person
  under 15", with `restricted: None`. That is 1.45.4's defect - an
  incomplete measure wearing a complete measure's name - surviving in
  the one dimension 346 could not see.
  JOHN'S RULING decided the remedy rather than my guess: his position
  on user-entered specs is that experienced users' choices are not to
  be altered, so the index is COMPUTED and the restriction is WRITTEN
  DOWN. `noted` is deliberately separate from `gaps`, because gaps
  REFUSE and this must not. A 't'-only folder is not restricted: t is
  everybody.
  ONE OF MY OWN 1.51.1 TESTS PINNED THE OLD BEHAVIOUR and failed -
  correctly. It asserted `restricted is None` for a single-sex folder,
  which is now true only for 't'. Amended rather than deleted: the
  half it was written for - that a single-sex folder is not REFUSED -
  still stands and is the half that matters.

- ~~360~~ | DONE v1.53.0, THE 1.52 REVIEW | A SIDE MADE OF TWO RANGES
  WAS REPORTED AS ONE.
  The dependency numerator is "0-14 AND 65 and over". `effective_range`
  forced `hi = None` whenever `plus` was set and returned
  covers = (0, None) - which reads as EVERY AGE, and every age is also
  its own denominator's range. A demographer reading the plan (it is
  attached to the manifest as man["plans"]) would conclude the two
  halves overlap. Worse, forcing hi = None made `exact`
  unconditionally True, which switched OFF the moved-boundary note
  for the one index that uses `plus`: asking for "0-17,65-" dropped
  ages 15, 16 and 17 and still claimed to be exact.
  JOHN ASKED WHAT HE WAS RULING ON HERE and the honest answer was
  nothing - I had over-asked. The columns selected were right all
  along; this was a reporting fault. `ranges` now carries each range
  with its own asked/covers/exact, `exact` is true only when every
  range is, and `covers`/`asked` keep their old shape so nothing that
  reads them breaks.

- ~~359~~ | DONE v1.53.0, JOHN'S RULING | 'fmt' IS REFUSED.
  John: "fmt should not be accepted." 't' IS f+m, so naming it
  alongside either counts those people twice. The rule was written
  down at columns_for - "mixing it with either double counts" - and
  enforced NOWHERE: `fmt:0-14,65-` was accepted, gave 30 numerator
  columns where `fm:` gives 20, and because t repeats f+m the sum came
  out at about twice the truth. Nothing flagged it, because every sex
  carried every band so the completeness grid saw a perfect side - and
  the error message for a bad sex letter even advertised multi-sex
  specs ("or several, like 'fm:15-49'").
  't' ALONE stays fine, and so does 'fm:': a t-only folder is
  ordinary, and the refusal must not catch a correct configuration.

- ~~358~~ | DONE v1.53.0, THE 1.52 REVIEW | A YEAR THE DATA DOES NOT
  CARRY WAS BLAMED ON THE FILENAMES.
  `plan` validated `year` against `years_in(labels)` only when
  `year is None`. Asking for 2030 on a 2020 folder fell through to
  pick_sex, found no cohort, and raised "No columns here look like a
  cohort. Machine 4 needs labels of the form sex_age_year" - about
  labels that are perfectly well formed. It sent the user to check
  their naming convention instead of their year box, and `years_in`
  had the right answer six lines above. Same family as 1.44.6 and
  1.46.2: a message naming the wrong cause costs a support round trip
  and a loss of trust in every other message.

- ~~357~~ | DONE v1.53.0, THE 1.52 REVIEW | `pattern=` OUTLIVED ITS
  CALL AND REPLACED THE REGISTRY IT CLAIMED TO PRECEDE.
  Two faults in two lines. `CONVENTIONS["_user"] = pattern` wrote into
  a MODULE-GLOBAL dict and never removed it, so in QGIS, ArcGIS Pro or
  Stata's embedded Python - where the interpreter outlives the run - a
  second load_folder on a DIFFERENT folder took its labels from the
  first call's regex, and the answer depended on call history.
  Verified: after one patterned load, `parse_name('zzz_whatever')`
  with no arguments at all returned {'sex': 'zzz', '_convention':
  '_user'}. It leaked between tests in one session too.
  And `parse_name(stem, "_user")` made the convention EXCLUSIVE, while
  load_folder's docstring promised the pattern was "tried before the
  registry" - so giving a pattern for ONE oddly-named file silently
  turned WorldPop parsing off for the other 119: every iso3 gone,
  every label changed. The pattern is an ARGUMENT now, tried first and
  then the registry, living exactly as long as the call. An unknown
  `convention=` also stopped raising KeyError, which the docstring
  ("Never raises") had always denied it could.

- ~~356~~ | DONE v1.53.0, THE 1.52 REVIEW | A GROUP EQUAL TO THE
  WEIGHT COLUMN REPORTED A SHARE OF 327%.
  A group column is multiplied by the weight inside build_cells,
  because a group is normally a 0/1 marker. A COMPOSED group is
  already a headcount, so it is converted to a share first - and the
  conversion was skipped when `gname == weight`, to avoid dividing a
  column by itself. The correct value in that case is a share of 1.0:
  the group IS the population. Left raw, build_cells computes
  sum(v * w) - the SUM OF SQUARES of the population - and the reported
  per-cell share came out between 0.0002 and 3.27 where the truth is
  1.0 everywhere. A share of 327% is not a number anybody reads as a
  loader bug. Reachable from a single-cohort folder where the user
  names that cohort as the treatment, or weight='total' with
  groups=['t_15_2026'].
  A group the folder does not have is also NAMED now, rather than
  skipped silently here and met downstream as a bare KeyError from
  pandas.

- ~~355~~ | DONE v1.53.0, THE 1.52 REVIEW | A FLOAT YEAR MEANT TWO
  DIFFERENT WRONG THINGS IN TWO MACHINES.
  A label's year is text, and both comparisons were written as
  `str(year)`. For an int or a string that is right; `str(2020.0)` is
  "2020.0", which no label equals. **Machine 3 then fell through to
  `if same_year:` and KEPT EVERY YEAR, with no message** - 29,685
  people became 59,369, exactly double, which is BACKLOG 273's
  non-reproducibility reachable by passing a float. **Machine 4
  refused**, with 358's message blaming the filenames. One input, two
  machines, two different failures.
  Floats arrive easily: a numeric from a spin box, a pandas value,
  anything through read_csv. The QGIS door happens to use
  parameterAsString and so escaped it; the Python API did not.
  `normalise_year()` is now the one normaliser and both machines call
  it. A year with a real fraction is REFUSED rather than truncated,
  because 2020.5 is not a typo it is safe to guess at. And a year that
  matches nothing is an ERROR naming the years that exist, because
  answering a different question quietly is the defect itself.

- ~~354~~ | DONE v1.53.0, THE 1.52 REVIEW | THE RULE SAID "DECIDED
  ONCE" ABOVE FOUR COPIES OF ITSELF, AND THE FOURTH WAS STALE.
  272 and 232 both came from "which columns are measurements" being
  written as an exclusion list in more than one place. The comment
  left behind said the rule was "decided ONCE" and sat above THREE
  copies; by 1.52 there were FOUR, and the fourth - in
  folder_to_cells, the one function that INFERS THE WEIGHT - was the
  copy nobody updated when keep_index added gx and gy. So
  `keep_index=True` made a perfectly good single-cohort folder
  un-runnable: "this folder holds 3 population columns", two of them
  grid indices, presented to the user as people.
  AND `compose=` BROKE THE SAME PROMISE TWICE. A composed column is a
  SUM OF OTHER COLUMNS, and the exclusion list did not know about it:
  `compose={"copy": [...]}` with `sum_cohorts=True` counted everybody
  in it exactly **2.0000x**, measured, with the composed column not
  even visible in the output - and the same column was prefix-matched
  into `weight='sexes'`, doubling the reference population by the
  second route. John's documented use is
  compose={"under5": [...]} + sum_cohorts, which counted every child
  under five twice.
  `measurement_columns(frame, derived=())` is the one rule now, and
  `derived` is what keeps a composed column OUT of a total and IN the
  table. A test fails if an open-coded copy reappears.

- ~~353~~ | DONE v1.53.0, THE 1.52 REVIEW, AND THE ONE THAT MATTERED
  FOR FEBRUARY | TWO LINES MADE "NOBODY LIVES HERE" THE SAME AS "THIS
  IS THE SEA", AND THREW AWAY EVERY NEGATIVE VALUE.
      arr = np.where(np.isfinite(arr) & (arr != nod), arr, 0.0)
      rows, cols = np.nonzero(arr > 0)
  THE EXPOSOME CASE FIRST, because it is why this was taken now.
  PROPOSALS.md said climate rasters through machine 3 might need
  "nothing new ... worth knowing before promising anything". It was
  worth knowing. Measured on a temperature-anomaly field with a true
  mean of -0.0046 degC: **it came back as +1.19 degC, warming
  everywhere**, because every cooling pixel was discarded without a
  word. A zero-floored PM2.5 surface came back **9.9% high** because
  its clean-air pixels were read as absent. The single claim an
  exposome consortium will test first - population-weighted exposure
  per group, per neighbourhood - ran through the one path that cannot
  carry an exposure surface.
  **AND IT MADE MY OWN GUARD FROM TWO DAYS AGO UNREACHABLE.** cells.py
  refuses a negative population and says, in its own comment, that it
  exists because "rasterfolder hands a raster's own column straight
  in, and a raster's NoData is frequently -9999". It could never fire
  on this path: the negatives were gone before build_cells saw them.
  The guard and the hole were forty lines apart in one package.
  **AND `keep_zero` WAS COMPLETELY DEAD** - both branches. A pixel
  zero everywhere was never created, so keep_zero=True could not
  bring it back; every row that existed had a positive value, so
  keep_zero=False dropped nothing. Documented as working and exposed
  at the continental door. JOHN'S CASE FOR IT, which is why the
  remedy is to implement rather than remove - my first recommendation
  was to remove it and he corrected me: "if we have an instance where
  we used to have populations some years ago, and we want to compare
  how these places are doing now - we should have zeros in the deck.
  Then they add nothing to reference or treatment but they hold a
  place for results." That is HIS OWN RULE from 1.22.2, which the
  Stata path honours through _add_empty_origin_cells. The raster path
  had an option claiming to offer it and offering nothing. dnk_f_15_2020
  in the project's own fixture carries 1,201 observed zeros; every one
  was being dropped.
  THE DISTINCTION EXISTS IN THE FILE - WorldPop ships
  nodata=-99999.0 - so this was never a missing-information problem.
  OBSERVED is the mask now; keep_zero decides only whether an observed
  zero earns a row; negatives are carried as given and SAID OUT LOUD,
  because silence is what let the sign flip pass.
  **THE DEFAULT PATH IS BIT-IDENTICAL**, asserted against the old two
  lines recomputed from the files rather than against stored numbers.
  And the break-check found that the identity has TWO independent
  gates - `pick` and the keep_zero row filter - either of which alone
  preserves it. Recorded in the test, so nobody deletes one as
  redundant.
  ONE INTERACTION NEARLY UNDID IT: eight lines later, the
  keep_zero=False filter dropped rows whose measures SUM to zero or
  less, which for a headcount is "zero everywhere" and for a signed
  surface is not - a pixel holding a single -1.2 degC anomaly sums
  negative and was deleted immediately after being rescued. Fixing one
  without the other would have shipped a fix that did nothing.

- ~~352~~ | DONE v1.52.0, MADE AND CAUGHT WHILE CUTTING 1.52.0 | THE
  BUMP TOOL COULD LEAVE THE REPOSITORY HALF-VERSIONED, TWO WAYS.
  A version lives in a dozen declarations across ten files, and the
  tool wrote and reported them one at a time. Both failures below
  happened in one afternoon and **both were caught by the
  version-agreement tests within a minute**, which is what those seven
  tests exist for and the clearest demonstration yet that they earn
  their keep.
  **FIRST: the tool died part-way through its writes.** The command
  was piped through `head -4` to keep the transcript short; `head`
  exited, the fourth `print` raised BrokenPipeError, and the process
  died with THREE files bumped and NINE not. The repo was internally
  inconsistent and the tool had reported nothing wrong, because the
  report IS the thing that killed it. My misuse, but it exposed real
  fragility: a tool that mutates a dozen files should not depend on
  its own stdout surviving. Every write now happens before any of the
  reporting, so the worst a broken pipe can cost is the summary.
  **SECOND: the rewrite that fixed the first one introduced a worse
  bug.** Planning every declaration from each file's ORIGINAL text and
  then writing them all means two declarations in one file produce two
  full-file texts, and the second write discards the first. Two files
  carry two declarations each - stata/equipop.ado has a `*!` banner
  and `eqp_ado_version`, equipop_test_pass.do has a header and a body
  line - so the .ado came out with its `eqp_ado_version` bumped and
  its banner still at the old release. Edits accumulate per file now,
  keyed by path.
  **AND THE OBVIOUS TEST FOR IT DOES NOT WORK**, which is the part
  worth keeping. A round trip - bump away, bump back, every file
  byte-identical - is the natural check and it is SELF-HEALING for the
  second defect: the patterns match any version string rather than the
  old one specifically, so the return bump repairs whatever the first
  left behind. The break-check proved it, by restoring last-write-wins
  and watching the round trip come out clean. The check that catches
  it is the direct one - after ONE bump, no declared file may still
  mention the old version - and the test now does both, because the
  round trip still catches a declaration the tool knows nothing about.
  Third entry in one release for HANDOVER_15's shape 4: an assertion
  with no counter-example left in the system.

- ~~159~~ | DONE v1.52.0, OPEN SINCE 1.29.6 | THE RECORD CALLED ITSELF
  PROGRESSIVE AND WAS NOT.
  meta.py's own docstring: *"Written progressively: the file exists
  from start_run onward, so a crashed run still leaves a record."* It
  did not. With the default constructor `_path` is None, so every
  `_flush()` in add_input, event, set_data and set_output was a NO-OP
  and nothing reached disk until finalize(). **Both GUI doors used the
  default constructor** - checked at the call sites, neither passed a
  path - so a QGIS or Pro run that died mid-analysis left NOTHING AT
  ALL. The claim was in the docstring, in the manual and in this
  file's own description of item 2; it was never in the code.
  SHARPEST AT THIS MOMENT, which is why it was taken now: 1.51.1 gave
  TWO modules crash-survivable progressive records for exactly this
  reason - bigrun writes each tile's manifest atomically (344) and
  fetching commits after every verified asset (347). The class whose
  docstring claimed the property is the one that did not get it.
  THE DOORS ALREADY KNEW THE DESTINATION. `parameters.get(self.OUT)`
  is read in base.py forty lines before the engine starts, for the
  field-name check. It is now passed to `record(destination=)`, which
  resolves it through a new `meta.sidecar_for()` - and the record
  exists from that moment, saying `"status": "running"`. Verified by
  killing the engine mid-run through the real door: the sidecar is
  there, with the run id, the input row count and the settings the
  engine had bound. `_flush()` is also replace-and-rename now rather
  than `write_text`, which TRUNCATES BEFORE IT WRITES - the same
  window 344 closed in bigrun, met many times per run here because a
  progressive record is written often.
  AND `sidecar_for()` IS WHY THE RULE MOVED. 348 gave each layer of a
  GeoPackage its own sidecar, with the naming written inside
  write_provenance. 159 needs the SAME answer before the run, to open
  the log at the right file. A rule two places need belongs in one, so
  write_provenance calls it too; if they ever drift, the record is
  opened at one path and finalized at another, and a test fails.
  TWO CORRECTIONS TO THIS ENTRY AS IT WAS WRITTEN. Its second half -
  "if a different output path arrives at finalize() the logger writes
  a new file and leaves the first marked running forever" - **did not
  reproduce**: both files said `completed`, because nothing was
  written before finalize in the first place. It describes a symptom
  that only becomes POSSIBLE once the record is progressive, so it is
  now guarded (`moved_from` records the earlier path rather than
  leaving a stale file unexplained). And the honest limit is stated
  rather than papered over: a QGIS temporary layer - QGIS's own
  default - has nowhere to put a sidecar, and the record is printed to
  the log instead.
  ALSO HERE, a 348 follow-on found by needing the same thing twice:
  `record(source=)` in both GUI doors was still passing `sourceName()`,
  the label in the layers panel. 348 fixed that in write_provenance
  and not at the other end of the run. `BaseAlg.source_uri()` now
  holds the rule once and both ends call it.

- ~~158~~ | DONE v1.52.0, OPEN SINCE 1.29.6 | HEX CELLS WERE CHARGED A
  SQUARE'S AREA, AND THE DOCSTRING DEFENDED IT.
  `hex.py` sets `unit_size = hex_size`, the width across flats, which
  is right - that IS the grid's size. `selfpot.radius_for_k` then
  squared it, and its own docstring said "cell side in metres (cells
  are square by construction)". A hexagon 100 m across the flats holds
  **8,660 m2, not 10,000**, so the self-potential radius came out
  **7.46% too large** - 39.89 m where 37.13 m is right at k=50 of 100.
  THE SECOND HALF WAS EASY TO MISS and is the one that would have been
  fixed halfway: `decay_distance` used MEAN_INTRACELL = 0.3826, the
  SQUARE's mean centre-to-point distance. A hexagon's is **0.3510** of
  its width, so the intra-cell decay distance was **9.0% too large** -
  on the mass a run knows least about, carrying the largest single
  weight in the whole calculation. The radius is area-based and the
  decay distance is a mean distance: two constants, two derivations,
  and fixing only the first would have looked finished.
  NOTHING PUBLISHED IS WRONG. Hexes are reachable from Python only -
  one cookbook example - because tests/reachability.py refused them at
  every door FOR THIS REASON: "it should not be offered at a door
  until that is fixed." So this was a blocker with a capability behind
  it rather than a live defect, which is why it could wait eight
  releases and why it was worth taking now.
  THE SHAPE IS THE ONE NEW FACT. `CellData.cell_shape` defaults to
  "square"; `selfpot.SHAPES` maps a shape to an area factor and a
  mean-distance factor; area and mean distance are DERIVED, so an area
  cannot be set that disagrees with the geometry it came from. The
  square factors are exactly 1.0 and the existing constant, **so every
  square run is an identity** - asserted against the pre-1.52 formula
  itself rather than against stored numbers, and the full suite passed
  unchanged. Five call sites across fastcounts and analysis thread
  `cd.cell_shape`; `run_knn` and the two effort engines take a
  DataFrame or a FrictionGrid and cannot receive a hex CellData at
  all, so square there is a fact about the input and now says so.
  THE HEX CONSTANTS ARE DERIVED, NOT MEASURED. Area = (sqrt(3)/2)w2.
  Mean distance = (1/sqrt(3))(1/3 + ln(3)/4) w, from the integral of r
  over one of the twelve congruent sectors where the boundary is
  h/cos(theta). A Monte Carlo check first DISAGREED at 2.4e-4 and the
  closed form was right - quadrature confirms it to 1e-12. Worth
  recording: the sampling noise looked like a discrepancy, and the
  answer was a better instrument rather than a changed constant.
  AN UNKNOWN SHAPE IS REFUSED. `SHAPES.get(shape, square)` is the
  tempting line and it is this item's own defect: silently treating
  something unknown as a square is how a hexagon came to be charged
  10,000 m2 for eight years.
  THE MATRIX ROW CHANGED CATEGORY, which is 333's mechanism working:
  hexes at the GIS doors were a RULING justified by this bug, and are
  now a GAP with a witness (`hexsize` in each door's file), so the day
  somebody adds the box the entry fails instead of going stale.
  Stata stays a ruling, on its own reasoning rather than on 158's.

- ~~351~~ | DONE v1.51.2, JOHN'S QUESTION ON THE 343 RELEASE | A
  REFUSAL THAT WAS RIGHT AND ADVICE THAT WAS WRONG.
  John, reading 343: *"what if a negative population represented the n
  the local has lost - I realize that would clash with some stats but
  not all. Should there be a warning rather than refusal? - you
  decide."*
  **THE REFUSAL STAYS, and his ruling after the reasoning: "negative
  population is refused and for a good reason."** The reason is a step
  EARLIER than statistics, which is the part worth writing down,
  because his instinct was that this is a statistics problem. k counts
  PEOPLE and a neighbourhood is grown outward until it holds k of
  them, so with a negative weight the running total is NOT MONOTONE IN
  RADIUS: it can rise, fall and cross k several times, or never. "The
  radius at which k was reached" stops having one answer, so Dist_k is
  not wrong but UNDEFINED - and every self-calibrating bandwidth reads
  Dist_k. `proportional`, the default since 1.30, divides by the
  crossing cell's population to take a share of it, so a negative
  denominator inverts the share and lands N on the wrong side of k.
  R_k = T_k/N_k flips sign with its denominator. Only THEN come the
  statistics: a weighted mean with mixed-sign weights can land outside
  the range of the data, Gini has no definition for them, and a
  weighted median found by cumulative weight has none when the
  cumulative sum is not monotone. There is no warn-and-proceed that
  yields a number either of us would defend.
  **AND THE ROUTE HE WANTS ALREADY WORKS.** A change or net-migration
  variable is a MEASUREMENT, not a population: it goes in values(),
  weighted by the real headcount in pop(). Verified before answering,
  not asserted - three places 100 m apart, ten people each, change
  [-50, +20, -5], k=20: Mean_chg_20 = [-15, -3.75, 7.5], and -15 is
  exactly (-50*10 + 20*10)/20, with a weighted SD and median alongside.
  **SO THE DEFECT WAS THE MESSAGE.** It gave ONE cause - an undeclared
  sentinel - and one remedy, missing(). For a genuine change variable
  both are wrong, and the user is left with a refusal and nowhere to
  go. 1.44.3's rule: if the code knows the right answer, a refusal
  that only names the problem is a wasted trip. All three negative
  guards - validate_weight, validate_treatment's count rule, and
  build_cells' weights column - now name BOTH causes in the same
  order, say why a negative population breaks the search rather than
  only that it is impossible, and point at values().
  TWO EXISTING TESTS MATCHED A PHRASE OF THOSE MESSAGES and so failed
  when the wording improved while the guards were untouched - shape 7
  in HANDOVER_15's list, added in the same release that then tripped
  over it. Rewritten to assert the behaviour and to check that the
  refusal names the offending value; the wording is pinned by 351's
  own test, where it belongs.
  ALSO HERE, found while checking the figure for 349: **the
  origin-rule measurement existed in THREE copies and one was the
  retracted one.** selfrule.py's header explicitly supersedes an
  earlier 13.4% - a bench run with the neighbour search capped at 48
  cells, which never reached k for remote blocks - and
  `selfrule.CHOICES`, NINETEEN LINES BELOW THAT CORRECTION, still said
  13.4%. Nothing renders it: the doors read doors/help.py, which has
  always said 13.6%, and the shipped equipop.sthlp was checked and
  says 13.6%, so no user ever saw the wrong number. A third copy that
  disagrees with the other two is still 105's and 338's defect, and it
  had already propagated into BACKLOG 349 and HANDOVER_15 before
  anybody compared them - both corrected. A test now pins the copies
  TO EACH OTHER rather than to a literal, so the next correction has
  to move them together or fail.

- ~~350~~ | DONE v1.51.1, FOUND WHILE BUILDING THE 1.51.1 BUNDLE | THE
  RELEASE ZIP SHIPPED A SECOND COPY OF THE WHOLE PACKAGE, AND 1.51.0
  WENT OUT THAT WAY.
  `python -m build` leaves `build/lib/equipop/` and `dist/`, and
  make_release_zip walks the whole tree. **The 1.51.0 working-tree zip
  - the archive John unzips over C:\Data\EQP\ForGit\ and COMMITS -
  contains all 40 modules twice**, the second set frozen at whatever
  version last built. A grep of the tree would find every rule in two
  places: this project's signature defect, arriving through the
  directory layout rather than through the code, and the exact thing
  272, 337 and 346 are each an instance of.
  NOTHING NOTICED, and the reason is worth keeping. 156's check asks
  whether a member can be EXTRACTED - drive letters, backslashes,
  traversal - and every one of these names is perfectly valid. The
  zip opens cleanly. A guard that checks the shape of a name cannot
  see a file that should not be there at all.
  FOUND BY READING THE SIZE. The 1.51.1 bundle's tree zip came out at
  14.8 MB against 1.51.0's 12.0, which is the only reason I looked -
  `dist/` had been swept in because I ran `python -m build` before the
  zip this time. Checking 1.51.0 then showed `build/lib/` had been in
  it all along, by the opposite ordering. **Both orderings are wrong
  and the difference is which artefact you get**, which is why this
  went in the TOOL and not in the release checklist - the tool's own
  docstring makes that argument for 156 and it applies unchanged.
  `build` and `dist` are in SKIP_DIRS, and a test walks a fake tree
  through the builder's member list so it does not depend on whether a
  build has happened in the checkout.
  AND `.gitignore` HELD `dist/` BUT NOT `build/`, which is why the
  committable copy was the one that shipped. It now ignores `build/`,
  `*.egg-info/` and `arcgis/*.pyt.xml` - the last because those
  sidecars are generated by make_help_xml.py and
  test_packaging.py already fails if they are left in the tree, so the
  tree was relying on a test to enforce what an ignore line states.
  STILL JOHN'S, because I cannot see the git history from here: if
  `build/` was ever actually committed, `git rm -r --cached build`
  removes it without touching the working copy. Check with
  `git ls-files build | head`. Same shape as 101's committed stray
  CSVs, which are still in the public repository.

- ~~348~~ | DONE v1.51.1, EXTERNAL REVIEW OF 1.51.0 (F9) | A
  PROVENANCE RECORD THAT COULD NOT NAME ITS OWN OUTPUT.
  THREE FAULTS IN ONE RECORD, all reproduced.
  **One sidecar for every layer in a GeoPackage.** A QGIS destination
  may carry a layer - `out.gpkg|layername=k20` - and write_provenance
  split on "|" and threw the layer away, so k20 and k800 both wrote
  `out.meta.json` and the second run OVERWROTE the first run's
  provenance. Nothing in the survivor said which layer it described.
  Several result layers in one container is the ordinary way to use a
  GeoPackage. Each layer now gets its own sidecar - `out.k20.meta.json`
  - and `run.output.destination` records the full string.
  **The record documented field names the file did not have.** write()
  renames a result column that clashes with one of the input's own
  (316) and DISCARDED the mapping; write_provenance then described the
  engine's result keys. With a source already carrying an N_20 the
  layer held N_20 and N_20b while the record defined only `N_20` - THE
  SOURCE'S COLUMN - so a reader looking up the run's own result found
  somebody else's field described. Two functions written minutes
  apart, neither knowing about the other.
  AND FIXING THAT BROKE THE DEFINITION: `N_20b` matches none of the
  patterns in _COLUMN_DOCS, which describe EquiPop's naming
  convention, so the correctly-named field was documented as "(no
  definition registered)". A definition belongs to the QUANTITY, so
  _describe_columns now looks it up under the original name and
  reports it under the new one, with `[renamed from N_20]`.
  **The input was not identified at all.** The call read
  `sourceName()`, which is the label in the layers panel - "my
  points" - not a path, so add_input() found nothing to measure and
  recorded md5=null. On the stub, which had NO sourceName, it recorded
  the empty string: Path("") resolves to the current directory, _md5
  raised IsADirectoryError, and `except Exception: pass` swallowed it.
  EVERY QGIS PROVENANCE RECORD IN THE SUITE CARRIED `"inputs": []`
  AND NO TEST ASKED. A simulator that omits a method cannot fail the
  code that needs it, so tests/qgis_stub.py now has both.
  `RunLog.set_output()` holds the schema, and render_txt() prints an
  OUTPUT block - the .txt is what a QGIS user reads, so a record that
  names its output only in the JSON names it only for programs.

- ~~347~~ | DONE v1.51.1, EXTERNAL REVIEW OF 1.51.0 (F7) | 291 FIXED
  ONE EXCEPTION TYPE, AND IT WAS THE ONE THAT ALMOST NEVER HAPPENS.
  291 wrapped the fetch loop so "a failure must not erase what
  succeeded" - and caught `FetchError`, the error this module raises
  about its OWN checks. Every way a download actually dies went
  straight past it: a reset connection or DNS failure (urllib raises
  URLError), a timeout, a full disk or read-only folder (OSError), a
  malformed response (HTTPException), or the user pressing Ctrl-C
  forty files into fifty.
  REPRODUCED with URLError on entry 2 of 3: file 1 downloaded,
  verified, and left on disk WITH NO MANIFEST AT ALL - the exact
  situation 291 exists to prevent, by the likeliest route to it. And
  the consequence made it unrecoverable: with no record of where
  pop_0.tif came from, the RETRY REFUSED TO CONTINUE rather than
  attribute bytes it had not observed. Correctly. So the user could
  neither resume nor repeat without moving files aside by hand.
  TWO CHANGES. The manifest is committed AFTER EVERY VERIFIED ASSET
  rather than once at the end, so what is on disk and what is recorded
  never diverge by more than the file being fetched right now - a
  kill -9 has no window to land in. And the wrapper catches whatever
  arrives, records it BY CLASS AND MESSAGE ("timed out" and "no space
  left on device" are different problems with different answers; str()
  of some transport errors is empty), writes, and RE-RAISES THE
  ORIGINAL - a transport failure must not come back dressed as a
  FetchError.
  Break-checked in both halves separately, which showed the per-asset
  commit is the load-bearing one and the broad except adds the
  attribution.

- ~~346~~ | DONE v1.51.1, EXTERNAL REVIEW OF 1.51.0 (F4) | COHORTS ARE
  PAIRS, AND THE CHECK VALIDATED TWO SETS.
  279 asked whether a measure is entitled to its name. The check it
  produced gathered the band numbers of whatever columns were
  selected, compared that SET against the bands needed, and then -
  separately - asked whether each sex appeared anywhere on the side.
  BOTH SETS CAN BE COMPLETE WHILE NO PAIR IS.
  Reproduced on the ageing index with f and m across every band except
  `m_65`: f supplied 65 to the pooled age set, m appeared in the other
  bands, no gap was reported, and "People 65 and over per person under
  15" was published with MEN AGED 65-69 ABSENT FROM THE NUMERATOR. The
  error is not loud - it biases the index by about one cohort of one
  sex, in whichever direction the hole lies, and nothing in the output
  says so.
  MY FIRST PROBE WAS REFUSED and I nearly recorded the finding as
  unconfirmed: giving f only the young bands and m only the old ones
  IS caught, by the per-sex half. The hole is narrower than that and
  needed a second attempt to find.
  Now validated as the GRID - every (sex, band) the side covers,
  which is what the sum ranges over - and the message names the
  missing PAIR, because "fetch m_65" is an instruction and "the
  numerator is incomplete" is not. allow_incomplete still records the
  restriction, so a deliberate one stays legitimate; all four indices
  on a full f/m grid, single-sex folders and 't'-only folders are
  unchanged.
  ALSO HERE, the review's housekeeping item: `effective_range` WAS
  DEFINED TWICE, forty lines apart, so one was dead and nothing said
  which. They were not identical in source - the dead one guarded the
  open-ended top band with an extra branch - and I first reported that
  "the executable logic differs", which was about the SOURCE and not
  the behaviour. CHECKED RATHER THAN ASSUMED: over all 25,650
  (lo, hi, plus) combinations the band table admits, ZERO differing
  results, because _band_end() already returns None for the last band
  start. The simpler one kept; an AST test now fails if a second
  definition reappears. 272's lesson, which expected_bands() right
  above it already carries: a second copy that happens to agree is
  still a second copy waiting to stop agreeing.

- ~~345~~ | DONE v1.51.1, FOUND WHILE FIXING 344 | FIVE ENGINE OPTIONS
  WERE UNREACHABLE THROUGH THE TILED WRAPPER.
  `run_knn_counts` accepts self_potential, overshoot_mode, self_rule,
  seed and decay_eps. `run_knn_counts_tiled` accepted NONE of them, so
  a tiled continental run silently took the defaults and the origin
  rule a spatial regression needs could not be asked for at all.
  FOUND BY TRYING TO FINGERPRINT THEM for 344: recording an option
  that cannot be varied would have been theatre, and asking which
  options the identity should cover is what exposed that five of them
  had no way in.
  Same shape as 340 (r_values honoured on the untiled branch and
  dropped on the tiled one) and 341 (the bridge not telling the effort
  engines which overshoot mode to use) - an option honoured on one
  path and ignored on another, three times on the same branch. Now
  threaded, and tests/test_rule_cross_product.py enumerates engine x
  rule x mode so the next one of these fails a test instead of
  shipping.
  STILL OPEN, deliberately: the continental DOOR (`run_folder`) does
  not expose them on EITHER branch, so this is a uniform gap rather
  than a divergence. Exposing it means new door options, help text and
  four-door parity - a feature, not a correctness fix, and it is not
  going into a correctness release. See 349.

- ~~344~~ | DONE v1.51.1, EXTERNAL REVIEW OF 1.51.0 (F3) | A RESUMABLE
  RUN THAT COULD NOT SEE ITS OWN DATA.
  276 taught resume to compare PARAMETERS, which stopped "k=100 then
  k=200 into the same folder". What it recorded about the data was
  `n_cells` and `unit_size`. REPRODUCED on two 9-cell tables with
  identical geometry and different populations - 10 people per cell,
  then 20 - where resuming the second against the first's folder
  returned the FIRST run's numbers, reported success, and left a
  manifest whose recorded parameters matched perfectly. The answers
  genuinely differed: Dist_20 of 81.2 m against 56.4 m. A three-day
  continental run is exactly where nobody will notice.
  `CellData.fingerprint()` now digests everything the counting engine
  reads - coordinates, population, each treatment's totals and
  observed denominators - in a fixed order as little-endian float64,
  so the digest does not depend on dtype or dict ordering. Value
  arrays are deliberately OUT: the counts engine never reads them and
  hashing a per-person list at continental scale would cost more than
  the run it guards, which is written down in the method so a future
  engine knows it owes this a line.
  AND `calibration` WAS MISSING from the decay record, which is the
  setting that turns a half-life into a beta - two runs at the same
  half_life_m under the two calibrations have different betas,
  different answers, and resume called them the same run.
  `Decay.fingerprint()` now holds that knowledge with the class.
  THE RULE FOR THE IDENTITY, written down: a key belongs there if
  changing it changes a NUMBER, and must stay out if it changes only
  the speed. m_neighbors and chunk are deliberately absent and a test
  fails if they are added - a user who raises chunk to go faster must
  not be told their finished run is a different analysis. The other
  half of a good guard: no correct configuration may trip it.
  ALSO: the manifest was written with `json.dump(man, open(mpath,
  "w"))`, which TRUNCATES BEFORE IT WRITES, so a crash in that window
  left a fragment and the whole finished run unresumable - the one
  failure this module exists to survive. Tiles and manifest are now
  written beside and renamed into place (os.replace is atomic within
  a filesystem), and a failed write leaves no litter for the next run
  to reason about. A hash mismatch also EXPLAINS ITSELF, because two
  hex strings tell a user nothing.
  This closes 119.

- ~~343~~ | DONE v1.51.1, EXTERNAL REVIEW OF 1.51.0 (F2) | THE STATA
  STATISTICS PATH ROUNDED PEOPLE AWAY, AND 118 HAD BEEN OPEN FOR IT
  SINCE 1.29.
  v1.16 implemented "weight by population" by repeating each row
  np.round(weight) times - exact for whole numbers, and WorldPop
  counts are not whole numbers. Three faults, all reproduced:
  **Wrong answers.** Two cells, values [0, 10], weights [0.4, 0.6]:
  the dispatcher reported a mean of 10 where the hand calculation and
  the direct weighted-cells route both give 6.
  **Deleted populations.** Six cells each weighing 0.4: every weight
  rounds to zero, so the ENTIRE POPULATION VANISHED and every row got
  N = 0 and a mean of MISSING. This is 118's WorldPop deletion -
  measured on John's rasters at 50.5% of people lost, 39% in Rwanda
  and 69% in Denmark, so the loss grew with latitude and any
  Europe-against-Africa comparison was biased by construction -
  reaching the Stata door EIGHT VERSIONS after the cell engine learned
  to carry fractional weights. The engine had `value_weights` since
  1.41; the door never used it.
  **A memory ceiling set by the population, not the data.** Two rows
  holding municipal totals materialised 5,000,000 rows, 3.25 s for an
  answer that is two multiplications. Now 0.01 s and nothing
  materialised.
  The weight goes to `build_cells(weights=)` as a NUMBER. Median, Gini
  and the percentiles come out weighted because run_knn_stats reads
  `value_weights` rather than counting entries - checked against
  hand-weighted arithmetic, and fractional against x10-whole weights
  agree exactly, which is the test that distinguishes a weight from a
  count. `Nv_` counts the WEIGHT of rows whose value is observed, which
  is the denominator 168 ruled on. John's rule since 1.22.2 still
  holds: a zero-count row is nobody's neighbour and still gets its own
  results.
  AND A NEGATIVE POPULATION WAS ACCEPTED BY BOTH MACHINES, which
  disagreed about it: weights [-5, 10] gave N = 5 in machine 1 (it
  summed them) and N = 10 in machine 2 (it zeroed the negative). A
  population of minus five is not a quantity, it is a sentinel nobody
  declared - the defect 168 closed for TREATMENTS and left open for
  the weight itself. `validate_weight()` now refuses it in both, with
  168's `missing()` guidance; a BLANK weight stays a blank, because
  Stata's missing arrives that way and John's rule says a row with no
  count still gets results.
  ALSO FIXED, and correct only by accident until now:
  `_add_empty_origin_cells` extended E, N, n, value_arrays and
  binary_sums and left `value_weights` and `binary_valid` SHORT. Both
  were always empty before this change, so the omission was invisible;
  a zero-weight origin plus fractional weights is the combination that
  finds it. Every parallel array now grows.
  This closes 118.

- ~~342~~ | DONE v1.51.0, EXTERNAL REVIEW OF 1.51.0 (F5) | A
  SELF-CALIBRATING DECAY DREW TWO SEEDS AND REPORTED ONE.
  Under `sampled` the seed decides which cells of a crossing ring are
  admitted. A self-calibrating decay runs TWO passes - one to measure
  each row's own Dist_k, one to use it - and each pass drew its own
  seed, so the bandwidth was calibrated from one neighbourhood and
  then applied to a different one, and NEITHER RUN WAS REPRODUCIBLE
  FROM ITS OWN RECORD because the seed it reported was never the seed
  it used. Reproduced on three cells 100 m apart, 10 people each,
  k=15, whole: the whole-ring Dist_15 is 100 m at every origin and the
  calibration pass reported 50-71 m - PROPORTIONAL's answer - giving
  ND_15 [13.75, 15, 13.75] where the same bandwidth supplied as a
  field gives [15, 20, 15].
  The seed is now resolved ONCE in dispatch(), before anything can
  draw its own, and reaches both passes and the provenance record as
  one value. The calibration pass also gets `overshoot_mode`, which it
  was never given.
  AND THE FIX SHIPPED A REGRESSION THAT THE SUITE CAUGHT. Resolving
  the seed means the engine below sees one, so it printed "sampled
  order from seed N" - the line that means YOU chose - and
  "[overshoot] no seed given; drew N. Enter that number to repeat this
  exact run." disappeared from every door at once. My block had
  written its own sentence instead of using `seed_message()`: a SECOND
  VOICE on repeatability, in different words, which is 105's and 328's
  fault exactly. test_6b - written after a deliberate break, for
  precisely this - failed. seed_message() stays the one formatter and
  the block appends a clause.

- ~~341~~ | DONE v1.51.0, EXTERNAL REVIEW OF 1.51.0 (F1) | THE BRIDGE
  DOCUMENTED THREE OPTIONS TO THE EFFORT ENGINES, RECORDED THEM IN THE
  PROVENANCE, AND DID NOT PASS THEM.
  `self_rule`, `overshoot_mode` and `seed` were accepted by dispatch,
  taken by run_knn_friction and run_knn_slope, and dropped in between.
  So a friction or slope run under `originrule(exclude)` included the
  origin, and one under `overshoot(whole)` computed proportional.
  WORSE THAN INCOMPLETE - ACTIVELY MISLEADING, because 293 had just
  taught every run to record its settings from the engine's own
  arguments: the record faithfully wrote down `overshoot_mode: whole`
  while the engine computed something else. A provenance system makes
  a pass-through gap into a false statement.
  The suite had thorough coverage of each option and thorough coverage
  of each engine, and NOTHING THAT CROSSED THE TWO.
  tests/test_rule_cross_product.py now enumerates the pairs, and
  catches this defect as shipped: reverting the fix fails four tests
  that name exactly the two engines and the two options.

- ~~340~~ | DONE v1.51.0, FOUND BY THE 1.51.0 CODE REVIEW | r_values
  WAS HONOURED ON ONE BRANCH AND DROPPED ON THE OTHER.
  The continental door accepted `r_values`, forwarded it on the
  untiled branch, and silently dropped it on the tiled one - so a
  tiled continental run asked for radii produced none, and a
  RADIUS-ONLY tiled request reached the core with no neighbourhood at
  all. Nothing compared the two branches' outputs, which is how a
  parameter came to be honoured on one path and ignored on another.
  See 341 and 345: the same defect twice more on the same branch.

- ~~339~~ | DONE v1.51.0, EXTERNAL REVIEW OF 1.51.0 (F6), MY OWN
  REGRESSION | THE TAU PRODUCER MOVED AND THE CONSUMER DID NOT.
  337 replaced four separate float-to-label formatters with
  equipop/labels.py. In friction.py I changed the producer to
  `tau_suffix` and MISSED THE CONSUMER 110 lines below, which still
  built its own name - so `tau=[2.5]` produced a column the caller
  then looked for under a different spelling. My 337 test covered
  RADII ONLY, so the suite was green on a half-landed rename, which is
  the exact shape of the rename I had warned about in the same
  release's comments. Fixed, and the test now covers tau: [3], [2.5],
  [1000000] and [2.5, 3] all round-trip.

- ~~334~~ | DONE v1.51.0, FOUND BY MARINA'S PULL REQUEST | `g` IS NOT
  THE ANCILLARY KEYWORD, AND 330 SHIPPED FOR A DAY BELIEVING IT WAS.
  330 declared the worked examples and the test data in equipop.pkg
  with `g`, on my belief that `g` meant "ancillary". `g` is the
  PLATFORM-SPECIFIC directive and its syntax is
  `g PLATFORMNAME sourcefile targetfile` - for shipping a different
  compiled plugin to WIN64A, MACARM64, LINUX64. So Stata read
  "equipop_example.do" as a platform name with no files after it, and
  THOSE THREE FILES WOULD NOT HAVE INSTALLED AT ALL from
  `net install`. Marina's pull request had them as `f` all along.
  `f` IS CORRECT: Stata decides what to do with a file from its
  EXTENSION, installing .ado and .sthlp into the ado path and fetching
  .do and .dta with `net get`, which is what the `all` option of
  `ssc install` performs.
  AND THE TEST I WROTE BESIDE 330 VALIDATED THE BUG. It walked the `g`
  lines and asserted the named file existed in stata/ - which it did.
  A test written beside a change encodes the change's assumption, and
  this one encoded a wrong one. That is the seventh unfalsifiable-or-
  wrong test of this stretch and the second that was mine.
  The check now rejects a `g` line whose second word is not a real
  platform name, and requires every .do and .dta in stata/ to be an
  `f` line. Both break-checked against the exact bug.

- ~~335~~ | DONE v1.51.0, MARINA'S PULL REQUEST | A RADIUS-ONLY RUN
  WITH treat() CRASHED BEFORE COMPUTING ANYTHING.
  `foreach ... of numlist `k'` with an EMPTY `k' is a SYNTAX
  ERROR in Stata, not an empty loop. The name-length warning looped
  over k() unguarded, so `equipop, x() y() r(500) treat(HighEdu)` died
  with "invalid numlist has too few elements". k() and r() are each
  optional and either will do (BACKLOG 305), so a radius-only run with
  a treatment is an ordinary thing to ask for.
  THE GUARD ALREADY EXISTED FORTY LINES ABOVE, in the replace drop
  block, with a comment explaining this exact property of numlist. The
  rule was written down in the file and not applied below it - the
  same shape as 330, where the right version invariant sat in a
  comment three files from the code that ignored it. A test now walks
  every numlist loop in the ado and requires the guard, because the
  lesson demonstrably does not stick on its own.

- ~~336~~ | DONE v1.51.0, MARINA'S PULL REQUEST | -replace- LEFT THE
  DECAY OUTPUTS BEHIND, so a second decay() run told the user to "use
  option replace" when they already had.
  The drop list cleared N_, Dist_, T_ and R_ and not ND_, TD_, RD_.
  Her fix covers all three for the k loop and the r loop, and
  correctly does NOT drop Dist_r - a radius run reports no distance,
  because the radius IS the distance (203, John's ruling).
  THE TEST READS THE FAMILIES FROM THE ENGINE, equipop.analysis.NAMES,
  rather than listing them - so a new output family added to the
  engine fails the test instead of quietly escaping the drop list,
  which is how these three escaped it.
  AND MY FIRST VERSION OF THAT TEST COULD NOT FAIL PROPERLY: it
  searched the whole drop block, so deleting the decay drop from the
  k half still passed, because the radius half's `drop ND_r`rl'`
  matched the same pattern. Caught by breaking it. It now checks each
  half separately.

- ~~337~~ | DONE v1.51.0, DIAGNOSED BY MARINA, FIXED DIFFERENTLY | ONE
  RADIUS, FOUR DOORS, FOUR DIFFERENT ANSWERS.
  Marina found that two radii agreeing to six significant digits
  collapse into ONE output column, silently, and that a radius needing
  scientific notation makes an illegal Stata name. Both reproduced.
  THE CAUSE WAS FOUR FORMATTERS FOR ONE LABEL:
    fastcounts._lab            f"{x:g}"
    analysis.record(suffix=)   f"r{rv:g}"
    stata_bridge labs          f"r{r:g}"
    doors/fields._fmt_num      str(int(f)) if whole else str(f)
  `:g` carries six significant digits and goes exponential outside a
  narrow range, so for r(1000000) - 1000 km, an ordinary continental
  radius - Python got N_r1e+06, ArcGIS Pro stored the unreadable
  N_r1e_06, QGIS got N_r1e+06 and STATA CRASHED. And the PREDICTION
  disagreed with the engine: doors/fields promised N_r1000000 while
  the engine made N_r1e+06, so Pro's shapefile-name check and its
  "names will be shortened" warning were computed against a field that
  never appears - in a function whose docstring says it is "validated
  against the real dispatch ... and does not drift into a guess".
  WHY NOT HER FIX. Hers raises ValueError for a label that is not a
  legal STATA name, inside knn_to_rows and dispatch - so every door,
  Python included, is refused r(1000000) because of a Stata naming
  rule, and tests/test_menu.py uses 1e6 deliberately and calls it the
  whole-world radius. The project's own rule, written in dispatch for
  missing codes, is that no engine learns a door's concepts.
  BUILT INSTEAD: equipop/labels.py, one formatter, used by the engine
  AND by the prediction. Six decimal places, never scientific, the dot
  already an underscore, fixed AT THE SOURCE so no name needs
  repairing at an output boundary. EVERY RADIUS ANYBODY HAS USED KEEPS
  ITS NAME - 50, 100, 500, 800, 2800 are unchanged - so no pinned
  number moves. A true collision is still refused, which is her rule
  kept; at six decimal places it fires only when the two radii are the
  same radius.
  AND tau HAD THE SAME EXPOSURE, found with it: friction.py formatted
  effort budgets with `:g` too, so tau(3.5) made the illegal
  Rounds_tau3.5. Same function, fixed together.
  AND THE TEST SUITE WAS PINNING THE BUG. test_menu asserted the
  column "N_r1e+06" - a name no Stata variable and no shapefile field
  may have - for the one radius there that most needed checking, and
  it computed the expected name with the same `:g` the code used. A
  test that derives the expected name the way the code does cannot
  catch a naming fault. The name is now spelled out, and a second
  assertion refuses any result column containing an exponent or a dot.

- ~~338~~ | DONE v1.51.0, MARINA'S PULL REQUEST, TAKEN DIFFERENTLY |
  THE HELP'S EXAMPLES NAMED NO VARIABLES, AND A SHARED EXPLANATION
  NEARLY GOT A SECOND COPY.
  Her PR adds help text for r() and overshoot() as STATA_ONLY entries,
  described as boxes that "had no help entry". THEY HAD ONE: OPTION_HELP
  maps both to keys in equipop/doors/help.py, which is the mechanism
  that makes a QGIS student and a Stata student read the same words
  about the same box. STATA_ONLY REPLACES that text, so her version
  would have given Stata its own copy of two paragraphs - BACKLOG 105's
  fault exactly, where Pro said "additive (sum)" and QGIS said
  "additive (costs add up)". I repeated her claim in my review before
  checking it; the shared entries exist and I was wrong.
  WHAT IS GENUINELY STATA-SPECIFIC IS REAL, THOUGH: overshoot(sampled)
  is refused by the ado. So STATA_EXTRA now APPENDS a door-specific
  sentence to the shared explanation instead of overriding it. The
  permanent duplication of 105 exists only because a QGIS plugin may
  not import the package at load time; the Stata help generator has no
  such constraint, so it should not duplicate.
  TAKEN FROM HER: the examples now say what they run ON - the help
  named no variables, so a reader could not try them - with Kit Baum's
  filenames and the findfile idiom 1.49.3 established, because an SSC
  install puts ancillary files under PLUS and not in the working
  directory.
  ALSO HERS: the help sent users to TESTING_STATA.md, gone since 1.36.
  1.49.3 pointed at `equipop doctor`; her README_STATA.md is the better
  target for an installation question and is now named alongside it.

- ~~333~~ | DONE v1.50.0, FOUND WHILE ANSWERING "WHAT NEXT" | A `no_door` ENTRY CANNOT FAIL, SO THE REACHABILITY MATRIX
  GOES STALE IN THE ONE DIRECTION IT EXISTS TO WATCH.
  tests/reachability.py was written in 1.47.6 after five capabilities
  shipped with no way to reach them. It is the right instrument and it
  has an asymmetry:
    test_1 walks `entry[0] == "door"` and checks the named file still
    mentions the named symbol. A door that DISAPPEARS is caught.
    A `no_door(why, item)` names NO file and NO symbol, so NOTHING
    about it is verified. A door that APPEARS is never noticed, and
    the matrix goes on saying the capability is unreachable.
  IT HAS ALREADY HAPPENED, to the entry the matrix was written for.
  "vector to lattice join (OSM roads, polygons)" declares no_door for
  QGIS, with Pro and Stata pointing at that reason:
    "The headline engine of 1.46.0 and 1.46.1 has no GUI. Reachable
     only from run_osm_friction.py"
  Both GUIs have had it since 1.47.6. Verified in the code, not
  inferred: alg_continental.py offers the `joinlayer` box at line 125
  and calls paths_to_cells at 390; EquiPop.pyt declares joinlayer at
  3759 and _join_layer calls paths_to_cells at 3539.
  WHY THIS DIRECTION IS THE WORSE ONE. A false "no door" costs a
  RELEASE: it tells a future session to build something that exists.
  The backlog's own head did exactly that - "the two finished engines
  with NO DOOR" - and I nearly recommended it as the next piece of
  work before checking the code.
  AND IT IS THE SESSION'S OWN THEME FOUND IN THE SESSION'S OWN
  INSTRUMENT. Four tests that could not fail in 1.48.2-1.49.0, a
  fifth in 1.49.1, my own sixth in 1.49.3 - and the guard built to
  catch unreachable capabilities has an assertion of exactly that
  shape. A matrix that can only be wrong in one direction will be.
  PROPOSED FIX, small:
  (a) A GAP AND A RULING ARE DIFFERENT THINGS and no_door conflates
      them. "Downloading is not a Stata activity" is a ruling - it
      needs no witness and should never fire. "No GUI yet" is a GAP,
      and a gap should be able to announce its own obsolescence.
  (b) So a gap carries a WITNESS: the file that would hold the door,
      and a symbol that must NOT appear in it. For the lattice join
      that is ("qgis/.../alg_continental.py", "joinlayer") - the BOX
      name, not the engine function, because barriers.py and
      EquiPop.pyt both call paths_to_cells for machine 1's barrier
      charging, which is a different capability the matrix's own
      docstring warns against conflating.
  (c) A new test asserts the witness is absent. It fails the moment
      the door is built, which is the moment the entry becomes a lie.
  (d) Audit every existing no_door while doing it: this one was found
      by accident, so the others are unaudited by definition.
  BUILT. `no_door` is GONE as a name, which is deliberate: leaving it
  available as a catch-all would have let the blind spot back in on
  the next entry somebody wrote. Every absence is now `ruled_out(why,
  item)` or `not_yet(why, item, absent=(file, symbol))`, and the
  classification of all 26 forced the audit.
  PROOF IT WORKS: restoring the exact 1.47.6 claim - no QGIS door for
  the lattice join - now fails the suite, naming the file and the
  symbol. Three breaks checked: the false claim, a same_as borrowing
  another door's witness, and a gap declared with no witness at all.
  THE AUDIT FOUND TWO MORE THINGS.
  (a) "accessibility and FCA" was three identical lines reading "No
      door. No demand recorded." - 28 characters, just past the
      25-character minimum, saying nothing a future session could
      act on. kFCA has been in the engine since 1.12.0. Rewritten,
      and the two GUI rows now carry witnesses.
  (b) `diagnostics (the doctor)` had `pro: same_as("qgis")`, which
      cannot carry a witness - it would assert something about a QGIS
      file and prove nothing about Pro. That is the SAME MECHANISM as
      the lattice join's false Pro claim. Two gaps now, two
      witnesses, and the resolver refuses a reference that lands on a
      gap.
  AND THE REPORT NOW SAYS WHICH KIND each absence is: 8 watched gaps,
  18 rulings. It used to print "26 declared gaps, every one with a
  reason", which told a reader nothing about whether what they were
  looking at was a decision or an oversight - the exact distinction
  the file exists to make.
  THE STATA ROW FOR THE LATTICE JOIN became a ruling rather than a
  door, on 296's reasoning: a vector layer put on a raster lattice is
  a GIS operation on GIS inputs, and the result reaches Stata as the
  point table machine 3 writes.

- 321 | OPEN, PROPOSED 23 SEPTEMBER 2026 | WHAT OF PETER'S BURDEN
  METRICS COULD GO IN TOOL 4, AND WHAT MUST NOT.
  John asked which measures from the eBoD literature could be added to
  machine 4 with little fuss. TOOL 4'S OWN DOCSTRING DECIDES MOST OF
  IT: it computes RATIOS OF TWO AGE-SEX GROUPS over a k-neighbourhood,
  and already excludes TFR, ASFR, CBR, CDR and life expectancy on the
  stated ground that "they need vital events and an age-sex folder
  carries stock, not flow".
  BY THAT RULE, ALMOST NOTHING FROM THE LIST BELONGS:
    DALY, QALY, WALY, YLD  need disability or utility weights and a
                           disease model. Not demography, and not
                           ours - they belong with the epidemiology
                           partner, as PROPOSALS.md already says.
    YLL / YPLL             needs DEATHS BY AGE, which is flow. Out for
                           the same reason CDR is out. Adding it would
                           break tool 4's own boundary, and that
                           boundary is why the tool is coherent.
  WHAT COULD GO IN, AND IS GENUINELY LITTLE FUSS:
    (1) EXPECTED COUNTS UNDER A SUPPLIED RATE SCHEDULE. Give tool 4 a
        rate per age band - deaths per 1000, dispensations per 1000,
        from a published table or the user's own - and it returns
        sum(pop_band * rate_band) over the k-neighbourhood. Pure
        arithmetic on stock, NO new data layer, and the machinery is
        the one already there: tool 4 sums arbitrary band sets into a
        group, so this weights each band instead of counting its
        membership.
        THIS IS INDIRECT STANDARDISATION, and it is the thing every
        burden study needs before it starts. With expected counts the
        user computes SMR or SIR downstream as observed/expected.
    (2) THE AGE COMPOSITION AS COLUMNS - population per band over the
        neighbourhood. The input to any standardisation, and the same
        sums tool 4 already forms, emitted rather than divided.
  WHAT IS NOT AVAILABLE, and the distinction is worth stating because
  it is easy to get wrong: DIRECT standardisation needs EVENTS BY AGE
  WITHIN EACH NEIGHBOURHOOD, which is flow again. Indirect works on
  stock alone. So indirect is cheap and direct is impossible here.
  WHY IT MATTERS BEYOND THE PROPOSAL: a crude rate over a bespoke
  neighbourhood mostly measures WHERE OLD PEOPLE LIVE. Age
  standardisation is not an optional extra for a neighbourhood health
  rate - it is what makes one mean anything. That argument holds for
  the EquiEXPOSE prescription work directly.
  NOT BUILT. Awaiting John's ruling on whether tool 4 takes a rate
  schedule, and on what the box should be called.

- ~~327~~ | DONE v1.49.1, FOUND BY JOHN IN THE FIELD | A CSV INPUT
  COULD NOT WRITE A NEW FEATURE CLASS.
  John gave Pro the Northern Ireland 1 km grid as a CSV, chose
  Output = New feature class, named it TrialRun - and the dialog
  refused with "Table input has no feature class to append to - set
  the output table (.csv)" while the feature-class box sat filled in
  directly above the complaint.
  The check asked ONLY whether the INPUT was a table. It never looked
  at the output mode, so the one obvious thing to do with a table of
  coordinates - turn it into points - was unreachable. THE MESSAGE WAS
  TRUE OF APPENDING AND FALSE OF THE RUN.
  FIXED: the .csv is demanded only when the mode is Append to input,
  where there genuinely is nowhere else for results to go, and the
  refusal now says why - "a table input cannot be appended to, a .csv
  on disk is not a feature class" - and names both ways out.
  A TEST THAT COULD NOT FAIL, AGAIN. The first version read
  pm["outtable"].message; the simulator stores (kind, text) pairs in
  .messages and has no .message at all, so the assertion read an
  attribute that is always empty and would have passed however the
  code behaved. THIRD TIME THIS WEEK - after the ensurepip test in
  1.48.2 and the two 306 grep-tests in 1.49.0. Caught by breaking the
  fix, which is the only thing that catches it.

- ~~328~~ | DONE v1.49.1, JOHN'S RULING FROM THE FIELD | A GROUP
  LARGER THAN ITS POPULATION IS NOW REPORTED, NOT REFUSED.
  John: "this is a bit odd the treatment variable is greater than the
  numerator - that is unusual I agree, but not a cause for reject - it
  is the choice of the user - we should be able to have ratios on the
  basis of say 77/66 and not only 55/66".
  HIS OWN DATA IS THE COUNTER-EXAMPLE, and it is a good one. The
  Northern Ireland 1 km grid holds TOTAL_HOUSEHOLD, which counts
  HOUSEHOLDS, and ECONOMICALLYACTIVE, which counts PEOPLE. Two
  working adults in one household and the ratio passes 1
  legitimately: R is then economically active persons per household -
  a real measure, and on the full file its median is 1.333, which is
  right for Northern Ireland.
  THE NUMERATOR WAS NEVER REQUIRED TO BE A SUBSET OF THE
  DENOMINATOR. R_k = T_k / N_k is a ratio; the subset assumption was
  about typical use, not about the arithmetic.
  THREE PLACES SAID IT, AND ONE OF THEM WAS FOUND LAST:
    validate_treatment()        raised on the way in
    check_results_are_possible() raised on the way out
    a bare print() in knn_to_rows, which STILL called it "a data
    error" after the other two had been corrected - found by running
    John's real file end to end, not by any test. A SECOND VOICE
    CONTRADICTING THE FIRST IS WORSE THAN NO VOICE AT ALL, so it is
    gone; validate_treatment already says this, with the ratio.
  THE OUTPUT BACKSTOP'S PREMISE WAS FALSIFIED. It was ruled in "on
  the reasoning that no correct run can trip it". A correct run trips
  it whenever the two count different units. It still reads the
  number the user is about to be handed - that is why it exists - but
  it reports, and it no longer calls the result "impossible", which
  was the word a counter-example could not leave standing.
  WHAT THE NOTE MUST GIVE, and does: the RATIO. That is how a user
  tells a legitimate different-units measure from two variables the
  wrong way round - John's case reads 1.33, a genuine swap of
  total_pop and a group reads 8.33. The magnitude does the
  diagnosing, so the number is reported and the user judges.
  ONE HALF OF THE OLD MESSAGE WAS ALSO WRONG: it offered "or it is a
  0/1 marker and needs treatmode(flags)". A 0/1 marker can only
  exceed the population where the population is ZERO, so that is
  almost never the cause of this trip. Removed rather than repeated.
  STILL REFUSED, and rightly: a NEGATIVE count. A census no-data code
  like -666666666 read as a count is a wrong answer, not a choice.
  AND MY OWN NOTE LEAKED A NUMPY WARNING. The ratio divides by a
  population that can be zero, so the explanation arrived with a
  fragment of a RuntimeWarning attached. Suppressed, and tested with
  warnings-as-errors.

- ~~332~~ | DONE v1.49.3, JOHN'S QUESTION | THE ENGINE FLOOR WAS A
  RELEASE NUMBER PRETENDING TO BE A DEPENDENCY.
  John, after being handed the three-step release order for 331:
  "wouldn't it be easier to generate a new version of equipop and I
  will git it and py it and this will never happen again".
  HALF RIGHT, AND THE OTHER HALF IS THE INTERESTING ONE. He needs no
  new version - 1.49.3 exists nowhere, so releasing it IS his plan
  with one step fewer. But a synchronised release does not make it
  never happen again, because the gap REOPENS AT THE NEXT RELEASE:
  SSC is an email to a person and PyPI is a command, and this
  project's own submission notes say to submit to SSC rarely. PyPI
  ahead of SSC is the steady state, not the accident.
  SO WHAT MAKES IT NEVER HAPPEN AGAIN IS NOT A RELEASE, IT IS A
  DEFINITION. Setup asked pip for `equipop>=<the ado's own version>`,
  which BACKLOG 196 built and which reads "the engine must be as new
  as this release". THAT IS NOT A DEPENDENCY. Two consequences, both
  real and both live:
    1.49.2 TOUCHED THE ARCGIS TOOLBOX AND NOTHING ELSE, and silently
    raised the Stata engine floor to 1.49.2. The commands did not
    need one byte of it.
    AND A FLOOR THAT NAMES AN UNPUBLISHED ENGINE CANNOT BE SATISFIED,
    so pip installs nothing at all - which is 331.
  THE HONEST FLOOR is the oldest engine that satisfies the calls the
  ado makes. Declared by hand as `eqp_min_engine`, beside the list of
  what sets it:
      equipop.stata_bridge   knn_to_rows, to_stata_values,
                             project_for_stata, degrees_warning,
                             zone_span_warning       long-standing
      equipop.doctor.run(ado_version=)               1.40.1
      equipop.decay.Decay(calibration=)              1.48.0
  So 1.48.0, where the ado's own version is 1.49.3. It moves only
  when the commands start calling something new, and only after that
  engine is on PyPI - so it can never name something that is not
  there, and the hard failure becomes IMPOSSIBLE rather than merely
  documented. bump_version.py must not touch it, and a test asserts
  that it does not: a floor that follows the release number is 332
  back within one release and invisible.
  AND THE DOCTOR NOW JUDGES THE FLOOR, not the two release numbers,
  which is the better answer to 330 than the one I shipped two hours
  earlier. Kit's case stops needing a paragraph of reassurance and
  becomes one line:
      engine       : 1.49.3   (the Python package)
      commands     : 1.49.3   (the .ado files)
      needs engine : 1.48.0 or newer - satisfied
  330's calm note survives for a PRE-1.49.3 ADO, which sends no floor
  and is installed on real machines - there the direction of the
  difference is the best signal available.
  THE TRADE-OFF, STATED SO IT CAN BE OVERRULED. The old design failed
  LOUDLY AND EARLY: pip refused, at install time. A hand-maintained
  floor can fail LATER AND LESS CLEARLY - add a call to a newer
  engine, forget to raise the floor, and the user meets an
  ImportError mid-run. So the imports are checked: a test reads every
  `from equipop... import ...` in the ado's python block and asserts
  each name exists in the installed engine, plus the one requirement
  hasattr cannot see - Decay's `calibration` keyword, which is what
  sets the floor today. That cannot prove the floor NUMBER is right,
  only a matrix of old engines could, and that is not worth building;
  it catches the failure that would actually reach a user.
  AND THE ADO MUST NOT BREAK ON AN OLDER ENGINE THAN ITSELF: passing
  min_engine to a pre-1.49.3 doctor raises TypeError, so the call
  falls back to the old signature. The loss is one line of a report.

- ~~331~~ | DONE v1.49.3, JOHN, BEFORE THE REPLY TO BAUM WENT OUT |
  THE ENGINE MUST REACH PyPI BEFORE THE COMMANDS REACH SSC, AND THE
  FIX FOR 330 IS IN THE ENGINE.
  John, reading the batch I had just handed him: "short question -
  this way ado will be 1.49.3 and the py version an earlier version
  which would lead to a conflict, correct?"
  CORRECT, AND WORSE THAN A CONFLICT. PyPI's newest was 1.49.1.
  Verified against the real index rather than assumed:
      pip install --dry-run "equipop>=1.49.3"
      ERROR: No matching distribution found for equipop>=1.49.3
  So `equipop setup` - the FIRST INSTRUCTION IN THE PAPER - would have
  failed outright for every new reader, not warned. I had built the
  whole 330 fix, bumped the version, written the covering letter, and
  not checked the one number that decides whether any of it installs.
  AND THE 330 FIX ITSELF IS IN THE PYTHON PACKAGE. The doctor's entire
  report comes from equipop/doctor.py; the ado only does
  `from equipop.doctor import run`. So sending Kit the ado alone would
  have changed NOTHING HE COULD SEE - he would have run the new
  commands against the old engine, read the same "VERSION MISMATCH"
  paragraph, and reasonably concluded it had not been fixed. A reply
  that says "fixed" and demonstrably is not is worse than no reply.
  RECORDED AS A HARD PRECONDITION, section 0 of SSC_SUBMISSION.md,
  with the two commands that compare the numbers - and in
  tools/bump_version.py, printed at the moment the two versions part
  company, because that is where the mistake is made and not where it
  is discovered.
  THE PIP ADVICE FOR IT WAS CONFIDENTLY WRONG. "No matching
  distribution" fell into the network branch: "pip could not reach
  PyPI, or could not find a build for this Python. Check the network
  and any proxy, and that this Python is 3.10 or newer." All true,
  none of it the cause, and the user cannot fix it in any case. THAT
  IS BACKLOG 319'S EXACT FAULT, WRITTEN IN THE RELEASE THAT FIXED 319.
  Setup now recognises its own floor in pip's message, says the
  mistake is ours, and gives the fallback that works - the newest
  engine there is, plus the doctor to see the gap it leaves.
  AND THE .ADO'S PYTHON BLOCK IS REACHABLE BY TESTS AT LAST. Its own
  comment said so, for releases:
    "Code in here can only be run by Stata, so the Python test suite
     cannot reach it - which is how ... and 173 survive."
  True, and it is why every guard in `equipop setup` - the venv
  detection, the ensurepip advice, the externally-managed advice, the
  whole dispatch on what pip said - was verified by GREPPING THE FILE
  FOR STRINGS. That is how the 1.48.2 ensurepip test came to assert
  nothing, and how a branch of advice could point the wrong way for a
  whole release with tests passing over it.
  The block needs Stata only for `sfi`. Everything else is standard
  library BY DESIGN, because setup runs before the package exists - so
  tests/test_stata_python_block.py stubs sfi, EXECUTES the block, calls
  the functions with pip's real output, and reads the advice back from
  what was PRINTED. Nine tests; each one fails when the thing it
  describes is broken, checked one break at a time. The block's
  comment now says what keeps it reachable: an import of numpy, pandas
  or equipop on a setup path would put it back out of reach and take
  its tests with it.

- ~~330~~ | DONE v1.49.3, FOUND BY C. F. BAUM ON THE SSC RELEASE |
  THREE VOICES CALLING A CORRECT INSTALL A FAULT, AND THE FILENAMES
  THE ARCHIVE COULD NOT TAKE.
  equipop is on SSC. Kit Baum installed it by following the
  manuscript exactly - `equipop setup`, full restart of Stata - and
  wrote: "I am a bit confused as to why the doctor routine identifies
  a version mismatch." He had commands 1.48.2 from SSC and engine
  1.49.1 from pip.
  HE WAS RIGHT TO BE CONFUSED AND THE PACKAGE WAS WRONG. That state
  is not a mismatch to repair: IT IS WHAT OUR OWN INSTALLER PRODUCES.
  `equipop setup` asks pip for `equipop>=<ado version>` - deliberately,
  since 1.48.2, because new commands need a new engine - so pip takes
  the newest there is, which is ahead of SSC whenever PyPI has moved.
  And PyPI and SSC are on separate tracks BY DESIGN, which 1.48.2's
  own note says. So the package shipped an installer that creates a
  state and a diagnostic that calls that state a fault. BACKLOG 328's
  lesson arriving from the other direction: a second voice
  contradicting the first is worse than no voice at all.
  THE DIRECTION IS THE WHOLE DIAGNOSIS, and `!=` cannot see it:
    engine NEWER than commands   expected, harmless. Commands only
                                 ever call engine functions that
                                 existed when they were written.
    engine OLDER than commands   the real fault, and the ONLY one
                                 that produces `ImportError: cannot
                                 import name ...` - which is the
                                 error the old message illustrated
                                 BOTH cases with.
  The loud message now goes only to the second. The first gets three
  calm lines that quote what setup asked pip for, because the two
  version numbers differ on screen and an unexplained difference is
  its own kind of alarm. An unreadable version string makes the
  doctor go quiet rather than guess.
  AND THE ANSWER WAS ALREADY WRITTEN DOWN, WHICH IS THE WORST PART.
  The comment beside the pip call in equipop.ado, put there for
  BACKLOG 196 in 1.48.2, says it exactly:
    "A FLOOR, NOT A PIN... doctor then reports a mismatch that SETUP
     CREATED... THE REAL INVARIANT: the ado is the caller and the
     engine is the library, so THE LIBRARY MUST BE AT LEAST AS NEW AS
     THE CALLER."
  So the reasoning was correct, recorded, and eleven releases old, and
  the diagnostic three files away was never told. Nothing connects a
  comment to the code that should obey it - which is the same shape as
  BACKLOG 103 and 320, two doors disagreeing, with prose as one of the
  doors. The tests now hold the doctor, the test pass and the setup
  floor to one rule.
  AND IT WAS IN TWO MORE PLACES, both found by looking for it:
    equipop_test_pass.do, block 0: `"$EQP_ENGINE" == "$EQP_EXPECT"`.
      So the pass FAILS A CHECK on a correct SSC installation - while
      SSC_SUBMISSION.md instructs the submitter to run it and expect
      every check to pass. Now "at least", with a note when newer.
    SSC_SUBMISSION.md itself, which told the reader to make "the
      doctor's mismatch message current before submitting". It was
      current. It was wrong.
  THE FILENAMES. Kit also renamed two files, and his reasoning is
  correct: "We obviously cannot host a file named example.do on the
  archive... Likewise stata_test_data.dta is not a workable name (as
  it could be used by many package authors)". SSC's filename space is
  FLAT AND GLOBAL. The repository now uses HIS names -
  equipop_example.do, equipop_test_data.dta - so that one file has
  one name everywhere, and a test asserts the prefix on everything in
  stata/.
  WHICH EXPOSED THE CONSEQUENCE HE COULD NOT HAVE SEEN: both sample
  do-files open with `use stata_test_data, clear`, so AS HOSTED they
  fail on their first data line. Renaming the data without renaming
  the reference breaks the example - and the reference was in a file
  he was not renaming. Both now use findfile, which fixes a second
  fault underneath the first: ancillary files install into Stata's
  PLUS folder, not the working directory, so `use equipop_test_data`
  would not have found it even under the right name. The shipped
  examples had only ever been runnable from a clone of the repository.
  AND THE .PKG HAD NEVER LISTED THEM AT ALL. Eleven releases of `net
  install` from GitHub handed over the commands and not the material
  the help and the paper tell people to run, while SSC - whose .pkg
  the archive generates from the zip - handed over both. TWO INSTALL
  ROUTES OFFERING DIFFERENT FILES, and neither route's contents
  written down anywhere. Now declared with `g`, and a test walks both
  the `f` and the `g` lines.
  THE HELP FILE NEVER NAMED THE EXAMPLES either, which left the paper
  as the only place they appeared - by the filenames SSC then changed.
  It names them now, with the findfile idiom, so an SSC user can find
  what they installed.
  AND THE HELP FILE'S SMCL WAS BROKEN, found while editing it. Every
  escaped brace shipped malformed, since the generator was written:
  _smcl_escape chained two .replace() calls and the second ATE THE
  FIRST ONE'S OUTPUT - `{` became `{c -(}`, whose closing brace the
  second replace turned into `{c )-}`, giving `{c -({c )-}` - and the
  line wrapper, which knows nothing about SMCL, then broke the wreck
  across a newline. FIVE OF THEM WERE IN THE FILE KIT READ. str
  .translate does it in one pass and never re-scans its own output.
  Five paragraphs were also being brace-escaped when they WANTED live
  markup, so `{help python}` had shipped as the words rather than the
  link for as long as the line existed; they go through a new _smcl
  that wraps without escaping and refuses to break inside a
  directive. One of those paragraphs pointed at TESTING_STATA.md,
  which has not existed outside stata/historical/ since 1.36 - a help
  file naming a missing file, now on SSC. It points at
  `equipop doctor` instead.
  THE SIXTH UNFALSIFIABLE TEST OF THE WEEK, and my own: the
  output-side check for broken SMCL could not fail once the five
  paragraphs moved off the escaper, because nothing reached it with a
  brace any more - breaking _smcl_escape again changed no shipped
  byte and the test passed over the restored bug. _smcl_escape is now
  pinned by a unit test of its own, and the output check is kept for
  the two regressions it CAN catch.

- ~~329~~ | DONE v1.49.2, FOUND BY JOHN IN THE FIELD, THE SAME DAY AS
  327 | THE CAPABILITY DID NOT EXIST, ONLY THE REFUSAL.
  John ran 1.49.1 - the release that fixed 327 - and met the SAME
  SENTENCE:

      File "C:\Data\EQP\EquiPop.pyt", line 1570, in _run_tool
      arcgisscripting.ExecuteError: Table input has no feature class
      to append to - set the output table (.csv).

  MY FIRST READING WAS WRONG AND WORTH RECORDING. I assumed a second
  COPY of the check on the execution path - that I had fixed the one I
  happened to find instead of grepping for the message. There was no
  second copy. The message at line 1570 was the ONLY thing _run_tool
  did with a table input, because the four lines read

      if kind == "table":   ...
      elif out_mode.startswith("New"):   ...

  and an `elif` after `if kind == "table"` is unreachable for a table.
  So 1.49.1 stopped the DIALOG refusing and left the engine with
  nothing to run. FIXING A VALIDATOR DOES NOT BUILD A FEATURE. The
  toolbox had offered "New feature class" to table inputs for as long
  as the box had existed, and no code anywhere could do it.
  AND THE 327 TEST COULD NOT HAVE CAUGHT IT. It called
  updateMessages() and stopped - a validator test certifies the
  validator. Fifth unfalsifiable-or-insufficient test this week
  (ensurepip in 1.48.2, the two 306 greps and the .message attribute
  in 1.49.0, this). The common shape: the test exercises the layer the
  fix touched instead of the behaviour the user asked for.
  BUILT: arcpy.management.XYTableToPoint, which is the right tool and
  was used nowhere in the toolbox. It carries EVERY column of the
  table across, not only the ones EquiPop read, so John's census
  counts arrive on the layer beside the results computed from them.
  After the conversion `kind` becomes "point" and the whole ordinary
  write path runs unaltered - the shapefile name check, keep-both, the
  ExtendTable write, the verification and the manifest.
  BACKLOG 164 BITES HARDER HERE THAN FOR A COPY. A table has no
  identifier to preserve at all, so the new feature class numbers its
  rows from scratch (1 in a geodatabase, 0 in a shapefile) and `oid`
  was None a moment earlier. The ids are read back in row order and
  used, exactly as the copy path does. The test proves it on
  Dist_200, which VARIES row by row - N_200 reads 200 everywhere
  under `proportional`, which is why the original 164 misalignment
  was invisible for four releases.
  ROWS WITH NO COORDINATE ARE THE ONE BEHAVIOURAL DIFFERENCE, and it
  is refused rather than absorbed: the conversion DROPS them, where
  EquiPop's convention is Null results, so the row count is checked
  and a mismatch stops the run naming the cause. A misaligned write
  is not worth a convenience.
  WHERE THE PROJECTION COMES FROM - the one real design question. A
  table declares none: a CSV of eastings and northings is two columns
  of numbers. BACKLOG 313's rule is never guess a CRS and never be
  silent about a missing one, so there is now a box, "Coordinate
  system of the X/Y columns", and it is honoured in the direction that
  applies here. The NUMBERS never depend on it - distances are in
  whatever unit the columns are - only the MAP does, so a blank box
  writes the feature class with an unknown coordinate system and says
  so loudly, naming both remedies (fill the box, or run Define
  Projection) and the two grids John's audience uses. Refusing the run
  over a metadata field would be 327's mistake again in the other
  direction.
  AND THE SPATIAL REFERENCE IS PASSED EXPLICITLY EVEN WHEN UNKNOWN,
  because arcpy's own default for XYTableToPoint's coordinate_system
  is GCS_WGS_1984: omitting it would stamp Irish Grid eastings as
  degrees of longitude and the layer would claim a projection it does
  not have. An empty SpatialReference() says "unknown", which is
  true. A GEOGRAPHIC choice in the box is refused outright - EquiPop
  measures in metres and a degree is not a length.
  THE BOX WENT ON THE END OF THE PARAMETER LIST, not beside the other
  coordinate boxes: Pro places a box by its CATEGORY, and a parameter
  inserted mid-list renumbers every parameter after it, which silently
  rewires a saved ModelBuilder model.
  TWO THINGS FOUND WHILE DOING IT:
  (a) A TABLE RUN'S MANIFEST COULD NAME A CRS IT NEVER HAD.
      last_crs_text and last_unit are attributes ON _read_input, so
      they survive from one tool run to the next inside one Pro
      session, and the tabular branch set NEITHER - it read them with
      getattr(..., "unknown"), which returns what the last FEATURE
      CLASS read in that session left behind. Read a projected layer,
      then a CSV of Irish Grid numbers, and the second manifest
      records the first run's coordinate system. A manifest exists so
      a result can be reproduced a year later; one that names the
      wrong CRS is worse than one that admits it does not know. Now
      set explicitly on every path, and "unknown - a table declares
      none" when nothing is declared.
  (b) BACKLOG 320 MISSED THE CSV A STUDENT ACTUALLY OPENS. It made
      the name-map and the manifest utf-8-sig and left the RESULTS
      csv - the only to_csv in the toolbox - with no encoding at all.
      That is the file with T_andel_fodt_i_Norge_333 in its header.
      Fixed here.
  ALSO: both output boxes are now honoured. A table input may take a
  .csv AND a new feature class, and gets both, with a manifest beside
  each. Until this release the CSV writer lived inside
  `if kind == "table":` and the feature-class path had already changed
  `kind`, so filling both boxes silently threw one away - the same
  fault as the rest of the item, one line further down.

- ~~316~~ | DONE v1.49.0 | KEEP BOTH: A THIRD
  CHOICE FOR "if result fields already exist".
  THE GAP IS REAL AND EXERCISE 4 WALKS INTO IT. The box offers
  "Overwrite" or "Stop with a message", so running the same k twice
  with two different friction fields - walk and drive, which is the
  whole point of that exercise - cannot be done in one file. The
  second run destroys the first.
  JOHN'S DESIGN, session 12: a third option, and the columns get
  LETTER SUFFIXES. The first keeps its canonical name, the second
  takes `b`, the third `c`:
      R_black_alone_333, R_black_alone_333b, R_black_alone_333c
  HE RULED AGAINST A RUN-LABEL BOX, which Claude argued for on the
  grounds that `b` is not self-describing and is order-dependent.
  His reasoning is better: "it might be that we are running several -
  walk, it may be very complex quickly, user that calls the option
  will be sure to take note, and the log would tell the story". A
  label box charges EVERY run a decision to solve a problem that
  arises occasionally, and the provenance already has two homes - the
  log and the manifest.
  WHAT IT MUST DO, or it becomes this week's failure a seventh time:
  SAY SO. "R_black_alone_333 already exists; wrote R_black_alone_333b
  instead." A user who looks for their column, does not find it, and
  concludes the run failed is exactly the pattern of 309, 310 and
  311. And record the mapping in the manifest, beside the
  shortened-name mapping already written to <output>_EquiPop_fields.
  csv.
  USER'S CHOICE, NOT AUTOMATIC. Claude offered comparing the recorded
  settings and adding a column only when they differ; John chose the
  explicit option. Re-running the same analysis to fix a typo is
  normal and should overwrite, and deciding that by inference is the
  kind of cleverness this project has been punished for.
  BOTH REMAINING DETAILS RULED BY JOHN, session 12:
    - SHAPEFILES CUT, and that is fine. The suffix is added FIRST and
      the existing shortener then treats the suffixed name as any
      other over-length name - which matters, because it already
      resolves collisions with a disambiguating digit (1.46.3). So
      R_black_alone_333 and R_black_alone_333b truncating to the same
      ten characters is a case the shortener already knows how to
      handle, PROVIDED it sees the suffixed name rather than being
      run before the suffix is applied. ORDER OF OPERATIONS IS THE
      WHOLE OF THIS DETAIL.
    - PAST z, USE aa. Then ab, ac. No ceiling, no refusal. John:
      "aa is a good solution". It costs nothing and removes a wall
      somebody would otherwise hit at the least convenient moment.
  NOTE THE EXISTING SCHEME IT MUST NOT BE CONFUSED WITH: 1.46.3
  appends a DIGIT for collisions after shortening
  (h72004_africanamericanalo1_100). Letters here keep the two
  distinguishable, which is a point in favour of John's choice.

- ~~306~~ | DONE v1.49.0 | MACHINE 1'S BARRIER
  CHARGES PER FEATURE, NOT PER CLASS - so it still has the defect
  298 removed from machine 3's join.
  John's ruling in session 12 was that a cell should be charged once
  per CLASS, because OSM cuts one street into a new record wherever a
  tag changes. paths_to_cells() implements that and machine 3's join
  uses it. Machine 1's barrier goes through barrier_to_friction() ->
  paths_to_friction(), which charges ONCE PER FEATURE.
  MEASURED ON REAL DOWNTOWN LA ROADS: 3,975 costed features in a 5 km
  box produce cell costs from 1 to 166, where the friction table tops
  out at 8. The number is mostly a fact about how OSM fragmented the
  roads.
  IT MATTERS BECAUSE EXERCISE 4 IS THE COURSE'S CENTREPIECE - a
  motorway that blocks walking and carries driving - and it runs
  through this path, not through machine 3's.
  THE WORKAROUND WORKS AND IS IN THE EXERCISE: dissolve the roads by
  fclass first, so each class is one multipart feature and is charged
  once. That is a real GIS step and arguably worth teaching. But it
  is a workaround.
  THE FIX: a class-field box on the barrier input, routing to
  paths_to_cells(fidelity="class") when it is set. The engine already
  exists and is geopandas-free; this is door wiring plus the same box
  in Pro.
  WHY IT WAS MISSED: 298 was written against machine 3's join because
  that is where John's question arrived. Nobody asked which OTHER
  paths charge vector features onto cells. The reachability matrix
  lists CAPABILITIES against DOORS; it has no notion of two paths
  that do the same thing by different rules.

- ~~305~~ | DONE v1.47.8 | NEITHER DOOR REFUSED A RUN WITH NO
  NEIGHBOURHOOD, AND PRO DID NOT REFUSE IT AT ALL. John hit this on
  the first run of Exercise 1: his k values had gone by the time he
  reached the foot of Pro's dialog, Pro was content, and the failure
  arrived forty lines into a traceback reading "give k_values and/or
  r_values" - words naming ENGINE ARGUMENTS rather than boxes, so the
  message did not even point at the dialog.
  BOTH BOXES STAY OPTIONAL, John's ruling: "no need to restrict
  missing k, think that there may be only r". A radius-only run is a
  perfectly good question. What is required is ONE OF THE TWO, and
  nothing said so.
  Pro's updateMessages checked shapefile field limits and null
  handling and never checked that the tool had a neighbourhood to
  measure. QGIS did refuse - but inside processAlgorithm, AFTER Run,
  so the answer came as a red exception rather than a blocked button;
  it now implements checkParameterValues, which QGIS offers for
  exactly this and which no door had ever used.
  WHY THE VALUES VANISHED IS NOT OURS, as far as can be told. Every
  place the Pro door clears a parameter was checked: the coordinate
  trio when the layer changes, and machine 2's `measures`. Neither
  touches k, which sits at index 14 and is read by name. The likely
  cause is Pro resetting a cached dialog because THE PARAMETER LIST
  CHANGED - originrule was added in 1.47.4 - which is what the
  ArcGIS guide's "remove the toolbox and add it again" exists for.
  Recorded as unexplained rather than guessed.
  AND THE EXERCISE NAMED THE WRONG BOX. It said "Neighbourhood sizes,
  in people", which is MACHINE 3's label; machine 1 in Pro says "k
  values (space-separated, e.g. 200 1600)" and in QGIS "3 - k -
  neighbourhood sizes in people". THREE NAMES FOR ONE CONCEPT across
  two doors and two machines, which is how the wrong one got into the
  document. door_parity checks that both doors HAVE a box called `k`;
  it does not check that they call it the same thing to a human.
  That gap is real and is not closed here.
  ALSO: the simulator had no checkParameterValues at all, so a door
  overriding it could not be tested - and one calling super() would
  have died with AttributeError in the field while every test passed.
  Sixth sparse-stub gap this release series.

- ~~304~~ | DONE v1.47.7 | A ROUNDING ERROR BROUGHT BACK Dist_k = 0.
  FOUND BY BUILDING THE TEACHING MATERIAL, on John's LA County
  blocks: 1,213 of 75,109 reported the hundred nearest people as ZERO
  METRES AWAY.
  Under `proportional` the crossing cell contributes a FRACTION, so
  the neighbourhood total arrives as 99.99999999999999 rather than
  100. All three self-potential guards read `n >= k`, which is FALSE
  for that float - so the correction never fired and the distance
  stayed 0.
  THIS IS BACKLOG 191's DEFECT RETURNING THROUGH A DIFFERENT DOOR.
  A zero distance makes k stop distinguishing origins, which is the
  whole reason self-potential was built in 1.29.5.
  IT NEEDED DENSE DATA. LA County averages 131 people per block and
  41% of origins reach k INSIDE A SINGLE CELL; no fixture in the
  suite was dense enough to produce the rounding, which is why five
  releases of self-potential work never saw it. The exercise asks a
  student to sort by Dist_100 and find the smallest - they would have
  found a zero on the first try.
  Fixed in all three places (fastcounts, and twice in analysis) with
  a 1e-9 tolerance, and guarded by a fixture whose FIRST assertion is
  that it still produces the rounding - a test for a float problem
  that stops producing the float stops being a test.
  THE GENERAL SHAPE, AND IT IS THIS SESSION'S SIXTH: `>=` against a
  value that arrives by summation is a comparison against a number
  nobody computed exactly.

- ~~303~~ | DONE v1.47.6 | THE GUARD WAS DEFEATED BY THE ROUTINE
  THAT RAISES THE QUESTION. TEACHING.md and PROPOSALS.md each carry
  `**Last updated: <version>**`, and a test compares it against
  pyproject.toml so a release cannot pass while a planning document
  has drifted. It was written this same session, with the priority
  list's eleven stale releases as the reason.
  IT COULD NEVER FIRE. Versions are moved with a blanket sed over
  every file containing the old string - and that includes the "Last
  updated" line. The one thing meant to prove A HUMAN HAD LOOKED was
  being answered by the same command that asked the question. Found
  when the bump to 1.47.6 left the test green on documents nobody had
  read.
  A CHECK THAT THE ROUTINE UPDATES AUTOMATICALLY IS NOT A CHECK.
  Before trusting a guard, ask what the normal workflow does to it -
  which is a different question from whether the guard is correct,
  and this one was correct.
  FIXED BY MAKING THE RULE EXECUTABLE: tools/bump_version.py moves
  the version everywhere it must move and skips the status documents
  by name, so their line moves only when somebody reads them. A test
  asserts the NEVER list still holds both. The old blanket sed also
  rewrote BACKLOG.md and MANUAL.md, where "DONE v1.29.5" is a FACT
  ABOUT THE PAST and must not be rewritten; the tool skips those too.

- ~~301~~ | DONE v1.47.6 | MACHINE 6 COULD NOT SEE A FILE
  GEODATABASE. John supplied CalidataOSM.gdb - four OSM layers for LA
  County, the format he actually uses in ArcGIS Pro - and the
  inventory returned EIGHTY-SIX ROWS OF GARBAGE: a00000001.gdbtable,
  a00000001.gdbtablx, the .lock files, all listed as "other", while
  the four layers were never seen at all.
  A .gdb IS A DIRECTORY AND os.walk YIELDS FILES. `.gdb` was already
  in the VECT tuple, so the code LOOKED right; the check simply never
  ran against a directory. Now matched from _dirs, pruned so the
  internals are not walked, and sized by summing the folder. Four
  rows instead of eighty-six.
  EVERY FIXTURE UNTIL NOW WAS SHAPEFILES AND GEOTIFFS, and both of
  those are files. The tool was built, tested, documented and shipped
  in TWO DOORS without once meeting the format its author uses daily.
  THE FIRST VERSION OF THE TEST COULD NOT FAIL. It wrote a real .gdb
  with pyogrio and SKIPPED - no OpenFileGDB write support in this
  environment - so the deliberate break sailed straight past. What is
  being fixed is the WALK, not the reading, so the fixture is now a
  directory with the right name and plausible internals. Whether GDAL
  can open it is a separate question, and the answer being "no" is
  part of the assertion: the row must still be ONE row and must carry
  its error.

- ~~302~~ | DONE v1.47.6 | THE GEOPANDAS-FREE JOIN WAS ONLY TESTED
  WHERE GEOPANDAS WAS PRESENT. tests/test_vectorjoin.py calls
  pytest.importorskip("geopandas") at MODULE level, so every test in
  it - including two written for paths_to_cells, which needs neither
  geopandas nor shapely - was skipped on exactly the machine where
  the freedom matters.
  A TEST THAT ONLY RUNS WHEN THE DEPENDENCY IS PRESENT CANNOT SHOW
  THAT THE DEPENDENCY IS UNNECESSARY. Moved to
  tests/test_vectorjoin_free.py, which imports neither, plus a guard
  that reads its OWN imports with ast. The first version of that
  guard scanned the source for the string "import geopandas" and
  failed on its own list of banned words - a small lesson about
  checking for a name by looking for its letters.
  THE TESTS THEMSELVES ARE THE COURSE'S. John's exercise 3 has a
  motorway BLOCKING WALKING and CARRYING REGIONAL TRAFFIC - same
  feature, opposite signs - so the value field takes negatives, and
  nothing had ever tried one. They work: +8/+8/+1 collapses to 9,
  -5/-5/+1 to -4, and a cell whose charges cancel to exactly 0 KEEPS
  ITS ROW rather than vanishing.

- ~~300~~ | DONE v1.47.6 | pyproj WAS NEVER MENTIONED IN ANY INSTALL
  GUIDE, and a student lost an evening to it.
  INSTALL.md's rule ONE is "--no-deps, always", and it is right:
  without it pip upgrades the host's numpy or scipy, which is what
  broke QGIS's scipy and Stata's pyproj. THE RULE HAS A CONSEQUENCE
  NOBODY WROTE DOWN: --no-deps also skips the dependencies that are
  not already there, and there is exactly one - pyproj. ArcGIS Pro,
  QGIS and Stata all ship numpy, pandas and scipy; none ships pyproj,
  which the package requires.
  THE STUDENT GUIDE MADE IT WORSE by verifying `import numpy, pandas,
  scipy, pyproj` at the end of an install that never fetched pyproj,
  and saying only that "the instructor must prepare those
  separately" - without naming which. So the instructor could not
  prepare it either. Mercy Lanz hit exactly this on 1.46.4: three
  imports fine, the fourth missing, and she did the right thing and
  asked before installing anything.
  FIXED in INSTALL.md (all three hosts), in the student guide, and
  guarded by a test that reads `dependencies` from pyproject and
  requires every name to appear in INSTALL.md - so a dependency added
  later cannot go unmentioned the same way.
  A CLAIMED CONTRADICTION THAT WAS NOT ONE. Claude reported that
  INSTALL.md told students to use --user while ARCGIS_GUIDE said
  --user strands packages where Pro never reads. Both statements
  exist; they are in DIFFERENT SECTIONS for DIFFERENT HOSTS - --user
  is correct for QGIS's OSGeo4W and wrong for Pro, and the Pro
  section already uses PYTHONNOUSERSITE and explains why. Claimed
  from a grep hit without checking which section the line was in.
  Fifth time in one session that a claim was written from what the
  code ought to look like with the answer a line away.

- 296 | ~~RULED OUT~~ SESSION 12, FOUND BY THE MATRIX | THE STATA
  COMMAND CANNOT REACH FRICTION OR SLOPE, THOUGH THE BRIDGE CAN.
  `stata_bridge` takes `engine="friction"` with a friction_file and
  `engine="slope"` with a DEM and a walking model. `stata/equipop.ado`
  mentions `barrier` ZERO times, `friction` ZERO times, `slope` ZERO
  times; the single `dem` in the file is the word "demands" in a
  comment. So the effort engines are finished, tested, reachable from
  Python, QGIS and Pro - and the Stata command simply never grew the
  options.
  THE SIXTH UNREACHABLE THING FOUND THIS SESSION AND THE FIRST FOUND
  BY A TOOL. The other five - inventory.py, vectorjoin.py, RunLog,
  the Pro sidecars, make_help_xml.py - all turned up by accident, one
  at a time, in a session that was not looking for them. This one was
  found by tests/reachability.py within a minute of its first run,
  and it was found IN CLAUDE'S OWN DECLARATION: the matrix was
  written claiming a Stata door for both, from memory, and the check
  refused it.
  JOHN'S RULING, SESSION 12: "stata doors for friction and slope is
  not needed - those are GIS features, and not needed in statistics".
  A DIFFERENT REASON FROM 205 AND WORTH KEEPING SEPARATE. 205 was
  ruled out because Stata does the job BETTER - it computes weighted
  statistics natively. This is ruled out because the job is not
  Stata's AT ALL: barriers and terrain are about how a landscape is
  crossed, which is a question you ask of a map. The two rulings
  together describe the division of labour this project settles on -
  EquiPop builds neighbourhoods, GIS handles geography, Stata handles
  statistics - and a future session proposing either door should read
  both before raising it again.
  SO THE MATRIX NOW RECORDS A DOOR DELIBERATELY NOT BUILT rather than
  a capability missing, which is the distinction it exists to make.

- ~~293~~ | DONE v1.50.0, FOUND v1.47.6 | RunLog IS DEAD CODE, AND IT
  IS BACKLOG ITEM 2. equipop/meta.py - "the per-run metadata log (backlog item 2,
  design as agreed)" - is complete, documented, exported in __all__,
  and CALLED BY NOTHING AND TESTED BY NOTHING. No door, no engine, no
  runner constructs a RunLog.
  FOUND while looking for somewhere to record the self rule of 290.
  There was nowhere: analysis runs have no provenance record at all,
  which is also why `overshoot` has never been recorded despite
  moving every k-based number since 1.30.
  NOT FIXED IN 1.47 DELIBERATELY. Building a provenance system inside
  the self-rule item is the scope creep that produced engines without
  doors in the first place. It needs its own release and its own
  decision about which door writes the sidecar.
  THIRD UNREACHABLE CAPABILITY FOUND THIS SESSION, after
  doors/inventory.py (269, shipped 1.45.0) and vectorjoin.py
  (280/282). This one is the oldest by a wide margin. The pattern is
  now the project's characteristic failure: a thing is built, tested,
  and never connected to a way of reaching it.

  BUILT v1.50.0, AND THE DIAGNOSIS WAS WRONG IN A USEFUL WAY. "Analysis
  runs have no provenance record" is not quite what was true. PRO HAD
  ONE - an _EquiPop_run.csv beside every output since 1.26 - so the
  real state was TWO IMPLEMENTATIONS OF ONE JOB, which is BACKLOG
  103's shape with a dead one and a live one. And the live one was
  HAND-MAINTAINED, so it drifted exactly as a hand-written list does:
  `overshoot` moved every k-based number from 1.30 and appeared in no
  record until 1.47 because nobody added it; 148 is the same story
  told larger - the manifest recorded k, cell size, decay and barriers
  and NONE of the settings that define the numbers, so two runs could
  carry identical records and different answers, and Claude tried to
  use two of John's to settle which of his runs had differed and could
  not.
  SO THE FIX IS NOT "WRITE A RECORD". It is that THE RECORD COMES FROM
  THE ENGINE'S OWN ARGUMENTS. `dispatch(..., provenance=runlog)` fills
  it from `locals()` at entry - the arguments AS BOUND, defaults
  included - so a parameter added to the engine appears in the record
  the same day with no door touched. A setting the caller never
  mentioned is recorded as the value that actually ran, which is what
  a record is for: self_potential changes every Dist_k and decay_eps
  changes how far the search goes, and no door passes either when the
  default suits it.
  A TEST WALKS dispatch's OWN SIGNATURE and fails if any parameter is
  missing from the record. That is the anti-drift guard this item has
  needed since it was raised as item 2.
  EACH DOOR, AND ITS OWN SHAPE:
    python  RunLog directly, as the module docstring always showed.
    qgis    .meta.json + .meta.txt beside the output - this door wrote
            NOTHING before. With a temporary or in-memory destination,
            which is QGIS's own default, there is nowhere to put a
            sidecar, so the settings are PRINTED instead of silently
            not existing.
    pro     the engine's rows appended to the existing CSV under an
            `engine.` prefix. NO SECOND SIDECAR: that CSV is the file
            a user already looks for, and two files describing one run
            is how this item's problem started. The two overlap on
            purpose - cell_size_m against engine.unit_size - because a
            disagreement between what the dialog believes it sent and
            what the engine received is a bug class nobody could see
            before.
    stata   a PRINTED note, John's ruling, because a Stata run writes
            variables into memory and may produce no file at all, and
            `log using` is where a Stata user's reproducibility
            already lives. Plus r(overshoot), r(originrule) and
            r(provenance) - the first two being the settings this item
            was raised about, returned as the EFFECTIVE value so an
            unset option reports the default that ran rather than an
            empty string.
  THE STATA SIDE IS SPLIT IN TWO BLOCKS ON PURPOSE. The r() values
  need only overshoot.DEFAULT (1.30) and selfrule.DEFAULT (1.47); the
  printed note needs equipop.meta.record, which is new here. So the
  note degrades to one line on an older engine rather than forcing
  eqp_min_engine up and making `equipop setup` demand a version nobody
  has yet (332). A note is a convenience; an install that cannot
  complete is not.
  WHAT IS NOT IN THE RECORD: the data. A population column is not a
  setting, and a sidecar is not the place to copy one - megabytes of
  numbers already in the input file, plus a disclosure question nobody
  asked for. Arrays are summarised: count, dtype, how many present,
  the range. A test caps the record at 20 kB on a 500-row run with a
  treatment column, which is what catches a future change that starts
  dumping them.
  AND A None IS KEPT RATHER THAN DROPPED. "overshoot_mode was not
  passed" and "overshoot_mode was whole" are different runs; a record
  that omits the first cannot say which happened, which is how a door
  that named no mode became impossible to measure against an answer
  key (99). The PRINTED note drops them, and only the printed note,
  because on screen a None is noise and in a record it is evidence.
  FOUND WHILE DOING IT: the record named the WRONG ENGINE VERSION.
  _versions() asked importlib.metadata, which reads dist-info - and
  dist-info lags the source on every editable install and on any
  machine where the toolbox was copied in by hand. Measured: it said
  1.49.1 while __version__ said 1.49.3, so a provenance record would
  have named a version that did not produce it. __version__ is also
  the string the doctor and the .ado compare, so anything else here
  would have made the record disagree with the rest of the package
  about which engine ran.
  AND 333's WITNESS CAUGHT THIS WORK AN HOUR AFTER IT WAS BUILT. The
  three `not_yet` entries for run provenance fired the moment the
  doors were wired, in the same session. An hour earlier they would
  have gone on claiming the capability was unreachable - which is
  precisely what the lattice join did for three releases.

- 194 | OPEN | THE 1.41 PLAN IN HANDOVER 11 CONTAINED TWO ERRORS THAT
  WOULD HAVE BEEN BUILT VERBATIM. Both found by the external review,
  neither would have raised an error.
  (a) CATEGORY SYNTAX. The handover proposed
  treatspec("A: 5 6 7; B: 1 2"). parse_treat_spec splits groups on
  ';' and values on ','. That string parses to {'A': ['5 6 7'],
  'B': ['1 2']} and matches ZERO ROWS. Verified. The working form is
  treatspec("A: 5, 6, 7; B: 1, 2"). Keep commas - whitespace makes a
  label containing a space ambiguous.
  (b) outside(zero) SEMANTICS. The handover called it post-processing
  that should "blank the results of excluded rows, or zero them".
  THAT IS THE WRONG GEOGRAPHY. John's rule, already in
  doors/help.py and implemented in alg_counts.py as
  `weight = base * pop_mask`: an outside row contributes ZERO to the
  reference population and is nobody's neighbour, but it REMAINS AN
  ORIGIN and receives real results for what surrounds it. A library
  outside an eating-place reference population still has eating
  places around it. It is INPUT SHAPING before dispatch, not output
  editing.
  THE LESSON: a handover can carry a wrong instruction forward and
  nothing catches it. Run the example against the parser and read the
  existing implementation before building from a plan.

- 195 | OPEN | STATA PARITY MOVES AHEAD OF THE CATEGORY RUNG. The
  reviewer's argument beats the previous ordering: the category work
  touches the exact seam where door drift has happened before -
  reference membership, treatment membership, units, outside rows,
  group names, generated outputs. A third implementation added before
  Stata is in the answer key invites another plausible-but-different
  result. Extend tests/door_parity.py first, extract ONE shared
  category/reference preparation helper from the GIS doors, then
  implement Stata through it.

- ~~196~~ | DONE v1.48.2 | `equipop setup` WAS NOT VERSION-PINNED AND
  RETURNS SUCCESS ON A PIP FAILURE. It runs `pip install --upgrade
  equipop`, so a 1.40.4 command file can pull a newer engine after a
  later PyPI release - doctor detects the mismatch afterwards, but
  setup created it. And it prints "PIP FAILED" then returns normally,
  so a scripted install has no failure code.
  DONE v1.48.2, WITH ONE CHANGE TO THE FIX THIS ENTRY PROPOSED. Not
  `equipop==<version>`: an exact pin would stop an older ado ever
  receiving a bug-fixed engine, which is the wrong failure. THE REAL
  INVARIANT IS A FLOOR - the ado is the caller, the engine is the
  library, so the library must be AT LEAST AS NEW as the caller:
  `pip install "equipop>=<ado version>"`. That permits fixes and
  forbids the case that actually breaks, an ado calling something its
  engine does not have. The run now says which floor it asked for.
  Both failing exits set a local the ado turns into `exit 601`.
  RAISED IN PRIORITY BY THE SSC SUBMISSION, and that is the general
  lesson: from GitHub the ado and engine arrived together from one set
  of instructions, but on SSC they sit on SEPARATE UPDATE TRACKS -
  adoupdate for the commands, `equipop setup` for the engine - so
  drift stops being an accident and becomes the normal state. The same
  item was cheap to ignore for months and became urgent the week the
  distribution channel changed.

- ~~322~~ | DONE v1.48.2, SAME RELEASE | THE UNKNOWN-SUBCOMMAND
  MESSAGE SENT USERS TO A RAW GITHUB URL. It is printed at the exact
  moment a confused user is reading carefully, and once the package is
  on SSC it was the wrong instruction - `adoupdate` only knows about
  packages installed from a site. SSC first now, GitHub kept below it
  as the development route and as the answer while an SSC update is
  still propagating. README_STATA.md had the same single route.
  NOT IN THE BACKLOG BEFORE THIS RELEASE: found by reading the ado's
  user-facing text with the submission in mind rather than by a test.

- ~~324~~ | DONE v1.49.0, FOUND BUILDING 316 | THE QGIS DOOR APPENDED
  A DUPLICATE FIELD NAME AND NOTHING DETECTED IT.
  base.py's write() copies the source's fields and then appends the
  result names - blind. QGIS writes a NEW layer each run, so feeding
  a previous run's output back in, which is EXACTLY what comparing
  walk against drive requires, produced TWO FIELDS OF ONE NAME in the
  output and left OGR to resolve it however it liked.
  316 was written about Pro, where the box offered Overwrite or Stop.
  Nobody asked what the OTHER door does with a repeated name - the
  same blind spot as 306, where the class rule was given to machine
  3's join and never to machine 1's barrier. TWO DOORS DOING ONE
  THING BY DIFFERENT RULES is now three findings deep (306, 320,
  324) and the reachability matrix cannot see it: it lists
  CAPABILITIES against DOORS, not the paths inside them.
  FIXED: QGIS needs no box, because with a new layer every run there
  is no overwrite to choose - keeping both is simply correct. Pro,
  which appends to the input, keeps the explicit choice John ruled
  for.
  AND THE LOGIC LIVES IN equipop/doors/fields.py, not in either
  door - the lesson of 320, where Pro had a locale-proof number
  reader from 1.16.7 that QGIS never received because the code sat in
  the .pyt.
  CAUGHT ON THE WAY: renaming `order` in the write loop would have
  broken the value lookup, since result[name] is read below it. The
  written name and the result key are separate now.

- ~~325~~ | DONE v1.49.0, FOUND BY BREAK-CHECKING 316 | keep_both()
  HAD AN UNBOUNDED `while True`, SO A BAD SUFFIX WAS A HANG.
  The loop asked letter_suffix for name after name until one was
  free. That is correct only while letter_suffix keeps producing NEW
  names - and a deliberate break that made it return a constant
  turned the loop into an INFINITE ONE rather than a failure. The
  break-check did not report a failing test; it reported a timeout.
  A HANG INSIDE ARCGIS PRO IS A FORCE-QUIT AND LOST WORK, which is
  worse than any error message. Bounded now, and it raises with the
  reason instead of spinning.
  THE LESSON IS ABOUT THE METHOD, NOT THE LOOP: breaking a fix on
  purpose found a defect that the fix's own tests, all passing, could
  not have found. A test suite checks that the code does the right
  thing; breaking it checks what happens when it does the wrong one.

- ~~326~~ | DONE v1.49.0 | TWO OF MY OWN TESTS WERE TOO WEAK, AND THE
  BREAK-CHECK SAID SO.
  The first version of the 306 tests asserted that the strings
  "class_field" and "fidelity=CLASS" appeared SOMEWHERE in
  barriers.py, and that "barrierclass" appeared somewhere in
  alg_counts.py. Both survived a break in one place, because the
  other occurrence of the same string was still there. Two of three
  deliberate breaks passed.
  REPLACED WITH A BEHAVIOURAL TEST that RUNS the QGIS barrier through
  the simulator on John's own junction example - 'unclassified' three
  times and 'trunk_link' twice - and asserts 30 per feature against
  11 per class. All three breaks now fail it.
  THE SAME WEAKNESS AS THE ensurepip TEST in 1.48.2, which only
  checked that the word appeared. A GREP IS NOT A TEST: asserting a
  string exists somewhere in a file proves nothing about whether the
  path that uses it runs.
  AND THE FIRST BEHAVIOURAL VERSION WAS REFUSED BY A GUARD THAT WAS
  RIGHT: an 80 m barrier at 100 m cells "cannot block anything", said
  the extent check, correctly. The test geometry was wrong, not the
  code.

- ~~323~~ | DONE v1.48.2 | MACHINE 3 COULD NOT BE IMPORTED ON THE
  PYTHON ARCGIS PRO SHIPS, AND THE WHOLE SUITE PASSED ANYWAY.
  pyproject promises `requires-python = ">=3.10"`.
  equipop/doors/continental.py line 172 put a \u2019 escape INSIDE an
  f-string expression, which Python refuses before 3.12 - PEP 701
  lifted that restriction only there. So on Python 3.10 and 3.11 the
  module raises SyntaxError at IMPORT: not a wrong answer, no answer
  at all. ArcGIS Pro 3.3 and 3.4 ship Python 3.11.
  HOW IT SURVIVED: every session until now ran Python 3.12, where the
  interpreter accepts it. 1,272 tests passed over a module that could
  not load on the floor the package advertises. FOUND ONLY BECAUSE THE
  TEST CONTAINER CAME BACK AS 3.11 after a reset - by accident, not by
  a guard.
  THE FAMILY, AND IT IS A NEW MEMBER: 309-311 and 318 were all
  failures reported as something else. THIS IS A FAILURE THE
  ENVIRONMENT HID ENTIRELY. A test suite can only fail on the
  interpreter it runs on, so a compatibility promise that nothing
  checks is not a promise.
  FIXED by lifting the string to a module constant, _OWN_CRS. GUARDED
  by a test that compiles every module AND, while the declared floor
  is below 3.12, refuses a backslash inside any f-string expression -
  because a compile check on 3.12 cannot catch what 3.12 allows. The
  test says to delete its second half, not itself, if the floor ever
  rises.
  WORTH DOING SEPARATELY: run the suite on the OLDEST declared Python
  in CI, not merely on whatever the machine has. This release proves
  the value and does not provide it.

- 197 | OPEN, HOUSEKEEPING | THE COMPLETE ZIP CARRIES CACHE
  DIRECTORIES AND A STALE HANDOVER. .pytest_cache and seven
  __pycache__ folders survive into the complete zip (the wheel, sdist
  and QGIS zip are clean), the inner HANDOVER_11 is older than the
  delivered one, and equipop_test_pass.do ships only outside the zip
  and identifies itself as 1.40.3. FIX: make the release builder copy
  the FINAL handover and field pass in after their last edit, assert
  their version strings, and filter cache directories.
  ALSO: comments in stata_bridge.py still call treat_are_counts=False
  "legacy, Stata" and True "the GIS doors", although Stata has
  deliberately used True since 1.37.1. Behaviour correct, comment
  stale, and it could mislead the next change.

- 191 | DONE v1.40.4 | Dist_k FELL AS k ROSE. Found in the FIELD, by
  a line in the test pass that said "if any row breaks that ordering,
  something is wrong" - and returned 198 on John's 10,892-row set.
      Dist_50 = 51.1 m, Dist_100 = 35.8 m, same origin.
  Up to 18 m, 1.8% of rows, all sub-cell. It touches Dist_k only: not
  N_k, not T_, not R_, not any decayed column.
  THE CAUSE was two distance conventions meeting at a discontinuity.
  Inside the origin cell, Dist is the equal-area radius
  s*sqrt(unit^2*k/(n*pi)), correctly rising with k. The moment k needs
  the first ring OUTSIDE, `proportional` interpolates area-linearly
  from the previous radius - and took that to be ZERO rather than the
  cell's own radius. Stepping outside reset the baseline to the cell
  CENTRE, so the answer could land below where it already was.
  IT NEEDED BOTH proportional AND a self-potential above zero. Either
  alone hides it, which is why eleven releases never saw it - and why
  the guard now runs over every combination of the two.
  THE FIX starts the interpolation at s*unit/sqrt(pi), the value the
  in-cell formula reaches at k = n, so the conventions meet
  continuously.
  IT HAD TO LAND IN BOTH ENGINES. Fixing only the fast one broke
  test_fast_engine_identical and test_both_engines_apply_the_same_rule
  immediately - the parity tests doing exactly their job.
  AND THE FIRST CLASSIC FIX WAS WRONG: raising `dist_m` at
  initialisation destroyed a SENTINEL, because dist_m == 0.0 also
  means "the neighbourhood is still inside the origin cell" and
  selects the k-scaled in-cell estimate. Two engines then disagreed by
  40 m on two rows. The value must be substituted AT THE INTERPOLATION
  CALL, never by raising the running distance. A VARIABLE DOING DOUBLE
  DUTY AS A MEASUREMENT AND AS A FLAG IS A TRAP; documented in
  _interp_base().

- 192 | DONE v1.40.4 | [fweight=] SILENTLY DROPPED PLACES WITH NO
  PEOPLE, pop() DID NOT. Field report: 109 of John's 10,892 rows have
  ValCount == 0, and marksample marks out zero weights by default, so
  those places received no results under [fweight=] while pop() gave
  them results - two routes into the same idea disagreeing at the
  boundary, and a silent 1% difference in the sample.
  John's ruling: "they shall have results". `marksample touse,
  novarlist zeroweight`. Same principle as a case blanked by
  missing(): still the placeholder for results, contributing nothing
  itself. Both marksample options are counter-intuitive and each was
  added to close a field report, so a test asserts the reason for each
  is written down beside it.

- 189 | OPEN, NEXT CODING ROUND | arcpy.da.ExtendTable FAILS ON A
  `memory` TARGET ABOVE ONE FIELD, AND OUR ERROR HANDLING INVENTED A
  DIFFERENT STORY. Two field reports from John, then six diagnostic
  snippets in the Pro Python window. THE MEASUREMENT, on a 682-row
  memory feature class:
      1 field  -> no error, VALUES OK
      2 fields -> SystemError, 2 created, ALL NULL
      3 fields -> SystemError, 3 created, ALL NULL
      4 fields -> SystemError, 4 created, ALL NULL
      8 fields -> SystemError, 8 created, ALL NULL
  The threshold is exactly TWO. The fields are created and left empty,
  and `arcpy.GetMessages(2)` is EMPTY, so there is no hidden diagnosis
  to recover. A real run writes a dozen or more columns, so `memory`
  is simply unusable for the bulk write and no setting avoids it.
  WHAT THE USER SAW WAS OUR OWN DOING. Attempt 1 fails with
  SystemError, whose text carries nothing; _is_field_refusal() reads
  str(exc) and cannot classify it; the code concludes the target is
  busy and RETRIES WITHOUT UNDOING FIRST; attempt 2 now meets the
  fields attempt 1 created and says "field 'N_1432' exist"; that
  exception overwrites `first`; and _write_failure() tests for
  "already exist" - which this message does not contain - so it fell
  through to a generic lock explanation. Wrong cause, wrong remedy,
  and the real error discarded.
  THE FIX:
   1. VERIFY AFTER EVERY BULK WRITE, raised or not - read one row
      back. Fields present and populated is success however the call
      reported itself; present and null is failure however quietly.
      This is the item worth having regardless of `memory`.
   2. On a verified failure, undo and go ROW BY ROW. That path
      already exists and is tested. Not a retry - the bulk write is
      unavailable, not busy.
   3. Skip the bulk attempt entirely for `memory\` and `in_memory\`
      targets, and say so ONCE - John's ruling: a run that takes
      noticeably longer with no explanation reads as a fault.
   4. Never let a retry's exception replace the original, and undo
      BEFORE each retry rather than only after the last.
   5. One shared vocabulary between _is_field_refusal() and
      _write_failure(); they currently disagree about the same
      message.
  NOT A DATA-LOSS BUG: the fields came back all None, so
  _undo_partial has only ever deleted empty shells. Checked, because
  the alternative would have been serious.
  DROPPED FROM THE FIX LIST: reading arcpy.GetMessages(2) as a second
  source. The queue is empty in exactly the case that matters.

- 190 | OPEN, SMALL | THE QGIS DOOR REPORTS A ROW COUNT IT NEVER
  CHECKED. base.py writes results with `sink.addFeature(nf)` and
  DISCARDS THE RETURN VALUE. QgsFeatureSink.addFeature() returns a
  bool and does NOT raise, so a refused feature is silently skipped
  and the run still reports "Wrote N rows with M new columns" - a
  figure that is asserted rather than measured. Same shape as 189: the
  report of success does not come from checking the result.
  SMALLER THAN 189, and John agreed it is not a big thing: QGIS builds
  a NEW sink with the fields declared up front, so there is no
  bulk-extend call, no partial-write state and no in-memory target to
  trip over - none of 189 applies. And a lost FEATURE makes the output
  visibly short rather than quietly wrong.
  FIX: count the True returns, compare against the feature count, and
  say plainly if they differ instead of reporting the intended figure.
  Fold into any run that touches base.py.
  CHECKED WHILE LOOKING AND FOUND SOUND: the NaN-to-None conversion on
  the way out, including the isinstance(v, float) guard ordering, so a
  None never reaches np.isnan.

- 188 | DONE v1.40.3 | "varlist not allowed" WAS THE WHOLE ANSWER A
  USER GOT FOR AN UNKNOWN SUBCOMMAND. Field report: John ran
  `equipop setup` against an .ado installed from main, which predated
  the subcommand. With no `setup` branch the word fell through to the
  syntax line, Stata read it as a variable list, the command declares
  none, and it said `varlist not allowed`, r(101) - true, and useless.
  A conference audience typing a subcommand their copy is too old for
  meets the same wall, and would reasonably conclude the software is
  broken.
  Now: the word is named, the real subcommands are listed, the
  likeliest cause (an out-of-date .ado) is stated with the net install
  line to fix it, and the second likeliest (variables typed where a
  subcommand goes) is answered with `equipop, x(X) y(Y) k(25)`.
  THE TEST IS SAFE BECAUSE EVERY REAL FIRST TOKEN IS PUNCTUATION OR A
  KEYWORD - a comma, an [fweight=...], `if` or `in`. Only a bare
  alphabetic word can be a mistaken subcommand, and `if`/`in` are
  excluded by name. A guard that swallowed a legitimate command line
  would be far worse than the message it replaces, so that is asserted
  too.
  NOTE THE SHAPE OF THIS BUG: the fix cannot help the person who hit
  it, because they are by definition running the version without it.
  It is for everyone after.

- 187 | DONE v1.40.2 | INSTALLING IS TWO LINES NOW, ON BOTH
  PLATFORMS. John asked how hard a Windows and Mac installer would be,
  since SSC listing will take weeks. ANSWER: an OS installer is the
  wrong tool. The hard part of installing EquiPop is not moving files
  - it is targeting the PARTICULAR Python that Stata is configured to
  use, which varies per machine and is exactly what `python query`
  exists to discover at run time. An .msi or .pkg would have to guess
  it, or bundle its own interpreter and risk creating the very
  two-copies conflict that closes Stata on Windows. It would also need
  an Apple Developer ID and notarisation, plus a Windows signing
  certificate, and a rebuild per release per OS per architecture.
  WHAT WAS BUILT INSTEAD: `equipop setup`. It runs pip from inside
  Stata against sys.executable, so the interpreter cannot be guessed
  wrong, and `equipop setup, repair` force-reinstalls numpy, scipy and
  pandas for the processor mismatch case. Install is now:
      net install equipop, from(...github.../stata) replace
      equipop setup
  identical on Windows and Mac, nothing to sign, nothing to rebuild.
  TWO DESIGN POINTS: it uses the STANDARD LIBRARY ONLY, because it
  runs before the package exists and must not need the thing it
  installs; and it does NOT run the doctor afterwards, because Python
  starts once per Stata session and after an upgrade the doctor would
  report the version still in memory - the OLD one - and say
  everything matched when it did not.

- 43 | DONE v1.40.2 | CITATION.cff SAID 1.0.0 FOR FORTY RELEASES,
  because nothing checked it. Now 1.40.2 and PINNED by a test against
  the package - an EIGHTH place a version string lives. Only the
  `version:` field moves: the preferred-citation is the 2014 report
  and records where the work was written, so it does not follow the
  software version or an author's later affiliation.

- 101-remnant | PARTLY DONE v1.40.2 | `tmp/` IS NOW IGNORED. Exactly
  ONE file is committed under it -
  tmp/pytest-of-root/pytest-30/.../result_EquiPop_run.csv, a pytest
  scratch artifact from a 2026 run - and the folder regrows on every
  test run because conftest's work_outside_the_repository fixture
  chdirs into a tmp_path. There was no .gitignore rule, which is why
  the earlier `git rm -r --cached` never made it stay gone. The rule
  is in now; the `git rm -r --cached tmp` is still John's to run once.

- 186 | DONE v1.40.1 | THE DOCTOR NOTICES THE TWO-PART UPDATE. The
  .ado files come from the repository by net install; the engine comes
  from pip into Stata's Python. Updating one and not the other is the
  most frequent field failure this project has, and it surfaces as
  "ImportError: cannot import name ...", which reads as our bug.
  `equipop doctor` now prints both versions and, when they differ,
  says which route updates which half and that Stata must be
  restarted. Silent when they match - a warning that fires on a
  correct installation teaches people to ignore warnings.
  COST: the .ado carries its own version string, so a version now
  lives in SEVEN places. That is guarded, not just documented:
  test_doctor.py asserts the .ado's local against line 1 of the same
  file AND against the package, so a half-done bump fails the suite
  rather than making the doctor report a mismatch on a correct
  install.

- 185-notes | DONE v1.40 | WHAT THE FIX ACTUALLY TOUCHED. Cumulative
  DECAYED arrays are built beside cp/cgrp/cok and read at the SAME
  position, in both the whole-ring and the split-ring branch. The
  split ring takes the SAME per-cell fractions as the raw count - a
  deliberate break that dropped them was NOT caught at first, because
  the test only asserted <= and the broken version passed by being
  EQUAL. Strengthened to require both raw and decayed to MOVE, and to
  agree about which origins had a split ring.
  THE UNBOUNDED SUM IS DELETED, not commented out - John: "it risks
  becoming an orphan or picked up in a later session with unknown
  consequences". Dead code rots; git remembers.
  CONSEQUENCES WORTH KNOWING:
  - decay ALONE is no longer a valid run. It used to produce ND_inf
    with no k and no r; now it produces nothing, so it is REFUSED
    with a message saying why.
  - `covered < trunc` left the unsatisfied-origin test. Nothing reads
    past k any more, and requiring truncation coverage forced a decay
    run to scan the whole map - 283 neighbour cells where 64 would do.
  - ND_inf WAS SHIPPED AT QGIS AND ARCGIS PRO, not only Stata. Their
    output columns change to ND_<k>, TD_<v>_<k>, RD_<v>_<k>. The field
    PREDICTOR in equipop/doors/fields.py had to change with them - it
    declares output fields before a run, and a predictor that promises
    a column the engine no longer makes is the same class of fault as
    a door offering a model the engine lacks (1.39).
  - test_selfpot's shift assertion had to move from N_local to N_k:
    for that origin the whole neighbourhood IS its own cell, so under
    the default overshoot only part of it is taken. The old figure was
    right when the sum ran to truncation and swallowed the cell whole.

- 42/99/102-stata | DONE v1.39 | THE LAST OF THE ANALYTICAL BOXES
  REACH STATA: decay with fixed or variable bandwidth, the overshoot
  mode, and the self-potential ladder. Menu work - the engine has
  taken all of them for many releases - EXCEPT that writing the tests
  found two door/engine mismatches:
  (a) THE DOOR OFFERED A DECAY MODEL THE ENGINE DOES NOT HAVE. It
  listed negexp, power and "gauss"; equipop.decay.MODELS holds
  negexp, expnormal, expsqrt, lognormal and power. The door would
  have accepted gauss and been refused deep inside the engine, while
  refusing three models that work. The list is duplicated on purpose
  (78/105 - a door may not import the package to learn its own
  vocabulary) and is now PINNED against MODELS by a test.
  (b) DECAY DOES NOT REWEIGHT THE k-COUNTS. Measured: N_k and Dist_k
  come back identical, and decay ADDS a distance-weighted total in a
  column beginning ND_. The help said the opposite. The wording was
  corrected, not the code - and the test that found it was written
  expecting Dist_k to move, which is why it found anything at all.
  OVERSHOOT: `sampled` is REFUSED BY NAME, with the reason. John's
  ruling: it exists only to reproduce old EquiPop versions, so it is
  not a Stata concern, and refusing it drops the seed option too.
  SELF-POTENTIAL: three rungs by name - none, median, full - carrying
  the engine's own 0, 2**-0.5 and 1, pinned against
  rungs.SELF_POTENTIAL_VALUES. selfpot(#) still takes any number, so
  nothing already written breaks.
  The decay help text lives in equipop/doors/help.py as "decaymodel",
  so QGIS gets the same words when 102 is done rather than a third
  wording.

- 168-stata | DONE v1.38 | MISSING-VALUE CODES REACH THE STATA DOOR.
  knn_to_rows() had no missing_codes parameter - only the broader
  dispatch() route did - so the one engine Stata uses could not
  exclude a sentinel. blank_missing_codes() now does it in one shared
  place, and it runs FIRST, before anything looks at the numbers:
  a sentinel judged as a group count is refused for being negative,
  and the user is told to check their treatment variable when what
  they needed was missing().
  John's ruling holds end to end: a blanked case STILL COUNTS AS
  PEOPLE towards k and still receives its own row of results - it
  "could still be the placeholder for results - it just doesn't
  contribute self" - and the share divides by the OBSERVED part.
  Measured: six cells of 100 people, 30 of the group each, two cells
  blanked -> N=600, T=120, R=0.30. That is 120/400, not 120/600.
  The help text lives in equipop/doors/help.py under "missingcodes",
  so QGIS and Pro inherit the same words when they get the box.

- 183 | DONE v1.38 | A NEGATIVE GROUP COUNT SLIPPED PAST THE 179
  GUARD. Found by a test that expected the undeclared Census sentinel
  to be refused and watched it pass. The check asked whether the group
  was BIGGER than the population; -666666666 is comfortably smaller
  than any population, so it sailed through. A count of people cannot
  be negative on its own terms. The refusal now names missing() as the
  fix, because the user who trips this is precisely the one who does
  not know the option exists. A guard written against one impossible
  case will not catch the others - enumerate them.

- 184 | DONE v1.38 | RESULT NAMES WERE VALIDATED WHILE VARIABLES WERE
  ALREADY BEING WRITTEN. External review of 1.36, P1. The collision
  check sat INSIDE the writing loop, so a clash or an over-long name
  on the tenth variable left nine already in the dataset - a run that
  stopped with an error and changed the data anyway. prefix() was
  checked only against "N_1", which proves nothing about
  T_<longvariablename>_100 against Stata's 32-character limit. Now
  every intended name is built and checked - length, collision,
  duplication - BEFORE any variable is created, and all the problems
  are reported at once rather than one per run.

- 179 | DONE v1.37.1 | treat() HAD TWO INCOMPATIBLE MEANINGS AND THE
  WRONG ONE WON IN STATA. External review of 1.36, reproduced before
  fixing. The help and both GIS doors say treat() holds the group's
  PERSON COUNT; the Stata bridge applied the legacy rule, treat as a
  0/1 flag multiplied by the population, because equipop.ado never
  passed treat_are_counts. Population 100, group count 30, k=100 gave
  N=100, T=3000, R=30.0 - a group three times the neighbourhood
  containing it, and a share of 3000%. unit() is the CELL SIZE and
  does not scale R, so there is no reading of those numbers that is
  correct. It was not confined to weighted runs: counts with no
  weight gave N=5 rows against T=150 persons, R=30 again.
  JOHN'S RULING: counts are the default, matching the help and the GIS
  doors; flags stay available by name via treatmode(flags) so nothing
  written already breaks; and impossible combinations are REFUSED.
  validate_treatment() refuses on the way IN - a flag outside 0-1,
  counts with no population, a group larger than its population, each
  naming which setting to use. check_results_are_possible() refuses on
  the way OUT, because a guard on the input can be defeated by an
  engine change while one on the output reads the number the user is
  about to be handed.
  IT IMMEDIATELY FOUND IMPOSSIBLE DATA IN OUR OWN FIXTURES. test_rungs
  drew Population and LowInc independently, so the group exceeded its
  own population at 84 of 400 points; test_arcgis_stub did the same
  with Pop and Grp. Both fixtures were corrected, not the guard. This
  is the bad-fixture failure again: data that cannot occur in the
  field proves nothing about the field.

- 180 | DONE v1.37.1 | AN EMPTY treat() BROKE -replace-. Reviewer P1,
  confirmed. treat() became optional in 1.36 and the replace branch
  holds `foreach v of varlist `treat''` twice. An empty varlist loop
  is a SYNTAX ERROR in Stata, not an empty loop, so
  `equipop, x() y() k(25) replace` failed on exactly the combination
  that ruling created. A THIRD CLASS OF STATA DEFECT, after 172's
  arity mismatch and 173's None: the parser test models argument
  passing, not Stata's runtime grammar, and no amount of parsing the
  file reveals this. Guarded by reading the guard's scope, not by
  searching for a string.

- 181 | DONE v1.37.1 | STATA REOPENED THE FRACTIONAL CELL SIZE ALREADY
  CLOSED AT THE GIS DOORS. Reviewer P1, confirmed. 155 refused
  fractional cell sizes in QGIS and Pro from 1.29.8; Stata declared
  unit() a plain real and checked nothing, not even zero or negative.
  MEASURED: unit 2.5 with points at 0.1, 2.6 and 5.1 gives centres 1,
  3, 6 - spacings of 2 and 3, neither of them 2.5 - because centres
  are cast to integers. The test asserts the UNREPRESENTABILITY rather
  than quoting the rule, so if the core ever changes the rule gets
  revisited instead of kept from habit.

- 182 | DONE v1.37.1 | SHIPPED INSTRUCTIONS POINTED USERS AT THE
  CONFIGURATION THAT CLOSES STATA. Reviewer P0. README_STATA.md told
  users to point Stata at an Anaconda environment - the one setup the
  handover records as fatal. STATA_GUIDE.md still taught equipop_knn
  with a mandatory treat() and the removed weight() option;
  TESTING_STATA.md gave invented Anaconda paths and promised for 1.38
  things that shipped in 1.36. INSTRUCTIONS ARE PART OF THE RELEASE:
  this one could break a machine before EquiPop ran. Now ONE current
  page, the rest moved to stata/historical/ behind a DO NOT FOLLOW
  banner, and a test refuses "anaconda" outside a prohibition,
  weight(), and stale release promises in current guidance. Broken on
  purpose by putting an Anaconda path back into a `python set exec`
  line - caught.

- 178 | DONE v1.37 | A SINGLE-ZONE PROJECTION OVER WIDE DATA SAYS
  SO, AND CARRIES ON. John's ruling, and the reasoning is his: "allow
  the user to proceed regardless - the effects are smaller than
  expected. This since the bespoke neighbourhood departs from the
  nearest k-neighbours, it becomes almost impossible to find a
  situation where an erroneous nearest neighbour is selected before
  the true nearest, and if that happened it would be in very large k,
  and at distances that makes very little difference. (i.e. for me it
  is the risk of counting the wrong cafe in Lyon/France from Oslo)".
  THE ARGUMENT IS ABOUT ORDER, NOT DISTANCE, and it is the same one
  that closed 171: a neighbourhood is built from the rank in which
  neighbours are reached, so a sub-percent stretch changes an answer
  only by swapping two cells' rank - and two cells that close in true
  distance, at the k needed to reach across zones, are interchangeable
  members of the same neighbourhood. So the note is honesty about what
  was done, not a warning of a defect, and it NEVER refuses.
  Three zones is the threshold; two is ordinary, since any dataset
  near a boundary straddles one.
  THE NOTE CARRIES THE FIGURE FOR THE USER'S OWN EXTENT rather than a
  generic reassurance - "stretched by at most 0.78% at the far edge of
  this data" beats "well under one percent", because a reader can
  weigh 0.78% against their cell size and cannot weigh a platitude.
  The second-order point-scale formula k = k0(1 + (dlam cos phi)^2/2)
  is checked against pyproj's geodesic at three longitudes and agrees
  to within 5e-5; at 9 degrees off the meridian it predicts 0.469%
  and the measured error is 0.470%.
  The note is computed on the DEGREES, before the coordinates are
  replaced, and any failure to compute it yields no note rather than a
  failed run: a remark about the data must never be the thing that
  stops the data being analysed.

- 177 | DONE v1.37 | LAT/LONG IS A USAGE BLOCKER, AND THE FIX MUST
  NOT COST A DEPENDENCY. John's ruling and the whole specification:
  "for professional spatial analysts, this function is not needed,
  they will have routines for projecting the data as they need and
  want - However, for the unexperienced stat and econ people that are
  not trained to think beyond lat/long, a simple function to generate
  good-enough projections are what is needed. I think that we should
  communicate in the output which projection that was used in each
  case (i.e. EPSG code for UTM would be enough)".
  WHY NOT pyproj: it is a fourth compiled library, and it would be
  demanded of exactly the users least able to repair it when it will
  not load - undoing 176, which had just taken it off the Stata path.
  So `equipop/utm.py` does transverse Mercator by the Kruger series in
  numpy alone. CHECKED, NOT CLAIMED: against pyproj over all 120
  zones, 200 points each, worst disagreement 0.000193 mm. A
  neighbourhood is hundreds of metres wide, so millimetres are
  irrelevant - agreement at that level is evidence the implementation
  is RIGHT, not merely close. Also a round trip independent of pyproj,
  and one hand-checkable point on the central meridian.
  THE ZONE IS CHOSEN BY THE MEDIAN, not the mean, so a fringe of
  far-away points cannot drag the whole dataset into a zone holding
  none of it. Refuses rather than guesses: coordinates outside the
  degree envelope, latitudes beyond 84N/80S, an EPSG that is not a
  WGS84 UTM zone. Single zone throughout - 171's ruling.
  THE RUN SAYS WHAT IT DID: "equipop: projected to UTM zone 19N
  (EPSG:32619)", and r(epsg) and r(crs) carry it back.
  WITHOUT -project-, coordinates that look like degrees now raise a
  WARNING naming the option. Warn, never act: silently projecting
  changes every number with no record, and silently counting in
  degrees - the behaviour before 1.37 - gives a wrong answer with no
  signal at all. The warning is conservative and does not fire on
  projected data, so it cannot nag a professional on every run.
  NOT DONE, deliberately: the Norway and Svalbard zone exceptions. The
  zone comes from the longitude by the standard formula, so the EPSG
  reported describes exactly what was done; only the central meridian
  differs from official UTM there, and the projection is valid either
  way.
  FOUND WHILE BREAKING GUARDS: the missing-value mask in to_utm() is
  redundant - NaN propagates through the whole series, so deleting it
  breaks no test. Kept as a statement of the contract, and labelled as
  redundant in the source rather than left looking like coverage.

- 176 | DONE v1.37 | `import equipop` LOADED FIVE COMPILED
  LIBRARIES FOR A COMMAND THAT NEEDS THREE. Found from Umut's Mac,
  testing 1.36 for the conference: pandas would not load, because the
  copy in his user folder was built for Intel and his Stata runs as an
  Apple-Silicon program. The loader refuses to mix processors. numpy
  imported fine - it was a different, correct build - which made it
  read as a pandas fault rather than an installation one.
  MEASURED BEFORE TOUCHING ANYTHING: `import equipop` took 2.46s and
  pulled in numpy, pandas, scipy, pyproj and matplotlib, 1226 modules.
  Machine 1 needs numpy, pandas and scipy. pyproj and matplotlib were
  loaded on every Stata run by users who never asked to project or to
  draw, and a fault in either took the whole package down. geopandas
  and rasterio were already deferred inside the functions that use
  them - checked, not assumed, and that is why `_EXTRAS` names viz
  alone. THE FIX is PEP 562: `__init__.py` maps every public name to
  its module and fetches it on first use. `equipop.run_knn`,
  `from equipop import run_knn` and `import equipop.analysis` all
  behave as before; only the timing changes. All 60 public names of
  1.36 resolve, out of the same modules, asserted against a recording
  of the 1.36 surface. AFTER: `import equipop` costs 0.00s and 72
  modules and loads nothing compiled; the Stata path loads numpy,
  pandas and scipy and stops. A broken pyproj now breaks projection
  and nothing else, which is the precondition for 1.38 - projection
  cannot be added while pyproj loads for everybody. Guarded by
  tests/test_lazy_imports.py, which imports in a clean SUBPROCESS
  because once pytest has loaded a library an in-process check passes
  for the wrong reason. Broken on purpose three ways: an eager import
  added back, a wrong module in the map, and a numpy import added to
  doctor.py - each caught.

- 175 | DONE v1.36 | THE STATA HELP IS GENERATED, NOT WRITTEN.
  `stata/equipop.sthlp` comes from tools/make_sthlp.py, which reads
  equipop/doors/help.py - the same sentences ArcGIS Pro renders
  through make_help_xml.py and QGIS reads for shortHelpString.
  WHY THIS AND NOT A HAND-WRITTEN FILE: John ruled help ahead of
  projection ON CONDITION that projection could be added to the help
  easily afterwards. Generated help satisfies that condition
  exactly - projection's sentences get written once in help.py and
  appear at all four doors together. A hand-written .sthlp would
  have to be remembered separately, and would be the first thing to
  drift.
  WHAT IS NOT INHERITED: door-specific wording. The dialogs qualify
  x and y with "only for tables or attribute mode", because a GIS
  layer may carry geometry instead of columns. A Stata dataset never
  does. Those two are overridden in make_sthlp.py with a comment
  saying why. Shared text where it is genuinely shared; door text
  where pretending otherwise would mislead.
  PACKAGING: stata.toc and equipop.pkg, so
  `net install equipop, from(https://raw.githubusercontent.com/GeoJohnSwe/EquiPop/main/stata)`
  works the moment he pushes. A test refuses a .pkg that names a
  file which is not in stata/ - that failure would otherwise happen
  at the user's end, not ours.

- 173 | DONE v1.35.1 | STATA REFUSES None FOR A MISSING NUMBER.
  John's FIRST successful field run of the Stata door, 1.35 session.
  The engine finished - 1,958 cells, both k, the self-potential
  report, 16 columns for 10,892 observations - and the command then
  died handing the results back: TypeError, the specified value
  should be a numeric value.
  CAUSE. Stata has no NaN. A missing number in a Stata double is
  2**1023 and anything larger encodes .a-.z, which is why every
  reader in stata_bridge treats `> 8.9e307` as missing on the way IN.
  The glue passed None on the way OUT. sfi refuses it.
  WHY IT SURVIVED. It needs a missing RESULT to be reached at all.
  Every earlier exercise used complete coordinates, so the branch had
  never once executed. John's data had 9 rows without coordinates and
  hit it on the first run. Same line, same latent fault, in
  equipop_run.ado - never reached there either.
  FIX. The conversion moved OUT of the .ado and INTO the package as
  stata_bridge.to_stata_values(): plain Python floats, never numpy
  scalars, NaN and infinity written as Stata's own missing sentinel so
  the value survives the round trip through the `> 8.9e307` readers.
  THE PRINCIPLE THIS SETTLES: code inside a `python:` block can only
  be run by Stata, so nothing in pytest can reach it. Every line moved
  out of that block is a line the suite can test. The block should
  hold sfi calls and nothing else. 172 made the block READABLE by the
  suite; 173 makes as much of it as possible RUNNABLE by the suite.
  GUARDS. to_stata_values tested directly, including the round trip
  back through the missing-value convention, plus a reader over every
  Data.store call in every .ado that refuses None among its VALUES
  while allowing the legitimate None in the observation slot - broken
  on purpose against the pre-fix line.

- 172 | DONE v1.35 | THE STATA COMMAND COULD NOT RUN, AND HAD NOT
  SINCE v1.29.5. Found by Claude reading the file at the start of the
  1.35 session, in the first ten minutes of a deadline session, before
  any of the Stata catch-up work was planned.
  `stata/equipop_knn.ado` called `_equipop_knn` with EIGHT arguments;
  the def in the same file took SEVEN (six required, `rlist=""`). The
  body ALSO read `selfpot`, which was not one of its parameters. So
  every invocation raised TypeError before EquiPop was reached, and
  would have raised NameError immediately after.
  IT BROKE IN THE RELEASE THAT ADDED THE OPTION. v1.29.5 (BACKLOG 113)
  put `SELFpot(real 1)` on the syntax line and `selfpot` at the call
  site and left the def alone. Eleven releases, 435 green tests, and
  the only detector was John running it - which he had not, because he
  works in GIS and the Stata door was assumed done at v1.0.
  WHY NOTHING SAW IT. Stata sits outside `door_parity.py`, which
  HANDOVER 8 already says. It also sat outside the suite ENTIRELY:
  nothing in the project had ever opened an `.ado`. `door_parity`
  compares box names and `LADDER_CASES` compares result columns;
  neither can see a file that no test reads.
  THE FIX IS TO THE TRAP, NOT THE INSTANCE. The glue is called by
  NAME and its parameters are KEYWORD-ONLY. Adding a box can no
  longer shift the meaning of every argument after it, order cannot
  be got wrong, and a wrong name is refused BY that name. This is
  BACKLOG 169's medicine applied to the other door that threads
  arguments positionally.
  THE GUARD: tests/test_stata_ado.py, which reads every `.ado` and
  refuses (1) a `python:` block that does not compile, (2) a call
  site that does not match its own def by arity or by keyword, (3) a
  name read in the glue that nothing defines, (4) an option declared
  on the `syntax` line and never read - BACKLOG 148's failure in
  Stata dress, and (5) a keyword handed to `equipop.stata_bridge`
  that no longer exists there, which is the narrow parity check the
  Stata door has never had. All five broken on purpose; each names
  the offending line. Run against the real 1.34 file, (2) and (3)
  fail with the exact TypeError Stata would have printed.
  THE NAME: the command is `equipop` from 1.35, John's call, with
  `equipop_knn.ado` kept as a forwarding alias. `equipop_run.ado` was
  read by the same test and is sound - 28 arguments into 28
  parameters, `selfpot` and `wperm` threaded properly.
  WHAT THIS SAYS ABOUT THE REST OF THE STATA WORK: the bridge is far
  AHEAD of the doors. `dispatch()` already takes missing_codes,
  overshoot_mode, seed, self_potential, decay in every form,
  r_values and treat_are_counts. The catch-up of section 1 of
  HANDOVER 8 is `.ado` syntax lines and threading, not engine work -
  with projection the one real exception.

- 168 | CORE DONE v1.32, DOORS STILL TO DO | MISSING-VALUE CODES.
  John, field, 1.31, on finding the Census sentinel -666666666 in 64
  of his 1074 Bristol rows: "the cause is unimportant, but the
  possibility to dismiss/exclude those values would be of importance
  ... when a case with this kind of value is reached the treatment
  value is not included (it could still be the placeholder for
  results - it just doesn't contribute self)".
  Undeclared, that sentinel takes a neighbourhood mean household
  income to MINUS 166 MILLION, quietly. Declared, the same run reads
  300.0 on the test layout.
  DONE: `missing_codes=[...]` on dispatch. The conversion happens
  ONCE, at that door, so counts, stats, friction, slope and fca all
  get it and no engine learns a new concept - the same placement and
  the same reasoning as the Gini guard of BACKLOG 154. A declared
  code becomes ordinary missing, and every path downstream already
  knew what missing meant.
  THE DENOMINATOR, John's ruling on his own worked example: of 400
  people with 60 of unknown group the share divides by 340, never by
  400 - dividing by 400 quietly assumes those 60 were not in the
  group. CellData gained `binary_valid` (people whose value for that
  variable is usable) and both engines divide by it. It equals the
  full population unless codes were declared, so no published number
  moves. Note the trap avoided: with aggregated input one ROW stands
  for many people, so the valid count sums WEIGHTS, not rows -
  broken on purpose and caught.
  The case still counts towards k and still receives its own results;
  N_k and Dist_k are unchanged by declaring a code, and only Nv_ and
  the statistics move. Guarded.
  STILL TO DO: the box in all three doors - Pro, QGIS and Stata - so
  a user can paste the codes without writing Python. John's shape: a
  text box.

- ~~169~~ | DONE v1.33 | THE PROJECTION ARGUMENT ORDER, and the
  book taught the mistake. suggest_projection() says (lat, lon);
  every other module in EquiPop says (x, y), which is (lon, lat).
  Called positionally in the codebase's own order on John's Bristol
  County data it returned EPSG:32737 - UTM zone 37 SOUTH, for Rhode
  Island - and reported "single-zone projection is safe (distortion
  < 0.1%)" while doing it. Found by Claude making exactly that call
  by accident while answering John's question about autoprojecting
  for Stata.
  NOTHING DOWNSTREAM COULD CATCH IT. The output is metres, the metres
  are plausible, and every distance is wrong by a factor nobody can
  see. And RANGE CHECKS CANNOT RESCUE THIS CASE: -71.3 is a perfectly
  legal latitude, so the swapped call is not detectably wrong - it is
  a correct answer about somewhere else.
  So the ORDER was removed as a thing a caller can get wrong:
  lat_col/lon_col are KEYWORD-ONLY in suggest_projection and
  assign_zones, and suggest_projection_xy() takes EquiPop's usual
  (x, y). A positional call now raises TypeError.
  What CAN be checked now is: a latitude beyond +/-90 or a longitude
  beyond +/-180 is refused by name, which catches the commoner
  mistake of handing projected metres to a function that wants
  degrees.
  THE SHIPPED BOOK HAD IT WRONG: docs/book/ch03_data_in.md printed
  `suggest_projection(df, "lon", "lat")` - swapped AND positional.
  Anyone following it got the wrong CRS. Corrected, and pinned by a
  test that reads the book.
  WHY IT MATTERED NOW: projection becomes a MUST-HAVE on the Stata
  door, and John's reason is that most Stata users are not GIS people
  - "forcing them to project may be a big usage blocker". The users
  least able to spot a wrong CRS are exactly the ones about to be
  handed this.

- ~~170~~ | CLOSED v1.34, WILL NOT DO - John's ruling | WARN WHEN A
  VALUE VARIABLE HAS FAR FEWER
  DISTINCT VALUES THAN ROWS. John's ruling, 1.31, on the Gini: it
  measures inequality BETWEEN cell values, so within-cell inequality
  is invisible. On his Bristol extract the ACS attributes are
  block-GROUP values back-filled to blocks - 34 distinct incomes
  across 1074 rows - so a Gini there is dispersion between area
  medians and understates household inequality substantially. He
  agreed it should say so: "Most of the listeners will be advanced
  econometricians and spatial analysts so in my work (and the user of
  EquiPop) this is easy to grasp." Cheap to add, one line at run
  time, and it protects him from the question at the conference.
  DECLINED, 1.34: "no need, the users will either know what they test
  or understand statistics better than using it with too few distinct
  values." Recorded rather than deleted: the observation is still
  true and the reason for not warning is a judgement about WHO USES
  THIS, which a later session should not quietly reverse.

- ~~171~~ | CLOSED v1.34, WILL NOT DO - John's ruling | THE
  SINGLE-ZONE PROJECTION NOTE.
  John, 1.32, ruling that single-zone is acceptable: "there is always
  a potential of doing better things in GIS ... There need to be a
  comment in the help sections where the single projection biases are
  mentioned (not at any length but as just to hint the user - i.e.
  thinking of the US data, using the projection for attached County
  also in Chicago means that the xxx feet/meters are 'floating') - in
  most cases this has no effects (since we study nearest neighbours
  where this problem becomes small in relative terms)". Belongs in
  the Stata help and the shared help text, briefly.
  DECLINED, 1.34, and the reasoning is worth keeping because it is a
  statement about when projection error MATTERS: "Professionals would
  project according to specific settings, this is to make sure all
  have the opportunity to run EquiPop, especially when the effect is
  close to none. (if we have 100m units, the sheer amount of k needed
  to reach an erroneous cell due to mis-projection before reaching
  the correct one is likely very high, and the effect would be so
  minimal that it wouldn't matter - and at those distances, the
  precise metric distance to k is of no importance)".
  In other words the error is bounded by the ORDER in which cells are
  reached, not by the distance figure itself: a projection wrong
  enough to reorder a k-neighbourhood at 100 m units would have to be
  wrong by a great deal, and by the time k is large enough to span
  that distance the exact metric radius has stopped carrying the
  meaning. The autoprojection stays silent.

- ~~101~~ | DONE v1.34 | THE TEST SUITE WROTE INTO THE REPOSITORY.
  Open since v1.24. Running the suite left files like
  `C:\Data\Kayseri_EquiPop_run.csv` and `memory/lyr_EquiPop_run.csv`
  in the repository ROOT, and seven are committed to main. The
  release-zip guard refused a build over them TWICE in the 1.30
  series, which is the only reason they never shipped inside a zip.
  NOT A BUG IN THE WRITERS. The ArcGIS tests hand the toolbox
  realistic Windows catalog paths - that is their job, they simulate
  Pro on Windows - and on Windows the sidecar lands beside the output
  correctly. On Linux a backslash is an ordinary character, so the
  whole thing is one long FILENAME and it lands wherever the suite is
  standing.
  NO PRODUCT-SIDE GUARD WOULD DO IT. Refusing to write a sidecar when
  the output's folder does not exist cannot tell that case apart from
  a user legitimately passing a relative `out.csv` and expecting the
  manifest beside it - both have an empty directory component. It
  would break the honest case to tidy up after the dishonest one, and
  John's own field testing writes relative paths.
  So tests/conftest.py runs the whole suite from a temporary
  directory. That holds whatever a future test does with a path,
  which is the property worth having: the repository cannot be
  polluted by a test nobody has written yet. It ALSO fails the run if
  anything new appears in the root anyway, naming the file, so a test
  writing there by absolute path is reported rather than tidied away
  silently. Verified by writing a stray on purpose.
  STILL JOHN'S: `git rm -r --cached` on the seven already committed -
  C__/Data/, Instance=C_/Data/, segregation_profile_HighEdu.csv. This
  stops new ones; it cannot un-commit the old ones.

- 161 | open v1.30 | PRO WILL NOT OFFER A BARRIER RASTER FROM THE
  MAP. John, field, 1.29.9: the raster was already loaded in the
  Contents pane, but the Barrier rasters box has no dropdown, so he
  had to drag and drop it in. "It works but it is too complex for
  unexperienced users." He wants it to look like the DEM box, which
  does offer the dropdown.
  THE CAUSE. Two lines, declared differently:
      dem            ["DERasterDataset", "GPRasterLayer"]
      barrierrasters  "DERasterDataset"      multiValue=True
  GPRasterLayer is what makes Pro populate the list from the map.
  The barrier box never had it. QGIS is NOT affected - it uses
  QgsProcessingParameterRasterLayer for the barrier raster and the
  DEM alike, so Q has always behaved the way John wants Pro to.
  THE TRAP. Adding the datatype alone produces a dropdown that then
  FAILS. The DEM survives a Layer object because it is read through
  _ref(), the v1.16.7 normaliser ("Expected a Raster instance or
  path name"). The barrier rasters are read as DISPLAY TEXT instead:
      _txt(pm, "barrierrasters").split(";")
  and a layer's text is its NAME, not a path. So the fix is two
  parts: add GPRasterLayer, AND read pm["barrierrasters"].values,
  passing each through _ref().
  A SECOND, OLDER DEFECT IN THE SAME LINE. Pro renders a multi-value
  box as its members joined by ";", and QUOTES any member containing
  a space. So a barrier raster in a folder with a space in its name
  already comes back as 'C:\My Data\friction.tif' - quotes included -
  and splitting on ";" hands that straight to the reader. Present
  since the parameter was written; invisible because no test uses a
  path with a space in it. Same family as the GeoPackage catalogPath
  finding: arcpy hands back a display string and the code treats it
  as a location.
  THE SIMULATOR CANNOT SEE ANY OF THIS. tests/test_arcgis_stub.py
  models Parameter.valueAsText as str(self.value) and has no notion
  of multiValue, .values, semicolon joining or quoting. It must
  learn the real behaviour first, or the fix is unprovable here and
  John field-tests it blind.

- ~~160~~ | DONE v1.29.8 | Both doors read the working CRS's linear unit and say it. QGIS maps QgsUnitTypes; Pro reads linearUnitName. The run message and the closing Dist_k note both carry the real unit, the box labels say 'map units', and NO WARNING is raised - John, 1.29.7: 'no need to warn - the users will understand.' Guarded by a test that no source file asserts metres without asking.

- ~~155~~ | DONE v1.29.8 | A fractional cell size is REFUSED, not rounded, in both QGIS machines and in Pro's runner. The rule is whole MAP UNITS, per John's correction in 160.

- ~~156~~ | DONE v1.29.7 | tools/make_release_zip.py builds the archive from an allow-listed walk and REFUSES any member name carrying a drive letter, a backslash, an absolute path, a traversal component or a Windows-illegal character. A manual clean in the right order was not a fix - it had been run, before the test suite, which recreated the files. Guarded five ways.

- ~~157~~ | DONE v1.29.8 | The layer is chosen from the ARCHIVE'S OWN LISTING rather than by globbing the extraction folder, so a stale extraction of a replaced archive can no longer win. An archive holding more than one GIS layer is now REFUSED rather than guessed at - EquiPop says how many it found and asks the user to name one.

- 158 | open v1.29.6 | HEX SELF-POTENTIAL USES A SQUARE-CELL AREA.
  External review: hex cells pass hex_size into the same unit_size
  field, and selfpot.radius_for_k() computes area as unit_size^2. A
  hexagon 100 m flat-to-flat has an area of about 8,660 m^2, not
  10,000 - so the radius is overstated by about 7.5% (17.84 m where
  16.60 m is right). The formula is AREA-based and correct; it is
  simply being handed the wrong area. Carry cell AREA and geometry
  in CellData rather than a side length, and define the hex mean
  intra-cell distance for the decay half too (0.3826c is the square).
  Ties to 3.

- 159 | open v1.29.6 | RunLog IS NOT THE PROGRESSIVE RECORD THE
  MANUAL DESCRIBES. External review: with the default constructor no
  file exists before finalize(), so a crashed run leaves nothing; and
  if a different output path arrives at finalize() the logger writes
  a new file and leaves the first marked "running" forever. Fix one
  immutable path at the start, write immediately, update atomically -
  or document that progressive persistence is unavailable. Ties to
  148: a record that is not written until success is not provenance.

- ~~150~~ | DONE v1.29.8 | Two things, both from John. First, CLAUDE'S ERROR: John was sent to look in the PROCESSING TOOLBOX, where QGIS uses its own generic gear icon for every provider - a plugin's icon.png appears in the PLUGIN MANAGER list and on the repository page, and nowhere else. His "just the traditional looks of the tool" was CORRECT, and so was his install route. The icon was there all along; he found it once he looked in the right place. Second, an ~E~ was drafted at John's suggestion - a condensed capital E in the old EquiPop Flow red with a tilde either side, after the C# release's e-with-waves - AND THEN WITHDRAWN BY JOHN: "there is a risk that the version I proposed may look a bit like a German swastika." He is right - two dark angular forms flanking a hard geometric centre is a bad silhouette to leave on a plugin list, and Claude did not see it. The ring-of-neighbours icon of 79 stands, and has the better claim anyway: it depicts what EquiPop MEASURES rather than spelling its name. Recorded so nobody proposes the ~E~ again.

- 128 | STATA HALF DONE v1.37, Pro and QGIS open | `equipop doctor` - ONE DIAGNOSTIC, EVERY DOOR.
  Proposed by the distribution review and worth taking: the release
  risk is not the mathematics, it is getting a compatible Python
  environment inside four host applications, each of which owns a
  different one. A read-only report naming the host, the exact Python
  executable, the equipop version, which dependencies are missing and
  the precise command to fix it - copyable, and safe to paste into a
  support thread. The QGIS door has check_versions(), which compares
  two version strings and nothing else; there is no shared diagnostic
  and no way for a user to answer "what have I actually got".
  It also fits what this project already believes: stub_audit.py was
  taught to EXPLAIN rather than raise in 1.29.5 for the same reason.
  RECOMMENDATION, not a platform requirement.

- 129 | open v1.29.5 | VERSION THE OUTPUT SEMANTICS, NOT JUST THE
  STRUCTURE. The distribution review asks for an OUTPUT_SCHEMA_VERSION
  in every adapter. Sharper than it sounds, and 1.29.5 is the proof:
  check_versions() compares a CONTRACT NUMBER that its own docstring
  says "only changes when something STRUCTURAL does" - but 1.29.5
  changed what Dist_k MEANS (BACKLOG 95, 115) without changing any
  structure at all. Same columns, same types, different numbers, no
  message. A user with a saved model or a Processing script gets
  different answers and nothing anywhere tells them. That is exactly
  the silence this project exists to hunt, in the one place we have
  not looked. Needs a SEMANTICS version that changes when a number's
  meaning changes, and a door that says so when the model it is
  running predates it.

- 130 | open v1.29.5 | STATA IS NOT SSC-READY. Confirmed against the
  tree, not taken on trust:
  - NO .sthlp FILES AT ALL. stata/ has two .ado files, Markdown
    guides and examples. Native help is a first-class deliverable for
    SSC, and Markdown is not it.
  - THE VERSION STORY CONTRADICTS ITSELF: equipop_knn.ado line 1 says
    "v1.0", equipop_run.ado line 1 says "EquiPop 1.6", the package is
    1.29.5. Neither users nor `adoupdate` can tell what they have.
  - equipop_knn REQUIRES treat(): the syntax line has
    TREAT(varlist numeric) OUTSIDE the optional brackets, so a
    distance-only k run - N_k and Dist_k, no groups - cannot be asked
    for through that command at all. It is the simplest thing EquiPop
    does and the focused command refuses it.
  Also needs a .pkg/stata.toc harness tested with `net install` into
  an empty environment, and a licensed Stata run: README_STATA.md
  still says the sfi glue awaits its first real Stata execution.

- ~~131~~ | DONE v1.29.6 | LICENSE copied into the plugin folder and hasProcessingProvider=yes declared. Guarded: the plugin must carry what the repository requires.

- 132 | open v1.29.5 | ARCGIS PUBLIC DISTRIBUTION. The .pyt is
  already the right artifact - native, batchable, ModelBuilder-usable
  - and the review is explicit that a .NET add-in would add a
  language, an SDK lifecycle and a signing surface without improving
  anything analytical. What is missing is a public ITEM: a versioned
  Geoprocessing Sample ZIP with relative paths, the .pyt, the help
  sidecars, LICENSE, README, a golden dataset and its expected
  results, tested after extraction into a fresh project.

- 133 | open v1.29.5 | A FOURTH DOOR - AND R, WHICH THE REVIEW DOES
  NOT MENTION. John raised it: "R is not mentioned but in of course."
  Claude's assessment: R via reticulate is STRUCTURALLY THE SAME AS
  THE STATA DOOR and easier - native data frames, and none of the
  variable-name sanitising that produced the decimal-radius bug in
  113. SPSS is feasible as an extension command (.spe/.spxt) but
  carries a harder dependency story: SPSS 31 embeds Python 3.13,
  older supported releases embed older ones, and every compiled
  dependency needs a wheel for each combination.
  THE GATE IS NOT THE HOST, IT IS 120. Every door duplicates the
  reference and treatment construction, and BACKLOG 108 - a silent
  scientific corruption that survived eight published releases -
  existed precisely because that logic is written twice and only one
  copy was fixed. A fourth door is a fourth place for the next 108 to
  hide. 120 first.
  One thing in our favour: the BACKLOG 78 constraint that stopped 105
  sharing its wording is a QGIS/Pro problem - those hosts import
  adapters at STARTUP. R and SPSS load on demand, so a new door
  probably CAN import shared code, which is an argument for building
  120's shared module in a way both old and new doors can use.

- 134 | open v1.29.5 | A GOLDEN DATASET AND EXPECTED RESULTS, ONE PER
  HOST. Proposed by the distribution review and the cheapest item in
  it: one tiny redistributable example with known answers, shipped
  with every door. It becomes the smoke test, the documentation
  example and the first thing to ask for in a support thread. Gridby
  already exists and needs no file, so most of the work is choosing
  the numbers and writing them down.

- ~~135~~ | DONE v1.29.6 | A field-level refusal is no longer retried as a lock - the retry was making things worse, running twice against a half-written table. Where the target cannot take the write, the message names the real cause, and Output = New feature class remains the way through. Guarded by test_a_field_refusal_is_not_retried_as_a_lock.

- ~~136~~ | DONE v1.29.6 | The shared dispatch no longer announces itself as "[stata]" in every door. The MODULE keeps its name until 120 moves that file anyway.

- 137 | open v1.29.5 | WORLDPOP IS PER COUNTRY, AND 92 ASSUMES ONE.
  Raised by John, 1.29.5: "there may not be a pure Africa tif, but
  there may be country files... allow for a mosaic function to merge
  all selected into a continental one - or simply point to folders
  where the needed data is stored." He is right, and it is a HOLE IN
  92, which Claude helped write: 92 is grounded on the Kenya page and
  never addresses the multi-country case, which is the actual shape
  of the data. Africa for ASFR is roughly 54 countries x 7 cohort
  files, not 7.
  DO NOT MOSAIC. rasters_to_points() reads a raster and immediately
  discards it, keeping a table of populated cells. A mosaic builds a
  BIGGER RASTER which we would then throw away - Africa at 100 m is
  ~3 billion cells, mostly empty, so mosaic-then-extract needs
  terabytes of intermediate GeoTIFF to reach the same table that
  extract-then-concatenate reaches directly. Same answer, no middle
  step. raster.py already understands glob alternatives, so a cohort
  rule like *_f_15_2020.tif over a folder tree is nearly free.
  AND CONCATENATING THE DATA IS NOT MERELY CHEAPER, IT IS THE ONLY
  CORRECT ROUTE. Neighbourhoods cross borders: a woman near the
  Kenya-Tanzania line needs her k nearest in Tanzania. Running per
  country and merging the RESULTS would be wrong everywhere near a
  border, and Africa is mostly border. bigrun.py already answers
  this - a global tree with origin tiling - provided every country's
  cells sit in one table.
  THE HARD PART IS THE PART MOSAIC OPERATORS EXIST FOR. Country
  rasters are clipped to national boundaries, and where two clips
  disagree you can get a cell claimed twice, which a straight concat
  would double-count. FIRST / MEAN / SUM / BLEND exist for exactly
  that choice and none of them is obviously right for population
  COUNTS. Needs real data in front of us; do not decide in advance.
  VERIFIED, 1.29.5, on real WorldPop files John supplied - Burundi
  and Rwanda, f_15, 2020, 100 m (R2025A):
  - THEY SHARE ONE LATTICE EXACTLY. Same CRS (EPSG:4326), same
    3-arc-second pixel, and the origins differ by 168 and -1515
    WHOLE pixels. No resampling is needed to combine them and
    raster.py's grid check will pass across countries.
  - THEY DO NOT OVERLAP AT ALL. The bounding boxes overlap by
    1.85 x 0.53 degrees, but of 1,406,525 cells in that window, the
    number carrying data in BOTH files is ZERO. Each clip stops at
    its own national boundary. SO NO BORDER RULE IS NEEDED - a
    straight concatenation cannot double-count, and the FIRST /
    MEAN / SUM / BLEND question does not arise.
  - The nodata strip between them (median ~13 cells) is the
    Akanyaru and Kagera rivers and their lakes, which nobody lives
    on. Irrelevant here because only POPULATED cells are kept.
  - CONCATENATION IS NECESSARY, MEASURED: at 1 km with k=1000,
    1,330 of 46,317 origins (2.9%) draw their neighbourhood from
    BOTH countries, covering 25,359 women 15-19 (1.9%). Rwandan
    shares 5% to 59% at radii of 3-5 km. Run the countries
    separately and those 25,000 women get half a neighbourhood
    with nothing to say so.
  - Scale of the real thing: 11.0 million raster cells -> 3.9
    million POPULATED cells (35%) -> 46,317 origins at 1 km.
    1,341,945 women 15-19 (BDI 624,390, RWA 717,555), both about
    5% of national population.
  WHAT THIS FIXTURE DOES NOT TEST: cell width varies only 0.29%
  across these two countries (both within 4.5 deg of the equator)
  against a factor of 1.25 across Africa. The latitude-varying
  search window of 93 needs a NORTH-SOUTH pair - Sudan and South
  Africa, or Morocco and Tanzania - and is still unexercised.
  A 1 km fixture (46,317 cells, 639 KB) has been cut from this and
  is worth keeping as the continental machine's first regression.
  EFFORT, honestly: folder walk, pattern rule and concatenation
  about a day; the duplicate-cell question is design-then-look, so a
  few days in total. Part of 92, not a new project.
  Also makes 124 acute: fetching hundreds of files with a cache
  keyed only on basename is a collision waiting to happen.

- ~~141~~ | DONE v1.29.6 | A three-way choice in every door - none / median (0.71) / equal-area radius (default) - with John's wording. Safe to change NOW because 1.29.5 was never published, so no saved model holds selfpot as a number; after a release a stored 1.0 would have been reread as choice index 1, the median, silently. The ENGINE keeps a float, so Python and Stata retain the full range. Wording and values pinned across all three copies, plus a test that the middle choice really is the median - 1/sqrt(2), because the equal-area radius scales with the square root of the share, so half the AREA sits at r/sqrt(2) and not at r/2.

- ~~146~~ | DONE v1.29.6 | Both halves. The layer half falls out of 143. The rung half behaves as recommended: boxes the current rung does not read are IGNORED and SAID SO, rather than silently cleared - clearing would destroy work someone may be about to switch back to.

- ~~144~~ | DONE v1.29.6 | Refused in the dialog, before the compute, and shorten_names() now compares case-insensitively so its "collision-free" promise is true. The full names collided too, so shortening was never the cause.

- 149 | open v1.29.5 | suggest_projection() DECIDES BY ZONE
  MEMBERSHIP, NOT BY EXTENT SPAN, and splits runs that need no
  splitting. Found on John's Burundi + Rwanda files, 1.29.5. That
  extent is 2.02 DEGREES of longitude - a third of a UTM zone - but
  it straddles the 30E boundary, so the advice reads:
      "Data spans UTM zones 35 (59%) and 36 (41%). Recommend two
       tiled runs, each in its own zone, with an overlap buffer."
  MEASURED COST OF IGNORING THAT ADVICE: over 20,000 random point
  pairs across the whole two-country extent, a single UTM 35S gives
  a distance error with median +0.09% and a SPREAD OF 0.17% (range
  +0.02% to +0.18%). That is smaller than the sphere-vs-ellipsoid
  error of 0.1-0.4% that John already agreed to print for the
  great-circle route of 93.
  AND THE SPLIT WOULD FALL AT 30E, which runs through the middle of
  both countries - cutting exactly the cross-border neighbourhoods
  that 137 measured (1,330 origins, 25,359 women). The recommended
  workflow would introduce the very error concatenation exists to
  avoid, for an extent a third of a zone wide.
  This is 93's rule stated from the other side: decide by the SPAN
  of the extent, not by which zones it happens to touch. Under 6
  degrees is one zone whatever the boundaries do.

- ~~148~~ | DONE v1.29.6 | _manifest_rows() now carries the settings that DEFINE the numbers - the reference and treatment rungs, the count field, the types, the keepoutside rung, self-potential - and records the true SOURCE rather than the copy it wrote.

- ~~147~~ | DONE v1.29.6 | Refused in the dialog with the two ways out named, rather than after the run with a message blaming OneDrive. dBASE has no null for a number; this was never going to work and the user can be told in advance.

- ~~145~~ | DONE v1.29.6 | "Nothing was changed" is no longer claimed when it is not true, and the cloud-sync note appears only when the reason is genuinely a lock - it fired on three of John's failures in one evening and was the cause of none of them.

- ~~143~~ | DONE v1.29.6 | Every Field parameter now gets parameterDependencies, DERIVED from the declared datatype rather than listed by name - so a new field box cannot be forgotten, which is how this one was. Fixes 146's layer half as a side effect: a real picker is revalidated when its layer changes, a free-text box is not.

- ~~142~~ | DONE v1.29.6 | The internal calibration pass no longer reports its own k as "the k you asked for".

- ~~140~~ | DONE v1.29.6 | The label leads with what it wants: "OR: self-calibrating - ENTER A k, and each point's own Dist_k becomes its half-life (a number, not a field...)". The instruction was fifteen words in and misled the author of the software twice in two days.

- ~~139~~ | DONE, UNRELEASED (version number pending) | A DIAGONAL
  MOVE COSTS THE SAME AS A STRAIGHT
  ONE, so on open ground the effort engine measures CHEBYSHEV
  distance, not Euclidean. FrictionGrid builds 8-neighbour moves with
  `data.append(1 + friction[dst])` - no sqrt(2). Consequences,
  measured on a 25x25 open grid with NO barriers at all:
      k     N_k radial   N_k effort   Dist_k radial   Dist_k effort
      5            5.2          8.6          106.74          142.33
     11           12.8         22.7          204.11          283.75
     50           54.4         71.2          449.24          599.17
  The distance ratio is 1.39, which is sqrt(2) as predicted. So
  ADDING AN EMPTY BARRIER LAYER CHANGES EVERY NUMBER. John, 1.29.5:
  "that is OK" - the model is defensible - but he also ruled the cost
  SHOULD BE SQRT(2), as a CLEAN BREAK with a loud MANUAL row rather
  than a setting, because "a step is a step" was never a considered
  choice.
  It also makes iso-effort contours SQUARES, so rings run 8, 16, 24,
  32 cells against 4-8 for equal distance - measured, largest effort
  ring 112 cells against 16. That is why the overshoot of 99 is
  roughly seven times worse under friction than under distance, and
  why 99 must cover the effort engines from the start.
  Changes every effort result ever produced.

  THE FIX. A step now costs its TRUE LENGTH and the penalty scales
  with it, because friction is a delay per unit TRAVELLED, not a toll
  paid at the door:
      friction.py   step * (1 + friction[dst])
      slope.py      step * (penalty(s) + friction[dst])
  where step = hypot(dx, dy) = 1 or sqrt(2). slope.py had ALREADY
  computed this - `run` uses it for the gradient - and then discarded
  it when building the cost.

  MEASURED, 21x21 open grid, one person per cell, tau budget:
      tau      before (Chebyshev)   after (octile disc)
        1               9                   5
        2              25                  13
        3              49                  29
  "Before" measured against the untouched 1.29.9 archive, not
  recalled. Open ground now agrees with the radial engine exactly at
  k=5, 11 and 25 - an empty barrier layer no longer changes anything.
  Flat DEM still reproduces run_knn_friction exactly, all models.

  THE HONEST LIMIT, now written into the friction.py docstring and
  the rewritten test: an 8-neighbour graph walks only in 45- and
  90-degree steps, so its shortest path is OCTILE, max +
  (sqrt(2)-1)*min. That overstates Euclidean distance by up to 8.2%,
  worst at 22.5 degrees off an axis, zero along an axis or a perfect
  diagonal. Systematic, bounded, declared.

  TESTS. Two pinned the defect as the specification and were
  rewritten: test_tau_flat_grid_is_chebyshev (now
  ..._is_octile_disc) and test_effort_potential_brute_flat, whose
  brute-force reference WAS the Chebyshev distance. A third,
  test_effort_reach_flat_brute, was labelled "Chebyshev" but runs on
  a 3x1 domain where no diagonal exists, so it passed for a reason
  its own comment got wrong; relabelled, and it does NOT discriminate
  this fix. MANUAL.md's validation record asserted the old behaviour
  in three places and was corrected rather than left to contradict
  pytest.

  TWO MUTANTS SURVIVED THE WHOLE SUITE and are now killed by new
  tests. (a) scaling the step but adding friction unscaled -
  `step + friction` - is algebraically identical on open ground and
  on every orthogonal move, so all 353 tests passed it; nothing
  crossed a barrier on the diagonal. (b) the same in slope.py -
  `step * penalty(s) + friction` - survived even
  test_flat_dem_reproduces_friction_exactly, because that fixture
  carries friction 3, high enough that every shortest path routes
  AROUND the barrier and the scaling rule is never exercised. Both
  are now pinned by a 3x3 fixture with friction 1 on the diagonal
  cell, where the direct diagonal IS the shortest path: entering it
  costs sqrt(2)*(1+1) = 2.8284, not sqrt(2)+1 = 2.4142.

  NOT DONE HERE: the MANUAL row John asked for as the loud statement
  of the clean break. The validation record is corrected; the
  user-facing row is not written.

- ~~138~~ | DONE v1.29.6 | Pro refuses an empty rung box exactly as QGIS does, and the verification now compares against what was ASKED FOR rather than what came back - so a dropped treatment can no longer pass a check that only ever saw the output. Guarded.

- ~~99~~ | DONE v1.30 | THE OVERSHOOT: TAKE A PROPORTIONAL SHARE OF
  THE RING THAT CROSSES k. Logged far too narrowly the first time -
  as a seam in Dist_k - and RAISED by John, 1.29.5, who is the
  authority here: "the original EquiPop was developed to counter the
  overshoot effects so this is not a wish. We have to manage this."
  THE HARM, MEASURED. John's example: a 3x3 of cells holding 10 each,
  ask for k=11, receive 50. Claude tested it on a planted SHARP
  BOUNDARY - all of one group west, none east, which is what
  segregation looks like - at k=11, in the cell on the edge:
      whole ring (now)     R_k = 0.20
      proportional share   R_k = 0.02
  A TENFOLD DIFFERENCE IN A SEGREGATION MEASURE, in the exact cell
  where segregation is being measured. The origin's own cell is pure
  one group; the ring rule drags in all four rooks, one of them
  across the boundary, so 10 of 50 come from the other side. At k=25
  they converge (0.20 vs 0.15). So the damage is concentrated at
  SMALL k and AT BOUNDARIES, which is precisely where the value is.
  On a smooth linear gradient the effect nearly vanishes - a
  symmetric ring averages out - which is why it has hidden so long.
  THE RULE, and it is deterministic:
      f   = (k - cumulative_before) / ring_total
      N_k = k exactly
      T_k = T_before + f * T_ring        R_k = T_k / k
  No cell is chosen over another; every tied cell contributes the
  same fraction. This ALSO answers John's seed question of the same
  session, and in the better direction: it removes the arbitrariness
  without needing randomness.
  AND Dist_k FALLS OUT OF ONE FORMULA THAT ALREADY EXISTS:
      r = sqrt(d_prev^2 + f * (d_ring^2 - d_prev^2))
  With d_prev = 0 and the ring being the origin's own cell, that is
  BIT-IDENTICAL to the shipped self-potential formula (verified). So
  95, this, and 100 are one rule with three uses, and half of it is
  already in equipop/selfpot.py.
  SCOPE, honestly:
  - fastcounts needs the ring's START index as well as its end,
    about ten lines; analysis and the effort engines already walk
    ring by ring and are easier.
  - RADIUS RUNS ARE UNTOUCHED - no k, so no boundary ring. Same for
    decay (ND_inf) and tau budgets. A large part of the surface
    disappears.
  - MACHINE 2 CANNOT HAVE THIS UNTIL 118. A quarter of a cell inside
    a median, a Gini or a percentile needs weighted statistics with
    FRACTIONAL weights, which is the person-expansion blocker. So
    counts get it first and statistics lag unless 118 travels with
    it.
  - Every downstream measure consumes N_k/T_k/R_k, so segregation,
    FCA, access and autocorrelation all move; the conformance answer
    key changes; every published number changes. Needs the selfpot
    treatment: a setting, a default, and an exact way back.
  - It produces FRACTIONAL PEOPLE. T_k of 0.25 is an estimate, not a
    person. Defensible for counts and ratios; say so in the help.
  RULED by John, 1.29.5 - THREE OPTIONS, one box, Advanced, in every
  door:
    1. "radial overshoot"              - the whole ring, today
    2. "proportional radial overshoot" - each cell's share, N_k = k
                                         exactly. DEFAULT.
    3. "sampled radial overshoot (seeded)" - cells taken one at a
       time in seeded order until k is reached. Integer people,
       overshoot bounded by ONE CELL rather than a whole ring,
       reproducible from the seed. John ruled it is for the POINT
       ESTIMATE, not for a spread.
  CLOSED v1.30. The last two reds were the SAME defect - NEITHER
  DOOR COULD NAME A MODE - and they are gone the way the item said
  they had to be, not papered over. Both machines in both doors
  carry the box, the shared help and a SEED field; the two
  conformance tests name the mode from the spec rather than
  inheriting a default. 373 green.
  WHAT THE DOOR HALF ADDED, beyond the box:
  - THE SEED IS NOW AN ANALYTICAL BOX. Under `sampled` it decides
    the answer, so by door_parity.py's own stated rule it belongs in
    CORE. QGIS had never offered one and Pro's MACHINE 2 had never
    offered one. Both now do, and both lists carry it.
  - A ZERO-TRAP, caught before shipping. `parameterAsInt` returns 0
    for an empty box, so an untouched QGIS seed would have read as
    seed 0 - every `sampled` run pinned to one draw while announcing
    that none was given. base.optional_int() distinguishes empty
    from zero. The BACKLOG 116 family, and the reason the test for
    it drives processAlgorithm rather than the helper: the FIRST
    version of that test drove the helper, and swapping optional_int
    back for parameterAsInt left it perfectly green. BACKLOG 95's
    lesson, met again in the same shape.
  - MACHINE 2 DEFAULTS TO `whole`, machine 1 to `proportional`, and
    this is forced rather than chosen: run_knn_stats computes
    `chosen = overshoot_mode is not None`, so the moment a door
    passes its dropdown value explicitly an inherited `proportional`
    becomes an EXPLICIT one and every value-statistics run raises.
    Machine 2 still OFFERS all three - the refusal names 118, an
    absent option would explain nothing, and the choice starts
    working by itself when 118 lands.
  - MACHINE 2 SAYS SO, once per run, naming the mode it used and
    machine 1's default. Without it a student runs both machines
    over one dataset and gets two different N_k with nothing said.
    The condition is written against machine 1's DEFAULT so that it
    retires by itself when 118 lands. Note honestly: today it fires
    on EVERY machine-2 run, because both modes machine 2 can run
    differ from machine 1's default. A test asserting a silent case
    was written, failed, and was replaced rather than weakened.
  - Pro's seed label said "only matters where permutations are
    used". From 1.30 that is false.

  THE CONFORMANCE KEY IS NOW PINNED EXPLICITLY, reference.py SPEC
  "overshoot": "whole". The default flip had silently invalidated it -
  2287 of 2360 rows moved - because it inherited whatever the default
  was. A key that proves DOORS agree with the CORE must not move when
  an unrelated default moves. Pinned to `whole` and not to the new
  default because the spec asks for mean, median and Gini, which
  `proportional` refuses. GAP RECORDED, BACKLOG 162: the doors are
  therefore certified only under `whole` while most users will get
  `proportional`; a second key - counts, shares and distances only -
  is needed.

  JOHN, 1.30, on 118: shares and distances matter more than the
  awkward value statistics, and those can be dropped if they block
  progress. That makes 118 far less of a barrier than feared.

  FIVE ENGINES, NOT FOUR. run_knn_stats - machine 2 - walks its own
  neighbour list and was missed. It disagreed with machine 1 on
  Dist_50 (570.71 against 583.09) until wired. All five now agree to
  ZERO in all three modes.

  TWO DEFECTS FOUND WHILE UPDATING THE CHECKS, both mine, both
  invisible under `whole`:
  (a) the self-potential equal-area radius was handed the SHARE
      reported instead of the people standing in the cell. Under
      `proportional` N_k is k exactly, so the radius became a
      constant - 56.42 m where 10.30 m was right. Five of the
      seventeen red checks were this, not the default flip. I had
      told John the seventeen were "the default flip and nothing
      else"; a defect that only appears under the new default hides
      from exactly the test that claim rested on.
  (b) an edit script asserted and died BEFORE writing, so a signature
      change was silently lost and only surfaced as a TypeError two
      steps later.

  THE DEFAULT FLIP BREAKS MACHINE 2 - NEEDS JOHN. `proportional`
  cannot produce a median, percentile or Gini, so making it the
  DEFAULT means every value-statistics run refuses without the user
  having chosen anything. Interim rule, pending his ruling: an
  EXPLICIT proportional + value statistics is refused; an inherited
  default falls back to `whole` and PRINTS why. Machines 1 and 2 then
  still agree wherever both can answer. Properly fixed by BACKLOG 118
  (weighted statistics with fractional weights), which is also the
  continental blocker.

  PROGRESS v1.30. equipop/overshoot.py holds the shared rule; all
  FOUR engines call it - both radial (fastcounts, analysis) and both
  effort (friction, slope, via _count_from_grid). Measured, unequal
  cells, k = 11/25/60: every engine agrees with every other to ZERO
  in all three modes. Under `whole` the whole suite is green (355),
  so the wiring changes nothing on its own; the 17 red checks are the
  DEFAULT FLIP to proportional, ruled by John, and nothing else.

  THE SAMPLED DISAGREEMENT IS SOLVED, and the cause was not ordering.
  The engines could not agree on what a CELL IS: the fast engine
  knows a cell by its row in the file, the ring engine stores only
  (count, group) keyed by grid position and never sees a row number.
  Identity now comes from GRID POSITION - overshoot.cell_identity -
  which both already hold. Stronger than John asked for: a re-sorted
  or re-exported file now reproduces a seeded run exactly.

  That fix exposed a second disagreement, proportional, up to 28
  people. Cause: the ring engine handled the ORIGIN CELL before its
  ring loop began, so a k smaller than the origin's own population
  still reported the whole cell. The origin is a ring too - a ring of
  one.

  FOUND BY JOHN'S HAND CHECK: k <= 0 was ACCEPTED by every engine,
  returning zeros and NaN. k=0 asks for nobody and each mode then
  answers differently about a neighbourhood that does not exist. All
  four engines now refuse.

  STILL TO DO: the 17 checks, of which 6 are the conformance answer
  key - John ruled it regenerated under proportional, anchored to the
  hand-check workbook rather than to this code; the doors (boxes,
  help, seed field); and the MANUAL row.

  Note what 2 and 3 are to each other: 2 is the EXPECTED VALUE of 3
  over every possible draw. So 3 as a point estimate is 2 with noise.
  Say that in the help rather than let someone discover it.
  *** CORRECTED v1.30, MEASURED, NOT ARGUED: THAT IS FALSE. ***
  Sampled is proportional ROUNDED UP TO A WHOLE CELL. The two agree
  when the shortfall is a whole number of cells; otherwise sampled
  overshoots to the next cell boundary and averaging draws does NOT
  converge on the proportional answer - the overshoot is systematic,
  not noise. Ring of 8 equal cells, core of 10, ring share 0.75:
      shortfall/ring   proportional N/R    sampled mean N/R
          0.0125        11.00 / 0.9773     20.00 / 0.8736
          0.05          14.00 / 0.9286     20.00 / 0.8736
          0.125         20.00 / 0.8750     20.00 / 0.8736
          0.25          30.00 / 0.8333     30.00 / 0.8341
          1.00          90.00 / 0.7778     90.00 / 0.7778
  The entry's own worked example already contradicted the claim -
  proportional 11, sampled 20 - and it went unnoticed for four
  sessions because the sentence read plausibly.
  THE CONSEQUENCE JOHN MUST RULE ON: on the k=11 case that motivated
  this whole item, sampled still overshoots by 82% and reads R 0.874
  against proportional's 0.977. Sampled REDUCES the overshoot (50 to
  20) but does not remove it. It buys whole people and a bound of one
  cell. Whether that is worth a third mode is his call.
  With UNEQUAL cells there is a second effect on top: a large cell is
  more likely to be the one that crosses the threshold, so sampled
  over-represents large cells. Measured (3,11,2,24), need 7:
  proportional R 0.4250, sampled mean R 0.3225.
  THE SEED MUST BE PER-ORIGIN. One shuffle order applied everywhere
  would favour the same direction at every origin - a spatial
  artefact worse than the thing it fixes.
  APPLIES TO EFFORT RUNS FROM THE START (John: "do both") - it is the
  same code path, and the overshoot is WORSE there: see 139.
  CONTINENTAL DEFAULT IS 2, WITH THE REASON PRINTED, and 3 is not
  forbidden. The reason is not speed: WorldPop counts are FRACTIONAL
  MODELLED ESTIMATES, so option 3 has no whole people to preserve and
  buys only noise. Forbidding it outright would make the continental
  machine answer differently from the local one for convenience,
  which is the "two doors disagree" family that has bitten this
  project three times in one week.
  COST: 1 and 2 are two lines apart and stay array arithmetic; 3
  needs a per-origin shuffle and RNG and cannot be reduced to it.
  STILL UNRULED: whether machine 2 waits for 118.

- 100 | open v1.29.5 | MedDist_k AS ITS OWN COLUMN. Also ruled in
  during design and deferred with 99. The MEDIAN distance to a
  neighbour is an accessibility measure the literature largely
  lacks, and it must NOT be folded into Dist_k, which is an outer
  radius - one column meaning two things is the silence this project
  keeps catching. Note the engine can do better than r/sqrt(2): it
  knows the population of every ring it visited, so the true median
  can be computed exactly, with no evenness assumption at all.
  r/sqrt(2) is only what you get when density is flat.

- 97 | open v1.29.5 | RULED IN by John, 1.29.5. A DECAYED
  DENOMINATOR IS NOT A COUNT. If machine 3 uses decay to handle
  sparse cohorts (John's 4c), the person-years behind a rate become
  a WEIGHTED sum, and the standard error must use the EFFECTIVE
  sample size n_eff = (sum w)^2 / sum(w^2), not sum(w). Reporting SE
  from the weighted sum understates the uncertainty, silently, and
  worst where the cohort is thinnest - which is the case the decay
  was introduced to rescue. The engine already computes
  ND_inf = sum(n*w); adding sum(n*w^2) is one line and makes an
  honest SE possible. Ties to the E&W 5000 person-year threshold:
  with decay the threshold must be read against n_eff.

- 98 | open v1.29.5 | MORTALITY BY YEAR DIFFERENCING: NEVER CLAMP
  THE NEGATIVES. RULED by John 1.29.5 after Claude simulated the
  alternative. Two WorldPop years are separately modelled surfaces,
  so their difference carries model revision as well as mortality
  and a large share of cells imply NEGATIVE deaths. John asked
  whether clamping to zero would be easier; it is not, it is wrong:
    model error   % cells negative   raw mean   clamped   bias
             2%             36.1%       2.00      3.39    1.7x
             5%             44.2%       2.06      6.71    3.4x
            10%             47.0%       2.00     12.25    6.1x
            20%             48.7%       2.07     23.52   11.8x
  (true deaths 2.00/cell, 200 000 cells.) The RAW difference is
  unbiased at every noise level - the negatives are the other half
  of a symmetric spread and are what makes the mean correct.
  Clamping deletes that half and inflates mortality 1.7x to 11.8x,
  worst where the data is weakest. The negative FRACTION is also the
  best available diagnostic of how much of the surface is model
  noise. So: keep the raw value, report the count and the fraction,
  never clamp and never null. Same family as 1.27.0's facilitators,
  where truncating below zero silently ignored the input.


- ~~94~~ | DONE v1.29.5 | Reported rather than left in the data: both engines now say how often N_k reached at least twice the k asked for, through one shared function so they cannot describe themselves differently. The COLUMN was not added - that is a schema change across both doors and did not belong in a three-item release.


- 92 | open v1.29.3 | THE CONTINENTAL DATA PATH. Designed with John
  in the 1.29.3 session; it lived only in the handover until 1.29.5,
  which is why it arrives late. Grounded on the real WorldPop Kenya
  page (hub.worldpop.org id=81758): 63 GeoTIFFs, ~66 MB each,
  3.78 GB zipped; 20 age bands (0, 1-4, 5-9 ... 90+) x three genders,
  3 arc-second, WGS84, counts per grid square.
  - A THIRD OF EVERY DOWNLOAD IS REDUNDANT: t_XX = f_XX + m_XX.
  - NEVER FETCH THE ZIP. The .tif URLs follow a strict pattern, so a
    tool that knows its cohorts can name its own files: ASFR needs
    f_15..f_45, SEVEN files, 464 MB rather than 3.78 GB.
  - SCALE DECIDES THE ARCHITECTURE. Africa at 1 km is ~30 million
    cells per layer, ~1 GB for 40 layers of populated cells - it fits
    in memory and needs no tiling of the destinations. At 100 m it is
    ~3.0 BILLION per layer, ~73 GB, and must stream. Same code path;
    BUILD AND TEST AT 1 km.
  - CACHE THE EXTRACTION ONCE to populated cells only, in Parquet.
    Same insight as 68: reading was the cost.
  - Note against the existing code: equipop/raster.py already reads
    WorldPop-shaped rasters and already keeps only populated pixels,
    and bigrun.py already flushes to Parquet with a manifest. The
    missing pieces are the cohort-aware file naming, the cache, and
    a door.

- 93 | open v1.29.3 | THE WORKING FRAME - John's ruling: CHOOSE BY
  EXTENT, NOT BY FORMAT, AND OFFER WGS84. Designed with John in the
  1.29.3 session and likewise recorded late.
  Degrees and metres are not in conflict: a great-circle distance
  gives TRUE METRES from degree coordinates, so k, radii, tau and
  Dist_k all keep their meaning and stay comparable with a projected
  run. Measured cost: a sphere against the ellipsoid is out by
  0.1-0.4% (12 m at 11 km near the equator) - say the number rather
  than calling it negligible.
  - Extent under one UTM zone (6 deg of longitude) auto-projects
    exactly as today. MALTA IS UNCHANGED.
  - 6 to 20 deg projects with a WARNING carrying the measured scale
    error.
  - Beyond that, WGS84 with great-circle, said plainly.
  - John's worry, and it is the right one: a Malta-sized WGS84
    dataset where the user thinks in metres must keep working
    without them thinking about any of this.
  - THE CELL BOX STAYS IN METRES (no new unit for students), but
    with raster input it SNAPS to a whole multiple of the source
    grid, because any other value resamples the raster - the very
    destruction we are avoiding. A 3 arc-second cell is 92.8 m TALL
    everywhere and 92.8 / 89.6 / 84.1 / 76.0 m wide at 0 / 15 / 25 /
    35 degrees; across Africa the width varies by a factor of 1.25,
    far less than any single projection would impose.
  - TOOL HELP IS PART OF THE JOB, NOT A FOOTNOTE (John): both doors
    must state the scales at play - "you asked for 100 m; using 1 x
    the source grid, cells are 92.8 m tall and 92.8-76.0 m wide
    across your extent; no resampling".
  - AND IT WOULD FAIL SILENTLY: the fast pass sizes its neighbour-
    cell window from an assumed UNIFORM cell size. With degree cells
    that varies with latitude, so the window must be sized for the
    WIDEST cells in the extent, or the search stops short and
    returns a k-neighbourhood that is not one.
  - Note against the existing code: equipop/projection.py already
    decides by extent, but its answer beyond two UTM zones is an
    equal-distance compromise CRS or an A/B tiled run - NOT WGS84
    with great-circle. This ruling supersedes that branch and the
    module must be told.

- 90 | open v1.29.3 | THE DECAY-TRUNCATION SPIN BOX STEPS BY 1 IN
  QGIS, so a stray scroll or click moves 0.000001 to 1.000001 and
  nothing objects: the run succeeds and the number is nonsense.
  The classic silent wrong answer. Set the step and the decimal
  places to match the quantity, and say something above a plausible
  ceiling. (John's locale renders it 0,000001.)

- 87 | open v1.29.3 | THE SIMULATED ARCPY RESOLVES ANY STRING IN A
  VALUE TABLE TO A LAYER PATH, so 'bar' arrives as 'memory/bar' and a
  test that fills reftable through the dialog is refused with "these
  values are not in the category field". Found while writing the
  behavioural parity test for 86, which had to be driven at
  _run_tool instead. A stub that is WRONG rather than merely sparse:
  it makes a real path untestable through the dialog, which is
  exactly where John meets it.

- 88 | open v1.29.3 | POLYGON BARRIERS have never been run in Pro.
  1.29.3 fixed the QGIS path after John's crash, and _paths_of is a
  QGIS-side function - but nobody has pointed the ArcGIS toolbox at
  a lake either, and the two doors build their geometry payloads
  separately. One field run answers it.

- 91 | open v1.29.3 | RULED by John: SHORT DECAY LABELS IN BOTH
  DOORS, with the explanation moved out of the dropdown text and
  into HELP["model"] where the shared help already lives. One text,
  two doors. Travels with the next release that touches the doors.

- 89 | open v1.29.3 | THE OUTPUT-TABLE RULE IS OVER-STRICT. It asks
  "is the input a table?" and never "has the user already said where
  the output goes?", so a run that has named its own output is
  refused anyway. Found by John in the field, 1.29.3.

- ~~85~~ | DONE v1.29.3 | THE TREATMENT LADDER IS IGNORED UNLESS THE
  REFERENCE LADDER IS ON RUNG 3 - QGIS door only. alg_counts.py line
  ~267 nests the whole grouping block inside `if refmode == 2 and
  catfield:`, so treatmode=2 does nothing when refmode is 0 or 1.
  John, field, 3.42.1: refmode=0, treatmode=2, treatcatfield=fclass,
  treattable=[bar, social] produced N_223 and Dist_223 and NOTHING
  else - no T_, no R_, and NO MESSAGE. Reproduced here: the same run
  with refmode=2 gives T_social_100 and R_social_100.
  The two ladders are INDEPENDENT by design - that is what separating
  reference from treatment was for in 1.22.0. Pro is correct: it
  passes ref_mode and treat_mode to _run_tool and lets the shared
  engine decide. QGIS reimplemented the logic locally and coupled
  them. So the doors agree perfectly on NAMES and disagree on
  BEHAVIOUR - which door_parity.py cannot see. Predates 1.29.2.
  WHILE THERE: John also filled reftable while on rung 1, where it
  is ignored. QGIS Processing cannot grey boxes out as Pro does, so
  nothing stopped him. A box that is filled but ignored must SAY so.

- ~~86~~ | DONE v1.29.3 | PARITY IS CHECKED FOR NAMES, NEVER FOR
  BEHAVIOUR. tests/door_parity.py asks whether both doors offer the
  same boxes. It cannot ask whether the same boxes DO the same
  thing, which is how 85 lived undetected. What is wanted: one
  fixture, the same inputs through both doors, and the result
  columns and values compared - the cross-door conformance reference
  already does this for a single default run, so the machinery
  exists; it needs to cover the LADDER combinations. Worth more than
  the fix for 85, because it catches the next one too.

- ~~84~~ | DONE v1.29.3 | RAISE qgisMinimumVersion TO 3.38 and clear two
  deprecations (John's ruling). QGIS 3.42 warns on every run:
  parameterAsFields() deprecated in 3.40, use parameterAsStrings()
  (added 3.32); and the QgsField(name, QVariant.Double) constructor,
  from the QVariant -> QMetaType migration around 3.38. 12 call
  sites for the first, 1 for the second. The declared minimum is
  3.28, so BOTH replacements are newer than what we promise - hence
  the ruling to raise it rather than write fallbacks.
  NOTE THE NEW CLASS OF DRIFT: stub_audit.py checks that a method
  EXISTS, and a deprecated method exists perfectly well. The
  simulator cannot see "this works but is dying" at all. The cheap
  guard is free, because QGIS already does it: read the QGIS log
  after a field run and treat a DeprecationWarning as a release
  blocker. That is how these were found.

- ~~83~~ | DONE v1.29.2 | MACHINE 2 CANNOT GIVE RESULTS TO A NON-MEMBER,
  and machine 1 can. John's rule since 1.22.2 is that a row outside
  the reference population counts as ZERO - nobody's neighbour - but
  still gets its own results. In stata_bridge.dispatch the stats path
  does `valid = valid & (rep > 0)`, so a zero-weight row is dropped
  as an ORIGIN and _map_back gives it NaN. Measured, identical setup,
  600 rows with 300 outside: machine 1 Null for 0 of 300, machine 2
  Null for 300 of 300. Not a co-location artefact - scattered and
  co-located behave the same.
  Exposed by the 1.29.2 ladder, which gave machine 2 its first way of
  putting a row outside the reference population; the inconsistency
  had simply been unreachable before.
  John's ruling: make it the USER's choice (option C). The box
  already exists and already says it - `keepoutside`, "give them
  results, counting as zero" / "leave their results Null" - so the
  dialog is right and only the engine has to catch up. Default stays
  "give them results", matching machine 1.
  THE HARD PART: a zero-weight row alone in a 100 m cell has no cell
  in the population grid, so the engine needs an origin that is not
  a member. Own round, with its own tests.
  ALSO FIXED HERE: the engine PRINTED "they still receive their own
  results" while doing the opposite. A false reassurance is worse
  than silence.

- 82 | open v1.29.2 | MACHINES 3 AND 4 SHIP SEPARATELY, as
  `equipop-demography` (John's ruling, 1.29.2 session: "alternative
  A"). Machine 3 = demographic measures (life expectancy, fertility,
  CDR/CBR/ASFR, dependency ratios); machine 4 = space syntax. The
  reason is access control during development, and the honest form
  of that is DISTRIBUTION, not a password: EquiPop is MIT and public
  on PyPI, so any check inside shipped Python is a line the reader
  can delete. A second wheel, given to named people, actually
  controls access - and demographic estimates that reach print must
  stay auditable, so obfuscated analysis code would fight the very
  purpose of the tool.
  WHAT THIS NEEDS FROM THE DOORS FIRST: provider.py hard-codes its
  two algorithms and the .pyt hard-codes its two tools, so a machine
  living in another package cannot appear at all. The doors must
  DISCOVER machines rather than list them. That is the same change
  that lets tests/door_parity.py scale past two hand-written lists,
  and it rests on the discipline fixed in 78 - a missing half gives
  absence and a sentence, never a traceback. Order: 78 (done),
  then discovery, then the machines themselves.

- 81 | open v1.29.1 | THE BOOK DOES NOT MENTION QGIS. Not once, in
  any of the fifteen chapters - checked. There is ch15 for the
  ArcGIS door and ch16 for Stata, and nothing for the door John
  actually teaches with. The QGIS door shipped in 1.20.0, has been
  field-tested twice (Malta, 1.26.1) and reached parity with Pro in
  1.29.0, so a reader of the Book would not learn it exists. John's
  instruction (1.29.1): the QGIS plugin should be covered the same
  way the Pro toolbox is. NOT a chapter to bolt on in a hurry - the
  Book's principle is that the two doors are the SAME document with
  different pictures, so ch15 and the new chapter should be written
  as a pair and the parity of 1.29.0 is what makes that honest now.
  Queued deliberately for the NEXT BOOK RUN, with the other writing
  items (42), not squeezed into a code release.

- ~~78~~ | DONE v1.29.2 | THE PLUGIN DIES AT LOAD when the equipop
  package is older than the plugin. `alg_counts.py` calls
  `_decay_choices()` at MODULE level, so the import runs before QGIS
  has an algorithm to attach a message to - and every guard
  (`check_versions`, the DoorError contract, the "install equipop"
  sentence) lives inside `processAlgorithm`, which fires on Run. The
  sentence explaining exactly this situation is already written and
  cannot reach the user. FIX: build the decay list on first USE, and
  port the ArcGIS lazy-import test (which fails if the discipline is
  broken) to the QGIS door. Cost John an hour in the field, 1.29.0.
- ~~79~~ | DONE v1.29.5 | icon.png shipped at 128x128 RGBA: the origin, its k nearest inside the radius, and the ones beyond it faded. Checked at 24 px, where QGIS is smallest. The lasting part is the test: metadata.txt may no longer name any file the plugin does not carry.

- 80 | open v1.29.1 | Run `tools/stub_audit.py` in a live QGIS as
  part of every release that touches the QGIS door, and record the
  result in the MANUAL validation row. It is the only check that can
  see the simulator flattering itself; 1.29.1 exists because nothing
  did. NOT CLOSEABLE BY CLAUDE, ever: it needs real PyQGIS, so it is
  John's on every release, permanently.
  RUN AND PASSED FOR 1.29.8 (John, QGIS 3.42.1-Münster): 63 methods
  and constants checked, no classes skipped, NO GAPS - "the
  simulator is not flattering itself". Recorded in the MANUAL
  validation row, which is what this item asks for. It reopens for
  the next release that touches the QGIS door.
  1.29.5 did what could be
  done from here - the tool now EXPLAINS itself and exits 2 instead
  of raising ModuleNotFoundError at whoever runs it in the wrong
  place, and the message names this item and where to run it.

- ~~68~~ | DONE v1.29.2 | Reading a GeoPackage in QGIS took 5.5 s against 0.3 s
  of calculation (John, field, 8730 points). read_points builds a
  Python list of features and loops per attribute. Worth optimising
  before continental work.

- ~~76~~ | DONE v1.29.2 | THE MACHINE 2 LADDER. 1.29 gave machine 2
  machine 1's words and made insertion safe (it now reads its boxes
  by NAME); the ladder itself was deferred by John - "change the
  words first, we can test the ladder later". What is missing: a
  `refmode` question with the same three rungs, `catfield` +
  `reftable` for rung 3, and `keepoutside` for the zero-versus-null
  rule. Capability, not tidying - today machine 2 cannot restrict
  its reference population at all, so "mean income of the nearest
  400 RESIDENTS" in a layer that also holds workplaces is
  impossible. Add the new names to tests/door_parity.py CORE_M2 in
  the same edit, and to QGIS's alg_stats.py, or the parity check
  fails - which is the point of it.

- 67 | open | QGIS barriers are simulator-proved only. The ArcGIS
  round is the evidence for how far that is from proved.

- 58 | open | A GeoPackage barrier layer has still never been run in
  the field. The code path is now believed sound; only Pro can say.


- 42 | open v1.18.0 | docs/manual/ (the illustrated ArcGIS
  walk-through) does not describe variable-bandwidth decay at all -
  the headline feature of 1.17. Decay gets one sentence in section 2
  and the ND_/TD_/RD_ columns in section 7, with nothing on
  half-life from a field or self-calibration from Dist_k. WRITING
  session item. While there: the manual's own plain-words habit
  ("two rulers", "doubling it quarters the work", "a finding, not a
  nuisance") is the model the queued naming pass should copy.

- ~~44~~ | DONE v1.47.6, CONFIRMATION PENDING | `make_help_xml.py`
  still writes `SyncOnce=TRUE`, the suspected cause of item 34
  (summary/usage rendering empty in Pro). Untouched this round: it
  needs one field cycle to confirm, and this was a refactor release.
  Now a one-line change in a single place whenever that cycle happens.
  THE ONE-LINE CHANGE IS MADE in 1.47.6:
  SyncOnce=FALSE, which tells Pro the metadata is authored and not to
  synchronise its own over the top. Struck because the change this
  item describes is done - but it was ONE OF THREE faults found in the
  same breath, and the other two (an unshipped sidecar, plain text
  where escaped HTML belongs) are at least as likely to have been the
  cause. See 34. Do not read this as proof that SyncOnce was the
  problem.

- ~~34~~ | DONE v1.47.6, CONFIRMED IN THE FIELD | Tool help page:
  summary/usage sections render empty in Pro. Suspect SyncOnce=TRUE
  letting Pro regenerate over the authored text, plus missing
  datatype attributes and plain text where escaped HTML is expected.
  The per-parameter comments (dialogReference) DO work | Needed one
  field cycle to confirm.
  OPEN FROM v1.16.8 TO v1.47.6 - thirty releases - and closed by John
  in session 12: "all good, ? page is good".
  THE HEADLINE OF THIS ITEM WAS WRONG THE WHOLE TIME. Summary and
  usage were never empty for the tools that had a sidecar. What was
  empty was the per-parameter EXPLANATION COLUMN of the '?' page, for
  text that was present in the XML and rendering perfectly in the
  dialog flyout beside the same box. The item's own second sentence -
  "dialogReference DOES work" - was half right and hid the other
  half for thirty releases.
  WHAT WAS CHANGED: SyncOnce TRUE -> FALSE (44), and the parameter
  comments written as escaped <p> paragraphs instead of plain text -
  which was this item's own guess, made in v1.16.8.
  WHICH ONE FIXED IT IS NOT KNOWN. Both shipped together and John
  reported the outcome, not the cause. `make_help_xml.py --plain`
  regenerates without the markup and would settle it in one cycle if
  anyone ever needs to know. RECORDED AS UNATTRIBUTED rather than
  credited to the more interesting of the two - a fix whose cause is
  guessed at is how 44 sat open for twenty-nine releases on a
  suspicion nobody tested.
  AND THE EVIDENCE THAT CLOSED IT ALMOST CLOSED THE WRONG ITEM.
  John's first screenshot - an empty flyout - was recorded here as
  the long-awaited field cycle. It was a STALE SIDECAR: his XML held
  38 parameters and no `originrule`, because he had replaced the .pyt
  and not the .xml, following a guide that said "FOUR files" and
  listed three. His second - machine 3's '?' page, entirely blank -
  was BACKLOG 294, a tool with no sidecar at all. Only the third
  answered this item. THREE PIECES OF EVIDENCE, THREE DIFFERENT
  CAUSES, and the first two both looked exactly like this one.

- 49 | open | The reference covers counts and stats; friction,
  slope, fca and lisa are not in it. Now that a second door exists
  and the mechanism is proved, this is worth doing.

- ~~45~~ | DONE v1.47.6 | (1.29.0 note: the BOOK build does it too - docs/book/build.sh leaves gamma_decay_figure.png in the repo ROOT, because examples/cookbook_01 writes relative to the working directory. Same fix, same item.) The simulated-arcpy tests write their output to
  the Windows-style catalog paths they pretend to use, so a test run
  on Linux leaves four literal files named `C:\Data\...csv` in the
  repo root (and one stray figure from the Book build). Harmless,
  untracked, and cleaned by hand this round - but they belong in
  pytest's tmp_path, and on Windows those paths are real. Small.
  CLOSED v1.47.6, AND ONLY HALF OF IT WAS STILL TRUE. Measured by
  running the suite on a clean tree: the four `C:\Data\...csv` files
  did NOT recur and appear to have been fixed earlier without anyone
  narrowing this entry. What DID recur was two files the item never
  named - arcgis/EquiPop.CountsShares.pyt.xml and
  EquiPop.ValueStatistics.pyt.xml, written on every run by
  make_help_xml.py. Build outputs, neither committed nor shipped,
  that the repo only ever held by accident.
  make_help_xml.py now takes --out and the test passes tmp_path.
  GUARDED BY RUNNING THE GENERATOR and looking at arcgis/ afterwards,
  not by reading the call - a test that writes into the tree it is
  testing can mask the change it exists to catch.
  THE LESSON IS THE STALE HALF, not the fix. This entry described a
  symptom that had already gone and missed one that was still there,
  so anyone working from it would have fixed nothing. An item is only
  as good as its last measurement.

### 1.18.0, second pass: the source archive

- 62 | open | The shapefile-in-a-map warning fires whenever the
  input is a .shp and the output is not a new feature class. It may
  be too eager - a shapefile NOT in a map is fine, and the toolbox
  cannot tell from the path alone. Watch whether it becomes noise.


- 41 | open v1.18.0 | MANUAL.md had NO 1.17 row - the release went in
  without its version row, validation record or design decisions,
  against the standing convention. A reconstructed row was written
  in 1.18.0 from the session handover and is marked as such; **John
  should check it against what actually shipped.** The 1.17
  validation record was deliberately NOT reconstructed: writing one
  would mean claiming validation nobody performed.

- ~~43~~ | DONE v1.40.2, see the entry above | CITATION.cff still says
  `version: 1.0.0` while the package is at 1.18.0. Left alone
  deliberately - citation metadata is the author's to set, and it
  matters more than usual ahead of the Zenodo DOI at 2.0.0.
  THIS COPY WAS STALE AND IT COST A ROUND TRIP IN SESSION 12. Item 43
  closed in 1.40.2: only the `version:` field moves, it is PINNED BY A
  TEST against the package, and it is therefore a mechanical bump
  rather than an author's decision. Reading this copy, Claude put it
  to John as "author's call", John reasonably answered "no update for
  now", and the release then failed its own citation test.
  The author's part - the preferred-citation, the 2014 report, the
  affiliation - is untouched by a version bump and remains John's
  alone. Struck here so the file holds one answer.

- 77 | open v1.29.0 | The vocabulary sweep. 1.29 made the shared
  `pop` entry neutral (John: a point may stand for services, jobs,
  houses, anything), but "persons" survives in about fifteen other
  places - help.py entries for k/treat/tau/groupscount, both tool
  descriptions in the .pyt, QGIS's tau label, the SUMMARY for
  machine 1. Deliberately NOT swept in 1.29: fifteen sentences John
  has not read is not a change to make quietly. One pass, shown
  before it lands. Note `groups_count="persons"` in the .pyt is a
  CODE VALUE, not prose - do not touch it.

- 38 | open v1.16.8 | Continental segmentation wired into the GUI: origin tiling (bigrun, already built and tested, currently unreachable) with output folder + resume; halo-based full partitioning only if destinations stop fitting, with the halo checked against Dist_k and widened for the origins that touched it; merge on an explicit EQP_ID, never OID (ArcGIS renumbers OIDs on copy) | John's B1-10/C1-2 sketch
  DIALOG DESIGN AGREED WITH JOHN, 1.29.5, in two rounds - and
  EXPLICITLY NOT LOCKED ("let us develop them in the rounds to
  come"). Three tools, not one, because a run of hours must survive
  the door being closed:
  (1) PREPARE - measure (population composition / ASFR / life
      expectancy & mortality / dependency ratios / infant mortality)
      drives everything below; source is a raster folder, the named
      rasters fetched, OR A POINTS LAYER (CSV, shapefile,
      GeoPackage, database table - John, round two: rasters are
      common in this world but so is everything else); area; years
      with three-year pooling as default; SPLIT BY GROUP - sex,
      ethnicity or any other, NOT "split by sex" (John, round two;
      note that on the raster path the only group WorldPop carries
      is sex, so there the box reads the file naming, while on the
      points path it picks a field); mortality-by-differencing
      switch; cache folder; advanced cell size, snapped.
      Prints before acting: which cohorts the measure needs and so
      which files; the frame decision of 93 with its measured error;
      the scale report; and the negative-death count of 98.
  (2) RUN - cache folder; k VALUES as a list (already in the engine,
      John's "several k per cohort, they tell different spatial
      stories"); optional PER-COHORT k override table (the new box);
      bandwidth none / fixed / from a field / SELF-CALIBRATING from
      Dist_k (John's "decay on the k" - it is the 1.17 feature, see
      96); decay model; SELF-POTENTIAL (95); output folder; resume;
      advanced tile size and radii.
  (3) COLLECT - run folder; columns, which the measure knows
      (ASFR_15_19, Events_15_19, SE_15_19, Dist_k_15_19,
      MedDist_k_15_19); output format; verify checksums. Prints the
      plausibility summary including 98's negatives and where a
      decayed n_eff falls under the E&W 5000 person-year threshold.
  Note that bigrun.py ALREADY provides (2)'s substrate - origin
  tiling with a global tree, so results are exactly the untiled
  ones, plus parquet flush, manifest, md5 and resume. At 1 km the
  destinations fit in memory and there is NO halo problem at all;
  halos arrive only at 100 m.

- 59 | open | Does the QGIS door refresh GeoPackage fields properly?
  Expected yes (OGC format, QGIS's native default). If so it is a
  real argument for teaching on QGIS with .gpkg data - worth knowing
  before September.


- 61 | open | The dialog structure is simulator-proved only. Whether
  three rungs and the greying READ well in Pro is John's call.


- 55 | open | The dialog-structure tests assert Pro's `category` and
  `enabled`; the simulator honours both, but only a real Pro can say
  whether the three headings read well on screen. Worth a look in
  the next field cycle.


- 54 | open | Gridby has NO missing data, so the missing-data rules
  are tested only on small fixtures. A Gridby variant with holes
  punched in it would test the documented rule properly.


- 57 | open | The old single-table path (cat_rows) is kept in
  _run_tool for compatibility but is no longer reachable from the
  dialog. Retire once John confirms no saved tools depend on it.


- ~~65~~ | ANSWERED v1.29.5 | Not a defect and nothing to hunt. The
  sync-folder warning is raised in updateMessages() as a PARAMETER
  warning, so it appears beside the output box in the dialog and
  NEVER in the messages pane - which is the only place John was
  looking, both times. Confirmed against a 1.29.5 Pro run of his
  whose output sat in "OneDrive - OsloMet" with no such line in the
  log. Worth remembering when reading any field report: a Pro
  parameter warning and a Pro run message are two different surfaces.

- 40 | open v1.16.8 | Gridby README: Test E must say to clear BOTH the population field and the group count fields (the key assumes one row = one person) | Documentation error found in the field

- 3 | open v1.29.5 | HEXAGONS ARE THE PRINCIPLED FIX FOR 139, not a
  patch. Raised by John, 1.29.5: "a hexagonal growth is in principle
  easier since rook/queen patterns are replaced with equal
  distances." Half right, and the half that is wrong matters:
  MEASURED tie groups, nearest first -
      HEX   : 6 at 1.000, 6 at 1.732, 6 at 2.000, 12 at 2.646
      SQUARE: 4 at 1.000, 4 at 1.414, 4 at 2.000,  8 at 2.236
  The smallest step out is SIX cells on hex against FOUR on square,
  so for the overshoot at small k hexagons are slightly WORSE, and
  ring 2 is not uniform either. The "all equal distances" intuition
  holds only for the immediate neighbours.
  WHERE THEY WIN IS 139. All six neighbours are genuinely
  equidistant, so "one round = one step" is a CORRECT model of
  movement and the sqrt(2) correction is unnecessary - the problem
  does not exist rather than being patched.
  equipop/hex.py ALREADY EXISTS and yields a standard CellData, so
  the radial engine works on hexagons today. Its own docstring names
  the gap: "The 6-neighbour graph for hexagonal FRICTION growth is a
  separate, future addition." That is the piece worth building.
  BUT HEXAGONS ARE WRONG FOR RASTER INPUT. WorldPop arrives on a
  square 3-arc-second grid; binning it to hexagons means resampling,
  which is exactly what 93's snapping rule exists to prevent. Hex
  suits point data and the effort engine, not the continental path.
  Minor bonus: the self-potential formula is AREA-based, so
  sqrt(A*k/(n*pi)) is unchanged, and a hexagon is rounder than a
  square so the equal-area circle fits more comfortably inside it.

- 4 | open | Heights / third dimension (D-dimensions) for grids AND hexagons | No suitable test data yet — design can precede data. Thoughts below.


- 66 | open | Editing multi-line Python by blind string replacement
  damaged alg_counts.py this round; recovered from the release zip.
  Read the real text first (view/sed), then str_replace against it.


## Design notes and longer thoughts (kept, not a to-do list)

## Item 2 — Metadata log file, agreed design

**Core idea:** one immutable sidecar per run, machine-readable, doubling
as a re-run recipe.

- **Format:** JSON sidecar named after the output
  (`output.csv` + `output.meta.json`), plus an optional human-readable
  `.meta.txt` rendering (spirit of the original EquiPop metadata.txt).
- **Re-runnable provenance:** the `settings` section mirrors the function
  parameters exactly, so `equipop.rerun("output.meta.json")` reproduces
  the run — absorbs the "log-file as script" idea from the original
  specification without generating Python code.
- **Six sections:**
  1. `run` — run id, timestamp, duration, library version
  2. `environment` — python/pandas/scipy/pyproj versions, OS
  3. `inputs` — per file: path, **md5 hash**, rows, dropped rows,
     CRS in → CRS used
  4. `settings` — engine, unit_size, k_values, tie_mode, **seed** (#1),
     decay spec, friction spec (default, combine rule, coverage %)
  5. `data` — n cells, global N, per-variable min/max/sum, extent
  6. `events` — structured capture of everything currently printed:
     warnings with counts and details (dropped rows, duplicate summing,
     coverage, suppressed repeats — spec §12 list)
- **Progressive writing:** log opened at run start, events appended live,
  summary finalised at end — a crashed run still leaves a record
  (pairs with future tile-and-flush).
- **Realm relationship:** per-run metadata is immutable history; the
  realm is mutable memory holding run-ids + meta paths + last-used
  settings for defaults. The realm remembers, the metadata testifies.
- **Include the output column list** with a one-line definition per
  column, so a shared CSV+meta pair is self-documenting (decided: yes).


## Item 3 — Hexagons, design thoughts (recorded, not decided)

- **Conversion vs import:** two entry paths. (a) CONVERT: points/rasters
  are binned into a hexagon tessellation we generate (user sets the
  hexagon "diameter" analogous to unit_size; pointy-top or flat-top is
  a setting). (b) IMPORT: data already carries hexagon IDs/coordinates
  (e.g. H3 indices or axial q/r columns) and is taken as-is.
- **Coordinates:** internally use CUBE coordinates (x+y+z=0) — the
  X/Y/Z from the original spec. Neighbourhood = 6 neighbours instead
  of 8; hex distance = (|dx|+|dy|+|dz|)/2 (rounds metric); Cartesian
  distance for Dist_k output from hexagon centre points.
- **Engine impact:** the radial sort core needs only a different
  centre-point distance formula (small change). The friction/BFS
  engine needs the 6-neighbour graph instead of 8 (parameterise
  neighbourhood construction — one function swap). The ring/tie logic,
  k-thresholds, decay, statistics: all unchanged.
- **Snapping:** point -> hexagon assignment via standard axial rounding
  (cube-round algorithm). Keep original coordinates as always.
- **Candidate shortcut:** the `h3` library (Uber) handles tessellation,
  indexing and neighbours on the globe — but introduces fixed
  resolution levels rather than free diameters. Decide: own metric
  hexagons (free size, consistent with our metric grids) vs H3
  (interoperability). Leaning: own metric hexagons as default,
  H3 import as an accepted in-data format.


## Item 4 — Heights / D-dimensions, design thoughts (recorded, not decided)

- **From the original spec:** any number of added dimensions (D1, D2,
  ...) for height, time, etc. Height is the first concrete case.
- **Two fundamentally different roles for height — must be kept apart:**
  (a) height as a FRICTION SOURCE: slope between neighbouring cells
  converted to friction values (steeper = more rounds). Fits the
  existing friction engine with zero engine change — just a
  preprocessing helper (DEM raster -> slope -> friction file). Probably
  the highest-value/lowest-cost use of height data.
  (b) height as a TRUE THIRD SPATIAL DIMENSION: cells become voxels
  (X/Y/H), neighbourhood grows to 26 neighbours (or 8 + up/down),
  distance formula 3D. Relevant for multi-storey urban data (population
  per floor). Bigger change: grid domain, graph construction, ring
  table all gain a dimension — but the engines' logic is
  dimension-agnostic in principle.
- **Time as a D-dimension** is different again: usually SEPARATE runs
  per time-ID (already the D3 example in the spec), not adjacency
  across time. Do not model time as a spatial axis.
- **Data formats when it becomes real:** DEM GeoTIFF for (a) — the
  raster module already reads it; point tables with a height/floor
  column for (b).
- **No suitable test data yet** — when implementing, start with (a)
  slope-to-friction (synthetic DEM is easy to fabricate and validate
  by hand), defer (b) voxels until a real use case exists.


## Data notes (remember, nothing to act on)
- Stockholm semi-synthetic (.sav) + Kommun shapefile: coordinates are
  APPROXIMATE (discretion jitter) and the municipality polygons are
  CRUDE generalisations - neither is a perfect delimitator. The 9,033
  cells falling outside all polygons in the v0.8 Alt-2 join are the
  expected product of that pairing, not an error. Interpretation and
  any future join-tolerance option (e.g. nearest-polygon snap within
  X m) should keep this in mind.


## Item 4 expanded — three height mechanisms (opinions as requested)
**4a. DEM slope-asymmetric friction ("inverted watershed").** Downhill/
flat = 0 effort, uphill costs. VERDICT: highest research value of the
three (active mobility, X-minute-city relevance) and NOT too heavy:
requires directional EDGE weights, and the friction engine's Dijkstra
graph is already directed - cost(i->j) = 1 + g(elev_j - elev_i), same
graph size, same runtime class as v0.4 Stockholm (~1 min). Effort
function: offer BOTH (i) a transparent linear rule - one extra round
per s0 % uphill slope, s0 user-set, default suggestion 5% - and (ii)
Tobler's hiking function (speed = 6*exp(-3.5|slope+0.05|) km/h,
asymmetric, canonical, citable) converted to rounds relative to flat.
Validate on a synthetic cone hill (neighbourhoods must skew downhill).
Preprocessing helper: DEM GeoTIFF -> cell elevations -> per-edge costs
(raster module already reads DEMs).
**4b. Building levels / heights at coordinates (U-curve travel:**
down to level 0, across, up at j). d'ij = dij + h_i + h_j, with h given
either in metres (used directly) or in LEVELS x user-set
metres-per-level. Individuals in one cell at different levels need
sub-cell records (same pattern as individual decay). VERDICT:
conceptually sound - vertical travel is real distance - modest
implementation cost in the sort engine (per-destination offset changes
ordering; per-origin offset shifts reported distance and decay weight).
Data availability is the real constraint, not code.
**4c. Height as availability adjustment (may be NEGATIVE - regression
residuals, subway proximity, line of sight).** Same formula as 4b.
VERDICT: implement 4b+4c as ONE mechanism ("node distance offsets",
metres, negatives allowed, optional floor-at-zero), documented twice.
Honest caveats to state loudly: (i) with decay, a negative offset gives
weights > 1 - amplification - which must be an intentional modelling
choice, not a surprise; (ii) outputs must be labelled ADJUSTED distance
to protect the Dist_k semantics. Academic-niche value acknowledged, but
the marginal cost on top of 4b is near zero, so include it.
Priority: 4a first (needs the DEM the user is sourcing), 4b/4c as one
small batch after.



## v1.2.0 updates (this session)
- ~~#4a DEM slope-asymmetric directional friction~~ DONE in v1.2.0
  (tobler + linear via SLOPE_MODELS; Malta-validated; "valley tax"
  asymmetry finding recorded). Square grids only - hexagonal slope
  rides on the parked hex-friction 6-neighbour graph.
- #11 substrate progress: `origins=` subset option now exists on both
  graph engines (friction + slope). Still needed for #11: reach modes,
  match-table segmentation, chaining orchestrator. #12 still BEFORE #11.
- #4b + #4c (node distance offsets) remain parked, unchanged verdicts.
- NEW small idea (parked): windowed DEM reading in dem_to_cell_altitude
  for national-scale rasters (Malta-size reads whole array fine).
- NEW small idea (parked): slope-model parameter sweep helper
  (lambda_up sensitivity reporting) once #12's neighbourhood menu lands.



## Session additions (post-v1.2.0, recorded without coding)

- **#12 EXPANDED - neighbourhood definition menu, now with parity
  checklist.** Goal restated: everything available for k must exist
  for metric radius r (and where meaningful, friction tau). Checklist
  to tick at build time: fast engine (KD-tree ball query) | ring
  engine (stopping rule swap) | stats engine (all three exactness
  tiers) | decay (r-bounded and the unbounded decayed sum) | friction
  + slope (tau_values = effort isochrones) | segregation profile over
  r | area aggregation | maps | RunLog column definitions | Stata
  bridge (r() option) | hex. Decisions to record when building:
  naming scheme (proposal: N_r500 style), empty-radius convention
  (N=0 is a valid partial result, never nothing), tau semantics under
  real-valued slope effort. Note: ties VANISH under r (cells within r
  included wholly) - document as a simplification, not a change.
  STILL BEFORE #11. Recommended as next build.

- **#13 (NEW) Cookbook: 10-20 complete A-to-Z scenario scripts.**
  Runnable scripts in examples/cookbook/ against small bundled
  fixtures + a COOKBOOK.md index; CI smoke-runs them so documentation
  cannot rot. Candidate scenarios: (1) CSV -> decay analysis -> map;
  (2) SPSS register -> segregation profile -> area aggregation;
  (3) WorldPop rasters -> elderly context; (4) OSM pbf -> POI
  accessibility; (5) wrong-CRS shapefile rescue; (6) friction with
  water barriers; (7) DEM slopes -> valley-tax map; (8) grid vs hex
  MAUP experiment; (9) individual data with missings -> stats engine;
  (10) weighted/aggregated in-data; (11) the Stata round trip;
  (12) RunLog-driven reproduction; (13) national-scale tactics;
  (14+) radius variants of 1/3/7 - BLOCKED ON #12. Grows with the
  package; partial delivery acceptable.

- **#14 (NEW) Spatial autocorrelation module: Moran's I and
  Getis-Ord, global + local, multiscalar.** Weights matrices born
  from our own engines: binary kNN, distance band (needs #12),
  decay-weighted via the five half-life models, friction/slope
  effort-weighted (novel). Profile-across-k pattern alongside
  seg_profile. Components: W builder, global I and G, local LISA and
  Gi/Gi*, permutation inference (conditional permutation for local -
  a real computational piece, plan chunked/seeded). Mandatory loud
  warning in docs + RunLog: autocorrelation of R_k columns measures
  an already-smoothed surface (overlapping neighbourhoods induce
  correlation by construction) - legitimate but must be understood.
  Validation: known answers cross-checked against PySAL esda on
  fixtures. SEQUENCE AFTER #12 (weights builder should speak the full
  neighbourhood menu from birth).



## Session additions (round 2, recorded without coding - NEXT ROUND items)

- **#4a-RT (NEXT ROUND) Round-trip slope effort.** `roundtrip=True` on
  run_knn_slope: two Dijkstra passes per origin (graph + transpose =
  cheapest return path, which may differ from outbound - correct),
  summed, reported as PER-LEG AVERAGE (sum/2) so flat DEM regresses
  exactly to one-way values (regression test extends). No new cost
  models needed: convexity gives p(s)+p(-s) >= 2p(0) for both tobler
  (2.031 at +-5%, 2.419 at +-10%, 3.433 at +-20%) and linear
  (2+(lu+ld)|s|) - varied terrain automatically costs more round-trip,
  the requested physics. Cost 2x runtime. k stays raw-count-defined.

- **decay: gamma-parameterised shifted power (NEXT ROUND).** Audit
  verdict on current power model: half-life is EXACT via the +1m
  shift (w(d)=(d+1)^b, b=ln.5/ln(h+1)) BUT the shift is a hidden
  1-metre reference scale forcing an ultra-heavy tail (h=1000 =>
  exponent -0.10; w(10h)=0.40, w(100km)=0.32). Fix: add
  w(d) = (1 + (2^(1/g)-1) d/h)^(-g) - exact half-life at h for ANY
  tail exponent g (verified g=0.5,1,2,5); g=1 is w=1/(1+d/h).
  Keep current model reproducible as legacy special case. Document
  the tail table (negexp vs power) in the manual.

- **#15 (NEW) Access potential & the opportunity horizon.**
  Theory recorded: uniform POI density + negexp gives marginal access
  a(r) = 2*pi*rho * r*exp(-|b|r) - a Gamma(2) density (chi^2, 4 df,
  up to scale; the user's conjecture confirmed exactly); peak at
  r* = 1/|b| = h/ln2 ~= 1.4427h ("the opportunity horizon");
  cumulative A(R) = (2 pi rho/b^2)[1-(1+|b|R)exp(-|b|R)].
  Components: (a) access_potential surface (Hansen 1959 potential
  accessibility - claim the classical name) from ALL grid/hex
  midpoints incl. unpopulated (zero-mass origin rows on origins=
  machinery); (b) POI-placement surplus surface = REVERSE potential
  sum_i pop_i * w(d(i,x)) - ONE kernel pass, on regular grids a
  convolution => FFT whole-surface in O(n log n), NO ITERATIONS
  (iterations only for competition effects - 2SFCA crowding /
  doubly-constrained - which is #11 territory, optional); (c) greedy
  sequential placement is submodular => lazy-greedy with (1-1/e)
  near-optimality guarantee, no combinatorial search; (d) later:
  friction/slope effort replaces Euclidean d (geometry term becomes
  empirical ring mass), per-individual decay components.
  Related models to keep in view: Huff choice, Reilly breaking-point,
  Wilson entropy family, p-median/MCLP consuming our surfaces.
  Natural sequence: after #12 (needs the neighbourhood menu's
  unbounded decayed-sum mode as substrate).



## v1.3.0 updates (this session)
- ~~#12 Neighbourhood definition menu~~ DONE in v1.3.0, INCLUDING the
  area family (k / r / tau / unbounded decayed sum / AREA - the
  teaching triad k-r-area is now complete in one package). Parity
  checklist ticked except: ring-engine r (redundant - documented
  mathematical equivalence with the stats engine); hex needs no
  change (same engines). Stata: r() live in bridge (pytest) + ado
  (in-Stata untested until next user run).
- NEW parked: weighted quantiles/Gini for area_stats value statistics
  (weights currently apply to N and binary T/R only - loud note in
  docstring).
- NEW parked: r/tau variants in the ring engine IF a decay-at-radius
  use case appears (decayed sums already live in the fast engine).
- Unblocked by this release: #13 cookbook radius scenarios, #14
  weights matrices (kNN + distance-band + decay all available), #15
  (unbounded decayed sum = the access_potential substrate), #11.



## v1.4.0 updates (this session)
- ~~#4a-RT round-trip slopes~~ DONE (per-leg average; flat==one-way
  exact; known-answer + symmetry + convexity pytest).
- ~~decay: gamma-parameterised shifted power~~ DONE (exact half-life
  any gamma; legacy kept; horizon analytic, INFINITE for gamma<=1).
- ~~#15 access potential & opportunity horizon~~ DONE (FFT
  potential_surface exact-on-grid, surplus = reverse potential,
  effort_potential incl. round-trip; Malta: full-island surfaces in
  1.4 s, optimal next-POI at Birkirkara-Msida, terrain access tax
  2.6% mean / 15.9% max, frontier-vs-core finding, coming-home
  penalty p95 6.9%). PARKED from #15: greedy sequential placement
  helper (submodular, 1-1/e); Huff/Reilly/Wilson/p-median remain
  a recorded modelling menu; competition = #11.
- Next natural: #11 kFCA (all substrates now exist) or #14
  autocorrelation; #13 cookbook grows alongside.



## v1.5.0 updates (this session)
- ~~gamma-figure~~ DONE (examples/cookbook_01_gamma_decay.py - #13
  entry 01; negexp dashed reference as endorsed; horizons drawn:
  g=2 -> 4.83 km, g=4 -> 3.52 km, negexp 2.89, g<=1 infinite).
- ~~#11 kFCA/ELMO-3SFCA (module)~~ DONE: reach modes decay/r/k/effort
  (round-trip capable), 2SFCA + 3SFCA, doubly-constrained balancing
  (margin scaling for imbalanced markets + GAUGE FIXING of factor
  scale - both loud, both tested), match-table orchestrator.
  **REAL-DATA ACT PENDING RE-UPLOAD** of People.sav + LowEduJobs.sav
  (uploads failed to reach the container this round); the joint-
  isometry anonymiser is ready and self-checked, so headline run +
  shareable fixture are one command after re-upload.
- NOTE: mystery *_synthetic.sav files found in session outputs were
  REJECTED (jobs coordinates spanned 900 km for one municipality -
  geometry not trustworthy); nothing was built on them.
- NEW parked: kFCA reach where k counts OWN-side mass (competition
  catchments) as an alternative convention - decide with real data.
- NEW parked: FCA congestion maps + Stata bridge exposure of fca().



## v1.5.1 updates (real-data act)
- #11 REAL-DATA ACT DONE: municipality labour market run (2SFCA/3SFCA/
  kFCA/balanced), education-gap map, congestion map; fixture +
  checkpoint regression in suite (isometry-proven identical);
  synthetic .sav pair delivered for sharing (full files, jobs
  Sweden-wide as in the original).
- User's "simple solution" steps 1-4 confirmed == method="2sfca"
  (the default); J column added so step 1 is a first-class output.
- NEW parked: per-cell effective-pressure output (J/A) as a named
  column; commuting half-life estimation from observed flows (would
  need a flows file); kFCA own-side-mass convention decision.



## v1.6.0 updates (this session)
- ~~#17 generic Stata dispatcher~~ DONE (dispatch() + equipop_run.ado,
  five engines, fca-first as planned; sfi-stub verbatim-validated;
  in-Stata maiden run = user-side action). FUNCTION_MATRIX.md now in
  repo docs/ (SB row spans FC/ST/FR/SL/FA). GitHub-fetch workflow
  PROVEN this session (clone of tag v1.5.1, 38/38 before build).

- **#18 (NEW, designed) CONTINENTAL SCALE - very large data
  (user: 16M coordinates run in old EquiPop; Europe-wide 100 m
  grids; memory is the constraint, not time).** Arithmetic: Europe
  bbox ~5000x4500 km at 100 m = ~2.25 BILLION domain cells - engines
  must NEVER materialize domain-sized arrays; populated cells from
  16M coords (~10M unique) fit RAM comfortably (KD-tree ~GBs).
  Architecture per engine:
  (a) fastcounts: chunked KD-tree already streams; add TILE-AND-FLUSH
      (absorbs the parked item): process origin tiles, write parquet
      per tile, float32 outputs, uint32 counts; k-NN has NO a-priori
      radius bound -> per-tile halo from local density estimate with
      the EXISTING straggler re-query as exactness guarantee (seams
      exact by construction, not by hope).
  (b) graph engines: restrict domain to inhabited + corridor cells
      (sparse node set), or tile Dijkstra with halo = tau_max *
      max-edge-cost bound; hex same when hex-friction lands.
  (c) FFT potential: tiled overlap-add with kernel-radius halo -
      mathematically EXACT, memory = tile + halo only.
  (d) fca: supply-side tiling with decay-truncation halos.
  (e) I/O: memory-mapped/parquet chunks in, progressive RunLog with
      per-tile md5 manifest + resumable rerun() (absorbs the parked
      rerun()-from-meta idea), float32 by default at this scale.
  Priority order: (a) first - matches the user's 16M k-NN use case;
  validation: tiled run == untiled run EXACTLY on a mid-size fixture.



## v1.7.0 updates (this session)
- ~~#18a tile-and-flush (fast engine)~~ DONE: origins= on fastcounts,
  bigrun module (parquet tiles, manifest+md5, resume), golden
  tiled==untiled test, 250k-origin/1.5GB demo, ~2h extrapolation for
  the 16M use case. Absorbs the old parked tile-and-flush item.
- #18b-e remain parked until data demands them: graph-engine corridor
  subgraphs / halo Dijkstra; overlap-add FFT tiling; fca supply
  tiling; mmap/parquet ingestion; true domain tiling with
  density-estimated halos (>100M cells).
- Board next: #16 propensity FCA (2x2 runnable on delivered data) or
  #14 autocorrelation; user-side: tag v1.6.0 + this v1.7.0 release.



## v1.8.0 progress (Book session 1)
- #19 underway: Gridby generator (planted truths PYTEST-ENFORCED:
  gradient recovered, river isochrone bites, hill peak exact, jobs
  cluster share), equipop.datasets loader (gridby/municipality/
  berlin/stata_test), chapters 1+2+4 written in docs/book/ with two
  cookbook figure scripts (02, 03), compile pipeline + first .docx
  sample this session. Next book bites: ch 13+16 (Stata Journal
  feeders), then Part II.



## v1.8.1 (CI fix round)
- Root cause of the reported pytest/GitHub errors FOUND AND
  REPRODUCED without needing the logs: test extras lacked pyarrow
  (bigrun parquet) - failed on every clean env; also rasterio absent
  meant the DEM test never actually ran on CI. Fixed (extras +
  importorskip + helpful bigrun error). Verified three ways: bare
  env 44+3skip, +pyarrow 46+1skip, full 47/47.
- WATCH: rasterio/NumPy2.5 DeprecationWarning (upstream, cosmetic).
- REMINDER: GitHub main is STILL at 1.6.0 - pushes for 1.7.0/1.8.x
  have not left the local machine; the 1.8.1 zip supersedes all -
  ONE swap-commit-push-tag carries everything, CI should then show
  47 green x 2 Pythons.



## v1.9.0 updates (this session)
- ~~#14 spatial autocorrelation~~ DONE (weights from the menu, I/LISA/
  Gi* esda-cross-validated, multiscalar profile, loud smoothed-surface
  warning, Gridby ch.11 figure). NEW small parked: dispatcher engine
  "lisa" (row-aligned Ii/quad/p to Stata - Stata Journal candidate);
  hex weights (6-neighbour) when hex-friction lands; permutation
  chunking for national-scale LISA (#18 family).
- Board next: #16 propensity FCA, Book chapters 13+16, or #7 QGIS.



## v1.9.1 (Book-per-release round)
- CONVENTION ADOPTED: every release = zip + manual + backlog + BOOK
  (compiled docx, version-stamped). Locally: docs/book/build.sh. On
  CI: the new "book" job uploads EquiPop_Book.docx as an artifact on
  every push (find it: Actions -> run -> Artifacts, bottom of page).
- Chapter 11 written (4 chapters compiled of 20; ~9 pages - Part II
  will thicken the volume). Next bites: ch 13 + 16.



## v1.10.0 updates (#16 round)
- ~~#16 propensity match-table FCA~~ DONE (group + cell modes,
  estimators (c)+(f) as user chose; identity regression free; ch13 +
  cookbook_05 on the register fixture; Book compiled).
- kFCA continuation UPDATED per user: parametrize k_side AND return
  BOTH sides side-by-side (A_kjobs, A_kworkers) - "having them both
  could be interesting in analyses". Queued with the divergence-map
  experiment.
- AWAITING USER: estimated M from their regressions (area effects
  stripped, per ch13) -> rerun the municipality act as RESEARCH, not
  scenario; candidate Stata Journal exhibit.



## v1.11.0 (Voice + lisa round)
- Book style guide EXECUTED on ch01/02/04/11/13; ch16 born in the
  register; sample-approved voice now the volume's voice.
- ~~lisa dispatcher engine~~ DONE (Stata Journal exhibit ready:
  equipop_run, engine(lisa) x() y() values(R_HighEdu_400) -> LISA
  variables for spmap/regress).
- Writing/coding split adopted: next WRITING session = Part II
  chapters (5-7); next CODING session = kFCA k_side both-sides +
  divergence experiment (awaits nothing) or RunLog audit.



## v1.12.0 updates (kFCA both-sides round)
- ~~kFCA continuation~~ DONE (k_side incl. "both"; A_ksupply/A_kdemand
  per user naming; divergence experiment: corr 0.329 on the
  municipality - conventions measure different geographies).
- Small parked: expose k_side in dispatcher/ado fca engine.
- ch5-7 pack merged into repo; Book at 9 chapters.


## GIS & stats-software bridges (feasibility discussion, FOR LATER)
- #7a QGIS Processing provider: HIGH feasibility, first target.
  QGIS runs Python; pip-install equipop into its interpreter, wrap
  engines as Processing algorithms -> appears in the Toolbox, chains
  with all QGIS tools. #7b full Plugin (GUI dialogs, plugin
  repository distribution) builds on 7a.
- #21 ArcGIS Pro Python toolbox (.pyt): HIGH technical feasibility -
  Pro is conda-based Python; a thin .pyt wraps the same engines
  (glue-only, all math stays in the tested package). Constraint:
  arcpy cannot run in CI (licence) -> validate the glue via a stub,
  exactly the Stata discipline.
- #22 SPSS: MEDIUM. Path A: SPSS Statistics Python integration /
  extension command mirroring equipop_run. Path B (zero-maintenance,
  available TODAY): documented .sav round trip - read .sav, compute,
  write .sav back (pyreadstat already in the io extras); a Book
  appendix recipe rather than code.
- R: an R version predates EquiPop; a thin reticulate wrapper would
  expose the Python package natively in R - LOW effort, note kept.
- Shared principle for ALL bridges (the Stata lesson): hosts get
  GLUE ONLY; mathematics lives in the pip package where pytest
  guards it; every glue layer gets a stub validation.



## v1.13.0 updates (#21 ArcGIS opener)
- ~~#21 first release~~ DONE: 3 tools (user's priorities 1+2 first-
  class, friction included as the ready door), stub-validated glue,
  guide. MAIDEN RUN user-side: add .pyt in Pro, Tool 1 on any point
  layer. Future #21b: LISA + FCA tools (after maiden feedback),
  symbology presets, tool 3 accepting a polyline barrier layer
  (auto-rasterize rivers/roads to friction cells - natural next).
- Decay now flows through the counts ROW path everywhere (Stata ado
  inherits it free via dispatch - expose halflife() option: small).



## v1.14.0 (#21b - the field-tested toolbox)
- ~~#21b~~ DONE, all spec items incl. category mode + categorical
  package factory. John's two observations resolved: Dist_k =
  floating radius (now self-explaining), T>N = counts-without-
  population (now auto-hinted + honest labels).
- REMAINING #21 family: Stata catvar()/treatvalues() options (the
  factory is waiting), per-parameter metadata XML sidecars (polish),
  LISA + FCA tools (#21c), polyline-barrier auto-rasterizer.
- Book at 14 chapters, riding this release.



## v1.14.1 (hotfix - the counts-convention bug, found by John on the

## real register through ArcGIS; shapefile name truncation decoded in

## chat -> reinforce gdb / New-feature-class-to-gdb advice)


## STATA-UX SPEC (feedback from Umut - next Stata session)
- i) NATURAL INSTALL, two stages: (a) NOW: `net install equipop,
  from(https://raw.githubusercontent.com/GeoJohnSwe/EquiPop/main/stata/)`
  - needs stata.toc + equipop.pkg files in stata/ (small, buildable
  immediately); ado then CHECKS for the python package and prints
  the pip line if absent. (b) LATER: SSC submission (bundle ados +
  sthlp help files + ancillaries, email to SSC maintainer) ->
  `ssc install equipop` for the world.
- ii) `help equipop` -> write SMCL help files: equipop.sthlp
  (overview + engines table), equipop_run.sthlp, equipop_knn.sthlp
  (syntax, options, examples with expected output, the two treat
  conventions EXPLAINED).
- iii) VARIABLE LABELS on every generated variable (via `label
  variable` after store): e.g. R_HighEdu_400 -> "EquiPop: share
  HighEdu among 400 nearest"; plus a prefix() option (e.g.
  prefix(eq_)) so new variables sort together and cannot collide
  with old ones; the completion message already lists them.



## v1.15.0 (#21c delivered)
- ~~#21c items 1-3~~ DONE per confirmed spec. Deferred honestly:
  stats-over-effort engine (machine 2 ingredients await it);
  decay-over-effort; one-click Pro wrapper for features_to_friction
  (needs geopandas in the Pro clone - document or wrap);
  negative-friction/speedups discussion.
- Next candidates: the 1.17 dialog + theory round (items 30-36:
  value tables, persons/places, collapsible sections, variable
  bandwidth and individual tau), then the shared-core refactor and
  the QGIS door (39). Stata-UX round (Umut, on his return), #21d
  LISA/FCA tools, writing ch14+15+17.


## v1.18.0 (the shared core - BACKLOG 39, part 1 of 3)
- ~~39, part 1~~ DONE. `equipop/doors/` now holds what every door was
  rebuilding: `help.py` (the text beside every box, keyed by
  parameter name), `report.py` (Channel + Reporter + stage: the
  package's printed voice into arcpy messages / QGIS feedback /
  console / silence), `fields.py` (predicted result names, 10-char
  shortening, the refusal - with the roomy container as an argument
  so QGIS says GeoPackage where Pro says file geodatabase),
  `loader.py` (PointInput, the coordinate rules, the projection
  hint, and DoorError). ArcGIS re-pointed with behaviour unchanged;
  114 existing tests green untouched + 40 new door-blind ones.
- Contract check added: each door declares `_CONTRACT`, the package
  refuses a mismatch by name and says which half to replace. Also
  closes an old rough edge - a missing package used to give a bare
  ModuleNotFoundError mid-run; it now gives the pip line.
- REMAINING in 39: (2) the QGIS Processing plugin against a
  simulated PyQGIS, the way fake arcpy works - the shared core is
  the half of this that is now done, and `Channel.from_qgis` and
  `refuse_short_target(container=...)` exist ready for it; (3)
  Gridby's answer key through both doors as the conformance suite.
  Then R (reticulate) and SPSS.

### Found while doing it (not acted on)

## v1.18.1 (one-line fix, found from John's upgrade routine)
- The toolbox told the wrong story for the LIKELY half of version
  skew. John upgrades the package with pip and replaces the toolbox
  files by hand - two steps, easily done in the wrong order or in
  the wrong Pro environment. With a new toolbox and an old package,
  `import equipop.doors` fails and 1.18.0 said "the EquiPop Python
  package is not installed", sending the user to look for a package
  sitting right there. It now tells the two cases apart: missing
  entirely -> install; present but older -> names the version found
  and says `pip install --upgrade equipop`. Test added and verified
  to fail against the old message. 155 tests.

### Found while ruling on the conformance reference (for 1.19.0)

## v1.19.0 (the teaching data ships; the doors get an answer key)
- ~~47~~ DONE. Gridby's generator moved into the package
  (equipop/gridby.py, shim left in examples/); the Book's other
  dataset moved to equipop/data/ and is declared in pyproject, so
  the wheel carries it. Verified from a clean venv: gridby and
  municipality load, berlin names openpyxl as the missing reader,
  stata_test refuses by saying where to get it. tests/test_packaging
  .py added - it checks the SHAPE of what ships, which is the only
  way to catch a bug that cannot fail inside the repo.
- ~~48~~ DONE. equipop/doors/reference.py + equipop/data/
  gridby_reference.csv (2360 x 14, both engines and the radius
  path). compare() judges any door: counts exact, continuous within
  tolerance, rows matched on coordinates. explain() turns the report
  into sentences for a door's message pane.
- NEXT: the QGIS Processing plugin (BACKLOG 39 part 2). It now has
  both halves of its foundation - the shared core to build on, and
  the reference to be judged by from its first day.

## v1.20.0 (the QGIS door)
- ~~39 part 2~~ DONE. qgis/equipop_qgis/ - provider, plugin scaffold,
  and two algorithms (Counts and Shares, Value Statistics) built on
  equipop.doors. tests/qgis_stub.py simulates PyQGIS the way fake
  arcpy simulates arcpy. 14 door tests + the conformance pair.
- ~~39 part 3~~ DONE in effect: BOTH doors now pass the Gridby
  reference, 2360 rows, every column. That was the definition of a
  finished door and it is now a test in each suite.
- FIXED: the 1.19.0 reference named its treatment 'minority' while
  every door names treatments by FIELD - so no door could ever have
  matched it. Caught only by building the second door, which is
  itself the argument for building the second door.
- qgis/README_QGIS.md - the one-page install note (equipop must
  reach QGIS's own Python; OSGeo4W shell or the QGIS Python Console,
  where sys.executable cannot be the wrong interpreter).

### Open, in priority order (John's arrangement, 1.19 session)

## v1.21.0 (Malta: three GeoPackage findings + the remainder box)
- ~~46 (Malta a)~~ category dropdown: read through the layer OBJECT,
  not a path; report success and failure out loud.
- ~~(Malta b)~~ ExtendTable unsupported on GeoPackage -> _add_columns
  falls back to AddField + UpdateCursor and explains the trade.
- ~~(Malta c)~~ CopyFeatures renames the identifier (fid ->
  OBJECTID); the values now travel with the copy.
- tests/test_geopackage.py + a GeoPackage-shaped simulator fixture
  (oid_names, no_extend, a dataSource that refuses to reopen). All
  three field failures reproduce here first, then pass.
- ~~51~~ the remainder box, in the engine so both doors share it.
- Missing-data rules written down for BOTH machines (John's ruling):
  group counts -> zero; continuous values -> excluded, Nv reports.
- QGIS: category table + remainder + decay. Fixed: the QGIS reader
  forced text columns to NaN.

## v1.21.1 (the Groups section, made legible)
- Placement bug from 1.21.0: restgroup/restinpop had no SECTION, so
  Pro floated them to the top of the dialog, above the field they
  depend on. One missing line in the SECTION map; found in the field
  within a day, which is the argument for shipping small.
- Groups split into three headings; the unused route greys out; the
  remainder box waits for a category field. Population field stays
  live in both, since it applies to both.
- Labels: the remainder box asks for a group NAME with an example.
- QGIS: same clarity by ordering and wording (no sections there).

## v1.22.0 (two populations)
- The dialog reorganised around REFERENCE and TREATMENT populations,
  matching the words the T_ and R_ columns have always used.
- cattable (value/group/in-population) split into reftable (which
  values are around) and treattable (which values form which group).
  An EMPTY reference table means everything - the fastfood-per-POI
  vs fastfood-per-eating-place distinction, with no tick.
- treatvalue: the treatment population's own value field. Empty =
  the reference's field (same units, R_ is a share). Different =
  a ratio, warned about plainly.
- groupscount RETIRED: the value fields carry that meaning now.
  Places-over-persons is no longer reachable (it was the 1.17 bug).
- categories_to_binary gained rest_in_population=None, meaning "the
  population is decided elsewhere" - needed once a separate
  reference table exists.
- Warnings appear beside their fix AND at top level, since Pro hides
  a warning inside a collapsed section (John, field).

## v1.22.1 (the one-line root of the Malta round)
- _ref() now resolves through arcpy.Describe(value).catalogPath, for
  names as well as objects. catalogPath is not an attribute of a
  Layer - it belongs to its Describe - so the branch that was meant
  to produce a workable path never ran, and everything fell through
  to dataSource, which a GeoPackage reports as an unusable
  connection string.
- One line behind three field failures. The write, the dropdown and
  (latently) the barriers all used the same helper.
- The simulator models it: the layer is refused, the catalog path is
  accepted, and a catalog path resolves back to its layer.

## v1.22.2 (rows outside the reference; the GeoPackage verdict)
- keep_outside (default TRUE, John's ruling): a row outside the
  reference population counts as ZERO people - nobody's neighbour -
  but still gets its own results. Was: dropped, Null. Both doors.
  A test asserts keeping them does not move the numbers of the rows
  already inside, which is what "counts as zero" has to mean.
- 52 CLOSED as a HOST limitation, evidenced not inferred: Pro does
  not show new fields on a GeoPackage layer in a map; Add Field is
  greyed out with "the table or its schema is read only" on a clean
  project. Esri community enhancement request open, reported from
  Pro 3.0.2 through 3.5.2, and the same files behave normally in
  QGIS. The dialog now warns at DIALOG time and points at Output =
  New feature class.

## v1.23.0 (the ladder made visible)
- refmode / treatmode: three rungs each, simplest first, with the
  boxes a rung does not need greyed out. John's design, agreed by
  sketching the structure back and forth before any code.
- treatvalue RETIRED (reverses 1.22.0): k is confined to the
  reference population, so the treatment shares its units. Every R_
  is a share by construction.
- treatcatfield added: the treatment names its own type column, so
  its section reads on its own.
- keepoutside is a two-way choice, not a tick (John: "should be an
  active choice").
- Help now states totals-vs-averages: machine 1 SUMS its group
  columns; per-point averages belong in machine 2, which weights by
  the reference population. Verified empirically: two locations, 10
  people at 100 and 1 person at 1000, give the weighted 181.82 and
  not the unweighted 550, with Nv reporting 11 persons not 2 rows.

## v1.24.0 (four write-path bugs from one evening in the field)
- outfc/outtable declared direction="Output". Every parameter was an
  INPUT, so Pro's browse dialog would not create a new feature class
  ("Cannot access anyfile"). Present since the toolbox was written.
  The simulator checked names, types and sections but never
  DIRECTION - now it does, and the check was verified to fail when
  the bug is put back.
- _write_failure(): one diagnosis for locks / unsupported formats /
  refusals, keeping the ORIGINAL arcpy error in the message. The add
  path also retries, as the update path has since 1.17.
- Cloud-synced folders (OneDrive, Dropbox, SharePoint...) named on
  input and output, in both doors. Esri documents this as
  unsupported and the symptoms match exactly.
- Dialog-time checks: missing output path, synced folder, shapefile
  in an open map.

## v1.25.0 (QGIS layout; a parity gap)
- FOUND: 1.23.0's QGIS edit half-applied - refmode never reached the
  QGIS door, so the reference ladder existed only in Pro. The parity
  test checked QGIS names are a SUBSET of Pro's, which a missing box
  satisfies. Now checked both ways against a named CORE set.
- QGIS layout, within what Processing allows: Advanced area for the
  rarely-touched boxes, numbered labels (1 / 1a / 2 / 2b / 3 / 4),
  ladder order, tooltips from the shared help.
- qgisMinimumVersion 3.16 -> 3.28, with "tested on 3.42" stated.
- [stata] full population now names the total.

## v1.26.0 (barriers and terrain in QGIS)
- qgis/equipop_qgis/barriers.py: vector barriers (points, lines,
  polygons, multipart), friction rasters, elevation for slope, tau
  budgets, round-trip, overlap rule. Reprojected to the working CRS.
- The engine wants features as {"type": ..., "parts": ...} - line
  charged by LENGTH, polygon by AREA - and friction means a
  DIFFERENT ENGINE (friction/slope), not an extra argument. Both
  found by test, not by reading.
- Parity test corrected: it now asserts every box in either door has
  an entry in the shared help, rather than requiring identical
  widget names. Pro's barrier VALUE TABLE and QGIS's layer+field are
  the same idea in two hosts.

## v1.26.1 (Malta's barrier day)
- The barrier was reprojected against the layer's ARRIVAL CRS, not
  the WORKING CRS of the run. Degrees vs degrees -> no transform ->
  40,678 roads in one 100 m cell. base.py now remembers the working
  CRS and the barrier path uses it.
- check_plausible(): refuses a friction surface that cannot be
  right (mass collapse into few cells; no overlap with the points),
  naming the likely cause. THE lesson of the round - the CRS bug was
  one instance of a class, and only the guard catches the class.
- The effort engine emitted T_/R_ with no treatment given. Fixed in
  friction.py and the merge in stata_bridge.py; the counts engine
  was already right.

## v1.27.0 (facilitators)
- Costs may now go below zero, down to but not including -1.
  _check_cost_range() names the floor and what the values mean.
- THE reason it could not have been a quiet change: FrictionGrid
  held np.int64, so -0.9 became 0. Now float. Barriers were immune
  to this because whole numbers survive truncation - a good example
  of a bug that only a new feature could reveal.
- Refusals that read: a line layer as INPUT; a barrier smaller than
  one cell, checked BEFORE the engine's value validation.
- check_versions(): plugin and package versions compared, since the
  contract number only moves on structural change.

## v1.28.0 (the invented decay models; the Book's friction chapter)
- equipop/doors/decaynames.py: the decay list is BUILT from
  equipop.decay.MODELS, with a plain-words gloss per model and a
  parser back to the engine's name. Both doors use it. A test
  asserts every offered label maps to a real model.
- QGIS had offered "gauss" and "linear" - neither exists. The
  Gaussian is expnormal and was missing from the list that invented
  them.
- curve_in_plain_numbers(): the curve printed from the engine's own
  weight function, not an assumed shape.
- BOOK ch09: "What the number actually means" (friction as a delay
  in rounds; the table from 3 down to -1; barriers and facilitators
  as one dial) and "What happens to Dist_k when effort is on"
  (the neighbourhood is gathered by effort, so membership changes;
  Dist_k is not a radius; the two-run comparison). Pitfalls gained
  the facilitator cautions: a motorway facilitates a driver and
  bars a pedestrian, and a dial applied uniformly has no contrast
  left to measure.

## v1.29.0 (machine 2 learns the words; the parity gap nobody had looked at)

- MACHINE 2 VOCABULARY (56, and its four re-adds 60/64/69/75). Value
  Statistics said "Full population field" and "Numeric value fields";
  machine 1 has said REFERENCE population / TREATMENT population since
  1.22.0. The boxes now read "Reference population: count field - how
  many each row stands for" and "Treatment values", and the section
  headings match machine 1's.
- THE GAP FOUND ON THE WAY. Pro called that box `fullpop`; QGIS has
  called it `pop` since 1.20.0. The shared help carried BOTH, with
  different words - one box explained twice, differently, which is
  precisely what the parity test's docstring forbids. It survived nine
  releases because the both-ways check of 1.25.0 was written for
  MACHINE 1 and machine 2 was only ever asked whether each box had
  *some* help text. That passes when the doors disagree about names.
- THE FIX THAT OUTLIVES IT: tests/door_parity.py. The shared box list
  moved out of the QGIS test, where it could only describe QGIS, and
  is now checked against BOTH doors and BOTH machines. Proved to fail:
  restoring `fullpop` gives "Pro's Value Statistics is missing ['pop']".
- BY-NAME READING (groundwork for 76). Machine 2 read its sixteen
  boxes by POSITION. The deferred ladder inserts boxes in the middle,
  shifting every index after it - and a shifted index does not raise,
  it reads the neighbouring box and succeeds. All three methods now
  address boxes by name, as machine 1 has since 1.16.6. Proved to
  fail: one line reverted plus a spare box gives 8 result columns
  instead of 10. The FIRST version of that guard passed against the
  broken code, because the simulated arcpy keeps one table across
  runs and a run that did nothing still showed the previous columns;
  each run now gets a fresh simulator. Worth remembering as the shape
  of a useless test.
- FACILITATORS IN THE WORDS (71/74). Shipped in 1.27, never mentioned
  in the help either door shows. Now stated where both read it, with
  the delay rule that makes the sign make sense.
- NEUTRAL VOCABULARY (John's ruling): a point may stand for people,
  jobs, dwellings or services, so the shared `pop` entry no longer
  says "persons". The other fifteen occurrences are item 77 and were
  deliberately left for a pass John can see before it lands.
- THIS FILE, at last, in the order agreed in the 1.19 session.
- The LADDER was deferred by John and is item 76.
- 264 tests (259 + 5). Nothing run in Pro or QGIS.

## v1.29.1 (a field morning: the door would not open, and the guards were unreachable)

- THE LOAD-TIME CRASH (now item 78). Plugin 1.29.0 on package 1.27.0;
  `equipop.doors.decaynames` arrived in 1.28.0. The plugin imports it
  at module level, so it died before QGIS could show anything - and
  `check_versions()`, which is written to say precisely "your two
  halves are different releases", lives inside processAlgorithm and
  never ran. GUARD DOWNSTREAM OF ITS OWN FAILURE. The fix is queued
  as 78, not done here: it is structural and deserves its own round.
- `isAdvanced()` DOES NOT EXIST IN PyQGIS. base.py wrote the Advanced
  flag correctly and read it back with an invented method. Fixed to
  `bool(p.flags() & FlagAdvanced)`, the way add() writes it.
- AND THE STUB HAD INVENTED IT. tests/qgis_stub.py defined
  isAdvanced(), so 259 tests passed over a line that cannot run in
  QGIS. Removing it fails three tests at base.py:114 - proved, not
  assumed. The three tests now read the flag. A stub is safe only
  where it is STRICTER than the real thing.
- tools/stub_audit.py SHIPS. It checks every method and constant the
  plugin relies on against a LIVE QGIS, because the simulator cannot
  audit itself. John ran it on 3.42.1: 63 checked, no gaps. It also
  caught FlagAdvanced = 1 in the stub where QGIS says 2 (harmless,
  corrected). Its first version cried wolf on the stub's own private
  attributes - fixed, and a reminder that a noisy guard trains you to
  skim, which is how isAdvanced got through.
- THE TOOLTIP THAT MISLED. "Put it in a file geodatabase" shown to a
  QGIS user, beside QGIS refusing a name with no extension: John read
  it as "you must save into a database first", which is exactly what
  the words said. FOUR shared texts carried one door's dialect (the
  audit found no others in 50 entries). help.py now carries TOKENS -
  {target}, {container}, {formatnote} - filled per door, as fields.py
  has done since 1.18.0. One text per box, still true in both.
  make_help_xml.py read the dicts RAW and would have printed the
  tokens into Pro's help; it renders them now.
- THE VERSION STRING CLAUDE MISSED. 1.29.0 bumped three and left
  qgis/equipop_qgis/__init__.py at 1.28.0, so check_versions warned
  about a mismatch that did not exist - on the morning a real one had
  just cost an hour. A test now reads every version string in the
  repo and requires agreement.
- USAGE[ValueStatistics] still said "full-population field", retired
  in 1.29.0. Fixed, and neutralised (people, jobs, dwellings).
- 269 tests (265 + 4). QGIS findings FIELD-CONFIRMED on 3.42.1.

## v1.29.2 (the door opens, reads fast, and machine 2 keeps John's rule)

- 78 THE PLUGIN NO LONGER DIES AT LOAD. One line did it: the decay
  list was built at MODULE level, so a package older than the plugin
  killed the import before QGIS had anything to attach a message to.
  Every guard for that case lived inside processAlgorithm. Built on
  USE now; shortHelpString survives a missing package; both of Pro's
  probes ported, including the OLD-package one, which is the harder
  case because `import equipop` succeeds and only the newest module
  inside is absent.
- 68 WAS MISNAMED. It blamed the GeoPackage. Materialising 8,730
  features took 0.11 s. The cost was ours: attributes() once PER
  FIELD, each call building a list of EVERY field and keeping one
  value. 31 fields on John's layer - result columns from earlier runs
  - so 270,630 calls converting 8.4 million values to obtain 270,630.
  Every run made the next one slower, squared. One pass now: 5.40 s
  -> 1.00 s measured on the real file.
- 76 THE LADDER, reference side only. Machine 2 can restrict who is
  around: "the mean income of the nearest 400 RESIDENTS" in a layer
  that also holds workplaces. Pro's getParameterInfo still counted
  boxes by POSITION and would have slid the measures list onto the
  percentiles box; converted, with two tests that did the same.
- 83, FOUND BY 76 WITHIN MINUTES. ORIGIN and MEMBER were one set in
  machine 2. Now separate, so a non-member gets its own results, as
  machine 1 has always done. The k-search needed no change - that was
  tested from an empty cell BEFORE any bookkeeping was touched. An
  unknown count is treated as machine 1 treats it (John's ruling).
- Two pre-existing tests asserted the OLD behaviour and were
  REVERSED deliberately, with the reason on the line.
- 274 tests. The QGIS numbers are field-measured on 3.42.1; the
  ladder is simulator-only in both doors and wants an evening.

## v1.29.3 (John's field evening, and the bug in the door we thought was fine)

- POLYGON BARRIERS CRASHED on the first real lake. Lines are points
  per part, polygons are RINGS per part - a lake may have islands and
  is charged by AREA. _paths_of flattened one level too far. It
  survived because the QGIS tests had NO polygon barrier and COULD
  not: the stub lacked QgsGeometry.fromPolygonXY, which real PyQGIS
  has. A stub too GENEROUS certifies code that cannot run; a stub too
  SPARSE narrows what can be asked, and the gap looks like coverage.
- 85 THE TWO LADDERS ARE INDEPENDENT AGAIN. treatmode was ignored
  unless refmode was on rung 3. An empty grouping now refuses loudly,
  and a reference table filled on the wrong rung says it is ignored -
  QGIS cannot grey a box out, so the notice is the only warning.
- 86 PARITY OF BEHAVIOUR. door_parity.LADDER_CASES runs the same
  dialog combinations through BOTH doors and compares the columns.
  On its first run it found that PRO HAD THE SAME BUG, twice over,
  in _run_tool - after Claude had told John Pro was correct, having
  read the code rather than run it. Add a rung, add a case.
- 84 DEPRECATIONS CLEARED, minimum raised 3.28 -> 3.38 (John's
  ruling). The stub DROPPED parameterAsFields so nothing can regress.
  Worth remembering: stub_audit checks that a method EXISTS, and a
  deprecated method exists perfectly well - John reading the QGIS log
  is the only thing that catches this class.
- THE HELP PANEL WAS NAMING COLUMNS THAT DO NOT EXIST. QGIS renders
  the help as HTML and Qt ate <field> and <group>, so it printed
  Nv__k, T__k, R__k. Escaped now.
- MACHINE 2'S TREATMENT BOXES numbered 2/2a/2b/3/3a at last - QGIS
  writes its own labels and only Pro's were changed in 1.29.0.
- 283 tests. Every fault here came from one evening of John's.

## Done

- ~~1~~ | DONE v0.7 | Seeded tie-break orientation: a user-settable seed determining the within-ring visiting order in `tie_mode="sequential"`, with the seed written to the metadata log (`settings.seed`) | Ring mode unaffected (order-free by design). Makes sequential mode fully reproducible.

- ~~2~~ | DONE v0.7 | Metadata log file — full design agreed, see below | Implement as one batch; pairs with #1.

- ~~3~~ | DONE v0.7 (convert path; 6-neighbour hex friction remains) | Hexagonal grids: convert or simply import point/raster data as hexagons (X/Y/Z axial or cube coordinates) | From the original spec. Design thoughts below.

- ~~5~~ | DONE v0.9 (repo built; publish + PyPI-name check remain manual steps) | GitHub sharing preparation | Strategy: repo layout (src/equipop, tests/, examples/, docs/); pyproject.toml with optional extras [geo]=geopandas,rasterio [fast]=scipy [xl]=openpyxl,pyarrow; turn the demo validations into pytest suite (Berlin regression, Sweden brute-force, wall test, decay properties, Malta totals); LICENSE decision (MIT vs EUPL - user choice); CITATION.cff pointing at the EquiPop papers; README = trimmed manual quick starts; GitHub Actions CI running pytest on push; versioning via git tags matching manual history; CONTRIBUTING with the design-decision log as ground rules; publish to PyPI when named (see naming note in spec).

- ~~6~~ | DONE v0.8 (evenness+exposure; delta/concentration family awaits the area-term decision) | Segregation index module (per US Census formulary + Östh/Clark/Malmberg 2015) | Aggregate indices computed FROM k-NN output across all origins i, per k: Spatial Isolation SI_k = sum(x_i * (x_ik/k)) / sum(x_i) (the 2015 paper's measure - weight each origin's k-share by its own minority count); interaction (x->y) analogue; Dissimilarity D_k = 0.5*sum|x_i/X - y_i/Y| over bespoke neighbourhoods; entropy/Theil H_k; Gini_k (segregation form, from the census formulary, distinct from the inequality Gini already implemented); Atkinson(b); correlation ratio (I-P)/(1-P); delta & concentration family needs area a_i = k-neighbourhood footprint (Dist_k-derived) - flag as derived-area caveat. Design: segregation.py taking a run_knn(_stats) output DataFrame + k list, returning one row per k per index - i.e. POST-ANALYSIS on existing output, no engine change. Validate against Table A4 style numbers (SI for k=100/6400) when a suitable dataset exists.

- ~~7~~ | Stata part DONE v1.1 (bridge pytest-tested; ado sfi-glue awaits first in-Stata run); QGIS part remains | Stata & QGIS availability | QGIS: ships Python - short term a processing-toolbox script (paste-in) calling equipop if installed in the QGIS python (pip install via OSGeo shell); mid term a minimal plugin wrapping InData->run->load-result-as-layer. ArcGIS Pro: arcpy python env can pip install equipop (conda-based env cloning), no plugin needed for script use. Stata: no embedded CPython officially until recent versions - Stata 16+ HAS python integration: `python:` blocks share data via sfi (Scala Function Interface) Data class; strategy = thin equipop_stata.ado + python glue: read frame via sfi.Data.get(), run equipop, write back new variables via sfi.Data.addVarDouble()+store - enabling the requested regress->knn->regress round trip entirely inside Stata. Deliverable order: (1) plain .do example with python block, (2) ado wrapper, (3) QGIS processing script, (4) QGIS plugin.

- ~~8~~ | DONE v0.8 | Map visualisation of output + export | matplotlib-based map_output(df, column, classing=quantiles/equal/sd/jenks, n_classes, basemap=None/simple-extent, north arrow + scale bar + legend with class bounds); jenks via jenkspy (small pip dep) with fallback to quantiles; hexagons drawn as polygons, grid as squares; export .png/.svg/.pdf via savefig plus data export of the classed column (save_output already covers gpkg for GIS styling). Colour: viridis default, diverging option for ratio-around-mean. Keep it deliberately simple - QGIS is the real GIS; this is quick-look QC.

- ~~9~~ | DONE v0.8 (all three alternatives) | Area-based output (policy-friendly aggregation of k-NN results) | Three alternatives, same principle - bring overlapping bespoke-neighbourhood output back to fixed geographies that policy makers grasp: **Alt 1** user-provided belonging ID (location/municipality code already on the data; label_col/CellId machinery is the natural carrier) -> aggregate any output column per ID (mean/median/pop-weighted mean, N). **Alt 2** uploaded polygons (shp/gpkg municipalities) -> point-in-polygon assignment of origin cells (geopandas sjoin), then as Alt 1. **Alt 3** coarse grid/hex scales - e.g. 100 m results aggregated to 1000/5000 m super-cells; aggregation origin anchored at min X/Y/(Z). Design: one post-analysis function `aggregate_output(df, by=..., how=...)`; document explicitly that overlap-then-aggregate is intentional (bespoke values summarised per area, not area-recomputed) so reviewers don't mistake it for a contradiction. Pairs naturally with #6 (per-area index reporting) and #8 (choropleths per area).

- ~~10~~ | DONE v0.9 (MANUAL_TOPICS.md) | Topic-based beginner manual | Restructure the manual by TOPIC rather than version/dataset: Installation; File formats & data management; Projections; Grids or hexagons; Selecting k-values; Determining decay; Determining friction; Statistics; Segregation measures; Area output; Metadata & reproducibility; Troubleshooting. Keep the current version-history + validation-record + design-decision log as appendices (they are the scientific audit trail). Write once the v0.8 feature set lands so topics stabilise; each topic = concept in plain language -> minimal example -> settings table -> pitfalls.


- ~~30~~ | DONE v1.17 | Category & friction VALUE TABLES in the Pro dialogs (John's Extract-Multi-Values pattern): a grid with *value* (dropdown built from the field's own distinct values), *group name*, *in population?* - retires the `;`/`,`/`:` syntax entirely and expresses "in a group but not in the population" (services near residents). Same grid for MULTI-SOURCE friction: source + friction field per row, so lines + lake + raster finally coexist and the overlap rule becomes reachable at all | Field-found: `shop, school` parsed as ONE group matching zero rows; also today's only way to combine barriers is a single layer

- ~~31~~ | DONE v1.17 | Persons-versus-places rule for category groups: with a population field set, N counts PERSONS while category flags count ROWS, so R = places / persons silently. Add an explicit control (default: weight categories by the population field) and state it in the messages and manifest | Field-found: T=4 places over N=140 persons

- ~~32~~ | DONE v1.17 | A group/category matching ZERO rows must be a dialog-time REFUSAL naming the field's actual values, not an info line among fourteen | Silent columns of zeros are exactly the wrongness EquiPop refuses elsewhere

- ~~33~~ | DONE v1.17 | Collapsible dialog sections via each parameter's `category` property (Coordinates / Neighbourhood / Groups / Barriers and terrain / Output / Advanced) + a full label pass saying what each box DOES | 29 parameters presented at once; John: "they were not fully clear to me watching the menu"

- ~~35~~ | DONE v1.17 | Individual / local TAU (effort budget from a field or a single value), mirroring variable-bandwidth decay. Easier than decay: the traversal already stops at a budget, so a per-origin budget is just a different stopping value. Naming: N_tau_<field> since the column can no longer carry the number | John: tau is the HARD prism boundary, half-life the soft one - both parameterisable per person is a time-geographic instrument

- ~~36~~ | DONE v1.17 | Variable-bandwidth decay (the 1.17 theme): half-life from a field or self-calibrated from Dist_k (urban form sets the bandwidth); bucket into quantile bins so cost is dominated by the largest bin; combine several potentials via log-odds / geometric mean of half-lives, all three behind one switch and compared on Gridby | John's ladder: 1 no decay, 2 one parameter, 3 group potentials (Hägerstrand prisms), 4 form-derived, 5 principled merger

- ~~37~~ | DONE v1.17 | Seed exposure + manifest entry wherever permutations happen (morans_i, sequential tie-break). Engines are otherwise deterministic - note in the manual that this holds as long as summation order does |

- ~~39~~ | PARTS 1-2 DONE v1.20.0 | ~~Shared core ahead of the QGIS/R/SPSS doors: one help-text source, one reporter object, one loader contract~~ - DELIVERED as `equipop.doors` (help / report / fields / loader), ArcGIS re-pointed, 154 tests green. REMAINING: QGIS Processing plugin (simulated PyQGIS like the fake arcpy), R via reticulate (file bridge as documented fallback), SPSS via its Python integration. Gridby's answer key becomes the cross-door conformance suite | The ArcGIS glue got fat because three things were reinvented per door

- 46 | DONE v1.18.0 | The `.tar.gz` carried the package and the test
  CODE but not the ArcGIS toolbox, the Stata door, the fixtures its
  own tests read, or CITATION.cff. Verified against PyPI, not
  inferred: unpack the published equipop-1.17.3.tar.gz and 39 of its
  41 ArcGIS tests fail immediately on the missing EquiPop.pyt. An
  academic package also went out without its citation file.
  Long-standing (no MANIFEST.in had ever existed) and not caused by
  the shared core, but 1.18.0 makes it matter more: the toolbox and
  the package are now two halves of one thing. MANIFEST.in added;
  the Book's figures stay out because build.sh regenerates them
  (4.2 MB of a 4.8 MB archive). Archive now 121 files, 605 KB, and
  the whole suite - all 154 - passes from inside the unpacked
  archive alone.


- ~~47~~ | DONE v1.19.0 | **`load()` fails for anyone who installed from PyPI.**
  All four datasets: `gridby` reaches into `../examples/` for
  make_gridby.py, and `municipality`/`berlin`/`stata_test` reach into
  `../tests/` and `../stata/` - none of which is in the wheel.
  Verified in a clean venv against the 1.18.1 wheel: four failures
  out of four. Book chapter 1 line 85 tells the reader to type
  `g = load("gridby")` as their first act. Gridby is the TEACHING
  town, so this is the first thing a student hits. MANIFEST.in fixed
  the source archive; the WHEEL is a separate matter and is what
  students actually install. Fix: move the Gridby generator into the
  package (`equipop/gridby.py`, with examples/make_gridby.py left as
  a shim), ship the small fixtures as package data, and declare them
  in pyproject so they enter the wheel. Then a clean-venv test that
  loads all four - the kind of check that only fails outside the
  repo, which is why it has never fired.

- ~~48~~ | DONE v1.19.0 | The cross-door conformance reference (ruling made,
  1.18 session). Format: CSV, UTF-8, dot decimal, comma separator,
  fixed column order - every door reads and writes it natively, and
  a student can open it in Excel. It ships INSIDE the package
  (`equipop/data/`) so all four doors and every student reach it the
  same way whatever their install. Generated by the Python core -
  already the trusted engine - from Gridby at a fixed, documented
  parameter set. Comparison lives in `equipop.doors` so Pro, QGIS,
  Stata and SPSS all judge themselves identically: counts and Rounds
  EXACT (they are integers), continuous columns within a stated
  tolerance. Blocked on 47: shipping data inside the package is the
  same fix.



- 50 | PARTLY DONE v1.21.0 | QGIS gained the CATEGORY TABLE (with the
  remainder box) and DISTANCE DECAY. Still missing: BARRIERS and
  TERRAIN, which need the friction-building path (points/paths to
  friction, DEM slope) ported to read QGIS layers. Same engine
  underneath. Same shared code underneath - boxes to add,
  not machinery to build. The remainder box (below) should land here
  at the same time.

- ~~51~~ | DONE v1.21.0 | THE REMAINDER BOX (agreed with John, 1.19 session):
  one box under the category table - "Put every other value in this
  group:" - so a few values can be named 'service' and everything
  else falls into 'other', in the population. Today the only way is
  to untick every 'In population?' box, which reads backwards. Build
  the rule in the engine and the help in the shared core so BOTH
  doors get it.

- ~~52~~ | CLOSED v1.22.2 as NOT OURS | GeoPackage attribute table does not refresh after a
  run (John, field, 1.19 session). The toolbox writes with
  ExtendTable and declares NO derived output, so Pro keeps its
  cached schema; removing and re-adding the layer forces a re-read,
  which is the workaround John found. Likely fix: declare the
  modified layer as a derived output parameter. UNVERIFIED - needs a
  field cycle on Malta.gpkg AND on a file geodatabase.
- 34/44 | open | Tool help page summary/usage renders empty in Pro;
  SyncOnce=TRUE suspected, one line in make_help_xml.py. Needs a
  field cycle. Students read this page.

- ~~53~~ | DONE v1.22.1 | The barrier path went through the same
  _ref(), so the catalogPath fix closes it too - though a barrier
  from a .gpkg still has not been FIELD-tested.

- ~~56~~ | DONE v1.29.0 | Machine 2 (Value Statistics) still uses the old
  vocabulary - "Full population field", "Numeric value fields". It
  should be reference-population language too, for the same reason.

- ~~60~~ | DONE v1.29.0 (merged into 56) | MACHINE 2 still uses the old vocabulary and has no
  ladder. Same treatment needed: a reference-population section with
  the same three rungs, and value fields named as values (weighted
  by the reference), not as "treatment".

- ~~63~~ | DONE v1.26.0 | Barriers and terrain in QGIS. Deferred
  again rather than started half-finished - it needs the friction
  building path (points/paths to friction, DEM slope) ported to read
  QGIS layers, which is a round of its own.

- ~~64~~ | DONE v1.29.0 (merged into 56) | MACHINE 2 vocabulary (was 60) - not started.

- ~~69~~ | DONE v1.29.0 (merged into 56) | MACHINE 2 vocabulary - still not started (was 64).


- ~~70~~ | DONE v1.27.0 | FACILITATORS (John's academic question, worth a real
  answer). Entering a cell costs 1 + friction, so a facilitator is a
  value between -1 and 0: -0.5 halves the cost of a cell, -0.9 makes
  it a tenth. The engine currently refuses anything below zero,
  which is stricter than the mathematics requires - the true floor
  is -1, where movement becomes free. Relaxing it would let
  motorways be modelled as genuinely faster, the natural counterpart
  to barriers for accessibility work. Needs a decision on what
  happens at exactly -1 and whether the shortest-path expansion
  stays well-behaved.


- ~~71~~ | DONE v1.29.0 | The ArcGIS door has no facilitator help text yet and
  its barrier help still says costs must be positive. Same for the
  Book (ch09) - queued with the friction/delay writing session.

- ~~72~~ | DONE v1.28.0 (Book ch09) | Dist_k under effort is NOT a radius: the neighbourhood
  is a shape moulded by the cost surface, and Dist_k is how far away
  the last person reached happened to be. Comparing Dist_k with and
  without a barrier measures how much the barrier REARRANGED the
  world. Worth a paragraph in the book (John's insight, and Claude
  was wrong about it first).


- ~~73~~ | DONE v1.28.0 | The barrier/terrain block moved into
  QGIS's Advanced area (16 everyday boxes, 11 advanced), and the
  help panel names what is in there - Pro's collapsed section shows
  its title, QGIS's Advanced area does not.

- ~~74~~ | DONE v1.29.0 (merged into 71) | The ArcGIS help text still says friction costs must be
  positive; it predates facilitators. Book ch10 (slopes) may need
  the same pass.

- ~~75~~ | DONE v1.29.0 (merged into 56) | MACHINE 2 vocabulary - carried forward again.
