"""
catalogue.py - MACHINE 5, first half: WHAT IS THERE, as one table.

BACKLOG 414, v1.58.0. The fetch tool asked for a table of settings -
`project`, `category`, `iso3`, `year` - and John spent a whole session
learning what to type into it. The words were WorldPop's, not his,
and every provider had different ones. Three probe rounds (14 October
2026, run by John against the live services) then mapped how the two
providers he uses most actually arrange their data:

  WorldPop    project -> category -> record (one country, one year)
              -> files (one GeoTIFF per sex and age band)
  Geofabrik   region tree (continent -> country -> state) -> one
              extract per region, as a shapefile zip of 20 layers or
              an OSM .pbf; dated .pbf copies on 1 January of past years

So the tool no longer asks what to type. It LISTS WHAT EXISTS, as a
table with ONE ROW PER DOWNLOADABLE THING and THE SAME COLUMNS FOR
EVERY PROVIDER. The user selects rows (in QGIS: in the attribute
table, with the tools QGIS already has for selecting), and the fetch
step downloads exactly those rows. Nothing is downloaded here.

THE PRACTICES THIS FOLLOWS (agreed with John, 14 October 2026):

  1. No typing of keys. Places and years are typed in plain words;
     everything else is a row to select.
  2. One table shape for every provider (COLUMNS below).
  3. Look before downloading: every row carries its size, and says
     whether the size was measured or estimated.
  4. The smallest correct unit: one GeoTIFF, one shapefile LAYER out
     of a zip of twenty - not the zip.
  5. Warn at selection, not after: a row says when it comes from a
     different series, method or resolution than the others.
  6. Provenance comes from the publisher: licence, citation and DOI
     are copied from what WorldPop states, never written here.
  7. A recipe and a manifest: the fetched rows are kept as a table
     that can be fetched again.
  8. Dated catalogues: the date of every extract is in its row and in
     the name of every file made from it.

And one more that the probes taught: FOR CHANGE OVER TIME, TAKE EVERY
YEAR IN THE SAME FORM. WorldPop's 2000-2020 series and its R2025A
release differ in method and in their top age band; Geofabrik's
shapefiles and its raw .pbf differ in classification. A difference
between two years must not be a difference between two products, so
the catalogue keeps one product across years whenever one covers them
all, and says so in every row when none does.

    from equipop.doors.catalogue import browse_worldpop, browse_geofabrik
    rows = browse_worldpop("age_sex", "Sweden, Kenya, Burundi", "2015, 2020")
    rows = browse_geofabrik("Sweden", ["buildings", "roads"])
"""

from __future__ import annotations

import csv
import difflib
import io
import json
import os
import re
import time
import unicodedata
import urllib.parse
import zipfile
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from .fetching import FetchError, url_filename

# ------------------------------------------------------------ the table
#: THE ONE SHAPE. Every provider's rows have exactly these columns, in
#: this order; a column that means nothing for a provider is left empty
#: rather than dropped, so two catalogues can be stacked and filtered
#: with the same expression. (name, kind) - kind is str, int or float.
COLUMNS = (
    ("provider", "str"),     # WorldPop | Geofabrik
    ("theme", "str"),        # age_sex | population | osm
    ("series", "str"),       # R2025A | 2000-2020 | shapefile | pbf
    ("place", "str"),        # the publisher's own name for it
    ("place_code", "str"),   # ISO3 for WorldPop, region id for Geofabrik
    ("year", "int"),
    ("date", "str"),         # publisher's date (YYYY-MM-DD)
    ("layer", "str"),        # f_15 | pop | buildings_a | roads ...
    ("sex", "str"),          # f | m | t (both) | empty
    ("age_from", "int"),
    ("age_to", "int"),       # empty = open-ended (90+)
    ("resolution", "str"),   # 100m | 1km | empty for vectors
    ("format", "str"),
    ("crs", "str"),
    ("size_mb", "float"),
    ("size_is", "str"),      # measured | estimated | shared | unknown
    ("file", "str"),         # the name it will be saved under
    ("url", "str"),
    ("inside", "str"),       # what to take from inside the download
    ("md5_url", "str"),
    ("licence", "str"),
    ("citation", "str"),
    ("doi", "str"),
    ("source_page", "str"),
    ("record_id", "str"),
    ("note", "str"),
)
COLUMN_NAMES = tuple(c for c, _ in COLUMNS)


def blank_row(**values):
    """A row with every column, unknown keys refused."""
    bad = sorted(set(values) - set(COLUMN_NAMES))
    if bad:
        raise KeyError(f"not catalogue columns: {', '.join(bad)}")
    row = {c: None for c in COLUMN_NAMES}
    row.update(values)
    return row


def write_csv(rows, path):
    """The table as CSV - the columns in COLUMNS order, always."""
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(COLUMN_NAMES),
                           extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k))
                        for k in COLUMN_NAMES})
    os.replace(tmp, path)
    return path


def coerce_row(raw):
    """A row read back from anywhere - a CSV, a QGIS feature - with each
    column in its own kind. Empty, NULL and 'None' become None."""
    out = {}
    kinds = dict(COLUMNS)
    for c in COLUMN_NAMES:
        v = raw.get(c)
        if v is not None and str(v).strip() in ("", "NULL", "None", "nan"):
            v = None
        if v is not None:
            if kinds[c] == "int":
                v = int(float(v))
            elif kinds[c] == "float":
                v = float(v)
            else:
                v = str(v)
        out[c] = v
    return out


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if rows:
        missing = [c for c in ("provider", "url", "file") if c not in rows[0]]
        if missing:
            raise FetchError(
                f"{os.path.basename(path)} is not a catalogue table: it has "
                f"no {', '.join(missing)} column. Make one with the "
                "WorldPop or OpenStreetMap catalogue tool.")
    return [coerce_row(r) for r in rows]


# -------------------------------------------------------- the network
#: Only these sites may appear in a row. A recipe is a CSV that can be
#: edited or passed on; the fetch step must not become a way to make
#: EquiPop download from wherever a cell says. A new provider adds its
#: domain here, in code, with its adapter.
ALLOWED_DOMAINS = ("worldpop.org", "geofabrik.de")


def check_url(url):
    """Refuse a URL that is not https on a provider's own domain."""
    p = urllib.parse.urlsplit(str(url or ""))
    host = (p.hostname or "").lower()
    if p.scheme != "https" or not any(
            host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS):
        raise FetchError(
            f"{url!r} is not an https address at "
            f"{' or '.join(ALLOWED_DOMAINS)}, so EquiPop will not "
            "download it. Catalogue rows come from those providers; a "
            "row pointing elsewhere was edited or made by something "
            "else.")
    return url


