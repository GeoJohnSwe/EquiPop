# EquiPop — HANDOVER 13
### written at the end of the continental session

**Supersedes HANDOVER_12.md.** 12 is kept for the Bulgaria week and its
findings 25–29. **Sections 5 and 6 of HANDOVER 12 have not changed and
are not repeated here** — read 12 §5 for what a fresh session
rediscovers slowly, and **12 §6 for how to write to John, which is the
thing that makes these sessions work.**

---

## 0. START HERE

```
https://github.com/GeoJohnSwe/EquiPop
head -8 pyproject.toml
```

**READ THE VERSION IN THE CLONE BEFORE PLANNING ANYTHING.**

New session = upload this file plus one line: *"continue; next: X"*.

---

## 1. STATE

**The working tree is at 1.40.7 and NOTHING IS RELEASED from this
session — John's decision, and it still stands. 654 tests pass**, up
from 605 at the start of the previous session.

Bulgaria is done with as a deadline. The Stata door was field-tested by
John on Windows and came back **57 of 57 PASSED**.

### Uncommitted work in the tree, all engine-side

| | |
|---|---|
| `equipop/rasterfolder.py` | NEW. Folder of rasters → one point table → `CellData` |
| `equipop/cells.py` | `build_cells(weights=...)`, `CellData.value_weights` |
| `equipop/analysis.py` | fractional weights honoured instead of row counts |
| `equipop/raster.py` | point set is now the UNION over layers, zeros kept |
| `tests/fixtures/worldpop/` | 1.1 MB, three clipped WorldPop rasters |
| `tests/test_worldpop_fractional.py` | 7 tests, BACKLOG 118 |
| `tests/test_rasterfolder.py` | 19 tests, BACKLOG 206 |
| `tests/test_window_sensitivity.py` | 2 tests, BACKLOG 207 |
| `equipop_demo_bristol.do` | the Bristol presentation run |

---

## 2. WHAT WAS DONE

### 118 — fractional weights, engine side. HALF DONE.

`build_cells(weights=...)` carries a weight column into
`CellData.value_weights`; `run_knn_stats` sums weights per distinct
value instead of counting rows. **Empty by default, so no existing
caller moves** — `test_without_weights_nothing_moves` pins that.

**Measured on John's WorldPop rasters, and THREE quantities were being
conflated.** The first version of the test asserted the wrong one and
failed, correctly:

| | places lost | people in them | net mass |
|---|---|---|---|
| Burundi | 85.0% | 52.9% | 40.1% |
| Rwanda | 78.2% | 39.3% | 28.5% |
| Austria | 98.3% | 66.5% | 60.1% |
| Denmark | 98.1% | 69.1% | 58.6% |

**The first column is the one that matters and it is the worst.** A
pixel rounding to zero stops being an origin AND stops being anybody's
neighbour, so the map loses the *location*, not merely the headcount.
Net mass understates the damage, because round-ups compensate. Every
measure worsens with latitude, so Europe-against-Africa was biased by
construction.

**STILL OPEN: `stata_bridge.py:738` still expands rows into persons.**
That is the Stata door only. The continental path goes through
`build_cells` and `run_knn_stats` directly and is now unblocked.
Rewiring the door changes behaviour for existing Stata users, so it
wants its own session and its own release.

### 206 — the folder loader. DONE, engine side.

`equipop/rasterfolder.py`, built to **John's rule, which is about
geometry rather than filenames**:

> different ground does not overlap → **ROWS**
> the same ground does overlap → **COLUMNS**

That is measurable, so the merge survives any renaming. **THE TEST IS
DATA OVERLAP, NOT EXTENT.** Burundi and Rwanda share a bounding box
over 1.4M cells and do not share ONE pixel carrying data in both; an
extent-based merge would add two countries into one column.

Naming degrades in three tiers — a registry of known conventions, then
a user regex or explicit dict, then the filename stem — and says out
loud when it fell through. **The merge never consults any of it.**

**ZEROS ARE KEPT (John, explicitly).** The point set is the UNION over
every layer, so a pixel with no women aged 15–19 but three men survives
with a real `0.0`. `raster.py` had the identical defect — it chose the
point set from whichever variable was listed *first* — and is fixed.

**Age bands are not all five years:** `0` is under-one alone, `1` covers
1–4, then fives, then an open `90+`. `band_width(90)` returns `None`, so
cohorts can be **summed** but never averaged or differenced across bands
without the widths. It refuses rather than guesses.

Verified on all four real rasters: **11,562,095 points, one column
`f_15_2020`, latitude −4.469 to 57.750, mass conserved exactly at
1,721,880.**

### 38 — bigrun wired to the raster path. FIRST RUN DONE.

`folder_to_cells()` in `rasterfolder.py`. Burundi + Rwanda, 1 km,
k=[100,1000]: 3.9M points → **46,317 cells**, tiled run **38.9 s in 34
tiles, 1.5 MB on disk**; untiled reference 9.7 s. Tiling is slower at
this scale and exists for the scale where the untiled run does not fit.

---

## 3. THE FINDING THAT MATTERS — BACKLOG 207

