# -*- coding: utf-8 -*-
"""BACKLOG 466: barriers and the elevation raster are placed in THIS
run's coordinate system - not the previous run's, and not their own.

Found in the code review of 1.63.7 (10 November 2026). Three faults
with one cause: the coordinate system a run works in was remembered
on a function attribute that only ONE of the two reading routes set.

1. A TABLE run (X/Y columns) never set it. In one Pro session, after
   a run on a feature class, a table run converted its line and
   polygon barriers into the EARLIER layer's coordinate system, and
   checked its elevation raster against that layer too. BACKLOG 329
   fixed exactly this for the text in the manifest and left the
   object that does the converting.
2. POINT barriers were never converted at all; lines and polygons
   were.
3. A barrier RASTER was never checked. John's ruling of 313 - a
   raster in another coordinate system is refused, an undefined one
   is refused - reached the elevation raster only.

The stand-in arcpy records which spatial reference each reader was
handed; that is the thing the toolbox decides.
"""
import types

import numpy as np
import pandas as pd
import pytest

from test_arcgis_stub import (_install_fake_arcpy, _load_pyt, _Messages,
                              _geom)


def _sr(code, name=None):
    return types.SimpleNamespace(factoryCode=code,
                                 name=name or f"EPSG {code}",
                                 type="Projected",
                                 linearUnitName="Meter")


def _session():
    """One Pro session: a feature class 'people' in EPSG:3006, a plain
    table 'tbl' of the same places, a river and an elevation raster."""
    left_y = np.arange(50.0, 550.0, 100.0)
    xs = np.r_[np.full(5, 1450.0), np.full(5, 1650.0)]
    ys = np.r_[left_y, left_y]
    t = pd.DataFrame({"OBJECTID": np.arange(1, 11),
                      "SHAPE@X": xs, "SHAPE@Y": ys})
    state = _install_fake_arcpy(t)
    state["crs_codes"] = {"people": 3006}
    state["aux_tables"] = {"tbl": pd.DataFrame({"Easting": xs,
                                                "Northing": ys})}
    river = [(1550.0, -50.0), (1550.0, 1050.0)]
    state["shape_types"] = {"roads": "Polyline", "dem": "Raster"}
    state["geom_layers"] = {"roads": [(_geom([river]), 6.0)]}
    state["layers"] = {}
    state["rasters"] = {"dem": {
        "array": np.tile(np.linspace(0.0, 30.0, 20), (20, 1)),
        "xmin": 0.0, "ymax": 2000.0, "cw": 100.0, "ch": 100.0,
        "nodata": None}}
    import arcpy
    seen = []
    real = arcpy.da.SearchCursor

    class Cursor(real):
        def __init__(self, layer, fields, spatial_reference=None):
            seen.append((str(layer), spatial_reference))
            super().__init__(layer, fields,
                             spatial_reference=spatial_reference)

    arcpy.da.SearchCursor = Cursor
    return state, _load_pyt(), seen


def _for(seen, layer):
    # the toolbox reads through the catalog path ("memory/roads")
    got = [sr for name, sr in seen if name.endswith(layer)]
    assert got, f"{layer} was never read"
    return got[-1]


def test_a_table_run_does_not_inherit_the_previous_runs_system(tmp_path):
    """BROKEN WITH: the tabular branch of _read_input not setting
    last_sr - the river is handed EPSG:3006, left by the run before."""
    state, pyt, seen = _session()
    pyt._run_tool("counts", "people", _Messages(), k_text="5",
                  barrier="roads", barrier_field="cost", tau_text="4")
    assert _for(seen, "roads").factoryCode == 3006     # its own run
    del seen[:]
    msg = _Messages()
    pyt._run_tool("counts", "tbl", msg, k_text="5",
                  barrier="roads", barrier_field="cost", tau_text="4",
                  out_table=str(tmp_path / "out1.csv"))
    assert _for(seen, "roads") is None, (
        "the table declares no coordinate system, so there is nothing "
        "to convert the barrier into - least of all the last layer's")
    assert any("NO COORDINATE SYSTEM" in m for m in msg.log)


def test_a_declared_system_is_what_the_barriers_are_converted_into(tmp_path):
    state, pyt, seen = _session()
    pyt._run_tool("counts", "people", _Messages(), k_text="5",
                  barrier="roads", barrier_field="cost", tau_text="4")
    del seen[:]
    msg = _Messages()
    pyt._run_tool("counts", "tbl", msg, k_text="5",
                  barrier="roads", barrier_field="cost", tau_text="4",
                  out_table=str(tmp_path / "out2.csv"), table_crs=_sr(3035))
    assert _for(seen, "roads").factoryCode == 3035
    assert not any("NO COORDINATE SYSTEM" in m for m in msg.log)


