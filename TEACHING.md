# TEACHING.md — the course material, and what it still needs

**Last updated: 1.53.3, 8 October 2026.**
*Reviewed at 1.53.3: NO EXERCISE CHANGES, and one thing to say out
loud in the first session.
A layer with features that have NO GEOMETRY is ordinary teaching
data - a geocoder that failed on three addresses, a spreadsheet join
that missed, a shapefile edited by hand. Until this release machine 1
in ArcGIS Pro answered that with an arcpy traceback and the whole run
was lost. It now keeps those rows, gives them Null results, and says
how many - which is the SAME rule the course already teaches for
Stata: a place with no usable data is nobody's neighbour and still
gets its own row.
THE TEACHABLE POINT, and it is a better one than the bug: the fix was
not new behaviour. The rule was already in the engine, already named
"EquiPop convention" in its own message, and already honoured by
QGIS - so the two GUIs gave DIFFERENT answers to the same question
for a year. Worth a slide for a methods class: when two
implementations of one rule disagree, the interesting question is not
which is faster but which one is wrong, and the answer is not always
the one that crashed.
FOR DEMONSTRATORS: if a student's Pro run dies with "cannot create
NumPyArray", that is a pre-1.53.3 install. And tell them not to
"fix" it by selecting the non-null features - it works, but their
output then has fewer rows than their input, which breaks any
before/after comparison they build on top of it.*
*Reviewed at 1.53.2: ONE SLIDE TO ADD, AND IT IS A GOOD ONE, BUT READ
THE WARNING FIRST.
THE WARNING. Until this release, typing `1,000` or `1.000` in a k box
gave a neighbourhood of ONE PERSON and the run finished normally. The
only sign was a column called `N_1` where `N_1000` was expected. If
any exercise was run with a thousands separator - and a Swedish or
Norwegian keyboard makes that the natural thing to type - **those
results are wrong, not oddly named**. Worth grepping old outputs for
`N_1`, `N_10` and `Mean_*_1` before reusing any of them in class. It
is refused now, per John's ruling, with a message naming the number
it thinks was meant.
THE SLIDE. "How does the software know what you typed?" is a better
lesson than it sounds, because the answer differs BY BOX and the
reason is substantive rather than technical. In a radius box `500,5`
is five hundred and a half metres - half of Europe writes a decimal
that way and it must keep working. In a k box `1,000` cannot be a
decimal, because a fraction of a person is not a thing - which is
exactly what frees the comma up to mean a thousands separator, and
that is why the same character is read two ways one box apart. Ask
the room which reading `300,500` should get. There is no right
answer, and the software now refuses it and says so, which is the
point: **a tool that guesses between two readings is worse than one
that asks.**
AND THE STUDENT-FACING HALF: a dialog that says nothing is wrong is
not the same as a dialog that has checked. machine 2 accepted a k box
holding one space - ArcGIS Pro counts a space as a value - and then
answered with a traceback naming an argument nobody typed. Every door
checks before Run now. If a student reports "it says give k_values",
that is a pre-1.53.2 install.*
*Reviewed at 1.53.1: NOTHING IN THE COURSE CONTENT MOVES - this
release only changes what `equipop doctor` says. But it changes the
FIRST HOUR of every workshop, which is the hour that decides whether
students get to the material at all.
The student installation guide's troubleshooting section can shrink.
A broken install used to produce one line - `rasterio : BROKEN  No
module named 'click'` - and a student who installed click would then
meet `attrs`, then `cligj`, then `pyparsing`, which in a timetabled
session means they are out for the morning. The doctor now names
every missing dependency at once with one command to paste, and it
flags the `~`-prefixed directories that mean an earlier pip run was
interrupted - which on a university machine with antivirus and a
roaming profile is the common case, not the exotic one.
WORTH SAYING OUT LOUD IN THE SESSION, because it generalises past
EquiPop: `WARNING: Ignoring invalid distribution ~yproj` is the line
students are taught by habit to ignore, and it is the most useful
line in the output. `~yproj` is a half-deleted `pyproj`. The lesson
is that pip's warnings are not noise, and that a tool reporting the
FIRST thing it found is not the same as a tool reporting what is
wrong - which is the same lesson as 353, in the room rather than in
the data.
ONE THING FOR THE DEMONSTRATOR, not the students: tell them to close
QGIS and Pro before running pip. A file held open is what leaves the
half-installed state behind, so the fix and the cause are the same
window.*

