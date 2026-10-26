#!/usr/bin/env python3
# =====================================================================
# release_record.py - what a release note may say about its tests,
# taken from the release itself.
#
# v1.57.1, external review of 1.57.0 (BACKLOG 411). The 1.57.0 note
# said "1,725 passed, 19 skipped, 1,744 collected"; the reviewer
# collected 1,763. Both were right: their machine had geopandas, which
# collects two test modules mine skipped whole. The number was true
# and still not EVIDENCE, because a reader could not tell which
# machine, which packages, or which tree it came from.
#
# So this runs the suite FROM THE SHIPPED WORKING-TREE ZIP, extracted
# into a fresh folder - the frozen release, not the tree it was built
# from - once per interpreter given, and prints a block for the
# release note: the totals, the versions that produced them, the
# optional packages that were absent (each one turns tests into
# skips), and the SHA-256 of every other file in the bundle (the
# release note that carries this block is added to it afterwards).
#
# Usage:  python tools/release_record.py <bundle_dir> [python ...]
#         (no interpreter given: this one)
# =====================================================================

import hashlib
import os
import re
import subprocess
import sys
import tempfile
import zipfile

#: Optional packages the suite can use; absent, their tests skip.
OPTIONAL = ("geopandas", "rasterio", "esda", "libpysal", "cffconvert",
            "yaml", "openpyxl", "pyreadstat", "matplotlib")
CORE = ("numpy", "pandas", "scipy", "pytest")

_PROBE = """
import importlib, json, platform, sys
out = {"python": platform.python_version()}
for m in %r + %r:
    try:
        mod = importlib.import_module(m)
        out[m] = getattr(mod, "__version__", "present")
    except Exception:
        out[m] = None
print(json.dumps(out))
"""


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


#: The child writes its output as UTF-8 and we read it as UTF-8
#: (BACKLOG 426) - otherwise each side uses its own system encoding,
#: and a path or test name with "ö" in it could be misread.
_CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def environment(python):
    import json
    r = subprocess.run([python, "-c", _PROBE % (CORE, OPTIONAL)],
                       capture_output=True, check=True, env=_CHILD_ENV,
                       text=True, encoding="utf-8", errors="replace")
    return json.loads(r.stdout)


def run_suite(python, tree):
    """The suite's final summary line, run from `tree`."""
    r = subprocess.run([python, "-m", "pytest", "-q", "-p",
                        "no:cacheprovider"], cwd=tree,
                       capture_output=True, env=_CHILD_ENV,
                       text=True, encoding="utf-8", errors="replace")
    last = [ln for ln in r.stdout.splitlines() if " in " in ln
            and re.search(r"\d+ (passed|failed)", ln)]
    if not last:
        raise SystemExit(f"no pytest summary from {python}:\n"
                         + r.stdout[-2000:] + r.stderr[-2000:])
    return last[-1].strip("= ").strip(), r.returncode


def collected(summary):
    n = {k: int(v) for v, k in re.findall(
        r"(\d+) (passed|failed|skipped|errors?|xfailed|xpassed)", summary)}
    return n, sum(n.values())


def main(argv):
    if not argv:
        raise SystemExit("usage: release_record.py <bundle_dir> [python ...]")
    bundle, pythons = argv[0], argv[1:] or [sys.executable]
    tree_zip = os.path.join(bundle, "equipop_working_tree.zip")
    lines = ["## Build record", "",
             f"Working tree (the frozen release): `equipop_working_tree.zip`"
             f", SHA-256 `{_sha(tree_zip)}`.", "",
             "The suite was run FROM THAT ZIP, extracted into a fresh "
             "folder:", ""]
    failed = False
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(tree_zip) as z:
            z.extractall(tmp)
            top = z.namelist()[0].split("/")[0]
        tree = os.path.join(tmp, top)
        for py in pythons:
            env = environment(py)
            summary, rc = run_suite(py, tree)
            counts, total = collected(summary)
            failed |= rc != 0
            core = ", ".join(f"{m} {env[m]}" for m in CORE if env.get(m))
            absent = [m for m in OPTIONAL if not env.get(m)]
            present = [f"{m} {env[m]}" for m in OPTIONAL if env.get(m)]
            lines += [f"- **{summary}** ({total:,} collected) - Python "
                      f"{env['python']}, {core}.",
                      f"  Optional present: {', '.join(present) or 'none'}"
                      f"; absent: {', '.join(absent) or 'none'}."]
    # "every OTHER file" (v1.61.4, review of 1.61.3): this record
    # becomes part of RELEASE_x.md, which is placed in the bundle after
    # it is written - so the note cannot list its own checksum.
    lines += ["", "SHA-256 of every other file in the bundle (the release "
              "note, which carries this list, is added after it):", "",
              "```"]
    for name in sorted(os.listdir(bundle)):
        p = os.path.join(bundle, name)
        if os.path.isfile(p) and not name.startswith("."):
            lines.append(f"{_sha(p)}  {name}")
    lines.append("```")
    print("\n".join(lines))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
