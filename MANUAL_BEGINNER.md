# EquiPop 1.5 — The Beginner's Manual

*A complete, gentle guide to using EquiPop with no prior Python
experience beyond copy-pasting. Every section stands alone and every
code block runs as-is once you adapt the file names. For the research
background, see the README and the five references in CITATION.cff.*

---

## 0. What EquiPop does, in one paragraph

For every person (or place) in your data, EquiPop looks outward and
finds their **k nearest neighbours** — the 100, or 1,600, or 25,600
people who live closest — and then describes that personal,
"egocentric" neighbourhood: how many belong to some group, their mean
income, the distance or *effort* needed to reach them. Because every
person gets their own neighbourhood at every scale k, you escape the
arbitrariness of administrative areas, and segregation, accessibility
and context effects become **multiscalar**: measured across a whole
range of neighbourhood sizes rather than at one frozen level.

## 1. Installing

You need Python 3.11 or newer (the free **Anaconda** distribution is
the easiest way to get it). Then, in a terminal / Anaconda Prompt:

```
pip install equipop
```

That gives you the core. Some features need optional extras — install
only what you use:

| You want to… | Also install |
|---|---|
| Read shapefiles / GeoPackage / OSM `.pbf` | `pip install geopandas pyogrio` |
| Read rasters (WorldPop, DEMs) | `pip install rasterio` |
| Read SPSS `.sav` | `pip install pyreadstat` |
| Read Excel `.xlsx` | `pip install openpyxl` |
| Maps with jenks class breaks | `pip install matplotlib jenkspy` |

Everything below assumes you work in a Python script, a Jupyter
notebook, or Spyder — anywhere you can run Python code.

## 2. What your data must look like

EquiPop wants, at minimum, **coordinates**. Three shapes of in-data
are accepted:

**A. Individual rows** — one row per person/POI, possibly sharing
coordinates (a whole building on one point is fine):

```
ID;X;Y;HighEdu;Income
1;6580342;1628490;1;312000
2;6580342;1628490;0;198000
```

**B. Aggregated cells** — one row per grid cell with counts:

```
x;y;count_all;count_group
1628450;6580350;14;3
```

**C. Rasters** — population GeoTIFFs (e.g. WorldPop): see §7.

Coordinates must end up **metric** (metres, not degrees). If your data
is in longitude/latitude, EquiPop projects it for you and even
suggests a suitable projection (§4). Separator and encoding of text
files are sniffed automatically (§3).

## 3. Reading data: the io module

```python
from equipop.io import read_table
df = read_table("mydata.csv")          # sniffs ; , tab, BOM, etc.
df = read_table("mydata.sav")          # SPSS
df = read_table("mydata.xlsx")         # Excel
df = read_table("pois.gpkg", layer="points")   # GIS formats
df = read_table("region.zip")          # zipped shapefile — just works
```

Not sure what's inside a GIS file?

```python
from equipop.io import list_layers
print(list_layers("osm/malta.gpkg"))
```

## 4. Projection and grid snapping

```python
from equipop import project_to_metric, snap_to_grid

df = project_to_metric(df, lat_col="lat", lon_col="lon")
# no EPSG given → EquiPop SUGGESTS one (e.g. UTM zone) and tells you.
# Or be explicit: project_to_metric(df, target_epsg=3006)  # SWEREF99TM

df = snap_to_grid(df, unit_size=100)   # 100 m cells; adds E_grid, N_grid
```

Snapping places every point into a square cell and works with the
cell **midpoint** from then on. `unit_size` is your resolution dial —
100 m is the register-data classic; anything consistent works.

## 5. The basic run: counts and ratios (fast engine)

Individual-level data, one line each for the cell build and the run:

```python
from equipop.cells import build_cells
from equipop.fastcounts import run_knn_counts

cd  = build_cells(df, "E_grid", "N_grid",
                  binary_vars=["HighEdu"], unit_size=100)
res = run_knn_counts(cd, k_values=[100, 400, 1600, 6400])
res.to_csv("my_contexts.csv", index=False)
```

You get one row per populated cell with, for every k:

| Column | Meaning |
|---|---|
| `N_k` | persons actually counted (≥ k — whole cells are added at once) |
| `T_HighEdu_k` | of whom in the group |
| `R_HighEdu_k` | the ratio T/N — the individualised context share |
| `Dist_k` | metres needed to reach k |

Missing coordinates are dropped **with a warning**; unreached k gives
partial results, never nothing; everything loud, nothing silent.


## 5b. NEW in 1.3 - the neighbourhood definition menu: k, radius, effort, area

