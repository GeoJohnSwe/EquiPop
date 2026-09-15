# -*- coding: utf-8 -*-
"""test_inventory_doors.py - MACHINE 6 AT BOTH DOORS (BACKLOG 269).

The engine shipped in 1.45.0 with no door of any kind: no GUI, no
runner, no Stata. It was reachable only by writing Python, which the
person this project is built for does not do. These tests drive the
two doors the way a user does and check the TABLE THAT COMES BACK,
not the call.

Each was verified by breaking it on purpose:

  * the lattice column dropped from COLUMNS        -> 1, 4 fail
  * _rows() reading rec["path"] (the shape the
    first draft invented) instead of rec["file"]   -> 2 fails
  * the multi-lattice warning removed              -> 4 fails
  * addFeature's return discarded in the door      -> 5 fails
  * the Pro row builder drifting from the QGIS one -> 6 fails
"""
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "qgis"))

import qgis_stub                                        # noqa: E402
qgis_stub.install()

from qgis.core import QgsProcessingFeedback             # noqa: E402
from equipop_qgis.alg_inventory import (COLUMNS,        # noqa: E402
                                        FolderInventory, _rows)

rasterio = pytest.importorskip("rasterio")


def _tif(path, west, north, cell, crs="EPSG:3006", n=4):
    from rasterio.transform import from_origin
    data = np.arange(n * n, dtype="float32").reshape(n, n)
    with rasterio.open(
            path, "w", driver="GTiff", height=n, width=n, count=1,
            dtype="float32", crs=crs,
            transform=from_origin(west, north, cell, cell)) as dst:
        dst.write(data, 1)


@pytest.fixture
def folder(tmp_path):
    """Three rasters: two on ONE lattice, one on another.

    That is the case the tool exists for. Same CRS and same cell size
    is NOT the same lattice - the origins must also agree modulo the
    cell - so the third file is offset by half a cell, which looks
    identical in any file listing and cannot be merged by index.
    """
    _tif(str(tmp_path / "pop_2020.tif"), 300000, 6500000, 100)
    _tif(str(tmp_path / "pop_2021.tif"), 300000 + 500, 6500000, 100)
    _tif(str(tmp_path / "offset.tif"), 300050, 6500000, 100)
    return tmp_path


def _run(folder, **over):
    alg = FolderInventory()
    alg.initAlgorithm()
    p = {"folder": str(folder), "deep": True, "write": True,
         "OUTPUT": "memory:out"}
    p.update(over)
    fb = QgsProcessingFeedback()
    alg.processAlgorithm(p, None, fb)
    return p["_sinks"]["OUTPUT"].to_frame(), fb


# --- 1, 2: the table is the answer -----------------------------------

def test_1_the_door_returns_one_row_per_file_with_a_lattice(folder):
    df, _ = _run(folder)
    assert len(df) == 3, df
    assert set(df["file"]) == {"pop_2020.tif", "pop_2021.tif",
                               "offset.tif"}
    assert (df["kind"] == "raster").all()
    assert df["lattice"].ne("").all(), "no lattice recorded"


def test_2_the_columns_carry_what_the_engine_gave_them(folder):
    """The first draft of _rows() invented a nested shape - files
    holding layers - and read rec['path'] and rec['pixel_x']. The
    package returns FLAT records with rec['file'] and a two-element
    rec['pixel_size']. Written from memory of what an inventory ought
    to look like, with the engine thirty lines away."""
    df, _ = _run(folder)
    assert (df["cell_size"] == "100 x 100").all(), df["cell_size"].tolist()
    assert (df["crs"].str.contains("3006")).all()
    assert (df["problem"] == "").all()


# --- 3, 4: the lattice is the point ----------------------------------

def test_3_two_files_on_one_grid_share_a_lattice_key(folder):
    """Two rasters offset by a WHOLE number of cells are the same
    lattice and join by index exactly."""
    df, _ = _run(folder)
    keys = dict(zip(df["file"], df["lattice"]))
    assert keys["pop_2020.tif"] == keys["pop_2021.tif"]


def test_4_a_half_cell_offset_is_a_different_lattice_and_is_said(folder):
    """THE FAILURE THIS TOOL EXISTS TO PREVENT. Same CRS, same cell
    size, origin off by half a cell: indistinguishable in a file
    listing, and merging by index silently misaligns every value.
    BACKLOG 239 is the version of this that merged rasters 3,300 km
    apart."""
    df, fb = _run(folder)
    keys = dict(zip(df["file"], df["lattice"]))
    assert keys["offset.tif"] != keys["pop_2020.tif"]
    said = " ".join(fb.info) + " " + " ".join(fb.warnings)
    assert "DIFFERENT LATTICES" in said.upper(), said[:300]


# --- 5: the row loss guard, from the start ---------------------------

def test_5_a_refused_row_stops_the_run(folder):
    """BACKLOG 291's lesson applied to a new door on its first day:
    count what the sink TOOK, never what was offered."""
    from qgis.core import QgsProcessingException
    qgis_stub._Sink.refuse_rows = (1,)
    try:
        with pytest.raises(QgsProcessingException, match="(?i)kept only"):
            _run(folder)
    finally:
        qgis_stub._Sink.refuse_rows = ()


# --- 6: the two doors build the same table ---------------------------

def test_6_pro_and_qgis_produce_the_same_rows(folder):
    """A table whose columns differ between doors is the oldest
    failure in this project (BACKLOG 105, 103, 86). The two row
    builders are separate code - they must not be separate answers."""
    import pandas as pd
    import test_arcgis_stub as H
    # Pro's fake arcpy must be installed before the .pyt will import -
    # it is a module-level `import arcpy` in a file written for Pro.
    H._install_fake_arcpy(pd.DataFrame({"OBJECTID": [1],
                                        "SHAPE@X": [0.0],
                                        "SHAPE@Y": [0.0]}))
    pyt = H._load_pyt()
    from equipop.doors.inventory import inventory
    got = inventory(str(folder), say=lambda *a: None, deep=True,
                    write=False)
    qgis_rows = _rows(got)
    pro_rows = pyt._inventory_rows(got)
    assert [r["file"] for r in qgis_rows] == \
           [r["file"] for r in pro_rows]
    for a, b in zip(qgis_rows, pro_rows):
        assert a == b, (a, b)
    # and both must fill every declared column
    for r in qgis_rows:
        assert set(r) == {nm for nm, _ in COLUMNS}


def test_7_the_json_is_written_and_readable(folder):
    from equipop.doors.inventory import read_inventory
    _run(folder)
    back = read_inventory(str(folder))
    assert back and len(back["files"]) == 3
    assert len(back["lattices"]) == 2


def test_8_not_writing_leaves_the_folder_untouched(tmp_path):
    """A read-only folder, or somebody else's data."""
    _tif(str(tmp_path / "a.tif"), 300000, 6500000, 100)
    before = set(os.listdir(tmp_path))
    df, _ = _run(tmp_path, write=False)
    assert len(df) == 1
    assert set(os.listdir(tmp_path)) == before
