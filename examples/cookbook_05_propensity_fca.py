"""cookbook_05 - propensity FCA on the municipality (Book ch. 13)."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from equipop.datasets import load
from equipop.decay import Decay
from equipop.fca import fca_segments, fca_propensity

p, j = load("municipality")
p["Other_sum"] = p.Working_sum - p.LowEdu_sum
j["Other_jobs"] = j.Jobs - j.LowEdu_jobs
dec = Decay(model="negexp", half_life_m=3000.0)

# baseline: binary walls between the markets (identity M)
dI, _ = fca_segments(p, j, [
    {"name": "low", "demand_col": "LowEdu_sum", "supply_col": "LowEdu_jobs"},
    {"name": "oth", "demand_col": "Other_sum", "supply_col": "Other_jobs"}],
    decay=dec)
# cross-competition: the educated also chase low-edu jobs
# (ILLUSTRATIVE M - replace with estimated propensities, see ch. 13)
M = pd.DataFrame([[0.85, 0.15], [0.25, 0.75]],
                 index=["low", "oth"], columns=["lowjob", "othjob"])
dM, _ = fca_propensity(p, j, M,
                       {"low": "LowEdu_sum", "oth": "Other_sum"},
                       {"lowjob": "LowEdu_jobs", "othjob": "Other_jobs"},
                       decay=dec)
lw = p.LowEdu_sum.to_numpy()
wm = lambda a: np.average(a, weights=np.maximum(lw, 0))
print(f"A_low walls {wm(dI.A_low):.4f} -> cross-competition {wm(dM.A_low):.4f} "
      f"({(wm(dM.A_low)/wm(dI.A_low)-1)*100:+.1f}%)")

fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.6))
m = lw > 0
s0 = ax[0].scatter(p.x[m]/1000, p.y[m]/1000, c=dI.A_low[m], s=5,
                   cmap="viridis", vmin=0, vmax=0.35)
ax[0].set_title("A_low with market walls (identity M)")
delta = (dM.A_low - dI.A_low)
s1 = ax[1].scatter(p.x[m]/1000, p.y[m]/1000, c=delta[m], s=5,
                   cmap="RdBu_r", vmin=-0.06, vmax=0.06)
ax[1].set_title("What cross-competition changes (A_low: M - identity)")
for a, s in zip(ax, [s0, s1]):
    a.set_aspect("equal"); a.set_xlabel("km"); plt.colorbar(s, ax=a, shrink=.85)
    a.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig("docs/book/figs/ch13_propensity.png", dpi=140)
print("ch13 figure saved")
