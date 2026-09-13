# -*- coding: utf-8 -*-
"""test_fetch_reliability.py - the download defects confirmed in the
external review of 1.46.4 (BACKLOG 291), each reproduced against the
shipped source before it was fixed.

The review read the code and ran offline probes; every finding below
was then CHECKED IN THIS TREE rather than taken on trust, and one
turned out worse than reported - see the md5 test.

Each test was verified by restoring the old behaviour and watching it
fail:

  * search() asking rows=100 with no start        -> 1, 2 fail
  * dropping the dedupe on stable id              -> 3 fails
  * md5_url written but never fetched             -> 4, 5 fail
  * the manifest written only after the last file -> 6 fails
  * untracked files compared by basename          -> 7 fails
  * no content-type/format check on a download    -> 8 fails
  * endswith() against the whole URL              -> 9 fails
"""
import json
import os

import pytest

from equipop.doors import fetching
from equipop.doors.fetching import HDX, FetchError


# ------------------------------------------------- 1, 2, 3: HDX pages
def _ckan(total, page=100):
    """A CKAN stand-in that honours rows/start the way the real one
    does, and records what it was asked."""
    calls = []

    def get_json(url):
        calls.append(url)
        rows = int(url.split("rows=")[1].split("&")[0])
        start = int(url.split("start=")[1].split("&")[0]) \
            if "start=" in url else 0
        end = min(start + rows, total)
        return {"success": True, "result": {
            "count": total,
            "results": [{"id": f"id{i}", "name": f"ds-{i}",
                         "title": f"Dataset {i}", "resources": []}
                        for i in range(start, end)]}}
    return get_json, calls


def test_1_a_country_with_more_than_one_page_is_fully_listed():
    """Turkey had 175 datasets in the review's live check; the code
    asked for 100 and stopped, so results 101-175 could not be
    selected at all. Sweden has 98 and fitted, which is exactly why a
    Sweden-only fixture never showed the limitation."""
    get_json, _ = _ckan(175)
    got = HDX().search("tur", get_json=get_json)
    assert len(got) == 175
    assert got[-1]["name"] == "ds-174"


def test_2_a_single_page_country_still_costs_one_request():
    """Paging must not make the common case slower."""
    get_json, calls = _ckan(98)
    got = HDX().search("swe", get_json=get_json)
    assert len(got) == 98
    assert len(calls) == 1, calls


def test_3_a_dataset_repeated_across_pages_is_not_offered_twice():
    """CKAN can repeat a record when the catalogue changes mid-query.
    A name that resolves to two records is a selection that cannot be
    trusted."""
    def get_json(url):
        start = int(url.split("start=")[1].split("&")[0])
        # every page returns the SAME two datasets
        return {"success": True, "result": {
            "count": 4,
            "results": [{"id": "a", "name": "ds-a"},
                        {"id": "b", "name": "ds-b"}]}}
    got = HDX().search("xxx", get_json=get_json)
    assert [p["id"] for p in got] == ["a", "b"]


def test_3b_a_miscounting_provider_cannot_page_forever():
    """A `count` larger than the catalogue must stop, and say so."""
    def get_json(url):
        return {"success": True, "result": {
            "count": 10 ** 9,
            "results": [{"id": "x", "name": "ds-x"}]}}
    said = []
    got = HDX().search("xxx", get_json=get_json, say=said.append)
    assert len(got) == 1
    assert any("stopped after" in m for m in said), said


# ------------------------------------------- 4, 5: the Geofabrik md5
def test_4_the_publisher_checksum_is_actually_fetched():
    """THE REVIEW UNDERSTATED THIS ONE. `md5_url` appeared exactly
    twice in 1.46.4: at the line that wrote it, and inside a comment
    claiming BACKLOG 278 had fixed it. Nothing ever retrieved the
    sidecar. The fix covered HDX, which supplies `publisher_md5`
    inline, and left Geofabrik entirely unverified while the comment
    read as though both were done."""
    src = open(os.path.join(os.path.dirname(fetching.__file__),
                            "fetching.py"), encoding="utf-8").read()
    # the key must be READ somewhere, not only written and described
    reads = [ln for ln in src.splitlines()
             if "md5_url" in ln and "#" not in ln.split("md5_url")[0]]
    assert any("get(" in ln or "[" in ln for ln in reads
               if "\"md5_url\":" not in ln and "'md5_url':" not in ln), (
        "md5_url is still only written and commented about, never read")


