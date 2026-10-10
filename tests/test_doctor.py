"""BACKLOG 128 - the read-only environment report.

The doctor is the one piece of EquiPop that has to work on a machine
where EquiPop does not. So the tests are mostly about what it does
when things are broken, not when they are fine.
"""

import io as _io

import pytest

from equipop import doctor

# ---------------------------------------------------------- review F6
# RASTERIO'S DECLARED REQUIREMENTS, AS JOHN'S MACHINE HAD THEM on
# 6 October 2026 - recorded as a FIXTURE instead of read live.
#
# Three tests below used the installed rasterio as both the fixture
# AND the subject: they made `cligj` absent and then expected the
# doctor to name it, which only works while rasterio declares cligj.
# Rasterio 1.5.2 does not, so on a current environment the doctor was
# correctly silent and all three tests failed - which is why the
# 1.54.0 claim of "1,588 tests pass" did not reproduce for the
# reviewer. The pass was real; it was real about rasterio 1.4.4.
#
# The behaviour under test is EquiPop's - does it name every missing
# dependency, does it quote a constraint, does it count them - and
# none of that should move when a third party edits its packaging. So
# the metadata is supplied. These strings are the real ones from his
# case, so the field evidence is preserved rather than mocked away;
# what is gone is the dependency on what rasterio happens to declare
# today. A separate compatibility test still looks at the live
# package, and asserts only what is true of any version.
JOHNS_RASTERIO_REQUIRES = [
    "affine",
    "attrs",
    "certifi",
    "click!=8.2.*,>=4.0",
    "cligj>=0.5",
    "numpy>=1.24",
    "click-plugins",
    "pyparsing",
    # a marker, kept so these tests still prove it is SKIPPED rather
    # than guessed at (doctor._missing_requirements' own rule)
    "ipython>=2.0; extra == 'ipython'",
]


def _fixed_requires(monkeypatch, reqs=None, lib="rasterio"):
    """Make importlib.metadata.requires answer from the fixture.

    One read to patch - doctor._missing_requirements calls
    `md.requires(lib)` once - so the whole question becomes
    deterministic without touching how the doctor works.
    """
    import importlib.metadata as md

    real = md.requires

    def fake(name):
        if str(name).replace("_", "-").lower() == lib:
            return list(JOHNS_RASTERIO_REQUIRES if reqs is None else reqs)
        return real(name)

    monkeypatch.setattr(md, "requires", fake)
    # AND PROVE IT TOOK EFFECT. Break-check found that disabling this
    # patch left the three tests passing - because they then fell
    # back to the LIVE rasterio, which on this machine still declares
    # cligj. The gap only shows up on the reviewer's rasterio, which
    # is the very environment-dependence F6 is about. Returning the
    # installed list lets each test assert it is the one in force, so
    # a bypass fails everywhere rather than somewhere.
    installed = list(JOHNS_RASTERIO_REQUIRES if reqs is None else reqs)
    assert md.requires(lib) == installed, (
        "the requirement fixture is not in force - these tests would "
        "silently fall back to whatever the installed package "
        "declares, which is what review F6 was about")
    return installed


def _absent(monkeypatch, gone, present=None):
    """A COMPLETE fake installed set: `gone` is missing, everything
    else in the fixture is present, and nothing is asked of the real
    environment.

    REVIEW FINDING 2, 1.54.2. This used to force only the named
    packages absent and delegate every other lookup to the live
    environment - so the answer still depended on what happened to be
    installed. The fixture declares `click-plugins`; on a machine
    without it the doctor correctly reported FOUR missing dependencies
    where the test expected three, and the historical-case tests
    failed again on a defect that was not there. **Half of F6's fix
    was the declared requirements; this is the other half.**

    A lookup for something neither in the fixture nor in `gone` is an
    ERROR rather than a silent pass to the real environment, because a
    silent pass is how this came back a second time.
    """
    import importlib.metadata as md

    gone = {g.replace("_", "-").lower() for g in gone}
    if present is None:
        present = {_requirement_dist(spec)
                   for spec in JOHNS_RASTERIO_REQUIRES
                   if ";" not in spec}
    present = {p.replace("_", "-").lower() for p in present} - gone

    class _FakeDist:
        """Only what the doctor asks of a distribution: that it
        exists. _missing_requirements calls md.distribution(name) and
        looks at nothing on the result."""
        def __init__(self, name):
            self.name = name

    def fake(name):
        norm = str(name).replace("_", "-").lower()
        if norm in gone:
            raise md.PackageNotFoundError(name)
        if norm in present:
            return _FakeDist(norm)
        # RECORDED, NOT RAISED. `_missing_requirements` wraps this
        # call in `except Exception` and treats any failure as
        # "absent", which is right for the doctor and means an
        # exception here would be SWALLOWED exactly where it matters.
        # The autouse fixture below turns the record into a failure
        # after the test, where nothing can catch it.
        _UNACCOUNTED.append(norm)
        raise md.PackageNotFoundError(name)

    monkeypatch.setattr(md, "distribution", fake)


