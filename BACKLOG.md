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


## v1.2.0 updates (this session)
- ~~#4a DEM slope-asymmetric directional friction~~ DONE in v1.2.0
  (tobler + linear via SLOPE_MODELS; Malta-validated; "valley tax"
  asymmetry finding recorded). Square grids only - hexagonal slope
  rides on the parked hex-friction 6-neighbour graph.
- #11 substrate progress: `origins=` subset option now exists on both
  graph engines (friction + slope). Still needed for #11: reach modes,
  match-table segmentation, chaining orchestrator. #12 still BEFORE #11.
- #4b + #4c (node distance offsets) remain parked, unchanged verdicts.
- NEW small idea (parked): windowed DEM reading in dem_to_cell_altitude
  for national-scale rasters (Malta-size reads whole array fine).
- NEW small idea (parked): slope-model parameter sweep helper
  (lambda_up sensitivity reporting) once #12's neighbourhood menu lands.


## Session additions (post-v1.2.0, recorded without coding)

- **#12 EXPANDED - neighbourhood definition menu, now with parity
  checklist.** Goal restated: everything available for k must exist
  for metric radius r (and where meaningful, friction tau). Checklist
  to tick at build time: fast engine (KD-tree ball query) | ring
  engine (stopping rule swap) | stats engine (all three exactness
  tiers) | decay (r-bounded and the unbounded decayed sum) | friction
  + slope (tau_values = effort isochrones) | segregation profile over
  r | area aggregation | maps | RunLog column definitions | Stata
  bridge (r() option) | hex. Decisions to record when building:
  naming scheme (proposal: N_r500 style), empty-radius convention
  (N=0 is a valid partial result, never nothing), tau semantics under
  real-valued slope effort. Note: ties VANISH under r (cells within r
  included wholly) - document as a simplification, not a change.
  STILL BEFORE #11. Recommended as next build.

- **#13 (NEW) Cookbook: 10-20 complete A-to-Z scenario scripts.**
  Runnable scripts in examples/cookbook/ against small bundled
  fixtures + a COOKBOOK.md index; CI smoke-runs them so documentation
  cannot rot. Candidate scenarios: (1) CSV -> decay analysis -> map;
  (2) SPSS register -> segregation profile -> area aggregation;
  (3) WorldPop rasters -> elderly context; (4) OSM pbf -> POI
  accessibility; (5) wrong-CRS shapefile rescue; (6) friction with
  water barriers; (7) DEM slopes -> valley-tax map; (8) grid vs hex
  MAUP experiment; (9) individual data with missings -> stats engine;
  (10) weighted/aggregated in-data; (11) the Stata round trip;
  (12) RunLog-driven reproduction; (13) national-scale tactics;
  (14+) radius variants of 1/3/7 - BLOCKED ON #12. Grows with the
  package; partial delivery acceptable.

- **#14 (NEW) Spatial autocorrelation module: Moran's I and
  Getis-Ord, global + local, multiscalar.** Weights matrices born
  from our own engines: binary kNN, distance band (needs #12),
  decay-weighted via the five half-life models, friction/slope
  effort-weighted (novel). Profile-across-k pattern alongside
  seg_profile. Components: W builder, global I and G, local LISA and
  Gi/Gi*, permutation inference (conditional permutation for local -
  a real computational piece, plan chunked/seeded). Mandatory loud
  warning in docs + RunLog: autocorrelation of R_k columns measures
  an already-smoothed surface (overlapping neighbourhoods induce
  correlation by construction) - legitimate but must be understood.
  Validation: known answers cross-checked against PySAL esda on
  fixtures. SEQUENCE AFTER #12 (weights builder should speak the full
  neighbourhood menu from birth).


## Session additions (round 2, recorded without coding - NEXT ROUND items)

- **#4a-RT (NEXT ROUND) Round-trip slope effort.** `roundtrip=True` on
  run_knn_slope: two Dijkstra passes per origin (graph + transpose =
  cheapest return path, which may differ from outbound - correct),
  summed, reported as PER-LEG AVERAGE (sum/2) so flat DEM regresses
  exactly to one-way values (regression test extends). No new cost
  models needed: convexity gives p(s)+p(-s) >= 2p(0) for both tobler
  (2.031 at +-5%, 2.419 at +-10%, 3.433 at +-20%) and linear
  (2+(lu+ld)|s|) - varied terrain automatically costs more round-trip,
  the requested physics. Cost 2x runtime. k stays raw-count-defined.

