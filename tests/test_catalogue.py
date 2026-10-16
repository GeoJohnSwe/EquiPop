# -*- coding: utf-8 -*-
"""test_catalogue.py - machine 5's catalogue: what is there, as a table.

BACKLOG 414, v1.58.0. Every answer here comes from the services as
John's three probe runs found them on 14 October 2026, trimmed into
tests/fixtures/catalogue and served by tests/fakeweb.py - including
what was wrong with them (Norway's missing shapefile, Germany's absent
one, the index's 'Georgia' twice).

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import fakeweb                                       # noqa: E402
from equipop.doors import catalogue as cat          # noqa: E402
from equipop.doors.fetching import FetchError        # noqa: E402


@pytest.fixture
def web():
    return fakeweb.captured()


@pytest.fixture
def net(web):
    return cat.Net(opener=web, pause=0)


def quiet():
    said = []
    return said, said.append


# ============================================================ the table
def test_every_row_has_every_column_in_one_order(net):
    """Practice 2: one table shape for every provider.

    BROKEN WITH: blank_row starting from an empty dict instead of every
    column (rows then hold only the keys their builder gave, in its
    order - Geofabrik's have no sex or ages at all)."""
    _, say = quiet()
    rows = (cat.browse_worldpop("age_sex", "Sweden", "2020", net=net, say=say)
            + cat.browse_geofabrik("Sweden", "roads", net=net, say=say)
            + cat.browse_geofabrik("Bayern", "roads", years="2020",
                                   net=net, say=say))
    assert {r["provider"] for r in rows} == {"WorldPop", "Geofabrik"}
    assert {r["series"] for r in rows} >= {"R2025A", "shapefile", "pbf"}
    for r in rows:
        assert tuple(r) == cat.COLUMN_NAMES


def test_the_table_survives_a_csv_round_trip(net, tmp_path):
    """Practice 7: a recipe is the table itself, so writing and reading
    it must give back the same values, in their own kinds.

    BROKEN WITH: coerce_row leaving age_to as the string '4'."""
    _, say = quiet()
    rows = cat.browse_worldpop("age_sex", "Kenya", "2015", net=net, say=say)
    p = cat.write_csv(rows, str(tmp_path / "t.csv"))
    back = cat.read_csv(p)
    assert back == [cat.coerce_row(r) for r in rows]
    open_top = [r for r in back if r["age_from"] == 90]
    assert open_top and all(r["age_to"] is None for r in open_top)
    assert [r for r in back if r["age_from"] == 1][0]["age_to"] == 4


def test_a_table_without_the_columns_is_refused(tmp_path):
    """BROKEN WITH: read_csv's column check removed."""
    p = tmp_path / "other.csv"
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(FetchError, match="not a catalogue table"):
        cat.read_csv(str(p))


@pytest.mark.parametrize("url", [
    "http://data.worldpop.org/x.tif",              # not https
    "https://example.org/x.tif",                   # not a provider
    "https://worldpop.org.evil.net/x.tif",         # a look-alike
    "https://evilworldpop.org/x.tif",              # another
    "file:///etc/passwd",
    "https://download.geofabrik.de@evil.net/x.pbf",
])
def test_only_the_providers_own_sites(url):
    """A recipe is a CSV anyone can edit; a cell must not decide where
    EquiPop downloads from.

    BROKEN WITH: the domain test written host.endswith(d) without the
    dot, which lets evilworldpop.org through - only that case failed,
    as it should."""
    with pytest.raises(FetchError, match="will not"):
        cat.check_url(url)
    cat.check_url("https://data.worldpop.org/GIS/x.tif")
    cat.check_url("https://download.geofabrik.de/europe/sweden.html")


# ================================================================ years
@pytest.mark.parametrize("given,want", [
    ("2015, 2020", [2015, 2020]), ("2010-2012", [2010, 2011, 2012]),
    ("2012 - 2010", [2010, 2011, 2012]), ([2020, 2015], [2015, 2020]),
    (2020, [2020]), ("", []), (None, []), ("2015;2015\n2016", [2015, 2016]),
])
def test_years_in_plain_words(given, want):
    """BROKEN WITH: the span made exclusive of its last year."""
    assert cat.parse_years(given) == want


@pytest.mark.parametrize("bad", ["twenty", "20", "1850", "2015,x"])
def test_a_year_that_is_not_one_is_refused(bad):
    """BROKEN WITH: the 1900-2100 check removed (1850 then passes)."""
    with pytest.raises(FetchError):
        cat.parse_years(bad)


# =============================================================== places
KNOWN = {"SWE": "Sweden", "KOR": "Republic of Korea",
         "PRK": "Democratic People's Republic of Korea", "COG": "Congo",
         "COD": "Democratic Republic of the Congo", "CIV": "Côte d'Ivoire",
         "GBR": "United Kingdom of Great Britain and Northern Ireland",
         "CHN": "China", "TCD": "Chad"}


@pytest.mark.parametrize("typed,want", [
    ("swe", ["SWE"]), ("Sweden", ["SWE"]), ("cote d'ivoire", ["CIV"]),
    ("Congo", ["COG"]), ("United Kingdom", ["GBR"]),
    ("Sweden, SWE", ["SWE"]),
])
def test_a_place_by_code_name_or_unique_part(typed, want):
    """BROKEN WITH: accents not folded (Côte d'Ivoire unmatched)."""
    assert cat.match_places(typed, KNOWN, "country") == want


def test_every_unrecognised_place_in_one_message():
    """Five places, two wrong: both named at once, an ambiguous one
    with its candidates and a misspelt one with a suggestion.

    BROKEN WITH: the loop raising at the first problem."""
    with pytest.raises(FetchError) as e:
        cat.match_places("Sweden, Korea, Swedn, Congo", KNOWN, "country")
    msg = str(e.value)
    assert "'Korea' fits 2 places" in msg and "(PRK)" in msg
    assert "'Swedn'" in msg and "did you mean Sweden (SWE)" in msg


def test_a_short_code_is_never_a_fragment():
    """'CHA' is somebody's code; as a fragment it would fit China and
    Chad. Three letters match only whole codes and names.

    BROKEN WITH: the four-letter minimum removed - 'CHA' then fits both
    and is refused as ambiguous instead of as unknown, and 'HAD' takes
    Chad silently."""
    with pytest.raises(FetchError, match="'HAD' is not"):
        cat.match_places("HAD", KNOWN, "country")
    with pytest.raises(FetchError, match="'CHA' is not"):
        cat.match_places("CHA", KNOWN, "country")


# ============================================================= WorldPop
def test_johns_first_request(net, web):
    """'Population of all age cohorts and gender, counts for several
    countries and one or two years.' Three countries, two years: 40
    files each (20 bands x f, m), 1 km, R2025A - and SIX size
    requests, one per country and year, not 240.

    BROKEN WITH: the default resolution changed to 100m."""
    said, say = quiet()
    rows = cat.browse_worldpop("age_sex", "Sweden, Kenya, Burundi",
                               "2015, 2020", net=net, say=say)
    assert len(rows) == 3 * 2 * 40
    assert {r["resolution"] for r in rows} == {"1km"}
    assert {r["series"] for r in rows} == {"R2025A"}
    assert {r["sex"] for r in rows} == {"f", "m"}
    assert [r["place_code"] for r in rows[::80]] == ["SWE", "KEN", "BDI"]
    assert web.count("HEAD") == 6
    assert sum(r["size_is"] == "measured" for r in rows) == 6
    assert any("NOTHING HAS BEEN DOWNLOADED" in s for s in said)


def test_the_age_bands_come_from_the_files(net):
    """0 is under one, 1 is 1-4, then five-year bands, and the top band
    has no upper age - read from the bands present, not assumed.

    BROKEN WITH: age_to computed as age_from + 4 for every band."""
    _, say = quiet()
    rows = cat.browse_worldpop("age_sex", "Sweden", "2020", net=net, say=say)
    f = sorted((r["age_from"], r["age_to"]) for r in rows if r["sex"] == "f")
    assert f[:3] == [(0, 0), (1, 4), (5, 9)]
    assert f[-1] == (90, None) and f[-2] == (85, 89)


def test_layers_that_are_sums_of_others_only_when_asked(net):
    """Both sexes (t_) and all ages (T_F, T_M, at 100 m only) add
    nothing that cannot be added up.

    BROKEN WITH: the t_ rows let through when include_totals is off."""
    _, say = quiet()
    one = dict(places="Sweden", years="2020", net=net, say=say)
    assert len(cat.browse_worldpop("age_sex", **one)) == 40
    assert len(cat.browse_worldpop("age_sex", include_totals=True,
                                   **one)) == 60
    rows = cat.browse_worldpop("age_sex", resolution="100m",
                               include_totals=True, **one)
    assert len(rows) == 62
    tot = [r for r in rows if r["layer"].startswith("T_")]
    assert sorted(r["layer"] for r in tot) == ["T_F", "T_M"]
    assert all("sum of" in r["note"] for r in tot)


def test_one_series_for_every_year_when_one_exists(net):
    """2010 and 2020 are both in the 2000-2020 series, so both come
    from it - at 100 m, since that series has no 1 km per country -
    rather than 2020 from R2025A and 2010 from something else.

    BROKEN WITH: the series chosen per year (newest first)."""
    said, say = quiet()
    rows = cat.browse_worldpop("age_sex", "Sweden", "2010, 2020", net=net,
                               say=say)
    assert {(r["series"], r["resolution"]) for r in rows} == \
        {("2000-2020", "100m")}
    assert {r["year"] for r in rows} == {2010, 2020}
    assert max(r["age_from"] for r in rows) == 80          # 80+, not 90+
    assert all("unconstrained" in r["note"] for r in rows)
    assert any("one series for every year" in s for s in said)


def test_mixed_series_are_said_in_every_row(net):
    """2010 and 2025 share no series. The table is still made, and
    every row - not only a log line nobody reads twice - says the
    change between them is partly a change of method.

    BROKEN WITH: the MIXED note added only to the older rows."""
    said, say = quiet()
    rows = cat.browse_worldpop("age_sex", "SWE", "2010, 2025", net=net,
                               say=say)
    assert {r["series"] for r in rows} == {"2000-2020", "R2025A"}
    assert all("MIXED SERIES" in r["note"] for r in rows)
    assert any("PARTLY A CHANGE OF METHOD" in s for s in said)


def test_a_year_nobody_has_names_what_there_is(net):
    """BROKEN WITH: the refusal's span list removed."""
    with pytest.raises(FetchError) as e:
        cat.browse_worldpop("age_sex", "Sweden", "1995", net=net,
                            say=lambda s: None)
    assert "Sweden 1995" in str(e.value) and "2000-2030" in str(e.value)


def test_a_year_the_index_lists_and_the_records_lack_is_said(net):
    """The index and the records are two answers. The fixture's records
    were trimmed to 2000, 2010, 2015, 2020, 2025 while its index kept
    every year - exactly the disagreement to report.

    BROKEN WITH: the `absent` message removed - the table then came back
    one year short, looking complete."""
    said, say = quiet()
    rows = cat.browse_worldpop("population", "Sweden", "2005, 2010",
                               net=net, say=say)
    assert [r["year"] for r in rows] == [2010]
    assert any("Sweden 2005" in s and "do not hold" in s for s in said)


def test_no_year_means_every_year_of_the_newest(net):
    """BROKEN WITH: an empty year refused instead of listed."""
    said, say = quiet()
    rows = cat.browse_worldpop("population", "Kenya", "", net=net, say=say)
    assert any("2015-2030" in s for s in said)
    assert {r["year"] for r in rows} == {2015, 2020, 2025}


def test_population_is_one_file_per_country_and_year(net):
    """BROKEN WITH: the 'pop' file pattern removed - the rows then say
    FILE NAME NOT RECOGNISED."""
    _, say = quiet()
    rows = cat.browse_worldpop("population", "Sweden, Kenya", "2020",
                               net=net, say=say)
    assert [(r["place_code"], r["layer"], r["sex"]) for r in rows] == \
        [("SWE", "pop", "t"), ("KEN", "pop", "t")]
    assert all("NOT RECOGNISED" not in r["note"] for r in rows)
    old = cat.browse_worldpop("population", "Sweden", "2010", net=net,
                              say=say)
    assert [r["file"] for r in old] == ["swe_ppp_2010_1km_Aggregated.tif"]


def test_every_real_file_name_is_understood():
    """All WorldPop names in the captures - R2025A at both resolutions,
    the 2000-2020 series, the population files - parse.

    BROKEN WITH: the 2000-2020 pattern's age written \\d{2} (swe_f_0_
    and swe_f_5_ then fail)."""
    names = set()
    for p in fakeweb.FIX.glob("wp_full_*.json"):
        for rec in json.loads(p.read_text(encoding="utf-8"))["data"]:
            names |= {u.rsplit("/", 1)[1] for u in rec.get("files") or []
                      if u.endswith(".tif")}
    assert len(names) > 1000
    assert [n for n in names if cat.parse_worldpop_name(n) is None] == []


def test_a_file_nobody_recognises_is_listed_not_dropped(net, web):
    """A missing file with no message is the hardest kind to notice.

    BROKEN WITH: unparsed names skipped."""
    url = f"{fakeweb.WP}/pop/G2_CN_POP_R25A_1km?iso3=SWE"
    data = json.loads(json.dumps(web.json[url]))
    data["data"][0]["files"].append(
        "https://data.worldpop.org/GIS/x/swe_new_thing_2015.tif")
    web.add_json(url, data)
    web.add_file("https://data.worldpop.org/GIS/x/swe_new_thing_2015.tif",
                 size=10)
    rows = cat.browse_worldpop("population", "Sweden", "2015", net=net,
                               say=lambda s: None)
    odd = [r for r in rows if r["file"] == "swe_new_thing_2015.tif"]
    assert odd and "NOT RECOGNISED" in odd[0]["note"]


def test_provenance_is_the_publishers_own(net, web):
    """Practice 6: licence, citation and DOI are copied from the record,
    never written here.

    BROKEN WITH: the licence column written as 'CC BY 4.0'."""
    url = f"{fakeweb.WP}/age_structures/G2_CN_Age_R25A_1km?iso3=SWE"
    rec = [r for r in web.json[url]["data"] if r["popyear"] == "2020"][0]
    rows = cat.browse_worldpop("age_sex", "Sweden", "2020", net=net,
                               say=lambda s: None)
    for r in rows:
        assert (r["licence"], r["citation"], r["doi"], r["record_id"]) == \
            (rec["license"], rec["citation"], rec["doi"], rec["id"])


def test_exact_sizes_measure_every_file(net, web):
    """BROKEN WITH: exact_sizes ignored."""
    rows = cat.browse_worldpop("age_sex", "Burundi", "2020", net=net,
                               exact_sizes=True, say=lambda s: None)
    assert web.count("HEAD") == len(rows) == 40
    assert {r["size_is"] for r in rows} == {"measured"}
    assert len({r["size_mb"] for r in rows}) > 1


def test_a_newer_release_than_equipop_knows_is_said(net, web):
    """The products table is written down; a release published after it
    must not be passed over in silence.

    BROKEN WITH: the release comparison made on the year alone (R25B,
    a later release of the same year, then goes unmentioned)."""
    url = f"{fakeweb.WP}/age_structures"
    data = json.loads(json.dumps(web.json[url]))
    data["data"].append({"alias": "G2_CN_Age_R25B_1km", "name": "new"})
    web.add_json(url, data)
    said, say = quiet()
    cat.browse_worldpop("age_sex", "Sweden", "2020", net=net, say=say)
    assert any("G2_CN_Age_R25B_1km" in s and "NEWER" in s for s in said)


# ============================================================ Geofabrik
def test_the_real_swedish_zip_is_twenty_layers():
    """The table of contents John's third probe read from Sweden's
    1.87 GB zip: twenty layers of five files, the README left out, and
    buildings 329 MB packed.

    BROKEN WITH: names outside the pattern (the README) kept as a layer
    of their own."""
    toc = fakeweb.fixture("geofabrik_sweden_shp_toc.json")
    layers = cat.layers_in_zip(toc)
    assert len(layers) == 20
    assert all(len(d["members"]) == 5 for d in layers.values())
    assert round(layers["buildings_a"]["packed"] / 1e6) == 329
    assert sum(d["packed"] for d in layers.values()) < sum(
        m["packed"] for m in toc)                          # README out


def test_a_layer_in_numbered_parts_is_one_layer():
    """BROKEN WITH: parts keyed separately (two 'buildings_a' entries)."""
    members = [(f"gis_osm_buildings_a_free_{p}.{e}", 10, 5)
               for p in (1, 2) for e in ("shp", "dbf")]
    d = cat.layers_in_zip(members)["buildings_a"]
    assert d["parts"] == [1, 2] and len(d["members"]) == 4


def test_johns_second_request_reads_only_the_end_of_the_zip(net, web):
    """'Buildings in one or more countries.' One row per layer, its size
    the packed size of just that layer, its name carrying the extract's
    date - and three requests: the index, a HEAD, one range.

    BROKEN WITH: the row size taken from the whole zip's length."""
    _, say = quiet()
    rows = cat.browse_geofabrik("Sweden", "buildings", net=net, say=say)
    assert len(rows) == 1
    r = rows[0]
    assert (r["layer"], r["date"], r["series"]) == \
        ("buildings_a", "2026-10-14", "shapefile")
    assert r["file"] == "sweden_20261014_buildings_a.shp"
    assert len(r["inside"].split(";")) == 5
    import io
    import zipfile
    body = web.files[r["url"]]["body"]
    packed = sum(i.compress_size for i in zipfile.ZipFile(
        io.BytesIO(body)).infolist()
        if i.filename.startswith("gis_osm_buildings_a_free_"))
    assert r["size_mb"] == round(packed / 1e6, 3) != round(len(body) / 1e6, 3)
    assert len(web.log) == 3 and web.log[2][2].startswith("bytes=")


def test_johns_third_request_roads_railways_and_pois(net):
    """'All roads and railroads; or all POI' - POIs are two layers,
    points and areas.

    BROKEN WITH: 'pois' mapped to the point layer only."""
    rows = cat.browse_geofabrik("Kenya", "roads, railways, pois", net=net,
                                say=lambda s: None)
    assert [r["layer"] for r in rows] == ["roads", "railways", "pois",
                                          "pois_a"]


def test_a_country_without_a_shapefile_is_its_parts(net):
    """Geofabrik publishes no shapefile for Germany; it does for each
    state, so the states are listed, each saying whose part it is.

    BROKEN WITH: shapefile_regions returning the country itself."""
    said, say = quiet()
    rows = cat.browse_geofabrik("Germany", "roads", net=net, say=say)
    assert [r["place_code"] for r in rows] == ["bayern", "berlin"]
    assert all("part of Germany" in r["note"] for r in rows)
    assert any("no shapefile for the whole of it" in s for s in said)


def test_the_united_states_are_found_by_their_ids(net):
    """The US states name North America as their parent and carry 'us/'
    in their id (probe round 1); California again has no shapefile and
    is its two halves.

    BROKEN WITH: _children reading the parent field only."""
    rows = cat.browse_geofabrik("us", "roads", net=net, say=lambda s: None)
    assert [r["place_code"] for r in rows] == ["us/alabama", "norcal",
                                               "socal"]
    assert rows[0]["file"].startswith("us-alabama_")


def test_a_missing_shapefile_falls_back_to_the_pbf(net):
    """Norway's shapefile is in the index and 404 on the server (probe
    round 3). The .pbf of the same day is there, so it is listed, and
    the row says why.

    BROKEN WITH: the 404 left to raise."""
    said, say = quiet()
    rows = cat.browse_geofabrik("Norway", "buildings", net=net, say=say)
    assert [(r["series"], r["layer"]) for r in rows] == \
        [("pbf", "buildings_a")]
    assert "could not be reached" in rows[0]["note"]
    assert rows[0]["file"] == "norway_20261014_buildings_a.gpkg"
    assert any("answered 404" in s for s in said)


def test_years_come_from_dated_pbf_and_so_does_today(net):
    """With years, EVERY row - the current extract too - is from a
    .pbf, so two years are never two classifications. Each layer of
    one .pbf is one row, sharing one download.

    BROKEN WITH: the current extract left as shapefile rows."""
    said, say = quiet()
    rows = cat.browse_geofabrik("Bayern", "buildings, roads",
                                years="2020, 2021, 2022", net=net, say=say)
    assert {r["series"] for r in rows} == {"pbf"}
    assert sorted({r["date"] for r in rows}) == \
        ["2020-01-01", "2022-01-01", "2026-10-14"]
    assert any("2021-01-01" in s and "404" in s for s in said)
    assert {r["size_is"] for r in rows} == {"shared"}
    mb, n, _ = cat.total_mb(rows)
    assert n == 3                                 # three .pbf, six rows
    assert rows[0]["inside"] == cat.PBF_RULES["buildings_a"]
    assert rows[0]["md5_url"] == rows[0]["url"] + ".md5"


def test_a_layer_with_no_pbf_rule_is_refused_before_asking(net, web):
    """BROKEN WITH: the rule check removed - a KeyError then arrives,
    after the HEAD requests have been made."""
    with pytest.raises(FetchError, match="no rule for transport"):
        cat.browse_geofabrik("Bayern", "transport", years="2020", net=net)
    assert web.count("HEAD") == 0


def test_georgia_is_two_places(net):
    """A country whose id is 'georgia' and a US state named 'Georgia':
    the id must not win in silence. Each is reachable by its code.

    BROKEN WITH: the id matched before the names (the old tiering)."""
    with pytest.raises(FetchError) as e:
        cat.browse_geofabrik("Georgia", "roads", net=net)
    assert "Georgia (in Europe) (georgia)" in str(e.value)
    assert "Georgia (in North America) (us/georgia)" in str(e.value)
    gf = cat.GeofabrikCatalogue(net)
    assert gf.resolve("GE, US-GA") == ["georgia", "us/georgia"]


def test_a_three_letter_code_gets_a_hint(net):
    """BROKEN WITH: the hint's pattern written for two letters."""
    with pytest.raises(FetchError, match="two-letter code"):
        cat.browse_geofabrik("SWE", "roads", net=net)


@pytest.mark.parametrize("asked,want", [
    ("buildings", ["buildings_a"]), ("POIs", ["pois", "pois_a"]),
    ("roads, roads", ["roads"]), ("pois_a", ["pois_a"]),
])
def test_layers_in_plain_words(asked, want):
    """BROKEN WITH: themes not case-folded ('POIs' refused)."""
    assert cat.gf_layers(asked) == want


def test_all_is_every_layer_and_nonsense_is_refused():
    """BROKEN WITH: 'all' not expanded."""
    assert len(cat.gf_layers("all")) == 20
    with pytest.raises(FetchError, match="No OpenStreetMap layer 'bridges'"):
        cat.gf_layers("bridges")


def test_a_replaced_zip_is_noticed_not_mixed(net, web):
    """If-Range: the zip replaced between the HEAD and the range read
    must answer with the whole new file - and be refused - rather than
    hand over bytes of the new zip at the old one's offsets.

    BROKEN WITH: get_range sending no If-Range header."""
    url = "https://download.geofabrik.de/europe/sweden-latest-free.shp.zip"
    st, h = net.head(url)
    from datetime import datetime, timezone
    web.replace(url, fakeweb.shapefile_zip("sweden", seed=1),
                datetime(2026, 10, 15, 21, tzinfo=timezone.utc))
    with pytest.raises(cat.NetError, match="REPLACED"):
        cat.zip_contents(net, url, cat.size_of(h), cat.validator_of(h))


def test_the_rules_are_real_ogr_filters():
    """Every pbf rule parses, names a layer of GDAL's OSM driver, and is
    accepted by GDAL as a filter on the tiny extract.

    BROKEN WITH: the buildings rule written 'polygons: ...' (no such
    layer in the OSM driver)."""
    pyogrio = pytest.importorskip("pyogrio")
    if "OSM" not in pyogrio.list_drivers():
        pytest.skip("GDAL here has no OSM driver")
    import pyogrio.raw as raw
    src = str(fakeweb.FIX / "tiny.osm.pbf")
    got = {}
    for layer, rule in cat.PBF_RULES.items():
        osm, where = cat.parse_rule(rule)
        got[layer] = len(raw.read(src, layer=osm, where=where)[2])
    assert got["buildings_a"] == 1 and got["roads"] == 1
    assert got["railways"] == 1 and got["pois"] == 1 and got["places"] == 1
    assert got["pois_a"] == 0


def test_a_rule_that_is_not_one_is_refused():
    """BROKEN WITH: parse_rule accepting any word before the colon."""
    with pytest.raises(FetchError):
        cat.parse_rule("polygons: building IS NOT NULL")
    with pytest.raises(FetchError):
        cat.parse_rule("building IS NOT NULL")
