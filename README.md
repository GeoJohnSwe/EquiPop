# EquiPop (Python)

k-nearest neighbour contexts/neighbourhoods on gridded and hexagonal
data: bespoke neighbourhoods, friction-aware growth, distance decay,
neighbourhood statistics and segregation measures - for very large
datasets.

EquiPop finds, for every populated location, the k nearest individuals
(by cumulative population count, expanding over a uniform grid) and
reports the composition of that individualised neighbourhood. The
gridded design means one pre-computed distance ordering serves every
origin, which is what makes millions of locations feasible.

## The EquiPop family
This is the first Python implementation. Its relatives: the original
**C# EquiPop** (three generations, two public releases; radial and Flow
models, downloadable via Uppsala University) and an **R version**
covering I/O and the basic k-NN parts. This Python version additionally
carries friction growth, five decay models, exact neighbourhood
statistics (mean/median/SD/SE/Gini/entropy), segregation indices,
hexagonal grids, area aggregation and metadata logging.

## Install
```
pip install equipop            # core
pip install equipop[geo,io,viz]  # shapefiles/rasters, Excel/SPSS, maps
```

## Quick start
```python
import pandas as pd
from equipop import build_cells, run_knn_stats

df = pd.read_csv("individuals.csv")        # one row per individual
cd = build_cells(df, e_col="X", n_col="Y",
                 binary_vars=["treated"], value_vars=["income"],
                 unit_size=100)
res = run_knn_stats(cd, k_values=[100, 400, 1600, 6400],
                    stats={"treated": ["ratio"],
                           "income": ["mean", "median", "gini"]})
```
For aggregated counts at national scale use the vectorised
`run_knn_counts`; for friction-constrained growth `run_knn_friction`;
for segregation profiles `seg_profile`; for policy-area reporting
`aggregate_output`; for quick maps `map_output`. See MANUAL_TOPICS.md.

Repository: https://github.com/GeoJohnSwe/EquiPop

## Citing
Please cite the software and the methods you use - see CITATION.cff.
Core reference: Östh (2014), *Introducing the EquiPop software*,
Uppsala University. Segregation measures: Östh, Clark & Malmberg
(2015), *Geographical Analysis* 47(1). Decay parameters: Östh, Lyhagen
& Reggiani (2016), *EJTIR* 16(2). Friction growth: Östh & Türk (2020),
*Handbook of Urban Segregation*. Decay profiles in application:
Türk, Östh, Kourtit & Nijkamp (2026), *Journal of Urban Mobility* 9.

## License
MIT. Attribution through citation is warmly requested (see above).
