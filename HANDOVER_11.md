# EquiPop — HANDOVER 11
### written during the 1.37 → 1.40.1 session, days before the conference

**Supersedes HANDOVER_10.md**, which was amended seven times as this
session shipped and has been rewritten rather than patched again.
8, 9 and 10 are kept only for their history.

---

## 0. START HERE

### THE REPOSITORY

```
https://github.com/GeoJohnSwe/EquiPop
```

**It is public and clones without credentials.** No handover before 10
recorded this, and three sessions opened by asking John for it. If a
future session cannot clone it, ask for a zip of the working tree —
do NOT ask for a token, and do not accept one.

New session = upload this file plus one line: *"continue; next: X"*.
Claude clones main, reads this and `BACKLOG.md`, and works.
**Do not rely on Claude remembering anything.**

### READ THE VERSION IN THE CLONE BEFORE PLANNING ANYTHING

```
head -8 pyproject.toml
```

In the previous session the handover said 1.35.1 and main was at 1.36
— an entire release the handover did not know about. Half a plan was
built on a state that no longer existed. This costs nothing to check.

**HANDOVER FILES DO NOT TRAVEL IN THE ZIP UNLESS SOMEBODY PUTS THEM
THERE.** The external reviewer caught this: the delivery contained
HANDOVER_9 while the source zip contained only 6–8, so a session
starting from the zip alone would begin from superseded priorities.
Commit each handover to the repo root.

### Then ask two questions before diagnosing anything

1. **Which versions are on the machine RIGHT NOW?**
   - Stata: `equipop doctor` — one line, and since 1.40.1 it compares
     the `.ado` version against the engine version itself.
   - QGIS Python Console (it compiles a paste as ONE statement, hence
     the semicolons):
     ```python
     import equipop; print("package:", equipop.__version__); import equipop_qgis; print("plugin:", equipop_qgis.__version__)
     ```
2. **What changed between the run that worked and the run that did
   not?** Never assume nothing did.

---

## 1. THE DEADLINE

**John presents in Bulgaria in the LAST WEEK OF AUGUST 2026, and Umut
presents too — from a Mac.** That second fact arrived this session and
changes the weighting: Mac resilience is not a nicety, it is the
presentation machine.

**SSC listing will not happen in that window** — submission goes
through Kit Baum and turnaround is weeks. The target is `net install`
from the GitHub repo, which needs the `.pkg` and `stata.toc` that
shipped in 1.36 and is live the moment John pushes. SSC afterwards.

### What the Stata door must contain — machine 1 ONLY

John's words: *"the simple answer is - only machine 1 since that is
the one thing genuinely missing in Stata."* No friction, effort,
slope, FCA or LISA.

### WHAT `equipop` ACCEPTS TODAY — after 1.40.1

```
equipop setup [, repair]
equipop doctor

equipop [fweight] [if] [in], x() y()
        [ treat() treatmode() missing()
          k() r() unit() pop() selfpot() selfpotname()
          decay() halflife() halflifevar() bins() overshoot()
          project epsg() prefix() replace ]

```

`equipop_knn` remains as a forwarding alias so nothing already written
breaks.

**WHAT IS LEFT — one release, and it is one piece of work.** See
section 4.

### The demo dataset

`DataBristolCounty2022_filled.xlsx` — 1,074 census blocks in 37 block
groups, Bristol County, Rhode Island, 50,793 people. Age (`B01002`),
race (`B02001`), median household income (`B19013`), population,
lat/long. A `.dta` conversion was handed to John already.

- **`B19013_E001` carries the Census sentinel `-666666666` in 64 rows
  (6%)**, and 64 more are top-coded at `250001`. Use
  `missing(-666666666)`.
- **The ACS attributes vary at BLOCK-GROUP resolution**, back-filled
  to blocks — 34–36 distinct values across 1,074 rows. Not a flaw: it
  is the argument for the method, since k-neighbourhoods cut across
  those 37 boundaries while the source data cannot. It also means a
  Gini over it measures dispersion between area medians, which
  understates household inequality.
- It is in **lat/long**, so `project` applies: UTM zone 19N,
  EPSG:32619.

---

## 2. WHO JOHN IS, AND HOW TO WRITE TO HIM

John Östh — OsloMet, with Lund and Uppsala. EquiPop is his software, a
reimplementation with Claude of his older C# tool. **Geographer,
demographer and spatial analyst — NOT a programmer**, non-native
English speaker.

### THE COMMUNICATION RULE, which he asked for explicitly

> **Plain words for anything about code. Full technical strength for
> statistics, geography and method.**

"It parses each `.ado` and refuses a call site that does not match its
def by arity" is fog. "It checks that the two halves of the file agree
about what gets handed over" is not. The reverse also holds: do NOT
water down the statistics. Why a sub-percent scale error cannot
reorder a k-neighbourhood, what a Gini over area medians actually
measures, why a decayed total must be smaller than its raw total —
write those at full strength. **Say what a thing does before saying
what it is.**

