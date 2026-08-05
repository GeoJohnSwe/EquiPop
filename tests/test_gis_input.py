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
    # v1.29.2, BACKLOG 83 - this assertion used to read "no pop ->
    # Null" and is deliberately REVERSED. A row with no count is not
    # a MEMBER (it adds nobody to the population) but it is still an
    # ORIGIN: it may ask what is around it, and machine 1 has always
    # answered. Row 1 sits on top of row 0's two persons, so the two
    # nearest persons both earn 10.
    assert res2["Nv_inc_2"][1] == 2                 # it found them
    assert res2["Mean_inc_2"][1] == 10.0            # and answers
    assert res2["N_2"][1] == 2                      # persons, not rows


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
    # v1.27: costs may go BELOW zero - a facilitator is a fraction of
    # a round - but never to -1, where a cell becomes free and there
    # is no neighbourhood left to speak of
    with pytest.raises(ValueError, match="floor"):
        paths_to_friction([{"type": "line",
                            "parts": [[(0, 0), (10, 10)]]}], [-1], 100)
    fast = paths_to_friction([{"type": "line",
                               "parts": [[(0, 0), (10, 10)]]}],
                             [-0.9], 100)
    assert float(fast.friction.iloc[0]) == pytest.approx(-0.9)
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



def test_stats_fast_path_identical_to_exhaustive():
    """v1.16.3: the KD-tree fast path must reproduce the exhaustive
    engine BIT FOR BIT at any m - including m so small that the tie-
    ring guard has to trigger the exact recomputation."""
    from equipop.cells import build_cells, auto_m_neighbors
    from equipop.analysis import run_knn_stats
    rng = np.random.default_rng(4242)
    n = 2500
    df = pd.DataFrame({"_x": rng.uniform(0, 5000, n),
                       "_y": rng.uniform(0, 5000, n),
                       "inc": rng.lognormal(10, 0.4, n),
                       "hi": rng.integers(0, 2, n).astype(float)})
    cd = build_cells(df, "_x", "_y", value_vars=["inc"],
                     binary_vars=["hi"], unit_size=100)
    st = {"inc": ["mean", "median", "gini", "p10", "p90", "count"],
          "hi": ["ratio", "sd"]}
    slow = run_knn_stats(cd, k_values=[40, 300], r_values=[400.0],
                         stats=st, m_neighbors=10 ** 9)
    for m in (8, 64, 512, None):
        fast = run_knn_stats(cd, k_values=[40, 300], r_values=[400.0],
                             stats=st, m_neighbors=m)
        pd.testing.assert_frame_equal(slow, fast)
    m_auto = auto_m_neighbors(cd, [300], [400.0])
    assert 64 <= m_auto <= len(cd)


def test_auto_m_scales_with_k_and_density():
    from equipop.cells import build_cells, auto_m_neighbors
    rng = np.random.default_rng(5)
    n = 4000
    df = pd.DataFrame({"_x": rng.uniform(0, 8000, n),
                       "_y": rng.uniform(0, 8000, n)})
    cd = build_cells(df, "_x", "_y", unit_size=100)
    small = auto_m_neighbors(cd, [50], None)
    big = auto_m_neighbors(cd, [800], None)
    assert small < big <= len(cd)
    assert auto_m_neighbors(cd, [50], [2000.0]) > small   # radius rules


def test_counts_ladder_identical_to_exhaustive():
    """v1.16.4: widening the neighbour search step by step (instead
    of re-solving thin origins against every cell) must not move a
    single number - checked with m so small that almost every origin
    has to climb the ladder."""
    from equipop.cells import build_cells
    from equipop.fastcounts import run_knn_counts
    rng = np.random.default_rng(4711)
    n = 3000
    # urban/rural contrast: this is what makes origins straggle
    nd = int(n * 0.7)
    x = np.r_[rng.normal(2000, 300, nd), rng.uniform(0, 40000, n - nd)]
    y = np.r_[rng.normal(2000, 300, nd), rng.uniform(0, 40000, n - nd)]
    pop = np.r_[rng.integers(4, 30, nd),
                rng.integers(1, 3, n - nd)].astype(float)
    # expand to individuals (build_cells counts rows as persons)
    rep = pop.astype(int)
    xi = np.repeat(x, rep)
    yi = np.repeat(y, rep)
    hi = np.repeat(rng.integers(0, 2, n), rep).astype(float)
    df = pd.DataFrame({"_x": xi, "_y": yi, "hi": hi})
    cd = build_cells(df, "_x", "_y", binary_vars=["hi"],
                     unit_size=100)
    ref = run_knn_counts(cd, k_values=[200, 444], r_values=[444.0],
                         m_neighbors=len(cd))          # exhaustive
    for m in (8, 64, 300, None):
        got = run_knn_counts(cd, k_values=[200, 444], r_values=[444.0],
                             m_neighbors=m)
        pd.testing.assert_frame_equal(ref, got)


