# -*- coding: utf-8 -*-
"""conftest.py - BACKLOG 101: keep the repository clean.

Running the suite used to leave files like

    C:\\Data\\Kayseri_EquiPop_run.csv
    C:\\Data\\gridby_points_EquiPop_run.csv
    memory/lyr_EquiPop_run.csv

in the REPOSITORY ROOT, and seven of them are committed to main.
They have been on John's list since v1.24 and they refused the
release build twice in the 1.30 series, which is the only reason
they did not ship inside a zip.

WHY THEY APPEAR, because it is not a bug in the writers. The ArcGIS
tests hand the toolbox realistic Windows catalog paths - that IS
their job, since they are simulating Pro on Windows. On Windows
`C:\\Data\\x_EquiPop_run.csv` is a path and the sidecar lands beside
the output, correctly. On Linux a backslash is an ordinary character,
so the whole thing is one long FILENAME and it lands in whatever
directory the suite happens to be standing in.

WHY NO PRODUCT-SIDE GUARD WOULD DO. The obvious fix - refuse to write
a sidecar when the output's folder does not exist - cannot tell that
case apart from a user legitimately passing a relative `out.csv` and
expecting the manifest beside it. Both have an empty directory
component. Refusing would break the honest case to tidy up after the
dishonest one, and John's own testing writes relative paths.

So the suite works somewhere else instead. This is the only thing
that holds no matter what a future test does with a path, which is
the property worth having: the repository cannot be polluted by a
test that has not been written yet.

The fixture also FAILS THE RUN if anything new turns up in the root
anyway, so a test that writes there by absolute path is reported
rather than silently tidied.
"""
import os
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Directories the tooling legitimately creates in the root.
_ALLOWED = {".pytest_cache", "__pycache__", "equipop.egg-info",
            "build", "dist", ".coverage", ".mypy_cache", ".ruff_cache"}


@pytest.fixture(scope="session", autouse=True)
def work_outside_the_repository(tmp_path_factory):
    """Run the whole suite from a temporary directory.

    Tests that need repository files already resolve them from
    __file__ rather than from the working directory - that is why
    every test module computes ROOT at the top - so moving is safe.
    """
    before = {p.name for p in ROOT.iterdir()}
    here = os.getcwd()
    os.chdir(tmp_path_factory.mktemp("equipop_run"))
    try:
        yield
    finally:
        os.chdir(here)

    after = {p.name for p in ROOT.iterdir()}
    strays = sorted(after - before - _ALLOWED)
    if strays:
        raise AssertionError(
            "BACKLOG 101: the test suite wrote into the repository "
            "root:\n    " + "\n    ".join(strays) +
            "\n\nThese are almost certainly run manifests or field "
            "files. Point the test at tmp_path instead - the "
            "repository is not a scratch directory, and anything "
            "left here can be committed by accident and shipped "
            "inside a release zip.")


@pytest.fixture(scope="session", autouse=True)
def toolbox_settings_of_its_own(tmp_path_factory):
    """v1.62.0, BACKLOG 438. Tool 0 SAVES a choice - which tools the
    GIS toolboxes show - in the user's own settings folder, and the
    doors read it. The suite must neither read the developer's real
    choice (a test of the default would pass or fail by whoever runs
    it) nor overwrite it. So the settings folder is a temporary one,
    and the environment override is cleared: every run starts from
    John's default, tools 3 to 6 hidden."""
    keep = {k: os.environ.get(k) for k in
            ("APPDATA", "XDG_CONFIG_HOME", "EQUIPOP_SHOW_ALL_TOOLS")}
    home = tmp_path_factory.mktemp("settings")
    os.environ["APPDATA"] = str(home)
    os.environ["XDG_CONFIG_HOME"] = str(home)
    os.environ.pop("EQUIPOP_SHOW_ALL_TOOLS", None)
    try:
        yield
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