- **decay: gamma-parameterised shifted power (NEXT ROUND).** Audit
  verdict on current power model: half-life is EXACT via the +1m
  shift (w(d)=(d+1)^b, b=ln.5/ln(h+1)) BUT the shift is a hidden
  1-metre reference scale forcing an ultra-heavy tail (h=1000 =>
  exponent -0.10; w(10h)=0.40, w(100km)=0.32). Fix: add
  w(d) = (1 + (2^(1/g)-1) d/h)^(-g) - exact half-life at h for ANY
  tail exponent g (verified g=0.5,1,2,5); g=1 is w=1/(1+d/h).
  Keep current model reproducible as legacy special case. Document
  the tail table (negexp vs power) in the manual.

- **#15 (NEW) Access potential & the opportunity horizon.**
  Theory recorded: uniform POI density + negexp gives marginal access
  a(r) = 2*pi*rho * r*exp(-|b|r) - a Gamma(2) density (chi^2, 4 df,
  up to scale; the user's conjecture confirmed exactly); peak at
  r* = 1/|b| = h/ln2 ~= 1.4427h ("the opportunity horizon");
  cumulative A(R) = (2 pi rho/b^2)[1-(1+|b|R)exp(-|b|R)].
  Components: (a) access_potential surface (Hansen 1959 potential
  accessibility - claim the classical name) from ALL grid/hex
  midpoints incl. unpopulated (zero-mass origin rows on origins=
  machinery); (b) POI-placement surplus surface = REVERSE potential
  sum_i pop_i * w(d(i,x)) - ONE kernel pass, on regular grids a
  convolution => FFT whole-surface in O(n log n), NO ITERATIONS
  (iterations only for competition effects - 2SFCA crowding /
  doubly-constrained - which is #11 territory, optional); (c) greedy
  sequential placement is submodular => lazy-greedy with (1-1/e)
  near-optimality guarantee, no combinatorial search; (d) later:
  friction/slope effort replaces Euclidean d (geometry term becomes
  empirical ring mass), per-individual decay components.
  Related models to keep in view: Huff choice, Reilly breaking-point,
  Wilson entropy family, p-median/MCLP consuming our surfaces.
  Natural sequence: after #12 (needs the neighbourhood menu's
  unbounded decayed-sum mode as substrate).


## v1.3.0 updates (this session)
- ~~#12 Neighbourhood definition menu~~ DONE in v1.3.0, INCLUDING the
  area family (k / r / tau / unbounded decayed sum / AREA - the
  teaching triad k-r-area is now complete in one package). Parity
  checklist ticked except: ring-engine r (redundant - documented
  mathematical equivalence with the stats engine); hex needs no
  change (same engines). Stata: r() live in bridge (pytest) + ado
  (in-Stata untested until next user run).
- NEW parked: weighted quantiles/Gini for area_stats value statistics
  (weights currently apply to N and binary T/R only - loud note in
  docstring).
- NEW parked: r/tau variants in the ring engine IF a decay-at-radius
  use case appears (decayed sums already live in the fast engine).
- Unblocked by this release: #13 cookbook radius scenarios, #14
  weights matrices (kNN + distance-band + decay all available), #15
  (unbounded decayed sum = the access_potential substrate), #11.


## v1.4.0 updates (this session)
- ~~#4a-RT round-trip slopes~~ DONE (per-leg average; flat==one-way
  exact; known-answer + symmetry + convexity pytest).
- ~~decay: gamma-parameterised shifted power~~ DONE (exact half-life
  any gamma; legacy kept; horizon analytic, INFINITE for gamma<=1).
- ~~#15 access potential & opportunity horizon~~ DONE (FFT
  potential_surface exact-on-grid, surplus = reverse potential,
  effort_potential incl. round-trip; Malta: full-island surfaces in
  1.4 s, optimal next-POI at Birkirkara-Msida, terrain access tax
  2.6% mean / 15.9% max, frontier-vs-core finding, coming-home
  penalty p95 6.9%). PARKED from #15: greedy sequential placement
  helper (submodular, 1-1/e); Huff/Reilly/Wilson/p-median remain
  a recorded modelling menu; competition = #11.
- Next natural: #11 kFCA (all substrates now exist) or #14
  autocorrelation; #13 cookbook grows alongside.


## v1.5.0 updates (this session)
- ~~gamma-figure~~ DONE (examples/cookbook_01_gamma_decay.py - #13
  entry 01; negexp dashed reference as endorsed; horizons drawn:
  g=2 -> 4.83 km, g=4 -> 3.52 km, negexp 2.89, g<=1 infinite).
- ~~#11 kFCA/ELMO-3SFCA (module)~~ DONE: reach modes decay/r/k/effort
  (round-trip capable), 2SFCA + 3SFCA, doubly-constrained balancing
  (margin scaling for imbalanced markets + GAUGE FIXING of factor
  scale - both loud, both tested), match-table orchestrator.
  **REAL-DATA ACT PENDING RE-UPLOAD** of People.sav + LowEduJobs.sav
  (uploads failed to reach the container this round); the joint-
  isometry anonymiser is ready and self-checked, so headline run +
  shareable fixture are one command after re-upload.
