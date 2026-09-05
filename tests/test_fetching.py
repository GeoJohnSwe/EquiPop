"""MACHINE 5 - fetching, tested against REAL API responses.

BACKLOG 240. The download leg is the one part that CANNOT be
exercised in development: every WorldPop host is blocked from the
sandbox, verified - 403 at the proxy for hub, data and www. So the
transport is two tiny functions and everything else is tested here,
with John's own captured JSON standing in for the network.

That matters more than usual. The published WorldPop API
documentation is from 2022 and is STALE: it lists four projects where
the live API returns eighteen, and shows `ftp://` download URLs where
the live API returns `https://data.worldpop.org`. An adapter built
from the documentation would have been wrong in both places - John's
FTP was blocked, so it would have failed on his machine and worked
nowhere.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from equipop.doors.fetching import (FetchError, MANIFEST, PROVIDERS,
                                    plan_fetch, read_manifest, run_fetch,
                                    sha256_of, verify_folder)

HERE = Path(__file__).resolve().parent
CAPTURED = HERE / "fixtures" / "worldpop_api"


def _load(name):
    with open(CAPTURED / name, encoding="utf-8") as f:
        return json.load(f)


def _fake_json(mapping, has_iso=("BDI",)):
    """A transport that answers from captured responses, by URL.

    IT MUST HONOUR ?iso3= . The first version matched on a URL
    fragment only, so a request for ZZZ returned Burundi's records and
    a test asserting "no such country" failed against code that was
    correct. A stand-in looser than the thing it stands in for
    certifies the wrong behaviour - the same fault as the QGIS
    simulator accepting a bare int for a WKB type (BACKLOG 221).
    """
    def get(url, timeout=60):
        if "iso3=" in url:
            want = url.split("iso3=", 1)[1].split("&")[0].upper()
            if want not in has_iso:
                return {"data": []}
        for frag, payload in mapping.items():
            if frag in url:
                return payload
        raise AssertionError(f"no captured response for {url}")
    return get


@pytest.fixture
def api():
    root = _load("data.json")
    bdi = _load("wpgp.json")
    cats = {"data": [{"alias": "wpgp",
                      "name": "Global per country 2000-2020"}]}
    return _fake_json({"rest/data/pop/wpgp": bdi,
                       "rest/data/pop": cats,
                       "rest/data": root})


def _quiet(*a, **k):
    pass


# ------------------------------------------------- the live catalogue
def test_the_live_api_offers_far_more_than_the_docs_describe(api):
    """The 2022 documentation lists four projects. There are eighteen,
    and age_structures - the one this project needs - is not in the
    docs at all."""
    got = PROVIDERS["worldpop"].projects(get_json=api)
    assert len(got) > 10, got
    assert "age_structures" in got
    for old in ("pop", "births", "pregnancies", "urban_change"):
        assert old in got, "the documented four should still be there"


def test_download_urls_are_https_not_ftp(api):
    """The docs show ftp://ftp.worldpop.org.uk. The live API returns
    https://data.worldpop.org - and John's FTP is blocked, so an
    adapter built from the documentation would have failed on his
    machine."""
    recs = PROVIDERS["worldpop"].records("pop", "wpgp", "BDI",
                                         get_json=api)
    urls = [u for r in recs for u in (r.get("files") or [])]
    assert urls
    assert all(u.startswith("https://") for u in urls), urls[:3]
    assert not any(u.startswith("ftp://") for u in urls)


def test_provenance_comes_from_the_provider_not_from_us(api):
    """doi, citation and licence are stated by WorldPop. The manifest
    records what they say rather than what EquiPop assumed."""
    recs = PROVIDERS["worldpop"].records("pop", "wpgp", "BDI",
                                         get_json=api)
    e = PROVIDERS["worldpop"].entries(recs[0])[0]
    assert e["doi"] and e["citation"] and e["licence"]
    assert "worldpop" in e["citation"].lower()


# ------------------------------------------------------------- plan
def test_a_plan_downloads_nothing(api, tmp_path):
    before = set(os.listdir(tmp_path))
    plan = plan_fetch(project="pop", iso3="BDI", year=2000,
                      get_json=api, say=_quiet)
    assert plan["entries"]
    assert set(os.listdir(tmp_path)) == before, "a plan must not write"


def test_the_plan_says_what_it_would_do(api):
    said = []
    plan_fetch(project="pop", iso3="BDI", year=2000, get_json=api,
               say=said.append)
    text = " ".join(said)
    assert "NOTHING HAS BEEN DOWNLOADED" in text
    assert "licence" in text
    assert "bdi_ppp_2000.tif" in text


def test_a_year_narrows_the_records(api):
    allyears = plan_fetch(project="pop", iso3="BDI", get_json=api,
                          say=_quiet)
    one = plan_fetch(project="pop", iso3="BDI", year=2000,
                     get_json=api, say=_quiet)
    assert len(one["entries"]) < len(allyears["entries"])
    assert all(str(e["year"]) == "2000" for e in one["entries"])


# ---------------------------------------------------------- refusals
def test_an_unknown_dataset_lists_the_real_ones(api):
    with pytest.raises(FetchError, match="No such dataset"):
        plan_fetch(project="fertility", iso3="BDI", get_json=api,
                   say=_quiet)


def test_an_unknown_provider_is_refused():
    with pytest.raises(FetchError, match="No such provider"):
        plan_fetch("censusbureau", project="pop", iso3="BDI")


def test_a_country_with_nothing_says_which(api):
    with pytest.raises(FetchError, match="ZZZ"):
        plan_fetch(project="pop", iso3="ZZZ", year=2000, get_json=api,
                   say=_quiet)


def test_a_year_with_nothing_says_so(api):
    with pytest.raises(FetchError, match="1066"):
        plan_fetch(project="pop", iso3="BDI", year=1066, get_json=api,
                   say=_quiet)


def test_no_country_is_refused(api):
    with pytest.raises(FetchError, match="Which country"):
        plan_fetch(project="pop", iso3=[], get_json=api, say=_quiet)


# ------------------------------------------------------------- fetch
def _fake_files(bodies):
    """A transport that writes canned bytes instead of downloading."""
    import hashlib

    def get(url, dest, timeout=900):
        body = bodies.get(os.path.basename(url), b"raster-bytes")
        with open(dest, "wb") as f:
            f.write(body)
        return len(body), hashlib.sha256(body).hexdigest()
    return get


def test_a_fetch_writes_the_files_and_a_manifest(api, tmp_path):
    plan = plan_fetch(project="pop", iso3="BDI", year=2000,
                      get_json=api, say=_quiet)
    man = run_fetch(plan, str(tmp_path), get_file=_fake_files({}),
                    say=_quiet)
    assert (tmp_path / MANIFEST).exists()
    assert len(man["files"]) == len(plan["entries"])
    for f in man["files"]:
        assert (tmp_path / f["name"]).exists()
        assert len(f["sha256"]) == 64


def test_the_manifest_records_what_reproducibility_needs(api, tmp_path):
    """The manifest IS the deliverable. Without these a downloaded
    raster is less reproducible than one a colleague emailed."""
    plan = plan_fetch(project="pop", iso3="BDI", year=2000,
                      get_json=api, say=_quiet)
    run_fetch(plan, str(tmp_path), get_file=_fake_files({}), say=_quiet)
    man = read_manifest(str(tmp_path))
    assert man["fetched_utc"].endswith("Z")
    assert man["fetched_by"].startswith("EquiPop ")
    assert man["provider"] == "worldpop"
    f = man["files"][0]
    for key in ("url", "sha256", "bytes", "doi", "citation", "licence",
                "published", "title"):
        assert f.get(key), f"the manifest lost {key}"


def test_a_second_fetch_reuses_and_does_not_redownload(api, tmp_path):
    plan = plan_fetch(project="pop", iso3="BDI", year=2000,
                      get_json=api, say=_quiet)
    run_fetch(plan, str(tmp_path), get_file=_fake_files({}), say=_quiet)

    def explode(url, dest, timeout=900):
        raise AssertionError("it re-downloaded an existing file")

    man = run_fetch(plan, str(tmp_path), get_file=explode, say=_quiet)
    assert all(f["reused"] for f in man["files"])


def test_a_CHANGED_file_stops_the_run_and_is_named(api, tmp_path):
    """John's ruling. Whatever was computed from that file was
    computed from THAT file, so replacing it silently is the worst
    available option."""
    plan = plan_fetch(project="pop", iso3="BDI", year=2000,
                      get_json=api, say=_quiet)
    run_fetch(plan, str(tmp_path), get_file=_fake_files({}), say=_quiet)
    victim = tmp_path / plan["entries"][0]["name"]
    victim.write_bytes(b"something else entirely")
    with pytest.raises(FetchError, match="CHANGED"):
        run_fetch(plan, str(tmp_path), get_file=_fake_files({}),
                  say=_quiet)


def test_overwriting_is_refused_when_asked_not_to_skip(api, tmp_path):
    plan = plan_fetch(project="pop", iso3="BDI", year=2000,
                      get_json=api, say=_quiet)
    run_fetch(plan, str(tmp_path), get_file=_fake_files({}), say=_quiet)
    with pytest.raises(FetchError, match="Refusing to overwrite"):
        run_fetch(plan, str(tmp_path), get_file=_fake_files({}),
                  say=_quiet, skip_existing=False)


# ------------------------------------------------------------ verify
def test_verify_says_a_folder_is_untouched(api, tmp_path):
    plan = plan_fetch(project="pop", iso3="BDI", year=2000,
                      get_json=api, say=_quiet)
    run_fetch(plan, str(tmp_path), get_file=_fake_files({}), say=_quiet)
    got = verify_folder(str(tmp_path), say=_quiet)
    assert got["ok"] == len(plan["entries"])
    assert not got["changed"] and not got["missing"]


def test_verify_finds_a_changed_file_a_year_later(api, tmp_path):
    plan = plan_fetch(project="pop", iso3="BDI", year=2000,
                      get_json=api, say=_quiet)
    run_fetch(plan, str(tmp_path), get_file=_fake_files({}), say=_quiet)
    (tmp_path / plan["entries"][0]["name"]).write_bytes(b"edited")
    got = verify_folder(str(tmp_path), say=_quiet)
    assert got["changed"] == [plan["entries"][0]["name"]]


def test_verify_refuses_a_folder_it_did_not_fetch(tmp_path):
    with pytest.raises(FetchError, match="not fetched by EquiPop"):
        verify_folder(str(tmp_path), say=_quiet)


# ------------------------------------------------- the standing rule
def test_the_fetcher_never_analyses_anything():
    """HANDOVER 13 section 3c: it downloads, writes a manifest, and
    STOPS. If this module ever imports the engine, the rule has been
    broken and reproducibility has left with it."""
    src = (Path(__file__).resolve().parents[1] / "equipop" / "doors"
           / "fetching.py").read_text(encoding="utf-8")
    for banned in ("run_knn", "build_cells", "run_folder",
                   "run_indices", "fastcounts", "rasterfolder"):
        assert banned not in src, (
            f"the fetcher references {banned} - it must fetch and stop")


def test_categories_that_cannot_be_chosen_are_not_offered():
    """BACKLOG 242. John's run of `pop` listed 17 categories and the
    first was a BLANK LINE - a catalogue entry whose alias is empty
    and whose name is a bare DOI stub, WP00643. It cannot be passed to
    --category, so listing it is worse than a shorter list.
    """
    def fake(url, timeout=60):
        return {"data": [{"alias": "", "name": "WP00643"},
                         {"alias": "  ", "name": "whitespace"},
                         {"name": "no alias key at all"},
                         {"alias": "wpgp", "name": "the real one"}]}
    got = PROVIDERS["worldpop"].categories("pop", get_json=fake)
    assert got == {"wpgp": "the real one"}


def test_the_category_refusal_lists_what_can_actually_be_typed(api):
    """The refusal is the tool's most useful output here: 17 real
    datasets differing by constraint, resolution and release. Every
    line must be something the user can paste back."""
    def many(url, timeout=60):
        if url.endswith("/pop"):
            return {"data": [{"alias": "", "name": "WP00643"},
                             {"alias": "wpgp1km", "name": "1km"},
                             {"alias": "wpgp", "name": "100m"}]}
        return api(url)
    with pytest.raises(FetchError) as e:
        plan_fetch(project="pop", iso3="BDI", get_json=many, say=_quiet)
    msg = str(e.value)
    assert "wpgp1km" in msg and "wpgp" in msg
    assert "WP00643" not in msg
    for line in msg.splitlines()[1:]:
        assert line.strip(), "a blank line is not a choice"


def test_the_plan_does_not_contradict_a_go_run(api):
    """BACKLOG 243. A --go run printed NOTHING HAS BEEN DOWNLOADED and
    then downloaded on the very next line. A tool that contradicts
    itself twice in two lines teaches the reader to stop reading it."""
    said = []
    plan_fetch(project="pop", iso3="BDI", year=2000, get_json=api,
               say=said.append, will_download=True)
    text = " ".join(said)
    assert "NOTHING HAS BEEN DOWNLOADED" not in text
    assert "Downloading now" in text


def test_a_plain_plan_still_says_it_downloaded_nothing(api):
    said = []
    plan_fetch(project="pop", iso3="BDI", year=2000, get_json=api,
               say=said.append)
    assert "NOTHING HAS BEEN DOWNLOADED" in " ".join(said)


# ---------------------------------------------------------------------
# BACKLOG 250. John left both boxes empty, got "bic Individual
# countries", typed exactly that, and was refused. Quite reasonable:
# the line LOOKS like one string. His suggestion - number them - is
# the fix, and the whole pasted line now works too.
# ---------------------------------------------------------------------
def test_the_listing_is_numbered_and_columned():
    from equipop.doors.fetching import numbered
    got = numbered({"bic": "Individual countries",
                    "age_structures": "Age and sex structures"})
    assert got[0].strip().startswith("1 ")
    assert got[1].strip().startswith("2 ")
    # the alias stands in its own column, so it cannot be read as
    # part of the description
    assert "age_structures  Age and sex" in got[0]


@pytest.mark.parametrize("typed", ["2", "#2", " 2 ", "bic",
                                   "bic Individual countries"])
def test_a_choice_may_be_a_number_an_alias_or_the_whole_line(typed):
    from equipop.doors.fetching import resolve
    opts = {"age_structures": "Age and sex", "bic": "Individual countries",
            "pop": "Population Counts"}
    assert resolve(typed, opts, "dataset") == "bic"


def test_a_number_out_of_range_says_how_many_there_are():
    from equipop.doors.fetching import resolve
    with pytest.raises(FetchError, match="there are 2"):
        resolve("9", {"a": "A", "b": "B"}, "dataset")


def test_an_unknown_name_reprints_the_numbered_list():
    from equipop.doors.fetching import resolve
    with pytest.raises(FetchError) as e:
        resolve("nonsense", {"a": "A", "b": "B"}, "dataset")
    assert "1  a" in str(e.value) and "2  b" in str(e.value)


def test_a_wrong_year_LISTS_THE_YEARS_THAT_EXIST():
    """John: "worldpop has nothing for BDI in births/bic for 2001.
    Check the ISO3 code and the year." The country was right and only
    the year was wrong, and the answer was already in hand."""
    recs = [{"popyear": y, "iso3": "BDI", "files": [f"https://x/{y}.tif"]}
            for y in (2000, 2010, 2015, 2020)]

    def fake(url, timeout=60):
        if "rest/data/births/bic" in url:
            return {"data": recs}
        if "rest/data/births" in url:
            return {"data": [{"alias": "bic", "name": "Individual"}]}
        return {"data": [{"alias": "births", "name": "Births"}]}

    with pytest.raises(FetchError) as e:
        plan_fetch(project="births", category="bic", iso3="BDI",
                   year=2001, get_json=fake, say=_quiet)
    msg = str(e.value)
    assert "2000, 2010, 2015, 2020" in msg
    assert "Check the ISO3" not in msg, (
        "the country was fine; do not send them hunting for it")


def test_a_country_that_has_nothing_is_still_told_about_the_code():
    def fake(url, timeout=60):
        if "rest/data/births/bic" in url:
            return {"data": []}
        if "rest/data/births" in url:
            return {"data": [{"alias": "bic", "name": "Individual"}]}
        return {"data": [{"alias": "births", "name": "Births"}]}

    with pytest.raises(FetchError, match="three-letter"):
        plan_fetch(project="births", category="bic", iso3="ZZZ",
                   year=2001, get_json=fake, say=_quiet)


def test_a_product_with_no_years_does_not_blame_the_year_box():
    """BACKLOG 253. dahi records carry no popyear, so the refusal
    printed "The years it does have: BDI:" and then nothing - telling
    the user to choose from an empty list."""
    def fake(url, timeout=60):
        if "rest/data/dahi/dhic" in url:
            return {"data": [{"iso3": "BDI",
                              "files": ["https://x/a.tif"]}]}
        if "rest/data/dahi" in url:
            return {"data": [{"alias": "dhic", "name": "Individual"}]}
        return {"data": [{"alias": "dahi", "name": "Development"}]}

    with pytest.raises(FetchError) as e:
        plan_fetch(project="dahi", category="dhic", iso3="BDI",
                   year=2001, get_json=fake, say=_quiet)
    msg = str(e.value)
    assert "carry NO YEAR" in msg
    assert "Clear it" in msg
    assert "The years it does have" not in msg, (
        "do not offer a list that is empty")


def test_a_mixed_case_still_lists_the_years_that_exist():
    """One country with years, one without - both must read sensibly."""
    def fake(url, timeout=60):
        if "iso3=RWA" in url:
            return {"data": [{"iso3": "RWA",
                              "files": ["https://x/r.tif"]}]}
        if "rest/data/pop/wpgp" in url:
            return {"data": [{"iso3": "BDI", "popyear": 2000,
                              "files": ["https://x/b.tif"]}]}
        if "rest/data/pop" in url:
            return {"data": [{"alias": "wpgp", "name": "x"}]}
        return {"data": [{"alias": "pop", "name": "Population"}]}

    with pytest.raises(FetchError) as e:
        plan_fetch(project="pop", category="wpgp", iso3=["BDI", "RWA"],
                   year=2001, get_json=fake, say=_quiet)
    msg = str(e.value)
    assert "BDI: 2000" in msg
    assert "RWA: no year recorded" in msg


# ---------------------------------------------------------------------
# BACKLOG 254. John chose version 5 of `pop` - G2_MOS_POP_R25A_1km,
# "Global mosaics" - and asked for BDI. The refusal said "Check the
# ISO3 code", so he checked a code that was correct. A global mosaic
# holds no single country and never will.
# ---------------------------------------------------------------------
@pytest.mark.parametrize("name,per_country", [
    ("Individual countries 2015-2030 ( 1km resolution ) R2025A v1", True),
    ("Unconstrained individual countries 2000-2020 ( 100m )", True),
    ("Constrained Individual countries 2020 UN adjusted", True),
    ("Global mosaics 2015-2030 ( 1km resolution ) R2025A v1", False),
    ("Unconstrained global mosaics 2000-2020 ( 1km resolution )", False),
    ("Whole Continent", False),
])
def test_the_catalogue_says_which_products_are_per_country(name,
                                                           per_country):
    from equipop.doors.fetching import is_per_country
    assert is_per_country(name) is per_country


def _pop_api(records=None):
    cats = {"G2_MOS_POP_R25A_1km": "Global mosaics 2015-2030 ( 1km )",
            "G2_CN_POP_R25A_1km": "Individual countries 2015-2030 ( 1km )",
            "wpgp": "Unconstrained individual countries 2000-2020",
            "pop_continent": "Whole Continent"}

    def fake(url, timeout=60):
        if "/pop/" in url:
            return {"data": records or []}
        if url.rstrip("/").endswith("/pop"):
            return {"data": [{"alias": k, "name": v}
                             for k, v in cats.items()]}
        return {"data": [{"alias": "pop", "name": "Population Counts"}]}
    return fake


def test_a_global_product_says_so_instead_of_blaming_the_code():
    with pytest.raises(FetchError) as e:
        plan_fetch(project="pop", category="G2_MOS_POP_R25A_1km",
                   iso3="BDI", year=2001, get_json=_pop_api(),
                   say=_quiet)
    msg = str(e.value)
    assert "GLOBAL product" in msg
    assert "never work" in msg
    assert "Check the ISO3" not in msg, (
        "his code was right; do not send him to check it")


def test_it_lists_the_PER_COUNTRY_versions_so_the_fix_is_one_step():
    with pytest.raises(FetchError) as e:
        plan_fetch(project="pop", category="G2_MOS_POP_R25A_1km",
                   iso3="BDI", get_json=_pop_api(), say=_quiet)
    msg = str(e.value)
    assert "G2_CN_POP_R25A_1km" in msg and "wpgp" in msg
    assert "pop_continent" not in msg, "a continent is not per-country"
    assert "G2_MOS_POP_R25A_1km" in msg.split("versions of")[0], (
        "name the offending one, then the alternatives")


def test_a_per_country_product_with_a_bad_code_still_says_so():
    """The old message was right for the case it was written for."""
    with pytest.raises(FetchError, match="three-letter"):
        plan_fetch(project="pop", category="wpgp", iso3="ZZZ",
                   get_json=_pop_api(), say=_quiet)


# ---------------------------------------------------------------------
# BACKLOG 256. The spine took project, category, iso3 and year as fixed
# keyword arguments - WorldPop's shape, baked into the machine. GHSL is
# tiled globally and has no iso3; Overture has no year; HDX has
# neither. A rule shaped by one case and discovered when the second
# arrives is this project's most repeated mistake, so it was loosened
# BEFORE the second adapter rather than after.
#
# The proof is a provider shaped NOTHING like WorldPop.
# ---------------------------------------------------------------------
class _Tiles:
    """A pretend provider with no countries and no years."""

    name = "tiles"
    FIELDS = [
        {"name": "release", "label": "Release", "required": True},
        {"name": "tile", "label": "Tile", "required": True,
         "missing": "Which tile? They look like R4_C19."},
        {"name": "band", "label": "Band", "required": False},
    ]

    def plan(self, choices, get_json=None, say=print):
        rel, tile = choices["release"], choices["tile"]
        if tile != "R4_C19":
            raise FetchError(f"No tile {tile!r} in {rel}.")
        return ([{"url": f"https://x/{rel}/{tile}.tif",
                  "name": f"{tile}.tif", "licence": "CC-BY 4.0"}],
                {"release": rel, "tile": tile})


@pytest.fixture
def tiles():
    from equipop.doors import fetching as F
    F.PROVIDERS["tiles"] = _Tiles()
    yield
    F.PROVIDERS.pop("tiles", None)


def test_a_provider_with_no_countries_and_no_years_works(tiles):
    plan = plan_fetch("tiles", release="R2023A", tile="R4_C19",
                      say=_quiet)
    assert plan["provider"] == "tiles"
    assert plan["release"] == "R2023A" and plan["tile"] == "R4_C19"
    assert len(plan["entries"]) == 1
    assert "iso3" not in plan and "year" not in plan


def test_the_spine_reports_what_that_provider_asks_for(tiles):
    with pytest.raises(FetchError, match="does not take iso3"):
        plan_fetch("tiles", release="R2023A", iso3="BDI", say=_quiet)


def test_a_field_may_carry_its_own_wording(tiles):
    """Moving a check up a layer must not cost the user the better
    message. The generic "tiles needs tile - Tile" is correct and
    worse than the sentence the adapter can write."""
    with pytest.raises(FetchError, match="They look like R4_C19"):
        plan_fetch("tiles", release="R2023A", say=_quiet)


def test_a_field_without_its_own_wording_still_gets_a_message(tiles):
    with pytest.raises(FetchError, match="needs release - Release"):
        plan_fetch("tiles", tile="R4_C19", say=_quiet)


def test_the_spine_never_mentions_worldpops_vocabulary():
    """If 'iso3' or 'popyear' appear in plan_fetch itself, the shape
    has leaked back in."""
    src = (Path(__file__).resolve().parents[1] / "equipop" / "doors"
           / "fetching.py").read_text(encoding="utf-8")
    spine = src[src.index("def plan_fetch("):src.index("def run_fetch(")]
    for word in ("iso3", "popyear", "country", "ISO3"):
        assert word not in spine, (
            f"the spine mentions {word!r} - a provider's vocabulary "
            "has leaked back into the machine")


def test_a_downloaded_plan_from_any_provider_still_writes_a_manifest(
        tiles, tmp_path):
    import hashlib

    def fake(url, dest, timeout=900):
        with open(dest, "wb") as f:
            f.write(b"tile")
        return 4, hashlib.sha256(b"tile").hexdigest()

    plan = plan_fetch("tiles", release="R2023A", tile="R4_C19",
                      say=_quiet)
    man = run_fetch(plan, str(tmp_path), get_file=fake, say=_quiet)
    assert man["provider"] == "tiles"
    assert man["files"][0]["sha256"]


# ---------------------------------------------------------------------
# BACKLOG 261 - HDX, confirmed against John's real package_search
# response for Sweden, 2 Sep 2026. Two things that response settled,
# and the second broke an assumption in PROVIDERS_PLAN.md.
# ---------------------------------------------------------------------
def _hdx_api():
    with open(CAPTURED / "hdx_swe.json", encoding="utf-8") as f:
        rec = json.load(f)
    return lambda url, timeout=60: rec


def test_hdx_is_a_provider():
    from equipop.doors.fetching import PROVIDERS
    assert "hdx" in PROVIDERS


def test_no_dataset_lists_them_numbered():
    with pytest.raises(FetchError) as e:
        plan_fetch("hdx", country="swe", get_json=_hdx_api(), say=_quiet)
    msg = str(e.value)
    assert "iati-swe" in msg and "cod-ab-swe" in msg
    assert "1  " in msg, "numbered, as everywhere else"


def test_every_resource_carries_THE_PUBLISHERS_OWN_MD5():
    """Like Geofabrik, HDX states a hash. That lets a download be
    checked against what the PUBLISHER says the file is, not merely
    against the bytes that arrived. WorldPop offers nothing of the
    kind."""
    plan = plan_fetch("hdx", country="swe", dataset="iati-swe",
                      get_json=_hdx_api(), say=_quiet)
    for e in plan["entries"]:
        assert e["publisher_md5"], e["name"]
        assert len(e["publisher_md5"]) == 32


def test_an_unresolvable_licence_is_admitted_not_guessed():
    """THE ASSUMPTION THIS BROKE. PROVIDERS_PLAN.md said the manifest
    would record whether a source may be redistributed and whether it
    imposes share-alike. For HDX that is often UNKNOWABLE: the IATI
    dataset returns license_id 'hdx-other', title 'Other', and prose
    pointing at a web page. Guessing would be worse than admitting."""
    e = plan_fetch("hdx", country="swe", dataset="iati-swe",
                   get_json=_hdx_api(), say=_quiet)["entries"][0]
    assert e["licence_id"] == "hdx-other"
    assert e["may_redistribute"] is None
    assert e["share_alike"] is None
    assert e["licence_note"], "the prose must survive for a human"


def test_a_known_licence_IS_resolved():
    e = plan_fetch("hdx", country="swe", dataset="cod-ab-swe",
                   get_json=_hdx_api(), say=_quiet)["entries"][0]
    assert e["licence_id"] == "cc-by"
    assert e["may_redistribute"] is True
    assert e["share_alike"] is False


def test_an_unreadable_licence_is_said_out_loud():
    said = []
    plan_fetch("hdx", country="swe", dataset="iati-swe",
               get_json=_hdx_api(), say=said.append)
    text = " ".join(said)
    assert "LICENCE NOT MACHINE-READABLE" in text
    assert "before republishing" in text


def test_a_format_filter_narrows_and_says_what_exists():
    plan = plan_fetch("hdx", country="swe", dataset="iati-swe",
                      format="CSV", get_json=_hdx_api(), say=_quiet)
    assert len(plan["entries"]) == 2
    with pytest.raises(FetchError, match="It offers: CSV"):
        plan_fetch("hdx", country="swe", dataset="iati-swe",
                   format="SHP", get_json=_hdx_api(), say=_quiet)


def test_one_dataset_may_hold_several_files():
    """Unlike GHSL, where one set of choices names one file."""
    plan = plan_fetch("hdx", country="swe", dataset="iati-swe",
                      get_json=_hdx_api(), say=_quiet)
    assert len(plan["entries"]) == 2


def test_a_number_chooses_the_dataset_too():
    plan = plan_fetch("hdx", country="swe", dataset="2",
                      get_json=_hdx_api(), say=_quiet)
    assert plan["dataset"] == "iati-swe"


# ---------------------------------------------------------------------
# BACKLOG 262 - Geofabrik. Structure confirmed against the real
# index-v1.json, all 700 pages of it, supplied by John.
# ---------------------------------------------------------------------
def _gf_api():
    with open(CAPTURED / "geofabrik_index.json", encoding="utf-8") as f:
        rec = json.load(f)
    return lambda url, timeout=60: rec


def test_an_empty_region_lists_the_continents():
    """John: 'a simple selection like a continent/country/region list
    where download from any level is acceptable'."""
    with pytest.raises(FetchError) as e:
        plan_fetch("geofabrik", region="", get_json=_gf_api(),
                   say=_quiet)
    msg = str(e.value)
    assert "africa" in msg and "europe" in msg
    assert "Every level is downloadable" in msg


