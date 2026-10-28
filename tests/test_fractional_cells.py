# -*- coding: utf-8 -*-
"""Fractional cell sizes, through every engine and door (v1.63.0,
BACKLOG 445).

From 1.29.8 to 1.62.1 every door refused a fractional cell size (155):
six modules rounded it differently, so 2.5 gave centres 1, 3, 6. 1.62.1
made the centres exact; 1.63.0 found and removed what still rounded -
the effort engines' grid took int(unit_size) and int(lowest coordinate)
(446), the slope engine matched its DEM on recomputed float midpoints,
the fast engines rounded output coordinates to two decimals (a 0.1 m
grid's 0.35000000000000003 came back as 0.35 and could not be mapped
to its rows) - and John lifted the refusal.

THE PROOF IS SCALE. The same town measured in 2.5 m cells and in 100 m
cells is the same town: every count, share and effort must agree, and
every distance must scale by 2.5/100. Points are placed inside their
cells, not on the edges, so no rounding boundary is involved, and the
town straddles 0 in both directions.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import contextlib
import io
import os
import sys

import numpy as np
import pandas as pd
import pytest

from equipop import overshoot
from equipop.stata_bridge import dispatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))

SIZES = [2.5, 0.1, 0.3]
REF = 100.0
ENGINES = ["counts", "stats", "friction", "slope"]
MODES = [overshoot.WHOLE, overshoot.PROPORTIONAL, overshoot.SAMPLED]

_rng = np.random.default_rng(5)
_N = 300
I_, J_ = _rng.integers(-6, 6, _N), _rng.integers(-6, 6, _N)
FX, FY = _rng.uniform(.2, .8, _N), _rng.uniform(.2, .8, _N)
G = (_rng.random(_N) < .35) * 1.0
V = _rng.normal(10, 3, _N)


def _quiet(f, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return f(*a, **k)


def _run(engine, u, mode, tmp_path):
    x, y = (I_ + FX) * u, (J_ + FY) * u
    kw = dict(unit_size=u, k_values=[5, 40], overshoot_mode=mode, seed=7)
    if engine == "stats":
        kw.update(values={"v": V}, stats={"v": ["mean"]})
    else:
        kw.update(treat={"g": G})
    if engine == "slope":
        # a hill whose GRADIENT is the same at every scale: its height
        # scales with the cells, from a DEM twice as fine as the grid
        px = u / 2
        x_min, y_max = -8 * u, 8 * u
        n = 32
        cx = x_min + px * (np.arange(n) + .5)
        cy = y_max - px * (np.arange(n) + .5)
        hill = 40 * (u / REF) * np.exp(
            -((cx[None, :] / u) ** 2 + (cy[:, None] / u) ** 2) / 16)
        kw["dem"] = {"array": hill, "x_min": x_min, "y_max": y_max,
                     "cell_w": px, "cell_h": px, "nodata": None}
    if engine == "friction":
        c = np.arange(-7, 7)
        E, N = np.meshgrid((c + .5) * u, (c + .5) * u)
        p = tmp_path / f"fr_{u}.csv"
        pd.DataFrame({"x": E.ravel(), "y": N.ravel(),
                      "friction": ((np.abs(E) < 1.5 * u) * 2.0).ravel()}
                     ).to_csv(p, index=False)
        kw["friction_file"] = str(p)
    return _quiet(dispatch, engine, x, y, **kw)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("engine", ENGINES)
def test_a_town_in_fractional_cells_is_the_same_town(engine, mode,
                                                     tmp_path):
    """Every engine, every overshoot mode, three fractional sizes.

    BROKEN WITH, each on its own: fastcounts' output coordinates
    rounded to 2 decimals again (counts: the 0.1 m rows find no cell);
    FrictionGrid on int(unit_size) (friction and slope); SlopeGrid's
    midpoints on int(unit_size) (slope); the DEM matched on float
    midpoints (slope at 0.1 and 0.3); the effort ring gathered by exact
    equality (slope: last-bit differences between scales split ties).
    """
    ref = _run(engine, REF, mode, tmp_path)
    for u in SIZES:
        got = _run(engine, u, mode, tmp_path)
        assert set(got) == set(ref), u
        for c in ref:
            a = np.asarray(ref[c], float)
            b = np.asarray(got[c], float)
            if c.startswith("Dist"):
                b = b * REF / u
            assert np.isfinite(b).sum() == np.isfinite(a).sum(), (u, c)
            assert np.allclose(a, b, rtol=1e-9, atol=1e-9,
                               equal_nan=True), (u, c)


@pytest.mark.parametrize("mode", MODES)
def test_the_fast_engines_per_origin_path_too(mode, tmp_path, monkeypatch):
    """The fast engine has two paths that must agree bit for bit
    (tests/test_batched_engine.py); dispatch takes the batched one, so
    the per-origin path is checked here on its own.

    BROKEN WITH: the per-origin path's output coordinates rounded to 2
    decimals again (the 0.1 m rows find no cell)."""
    import equipop.fastcounts as FC
    monkeypatch.setattr(FC, "BATCHED", False)
    ref = _run("counts", REF, mode, tmp_path)
    for u in (0.1, 2.5):
        got = _run("counts", u, mode, tmp_path)
        for c in ref:
            a = np.asarray(ref[c], float)
            b = np.asarray(got[c], float)
            if c.startswith("Dist"):
                b = b * REF / u
            assert np.allclose(a, b, rtol=1e-9, atol=1e-9,
                               equal_nan=True), (u, c)


def test_the_ring_engine_at_a_fractional_size():
    """run_knn, fed by snap_to_grid and aggregate_to_cells - the route
    the QGIS and Pro statistics tools take.

    BROKEN WITH: analysis.run_knn's output coordinates rounded to 2
    decimals again (two 0.1 m cells either side of a rounding step come
    back as one key)."""
    from equipop.analysis import run_knn
    from equipop.transform import aggregate_to_cells, snap_to_grid
    out = {}
    for u in (REF, 2.5, 0.1):
        t = pd.DataFrame({"x": (I_ + FX) * u, "y": (J_ + FY) * u,
                          "FullPop": 1.0, "Treatment": G})
        s = snap_to_grid(t, unit_size=u, easting_col="x", northing_col="y")
        cells = aggregate_to_cells(s, ["FullPop", "Treatment"])
        r = _quiet(run_knn, cells, [5, 40], unit_size=u, id_col=None,
                   max_radius_units=60)
        r = r.assign(_i=np.floor(r.EastWest / u).astype(int),
                     _j=np.floor(r.NorthSouth / u).astype(int))
        out[u] = r.sort_values(["_i", "_j"]).reset_index(drop=True)
    ref = out[REF]
    for u in (2.5, 0.1):
        got = out[u]
        assert len(got) == len(ref)
        assert (got._i == ref._i).all() and (got._j == ref._j).all()
        assert len(set(zip(got.EastWest, got.NorthSouth))) == len(got)
        for c in ref.columns:
            if c in ("Id", "EastWest", "NorthSouth", "_i", "_j") or \
                    not pd.api.types.is_numeric_dtype(ref[c]):
                continue
            b = got[c].to_numpy(float)
            if "Dist" in c:                 # Dist_k, MaxDistance
                b = b * REF / u
            assert np.allclose(ref[c].to_numpy(float), b, rtol=1e-9,
                               atol=1e-9, equal_nan=True), (u, c)


@pytest.mark.parametrize("u", [0.1, 2.5, 0.3, 1e-3])
def test_the_cells_are_evenly_spaced(u):
    """What 155 was about: a 2.5 m grid's centres came out 1, 3, 6.

    BROKEN WITH: build_cells' midpoints cast to int (the 1.61 code)."""
    from equipop.cells import build_cells
    k = np.arange(-40, 40)
    df = pd.DataFrame({"e": (k + .37) * u, "n": 0.0})
    cd = _quiet(build_cells, df, "e", "n", unit_size=u)
    e = np.sort(np.asarray(cd.E, float))
    assert len(e) == len(k)
    assert np.allclose(np.diff(e), u, rtol=1e-9)
    assert np.allclose(e, (k + .5) * u, rtol=1e-9, atol=1e-12 * u)


