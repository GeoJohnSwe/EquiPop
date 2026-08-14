# EquiPop — HANDOVER 8
### written during the 1.30 → 1.33 session, with a conference deadline

**Supersedes HANDOVER_7.md**, which described 1.30 and predates items
164–169. 6 and 7 are kept only for their history.

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

## 1. THE DEADLINE — read this before planning anything

**John presents at a conference in Bulgaria in the LAST WEEK OF
AUGUST 2026.** He wants a Stata version ready for it. That governs
priority until it is done or the date passes.

**SSC listing will not happen in that window** — submission goes
through Kit Baum and turnaround is weeks. The target is `net install`
straight from the GitHub repo, which needs the same `.pkg` and
`stata.toc` files and is live the moment he pushes. SSC afterwards.

### What he ruled the Stata door must contain — machine 1 ONLY

His words: *"the simple answer is - only machine 1 since that is the
one thing genuinely missing in Stata."*

- both reference and treatment population selections (the ladders)
- k and radius specification
- decay modelling — but NOT friction, effort, slope, FCA, LISA
- `whole` and `proportional` overshoot. **`sampled` is NOT needed** —
  cut it, and refuse `overshoot(sampled)` by name with a pointer to
  QGIS/Pro rather than ignoring it. Dropping it also drops the need
  for a seed option, which is a real saving
- self-potential and variable cell size
- **transformation of lat/long to a useful projection is a MUST.**
  His reason: *"Most stata users are not good at these things so
  forcing them to project may be a big usage blocker"*
- the command is **`equipop`**, not `equipop_knn` — his call, because
  radius runs exist and asking for a radius under a `_knn` name reads
  oddly. Keep `equipop_knn` working as an alias so nothing he has
  already written breaks

### What already exists on the Stata side

`stata/equipop_knn.ado` **is machine 1 already**, at v1.0 — `N_`,
`Dist_`, `T_`, `R_`. So this is a CATCH-UP, not a new door. Missing
from it: both ladders, `keepoutside`, decay, the overshoot box, the
self-potential three-rung ladder (Stata still has it as a free
number), missing-value codes, and projection. `stata_test_data.dta`
ships. **There are no `.sthlp` files at all** and no `stata.toc`/
`.pkg`.

**Stata sits outside `door_parity.py` entirely** — the file whose
whole job is to stop doors drifting. It has drifted; that is how
`selfpot` ended up a free number there and a ladder everywhere else.
Bring Stata under parity as part of this or it will drift again.

### The demo dataset

`DataBristolCounty2022_filled.xlsx` — 1,074 census blocks in 37 block
groups, Bristol County, Rhode Island, 50,793 people. Complete: age
(`B01002`), race (`B02001`), median household income (`B19013`),
population, lat/long. A `.dta` conversion was handed to John already.

Two things to know about it:
- **`B19013_E001` carries the Census sentinel `-666666666` in 64 rows
  (6%)**, and 64 more are top-coded at `250001`. This is what BACKLOG
  168 was built for.
- **The ACS attributes vary at BLOCK-GROUP resolution**, back-filled
  to blocks — 34–36 distinct values across 1,074 rows. Not a flaw: it
  is the argument for the method, since k-neighbourhoods cut across
  those 37 boundaries while the source data cannot. It also means a
  Gini over it measures dispersion between area medians, which
  understates household inequality.

---

## 2. Who John is, and what he wants from Claude

John Östh — OsloMet, with Lund and Uppsala. EquiPop is his software, a
reimplementation with Claude of his older C# tool. Geographer and
demographer, not a software engineer, non-native English speaker.
Write plainly about code and at full strength about statistics and
geography. **Say what a thing does before saying what it is.**

- **He rules quickly and overrules freely.** Numbered lists for
  decisions; he answers in kind, often in a few words.
- **Ask ONE question per point and make it answerable.**
- **HE WOULD RATHER HAVE A BUILD THAN A CONVERSATION.** His words:
  *"we spent most of last session discussing and not generating a
  gittable version - and I really want to test the machines for
  real."* When a decision is genuinely his, take a position, say
  which way you went, and let him overrule.