def _requirement_dist(spec):
    """The distribution name out of a requirement string."""
    return doctor._requirement_name(spec) or spec


#: Names `_absent` was asked about that its caller did not account
#: for. Review finding 2: a fall-through to the real environment is
#: how the second half of that finding came back after 393 fixed the
#: first, so it is now impossible to leave one unnoticed.
_UNACCOUNTED: list = []


@pytest.fixture(autouse=True)
def _no_unaccounted_lookups():
    """Fail any test whose fake installed set was incomplete.

    AFTER the test, because the doctor catches everything the lookup
    can throw. A post-condition is the only form this guard can take
    and still be reachable.
    """
    _UNACCOUNTED.clear()
    yield
    assert not _UNACCOUNTED, (
        f"the doctor was asked about {sorted(set(_UNACCOUNTED))}, "
        f"which the test's fake installed set did not account for - "
        f"the answer would have depended on what happens to be "
        f"installed on this machine (review finding 2)")


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


def test_a_missing_module_the_library_does_not_declare_invents_no_cause():
    """BROKEN WITH: returning a hint whenever the tag is MISSING_DEP,
    without checking that anything is actually missing.

    AMENDED IN 1.53.1, BACKLOG 367/370. This test used to assert that
    an ordinary ModuleNotFoundError got `tag == ""` - no advice at all -
    and that is exactly the behaviour John's machine was failed by: the
    commonest cause of a BROKEN library was the one case with nothing
    to say.

    The INTENT of the old test survives and is what is checked here,
    one level further out: do not invent a cause. A library whose own
    declared dependencies are all present, failing on some other
    module, gets the reason line and no explanation - because any
    explanation would be a guess. The tag is now set; the HINT is what
    stays silent, and the hint is what a user sees.
    """
    reason, tag = doctor._describe_failure(
        ModuleNotFoundError("No module named 'pyproj'"))
    assert tag == "MISSING_DEP"
    assert "pyproj" in reason

    # `pytest` is installed and its declared dependencies are present,
    # so there is nothing true to say about it.
    assert doctor._hint_lines("pytest", "MISSING_DEP") == [], (
        "a cause was invented for a library with no missing "
        "dependencies")


# ---------------------------------------------------------------- 367
# A BROKEN library names EVERY missing dependency, not the first one.

def test_a_broken_library_names_every_missing_dependency(monkeypatch):
    """BROKEN WITH: `return missing[:1]` in _missing_requirements.

    JOHN'S MACHINE, 6 OCTOBER 2026, AND THE WHOLE REASON FOR THIS
    RELEASE. The doctor said:

        rasterio     : BROKEN  No module named 'click'

    He installed click. pip then said rasterio also wanted attrs,
    cligj and pyparsing. Reporting the FIRST missing module is the
    wrong unit of truth - it cost three round trips to learn that a
    whole dependency set had been wiped, and the COUNT is itself the
    diagnosis: one missing package is an accident, four is an
    interrupted pip run.

    Checked against rasterio's declared metadata AS HIS MACHINE HAD
    IT, with exactly the three pip named made absent - so this
    asserts the behaviour on his case rather than on an invented one.

    REVIEW F6: that metadata is now SUPPLIED rather than read from the
    installed rasterio. It used to be read live, which made the
    installed package both the fixture and the subject: rasterio
    1.5.2 stopped declaring cligj, so the doctor was correctly silent
    and this test failed on a defect that was not there. The strings
    are still the real ones from his case.
    """
    installed = _fixed_requires(monkeypatch)
    assert any("cligj" in r for r in installed), (
        "the fixture no longer carries cligj, so this test is not "
        "about John's case any more")

    gone = {"attrs", "cligj", "pyparsing"}
    _absent(monkeypatch, gone)

    missing = doctor._missing_requirements("rasterio")
    names = {doctor._requirement_name(s) for s in missing}
    assert names == gone, (
        f"expected exactly the three pip named, got {sorted(names)}")

    lines = doctor._hint_lines("rasterio", "MISSING_DEP")
    text = "\n".join(lines)
    for pkg in sorted(gone):
        assert pkg in text, f"{pkg} is missing and the hint does not say so"
    assert "3 of this library's own declared dependencies are not" in text, (
        "the COUNT is the diagnosis - it is what distinguishes an "
        "accident from an interrupted pip run")
    # One command, not three.
    assert text.count("-m pip install") == 1