@pytest.mark.parametrize("u", [2.5, 0.3, 3.0])
def test_effort_potential_and_fca_scale(u):
    """The two other users of the effort grid, across 0.

    BROKEN WITH: access or fca finding their nodes by int(unit_size)
    and the old corner arithmetic (BACKLOG 446)."""
    from equipop.access import effort_potential
    from equipop.decay import Decay
    from equipop.fca import fca

    def town(s):
        i = np.arange(-3, 3)
        pop = pd.DataFrame({"x": np.repeat(i, 6) * s + s / 2,
                            "y": np.tile(i, 6) * s + s / 2,
                            "count_all": 1.0 + np.arange(36) % 4})
        mass = pd.DataFrame({"x": [-2.5 * s, 2.5 * s],
                             "y": [-2.5 * s, 1.5 * s],
                             "mass": [2.0, 3.0]})
        return pop, mass

    dec = Decay(model="negexp", half_life_m=2.0)    # ROUNDS
    res = {}
    for s in (REF, u):
        pop, mass = town(s)
        n_dom = 36
        a = _quiet(effort_potential, pop, mass, dec,
                   altitude=np.zeros(n_dom), model="tobler",
                   roundtrip=True, unit_size=s)
        demand = pop.rename(columns={"count_all": "w"})
        supply = mass.rename(columns={"mass": "jobs"})
        d, _ = _quiet(fca, demand, supply, "w", "jobs", decay=dec,
                      reach="effort", altitude=np.zeros(n_dom),
                      model="tobler", roundtrip=True, unit_size=s)
        res[s] = (a.A.to_numpy(float), d.A.to_numpy(float))
    assert np.allclose(res[REF][0], res[u][0], rtol=1e-12)
    assert np.allclose(res[REF][1], res[u][1], rtol=1e-12)
    assert (res[u][0] > 0).all()


