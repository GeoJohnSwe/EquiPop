"""BACKLOG 269 - the inventory: what is IN a folder.

John: "could we generate a short meta text saved with each download
specifying the contents ... then the mergers can use the meta data for
dropdown menus."

TWO OBJECTS, AND ONLY ONE IS MACHINE 5'S. The manifest records
PROVENANCE and machine 5 writes it without opening anything, because
a fetcher downloads and stops. The inventory records CONTENTS, needs
the files read, and therefore belongs on the analysis side.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from equipop.doors.inventory import (INVENTORY, classes_in, inventory,
                                     lattice_key, read_inventory)

FIX = Path(__file__).resolve().parent / "fixtures" / "worldpop"
pytest.importorskip("rasterio")


@pytest.fixture(scope="module")
def osm(tmp_path_factory):
    """Shaped like Geofabrik's free shapefiles: an fclass column, and
    a high-cardinality name column that must NOT be offered as one."""
    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import LineString, Point
    d = tmp_path_factory.mktemp("osm")
    rng = np.random.default_rng(7)
    gpd.GeoDataFrame({
        "osm_id": [str(i) for i in range(120)],
        "fclass": rng.choice(["motorway", "primary", "residential",
                              "footway"], 120),
        "name": [f"Street {i}" for i in range(120)],
        "geometry": [LineString([(30 + rng.random() / 10, -3),
                                 (30, -3 + rng.random() / 10)])
                     for _ in range(120)]},
        crs="EPSG:4326").to_file(d / "gis_osm_roads_free_1.shp")
    gpd.GeoDataFrame({
        "osm_id": [str(i) for i in range(40)],
        "fclass": rng.choice(["cafe", "restaurant", "school"], 40),
        "geometry": [Point(30 + rng.random() / 10,
                           -3 + rng.random() / 10) for _ in range(40)]},
        crs="EPSG:4326").to_file(d / "gis_osm_pois_free_1.shp")
    return d


def _quiet(*a, **k):
    pass


# ------------------------------------------------------ the lattice
def test_the_same_grid_gets_the_same_key():
    """Two rasters covering DIFFERENT AREAS of one grid are the same
    lattice. What matters is whether the cell boundaries coincide -
    the origin modulo the pixel size - not the origin itself."""
    a = lattice_key("EPSG:4326", (0.001, 0, 30.0, 0, -0.001, -2.0))
    b = lattice_key("EPSG:4326", (0.001, 0, 31.0, 0, -0.001, -3.0))
    assert a == b


def test_a_shifted_grid_gets_a_different_key():
    a = lattice_key("EPSG:4326", (0.001, 0, 30.0000, 0, -0.001, -2.0))
    b = lattice_key("EPSG:4326", (0.001, 0, 30.0005, 0, -0.001, -2.0))
    assert a != b


def test_a_different_crs_is_a_different_lattice():
    """The numbers can agree while the worlds do not - BACKLOG 239."""
    a = lattice_key("EPSG:4326", (0.001, 0, 30.0, 0, -0.001, -2.0))
    b = lattice_key("EPSG:3857", (0.001, 0, 30.0, 0, -0.001, -2.0))
    assert a != b


def test_rasters_on_one_grid_are_grouped(tmp_path):
    inv = inventory(FIX, say=_quiet, write=False)
    assert len(inv["lattices"]) == 1
    assert len(next(iter(inv["lattices"].values()))) == 3


def test_more_than_one_lattice_is_said_out_loud(tmp_path):
    import rasterio
    from rasterio.transform import from_origin
    for name, px in (("a.tif", 0.001), ("b.tif", 0.002)):
        with rasterio.open(tmp_path / name, "w", driver="GTiff",
                           height=4, width=4, count=1, dtype="float32",
                           crs="EPSG:4326",
                           transform=from_origin(30, -2, px, px)) as o:
            o.write(np.ones((4, 4), "float32"), 1)
    said = []
    inv = inventory(tmp_path, say=said.append)
    assert len(inv["lattices"]) == 2
    assert "MORE THAN ONE LATTICE" in " ".join(said)
    assert "cannot be merged by index" in " ".join(said)


# ------------------------------------------------------ the classes
def test_fclass_values_come_from_THE_DATA(osm):
    inv = inventory(osm, say=_quiet)
    # A shapefile is FIVE files - .cpg, .dbf, .prj, .shp, .shx - and
    # all of them match "roads". Filter on kind, not on the name.
    roads = [f for f in inv["files"]
             if "roads" in f["file"] and f["kind"] == "vector"][0]
    got = roads["classes"]["fclass"]["values"]
    assert set(got) == {"motorway", "primary", "residential", "footway"}


def test_a_high_cardinality_column_is_not_offered_as_a_class(osm):
    """120 street names would bury fclass."""
    inv = inventory(osm, say=_quiet)
    roads = [f for f in inv["files"]
             if "roads" in f["file"] and f["kind"] == "vector"][0]
    assert "name" not in (roads.get("classes") or {})


def test_classes_in_gives_a_grouping_tool_its_dropdown(osm):
    inventory(osm, say=_quiet)
    got = classes_in(osm)
    flat = {v for layers in got.values() for vals in layers.values()
            for v in vals}
    assert {"cafe", "restaurant", "school"} <= flat
    assert {"motorway", "footway"} <= flat


def test_classes_in_refuses_a_folder_it_has_not_seen(tmp_path):
    with pytest.raises(ValueError, match="Run inventory"):
        classes_in(tmp_path)


# -------------------------------------------------------- behaviour
def test_it_writes_a_file_that_can_be_read_back(osm):
    inv = inventory(osm, say=_quiet)
    assert (Path(osm) / INVENTORY).exists()
    back = read_inventory(osm)
    assert back["files"] == inv["files"]
    assert back["made_by"].startswith("EquiPop ")


def test_the_geometry_and_count_are_recorded(osm):
    inv = inventory(osm, say=_quiet)
    kinds = {f["file"]: (f.get("geometry"), f.get("features"))
             for f in inv["files"] if f["kind"] == "vector"}
    assert kinds["gis_osm_roads_free_1.shp"] == ("LineString", 120)
    assert kinds["gis_osm_pois_free_1.shp"] == ("Point", 40)


def test_an_unreadable_file_is_RECORDED_not_skipped(tmp_path):
    """A file silently missing from an inventory is worse than one
    listed as unreadable - and this is how the numpy-array bug in
    Claude's own reader was found rather than losing two shapefiles."""
    (tmp_path / "broken.tif").write_bytes(b"not a tif")
    inv = inventory(tmp_path, say=_quiet)
    bad = [f for f in inv["files"] if f["kind"] == "unreadable"]
    assert len(bad) == 1
    assert bad[0]["error"], "the reason must be kept"


def test_it_changes_nothing_but_its_own_file(osm):
    before = {p.name for p in Path(osm).iterdir()} - {INVENTORY}
    inventory(osm, say=_quiet)
    after = {p.name for p in Path(osm).iterdir()} - {INVENTORY}
    assert before == after


def test_the_manifest_is_not_inventoried(tmp_path):
    """The two files describe different things and must not describe
    each other."""
    (tmp_path / "equipop_fetch.json").write_text("{}", encoding="utf-8")
    inv = inventory(tmp_path, say=_quiet)
    assert all("equipop_fetch" not in f["file"] for f in inv["files"])
