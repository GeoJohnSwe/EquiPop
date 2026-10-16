# -*- coding: utf-8 -*-
"""
live_fetch_check.py - machine 5's catalogue and fetch, against the LIVE
services. About five minutes; under 30 MB downloaded.

BACKLOG 414, v1.58.0. Everything in tools 5a, 5b and 5c is tested
offline against the answers John's three probes captured on 14 October
2026. What no offline test can show is that the services still answer
that way today, and that QGIS's own GDAL writes the .pbf layers. This
runs John's three common requests for real, small:

  1. WorldPop age and sex, three countries, two years (listed), and
     two 1 km files fetched.
  2. Geofabrik: Sweden's RAILWAYS taken out of its 1.87 GB shapefile
     zip by range requests (about 5 MB); Germany listed by its states;
     Norway's missing shapefile.
  3. Dated extracts: which 1 January .pbf files Sweden has (listed
     only), and Liechtenstein's 2020 roads and buildings fetched and
     written to GeoPackage.

HOW TO RUN IT - IN QGIS, which is where 5a-5c run:
  Plugins > Python Console > Show Editor (the notepad icon) > Open
  this file > Run (the green arrow). QGIS is busy until it prints
  DONE. Or from a prompt where equipop is installed:
      python live_fetch_check.py

Everything goes into a new folder in your home folder,
equipop_live_check/<date_time>/, and a zip of the RECORDS (not the
data) is made beside it. Send that zip back.
"""
import json
import os
import platform
import sys
import time
import traceback
import zipfile
from datetime import datetime

OUT = os.path.join(os.path.expanduser("~"), "equipop_live_check",
                   datetime.now().strftime("%Y%m%d_%H%M"))
os.makedirs(OUT, exist_ok=True)
LOG = []


def say(line=""):
    print(line)
    LOG.append(str(line))


def step(title, fn):
    say("")
    say(f"## {title}")
    t0 = time.time()
    try:
        fn()
        say(f"- OK in {time.time() - t0:.1f} s")
        return True
    except Exception as e:
        say(f"- FAILED after {time.time() - t0:.1f} s: "
            f"{type(e).__name__}: {e}")
        LOG.append("```\n" + traceback.format_exc()[-3000:] + "```")
        return False


