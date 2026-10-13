#!/usr/bin/env python3
# =====================================================================
# bundle_out.py - where tools/make_bundle.sh may put a bundle, and how
# the finished files get there.
#
# v1.57.1, external review of 1.57.0 (BACKLOG 411). make_bundle.sh
# began with `rm -rf "$OUT"` on whatever path it was given. Reproduced
# on disposable copies of the tree: an output of `tests` deleted all
# 77 test files, and `../EquiPop` deleted the whole repository. (`.`,
# the reviewer's example, happens to be refused by rm itself.)
#
# So the bundle script now deletes NOTHING it is given. It builds into
# a fresh temporary folder, and this file:
#   check   - decides, BEFORE anything is built, whether OUT is a place
#             a bundle may go;
#   install - moves the finished files into OUT, removing only the
#             files a PREVIOUS bundle there listed in its marker - so a
#             release note added beside a bundle survives a rebuild,
#             and nothing this script did not make is ever touched.
#
# Usage:  python tools/bundle_out.py check ROOT OUT
#             prints OUT as an absolute path, or refuses (exit 1)
#         python tools/bundle_out.py install ROOT WORK OUT
# =====================================================================

import hashlib
import os
import shutil
import sys

#: The file a bundle leaves in its folder: the files it made, each
#: with its SHA-256. Its presence is what makes a folder replaceable.
MARKER = ".equipop_bundle"
_HEAD = "# equipop make_bundle.sh - files this bundle made, and SHA-256"


def canon(path):
    return os.path.realpath(os.path.abspath(os.path.expanduser(path)))


def _same(a, b):
    return os.path.normcase(a) == os.path.normcase(b)


def _inside(child, parent):
    c, p = os.path.normcase(child), os.path.normcase(parent)
    return c.startswith(p.rstrip(os.sep) + os.sep)


def problem(root, out, home=None):
    """Why a bundle may NOT go to `out`, or None. Decides only."""
    root, out = canon(root), canon(out)
    home = canon(home if home is not None else os.path.expanduser("~"))
    if _same(out, os.path.dirname(out)):
        return "it is the top of a file system"
    if _same(out, home):
        return "it is your home folder"
    if _same(out, root):
        return "it is the repository itself"
    if _inside(root, out):
        return "the repository is inside it"
    if _inside(out, root):
        return ("it is inside the repository - a bundle there is swept "
                "into the next working-tree zip, and deleting it can "
                "take repository files with it")
    if os.path.lexists(out):
        if not os.path.isdir(out) or os.path.islink(out):
            return "it exists and is not a plain folder"
        entries = os.listdir(out)
        if entries and MARKER not in entries:
            return ("it exists, is not empty, and holds no bundle made by "
                    "this script - nothing in it will be deleted")
    return None


def _listed(out):
    """The file names the previous bundle in `out` made."""
    path = os.path.join(out, MARKER)
    if not os.path.exists(path):
        return []
    names = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        name = line.split("  ", 1)[-1]
        if (not name or name in (".", "..", MARKER) or "/" in name
                or "\\" in name or os.sep in name):
            raise SystemExit(f"REFUSING: {path} lists '{name}', which is "
                             "not a plain file name. Nothing was touched.")
        names.append(name)
    return names


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def install(root, work, out):
    """Move every plain file in `work` into `out`. Returns
    [(sha256, name)] for what was installed."""
    why = problem(root, out)
    if why:
        raise SystemExit(f"REFUSING to install the bundle into {out}: "
                         f"{why}.")
    out = canon(out)
    new = sorted(n for n in os.listdir(work)
                 if not n.startswith(".")
                 and os.path.isfile(os.path.join(work, n)))
    if not new:
        raise SystemExit(f"REFUSING: {work} holds no files to install.")
    old = set(_listed(out)) if os.path.isdir(out) else set()
    if os.path.isdir(out):
        clash = [n for n in new
                 if n not in old and os.path.lexists(os.path.join(out, n))]
        if clash:
            raise SystemExit(
                f"REFUSING: {out} already holds {clash}, which no earlier "
                "bundle made - they would be overwritten. Nothing was "
                "touched.")
    os.makedirs(out, exist_ok=True)
    for name in sorted(old):                 # ONLY what a bundle made
        p = os.path.join(out, name)
        if os.path.isfile(p) and not os.path.islink(p):
            os.remove(p)
    record = []
    for name in new:
        shutil.move(os.path.join(work, name), os.path.join(out, name))
        record.append((_sha256(os.path.join(out, name)), name))
    with open(os.path.join(out, MARKER), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(_HEAD + "\n")
        for digest, name in record:
            fh.write(f"{digest}  {name}\n")
    return record


def main(argv):
    if len(argv) == 3 and argv[0] == "check":
        why = problem(argv[1], argv[2])
        if why:
            print(f"REFUSING to build a bundle into {canon(argv[2])}: "
                  f"{why}.", file=sys.stderr)
            print("  Give a new folder, or one an earlier bundle was "
                  "built into.", file=sys.stderr)
            return 1
        print(canon(argv[2]))
        return 0
    if len(argv) == 4 and argv[0] == "install":
        for digest, name in install(argv[1], argv[2], argv[3]):
            print(f"{digest}  {name}")
        return 0
    print("usage: bundle_out.py check ROOT OUT | install ROOT WORK OUT",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
