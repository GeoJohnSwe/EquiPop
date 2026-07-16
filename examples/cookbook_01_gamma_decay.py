"""
cookbook_01_gamma_decay.py - the gamma effect in power decay (#13 entry 1).

Two panels, one lesson each:
 LEFT  - the weight curves w(d) for gamma 0.5, 1, 2, 4 at a fixed
         half-life: every curve crosses EXACTLY at (h, 0.5) - the
         half-life anchors, gamma is the TAIL dial. Negexp dashed
         as the familiar reference.
 RIGHT - the marginal access r*w(r) (uniform opportunity density):
         gamma > 1 shows a peak - the OPPORTUNITY HORIZON; gamma <= 1
         never turns over - the horizon is INFINITE (the v1.4.0
         theorem, drawn instead of stated).

Run:  python examples/cookbook_01_gamma_decay.py
Out:  gamma_decay_figure.png (embed in MANUAL_BEGINNER.md section 17)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from equipop.decay import Decay
from equipop.access import opportunity_horizon

H = 2000.0                                    # half-life, metres
GAMMAS = [0.5, 1.0, 2.0, 4.0]
COLS = ["#c2571a", "#8a2be2", "#1f77b4", "#2ca02c"]

d = np.linspace(0.0, 5.5 * H, 800)
neg = Decay(model="negexp", half_life_m=H)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5))

for g, c in zip(GAMMAS, COLS):
    dc = Decay(model="power", half_life_m=H, gamma=g)
    ax1.plot(d / 1000, dc.weight_vec(d), color=c,
             label=f"power, $\\gamma$ = {g:g}")
    ax2.plot(d / 1000, d * dc.weight_vec(d) / H, color=c)
    r_star = opportunity_horizon(dc)
    if np.isfinite(r_star):
        ax2.axvline(r_star / 1000, color=c, lw=0.9, ls=":")
ax1.plot(d / 1000, neg.weight_vec(d), "k--", lw=1.4, label="negexp (reference)")
ax2.plot(d / 1000, d * neg.weight_vec(d) / H, "k--", lw=1.4)
ax2.axvline(opportunity_horizon(neg) / 1000, color="k", lw=0.9, ls=":")

ax1.scatter([H / 1000], [0.5], zorder=5, color="black", s=28)
ax1.annotate("all curves cross here:\nw(h) = 0.5 exactly",
             xy=(H / 1000, 0.5), xytext=(H / 1000 + 1.1, 0.62),
             arrowprops=dict(arrowstyle="->", lw=0.9), fontsize=9)
ax1.set(xlabel="distance (km)", ylabel="weight w(d)",
        title=f"The tail dial: shifted power, half-life {H/1000:g} km")
ax1.legend(frameon=False, fontsize=9)

ax2.set(xlabel="distance (km)", ylabel="marginal access  r·w(r) / h",
        title="Where access comes from: horizons exist only for $\\gamma$ > 1")
ax2.annotate("$\\gamma \\leq 1$: never turns over —\nthe horizon is infinite",
             xy=(4.9, 0.9 * (4.9 * 1000 * Decay(model='power', half_life_m=H,
                 gamma=0.5).weight(4900) / H)),
             xytext=(2.6, 1.55), fontsize=9,
             arrowprops=dict(arrowstyle="->", lw=0.9))
for a in (ax1, ax2):
    a.spines[["top", "right"]].set_visible(False)

fig.suptitle("Power decay with exact half-life: one parameter for the anchor, one for the tail",
             fontsize=12)
fig.tight_layout()
fig.savefig("gamma_decay_figure.png", dpi=150)
print("saved gamma_decay_figure.png | horizons (km):",
      {f"g={g:g}": round(opportunity_horizon(
          Decay(model='power', half_life_m=H, gamma=g)) / 1000, 2)
       for g in GAMMAS},
      "| negexp:", round(opportunity_horizon(neg) / 1000, 2))
