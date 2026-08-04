# EquiPop Pangea — Backlog of small items to batch in later

Workflow: suggestions are appended here without altering code.
When we decide to batch, items are implemented, validated, moved to
the manual's version history, and struck from this list.

| # | Added | Item | Notes |
|---|-------|------|-------|
| ~~1~~ | DONE v0.7 | Seeded tie-break orientation: a user-settable seed determining the within-ring visiting order in `tie_mode="sequential"`, with the seed written to the metadata log (`settings.seed`) | Ring mode unaffected (order-free by design). Makes sequential mode fully reproducible. |
| ~~2~~ | DONE v0.7 | Metadata log file — full design agreed, see below | Implement as one batch; pairs with #1. |
| ~~3~~ | DONE v0.7 (convert path; 6-neighbour hex friction remains) | Hexagonal grids: convert or simply import point/raster data as hexagons (X/Y/Z axial or cube coordinates) | From the original spec. Design thoughts below. |
| ~~30~~ | DONE v1.17 | Category & friction VALUE TABLES in the Pro dialogs (John's Extract-Multi-Values pattern): a grid with *value* (dropdown built from the field's own distinct values), *group name*, *in population?* - retires the `;`/`,`/`:` syntax entirely and expresses "in a group but not in the population" (services near residents). Same grid for MULTI-SOURCE friction: source + friction field per row, so lines + lake + raster finally coexist and the overlap rule becomes reachable at all | Field-found: `shop, school` parsed as ONE group matching zero rows; also today's only way to combine barriers is a single layer |
| ~~31~~ | DONE v1.17 | Persons-versus-places rule for category groups: with a population field set, N counts PERSONS while category flags count ROWS, so R = places / persons silently. Add an explicit control (default: weight categories by the population field) and state it in the messages and manifest | Field-found: T=4 places over N=140 persons |
| ~~32~~ | DONE v1.17 | A group/category matching ZERO rows must be a dialog-time REFUSAL naming the field's actual values, not an info line among fourteen | Silent columns of zeros are exactly the wrongness EquiPop refuses elsewhere |
| ~~33~~ | DONE v1.17 | Collapsible dialog sections via each parameter's `category` property (Coordinates / Neighbourhood / Groups / Barriers and terrain / Output / Advanced) + a full label pass saying what each box DOES | 29 parameters presented at once; John: "they were not fully clear to me watching the menu" |
| 34 | open v1.16.8 | Tool help page: summary/usage sections render empty in Pro. Suspect `SyncOnce=TRUE` letting Pro regenerate over the authored text, plus missing `datatype` attributes and plain text where escaped HTML is expected. The per-parameter comments (dialogReference) DO work | Needs one field cycle to confirm |
| ~~35~~ | DONE v1.17 | Individual / local TAU (effort budget from a field or a single value), mirroring variable-bandwidth decay. Easier than decay: the traversal already stops at a budget, so a per-origin budget is just a different stopping value. Naming: N_tau_<field> since the column can no longer carry the number | John: tau is the HARD prism boundary, half-life the soft one - both parameterisable per person is a time-geographic instrument |
| ~~36~~ | DONE v1.17 | Variable-bandwidth decay (the 1.17 theme): half-life from a field or self-calibrated from Dist_k (urban form sets the bandwidth); bucket into quantile bins so cost is dominated by the largest bin; combine several potentials via log-odds / geometric mean of half-lives, all three behind one switch and compared on Gridby | John's ladder: 1 no decay, 2 one parameter, 3 group potentials (Hägerstrand prisms), 4 form-derived, 5 principled merger |
| ~~37~~ | DONE v1.17 | Seed exposure + manifest entry wherever permutations happen (morans_i, sequential tie-break). Engines are otherwise deterministic - note in the manual that this holds as long as summation order does | |
| 38 | open v1.16.8 | Continental segmentation wired into the GUI: origin tiling (bigrun, already built and tested, currently unreachable) with output folder + resume; halo-based full partitioning only if destinations stop fitting, with the halo checked against Dist_k and widened for the origins that touched it; merge on an explicit EQP_ID, never OID (ArcGIS renumbers OIDs on copy) | John's B1-10/C1-2 sketch |
| ~~39~~ | PARTS 1-2 DONE v1.20.0 | ~~Shared core ahead of the QGIS/R/SPSS doors: one help-text source, one reporter object, one loader contract~~ - DELIVERED as `equipop.doors` (help / report / fields / loader), ArcGIS re-pointed, 154 tests green. REMAINING: QGIS Processing plugin (simulated PyQGIS like the fake arcpy), R via reticulate (file bridge as documented fallback), SPSS via its Python integration. Gridby's answer key becomes the cross-door conformance suite | The ArcGIS glue got fat because three things were reinvented per door |
| 40 | open v1.16.8 | Gridby README: Test E must say to clear BOTH the population field and the group count fields (the key assumes one row = one person) | Documentation error found in the field |
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


