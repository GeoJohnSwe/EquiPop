# PROPOSALS.md — funding applications, and what the code owes them

**Last updated: 1.54.3, 10 October 2026.**
*Reviewed at 1.54.3: NO CLAIM IN THIS FILE CHANGES. The release
adds `equipop help` as a subcommand, two lines to the doctor's
clean verdict, and three tests that derive a documented list
from the code rather than keeping it by hand. Usability and
test hygiene; nothing touching the exposome positioning, the
origin-rule measurement or the MAUP argument.*
*Reviewed at 1.54.2: NO CLAIM IN THIS FILE CHANGES, and the
corrected sentence from the 1.54.1 note below still stands as
written. The second review's findings were a malformed Stata help
file, two test-isolation defects, a fractional k accepted by the
Python advisory, an ordering mistake in the downloader's scheme
check and a cache that validated the request but not the stored
answer. All of them are correctness and packaging work; none
touches the exposome positioning, the origin-rule measurement or
the MAUP argument.
ONE THING NOT TO PUT IN A PROPOSAL: the review rounds themselves.
It is tempting to offer a software-quality claim on the strength
of three external reviews in two days, and a reviewer would be
right to read that as an admission rather than a credential.
What belongs in a proposal is the measurement, not the process
that produced it.*
*Reviewed at 1.54.1: **ONE SENTENCE IN THE 1.54.0 NOTE BELOW WAS
OVER-CLAIMING AND IS CORRECTED HERE.** It offered, for a methods or
comparability section: "the share of neighbourhoods whose radius is
estimated rather than measured is reported for every cell size."

That is true only under `originrule(include)`. An external review of
1.54.0 found the advisory handing include-rule counts to `exclude`
runs; measured, under `exclude` the engine drops the origin's whole
cell, so the saturated count is structurally zero and the criterion
describes nothing. **The true version of the sentence names the
rule**: "under the published include convention, the share of
neighbourhoods whose radius is estimated rather than measured is
reported for every cell size; under the w(ii)=0 convention the
question does not arise, because an origin's own cell is never its
neighbourhood."

**THAT SECOND HALF IS WORTH HAVING IN THE PROPOSAL RATHER THAN BEING
AN ASIDE.** This file's strongest card is the origin-rule measurement
- that excluding the origin changes African American isolation by
13.6% and flattens the scale profile sixfold. The new finding says
something adjacent and useful: the w(ii)=0 convention that spatial
regression requires is ALSO the one in which cell size cannot quietly
destroy k. A reviewer asking "how do you know your scale profile is
not an artefact of the grid" has a cleaner answer under exclude than
under include, and that is an argument for the convention rather than
only a caveat about it.

Nothing else changes. The MAUP trap named in the 1.54.0 note stands,
and now has a sharper form: it applies to an include-rule scale
profile specifically.*
*Reviewed at 1.54.0: **NO CLAIM CHANGES, AND ONE ARGUMENT THIS FILE
ALREADY MAKES GETS AN INSTRUMENT - PLUS A TRAP IT SHOULD NAME.**

This file says, under the candidates below, that whether a *general*
correction for unit granularity is possible "might be the intellectual
core of the WP rather than a feature". 1.54.0 does not answer that
question. It supplies something the question needs first: a
measurement of **when a cell size has destroyed the parameter**.

Once a cell holds k people on its own, the whole neighbourhood IS
that cell - the radius stops being measured and comes from the
self-potential formula, and k=200 and k=2000 return the same number.
BACKLOG 95 named this in 2026 and the engine has reported it after
every run since 1.29.5; the release reports it BEFORE one, across a
ladder of cell sizes, as a share of CELLS and a share of PEOPLE.
Measured against the engine on three shapes rather than derived.

**THE TRAP, AND IT BEARS ON THE STRONGEST CARD ABOVE.** The
measurement this file leads with is a scale profile - the origin rule
flattening African American isolation sixfold between k=100 and k=800
on US blocks averaging 113 people. A MAUP comparison *across cell
sizes* is the natural companion to it, and at the coarse end of any
such ladder **some of the cells have already swallowed the whole
neighbourhood**, so those points are not comparisons at different
scales: they are the same answer repeated, with k no longer the
parameter being varied. On LA County at 100 m that is 41% of blocks
(TEACHING.md measured it). Any scale profile across unit sizes has to
report the saturated share at each size or a reviewer can ask whether
the flattening is the method or the grid - and that is a question
better answered in the methods section than at review.

