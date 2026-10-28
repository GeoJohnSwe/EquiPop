"""v1.15 friction additions."""
import numpy as np
import pytest


def test_features_to_friction_reproduces_gridby_river():
    """THE validation: Gridby's river drawn as LINE features must
    reproduce the CSV-barrier cells exactly - and two overlapping
    features must stack additively."""
    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import LineString
    from equipop.friction import features_to_friction
    from equipop.datasets import load

    g = load("gridby")
    ref = g["friction"]                       # 39 cells, value 6
    # the river as two line segments along x=3050, skipping the
    # bridge cell (row 20 => y in [2000, 2100))
    south = LineString([(3050, 0), (3050, 1999.9)])
    north = LineString([(3050, 2100.1), (3050, 4000)])
    gdf = gpd.GeoDataFrame({"friction": [6, 6]},
                           geometry=[south, north], crs=None)
    out = features_to_friction(gdf, unit_size=100.0)
    a = set(zip(ref.x, ref.y))
    b = set(zip(out.x, out.y))
    assert a == b                              # same cells exactly
    assert (out.friction == 6).all()
    # additive stacking: a railway crossing one river cell
    rail = LineString([(3000, 550), (3100, 550)])
    gdf2 = gpd.GeoDataFrame({"friction": [6, 6, 4]},
                            geometry=[south, north, rail], crs=None)
    out2 = features_to_friction(gdf2, unit_size=100.0)
    hit = out2[(out2.x == 3050) & (out2.y == 550)]
    assert np.isclose(hit.friction.iloc[0], 10.0)   # 6 + 4


def test_friction_scales_with_step_length():
    """BACKLOG 139: friction is a delay per unit TRAVELLED.

    Entering a friction-1 cell DIAGONALLY must cost sqrt(2)*(1+1),
    not sqrt(2)+1. The two rules are algebraically identical on open
    ground (friction 0) and on every orthogonal move (step 1), so
    ONLY a diagonal move into a friction cell tells them apart.

    This test exists because it did not. A mutant that scaled the
    step but added friction unscaled passed the entire suite - 353
    tests - because nothing crossed a barrier on the diagonal. A
    guard that has never fired is a hypothesis.
    """
    import pandas as pd
    from equipop.friction import FrictionGrid

    U = 100.0
    xs = [0, 0, 0, U, U, U, 2 * U, 2 * U, 2 * U]
    ys = [0, U, 2 * U, 0, U, 2 * U, 0, U, 2 * U]
    pop = pd.DataFrame({"x": xs, "y": ys,
                        "count_all": 1.0, "count_group": 0.0})
    fr = pd.DataFrame({"x": [U], "y": [U], "friction": [1.0]})

    g = FrictionGrid(pop, fr, unit_size=U)
    # the grid's own rule for finding a node (v1.63.0, BACKLOG 446;
    # this line used to repeat the old corner arithmetic)
    origin = int(g.node_of(0.0, 0.0))
    r = g.rounds_from(np.array([origin]))[0]

    root2 = 2.0 ** 0.5
    idx = {(int(x / U), int(y / U)): i
           for i, (x, y) in enumerate(zip(xs, ys))}

    # THE discriminating cell: reached by one diagonal step into
    # friction 1.  correct sqrt(2)*(1+1) = 2.8284;  wrong sqrt(2)+1
    assert np.isclose(r[idx[(1, 1)]], root2 * 2.0, rtol=1e-12)
    assert not np.isclose(r[idx[(1, 1)]], root2 + 1.0, rtol=1e-6)

    # orthogonal steps over open ground are unchanged at exactly 1
    assert np.isclose(r[idx[(0, 1)]], 1.0, rtol=1e-12)
    assert np.isclose(r[idx[(1, 0)]], 1.0, rtol=1e-12)
    assert np.isclose(r[idx[(0, 2)]], 2.0, rtol=1e-12)

    # a diagonal over OPEN ground costs sqrt(2), so (1,2) is reached
    # from (0,1) for 1 + sqrt(2) - cheaper than going round
    assert np.isclose(r[idx[(1, 2)]], 1.0 + root2, rtol=1e-12)
    assert np.isclose(r[idx[(2, 1)]], 1.0 + root2, rtol=1e-12)

    # and the far corner routes AROUND the friction cell, not through
    assert np.isclose(r[idx[(2, 2)]], 2.0 + root2, rtol=1e-12)


def test_equal_efforts_reached_by_different_steps_are_one_ring(tmp_path):
    """v1.63.0, BACKLOG 447. One ring is every cell at the same effort,
    within overshoot.RING_TOL - as in the radial engines.

    Found while checking fractional cell sizes: a 5 x 5 town of ten
    people a cell, one column of friction 1, the origin in that column
    on the edge. Cell (4, 4) is reached at 1 + 3*sqrt(2) and cell
    (1, 3) at (1 + sqrt(2)) + 2*sqrt(2): the same effort, 5.2426...,
    which Dijkstra's additions end in ...285 and ...286. 22 cells (220
    people) are nearer; k = 225 crosses the ring of those two.

    BROKEN WITH: the ring gathered by exact equality again (whole then
    admits (4, 4) alone, N = 230, a direction picked by the last bit
    of a sum)."""
    import io
    from contextlib import redirect_stdout
    import pandas as pd
    from equipop import overshoot
    from equipop.stata_bridge import dispatch

    xs = [100.0 * i + 50 for i in range(5) for _ in range(5)]
    ys = [100.0 * j + 50 for _ in range(5) for j in range(5)]
    p = tmp_path / "band.csv"
    pd.DataFrame({"x": xs, "y": ys,
                  "friction": [1.0 if x == 150.0 else 0.0 for x in xs]}
                 ).to_csv(p, index=False)
    mark = [1.0 if (x, y) == (150.0, 350.0) else 0.0      # cell (1, 3)
            for x, y in zip(xs, ys)]
    origin = list(zip(xs, ys)).index((150.0, 50.0))
    for mode, n_want, t_want in ((overshoot.WHOLE, 240.0, 10.0),
                                 (overshoot.PROPORTIONAL, 225.0, 2.5)):
        with redirect_stdout(io.StringIO()):
            out = dispatch("friction", xs, ys, unit_size=100.0,
                           weight=[10.0] * 25, k_values=[225],
                           treat={"g": [10.0 * m for m in mark]},
                           treat_are_counts=True, friction_file=str(p),
                           overshoot_mode=mode)
        assert float(out["N_225"][origin]) == n_want, mode
        # proportional takes the same share of BOTH cells: 5 of 20
        # people, so a quarter of (1, 3)'s ten
        assert float(out["T_g_225"][origin]) == pytest.approx(t_want), mode
