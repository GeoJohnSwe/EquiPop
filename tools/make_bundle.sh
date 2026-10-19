#!/bin/bash
# =====================================================================
# make_bundle.sh - build the complete release bundle (19 slots until
# 1.58; 1.59.0 added three Pro help sidecars for tools 5a-5c).
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
#   9. VERIFY every zip, DELETE the sidecars, then INSTALL into <outdir>
#
# v1.57.1, external review of 1.57.0 (BACKLOG 411). TWO FAULTS HERE.
#   * Step 7 zipped the tree with `zip -qr` and never called
#     tools/make_release_zip.py, whose whole purpose is refusing
#     members Windows cannot extract - so 1.56.0 and 1.57.0 shipped
#     `C:\Data/EquiPop_runs/people_EquiPop_run.csv`, a run record my
#     own scratch script had written into the tree. The tree zip is now
#     built BY that tool, and every zip is re-opened and extracted
#     before the bundle is accepted.
#   * This script began `rm -rf "$OUT"`. Reproduced on copies: an
#     <outdir> of `tests` deleted every test, `../EquiPop` the whole
#     repository. It now deletes nothing it is given: it builds in a
#     fresh temporary folder, tools/bundle_out.py decides first whether
#     <outdir> may receive a bundle, and installing removes only files
#     an earlier bundle there listed in its marker.
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
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Decided BEFORE `cd`, so a relative <outdir> means what the caller
# meant, and before anything is built, so a refusal costs nothing.
OUT="$(python "$ROOT/tools/bundle_out.py" check "$ROOT" "$2")" || exit 1

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

# Everything is built HERE, a folder nobody else owns, and installed
# into $OUT only once it has all been checked.
WORK="$(mktemp -d "${TMPDIR:-/tmp}/equipop_bundle.XXXXXX")"
STAGE="$WORK/.stage"
LOGS="$WORK/.logs"
mkdir -p "$STAGE" "$LOGS"

