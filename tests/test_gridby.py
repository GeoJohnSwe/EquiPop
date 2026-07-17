"""Gridby planted truths must be recoverable, or the city is fired."""
import numpy as np
import pandas as pd

from equipop.datasets import load
from equipop.cells import CellData
from equipop.fastcounts import run_knn_counts
from equipop.friction import run_knn_friction


def test_gridby_planted_truths():
    g = load("gridby")
    p = g["people"]
    # deterministic
    assert load("gridby")["meta"] == g["meta"]

    # 1. the gradient: west-edge context share ~0.1ish, east ~0.6ish
    cd = CellData(E=p.x.to_numpy(), N=p.y.to_numpy(),
                  n=p.count_all.to_numpy(),
                  binary_sums={"g": p.count_group.to_numpy()},
                  value_arrays={}, unit_size=100.0)
    out = run_knn_counts(cd, [400])
    west = out[out.EastWest < 500]["R_g_400"].mean()
    east = out[out.EastWest > 5500]["R_g_400"].mean()
    assert west < 0.18 and east > 0.50 and east - west > 0.3

    # 2. the river: a 3-round isochrone from a river-hugging cell
    # holds far fewer people than from an interior cell (half the
    # disk is behind a friction-6 wall)
    fr = g["friction"]
    res = run_knn_friction(p, [], fr=fr, unit_size=100.0,
                           tau_values=[3])
    res = res.set_index(["EastWest", "NorthSouth"])
    hug = res[res.index.get_level_values(0).isin([2950, 3150])
              ]["N_tau3"].median()
    interior = res[res.index.get_level_values(0).isin([1050, 4950])
                   ]["N_tau3"].median()
    assert hug < 0.72 * interior      # the wall visibly bites

    # 3. the hill: altitude peak where planted
    alt = g["altitude"].reshape(60, 40)
    cx, cy = np.unravel_index(alt.argmax(), alt.shape)
    assert (cx, cy) == (48, 30) and abs(alt.max() - 90) < 1

    # 4. jobs cluster: >60% of jobs west of the river
    j = g["jobs"]
    assert j[j.x < 3000].jobs.sum() / j.jobs.sum() > 0.6


def test_datasets_loader_municipality():
    p, j = load("municipality")
    assert len(j) == 870 and np.isclose(j.Jobs.sum(), 7142)
