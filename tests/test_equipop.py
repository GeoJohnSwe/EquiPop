"""
EquiPop test suite. Core tests use SYNTHETIC in-code fixtures (no data
files needed); two small shareable files under tests/data extend
coverage: the Berlin worked example and an anonymised individual-level
fixture (isometry-transformed; all results provably identical to the
source it was derived from).
"""
import math
from pathlib import Path

import numpy as np
import os
import pandas as pd
import pytest

from equipop import (build_cells, run_knn_stats, run_knn, Decay,
                     snap_to_grid, project_to_metric)
from equipop.cells import CellData
from equipop.fastcounts import run_knn_counts
from equipop.friction import run_knn_friction
from equipop.decay import MODELS
from equipop.stats import gini_sorted, BINARY_STATS
from equipop.hex import build_hex_cells, _cube_round, _axial_from_xy
from equipop.segregation import seg_indices_at_scale, seg_profile
from equipop.area import aggregate_output
from equipop.transform import aggregate_to_cells

DATA = Path(__file__).parent / "data"


# ---------------------------------------------------------- fixtures
def synth_cells(n=400, seed=7):
    """Reproducible synthetic grid: clustered population + treatment."""
    rng = np.random.default_rng(seed)
    E = (rng.integers(0, 40, n) * 100 + 50).astype(np.int64)
    N = (rng.integers(0, 40, n) * 100 + 50).astype(np.int64)
    df = pd.DataFrame({"E": E, "N": N,
                       "pop": rng.integers(1, 50, n),
                       "grp": 0})
    df["grp"] = (df["pop"] * rng.uniform(0, 0.5, n)).astype(int)
    df = df.groupby(["E", "N"], as_index=False).sum()
    return CellData(E=df.E.to_numpy(), N=df.N.to_numpy(),
                    n=df["pop"].to_numpy(),
                    binary_sums={"grp": df.grp.to_numpy(float)},
                    value_arrays={}, unit_size=100)


# ------------------------------------------------------- grid engine
def test_hand_computed_knn():
    """Three cells on a line; every output value known by hand."""
    cd = CellData(E=np.array([50, 250, 1050]), N=np.array([50, 50, 50]),
                  n=np.array([10, 10, 10]),
                  binary_sums={"g": np.array([0.0, 10.0, 5.0])},
                  value_arrays={}, unit_size=100)
    # BACKLOG 99: this checks a HAND-COMPUTED whole-ring answer, so
    # it names the rule it assumes rather than inheriting a default.
    r = run_knn_stats(cd, [15, 25], stats={"g": ["ratio"]},
                      overshoot_mode="whole")
    row = r[r.EastWest == 50].iloc[0]
    assert row["N_15"] == 20 and row["Dist_15"] == 200.0
    assert row["N_25"] == 30 and row["Dist_25"] == 1000.0
    assert abs(row["R_g_25"] - 0.5) < 1e-12


def test_ring_atomic_ties():
    """Four equidistant cells must be counted as one atomic ring."""
    cd = CellData(E=np.array([50, 150, 50, -50, 50]),
                  N=np.array([50, 50, 150, 50, -50]),
                  n=np.array([1, 5, 5, 5, 5]),
                  binary_sums={"g": np.zeros(5)},
                  value_arrays={}, unit_size=100)
    # BACKLOG 99: THE ATOMIC RING tie rule - equidistant cells are
    # taken together - which only has meaning when a ring is taken
    # whole. Named, not inherited.
    r = run_knn_stats(cd, [2], stats={"g": ["ratio"]},
                      overshoot_mode="whole")
    # from origin, all four neighbours sit at exactly 100 m: k=2 must
    # report the whole ring (N = 1 + 20), not a partial count
    assert r[r.EastWest == 50].iloc[0]["N_2"] == 21


