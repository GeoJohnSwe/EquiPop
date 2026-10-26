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
import sys

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
    p = os.path.join(PKG, "..", "stata", "equipop_test_data.dta")
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


def test_the_release_zip_leaves_build_outputs_out_of_the_tree():
    """BACKLOG 350. 1.51.0 SHIPPED A SECOND COPY OF THE WHOLE PACKAGE.

    `python -m build` leaves `build/lib/equipop/` and `dist/`, and the
    release zip was built from the whole tree - so the archive John
    unzips over his working tree and COMMITS carried all 40 modules
    twice, the second set frozen at whatever version last built. A
    grep of the tree would then find every rule in two places, which
    is this project's signature defect arriving through the directory
    layout rather than through the code. Nothing noticed, because
    every name is valid and the zip extracts perfectly - the 156 check
    above asks whether members can be EXTRACTED, not whether they
    should be there.

    `dist/` is the same mistake 3 MB larger: the wheel and the source
    archive are siblings of this zip in the release bundle.

    Checked by walking a FAKE TREE through the builder's own member
    list, so the test does not depend on whether a build has happened
    in this checkout.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_mkzip", os.path.join(ROOT, "tools", "make_release_zip.py"))
    mk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mk)

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        for rel in ("equipop/cells.py", "README.md",
                    "build/lib/equipop/cells.py",
                    "dist/equipop-9.9.9.tar.gz",
                    "equipop.egg-info/PKG-INFO",
                    "equipop/__pycache__/cells.cpython-311.pyc"):
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as fh:
                fh.write("x")
        names = sorted(arc for _full, arc in mk.members(tmp))

    assert names == ["README.md", "equipop/cells.py"], \
        f"the builder swept in build outputs: {names}"


def test_the_release_zip_builder_refuses_generated_sidecars():
    """BACKLOG 404, v1.54.6. The 350 test above asks what the builder
    SWEEPS IN by walking directories. The Pro help sidecars are not
    swept in by a directory rule, because they live in arcgis/ beside
    files that must ship - so neither check above can see them, and
    the 1.54.0 bundle carried them until it was caught by hand.

    They are build outputs: make_help_xml.py writes them, MANIFEST.in
    ships them in the sdist, and the working tree must not hold them
    (BACKLOG 45, asserted by
    test_the_sidecars_are_not_committed_to_the_repository). The build
    ORDER is therefore the trap - generate, build the Pro step from
    them, delete - and that is the one thing this file's own docstring
    says never to leave to memory.

    REFUSE, NOT SKIP: a skip builds a clean zip and leaves the files
    in the tree, so `pytest` fails next instead. The fault would move,
    not go.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_mkzip", os.path.join(ROOT, "tools", "make_release_zip.py"))
    mk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mk)

    good = ["arcgis/EquiPop.pyt", "equipop/cells.py", "MANIFEST.in"]
    mk.check_build_outputs(good)                      # must not raise

    with pytest.raises(SystemExit) as e:
        mk.check_build_outputs(
            good + ["arcgis/EquiPop.CountsShares.pyt.xml"])
    msg = str(e.value)
    assert "REFUSING" in msg
    assert "rm arcgis/*.pyt.xml" in msg, (
        "the refusal must say what to do - a refusal without a remedy "
        "is where 402 came from")

    # ...AND THE REAL BUILDER MUST CONSULT IT. A checker nothing calls
    # is this project's signature defect; `build` is where the order
    # is actually got wrong, so the test drives `build` itself.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        for rel in ("equipop/cells.py",
                    "arcgis/EquiPop.CountsShares.pyt.xml"):
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as fh:
                fh.write("x")
        out = os.path.join(tmp, "_out")
        with pytest.raises(SystemExit) as e:
            mk.build(tmp, "9.9.9", out)
        assert "REFUSING" in str(e.value)
        assert not os.path.exists(
            os.path.join(out, "EquiPop-9.9.9-complete.zip")), \
            "it refused and wrote the zip anyway"


