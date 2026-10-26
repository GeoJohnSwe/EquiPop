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


# ------------------- v1.61.4: what the check needs, and what it reports
def _checker(monkeypatch, absent):
    """The tree's own windows_check, with `absent` reported missing and
    the two child processes faked - so nothing is installed and no
    suite is run."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "windows_check_under_test", ROOT / "tools" / "windows_check.py")
    wc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wc)
    real = wc._have
    monkeypatch.setattr(wc, "_have",
                        lambda n: None if n in absent else real(n) or "x")

    class _Probe:
        stdout, stderr = "equipop/__init__.py\n", ""

    class _Suite:
        def __init__(self, *a, **k):
            self.stdout = iter(["1 passed in 0.01s\n"])

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def wait(self):
            return 0
    monkeypatch.setattr(wc.subprocess, "run", lambda *a, **k: _Probe())
    monkeypatch.setattr(wc.subprocess, "Popen", _Suite)
    return wc


def test_pyyaml_is_needed_and_named_as_pip_knows_it(monkeypatch, tmp_path,
                                                    capsys):
    """pyyaml joined the test extra in 1.61.3, for the citation checks;
    without it they skip in silence. The check stops and gives the
    install line - `pyyaml`, which is what pip installs, not `yaml`,
    which is what Python imports.

    BROKEN WITH: `yaml` left out of NEEDED (the check ran and passed)."""
    wc = _checker(monkeypatch, {"yaml"})
    assert wc.main(report_dir=str(tmp_path)) == 2
    out = capsys.readouterr().out
    assert "pip install pyyaml" in out and "pip install yaml" not in out


def test_cffconvert_is_reported_but_never_suggested(monkeypatch, tmp_path,
                                                    capsys):
    """The full schema check needs cffconvert, which would downgrade
    jsonschema in Pro's or Anaconda's Python. So its absence is in the
    report, and the advice says why it is not offered.

    BROKEN WITH: cffconvert left out of the report's package line."""
    wc = _checker(monkeypatch, {"cffconvert"})
    assert wc.main(report_dir=str(tmp_path)) == 0
    out = capsys.readouterr().out
    assert "pip install cffconvert" not in out
    assert "not suggested for this Python" in out
    report = next(tmp_path.glob("*_windows_check_*.txt")).read_text(
        encoding="utf-8")
    assert "cffconvert MISSING" in report
