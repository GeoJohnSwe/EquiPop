# -*- coding: utf-8 -*-
"""test_vital_doors.py - the rates and life expectancies reach QGIS and
ArcGIS Pro (v1.60.0, BACKLOG 416).

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "qgis"))
pytest.importorskip("rasterio")

import qgis_stub                                     # noqa: E402
qgis_stub.install()

import test_vital_machine4 as M4                     # noqa: E402
from equipop.doors import vital as V                 # noqa: E402


@pytest.fixture(scope="module")
def folder(tmp_path_factory):
    return str(M4.make_folder(tmp_path_factory.mktemp("ken_doors")))


def _pyt_lists():
    tree = ast.parse((ROOT / "arcgis" / "EquiPop.pyt").read_text(
        encoding="utf-8"))
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(
                node.targets[0], ast.Name) and node.targets[0].id in (
                "RATE_NAMES", "RATE_LABELS", "RATE_SEXES",
                "RATE_SEX_LABELS"):
            out[node.targets[0].id] = ast.literal_eval(node.value)
    return out


def test_both_doors_offer_the_packages_measures_in_its_words():
    """The lists are written into each door (a door must load without
    the package) and pinned here against vital.MEASURES and each other.

    BROKEN WITH: Pro's 'Life expectancy at birth (UNRELIABLE)' without
    its flag."""
    from equipop_qgis import alg_demography as Q
    assert Q.RATE_NAMES == list(V.MEASURES)
    assert Q.RATE_LABELS == [V.MEASURES[n]["label"] for n in Q.RATE_NAMES]
    pro = _pyt_lists()
    for name in ("RATE_NAMES", "RATE_LABELS", "RATE_SEXES",
                 "RATE_SEX_LABELS"):
        assert pro[name] == getattr(Q, name), name


# ------------------------------------------------------------- QGIS
class _Feedback:
    def __init__(self):
        self.lines = []

    def pushInfo(self, m):
        self.lines.append(str(m))

    def pushWarning(self, m):
        self.lines.append("WARNING " + str(m))

    def reportError(self, m, fatal=False):
        self.lines.append("ERROR " + str(m))

    def setProgress(self, *a):
        pass

    def isCanceled(self):
        return False


def _qgis(folder, **over):
    from equipop_qgis.alg_demography import SpatialDemography
    alg = SpatialDemography()
    alg.initAlgorithm()
    p = {"folder": folder, "indices": [], "rates": [0, 3, 4, 6],
         "ratesex": 0, "k": "5000", "unit": 1000.0, "year": "",
         "crs": None, "outcrs": None, "settings": [], "OUTPUT": "memory:"}
    p.update(over)
    fb = _Feedback()
    alg.processAlgorithm(p, {}, fb)
    sink = p.get("_sinks", {}).get("OUTPUT")
    return (sink.to_frame() if sink is not None else None), \
        " ".join(fb.lines)


def test_qgis_runs_rates_alone(folder):
    """No index ticked, four rates: the layer carries them, and the log
    says which are unreliable and where the reference came from.

    BROKEN WITH: the door passing vital= nothing."""
    table, said = _qgis(folder)
    assert {"e60_5000", "e0u_5000", "TFR_5000", "CDR_5000"} <= \
        set(table.columns), list(table.columns)
    assert "UNRELIABLE" in said
    assert "World Population Prospects 2024" in said


def test_qgis_reads_womens_tables_when_asked(folder):
    """BROKEN WITH: box 2d read but not passed on (always both)."""
    _t, said = _qgis(folder, rates=[0], ratesex=1)
    assert "(women, bands 0 to 90+)" in said


def test_qgis_with_nothing_ticked_says_which_boxes(folder):
    """BROKEN WITH: the check asking for an index only."""
    from qgis.core import QgsProcessingException
    with pytest.raises(QgsProcessingException, match="index or rate"):
        _qgis(folder, rates=[])


# --------------------------------------------------------------- Pro
def _pro(folder, tmp_path, **vals):
    import test_arcgis_continental as AC
    pyt, tool, state = AC._tool("SpatialDemography")
    out = str(tmp_path / "rates.shp")
    msg = AC._Messages()
    tool.execute(AC._params(tool, folder=folder, k="5000", unit=1000.0,
                            out=out, **vals), msg)
    return state["written"][out]["table"], " ".join(msg.log)


def test_pro_runs_rates_alone(folder, tmp_path):
    """BROKEN WITH: Pro's door ignoring the rates box."""
    table, said = _pro(folder, tmp_path, indices="",
                       rates="Life expectancy at 60;Total fertility rate")
    assert {"e60_5000", "TFR_5000"} <= set(table.columns)
    assert "national reference, KEN" in said


def test_pro_reads_mens_tables_when_asked(folder, tmp_path):
    """BROKEN WITH: Pro's sex box read but not passed on."""
    _t, said = _pro(folder, tmp_path, indices="",
                    rates="Life expectancy at 60", ratesex="Men")
    assert "(men, bands 0 to 90+)" in said


def test_pro_refuses_a_rate_it_does_not_have(folder, tmp_path):
    """BROKEN WITH: unknown labels skipped silently."""
    import test_arcgis_continental as AC
    pyt, tool, state = AC._tool("SpatialDemography")
    with pytest.raises(pyt.arcpy.ExecuteError, match="No such rate"):
        tool.execute(AC._params(tool, folder=folder, k="5000",
                                unit=1000.0, indices="",
                                rates="Life expectancy at 70",
                                out=str(tmp_path / "x.shp")),
                     AC._Messages())
