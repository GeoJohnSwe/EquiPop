# The 1.29.4 external review — what I verified, and what to do

Written after checking the review against the code rather than reading
it. Reproductions were run where a reproduction was possible; where it
was not, I say so.

---

## 1. Verdict

**I checked eighteen claims. All eighteen held.** Nothing I tested was
wrong, overstated in a way that mattered, or an artefact of reading a
stale tree. That is an unusually high hit rate and it should change how
much weight we give the document: this is not a list of suggestions to
triage, it is a defect report.

Three of the findings are **mine, introduced in this release**. One is a
critical defect I read past twice while working in the same function.

The review's headline recommendation — *do not build continental
functionality on this snapshot unchanged* — I now agree with. Its other
headline, *do not publish*, needs one correction that the reviewer could
not make without git access, and I give it in §4.

---

## 2. What I verified, and how

| # | claim | how checked | result |
|---|---|---|---|
| 1 | QGIS discards population weights on one route | **reproduced** | **holds** |
| 2 | Negative raster facilitators discarded | read `friction.py:750` | holds |
| 3 | Self-potential ignored by friction/slope | signature of `run_knn_friction` | holds |
| 4 | Effort `Dist_k` depends on row order | read `friction.py:293-301` | holds |
| 5 | Resume never validates parameters | read `bigrun.py:79-100` | holds |
| 6 | Weighted stats expand rows into persons | read `stata_bridge.py:444` | holds |
| 8 | Friction graph built twice | read — literally duplicated verbatim | holds |
| 9 | Stata cannot select self-potential | zero matches in either `.ado` | holds |
| 10 | QGIS lacks variable bandwidth | already logged by us as 102 | holds |
| 11 | Stats tally double-counts on fallback | **reproduced** | **holds** |
| — | No `isCanceled` in the QGIS door | grep | holds |
| — | Cell size 0 silently becomes 100 | read `alg_counts.py:232` | holds |
| — | `fetch` caches on filename only | read `fetch.py:38` | holds |
| — | `README_QGIS` says features are absent | read — three of four now exist | holds |
| — | `MANUAL.md` calls itself 0.3.1 | read | holds |
| — | `MANUAL_BEGINNER` says 1.7 | read | holds |
| — | Package docstring says "no friction, no decay yet" | read | holds |
| — | `CITATION.cff` still 1.0.0 | read — already our item 43 | holds |

Two reproductions worth showing.

**Population weights.** Two included rows carrying 10 and 1 people,
k=5, reference population restricted by type:

```
keepoutside = "give them results, counting as zero" : N_5 = [11, 11]   correct
keepoutside = "leave their results Null"            : N_5 = [ 2,  2]   wrong
```

The second branch sets the weight to the Boolean mask, so every
included row counts as one and the population field is thrown away. No
message. The same code in Value Statistics is correct.

**My own tally.** 514 real origins, with the neighbour search forced to
widen:

```
TRUE origins (cells): 514
[selfpot] k=300: ... 1 of 1,511 origins ...
```

`_walk()` is called again on every retry and my counter sits inside it.
So the denominator in the report I added to end silences is itself
wrong whenever the search widens.

---

## 3. Three of these are mine

I want these named rather than folded into a list.

**Self-potential is ignored the moment a run switches to effort.** I
added the box to both doors and threaded the value through the counts
and stats engines. I did not thread it through friction or slope, and
`run_knn_friction()` has no such parameter. The box stays visible and
fillable when barriers or terrain are set, and does nothing. That is
precisely the failure this release existed to end — a box that is
filled and ignored — reintroduced by the release that ended it.

**Stata cannot reach the old behaviour.** Both `.ado` commands inherit
the new default of 1.0 with no option to set 0. So the one route I made
sure was reproducible in both GIS doors is unreachable from the door
John's published work goes through.

**My origin tally double-counts.** Above.

The common thread: I threaded a new parameter through the paths I was
looking at and did not enumerate the paths I was not. There is no test
that asserts *every engine* honours it, and there should be.

---

## 4. The one correction the reviewer could not make

The reviewer recommends holding 1.29.4 from publication because of the
population-weight defect. Without git access they could not check when
it entered.

**It entered in 1.21 and is present in the released 1.29.3, live on
PyPI today.** So it is not a reason to hold 1.29.5 — it is already out
there, and 1.29.5 does not make it worse. It is a strong reason to
follow quickly with a correctness release.

That said, publishing 1.29.5 while knowing this would mean shipping a
version whose headline is *we ended a silence* alongside a louder one
we have just confirmed. My recommendation is in §7.

---

## 5. Already answered in 1.29.5

The review is of 1.29.4, so some of it is done:

- **Plugin icon** — shipped, plus a test that metadata cannot promise a
  missing file (79).
- **Rung-to-box silence** — the defect that cost John a field run;
  fixed in both machines (104).
- **QGIS statistics menu** — six options became eleven (103).
- **Stub audit** — explains itself instead of raising
  `ModuleNotFoundError` (80, partial; the item itself never closes).
- **Test writes outside tmp** — logged as 101, including the seven
  files committed to main.
- **QGIS variable bandwidth, and parity comparing menu contents** —
  logged as 102 and 105, independently found.

---

## 6. Where I would qualify or extend

**Effort `Dist_k` (finding 4) has a defensible right answer**, not just
a product decision. `Dist_k` means *the radius that was required to
reach k*. For an equal-effort ring accepted atomically, that is the
**maximum straight-line extent of the accepted ring** — the smallest
circle that contains everyone counted. Minimum understates it; `ring[-1]`
is input order and is not a quantity at all. I would propose max and let
John overrule, rather than open the question.

