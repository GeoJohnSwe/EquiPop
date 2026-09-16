# TEACHING.md — the course material, and what it still needs

**Last updated: 1.47.7, 16 September 2026.**
*Reviewed at 1.47.6: the OSM geodatabase and the InsideAirbnb
extract both arrived and are described above; the .gdb finding
(BACKLOG 301) came out of them.
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