@pytest.mark.parametrize("region", ["africa", "burundi", "act"])
def test_any_level_can_be_fetched(region):
    """A continent, a country, and a sub-region."""
    plan = plan_fetch("geofabrik", region=region, get_json=_gf_api(),
                      say=_quiet)
    assert plan["entries"][0]["url"].endswith(".osm.pbf")


def test_a_near_miss_suggests_the_real_one():
    with pytest.raises(FetchError, match="sweden"):
        plan_fetch("geofabrik", region="swed", get_json=_gf_api(),
                   say=_quiet)


def test_the_publishers_md5_sidecar_is_recorded():
    """Geofabrik states a checksum beside every file, so a download
    can be checked against what the PUBLISHER says it is."""
    e = plan_fetch("geofabrik", region="burundi", get_json=_gf_api(),
                   say=_quiet)["entries"][0]
    assert e["md5_url"] == e["url"] + ".md5"


def test_ODbL_share_alike_is_recorded_AND_said_out_loud():
    """The first source here with a share-alike obligation, and
    EquiPop exists to produce published derived surfaces."""
    said = []
    plan = plan_fetch("geofabrik", region="burundi",
                      get_json=_gf_api(), say=said.append)
    e = plan["entries"][0]
    assert e["share_alike"] is True
    assert e["may_redistribute"] is True
    assert "ODbL" in e["licence"]
    text = " ".join(said)
    assert "SHARE-ALIKE" in text and "before publishing" in text