## v1.13.0 updates (#21 ArcGIS opener)
- ~~#21 first release~~ DONE: 3 tools (user's priorities 1+2 first-
  class, friction included as the ready door), stub-validated glue,
  guide. MAIDEN RUN user-side: add .pyt in Pro, Tool 1 on any point
  layer. Future #21b: LISA + FCA tools (after maiden feedback),
  symbology presets, tool 3 accepting a polyline barrier layer
  (auto-rasterize rivers/roads to friction cells - natural next).
- Decay now flows through the counts ROW path everywhere (Stata ado
  inherits it free via dispatch - expose halflife() option: small).


## v1.14.0 (#21b - the field-tested toolbox)
- ~~#21b~~ DONE, all spec items incl. category mode + categorical
  package factory. John's two observations resolved: Dist_k =
  floating radius (now self-explaining), T>N = counts-without-
  population (now auto-hinted + honest labels).
- REMAINING #21 family: Stata catvar()/treatvalues() options (the
  factory is waiting), per-parameter metadata XML sidecars (polish),
  LISA + FCA tools (#21c), polyline-barrier auto-rasterizer.
- Book at 14 chapters, riding this release.


## v1.14.1 (hotfix - the counts-convention bug, found by John on the
## real register through ArcGIS; shapefile name truncation decoded in
## chat -> reinforce gdb / New-feature-class-to-gdb advice)

## STATA-UX SPEC (feedback from Umut - next Stata session)
- i) NATURAL INSTALL, two stages: (a) NOW: `net install equipop,
  from(https://raw.githubusercontent.com/GeoJohnSwe/EquiPop/main/stata/)`
  - needs stata.toc + equipop.pkg files in stata/ (small, buildable
  immediately); ado then CHECKS for the python package and prints
  the pip line if absent. (b) LATER: SSC submission (bundle ados +
  sthlp help files + ancillaries, email to SSC maintainer) ->
  `ssc install equipop` for the world.
- ii) `help equipop` -> write SMCL help files: equipop.sthlp
  (overview + engines table), equipop_run.sthlp, equipop_knn.sthlp
  (syntax, options, examples with expected output, the two treat
  conventions EXPLAINED).
- iii) VARIABLE LABELS on every generated variable (via `label
  variable` after store): e.g. R_HighEdu_400 -> "EquiPop: share
  HighEdu among 400 nearest"; plus a prefix() option (e.g.
  prefix(eq_)) so new variables sort together and cannot collide
  with old ones; the completion message already lists them.


## v1.15.0 (#21c delivered)
- ~~#21c items 1-3~~ DONE per confirmed spec. Deferred honestly:
  stats-over-effort engine (machine 2 ingredients await it);
  decay-over-effort; one-click Pro wrapper for features_to_friction
  (needs geopandas in the Pro clone - document or wrap);
  negative-friction/speedups discussion.
- Next candidates: the 1.17 dialog + theory round (items 30-36:
  value tables, persons/places, collapsible sections, variable
  bandwidth and individual tau), then the shared-core refactor and
  the QGIS door (39). Stata-UX round (Umut, on his return), #21d
  LISA/FCA tools, writing ch14+15+17.

## v1.18.0 (the shared core - BACKLOG 39, part 1 of 3)
- ~~39, part 1~~ DONE. `equipop/doors/` now holds what every door was
  rebuilding: `help.py` (the text beside every box, keyed by
  parameter name), `report.py` (Channel + Reporter + stage: the
  package's printed voice into arcpy messages / QGIS feedback /
  console / silence), `fields.py` (predicted result names, 10-char
  shortening, the refusal - with the roomy container as an argument
  so QGIS says GeoPackage where Pro says file geodatabase),
  `loader.py` (PointInput, the coordinate rules, the projection
  hint, and DoorError). ArcGIS re-pointed with behaviour unchanged;
  114 existing tests green untouched + 40 new door-blind ones.
