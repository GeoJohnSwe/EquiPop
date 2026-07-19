"""cookbook_10 - the river shadow: friction isochrones (Book ch. 9)."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from equipop.datasets import load
from equipop.friction import run_knn_friction

g = load("gridby"); p = g["people"]; fr = g["friction"]
res = run_knn_friction(p, [200], fr=fr, unit_size=100.0,
                       tau_values=[3])
fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.2))
s0 = ax[0].scatter(res.EastWest/1000, res.NorthSouth/1000,
                   c=res.N_tau3, s=6, cmap="cividis")
ax[0].set_title("people reachable within 3 rounds (N_tau3)")
s1 = ax[1].scatter(res.EastWest/1000, res.NorthSouth/1000,
                   c=res.Rounds_200, s=6, cmap="magma_r")
ax[1].set_title("rounds needed to gather 200 people (Rounds_200)")
for a, s in zip(ax, [s0, s1]):
    a.axvline(3.05, color="steelblue", lw=2, alpha=.5)
    a.set_aspect("equal"); a.set_xlabel("km")
    plt.colorbar(s, ax=a, shrink=.85)
    a.spines[["top","right"]].set_visible(False)
fig.tight_layout(); fig.savefig("docs/book/figs/ch09_friction.png", dpi=140)
print("ch09 figure saved")
