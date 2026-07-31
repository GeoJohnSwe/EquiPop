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