#: Seconds between requests: a size check over 240 files is 240
#: requests, and a catalogue should not arrive at a provider as a burst.
DEFAULT_PAUSE = 0.05


#: HOW OFTEN A DROPPED, CUT, STALLED OR BUSY CONNECTION IS TRIED AGAIN,
#: and how long to wait before each new try, in seconds.
#:
#: v1.58.1, John's first live 5c run (16 October 2026): WorldPop's file
#: server took 7 to 11 seconds over EVERY request that morning - a size
#: check, a 146 kB file and a 1.6 MB file alike - where the probes of
#: 14 October had measured 0.2 s. One request it dropped without
#: answering ("RemoteDisconnected"), and 5c, which tried each file
#: once, stopped. A slow server is not a failure; a fetcher that gives
#: up at its first stumble turns it into one.
DEFAULT_TRIES = 4
DEFAULT_WAITS = (3, 10, 30)


class NetError(FetchError):
    """The network said no, in plain words."""


class Truncated(NetError):
    """Fewer bytes arrived than the server declared: a connection cut
    part-way through, which is worth trying again."""


def _root(exc):
    """The failure underneath EquiPop's own wrapping."""
    for _ in range(10):
        if (isinstance(exc, NetError) and not isinstance(exc, Truncated)
                and exc.__cause__ is not None):
            exc = exc.__cause__
        else:
            break
    return exc


def transient(exc):
    """Is this worth trying again? A dropped, cut, stalled or busy
    connection is. A missing file, a refusal, a name that does not
    resolve, a file REPLACED on the server, or bytes that fail their
    checksum are not: trying again cannot change those, and must not
    be allowed to hide them."""
    import http.client
    import socket
    import ssl
    import urllib.error
    exc = _root(exc)
    if isinstance(exc, Truncated):
        return True
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in (408, 429, 500, 502, 503, 504)
    if isinstance(exc, urllib.error.URLError) and isinstance(
            getattr(exc, "reason", None), BaseException):
        exc = exc.reason
    if isinstance(exc, socket.gaierror):
        return False
    return isinstance(exc, (http.client.RemoteDisconnected,
                            http.client.IncompleteRead, ConnectionError,
                            TimeoutError, socket.timeout, ssl.SSLEOFError,
                            ssl.SSLZeroReturnError))


def what_happened(exc, timeout=None):
    """A transient failure, in words a person can act on."""
    import http.client
    import ssl
    import urllib.error
    exc = _root(exc)
    if isinstance(exc, Truncated):
        return "stopped sending part-way through"
    if isinstance(exc, urllib.error.HTTPError):
        return f"answered {exc.code} - busy or briefly unavailable"
    if isinstance(exc, urllib.error.URLError) and isinstance(
            getattr(exc, "reason", None), BaseException):
        exc = exc.reason
    if isinstance(exc, http.client.RemoteDisconnected):
        return "closed the connection without answering"
    if isinstance(exc, http.client.IncompleteRead):
        return "stopped sending part-way through"
    if isinstance(exc, TimeoutError):
        return (f"did not answer within {timeout:g} s" if timeout
                else "did not answer in time")
    if isinstance(exc, (ssl.SSLEOFError, ssl.SSLZeroReturnError)):
        return "ended the secure connection unexpectedly"
    if isinstance(exc, ConnectionError):
        return "broke the connection off"
    return type(exc).__name__


class Net:
    """THE ONE DOOR TO THE NETWORK, so every test can replace it.

    Everything here goes through `opener(request) -> response`, which
    is urllib's urlopen in real use and a dictionary of captured
    answers in the tests. A response has .status, .headers and
    .read(n), and is a context manager.
    """

    def __init__(self, opener=None, pause=None, timeout=60, tries=None,
                 waits=None, say=None):
        self._open = opener or self._urlopen
        self.pause = DEFAULT_PAUSE if pause is None else pause
        self.timeout = timeout
        self.tries = max(1, int(DEFAULT_TRIES if tries is None else tries))
        self.waits = tuple(DEFAULT_WAITS if waits is None else waits)
        self.say = say or print
        self.calls = 0
        self.retries = 0

    def attempt(self, url, fn):
        """fn(), tried again after a dropped, cut, stalled or busy
        connection - and ONLY then (see transient). Each new try is
        said, so a slow run reads as slow and not as stuck."""
        host = urllib.parse.urlsplit(str(url)).hostname or str(url)
        waited = 0.0
        for i in range(1, self.tries + 1):
            try:
                return fn()
            except Exception as e:
                if not transient(e):
                    raise
                what = what_happened(e, self.timeout)
                if i == self.tries:
                    raise NetError(
                        f"{host} {what} - {self.tries} tries in a row for "
                        f"{url_filename(url)}, with {waited:g} s of waiting "
                        "between them. That is the server being busy or "
                        "down, not EquiPop: try again later.") from e
                wait = (self.waits[min(i - 1, len(self.waits) - 1)]
                        if self.waits else 0)
                self.retries += 1
                self.say(f"[net] {host} {what} ({url_filename(url)}) - "
                         f"trying again in {wait:g} s, try {i + 1} of "
                         f"{self.tries}.")
                if wait:
                    time.sleep(wait)
                waited += wait

    def _urlopen(self, req):                          # pragma: no cover
        import urllib.request
        return urllib.request.urlopen(req, timeout=self.timeout)

    @staticmethod
    def _headers(resp):
        h = getattr(resp, "headers", None) or {}
        try:
            items = h.items()
        except AttributeError:                        # pragma: no cover
            items = dict(h).items()
        return {str(k).lower(): v for k, v in items}

    def open(self, url, method="GET", headers=None):
        """A response, or NetError. The caller closes it."""
        import urllib.error
        import urllib.request
        check_url(url)
        from .. import __version__
        req = urllib.request.Request(
            url, method=method,
            headers={"User-Agent": f"EquiPop/{__version__} (catalogue)",
                     **(headers or {})})
        if self.pause:
            time.sleep(self.pause)
        self.calls += 1
        try:
            return self._open(req)
        except urllib.error.HTTPError as e:
            raise NetError(f"{url} answered {e.code}"
                           + (f" ({e.reason})" if e.reason else "")) from e
        except NetError:
            raise
        except Exception as e:
            raise NetError(f"could not reach {url}: "
                           f"{type(e).__name__}: {e}") from e

    def get_json(self, url):
        def once():
            with self.open(url) as r:
                return r.read()
        body = self.attempt(url, once)
        try:
            return json.loads(body.decode("utf-8"))
        except Exception as e:
            raise NetError(f"{url} did not answer with readable JSON "
                           f"({type(e).__name__})") from e

    def get_text(self, url, limit=64 * 1024):
        """A small text file - a .md5 sidecar - capped at `limit`."""
        def once():
            with self.open(url) as r:
                return r.read(limit)
        return self.attempt(url, once).decode("utf-8", "replace")

    def head(self, url):
        """(status, headers). A 404 is an ANSWER here, not an error -
        whether a dated extract exists is asked exactly this way."""
        import urllib.error

        def once():
            with self.open(url, method="HEAD") as r:
                return getattr(r, "status", 200), self._headers(r)
        try:
            return self.attempt(url, once)
        except NetError as e:
            cause = _root(e)
            if isinstance(cause, urllib.error.HTTPError):
                return cause.code, {}
            raise

    def get_range(self, url, lo, hi, validator=None):
        """Bytes lo..hi inclusive, or NetError. `validator` (an ETag or
        a Last-Modified date) makes the server refuse the range if the
        file has been replaced since it was looked at."""
        hdr = {"Range": f"bytes={lo}-{hi}"}
        if validator:
            hdr["If-Range"] = validator

        def once():
            with self.open(url, headers=hdr) as r:
                st = getattr(r, "status", 200)
                if st != 206:
                    raise NetError(
                        f"{url} did not send part of the file (status "
                        f"{st}). "
                        + ("It has been REPLACED since it was looked at - "
                           "look again." if validator and st == 200 else
                           "The server does not offer partial downloads."))
                body = r.read(hi - lo + 1)
            if len(body) != hi - lo + 1:
                raise Truncated(f"{url} sent {len(body)} bytes of a "
                                f"{hi - lo + 1}-byte range")
            return body
        return self.attempt(url, once)


