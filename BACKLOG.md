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
1. ~~**139**~~ — DONE, unreleased. A diagonal move now costs sqrt(2); iso-effort contours are round, not square
2. ~~**99**~~ — DONE v1.30. THE OVERSHOOT, closed at both doors; ~~**162**~~ and ~~**163**~~ travelled with it
2b. ~~**164**~~ — DONE v1.30.1. John's field test: a new feature class received every result ONE ROW EARLY, silently, since v1.20
3. **161** — Pro will not offer a barrier raster from the map. John field-found it: he had to drag and drop. Small, and it makes the barrier box behave the way the DEM box and all of QGIS already do
4. **102** — QGIS has no bandwidth boxes, so the 1.17 headline feature is missing from the teaching door
4. ~~**128**~~ — STATA HALF DONE v1.37 (`equipop doctor`). Pro and QGIS still to do; the dependency story is the adoption risk
5. **129** — version the output SEMANTICS, not just the structure. 1.29.5 changed what Dist_k MEANS and said nothing
6. **117** — one validated run specification, used by the package and every door
7. **120** — move reference and treatment construction into shared package code
8. **133** — a fourth door (R, SPSS). GATED BEHIND 120: every door is another copy of the logic that produced 108

9. **CONTINENTAL RUNS / 38** — segmentation and tiling as its own machine; John's destination, and machine 3 waits behind it. UNPAUSED by John, 1.29.3+
10. **118** — weighted statistics without person expansion. BLOCKER for the continental machine
11. **119** — resume must validate its parameters and fingerprint its input
12. **93** — the WORKING FRAME (choose by extent, offer WGS84 with great-circle). It decides what 38's numbers MEAN, so it is settled before 38 is coded
13. **149** — suggest_projection splits a 2-degree extent because it straddles a zone boundary; one zone costs 0.17%
14. **92** — the continental DATA path: name the files instead of fetching the zip, cache populated cells once
15. **137** — WorldPop is per COUNTRY and 92 assumes one; concatenate the extracted cells, never mosaic the rasters
16. **124** — fetch caches by filename only; WorldPop filenames repeat across countries
17. **125** — QGIS runs cannot be cancelled; needed before continental GUI work
18. **97** — a decayed denominator is not a count; machine 3's standard errors need the effective sample size. RULED IN by John 1.29.5
19. **106** — decay for machine 2; engine work, and the same job as 97
20. **98** — mortality by differencing: keep the raw negatives, report the count. Clamping inflates mortality up to 11.8x. RULED by John 1.29.5
21. **82** — machines must be DISCOVERED, not hard-coded; 38 is itself a machine and machine 3 waits behind it, so the doors stop counting to two
22. **90** — the decay-truncation box steps by 1 in QGIS: a stray click turns 0,000001 into 1,000001 and the run succeeds. A silent wrong answer, and a cheap fix
23. **67** — QGIS barriers are simulator-proved only - an evening of John's, not a release of Claude's
24. **58** — same evening: a GeoPackage barrier layer has still never been run
25. **88** — and polygon barriers have never been run in PRO; same subject, same evening
26. **42** — the illustrated manual still never describes variable-bandwidth decay - a WRITING session
27. **81** — the Book has a chapter for the Pro door and none for QGIS, which is the door being taught with; travels with the next BOOK run
28. **44** — the suspected one-line cause of 34; they travel together
29. **34** — Pro renders the help page empty; needs one field cycle to confirm
30. **87** — the simulated arcpy is WRONG rather than sparse, and makes a real Pro dialog route untestable
31. **101** — the suite writes run manifests into the working directory; on Windows that is a real C:\Data\
32. **91** — RULED already: short decay labels in both doors; travels with the next release that touches the doors
33. **89** — the output-table rule refuses a run that has already said where its output goes
34. **49** — extend the conformance reference beyond counts and stats - a second door now proves the mechanism
35. **45** — small, but these files ship inside every release zip
36. **62** — the shapefile-in-a-map warning may be too eager; John's eye decides
37. **100** — MedDist_k as its own column, computed exactly from the rings rather than as r/sqrt(2). Never folded into Dist_k
38. **41** — the reconstructed 1.17 MANUAL row has never been checked against what shipped
39. **43** — CITATION.cff still says 1.0.0 - the author's to set, not Claude's
40. **77** — the rest of the neutral-vocabulary pass, to be shown before it lands
41. **59** — does QGIS refresh GeoPackage fields properly? one look answers it
42. **61** — whether the rungs READ well in Pro is John's call, not the simulator's
43. **55** — same: the simulator honours category and enabled, only Pro can say they read well
44. **54** — Gridby has no missing data, so the missing-data rules rest on small fixtures
45. **57** — retire the old single-table path once John confirms no saved tool needs it
46. **40** — one sentence in the Gridby README
47. **4** — heights / third dimension - design can precede data, and there is no data yet
48. **3** — hexagons: the principled fix for 139, and hex.py already exists; the 6-neighbour friction graph is the missing piece
49. **80** — run the stub audit in a live QGIS every release that touches the QGIS door
50. **66** — not a task: a standing caution about editing multi-line Python

