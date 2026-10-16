# -*- coding: utf-8 -*-
"""test_fetchrows.py - machine 5 fetches THE ROWS YOU SELECTED.

BACKLOG 414, v1.58.0. Real bytes throughout: WorldPop files shaped
like GeoTIFFs, Geofabrik zips with Geofabrik's member names, and two
genuine .osm.pbf files read by GDAL's own OSM driver - served by
tests/fakeweb.py, which speaks HEAD, Range and If-Range.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import io
import json
import os
import sys
import types
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import fakeweb                                       # noqa: E402
from equipop.doors import catalogue as cat          # noqa: E402
from equipop.doors import fetchrows as fr           # noqa: E402
from equipop.doors.fetching import (FetchError, MANIFEST,  # noqa: E402
                                    verify_folder)

SWEDEN_ZIP = "https://download.geofabrik.de/europe/sweden-latest-free.shp.zip"
NEXT_DAY = datetime(2026, 10, 15, 21, 30, tzinfo=timezone.utc)


def mute(*_a):
    return None


def _need_osm_driver():
    try:
        import pyogrio
        ok = "OSM" in pyogrio.list_drivers()
    except Exception:
        ok = False
    if not ok and fr.find_converter() is None:
        pytest.skip("no GDAL OSM driver here")


@pytest.fixture
def web():
    return fakeweb.captured(bodies=True)


@pytest.fixture
def net(web):
    return cat.Net(opener=web, pause=0)


@pytest.fixture
def picked(net):
    """John's three requests, a little of each: two WorldPop files,
    Sweden's buildings and roads, Bayern's 2020 roads and POIs."""
    wp = cat.browse_worldpop("age_sex", "Burundi", "2020", net=net, say=mute)
    sh = cat.browse_geofabrik("Sweden", "buildings, roads", net=net,
                              say=mute)
    pb = cat.browse_geofabrik("Bayern", "roads, pois", years="2020",
                              latest=False, net=net, say=mute)
    return ([r for r in wp if r["sex"] == "f" and r["age_from"] in (15, 20)]
            + sh + pb)


def _manifest(folder):
    with open(os.path.join(folder, MANIFEST), encoding="utf-8") as f:
        return {x["name"]: x for x in json.load(f)["files"]}


def _gets(web, url, ranged=None):
    return [r for m, u, r in web.log if m == "GET" and u == url
            and (ranged is None or bool(r) == ranged)]


# =========================================================== the run
def test_the_selected_rows_and_nothing_else(picked, net, web, tmp_path):
    """Every row arrives under its catalogue name, the manifest records
    each with how it was checked, and verify finds the folder whole.

    BROKEN WITH: the shapefile members named after the zip's members
    (gis_osm_roads_free_1.dbf) instead of the row's file."""
    _need_osm_driver()
    out = str(tmp_path / "f")
    res = fr.fetch_rows(picked, out, net=net, say=mute)
    names = sorted(os.listdir(out))
    want = (["bayern-200101.osm.pbf", "bayern_20200101_pois.gpkg",
             "bayern_20200101_pois_a.gpkg", "bayern_20200101_roads.gpkg",
             "bdi_f_15_2020_CN_1km_R2025A_UA_v1.tif",
             "bdi_f_20_2020_CN_1km_R2025A_UA_v1.tif",
             "equipop_fetch.json", "equipop_recipe.csv"]
            + [f"sweden_20261014_{l}.{e}" for l in ("buildings_a", "roads")
               for e in ("cpg", "dbf", "prj", "shp", "shx")])
    assert names == sorted(want)
    man = _manifest(out)
    assert man["sweden_20261014_roads.dbf"]["publisher_check"] == \
        "verified against the zip's own CRC-32"
    assert man["bayern-200101.osm.pbf"]["publisher_check"] == \
        "verified against publisher md5"
    assert man["bdi_f_15_2020_CN_1km_R2025A_UA_v1.tif"]["licence"] == \
        "https://hub.worldpop.org/data/licence.txt"
    v = verify_folder(out, say=mute)
    assert v["ok"] == len(man) and not v["untracked"] and not v["changed"]
    assert len(res["derived"]) == 3


