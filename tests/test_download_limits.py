# -*- coding: utf-8 -*-
"""test_download_limits.py - the size limit counts what ARRIVES, Cancel
stops a file part-way, and a redirect is checked like the address it
came from.

v1.59.2, external review of 1.59.1:
  * max_mb added up the sizes the catalogue knew, so files of unknown
    size passed any limit - all 40 of Burundi's against 0.0001 MB;
  * Cancel was heard only between files, so Sweden's 1.9 GB .pbf ran
    to the end once started;
  * urllib followed a redirect wherever it pointed.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import io
import json
import os
import sys
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import fakeweb                                       # noqa: E402
from equipop.doors import catalogue as cat          # noqa: E402
from equipop.doors import fetchrows as fr           # noqa: E402
from equipop.doors.fetching import FetchError, MANIFEST  # noqa: E402

SWEDEN_ZIP = "https://download.geofabrik.de/europe/sweden-latest-free.shp.zip"


def mute(*_a):
    return None


@pytest.fixture
def web():
    return fakeweb.captured(bodies=True)


@pytest.fixture
def net(web):
    return cat.Net(opener=web, pause=0, waits=(0,))


def _burundi(net, n=None, sizes=True):
    rows = cat.browse_worldpop("age_sex", "Burundi", "2020", net=net,
                               say=mute)
    rows = rows[:n] if n else rows
    if not sizes:
        for r in rows:
            r["size_mb"], r["size_is"] = None, "unknown"
    return rows


def _recorded(folder):
    p = os.path.join(folder, MANIFEST)
    if not os.path.exists(p):
        return set()
    with open(p, encoding="utf-8") as f:
        return {x["name"] for x in json.load(f)["files"]}


def _on_disk(folder):
    return sorted(os.listdir(folder)) if os.path.isdir(folder) else []


# ------------------------------------------------------------ the limit
def test_files_of_unknown_size_stop_at_the_limit(net, web, tmp_path):
    """The reviewer's case: no sizes in the catalogue, so the check
    before downloading has nothing to add up. The bytes are counted as
    they come, and the fetch stops at the file that would pass the
    limit - that file not kept, the ones before it kept and recorded.

    BROKEN WITH: Net.block's limit test removed."""
    rows = _burundi(net, sizes=False)
    each = len(web.files[rows[0]["url"]]["body"])
    folder = str(tmp_path / "f")
    said = []
    with pytest.raises(cat.OverLimit, match="limit of") as e:
        fr.fetch_rows(rows, folder, net=net, say=said.append,
                      max_mb=2.5 * each / 1e6)
    assert rows[2]["file"] in str(e.value)
    assert _recorded(folder) == {rows[0]["file"], rows[1]["file"]}
    assert not any(n.endswith(".part") for n in _on_disk(folder))
    assert rows[2]["file"] not in _on_disk(folder)
    assert any("no size in the catalogue" in s for s in said)


def test_a_file_with_no_declared_length_stops_part_way(net, web,
                                                       tmp_path):
    """No Content-Length, no size in the row: the limit is met inside
    the file, block by block, and what had arrived of it is removed.

    BROKEN WITH: the per-block call to net.block removed from
    download (the declared-size call kept)."""
    rows = _burundi(net, 1, sizes=False)
    url = rows[0]["url"]
    web.files[url]["body"] = fakeweb.tif_bytes(url, n=3 << 20)
    web.files[url]["size"] = len(web.files[url]["body"])
    web.make_trouble(url, "nolength")
    folder = str(tmp_path / "f")
    with pytest.raises(cat.OverLimit, match="had reached"):
        fr.fetch_rows(rows, folder, net=net, say=mute, max_mb=1.5)
    assert [n for n in _on_disk(folder) if n.endswith(".tif")
            or n.endswith(".part")] == []


def test_the_size_the_server_gives_now_is_checked_before_reading(
        net, web, tmp_path):
    """A 'latest' file can grow after the catalogue lists it. The row
    says a few kB; the server now declares 3 MiB, which passes the
    limit - refused before a byte of it is read.

    BROKEN WITH: the declared-size call to net.block removed."""
    rows = _burundi(net, 1)
    url = rows[0]["url"]
    web.files[url]["body"] = fakeweb.tif_bytes(url, n=3 << 20)
    web.files[url]["size"] = len(web.files[url]["body"])
    reads = []
    real = fakeweb.Response.read

    def counted(self, n=-1):
        data = real(self, n)
        reads.append(len(data))
        return data
    fakeweb.Response.read = counted
    try:
        with pytest.raises(cat.OverLimit, match="the server says"):
            fr.fetch_rows(rows, str(tmp_path / "f"), net=net, say=mute,
                          max_mb=1)
    finally:
        fakeweb.Response.read = real
    assert sum(reads) == 0


