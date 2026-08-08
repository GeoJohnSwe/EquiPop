"""What we SHIP has to contain what it needs.

This file exists because of a bug that could not fail inside the
repository. `load("gridby")` - the first line of the Book's chapter
1 - reached out to ../examples and ../tests. Both are there in a git
clone and in the source archive, and neither is in a wheel, so every
student who installed EquiPop from PyPI got ModuleNotFoundError on
their first command. The test suite could never have caught it,
because the test suite runs inside the repository, where the folders
are right there.

So these tests check the SHAPE of what gets installed rather than
behaviour: nothing the package needs at run time may live outside
the package, and anything added to equipop/data must be declared or
it will silently not travel.
"""
import os
import re

import pytest

import equipop
from equipop import datasets

PKG = os.path.dirname(os.path.abspath(equipop.__file__))
ROOT = os.path.dirname(PKG)


def test_the_data_folder_is_inside_the_package():
    """Not ../tests, not ../examples - inside, or it will not ship."""
    d = os.path.abspath(datasets._DATA)
    assert d.startswith(PKG + os.sep), (
        f"datasets._DATA resolves to {d}, which is outside the "
        f"package at {PKG} - it will not be in the wheel")


@pytest.mark.parametrize("name", ["gridby", "municipality"])
def test_the_datasets_the_book_teaches_from_load(name):
    """These two are what the Book asks the reader to type: gridby
    15 times, municipality 3."""
    got = datasets.load(name)
    assert got is not None


def test_gridby_needs_no_file_at_all():
    """The teaching town is GENERATED from seed 1848, so it costs the
    wheel nothing but a module. Guarding that: if it ever grows a
    data file, this fails and someone has to declare it."""
    from equipop import gridby as G
    assert G.SEED == 1848
    src = open(os.path.join(PKG, "gridby.py")).read()
    assert "read_csv" not in src and "read_excel" not in src


def test_every_shipped_data_file_is_declared():
    """A file dropped into equipop/data that no pattern in
    pyproject.toml matches will simply not travel - and it will still
    work perfectly for everyone testing inside the repo."""
    toml = open(os.path.join(ROOT, "pyproject.toml")).read()
    block = toml.split("[tool.setuptools.package-data]", 1)
    assert len(block) == 2, "package-data section has gone missing"
    patterns = re.findall(r'"data/\*(\.[a-z]+)"', block[1])
    assert patterns, "no data patterns declared"
    present = {os.path.splitext(f)[1]
               for f in os.listdir(datasets._DATA)
               if not f.startswith(".")}
    undeclared = present - set(patterns)
    assert not undeclared, (
        f"equipop/data holds {sorted(undeclared)} but pyproject "
        f"declares only {sorted(set(patterns))} - those files will "
        "not be installed")


def test_the_loader_never_reaches_above_the_package_at_import_time():
    """One exception is allowed and documented: the Stata door's
    test fixture, which belongs to the Stata door rather than to the
    Python package - and which refuses with an explanation naming
    where to get it."""
    src = open(os.path.join(PKG, "datasets.py")).read()
    escapes = re.findall(r'"\.\."', src)
    assert len(escapes) <= 1, (
        f"{len(escapes)} paths escape the package; only the Stata "
        "fixture may, and it must explain itself")
    if escapes:
        assert "stata" in src.lower()


def test_the_stata_fixture_refuses_by_explaining_where_to_get_it():
    p = os.path.join(PKG, "..", "stata", "stata_test_data.dta")
    if os.path.exists(p):
        pytest.skip("running inside the repo, where the file exists")
    with pytest.raises(FileNotFoundError) as e:
        datasets.load("stata_test")
    assert "source archive" in str(e.value)


