"""MACHINE 4's QGIS door, EXECUTED rather than constructed.

Machine 3's door shipped three wiring faults that 682 passing tests
could not see, because nothing ever called processAlgorithm. This
file calls it from the first commit.

It already earned that: initAlgorithm() imported the package to build
its tick-box list, which meant the whole PLUGIN died at startup when
equipop was absent - turning "install equipop" from a sentence into a
traceback. The other three tools survive that; this one did not.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "qgis"))
rasterio = pytest.importorskip("rasterio")
from rasterio.transform import from_origin           # noqa: E402

import qgis_stub                                     # noqa: E402
qgis_stub.install()

from equipop.doors.demography import BAND_STARTS, INDICES  # noqa: E402


def _alg():
    from equipop_qgis.alg_demography import SpatialDemography
    a = SpatialDemography()
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


@pytest.fixture(scope="module")
def folder():
    """Two countries, a real-shaped pyramid, fractional counts."""
    px = 1.0 / 1200
    d = tempfile.mkdtemp()
    rng = np.random.default_rng(11)
    shape = (50, 50)
    for iso, off in (("bdi", 0.0), ("rwa", 0.05)):
        for sex in ("f", "m"):
            for age in BAND_STARTS:
                a = (rng.random(shape)
                     * max(0.2, 3.0 - age / 30.0)).astype("float32")
                with rasterio.open(
                        os.path.join(d, f"{iso}_{sex}_{age:02d}_2026"
                                        "_CN_1km_R2025A_UA_v1.tif"),
                        "w", driver="GTiff", height=shape[0],
                        width=shape[1], count=1, dtype="float32",
                        crs="EPSG:4326", nodata=-99999.0,
                        transform=from_origin(30.0 + off,
                                              -2.0 + shape[0] * px,
                                              px, px)) as o:
                    o.write(a, 1)
    return d


def _params(folder, **over):
    p = {"folder": folder, "indices": [1], "k": "500", "unit": 1000.0,
         "year": "", "crs": None, "outcrs": None, "settings": [],
         "OUTPUT": "memory:"}
    p.update(over)
    return p


# ------------------------------------------------- the startup fault
def test_the_dialog_does_not_read_the_package():
    """initAlgorithm runs while QGIS builds the dialog. A plugin must
    still LOAD when equipop is absent."""
    src = (ROOT / "qgis" / "equipop_qgis"
           / "alg_demography.py").read_text(encoding="utf-8")
    head = src.split("def processAlgorithm")[0]
    code = [ln for ln in head.splitlines()
            if not ln.lstrip().startswith("#")]
    assert not [ln for ln in code if "from equipop" in ln], (
        "nothing above processAlgorithm may import the package")


def test_the_hard_coded_list_matches_the_package():
    """The price of not importing it is that the list can drift.

    So pin it here, where both are available.
    """
    from equipop_qgis.alg_demography import INDEX_LABELS, INDEX_NAMES
    assert INDEX_NAMES == sorted(INDICES), (
        "the tick-box list has drifted from the package's indices")
    assert INDEX_LABELS == [INDICES[n]["label"] for n in INDEX_NAMES]


# ------------------------------------------------------- running it
def test_the_door_runs_one_index(folder):
    alg, fb = _alg(), _Feedback()
    out = alg.processAlgorithm(_params(folder), {}, fb)
    assert "OUTPUT" in out
    said = " ".join(fb.lines)
    assert "on top" in said and "divided by" in said
    assert "ERROR" not in said, said[-400:]


def test_several_indices_cost_one_pass(folder):
    """John's preference. The saving is real at continental scale: the
    load, the projection and the tree are the cost, and they are
    identical whichever index is wanted."""
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(folder, indices=[0, 1, 2, 3]), {}, fb)
    said = " ".join(fb.lines)
    assert "4 indices" in said
    # ONE TRAVERSE: the cell table is built once, not four times.
    # Count the loader's own line, not the spine's echo of it - the
    # first version of this counted a phrase that appears in both and
    # failed on a run that was perfectly correct.
    assert said.count("[cells]") == 1, (
        "the cells were built more than once")
    assert said.count("fast pass") == 1, "the tree was built more than once"


def test_the_suggested_columns_are_shown_before_computing(folder):
    """John: "suggested fields loaded, but with option to add/remove"."""
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(folder, indices=[1]), {}, fb)
    said = " ".join(fb.lines)
    assert "f_15_2026" in said, "the user must see the actual columns"


def test_each_index_can_be_altered_SEPARATELY_in_one_run(folder):
    """John: "it also means I cannot run different demographic
    indicators at the same time, since restricting to women in fertile
    ages will not fly in the other measures".

    Quite right, and it defeated the point of the tool - four indices
    in one traverse was the reason to build it. A per-index TABLE lets
    them differ. His own suggestion.
    """
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(
        folder, indices=[0, 1],
        settings=["Child-woman ratio", "", "f:15-44",
                  "Ageing index", "70-", ""]), {}, fb)
    said = " ".join(fb.lines)
    assert "ERROR" not in said, said[-400:]
    # Read THE PLANS, not the whole log - the field guide printed at
    # the end names every column and so contains f_45 whatever the
    # measures were. An earlier version of this test searched the lot
    # and failed on a run that was entirely correct.
    plans = [ln for ln in fb.lines
             if ln.startswith("   on top") or ln.startswith("   divided by")]
    assert len(plans) == 4, plans
    cwr_den = [ln for ln in plans if "divided by" in ln][-1]
    assert "f_40_2026" in cwr_den and "f_45_2026" not in cwr_den, cwr_den
    age_num = [ln for ln in plans if "on top" in ln][0]
    assert "f_70_2026" in age_num and "f_65_2026" not in age_num, age_num
    assert "2 indices" in said


def test_an_untouched_index_keeps_its_own_measure(folder):
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(
        folder, indices=[0, 1],
        settings=["Ageing index", "70-", ""]), {}, fb)
    said = " ".join(fb.lines)
    # child-woman ratio was not named in the table, so 15-49 stands
    assert "f_45_2026" in said


def test_an_empty_table_changes_nothing(folder):
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(folder, settings=["", "", ""]), {}, fb)
    assert "ERROR" not in " ".join(fb.lines)


def test_a_row_naming_an_unticked_index_is_refused(folder):
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="not ticked"):
        alg.processAlgorithm(_params(
            folder, indices=[1],
            settings=["Ageing index", "70-", ""]), {}, fb)


def test_a_row_naming_no_such_index_lists_the_real_ones(folder):
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="do not have"):
        alg.processAlgorithm(_params(
            folder, settings=["Total fertility rate", "15-49", ""]),
            {}, fb)


def test_a_malformed_age_range_is_refused_naming_the_index(folder):
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException,
                       match="Child-woman ratio.*not an age range"):
        alg.processAlgorithm(_params(
            folder, indices=[1],
            settings=["Child-woman ratio", "", "15 to 44"]), {}, fb)


def test_a_ragged_table_is_refused_by_name(folder):
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="whole number of rows"):
        alg.processAlgorithm(_params(
            folder, settings=["Child-woman ratio", "0-4"]), {}, fb)


def test_no_index_ticked_is_refused(folder):
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="at least one"):
        alg.processAlgorithm(_params(folder, indices=[]), {}, fb)


def test_a_k_that_is_not_a_number_is_refused_by_name(folder):
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="not a number"):
        alg.processAlgorithm(_params(folder, k="a thousand"), {}, fb)


def test_a_degree_projection_is_refused(folder):
    from qgis.core import QgsProcessingException
    from qgis.core import QgsCoordinateReferenceSystem
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="degrees"):
        alg.processAlgorithm(
            _params(folder, crs=QgsCoordinateReferenceSystem("EPSG:4326")),
            {}, fb)


def test_a_folder_that_is_not_there_is_refused_in_plain_words(folder):
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="Not a folder"):
        alg.processAlgorithm(_params("/no/such/place"), {}, fb)


def test_the_sink_is_given_a_WKB_TYPE_not_a_number():
    """BACKLOG 221. John's run computed 46,071 origins and two indices
    in 10.8 s, then died on the last line before writing the layer:

        TypeError: parameterAsSink(): argument 5 has unexpected
        type 'int'

    Two numberings live in QgsWkbTypes - GEOMETRY types (Point=0) and
    WKB types (Point=1) - and both doors passed a literal 2, which is
    POLYGON in the one that matters. PyQGIS refuses a bare int anyway.

    THE ROOT CAUSE WAS THE SIMULATOR, not the doors: it accepted
    anything, so twelve tests passed against a call QGIS rejects. It
    now refuses an int exactly as PyQGIS does, and this test guards
    the source as well, because a future door could reintroduce it.
    """
    for door in ("alg_continental.py", "alg_demography.py"):
        src = (ROOT / "qgis" / "equipop_qgis" / door).read_text(
            encoding="utf-8")
        call = src.split("parameterAsSink")[1][:200]
        assert "QgsWkbTypes.Point" in call, (
            f"{door} passes something other than a WKB type to the sink")


def test_the_simulator_refuses_an_int_as_pyqgis_does():
    """If this stops raising, the simulator has gone permissive again
    and the doors are no longer being checked at all."""
    from qgis.core import QgsWkbTypes
    alg = _alg()
    with pytest.raises(TypeError, match="unexpected type 'int'"):
        alg.parameterAsSink({}, "OUTPUT", {}, [], 2, None)
    # and the real constant is accepted
    alg.parameterAsSink({}, "OUTPUT", {}, [], QgsWkbTypes.Point, None)


def test_the_layer_is_written_in_the_RASTERS_own_projection(folder):
    """John: "the raster has an in-data projection, perhaps we should
    depict in the same format? it ought to be easy to place correctly".

    The analysis runs in metres and must. The OUTPUT need not - and
    the metric one is a trap, because UTM southern zones carry a FALSE
    NORTHING of 10,000,000 m. Burundi comes out at northing ~9,779,000,
    which on a European basemap reads as the far north. That is why
    John's layer drew west of Norway EVEN WITH the project set to the
    layer's own EPSG:32735.
    """
    alg, fb = _alg(), _Feedback()
    params = _params(folder)
    alg.processAlgorithm(params, {}, fb)
    sink = params["_sinks"]["OUTPUT"]
    assert sink.crs.authid() == "EPSG:4326", (
        "the rasters were geographic; the layer should be too")


def test_the_geometry_lands_where_the_rasters_were(folder):
    """The whole point: no reprojection step for the user."""
    alg, fb = _alg(), _Feedback()
    params = _params(folder)
    alg.processAlgorithm(params, {}, fb)
    pt = params["_sinks"]["OUTPUT"].features[0].geometry().asPoint()
    assert 29.0 < pt.x() < 31.0, f"longitude {pt.x()}"
    assert -3.0 < pt.y() < -1.0, f"latitude {pt.y()}"


def test_the_metric_projection_can_still_be_asked_for(folder):
    from qgis.core import QgsCoordinateReferenceSystem
    alg, fb = _alg(), _Feedback()
    params = _params(folder,
                     outcrs=QgsCoordinateReferenceSystem("EPSG:32736"))
    alg.processAlgorithm(params, {}, fb)
    sink = params["_sinks"]["OUTPUT"]
    assert sink.crs.authid() == "EPSG:32736"
    pt = sink.features[0].geometry().asPoint()
    assert abs(pt.x()) > 1000, "metres, not degrees"


def test_the_run_explains_every_field_it_wrote(folder):
    """John: "I have no explanation to what the field names are
    representing"."""
    alg, fb = _alg(), _Feedback()
    params = _params(folder)
    alg.processAlgorithm(params, {}, fb)
    said = "\n".join(fb.lines)
    assert "WHAT THE FIELDS MEAN" in said
    for must in ("N_500", "Dist_500", "SumN", "MaxDistance",
                 "T_cwr_num_500", "cwr_500"):
        assert must in said, f"{must} was written but never explained"
    # and the one that matters most is marked as the answer
    assert ">>>" in said, "the index itself should stand out"


def test_the_projection_is_stated_in_words_not_just_stamped(folder):
    """A layer in the wrong place is a CRS misunderstanding, so say it."""
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(folder), {}, fb)
    said = "\n".join(fb.lines)
    assert "THE LAYER IS IN EPSG:" in said
    assert "Layer Properties" in said, (
        "tell the user where to check when it draws in the wrong place")