k is one way to draw a neighbourhood; EquiPop 1.3 gives you the whole
menu, and they compose freely in one run:

```python
res = run_knn_counts(cd, k_values=[400], r_values=[500, 2000])
# adds N_r500, T_HighEdu_r500, R_HighEdu_r500 ... alongside the k columns
```

- **k** fixes the POPULATION (400 people, wherever they live),
- **r** fixes the GEOMETRY (everyone within 500 m, however many),
- **tau** fixes the EFFORT - on the friction and slope engines,
  `tau_values=[4, 8]` gives everyone reachable within 4 or 8
  flat-equivalent rounds (effort isochrones):

```python
res = run_knn_slope(pop, k_values=[], tau_values=[8],
                    altitude="dem.tif", model="tobler")
```

- **the unbounded decayed sum** drops the boundary entirely: every
  person in the data counts, weighted by distance decay -

```python
from equipop.decay import Decay
res = run_knn_counts(cd, decay=Decay(model="negexp", half_life_m=2000))
# adds ND_inf, TD_HighEdu_inf, RD_HighEdu_inf
```

- **area** fixes the ADMINISTRATION - classic per-municipality
  statistics from the same variable declarations:

```python
from equipop.area import area_stats
res = area_stats(df, area_col="Kommun",
                 binary_vars=["HighEdu"], value_vars=["Income"])
```

Note what is missing in each mode, on purpose: `Dist_` exists only
for k (for r, the distance IS r); `Rounds_` only for k on the graph
engines; area mode has neither - areas do not expand, so there is
nothing to measure. Columns are honestly absent, never faked.
One warning for radius users: N_r varies enormously across space -
that is the point (geometry fixed, population floating) - so ratios
R_*_r500 in sparse areas rest on few people. The Nv_/N_ columns
always show you the basis.

## 6. Value statistics: mean, median, Gini among the k nearest

For continuous variables (income, age, rent):

```python
from equipop.analysis import run_knn_stats

cd  = build_cells(df, "E_grid", "N_grid",
                  binary_vars=["HighEdu"], value_vars=["Income"],
                  unit_size=100)
res = run_knn_stats(cd, k_values=[400, 1600],
                    stats={"Income": ["mean", "sd", "median", "gini"],
                           "HighEdu": ["ratio"]})
```

New columns: `Mean_Income_k`, `Med_Income_k`, `Gini_Income_k`, plus
`Nv_Income_k` — how many of the k had a valid value (missing values
still count towards k, but not towards the statistic; you always see
the basis).

## 7. Rasters as in-data (WorldPop and friends)

```python
from equipop.raster import rasters_to_points
df = rasters_to_points({
    "pop": "malta/mlt_t_*_2020*.tif",                  # glob: summed
    "old": "malta/mlt_t_{65,70,75,80,85,90}_2020*.tif" # cohorts 65+
})
# → columns lon, lat, pop, old — continue exactly as in §4-§5
```

Fractional populations are fine; mass conservation is checked and
reported.

## 8. Distance decay: nearby neighbours matter more

```python
from equipop import run_knn          # the ring engine
from equipop.decay import Decay

res = run_knn(cells, k_values=[400], unit_size=100,
              decay=Decay(model="negexp", half_life_m=2000))
```

`half_life_m` is the researcher-friendly dial: the distance at which
a neighbour counts half. Five models exist — `negexp`, `expnormal`,
`expsqrt`, `lognormal`, `power` — all half-life-parameterised. Output
adds `ND_k`, `TD_k`, `RD_k` (decayed count/group/ratio). Convention:
k is defined by RAW counts; decayed values are recorded at that same
moment, so decayed ≤ raw always. (`cells` here is a per-cell frame
with columns `E_grid`, `N_grid`, `FullPop`, `Treatment` — see the
topic manual for the aggregation helper.)

## 9. Hexagons instead of squares

```python
from equipop.hex import build_hex_cells
cd = build_hex_cells(df, "easting_m", "northing_m", unit_size=100,
                     binary_vars=["HighEdu"])
```

Same engines, same outputs — the geometry is the only change. Compare
grid vs hex results and you have a MAUP experiment (we measured
correlations 0.86 → 0.97 rising with k on Malta POIs).

## 10. Friction: barriers bend neighbourhoods (FARB)

Water, motorways and fences make straight-line distance a lie.
The friction engine grows neighbourhoods in **rounds**; a cell with
friction f waits out f extra rounds:

