* ============================================================================
* equipop_showcase.do - EquiPop 1.44.6 from Stata: every function, one script
* ----------------------------------------------------------------------------
* Requires: Stata 17+, Python visible to Stata (help python), and the
* package installed in THAT Python:  pip install equipop
*
* Run from the stata/ folder of the EquiPop repository (it needs
* equipop.ado and stata_test_data.dta next to it).
*
* Sections 1-5 use the equipop command (the ado; equipop_knn still works). Sections 6-8 reach
* deeper into the EquiPop package through Stata's python blocks: value
* statistics, distance decay, and a segregation profile.
*
* "EXPECT:" comments give the numbers this exact script produced when the
* computations were verified outside Stata against this exact dataset -
* if your numbers match, the whole chain (Stata -> sfi -> EquiPop -> back)
* is working perfectly.
* ============================================================================

version 17
clear all
set more off

* ---------------------------------------------------------------------------
* SECTION 0 - one-time setup (uncomment and adapt on FIRST use only)
* ---------------------------------------------------------------------------
* python query
*     // shows which Python Stata uses. If it is not the one where you
*     // installed equipop, point Stata to the right one, e.g.:
* python set exec "C:\ProgramData\anaconda3\python.exe", permanently
*     // then, in a terminal for that Python:  pip install equipop

* make the equipop command visible this session (ado in current folder)
adopath + "`c(pwd)'"

* ---------------------------------------------------------------------------
* SECTION 1 - the test data
* ---------------------------------------------------------------------------
use stata_test_data, clear
describe
* 10,892 observations. Metric coordinates X_local / Y_local; four binary
* education variables (LowEdu, HighEdu, TheoEdu, VocaEdu); one continuous
* variable (ValFloat, has missings by design); one count (ValCount).

count if missing(X_local) | missing(Y_local)
* EXPECT: 9. These rows are kept - EquiPop gives them missing results and
* says so, rather than silently dropping them (design decision).

* ---------------------------------------------------------------------------
* SECTION 2 - the basic call: one treatment variable, several k
* ---------------------------------------------------------------------------
* For every individual: among the k nearest persons (grid-cell based,
* 100 m cells), how many belong to the group?
*   N_<k>         people reached - EXACTLY k by default. (It read
*                 ">= k, whole cells are added" until 1.40.7; the
*                 default overshoot is now proportional, which
*                 interpolates inside the ring that crosses k. Ask for
*                 overshoot(whole) to get the old >= k behaviour.)
*   Dist_<k>      radius needed to reach k
*   T_<v>_<k>     group members among them
*   R_<v>_<k>     the ratio T/N - the individualised context share

equipop, x(X_local) y(Y_local) treat(HighEdu) k(50 200 800) unit(100)

summarize N_200 Dist_200 R_HighEdu_*
* EXPECT (means): N_200 200.00 | Dist_200 1142.40 | R_HighEdu_50 .1882 |
*                 R_HighEdu_200 .1849 | R_HighEdu_800 .1871

* The scale story in one picture: context share is noisy at k=50,
* smooth at k=800 - aggregation as a dial, not a fixed choice.
twoway (histogram R_HighEdu_50,  color(navy%40))  ///
       (histogram R_HighEdu_800, color(maroon%40)), ///
       legend(order(1 "k = 50" 2 "k = 800")) ///
       title("Individualised context share of HighEdu, two scales")

* ---------------------------------------------------------------------------
* SECTION 3 - several treatments at once, and the replace option
* ---------------------------------------------------------------------------
* treat() takes a varlist: one spatial search, results for every variable.
equipop, x(X_local) y(Y_local) treat(HighEdu LowEdu TheoEdu VocaEdu) ///
             k(50 200 800) unit(100) replace
* (replace: drop and recreate any of the result variables that already
*  exist - without it the command refuses to overwrite, on purpose.)

summarize R_*_200

* ---------------------------------------------------------------------------
* SECTION 4 - weighted rows (aggregated in-data)
* ---------------------------------------------------------------------------
* pop() says "this row represents <w> persons". Treatment values are
* then treated as shares/counts scaled by the weight. Here we PRETEND
* ValCount is such a population weight, purely to demonstrate the option.
preserve
equipop, x(X_local) y(Y_local) treat(HighEdu) k(200) unit(100) ///
             pop(ValCount) treatmode(flags) replace
summarize R_HighEdu_200
* EXPECT: mean approx .2089 (differs from .1849 - the weighting matters)
* treatmode(flags) IS REQUIRED HERE and was missing until 1.40.7.
* HighEdu is a 0/1 MARKER. Once pop() supplies a population, the
* default treatmode(counts) reads that marker as a number of PEOPLE,
* so the numerator counts POINTS while the denominator counts PEOPLE
* and the share comes back about 47 times too small - .0044 instead
* of .2089. Nothing refuses it, because 0 and 1 are perfectly
* possible person counts. See block 7 of equipop_test_pass.do, which
* runs both settings side by side and measures the ratio.
restore

