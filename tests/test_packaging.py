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


def test_every_runner_at_the_root_is_carried_by_the_manifest():
    """v1.47. The sdist for 1.46.4 carried NONE of run_fetch.py,
    run_raster_folder.py or run_osm_friction.py. MANIFEST.in had
    gained `include demo_*.py` for BACKLOG 107 and nothing for the
    runners, so the pattern the file's own comments describe three
    times happened a fourth.

    It mattered most for run_osm_friction.py. BACKLOG 283 records
    that it is THE ONLY WAY to reach the OSM lattice engine, because
    no door wraps it - so the source archive shipped the headline
    feature of 1.46.0 and 1.46.1 with no way to run it.

    Checked against the FILES ON DISK rather than a fixed list, so a
    runner added later is covered without anyone remembering to come
    back here.
    """
    runners = sorted(f for f in os.listdir(ROOT)
                     if re.fullmatch(r"run_.*\.py", f))
    assert runners, "no run_*.py at the root - has the naming changed?"
    manifest = open(os.path.join(ROOT, "MANIFEST.in"),
                    encoding="utf-8").read()
    lines = [l.strip() for l in manifest.split("\n")]
    covered = any(re.fullmatch(r"include run_\*\.py", l) for l in lines)
    if not covered:
        missing = [f for f in runners
                   if not any(l == f"include {f}" for l in lines)]
        assert not missing, (
            f"MANIFEST.in does not carry {missing} - the source "
            "archive will ship a runner-less copy, which is how "
            "1.46.4 shipped the OSM work with no way to run it")


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


def test_the_plugin_carries_what_the_repository_requires():
    """BACKLOG 131. Two things the QGIS plugin repository checks that
    EquiPop did not ship: a LICENSE file INSIDE the plugin folder (the
    repo does not look at the one in the project root), and
    hasProcessingProvider=yes, without which neither the repository
    nor QGIS describes the plugin correctly. Both absent since the
    first release; neither noticed, because a locally installed
    plugin works fine without them.
    """
    plugin = os.path.join(ROOT, "qgis", "equipop_qgis")
    assert os.path.exists(os.path.join(plugin, "LICENSE")), \
        "the plugin folder has no LICENSE - the repository requires one"
    meta = open(os.path.join(plugin, "metadata.txt"),
                encoding="utf-8").read()
    assert "hasProcessingProvider=yes" in meta, \
        "metadata.txt does not declare hasProcessingProvider"


