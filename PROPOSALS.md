# PROPOSALS.md — funding applications, and what the code owes them

**Last updated: 1.53.1, 6 October 2026.**
*Reviewed at 1.53.1: NO CLAIM IN THIS FILE CHANGES. One paragraph in
the February text gets easier to write honestly, and it is a
paragraph reviewers do read.
A consortium work package that says partners will run the software on
their own national data is making a claim about INSTALLABILITY, not
just about method. Every partner will be on Windows, and on Windows
the most likely way rasterio, geopandas or pyproj fails is `DLL load
failed` - a case this project had classified and tested since 1.35
and never once printed advice for. A partner meeting that message got
a dead end from a tool whose own diagnostic knew what had happened.
That is fixed, along with naming every missing dependency at once
rather than the first, so the sentence about partners self-serving
their data has something behind it.
IT DOES NOT CHANGE THE SCOPE, and do not let it read as a capability
in the proposal - a diagnostic is not a feature, and claiming it as
one invites the reviewer to ask what else is only diagnosed. Mention
it, if at all, in the data-management or risk section: "failure modes
on partner machines are reported with their remedy" is the true
version.
BACKLOG 365 IS STILL THE ONE NOT TO PROMISE. Unchanged from 1.53.0
and repeated because it is the item most likely to be written as done
by accident: a continental DEMOGRAPHIC index has no tiled route, so
Europe-wide dependency ratios remain the piece the software cannot do
at scale. 353 made the exposure surfaces carriable; the index is a
separate job.*

*Reviewed at 1.53.0: THE CLIMATE-RASTER ENTRY BELOW WAS WRONG AND IS
NOW CORRECTED IN PLACE - read it before writing the data-management
section. It said machine 3 might need "nothing new" for heat, air
quality and drought surfaces; measured, a temperature anomaly came
back with the wrong SIGN. Fixed in this release, so the claim can be
made in the present tense for the first time. The depopulation case
came back with it.
NOTHING ELSE IN THE POSITIONING CHANGES. One thing to keep in view
for the WP description: a continental DEMOGRAPHIC index still has no
tiled route (BACKLOG 365), so Europe-wide dependency ratios are the
one piece of the exposome story the software cannot yet do at scale.
It is measured work, not research - the tiles already carry both
halves of the ratio - but do not promise it as done.
*Reviewed at 1.52.0: ONE SENTENCE GETS STRONGER. This file argues
that a general correction for unit granularity may be the
intellectual core of the exposome work package rather than a feature
of it. Until this release EquiPop could not have supported that claim
with hexagons, because its own hex cells were being charged a
square's area - the reachability matrix refused them at every door
for exactly that reason. The engine half is correct now, so a MAUP
comparison across cell GEOMETRIES, not only across cell sizes, is
available to the research question. Nothing else in the positioning
changes.
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

    opens     29 October 2026      single stage, RIA, EUR 45m
    deadline  17 February 2027

**FEBRUARY IS THE DEADLINE, NOT THE OPENING.** That sentence is first
because the mistake has now been made twice by the same person, in the
same direction, five months apart.

The Commission **brought the 2027 Health deadlines forward**. The
earlier schedule — open February 2027, close April — is the one that
sticks in the memory, and it is wrong by about four months at the
opening and two at the deadline. The original April date still
circulates: a funding aggregator was showing *deadline 2027-04-13* as
recently as this week, which is the pre-change schedule, so a search
will return both answers and the stale one looks reassuring.

**RE-CHECKED 5 October 2026**, because John said the call was "not
opening soon, but in february". Two sources agree with the table
above: NCP Brussels (published 23 June 2026, updated 8 July) and an
accelopment summary of the official Work Programme (last modified
1 October 2026). I could not read the Funding & Tenders portal topic
page directly — it renders its content through a script — so **the
portal remains the authority and is still worth one look by a human.**

