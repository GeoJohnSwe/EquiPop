"""
fetchrows.py - MACHINE 5, second half: fetch THE ROWS YOU SELECTED.

BACKLOG 414, v1.58.0. The catalogue (catalogue.py) lists what exists,
one row per downloadable thing. This takes any of those rows - the
ones selected in QGIS, a filtered list in Python, or a recipe CSV
saved by an earlier fetch - and downloads exactly them. The standing
rule of machine 5 is unchanged: DOWNLOAD INTO A FOLDER, WRITE A
MANIFEST, STOP. Every download still goes through run_fetch, so the
refusals that took a dozen releases to get right - never overwrite,
check the publisher's checksum, record what arrived before the next
file starts - apply here without being written twice.

THREE KINDS OF ROW:

  WorldPop GeoTIFF     one file, downloaded as it is.

  Geofabrik shapefile  ONE LAYER OUT OF THE ZIP. The zip's table of
  layer               contents is read from its end (two requests),
                      and only that layer's five files are fetched,
                      each as one range of the zip - Sweden's buildings
                      are 329 MB of a 1.87 GB zip. Each is checked
                      against the CRC-32 the zip itself records, which
                      is the publisher's checksum for that file.

  Geofabrik .pbf       the whole-region .osm.pbf, ONCE however many
  layer               layers are taken from it, checked against its
                      .md5; then each layer is written to its own
                      GeoPackage by GDAL's OSM driver with the rule in
                      the row's `inside` column. The GeoPackage is
                      recorded in the manifest as DERIVED from the .pbf,
                      with the rule, so what was taken is on record.

AND IT LEAVES A RECIPE: equipop_recipe.csv, the rows that were
fetched, in the catalogue's own columns. Load it in QGIS and fetch it
again, or give it to a colleague.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import zlib

from .catalogue import (COLUMN_NAMES, Net, NetError, Truncated, check_url,
                        coerce_row,
                        date_of, layers_in_zip, parse_rule,
                        read_csv, size_of, total_mb, validator_of,
                        write_csv, zip_contents, _safe_id, _stamp)
from .fetching import (MANIFEST, RECIPE, FetchError, read_manifest,
                       run_fetch, sha256_of, url_filename)

PROVIDERS = ("WorldPop", "Geofabrik")


# ------------------------------------------------------- the transport
def download(net, url, dest):
    """Stream a whole file to `dest`. (bytes, sha256, md5).

    The same promises as fetching._get_file - the declared length is
    checked and nothing partial is left - but through the Net, so the
    tests can serve it, and TRIED AGAIN FROM THE START when the
    connection drops, stalls or is cut part-way (v1.58.1: WorldPop
    dropped John's first live download, on a morning when every request
    there took ten seconds). A file whose bytes are wrong is never
    tried again; only one whose connection failed."""
    tmp = dest + ".part"

    def once():
        sha, md5, n = (hashlib.sha256(), hashlib.md5(usedforsecurity=False),
                       0)
        with net.open(url) as r, open(tmp, "wb") as f:
            declared = size_of(Net._headers(r))
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                sha.update(b)
                md5.update(b)
                f.write(b)
                n += len(b)
        if declared is not None and n != declared:
            raise Truncated(
                f"{os.path.basename(dest)} is INCOMPLETE: the server "
                f"declared {declared:,} bytes and {n:,} arrived.")
        return n, sha.hexdigest(), md5.hexdigest()
    try:
        got = net.attempt(url, once)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    os.replace(tmp, dest)
    return got


def extract_member(net, zip_url, info, validator, dest):
    """ONE FILE OUT OF A REMOTE ZIP, as one range request.

    The local header says where the data starts; the central directory
    (already read) says how long it is, how it is packed, and its
    CRC-32. The If-Range validator means a zip replaced on the server
    since its contents were read answers with the whole file instead
    of the range - refused here - rather than with bytes of a
    different zip at the old offsets. A connection that drops or is cut
    is tried again from the member's first byte; a replaced zip, a
    damaged stream or a wrong CRC never is."""
    if info.compress_type not in (zipfile_STORED, zipfile_DEFLATED):
        raise FetchError(
            f"{info.filename} is packed with method {info.compress_type}, "
            "which EquiPop does not unpack. Fetch the whole zip instead.")
    head = net.get_range(zip_url, info.header_offset,
                         info.header_offset + 29, validator)
    if head[:4] != b"PK\x03\x04":
        raise FetchError(f"{info.filename}: the zip has no file where its "
                         "table of contents says one starts.")
    n_name, n_extra = struct.unpack("<HH", head[26:30])
    start = info.header_offset + 30 + n_name + n_extra
    tmp = dest + ".part"

    def once():
        sha, md5 = hashlib.sha256(), hashlib.md5(usedforsecurity=False)
        crc, total, got = 0, 0, 0
        dec = zlib.decompressobj(-15) if info.compress_type else None
        with open(tmp, "wb") as f:
            def put(data):
                nonlocal crc, total
                if data:
                    f.write(data)
                    sha.update(data)
                    md5.update(data)
                    crc = zlib.crc32(data, crc)
                    total += len(data)
            if info.compress_size:
                hdr = {"Range": f"bytes={start}-"
                                f"{start + info.compress_size - 1}"}
                if validator:
                    hdr["If-Range"] = validator
                with net.open(zip_url, headers=hdr) as r:
                    st = getattr(r, "status", 200)
                    if st != 206:
                        raise NetError(
                            f"{url_filename(zip_url)} did not send part of "
                            f"itself (status {st}) - it has most likely "
                            "been REPLACED on the server since its contents "
                            "were read. Run the fetch again.")
                    try:
                        while True:
                            b = r.read(1 << 20)
                            if not b:
                                break
                            got += len(b)
                            put(dec.decompress(b) if dec else b)
                        if dec:
                            put(dec.flush())
                    except zlib.error as e:
                        raise FetchError(
                            f"{info.filename} arrived DAMAGED - it could "
                            f"not be unpacked ({e}). Nothing was kept - "
                            "try again.") from e
            if got != info.compress_size:
                raise Truncated(
                    f"{info.filename} is INCOMPLETE: {got:,} of "
                    f"{info.compress_size:,} packed bytes arrived.")
            if total != info.file_size or (crc & 0xFFFFFFFF) != info.CRC:
                raise FetchError(
                    f"{info.filename} DOES NOT MATCH the zip's own record "
                    f"of it (CRC-32 {info.CRC:08x}, {info.file_size:,} "
                    f"bytes; arrived {crc & 0xFFFFFFFF:08x}, {total:,} "
                    "bytes). Nothing was kept - try again.")
        return (total, sha.hexdigest(), md5.hexdigest(),
                "verified against the zip's own CRC-32")
    try:
        got = net.attempt(zip_url, once)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    os.replace(tmp, dest)
    return got


zipfile_STORED, zipfile_DEFLATED = 0, 8


# ---------------------------------------------------- .pbf -> GeoPackage
class GdalConverter:
    """GDAL's own Python bindings - always present in QGIS."""

    def __init__(self, gdal):
        self.gdal = gdal
        self.name = f"GDAL {gdal.__version__} (osgeo)"

    def convert(self, src, osm_layer, where, out, layer):
        gdal = self.gdal
        gdal.UseExceptions()
        opts = gdal.VectorTranslateOptions(
            format="GPKG", layers=[osm_layer], where=where,
            layerName=layer)
        ds = gdal.VectorTranslate(out, src, options=opts)
        if ds is None:                              # pragma: no cover
            raise FetchError(f"GDAL could not write {out}")
        ds = None                                   # closes and flushes
        v = gdal.OpenEx(out, gdal.OF_VECTOR)
        n = v.GetLayer(0).GetFeatureCount()
        v = None
        return int(n)


