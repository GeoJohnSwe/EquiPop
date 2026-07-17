"""
make_gridby.py - Gridby, the synthetic teaching city (founded 1848).

A 6 x 4 km town on a 100 m grid, generated deterministically with
PLANTED, documented properties so every figure in the Book can
demonstrate exactly one phenomenon:

  1. A west-east SEGREGATION GRADIENT: the minority share rises
     linearly from 10% (west) to 60% (east).
  2. A RIVER running north-south through the middle (friction 6),
     with ONE bridge - straight-line distance lies about the far bank.
  3. A HILL in the north-east (Gaussian, ~90 m) - climbing costs.
  4. A JOBS CLUSTER west of the river (70% of jobs), the rest
     scattered - competition has a geography.

Ground truths live in meta() and double as test fixtures: if EquiPop
cannot recover a planted truth, the tests fail.
"""
import numpy as np
import pandas as pd

SEED = 1848
NX, NY, U = 60, 40, 100.0          # 6 x 4 km
RIVER_COL = 30                      # cell column of the river
BRIDGE_ROW = 20                     # the one bridge
HILL = (48, 30, 90.0, 8.0)          # cx, cy, height_m, sd_cells


def gridby(seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    gx, gy = np.meshgrid(np.arange(NX), np.arange(NY), indexing="ij")
    gx, gy = gx.ravel(), gy.ravel()
    x = gx * U + U / 2
    y = gy * U + U / 2

    pop = rng.poisson(8, NX * NY).astype(float)
    pop[gx == RIVER_COL] = 0.0                       # nobody lives IN the river
    share = 0.10 + 0.50 * gx / (NX - 1)              # planted gradient
    grp = rng.binomial(pop.astype(int), share).astype(float)

    live = pop > 0
    people = pd.DataFrame({"x": x[live], "y": y[live],
                           "count_all": pop[live],
                           "count_group": grp[live]})

    river = (gx == RIVER_COL) & (gy != BRIDGE_ROW)
    friction = pd.DataFrame({"x": x[river], "y": y[river],
                             "friction": 6})

    cx, cy, h, sd = HILL
    altitude = h * np.exp(-((gx - cx) ** 2 + (gy - cy) ** 2)
                          / (2 * sd ** 2))           # per DOMAIN cell

    n_jobs = 2000
    west = rng.normal([12 * U, 20 * U], [6 * U, 6 * U], (int(n_jobs * .7), 2))
    scat = np.c_[rng.uniform(0, NX * U, int(n_jobs * .3)),
                 rng.uniform(0, NY * U, int(n_jobs * .3))]
    jx = np.clip(np.vstack([west, scat]), 0, [NX * U - 1, NY * U - 1])
    jobs = (pd.DataFrame({"x": np.floor(jx[:, 0] / U) * U + U / 2,
                          "y": np.floor(jx[:, 1] / U) * U + U / 2,
                          "jobs": 1.0})
            .groupby(["x", "y"], as_index=False).sum())
    jobs = jobs[~((np.floor(jobs.x / U) == RIVER_COL))]   # not in the river

    meta = {"seed": seed, "nx": NX, "ny": NY, "unit": U,
            "gradient": "minority share 0.10 (west) -> 0.60 (east), linear",
            "river_col": RIVER_COL, "bridge_row": BRIDGE_ROW,
            "hill": {"cx": cx, "cy": cy, "height_m": h},
            "jobs_cluster": "70% west of river around cell (12, 20)",
            "population": float(people.count_all.sum()),
            "minority": float(people.count_group.sum())}
    return {"people": people, "jobs": jobs, "friction": friction,
            "altitude": altitude, "meta": meta}


if __name__ == "__main__":
    g = gridby()
    print({k: (v.shape if hasattr(v, "shape") else len(v))
           for k, v in g.items() if k != "meta"})
    print(g["meta"])