def size_of(headers):
    v = (headers or {}).get("content-length")
    return int(v) if v and str(v).isdigit() else None


def date_of(headers):
    """The Last-Modified day, as YYYY-MM-DD, or None."""
    v = (headers or {}).get("last-modified")
    if not v:
        return None
    try:
        return parsedate_to_datetime(v).astimezone(timezone.utc) \
            .strftime("%Y-%m-%d")
    except Exception:
        return None


def validator_of(headers):
    """What If-Range should carry: a strong ETag, else the date."""
    et = (headers or {}).get("etag")
    if et and not str(et).startswith("W/"):
        return et
    return (headers or {}).get("last-modified")


# ------------------------------------------------- inside a remote zip
class RangeFile(io.RawIOBase):
    """A remote file read in pieces, so zipfile can read the table of
    contents at the END of a 2 GB zip without fetching the rest.

    From the third probe (14 October 2026), where it read Sweden's
    1.87 GB shapefile zip in two requests."""

    def __init__(self, net, url, size, validator=None, block=1 << 16):
        self.net, self.url, self.size = net, url, size
        self.validator, self.block = validator, block
        self.pos, self.cache, self.error = 0, {}, None

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        out = []
        while n > 0 and self.pos < self.size:
            bi = self.pos // self.block
            if bi not in self.cache:
                lo = bi * self.block
                hi = min(self.size, lo + self.block) - 1
                try:
                    self.cache[bi] = self.net.get_range(
                        self.url, lo, hi, self.validator)
                except NetError as e:
                    # zipfile swallows OSError while it hunts for the
                    # table of contents and then says only "not a zip
                    # file", so the real reason is kept here as well
                    self.error = str(e)
                    raise OSError(self.error) from e
            chunk = self.cache[bi]
            take = chunk[self.pos - bi * self.block:][:n]
            if not take:                              # pragma: no cover
                break
            out.append(take)
            self.pos += len(take)
            n -= len(take)
        return b"".join(out)

    def readinto(self, b):                            # pragma: no cover
        data = self.read(len(b))
        b[:len(data)] = data
        return len(data)


def zip_contents(net, url, size, validator=None):
    """The zip's members (zipfile.ZipInfo), read from its end only."""
    rf = RangeFile(net, url, size, validator)
    try:
        return zipfile.ZipFile(rf).infolist()
    except Exception as e:
        raise NetError(f"could not read the contents of {url}: "
                       f"{rf.error or type(e).__name__ + ': ' + str(e)}"
                       ) from e


#: Geofabrik's shapefile members: gis_osm_<layer>_free_<part>.<ext>
_GF_MEMBER = re.compile(r"^gis_osm_(?P<layer>[a-z_]+?)_free_(?P<part>\d+)"
                        r"\.(?P<ext>[A-Za-z0-9]+)$")


def layers_in_zip(members):
    """Members grouped by LAYER: a shapefile is five files (.shp .shx
    .dbf .prj .cpg), and a large layer may come in numbered parts.

    `members` are (name, unpacked, packed) or ZipInfo. Returns
    {layer: {"members": [...], "packed": n, "size": n, "parts": [..]}}.
    Names that do not follow Geofabrik's pattern (the README) are left
    out - they are not layers."""
    out = {}
    for m in members:
        if isinstance(m, zipfile.ZipInfo):
            name, size, packed = m.filename, m.file_size, m.compress_size
        elif isinstance(m, dict):
            name, size, packed = m["name"], m["size"], m["packed"]
        else:
            name, size, packed = m
        hit = _GF_MEMBER.match(os.path.basename(name))
        if not hit:
            continue
        d = out.setdefault(hit["layer"], {"members": [], "packed": 0,
                                          "size": 0, "parts": set()})
        d["members"].append(name)
        d["packed"] += packed
        d["size"] += size
        d["parts"].add(int(hit["part"]))
    for d in out.values():
        d["members"].sort()
        d["parts"] = sorted(d["parts"])
    return out


# ------------------------------------------------------- plain words
def _fold(text):
    """Casefolded, accents removed: "Côte d'Ivoire" == "cote d'ivoire"."""
    t = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in t if not unicodedata.combining(c)).casefold() \
        .strip()


