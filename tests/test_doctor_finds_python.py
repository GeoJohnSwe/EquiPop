# -*- coding: utf-8 -*-
"""BACKLOG 461: the doctor looks for a Python that is already there,
and says the whole way out in words.

Kit Baum's Mac Stata had picked Apple's Python 3.9. The 1.63.2 advice
was correct and too short - "install Python 3.11 or newer from
python.org", then four lines of Stata - for someone who has never
installed a Python (John, 6 November 2026: "if we lose Mac users
because of their unexperience with python - I think it is our loss").
Now the doctor, setup and a refused run search the places installers
put Python, start each one found to ask what it is, and name the best
with the exact line to type; when there is none, they say which page,
which button, what the installer asks and which path to type.

Two layers are tested. The search itself on this machine's real
interpreters (a Python that is not one, Python 3.9 and 3.10 when
present, a distribution's "externally managed" Python, a virtual
environment beside its base). And the WORDS a user reads, on a
simulated Mac, Windows and Linux, with the interpreters stood in for -
what a test can reach of a Mac without a Mac.
"""
import os
import subprocess
import sys
import venv
from pathlib import Path

import pytest

from test_stata_block_without_numpy import (     # noqa: F401  (fixture)
    ADO, APPLE_PY, PY39, PY310, PY312, _as, _load, sfi)

MIN = "1.48.0"


def _info(ver, *, managed=False, venv_=False, shared=True, bits=64,
          machine="arm64", engine=""):
    return {"version": ver, "shared": shared, "managed": managed,
            "venv": venv_, "bits": bits, "machine": machine,
            "engine": engine}


def _files(tmp_path, *rel):
    """Real files, so the search's isfile() sees them."""
    out = []
    for r in rel:
        f = tmp_path / r
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("")
        out.append(str(f))
    return out


def _stand_in(ns, monkeypatch, table, started=None):
    """The search finds exactly table's paths, and a 'started' Python
    answers with table's info. Records what was started."""
    started = [] if started is None else started

    def probe(path):
        started.append(path)
        return table[path]

    ns["_python_candidates"] = lambda: list(table)
    ns["_probe_python"] = probe
    monkeypatch.setattr("platform.machine", lambda: "arm64")
    return started


def _doctor(ns, capsys, min_engine=MIN):
    ns["_equipop_doctor_py"]("1.63.4", min_engine)
    return capsys.readouterr().out


# ---------------------------------------------------- the real search
def test_the_probe_reads_the_python_running_this_test(sfi):
    ns = _load(ADO, search=True)
    info = ns["_probe_python"](sys.executable)
    assert info is not None
    assert info["version"] == tuple(sys.version_info[:3])
    assert info["bits"] == 64
    assert info["shared"] in (True, False)


def test_something_that_is_not_a_python_says_nothing(sfi, tmp_path):
    ns = _load(ADO, search=True)
    junk = tmp_path / "python3.12"
    junk.write_text("not a program")
    assert ns["_probe_python"](str(junk)) is None
    assert ns["_probe_python"](str(tmp_path / "missing")) is None


@pytest.mark.parametrize("ver", ["3.9", "3.10"])
def test_old_pythons_are_found_and_named_too_old(sfi, ver):
    exe = Path.home() / ".local" / "bin" / f"python{ver}"
    if not exe.exists():
        pytest.skip(f"no Python {ver} here")
    ns = _load(ADO, search=True)
    info = ns["_probe_python"](str(exe))
    assert info["version"][:2] == tuple(int(p) for p in ver.split("."))
    why = ns["_python_unusable"](info)
    assert why.startswith("too old"), why
    if ver == "3.10":
        assert "1.61.0" in why


def test_a_distribution_python_is_seen_as_externally_managed(sfi):
    """Debian's /usr/bin/python3.12 here carries EXTERNALLY-MANAGED."""
    exe = "/usr/bin/python3.12"
    if not os.path.exists(exe):
        pytest.skip("no distribution Python here")
    stdlib = subprocess.run(
        [exe, "-c", "import sysconfig; print(sysconfig.get_path('stdlib'))"],
        capture_output=True, text=True).stdout.strip()
    marker = Path(stdlib) / "EXTERNALLY-MANAGED"
    ns = _load(ADO, search=True)
    assert ns["_probe_python"](exe)["managed"] == marker.exists()


