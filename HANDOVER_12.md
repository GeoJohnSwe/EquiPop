# EquiPop — HANDOVER 12
### written in the 1.40.5/6/7 session, SEVEN DAYS before the presentation

**Supersedes HANDOVER_11.md.** 11 is kept for its history and its
long findings list, which is NOT repeated here — read section 5 of 11
for how Claude should work, section 6 for the Stata environment, and
section 7 for what the Stata door does. Those three sections have not
changed and are still correct.

---

## 0. START HERE

```
https://github.com/GeoJohnSwe/EquiPop
```

Public, clones without credentials. Do not ask for a token.

```
head -8 pyproject.toml
```

**READ THE VERSION IN THE CLONE BEFORE PLANNING ANYTHING.** In the
1.40.5 session it matched the handover for once. Do not assume that
twice.

New session = upload this file plus one line: *"continue; next: X"*.

---

## 1. THE DEADLINE, AND WHAT IT MEANS NOW

**John presents WEDNESDAY 26 AUGUST 2026. Umut presents too, from a
Mac.** As of the 1.40.5 session that is seven days.

**John's ruling, this session: the Stata door is FROZEN for features
until after Bulgaria. Other doors and other topics stay open.**

So: no 1.41, no category boxes (`treatcat`/`refcat`/`outside`), no
Stata-into-`door_parity.py` this week. Those remain the right next
work and they are the wrong work for these seven days, because 1.41
touches the exact seam where the three doors have drifted before.
QGIS, Pro, docs and the R scoping are NOT frozen.

**THE ONE RISK THAT MATTERS: 1.37 through 1.40.5 — seven releases —
have never been run inside real Stata by anybody.** Everything below
is arranged around retiring that.

---

## 2. STATE AT THE END OF THIS SESSION

**1.40.5 built, archive-checked, handed over. 616 tests, 14 skipped,
run from inside the unpacked sdist.** 605 at the start of the session.

### Released this session

| | |
|---|---|
| **1.40.5** | 193 the field pass now ENFORCES; 201 block 17 asserted the decay models backwards; 107 MANIFEST omitted the field pass and the demos |

### What 1.40.5 actually changed

Nothing in the engine. Nothing in the `.ado` except the version
stamp. **This release is entirely about the instrument**, which is
why it was safe to ship in a freeze week.

- `equipop_test_pass.do` rebuilt. 57 checks, each printing `[ok]` or
  `[FAIL]`. **The count is PINNED** — a block that dies before
  reaching its checks is caught by the tally even when nothing raised
  an error. Every block is trapped separately so one failure cannot
  hide the other twenty-two. Exits 9 on any failure.
- The data path ships EMPTY, falls back to the working directory,
  and says so plainly if the file is absent. The old hard-coded
  `C:\Data\...` was a wall for anyone on a Mac.
- `tests/test_field_pass.py` parses the do-file and refuses: a block
  with no check, a refusal whose `_rc` nobody reads, a stale pinned
  count, a returned hard-coded path, a drifted version stamp,
  `ValFloat` back in `treat()`, and the old decay claim. **All seven
  broken on purpose; all seven caught.**

### THREE THINGS FOUND BY MEASURING RATHER THAN READING

1. **Block 17 asserted the decay models in the WRONG ORDER** (201).
   It expected `power` to keep more mass than `negexp` at the same
   half-life. Measured: power keeps LESS on 10,839 of 10,883 rows.
   **The shipped help text is CORRECT and was not the source** —
   "distant places never quite stop counting" describes the tail
   accurately. Both models are 0.5 at the half-life by construction,
   so that is where they CROSS: power is harsher inside the bandwidth
   and gentler outside it. At half-life 800 m, negexp gives 0.958 at
   50 m and 0.063 at 3,200 m; power gives 0.665 and 0.433. Which
   keeps more mass depends on where the NEIGHBOURHOOD sits, and here
   a k=300 neighbourhood has a median radius of 48 m against a
   half-life of 800 m. Both engines agree; this was never a code
   defect, only a wrong belief. **Do not re-open it, and do not
   "correct" the help text — the help is right.**
2. **Block 20 was invalid AND halted the pass** (193), so blocks 21
   and 22 — the refusals and the `r()` results — had never run in the
   field at all. Rebuilt on a synthetic count column with `-999` on
   every twelfth row: deliberate, not random, so it is exactly 907
   rows on every machine and every Stata version.
