"""#11 FCA validations: hand-computed 2SFCA/3SFCA, kFCA ties,
doubly-constrained margins, segmentation, effort reach."""
import numpy as np
import pandas as pd

from equipop.fca import fca, fca_segments, _k_mask
from equipop.decay import Decay


def _line():
    demand = pd.DataFrame({"x": [0.0, 100.0, 200.0], "y": 0.0,
                           "workers": [10.0, 20.0, 30.0]})
    supply = pd.DataFrame({"x": [0.0, 200.0], "y": 0.0,
                           "jobs": [5.0, 8.0]})
    return demand, supply


def test_2sfca_hand_computed():
    """W = [[1,0],[1,1],[0,1]] at r=100 =>
    R = [5/30, 8/50]; A = [1/6, 1/6+0.16, 0.16]."""
    demand, supply = _line()
    d, s = fca(demand, supply, "workers", "jobs", reach="r", r=100.0)
    assert np.allclose(s["R"], [5 / 30, 8 / 50])
    assert np.allclose(d["A"], [1 / 6, 1 / 6 + 0.16, 0.16])
    assert np.allclose(d["J"], [5.0, 13.0, 8.0])   # step-1 raw potential


def test_3sfca_hand_computed():
    """G = [[1,0],[.5,.5],[0,1]]; effective W = G*W =>
    R = [5/20, 8/40] = [0.25, 0.2]; A = [0.25, 0.225, 0.2]."""
    demand, supply = _line()
    d, s = fca(demand, supply, "workers", "jobs", reach="r", r=100.0,
               method="3sfca")
    assert np.allclose(s["R"], [0.25, 0.2])
    assert np.allclose(d["A"], [0.25, 0.225, 0.2])


def test_kfca_mask_with_atomic_tie():
    """Homes gather k=3 jobs; the middle home sees BOTH workplaces at
    d=100 - the tie ring enters wholly (EquiPop convention)."""
    D = np.array([[0.0, 200.0], [100.0, 100.0], [200.0, 0.0]])
    mask = _k_mask(D, np.array([3.0, 1.0]), k=3)
    assert (mask == np.array([[True, False],
                              [True, True],
                              [True, True]])).all()


def test_balanced_margins_reproduced():
    rng = np.random.default_rng(3)
    demand = pd.DataFrame({"x": rng.uniform(0, 1000, 12),
                           "y": rng.uniform(0, 1000, 12),
                           "workers": rng.uniform(5, 30, 12)})
    supply = pd.DataFrame({"x": rng.uniform(0, 1000, 7),
                           "y": rng.uniform(0, 1000, 7),
                           "jobs": rng.uniform(10, 60, 7)})
    dec = Decay(model="negexp", half_life_m=400.0)
    d, s = fca(demand, supply, "workers", "jobs", decay=dec,
               reach="decay", balance=500)
    # flows are gauge-invariant: rebuild up to one scalar and check margins
    from equipop.fca import _weights
    W = _weights(demand.assign(_D=demand.workers),
                 supply.assign(_S=supply.jobs), dec, "decay",
                 None, None, 1e-6, {})
    Dm = demand.workers.to_numpy(); Sm = supply.jobs.to_numpy()
    sf = Dm.sum() / Sm.sum()
    M = (Dm / d["A"].to_numpy())[:, None] * W \
        * (Sm * sf / s["C"].to_numpy())[None, :]
    F = M * (Dm.sum() / M.sum())
    assert np.allclose(F.sum(1), Dm, rtol=1e-7)       # workers conserved
    assert np.allclose(F.sum(0), Sm * sf, rtol=1e-7)  # scaled jobs margin
    # gauge convention: demand-weighted mean A == global S/D exactly
    assert np.isclose(np.average(d["A"], weights=Dm), Sm.sum() / Dm.sum())
    assert np.isclose(np.average(s["C"], weights=Sm), 1.0)


def test_segments_orchestrator_matches_single_runs():
    demand, supply = _line()
    demand["low_workers"] = [5.0, 5.0, 10.0]
    supply["low_jobs"] = [2.0, 3.0]
    segs = [{"name": "all", "demand_col": "workers",
             "supply_col": "jobs"},
            {"name": "low", "demand_col": "low_workers",
             "supply_col": "low_jobs"}]
    d, s = fca_segments(demand, supply, segs, reach="r", r=100.0)
    d_all, _ = fca(demand, supply, "workers", "jobs", reach="r", r=100.0)
    d_low, _ = fca(demand, supply, "low_workers", "low_jobs",
                   reach="r", r=100.0)
    assert np.allclose(d["A_all"], d_all["A"])
    assert np.allclose(d["A_low"], d_low["A"])
    assert {"R_all", "R_low"} <= set(s.columns)


def test_effort_reach_flat_brute():
    """Flat DEM: effort = Chebyshev moves; brute-check A for 2SFCA."""
    U = 100.0
    demand = pd.DataFrame({"x": [U / 2, 2 * U + U / 2], "y": U / 2,
                           "workers": [4.0, 6.0]})
    supply = pd.DataFrame({"x": [U / 2], "y": [U / 2], "jobs": [3.0]})
    dec = Decay(model="negexp", half_life_m=1.0)   # 1 ROUND
    n_dom = 3 * 1
    d, s = fca(demand, supply, "workers", "jobs", decay=dec,
               reach="effort", altitude=np.zeros(n_dom),
               model="tobler", roundtrip=True, unit_size=U)
    w = dec.weight_vec(np.array([0.0, 2.0]))       # Chebyshev rounds
    R = 3.0 / (w[0] * 4.0 + w[1] * 6.0)
    assert np.allclose(s["R"], [R])
    assert np.allclose(d["A"], [w[0] * R, w[1] * R], rtol=1e-9)


def test_real_labour_market_fixture_regression():
    """Anonymised (joint-isometry) municipality fixture: results are
    IDENTICAL to the original register run - checkpoints recorded at
    build time (v1.5.1). Jobs pre-filtered to the residential bbox
    BEFORE the isometry (axis-aligned boxes are not isometry-
    invariant - learned loudly)."""
    import os
    base = os.path.join(os.path.dirname(__file__), "data")
    pl = pd.read_csv(os.path.join(base, "people_syn.csv"))
    jl = pd.read_csv(os.path.join(base, "jobs_syn.csv"))
    assert len(jl) == 870 and np.isclose(jl.Jobs.sum(), 7142)
    segs = [{"name": "all", "demand_col": "Working_sum",
             "supply_col": "Jobs"},
            {"name": "low", "demand_col": "LowEdu_sum",
             "supply_col": "LowEdu_jobs"}]
    d, s = fca_segments(pl, jl, segs,
                        decay=Decay(model="negexp", half_life_m=3000.0))
    w = d.Working_sum.to_numpy()
    a = d.A_all[w > 0]
    assert np.isclose(np.percentile(a, 10), 0.191093, atol=1e-5)
    assert np.isclose(np.percentile(a, 90), 0.788133, atol=1e-5)
    assert np.isclose(np.average(d.A_all, weights=np.maximum(w, 0)),
                      0.629639, atol=1e-5)          # = global S/D
    gap = (d.A_low / np.maximum(d.A_all, 1e-9))[(w > 0)
                                                & (d.LowEdu_sum > 0)]
    assert np.isclose(np.median(gap), 0.241364, atol=1e-5)
