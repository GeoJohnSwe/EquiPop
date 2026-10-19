# -*- coding: utf-8 -*-
"""test_vital_machine4.py - machine 4 reads life expectancy, TFR, CBR
and CDR over k-neighbourhoods (v1.60.0, BACKLOG 416).

A FOLDER WITH A KNOWN ANSWER. Forty rasters shaped like WorldPop's
(ken_f_00_2020 ... ken_m_90_2020): the east half of the grid holds a
population with Kenya's 2020 life tables, the west half one whose death
rates from 60 are half again as high. Read with k as large as the whole
folder, every neighbourhood IS the nation, so the answers must be the
nation's own; read locally, the west must come out older-dying.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import test_vital as TV                              # noqa: E402
from equipop.doors import vital as V                 # noqa: E402
from equipop.doors.demography import (DemographyError,  # noqa: E402
                                      run_indices, vital_plan)

rasterio = pytest.importorskip("rasterio")
from rasterio.transform import from_origin           # noqa: E402

ALL = list(V.MEASURES)
NX, NY = 24, 12                     # pixels; west half x < NX/2
PX = 1 / 120                        # 30 arc-seconds, as WorldPop's 1 km


def _pyramids():
    """People per band in one pixel, women and men, east and west."""
    out = {}
    bands = V.national("KEN", 2020, "F")["bands"]
    i60 = bands.index(60)
    for sex, code, share in (("f", "F", TV.PF), ("m", "M", 1 - TV.PF)):
        m = V.national("KEN", 2020, code)["m"].copy()
        _l, L = TV.band_table(m, bands)
        m_w = m.copy()
        m_w[i60:] *= 1.5
        _lw, Lw = TV.band_table(m_w, bands)
        out[(sex, "east")] = 400 * share * TV.stable(L, 0.022, bands)
        out[(sex, "west")] = 400 * share * TV.stable(Lw, 0.022, bands)
    return bands, out


def make_folder(tmp_path, drop=(), sexes="fm"):
    bands, pyr = _pyramids()
    for sex in sexes:
        for j, b in enumerate(bands):
            name = f"ken_{sex}_{b:02d}_2020_CN_1km_R2025A_UA_v1"
            if name.split("_2020")[0][4:] in drop:
                continue
            a = np.empty((NY, NX), "float32")
            if sex == "t":
                east = pyr[("f", "east")][j] + pyr[("m", "east")][j]
                west = pyr[("f", "west")][j] + pyr[("m", "west")][j]
            else:
                east, west = pyr[(sex, "east")][j], pyr[(sex, "west")][j]
            a[:, : NX // 2] = west
            a[:, NX // 2:] = east
            with rasterio.open(
                    tmp_path / f"{name}.tif", "w", driver="GTiff",
                    height=NY, width=NX, count=1, dtype="float32",
                    crs="EPSG:4326", nodata=-99999.0,
                    transform=from_origin(36.0, -1.0, PX, PX)) as d:
                d.write(a, 1)
    return tmp_path


def total_people(folder):
    s = 0.0
    for p in folder.glob("*.tif"):
        with rasterio.open(p) as d:
            s += float(d.read(1).sum())
    return s


@pytest.fixture(scope="module")
def folder(tmp_path_factory):
    return make_folder(tmp_path_factory.mktemp("ken"))


def test_the_whole_folder_read_as_one_neighbourhood_is_the_nation(folder):
    """k = everybody: every neighbourhood is the nation, so e60 is the
    nation's (WPP's, from its own table), TFR is WPP's, and CDR is the
    nation's death rates over the folder's pyramid.

    BROKEN WITH: the reference read for another year than the
    folder's."""
    k = int(total_people(folder)) - 1
    man = run_indices(str(folder), [], vital=ALL, k_values=[k],
                      unit_size=1000.0, epsg=32737)
    r = man["results"]
    nat = V.national("KEN", 2020, "B")
    i60 = nat["bands"].index(60)
    e60 = nat["L"][i60:].sum() / nat["l"][i60]
    assert np.allclose(r[f"e60_{k}"], e60, atol=0.05)
    assert np.allclose(r[f"e0u_{k}"], nat["L"].sum(), atol=0.1)
    assert np.allclose(r[f"TFR_{k}"], nat["tfr"], rtol=0.003)
    assert man["vital"]["countries"] == ["KEN"]
    assert "World Population Prospects 2024" in man["vital"]["reference"]