- **He rules quickly and overrules freely.** Numbered lists for
  decisions; he answers in kind, often in a few words. A numbered
  proposal answered with "1. Yes 2. Yes 3. your best choice" is the
  shape that works.
- **Ask ONE question per point and make it answerable.**
- **HE WOULD RATHER HAVE A BUILD THAN A CONVERSATION.** When a
  decision is genuinely his, take a position, say which way you went,
  and let him overrule.
- **Budget session credits, and BUILD ARTIFACTS EARLY.** He needs the
  complete zip, the wheel AND the `.tar.gz`, and `present_files` for
  all of them.
- **He publishes, then tests. He pushes himself.** Claude builds; John
  pushes. Few users, rollback is one command.
- **He tests in the field, and the field is the truth.** When his
  report and Claude's reading of the code disagree, **John is right
  until something running proves otherwise.**
- **He values honesty over polish.** Say plainly when something is
  unverified, when a claim was wrong, or when Claude's own edit broke
  something. Two claims in this session's first message were wrong and
  correcting them plainly cost nothing.
- **He is generous about his own part in a mistake. Do not accept it
  when it is not his.** He offered that the decay misunderstanding was
  his failure to express what he needed; it was not — the rule was
  written in `analysis.py`'s own docstring and the fast engine had
  diverged from it. Say so.

### Umut

Umut tests on a **Mac** and **presents in Bulgaria**. His machine
found BACKLOG 176. He is a second field tester on a different
operating system, which matters more than it sounds: every Stata
problem before him had been Windows-shaped.

### THREE INDEPENDENT SOURCES OF REAL DEFECTS

The suite is the weakest of the three. This session:

1. **The field** — Umut's Mac (176).
2. **An external reviewer** — the treatment contract (179), the empty
   `treat()` loop (180), fractional cell sizes (181), the dangerous
   shipped instructions (182), the name preflight (184).
3. **John reading the release notes** — the decay measure (185).

---

## 3. STATE AT THE END OF THIS SESSION

**1.40.1 is built, archive-checked and handed over. 583 tests, 14
skipped, run from inside the unpacked sdist.** 454 tests at the start
of the session.

**NOTHING FROM THIS SESSION HAS RUN INSIDE REAL STATA YET.** John
intends a field pass: `equipop doctor`, a `project` run on Bristol,
and a `decay()` run to see `ND_300` beside `N_300`.

### Released this session

| | |
|---|---|
| **1.37** | 176 the import trim; 128 `equipop doctor`; 177 UTM projection in numpy alone; 178 the multi-zone note |
| **1.37.1** | 179 THE TREATMENT CONTRACT; 180 empty `treat()` broke `replace`; 181 fractional cell sizes; 182 the shipped Stata instructions |
| **1.38** | 168-stata missing-value codes; 183 a negative group count slipped the 179 guard; 184 result names preflighted |
| **1.39** | 42/99/102-stata decay, overshoot, the self-potential ladder |
| **1.40** | 185 the decayed totals are reported AT k, on the raw threshold — an ENGINE change, so it lands at QGIS and Pro too |
| **1.40.1** | 186 the doctor compares the `.ado` version against the engine |
| **1.40.2** | 187 `equipop setup` — installing is two lines on both platforms; 43 CITATION pinned; 101 `tmp/` ignored |
| **1.40.3** | 188 an unknown subcommand is named, not called a variable list |
| **1.40.4** | 191 Dist_k FELL AS k ROSE - both engines; 192 places with no people now get results |

1.36 was already on main when the session opened and is not this
session's work.

### John's rulings this session, so they are not re-litigated

1. **`treat()` MEANS COUNTS** — the number of people of the group at
   that point, matching the help and both GIS doors. `treatmode(flags)`
   keeps the old 0/1 rule. **Impossible combinations REFUSE**, they do
   not warn.
2. **Ship a correctness fix immediately; do not hold it behind feature
   work.** He had ruled the opposite for 1.37 and overruled himself the
   moment the defect was a wrong number.
3. **Projection is for the beginner, not the professional.** His
   words: *"for professional spatial analysts, this function is not
   needed... However, for the unexperienced stat and econ people that
   are not trained to think beyond lat/long, a simple function to
   generate good-enough projections are what is needed."*
4. **The run must SAY which projection it used** — *"i.e. EPSG code
   for UTM would be enough"*.
5. **Wide data gets a note and PROCEEDS.** Never a refusal. His
   reasoning, which also closed 171 and must not be re-argued: *"the
   bespoke neighbourhood departs from the nearest k-neighbours, it
   becomes almost impossible to find a situation where an erroneous
   nearest neighbour is selected before the true nearest, and if that
   happened it would be in very large k, and at distances that makes
   very little difference. (i.e. for me it is the risk of counting the
   wrong cafe in Lyon/France from Oslo)"*
6. **DECAY DOES NOT CHOOSE THE NEIGHBOURHOOD.** His words: *"the
   k-values should aim for a NON-DECAYED k. i.e. if k=300 is
   requested, the 300 nearest population is the right call - the
   decayed populations should be reported and are always ... smaller
   than k"*. It weights the reference and treatment populations; it
   does not affect distance.
