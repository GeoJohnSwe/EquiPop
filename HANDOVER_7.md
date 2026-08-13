# EquiPop — HANDOVER 7
### written at the end of the 1.30 session (session 8)

**Supersedes HANDOVER_6.md**, which was written at the end of 1.29.5
and was three releases stale by the time it was read. Read this one;
6 is kept only for its history.

---

## 0. Start here

New session = upload this file plus one line: *"continue; next: X"*.
Claude clones GitHub main, reads this and `BACKLOG.md`, and works.
**Do not rely on Claude remembering anything.**

**Ask two questions before diagnosing anything:**

1. **Which versions are on the machine RIGHT NOW?** QGIS Python
   Console (it compiles a paste as ONE statement, hence the
   semicolons):
   ```python
   import equipop; print("package:", equipop.__version__); import equipop_qgis; print("plugin:", equipop_qgis.__version__)
   ```
2. **What changed between the run that worked and the run that did
   not?** Never assume nothing did.

---

## 1. Who John is, and what he wants from Claude

John Östh — OsloMet, with Lund and Uppsala. EquiPop is his software, a
reimplementation with Claude of his older C# tool. Geographer and
demographer, not a software engineer, non-native English speaker.
Write plainly about code and at full strength about statistics and
geography. **Say what a thing does before saying what it is.**

- **He rules quickly and overrules freely.** Numbered lists for
  decisions; he answers in kind, often in a few words.
- **Ask ONE question per point and make it answerable.**
- **HE WOULD RATHER HAVE A BUILD THAN A CONVERSATION.** His words,
  1.30: *"we spent most of last session discussing and not generating
  a gittable version - and I really want to test the machines for
  real."* When a decision is genuinely his, take a position, say
  which way you went, and let him overrule. Do not stack up questions
  and wait.
- **Budget his session credits.** He runs low late in the week and
  wants the remainder for field testing. **Build the artifacts EARLY
  rather than last** — in the 1.30 session Claude did all the work
  first and ran out of calls before packaging, so a finished release
  sat in a container John could not reach.
- **He pauses things decisively.** Do not quietly reintroduce them.
- **He values honesty over polish.** Say plainly when something is
  unverified, when a claim was wrong, or when Claude's own edit broke
  something.
- **He tests in the field, and the field is the truth.** When his
  report and Claude's reading of the code disagree, **John is right
  until something running proves otherwise.**
- **He publishes, then tests.** Few users, rollback is one command,
  more testers beats caution. Just make sure a release note says what
  changed.
- Design, coding and writing sessions are separate. He will say which.

---

## 2. State at the end of this session

**1.30 IS BUILT AND FULLY TESTED HERE. NOT field-tested, NOT
published.** **373 passed, 9 skipped** (345 passed / 2 failed when the
session opened).

**1.30 CHANGES NUMBERS** — every k-based number EquiPop has ever
produced — and the way back is one setting, `overshoot="whole"`.

### What 1.30 contains