def test_an_incomplete_fake_installed_set_is_RECORDED(monkeypatch):
    """BROKEN WITH: letting `_absent` fall through to the real
    environment without recording it.

    REVIEW FINDING 2's guard, and break-check found my first version
    of it unreachable. I had `_absent` RAISE on an unknown name - but
    `_missing_requirements` wraps that call in `except Exception` and
    treats any failure as "absent", which is correct for the doctor
    and means the guard was swallowed exactly where it mattered.

    So it records instead, and an autouse fixture turns the record
    into a failure after the test, where nothing can catch it. This
    test checks the record directly, which is the only way to assert
    the mechanism without failing itself.

    The point of the guard: 393 controlled rasterio's declared
    requirements and left the installed-state lookups going to the
    live machine, so two tests failed again on a defect that was not
    there. A fall-through must not be quiet a third time.
    """
    _fixed_requires(monkeypatch)
    # deliberately incomplete: the fixture declares affine, numpy,
    # click, pyparsing and click-plugins too
    _absent(monkeypatch, {"cligj"}, present={"attrs", "certifi"})

    doctor._missing_requirements("rasterio")
    unaccounted = set(_UNACCOUNTED)
    _UNACCOUNTED.clear()          # or the autouse fixture fails too

    assert "affine" in unaccounted and "numpy" in unaccounted, (
        f"an incomplete fake set went unrecorded: {sorted(unaccounted)}")
    assert "attrs" not in unaccounted, "a declared-present name was recorded"
    assert "cligj" not in unaccounted, "a declared-absent name was recorded"

    # and the three historical tests account for everything, which is
    # what the autouse fixture proves for them on every run
    complete = {_requirement_dist(spec)
                for spec in JOHNS_RASTERIO_REQUIRES if ";" not in spec}
    assert {"affine", "numpy", "click-plugins"} <= complete, (
        "the recorded fixture no longer lists the packages whose "
        "absence from the live machine caused finding 2")


def test_the_post_condition_itself_fails_a_test(monkeypatch):
    """BROKEN WITH: `assert True` in the _no_unaccounted_lookups
    fixture.

    TESTING THE GUARD, not just the recording. Break-check found that
    neutering the fixture's assertion changed nothing, because the
    test above inspects the record directly - so the record was
    covered and the thing that turns it into a failure was not. That
    is the same shape as everything else in this review round: a
    check that exists and nothing reaches.

    The fixture's underlying generator is driven by hand here, which
    is the only way to assert that a fixture fails without failing.
    """
    gen_fn = getattr(_no_unaccounted_lookups, "__wrapped__",
                     _no_unaccounted_lookups)
    gen = gen_fn()
    next(gen)                                  # the setup half
    _UNACCOUNTED.append("something-nobody-declared")
    with pytest.raises(AssertionError, match="did not account for"):
        next(gen, None)                        # the teardown half
    _UNACCOUNTED.clear()

    # and a clean run passes through it
    gen = gen_fn()
    next(gen)
    with pytest.raises(StopIteration):
        next(gen)


