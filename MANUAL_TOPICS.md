# EquiPop (Python) — User Manual by Topic

*For beginners through to all functions and settings. The release
history, validation record and design-decision log live in
MANUAL.md (the development manual), which serves as this document's
scientific appendix.*

## 1. Installation
Requires Python ≥ 3.10. With Anaconda: create an environment once
(`conda create -n equipop python=3.12 -y`, `conda activate equipop`),
then `pip install equipop` — or, working from source, unzip the package
folder and work inside it. Optional extras: `pip install
equipop[geo,io,viz]` adds shapefile/raster support, Excel/SPSS reading,
and mapping. In Jupyter always install with `%pip` (not `!pip`) and
restart the kernel afterwards.

## 2. File formats and data management
`read_table(path)` reads csv/tsv/txt/dat (separator auto-sniffed:
tab, semicolon, comma, pipe; BOM handled), Excel (`sheet=`), parquet,
JSON/GeoJSON, SPSS `.sav`, and — with the geo extra — shapefile,
GeoPackage (`layer=`, see `list_layers()`), OSM `.pbf`, and zipped GIS
archives (auto-extracted). Line/polygon layers become representative
points with a printed note: point representation is a conscious choice.
`save_output(df, path)` writes csv/tsv/xlsx/parquet/json, and gpkg/shp
with point geometry (`epsg=`). Rasters: `rasters_to_points({"pop":
"t_*.tif", ...})` sums matching GeoTIFFs per variable with grid/CRS
checks and mass-conservation totals. Remote sources: `fetch(url,
workdir, unzip=True)` downloads with caching. Missing coordinates are
dropped with a warning; missing values in a variable keep counting
towards k but not towards that variable's statistics (`Nv_` columns).

**Getting data: look, select, fetch (1.58.0).** In QGIS, tool 5a lists
what WorldPop has for some countries and years, and 5b what Geofabrik
has for some regions, as a table - one row per file or layer, with its
size, date and licence. Nothing is downloaded. Open the table, select
the rows you want (Select by Expression: `"sex" = 'f' AND "age_from" >=
15`, or `"layer" = 'roads'`), and run 5c with *Selected features only*
ticked: it downloads exactly those rows, records each in
`equipop_fetch.json` with its checksum, and keeps the rows as
`equipop_recipe.csv` to fetch again. From Python the same is
`browse_worldpop(...)`, `browse_geofabrik(...)` and `fetch_rows(rows,
folder)` in `equipop.doors.catalogue` and `equipop.doors.fetchrows`.
Two rules worth knowing: rows for several years come from ONE series
whenever one covers them all, and the row says so when none does; and
OpenStreetMap for past years comes from raw `.pbf` extracts, so with
years every row - today's too - is taken the same way.

## 3. Projections
All analysis happens in METRIC coordinates - degrees are unequal-sized.
`project_to_metric(df, lat_col, lon_col, target_epsg=None)` reprojects;
with no EPSG given a UTM zone is suggested from the centroid. For
advice first: `print(suggest_projection(df))` - single zone, two-zone
(primary + secondary + the A/B tiled workflow via `assign_zones`), or
continental recommendations with explicit distortion warnings. Data
already in metres needs no projection; verify what CRS it truly is
(column names can lie - check coordinate ranges).

## 4. Grids or hexagons
Square grid: `snap_to_grid(df, unit_size=100)` snaps to midpoints
(...50, ...150), then `build_cells(...)` (individual rows; duplicates
welcome) or `aggregate_to_cells(...)` (already-aggregated counts).
Hexagons: `build_hex_cells(df, e_col, n_col, hex_size=100, ...)` -
hex_size is width across flats, the analogue of unit_size; internally
axial/cube indexing (q+r+s=0). Original coordinates are always kept.
Choosing unit size: smaller preserves locality but slows computation;
the binning preview logic (share of unique vs co-located points at
candidate sizes) guides the choice. Grid-vs-hex differences are largest
at small k and wash out with scale.

## 5. Selecting k-values
k is neighbourhood scale measured in PEOPLE, not metres. The classic
doubling series 12, 25, 50, ..., 12800 (and beyond) reflects population
composition well and log-transforms nicely. Interpretation anchors:
k≈100 a local neighbourhood, k≈6400 a community, k≈51000 a small city.
Reported counts slightly overshoot k (whole cells are added at once);
`N_k` holds the factual count, `Dist_k` the distance at which k was
reached (0 = satisfied within the origin cell). k above the reachable
population yields partial results, never nothing.

## 6. Determining decay
Off by default. `Decay(half_life_m=8000)` gives negative exponential
weighting with weight exactly 0.5 at 8 km; models: negexp, expnormal,
expsqrt, lognormal, power (all half-life parameterised; they differ
strongly in tail weight). k-thresholds remain defined by RAW counts;
decayed values (ND/TD/RD) are recorded at the same moment, so decayed
<= raw always. Add custom models with one line in `decay.MODELS`.

