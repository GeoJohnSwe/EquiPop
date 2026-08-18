"""BACKLOG 128 - the read-only environment report.

The doctor is the one piece of EquiPop that has to work on a machine
where EquiPop does not. So the tests are mostly about what it does
when things are broken, not when they are fine.
"""

import io as _io

import pytest

from equipop import doctor


# The real message macOS produces when a library built for Intel is
# loaded by an Apple-Silicon Python. This is Umut's, from 1.37, with
# the path shortened.
MACOS_ARCH_ERROR = (
    "dlopen(/Users/x/Library/Python/3.10/lib/python/site-packages/"
    "pandas/_libs/pandas_parser.cpython-310-darwin.so, 0x0002): tried: "
    "'.../pandas_parser.cpython-310-darwin.so' (mach-o file, but is an "
    "incompatible architecture (have 'x86_64', need 'arm64e' or "
    "'arm64'))"
)

WINDOWS_DLL_ERROR = (
    "DLL load failed while importing _multiarray_umath: The specified "
    "module could not be found."
)


def test_the_report_runs_and_says_something_about_each_library():
    lines = doctor.report()
    text = "\n".join(lines)
    for lib in doctor.REQUIRED:
        assert lib in text, f"{lib} is not mentioned in the report"
    for lib, _why in doctor.OPTIONAL:
        assert lib in text
    assert "VERDICT" in text


def test_the_interpreter_path_is_printed_before_any_library_is_touched():
    """Ordering is the whole design.

    On Windows with Anaconda, importing numpy does not raise - it closes
    Stata. Whatever reached the screen first is the only evidence, and
    the interpreter path is the thing that has to change. So it must
    come before any probe.
    """
    lines = doctor.report()
    joined = [ln.lower() for ln in lines]
    exe = next(i for i, ln in enumerate(joined) if "executable" in ln)
    first_probe = next(i for i, ln in enumerate(joined)
                       if any(lib in ln for lib in doctor.REQUIRED))
    assert exe < first_probe, (
        "a library is probed before the interpreter path is printed - "
        "if the probe kills the process the user learns nothing")


def test_a_processor_mismatch_is_named_as_one():
    """Umut's Mac. The raw message is 40 lines of dlopen paths and the
    words that matter are buried in the middle of it."""
    reason, tag = doctor._describe_failure(ImportError(MACOS_ARCH_ERROR))
    assert tag == "ARCH"
    assert reason  # a single line, not the whole wall
    assert "\n" not in reason


def test_a_windows_dll_failure_is_recognised_separately():
    reason, tag = doctor._describe_failure(ImportError(WINDOWS_DLL_ERROR))
    assert tag == "DLL"
    assert "\n" not in reason


def test_an_ordinary_missing_module_gets_no_special_advice():
    reason, tag = doctor._describe_failure(
        ModuleNotFoundError("No module named 'pyproj'"))
    assert tag == ""
    assert "pyproj" in reason


def test_the_arch_hint_names_the_library_it_is_about():
    hint = doctor._ARCH_HINT.format(lib="pandas")
    assert "pandas" in hint
    assert "--force-reinstall" in hint
    assert "--no-cache-dir" in hint, (
        "without --no-cache-dir pip reuses the wrong-processor wheel it "
        "already downloaded and the fix appears not to work")


def test_a_library_that_raises_on_import_is_reported_not_propagated(
        monkeypatch):
    """The case the doctor exists for.

    If a broken library made the doctor raise, the user would get the
    same unexplained traceback they called it to understand.
    """
    def explode(name):
        raise ImportError(MACOS_ARCH_ERROR)

    monkeypatch.setattr(doctor.importlib, "import_module", explode)
    state, detail, tag = doctor._probe("pandas")
    assert state == "BROKEN"
    assert tag == "ARCH"

    lines = doctor.report()
    text = "\n".join(lines)
    assert "CANNOT run" in text
    assert "PROCESSOR MISMATCH" in text


def test_a_library_that_kills_more_than_an_importerror_is_still_caught(
        monkeypatch):
    """Compiled libraries fail in exotic ways - a bad build can raise
    SystemError or RuntimeError rather than ImportError. Anything the
    process survives should become a line, not a traceback."""
    def explode(name):
        raise RuntimeError("something went wrong deep in a .so")

    monkeypatch.setattr(doctor.importlib, "import_module", explode)
    state, _detail, _tag = doctor._probe("numpy")
    assert state == "BROKEN"


def test_an_absent_library_is_absent_not_broken():
    state, detail, _tag = doctor._probe("a_library_nobody_has_installed")
    assert state == "absent"
    assert "not installed" in detail


def test_run_writes_every_line_and_flushes():
    """The flush is not tidiness: an unflushed buffer dies with the
    process, and the process dying is the scenario."""
    flushes = []

    class Watched(_io.StringIO):
        def flush(self):
            flushes.append(len(self.getvalue()))

    out = Watched()
    doctor.run(stream=out)
    written = out.getvalue()
    assert written.count("\n") == len(doctor.report())
    assert len(flushes) == len(doctor.report()), (
        "lines are not flushed one at a time")


def test_the_verdict_is_positive_when_the_three_are_present():
    lines = doctor.report()
    verdict = "\n".join(lines).split("VERDICT")[1]
    if all(doctor._probe(lib)[0] == "ok" for lib in doctor.REQUIRED):
        assert "can run" in verdict
    else:                                       # pragma: no cover
        pytest.skip("this environment is missing a required library")


# --------------------------------------------------------------------
# The two-part update - v1.40.1
# --------------------------------------------------------------------

def test_a_version_mismatch_is_named_and_explained():
    """The .ado files and the Python package are installed separately,
    by net install and by pip. Updating one and not the other is the
    single most frequent field failure this project has, and it
    surfaces as an ImportError that looks like our bug."""
    text = "\n".join(doctor.report(ado_version="0.0.1"))
    assert "VERSION MISMATCH" in text
    assert "net install" in text and "pip" in text
    assert "ImportError" in text


def test_matching_versions_say_nothing_about_it():
    """A warning that fires when nothing is wrong teaches people to
    ignore warnings."""
    import equipop
    text = "\n".join(doctor.report(ado_version=equipop.__version__))
    assert "MISMATCH" not in text


def test_no_ado_version_given_is_not_a_mismatch():
    """python -m equipop.doctor has no .ado to ask."""
    assert "MISMATCH" not in "\n".join(doctor.report())


def test_the_seventh_version_string_agrees_with_the_other_six():
    """The .ado now carries its own version so the doctor can compare.
    That is a seventh place a version lives, and the only thing
    stopping it drifting is this test."""
    import os
    import re

    import equipop

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ado = open(os.path.join(here, "stata", "equipop.ado"),
               encoding="utf-8").read()

    declared = re.search(r'local eqp_ado_version "([^"]+)"', ado)
    assert declared, "the .ado no longer declares its version"
    assert declared.group(1) == equipop.__version__, (
        f"the .ado says {declared.group(1)}, the package says "
        f"{equipop.__version__} - the doctor would report a mismatch "
        f"on a correct installation")

    header = re.search(r"^\*! equipop v(\S+)", ado, re.M)
    assert header and header.group(1) == equipop.__version__, (
        "line 1 of the .ado disagrees with the package version")
