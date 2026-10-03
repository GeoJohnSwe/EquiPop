# PROPOSALS.md — funding applications, and what the code owes them

**Last updated: 1.51.2, 3 October 2026.**
*Reviewed at 1.51.2: nothing in the positioning changes. The
release aligns every door's version number for teaching reasons
and improves a refusal message; neither is a consortium-facing
fact. The 1.51.1 note below stands unchanged.
Reviewed at 1.51.1: ONE THING HERE WAS OVERSTATED AND IS NOW TRUE.
The 1.50.0 note below says provenance "is a reviewer's question and it
now has an answer" - and for the Stata and Pro doors it was. For QGIS
the record could not name which layer it described: every result layer
in one GeoPackage shared a single sidecar and each run overwrote the
last, and where a field had been renamed the record documented the
engine's name rather than the file's. A data-management plan that
promises per-run provenance should not have been written against that,
and can be now.
MORE USEFUL FOR THE EXPOSOME CASE: the WorldPop deletion is closed on
the Stata path (BACKLOG 343). The partner-facing claim this file makes
- population-weighted exposure per group, per neighbourhood, at
several scales, which eBoD needs and rarely has - ran through the one
route that rounded fractional counts to whole people, losing a
MEASURED 39% in Rwanda and 69% in Denmark. An Africa-against-Europe
comparison, which is exactly what a global exposome consortium is, was
biased by construction and by LATITUDE. That is now a sentence worth
having rather than a hazard: the figure demonstrates both that the
project measures its own defects and that this particular one is
fixed, and a reviewer who asks "how do you handle gridded fractional
counts" has a specific answer.
AND THE CONTRIBUTABILITY CLAIM GOT STRONGER AGAIN. The 1.51.0 note
below says the first outside pull request landed and every finding was
real. A fuller external code review followed within the day, nine
findings, all nine confirmed and fixed in 1.51.1 - two of them
mistakes made in 1.51.0 itself. For a consortium section claiming an
open, reviewable codebase, "two independent external reviews in two
days, twelve findings, all acted on" is demonstrated rather than
asserted. BACKLOG 349 is the one piece of continental capability
deliberately left open, and it is the one an exposome partner would
want: the origin rule is unreachable from the continental door.
Reviewed at 1.51.0: nothing in the positioning changes, but the
project took its first outside pull request and every finding in it
was real - worth knowing for any consortium section that claims an
open, contributable codebase, because it is now demonstrated rather
than asserted.
Reviewed at 1.50.0: PROVENANCE IS A REVIEWER'S QUESTION AND IT NOW
HAS AN ANSWER. Every run records the settings that produced it, taken
from the engine's own arguments rather than from a list somebody
maintains - which is the thing to write in a data-management plan,
and the thing an exposome consortium will ask about before it shares
anything. Worth a sentence wherever this file promises reproducible
multi-site analysis.
Reviewed at 1.49.3: EQUIPOP IS ON SSC. That is the sentence a
reviewer looks for - a Stata module distributed through the archive
economists actually use, not a link to a repository - and it can now
be written in the present tense wherever this file says "planned".
Reviewed at 1.49.2: nothing in the positioning changes. Worth
noting for the EquiEXPOSE data story, though: the exposome inputs -
WorldPop extracts, air-quality grids, remote-sensing summaries -
arrive as TABLES of coordinates far more often than as feature
classes, and until this release Pro could not turn one into a layer.
The partner-facing claim that EquiPop takes "whatever the provider
sends" is now true of the commonest case rather than nearly true.
BACKLOG 321 still awaits John's ruling.
Reviewed at 1.49.1: the ratio ruling matters for EquiEXPOSE. A
prescription count over a population is a rate, not a share, and can
exceed 1 - dispensations per person routinely do. EquiPop no longer
refuses that. BACKLOG 321, expected counts under a supplied rate
schedule, still awaits John's ruling.
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

## From exposure to health burden — eBoD and DALYs

*Added 21 September 2026, from Peter G. Schild's literature list on
metrics for environmental burden of disease.*

**Why this matters for the call.** It is a HEALTH call, and the
section above says plainly that a tool is not a proposal: it needs
health outcomes. EquiPop measures *exposure* — who is near what, at
which scale. Environmental burden of disease (eBoD) is the established
route from exposure to *health*, expressed as DALYs. It closes the gap
between what EquiPop produces and what a reviewer of an ENVHLTH topic
will ask for.

**The chain, and where each part sits:**

    exposure           who is exposed, where, at what scale   EquiPop
      -> exposure-response function                           epidemiology
      -> attributable fraction of disease                     epidemiology
      -> burden in DALYs  (= YLL + YLD)                       eBoD method

