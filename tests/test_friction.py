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