def split_list(value):
    """'Sweden, Kenya; BDI' -> ['Sweden', 'Kenya', 'BDI']. A list passes
    through. Commas, semicolons and new lines all separate."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        items = [str(v) for v in value]
    else:
        items = re.split(r"[,;\n]+", str(value))
    return [i.strip() for i in items if i and i.strip()]


def parse_years(value):
    """'2015, 2020' or '2010-2015' or [2015, 2020] -> sorted ints.
    Empty means "every year there is"."""
    if value is None or value == "":
        return []
    if isinstance(value, int):
        value = [value]
    years = set()
    for item in split_list(value):
        m = re.fullmatch(r"(\d{4})\s*(?:-|–|:|to)\s*(\d{4})", item)
        if m:
            a, b = sorted((int(m[1]), int(m[2])))
            years.update(range(a, b + 1))
        elif re.fullmatch(r"\d{4}", item):
            years.add(int(item))
        else:
            raise FetchError(
                f"{item!r} is not a year. Give years such as 2015, 2020 "
                "or a span such as 2010-2015.")
    bad = sorted(y for y in years if not 1900 <= y <= 2100)
    if bad:
        raise FetchError(f"{bad[0]} is not a year these catalogues hold.")
    return sorted(years)


def match_places(asked, known, what, codes=None, labels=None):
    """Each typed place -> one key of `known` ({key: name}).

    Accepts the key, a code from `codes` ({key: [codes]}), the exact
    name (accents and case ignored), or a part of the name that fits
    ONE place. Refuses anything that fits several, and suggests the
    nearest names for one that fits none - with every problem in ONE
    message, so a list of five places is not corrected one refusal at
    a time.

    THE KEY, THE CODES AND THE NAME ARE ONE TIER. Geofabrik has a
    country whose id is 'georgia' and a US state whose name is
    'Georgia'; taking the id first would hand an American the
    Caucasus without a word. Both fit, so both are named."""
    codes = codes or {}
    labels = labels or known
    by_name = {}
    for k, n in known.items():
        by_name.setdefault(_fold(n), []).append(k)
    out, problems = [], []
    for item in split_list(asked):
        f = _fold(item)
        hits = {k for k in known if _fold(k) == f}
        hits |= {k for k, cs in codes.items() if f in {_fold(c) for c in cs}}
        hits |= set(by_name.get(f, []))
        # A PART OF A NAME, but never a short one: 'CHE' or 'GER' is
        # someone's code for a country, and as a fragment it fits
        # whatever name happens to contain those letters.
        if not hits and len(f) >= 4:
            hits = {k for k, n in known.items() if f in _fold(n)}
        if len(hits) == 1:
            k = hits.pop()
            if k not in out:
                out.append(k)
            continue
        if hits:
            problems.append(
                f"  {item!r} fits {len(hits)} places - give one of: "
                + "; ".join(f"{labels[k]} ({k})" for k in sorted(hits)[:12]))
            continue
        near = difflib.get_close_matches(
            f, list(by_name) + [_fold(k) for k in known], n=4, cutoff=0.6)
        names = []
        for n in near:
            for k in by_name.get(n, []) or [k for k in known if _fold(k) == n]:
                lab = f"{labels[k]} ({k})"
                if lab not in names:
                    names.append(lab)
        problems.append(f"  {item!r} is not a {what}"
                        + (" - did you mean " + "; ".join(names) + "?"
                           if names else "."))
    if problems:
        raise FetchError("Some places were not recognised:\n"
                         + "\n".join(problems))
    if not out:
        raise FetchError(f"No {what} was given.")
    return out


def _mb(n):
    return None if n is None else round(n / 1e6, 3)


# ============================================================ WorldPop
WP_ROOT = "https://www.worldpop.org/rest/data"

#: THE PRODUCTS THAT COUNT PEOPLE, per country, as WorldPop's catalogue
#: names them (probe rounds 1 and 2, 14 October 2026). Written down
#: rather than discovered, because which products are COMPARABLE is a
#: judgement the API cannot make - but the years and countries of each
#: are read from the live index, never assumed. Newest first: the
#: first series that covers a request is the one taken.
WP_SERIES = (
    # theme, series, resolution, project, alias, method
    ("age_sex", "R2025A", "1km", "age_structures", "G2_CN_Age_R25A_1km",
     "constrained"),
    ("age_sex", "R2025A", "100m", "age_structures", "G2_CN_Age_R25A_100m",
     "constrained"),
    ("age_sex", "2000-2020", "100m", "age_structures", "aswpgp",
     "unconstrained"),
    ("population", "R2025A", "1km", "pop", "G2_CN_POP_R25A_1km",
     "constrained"),
    ("population", "R2025A", "100m", "pop", "G2_CN_POP_R25A_100m",
     "constrained"),
    ("population", "2000-2020", "1km", "pop", "wpic1km", "unconstrained"),
    ("population", "2000-2020", "100m", "pop", "wpgp", "unconstrained"),
)
WP_THEMES = {"age_sex": "Age and sex (people per sex and age band)",
             "population": "Population (all people)"}

_METHOD_WORDS = {
    "constrained": "constrained - people are placed only in cells "
                   "WorldPop maps as built settlement",
    "unconstrained": "unconstrained - people may be placed in any cell",
}

#: A newer release than any above, by its catalogue alias. Seen, the
#: user is told; the table above is not silently out of date.
_WP_RELEASE = re.compile(r"^G2_CN_(Age|POP)_R(\d{2})([A-Z])_(100m|1km)$")

#: File names, as WorldPop states them in each record's description:
#: {iso}_{sex}_{age}_{year}_{type}_{res}_{release}_{version}.tif
_WP_FILE = (
    ("agesex", re.compile(
        r"^(?P<iso>[a-z]{3})_(?P<sex>[fmt])_(?P<age>\d{2})_(?P<year>\d{4})"
        r"_(?:CN|UC)_(?:100m|1km)_R\d{4}[A-Z](?:_UA)?_v\d+\.tif$")),
    ("total", re.compile(
        r"^(?P<iso>[a-z]{3})_T_(?P<tot>[FM])_(?P<year>\d{4})"
        r"_(?:CN|UC)_(?:100m|1km)_R\d{4}[A-Z](?:_UA)?_v\d+\.tif$")),
    ("pop", re.compile(
        r"^(?P<iso>[a-z]{3})_pop_(?P<year>\d{4})"
        r"_(?:CN|UC)_(?:100m|1km)_R\d{4}[A-Z](?:_UA)?_v\d+\.tif$")),
    ("agesex", re.compile(                          # 2000-2020 series
        r"^(?P<iso>[a-z]{3})_(?P<sex>[fm])_(?P<age>\d{1,2})_(?P<year>\d{4})"
        r"\.tif$")),
    ("pop", re.compile(
        r"^(?P<iso>[a-z]{3})_ppp_(?P<year>\d{4})(?:_1km_Aggregated)?\.tif$")),
)


def parse_worldpop_name(name):
    """What a WorldPop file holds, from its name: {"kind", "sex",
    "age"} - or None for a name that follows none of the patterns."""
    for kind, rx in _WP_FILE:
        m = rx.match(name)
        if m:
            g = m.groupdict()
            if kind == "total":
                return {"kind": "total", "sex": g["tot"].lower(), "age": None}
            if kind == "pop":
                return {"kind": "pop", "sex": "t", "age": None}
            return {"kind": "agesex", "sex": g["sex"], "age": int(g["age"])}
    return None


class WorldPopCatalogue:
    def __init__(self, net, say=print, root=WP_ROOT):
        self.net, self.say, self.root = net, say, root
        self._index = {}

    def index(self, project, alias):
        """The SLIM index: id, iso3, popyear and title of every record
        of a product - one request for all 242 countries."""
        key = (project, alias)
        if key not in self._index:
            data = self.net.get_json(f"{self.root}/{project}/{alias}")
            self._index[key] = [r for r in (data or {}).get("data", [])
                                if r.get("iso3")]
        return self._index[key]

    def records(self, project, alias, iso3):
        """FULL records, with files, for one country."""
        data = self.net.get_json(
            f"{self.root}/{project}/{alias}?iso3={iso3}")
        return (data or {}).get("data", []) or []

    def newer_releases(self, project, known):
        """Aliases of a newer release than the ones EquiPop knows."""
        try:
            cats = self.net.get_json(f"{self.root}/{project}")["data"]
        except Exception:
            return []
        rel = lambda a: (int(_WP_RELEASE.match(a)[2]),     # noqa: E731
                         _WP_RELEASE.match(a)[3])
        mine = [rel(a) for a in known if _WP_RELEASE.match(a)]
        top = max(mine) if mine else (0, "")
        out = []
        for c in cats:
            a = str(c.get("alias") or "").strip()
            if _WP_RELEASE.match(a) and rel(a) > top:
                out.append(a)
        return sorted(out)


def _choose_series(cands, pairs, have):
    """The FIRST candidate (newest, preferred resolution first) that
    holds every (place, year) asked for - or None."""
    for c in cands:
        if pairs <= have[c]:
            return c
    return None


def browse_worldpop(theme, places, years=None, resolution="1km", *,
                    include_totals=False, exact_sizes=False, net=None,
                    say=print):
    """Rows for every file of `theme` for these places and years.

    theme        "age_sex" or "population"
    places       names or ISO3 codes: "Sweden, KEN, Burundi"
    years        "2015, 2020", "2010-2020", or empty for every year
    resolution   "1km" (default: 2.2 MB a file for Sweden, against
                 47 MB at 100 m - measured, probe round 2) or "100m"
    include_totals  also list the layers that are sums of others: both
                 sexes ("t_") and all ages ("T_F", "T_M"). Off, because
                 they add nothing that cannot be added up, and at 100 m
                 they are a third of the download.
    exact_sizes  measure every file (one request each). Off: one file
                 per country and year is measured and the rest are
                 estimated from it, which the size_is column says.
    """
    net = net or Net()
    net.say = say
    if theme not in WP_THEMES:
        raise FetchError(
            f"No WorldPop theme {theme!r}. Choose one of: "
            + "; ".join(f"{k} - {v}" for k, v in WP_THEMES.items()))
    resolution = str(resolution or "1km").replace(" ", "").lower()
    if resolution not in ("1km", "100m"):
        raise FetchError(f"Resolution {resolution!r}: choose 1km or 100m.")
    yrs = parse_years(years)
    wp = WorldPopCatalogue(net, say)

    # newest first; within a release, the resolution asked for first
    mine = [s for s in WP_SERIES if s[0] == theme]
    order = []
    for series in dict.fromkeys(s[1] for s in mine):
        same = [s for s in mine if s[1] == series]
        order += sorted(same, key=lambda s: s[2] != resolution)

    have, names = {}, {}
    for s in order:
        idx = wp.index(s[3], s[4])
        have[s] = {(r["iso3"], int(r["popyear"])) for r in idx
                   if str(r.get("popyear") or "").isdigit()}
        for r in idx:
            if " - " in str(r.get("title", "")):
                names.setdefault(r["iso3"], r["title"].rsplit(" - ", 1)[0])
    for s in order:
        for iso, _ in have[s]:
            names.setdefault(iso, iso)

    isos = match_places(places, names, "country WorldPop publishes")

    newer = wp.newer_releases(mine[0][3], [s[4] for s in mine])
    if newer:
        say(f"[catalogue] WorldPop lists {', '.join(newer)}, a NEWER "
            "release than this version of EquiPop knows. The rows below "
            "are from the newest release it does know; an update of "
            "EquiPop will add the new one.")

    if not yrs:
        top = order[0]
        yrs = sorted({y for iso, y in have[top] if iso in isos})
        say(f"[catalogue] No year given: every year of {top[1]} "
            f"({yrs[0]}-{yrs[-1]}) is listed.")

    # ONE SERIES FOR EVERY YEAR, WHEN ONE EXISTS
    pairs = {(i, y) for i in isos for y in yrs}
    one = _choose_series(order, pairs, have)
    plan = {}
    if one:
        for p in pairs:
            plan[p] = one
        if one[2] != resolution:
            say(f"[catalogue] {one[1]} is not published per country at "
                f"{resolution}, so it is listed at {one[2]}: one series "
                "for every year matters more than the resolution, which "
                "can be coarsened afterwards. See the size column.")
    else:
        for p in sorted(pairs):
            c = _choose_series(order, {p}, have)
            if c:
                plan[p] = c
        gone = sorted(pairs - set(plan))
        if gone:
            raise FetchError(
                "WorldPop has no " + theme.replace("_", " and ")
                + " data for: " + ", ".join(f"{names.get(i, i)} {y}"
                                            for i, y in gone)
                + ". Every year it has for these places: "
                + "; ".join(f"{names.get(i, i)} "
                            + _span(sorted({y for s in order
                                            for j, y in have[s] if j == i}))
                            for i in isos))
    used = sorted({(s[1], s[2]) for s in plan.values()})
    mixed = len({s[1] for s in plan.values()}) > 1
    if mixed:
        say("[catalogue] NO ONE SERIES COVERS EVERY YEAR asked for, so "
            "the rows come from " + " and ".join(f"{a} ({b})"
                                                 for a, b in used)
            + ". A change between those years is PARTLY A CHANGE OF "
              "METHOD. Each row's note says which it is.")

    rows, absent = [], []
    for (iso, s), want in _group(plan).items():
        theme_, series, res, project, alias, method = s
        recs = [r for r in wp.records(project, alias, iso)
                if str(r.get("popyear")) in {str(y) for y in want}]
        # THE INDEX AND THE RECORDS ARE TWO ANSWERS. A year the index
        # lists and the country's records then lack must be SAID - a
        # table one year short looks exactly like a complete one.
        got = {str(r.get("popyear")) for r in recs}
        absent += [f"{names.get(iso, iso)} {y}" for y in sorted(want)
                   if str(y) not in got]
        for rec in sorted(recs, key=lambda r: str(r.get("popyear"))):
            rows += _worldpop_rows(rec, s, include_totals, mixed, used)
    if absent:
        say("[catalogue] WorldPop's index lists " + ", ".join(absent)
            + ", but the records it sent back do not hold "
            + ("it" if len(absent) == 1 else "them")
            + " - not listed. Try again later; if it repeats, the "
              "catalogue and the records disagree at WorldPop.")
    place_order = {iso: i for i, iso in enumerate(isos)}
    rows.sort(key=lambda r: (place_order.get(r["place_code"], 99),
                             r["year"], r["series"], r["sex"] or "",
                             -1 if r["age_from"] is None else r["age_from"],
                             r["file"]))
    if not rows:
        raise FetchError("WorldPop listed those records but no files in "
                         "them. Nothing to select.")
    _worldpop_sizes(rows, net, exact_sizes, say)
    _summarise(rows, say)
    return rows


def _span(years):
    if not years:
        return "(none)"
    return f"{years[0]}-{years[-1]}" if len(years) > 1 else str(years[0])


def _group(plan):
    out = {}
    for (iso, y), s in plan.items():
        out.setdefault((iso, s), []).append(y)
    return out


def _worldpop_rows(rec, s, include_totals, mixed, used):
    theme, series, res, project, alias, method = s
    files = sorted(u for u in (rec.get("files") or [])
                   if url_filename(u).lower().endswith((".tif", ".tiff")))
    parsed = {u: parse_worldpop_name(url_filename(u)) for u in files}
    ages = sorted({p["age"] for p in parsed.values()
                   if p and p["kind"] == "agesex"})
    upper = {a: (ages[i + 1] - 1 if i + 1 < len(ages) else None)
             for i, a in enumerate(ages)}
    top = f"{ages[-1]}+" if ages else ""
    base = (f"WorldPop {series}, {res}, {_METHOD_WORDS[method]}"
            + (f"; age bands up to {top}" if top else ""))
    if mixed:
        others = [f"{a} ({b})" for a, b in used if (a, b) != (series, res)]
        base += ("; MIXED SERIES - other rows come from "
                 + ", ".join(others) + ", so a change between them is "
                 "partly a change of method")
    out = []
    for u in files:
        p = parsed[u]
        name = url_filename(u)
        note = base
        if p is None:
            layer, sex, a0, a1 = os.path.splitext(name)[0], None, None, None
            note += "; FILE NAME NOT RECOGNISED - check what it holds"
        elif p["kind"] == "total":
            if not include_totals:
                continue
            layer, sex, a0, a1 = f"T_{p['sex'].upper()}", p["sex"], 0, None
            note += "; the sum of this sex's age bands"
        elif p["kind"] == "pop":
            layer, sex, a0, a1 = "pop", "t", 0, None
        else:
            if p["sex"] == "t" and not include_totals:
                continue
            layer = f"{p['sex']}_{p['age']:02d}"
            sex, a0, a1 = p["sex"], p["age"], upper.get(p["age"])
            if p["sex"] == "t":
                note += "; both sexes - the sum of the f_ and m_ files"
        out.append(blank_row(
            provider="WorldPop", theme=theme, series=series,
            place=rec.get("country") or rec.get("iso3"),
            place_code=rec.get("iso3"), year=int(rec["popyear"]),
            date=rec.get("date"), layer=layer, sex=sex, age_from=a0,
            age_to=a1, resolution=res, format="GeoTIFF",
            crs="EPSG:4326", file=name, url=u, inside=None, md5_url=None,
            licence=rec.get("license"), citation=rec.get("citation"),
            doi=rec.get("doi"), source_page=rec.get("url_summary"),
            record_id=str(rec.get("id") or ""), note=note,
            size_mb=None, size_is="unknown"))
    return out


def _worldpop_sizes(rows, net, exact, say):
    """Measure one file per country, year and resolution (or every
    file), and estimate the rest from it."""
    groups = {}
    for r in rows:
        groups.setdefault((r["place_code"], r["year"], r["resolution"],
                           r["series"]), []).append(r)
    failed = 0
    for grp in groups.values():
        todo = grp if exact else [sorted(grp, key=lambda r: r["file"])
                                  [len(grp) // 2]]
        sizes = []
        for r in todo:
            try:
                st, h = net.head(r["url"])
            except NetError:
                st, h = None, {}
            n = size_of(h) if st == 200 else None
            if n is None:
                failed += 1
                continue
            r["size_mb"], r["size_is"] = _mb(n), "measured"
            sizes.append(n)
        if sizes and not exact:
            est = _mb(sum(sizes) / len(sizes))
            for r in grp:
                if r["size_is"] != "measured":
                    r["size_mb"], r["size_is"] = est, "estimated"
    if failed:
        say(f"[catalogue] {failed} size request(s) went unanswered; "
            "those rows say 'unknown'.")


def download_key(row):
    """What one download IS. A .pbf is shared by every layer taken from
    it, so its rows count once; a shapefile layer is its own download
    even though five layers name the same zip."""
    if row.get("size_is") == "shared" or str(row.get("format") or "") \
            .endswith(".pbf"):
        return (row.get("url"),)
    return (row.get("url"), row.get("inside"), row.get("file"))


def total_mb(rows):
    """(MB, downloads, any estimated or unknown) for these rows."""
    seen, total, est = set(), 0.0, False
    for r in rows:
        k = download_key(r)
        if k in seen:
            continue
        seen.add(k)
        if r.get("size_mb") is None:
            est = True
            continue
        total += float(r["size_mb"])
        est = est or r.get("size_is") in ("estimated", "unknown")
    return total, len(seen), est


def _summarise(rows, say):
    total, n, est = total_mb(rows)
    example = ("\"sex\" = 'f' AND \"age_from\" >= 15"
               if rows and rows[0]["provider"] == "WorldPop"
               else "\"layer\" = 'roads'")
    unknown = sum(1 for r in rows if r["size_mb"] is None)
    say(f"[catalogue] {len(rows)} rows, {n} download(s), "
        f"{'about ' if est else ''}{total:,.1f} MB if every row is "
        "taken" + (f" ({unknown} of unknown size)" if unknown else "")
        + ". NOTHING HAS BEEN DOWNLOADED.")
    say("[catalogue] Select the rows you want - in QGIS, in the "
        f"attribute table, e.g. Select by Expression {example} - then "
        "fetch the selected rows.")


# =========================================================== Geofabrik
GF_INDEX = "https://download.geofabrik.de/index-v1-nogeom.json"
GF_LICENCE = ("ODbL 1.0 - attribution AND SHARE-ALIKE on derived "
              "databases (opendatacommons.org/licenses/odbl)")
GF_CITATION = ("© OpenStreetMap contributors, openstreetmap.org/copyright. "
               "Extract by Geofabrik GmbH, download.geofabrik.de.")

#: WHAT A USER ASKS FOR -> Geofabrik's layer names. The shapefile zip
#: holds 20 layers (probe round 3: Sweden); "_a" layers are areas, the
#: others points or lines, so a theme can be two layers.
GF_THEMES = {
    "buildings": ("buildings_a",),
    "roads": ("roads",),
    "railways": ("railways",),
    "pois": ("pois", "pois_a"),
    "places": ("places", "places_a"),
    "landuse": ("landuse_a",),
    "water": ("water_a", "waterways"),
    "natural": ("natural", "natural_a"),
    "transport": ("transport", "transport_a"),
    "traffic": ("traffic", "traffic_a"),
    "worship": ("pofw", "pofw_a"),
    "protected": ("protected_areas_a",),
    "admin": ("adminareas_a",),
}

#: THE SAME LAYERS FROM A RAW .osm.pbf, for the years. A dated extract
#: is published only as .pbf, which holds OSM's own tags rather than
#: Geofabrik's classification, so these are GDAL OSM-driver layers with
#: an attribute filter on the default fields (checked against GDAL
#: 3.12's driver, 14 October 2026). Written into each row's `inside`
#: column, so what was taken is on record next to what was fetched.
PBF_RULES = {
    "buildings_a": "multipolygons: building IS NOT NULL",
    "roads": "lines: highway IS NOT NULL",
    "railways": "lines: railway IS NOT NULL",
    "pois": ("points: other_tags LIKE '%\"amenity\"=>%' OR other_tags "
             "LIKE '%\"shop\"=>%' OR other_tags LIKE '%\"tourism\"=>%' OR "
             "other_tags LIKE '%\"leisure\"=>%' OR other_tags LIKE "
             "'%\"office\"=>%' OR other_tags LIKE '%\"historic\"=>%'"),
    "pois_a": ("multipolygons: amenity IS NOT NULL OR shop IS NOT NULL OR "
               "tourism IS NOT NULL OR leisure IS NOT NULL OR office IS "
               "NOT NULL OR historic IS NOT NULL"),
    "places": "points: place IS NOT NULL",
    "places_a": "multipolygons: place IS NOT NULL",
    "landuse_a": "multipolygons: landuse IS NOT NULL",
    "waterways": "lines: waterway IS NOT NULL",
    "water_a": ("multipolygons: natural = 'water' OR landuse = "
                "'reservoir' OR landuse = 'basin'"),
}
OSM_LAYERS = ("points", "lines", "multilinestrings", "multipolygons",
              "other_relations")


def parse_rule(text):
    """'lines: highway IS NOT NULL' -> ('lines', 'highway IS NOT NULL')."""
    m = re.fullmatch(r"\s*([a-z_]+)\s*:\s*(.+?)\s*", str(text or ""), re.S)
    if not m or m[1] not in OSM_LAYERS:
        raise FetchError(
            f"{text!r} is not a rule for a .pbf layer: it should be one of "
            f"{', '.join(OSM_LAYERS)}, a colon, and a filter.")
    return m[1], m[2]


def gf_layers(themes):
    """['buildings', 'roads'] -> ['buildings_a', 'roads']. Geofabrik's
    own layer names are accepted too, and 'all' is every layer."""
    names = split_list(themes) or ["buildings"]
    every = [l for ls in GF_THEMES.values() for l in ls]
    out = []
    for n in names:
        k = _fold(n).replace(" ", "_")
        if k == "all":
            got = every
        elif k in GF_THEMES:
            got = list(GF_THEMES[k])
        elif k in every:
            got = [k]
        else:
            raise FetchError(
                f"No OpenStreetMap layer {n!r}. Choose from: "
                + ", ".join(GF_THEMES) + " - or 'all'.")
        out += [g for g in got if g not in out]
    return out


def _children(index, rid):
    """Sub-regions. Most name their parent; the United States' states
    instead carry 'us/' in their id and name North America as parent
    (probe round 1)."""
    return sorted(k for k, p in index.items()
                  if p.get("parent") == rid
                  or (k.startswith(rid + "/") and "/" not in k[len(rid) + 1:]))


def _page(urls):
    """The region's download page, from its .pbf address."""
    pbf = urls.get("pbf") or ""
    return re.sub(r"-latest\.osm\.pbf$", ".html", pbf) or None


