"""
demo_stats_sweden.py - statistics on the individual-level Swedish test
data, with THREE independent validations:
  A. global check: at k > global N, every statistic must equal the
     plain whole-file statistic (computable in SPSS/Excel too)
  B. brute-force spot check: 6 random origins recomputed with a
     completely separate pandas implementation
  C. independent Gini: pairwise |xi-xj| definition vs the rank formula
"""
import numpy as np
import pandas as pd
from equipop import build_cells, run_knn_stats

# ------------------------------------------------------------- load
df = pd.read_csv("PopMuniTest.csv", sep=";")
cd = build_cells(df, e_col="RT90_East_4124", n_col="RT90_North_4124",
                 binary_vars=["HighEdu", "LowEdu"],
                 value_vars=["ForvInk", "age"],
                 unit_size=100)

STATS = {
    "HighEdu": ["ratio", "sd", "se", "entropy", "gini"],
    "ForvInk": ["mean", "median", "sd", "se", "gini"],
    "age":     ["mean", "median"],
}
K = [50, 100, 200, 400, 800, 1600, 3200, 15000]   # 15000 > global N (partial)

res = run_knn_stats(cd, k_values=K, stats=STATS)
res.to_csv("sweden_knn_stats_output.csv", index=False)
print(f"\nOutput: {res.shape[0]} rows x {res.shape[1]} columns "
      f"-> sweden_knn_stats_output.csv")

# ------------------------------------------- A. global consistency
print("\n=== A. Global check (k=15000 > N: must equal whole-file stats) ===")
d = df.copy()
for c in ["RT90_East_4124", "RT90_North_4124", "ForvInk"]:
    d[c] = pd.to_numeric(d[c], errors="coerce")
d = d.dropna(subset=["RT90_East_4124", "RT90_North_4124"])
inc = d["ForvInk"].dropna().to_numpy()

def gini_pairwise_chunked(x, chunk=1000):
    """Independent Gini: mean absolute difference definition."""
    n, s, tot = len(x), x.sum(), 0.0
    for i in range(0, n, chunk):
        tot += np.abs(x[i:i+chunk, None] - x[None, :]).sum()
    return tot / (2 * n * n * x.mean())

checks = [
    ("R_HighEdu_15000",    d["HighEdu"].mean()),
    ("Gini_HighEdu_15000", 1 - d["HighEdu"].mean()),
    ("Mean_ForvInk_15000", inc.mean()),
    ("Med_ForvInk_15000",  np.median(inc)),
    ("SD_ForvInk_15000",   inc.std(ddof=1)),
    ("Gini_ForvInk_15000", gini_pairwise_chunked(inc)),
    ("N_15000",            len(d)),
    ("Nv_ForvInk_15000",   len(inc)),
]
for col, truth in checks:
    got = res[col].iloc[0]
    same = np.allclose(res[col], got) and abs(got - truth) < 1e-6 * max(1, abs(truth))
    print(f"{col:22s} engine={got:12.6f}  independent={truth:12.6f}  "
          f"{'OK' if same else 'MISMATCH'}")

# --------------------------------------- B. brute-force spot check
print("\n=== B. Brute force, 6 random origins, k=200 ===")
rng = np.random.default_rng(42)
E = np.floor(d["RT90_East_4124"] / 100) * 100 + 50
N = np.floor(d["RT90_North_4124"] / 100) * 100 + 50
d = d.assign(_E=E.astype(int), _N=N.astype(int))

for oi in rng.choice(len(res), 6, replace=False):
    e0, n0 = res["EastWest"].iloc[oi], res["NorthSouth"].iloc[oi]
    dd = d.assign(dist=np.hypot(d["_E"] - e0, d["_N"] - n0))
    # ring-atomic accumulation, independent implementation
    per_dist = (dd.groupby("dist").size().sort_index().cumsum())
    stop_dist = per_dist.index[np.searchsorted(per_dist.values, 200)]
    sel = dd[dd["dist"] <= stop_dist]
    vals = sel["ForvInk"].dropna().to_numpy()
    ok_n = int(res[f"N_200"].iloc[oi]) == len(sel)
    ok_med = np.isclose(res["Med_ForvInk_200"].iloc[oi], np.median(vals))
    ok_gini = np.isclose(res["Gini_ForvInk_200"].iloc[oi],
                         gini_pairwise_chunked(vals))
    ok_r = np.isclose(res["R_HighEdu_200"].iloc[oi], sel["HighEdu"].mean())
    print(f"origin ({e0},{n0}): N {'OK' if ok_n else 'BAD'} | "
          f"median {'OK' if ok_med else 'BAD'} | "
          f"gini {'OK' if ok_gini else 'BAD'} | ratio {'OK' if ok_r else 'BAD'}")

# ------------------------------------------------ example output rows
print("\n=== Sample output ===")
cols = ["EastWest", "NorthSouth", "N_local", "N_200", "Dist_200",
        "R_HighEdu_200", "Gini_HighEdu_200",
        "Mean_ForvInk_200", "Med_ForvInk_200", "Gini_ForvInk_200",
        "Nv_ForvInk_200", "Mean_age_200"]
print(res[cols].head(5).round(3).to_string())