def test_every_runner_imports_only_modules_the_package_ships():
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
    """v1.47.11. EquiPop.<Tool>.pyt.xml is where ArcGIS Pro reads the
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


def test_the_bundle_script_generates_the_sidecars_before_it_builds():
    """BACKLOG 404, v1.54.6. THE OTHER HALF, AND THE ROOT CAUSE.

    Up to 1.54.5 the 19-slot release bundle was built by a script
    living OUTSIDE the repository, rewritten from the last one each
    release. Three defects came out of that in one hour, and this is
    the one that produced the other two: the Pro help sidecars were
    present at build time only BY ACCIDENT of the order I happened to
    work in. Put where the Pro slot needs them, the first 1.54.6
    sdist shipped with ZERO of them while every check stayed green.

    `tools/make_release_zip.py` had the rule all along - *"a manual
    step in the right order is not a fix, because the order will be
    got wrong again"* - and the bundle's order was the one step still
    kept in a memory. `tools/make_bundle.sh` now carries it, and this
    reads the order out of it.

    POSITION IS THE PROPERTY HERE, so position is what is asserted -
    1.54.5's lesson, where "the note exists" was true of the version
    John complained about. The script also guards itself at runtime
    (it fails if the sdist comes out with no sidecars), which is the
    behavioural half; this is the half that fails in CI rather than
    at 11pm on a release night.
    """
    path = os.path.join(ROOT, "tools", "make_bundle.sh")
    assert os.path.exists(path), (
        "tools/make_bundle.sh is gone - the bundle order is back in "
        "somebody's memory, which is where BACKLOG 404 came from")
    src = open(path, encoding="utf-8").read()

    def one(pattern, what):
        hits = [m.start() for m in re.finditer(pattern, src, re.M)]
        assert len(hits) == 1, (
            f"{what}: expected exactly one line matching {pattern!r}, "
            f"found {len(hits)} - an ambiguous anchor makes this test "
            "prove nothing")
        return hits[0]

    gen = one(r"^python arcgis/make_help_xml\.py", "the generate step")
    bld = one(r"^python -m build ", "the wheel/sdist step")
    assert gen < bld, (
        "make_bundle.sh builds the wheel and sdist BEFORE generating "
        "the Pro help sidecars, so MANIFEST.in's `include "
        "arcgis/*.pyt.xml` has nothing to include and the sdist ships "
        "without them - exactly the 1.54.6 regression")

    # ...and it must leave the tree as it found it, or the next
    # `pytest` fails on stray build outputs instead.
    assert re.search(r"rm -f .*arcgis/\*\.pyt\.xml", src), (
        "make_bundle.sh does not delete the sidecars it generates - "
        "the tree is left dirty and the fault moves to the suite")
    assert "trap cleanup EXIT" in src, (
        "the cleanup is not on a trap, so a failure midway leaves "
        "build outputs in the tree")

    # The sdist self-check is what catches an order nobody re-read.
    sd = one(r"tar tzf .*equipop-\$V\.tar\.gz", "the sdist self-check")
    assert sd > bld, "the sdist is checked before it is built"
    assert "carries no Pro help sidecars" in src, (
        "make_bundle.sh does not verify that the sdist it just built "
        "actually carries the sidecars")


def test_the_sdist_really_carries_the_pro_sidecars(tmp_path):
    """BACKLOG 404, v1.54.6. THE TEST ABOVE ASSERTS A LINE OF
    MANIFEST.in. A line is a PERMISSION, not a guarantee: the five
    files must EXIST at the moment `python -m build` runs, and whether
    they do is a question of build ORDER - which nothing in the tree
    answered, because the bundle has always been built by a script
    living outside it.

    MEASURED, and it is not hypothetical. 1.54.3, 1.54.4 and 1.54.5
    shipped sdists carrying all five - by accident of the order I
    happened to work in. The first 1.54.6 build, with the generation
    step put where the bundle's Pro slot needs it, shipped an sdist
    with **ZERO**, and every existing check stayed green: MANIFEST.in
    was unchanged, the bundle's five loose copies were present, and
    the suite passed. Only comparing the two tarballs by hand showed
    it.

    The test above states the lesson it then missed by one level -
    *"a check on an artefact nobody ships is a check on nothing"*. So
    this one builds the artefact and looks inside it.

    WHAT THIS DOES **NOT** PROVE, said here rather than left to be
    assumed: it generates the sidecars itself, so it proves that
    MANIFEST.in and the packaging config DELIVER them when they
    exist. It cannot prove they exist when the release is built -
    that is the build ORDER, and the order is asserted on
    `tools/make_bundle.sh` by
    test_the_bundle_script_generates_the_sidecars_before_it_builds.
    Two halves, and today's regression was in the second one.

    Skipped where `build` is not installed, which is most of John's
    hosts: the suite must pass there, and this is a release-time
    property.
    """
    import importlib.util
    import shutil
    import subprocess
    import tarfile
    if importlib.util.find_spec("build") is None:
        pytest.skip("the `build` package is not installed here")

    arc = os.path.join(ROOT, "arcgis")
    gen = os.path.join(arc, "make_help_xml.py")
    made = []
    try:
        g = subprocess.run([sys.executable, gen], cwd=ROOT,
                           capture_output=True, text=True, timeout=300)
        made = [f for f in os.listdir(arc) if f.endswith(".pyt.xml")]
        # v1.55.1, BACKLOG 407. THIS USED TO ASK ONLY THAT SOMETHING
        # WAS WRITTEN, and compare the sdist with however much that
        # was. Under an older installed equipop the generator wrote
        # ONE sidecar, then refused for missing help - and this test
        # passed, one of one. A generator that failed is not a
        # generator that ran; and five tools need five sidecars.
        assert g.returncode == 0, (
            f"make_help_xml.py failed:\n{g.stdout[-800:]}{g.stderr[-800:]}")
        pyt_src = open(os.path.join(arc, "EquiPop.pyt"),
                       encoding="utf-8").read()
        n_tools = len([t for t in re.search(
            r"self\.all_tools = \[([^\]]+)\]", pyt_src).group(1).split(",")
            if t.strip()])
        assert len(made) == n_tools, (
            f"the generator wrote {sorted(made)} for {n_tools} tools")
        out = tmp_path / "sd"
        p = subprocess.run(
            [sys.executable, "-m", "build", "--sdist", "--no-isolation",
             "--outdir", str(out)],
            cwd=ROOT, capture_output=True, text=True, timeout=900)
        assert p.returncode == 0, f"sdist build failed:\n{p.stdout[-2000:]}"
        tars = list(out.glob("*.tar.gz"))
        assert len(tars) == 1, f"expected one sdist, got {tars}"
        inside = [n for n in tarfile.open(tars[0]).getnames()
                  if n.endswith(".pyt.xml")]
        assert len(inside) == len(made), (
            f"the sdist carries {len(inside)} of {len(made)} Pro help "
            "sidecars. MANIFEST.in permits them; the build ORDER "
            "decides whether they are there, and a Pro user with no "
            "sidecar gets an empty comment beside every parameter box "
            "(BACKLOG 34)")
    finally:
        for f in made:
            try:
                os.remove(os.path.join(arc, f))
            except OSError:
                pass
        # `build` leaves this behind, and the release zip must not
        # sweep it in (BACKLOG 350).
        shutil.rmtree(os.path.join(ROOT, "equipop.egg-info"),
                      ignore_errors=True)
        left = [f for f in os.listdir(arc) if f.endswith(".pyt.xml")]
        assert not left, (
            f"this test left {left} in the tree, which breaks the test "
            "below it - that is the fault moving, not going")


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
    """v1.47.11. The guide said "Keep these FOUR files together" and
    then listed THREE. A user following it replaces the toolbox and
    keeps the sidecars - which is exactly what happened in the field
    at 1.47.11, and it is why the new parameter's help flyout came
    back empty while every older box looked fine.

    THE INSTRUCTION, NOT THE PACKAGING, produced that. So the count
    in the sentence is checked against the list beneath it.
    """
    guide = open(os.path.join(ROOT, "arcgis", "ARCGIS_GUIDE.md"),
                 encoding="utf-8").read()
    listed = set(re.findall(r"EquiPop[.\w]*\.pyt(?:\.xml)?", guide))
    must = {"EquiPop.pyt", "EquiPop.ShowTools.pyt.xml",
            "EquiPop.CountsShares.pyt.xml",
            "EquiPop.ValueStatistics.pyt.xml",
            "EquiPop.ContinentalRasters.pyt.xml",
            "EquiPop.SpatialDemography.pyt.xml",
            "EquiPop.WorldPopCatalogue.pyt.xml",
            "EquiPop.OsmCatalogue.pyt.xml",
            "EquiPop.FetchSelected.pyt.xml",
            "EquiPop.FolderInventory.pyt.xml"}
    assert must <= listed, f"the guide does not name {sorted(must - listed)}"
    words = {"TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5, "SIX": 6,
             "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10}
    claim = re.search(r"\*\*(TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN)"
                      r" files must sit",
                      guide)
    assert claim, "the guide no longer states how many files travel together"
    assert words[claim.group(1)] == len(must), (
        f"the guide claims {claim.group(1)} files must sit together "
        f"but {len(must)} are required")


def test_the_guide_does_not_undercount_the_toolbox():
    """It also said "Two tools appear" when four do.

    v1.62.0 (BACKLOG 438): two numbers now - the tools that appear
    when the toolbox is added (tool 0 and the standard set), and how
    many appear once tool 0 shows the rest. Both are counted from the
    code, not written here."""
    from equipop.doors.toolset import EXTENDED, STANDARD
    guide = open(os.path.join(ROOT, "arcgis", "ARCGIS_GUIDE.md"),
                 encoding="utf-8").read()
    pyt = open(os.path.join(ROOT, "arcgis", "EquiPop.pyt"),
               encoding="utf-8").read()
    registered = [t.strip() for t in re.search(
        r"self\.all_tools = \[([^\]]+)\]", pyt).group(1).split(",")
        if t.strip()]
    shown = [t for t in registered if t in STANDARD]
    assert set(registered) <= set(STANDARD) | set(EXTENDED), registered
    words = {"TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5, "SIX": 6,
             "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10}
    claim = re.search(r"pick the \.pyt\. (TWO|THREE|FOUR|FIVE|SIX|SEVEN|"
                      r"EIGHT|NINE|TEN) tools appear", guide)
    assert claim, "the guide no longer says how many tools appear"
    assert words[claim.group(1)] == len(shown)
    every = re.search(r"\(or restart Pro\)\. (TWO|THREE|FOUR|FIVE|SIX|"
                      r"SEVEN|EIGHT|NINE|TEN) tools then appear", guide)
    assert every, "the guide no longer says how many tools tool 0 shows"
    assert words[every.group(1)] == len(registered)


def test_the_handover_keeps_up_with_the_version():
    """v1.47.11. BACKLOG 289 records John's ruling that a handover must
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
    series = ".".join(version.split(".")[:2])       # 1.47.11 -> 1.47
    text = open(os.path.join(ROOT, newest), encoding="utf-8").read()
    assert series in text, (
        f"{newest} does not mention {series} - the handover is for an "
        "older release, which is how sessions 9 and 10 were lost")