*Reviewed at 1.53.0: NO FIGURE CHANGES - every course exercise uses
WHOLE population counts and the default raster path is bit-identical,
which is the safety argument for the whole release. TWO THINGS THE
COURSE GAINS, both good ones.
FIRST, a worked example that was impossible before: "here is a place
that had people and now has none." `keep_zero` promised that and did
nothing - a depopulated pixel was simply absent from the output -
and it works now. Denmark's fixture raster carries 1,201 of them. The
lesson it teaches is John's own rule from 1.22.2, which the course
already states for Stata: a place with nobody in it is nobody's
neighbour AND still gets its own result. Students who have met that
rule in one machine can now see it in another.
SECOND, the distinction between a COUNT and a FIELD, which is the one
students most often get wrong and which the software had got wrong
itself. Machine 3 was selecting pixels with `arr > 0`, so a
temperature anomaly with a true mean of -0.005 degC came back as
+1.19 - warming everywhere, every cooling pixel gone, no warning. Put
that on a slide: the arithmetic was never wrong, the QUESTION the
code was asking was. "Is this a headcount or a measurement?" decides
whether zero means empty or means zero, and whether a negative is
impossible or ordinary.
A third, smaller: the demographic indices now say PER ONE in the
field guide. A sex ratio of 0.97 is 97 men per 100 women, and a
student who does not know that reads it as 1%.
*Reviewed at 1.52.0: NO FIGURE CHANGES - every course exercise uses
SQUARE cells, and the square path is an exact identity, which is the
whole safety argument for the hex fix. ONE NEW TEACHING MOMENT, and a
good one: EquiPop had been charging a hexagon a square's area for
eight years because the only thing the engines were told was a LENGTH,
and a hexagon's width and a square's side look identical in a diff.
That is the modifiable areal unit problem arriving inside the
software rather than in the data - which is the course's own subject.
If hexes ever get a box at the GIS doors, the exercise writes itself:
same points, same k, square against hexagon, and the difference is
7.46% on the in-cell radius for a reason students can derive with a
pencil.
*Reviewed at 1.51.2: THIS RELEASE EXISTS FOR THIS FILE'S SAKE, more or
less. John's reason for cutting it was pedagogical: the engine, the
commands, the QGIS plugin and the Pro toolbox are installed by four
different means, so they drift, and a class should not have to be
taught why. Every one of them now says 1.51.2, and the first thing to
do in a session is `equipop setup`, restart Stata, `equipop doctor`:

      engine       : 1.51.2   (the Python package)
      commands     : 1.51.2   (the .ado files)
      needs engine : 1.48.0 or newer - satisfied

