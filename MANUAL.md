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
| 1.14.0 | ArcGIS toolbox #21b - the field-tested release (every feature from John's maiden runs): honest Tool-1 labels (Population field / Group count fields, both data shapes taught), "no decay" DEFAULT with half-life box self-disabling (updateParameters), generic Tool 2/3 titles, re-run handling (Overwrite loudly / Stop) + NEW-feature-class output (CopyFeatures, input pristine), CATEGORY MODE (fclass -> population filter + grouped treatments, "food: restaurant, cafe"; excluded rows Null; zero-match warning), Dist_k=metres explanation printed, package-level `categorical` factory (Stata inherits later) + LOUD counts-without-population hint in knn_to_rows; stub grew ListFields/DeleteField/CopyFeatures + text-field fidelity; guide gains the field-tested troubleshooting ladder (exec_prefix, the Roaming stowaway, PYTHONNOUSERSITE). 63 tests |
| 1.13.0 | ArcGIS Pro toolbox (#21, department priority): `arcgis/EquiPop.pyt` - three tools (Counts & Shares w/ k, r, groups, weights AND decay; Value Statistics incl. income median/Gini; Friction Effort w/ barrier csv + tau) over ONE shared glue path; glue-only discipline (all math in the pip package), stub-arcpy VERBATIM validation incl. Null propagation and a decayed-sum cross-check vs dispatch; shapefile 10-char warning; ARCGIS_GUIDE.md (env clone -> pip -> Add Toolbox). Enabler: decay wired through knn_to_rows/dispatch counts path (ND/TD/RD_inf now row-aligned, validated 1e-10). Book ch3-8-9 pack merged (12 chapters ride this release). 60 tests |
| 1.12.0 | kFCA both sides: `k_side` on fca/fca_segments ("supply" = everyone weighs k of supply mass, "demand" = every supply point weighs k of demand mass, "union" = legacy default, "intersection", "both" = parallel outputs A_ksupply/A_kdemand + J/R twins - USER NAMING, activity-agnostic); uncovered-supply coverage printed loudly; hand-computed side validation (0.6 vs 0.9, J 6 vs 9), both==singles at 1e-12, union default regression-locked; DIVERGENCE EXPERIMENT on the municipality: corr(A_ksupply, A_kdemand) = 0.329, median |divergence| 0.291 - the convention IS half the finding (cookbook_08 + figure); Book ch5-7 pack merged (9 chapters compiled). 58 tests |
| 1.11.0 | The Voice release: all five Book chapters rewritten to the binding beginner register (style guide honoured - structure and imagery untouched, prose ~doubled, every term earns its meaning before use); ch16 (Stata) written in the new voice; dispatcher gains engine="lisa" (cell-mean LISA -> row-aligned LISA_<v>_Ii / _quad (1=HH 2=LL 3=HL 4=LH) / _p; loud cell-mean notice; validated vs direct local_morans at 1e-9); equipop_run.ado extended (values() + wperm()); Book compiled: 6 chapters. 56 tests |
| 1.10.0 | Propensity FCA (#16): `fca_propensity` GROUP mode (M[g][c], rows loudly normalized to the search-allocation convention) and CELL mode (per-cell propensity fields, estimator (f)); identity-M == fca_segments at 1e-12 (the free regression), hand-computed cross-competition known answer, cell==group under uniform propensities (pytest x3); municipality scenario: A_low 0.154 (walls) -> 0.301 under illustrative 15/25% cross-search (+95% - "the matrix is the model"); Book ch. 13 written + cookbook_05 figure from the register fixture; Book compiled per release convention |
| 1.9.1 | The Book compiles EVERY RELEASE (#19 convention): chapter 11 written (autocorrelation, incl. the warning in full); docs/book/build.sh (figures -> compile, one command); CI gains a "book" job - every push regenerates all cookbook figures and attaches EquiPop_Book.docx as an Actions artifact, version-stamped from pyproject |
| 1.9.0 | Spatial autocorrelation (#14): `autocorr` module - `build_weights` (knn with ATOMIC tie ring / distance band / decay-weighted from the five families; row-standardised default; isolates reported), `morans_i` (analytic E[I], seeded permutation p), `local_morans` (LISA quadrants + conditional permutation, esda (n-1) moment convention documented), `getis_g` + `local_g` (Gi/Gi*), `autocorr_profile` (multiscalar I-by-k pattern); THE LOUD WARNING auto-fires on R_*_k-shaped columns (smoothed-surface caveat); cookbook_04 LISA figure (Book ch. 11). 52 tests |
| 1.8.1 | CI fix: pyarrow was missing from the test extra (bigrun's parquet tests failed on any clean environment - reproduced in a CI-identical venv, 2 ImportErrors); fix three-pronged: pyarrow AND rasterio added to test extras (CI now runs the full 47 incl. the DEM zonal test that had silently skipped since 1.2.0), importorskip guards so core-only installs skip gracefully (44+3s), bigrun raises a helpful "pip install pyarrow" instead of pandas' fastparquet confusion. Upstream watch-item: rasterio x NumPy 2.5 DeprecationWarning (not ours) |
| 1.7.0 | Continental scale (#18a): `origins=` on the fast engine (global tree, subset origins - per-origin results EXACT vs full run); `bigrun` module - `run_knn_counts_tiled` (spatial origin tiles -> per-tile parquet float32, progressive manifest.json with md5s, resume=True continues crashed runs) + `load_tiled` (md5-verified, column-selective). No halos needed at this scale: tree and destination mass stay global, so tiled == untiled by construction. Demo: 250k origins / 171 s / 1.53 GB peak RSS -> ~2 h for the user's 16M-coordinate scale. 45 tests |
| 1.6.0 | The dispatcher (#17): `stata_bridge.dispatch(engine, ...)` - ONE row-alignment layer exposing counts / stats / friction / slope / fca to Stata; `stata/equipop_run.ado` single command with per-engine options (fca: demand = rows in memory, supply from file, returns A + J regression-ready); shared `_snap`/`_map_back` helpers; ado python block sfi-stub-validated verbatim (counts/stats/fca), slope path pytest-covered incl. flat-DEM==friction THROUGH the bridge; FUNCTION_MATRIX.md enters repo docs/ (SB row now spans five engines); 42 tests |
| 1.5.1 | Real-data act for #11 (Swedish municipality register, RT90): jobs outside residential bbox dropped per data owner (998 rows / 3,118 out-of-town jobs); fca gains J column (step-1 potential; J/A = effective decayed competitor mass); fca_segments propagates J_<name>; anonymised two-file fixture (joint isometry, PRE-FILTERED before transform - axis-aligned bboxes are not isometry-invariant, learned loudly) + checkpoint regression test; 38 tests |
| 1.5.0 | FCA family (#11): `fca` module - reach modes from the neighbourhood menu (decay-unbounded / r-catchment / kFCA fixed-mass catchments with atomic-tie inclusion / EFFORT via slope engine incl. round-trip, decay in ROUNDS - loud); methods 2SFCA and 3SFCA (Wan selection weights); optional doubly-constrained Wilson balancing (`balance=n`) with supply-margin scaling for imbalanced markets (loud) and GAUGE FIXING of the (a,b) factor scale (demand-weighted mean A = global S/D, supply-weighted mean C = 1 - flows invariant); match-table segmentation orchestrator `fca_segments` (per-segment overrides win); orphan/starved cells get 0 loudly, never NaN-hidden. Also: gamma-decay manual figure + reproducible script (cookbook entry 01); joint-isometry anonymiser for two-file systems (examples/make_synthetic_jobs_people.py, self-checking). 37 tests |
| 1.4.0 | The Access release: round-trip slope effort (#4a-RT: `roundtrip=True`, forward+transpose Dijkstra, PER-LEG AVERAGE so flat == one-way exactly; the return path may differ from outbound - correct); gamma-parameterised shifted power decay (`Decay(model="power", half_life_m=h, gamma=g)`: w=(1+(2^(1/g)-1)d/h)^(-g), EXACT half-life for any tail; legacy +1m form kept when gamma=None); access module (#15): `potential_surface` (Hansen potential for EVERY domain midpoint via FFT convolution - exact on the grid, eps-truncated kernel, doubles as new-POI surplus with population as mass, NO iterations), `opportunity_horizon` (analytic negexp h/ln2 and shifted-power h/((2^(1/g)-1)(g-1)) for g>1, INFINITE for g<=1 - loud; refined numeric otherwise), `effort_potential` (potential over slope/friction effort, optionally round-trip; decay half-life in ROUNDS, stated loudly); 31 tests |
| 1.3.0 | Neighbourhood definition menu (#12): metric radii `r_values` in fast + stats engines (N_r500 naming, cells within r included wholly - ties vanish by construction); effort isochrones `tau_values` in friction + slope engines (N_tau8, real-valued tau under slope); unbounded decayed sums in fast engine (`decay=` -> ND_inf/TD/RD_inf, eps-truncation with bisection-derived radius, analytic match verified); AREA family `area_stats` (per-area N/T/R + value statistics via the registries, weights for N/T/R, NO Dist/Rounds - honestly absent); seg_profile accepts r/tau labels; Stata bridge + ado gain r(); 25 tests |
| 1.2.0 | Slope-asymmetric directional friction (#4a): `slope` module - `SLOPE_MODELS` dict (tobler/linear, penalty(0)=1 enforced), `dem_to_cell_altitude` (zonal-mean DEM sampling, sea-clip, coverage warnings), `SlopeGrid` (directed edge costs `penalty(slope)+friction(dst)`, slope over true centre distance u / u*sqrt(2)), `run_knn_slope` (same output contract + real-valued `Rounds_k` = flat-equivalent effort); `origins=` subset option on both graph engines (#11 substrate); friction indexer robust to float coordinates (latent bug fixed); 18 tests |
| 1.1.0 | Stata integration (Round C part 1): `equipop.stata_bridge.knn_to_rows` - row-aligned disaggregated results for individual-level data, missing-coordinate-safe, engine-identical (pytest-covered); `stata/equipop_knn.ado` (Stata 17+, thin sfi glue) + example.do + README_STATA + test .dta; tolerance-based tie detection (1e-6 m) unified across engines after a cross-engine ulp-level tie discrepancy was caught by the bridge test |
| 1.0.0 | First public release: repository https://github.com/GeoJohnSwe/EquiPop, PyPI name `equipop` claimed; version stamped across pyproject/package/CITATION; wheel + sdist built and install-verified |
| 0.9.0 | Round B: GitHub-ready repository under the name **EquiPop** (pyproject with optional extras, MIT license + citation request, CITATION.cff with ORCID and the five reference works, README with C#/R/Python lineage, CI workflow, examples); pytest suite - 11 tests, synthetic fixtures for engines/decay/hex/stats/segregation plus Berlin regression and the anonymized individual dataset; PopMuniTest anonymized to `synthetic_individuals.csv` via isometric transform (reflection + translation; pairwise distances and all k-NN results proven multiset-identical), variables renamed ValFloat/ValCount; topic-based beginner manual (MANUAL_TOPICS.md); CORRECTION: the Berlin tie deviation is 6 cells (2 per k-level), not 2 as earlier noted |
| 1.14.0 | ArcGIS toolbox #21b - the field-tested release (every feature from John's maiden runs): honest Tool-1 labels (Population field / Group count fields, both data shapes taught), "no decay" DEFAULT with half-life box self-disabling (updateParameters), generic Tool 2/3 titles, re-run handling (Overwrite loudly / Stop) + NEW-feature-class output (CopyFeatures, input pristine), CATEGORY MODE (fclass -> population filter + grouped treatments, "food: restaurant, cafe"; excluded rows Null; zero-match warning), Dist_k=metres explanation printed, package-level `categorical` factory (Stata inherits later) + LOUD counts-without-population hint in knn_to_rows; stub grew ListFields/DeleteField/CopyFeatures + text-field fidelity; guide gains the field-tested troubleshooting ladder (exec_prefix, the Roaming stowaway, PYTHONNOUSERSITE). 63 tests |
| 1.13.0 | ArcGIS Pro toolbox (#21, department priority): `arcgis/EquiPop.pyt` - three tools (Counts & Shares w/ k, r, groups, weights AND decay; Value Statistics incl. income median/Gini; Friction Effort w/ barrier csv + tau) over ONE shared glue path; glue-only discipline (all math in the pip package), stub-arcpy VERBATIM validation incl. Null propagation and a decayed-sum cross-check vs dispatch; shapefile 10-char warning; ARCGIS_GUIDE.md (env clone -> pip -> Add Toolbox). Enabler: decay wired through knn_to_rows/dispatch counts path (ND/TD/RD_inf now row-aligned, validated 1e-10). Book ch3-8-9 pack merged (12 chapters ride this release). 60 tests |
| 1.12.0 | kFCA both sides: `k_side` on fca/fca_segments ("supply" = everyone weighs k of supply mass, "demand" = every supply point weighs k of demand mass, "union" = legacy default, "intersection", "both" = parallel outputs A_ksupply/A_kdemand + J/R twins - USER NAMING, activity-agnostic); uncovered-supply coverage printed loudly; hand-computed side validation (0.6 vs 0.9, J 6 vs 9), both==singles at 1e-12, union default regression-locked; DIVERGENCE EXPERIMENT on the municipality: corr(A_ksupply, A_kdemand) = 0.329, median |divergence| 0.291 - the convention IS half the finding (cookbook_08 + figure); Book ch5-7 pack merged (9 chapters compiled). 58 tests |
| 1.11.0 | The Voice release: all five Book chapters rewritten to the binding beginner register (style guide honoured - structure and imagery untouched, prose ~doubled, every term earns its meaning before use); ch16 (Stata) written in the new voice; dispatcher gains engine="lisa" (cell-mean LISA -> row-aligned LISA_<v>_Ii / _quad (1=HH 2=LL 3=HL 4=LH) / _p; loud cell-mean notice; validated vs direct local_morans at 1e-9); equipop_run.ado extended (values() + wperm()); Book compiled: 6 chapters. 56 tests |
| 1.10.0 | Propensity FCA (#16): `fca_propensity` GROUP mode (M[g][c], rows loudly normalized to the search-allocation convention) and CELL mode (per-cell propensity fields, estimator (f)); identity-M == fca_segments at 1e-12 (the free regression), hand-computed cross-competition known answer, cell==group under uniform propensities (pytest x3); municipality scenario: A_low 0.154 (walls) -> 0.301 under illustrative 15/25% cross-search (+95% - "the matrix is the model"); Book ch. 13 written + cookbook_05 figure from the register fixture; Book compiled per release convention |
| 1.9.1 | The Book compiles EVERY RELEASE (#19 convention): chapter 11 written (autocorrelation, incl. the warning in full); docs/book/build.sh (figures -> compile, one command); CI gains a "book" job - every push regenerates all cookbook figures and attaches EquiPop_Book.docx as an Actions artifact, version-stamped from pyproject |
| 1.9.0 | Spatial autocorrelation (#14): `autocorr` module - `build_weights` (knn with ATOMIC tie ring / distance band / decay-weighted from the five families; row-standardised default; isolates reported), `morans_i` (analytic E[I], seeded permutation p), `local_morans` (LISA quadrants + conditional permutation, esda (n-1) moment convention documented), `getis_g` + `local_g` (Gi/Gi*), `autocorr_profile` (multiscalar I-by-k pattern); THE LOUD WARNING auto-fires on R_*_k-shaped columns (smoothed-surface caveat); cookbook_04 LISA figure (Book ch. 11). 52 tests |
| 1.8.1 | CI fix: pyarrow was missing from the test extra (bigrun's parquet tests failed on any clean environment - reproduced in a CI-identical venv, 2 ImportErrors); fix three-pronged: pyarrow AND rasterio added to test extras (CI now runs the full 47 incl. the DEM zonal test that had silently skipped since 1.2.0), importorskip guards so core-only installs skip gracefully (44+3s), bigrun raises a helpful "pip install pyarrow" instead of pandas' fastparquet confusion. Upstream watch-item: rasterio x NumPy 2.5 DeprecationWarning (not ours) |
| 1.7.0 | Continental scale (#18a): `origins=` on the fast engine (global tree, subset origins - per-origin results EXACT vs full run); `bigrun` module - `run_knn_counts_tiled` (spatial origin tiles -> per-tile parquet float32, progressive manifest.json with md5s, resume=True continues crashed runs) + `load_tiled` (md5-verified, column-selective). No halos needed at this scale: tree and destination mass stay global, so tiled == untiled by construction. Demo: 250k origins / 171 s / 1.53 GB peak RSS -> ~2 h for the user's 16M-coordinate scale. 45 tests |
| 1.6.0 | The dispatcher (#17): `stata_bridge.dispatch(engine, ...)` - ONE row-alignment layer exposing counts / stats / friction / slope / fca to Stata; `stata/equipop_run.ado` single command with per-engine options (fca: demand = rows in memory, supply from file, returns A + J regression-ready); shared `_snap`/`_map_back` helpers; ado python block sfi-stub-validated verbatim (counts/stats/fca), slope path pytest-covered incl. flat-DEM==friction THROUGH the bridge; FUNCTION_MATRIX.md enters repo docs/ (SB row now spans five engines); 42 tests |
| 1.5.1 | Real-data act for #11 (Swedish municipality register, RT90): jobs outside residential bbox dropped per data owner (998 rows / 3,118 out-of-town jobs); fca gains J column (step-1 potential; J/A = effective decayed competitor mass); fca_segments propagates J_<name>; anonymised two-file fixture (joint isometry, PRE-FILTERED before transform - axis-aligned bboxes are not isometry-invariant, learned loudly) + checkpoint regression test; 38 tests |
| 1.5.0 | FCA family (#11): `fca` module - reach modes from the neighbourhood menu (decay-unbounded / r-catchment / kFCA fixed-mass catchments with atomic-tie inclusion / EFFORT via slope engine incl. round-trip, decay in ROUNDS - loud); methods 2SFCA and 3SFCA (Wan selection weights); optional doubly-constrained Wilson balancing (`balance=n`) with supply-margin scaling for imbalanced markets (loud) and GAUGE FIXING of the (a,b) factor scale (demand-weighted mean A = global S/D, supply-weighted mean C = 1 - flows invariant); match-table segmentation orchestrator `fca_segments` (per-segment overrides win); orphan/starved cells get 0 loudly, never NaN-hidden. Also: gamma-decay manual figure + reproducible script (cookbook entry 01); joint-isometry anonymiser for two-file systems (examples/make_synthetic_jobs_people.py, self-checking). 37 tests |
| 1.4.0 | The Access release: round-trip slope effort (#4a-RT: `roundtrip=True`, forward+transpose Dijkstra, PER-LEG AVERAGE so flat == one-way exactly; the return path may differ from outbound - correct); gamma-parameterised shifted power decay (`Decay(model="power", half_life_m=h, gamma=g)`: w=(1+(2^(1/g)-1)d/h)^(-g), EXACT half-life for any tail; legacy +1m form kept when gamma=None); access module (#15): `potential_surface` (Hansen potential for EVERY domain midpoint via FFT convolution - exact on the grid, eps-truncated kernel, doubles as new-POI surplus with population as mass, NO iterations), `opportunity_horizon` (analytic negexp h/ln2 and shifted-power h/((2^(1/g)-1)(g-1)) for g>1, INFINITE for g<=1 - loud; refined numeric otherwise), `effort_potential` (potential over slope/friction effort, optionally round-trip; decay half-life in ROUNDS, stated loudly); 31 tests |
| 1.3.0 | Neighbourhood definition menu (#12): metric radii `r_values` in fast + stats engines (N_r500 naming, cells within r included wholly - ties vanish by construction); effort isochrones `tau_values` in friction + slope engines (N_tau8, real-valued tau under slope); unbounded decayed sums in fast engine (`decay=` -> ND_inf/TD/RD_inf, eps-truncation with bisection-derived radius, analytic match verified); AREA family `area_stats` (per-area N/T/R + value statistics via the registries, weights for N/T/R, NO Dist/Rounds - honestly absent); seg_profile accepts r/tau labels; Stata bridge + ado gain r(); 25 tests |
| 1.2.0 | Slope-asymmetric directional friction (#4a): `slope` module - `SLOPE_MODELS` dict (tobler/linear, penalty(0)=1 enforced), `dem_to_cell_altitude` (zonal-mean DEM sampling, sea-clip, coverage warnings), `SlopeGrid` (directed edge costs `penalty(slope)+friction(dst)`, slope over true centre distance u / u*sqrt(2)), `run_knn_slope` (same output contract + real-valued `Rounds_k` = flat-equivalent effort); `origins=` subset option on both graph engines (#11 substrate); friction indexer robust to float coordinates (latent bug fixed); 18 tests |
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

### Validation record - v1.2.0 (slope, #4a)
- Flat-DEM regression: `run_knn_slope` == `run_knn_friction` exactly, all models (pytest).
- Ramp invariants: uphill effort > flat; Tobler gentle-descent < flat (the -5% optimum, penalty 0.839); linear lambda_down=0 descent == flat (pytest).
- Known answer: 3-cell 10%-ramp efforts hand-computed, match to 1e-9 (pytest).
- Zonal DEM sampling: synthetic GeoTIFF constant blocks reproduced exactly (pytest).
- Malta real data (Copernicus DEM ~17 m px / GLO-90 effective, EPSG:32633; WorldPop 2020, 514,526 pop, 18.48% 65+ matching v0.5): 2,500-origin subsample vs flat FARB and radial. R_k correlations 0.994-0.996 (composition nearly slope-invariant on Malta); effort stretch mean 1.05-1.06, p95 1.23-1.38, max 2.35 (k=100), declining with k. Asymmetry finding: lowest-altitude quartile stretch 1.093 vs highest 1.031 - the "valley tax": communities below scarps pay, plateau dwellers descend at flat-or-cheaper Tobler prices. Max edge cost 86.9 located on the Dingli cliff belt (~128% grade), as expected.

### Design decisions - v1.2.0
- Slope cost is a MULTIPLIER on the move (penalty(0)=1 enforced at model registration), friction stays an ADDITIVE destination-node term: cost(i->j) = penalty(s_ij) + friction(j). Rounds remain "flat-equivalent effort"; flat DEM regresses to plain FARB exactly.
- Slope computed over TRUE centre distance (u orthogonal, u*sqrt(2) diagonal).
- Rounds under slope are real-valued; tie convention unchanged (equal effort = one atomic ring, exact float equality - symmetric constructions still tie).
- DEM sampling = zonal mean of pixel centres per cell; negative altitude (sea noise) clipped to 0; cells outside DEM coverage filled 0 with loud count.
- `origins=` computes results for an origin subset with COMPLETE destination mass (exact per-origin results; substrate for #11 kFCA).
- Hexagonal slope inherits later with the parked 6-neighbour friction graph (recorded, not built).

### Validation record - v1.3.0 (#12 menu)
- Radius: fast engine vs brute force, three radii incl. whole-world (= global totals) - exact (pytest). Stats engine N/R equal fast engine; within-radius mean equals brute concatenation (pytest).
- Tau: flat friction reproduces the Chebyshev ball exactly - centre 9/25 cells at tau 1/2, corner clipped 4/9 (pytest).
- Decayed sum: ND_inf/TD_inf equal the exact all-pairs sums at rtol 1e-9 (negexp h=500, eps=1e-9) (pytest).
- Area: hand-computed two-area fixture incl. weighted N/T/R, unweighted Mean/Med, NaN-area exclusion, absence of Dist/Rounds columns (pytest).
- Bridge: r_values row-aligned, self-inclusion invariant N_r >= 1 (pytest). seg_profile runs over mixed k and r labels (pytest).

### Design decisions - v1.3.0
- The teaching triad is explicit: k fixes POPULATION, r fixes GEOMETRY, area fixes ADMINISTRATION. All statistics transfer across the triad; Dist_/Rounds_ exist only where a search expands (k), and are honestly absent for r (r IS the distance), tau (tau IS the effort) and area.
- Naming: N_r500 / N_tau8 (compact %g labels; N_50 stays k). ND_inf marks the unbounded decayed sum.
- Radius/tau semantics are INCLUSIVE (dist <= r, effort <= tau); no tie problem exists in these modes since qualifying cells are included wholly.
- Decayed sums truncate where weight < eps (default 1e-6), radius found by bisection per model, printed; neglected tail below eps per unit mass.
- area_stats: weight applies to N and binary T/R; value statistics are row-unweighted with a loud docstring note (weighted quantiles PARKED). Unassigned rows excluded loudly (Stockholm 9,033 precedent).
- Ring engine did NOT get r_values: for radial counts/stats it is mathematically identical to the stats engine (documented equivalence), so the addition would be redundant; recorded, not hidden.

### Validation record - v1.4.0 (Access release)
- Round-trip: flat DEM RT == one-way EXACTLY (symmetry, pytest); 3-cell 10% ramp known answer e^0.35+1 per leg to 1e-9, west==east RT symmetry, RT>flat convexity, linear per-leg 1+lu*s/2 (pytest).
- Gamma power: w(h)=0.5 exactly for gamma 0.5/1/2/5, gamma=1 == 1/(1+d/h), legacy +1m values reproduced (pytest).
- potential_surface: FFT vs brute-force all-pairs at 25 random midpoints, rtol 1e-9 (pytest). opportunity_horizon: negexp analytic; gamma=2 analytic 1/s; gamma=0.5 infinite; expsqrt numeric vs fine brute (pytest).
- effort_potential: flat-DEM roundtrip == Chebyshev-rounds brute at every origin, rtol 1e-9 (pytest).
- Malta headline: two FULL-ISLAND FFT surfaces (1.3M midpoints each) in 1.4 s; optimal next-POI location = E453250/N3972450 (Birkirkara-Msida conurbation, 136,799 decayed persons); round-trip Tobler access on 2,000 origins: terrain access tax mean 2.6%, p95 7.4%, max 15.9% - MILDER than the k-frontier stretch (v1.2.0), i.e. hills tax the FRONTIER more than the CORE (access sums are dominated by near, same-plateau mass); "coming home" penalty mean 1.0% but p95 6.9% - concentrated on steep-flank origins where out and back genuinely differ.

### Design decisions - v1.4.0
- RT effort is reported PER LEG (sum/2): flat regresses exactly, rounds stay comparable; cheapest return may take a different route (correct, free).
- Decay convexity does the round-trip physics: p(s)+p(-s) >= 2p(0) for both models - no extra machinery.
- Gamma power: one parameter for the tail (gamma), one for the scale (half-life) - separated at last; legacy form stays default for reproducibility.
- FFT potential is EXACT on the grid (kernel offsets ARE the midpoint distances); the only cutoff is the eps kernel truncation (printed).
- effort_potential decay operates in ROUNDS; competition effects are out of scope by design (FCA family, #11); greedy sequential placement (submodular, 1-1/e) PARKED as a helper.
- Opportunity horizon undefined (infinite) for power tails gamma<=1 - reported loudly, never silently clipped.

### Validation record - v1.5.0 (#11 FCA)
- 2SFCA hand-computed 3x2 known answer: R = [5/30, 8/50], A = [1/6, 1/6+0.16, 0.16] exact (pytest).
- 3SFCA hand-computed selection weights: R = [0.25, 0.2], A = [0.25, 0.225, 0.2] exact (pytest).
- kFCA catchment mask incl. ATOMIC TIE (two workplaces at equal distance both enter) - hand truth table (pytest).
- Doubly-constrained: rebuilt flows reproduce both margins at rtol 1e-7 on an IMBALANCED market (S scaled internally); gauge convention verified exactly (pytest).
- Segmentation orchestrator == individual runs, column contract (pytest).
- Effort reach: flat DEM == Chebyshev-rounds brute at rtol 1e-9 (pytest).
- REAL-DATA ACT PENDING: jobs+workers .sav uploads did not reach the container this round - headline run and .sav-derived fixture queued for the re-upload (anonymiser ready and self-checked).

### Design decisions - v1.5.0
- kFCA catchments hold fixed OPPOSITE-side mass (homes gather k jobs, workplaces gather k people); union of the two directed catchments feeds W; equidistant cells enter wholly (tie convention carried over).
- Doubly-constrained flows need SUM(D)=SUM(S): the supply margin is scaled to the demand total INSIDE the flow model only, loudly; reported A keeps unscaled jobs-per-worker units.
- Wilson factors (a,b) are identified only up to a scalar: gauge fixed by convention (demand-weighted mean A = global S/D; supply-weighted mean C = 1); flows are gauge-invariant, tested.
- Weight matrices are dense demand x supply (municipality scale); tile-and-flush for national scale stays parked.
- Anonymisation of multi-file systems uses ONE joint isometry so CROSS-file distances are exactly preserved (self-check enforced at write time).

### Validation record - v1.5.1 (real labour market)
- Market: 2,699 residential cells (24,268 pop; 11,343 working; 44.9% low-edu) vs 870 local job cells (7,142 jobs; 11.0% low-edu). Global jobs-per-worker 0.630 (commuter municipality); LOW segment 0.154.
- Conservation theorem confirmed in data: demand-weighted mean A == global S/D in EVERY method (2SFCA/3SFCA/kFCA/balanced) - methods differ in DISTRIBUTION only.
- Distribution (A_all, h=3 km): 2SFCA p90/p10 = 4.12; 3SFCA compresses to 3.00 (demand-splitting softens periphery); kFCA k=500 raises the floor (p10 0.191->0.298), corr with 2SFCA only 0.45 - fixed-mass catchments redraw the geography.
- The education gap: per-cell A_low/A_all median 0.241 (p10 0.227, p90 0.302) - the low-educated face about a QUARTER of general access everywhere in the municipality.
- Synthetic fixture reproduces the register run to the sixth decimal (isometry-proven); balanced model converged in 42/55 iterations on genuinely imbalanced margins (S/D 0.63 and 0.15).

### Design decisions - v1.5.1
- J (step-1 decayed supply) returned alongside A; J/A reads as effective decayed competitor mass (units: workers) - NOT a 0-1 share (corrected in-code).
- Anonymised fixtures for filtered analyses: FILTER FIRST, TRANSFORM SECOND (bbox rules are not isometry-invariant).
- Out-of-area supply handling is the data owner's call, executed loudly (rows and mass counted).

### Validation record - v1.6.0 (#17 dispatcher)
- dispatch(counts) == knn_to_rows exactly; stats row-alignment (cell-sharing rows share values, missing coords NaN); slope-flat == friction THROUGH the dispatcher (incl. roundtrip, tau); fca == direct cell run at rtol 1e-12 with supply read from file (pytest x4).
- equipop_run.ado python block executed VERBATIM under the sfi stub for counts, stats and fca paths (15 variables stored, missing-coordinate rows NaN as promised). In-Stata maiden run pending user-side, as per discipline.

### Design decisions - v1.6.0
- One dispatcher, not one ado per engine: the row-alignment layer (snap -> aggregate -> engine -> map back) is the SHARED contract; engines plug into it.
- fca from Stata: demand = the dataset in memory, supply = a FILE path (csv/dta/sav via io.read_table) - matches how Stata users actually hold two-table problems.
- Variable-name safety: dots in labels become underscores at the Stata boundary.

### Validation record - v1.7.0 (#18a)
- origins= subset == full-run rows exactly (pytest).
- GOLDEN: tiled == untiled across N/T/R/Dist/N_r/ND_inf/RD_inf at float32 packaging tolerance (pytest).
- Resume: deleted tile + manifest entry self-repairs; md5 verification on load (pytest).
- Scale demo: 250,000 origins, k=100, 12 tiles: 171 s, 1,465 origins/s, peak RSS 1.53 GB; extrapolation ~1.9 h for ~10M cells (16M coordinates) - within the user's a-day-is-fine budget with bounded memory.

### Design decisions - v1.7.0
- At <= ~50M cells the tree stays GLOBAL and only origins tile: exactness by construction, no halos, no seams. Domain tiling with density-estimated halos + straggler guarantee remains the >100M-cell escalation (#18b-e parked: graph-engine corridor subgraphs, overlap-add FFT tiles, fca supply tiling, mmap inputs).
- float32 on DISK only (engine computes float64); manifest records params + per-tile md5; progressive writes make three-day runs resumable and auditable.

### Validation record - v1.9.0 (#14)
- Cross-validated against PySAL esda 2.10: global I within 5e-3 of esda-KNN (difference = our atomic tie ring vs strict-k, documented), local Ii allclose 1e-9 after adopting esda's (n-1) moment (diagnosed as an EXACT n/(n-1) ratio), Gi* z-scores allclose 1e-8 (pytest x3, importorskip-guarded).
- Known answers: checkerboard on rook weights I < -0.5; gradient I > 0.8; noise |I| < 0.1 with insignificant p (pytest).
- Gridby: profile I(R_g_k) = 0.947 -> 0.995 -> 0.998 for k = 50/400/1600 - the smoothing theorem drawn; smell warning pytest-enforced; LISA map shows HH east / LL west split at the planted gradient, river visible in the cluster edge.

### Design decisions - v1.9.0
- Weights are born from the neighbourhood menu; knn mode keeps the atomic-tie convention (documented as the source of tiny I differences vs strict-k libraries).
- Local Moran moment uses (n-1) to match esda exactly - cross-library comparability beats internal aesthetics.
- Non-finite values: mean-imputed for global I WITH a loud count; isolates yield NaN locals, never silent zeros.
- The smoothed-surface warning is automatic on R_*-shaped names - legitimate use, mandatory awareness.

### Validation record - v1.10.0 (#16)
- Identity M reproduces fca_segments exactly (rtol 1e-12) - groups==categories regression.
- Hand-computed 1x2x2 cross-competition: pressures 10/20, R .6/.6, A .6/.6, J 7.2/11.4 - exact.
- CELL mode == GROUP mode under uniform propensities (rtol 1e-12).
- Municipality act: walls A_low = 0.1541; illustrative M [[.85,.15],[.25,.75]] -> 0.3007 (+95.1%) - scenario labeled as such; ch13 figure maps where the gain lands.

### Design decisions - v1.10.0
- Rows of M = search allocation, sum to 1 (loud normalization); optional intensity scalars only with evidence (recorded, not built).
- Estimator guidance shipped in ch13: (c) per-category regressions with AREA EFFECTS STRIPPED (geography belongs to the FCA - double-count warning), row-normalized; (f) per-cell propensity fields via cell_propensity=True.
- Cross-tab baseline documented as realized-allocation, not search intent.
- kFCA continuation (user request): run BOTH sides (fixed k on jobs AND on residences) as parallel outputs - recorded for the k_side parametrization round.

### Validation record - v1.12.0 (kFCA both sides)
- Brute force: 1 home (D=10), 3 supplies (S=3 at 100/200/300 m), k=5: supply-side catchment = 2 nearest -> A=0.6, J=6; demand-side links all 3 -> A=0.9, J=9. Exact.
- both == separate single-side runs at rtol 1e-12; k_side omitted == "union" (legacy protected).
- Municipality (all segment, k=500): corr 0.329 between conventions; wmeans 0.624/0.630 (conservation over covered supply); median |A_kd - A_ks| = 0.291, p90 = 0.736. The divergence map is a candidate publication figure.

### Design decisions - v1.12.0
- Column naming per user: A_ksupply / A_kdemand (mass-anchored, activity-agnostic - works for jobs, GPs, school places alike).
- Uncovered supply (in nobody's catchment) drops out with a LOUD count; conservation is stated over covered mass only.
- k_side="both" is a convenience wrapper over two verified single-side runs - no third code path to validate.

### Validation record - v1.13.0 (#21)
- dispatch("counts", half_life_m=...) decayed sums == direct run_knn_counts at 1e-10 through the full row path (pytest).
- EquiPop.pyt _run_tool executed VERBATIM under fake arcpy (Describe / FeatureClassToNumPyArray / ExtendTable): counts+decay, stats (Med/Gini income), friction (Rounds, N_tau3) all append correctly; missing coordinates -> Null; ND_inf equals dispatch reference exactly. In-Pro maiden run = user-side, per discipline.

### Design decisions - v1.13.0
- One _run_tool glue path for all tools: single stub-tested surface, tools are parameter forms.
- arcpy surface minimized to three da calls (numpy in, numpy out, ExtendTable join) - no cursors.
- Point layers only, loud; shapefiles warned toward gdb; Pro/Py3 only (user decision).

### Validation record - v1.14.0 (#21b)
- Category mode verbatim under fake arcpy: population filter (school rows -> Null everywhere), grouped treatment R_food_20, T <= N sanity holds.
- Re-run with identical parameters: Overwrite path deletes and re-extends, loud message, no TypeError (the field-test bug, now regression-locked).
- New-feature-class mode: input table PRISTINE, copy carries all result fields.
- counts-without-population HINT fires on count-like group values (pytest, capsys).
- categorical parse: grouped syntax, zero-match warning (pytest).

### Design decisions - v1.14.0
- Field observations answered in-product: Dist_k explained at runtime (metres BY DESIGN); the T>N confusion detected and hinted automatically - dialogs must be loud-by-design too.
- Category treatments never use selections (no override problem exists); population may come from filter OR the active map selection (arcpy honours it for free).
- New-output = CopyFeatures then extend the copy: GIS-native, input untouched.