def test_every_required_dependency_is_named_in_the_install_guide():
    """v1.47.11. `--no-deps` is rule one of INSTALL.md, and rightly -
    without it pip upgrades the host's numpy or scipy. But it also
    skips the dependencies that are NOT already there, and nobody
    wrote that down: QGIS, Pro and Stata all ship numpy, pandas and
    scipy, and NONE of them ships pyproj.

    A student lost an evening to it in September 2026. Three of the
    four verification imports worked and the fourth did not, and no
    guide had ever named pyproj - while the student guide's own
    verification step told her to import it.

    So every name in pyproject's `dependencies` must appear in
    INSTALL.md. Read from pyproject rather than listed here, so a
    dependency added later cannot go unmentioned the same way.
    """
    toml = open(os.path.join(ROOT, "pyproject.toml"),
                encoding="utf-8").read()
    block = re.search(r"^dependencies\s*=\s*\[(.*?)\]", toml,
                      re.S | re.M).group(1)
    names = re.findall(r'"([A-Za-z0-9_.-]+)', block)
    assert names, "no dependencies found in pyproject.toml"
    guide = open(os.path.join(ROOT, "INSTALL.md"),
                 encoding="utf-8").read().lower()
    missing = [n for n in names if n.lower() not in guide]
    assert not missing, (
        f"{missing} are required by the package and never mentioned "
        "in INSTALL.md. With `--no-deps` - which is rule one - a "
        "dependency the host does not already ship is simply absent, "
        "and the first a user knows is an ImportError")


def test_the_status_documents_keep_up_with_the_version():
    """v1.47.11. TEACHING.md and PROPOSALS.md carry a version line, and
    it must match the package.

    THIS IS THE PRIORITY-LIST LESSON APPLIED IN ADVANCE. The backlog's
    "what next" section stopped at item 164 and nobody noticed for
    eleven releases; item 257's "STILL NEEDED" asked for samples
    already supplied; item 43 sat open five releases after it was
    done. A planning document with no check on it rots, and a rotten
    TEACHING.md is worse than none - a student follows it.

    Only the version is checked. Nothing here can tell whether the
    PROSE is still true; that remains a human job, and the version
    line is the prompt to do it.
    """
    version = re.search(
        r'^version\s*=\s*"([^"]+)"',
        open(os.path.join(ROOT, "pyproject.toml"),
             encoding="utf-8").read(), re.M).group(1)
    for name in ("TEACHING.md", "PROPOSALS.md"):
        path = os.path.join(ROOT, name)
        assert os.path.exists(path), f"{name} is missing"
        text = open(path, encoding="utf-8").read()
        m = re.search(r"\*\*Last updated:\s*([0-9][^,]*),", text)
        assert m, (
            f"{name} has no '**Last updated: <version>, <date>**' "
            "line - without one nothing can tell whether it has "
            "drifted")
        assert m.group(1).strip() == version, (
            f"{name} says {m.group(1).strip()}, the package is "
            f"{version}. Either it was reviewed this release and the "
            "line needs bumping, or it was NOT reviewed and that is "
            "the thing worth noticing")


def test_the_proposals_file_does_not_ship():
    """Funding strategy, consortium thinking and draft positioning are
    not things to publish on PyPI by accident. TEACHING.md ships
    because it helps a user; this one does not."""
    manifest = open(os.path.join(ROOT, "MANIFEST.in"),
                    encoding="utf-8").read()
    assert re.search(r"^exclude PROPOSALS\.md", manifest, re.M), (
        "MANIFEST.in must exclude PROPOSALS.md explicitly - a default "
        "that happens to leave it out is not a decision")


def test_the_bump_tool_refuses_to_touch_the_status_documents():
    """v1.47.11. The version-line guard on TEACHING.md and
    PROPOSALS.md was DEFEATED BY THE ROUTINE that raises the question.

    Versions were moved with a blanket sed over every file holding the
    old string - which included the "Last updated" lines. The check
    could never fire: the one thing meant to prove a human had looked
    was answered by the same command that asked.

    A CHECK THAT THE ROUTINE UPDATES AUTOMATICALLY IS NOT A CHECK.
    tools/bump_version.py makes the exclusion executable rather than
    remembered, and this asserts it stays that way.
    """
    src = open(os.path.join(ROOT, "tools", "bump_version.py"),
               encoding="utf-8").read()
    m = re.search(r"NEVER\s*=\s*\(([^)]*)\)", src)
    assert m, "bump_version.py no longer has a NEVER list"
    for name in ("TEACHING.md", "PROPOSALS.md"):
        assert name in m.group(1), (
            f"{name} is not in bump_version.py's NEVER list, so the "
            "next routine bump will silence its own guard")


def test_the_published_test_dataset_says_what_it_is():
    """BACKLOG 237. John, from the field: "ValFloat is not float and
    should be; ValCount holds counts."

    It was declared Stata `double` under a name that says float, and
    all nine variables had EMPTY LABELS - so the name carried the
    whole burden of saying what a variable meant, and one of the names
    lied. That matters more than it used to: the file now ships to
    every SSC user who types `ssc install equipop, all`, next to the
    paper, and it is the first thing a reader inspects.

    THE VALUES ARE NOT CHECKED HERE and must not change without a
    ruling - they are the answer key behind the showcase's pinned
    `Nv 167.30 | Mean 1815.23 | Med 1248.10 | Gini .5806`. What is
    checked is that the file still DESCRIBES ITSELF.
    """
    import pandas as pd
    path = os.path.join(ROOT, "stata", "equipop_test_data.dta")
    if not os.path.exists(path):                     # pragma: no cover
        pytest.skip("the Stata test dataset is not present")
    r = pd.io.stata.StataReader(path)
    r.read(1)
    types = dict(zip(r._varlist, [str(t) for t in r._typlist]))
    labels = r.variable_labels()

    assert types.get("ValFloat") == "f", (
        f"ValFloat is declared {types.get('ValFloat')!r}, not a Stata "
        "float. The name is the lesson - a continuous measure belongs "
        "in values() and not in treat() - and a name that disagrees "
        "with `describe` undercuts it every time somebody looks")
    for coord in ("X_local", "Y_local"):
        assert types.get(coord) == "d", (
            f"{coord} must stay DOUBLE: these are metres in a local "
            "projection and a float would lose sub-metre precision "
            "on six-figure eastings")
    empty = sorted(n for n, lab in labels.items() if not lab.strip())
    assert not empty, (
        f"{empty} have no variable label. In Stata the label is where "
        "meaning lives; without one the NAME has to carry it, which "
        "is how ValFloat came to teach the wrong thing. "
        "tools/make_test_data.py holds the text")
    assert "not a 0/1 marker" in labels.get("ValCount", ""), (
        "ValCount's label must say what it is NOT - the pair "
        "ValFloat/ValCount is the confusion 237 was raised about, and "
        "block 20 of the field pass was invalid for a release because "
        "of exactly that mix-up")


