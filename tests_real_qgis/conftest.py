# -*- coding: utf-8 -*-
"""Tests that run INSIDE a real QGIS - never the stand-in.

Everything under tests/ runs against tests/qgis_stub.py, a simulated
PyQGIS. A stand-in is only safe where it is stricter than the real
thing; where it is kinder it certifies code that cannot run (BACKLOG
80, 288: "the simulator kinder than QGIS - FIVE times"). These tests
close that gap: they load the plugin into a real QGIS, run its tools
through Processing exactly as the toolbox does, and compare the
numbers with the engine's own.

HOW TO RUN (any machine with QGIS; CI does this on every push):
    QT_QPA_PLATFORM=offscreen  <QGIS's python> -m pytest tests_real_qgis

With conda-forge's QGIS, QGIS's Python modules are not on the path by
default; this file adds <prefix>/share/qgis/python when it finds it.
Run it with a plain Python and the whole folder is SKIPPED, saying so.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# conda-forge puts PyQGIS here, outside site-packages
for _p in (os.path.join(sys.prefix, "share", "qgis", "python"),
           os.path.join(sys.prefix, "Library", "python"),       # Windows
           os.path.join(sys.prefix, "share", "qgis", "python", "plugins"),
           os.path.join(sys.prefix, "Library", "python", "plugins")):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.append(_p)

for _p in (ROOT, os.path.join(ROOT, "qgis")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

qgis_core = pytest.importorskip(
    "qgis.core", reason="no real PyQGIS here - run these tests with "
    "QGIS's own Python (see tests_real_qgis/conftest.py)")

if not getattr(qgis_core, "__file__", None):
    # the stand-in is a module built in memory; real PyQGIS is a file
    raise RuntimeError("tests_real_qgis found the QGIS STAND-IN, not "
                       "QGIS. Run this folder on its own, not together "
                       "with tests/.")

from qgis.core import QgsApplication                    # noqa: E402

_APP = QgsApplication([], False)
_APP.initQgis()

from processing.core.Processing import Processing      # noqa: E402

Processing.initialize()

from equipop_qgis.provider import EquipopProvider      # noqa: E402

PROVIDER = EquipopProvider()
QgsApplication.processingRegistry().addProvider(PROVIDER)


def pytest_configure(config):
    # BACKLOG 84: a deprecated QGIS call works today and breaks in the
    # next QGIS, and no stand-in can see it ("a deprecated method exists
    # perfectly well"). Raised by the PLUGIN's own code, it fails here.
    # QGIS's own modules are left alone: their warnings are not ours.
    config.addinivalue_line("filterwarnings",
                            "error::DeprecationWarning:equipop_qgis")
    config.addinivalue_line("filterwarnings",
                            "error::DeprecationWarning:equipop")


def pytest_report_header(config):
    from qgis.core import Qgis
    import equipop
    return [f"QGIS {Qgis.version()} (real), Python {sys.version.split()[0]}",
            f"equipop {equipop.__version__} from {os.path.dirname(equipop.__file__)}"]


@pytest.fixture(scope="session")
def provider():
    return PROVIDER