def test_a_shapefile_layer_is_its_own_bytes_out_of_the_zip(picked, net,
                                                           web, tmp_path):
    """The files are the zip's members, byte for byte - and the zip is
    never downloaded whole: one ranged GET for its table of contents
    while browsing, one for it again when fetching, then two per
    member (its local header, its data).

    BROKEN WITH: extract_member reading from the central directory's
    header offset without skipping the local header (the bytes are
    then shifted by 30 + name length, and the CRC refuses them)."""
    out = str(tmp_path / "f")
    rows = [r for r in picked if r["series"] == "shapefile"]
    fr.fetch_rows(rows, out, net=net, say=mute)
    z = zipfile.ZipFile(io.BytesIO(web.files[SWEDEN_ZIP]["body"]))
    for layer in ("buildings_a", "roads"):
        for e in ("cpg", "dbf", "prj", "shp", "shx"):
            with open(os.path.join(out, f"sweden_20261014_{layer}.{e}"),
                      "rb") as f:
                assert f.read() == z.read(f"gis_osm_{layer}_free_1.{e}")
    assert _gets(web, SWEDEN_ZIP, ranged=False) == []
    assert len(_gets(web, SWEDEN_ZIP, ranged=True)) == 1 + 1 + 2 * 10


def test_fetching_again_downloads_nothing(picked, net, web, tmp_path):
    """BROKEN WITH: the 'already here and unchanged' check (_have) made
    to return False - the .pbf then comes again."""
    _need_osm_driver()
    out = str(tmp_path / "f")
    fr.fetch_rows(picked, out, net=net, say=mute)
    before = len(web.log)
    fr.fetch_rows(picked, out, net=net, say=mute)
    again = web.log[before:]
    assert [m for m, u, r in again if m == "GET" and not r] == []
    assert sum(1 for m, u, r in again if r) == 1      # the zip's contents


def test_a_layer_in_numbered_parts_keeps_its_parts(net, web, tmp_path):
    """BROKEN WITH: every part written to the same name."""
    web.add_file(SWEDEN_ZIP, body=fakeweb.shapefile_zip(
        "sweden", big={"roads": 2}))
    rows = cat.browse_geofabrik("Sweden", "roads", net=net, say=mute)
    assert "2 numbered parts" in rows[0]["note"]
    out = str(tmp_path / "f")
    fr.fetch_rows(rows, out, net=net, say=mute)
    assert sorted(n for n in os.listdir(out) if n.endswith(".shp")) == \
        ["sweden_20261014_roads_1.shp", "sweden_20261014_roads_2.shp"]


# ===================================================== what can go wrong
def test_a_zip_replaced_mid_fetch_is_refused_not_mixed(net, web, tmp_path):
    """Geofabrik rewrites its 'latest' zip daily. Replaced after the
    fetch read its contents, the next member is refused - not taken
    from the new zip at the old zip's offsets - and what had arrived
    is recorded, the job marked incomplete.

    BROKEN WITH: the member's ranged GET sent without If-Range."""
    rows = cat.browse_geofabrik("Sweden", "buildings", net=net, say=mute)

    calls = {"n": 0}
    orig = web.__class__.__call__

    def opener(req):
        if req.get_header("Range") and req.full_url == SWEDEN_ZIP:
            calls["n"] += 1
            if calls["n"] == 5:                 # TOC, then 2 members
                web.replace(SWEDEN_ZIP, fakeweb.shapefile_zip(
                    "sweden", seed=7), NEXT_DAY)
        return orig(web, req)
    out = str(tmp_path / "f")
    with pytest.raises(cat.NetError, match="REPLACED"):
        fr.fetch_rows(rows, out, net=cat.Net(opener=opener, pause=0),
                      say=mute)
    man = json.load(open(os.path.join(out, MANIFEST), encoding="utf-8"))
    assert man["fetches"][-1]["status"] == "incomplete"
    assert len(man["files"]) == 1
    assert [n for n in os.listdir(out) if n.endswith(".part")] == []


def _zip_with_bad_member(method):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", method) as z:
        z.writestr("gis_osm_roads_free_1.shp", b"roads " * 400)
        for e in ("cpg", "dbf", "prj", "shx"):
            z.writestr(f"gis_osm_roads_free_1.{e}", b"x" * 50)
    raw = bytearray(buf.getvalue())
    info = zipfile.ZipFile(io.BytesIO(bytes(raw))).getinfo(
        "gis_osm_roads_free_1.shp")
    start = info.header_offset + 30 + len(info.filename)
    if method == zipfile.ZIP_STORED:
        raw[start + 5] ^= 0xFF               # same size, wrong bytes
    else:
        raw[start] = 0xFF                    # a deflate block type of 3,
    return bytes(raw)                        # which does not exist


