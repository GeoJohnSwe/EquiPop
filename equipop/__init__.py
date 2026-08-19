"""
EquiPop Pangea - k-nearest neighbour contextual analysis on gridded data.

Bespoke neighbourhoods around every location instead of administrative
boundaries: the nearest k people, the radius needed to reach them
(Dist_k), and what that neighbourhood contains.

Engines: radial counts and shares (fastcounts), value statistics
(analysis), effort over a friction surface (friction) and over terrain
(slope), distance decay with fixed or variable bandwidth (decay), and
tiled continental runs (bigrun). Post-analysis: segregation,
accessibility, FCA, spatial autocorrelation, areas.

Doors: a QGIS Processing plugin, an ArcGIS Pro toolbox, and Stata
commands. The doors move data and explain parameters; this package
calculates.

(This docstring said "no friction, no decay yet - those come in Phase
2" until 1.29.9 - BACKLOG 121.)

WHY THE IMPORTS BELOW LOOK ODD - BACKLOG 176, v1.37
---------------------------------------------------
Nothing heavy is loaded when you type `import equipop`. The names are
fetched from their modules the first time somebody asks for one.

`equipop.run_knn`, `from equipop import run_knn` and
`import equipop.analysis` all behave exactly as before; the only
difference is WHEN the work happens.

The reason is Stata. Every compiled library loaded into Stata's Python
is a chance for the session to fail before EquiPop is reached, and the
failure is never recognisable as ours:

  - a library built for the wrong processor stops the import dead
    (Umut's Mac, 1.37: an Intel pandas inside an Apple-Silicon Stata);
  - two copies of the same maths library in one process close Stata
    outright, with no error at all (Windows plus Anaconda, 1.35).

Until 1.37 `import equipop` loaded five compiled libraries - numpy,
pandas, scipy, pyproj and matplotlib - for a Stata command that needs
three. pyproj and matplotlib were loaded on every run by users who
never asked to project anything or draw anything, and a fault in
either took the whole package down with it. Now a broken pyproj
breaks projection and nothing else.

Keep it that way: DO NOT add a module-level `from .x import y` here.
tests/test_lazy_imports.py imports the package in a clean subprocess
and fails if any of the optional libraries arrive uninvited.
"""

from importlib import import_module as _import_module

__version__ = "1.40.6"

# name -> the module it lives in. This is the whole public surface;
# adding a name here is how a new export is published.
_LAZY = {
    "project_to_metric": "transform",
    "snap_to_grid": "transform",
    "run_knn": "analysis",
    "run_knn_stats": "analysis",
    "Decay": "decay",
    "build_cells": "cells",
    "CellData": "cells",
    "run_knn_friction": "friction",
    "load_friction_table": "friction",
    "suggest_projection": "projection",
    "suggest_projection_xy": "projection",
    "assign_zones": "projection",
    "read_table": "io",
    "save_output": "io",
    "list_layers": "io",
    "fetch": "fetch",
    "build_hex_cells": "hex",
    "RunLog": "meta",
    "load_meta": "meta",
    "run_knn_counts": "fastcounts",
    "seg_profile": "segregation",
    "aggregate_output": "area",
    "area_stats": "area",
    "map_output": "viz",
    "run_knn_slope": "slope",
    "dem_to_cell_altitude": "slope",
    "SLOPE_MODELS": "slope",
    "slope_penalty": "slope",
    "potential_surface": "access",
    "opportunity_horizon": "access",
    "effort_potential": "access",
    "fca": "fca",
    "fca_segments": "fca",
    "fca_propensity": "fca",
    "build_weights": "autocorr",
    "morans_i": "autocorr",
    "local_morans": "autocorr",
    "local_g": "autocorr",
    "getis_g": "autocorr",
    "autocorr_profile": "autocorr",
}

# Submodules reachable as attributes after a plain `import equipop`,
# which is what they were when every one of them was imported here.
_SUBMODULES = frozenset({
    "access", "analysis", "area", "autocorr", "bigrun", "categorical",
    "cells", "datasets", "decay", "doctor", "doors", "fastcounts",
    "fca", "fetch", "friction", "gridby", "hex", "io", "meta",
    "overshoot", "projection", "raster", "segregation", "selfpot",
    "slope", "stata_bridge", "stats", "transform", "viz", "wstats",
})

# Modules that cannot even be IMPORTED without an optional library,
# and the one line each that tells a user what to install.
#
# Only viz is on this list, and that is worth knowing rather than
# guessing at: io, area, friction, slope and raster already fetch
# geopandas and rasterio inside the functions that use them, so those
# modules import perfectly well without either. Their absence is
# reported by the function that needed them, which is the better place
# for it. Checked, not assumed - tests/test_lazy_imports.py resolves
# read_table in an environment with no geopandas at all.
_EXTRAS = {
    "viz": ("matplotlib", "viz"),
}

__all__ = ["project_to_metric", "snap_to_grid", "run_knn", "Decay", "run_knn_stats", "build_cells", "CellData", "run_knn_friction", "load_friction_table", "suggest_projection", "suggest_projection_xy", "assign_zones", "read_table", "save_output", "fetch", "build_hex_cells", "RunLog", "load_meta", "list_layers", "run_knn_counts", "seg_profile", "aggregate_output", "map_output"]


def __getattr__(name):
    """Fetch a public name from its module on first use (PEP 562).

    Caches into globals(), so the cost is paid once and every later
    lookup is an ordinary attribute read.
    """
    where = _LAZY.get(name)
    if where is None:
        if name in _SUBMODULES:
            mod = _import_module("." + name, __name__)
            globals()[name] = mod
            return mod
        raise AttributeError(
            f"module 'equipop' has no attribute {name!r}")

    try:
        mod = _import_module("." + where, __name__)
    except ImportError as exc:
        extra = _EXTRAS.get(where)
        if extra is None:
            raise
        lib, tag = extra
        raise ImportError(
            f"equipop.{name} needs {lib}, which is not installed here "
            f"(pip install equipop[{tag}]). Everything that does not "
            f"use {lib} still works.\n  original error: {exc}"
        ) from exc

    value = getattr(mod, name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(_LAZY) | set(_SUBMODULES))