SAY WHAT THAT THIRD LINE IS, because a sharp student will ask. It is
not a version, it is a REQUIREMENT - the oldest engine the commands'
own calls need - and it is deliberately older than the release. Two
numbers that must match and one that must merely be satisfied is a
good ten-minute lesson about what a version actually promises, and the
doctor's report is the artefact to teach it from.
A SECOND EXERCISE ARRIVED FOR FREE. Negative populations are refused,
and the refusal now explains itself - so "why can't I put population
CHANGE in pop()?" is a question with a teachable answer: because k
counts people and a neighbourhood grows until it holds k of them, a
total that can fall with distance has no single radius at which k was
reached. Then show the right route: change goes in values(), the
headcount stays in pop(), and the result is a population-weighted mean
of a signed quantity per neighbourhood. That is the distinction
between a WEIGHT and a MEASUREMENT, which is the thing students most
often get wrong in this software, and here the error message teaches
it for you.
Reviewed at 1.51.1: NO FIGURE CHANGES, and one check worth stating
because the release moves numbers for somebody. Every course exercise
uses WHOLE population counts - register rows, census blocks, the
Los Angeles blocks - so the fractional-weight correction cannot touch
a single figure here: rounding 10 to 10 is an identity. It WOULD touch
an exercise built on WorldPop, which is fractional by construction,
and there is no such exercise yet. If one is written, say in class
that the engine carries a fifth of a person as a fifth of a person,
because the naive route - repeat each row `weight` times - is both the
obvious implementation and the one that deleted half of John's people.
TWO THINGS TO MENTION if they come up. A GeoPackage holding several
result layers now gets one provenance sidecar PER LAYER
(out.k100.meta.json, not out.meta.json), which is worth knowing before
a student wonders where the first one went. And the demographic index
tools now refuse a folder that is missing one cohort of one sex, and
name it - which is a better teaching moment than the old behaviour: it
shows what "the data cannot support this measure under its own name"
means in a case where the arithmetic would have worked fine.
THE METHODOLOGICAL LESSON of this release is the best one it has for a
class, and it is not about any feature: the suite had thorough tests
for each option and thorough tests for each engine, and nothing that
crossed the two - so an option could be documented, recorded in the
run's own provenance, and never passed to the engine. Three of the
nine findings were that shape. "Test the pairs, not the parts" is
worth ten minutes of anybody's course.
Reviewed at 1.51.0: no figure or exercise changes. One thing to
mention if anyone asks about radii: a radius now appears in a column
name with its decimal point as an underscore, so r(100.5) gives
N_r100_5, and two radii closer than a millionth cannot be told apart
and are refused rather than quietly merged.
Reviewed at 1.50.0: one change reaches the course, and it is a
good one to say out loud. Every EquiPop run now leaves a record of
the settings that produced it - in QGIS as a .meta.json beside the
output, in Pro inside the run CSV, in Stata printed into the log and
returned in r(). That is the answer to "which run was this?", which
is the question a student asks on the second day and cannot answer
on the first. The test dataset also describes itself now: `describe`
shows a label on every variable.
Reviewed at 1.49.3: nothing in the course changes - this release
is the Stata door and the SSC archive. Worth saying once in class,
though, now that it is true: `ssc install equipop` gets the command
without a clone, and `ssc install equipop, all` brings a worked
do-file and a test dataset with it, which is a gentler first run
than the GIS exercises for a student who already knows Stata.
Reviewed at 1.49.2: no figure changes. One exercise gains a step it
could not have before - the Airbnb listings arrive as
`listings.csv.gz`, and a CSV of coordinates can now be pointed at
directly and written out as a point feature class, instead of being
imported first. That also brings the coordinate-system box into
class: a table declares no projection, so the student either
declares it or gets a layer marked "unknown", which is a small,
concrete instance of the lesson the whole course keeps making - the
software will not guess, and it says what it does not know. Note that
the listings are in DEGREES, so the projection box is not the whole
answer there; they still need projecting, which machine 3's box does
and reports.
Reviewed at 1.49.1: no change to the exercises, but the ratio
ruling is worth a sentence in class - R is a RATIO, and it exceeds 1
whenever numerator and denominator count different units. Every
course exercise uses the same unit on both sides, so all the figures
stand.
A test checks that version against pyproject.toml. If they disagree
the suite fails, because a teaching document that has drifted from the
software is worse than none — a student follows it.*

---

## Why this file exists

Teaching material is not a by-product of the code. **It is the best
acceptance test this project has**, and session 12 proved it twice in
one afternoon:

- John's `CaliData2010` run validated the origin rule against a
  PUBLISHED PAPER — the package reproduces Östh, Clark and Malmberg
  (2015) to seven decimals. Almost nothing else here is checked
  against anything but itself.
- John's Swedish OSM folder found two defects no fixture would have
  shown: 91 of 109 inventory rows were shapefile sidecars, and the
  class vocabulary — the whole point of the tool on OSM — was
  silently optional, vanishing without geopandas into a warnings key
  no door displayed.

Both were found by USING the software the way a stranger will. That is
what this stream is for, and it is why it comes before the installers
and beside the proposal rather than after them.

---

## The worked example: five-county Los Angeles

**Why this one.** It is the only dataset in the project with an
external answer. The five counties — Los Angeles (037), Orange (059),
Riverside (065), San Bernardino (071) and Ventura (111) — are the CSA
behind the 2015 paper, so every number a student produces can be
checked against print.

*(Santa Barbara is a separate MSA and is NOT in the set. Noted because
it came up once and the published figures depend on the boundary.)*

### What exists

| | what | state |
|---|---|---|
| Blocks + race | `CaliData2010.dta`, 708,078 blocks statewide, 157,779 populated in the five counties | HELD BY JOHN, 269 MB |
| k-NN results | `N_/T_/R_/Dist_` at k = 100…800, from the 2014 software | in the same file |
| OSM | roads, land use, water, railways | **NEEDED — see below** |
| Rasters | WorldPop fixtures in `tests/fixtures/worldpop` | tiny, for tests only |

