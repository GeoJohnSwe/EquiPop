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
reduces to 1 - p; entropy is in nats. Add statistics with one line in
`stats.VALUE_STATS`.

## 10. Segregation measures
`seg_profile(knn_out, k_values, ...)` returns one row per scale plus an
aspatial 'local' baseline: D, segregation Gini, entropy H, Atkinson(b),
Isolation, Interaction, Correlation V, and SI (the 2015 paper's
population-weighted k-share isolation). Units at scale k are the
bespoke neighbourhoods. Concentration/delta indices await a bespoke
area-term decision.

## 11. Area-based output
`aggregate_output(df, by=..., how="wmean")` summarises overlapping
bespoke results per fixed geography - by belonging ID column, by
uploaded polygons (`id_field=`, `points_epsg=` for CRS-aware joins), or
by a coarser supergrid size in metres. This is individualised context
reported per area, not areal recomputation - state that in your methods
section.

## 12. Maps
`map_output(df, "R_VM_1600", cell="square"|"hex"|"point",
classing="jenks"|"quantiles"|"equal"|"sd", n_classes=6,
save="map.png")` - classed legend, scale bar, north arrow; export to
png/svg/pdf. For real cartography, `save_output(..., "out.gpkg")` and
style in QGIS.

## 13. Metadata and reproducibility
Wrap runs in `RunLog(settings={...})`: `add_input()` records md5 hashes
and CRS decisions, `event()` captures warnings, `finalize(df,
"out.csv")` writes `out.meta.json` (six sections + full column
definitions) and a readable `.meta.txt`. Written progressively - a
crashed run still leaves its record. Put your seed and every deliberate
choice in settings; the meta file is your methods section's receipt.

## 14. Troubleshooting
`ModuleNotFoundError` in Jupyter: `%pip install <pkg>`, restart kernel.
Nordic CSVs: separator is sniffed, but check the row count. Coordinates
that "look wrong": compare ranges against the claimed CRS. Slow runs:
switch to `run_knn_counts`; very large areas: tile with A/B zones.
Everything the engines print is also captured by RunLog.