7. **`overshoot(sampled)` REFUSES by name.** It exists only to compare
   against old EquiPop versions, so it is not a Stata concern.
   Dropping it drops the seed option too.
8. **The self-potential ladder has THREE rungs** — 0, the equal-area
   radius 0.7071, and 1. John corrected this directly.
9. **Words, not numbers, for every Stata option.** A do-file read six
   months later has to say what it did.
10. **The unbounded decayed sum was DELETED, not commented out** —
    *"it risks becoming an orphan or picked up in a later session with
    unknown consequences"*.
11. **`equipop doctor` is enough in Stata for now.** Pro and QGIS
    after the conference.

### Rulings carried forward, still in force

1. **Quantiles are INTERPOLATED, not stepped.**
2. **Missing codes**: the cause is unimportant, the ability to exclude
   matters. A blanked case *"could still be the placeholder for
   results - it just doesn't contribute self"*.
3. **A share divides by the OBSERVED part**: 400 people, 60 of unknown
   group → denominator **340**, never 400.
4. **`if`/`in` restrict the OUTPUT ROWS, not the neighbour pool.**
5. **Use Stata's own commands where we can**, not where it
   jeopardises our code. Hence `marksample touse, novarlist`.
6. **Overshoot labels are short and the word "recommended" is gone.**
7. **Sidecar CSVs go to an `EquiPop_runs` folder** beside the
   container.
8. **Single-zone projection is acceptable.** 170 and 171 were both
   DECLINED in 1.34. Do not reopen them.

### FINDINGS — the ones that keep earning their place

1. **A default argument is the easiest place in this codebase for a
   feature to disappear.** 148, and 172 in Stata dress.
2. **A guard that drives the helper is not a guard on the door.**
3. **GREP TESTS CAN CERTIFY A CORPSE. Parse, do not search.**
4. **Guessing at performance is a waste of turns. Profile.** The
   import cost was measured before it was changed — 2.46 s, 1226
   modules, five compiled libraries — and the measurement made the
   case, not the argument.
5. **A code path that needs a MISSING VALUE to be reached will not be
   reached by clean test data.**
6. **Code inside a Stata `python:` block can only be run by Stata.**
7. **The handover can be a release behind the repository.** Read the
   clone first.
8. **A THIRD CLASS OF STATA DEFECT: RUNTIME GRAMMAR.** After 172's
   arity mismatch and 173's `None`, 180 is a construct that PARSES
   perfectly and fails only when Stata runs it. `foreach v of varlist
   \`treat'` on an empty macro is a SYNTAX ERROR, not an empty loop.
   When an option becomes optional, hunt for every place its macro is
   expanded into Stata syntax rather than passed as a string.
9. **A GUARD THAT REFUSES THE IMPOSSIBLE WILL FIND YOUR OWN FIXTURES
   FIRST.** 179's guard broke six tests on day one: two fixtures drew
   the population and the group independently, so the group exceeded
   its own population at 84 of 400 points. The FIXTURES were wrong.
   Third time this project has been bitten by data that could not
   occur in the field.
10. **A GUARD WRITTEN AGAINST ONE IMPOSSIBLE CASE WILL NOT CATCH THE
    OTHERS.** 183: 179 asked whether a group was BIGGER than its
    population, and a sentinel of -666666666 is comfortably smaller.
    Enumerate the impossible cases.
11. **A TEST THAT ASSERTS ONLY `<=` CAN PASS BY BEING EQUAL.** 1.40's
    hardest guard — that a split overshoot ring gives the decayed sum
    the SAME fractions as the raw count — was broken on purpose and
    NOT caught, because the broken version produced equality and the
    assertion allowed it. An inequality guard needs a companion
    assertion that both sides actually MOVE.
12. **A DOOR CAN OFFER SOMETHING THE ENGINE DOES NOT HAVE.** 1.39's
    door offered a decay model called `gauss`; the engine implements
    negexp, expnormal, expsqrt, lognormal and power. Doors may not
    import the package to learn their own vocabulary (78/105), so
    every duplicated list must be PINNED against its engine list by a
    test, the way `test_rungs.py` does.
13. **WHEN AN ENGINE OUTPUT CHANGES, THE FIELD PREDICTOR MUST CHANGE
    WITH IT.** `equipop/doors/fields.py` declares a run's output
    columns BEFORE the run, for ArcGIS. It promised `ND_inf` after the
    engine stopped making it. Whenever a column name changes, grep
    `equipop/doors/` before assuming the change is confined to the
    engine.
14. **WRITE THE TEST EXPECTING THE OBVIOUS THING, AND LET IT FAIL.**
    The decay test was written assuming decay would move `Dist_k`. It
    does not. The HELP was wrong, not the code.
15. **INSTRUCTIONS ARE PART OF THE RELEASE.** 182: the shipped README
    told users to point Stata at Anaconda, the one configuration that
    closes Stata. A document can break a machine before any code runs.