def test_the_shapefile_route_exists_because_there_is_no_gpkg():
    """A search snippet claimed .gpkg.zip; the real index offers pbf
    and shp only. shp is the route that needs no new dependency."""
    plan = plan_fetch("geofabrik", region="sweden", format="shp",
                      get_json=_gf_api(), say=_quiet)
    assert plan["entries"][0]["url"].endswith(".shp.zip")
    with pytest.raises(FetchError, match="It offers: pbf, shp"):
        plan_fetch("geofabrik", region="sweden", format="gpkg",
                   get_json=_gf_api(), say=_quiet)


def test_taking_a_whole_continent_is_allowed_but_mentioned():
    said = []
    plan_fetch("geofabrik", region="africa", get_json=_gf_api(),
               say=said.append)
    assert "sub-regions" in " ".join(said)


def test_NAMIBIA_survives():
    """iso3166-1:alpha2 for Namibia is "NA", which pandas turns into
    NaN by default. A country vanishing from a country list without a
    word is this project's signature fault, so it is pinned."""
    e = plan_fetch("geofabrik", region="namibia", get_json=_gf_api(),
                   say=_quiet)["entries"][0]
    assert e["iso3166_1"] == ["NA"], e["iso3166_1"]
    assert e["region_name"] == "Namibia"
