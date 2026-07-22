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


def test_paths_to_friction_twin_and_conventions():
    """#21d: the geopandas-FREE rasterizer must match the shapely twin
    cell-for-cell on random lines and polygons (incl. a hole), and
    honour the conventions: corner kiss free, one charge per feature
    per cell, additive stacking."""
    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import LineString, Polygon
    from equipop.friction import features_to_friction, paths_to_friction

    rng = np.random.default_rng(1848)
    lines, feats, vals = [], [], []
    for _ in range(15):
        pts = rng.uniform(0, 2500, (rng.integers(2, 6), 2))
        lines.append(LineString(pts))
        feats.append({"type": "line", "parts": [list(map(tuple, pts))]})
        vals.append(float(rng.integers(1, 9)))
    a = features_to_friction(
        gpd.GeoDataFrame({"friction": vals}, geometry=lines),
        unit_size=100).sort_values(["x", "y"]).reset_index(drop=True)
    b = paths_to_friction(feats, vals, unit_size=100) \
        .sort_values(["x", "y"]).reset_index(drop=True)
    assert a.equals(b)

    polys, feats2, vals2 = [], [], []
    for _ in range(8):
        c = rng.uniform(300, 2200, 2)
        ang = np.sort(rng.uniform(0, 2 * np.pi, rng.integers(3, 8)))
        r = rng.uniform(80, 350)
        pts = np.c_[c[0] + r * np.cos(ang), c[1] + r * np.sin(ang)]
        polys.append(Polygon(pts))
        feats2.append({"type": "polygon",
                       "parts": [[list(map(tuple, pts))]]})
        vals2.append(float(rng.integers(1, 5)))
    ext = [(500, 500), (1200, 500), (1200, 1200), (500, 1200)]
    hole = [(700, 700), (1000, 700), (1000, 1000), (700, 1000)]
    polys.append(Polygon(ext, [hole]))
    feats2.append({"type": "polygon", "parts": [[ext, hole]]})
    vals2.append(3.0)
    a2 = features_to_friction(
        gpd.GeoDataFrame({"friction": vals2}, geometry=polys),
        unit_size=100).sort_values(["x", "y"]).reset_index(drop=True)
    b2 = paths_to_friction(feats2, vals2, unit_size=100) \
        .sort_values(["x", "y"]).reset_index(drop=True)
    assert a2.equals(b2)

    # conventions, numpy side alone
    # corner kiss: diagonal through the exact corner (1000, 1000)
    # charges the two cells it PASSES THROUGH, not the two it kisses
    kiss = paths_to_friction(
        [{"type": "line", "parts": [[(950.0, 950.0),
                                     (1050.0, 1050.0)]]}], [5.0], 100)
    cells = set(zip(kiss.x, kiss.y))
    assert cells == {(950.0, 950.0), (1050.0, 1050.0)}
    # polygon touching a cell only along its EDGE charges nothing there
    edge = paths_to_friction(
        [{"type": "polygon",
          "parts": [[[(100.0, 100.0), (200.0, 100.0),
                      (200.0, 180.0), (100.0, 180.0)]]]}], [2.0], 100)
    assert set(zip(edge.x, edge.y)) == {(150.0, 150.0)}
    # additive stacking of two features in one cell
    two = paths_to_friction(
        [{"type": "line", "parts": [[(10.0, 50.0), (90.0, 50.0)]]},
         {"type": "line", "parts": [[(50.0, 10.0), (50.0, 90.0)]]}],
        [6.0, 4.0], 100)
    assert len(two) == 1 and float(two.friction.iloc[0]) == 10.0
