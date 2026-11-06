# -*- coding: utf-8 -*-
"""BACKLOG 459: the Stata commands on a Python that cannot take the engine.

Found by Kit Baum testing the SSC submission of 1.63.1 on a Mac whose
Stata used Apple's own Python 3.9.6. `equipop doctor` died with
"No module named 'numpy'" and "error occurred while loading
equipop.ado", r(7102): Stata runs an ado's top-level `python:` block
when it LOADS the file, and the block imported numpy at the top, so
every subcommand failed - the doctor written for that machine included.

tests/test_stata_python_block.py runs the same block, but with numpy
installed, which is why it could not see this. Here numpy, pandas,
scipy and equipop are hidden, `sfi` is stubbed, and the version and
platform are set to the cases that matter: Apple's 3.9, a legacy 3.10
and a current Python. What is checked is what a user would READ.

The review of 1.63.2 found four gaps the first version of these tests
could not see, because they stopped at the classifying function:
the recovery steps told the user to change python_exec BEFORE the
restart (F1), `equipop unit` skipped the check (F2), an ordinary run on
3.10 dropped the warning (F4), and nothing looked at the Mac wording or
equipop_run's message (F5). Each now has a test at the command level.
"""
import ast
import collections
import re
import subprocess
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ADO = ROOT / "stata" / "equipop.ado"
RUN_ADO = ROOT / "stata" / "equipop_run.ado"

_VI = collections.namedtuple("_VI", "major minor micro releaselevel serial")
PY39 = _VI(3, 9, 6, "final", 0)
PY310 = _VI(3, 10, 14, "final", 0)
PY312 = _VI(3, 12, 7, "final", 0)
APPLE_PY = ("/Library/Developer/CommandLineTools/Library/Frameworks/"
            "Python3.framework/Versions/3.9/bin/python3")


def _block(path):
    """The text between the file's one `python:` and its `end`."""
    lines = path.read_text(encoding="utf-8").splitlines()
    starts = [i for i, ln in enumerate(lines) if ln.rstrip() == "python:"]
    assert len(starts) == 1, f"{path.name}: expected one python: block"
    i = starts[0]
    for j in range(i + 1, len(lines)):
        if lines[j].rstrip() == "end":
            return "\n".join(lines[i + 1:j])
    raise AssertionError(f"{path.name}: python: block never closed")


@pytest.fixture
def sfi(monkeypatch):
    """`sfi` stubbed; numpy, pandas, scipy and equipop cannot import."""
    mod = types.ModuleType("sfi")
    mod.LOCALS, mod.RC, mod.ERR, mod.SHOWN = {}, [], [], []

    class Macro:
        @staticmethod
        def setLocal(name, value):
            mod.LOCALS[name] = value

        @staticmethod
        def getLocal(name):
            return mod.LOCALS.get(name, "")

    class SFIToolkit:
        @staticmethod
        def errprintln(s):
            mod.ERR.append(s)

        @staticmethod
        def displayln(s):
            mod.SHOWN.append(s)

        @staticmethod
        def error(rc):
            mod.RC.append(rc)

        @staticmethod
        def stata(cmd):
            pass

    mod.Macro, mod.SFIToolkit = Macro, SFIToolkit
    mod.Data = type("Data", (), {})
    mod.Matrix = type("Matrix", (), {})
    monkeypatch.setitem(sys.modules, "sfi", mod)
    for name in ("numpy", "pandas", "scipy", "equipop"):
        monkeypatch.setitem(sys.modules, name, None)
    return mod


def _load(path, ns=None):
    ns = {"__name__": "__main__"} if ns is None else ns
    exec(compile(_block(path), path.name, "exec"), ns)
    return ns


def _as(monkeypatch, version, platform=None, exe=None):
    monkeypatch.setattr(sys, "version_info", version)
    if platform:
        monkeypatch.setattr(sys, "platform", platform)
    if exe:
        monkeypatch.setattr(sys, "executable", exe)


# ------------------------------------------------------------ loading
@pytest.mark.parametrize("path", [ADO, RUN_ADO], ids=lambda p: p.name)
def test_the_block_loads_without_numpy_or_the_engine(sfi, path):
    """BROKEN WITH: `import numpy as np` back at the top of the block."""
    _load(path)


