"""cookbook_13 - theta(k): how much of income inequality lines up with
the kind of neighbourhood people come from, and at what scale
(MANUAL_TOPICS.md section 17; v1.62.0).

A SYNTHETIC town, labelled as such, with planted truths. 12 x 12 km on
a 100 m grid; parents with low education are more common in five
districts. The same people get incomes three ways:

  A  the neighbourhood matters, at 800 people - and family matters
  B  only family matters (but families cluster in space)
  C  nothing matters

Read the profiles against what was planted: A peaks at k = 800 and
keeps about half of it on top of family; B lines up "alone" and adds
nothing on top of family; C sits on its noise floor.
"""
import contextlib
import io

import numpy as np
import pandas as pd

import equipop
from equipop.cells import build_cells
import equipop.fastcounts as FC

rng = np.random.default_rng(2026)
NX = NY = 120
gx, gy = np.meshgrid(np.arange(NX), np.arange(NY), indexing="ij")
gx, gy = gx.ravel().astype(float), gy.ravel().astype(float)

dens = 1.0
for cx, cy, h, s in [(60, 60, 14, 18), (25, 30, 8, 9), (95, 35, 7, 8),
                     (40, 100, 8, 10)]:
    dens = dens + h * np.exp(-((gx - cx) ** 2 + (gy - cy) ** 2) / (2 * s * s))
pop = rng.poisson(dens * 0.9)
z = -1.6 + 1.2 * gx / NX
for cx, cy, h, s in [(70, 55, 2.2, 8), (30, 35, 1.8, 6), (100, 80, 2.0, 9),
                     (50, 95, 1.6, 7), (90, 25, 1.4, 5)]:
    z = z + h * np.exp(-((gx - cx) ** 2 + (gy - cy) ** 2) / (2 * s * s))
p_low = 1 / (1 + np.exp(-(z + rng.normal(0, 0.5, z.size))))

live = np.flatnonzero(pop > 0)
cell = np.repeat(live, pop[live])
low = (rng.random(cell.size) < p_low[cell]).astype(float)
people = pd.DataFrame({
    "x": gx[cell] * 100 + 100 * rng.random(cell.size),
    "y": gy[cell] * 100 + 100 * rng.random(cell.size),
    "low_edu": low,
    "parents_edu": np.where(low > 0, "low", "not low")})

# the planted neighbourhood: the share of low education among the 800
# nearest, own cell left out - measured by EquiPop itself
with contextlib.redirect_stdout(io.StringIO()):
    cd = build_cells(people, "x", "y", binary_vars=["low_edu"],
                     unit_size=100.0)
    r = FC.run_knn_counts(cd, k_values=[800], self_rule="exclude", seed=1)
look = dict(zip(zip(r.EastWest.round().astype(int),
                    r.NorthSouth.round().astype(int)), r.R_low_edu_800))
snap = lambda v: (np.floor(v / 100) * 100 + 50).astype(int)  # noqa: E731
c800 = np.array([look[k] for k in zip(snap(people.x), snap(people.y))])

eps = rng.normal(0, 0.55, len(people))
people["income_A"] = np.exp(10 - 0.30 * low - 1.0 * c800 + eps)
people["income_B"] = np.exp(10 - 0.60 * low + eps)
people["income_C"] = np.exp(10 + eps)

K = [50, 100, 200, 400, 800, 1600, 3200, 6400]
for world in "ABC":
    print(f"\n=== world {world} ===")
    equipop.theta_profile(people, outcome=f"income_{world}",
                          character="low_edu", family="parents_edu",
                          k_values=K)
