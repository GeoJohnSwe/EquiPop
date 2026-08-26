"""The QGIS continental door, EXECUTED rather than merely constructed.

WHY THIS FILE EXISTS. The door shipped with two faults that the suite
could not see, and John found both on his first run in QGIS 3.42:

  self.check_versions(ch)   -> AttributeError. It is a MODULE
      function in base.py, not a method. Written from a hurried
      reading; alg_counts.py had the right form four lines into its
      own processAlgorithm.
  tiles = "TEMPORARY_OUTPUT" -> an optional FolderDestination left
      alone does not arrive empty. QGIS fills it with that literal
      string, which taken at face value writes tiles into a folder of
      that name.

Both are wiring, not arithmetic, and the shared spine's fifteen tests
could not reach either, because they call run_folder directly. The
lesson is finding 28 again: prefer a test that RUNS the thing over one
that asserts about it. So this file calls processAlgorithm.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "qgis"))
pytest.importorskip("rasterio")

import qgis_stub                                    # noqa: E402

# install() is what puts the fake modules into sys.modules. Importing
# qgis_stub alone does nothing - Claude left the call out and all nine
# tests failed with ModuleNotFoundError, which is the right failure for
# the wrong reason.
qgis_stub.install()

FIX = ROOT / "tests" / "fixtures" / "worldpop"


def _alg():
    from equipop_qgis.alg_continental import ContinentalRasters
    a = ContinentalRasters()
    a.initAlgorithm()
    return a


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


def _params(**over):
    p = {"folder": str(FIX), "k": "500", "unit": 1000.0, "crs": None,
         "outcrs": None, "shape": 0,
         "weight": "", "sumcohorts": False, "pattern": "",
         "tiles": "TEMPORARY_OUTPUT", "OUTPUT": "memory:"}
    p.update(over)
    return p


def test_the_door_runs_end_to_end():
    """The whole point: it EXECUTES, not just constructs."""
    alg, fb = _alg(), _Feedback()
    out = alg.processAlgorithm(_params(), {}, fb)
    assert "OUTPUT" in out
    said = " ".join(fb.lines)
    assert "cells of 1000 m" in said, said[-400:]
    assert "ERROR" not in said, said


def test_check_versions_is_called_the_way_base_defines_it():
    """BUG 1. self.check_versions(ch) raised AttributeError in QGIS."""
    src = (ROOT / "qgis" / "equipop_qgis"
           / "alg_continental.py").read_text(encoding="utf-8")
    # CODE lines only - the comment above the call names the old form
    # on purpose, and a naive grep flagged its own explanation.
    code = [ln for ln in src.splitlines()
            if not ln.lstrip().startswith("#")]
    assert not [ln for ln in code if "self.check_versions" in ln], (
        "check_versions is a module function in base.py, not a method")
    assert "from .base import check_versions" in src


def test_an_untouched_tiles_box_means_in_memory():
    """BUG 2. QGIS fills an optional FolderDestination with the literal
    string TEMPORARY_OUTPUT, which must not become a folder name."""
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(tiles="TEMPORARY_OUTPUT"), {}, fb)
    said = " ".join(fb.lines)
    assert "TEMPORARY_OUTPUT" not in said
    assert "Tiled run finished" not in said, (
        "an untouched box must not trigger a tiled run")
    assert "origin rows" in said


def test_a_real_tiles_folder_does_tile(tmp_path):
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(tiles=str(tmp_path / "run")), {}, fb)
    said = " ".join(fb.lines)
    assert "Tiled run finished" in said, said[-400:]
    assert (tmp_path / "run" / "manifest.json").exists()


def test_the_pane_explains_what_dist_k_is():
    """The line that stops a varying radius being read as an error."""
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(), {}, fb)
    said = " ".join(fb.lines)
    assert "radius" in said.lower() and "density" in said.lower()


# ------------------------------------------------------- refusals
def test_a_k_that_is_not_a_number_is_refused_by_name():
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="not a number"):
        alg.processAlgorithm(_params(k="one thousand"), {}, fb)


def test_an_empty_k_box_gives_the_POINT_TABLE(tmp_path):
    """John: sixty populations, none of them "the" one.

    A blank k used to be refused. It now means "just give me the
    points" - the rasters as one point layer with every cohort a
    field, which needs no weight because nothing is being counted yet.
    """
    alg, fb = _alg(), _Feedback()
    out = alg.processAlgorithm(_params(k="  "), {}, fb)
    assert "OUTPUT" in out
    said = " ".join(fb.lines)
    assert "point table" in said, said[-300:]
    assert "Give a k" in said
    assert "ERROR" not in said


def test_the_points_path_never_asks_which_column_holds_the_people():
    """The refusal John hit cannot arise when nothing is counted."""
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(k=""), {}, fb)
    assert "which" not in " ".join(fb.lines).lower()


def test_a_folder_that_is_not_there_is_refused_in_plain_words():
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="Not a folder"):
        alg.processAlgorithm(_params(folder="/no/such/place"), {}, fb)


def test_several_k_values_are_accepted_either_way():
    for text in ("300 500", "300, 500"):
        alg, fb = _alg(), _Feedback()
        alg.processAlgorithm(_params(k=text), {}, fb)
        assert "ERROR" not in " ".join(fb.lines)


def test_the_country_reaches_the_output_layer_as_text():
    """BACKLOG 215. iso3 is a LABEL, and the writer used to cast every
    column to float - 'could not convert string to float: dnk'. The
    third place in this codebase to assume that anything which is not
    a coordinate is a measurement.
    """
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(k=""), {}, fb)
    assert "ERROR" not in " ".join(fb.lines)


def test_the_writer_decides_field_type_per_column():
    src = (ROOT / "qgis" / "equipop_qgis"
           / "alg_continental.py").read_text(encoding="utf-8")
    assert "is_numeric_dtype" in src, (
        "field types must follow the data, not the column position")
    assert "QMetaType.Type.QString" in src


def test_the_points_are_written_in_the_rasters_own_projection():
    """BACKLOG 227 - same reason as machine 4. A metric layer with a
    false northing of 10,000,000 m draws off the top of the world."""
    alg, fb = _alg(), _Feedback()
    params = _params(k="")
    alg.processAlgorithm(params, {}, fb)
    sink = params["_sinks"]["OUTPUT"]
    assert sink.crs.authid() == "EPSG:4326"


def test_the_points_can_be_written_LONG(tmp_path):
    """John: "it would be good to have the option of making the
    dataset wide or long". Wide is what the analysis runs on and what
    scales; long is the tidier shape to read."""
    alg, fb = _alg(), _Feedback()
    params = _params(k="", shape=1)
    alg.processAlgorithm(params, {}, fb)
    names = [f.name() for f in params["_sinks"]["OUTPUT"]._fields]
    assert "cohort" in names and "population" in names
    assert not any(n.startswith("f_") for n in names), (
        "long means the cohort is a VALUE, not a column")


def test_wide_is_still_the_default():
    alg, fb = _alg(), _Feedback()
    params = _params(k="")
    alg.processAlgorithm(params, {}, fb)
    names = [f.name() for f in params["_sinks"]["OUTPUT"]._fields]
    assert any(n.startswith("f_") for n in names)
    assert "cohort" not in names
