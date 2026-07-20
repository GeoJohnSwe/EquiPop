"""cookbook_11 - the hill's toll and the journey home (Book ch. 10)."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from equipop.datasets import load
from equipop.slope import run_knn_slope

g = load("gridby"); p = g["people"]
NX, NY, U = g["meta"]["nx"], g["meta"]["ny"], g["meta"]["unit"]
gx, gy = np.meshgrid(np.arange(NX), np.arange(NY), indexing="ij")
alt = pd.DataFrame({"x": gx.ravel()*U + U/2, "y": gy.ravel()*U + U/2,
                    "alt": g["altitude"]})
one = run_knn_slope(p, [200], altitude=alt, unit_size=U,
                    fr=g["friction"])
rt = run_knn_slope(p, [200], altitude=alt, unit_size=U,
                   fr=g["friction"], roundtrip=True)
pen = rt.Rounds_200 / one.Rounds_200
fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.2))
s0 = ax[0].scatter(one.EastWest/1000, one.NorthSouth/1000,
                   c=one.Rounds_200, s=6, cmap="magma_r")
ax[0].set_title("effort to gather 200 people (hill + river, one-way)")
s1 = ax[1].scatter(rt.EastWest/1000, rt.NorthSouth/1000, c=pen, s=6,
                   cmap="RdPu", vmin=1.0, vmax=float(np.nanpercentile(pen, 99)))
ax[1].set_title("the journey home: round-trip / one-way effort")
for a, s in zip(ax, [s0, s1]):
    circ = plt.Circle((4.85, 3.05), .5, fill=False, ls=":", color="k")
    a.add_patch(circ); a.axvline(3.05, color="steelblue", lw=2, alpha=.4)
    a.set_aspect("equal"); a.set_xlabel("km")
    plt.colorbar(s, ax=a, shrink=.85)
    a.spines[["top","right"]].set_visible(False)
fig.tight_layout(); fig.savefig("docs/book/figs/ch10_slopes.png", dpi=140)
print("ch10 figure saved | max RT penalty:", round(float(np.nanmax(pen)), 3))
