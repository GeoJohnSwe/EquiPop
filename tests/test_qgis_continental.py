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

import numpy as np
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
         "outcrs": None, "shape": 0, "joinlayer": None,
         "joinfield": "", "joinname": "joined",
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


# ---------------------------------------------------------------------
# BACKLOG 238, John: "Machine 3 - Raster Data curation -> facilitate
# for the integration of shapefiles > i.e. points can have values that
# can populate raster grids > merges to the generated points."
#
# QGIS already counts points in cells and does it well. THE HARD PART
# IS THE LATTICE: EquiPop knows the exact grid the raster points sit
# on and QGIS does not, so a join done outside is approximate at cell
# boundaries. Here it is exact, because the grid is ours.
# ---------------------------------------------------------------------
def _shops(n=12, field=None):
    """A point layer sitting exactly on cells the rasters occupy."""
    import contextlib
    import io
    import pandas as pd
    from equipop.rasterfolder import load_folder
    from qgis_stub import _Source
    with contextlib.redirect_stdout(io.StringIO()):
        pts, _ = load_folder(str(FIX), keep_index=True)
    take = pts.sample(n, random_state=9)
    t = pd.DataFrame({"x": take["lon"].to_numpy(),
                      "y": take["lat"].to_numpy()})
    if field:
        t[field] = np.arange(1.0, n + 1.0)
    return _Source(t, crs="EPSG:4326"), take


def test_a_point_layer_becomes_a_column_on_the_raster_points():
    src, take = _shops()
    alg, fb = _alg(), _Feedback()
    params = _params(k="", joinlayer=src, joinfield="", joinname="shops")
    alg.processAlgorithm(params, {}, fb)
    names = [f.name() for f in params["_sinks"]["OUTPUT"]._fields]
    assert "shops" in names, names
    said = " ".join(fb.lines)
    assert "LATTICE INDEX" in said and "not by" in said


def test_the_join_is_exact_not_approximate():
    """Every shop must land on the cell it was taken from."""
    src, take = _shops(n=15)
    alg, fb = _alg(), _Feedback()
    params = _params(k="", joinlayer=src, joinfield="", joinname="shops")
    alg.processAlgorithm(params, {}, fb)
    feats = params["_sinks"]["OUTPUT"].features
    i = [f.name() for f in params["_sinks"]["OUTPUT"]._fields].index("shops")
    hit = sum(1 for f in feats if float(f.attributes()[i]) > 0)
    assert hit == len(take), f"{hit} cells hold a shop, expected {len(take)}"


def test_cells_the_layer_never_touched_carry_a_real_zero():
    src, take = _shops(n=6)
    alg, fb = _alg(), _Feedback()
    params = _params(k="", joinlayer=src, joinfield="", joinname="shops")
    alg.processAlgorithm(params, {}, fb)
    sink = params["_sinks"]["OUTPUT"]
    i = [f.name() for f in sink._fields].index("shops")
    vals = [float(f.attributes()[i]) for f in sink.features]
    assert min(vals) == 0.0 and sum(vals) == 6.0
    assert all(v is not None for v in vals), "0.0, not an absence"


def test_a_field_is_SUMMED_rather_than_counted():
    src, take = _shops(n=8, field="beds")
    alg, fb = _alg(), _Feedback()
    params = _params(k="", joinlayer=src, joinfield="beds",
                     joinname="beds")
    alg.processAlgorithm(params, {}, fb)
    sink = params["_sinks"]["OUTPUT"]
    i = [f.name() for f in sink._fields].index("beds")
    assert sum(float(f.attributes()[i]) for f in sink.features) == \
        pytest.approx(sum(range(1, 9)))


def test_no_layer_means_no_extra_column():
    alg, fb = _alg(), _Feedback()
    params = _params(k="")
    alg.processAlgorithm(params, {}, fb)
    names = [f.name() for f in params["_sinks"]["OUTPUT"]._fields]
    assert "joined" not in names


def test_joining_during_a_NEIGHBOURHOOD_run_is_refused_with_the_fix():
    """The join needs the point table, which a k-run does not produce."""
    from qgis.core import QgsProcessingException
    src, _ = _shops(n=4)
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="leave box"):
        alg.processAlgorithm(_params(k="500", joinlayer=src,
                                     joinfield="", joinname="s"), {}, fb)