def _stamp(date):
    return (date or "").replace("-", "")


def _safe_id(rid):
    return rid.replace("/", "-")


class GeofabrikCatalogue:
    def __init__(self, net, say=print, index_url=GF_INDEX):
        self.net, self.say, self.index_url = net, say, index_url
        self._ix = None

    def index(self):
        if self._ix is None:
            fc = self.net.get_json(self.index_url)
            self._ix = {f["properties"]["id"]: f["properties"]
                        for f in (fc or {}).get("features", [])
                        if (f.get("properties") or {}).get("id")}
            if not self._ix:
                raise FetchError("Geofabrik's index came back empty. It is "
                                 f"normally at {self.index_url}")
        return self._ix

    def resolve(self, places):
        ix = self.index()
        known = {k: p.get("name", k) for k, p in ix.items()}
        codes = {k: list(p.get("iso3166-1:alpha2") or [])
                 + list(p.get("iso3166-2") or []) for k, p in ix.items()}
        # the parent, so 'Georgia' can be told apart from 'Georgia (US)'
        labelled = {k: (f"{n} (in {ix[ix[k]['parent']]['name']})"
                        if ix[k].get("parent") in ix else n)
                    for k, n in known.items()}
        try:
            return match_places(places, known, "Geofabrik region", codes,
                                labels=labelled)
        except FetchError as e:
            msg = str(e)
            if re.search(r"'[A-Za-z]{3}' is not", msg):
                msg += ("\nGeofabrik does not use three-letter codes: give "
                        "the name, or the two-letter code (SE for Sweden).")
            raise FetchError(msg) from None

    def shapefile_regions(self, rid, via=None):
        """`rid`, or - when Geofabrik publishes no shapefile for it - the
        sub-regions that do have one: [(region id, the region asked)]."""
        ix = self.index()
        p = ix[rid]
        if "shp" in (p.get("urls") or {}):
            return [(rid, via)]
        out = []
        for c in _children(ix, rid):
            out += self.shapefile_regions(c, via or rid)
        return out


