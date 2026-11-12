# -*- coding: utf-8 -*-
"""The QGIS plugin in a REAL QGIS: the stand-in audited, the tools run
through Processing, the numbers held to the engine's.

What these catch that tests/ cannot: a method or enum the stand-in
invented (stub_audit), a parameter QGIS reads differently from the
stand-in (a list where QGIS gives an int), the real OGR writer
(GeoPackage and shapefile), and anything QGIS 4 dropped. Each test
says which past failure it guards.
"""
import os
import runpy
import sys

import numpy as np
import pytest
from qgis.core import (Qgis, QgsFeature, QgsGeometry,
                       QgsProcessingException, QgsPointXY,
                       QgsVectorLayer)
import processing

from equipop import stata_bridge as sb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALG_COUNTS = "equipop:countsandshares"
ALG_STATS = "equipop:valuestatistics"


# ------------------------------------------------------------ data
def _points(n=240, seed=7):
    """A small town in SWEREF99 TM: pid, pop, grp (a count inside
    pop), income, a type field, and a group that holds nobody."""
    rng = np.random.RandomState(seed)
    x = 674000 + rng.uniform(0, 3000, n)
    y = 6580000 + rng.uniform(0, 3000, n)
    pop = rng.randint(0, 21, n).astype(float)
    grp = np.floor(pop * rng.uniform(0, 1, n))
    income = np.round(rng.lognormal(10, 0.5, n), 2)
    types = np.array(["school", "bar", "shop"])[rng.randint(0, 3, n)]
    lyr = QgsVectorLayer(
        "Point?crs=EPSG:3006&field=pid:integer&field=pop:double"
        "&field=grp:double&field=income:double&field=none_here:double"
        "&field=fclass:string(20)", "town", "memory")
    feats = []
    for i in range(n):
        f = QgsFeature(lyr.fields())
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x[i], y[i])))
        f.setAttributes([i, float(pop[i]), float(grp[i]),
                         float(income[i]), 0.0, str(types[i])])
        feats.append(f)
    assert lyr.dataProvider().addFeatures(feats)
    lyr.updateExtents()
    return lyr, dict(x=x, y=y, pop=pop, grp=grp, income=income,
                     types=types)


def _river():
    """A line barrier across the town, friction 6."""
    lyr = QgsVectorLayer("LineString?crs=EPSG:3006&field=cost:double",
                         "river", "memory")
    f = QgsFeature(lyr.fields())
    f.setGeometry(QgsGeometry.fromPolylineXY(
        [QgsPointXY(675500, 6579900), QgsPointXY(675500, 6583100)]))
    f.setAttributes([6.0])
    assert lyr.dataProvider().addFeatures([f])
    return lyr


def _read(path):
    """The written file, read back through OGR: {field: array by pid}."""
    lyr = QgsVectorLayer(str(path), "out", "ogr")
    assert lyr.isValid(), f"QGIS cannot open what it wrote: {path}"
    names = lyr.fields().names()
    rows = sorted((f.attributes() for f in lyr.getFeatures()),
                  key=lambda a: a[names.index("pid")])
    return {n: np.array([r[i] for r in rows], dtype=object)
            for i, n in enumerate(names)}


def _num(col):
    return np.array([np.nan if v is None else float(v) for v in col])


# Settings named explicitly on both sides, so a changed default fails
# here as a changed default and not as a mystery.
SETTINGS = dict(overshoot=1, selfpot=2, originrule=0)
ENGINE = dict(overshoot_mode="proportional", self_potential=1.0,
              self_rule="include", treat_are_counts=True)


# ------------------------------------------------------ the stand-in
def test_the_stand_in_promises_nothing_this_qgis_lacks():
    """BACKLOG 80, 472: tools/stub_audit.py, the check John used to
    paste into the QGIS console by hand, on every QGIS this runs on."""
    ns = runpy.run_path(os.path.join(ROOT, "tools", "stub_audit.py"),
                        run_name="stub_audit")
    assert ns["checked"] > 50
    assert not ns["gaps"], f"the stand-in invents: {sorted(set(ns['gaps']))}"


def test_the_plugin_says_it_runs_on_this_qgis():
    with open(os.path.join(ROOT, "qgis", "equipop_qgis", "metadata.txt"),
              encoding="utf-8") as fh:
        meta = fh.read()
    field = {k.strip(): v.strip() for k, v in
             (line.split("=", 1) for line in meta.splitlines()
              if "=" in line and not line.startswith("#"))}

    def num(text):
        parts = [int(p) for p in text.split(".")] + [0, 0]
        return parts[0] * 10000 + parts[1] * 100 + parts[2]

    here = Qgis.versionInt()
    assert num(field["qgisMinimumVersion"]) <= here
    assert here <= num(field["qgisMaximumVersion"]) + 99


def test_every_tool_is_registered(provider):
    ids = {a.id() for a in provider.algorithms()}
    assert {ALG_COUNTS, ALG_STATS} <= ids, ids