@pytest.mark.parametrize("method,why", [
    (zipfile.ZIP_STORED, "DOES NOT MATCH the zip's own record"),
    (zipfile.ZIP_DEFLATED, "arrived DAMAGED"),
])
def test_a_damaged_member_is_refused_and_removed(net, web, tmp_path,
                                                 method, why):
    """The zip's CRC-32 is the publisher's checksum for each member.

    BROKEN WITH: the CRC comparison removed (stored: the damaged file
    is kept); and, for deflate, zlib.error left unconverted (it then
    surfaces as 'Error -3 while decompressing data' with no advice)."""
    web.add_file(SWEDEN_ZIP, body=_zip_with_bad_member(method))
    rows = cat.browse_geofabrik("Sweden", "roads", net=net, say=mute)
    out = str(tmp_path / "f")
    with pytest.raises(FetchError, match=why):
        fr.fetch_rows(rows, out, net=net, say=mute)
    assert not os.path.exists(os.path.join(out,
                                           "sweden_20261014_roads.shp"))
    assert [n for n in os.listdir(out) if n.endswith(".part")] == []


def test_an_extract_updated_since_browsing_is_fetched_under_its_own_date(
        net, web, tmp_path):
    """Browsed on the 14th, fetched after Geofabrik's run on the 15th:
    the 15th is what is there, so it is fetched - named for the 15th,
    and said.

    BROKEN WITH: _relabel returning the row unchanged (the 15th's bytes
    then sit under the 14th's name)."""
    rows = cat.browse_geofabrik("Sweden", "roads", net=net, say=mute)
    web.replace(SWEDEN_ZIP, fakeweb.shapefile_zip("sweden", seed=3),
                NEXT_DAY)
    said = []
    out = str(tmp_path / "f")
    fr.fetch_rows(rows, out, net=net, say=said.append)
    assert "sweden_20261015_roads.shp" in os.listdir(out)
    assert not any("20261014" in n for n in os.listdir(out))
    assert any("2026-10-14 -> 2026-10-15" in s for s in said)
    recipe = cat.read_csv(os.path.join(out, fr.RECIPE))
    assert recipe[0]["date"] == "2026-10-15"


def test_a_latest_pbf_is_saved_under_its_date(net, web, tmp_path):
    """sweden-latest.osm.pbf changes daily under one name; saved under
    it, tomorrow's fetch would take today's file for the same thing.

    BROKEN WITH: the 'latest' name kept for the saved .pbf."""
    _need_osm_driver()
    rows = cat.browse_geofabrik("Norway", "roads", net=net, say=mute)
    out = str(tmp_path / "f")
    fr.fetch_rows(rows, out, net=net, say=mute)
    assert "norway-261014.osm.pbf" in os.listdir(out)
    assert "norway-latest.osm.pbf" not in os.listdir(out)


def test_too_much_is_refused_before_anything_moves(picked, net, web,
                                                   tmp_path):
    """BROKEN WITH: the limit check removed."""
    before = len(web.log)
    with pytest.raises(FetchError, match="above the limit"):
        fr.fetch_rows(picked, str(tmp_path / "f"), net=net, say=mute,
                      max_mb=1e-6)
    assert len(web.log) == before


def test_no_way_to_read_a_pbf_is_refused_before_downloading(
        picked, net, web, tmp_path, monkeypatch):
    """A .pbf that cannot be written out must not be downloaded first -
    for a continent that is gigabytes for nothing.

    BROKEN WITH: the refusal removed - a missing converter then fails
    only after the .pbf has been downloaded."""
    monkeypatch.setattr(fr, "find_converter", lambda: None)
    before = len(web.log)
    with pytest.raises(FetchError, match="neither"):
        fr.fetch_rows(picked, str(tmp_path / "f"), net=net, say=mute)
    assert len(web.log) == before


def test_a_foreign_geopackage_stops_the_run_before_the_download(
        net, web, tmp_path):
    """BROKEN WITH: the check left only in _write_layer, after the
    .pbf had come."""
    rows = cat.browse_geofabrik("Bayern", "roads", years="2020",
                                latest=False, net=net, say=mute)
    out = tmp_path / "f"
    out.mkdir()
    (out / "bayern_20200101_roads.gpkg").write_bytes(b"mine")
    with pytest.raises(FetchError, match="Nothing was downloaded"):
        fr.fetch_rows(rows, str(out), net=net, say=mute)
    assert not (out / "bayern-200101.osm.pbf").exists()
    assert (out / "bayern_20200101_roads.gpkg").read_bytes() == b"mine"