**DO NOT PRESENT IT AS A CAPABILITY.** Same rule this file applies to
the shared input reader at 1.53.2 and the Windows diagnostics at
1.53.1: an advisory is not a feature, and claiming it as one invites
the question of what else is only advised about. For the methods or
comparability section: "the share of neighbourhoods whose radius is
estimated rather than measured is reported for every cell size" is
the true version. **It changes no default and chooses nothing** - if
the software picked the cell size, two runs on the same data could
use different ones and a published figure would rest on a heuristic
that might change between versions.

349 remains the last gap between a continental run and the full
engine, unchanged. MACHINE 7 (section 3) is unchanged and still
waiting on John's two decisions and a literature check.*
*Reviewed at 1.53.4: **THE STANDING WARNING IN THIS FILE IS RETIRED.**
Four releases running, this section said BACKLOG 365 was the one piece
not to promise as done - a continental DEMOGRAPHIC index had no tiled
route, so Europe-wide dependency ratios were the thing the software
could not do at scale. John ruled it worth pursuing and it is done:
the tiles already carried both halves of the ratio per origin, so it
is a per-tile post-pass with memory bounded at one tile.
**WHAT MAY NOW BE WRITTEN IN THE PRESENT TENSE**: population-weighted
exposure surfaces (1.53.0) AND demographic indices over bespoke
neighbourhoods, both at continental scale, in one traverse of the
data. That is the whole exposome claim rather than half of it, and it
is the first time this file has been able to say so.
TWO THINGS TO STATE ACCURATELY RATHER THAN QUIETLY. A tiled run's
index is stored as float32, because machine 3 stores tiles that way
and declares it in the manifest - max relative difference against the
in-memory float64 answer, measured, 1.3e-07. That is irrelevant to a
ratio reported to three decimals and it should still be in a methods
footnote rather than discovered by a reviewer. And age bands above 90
are now FOLDED INTO the 90+ band (John's ruling, 363), which means
"90+" in a published figure is the FOLDER'S top, not WorldPop's - the
run says so, and so should the methods section.
**349 IS NOW THE LAST GAP** between a continental run and the full
engine: the continental door exposes none of the five engine options,
so `originrule(exclude)` - the w(ii)=0 convention spatial regression
requires - is unreachable at that scale. Smaller than 365 was, and it
is what the next pass should take.
MACHINE 7 (section 3) is unchanged and still waiting on John's two
decisions and a literature check.*
*Reviewed at 1.53.3: NO CLAIM CHANGES. One line of evidence for the
risk section, and one note for the machine 7 entry below.
A work package promising that partners run the software on their own
national data is promising it survives THEIR data. Null geometry is
what partner data has - failed geocodes, hand-edited shapefiles,
joins that missed - and until this release one of the two GUI doors
lost the whole run to it while the other handled it correctly. Fixed,
and the two doors are now tested against EACH OTHER for the same
input, which is the more useful claim: not "we handle missing data"
but "our implementations agree".
FOR MACHINE 7 (section 3): this release strengthens the case for the
row-alignment argument made there. A row EquiPop cannot locate keeps
its slot and returns Null, so two scenario runs stay aligned and a
difference between them is a difference in the ANSWER rather than a
change of denominator. That is the same property the agent model
needs for its paired common-random-number comparison, and it is now
true at every door rather than at one.
BACKLOG 365 IS STILL THE ONE NOT TO PROMISE - fourth release
running.*
*Reviewed at 1.53.2: NO CLAIM CHANGES, and one risk sentence gets
easier to write honestly.
A consortium proposal says partners will run the software on their own
national data. Every partner will be on Windows, and most of them will
type a thousands separator into a box at some point, because that is
how numbers are written in the countries this project is for. Until
this release that produced a completed run with the wrong
neighbourhood size and no warning - which is the one failure mode a
reviewer of a methods work package should care about most, because it
does not announce itself and it survives into published figures.
It is refused now, in all four doors, through one reader that a test
forbids anybody from bypassing. If the risk section needs a sentence:
"inputs are validated at the dialog, before computation, through a
single shared reader" is the true version. Do NOT present it as a
feature - a validation layer is not a capability, and claiming it as
one invites the question of what else is only validated.
BACKLOG 365 IS STILL THE ONE NOT TO PROMISE, third release running
and repeated because it is the item most likely to be written as done
by accident: a continental DEMOGRAPHIC index has no tiled route, so
Europe-wide dependency ratios remain the piece the software cannot do
at scale.*
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

---

# 3. MACHINE 7 — AGENT-BASED ACCESSIBILITY ASSIGNMENT

**A thought experiment, 8 October 2026. John's idea; nothing is
implemented and nothing should be until the decisions below are
settled.** Recorded here rather than in the backlog because its first
value is to a funding application, not to a release.

John's question: could EquiPop generate agent-based models — barriers,
frictions, decay and the reference/treatment split already present,
plus a random component for choice, a number of users set per location
by field or constant, destination capacity, and rounds to fill it —
in order to simulate **how accessibility changes as the landscape is
altered**?

## AMENDED 9 OCTOBER 2026 - MOST OF THIS IS ALREADY BUILT

**THE RECOMMENDATION BELOW WAS WRONG AND IS CORRECTED HERE RATHER
THAN DELETED**, because the mistake is instructive. "Recommended
sequencing" told John to build a deterministic capacity-aware
accessibility measure first - 2SFCA with the arbitrary catchment
replaced by EquiPop's - as a cheap stepping stone. **`equipop/fca.py`
has been that since it was written.** From its own docstring:

    reach="k"      kFCA: each catchment GROWS until it contains k
                   units of the opposite side's MASS - fixed-population
                   catchments, the EquiPop signature
    reach="effort" weights from SLOPE/FRICTION effort (optionally
                   round-trip); decay half-life is then in ROUNDS
    method="2sfca" / "3sfca"
    balance=n      doubly-constrained (Wilson) balancing

So 2SFCA, 3SFCA, bespoke catchments and friction-based effort are all
present - AND `balance=n` is the doubly-constrained spatial
interaction model that the VALIDATION section below nominates as the
external answer key. **The answer key is in the package.** Tobler is
too: `slope.py` carries the hiking function and it is the DEFAULT
model in both `access.py` and `fca.py`, so the DEM half of John's
scenario costs nothing.
THE LESSON, which is this session's own recurring one pointed at
Claude rather than at the code: a capability that nothing surfaces is
a capability nobody has. Five releases of this session found a guard,
a hint, a parse, a convention and an index column that existed and
could not be reached. This is the sixth, and the unreachable thing was
reachable all along to anyone who read the module.

## JOHN'S TWO SCENARIOS, 9 OCTOBER, AGAINST WHAT EXISTS

**SCENARIO 1 - nearest shop, customers per shop, then counterfactuals
with decay, barriers, friction and a DEM.** Expressible today, read as
an FCA with the roles that way round:

    fca(demand=residents, supply=shops, reach="k", k=1)

Each resident's catchment grows until it contains ONE shop, so W_ij is
the nearest-shop indicator and **sum_i W_ij D_i is exactly "customers
of shop j"**. `decay=` turns winner-takes-all into shares;
`reach="effort"` brings in friction, barriers and Tobler slope; the
counterfactual is two runs differenced.

**THE ONE THING MISSING IS THE OUTPUT, AND IT IS ONE COLUMN.** In
fca.py:

    denom = ...                 # sum_i W_ij D_i - the customers
    R = Sm / denom
    supply_out["R"] = R         # only the ratio comes back

The number John wants is computed and discarded. Recoverable as
S_j / R_j, and that breaks wherever R = 0, and nobody should have to
know to do it. The i-j relationships he wants kept are the same story:
that is W, built and dropped - sparse at k=1, one entry per demand
cell, so cheap to return; dense with decay, which is where the cost
actually is.
TWO THINGS TO MEASURE BEFORE PROMISING. The assignment is to a CELL,
not to a shop, so unit_size is the spatial resolution and a cell
holding two shops cannot tell them apart - that wants a diagnostic.
And the tie convention for reach="k" says equidistant cells enter
wholly; what k=1 does with a MULTI-SHOP cell is unmeasured, and it
decides whether a customer goes to one shop or is split between them.

**SCENARIO 2 - a random walk instead of road distance.** The
randomness is probably redundant, and there is a test for whether it
is. A random walk over a friction surface converges IN EXPECTATION to
what a decay kernel gives in closed form, so many replications recover
a function that can be evaluated once. The question to put to the walk
is therefore: **what do you want that is PATH-DEPENDENT?**
  - ARRIVAL outcomes - customers per shop, access scores, catchments.
    Deterministic. The averaged baseline and averaged counterfactual
    each collapse to ONE run.
  - PATH outcomes - which bridge was used, flow per link, where
    congestion lands. Genuinely new, and **the deterministic route
    beats a walk**: take the i->j assignment, compute the least-cost
    path over the friction surface, accumulate flow onto cells. That
    answers "how many people cross this bridge to reach their shop"
    exactly, and closing the bridge is a paired deterministic
    difference. Flow accumulation over an assignment tree - the same
    machinery as all-or-nothing assignment in transport, or D8
    accumulation in hydrology.
A walk earns its place only to model IMPERFECT KNOWLEDGE or
route-choice heterogeneity - people not taking the best path. That is
a behavioural claim to defend to a referee, not a technical
necessity.
BFS, which John wondered about, is what the engine already does: the
search is a breadth-first expansion over the cell lattice. The
algorithm is there; the RECORDED PATH is not.

**AND THE VALIDATION PROBLEM LARGELY DISSOLVES**, which is the
strongest argument for doing Scenario 1 first whatever happens to the
agent model. With no randomness: conservation is exactly checkable
rather than approximately; the degenerate case has a real external key
(no barriers, no decay, flat DEM -> the assignment must equal
straight-line nearest, which cKDTree gives in three lines, bit-
identical or wrong); monotonicity under an added barrier is a
pass/fail; and `balance=n` supplies a second independent key from
inside the package.

**ON THE NAME.** Scenario 1 is not an agent-based model and should not
be called one in print - it is catchment generation, or all-or-nothing
assignment. Calling it an ABM invites "where are your agents, and what
did they learn?" and gets the work reviewed against the wrong
literature.

## THE REFRAMING, WHICH IS THE WHOLE REASON TO TAKE IT SERIOUSLY

An accessibility simulation must answer two questions before any agent
moves: **which destinations does this person consider**, and **what
does distance cost them**. Standard practice fudges both — a fixed
buffer, a fixed *n* nearest, or everything in the study area. That
arbitrariness is the standing critique of the two-step floating
catchment literature.

**EquiPop's bespoke neighbourhood is a choice-set generator.** The
choice set is the destinations inside the radius at which *k* people
are reached: density-adaptive by construction, which is the argument
the Stata Journal paper already makes in print.

**And the decay families are already a choice kernel**, up to
normalisation. `p_ij = w(d_ij)·A_j / Σ_j w(d_ij)·A_j` is a Huff model;
competing-destinations is the same object with a competition term. So
the "random component" is not new mathematics — it is **sampling from
a kernel the engine already computes correctly**, including the
own-cell weight and the shape-aware intra-cell distance that 1.52.0
fixed and that most agent models ignore.

So the proposal is **not** "add ABM to EquiPop". It is **expose an
existing competence to a literature that needs it** — which is far
cheaper to build and far easier to defend to a reviewer.

The reference/treatment split carries straight over: the treatment
population IS the agent pool (under-fives seeking a nursery place),
the reference population IS the competition setting the denominator.
`pop()`, `values()` and groups already specify who the agents are, so
no new vocabulary is needed for that. Machine 4 is a natural upstream
feeder — a dependency ratio identifies who needs care, which is an
agent population for a care-accessibility run. That gives **365** (no
tiled path for machine 4) a second reason to be closed.

## WHAT IS FREE AND WHAT IS NOT

| already built and tested | genuinely new |
|---|---|
| bespoke neighbourhood → the choice set | agent representation and memory model |
| five decay families → choice probabilities | normalised kernel + a draw (*small*) |
| barriers, tau/effort, roundtrip → friction | **capacity state, and its coupling** |
| self-potential, hex/square intra-cell distance | the assignment and stopping rule |
| seeded sampling, `seed_message` | an O-D output artefact |
| run record, manifest, `cells_md5` | a stochastic test idiom |
| tiling → continental scale | independent seed streams |
| the 1.22.2 zero-population rule | |
| signed rasters → environmental attractiveness | |

The zero-population rule matters more here than anywhere: scenario
work is precisely about places whose population changed, and 1.53.0
made `keep_zero` actually deliver it.

## THE ONE THING THAT BREAKS THE ARCHITECTURE

**Capacity destroys per-origin independence.** Everything EquiPop does
today is embarrassingly parallel — each neighbourhood is computed
without reference to any other, which is *why* tiled continental runs
exist. The moment destination *j* can fill, origin *i*'s outcome
depends on what origin *i'* chose. The computation becomes a global
iteration.

That costs, concretely:

- the tiled path cannot be reused naively
- results become **order-dependent** unless the rule removes order
- `cells_md5` stops being a sufficient run identity: the seed family,
  the capacity vector, the rule and the iteration count all enter it
- "rounds to capacity" is an arbitrary parameter unless it has a
  defined endpoint

**Two escapes from the last one.** A **stable matching** — agents rank
destinations by kernel weight, destinations rank by distance or
priority, run deferred acceptance — terminates on its own and is
**independent of processing order**, which kills the reproducibility
problem rather than managing it. Alternatively **queueing**, where
congestion adds a waiting term that feeds back into the friction. The
second is scientifically the more interesting, because it makes
accessibility genuinely **endogenous**: your access depends on
everyone else's choices. That is the research contribution hiding in
the idea, and it is what distinguishes this from a faster 2SFCA.

## VALIDATION — JOHN'S ANSWER, AND WHAT EACH PART IS WORTH

This is the real risk. The project's credibility rests on nothing
being claimed until it is measured, and on answers checkable against
published work. **A simulation has no answer key**, so the plan has to
be explicit. John's three proposals, 8 October, ranked by what they
actually establish:

**1. Conservation — "if the sum leaving all i and arriving at any j is
the same, I am happy."** NECESSARY, NOT SUFFICIENT. It catches
leakage, duplication and double-assignment and belongs as the first
invariant. But a wrong model satisfies it: send everyone to their
nearest destination, or shuffle at random, and the sums still balance.
It validates the plumbing, not the behaviour.

**2. Iterations against selection likelihood — THE REAL ONE, and
stronger than stated.** For the unconstrained case the target is not
empirical at all, it is **closed form**: `p_ij` above is computable
exactly from the kernel. Run N replications, check the observed
selection frequency converges to the analytic probability within a
tolerance shrinking as 1/√N. That is an external answer key, not
self-comparison, and it pins the kernel AND the draw together.
It stops working once capacity binds — there is no closed form for
realised shares then — which is exactly why it is the **zero-pressure
degenerate case**: infinite capacity must reproduce the analytic
probabilities, and capacity is then tested separately.

**3. Aggregate behavioural statistics — right about variance, risky
about inference.** Aggregate functionals converge far faster than
per-pair shares, so the replication count genuinely falls. But
"agents move toward dense areas" is a PREDICTION OF THE MODEL, so
confirming it confirms the model does what its own assumptions
dictate. That is face validity: good for catching sign flips and
inverted kernels, good for a figure, blind to subtle error.
**It becomes a real test as MONOTONICITY under a known perturbation:**
raise a barrier and cross-barrier flow must not increase; steepen the
decay and mean trip length must fall; add capacity at *j* and *j*'s
load must not drop. Paired runs on the same seed make the comparison
within-agent, so very few replications are needed.

**Plus two the project should insist on itself:**

- **The degenerate case must reduce EXACTLY.** Zero randomness and
  infinite capacity must reproduce the existing deterministic measure
  **bit-identically** — the same identity discipline as the 1.52.0
  square-cell proof and the 1.53.0 default-path proof. Strongest test
  available, and free.
- **A doubly-constrained spatial interaction model solved by iterative
  proportional fitting** on the same inputs has a known convergent
  solution. Flow-mode results should match it. Also external.

**And a labelling rule.** A machine 7 column is a SIMULATED quantity.
It must never be mistakable for a machine 1–4 measurement, and the
question "is that figure measured or simulated?" must have a one-word
answer. The run record and sidecar already provide the machinery; the
seed belongs in it.

## DECISIONS ONLY JOHN CAN MAKE

- **What is an agent?** A *flow* of fractional people (then it is a
  spatial interaction model, fast, and not an ABM); an *individual*
  per person (6M for Denmark is fine, 450M for Europe is not); or a
  *cohort* carrying weight *m* — the pragmatic middle, which maps onto
  the fractional-weight arithmetic the proportional overshoot mode
  already performs. **Recommended: the cohort, stated in print.**
- **One choice or a trip chain?** Single-destination assignment is a
  one-shot problem. An activity schedule is a different and far larger
  program. **Recommended: refuse the second explicitly in the docs.**
- **What does capacity do when it binds?** Refuse-and-rechoose, queue
  -and-wait, or degrade-with-load. Three different papers.
- **Where does randomness enter?** At least four places — which
  destination, how many users per origin, whether a person
  participates at all, and the overshoot sampling that already exists.
  They need **independent seed substreams**, not one global seed, or
  variance cannot be attributed to its source. Cheap now, painful to
  retrofit.
- **Where does the output live?** Architectural. The whole output
  convention is "columns on the origin table". An assignment produces
  per-origin results, per-DESTINATION results (load, utilisation,
  unmet demand) and a **pair-level flow matrix** — and an O-D matrix
  has nowhere to go in the current shape. A third artefact beside the
  point table and the manifest.

## SCOPE — WHAT NOT TO BUILD

Not "an ABM framework". NetLogo, MESA and GAMA exist and this would be
a worse one. The defensible name is **"capacity-constrained stochastic
accessibility assignment over bespoke neighbourhoods"** — unfashionable,
precise, publishable, competing with nothing. If it grows agent
memory, learning, inter-agent interaction or networks, it has become a
worse MESA and should be stopped.

Two costs the project should price in. The suite asserts exact numbers
everywhere; a stochastic machine needs a different idiom — seeded
byte-identity, distributional bounds derived from the replication
count, and invariants. And the 1.53.2 release found **seven** copies of
one number parser: any new numeric input — capacity, rounds, kernel
parameters — comes through `doors/numbers.py` and the reachability
matrix on day one, or it becomes copies eight through fourteen.

## RECOMMENDED SEQUENCING

**A strong proposal component and a weak immediate build.** The
February application gains more from a credible work-package design —
this section — than from a half-finished machine 7 standing beside two
already-incomplete items (365, 349).

**The cheap intermediate worth having on its own: a DETERMINISTIC
capacity-aware accessibility measure.** No agents, no randomness —
"how many people can reach this facility within their own bespoke
neighbourhood, and does it have room for them." That is 2SFCA with the
arbitrary catchment replaced by EquiPop's, which is a methodological
contribution in its own right; it reuses everything above; it needs no
new test idiom; and the agent model becomes its microsimulation
extension rather than a from-scratch machine. It also forces the O-D
output question early, while answering it is still cheap.

## Status

    [ ]  John to settle: agent representation, capacity behaviour
    [ ]  Literature checked against sources, NOT from memory
    [ ]  Decide whether the deterministic measure goes first
    [ ]  Only then: a backlog entry, with doors deliberately deferred

**Literature named from memory and NOT verified** — Huff on retail
gravity, Fotheringham on competing destinations, Luo and Wang on
2SFCA, Gale and Shapley on stable matching, and common random numbers
as a variance-reduction technique. All are well known and all are
plausible framings, but none has been checked against a source in this
session. **Verify before any of it reaches a proposal.** The
stable-matching suggestion in particular is this session's framing,
not something seen applied to bespoke neighbourhoods — a lead, not a
citation.