class PyogrioConverter:
    """pyogrio, which reads the same driver - for Python without QGIS."""

    def __init__(self):
        import pyogrio
        self.name = (f"pyogrio {pyogrio.__version__} / GDAL "
                     f"{pyogrio.__gdal_version_string__}")

    def convert(self, src, osm_layer, where, out, layer):
        import pyogrio.raw as raw
        meta, _fids, geom, fields = raw.read(src, layer=osm_layer,
                                             where=where)
        raw.write(out, geom, fields, meta["fields"], layer=layer,
                  driver="GPKG", geometry_type=meta["geometry_type"],
                  crs=meta["crs"])
        return int(len(geom))


def find_converter():
    """GDAL from osgeo (QGIS), else pyogrio with the OSM driver, else
    None - and None is refused BEFORE anything is downloaded."""
    try:
        from osgeo import gdal                       # noqa: F401
        if gdal.GetDriverByName("OSM") is not None:
            return GdalConverter(gdal)
    except Exception:
        pass
    try:
        import pyogrio
        if "OSM" in pyogrio.list_drivers():
            return PyogrioConverter()
    except Exception:
        pass
    return None


# ------------------------------------------------------------ the rows
def _plain_name(name):
    n = str(name or "")
    if (not n or n != os.path.basename(n) or "\\" in n or n.startswith(".")
            or n in (MANIFEST, RECIPE)):
        raise FetchError(f"{name!r} is not a plain file name, so a row "
                         "cannot be saved under it.")
    return n


