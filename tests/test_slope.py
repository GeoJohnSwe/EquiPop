"""Slope engine (#4a) validations: regression, invariants, known answer."""
import numpy as np
import pandas as pd
import pytest

from equipop.friction import run_knn_friction
from equipop.slope import (SLOPE_MODELS, slope_penalty, run_knn_slope,
                           dem_to_cell_altitude)

U = 100.0


def _pop_grid(nx, ny, seed=7):
    rng = np.random.default_rng(seed)
    E, N = np.meshgrid(np.arange(nx) * U + U / 2,
                       np.arange(ny) * U + U / 2, indexing="ij")
    return pd.DataFrame({
        "x": E.ravel(), "y": N.ravel(),
        "count_all": rng.integers(1, 9, nx * ny).astype(float),
        "count_group": rng.integers(0, 3, nx * ny).astype(float)})


def test_flat_dem_reproduces_friction_exactly():
    """penalty(0)=1 for every model => flat terrain == plain FARB."""
    pop = _pop_grid(9, 7)
    fr = pd.DataFrame({"x": [350.0, 450.0], "y": [350.0, 350.0],
                       "friction": [3, 3]})       # a small barrier too
    n_cells = ((pop.x.max() - pop.x.min()) / U + 1) \
        * ((pop.y.max() - pop.y.min()) / U + 1)
    flat = np.zeros(int(n_cells))
    base = run_knn_friction(pop, [10, 60], fr=fr, unit_size=U)
    for model in SLOPE_MODELS:
        got = run_knn_slope(pop, [10, 60], altitude=flat, model=model,
                            fr=fr, unit_size=U)
        pd.testing.assert_frame_equal(
            got, base, check_dtype=False, atol=1e-9,
            obj=f"flat-DEM regression, model={model}")


def test_ramp_asymmetry_invariants():
    """Constant 5% ramp: uphill effort > flat; Tobler descent < flat
    (the -5% optimum); linear descent == flat (lambda_down=0)."""
    nx, ny = 21, 3
    pop = _pop_grid(nx, ny, seed=1)
    pop["count_all"] = 1.0                       # 1 person per cell
    alt = 0.05 * (pop["x"].to_numpy())           # 5% ramp along x
    k = nx * ny                                  # reach everyone
    dom = pd.DataFrame({"x": pop.x, "y": pop.y, "alt": alt})

    def col_effort(out):
        west = out[out.EastWest == out.EastWest.min()]
        east = out[out.EastWest == out.EastWest.max()]
        return (west[f"Rounds_{k}"].mean(),      # its far cells lie uphill
                east[f"Rounds_{k}"].mean())      # its far cells lie downhill

    flat = run_knn_slope(pop, [k], altitude=np.zeros(nx * ny),
                         model="tobler", unit_size=U, id_col=None)
    f_west, f_east = col_effort(flat)            # equal by symmetry
    assert np.isclose(f_west, f_east)

    def run(model):
        return col_effort(run_knn_slope(pop, [k], altitude=dom,
                                        model=model, unit_size=U,
                                        id_col=None))

    up_t, down_t = run("tobler")
    assert up_t > f_west, "Tobler: climbing must cost more than flat"
    assert down_t < f_east, "Tobler: gentle descent must cost LESS (the -5% optimum)"
    assert up_t > down_t, "Tobler: asymmetry must point uphill"

    up_l, down_l = run("linear")
    assert up_l > f_west, "linear: climbing must cost more than flat"
    assert np.isclose(down_l, f_east), "linear lambda_down=0: descent flat-priced"