## 7. Determining friction
Friction constrains growth to the logic of the landscape: a cell with
friction f is entered f rounds late (`round(j) = round(i) + 1 +
friction(j)`); neighbourhoods travel fast along low-friction paths and
refuse to jump barriers. Build the friction table on the SAME grid as
the population (`load_friction_table` cleans malformed rows and sums
overlapping layers); `default_friction` decides what unlisted cells
cost - 0 means the file lists barriers; the max means the file lists
fast roads. Run with `run_knn_friction(pop, k_values, fr=...)`; output
adds `Rounds_k`. Coverage below 80% of the analysis extent triggers a
warning.

## 8. Which engine?
`run_knn_counts` - vectorised fast path for counts/ratios (KD-tree;
73k origins in under a minute). `run_knn_stats` - value statistics
(mean/median/SD/SE/Gini/entropy) needing per-cell individual values.
`run_knn` - the ring engine with decay and legacy-compatible naming.
`run_knn_friction` - friction growth. All share the ring-atomic tie
convention: equidistant cells count as one atomic ring
(`tie_mode="sequential"` with a `seed` reproduces the original C#
behaviour instead).

## 9. Statistics
Requested per variable: `stats={"treated": ["ratio","sd","se",
"entropy","gini"], "income": ["mean","median","sd","se","gini"]}`.
Three exactness tiers: binary statistics are exact from counts alone;
continuous mean/SD/SE exact from moments; continuous median/Gini need
individual-level in-data (rows with duplicate coordinates). Binary Gini
reduces to 1 - p; entropy is in nats. `mld` (mean log deviation) and
`theil` are inequality indices for incomes: MLD refuses a zero, Theil
accepts one, and both split between and within groups - section 10.
Add statistics with one line in `stats.VALUE_STATS`.

## 10. Inequality between and within groups
**The question.** Among the k people nearest each place, how unequal
are incomes - and how much of that inequality lies BETWEEN groups
(born in Sweden or abroad, parental education) rather than WITHIN
them? Machine 2 answers with the two indices that split exactly into
those two parts: the mean log deviation (MLD) and the Theil index. The
Gini does not split this way - it leaves an overlap term - so it has no
split. The split never changes the neighbourhood: k still counts
everybody.

**Asking for it.** Tick MLD, Theil or both among the measures, and name
the grouping field: in QGIS *2c ▸ ...split MLD / Theil BETWEEN and
WITHIN the groups of this field*, in Pro *Split MLD / Theil BETWEEN
and WITHIN the groups of this field*. In Python, through the entry
both doors use:

```python
import numpy as np
from equipop.stata_bridge import dispatch

res = dispatch("stats", np.full(4, 50.0), np.full(4, 50.0), unit_size=100,
               k_values=[4],
               values={"income": np.array([1.0, 3.0, 4.0, 4.0])},
               stats={"income": ["mld", "theil"]},
               decompose_by={"grp": np.array(["A", "A", "B", "B"])},
               min_group=0)
```

The grouping field may hold text or codes, up to 20 groups; a blank,
NaN or Stata missing means "no group". The Stata door does not offer
the split: `ineqdeco` does it natively.

### One neighbourhood, worked by hand
Four people share one cell, so at k = 4 each has the same
neighbourhood: all four. Group A earns 1 and 3, group B earns 4 and 4.
The mean is 3; A's is 2 and B's is 4. (`min_group=0` because each group
holds two people: with the default minimum of 30 the split would be
empty - see below.)

| Column | Value | What it is |
|---|---|---|
| `Nv_income_4` | 4 | people with an income |
| `MLD_income_4` | 0.1308 | MLD over everyone: the mean of ln(3 / y) = (ln 3 + ln 1 + 2 ln ¾) / 4 |
| `MLDb_income_4` | 0.0589 | BETWEEN: the MLD if everyone earned their group's mean = ½ ln(3/2) + ½ ln(3/4) |
| `MLDw_income_4` | 0.0719 | WITHIN: each group's own MLD, weighted by its share of the PEOPLE = ½ × 0.1438 + ½ × 0 |
| `MLDsh_income_4` | 0.4502 | the between-group SHARE, b / (b + w) |
| `Theil_income_4` | 0.1002 | Theil over everyone: the mean of (y / 3) ln(y / 3) |
| `Theilb_income_4` | 0.0566 | BETWEEN = ½ (2/3) ln(2/3) + ½ (4/3) ln(4/3) |
| `Theilw_income_4` | 0.0436 | WITHIN: each group's own Theil, weighted by its share of the INCOME = (4/12) × 0.1308 + (8/12) × 0 |
| `Theilsh_income_4` | 0.5650 | the between-group share |
| `Ng_income_4` | 2 | groups present |
| `NgMin_income_4` | 2 | people in the smallest group present |
| `NgN_income_4` | 4 | people the split covers: a value AND a group |

Three things to read off it:

- **b + w is the index, exactly**: 0.0589 + 0.0719 = 0.1308, and
  0.0566 + 0.0436 = 0.1002. That is what makes these two indices the
  right ones, and EquiPop's tests hold it to 1e-11 in every overshoot
  mode, with fractional people.