def test_the_west_dies_younger_and_its_death_rate_shows_it(folder):
    """Death rates from 60 half again as high in the west half: its e60
    comes out lower and its CDR higher, while TFR, which the old do not
    touch, comes out the same on both sides.

    BROKEN WITH: the CDR given the nation's e60 instead of the
    neighbourhood's."""
    man = run_indices(str(folder), [], vital=ALL, k_values=[5000],
                      unit_size=1000.0, epsg=32737)
    r = man["results"]
    west = r["EastWest"] < r["EastWest"].median()
    e60w, e60e = r.loc[west, "e60_5000"].median(), \
        r.loc[~west, "e60_5000"].median()
    assert e60w < e60e - 2
    assert r.loc[west, "CDR_5000"].median() > \
        r.loc[~west, "CDR_5000"].median()
    assert r.loc[west, "TFR_5000"].median() == pytest.approx(
        r.loc[~west, "TFR_5000"].median(), rel=0.03)


def test_the_band_counts_do_not_reach_the_output(folder):
    """Forty-odd T_vb_/R_vb_ columns are machinery, not results.

    BROKEN WITH: apply_vital's drop of the machinery columns removed."""
    man = run_indices(str(folder), [], vital=["life_expectancy_60"],
                      k_values=[5000], unit_size=1000.0, epsg=32737)
    cols = list(man["results"].columns)
    assert "e60_5000" in cols
    assert not [c for c in cols if c.startswith(("T_v", "R_v", "vb_",
                                                 "vw_", "vc"))]


def test_a_pyramid_with_a_hole_is_refused_by_name(tmp_path):
    """No men aged 85-89: that band would read as everybody dead.

    BROKEN WITH: vital_plan's completeness check removed."""
    f = make_folder(tmp_path, drop=("m_85",))
    with pytest.raises(DemographyError, match="m_85"):
        run_indices(str(f), [], vital=["life_expectancy_60"],
                    k_values=[2000], unit_size=1000.0, epsg=32737)


def test_tfr_needs_the_women_and_says_so(tmp_path):
    """A t_-only folder can give life expectancy (both sexes) but not
    TFR, which needs to know how many of the people are women.

    BROKEN WITH: the women-files check removed (a KeyError instead)."""
    f = make_folder(tmp_path, sexes="t")
    labels = [p.stem.split("_CN")[0][4:] for p in f.glob("*.tif")]
    vp = vital_plan(labels, ["life_expectancy_60"])
    assert vp["sexes"] == ["t"]
    with pytest.raises(DemographyError, match="women's files"):
        vital_plan(labels, ["total_fertility_rate"])


def test_women_and_men_have_their_own_tables(folder):
    """sex='women' reads the women's pyramid against the women's life
    table: e60 for women is the higher.

    BROKEN WITH: the sex code ignored (always the both-sexes table)."""
    k = 5000
    w = run_indices(str(folder), [], vital=["life_expectancy_60"],
                    vital_sex="women", k_values=[k], unit_size=1000.0,
                    epsg=32737)["results"][f"e60_{k}"].median()
    m = run_indices(str(folder), [], vital=["life_expectancy_60"],
                    vital_sex="men", k_values=[k], unit_size=1000.0,
                    epsg=32737)["results"][f"e60_{k}"].median()
    assert w > m + 1


