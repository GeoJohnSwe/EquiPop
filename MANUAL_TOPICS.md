# EquiPop (Python) — User Manual by Topic

*For beginners through to all functions and settings. The release
history, validation record and design-decision log live in
MANUAL.md (the development manual), which serves as this document's
scientific appendix.*

## 1. Installation
Requires Python ≥ 3.11. With Anaconda: create an environment once
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
kind: groups compared by their means. The question across the whole
population - how much of inequality lines up with the KIND of
neighbourhood people come from, and at what scale - is section 17.

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

## 16. Rates and life expectancy from an age pyramid (machine 4)
*v1.60.0.* An age-and-sex raster folder holds people, not births or
deaths, so no rate can be *measured* from it. Machine 4 *estimates*
them, and every output says so:

    run_indices(folder, [], vital=["life_expectancy_60",
                "total_fertility_rate", "crude_birth_rate",
                "crude_death_rate"], k_values=[5000])

Machine 4 can start from a folder of rasters, or - since 1.60.1 -
from the point layer machine 3 made from one (`points=`, with
`points_crs=` its coordinate system). The two give the same numbers.
In a point layer a blank cohort value is read as nobody - counted per
field in the log and kept in the record as `blanks_as_zero` - while
text, a negative number or an infinity is refused by field. Plain
x/y coordinates need their coordinate system; lon/lat and machine 3's
EastWest/NorthSouth are read as degrees when they fit.

**Every formula** - sections 2 to 5 below in full, with the
assumptions and references - is in `METHODS_RATES.md` (in the release,
and inside the installed package as `equipop/METHODS_RATES.md`).

**Whose nation (since 1.61.0).** By default each person is read
against their OWN country (`vital_reference="own"`): a neighbourhood
across a border pools both sides, each against its own nation, and
lands between the two nations rather than jumping where the reference
flips. Within one country this is exactly the older rule,
`vital_reference="cell"` - the whole neighbourhood against its cell's
country. Machine 4 can also run TILED (`out_dir=`, box 2e), as
machine 3 can, for merged regions larger than memory.

**How.** Each neighbourhood's age pyramid is read **against its
nation's**. The nation's own age patterns come from UN World Population
Prospects 2024, which ships with EquiPop for 236 countries, 2000-2030.
The nation's pyramid is the folder's own total for that country, so
give whole countries. Since 1.60.2 the log warns when a country holds
under 90% of WPP's population for it (WorldPop's totals are matched
to the UN's, so a whole country comes close to 100%), and the run's
record keeps each share as `vital.national_coverage`.
- **Life expectancy:** if every cohort had started equally large and
  nobody moved, the pyramid *would* be the life table. It is not -
  births grew - so the local share of each age is divided by the
  national share, and the nation's birth history cancels out.
- **TFR:** the children under five per woman, with the women weighted
  by the nation's fertility at their age, relative to the same ratio
  nationally (the approach of Hauer & Schmertmann, *Demography* 2020).
- **CBR:** births a year per 1,000 people, from the same reading.
- **CDR:** the nation's death rates below 60, and from 60 the level the
  neighbourhood's e60 implies.

**How far to trust it.** Tested on simulated populations with known
answers:
- Life expectancy at 60 (`e60_k`) holds up. It stays within about two
  years when local growth differs from the nation's, and is untouched
  by young migrants.
- From 50, 30 and birth it does not. A neighbourhood growing faster
  than the nation, or drawing young adults, reads as one with different
  mortality. Those columns end in **u** (`e50u_k`, `e30u_k`, `e0u_k`),
  are labelled UNRELIABLE in the log, and are meant as predictors in a
  model, not as life expectancies.
- Use a **k of 5,000 or more** for life expectancy; fewer people leave
  the oldest bands nearly empty.

**Before publishing,** check the estimates against places where the
real figure is known (for Sweden, SCB publishes life expectancy by
municipality). Cite UN WPP 2024 for the national schedules, under its
licence: CC BY 3.0 IGO.

## 17. Inequality of opportunity across scales: θ(k)
*New in 1.62.0, in Python only for its test round; corrected in 1.62.1
after an external review.* Section 10 splits
inequality INSIDE each neighbourhood. This asks the reverse question,
over everybody: how much of the inequality of an outcome lines up with
the KIND of neighbourhood people come from - and at what neighbourhood
size that is strongest.

**The steps.**
1. An **outcome** and the **people** it is measured on: adult income,
   say, for everyone aged 30-40, each placed where they grew up.
2. One neighbourhood **character**: the share of the k nearest people
   with low education (a 0/1 field gives a share; any other number
   gives a mean). EquiPop measures it around each person, for every k
   asked for.