def test_bytes_tried_again_are_not_counted_twice(net, web, tmp_path):
    """A file cut part-way is downloaded again from its start. Only
    the copy that is kept counts: a limit that fits the files fits
    them however often a connection was cut.

    BROKEN WITH: net.done called for every block as it streams, so
    every try's bytes count."""
    rows = _burundi(net, 3, sizes=False)
    each = len(web.files[rows[0]["url"]]["body"])
    for r in rows:
        web.make_trouble(r["url"], "cut", "cut")
    folder = str(tmp_path / "f")
    fr.fetch_rows(rows, folder, net=net, say=mute,
                  max_mb=3.2 * each / 1e6)
    assert _recorded(folder) == {r["file"] for r in rows}


def test_a_shapefile_layer_is_counted_by_its_packed_bytes(net, web,
                                                          tmp_path):
    """Out of a remote zip, what crosses the network is the PACKED
    member, and the zip's table of contents says how large it is: a
    limit below it stops the fetch before any of the member - its
    header included - is asked for.

    BROKEN WITH: the declared-size call to net.block removed from
    extract_member."""
    import zipfile
    rows = cat.browse_geofabrik("Sweden", "buildings", net=net, say=mute)
    for r in rows:              # past the check made before downloading
        r["size_mb"], r["size_is"] = None, "unknown"
    infos = zipfile.ZipFile(io.BytesIO(web.files[SWEDEN_ZIP]["body"]))
    starts = {i.header_offset for i in infos.infolist()
              if "buildings" in i.filename}
    with pytest.raises(cat.OverLimit):
        fr.fetch_rows(rows, str(tmp_path / "f"), net=net, say=mute,
                      max_mb=1e-5)
    asked = {int(r.split("=")[1].split("-")[0]) for m, u, r in web.log
             if u == SWEDEN_ZIP and r and m == "GET"}
    assert starts and not (asked & starts)


def test_no_limit_means_no_limit(net, web, tmp_path):
    """0 in the box (None here) fetches everything, sizes or not.

    BROKEN WITH: fetch_rows setting a limit of 0 bytes for max_mb=None."""
    rows = _burundi(net, 4, sizes=False)
    folder = str(tmp_path / "f")
    fr.fetch_rows(rows, folder, net=net, say=mute, max_mb=None)
    assert _recorded(folder) == {r["file"] for r in rows}


# ---------------------------------------------------------------- Cancel
def test_cancel_stops_a_large_file_part_way(net, web, tmp_path):
    """Cancel pressed while the second file is streaming: it stops
    there, mid-file - not when the file has finished - its part is
    removed, and the first file is recorded so a new run continues.

    BROKEN WITH: the cancel test removed from Net.block (the door's
    between-files check is all that is left)."""
    rows = _burundi(net, 2)
    big = rows[1]["url"]
    web.files[big]["body"] = fakeweb.tif_bytes(big, n=4 << 20)
    web.files[big]["size"] = len(web.files[big]["body"])
    folder = str(tmp_path / "f")
    part = os.path.join(folder, rows[1]["file"] + ".part")
    seen = {"bytes": 0}

    def pressed():
        # pressed once a megabyte of the big file is on disk
        if os.path.exists(part):
            seen["bytes"] = os.path.getsize(part)
            return seen["bytes"] >= 1 << 20
        return False
    with pytest.raises(cat.Cancelled, match="Cancelled while fetching") \
            as e:
        fr.fetch_rows(rows, folder, net=net, say=mute, cancelled=pressed)
    assert rows[1]["file"] in str(e.value)
    assert 0 < seen["bytes"] < (4 << 20)
    assert _recorded(folder) == {rows[0]["file"]}
    assert _on_disk(folder) == sorted([MANIFEST, rows[0]["file"]])
    fr.fetch_rows(rows, folder, net=net, say=mute)
    assert _recorded(folder) == {r["file"] for r in rows}


def test_cancel_is_never_tried_again(net, web, tmp_path):
    """A Cancel is not a dropped connection.

    BROKEN WITH: transient() answering True for Cancelled."""
    rows = _burundi(net, 1)
    with pytest.raises(cat.Cancelled):
        fr.fetch_rows(rows, str(tmp_path / "f"), net=net, say=mute,
                      cancelled=lambda: True)
    assert net.retries == 0
    assert not cat.transient(cat.Cancelled("x"))
    assert not cat.transient(cat.OverLimit("x"))