3. **The sdist never carried the field pass** (107). Caught by the
   archive check: 11 failures inside the unpacked `.tar.gz`. The
   instrument the whole release is about had never travelled in a
   source archive.

### John's rulings this session

1. **Stata frozen for features until after Bulgaria; other topics
   continue.**
2. **The presentation is Wednesday 26 August.** The trip is partly
   floating; that date is not.
3. **Umut's Mac is working, and he may already have results.**

### Rulings carried forward — all of HANDOVER 11 section 3 still
stands, unchanged. `treat()` means counts; ship a correctness fix
immediately; projection is for the beginner; the run must say which
projection it used; wide data gets a note and proceeds; decay does
not choose the neighbourhood; `overshoot(sampled)` refuses by name;
three rungs on the self-potential ladder; words not numbers for every
Stata option; quantiles interpolated; a share divides by the OBSERVED
part; `if`/`in` restrict output rows only.

---

### THE FIRST REAL STATA RUN SINCE 1.36 — 1.40.5 ON WINDOWS

John ran it the same day. **All 57 checks executed; the pinned tally
matched exactly; two failed.**

- **Block 0, engine 1.40.4 against commands 1.40.5.** Not a defect:
  the `.ado` files came from the zip and the engine from PyPI, which
  still held 1.40.4. **The doctor caught it and explained it.** 1.40.5
  changed no engine code at all, so every number in that log is valid
  evidence for the engine — **this run retired the seven-release
  unverified-in-Stata risk for 1.37 through 1.40.4.**
- **Block 4 asked for a column that has never existed** (202). Fixed
  in 1.40.6, do-file only, so the freeze holds.

**Every measured threshold matched the Python probe to the decimal**
— ratio 47.03, `w_N_200` mean 999.08, `R_Grp_200` mean 0.4939, 907
sentinels, 10,743 inside-bandwidth rows and zero exceptions on the
corrected block 17. Reproducing the door's call through
`stata_bridge.py` is therefore a trustworthy oracle for writing
thresholds, which is worth knowing before the next field script.

**And the design earned itself on its first outing.** Under the old
file, block 4's `confirm` would have raised an error and stopped the
pass, hiding the eighteen blocks after it. Trapped, it cost one line
and the other 55 checks still ran.

### THE SECOND FIELD RUN — THE WRONG FILE, AND THE BEST FIND OF THE DAY

John ran `stata/equipop_showcase.do` from his dev folder by mistake.
**It crashed at section 6 and had been crashing for many releases.**

`Data.store(c, None, [v if isfinite(v) else None ...])` — Stata
refuses `None` for a numeric. That is BACKLOG 173, whose fix
`to_stata_values()` has been in `equipop_run.ado` since 1.40.1. The
showcase never adopted it. **Two** crash sites, so sections 7 and 8
had never run in Stata at all, and their EXPECT numbers had never in
the file's life been compared with anything. Section 4 was also
demonstrating the 47x `treatmode` trap instead of the `pop()` feature.
The file called itself "EquiPop 1.1".

**NOTHING TESTED IT BECAUSE NOTHING READ IT.** That is the whole
lesson, and it is not about Stata. `tests/test_field_pass.py` now
walks EVERY shipped `.do` file, refuses the `None`-store pattern, and
compiles every `python:` block.

**And it exposed a real gap — BACKLOG 205.** The `equipop` command has
no `stats()` option: machine 2 is unreachable from Stata except by
hand-written `python:` blocks. That is why section 6 exists at all,
and **it also explains block 20 of the field pass** — whoever wrote
`treat(ValFloat) missing(0)` was not being careless, they were
reaching for the only handle the door offers. A Stata user with a
continuous variable has nowhere correct to put it. Sizeable, and not
for this week.

## 3. FINDINGS ADDED THIS SESSION

All of HANDOVER 11's findings 1–24 still hold. These are new.

25. **A STATED INVARIANT THAT NOBODY HAS COMPUTED IS A BELIEF, NOT A
    GUARD.** Block 17 sat in the file for many releases asserting the
    opposite of what the code does, and would have been "confirmed"
    by eye. It is finding 14 arriving from the other direction: there,
    the test expected the obvious thing and the HELP was wrong; here,
    the *pass* expected the obvious thing and the pass was wrong.
    Before trusting any number written in a field script, reproduce
    it through the engine.
