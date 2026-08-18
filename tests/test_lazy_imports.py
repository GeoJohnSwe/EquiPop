"""BACKLOG 176 - what `import equipop` drags into the process.

Every compiled library loaded into Stata's Python is a chance for the
session to die before EquiPop is reached, and the death is never
recognisable as ours. Two real ones, both costing days:

  - v1.37, Umut's Mac: pandas built for Intel inside an Apple-Silicon
    Stata. The loader refuses to mix processors and the import stops.
  - v1.35, John's Windows: Stata plus Anaconda, two copies of the same
    maths library in one process. `import numpy` closes Stata outright
    with no error and no return code.

Until 1.37, `import equipop` loaded five compiled libraries - numpy,
pandas, scipy, pyproj and matplotlib - for a Stata command that needs
three of them. These tests hold the line at the level the USER meets
it: a clean interpreter, `import equipop`, and a look at what arrived.

They must run in a SUBPROCESS. Once pytest has imported anything, the
libraries are in sys.modules for good and an in-process assertion
would pass for the wrong reason.
"""

import json
import subprocess
import sys

import pytest

HEAVY = ["numpy", "pandas", "scipy", "pyproj", "matplotlib",
         "rasterio", "geopandas"]

# What the Stata command genuinely needs. Machine 1 counts people and
# does statistics on them; it neither projects nor draws.
STATA_PATH_ALLOWS = {"numpy", "pandas", "scipy"}


def _in_fresh_python(code):
    """Run code in a clean interpreter and return its parsed stdout."""
    r = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


def _loaded_after(statement):
    return _in_fresh_python(
        "import sys, json\n"
        f"{statement}\n"
        f"print(json.dumps([m for m in {HEAVY!r} if m in sys.modules]))\n")


def test_importing_equipop_loads_no_compiled_library():
    """The headline. `import equipop` should cost nothing."""
    loaded = _loaded_after("import equipop")
    assert loaded == [], (
        f"import equipop pulled in {loaded}. Something has been added "
        f"back to equipop/__init__.py as a module-level import - put it "
        f"in _LAZY instead. Every one of these is a way for Stata to "
        f"fail before EquiPop is reached.")


def test_the_stata_path_loads_only_what_it_needs():
    """What Umut's Mac actually has to have working.

    The Stata glue does `from equipop.stata_bridge import ...`. Before
    1.37 that route loaded pyproj and matplotlib too, so a fault in
    either broke a command that never touches them.
    """
    loaded = set(_loaded_after(
        "from equipop.stata_bridge import knn_to_rows, to_stata_values"))
    assert loaded <= STATA_PATH_ALLOWS, (
        f"the Stata path now loads {sorted(loaded - STATA_PATH_ALLOWS)} "
        f"as well. A Stata user must install and keep working every "
        f"library on this list.")
    assert "numpy" in loaded, "sanity: the bridge really should use numpy"


def test_the_doctor_runs_without_the_libraries_it_reports_on():
    """The diagnostic must survive the machine it was written for.

    If importing equipop.doctor loaded numpy, then on the machine where
    numpy is what is broken the doctor would die instead of explaining.
    """
    loaded = _loaded_after("import equipop.doctor")
    assert loaded == [], (
        f"equipop.doctor pulled in {loaded} - it must stay standard "
        f"library only, or it cannot run on a machine whose compiled "
        f"libraries are the fault.")


def test_projection_still_loads_pyproj_when_asked():
    """The other half: lazy must not mean absent.

    A trim that quietly stopped projection working would be worse than
    the problem it solves.
    """
    pytest.importorskip("pyproj")
    loaded = _loaded_after(
        "import equipop\n"
        "f = equipop.project_to_metric")
    assert "pyproj" in loaded, (
        "asking for project_to_metric did not load pyproj - the name is "
        "resolving to something else, or _LAZY points at the wrong "
        "module")


def test_every_public_name_still_resolves():
    """Parity with 1.36's surface.

    _LAZY is hand-written, so a typo in a module name would remove a
    public function and nothing else would notice until a door called
    it.
    """
    import equipop

    for name in equipop.__all__:
        assert hasattr(equipop, name), (
            f"{name} is in __all__ but does not resolve - check its "
            f"entry in _LAZY")

    for name, where in equipop._LAZY.items():
        obj = getattr(equipop, name)
        assert obj is not None
        home = getattr(obj, "__module__", "")
        if home:
            assert home.endswith(where), (
                f"{name} resolved out of {home}, but _LAZY says "
                f"{where}")


def test_star_import_gives_what_it_used_to():
    ns = {}
    exec("from equipop import *", ns)          # noqa: S102 - the test
    import equipop
    for name in equipop.__all__:
        assert name in ns, f"from equipop import * lost {name}"


def test_submodules_are_reachable_as_attributes():
    """`equipop.cells` used to work because __init__ imported it.

    Door code and the Book both do this, so laziness must not take it
    away.
    """
    import equipop
    assert equipop.cells.__name__ == "equipop.cells"
    assert equipop.stata_bridge.__name__ == "equipop.stata_bridge"


def test_an_unknown_name_still_raises_attributeerror():
    """A module __getattr__ that raises the wrong exception type breaks
    hasattr(), and hasattr is how optional features are detected."""
    import equipop
    with pytest.raises(AttributeError):
        equipop.no_such_function
    assert not hasattr(equipop, "no_such_function")


def test_names_resolve_even_when_an_optional_library_is_absent():
    """A name whose module defers its heavy import must still resolve.

    read_table lives in io.py, which uses geopandas - but fetches it
    inside the functions that need it. So the NAME must be reachable on
    a machine with no geopandas, and the complaint must come later,
    from the function, about the specific format it cannot read. This
    is why _EXTRAS lists viz and nothing else.
    """
    import equipop
    try:
        import geopandas                       # noqa: F401
    except ImportError:
        pass
    else:
        pytest.skip("geopandas is installed here, nothing to prove")

    assert callable(equipop.read_table)


def test_a_module_that_cannot_import_names_the_library_and_the_extra(
        monkeypatch):
    """The wrap itself, proved without breaking a real library.

    A bare ModuleNotFoundError from three files down does not tell a
    user what to install. _EXTRAS exists to turn it into a sentence.
    """
    import equipop

    monkeypatch.setitem(equipop._LAZY, "_probe_name", "_probe_module")
    monkeypatch.setitem(equipop._EXTRAS, "_probe_module",
                        ("somelib", "geo"))
    with pytest.raises(ImportError) as exc:
        equipop._probe_name
    text = str(exc.value)
    assert "somelib" in text
    assert "equipop[geo]" in text


def test_an_unlisted_module_failure_is_not_disguised(monkeypatch):
    """The other direction: a module that fails for a reason we have
    NOT anticipated must surface its own error, not a made-up one about
    a missing extra."""
    import equipop

    monkeypatch.setitem(equipop._LAZY, "_probe_name2", "_probe_module2")
    with pytest.raises(ImportError) as exc:
        equipop._probe_name2
    assert "equipop[" not in str(exc.value)