def test_the_ssc_package_lists_every_ado_and_a_current_date():
    """v1.47.12. SSC shows Distribution-Date to users and uses it to
    decide what is new. It sat at 20260830 through twelve releases
    because the blanket version replace never matched a date and
    nothing checked.

    Also: a file missing from the .pkg simply does not install, and
    the user finds out when a command is not found.
    """
    pkg = open(os.path.join(ROOT, "stata", "equipop.pkg"),
               encoding="utf-8").read()
    listed = set(re.findall(r"^f (\S+)", pkg, re.M))
    on_disk = {f for f in os.listdir(os.path.join(ROOT, "stata"))
               if f.endswith(".ado")}
    missing = on_disk - listed
    assert not missing, (
        f"{sorted(missing)} are in stata/ but not in equipop.pkg - "
        "they will not install, and the user finds out when a command "
        "is not found")
    assert "equipop.sthlp" in listed, "the help file must install too"

    # BACKLOG 330, KIT BAUM ON THE SSC RELEASE. The archive builds its
    # OWN .pkg and he included the worked examples and the test data;
    # this one had never declared them, so `net install` from GitHub
    # gave the commands and not the material the help and the paper
    # tell people to run. TWO INSTALL ROUTES OFFERING DIFFERENT FILES,
    # and only one of them was described anywhere.
    #
    # He also renamed them - example.do and stata_test_data.dta are
    # not names one package may take on a flat archive - so the check
    # pins the prefixed names: a generic name here is a name SSC will
    # refuse, and finding that out by email costs a release.
    ship = set(re.findall(r"^[fg] (\S+)", pkg, re.M))
    for name in ("equipop_example.do", "equipop_showcase.do",
                 "equipop_test_data.dta"):
        assert name in ship, (
            f"{name} is not in equipop.pkg, so `net install` from "
            "GitHub installs less than `ssc install` does")
    for name in os.listdir(os.path.join(ROOT, "stata")):
        if name.endswith((".do", ".dta")):
            assert name.startswith("equipop"), (
                f"stata/{name} has a name the SSC archive cannot "
                "take - every file there shares a flat, global "
                "namespace, so it needs the equipop prefix")

    ver = re.search(r'^version\s*=\s*"([^"]+)"',
                    open(os.path.join(ROOT, "pyproject.toml"),
                         encoding="utf-8").read(), re.M).group(1)
    assert re.search(rf"^d EquiPop {re.escape(ver)} ", pkg, re.M), (
        f"equipop.pkg does not announce {ver}")

    m = re.search(r"^d Distribution-Date: (\d{8})", pkg, re.M)
    assert m, "no Distribution-Date - SSC needs one"
    import datetime
    d = datetime.datetime.strptime(m.group(1), "%Y%m%d").date()
    age = (datetime.date.today() - d).days
    assert 0 <= age <= 120, (
        f"Distribution-Date is {m.group(1)}, {age} days old. It is "
        "bumped with the version; if this fails, a release went out "
        "without one")


def test_the_run_manifests_carry_a_bom_for_excel():
    """BACKLOG 320(b). Excel on Windows reads a BOM-less UTF-8 CSV as
    the ANSI codepage, so a path or field name holding a Norwegian
    vowel arrives as mojibake - andel_fodt became andel_fXdt, verified
    against cp1252. Students reported it after the LA lecture."""
    src = open(os.path.join(ROOT, "arcgis", "EquiPop.pyt"),
               encoding="utf-8").read()
    assert 'newline="", encoding="utf-8")' not in src, (
        "a CSV is written without a BOM again - Excel will mangle "
        "every non-ASCII character in it")
    assert src.count("utf-8-sig") >= 2


def test_stata_setup_does_not_force_user_in_a_virtual_environment():
    """BACKLOG 319. pip refuses --user inside a venv, so setup failed
    on exactly the people careful enough to give Stata its own
    environment. And the failure message used to print the same advice
    whatever pip said - for "No module named pip" it told them to
    replace their whole Python."""
    src = open(os.path.join(ROOT, "stata", "equipop.ado"),
               encoding="utf-8").read()
    assert 'args = ["--user", "--upgrade"]' not in src, (
        "--user is unconditional again; a virtual environment will "
        "refuse it")
    assert "base_prefix" in src, "no virtual environment detection"
    # The advice must be REACHABLE, not merely present: an earlier
    # version of this test only looked for the word "ensurepip", so
    # disabling the branch that offers it still passed.
    assert '"no module named pip" in low' in src, (
        "setup no longer dispatches on what pip actually said - the "
        "'No module named pip' case will fall through to generic "
        "advice again")
    assert "ensurepip" in src, (
        "the 'No module named pip' case is unhandled - the one-line "
        "fix is ensurepip, not a new Python")
    assert '"externally managed" in low' in src


def test_setup_asks_for_an_engine_at_least_as_new_as_it_needs():
    """BACKLOG 196, corrected by 332. `equipop setup` installed a bare
    `equipop`, so a 1.40 command file could pull whatever PyPI had that
    day - and `equipop doctor` then reported a drift that SETUP had
    created.

    A FLOOR, NOT A PIN, AND NOT THE ADO'S VERSION EITHER. 196 built
    the floor out of the ado's own release number, which is not a
    dependency: 1.49.2 touched only the ArcGIS toolbox and silently
    raised the Stata engine floor, and a release that reaches SSC
    before PyPI names an engine that does not exist, so pip installs
    nothing at all.

    The floor is now the oldest engine that satisfies the calls the
    ado makes, declared by hand beside the list of what sets it.
    """
    import re
    src = open(os.path.join(ROOT, "stata", "equipop.ado"),
               encoding="utf-8").read()
    assert 'args.append("equipop>=" + floor)' in src, (
        "no version floor - setup can install an engine older than "
        "the commands calling it")
    assert 'args.append("equipop>=" + ado_version)' not in src, (
        "the floor is the ado's own release number again, so a "
        "release that reaches SSC before PyPI cannot be installed")
    assert ('def _equipop_setup_py(repair="", ado_version="", '
            'min_engine="")') in src, (
        "the setup routine does not receive the engine floor")

    # the floor must be declared TWICE and identically - setup asks
    # pip for it, the doctor judges against it, and a floor the two
    # disagree about is worse than no floor
    floors = set(re.findall(r'local eqp_min_engine "([^"]+)"', src))
    assert len(floors) == 1, (
        f"setup and the doctor name different engine floors: {floors}")
    floor = floors.pop()
    assert re.fullmatch(r"\d+\.\d+(\.\d+)?", floor), floor

    # AND IT MUST NOT BE BUMPED AUTOMATICALLY. The whole point is that
    # it moves only when the commands start calling something new,
    # which is a human decision - if bump_version.py touched it the
    # fault would be back within one release and invisible.
    #
    # Checked by RUNNING EVERY PATTERN the tool applies against the
    # floor's own line, rather than by grepping the tool for the
    # name: the first version of this check did grep, and failed on
    # the COMMENT that explains why the floor is left alone. A test
    # that forbids documenting a rule is testing the wrong thing.
    import sys
    pkg_version = re.search(
        r'^version\s*=\s*"([^"]+)"',
        open(os.path.join(ROOT, "pyproject.toml"),
             encoding="utf-8").read(), re.M).group(1)
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    try:
        import bump_version
    finally:
        sys.path.pop(0)
    floor_line = f'    local eqp_min_engine "{floor}"'
    for entry in bump_version.DECLARATIONS:
        rel, pat = entry[0], entry[1]
        if not rel.endswith("equipop.ado"):
            continue
        assert not re.search(pat, floor_line, re.M), (
            f"bump_version.py pattern {pat!r} matches the engine "
            "floor, so the floor will follow the release number "
            "again - BACKLOG 332 exactly")
    # and the ado's own version line must still be matched by one of
    # them, or the opposite fault is waiting
    ado_line = f'    local eqp_ado_version "{pkg_version}"'
    assert any(re.search(e[1], ado_line, re.M)
               for e in bump_version.DECLARATIONS
               if e[0].endswith("equipop.ado")), (
        "no pattern matches the ado's own version line - it will "
        "drift from pyproject.toml")
    assert floor != pkg_version or floor == "0", (
        f"the floor has caught up with the release number ({floor}). "
        "That is allowed only if this release really did add an "
        "engine call the commands need - if it did, say which in the "
        "comment beside eqp_min_engine and change this test's "
        "reasoning deliberately")

    # the version it passes in must be the SAME string the doctor uses,
    # or the two halves of the same guard disagree
    vers = set(re.findall(r'local eqp_ado_version "([^"]+)"', src))
    assert len(vers) == 1, (
        f"the ado declares more than one version of itself: {vers}")
    pkg = re.search(r'^version\s*=\s*"([^"]+)"',
                    open(os.path.join(ROOT, "pyproject.toml"),
                         encoding="utf-8").read(), re.M).group(1)
    assert vers == {pkg}, f"ado says {vers}, package says {pkg}"


