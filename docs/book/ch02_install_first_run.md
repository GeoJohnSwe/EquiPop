# 2. Install and first run

## The idea

EquiPop is an ordinary Python package, and that is a deliberate
choice: no separate program to install, no licence server, no GIS
system as a prerequisite. If your computer can run Python — and any
computer with the free Anaconda distribution can — then one command
in a terminal window fetches EquiPop from the internet and makes it
available everywhere on your machine. The command is `pip install
equipop`, and "pip" is simply Python's built-in app store: it
downloads the package, checks what it depends on, and puts
everything in place.

The core installation is intentionally small. It brings only the
essential mathematical libraries, which means it installs in under a
minute and works on modest machines. The heavier abilities — reading
satellite rasters, opening GIS shapefiles, importing SPSS files,
drawing maps — live in optional helper packages that you install
only if and when you need them. You never have to guess which one:
the moment a function needs a helper that is missing, EquiPop stops
and tells you its exact name and the exact command to install it.

## Cook it

Open a terminal (on Windows, search the Start menu for "Anaconda
Prompt") and type:

```
pip install equipop
```

When the prompt returns, the installation is done. Now the
thirty-second first analysis. Paste the following into any Python
window — Jupyter, Spyder, or plain `python` in the terminal. It
invents a tiny dataset of seven people by hand, so nothing needs to
be downloaded: each person has an x and a y coordinate (in metres)
and a 0/1 marker called `hi` for belonging to some group.

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

Two things happen here. `build_cells` takes the seven individuals
and sorts them into 100-metre squares — people who share a square
are counted together, which is both faster and, with register data,
often required for privacy. Then `run_knn_counts` builds each
square's egocentric neighbourhood at two sizes, k = 3 and k = 5.
The printed table shows every column type you will meet in this
book: `N_local` (how many people share your own square), `N_3` (at
least three — whole squares enter at once, as chapter 1 explained),
`T_hi_3` and `R_hi_3` (the group count and the group share among
them), and `Dist_3` (how far, in metres, the search travelled to
find three people). If that table printed, your installation is
complete and correct, and everything else in this book will run.

## The dials

The optional helpers, installed on demand with the same `pip
install` pattern: `geopandas pyogrio` for GIS files such as
shapefiles and GeoPackages; `rasterio` for rasters, including
elevation models; `pyreadstat` for SPSS `.sav` files; `openpyxl`
for Excel; `matplotlib jenkspy` for the mapping functions; and
`pyarrow` for the very-large-run machinery of chapter 17.

## Under the hood

It is worth understanding, once, why the software works on
**squares** ("cells") rather than directly on individuals, because
this single design choice explains much of EquiPop's speed and
reach. When `build_cells` aggregates people into 100-metre squares,
a country of sixteen million residents becomes a few million
squares — a size that fits comfortably in an ordinary computer's
memory — while losing at most fifty metres of positional precision,
which is usually finer than the data's own accuracy. All engines in
this book work on those squares and share the conventions of
chapter 1. The engine used above is the "fast engine", the workhorse
for counts and shares; its two siblings handle value statistics
(chapter 6) and travel effort over rivers and hills (chapters 9
and 10).

## Pitfalls

Coordinates must be **metric** — expressed in metres, like the
Swedish or UTM national grids — not in degrees of longitude and
latitude. Degrees are not distances (a degree of longitude shrinks
as you travel north), so distance-based analysis on them is
meaningless. If your data arrives in longitude/latitude, chapter 3
shows the one-line conversion, and EquiPop will even *suggest* a
suitable metric system for your part of the world if you do not
know which one to use.