16. **A SUBCOMMAND THAT DOES NOT EXIST YET PRODUCES A BAFFLING
    ERROR, AND THE FIX CANNOT HELP THE PERSON WHO FOUND IT.** 188:
    `equipop setup` on an .ado that predated the subcommand fell
    through to the `syntax` line, Stata read the word as a variable
    list, and said `varlist not allowed`. Whenever a subcommand is
    ADDED, remember that everyone on an older copy gets that wall.
    The general lesson: **a Stata command's first token is the one
    place a user can put something the parser has no vocabulary for**,
    so it needs its own error, not `syntax`'s.
17. **THE ONLY TRUSTWORTHY TEST OF A WRITE IS READING IT BACK.** 189:
    `arcpy.da.ExtendTable` RAISES on a `memory` layer having created
    the fields, and elsewhere could return cleanly having written
    nothing. Neither the return value nor the exception is evidence.
    The same assumption is in the QGIS door (190), which discards a
    boolean. **Applies to every door and every write.**
18. **DIAGNOSE BY BISECTION, AND VERIFY THE PROBE ITSELF.** 189 took
    six snippets and THREE wrong hypotheses from Claude - a stale
    field, a `memory` limitation, then NaN - because the early probes
    only checked that no exception was raised, never that values
    arrived. A probe that does not verify its own success is worth
    nothing. Also: a "contiguous OIDs" check compared cursor ORDER
    against 1,2,3 and reported False on a complete 1-682 set; say so
    when a probe was the thing that was wrong.
19. **A VARIABLE DOING DOUBLE DUTY AS A MEASUREMENT AND AS A FLAG IS
    A TRAP.** 191: `dist_m == 0.0` meant both "no distance covered
    yet" AND "the neighbourhood is still inside the origin cell,
    so use the in-cell estimate". Raising it to fix the first
    destroyed the second, and two engines disagreed by 40 m. The
    correction had to be substituted AT THE INTERPOLATION CALL. When a
    sentinel value is also a real measurement, say so where it is set.
20. **A FIX TO ONE ENGINE MUST LAND IN BOTH.** 191 was fixed in
    `fastcounts.py` and `test_fast_engine_identical` plus
    `test_both_engines_apply_the_same_rule` failed within the minute.
    Those two tests are the reason the engines have not drifted; treat
    a failure in them as information, not as an obstacle.
21. **THE FIELD TEST PASS IS A GUARD.** 191 was found by a line in
    `equipop_test_pass.do` that said "if any row breaks that
    ordering, something is wrong" and returned 198. Property checks
    written INTO the do-file catch things the suite cannot, because
    they run on real data at real size. Keep adding them.
22. **A HANDOVER CAN CARRY A WRONG INSTRUCTION FORWARD, AND NOTHING
    WILL CATCH IT.** The 1.40.4 external review found TWO in this
    file's own 1.41 plan: a category syntax that parses to zero
    matches, and an `outside(zero)` description with the geography
    backwards. Both would have been built straight from the note, and
    neither would have raised an error. **Before implementing
    anything a handover proposes, run the example against the parser
    and read the existing implementation.** A plan is not evidence.
23. **THE EXTERNAL REVIEW IS THE THIRD SOURCE OF REAL DEFECTS, AND IT
    IS THE ONLY ONE THAT READS THE PLAN.** The field finds wrong
    numbers; the suite finds regressions; the reviewer finds wrong
    intentions. Send each release out for one.
24. **Breaking a guard on purpose sometimes reveals that the guard is
    REDUNDANT, and that is worth saying out loud.** The missing-value
    mask in `to_utm()` cannot be caught by any test, because NaN
    already propagates. It was kept and LABELLED as redundant rather
    than left looking like coverage.

### Still John's to do

- **The QGIS plugin ZIP is built by `tools/make_plugin_zip.py`**, not
  by the release-zip tool. QGIS's Install from ZIP needs ONE
  top-level folder named `equipop_qgis/` with `metadata.txt` inside
  it; a zip of the folder's CONTENTS installs as a plugin that loads
  once and then cannot be found. The tool asserts the shape and
  reuses the release zip's `__pycache__`/`.pyc`/bad-name filters.
- **The author line is already correct** — John Östh, OsloMet first,
  then Lund and Uppsala — in `metadata.txt`, `CITATION.cff` and
  `pyproject.toml`. A QGIS install showing "John Osth, Uppsala
  University" is an OLD PLUGIN, not a stale string.
- **BACKLOG 101 remnant** — `git rm -r --cached tmp` ONCE. The
  `.gitignore` rule went in at 1.40.2, which is what was missing
  before; without it the earlier removal never stayed done. Exactly
  one file is tracked under `tmp/`.
- PyPI upload of each release. **`equipop setup` depends on this** —
  it runs `pip install equipop`, so a release that is not on PyPI
  cannot be installed the easy way.
- Commit the handovers to the repo root so they travel with the code.
- Field-test 1.40.1.

---

## 4. WHAT IS NEXT