def test_a_failed_setup_is_a_failed_command():
    """BACKLOG 196, the other half. Setup printed "PIP FAILED" and
    then returned normally, so a scripted or institutional install had
    no failure code to act on."""
    src = open(os.path.join(ROOT, "stata", "equipop.ado"),
               encoding="utf-8").read()
    assert src.count('Macro.setLocal("eqp_setup_failed", "1")') >= 2, (
        "not every failing exit flags the failure - both the "
        "could-not-run-pip and the pip-returned-nonzero paths must")
    assert '''if "`eqp_setup_failed'" != "" {''' in src and \
        "exit 601" in src, (
        "the ado does not turn the flag into a non-zero exit")


def test_the_update_advice_names_ssc_first():
    """v1.48.2. The unknown-subcommand message named a raw GitHub URL
    only - printed at the exact moment a confused user is reading
    carefully, and the wrong instruction once the package is on SSC.
    GitHub stays as the development route."""
    src = open(os.path.join(ROOT, "stata", "equipop.ado"),
               encoding="utf-8").read()
    i_ssc = src.find("ssc install equipop, replace")
    i_git = src.find("raw.githubusercontent")
    assert i_ssc > 0, "the update advice does not mention SSC"
    assert i_ssc < i_git, (
        "GitHub is offered before SSC - a Stata user updates from SSC")
    readme = open(os.path.join(ROOT, "stata", "README_STATA.md"),
                  encoding="utf-8").read()
    assert "ssc install equipop" in readme, (
        "README_STATA.md still offers only the GitHub route")


def test_every_module_compiles_on_the_oldest_python_we_promise():
    """v1.48.2, FOUND BY THE TEST ENVIRONMENT CHANGING.

    pyproject declares requires-python >= 3.10, and
    equipop/doors/continental.py could not be IMPORTED on 3.10 or
    3.11: it put a \\u2019 escape inside an f-string expression, which
    PEP 701 only permitted from 3.12. ArcGIS Pro 3.3 and 3.4 ship
    Python 3.11, so machine 3 was dead there - and every session until
    now ran 3.12, where the interpreter accepted it and the entire
    suite passed.

    A COMPILE CHECK CANNOT CATCH WHAT THIS INTERPRETER ALLOWS, so this
    test does what it can: it compiles every module, and separately
    refuses the one construct known to differ. If the declared floor
    ever rises to 3.12, delete the second half rather than the test.
    """
    import re
    roots = ("equipop", "qgis", "arcgis")
    files = []
    for r in roots:
        for dirpath, _dirs, names in os.walk(os.path.join(ROOT, r)):
            if "__pycache__" in dirpath:
                continue
            files.extend(os.path.join(dirpath, n) for n in names
                         if n.endswith((".py", ".pyt")))
    assert files, "found no modules to compile - the walk is wrong"

    declared = re.search(r'requires-python\s*=\s*"[^0-9]*(\d+)\.(\d+)',
                         open(os.path.join(ROOT, "pyproject.toml"),
                              encoding="utf-8").read())
    floor = (int(declared.group(1)), int(declared.group(2)))

    bad = []
    for f in files:
        src = open(f, encoding="utf-8").read()
        try:
            compile(src, f, "exec")
        except SyntaxError as exc:
            bad.append(f"{f}:{exc.lineno} {exc.msg}")
        if floor < (3, 12):
            # A BACKSLASH INSIDE AN f-STRING EXPRESSION. Matched on the
            # {...} parts of f-string lines only, so an ordinary
            # escape in the literal text is left alone.
            for i, line in enumerate(src.splitlines(), 1):
                if not re.search(r'\bf["\']', line):
                    continue
                for expr in re.findall(r"\{([^{}]*)\}", line):
                    if "\\" in expr:
                        bad.append(
                            f"{f}:{i} backslash inside an f-string "
                            f"expression - refused by Python "
                            f"{floor[0]}.{floor[1]}, which pyproject "
                            f"promises to support")
    assert not bad, "\n".join(bad)


def test_the_bump_tool_does_not_translate_line_endings(tmp_path):
    """REVIEW F5, and it reproduced only on Windows.

    `bump_version.py` read and wrote in text mode with Python's
    default newline handling. On Windows that converts every LF to
    CRLF on write, so a release operation there rewrites EVERY LINE of
    all ten declared files - including the 4,932-line ArcGIS toolbox -
    and the byte-identical round-trip test below reports all ten as
    changed. No analytical output moves; what it costs is whole-file
    diffs and merge conflicts at exactly the moment a release is being
    reviewed.

    TWO CHECKS, because this platform cannot see the defect.

    The READ side is directly testable anywhere: with newline="" a
    CRLF file comes back with its CRLFs intact, and without it
    Python's universal-newline translation silently turns them into
    LF - so the tool would "fix" line endings it was never asked to
    touch. That half is measured here.

    The WRITE side cannot be measured on Linux, because text mode
    writes LF as LF here whatever the setting. So it is asserted
    structurally instead: every open-for-write in the tool must pass
    newline="". A property over the AST rather than a grep, and the
    honest statement of its limit is that it checks the mechanism
    while the round-trip test below checks the result - on whichever
    platform it runs.
    """
    import ast

    spec_path = os.path.join(ROOT, "tools", "bump_version.py")
    src = open(spec_path, encoding="utf-8").read()

    # --- the read side, for real
    f = tmp_path / "crlf.txt"
    f.write_bytes(b'version = "1.0.0"\r\nsecond line\r\n')
    with open(f, encoding="utf-8", newline="") as fh:
        kept = fh.read()
    assert "\r\n" in kept, (
        "newline='' no longer preserves CRLF on this platform, so the "
        "guarantee this test is about has changed")
    with open(f, encoding="utf-8") as fh:
        translated = fh.read()
    assert "\r\n" not in translated, (
        "universal newlines no longer translate, so the defect this "
        "test is about is no longer possible and the test is stale")

    # --- the write side, structurally
    writes = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "id", None)
        if name != "open":
            continue
        mode = ""
        for arg in node.args[1:2]:
            if isinstance(arg, ast.Constant):
                mode = str(arg.value)
        for kw in node.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                mode = str(kw.value.value)
        if "w" not in mode and "a" not in mode:
            continue
        has = any(kw.arg == "newline" and
                  isinstance(kw.value, ast.Constant) and
                  kw.value.value == "" for kw in node.keywords)
        writes.append((node.lineno, has))
    assert writes, (
        "no open-for-write found in bump_version.py - it writes "
        "through something else now and this check has stopped "
        "guarding anything")
    bad = [ln for ln, has in writes if not has]
    assert not bad, (
        f"bump_version.py writes at line(s) {bad} without "
        f"newline='' - on Windows that rewrites every line ending in "
        f"every declared file")
    # and the text those writes carry must have been read the same
    # way, or the round trip is not byte-for-byte either
    reads = re.findall(r"open\((?:path|p)[^)]*\)", src)
    assert all('newline=""' in r for r in reads if '"w"' in r or
               "'w'" in r), "a write path reads without newline=''"


