# EquiPop Pangea — User & Developer Manual

**Version 0.3.1 — living document, updated with every release**

---

## Version history

| Version | Contents |
|---|---|
| 0.1.0 | Projection, grid snapping, radial k-NN engine, legacy-compatible output, validation against original EquiPop (Berlin, 250 cells) |
| 0.2.0 | Distance decay (negative exponential, half-life parameterisation), short output-naming scheme, extensible decay-model registry |
| 0.3.0 | Individual-level in-data with duplicate coordinates, per-variable statistics (ratio, mean, median, SD, SE, entropy, Gini) in three exactness tiers, missing-data handling, distance-sort engine |
| 0.3.1 | Optional cell ID (`label_col`) carried through to output; this manual |
| 1.1.0 | Stata integration (Round C part 1): `equipop.stata_bridge.knn_to_rows` - row-aligned disaggregated results for individual-level data, missing-coordinate-safe, engine-identical (pytest-covered); `stata/equipop_knn.ado` (Stata 17+, thin sfi glue) + example.do + README_STATA + test .dta; tolerance-based tie detection (1e-6 m) unified across engines after a cross-engine ulp-level tie discrepancy was caught by the bridge test |
| 1.0.0 | First public release: repository https://github.com/GeoJohnSwe/EquiPop, PyPI name `equipop` claimed; version stamped across pyproject/package/CITATION; wheel + sdist built and install-verified |
| 0.9.0 | Round B: GitHub-ready repository under the name **EquiPop** (pyproject with optional extras, MIT license + citation request, CITATION.cff with ORCID and the five reference works, README with C#/R/Python lineage, CI workflow, examples); pytest suite - 11 tests, synthetic fixtures for engines/decay/hex/stats/segregation plus Berlin regression and the anonymized individual dataset; PopMuniTest anonymized to `synthetic_individuals.csv` via isometric transform (reflection + translation; pairwise distances and all k-NN results proven multiset-identical), variables renamed ValFloat/ValCount; topic-based beginner manual (MANUAL_TOPICS.md); CORRECTION: the Berlin tie deviation is 6 cells (2 per k-level), not 2 as earlier noted |
| 1.1.0 | Stata integration (Round C part 1): `equipop.stata_bridge.knn_to_rows` - row-aligned disaggregated results for individual-level data, missing-coordinate-safe, engine-identical (pytest-covered); `stata/equipop_knn.ado` (Stata 17+, thin sfi glue) + example.do + README_STATA + test .dta; tolerance-based tie detection (1e-6 m) unified across engines after a cross-engine ulp-level tie discrepancy was caught by the bridge test |
| 1.0.0 | First public release: repository https://github.com/GeoJohnSwe/EquiPop, PyPI name `equipop` claimed; version stamped across pyproject/package/CITATION; wheel + sdist built and install-verified |
| 0.9.0 | Round B: GitHub-ready repository (pyproject.toml, MIT LICENSE, CITATION.cff with the five references + ORCID, README with family history, CI workflow); pytest suite - 13 tests, all synthetic or shareable fixtures, all green (hand-computed k-NN, ring-atomic ties, fast-vs-stats identity, decay properties, friction wall, Gini dual-formula, global-equals-wholefile, hex cube invariants, Berlin projection, segregation bounds, area alternatives); anonymised individual-level fixture (isometry-proven: mirror + translation preserves every result); topic-based user manual (MANUAL_TOPICS.md); name decision: EquiPop, first Python implementation, 1.0.0 at public release |
| 0.8.0 | Round A: segregation index module (`seg_profile`: D, Gini, H/Theil, Atkinson(b), Isolation, Interaction, Correlation V, and the 2015 SI, one row per scale + aspatial local baseline); area-based output (`aggregate_output`, three alternatives: belonging ID / uploaded polygons via CRS-aware sjoin / coarse supergrid); map visualisation (`map_output`: quantile-equal-sd-jenks classing, square/hex/point cells, legend, scale bar, north arrow, png-svg-pdf export); vectorised fast engine (`run_knn_counts`, KD-tree + chunked cumsum, identical results to run_knn_stats by regression test, 73k Stockholm origins in 54 s vs >30 min); SPSS .sav reading; Stockholm county validation reproducing published Table A4 SI values |
| 0.7.0 | Hexagonal grids (convert path: `build_hex_cells`, axial/cube X-Y-Z indexing, same engines); metadata log (`RunLog`: six-section JSON sidecar + txt rendering, md5 input hashes, progressive writing, column definitions included); seeded sequential tie order (`run_knn(..., seed=)`); io: multi-layer `layer=` + `list_layers`, OSM `.pbf` (GDAL driver), zipped GIS archives; Malta OSM POI validation (grid vs hexagon) |
| 0.6.0 | In/out formats (`read_table` with separator sniffing + BOM handling, shp/gpkg via optional geopandas with line/polygon representative-point note, `save_output` to csv/tsv/xlsx/parquet/json/gpkg/shp); projection framework (`suggest_projection` with single-zone / two-zone A/B / continental advice, `assign_zones` overlap buffers); all five original decay models half-life parameterised (negexp, expnormal, expsqrt, lognormal, power); URL retrieval with caching (`fetch`, zip auto-extract) |
| 0.5.0 | Raster in-data module (`equipop.raster`, WorldPop-style GeoTIFF cohort summing with grid/CRS checks and mass-conservation reporting); fractional (estimated) population counts accepted by the stats engine; Malta 65+ validation |
| 0.4.0 | Friction growth model (FARB core): Dijkstra-exact BFS-with-delays, friction file loader with malformed-row fencing and layer summing, coverage warning, `Rounds_k` output, Stockholm validation reproducing the published radial-vs-friction pattern |

Planned next: WorldPop raster in-data, place-based statistic variants, metadata log file, realm.

---

## 1. What the library does

For every populated location *i* in a gridded dataset, the library finds the *k* nearest individuals (by cumulative population count, expanding outward by distance) and reports the composition of that individualised neighbourhood: counts, treatment ratios, statistical summaries, distances, and — optionally — distance-decay-weighted versions. It is a Python reimplementation and extension of the EquiPop software (Östh, Uppsala University), whose gridded design makes k-NN feasible for millions of observations: on a uniform grid, the relative distances from any origin to its surroundings are identical everywhere, so one pre-computed distance ordering serves all origins.

## 2. Installation

Requires Python ≥ 3.10 with `pandas`, `numpy`, `pyproj`, `openpyxl` (for Excel files). With Anaconda:

```
conda create -n equipop python=3.12 pandas openpyxl -y
conda activate equipop
pip install pyproj
```

Unzip the package folder; work in that folder (Jupyter: create the notebook inside it, or `os.chdir(...)`).

**Practical notes learned the hard way:**
- Inside Jupyter, install with `%pip install pyproj` (never `!pip` — on machines with several Pythons, `!pip` may install into the wrong one). Restart the kernel after installing.
- Nordic CSV files usually need `pd.read_csv(path, sep=";")`.
- Dropbox folders work, but large runs writing big files will keep Dropbox busy syncing.

## 3. Quick start A — aggregated in-data (one row per cell)

```python
import pandas as pd
from equipop import project_to_metric, snap_to_grid, run_knn, Decay
from equipop.transform import aggregate_to_cells

df = pd.read_csv("my_points.csv")                          # lat/long + counts
df = project_to_metric(df, lat_col="lat", lon_col="lon")   # auto-suggests UTM
df = snap_to_grid(df, unit_size=100)
cells = aggregate_to_cells(df, value_cols=["pop", "treated"], id_col="myid")

result = run_knn(cells, k_values=[50, 100, 200, 400, 800],
                 count_all_col="pop", count_group_col="treated",
                 unit_size=100, max_radius_units=400,
                 decay=Decay(half_life_m=8000))            # decay optional
result.to_csv("out.csv", index=False)
```

## 4. Quick start B — individual in-data (one row per person)

```python
from equipop import build_cells, run_knn_stats

df = pd.read_csv("PopMuniTest.csv", sep=";")
cd = build_cells(df, e_col="RT90_East_4124", n_col="RT90_North_4124",
                 binary_vars=["HighEdu", "LowEdu"],
                 value_vars=["ForvInk", "age"],
                 unit_size=100,
                 label_col=None)          # or e.g. a place/year column

stats = {                                  # switch functions on per variable
    "HighEdu": ["ratio", "sd", "se", "entropy", "gini"],
    "ForvInk": ["mean", "median", "sd", "se", "gini"],
    "age":     ["mean", "median"],
}
res = run_knn_stats(cd, k_values=[50, 100, 200, 400, 800], stats=stats)
```

Duplicate coordinates are expected and welcome — that is what makes individual-level (tier 3) statistics exact.

## 5. Core concepts

**Grid midpoints.** A grid of `unit_size` 100 m has midpoints at ...50, ...150, ...250. Snapping is `floor(x/100)*100 + 50` and is idempotent — register data already delivered on 100 m midpoints passes through unchanged. Original coordinates are always preserved for post-analysis rejoining.

**k overshoot.** Because a whole cell is added at once, the reported count at threshold k is usually slightly above k (the count after adding the cell that crossed the threshold). `N_k` reports the factual count.

**Ties (equidistant cells) — a documented design decision.** Several cells can lie at exactly the same distance from an origin. Default (`tie_mode="ring"`): the whole equidistant ring is added before thresholds are checked — deterministic and direction-symmetric. Original EquiPop instead checked after each single cell (`tie_mode="sequential"`), making the reported count depend on an arbitrary within-ring order. This is the only known, deliberate deviation from the original software; in the Berlin validation it affected 6 of 250 cells (2 per k-level at k = 100/200/800 - a correction of the earlier "2 cells" note, which counted only the k = 100 pair). Distances are identical everywhere, the tie signature.

**Unreached k.** If k exceeds the reachable population (or the `max_radius_units` search limit is hit), partial results are reported rather than nothing — mirroring original EquiPop behaviour.

**Two engines, one mathematics.** `run_knn` uses ring expansion; `run_knn_stats` uses a vectorised distance sort. For the radial (no-friction) model they are mathematically identical; the sort core is faster on sparse data. Friction (coming) requires the true BFS ring engine, since visiting order then depends on the path.

## 6. Function reference

### `project_to_metric(df, lat_col, lon_col, target_epsg=None, source_epsg=4326)`
Adds `easting_m`, `northing_m` (+ CRS strings). If `target_epsg` is omitted, a UTM zone is suggested from the data centroid. For official European work prefer explicit ETRS89 codes (25832/25833). *Note:* Swedish RT90 coordinates in metres are EPSG:3021 (RT90 2.5 gon V); EPSG:4124 is the degree-based variant — data already in metres needs no projection at all.

### `snap_to_grid(df, unit_size, easting_col="easting_m", northing_col="northing_m")`
Adds integer `E_grid`, `N_grid` midpoint columns.

### `aggregate_to_cells(df, value_cols, id_col=None)`
Sums `value_cols` per cell; concatenates ids.

### `run_knn(cells, k_values, count_all_col, count_group_col, unit_size, max_radius_units, id_col, tie_mode="ring", decay=None, naming="short")`
The ring-expansion engine for aggregated data. Output columns below.

### `Decay(model="negexp", beta=None, half_life_m=None)`
`half_life_m` is the distance at which weight = 0.5; internally `beta = ln(0.5)/half_life` (negative) and `weight(d) = exp(d·beta)`. k-thresholds are still defined by RAW counts; decayed values are recorded at the same moment (original EquiPop convention), so decayed ≤ raw always, and where k is satisfied at distance 0, decayed = raw. Add models in one line: `decay.MODELS["power"] = lambda d, b: (d+1)**b`.

### `build_cells(df, e_col, n_col, binary_vars, value_vars, unit_size, snap=True, label_col=None)`
Individual rows → `CellData`. Declares which variables are binary (tier 1) vs continuous (tiers 2–3). `label_col` carries an ID (place, year, ...) into the output as `CellId`; cells containing several distinct labels get them joined with `|` plus a warning.

### `run_knn_stats(cd, k_values, stats, max_radius_units=None)`
The statistics engine. `stats` is a dict `{variable: [function, ...]}` — the Y/N switchboard, per function, applied to all k.

## 7. Statistics reference — the three tiers

| Tier | Applies to | Statistics | Exactness |
|---|---|---|---|
| 1 | binary variables | ratio, sd, se, entropy, gini | exact at individual level from the counts (n, t) alone |
| 2 | continuous | mean, sd, se | exact (computable from moments) |
| 3 | continuous | median, gini | exact **only** with individual-level in-data |

Conventions (all changeable in one place, `equipop/stats.py`):
- Continuous SD uses the sample formula (ddof = 1); SE = SD/√n_valid.
- Binary SD = √(p(1−p)) (Bernoulli); SE = √(p(1−p)/n).
- Entropy is Shannon entropy in **nats** (natural log); divide by ln 2 for bits. Currently binary only — continuous entropy needs a binning decision (open design question).
- **Binary Gini reduces mathematically to 1 − p.** It mirrors the ratio and is reported for completeness; interpret accordingly (p→1 gives G→0, perfect equality of the attribute).
- Gini is NaN when the mean is ≤ 0 or fewer than 2 valid values.
- Place-based variants (cells as units) are planned as explicitly labelled alternatives (`_p` suffix) — they answer a different question and are grid-size dependent (MAUP).

Add your own statistic in one line:
```python
from equipop import stats
stats.VALUE_STATS["p90"] = lambda x: float(np.percentile(x, 90))
```

## 8. Missing data (spec §12 behaviour)

| Situation | Behaviour |
|---|---|
| Missing coordinates | rows dropped, warning with count printed |
| Missing value in a continuous variable | individual still counts towards k; excluded from that variable's statistics; valid count reported as `Nv_<var>_<k>` |
| k > global N or search limit hit | partial results reported |
| Blank fields in semicolon CSVs | coerced to NaN and handled as above |

## 9. Output naming

Fixed columns: `Id`/`CellId`, `EastWest`, `NorthSouth`, `CountAllLocal`/`N_local`, `SumCountAll`/`SumN`, `Ratio`, `MaxDistance`.

Per-k columns, short scheme (default) vs legacy (`naming="legacy"`, `run_knn` only):

| short | legacy | meaning |
|---|---|---|
| `N_50` | `IntervalSumCountAll_50` | factual count at k=50 |
| `T_50` | `IntervalSumCountGroup_50` | treatment count |
| `R_50` | `IntervalRatio_50` | ratio T/N |
| `Dist_50` | `IntervalDistance_50` | metres to where k was reached (0.0 = satisfied within origin cell) |
| `ND_50` `TD_50` `RD_50` | `...Decay_50` | decay-weighted N, T, ratio |

Statistics columns: `<Prefix>_<var>_<k>` with prefixes `R, Mean, Med, SD, SE, Ent, Gini`, plus `Nv_<var>_<k>`. All prefixes editable in `stats.PREFIX`.

## 10. Validation record

**Berlin (v0.1, aggregated, 250 cells, EPSG:25832, 100 m, k = 50–800):** projection max error 0.0008 m vs pre-computed columns; grid snapping 250/250 identical; distances identical at all k; counts/ratios identical for 248/250 cells — the 2 deviations are the tie-mode decision (Section 5), verified as such.

**Decay (v0.2, Berlin, half-life 8000 m):** weights verified 1.0 / 0.5 / 0.25 at 0 / 8000 / 16000 m; invariants asserted in code: decayed ≤ raw everywhere; k-at-distance-0 ⇒ decayed = raw.

**Friction, synthetic (v0.4):** hand-computed wall scenario - three clusters on a line, k reachable only beyond a friction-20 barrier: rounds without wall = 10, with wall = 30 (10 + 20), near-side results unaffected. All assertions pass.

**Friction, Stockholm (v0.4, 8 312 cells, 475 887 individuals, SWEREF99TM, 100 m, k = 12-12 800, water+road barrier friction 50/100/150):** full run 69 s. Radial-vs-friction comparison reproduces the published pattern (Östh & Türk 2020, Figs 22.6-22.7): correlation peaks mid-k (0.986 at k = 1600-3200) and falls toward both extremes; RMSE declines from k = 12 to k = 3200 and then rises again; friction means slightly below radial means across most k. Data-quality handling exercised on real quirks: 6 digit-shift coordinate rows fenced out, 31 water+road overlaps summed to 150, 69.3% coverage warning triggered.

**Sweden (v0.3, individual level, 10 892 rows → 1 958 cells, RT90 metres, 100 m):** three independent validations, all exact — (A) at k = 15 000 > N every statistic equals the whole-file value (ratio 0.191491, income mean 1822.6699, median 1170, SD 1988.8489, Gini 0.584542 — reproducible in SPSS/Excel); (B) 6 random origins recomputed with a separate brute-force implementation at k = 200: N, median, Gini, ratio all identical; (C) Gini rank formula ≡ pairwise |xᵢ−xⱼ| definition. Runtime 12.7 s for 1 958 origins × 8 k-levels.

## 11. Design-decision log

1. **Tie handling** — ring-atomic default; sequential available for legacy compatibility (Section 5).
2. **Decay convention** — k defined by raw counts; decayed recorded at the same threshold moment (matches original EquiPop; decayed ≤ raw by construction).
3. **Short naming default** — legacy names remain available for file-compatibility with the original software.
4. **Binary Gini = 1 − p** — reported, documented, interpret with care.
5. **Two engines** — sort core for radial statistics runs; ring/BFS core retained as the friction foundation.
6. **Missing values count towards k** — presence in the population is independent of variable completeness; `Nv_` makes the basis explicit.
7. **Individual data via duplicate coordinates** — in-data format unchanged (one row per record); tier 3 activates simply by loading individual rows through `build_cells`.

## 12. Friction (v0.4)

```python
from equipop import load_friction_table, run_knn_friction

fr  = load_friction_table("ComboLowXY_WatRoad.txt",
                          x_col="LowX", y_col="LowY", friction_col="Friction")
res = run_knn_friction(pop_df, k_values=[12, 25, ..., 12800], fr=fr,
                       unit_size=100, default_friction=0,
                       count_all_col="count_all", count_group_col="count_group",
                       id_col="rutid100_sw_max")
```

**The model** (Östh & Türk 2020): growth moves to the eight surrounding
cells one round per move; a cell with friction f sits out f extra rounds
before inclusion: `round(j) = round(i) + 1 + friction(j)`. Implemented as
exact Dijkstra on the grid graph (scipy, C speed) - mathematically identical
to round-by-round simulation, dramatically faster. Cells are counted in
included-round order; equal rounds form an atomic ring (same tie convention
as the radial engine). Output adds `Rounds_k` - the friction-adjusted round
at which k was reached (the friction analogue of distance); `Dist_k` stays
the straight-line metres, as in original EquiPop.

**default_friction** decides what unlisted cells cost. `0` (default) means
the friction file lists BARRIERS (water, motorways) on otherwise free land.
The opposite convention (file lists fast roads; everything else slow) is
used in some studies - then set `default_friction` to the maximum coded value.

**Friction file cleaning:** malformed coordinates are fenced out with a
warning (e.g. digit-shift errors); duplicated cells (a cell present in
several layers, e.g. water AND road) are combined - `sum` by default per
the additive-layers rule; coverage below 80% of the analysis extent
triggers a warning; cells outside receive the default friction.

**Domain note:** growth is confined to the bounding box of population +
friction cells. A padding option is a candidate future addition.

## 13. Raster in-data (v0.5)

```python
from equipop.raster import rasters_to_points
df = rasters_to_points({
    "pop": "malta/mlt_t_*_2020_*.tif",                       # sum all cohorts
    "old": "malta/mlt_t_{65,70,75,80,85,90}_2020_*.tif"})    # sum 65+ cohorts
```
Each key becomes a column = the SUM of all rasters matching its glob pattern
({a,b} alternatives supported). Nodata masked; grids/CRS must match (checked);
per-variable totals printed so mass conservation can be verified after
regridding. Reprojecting lat/long pixels (~75 x 93 m at Maltese latitudes)
onto a 100 m metric grid makes some pixels share a cell - sums conserve mass.
Fractional (model-estimated) populations are accepted throughout. Requires
`pip install rasterio`.

**Malta validation (v0.5):** 60 WorldPop cohort rasters; cross-checks
sum(t-cohorts) = T_F + T_M = 514,526.000 and t65+ = m+f 65+ = 95,103.000
(exact); population 514,526 with 18.5% aged 65+ matches official Malta 2020
statistics; mass conserved through reprojection (42,853 pixels -> 30,236
cells); k = 12-12,800 in 71 s; shares converge on the global 18.5% as k grows.

## 14. In/out, projections, decay models, fetching (v0.6)

**Reading anything:** `read_table(path)` - separator sniffed for text
(tab/;/,/|), BOM stripped, Excel sheets, parquet, json/geojson (point
features -> lon/lat), and via optional geopandas: shp/gpkg/dbf, where
line/polygon layers become representative points WITH a printed note
(spec: point representation must be a conscious choice). **Writing:**
`save_output(df, "out.gpkg", epsg=3006)` - extension decides; gpkg/shp
build point geometry from EastWest/NorthSouth.

**Projection framework:** `print(suggest_projection(df))` analyses WGS84
extents and recommends: a single UTM zone (with a 5% fringe tolerance);
two zones -> primary + secondary and the A/B tiled workflow
(`assign_zones(df, buffer_m=20000)` adds zone_A plus per-zone buffer
booleans); continental Europe -> EPSG:3035 with an explicit equal-area-
not-equal-distance warning; polar and cross-hemisphere warnings. Nothing
is applied silently - the advice object carries EPSG + rationale.

**Five decay models** (Östh, Lyhagen & Reggiani 2016), all accepting
`half_life_m` so that weight = 0.5 exactly at the half-life:
negexp exp(bd), expnormal exp(bd^2), expsqrt exp(b sqrt d),
lognormal exp(b ln(d+1)^2), power (d+1)^b. They differ in tail weight -
at twice the 8 km half-life: 0.25 / 0.06 / 0.37 / 0.45 / 0.47
respectively. Verified by property test (w(0)=1, w(h)=0.5, monotone).

**Fetching:** `fetch(url, workdir, unzip=True)` downloads into the
required work folder (spec: external source -> ask local folder),
caches by file name (re-runs reuse; delete to force), auto-extracts
zips. Errors are reported verbatim (restricted networks show their
denial reason).

## 15. Hexagons, metadata log, seed, OSM (v0.7)

**Hexagons:** `build_hex_cells(df, e_col, n_col, hex_size=100, binary_vars=[...])`
bins points into pointy-top hexagons (`hex_size` = width across flats =
lateral centre spacing, the analogue of unit_size). Axial/cube indexing
(q+r+s=0 - the spec's X/Y/Z), exact cube rounding, centres as E/N, CellId
"q|r". The radial statistics engine runs UNCHANGED on the result; only
hexagonal FRICTION (6-neighbour graph) remains future work.

**Metadata log:** `RunLog(settings={...})` -> `.add_input(path,...)` (md5
hashed) -> `.event(level,msg)` -> `.finalize(df, "out.csv")` writes
out.meta.json (six sections + full column definitions, per decision) and
a human-readable out.meta.txt. Progressive writing: a crashed run still
leaves its record. `load_meta()` reads it back (rerun() planned).

**Seed:** `run_knn(..., tie_mode="sequential", seed=42)` makes the
within-ring visiting order reproducible; put the seed in RunLog settings.

**io:** `read_table(path, layer=...)` for multi-layer sources;
`list_layers(path)`; OSM `.pbf` read natively via GDAL (defaults to the
points layer with a note); `read_table("...gpkg.zip")` auto-extracts.

**Malta OSM POI validation (v0.7):** 13 487 POIs (8 730 points + 4 757
area features as representative points), treatment fclass=='hotel'
(238; guesthouse/hostel/motel excluded by design), EPSG:32633, k=12-100.
Grid (100 m) vs hexagon (100 m) comparison: means nearly identical
(0.0143-0.0146 at all k); correlation grid-vs-hex rises 0.864 -> 0.973
from k=12 to k=100 - tessellation geometry matters most at micro scale
and washes out with k, as MAUP theory predicts.

## 16. Round A: segregation, areas, maps, fast engine (v0.8)

**Segregation profile:** `seg_profile(knn_out, k_values, ...)` returns one
row per scale (plus an aspatial 'local' baseline): Dissimilarity D,
segregation Gini (O(n log n)), Entropy/Theil H, Atkinson(b), Isolation
xPx, Interaction xPy, Correlation V, and SI - the population-weighted
k-share isolation of Östh, Clark & Malmberg (2015). Units at scale k are
the bespoke neighbourhoods (t_i = N_k, p_i = R_k); P is the global share.
The concentration/delta family is deliberately absent until the bespoke
area term is decided (backlog note).

**Area output:** `aggregate_output(df, by=..., how='wmean')` with
by = column name (Alt 1), polygon file + id_field (+ points_epsg for
CRS-aware join) (Alt 2), or a supergrid size in metres (Alt 3). Stated
design: individualised context summarised per area - not areal
recomputation (precedent: 2015 fig. 1).

**Maps:** `map_output(df, column, cell='square'|'hex'|'point',
classing='jenks'|..., save='map.png')` - classed legend, scale bar,
north arrow; jenkspy optional with quantile fallback.

**Fast engine:** `run_knn_counts(cd, k_values, m_neighbors=...)` -
KD-tree chunked cumulative counting, ring-atomic ties, sparse origins
exact-solved automatically. Regression-identical to run_knn_stats;
use it for counts/ratios at scale, the stats engine for value
statistics.

**Stockholm county validation (v0.8, semi-synthetic, 72 951 cells,
2.3 M population, P = 0.1385):** k-NN in 54 s. The SI profile
reproduces the PUBLISHED Stockholm values of Table A4 (2015):
SI(k=100) = 0.2822 vs published 0.287; SI(k=6400) = 0.2501 vs
published 0.250. D falls with scale (0.488 local -> 0.347 at 6400),
as the scale literature predicts. Area alternatives cross-checked:
belonging-ID vs polygon-join agree within 0.018 on all 26
municipalities (9 033 jittered coastal cells fall outside polygons -
a property of the discretion-altered data, reported by the module).

## 17. Roadmap

Friction (BFS growth, raster + vector friction layers, combination rules) → WorldPop raster in-data challenge (Malta) → metadata log file → place-based statistic variants → realm / project memory → continuous entropy (binning decision) → histogram-sketch approximations for national-scale median/Gini → hexagonal grids → GIS export.