def test_5_a_sidecar_that_disagrees_stops_the_download(tmp_path):
    """The whole point of fetching the sidecar."""
    entry = {"name": "a.osm.pbf", "url": "https://example/a.osm.pbf",
             "md5_url": "https://example/a.osm.pbf.md5"}

    def get_text(url):
        # the publisher says the file hashes to something else
        return "0" * 32 + "  a.osm.pbf\n"

    def get_file(url, dest):
        open(dest, "wb").write(b"not that file")
        import hashlib
        b = b"not that file"
        return (len(b), hashlib.sha256(b).hexdigest(),
                hashlib.md5(b).hexdigest())

    plan = {"provider": "geofabrik", "entries": [entry],
            "licence": "ODbL", "may_redistribute": True}
    with pytest.raises(FetchError, match="(?i)publisher|md5|match"):
        fetching.run_fetch(plan, str(tmp_path), get_file=get_file,
                           get_text=get_text, say=lambda *a: None)
    assert not os.path.exists(tmp_path / "a.osm.pbf"), \
        "a file that failed its publisher checksum was left on disk"


# ------------------------------- 6: a failure must not erase success
def test_6_file_one_keeps_its_provenance_when_file_two_fails(tmp_path):
    """The review's first finding. The manifest was written only after
    the LAST entry, so an interruption at file 2 of 3 left file 1 on
    disk with nothing recording where it came from - and a retry then
    met it as an unknown file with a clashing name and refused."""
    import hashlib

    def get_file(url, dest):
        if url.endswith("b.tif"):
            raise FetchError("the network went away")
        b = b"first file"
        open(dest, "wb").write(b)
        return (len(b), hashlib.sha256(b).hexdigest(),
                hashlib.md5(b).hexdigest())

    plan = {"provider": "worldpop", "licence": "CC BY 4.0",
            "may_redistribute": True,
            "entries": [{"name": "a.tif", "url": "https://x/a.tif"},
                        {"name": "b.tif", "url": "https://x/b.tif"}]}
    with pytest.raises(FetchError):
        fetching.run_fetch(plan, str(tmp_path), get_file=get_file,
                           say=lambda *a: None)

    man = fetching.read_manifest(str(tmp_path))
    assert man, "no manifest at all after a mid-job failure"
    names = {f["name"] for f in man["files"]}
    assert "a.tif" in names, (
        "the file that succeeded has no provenance - a retry will "
        "meet it as an unknown file")
    assert man["fetches"][-1]["status"] == "incomplete"
    assert man["fetches"][-1]["planned"] == 2


def test_6b_a_retry_recognises_what_the_failed_job_completed(tmp_path):
    """The consequence that made the missing record expensive."""
    import hashlib
    calls = []

    def get_file(url, dest):
        calls.append(url)
        if url.endswith("b.tif") and len(calls) < 3:
            raise FetchError("the network went away")
        b = b"first file" if url.endswith("a.tif") else b"second file"
        open(dest, "wb").write(b)
        return (len(b), hashlib.sha256(b).hexdigest(),
                hashlib.md5(b).hexdigest())

    plan = {"provider": "worldpop", "licence": "CC BY 4.0",
            "may_redistribute": True,
            "entries": [{"name": "a.tif", "url": "https://x/a.tif"},
                        {"name": "b.tif", "url": "https://x/b.tif"}]}
    with pytest.raises(FetchError):
        fetching.run_fetch(plan, str(tmp_path), get_file=get_file,
                           say=lambda *a: None)
    # the retry: a.tif is on disk AND in the manifest, so it is reused
    man = fetching.run_fetch(plan, str(tmp_path), get_file=get_file,
                             say=lambda *a: None)
    assert man["fetches"][-1]["status"] == "complete"
    assert {f["name"] for f in man["files"]} == {"a.tif", "b.tif"}


# ------------------------------ 7: verify sees nested untracked files
def test_7_a_nested_file_does_not_hide_behind_a_tracked_name(tmp_path):
    """Untracked files were compared by BASENAME, so `nested/a.tif`
    disappeared behind a tracked top-level `a.tif` - the one thing a
    verify exists to notice was the thing it could miss."""
    import hashlib

    def get_file(url, dest):
        b = b"real"
        open(dest, "wb").write(b)
        return (len(b), hashlib.sha256(b).hexdigest(),
                hashlib.md5(b).hexdigest())

    plan = {"provider": "worldpop", "licence": "CC BY 4.0",
            "may_redistribute": True,
            "entries": [{"name": "a.tif", "url": "https://x/a.tif"}]}
    fetching.run_fetch(plan, str(tmp_path), get_file=get_file,
                       say=lambda *a: None)
    nest = tmp_path / "nested"
    nest.mkdir()
    (nest / "a.tif").write_bytes(b"something nobody fetched")

    said = []
    fetching.verify_folder(str(tmp_path), say=said.append)
    report = " ".join(said)
    assert "1 untracked" in report, report


