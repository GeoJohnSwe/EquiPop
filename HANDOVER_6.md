# EquiPop — HANDOVER 6
### written at the end of the 1.29.5 session

---

## 0. Start here

New session = upload this file plus one line: *"continue; next: X"*.
Claude clones GitHub main, reads this and `BACKLOG.md`, and works.
**Do not rely on Claude remembering anything.**

**Ask two questions before diagnosing anything:**

1. **Which versions are on the machine RIGHT NOW?** QGIS Python Console
   (it compiles a paste as ONE statement, hence the semicolons):
   ```python
   import equipop; print("package:", equipop.__version__); import equipop_qgis; print("plugin:", equipop_qgis.__version__)
   ```
2. **What changed between the run that worked and the run that did
   not?** Never assume nothing did.

---

## 1. Who John is, and what he wants from Claude

John Östh, Uppsala University. EquiPop is his software — a
reimplementation, with Claude, of his older tool. Geographer and
demographer, not a software engineer, non-native English speaker.
Write plainly about code and at full strength about statistics and
geography. **Say what a thing does before saying what it is.**

- **He rules quickly and overrules freely.** Numbered lists for
  decisions. He answers in kind, often in a few words.
- **Ask ONE question per point and make it answerable.** In this
  session he twice said "not sure what you are asking" — both times
  Claude had buried a question inside a statement. If a question needs
  a decision, write it as a question.
- **He pauses things decisively.** Do not quietly reintroduce them.
- **He values honesty over polish.** Say plainly when something is
  unverified, when a claim was wrong, or when Claude's own edit broke
  something.
- **He tests in the field, and the field is the truth.** When his
  report and Claude's reading of the code disagree, **John is right
  until something running proves otherwise.**
- **He publishes, then tests.** Reverted deliberately in 1.29.5: few
  users, rollback is one command, and more testers is worth more than
  caution. Do not argue him back out of it; just make sure a release
  note says what changed.
- Design, coding and writing sessions are separate. He will say which.
- He is aware of session cost and dislikes friction between sessions,
  so work long in one conversation.

---

## 2. State at the end of this session

**1.29.8 IS BUILT AND FULLY TESTED HERE. NOT field-tested, NOT
published.** 338 passed, 6 skipped (279 when this run of work began).

**1.29.6 closes THIRTEEN items, all from John's ArcGIS Pro field
evening, and changes NO NUMBERS** - every one is a guard, a message or
a refusal: 131, 135, 136, 138, 140, 141, 142, 143, 144, 145, 146, 147,
148. See the MANUAL version row for the detail.

**1.29.8 is the first release since 1.29.3 that CHANGES NUMBERS**, and
all three changes are opt-out: run_knn gained self-potential (153),
Gini refuses negatives (154), and cell size must be a whole number of
MAP UNITS - not metres, because nothing ever read the CRS's linear
unit and a survey-feet projection was labelled wrong by 3.28 (155,
160). Reading a .zip no longer globs the folder beside it (157).

**Neither 1.29.4 nor 1.29.5 was ever published.** 1.29.6 is the first
release intended to reach PyPI since 1.29.3. That matters for one
decision already taken: self-potential became a three-way CHOICE
rather than a free number (141), which was safe only because no saved
model anywhere holds the old numeric parameter.

**It now also carries GATE A of an external review.** John had another
model review the 1.29.4 build. Claude checked eighteen of its claims
against the code; **all eighteen held**, including one critical defect
Claude had read past twice and three that Claude had introduced. Eight
were fixed here (items 108-115), and three more followed (105, 116,
121). The full assessment is in `REVIEW_RESPONSE_1.29.4.md`; the brief
for the next review is in `REVIEWER_BRIEF.md`.

**Seventeen items closed in 1.29.5**: 79, 94, 95, 96, 103, 104, 105,
108-116, 121.

