"""Build the QGIS plugin ZIP.

QGIS's Install from ZIP requires ONE top-level folder named exactly as
the Python package - `equipop_qgis/` - with metadata.txt inside it. A
zip of the folder's CONTENTS installs as a broken plugin that loads
and then cannot be found again, so the shape is checked here rather
than trusted.

Reuses the safety checks from make_release_zip: no __pycache__, no
.pyc, and no member name that Windows cannot extract (BACKLOG 101).
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, "tools")
from make_release_zip import BAD_NAME, SKIP_DIRS, SKIP_SUFFIX   # noqa: E402

SRC = "qgis/equipop_qgis"
TOP = "equipop_qgis"


def build(version, outdir):
    out = os.path.join(outdir, f"equipop_qgis-{version}.zip")
    names, files = [], []
    for dirpath, dirnames, filenames in os.walk(SRC):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if fn.endswith(SKIP_SUFFIX):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, SRC).replace(os.sep, "/")
            names.append(f"{TOP}/{rel}")
            files.append((full, f"{TOP}/{rel}"))

    bad = [n for n in names if BAD_NAME.search(n)]
    if bad:
        raise SystemExit(f"REFUSING: unextractable names {bad[:5]}")

    # The three QGIS itself insists on.
    for needed in (f"{TOP}/metadata.txt", f"{TOP}/__init__.py"):
        if needed not in names:
            raise SystemExit(f"REFUSING: {needed} is missing")
    if not any(n.startswith(f"{TOP}/") for n in names):
        raise SystemExit("REFUSING: no single top-level folder")

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for full, arc in files:
            z.write(full, arc)
    return out, names


if __name__ == "__main__":
    out, names = build(sys.argv[1], sys.argv[2])
    print("wrote", out)
    for n in names:
        print("   ", n)