def test_the_floor_in_the_ado_is_pyproject_s():
    """One floor. BROKEN WITH: pyproject raised and _PY_ENGINE_FLOOR not."""
    py = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    floor = re.search(r'requires-python\s*=\s*">=(\d+)\.(\d+)"', py)
    src = ADO.read_text(encoding="utf-8")
    ado = re.search(r"^_PY_ENGINE_FLOOR = \((\d+), (\d+)\)$", src, re.M)
    assert ado, "equipop.ado no longer declares _PY_ENGINE_FLOOR"
    assert ado.groups() == floor.groups()


def test_the_two_blocks_do_not_redefine_each_other_s_names():
    """Both blocks run in ONE Python namespace in a Stata session, so a
    name defined in both is whichever file Stata loaded last. Only the
    two helpers that are identical by design may be shared.

    BROKEN WITH: equipop_run.ado's note helper named _python_note_once."""
    def names(path):
        tree = ast.parse(_block(path))
        out = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                out.add(node.name)
            elif isinstance(node, ast.Assign):
                out |= {t.id for t in node.targets
                        if isinstance(t, ast.Name)}
        return out
    shared = names(ADO) & names(RUN_ADO)
    assert shared <= {"_col", "_engine_takes_unit"}, shared


LOCAL_MACRO = re.compile(r"`[^'\n]*'")      # `name' and `: function'
GLOBAL_MACRO = re.compile(r"\$[A-Za-z_{]")    # $name and ${name}


def _every_block_line(path):
    """(line number, text) for every line of every python block."""
    lines = path.read_text(encoding="utf-8").splitlines()
    inside, out = False, []
    for n, line in enumerate(lines, 1):
        bare = line.strip()
        if not inside and bare in ("python:", "python"):
            inside = True
        elif inside and bare == "end":
            inside = False
        elif inside:
            out.append((n, line))
    return out


@pytest.mark.parametrize(
    "path", sorted((ROOT / "stata").glob("*.ado")), ids=lambda p: p.name)
def test_no_line_of_a_python_block_is_a_stata_macro(path):
    """BACKLOG 460. Stata expands macros in EVERY line of a python
    block before Python sees it - comments and strings too. 1.63.2's
    comment quoted the doctor between backticks beside "Apple's", so
    Stata read `: Stata had picked Apple' as a macro function, said
    "Stata not allowed" and printed the rest of the block (John's
    first Windows run). Running the block in Python, as every other
    test here does, cannot see this: it never passes through Stata.

    BROKEN WITH: the 1.63.2 comment line put back."""
    bad = [f"{path.name}:{n}: {line.strip()}"
           for n, line in _every_block_line(path)
           if LOCAL_MACRO.search(line) or GLOBAL_MACRO.search(line)]
    assert not bad, ("Stata would expand these as macros - write "
                     "-command- instead of backticks:\n" + "\n".join(bad))


def test_the_macro_check_reads_the_line_that_broke_1_63_2():
    """The check above has to fire on the real thing, not only on
    tidy examples."""
    line = ("# from `equipop doctor`: Stata had picked Apple's own "
            "Python 3.9.6.")
    assert LOCAL_MACRO.search(line)
    assert not LOCAL_MACRO.search("# from -equipop doctor-: Stata had "
                                  "picked Apple's own Python 3.9.6.")
    assert GLOBAL_MACRO.search('print("$HOME")')


# ------------------------------------------------- doctor and setup
def test_doctor_on_apple_python_says_what_to_do(sfi, monkeypatch, capsys):
    ns = _load(ADO)
    _as(monkeypatch, PY39, "darwin", APPLE_PY)
    ns["_equipop_doctor_py"]("1.63.2", "1.48.0")
    out = capsys.readouterr().out
    assert "needs Python 3.11 or newer" in out
    assert "Python 3.9.6" in out and APPLE_PY in out
    assert "Apple's developer" in out
    assert "/usr/local/bin/python3.12" in out
    assert "Traceback" not in out


def test_the_restart_comes_before_set_python_exec(sfi, monkeypatch,
                                                  capsys):
    """Review of 1.63.2, F1. These lines are printed by a running
    Python, and Stata will not change python_exec once Python has
    started. BROKEN WITH: the first draft's order (set, then restart)."""
    ns = _load(ADO)
    _as(monkeypatch, PY39, "darwin", APPLE_PY)
    ns["_equipop_doctor_py"]("1.63.2", "1.48.0")
    out = capsys.readouterr().out
    restart = out.index("Quit Stata completely")
    search = out.index("python search")
    set_exec = out.index("set python_exec")
    setup = out.index("equipop setup")
    assert restart < search < set_exec < setup
    assert "BEFORE equipop or any other Python command" in out


