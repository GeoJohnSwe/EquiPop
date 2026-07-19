"""cookbook_06 - one town, three magnifications (Book ch. 5)."""
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
out = run_knn_counts(cd, [50, 1600])
out["R_local"] = out["g_local"] / out["N_local"]
fig, ax = plt.subplots(1, 3, figsize=(15, 3.9))
for a, (c, t) in zip(ax, [("R_local", "own square only (N_local)"),
                          ("R_g_50", "k = 50"), ("R_g_1600", "k = 1600")]):
    s = a.scatter(out.EastWest/1000, out.NorthSouth/1000, c=out[c], s=6,
                  cmap="viridis", vmin=0, vmax=0.8)
    a.set_title(t); a.set_aspect("equal"); a.set_xlabel("km")
    a.spines[["top","right"]].set_visible(False)
plt.colorbar(s, ax=ax, shrink=.8, label="minority share")
fig.suptitle("The same town at three magnifications")
fig.savefig("docs/book/figs/ch05_triptych.png", dpi=140, bbox_inches="tight")
print("ch05 figure saved")