- Contract check added: each door declares `_CONTRACT`, the package
  refuses a mismatch by name and says which half to replace. Also
  closes an old rough edge - a missing package used to give a bare
  ModuleNotFoundError mid-run; it now gives the pip line.
- REMAINING in 39: (2) the QGIS Processing plugin against a
  simulated PyQGIS, the way fake arcpy works - the shared core is
  the half of this that is now done, and `Channel.from_qgis` and
  `refuse_short_target(container=...)` exist ready for it; (3)
  Gridby's answer key through both doors as the conformance suite.
  Then R (reticulate) and SPSS.

### Found while doing it (not acted on)
- 41 | open v1.18.0 | MANUAL.md had NO 1.17 row - the release went in
  without its version row, validation record or design decisions,
  against the standing convention. A reconstructed row was written
  in 1.18.0 from the session handover and is marked as such; **John
  should check it against what actually shipped.** The 1.17
  validation record was deliberately NOT reconstructed: writing one
  would mean claiming validation nobody performed.
- 42 | open v1.18.0 | docs/manual/ (the illustrated ArcGIS
  walk-through) does not describe variable-bandwidth decay at all -
  the headline feature of 1.17. Decay gets one sentence in section 2
  and the ND_/TD_/RD_ columns in section 7, with nothing on
  half-life from a field or self-calibration from Dist_k. WRITING
  session item. While there: the manual's own plain-words habit
  ("two rulers", "doubling it quarters the work", "a finding, not a
  nuisance") is the model the queued naming pass should copy.
- 43 | open v1.18.0 | CITATION.cff still says `version: 1.0.0` while
  the package is at 1.18.0. Left alone deliberately - citation
  metadata is the author's to set, and it matters more than usual
  ahead of the Zenodo DOI at 2.0.0.
- 44 | open v1.18.0 | `make_help_xml.py` still writes
  `SyncOnce=TRUE`, the suspected cause of item 34 (summary/usage
  rendering empty in Pro). Untouched this round: it needs one field
  cycle to confirm, and this was a refactor release. Now a one-line
  change in a single place whenever that cycle happens.
- 45 | open v1.18.0 | The simulated-arcpy tests write their output to
  the Windows-style catalog paths they pretend to use, so a test run
  on Linux leaves four literal files named `C:\Data\...csv` in the
  repo root (and one stray figure from the Book build). Harmless,
  untracked, and cleaned by hand this round - but they belong in
  pytest's tmp_path, and on Windows those paths are real. Small.

### 1.18.0, second pass: the source archive
- 46 | DONE v1.18.0 | The `.tar.gz` carried the package and the test
  CODE but not the ArcGIS toolbox, the Stata door, the fixtures its
  own tests read, or CITATION.cff. Verified against PyPI, not
  inferred: unpack the published equipop-1.17.3.tar.gz and 39 of its
  41 ArcGIS tests fail immediately on the missing EquiPop.pyt. An
  academic package also went out without its citation file.
  Long-standing (no MANIFEST.in had ever existed) and not caused by
  the shared core, but 1.18.0 makes it matter more: the toolbox and
  the package are now two halves of one thing. MANIFEST.in added;
  the Book's figures stay out because build.sh regenerates them
  (4.2 MB of a 4.8 MB archive). Archive now 121 files, 605 KB, and
  the whole suite - all 154 - passes from inside the unpacked
  archive alone.

## v1.18.1 (one-line fix, found from John's upgrade routine)
- The toolbox told the wrong story for the LIKELY half of version
  skew. John upgrades the package with pip and replaces the toolbox
  files by hand - two steps, easily done in the wrong order or in
  the wrong Pro environment. With a new toolbox and an old package,
  `import equipop.doors` fails and 1.18.0 said "the EquiPop Python
  package is not installed", sending the user to look for a package
  sitting right there. It now tells the two cases apart: missing
  entirely -> install; present but older -> names the version found
  and says `pip install --upgrade equipop`. Test added and verified
  to fail against the old message. 155 tests.

### Found while ruling on the conformance reference (for 1.19.0)
- ~~47~~ | DONE v1.19.0 | **`load()` fails for anyone who installed from PyPI.**
  All four datasets: `gridby` reaches into `../examples/` for
  make_gridby.py, and `municipality`/`berlin`/`stata_test` reach into
  `../tests/` and `../stata/` - none of which is in the wheel.
  Verified in a clean venv against the 1.18.1 wheel: four failures
  out of four. Book chapter 1 line 85 tells the reader to type
  `g = load("gridby")` as their first act. Gridby is the TEACHING
  town, so this is the first thing a student hits. MANIFEST.in fixed
  the source archive; the WHEEL is a separate matter and is what
  students actually install. Fix: move the Gridby generator into the
  package (`equipop/gridby.py`, with examples/make_gridby.py left as
  a shim), ship the small fixtures as package data, and declare them
  in pyproject so they enter the wheel. Then a clean-venv test that
  loads all four - the kind of check that only fails outside the
  repo, which is why it has never fired.
- ~~48~~ | DONE v1.19.0 | The cross-door conformance reference (ruling made,
  1.18 session). Format: CSV, UTF-8, dot decimal, comma separator,
  fixed column order - every door reads and writes it natively, and
  a student can open it in Excel. It ships INSIDE the package
  (`equipop/data/`) so all four doors and every student reach it the
  same way whatever their install. Generated by the Python core -
  already the trusted engine - from Gridby at a fixed, documented
  parameter set. Comparison lives in `equipop.doors` so Pro, QGIS,
  Stata and SPSS all judge themselves identically: counts and Rounds
  EXACT (they are integers), continuous columns within a stated
  tolerance. Blocked on 47: shipping data inside the package is the
  same fix.


## v1.19.0 (the teaching data ships; the doors get an answer key)
- ~~47~~ DONE. Gridby's generator moved into the package
  (equipop/gridby.py, shim left in examples/); the Book's other
  dataset moved to equipop/data/ and is declared in pyproject, so
  the wheel carries it. Verified from a clean venv: gridby and
  municipality load, berlin names openpyxl as the missing reader,
  stata_test refuses by saying where to get it. tests/test_packaging
  .py added - it checks the SHAPE of what ships, which is the only
  way to catch a bug that cannot fail inside the repo.
- ~~48~~ DONE. equipop/doors/reference.py + equipop/data/
  gridby_reference.csv (2360 x 14, both engines and the radius
  path). compare() judges any door: counts exact, continuous within
  tolerance, rows matched on coordinates. explain() turns the report
  into sentences for a door's message pane.
- NEXT: the QGIS Processing plugin (BACKLOG 39 part 2). It now has
  both halves of its foundation - the shared core to build on, and
  the reference to be judged by from its first day.
- 49 | open | The reference covers counts and stats. Friction,
  slope, fca and lisa are not in it. Worth extending once a second
  door exists to prove the mechanism, rather than guessing now what
  a door will need.


## v1.20.0 (the QGIS door)
- ~~39 part 2~~ DONE. qgis/equipop_qgis/ - provider, plugin scaffold,
  and two algorithms (Counts and Shares, Value Statistics) built on
  equipop.doors. tests/qgis_stub.py simulates PyQGIS the way fake
  arcpy simulates arcpy. 14 door tests + the conformance pair.
- ~~39 part 3~~ DONE in effect: BOTH doors now pass the Gridby
  reference, 2360 rows, every column. That was the definition of a
  finished door and it is now a test in each suite.
- FIXED: the 1.19.0 reference named its treatment 'minority' while
  every door names treatments by FIELD - so no door could ever have
  matched it. Caught only by building the second door, which is
  itself the argument for building the second door.
- qgis/README_QGIS.md - the one-page install note (equipop must
  reach QGIS's own Python; OSGeo4W shell or the QGIS Python Console,
  where sys.executable cannot be the wrong interpreter).

### Open, in priority order (John's arrangement, 1.19 session)
- 50 | PARTLY DONE v1.21.0 | QGIS gained the CATEGORY TABLE (with the
  remainder box) and DISTANCE DECAY. Still missing: BARRIERS and
  TERRAIN, which need the friction-building path (points/paths to
  friction, DEM slope) ported to read QGIS layers. Same engine
  underneath. Same shared code underneath - boxes to add,
  not machinery to build. The remainder box (below) should land here
  at the same time.
- ~~51~~ | DONE v1.21.0 | THE REMAINDER BOX (agreed with John, 1.19 session):
  one box under the category table - "Put every other value in this
  group:" - so a few values can be named 'service' and everything
  else falls into 'other', in the population. Today the only way is
  to untick every 'In population?' box, which reads backwards. Build
  the rule in the engine and the help in the shared core so BOTH
  doors get it.
- ~~52~~ | CLOSED v1.22.2 as NOT OURS | GeoPackage attribute table does not refresh after a
  run (John, field, 1.19 session). The toolbox writes with
  ExtendTable and declares NO derived output, so Pro keeps its
  cached schema; removing and re-adding the layer forces a re-read,
  which is the workaround John found. Likely fix: declare the
  modified layer as a derived output parameter. UNVERIFIED - needs a
  field cycle on Malta.gpkg AND on a file geodatabase.
- 34/44 | open | Tool help page summary/usage renders empty in Pro;
  SyncOnce=TRUE suspected, one line in make_help_xml.py. Needs a
  field cycle. Students read this page.
- 42 | open | docs/manual/ never describes variable-bandwidth decay.
  WRITING session.
- 43 | open | CITATION.cff still says version 1.0.0.
- 49 | open | The reference covers counts and stats; friction,
  slope, fca and lisa are not in it. Now that a second door exists
  and the mechanism is proved, this is worth doing.
- 38 | open | Continental tiling into the GUI. Paused by John.
- 45 | open | Tests leave literal C:\Data\... files in the repo root.


## v1.21.0 (Malta: three GeoPackage findings + the remainder box)
- ~~46 (Malta a)~~ category dropdown: read through the layer OBJECT,
  not a path; report success and failure out loud.
- ~~(Malta b)~~ ExtendTable unsupported on GeoPackage -> _add_columns
  falls back to AddField + UpdateCursor and explains the trade.
- ~~(Malta c)~~ CopyFeatures renames the identifier (fid ->
  OBJECTID); the values now travel with the copy.
- tests/test_geopackage.py + a GeoPackage-shaped simulator fixture
  (oid_names, no_extend, a dataSource that refuses to reopen). All
  three field failures reproduce here first, then pass.
- ~~51~~ the remainder box, in the engine so both doors share it.
- Missing-data rules written down for BOTH machines (John's ruling):
  group counts -> zero; continuous values -> excluded, Nv reports.
- QGIS: category table + remainder + decay. Fixed: the QGIS reader
  forced text columns to NaN.
- ~~53~~ | DONE v1.22.1 | The barrier path went through the same
  _ref(), so the catalogPath fix closes it too - though a barrier
  from a .gpkg still has not been FIELD-tested.
- 54 | open | Gridby has NO missing data, so the missing-data rules
  are tested only on small fixtures. A Gridby variant with holes
  punched in it would test the documented rule properly.

## v1.21.1 (the Groups section, made legible)
- Placement bug from 1.21.0: restgroup/restinpop had no SECTION, so
  Pro floated them to the top of the dialog, above the field they
  depend on. One missing line in the SECTION map; found in the field
  within a day, which is the argument for shipping small.
- Groups split into three headings; the unused route greys out; the
  remainder box waits for a category field. Population field stays
  live in both, since it applies to both.
- Labels: the remainder box asks for a group NAME with an example.
- QGIS: same clarity by ordering and wording (no sections there).
- 55 | open | The dialog-structure tests assert Pro's `category` and
  `enabled`; the simulator honours both, but only a real Pro can say
  whether the three headings read well on screen. Worth a look in
  the next field cycle.

## v1.22.0 (two populations)
- The dialog reorganised around REFERENCE and TREATMENT populations,
  matching the words the T_ and R_ columns have always used.
- cattable (value/group/in-population) split into reftable (which
  values are around) and treattable (which values form which group).
  An EMPTY reference table means everything - the fastfood-per-POI
  vs fastfood-per-eating-place distinction, with no tick.
- treatvalue: the treatment population's own value field. Empty =
  the reference's field (same units, R_ is a share). Different =
  a ratio, warned about plainly.
- groupscount RETIRED: the value fields carry that meaning now.
  Places-over-persons is no longer reachable (it was the 1.17 bug).
- categories_to_binary gained rest_in_population=None, meaning "the
  population is decided elsewhere" - needed once a separate
  reference table exists.
- Warnings appear beside their fix AND at top level, since Pro hides
  a warning inside a collapsed section (John, field).
- 56 | open | Machine 2 (Value Statistics) still uses the old
  vocabulary - "Full population field", "Numeric value fields". It
  should be reference-population language too, for the same reason.
- 57 | open | The old single-table path (cat_rows) is kept in
  _run_tool for compatibility but is no longer reachable from the
  dialog. Retire once John confirms no saved tools depend on it.

## v1.22.1 (the one-line root of the Malta round)
- _ref() now resolves through arcpy.Describe(value).catalogPath, for
  names as well as objects. catalogPath is not an attribute of a
  Layer - it belongs to its Describe - so the branch that was meant
  to produce a workable path never ran, and everything fell through
  to dataSource, which a GeoPackage reports as an unusable
  connection string.
- One line behind three field failures. The write, the dropdown and
  (latently) the barriers all used the same helper.
- The simulator models it: the layer is refused, the catalog path is
  accepted, and a catalog path resolves back to its layer.
- 58 | open | A GeoPackage barrier layer has still never been run in
  the field. The code path is now believed sound; only Pro can say.

## v1.22.2 (rows outside the reference; the GeoPackage verdict)
- keep_outside (default TRUE, John's ruling): a row outside the
  reference population counts as ZERO people - nobody's neighbour -
  but still gets its own results. Was: dropped, Null. Both doors.
  A test asserts keeping them does not move the numbers of the rows
  already inside, which is what "counts as zero" has to mean.
- 52 CLOSED as a HOST limitation, evidenced not inferred: Pro does
  not show new fields on a GeoPackage layer in a map; Add Field is
  greyed out with "the table or its schema is read only" on a clean
  project. Esri community enhancement request open, reported from
  Pro 3.0.2 through 3.5.2, and the same files behave normally in
  QGIS. The dialog now warns at DIALOG time and points at Output =
  New feature class.
- 59 | open | Does the QGIS door refresh GeoPackage fields properly?
  Expected yes (OGC format, QGIS's native default). If so it is a
  real argument for teaching on QGIS with .gpkg data - worth knowing
  before September.

## v1.23.0 (the ladder made visible)
- refmode / treatmode: three rungs each, simplest first, with the
  boxes a rung does not need greyed out. John's design, agreed by
  sketching the structure back and forth before any code.
- treatvalue RETIRED (reverses 1.22.0): k is confined to the
  reference population, so the treatment shares its units. Every R_
  is a share by construction.
- treatcatfield added: the treatment names its own type column, so
  its section reads on its own.
- keepoutside is a two-way choice, not a tick (John: "should be an
  active choice").
- Help now states totals-vs-averages: machine 1 SUMS its group
  columns; per-point averages belong in machine 2, which weights by
  the reference population. Verified empirically: two locations, 10
  people at 100 and 1 person at 1000, give the weighted 181.82 and
  not the unweighted 550, with Nv reporting 11 persons not 2 rows.
- 60 | open | MACHINE 2 still uses the old vocabulary and has no
  ladder. Same treatment needed: a reference-population section with
  the same three rungs, and value fields named as values (weighted
  by the reference), not as "treatment".
- 61 | open | The dialog structure is simulator-proved only. Whether
  three rungs and the greying READ well in Pro is John's call.

## v1.24.0 (four write-path bugs from one evening in the field)
- outfc/outtable declared direction="Output". Every parameter was an
  INPUT, so Pro's browse dialog would not create a new feature class
  ("Cannot access anyfile"). Present since the toolbox was written.
  The simulator checked names, types and sections but never
  DIRECTION - now it does, and the check was verified to fail when
  the bug is put back.
- _write_failure(): one diagnosis for locks / unsupported formats /
  refusals, keeping the ORIGINAL arcpy error in the message. The add
  path also retries, as the update path has since 1.17.
- Cloud-synced folders (OneDrive, Dropbox, SharePoint...) named on
  input and output, in both doors. Esri documents this as
  unsupported and the symptoms match exactly.
- Dialog-time checks: missing output path, synced folder, shapefile
  in an open map.
- 62 | open | The shapefile-in-a-map warning fires whenever the
  input is a .shp and the output is not a new feature class. It may
  be too eager - a shapefile NOT in a map is fine, and the toolbox
  cannot tell from the path alone. Watch whether it becomes noise.

## v1.25.0 (QGIS layout; a parity gap)
- FOUND: 1.23.0's QGIS edit half-applied - refmode never reached the
  QGIS door, so the reference ladder existed only in Pro. The parity
  test checked QGIS names are a SUBSET of Pro's, which a missing box
  satisfies. Now checked both ways against a named CORE set.
- QGIS layout, within what Processing allows: Advanced area for the
  rarely-touched boxes, numbered labels (1 / 1a / 2 / 2b / 3 / 4),
  ladder order, tooltips from the shared help.
- qgisMinimumVersion 3.16 -> 3.28, with "tested on 3.42" stated.
- [stata] full population now names the total.
- ~~63~~ | DONE v1.26.0 | Barriers and terrain in QGIS. Deferred
  again rather than started half-finished - it needs the friction
  building path (points/paths to friction, DEM slope) ported to read
  QGIS layers, which is a round of its own.
- 64 | open | MACHINE 2 vocabulary (was 60) - not started.
- 65 | open | The OneDrive warning did not fire on John's run. Most
  likely that run predates 1.24.0; confirm before hunting.
- 66 | open | Editing multi-line Python by blind string replacement
  damaged alg_counts.py this round; recovered from the release zip.
  Read the real text first (view/sed), then str_replace against it.

## v1.26.0 (barriers and terrain in QGIS)
- qgis/equipop_qgis/barriers.py: vector barriers (points, lines,
  polygons, multipart), friction rasters, elevation for slope, tau
  budgets, round-trip, overlap rule. Reprojected to the working CRS.
- The engine wants features as {"type": ..., "parts": ...} - line
  charged by LENGTH, polygon by AREA - and friction means a
  DIFFERENT ENGINE (friction/slope), not an extra argument. Both
  found by test, not by reading.
- Parity test corrected: it now asserts every box in either door has
  an entry in the shared help, rather than requiring identical
  widget names. Pro's barrier VALUE TABLE and QGIS's layer+field are
  the same idea in two hosts.
- 67 | open | QGIS barriers are simulator-proved only. The ArcGIS
  round is the evidence for how far that is from proved.
- 68 | open | Reading a GeoPackage in QGIS took 5.5 s against 0.3 s
  of calculation (John, field, 8730 points). read_points builds a
  Python list of features and loops per attribute. Worth optimising
  before continental work.
- 69 | open | MACHINE 2 vocabulary - still not started (was 64).

## v1.26.1 (Malta's barrier day)
- The barrier was reprojected against the layer's ARRIVAL CRS, not
  the WORKING CRS of the run. Degrees vs degrees -> no transform ->
  40,678 roads in one 100 m cell. base.py now remembers the working
  CRS and the barrier path uses it.
- check_plausible(): refuses a friction surface that cannot be
  right (mass collapse into few cells; no overlap with the points),
  naming the likely cause. THE lesson of the round - the CRS bug was
  one instance of a class, and only the guard catches the class.
- The effort engine emitted T_/R_ with no treatment given. Fixed in
  friction.py and the merge in stata_bridge.py; the counts engine
  was already right.
- ~~70~~ | DONE v1.27.0 | FACILITATORS (John's academic question, worth a real
  answer). Entering a cell costs 1 + friction, so a facilitator is a
  value between -1 and 0: -0.5 halves the cost of a cell, -0.9 makes
  it a tenth. The engine currently refuses anything below zero,
  which is stricter than the mathematics requires - the true floor
  is -1, where movement becomes free. Relaxing it would let
  motorways be modelled as genuinely faster, the natural counterpart
  to barriers for accessibility work. Needs a decision on what
  happens at exactly -1 and whether the shortest-path expansion
  stays well-behaved.

## v1.27.0 (facilitators)
- Costs may now go below zero, down to but not including -1.
  _check_cost_range() names the floor and what the values mean.
- THE reason it could not have been a quiet change: FrictionGrid
  held np.int64, so -0.9 became 0. Now float. Barriers were immune
  to this because whole numbers survive truncation - a good example
  of a bug that only a new feature could reveal.
- Refusals that read: a line layer as INPUT; a barrier smaller than
  one cell, checked BEFORE the engine's value validation.
- check_versions(): plugin and package versions compared, since the
  contract number only moves on structural change.
- 71 | open | The ArcGIS door has no facilitator help text yet and
  its barrier help still says costs must be positive. Same for the
  Book (ch09) - queued with the friction/delay writing session.
- 72 | open | Dist_k under effort is NOT a radius: the neighbourhood
  is a shape moulded by the cost surface, and Dist_k is how far away
  the last person reached happened to be. Comparing Dist_k with and
  without a barrier measures how much the barrier REARRANGED the
  world. Worth a paragraph in the book (John's insight, and Claude
  was wrong about it first).