def test_cancel_stops_a_shapefile_layer_too(net, tmp_path):
    """The same check inside the remote-zip reader.

    BROKEN WITH: the cancel test removed from Net.block."""
    rows = cat.browse_geofabrik("Sweden", "roads", net=net, say=mute)
    with pytest.raises(cat.Cancelled):
        fr.fetch_rows(rows, str(tmp_path / "f"), net=net, say=mute,
                      cancelled=lambda: True)
    assert not [n for n in _on_disk(str(tmp_path / "f"))
                if n.endswith((".shp", ".dbf", ".part"))]


# ------------------------------------------------------------ redirects
class _Https(urllib.request.HTTPSHandler):
    """Stands in for the https transport: each address answers from a
    table - a redirect, or a body."""

    def __init__(self, answers):
        super().__init__()
        self.answers, self.asked = answers, []

    def https_open(self, req):
        self.asked.append(req.full_url)
        to = self.answers[req.full_url]
        if to.startswith("http"):
            hdrs = {"Location": to, "Content-Length": "0"}
            resp = urllib.response.addinfourl(io.BytesIO(b""), _Hdr(hdrs),
                                              req.full_url, 302)
            resp.msg = "Found"
            return resp
        body = to.encode()
        resp = urllib.response.addinfourl(
            io.BytesIO(body), _Hdr({"Content-Length": str(len(body))}),
            req.full_url, 200)
        resp.msg = "OK"
        return resp

    def http_open(self, req):                           # pragma: no cover
        self.asked.append(req.full_url)
        raise AssertionError("an http address was opened")


def _Hdr(d):
    """Headers as urllib reads them - case-insensitive."""
    import email.message
    m = email.message.Message()
    for k, v in d.items():
        m[k] = v
    return m


import urllib.response                               # noqa: E402

START = "https://data.worldpop.org/GIS/x.tif"


def _net(answers):
    https = _Https(answers)
    net = cat.Net(opener=lambda req: cat.safe_opener(https).open(req),
                  pause=0, waits=(0,))
    return net, https


def test_a_redirect_within_the_provider_is_followed():
    """Same provider, still https: followed, as before.

    BROKEN WITH: SafeRedirect refusing every redirect."""
    other = "https://hub.worldpop.org/files/x.tif"
    net, https = _net({START: other, other: "BYTES"})
    with net.open(START) as r:
        assert r.read() == b"BYTES"
    assert https.asked == [START, other]


@pytest.mark.parametrize("to, words", [
    ("https://elsewhere.example.com/x.tif", "not at worldpop.org"),
    ("http://data.worldpop.org/GIS/x.tif", "not https"),
    ("https://127.0.0.1/x.tif", "not at worldpop.org"),
    ("https://worldpop.org.example.com/x.tif", "not at worldpop.org")])
def test_a_redirect_elsewhere_is_refused_and_named(to, words):
    """Another site, a private address, a look-alike domain, or a step
    down to plain http: refused, the address named, never opened.

    BROKEN WITH: SafeRedirect.redirect_request passing everything to
    urllib's own."""
    net, https = _net({START: to, to: "BYTES"})
    with pytest.raises(cat.Redirected, match=words) as e:
        net.open(START)
    assert to in str(e.value)
    assert https.asked == [START]
    assert not cat.transient(e.value)


def test_a_redirect_loop_stops_and_is_not_tried_again():
    """Two addresses at the provider sending EquiPop to each other:
    urllib gives up after a few rounds, and that is an answer, not a
    stumble worth another try.

    BROKEN WITH: transient() answering True for any HTTPError."""
    other = "https://hub.worldpop.org/files/x.tif"
    net, https = _net({START: other, other: START})
    with pytest.raises(cat.NetError) as e:
        net.get_text(START)
    assert not cat.transient(e.value)
    assert net.retries == 0 and len(https.asked) <= 12


def test_the_real_opener_checks_redirects():
    """Net's own opener (the one used outside the tests) is the
    checking one.

    BROKEN WITH: Net._urlopen put back on urllib.request.urlopen."""
    src = (ROOT / "equipop" / "doors" / "catalogue.py").read_text(
        encoding="utf-8")
    body = src.split("def _urlopen(self, req):", 1)[1].split("\n\n", 1)[0]
    assert "safe_opener().open(req" in body
    assert "urlopen(" not in body.replace("_urlopen", "")