def browse_geofabrik(places, layers=("buildings",), years=None, *,
                     latest=True, net=None, say=print):
    """Rows for OpenStreetMap layers of these regions.

    places   names, Geofabrik ids or two-letter codes: "Sweden, Kenya"
    layers   themes - buildings, roads, railways, pois, places, landuse,
             water, ... ('all' for every one) - or Geofabrik's own
             layer names (buildings_a, pois_a)
    years    past years, as 1 January extracts: "2018, 2022". Empty:
             the current extract only.
    latest   also list the current extract (with years given).

    THE CURRENT EXTRACT ALONE comes from the shapefile zip, ONE LAYER AT
    A TIME: Sweden's buildings are 329 MB of a 1.87 GB zip, and only
    those bytes are fetched. WITH YEARS, every row - the current one
    too - comes from the .pbf, because the dated extracts exist only
    as .pbf and a comparison across years must not also be a
    comparison between two classifications.
    """
    net = net or Net()
    net.say = say
    yrs = parse_years(years)
    want = gf_layers(layers)
    gf = GeofabrikCatalogue(net, say)
    ix = gf.index()
    regions = gf.resolve(places)
    rows = []
    if yrs:
        no_rule = [l for l in want if l not in PBF_RULES]
        if no_rule:
            raise FetchError(
                "For past years the layers come from OSM's raw .pbf, and "
                "EquiPop has no rule for " + ", ".join(no_rule) + " there. "
                "Layers available for years: " + ", ".join(PBF_RULES) + ".")
        for rid in regions:
            p = ix[rid]
            pbf = (p.get("urls") or {}).get("pbf")
            if not pbf:
                say(f"[catalogue] {p.get('name')}: no .pbf published - "
                    "skipped.")
                continue
            for y in yrs:
                url = pbf.replace("-latest.osm.pbf", f"-{y % 100:02d}0101.osm.pbf")
                rows += _pbf_rows(net, p, rid, url, f"{y}-01-01", want, say,
                                  None)
            if latest:
                rows += _pbf_rows(net, p, rid, pbf, None, want, say, None)
    else:
        for asked in regions:
            subs = gf.shapefile_regions(asked)
            if not subs:
                say(f"[catalogue] {ix[asked].get('name')}: Geofabrik "
                    "publishes no shapefile for it or its parts - its "
                    ".pbf is listed instead.")
                rows += _pbf_rows(net, ix[asked], asked,
                                  ix[asked]["urls"]["pbf"], None,
                                  [l for l in want if l in PBF_RULES], say,
                                  "no shapefile is published for it")
                continue
            if subs != [(asked, None)]:
                say(f"[catalogue] {ix[asked].get('name')}: Geofabrik "
                    f"publishes no shapefile for the whole of it, so its "
                    f"{len(subs)} parts that have one are listed instead.")
            for rid, via in subs:
                rows += _shp_rows(net, ix, rid, via, want, say)
    if not rows:
        raise FetchError("Nothing to list for those places and years.")
    say("[catalogue] OpenStreetMap is ODbL: attribution AND SHARE-ALIKE on "
        "derived databases. A surface published from it may carry the "
        "same obligation - check before publishing.")
    _summarise(rows, say)
    return rows


