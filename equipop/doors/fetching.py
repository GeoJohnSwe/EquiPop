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

    def projects(self, get_json=None):
        get_json = get_json or _get_json
        return {d["alias"]: d.get("name", "")
                for d in get_json(self.root)["data"]}

    def categories(self, project, get_json=None):
        get_json = get_json or _get_json
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

    def records(self, project, category, iso3, get_json=None):
        get_json = get_json or _get_json
        url = f"{self.root}/{project}/{category}?iso3={iso3}"
        return get_json(url).get("data", [])

    # WHAT THIS PROVIDER ASKS FOR, declared so the SPINE need not
    # know. BACKLOG 256: plan_fetch took project, category, iso3 and
    # year as fixed keyword arguments - WorldPop's shape, baked into
    # the machine. GHSL has no iso3 (it is tiled globally), Overture
    # has no year, HDX has neither. A rule shaped by one case and
    # discovered when the second arrives is this project's most
    # repeated mistake; this time it is loosened BEFORE.
    FIELDS = [
        {"name": "project", "label": "Dataset", "required": True},
        {"name": "category", "label": "Version of it", "required": False},
        {"name": "iso3", "label": "Countries (ISO3)", "required": True,
         "many": True,
         # A field may say how to ask for itself. The generic
         # "worldpop needs iso3" is correct and worse than the
         # sentence it replaced; moving a check up a layer must not
         # cost the user the better message.
         "missing": "Which country? Give one or more ISO3 codes, "
                    "such as BDI or ['BDI', 'RWA']."},
        {"name": "year", "label": "Year", "required": False,
         "kind": "int"},
    ]

    def plan(self, choices, get_json=None, say=print):
        """This provider's choices -> entries, and what to record.

        Everything WorldPop-specific lives here: the dataset, the
        version, the per-country lookup, the year filter, and the
        three refusals that took three rounds to get right.
        """
        get_json = get_json or _get_json
        provider = self.name
        project = choices.get("project")
        category = choices.get("category")
        year = choices.get("year")
        iso3 = choices.get("iso3")
        isos = [iso3] if isinstance(iso3, str) else list(iso3 or [])
        if not isos:
            raise FetchError(
                "Which country? Give one or more ISO3 codes, such as "
                "BDI or ['BDI', 'RWA'].")

        known = self.projects(get_json=get_json)
        project = resolve(project, known, "dataset")

        cats = self.categories(project, get_json=get_json)
        if category is None or category == "":
            if len(cats) == 1:
                category = next(iter(cats))
            else:
                raise FetchError(
                    f"{project!r} has {len(cats)} versions and they "
                    "are DIFFERENT DATASETS - constrained or not, "
                    "100 m or 1 km, different releases - so there is "
                    "no sensible default. Give the number or the "
                    "short name:\n" + "\n".join(numbered(cats)))
        category = resolve(category, cats, f"version of {project!r}")

        entries, missing, wrong_year = [], [], {}
        for iso in isos:
            recs = self.records(project, category, iso,
                                get_json=get_json)
            if not recs:
                missing.append(iso)
                continue
            if year is not None:
                keep = [r for r in recs
                        if str(r.get("popyear")) == str(year)]
                if not keep:
                    wrong_year[iso] = sorted(
                        {str(r.get("popyear")) for r in recs
                         if r.get("popyear")})
                    continue
                recs = keep
            for r in recs:
                entries.extend(self.entries(r))

        if missing:
            if not is_per_country(cats.get(category, "")):
                per = {k: v for k, v in cats.items()
                       if is_per_country(v)}
                raise FetchError(
                    f"{category} is a GLOBAL product - "
                    f"{cats.get(category, '')!r} - so it holds no "
                    f"single country and asking it for "
                    f"{', '.join(missing)} will never work. The "
                    f"per-country versions of {project!r} are:\n"
                    + "\n".join(numbered(per))
                    + "\nGive one of those in the version box.")
            raise FetchError(
                f"{provider} has nothing at all for "
                f"{', '.join(missing)} in {project}/{category}. Check "
                "the ISO3 code - it is the three-letter one, such as "
                "BDI.")
        if wrong_year:
            if not any(wrong_year.values()):
                raise FetchError(
                    f"The records in {project}/{category} carry NO "
                    "YEAR, so the year box cannot choose among them. "
                    "Clear it and run again. (Records were found for "
                    f"{', '.join(sorted(wrong_year))}.)")
            lines = [f"{provider} has nothing for {year} in "
                     f"{project}/{category}."]
            for iso, yrs in sorted(wrong_year.items()):
                lines.append(f"  {iso}: " + (", ".join(yrs) if yrs
                                             else "no year recorded"))
            lines.append("Put one of those in the year box, or leave "
                         "it empty to take them all.")
            raise FetchError("\n".join(lines))

        return entries, {"project": project, "category": category,
                         "iso3": isos, "year": year}

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

