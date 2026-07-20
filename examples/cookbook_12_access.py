"""cookbook_12 - access potential and the next best place (Book ch. 12)."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from equipop.datasets import load
from equipop.decay import Decay
from equipop.access import potential_surface, opportunity_horizon

g = load("gridby")
jobs = g["jobs"].rename(columns={"jobs": "mass"})
people = g["people"].rename(columns={"count_all": "mass"})
dec = Decay(model="negexp", half_life_m=1000.0)
acc = potential_surface(jobs, dec, unit_size=100.0)        # access to jobs
sur = potential_surface(people, dec, unit_size=100.0)      # new-job surplus
best = sur.loc[sur.potential.idxmax()]
print(f"opportunity horizon (negexp h=1km): {opportunity_horizon(dec):.0f} m")
print(f"best next-job location: ({best.x/1000:.2f}, {best.y/1000:.2f}) km, "
      f"decayed persons {best.potential:.0f}")
fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.2))
s0 = ax[0].scatter(acc.x/1000, acc.y/1000, c=acc.potential, s=4, cmap="viridis")
ax[0].set_title("access to jobs: decayed jobs within reach (h = 1 km)")
s1 = ax[1].scatter(sur.x/1000, sur.y/1000, c=sur.potential, s=4, cmap="inferno")
ax[1].scatter([best.x/1000], [best.y/1000], marker="*", s=180,
              c="white", edgecolors="k", zorder=5)
ax[1].set_title("where would ONE new job help most? (decayed persons)")
for a, s in zip(ax, [s0, s1]):
    a.axvline(3.05, color="steelblue", lw=2, alpha=.4)
    a.set_aspect("equal"); a.set_xlabel("km")
    plt.colorbar(s, ax=a, shrink=.85)
    a.spines[["top","right"]].set_visible(False)
fig.tight_layout(); fig.savefig("docs/book/figs/ch12_access.png", dpi=140)
print("ch12 figure saved")