def _shp_rows(net, ix, rid, via, want, say):
    p = ix[rid]
    url = p["urls"]["shp"]
    try:
        st, h = net.head(url)
    except NetError as e:
        st, h, why = None, {}, str(e)
    else:
        why = f"answered {st}"
    if st != 200 or not size_of(h):
        # Norway's shapefile is in the index and 404 on the server
        # (probe round 3); the .pbf of the same day is there.
        say(f"[catalogue] {p.get('name')}: the shapefile zip {why} - its "
            ".pbf is listed instead.")
        return _pbf_rows(net, p, rid, p["urls"]["pbf"], None,
                         [l for l in want if l in PBF_RULES], say,
                         "the shapefile zip could not be reached")
    date = date_of(h)
    try:
        layers = layers_in_zip(zip_contents(net, url, size_of(h),
                                            validator_of(h)))
    except NetError as e:
        say(f"[catalogue] {p.get('name')}: {e} - its .pbf is listed "
            "instead.")
        return _pbf_rows(net, p, rid, p["urls"]["pbf"], None,
                         [l for l in want if l in PBF_RULES], say,
                         "the shapefile zip could not be read in parts")
    out = []
    absent = [l for l in want if l not in layers]
    if absent:
        say(f"[catalogue] {p.get('name')}: no {', '.join(absent)} layer in "
            "its shapefile zip.")
    for l in want:
        if l not in layers:
            continue
        d = layers[l]
        note = (f"Geofabrik shapefile layer, extract of {date}; "
                f"{len(d['members'])} files, {_mb(d['size']):,.1f} MB "
                "unpacked")
        if via:
            note += (f"; part of {ix[via].get('name')} (Geofabrik publishes "
                     "its shapefiles by part)")
        if len(d["parts"]) > 1:
            note += f"; the layer comes in {len(d['parts'])} numbered parts"
        out.append(blank_row(
            provider="Geofabrik", theme="osm", series="shapefile",
            place=p.get("name"), place_code=rid,
            year=int(date[:4]) if date else None, date=date, layer=l,
            resolution=None, format="Shapefile layer", crs="EPSG:4326",
            size_mb=_mb(d["packed"]), size_is="measured",
            file=f"{_safe_id(rid)}_{_stamp(date)}_{l}.shp", url=url,
            inside=";".join(d["members"]), md5_url=None,
            licence=GF_LICENCE, citation=GF_CITATION, doi=None,
            source_page=_page(p.get("urls") or {}), record_id=rid,
            note=note))
    return out