```
1. FIELD GUARD FIRST - the external review of 1.40.4 is right that
         no feature should go in ahead of this.
         - equipop_test_pass.do STATES its invariants but does not
           ENFORCE them: no assert, no exit. A failed property prints
           a number and the run carries on. Turn each `count if` into
           `assert r(N) == 0`, capture `_rc` straight after each
           expected refusal and fail if it did not happen, make the
           data path a checked configuration line, and pin the
           version and run count.
         - BLOCK 20 IS STILL WRONG and halts the pass before the end.
           ValFloat is CONTINUOUS: after missing(0), 5,645 of 5,838
           values exceed their population and the treatment guard
           refuses - correctly. A continuous measure belongs in
           machine 2, not treat(). Build a small synthetic COUNT
           column with a -999 sentinel instead.
         - Save the Stata log as a release artifact, so
           "field-tested" has durable evidence.

2. 189/190 THE TWO WRITE RISKS, before any new analytical box. An
         analytical feature is not delivered if the door can report
         success with empty result columns. The read-back must
         compare against the values about to be written, not merely
         check that the fields exist.

3. STATA INTO door_parity.py - BEFORE the category rung, not after.
         The reviewer's argument beats this handover's earlier
         ordering: the category work touches the exact seam where
         door drift has happened before - reference membership,
         treatment membership, units, outside rows, group names,
         generated outputs. Adding a THIRD implementation before
         Stata is in the answer key invites another
         plausible-but-different result.

4. 1.41  THE LAST TWO BOXES - through a SHARED helper, not a third
         hand-written copy.
         - CATEGORY VALUES ARE COMMA-SEPARATED. parse_treat_spec
           splits groups on ';' and values on ','. An earlier version
           of this handover proposed treatspec("A: 5 6 7; B: 1 2"),
           which parses to {'A': ['5 6 7'], 'B': ['1 2']} and matches
           ZERO ROWS, silently. The working form is:
             treatcat(varname) treatspec("A: 5, 6, 7; B: 1, 2")
             refcat(varname)   reftypes("...")
           Keep commas: whitespace as a delimiter makes a category
           label containing a space ambiguous.
         - outside(zero|null) IS INPUT SHAPING, NOT POST-PROCESSING.
           An earlier version of this handover said it should "blank
           the results of excluded rows, or zero them". THAT IS THE
           WRONG GEOGRAPHY, and it would have been built from this
           note. John's rule, already in equipop/doors/help.py and in
           the QGIS code:
             zero - the row contributes ZERO to the reference
                    population and is nobody's neighbour, but it
                    REMAINS AN ORIGIN and receives the real results
                    for what surrounds it. A library outside an
                    eating-place reference population still has
                    eating places around it.
             null - contributes nothing AND receives no results.
           So: build the membership mask, multiply the reference
           count by it - QGIS does exactly `weight = base * pop_mask`
           in alg_counts.py - keep the coordinates for zero, mask the
           origin for null, THEN run the engine.
         - Three rules the GIS doors already have and Stata must not
           lose: read STRING categories without forcing them through
           the numeric _col(); multiply a category's 0/1 membership
           by the count field so treatment and reference share units;
           and preflight empty group names, case-clashing output
           names, and groups that match zero rows.

   Alongside 2, and small: 198 A QGIS INSTALLER, the same two steps
         as Stata - a plugins.xml repository hosted on GitHub (which
         also gives update notices, unlike Install-from-ZIP) plus an
         in-plugin action running pip against sys.executable. NOTE:
         --no-deps is NOT optional inside QGIS's managed scientific
         stack; upgrading numpy there can break QGIS itself. Fix
         README_QGIS.md's contradicting advice in the same edit.

--- after the conference ---
   199   ArcGIS Pro CANNOT have an engine installer - `arcgispro-py3`
         is read-only until the user clones it in Package Manager,
         which is Esri's design. Detect and instruct instead: the Pro
         half of 128.
   200   AN R VERSION OF MACHINE 1, scoped. ~1,700 lines of core, all
         of it mapping onto data.table plus RANN/dbscan. NATIVE, not
         reticulate - a wrapper inherits every Python-environment
         problem, and the port's audience is exactly the people least
         able to repair one. The cost is not the code, it is proving
         agreement: after 195 (Stata parity + a shared conformance
         route) it is roughly a fortnight, validated against
         tests/test_conformance.py. Before 195, do not estimate.

5. 189   THE PRO DOOR CANNOT WRITE TO A `memory` LAYER, AND SAID SO
         WRONGLY. Measured with six snippets in the Pro Python
         window, on a 682-row memory feature class:
             1 field  -> no error, VALUES OK
             2 fields -> SystemError, created, ALL NULL
             8 fields -> SystemError, created, ALL NULL
         The threshold is exactly TWO, and arcpy.GetMessages(2) is
         EMPTY, so there is nothing to recover from the queue. A real
         run writes a dozen columns, so `memory` is unusable for the
         bulk write and no setting avoids it.
         The "field 'N_1432' exist" the user saw was OUR OWN retry
         meeting the fields the first attempt had created. See
         BACKLOG 189 for the five-part fix. The first item -
         VERIFY EVERY BULK WRITE BY READING A ROW BACK - is worth
         having whatever ArcGIS does, because neither the return
         value nor the exception is evidence.
         NOT data loss: the fields came back all None.
6. 190   the QGIS door discards `sink.addFeature()`'s return value
         and reports a row count it never checked. Small - a lost
         FEATURE is visibly short rather than quietly wrong - and it
         can travel with any run that touches base.py.
   STATA PARITY is item 3 above. It has been deferred by HANDOVER 8, 9 and
   10 all said this and it still has not happened; 172 is the bill.

--- after the conference ---
5. 128-doors  equipop doctor in Pro and QGIS
6. 168-doors  the missing-code box in Pro and QGIS
7. 161        Pro will not offer a barrier raster from the map.
              NOTE THE TRAP: adding GPRasterLayer alone produces a
              dropdown that then FAILS, and the simulator cannot see
              it - test_arcgis_stub models valueAsText as str(value)
              and has no notion of multiValue, .values or quoting
8. 102        QGIS has no bandwidth boxes. Travels with 42
9. 118-rest   the expansion UPSTREAM, where counts become persons.
              This is what unblocks 38, and it is a pipeline change
10. 38        CONTINENTAL RUNS - John's destination
```

