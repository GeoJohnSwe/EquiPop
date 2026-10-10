# -*- coding: utf-8 -*-
"""RUN the .ado's embedded Python, instead of grepping it.

BACKLOG 331. The block's own comment has said this for releases:

    Keep this block as SMALL as possible. Code in here can only be
    run by Stata, so the Python test suite cannot reach it - which is
    how ... and 173 survive.

It was true and it was expensive. Every guard in `equipop setup` -
the venv detection, the ensurepip advice, the externally-managed
advice, the whole dispatch on what pip actually said - is tested by
GREPPING THE FILE FOR STRINGS. That is how the 1.48.2 ensurepip test
came to pass while asserting nothing, and it is why the advice for
"No matching distribution" could sit there for a release pointing at
the network when the cause was our own release ordering.

The block needs Stata only for `sfi`. Everything else is the standard
library, on purpose, because setup runs before the package exists. So
`sfi` is stubbed, the block is exec'd, and the functions are called
with pip's real output as input. The advice is then read back from
what was PRINTED - which is what a user sees - rather than from what
is written in the file.

WHAT THIS CANNOT DO, stated so nobody mistakes its scope: it does not
run Stata, so nothing here proves the ado's SYNTAX parsing, its
macros, or that Stata calls these functions with the arguments the
ado believes it passes. tests/test_stata_ado.py still reads the ado
for those. This covers the Python half only.
"""
import io
import os
import re
import sys
import types
from contextlib import redirect_stdout

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADO = os.path.join(ROOT, "stata", "equipop.ado")


def _block_source():
    """The text between `python:` and its closing `end`."""
    text = open(ADO, encoding="utf-8").read().splitlines()
    starts = [i for i, ln in enumerate(text) if ln.rstrip() == "python:"]
    assert len(starts) == 1, (
        f"expected exactly one `python:` block in equipop.ado, found "
        f"{len(starts)} - this harness no longer knows which to run")
    i = starts[0]
    for j in range(i + 1, len(text)):
        if text[j].rstrip() == "end":
            return "\n".join(text[i + 1:j])
    raise AssertionError("the python: block is never closed by `end`")


class _Macro:
    """The two sfi calls the block makes, and nothing more."""
    store: dict = {}

    @classmethod
    def setLocal(cls, name, value):
        cls.store[name] = value

    @classmethod
    def setGlobal(cls, name, value):
        cls.store[name] = value

    @classmethod
    def getGlobal(cls, name):
        return cls.store.get(name, "")

    @classmethod
    def getLocal(cls, name):
        return cls.store.get(name, "")


@pytest.fixture
def block():
    """The block, executed, with sfi stubbed out."""
    sfi = types.ModuleType("sfi")
    sfi.Macro = _Macro
    sfi.Data = types.SimpleNamespace()
    sfi.SFIToolkit = types.SimpleNamespace(
        stata=lambda *a, **k: None,
        displayln=lambda s: print(s))
    _Macro.store = {}
    saved = sys.modules.get("sfi")
    sys.modules["sfi"] = sfi
    try:
        ns: dict = {"__name__": "equipop_ado_block"}
        exec(compile(_block_source(), "equipop.ado:python", "exec"), ns)
        yield ns
    finally:
        if saved is None:
            sys.modules.pop("sfi", None)
        else:
            sys.modules["sfi"] = saved


def _run_setup(block, monkeypatch, stderr, stdout="", code=1,
               ado_version="1.49.3"):
    """Call the real _equipop_setup_py with a canned pip result."""
    import subprocess

    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, code, stdout, stderr)

    monkeypatch.setattr(subprocess, "run", fake_run)
    buf = io.StringIO()
    with redirect_stdout(buf):
        block["_equipop_setup_py"]("", ado_version)
    return buf.getvalue()


# --------------------------------------------------------------------
# The release-ordering failure, which is what 331 is about
# --------------------------------------------------------------------

PIP_NO_SUCH_VERSION = (
    "ERROR: Could not find a version that satisfies the requirement "
    "equipop>=1.49.3 (from versions: 1.48.0, 1.48.2, 1.49.1)\n"
    "ERROR: No matching distribution found for equipop>=1.49.3\n")


