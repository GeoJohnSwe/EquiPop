# HANDOVER 14

### written after the machines 3–5 and provider sessions

**HANDOVER 12 §5 and HANDOVER 13 still hold and are not repeated.**
Read 13 first — the delivery rule and the network rule live there and
are still the operating agreement.

Where 13 ended at **1.41.0**, this ends at **1.44.9**: eighteen
releases, 998 tests, 57 backlog items closed and 12 still open.

---

## 1. WHAT EXISTS NOW THAT DID NOT

| | |
|---|---|
| **Machine 3** | Raster Data Curation — a folder of rasters to one point table |
| **Machine 4** | Spatial Demographic Analysis — indices over k-neighbourhoods |
| **Machine 5** | Fetch data — downloads, writes a manifest, and **stops** |
| **The registry** | `equipop/providers/*.json` — providers as DATA |
| **Providers** | worldpop, ghsl, hdx, geofabrik |
| **Doors** | all five machines in QGIS; 3 and 4 in ArcGIS Pro |

Machine 5 and the registry are the new architecture. Everything else
is an extension of what 13 described.

---

## 2. THE STANDING RULES ADDED, AND WHY

**Anything that touches the network produces files and stops**
(13 §3c, John's ruling). Machines 1–4 give the same answers offline,
forever; a downloader cannot. Machine 5 therefore produces **no
layer** — a test forbids it from even importing the engine.

**A provider definition is DATA and may never contain code.**
`_check_safe()` refuses `import`, `eval`, `lambda`, `os.` and the
rest, and the check runs over every **bundled** file, not only loaded
ones. EquiPop installs inside QGIS and ArcGIS Pro; a tool that
executed instructions fetched over the network would be a remote code
execution hole in a research instrument. **This is not negotiable and
should never be relaxed for convenience.**

**The manifest is the deliverable, not the files.** Product version,
fetch date, checksum, licence — and, since the registry, *which
registry version was in force*. Without those a downloaded raster is
less reproducible than one a colleague emailed.

**Nothing is overwritten.** A file present with a matching checksum is
reused; one whose checksum differs stops the run and is named, because
whatever was computed from it was computed from *that* file.

---

## 3. THE FOUR PATTERNS THAT REPEATED

These cost more time than any single defect. **Every one recurred
after being written down**, so writing them down is not sufficient —
they need tests that fire.

### 3.1 The simulator was kinder than the thing it simulates — 5 times

`tests/qgis_stub.py` accepted a bare int for a WKB type (221),
accepted and **discarded** the sink's CRS (223), lacked
`parameterAsEnum` entirely (231), returned `[]` for an empty matrix
(264), and returned `""` where PyQGIS returns **NULL**, whose `str()`
is the four characters `"NULL"` (265).

**Every one let a door ship broken with a green suite.** A simulator
more forgiving than reality does not merely fail to catch bugs — it
**actively certifies them**. When a door works under test and fails in
QGIS, suspect the stub first.

**Outstanding: a deliberate hardening pass** over every
`parameterAs*`, rather than one gap per round trip.

### 3.2 A generalisation overruled the thing it generalised — 4 times

The spine's `required` check fired before an adapter could apply its
own defaults (256); the number-picking convenience read `2020` as *the
2020th option* (250); the required check refused before Geofabrik
could list its continents (262); the shared matrix reader dropped
trailing blanks, which suits a two-column table and destroys a
three-column row (265).

**When a check moves up a layer, the layer below loses the ability to
answer for itself.** Fields may now carry `default`, `options`,
`lists_when_empty` and their own `missing` wording precisely so the
spine knows when to keep quiet.

### 3.3 A refusal blamed the wrong thing — 3 times

"Check the ISO3 code and the year" when the code was right (251); "the
years it does have:" followed by nothing, for a product with no years
(253); "check the ISO3 code" for a **global mosaic** that holds no
country at all (254).

**Each time the information needed to answer correctly was already in
hand and was not consulted.** If the code knows the right answer, a
refusal that only names the problem is a wasted trip.

### 3.4 A rule written from one sample — 3 times

The WorldPop naming registry, written from four files, failed on all
120 of John's (211). The documented default of 1000 m, sensible for
the rasters it was tested on, **striped a continent** on his (225).
`PROVIDER_NAMES = ["worldpop"]`, written when there was one provider,
showed one of four (263).

**A registry, a default and a threshold are the same mistake when they
come from one sample.** BACKLOG 258 — the external registry — exists
because of this pattern: volatile knowledge belongs in data that can
be corrected without a release.

---

## 4. THE TWO ENGINE DEFECTS WORTH REMEMBERING

**A crossing ring cut by the search window was treated as complete**
(207). `Dist_k` and every group share moved with a setting that
changes nothing else, while `N_k` stayed exactly k — so no guard could
see it. 249 of 46,317 origins moved by up to 168 m; a cross-border
share read 0.043 where the converged answer is 0.065.

**Rasters in different coordinate systems were merged silently**
(239). The lattice check compared pixel size and origin — pure numbers
that say nothing about which world they describe — and the manifest
then reported a single CRS, hiding the mixture. 30.0 in EPSG:4326 is a
longitude in Burundi; in EPSG:3857 it is thirty metres from
Greenwich.

Both were **silent**. Both produced plausible maps. That is this
project's signature fault and the reason for its testing discipline.

---

## 5. WHAT IS OPEN

**Correctness, watch first**
- **224** `N_1000` read 2000 once, in John's attribute table, and has
  not reproduced. Left open deliberately: an intermittent wrong `N` is
  worse than a repeatable one, and 225 was found in the same data.
- **232** "add all cohorts" gave NULLs; needs the log for that run.

**Ready to build**
- **257** the next adapters — EOG nightlights, Copernicus, Overture.
  `PROVIDERS_PLAN.md` has what is known and what is missing.
- **210** rasters from inside a zip: measured at 3.5× slower,
  byte-identical, and the cost does **not** amortise.
- **216** vital-event rasters — read the circularity note first.

**Deferred with reasons recorded**
- **219** no restriction on what may be a weight (John's ruling)
- **255** checking all settings at once — partly impossible, the
  checks are dependent
- **237** `ValFloat` is not float, next dataset regeneration
- **200, 203, 205** predate this session

**Not started**
- The Pro door for machine 5
- The `.osm.pbf` reader — try the shapefile route first, it needs no
  new dependency
- The command-line runner still speaks WorldPop's vocabulary

---

## 5b. HANDOVERS 9 AND 10 ARE STILL MISSING

The tree holds 6, 7, 8, 11, 12, 13 and this one. **9 and 10 have never
been in it** — HANDOVER 13 §"still John's to do" flagged them and they
are still absent, so two sessions of reasoning exist only in
downloads, if at all.

If John still has them, they belong in the repository root. If not,
they are gone, and the gap between 8 and 11 should be noted in this
file rather than left for someone to wonder about.

## 6. THINGS A FRESH SESSION WILL GET WRONG

**`equipop/fetch.py` is not machine 5.** It is the original spec's
single-URL helper. Machine 5 is `equipop/doors/fetching.py`.

**The `osm` in `fastcounts.py` is overshoot mode**, not
OpenStreetMap. EquiPop cannot read `.osm.pbf`.

**Provider definitions live INSIDE the package** — `equipop/providers/`
— so they travel in the wheel. Beside it, they ship to nobody.

**The plugin and the engine are separate installs.** A fix in
`qgis/equipop_qgis/` needs the plugin zip; a fix in `equipop/` needs
the wheel. Both, every release.

**Check PyPI before claiming a version is not published.** It has been
asserted wrongly twice, both times in one session, when the check is a
single call.

**Read the lines before editing them.** Four edits this session were
written against text that had not been read — a `ROOT` that did not
exist, line numbers off by one, an anchor string that was never there.