def test_the_dependency_scan_still_works_on_the_INSTALLED_rasterio():
    """REVIEW F6's other half: keep the real package in view, and
    assert only what is true of ANY version of it.

    BROKEN WITH: `_missing_requirements` returning a name that is not
    in the library's declared requirements at all.

    The three tests above now supply rasterio's metadata, which is
    right - they are about EquiPop's logic. The risk in supplying it
    is the opposite failure: the fixture drifts from reality and every
    one of them passes about a world that no longer exists.

    So this one reads the LIVE package and checks the properties that
    cannot depend on its packaging: the scan returns a subset of what
    is actually declared, it skips markers, and it does not crash. It
    asserts nothing about WHICH packages rasterio wants, which is the
    thing that changed under the reviewer and broke the suite.
    """
    import importlib.metadata as md

    try:
        md.distribution("rasterio")
    except Exception:
        pytest.skip("rasterio is not installed in this environment")

    declared = md.requires("rasterio") or []
    missing = doctor._missing_requirements("rasterio")
    assert set(missing) <= set(declared), (
        f"the scan reported {sorted(set(missing) - set(declared))}, "
        f"which rasterio does not declare at all")
    assert not any(";" in spec for spec in missing), (
        "a requirement with an environment marker was reported - the "
        "doctor's own rule is to skip those rather than guess, "
        "because accusing a user of a package their platform does not "
        "want is worse than silence")
    for spec in missing:
        assert doctor._requirement_name(spec), (
            f"{spec!r} produced an empty package name")
    # and with nothing absent the hint stays quiet, whatever rasterio
    # declares today
    if not missing:
        assert doctor._hint_lines("rasterio", "MISSING_DEP") == [] or \
            all("not installed" not in ln
                for ln in doctor._hint_lines("rasterio", "MISSING_DEP")), (
            "nothing is missing and the doctor still advises about it")


def test_a_version_constraint_in_the_install_command_is_quoted():
    """BROKEN WITH: `specs = " ".join(missing)`, unquoted.

    THIS IS A WINDOWS DATA-LOSS BUG, NOT A COSMETIC ONE. `cligj>=0.5`
    pasted into cmd.exe or PowerShell REDIRECTS: the shell eats `>` and
    writes a file called `=0.5`, and pip is handed a bare `cligj`. The
    advice would appear to work, silently installing an unconstrained
    version, and leave a junk file in whatever directory the user
    happened to be standing in.

    A bare name with no constraint is left unquoted, so the common case
    still reads as something a human would type.

    REVIEW F6: `cligj>=0.5` comes from the recorded fixture rather
    than from whatever the installed rasterio declares - the point is
    that EquiPop quotes a constraint, not that rasterio has one.
    """
    import pytest as _pytest
    with _pytest.MonkeyPatch.context() as mp:
        installed = _fixed_requires(mp)
        assert any(r.startswith("cligj>=") for r in installed), (
            "the fixture no longer carries a CONSTRAINED requirement, "
            "so there is nothing for this test to check quoting on")
        _absent(mp, {"cligj", "attrs"})
        text = "\n".join(doctor._hint_lines("rasterio", "MISSING_DEP"))

    assert '"cligj>=0.5"' in text, (
        "a requirement carrying > or < must be quoted or the Windows "
        "shell treats it as a redirect")
    assert "attrs" in text and '"attrs"' not in text, (
        "a bare name needs no quotes and reads better without them")


def test_a_dependency_held_back_by_a_marker_is_not_accused(monkeypatch):
    """BROKEN WITH: dropping the `if ";" in spec: continue` guard.

    A requirement like `foo; sys_platform == "win32"` is not wanted on
    this machine, and evaluating markers needs `packaging`, which this
    file may not import. Accusing the user of a package their platform
    does not want is worse than saying nothing - the same rule
    `_as_numbers` already follows: go quiet rather than guess.
    """
    import importlib.metadata as md

    monkeypatch.setattr(md, "requires", lambda _lib: [
        "ghost_marker_dep; sys_platform == \"win32\"",
        "ghost_extra_dep; extra == \"docs\"",
        "ghost_plain_dep",
    ])
    monkeypatch.setattr(
        md, "distribution",
        lambda name: (_ for _ in ()).throw(md.PackageNotFoundError(name)))

    missing = doctor._missing_requirements("rasterio")
    names = {doctor._requirement_name(s) for s in missing}
    assert names == {"ghost_plain_dep"}, (
        f"a marked requirement was accused: {sorted(names)}")


