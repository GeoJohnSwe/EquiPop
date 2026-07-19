"""cookbook_07 - local median and local inequality (Book ch. 6).
Gridby has no income variable, so this script INVENTS one for
illustration: incomes are drawn lognormally, higher on average in
the west, more unequal near the river. Labelled synthetic."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from equipop.datasets import load
from equipop.cells import build_cells
from equipop.analysis import run_knn_stats

g = load("gridby"); p = g["people"]
rng = np.random.default_rng(1848)
rows = p.loc[p.index.repeat(p.count_all.astype(int))].reset_index(drop=True)
west_bonus = 0.5 * (1 - rows.x / rows.x.max())
spread = 0.45 + 0.35 * np.exp(-np.abs(rows.x - 3050) / 600)
rows["income"] = np.exp(rng.normal(10 + west_bonus, spread))
cd = build_cells(rows, "x", "y", value_vars=["income"], unit_size=100)
st = run_knn_stats(cd, k_values=[400],
                   stats={"income": ["median", "gini"]})
fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.2))
for a, (c, t, cm) in zip(ax, [("Med_income_400", "local median income (k = 400)", "cividis"),
                              ("Gini_income_400", "local income inequality: Gini (k = 400)", "magma")]):
    s = a.scatter(st.EastWest/1000, st.NorthSouth/1000, c=st[c], s=6, cmap=cm)
    a.set_title(t); a.set_aspect("equal"); a.set_xlabel("km")
    plt.colorbar(s, ax=a, shrink=.85)
    a.spines[["top","right"]].set_visible(False)
fig.tight_layout()
fig.savefig("docs/book/figs/ch06_valuestats.png", dpi=140)
print("ch06 figure saved")