def test_every_helper_the_tests_import_is_named_in_the_manifest():
    """v1.29.0. The tests import helpers that are NOT named test*.py -
    qgis_stub (the simulated PyQGIS) and door_parity (the shared box
    list). setuptools ships test*.py by an old default and nothing
    else, so from 1.20.0 to 1.28.0 every published archive failed to
    collect its own suite with `No module named 'qgis_stub'`. The
    archive is built by a tool we do not run here, so this guards the
    RULE instead: whatever the tests import from their own directory
    must be claimed by MANIFEST.in."""
    here = os.path.dirname(os.path.abspath(__file__))
    manifest = open(os.path.join(here, "..", "MANIFEST.in"),
                    encoding="utf-8").read()
    helpers = [f[:-3] for f in os.listdir(here)
               if f.endswith(".py") and not f.startswith("test_")]
    assert helpers, "expected at least qgis_stub and door_parity"
    imported = set()
    for f in os.listdir(here):
        if not f.startswith("test_") or not f.endswith(".py"):
            continue
        src = open(os.path.join(here, f), encoding="utf-8").read()
        for h in helpers:
            if re.search(rf"^\s*(import {h}\b|from {h} import)",
                         src, re.M):
                imported.add(h)
    assert imported, "no test imports a local helper - has the layout changed?"
    # match whole DIRECTIVE LINES: "graft tests/data" contains the
    # substring "graft tests" and would wave this through - the first
    # version of this test did exactly that and passed against a
    # manifest with the line deleted.
    lines = [l.strip() for l in manifest.split("\n")]
    claimed = any(re.fullmatch(r"(include tests/\*\.py|graft tests)", l)
                  for l in lines)
    assert claimed, (
        f"the tests import {sorted(imported)} from their own folder, "
        "but MANIFEST.in does not carry tests/*.py - the published "
        "archive will not be able to collect its own suite")


def test_every_version_string_in_the_repo_agrees():
    """v1.29.1. The 1.29.0 release bumped three version strings and
    missed a fourth - qgis/equipop_qgis/__init__.py stayed at 1.28.0.
    Nothing broke, but check_versions() then told John his halves were
    a release apart when they were not: the guard built to catch a
    real mismatch cried wolf, on the very morning a real mismatch had
    cost him an hour. A warning that fires when nothing is wrong gets
    scrolled past.

    The cause was checking the places one REMEMBERS. So this asks the
    repository instead."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    sources = {
        "pyproject.toml": r'^version\s*=\s*"([^"]+)"',
        os.path.join("equipop", "__init__.py"): r'^__version__\s*=\s*"([^"]+)"',
        os.path.join("qgis", "equipop_qgis", "__init__.py"):
            r'^__version__\s*=\s*"([^"]+)"',
        os.path.join("qgis", "equipop_qgis", "metadata.txt"):
            r'^version\s*=\s*(.+)$',
    }
    found = {}
    for rel, pattern in sources.items():
        path = os.path.join(root, rel)
        assert os.path.exists(path), f"{rel} has moved - update this test"
        m = re.search(pattern, open(path, encoding="utf-8").read(), re.M)
        assert m, f"no version string found in {rel}"
        found[rel] = m.group(1).strip()
    assert len(set(found.values())) == 1, (
        "the version strings disagree: "
        + "; ".join(f"{k} = {v}" for k, v in sorted(found.items())))


def test_the_stub_audit_travels_with_the_code_it_checks():
    """v1.29.1. tools/stub_audit.py is the only check that can catch
    the simulator promising methods QGIS does not have - the fault
    that let `isAdvanced()` ship. BACKLOG 80 requires it to be run in
    a live QGIS each release, which is impossible if the archive does
    not carry it. The first 1.29.1 build did not."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    tool = os.path.join(root, "tools", "stub_audit.py")
    assert os.path.exists(tool), "tools/stub_audit.py has gone"
    manifest = open(os.path.join(root, "MANIFEST.in"),
                    encoding="utf-8").read()
    lines = [l.strip() for l in manifest.split("\n")]
    assert any(re.fullmatch(r"(graft tools|include tools/\*\.py)", l)
               for l in lines), \
        "MANIFEST.in does not carry tools/ - the audit will not ship"


def test_metadata_declares_no_file_it_does_not_ship():
    """BACKLOG 79: metadata.txt declared `icon=icon.png` from the very
    first release and the file never existed - not in the repo, not in
    the 1.28.0 zip, not in 1.29.0. QGIS shrugs at a missing icon, so
    nothing ever complained, and it would have blocked a submission to
    the plugin repository. Shipped in 1.29.5. This test is the part
    that matters: the promise cannot quietly lapse again, and it now
    covers every file metadata.txt names, not just this one.
    """
    plugin = os.path.join(ROOT, "qgis", "equipop_qgis")
    meta = os.path.join(plugin, "metadata.txt")
    missing = []
    for line in open(meta, encoding="utf-8"):
        key, _, value = line.partition("=")
        value = value.strip()
        if (key.strip() in {"icon", "about_icon"} or
                value.lower().endswith((".png", ".svg", ".ico"))):
            if value and not os.path.exists(os.path.join(plugin, value)):
                missing.append(f"{key.strip()}={value}")
    assert not missing, (
        f"metadata.txt promises files the plugin does not ship: "
        f"{missing}")
