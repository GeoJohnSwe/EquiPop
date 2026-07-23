"""v1.16 GIS input rework - package-side units: coordinate guessing,
selectable statistics incl. percentiles, full-population expansion,
and the geometry/raster -> friction converters with overlap rules."""
import numpy as np
import pandas as pd
import pytest

from equipop.io import guess_xy_fields, resolve_xy_columns
from equipop.friction import (points_to_friction, paths_to_friction,
                              raster_to_friction)
from equipop.stata_bridge import dispatch


def test_guess_xy_fields_aliases_and_degrees():
    assert guess_xy_fields(["id", "Easting", "Northing"])[:2] == \
        ("Easting", "Northing")
    assert guess_xy_fields(["POINT_X", "POINT_Y"])[:2] == \
        ("POINT_X", "POINT_Y")
    assert guess_xy_fields(["East_RT90", "North_RT90"])[:2] == \
        ("East_RT90", "North_RT90")
    gx, gy, deg = guess_xy_fields(["Longitude", "Latitude"])
    assert deg                                   # flagged, not used
    assert guess_xy_fields(["osm_id", "fclass", "FRiction"]) == \
        (None, None, False)                      # never raises
    with pytest.raises(ValueError, match="DEGREES"):
        resolve_xy_columns(pd.DataFrame({"longitude": [1.0],
                                         "latitude": [2.0]}))


def test_selectable_measures_known_answers():
    """Every new measure against numpy on a hand-buildable case: two
    cells, k large enough to always gather BOTH."""
    x = np.array([50.0, 50.0, 50.0, 250.0])
    y = np.full(4, 50.0)
    v = np.array([1.0, 3.0, 5.0, 11.0])
    res = dispatch("stats", x, y, values={"v": v},
                   stats={"v": ["mean", "median", "var", "sd", "min",
                                "max", "count", "sum", "range",
                                "p25", "p75"]},
                   k_values=[4], unit_size=100)
    r0 = {c: res[c][0] for c in res}
    assert r0["Mean_v_4"] == np.mean(v)
    assert r0["Med_v_4"] == np.median(v)
    assert abs(r0["Var_v_4"] - np.var(v, ddof=1)) < 1e-12
    assert abs(r0["SD_v_4"] - np.std(v, ddof=1)) < 1e-12
    assert (r0["Min_v_4"], r0["Max_v_4"]) == (1.0, 11.0)
    assert r0["Cnt_v_4"] == 4 and r0["Sum_v_4"] == 20.0
    assert r0["Rng_v_4"] == 10.0
    assert r0["P25_v_4"] == np.percentile(v, 25, method="linear")
    assert r0["P75_v_4"] == np.percentile(v, 75, method="linear")
    with pytest.raises(ValueError, match="Unknown value statistic"):
        dispatch("stats", x, y, values={"v": v},
                 stats={"v": ["mode"]}, k_values=[2], unit_size=100)


def test_full_population_expansion_weighted_exact():
    """weight = persons per row: k counts PERSONS and statistics are
    population-weighted EXACTLY (row expansion)."""
    x = np.array([50.0, 50.0, 250.0])
    y = np.full(3, 50.0)
    inc = np.array([10.0, 20.0, 99.0])
    pop = np.array([3.0, 1.0, 5.0])
    res = dispatch("stats", x, y, values={"inc": inc}, weight=pop,
                   k_values=[4], unit_size=100)
    assert res["N_4"][0] == 4                       # persons, not rows
    assert abs(res["Mean_inc_4"][0]
               - np.average([10, 20], weights=[3, 1])) < 1e-12
    assert res["Med_inc_4"][0] == 10.0              # weighted median
    res2 = dispatch("stats", x, y, values={"inc": inc},
                    weight=np.array([2.0, np.nan, 1.0]), k_values=[2],
                    unit_size=100)
    assert np.isnan(res2["Mean_inc_2"][1])          # no pop -> Null


