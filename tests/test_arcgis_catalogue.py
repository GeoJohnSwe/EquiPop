# -*- coding: utf-8 -*-
"""test_arcgis_catalogue.py - tools 5a, 5b and 5c in ArcGIS Pro, EXECUTED.

BACKLOG 414, v1.59.0. The QGIS door has run since 1.58.0, and John
confirmed it live on 16 October; this is the same engine behind Pro's
own door. The .pyt runs VERBATIM under the simulated arcpy of
tests/test_arcgis_stub.py, against the web as John's probes found it
(tests/fakeweb.py). The path that matters is the user's: 5a writes a
table, rows are SELECTED in Pro, 5c fetches exactly those.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "qgis"))

import qgis_stub                                     # noqa: E402
qgis_stub.install()                  # the QGIS door's lists are compared

import fakeweb                                       # noqa: E402
import test_arcgis_stub as H                         # noqa: E402
from equipop.doors import catalogue as cat          # noqa: E402
from equipop.doors import help as HLP               # noqa: E402


@pytest.fixture
def pro(monkeypatch):
    state = H._install_fake_arcpy(pd.DataFrame({"OBJECTID": [1],
                                                "SHAPE@X": [0.0],
                                                "SHAPE@Y": [0.0]}))
    web = fakeweb.captured(bodies=True)
    monkeypatch.setattr(cat.Net, "_urlopen", lambda self, req: web(req))
    monkeypatch.setattr(cat, "DEFAULT_PAUSE", 0)
    monkeypatch.setattr(cat, "DEFAULT_WAITS", (0,))
    return types.SimpleNamespace(pyt=H._load_pyt(), state=state, web=web,
                                 arcpy=sys.modules["arcpy"])


def run(pro, cls, **values):
    tool = getattr(pro.pyt, cls)()
    params = tool.getParameterInfo()
    for p in params:
        if p.name in values:
            p.value = values[p.name]
    msgs = H._Messages()
    tool.execute(params, msgs)
    return msgs


def table(pro, key):
    return pro.state["created"][key]


# ======================================================== the shapes
def test_the_columns_are_the_packages_and_the_qgis_doors(pro):
    """Three copies of one list - package, QGIS, Pro - so pinned.

    BROKEN WITH: 'age_to' declared TEXT in the Pro list."""
    from equipop_qgis import alg_catalogue as Q
    kinds = {"str": "TEXT", "int": "LONG", "float": "DOUBLE"}
    assert pro.pyt.CATALOGUE_COLUMNS == [(n, kinds[k])
                                         for n, k in cat.COLUMNS]
    assert [n for n, _ in Q.COLUMNS] == [n for n, _ in
                                         pro.pyt.CATALOGUE_COLUMNS]


def test_the_choices_are_the_same_in_both_doors(pro):
    """BROKEN WITH: Pro's 'Total population only' label left at the old
    wording ('Population - all people, ...')."""
    from equipop_qgis import alg_catalogue as Q
    assert pro.pyt.WP_THEMES == Q.WP_THEMES == list(cat.WP_THEMES)
    assert pro.pyt.WP_THEME_LABELS == Q.WP_THEME_LABELS
    assert pro.pyt.WP_RESOLUTIONS == Q.WP_RESOLUTIONS
    assert pro.pyt.WP_RESOLUTION_LABELS == Q.WP_RESOLUTION_LABELS
    assert pro.pyt.OSM_THEMES == Q.OSM_THEMES == list(cat.GF_THEMES)


@pytest.mark.parametrize("cls", ["WorldPopCatalogue", "OsmCatalogue",
                                 "FetchSelected"])
def test_each_tool_is_named_and_explained_as_in_qgis(pro, cls):
    """The label, the summary and every box's help: one text, two
    doors.

    BROKEN WITH: Pro's 5c label written 'Fetch selected rows'."""
    from equipop_qgis import alg_catalogue as Q
    tool = getattr(pro.pyt, cls)()
    assert tool.label == HLP.LABELS[cls] == getattr(Q, cls).EQP_LABEL
    assert tool.description == HLP.summary_for(cls)
    names = [p.name for p in tool.getParameterInfo()]
    assert not HLP.missing_help(names), HLP.missing_help(names)


