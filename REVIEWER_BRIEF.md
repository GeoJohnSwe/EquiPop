# Brief for the external reviewer

For the next review of EquiPop. Written by Claude at John's request
after the 1.29.4 review, which was accurate on all eighteen claims we
independently checked.

---

## Why a brief rather than a reply

Pasting our response back would work, but it would not fix the two
things that cost you effort last time, both of which were our fault
for what we sent you:

1. **You had no `.git`.** So you could not date a defect, and had to
   write "not verifiable" where the answer was one command away. You
   recommended holding 1.29.4 over the population-weight bug; with
   history you would have seen it entered in **1.21** and has been
   published since, which changes the recommendation.
2. **You had an outdated handover and no `BACKLOG.md` context.** So
   several findings you reported carefully — the missing icon, tests
   writing outside tmp, QGIS lacking variable bandwidth — were already
   logged, and your effort on them was spent twice.

Everything below is aimed at those two problems.

---

## What we will send next time

- **A git clone, not an export.** Tags back to v1.0, so `git log -S`
  can date anything.
- **`BACKLOG.md` as it stands**, which is the authoritative list of
  what we already know. Anything with an item number is known; please
  do not spend time re-deriving it, but **do** tell us if our
  description of it is wrong or our priority is.
- **The current `HANDOVER_*.md`**, which carries the conventions and
  the rulings.
- **The `MANUAL.md` version table**, which is the change history in
  prose — it is long, but it is where the *reasoning* behind odd
  decisions lives.
- **A working environment**, so you can run the suite: Python 3.10+,
  `pip install -e ".[test]"`. Note **BACKLOG 101**: the suite still
  writes run manifests into the working directory, so use a
  disposable clone.

---

## What EquiPop is, in one paragraph

EquiPop builds a bespoke neighbourhood around every location instead
of using administrative boundaries: the nearest *k* people, the radius
that was needed to reach them (`Dist_k`), and what that neighbourhood
contains. It exists to remove the zoning half of the modifiable areal
unit problem. The Python package computes; the "doors" (QGIS
Processing, an ArcGIS Pro toolbox, Stata `.ado` commands) are supposed
only to move data and explain parameters. Where that boundary has been
broken, defects follow — **BACKLOG 108 exists precisely because the
same population logic is written twice and only one copy was fixed.**

---

## The conventions a reviewer needs to know

These are deliberate, so please do not report them as defects — but do
say if you think one is wrong.

- **Ring-atomic ties.** Cells at equal distance are accepted as one
  atomic ring, so `N_k >= k` always. The overshoot is by design and is
  now reported (BACKLOG 94).
- **Origin and member are separate sets.** A row may ask what is
  around it without being part of what is around anyone.
- **Silence is the enemy.** A wrong number that announces itself is a
  bug; a wrong number that does not is the thing this project is most
  afraid of. When you find something that fails quietly, say so
  loudly — that framing is more useful to us than severity alone.
- **`s = 0` must reproduce pre-1.29.5 numbers exactly.** Self-potential
  changed a default; reproducibility of published work rests on that
  escape hatch, and it is asserted by a test.
- **QGIS Processing cannot grey a box out.** Several oddities in the
  QGIS door exist to work around that; see `equipop/doors/rungs.py`.

---

## What we would most value

In rough order.

1. **Numerical defects in combinations nothing drives.** This is where
   you were most valuable and where we are weakest. Our guards compare
   parameter *names* (`door_parity.py`) and result *column families*
   (`LADDER_CASES`); neither can see a number. BACKLOG 108 survived
   eight releases inside that blind spot.
2. **Anything that changes a scientific result silently.** Rank by
   whether a user would notice, not by how deep the code is.
3. **Reproductions with numbers.** Your before/after figures — `N_5`
   of 11 against 2, `Dist_2` of 141.421 against 100.0 — were worth
   more than any amount of description, and they are what let us
   confirm each finding in minutes.
4. **Places where the doors disagree.** Not just missing boxes:
   different *contents* of the same box, different defaults, different
   validation. We have found three such gaps in a week and expect more.
5. **Whether our own fixes are right.** Gate A of this release was
   written in response to you; the fixes are in `BACKLOG.md` items
   108–115 with their reasoning. Checking them is fair game.

## What we do not need

- **Disclosure control for register data.** Raised well, and **ruled
  out by John**: access to restricted data already requires agreed
  ethical protocols, so the tool does not need its own layer. Logged
  as item 122 with his reasoning, because it will be asked again.
- **Style, formatting, type annotations, CI.** Known, deliberate, or
  not our priority yet.
- **The `arcgis/EquiPop.pyt` file being long.** Known. It is one file
  because ArcGIS wants one file.

---

## Open questions where a second opinion would genuinely help

1. **`Dist_k` under effort.** Now the maximum straight-line extent of
   the accepted equal-effort ring (item 115). Is that the right
   quantity, or does an effort neighbourhood need a shape measure
   rather than a radius?
2. **Weighted statistics without person expansion** (item 118). We
   need exact weighted median, percentile and Gini on values plus
   weights. It blocks continental work. If you know a formulation that
   stays exact and streams, that would save us a week.
3. **The working frame** (item 93). Beyond ~20° of longitude we intend
   to stay in WGS84 and measure with great-circle distances rather than
   project, so that `k`, `Dist_k` and `tau` keep their meaning and stay
   comparable with a projected local run. The engine is metric to the
   bone, so this is the largest single piece of work ahead. Is the
   reasoning sound?
4. **Resume validation** (item 119). We plan to compare a canonical
   parameter set plus a fingerprint of the input coordinates and
   weights, and refuse on mismatch. Is a fingerprint of inputs enough,
   or does anything else need to be in it?

---

## How to report

The 1.29.4 format worked well and we would keep it: a ranked table
with impact, urgency, effort and **confidence**, with *reproduced*
distinguished from *confirmed in code*. That distinction is the same
discipline we use internally, and it is why we could act on your
document in a single session.

One addition, please: **where you can date a defect, do** — the release
it entered changes what we do about it more than its severity does.