def test_the_requirement_name_is_stripped_of_its_constraint():
    """BROKEN WITH: `return spec.split('>')[0]` only."""
    cases = {
        "cligj>=0.5": "cligj",
        "click!=8.2.*,>=4.0": "click",
        "click-plugins": "click-plugins",
        "numpy>=1.24": "numpy",
        "foo[bar]==1.0": "foo",
        "baz ~= 2.1": "baz",
    }
    for spec, want in cases.items():
        assert doctor._requirement_name(spec) == want, spec


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

def test_the_floor_is_what_the_doctor_judges_against():
    """BACKLOG 332. Two version numbers on screen, and NEITHER of
    them is the question. What matters is the engine the commands
    actually need, which the ado now states.

    So the ordinary case - engine ahead of commands, which is what
    `equipop setup` produces and what confused Kit Baum - has nothing
    to report beyond one satisfied line. No paragraph explaining
    itself, because there is nothing to explain.
    """
    text = "\n".join(doctor.report(ado_version="1.49.3",
                                   min_engine="1.48.0"))
    assert "1.48.0 or newer - satisfied" in text, text
    assert "MISMATCH" not in text
    assert "nothing to fix" not in text, (
        "the old reassurance is still being printed - with a floor "
        "there is no difference to reassure anybody about")


def test_an_engine_below_the_floor_is_refused_loudly():
    """The one case that breaks: the commands call something the
    engine does not have."""
    text = "\n".join(doctor.report(ado_version="1.49.3",
                                   min_engine="99.0.0"))
    assert "TOO OLD FOR THESE COMMANDS" in text
    assert "ImportError" in text
    assert "equipop setup" in text


def test_a_floor_the_doctor_cannot_read_is_not_guessed_at():
    for odd in ("", "dev", "1.x.4"):
        text = "\n".join(doctor.report(ado_version="1.49.3",
                                       min_engine=odd))
        assert "TOO OLD" not in text, f"{odd!r} produced a verdict"


def test_an_engine_older_than_the_commands_is_named_and_explained():
    """The direction that actually breaks. Commands written against an
    engine that is not installed yet call a function that is not there,
    which arrives as an ImportError and looks like our bug."""
    text = "\n".join(doctor.report(ado_version="99.0.0"))
    assert "OLDER THAN THE COMMANDS" in text
    assert "ImportError" in text
    assert "equipop setup" in text, (
        "the loud message must name the one-line fix")


def test_an_engine_newer_than_the_commands_is_not_alarming():
    """BACKLOG 330, KIT BAUM ON THE SSC RELEASE. He followed the
    manuscript exactly - `equipop setup`, full restart of Stata - and
    the doctor told him he had a VERSION MISMATCH to repair. He did
    not. He had commands 1.48.2 from SSC and engine 1.49.1 from pip,
    which is what `equipop setup` ASKS FOR: it installs
    equipop>=<ado version>, so pip takes the newest there is, and PyPI
    runs ahead of SSC by design.

    The package shipped an installer that creates a state and a
    diagnostic that calls that state a fault. This test holds the two
    to the same story.
    """
    text = "\n".join(doctor.report(ado_version="0.0.1"))
    assert "MISMATCH" not in text, (
        "the expected outcome of our own installer is still being "
        f"reported as a fault:\n{text}")
    assert "ImportError" not in text, (
        "a harmless state must not be illustrated with the error "
        "message from the harmful one")
    assert "nothing to fix" in text, (
        "silence is not enough - the two version lines differ on "
        "screen, so the reason must be there too")
    assert "equipop>=0.0.1" in text, (
        "the note should quote what setup actually asked pip for")


def test_an_unreadable_version_makes_the_doctor_go_quiet():
    """Better no comment than a comparison it could not make."""
    for odd in ("", "dev", "1.x.4", "unknown"):
        text = "\n".join(doctor.report(ado_version=odd))
        assert "MISMATCH" not in text and "OLDER THAN" not in text, (
            f"ado version {odd!r} produced a verdict anyway")


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