# ...plus every definition in providers/, which are DATA and can be
# corrected without a release (BACKLOG 258). Code adapters win a name
# clash: a JSON file must never silently replace tested logic.
try:                                                # pragma: no cover
    from .registry import load_registry
    for _name, _p in load_registry().items():
        PROVIDERS.setdefault(_name, _p)
except Exception:                                   # pragma: no cover
    # A broken registry must not stop the tool from starting, for the
    # same reason the QGIS plugin loads when equipop is absent.
    pass


# ------------------------------------------------------- ask, then act
def numbered(options):
    """The listing, numbered, with the alias in its own column.

    John typed `bic Individual countries` - the whole line - and was
    refused. Quite reasonable: "bic Individual countries" LOOKS like
    one string. The alias now stands in its own column, the line is
    numbered, and resolve() accepts the number, the alias, or the
    whole line pasted back.
    """
    keys = sorted(options)
    w = max((len(k) for k in keys), default=0)
    return [f"  {i:>2}  {k:<{w}}  {options[k]}"
            for i, k in enumerate(keys, 1)]


def resolve(value, options, what):
    """A number from the listing, an alias, or a whole pasted line."""
    keys = sorted(options)
    v = str(value).strip().lstrip("#").strip()
    # A NUMBER IS ONLY AN INDEX WHEN THE CHOICES ARE NOT THEMSELVES
    # NUMBERS. GHSL's epochs are years - 1975 to 2030 - and "2020" was
    # read as "the 2020th option", refused as out of range. If the
    # value IS one of the choices, it is the choice.
    if v in options:
        return v
    if v.isdigit():
        i = int(v)
        if 1 <= i <= len(keys):
            return keys[i - 1]
        raise FetchError(
            f"There is no {what} number {i}; there are {len(keys)}. "
            "Leave the box empty to see the list again.")
    if v in options:
        return v
    head = v.split()[0] if v.split() else ""
    if head in options:                 # the whole line, pasted back
        return head
    raise FetchError(
        f"No such {what}: {value!r}. Type its NUMBER, or the short "
        "name in the left column:\n" + "\n".join(numbered(options)))


def is_per_country(name):
    """Is this category a per-country product, by its own description?

    Some are GLOBAL MOSAICS or whole continents. Asking one of those
    for a single country returns nothing - and the refusal then blamed
    the ISO3 code, sending John to check a code that was correct. The
    catalogue says which is which in plain words, so read it.
    """
    low = str(name or "").lower()
    return not ("mosaic" in low or "whole continent" in low
                or "global" in low and "countries" not in low)


