"""v1.4.0 Access release: round-trip slopes, gamma power, potential."""
import numpy as np
import pandas as pd

from equipop.friction import run_knn_friction
from equipop.slope import run_knn_slope
from equipop.decay import Decay
from equipop.access import (potential_surface, opportunity_horizon,
                            effort_potential)

U = 100.0


def _line_pop(nx=3):
    return pd.DataFrame({"x": np.arange(nx) * U + U / 2,
                         "y": [U / 2] * nx,
                         "count_all": [1.0] * nx,
                         "count_group": [0.0] * nx})


def test_roundtrip_flat_equals_oneway():
    """Flat DEM: out and back are symmetric -> RT per-leg average is
    EXACTLY the one-way result (and hence exactly plain FARB)."""
    rng = np.random.default_rng(4)
    n = 8
    pop = pd.DataFrame({
        "x": np.repeat(np.arange(n), n) * U + U / 2,
        "y": np.tile(np.arange(n), n) * U + U / 2,
        "count_all": rng.integers(1, 5, n * n).astype(float),
        "count_group": 0.0})
    flat = np.zeros(n * n)
    one = run_knn_slope(pop, [20], altitude=flat, model="tobler",
                        unit_size=U)
    rt = run_knn_slope(pop, [20], altitude=flat, model="tobler",
                       unit_size=U, roundtrip=True)
    pd.testing.assert_frame_equal(rt, one, check_dtype=False, atol=1e-9)


def test_roundtrip_known_answer_and_invariants():
    """3-cell 10% ramp, Tobler:
    one-way west->all = 2 climbs = 2*e^0.35; back = 2 descents = 2*1.
    RT per-leg = (2e^0.35 + 2)/2 = e^0.35 + 1.  Symmetric: east == west."""
    pop = _line_pop(3)
    alt = np.array([0.0, 10.0, 20.0])
    rt = run_knn_slope(pop, [3], altitude=alt, model="tobler",
                       unit_size=U, roundtrip=True,
                       id_col=None).set_index("EastWest")
    expect = np.exp(0.35) + 1.0
    assert np.isclose(rt.loc[50, "Rounds_3"], expect, atol=1e-9)
    assert np.isclose(rt.loc[250, "Rounds_3"], expect, atol=1e-9)  # symmetry
    # RT over varied terrain must exceed flat (convexity)
    flatv = run_knn_slope(pop, [3], altitude=np.zeros(3),
                          model="tobler", unit_size=U, roundtrip=True,
                          id_col=None).set_index("EastWest")
    assert (rt["Rounds_3"] > flatv["Rounds_3"] - 1e-12).all()
    assert rt.loc[50, "Rounds_3"] > flatv.loc[50, "Rounds_3"]
    # linear with free descent: RT per-leg = 1 + lambda_up*s/2 per move
    rtl = run_knn_slope(pop, [3], altitude=alt, model="linear",
                        lambda_up=5.0, unit_size=U, roundtrip=True,
                        id_col=None).set_index("EastWest")
    assert np.isclose(rtl.loc[50, "Rounds_3"], 2 * (1 + 5.0 * 0.1 / 2))


def test_gamma_power_exact_half_life_and_legacy():
    for g in (0.5, 1.0, 2.0, 5.0):
        dc = Decay(model="power", half_life_m=2000, gamma=g)
        assert np.isclose(dc.weight(2000.0), 0.5)
        assert np.isclose(dc.weight(0.0), 1.0)
        assert np.allclose(dc.weight_vec([0.0, 2000.0]), [1.0, 0.5])
    g1 = Decay(model="power", half_life_m=2000, gamma=1.0)
    d = np.array([0.0, 1000.0, 6000.0])
    assert np.allclose(g1.weight_vec(d), 1.0 / (1.0 + d / 2000.0))
    legacy = Decay(model="power", half_life_m=2000)     # +1m shifted form
    assert np.isclose(legacy.weight(2000.0), 0.5)
    assert np.isclose(legacy.weight(1000.0),
                      (1001.0) ** (np.log(0.5) / np.log(2001.0)))


def test_potential_surface_fft_vs_brute():
    rng = np.random.default_rng(6)
    n = 40
    mass = pd.DataFrame({"x": rng.integers(0, 12, n) * U + U / 2,
                         "y": rng.integers(0, 12, n) * U + U / 2,
                         "mass": rng.uniform(0.5, 3.0, n)})
    dec = Decay(model="negexp", half_life_m=300.0)
    surf = potential_surface(mass, dec, unit_size=U, eps=1e-12)
    # brute force at every surface midpoint
    mE = (np.floor(mass.x / U) * U + U / 2).to_numpy()
    mN = (np.floor(mass.y / U) * U + U / 2).to_numpy()
    for i in rng.choice(len(surf), 25, replace=False):
        x0, y0 = surf.x.iloc[i], surf.y.iloc[i]
        d = np.hypot(mE - x0, mN - y0)
        a = (dec.weight_vec(d) * mass.mass.to_numpy()).sum()
        assert np.isclose(surf.potential.iloc[i], a, rtol=1e-9, atol=1e-9)


def test_opportunity_horizon():
    dec = Decay(model="negexp", half_life_m=1000.0)
    assert np.isclose(opportunity_horizon(dec), 1000.0 / np.log(2.0))
    # numeric path (gamma power): argmax of r*w(r) is finite and > 0
    g2 = Decay(model="power", half_life_m=1000.0, gamma=2.0)
    s = (2 ** 0.5 - 1) / 1000.0
    assert np.isclose(opportunity_horizon(g2), 1.0 / s)   # analytic
    g_half = Decay(model="power", half_life_m=1000.0, gamma=0.5)
    assert np.isinf(opportunity_horizon(g_half))          # no horizon
    # numeric fallback path (expsqrt): finite, matches fine brute
    es = Decay(model="expsqrt", half_life_m=1000.0)
    r_star = opportunity_horizon(es)
    r = np.linspace(1, 100000, 400000)
    assert np.isclose(r_star, r[np.argmax(r * es.weight_vec(r))],
                      rtol=5e-3)


def test_effort_potential_brute_flat():
    """Flat DEM, roundtrip: effort = Chebyshev moves; brute-check A."""
    n = 5
    pop = pd.DataFrame({
        "x": np.repeat(np.arange(n), n) * U + U / 2,
        "y": np.tile(np.arange(n), n) * U + U / 2,
        "count_all": 1.0})
    mass = pd.DataFrame({"x": [U / 2, 4 * U + U / 2],
                         "y": [U / 2, 4 * U + U / 2],
                         "mass": [2.0, 3.0]})
    dec = Decay(model="negexp", half_life_m=2.0)   # half-life 2 ROUNDS
    res = effort_potential(pop, mass, dec, altitude=np.zeros(n * n),
                           model="tobler", roundtrip=True,
                           unit_size=U).set_index(["x", "y"])
    gx, gy = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    for (px, py), row in res.iterrows():
        i, j = int((px - U / 2) // U), int((py - U / 2) // U)
        cheb = np.maximum(np.abs(np.array([0, 4]) - i),
                          np.abs(np.array([0, 4]) - j)).astype(float)
        a = (dec.weight_vec(cheb) * np.array([2.0, 3.0])).sum()
        assert np.isclose(row["A"], a, rtol=1e-9)