# --------------------------------------------------- counts, parity
def test_counts_match_the_engine(tmp_path):
    """The door adds nothing to the numbers: tool 1 through real
    Processing gives what dispatch() gives for the same question."""
    lyr, d = _points()
    out = tmp_path / "counts.gpkg"
    processing.run(ALG_COUNTS, dict(
        layer=lyr, refmode=1, pop="pop", treatmode=1, treat=["grp"],
        k="10 50", unit=100, outfc=str(out), **SETTINGS))
    got = _read(out)
    want = sb.dispatch("counts", d["x"], d["y"], unit_size=100.0,
                       weight=d["pop"], treat={"grp": d["grp"]},
                       k_values=[10, 50], **ENGINE)
    for col in ("N_10", "Dist_10", "T_grp_10", "R_grp_10",
                "N_50", "Dist_50", "T_grp_50", "R_grp_50"):
        assert col in got, f"{col} missing; wrote {sorted(got)}"
        np.testing.assert_allclose(_num(got[col]), want[col],
                                   rtol=1e-9, atol=1e-9, err_msg=col)


def test_a_shapefile_gets_the_same_numbers(tmp_path):
    """The real shapefile writer: short names survive and carry the
    same values as the GeoPackage."""
    lyr, _ = _points()
    gpkg, shp = tmp_path / "a.gpkg", tmp_path / "a.shp"
    for target in (gpkg, shp):
        processing.run(ALG_COUNTS, dict(
            layer=lyr, refmode=1, pop="pop", treatmode=1, treat=["grp"],
            k="10", unit=100, outfc=str(target), **SETTINGS))
    a, b = _read(gpkg), _read(shp)
    for col in ("N_10", "Dist_10", "T_grp_10", "R_grp_10"):
        assert col in b, f"{col} missing from the shapefile: {sorted(b)}"
        np.testing.assert_allclose(_num(b[col]), _num(a[col]),
                                   rtol=1e-9, err_msg=col)


def test_a_long_group_name_is_refused_for_a_shapefile(tmp_path):
    """BACKLOG 489 in a real QGIS: refused before anything is written."""
    lyr, _ = _points()
    shp = tmp_path / "long.shp"
    with pytest.raises(QgsProcessingException) as e:
        processing.run(ALG_COUNTS, dict(
            layer=lyr, refmode=1, pop="pop", treatmode=2,
            treatcatfield="fclass",
            treattable=["school", "some_long_group_name"],
            k="10", unit=100, outfc=str(shp), **SETTINGS))
    assert "GeoPackage" in str(e.value)
    assert not shp.exists()


def test_grouped_types_match_count_columns(tmp_path):
    """Grouped types (box 2c) are the same question as a count column
    per type (box 2a): one person per point, k = 20."""
    lyr, d = _points()
    out = tmp_path / "typed.gpkg"
    processing.run(ALG_COUNTS, dict(
        layer=lyr, refmode=0, treatmode=2, treatcatfield="fclass",
        treattable=["school", "edu"], k="20", unit=100,
        outfc=str(out), **SETTINGS))
    got = _read(out)
    want = sb.dispatch("counts", d["x"], d["y"], unit_size=100.0,
                       treat={"edu": (d["types"] == "school").astype(float)},
                       k_values=[20], **ENGINE)
    np.testing.assert_allclose(_num(got["T_edu_20"]), want["T_edu_20"],
                               rtol=1e-9, atol=1e-9)


def test_a_barrier_run_keeps_an_empty_groups_columns(tmp_path):
    """BACKLOG 488 in a real QGIS: a group asked for and holding nobody
    keeps T_ and R_ (zeros) on the effort engine."""
    lyr, _ = _points()
    out = tmp_path / "effort.gpkg"
    processing.run(ALG_COUNTS, dict(
        layer=lyr, refmode=1, pop="pop", treatmode=1,
        treat=["none_here"], k="20", unit=100, barrier=_river(),
        barrierfield="cost", outfc=str(out), **SETTINGS))
    got = _read(out)
    assert {"T_none_here_20", "R_none_here_20", "Rounds_20"} <= set(got)
    assert np.nansum(_num(got["T_none_here_20"])) == 0


# ---------------------------------------------------- stats, parity
def test_value_statistics_match_the_engine(tmp_path):
    lyr, d = _points()
    out = tmp_path / "stats.gpkg"
    processing.run(ALG_STATS, dict(
        layer=lyr, refmode=1, pop="pop", values=["income"],
        measures=[0, 1], k="25", unit=100, outfc=str(out), **SETTINGS))
    got = _read(out)
    want = sb.dispatch("stats", d["x"], d["y"], unit_size=100.0,
                       weight=d["pop"], values={"income": d["income"]},
                       stats={"income": ["mean", "median"]},
                       k_values=[25], overshoot_mode="proportional",
                       self_potential=1.0, self_rule="include")
    cols = [c for c in want if c.startswith(("Mean_income", "Median_income",
                                              "Med_income"))]
    assert cols, sorted(want)
    for col in cols:
        assert col in got, f"{col} missing; wrote {sorted(got)}"
        np.testing.assert_allclose(_num(got[col]), want[col],
                                   rtol=1e-9, atol=1e-9, err_msg=col)