def test_an_engine_that_does_not_exist_yet_is_named_as_our_mistake(
        block, monkeypatch):
    """BACKLOG 331, John's question before the SSC reply went out:
    "this way ado will be 1.49.3 and the py version an earlier version
    which would lead to a conflict, correct?"

    Correct, and worse than a conflict. Setup asks pip for
    `equipop>=<ado version>`; if the commands reach SSC before the
    engine reaches PyPI, pip finds nothing that new and the install
    FAILS OUTRIGHT for every new user - not a doctor warning, a hard
    stop at the first instruction in the paper.

    The advice must name the real cause, because the user cannot fix
    it and must not be sent looking. Before this it fell into the
    network branch: "pip could not reach PyPI... Check the network and
    any proxy, and that this Python is 3.10 or newer." All true, none
    of it the cause - BACKLOG 319's exact fault, written in the very
    release that fixed 319.
    """
    out = _run_setup(block, monkeypatch, PIP_NO_SUCH_VERSION)
    assert "OUR MISTAKE" in out, (
        "the user is not told that the missing engine is our release "
        f"ordering and not their machine:\n{out}")
    assert "network" not in out.lower() and "proxy" not in out.lower(), (
        "still sending the user to debug their network for a version "
        f"we never published:\n{out}")
    # and it must leave them somewhere to go
    assert "pip install --upgrade equipop" in out, (
        "no workable fallback offered - the newest engine there is")
    assert "doctor" in out, (
        "the fallback leaves the engine behind the commands, so it "
        "must send them to the doctor to see that")


def test_a_real_network_failure_still_gets_the_network_advice(
        block, monkeypatch):
    """The branch above must not swallow the case it was carved out
    of. Same pip error class, no version floor in it."""
    out = _run_setup(
        block, monkeypatch,
        "ERROR: Could not find a version that satisfies the "
        "requirement equipop (from versions: none)\n"
        "ERROR: No matching distribution found for equipop\n")
    assert "network" in out.lower(), out
    assert "OUR MISTAKE" not in out


# --------------------------------------------------------------------
# The guards that had only ever been grepped for
# --------------------------------------------------------------------

def test_a_python_without_pip_gets_the_one_line_fix(block, monkeypatch):
    """BACKLOG 319. The 1.48.2 test for this asserted that the word
    "ensurepip" appeared in the file, which it did however the code
    behaved. This calls the code."""
    out = _run_setup(block, monkeypatch,
                     "/usr/bin/python: No module named pip\n")
    assert "ensurepip" in out, out
    assert "python.org" in out, (
        "the second-line fallback - a Python built without ensurepip "
        "- is not offered")


def test_a_system_python_is_not_ours_to_change(block, monkeypatch):
    out = _run_setup(
        block, monkeypatch,
        "error: externally-managed-environment\n"
        "This environment is externally managed\n")
    assert "python.org" in out
    assert "python set exec" in out, (
        "the user is told to install another Python and not how to "
        "point Stata at it")


def test_an_unrecognised_pip_message_is_quoted_and_not_guessed_at(
        block, monkeypatch):
    """The 1.48.2 ruling: when pip says something we do not know,
    quote it and stop. Confident wrong advice cost a colleague a day."""
    out = _run_setup(block, monkeypatch,
                     "ERROR: something nobody has seen before\n")
    assert "do not recognise" in out
    assert "something nobody has seen before" in out, (
        "pip's own message is not shown, so the user has nothing to "
        "search for")
    assert "ensurepip" not in out and "python.org" not in out, (
        "advice for a different failure is being offered anyway")


def test_a_failed_setup_reports_failure_to_stata(block, monkeypatch):
    """BACKLOG 196. Setup used to print an error and return success,
    so the ado carried on. The Stata-side flag is what stops it."""
    _Macro.store = {}
    _run_setup(block, monkeypatch, "ERROR: anything at all\n")
    assert _Macro.store.get("eqp_setup_failed") == "1", (
        "pip failed and Stata was not told, so `equipop setup` exits "
        f"0: {_Macro.store}")


