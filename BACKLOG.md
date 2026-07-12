# EquiPop Pangea — Backlog of small items to batch in later

Workflow: suggestions are appended here without altering code.
When we decide to batch, items are implemented, validated, moved to
the manual's version history, and struck from this list.

| # | Added | Item | Notes |
|---|-------|------|-------|
| ~~1~~ | DONE v0.7 | Seeded tie-break orientation: a user-settable seed determining the within-ring visiting order in `tie_mode="sequential"`, with the seed written to the metadata log (`settings.seed`) | Ring mode unaffected (order-free by design). Makes sequential mode fully reproducible. |
| ~~2~~ | DONE v0.7 | Metadata log file — full design agreed, see below | Implement as one batch; pairs with #1. |
| ~~3~~ | DONE v0.7 (convert path; 6-neighbour hex friction remains) | Hexagonal grids: convert or simply import point/raster data as hexagons (X/Y/Z axial or cube coordinates) | From the original spec. Design thoughts below. |
| 4 | open | Heights / third dimension (D-dimensions) for grids AND hexagons | No suitable test data yet — design can precede data. Thoughts below. |

## Item 2 — Metadata log file, agreed design

**Core idea:** one immutable sidecar per run, machine-readable, doubling
as a re-run recipe.

- **Format:** JSON sidecar named after the output
  (`output.csv` + `output.meta.json`), plus an optional human-readable
  `.meta.txt` rendering (spirit of the original EquiPop metadata.txt).
- **Re-runnable provenance:** the `settings` section mirrors the function
  parameters exactly, so `equipop.rerun("output.meta.json")` reproduces
  the run — absorbs the "log-file as script" idea from the original
  specification without generating Python code.