```python
from equipop.friction import load_friction_table, run_knn_friction

fr  = load_friction_table("water_roads.txt", "X", "Y", "Friction")
res = run_knn_friction(pop, k_values=[400, 1600], fr=fr,
                       unit_size=100, default_friction=0)
```

`default_friction=0` means: the file lists BARRIERS, unlisted land is
free (set it high for the opposite convention). Output adds
`Rounds_k` — the effort at which k was reached, the friction analogue
of `Dist_k`. Malformed friction rows are fenced and shown; overlapping
layers sum; poor spatial coverage triggers a warning.

## 11. NEW in 1.2 — Slopes: terrain-aware, direction-asymmetric effort

Hills make some neighbours cheaper to reach than others — and,
crucially, **the cost differs by direction**: climbing to the plateau
is not the same as strolling down from it.

```python
from equipop.slope import run_knn_slope

res = run_knn_slope(pop, k_values=[100, 400, 1600],
                    altitude="my_dem.tif",      # a GeoTIFF DEM
                    model="tobler", unit_size=100)
```

That's the whole thing. What happens inside:

1. The DEM is sampled to your grid — the **mean of all DEM pixels in
   each cell** (your GIS "extract values", but zonal and robust).
   Sea-level noise is clipped; uncovered cells reported loudly.
   **The DEM must be in the same metric CRS as your coordinates.**
2. Every move between adjacent cells gets a directed cost:
   `penalty(slope)` — over the true centre distance, so diagonal
   moves are gentler — plus any friction you also loaded (`fr=` works
   here too: water barriers AND hills in one model).
3. Dijkstra finds the cheapest paths; `Rounds_k` now reads as
   **flat-equivalent effort** (real-valued).

Two slope models (add your own with one dict entry in
`SLOPE_MODELS`):

- `model="tobler"` — Tobler's hiking function as a time penalty.
  Asymmetric with the famous quirk: a gentle −5 % descent is
  *cheaper than flat* (penalty 0.839). Steep in both directions is
  expensive.
- `model="linear", lambda_up=5, lambda_down=0` — the transparent
  baseline: a 10 % climb costs 1.5 moves, descent is flat-priced.

Guarantees you can rely on: with a flat DEM the results are
**exactly** those of `run_knn_friction` (regression-tested), and
`penalty(0)=1` is enforced for every model, so rounds stay comparable
across studies. On Malta this engine found the "valley tax": people
below the scarps spend up to 2.4× the flat effort to assemble their
k=100 neighbourhood, while plateau dwellers descend at flat-or-better
prices.

Sampling altitudes for any other purpose is one call:

```python
from equipop.slope import dem_to_cell_altitude
alt = dem_to_cell_altitude("my_dem.tif", E=cells.E, N=cells.N,
                           unit_size=100)
```

Advanced: `origins=` (an array of row indices) computes results for a
subset of origins while keeping the complete destination mass — for
big runs, subsample validations, and accessibility workflows.

## 12. Segregation indices across scales

```python
from equipop.segregation import seg_profile
prof = seg_profile(res, k_values=[100, 400, 1600],
                   n_col="N_{k}", t_col="T_HighEdu_{k}",
                   local_all="N_local", local_grp="HighEdu_local")
```

Eight indices (D, Gini, entropy H, Atkinson, Isolation, Interaction,
Correlation V, SI) at every k plus the local level — the multiscalar
profile of Östh, Clark & Malmberg (2015). Validated against the
published Stockholm Table A4 (SI(100) = 0.2822 vs 0.287 published).

## 13. Area aggregation and maps

```python
from equipop.area import aggregate_output
areas = aggregate_output(res, polygons="Kommun.gpkg")   # sjoin, CRS-aware

from equipop.viz import map_output
map_output(res, column="R_HighEdu_400", classes="jenks",
           out="context_map.png")     # scale bar + north arrow included
```

Aggregation is the *individualised context summarised per area* — not
an areal recomputation (the 2015 fig. 1 logic).

## 14. The run log: your audit trail

Wrap any run in a `RunLog` and you get a JSON + txt sidecar with
input md5 hashes, environment versions, settings, warnings and column
definitions — written progressively, so even a crashed run leaves a
record. Months later, the sidecar answers "what CRS was that grid?"
(it has already saved this project once.)

## 15. Using EquiPop from Stata

Stata 17+ can call EquiPop directly — your data never leaves Stata's
memory; results come back as ordinary variables ready for `regress`.
See **STATA_GUIDE.md** for the command (`equipop_knn`), a full
showcase do-file, and recipes for decay, statistics, segregation and
slopes from within Stata.

