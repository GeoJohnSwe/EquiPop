# -*- coding: utf-8 -*-
"""test_windows_check.py - the Windows check runs even when pytest's own
temporary folder cannot be used.

John's first run of tools/windows_check.py (18 October 2026, Windows 11,
Python 3.13) stopped all 1,974 tests at setup: "Access is denied" on
AppData\\Local\\Temp\\pytest-of-<him>, the folder pytest keeps for itself.
Nothing about EquiPop was tested. The check now hands pytest a folder of
its own (--basetemp) and removes it afterwards.

Reproduced here by pointing pytest's temporary root at a FILE
(PYTEST_DEBUG_TEMPROOT), so the folder it would make under it cannot
exist - the same dead end, reachable without Windows rights.

BROKEN WITH: the --basetemp argument removed from windows_check.py.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _tree(tmp_path):
    """A small EquiPop-shaped folder: the check script, a package, and
    two tests that need a temporary folder."""
    tree = tmp_path / "EquiPop-9.9.9"
    (tree / "tools").mkdir(parents=True)
    (tree / "equipop").mkdir()
    (tree / "tests").mkdir()
    shutil.copy(ROOT / "tools" / "windows_check.py", tree / "tools")
    (tree / "equipop" / "__init__.py").write_text('__version__ = "9.9.9"\n')
    (tree / "tests" / "test_tmp.py").write_text(
        "def test_one(tmp_path):\n"
        "    (tmp_path / 'x').write_text('y')\n\n"
        "def test_two(tmp_path_factory):\n"
        "    assert tmp_path_factory.mktemp('z').is_dir()\n")
    return tree


def test_a_broken_pytest_temp_folder_does_not_stop_the_check(tmp_path):
    tree = _tree(tmp_path)
    blocked = tmp_path / "not_a_folder"
    blocked.write_text("pytest cannot make its folder under a file")
    temp = tmp_path / "temp"          # where the check makes its own
    temp.mkdir()
    env = dict(os.environ, PYTEST_DEBUG_TEMPROOT=str(blocked),
               TMPDIR=str(temp), TEMP=str(temp), TMP=str(temp),
               PYTHONDONTWRITEBYTECODE="1")
    run = subprocess.run([sys.executable, str(tree / "tools" /
                                              "windows_check.py")],
                         cwd=str(tmp_path), env=env, capture_output=True,
                         text=True, timeout=300)
    out = run.stdout + run.stderr
    assert run.returncode == 0, out[-3000:]
    assert "2 passed" in out
    reports = list(tmp_path.glob("EquiPop_9.9.9_windows_check_*.txt"))
    assert len(reports) == 1
    assert "result   : 2 passed" in reports[0].read_text(encoding="utf-8")
    # its own scratch folder was made where asked, and removed again
    assert list(temp.iterdir()) == []


def test_the_copy_beside_the_release_zip_finds_the_tree(tmp_path):
    """v1.60.0: John looked for the script and it was inside a zip
    inside the release zip. A copy now sits at the top of the archive,
    beside equipop_working_tree.zip, and unpacks it on first use.

    BROKEN WITH: find_root looking only in tools/.. (the copy then
    reports that it found no tree)."""
    import zipfile
    tree = _tree(tmp_path / "src")
    rel = tmp_path / "release"
    rel.mkdir()
    with zipfile.ZipFile(rel / "equipop_working_tree.zip", "w") as z:
        for p in tree.rglob("*"):
            if p.is_file():
                z.write(p, f"EquiPop-9.9.9/{p.relative_to(tree).as_posix()}")
    shutil.copy(ROOT / "tools" / "windows_check.py", rel)
    temp = tmp_path / "temp"
    temp.mkdir()
    env = dict(os.environ, TMPDIR=str(temp), TEMP=str(temp),
               TMP=str(temp), PYTHONDONTWRITEBYTECODE="1")
    for _ in range(2):                      # the second run reuses it
        run = subprocess.run([sys.executable, "windows_check.py"],
                             cwd=str(rel), env=env, capture_output=True,
                             text=True, timeout=300)
        out = run.stdout + run.stderr
        assert run.returncode == 0, out[-3000:]
        assert "2 passed" in out
    assert (rel / "EquiPop-9.9.9" / "tests" / "test_tmp.py").exists()
    assert len(list(rel.glob("EquiPop_9.9.9_windows_check_*.txt"))) >= 1
