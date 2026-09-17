# PROPOSALS.md — funding applications, and what the code owes them

**Last updated: 1.47.10, 16 September 2026.**
*Reviewed at 1.47.10: nothing has changed. The dates still need
John's confirmation from the portal, and no concept note exists.
Bumped because it was READ, which is the only thing the version
line is allowed to mean.
A test checks that version against pyproject.toml.*

**NOT SHIPPED.** This file stays in the repository and out of the
wheel and the source archive — MANIFEST.in excludes it deliberately.
Funding strategy, consortium thinking and draft positioning are not
things to publish on PyPI by accident. TEACHING.md does ship; this
does not.

---

## Why this file exists

An application is not a distraction from the code. It is a **question
put to the code**: does EquiPop answer what a funder is actually
asking? Session 12's origin-rule finding — that measured minority
isolation depends on the granularity of the units, by 13.6% on US
blocks at k=100 — became relevant to a Horizon call the day after it
was measured. That is the kind of thing that gets lost between
sessions unless somewhere holds it.

---

# 1. HORIZON-HLTH-2027-01-ENVHLTH-02

**"Integrating climate-related exposures into the human exposome and
characterising its changes in response to climate change"**

John: **coordinator and PI.**

## Dates — CHECK THE PORTAL, NOT THIS FILE

    opens     29 October 2026
    deadline  17 February 2027

The Commission **brought the 2027 Health deadlines forward**. John's
recollection was of the earlier schedule (open February 2027, close
April) and that is now wrong by roughly four months at the opening and
two at the deadline. Two national contact points agree on the dates
above; the Funding & Tenders portal is the authority and the dates
have already moved once.

**Consequence:** drafting overlaps with the call being open rather
than preceding it, and the consortium has to be settled well before
either date.

## Why EquiPop fits

The call asks, in its own words, for research that is **multiscale**,
for **intersectional vulnerability**, for **disproportionately
affected populations**, and for **racial or ethnic origin-
disaggregated data**. That is a description of what this software
does. It also asks projects to *build on existing exposome toolboxes
and increase their robustness and coverage*, and to contribute tools
to the IHEN Exposome Toolbox — a named route for a method
contribution rather than a hope.

**The strongest card is a measurement, not a claim.** An exposome
study pooling European registers, US census blocks and African survey
clusters is comparing neighbourhoods built from units of wildly
different size. Session 12 measured what that does: on US blocks
averaging 113 people, excluding the origin unit changes measured
African American isolation by 13.6% and White by under 1%, and it
flattens the scale profile sixfold between k=100 and k=800. **The
distortion is largest for exactly the concentrated minority
populations such a call exists to study.** That is a comparability
problem the field has and a number nobody else is offering.

## What EquiPop is, and is not, in this proposal

**IS:** a work package. A method for building comparable
neighbourhoods across incompatible geographies, a tool contributable
to the IHEN toolbox, and the multiscale machinery for the exposure
side.

**IS NOT:** the proposal. This is a consortium RIA needing cohorts,
health outcomes, biomarkers, SSH partners and clinical-study
annexes. A tool is a WP.

## Open — John's

    [ ]  Consortium: who, and which of them brings the cohorts
    [ ]  Which SSH partner (the call REQUIRES effective SSH
         contribution, not a token)
    [ ]  Whether to target this topic or a sibling in the same call
    [ ]  One-page concept, before approaching partners

## What the code could owe it

Nothing is committed. Recorded as candidates only, so that a session
choosing work knows which choices serve two purposes at once:

- **Provenance (293).** A methods WP in a consortium needs runs to be
  reproducible by other partners. Analysis runs have no record of
  their settings outside Pro.
- **Cross-geography comparability.** The origin rule is the first
  instrument for it. Whether a *general* correction for unit
  granularity is possible is a research question and might be the
  intellectual core of the WP rather than a feature.
- **Climate rasters through machine 3.** Heat, air quality and
  drought surfaces are continental rasters, which is what machine 3
  already curates. Nothing new may be needed, which is worth knowing
  before promising anything.

## Status

    [ ]  Portal dates confirmed by John
    [ ]  Concept note
    [ ]  Partners approached

---

# 2. Stata Journal — the software paper

Mentioned in session 12 as near-term and never opened properly.
Relevant here because it shares an artefact with TEACHING.md: the
five-county Los Angeles worked example is the course exercise AND the
paper's application AND the proposal's evidence. **Build it once.**

Wording already agreed for the methods section, on the boundary rule:

> Neighbourhoods are grown outward until they contain *k* people.
> Where the unit that crosses *k* would carry the total past it, that
> unit contributes a proportional share, so the denominator is exactly
> *k*. This matches the convention of the original EquiPop software.
> Setting `overshoot(whole)` instead admits each unit entire, giving
> N ≥ *k* — on US census blocks at k=100, N then ranges to several
> thousand, and indices computed under the two rules are not
> comparable.

Open: nothing drafted; no timeline agreed.
