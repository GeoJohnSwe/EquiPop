#!/usr/bin/env python3
"""
run_fetch.py - MACHINE 5 from the command line.

The download leg has never run in development: every WorldPop host is
blocked from the sandbox EquiPop is built in. So THIS SCRIPT ASKS
FIRST. It lists what it would fetch and stops, and only downloads when
you add --go.

    # what datasets are there?
    python run_fetch.py --list

    # what categories does one of them have?
    python run_fetch.py --list age_structures

    # what WOULD be fetched - downloads nothing
    python run_fetch.py --project pop --iso3 BDI --year 2020 \
                        --into rasters/BDI

    # do it
    python run_fetch.py --project pop --iso3 BDI --year 2020 \
                        --into rasters/BDI --go

    # a year later: are these still the files the paper used?
    python run_fetch.py --verify rasters/BDI

Then point machine 3 at the folder. This script never analyses
anything - that is the whole point of it being separate.
"""
import argparse
import sys

from equipop.doors.fetching import (FetchError, PROVIDERS, plan_fetch,
                                    run_fetch, verify_folder)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Fetch data into a folder, with a manifest. "
                    "Downloads nothing unless you pass --go.")
    ap.add_argument("--provider", default="worldpop",
                    choices=sorted(PROVIDERS))
    ap.add_argument("--list", nargs="?", const="", metavar="DATASET",
                    help="list datasets, or the categories of one")
    ap.add_argument("--project", help="e.g. pop, age_structures, births")
    ap.add_argument("--category", help="if the dataset has several")
    ap.add_argument("--iso3", nargs="+", metavar="CODE",
                    help="one or more country codes, e.g. BDI RWA")
    ap.add_argument("--year", type=int)
    ap.add_argument("--into", metavar="FOLDER")
    ap.add_argument("--go", action="store_true",
                    help="actually download. Without this, nothing is "
                         "written")
    ap.add_argument("--verify", metavar="FOLDER",
                    help="check a fetched folder against its manifest")
    a = ap.parse_args(argv)

    try:
        if a.verify:
            got = verify_folder(a.verify)
            return 1 if (got["changed"] or got["missing"]) else 0

        if a.list is not None:
            p = PROVIDERS[a.provider]
            if a.list:
                for k, v in sorted(p.categories(a.list).items()):
                    print(f"  {k:28s} {v}")
            else:
                for k, v in sorted(p.projects().items()):
                    print(f"  {k:22s} {v}")
            return 0

        if not (a.project and a.iso3):
            ap.error("give --project and --iso3, or use --list")

        plan = plan_fetch(a.provider, project=a.project,
                          category=a.category, iso3=a.iso3,
                          year=a.year, will_download=a.go)
        if not a.go:
            print("\nAdd --go --into FOLDER to download these.")
            return 0
        if not a.into:
            ap.error("--go needs --into FOLDER")
        run_fetch(plan, a.into)
        return 0

    except FetchError as e:
        print(f"\nRefused: {e}", file=sys.stderr)
        return 2
    except Exception as e:                          # network, mostly
        print(f"\n{type(e).__name__}: {e}", file=sys.stderr)
        print("\nIf this is a network error, the request never reached "
              "the provider - check the URL in a browser first.",
              file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