def main():
    import equipop
    from equipop.doors import catalogue as cat
    from equipop.doors import fetchrows as fr
    from equipop.doors.fetching import verify_folder

    say(f"# EquiPop live fetch check, {datetime.now():%Y-%m-%d %H:%M}")
    say(f"- equipop {equipop.__version__} from {equipop.__file__}")
    say(f"- Python {platform.python_version()} at {sys.executable}")
    conv = fr.find_converter()
    say(f"- .pbf layers written by: {conv.name if conv else 'NOTHING HERE'}")
    net = cat.Net()
    seen = {}

    def wp_list():
        rows = cat.browse_worldpop("age_sex", "Sweden, Kenya, Burundi",
                                   "2015, 2020", net=net, say=say)
        cat.write_csv(rows, os.path.join(OUT, "catalogue_worldpop.csv"))
        say(f"- {len(rows)} rows (240 expected); sizes: "
            + ", ".join(f"{r['place_code']} {r['year']} {r['size_mb']} MB"
                        f" ({r['size_is']})" for r in rows
                        if r["size_is"] == "measured"))
        seen["wp"] = rows

    def wp_old():
        rows = cat.browse_worldpop("age_sex", "Burundi", "2010, 2020",
                                   net=net, say=say)
        say(f"- {len(rows)} rows, series "
            f"{sorted({(r['series'], r['resolution']) for r in rows})}, "
            f"top band {max(r['age_from'] for r in rows)}+")

    def wp_fetch():
        pick = [r for r in seen["wp"] if r["place_code"] == "BDI"
                and r["year"] == 2020 and r["age_from"] == 15]
        res = fr.fetch_rows(pick, os.path.join(OUT, "fetched"), net=net,
                            say=say)
        say(f"- downloaded: {res['downloaded']}")

    def gf_sweden_railways():
        rows = cat.browse_geofabrik("Sweden", "railways", net=net, say=say)
        cat.write_csv(rows, os.path.join(OUT, "catalogue_osm_sweden.csv"))
        r = rows[0]
        say(f"- {r['series']} {r['layer']} of {r['date']}: {r['size_mb']} "
            f"MB packed; inside: {r['inside']}")
        n0 = net.calls
        res = fr.fetch_rows(rows, os.path.join(OUT, "fetched"), net=net,
                            say=say, max_mb=60)
        say(f"- {net.calls - n0} requests; files: {res['downloaded']}")
        shp = [n for n in res["downloaded"] if n.endswith(".shp")]
        if shp:
            say(f"- {shp[0]} opens with "
                f"{_count(os.path.join(OUT, 'fetched', shp[0]))} features")

    def gf_germany():
        rows = cat.browse_geofabrik("Germany", "roads", net=net, say=say)
        cat.write_csv(rows, os.path.join(OUT, "catalogue_osm_germany.csv"))
        say(f"- {len(rows)} rows: " + ", ".join(
            f"{r['place_code']} {r['size_mb']:.0f} MB" for r in rows))

    def gf_norway():
        rows = cat.browse_geofabrik("Norway", "buildings", net=net, say=say)
        say(f"- {[(r['series'], r['file'], r['size_mb']) for r in rows]}")

    def gf_years_listed():
        rows = cat.browse_geofabrik("Sweden, Liechtenstein", "buildings",
                                    years="2014, 2018, 2020, 2024, 2026",
                                    latest=False, net=net, say=say)
        cat.write_csv(rows, os.path.join(OUT, "catalogue_osm_years.csv"))
        say("- dated .pbf found: " + ", ".join(
            f"{r['place_code']} {r['date']} {r['size_mb']} MB"
            for r in rows))

    def gf_years_fetch():
        if conv is None:
            say("- SKIPPED: nothing here can write .pbf layers")
            return
        rows = cat.browse_geofabrik("Liechtenstein", "buildings, roads, pois",
                                    years="2020", latest=True, net=net,
                                    say=say)
        res = fr.fetch_rows(rows, os.path.join(OUT, "fetched"), net=net,
                            say=say, max_mb=60)
        say(f"- derived: {res['derived']}")

    def verify():
        v = verify_folder(os.path.join(OUT, "fetched"), say=say)
        say(f"- ok {v['ok']}, changed {v['changed']}, missing "
            f"{v['missing']}, untracked {v['untracked']}")

    for title, fn in (
            ("1a. WorldPop age and sex - three countries, two years",
             wp_list),
            ("1b. WorldPop 2010 and 2020 - one series for both?", wp_old),
            ("1c. WorldPop - fetch two 1 km files", wp_fetch),
            ("2a. Geofabrik - Sweden's railways out of the 1.87 GB zip",
             gf_sweden_railways),
            ("2b. Geofabrik - Germany by its states (listed)", gf_germany),
            ("2c. Geofabrik - Norway (its shapefile was missing)",
             gf_norway),
            ("3a. Dated extracts - which years exist (listed)",
             gf_years_listed),
            ("3b. Dated extracts - Liechtenstein 2020 and today, fetched",
             gf_years_fetch),
            ("4. Verify the folder", verify)):
        step(title, fn)
    say("")
    say(f"- {net.calls} requests in all")


def _count(path):
    try:
        from osgeo import ogr
        ds = ogr.Open(path)
        return ds.GetLayer(0).GetFeatureCount()
    except Exception:
        pass
    try:
        import pyogrio
        return pyogrio.read_info(path)["features"]
    except Exception as e:
        return f"(could not open: {e})"


def finish():
    with open(os.path.join(OUT, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")
    keep = []
    for root, _d, names in os.walk(OUT):
        for n in names:
            if n.endswith((".md", ".csv", ".json")):
                keep.append(os.path.join(root, n))
    zpath = OUT + "_records.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in keep:
            z.write(p, os.path.relpath(p, os.path.dirname(OUT)))
    print("")
    print(f"DONE. Send this file back: {zpath}")


try:
    main()
except Exception as e:                       # equipop itself missing
    say(f"COULD NOT START: {type(e).__name__}: {e}")
    LOG.append("```\n" + traceback.format_exc()[-3000:] + "```")
finally:
    finish()