26. **REPRODUCE THE DOOR'S CALL, NOT A CALL THAT LOOKS LIKE IT.** The
    first probe passed `decay="power"` as a string to `dispatch()`,
    which has no `decay` parameter — it vanished into `**extra` and
    every model returned identical numbers. The `.ado` builds a real
    `Decay` object and calls `knn_to_rows`. **Read the call site in
    the `.ado` before writing a probe**, or the probe measures
    something else and says so confidently.
27. **A PROBE THAT HAS NOT BEEN VERIFIED AGAINST A KNOWN-GOOD FILE IS
    WORTH NOTHING.** The first parser for `test_field_pass.py` split
    the do-file on its separator lines and reported all 22 blocks as
    unchecked — the separator appears twice per block, so headers and
    code landed in different chunks. It was the probe that was wrong.
    This is finding 18 in a new costume.
28. **A TEST WRITTEN FOR ONE REASON CAN BE THE GUARD FOR ANOTHER.**
    `test_the_do_file_is_present` was written as a formality. It is
    what caught the MANIFEST gap, because a test that READS a shipped
    file cannot pass in an archive that lacks it. Prefer tests that
    read the artifact over tests that assert about it.
29. **WRAP EACH BLOCK, DO NOT HALT THE PASS.** A field round trip
    costs a day. With seven days left, a run that stops at the first
    problem buys one fact; a run that traps each block and ends with
    a verdict buys all of them. The pinned check count is what makes
    the trapped version safe — without it, a block dying early is
    indistinguishable from a block passing.

---

## 4. WHAT IS NEXT

```
1. FIELD-TEST 1.40.5, BOTH PLATFORMS. Nothing else counts until this
      is done. John first, on Windows, because a syntax slip in the
      do-file should cost an hour rather than a day of Umut's time.
      Then Umut on the Mac.
      NOT VERIFIED BY ANYTHING IN THIS REPOSITORY: the do-file's
      Stata syntax. The braces balance, the sfi one-liner compiles in
      `single` mode, and every threshold was measured through
      stata_bridge.py - but Stata syntax is only proved by Stata.
      Expect: 57 of 57 checks, verdict PASSED.
      If the tally is lower than 57, a block died early; the reason
      is above it in the log.

2. SAVE THE LOGS AS RELEASE ARTIFACTS. Proposed and awaiting John:
      logs/field_pass_1.40.5_windows.log and _mac.log in the repo, so
      "field-tested on both platforms" has two files behind it.

3. THE PRESENTATION RUN ITSELF - not yet built, and nothing in
      HANDOVER 11 named it. A Bristol do-file that runs start to
      finish on both machines: `project` reporting EPSG:32619, then
      k(300) with decay(negexp) so ND_300 sits beside N_300 - the
      visible proof that decay weights the population without moving
      the neighbourhood.
      THE CAVEAT THAT BELONGS ON THE SLIDE: the ACS attributes vary
      at BLOCK-GROUP resolution and are back-filled to 1,074 blocks,
      so a Gini over them measures dispersion between 37 area medians,
      not between households, and understates household inequality.
      It is also the argument for the method: the k-neighbourhoods cut
      across those 37 boundaries and the source geography cannot.

--- after the conference, in this order ---
4. 189/190  THE TWO WRITE RISKS. An analytical feature is not
      delivered if the door can report success with empty result
      columns. The read-back must compare against the values about to
      be written, not merely check that the fields exist.
5. STATA INTO door_parity.py - BEFORE the category rung, not after.
      Deferred by HANDOVER 8, 9, 10, 11 and now 12; 172 is the bill.
6. 1.41  THE LAST TWO BOXES, through a SHARED helper.
      - treatcat(varname) treatspec("A: 5, 6, 7; B: 1, 2")
        refcat(varname)   reftypes("...")
        COMMAS ARE REQUIRED. parse_treat_spec splits groups on ';'
        and values on ','. The form without commas parses to
        {'A': ['5 6 7']} and matches ZERO ROWS, silently.
      - outside(zero|null) IS INPUT SHAPING, NOT POST-PROCESSING.
        zero - contributes ZERO to the reference population and is
               nobody's neighbour, but REMAINS AN ORIGIN and receives
               the real results for what surrounds it.
        null - contributes nothing AND receives no results.
        Build the membership mask, multiply the reference count by it
        (QGIS does `weight = base * pop_mask` in alg_counts.py), keep
        the coordinates for zero, mask the origin for null, THEN run.
      - Three rules the GIS doors have and Stata must not lose: read
        STRING categories without forcing them through the numeric
        _col(); multiply a category's 0/1 membership by the count
        field; preflight empty group names, case-clashing output
        names, and groups matching zero rows.
7. 198  A QGIS INSTALLER. --no-deps is NOT optional inside QGIS's
      managed stack. Fix README_QGIS.md's contradicting advice in the
      same edit.
8. 199  ArcGIS Pro cannot have an engine installer; detect and
      instruct instead.
9. 200  AN R VERSION OF MACHINE 1. Native, not reticulate. Do not
      estimate before 195.
10. 128-doors / 168-doors / 161 / 102 / 118 / 38 - as HANDOVER 11.
```

