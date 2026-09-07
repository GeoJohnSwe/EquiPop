"""BACKLOG 280 - VECTOR FEATURES REDUCED TO VALUES ON THE LATTICE.

The missing half of John's OSM plan. Points already landed on the
grid; lines and polygons did not, and LINES ARE WHAT FRICTION NEEDS -
features_to_friction(), load_friction_table() and run_knn_friction()
have existed for months waiting for this input.

THE UNIT IS THE MEASURE. John: "if we declare that the longest road
stretch in the unit defines the friction value we need to know WHERE
it is the longest". "Longest" is meaningless without a cell, so
friction is a property of THE CELL, not of the road.
"""
from __future__ import annotations

import pytest

gpd = pytest.importorskip("geopandas")
from shapely.geometry import LineString, Point, Polygon   # noqa: E402

from equipop.vectorjoin import (VectorJoinError, apply_groups,   # noqa
                                areas_to_cells, lines_to_cells)

LAT = {"a": 100.0, "e": -100.0, "c": 0.0, "f": 1000.0,
       "crs": "EPSG:32633"}


def _quiet(*a, **k):
    pass


def _roads(rows, crs="EPSG:32633"):
    return gpd.GeoDataFrame(
        {"fclass": [r[0] for r in rows],
         "geometry": [LineString(r[1]) for r in rows]}, crs=crs)


# --------------------------------------------------- length is exact
def test_a_road_is_DIVIDED_between_the_cells_it_crosses():
    """A road is not assigned to one cell. 250 m spanning three cells
    must appear as 50 + 100 + 100."""
    got = lines_to_cells(_roads([("motorway",
                                  [(50, 950), (300, 950)])]),
                         LAT, say=_quiet)
    assert len(got) == 3
    assert sorted(got["motorway"].tolist()) == [50.0, 100.0, 100.0]


def test_total_length_is_conserved():
    """The property that matters: nothing is lost or double-counted
    at a boundary."""
    got = lines_to_cells(_roads([("motorway",
                                  [(50, 950), (300, 950)])]),
                         LAT, say=_quiet)
    assert got["length_total"].sum() == pytest.approx(250.0)


def test_a_diagonal_road_is_also_conserved():
    import math
    line = [(10, 990), (290, 710)]
    want = math.dist(line[0], line[1])
    got = lines_to_cells(_roads([("track", line)]), LAT, say=_quiet)
    assert got["length_total"].sum() == pytest.approx(want, rel=1e-9)


# -------------------------------------------------- longest wins
def test_the_longest_class_in_the_cell_is_named():
    """John's rule, stated directly."""
    got = lines_to_cells(
        _roads([("motorway", [(10, 950), (40, 950)]),
                ("footway", [(10, 940), (90, 940)])]),
        LAT, say=_quiet)
    assert got["length_top"].iloc[0] == "footway"
    assert got["footway"].iloc[0] == pytest.approx(80.0)
    assert got["motorway"].iloc[0] == pytest.approx(30.0)


def test_longest_is_per_cell_not_per_road():
    """The whole point of the unit: a class can win in one cell and
    lose in the next."""
    got = lines_to_cells(
        _roads([("motorway", [(10, 950), (190, 950)]),
                ("footway", [(10, 940), (60, 940)])]),
        LAT, say=_quiet).set_index("gx")
    assert got.loc[0, "length_top"] == "motorway"
    assert got.loc[1, "length_top"] == "motorway"


# ------------------------------------------------------- grouping
def test_classes_can_be_grouped():
    """cafe + restaurant + fast_food = eateries, in John's words."""
    got = lines_to_cells(
        _roads([("footway", [(10, 950), (40, 950)]),
                ("path", [(10, 940), (50, 940)])]),
        LAT, groups={"paths": ["footway", "path"]}, say=_quiet)
    assert "paths" in got.columns
    assert got["paths"].iloc[0] == pytest.approx(70.0)


def test_an_ungrouped_value_keeps_its_own_name():
    """A class disappearing from a classification is this project's
    signature fault."""
    got = lines_to_cells(
        _roads([("footway", [(10, 950), (40, 950)]),
                ("motorway", [(10, 940), (50, 940)])]),
        LAT, groups={"paths": ["footway"]}, say=_quiet)
    assert "motorway" in got.columns and "paths" in got.columns


def test_a_value_in_two_groups_is_refused():
    with pytest.raises(VectorJoinError, match="two groups"):
        apply_groups(["a"], {"one": ["a"], "two": ["a"]})


# ---------------------------------------------------------- areas
def test_a_polygon_reports_the_SHARE_of_the_cell():
    """A fraction, not an area - raw area depends on the cell size
    and stops being comparable between runs."""
    water = gpd.GeoDataFrame(
        {"fclass": ["water"],
         "geometry": [Polygon([(0, 900), (50, 900), (50, 1000),
                               (0, 1000)])]}, crs="EPSG:32633")
    got = areas_to_cells(water, LAT, say=_quiet)
    assert got["water"].iloc[0] == pytest.approx(0.5)
    assert 0.0 <= got["cover_any"].iloc[0] <= 1.0


def test_a_full_cell_is_one():
    water = gpd.GeoDataFrame(
        {"fclass": ["water"],
         "geometry": [Polygon([(0, 900), (100, 900), (100, 1000),
                               (0, 1000)])]}, crs="EPSG:32633")
    got = areas_to_cells(water, LAT, say=_quiet)
    assert got["water"].iloc[0] == pytest.approx(1.0)


