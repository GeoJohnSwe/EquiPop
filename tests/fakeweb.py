# -*- coding: utf-8 -*-
"""fakeweb.py - the web as John's probes found it, served from disk.

The catalogue and fetch code reach the network through ONE function,
`opener(request) -> response` (equipop.doors.catalogue.Net). This is
that function, answering from the captures of 14 October 2026 trimmed
into tests/fixtures/catalogue, plus files made here when a test needs
real bytes: a shapefile zip with Geofabrik's member names, a GeoTIFF-
shaped body, an OSM extract.

It speaks just enough HTTP to be honest about the parts that matter:
HEAD, Range, If-Range (a replaced file answers 200, not 206),
Last-Modified, ETag, and 404 for anything it does not hold.
"""
from __future__ import annotations

import hashlib
import http.client
import io
import json
import re
import urllib.error
import zipfile
from email.utils import format_datetime
from datetime import datetime, timezone
from pathlib import Path

FIX = Path(__file__).resolve().parent / "fixtures" / "catalogue"
WP = "https://www.worldpop.org/rest/data"
GF = "https://download.geofabrik.de"


def fixture(name):
    with open(FIX / name, encoding="utf-8") as f:
        return json.load(f)


class Response:
    def __init__(self, status, headers, body, cut=False):
        self.status, self.headers = status, dict(headers)
        self._buf = io.BytesIO(body or b"")
        self._cut = cut                 # the connection dies at the end

    def read(self, n=-1):
        data = (self._buf.read() if n is None or n < 0
                else self._buf.read(n))
        if not data and self._cut:
            # what http.client raises when the server closes the
            # connection before the declared length has arrived
            raise http.client.IncompleteRead(b"", 1)
        return data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeWeb:
    def __init__(self):
        self.json = {}
        self.files = {}            # url -> dict(body, size, lm, etag)
        self.log = []              # (method, url, range)
        self.trouble = {}          # (method, url) -> [what goes wrong]

    # ---------------------------------------------------------- setup
    def add_json(self, url, obj):
        self.json[url] = obj

    def add_file(self, url, body=None, size=None, when=None, etag=None):
        """A file. `body` bytes, or just a `size` for HEAD-only use."""
        when = when or datetime(2026, 10, 14, 21, 30, tzinfo=timezone.utc)
        n = len(body) if body is not None else int(size)
        tag = etag or '"' + hashlib.md5(
            (url + str(n) + str(when)).encode()).hexdigest()[:16] + '"'
        self.files[url] = {"body": body, "size": n,
                           "lm": format_datetime(when, usegmt=True),
                           "etag": tag}

    def replace(self, url, body, when):
        """The publisher writes a new file under the same name."""
        self.add_file(url, body=body, when=when)

    def make_trouble(self, url, *actions, method="GET"):
        """The next requests for `url` go wrong, one action each:
        'drop' (closed without an answer - John's 16 October run),
        'reset', 'timeout', 'nolength' (no Content-Length),
        'cut' (half the body, then the connection
        dies), or an HTTP status such as 503."""
        self.trouble.setdefault((method, url), []).extend(actions)

    def count(self, method=None, contains=""):
        return sum(1 for m, u, _ in self.log
                   if (method is None or m == method) and contains in u)

    # ------------------------------------------------------- the opener
    def __call__(self, req):
        url, method = req.full_url, req.get_method()
        rng = req.get_header("Range")
        self.log.append((method, url, rng))
        todo = self.trouble.get((method, url))
        act = todo.pop(0) if todo else None
        if act == "drop":
            raise http.client.RemoteDisconnected(
                "Remote end closed connection without response")
        if act == "reset":
            raise ConnectionResetError(10054, "An existing connection was "
                                       "forcibly closed by the remote host")
        if act == "timeout":
            raise TimeoutError("timed out")
        if isinstance(act, int):
            raise urllib.error.HTTPError(url, act, "Service Unavailable",
                                         None, None)
        if url in self.json:
            body = json.dumps(self.json[url]).encode()
            return Response(200, {"Content-Type": "application/json",
                                  "Content-Length": str(len(body))}, body)
        f = self.files.get(url)
        if f is None:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        hdr = {"Content-Length": str(f["size"]), "Last-Modified": f["lm"],
               "ETag": f["etag"], "Accept-Ranges": "bytes"}
        if method == "HEAD":
            return Response(200, hdr, b"")
        body = f["body"] if f["body"] is not None else b"\0" * f["size"]
        cond = req.get_header("If-range")
        if rng and (cond is None or cond in (f["etag"], f["lm"])):
            m = re.fullmatch(r"bytes=(\d+)-(\d+)", rng)
            lo, hi = int(m[1]), min(int(m[2]), f["size"] - 1)
            part = body[lo:hi + 1]
            if act == "cut":
                return Response(206, {**hdr, "Content-Length": str(len(part)),
                                      "Content-Range":
                                          f"bytes {lo}-{hi}/{f['size']}"},
                                part[:len(part) // 2], cut=True)
            return Response(206, {**hdr, "Content-Length": str(len(part)),
                                  "Content-Range":
                                      f"bytes {lo}-{hi}/{f['size']}"}, part)
        if act == "cut":
            return Response(200, hdr, body[:len(body) // 2], cut=True)
        if act == "nolength":
            # a server that does not say how long the file is
            return Response(200, {k: v for k, v in hdr.items()
                                  if k != "Content-Length"}, body)
        return Response(200, hdr, body)


# ------------------------------------------------------------ WorldPop
def _wp_size(url):
    """A stable, plausible size per file: Sweden's f_15 2020 measured
    2.2 MB at 1 km and 46.6 MB at 100 m (probe round 2)."""
    h = int(hashlib.md5(url.encode()).hexdigest()[:6], 16) / 0xFFFFFF
    return int((40e6 if "100m" in url or "ppp" in url else 2e6)
               * (0.8 + 0.4 * h))


SERIES = (("age_structures", "G2_CN_Age_R25A_1km"),
          ("age_structures", "G2_CN_Age_R25A_100m"),
          ("age_structures", "aswpgp"),
          ("pop", "G2_CN_POP_R25A_1km"), ("pop", "G2_CN_POP_R25A_100m"),
          ("pop", "wpic1km"), ("pop", "wpgp"))


def add_worldpop(web, bodies=False):
    """Every WorldPop answer the probes captured. With `bodies`, each
    file also has bytes, so it can be downloaded."""
    web.add_json(f"{WP}/age_structures",
                 fixture("wp_categories_age_structures.json"))
    web.add_json(f"{WP}/pop", fixture("wp_categories_pop.json"))
    for project, alias in SERIES:
        web.add_json(f"{WP}/{project}/{alias}",
                     fixture(f"wp_index_{project}_{alias}.json"))
        for iso in ("SWE", "KEN", "BDI"):
            full = fixture(f"wp_full_{alias}_{iso}.json")
            web.add_json(f"{WP}/{project}/{alias}?iso3={iso}", full)
            for rec in full["data"]:
                for u in rec.get("files") or []:
                    if bodies:
                        web.add_file(u, body=tif_bytes(u))
                    else:
                        web.add_file(u, size=_wp_size(u))
    return web


def tif_bytes(url, n=3000):
    """Bytes that START like a GeoTIFF and differ per URL."""
    seed = hashlib.sha256(url.encode()).digest()
    return b"II*\x00" + (seed * (n // len(seed) + 1))[:n]


# ----------------------------------------------------------- Geofabrik
LAYERS = ("buildings_a", "roads", "railways", "pois", "pois_a", "places",
          "landuse_a")


def shapefile_zip(region, layers=LAYERS, seed=0, big=None):
    """A zip with Geofabrik's member names and compressible bodies.
    `big` = {layer: n parts} to split a layer into numbered parts."""
    buf = io.BytesIO()
    big = big or {}
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README", f"OpenStreetMap data for {region}\n")
        for i, layer in enumerate(layers):
            for part in range(1, big.get(layer, 1) + 1):
                for ext in ("cpg", "dbf", "prj", "shp", "shx"):
                    word = f"{region}-{layer}-{part}-{ext}-{seed}|".encode()
                    z.writestr(f"gis_osm_{layer}_free_{part}.{ext}",
                               word * (50 + 37 * i + 11 * part))
    return buf.getvalue()


OSM_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6" generator="equipop-test">
 <node id="1" lat="59.30" lon="18.00" version="1"/>
 <node id="2" lat="59.30" lon="18.01" version="1"/>
 <node id="3" lat="59.31" lon="18.01" version="1"/>
 <node id="4" lat="59.31" lon="18.00" version="1"/>
 <node id="5" lat="59.32" lon="18.02" version="1">
  <tag k="amenity" v="school"/><tag k="name" v="Skolan"/></node>
 <node id="6" lat="59.33" lon="18.03" version="1">
  <tag k="place" v="village"/><tag k="name" v="Byn"/></node>
 <node id="7" lat="59.34" lon="18.04" version="1"/>
 <node id="8" lat="59.35" lon="18.05" version="1"/>
 <node id="9" lat="59.36" lon="18.06" version="1"/>
 <way id="10" version="1"><nd ref="1"/><nd ref="2"/><nd ref="3"/>
  <nd ref="4"/><nd ref="1"/><tag k="building" v="yes"/></way>
 <way id="11" version="1"><nd ref="7"/><nd ref="8"/>
  <tag k="highway" v="residential"/><tag k="name" v="Gatan"/></way>
 <way id="12" version="1"><nd ref="8"/><nd ref="9"/>
  <tag k="railway" v="rail"/></way>
</osm>
"""

#: The same place a year on: one more building. Both are kept as REAL
#: .pbf files in fixtures/catalogue (tiny.osm.pbf and tiny_more.osm.pbf,
#: written once from these two texts with pyosmium's SimpleWriter),
#: because GDAL's OSM driver - the thing under test - reads .pbf, and
#: an XML body would be refused by the fetch as a web page, rightly.
OSM_XML_MORE = OSM_XML.replace(b"</osm>", b""" <node id="13" lat="59.40" lon="18.10" version="1"/>
 <node id="14" lat="59.40" lon="18.11" version="1"/>
 <node id="15" lat="59.41" lon="18.11" version="1"/>
 <way id="16" version="1"><nd ref="13"/><nd ref="14"/><nd ref="15"/>
  <nd ref="13"/><tag k="building" v="house"/></way>
</osm>""")


def pbf(name="tiny"):
    return (FIX / f"{name}.osm.pbf").read_bytes()


def add_geofabrik(web):
    """The trimmed index, and files for the regions the tests use:
    Sweden and Kenya shapefile zips; Norway's zip MISSING (as found);
    Bayern's and Berlin's zips; dated .pbf for Bayern 2020 and 2022."""
    web.add_json(f"{GF}/index-v1-nogeom.json",
                 fixture("geofabrik_index_trimmed.json"))
    when = datetime(2026, 10, 14, 21, 30, tzinfo=timezone.utc)
    ix = {f["properties"]["id"]: f["properties"]
          for f in web.json[f"{GF}/index-v1-nogeom.json"]["features"]}
    for rid in ("sweden", "kenya", "bayern", "berlin", "england",
                "scotland", "norcal", "socal", "us/alabama"):
        web.add_file(ix[rid]["urls"]["shp"],
                     body=shapefile_zip(rid), when=when)
    for rid in ("sweden", "norway", "kenya", "bayern", "berlin", "georgia",
                "germany", "great-britain"):
        url = ix[rid]["urls"]["pbf"]
        add_pbf(web, url, pbf("tiny_more"), when)
    for rid, yy in (("bayern", "20"), ("bayern", "22"), ("sweden", "20")):
        base = ix[rid]["urls"]["pbf"].replace("-latest.osm.pbf", "")
        url = f"{base}-{yy}0101.osm.pbf"
        add_pbf(web, url, pbf("tiny"),
                datetime(2000 + int(yy), 1, 1, 22, tzinfo=timezone.utc))
    return web


def add_pbf(web, url, body, when):
    """A .pbf and its .md5 sidecar, as Geofabrik publishes them."""
    web.add_file(url, body=body, when=when)
    web.add_file(url + ".md5", body=(
        hashlib.md5(body).hexdigest() + f"  {url.rsplit('/', 1)[1]}\n"
    ).encode(), when=when)


def captured(bodies=False):
    web = FakeWeb()
    add_worldpop(web, bodies=bodies)
    add_geofabrik(web)
    return web