# From here on the tree holds build outputs, so clean up on any exit.
# On failure the work folder is KEPT, because its logs say why.
cleanup() {
    rc=$?
    rm -f "$ROOT"/arcgis/*.pyt.xml
    if [ "$rc" -eq 0 ]; then rm -rf "$WORK"
    else echo "  (build failed - its logs are in $LOGS)" >&2; fi
}
trap cleanup EXIT

# ---- 1. the Pro help sidecars, FIRST --------------------------------
python arcgis/make_help_xml.py > "$LOGS/help_xml.log" 2>&1
test -n "$(ls arcgis/*.pyt.xml 2>/dev/null)" || {
    echo "FATAL: make_help_xml.py wrote no sidecars" >&2; exit 1; }

# ---- 2. the wheel and the source archive ----------------------------
rm -rf dist build
python -m build --outdir dist > "$LOGS/build_py.log" 2>&1
python -m twine check "dist/equipop-$V-py3-none-any.whl" \
    "dist/equipop-$V.tar.gz" >> "$LOGS/build_py.log" 2>&1
cp "dist/equipop-$V-py3-none-any.whl" "dist/equipop-$V.tar.gz" "$WORK/"

# ...and CHECK that MANIFEST.in's permission actually delivered.
if [ "$(tar tzf "$WORK/equipop-$V.tar.gz" | grep -c 'pyt\.xml')" -eq 0 ]; then
    echo "FATAL: the sdist carries no Pro help sidecars - step 1 ran" >&2
    echo "  too late, or MANIFEST.in lost its include line." >&2
    exit 1
fi

# ---- 3. the QGIS plugin ---------------------------------------------
mkdir -p "$STAGE/qgis"
cp -r qgis/equipop_qgis "$STAGE/qgis/"
find "$STAGE/qgis" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$STAGE/qgis" -name "*.pyc" -delete 2>/dev/null || true
( cd "$STAGE/qgis" && zip -qr "$WORK/equipop_qgis-$V.zip" equipop_qgis )

# ---- 4. the Pro toolbox, the eight sidecars, the generator ----------
cp arcgis/EquiPop.pyt arcgis/make_help_xml.py "$WORK/"
for t in CountsShares ValueStatistics ContinentalRasters \
         SpatialDemography WorldPopCatalogue OsmCatalogue FetchSelected \
         FolderInventory; do
    cp "arcgis/EquiPop.$t.pyt.xml" "$WORK/"
done

# ---- 5. Stata: net install (keeps the stata/ folder) ----------------
mkdir -p "$STAGE/net/stata"
cp stata/README_STATA.md stata/equipop.ado stata/equipop.pkg \
   stata/equipop.sthlp stata/equipop_example.do stata/equipop_knn.ado \
   stata/equipop_run.ado stata/equipop_showcase.do \
   stata/equipop_test_data.dta stata/stata.toc "$STAGE/net/stata/"
( cd "$STAGE/net" && zip -qr "$WORK/equipop_stata_netinstall-$V.zip" stata )

# ---- 6. Stata: the SSC batch (FLAT, no .pkg, no stata.toc) ----------
mkdir -p "$STAGE/ssc"
cp stata/equipop.ado stata/equipop.sthlp stata/equipop_example.do \
   stata/equipop_knn.ado stata/equipop_run.ado \
   stata/equipop_showcase.do stata/equipop_test_data.dta "$STAGE/ssc/"
( cd "$STAGE/ssc" && zip -qr "$WORK/equipop_ssc_submission-$V.zip" . )

# ---- 7. the whole working tree, under EquiPop-<version>/ ------------
# BY THE SAFE BUILDER (411): it skips caches and build directories,
# REFUSES names Windows cannot extract and run records, leaves out the
# sidecars step 1 made on purpose, and extracts the result before it
# returns. A refusal stops the bundle; it is never skipped past.
python tools/make_release_zip.py "$V" "$WORK" \
    --name equipop_working_tree.zip --skip-build-outputs \
    > "$LOGS/tree_zip.log" 2>&1 || { cat "$LOGS/tree_zip.log" >&2; exit 1; }

# ---- 8. the documents -----------------------------------------------
HAND=$(ls -1 HANDOVER_*.md | sed 's/HANDOVER_\([0-9]*\)\.md/\1 &/' \
       | sort -n | tail -1 | cut -d' ' -f2)
cp BACKLOG.md MANUAL.md INSTALL.md "$HAND" "$WORK/"
cp arcgis/ARCGIS_GUIDE.md "$WORK/"
# v1.60.0: the Windows check at the TOP of the archive, beside the
# working tree it unpacks and tests - John looked for it inside the
# working-tree zip inside the release zip, and could not find it.
cp tools/windows_check.py "$WORK/"

# ---- 9. verify, leave the tree as it was found, install -------------
# Every archive a user unzips is re-opened, CRC-checked, name-checked
# and extracted; the working tree is checked as a tree as well.
python tools/make_release_zip.py --verify "$WORK/equipop_qgis-$V.zip" \
    "$WORK/equipop_stata_netinstall-$V.zip" \
    "$WORK/equipop_ssc_submission-$V.zip" \
    "$WORK/equipop-$V-py3-none-any.whl" > "$LOGS/verify.log" 2>&1 \
    || { cat "$LOGS/verify.log" >&2; exit 1; }
python tools/make_release_zip.py --verify \
    "$WORK/equipop_working_tree.zip" --tree-version "$V" \
    >> "$LOGS/verify.log" 2>&1 || { cat "$LOGS/verify.log" >&2; exit 1; }

rm -f "$ROOT"/arcgis/*.pyt.xml
if ls "$ROOT"/arcgis/*.pyt.xml > /dev/null 2>&1; then
    echo "FATAL: sidecars left in the tree" >&2; exit 1
fi
rm -rf "$STAGE"
cat "$LOGS/verify.log"
rm -rf "$LOGS"

echo "---- $OUT ----"
python tools/bundle_out.py install "$ROOT" "$WORK" "$OUT"
echo "---- $(sed -n '/^[0-9a-f]\{64\}  /p' "$OUT/.equipop_bundle" | wc -l) files, SHA-256 above and in $OUT/.equipop_bundle ----"
