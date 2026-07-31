"""
make_gridby.py - kept as a forwarding shim (1.19.0).

Gridby now lives in the package, at equipop/gridby.py, so that
`load("gridby")` works for someone who installed EquiPop with pip
rather than cloning the repository. This file remains so that older
scripts and notebooks doing `from make_gridby import gridby` keep
working. New code should use:

    from equipop.gridby import gridby        # or
    from equipop.datasets import load; g = load("gridby")
"""
from equipop.gridby import (gridby, SEED, NX, NY, U, RIVER_COL,   # noqa: F401
                            BRIDGE_ROW, HILL)
