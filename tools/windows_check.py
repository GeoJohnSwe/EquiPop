#!/usr/bin/env python3
"""
windows_check.py - run EquiPop's whole test suite on this machine, and
write a short report to send back.

v1.59.2. The external review of 1.59.1 ran the suite on Windows and
found nine failures that Linux - where every release had been tested -
could not show: a fake-ArcGIS path joined with the wrong separator, and
a manifest that Windows briefly refused to replace. Real ArcGIS Pro
runs only on Windows, so the suite has to pass there too. This runs it.

HOW: extract equipop_working_tree.zip from the release archive, then
in the Anaconda Prompt (Start menu > Anaconda Prompt) go into the
EquiPop-<version> folder it makes, and run:

    python tools\\windows_check.py

or with the full path to this file. It uses the Python it is started
with, tests the code in THIS folder (not an installed EquiPop), changes
nothing outside the report, and needs no network. It takes a few
minutes. At the end it names the report file - send that back.

If a package the tests need is missing, it says which and the one line
that installs them, and stops before running anything.
"""

from __future__ import annotations

import datetime as _dt
import importlib
import os
import platform
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Needed: without these, tests fail rather than skip.
NEEDED = ("pytest", "numpy", "pandas", "scipy", "pyproj", "rasterio",
          "openpyxl", "pyarrow")
#: Wanted: without these, the tests that need them are skipped - the
#: run is still worth having, but says less.
WANTED = ("geopandas", "pyogrio", "shapely", "matplotlib")


def _version_of_tree():
    try:
        src = open(os.path.join(ROOT, "equipop", "__init__.py"),
                   encoding="utf-8").read()
        m = re.search(r'__version__\s*=\s*["\']([^"\']+)', src)
        return m.group(1) if m else "unknown"
    except OSError:
        return "unknown"


def _have(name):
    try:
        mod = importlib.import_module(name)
        return str(getattr(mod, "__version__", "present"))
    except Exception:
        return None


def main(argv=None):
    if not os.path.isdir(os.path.join(ROOT, "tests")) or \
            not os.path.isdir(os.path.join(ROOT, "equipop")):
        print(f"This file should sit in the tools folder of an extracted "
              f"EquiPop source zip; {ROOT} has no tests or equipop "
              "folder beside it.")
        return 2
    version = _version_of_tree()
    print(f"EquiPop {version} - the test suite, on this machine")
    print(f"  code   : {ROOT}")
    print(f"  Python : {sys.version.split()[0]} ({sys.executable})")

    found = {n: _have(n) for n in NEEDED + WANTED}
    missing = [n for n in NEEDED if not found[n]]
    if missing:
        print("\nThese packages are needed for the tests and are not in "
              "this Python:\n  " + ", ".join(missing))
        print("Install them with this line, then run this again:\n"
              f"  pip install {' '.join(missing)}")
        return 2
    lacking = [n for n in WANTED if not found[n]]
    if lacking:
        print(f"  (without {', '.join(lacking)}, the tests that need "
              f"them are skipped: pip install {' '.join(lacking)})")

    # THE TREE'S OWN CODE, not an installed copy. `python -m pytest`
    # from the tree's folder puts it first on the path; checked rather
    # than assumed, and said in the report.
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    probe = subprocess.run(
        [sys.executable, "-c", "import equipop; print(equipop.__file__)"],
        cwd=ROOT, env=env, capture_output=True, text=True)
    used = (probe.stdout or probe.stderr).strip().splitlines()[-1:] or ["?"]
    print(f"  testing: {used[0]}\n")

    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M")
    report = os.path.join(os.path.dirname(ROOT),
                          f"EquiPop_{version}_windows_check_{stamp}.txt")
    cmd = [sys.executable, "-m", "pytest", "tests", "-q", "-rfEs",
           "--tb=short", "-p", "no:cacheprovider"]
    t0 = time.time()
    lines = []
    with subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True,
                          encoding="utf-8", errors="replace") as p:
        for line in p.stdout:
            print(line, end="")
            lines.append(line)
        code = p.wait()
    minutes = (time.time() - t0) / 60

    tail = [ln.strip() for ln in lines if re.search(
        r"\d+ (passed|failed|error)", ln)]
    head = [
        f"EquiPop {version} - test suite on {platform.system()}",
        f"date     : {_dt.datetime.now():%Y-%m-%d %H:%M}",
        f"system   : {platform.platform()}",
        f"python   : {sys.version.split()[0]} ({sys.executable})",
        f"code     : {ROOT}",
        f"imported : {used[0]}",
        "packages : " + ", ".join(f"{n} {found[n] or 'MISSING'}"
                                  for n in NEEDED + WANTED),
        f"took     : {minutes:.1f} min",
        f"result   : {tail[-1] if tail else 'no summary line - see below'}",
        "", "-" * 70, ""]
    with open(report, "w", encoding="utf-8") as f:
        f.write("\n".join(head))
        f.writelines(lines)
    print("\n" + "=" * 70)
    print(f"Result: {tail[-1] if tail else 'see the report'}")
    print(f"Report: {report}")
    print("Please send that file back.")
    return code


if __name__ == "__main__":
    sys.exit(main())
