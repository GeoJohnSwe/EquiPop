"""cookbook_08 - the kFCA divergence experiment (both sides)."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from equipop.datasets import load
from equipop.fca import fca

p, j = load("municipality")
d, s = fca(p, j, "Working_sum", "Jobs", reach="k", k=500,
           k_side="both")
w = p.Working_sum.to_numpy()
m = w > 0
a_s, a_d = d.A_ksupply.to_numpy(), d.A_kdemand.to_numpy()
corr = np.corrcoef(a_s[m], a_d[m])[0, 1]
div = a_d - a_s
print(f"corr(A_ksupply, A_kdemand) = {corr:.3f}")
print(f"A_ksupply wmean {np.average(a_s, weights=w):.3f} | "
      f"A_kdemand wmean {np.average(a_d, weights=w):.3f}")
print(f"divergence |A_kd - A_ks|: median {np.median(np.abs(div[m])):.3f}, "
      f"p90 {np.percentile(np.abs(div[m]), 90):.3f}")

fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.3))
for a, (v, t) in zip(ax[:2], [(a_s, "A_ksupply: everyone weighs k=500 jobs"),
                              (a_d, "A_kdemand: every job weighs k=500 workers")]):
    sc = a.scatter(p.x[m]/1000, p.y[m]/1000, c=v[m], s=5, cmap="viridis",
                   vmin=0, vmax=np.percentile(a_d[m], 98))
    a.set_title(t, fontsize=10); plt.colorbar(sc, ax=a, shrink=.85)
lim = np.percentile(np.abs(div[m]), 98)
sc = ax[2].scatter(p.x[m]/1000, p.y[m]/1000, c=div[m], s=5, cmap="RdBu_r",
                   vmin=-lim, vmax=lim)
ax[2].set_title("The divergence: A_kdemand - A_ksupply", fontsize=10)
plt.colorbar(sc, ax=ax[2], shrink=.85)
for a in ax:
    a.set_aspect("equal"); a.set_xlabel("km")
    a.spines[["top","right"]].set_visible(False)
fig.tight_layout()
fig.savefig("docs/book/figs/kfca_divergence.png", dpi=140)
print("divergence figure saved")
