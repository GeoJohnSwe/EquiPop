"""cookbook_02 - Gridby tour + the multiscalar profile (Book ch. 1)."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from equipop.datasets import load
from equipop.cells import CellData
from equipop.fastcounts import run_knn_counts

g = load("gridby"); p = g["people"]
cd = CellData(E=p.x.to_numpy(), N=p.y.to_numpy(), n=p.count_all.to_numpy(),
              binary_sums={"g": p.count_group.to_numpy()},
              value_arrays={}, unit_size=100.0)
out = run_knn_counts(cd, [50, 400, 1600])

fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.6),
                       gridspec_kw={"width_ratios": [1.5, 1]})
s = ax[0].scatter(out.EastWest/1000, out.NorthSouth/1000,
                  c=out.R_g_400, s=8, cmap="viridis")
ax[0].axvline(3.05, color="steelblue", lw=3, alpha=.6)
ax[0].annotate("the river\n(one bridge)", (3.1, 2.05), fontsize=9)
ax[0].add_patch(plt.Circle((4.85, 3.05), .5, fill=False, ls=":", color="brown"))
ax[0].annotate("the hill", (4.4, 3.6), fontsize=9, color="brown")
ax[0].set(title="Gridby: minority context share, k = 400",
          xlabel="km", ylabel="km"); ax[0].set_aspect("equal")
plt.colorbar(s, ax=ax[0], shrink=.85)
xs = out.EastWest/1000
for k, c in zip([50, 400, 1600], ["#cc6633", "#337799", "#333333"]):
    b = out.groupby((xs*10).round()/10)[f"R_g_{k}"].mean()
    ax[1].plot(b.index, b.values, color=c, label=f"k = {k}")
ax[1].plot([0, 6], [0.10, 0.60], "k--", lw=1, label="planted truth")
ax[1].set(title="One gradient, three scales", xlabel="km west-east",
          ylabel="context share"); ax[1].legend(fontsize=8, frameon=False)
for a in ax: a.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig("docs/book/figs/ch01_gridby.png", dpi=140)
print("ch01 figure saved")