def test_the_release_zip_builder_refuses_unextractable_names():
    """BACKLOG 156. The 1.29.6 release ZIP could not be opened on
    Windows: five members were named
    "EquiPop-1.29.6/C:\\Data\\...\\gridby_points_EquiPop_run.csv",
    because the suite writes run manifests into the working directory
    (BACKLOG 101) and the zip was built from the whole tree.

    The clean-up HAD been run - before the tests, which recreated the
    files. So the fix is not to remember the right order; it is to
    make the builder refuse. This checks that it does.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_mkzip", os.path.join(ROOT, "tools", "make_release_zip.py"))
    mk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mk)

    good = ["equipop/cells.py", "docs/book/ch1.md", "README.md"]
    mk.check(good)                       # must not raise

    for bad in ("C:\\Data\\x_EquiPop_run.csv",
                "equipop\\cells.py",
                "/etc/passwd",
                "../outside.txt",
                "docs/a:b.md"):
        with pytest.raises(SystemExit) as e:
            mk.check(good + [bad])
        assert "REFUSING" in str(e.value), bad


def test_every_module_a_shipped_runner_imports_is_in_the_wheel():
    """BACKLOG 241. run_fetch.py was delivered importing
    equipop.doors.fetching, which existed in the working tree and in
    NO WHEEL - so John got ModuleNotFoundError on his first command.

    A runner is useless without the module it drives, and 'it works in
    my tree' is not shipping. This walks every top-level runner's
    imports and checks the package really provides them.
    """
    import ast
    import importlib.util

    from pathlib import Path as _P
    runners = sorted(_P(ROOT).glob("run_*.py"))
    assert runners, "no runners found - has the naming changed?"
    for r in runners:
        tree = ast.parse(r.read_text(encoding="utf-8"))
        wanted = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("equipop"):
                    wanted.add(node.module)
            elif isinstance(node, ast.Import):
                for n in node.names:
                    if n.name.startswith("equipop"):
                        wanted.add(n.name)
        for mod in sorted(wanted):
            assert importlib.util.find_spec(mod) is not None, (
                f"{r.name} imports {mod}, which the package does not "
                "provide")


def test_the_pro_help_sidecars_are_shipped_beside_the_toolbox():
    """v1.47.4. EquiPop.<Tool>.pyt.xml is where ArcGIS Pro reads the
    comment beside each parameter box. They were NEVER SHIPPED - not
    in MANIFEST.in, not in the sdist, not in any delivery - so a Pro
    user has only ever had the help they generated themselves, one
    release stale at best.

    BACKLOG 34 has recorded "summary/usage render empty in Pro" since
    v1.16.8 and asked for a field cycle to confirm. John supplied one
    in session 12: a dialogReference flyout with a correct title and
    an EMPTY BODY. A missing sidecar produces exactly that.

    THE TEST THAT EXISTED did not catch this. It generates the files
    and checks every parameter has help in them - true, and no help
    at all for a user who never receives the file. A check on an
    artefact nobody ships is a check on nothing.
    """
    manifest = open(os.path.join(ROOT, "MANIFEST.in"),
                    encoding="utf-8").read()
    lines = [l.strip() for l in manifest.split("\n")]
    assert any(re.fullmatch(r"include arcgis/\*\.pyt\.xml", l)
               or re.fullmatch(r"graft arcgis", l) and
               "include arcgis/*.pyt.xml" in manifest
               for l in lines), (
        "MANIFEST.in does not carry arcgis/*.pyt.xml - Pro will show "
        "an empty comment beside every parameter box")


def test_the_sidecars_are_not_committed_to_the_repository():
    """The other half, and the two are not in conflict: the sidecars
    are BUILD OUTPUTS regenerated by make_help_xml.py, so they are
    excluded from the tree (BACKLOG 45) and included in the archive.
    Do not commit them; do ship them."""
    stray = [f for f in os.listdir(os.path.join(ROOT, "arcgis"))
             if f.endswith(".pyt.xml")]
    assert not stray, (
        f"{stray} are sitting in arcgis/ - they are build outputs and "
        "the suite must not leave them behind (BACKLOG 45)")


def test_the_arcgis_guide_names_the_files_it_says_it_names():
    """v1.47.4. The guide said "Keep these FOUR files together" and
    then listed THREE. A user following it replaces the toolbox and
    keeps the sidecars - which is exactly what happened in the field
    at 1.47.4, and it is why the new parameter's help flyout came
    back empty while every older box looked fine.

    THE INSTRUCTION, NOT THE PACKAGING, produced that. So the count
    in the sentence is checked against the list beneath it.
    """
    guide = open(os.path.join(ROOT, "arcgis", "ARCGIS_GUIDE.md"),
                 encoding="utf-8").read()
    listed = set(re.findall(r"EquiPop[.\w]*\.pyt(?:\.xml)?", guide))
    must = {"EquiPop.pyt", "EquiPop.CountsShares.pyt.xml",
            "EquiPop.ValueStatistics.pyt.xml",
            "EquiPop.ContinentalRasters.pyt.xml",
            "EquiPop.SpatialDemography.pyt.xml",
            "EquiPop.FolderInventory.pyt.xml"}
    assert must <= listed, f"the guide does not name {sorted(must - listed)}"
    words = {"TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5, "SIX": 6}
    claim = re.search(r"\*\*(TWO|THREE|FOUR|FIVE|SIX) files must sit",
                      guide)
    assert claim, "the guide no longer states how many files travel together"
    assert words[claim.group(1)] == len(must), (
        f"the guide claims {claim.group(1)} files must sit together "
        f"but {len(must)} are required")


def test_the_guide_does_not_undercount_the_toolbox():
    """It also said "Two tools appear" when four do."""
    guide = open(os.path.join(ROOT, "arcgis", "ARCGIS_GUIDE.md"),
                 encoding="utf-8").read()
    pyt = open(os.path.join(ROOT, "arcgis", "EquiPop.pyt"),
               encoding="utf-8").read()
    registered = re.search(r"self\.tools = \[([^\]]+)\]", pyt).group(1)
    n = len([t for t in registered.split(",") if t.strip()])
    claim = re.search(r"pick the \.pyt\. (TWO|THREE|FOUR|FIVE|SIX) "
                      r"tools appear", guide)
    assert claim, "the guide no longer says how many tools appear"
    assert {"TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5,
            "SIX": 6}[claim.group(1)] == n


def test_the_handover_keeps_up_with_the_version():
    """v1.47.4. BACKLOG 289 records John's ruling that a handover must
    enter the repository in the same act as the release - and session
    12, which wrote that entry, then shipped three releases without
    one. "In the same act" was too vague to be followed by the people
    who wrote it, so it is checked instead.

    The newest HANDOVER_N.md must name the current version. It does
    not have to be perfect prose; it has to exist and be about THIS
    release rather than the last one.
    """
    hands = sorted(
        (int(re.search(r"HANDOVER_(\d+)\.md", f).group(1)), f)
        for f in os.listdir(ROOT)
        if re.fullmatch(r"HANDOVER_\d+\.md", f))
    assert hands, "no handover in the repository root"
    _, newest = hands[-1]
    version = re.search(
        r'^version\s*=\s*"([^"]+)"',
        open(os.path.join(ROOT, "pyproject.toml"),
             encoding="utf-8").read(), re.M).group(1)
    series = ".".join(version.split(".")[:2])       # 1.47.4 -> 1.47
    text = open(os.path.join(ROOT, newest), encoding="utf-8").read()
    assert series in text, (
        f"{newest} does not mention {series} - the handover is for an "
        "older release, which is how sessions 9 and 10 were lost")