def test_rows_that_are_not_rows_are_refused_together(picked, tmp_path):
    """A recipe is a CSV anyone can edit. Every bad row is named at once.

    BROKEN WITH: _plain_name accepting a name with a folder in it."""
    nowhere = cat.Net(opener=fakeweb.FakeWeb(), pause=0)
    bad = [dict(picked[0], url="https://example.org/x.tif"),
           dict(picked[1], file="sub/escape.tif"),
           dict(picked[2], provider="Somebody"),
           dict(picked[-1], inside="polygons: x")]
    with pytest.raises(FetchError) as e:
        fr.fetch_rows(bad, str(tmp_path / "f"), net=nowhere, say=mute)
    msg = str(e.value)
    for i in (1, 2, 3, 4):
        assert f"row {i} " in msg
    assert not (tmp_path / "f").exists()


def test_one_name_two_sources_is_refused(picked, tmp_path):
    """BROKEN WITH: the clash check removed - the second row's bytes
    would be refused late by run_fetch, after downloads, or not at all."""
    a = picked[0]
    b = dict(picked[1], file=a["file"])
    nowhere = cat.Net(opener=fakeweb.FakeWeb(), pause=0)
    with pytest.raises(FetchError, match="same file"):
        fr.fetch_rows([a, b], str(tmp_path / "f"), net=nowhere, say=mute)


def test_nothing_selected_says_how_to_select(tmp_path):
    """BROKEN WITH: the empty-selection check removed - the run then
    'succeeds', having fetched nothing, and writes an empty recipe."""
    with pytest.raises(FetchError, match="Select rows"):
        fr.fetch_rows([], str(tmp_path / "f"), say=mute)


def test_the_same_row_twice_is_fetched_once(picked, net, tmp_path):
    """Two catalogues stacked share rows.

    BROKEN WITH: de-duplication removed - the second copy is then
    refused as a file nobody fetched."""
    said = []
    wp = [r for r in picked if r["provider"] == "WorldPop"]
    fr.fetch_rows(wp + wp, str(tmp_path / "f"), net=net, say=said.append)
    assert any("appeared twice" in s for s in said)


# ========================================================== the record
def test_a_derived_layer_says_where_it_came_from(picked, net, tmp_path):
    """The GeoPackage is recorded as derived from the .pbf, with the
    rule, the count and the program that wrote it.

    BROKEN WITH: the rule left out of the derived record."""
    _need_osm_driver()
    out = str(tmp_path / "f")
    fr.fetch_rows(picked, out, net=net, say=mute)
    d = _manifest(out)["bayern_20200101_roads.gpkg"]
    assert d["derived_from"] == "bayern-200101.osm.pbf"
    assert d["rule"] == cat.PBF_RULES["roads"]
    assert d["features"] == 1 and d["written_by"]
    import pyogrio
    assert pyogrio.read_info(os.path.join(out, d["name"]))["features"] == 1


def test_the_recipe_fetches_the_same_files_again(picked, net, tmp_path):
    """Practice 7. The recipe is the catalogue's own table, so fetching
    it into another folder gives the same bytes.

    BROKEN WITH: the recipe written without the `inside` column (the
    .pbf rows are then refused as having no rule)."""
    _need_osm_driver()
    a, b = str(tmp_path / "a"), str(tmp_path / "b")
    res = fr.fetch_rows(picked, a, net=net, say=mute)
    fr.fetch_recipe(res["recipe"], b, net=net, say=mute)
    ma, mb = _manifest(a), _manifest(b)
    data = {n for n in ma if not n.endswith(".gpkg")}
    assert data and {n: ma[n]["sha256"] for n in data} == \
        {n: mb[n]["sha256"] for n in data}
    assert sorted(os.listdir(a)) == sorted(os.listdir(b))