**Person expansion (finding 6) is a hard blocker for the continental
machine**, not merely a risk for large runs. WorldPop cells hold
*fractional* counts. Rounding them is a second silent error — a cell
holding 0.4 people becomes 0 — and a 1 km African run would try to
materialise on the order of a billion rows before the engine starts.
This has to be fixed before 38, not alongside it.

**"Exactly the untiled result" is defensible but under-stated.** The
*computation* is exact; the float32 conversion is a storage choice, and
the test's tolerance reflects that. The docstring should say so rather
than the claim being withdrawn.

**Resume validation (finding 5) is cheaper than the review implies.**
The manifest already records the parameters. It needs a comparison on
resume and a refusal on mismatch, plus a fingerprint of the input
coordinates and weights. That is an afternoon, not a project.

**The disclosure-control question deserves elevating.** The reviewer
frames it as an optional profile. For Swedish register work it is the
difference between a tool that can be used inside a protected
environment and one that cannot. Small k, `N_local`, and exact
percentiles on register microdata are disclosure risks. This is John's
domain, not mine, and it is the one item where I would want his ruling
before any design.

**The `or default` idiom is a systematic hazard, not four bugs.** Cell
size 0 becomes 100; I nearly shipped self-potential 0 becoming 1. Any
parameter whose zero is meaningful is at risk. Worth one sweep and one
lint rule rather than case-by-case fixes.

---

## 7. Proposed action list

Numbers continue from the current backlog (max 107). Nothing has been
logged yet — this is the proposal.

### Gate A — correctness, before anything else *(one release)*

| item | what | effort |
|---|---|---|
| **108** | QGIS discards population weights when outside rows are Nulled. Since 1.21, live on PyPI. **Reproduced.** | hours |
| **109** | Negative raster values are filtered out before the facilitator check, so raster facilitators silently do nothing | hours |
| **110** | Self-potential is ignored by friction and slope. *Mine.* Either implement it or refuse loudly — silent acceptance must not remain | 1–2 days |
| **111** | My origin tally double-counts on search fallback. *Mine.* | hours |
| **112** | Friction graph and coverage warning built twice, verbatim | minutes |
| **113** | Stata: no self-potential option, and decimal radii use the unsanitised name. *Partly mine.* | hours |
| **114** | A test that asserts **every engine** honours self-potential — the gap that let 110 and 113 happen | hours |

### Gate B — semantics that need a ruling *(one release)*

| item | what |
|---|---|
| **115** | Effort `Dist_k` on an equal-effort ring. My proposal: maximum straight-line extent of the accepted ring. **Needs John's ruling.** |
| **116** | The `or default` sweep — every parameter whose zero is meaningful |
| **117** | A shared validated run specification used by the package and every door: positive finite k, radii, cell size; non-negative counts; decay sanity; refusal rather than substitution |

### Gate C — before the continental machine

| item | what |
|---|---|
| **118** | Weighted statistics without person expansion — exact weighted median, percentile, Gini, mean, variance on values plus weights. **Blocker for 38.** |
| **119** | `bigrun` resume must validate a canonical parameter set and an input fingerprint, and verify tile hashes before skipping. State float32 honestly, or default scientific columns to float64 |
| **120** | Move reference and treatment construction out of both doors into shared package code. 108 exists because that logic is duplicated |

### Gate D — documentation, which now actively misleads

| item | what |
|---|---|
| **121** | `README_QGIS.md` says decay, barriers, terrain and grouping are unavailable in QGIS; three of the four exist. `MANUAL.md` says 0.3.1, `MANUAL_BEGINNER` says 1.7, `FUNCTION_MATRIX` says 1.5.1, the package docstring says "no friction, no decay yet". Users cannot tell what exists |

### Gate E — product decisions, John's alone

| item | what |
|---|---|
| **122** | Disclosure control for register data: minimum k, suppression of `N_local` and thin results, redaction of absolute paths, a recorded note that suppression was applied. **Needs a ruling before design** |
| **123** | `RunLog` and ArcGIS manifests record absolute paths, usernames and OS details; sharing them may disclose institutional structure |
| **124** | `fetch` caches by filename only, so two URLs sharing a basename collide; archive extraction is unbounded |

### Gate F — quality of life

| item | what |
|---|---|
| **125** | QGIS cancellation: no `isCanceled()` anywhere, and progress only moves during output writing |
| **126** | `_convert()` loses a text category whenever any value in the column parses as a number |
| **127** | Value Statistics does not call the version-mismatch warning that Counts and Shares does, and shadows `wanted` between measures and reference categories |

---

## 8. What this says about how we work

Three observations I would rather write down than let pass.

**A second reader found things a first reader could not.** I have been
inside `alg_counts.py` repeatedly this week — I edited the function
containing finding 1 twice — and did not see it. Familiarity with a file
is not the same as reading it. A periodic outside review is worth
scheduling, not just accepting when offered.

**Threading a parameter is not the same as covering the paths.** All
three of my defects have one shape: I followed the routes I was already
looking at. The remedy is a test that enumerates engines rather than
one that tests the engine in front of me — proposed as item 114.

**Our guard tests keep passing while the software is wrong**, and this
is now a pattern with a name. `door_parity` compares box names.
`LADDER_CASES` compares result columns. Neither sees numbers. This week
alone that let through the bandwidth gap, the statistics menu, and
finding 1 — a numerical defect in a combination no test drives. Item
105 was already logged for menus; it should be widened to numbers.

**One thing to keep.** The review's own confidence column distinguishes
*reproduced* from *confirmed in code*, and every reproduced item held
when I re-ran it independently. That is the same discipline this project
uses, arriving from outside, and it is the reason the document is worth
this much of our time.
