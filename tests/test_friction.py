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
    u = int(U)
    origin = int(((0 - g.x0) // u) * g.ny + ((0 - g.y0) // u))
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