def test_the_citation_version_matches_the_package():
    """BACKLOG 43. CITATION.cff sat at 1.0.0 for forty releases
    because nothing checked it - an eighth place a version lives.

    Only the `version:` field moves. The preferred-citation is the 2014
    report and records where the work was written; it is not updated
    when the software changes or when an author moves institution.
    """
    import os
    import re

    import equipop

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cff = open(os.path.join(here, "CITATION.cff"), encoding="utf-8").read()

    m = re.search(r"^version: (\S+)", cff, re.M)
    assert m, "CITATION.cff no longer declares a version"
    assert m.group(1) == equipop.__version__, (
        f"CITATION.cff says {m.group(1)}, the package says "
        f"{equipop.__version__}")
    assert "year: 2014" in cff, (
        "the preferred citation is the 2014 report and must not be "
        "moved to the software's release year")


# ---------------------------------------------------------------- 368
# A tag that is classified and tested must actually be PRINTED.

def test_the_dll_hint_reaches_the_report(monkeypatch):
    """BROKEN WITH: removing the `tag == "DLL"` branch from
    _hint_lines - i.e. putting the code back how it was.

    THE TEST THAT SHOULD HAVE EXISTED SINCE 1.35. `_describe_failure`
    classified "DLL load failed" as its own case and
    `test_a_windows_dll_failure_is_recognised_separately` asserted the
    classification - and for its entire life NOTHING PRINTED ANYTHING,
    because only `tag == "ARCH"` was ever rendered. The old test could
    not catch it: it asserted the MECHANISM (a tag is computed) and
    never the CONSEQUENCE (a user reads advice). On Windows this is the
    most likely way rasterio, geopandas and pyproj fail, so the case
    that most needed advice was the one case with none.
    """
    monkeypatch.setattr(
        doctor, "_probe",
        lambda name: ("BROKEN", WINDOWS_DLL_ERROR.splitlines()[0], "DLL"))

    text = "\n".join(doctor.report())
    assert "MISSING SYSTEM LIBRARY" in text, (
        "the DLL case is classified and tested and still prints no "
        "advice - which is the defect this release exists to fix")
    assert "--only-binary" in text
    assert "CLOSED" in text, (
        "a file held open by a running Python or Pro is how the "
        "half-installed state happens in the first place")


def test_every_tag_that_can_be_classified_has_something_to_say():
    """BROKEN WITH: adding a tag to _describe_failure with no branch in
    _hint_lines - which is precisely the state 1.53.0 shipped in.

    THE PROPERTY, NOT A CASE. The DLL gap survived because the suite
    tested the tags it knew about one at a time, so a tag with no
    renderer was invisible. This asserts the relationship instead:
    every tag the classifier can produce must produce output. A new tag
    with no hint fails here on the day it is written, rather than in
    somebody's terminal eight releases later.
    """
    import re
    src = open(doctor.__file__, encoding="utf-8").read()
    body = src[src.index("def _describe_failure"):src.index("def _requirement_name")]
    tags = {m for m in re.findall(r'return first, "([A-Z_]+)"', body)}
    assert tags, "no tags found - the scrape above has gone stale"
    assert {"ARCH", "DLL", "MISSING_DEP"} <= tags

    for tag in sorted(tags):
        if tag == "MISSING_DEP":
            # Needs a library with something genuinely missing; covered
            # by its own test. Here only that the branch exists.
            assert f'tag == "{tag}"' in src, (
                f"{tag} is classified but _hint_lines has no branch "
                "for it")
            continue
        lines = doctor._hint_lines("rasterio", tag)
        assert lines, (
            f"_describe_failure can return {tag!r} and _hint_lines "
            "prints nothing for it - a classified, tested, invisible "
            "case")


def test_the_hint_is_rendered_from_one_place():
    """BROKEN WITH: re-inlining `_ARCH_HINT.format(...)` into the
    REQUIRED and OPTIONAL loops, as 1.53.0 had it.

    354'S LESSON, ONE RELEASE LATER, IN A DIFFERENT FILE. The ARCH hint
    was rendered by two open-coded copies of the same `if`, and the DLL
    hint by neither - a rule written twice is a rule that gets extended
    once. Both sections must read the same function, so adding a tag is
    one edit in one place.
    """
    src = open(doctor.__file__, encoding="utf-8").read()
    report_body = src[src.index("def report("):]
    assert "_ARCH_HINT.format" not in report_body, (
        "report() formats a hint itself again - put it in _hint_lines "
        "so both sections share it")
    assert report_body.count("_hint_lines(lib, tag)") == 2, (
        "both REQUIRED and OPTIONAL must render hints through the one "
        "helper")