def test_the_version_bump_survives_a_round_trip(tmp_path):
    """BACKLOG 352. The version lives in a dozen declarations across
    ten files, and TWO FILES CARRY TWO DECLARATIONS EACH -
    stata/equipop.ado has a `*!` banner and `eqp_ado_version`,
    equipop_test_pass.do has a header and a body line. Any rewrite of
    the bump tool that plans each declaration from a file's ORIGINAL
    text and then writes them all will make the second write discard
    the first, leaving a file bumped in one place and not the other.

    That happened while cutting 1.52.0 and was caught by the
    version-agreement tests within a minute - twice, because the same
    release also had the tool die part-way through its writes when its
    stdout was piped into `head`, leaving three files bumped and nine
    not. Both failure modes are invisible to a human reading the tool's
    output, which reported success in the first case and nothing in the
    second.

    TWO CHECKS, because the obvious one is not enough. A round trip -
    bump away and back, every file byte-identical - catches a
    declaration that is MISSED and the half-written repo. It does NOT
    catch last-write-wins, and the break-check is what revealed that:
    the patterns match any version string rather than the old one
    specifically, so the second bump repairs whatever the first left
    behind and the round trip comes out clean over a file that was
    wrong in between. The check that catches it is the direct one -
    after ONE bump, no declared file may still mention the old version.

    Run against a COPY of the declared files so the repository is never
    left mid-bump by a test.
    """
    import hashlib
    import shutil
    import subprocess
    import sys

    spec_path = os.path.join(ROOT, "tools", "bump_version.py")
    assert os.path.exists(spec_path), "the bump tool has moved"

    declared = ["pyproject.toml", "equipop/__init__.py",
                "qgis/equipop_qgis/__init__.py",
                "qgis/equipop_qgis/metadata.txt", "arcgis/EquiPop.pyt",
                "stata/equipop.pkg", "stata/equipop.ado",
                "CITATION.cff", "equipop_test_pass.do", "INSTALL.md",
                # v1.61.4: the two older commands' banners
                "stata/equipop_knn.ado", "stata/equipop_run.ado"]
    for rel in declared:
        src = os.path.join(ROOT, rel)
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    shutil.copytree(os.path.join(ROOT, "tools"), tmp_path / "tools")

    # ONE DECLARATION IS STAMPED "TODAY" BY DESIGN, so it cannot
    # survive a round trip across midnight. This test passed on the
    # day it was written and failed the next morning, which makes it a
    # test whose answer depends on the clock - the shape the project
    # keeps finding under a different name. The date line is
    # normalised out rather than the test being deleted, because
    # everything else in the file still has to come back identical.
    import re as _re
    _TODAY_FIELD = _re.compile(rb"^(d Distribution-Date:).*$", _re.M)

    def digests():
        out = {}
        for r in declared:
            raw = (tmp_path / r).read_bytes()
            raw = _TODAY_FIELD.sub(rb"\1 <today>", raw)
            out[r] = hashlib.md5(raw).hexdigest()
        return out

    import equipop
    here = equipop.__version__
    before = digests()

    def bump(version):
        r = subprocess.run(
            [sys.executable, str(tmp_path / "tools" / "bump_version.py"),
             version], capture_output=True, text=True, cwd=str(tmp_path))
        assert r.returncode == 0, r.stdout + r.stderr

    # (1) ONE bump forward: no DECLARATION may still say the old
    # version.
    #
    # v1.53.2: "declaration" is the point, and this used to test every
    # LINE. The bump tool prints its own rule - "code comments,
    # BACKLOG.md and MANUAL.md are left alone: a version in prose is a
    # FACT ABOUT THE PAST" - and this test contradicted it, so the
    # moment a release wrote `BACKLOG 377, v1.53.2` into a comment in
    # EquiPop.pyt (a file that also holds a real declaration) the
    # guard failed on nine comments that are CORRECT and must never
    # move. A comment recording when something was fixed is history;
    # bumping it would falsify the record.
    # Narrowed to the patterns the bump tool itself declares, so the
    # test now checks the thing its name says. Same mistake, third
    # time this week: a test matching TEXT where it meant to match a
    # KIND of line.
    bump("9.9.9")
    sys.path.insert(0, str(tmp_path / "tools"))
    for mod in ("bump_version",):
        sys.modules.pop(mod, None)
    import bump_version as _bv
    stale = []
    for rel, pattern, *_rest in _bv.DECLARATIONS:
        text = (tmp_path / rel).read_text(encoding="utf-8",
                                          errors="replace")
        for line in text.splitlines():
            if not re.search(pattern, line):
                continue
            if here in line and "9.9.9" not in line:
                stale.append(f"{rel}: {line.strip()[:72]}")
    assert not stale, (
        "a bump left these declarations at the old version - a second "
        "declaration in the same file has overwritten the first, or "
        "the tool stopped part-way:\n  " + "\n  ".join(stale))

    # (1b) v1.61.4, found by the break-check: the checks above take
    # their list of declarations FROM THE TOOL, and the round trip
    # below cannot see a line the tool does not know - it never moves,
    # so it comes back identical. Removing the equipop_run.ado
    # declaration passed both. So the banners Stata's `which` prints
    # are checked from the files themselves: every .ado, found by
    # glob, must say the new version after one bump.
    from pathlib import Path as _P
    for src_ado in sorted((_P(ROOT) / "stata").glob("*.ado")):
        ado = tmp_path / "stata" / src_ado.name
        assert ado.exists(), (f"{src_ado.name} is not in `declared` "
                              "above, so its banner is never bumped here")
        first = ado.read_text(encoding="utf-8").splitlines()[0]
        assert first.startswith(f"*! {ado.stem} v9.9.9 "), (
            f"{ado.name}'s banner did not move with the bump: {first!r}"
            " - add it to DECLARATIONS in tools/bump_version.py (and to "
            "`declared` above, so it is copied here)")

    # (2) and back again: every file byte-identical, which catches a
    # declaration that is written over, or one the tool cannot undo.
    # (Not one the tool does not know at all: that line never moves,
    # and comes back identical - which is what (1b) is for.)
    bump(here)
    moved = [r for r in declared if before[r] != digests()[r]]
    assert not moved, (
        "a bump round trip changed these files, so a declaration was "
        f"written over or missed: {moved}")


