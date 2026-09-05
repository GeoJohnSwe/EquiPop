# Machine 5 — the next providers

What is known about each, and what is still missing. Written down
because the WorldPop adapter's published documentation turned out to
be four years stale, and building from memory of a web page is how
that happens.

Order is by effort and risk, not by how interesting the data is.

---

## 1. GHSL — Global Human Settlement Layer (JRC)

**Read from the datasets page, 2 Sep 2026.**

**No API.** The website offers `download.php?ds=pop` links, but there
is a machine-readable tree behind it:

```
https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/
    GHS_{PRODUCT}_{COVERAGE}_{RELEASE}/
        GHS_{PRODUCT}_{COVERAGE}_{RELEASE}_{CRS}_{RES}/
            V{n}-{m}/
```

Seen in the wild: `GHS_AGE_GLOBE_R2025A/`,
`GHS_BUILT_S1NODSM_GLOBE_R2018A/GHS_BUILT_S1NODSM_GLOBE_R2018A_3857_20/V1-0/`,
`GHS_OBAT_GLOBE_R2024A/`.

**Fields the adapter would declare:** product, release, epoch,
resolution, crs. **No iso3** — GHSL is tiled globally, which is
exactly the case that forced the spine to be loosened (BACKLOG 256).

| product | epochs | resolutions | CRS |
|---|---|---|---|
| POP | 1975–2030, 5-yr | 100 m, 1 km, 3″, 30″ | Mollweide, **WGS84** |
| BUILT-S | 1975–2030 | 100 m, 1 km | Mollweide, **WGS84** |
| BUILT-V | 1975–2030 | 100 m, 1 km, 3″, 30″ | Mollweide, **WGS84** |
| BUILT-H | 2018 | 100 m, 3″ | Mollweide, WGS84 |
| SMOD | 1975–2030 | 1 km | Mollweide only |
| LAND | 2018 | 10 m, 100 m, 1 km | Mollweide only |
| AGE | 1975–2020 | 100 m, 1 km | Mollweide only |

### ⚠️ The thing that matters most for EquiPop

**Most GHSL products default to Mollweide (ESRI:54009). WorldPop is
WGS84.** Put both in one folder and the loader will refuse them —
correctly, because BACKLOG 239 exists precisely to stop rasters from
different worlds being merged.

**But POP, BUILT-S and BUILT-V are also published in WGS84 at 3 and
30 arc-seconds — the same grid family as WorldPop.** So GHSL and
WorldPop can share a folder, *provided the WGS84 variants are chosen*.
Whether the origins actually align is a measurement nobody has made;
it should be checked before the two are combined, and the aliasing
warning from BACKLOG 225 will speak up if the spacings disagree.

**The adapter should therefore default to WGS84 and say why.**

**Licence:** "© European Union, 1995-2025. Reuse of this data is
authorised with proper acknowledgment of the source." Permissive,
attribution required, no share-alike.

**Provenance:** every product carries a DOI and a full citation on the
datasets page. There is no API to ask, so these must be written into
the adapter — which means they can go stale, and the release string
should be recorded so a reader can check.

**Still needed:** one directory listing from
`jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/` so the exact folder
and file naming is confirmed rather than inferred.

---

## 2. HDX — Humanitarian Data Exchange

**BUILT AND CONFIRMED** against a real `package_search` response for
Sweden, 2 Sep 2026 (98 datasets). It is a CODE adapter, not a registry
entry: a search must be issued and a dataset chosen, so it cannot be
named from the user's choices alone.

**Every resource carries an MD5 in `hash`.** Like Geofabrik, a
download can be checked against **what the publisher says the file
is**, not merely against the bytes that arrived. Two of the three
providers now offer this; WorldPop does not.

### ⚠️ AND IT BROKE AN ASSUMPTION WRITTEN HERE

This file said the manifest would record *may it be redistributed* and
*does it impose share-alike*. **For HDX that is frequently
unknowable.** The IATI dataset returns `license_id` `"hdx-other"`,
`license_title` `"Other"`, and prose pointing at a web page.

So those fields are `None` when the licence cannot be resolved, the
prose is carried verbatim for a human, and the run **says so out
loud** before anything is fetched. *Guessing "probably CC-BY" would
have been worse than admitting ignorance* — and would have been
exactly the kind of plausible wrong answer this project keeps
finding.

