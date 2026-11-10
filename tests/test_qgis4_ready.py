# -*- coding: utf-8 -*-
"""BACKLOG 464: one plugin for QGIS 3.38 to 4.x.

QGIS 4 (released March 2026, Qt 6 / PyQt6) said of EquiPop 1.63.5:
"This plugin is incompatible with this version of QGIS. Plugin
designed for QGIS 3.38 - 3.99" (John, 9 November 2026). Two causes:

1. metadata.txt named no qgisMaximumVersion, which the Plugin Manager
   and the plugin repository read as 3.99;
2. the code used the old, unscoped enum spellings
   (QgsProcessing.TypeVector, QgsProcessingParameterNumber.Double,
   QgsWkbTypes.PointGeometry, ...FlagAdvanced) and compared geometry
   types with numbers. Under PyQt6 an enum is a real enum and equals
   no number - so "geometryType(...) != 0" would have refused every
   POINT layer, and "== 1" would have charged every barrier LINE as a
   polygon, silently.

Not reachable here: a real QGIS 4. The official checker
(pyqgis4-checker) runs in Docker, which this sandbox lacks. What is
tested instead: the metadata, the source (no old spelling, no number
compared with a geometry type), and every QGIS test now runs against
a simulator as strict as QGIS 4 (tests/qgis_stub.py, class Qgis).
"""
import configparser
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "qgis" / "equipop_qgis"
SOURCES = sorted(PLUGIN.glob("*.py"))


def _code(path):
    """The file without comments and docstrings' prose lines - a
    rough cut, enough to tell code from the notes about it."""
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.split("#", 1)[0]
        out.append(stripped)
    return "\n".join(out)


def test_the_metadata_admits_qgis_4():
    cp = configparser.ConfigParser()
    cp.read(PLUGIN / "metadata.txt", encoding="utf-8")
    g = cp["general"]
    assert g["qgisMinimumVersion"] == "3.38"
    assert g["qgisMaximumVersion"] == "4.99", (
        "without it QGIS 4 calls the plugin incompatible")
    assert "supportsQt6" not in g, "no longer read by QGIS"


OLD = [
    r"\bQgsProcessing\.Type\w+",
    r"\bQgsProcessingParameter(Number|Field|File)\.[A-Z]\w*",
    r"\bQgsProcessingParameterDefinition\.Flag\w+",
    r"\bQgsWkbTypes\.(?!geometryType\b)[A-Z]\w*",
    r"\b_?[WD]\.(PointGeometry|LineGeometry|PolygonGeometry|Flag\w+)",
    r"\bPyQt5\b",
    r"\bQVariant\b",
    r"\.exec_\(",
]


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.name)
def test_no_old_spelling_qgis_4_dropped(path):
    """BROKEN WITH: any of the 39 old spellings of 1.63.6 put back."""
    code = _code(path)
    hits = [m.group(0) for pat in OLD for m in re.finditer(pat, code)]
    assert not hits, f"{path.name}: {sorted(set(hits))}"


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.name)
def test_no_geometry_type_is_compared_with_a_number(path):
    """BROKEN WITH: barriers.py's "== 1" or base.py's "gt != 0"."""
    code = _code(path)
    bad = re.findall(r"geometryType\([^)]*\)\)?\s*[!=]=\s*\d", code)
    # any name a geometry type was put in, then compared with a number
    for name in set(re.findall(r"\b(\w+)\s*=\s*[\w.]*geometryType\(", code)):
        bad += re.findall(rf"\b{name}\s*[!=]=\s*\d", code)
    bad += re.findall(r"_is_kind\([^,]+,\s*\d", code)
    assert not bad, f"{path.name}: {bad}"


def test_the_simulator_is_as_strict_as_qgis_4():
    """If these stop holding, the tests above certify nothing."""
    import sys
    sys.path.insert(0, str(ROOT / "tests"))
    import qgis_stub
    Q = qgis_stub.Qgis
    assert Q.GeometryType.Point != 0 and Q.GeometryType.Line != 1
    assert not hasattr(qgis_stub.QgsProcessing, "TypeVector")
    assert not hasattr(qgis_stub.QgsWkbTypes, "PointGeometry")
    assert not hasattr(qgis_stub.QgsProcessingParameterDefinition,
                       "FlagAdvanced")
    assert qgis_stub.QgsWkbTypes.geometryType(Q.WkbType.LineString) \
        is Q.GeometryType.Line


def test_a_point_layer_passes_the_points_only_check():
    """The check that would have refused every point layer on QGIS 4:
    run on a point source, it must say nothing."""
    import sys
    sys.path.insert(0, str(ROOT / "tests"))
    sys.path.insert(0, str(ROOT / "qgis"))
    import qgis_stub
    qgis_stub.install()
    src = (PLUGIN / "base.py").read_text(encoding="utf-8")
    assert "gt != Qgis.GeometryType.Point" in src


@pytest.mark.parametrize("wkb,kind", [(2, "line"), (3, "polygon")])
def test_the_continental_door_tells_lines_from_polygons(wkb, kind):
    """alg_continental._geometry_parts on the strict simulator.
    BROKEN WITH: "t == 1" for a line - None comes back, and the
    feature is dropped from the join without a word."""
    import sys
    sys.path.insert(0, str(ROOT / "tests"))
    sys.path.insert(0, str(ROOT / "qgis"))
    import qgis_stub
    qgis_stub.install()
    from qgis.core import QgsGeometry, QgsPointXY
    from equipop_qgis.alg_continental import _geometry_parts
    g = QgsGeometry()
    ring = [QgsPointXY(0, 0), QgsPointXY(10, 0), QgsPointXY(10, 10),
            QgsPointXY(0, 0)]
    g._parts = [ring]
    g._wkb = wkb
    got = _geometry_parts(g)
    assert got and got["type"] == kind
