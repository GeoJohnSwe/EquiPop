#!/usr/bin/env python3
"""bump_version.py - move the version everywhere it must move, and
NOWHERE IT MUST NOT.

    python tools/bump_version.py 1.47.11
    python tools/bump_version.py 1.47.11 --check   # say, change nothing

WHY THIS EXISTS (v1.47.11). The version lived in a dozen files and was
moved with a blanket sed:

    for f in $(grep -rl "1.47.5" .); do sed -i 's/1.47.5/1.47.11/g' $f; done

That works and it quietly destroyed a guard. TEACHING.md and
PROPOSALS.md each carry `**Last updated: <version>, <date>**`, and a
test compares it against pyproject.toml so that a release cannot pass
while a planning document has drifted. THE BLANKET SED UPDATED THAT
LINE TOO. The check could never fire: the one thing meant to prove a
human had looked was being answered by the same command that raised
the question.

So the rule is made EXECUTABLE rather than remembered. This tool
skips the status documents, and their version line moves only when
somebody has actually read them.

THE GENERAL LESSON, worth more than the tool: A CHECK THAT THE
ROUTINE UPDATES AUTOMATICALLY IS NOT A CHECK. Before trusting a guard,
ask what the normal workflow does to it.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Documents whose version line asserts A HUMAN REVIEWED THEM. Never
#: touched here. If the suite then complains that they are stale, that
#: is the guard working and the answer is to READ THEM, not to bump
#: them.
NEVER = ("TEACHING.md", "PROPOSALS.md")

#: Not code, and full of historical version numbers that must not be
#: rewritten: "DONE v1.29.5" is a fact about the past.
SKIP_ALSO = ("BACKLOG.md", "MANUAL.md", "CHANGELOG.md")

SKIP_DIRS = {".git", "dist", "build", "__pycache__", ".pytest_cache",
             "node_modules", "fixtures"}


def current():
    with open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8") as f:
        return re.search(r'^version\s*=\s*"([^"]+)"', f.read(),
                         re.M).group(1)


def files_with(old):
    out = []
    for root, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in names:
            if n in NEVER or n in SKIP_ALSO:
                continue
            if n.endswith((".pyc", ".whl", ".gz", ".zip", ".7z",
                           ".tif", ".dta", ".parquet")):
                continue
            p = os.path.join(root, n)
            try:
                with open(p, encoding="utf-8") as f:
                    if old in f.read():
                        out.append(p)
            except (OSError, UnicodeDecodeError):
                continue
    return sorted(out)


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    new = argv[0]
    if not re.fullmatch(r"\d+\.\d+\.\d+", new):
        print(f"[bump] '{new}' is not a version like 1.47.11")
        return 2
    check = "--check" in argv
    old = current()
    if old == new:
        print(f"[bump] already {new}")
        return 0
    hits = files_with(old)
    print(f"[bump] {old} -> {new}, {len(hits)} file(s)"
          + (" (check only, nothing written)" if check else ""))
    for p in hits:
        rel = os.path.relpath(p, ROOT)
        print("   ", rel)
        if check:
            continue
        with open(p, encoding="utf-8") as f:
            s = f.read()
        with open(p, "w", encoding="utf-8") as f:
            f.write(s.replace(old, new))
    print()
    print("[bump] NOT TOUCHED, on purpose: " + ", ".join(NEVER))
    print("       Their version line says a HUMAN HAS READ THEM. If")
    print("       the suite now reports them stale, read them - do")
    print("       not bump them to silence it.")
    print("[bump] also skipped: " + ", ".join(SKIP_ALSO)
          + " (historical version numbers are facts about the past)")
    if not check:
        print("\n[bump] regenerate what is derived:")
        print("       python tools/make_sthlp.py")
        print("       python arcgis/make_help_xml.py")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