### Still John's to do

- **Push 1.40.5**, and upload it to PyPI. **`equipop setup` depends on
  the PyPI upload** — it runs `pip install equipop`, so a release that
  is not on PyPI cannot be installed the easy way. 1.40.4 IS on PyPI;
  keep that unbroken.
- **`git rm -r --cached tmp` ONCE.** Exactly one file is still tracked
  under `tmp/`. The `.gitignore` rule went in at 1.40.2, so this time
  the removal will stay done.
- **Commit HANDOVER 9, 10 and 12** to the repo root. Only 6, 7, 8 and
  11 are there. Handovers travel in the COMPLETE ZIP but deliberately
  not in the PyPI sdist — they are internal working notes and the
  repository is where they belong.
- Field-test 1.40.5 and send the log.

---

## 5. THE THINGS A FRESH SESSION REDISCOVERS SLOWLY

Unchanged from HANDOVER 11, and still true:

- **`equipop/bigrun.py` exists and is tested.** ORIGIN tiling with a
  GLOBAL tree. Unreachable from any door; that is the gap.
- **`equipop/raster.py` reads WorldPop-shaped rasters** but re-bins
  lat/long onto a metric grid.
- **`equipop/wstats.py` is the weighted-statistics core.** Whole-number
  weights reproduce the person expansion exactly. Do not relax that
  without saying so loudly.
- **The import rule**: `equipop/__init__.py` must not gain a
  module-level `from .x import y`. Guarded in a subprocess by
  `tests/test_lazy_imports.py`.
- **Version strings live in EIGHT places.** `pyproject.toml`,
  `equipop/__init__.py`, `qgis/equipop_qgis/__init__.py`,
  `qgis/equipop_qgis/metadata.txt`, `stata/equipop.ado` **line 1 AND
  the `local eqp_ado_version`**, `stata/equipop.pkg` line 2, and
  `CITATION.cff`. **A NINTH now follows them**: the field pass stamps
  the version twice — its `*!` header and `global EQP_EXPECT` — and
  `test_field_pass.py` asserts both against `pyproject.toml`.
  `stata/equipop.ado` line 116 says "ruling, 1.40.4" as HISTORY and
  must NOT move; any bump script needs an anchor that cannot match it.
- **Regenerate the help after any option change**:
  `python tools/make_sthlp.py`. The suite fails until you do.
- **Unpack the archive into an EMPTY directory and run the suite from
  inside it.** It has now earned itself three times.
- **End every message with "Next steps & questions".**

---

## 6. HOW TO WRITE TO JOHN

Unchanged, and it is the thing that makes the sessions work.

> **Plain words for anything about code. Full technical strength for
> statistics, geography and method.**

John Östh — OsloMet, with Lund and Uppsala. Geographer, demographer
and spatial analyst, **not a programmer**, non-native English speaker.

- He rules quickly and overrules freely. Numbered lists; he answers
  in kind, often in a few words.
- **ONE question per point, and make it answerable.**
- **He would rather have a build than a conversation.** Take a
  position, say which way you went, let him overrule.
- **BUILD ARTIFACTS EARLY** and `present_files` the complete zip, the
  wheel and the `.tar.gz`.
- **He tests in the field, and the field is the truth.** When his
  report and Claude's reading of the code disagree, John is right
  until something running proves otherwise.
- **He values honesty over polish.** Say plainly what has NOT been
  verified. This session had three of Claude's own probes come back
  wrong before the finding was right; saying so cost nothing.
- LABEL EVERY SNIPPET `[Stata]`, `[Command Prompt]` or
  `[Mac Terminal]`, and **NEVER WRITE A PLAUSIBLE-LOOKING FILE
  PATH**.