def test_the_elevation_raster_is_not_checked_against_the_last_layer(tmp_path):
    """After a run on EPSG:3006 points, a table run with a raster in
    another system must not be refused in the NAME of that earlier
    layer. With nothing declared there is nothing to compare; with a
    system declared, the comparison is against that one.
    BROKEN WITH: the tabular branch not setting last_sr - "The
    elevation raster is in ... but the analysis is running in
    SWEREF99 TM"."""
    state, pyt, seen = _session()
    state["crs_codes"]["dem"] = 32633
    pyt._run_tool("counts", "people", _Messages(), k_text="5")
    msg = _Messages()
    pyt._run_tool("counts", "tbl", msg, k_text="5", extra_dem="dem",
                  tau_text="4", out_table=str(tmp_path / "out3.csv"))
    assert any("NO COORDINATE SYSTEM" in m for m in msg.log)
    # declared the same as the raster: runs, and says nothing
    msg = _Messages()
    pyt._run_tool("counts", "tbl", msg, k_text="5", extra_dem="dem",
                  tau_text="4", out_table=str(tmp_path / "out4.csv"),
                  table_crs=_sr(32633))
    assert not any("NO COORDINATE SYSTEM" in m for m in msg.log)
    # declared different: refused, naming the DECLARED system
    with pytest.raises(Exception) as e:
        pyt._run_tool("counts", "tbl", _Messages(), k_text="5",
                      extra_dem="dem", tau_text="4",
                      out_table=str(tmp_path / "out5.csv"),
                      table_crs=_sr(3035, "ETRS89 LAEA"))
    assert "ETRS89 LAEA" in str(e.value)
    assert "will not reproject" in str(e.value)


def test_point_barriers_are_converted_like_lines_and_polygons():
    """The stand-in converts as real arcpy does when handed a spatial
    reference (here: degrees to the metres of UTM 33). A barrier point
    at 15.001 E, 0.0005 N lies 111 m east and 55 m north of the
    zone's origin: cell (150, 50). Read by its own numbers it would be
    cell (50, 50).
    BROKEN WITH: _read_columns called without sr=main_sr."""
    state, pyt, seen = _session()
    state["layers"] = {"spots": pd.DataFrame(
        {"SHAPE@X": [15.001], "SHAPE@Y": [0.0005], "cost": [6.0]})}
    state["shape_types"]["spots"] = "Point"
    fr = pyt._barrier_frame("spots", "cost", "additive (sum)", 100.0,
                            _sr(32633), None, None, _Messages())
    assert set(zip(fr.x, fr.y, fr.friction)) == {(150.0, 50.0, 6.0)}
    # and with no analysis system known they are read as they are
    fr = pyt._barrier_frame("spots", "cost", "additive (sum)", 100.0,
                            None, None, None, _Messages())
    assert set(zip(fr.x, fr.y, fr.friction)) == {(50.0, 50.0, 6.0)}


def _grid(state):
    state["shape_types"]["grid"] = "Raster"
    state["rasters"]["grid"] = {
        "array": np.array([[5.0, 0.0], [0.0, 7.0]]),
        "xmin": 0.0, "ymax": 200.0, "cw": 100.0, "ch": 100.0,
        "nodata": None}


def test_a_barrier_raster_in_another_system_is_refused():
    """BROKEN WITH: the raster branch of _barrier_frame without
    _barrier_crs_ok - the raster is sampled where its numbers land."""
    state, pyt, seen = _session()
    _grid(state)
    state["crs_codes"]["grid"] = 32633
    with pytest.raises(Exception) as e:
        pyt._barrier_frame("grid", None, "", 100.0, _sr(3006, "SWEREF99 TM"),
                           None, None, _Messages())
    assert "will not reproject a raster" in str(e.value)
    assert "The barrier raster" in str(e.value)
    # the same system: read
    fr = pyt._barrier_frame("grid", None, "", 100.0, _sr(32633),
                            None, None, _Messages())
    assert len(fr) == 2
    # nothing to compare with: read, as before
    fr = pyt._barrier_frame("grid", None, "", 100.0, None, None, None,
                            _Messages())
    assert len(fr) == 2


@pytest.mark.parametrize("layer,what", [("grid", "The barrier raster"),
                                        ("roads", "The barrier layer")])
def test_a_barrier_with_no_coordinate_system_is_refused(layer, what):
    """BACKLOG 313's second ruling, which had a test of the helper
    ("The barrier layer") and no caller in the barrier reader.
    BROKEN WITH: _barrier_crs_ok not called for that kind."""
    state, pyt, seen = _session()
    _grid(state)
    import arcpy
    real = arcpy.Describe

    def describe(v):
        d = real(v)
        if str(v).endswith(layer):
            d.spatialReference = types.SimpleNamespace(
                factoryCode=0, name="Unknown")
        return d

    arcpy.Describe = describe
    with pytest.raises(Exception) as e:
        pyt._barrier_frame(layer, "cost", "", 100.0, _sr(3006),
                           None, None, _Messages())
    assert "NO COORDINATE SYSTEM" in str(e.value)
    assert what in str(e.value)