**`Dist_k` depends on the search window, and the ladder cannot catch
it.** Untiled, identical data, only `m_neighbors` changed:

- auto (m=104, widened to 832) vs m=4096 → **249 of 46,317 rows differ
  in `Dist_1000`, max 168.79 m**, with `N_1000` **exactly 1000 in both**
- m=4096 vs m=16384 → **0 rows differ.** The answer converges by 4096;
  `auto_m_neighbors` picked 104.

Worst origin reports 6,598.03 m where the converged answer is 6,429.24 m
— **a neighbourhood reported larger than it is.**

**Why the ladder misses it:** `fastcounts.py:344` re-solves only origins
that FAIL TO REACH k. An origin that reaches k out of slightly too-far
people has a complete count and never enters the ladder. The guarantee
in that comment — *"results are unchanged either way"* — holds for `N_k`
and **not** for `Dist_k`.

0.54% of origins, and they are the sparse far-reaching ones — precisely
the rural population a continental run exists to describe. Everything
built on `Dist` inherits it: variable bandwidths (block 19 of the field
pass takes its bandwidth from `Dist_400`), density, any decay whose
half-life comes from the radius.

**This partly reinstates 93.** Claude told John the "fails silently"
worry was stale because the ladder guaranteed correctness. John was
right that positional error from degree cells is negligible — great
circle gives true metres, 0.1–0.4% sphere-against-ellipsoid — but the
WINDOW concern was real and was conceded too fast.

**Not yet diagnosed: the mechanism.** Suspect the proportional overshoot
interpolating inside the crossing ring, whose shape changes as more
cells become available. **Read `_solve` before touching anything.**

---

### 207 IS FIXED — AND IT WAS NOT A DISTANCE DEFECT

`ring_bounds()` walked forward with `while hi + 1 < n`, where n is the
**fetched window**, not the ring. A crossing ring running off the edge
was treated as complete, so its share was measured against whichever
part happened to fit. **The radius and every group share built from
that ring were wrong**; `N_k` stayed exactly k, so no guard fired.

Measured before the fix: a four-cell lattice ring seen two cells wide
gave `Dist_11` = 200.0 m against a true 173.2; Burundi + Rwanda at
500 m moved a cross-border share to **0.043 against a converged
0.065**. Not monotone in m — 34 rows moved at 32, 426 at 64, 33 at 128
— so **no larger default would have fixed it**; detection was the only
route.

The fix defers such an origin to the ladder that already existed for
the other reason. Every window from 32 to 2048 now agrees exactly.
Cost is self-limiting: 8,745 of 8,798 origins widen at m=32, 291 at
128, none at 512.

**John's ruling: continental and possibly global, so correctness over
speed.** And his second ruling: **207 before the doors** — a door is a
window onto the engine, so fix the view first.

**WHY THE FIRST REPRODUCTION FAILED, and it is the transferable part:**
it used RANDOM POINTS, which never tie, so every "ring" was one cell
and could not be cut. WorldPop is a LATTICE. Reading the mechanism in
`ring_bounds` first and then building the case deliberately took one
attempt.

## 3b. HOW WORK IS DELIVERED — A STANDING RULE

**JOHN'S RULING, after an afternoon lost to an ArcGIS Pro install:**
"I wish that we can use one general method for uploading and running
and stick to it through the sessions."

**EVERY SESSION THAT CHANGES CODE ENDS WITH FOUR FILES, BUILT AND
VERIFIED, NAMED BY VERSION:**

    equipop-<ver>-py3-none-any.whl     the engine
    equipop-<ver>.tar.gz               source, for PyPI
    equipop_qgis-<ver>.zip             the QGIS plugin
    EquiPop.pyt                        the ArcGIS Pro toolbox

plus the working-tree zip for the repository. Git carries the history
— John runs `git add -A`, commit, push, and that works. **Git is not
the install route.** Building a wheel from a clone is another
Python-shell operation, and the Python shell is exactly what keeps
failing.

**NEVER ASK HIM TO INSTALL FROM A FOLDER OR FROM PyPI WHILE TESTING.**
A folder install needs a shell to be in the right place; a PyPI
install cannot be distinguished from the local build by version number
alone — that ambiguity has now cost two full round trips.

**INSTALL.md IS THE ONE DOCUMENT.** Three hosts, one verify line, and
the shell-versus-Python check at the top, because a `SyntaxError` on a
pip command means the user is typing into Python and NOT that anything
is wrong with the package. That is what happened in Pro, five times in
one log.

**AND SAY WHAT IS UNTESTED, IN BOLD.** There is no arcpy in this
environment, so no Pro instruction has EVER been executed here. Claude
gave Pro steps four times in numbered form, reading as though
verified. They were read from documentation. The honest label is
"hypothesis", and the cost of omitting it fell entirely on John, who
is not a programmer and had no way to know.

## 4. FINDINGS ADDED

All of HANDOVER 11 §5 and HANDOVER 12 §3 still hold. These are new.