51. **107** — MANIFEST.in omits the demo scripts, so they have never shipped in an sdist
52. **123** — run metadata records absolute paths and machine details
53. **126** — a text category is lost whenever any value in the column parses as a number
54. **127** — Value Statistics skips the version warning and shadows `wanted`
55. **130** — Stata is not SSC-ready: no .sthlp, contradictory version headers, treat() wrongly mandatory
56. **134** — a golden dataset with expected results, one per host
57. **132** — a public ArcGIS Online item; the .pyt is already the right artifact
58. **158** — hex self-potential uses a square-cell area, overstating the radius by 7.5%
59. **159** — RunLog is not the progressive record the manual promises
## Still to do — detail, in the order above

- ~~95~~ | DONE v1.29.5 | SELF-POTENTIAL, shipped. equipop/selfpot.py holds the rule once so the two engines cannot drift; both apply it; both doors offer `selfpot` and BOTH ARE CHECKED ON VALUES, not names. Default 1.0, John's ruling. Guards broken on purpose six ways before being trusted - including the Pro one, whose FIRST version passed against a deliberate break because it drove _run_tool and skipped the dialog hop where `or 1.0` eats a falsy 0. Rewritten through execute(). s=0 reproduces pre-1.29.5 numbers exactly, asserted not assumed.

- ~~96~~ | DONE v1.29.5 | Fixed by 95 and made loud. The substitution now prints a WARNING with the count and percentage, and the reported bandwidth range is the range BEFORE substitution - it used to be after, which hid it completely. Field check: 6,000 rows with a dense block, s=0 -> 'WARNING: 3,000 of 6,000 rows (50.0%) ... given the MEDIAN bandwidth (632 m)'; s=1 -> no warning, and the dense block becomes its own bin at a 10 m half-life instead of hiding in a 632 m bin.

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

- 203 | OPEN, QUESTION FOR JOHN | SHOULD A RADIUS RUN REPORT A
  DISTANCE AT ALL? 202 establishes that Dist_r would be the constant
  the user typed, which is useless. But two OTHER distances inside a
  fixed radius are not constant and are not currently offered:
  the MEAN distance to the N_r people found, and the distance to the
  FURTHEST one actually included, which is <= r and varies. Both are
  real descriptions of how the population sits inside the circle, and
  the second is the natural companion to Dist_k. Not a defect and not
  urgent - a method question, and John's to rule on. Do not build
  before he does.

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

- 205 | OPEN, REAL GAP | THE STATA COMMAND CANNOT REACH MACHINE 2 AT
  ALL. There is no stats() or values() option in equipop.ado's syntax
  line - mean, median, quantiles and Gini over a neighbourhood are
  unreachable from Stata except by hand-written python: blocks, which
  is exactly why section 6 of the showcase exists and exactly why it
  was able to rot unnoticed. THIS ALSO EXPLAINS BLOCK 20 OF THE FIELD
  PASS: whoever wrote treat(ValFloat) missing(0) was not being
  careless, they were reaching for the only handle the door offers. A
  user with a continuous variable has nowhere correct to put it. QGIS
  and Pro both expose machine 2. Sizeable, and NOT for this week.

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

- 196 | OPEN, SMALL | `equipop setup` IS NOT VERSION-PINNED AND
  RETURNS SUCCESS ON A PIP FAILURE. It runs `pip install --upgrade
  equipop`, so a 1.40.4 command file can pull a newer engine after a
  later PyPI release - doctor detects the mismatch afterwards, but
  setup created it. And it prints "PIP FAILED" then returns normally,
  so a scripted install has no failure code. FIX: pass the .ado
  version in and install equipop==<that version>; return non-zero on
  pip failure.

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

- 44 | open v1.18.0 | `make_help_xml.py` still writes
  `SyncOnce=TRUE`, the suspected cause of item 34 (summary/usage
  rendering empty in Pro). Untouched this round: it needs one field
  cycle to confirm, and this was a refactor release. Now a one-line
  change in a single place whenever that cycle happens.

- 34 | open v1.16.8 | Tool help page: summary/usage sections render empty in Pro. Suspect `SyncOnce=TRUE` letting Pro regenerate over the authored text, plus missing `datatype` attributes and plain text where escaped HTML is expected. The per-parameter comments (dialogReference) DO work | Needs one field cycle to confirm

- 49 | open | The reference covers counts and stats; friction,
  slope, fca and lisa are not in it. Now that a second door exists
  and the mechanism is proved, this is worth doing.

- 45 | open v1.18.0 | (1.29.0 note: the BOOK build does it too - docs/book/build.sh leaves gamma_decay_figure.png in the repo ROOT, because examples/cookbook_01 writes relative to the working directory. Same fix, same item.) The simulated-arcpy tests write their output to
  the Windows-style catalog paths they pretend to use, so a test run
  on Linux leaves four literal files named `C:\Data\...csv` in the
  repo root (and one stray figure from the Book build). Harmless,
  untracked, and cleaned by hand this round - but they belong in
  pytest's tmp_path, and on Windows those paths are real. Small.

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

- 43 | open v1.18.0 | CITATION.cff still says `version: 1.0.0` while
  the package is at 1.18.0. Left alone deliberately - citation
  metadata is the author's to set, and it matters more than usual
  ahead of the Zenodo DOI at 2.0.0.

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