def test_a_successful_setup_does_not_claim_to_have_failed(
        block, monkeypatch):
    _Macro.store = {}
    out = _run_setup(block, monkeypatch, "", stdout="Successfully "
                     "installed equipop-1.49.3\n", code=0)
    assert _Macro.store.get("eqp_setup_failed") is None
    assert "QUIT STATA" in out, (
        "the restart instruction is missing - Stata keeps the Python "
        "it first loaded, so the new engine is not in memory")


# --------------------------------------------------------------------
# The floor itself
# --------------------------------------------------------------------

def _pip_cmd(block, monkeypatch, *args):
    """The command pip would actually receive."""
    import subprocess
    seen = {}

    def fake_run(cmd, **kw):
        seen["cmd"] = list(cmd)
        return subprocess.CompletedProcess(cmd, 0, "ok", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with redirect_stdout(io.StringIO()):
        block["_equipop_setup_py"](*args)
    return seen["cmd"]


def test_pip_is_asked_for_the_floor_and_not_the_release_number(
        block, monkeypatch):
    """BACKLOG 332. A floor, not a pin, and NOT the ado's version.

    196 built the floor out of the ado's own release number, which is
    not a dependency - it is a release number pretending to be one.
    The number pip is asked for must be the oldest engine that
    satisfies the ado's calls, so it can only ever name something
    already published.
    """
    cmd = _pip_cmd(block, monkeypatch, "", "1.49.3", "1.48.0")
    assert "equipop>=1.48.0" in cmd, cmd
    assert "equipop>=1.49.3" not in cmd, (
        "pip is being asked for the ado's release number again - a "
        "release that reaches SSC before PyPI then installs nothing")
    assert "equipop==1.48.0" not in cmd, (
        "an exact pin would stop an older ado ever receiving a "
        "bug-fixed engine")
    assert re.search(r"equipop>=\d+\.\d+", " ".join(cmd)), cmd


def test_an_old_ado_that_sends_no_floor_still_gets_one(
        block, monkeypatch):
    """A pre-1.49.3 ado passes two arguments. Its own version is then
    the best floor available, which is what it always was."""
    cmd = _pip_cmd(block, monkeypatch, "", "1.48.2")
    assert "equipop>=1.48.2" in cmd, cmd


def test_every_engine_call_the_ado_makes_is_one_the_engine_accepts():
    """JOHN'S DOCTOR OUTPUT, 10 OCTOBER 2026, AND SIX RELEASES OF DEAD
    CODE.

    BROKEN WITH: removing `min_engine` from doctor.run's signature, or
    calling it with a keyword the engine does not take.

    His report showed engine 1.54.2 against commands 1.54.3 with a
    loud "THE ENGINE IS OLDER THAN THE COMMANDS, and that combination
    does break" - and the floor those commands declare, 1.48.0, was
    satisfied. The correct line is "needs engine : 1.48.0 or newer -
    satisfied".

    THE CAUSE: `report()` takes `min_engine` and `run()` did not. The
    .ado calls `run()`. So every doctor run since BACKLOG 332 raised
    TypeError, fell back to a call without the floor, and reported by
    comparing two RELEASE numbers - which 332 exists to stop. **The
    floor check was never once consulted from the Stata door.**

    AND IT WAS HIDDEN BY A BROAD EXCEPT, written for an engine older
    than 1.49.3: `except TypeError` cannot tell a missing parameter
    from a TypeError raised deep inside the report, and it degraded
    silently either way.

    I WROTE THIS EXACT TEST IN 1.54.0 and pointed it at three doors -
    "every door calls the advisory with arguments it accepts" - after
    reasoning that a call inside a broad except would fail forever in
    silence. I did not point it at the doctor and setup calls in the
    same file. So: every engine function the block calls by keyword,
    bound against the live signature.
    """
    import ast
    import importlib
    import inspect

    src = _block_source()
    tree = ast.parse(src)

    origin = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and \
                (node.module or "").startswith("equipop"):
            for alias in node.names:
                origin[alias.asname or alias.name] = (node.module,
                                                      alias.name)
    assert origin, "the block imports nothing from the engine"

    checked = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "id", None)
        if name not in origin:
            continue
        module, attr = origin[name]
        fn = getattr(importlib.import_module(module), attr, None)
        if not callable(fn) or inspect.isclass(fn):
            continue
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            continue
        kwargs, starred = {}, False
        for kw in node.keywords:
            if kw.arg is None:
                starred = True
            else:
                kwargs[kw.arg] = None
        if starred:
            continue
        try:
            sig.bind(*[None] * len(node.args), **kwargs)
        except TypeError as exc:
            raise AssertionError(
                f"equipop.ado calls {module}.{attr}("
                f"{', '.join(sorted(kwargs))}) at line {node.lineno} "
                f"of the python block, and the engine's signature is "
                f"{attr}{sig} - {exc}. This is what made BACKLOG "
                f"332's floor check dead from the Stata door for six "
                f"releases: the call raised TypeError every time and "
                f"a fallback reported without it.")
        checked += 1
    assert checked >= 1, (
        f"only {checked} engine call(s) with keywords were checked - "
        f"if the block stopped calling the engine by keyword, this "
        f"test has stopped guarding anything")