* ---------------------------------------------------------------------------
* SECTION 5 - the MAUP dial: unit() and what it does to your variable
* ---------------------------------------------------------------------------
* Same data, same k, coarser grid: 400 m cells instead of 100 m.
rename R_HighEdu_200 R_u100_200
equipop, x(X_local) y(Y_local) treat(HighEdu) k(200) unit(400) replace
rename R_HighEdu_200 R_u400_200

correlate R_u100_200 R_u400_200
* EXPECT: r approx 0.912 - high but not 1. The grid size is part of the
* measurement. (Same phenomenon we quantified on Malta POI data: the
* correlation climbs towards 1 as k grows.)
rename R_u400_200 R_HighEdu_200   // keep names tidy for what follows

* the classic downstream use: context as a regressor
regress ValFloat R_HighEdu_200 ValCount

* ============================================================================
* THE DEEPER SHELF - sections 6-8 call EquiPop's wider machinery directly
* through Stata python blocks. Same pattern as inside the ado: pull columns
* over the sfi bridge, compute in Python, store results row-aligned.
* ============================================================================

* ---------------------------------------------------------------------------
* SECTION 6 - value STATISTICS among the k nearest (stats engine)
* ---------------------------------------------------------------------------
* WHY THIS ONE NEEDS PYTHON AT ALL: the equipop command has no stats()
* option, so mean, median and Gini over a neighbourhood cannot be
* reached from Stata any other way. treat() is NOT the way round it -
* it holds a COUNT OF PEOPLE, and a continuous magnitude divided by a
* headcount is not a share. See BACKLOG 204.
* Not just counts: mean, median and Gini of a continuous variable
* (ValFloat) among each person's 200 nearest neighbours. ValFloat has
* missings: those persons still count towards k, but not towards the
* statistic (Nv_ = the valid basis).

capture drop Mean_ValFloat_200 Med_ValFloat_200 Gini_ValFloat_200 Nv_ValFloat_200

python:
from sfi import Data
import numpy as np
import pandas as pd
from equipop.cells import build_cells
from equipop.analysis import run_knn_stats
from equipop.stata_bridge import to_stata_values

def _col(v):
    a = np.array(Data.get(v), dtype=float)
    a[a > 8.9e307] = np.nan            # Stata missings arrive huge
    return a

x, y, val = _col("X_local"), _col("Y_local"), _col("ValFloat")
UNIT, K = 100.0, 200

df = pd.DataFrame({"x": x, "y": y, "ValFloat": val})
valid = df["x"].notna() & df["y"].notna()
dv = df[valid]

cd = build_cells(dv, "x", "y", value_vars=["ValFloat"], unit_size=UNIT)
st = run_knn_stats(cd, [K], stats={"ValFloat": ["mean", "median", "gini"]})
st = st.set_index(["EastWest", "NorthSouth"])

half = UNIT / 2.0
E = (np.floor(dv["x"] / UNIT) * UNIT + half).astype("int64")
N = (np.floor(dv["y"] / UNIT) * UNIT + half).astype("int64")
keys = list(zip(E, N))
vidx = np.flatnonzero(valid.to_numpy())

for cname in [f"Nv_ValFloat_{K}", f"Mean_ValFloat_{K}",
              f"Med_ValFloat_{K}", f"Gini_ValFloat_{K}"]:
    out = np.full(len(x), np.nan)
    out[vidx] = st.loc[keys, cname].to_numpy(dtype=float)
    Data.addVarDouble(cname)
    # to_stata_values, NOT a None: Stata's Data.store refuses None for
    # a numeric and raises "the specified value should be a numeric
    # value". This is BACKLOG 173, fixed in equipop_run.ado in 1.40.1;
    # this file kept the old pattern and so has crashed here ever
    # since ValFloat's missings started reaching the output.
    Data.store(cname, None, to_stata_values(out))
print("stats engine: 4 variables stored")
end

summarize Mean_ValFloat_200 Med_ValFloat_200 Gini_ValFloat_200
* EXPECT (means): Nv 167.30 | Mean 1815.23 | Med 1248.10 | Gini .5806
* MEASURED FOR THE FIRST TIME IN 1.40.7. This section had never run
* to completion in Stata - it died at the Data.store above - so its
* old expectations had never been compared with anything.
* Median < mean and Gini approx .58: a right-skewed, unequal variable -
* and now you have LOCAL inequality per individual, ready to regress.

* ---------------------------------------------------------------------------
* SECTION 7 - DISTANCE DECAY (ring engine, negexp with half-life)
* ---------------------------------------------------------------------------
* Nearby neighbours matter more. Weight every neighbour by exp(beta*d)
* with the half-life parameterisation: at 1000 m a person counts half.
* Five models exist (negexp, expnormal, expsqrt, lognormal, power);
* negexp shown here - swap the model= string to try the others.
* Convention: k is defined by RAW counts; decayed values are recorded at
* that same moment; decayed <= raw by construction.