def test_points_paths_raster_converters_and_overlap():
    p = points_to_friction([10, 20, 150], [10, 20, 10], [6, 4, 2], 100)
    assert set(zip(p.x, p.y, p.friction)) == {(50.0, 50.0, 10.0),
                                              (150.0, 50.0, 2.0)}
    for agg, want in (("max", 6.0), ("min", 4.0), ("mean", 5.0)):
        q = points_to_friction([10, 20], [10, 20], [6, 4], 100,
                               agg=agg)
        assert float(q.friction.iloc[0]) == want
    with pytest.raises(ValueError, match="overlap rule"):
        points_to_friction([1], [1], [1], 100, agg="median")
    with pytest.raises(ValueError, match="missing"):
        points_to_friction([1.0], [1.0], [np.nan], 100)
    with pytest.raises(ValueError, match="negative"):
        paths_to_friction([{"type": "line",
                            "parts": [[(0, 0), (10, 10)]]}], [-1], 100)
    # conventions on the numpy rasterizer alone
    kiss = paths_to_friction([{"type": "line",
                               "parts": [[(950.0, 950.0),
                                          (1050.0, 1050.0)]]}],
                             [5.0], 100)
    assert set(zip(kiss.x, kiss.y)) == {(950.0, 950.0),
                                        (1050.0, 1050.0)}
    edge = paths_to_friction(
        [{"type": "polygon",
          "parts": [[[(100.0, 100.0), (200.0, 100.0),
                      (200.0, 180.0), (100.0, 180.0)]]]}], [2.0], 100)
    assert set(zip(edge.x, edge.y)) == {(150.0, 150.0)}
    two = paths_to_friction(
        [{"type": "line", "parts": [[(10.0, 50.0), (90.0, 50.0)]]},
         {"type": "line", "parts": [[(50.0, 10.0), (50.0, 90.0)]]}],
        [6.0, 4.0], 100)
    assert len(two) == 1 and float(two.friction.iloc[0]) == 10.0
    r = raster_to_friction(np.array([[1.0, 0.0], [3.0, 9.0]]),
                           0.0, 100.0, 50.0, 50.0, unit_size=100)
    assert set(zip(r.x, r.y, r.friction)) == {(50.0, 50.0, 9.0)}
    r2 = raster_to_friction(np.full((5, 5), 7.0), 0.0, 500.0,
                            100.0, 100.0, unit_size=100, nodata=7.0)
    assert len(r2) == 0


def test_paths_vs_shapely_twin_with_agg():
    """Cross-implementation twin: numpy rasterizer == shapely
    rasterizer cell-for-cell, for BOTH overlap rules, random lines
    and polygons incl. a holed rectangle (the check that caught the
    boundary-contact bug)."""
    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import LineString, Polygon
    from equipop.friction import features_to_friction
    rng = np.random.default_rng(1848)
    lines, feats, vals = [], [], []
    for _ in range(15):
        pts = rng.uniform(0, 2500, (rng.integers(2, 6), 2))
        lines.append(LineString(pts))
        feats.append({"type": "line", "parts": [list(map(tuple, pts))]})
        vals.append(float(rng.integers(1, 9)))
    polys, feats2, vals2 = [], [], []
    for _ in range(8):
        c = rng.uniform(300, 2200, 2)
        ang = np.sort(rng.uniform(0, 2 * np.pi, rng.integers(3, 8)))
        rr = rng.uniform(80, 350)
        pts = np.c_[c[0] + rr * np.cos(ang), c[1] + rr * np.sin(ang)]
        polys.append(Polygon(pts))
        feats2.append({"type": "polygon",
                       "parts": [[list(map(tuple, pts))]]})
        vals2.append(float(rng.integers(1, 5)))
    ext = [(500, 500), (1200, 500), (1200, 1200), (500, 1200)]
    hole = [(700, 700), (1000, 700), (1000, 1000), (700, 1000)]
    polys.append(Polygon(ext, [hole]))
    feats2.append({"type": "polygon", "parts": [[ext, hole]]})
    vals2.append(3.0)
    for agg in ("sum", "max"):
        a = features_to_friction(
            gpd.GeoDataFrame({"friction": vals}, geometry=lines),
            unit_size=100, agg=agg).sort_values(["x", "y"]) \
            .reset_index(drop=True)
        b = paths_to_friction(feats, vals, unit_size=100, agg=agg) \
            .sort_values(["x", "y"]).reset_index(drop=True)
        assert a.equals(b)
        a2 = features_to_friction(
            gpd.GeoDataFrame({"friction": vals2}, geometry=polys),
            unit_size=100, agg=agg).sort_values(["x", "y"]) \
            .reset_index(drop=True)
        b2 = paths_to_friction(feats2, vals2, unit_size=100, agg=agg) \
            .sort_values(["x", "y"]).reset_index(drop=True)
        assert a2.equals(b2)