def test_the_ado_asks_whether_the_engine_takes_the_floor():
    """BROKEN WITH: dropping `min_engine=` from the ado's run() call,
    or going back to `except TypeError` around it.

    The ado half of the same finding, and break-check found both ways
    of losing it surviving the signature test above - which binds
    `run(ado_version=...)` happily, because that call IS valid. It is
    just not the call that consults the floor.

    TWO PROPERTIES. The floor must be PASSED, and the decision about
    whether the engine can take it must be ASKED rather than CAUGHT:
    a blanket `except TypeError` cannot tell a missing parameter from
    a TypeError raised deep inside the report, and it is what hid
    this for six releases by degrading in silence. When the answer is
    no, the report has to say the floor could not be checked.
    """
    import ast

    src = _block_source()
    fn = next(n for n in ast.parse(src).body
              if isinstance(n, ast.FunctionDef)
              and n.name == "_equipop_doctor_py")
    body = ast.dump(fn)

    assert "min_engine" in body, (
        "the doctor glue no longer mentions min_engine at all")
    # a run() call that passes the floor
    passes = [
        c for c in ast.walk(fn)
        if isinstance(c, ast.Call) and getattr(c.func, "id", None) == "run"
        and any(k.arg == "min_engine" for k in c.keywords)]
    assert passes, (
        "the ado never calls run() with min_engine=, so the floor it "
        "went to the trouble of declaring is not consulted - which is "
        "the state John's 10 October doctor output came from")

    # and the choice is made by asking, not by catching
    assert "signature" in body, (
        "the ado does not inspect run()'s signature - if it decides "
        "by catching TypeError instead, a TypeError from anywhere "
        "inside the report silently degrades the whole thing")
    handlers = [h for h in ast.walk(fn) if isinstance(h, ast.ExceptHandler)
                and getattr(h.type, "id", None) == "TypeError"]
    assert not handlers, (
        "a bare `except TypeError` is back around the doctor call. It "
        "cannot distinguish a missing parameter from a failure inside "
        "the report, and it degrades without saying so.")

    # the degraded path must announce itself
    assert "could not check it" in src, (
        "an engine too old to be told the floor is reported with no "
        "note saying the floor went unchecked - a silent degrade is "
        "exactly what hid this")


def test_the_doctor_is_told_which_engine_the_commands_need():
    """BROKEN WITH: the ado dropping min_engine, or run() ignoring it.

    The other half of the same finding, asserted on BEHAVIOUR rather
    than on signatures: with the floor supplied and met, the report
    says so calmly; without it, the release-number comparison speaks
    instead. John got the second where the first was correct.
    """
    from equipop import doctor

    with_floor = "\n".join(doctor.report(ado_version="99.0.0",
                                          min_engine="1.0.0"))
    assert "needs engine : 1.0.0 or newer - satisfied" in with_floor, (
        "the floor is supplied and met and the report does not say so")
    assert "OLDER THAN THE COMMANDS" not in with_floor, (
        "the floor is met and the report still warns about the "
        "release numbers - which is the message John got")

    without = "\n".join(doctor.report(ado_version="99.0.0"))
    assert "OLDER THAN THE COMMANDS" in without, (
        "with no floor to judge against, the release-number "
        "comparison is all there is and has to still appear")

    unmet = "\n".join(doctor.report(ado_version="99.0.0",
                                     min_engine="99.0.0"))
    assert "THE ENGINE IS TOO OLD FOR THESE COMMANDS" in unmet

    import inspect

    assert "min_engine" in inspect.signature(doctor.run).parameters, (
        "doctor.run does not accept min_engine, so the .ado cannot "
        "pass the floor and every report falls back to comparing "
        "release numbers")
    buf = io.StringIO()
    doctor.run(stream=buf, ado_version="99.0.0", min_engine="1.0.0")
    assert "needs engine : 1.0.0 or newer - satisfied" in buf.getvalue(), (
        "run() accepts min_engine and does not forward it to report")


