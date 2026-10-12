#!/bin/bash
# =====================================================================
# make_bundle.sh - build the complete 19-slot release bundle.
#
# BACKLOG 404, v1.54.6. THIS PROCEDURE LIVED OUTSIDE THE REPOSITORY
# FOR EVERY RELEASE UP TO 1.54.5, in a scratch script rewritten from
# the last one each time. Three defects came out of that in one hour:
#
#   * tools/make_release_zip.py had no guard against the Pro help
#     sidecars, while my scratch script did - so the durable tool was
#     the weaker one, and 1.54.0 shipped an archive carrying them;
#   * the sidecars were present at build time only BY ACCIDENT of the
#     order I happened to work in. Moved to where the Pro slot needs
#     them, the first 1.54.6 sdist shipped with ZERO of them and
#     every check stayed green;
#   * and MANIFEST.in's `include arcgis/*.pyt.xml` is a PERMISSION,
#     not a guarantee: the files must EXIST when `python -m build`
#     runs.
#
# make_release_zip.py's own docstring had the rule all along: "a
# manual step in the right order is not a fix, because the order will
# be got wrong again". The order is written down here now, and
# tests/test_packaging.py asserts it.
#
# THE ORDER, and why each step is where it is:
#   1. GENERATE the sidecars        - they must exist before step 2
#   2. the wheel and sdist          - MANIFEST.in puts them in the sdist
#   3. the QGIS plugin
#   4. the Pro toolbox + sidecars loose, which is how a Pro user
#      actually installs them
#   5/6. the two Stata archives     - net install keeps a stata/
#        folder, SSC is FLAT with no .pkg and no stata.toc
#   7. the working tree             - sidecars DELETED from the staged
#      copy: they are build outputs and the tree must not hold them
#      (BACKLOG 45), or John unzips, commits, and his own suite fails
#   8. the documents
#   9. DELETE the sidecars          - leave the tree as it was found
#
# Usage:  tools/make_bundle.sh <version> <outdir>
# NEVER PIPED into head (BACKLOG 384): redirect and read the file.
# =====================================================================
set -euo pipefail

if [ "$#" -lt 2 ]; then
    echo "usage: tools/make_bundle.sh <version> <outdir>" >&2
    exit 2
fi

V="$1"
OUT="$(cd "$(dirname "$2")" 2>/dev/null && pwd)/$(basename "$2")"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="$OUT/.stage"
LOGS="$OUT/.logs"

cd "$ROOT"

# The version in the tree must be the version asked for, or the
# bundle's name and its contents disagree - which is the skew the
# doctor spends three screens explaining.
HAVE=$(sed -n 's/^version *= *"\(.*\)"/\1/p' pyproject.toml | head -1)
if [ "$HAVE" != "$V" ]; then
    echo "REFUSING: pyproject.toml says $HAVE, you asked for $V." >&2
    echo "  Run tools/bump_version.py $V first." >&2
    exit 1
fi

rm -rf "$OUT"
mkdir -p "$OUT" "$STAGE" "$LOGS"

# ---- 1. the Pro help sidecars, FIRST --------------------------------
python arcgis/make_help_xml.py > "$LOGS/help_xml.log" 2>&1
test -n "$(ls arcgis/*.pyt.xml 2>/dev/null)" || {
    echo "FATAL: make_help_xml.py wrote no sidecars" >&2; exit 1; }