### OSM — supplied session 12, `CalidataOSM.gdb`, LA County

A File Geodatabase, four layers, clipped by John in ArcGIS Pro.
**WGS 84 (CRS84) — degrees**, so a run must project; machine 3's
projection box does it and says which CRS it chose.

| layer | geometry | features | fclass |
|---|---|---|---|
| `roadsLA` | MultiLineString | **735,098** | 28 |
| `landuse` | MultiPolygon | 45,015 | 20 |
| `POILA` | Point | 43,525 | **132** |
| `ProtectedAreas` | MultiPolygon | 435 | 7 |

**735,098 road features for one county.** That is the segmentation
argument made concrete, and the reason "each class once" is the
default: `service` (278,467) and `footway` (206,687) alone are 66% of
them. For exercise 3 the classes that matter are `motorway` (7,216)
and `motorway_link` (9,105).

**132 POI classes, and most of them are street furniture.** The
largest are `restaurant` (5,350), `bench` (4,527),
`camera_surveillance` (3,776), `fast_food` (3,456), `waste_basket`
(2,756). A naive "count POI per cell" would be a map of benches and
bins. THE STUDENT HAS TO CHOOSE WHICH CLASSES COUNT, and that is the
exercise rather than an obstacle to it - it is what the class field
and the value field exist for.

**A number worth using in the lecture:** 43,525 OSM points of every
kind in LA County, and 43,751 Airbnb listings. **There are as many
short-term rentals in Los Angeles as there are mapped amenities of
all kinds put together.**

#### What this found in the software

Machine 6 produced **86 rows of garbage** on this folder: a `.gdb` is
a DIRECTORY and `os.walk` yields files, so the walk descended into the
geodatabase and listed `a00000001.gdbtable` and its siblings while the
four layers were never seen. Fixed in 1.47.6 (BACKLOG 301); the same
folder now gives four rows.

Every fixture until this point was shapefiles and GeoTIFFs. Both are
files. **The format John actually uses in Pro had never been tried.**

### InsideAirbnb — supplied session 12, LA County

`listings.csv.gz`, **43,751 listings**, lat 33.34–34.81, lon
−118.92 to −117.65. 265 neighbourhood names, Long Beach / Hollywood /
Venice / West Hollywood / Santa Monica the largest. 74% entire
home/apt, median price $224, and **65% of listings belong to a host
who has more than one** — the commercial-operator signal, and the
equity hook the exercise hangs on.

**Licence: CC BY 4.0.** Attribution, no share-alike. The simplest of
the three datasets, and unlike OSM it can travel with course material
as long as Inside Airbnb is credited.

**Keep `listings.csv.gz` and `neighbourhoods.geojson`. Drop the
reviews** — 234 MB across two files, one per review, and
`number_of_reviews` is already a column in listings. Nothing in the
exercises needs them.

#### THE 150-METRE PROBLEM, WHICH IS THE BEST LESSON IN THE COURSE

Inside Airbnb's own Data Assumptions state that Airbnb anonymises
listing locations: a point sits **0–150 m from the real address**, and
**listings in the same building are anonymised individually**, so a
forty-unit block appears as forty points scattered over that radius
rather than forty points at one address.

**Both facts bite exactly where EquiPop works.** At a 100 m analysis
cell the displacement is one to two cells, so a small-k run on these
points is partly measuring the anonymisation. And the
same-building scattering SYSTEMATICALLY DISPERSES CONCENTRATION —
the thing a segregation measure exists to detect.

Do not treat this as a defect in the data. **It is the same lesson as
the origin rule, arriving from the other direction**: the origin rule
showed that measured concentration depends on how big the units are,
and this shows it depends on how precisely they are placed. A student
who meets both has met the general point — a concentration measure
reports the data's resolution as well as the world's — and that is
worth more than either exercise alone.

Practical guidance for the exercise: do not run these points below
roughly 300 m cells, read the result as neighbourhood-level rather
than block-level, and SAY WHY. A run that silently uses k=50 on
jittered points produces a confident number about nothing.

### The published anchor

Weighted by the group, over the 78,208 blocks with African American
residents:

    2014 software   mean 0.2752264  sd 0.2464846  min 0.0004955
    EquiPop 1.47    mean 0.2752264  sd 0.2464846  min 0.0004955
    same, i!=j      mean 0.2378486  sd 0.2482518  min 0.0000000