### THE LADDERS ARE MOSTLY ALREADY THERE, IN STATA'S OWN GRAMMAR

Read this before building anything for item 1.

| ladder rung | how Stata already says it |
|---|---|
| reference 0 — every point counts as one | no weight given |
| reference 1 — a field holds the count | `pop()` or `[fweight=]` |
| reference 2 — only selected types, with a count field | **NOT DONE** |
| treatment 0 — not measuring one | `treat()` omitted |
| treatment 1 — one column per group, counts inside | `treat()` + `treatmode(counts)` |
| treatment 2 — types from a type field, grouped | **NOT DONE** |

The GIS doors need an explicit mode selector because a dialog has to
ask. Stata expresses the same choice through the presence or absence
of a weight and of `treat()`. Adding `refmode()` on top would be
redundant AND would contradict the words-not-numbers ruling. **John
agreed the lower rungs stay implicit.**

### Three things about the code a fresh session would rediscover slowly

- **`equipop/bigrun.py` exists and is tested.** ORIGIN tiling with a
  GLOBAL tree, so results are exactly the untiled ones. At 1 km,
  Africa's ~30 million cells fit in memory. It is unreachable from any
  door; that is the gap.
- **`equipop/raster.py` reads WorldPop-shaped rasters** but re-bins
  lat/long onto a metric grid, which is the resampling item 93's
  snapping rule exists to stop.
- **`equipop/wstats.py` is the weighted-statistics core.** Its
  contract is that whole-number weights reproduce the person expansion
  exactly. Do not relax that without saying so loudly.

---

## 5. HOW CLAUDE SHOULD WORK

### THE IMPORT RULE — easy to undo by accident

**`equipop/__init__.py` must not gain a module-level
`from .x import y`.** Names are mapped in `_LAZY` and fetched on first
use. This is not style: before 1.37, `import equipop` loaded numpy,
pandas, scipy, pyproj and matplotlib for a Stata command that needs
three, and a fault in any one took the whole package down.

`tests/test_lazy_imports.py` guards it **in a subprocess**, because
once pytest has imported a library an in-process check passes for the
wrong reason. Adding a public name means adding a `_LAZY` entry — a
typo there removes a function and nothing else notices.

**Anything new that a Stata run touches must not add a compiled
dependency.** That is why the projection is transverse Mercator in
numpy (`equipop/utm.py`) rather than pyproj: adding a fourth library
for the feature aimed at beginners would have undone the same
release's first half. It is checked against pyproj across all 120
zones — worst disagreement 0.000193 mm.

### THE STATA DOOR

**Code inside a `python:` block in an `.ado` can only be run by Stata.
Nothing in pytest can reach it, ever.** Therefore:

- **Move everything possible OUT of the block and INTO the package.**
  `to_stata_values()`, `project_for_stata()`, `degrees_warning()`,
  `zone_span_warning()`, `validate_treatment()`,
  `check_results_are_possible()`, `blank_missing_codes()` all live in
  `stata_bridge.py` for this reason. The block should hold sfi calls
  and nothing else. **Every line moved out is a line that can be
  tested.**
- **What must stay gets READ instead.** `tests/test_stata_ado.py`
  parses every `.ado` and refuses: a block that will not compile; a
  call site not matching its own def by argument count or keyword; a
  name read that nothing defines; an option on the `syntax` line never
  used; an option with no help; a keyword handed to `stata_bridge`
  that no longer exists; and a `None` among the values of a
  `Data.store`.
- **The glue is called BY NAME with keyword-only parameters.**
- **Stata has no NaN.** Missing in a double is 2**1023; readers treat
  `> 8.9e307` as missing coming IN, and `to_stata_values()` writes the
  same sentinel going OUT. Never `None`.