3. **Types.** Everyone is lined up by that character and the line is
   cut into equal-sized groups - 10 unless `groups=` says otherwise. A
   type is one group: "the tenth from the most disadvantaged
   neighbourhoods at this k".
4. The outcome's inequality (MLD; Theil if it has zeros) is split
   exactly into the part BETWEEN the types and the part WITHIN them.
   **θ(k) = between ÷ total.**
5. Repeated for each k, the profile shows the scale at which the
   neighbourhood lines up most with the outcome.

```python
import equipop
prof = equipop.theta_profile(
    people,                        # one row per person, metric x / y
    outcome="income", character="low_edu",
    family="parents_edu",          # optional: what is ON TOP of family
    k_values=[100, 200, 400, 800, 1600, 3200, 6400],
    context=adults,                # optional: whom the neighbourhood is made of
    groups=10)
```

**What comes back**, one row per k (shares, so 0.06 is 6%):

| column | what it is |
|---|---|
| `theta` | between the types ÷ total |
| `theta_nogroups` | the same with no groups: the inequality of the outcome predicted from the character (a quadratic fitted to the outcome itself) ÷ total - what θ approaches as the groups get finer. If `theta` is far below it, the groups are too coarse. Empty, with a `note`, if the fit predicts an outcome of zero or below |
| `noise`, `noise_p95` | θ with the outcome shuffled among the same people (99 times by default): its mean and 95th percentile - what chance alone gives. About (groups − 1) ÷ people |
| `p_value` | the share of shuffles that reach θ, counting θ itself: (1 + shuffles ≥ θ) ÷ (1 + shuffles). 0.01 is the smallest with 99 shuffles. The run names a peak only where it is 0.05 or less |
| `groups`, `smallest_group` | groups formed (people sharing a cell share a group, so ties can merge two), and the smallest |
| `theta_family` | with `family=`: family background alone |
| `theta_on_top` | what the neighbourhood adds on top of family: θ(groups × family) − θ(family) |
| `noise_on_top`, `noise_on_top_p95`, `p_value_on_top` | the same, with the outcome shuffled only WITHIN each family category |
| `note` | why a row, or a column of it, is empty |

**Why equal-sized groups, and why 10** - measured on a synthetic town
with the effect planted at 800 people. The profile peaked at 800
however the types were formed, so the choice moves the LEVEL, not the
scale. Too few groups understate: 3 groups gave 76% of the no-groups
value at the peak, 5 gave 90%, 10 gave 97%, 20 gave 99.5% (1.62.1).
Fixed
cut-offs (under 10%, 10-20% ...) are not offered: bigger neighbourhoods
are more alike, so the outer groups empty as k grows - five types at
k = 25, three from k = 3,200 - and the k's stop being comparable. Too
MANY groups add noise: with 2,000 people and no relationship at all,
100 groups gave θ = 5.7% from chance. The chance columns measure that
on your own data, and the run says where θ is not clearly above it.

**On top of family.** "Neighbourhood alone" mixes the place with who
lives there. In a town where only family background mattered and
families with low-educated parents clustered, the neighbourhood alone
gave 1% - and 0.00% on top of family. So give `family=` whenever the
people carry it (registers that link generations often do so only for
the younger cohorts - under about 40 - which is where to start).

**Choices that matter.**
- The person's OWN 100 m cell is left out of their neighbourhood
  (`self_rule="exclude"`): otherwise a small neighbourhood is largely
  their own household, and θ at small k measures family twice.
- `context=` builds the neighbourhood from another population - all
  adults around people aged 30-40. Without it, the people themselves.
- As in section 10, a type under `min_group` people (30) leaves that
  k's θ EMPTY, never zero.
- **Weights** (`weight=`) are numbers of people per row, and also
  weight the neighbourhood when no `context=` is given. The shuffles
  move people, not rows, so they need whole numbers; with fractional
  weights the chance columns are left empty and the run says so.
- **Settings are refused, never rounded**: k = 10.9, groups = 2.9 or a
  negative minimum stop the run with a sentence.
- **Memory** does not grow with `shuffles` (1.62.1): a few arrays of
  one number per person. On a national register, try a subsample
  first to see the time per k; the run prints it when a k takes over
  five seconds.

**What it is, and is not.** The ex-ante reading, groups compared by
their means. It describes how inequality lines up with neighbourhood
type, not what the neighbourhood causes. On gridded census or WorldPop
counts it describes places; it becomes inequality of opportunity only
with individuals' own outcomes and backgrounds - registers.
`examples/cookbook_13_theta_profile.py` builds the synthetic town and
runs all three of its worlds.