def test_dropping_the_pbf_is_recorded_not_lost(net, tmp_path):
    """keep_pbf=False removes the .pbf after its layers are written;
    the manifest says so, verify reports it as removed - not missing -
    and fetching again downloads nothing, the layers being there.

    BROKEN WITH: verify_folder not reading the 'removed' mark."""
    _need_osm_driver()
    rows = cat.browse_geofabrik("Bayern", "roads, buildings", years="2022",
                                latest=False, net=net, say=mute)
    out = str(tmp_path / "f")
    fr.fetch_rows(rows, out, net=net, say=mute, keep_pbf=False)
    assert "bayern-220101.osm.pbf" not in os.listdir(out)
    v = verify_folder(out, say=mute)
    assert v["removed"] == ["bayern-220101.osm.pbf"] and v["missing"] == []
    assert v["ok"] == 2
    res = fr.fetch_rows(rows, out, net=net, say=mute)
    assert res["downloaded"] == [] and res["derived"] == []


# ======================================================= the converters
class _FakeGdal(types.SimpleNamespace):
    """Just enough of osgeo.gdal to see what EquiPop asks of it."""

    def __init__(self):
        super().__init__(__version__="3.10.0", OF_VECTOR=4, calls=[])

    def UseExceptions(self):
        self.calls.append(("UseExceptions",))

    def GetDriverByName(self, name):
        return object() if name == "OSM" else None

    def VectorTranslateOptions(self, **kw):
        self.calls.append(("options", kw))
        return kw

    def VectorTranslate(self, dest, src, options=None):
        self.calls.append(("translate", dest, src, options))
        with open(dest, "wb") as f:
            f.write(b"SQLite format 3\0")
        return object()

    def OpenEx(self, path, flags):
        lay = types.SimpleNamespace(GetFeatureCount=lambda: 7)
        return types.SimpleNamespace(GetLayer=lambda i: lay)


def test_qgis_gdal_is_asked_for_exactly_the_rule(tmp_path):
    """QGIS has osgeo and not pyogrio, and osgeo cannot be installed
    here - so the call is checked: one OSM layer, the row's filter,
    GeoPackage, the layer named for the row.

    BROKEN WITH: `layers` passed as the bare string 'lines' rather than
    the list GDAL documents."""
    g = _FakeGdal()
    conv = fr.GdalConverter(g)
    out = str(tmp_path / "x.gpkg")
    n = conv.convert("in.osm.pbf", "lines", "highway IS NOT NULL", out,
                     "roads")
    assert n == 7
    opts = [c[1] for c in g.calls if c[0] == "options"][0]
    assert opts == {"format": "GPKG", "layers": ["lines"],
                    "where": "highway IS NOT NULL", "layerName": "roads"}
    assert ("UseExceptions",) in g.calls


def test_qgis_gdal_is_preferred_when_present(monkeypatch):
    """BROKEN WITH: osgeo not tried (pyogrio then chosen)."""
    g = _FakeGdal()
    monkeypatch.setitem(sys.modules, "osgeo",
                        types.SimpleNamespace(gdal=g))
    monkeypatch.setitem(sys.modules, "osgeo.gdal", g)
    assert isinstance(fr.find_converter(), fr.GdalConverter)


def test_the_inventory_does_not_take_the_recipe_for_data(picked, net,
                                                          tmp_path):
    """The recipe is the fetch's record, like the manifest - machine 6
    must not list it among the data.

    BROKEN WITH: the recipe left out of the inventory's skip list."""
    from equipop.doors.inventory import inventory
    out = str(tmp_path / "f")
    wp = [r for r in picked if r["provider"] == "WorldPop"]
    fr.fetch_rows(wp, out, net=net, say=mute)
    got = inventory(out, say=mute, deep=False, write=False)
    files = {os.path.basename(f["file"]) for f in got["files"]}
    assert fr.RECIPE not in files and MANIFEST not in files
    assert any(f.endswith(".tif") for f in files)


def test_a_short_download_is_refused(net, web, tmp_path):
    """A server that announces more bytes than it sends: nothing kept.

    BROKEN WITH: download() not comparing the declared length."""
    url = "https://data.worldpop.org/GIS/short/bdi_pop_2020.tif"
    web.add_file(url, body=fakeweb.tif_bytes(url))
    real = web.__class__.__call__

    def opener(req):
        r = real(web, req)
        if req.full_url == url and req.get_method() == "GET":
            r.headers["Content-Length"] = str(len(web.files[url]["body"])
                                              + 100)
        return r
    dest = str(tmp_path / "x.tif")
    with pytest.raises(FetchError, match="INCOMPLETE"):
        fr.download(cat.Net(opener=opener, pause=0), url, dest)
    assert os.listdir(tmp_path) == []