- **Six sections:**
  1. `run` — run id, timestamp, duration, library version
  2. `environment` — python/pandas/scipy/pyproj versions, OS
  3. `inputs` — per file: path, **md5 hash**, rows, dropped rows,
     CRS in → CRS used
  4. `settings` — engine, unit_size, k_values, tie_mode, **seed** (#1),
     decay spec, friction spec (default, combine rule, coverage %)
  5. `data` — n cells, global N, per-variable min/max/sum, extent
  6. `events` — structured capture of everything currently printed:
     warnings with counts and details (dropped rows, duplicate summing,
     coverage, suppressed repeats — spec §12 list)
- **Progressive writing:** log opened at run start, events appended live,
  summary finalised at end — a crashed run still leaves a record
  (pairs with future tile-and-flush).
- **Realm relationship:** per-run metadata is immutable history; the
  realm is mutable memory holding run-ids + meta paths + last-used
  settings for defaults. The realm remembers, the metadata testifies.
- **Include the output column list** with a one-line definition per
  column, so a shared CSV+meta pair is self-documenting (decided: yes).

## Item 3 — Hexagons, design thoughts (recorded, not decided)

- **Conversion vs import:** two entry paths. (a) CONVERT: points/rasters
  are binned into a hexagon tessellation we generate (user sets the
  hexagon "diameter" analogous to unit_size; pointy-top or flat-top is
  a setting). (b) IMPORT: data already carries hexagon IDs/coordinates
  (e.g. H3 indices or axial q/r columns) and is taken as-is.
- **Coordinates:** internally use CUBE coordinates (x+y+z=0) — the
  X/Y/Z from the original spec. Neighbourhood = 6 neighbours instead
  of 8; hex distance = (|dx|+|dy|+|dz|)/2 (rounds metric); Cartesian
  distance for Dist_k output from hexagon centre points.
- **Engine impact:** the radial sort core needs only a different
  centre-point distance formula (small change). The friction/BFS
  engine needs the 6-neighbour graph instead of 8 (parameterise
  neighbourhood construction — one function swap). The ring/tie logic,
  k-thresholds, decay, statistics: all unchanged.
- **Snapping:** point -> hexagon assignment via standard axial rounding
  (cube-round algorithm). Keep original coordinates as always.
- **Candidate shortcut:** the `h3` library (Uber) handles tessellation,
  indexing and neighbours on the globe — but introduces fixed
  resolution levels rather than free diameters. Decide: own metric
  hexagons (free size, consistent with our metric grids) vs H3
  (interoperability). Leaning: own metric hexagons as default,
  H3 import as an accepted in-data format.

## Item 4 — Heights / D-dimensions, design thoughts (recorded, not decided)

- **From the original spec:** any number of added dimensions (D1, D2,
  ...) for height, time, etc. Height is the first concrete case.
- **Two fundamentally different roles for height — must be kept apart:**
  (a) height as a FRICTION SOURCE: slope between neighbouring cells
  converted to friction values (steeper = more rounds). Fits the
  existing friction engine with zero engine change — just a
  preprocessing helper (DEM raster -> slope -> friction file). Probably
  the highest-value/lowest-cost use of height data.
  (b) height as a TRUE THIRD SPATIAL DIMENSION: cells become voxels
  (X/Y/H), neighbourhood grows to 26 neighbours (or 8 + up/down),
  distance formula 3D. Relevant for multi-storey urban data (population
  per floor). Bigger change: grid domain, graph construction, ring
  table all gain a dimension — but the engines' logic is
  dimension-agnostic in principle.
- **Time as a D-dimension** is different again: usually SEPARATE runs
  per time-ID (already the D3 example in the spec), not adjacency
  across time. Do not model time as a spatial axis.
- **Data formats when it becomes real:** DEM GeoTIFF for (a) — the
  raster module already reads it; point tables with a height/floor
  column for (b).
- **No suitable test data yet** — when implementing, start with (a)
  slope-to-friction (synthetic DEM is easy to fabricate and validate
  by hand), defer (b) voxels until a real use case exists.

| ~~5~~ | DONE v0.9 (repo built; publish + PyPI-name check remain manual steps) | GitHub sharing preparation | Strategy: repo layout (src/equipop, tests/, examples/, docs/); pyproject.toml with optional extras [geo]=geopandas,rasterio [fast]=scipy [xl]=openpyxl,pyarrow; turn the demo validations into pytest suite (Berlin regression, Sweden brute-force, wall test, decay properties, Malta totals); LICENSE decision (MIT vs EUPL - user choice); CITATION.cff pointing at the EquiPop papers; README = trimmed manual quick starts; GitHub Actions CI running pytest on push; versioning via git tags matching manual history; CONTRIBUTING with the design-decision log as ground rules; publish to PyPI when named (see naming note in spec). |
| ~~6~~ | DONE v0.8 (evenness+exposure; delta/concentration family awaits the area-term decision) | Segregation index module (per US Census formulary + Östh/Clark/Malmberg 2015) | Aggregate indices computed FROM k-NN output across all origins i, per k: Spatial Isolation SI_k = sum(x_i * (x_ik/k)) / sum(x_i) (the 2015 paper's measure - weight each origin's k-share by its own minority count); interaction (x->y) analogue; Dissimilarity D_k = 0.5*sum|x_i/X - y_i/Y| over bespoke neighbourhoods; entropy/Theil H_k; Gini_k (segregation form, from the census formulary, distinct from the inequality Gini already implemented); Atkinson(b); correlation ratio (I-P)/(1-P); delta & concentration family needs area a_i = k-neighbourhood footprint (Dist_k-derived) - flag as derived-area caveat. Design: segregation.py taking a run_knn(_stats) output DataFrame + k list, returning one row per k per index - i.e. POST-ANALYSIS on existing output, no engine change. Validate against Table A4 style numbers (SI for k=100/6400) when a suitable dataset exists. |
| ~~7~~ | Stata part DONE v1.1 (bridge pytest-tested; ado sfi-glue awaits first in-Stata run); QGIS part remains | Stata & QGIS availability | QGIS: ships Python - short term a processing-toolbox script (paste-in) calling equipop if installed in the QGIS python (pip install via OSGeo shell); mid term a minimal plugin wrapping InData->run->load-result-as-layer. ArcGIS Pro: arcpy python env can pip install equipop (conda-based env cloning), no plugin needed for script use. Stata: no embedded CPython officially until recent versions - Stata 16+ HAS python integration: `python:` blocks share data via sfi (Scala Function Interface) Data class; strategy = thin equipop_stata.ado + python glue: read frame via sfi.Data.get(), run equipop, write back new variables via sfi.Data.addVarDouble()+store - enabling the requested regress->knn->regress round trip entirely inside Stata. Deliverable order: (1) plain .do example with python block, (2) ado wrapper, (3) QGIS processing script, (4) QGIS plugin. |
| ~~8~~ | DONE v0.8 | Map visualisation of output + export | matplotlib-based map_output(df, column, classing=quantiles/equal/sd/jenks, n_classes, basemap=None/simple-extent, north arrow + scale bar + legend with class bounds); jenks via jenkspy (small pip dep) with fallback to quantiles; hexagons drawn as polygons, grid as squares; export .png/.svg/.pdf via savefig plus data export of the classed column (save_output already covers gpkg for GIS styling). Colour: viridis default, diverging option for ratio-around-mean. Keep it deliberately simple - QGIS is the real GIS; this is quick-look QC. |
| ~~9~~ | DONE v0.8 (all three alternatives) | Area-based output (policy-friendly aggregation of k-NN results) | Three alternatives, same principle - bring overlapping bespoke-neighbourhood output back to fixed geographies that policy makers grasp: **Alt 1** user-provided belonging ID (location/municipality code already on the data; label_col/CellId machinery is the natural carrier) -> aggregate any output column per ID (mean/median/pop-weighted mean, N). **Alt 2** uploaded polygons (shp/gpkg municipalities) -> point-in-polygon assignment of origin cells (geopandas sjoin), then as Alt 1. **Alt 3** coarse grid/hex scales - e.g. 100 m results aggregated to 1000/5000 m super-cells; aggregation origin anchored at min X/Y/(Z). Design: one post-analysis function `aggregate_output(df, by=..., how=...)`; document explicitly that overlap-then-aggregate is intentional (bespoke values summarised per area, not area-recomputed) so reviewers don't mistake it for a contradiction. Pairs naturally with #6 (per-area index reporting) and #8 (choropleths per area). |
| ~~10~~ | DONE v0.9 (MANUAL_TOPICS.md) | Topic-based beginner manual | Restructure the manual by TOPIC rather than version/dataset: Installation; File formats & data management; Projections; Grids or hexagons; Selecting k-values; Determining decay; Determining friction; Statistics; Segregation measures; Area output; Metadata & reproducibility; Troubleshooting. Keep the current version-history + validation-record + design-decision log as appendices (they are the scientific audit trail). Write once the v0.8 feature set lands so topics stabilise; each topic = concept in plain language -> minimal example -> settings table -> pitfalls. |

## Data notes (remember, nothing to act on)
- Stockholm semi-synthetic (.sav) + Kommun shapefile: coordinates are
  APPROXIMATE (discretion jitter) and the municipality polygons are
  CRUDE generalisations - neither is a perfect delimitator. The 9,033
  cells falling outside all polygons in the v0.8 Alt-2 join are the
  expected product of that pairing, not an error. Interpretation and
  any future join-tolerance option (e.g. nearest-polygon snap within
  X m) should keep this in mind.

## Item 4 expanded — three height mechanisms (opinions as requested)
**4a. DEM slope-asymmetric friction ("inverted watershed").** Downhill/
flat = 0 effort, uphill costs. VERDICT: highest research value of the
three (active mobility, X-minute-city relevance) and NOT too heavy:
requires directional EDGE weights, and the friction engine's Dijkstra
graph is already directed - cost(i->j) = 1 + g(elev_j - elev_i), same
graph size, same runtime class as v0.4 Stockholm (~1 min). Effort
function: offer BOTH (i) a transparent linear rule - one extra round
per s0 % uphill slope, s0 user-set, default suggestion 5% - and (ii)
Tobler's hiking function (speed = 6*exp(-3.5|slope+0.05|) km/h,
asymmetric, canonical, citable) converted to rounds relative to flat.
Validate on a synthetic cone hill (neighbourhoods must skew downhill).
Preprocessing helper: DEM GeoTIFF -> cell elevations -> per-edge costs
(raster module already reads DEMs).
**4b. Building levels / heights at coordinates (U-curve travel:**
down to level 0, across, up at j). d'ij = dij + h_i + h_j, with h given
either in metres (used directly) or in LEVELS x user-set
metres-per-level. Individuals in one cell at different levels need
sub-cell records (same pattern as individual decay). VERDICT:
conceptually sound - vertical travel is real distance - modest
implementation cost in the sort engine (per-destination offset changes
ordering; per-origin offset shifts reported distance and decay weight).
Data availability is the real constraint, not code.
**4c. Height as availability adjustment (may be NEGATIVE - regression
residuals, subway proximity, line of sight).** Same formula as 4b.
VERDICT: implement 4b+4c as ONE mechanism ("node distance offsets",
metres, negatives allowed, optional floor-at-zero), documented twice.
Honest caveats to state loudly: (i) with decay, a negative offset gives
weights > 1 - amplification - which must be an intentional modelling
choice, not a surprise; (ii) outputs must be labelled ADJUSTED distance
to protect the Dist_k semantics. Academic-niche value acknowledged, but
the marginal cost on top of 4b is near zero, so include it.
Priority: 4a first (needs the DEM the user is sourcing), 4b/4c as one
small batch after.