30. **A GUARANTEE IN A COMMENT IS A BELIEF UNTIL SOMEBODY COMPUTES IT.**
    `fastcounts.py` says "results are unchanged either way" and it is
    true of the count and false of the distance. Finding 25 again, one
    level deeper: it is not only *stated invariants in test scripts*
    that rot, it is confident comments in the engine.
31. **CONCEDING TOO FAST IS ITS OWN FAILURE MODE.** John's argument
    against the latitude worry was right in its own terms, and Claude
    generalised it into striking a concern that was separately real.
    Agreeing with the person is not the same as checking. **Concede the
    part that is proven and keep the part that is untested.**
32. **THREE QUANTITIES CAN HIDE IN ONE NUMBER.** "Rounding deletes 50%"
    conflated places lost, people in those places, and net mass. They
    differ by 30 percentage points and only one of them is the point.
    Before quoting a proportion, say **of what**.
33. **A TEST THAT XPASSES IS TELLING YOU YOUR REPRODUCTION IS WRONG.**
    The synthetic case for 207 xpassed; random points with a sparse tail
    do not reproduce it. The reproduction recipe is in the test file
    instead. **A defect nobody can reproduce cheaply gets fixed by
    guesswork.**
34. **THE PROJECT'S OWN RECORD ALREADY WARNED ABOUT THE pip DAMAGE.**
    HANDOVER 6 recorded that `--force-reinstall` without `--no-deps`
    reinstalls pandas, numpy, scipy and pyproj — "a well-known way to
    break a working QGIS". Claude then did exactly that to John's Stata
    Python, from inside a live Stata session, and broke pyproj. **Never
    run pip against an interpreter a running program has loaded.** On
    Windows the DLLs are memory-mapped and cannot be replaced. Close the
    program first, and drop `--force-reinstall` unless a package is
    actually broken.

---

35. **A GREEN TEST CAN BE AS WRONG AS A RED ONE.** BACKLOG 208's
    manifest test passed on Linux for years while writing its file into
    a junk relative tree, because every assertion it made was still
    true there. Only Windows made it visible. When a test passes on one
    platform and fails on another, suspect the PASS.
36. **BUILD THE REPRODUCTION FROM THE MECHANISM, NOT FROM GUESSES AT
    DATA.** Random points could not reproduce 207 and no amount of
    re-rolling would have. Reading `ring_bounds` first said exactly
    what the case needed - exact distance ties - and the lattice
    followed in one attempt.
37. **CHECK WHICH COPY IS IMPORTED.** Three editable installs in one
    session meant `import equipop` silently resolved to an unpacked
    archive, and a probe failed on a signature that was right in the
    tree. `inspect.getfile(equipop)` before believing any measurement.

## 5. WHAT IS NEXT

```
1. 38-PRO  REGISTER THE PRO TOOL, ONCE IT CAN BE TESTED. The class is
      written and sits on the same run_folder as QGIS; self.tools does
      not list it. Extend tests/test_arcgis_stub.py to cover a
      DEFolder box and NumPyArrayToFeatureClass, THEN register. Do not
      register on a reading.

2. 207-was  Dist_k MOVED WITH THE SEARCH WINDOW - DONE, see above.
      Old entry kept for the shape of it: Correctness, and it
      poisons every derived measure. Find a cheap reproduction FIRST,
      then read _solve. Do not guess at auto_m_neighbors.

2. 118  THE STATA HALF. stata_bridge.py:738 still expands rows into
      persons. Behaviour-changing for existing Stata users, so its own
      session and its own release.

3. 38   THE GUI ON TOP OF folder_to_cells(), in the Q and Pro doors.
      John: "one ring to rule them all" - ONE function, several doors.
      Do not reimplement the merge rule per door; that is how the
      doors have drifted every time before.

4. 149  suggest_projection() SPLITS TOO EAGERLY - confirmed live this
      session. Burundi+Rwanda span zones 35 (59%) and 36 (41%) and it
      recommends two runs; the split falls through the middle of both
      countries. A single zone costs 0.17%.

5. 93   THE WORKING FRAME. No great-circle frame exists, so an
      Africa+Europe run in one frame is not possible today. Each
      continent alone is fine.

--- then, from HANDOVER 12 ---
6. 189/190 the two write risks. 7. Stata into door_parity.py.
8. 1.41 the last two boxes. 9. 198 QGIS installer. 10. 199 Pro.
11. 200 R. 12. 203 should a radius run report a distance at all?
13. 205 THE STATA DOOR CANNOT REACH MACHINE 2 AT ALL - no stats()
      option exists, which is why block 20 of the field pass had
      treat(ValFloat) in it. A user with a continuous variable has
      nowhere correct to put it.
```

### Still John's to do

- **Push 1.40.7 and upload it to PyPI.** `equipop setup` runs
  `pip install equipop`, so an unpushed release cannot be installed the
  easy way. PyPI still holds 1.40.4.
- **`git rm -r --cached tmp` ONCE.** Exactly one file still tracked.
- **Commit HANDOVER 9, 10, 12 and 13** to the repo root. Only 6, 7, 8
  and 11 are there.
- Field-test on Umut's Mac — still the only untested platform.