- NOTE: mystery *_synthetic.sav files found in session outputs were
  REJECTED (jobs coordinates spanned 900 km for one municipality -
  geometry not trustworthy); nothing was built on them.
- NEW parked: kFCA reach where k counts OWN-side mass (competition
  catchments) as an alternative convention - decide with real data.
- NEW parked: FCA congestion maps + Stata bridge exposure of fca().


## v1.5.1 updates (real-data act)
- #11 REAL-DATA ACT DONE: municipality labour market run (2SFCA/3SFCA/
  kFCA/balanced), education-gap map, congestion map; fixture +
  checkpoint regression in suite (isometry-proven identical);
  synthetic .sav pair delivered for sharing (full files, jobs
  Sweden-wide as in the original).
- User's "simple solution" steps 1-4 confirmed == method="2sfca"
  (the default); J column added so step 1 is a first-class output.
- NEW parked: per-cell effective-pressure output (J/A) as a named
  column; commuting half-life estimation from observed flows (would
  need a flows file); kFCA own-side-mass convention decision.


## v1.6.0 updates (this session)
- ~~#17 generic Stata dispatcher~~ DONE (dispatch() + equipop_run.ado,
  five engines, fca-first as planned; sfi-stub verbatim-validated;
  in-Stata maiden run = user-side action). FUNCTION_MATRIX.md now in
  repo docs/ (SB row spans FC/ST/FR/SL/FA). GitHub-fetch workflow
  PROVEN this session (clone of tag v1.5.1, 38/38 before build).

- **#18 (NEW, designed) CONTINENTAL SCALE - very large data
  (user: 16M coordinates run in old EquiPop; Europe-wide 100 m
  grids; memory is the constraint, not time).** Arithmetic: Europe
  bbox ~5000x4500 km at 100 m = ~2.25 BILLION domain cells - engines
  must NEVER materialize domain-sized arrays; populated cells from
  16M coords (~10M unique) fit RAM comfortably (KD-tree ~GBs).
  Architecture per engine:
  (a) fastcounts: chunked KD-tree already streams; add TILE-AND-FLUSH
      (absorbs the parked item): process origin tiles, write parquet
      per tile, float32 outputs, uint32 counts; k-NN has NO a-priori
      radius bound -> per-tile halo from local density estimate with
      the EXISTING straggler re-query as exactness guarantee (seams
      exact by construction, not by hope).
  (b) graph engines: restrict domain to inhabited + corridor cells
      (sparse node set), or tile Dijkstra with halo = tau_max *
      max-edge-cost bound; hex same when hex-friction lands.
  (c) FFT potential: tiled overlap-add with kernel-radius halo -
      mathematically EXACT, memory = tile + halo only.
  (d) fca: supply-side tiling with decay-truncation halos.
  (e) I/O: memory-mapped/parquet chunks in, progressive RunLog with
      per-tile md5 manifest + resumable rerun() (absorbs the parked
      rerun()-from-meta idea), float32 by default at this scale.
  Priority order: (a) first - matches the user's 16M k-NN use case;
  validation: tiled run == untiled run EXACTLY on a mid-size fixture.


## v1.7.0 updates (this session)
- ~~#18a tile-and-flush (fast engine)~~ DONE: origins= on fastcounts,
  bigrun module (parquet tiles, manifest+md5, resume), golden
  tiled==untiled test, 250k-origin/1.5GB demo, ~2h extrapolation for
  the 16M use case. Absorbs the old parked tile-and-flush item.
- #18b-e remain parked until data demands them: graph-engine corridor
  subgraphs / halo Dijkstra; overlap-add FFT tiling; fca supply
  tiling; mmap/parquet ingestion; true domain tiling with
  density-estimated halos (>100M cells).
- Board next: #16 propensity FCA (2x2 runnable on delivered data) or
  #14 autocorrelation; user-side: tag v1.6.0 + this v1.7.0 release.


## v1.8.0 progress (Book session 1)
- #19 underway: Gridby generator (planted truths PYTEST-ENFORCED:
  gradient recovered, river isochrone bites, hill peak exact, jobs
  cluster share), equipop.datasets loader (gridby/municipality/
  berlin/stata_test), chapters 1+2+4 written in docs/book/ with two
  cookbook figure scripts (02, 03), compile pipeline + first .docx
  sample this session. Next book bites: ch 13+16 (Stata Journal
  feeders), then Part II.