# ======================================================= 5a, 5b, 5c
GDB = "/data/work.gdb"


def test_5a_writes_a_table_with_real_nulls(pro):
    """The open top band (90+) has no upper age, and must reach Pro as
    NULL - the inventory's writer would have written 0, so '90 to 0'.

    BROKEN WITH: _write_catalogue replaced by the inventory's
    _write_table (NumPyArrayToTable, 0 for an empty integer)."""
    msgs = run(pro, "WorldPopCatalogue", wp_places="Burundi, Kenya",
               wp_years="2020", CATALOGUE=f"{GDB}/wp")
    t = table(pro, f"{GDB}/wp")
    assert len(t) == 80 and list(t.columns) == list(cat.COLUMN_NAMES)
    top = t[t["age_from"] == 90]
    assert len(top) == 4 and top["age_to"].isna().all()
    assert set(t[t["age_from"] == 1]["age_to"]) == {4}
    assert any("Select By Attributes" in m for m in msgs.log)
    assert [m for m, u, r in pro.web.log if m == "GET" and ".tif" in u] == []


def test_a_long_citation_fits_its_field(pro):
    """Text fields are sized to what they hold: WorldPop's citations run
    to hundreds of characters, and a fixed 255 would refuse them.

    BROKEN WITH: every TEXT field given field_length=255."""
    run(pro, "WorldPopCatalogue", wp_places="Sweden", wp_years="2020",
        CATALOGUE=f"{GDB}/wp")
    t = table(pro, f"{GDB}/wp")
    assert t["citation"].str.len().max() > 255


def test_5a_refuses_a_dbase_table(pro):
    """BROKEN WITH: the geodatabase check removed - a folder target then
    becomes a .dbf that cuts 'source_page' to ten characters."""
    with pytest.raises(pro.arcpy.ExecuteError, match="dBASE"):
        run(pro, "WorldPopCatalogue", wp_places="Sweden", wp_years="2020",
            CATALOGUE="/data/folder/wp")


def test_5a_can_write_a_csv(pro, tmp_path):
    """BROKEN WITH: the .csv branch removed (CreateTable then gets a
    .csv name)."""
    out = str(tmp_path / "wp.csv")
    run(pro, "WorldPopCatalogue", wp_places="Sweden", wp_years="2020",
        CATALOGUE=out)
    assert len(cat.read_csv(out)) == 40


def test_5a_reads_its_dropdowns_by_label(pro):
    """BROKEN WITH: _pick always returning the first key."""
    run(pro, "WorldPopCatalogue",
        wp_theme=pro.pyt.WP_THEME_LABELS[1], wp_places="Sweden",
        wp_years="2020", CATALOGUE=f"{GDB}/pop")
    t = table(pro, f"{GDB}/pop")
    assert list(t["layer"]) == ["pop"]


def test_5b_takes_its_layers_from_the_checklist(pro):
    """Pro hands a multi-value box over as 'a;b' text.

    BROKEN WITH: _multi reading the box as one value."""
    run(pro, "OsmCatalogue", osm_places="Sweden",
        osm_layers="roads;'pois'", CATALOGUE=f"{GDB}/osm")
    t = table(pro, f"{GDB}/osm")
    assert list(t["layer"]) == ["roads", "pois", "pois_a"]


