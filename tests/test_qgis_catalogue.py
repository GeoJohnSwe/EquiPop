# -*- coding: utf-8 -*-
"""test_qgis_catalogue.py - tools 5a, 5b and 5c, EXECUTED.

BACKLOG 414, v1.58.0. Every QGIS door in this project has shipped with
a wiring fault that construction could not see, so these call
processAlgorithm through the simulator, against the web as John's
probes found it (tests/fakeweb.py). The round trip that matters is the
user's: 5a makes a table, rows are SELECTED, and 5c fetches exactly
those.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "qgis"))

import qgis_stub                                     # noqa: E402
qgis_stub.install()

import fakeweb                                       # noqa: E402
from equipop.doors import catalogue as cat          # noqa: E402
from equipop.doors import help as HLP               # noqa: E402
from equipop.doors import fetchrows as fr           # noqa: E402
from equipop_qgis import alg_catalogue as A         # noqa: E402
from qgis.core import (QgsProcessingException,      # noqa: E402
                       QgsProcessingFeedback)


@pytest.fixture
def web(monkeypatch):
    w = fakeweb.captured(bodies=True)
    monkeypatch.setattr(cat.Net, "_urlopen", lambda self, req: w(req))
    monkeypatch.setattr(cat, "DEFAULT_PAUSE", 0)
    return w


def run(alg, **params):
    alg.initAlgorithm()
    p = {"CATALOGUE": "TEMPORARY_OUTPUT"}
    p.update(params)
    fb = QgsProcessingFeedback()
    out = alg.processAlgorithm(p, None, fb)
    sink = p.get("_sinks", {}).get("CATALOGUE")
    if sink is not None:
        # A TABLE, not a layer of points: 5c reads it as one, and a
        # geometry column would put 80 rows at (0, 0) on the map.
        assert int(sink.wkb) == int(qgis_stub.QgsWkbTypes.NoGeometry)
    return out, (sink.to_frame() if sink else None), fb


def _said(fb):
    return " ".join(fb.info + fb.warnings)


# ===================================================== what is written
def test_the_columns_are_the_packages_columns():
    """Written down in the door (it must load without the package), so
    pinned here against catalogue.COLUMNS.

    BROKEN WITH: 'size_mb' declared as int in the door."""
    assert A.COLUMNS == list(cat.COLUMNS)


def test_the_option_lists_are_the_packages():
    """BROKEN WITH: 'worship' left out of the door's OSM list."""
    assert A.WP_THEMES == list(cat.WP_THEMES)
    assert A.OSM_THEMES == list(cat.GF_THEMES)
    assert len(A.OSM_THEME_LABELS) == len(A.OSM_THEMES)
    assert len(A.WP_THEME_LABELS) == len(A.WP_THEMES)
    assert A.WP_RESOLUTIONS == ["1km", "100m"]


@pytest.mark.parametrize("cls", [A.WorldPopCatalogue, A.OsmCatalogue,
                                 A.FetchSelected])
def test_every_box_is_explained_in_the_shared_text(cls):
    """BROKEN WITH: the HELP entry for 'wp_exact' removed."""
    alg = cls()
    alg.initAlgorithm()
    names = [p.name() for p in alg.parameterDefinitions()]
    assert not HLP.missing_help(names), HLP.missing_help(names)
    assert len(HLP.summary_for(cls.EQP_TOOL).split()) >= 20
    assert len(HLP.usage_for(cls.EQP_TOOL).split()) >= 20
    assert cls().displayName() == cls.EQP_LABEL


def test_the_toolbox_orders_look_select_fetch():
    """QGIS sorts a group's tools by name: 5a, 5b, 5c, then the old
    settings tool as 5d - so the new way is the one met first.

    BROKEN WITH: the old tool keeping its '5. Fetch data' label, which
    sorts before '5a'."""
    from equipop_qgis.alg_fetch import SpatialDataFetch
    labels = sorted([A.WorldPopCatalogue().displayName(),
                     A.OsmCatalogue().displayName(),
                     A.FetchSelected().displayName(),
                     SpatialDataFetch().displayName()])
    assert [l[:2] for l in labels] == ["5a", "5b", "5c", "5d"]


