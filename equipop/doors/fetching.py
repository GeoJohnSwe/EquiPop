"""
fetching.py - MACHINE 5: bring data in, write files, STOP.

THE STANDING RULE, HANDOVER 13 section 3c. Machines 1 to 4 give the
same answers offline, forever. A downloader cannot: the service may be
down, estimates get revised, the API changes on the provider's
schedule. Put a Download button inside an analysis tool and the whole
tool loses reproducibility.

So a fetcher DOWNLOADS INTO A FOLDER, WRITES A MANIFEST, AND ENDS.
Machine 3 then reads that folder exactly as it reads any other, and
machines 1, 2 and 4 never learn that WorldPop exists.

THE MANIFEST IS THE DELIVERABLE, NOT THE FILES. Without a product
version, a fetch date and a checksum, a downloaded raster is LESS
reproducible than one a colleague emailed. WorldPop's API returns doi,
citation and licence, so none of that is invented here - it is
recorded from what the provider states.

NOTHING IS OVERWRITTEN (John's ruling). A file already present whose
checksum differs stops the run and is named. A quiet overwrite is how
a reproducible run becomes unreproducible with nobody noticing.

NOT equipop/fetch.py. That is the original spec's single-URL helper -
give it a URL, get a local path, with caching. It stays as it is and
is still exported. This module is the other thing: resolve a REQUEST
against a provider's catalogue, fetch a SET, and record what happened.

THE PROVIDER IS A SMALL ADAPTER, so a second source is an adapter and
not a second machine - John's point that this pattern should bring
other web resources in.

    from equipop.doors.fetching import plan_fetch, run_fetch
    plan = plan_fetch("worldpop", project="age_structures",
                      iso3=["BDI"], year=2020)   # asks; downloads NOTHING
    run_fetch(plan, "rasters/BDI")               # this downloads
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

MANIFEST = "equipop_fetch.json"


class FetchError(Exception):
    """Refused, with the reason in plain words."""


# ------------------------------------------------------- the transport
# Separated so every test can replace it. The download leg is the one
# part that cannot be exercised in development - the sandbox blocks
# every WorldPop host - so it is kept to two tiny functions and
# everything else is testable.
def _get_json(url, timeout=60):                     # pragma: no cover
    import urllib.request
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _get_file(url, dest, timeout=900):              # pragma: no cover
    """Stream to disk. Returns (bytes, sha256). Never leaves a partial
    file at `dest`: it writes .part and renames only on success."""
    import urllib.request
    h, n, tmp = hashlib.sha256(), 0, dest + ".part"
    with urllib.request.urlopen(url, timeout=timeout) as r, \
            open(tmp, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            h.update(b)
            f.write(b)
            n += len(b)
    os.replace(tmp, dest)
    return n, h.hexdigest()


def sha256_of(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


# --------------------------------------------------- the WorldPop door
class WorldPop:
    """One adapter. Knows the catalogue; knows nothing about manifests.

    The REST shape, confirmed against the live API in August 2026 (the
    published documentation is from 2022 and is STALE - it lists four
    projects where there are eighteen, and shows ftp:// URLs where the
    API now returns https://data.worldpop.org).
    """

    name = "worldpop"
    root = "https://www.worldpop.org/rest/data"

    def projects(self, get_json=_get_json):
        return {d["alias"]: d.get("name", "")
                for d in get_json(self.root)["data"]}

    def categories(self, project, get_json=_get_json):
        """Selectable categories only.

        The catalogue contains entries with an EMPTY alias - John's
        run of `pop` listed one whose name is a bare DOI stub,
        WP00643, printed as a blank line. It cannot be chosen, so
        offering it is worse than a shorter list.
        """
        out = {}
        for d in get_json(f"{self.root}/{project}")["data"]:
            alias = str(d.get("alias") or "").strip()
            if alias:
                out[alias] = d.get("name", "")
        return out

    def records(self, project, category, iso3, get_json=_get_json):
        url = f"{self.root}/{project}/{category}?iso3={iso3}"
        return get_json(url).get("data", [])

    @staticmethod
    def entries(rec):
        """A catalogue record to one entry per downloadable file.

        Everything provenance-related is taken FROM THE RECORD. The
        API supplies doi, citation and licence, so the manifest states
        what WorldPop says rather than what EquiPop assumed.
        """
        out = []
        for url in rec.get("files") or []:
            if not str(url).lower().endswith((".tif", ".tiff", ".zip",
                                              ".csv", ".gz")):
                continue
            out.append({
                "url": url,
                "name": os.path.basename(url),
                "id": rec.get("id"),
                "iso3": rec.get("iso3"),
                "country": rec.get("country"),
                "year": rec.get("popyear"),
                "title": rec.get("title"),
                "doi": rec.get("doi"),
                "citation": rec.get("citation"),
                "licence": rec.get("license"),
                "category": rec.get("category"),
                "project": rec.get("project"),
                "published": rec.get("date"),
                "summary": rec.get("url_summary"),
            })
        return out


PROVIDERS = {"worldpop": WorldPop()}


# ------------------------------------------------------- ask, then act
def plan_fetch(provider="worldpop", *, project, iso3, year=None,
               category=None, get_json=_get_json, say=print,
               will_download=False):
    """Work out what WOULD be fetched. DOWNLOADS NOTHING.

    This exists because the download leg has never been exercised in
    development - every WorldPop host is blocked from the sandbox - so
    the first thing a user does must be safe and inspectable. Look at
    the list, then decide.
    """
    if provider not in PROVIDERS:
        raise FetchError(f"No such provider: {provider!r}. "
                         f"Available: {', '.join(sorted(PROVIDERS))}")
    p = PROVIDERS[provider]
    isos = [iso3] if isinstance(iso3, str) else list(iso3)
    if not isos:
        raise FetchError("Which country? Give one or more ISO3 codes, "
                         "such as BDI or ['BDI', 'RWA'].")

    known = p.projects(get_json=get_json)
    if project not in known:
        raise FetchError(
            f"No such dataset: {project!r}. {provider} offers: "
            + ", ".join(sorted(known)))

    cats = p.categories(project, get_json=get_json)
    if category is None:
        if len(cats) == 1:
            category = next(iter(cats))
        else:
            raise FetchError(
                f"{project!r} has {len(cats)} categories and they are "
                "different datasets, not different formats - choose "
                "one:\n  " + "\n  ".join(f"{k}  ({v})"
                                         for k, v in sorted(cats.items())))
    if category not in cats:
        raise FetchError(
            f"No such category {category!r} in {project!r}. "
            "Available:\n  " + "\n  ".join(f"{k}  ({v})"
                                           for k, v in sorted(cats.items())))

    entries, missing = [], []
    for iso in isos:
        recs = p.records(project, category, iso, get_json=get_json)
        if year is not None:
            recs = [r for r in recs if str(r.get("popyear")) == str(year)]
        if not recs:
            missing.append(iso)
            continue
        for r in recs:
            entries.extend(p.entries(r))
    if missing:
        raise FetchError(
            f"{provider} has nothing for {', '.join(missing)} in "
            f"{project}/{category}"
            + (f" for {year}" if year else "")
            + ". Check the ISO3 code and the year.")
    if not entries:
        raise FetchError("Nothing downloadable in those records.")

    plan = {"provider": provider, "project": project,
            "category": category, "iso3": isos, "year": year,
            "entries": entries,
            "planned_utc": datetime.now(timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ")}
    say(f"[fetch] {len(entries)} file(s) from {provider}, "
        f"{project}/{category}"
        + (f", {year}" if year else "")
        + f", for {', '.join(isos)}")
    for e in entries[:5]:
        say(f"          {e['name']}")
    if len(entries) > 5:
        say(f"          ... and {len(entries) - 5} more")
    lic = {e.get("licence") for e in entries if e.get("licence")}
    if lic:
        say(f"[fetch] licence: {'; '.join(sorted(lic))}")
    # BACKLOG 243. This used to say NOTHING HAS BEEN DOWNLOADED
    # unconditionally, so a --go run announced it would not download
    # and then downloaded on the next line. A tool that contradicts
    # itself in two consecutive lines teaches the reader to stop
    # reading it.
    if will_download:
        say("[fetch] Downloading now.")
    else:
        say("[fetch] NOTHING HAS BEEN DOWNLOADED. Pass this plan to "
            "run_fetch(plan, folder) to do that.")
    return plan


def run_fetch(plan, folder, *, get_file=_get_file, say=print,
              skip_existing=True):
    """Download the planned files and write the manifest.

    REFUSES TO OVERWRITE (John's ruling). A file already present whose
    checksum matches is left alone and reported; one whose checksum
    DIFFERS stops the run and is named, because silently replacing it
    is how a reproducible result stops being reproducible.
    """
    if not plan.get("entries"):
        raise FetchError("An empty plan. Call plan_fetch first.")
    os.makedirs(folder, exist_ok=True)

    prior = read_manifest(folder) or {}
    known = {f["name"]: f for f in prior.get("files", [])}

    files, fetched, kept = [], 0, 0
    for e in plan["entries"]:
        dest = os.path.join(folder, e["name"])
        if os.path.exists(dest):
            have = sha256_of(dest)
            was = known.get(e["name"], {}).get("sha256")
            if was and was != have:
                raise FetchError(
                    f"{e['name']} is already here but has CHANGED since "
                    "it was fetched - the manifest records "
                    f"{was[:16]}... and the file on disk is "
                    f"{have[:16]}.... Refusing to touch it. Move it "
                    "aside if you want a fresh copy; whatever you have "
                    "computed from it was computed from THIS file.")
            if skip_existing:
                kept += 1
                files.append({**{k: v for k, v in e.items() if k != "url"},
                              "url": e["url"],
                              "bytes": os.path.getsize(dest),
                              "sha256": have, "reused": True})
                continue
            raise FetchError(
                f"{e['name']} already exists in {folder}. Refusing to "
                "overwrite - move it aside, or fetch into a new folder.")
        n, h = get_file(e["url"], dest)
        fetched += 1
        files.append({**{k: v for k, v in e.items() if k != "url"},
                      "url": e["url"], "bytes": n, "sha256": h,
                      "reused": False})
        say(f"[fetch] {e['name']}  {n / 1e6:.1f} MB")

    from .. import __version__
    man = {
        "fetched_by": f"EquiPop {__version__}",
        "fetched_utc": datetime.now(timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": plan["provider"], "project": plan["project"],
        "category": plan["category"], "iso3": plan["iso3"],
        "year": plan["year"], "folder": os.path.abspath(folder),
        "files": files,
    }
    with open(os.path.join(folder, MANIFEST), "w", encoding="utf-8") as f:
        json.dump(man, f, indent=2, ensure_ascii=False)

    say(f"[fetch] {fetched} downloaded, {kept} already present, "
        f"{len(files)} recorded in {MANIFEST}.")
    say("[fetch] Done. Nothing has been analysed - point machine 3 at "
        "this folder when you want that.")
    return man


def read_manifest(folder):
    p = os.path.join(folder, MANIFEST)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def verify_folder(folder, say=print):
    """Do the files still match what was fetched?

    The point of recording a checksum. A year later this answers "is
    this the same data the paper used" without trusting a filename.
    """
    man = read_manifest(folder)
    if man is None:
        raise FetchError(
            f"No {MANIFEST} in {folder} - these files were not fetched "
            "by EquiPop, so there is nothing to check them against.")
    ok, changed, gone = 0, [], []
    for f in man["files"]:
        p = os.path.join(folder, f["name"])
        if not os.path.exists(p):
            gone.append(f["name"])
        elif sha256_of(p) != f["sha256"]:
            changed.append(f["name"])
        else:
            ok += 1
    say(f"[verify] {ok} unchanged, {len(changed)} CHANGED, "
        f"{len(gone)} missing, against a fetch of {man['fetched_utc']}")
    for n in changed + gone:
        say(f"           {n}")
    return {"ok": ok, "changed": changed, "missing": gone,
            "manifest": man}