# ------------------------------------------------------- refusals
def test_features_with_no_crs_are_refused():
    bad = _roads([("motorway", [(10, 950), (40, 950)])], crs=None)
    with pytest.raises(VectorJoinError, match="NO coordinate system"):
        lines_to_cells(bad, LAT, say=_quiet)


def test_a_missing_class_column_lists_what_is_there():
    g = _roads([("motorway", [(10, 950), (40, 950)])])
    with pytest.raises(VectorJoinError, match="fclass"):
        lines_to_cells(g, LAT, class_col="highway", say=_quiet)


def test_the_lattice_ORIGIN_decides_the_indices():
    """Claude expected a refusal here and was wrong: the grid is
    built AROUND the features, so a distant origin cannot leave them
    off-lattice - it only shifts the indices. That is worth pinning,
    because the indices are what a join matches on: the same road on
    two different lattice origins produces different gx/gy and would
    join to nothing.
    """
    road = _roads([("motorway", [(10, 950), (40, 950)])])
    here = lines_to_cells(road, LAT, say=_quiet)
    there = lines_to_cells(road, dict(LAT, c=5_000_000.0, f=6_000_000.0),
                           say=_quiet)
    assert here["length_total"].sum() == there["length_total"].sum()
    assert (here["gx"].iloc[0], here["gy"].iloc[0]) != \
        (there["gx"].iloc[0], there["gy"].iloc[0])


def test_a_hopeless_extent_is_refused_before_it_hangs():
    huge = _roads([("motorway", [(0, 0), (10_000_000, 10_000_000)])])
    with pytest.raises(VectorJoinError, match="not finish"):
        lines_to_cells(huge, LAT, say=_quiet)


def test_features_are_reprojected_to_the_lattice():
    """The lattice decides; the features follow."""
    said = []
    g = _roads([("motorway", [(10, 950), (40, 950)])]).to_crs("EPSG:4326")
    got = lines_to_cells(g, LAT, say=said.append)
    assert got["length_total"].sum() == pytest.approx(30.0, rel=1e-6)
    assert any("reprojecting" in s for s in said)


# ---------------------------------------------------------------------
# BACKLOG 282 - LENGTH IN A GEOGRAPHIC CRS IS DEGREES, NOT METRES.
# WorldPop's lattice is EPSG:4326, so a 1 km road measured 0.009 and
# every friction value derived from it would have been wrong. The
# docstring said metres. GEOPANDAS WARNED, into a log nobody read.
# ---------------------------------------------------------------------
GEO = {"a": 1.0 / 120, "e": -1.0 / 120, "c": 30.0, "f": -2.0,
       "crs": "EPSG:4326"}


def test_length_on_a_geographic_lattice_is_METRES():
    from shapely.geometry import LineString
    road = gpd.GeoDataFrame(
        {"fclass": ["motorway"],
         "geometry": [LineString([(30.001, -2.001), (30.010, -2.001)])]},
        crs="EPSG:4326")
    got = lines_to_cells(road, GEO, say=_quiet)
    # 0.009 degrees of longitude at 2S is about 1001 m
    assert got["length_total"].sum() == pytest.approx(1001, abs=5)


def test_it_says_that_it_measured_on_the_ellipsoid():
    from shapely.geometry import LineString
    said = []
    road = gpd.GeoDataFrame(
        {"fclass": ["motorway"],
         "geometry": [LineString([(30.001, -2.001), (30.010, -2.001)])]},
        crs="EPSG:4326")
    lines_to_cells(road, GEO, say=said.append)
    assert any("ELLIPSOID" in s.upper() for s in said)


def test_a_share_on_a_geographic_lattice_uses_THAT_CELLS_area():
    """A 30 arc-second cell is 860,000 m2 at the equator and 440,000
    at 60 degrees, so one figure for the whole grid would make the
    share wrong everywhere except the middle."""
    px = 1.0 / 120
    half = Polygon([(30.0, -2.0), (30.0 + px / 2, -2.0),
                    (30.0 + px / 2, -2.0 - px), (30.0, -2.0 - px)])
    water = gpd.GeoDataFrame({"fclass": ["water"], "geometry": [half]},
                             crs="EPSG:4326")
    got = areas_to_cells(water, GEO, say=_quiet)
    assert got["water"].iloc[0] == pytest.approx(0.5, abs=1e-3)


def test_the_same_share_holds_far_from_the_equator():
    """The test that would have caught a single global cell area."""
    px = 1.0 / 120
    north = dict(GEO, f=60.0)
    half = Polygon([(30.0, 60.0), (30.0 + px / 2, 60.0),
                    (30.0 + px / 2, 60.0 - px), (30.0, 60.0 - px)])
    water = gpd.GeoDataFrame({"fclass": ["water"], "geometry": [half]},
                             crs="EPSG:4326")
    got = areas_to_cells(water, north, say=_quiet)
    assert got["water"].iloc[0] == pytest.approx(0.5, abs=1e-3)


def test_a_projected_lattice_still_uses_plain_geometry():
    """The fix must not change what was already right."""
    got = lines_to_cells(_roads([("motorway",
                                  [(50, 950), (300, 950)])]),
                         LAT, say=_quiet)
    assert got["length_total"].sum() == pytest.approx(250.0)