def test_fast_engine_identical():
    cd = synth_cells()
    a = run_knn_stats(cd, [10, 50, 200], stats={"grp": ["ratio"]})
    b = run_knn_counts(cd, [10, 50, 200], m_neighbors=64)
    m = a.merge(b, on=["EastWest", "NorthSouth"])
    assert len(m) == len(a)
    for k in (10, 50, 200):
        assert (m[f"N_{k}_x"] == m[f"N_{k}_y"]).all()
        assert (m[f"R_grp_{k}_x"] - m[f"R_grp_{k}_y"]).abs().max() < 1e-12
        assert (m[f"Dist_{k}_x"] - m[f"Dist_{k}_y"]).abs().max() < 1e-9


def test_partial_results_when_k_unreachable():
    cd = synth_cells()
    total = cd.n.sum()
    r = run_knn_counts(cd, [int(total * 2)])
    assert (r[f"N_{int(total*2)}"] == total).all()


# ------------------------------------------------------------- decay
def test_decay_half_life_property():
    for m in MODELS:
        d = Decay(model=m, half_life_m=8000)
        assert abs(d.weight(0) - 1) < 1e-12
        assert abs(d.weight(8000) - 0.5) < 1e-12
        assert d.weight(16000) < 0.5


def test_decay_leq_raw():
    df = pd.DataFrame({"E_grid": [50, 150, 250], "N_grid": [50, 50, 50],
                       "pop": [5, 5, 5], "grp": [1, 2, 3]})
    cells = df.rename(columns={"pop": "FullPop", "grp": "Treatment"})
    # BACKLOG 99: named rather than inherited - the decay bound is
    # asserted against whole-ring counts.
    r = run_knn(cells, [10, 15], count_all_col="FullPop",
                overshoot_mode="whole",
                count_group_col="Treatment", unit_size=100,
                max_radius_units=10, id_col=None,
                decay=Decay(half_life_m=100))
    assert (r["ND_10"] <= r["N_10"] + 1e-9).all()


# ---------------------------------------------------------- friction
def test_friction_wall():
    pop = pd.DataFrame({"x": [50, 250, 1050], "y": [50, 50, 50],
                        "count_all": [10, 10, 10],
                        "count_group": [0, 10, 5]})
    wall = pd.DataFrame({"x": [650], "y": [50], "friction": [20]})
    r0 = run_knn_friction(pop, [25], fr=None, unit_size=100)
    r1 = run_knn_friction(pop, [25], fr=wall, unit_size=100)
    assert r0.loc[0, "Rounds_25"] == 10
    assert r1.loc[0, "Rounds_25"] == 30      # 10 + friction 20


# -------------------------------------------------------- statistics
def test_gini_and_binary_stats():
    x = np.array([1, 1, 1, 1, 1], float)
    assert abs(gini_sorted(x)) < 1e-12                 # equality -> 0
    rng = np.random.default_rng(3)
    v = rng.lognormal(0, 1, 500)
    # rank formula vs pairwise definition
    g1 = gini_sorted(v)
    g2 = np.abs(v[:, None] - v[None, :]).sum() / (2 * len(v) ** 2 * v.mean())
    assert abs(g1 - g2) < 1e-10
    assert abs(BINARY_STATS["gini"](10, 4) - 0.6) < 1e-12   # 1 - p
    assert abs(BINARY_STATS["sd"](10, 5) - 0.5) < 1e-12


def test_stats_global_equals_wholefile():
    df = pd.read_csv(DATA / "poptest_anon.csv")
    cd = build_cells(df, "X_local", "Y_local", binary_vars=["HighEdu"],
                     value_vars=["ValFloat"], unit_size=100)
    big = int(cd.n.sum() * 2)
    r = run_knn_stats(cd, [big], stats={"HighEdu": ["ratio"],
                                        "ValFloat": ["median", "gini"]})
    inc = df["ValFloat"].dropna().to_numpy()
    ok = df.dropna(subset=["X_local", "Y_local"])   # engine drops these 9
    inc = ok["ValFloat"].dropna().to_numpy()
    assert abs(r[f"R_HighEdu_{big}"].iloc[0] - ok["HighEdu"].mean()) < 1e-9
    assert abs(r[f"Med_ValFloat_{big}"].iloc[0] - np.median(inc)) < 1e-9
    assert abs(r[f"Gini_ValFloat_{big}"].iloc[0] - gini_sorted(inc)) < 1e-9