- **A refusal from the bridge must become a Stata error, not a Python
  traceback.** Catch `ValueError`, wrap the text, `SFIToolkit.error`.
- **Adding an option costs FOUR edits**: the `syntax` line, the call
  site, the `def`, and `OPTION_HELP` in `tools/make_sthlp.py`. Then
  regenerate the help. The suite catches all four, but knowing this
  saves a cycle.
- **Help text that any other door will also need goes in
  `equipop/doors/help.py`**, not in `make_sthlp.py`. `missingcodes`
  and `decaymodel` were written there so QGIS and Pro inherit the same
  words instead of a third wording.

### Release discipline

- **One release per conversation** — unless field reports arrive. This
  session shipped six, and that is fine when each is built,
  archive-checked and handed over.
- **BUILD THE ARTIFACTS BEFORE THE LAST QUARTER OF THE SESSION**, and
  `present_files` the complete zip, the wheel and the `.tar.gz`.
- **Read the real text before editing it. PARSE BEFORE WRITING.**
  Take a copy of `equipop/` and `stata/` to `/tmp` first. A test file
  was corrupted this session by writing before parsing — the same rule
  this project already had, broken again.
- **Anchors must be unique AND UNAMBIGUOUS.** `assert count == 1` in
  the edit script itself, before writing. `"treatmode(string)":`
  appeared twice this session and the assert caught it.
- **NEVER `git checkout` while work is uncommitted.** HEAD is the
  PREVIOUS RELEASE.
- **Break every guard on purpose and watch it fail — at the level the
  USER meets it.** And when one does NOT fail, say so, and work out
  whether the guard or the test is the problem.
- **Unpack the archive into an EMPTY directory and run the suite from
  inside it.**
- **Version strings live in EIGHT places** — the eighth is
  `CITATION.cff`, pinned since 1.40.2 after sitting at 1.0.0 for forty
  releases. Only its `version:` field moves; the preferred-citation is
  the 2014 report and does not follow the software. The other seven: `pyproject.toml`,
  `equipop/__init__.py`, `qgis/equipop_qgis/__init__.py`,
  `qgis/equipop_qgis/metadata.txt`, `stata/equipop.ado` **line 1 AND
  the `local eqp_ado_version` inside `_equipop_doctor`**, and
  `stata/equipop.pkg` line 2. `test_doctor.py` asserts they agree.
- **Add a MANUAL version row every release.**
- **End every message with "Next steps & questions".**

### The doors

- **A box that changes the ANSWER belongs in `CORE`** in
  `door_parity.py`. **Stata is still outside that file.**
- **Parity of names is not parity of behaviour.**
- A Pro parameter with no `category` floats to the TOP. Pro parameters
  are addressed **by name, never by index**.
- Beware `_num(pm, "x", default) or default` — it eats a deliberate 0.
  The QGIS equivalent is `parameterAsInt` on an optional box; use
  `base.optional_int()`.
- **A stub is safe only where it is STRICTER than the real thing.**
- Neither door may import the package to learn what its own dropdowns
  say (78/105). Pinned by `test_rungs.py`.

### Talking to John

- ONE-LINERS joined by semicolons for the QGIS console; verify they
  compile in `single` mode before sending.
- **LABEL EVERY SNIPPET `[Stata]`, `[Command Prompt]` or
  `[Mac Terminal]`.**
- **NEVER WRITE A PLAUSIBLE-LOOKING FILE PATH.** Use
  `PASTE_REAL_PYTHON_PATH`, or have the user produce the path.
- Number the snippets and ask for ALL of the output.
- Say plainly what has NOT been verified.

### One environment note, so it is not re-diagnosed

`test_arcgis_stub.py::test_help_xml_covers_every_parameter` shells out
to `arcgis/make_help_xml.py`, which does `import equipop`. It fails in
a fresh container until `pip install -e .` is run. Not a defect. In
this container `pip` needs `--break-system-packages`.

---

## 6. THE STATA ENVIRONMENT — do not re-diagnose this

**FIRST MOVE, ahead of every question about versions or paths:**

```stata
equipop doctor
```

It prints the interpreter Stata is using, the processor it is built
for, the state of every library — present, absent, or installed but
refusing to load — and since 1.40.1 the `.ado` version against the
engine version. It is standard-library only, and because the package
no longer loads numpy on import it runs **on a machine where numpy
itself is the fault**. Its lines flush one at a time, so a crash
mid-report still leaves evidence.

### 1. Stata plus Anaconda crashes on `import numpy` (Windows)

`python: import numpy` **closes Stata outright** — no error, no `r()`
code, the window disappears. Anaconda's numpy and Stata's own engine
each bundle the same Intel maths library, and two copies in one
process is fatal. **Not an EquiPop fault**; it happens before the
package is reached.

**The fix, and the only one that worked:** a plain python.org Python,
used by Stata and nothing else.