- **The two indices give different shares** - 45% and 56% here -
  because they weight the within part differently. Group A, the
  unequal one, holds half the people but a third of the income, so it
  counts for less under Theil. Neither is wrong; say which you used.
  MLD is the more sensitive to the bottom of the distribution, and it
  refuses a zero income: the log of zero has no value, and replacing
  the zero with a small number makes that number the answer. Theil
  accepts zeros.
- **When some people have no group**, they stay in `MLD_` and `Nv_`
  and are left out of the split. `NgN_` is then below `Nv_`, and
  b + w is the index of the people the split covers.

### Empty, never zero
The between, within and share columns are EMPTY - not zero - where

- only one group is present: there is no between to measure, and a
  zero would read as a finding;
- a group present holds fewer people than the minimum - 30 unless you
  set it (*2d ▸ ...smallest group* in QGIS, *Smallest group* in Pro,
  `min_group=` in Python; 0 means no minimum). Between-group inequality
  is biased UPWARD when a group is small: a handful of people have a
  noisy mean, and noise between means reads as inequality between
  groups;
- nobody in the neighbourhood has a value.

The share alone is also empty where everybody has the same income:
between and within are then 0, there is nothing to split, and 0/0 is
not a share. `Ng_`, `NgMin_` and `NgN_` are always written, so a
reader can see which reason applies. And the run says how many places
there were, per field and k:

```
[decompose] income, k=100: split reported in 1,563 of 5,000 places; empty in 3,437 - only one group present: 88; a group below 30 people: 3,349. In 4,810 places the split leaves out people with a value but no 'cob' (NgN_ below Nv_).
```

### Why the empty area shrinks as k grows
The minimum counts PEOPLE, not a share, on purpose: the noise in a
group's mean depends on how many people it holds, not on what fraction
of the neighbourhood they are. So the same 30 asks a group to be 30% of
a neighbourhood of 100 and 1.9% of one of 1,600. Larger neighbourhoods
also reach across the places where groups cluster, so "only one group
present" falls too.

The line above is from a synthetic town of 5,000 people, one in five
born abroad and concentrated towards its eastern edge, with 3% whose
country is not recorded (`tests/test_manual_split.py` builds it):

| k | a group must be at least | places empty, of 5,000 | only one group present | a group below 30 |
|---|---|---|---|---|
| 100 | 30% | 3,437 | 88 | 3,349 |
| 400 | 7.5% | 2,592 | 0 | 2,592 |
| 1,600 | 1.9% | 0 | 0 | 0 |

So at a small k, the default minimum maps the split only where both
groups are well represented. If that is not where you need to look,
raise k rather than lower the minimum: a lower minimum reports the
small-group places WITH the upward bias it exists to keep out.

**What it is not called.** Not "inequality of opportunity". Whether a
between-group share measures opportunity depends on whether the
grouping is a circumstance beyond a person's control - a judgement
for the analysis, not the tool. What EquiPop computes is the ex-ante
kind: groups compared by their means.

**Cost.** Small: measured on 50,000 points at k=400, one field split
into twenty groups took 28 s against 20 s unsplit.

## 11. Segregation measures
`seg_profile(knn_out, k_values, ...)` returns one row per scale plus an
aspatial 'local' baseline: D, segregation Gini, entropy H, Atkinson(b),
Isolation, Interaction, Correlation V, and SI (the 2015 paper's
population-weighted k-share isolation). Units at scale k are the
bespoke neighbourhoods. Concentration/delta indices await a bespoke
area-term decision.

## 12. Area-based output
`aggregate_output(df, by=..., how="wmean")` summarises overlapping
bespoke results per fixed geography - by belonging ID column, by
uploaded polygons (`id_field=`, `points_epsg=` for CRS-aware joins), or
by a coarser supergrid size in metres. This is individualised context
reported per area, not areal recomputation - state that in your methods
section.

## 13. Maps
`map_output(df, "R_VM_1600", cell="square"|"hex"|"point",
classing="jenks"|"quantiles"|"equal"|"sd", n_classes=6,
save="map.png")` - classed legend, scale bar, north arrow; export to
png/svg/pdf. For real cartography, `save_output(..., "out.gpkg")` and
style in QGIS.

## 14. Metadata and reproducibility
Wrap runs in `RunLog(settings={...})`: `add_input()` records md5 hashes
and CRS decisions, `event()` captures warnings, `finalize(df,
"out.csv")` writes `out.meta.json` (six sections + full column
definitions) and a readable `.meta.txt`. Written progressively - a
crashed run still leaves its record. Put your seed and every deliberate
choice in settings; the meta file is your methods section's receipt.

## 15. Troubleshooting
`ModuleNotFoundError` in Jupyter: `%pip install <pkg>`, restart kernel.
Nordic CSVs: separator is sniffed, but check the row count. Coordinates
that "look wrong": compare ranges against the claimed CRS. Slow runs:
switch to `run_knn_counts`; very large areas: tile with A/B zones.
Everything the engines print is also captured by RunLog.
