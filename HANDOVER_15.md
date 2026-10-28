# HANDOVER 15

*Session 12. Where 14 ended at **1.46.4**, this ends at **1.54.0**:
1,588 tests, SIX machines in QGIS and five in Pro, complete in-dialog
help in Pro for the first time, one analytical choice validated
against a published paper rather than against itself, a test that
asks whether anybody can reach any of it, the published
distance-decay method restored after twelve releases of silent
departure - and **equipop published on the SSC archive**, which is
the distribution the Stata Journal paper needs and the first time
this project has had a release it cannot quietly amend.*

*Amended through 1.63.1 rather than superseded: same session, run on
past 1.54.0 into October. Read section 0an first, then 0am back to 0b
in order - the header used to say "0k first", and stayed saying it
through six later sections, which is the staleness this file exists
to prevent. **1.54.0's stretch of the session ended by being
read from outside, three times in three days** - a pull request with
four findings, a full code review with nine, and then a review I was
asked to run on the project's own raster and demographic code, which
found fourteen more. Four of the first thirteen were mistakes made in
this session's own releases; **one of the fourteen made a guard I had
written two days earlier unreachable from the only path that could
trip it.** Before that, four of five releases were field findings,
none from the backlog, and three were about the project telling a
user something untrue. 1.50.0 is the exception: three items chosen
FROM the backlog, and the first thing they found was that the
backlog's own head was pointing at finished work - which the 1.51.0
review then found AGAIN, still pointing at it.*

---

## 0an. 1.63.1 - THE REVIEW OF 1.63.0

An external review (26 October) found five things; all reproduced
(scratchpad review1630/verify.py), all fixed (BACKLOG 448-452), two
logged as open (453 theta(k) time at register scale, 454 a first-class
segregation command).

- **"cells" said one thing and did another (448)** - and the note to
  learn is mine: 1.63.0 renamed the 1.62.1 formula (weights N_k) to
  "every place counts once" because under proportional overshoot every
  N_k is k. That is a coincidence of the default, not a definition.
  Equal weights now; numbers in the default mode unchanged (tested).
  When an option's NAME is a claim, test it on a case where the claim
  and the nearest other formula disagree (unequal N_k).
- **seg_profile now checks its input** (449) and says what it describes
  in its rows (452): SegregationError for undefined or impossible
  input; weighting, global_share_P, valid/excluded counts and a note on
  every row. Origins without a neighbourhood leave every index at that
  scale, SI included (450).
- **Cell size is checked in the package** (451): cells.check_unit_size
  in grid_midpoints, dispatch, FrictionGrid, build_hex_cells. A door
  may check too; the package no longer relies on it. equipop_run's
  unit() and wperm() are guarded before Python; missing() first,
  because Stata's . is greater than every number.
- **Break-check 436/436 on the first run.** The lesson of 0am applied
  in advance: each new test's data was chosen so it can show the fault
  its docstring names.

## 0am. 1.63.0 - JOHN'S THREE RULINGS, AND WHAT THEY FOUND

John, 26 October: "443= do as suggested - question (your call -
dismiss if not important)- should 1|2 be an option for the user to
decide, with 1 as default? 444 = fix according to suggestion 445 = as
determined earlier". Each one, done, found something further; all five
are BACKLOG 443-447.

- **443, segregation by people.** seg_profile(weighting="people") is the
  default, "cells" the option (his "1|2"). Both measure against the
  units' OWN weighted mean (P_ref), the only reference that bounds H
  and Atkinson at zero. Isolation at k under "people" IS SI; SI itself
  is untouched by either.
- **444, cell names.** overshoot.grid_identity is THE way to name a
  cell for a seeded draw: round(2 * centre / size), half widths. The
  floor() first proposed mends squares and still left 15% of hexagons
  sharing a name - found because the test asked for hexagons too. Do
  not call cell_identity with anything else. The tie test is a 3 x 3
  town at k = 65: under the old names all 40 seeds gave one answer AND
  the engines disagreed which.
- **445, fractional sizes.** Lifted in every door. What it took is the
  lesson: three more places still rounded (effort grid, output
  coordinates to 2 decimals, the ring engine's rebuilt-midpoint
  lookup). Cells are found by COLUMN AND ROW, floor(x / size),
  everywhere - never by a float midpoint rebuilt by arithmetic. The
  test that cannot be fooled is SCALE: the same town at 2.5, 0.1, 0.3
  and 100 must agree exactly, distances scaled
  (tests/test_fractional_cells.py) - the companion of 0al's
  translation test.
- **446, found writing 444's tests**: FrictionGrid's domain was
  int(lowest coordinate), so an odd size across 0 wrapped its first
  column to the far east edge. 1.62.1 said "all six places" were fixed;
  this was a seventh, in an engine its translation tests did not reach.
  test_odd_cells now covers friction and slope.
- **447, found by the scale test**: the effort engines gathered a ring
  by exact float equality, though RING_TOL was named for them. Last-bit
  differences split ties into a direction. Small (3-49 of 10,883 rows
  on the test data with a barrier), but wrong in kind.
- **Break-check 415/415** after three real gaps, all of one kind: a
  test whose data cannot show the fault it names. The test data's
  people-weighted share at k sits within 0.01 of P; random weights
  unrelated to the shares hide a formula that drops the weights; the
  bridge never takes the fast engine's per-origin path. Each got a
  case built to show it. When a docstring says BROKEN WITH, ask
  whether THIS data could show it.
- **Stata on an older engine**: both ados refuse a fractional unit()
  when the engine predates 1.63.0 (_engine_takes_unit); the floor
  eqp_min_engine stays 1.48.0 on purpose (331/385).
- **For John**: sampled draws change as if reseeded (444); the
  segregation profile's k rows change (443); a few friction rows change
  (447). Nothing else moves at 100 m or 1 km.

## 0al. 1.62.1 - THE REVIEW OF 1.62.0, AND STATA READY FOR SSC

An external review of 1.62.0 (26 October) found one pre-existing core
fault and six in theta(k); all reproduced (scratchpad
review1620/verify.py), all fixed (BACKLOG 439-442). John ruled the two
method questions: the no-groups check fits the outcome, and a p-value.

- **Exact midpoints** (cells.grid_midpoints, cells.exact_coords): THE
  rule for every square grid. Whole midpoints come back int64, so even
  sizes are unchanged byte for byte; odd sizes keep their .5. If you
  add a snapping path, use it - six copies of `.astype(int)` is how
  this happened. The test that cannot be fooled is translation
  invariance (tests/test_odd_cells.py).
- **theta(k)'s chance machinery** is _Chance: rows expanded to people
  once per k, outcomes shuffled IN PLACE, group sizes and the total
  fixed (they are permutation-invariant), family's part fixed under
  within-family shuffles. Memory: a few arrays per person, independent
  of `shuffles`. The p-value is (1 + #draws >= theta)/(1 + shuffles);
  a peak is named only where p <= 0.05, so 19 shuffles can say so.
- **theta_nogroups** is a WLS fit of y on [1, c, c^2] (and family
  dummies): the conditional mean. Empty, with a note, if it predicts a
  non-positive outcome - a log-link fit was tried and rejected: it
  gave 0.79 where the truth is 1 (y exactly linear in c).
- **Stata** (442): tests/stata_sim.py is the harness - read its
  docstring before trusting it further than it reaches. make_sthlp.py
  writes three help files. make_bundle.sh builds both Stata archives
  from equipop.pkg's f lines (the third written list removed this
  month, after the Pro sidecars and the round-trip test).
- **Break-check 381/381** after one real gap: a memory test on the
  whole run cannot see the shuffles - the engine sets the peak.
  Measure the part, not the run. (tracemalloc does see numpy.)
- **Left for John**: 443 (negative H and Atkinson at k scales in the
  segregation profile), 444 (cell identities collide in pairs in
  seeded draws) and 445 (fractional cell sizes could now be allowed -
  the test written to announce exactly that fired). All need his
  ruling; none is touched.

## 0ak. 1.62.0 - THETA(K) FOR A TEST ROUND; TOOLS 3-6 HIDDEN

John, 25 October 2026, three things (BACKLOG 436-438).

- **theta(k)** (equipop/opportunity.py, tests/test_opportunity.py,
  MANUAL_TOPICS section 17, cookbook_13). 405's step 4, unblocked by
  SHOWING John the binning question on data before asking it: a
  synthetic town (the generator is in the test and the cookbook) with
  three worlds - neighbourhood at 800 plus family, family only,
  nothing. He chose 10 groups, low education, family background for
  under-40s. Design points worth keeping:
  - the noise floor is MEASURED by shuffling, not a formula; with
    family, the shuffle is WITHIN family categories, which is the null
    for "nothing on top of family";
  - the no-groups check fits a quadratic on log y (MLD) - Theil fits y
    and is empty if a prediction is not positive;
  - own cell excluded by default (else small-k theta measures the
    household);
  - people in a cell with no context population are added as EMPTY
    cells so they still get a neighbourhood;
  - a peak is named in the messages only among k's above 3x noise -
    the first draft named a "peak" in pure noise.
  Python only; the matrix carries witnesses for QGIS, Pro and Stata
  (Stata is the likeliest next door: registers live there). John is
  to run it on his registers - expect questions about the context
  population (all adults vs. the cohort) and about family coding.
- **Tools 3-6 hidden until shown** (equipop/doors/toolset.py, tool 0
  in qgis/equipop_qgis/alg_show.py and EquiPop.pyt's ShowTools). The
  QGIS stub gained Qgis.ProcessingAlgorithmFlag, flags(), a registry
  and refreshAlgorithms; conftest gives the suite its own settings
  folder, so no test reads or writes a developer's real choice. Pro's
  tests and make_help_xml read `Toolbox().all_tools`, never `tools`.
  UNVERIFIED IN REAL QGIS: that HideFromToolbox re-evaluates after
  refreshAlgorithms() from inside a NoThreading algorithm. tool 0
  says "restart QGIS" if the toolbox does not change - ask John what
  he sees.
- **Box 1f**: the rates reference left Advanced in both doors; QGIS's
  advanced boxes renumbered (tiles 2e, output CRS 2f).
- **The first 1.62.0 bundle had no EquiPop.ShowTools.pyt.xml**:
  make_bundle.sh copied sidecars by a written list of eight names.
  It now copies `arcgis/EquiPop.*.pyt.xml` and checks the count
  against all_tools. Found by reading the bundle listing, not by
  any check - read the listing every release.
- **Break-check 351/351** after two fixes to θ(k)'s tests: a weight
  test with ONE weight for everybody cannot see weights ignored
  (use unequal weights), and a noise floor tested only in the null
  world cannot see 'no shuffling' (chance = theta there). Same lesson
  as 1.61.4's bump test: a check must be able to tell the fault
  from the truth in the case it is run on.

## 0aj. 1.61.4 - THE RADIUS WINDOW, AND THE REVIEW OF 1.61.3

An external review of 1.61.3 (23 October 2026) found one real fault
and three small ones; John said go (BACKLOG 430-435).

- **A radius must widen a window that ENDS ON it** (430). The fast
  engine's coverage test for radii was `covered < rmax`; a radius
  takes distance <= r, and the unfetched cells are at >= covered, so
  equality is exactly the case where the ring may continue outside
  the window. Both paths (_solve and _solve_batch) had the same `<`,
  so their bit-for-bit agreement proved nothing about it - **two
  implementations agreeing is not evidence when they share a rule.**
  The k-ring logic already did this right (it widens when the window
  may have cut the boundary); the radius was simply never held to
  it. tests/test_radius_window.py compares short windows with the
  whole map, which is the test that would always have caught it.
  test_window_sensitivity.py's "radius" test was about Dist_k, which
  is why this sat next to it unseen.
- **Guard a ratio on its own denominator** (431). The per-origin
  share tested the population, not the valid count, and computed 0/0
  for people with no usable value: right answer (NaN), 37 warnings a
  run. The batched path hid the same thing under np.errstate; it now
  passes the real denominator too (no behaviour change there, so no
  break-check entry for it).
- **windows_check.py: NEEDED / WANTED / REPORTED** (432). yaml is
  needed (pip name pyyaml, via PIP_NAME); cffconvert is REPORTED
  only - never suggested, because it pins jsonschema<4 and would
  break tools in Pro's or Anaconda's Python.
- **Wording** (433): release_record says "every other file" (the
  RELEASE note is added to the bundle after the record is written);
  REVIEWER_BRIEF points to the public repository for history. The
  public repo has tags for the published releases from v1.5.1 (not
  every release - some went out as archives only).
- **Ado banners** (434): equipop_knn.ado and equipop_run.ado carry
  the release in their `*!` line, in bump_version's DECLARATIONS
  and in test_packaging's round-trip list (that list is written out
  by hand on purpose - it must not come from the tool it checks).