# ---------------------------------------------------------------- 369
# A half-deleted package is the root cause, and it is visible.

def _fake_site(tmp_path, names):
    d = tmp_path / "site-packages"
    d.mkdir()
    for n in names:
        (d / n).mkdir()
    return d


def test_a_half_deleted_package_is_reported(tmp_path, monkeypatch):
    """BROKEN WITH: `if name.startswith("~.")` - i.e. never matching.

    JOHN'S ACTUAL ROOT CAUSE, and it was printed five times by pip
    while reading as noise:

        WARNING: Ignoring invalid distribution ~yproj

    `~yproj` is what pip leaves when it cannot delete `pyproj`: it
    renames the directory with a `~` prefix and carries on. That means
    a pip run DID NOT FINISH - which is why four of rasterio's
    dependencies went missing together instead of one going missing
    alone. It was visible from inside Python the whole time.
    """
    d = _fake_site(tmp_path, ["~yproj", "pyproj", "numpy"])
    monkeypatch.setattr(doctor, "_package_dirs", lambda: [str(d)])

    found = doctor._leftovers()
    assert [n for _dir, n in found] == ["~yproj"], (
        f"expected only the ~ entry, got {found}")

    text = "\n".join(doctor._lines_leftovers())
    assert "LEFTOVERS" in text
    assert "~yproj" in text
    assert "DID NOT FINISH" in text, (
        "the point is not tidiness - it is that this explains the "
        "missing dependencies above it")
    listed = [ln.strip() for ln in text.splitlines()
              if ln.startswith("  ") and not ln.startswith("       ")]
    assert "pyproj" not in listed and "numpy" not in listed, (
        f"a healthy package was listed as a leftover: {listed}")


def test_a_clean_installation_says_nothing_about_leftovers(tmp_path,
                                                           monkeypatch):
    """BROKEN WITH: returning the LEFTOVERS header unconditionally.

    Every healthy machine runs this. A section that appears when there
    is nothing to report teaches users to skip it, and then it is not
    read on the one machine where it matters.
    """
    d = _fake_site(tmp_path, ["numpy", "pandas"])
    monkeypatch.setattr(doctor, "_package_dirs", lambda: [str(d)])
    assert doctor._leftovers() == []
    assert doctor._lines_leftovers() == []
    assert "LEFTOVERS" not in "\n".join(doctor.report())


def test_the_leftovers_come_before_the_libraries(tmp_path, monkeypatch):
    """BROKEN WITH: appending _lines_leftovers() after the VERDICT.

    Ordering is this file's whole design - see
    test_the_interpreter_path_is_printed_before_any_library_is_touched.
    The leftover is the CAUSE and the broken library is the SYMPTOM, so
    a user scrolling from the top meets the explanation first. It is
    also cheap and cannot crash, which is the other reason it belongs
    above anything that imports.
    """
    d = _fake_site(tmp_path, ["~yproj"])
    monkeypatch.setattr(doctor, "_package_dirs", lambda: [str(d)])

    lines = [ln.lower() for ln in doctor.report()]
    left = next(i for i, ln in enumerate(lines) if "leftovers" in ln)
    first_probe = next(i for i, ln in enumerate(lines)
                       if any(lib in ln for lib in doctor.REQUIRED))
    assert left < first_probe, (
        "the cause is printed after the symptom")


def test_leftovers_are_named_and_never_removed(tmp_path, monkeypatch):
    """BROKEN WITH: adding shutil.rmtree to _leftovers.

    The report's first line promises "nothing is changed". A deletion
    here would be in the one directory a user cannot afford to have
    guessed at, from a command they ran to ASK A QUESTION.
    """
    d = _fake_site(tmp_path, ["~yproj", "~umpy"])
    monkeypatch.setattr(doctor, "_package_dirs", lambda: [str(d)])

    doctor._leftovers()
    doctor._lines_leftovers()
    doctor.report()
    assert (d / "~yproj").is_dir() and (d / "~umpy").is_dir(), (
        "the doctor deleted something - it is read-only")


