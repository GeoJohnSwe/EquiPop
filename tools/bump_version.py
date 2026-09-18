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

#: WHERE A VERSION IS DECLARED. One entry per place, with the pattern
#: that matches the DECLARATION and nothing else.
#:
#: BACKLOG 315. This used to be a blanket string replace over every
#: file containing the old version - and it quietly falsified the
#: history it passed over. A comment written during 1.47.4 saying
#: "v1.47.4, BACKLOG 299" became 1.47.5, then .6, and by 1.47.11 the
#: .pyt claimed item 299 landed in 1.47.11 when it landed in 1.47.6.
#: Five such comments in that file alone.
#: BACKLOG.md and MANUAL.md were already excluded for exactly this
#: reason - "historical version numbers are facts about the past" -
#: and the same reasoning was never applied to CODE COMMENTS, which
#: are full of them. The tool written to stop one kind of drift was
#: causing another, and a worse one: the backlog drift was visible.
DECLARATIONS = [
    ("pyproject.toml", r'^(version\s*=\s*")[^"]+(")'),
    ("equipop/__init__.py", r'^(__version__\s*=\s*")[^"]+(")'),
    ("qgis/equipop_qgis/__init__.py", r'^(__version__\s*=\s*")[^"]+(")'),
    ("qgis/equipop_qgis/metadata.txt", r'^(version=)\S+()'),
    ("arcgis/EquiPop.pyt", r'^(TOOLBOX_VERSION\s*=\s*")[^"]+(")'),
    ("stata/equipop.pkg", r'^(d EquiPop )\S+( )'),
    ("stata/equipop.ado", r'^(\*! equipop v)\S+(\s)'),
    ("stata/equipop.ado", r'^(\s*local eqp_ado_version\s+")[^"]+(")'),
    ("CITATION.cff", r'^(version:\s*)\S+()'),
    ("equipop_test_pass.do", r'^(\*! EquiPop )\S+(\s)'),
    ("equipop_test_pass.do", r'^(global EQP_EXPECT\s+")[^"]+(")'),
]

#: Files where the version appears inside a FILENAME the reader is
#: told to type - equipop-1.47.12-py3-none-any.whl and friends. Those
#: must move, and they are unambiguous, so a plain replace is right
#: for the filename pattern only.
FILENAMES = ["INSTALL.md", "arcgis/ARCGIS_GUIDE.md"]

#: Documents whose version line asserts A HUMAN REVIEWED THEM. Never
#: touched. If the suite then complains that they are stale, that is
#: the guard working and the answer is to READ THEM.
NEVER = ("TEACHING.md", "PROPOSALS.md")


def current():
    with open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8") as f:
        return re.search(r'^version\s*=\s*"([^"]+)"', f.read(),
                         re.M).group(1)


def _unused_files_with(old):
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
        print(f"[bump] '{new}' is not a version like 1.47.12")
        return 2
    check = "--check" in argv
    old = current()
    if old == new:
        print(f"[bump] already {new}")
        return 0
    print(f"[bump] {old} -> {new}"
          + (" (check only, nothing written)" if check else ""))

    missed = []
    for rel, pat in DECLARATIONS:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            missed.append(f"{rel} (file missing)")
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        fixed, n = re.subn(pat, lambda m: m.group(1) + new + m.group(2),
                           text, flags=re.M)
        if not n:
            missed.append(f"{rel} ({pat})")
            continue
        print(f"    {rel}  x{n}")
        if not check:
            with open(path, "w", encoding="utf-8") as f:
                f.write(fixed)

    for rel in FILENAMES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        fixed = text.replace(f"equipop-{old}", f"equipop-{new}")
        fixed = fixed.replace(f"equipop_qgis-{old}", f"equipop_qgis-{new}")
        if fixed != text:
            print(f"    {rel}  (filenames)")
            if not check:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(fixed)

    if missed:
        print("\n[bump] NOT FOUND - a declaration moved or was "
              "renamed, and a version is now stale:")
        for m in missed:
            print("   ", m)
        return 1

    print()
    print("[bump] NOT TOUCHED, on purpose: " + ", ".join(NEVER))
    print("       Their version line says a HUMAN HAS READ THEM.")
    print("[bump] code comments, BACKLOG.md and MANUAL.md are left")
    print("       alone: a version in prose is a FACT ABOUT THE PAST.")
    if not check:
        print("\n[bump] regenerate what is derived:")
        print("       python tools/make_sthlp.py")
        print("       python arcgis/make_help_xml.py")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