# =====================================================================
# v1.57.1 - external review of 1.57.0 (BACKLOG 411). Every test below
# was broken on purpose before it was believed.
# =====================================================================
def _tool(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        f"_{name}", os.path.join(ROOT, "tools", f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tree(base, files):
    for rel, text in files.items():
        p = os.path.join(base, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)


_GOOD = {"pyproject.toml": 'version = "9.9.9"\n',
         "equipop/__init__.py": '__version__ = "9.9.9"\n',
         "tests/test_x.py": "x", "README.md": "x"}


def test_windows_reserved_names_and_trailing_dots_are_refused():
    """156's pattern saw drive letters, backslashes and refused
    characters. Windows also refuses a reserved device name as ANY
    path component - CON, aux.txt, LPT1.log - and strips a trailing dot
    or space, so two members can land on one file.

    BROKEN WITH: the reserved-name loop removed from windows_problem."""
    mk = _tool("make_release_zip")
    for ok in ("docs/console.py", "a/COM10.txt", "equipop/cells.py"):
        assert mk.windows_problem(ok) is None, ok
    for bad in ("docs/CON", "data/aux.txt", "logs/lpt1.log",
                "a/b./c.md", "a/b /c.md"):
        assert mk.windows_problem(bad), bad
        with pytest.raises(SystemExit, match="REFUSING"):
            mk.check(["README.md", bad])


def test_a_run_record_in_the_tree_is_refused(tmp_path):
    """THE 1.56.0 AND 1.57.0 DEFECT. A scratch script of mine drove the
    simulated Pro door from the tree root with the input
    C:\\Data\\town.gdb\\people; Pro writes its run record beside the
    geodatabase, which on Linux is a folder literally named `C:\\Data`.
    It shipped in two working-tree zips. A run record is never source,
    and carries the local paths of whoever ran it - so it is refused
    wherever it sits, under any name a run writes.

    BROKEN WITH: build() not calling check_run_records."""
    mk = _tool("make_release_zip")
    with pytest.raises(SystemExit, match="run record"):
        mk.check_run_records(
            ["C:\\Data/EquiPop_runs/people_EquiPop_run.csv"])
    for rec in ("examples/people_EquiPop_run.csv", "out/result.meta.json",
                "out/result.meta.txt"):
        root = tmp_path / rec.replace("/", "_")
        _tree(str(root), {**_GOOD, rec: "item,value\n"})
        with pytest.raises(SystemExit, match="run record"):
            mk.build(str(root), "9.9.9", str(root / "_out"),
                     out_name="t.zip", skip_build_outputs=True)
        assert not (root / "_out" / "t.zip").exists(), rec
    mk.check_run_records(["equipop/meta.py", "docs/run_record.md"])


def test_the_bundles_tree_zip_is_built_checked_and_extracted(tmp_path):
    """The reviewer's end-to-end test: a tree holding representative
    junk, through the SAME call make_bundle.sh makes for its working
    tree (`--name equipop_working_tree.zip --skip-build-outputs`), then
    every member name inspected and the archive extracted.

    BROKEN WITH: --skip-build-outputs not honoured (the sidecar the
    bundle generates on purpose is then refused)."""
    mk = _tool("make_release_zip")
    root = tmp_path / "tree"
    _tree(str(root), {**_GOOD,
                      "arcgis/EquiPop.pyt": "x",
                      "arcgis/EquiPop.CountsShares.pyt.xml": "generated",
                      "build/lib/equipop/cells.py": "stale",
                      "dist/equipop-9.9.9.tar.gz": "x",
                      "equipop/__pycache__/cells.cpython-311.pyc": "x",
                      "renamed.egg-info/PKG-INFO": "x",
                      ".pytest_cache/v": "x"})
    out, n = mk.build(str(root), "9.9.9", str(tmp_path / "out"),
                      out_name="equipop_working_tree.zip",
                      skip_build_outputs=True)
    import zipfile
    names = sorted(zipfile.ZipFile(out).namelist())
    assert names == sorted(f"EquiPop-9.9.9/{r}" for r in
                           list(_GOOD) + ["arcgis/EquiPop.pyt"]), names
    assert mk.verify(out, tree_version="9.9.9") == n == 5


def test_verify_refuses_the_zip_1_57_0_shipped(tmp_path):
    """verify() re-opens a FINISHED archive. Fed a zip shaped like the
    one 1.57.0 shipped - the stray run record under `C:\\Data` - it
    must refuse; fed a tree whose stamps disagree, the same.

    BROKEN WITH: verify() skipping the per-name check (it extracts on
    Linux, where `C:\\Data` is a legal folder name)."""
    import zipfile
    mk = _tool("make_release_zip")

    def make(path, extra):
        with zipfile.ZipFile(path, "w") as z:
            for rel, text in {**_GOOD, **extra}.items():
                z.writestr(f"EquiPop-9.9.9/{rel}", text)
        return str(path)

    good = make(tmp_path / "good.zip", {})
    assert mk.verify(good, tree_version="9.9.9") == 4
    shipped = make(tmp_path / "shipped.zip", {
        "C:\\Data/EquiPop_runs/people_EquiPop_run.csv": "item,value\n"})
    with pytest.raises(SystemExit, match="REFUSING shipped.zip"):
        mk.verify(shipped, tree_version="9.9.9")
    # and by NAME alone, where no other rule applies - the run-record
    # rule would otherwise catch the case above on its own
    with pytest.raises(SystemExit, match="reserved device name"):
        mk.verify(make(tmp_path / "aux.zip", {"docs/aux.txt": "x"}))
    with pytest.raises(SystemExit, match="does not say 9.9.9"):
        mk.verify(make(tmp_path / "stale.zip",
                       {"pyproject.toml": 'version = "9.9.8"\n'}),
                  tree_version="9.9.9")


def test_the_bundle_script_builds_its_tree_through_the_safe_builder():
    """What 411 actually was: the protection existed, and the path
    that mattered went round it. So the script must CALL the builder
    for its working tree, verify every zip, and zip no tree itself.

    BROKEN WITH: step 7 restored to `zip -qr ... equipop_working_tree`."""
    src = open(os.path.join(ROOT, "tools", "make_bundle.sh"),
               encoding="utf-8").read()
    code = "\n".join(ln for ln in src.splitlines()
                     if not ln.lstrip().startswith("#"))
    assert re.search(r"make_release_zip\.py \"\$V\" \"\$WORK\" \\\n\s+"
                     r"--name equipop_working_tree\.zip "
                     r"--skip-build-outputs", code), \
        "the working tree is not built by tools/make_release_zip.py"
    assert not re.search(r"zip -q?r[^\n]*equipop_working_tree", code)
    assert "--verify" in code and "--tree-version" in code


def test_the_output_guard_decides_before_anything_is_deleted(tmp_path):
    """make_bundle.sh began `rm -rf "$OUT"`. Reproduced on copies of the
    tree: `tests` deleted every test, `../EquiPop` the repository. The
    decision now lives in tools/bundle_out.py, which DECIDES and never
    deletes - so every dangerous answer can be tested here safely,
    the top of the file system included.

    BROKEN WITH: the inside-the-repository check removed."""
    bo = _tool("bundle_out")
    repo = tmp_path / "repo"
    _tree(str(repo), {"pyproject.toml": "x", "tests/keep.py": "x"})
    home = tmp_path / "home"
    home.mkdir()
    foreign = tmp_path / "foreign"
    _tree(str(foreign), {"precious.txt": "x"})
    made = tmp_path / "made"
    _tree(str(made), {bo.MARKER: "#\n", "MANUAL.md": "x"})
    (tmp_path / "empty").mkdir()
    (tmp_path / "afile").write_text("x")
    top = os.path.abspath(os.sep)
    for out, words in ((repo, "repository itself"),
                       (repo / "tests", "inside the repository"),
                       (repo / "new", "inside the repository"),
                       (tmp_path, "repository is inside it"),
                       (home, "home folder"),
                       (top, "top of a file system"),
                       (foreign, "not empty"),
                       (tmp_path / "afile", "not a plain folder")):
        why = bo.problem(str(repo), str(out), home=str(home))
        assert why and words in why, (out, why)
    for out in (tmp_path / "new", tmp_path / "empty", made):
        assert bo.problem(str(repo), str(out), home=str(home)) is None, out
    # relative paths mean what the caller meant
    here = os.getcwd()
    try:
        os.chdir(repo)
        assert "repository itself" in bo.problem(str(repo), ".",
                                                 home=str(home))
    finally:
        os.chdir(here)


def test_installing_removes_only_what_a_bundle_made(tmp_path):
    """A rebuild into the same folder replaces the bundle and NOTHING
    ELSE - the release note written beside it survives. A file no
    bundle made is never overwritten, and a marker naming anything
    but a plain file name is refused before a byte moves.

    BROKEN WITH: install() clearing every file in the folder."""
    bo = _tool("bundle_out")
    repo, out, work = tmp_path / "repo", tmp_path / "out", tmp_path / "w"
    repo.mkdir()
    _tree(str(work), {"a.zip": "1", "MANUAL.md": "1"})
    bo.install(str(repo), str(work), str(out))
    (out / "RELEASE_9.9.9.md").write_text("mine")
    _tree(str(work), {"a.zip": "2"})                 # MANUAL.md dropped
    rec = bo.install(str(repo), str(work), str(out))
    assert sorted(p.name for p in out.iterdir()) == \
        [bo.MARKER, "RELEASE_9.9.9.md", "a.zip"]
    assert (out / "a.zip").read_text() == "2" and len(rec[0][0]) == 64
    (out / "user.txt").write_text("mine")
    _tree(str(work), {"user.txt": "bundle"})
    with pytest.raises(SystemExit, match="no earlier bundle made"):
        bo.install(str(repo), str(work), str(out))
    assert (out / "user.txt").read_text() == "mine"
    (out / bo.MARKER).write_text("abc  ../repo\n")
    with pytest.raises(SystemExit, match="not a plain file name"):
        bo.install(str(repo), str(work), str(out))


@pytest.mark.skipif(os.name == "nt" or not __import__("shutil").which("bash"),
                    reason="needs bash on a POSIX system")
def test_the_bundle_script_refuses_a_dangerous_output_end_to_end(tmp_path):
    """The script itself, run for real - in a THROWAWAY repository
    holding a copy of it, so a broken guard can only destroy tmp_path.
    Each dangerous output must be refused before anything is built or
    deleted.

    BROKEN WITH: the `bundle_out.py check` line replaced by the 1.57.0
    path arithmetic."""
    import shutil
    import subprocess
    repo = tmp_path / "repo"
    _tree(str(repo), {"pyproject.toml": 'version = "9.9.9"\n',
                      "tests/keep.py": "x"})
    (repo / "tools").mkdir()
    for f in ("make_bundle.sh", "bundle_out.py"):
        shutil.copy(os.path.join(ROOT, "tools", f), repo / "tools" / f)
    foreign = tmp_path / "foreign"
    _tree(str(foreign), {"precious.txt": "x"})
    env = dict(os.environ, HOME=str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    for out, cwd in ((".", repo), ("tests", repo), ("../repo", repo),
                     (str(tmp_path), tmp_path), (str(foreign), tmp_path),
                     (str(tmp_path / "home"), tmp_path)):
        r = subprocess.run(["bash", str(repo / "tools" / "make_bundle.sh"),
                            "9.9.9", out], cwd=cwd, env=env,
                           capture_output=True, text=True, timeout=60)
        assert r.returncode != 0 and "REFUSING" in r.stderr, (out, r.stderr)
        assert (repo / "tests" / "keep.py").exists(), out
        assert (foreign / "precious.txt").exists(), out


def test_the_release_record_counts_what_pytest_reports():
    """BACKLOG 411. The 1.57.0 note's count was true for my machine and
    the reviewer's 1,763 for theirs - geopandas collects two modules
    mine skipped whole. tools/release_record.py now runs the suite from
    the SHIPPED tree zip under each interpreter and states the packages
    behind each count; this pins the one piece of arithmetic in it.

    BROKEN WITH: skips left out of the collected total."""
    rr = _tool("release_record")
    assert rr.collected("1747 passed, 16 skipped in 260.72s") == (
        {"passed": 1747, "skipped": 16}, 1763)
    assert rr.collected("2 failed, 10 passed, 3 skipped, 1 error in 3s")[1] \
        == 16


def test_no_source_file_warns_when_it_is_compiled():
    """v1.59.2, external review of 1.59.1: tools/make_release_zip.py
    held `C:\\Data` in an ordinary docstring - an invalid escape, which
    Python 3.12 reports as a SyntaxWarning every time the tool runs (and
    a later Python will refuse). Every source file is compiled here with
    warnings made errors, so the next one stops the suite instead of
    joining the warnings nobody reads.

    BROKEN WITH: the escape put back into make_release_zip.py."""
    import warnings
    files = []
    for dirpath, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (
            "__pycache__", "dist", "build", ".git", "equipop.egg-info")]
        files.extend(os.path.join(dirpath, n) for n in names
                     if n.endswith((".py", ".pyt")))
    assert len(files) > 100, "the walk found too little"
    bad = []
    for f in files:
        src = open(f, encoding="utf-8").read()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            try:
                compile(src, f, "exec")
            except (SyntaxError, SyntaxWarning, DeprecationWarning) as exc:
                bad.append(f"{os.path.relpath(f, ROOT)}: {exc}")
    assert not bad, "\n".join(bad)


def test_the_bundle_copies_every_pro_sidecar_not_a_list():
    """v1.62.0. make_bundle.sh copied the Pro help sidecars by a written
    list of eight tool names. Tool 0 made nine, and the first 1.62.0
    bundle shipped without tool 0's help - every check green, because
    nothing compared the bundle with the toolbox. It now copies every
    sidecar make_help_xml wrote (one per tool in all_tools) and stops
    if the count differs from the toolbox's.

    BROKEN WITH: the written list restored."""
    src = open(os.path.join(ROOT, "tools", "make_bundle.sh"),
               encoding="utf-8").read()
    assert 'cp arcgis/EquiPop.*.pyt.xml "$WORK/"' in src
    assert "for t in CountsShares" not in src
    assert "Pro help sidecars for $WANT tools" in src