```stata
python set exec "PASTE_REAL_PATH\python.exe", permanently
```
then **restart Stata**.

If Stata closes when `equipop doctor` runs, the Python is wrong and
nothing else matters.

### 2. A library built for the wrong processor (Mac) — BACKLOG 176

Umut's Mac. Stata runs as an Apple-Silicon program; the pandas in his
user folder was built for Intel. The loader refuses to mix them and
the import stops dead. **numpy imported fine** — a different, correct
build — which made it read as a pandas fault rather than an
installation one.

The message to recognise: *incompatible architecture (have 'x86_64',
need 'arm64')*. `equipop doctor` names it.

Driven from Stata, into the interpreter Stata itself uses:

```stata
python: import subprocess, sys; p = subprocess.run([sys.executable, "-m", "pip", "install", "--user", "--force-reinstall", "--no-cache-dir", "--only-binary=:all:", "numpy", "scipy", "pandas"], capture_output=True, text=True); print(p.stdout[-3000:]); print("ERR:", p.stderr[-2000:])
```

`--no-cache-dir` is not decoration: without it pip reuses the
wrong-processor wheel it already downloaded and the fix appears not to
work. If pip refuses with *externally managed environment*, that is
Apple's own Python and the answer is a python.org install, as on
Windows.

### 3. `--user` installs need `python_userpath` (Windows)

```stata
set python_userpath "PASTE_REAL_FOLDER", permanently
```

### 4. `python query` is ground truth for Stata's own view

It reports the executable, the version, and whether Python has
initialised. On John's machine it revealed Stata was using base
Anaconda, not the environment everyone had assumed.

### 5. LABEL EVERY SNIPPET

`pip` lines belong in a Command Prompt or Terminal. Pasted into Stata
they produce an unrecognised-command error, and the error is
**identical every time**, so it reads as one failure repeating rather
than a wrong window.

### 6. NEVER WRITE A PLAUSIBLE-LOOKING PATH

Three rounds were lost to invented example paths that read as real
ones. Write blanks that cannot be mistaken for real.

### 7. Restart Stata after any package change

Python initialises once per session and keeps the old package loaded.

### 8. THE TWO-PART UPDATE, which Git only half carries

The `.ado` files are in the repository and Git carries them. The
Python package lives inside Stata's Python and only `pip` puts it
there. A release that changes both fails with `ImportError: cannot
import name ...` if only one is updated. **Since 1.40.1 `equipop
doctor` detects this and says which half to update** — but say it
anyway when handing over a release.

---

## 7. WHAT THE STATA DOOR DOES, IN ONE PAGE

For a fresh session that needs to answer a user question quickly.

| box | what it does |
|---|---|
| `x() y()` | coordinates; metric, or degrees with `project` |
| `k()` | one or more neighbourhood sizes, in people |
| `r()` | one or more fixed radii — either `k()` or `r()` is enough |
| `treat()` | one column per group, holding the NUMBER OF PEOPLE |
| `treatmode()` | `counts` (default) or `flags` for the old 0/1 rule |
| `missing()` | values that mean NO DATA; blanked cases still count as people and still receive results |
| `pop()` / `[fweight=]` | the population at each point |
| `unit()` | cell size; whole and positive only |
| `selfpot()` / `selfpotname()` | how far a place is from itself; `none`, `median`, `full`, or any number 0–1 |
| `decay()` | `negexp`, `expnormal`, `expsqrt`, `lognormal`, `power`; adds `ND_`, `TD_`, `RD_` at each k **without changing k or the radius** |
| `halflife()` / `halflifevar()` / `bins()` | the bandwidth, fixed or per place |
| `overshoot()` | `whole` or `proportional`; `sampled` is refused by name |
| `project` / `epsg()` | lat/long to UTM, reporting the zone in `r(epsg)` and `r(crs)` |
| `prefix()` | a prefix on every new variable; all names checked before any is created |
| `if` / `in` | restrict the OUTPUT ROWS; excluded rows still count as neighbours |
| `replace` | overwrite existing result variables |
| `equipop doctor` | the environment report, including the `.ado` version against the engine version |
| `equipop setup` | installs the engine into the Python Stata is using; `setup, repair` reinstalls numpy, scipy and pandas for a wrong-processor mismatch |

**Any other bare word after `equipop` is refused by name**, with the
subcommands listed and the `net install` line — because the likeliest
cause is an .ado older than the subcommand being typed.

### WHY THERE IS NO .msi OR .pkg — asked and answered, v1.40.2

The hard part of installing EquiPop is not moving files. It is
targeting the PARTICULAR Python that Stata is configured to use, which
differs per machine and is what `python query` exists to discover at
run time. An OS installer would have to guess it, or bundle its own
interpreter and risk creating the two-copies-of-one-maths-library
conflict that closes Stata on Windows. It would also need an Apple
Developer ID and notarisation, a Windows signing certificate, and a
rebuild per release, per OS, per processor. `equipop setup` does the
job in two lines, identically on both platforms, with nothing to sign.
Do not reopen this without a new reason.
