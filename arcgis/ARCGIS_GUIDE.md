# EquiPop for ArcGIS Pro - setup and first run

*Pro only (Python 3). Ten minutes the first time, zero thereafter.*

## 1. One-time: give Pro's Python the EquiPop package

ArcGIS Pro ships its own Python inside a conda environment, and the
default one is locked. The supported route is a clone:

1. In Pro: **Project -> Package Manager** (older versions: Python tab)
   -> **Environment Manager** -> select `arcgispro-py3` -> **Clone**.
   Name it e.g. `arcgispro-equipop`. (A few minutes.)
2. **Activate** the clone in the same dialog, restart Pro when asked.
3. Start menu -> ArcGIS -> **Python Command Prompt** (it opens inside
   the ACTIVE environment) and run:

       pip install equipop

4. Check: `python -c "import equipop; print(equipop.__version__)"`

### Files to copy (v1.16.8)
Keep these FOUR files together in one folder (e.g. `C:\Data\EQP`):

    EquiPop.pyt                     the toolbox
    EquiPop.CountsShares.pyt.xml    in-dialog help for machine 1
    EquiPop.ValueStatistics.pyt.xml in-dialog help for machine 2

The .xml files are what puts the small explanation beside each
parameter box. Pro caches toolboxes hard: after replacing them,
remove the toolbox from the project and add it again, or restart
Pro.

## 2. Add the toolbox to a project

Copy the `arcgis/EquiPop.pyt` file anywhere convenient (it can live
in the project folder). In Pro's **Catalog** pane: right-click
**Toolboxes -> Add Toolbox** -> pick the .pyt. Two tools appear
under "EquiPop".

## 3. First run (Counts and Shares)

Open **1. Counts and Shares**, pick your point layer of people,
choose a 0/1 group field, type `200 1600` under k, optionally a
decay half-life like `3000`, and run. New double fields appear on
the layer: `N_200`, `R_<group>_200`, `Dist_200`, ... and `ND_inf`
if decay was on - ready for **Symbology** or a join. Rows without
geometry get Null, as they should.

Tool 2 does income: pick numeric fields, statistics `mean median
gini`, k - fields like `Med_income_400` and `Gini_income_400`
appear. Tool 3 takes a barrier csv (`x,y,friction` in the SAME
metric coordinate system as the layer) and returns `Rounds_k` and
`N_tau...` isochrone counts.

## 4. Three things worth knowing

- **File geodatabase beats shapefile**: shapefiles truncate field
  names to 10 characters; the tool warns, but a gdb layer is the
  honest home for `Gini_income_400`.
- **Metric coordinates required** (metres - SWEREF 99, UTM...), the
  book's chapter 3 rule; reproject with Pro's Project tool first if
  needed.
- **Re-running**: results are appended; re-running with the same
  parameters overwrites those fields via the join. Different k
  values simply add more fields.

## 5. When something fails

"No module named equipop" -> Pro is not using your clone: Package
Manager, activate the clone, restart. Anything else -> the message
window shows the package's own loud diagnostics; copy them to the
maintainers (or to Claude) verbatim.


## 6. Troubleshooting - the field-tested ladder (v1.14)

Every step below was walked in a real failing installation; walk it
in order.

1. **Which Python is Pro using?** Python window:
   `import sys; print(sys.exec_prefix)` - NOT sys.executable, which
   in Pro's embedded window is ArcGISPro.exe itself (using it for
   pip LAUNCHES A SECOND PRO - do not ask how we know). The prefix
   must end in your CLONE's name; `arcgispro-py3` means the clone is
   not active: Environment Manager -> activate -> full Pro restart.
2. **The stowaway check.** `pip show equipop` may claim the package
   exists while Pro cannot import it: read the **Location** line. If
   it says `AppData\Roaming\Python\...` the package was stranded by
   pip's silent "user installation" fallback in a folder Pro NEVER
   READS. Evict and reinstall with the fallback disabled:

       import sys, os, subprocess
       py = os.path.join(sys.exec_prefix, "python.exe")
       env = dict(os.environ, PYTHONNOUSERSITE="1")
       subprocess.run([py, "-m", "pip", "uninstall", "-y", "equipop"])
       subprocess.run([py, "-m", "pip", "install", "equipop"],
                      env=env)

   Restart Pro (it binds packages at startup).
3. **Version check.** `import equipop; print(equipop.__version__)` -
   the toolbox needs >= 1.14.0 for the category mode and output
   options.

## 7. Reading the results honestly

- `Dist_k` is in METRES and that is the point: it is the radius each
  point needed to gather its k persons - k fixes the population, the
  geography floats. The tool prints this reminder whenever the
  column appears.