def check_rows(rows):
    """Every row a row this module can fetch - refused, all at once,
    before anything is downloaded."""
    if not rows:
        raise FetchError(
            "No rows to fetch. Select rows in the catalogue table first - "
            "or untick 'Selected features only' to take them all.")
    problems = []
    for i, r in enumerate(rows, 1):
        try:
            if r.get("provider") not in PROVIDERS:
                raise FetchError(f"provider {r.get('provider')!r} is not "
                                 f"one of {', '.join(PROVIDERS)}")
            check_url(r.get("url"))
            _plain_name(r.get("file"))
            if r["provider"] == "Geofabrik":
                if r.get("series") not in ("shapefile", "pbf"):
                    raise FetchError(f"series {r.get('series')!r}")
                if r["series"] == "pbf":
                    parse_rule(r.get("inside"))
                    if not str(r["file"]).endswith(".gpkg"):
                        raise FetchError("a .pbf layer is written to a "
                                         ".gpkg")
                elif not r.get("layer"):
                    raise FetchError("no layer named")
        except FetchError as e:
            problems.append(f"  row {i} ({r.get('file')}): {e}")
    if problems:
        raise FetchError("These rows cannot be fetched:\n"
                         + "\n".join(problems[:20])
                         + (f"\n  ... and {len(problems) - 20} more"
                            if len(problems) > 20 else ""))
    # ONE NAME, ONE THING
    by_file = {}
    for r in rows:
        by_file.setdefault(r["file"], set()).add((r["url"], r.get("inside")))
    clash = sorted(f for f, s in by_file.items() if len(s) > 1)
    if clash:
        raise FetchError(
            "Two different rows would be saved as the same file: "
            + ", ".join(clash[:5]) + ". Fetch them into separate folders.")


def _provenance(r):
    keep = ("provider", "theme", "series", "place", "place_code", "year",
            "date", "layer", "sex", "age_from", "age_to", "resolution",
            "licence", "citation", "doi", "source_page", "record_id")
    return {k: r.get(k) for k in keep if r.get(k) is not None}