def plan_fetch(provider="worldpop", *, get_json=None, say=print,
               will_download=False, **choices):
    """Work out what WOULD be fetched. DOWNLOADS NOTHING.

    THE SPINE KNOWS NOTHING about datasets, countries or years. Each
    adapter declares FIELDS and turns its own choices into entries;
    what remains here is common to every provider - refusing an
    unknown one, checking the declared fields are present, and saying
    what would happen.

    This exists at all because the download leg has never been
    exercised in development - every provider host is blocked from the
    sandbox - so the first thing a user meets must be inspectable.
    """
    get_json = get_json or _get_json
    if provider not in PROVIDERS:
        raise FetchError(f"No such provider: {provider!r}. "
                         f"Available: {', '.join(sorted(PROVIDERS))}")
    p = PROVIDERS[provider]
    declared = list(getattr(p, "FIELDS", []))
    names = [f["name"] for f in declared]

    unknown = sorted(k for k in choices if k not in names)
    if unknown and declared:
        raise FetchError(
            f"{provider} does not take {', '.join(unknown)}. It asks "
            "for: " + ", ".join(names) + ".")
    for f in declared:
        # A FIELD WITH A DEFAULT IS NOT MISSING. The spine checked
        # `required` before the adapter had a chance to apply its own
        # defaults, so a definition that supplies one was refused for
        # not supplying it. Generalising a check must not overrule the
        # thing it was generalised for.
        # A FIELD THE ADAPTER CAN ANSWER FOR ITSELF is not the
        # spine's business. A default, a fixed option list, or
        # "lists_when_empty" - Geofabrik lists the continents when the
        # region box is blank, and the spine was refusing first with a
        # generic message, so the listing never ran. Third time a
        # generalised check has overruled the thing it generalised.
        if ("default" in f or f.get("options")
                or f.get("lists_when_empty")):
            continue
        v = choices.get(f["name"])
        if f.get("required") and (v is None or v == "" or v == []):
            raise FetchError(
                f.get("missing")
                or f"{provider} needs {f['name']} - {f['label']}.")

    entries, described = p.plan(choices, get_json=get_json, say=say)
    if not entries:
        raise FetchError("Nothing downloadable in those records.")

    plan = {"provider": provider, "entries": entries,
            "planned_utc": datetime.now(timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ")}
    plan.update(described or {})

    what = "/".join(str(described[k]) for k in ("project", "category")
                    if described.get(k))
    say(f"[fetch] {len(entries)} file(s) from {provider}"
        + (f", {what}" if what else ""))
    for e in entries[:5]:
        say(f"          {e['name']}")
    if len(entries) > 5:
        say(f"          ... and {len(entries) - 5} more")
    lic = {e.get("licence") for e in entries if e.get("licence")}
    if lic:
        say(f"[fetch] licence: {'; '.join(sorted(lic))}")
    if will_download:
        say("[fetch] Downloading now.")
    else:
        say("[fetch] NOTHING HAS BEEN DOWNLOADED. Pass this plan to "
            "run_fetch(plan, folder) to do that.")
    return plan


def run_fetch(plan, folder, *, get_file=None, say=print,
              skip_existing=True):
    """Download the planned files and write the manifest.

    REFUSES TO OVERWRITE (John's ruling). A file already present whose
    checksum matches is left alone and reported; one whose checksum
    DIFFERS stops the run and is named, because silently replacing it
    is how a reproducible result stops being reproducible.
    """
    get_file = get_file or _get_file          # late-bound, see above
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
        "provider": plan["provider"],
        "folder": os.path.abspath(folder),
        "files": files,
    }
    # WHATEVER THE ADAPTER CHOSE TO RECORD. This used to name
    # project, category, iso3 and year explicitly - WorldPop's
    # vocabulary, in the one function that should be common to every
    # provider. A provider with tiles and releases instead of
    # countries and years raised KeyError here, which is exactly what
    # the fake second provider was written to find (BACKLOG 256).
    for k, v in plan.items():
        if k not in ("entries", "provider", "planned_utc"):
            man.setdefault(k, v)
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


# ---------------------------------------------------- the HDX door
# A CKAN API, so it needs code rather than a registry entry: a search
# must be issued, results paged and a dataset chosen. The registry
# handles providers whose files can be NAMED from the user's choices;
# this one has to ask.
class HDX:
    """Humanitarian Data Exchange. Confirmed against a real
    package_search response for Sweden, 2 Sep 2026.

    TWO THINGS THAT RESPONSE SETTLED.

    FIRST, EVERY RESOURCE CARRIES AN MD5 IN `hash`. Like Geofabrik,
    that lets a download be checked against WHAT THE PUBLISHER SAYS
    THE FILE IS, not merely against the bytes that arrived. Two
    providers now offer this and WorldPop does not.

    SECOND, AND IT BREAKS AN ASSUMPTION: HDX LICENCES ARE OFTEN NOT
    MACHINE-READABLE. The IATI dataset returns license_id
    "hdx-other", license_title "Other" and a PROSE license_other
    pointing at a web page. So `may_redistribute` and `share_alike`
    CANNOT be derived for many HDX datasets, and guessing would be
    worse than admitting it. Where the licence is a known open one
    they are set; otherwise they are None and the prose is carried
    verbatim for a human to read.
    """

    name = "hdx"
    root = "https://data.humdata.org/api/3/action"

    # The ones whose obligations are unambiguous. Anything else is
    # recorded and left undecided ON PURPOSE.
    KNOWN = {
        "cc-by": (True, False), "cc-by-sa": (True, True),
        "cc-zero": (True, False), "cc-by-igo": (True, False),
        "odc-by": (True, False), "odc-odbl": (True, True),
        "odc-pddl": (True, False),
    }

    FIELDS = [
        {"name": "country", "label": "Country group, e.g. swe, bdi",
         "required": True,
         "missing": "Which country? HDX groups datasets by a "
                    "three-letter code in lower case, such as swe."},
        {"name": "dataset", "label": "Which dataset (blank lists them)",
         "required": False},
        {"name": "format", "label": "Only this format, e.g. CSV",
         "required": False},
    ]

    def search(self, country, rows=100, get_json=None):
        get_json = get_json or _get_json
        url = (f"{self.root}/package_search?fq=groups:{country}"
               f"&rows={int(rows)}")
        got = get_json(url)
        if not got.get("success"):
            raise FetchError(f"HDX refused the search for {country!r}.")
        return got["result"]["results"]

    def _obligations(self, pkg):
        lic = str(pkg.get("license_id") or "").lower()
        if lic in self.KNOWN:
            return self.KNOWN[lic]
        return (None, None)          # unknown, and said so

    def plan(self, choices, get_json=None, say=print):
        country = str(choices.get("country") or "").strip().lower()
        wanted = str(choices.get("dataset") or "").strip()
        only = str(choices.get("format") or "").strip().upper()

        found = self.search(country, get_json=get_json)
        if not found:
            raise FetchError(
                f"HDX has no datasets in group {country!r}. The group "
                "is a lower-case three-letter code, such as swe.")

        names = {p["name"]: p.get("title", "") for p in found}
        if not wanted:
            raise FetchError(
                f"HDX has {len(found)} datasets for {country!r}. Give "
                "the number or the short name of one:\n"
                + "\n".join(numbered(names)))
        wanted = resolve(wanted, names, f"dataset in {country!r}")
        pkg = next(p for p in found if p["name"] == wanted)

        redistribute, share_alike = self._obligations(pkg)
        entries = []
        for r in pkg.get("resources", []):
            if only and str(r.get("format", "")).upper() != only:
                continue
            url = r.get("url")
            if not url:
                continue
            entries.append({
                "url": url,
                "name": os.path.basename(url.split("?")[0]),
                "title": r.get("name"),
                "format": r.get("format"),
                "bytes_expected": r.get("size"),
                # THE PUBLISHER'S OWN CHECKSUM.
                "publisher_md5": r.get("hash") or None,
                "dataset": pkg["name"],
                "dataset_title": pkg.get("title"),
                "source": pkg.get("dataset_source"),
                "organisation": (pkg.get("organization") or {}).get("title"),
                "licence": pkg.get("license_title"),
                "licence_id": pkg.get("license_id"),
                "licence_note": pkg.get("license_other"),
                "may_redistribute": redistribute,
                "share_alike": share_alike,
                "updated": r.get("last_modified"),
            })
        if not entries:
            have = sorted({str(r.get("format")) for r
                           in pkg.get("resources", [])})
            raise FetchError(
                f"{wanted} has nothing in {only!r}. It offers: "
                + ", ".join(have) + ".")
        if redistribute is None:
            say(f"[fetch] LICENCE NOT MACHINE-READABLE: "
                f"{pkg.get('license_title')!r}. Read it before "
                "republishing anything derived from this. "
                + (str(pkg.get('license_other'))[:120] if
                   pkg.get("license_other") else ""))
        return entries, {"country": country, "dataset": wanted,
                         "format": only or None}


PROVIDERS["hdx"] = HDX()


# ------------------------------------------------ the Geofabrik door
class Geofabrik:
    """OpenStreetMap extracts. A CODE adapter: the region tree comes
    from an index that must be fetched and walked.

    Structure confirmed against the real index-v1.json - all 700
    pages of it, supplied by John, 2 Sep 2026. Properties are id,
    parent, name, urls, iso3166-1:alpha2, iso3166-2; urls keys are
    pbf, shp, pbf-internal, history, taginfo, updates.

    THERE IS NO gpkg, though a search snippet said there was. The
    no-new-dependency route is therefore the SHAPEFILE ZIP, which QGIS
    and GDAL read natively - the route survives, for a different
    reason than the one first written down.

    ODbL, AND IT IS THE FIRST SOURCE HERE WITH SHARE-ALIKE. Attribution
    plus a share-alike obligation on derived DATABASES. EquiPop exists
    to produce published derived surfaces, so this is said out loud
    before anything is fetched, every time.

    AND THE PUBLISHER STATES A CHECKSUM: every file has an .md5
    sidecar, so a download can be checked against what Geofabrik says
    it is.
    """

    name = "geofabrik"
    index_url = "https://download.geofabrik.de/index-v1-nogeom.json"

    FIELDS = [
        {"name": "region", "label": "Continent, country or region",
         "required": True, "lists_when_empty": True,
         "missing": "Which region? Leave it empty to list the "
                    "continents, then name any level - a continent, a "
                    "country, or a sub-region."},
        {"name": "format", "label": "pbf or shp", "required": False},
    ]

    def index(self, get_json=None):
        get_json = get_json or _get_json
        fc = get_json(self.index_url)
        out = {}
        for f in fc.get("features", []):
            p = f.get("properties") or {}
            if p.get("id"):
                out[p["id"]] = p
        if not out:
            raise FetchError(
                "Geofabrik's index came back empty. It is normally at "
                f"{self.index_url}")
        return out

    @staticmethod
    def _children(index, parent):
        return {k: v.get("name", "") for k, v in index.items()
                if v.get("parent") == parent}

    def plan(self, choices, get_json=None, say=print):
        region = str(choices.get("region") or "").strip()
        fmt = str(choices.get("format") or "pbf").strip().lower()
        index = self.index(get_json=get_json)

        if not region:
            roots = self._children(index, None)
            raise FetchError(
                "Which region? The continents are:\n"
                + "\n".join(numbered(roots))
                + "\nName one of those, or any country or sub-region "
                  "directly - 'sweden', 'burundi', 'act'. Every level "
                  "is downloadable.")

        if region not in index:
            near = {k: v.get("name", "") for k, v in index.items()
                    if region.lower() in k.lower()
                    or region.lower() in str(v.get("name", "")).lower()}
            if near:
                raise FetchError(
                    f"No region called {region!r}. Did you mean:\n"
                    + "\n".join(numbered(dict(sorted(near.items())[:20]))))
            raise FetchError(
                f"No region called {region!r}. Leave the box empty to "
                "list the continents and work down from there.")

        p = index[region]
        urls = p.get("urls") or {}
        if fmt not in urls:
            offered = sorted(k for k in urls
                             if k in ("pbf", "shp", "bz2"))
            raise FetchError(
                f"{region} is not published as {fmt!r}. It offers: "
                + ", ".join(offered)
                + ". 'pbf' is the OSM format and needs a reader; "
                  "'shp' is a shapefile zip that QGIS opens directly.")
        url = urls[fmt]

        kids = self._children(index, region)
        if kids:
            say(f"[fetch] {p.get('name')} has {len(kids)} sub-regions. "
                "This takes the WHOLE of it; name a sub-region instead "
                "if that is too much.")
        say("[fetch] ODbL: attribution, AND SHARE-ALIKE ON DERIVED "
            "DATABASES. A surface published from this data may carry "
            "the same obligation - check before publishing.")

        return ([{
            "url": url,
            "name": os.path.basename(url),
            # THE PUBLISHER'S OWN CHECKSUM, beside every file.
            "md5_url": url + ".md5",
            "region": region,
            "region_name": p.get("name"),
            "parent": p.get("parent"),
            "iso3166_1": p.get("iso3166-1:alpha2"),
            "format": fmt,
            "licence": "ODbL 1.0 (OpenStreetMap contributors)",
            "may_redistribute": True,
            "share_alike": True,
            "citation": "© OpenStreetMap contributors, "
                        "openstreetmap.org/copyright. Extract by "
                        "Geofabrik GmbH.",
        }], {"region": region, "format": fmt})


PROVIDERS["geofabrik"] = Geofabrik()