# ------------------- 8: a web page is not a completed download
@pytest.mark.parametrize("page", [
    b"<!DOCTYPE html>\n<html><body>Please sign in</body></html>",
    b"<html><head><title>429 Too Many Requests</title></head>",
    b"  \n  <?xml version='1.0'?><Error>NoSuchKey</Error>",
])
def test_8_html_with_status_200_never_becomes_a_verified_asset(
        tmp_path, page):
    """The status code says the REQUEST succeeded. It says nothing
    about what came back, and a sign-in page saved as a raster used to
    be checksummed, manifested and reported as done."""
    import hashlib

    def get_file(url, dest):
        open(dest, "wb").write(page)
        return (len(page), hashlib.sha256(page).hexdigest(),
                hashlib.md5(page).hexdigest())

    plan = {"provider": "worldpop", "licence": "CC BY 4.0",
            "may_redistribute": True,
            "entries": [{"name": "pop.tif", "url": "https://x/pop.tif"}]}
    with pytest.raises(FetchError, match="(?i)web page|sign-in|not what"):
        fetching.run_fetch(plan, str(tmp_path), get_file=get_file,
                           say=lambda *a: None)
    assert not os.path.exists(tmp_path / "pop.tif")
    man = fetching.read_manifest(str(tmp_path)) or {}
    assert "pop.tif" not in {f["name"] for f in man.get("files", [])}


def test_8b_an_unknown_format_is_left_alone(tmp_path):
    """The first version of this check carried a table of magic bytes
    and refused anything absent from it. .csv, .json, .pbf and .shp
    were all absent, and so is whatever the next provider serves.
    Being narrow is the point, not a shortcoming."""
    import hashlib
    body = b"iso3,year,pop\nSWE,2020,10400000\n"

    def get_file(url, dest):
        open(dest, "wb").write(body)
        return (len(body), hashlib.sha256(body).hexdigest(),
                hashlib.md5(body).hexdigest())

    plan = {"provider": "hdx", "licence": "CC BY 4.0",
            "may_redistribute": True,
            "entries": [{"name": "t.csv", "url": "https://x/t.csv"}]}
    man = fetching.run_fetch(plan, str(tmp_path), get_file=get_file,
                             say=lambda *a: None)
    assert "t.csv" in {f["name"] for f in man["files"]}


# ------------------------------ 9: a query string is not an extension
def test_9_a_download_parameter_does_not_hide_a_raster():
    """`endswith()` ran against the WHOLE URL, so a perfectly good
    `...tif?download=1` was silently discarded - a missing file with
    no message, which is the hardest kind to notice."""
    from equipop.doors.fetching import _url_suffix
    assert _url_suffix("https://hub.worldpop.org/a/pop.tif") == ".tif"
    assert _url_suffix(
        "https://hub.worldpop.org/a/pop.tif?download=1") == ".tif"
    assert _url_suffix("https://x/y/data.zip?v=2&k=3") == ".zip"
    assert _url_suffix("https://x/y/pop.TIF") == ".tif"
    assert _url_suffix("https://x/y/catalogue") == ""


def test_9b_worldpop_keeps_a_file_served_with_a_query_string():
    """The consequence, at the level the user meets it."""
    from equipop.doors.fetching import PROVIDERS
    wp = PROVIDERS["worldpop"]
    rec = {"id": 1, "iso3": "SWE", "country": "Sweden", "popyear": 2020,
           "files": ["https://hub.worldpop.org/a/swe_pop.tif?download=1",
                     "https://hub.worldpop.org/a/swe_meta.html"]}
    names = [e["name"] for e in wp.entries(rec)]
    assert names == ["swe_pop.tif"], names


def test_9c_a_query_string_never_becomes_part_of_a_filename():
    """The SECOND defect the same query string caused, found while
    fixing the first. basename() of the whole URL produced a file
    called `swe_pop.tif?download=1` - refused outright by Windows,
    and on Linux a file no importer recognises by extension."""
    from equipop.doors.fetching import url_filename
    assert url_filename("https://x/a/swe_pop.tif?download=1") == \
        "swe_pop.tif"
    assert url_filename("https://x/a/b.zip#part2") == "b.zip"
    assert url_filename("https://x/a/name%20with%20space.tif") == \
        "name with space.tif"
    assert url_filename("https://x/a/") == "download"