def test_known_answer_three_cells_and_penalties():
    """Hand-computed: three cells in a row, 10 m rise per 100 m step.
    slope +0.1 uphill, -0.1 downhill.
    tobler:  penalty(+0.1)=exp(3.5*0.10)=1.41907, penalty(-0.1)=1.0
    linear5: penalty(+0.1)=1.5,                    penalty(-0.1)=1.0"""
    p_t = slope_penalty("tobler")
    assert np.isclose(p_t(0.1), np.exp(0.35))
    assert np.isclose(p_t(-0.1), 1.0)             # |−0.1+0.05|−0.05 = 0
    assert np.isclose(p_t(-0.05), np.exp(-0.175))  # the descent optimum
    p_l = slope_penalty("linear", lambda_up=5.0)
    assert np.isclose(p_l(0.1), 1.5)
    assert np.isclose(p_l(-0.1), 1.0)

    pop = pd.DataFrame({"x": [50.0, 150.0, 250.0], "y": [50.0] * 3,
                        "count_all": [1.0] * 3, "count_group": [0.0] * 3})
    alt = np.array([0.0, 10.0, 20.0])
    out = run_knn_slope(pop, [3], altitude=alt, model="tobler",
                        unit_size=U, id_col=None).set_index("EastWest")
    # west origin climbs twice: effort = 2 * 1.41907
    assert np.isclose(out.loc[50, "Rounds_3"], 2 * np.exp(0.35), atol=1e-9)
    # east origin descends twice at -0.1: effort = 2 * 1.0
    assert np.isclose(out.loc[250, "Rounds_3"], 2.0, atol=1e-9)


def test_dem_zonal_mean(tmp_path):
    """Synthetic GeoTIFF: 10 m pixels, two 100 m cells with constant
    altitude blocks 5 and 25 -> zonal means exactly 5 and 25."""
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import from_origin
    a = np.zeros((10, 20), dtype="float32")
    a[:, :10] = 5.0
    a[:, 10:] = 25.0
    path = tmp_path / "dem.tif"
    with rasterio.open(path, "w", driver="GTiff", height=10, width=20,
                       count=1, dtype="float32",
                       transform=from_origin(0, 100, 10, 10),
                       crs="EPSG:32633") as dst:
        dst.write(a, 1)
    alt = dem_to_cell_altitude(str(path), E=[50.0, 150.0], N=[50.0, 50.0],
                               unit_size=100.0)
    assert np.allclose(alt, [5.0, 25.0])


def test_slope_friction_scales_with_step_length():
    """BACKLOG 139: under slope too, friction is a delay per unit
    TRAVELLED - cost = step * (penalty(slope) + friction).

    A mutant writing `step * penalty(s) + friction` passed the whole
    suite, INCLUDING test_flat_dem_reproduces_friction_exactly. That
    fixture carries friction 3, high enough that every shortest path
    routes AROUND the barrier, so no path ever enters a friction cell
    and the scaling rule is never exercised. Friction 1 here is cheap
    enough that the diagonal THROUGH it is the shortest path, which
    is what makes the two rules distinguishable.
    """
    from equipop.friction import FrictionGrid
    from equipop.slope import SlopeGrid

    xs = [0, 0, 0, U, U, U, 2 * U, 2 * U, 2 * U]
    ys = [0, U, 2 * U, 0, U, 2 * U, 0, U, 2 * U]
    pop = pd.DataFrame({"x": xs, "y": ys,
                        "count_all": 1.0, "count_group": 0.0})
    fr = pd.DataFrame({"x": [U], "y": [U], "friction": [1.0]})
    flat = np.zeros(9)

    u = int(U)
    root2 = 2.0 ** 0.5
    idx = {(int(x / U), int(y / U)): i
           for i, (x, y) in enumerate(zip(xs, ys))}

    fg = FrictionGrid(pop, fr, unit_size=U)
    origin = int(((0 - fg.x0) // u) * fg.ny + ((0 - fg.y0) // u))
    want = fg.rounds_from(np.array([origin]))[0]

    # the absolute truth, independent of the friction engine
    assert np.isclose(want[idx[(1, 1)]], root2 * 2.0, rtol=1e-12)

    for model in SLOPE_MODELS:
        sg = SlopeGrid(pop, fr, unit_size=U, altitude=flat, model=model)
        got = sg.rounds_from(np.array([origin]))[0]
        assert np.allclose(got, want, rtol=0, atol=1e-9), (
            f"flat DEM must reproduce friction EXACTLY, model={model}")
        assert np.isclose(got[idx[(1, 1)]], root2 * 2.0, rtol=1e-12), (
            f"diagonal into friction 1 must cost sqrt(2)*(1+1), "
            f"model={model}")