# ============================================================ 5a and 5b
def test_5a_lists_without_downloading(web):
    """BROKEN WITH: the sink built with a Point geometry type; and,
    separately, the closing NEXT line removed."""
    out, df, fb = run(A.WorldPopCatalogue(), wp_theme=0,
                      wp_places="Sweden, Kenya", wp_years="2020",
                      wp_resolution=0)
    assert len(df) == 80 and list(df.columns)[:3] == ["provider", "theme",
                                                      "series"]
    assert set(df["sex"]) == {"f", "m"}
    assert [m for m, u, r in web.log if m == "GET" and ".tif" in u] == []
    assert "NOTHING HAS BEEN DOWNLOADED" in _said(fb)
    assert "Selected features only" in _said(fb)


def test_5a_refuses_in_the_users_words(web):
    """BROKEN WITH: FetchError left to escape as itself (QGIS then
    shows a traceback instead of the message)."""
    with pytest.raises(QgsProcessingException, match="Swedn"):
        run(A.WorldPopCatalogue(), wp_theme=0, wp_places="Swedn",
            wp_years="2020", wp_resolution=0)
    with pytest.raises(QgsProcessingException, match="Box 1b"):
        run(A.WorldPopCatalogue(), wp_theme=0, wp_places="  ",
            wp_resolution=0)


def test_5b_lists_the_ticked_layers(web):
    """BROKEN WITH: the enum indices passed through unmapped."""
    out, df, fb = run(A.OsmCatalogue(), osm_places="Sweden",
                      osm_layers=[0, 1, 3], osm_years="", osm_latest=True)
    assert list(df["layer"]) == ["buildings_a", "roads", "pois", "pois_a"]
    assert "SHARE-ALIKE" in _said(fb)


def test_5b_with_years(web):
    """BROKEN WITH: osm_latest read from the wrong box."""
    _, df, _ = run(A.OsmCatalogue(), osm_places="bayern", osm_layers=[1],
                   osm_years="2020, 2022", osm_latest=False)
    assert list(df["date"]) == ["2020-01-01", "2022-01-01"]


# ===================================================== the round trip
def _selected(df, keep):
    """What QGIS hands 5c with 'Selected features only' ticked: a
    no-geometry source holding just the selected rows."""
    return qgis_stub._Source(df[keep].reset_index(drop=True),
                             geometry=False)


def test_select_then_fetch_takes_exactly_the_selection(web, tmp_path):
    """The user's whole path: 5a's table, rows selected by expression
    ("sex" = 'f' AND "age_from" = 15), 5c - and only those files.

    BROKEN WITH: 5c reading the attribute VALUES in field order of the
    catalogue rather than the source's own field order."""
    _, df, _ = run(A.WorldPopCatalogue(), wp_theme=0,
                   wp_places="Burundi, Kenya", wp_years="2020",
                   wp_resolution=0)
    keep = (df["sex"] == "f") & (df["age_from"] == 15)
    src = _selected(df[list(reversed(df.columns))], keep)
    folder = str(tmp_path / "f")
    alg = A.FetchSelected()
    alg.initAlgorithm()
    fb = QgsProcessingFeedback()
    out = alg.processAlgorithm({"rows": src, "FOLDER": folder,
                                "max_mb": 5000, "keep_pbf": True}, None, fb)
    assert out == {"FOLDER": folder}
    tifs = sorted(n for n in os.listdir(folder) if n.endswith(".tif"))
    assert tifs == ["bdi_f_15_2020_CN_1km_R2025A_UA_v1.tif",
                    "ken_f_15_2020_CN_1km_R2025A_UA_v1.tif"]
    assert "equipop_recipe.csv" in os.listdir(folder)


def test_the_recipe_loaded_as_a_layer_fetches_again(web, tmp_path):
    """A recipe CSV loaded in QGIS gives NULLs and numbers as QGIS
    reads them; it must fetch the same files.

    BROKEN WITH: coerce_row not treating 'NULL' as empty - age_to then
    arrives as the text 'NULL'."""
    _, df, _ = run(A.OsmCatalogue(), osm_places="Sweden", osm_layers=[1],
                   osm_years="", osm_latest=True)
    a = str(tmp_path / "a")
    alg = A.FetchSelected()
    alg.initAlgorithm()
    alg.processAlgorithm({"rows": _selected(df, df["layer"] == "roads"),
                          "FOLDER": a, "max_mb": 0}, None,
                         QgsProcessingFeedback())
    recipe = pd.read_csv(os.path.join(a, "equipop_recipe.csv"))
    recipe = recipe.astype(object).where(recipe.notna(), qgis_stub.NULL)
    b = str(tmp_path / "b")
    alg.processAlgorithm({"rows": _selected(recipe, recipe["layer"] ==
                                            "roads"),
                          "FOLDER": b, "max_mb": 0}, None,
                         QgsProcessingFeedback())
    assert sorted(os.listdir(a)) == sorted(os.listdir(b))