Figure 4 of the paper reads ~0.28. **A student who gets 0.2752264 has
reproduced published research**, which is a better first exercise than
any invented one.

---

## Decided, session 12

**SCOPE: LOS ANGELES COUNTY, WHOLE.** John: "LA is the interesting one
with the diversity and famous parts, so I would go with that county as
a whole (the students' computers will have to deal with it although it
is big)."

RULED AGAINST A SMALL SLICE, and the reasoning is pedagogical rather
than technical: the point of a k-ladder is that neighbourhoods of 100
and of 51,200 are DIFFERENT PLACES, and a clipped study area cannot
show that — the large-k neighbourhoods run off the edge and the
exercise teaches an artefact. LA County has the diversity, the named
districts a student can recognise, and enough population for the top
of the ladder.

**The cost is runtime and it has to be measured, not guessed.** LA
County is roughly 90,000 populated blocks of the five-county 157,779.
Before this is put in front of students, someone times a full run on
an ordinary laptop and the exercise states the number. A student who
does not know whether four minutes is normal will assume it has hung.

**THE ANCHOR MOVES WITH THE SCOPE.** The published 0.2752264 is the
FIVE-COUNTY figure. An LA-County-only run gives a different number,
and it is not in print. Two honest routes: state the county figure as
"what you should get" and cite the five-county one as the published
comparison, or keep one five-county pass purely to reproduce the paper
and do everything else on the county. The second is better teaching —
it separates "reproduce published work" from "now explore" — and it is
the current plan.

**LICENSING: NOT A BLOCKER FOR NOW.** John: one course, his own
students, who can download OSM themselves. So the data is distributed
to a class rather than published, and the ODbL question is deferred
rather than answered. IT RETURNS THE MOMENT the material goes public,
into a paper, or into the repository — see below, which still stands.

---

## What the exercises teach — John, session 12

Five things, in his order. Machines 1 and 2 carry the course; 3 to 6
appear only as far as they must.

1. **k-nearest and r, for shares of population groups.** The core.
   Both neighbourhood definitions on the same data, so a student sees
   what fixing population and letting radius float does, and the
   reverse.
2. **Distance decay.** The same question with a weighted edge instead
   of a hard one.
3. **Friction, with a twist worth the whole exercise.** Highways are
   BLOCKERS FOR WALKING AND FACILITATORS FOR REGIONAL ACCESS. The same
   feature, opposite signs, depending on the question asked. This is
   the best argument in the course for why friction is a per-question
   choice and not a property of the map — and it is exactly what the
   value-field design supports, since the student writes the numbers.
4. **POI, and the skewed distribution of amenities.** Match
   `gis_osm_pois_free_1` to the population and ask who has what
   nearby. Machine 3's join at "each class once" is the tool.
5. **Airbnb (insideairbnb), if supplied.** Listings as a second
   amenity-like layer with an obvious equity question attached.

**Machine 2** gets used for local statistics on the result. **Machines
3 to 6** are means, not subjects: machine 6 to read the OSM folder,
machine 3 to join it. Neither needs teaching in its own right.

### What this implies for the code

- The friction exercise needs a value field per road class, prepared
  in GIS, with DIFFERENT SIGNS for the two questions. Already
  supported, and worth checking that a negative value behaves
  sensibly under `sum` — untested.
- POI are POINTS, so machine 3's join auto-detects and uses the
  centroid rule. Correct, and worth stating in the exercise so the
  student is not puzzled that the fidelity box does nothing.
- Nothing here needs code that does not exist. **That is the useful
  finding**: the course can be written against 1.47.6.

---

## Licensing — deferred, not answered

**US Census data is public domain.** `CaliData2010` can travel freely.

**OSM is ODbL: share-alike with attribution.** A derived extract that
ships inside the repository carries obligations onto the package, and
"derived database" is drawn broadly. Three routes:

- ship the course data OUTSIDE the wheel, alongside it, with its own
  licence file — safest and the default assumption;
- ship only an `equipop_inventory.json` of the OSM folder, which is a
  description rather than the data;
- ship nothing and have students fetch with machine 5, which is what
  machine 5 is for and which teaches the fetch step as a bonus.

The third is the most honest and the most fragile: it depends on
Geofabrik being reachable from a classroom network.

---

## What Claude cannot do here