## 16. When something looks wrong — the loud-by-design list

- *"dropping N rows with malformed/missing coordinates"* — shown, not
  hidden; check those rows.
- Coordinates look huge/tiny? Swedish registers mix RT90
  (east ≈ 1.2–1.9 M) and SWEREF99TM (east ≈ 250–950 k) — the ranges
  reveal the truth; also check corner-vs-midpoint conventions (mod 100).
- `N_k` a bit above k — by design: whole cells are added at once and
  the factual count is reported.
- Decayed values above raw — impossible by construction; if you think
  you see it, you're comparing different k columns.
- Slope run says "cells outside DEM coverage" — your DEM is smaller
  than the analysis extent, or in a different CRS than your grid.
  Fix the CRS first; that solves it nine times out of ten.

## 17. NEW in 1.4 - Access: potential surfaces, the opportunity horizon, and round trips

**Round-trip slopes.** Real journeys come home. Add `roundtrip=True`
to `run_knn_slope` (or `effort_potential`) and effort becomes the
cheapest out-AND-back journey, reported per leg - on flat ground
nothing changes, over hills the varied terrain costs more in both
models, automatically.

**A better power decay.** `Decay(model="power", half_life_m=2000,
gamma=1)` gives w = 1/(1+d/h): exact half-life AND a tail you choose
(bigger gamma = thinner tail). The old power form still works.

**Access potential.** How much opportunity can you reach, decayed?

```python
from equipop.access import potential_surface, opportunity_horizon
from equipop.decay import Decay

dec = Decay(model="negexp", half_life_m=2000)
surf = potential_surface(poi_cells, dec, unit_size=100)
# -> A(x) for EVERY midpoint on the island, in seconds (FFT), exact.
print(opportunity_horizon(dec))   # the distance most access comes from
```

Swap the mass: pass POPULATION instead of POIs and the same surface
answers "how many (decayed) persons would a NEW opportunity at x
reach?" - the placement-surplus map, no iterations, one call.

**Access over effort.** Replace metres with hills:

```python
from equipop.access import effort_potential
A = effort_potential(pop_cells, poi_cells,
                     Decay(model="negexp", half_life_m=20),  # 20 ROUNDS
                     altitude="dem.tif", model="tobler", roundtrip=True)
```

Note the half-life is now in effort rounds (flat-equivalent moves),
not metres - the run says so loudly. On Malta this showed hills tax
the FRONTIER of your neighbourhood more than the CORE of your access,
and that the price of coming home falls on the steep-flank dwellers.

## 18. NEW in 1.5 - jobs, doctors, and the competition for them (FCA)

Access potential (section 17) asks "how much can I reach?". The FCA
family asks the harder question: "how much can I reach ONCE EVERYONE
ELSE IS ALSO REACHING FOR IT?" Supply (jobs, GPs, school places)
meets demand (workers, patients, pupils):

```python
from equipop.fca import fca, fca_segments
from equipop.decay import Decay

d_out, s_out = fca(people_cells, job_cells,
                   demand_col="Working_sum", supply_col="Jobs",
                   decay=Decay(model="negexp", half_life_m=3000),
                   reach="decay", method="2sfca")
# d_out["A"]: jobs-per-worker experienced at each home cell
# s_out["R"]: workers competing for each job cell's supply
```

The reach comes from the neighbourhood menu: `reach="r", r=5000`
(classic catchments), `reach="k", k=1000` (kFCA - catchments that
GROW until they hold 1,000 jobs around a home / 1,000 workers around
a workplace, the fixed-mass EquiPop signature), or `reach="effort"`
with a DEM (hills and round trips included; the decay half-life is
then in effort rounds). `method="3sfca"` adds demand-splitting;
`balance=200` switches to the doubly-constrained model where supply
and demand are forced to clear (competition-adjusted A, congestion C).

Different people compete in different markets - the match table:

```python
segs = [{"name": "all", "demand_col": "Working_sum", "supply_col": "Jobs"},
        {"name": "low", "demand_col": "LowEdu_sum",
         "supply_col": "LowEdu_jobs"}]
d_out, s_out = fca_segments(people_cells, job_cells, segs,
                            decay=Decay(model="negexp", half_life_m=3000))
# A_all vs A_low: the accessibility GAP of the low-educated, per cell
```

Sharing sensitive point data? `examples/make_synthetic_jobs_people.py`
moves both files with ONE rigid transform - every distance (also
BETWEEN the files) is exactly preserved, so results reproduce, while
locations are gone. It refuses to write if its self-check fails.