---

## 3. Geofabrik — OSM extracts

**Structure confirmed from Geofabrik's own technical page.**

`https://download.geofabrik.de/index-v1.json`, or
`index-v1-nogeom.json` for a smaller file without boundary geometries.
A GeoJSON FeatureCollection, roughly 500 regions, each feature
carrying:

- `id` — unique, may contain `-` and `/`
- `parent` — the next larger extract, if any
- `name` — usually English long form
- `iso3166-1:alpha2` — **an array** of two-letter codes
- `urls` — one per format
- `level` — 1 continent, 2 country, 3 subregion, 4 sub-subregion

`parent` and `level` give exactly the continent → country → region
picker John asked for, and downloading from any level is natural
because every level is a first-class entry.

**Confirmed against the real index, 2 Sep 2026** (John supplied all
700 pages of it):

- properties: `id`, `parent`, `name`, `urls`, `iso3166-1:alpha2`,
  `iso3166-2`
- `urls` keys: **`pbf`, `shp`**, `pbf-internal`, `history`, `taginfo`,
  `updates`

### ⚠️ TWO CORRECTIONS TO WHAT WAS WRITTEN HERE YESTERDAY

**There is no `gpkg` in the index.** A search snippet listed
`.gpkg.zip` among Geofabrik's formats and this file repeated it. The
actual index offers **`pbf` and `shp`** only. So the no-new-dependency
route is the **shapefile zip**, not a GeoPackage — QGIS and GDAL read
shapefiles natively, so that route still stands, but for a different
reason than the one written here first. *Documentation described the
data; the data disagreed. Again.*

**`iso3166-1:alpha2` contains `"NA"` — Namibia.** Anything that reads
this index with pandas will turn that into NaN and Namibia will
silently vanish. `keep_default_na=False`, or do not use pandas for it.
A country disappearing from a country list is exactly the kind of
fault this project keeps finding: plausible output, nothing raised.

**Better than our own checksum:** Geofabrik publishes `.md5` sidecars,
so a fetch can be verified against **what the publisher says the file
is**, not merely against what we happened to receive. That is stronger
provenance than anything else on this list and the adapter should use
it.

**Licence: ODbL.** Attribution plus **share-alike on derived
databases**. This is the only source here with a share-alike
obligation, and it is the reason the manifest needs the two extra
fields (may redistribute / imposes share-alike) before this adapter
lands, not after.

**And fetching is only half the job.** EquiPop cannot read `.osm.pbf`
— the `osm` in `fastcounts.py` is the local variable for *overshoot
mode*, an unfortunate coincidence. Either a reader (`pyrosm`,
`pyosmium`) becomes a dependency, or the `.gpkg.zip` format is fetched
instead and the lattice join does the rest. **The second needs no new
dependency and should be tried first.**

**Still needed:** one feature from `index-v1-nogeom.json` — the first
twenty lines are enough — to confirm the `urls` key names.

---

## 4. EOG nightlights (Earth Observation Group)

Annual VIIRS composites, versioned and citable. **Believed to require
a free account**, which has not been confirmed. Check before planning
around it, because a login is the thing John specifically wanted to
avoid.

## 5. Copernicus — derived products

The Land Monitoring Service requires registration, so John's concern
about logins applies here too. GHSL is Copernicus-adjacent and needs
none, which is another reason it goes first.

## 6. Overture Maps

**Not a file download**, and this is the one that will surprise
anyone planning it. There is no per-country extract: it is global
GeoParquet on cloud storage, and the intended access is a spatial
query reading byte ranges over the network, typically through DuckDB.

That produces no artefact to checksum unless we define one — probably
"the query result, saved, with the release version recorded". Doable,
different from everything else here, and best attempted last when the
contract has settled.

---

## Two things to do before adapter number two

1. **The manifest needs licence obligations, not just a licence
   string.** Two fields: may it be redistributed, and does it impose
   share-alike on derived work. ODbL, CC-BY and "you may not retain
   this" impose very different duties on a published derived surface,
   and EquiPop exists to produce published derived surfaces.

2. **The QGIS door still has five fixed boxes matching WorldPop.**
   Building generic boxes now, for providers that do not exist yet,
   would be the same mistake as the naming registry written from four
   files. It waits for a second real adapter.