**A SECOND external document arrived**, on distribution and publishing
routes (SSC, the QGIS plugin repository, ArcGIS Online, the SPSS
Extension Hub). Its platform research is the part we could not have
done ourselves. Its repository findings were checked: most hold, one
was already fixed (the icon, 79) and one was WRONG (`license=MIT` has
been in metadata.txt since before 1.29.3). Logged as items 128-134.

**Its premise needs qualifying, and this matters for planning.** It
opens by saying EquiPop already keeps computation in the package and
the doors thin. That is the INTENT. We now know the doors compute -
BACKLOG 120 - and that BACKLOG 108, a silent corruption that survived
eight published releases, existed precisely because the reference and
treatment logic is written twice and only one copy was fixed. **A
fourth door is a fourth place for the next 108 to hide, so 120 is now
a prerequisite for any new door rather than a tidy-up.**

The single most important finding: **the QGIS door discarded the
population field whenever outside rows were Nulled**, from 1.21 until
now, published the whole time. Two rows carrying 10 and 1 people
reported N_5 = 2 instead of 11. No test drove that combination -
breaking the fix on purpose changed nothing until a guard was written.

**1.29.4 NEVER EXISTED.** It was built, John field-tested self-potential
from it, then ruled that everything be renumbered to 1.29.5 as if .4
had never happened. Nothing was ever committed or tagged for it. Every
file says 1.29.5.

- Archive check done: sdist unpacked into an empty directory, whole
  suite run from inside it, 310 passed, all four version strings
  correct **in the archive**.
- Artifacts: sdist, wheel, QGIS plugin zip (now carrying `icon.png`),
  and a complete repository zip.

### John's field test of self-potential — PASSED

Four runs on his own data, 682 points, k=400:

| run | Dist_400 in dense cells |
|---|---|
| cell 100, selfpot 0 | 316.23 / 223.61 / 282.84 |
| cell 100, selfpot 1 | **identical** — no cell holds 400, nothing fires |
| cell 1000, selfpot 0 | **0** — the old defect, visible |
| cell 1000, selfpot 1 | **302.111985780** (predicted 302.111985781) |

`N_`, `T_` and `R_` byte-identical across selfpot 0 and 1: the setting
moves the radius and nothing else, as designed.

### Where the work goes next, in words