def _pbf_rows(net, p, rid, url, date, want, say, why):
    try:
        st, h = net.head(url)
    except NetError as e:
        say(f"[catalogue] {p.get('name')}: {e}")
        return []
    if st != 200:
        say(f"[catalogue] {p.get('name')}: Geofabrik has no extract for "
            f"{date or 'today'} ({url_filename(url)} answered {st}).")
        return []
    if date is None:
        date = date_of(h)
    n = size_of(h)
    out = []
    for l in want:
        note = (f"from the whole-region .pbf of {date} "
                f"({_mb(n) if n else '?'} MB, downloaded ONCE for all of "
                "this region's layers that day); OSM's raw tags, not "
                "Geofabrik's classification - see 'inside' for the rule")
        if why:
            note += f"; .pbf because {why}"
        out.append(blank_row(
            provider="Geofabrik", theme="osm", series="pbf",
            place=p.get("name"), place_code=rid,
            year=int(date[:4]) if date else None, date=date, layer=l,
            resolution=None, format="GeoPackage layer from OSM .pbf",
            crs="EPSG:4326", size_mb=_mb(n),
            size_is="shared" if n else "unknown",
            file=f"{_safe_id(rid)}_{_stamp(date)}_{l}.gpkg", url=url,
            inside=PBF_RULES[l], md5_url=url + ".md5",
            licence=GF_LICENCE, citation=GF_CITATION, doi=None,
            source_page=_page(p.get("urls") or {}), record_id=rid,
            note=note))
    return out


def browse(provider, **kw):
    """One entry for both: browse("worldpop", theme=..., places=...)."""
    p = str(provider).strip().lower()
    if p == "worldpop":
        return browse_worldpop(**kw)
    if p in ("geofabrik", "osm", "openstreetmap"):
        return browse_geofabrik(**kw)
    raise FetchError(f"No catalogue for {provider!r}: worldpop or "
                     "geofabrik.")


def stamp_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