def test_a_virtual_environment_is_not_mistaken_for_its_base(sfi,
                                                           tmp_path):
    """A venv's python is a link to its base, so the real path alone
    would merge the two - and the venv is the one pip may write to.
    BROKEN WITH: the search keyed on os.path.realpath only."""
    env = tmp_path / "equipop-python"
    venv.EnvBuilder(with_pip=False, symlinks=True).create(env)
    ns = _load(ADO, search=True)
    inside = ns["_py_venv_python"](str(env))
    ns["_python_candidates"] = lambda: [inside, sys.executable]
    ns["_PY_FOUND"].clear()
    found = ns["_find_pythons"]()
    paths = [p for p, _, _ in found]
    assert inside in paths
    info = dict((p, i) for p, i, _ in found)[inside]
    assert info["venv"] is True and info["managed"] is False


def test_equipop_s_own_environment_is_looked_at_first(sfi, monkeypatch,
                                                     tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    ns = _load(ADO, search=True)
    pats = ns["_python_patterns"]()
    assert pats[0] == str(tmp_path / "equipop-python" / "bin" / "python")


def test_the_search_happens_once_per_stata_session(sfi, monkeypatch,
                                                   capsys, tmp_path):
    ns = _load(ADO, search=True)
    _as(monkeypatch, PY39, "darwin", APPLE_PY)
    (good,) = _files(tmp_path, "Versions/3.12/bin/python3.12")
    started = _stand_in(ns, monkeypatch, {good: _info((3, 12, 7))})
    _doctor(ns, capsys)
    _doctor(ns, capsys)
    ns["_equipop_setup_py"]("", "1.63.4", MIN)
    assert started == [good]


def test_no_more_than_twelve_pythons_are_started(sfi, monkeypatch,
                                                 capsys, tmp_path):
    ns = _load(ADO, search=True)
    _as(monkeypatch, PY39, "darwin", APPLE_PY)
    paths = _files(tmp_path, *[f"p{i}/bin/python3.12" for i in range(20)])
    started = _stand_in(ns, monkeypatch,
                        {p: _info((3, 12, 7)) for p in paths})
    _doctor(ns, capsys)
    assert len(started) == 12


def test_some_pythons_are_never_even_started(sfi, monkeypatch, capsys,
                                            tmp_path):
    """Apple's /usr/bin/python3 opens an installer dialog on a Mac
    without the developer tools; Anaconda closes Stata; a Windows Store
    shortcut can open the Store. Named in the report, never run.
    BROKEN WITH: _python_passed_over returning '' for everything."""
    ns = _load(ADO, search=True)
    _as(monkeypatch, PY39, "darwin", APPLE_PY)
    conda, store, arc = _files(
        tmp_path, "anaconda3/bin/python", "WindowsApps/python3.exe",
        "ArcGIS/Pro/bin/Python/envs/arcgispro-py3/python.exe")
    table = {conda: None, store: None, arc: None}
    if os.path.exists("/usr/bin/python3"):
        table["/usr/bin/python3"] = None
    started = _stand_in(ns, monkeypatch, table)
    out = _doctor(ns, capsys)
    assert started == []
    assert "Stata and Anaconda do not mix" in out
    assert "a Windows Store shortcut" in out
    assert "belongs to ArcGIS Pro" in out
    # nothing usable, so the install steps
    assert "Download macOS installer" in out


# ------------------------------------------------- what the user reads
def test_a_python_org_python_already_there_is_named_with_the_line(
        sfi, monkeypatch, capsys, tmp_path):
    ns = _load(ADO, search=True)
    _as(monkeypatch, PY39, "darwin", APPLE_PY)
    (good,) = _files(tmp_path, "Versions/3.12/bin/python3.12")
    _stand_in(ns, monkeypatch, {good: _info((3, 12, 7))})
    out = _doctor(ns, capsys)
    assert "GOOD NEWS" in out and "Python 3.12.7" in out
    line = f'set python_exec "{good}", permanently'
    assert line in out
    assert (out.index("Looking for other Pythons")
            < out.index("Quit Stata completely")
            < out.index(line) < out.index("        equipop setup")
            < out.index("        equipop doctor"))
    assert "Download macOS installer" not in out
    assert "BEFORE equipop or any other Python command" in out


def test_a_python_with_the_engine_already_needs_no_setup(
        sfi, monkeypatch, capsys, tmp_path):
    ns = _load(ADO, search=True)
    _as(monkeypatch, PY39, "darwin", APPLE_PY)
    (good,) = _files(tmp_path, "Versions/3.12/bin/python3.12")
    _stand_in(ns, monkeypatch, {good: _info((3, 12, 7), engine="1.63.3")})
    out = _doctor(ns, capsys)
    assert "already has the EquiPop engine (1.63.3)" in out
    assert "        equipop setup" not in out
    assert "        equipop doctor" in out


def test_an_engine_older_than_the_commands_does_not_count(
        sfi, monkeypatch, capsys, tmp_path):
    ns = _load(ADO, search=True)
    _as(monkeypatch, PY39, "darwin", APPLE_PY)
    (good,) = _files(tmp_path, "Versions/3.12/bin/python3.12")
    _stand_in(ns, monkeypatch, {good: _info((3, 12, 7), engine="1.40.1")})
    out = _doctor(ns, capsys)
    assert "        equipop setup" in out


def test_the_best_python_is_the_one_with_the_least_to_do(
        sfi, monkeypatch, capsys, tmp_path):
    """Engine already there, then one pip may install into, then the
    newest. Homebrew's 3.14 is newer but refuses pip; python.org's
    3.12 takes it directly."""
    ns = _load(ADO, search=True)
    _as(monkeypatch, PY39, "darwin", APPLE_PY)
    brew, org = _files(tmp_path, "opt/homebrew/bin/python3.14",
                       "Versions/3.12/bin/python3.12")
    _stand_in(ns, monkeypatch, {brew: _info((3, 14, 1), managed=True),
                                org: _info((3, 12, 7))})
    out = _doctor(ns, capsys)
    assert f'set python_exec "{org}", permanently' in out
    assert "Other Pythons on this computer:" in out and brew in out


def test_only_a_homebrew_python_goes_through_a_venv_of_our_own(
        sfi, monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    ns = _load(ADO, search=True)
    _as(monkeypatch, PY39, "darwin", APPLE_PY)
    (brew,) = _files(tmp_path, "opt/homebrew/bin/python3.13")
    _stand_in(ns, monkeypatch, {brew: _info((3, 13, 1), managed=True)})
    out = _doctor(ns, capsys)
    env = str(tmp_path / "home" / "equipop-python")
    assert "It belongs to Homebrew" in out
    assert "Terminal (in Applications > Utilities)" in out
    make = f'"{brew}" -m venv "{env}"'
    use = f'set python_exec "{env}/bin/python", permanently'
    assert make in out and use in out
    assert (out.index(make) < out.index("Quit Stata completely")
            < out.index(use) < out.index("        equipop setup"))


@pytest.mark.parametrize("info,why", [
    (_info((3, 12, 7), bits=32), "32-bit"),
    (_info((3, 12, 7), shared=False), "shared library"),
    (_info((3, 12, 7), machine="x86_64"), "built for x86_64"),
    (_info((3, 10, 14)), "only 1.61.0"),
    (_info((3, 9, 6)), "too old"),
])
def test_a_python_stata_cannot_use_is_not_suggested(
        sfi, monkeypatch, capsys, tmp_path, info, why):
    ns = _load(ADO, search=True)
    _as(monkeypatch, PY39, "darwin", APPLE_PY)
    (p,) = _files(tmp_path, "x/bin/python3.12")
    _stand_in(ns, monkeypatch, {p: info})
    out = _doctor(ns, capsys)
    assert "GOOD NEWS" not in out
    assert why in out
    assert "Download macOS installer" in out


def test_windows_with_nothing_gets_the_installer_and_the_exact_path(
        sfi, monkeypatch, capsys):
    local = os.path.join("C:", "Users", "kit", "AppData", "Local")
    monkeypatch.setenv("LOCALAPPDATA", local)
    ns = _load(ADO)          # nothing found; this is about the steps
    _as(monkeypatch, PY39, "win32", "C:/old/python.exe")
    monkeypatch.setattr("platform.machine", lambda: "AMD64")
    out = _doctor(ns, capsys)
    exe = os.path.join(local, "Programs", "Python", "Python313",
                       "python.exe")
    assert "https://www.python.org/downloads/windows/" in out
    assert "Download Windows installer (64-bit)" in out
    assert "Use admin privileges when installing py.exe" in out
    assert "Install Now" in out
    assert f'set python_exec "{exe}", permanently' in out
    assert "Apple" not in out


def test_windows_on_arm_gets_the_arm_installer(sfi, monkeypatch, capsys):
    monkeypatch.setenv("LOCALAPPDATA", "L")
    ns = _load(ADO)
    _as(monkeypatch, PY39, "win32", "C:/old/python.exe")
    monkeypatch.setattr("platform.machine", lambda: "ARM64")
    out = _doctor(ns, capsys)
    assert "Download Windows installer (ARM64)" in out
    assert os.path.join("Python313-arm64", "python.exe") in out


def test_linux_with_nothing_gets_a_venv_of_our_own(sfi, monkeypatch,
                                                   capsys, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    ns = _load(ADO)                       # search off: nothing found
    _as(monkeypatch, PY39, "linux", "/usr/bin/python3.9")
    out = _doctor(ns, capsys)
    env = str(tmp_path / "equipop-python")
    assert "sudo apt install python3 python3-venv" in out
    assert f'python3 -m venv "{env}"' in out
    assert f'set python_exec "{env}/bin/python", permanently' in out


# ---------------------------------------------- the other doors
def test_setup_on_an_old_python_shows_the_same_way_out(
        sfi, monkeypatch, capsys, tmp_path):
    ns = _load(ADO, search=True)
    _as(monkeypatch, PY39, "darwin", APPLE_PY)
    (good,) = _files(tmp_path, "Versions/3.12/bin/python3.12")
    _stand_in(ns, monkeypatch, {good: _info((3, 12, 7))})
    ns["_equipop_setup_py"]("", "1.63.4", MIN)
    out = capsys.readouterr().out
    assert sfi.LOCALS.get("eqp_setup_failed") == "1"
    assert f'set python_exec "{good}", permanently' in out


def test_a_refused_run_carries_the_same_steps(sfi, monkeypatch,
                                              tmp_path):
    ns = _load(ADO, search=True)
    _as(monkeypatch, PY39, "darwin", APPLE_PY)
    (good,) = _files(tmp_path, "Versions/3.12/bin/python3.12")
    _stand_in(ns, monkeypatch, {good: _info((3, 12, 7))})
    ns["_equipop_machine1"](x="x", y="y", treat="t", k="100")
    assert sfi.RC == [198]
    assert any(f'set python_exec "{good}"' in s for s in sfi.ERR)


def test_an_ordinary_run_on_310_does_not_search(sfi, monkeypatch):
    """The run goes on, so it must not be kept waiting while other
    Pythons are started. BROKEN WITH: _python_note_once calling
    _python_check() for the 'warn' level."""
    ns = _load(ADO, search=True)
    _as(monkeypatch, PY310)

    def no(*a, **k):
        raise AssertionError("searched on an ordinary 3.10 run")

    ns["_python_candidates"] = no
    ns["_equipop_machine1"](x="x", y="y", treat="t", k="100")
    assert any("Note:" in s for s in sfi.SHOWN)


def test_a_current_python_never_searches(sfi, monkeypatch, capsys):
    ns = _load(ADO, search=True)
    _as(monkeypatch, PY312)

    def no(*a, **k):
        raise AssertionError("searched on a current Python")

    ns["_python_candidates"] = no
    _doctor(ns, capsys)
    ns["_equipop_machine1"](x="x", y="y", treat="t", k="100")


def test_every_printed_line_fits_a_stata_window_but_paths(
        sfi, monkeypatch, capsys):
    """The Results window wraps at about 80 characters; a step broken
    by the window is harder to follow. Paths and the lines that carry
    them are exempt - they must be copied whole."""
    ns = _load(ADO, search=True)
    for plat, exe in (("darwin", APPLE_PY), ("win32", "C:/p.exe"),
                      ("linux", "/usr/bin/python3.9")):
        ns["_PY_FOUND"].clear()
        _as(monkeypatch, PY39, plat, exe)
        ns["_python_candidates"] = lambda: []
        out = _doctor(ns, capsys)
        long = [ln for ln in out.splitlines() if len(ln) > 80
                and "/" not in ln and os.sep not in ln]
        assert not long, (plat, long)