- If a share exceeds 1 or N looks smaller than T, the group field
  holds COUNTS while the Population field was left empty - the tool
  now prints a hint the moment it sees that pattern. Set Population
  to the total-persons field.
- Category mode: rows outside the population filter get Null in
  every result column - they were not part of the analysis, and
  Null says so.


## 8. v1.15 - two tools, several rulers

Machine 3 is retired - not removed, PROMOTED: friction and terrain
are now DISTANCE INGREDIENTS on tool 1. Add a barrier table (ANY
table Pro can open - gdb, dbf, csv, registered txt; coordinate
columns found by name automatically: x/y, East/North, POINT_X/Y...)
and/or a DEM raster, and the same counts-and-shares analysis runs on
the effort ruler: Rounds_k and N_tau# columns appear, the effort
dials reveal themselves, and - the point of the redesign - your
populations, groups, categories and weights all work ACROSS THE
WATER exactly as on flat ground. Both ingredients together = rivers
AND hills in one run. Runtime note: the effort engines cost real
time on large layers; the tool says so when they engage.

Rivers as LINES: in Python, `equipop.friction.features_to_friction`
turns line/polygon features with a friction field into the barrier
table (overlaps stack additively); a one-click Pro wrapper for it is
on the roadmap.


## 9. v1.16 - the GIS input rework (what changed for you)

**Coordinates come from the data, not from column names.** Point
layers are read straight from their geometry - no X/Y columns are
ever required. Plain tables (CSV, Excel, gdb tables) get their
coordinate fields guessed and pre-filled, and you can always
override the guess. Nothing ever asks you to rename a column.

**Coordinates must be metric.** Degree data is refused with the
projection that FITS your data computed from its own extent (Uppsala
gets SWEREF 99 TM, Kayseri gets UTM zone 36N). If you tick
*Auto-project degree data*, a LAYER is instead read on the fly in
that projection - your stored data is untouched, and the messages
say which CRS was used. A plain table cannot be auto-projected: its
numbers carry no CRS to project from.

**Barriers are geometry-aware.** One input accepts a point, line or
polygon layer, a table of cells, or a raster. Lines charge every
grid cell they genuinely cross, polygons every cell they cover
(holes and multipart handled), rasters are sampled at analysis-cell
midpoints with NoData and zero costing nothing. Where features share
a cell the *overlap rule* decides: additive by default (a river
crossed at a railway costs both), or max / min / mean.

**Machine 2 knows about population.** Set the full-population field
and k counts PERSONS - the median, the Gini and every percentile are
population-weighted, exactly, by expanding rows to persons. Tick
only the measures you want; only those are computed. Nv_<field>_k
always reports how many neighbours actually had a value.

**Output.** Results append to the input layer, or go to a new
feature class, or - for table inputs - to a .csv carrying your
coordinates and the original row order. Shapefiles cap field names
at 10 characters, so long result names are refused BEFORE the run
with advice; a file geodatabase has no such limit. If you tick
*Allow shortened field names*, names are shortened without ever
colliding and the mapping is printed and saved beside the output.

**Re-running is safe.** Fields that already exist are updated in
place, so nothing is deleted and a map layer never loses sight of
its own file. After writing, the tool re-reads the target and tells
you which fields really arrived, naming the dataset.

**Every run leaves a manifest** - `<output>_EquiPop_run.csv` - with
the EquiPop version, the working CRS (and whether it was
auto-projected), every parameter, the row and cell counts and the
per-stage timings. Keep it with the results and the run is
reproducible a year later.

### Reading the timings
The messages pane now shows where the time went:

    [time] reading input: 0.9 s
    [time] calculating: 4 min 44 s
    [time] writing results to the layer: 1 min 49 s
    [time] TOTAL: 6 min 58 s - most of it in 'calculating'

The package's own notes appear too (`[fast]`, `[stats]`, `[cells]`).
Two lines are worth understanding:

- `fast pass with m = N neighbour cells` - how many cells each origin
  looked at. It affects SPEED ONLY: any origin not settled inside
  that neighbourhood is recomputed exactly.
- `N sparse origins need a wider search` - thin-population origins
  climbing to a wider search. A handful is normal; a storm of them
  usually means a decay run whose truncation distance is large.

**The strongest speed control is yours: cell size.** Doubling it
quarters the number of origins. For decay runs, the *decay cutoff*
box is the second: 1e-6 (default) reaches about 20 half-lives, 1e-3
about 10 and runs roughly four times faster.

### Scale ceilings, honestly
Plain counts and statistics run comfortably at national scale (475k
points, k=444 with a radius: about a minute of calculation). The
EFFORT engines - barriers and DEM - are different: they build a
movement graph over the whole bounding box, empty ground included,
so they suit a bounded study area rather than a country at 100 m.
The tool estimates the memory first and tells you what to change.