**Fetch the OSM data.** The sandbox reaches PyPI, GitHub and npm and
nothing else; Geofabrik is not on the list. Machine 5 is exactly the
right tool and cannot be used from this side. The extract, or its
inventory JSON, has to be uploaded.

**Test on a student's machine.** Windows, ArcGIS Pro, a university
network and a locked-down laptop are all outside this container.

---

## Runtime: the barrier exercise is not like the others

MEASURED on the real data, k=332, downtown LA roads:

| box | blocks | seconds | ms per origin |
|---|---|---|---|
| 4 km | 437 | 0.3 | 0.69 |
| 8 km | 1,856 | 5.1 | 2.75 |
| 16 km | 7,456 | 61.4 | 8.23 |

**Cost per origin GROWS WITH THE STUDY AREA.** At k=332 each
neighbourhood is local, so the expansion should cost the same
wherever it sits - but the effort engines build a movement graph over
the WHOLE BOUNDING BOX, empty ground included, and per-origin cost
tracks the size of that graph.

LA County at 100 m is **2.5 million graph cells**: 97 times the 16 km
box for 10 times the origins. Extrapolated, hours rather than
minutes.

AND THE BOUNDING BOX IS WORSE THAN THE COUNTY. LA County is about
120 km tall on the mainland; **Catalina and San Clemente stretch the
extent 90 km further south**, and the graph covers all that ocean.

### Three levers, best first

1. **RAISE THE CELL SIZE.** 250 m takes the graph from 2.5M cells to
   400,000 and collapses blocks into fewer origins. For a barrier
   question at k=332 it is defensible anyway - you are asking which
   side of a motorway somebody is on, not resolving buildings.
2. **SELECT A SUBSET IN PRO AND RUN ON THE SELECTION.** John's note,
   session 12, and it is the neatest of the three: the tool reads
   through the LAYER, so a selection is honoured with no settings
   changed and nothing clipped or exported. Checked rather than
   assumed - the reader passes the layer to
   FeatureClassToNumPyArray, not the catalog path, so BACKLOG 310's
   change to the WRITE target did not affect it.
3. **Drop the islands**, which nearly halves the graph for free.

Exercises 1 to 3 run county-wide in seconds and need none of this.
Only the effort engines do.

## What building it found in the software

**BACKLOG 304 — a rounding error brought back Dist_k = 0**, on 1,213
of 75,109 LA blocks. Under `proportional` the crossing cell
contributes a fraction, the total arrives as 99.99999999999999, and
`n >= k` is false for that float, so the self-potential correction
never fired. It needed data dense enough that the whole neighbourhood
sits inside one cell - 41% of LA County - and no fixture in the suite
was.

**Exercise 1 step 3 asks a student to sort by `Dist_100` and find the
smallest. They would have found a zero on the first attempt.**

That is the third defect this dataset has found, after the geodatabase
and the shapefile sidecars. The pattern is consistent enough to state
as a rule: THE TEACHING MATERIAL IS NOT A CONSUMER OF THE SOFTWARE,
IT IS A TEST OF IT, and it finds things fixtures cannot because
fixtures are written by the person who wrote the code.

## Status

    [x]  OSM supplied: CalidataOSM.gdb, four layers, LA County
    [x]  Scope decided: Los Angeles County, whole
    [x]  Learning objectives written: five, above
    [x]  Licensing: deferred, one course, students download their own
    [x]  insideairbnb supplied: LA County, 43,751 listings,
         CC BY 4.0, 150 m anonymisation understood and turned into
         the lesson of exercise 5
    [x]  Runtime measured: 31 s for 75,109 blocks x 4 k-values x
         3 groups. A minute or two on a student laptop.
    [x]  LA-County anchor computed: African American isolation
         0.3357 / 0.3290 / 0.3201 / 0.3105 at k = 100/200/400/800;
         Asian 0.3613 falling to 0.3369; White alone 0.5963 to
         0.5830. HIGHER than the five-county published figure, and
         correctly so - dropping the low-minority suburbs makes
         everyone look more isolated, which is the spine of the
         course arriving before the software does.
    [x]  Exercise 1 drafted and every number in it verified
    [x]  Dataset built: la_blocks.gpkg (9 MB), la_osm.gpkg (230 MB),
         la_airbnb.gpkg (6 MB), all EPSG:26945
    [ ]  Run end to end by somebody who is not its author
