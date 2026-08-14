# 3. Data in: files, coordinates, and the quiet traps

## The idea

Every analysis in this book starts the same way: a table arrives
with one row per person (or per square), an east–west coordinate, a
north–south coordinate, and some columns describing people. This
chapter is about getting that table into EquiPop safely — and it is
longer than "read the file" deserves, because the traps of this
stage are quiet ones. A wrong half-life announces itself in odd
results; a wrong coordinate system produces maps that look
perfectly plausible and are perfectly wrong.

Reading the file is the easy part. The `read_table` helper opens
the formats register researchers actually meet — comma files,
semicolon files (the Nordic default, since our decimal commas
occupy the comma's job), tab files, Excel sheets, SPSS `.sav`
files, zipped GIS layers — and it *sniffs* rather than assumes:
the separator, the character encoding, the invisible "byte-order
mark" that Windows sometimes hides at the start of a file, all
detected and reported in one printed line. If that line says
"semicolon, 2,699 rows, 6 columns" and you expected commas and
seven columns, you have learned something important for the price
of reading one sentence.

Coordinates deserve the slow paragraph. A coordinate system is an
agreement about what the two numbers *mean*, and there are two
families. Longitude and latitude — the familiar degrees — describe
positions on a globe, and degrees are not distances: a step of one
degree east is 111 kilometres at the equator and half that in
northern Sweden. Distance-based analysis on degrees is therefore
meaningless. The second family, **metric** (projected) systems,
lays a flat grid over a region and counts metres: Sweden's
SWEREF 99 TM, the older Swedish RT90, the international UTM zones.
EquiPop requires the metric kind, and helps you get there: a
one-line conversion projects degrees into metres, and if you do not
know which metric system suits your region, the software will
inspect your coordinates and *suggest* one.

The last idea of the chapter is **snapping**. Register squares are
usually identified by coordinates that follow a convention — the
square's south-west corner, or its midpoint — and different
registers follow different ones. EquiPop snaps every point onto a
clean grid of square midpoints, which makes data from mixed
conventions line up, and prints how far the points moved so a
convention mismatch (a systematic 50-metre shift, say) becomes
visible instead of silent.

## Cook it

```python
from equipop.io import read_table
from equipop.projection import suggest_projection, project_to_metric
from equipop.cells import build_cells

df = read_table("residents.sav")          # sniffed and reported
# if the coordinates are degrees:
print(suggest_projection(df, lat_col="lat", lon_col="lon"))
# or, in EquiPop's usual order:  suggest_projection_xy(df, "x", "y")
df = project_to_metric(df, "lon", "lat", crs="EPSG:3006")  # SWEREF 99

cd = build_cells(df, "x", "y", binary_vars=["HighEdu"],
                 value_vars=["income"], unit_size=100)
```

Rows with missing coordinates are dropped at the `build_cells`
step — **with a printed count**, in the family tradition — because
a person who cannot be placed on the map cannot have a
neighbourhood; their other columns are untouched, and chapter 16
shows how such rows simply receive missing results when working
inside Stata.

## The dials

`read_table` accepts explicit overrides (separator, sheet name,
layer name) for the rare file that defeats sniffing; `unit_size`
sets the grid; `assign_zones` attaches administrative-area labels
from a polygon file to every point, which chapter 4's area mode and
chapter 14's aggregations both use.

## Under the hood

Why 100-metre squares? Partly tradition — Nordic registers deliver
at that resolution — and partly a genuine sweet spot: fine enough
that snapping moves a point at most 71 metres (half a diagonal),
coarse enough that a whole country stays computable (chapter 2's
memory argument). The snapping itself is a floor-division to the
grid, plus half a square — deterministic, reversible in spirit, and
identical across every engine so that all chapters' results align
square for square.

## Pitfalls

A war story, because it teaches better than a rule. A Swedish
dataset once arrived with columns proudly named after SWEREF 99 —
and coordinates that were actually RT90, the *previous* national
system. The numbers looked reasonable; the two systems differ in
ways a tired eye forgives; and every distance would have been
subtly wrong. The tell was the value range: SWEREF 99 TM eastings
in Sweden live roughly between 250,000 and 950,000, while RT90
eastings run about 1.2 to 1.9 million. **Column names are
testimony; value ranges are evidence.** Thirty seconds with
`df.describe()` before any analysis — checking that the coordinate
ranges are plausible for the system you believe you have — is the
cheapest insurance in this entire book. And one more habit from the
same family: registers sometimes mix corner-coded and
midpoint-coded squares; if a joined dataset refuses to line up,
check whether one side's coordinates are all divisible by 100 and
the other's all end in 50.
