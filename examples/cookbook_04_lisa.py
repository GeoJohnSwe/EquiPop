"""cookbook_04 - LISA clusters on Gridby (Book ch. 11)."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from equipop.datasets import load
from equipop.cells import CellData
from equipop.fastcounts import run_knn_counts
from equipop.autocorr import build_weights, local_morans, autocorr_profile

g = load("gridby"); p = g["people"]
cd = CellData(E=p.x.to_numpy(), N=p.y.to_numpy(), n=p.count_all.to_numpy(),
              binary_sums={"g": p.count_group.to_numpy()},
              value_arrays={}, unit_size=100.0)
out = run_knn_counts(cd, [50, 400, 1600])
W = build_weights(out.EastWest, out.NorthSouth, "knn", k=8)
lisa = local_morans(out.R_g_400, W, permutations=199, name="R_g_400")

fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.4),
                       gridspec_kw={"width_ratios": [1.5, 1]})
colors = {"HH": "#b2182b", "LL": "#2166ac", "HL": "#f4a582", "LH": "#92c5de"}
sig = lisa.p < 0.05
ax[0].scatter(out.EastWest[~sig]/1000, out.NorthSouth[~sig]/1000,
              c="#dddddd", s=6)
for q, c in colors.items():
    m = sig & (lisa.quad == q)
    ax[0].scatter(out.EastWest[m]/1000, out.NorthSouth[m]/1000, c=c, s=8,
                  label=f"{q} (n={int(m.sum())})")
ax[0].axvline(3.05, color="steelblue", lw=3, alpha=.5)
ax[0].legend(fontsize=8, frameon=False, loc="lower left")
ax[0].set(title="LISA clusters of R_g_400 (p < .05), Gridby",
          xlabel="km", ylabel="km"); ax[0].set_aspect("equal")

prof = autocorr_profile(out, ["R_g_50", "R_g_400", "R_g_1600"], k=8,
                        permutations=99)
ax[1].plot([50, 400, 1600], prof.I, "o-", color="#333333")
ax[1].set_xscale("log")
ax[1].set(title="Moran's I of the context share, by k",
          xlabel="k (log)", ylabel="Moran's I")
ax[1].annotate("smoothing raises I\nby construction -\nthe loud warning",
               (55, prof.I.iloc[0]+.02), fontsize=8)
for a in ax: a.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig("docs/book/figs/ch11_lisa.png", dpi=140)
print("ch11 figure saved | I by k:", np.round(prof.I.to_numpy(), 3))