def _relabel(r, date, say, told):
    """A 'latest' extract replaced since the catalogue was made: the
    new one is what is there, so it is what is fetched - under names
    that carry ITS date, and said once per region."""
    if not date or date == r.get("date"):
        return r
    key = (r["place_code"], r.get("date"), date)
    if key not in told:
        told.add(key)
        say(f"[fetch] Geofabrik has updated {r.get('place')} since the "
            f"catalogue was made ({r.get('date')} -> {date}). The {date} "
            "extract is what is there now, so it is what is fetched, and "
            "the file names carry its date.")
    old = _stamp(r.get("date"))
    r = dict(r)
    r["file"] = r["file"].replace(f"_{old}_", f"_{_stamp(date)}_", 1) \
        if old else r["file"]
    r["date"], r["year"] = date, int(date[:4])
    return r


def fetch_rows(rows, folder, *, net=None, say=print, keep_pbf=True,
               max_mb=None, converter=None):
    """Download these catalogue rows into `folder`.

    rows      catalogue rows (dicts, or anything with those keys)
    keep_pbf  keep the .osm.pbf after its layers are written out. On by
              default: it is the publisher's file, checked against its
              .md5, and every layer can be taken from it again.
    max_mb    refuse, before downloading, a selection larger than this
    converter for .pbf rows; found automatically (find_converter)

    Returns {"manifest", "downloaded", "derived", "recipe"}.
    """
    net = net or Net()
    net.say = say
    rows = [coerce_row(r) for r in rows]
    check_rows(rows)
    # the same row twice - two catalogues stacked - is one row
    seen, unique = set(), []
    for r in rows:
        k = (r["url"], r.get("inside"), r["file"])
        if k not in seen:
            seen.add(k)
            unique.append(r)
    if len(unique) < len(rows):
        say(f"[fetch] {len(rows) - len(unique)} row(s) appeared twice and "
            "are fetched once.")
    rows = unique

    mb, n_dl, est = total_mb(rows)
    say(f"[fetch] {len(rows)} row(s): {n_dl} download(s), "
        f"{'about ' if est else ''}{mb:,.1f} MB.")
    if max_mb and mb > float(max_mb):
        raise FetchError(
            f"That is {mb:,.0f} MB, above the limit of {float(max_mb):,.0f} "
            "MB set for this fetch. Select fewer rows, or raise the limit "
            "if you mean it. Nothing was downloaded.")

    for lic in sorted({str(r.get("licence")) for r in rows
                       if r.get("licence")}):
        say(f"[fetch] licence: {lic}")

    pbf_rows = [r for r in rows if r["provider"] == "Geofabrik"
                and r["series"] == "pbf"]
    if pbf_rows:
        converter = converter or find_converter()
        if converter is None:
            raise FetchError(
                f"{len(pbf_rows)} row(s) are layers of an OSM .pbf, which "
                "must be written out with GDAL's OSM driver - and neither "
                "GDAL's Python bindings (QGIS has them) nor pyogrio is "
                "here. Run this from QGIS, or install pyogrio. Nothing was "
                "downloaded.")
    os.makedirs(folder, exist_ok=True)

    entries, members, told = [], {}, set()
    fetched_rows = []

    # --- WorldPop: one file each
    for r in rows:
        if r["provider"] == "WorldPop":
            entries.append({"url": r["url"], "name": r["file"],
                            **_provenance(r)})
            fetched_rows.append(r)

    # --- Geofabrik shapefile layers: members of a remote zip
    shp = {}
    for r in rows:
        if r["provider"] == "Geofabrik" and r["series"] == "shapefile":
            shp.setdefault(r["url"], []).append(r)
    for url, group in shp.items():
        st, h = net.head(url)
        if st != 200 or not size_of(h):
            raise FetchError(f"{url_filename(url)} answered {st}. Browse "
                             "again - the catalogue may be out of date.")
        date, val = date_of(h), validator_of(h)
        infos = zip_contents(net, url, size_of(h), val)
        by_name = {i.filename: i for i in infos}
        layers = layers_in_zip(infos)
        for r in group:
            r = _relabel(r, date, say, told)
            d = layers.get(r["layer"])
            if not d:
                raise FetchError(
                    f"{r['place']}'s shapefile zip of {date} has no "
                    f"{r['layer']} layer now. Browse again.")
            stem = os.path.splitext(r["file"])[0]
            for m in d["members"]:
                info = by_name[m]
                base = os.path.basename(m)
                ext = base.rsplit(".", 1)[-1]
                part = base.rsplit("_free_", 1)[1].split(".")[0]
                name = (f"{stem}_{part}.{ext}" if len(d["parts"]) > 1
                        else f"{stem}.{ext}")
                eu = f"{url}#{m}"
                members[eu] = (url, info, val)
                entries.append({"url": eu, "name": name,
                                "bytes_expected": info.file_size,
                                "zip": url, "member": m,
                                "zip_date": date, **_provenance(r)})
            fetched_rows.append(r)

    # --- Geofabrik .pbf: one download per region and date
    pbf = {}
    for r in pbf_rows:
        pbf.setdefault(r["url"], []).append(r)
    prior = read_manifest(folder) or {}
    known = {f["name"]: f for f in prior.get("files", [])}
    jobs = []                                  # (pbf name, url, rows)
    for url, group in pbf.items():
        st, h = net.head(url)
        if st != 200:
            raise FetchError(f"{url_filename(url)} answered {st}. Browse "
                             "again - the catalogue may be out of date.")
        if url.endswith("-latest.osm.pbf"):
            date = date_of(h)
            group = [_relabel(r, date, say, told) for r in group]
            # A 'latest' file changes every day under one name; saved
            # under it, tomorrow's fetch would meet today's file and
            # take it for the same thing.
            name = url_filename(url).replace(
                "-latest.", f"-{_stamp(date)[2:]}.")
        else:
            name = url_filename(url)
        fetched_rows += group
        todo = [r for r in group if not _have(folder, known, r["file"])]
        # REFUSED HERE, NOT AFTER THE DOWNLOAD: a GeoPackage already in
        # the folder that this fetch did not make (or that has changed)
        # would stop the run only once a multi-gigabyte .pbf had come.
        foreign = [r["file"] for r in todo
                   if os.path.exists(os.path.join(folder, r["file"]))]
        if foreign:
            raise FetchError(
                f"{', '.join(foreign)} already in {folder}, and not the "
                "file this fetch would make (it is not recorded, or it "
                "has changed since). Refusing to overwrite - move it "
                "aside. Nothing was downloaded.")
        if not todo:
            say(f"[fetch] every layer wanted from {name} is already here "
                "and unchanged - not downloaded again.")
            continue
        entries.append({"url": url, "name": name, "md5_url": url + ".md5",
                        **{k: v for k, v in _provenance(group[0]).items()
                           if k not in ("layer",)}})
        jobs.append((name, url, todo))

    def get_file(url, dest):
        if url in members:
            zurl, info, val = members[url]
            return extract_member(net, zurl, info, val, dest)
        return download(net, url, dest)

    providers = sorted({r["provider"] for r in rows})
    man = None
    if entries:
        plan = {"provider": "+".join(providers), "entries": entries,
                "planned_utc": "", "from": "catalogue rows"}
        man = run_fetch(plan, folder, get_file=get_file,
                        get_text=lambda u: _get_text(net, u), say=say)

    derived = []
    for name, url, todo in jobs:
        src = os.path.join(folder, name)
        for r in todo:
            d = _write_layer(src, name, url, r, folder, converter, say)
            # RECORDED AS SOON AS IT EXISTS, like every download: a
            # failure on the third layer must not leave the first two
            # on disk with no record of where they came from.
            _record(folder, [d])
            derived.append(d)
        if not keep_pbf:
            os.remove(src)
            _mark_removed(folder, name)
            say(f"[fetch] {name} removed after its layers were written, as "
                "asked; the manifest says so.")

    recipe = _write_recipe(folder, fetched_rows)
    say(f"[fetch] Recipe: {RECIPE} - the rows fetched, in the catalogue's "
        "columns. Fetch it again to repeat this selection (a 'latest' "
        "extract will then be that day's).")
    # John, 16 Oct: 5 and 6 do different jobs - 5c records where each
    # file came from, 6 reports what the files hold - and the natural
    # order is 5c, then 6, then machine 3. Say so where 5c ends.
    say("[fetch] Next: tool 6 (What is in this folder?) lists what the "
        "folder now holds - layers, fields, projections, and which "
        "rasters share a grid.")
    return {"manifest": read_manifest(folder) or man,
            "downloaded": [e["name"] for e in entries],
            "derived": [d["name"] for d in derived], "recipe": recipe}