**99 — THE OVERSHOOT, closed at both doors.** The engine half was
already wired when this session began; the two remaining reds were one
defect, *neither door could name a mode*, so both produced
`proportional` while the shipped answer key was pinned to `whole` and
the doors silently stopped matching it on 2287 of 2360 rows. Both
machines in both doors now carry the box, the shared help text and a
**seed field**. Three modes, John's ruling: `whole` (pre-1.30),
`proportional` (default, N_k exactly k), `sampled` (the original 2014
C# method, kept for fidelity, not because it is a better estimator).

**162 — a SECOND conformance key**, under the mode users actually get.
`equipop/data/gridby_reference_proportional.csv`: counts, shares and
distances only, because `proportional` refuses medians. `N_400` reads
exactly 400 in all 2360 rows. `reference.py` now takes a KEY NAME, so
a third key is one entry in `KEYS`.

**163 — BACKLOG 148 was half-shipped.** 1.29.6 added `population` and
`source` to `_manifest_rows`, wrote the reasoning into the docstring,
and **neither call site ever passed them**. 148's own complaint — that
Claude could not use two of John's manifests to settle which run had
differed — was still true after the fix. Now filled and read back by a
test broken three ways.

**139** — a diagonal step costs sqrt(2); iso-effort contours are round.
Was already done and unreleased when the session opened.

### Three findings worth carrying forward

1. **A default argument is the easiest place in this codebase for a
   feature to disappear.** That is 163 in one line, and it survived a
   release because the manifest test asked only for engine, k, cell
   size and version.
2. **A guard that drives the helper is not a guard on the door.**
   Claude's first seed test called `optional_int` directly; swapping
   the broken `parameterAsInt` back in left it perfectly green. Same
   shape as the 1.29.4 Pro guard that drove `_run_tool` and skipped
   the dialog hop. Rewritten through `processAlgorithm`, re-broken,
   caught.
3. **A test can assert something unreachable and look like coverage.**
   "Machine 2 is silent when the modes agree" can never happen — both
   modes machine 2 can run differ from machine 1's default, so the
   note fires on every run and only retires when 118 lands. The test
   was replaced, not weakened. John had approved that line on Claude's
   description, and the description was wrong.

### A zero-trap caught before it shipped

`parameterAsInt` returns 0 for an empty QGIS box, so an untouched seed
would have read as *seed 0* — every `sampled` run pinned to one draw
while announcing that none was given. `base.optional_int()` now
distinguishes empty from zero. BACKLOG 116's family.

### Still John's to do

Field-test **both doors** with `TESTING_1.30.md` — seven tests, and
Test 2 is the one that matters most: **set the box to `whole ring`
and re-run a 1.29.9 job; every number must be identical, not close.**
Then run `tools/stub_audit.py` in a **live QGIS** (BACKLOG 80 —
impossible from here); then commit, tag `v1.30`, push, publish.

**The install command must carry `--no-deps`.** Without it,
`--force-reinstall` reinstalls pandas, numpy, scipy and pyproj inside
QGIS's own Python — a well-known way to break a working QGIS.

**BACKLOG 101 is still John's.** Seven test-litter files are COMMITTED
to main (`C__/Data/`, `Instance=C_/Data/`,
`segregation_profile_HighEdu.csv`). Confirmed still reproducing: one
test run of the 1.30 tree regrew five of them in the working
directory, and they were deleted by hand before packaging.
`git rm -r --cached` on those paths.

---

## 3. What is next

`BACKLOG.md` — the top of the file answers "what next?" without
reading the rest. After 99/162/163 closed, the order stands as:

```
1. 161  Pro will not offer a barrier raster from the map. John
        field-found it; small, and it makes the barrier box behave
        like the DEM box. NOTE THE TRAP recorded in the item: adding
        GPRasterLayer alone produces a dropdown that then FAILS,
        because barrier rasters are read as DISPLAY TEXT. And the
        simulator cannot see any of it - test_arcgis_stub.py models
        valueAsText as str(value) and has no notion of multiValue,
        .values, semicolon joining or quoting. The stub must learn
        the real behaviour first
2. 102  QGIS has no bandwidth boxes; the 1.17 headline feature is
        missing from the door John teaches with. Travels with 42
3. 128  `equipop doctor` - one read-only diagnostic, every door
4. 129  version the output SEMANTICS, not just the structure
5. 117  one validated run specification, package and every door
6. 120  move reference/treatment construction into shared code -
        BACKLOG 108 existed because it is written twice. GATES 133
7.  38  CONTINENTAL RUNS - John's destination
8. 118  weighted statistics without person expansion. BLOCKER for
        38, and now ALSO the blocker for proportional in machine 2
```

**118 has become more valuable since 1.30.** It was already a hard
blocker for the continental machine (WorldPop counts are fractional;
the current code rounds each weight and repeats the row, so a 1 km
African run would try to materialise on the order of a billion rows).
It is now *also* what lets machine 2 take a fraction of a cell, which
would let both machines share one default and retire the note machine
2 prints on every run.

Three things about the code a fresh session would otherwise
rediscover slowly:

- **`equipop/bigrun.py` exists and is tested.** ORIGIN tiling with a
  GLOBAL tree, so results are exactly the untiled ones — no halos. At
  1 km, Africa's ~30 million cells fit in memory, so there is no edge
  problem at 1 km at all. It is unreachable from any door; that is
  the gap.
- **`equipop/raster.py` already reads WorldPop-shaped rasters** but
  re-bins lat/long onto a metric grid, which is the resampling item
  93's snapping rule exists to stop.
- **`equipop/projection.py` already decides by extent**, but its
  answer beyond two UTM zones is a compromise projection, not WGS84
  with great-circle. **John's ruling supersedes that branch.**

---

## 4. How Claude should work

### Release discipline
- **One release per conversation.**
- **BUILD THE ARTIFACTS BEFORE THE LAST QUARTER OF THE SESSION.** See
  section 1. A release John cannot download is not a release.
- Fetch code from GitHub; never work from memory of it.
- **Read the real text before editing it, and check the seams
  afterwards.** Blind string replacement has damaged `alg_counts.py`
  twice and `BACKLOG.md` twice. **Assert what you expect to find, and
  count the items when you are done** — the 1.30 backlog edit
  asserted 163 items before and 165 after, with the added and lost
  sets printed.
- **NEVER `git checkout` at all while work is uncommitted.** HEAD is
  the PREVIOUS RELEASE, so `git checkout -- one/file.py` silently
  throws away every change to that file. Save copies to /tmp before
  deliberate breakage and restore from those.
- **Break one rule per command, restore in the same command, verify
  green before the next one.** A timed-out command has left a file
  mid-breakage before, and the next command then saved the DAMAGED
  file as its "clean" reference.
- **Break every guard on purpose and watch it fail** — and break it
  at the level the USER meets it, not at the level the helper lives.
- Stage progressively; check deliverables by unpacking them.
- Unpack the archive into an EMPTY directory and run the suite from
  inside it.
- Version strings live in FOUR places; `test_packaging.py` asks the
  repository, not memory.
- Add a MANUAL version row every release.
- End every message with **"Next steps & questions"**.

### One environment note, so it is not re-diagnosed
`test_arcgis_stub.py::test_help_xml_covers_every_parameter` shells out
to `arcgis/make_help_xml.py`, which does `import equipop`. It fails in
a fresh container until `pip install -e .` is run. Not a defect.

### The doors
- **Parity of names is not parity of behaviour, and parity of boxes is
  not parity of menus.** `door_parity.py` compares box names;
  `LADDER_CASES` compares result columns. Neither can see a parameter
  that changes NUMBERS. That blindness produced 95, 102, 103 — and
  the rule it implies produced 99's door half: *a box that changes
  the answer belongs in CORE.* `seed` joined CORE in 1.30 for exactly
  that reason.
- **Add a rung, add a case.**
- A Pro parameter with no `category` floats to the TOP; add it to the
  SECTION map in the same edit. Pro parameters are addressed **by
  name, never by index**.
- Beware `_num(pm, "x", default) or default` — it eats a deliberate 0.
  The QGIS equivalent is `parameterAsInt` on an optional box.
- QGIS Processing has no sections and cannot grey a box out. The only
  grouping is Advanced. This is why `equipop/doors/rungs.py` exists —
  and **neither door may import the package to learn what its own
  dropdowns say** (BACKLOG 78/105). The duplication is pinned by
  `test_rungs.py`, which now reads six copies.

### Talking to John
- ONE-LINERS joined by semicolons for the QGIS console; verify they
  compile in `single` mode before sending.
- Number the snippets and ask for ALL of the output.
- When something misbehaves, write a SHORT snippet that prints which
  of two routes works, rather than reasoning about which it might be.
- Say plainly what has NOT been verified.

---

## 5. Open questions for John

1. **Field-test 1.30 in both doors** (`TESTING_1.30.md`). Test 2 —
   `whole ring` reproducing 1.29.9 exactly — is the one that would
   stop the release if it failed.
2. **Is machine 2's one-line overshoot note worth it?** It fires on
   every Value Statistics run and cannot fall silent until 118. He
   ruled it "the right call" on a description that turned out to be
   wrong about when it fires.
3. **The stub audit in a live QGIS** (80), result recorded in the
   MANUAL validation row.
4. **BACKLOG 101** — `git rm -r --cached` on the seven committed
   litter files.
5. **Item 43** — `CITATION.cff` still says 1.0.0. The author's to set.
6. **Item 41** — the reconstructed 1.17 MANUAL row has never been
   checked against what shipped.
