#!/usr/bin/env python3
# =====================================================================
# make_release_zip.py - build the complete source ZIP, safely.
#
# BACKLOG 156. The 1.29.6 release ZIP could not be extracted on
# Windows. Five of its members were named
#
#     EquiPop-1.29.6/C:\Data\...\gridby_points_EquiPop_run.csv
#
# because the test suite writes run manifests into the working
# directory (BACKLOG 101) and the zip was built from the whole tree.
# Windows refuses drive-letter syntax inside an archive member, so the
# file needed deliberate member-skipping to open at all.
#
# The clean-up HAD been run - before the test suite, which then
# recreated the files. That is the lesson: a manual step in the right
# order is not a fix, because the order will be got wrong again. So
# the check lives here, runs every time, and REFUSES rather than
# warns.
#
# Usage:  python tools/make_release_zip.py <version> [outdir]
# =====================================================================

import os
import re
import sys
import zipfile

# Anything matching these cannot be extracted reliably, or should
# never have been in the tree in the first place.
BAD_NAME = re.compile(
    r"""(^[A-Za-z]:)      # a drive letter: C:\...
      | \\                # a backslash anywhere
      | (^/)              # an absolute path
      | (^|/)\.\.(/|$)    # a traversal component
      | [:*?"<>|]         # characters Windows refuses in a name
    """, re.VERBOSE)

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules",
             "equipop.egg-info", ".mypy_cache", ".ruff_cache"}
SKIP_SUFFIX = (".pyc", ".pyo")


def members(root):
    """Every file that should ship, as (absolute path, archive name)."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(SKIP_SUFFIX):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            yield full, rel


def check(names):
    """Refuse the whole build if any name cannot be extracted."""
    bad = [n for n in names if BAD_NAME.search(n)]
    if bad:
        raise SystemExit(
            "\n  REFUSING to build the release ZIP: "
            f"{len(bad)} member name(s) cannot be extracted on Windows.\n\n"
            + "".join(f"      {n}\n" for n in bad[:10])
            + ("      ...\n" if len(bad) > 10 else "")
            + "\n  These are almost certainly run manifests written into\n"
              "  the working directory by the test suite (BACKLOG 101).\n"
              "  Delete them and build again - do not skip them, or the\n"
              "  next release will carry them too.\n")


def build(root, version, outdir):
    top = f"EquiPop-{version}"
    out = os.path.join(outdir, f"{top}-complete.zip")
    found = list(members(root))
    check([rel for _, rel in found])
    os.makedirs(outdir, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for full, rel in sorted(found, key=lambda t: t[1]):
            z.write(full, f"{top}/{rel}")
    return out, len(found)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: make_release_zip.py <version> [outdir]")
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path, n = build(here, sys.argv[1],
                    sys.argv[2] if len(sys.argv) > 2 else here)
    print(f"  wrote {path}  ({n:,} files, every name checked)")