def test_select_then_fetch_takes_exactly_the_selection(pro, tmp_path):
    """The user's whole path in Pro: 5a's table, rows selected (Select
    By Attributes "sex" = 'f' AND "age_from" = 15), 5c - and only those
    files.

    BROKEN WITH: the simulator's cursor made to ignore the selection -
    which is what reading the table's catalog path instead of its view
    would do in Pro. The test leans on that contract, so it must fail
    without it."""
    run(pro, "WorldPopCatalogue", wp_places="Burundi, Kenya",
        wp_years="2020", CATALOGUE=f"{GDB}/wp")
    t = table(pro, f"{GDB}/wp")
    pick = t.index[(t["sex"] == "f") & (t["age_from"] == 15)]
    pro.state.setdefault("selections", {})[f"{GDB}/wp"] = set(pick)
    folder = str(tmp_path / "f")
    os.makedirs(folder)
    msgs = run(pro, "FetchSelected", rows=f"{GDB}/wp", FOLDER=folder)
    tifs = sorted(n for n in os.listdir(folder) if n.endswith(".tif"))
    assert tifs == ["bdi_f_15_2020_CN_1km_R2025A_UA_v1.tif",
                    "ken_f_15_2020_CN_1km_R2025A_UA_v1.tif"]
    assert any("2 row(s) selected" in m for m in msgs.log)
    assert any("tool 6" in m for m in msgs.log)


def test_no_selection_takes_everything_and_says_so(pro, tmp_path):
    """BROKEN WITH: the FIDSet message removed."""
    run(pro, "WorldPopCatalogue", wp_theme=pro.pyt.WP_THEME_LABELS[1],
        wp_places="Burundi", wp_years="2020", CATALOGUE=f"{GDB}/pop")
    folder = str(tmp_path / "f")
    os.makedirs(folder)
    msgs = run(pro, "FetchSelected", rows=f"{GDB}/pop", FOLDER=folder)
    assert any("NO ROWS ARE SELECTED, so all 1" in m for m in msgs.log)


def test_5c_stops_above_the_limit_before_downloading(pro, tmp_path):
    """BROKEN WITH: max_mb not passed on to fetch_rows."""
    run(pro, "WorldPopCatalogue", wp_places="Burundi", wp_years="2020",
        CATALOGUE=f"{GDB}/wp")
    before = len(pro.web.log)
    with pytest.raises(pro.arcpy.ExecuteError, match="above the limit"):
        run(pro, "FetchSelected", rows=f"{GDB}/wp", max_mb=0.001,
            FOLDER=str(tmp_path))
    assert len(pro.web.log) == before


def test_5c_refuses_a_table_that_is_not_a_catalogue(pro, tmp_path):
    """BROKEN WITH: the column check removed."""
    with pytest.raises(pro.arcpy.ExecuteError, match="not a catalogue"):
        run(pro, "FetchSelected", rows="people", FOLDER=str(tmp_path))


def test_5c_stops_when_pro_cancels(pro, tmp_path):
    """Cancel in Pro sets arcpy.env.isCancelled; 5c looks between files,
    and what arrived is recorded.

    BROKEN WITH: say() not reading isCancelled."""
    run(pro, "WorldPopCatalogue", wp_places="Burundi", wp_years="2020",
        CATALOGUE=f"{GDB}/wp")
    seen = {"n": 0}

    class Env:
        @property
        def isCancelled(self):
            seen["n"] += 1
            return seen["n"] > 5
    pro.arcpy.env = Env()
    folder = str(tmp_path / "f")
    os.makedirs(folder)
    with pytest.raises(pro.arcpy.ExecuteError, match="Cancelled"):
        run(pro, "FetchSelected", rows=f"{GDB}/wp", max_mb=0,
            FOLDER=folder)
    man = json.load(open(os.path.join(folder, "equipop_fetch.json")))
    assert man["fetches"][-1]["status"] == "incomplete"
    assert 0 < len(man["files"]) < 40


def test_an_old_package_is_told_to_upgrade(pro, monkeypatch):
    """`_doors()` passes on any package since 1.18; the catalogue is
    1.58. An older package must hear 'upgrade', not ImportError.

    BROKEN WITH: _catalogue_modules importing without the try."""
    import builtins
    real = builtins.__import__

    def no_catalogue(name, *a, **kw):
        if name == "equipop.doors" and a and a[2] and \
                "catalogue" in a[2]:
            raise ImportError("cannot import name 'catalogue'")
        return real(name, *a, **kw)
    monkeypatch.setattr(builtins, "__import__", no_catalogue)
    with pytest.raises(pro.arcpy.ExecuteError, match="1.58.0 or later"):
        run(pro, "WorldPopCatalogue", wp_places="Sweden",
            CATALOGUE=f"{GDB}/wp")
