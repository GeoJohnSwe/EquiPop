# 2. Install and first run

## The idea

EquiPop is a normal Python package: one `pip install`, no compiler,
no GIS installation. The core needs only numpy/pandas/scipy/pyproj;
heavier abilities (rasters, shapefiles, SPSS, maps) load only if you
install their optional helpers — the package tells you which one the
moment you need it.

## Cook it

In a terminal (Anaconda Prompt on Windows):

```
pip install equipop
```

Then the thirty-second first run, in any Python:

```python
import pandas as pd
from equipop.cells import build_cells
from equipop.fastcounts import run_knn_counts

df = pd.DataFrame({
    "x":  [100, 150, 300, 320, 900, 950, 980],
    "y":  [100, 120, 300, 310, 900, 920, 950],
    "hi": [1,   0,   1,   1,   0,   0,   1]})

cd = build_cells(df, "x", "y", binary_vars=["hi"], unit_size=100)
print(run_knn_counts(cd, k_values=[3, 5]))
```

Seven people, two scales, and every column type you will meet in
this book: `N_local` (who shares your cell), `N_3` (at least three,
whole cells at once), `T_hi_3` and `R_hi_3` (the group count and
share), `Dist_3` (how far three neighbours live). If that printed,
your installation is complete and correct.

## The dials

Optional extras, installed on demand: `geopandas pyogrio` (GIS
files), `rasterio` (rasters/DEMs), `pyreadstat` (SPSS), `openpyxl`
(Excel), `matplotlib jenkspy` (maps), `pyarrow` (large-run parquet).

## Under the hood

Real work happens on **cells**, not individuals: `build_cells`
aggregates people sharing a snapped 100 m cell and remembers per-cell
sums (and, for value statistics, the stored values). This is why a
16-million-person country is a few million cells and fits in memory
(chapter 17). The engine in this chapter is the KD-tree "fast
engine"; two siblings (chapters 6 and 9–10) share its conventions.

## Pitfalls

Coordinates must be **metric** (metres, not degrees). If your data
is in longitude/latitude, chapter 3 shows the one-line projection —
and EquiPop will even suggest a suitable CRS if you don't know one.