DALYs combine years of life lost to early death (YLL) with years lived
with disability (YLD). The method is set out in Prüss-Üstün et al.
(2003); Hänninen et al. (2014) apply it to nine environmental risk
factors in six European countries; Burnett et al. (2014) supply the
integrated exposure-response function for fine particles that the
Global Burden of Disease work uses; Cohen et al. (2017) give the
global ambient-air estimates.

**What EquiPop adds that standard eBoD does not.** eBoD studies
usually assign exposure at a coarse level — a country, a region, a
grid cell — and report one burden per area. That averages exactly the
inequality this call asks about. EquiPop assigns exposure per
bespoke neighbourhood, disaggregated by group and at several scales,
so the burden can be computed *for the disproportionately affected
populations* rather than for the area they happen to live in.

**And the granularity finding applies here too.** If coarse units
understate how concentrated a minority group is, they also misplace
how much of an exposure that group carries — and therefore how much
of the attributable burden. That makes the comparability problem in
"Why EquiPop fits" a health problem, not only a measurement one.

**The indoor half — and where SustainaBuilt comes in.** Most of the
example studies on the list are about the INDOOR environment:
De Oliveira Fernandes et al. (2009), Jantunen et al. (2011), Morawska
et al. (2013), Asikainen et al. (2016) and Carrer et al. (2015, 2018)
all quantify the health burden of indoor air and ventilation. That
matters because people spend most of their time indoors — commonly put
at close to 90% in Europe and North America — so the building envelope
and its ventilation stand between an outdoor climate exposure and the
exposure a person actually receives. Heat, wildfire smoke and ozone
all arrive through the building. This gives the proposal a natural
work package that turns *outdoor* climate exposure into *received*
exposure, and it is where the Department's building and indoor
expertise — SustainaBuilt — joins EquiPop and TransFrUrban.

**Which metric — John's decision, with a suggestion:**

| metric | what it counts | fit for this call |
|---|---|---|
| **DALY** | healthy years lost: YLL + YLD | **primary** — comparable with GBD and WHO eBoD |
| YLL / YPLL | years lost to early death only | a component of DALY, not a rival |
| YLD | years lived with disability only | the other component |
| QALY | quality-adjusted years gained | health economics, cost-effectiveness |
| HALY | umbrella term for all of these | no separate method |
| WALY | wellbeing-adjusted years | **worth considering for the SSH part** |

DALY is the natural primary measure: it is what the WHO eBoD method and
the Global Burden of Disease use, so results are comparable with
theirs. **WALY is worth a thought** because the call requires a real
social-science contribution, not a token one: a wellbeing-adjusted
measure is an SSH question in its own right, and could give that
partner a substantive role rather than a supporting one.

**The literature, by role:**

- *Method and reviews* — Prüss-Üstün et al. (2003); NCCID, summary
  measures of burden of disease.
- *Ambient air, global and European* — Burnett et al. (2014);
  Hänninen et al. (2014); Brauer et al. (2015); Cohen et al. (2017);
  WHO (2016).
- *Indoor environment and ventilation* — De Oliveira Fernandes et al.
  (2009); Jantunen et al. (2011); Morawska et al. (2013); Carrer et al.
  (2015, 2018); Asikainen et al. (2016); Morawska (2024).
- *Household energy* — Bonjour et al. (2013), on solid-fuel cooking.

**One reference to fix before it goes in the application.** The DOI
listed for WHO (2016) resolves to a one-page research brief reprinted
in the *Clean Air Journal* 26(2), 6. The author is correctly WHO, but
the full report of the same title — *Ambient air pollution: a global
assessment of exposure and burden of disease* — is the document to
cite in a grant.

## Open — John's

    [ ]  Consortium: who, and which of them brings the cohorts
    [ ]  Which SSH partner (the call REQUIRES effective SSH
         contribution, not a token)
    [ ]  Whether to target this topic or a sibling in the same call
    [ ]  One-page concept, before approaching partners
    [ ]  Burden metric: DALY as primary (suggested); WALY for the
         SSH part?
    [ ]  Which exposures - heat, PM2.5, ozone, wildfire smoke - and
         which exposure-response function for each
    [ ]  Model the indoor step (outdoor -> received exposure), with
         SustainaBuilt, or stay with outdoor exposure?
    [ ]  Who brings the epidemiology - exposure-response is not
         EquiPop's to supply

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
- **Probably nothing for eBoD itself - and that is deliberate.**
  DALYs are computed downstream from exposure, with exposure-response
  functions that belong to the epidemiology partner. That keeps the
  division of labour this project has held to: EquiPop builds the
  neighbourhoods, statistics happen in Stata or Python. What EquiPop
  DOES supply is the input eBoD needs and rarely has - population-
  weighted exposure per group, per neighbourhood, at several scales.
  Machine 2 already computes weighted summaries of a numeric field
  within each k-neighbourhood, so a sampled PM2.5 or heat surface may
  need no new code at all. Worth demonstrating before promising.
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