def test_every_engine_symbol_the_ado_imports_exists(block):
    """BACKLOG 332's safety net, and the reason the floor is safe to
    decouple.

    Tying the floor to the release number failed loudly and early -
    pip refused. A hand-maintained floor can fail LATER and less
    clearly: if the commands start calling something new and nobody
    raises the floor, the user gets an ImportError mid-run instead.
    So the imports are checked against the installed engine here, and
    the floor's comment in the ado lists what sets it.

    This cannot prove the floor NUMBER is right - only a matrix of
    old engines could, and that is not worth building. It proves the
    calls resolve at all, which is the failure that would actually
    reach a user.
    """
    import importlib
    src = _block_source()
    # parenthesised imports may run over several lines; bare ones stop
    # at the newline. An earlier regex tried to do both at once and
    # swallowed the line after `from equipop.decay import Decay`,
    # then reported that the engine has no name `return`.
    found = re.findall(r"from (equipop[\w.]*) import \(([^)]*)\)", src)
    found += re.findall(r"from (equipop[\w.]*) import ([^(\n]+)$",
                        src, re.M)
    assert found, "no engine imports found - has the glue moved?"

    def _names(clause):
        r"""The names IMPORTED, not their local aliases.

        BACKLOG 293 found this: `from equipop.overshoot import DEFAULT
        as _OVER_DEFAULT` was read as three names - DEFAULT, `as` and
        the alias - so the test reported that the engine "has no such
        name as". The bare \w+ scan had never met an alias.
        """
        out = []
        for part in clause.split(","):
            part = part.strip()
            if not part:
                continue
            out.append(re.split(r"\s+as\s+", part)[0].strip())
        return [n for n in out if re.fullmatch(r"\w+", n)]
    for module, names in found:
        mod = importlib.import_module(module)
        for name in _names(names):
            if hasattr(mod, name):
                continue
            # A SUBMODULE rather than an attribute. `from equipop
            # import unitsize` (BACKLOG 385) is a legal import that
            # hasattr cannot see until the submodule has been loaded,
            # so a bare hasattr reported the engine was missing a name
            # it has. Importing it is the same question asked the way
            # Python asks it - and a name that really is absent still
            # fails, which is the whole point of this test.
            try:
                importlib.import_module(f"{module}.{name}")
            except Exception:
                raise AssertionError(
                    f"equipop.ado imports {name} from {module} and the "
                    f"installed engine has neither such attribute nor "
                    f"such submodule - raise eqp_min_engine, or the "
                    f"commands will fail with ImportError at run time")

    # the one call that is a KEYWORD rather than a name, so hasattr
    # cannot see it: BACKLOG 317's calibration, which is what sets
    # the floor at 1.48.0 today
    from equipop.decay import Decay
    import inspect
    assert "calibration" in inspect.signature(Decay).parameters, (
        "Decay no longer takes calibration=, which the ado passes - "
        "the floor's stated reason is out of date")


def test_repair_reinstalls_the_three_libraries_from_binaries(
        block, monkeypatch):
    """The Mac processor-mismatch case. --no-cache-dir is not
    decoration: without it pip reuses the wrong wheel it already has
    and the repair appears not to work."""
    import subprocess
    seen = {}

    def fake_run(cmd, **kw):
        seen["cmd"] = list(cmd)
        return subprocess.CompletedProcess(cmd, 0, "ok", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with redirect_stdout(io.StringIO()):
        block["_equipop_setup_py"]("repair", "1.49.3")
    for need in ("--force-reinstall", "--no-cache-dir",
                 "--only-binary=:all:", "numpy", "scipy", "pandas"):
        assert need in seen["cmd"], f"{need} missing: {seen['cmd']}"
