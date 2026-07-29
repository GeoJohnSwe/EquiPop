# 15. The ArcGIS door: EquiPop where the data already lives

## The idea

Most people who need egocentric neighbourhoods do not live in a
Python prompt. They live in ArcGIS Pro, with the register extract
already loaded, symbolised and half-explored. The toolbox exists so
that EquiPop meets them there — and so that nothing in the meeting
changes an answer.

That last clause is the design. The toolbox is **glue only**: it
moves arrays between Pro and the `equipop` package and does not
compute anything itself. Every number you see in an attribute table
came out of the same functions the test suite guards, the Stata
bridge calls and the answer keys pin down. The door is thin on
purpose, because a door that computes is a door that drifts.

Two tools, two questions. *Counts and Shares* asks how many people
are near me and what proportion of them are something. *Value
Statistics* asks what the values around me look like — the median
income among my nearest four hundred neighbours, the spread, the
Gini. Barriers and terrain are not a third tool: they are
**ingredients** that change what "near" means, which is why they sit
inside machine 1 rather than beside it.

## Coordinates come from the data

Earlier versions asked the user to supply X and Y columns, and
politely suggested renaming things when the names were unfamiliar.
That was backwards. A point layer already knows where its points
are; asking its table for coordinates is asking the wrong part of
the file.

So the loader reads geometry directly. Only when the input is a
plain table — a CSV, an Excel sheet, a geodatabase table — does the
question of coordinate columns arise at all, and then the tool
guesses (`X`/`Y`, `East`/`North`, `Easting`/`Northing`, `POINT_X`,
`XKoord`…), pre-fills its guess, and lets you override it. It never
asks you to rename a column, because renaming someone's data to
suit a tool is a tool's failure, not a user's.

Coordinates must be **metric**, and this is refused rather than
patched over: EquiPop's distances are metres, and a degree is not a
distance. What the refusal adds is the fitting projection, computed
from the data's own extent — a Swedish layer is pointed at SWEREF 99
TM, an Anatolian one at UTM zone 36N. If you would rather not stop,
the *auto-project* checkbox reads a layer on the fly in that
projection and says so loudly; your stored data is never modified.
A bare table cannot be auto-projected: its numbers carry no
coordinate system to project *from*, and guessing would be
invention.

## Barriers, in whatever shape they arrive

Chapter 9 built friction from a table of cells. In the field,
barriers arrive as rivers and railways in a line shapefile, lakes in
a polygon layer, or a friction surface in a raster — and asking a
user to convert those into a cell table by hand is asking them to do
the tool's job.

The barrier input therefore routes by what the thing **is**:

- **lines** charge every grid cell they genuinely cross;
- **polygons** charge every cell they cover, holes excluded, all
  parts of a multipart feature included;
- **rasters** are sampled at analysis-cell midpoints, NoData and
  zero costing nothing;
- **points and tables** snap to their cells.

Two features in one cell need a rule, and the default is
**additive**: a river crossed at a railway costs both, which is what
the ground does. Where stacking is wrong — two overlapping polygons
describing the same marsh, say — max, min and mean are one click
away.

A subtlety worth stating, because it was found the hard way: a cell
is charged only when the feature's presence there has positive
*measure*. A line grazing a cell corner and a polygon touching a
cell edge both have zero presence and cost nothing. Two independent
implementations — one via shapely, one in plain numpy for hosts
whose Python cannot grow geopandas — agree on this cell for cell,
which is how the convention got pinned down.

## Population, and what k counts

Register data rarely gives one row per person. It gives places with
populations: a block of forty, a farm of two. Machine 2's
full-population field takes that seriously — set it, and *k counts
persons*, so a place of forty weighs forty times a place of one in
every statistic, the median and the Gini and each percentile
included. The implementation is deliberately unclever: rows are
expanded to persons before the neighbourhood is drawn, so weighted
order statistics are correct by construction rather than by a
formula that might be subtly wrong at the edges.

Tick only the measures you want. Nv_&lt;field&gt;_k always comes
along: how many neighbours actually had a usable value, so thin
coverage shows up as a number rather than hiding inside an average.

## Reading the messages

The messages pane is where EquiPop is loudest, and in this release
it finally carries the package's own voice as well as the door's:

    Coordinates read from feature geometry (475559 points).
    Working CRS: SWEREF99 TM (EPSG:3006)
    [time] reading input: 0.9 s
    [fast] 422549 cells, k = [444], fast pass with m = 874 cells
    [time] calculating: 1 min 12 s
    [time] writing results to the layer: 3 min 02 s
    [time] TOTAL: 4 min 57 s - most of it in 'writing results'

Three habits pay off. Read the **working CRS**, because every
distance is metres *in that projection*. Read the **stage timings**,
because they name the slow step instead of leaving you to guess —
and on large data the slow step is often ArcGIS writing fields, not
EquiPop computing them. Read `m = N neighbour cells`: it is how many
cells each origin looked at, and it affects speed only, since any
origin not settled inside its neighbourhood is recomputed exactly.

Beside the output, each run leaves a **manifest** — version, working
CRS, whether it was auto-projected, every parameter, row and cell
counts, per-stage timings. A results layer without provenance is a
number without a footnote.

## Pitfalls

**Shapefiles cap field names at ten characters.** `Mean_income_200`
does not fit, and a shapefile target is refused *before* the
computation with that advice rather than after it. Shortening is
available as an opt-in, collision-free by construction — because
truncating `P25_income_400` and `P75_income_400` to the same ten
characters would silently merge two different answers — and the
mapping is printed and saved beside the output. A file geodatabase
has no such limit and is the better home.

**Pro remembers your last run.** That is Pro being helpful, and it
means a field choice can outlive the layer it was chosen for. The
dialog now clears field boxes that don't exist in the current input
and validates the rest before Run, but if a result looks like
someone else's run, suspect a remembered parameter first.

**Effort has a scale ceiling that plain counts do not.** Barriers
and terrain build a movement graph over the whole bounding box,
empty ground included, so they suit a bounded study area rather than
a country at 100-metre cells. The tool estimates the memory in
advance and tells you what to change — usually a larger cell size,
which is in any case the strongest speed control you have: doubling
it quarters the number of origins.

## Under the hood

The toolbox is validated against a **simulated arcpy** — a stand-in
that answers the same calls Pro does, so every glue path can be
exercised in continuous integration on a machine with no ArcGIS
licence anywhere near it. That simulator has caught real bugs
before they shipped, and it is also honest about what it cannot
catch: file locking, schema caching, Pro's parameter memory, DLL
conflicts, and a Swedish locale writing `0,000001` where Python
expects a point. Those arrived from the field, each one now a test.

Which is the closing thought. The simulator proves the logic; only
the field proves the behaviour; and a synthetic town with a
published answer key — Gridby, whose river genuinely divides a
poorer west bank from a richer east — is what turns "it ran" into
"it computed the right thing".