def test_an_unreadable_package_directory_does_not_crash_the_doctor(
        monkeypatch):
    """BROKEN WITH: dropping the try/except around os.listdir.

    The doctor runs on broken machines by definition. A permission
    error while scanning must not take down the report that was called
    to explain the problem.
    """
    monkeypatch.setattr(doctor, "_package_dirs",
                        lambda: ["/definitely/not/a/directory/here"])
    assert doctor._leftovers() == []
    assert "VERDICT" in "\n".join(doctor.report())


# ------------------------------------------------- 367 + 369 together
def test_johns_machine_is_explained_in_one_run(tmp_path, monkeypatch):
    """BROKEN WITH: either half alone - no leftover scan, or only the
    first missing dependency named.

    THE ACCEPTANCE TEST FOR THE WHOLE RELEASE. His machine needed three
    exchanges to explain: the doctor named click, pip then named attrs,
    cligj and pyparsing, and the `~yproj` line that said WHY was
    printed as a warning nobody reads. One report must now carry all of
    it - what is missing, all of it, and the interrupted pip run that
    took it away.

    REVIEW F6: the requirement list is the recorded fixture, so this
    acceptance test keeps asserting what the release was for without
    depending on rasterio's current packaging.
    """
    d = _fake_site(tmp_path, ["~yproj", "rasterio"])
    monkeypatch.setattr(doctor, "_package_dirs", lambda: [str(d)])

    installed = _fixed_requires(monkeypatch)
    assert any("cligj" in r for r in installed)
    gone = {"attrs", "cligj", "pyparsing", "click"}
    _absent(monkeypatch, gone)
    monkeypatch.setattr(doctor, "_probe", lambda name: (
        ("BROKEN", "No module named 'click'", "MISSING_DEP")
        if name == "rasterio" else ("ok", "9.9.9", "")))

    text = "\n".join(doctor.report())

    assert "~yproj" in text, "the root cause is still invisible"
    for pkg in sorted(gone):
        assert pkg in text, f"{pkg} is missing and the report is silent"
    assert "4 of this library's own declared dependencies are not" in text
    assert "interrupted" in text.lower()
    assert "not an" in text and "EquiPop fault" in text, (
        "a user whose rasterio dependencies were wiped should not be "
        "left wondering whether EquiPop did it")


# ---------------------------------------------------------------- 371
def test_a_broken_optional_is_named_in_the_verdict(monkeypatch):
    """BROKEN WITH: dropping the broken_optional loop from the verdict.

    John's report ended:

        VERDICT
          machine 1 can run in this Python.

    directly below `rasterio : BROKEN`. The sentence is TRUE - machine
    1 needs none of the optional libraries - and it is the last thing
    on screen, so it reads as "all fine" to somebody whose work is
    almost entirely rasters. The verdict now still answers the machine
    1 question and then says what is broken anyway.
    """
    monkeypatch.setattr(doctor, "_probe", lambda name: (
        ("BROKEN", "DLL load failed while importing _gdal", "DLL")
        if name == "rasterio" else ("ok", "9.9.9", "")))

    lines = doctor.report()
    tail = "\n".join(lines[lines.index("VERDICT"):])
    assert "machine 1 can run" in tail, (
        "the machine 1 answer is still the verdict and must not be "
        "replaced")
    assert "rasterio" in tail and "BROKEN" in tail, (
        "a broken library is invisible in the verdict - which is how a "
        "true sentence reads as 'all fine'")
    assert "rasters" in tail, (
        "name the capability that is lost, not just the package")


def test_an_absent_optional_is_not_treated_as_a_fault(monkeypatch):
    """BROKEN WITH: `if state != "ok"` instead of `if state ==
    "BROKEN"` in the verdict loop.

    The OPTIONAL heading promises that "absent only means the feature
    is unavailable". A verdict that complains about every library a
    user chose not to install breaks that promise and makes a healthy
    machine look faulty - geopandas is absent on this very container
    by choice.
    """
    monkeypatch.setattr(doctor, "_probe", lambda name: (
        ("absent", "not installed in this Python", "")
        if name == "geopandas" else ("ok", "9.9.9", "")))

    lines = doctor.report()
    tail = "\n".join(lines[lines.index("VERDICT"):])
    assert "geopandas" not in tail, (
        "an absent optional library is a choice, not a fault")
    assert "BROKEN" not in tail