- **Budget his session credits, and BUILD ARTIFACTS EARLY.** In the
  1.30 session Claude did all the work first and ran out of calls
  before packaging, so a finished release sat in a container he could
  not reach.
- **He publishes, then tests.** Few users, rollback is one command.
- **He tests in the field, and the field is the truth.** When his
  report and Claude's reading of the code disagree, **John is right
  until something running proves otherwise.** Every one of items 164,
  165, 166 and 168 came from his field testing, not from the suite.
- **He values honesty over polish.** Say plainly when something is
  unverified, when a claim was wrong, or when Claude's own edit broke
  something.

---

## 3. State at the end of this session

**1.33 is built and fully tested here. Field-tested only through
1.31.** 435 tests.

### Released this session

| | |
|---|---|
| **1.30** | THE OVERSHOOT (99) closed at both doors; second conformance key (162); manifest finished (163) |
| **1.30.1** | 164 — a new feature class received every result ONE ROW EARLY, silently, since v1.20 |
| **1.30.2** | 165 truncation warning asked about the input; 166 manifest invisible inside a `.gdb`; 167 stub audit surface stale |
| **1.30.3** | 118 arithmetic — `wstats.py`, proven identical to the expansion for whole weights |
| **1.31** | 118 wired — machine 2 takes a fraction of a cell, refusal gone, both machines share one default |
| **1.32** | 168 — missing-value codes, and the observed-part denominator |
| **1.33** | 169 — the projection argument-order trap |

### John's rulings this session, so they are not re-litigated

1. **Quantiles are INTERPOLATED, not stepped.** His reason is the
   good one: EquiPop already averages the two middle values for an
   even count, and that average IS a linear interpolation.
2. **Warn when a value variable has far fewer distinct values than
   rows** (Gini understating within-cell inequality). Agreed but
   **NOT YET IMPLEMENTED** — see BACKLOG.
3. **Missing codes**: the cause is unimportant, the ability to
   exclude matters. A blanked case *"could still be the placeholder
   for results - it just doesn't contribute self"*.
4. **A share divides by the OBSERVED part**: 400 people, 60 of
   unknown group → denominator **340**, never 400.
5. **Overshoot labels are short and the word "recommended" is gone**
   from both machines — it was actively wrong in machine 2, where it
   recommended the one option that machine refused.
6. **Sidecar CSVs go to an `EquiPop_runs` folder** beside the
   container, not beside the `.gdb`, to avoid scattering the project
   folder.
7. **Single-zone projection is acceptable**, with a brief note in the
   help that distances "float" for distant areas — negligible for
   nearest-neighbour work. **The help note is NOT YET WRITTEN.**

### Four findings worth carrying forward

1. **A default argument is the easiest place in this codebase for a
   feature to disappear.** BACKLOG 148 shipped a `population`
   parameter that no call site ever passed, and survived a release
   because the manifest test asked only for engine, k, cell size and
   version.
2. **A guard that drives the helper is not a guard on the door.**
   Happened twice more this session.
3. **A test can assert something unreachable and look like
   coverage.** And a test with a bad FIXTURE is worse: three
   deliberate breaks of the 118 wiring all passed, because every cell
   in the fixture held the same value and the median could not move.
4. **Guessing at performance is a waste of turns.** Two wrong guesses
   at a 2.5× slowdown; the profiler found it in one call — cell-
   identity hashing done in every overshoot mode when only `sampled`
   reads it. 207s → 79s.

### Still John's to do

- **BACKLOG 101** — litter files are still COMMITTED to main.
  `git rm -r --cached` on `C__/Data/`, `Instance=C_/Data/`,
  `segregation_profile_HighEdu.csv`. They regrow on every test run and
  the release-zip guard has refused a build twice because of them.
- **Item 43** — `CITATION.cff` still says 1.0.0.
- Field-test 1.32/1.33 once the doors carry the missing-code box.

---

## 4. What is next