def test_5c_refuses_a_table_that_is_not_a_catalogue(web, tmp_path):
    """BROKEN WITH: the column check removed (the refusal then comes
    from deep inside, about row 1)."""
    src = qgis_stub._Source(pd.DataFrame({"name": ["a"], "x": [1.0],
                                          "y": [2.0]}), geometry=False)
    alg = A.FetchSelected()
    alg.initAlgorithm()
    with pytest.raises(QgsProcessingException, match="not a catalogue"):
        alg.processAlgorithm({"rows": src, "FOLDER": str(tmp_path)},
                             None, QgsProcessingFeedback())


def test_5c_with_nothing_selected_says_how(web, tmp_path):
    """BROKEN WITH: fetch_rows' empty-selection check removed."""
    _, df, _ = run(A.OsmCatalogue(), osm_places="Sweden", osm_layers=[1],
                   osm_years="", osm_latest=True)
    alg = A.FetchSelected()
    alg.initAlgorithm()
    with pytest.raises(QgsProcessingException, match="Select rows"):
        alg.processAlgorithm({"rows": _selected(df, df["layer"] == "x"),
                              "FOLDER": str(tmp_path / "f")}, None,
                             QgsProcessingFeedback())


def test_5c_stops_when_cancelled_and_keeps_the_record(web, tmp_path):
    """Cancel between files: what arrived is recorded, the job marked
    incomplete, and the message says a rerun continues.

    BROKEN WITH: say() not checking isCanceled."""
    _, df, _ = run(A.WorldPopCatalogue(), wp_theme=0, wp_places="Burundi",
                   wp_years="2020", wp_resolution=0)
    fb = QgsProcessingFeedback()
    calls = {"n": 0}
    real = fb.isCanceled

    def cancel_after_two():
        calls["n"] += 1
        return calls["n"] > 4 or real()
    fb.isCanceled = cancel_after_two
    alg = A.FetchSelected()
    alg.initAlgorithm()
    folder = str(tmp_path / "f")
    with pytest.raises(QgsProcessingException, match="Cancelled"):
        alg.processAlgorithm({"rows": _selected(df, df["sex"] == "f"),
                              "FOLDER": folder, "max_mb": 0}, None, fb)
    import json
    man = json.load(open(os.path.join(folder, "equipop_fetch.json")))
    assert man["fetches"][-1]["status"] == "incomplete"
    assert 0 < len(man["files"]) < 20


def test_the_plugin_lists_the_new_tools():
    """BROKEN WITH: the three tools left out of the provider."""
    from equipop_qgis.provider import EquipopProvider
    prov = EquipopProvider()
    prov.loadAlgorithms()
    names = {a.name() for a in prov.algorithms()}
    assert {"worldpopcatalogue", "osmcatalogue", "fetchselected",
            "spatialdatafetch"} <= names


def test_5c_refuses_qgis_temporary_folder(web, tmp_path, monkeypatch):
    """QGIS's folder box defaults to a processing_* folder in the
    system's temporary space, deleted when QGIS closes.

    BROKEN WITH: the _qgis_temporary check removed."""
    import tempfile
    _, df, _ = run(A.OsmCatalogue(), osm_places="Sweden", osm_layers=[1],
                   osm_years="", osm_latest=True)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    alg = A.FetchSelected()
    alg.initAlgorithm()
    before = len(web.log)
    for bad in (str(tmp_path / "processing_aBcD" / "FOLDER"), ""):
        with pytest.raises(QgsProcessingException,
                           match="TEMPORARY|Choose a folder"):
            alg.processAlgorithm({"rows": _selected(df, df["layer"] ==
                                                    "roads"),
                                  "FOLDER": bad}, None,
                                 QgsProcessingFeedback())
    assert len(web.log) == before