def test_variable_bandwidth_decay_is_exact_per_row():
    """v1.17: each row may carry its OWN half-life (an estimated
    median distance, a group potential, or its own Dist_k). Rows of
    one bandwidth must get exactly what a single-bandwidth run would
    give them - the binning is an implementation detail, not an
    approximation."""
    from equipop.stata_bridge import knn_to_rows
    from equipop.decay import Decay
    rng = np.random.default_rng(1917)
    n = 350
    x, y = rng.uniform(0, 3000, n), rng.uniform(0, 3000, n)
    hl = rng.choice([300.0, 1200.0], n)
    got = knn_to_rows(x, y, k_values=[40],
                      decay=Decay(model="negexp", half_life_m=500.0),
                      decay_half_life=hl, decay_bins=4)["ND_inf"]
    for h in (300.0, 1200.0):
        ref = knn_to_rows(x, y, k_values=[40],
                          decay=Decay(model="negexp",
                                      half_life_m=h))["ND_inf"]
        m = hl == h
        assert np.allclose(got[m], ref[m], equal_nan=True)
    # a continuous field goes through the quantile path
    hl2 = rng.uniform(200.0, 2000.0, n)
    got2 = knn_to_rows(x, y, k_values=[40],
                       decay=Decay(model="negexp", half_life_m=500.0),
                       decay_half_life=hl2, decay_bins=8)["ND_inf"]
    assert np.isfinite(got2).all()
    # wider bandwidth must gather at least as much mass
    assert np.corrcoef(hl2, got2)[0, 1] > 0.5
    with pytest.raises(ValueError, match="positive bandwidth"):
        knn_to_rows(x, y, k_values=[40],
                    decay=Decay(model="negexp", half_life_m=500.0),
                    decay_half_life=np.where(hl2 > 1000, np.nan, hl2))


def test_self_calibrating_bandwidth_follows_urban_form():
    """Dist_k fed back as the half-life: dense places get sharp
    kernels, thin places broad ones, with no external estimate."""
    from equipop.stata_bridge import dispatch
    rng = np.random.default_rng(1918)
    x = np.r_[rng.normal(1000, 150, 300), rng.uniform(0, 6000, 150)]
    y = np.r_[rng.normal(1000, 150, 300), rng.uniform(0, 6000, 150)]
    res = dispatch("counts", x, y, k_values=[40], half_life_m=500.0,
                   decay_model="negexp", half_life_from_dist=40,
                   decay_bins=5)
    assert "ND_inf" in res and np.isfinite(res["ND_inf"]).all()
    dist = res["Dist_40"]
    town = dist < np.nanmedian(dist)
    assert np.nanmean(dist[town]) < np.nanmean(dist[~town])


def test_a_missing_count_means_the_same_in_both_machines():
    """John's ruling, v1.29.2: an UNKNOWN count is treated exactly as
    machine 1 treats it - as zero. So a row with a missing count adds
    nobody to the population, is nobody's neighbour, and still gets
    its own results. The two machines must not diverge here again:
    they did until 1.29.2, and nobody noticed because machine 2 had
    no way to put a row outside the reference population."""
    x = np.array([50.0, 50.0, 250.0])
    y = np.full(3, 50.0)
    both = {}
    for label, w in (("nan", np.array([2.0, np.nan, 1.0])),
                     ("zero", np.array([2.0, 0.0, 1.0]))):
        both[label] = dispatch(
            "stats", x, y, values={"inc": np.array([10.0, 20.0, 99.0])},
            weight=w, k_values=[2], unit_size=100)
    for key in both["nan"]:
        a = np.asarray(both["nan"][key], float)
        b = np.asarray(both["zero"][key], float)
        assert np.allclose(a, b, equal_nan=True), (
            f"{key}: a missing count and a zero count must give the "
            f"same answer - got {a} against {b}")

    counts = dispatch("counts", x, y, weight=np.array([2.0, np.nan, 1.0]),
                      k_values=[2], unit_size=100)
    stats = both["nan"]
    assert np.isfinite(counts["N_2"][1]), \
        "machine 1 gives the unknown-count row results"
    assert np.isfinite(stats["N_2"][1]), \
        "and so, since v1.29.2, does machine 2"
    assert counts["N_2"][1] == stats["N_2"][1], (
        "the two machines must agree on how many persons that row "
        "found around it")