```
1. 168-doors  the missing-code box in Pro, QGIS and Stata
2. STATA DOOR the whole of section 1 above - the deadline
3. 161        Pro will not offer a barrier raster from the map.
              NOTE THE TRAP: adding GPRasterLayer alone produces a
              dropdown that then FAILS, and the simulator cannot see
              it - test_arcgis_stub models valueAsText as str(value)
              and has no notion of multiValue, .values or quoting
4. 102        QGIS has no bandwidth boxes. Travels with 42
5. 118-rest   the expansion UPSTREAM, where counts become persons.
              This is what unblocks 38, and it is a pipeline change
6. 38         CONTINENTAL RUNS - John's destination
```

Three things about the code a fresh session would rediscover slowly:

- **`equipop/bigrun.py` exists and is tested.** ORIGIN tiling with a
  GLOBAL tree, so results are exactly the untiled ones. At 1 km,
  Africa's ~30 million cells fit in memory. It is unreachable from
  any door; that is the gap.
- **`equipop/raster.py` reads WorldPop-shaped rasters** but re-bins
  lat/long onto a metric grid, which is the resampling item 93's
  snapping rule exists to stop.
- **`equipop/wstats.py` is the weighted-statistics core.** Its
  contract is that whole-number weights reproduce the person
  expansion exactly. Do not relax that without saying so loudly.

---

## 5. How Claude should work

### Release discipline
- **One release per conversation** — though this session shipped
  seven, because field reports kept arriving. That is fine when each
  one is built, archive-checked and handed over.
- **BUILD THE ARTIFACTS BEFORE THE LAST QUARTER OF THE SESSION.**
- **Read the real text before editing it. PARSE BEFORE WRITING.**
  `cells.py` was corrupted this session by an edit whose anchor
  matched the wrong `):`, and the file was written before
  `ast.parse` ran. Recovery came from the unpacked sdist. **Take a
  copy of `equipop/` to /tmp before a run of edits.**
- **Anchors must be unique AND unambiguous.** Two edits this session
  landed in the wrong function because the indentation of the anchor
  matched a different one first. Assert `count == 1` and check WHICH
  one.
- **NEVER `git checkout` while work is uncommitted.** HEAD is the
  PREVIOUS RELEASE.
- **Break every guard on purpose and watch it fail — at the level the
  USER meets it**, not at the level the helper lives.
- Unpack the archive into an EMPTY directory and run the suite from
  inside it.
- Version strings live in FOUR places.
- Add a MANUAL version row every release.
- End every message with **"Next steps & questions"**.

### One environment note, so it is not re-diagnosed
`test_arcgis_stub.py::test_help_xml_covers_every_parameter` shells out
to `arcgis/make_help_xml.py`, which does `import equipop`. It fails in
a fresh container until `pip install -e .` is run. Not a defect.

### The doors
- **A box that changes the ANSWER belongs in `CORE`** in
  `door_parity.py`. That rule produced 99's door half, and `seed`
  joined CORE in 1.30 because `sampled` makes it analytical.
- **Parity of names is not parity of behaviour.** `door_parity`
  compares box names; `LADDER_CASES` compares result columns. Neither
  can see a parameter that changes numbers.
- A Pro parameter with no `category` floats to the TOP; add it to the
  SECTION map in the same edit. Pro parameters are addressed **by
  name, never by index**.
- Beware `_num(pm, "x", default) or default` — it eats a deliberate 0.
  The QGIS equivalent is `parameterAsInt` on an optional box, which
  returns 0 for empty; use `base.optional_int()`.
- **A stub is safe only where it is STRICTER than the real thing.**
  Three times now a generous simulator has certified a door that could
  not run: 1.29.1 `isAdvanced`, 1.29.3 polygon barriers, and 1.30.1
  `CopyFeatures` keeping the input's identifiers.
- Neither door may import the package to learn what its own dropdowns
  say (78/105). The duplication is pinned by `test_rungs.py`.

### Talking to John
- ONE-LINERS joined by semicolons for the QGIS console; verify they
  compile in `single` mode before sending.
- Number the snippets and ask for ALL of the output.
- Say plainly what has NOT been verified.