# From here on the tree holds build outputs, so clean up on any exit.
cleanup() { rm -f "$ROOT"/arcgis/*.pyt.xml; }
trap cleanup EXIT

# ---- 2. the wheel and the source archive ----------------------------
rm -rf dist build
python -m build --outdir dist > "$LOGS/build_py.log" 2>&1
python -m twine check "dist/equipop-$V-py3-none-any.whl" \
    "dist/equipop-$V.tar.gz" >> "$LOGS/build_py.log" 2>&1
cp "dist/equipop-$V-py3-none-any.whl" "dist/equipop-$V.tar.gz" "$OUT/"

# ...and CHECK that MANIFEST.in's permission actually delivered.
if [ "$(tar tzf "$OUT/equipop-$V.tar.gz" | grep -c 'pyt\.xml')" -eq 0 ]; then
    echo "FATAL: the sdist carries no Pro help sidecars - step 1 ran" >&2
    echo "  too late, or MANIFEST.in lost its include line." >&2
    exit 1
fi

# ---- 3. the QGIS plugin ---------------------------------------------
mkdir -p "$STAGE/qgis"
cp -r qgis/equipop_qgis "$STAGE/qgis/"
find "$STAGE/qgis" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$STAGE/qgis" -name "*.pyc" -delete 2>/dev/null || true
( cd "$STAGE/qgis" && zip -qr "$OUT/equipop_qgis-$V.zip" equipop_qgis )

# ---- 4. the Pro toolbox, the five sidecars, the generator -----------
cp arcgis/EquiPop.pyt arcgis/make_help_xml.py "$OUT/"
for t in CountsShares ValueStatistics ContinentalRasters \
         SpatialDemography FolderInventory; do
    cp "arcgis/EquiPop.$t.pyt.xml" "$OUT/"
done

# ---- 5. Stata: net install (keeps the stata/ folder) ----------------
mkdir -p "$STAGE/net/stata"
cp stata/README_STATA.md stata/equipop.ado stata/equipop.pkg \
   stata/equipop.sthlp stata/equipop_example.do stata/equipop_knn.ado \
   stata/equipop_run.ado stata/equipop_showcase.do \
   stata/equipop_test_data.dta stata/stata.toc "$STAGE/net/stata/"
( cd "$STAGE/net" && zip -qr "$OUT/equipop_stata_netinstall-$V.zip" stata )

# ---- 6. Stata: the SSC batch (FLAT, no .pkg, no stata.toc) ----------
mkdir -p "$STAGE/ssc"
cp stata/equipop.ado stata/equipop.sthlp stata/equipop_example.do \
   stata/equipop_knn.ado stata/equipop_run.ado \
   stata/equipop_showcase.do stata/equipop_test_data.dta "$STAGE/ssc/"
( cd "$STAGE/ssc" && zip -qr "$OUT/equipop_ssc_submission-$V.zip" . )

# ---- 7. the whole working tree, under EquiPop-<version>/ ------------
mkdir -p "$STAGE/tree"
cp -r "$ROOT" "$STAGE/tree/EquiPop-$V"
( cd "$STAGE/tree/EquiPop-$V"
  rm -rf dist build .pytest_cache .git ./*.egg-info
  find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
  find . -name "*.pyc" -delete 2>/dev/null || true
  # THE SIDECARS MUST NOT TRAVEL IN THE WORKING TREE - build outputs,
  # shipped loose at step 4 and excluded from the repository. The
  # first 1.54.0 build left them here, so John would have unzipped
  # over his tree, committed them, and had his own suite fail with
  # "they are build outputs and the suite must not leave them behind".
  find . -name "*.pyt.xml" -delete 2>/dev/null || true )
( cd "$STAGE/tree" && zip -qr "$OUT/equipop_working_tree.zip" "EquiPop-$V" )

# ...and CHECK it, rather than trusting the line above.
if unzip -l "$OUT/equipop_working_tree.zip" | grep -q "\.pyt\.xml"; then
    echo "FATAL: the working tree zip carries .pyt.xml sidecars" >&2
    exit 1
fi

# ---- 8. the documents -----------------------------------------------
HAND=$(ls -1 HANDOVER_*.md | sed 's/HANDOVER_\([0-9]*\)\.md/\1 &/' \
       | sort -n | tail -1 | cut -d' ' -f2)
cp BACKLOG.md MANUAL.md INSTALL.md "$HAND" "$OUT/"
cp arcgis/ARCGIS_GUIDE.md "$OUT/"

# ---- 9. leave the tree as it was found ------------------------------
rm -rf "$STAGE" "$LOGS"
cleanup
trap - EXIT
if ls "$ROOT"/arcgis/*.pyt.xml > /dev/null 2>&1; then
    echo "FATAL: sidecars left in the tree" >&2; exit 1
fi

echo "---- $OUT ----"
ls -1 "$OUT"
echo "---- $(ls -1 "$OUT" | wc -l) files ----"
