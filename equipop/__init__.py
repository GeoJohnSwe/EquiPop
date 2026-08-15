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
"""

from .transform import project_to_metric, snap_to_grid
from .analysis import run_knn
from .decay import Decay
from .analysis import run_knn_stats
from .cells import build_cells, CellData
from .friction import run_knn_friction, load_friction_table
from .projection import (suggest_projection,
                         suggest_projection_xy, assign_zones)
from .io import read_table, save_output
from .fetch import fetch
from .hex import build_hex_cells
from .meta import RunLog, load_meta
from .io import list_layers
from .fastcounts import run_knn_counts
from .segregation import seg_profile
from .area import aggregate_output
try:
    from .viz import map_output
except ImportError:                       # matplotlib is an optional extra
    def map_output(*a, **k):
        raise ImportError("map_output needs matplotlib: "
                          "pip install equipop[viz]")

__version__ = "1.35"
__all__ = ["project_to_metric", "snap_to_grid", "run_knn", "Decay", "run_knn_stats", "build_cells", "CellData", "run_knn_friction", "load_friction_table", "suggest_projection", "suggest_projection_xy", "assign_zones", "read_table", "save_output", "fetch", "build_hex_cells", "RunLog", "load_meta", "list_layers", "run_knn_counts", "seg_profile", "aggregate_output", "map_output"]

from .slope import run_knn_slope, dem_to_cell_altitude, SLOPE_MODELS, slope_penalty
from .area import area_stats
from .access import potential_surface, opportunity_horizon, effort_potential
from .fca import fca, fca_segments
from .autocorr import build_weights, morans_i, local_morans, local_g, getis_g, autocorr_profile
from .fca import fca_propensity