def test_fca_and_lisa_through_the_bridge(tmp_path):
    """The bridge's other two engines map their answers back by the
    snapped midpoint, which at 0.1 m is 0.35000000000000003 and the
    like - so the map-back is tested at that size.

    BROKEN WITH: LISA's output coordinates rounded to 2 decimals, as
    the fast engines' were until 1.63.0 (the 0.1 m rows then find no
    cell to read)."""
    D = (np.arange(_N) % 4 + 1).astype(float)
    res = {}
    for u in (REF, 0.1):
        x, y = (I_ + FX) * u, (J_ + FY) * u
        p = tmp_path / f"sup_{u}.csv"
        pd.DataFrame({"sx": np.array([-3.3, 2.2, 0.4]) * u,
                      "sy": np.array([1.1, -2.7, 4.6]) * u,
                      "jobs": [5., 7., 3.]}).to_csv(p, index=False)
        f = _quiet(dispatch, "fca", x, y, unit_size=u, demand_arr=D,
                   supply_file=str(p), supply_x="sx", supply_y="sy",
                   supply_col="jobs", half_life_m=3 * u)
        lisa = _quiet(dispatch, "lisa", x, y, unit_size=u,
                      values={"v": V}, seed=3)
        res[u] = {**f, **lisa}
    for c, a in res[REF].items():
        b = np.asarray(res[0.1][c], float)
        assert np.isfinite(b).all(), c
        assert np.allclose(np.asarray(a, float), b, rtol=1e-6), c


# ---------------------------------------------------------- the doors
def test_stata_equipop_runs_a_fractional_size():
    """`equipop ..., unit(3.125)` on the test data shrunk 32 times is
    `unit(100)` on the test data - the ado no longer refuses it, and
    the Python it calls takes it as given. (32 and 3.125 are exact in
    binary, so no point changes cell by the shrinking itself.)

    BROKEN WITH: `unit = float(round(unit))` in the bridge (the cells
    become 3 m wide and every count moves)."""
    import stata_sim as SS
    df = SS.load_test_data()

    def run(d, unit):
        ns, st = SS.start(d.assign(__touse=1.0))
        SS.run_block(SS.blocks(os.path.join(ROOT, "stata",
                                            "equipop.ado"))[0], ns)
        _quiet(ns["_equipop_machine1"], x="X_local", y="Y_local",
               treat="HighEdu", k="50 200", r="", unit=unit, weight="",
               selfpot=1.0, touse="__touse", prefix="", project="",
               epsg=0, treatmode="", missing="", decay="", halflife=0.0,
               halflifevar="", bins=10, overshoot="", originrule="",
               calibration="", unit_was_set=1)
        return st.df

    big = run(df, 100.0)
    small = run(df.assign(X_local=df.X_local / 32, Y_local=df.Y_local / 32),
                3.125)
    for c in ("N_50", "N_200", "R_HighEdu_50", "R_HighEdu_200"):
        assert np.allclose(big[c], small[c], equal_nan=True), c
    assert np.allclose(big.Dist_200, small.Dist_200 * 32, rtol=1e-9,
                       equal_nan=True)
    ado = open(os.path.join(ROOT, "stata", "equipop.ado"),
               encoding="utf-8").read()
    assert "unit() must be a whole number" not in ado


