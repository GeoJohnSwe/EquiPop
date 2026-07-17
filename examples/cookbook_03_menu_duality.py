"""cookbook_03 - what floats: the k/r duality (Book ch. 4)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from equipop.datasets import load
from equipop.cells import CellData
from equipop.fastcounts import run_knn_counts

g = load("gridby"); p = g["people"]
cd = CellData(E=p.x.to_numpy(), N=p.y.to_numpy(), n=p.count_all.to_numpy(),
              binary_sums={}, value_arrays={}, unit_size=100.0)
out = run_knn_counts(cd, [400], r_values=[500.0])
fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.3))
a = ax[0].scatter(out.EastWest/1000, out.NorthSouth/1000, c=out.Dist_400,
                  s=8, cmap="magma_r")
ax[0].set_title("k = 400 fixes POPULATION - the radius floats (Dist_400, m)")
b = ax[1].scatter(out.EastWest/1000, out.NorthSouth/1000, c=out.N_r500,
                  s=8, cmap="cividis")
ax[1].set_title("r = 500 m fixes GEOMETRY - the count floats (N_r500)")
for x, im in zip(ax, [a, b]):
    x.set_aspect("equal"); x.set_xlabel("km"); plt.colorbar(im, ax=x, shrink=.85)
    x.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig("docs/book/figs/ch04_duality.png", dpi=140)
print("ch04 figure saved")
