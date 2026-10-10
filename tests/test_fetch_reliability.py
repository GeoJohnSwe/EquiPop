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


# --------------------------------------------------- review H1, 1.54.1
def test_only_http_and_https_are_downloaded():
    """BROKEN WITH: removing the _check_scheme call from any of the
    three download paths.

    REVIEW H1, and the reason it is worth doing rather than noting.
    `urlopen` accepts `file://`, and a bare path with no scheme it
    reads as a LOCAL FILE - so a mistyped or pasted string could make
    `fetch()` copy something off this machine and print
    `[fetch] saved ...` as if it had downloaded it. No exploit was
    demonstrated and none is needed: there is no case where a data
    provider needs anything but http(s), so the refusal costs nothing
    and removes the question.

    ONE READER, called by all three paths, because three copies of a
    scheme check is how one of them comes to be missing.
    """
    import pytest as _pytest

    # NOT `from equipop import fetch` - the lazy export map makes
    # that name the FUNCTION, so the module has to be asked for by
    # path. (Found by this test failing with "'function' object has
    # no attribute '_check_scheme'".)
    import importlib

    fetch_mod = importlib.import_module("equipop.fetch")
    fetching_mod = importlib.import_module("equipop.doors.fetching")

    for bad in ("file:///etc/passwd", "ftp://example.org/x.tif",
                "/etc/passwd", "C:\\Windows\\win.ini",
                "data:text/plain,hello", "javascript:alert(1)"):
        with _pytest.raises(ValueError, match="http"):
            fetch_mod._check_scheme(bad)
    for good in ("https://example.org/x.tif", "http://example.org/x.tif",
                 "HTTPS://EXAMPLE.ORG/X.TIF"):
        fetch_mod._check_scheme(good)      # must not raise

    # and every download path has to call it. Checked on the source
    # as a property - each function that opens a URL must reach the
    # one reader - because a path that skips it cannot be caught by
    # calling the reader directly.
    import ast
    import inspect

    for mod in (fetch_mod, fetching_mod):
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            body = ast.dump(node)
            opens = "urlopen" in body
            if not opens:
                continue
            assert "_check_scheme" in body, (
                f"{mod.__name__}.{node.name} opens a URL without "
                f"checking its scheme")


def test_a_forbidden_scheme_is_refused_BEFORE_the_cache_is_consulted(
        tmp_path):
    """BROKEN WITH: moving _check_scheme back inside fetch()'s
    download branch, which is where 1.54.1 put it.

    REVIEW FINDING 4, 1.54.2. `fetch()` builds its destination from
    the URL's BASENAME and returns the cached file when one exists -
    and the scheme check sat below that, in the download branch only.
    So with `payload.bin` already in the work directory,
    `fetch("file:///etc/payload.bin", wd)` printed `[fetch] cached`
    and returned the path, reporting a forbidden request as
    satisfied. Nothing forbidden is read in that case, so it is not
    the local-file-copy risk itself; it is worse as a CONTRACT,
    because the caller is handed an unrelated file and believes it
    holds that URL's content.

    AND THE PREVIOUS TEST COULD NOT CATCH IT. It asserted, over the
    AST, that every function containing `urlopen` also contains
    `_check_scheme` - which proves PRESENCE and says nothing about
    POSITION. Ordering needs a behavioural test, so this one actually
    primes the cache and calls fetch.
    """
    import importlib

    import pytest as _pytest

    fetch_mod = importlib.import_module("equipop.fetch")

    wd = tmp_path / "work"
    wd.mkdir()
    (wd / "payload.bin").write_bytes(b"an unrelated cached file")

    for bad in ("file:///etc/payload.bin",
                "ftp://example.org/payload.bin",
                "/etc/payload.bin"):
        with _pytest.raises(ValueError, match="http"):
            fetch_mod.fetch(bad, str(wd))

    # a cache HIT on a permitted scheme still works - the check is
    # about the scheme, not about refusing to use the cache
    got = fetch_mod.fetch("https://example.org/payload.bin", str(wd))
    assert str(got).endswith("payload.bin")
    assert (wd / "payload.bin").read_bytes() == b"an unrelated cached file"

    # and the refusal happens before the work directory is created,
    # so a forbidden call leaves nothing behind
    fresh = tmp_path / "never"
    with _pytest.raises(ValueError, match="http"):
        fetch_mod.fetch("file:///etc/x.bin", str(fresh))
    assert not fresh.exists(), (
        "a refused fetch created its work directory anyway")


def test_the_md5_uses_are_declared_non_security():
    """BROKEN WITH: dropping usedforsecurity=False.

    REVIEW H1's second half, done for a reason stronger than quieting
    a scanner: on a FIPS-enabled host `hashlib.md5()` RAISES, so
    `cells.fingerprint()`, the tile manifests and the unit-size cache
    key would all crash on an institutional machine configured that
    way. The flag makes the intent explicit and makes the call work
    there.

    AND IT CHANGES NO STORED VALUE, which is the part that had to be
    checked before touching it: bigrun writes tile checksums to disk
    and verifies them on every read, so a different digest would make
    every existing tiled run on John's machines fail verification.
    Measured: identical for empty, short and 2,560-byte payloads and
    for incremental updates.
    """
    import hashlib
    import inspect

    for payload in (b"", b"hello", bytes(range(256)) * 10):
        assert hashlib.md5(payload).hexdigest() == \
            hashlib.md5(payload, usedforsecurity=False).hexdigest(), (
            "the digest changed - every stored tile checksum and every "
            "cached fingerprint would now fail to verify")

    from equipop import bigrun, cells, meta, unitsize
    from equipop.doors import fetching

    for mod in (bigrun, cells, meta, unitsize, fetching):
        src = inspect.getsource(mod)
        bare = src.count("hashlib.md5()")
        assert bare == 0, (
            f"{mod.__name__} calls hashlib.md5() without "
            f"usedforsecurity=False at {bare} site(s) - it will raise "
            f"on a FIPS-enabled host")
