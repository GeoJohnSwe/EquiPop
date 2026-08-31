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
