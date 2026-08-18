> **HISTORICAL — DO NOT FOLLOW THIS DOCUMENT.**
>
> Retired at v1.37.1. It describes a command and an installation
> procedure that no longer exist, and following it can put Stata into a
> Python configuration that closes Stata outright on `import numpy`.
>
> **The current instructions are `help equipop` inside Stata, and
> `stata/README_STATA.md`.** Nothing else in this folder is current.
>
> Kept only so that a past field report can be read against what the
> user was told at the time.

---

# EquiPop from Stata — the guide

*Stata 17+, because that is when Stata learned Python. Your data never
leaves Stata's memory; EquiPop results come back as ordinary
variables, ready for `regress` the next line.*

## One-time setup

```stata
python query
* shows which Python Stata talks to. Point it to yours if needed:
python set exec "C:\ProgramData\anaconda3\python.exe", permanently
* then, in a terminal for THAT Python:   pip install equipop
```

Put `equipop_knn.ado` somewhere Stata finds it — simplest is to run
your do-files from this folder and start them with:

```stata
adopath + "`c(pwd)'"
```

## The command: equipop_knn

```stata
equipop_knn, x(varname) y(varname) treat(varlist) ///
             [k(numlist) r(numlist) unit(#) weight(varname) replace]
```

Give `k()` and/or `r()` (new in 1.3): `r(500 2000)` adds N_r500,
T_<v>_r500, R_<v>_r500 - everyone within the radius, however many.
k fixes population, r fixes geometry; use both and compare.

| Option | Meaning | Default |
|---|---|---|
| `x() y()` | metric coordinates (metres!) | required |
| `treat()` | one or MORE numeric group variables | required |
| `k()` | one or more k thresholds | required |
| `unit()` | grid cell size in metres | 100 |
| `weight()` | persons represented by each row (aggregated in-data) | 1 |
| `replace` | drop and recreate existing result variables | off |

Per k you receive `N_<k>`, `Dist_<k>`, and per treatment variable v:
`T_<v>_<k>`, `R_<v>_<k>` — row-aligned to the dataset in memory. Rows
with missing coordinates get missing results (and a message).

```stata
use stata_test_data, clear
equipop_knn, x(X_local) y(Y_local) treat(HighEdu LowEdu) ///
             k(50 200 800) unit(100) replace
regress ValFloat R_HighEdu_200
```

## The showcase

`equipop_showcase.do` in this folder walks through **everything**:
all command options, a live MAUP experiment, and — via python blocks —
value statistics, distance decay and a full segregation profile, each
with EXPECT-comments giving the exact numbers the run should produce
on `stata_test_data.dta`. Run it top to bottom once; steal from it
forever.

## Recipes beyond the command (python blocks)

The pattern is always the same three steps — pull columns over the
`sfi` bridge, compute with EquiPop, store results row-aligned — and
the showcase contains ready-made blocks for:

- **Value statistics** — mean / median / Gini of a continuous variable
  among each person's k nearest (showcase §6)
- **Distance decay** — negexp with a half-life in metres; decayed
  ratio `RD_*` back as a variable (showcase §7)
- **Segregation profile** — eight indices across scales, printed and
  saved to CSV (showcase §8)

## NEW in 1.2 — slopes from Stata

Terrain-aware, direction-asymmetric effort: how many "flat-equivalent
rounds" it takes each person to assemble their k nearest, given a DEM.
Requires `pip install rasterio` in Stata's Python, a DEM GeoTIFF in
the SAME metric CRS as your coordinates, and patience proportional to
your dataset (it is a shortest-path model; the block below prints
progress).

```stata
capture drop SlopeRounds_400 Rounds_400

python:
from sfi import Data
import numpy as np
import pandas as pd
from equipop.slope import run_knn_slope

DEM  = r"C:\data\my_dem.tif"     # <- adapt
UNIT, K = 100.0, 400

def _col(v):
    a = np.array(Data.get(v), dtype=float)
    a[a > 8.9e307] = np.nan
    return a

x, y, tr = _col("X_local"), _col("Y_local"), _col("HighEdu")
df = pd.DataFrame({"x": x, "y": y, "t": tr})
valid = df["x"].notna() & df["y"].notna()
dv = df[valid]

# individuals -> cells (the engine works on cells)
half = UNIT / 2.0
E = (np.floor(dv["x"] / UNIT) * UNIT + half).astype("int64")
N = (np.floor(dv["y"] / UNIT) * UNIT + half).astype("int64")
cells = (pd.DataFrame({"x": E, "y": N, "count_all": 1.0,
                       "count_group": dv["t"]})
         .groupby(["x", "y"], as_index=False).sum())

res = run_knn_slope(cells, [K], altitude=DEM, model="tobler",
                    unit_size=UNIT)
res = res.set_index(["EastWest", "NorthSouth"])

out = np.full(len(x), np.nan)
vidx = np.flatnonzero(valid.to_numpy())
out[vidx] = res.loc[list(zip(E, N)), f"Rounds_{K}"].to_numpy(float)
Data.addVarDouble(f"SlopeRounds_{K}")
Data.store(f"SlopeRounds_{K}", None,
           [v if np.isfinite(v) else None for v in out])
print("slope effort stored as SlopeRounds_%d" % K)
end

summarize SlopeRounds_400
* the interesting variable: effort per person - regress health,
* mobility, or service use on it, controlling for R_* composition.
```

Swap `model="tobler"` for `model="linear", lambda_up=5` (pass extra
parameters straight into `run_knn_slope(...)`). Add a friction table
with `fr=` to combine water barriers and hills in one model. For big
datasets, compute a subsample first: `origins=np.arange(0, len(cells), 10)`.

## If it fails

- *"equipop is not installed in Stata's Python"* — the pip install
  went into a different Python; `python query` shows which one Stata
  uses.
- *"variable X already exists - use option replace"* — exactly that.
- Anything else: the error text is your friend; the computation lives
  in `equipop.stata_bridge` and is pytest-covered, so problems are
  almost always environment (which Python, missing rasterio), not math.


## NEW in 1.6 - one command, the whole toolbox: equipop_run

```stata
* counts (as equipop_knn, same options):
equipop_run, engine(counts) x(X) y(Y) treat(HighEdu) k(200) r(500) replace
* value statistics among the k nearest:
equipop_run, engine(stats) x(X) y(Y) values(Income) stats(mean gini) k(400) replace
* slopes (DEM path; roundtrip optional):
equipop_run, engine(slope) x(X) y(Y) treat(HighEdu) k(400) tau(8) ///
    dem("C:\data\dem.tif") roundtrip replace
* FCA - your data = demand, supply from a file; returns A and J:
equipop_run, engine(fca) x(X) y(Y) demandvar(Workers) ///
    supply("C:\data\jobs.csv") supplycol(Jobs) halflife(3000) replace
regress outcome A
```

A and J arrive row-aligned: A = jobs-per-worker after competition,
J = the competition-blind potential, J/A = effective competitor mass.
The old equipop_knn keeps working unchanged.