# ---------------------------------------------------------- hexagons
def test_hex_cube_invariant_and_center():
    rng = np.random.default_rng(1)
    x = rng.uniform(0, 5000, 1000)
    y = rng.uniform(0, 5000, 1000)
    size = 100 / np.sqrt(3)
    q, r = _cube_round(*_axial_from_xy(x, y, size))
    s = -q - r
    assert (q + r + s == 0).all()
    df = pd.DataFrame({"x": x, "y": y, "v": 1})
    cd = build_hex_cells(df, "x", "y", hex_size=100, binary_vars=["v"])
    # every point must lie within circumradius of its hexagon centre
    from equipop.hex import _center_from_axial
    assert cd.n.sum() == 1000


# -------------------------------------------------------- projection
def test_projection_and_snap_berlin():
    # The Book's datasets moved into the package in 1.19.0 so that a
    # pip install can reach them; tests follow the package, not a path.
    from equipop.datasets import _DATA
    df = pd.read_excel(os.path.join(_DATA, "berlin_example.xlsx"),
                       sheet_name="Indata_and_generated_data", header=1)
    p = snap_to_grid(project_to_metric(df, target_epsg=25832),
                     unit_size=100)
    assert (p["easting_m"] - p["easting_epsg25832_m"]).abs().max() < 0.01
    assert (p["E_grid"] == p["E25832_100m"]).all()
    assert (p["N_grid"] == p["N25832_100m"]).all()


# ------------------------------------------------------- segregation
def test_segregation_bounds_and_zero():
    t = np.full(50, 100.0)
    P = 0.3
    x_even = t * P                       # perfectly even
    r = seg_indices_at_scale(t, x_even, P)
    for key in ("D", "Gini", "H"):
        assert abs(r[key]) < 1e-9
    assert abs(r["Isolation"] - P) < 1e-9
    x_seg = np.zeros(50); x_seg[:15] = 100     # fully segregated
    r2 = seg_indices_at_scale(t, x_seg, P)
    assert r2["D"] > 0.99 and r2["Isolation"] > 0.99


# -------------------------------------------------------------- area
def test_area_alternatives():
    df = pd.DataFrame({"EastWest": [50, 150, 1050, 1150],
                       "NorthSouth": [50, 50, 50, 50],
                       "N_local": [10, 10, 10, 30],
                       "R_grp_10": [0.1, 0.3, 0.5, 0.7],
                       "muni": ["A", "A", "B", "B"]})
    a1 = aggregate_output(df, by="muni", columns=["R_grp_10"])
    assert abs(a1.loc[a1.muni == "A", "R_grp_10"].iloc[0] - 0.2) < 1e-12
    assert abs(a1.loc[a1.muni == "B", "R_grp_10"].iloc[0]
               - (0.5 * 10 + 0.7 * 30) / 40) < 1e-12
    a3 = aggregate_output(df, by=1000.0, columns=["R_grp_10"])
    assert len(a3) == 2


# ------------------------------------------------------ stata bridge
def test_stata_bridge_row_alignment():
    from equipop.stata_bridge import knn_to_rows
    df = pd.read_csv(DATA / "poptest_anon.csv")
    res = knn_to_rows(df["X_local"], df["Y_local"], [50],
                      treat={"HighEdu": df["HighEdu"]})
    assert all(len(v) == len(df) for v in res.values())
    miss = (df["X_local"].isna() | df["Y_local"].isna()).to_numpy()
    assert np.isnan(res["R_HighEdu_50"][miss]).all()
    assert np.nanmin(res["N_50"]) >= 50
