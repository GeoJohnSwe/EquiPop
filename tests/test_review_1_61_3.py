# -*- coding: utf-8 -*-
"""External review of 1.61.3 (23 October 2026) - the small findings,
fixed in 1.61.4.

The two engine findings have files of their own: the radius window
(BACKLOG 430) and the share's denominator (431) are in
test_radius_window.py, and the Windows checker's package list (432)
is in test_windows_check.py. These are the wording: what the release
record says it lists, what the reviewer brief promises, and what
Stata's `which` prints for the two older commands.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _version():
    py = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'^version\s*=\s*"([^"]+)"', py, re.M).group(1)


def test_the_record_says_it_lists_every_OTHER_file(tmp_path):
    """The record goes into RELEASE_x.md, which is placed in the bundle
    afterwards - so the list cannot contain the note itself. "Every
    file" was untrue by one; it now says which one and why.

    BROKEN WITH: the heading back to "SHA-256 of every file in the
    bundle:"."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "a.txt").write_text("x", encoding="utf-8")
    with zipfile.ZipFile(bundle / "equipop_working_tree.zip", "w") as z:
        z.writestr("t/tests/test_one.py", "def test_one():\n    pass\n")
    r = subprocess.run([sys.executable, str(ROOT / "tools" /
                        "release_record.py"), str(bundle)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=600)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "every other file in the bundle" in r.stdout
    assert "every file in the bundle" not in r.stdout
    assert re.search(r"[0-9a-f]{64}  a\.txt", r.stdout)


def test_the_brief_sends_reviewers_to_the_public_history():
    """The brief promised "a git clone, not an export", and every
    archive since has been an export. It now says where the history
    is, and that the archive has none.

    BROKEN WITH: the old promise restored."""
    brief = (ROOT / "REVIEWER_BRIEF.md").read_text(encoding="utf-8")
    assert "A git clone, not an export" not in brief
    assert "https://github.com/GeoJohnSwe/EquiPop" in brief
    assert "carries no `.git`" in brief


def test_every_stata_command_prints_this_release():
    """Stata's `which equipop_knn` printed "v1.35" and `which
    equipop_run` "EquiPop 1.6" - beside an equipop.ado that moved with
    every release. A user checking an install was told it was years
    old. Every .ado's banner now carries the release, and the version
    bump moves them.

    BROKEN WITH: equipop_run's banner back to "EquiPop 1.6"; and its
    bump pattern removed (caught by the round-trip test in
    test_packaging.py)."""
    v = _version()
    ados = sorted((ROOT / "stata").glob("*.ado"))
    assert len(ados) >= 3
    for p in ados:
        first = p.read_text(encoding="utf-8").splitlines()[0]
        assert re.match(rf"\*! {p.stem} v{re.escape(v)}\s", first), (
            p.name, first)
