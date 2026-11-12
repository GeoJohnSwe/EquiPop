# -*- coding: utf-8 -*-
"""BACKLOG 489: QGIS's shapefile check covers GROUPED type names.

Found by the independent review of 1.64.0 (11 November 2026). The
ten-character check ran before the run on the names it was expected
to make, built from the count fields in box 2a. Grouped names come
from box 2c and were not known yet, so a group called
some_long_group_name went to a .shp as T_some_long_group_name_2 - and
OGR cuts field names to ten characters on its own terms.

Two checks now: once the group names are known, before anything is
computed; and in write(), on the names the file will hold, before the
file is made.
"""
import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, "tests"), os.path.join(ROOT, "qgis")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import qgis_stub                                    # noqa: E402
qgis_stub.install()
from qgis.core import QgsProcessingException        # noqa: E402
from equipop_qgis.alg_counts import CountsAndShares  # noqa: E402
from test_qgis_door import _run                     # noqa: E402


def _src():
    return qgis_stub.source_from(pd.DataFrame({
        "x": [0.0, 1, 2, 3], "y": [0.0, 1, 2, 3],
        "fclass": ["school", "bar", "school", "shop"]}))


def _grouped(name, **kw):
    return dict(treatmode=[2], treatcatfield="fclass",
                treattable=["school", name], k="2", **kw)


@pytest.fixture
def no_engine(monkeypatch):
    """A refusal BEFORE the run: the engine must never be reached."""
    import equipop.stata_bridge as sb

    def boom(*a, **k):
        raise AssertionError("the engine ran before the refusal")
    monkeypatch.setattr(sb, "dispatch", boom)


def test_a_long_group_name_is_refused_before_the_run(no_engine):
    """BROKEN WITH: no check once the group names are known - the run
    passes and writes T_some_long_group_name_2 to the shapefile."""
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, _src(), outfc="/tmp/results.shp",
             **_grouped("some_long_group_name"))
    msg = str(e.value)
    assert "SHAPEFILE" in msg and "GeoPackage" in msg
    assert "T_some_lon" in msg or "R_some_lon" in msg


def test_a_long_name_for_every_other_type_is_refused_too(no_engine):
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, _src(), outfc="/tmp/results.shp",
             restgroup="everything_else", **_grouped("sc"))
    assert "everything_else" in str(e.value) or "SHAPEFILE" in str(e.value)


def test_short_group_names_still_go_to_a_shapefile():
    out, _ = _run(CountsAndShares, _src(), outfc="/tmp/results.shp",
                  **_grouped("sc"))
    assert {"T_sc_2", "R_sc_2"} <= set(out.columns)


def test_a_geopackage_takes_the_long_names():
    out, _ = _run(CountsAndShares, _src(), outfc="/tmp/results.gpkg",
                  **_grouped("some_long_group_name"))
    assert "T_some_long_group_name_2" in out.columns


def test_the_writer_checks_the_names_it_will_write(monkeypatch):
    """The net under both predictions: with the prediction blanked out,
    as a future name source might leave it, write() still refuses -
    and no file is made.
    BROKEN WITH: write() without refuse_long_names."""
    import equipop.doors.fields as fields
    monkeypatch.setattr(fields, "predict_result_fields",
                        lambda *a, **k: [])
    params = {}
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, _src(), outfc="/tmp/results.shp",
             _sinks=params, **_grouped("some_long_group_name"))
    assert "SHAPEFILE" in str(e.value)
    assert "outfc" not in params, "the file was made before the refusal"