**Consequence, and it is not small.** As of the re-check the call opens
in **three and a half weeks** and closes in **nineteen**. Drafting
overlaps with the call being open rather than preceding it, and a
consortium RIA needing cohorts, health outcomes, biomarkers, SSH
partners and clinical-study annexes has to be settled now rather than
assembled after the opening.

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
- **Climate rasters through machine 3. SOMETHING WAS NEEDED, and it
  is done.** This entry used to read "nothing new may be needed, which
  is worth knowing before promising anything." It was worth knowing,
  and it was wrong. Machine 3's loader selected pixels with
  `arr > 0` - a POPULATION loader, and nothing said so. Measured on a
  temperature-anomaly field whose true mean is -0.0046 degC: it came
  back as **+1.19 degC, warming everywhere**, because every cooling
  pixel was silently discarded. A zero-floored PM2.5 surface came back
  **9.9% high**, because its clean-air pixels were read as absent.
  The one claim this file makes that an exposome consortium will test
  first - population-weighted exposure per group, per neighbourhood,
  at several scales - ran through the one path that could not carry an
  exposure surface.
  **Fixed in 1.53.0 (BACKLOG 353).** The loader now distinguishes
  OBSERVED from NoData, carries negative values as given, says so when
  a raster is signed, and the default path for a population raster is
  bit-identical to before. So the sentence can be written in the
  present tense: heat, air quality and drought surfaces go through
  machine 3, and a signed field keeps its sign.
  **AND THE SAME FIX GAVE BACK DEPOPULATION.** `keep_zero` promised
  to keep pixels that are zero everywhere and did nothing at all -
  both branches were dead. A place that HELD people and now holds none
  was simply absent from the output. It is a row again: nobody's
  neighbour, contributing nothing to reference or treatment, and
  entitled to its own result. That is John's own rule from 1.22.2, and
  it is what makes a then-and-now comparison possible at all.
  Worth a sentence in the data story: 1,201 such pixels were being
  dropped from Denmark in the project's own test fixture.

## Status

    [ ]  Portal dates confirmed by John
    [ ]  Concept note
    [ ]  Partners approached

---

# 2. ~~Stata Journal — the software paper~~ **SUBMITTED**

**Submitted, 5 October 2026.** *equipop: Individualized spatial
contexts in Stata*, The Stata Journal (2026), st0000. Struck as a
planning item; what remains is what the paper now OBLIGES, below.

The application it was expected to feed turned out differently from
the plan in this file: the paper does **not** use the five-county Los
Angeles example. It validates twice — reproducing the multiscalar
spatial-isolation workflow of Clark and Östh (2018), and comparing
against an exact point-level benchmark — and then applies the command
to **2023 LEHD Origin-Destination Employment Statistics workplace data
for Dallas–Fort Worth**, contrasting equal-job with equal-distance
employment contexts. The "build it once" argument therefore still
stands for the course and the proposal; it simply has no paper half
any more.

## WHAT THE PAPER NOW PINS

A submitted paper is a promise about behaviour. These are the claims a
future session must not casually break, checked against the shipped
1.51.2 code on the day of submission:

- **Equation (5), the adaptive radius.**
  `r_i(k) = inf { r : Σ_j p_j I(d_ij ≤ r) ≥ k }`. This is the formal
  statement of why BACKLOG 351 refuses a negative population: the
  infimum is the boundary of an **up-set**, which requires the
  accumulating sum to be monotone in *r*. With a negative `p_j` it is
  not, and equation (5) has no solution rather than an awkward one.
  The ruling and the published definition now agree.
- **Five decay families** — negative exponential, exponential normal,
  exponential square root, log normal, power. Verified: exactly those
  five in `decay.MODELS`, no more.
- **Power has no finite area-under-the-curve half-life** and is
  calibrated only by half-probability. Verified: the code says so and
  falls back, which is BACKLOG 317.
- **Footnote 1 is a correction to the published literature, and the
  code must earn it.** The appendix of Östh et al. (2016) sets an
  error-function term to one half; because the cumulative area for the
  log-normal contains (1 + erf(z))/2, that condition locates the THIRD
  QUARTILE and not the median. equipop solves the 50% cumulative-area
  condition directly. **Verified numerically on the shipped code**:
  the area below *h* is 0.500000 of the total. A regression here would
  make a submitted paper wrong about the thing it claims to fix.
- **Exclusion operates at the origin-CELL level** for gridded or
  aggregated data — which is what `selfrule.EXCLUDE` does, and the
  paper tells the reader to interpret it at the resolution of the
  input.
- **The place-based calibration distance is a TWO-CALL public
  workflow**: one call computes `r_i(k_h)`, a second supplies it
  through `halflifevar()`. Distinct from the engine's internal
  self-calibrating pass, which BACKLOG 342 fixed; if that internal
  route is ever promoted to the public workflow, the paper describes
  the two-call one.

Wording agreed earlier for the methods section, on the boundary rule,
and still the clearest statement of it:

> Neighbourhoods are grown outward until they contain *k* people.
> Where the unit that crosses *k* would carry the total past it, that
> unit contributes a proportional share, so the denominator is exactly
> *k*. This matches the convention of the original EquiPop software.
> Setting `overshoot(whole)` instead admits each unit entire, giving
> N ≥ *k* — on US census blocks at k=100, N then ranges to several
> thousand, and indices computed under the two rules are not
> comparable.

**Open:** referee response, if it comes back with one. And the
availability statement, which was open before submission — worth
checking it made it in, since SSC distribution is the answer and the
archive now has it.