def test_the_unreliable_ones_say_so_in_the_log_and_the_fields(folder,
                                                               capsys):
    """John's ruling: computed, and FLAGGED, where it is read.

    BROKEN WITH: the UNRELIABLE prefix dropped from explain_fields."""
    run_indices(str(folder), [], vital=["life_expectancy_0",
                                        "life_expectancy_60"],
                k_values=[2000], unit_size=1000.0, epsg=32737)
    said = capsys.readouterr().out
    assert "e0u_2000: >>> UNRELIABLE - Life expectancy at birth" in said
    assert "e60_2000: >>> Life expectancy at 60" in said
    assert "below 5,000" in said                  # k = 2,000 is noisy


def test_indices_and_rates_in_one_traverse(folder):
    """The child-woman ratio and TFR side by side, one run.

    BROKEN WITH: the vital groups not added to compose (KeyError)."""
    man = run_indices(str(folder), ["child_woman_ratio"],
                      vital=["total_fertility_rate"], k_values=[3000],
                      unit_size=1000.0, epsg=32737)
    r = man["results"]
    assert {"cwr_3000", "TFR_3000"} <= set(r.columns)
    # the same children over the same women, read two ways
    assert np.corrcoef(r["cwr_3000"], r["TFR_3000"])[0, 1] > 0.9 or \
        r["TFR_3000"].std() < 1e-6


def test_a_tiled_run_gives_the_same_answers(folder, tmp_path):
    """BROKEN WITH: the tiled post-pass applying the indices only."""
    from equipop.bigrun import load_tiled
    mem = run_indices(str(folder), [], vital=ALL, k_values=[4000],
                      unit_size=1000.0, epsg=32737)["results"]
    out = str(tmp_path / "tiles")
    run_indices(str(folder), [], vital=ALL, k_values=[4000],
                unit_size=1000.0, epsg=32737, out_dir=out, tile_m=5000)
    tiled = load_tiled(out)
    for c in ("e60_4000", "TFR_4000", "CDR_4000", "e0u_4000"):
        a = mem.sort_values("CellId")[c].to_numpy()
        b = tiled.sort_values("CellId")[c].to_numpy()
        assert np.allclose(a, b, equal_nan=True), c


def test_each_cell_is_read_against_its_own_country(tmp_path):
    """Two countries side by side, each with the SAME pyramid in every
    pixel: every neighbourhood well inside a country is that country's
    pyramid, so its e60 must be that country's - Uganda's in the west,
    Kenya's in the east - not one country's for everybody.

    BROKEN WITH: CellCountries replaced by the first country for every
    cell."""
    bands, pyr = _pyramids()
    half = NX // 2
    for iso, x0 in (("uga", 35.0), ("ken", 35.0 + half * PX)):
        for sex in "fm":
            for j, b in enumerate(bands):
                a = np.full((NY, half), pyr[(sex, "east")][j], "float32")
                with rasterio.open(
                        tmp_path / f"{iso}_{sex}_{b:02d}_2020_CN_1km_"
                                   "R2025A_UA_v1.tif",
                        "w", driver="GTiff", height=NY, width=half,
                        count=1, dtype="float32", crs="EPSG:4326",
                        nodata=-99999.0,
                        transform=from_origin(x0, 0.5, PX, PX)) as d:
                    d.write(a, 1)
    man = run_indices(str(tmp_path), [], vital=["life_expectancy_60"],
                      k_values=[2000], unit_size=1000.0, epsg=32736)
    r = man["results"]
    assert man["vital"]["countries"] == ["KEN", "UGA"]

    def e60(iso):
        nat = V.national(iso, 2020, "B")
        i = nat["bands"].index(60)
        return nat["L"][i:].sum() / nat["l"][i]
    west = r["EastWest"] < r["EastWest"].median()
    assert abs(e60("UGA") - e60("KEN")) > 0.3
    assert r.loc[west, "e60_2000"].median() == pytest.approx(e60("UGA"),
                                                             abs=0.05)
    assert r.loc[~west, "e60_2000"].median() == pytest.approx(
        e60("KEN"), abs=0.05)