- **Classifiers 3.11-3.15** (435). Labels for PyPI, nothing more: a
  pure-Python wheel installs the same way everywhere. (A stranger's
  suggestion that a 3.13 classifier would make pip pick "precompiled
  binary wheels" was wrong, and John was told not to apply it.) Each
  listed version is one the release record runs: environments for
  3.12, 3.13 and 3.14 are in the scratchpad under pyver/, built with
  `/usr/local/bin/uv` (3.12 and 3.13 are system Pythons; 3.14 came
  from `uv python install`). A test keeps the list starting at
  requires-python with no gaps. Before adding 3.16, check it is in
  trove-classifiers - PyPI refuses an upload with an unknown one.
- **The break-check found a test that checked the tool with the
  tool's own list.** test_the_version_bump_survives_a_round_trip
  read DECLARATIONS from bump_version.py, and its round trip cannot
  see a line the tool does not know (it never moves, so it comes
  back identical) - though its comment claimed it could. Removing
  a banner's declaration passed. Step (1b) now checks every
  stata/*.ado banner from the files themselves. The same shape as
  the radius fault: **a check that shares its rule with the thing
  it checks agrees with it.** (The third survivor was the break
  file's own error: a five-cell window holds the cross's whole
  ring, so it cannot show the fault. bc1614_three.py re-ran the
  three; all caught.)

## 0ai. 1.61.3 - PYTHON 3.15, AND WHAT IT SURFACED

John asked what the new Python means for EquiPop (22 October 2026).
Python 3.15.0 shipped on 9 October and 3.15.1, a security release, on
21 October. The answer was measured, not read: 3.15.1 was installed in
the session's sandbox and the whole suite run on it. It passed. Four
things were still worth fixing (BACKLOG 426-429):

- **Name the encoding on every text file.** From 3.15 the default is
  UTF-8 (PEP 686); before, it is the system's - cp1252 on a Western
  Windows machine, where ArcGIS Pro 3.6 runs Python 3.13. The
  .meta.txt was written in it: different bytes per Python, and on
  Windows a Turkish name ("Şanlıurfa") could not be written at all.
  tests/test_python_3_15.py has three guards - a simulated cp1252
  open, Python's own `-X warn_default_encoding` detector run as a
  subprocess, and an AST scan of all of EquiPop's code. **The scan
  cannot see a Path's `.open()`** (rasterio.open looks the same), and
  the detector cannot see Path.write_text (the warning is attributed
  to pathlib, not to equipop) - which is why there are three.
- **apply_vital and apply_vital_own RETURN the trimmed frame.** They
  no longer drop in place (pandas 3.1 deprecates `inplace=`). Both
  callers in run_indices take the return value; a new caller must too.
- **CITATION.cff failed its schema from 1.60.2 to 1.61.2**, and the
  check that says so skipped in every release run because cffconvert
  was not installed. venv_geo and the 3.15 venv now have cffconvert
  and pyyaml. **Not the system python3, and not the `test` extra**:
  cffconvert 2.0.0 pins jsonschema<4. Installed in the system python3
  it broke the `mcp` package there (removed again, jsonschema put
  back); in the extra it would downgrade any user's Jupyter. pyyaml is
  in the extra. A new citation test needs neither.
- **Python 3.11 is the floor.** A test checks that pyproject, both
  manuals, the reviewer brief and the Stata door's advice say the
  same number.

The 3.15 environment, to rebuild it: `/usr/local/bin/uv python install
3.15`, `uv venv -p 3.15`, then `uv pip install --only-binary=:all:`
the core and optional libraries (all have 3.15 wheels except jenkspy),
plus setuptools and build for the sdist test, and pyyaml (no 3.15
wheel; it builds from source, with its C extension). Beware
`/root/.local/bin/uv`: an old 0.8.17 that shadows the current one and
knows no 3.15.

## 0ah. 1.61.2 - EVERY FAST-ENGINE SETTING BATCHED

Decay, radii, `sampled` and long rings now take _solve_batch as well;
_solve runs only when BATCHED is False, which the tests use as the
answer key.

OFFERED TO JOHN, not built, waiting for his word:
1. **An "e0 anchored at 60"**: national mortality below 60, local
   from 60, so e0* = e0_nat + (l60/l0)(e60_local - e60_nat). It would
   sit beside the unreliable e0u, e30u and e50u.
2. **A per-cohort-k variant of life expectancy**, his own register
   practice: the distance to the k nearest people of each band, then
   the density ratio in place of S_b/S_a.

Also told him: as far as known, WorldPop's age structure comes from
census proportions by administrative unit. If so, the patchy e0u map
reflects those units, and validation should be at their level.

## 0ag. 1.61.1 - THE FAST ENGINE IN CHUNKS, BIT FOR BIT; PROGRESS

- **The default path is now batched.** fastcounts._solve_batch handles
  k values with whole or proportional overshoot, either self rule, no
  decay and no radii; everything else still goes through _solve.
- **_solve is now the REFERENCE.** test_batched_engine runs both
  engines and requires the same table bit for bit. A change to one
  must be made to the other.
- **Bit-for-bit depends on rowsum_like_numpy** reproducing numpy's
  pairwise sum. If a future numpy changes that order, the
  equal-to-np.sum test fails first: read that failure before
  loosening anything.
- John ran Turkey at 700 m with k = 5,000 and 9,000 (661,567 cells).
  The search was about 0.4 ms per origin before this release and is
  about a fifth of that now.

## 0af. 1.61.0 - OWN-COUNTRY RATES, TILES IN MACHINE 4, THE FORMULAS

BACKLOG 422 as agreed in 0ae. What to know before changing it:
- **The 'own' rule is per-POINT coefficients plus plain neighbourhood
  sums.** `apply_compose` gained a dict spec:
  {"cols", "by": "iso3", "coef": {iso: [...]}}. Any new measure that
  is a sum over people can follow the same route.
- **A changed default can hide the old path from its own tests.** The
  1.60 machine-4 tests silently started running 'own' and stopped
  reaching the 'cell' arithmetic. Three of the break-check's breaks
  survived for that reason, and those tests now run both rules.
- **METHODS_RATES.md has two copies**: at the top of the repository
  and as equipop/METHODS_RATES.md. A test keeps them identical. Edit
  both, or copy one onto the other.

## 0ae. 1.60.3 - CELLS IN ONE PASS; AN OLD PACKAGE IS REFUSED

John's first run of the rates on a whole country, Turkey at 1 km. Two
things came up the same day.

1. **The wheel had not been installed.** The traceback named 1.59.2's
   demography.py line 867. Every door now refuses a package older than
   itself.
2. **The run then sat silent for over an hour.** build_cells did four
   pandas operations per cell per group. It now runs in one pass.

His result map of TFR looked plausible to him (high in the southeast).

Next, agreed with John and NOT in 1.60.3 (BACKLOG 422):
- **Tiles for machine 4 in both doors.**
- **Each person read against their OWN country, as the default.** The
  cell's country, today's rule, becomes the option. Every estimator is
  a sum over people, so each pixel can carry its own country's
  coefficients before the neighbourhood sums are taken. That avoids
  splitting by country, and with one country it reduces EXACTLY to
  today's formulas. Concretely, per cell:
  - LE: X_a = sum_b S_b (P_a/P_b) L_b / l_a, against S_a;
  - TFR: E, E*r and E*TFR_nat, with r = C_nat/E_nat;
  - CDR: the deaths below 60, and S_b*m_b for each band from 60.
- **A methods document with every formula**, both forms, shipped and
  linked from the help.

## 0ad. 1.60.2 - THE EXTERNAL REVIEW OF 1.60.1

The review came the same evening: three P1, two P2, three P3, and
"product decisions". All reproduced first; all fixed; MANUAL's 1.60.2
row lists them. John decided two things:
- a blank cohort value in a point layer is NOBODY ("zero is our way -
  also because what is missing in some column (year or cohort) will
  be needed when compared later") - counted and said, never refused;
- the whole-country warning: WPP's national population now rides in
  the reference table, and under 90% of it is warned about.

Calibrations worth keeping:
- **The under-five finding was real but mostly cancelled.** Local and
  national children were counted the same way, so the ratio barely
  moved. It was fixed for being silent.
- **EPSG:None was older than the point route.** A raster folder in a
  custom projection failed the same way, since BACKLOG 277.
- **The degrees guess is now by name.** lon/lat and EastWest/NorthSouth
  are still guessed; plain x/y are refused.

Two lessons from the break-check:
- A test must not compute its expected value through the code under
  test. The coverage test did, and its break survived.
- `from equipop import fetch` is the FUNCTION. The module needs
  importlib, as test_fetch_reliability already said.

Open: the provenance of equipop/data/berlin_example.xlsx was asked of
John - if third-party, it belongs in THIRD_PARTY_NOTICES.md. Not done:
the preflight "health report", chunked point reading, a border policy
(cells still take the country of the point nearest their centre).

## 0ac. 1.60.1 - MACHINE 4 FROM MACHINE 3'S POINTS

John, an hour after 1.60.0, with a screenshot of Pro's machine 4
dialog: it takes only a folder of rasters, and should take the point
layer machine 3 makes as well. Both doors now have a second box. The
engine reads the points with `rasterfolder.load_points` (wide or long
shape, coordinates in their own CRS) through `load_source`, so
everything after loading - weights, compose, projection, cells - is
the folder's own code path. The test that matters: the same run from
the folder and from its points gives the same numbers - also for a
layer saved in UTM first, in both doors. Break-check 204 of 204.

Two things caught while writing it, in case they come back:
- Pro's factoryCode is not always EPSG. Esri numbers its own
  projections in the same field, so `_pyproj_crs` tries EPSG, then
  ESRI, then the WKT.
- In the long shape, the pivot keys are the coordinates and iso3 ONLY.
  The first version used every other field, so an OBJECTID made every
  row its own point. The totals were right; the point count was not.

**His screenshot also showed no rates box.** Because `indices` carried
no asterisk, it looked like the 1.59.2 toolbox (a required box with a
value shows none in Pro). It is not proven: he was asked to confirm
which Pro files he had.

## 0ab. 1.60.0 - RATES AND LIFE EXPECTANCY FROM ONE PYRAMID

John asked for a second-best local life expectancy built on national
data. Then he proposed reading the pyramid itself as the life table
(equal cohorts, no migration), and asked for TFR, CDR and CBR the same
way. **The design came out of a simulation, not a reading**
(BACKLOG 416):
- Read absolutely, John's rule measures growth: a Kenya-like nation
  with e0 65 reads 32.
- Read against the nation, the nation's birth history cancels.
  - From 60 it holds: within about two years under local growth
    differences, and untouched by young migrants.
  - From birth it does not: e0 49 for a true 65 at 3.0 % growth against
    2.2 %.

His ruling: build e60, and build e50, e30 and e0 too, FLAGGED, because
they are predictors for his models and he will validate them against
Swedish data.

**What is new:**
- `equipop/doors/vital.py` (the estimators).
- `vital_plan` / `vital_references` / `apply_vital` in
  `doors/demography.py`, in the same traverse as the indices.
- `equipop/data/wpp2024_reference.csv.xz` with its `.json` record.
- `tools/make_wpp_reference.py`, which builds the table from the
  wpp2024 R package. It REFUSES to write if its life tables miss WPP's
  e0 by more than 0.25 years; it was 0.05.
- Box 1e (the measures) and box 2d (whose life tables) in both doors.

**Decisions taken in the build, each said in the output:**
- **The nation's pyramid is the folder's OWN total per country**, not
  WPP's. The source's habits (age heaping, old ages overstated) then
  cancel where they are national.
- **TFR is read against the nation too.** Child survival, the five-year
  lag and counting habits then cancel. An absolute reading was 5-6 %
  low at 2.5 % growth.
- **CDR uses the nation's rates below 60, and above 60 a factor solved
  so a band life table gives the local e60.**
- **Each cell takes the country of the point nearest its centre.** The
  cell table carries no country code, and build_cells' label_col would
  have overwritten CellId.
- **Output columns are e60, e50u, e30u, e0u, TFR, CBR and CDR.** The u
  marks the unreliable ones, and every name fits a shapefile's ten
  characters at k = 10,000.

**The break-check found two tests that could not fail.**
- The empty-band test passed with the non-finite guard removed. An
  empty start band gives NaN on its own; the guard matters only for an
  INFINITE answer, which comes when the nation has nobody in a band
  that a border neighbourhood does. The test now builds that case.
- The nation's-CDR test passed with the e60 scaling removed, because
  the band-table approximation is too small to show at that tolerance.
  It now pins what it can see: theta solved the right way round.

**Found on the way:** `windows_check.py` needed its own pytest scratch
folder (John's first run, 18 Oct). It now also sits at the top of the
release archive, because John could not find it inside two zips.

**Open:** John's validation against Swedish municipalities; a
user-supplied national table (an SCB life table instead of WPP's); a
growth correction for e0 from the local TFR (exact in simulation, ±4
years for a 5 % TFR error).

## 0aa. 1.59.2 - AN OUTSIDE REVIEW RAN THE SUITE ON WINDOWS

The external review of 1.59.1 did what no release had done: it ran the
whole suite on Windows, the only system real ArcGIS Pro runs on, and
got 9 failures that Linux could not show. Every finding was reproduced
here before it was fixed. The one Windows-only fault, the lock itself,
cannot be produced on Linux, so os.replace was made to refuse the way
Windows does.
- **Windows refuses to replace a file for a moment** while a virus
  scanner or OneDrive looks at it. One such refusal on the fetch
  manifest stopped a fetch. Every swap (seven in machine 5, three
  more in bigrun and meta) now goes through `equipop/atomic.swap_in`,
  which tries again for about four seconds and then says what usually
  holds a file. Behind it was a worse fault: when the manifest could
  not be written at all, run_fetch said the files "listed above" had no
  provenance (the unrecorded one had never been listed), then that what
  arrived "IS recorded" - and the retry refused that very file. It now
  names the unrecorded file and says what to do. A file that has
  arrived but is not yet checked (its .md5 being fetched when the run
  stops) is removed, so a retry never meets it.
- **8 of the 9 failures were the simulator**, not the product:
  CreateTable filed tables under os.path.join, which on Windows
  is `work.gdb\wp`, and every look-up used `work.gdb/wp`. One
  normaliser, `table_key`, for every table path in and out.
- **The size limit added up the sizes the catalogue knew**, so files
  of unknown size passed any limit (all 40 of Burundi's against
  0.0001 MB). Bytes are now counted as they arrive (Net.block, after
  every 1 MiB, and once against the size the server declares), and a
  retried file counts once.
- **Cancel was heard between files only.** `cancelled=` is passed by
  both doors and asked after every 1 MiB, so a 1.9 GB .pbf stops
  part-way and is not kept.
- **A redirect was followed wherever it pointed.** safe_opener checks
  the new address as check_url checks the first, and refuses https to
  http. WorldPop and Geofabrik answer directly today. If that changes,
  the refusal names the address.
- **".gdb" as a substring** in three Pro checks: `data.gdb_backup` was
  a geodatabase. `_in_container` tests the PARTS of the path.
- The `C:\Data` escape in make_release_zip.py, plus a test that compiles
  every source file with warnings as errors.

**John's open question, answered with his go-ahead: a blank population
box now means EVERYBODY when the folder settles who that is.**
`rasterfolder.infer_everybody`:
- `sexes` when the year has every age band for women and men, with
  the same bands for both;
- `total` when it has every t_ band;
- refused otherwise, with the reason.

"Every band" runs from under-one to the open top band: 90+ for R2025A,
which the file names say, and 80+ for the older series. The review's
rule refused a folder holding both complete sets as "competing". It is
not: t_ is f_ + m_. That was changed, and is said in the log. The
choice is printed and recorded in the returned manifest as
`reference_population`. The tiled run's own manifest does not carry it
yet.

**Found on the way, twice:**
- Pro's machine 3 caught ContinentalError only. The loader refuses with
  ValueError, which is why John's 16 October refusal arrived as a
  traceback. Caught now, as QGIS has caught it since 1.43.
- The break-check found its own test outgrown. Once Cancel was heard
  inside downloads, the old QGIS cancel test passed with the door's
  between-steps check removed. A test written for that check alone
  (Cancel while .pbf layers are written out) then showed a real gap.
  Each layer was SAID before it was RECORDED, and `say` is where a
  door hears Cancel. So a Cancel at that moment left a GeoPackage that
  no manifest named, and the next run refused it as foreign. Now each
  layer is recorded first.

**For John:** `tools/windows_check.py` runs the suite on his machine
and writes a report to send back. That is the Windows job the review
asked for, without CI, which this project does not have.

*18 October:* his first run tested nothing. Every test stopped at
setup on "Access is denied" for pytest's own folder in
`AppData\Local\Temp`. The script now gives pytest a scratch folder of
its own; that fixed copy went to him by hand and is in the tree for the
next release. **His second run: 1,943 passed, 33 skipped, 0 failed -
the first clean run on Windows.** It also showed NumPy 2.5 deprecation
warnings at our raster reads, most likely from inside rasterio (see
BACKLOG 415). **His live check of the installed 1.59.2 passed too:** 88
real requests through the new redirect check, none refused, so the
providers really do answer directly. And machine 3 with the population
box blank, on a 5a folder: "works well" (18 October).

## 0z. 1.59.1 - JOHN'S FIRST PRO RUN, AND A DRIFT IT UNCOVERED

Four findings from the first real Pro run of fetch-then-curate. Two were
wording (the output boxes now say "geodatabase or memory, not a folder"
and "a folder on disk, not a geodatabase", and the dialog says so before
OK). Two were real:
- **Pro's machine 3 required a k**, where QGIS has made it optional since
  1.43 ("blank = just give me the points"). Fixing it exposed two faults
  hidden behind it: Pro's `_write_points` cast every column to float (the
  point table carries iso3 as text), and the lattice join Pro gained in
  1.47.6 needs the point table, so it was unreachable from Pro all along.
  door_parity checks box NAMES, not whether a box is required or how it
  is worded - which is how this drifted. The new test compares both.
- **The weight refusal offered 'total' to a folder with no t_ files.** 5a
  leaves the t_ sums out by default, so the most common fetched folder met
  a suggestion that would itself be refused. It now offers only what the
  folder can take.

**Open, and John's to decide:** should machine 3 take EVERYBODY when no
weight is given and the folder's columns are an age-sex partition? It
would remove the refusal for the common case, but it changes an analytical
default that was refused deliberately, so it was not done unasked.
*(Decided 17 October: yes, guarded - see 0aa.)*

## 0y. 1.59.0 - FETCHING IN PRO, AND WHAT THE LIVE CHECK SETTLED

**John's live check came back** (run in Anaconda, so with no GDAL and the
.pbf step skipped). Confirmed against the real services: WorldPop's
catalogue and files; a single shapefile LAYER read out of Sweden's real
1.87 GB zip in 12 requests; Germany as 16 states; Norway's 404 falling
back to .pbf; and Sweden's dated extracts on 1 January 2014-2026. **Still
not seen live: a .pbf written to GeoPackage by QGIS's GDAL.** John has
been asked to run 5b/5c on Liechtenstein 2020 in QGIS. **He did, the
same afternoon: it worked.** Every QGIS path is now confirmed live;
what remains unseen is Pro on a real machine.

**Pro got 5a-5c.** Two things are Pro's own and are worth knowing before
touching them:
- the catalogue is written with CreateTable + InsertCursor, NOT the
  inventory's `_write_table`, because NumPyArrayToTable cannot write a
  NULL integer and the open top age band has no upper age;
- 5c relies on Pro passing only the selected rows of a table view. It
  reads the view, never its catalog path, and says how many rows it got.

**John asked whether tool 6 should become 5-something.** No: it reads
any folder, fetched or not, and does a different job (what the files
hold, which share a grid) from 5c (where they came from). Kept as 6, at
his choice; 5c now ends by pointing to it.

**He also read "Population" as the age-sex files plus totals.** It is
one file of everyone. The dropdown now says so, and the real totals
(t_, T_F, T_M) are a visible box rather than an Advanced one.

## 0x. 1.58.1 - THE FIRST LIVE RUN, AND A FLAW IN THE BREAK-CHECK

**John's first live 5c stopped on its first file**: WorldPop closed the
connection without answering (`RemoteDisconnected`), and he read it
as a time-out. I could not reach WorldPop from the sandbox, so I sent
a one-minute script asking for the same file six ways. Every way
worked, EquiPop's name included, so nothing filters it and nothing on
his machine blocks Python. **But every request took 7-11 s**,
size checks and small files alike, where the probes two days earlier
measured 0.2 s. The server was slow and dropped one request. 5c had
tried each file once. Now `Net.attempt` tries a dropped, reset,
stalled, busy or cut connection again (4 tries; 3, 10, 30 s), says
each try, and never retries what retrying cannot fix. **Don't widen
`transient()` without reading why each exclusion is there.**

**The break-check harness was wrong, and it matters for every past
release.** A break that edits a file without changing its size, made
within the same second as the previous restore, matches the cached
`.pyc` on mtime and size, so Python runs the old code. Here that hid
a real break (`DEFAULT_TRIES = 4` -> `1`). It can also go the other
way: a same-size break's `.pyc` can outlive its restore and fail a
LATER test, which would read as "caught". **Run break-checks with
`PYTHONDONTWRITEBYTECODE=1` and empty `__pycache__` first.** 1.58.0's
79 breaks were rerun that way and all still caught. Earlier releases'
break-checks were not rerun.

**Speed is the next question, not correctness.** At 10 s a request, 40
files take about seven minutes. Parallel downloads (three or four at a
time) would cut that, at the cost of the per-file manifest commit
becoming a lock. Not done; recorded in 414.

## 0w. 1.58.0 - FETCHING BY SELECTING, NOT BY TYPING

John asked to "work intensively on the fetch function". The old tool
asked for a Setting/Value table in each provider's own words, and
every failed round in 268 and 284 was a right value in a wrong row.
The fault was the design.

**How it was decided.** Not from documentation (WorldPop's is four
years stale). I wrote three probe scripts - standard library only,
allow-listed hosts, request and byte budgets - and John ran them
against the live services on 14 October and sent the captures back.
They mapped each provider's hierarchy, measured file sizes, found the
providers' own faults (Norway's shapefile in the index and 404 on the
server; Germany with no shapefile at all; 'Georgia' twice), and showed
two things that made the design possible: Geofabrik answers HTTP range
requests, so one layer can be taken out of a 2 GB zip; and the GDAL
in QGIS and pyogrio reads .pbf, so past years are reachable.

**What was built.** `equipop/doors/catalogue.py` lists what exists as
ONE TABLE (26 columns, the same for both providers); `fetchrows.py`
fetches any rows of it through the existing `run_fetch`, so every old
refusal still applies. QGIS tools 5a (WorldPop), 5b (OpenStreetMap)
and 5c (fetch the selected rows). The old tool is 5d, for GHSL and
HDX, under its old id. The eight practices agreed with John are in
catalogue.py's docstring; the two judgements worth knowing:
- **One series across years.** If one WorldPop series covers every
  year asked, all rows come from it, even at a coarser or finer
  resolution than asked; resolution can be changed afterwards, method
  cannot. When none does, every row says so.
- **With years, every OpenStreetMap row is .pbf**, today's included,
  because Geofabrik's shapefiles and raw OSM tags are classified
  differently.

**What is NOT yet known.** Nothing here has touched the live services.
The fixtures are John's captures, and the fake web speaks HEAD, Range
and If-Range honestly, but these are untested for real: WorldPop's
HEAD sizes, a member read out of Sweden's real zip, real dated .pbf
files, and `osgeo.gdal.VectorTranslate` in QGIS (the call is checked
against a recording stand-in; osgeo cannot be installed here).
`tools/live_fetch_check.py` covers all four in about five minutes.
**Ask John to run it before calling 414 done.**

**Next, in order:** the live check; then Pro (5c needs pyogrio there
for .pbf); then GHSL as catalogue rows (regular names, 10-degree
tiles); then whether to offer Geofabrik's `-free.gpkg.zip`.

## 0v. 1.57.1 - THE ANALYSIS WAS APPROVED AND THE RELEASE WAS NOT

An external review of 1.57.0 arrived the next morning. It approved the
analytical code and said the ALL zip must not be published unchanged.
It was right about the zip, and the cause was mine twice over.

**A run record of mine was in two releases.** `equipop_working_tree.zip`
held `C:\Data/EquiPop_runs/people_EquiPop_run.csv`, which Windows will
not extract. It shipped in 1.56.0 as well as 1.57.0. My scratch script
for 410 drove the simulated Pro door from the tree root, and Pro writes
its run record beside the geodatabase. **And the guard against exactly
this has existed since 1.29.6** (156), in `make_release_zip.py`. The
bundle script I wrote in 1.54.6 never called it. That is the project's
signature defect - a rule in one place, a path that goes round it -
and I built the path. The tree zip is now built by that tool, every
shipped zip is extracted before a bundle is accepted, and the script
is tested in a throwaway repository.

**The bundle script could delete the repository.** `rm -rf "$OUT"` on
any path: `tests` emptied the test folder, `../EquiPop` removed the
whole tree. It now deletes nothing it is given.

**Two findings were not quite as reported, and that mattered.**
- The review's `.` example is refused by rm itself. The danger was
  real; that example was not it.
- The "stale" test count was right for my machine. geopandas adds
  exactly the reviewer's 19 tests. But a count that cannot say which
  machine it came from is not evidence. The record is now generated
  from the shipped zip.

The optional point - a scale-aware margin for `NgN_` - turned out to be
a real false message at WorldPop scale. Reproducing it, rather than
filing it as precautionary, is what showed that.

**The lesson for whoever builds the next release:** run scratch scripts
from the scratchpad, never from the tree. The builder now refuses what
they leave behind, but the tree should not need refusing.

## 0u. 1.57.0 - FOUR ITEMS IN THE ORDER JOHN APPROVED, AND THE ONE THAT WAS EXPENSIVE

John approved four items in my order: the faster split (409), a
coverage column (407a), a manual chapter, and machine 2 in the
proportional answer key (408). All four shipped together.

**409 made the split nearly free.** One field split into twenty
groups went from 196 s to 28 s, and three fields into twenty from
595 s and 1.4 GB to 59 s and 0.4 GB. Each group is now four additive
sums, which the engine adds up like people, with no sorted statistic
per group. The engine knows nothing about groups: `build_cells` splits
the sums by a code column inside one `bincount`, so the per-person
data does not grow with the number of groups. 405's identity test
certified it unchanged, at rtol 1e-11. **One design change came from
measuring rather than assuming.** Centring the logs, my first build,
still lost digits on large incomes with a small spread. Rescaling the
incomes themselves, since both indices ignore the unit, brought the
error down to the precision of the inputs.

**It found a 1.55/1.56 defect.** Where everyone in a neighbourhood
has the same income, the share is 0/0. With fractional weights, 1.56
reported one anyway in 282 of 600 constructed cases, mostly 1.0
("all between groups"), from rounding noise alone. Between and within
are now 0 there, and the share is empty.

**The chapter's numbers are read out of the chapter by a test.** The
1.56 note quoted a test town (6,005 points) I could not rebuild, so the
chapter uses one that `tests/test_manual_split.py` builds. That test
runs the chapter's own code block and checks every printed number at
the digits printed, so neither the text nor the code can drift alone.

**408 found a test enforcing the gap.** One test asserted that the
proportional key held NO machine 2 columns. Its reason expired in
1.31, so from 1.31 to 1.56 it guarded against the fix. It is
inverted now. Both doors match the extended key on all 2,360 rows.
A door that hardwires machine 2 to `whole`, the pre-1.31 workaround,
now fails, which the `whole` key could never show.

**Break-check: 29 of 29, after three corrections of mine, the fourth
release running.**
- `pytest.approx` adds an absolute 1e-12 unless told otherwise, so a
  precision test on an index of 4e-7 could not fail.
- Two BROKEN WITH claims were untrue. A `<=` with the rounding margin
  kept is the same test as `<`. And "2%" is a correct rounding of
  1.875%.

The procedure from 0t held: the breaks were written with the tests,
and they are what found all three.

**Open from here:**
- per-group means (John's format ruling);
- θ(k) (his binning ruling);
- 406;
- the live checks: QGIS aliases, and Pro and QGIS runs of the split
  at real scale. With the split now cheap, a k=1600 run on EquiTown is
  the natural next smoke test.

## 0t. 1.56.0 - WHAT THE COLUMNS MEAN, WHERE PEOPLE LOOK

John's first live Pro run of the split: a table header of MLDb_ /
MLDw_ / MLDsh_, `<Null>` in every visible row, and *"the w, sh, etc,
are not explained what I can see"*. He then asked for it to be built.

**The first thing found was that I had described the problem wrong.**
I wrote in 410 that no result column carried a description. The run
record did - a list of regular expressions in meta.py - and measured
on a real run it described 9 of 26 columns. Every T_ and R_ group
column, machine 1's main output, was "(no definition registered)",
and Dist_k was "0 inside the origin cell, in metres", which two
earlier releases had made untrue. **A description nothing checks rots
like anything else nothing checks.** So the fix was not a second
describer but making the one there was complete, correct and tested
against the predictor - and then using it everywhere a column is
read: the record, the run messages, Pro's field aliases, QGIS's.

**The line that answers the screenshot** is the summary: per field
and k, how many places got a split and why the rest are empty, in
rows. On a segregated test town at k=100 that is 4,670 of 6,005 empty
(2,670 with one group, 2,000 with a minority under 30) and at k=1600
it is 106. The absolute minimum in PEOPLE bites hard at small k - by
design, because sampling noise depends on how many people a group has,
not its share - and a user now sees that rather than having to infer
it.

**Pro's aliases are set after the write is verified, on geodatabases
only, and can never fail a run.** QGIS sets them too, but whether a
QGIS alias survives depends on the output format and version: that is
for John's next live run, not a claim.

**Break-check caught a vacuous test of mine for the third release
running** - this time a record test that passed the column list as the
DESTINATION argument, so the record held no columns and "none
undefined" was trivially true. Three releases, three of my tests that
could not fail the way they said. The lesson is now a procedure:
**every new test is broken before it is believed**, and the
break-check script is written with the tests, not after.

## 0s. 1.55.1 - A FAVOURABLE REVIEW, FOUR REAL FINDINGS, AND A POISONED INSTALL

The external review of 1.55.0 called it "mathematically sound" and
asked for a patch before broad publication. John wondered whether
some findings were obsolete - the zero and Theil items - but those
were under the reviewer's *what is strong*. **All four findings
reproduced, and two were worse than reported.**

- **Group codes** could become the wrong groups: `pd.NA` read as a
  group of its own, and two float codes printing alike shared one
  sub-field, turning a real MLD of 0.1308 into "between 0, within 0".
  The deeper fault was naming a sub-field by a DISPLAY label; it is a
  number now. The same class by another road - int64 codes above
  2**53 rounding together - was found while fixing it.
- **The overshoot help** still said machine 2 refuses proportional,
  eight releases after it stopped - in both GIS dialogs, Pro's
  sidecars and Stata's help. A claim no test reads outlives the thing
  it describes; this one now has a test that reads it AND runs what
  it describes.
- **Tests depended on the installed equipop.** The Pro help generator
  imported whatever was installed; `make_sthlp.py`, generating the
  same text, never had. This machine could not see it: its install is
  editable and points at the checkout, so "installed" and "checkout"
  were the same thing here.
- **Per-field measures were unioned**, and a zero in a field that
  asked only for Theil got the whole run refused in the name of a
  scaffolding field.

**THE METHOD WORTH KEEPING: a poisoned install.** An `equipop` whose
`__init__` raises, put ahead of everything on PYTHONPATH, turns every
quiet use of an installed package into a loud failure - which is the
only way to see this class from a machine with an editable install.
Over the whole suite it found what the reviewer's run could not: four
lazy-import tests that had always measured the installed package,
because conftest runs the suite from a temporary folder (BACKLOG 101)
and `python -c` imports from the working directory. On the reviewer's
machine they passed while checking 1.54.1. **A test that passes
against the wrong code is worse than one that fails**, because it is
believed. It also showed my 1.54.6 sdist test passing when the
generator died after one sidecar of five.

**The reviewer's benchmark, measured rather than estimated**: the
split costs nearly a value field per group. Two groups double a run;
twenty groups over three fields took 595 s and 1.4 GB against 44 s and
0.2 GB. The help says so now. BACKLOG 409 holds the fix, checked
before it was written down: MLD and Theil need four additive sums per
group and no sorting at all, 7e-10 against the sorted path.

**Break-check caught a test of mine for the second release running** -
a large-integer test whose two codes never collided as floats. The
pattern is now unmistakable: the docstring's BROKEN WITH line is
written when the test is, and is a hypothesis until a break proves it.

## 0r. 1.55.0 - JOHN'S IDEA, MEASURED BEFORE IT WAS BUILT

**Machine 2 now offers MLD and Theil, and with a grouping field it
splits them, in every bespoke neighbourhood, into the inequality
between groups and within them** - `MLDb_`, `MLDw_`, `MLDsh_` (the
between-group share), Theil's equivalents, and `Ng_` / `NgMin_`
saying how many groups were present and how big the smallest was.
QGIS and Pro both; Stata unchanged by ruling 205, because ineqdeco
already does this natively.

The idea came from a conversation of John's about inequality of
opportunity that was lost from the app; he pasted back what he had
copied and asked whether the methods belonged in the stats machine.
**Before anything was built, every claim the design rested on was
checked against the code**: that MLD and Theil split exactly (1e-17,
fractional weights), that the engine already computes a subgroup's
statistics from a value missing outside the group (it does, and says
so), and what each index does to a 0/1 variable (each is a transform
of the share - Theil = -ln p, Gini = 1 - p, MLD infinite - which
answered half of John's question and kept those columns out of the
binary family).

**His three rulings, and one was a question first.** He asked whether
replacing an income of zero with a small number would rescue MLD,
suspecting not. Measured, not argued: the replacement becomes the
answer (0.0013 for three people, 0.45 to 2.73 for four depending only
on epsilon), and the answer depends on the currency unit - 2.73 in
SEK, 1.01 in thousand SEK, 0.34 in million SEK. So MLD refuses a zero
and names Theil. A minimum group size, default 30, settable; below it
all three split columns are EMPTY, not zero, because the between part
is what small groups inflate. Ex ante only for now.

**Built without changing the neighbourhood.** Each value field is
split into one sub-field per group, named `inc[cob=abroad]` - a name
no GIS field can have - the engine runs exactly as before, and
`equipop/decompose.py` assembles the pieces. k still counts
everybody, pinned by test. **The certificate is an identity between
two routes that share no code below the engine**: between + within,
assembled per group, against the index computed directly over
everyone - 1e-14 in all three overshoot modes, with fractional
weights, k and radius, and where one of three groups is absent.

**The columns are level-independent on purpose.** A door predicts its
columns before it reads the layer, and the groups are not known then.
So per-group means are not written yet - their names would depend on
the data - and the prediction and the engine name the split with one
function.

**Four things found on the way, all small and all instances of
patterns this file already names:**

- QGIS machine 2 called the reference types `wanted`, the name of
  its measures list, so under rung 3 the log printed the types as the
  measures - since 1.29.2. **A name reused is a rule in two places.**
- Pro's description still said rows are "expanded exactly", which
  343 ended in 1.51. **A claim with no test behind it outlives the
  thing it describes.**
- `test_rungs` read the doors' menu lists with regexes, which glued
  `"theil",  # comment` and `"percentiles"` into `theilpercentiles`,
  and would have ended QGIS's list inside a comment holding `[0, 1,
  2]`. **A regex is not a parser**; one AST reader now, break-checked
  to still see a real drift.
- The reachability matrix's witness is `symbol in source`, so
  break-check's rename of `decompose_by` to `decompose_byx` passed it.
  The behavioural door test caught it. Recorded as 406 rather than
  fixed here: it changes how every row is proven. **A substring is
  not a dependency** - 1.54.5's lesson, at the scale of the whole
  matrix.

**And one of mine, found by break-check:** the hand-arithmetic test
claimed it was broken by "dividing by distinct values instead of
people", and with every weight 1 those are the same number, so it
was not. It now carries a weighted case worked by hand. 40 breaks,
40 caught. **A BROKEN WITH line is a claim, and claims get tested.**

**What is next is John's to unblock**: the scale profile theta(k)
beside `seg_profile`, where the types are DEFINED by neighbourhood
character at each k. It needs his ruling on how that character is
binned into types, because more bins push theta up.

## 0q. 1.54.6 - THE REVIEW CAME BACK POSITIVE AND THE ERRORS WERE ALL IN MY PROSE

The third external review of 1.54.5 returned **"a credible release
candidate... suitable for SSC"**. The code findings from the two
earlier reviews were confirmed fixed by measurement in his own
environment - Python 3.12.14, Rasterio 1.5.2 - not by reading my
notes about them.

**And it still found five things. Four of the five were claims.**

**THREE WRONG STATEMENTS IN MY OWN 1.54.5 RELEASE NOTE:**

- It said `equipop setup` would install 1.54.5. It requests `equipop>=`
  **the floor**, 1.48.0 - which is exactly what 332 decided and what
  the `.ado` has done ever since (`floor = min_engine or ado_version`).
  Setup works before the PyPI upload and *cannot install the
  unpublished release specifically*. The local wheel is the only
  pre-publication method. I wrote that fix in 1.54.5 and then
  described it wrongly in the same note.
- Its GitHub `net install` line fetches **whatever is on main**. Given
  to a tester before the tree is pushed, it installs the previous
  release's `.ado` while the note claims otherwise - a silent version
  skew, with the loud doctor warning downstream that I had just spent
  1.54.4 and 1.54.5 making legible. Push first, or install the
  supplied files locally.
- The test count had lost its environment qualifier. He measured 1,616
  passed / 28 skipped against the same 1,644 collected. Nothing is
  wrong; the skips are his optional dependencies. But **a test count
  is an environment measurement, not a property of a release** - first
  recorded at 1.54.1, re-learned here because I dropped the qualifier
  while editing the sentence that carried it.

These three were in text that no test reads. **The release note is the
only artefact in this project with no suite behind it, and it is the
first thing a new user obeys.** 0p's lesson was that a correct
document the reader cannot find does not help him; this one is one
turn worse - a document he *can* find, follows, and is misled by.

**THE TWO RESIDUALS, both fixed, both found by reproducing them:**

- **The floorless note contradicted itself.** 401's fallback could
  print *"this engine is too old to say"* and then *"so it is checked
  here instead"* - the second sentence answering the question the
  first had just declared unanswerable. Stubbing `_lines_floor` out
  reproduced it in one run. There are two real states and they now
  read as two: borrow the engine's own `_lines_floor` and print the
  satisfied line, or say the requirement is UNCHECKED either way and
  claim nothing more. **The test runs both branches** - a presence
  test passes on the contradictory version, which is 0p's ordering
  lesson in a new shape.
- **Cache validation accepted edited numbers.** Measured on a
  hand-edited `char _dta`: `people = -5` ACCEPTED, `people = 0`
  ACCEPTED, `points = -1` ACCEPTED, an inconsistent `share_cells`
  ACCEPTED. `_advice_is_coherent` now checks finiteness and sign and
  re-derives every share from the counts stored beside it.
  **One case genuinely cannot be caught, and the docstring now says
  so**: `people = 999999` is accepted because the payload holds no
  per-cell populations to total against. Before accepting that, I
  measured what it costs - after unpacking, `people` is read in
  exactly one place (the `format_advice` header) and reaches no
  decision. 1.54.1 would have called the function "validated". The
  limit is written where the next reader of it will see it.

**AND THEN VERIFYING THE BUNDLE FOUND TWO MORE, both the oldest shape
in this project: the thing exists and the path cannot reach it.** One
leak check on the archives did it, run on a premise that was wrong -
the sdist carries the five Pro help sidecars, and MANIFEST.in had
already ruled on that in writing: *"do not commit them, do ship
them."* Reading the recorded reason before fixing anything is what
stopped a correct decision being undone.

- **The durable release tool had no guard for them, and its own
  docstring states the rule it was missing.**
  `tools/make_release_zip.py` says: *"a manual step in the right order
  is not a fix, because the order will be got wrong again. So the
  check lives here, runs every time, and REFUSES rather than warns."*
  The sidecars are exactly that step - the bundle's Pro slot needs
  them present, the working tree must not hold them, so the order is
  generate, build, delete. My scratchpad build script checks for them.
  The in-tree tool, **the one that survives the session**, did not,
  and no existing check could see them: the BACKLOG 350 check skips
  whole directories, and these sit in `arcgis/` beside files that must
  ship. 1.54.0 shipped them and it was caught by hand. The tool
  refuses now, with the remedy in the message, and the test drives
  `build()` rather than the checker alone.
- **A test in this suite could not be reached as itself.** One
  function in `test_packaging.py` ran two tests: the 350 check, and
  then, after its assertion, a second docstring and the whole BACKLOG
  241 runner-imports check. A `def` line had been lost in an edit. So
  that check had no name, could not be selected with `-k`, never
  appeared in a report, and **ran only while the assertions above it
  passed** - break 350 and a guard silently stops executing. Fourth
  instance of that shape this session and the first inside the suite
  rather than the package.
  **Measured, because it is why this was invisible: re-merged, the
  file reports 34 passed instead of 35. Green either way, only the
  count moving** - which is this release's test-count lesson arriving
  from the other direction. `test_reachability.py` now walks every
  `test_*.py` by AST and fails on a string statement in the middle of
  a function body, that being what a lost `def` looks like.

- **And then my own fix for the first one silently emptied the source
  archive**, which turned out to be the root cause of all three. I had
  the build script generate the sidecars instead of trusting my memory,
  and put the step where the Pro slot needs them — *after* `python -m
  build`. Measured on the two tarballs: 1.54.5's sdist carries five,
  the first 1.54.6 sdist carries **zero**, with every check green.
  **`include arcgis/*.pyt.xml` is a permission, not a guarantee** — the
  files have to exist when the build runs. So 1.54.3, 1.54.4 and 1.54.5
  shipped them by accident of the order I happened to work in, and the
  test that asserts the MANIFEST *line* states the lesson it misses by
  exactly one level in its own docstring: *"a check on an artefact
  nobody ships is a check on nothing."*

**THE ROOT CAUSE, and it explains all three: the 19-slot bundle has
been built by a script living outside the repository at every release,
rewritten from the last one each time.** `tools/make_bundle.sh` is in
the tree now, carrying the order and the reason for each step, guarding
itself at runtime — it refuses if the sdist comes out with no sidecars,
if the working-tree zip has any, if the tree is left dirty, or if
pyproject's version is not the one asked for — and cleaning up on a
trap. Two tests, split deliberately: one BUILDS the sdist and looks
inside, proving the config delivers when the files exist and saying in
its docstring that it cannot prove they exist; the other asserts the
ORDER in the script, position being the property.

**One more time for the uniqueness rule:** my first break anchor for
the merged test matched **zero** times, because inserting a new test
had moved the text. The standing `count == 1` assertion said so, rather
than reporting a cheerful SURVIVED on a break that was never applied.
**18 break-checks across this release, all caught, no survivors.**

## 0p. 1.54.5 - THE FIX WORKED AND THE READER STILL BLAMED HIMSELF

John installed 1.54.4's commands against a 1.54.3 engine and asked
**"where did I go wrong during installation?"**

He had not. His output carried 401's new note, so that fix was working
- and the note was printed **after the VERDICT**, pages below the loud
release-number remark it exists to correct. He read *"THE ENGINE IS
OLDER THAN THE COMMANDS, and that combination does break"*, concluded
he had mis-installed something, and asked.

**A CORRECTION PRINTED AFTER THE ALARM IS READ TOO LATE.** The note
comes first now.

**And it states the verdict rather than the caveat**, which is the
more interesting half. The first version said only that the
requirement *could not be checked* - true, and it leaves an
unresolved alarm below it with no answer. But the `.ado` knows the
floor and can read `equipop.__version__`, so it can simply do the
comparison: it calls the engine's own `_lines_floor` and prints `needs
engine : 1.48.0 or newer - satisfied`, then says which of the two
statements to believe. One source for the wording, so it cannot drift
from what a current engine prints - 332's point, finally reached from
the door that could not reach it.

**TWO TEST LESSONS, both from break-check:**

- **The test asserts the ORDER, not the presence.** "The note exists"
  was true of the version he complained about. Where position is the
  property, position is what the test has to read - the same lesson
  as 1.54.2's finding 4, where an AST check proved a scheme guard was
  present and said nothing about it running first.
- **A substring is not a dependency.** `"_lines_floor" in src` also
  matches `_lines_floor = lambda a, b: []`, and break-check got
  exactly that stub past the first version of the one-source
  assertion. It reads the `ImportFrom` by AST now.

**AND ONE THING THAT WAS MINE AND NOT THE CODE'S.** He asked how he
had gone wrong because my 1.54.4 release note told him what to do
with the wheel *for PyPI* - `twine upload` - and never said how to get
it onto his own machine before it is uploaded. INSTALL.md has carried
that command since 1.47 (section 2, the `shell ... pip install ...
.whl` line); the release note never pointed there. **A document being
correct is not the same as a reader being able to find it.**

## 0o. 1.54.4 - SIX RELEASES OF A FLOOR CHECK THAT NEVER RAN

John sent a doctor report that worked, with "see if you find
something". It said:

```
  engine       : 1.54.2   (the Python package)
  commands     : 1.54.3   (the .ado files)

  THE ENGINE IS OLDER THAN THE COMMANDS, and that combination does break:
```

**The floor those commands declare is 1.48.0, and 1.54.2 satisfies
it.** The correct line is `needs engine : 1.48.0 or newer -
satisfied`. Nothing was wrong with his install.

**THE CAUSE.** `report()` takes `min_engine`. **`run()` did not.** The
`.ado` calls `run()`. So `run(ado_version=..., min_engine=...)` raised
`TypeError` on every doctor run since BACKLOG 332 landed, the ado's
fallback re-ran without the floor, and the report judged by comparing
two RELEASE NUMBERS - which is precisely what 332 exists to prevent.
Its docstring in `doctor.py` reads:

> The loud message belongs to the second and now goes only there.

It never went only there. **Six releases.** Built, documented at
length, tested through `report()` directly, and unreachable from the
only door that passes the argument.

**HIDDEN BY A BROAD EXCEPT, whose own comment said what it was for:**
"min_engine is newer than the argument list of every engine before
1.49.3". A blanket `except TypeError` around a call cannot tell a
missing parameter from a `TypeError` raised deep inside the report,
and it degraded in silence either way. The ado now ASKS
`inspect.signature(run)` and, when the answer is no, prints that the
floor went unchecked. **A silent degrade was the problem, not the old
engine.**

**AND I HAD ALREADY WRITTEN THE TEST THAT CATCHES THIS.** Section 0k
above describes `test_every_door_calls_the_advisory_with_arguments_it_accepts`
- it binds every call site's keywords against the live signature, and
its docstring explains exactly why: *"a call inside `except
Exception: pass` would fail SILENTLY at every run, forever."* I
pointed it at three doors and not at the `doctor` and `setup` calls
**in the same file**. It is now general over every engine function the
block calls by keyword.

**That is the sixth instance of one pattern in this session** - 353,
368, 373, 380, 388, this - and the first found by a user rather than
by a review or a break-check. The generalisable rule: **when a test
is written because a construct can hide failure, apply it to every
instance of that construct, not to the one that prompted it.**

**THE HELP REWRITE IS SMALLER AND WORTH NOTING TOO.** John: the
`unit(#)` entry "doesn't indicate how to ask the data (i.e. run and
rerun with information described in output)". He was right, and the
defect has a name: it stated that the advisory EXISTS and never said
how to see it. **A fact where an instruction was needed** - it read
as documentation of a feature rather than advice to somebody with a
dataset and no idea what to type. It now names the loop, with the
Stata command in the `STATA_EXTRA` half because the same paragraph is
read in QGIS and Pro where there is nothing to type. A blank line in
shared help text now becomes its own `{phang2}` block instead of
rendering flush-left outside the option's indent.

(The `the unit-size hows` mangling in his paste is a copy artifact,
not a defect: the shipped file has "report shows", and `unit(#)` at
433 characters is one of the SHORTER option lines - `overshoot` is
1,455 and renders fine.)

## 0n. 1.54.3 - A WORTHLESS TEST, FOUND BY ONE LINE OF JOHN'S CONSOLE

He sent two things in one message: the doctor's clean verdict, and

```
. equipop help
unknown subcommand: help
  equipop doctor  - report on the Python this Stata is using
  equipop setup   - install or update the calculating engine
```

**`equipop help` was never a subcommand**, because Stata's convention
is `help equipop`. That is true, and it is also not what anybody types
the moment a subcommand has just been refused. One line of dispatch
fixes the worst-timed error message in the program.

**THE PART TO LEARN FROM IS THE LIST ABOVE IT.** Two subcommands out
of three. I added `equipop unit` to that block in 1.54.0 and wrote
this assertion:

```python
assert "equipop unit" in text
```

over the whole `.ado` - which matches the DISPATCH BRANCH. The help
line could have been deleted and the test would still have passed.
**John's paste is a list missing an entry, and my test for that list
could not have told me.** (His output is from a pre-1.54 install, so
the line was not actually missing - but nothing in the suite was
checking.)

The list is now **derived from the dispatch** and scoped to the
unknown-subcommand block, so a fourth subcommand is covered the day it
is written.

**AND BREAK-CHECK FOUND A THIRD PLACE THE SAME OMISSION CAN LIVE.**
Deleting `equipop help` from the generated help section changed
nothing, because the derived test reads only the `.ado`. A companion
test now requires every dispatched subcommand to appear in
`help equipop` too. Three places - the dispatch, the
unknown-subcommand list, the help file - and one derivation covering
all three.

**The capture matters as much as the branch.** A partial install (the
`.ado` files present, `equipop.sthlp` missing) makes Stata answer
"help for equipop not found", which reads as though the command itself
is absent. Captured, the message names the real cause and gives the
same reinstall lines the unknown-subcommand branch prints.

**THE DOCTOR'S VERDICT GAINED TWO LINES**, and the pair he sent is the
argument for them: a user told `machine 1 can run in this Python.` has
nowhere obvious to go next, and `machine 1` is this project's
vocabulary rather than a Stata user's. It now says what machine 1 is
and names `help equipop` and `equipop unit` - printed ONLY when there
is nothing to fix, so it never competes with a real diagnosis, which a
test asserts in both directions.

**WHAT THIS RELEASE IS REALLY ABOUT.** Three reviews found defects in
the code. This one came from a user typing a word, and it exposed a
test that was shaped like a guard and guarded nothing. A `foo in text`
assertion over a whole file is the weakest form in this codebase and
it keeps reappearing - the 1.48.2 ensurepip test, the "changes
nothing" source grep in 1.54.0, this. **If a test's subject is a
specific block of output, the test has to be scoped to that block.**

## 0m. 1.54.2 - A TWO-WORD MISTAKE, AND WHY NOTHING CAUGHT IT

A second, deeper review. The blocker is the smallest defect in this
whole session and had the largest user-facing effect.

**`help equipop` WAS 746 LINES OF ONE CHARACTER EACH.**

`_wrap()` returns ONE STRING of joined lines. Every other call site in
`make_sthlp.py` does `add(_wrap(...))`. Mine was:

```python
for line in _wrap(HELP["unitadvice"]):
    add(line)
```

Iterating a string yields characters. 816 of the generated file's
1,103 lines were one character or blank, and `help equipop` was
unreadable from the unit-advice paragraph onward - **in both the SSC
submission and the net-install archive**, through two releases.

**THE FOUR REASONS NOTHING CAUGHT IT ARE THE USEFUL PART:**

1. **`make_sthlp.py --check` compares the malformed output against the
   malformed generator** and reports the file current. A currency
   check is structurally incapable of finding a defect in the
   generator. It said `stata/equipop.sthlp is current` the whole time.
2. **`test_the_help_file_holds_no_broken_smcl` counts braces per
   line**, and a line holding one letter has none. A test can be
   correct, passing, and about a different property.
3. **Every word of the paragraph is present, in order.** So any grep
   for its content succeeds.
4. **And I grepped it.** I ran `grep -n "equipop unit"` and
   `grep -n "r(advice)"`, saw the strings, and concluded the file was
   fine. The generator printed `wrote ... (1103 lines)` to me twice
   and I had no correct version to compare against - it is 385 lines
   now.

**The test that catches it is about PROSE, not content.** For every
paragraph the generator takes from `HELP` by name, the
whitespace-normalised text must appear in the whitespace-normalised
output: "What" split one letter per line normalises to `W h a t` and
does not match. General over every HELP entry, not just the one that
broke, plus a direct shape assertion - no run of more than three
one-character lines.

**WRITING THE OTHER HELP TESTS FOUND THREE MORE GAPS IN THE SAME
BLOCK**, which is the argument for writing them at all:

- `r(applies)` was returned by the ado and documented nowhere. It
  exists *solely* to distinguish two reasons `r(unit)` is missing, so
  undocumented it is useless for its only job.
- `candidates()`, `tolerance()` and `nocache` appeared in the syntax
  line and were explained nowhere - the options section is built from
  `OPTION_HELP`, which is the RUN's option list, so a subcommand-only
  option had no route into it and no test noticed.
- `r(cmd)` and `r(cmdline)`, found the moment the strongest test was
  written. **That test derives the documented `r()` names from the
  ado's own return statements, in both directions**, so a result added
  and not documented now fails. It is the only arrangement here that
  cannot go stale.

**FINDING 2: HALF OF 1.54.1'S TEST-ISOLATION FIX WAS A FIX.** 393 made
rasterio's *declared* requirements a recorded fixture. `_absent()`
still forced only the named packages absent and passed every other
lookup to the live environment - so the answer still depended on what
happened to be installed. The fixture declares `click-plugins`; on a
machine without it the doctor correctly reported FOUR missing
dependencies where the test expected three. **The same class of error,
inside the fix for that class of error, one release later.**

And my first guard for it was unreachable: I had `_absent` RAISE on an
unknown name, but `_missing_requirements` wraps that call in
`except Exception` and treats any failure as "absent" - correct for
the doctor, and it meant the guard was swallowed exactly where it
mattered. It records now, and an autouse fixture turns the record into
a failure after the test, where nothing can catch it.

**FINDING 3: A FRACTIONAL `k` WAS SILENTLY TRUNCATED.**
`k_values=[100.9]` came back as advice labelled k=100. The project's
own door reader refuses a non-whole k because k counts PEOPLE - and
the new public function undid that rule while its comment claimed to
validate what the engine would refuse. `100.0` is accepted, `100.9`
refused, and a bool is no longer read as k=1.

**FINDING 4: AN AST TEST CANNOT PROVE ORDERING.** H1's scheme check
sat inside `fetch()`'s download branch, below the cache lookup - so a
forbidden URL whose basename was already cached returned
`[fetch] cached`. My test asserted over the AST that every function
containing `urlopen` also contains `_check_scheme`, which proves
PRESENCE and says nothing about POSITION. **Where ordering is the
property, the test has to execute the path.** That applies to several
tests written in this session.

**FINDING 5: THE CACHE VALIDATED THE QUESTION AND NOT THE ANSWER.**
The request key covers fingerprint, k, tolerance, ladder and rule, and
says nothing about the stored result - so editing `recommended` to
999999, a cell count to -42 or a share to 7.5 was accepted. The worst
case is `applies` flipped against the origin rule, which delivers the
1.54.1 exclude defect straight out of a cache. And the 1.54.1 note was
wrong to imply tamper-resistance: anybody who can edit a dataset
characteristic can recompute whatever we store beside it. The fix
widens the protection (a coherence check) and narrows the claim (to
corruption and version-skew detection).

**THE BREAK-CHECK LESSON THIS ROUND: MUTUAL SUBSUMPTION.** Six breaks
survived the first pass and only two were real test gaps. The other
four were overlapping checks - flipping `applies` also broke the per-k
shape; a recommendation of 999999 was also off the ladder; a cell
count of -42 also broke `0 <= sat <= cells` - so **each break was
caught by a different check and none of those checks was
independently tested.** The responses differ by case and both matter:
the genuinely implied check was *removed* (a recommendation that
follows from the shares is on the ladder by construction), and the
rest got test cases built to fail exactly one check each. Two of those
needed new fixture data, because the original data never entered the
branch at all.

## 0l. 1.54.1 - THE REVIEW FOUND ME COMMITTING THE SESSION'S OWN LESSON

An external review of 1.54.0 recommended holding the release. It was
right, and the first finding is the one to read twice.

**F1. `originrule(exclude)` WAS SHOWN INCLUDE-RULE ADVICE - AND I HAD
WRITTEN DOWN WHY THAT WAS WRONG BEFORE SHIPPING IT.**

`advise_unit` took `self_rule` and used it as a LABEL. The numbers
were computed identically under either rule; the report announced
"Assumes originrule(exclude)" over include-rule counts, and a footnote
below said those counts do not apply. All three ordinary-run doors
pass the user's real rule in, so an exclude run was told *100.0% of
people are in a cell that already holds k* - and handed a
recommendation derived from it.

The module docstring I wrote for 385 says the criterion **"IS ONLY
TRUE UNDER THE `include` ORIGIN RULE"**. `tests/test_unitsize.py`
ASSERTED that the engine differs under exclude. The knowledge was
written down, tested, and then not used by the code path.

**That is 353, 368, 373 and 380 - and section 0k above is about
exactly that pattern.** I wrote a handover section on "the thing was
built, it was correct, and the path could not reach it", and shipped
an instance of it in the same release. Writing the lesson down is not
the same as applying it. The only defence that worked here was someone
else reading the code.

**AND THE MEASUREMENT WAS STRONGER THAN THE REVIEW.** Not "unreliable
under exclude": `fastcounts` drops the origin's **whole cell**
(`keep = idx != oi_range`, line 164), so the saturated count is
**structurally zero**. Four shapes, including one where a single cell
holds every person at k=1000 - include reports 1, exclude reports 0.
The advisory was predicting something that cannot happen.

**I then guessed at a correct exclude criterion and the measurement
said no.** The guess: under exclude a huge neighbouring cell would
serve every k, so `Dist_k` would stop varying. Measured, with a
10,000-person cell 100 m away: `Dist_k` came back **57.02, 62.17,
81.19** for k=100, 1000, 5000, because the engine spreads a cell's
population across its area. So k keeps its meaning under exclude at
every cell size, and there is nothing to warn about - which is good
news, and is now stated as such rather than as a missing feature.

The fix makes the rule decide whether the criterion applies at all.
Under exclude the per-k fields are **None, not 0** - a zero reads as a
measurement, and the next step is to pick the coarsest size on the
strength of it - the columns are not printed, nothing is recommended,
and the reason is given. The cost and resolution-floor columns stay,
because they are about the grid and hold under either rule.

**F2. THE CACHE ANSWERED A DIFFERENT QUESTION AND REPORTED A HIT**,
and my own test is why nobody noticed. `unpack_advice` validated the
version, fingerprint, k values and tolerance - not the candidate
ladder, not the origin rule. Advice cached for candidates 25 and 50
under include came back to a request for 1,000 and 5,000 under
exclude, labelled "read from this dataset's stored advice". The
release note said *"every way of being stale returns a miss"*; the
test called `test_a_stale_cache_misses_rather_than_lying` checked
three of the five components **and called that every**. A test named
after a property it only partly checks is worse than no test, because
it answers the question for the next reader.

**My first fix for it was also wrong**, and worth recording: I added
`candidates` and `self_rule` as optional keyword arguments. An
optional check is one a caller can forget - the same defect by a
different route. The request is now ONE key, `unpack_advice` requires
it positionally, and omitting it raises TypeError.

**F3. A WARNING BUILT AND THEN DISCARDED.** Three branches of
`advise_on_run` returned a fresh `[]` after the degree note had been
appended to `out`. And those are the branches where it matters most:
they are the quiet ones, so the note was not competing with other
output - it was the only output there would have been.

**F4. A PUBLIC FUNCTION ACCEPTING WHAT THE ENGINE REFUSES.** Negative
population (weights `[10, -9]` gave a `share_people` of **1,000%**,
then compared against the tolerance to choose a size), a zero total, a
tolerance of 5.0 (under which every candidate passes, so the coarsest
is always recommended), and - found while checking - `float("inf") > 0`
is **True**, so inf passed the candidate filter and produced a row at
an infinite cell size. Zero, negative and nan were already filtered,
which is why that one survived review by eye.

**F6 IS THE ONE THAT CHANGES HOW TO REPORT A RELEASE.** Three doctor
tests made `cligj` absent and expected the doctor to name it, which
works only while rasterio *declares* cligj. Rasterio 1.5.2 does not;
mine is 1.4.4. So three tests failed for the reviewer and passed for
me, and **"1,588 tests pass" was a fact about my rasterio, reported as
a fact about the release.** The requirement list is now a recorded
fixture - the real strings from John's machine - and verified by
simulating the reviewer's environment: all 37 doctor tests pass with
cligj, attrs, pyparsing and click-plugins dropped, and under that
simulation the live-metadata scan returns `[]`, confirming the old
assertion failed on a defect that was not there.

**A test count is an environment measurement, not a property of a
release. Say which environment, or do not say the number.**

**H1 turned out to matter more than the scanner thought.**
`usedforsecurity=False` is the honest declaration for md5 used as
cache identity - and it is functional: on a FIPS-enabled host
`hashlib.md5()` **raises**, so `cells.fingerprint()`, the tile
manifests and the unit-size cache key would crash on an institutional
partner's machine. Checked first that the digest VALUE is unchanged,
because `bigrun` verifies stored tile checksums on every read and a
different digest would make every existing tiled run unreadable.

**WHAT TO TAKE FROM THIS SESSION.** Four of the six confirmed findings
were in code written the same day, by someone who had just finished
documenting the defect pattern they belong to. The break-checks were
thorough and caught 47 breaks across two passes; none of them caught
F1, because a break-check tests what the tests assert, and my tests
asserted the limitation in prose while the code ignored it. **An
external reader is not a formality.**

## 0k. 1.54.0 - THE ANSWER WAS ALREADY IN THE BACKLOG

John, 9 October 2026: *"in all machines we assume that the unit size
of grid should be 100 ... is there a cheap way to determine the
average nearest neighbour or similar - that would enable us to
recommend a unit size? ... knowing the unit size is a battle between
computing time and detail."*

**THE FIRST THING TO GET RIGHT WAS THE CRITERION, AND IT IS NOT
NEAREST-NEIGHBOUR SPACING.** Average spacing tells you when cells
start being EMPTY. It does not tell you when the answer stops being an
answer - and there is a precise threshold for that, which this
project wrote down years ago in BACKLOG 95:

> once a cell holds >= k people the whole neighbourhood IS the origin
> cell, so the radius is not zero - it is unmeasured, and **k has
> stopped being a parameter**

Beyond that point `Dist_k` comes from `selfpot.radius_for_k` instead
of from the data, and k=200 and k=2000 return the same number. The
engine has reported this AFTER every run since 1.29.5. 1.54.0 reports
the same number BEFORE one, across a ladder of candidate sizes.

**So the useful lesson is about reading the backlog, not about grids.**
The question arrived as an open research problem and most of the
answer was already written down under a different heading. The work
was recognising it.

**MEASURED AGAINST THE ENGINE, NOT DERIVED ON PAPER.** The whole
advisory rests on one claim: the count of cells whose own population
reaches k equals the figure `fastcounts` prints as self-potential
origins. `tests/test_unitsize.py` checks it by RUNNING the real engine
and regex-parsing its own message - on one dense cell among sparse
ones, four cells at four densities, and population as a WEIGHT rather
than a row count, with the boundary values of k in each. This is
1.53.4's lesson applied immediately: an identity test between two
expressions of the same idea proves consistency and nothing about
correctness.

It is also **only true under `originrule(include)`**. Measured: under
`exclude` the advisory predicts 1 and the engine reports 0, because
the origin's own mass is removed before the search, so its own cell
cannot saturate it. The report names the rule it assumed.

**TWO THINGS THE OBVIOUS IMPLEMENTATION GETS WRONG**, both found by
break-check rather than by thinking:

- **`>= k - 1e-9` is load-bearing for a SECOND reason.** I wrote the
  slack to match the engine's guard, and documented BACKLOG 304's
  reason for it - `proportional` overshoot making the crossing cell
  sum to 99.99999999999999. Then a break of `>= k` with no slack
  SURVIVED the suite, which meant my tests never exercised it. They
  used whole weights. A WorldPop pixel carries a **fractional**
  population, so a cell total is an accumulated float sum: measured,
  1,000 pixels of 0.1 come to 99.9999999999986, short by 1.4e-12.
  Without the slack the advisory reports 0 saturated cells where the
  engine reports 1 - **on exactly the data EquiPop is usually pointed
  at**. The comment in the module now gives both reasons.
- **The grid key's multiplier has to be MEASURED.** Two int64 indices
  are paired into one 1-D key so the group-by is a single pass. A
  fixed multiplier wraps, and not in a corner case: on a 120 km by
  300 m strip - an ordinary study extent - a multiplier of 1000 turns
  1,201 cells into 1,200, makes the largest population read 2.0 where
  every real cell holds 1.0, and takes k=2 from 0 saturated cells to
  1. A recommendation off the back of a hash collision. The test uses
  `build_cells` as the answer key, because it grids by pandas
  group-by and pairs nothing - a different implementation of the same
  question.

**NO SINGLE NUMBER, AND NO DEFAULT MOVES.** John's own objection is
the reason for the first: density is heterogeneous, so one unit
cannot be right everywhere, and a single figure would hide exactly
the variation that makes the question hard. The second is BACKLOG
116's rule - reported, never substituted. If EquiPop chose the cell
size, two runs on the same data could silently use different ones and
a published figure would depend on a heuristic that might change
between versions. Every report ends `NOTHING IS CHANGED BY THIS`.

**THE CACHE JOHN ASKED ABOUT, AND THE MEASUREMENT BEFORE BUILDING
IT.** `advise_unit` costs 0.07 s on 100,000 rows, 0.84 s on a million,
16 s on ten million. `np.add.at` is already the fastest of three
groupings tried - `bincount` and `argsort`+`reduceat` are both slower
at 10M - so the 16 s is nine inherent linear passes and there is no
implementation win to find. The fingerprint that validates a cache
costs 0.55 s, so the cache earns its place on big data and is
pointless on small, which is where John's instinct put it. It lives
in `char _dta[equipop_unitsize]`: travels with the data, survives
`save`, dies with `clear` - the right lifetime for a fact about this
dataset. **Keyed on a digest of the COORDINATES**, because a path or a
row count is BACKLOG 344, where a resumed run returned the first
run's numbers since counting rows could not tell two tables apart.

**IT RUNS ON EVERY MACHINE-1 RUN BECAUSE IT IS FREE, AND IT IS
USUALLY SILENT.** Measured against a real run on the same data: the
advisory is **0.3%** of `build_cells` plus the kNN search, at both
20,000 and 60,000 individuals, and the ratio holds because the
advisory is linear while the run builds a tree and searches it. It
speaks when no `unit()` was given and a different size would do, or
when one was given and it saturates - quoting the user's own number.
Otherwise nothing, because a note printed after every run is noise
and noise is how a real warning gets missed.

**`Unit(real 100)` HAD TO GO, AND THAT IS THE ONE BEHAVIOURAL
CHANGE.** It delivers 100 both when the user typed `unit(100)` and
when they said nothing, so the advisory could not tell a choice from
a default and would have nagged everybody or nobody. The option is
read as a string and defaulted in the body, where the fact can be
recorded. `r(unit)` is unchanged.

**THE TEST THIS RELEASE IS ACTUALLY ABOUT.** Every door calls the
advisory inside `except Exception: pass`. That is right - the output
is already written by then and an advisory must never turn a finished
run into an error - and it is **a machine for hiding a mistake
forever**: one mistyped keyword and no door ever prints anything, no
test fails, and nobody finds out. Which is 353, 368, 373 and 380, the
four releases before this one.

So `tests/test_unitsize_doors.py` **binds every call site's keywords
against the live signature** with `inspect.signature().bind()`, and
checks that **both** of Pro's two exits (the early return for a table
output, and the end of the feature-class path) pass through the
advisory. Break-check confirmed it: a keyword typo in any one of the
three doors is caught, and so is dropping the call from either Pro
exit.

**THREE EXISTING GUARDS FIRED ON THIS WORK, AND ONE OF THEM WAS
WRONG ABOUT ITSELF.**

- `test_no_ado_hands_none_to_stata` matched every `.store()` by method
  name, so a legitimate `Matrix.store(name, values)` tripped a rule
  about `Data.store(var, obs, values)`. Fixed by dispatching on the
  OBJECT with a per-object shape, rather than narrowing by name -
  which would have let an unknown third `store` through in silence.
- `test_setup_uses_only_the_standard_library` sliced the file from
  `def _equipop_setup_py` to `def _equipop_doctor_py`. A third
  function landed between them and the test silently changed what it
  was about - it began reading `from equipop import unitsize` out of
  a function with nothing to do with installing. **It failed loudly,
  which was luck**: the slice could as easily have grown to include
  something that satisfied every assertion, and the guard would have
  gone quiet. Four tests shared the idiom; all four now take the
  function's own source by AST.
- `test_4_every_module_is_either_a_capability_or_declared_internal`
  caught `unitsize` as undeclared - the fifth new module it has
  stopped, after inventory, vectorjoin, doors.numbers and labels.
  **Its message was not true of its own code**: it offered "either as
  a capability with its doors, or to INTERNAL as machinery", but the
  check reads INTERNAL alone, so a module given a MATRIX row and left
  out of INTERNAL still failed - with a message telling the author
  they had already done enough. The wording was corrected rather than
  the check loosened.

**ONE GAP MY OWN TEST HAD, worth recording because it passed for the
wrong reason.** I asserted that a cache at the wrong version misses,
with `unpack_advice('{"v":0,"a":{}}') is None`. Break-check deleted
the version check and the assertion still passed - because the empty
dict failed the STRUCTURE check instead. The version check was not
covered at all. It now uses a structurally perfect payload with only
the version changed, plus the same payload at the current version to
prove the assertion is about the version and nothing else. **A stale
cache is dangerous precisely when it looks valid.**

**WHAT IS STILL MISSING: 386.** The advisory has a standalone door in
Stata (`equipop unit`) and in Python (`equipop.advise_unit`). At both
GIS doors it arrives ONLY attached to a finished run - so a GIS user
must pay for the expensive run, at the size they were unsure about, to
get an answer that costs 0.07 s. Recorded rather than built, because
the dialog wording is John's call.

## 0j. 1.53.4 - TWO RULINGS, AND A CAPABILITY THAT WAS SMALL

The first release of this session built from John's rulings rather
than from a defect. **365 had been at the head of the exposome arc for
four releases and the warning not to promise it is now retired.**

**365 - MEASURE FIRST, AND THE MEASUREMENT CHANGED THE JOB.** The
backlog entry said "the tiles already carry both, so a post-pass over
load_tiled() may be most of it. Worth measuring before promising."
Measured: a tiled machine-3 run with `groups=["num","den"]` writes
`T_num_k` AND `T_den_k` into every tile - 9 tiles, both halves in all
of them - and a demographic index is nothing but their ratio per
origin. So this was never an engine; it is a **per-tile post-pass with
memory bounded at one tile**, which is the whole point of tiling. A
continental dependency ratio runs on a laptop.

`bigrun.map_tiles` is the primitive, and **two of its three decisions
are the ones that would have been got wrong by writing it the obvious
way:**

- **The manifest is written PER TILE, not at the end.**
  `load_tiled(verify=True)` checks every md5, so a pass that rewrote
  all the tiles and then wrote one manifest would, if killed, leave a
  finished continental run in which **every tile fails its
  checksum** - days of compute unreadable because a post-pass was
  interrupted. Tested by raising on the second tile.
- **The md5 is verified BEFORE the read.** A rewrite computes a fresh
  checksum, so a post-pass over an already-corrupt tile would launder
  the corruption into a manifest that agrees with it from then on, and
  the guard would never fire again. The one chance to notice is before
  the read. Tested by corrupting four bytes.
- And the new column honours the manifest's declared dtype. The first
  version did not - counts float32 as declared, index float64, because
  `np.where` on float64 returns float64 - which made the manifest a
  lie about its own tiles.

**THE COUNT WAS NOTICED BEFORE THE CODE WAS WRITTEN, for once.**
`run_index` and `run_indices` each built the column names and the
ratio inline, so there were already **two** copies, and giving each a
tiled branch would have made **four**. One `index_triples` and one
`apply_index` instead, so the in-memory and tiled branches agree by
construction. That is 354, 368 and 377 not happening a fourth time,
and the only reason is that the arithmetic was counted first.

**The difference from an in-memory run is float32 tile storage and
nothing else**, measured: the tiled index is
`float32(float32(T_num)/float32(T_den))`, bit-identical to
recomputing it that way from the in-memory counts, max relative
difference 1.3e-07 over 1,980 origins. Machine 3 has stored float32
since it was written and its manifest declares it.

**363 - THE RULING HAD A TRAP IN IT.** John: *"fold into 90+ - but
note to user in output if found in the run."* Taken literally, a
fold into every side would put centenarians among the under-fives: a
folder's `f_95` belongs in an ageing index's numerator, which is 65
and over and open-ended, and not in a children's. **The fold reaches
only a side that actually wants the top band** - and that is a wrong
answer no message would have mentioned, because the note would have
been busy reporting that the fold had happened.

And the note moved to where both sides are known. 362 wired it to the
numerator alone, reasoning correctly that the note is about the
FOLDER. The ruling turned the hole that left from cosmetic into
substantive: all four built-in indices carry the open-ended side on
top, but the specs are user-overridable, so an index whose
**denominator** reached the top band folded cohorts into it and said
nothing. `above_top_note` is asked once, with both specs.

**WHAT THE NOTE HAS TO SAY.** Folding is right and it still changes
what 90+ MEANS in a published figure - it becomes the folder's own
top, open above 100 rather than above 90 - and a reader comparing two
studies can only learn that from the run's own output.

**THE BREAK-CHECK FOUND A REAL WEAKNESS IN MY TEST DESIGN, and it is
the most useful thing in this section.** Changing `/ b` to
`/ (b + 1e-9)` in `apply_index` passed the entire suite. My identity
test compares the tiled branch against the in-memory one - and **both
call the same function, so a break moves both together and they still
agree.** An identity test between two users of one function proves the
function is used consistently and proves *nothing* about whether it is
right. The fix is an **answer key computed outside the code**: 30/120
= 0.25, 75/150 = 0.5, 9/4 = 2.25, by hand. Two more gaps came out of
the same pass: a zero denominator silently becoming 0.0 rather than
missing (a dependency ratio of 0.0 reads as "no dependants here",
which is a finding, when the truth is there was nobody to count), and
the progressive manifest write being removable unnoticed.

13 breaks, all caught, "never failed under any break: none".

**Two tests from earlier releases were AMENDED, not fixed**, because
their premises were what the rulings changed: 362's test asserted the
cohorts were excluded and now asserts they are folded; 364's asserted
a tiled run is refused and now asserts it works. Both kept their
original property. And removing 364's refusal exposed
`tests/fixtures/worldpop` as too thin - three single-cohort rasters,
which the old test never noticed because its refusal came *before*
`plan()` validated anything. A guard standing in front of a guard.

---

## 0i. 1.53.3 - THE CONVENTION THAT COULD NOT BE REACHED

John, ArcGIS Pro: `ValueError: cannot create NumPyArray. geometry type
found`, from a layer holding null geometry. **Read this section for one
thing: the handling already existed, forty lines below the call that
died, in the same function.**

```python
# arcgis/EquiPop.pyt, inside _read_input
arr = arcpy.da.FeatureClassToNumPyArray(...)   # <- dies here
...                                            # 40 lines
n_missing = int((~(np.isfinite(x) & np.isfinite(y))).sum())
if n_missing:
    messages.addMessage(f"{n_missing} rows with missing coordinates"
                        " -> Null results (EquiPop convention).")
```

`skip_nulls=False, null_value=np.nan` was passed **deliberately** so
those rows would survive as NaN and land there. The QGIS door does the
same by hand and gets it right. So the convention was implemented in
the engine, **named in its own message**, honoured by one GUI, and
unreachable from the other — for as long as both doors have existed.

**Fourth release in a row of that shape.** 353 a guard unreachable
from the path that could trip it; 368 a hint classified and never
rendered; 373 a parse fixed downstream of the parse that breaks; 380
a convention announced by the function that cannot reach it. If a
fresh session takes one habit from this file, take this one: **when
something is already handled, check that the path can get there.**

**AND MY FIRST FIX WAS INCOMPLETE, WHICH IS THE OTHER HALF.** I fixed
`_read_input` and wrote a regression test scoped to `_read_input`. A
subagent audit of the property across the whole codebase found the
*same* defect at two more call sites — the barrier table and the
barrier point layer — each with a correct `isfinite` mask three or
four lines below a fast read that dies first. My test could not have
caught either. 1.53.2 found seven copies of a k parser the same way.
**The scan is module-wide now and allows by PROPERTY, not by name**: a
direct read is fine if it sits inside a `try` (the caller degrades) or
reads an OBJECTID only. My first draft listed function names and every
one was a guess the test then corrected — and a name list goes stale
on a rename, which is how the reachability matrix went wrong in 333.

**John's workaround is worth understanding, because it is not the same
answer.** He selected the non-null features, which runs — but those
rows then *vanish* from the output instead of being present-and-Null.
For scenario comparison, present-and-Null is the one that matters: two
runs stay row-aligned, so a difference is a difference in the answer
rather than a change of denominator. It is `keep_zero` from 1.53.0 one
layer up, and it is the same property the machine 7 proposal needs.

**TWO SIMULATOR FAULTS, AND BOTH MATTERED.** The QGIS stub built a
point from NaN ordinates instead of an empty geometry — so every test
that believed it was exercising null geometry was exercising a point
at NaN, and the reader's `g.isEmpty()` branch **had never been run by
anything**. And the sink could not read back an output feature with no
geometry, which is exactly what the convention writes. *A simulator
that cannot produce the input cannot test the handling* — the
counterpart to this file's existing rule about suspecting the
simulator when a door looks broken.

**The test guarding the CORRECT door was watching its text.** My first
version asserted `re.search(r"g is None or g\.isEmpty\(\)")` against
the QGIS source, and a break that kept the condition while turning
`xs.append(np.nan)` into `continue` sailed straight past. 370's
finding again. Behavioural now, through the real reader, plus a test
that **the two GUIs give the same answer for the same unlocatable
row** — which is the more useful claim than either door being
defensible alone.

**THREE SMALLER FINDINGS FROM THE AUDIT**, all the same family: the
answer was right and somebody else's error message was speaking for
EquiPop. `cells.py` and the Stata counts path tested coordinates with
`.isna()`/`.notna()` where they meant `isfinite`, so an infinite
coordinate reached an `.astype(int)` and came back as a pandas
sentence about dtypes (381). `run_knn_stats` had 150 lines of
validation and nothing about whether a cell has a *position*, so the
Python API could get "[stats] 3 cells" followed by a bare numpy
message — while `fastcounts` was already strict **by accident**,
because scipy refuses non-finite input (382). And both GUIs dropped
null-geometry features *above* the mask that counts dropped features,
so the warning undercounted and the number could not be reconciled
with the user's layer (383).

**I CORRECTED THE AUDIT ON ONE POINT AND IT MATTERS.** I first
recorded 381 as a silent wrong answer, because raw numpy turns `inf`
into INT64_MIN — a cell 9.2e18 m away. Measured, the pandas path these
two actually take *raises*. Nothing was silently wrong. The audit
over-claimed and the measurement corrected it; a subagent's report is
evidence to check, not a finding to file.

**And I killed my own break-check with `| head` — again.** SIGPIPE,
the final `restore()` never ran, and a break was left applied in the
tree. **That is BACKLOG 352, recorded forty screens up in this same
file, in this same session.** Knowing a hazard and writing it down did
not stop me reaching for the same shortcut on a different script. The
rule, now stated rather than remembered: **a script that mutates the
tree is never piped** — redirect to a file and read the file.

15 breaks, all caught, "never failed under any break: none".

---

## 0h. 1.53.2 - SEVEN WAYS TO READ ONE BOX

John, in ArcGIS Pro: `ValueError: give k_values and/or r_values`, then
*"any idea?"*. Six defects behind it, one shipping since 1.35, and the
release that fixed them found two more copies of the central one than
I had counted.

**THE DIAGNOSIS, IN THE ORDER IT UNFOLDED.** His k box held something
Pro called valid and the engine called nothing: a space, a semicolon,
a tab. **Pro's `Required` asks whether a box holds A VALUE, and a
space is a value.** The dialog's own guard - BACKLOG 305, added
eighteen months earlier *after he hit this same engine refusal while
teaching* - read `if not _txt(pm, "k")`, which a space walks straight
past. And it existed in **one door of the four** that reach that
refusal; machine 2 had no version of it at all.

Then, looking for why, the worse one. **`1,000` in a k box meant ONE
PERSON and the run finished.**

```
k typed '1,000'  -> k = 1     writes Mean_income_1
k typed '1.000'  -> k = 1
k typed '10,000' -> k = 10
```

No refusal, no warning, columns written. The only evidence is
`Mean_income_1` where `Mean_income_1000` belonged, which reads as
plausible unless you are looking for it. **A wrong answer that
completes is worse than the traceback that started the
investigation**, and he found the traceback first by luck. The cause
is a good fix one notch too wide: BACKLOG 320 made both GUIs share
one locale-proof reader, which is right for a *distance* - `500,5`
metres is what a Norwegian keyboard produces - and wrong for a *count
of people*, where `1,000` means one thousand in every notation anybody
types.

**JOHN'S RULING**, 7 October: *"yes - in the next round we should
refuse 1,000 - and good to keep it for radii."* Refusing is the honest
half; interpreting guesses at intent, and the other reading of `1,6`
is one and a half people. So the two readers are now deliberately
different and the docstring says why, because that asymmetry is
exactly what a later tidy-up would collapse.

**SEVEN K READERS.** This is the number to remember.

```
1. doors.numbers.intlist          correct - QGIS counts ONLY
2. .pyt  int(round(_numlist()))   Pro counts and stats
3. alg_stats  [int(v) for v in k_text.split()]
4. alg_continental._numbers       int(float(piece))
5. alg_demography._numbers        a verbatim copy of 4
6. Pro ContinentalRasters.execute int(float(piece))
7. Pro SpatialDemography.execute  a verbatim copy of 6
```

Six of the seven truncated silently - precisely what the one correct
reader exists to refuse, in a module whose docstring says it exists so
this cannot happen, with `to_int` carrying the sentence *"a silently
rounded k is a wrong answer that looks right"* since 1.47. **354 was
four copies of the measurement rule. 368 was two copies of the hint
rendering. This is seven copies of the k rule.** Three releases
running. A shared module being present and documented prevented none
of them.

**I COUNTED FIVE. THE PROPERTY TEST FOUND SEVEN.** Numbers 6 and 7
were in files I had read that morning, and the test written to forbid
a *sixth* copy found a sixth and a seventh on its first run. That is
the argument for property tests in one line: **a per-door test asserts
what its author already knows about; a property test asks the
codebase.**

**AND THE PATTERN NAMED, because it is the third consecutive release.**
BACKLOG 320 exists to stop `could not convert string to float: '500,5'`
reaching a user, and it added a locale-proof parse to `alg_counts` at
line 445. Field-name prediction, at **line 395**, had already touched
the same text with a bare `float()`. So that exact message still
reached users in both QGIS doors, from fifty lines *above* the fix
meant to prevent it. In Pro it was worse: prediction runs inside
`updateMessages`, so a decimal-comma radius **crashed the dialog's
validation callback while the user typed.**

> 353 was a guard unreachable from the path that could trip it.
> 368 was a hint classified and never rendered.
> 373 is a parse fixed downstream of the parse that breaks.
> **All three passed their tests.**

The rule: **when you fix how an input is handled, start at the
earliest point a door touches it, not at the line you happen to be
reading.**

**THREE OF MY OWN TESTS WERE WRONG, and the breaks found them.** This
is the uncomfortable half and the reason the discipline is worth the
time.

- Deleting one line - `NEEDS_A_NEIGHBOURHOOD = True` from alg_stats -
  **reproduced John's exact bug and the entire suite stayed green.**
  My test checked that the shared hook existed and that no door had
  its own copy, and never that a door *declared* it needed a
  neighbourhood. It now runs the real hook with both boxes empty.
- Restoring alg_stats' bare `[int(v) for v in k_text.split()]` broke
  nothing: my ast scan looked for a call *nested inside* `int()`, and
  the bare form passes a plain name.
- One test had never failed under any break, because I never broke the
  file it guards.

Final: **19 breaks, all caught, "never failed under any break: none".**

**Two smaller things worth knowing.** A comma still separates *values*
when it is not between digits - `300, 500` is two k values, machines 3
and 4 have accepted that since they were written, and
`test_qgis_continental` is what caught the shared reader forbidding
it. The fix for one real defect would have removed a real documented
capability, and an existing test is the only reason it did not.

And `test_the_version_bump_survives_a_round_trip` failed on this
release's own comments. The bump tool prints its rule - *"a version in
prose is a FACT ABOUT THE PAST"* - and the test contradicted it, so
writing `BACKLOG 377, v1.53.2` into a comment in `EquiPop.pyt` tripped
a guard on nine comments that are correct and must never move. Now
narrowed to the declaration patterns the tool itself publishes. **Same
mistake as the other two: a test matching TEXT where it meant to match
a KIND of line.**

---

## 0g. 1.53.1 - A QUESTION, NOT A BUG REPORT

John read the new doctor output and asked one thing: *"the message
states that rasteria is broken - is that the way it should be?"* He
was not reporting a defect. He was checking whether a word was too
strong — the same instinct that produced the 1.51.2 work after Baum
called the mismatch message confusing.

**The answer was yes, and that is why this release exists.** `BROKEN`
was correct: `click` really is imported at rasterio package-import
time (`__init__.py:25 → _base.pyx → crs.pyx → errors.py:3`, verified
by blocking click and nothing else), so rasterio genuinely could not
load and every raster path was down. The status was right. **What
followed it was not.** Five findings, all from one question.

**IF YOU READ ONE THING: THE FIRST FAILURE IS THE WRONG UNIT OF
TRUTH.** The doctor said `No module named 'click'`. He installed
click. pip then told him rasterio also wanted `attrs`, `cligj` and
`pyparsing`. **Three exchanges to learn that a whole dependency set
had been wiped**, when the count was the diagnosis all along: one
missing package is an accident, four is an interrupted pip run. The
doctor now reads the library's own declared metadata and names every
missing dependency with one install command (367).

And the thing that EXPLAINED it was on his screen the whole time,
printed five times, reading as noise:

```
WARNING: Ignoring invalid distribution ~yproj
```

`~yproj` is a half-deleted `pyproj` — when pip cannot delete a
directory on Windows it renames it with a `~` prefix and carries on.
So a pip run had been interrupted, which is why four dependencies went
missing together. **One `os.listdir` of site-packages would have found
it.** The doctor exists to explain broken machines and was not looking
in the directory the breakage was sitting in (369). LEFTOVERS now
prints above the libraries — cause before symptom — and is silent on a
clean machine.

**THE WORST ONE, AND THE ONE WITH A LESSON FOR THE SUITE.**
`_describe_failure` has classified `"DLL load failed"` as its own case
since 1.35. `report()` rendered `if tag == "ARCH"` and nothing else.
**Eighteen releases of a case that was classified, tested, and never
printed a single word** — on the platform every user of this project
is on, for the failure most likely to hit rasterio, geopandas and
pyproj. And the rendering was open-coded *twice*, in the REQUIRED loop
and again in OPTIONAL: **354's lesson arriving one release later in a
different file.** A rule written twice is a rule that gets extended
once; this one was extended zero times in two places. `_hint_lines`
is the single renderer now (368).

**The test is the part to carry forward.**
`test_a_windows_dll_failure_is_recognised_separately` asserted
`tag == "DLL"` and passed throughout. It is **not** a test that could
not fail — break the classifier and it fails. It is a test watching
**the wrong half of the mechanism**: the suite knew the tag was
computed and had no opinion about whether a human ever read it. That
is a new entry on this file's own list, and the first that is not
"the test cannot fail": *a test can fail, and still not be watching
the thing that matters.*

Testing tags one at a time is what hid it — a tag with no renderer is
invisible to a per-tag test. So the fix is a **property**:
`test_every_tag_that_can_be_classified_has_something_to_say` scrapes
the tags the classifier can return and asserts each produces output.
A new tag with no hint fails the day it is written (370).

Last, the verdict. His report ended `machine 1 can run in this
Python.` on the line below `rasterio : BROKEN`. **The sentence is
true** — machine 1 needs none of the optional libraries — and it is
the last thing on screen, so it is what a user remembers, and rasters
are most of what he does. The verdict still answers the machine-1
question and then names any optional library that is installed but
broken, with the capability lost. An `absent` library is deliberately
*not* mentioned: that is a choice, not a fault, and a verdict
grumbling about uninstalled libraries is one users learn to skip (371).

**20 breaks applied across `tests/test_doctor.py`, all caught; every
test function in the file fails under at least one, including the
seven that predate this release.** One of my own new tests was wrong
rather than the code — I asserted the advice prose contained the word
"pyproj" when it never had reason to. Second release running where my
expectation, not the suite, was the thing at fault.

**The general lesson, because it is the third time in three releases.**
353 was a guard that could not be reached from the path it named. 368
was a hint that was classified and never rendered. Both passed their
tests. **When you add a case, follow it all the way to the thing a
human sees** — and when a user asks whether a message is right, the
message usually is and what comes after it usually is not.

---

## 0f. 1.53.0 - TWO LINES THAT DECIDED WHAT COUNTS AS DATA

The first release of this session that came from **reading our own
code on purpose**, not from a user's traceback and not from an
outsider's review. John asked for it in those words: *"perhaps we
should devote more time to the demographic machineries and how raster
data is integrated in equipop ... see what are the easiest fruits to
pick, alternatively the best weeds to pick"*. The reason is February:
the Horizon call's exposome claim runs through exactly this code.

Fourteen findings, every one measured before it was called real.
Thirteen fixed, one (365) left open on purpose. Three went to John as
rulings rather than as code, and **two of his three answers changed
what I was going to do.**

**THE WEED WAS TWO LINES, AND IT DEFINED "DATA" WRONGLY.**

```python
arr = np.where(np.isfinite(arr) & (arr != nod), arr, 0.0)
rows, cols = np.nonzero(arr > 0)
```

`arr > 0` is three decisions wearing one mask. It says a pixel is
absent unless it is positive - so **NoData and a real zero became the
same thing**, and **every negative value was thrown away without a
word.** The mask is `observed` now (finite AND not the declared
nodata), `keep_zero` decides only whether an observed zero earns a
row, and negatives are carried as given *and announced*, because
silence is what let the rest of this happen.

What that cost, all measured on real surfaces:

- A temperature-anomaly field with a true mean of **-0.0046 degC came
  back as +1.19 degC** - warming everywhere, every cooling pixel
  silently discarded. A zero-floored PM2.5 surface came back **9.9%
  high.** Population-weighted exposure per group per neighbourhood is
  the first claim an exposome consortium will test, and it ran
  through the one path that could not carry an exposure surface.
- **`keep_zero` was completely dead, both branches.** A pixel zero
  everywhere was never created, so `keep_zero=True` could not bring
  it back; every row that existed was positive, so `keep_zero=False`
  dropped nothing. Documented as working, exposed at the continental
  door, doing nothing in either position since it was written.
- **It made my own guard from two days earlier unreachable.**
  `cells.py` refuses a negative population and says in its own
  comment that it exists because *"rasterfolder hands a raster's own
  column straight in, and a raster's NoData is frequently -9999"*. It
  could never fire on that path: the negatives were gone forty lines
  upstream. **The guard and the hole were in the same package, in the
  same week, by the same hand.** If you write a guard, go and check
  that the path it names can still reach it.

**JOHN'S CORRECTION IS THE ONE TO CARRY FORWARD.** My first
recommendation was to *remove* `keep_zero` as a dead option. He
corrected me: *"if we have an instance where we used to have
populations some years ago, and we want to compare how these places
are doing now - we should have zeros in the deck. Then they add
nothing to reference or treatment but they hold a place for results."*
That is **his own rule from 1.22.2**, which the Stata path has
honoured all along through `_add_empty_origin_cells`; the raster path
had an option advertising it and delivering nothing. `dnk_f_15_2020`
in the project's own fixture carries **1,201 observed zeros**, every
one dropped. The lesson is not "ask before deleting" - it is that a
dead option can be dead because *the feature was never finished*, and
the author of the feature knows which it is. Lean on that.

**TWO GATES, NOT ONE.** The default path is bit-identical - 267,632
rows, total 91254.736115 exactly - asserted against the old two lines
*recomputed from the files*, not against stored numbers. The
break-check then found something worth recording: the identity has
**two independent gates**, `pick` and the `keep_zero` row filter, and
breaking either alone is caught by the other. That is in the test
now, so nobody deletes one as redundant. It also nearly cost the fix:
eight lines downstream, the `keep_zero=False` filter dropped rows
whose measures *sum* to zero or less - fine for a headcount, fatal
for a signed surface, where a pixel holding a single -1.2 degC
anomaly sums negative and was deleted immediately after being
rescued. **Fixing one without the other would have shipped a fix that
did nothing.**

**THE OTHER THIRTEEN, GROUPED BY WHAT THEY TEACH.**

*One rule, four copies, and the fourth was stale (354).* "Which
columns are measurements" was an exclusion list written in four
places under a comment claiming it was "decided ONCE". The copy
nobody updated was in `folder_to_cells` - the one function that
INFERS THE WEIGHT - so `keep_index=True` made a good single-cohort
folder un-runnable by presenting `gx` and `gy` to the user as people.
And `compose=` broke the promise twice over: a composed column is a
SUM of other columns, the list did not know that, and
`compose={...}` with `sum_cohorts=True` counted everybody in it
**exactly 2.0000x, measured** - once through the total, once through
prefix-matching into the reference population. John's own documented
use is `compose={"under5": [...]}` + `sum_cohorts`, which counted
every child under five twice. `measurement_columns(frame, derived=())`
is the one rule now, and a test fails if an open-coded copy reappears.

*An input the code accepted and then misread (355-357).* A float year
`2020.0` reached the label text as `"2020.0"`, matched nothing, and
**was refused while being present** - one input, two answers. A group
name equal to the weight produced shares from 0.0002 to 3.27 instead
of 1.0 everywhere. A `pattern=` handed in at the door was written
into the module-level `CONVENTIONS` registry and **outlived the call
that supplied it**, so a later folder in the same session was parsed
by a stranger's rule.

*Four messages and a crash in machine 4 (358-366).* A year the data
does not hold blamed the filenames instead of naming the years
present (358); `fmt` is refused outright per John's ruling (359); a
side made of two ranges reported one range's coverage for both (360);
a folder holding one sex is **recorded, not refused** - also his
ruling, *"user entered info as 'f' or 'm' or non, are done by
experienced users"* (361); cohorts above 90 are no longer silently
dropped (362, with the demographic ruling itself left open as 363);
a tiled machine-4 run died with `KeyError: 'results'` and now refuses
up front (364); and the field guide says the indices are **PER ONE,
not per 100 or per 1,000** (366), which is the kind of thing a
reviewer finds in a table rather than in the code.

**WHAT I GOT WRONG IN THE REVIEW ITSELF**, because a fresh session
will make the same two mistakes. I reported that a duplicated
`effective_range` differed in executable logic; it did not - over
25,650 inputs, zero disagree, and the duplication was structural
only. I had to correct my own finding. And two of my break-check
expectations were wrong rather than the tests being wrong: one break
was caught by the *other* gate (above), and one fired a different and
entirely correct test from the one I had predicted. **The break-check
is evidence about the suite, not about my model of the suite.**

`tests/test_raster_review.py` is 33 tests over findings 353-366, 31
breaks applied, all caught, "never failed under any break: none".

---

## 0e. 1.52.0 - TWO CLAIMS THE SOFTWARE MADE ABOUT ITSELF

Both from the external review of 1.29.6, both open for eight releases,
and taken together because they are **one defect in two costumes: a
module asserting a property it did not have.**

**158 - THE DOCSTRING WAS THE BUG'S DEFENCE.**
`selfpot.radius_for_k` said *"cell side in metres (cells are square by
construction)"* while `hex.py` handed it a hexagon's width across the
flats. The formula is area-based and correct; it was being given the
wrong area - 10,000 m2 where the cell holds 8,660 - so the radius came
out 7.46% too large.
**THE SECOND HALF IS THE ONE TO REMEMBER.** `decay_distance` used
MEAN_INTRACELL = 0.3826, which is a SQUARE's mean centre-to-point
distance. A hexagon's is 0.3510. The radius is area-based; the decay
distance is a mean distance. **Two constants, two derivations** - and
fixing only the first would have looked finished while leaving the
origin cell's decay weight 9% out, on the mass a run knows least about
and carrying the largest single weight in the calculation. When an
item names one number, check whether the module has two.
**THE SHAPE IS THE ONE NEW FACT**, and everything is derived from it,
so an area cannot be set that disagrees with its geometry. The square
factors are exactly 1.0 and the existing constant, so the square path
is an IDENTITY - asserted against the pre-1.52 formula itself rather
than against stored numbers, which is the form of safety argument to
reach for when touching something every published result used.
**AN UNKNOWN SHAPE IS REFUSED.** `SHAPES.get(shape, square)` is the
tempting line and it is this item's own defect: silently treating
something unknown as a square is how a hexagon came to be charged a
square's area for eight years.
**A MONTE CARLO CHECK DISAGREED WITH THE CLOSED FORM** at 2.4e-4, and
the closed form was right - quadrature confirms it to 1e-12. The
sampling noise looked like a discrepancy. The answer was a better
instrument, not a changed constant.
**AND THE MATRIX ROW CHANGED CATEGORY**, which is 333's mechanism
working as designed: hexes at the GIS doors were a RULING justified by
this bug, and are now a GAP with a witness, so the day somebody adds
the box the entry fails instead of going stale.

**159 - "WRITTEN PROGRESSIVELY" WAS NEVER TRUE.**
meta.py's first paragraph promised *"the file exists from start_run
onward, so a crashed run still leaves a record"*. With the default
constructor `_path` is None, so every `_flush()` was a no-op and
nothing reached disk until finalize() - **and both GUI doors used the
default constructor.** A QGIS or Pro run that died mid-analysis left
nothing at all. The claim was in the docstring, the manual and the
backlog's own description of item 2; it was never in the code.
**THE DOORS ALREADY KNEW THE DESTINATION.** `parameters.get(self.OUT)`
is read in base.py forty lines before the engine starts, for the
field-name check. The information existed; it was simply not passed.
**Before concluding something cannot be done early, check whether the
value is already in scope.**
**WHY NOW:** 1.51.1 gave TWO modules crash-survivable progressive
records for exactly this reason - bigrun (344) and fetching (347). The
class whose docstring claimed the property was the one that did not
get it. If you fix a robustness defect in one module, grep for the
others that claim the same thing.
**HALF THE ENTRY DID NOT REPRODUCE.** It said a second output path at
finalize leaves the first file marked "running" forever. Both said
`completed` - because nothing was written before finalize at all. The
symptom only becomes POSSIBLE once the record is progressive, so it is
now guarded rather than inherited. **Re-measure an old entry before
implementing from it.**

**AND FOUR OF THIS RELEASE'S OWN TESTS COULD NOT FAIL**, caught by the
break-check and not by review:
- one asserted *atomicity* by re-reading the file in a loop, which a
  single-threaded reader can never see fail. **"It is atomic" is not
  observable from one thread; the CONSEQUENCE is** - a failed write
  must leave the last good record intact, which is testable by making
  serialisation raise.
- one was called "finalize keeps the file the run was writing" and was
  broken with "make finalize recompute the path" - which does not fail
  it, because the two naming rules AGREE. The agreement is the design
  working, so that is what the test should assert; the docstring was
  describing a different test.
- two more in the same family, recorded in their own docstrings.


**AND THE RELEASE PROCESS ITSELF BROKE, TWICE, IN ONE AFTERNOON
(BACKLOG 352).** Worth reading before cutting a release.
- `python tools/bump_version.py X | head -4` **killed the tool
  mid-write**: head exited, the fourth print raised BrokenPipeError,
  and three of twelve declarations were written. **Never pipe a
  file-mutating tool into `head`.** The tool now does every write
  before any reporting, so it no longer depends on its own stdout.
- The rewrite that fixed that introduced a worse bug: planning every
  declaration from each file's ORIGINAL text and writing them all
  means **two declarations in one file lose the first edit.** Two
  files have two each. Edits accumulate per file now.
- **BOTH WERE CAUGHT BY THE VERSION-AGREEMENT TESTS IN UNDER A
  MINUTE.** Seven tests nobody thinks about until the day they fire.
- And the obvious regression test for the second one **does not
  work**: a bump round trip is self-healing, because the patterns
  match any version rather than the old one, so the return trip
  repairs what the first left wrong. The break-check found that. The
  test that catches it asserts that after ONE bump nothing still
  mentions the old version.

## 0d. 1.51.2 - ONE NUMBER EVERYWHERE, AND A GOOD QUESTION ANSWERED

A small release with two things in it worth carrying forward.

**JOHN ASKED WHETHER A NEGATIVE POPULATION COULD BE A WARNING**, on
the grounds that it might be the n a place has LOST - net migration,
depopulation - and that this "would clash with some stats but not
all". He delegated the call. The answer is no, and **the reason is a
step earlier than statistics, which is the part to remember**: k
counts people and a neighbourhood grows outward until it holds k of
them, so a weight that can be negative makes the running total
non-monotone in radius. It can cross k several times or never, so
"the radius at which k was reached" has no single answer and Dist_k
is UNDEFINED rather than odd - and every self-calibrating bandwidth
reads Dist_k. `proportional`, the default, divides by the crossing
cell's population to take a share, so a negative denominator inverts
the share. The statistics (mixed-sign weighted means landing outside
the data's range, Gini having no definition, a cumulative-weight
median having none) come last, not first.
**But the REFUSAL was not the defect - the MESSAGE was.** It named one
cause, an undeclared sentinel, and one remedy, missing(). For his
actual case both are wrong, and he was left refused with nowhere to
go. The route he needed already worked and had never been written
where somebody hitting the refusal would see it: a signed quantity is
a MEASUREMENT, so it goes in values() with the real headcount in
pop(). **I verified that before answering rather than asserting it** -
three places, ten people each, change [-50, +20, -5], k=20 gives
Mean_chg_20 = [-15, -3.75, 7.5] and -15 is exactly the hand
calculation. All three negative guards now name both causes and the
route.
THE GENERAL LESSON: **when a user asks for a guard to be relaxed,
check whether what they want is already possible by another route
before arguing about the guard.** It often is, and then the guard is
right and its message is the thing that failed them.

**THE REST OF THE RELEASE IS A VERSION ALIGNMENT, at John's request,
for teaching.** The engine, the four .ado files, the QGIS plugin and
the Pro toolbox install by different means and drift; he wanted a
batch where every door reports the same number, because "run `equipop
doctor`, both halves say 1.51.2" is a better first lesson than an
explanation of why they differ. Worth knowing for a future session:
I first argued against a new version, correctly on the facts - 1.51.1
already stamped the ado at 1.51.1, and the real gap was that SSC held
1.49.3 - and his reason was still better than mine. A teachable
version story is a deliverable.
**THE FLOOR IS NOT A VERSION AND MUST NOT BE MADE ONE.**
`eqp_min_engine` stays 1.48.0 through both releases. It is the oldest
engine the commands' own CALLS need, maintained by hand, and
bump_version.py is forbidden to touch it. Raising it because a release
number moved is exactly BACKLOG 332's mistake. In the doctor's report
two numbers must match and a third must merely be satisfied, which is
the distinction to explain rather than to paper over.

**AND THE RELEASE TRIPPED OVER ITS OWN NEW LIST.** Section 4 below
gained shape 7 - "asserting a phrase of a message" - in 1.51.1. Two
tests written that same day matched "cannot be negative", so improving
the message in 1.51.2 failed them while the guards they watch were
untouched. Rewritten to assert the behaviour and that the refusal
names the offending value; the wording is pinned by 351's own test,
where it belongs. **A list of known failure shapes is only useful if
you read it before writing the next assertion**, and I did not.

## 0c. 1.51.1 - NINE FINDINGS, AND THE SHAPE THEY SHARE

A full code review of 1.51.0, arriving the same day as Marina's pull
request. **Nine findings. All nine reproduced before any code moved;
none dismissed; two of them were mine from 1.51.0.** Read this before
touching the Stata statistics path, bigrun, or anything that passes an
option to an engine.

**THE SHAPE, because it is the transferable part.** Three of the nine
were THE SAME DEFECT: an option accepted at the door, documented, and
not passed to the engine.

- **F1** - `self_rule`, `overshoot_mode` and `seed` reached
  run_knn_friction and run_knn_slope through a dispatch call that
  omitted all three. So `originrule(exclude)` included the origin.
- **340** (Marina's, same day) - `r_values` forwarded on the untiled
  continental branch, dropped on the tiled one.
- **345** (found while fixing F3) - FIVE options accepted by
  run_knn_counts and by nothing in run_knn_counts_tiled.

**F1 was worse than incomplete - it was a false statement**, because
1.50.0 had just taught every run to record its settings from the
engine's own arguments. The record faithfully wrote down
`overshoot_mode: whole` while the engine computed proportional. **A
provenance system turns a pass-through gap into a lie.** If you add a
provenance field, you have made every pass-through a correctness
surface.

**WHY THE SUITE COULD NOT SEE ANY OF THEM.** It had thorough coverage
of each option and thorough coverage of each engine, and nothing that
crossed the two. `tests/test_rule_cross_product.py` now enumerates
engine x origin rule x overshoot mode and asserts the two things that
matter: the option CHANGES A NUMBER, and saying nothing gives what the
documented default gives. Reverting F1 fails four tests that name
exactly the two engines and the two options. **Write the pair test
when you add an option, not the acceptance test** - every one of these
three passed a test proving no exception was raised.

**THE TWO THAT MOVE NUMBERS FOR SOMEBODY.**

- **F2, BACKLOG 343.** The Stata statistics path implemented "weight
  by population" by repeating each row `np.round(weight)` times. Six
  cells each weighing 0.4 returned N = 0 and a mean of MISSING for
  every row - **the whole population rounded away**. This is BACKLOG
  118's WorldPop deletion, measured on John's rasters at 50.5% of
  people lost, 39% Rwanda and 69% Denmark, **still live eight versions
  after the cell engine learned to carry fractional weights**. 118 sat
  on the backlog naming it. The engine had `value_weights` since 1.41
  and the door never called it. If you find an open backlog item that
  names a defect in a path you are touching, CHECK WHETHER IT IS STILL
  TRUE - this one had been quoted in three release notes as
  outstanding and nobody re-measured it.
- **F3, BACKLOG 344.** Resume recorded `n_cells` and `unit_size` and
  nothing about the data, so a folder of finished tiles answered a
  different population's question: nine cells either way, success
  reported, Dist_20 of 81.2 m returned where the truth was 56.4 m.
  `CellData.fingerprint()` now digests what the engine reads.
  **The rule for a run identity is written down in bigrun.py**: a key
  belongs if changing it changes a NUMBER, and stays out if it changes
  only the speed. A test fails if `chunk` or `m_neighbors` is added,
  because a user who goes faster must not be told their three-day run
  is a different analysis. That is the other half of every guard in
  this project: no correct configuration may trip it.

**AND ONE FIX SHIPPED A REGRESSION THAT THE SUITE CAUGHT.** F5
resolves the sampling seed once in `dispatch`, which is right. But it
meant the engines below now SEE a seed, so they printed "sampled order
from seed N" - the line that means *you* chose - and
`"[overshoot] no seed given; drew N. Enter that number to repeat this
exact run."` vanished from every door at once. My block had written
its own sentence instead of calling `seed_message()`: **a second voice
on repeatability, in different words.** That is BACKLOG 105's and
328's fault exactly, and `test_6b` - written after a deliberate break,
for precisely this - failed. One formatter. Always.

**WHAT ELSE TO KNOW, briefly:**

- **F4 / 346.** The cohort completeness check compared age bands
  pooled and sexes separately, so the grid had holes: every band for f
  and m except `m_65` passed, and the ageing index shipped without men
  65-69. **My first probe was refused and I nearly filed it as
  unconfirmed** - the obvious construction (f young, m old) IS caught.
  The hole is narrower. When a finding does not reproduce on the first
  try, construct the case the reviewer described rather than the one
  you thought of.
- **F7 / 347.** BACKLOG 291 wrapped the fetch loop so a failure would
  not erase success - and caught `FetchError` only, the error this
  module raises about its own checks. URLError, OSError, Ctrl-C all
  went past, leaving verified files with no provenance, after which
  the retry correctly refused to continue. **Check what your except
  clause actually catches against how the thing actually fails.**
- **F9 / 348.** QGIS provenance could not name its own output: one
  sidecar for every layer in a GeoPackage, each run overwriting the
  last, and the record documented the engine's column names rather
  than the file's. **And every QGIS provenance record in the suite
  carried `"inputs": []` with no test asking**, because `qgis_stub._Source`
  had no `sourceName()` at all and `except Exception: pass` swallowed
  the result. **Another qgis_stub.py fidelity failure** - I will not
  put a number on it, because the running count in MANUAL.md reached
  "fifth" at 1.44.8 and then one release added five at once, so any
  figure I quote here would be invented. A simulator that OMITS a
  method cannot fail the code that needs it, which is a different
  failure mode from the earlier ones: those were methods the stub had
  and got wrong. That file remains the most dangerous in the
  repository.
- **The duplicate `effective_range`.** Defined twice, forty lines
  apart. I first reported that "the executable logic differs" - that
  was about the SOURCE. Checked properly: over all 25,650 inputs the
  band table admits, **zero** differing results.
- **The backlog head was stale for the third time**, and the review
  said so: it still described RunLog as dead code (done in 1.50.0) and
  still asked for 118 and 119. "An entry that is struck leaves this
  list" is written six lines above the list that kept them. Striking
  an item and updating the index are two actions and only the first
  feels like finishing.

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
| 1.51.0 | my own `g`-line .pkg test | it walked the `g` lines and checked the file existed, which it did - it validated the bug |
| 1.51.0 | my 337 label test | covered RADII only, so the half-landed tau rename (339) stayed green |
| 1.51.1 | `test_a_matching_resume_still_works` | asserted one PHRASE of the resume banner, so it failed for a wording change while a broken resume looked identical |
| 1.51.1 | four of my OWN new review tests | see below - the break-check caught all four before they shipped |

**FOUR MORE IN 1.51.1, ALL MINE, ALL CAUGHT BY THE BREAK-CHECK RATHER
THAN BY REVIEW.** Written for the nine findings, each with a
"BROKEN WITH:" line in its docstring, and then actually broken that
way - 31 breaks applied mechanically
(`tools/`-less, the script lived in the session scratchpad). Four of
the 39 tests did not fail under any break:

- **The large-weights "ceiling" test** asserted the mean and N, both
  of which row expansion gets RIGHT, just slowly. It passed against
  the behaviour its own docstring named. Now it reads the row count
  build_cells prints, which is what distinguishes the two
  implementations.
- **The seed test** passed with `seed=` deliberately removed, because
  the fixture gave every cell ten identical people and no treatment -
  so whichever cell the sampled ring admitted, N came out the same.
  **A sampled choice is unobservable without something to tell the
  cells apart.** And once that was fixed it still passed for the slope
  engine, because the hill DEM gave every neighbour a distinct cost
  and left no tie to break.
- **A zero-weight-origin test** named a break that does not break it:
  the member/origin split was needed by the ROW-EXPANSION code (which
  deleted a row repeated zero times) and is unnecessary once weights
  are numbers. What carries the rule is `_add_empty_origin_cells`.
- **An N_local test parametrised over four engines SKIPPED ALL FOUR**,
  including the only engine that reports the column, because the skip
  named the wrong one. **Four green skips read as coverage and were
  nothing** - the same defect as an unfalsifiable assertion in
  different clothes.

Every one is recorded in its own docstring, including what it first
got wrong, because "I checked" is not evidence a later session can
use. The property finally asserted was not "each break fails a test"
but **"every test function fails under at least one break"** - which
is the question, and it is the one that found all four.

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
5. **A fixture that cannot show the difference.** 1.51.1: ten
   identical people per cell, so which cell a sampled ring admits
   changes no output; and a hill DEM that breaks every tie, so
   sampling has nothing to choose. The assertion was right, the
   arithmetic was right, and the test was empty. **Ask what in the
   fixture would differ between the two implementations.**
6. **A skip that reads as a pass.** A parametrised test that skips
   every case looks green and is absent. If a skip is right, say why
   in one line; if every case skips, the test is testing nothing.
7. **Asserting a phrase of a message.** 1.51.1: a resume test checked
   the words "parameters match", so it broke when the banner gained
   "and cell data" and would NOT have broken if resume had stopped
   working. Assert the behaviour; let the wording move.

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

**THE STATA JOURNAL PAPER IS SUBMITTED** (5 October 2026): *equipop:
Individualized spatial contexts in Stata*, st0000. It is no longer a
planning item, and PROPOSALS.md section 2 now records what the paper
**OBLIGES** instead - equation (5)'s adaptive radius (which is the
formal reason a negative population is refused), the five decay
families, the power family having no finite-area half-life, and
**footnote 1, a correction to the published literature that the code
must keep earning**: Östh et al. (2016)'s log-normal appendix sets an
erf term to one half, which locates the third quartile rather than the
median, and equipop solves the 50% cumulative-area condition directly.
Verified on the shipped code the day of submission: the area below *h*
is 0.500000 of the total. **A regression there would make a submitted
paper wrong about the thing it claims to fix.**

**158 AND 159 ARE CLOSED** in 1.52.0, so the detail below that refers
to them as open is history. The hex blocker is gone; what remains is a
dialog decision.

**THE HORIZON CALL OPENS 29 OCTOBER 2026 AND CLOSES 17 FEBRUARY 2027.**
Re-checked 5 October against two sources, one updated four days
earlier. **February is the DEADLINE, not the opening** - a mistake now
made twice by the same person five months apart, because the original
schedule (open February, close April) is the memorable one and still
circulates on aggregator sites. See PROPOSALS.md, which leads with it.

**365 - MACHINE 4 HAS NO TILED PATH, AND THIS IS THE ONE THAT TOUCHES
FEBRUARY.** Newest item, from 1.53.0, and left open deliberately
rather than missed. A continental demographic run - machine 4 over a
whole continent, which is the exposome claim's own scale - has no
supported route. 364 made it **refuse clearly instead of dying with
`KeyError: 'results'` after the tiles were already computed**, which
is the honest state but not a capability. Do NOT describe
population-weighted exposure at continental scale as done when
writing the Horizon material: 353 made the *surfaces* carriable and
365 is why the *index* still is not. Pairs naturally with 349 - both
are the continental door being thinner than the single-extent one.

**363 - NEEDS JOHN'S DEMOGRAPHIC RULING, NOT CODE.** What should
happen to age bands above 90. 362 stopped the silent dropping and
made the code SAY what it is leaving out, which is the part that
needed no ruling; what it should DO - fold them into a 90+ band,
offer them as extra bands, or refuse the folder - is a question about
what "90+" means in a published figure, and that is his call, not
mine. The 90 ceiling is WorldPop's convention, not every product's.

**349 - the continental door offers none of the engine options.**
From 1.51.1. `run_knn_counts_tiled` now takes
self_potential, overshoot_mode, self_rule, seed and decay_eps (345),
and `run_folder` passes none of them on EITHER branch, nor `decay` at
all. So nothing is inconsistent between tiled and untiled - it is a
uniform gap, which is why it is not a correctness fix and stayed out
of a correctness release. **It matters because `originrule(exclude)`
is the w(ii)=0 convention spatial regression requires, and a
continental run is exactly the scale at which somebody wants it**; the
13.6% figure session 12 measured on US blocks is a published number a
continental user cannot currently reproduce. Cost: four dialogs,
shared help text through doors/help.py (NOT a second copy - see 105
and 338), door-parity entries, and box-changes-the-answer tests to the
standard 99 and 341 set.

**118 and 119 ARE CLOSED** (343, 344), which matters for reading this
file: earlier sections and the backlog head both described them as
open, and the 1.51.0 review found the head still asking for them.

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