## v1.8.1 (CI fix round)
- Root cause of the reported pytest/GitHub errors FOUND AND
  REPRODUCED without needing the logs: test extras lacked pyarrow
  (bigrun parquet) - failed on every clean env; also rasterio absent
  meant the DEM test never actually ran on CI. Fixed (extras +
  importorskip + helpful bigrun error). Verified three ways: bare
  env 44+3skip, +pyarrow 46+1skip, full 47/47.
- WATCH: rasterio/NumPy2.5 DeprecationWarning (upstream, cosmetic).
- REMINDER: GitHub main is STILL at 1.6.0 - pushes for 1.7.0/1.8.x
  have not left the local machine; the 1.8.1 zip supersedes all -
  ONE swap-commit-push-tag carries everything, CI should then show
  47 green x 2 Pythons.


## v1.9.0 updates (this session)
- ~~#14 spatial autocorrelation~~ DONE (weights from the menu, I/LISA/
  Gi* esda-cross-validated, multiscalar profile, loud smoothed-surface
  warning, Gridby ch.11 figure). NEW small parked: dispatcher engine
  "lisa" (row-aligned Ii/quad/p to Stata - Stata Journal candidate);
  hex weights (6-neighbour) when hex-friction lands; permutation
  chunking for national-scale LISA (#18 family).
- Board next: #16 propensity FCA, Book chapters 13+16, or #7 QGIS.


## v1.9.1 (Book-per-release round)
- CONVENTION ADOPTED: every release = zip + manual + backlog + BOOK
  (compiled docx, version-stamped). Locally: docs/book/build.sh. On
  CI: the new "book" job uploads EquiPop_Book.docx as an artifact on
  every push (find it: Actions -> run -> Artifacts, bottom of page).
- Chapter 11 written (4 chapters compiled of 20; ~9 pages - Part II
  will thicken the volume). Next bites: ch 13 + 16.


## v1.10.0 updates (#16 round)
- ~~#16 propensity match-table FCA~~ DONE (group + cell modes,
  estimators (c)+(f) as user chose; identity regression free; ch13 +
  cookbook_05 on the register fixture; Book compiled).
- kFCA continuation UPDATED per user: parametrize k_side AND return
  BOTH sides side-by-side (A_kjobs, A_kworkers) - "having them both
  could be interesting in analyses". Queued with the divergence-map
  experiment.
- AWAITING USER: estimated M from their regressions (area effects
  stripped, per ch13) -> rerun the municipality act as RESEARCH, not
  scenario; candidate Stata Journal exhibit.


## v1.11.0 (Voice + lisa round)
- Book style guide EXECUTED on ch01/02/04/11/13; ch16 born in the
  register; sample-approved voice now the volume's voice.
- ~~lisa dispatcher engine~~ DONE (Stata Journal exhibit ready:
  equipop_run, engine(lisa) x() y() values(R_HighEdu_400) -> LISA
  variables for spmap/regress).
- Writing/coding split adopted: next WRITING session = Part II
  chapters (5-7); next CODING session = kFCA k_side both-sides +
  divergence experiment (awaits nothing) or RunLog audit.


## v1.12.0 updates (kFCA both-sides round)
- ~~kFCA continuation~~ DONE (k_side incl. "both"; A_ksupply/A_kdemand
  per user naming; divergence experiment: corr 0.329 on the
  municipality - conventions measure different geographies).
- Small parked: expose k_side in dispatcher/ado fca engine.
- ch5-7 pack merged into repo; Book at 9 chapters.

## GIS & stats-software bridges (feasibility discussion, FOR LATER)
- #7a QGIS Processing provider: HIGH feasibility, first target.
  QGIS runs Python; pip-install equipop into its interpreter, wrap
  engines as Processing algorithms -> appears in the Toolbox, chains
  with all QGIS tools. #7b full Plugin (GUI dialogs, plugin
  repository distribution) builds on 7a.
- #21 ArcGIS Pro Python toolbox (.pyt): HIGH technical feasibility -
  Pro is conda-based Python; a thin .pyt wraps the same engines
  (glue-only, all math stays in the tested package). Constraint:
  arcpy cannot run in CI (licence) -> validate the glue via a stub,
  exactly the Stata discipline.
- #22 SPSS: MEDIUM. Path A: SPSS Statistics Python integration /
  extension command mirroring equipop_run. Path B (zero-maintenance,
  available TODAY): documented .sav round trip - read .sav, compute,
  write .sav back (pyreadstat already in the io extras); a Book
  appendix recipe rather than code.
- R: an R version predates EquiPop; a thin reticulate wrapper would
  expose the Python package natively in R - LOW effort, note kept.
- Shared principle for ALL bridges (the Stata lesson): hosts get
  GLUE ONLY; mathematics lives in the pip package where pytest
  guards it; every glue layer gets a stub validation.