capture drop RD_HighEdu_200 ND_200

python:
from sfi import Data
import numpy as np
import pandas as pd
from equipop.cells import build_cells
from equipop.analysis import run_knn
from equipop.decay import Decay
from equipop.stata_bridge import to_stata_values

def _col(v):
    a = np.array(Data.get(v), dtype=float)
    a[a > 8.9e307] = np.nan
    return a

x, y, tr = _col("X_local"), _col("Y_local"), _col("HighEdu")
UNIT, K = 100.0, 200

df = pd.DataFrame({"x": x, "y": y, "HighEdu": tr})
valid = df["x"].notna() & df["y"].notna()
dv = df[valid]

cd = build_cells(dv, "x", "y", binary_vars=["HighEdu"], unit_size=UNIT)
cells = pd.DataFrame({"E_grid": cd.E, "N_grid": cd.N,
                      "FullPop": cd.n,
                      "Treatment": cd.binary_sums["HighEdu"]})
r = run_knn(cells, [K], unit_size=UNIT,
            decay=Decay(model="negexp", half_life_m=1000), id_col=None)
r = r.set_index(["EastWest", "NorthSouth"])

half = UNIT / 2.0
E = (np.floor(dv["x"] / UNIT) * UNIT + half).astype("int64")
N = (np.floor(dv["y"] / UNIT) * UNIT + half).astype("int64")
keys = list(zip(E, N))
vidx = np.flatnonzero(valid.to_numpy())

for src, dst in [(f"ND_{K}", f"ND_{K}"), (f"RD_{K}", f"RD_HighEdu_{K}")]:
    out = np.full(len(x), np.nan)
    out[vidx] = r.loc[keys, src].to_numpy(dtype=float)
    Data.addVarDouble(dst)
    Data.store(dst, None, to_stata_values(out))   # see section 6
print("decay: ND_200 and RD_HighEdu_200 stored (negexp, half-life 1000 m)")
end

summarize R_HighEdu_200 RD_HighEdu_200 N_200 ND_200
* EXPECT (means): RD_HighEdu_200 .1860 vs raw R .1849 | ND_200 126.01
* vs N_200 200.00. Also measured for the first time in 1.40.7.
* SINCE 1.40 YOU DO NOT NEED THIS PYTHON BLOCK for decay: the command
* takes decay(negexp) halflife(1000) directly, and that is the
* supported route. It is kept here because seeing the same answer
* arrive by both paths is the point of the deeper shelf.
* Note the lesson: decay barely moves the AVERAGE
* ratio (numerator and denominator reweight alike) - it moves the
* INDIVIDUALS whose nearby context differs from their far context:
gen ctx_gradient = RD_HighEdu_200 - R_HighEdu_200
summarize ctx_gradient, detail

* ---------------------------------------------------------------------------
* SECTION 8 - SEGREGATION PROFILE across scales (segregation module)
* ---------------------------------------------------------------------------
* Eight indices (D, Gini, Entropy H, Atkinson, Isolation, Interaction,
* Correlation V, SI) computed at each k - the multiscalar profile from
* Osth, Clark & Malmberg (2015). Printed as a table; also saved to CSV.

python:
from sfi import Data
import numpy as np
import pandas as pd
from equipop.cells import build_cells
from equipop.fastcounts import run_knn_counts
from equipop.segregation import seg_profile

def _col(v):
    a = np.array(Data.get(v), dtype=float)
    a[a > 8.9e307] = np.nan
    return a

x, y, tr = _col("X_local"), _col("Y_local"), _col("HighEdu")
df = pd.DataFrame({"x": x, "y": y, "HighEdu": tr}).dropna(subset=["x", "y"])

cd = build_cells(df, "x", "y", binary_vars=["HighEdu"], unit_size=100)
KS = [50, 200, 800]
out = run_knn_counts(cd, KS, m_neighbors=4096)

prof = seg_profile(out, KS,
                   n_col="N_{k}", t_col="T_HighEdu_{k}",
                   local_all="N_local", local_grp="HighEdu_local")
print(prof.round(4).to_string(index=False))
prof.to_csv("segregation_profile_HighEdu.csv", index=False)
print("saved: segregation_profile_HighEdu.csv")
end

* EXPECT (SI column): local .4036 | k=50 .2216 | k=200 .2002 | k=800 .1930
* Also measured for the first time in 1.40.7 - section 8 sits after
* two blocks that used to halt the script, so it had never been
* reached either.
* The classic declining profile: micro-scale sorting fades as the
* neighbourhood definition widens - the scale IS the finding.

* ---------------------------------------------------------------------------
* Done. Everything above is now ordinary Stata: regress, margins, graph.
* ============================================================================
display as result "equipop_showcase.do completed - EquiPop 1.44.6 full tour"