def _get_text(net, url):
    return net.get_text(url)


def _have(folder, known, name):
    """A derived file already here AND unchanged since it was made."""
    p = os.path.join(folder, name)
    rec = known.get(name)
    return bool(rec and os.path.exists(p) and rec.get("sha256")
                and sha256_of(p) == rec["sha256"])


def _write_layer(src, src_name, url, r, folder, converter, say):
    out = os.path.join(folder, r["file"])
    if os.path.exists(out):
        raise FetchError(
            f"{r['file']} is already in {folder}, and is not the one this "
            "fetch would make (it is not recorded, or it has changed). "
            "Refusing to overwrite it - move it aside.")
    osm_layer, where = parse_rule(r["inside"])
    tmp = out[:-len(".gpkg")] + ".partial.gpkg"
    if os.path.exists(tmp):
        os.remove(tmp)
    try:
        n = converter.convert(src, osm_layer, where, tmp, r["layer"])
        os.replace(tmp, out)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    say(f"[fetch] {r['file']}: {n:,} features, {r['layer']} from {src_name}")
    if n == 0:
        say(f"[fetch]   NO {r['layer']} at all in {r['place']} on "
            f"{r['date']} by the rule '{r['inside']}' - check the rule "
            "before reading this as an empty place.")
    return {"name": r["file"], "url": url, "derived_from": src_name,
            "rule": r["inside"], "features": n,
            "written_by": converter.name, "bytes": os.path.getsize(out),
            "sha256": sha256_of(out), "reused": False, **_provenance(r)}