def test_setup_refuses_an_old_python_before_pip(sfi, monkeypatch, capsys):
    ns = _load(ADO)
    _as(monkeypatch, PY39)

    def no_pip(*a, **k):
        raise AssertionError("pip must not run on Python 3.9")

    monkeypatch.setattr(subprocess, "run", no_pip)
    monkeypatch.setattr(subprocess, "check_output", no_pip)
    ns["_equipop_setup_py"]("", "1.63.2", "1.48.0")
    assert sfi.LOCALS.get("eqp_setup_failed") == "1"
    assert "needs Python 3.11 or newer" in capsys.readouterr().out


# ------------------------------------------------ the ordinary run
def test_machine1_on_an_old_python_refuses_in_words(sfi, monkeypatch):
    ns = _load(ADO)
    _as(monkeypatch, PY39)
    ns["_equipop_machine1"](x="x", y="y", treat="t", k="100")
    assert sfi.RC == [198]
    assert any("3.11 or newer" in s for s in sfi.ERR)
    assert any("Quit Stata completely" in s for s in sfi.ERR)


def test_unit_on_an_old_python_refuses_in_words(sfi, monkeypatch):
    """Review of 1.63.2, F2. BROKEN WITH: _equipop_unit_py without the
    check - it said "install into THAT one", which cannot work on 3.9."""
    ns = _load(ADO)
    _as(monkeypatch, PY39)
    ns["_equipop_unit_py"]()
    assert sfi.RC == [198]
    assert any("3.11 or newer" in s for s in sfi.ERR)
    assert not any("THAT one" in s for s in sfi.ERR)


def test_python_310_warns_once_per_session_on_an_ordinary_run(
        sfi, monkeypatch):
    """Review of 1.63.2, F4. BROKEN WITH: machine 1 discarding the
    'warn' lines, or showing them on every call."""
    ns = _load(ADO)
    _as(monkeypatch, PY310)
    for _ in range(3):
        ns["_equipop_machine1"](x="x", y="y", treat="t", k="100")
    notes = [s for s in sfi.SHOWN if "Note:" in s]
    assert len(notes) == 1
    assert "1.61.0" in notes[0]
    # numpy is hidden here, so each run then stops at the engine import
    assert sfi.RC == [198, 198, 198]


def test_a_doctor_that_showed_the_warning_is_not_repeated(sfi,
                                                          monkeypatch,
                                                          capsys):
    ns = _load(ADO)
    _as(monkeypatch, PY310)
    ns["_equipop_doctor_py"]("1.63.2", "1.48.0")
    assert "1.61.0" in capsys.readouterr().out
    ns["_equipop_machine1"](x="x", y="y", treat="t", k="100")
    assert not any("Note:" in s for s in sfi.SHOWN)


def test_a_current_python_is_not_mentioned(sfi, monkeypatch):
    ns = _load(ADO)
    _as(monkeypatch, PY312)
    assert ns["_python_check"]() == ("ok", [])
    ns["_equipop_machine1"](x="x", y="y", treat="t", k="100")
    assert not any("Note:" in s for s in sfi.SHOWN)
    # and the failure is the missing engine, said in words
    assert sfi.RC == [198]
    assert any("cannot be loaded" in s for s in sfi.ERR)


# ------------------------------------------------------ equipop_run
def _run(ns):
    ns["_equipop_run"]("counts", "x", "y", "t", "", "", "100", "", "",
                       100.0, "", "", "tobler", 0, "", "", "", "supply",
                       "x", "y", 0.0, "decay", "2sfca", 0.0, 0.0, 0)


def test_equipop_run_without_the_engine_says_what_to_do(sfi,
                                                        monkeypatch):
    ns = _load(RUN_ADO)
    _as(monkeypatch, PY39, exe=APPLE_PY)
    _run(ns)
    assert sfi.RC == [198]
    text = "\n".join(sfi.ERR)
    assert "Python 3.9.6" in text and APPLE_PY in text
    assert "3.11 or newer" in text and "equipop doctor" in text


def test_equipop_run_on_310_notes_once(sfi, monkeypatch):
    ns = _load(RUN_ADO)
    _as(monkeypatch, PY310)
    _run(ns)
    _run(ns)
    notes = [s for s in sfi.SHOWN if "Note:" in s]
    assert len(notes) == 1 and "1.61.0" in notes[0]
