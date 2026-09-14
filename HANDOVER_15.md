# HANDOVER 15

*Session 12. Where 14 ended at **1.46.4**, this ends at **1.47.2**:
1,144 tests, four machines in QGIS, four in ArcGIS Pro with complete
in-dialog help for the first time, and one new analytical choice that
is validated against a published paper rather than against itself.*

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
items 165–295 — three machines, the registry, every provider, the OSM
work — had never entered the ordered list. Rewritten, with a rule
written into it: struck items leave the list.

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

**Five things were built, tested, and unreachable.**

1. `doors/inventory.py` (269, shipped 1.45.0) — no GUI, no runner.
2. `vectorjoin.py` (280/282) — reachable only from a script that the
   source archive did not carry.
3. `RunLog` in `meta.py` — **backlog item 2**, complete, exported in
   `__all__`, called by nothing and tested by nothing. Still open as
   293.
4. The Pro help sidecars — generated, checked by a test, and never
   shipped to anyone.
5. `make_help_xml.py` — one of the five Pro files since 1.44.4, and
   until 1.47.2 it could not run from the folder it ships to.

Number 5 is the one to remember. It was offered to John as the
ten-second escape hatch from an untested change, he tried it, and it
failed on the first line. **The recovery path for a known risk was
itself unreachable, which is what made the risk feel acceptable.**

Every one of these passed its tests. The tests asked whether the
thing worked, never whether anyone could get to it.

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

---

## 5. WHAT IS OPEN

**Next, per the rewritten backlog head:** the Machine 5 browser arc
(248–265, 268, 278, 284) as its own multi-release project, with the
two door-less engines (280/282/283, 269) folded in — both are QGIS
dialog work. Then 293 (RunLog / no provenance for analysis runs),
205 + 118 (Stata cannot reach machine 2), 119 (resume compares
parameters but not content).

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