def _save(folder, man):
    tmp = os.path.join(folder, MANIFEST + ".part")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(man, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, os.path.join(folder, MANIFEST))


def _record(folder, entries):
    """Derived files into the manifest, beside what they came from."""
    man = read_manifest(folder) or {"files": [], "fetches": []}
    names = {e["name"] for e in entries}
    man["files"] = [f for f in man.get("files", [])
                    if f["name"] not in names] + entries
    _save(folder, man)


def _mark_removed(folder, name):
    man = read_manifest(folder)
    for f in man.get("files", []):
        if f["name"] == name:
            f["removed"] = "after its layers were written, as asked"
    _save(folder, man)


def _write_recipe(folder, rows):
    path = os.path.join(folder, RECIPE)
    old = read_csv(path) if os.path.exists(path) else []
    out, seen = [], set()
    for r in rows + old:                     # newest first wins a clash
        k = (r["url"], r.get("inside"), r["file"])
        if k not in seen:
            seen.add(k)
            out.append(r)
    out.sort(key=lambda r: (r["provider"], str(r.get("place")),
                            r.get("year") or 0, r["file"]))
    write_csv(out, path)
    return path


def fetch_recipe(path, folder=None, **kw):
    """Fetch a recipe CSV again - into its own folder by default."""
    rows = read_csv(path)
    return fetch_rows(rows, folder or os.path.dirname(os.path.abspath(path)),
                      **kw)


__all__ = ["fetch_rows", "fetch_recipe", "find_converter", "check_rows",
           "extract_member", "download", "RECIPE", "COLUMN_NAMES"]