def test_pro_runs_a_fractional_size(tmp_path):
    """The Pro toolbox's counts tool at 2.5: it runs, and it gives what
    the package gives at 2.5.

    BROKEN WITH: the 1.62.1 whole-number check back in EquiPop.pyt."""
    import test_arcgis_stub as PRO
    t = pd.DataFrame({"OBJECTID": np.arange(1, _N + 1),
                      "SHAPE@X": (I_ + FX) * 2.5, "SHAPE@Y": (J_ + FY) * 2.5,
                      "HighEdu": G})
    state = PRO._install_fake_arcpy(t)
    pyt = PRO._load_pyt()
    msg = PRO._Messages()
    pyt._run_tool("counts", "people", msg, treat_fields=["HighEdu"],
                  k_text="25", unit=2.5)
    got = state["table"]
    ref = dispatch("counts", t["SHAPE@X"].to_numpy(),
                   t["SHAPE@Y"].to_numpy(), k_values=[25], unit_size=2.5,
                   treat={"HighEdu": G})
    assert np.allclose(got["R_HighEdu_25"].to_numpy(float),
                       ref["R_HighEdu_25"], equal_nan=True)
    assert np.allclose(got["Dist_25"].to_numpy(float), ref["Dist_25"],
                       equal_nan=True)


@pytest.mark.parametrize("ado", ["equipop.ado", "equipop_run.ado"])
def test_an_older_engine_refuses_a_fractional_unit_in_words(ado,
                                                           monkeypatch):
    """eqp_min_engine stays at 1.48.0 - a whole size loses nothing on an
    older engine - so the ado itself refuses a FRACTIONAL unit() when
    the engine predates 1.63.0, where it would stop at a rounded
    coordinate or run the effort engines at the rounded size. A whole
    unit() still runs on that engine.

    BROKEN WITH: the version check in _engine_takes_unit removed (the
    fractional run goes ahead on an engine that says it is 1.62.1)."""
    import equipop
    import stata_sim as SS
    df = SS.load_test_data().head(400)
    monkeypatch.setattr(equipop, "__version__", "1.62.1")

    def call(unit):
        ns, st = SS.start(df.assign(__touse=1.0))
        SS.run_block(SS.blocks(os.path.join(ROOT, "stata", ado))[0], ns)
        try:
            if ado == "equipop.ado":
                _quiet(ns["_equipop_machine1"], x="X_local", y="Y_local",
                       treat="HighEdu", k="50", r="", unit=unit,
                       weight="", selfpot=1.0, touse="__touse",
                       prefix="", project="", epsg=0, treatmode="",
                       missing="", decay="", halflife=0.0,
                       halflifevar="", bins=10, overshoot="",
                       originrule="", calibration="", unit_was_set=1)
            else:
                _quiet(ns["_equipop_run"], "counts", "X_local", "Y_local",
                       "HighEdu", "", "", "50", "", "", unit, "", "",
                       "tobler", 0, "", "", "", "supply", "x", "y", 0.0,
                       "decay", "2sfca", 0.0, 0.0, 0, 1.0, 199)
        except SS.StataError as e:
            return st, e.args[0]
        return st, None

    st, rc = call(2.5)
    assert rc == 198
    assert any("1.63.0 or newer" in e and "1.62.1" in e for e in st.err)
    assert "N_50" not in st.df.columns
    st, rc = call(100.0)
    assert rc is None and "N_50" in st.df.columns