**The next release makes the doors safe and changes NO numbers.**
Everything the 1.29.5 Pro field test found belongs in one release,
because it is all guards, messages and refusals - low risk, and worth
doing while the findings are fresh.
- THE WRITE PATH. Three different write failures in one evening (a
  held file, group names colliding on case, nulls in a shapefile) all
  ended identically: two pointless retries, a message blaming OneDrive
  with certainty, and "Nothing was changed" when three fields had
  already been written. Stop retrying refusals that are not locks;
  make the reassurance true or drop it; stop naming a cause with
  certainty; refuse impossible combinations BEFORE computing; and
  where a target cannot take the write, copy to a new feature class
  and say so (John's ruling).
- PRO'S DIALOG does not guard the user the way QGIS now does: an empty
  box on a chosen rung runs silently, one type-field box is free text
  while its twin is a picker, settings survive layer and rung changes,
  and the "verified present" check confirms what was COMPUTED rather
  than what was ASKED FOR.
- LABELS AND MESSAGES: case-colliding group names, the bandwidth boxes
  that bury what they want, the self-potential report naming the
  calibration k, and every door announcing itself as "[stata]".
- THE MANIFEST, which omits the population definition, the keepoutside
  rung and self-potential, and names the copy as its input.

**The release after that changes numbers, and the three parts travel
together** because they touch the same code: the sqrt(2) diagonal cost
(clean break, John's ruling); the overshoot as a three-way choice with
proportional as default, radial and effort alike; and self-potential as
a named choice rather than a free number. All three need the treatment
self-potential got - a setting, a default, an exact way back, a loud
MANUAL row.

**Then the continental machine.** Two things BLOCK it rather than
accompany it: weighted statistics that do not expand rows into people,
and a resumable run that validates its own parameters. Plus the
multi-country data path - concatenate the extracted cells, never mosaic
the rasters.

**THE CONTINENTAL DATA QUESTION IS NOW SETTLED**, on real WorldPop
files John supplied (Burundi + Rwanda, f_15, 2020, 100 m). Everything
item 137 left open has been checked rather than assumed:
- the two country rasters share ONE lattice exactly - same CRS, same
  3-arc-second pixel, origins differing by whole pixels. No
  resampling needed.
- they DO NOT OVERLAP: of 1.4 million cells in the shared bounding
  box, ZERO carry data in both files. So no border rule is needed
  and a straight concatenation cannot double-count.
- concatenation is NECESSARY, not merely cheaper: at 1 km with
  k=1000, 1,330 of 46,317 origins draw from both countries, covering
  25,359 women 15-19. Run the countries apart and those women get
  half a neighbourhood in silence.
- and it exposed a NEW defect (149): suggest_projection() recommends
  splitting this 2-degree extent because it straddles a zone
  boundary, when a single UTM zone costs 0.17% - less than the
  sphere-vs-ellipsoid error already accepted. The split would fall
  through the middle of both countries.
NOT yet tested: the latitude-varying cell width of 93. These two
countries sit within 4.5 degrees of the equator so width varies by
0.29%, against a factor of 1.25 across Africa. That needs a
NORTH-SOUTH pair.
A 1 km fixture (46,317 cells, 639 KB) was cut from this and is worth
keeping as the continental machine's first regression test.

**Unfinished from the field test:** Test 6 alone - the population field
surviving both keepoutside routes, run into two FRESH feature classes
in a geodatabase. Everything else passed or is logged.

### Still John's to do

Field-test **Pro**; run `tools/stub_audit.py` in a **live QGIS**
(BACKLOG 80 — impossible from here); then commit, tag `v1.29.5`, push,
publish. `TESTING_1.29.5.md` is the manual for it.

**The install command must carry `--no-deps`.** Claude's first version
of that manual omitted it, and `--force-reinstall` alone would have
reinstalled pandas, numpy, scipy and pyproj inside QGIS's own Python —
a well-known way to break a working QGIS.

---

## 3. What 1.29.5 contains

**95 — SELF-POTENTIAL.** John's term, from accessibility research. Own-
cell people sat at distance 0, so wherever one cell held k people
`Dist_k` was 0 and **k stopped being a parameter** (`N_100 = N_1000 =
3,002`, both distances 0, no message). Rule: `d = s·√(A·k/(n·π))`,
default **1.0** by John's ruling; `s=0` reproduces pre-1.29.5 numbers
exactly, and that is asserted by a test. Lives once in
`equipop/selfpot.py`; decay gets the same setting on a different scale
(`0.3826c`). Validated against truth: 0.18% out at k=100, 0.09% at
k=1000.

**96 — the self-calibrating bandwidth** (the 1.17 headline) was
silently substituting the dataset median wherever `Dist_k` was 0 — the
urban core got a rural kernel, and the printed range was the range
*after* substitution. Fixed by 95; now warns with a count and a
percentage.

**94 — N_k overshoot** reported by both engines through one shared
function.

**104 — the rung-to-box mapping**, from John's own field run. He chose
treatment rung 1 and filled box 2a, which served rung 2: the run gave
`N_100` and `Dist_100`, no `T_`, no `R_`, **no message**. Cause was
ordering — a,b,c served rung 2 and d served rung 1, so rung 1's box was
last. Three answers shipped: each rung names its box ("fill 2a"); box 2
reordered so `treat` is now **2a**; and a box the rung ignores says so
while a rung with an empty box refuses. **In both machines** — machine 2
had the identical silence. Wording shared in `equipop/doors/rungs.py`.

**103 — QGIS machine 2 offered six statistics, Pro twelve.** Now
eleven, in Pro's order, `variance` mapped to the engine's `var` in one
place. Percentiles were never missing — separate box.

**79 — icon.png**, promised in `metadata.txt` since the first release
and never once shipped. Now exists, plus a test that metadata may not
name a file the plugin does not carry.

**80 — partial only.** `stub_audit.py` now explains itself and exits 2
instead of raising `ModuleNotFoundError`. The item itself **cannot ever
be closed by Claude**: it needs real PyQGIS, so it is John's on every
release, permanently.

---

## 4. What is next

John, this session: *"after this 1.29.5 has been tested and validated,
plus potential PRO things in adjacent versions — we should press on
with the continental run and machine 3."*

`BACKLOG.md` — 40 open items. Top six:

```
1. 102  QGIS has no bandwidth boxes; the 1.17 feature is missing
        from the door John teaches with. Travels with 42
2. 117  one validated run specification, package and every door
3. 120  move reference/treatment construction into shared code -
        BACKLOG 108 existed because it is written twice
4.  38  CONTINENTAL RUNS - John's destination
5. 118  weighted statistics without person expansion. BLOCKER for 38
6. 119  resume must validate its parameters and fingerprint inputs
```

**118 is a hard blocker for the continental machine, not a risk.**
WorldPop counts are FRACTIONAL, the current code rounds each weight
and repeats the row that many times, and a 1 km African run would try
to materialise on the order of a billion rows before the engine
starts. It has to be done before 38, not alongside it.

**The continental dialog design is written into BACKLOG item 38** —
three tools (prepare / run / collect), the measure driving raster
selection, split by GROUP not sex, k as a list with per-cohort
overrides, self-calibrating bandwidth for sparse cohorts. John:
*"let us go with these tools, but let us develop them in the rounds to
come so let us not lock in at this point."* **Agreed, not frozen.**

Three things about the code a fresh session would otherwise rediscover
slowly:

- **`equipop/bigrun.py` exists and is tested.** ORIGIN tiling with a
  GLOBAL tree, so results are exactly the untiled ones — no halos. At
  1 km, Africa's ~30 million cells fit in memory, so **there is no edge
  problem at 1 km at all**. Halos arrive only at 100 m. It is
  unreachable from any door; that is the gap.
- **`equipop/raster.py` already reads WorldPop-shaped rasters** and
  keeps only populated pixels — but re-bins lat/long onto a metric
  grid, which is the resampling item 93's snapping rule exists to stop.
- **`equipop/projection.py` already decides by extent**, but its answer
  beyond two UTM zones is a compromise projection, not WGS84 with
  great-circle. **John's ruling supersedes that branch.**

And the honest cost of 93: the engine is metric all the way down —
midpoints, grid flooring, tile sizes, and the fast pass's search window
all assume metres and a uniform cell. WGS84 is not a switch.

---

## 5. How Claude should work

### Release discipline
- **One release per conversation.**
- Fetch code from GitHub; never work from memory of it.
- **Read the real text before editing it, and check the seams
  afterwards.** Blind string replacement has damaged `alg_counts.py`
  twice. In this session two of Claude's own backlog edits went wrong:
  one landed a line late and split an item in half; the other
  swallowed item 80 whole, because 79 and 80 had no blank line between
  them and the edit searched for `\n\n`. Both were caught only by
  verifying afterwards. **Assert what you expect to find, and count
  the items when you are done.**
- **NEVER `git checkout` at all while work is uncommitted**, not even
  with an explicit path. The old rule said "never repo-wide, use an
  explicit path list" and that is not strong enough: HEAD is the
  PREVIOUS RELEASE, so `git checkout -- one/file.py` silently threw
  away every 1.29.5 change to that file. It happened in this session
  and was recovered only because a staged build still had a good copy.
  Save copies to /tmp before deliberate breakage and restore from
  those.
- **A timed-out command may leave a file mid-breakage.** One
  break-and-restore loop hit the execution limit between the break and
  the restore, and the next command then saved the DAMAGED file as its
  "clean" reference. Break one rule per command, restore in the same
  command, and verify green before the next one.
- **Break every guard on purpose and watch it fail.** In 1.29.4's work
  one guard was worthless: a Pro test drove `_run_tool` directly and
  passed against a deliberate break, because the trap was one hop
  earlier in `execute()`.
- Stage progressively; check deliverables by unpacking them.
- Unpack the archive into an EMPTY directory and run the suite from
  inside it.
- Version strings live in FOUR places; `test_packaging.py` asks the
  repository, not memory.
- Add a MANUAL version row every release.
- End every message with **"Next steps & questions"**.

### The doors
- **Parity of names is not parity of behaviour, and parity of boxes is
  not parity of menus.** `door_parity.py` compares box names;
  `LADDER_CASES` compares result columns. Neither can see a parameter
  that changes NUMBERS, and neither can see the CONTENTS of a dropdown.
  Three gaps this week from that one blindness (95, 102, 103).
- **Add a rung, add a case.**
- A Pro parameter with no `category` floats to the TOP; add it to the
  SECTION map in the same edit. Pro parameters are addressed **by name,
  never by index**.
- Beware `_num(pm, "x", default) or default` — it eats a deliberate 0.
- QGIS Processing has no sections and cannot grey a box out. The only
  grouping is Advanced, and Advanced does not advertise what is inside.
  This is why `equipop/doors/rungs.py` exists.

### Talking to John
- ONE-LINERS joined by semicolons for the QGIS console; verify they
  compile in `single` mode before sending.
- Number the snippets and ask for ALL of the output.
- When something misbehaves, write a SHORT snippet that prints which of
  two routes works, rather than reasoning about which it might be.
- Say plainly what has NOT been verified.

---

## 6. Lessons this session added

1. **A parameter fixed at a value is still a parameter.** Self-potential
   was not added in 1.29.5; it had been there from the beginning, set
   to zero, with no box, no name and no mention.
2. **A guard that drives the shortest path may skip the danger.**
3. **Some duplication cannot be removed, only pinned.** BACKLOG 105
   looked like a simple case of two doors keeping their own copy of
   the same wording. Removing it broke BACKLOG 78: QGIS imports a
   plugin at STARTUP, so a module-level `import equipop` kills the
   whole plugin when the package is missing, before there is any
   algorithm to attach a message to. Neither door may reach into the
   package to learn what its own dropdowns say. When a fix meets a
   constraint like that, pin the duplication with a test and RECORD
   WHY, or the next reader will try the same fix again.
4. **Design that lives only in the handover will be lost.** Items 92,
   93, 89, 90 and 91 were designed a session earlier and never reached
   the repository — five of seven logged items had vanished.
5. **A report that fires only when a problem is rare hides it when it
   is common.** The self-calibration printed its range after
   substituting, so 50% substitution looked like a healthy spread.
6. **Boxes ordered by letter rather than by rung will be filled
   wrongly, and by the author of the software first.**
7. **`--force-reinstall` without `--no-deps` is dangerous inside
   QGIS's Python.** It reinstalls the four libraries QGIS is built on.
8. **A fix without a guard is half a fix.** Two of Gate A's eight
   were fixed and then survived a deliberate re-break untouched,
   because no test existed for them. Always break the fix, not just
   the rule.

---

## 7. Open questions for John

1. **Pro field test of 1.29.5**, especially Test 5 in
   `TESTING_1.29.5.md` — the self-calibrating bandwidth at
   self-potential 0 then 1. Those two message blocks are the only place
   BACKLOG 96 can be seen, since QGIS has no such box.
2. **The stub audit in a live QGIS** (80), result recorded in the
   MANUAL validation row.
3. **BACKLOG 101** — seven test-litter files are COMMITTED to main
   (`C__/Data/`, `Instance=C_/Data/`, `segregation_profile_HighEdu.csv`,
   committed in 1.29.3, 1.22 and 1.5.1). `git rm -r --cached` on those
   paths is John's to run.
4. **Items 99 and 100** (last-cell interpolation, `MedDist_k`) are
   logged and deferred with his agreement.
5. **Item 43** — `CITATION.cff` still says 1.0.0. The author's to set.
6. **Item 41** — the reconstructed 1.17 MANUAL row has never been
   checked against what shipped.
