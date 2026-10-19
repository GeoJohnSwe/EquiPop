# -*- coding: utf-8 -*-
"""test_vital_own.py - each person read against their OWN country
(v1.61.0, the default).

John, 19 October: a neighbourhood that crosses a border should not be
read wholly against the country of its cell - "bring the destination
cell values from its country and weight the results accordingly".
Each point carries its own country's coefficients, so the
neighbourhood sums are the pooled estimators. Two properties pin it:
  - within ONE country it is exactly the 1.60 arithmetic ('cell');
  - people who look exactly like their own nation are read as their
    own nation, wherever the neighbourhood falls - a border
    neighbourhood lands BETWEEN the two nations, never outside them.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from equipop.doors import vital as V                     # noqa: E402
from equipop.doors.demography import (DemographyError,   # noqa: E402
                                      run_indices)

ALL = ["life_expectancy_60", "life_expectancy_50", "life_expectancy_30",
       "life_expectancy_0", "total_fertility_rate", "crude_birth_rate",
       "crude_death_rate"]
CODES = ["e60", "e50u", "e30u", "e0u", "TFR", "CBR", "CDR"]


def _run(table, rule, crs="EPSG:4326", k=3000, **kw):
    with redirect_stdout(io.StringIO()):
        return run_indices(None, [], vital=ALL, k_values=[k],
                           unit_size=1000.0, points=table, points_crs=crs,
                           vital_reference=rule, **kw)


# ------------------------------------------- one country: exactly 1.60
@pytest.fixture(scope="module")
def kenya(tmp_path_factory):
    pytest.importorskip("rasterio")
    import test_machine4_points as MP
    from equipop.doors.continental import run_folder
    d = tmp_path_factory.mktemp("kenya")
    with redirect_stdout(io.StringIO()):
        folder = MP.M4.make_folder(d)
        man = run_folder(str(folder), k_values=[])
    return (man["points_table"].rename(columns={"lon": "EastWest",
                                                "lat": "NorthSouth"}),
            man["crs"])


def test_within_one_country_own_is_exactly_the_cell_rule(kenya):
    """All seven measures, a real-shaped folder, every cell.

    BROKEN WITH: the life-table coefficient written P_b/P_a instead of
    P_a/P_b; with r = E_nat/C_nat; and with the CDR's mix weighted by
    the people of each band rather than by everybody 60+ (each moves
    some measure off the 1.60 value); and with the cell rule's sums
    left in its output."""
    table, crs = kenya
    a = _run(table, "cell", crs=crs, epsg=32737)["results"]
    b = _run(table, "own", crs=crs, epsg=32737)["results"]
    a = a.sort_values(["EastWest", "NorthSouth"]).reset_index(drop=True)
    b = b.sort_values(["EastWest", "NorthSouth"]).reset_index(drop=True)
    import re
    for frame in (a, b):         # neither rule leaves its sums behind
        assert not [c for c in frame.columns
                    if re.match(r"^([TR]_)?v(b|w|c|o)_?", c)], frame.columns
    for c in CODES:
        col = f"{c}_3000"
        assert np.isfinite(a[col]).sum() > 0.8 * len(a), col
        assert np.allclose(a[col], b[col], rtol=1e-9, atol=1e-9,
                           equal_nan=True), col


# ------------------------------------------------ two nations, a border
def _nation_like(iso, n_per_point=100.0):
    """A point whose pyramid IS its nation's stationary population
    (S_b proportional to L_b), half women: read against its own nation
    it must give that nation's own life table and rates."""
    nat = V.national(iso, 2020, "B")
    p = nat["L"] / nat["L"].sum() * n_per_point
    return nat, p


def _two_nations():
    lon = np.round(np.arange(35.0, 38.0, 0.01), 4)
    lat = np.round(np.arange(0.0, 0.4, 0.01), 4)
    X, Y = np.meshgrid(lon, lat)
    X, Y = X.ravel(), Y.ravel()
    iso = np.where(X < 36.5, "ken", "uga")
    df = pd.DataFrame({"EastWest": X, "NorthSouth": Y, "iso3": iso})
    nats = {}
    for c in ("ken", "uga"):
        nat, p = _nation_like(c)
        nats[c] = nat
        rows = iso == c
        for b, v in zip(V.BANDS, p):
            for sx in "fm":
                col = f"{sx}_{b:02d}_2020"
                if col not in df:
                    df[col] = 0.0
                df.loc[rows, col] = v / 2
    return df, nats


@pytest.fixture(scope="module")
def border():
    df, nats = _two_nations()
    return df, nats, _run(df, "own")["results"], _run(df, "cell")["results"]


def _national(nat):
    """The measures a nation-shaped neighbourhood must reproduce."""
    i = {a: V.BANDS.index(a) for a in (0, 30, 50, 60)}
    e = {a: nat["L"][i[a]:].sum() / nat["l"][i[a]] for a in i}
    return {"e60": e[60], "e50u": e[50], "e30u": e[30], "e0u": e[0],
            "TFR": nat["tfr"], "CDR": 1000 / e[0]}


def test_far_from_the_border_each_side_is_its_own_nation(border):
    """BROKEN WITH: every point given Kenya's coefficients."""
    df, nats, own, _cell = border
    for c, side in (("ken", own["EastWest"] < own["EastWest"].quantile(.2)),
                    ("uga", own["EastWest"] > own["EastWest"].quantile(.8))):
        want = _national(nats[c])
        for code, v in want.items():
            got = own.loc[side, f"{code}_3000"]
            assert np.allclose(got, v, rtol=1e-6), (c, code)


def test_across_the_border_own_lands_between_the_nations(border):
    """A neighbourhood holding people of both nations, each shaped like
    their own nation, reads as a blend of the two - never outside
    them. The cell rule reads the Ugandans there as Kenyans with an
    odd pyramid (or the reverse), and moves away from both.

    BROKEN WITH: the 'own' groups built but apply_vital (the cell
    arithmetic) used to read them; and with 'own' not passed through
    run_indices."""
    df, nats, own, cell = border
    nk, nu = _national(nats["ken"]), _national(nats["uga"])
    mid = own["EastWest"].between(own["EastWest"].quantile(.45),
                                  own["EastWest"].quantile(.55))
    moved = 0
    for code in ("e60", "e0u", "TFR", "CDR"):
        lo, hi = sorted((nk[code], nu[code]))
        got = own.loc[mid, f"{code}_3000"].dropna()
        assert len(got) and got.between(lo - 1e-6, hi + 1e-6).all(), code
        o = own.set_index(["EastWest", "NorthSouth"])[f"{code}_3000"]
        c = cell.set_index(["EastWest", "NorthSouth"])[f"{code}_3000"]
        moved += int((abs(o - c.reindex(o.index)) > 1e-3).sum())
    assert moved > 0, "the cell rule should differ at the border"


def test_the_rule_is_said_and_recorded(border):
    """BROKEN WITH: the reference rule left out of the record."""
    df, _n, _o, _c = border
    out = io.StringIO()
    with redirect_stdout(out):
        man = run_indices(None, [], vital=["total_fertility_rate"],
                          k_values=[3000], unit_size=1000.0, points=df,
                          points_crs="EPSG:4326")
    assert man["vital"]["rule"] == "own"
    assert "EACH PERSON'S OWN NATION" in out.getvalue()
    with pytest.raises(DemographyError, match="vital_reference"):
        run_indices(None, [], vital=["total_fertility_rate"],
                    k_values=[3000], points=df, points_crs="EPSG:4326",
                    vital_reference="nation")


# ---------------------------------------------------------- the doors
def test_qgis_reads_own_by_default_and_cell_when_asked(border):
    """BROKEN WITH: the QGIS door not passing vital_reference (the
    'cell' choice then gives 'own')."""
    sys.path.insert(0, str(ROOT / "qgis"))
    import qgis_stub
    qgis_stub.install()
    from equipop_qgis.alg_demography import SpatialDemography
    import test_vital_doors as VD
    df, _n, own, cell = border
    lyr = df.rename(columns={"EastWest": "x", "NorthSouth": "y"})

    def run(ix):
        alg = SpatialDemography()
        alg.initAlgorithm()
        p = {"folder": "", "indices": [], "rates": [0, 4], "ratesex": 0,
             "rateref": ix, "k": "3000", "unit": 1000.0, "year": "",
             "crs": None, "outcrs": None, "settings": [],
             "OUTPUT": "memory:",
             "points": qgis_stub._Source(lyr, crs="EPSG:4326",
                                         geometry=True)}
        alg.processAlgorithm(p, {}, VD._Feedback())
        return p["_sinks"]["OUTPUT"].to_frame()
    for ix, want in ((0, own), (1, cell)):
        got = run(ix)
        assert np.allclose(np.sort(got["TFR_3000"].dropna()),
                           np.sort(want["TFR_3000"].dropna())), ix


def test_pro_reads_cell_when_asked(border, tmp_path):
    """BROKEN WITH: Pro's door not passing vital_reference."""
    import test_arcgis_continental as AC
    df, _n, own, cell = border
    pyt, tool, state = AC._tool("SpatialDemography")
    lyr = df.rename(columns={"EastWest": "SHAPE@X",
                             "NorthSouth": "SHAPE@Y"})
    state.setdefault("layers", {})["two"] = lyr
    state.setdefault("crs_codes", {})["two"] = 4326
    out = str(tmp_path / "o.shp")
    tool.execute(AC._params(tool, points="two", indices="",
                            rates="Total fertility rate",
                            rateref="The country of the neighbourhood's "
                                    "cell", k="3000", unit=1000.0,
                            out=out), AC._Messages())
    got = state["written"][out]["table"]
    assert np.allclose(np.sort(got["TFR_3000"].dropna()),
                       np.sort(cell["TFR_3000"].dropna()))
    assert not np.allclose(np.sort(got["TFR_3000"].dropna()),
                           np.sort(own["TFR_3000"].dropna()))


# ------------------------------------------------- tiles, in both doors
def test_qgis_machine_4_tiled_gives_the_in_memory_answers(border, tmp_path):
    """John: "please add also an opportunity to split a run into tiles
    for Q and Pro". The same rates and index, read back from the tiles.

    BROKEN WITH: the QGIS door not passing out_dir (no tiles written;
    the folder is then empty and load_tiled refuses)."""
    sys.path.insert(0, str(ROOT / "qgis"))
    import qgis_stub
    qgis_stub.install()
    from equipop_qgis.alg_demography import SpatialDemography
    import test_vital_doors as VD
    df, _n, own, _cell = border
    lyr = df.rename(columns={"EastWest": "x", "NorthSouth": "y"})
    alg = SpatialDemography()
    alg.initAlgorithm()
    p = {"folder": "", "indices": [1], "rates": [0, 4, 6], "ratesex": 0,
         "rateref": 0, "k": "3000", "unit": 1000.0, "year": "",
         "crs": None, "outcrs": None, "settings": [], "OUTPUT": "memory:",
         "tiles": str(tmp_path / "tiles"),
         "points": qgis_stub._Source(lyr, crs="EPSG:4326", geometry=True)}
    alg.processAlgorithm(p, {}, VD._Feedback())
    got = p["_sinks"]["OUTPUT"].to_frame()
    assert any(f.endswith(".parquet") for f in
               __import__("os").listdir(tmp_path / "tiles"))
    for c in ("TFR_3000", "e60_3000", "CDR_3000"):
        assert np.allclose(np.sort(got[c].dropna()),
                           np.sort(own[c].dropna())), c


def test_pro_machine_4_tiled_gives_the_in_memory_answers(border, tmp_path):
    """BROKEN WITH: Pro's door reading man['results'] after a tiled run
    (there is none - KeyError)."""
    import os
    import test_arcgis_continental as AC
    df, _n, own, _cell = border
    pyt, tool, state = AC._tool("SpatialDemography")
    lyr = df.rename(columns={"EastWest": "SHAPE@X",
                             "NorthSouth": "SHAPE@Y"})
    state.setdefault("layers", {})["two"] = lyr
    state.setdefault("crs_codes", {})["two"] = 4326
    out = str(tmp_path / "o.shp")
    tiles = str(tmp_path / "tiles")
    tool.execute(AC._params(tool, points="two", indices="",
                            rates="Total fertility rate;Crude death rate",
                            k="3000", unit=1000.0, tiles=tiles, out=out),
                 AC._Messages())
    assert any(f.endswith(".parquet") for f in os.listdir(tiles))
    got = state["written"][out]["table"]
    for c in ("TFR_3000", "CDR_3000"):
        assert np.allclose(np.sort(got[c].dropna()),
                           np.sort(own[c].dropna())), c


# ------------------------------------------------------ the formulas
def test_the_formulas_travel_with_the_release_and_the_package():
    """John: "I wonder if we should provide the users with the formulas
    of the new models". One document, at the top of the release and
    inside the package, the same words in both.

    BROKEN WITH: the package copy edited alone; and with the document
    left out of package-data."""
    top = (ROOT / "METHODS_RATES.md").read_text(encoding="utf-8")
    inside = (ROOT / "equipop" / "METHODS_RATES.md").read_text(
        encoding="utf-8")
    assert top == inside
    for must in ("ρ_b  =  (S_b / S_a) / (P_b / P_a)",
                 "λ     =  (C / E) / (C_nat / E_nat)",
                 "θ solves", "Whose nation", "Andreev"):
        assert must in top, must
    toml = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    block = toml.split("[tool.setuptools.package-data]", 1)[1]
    assert '"METHODS_RATES.md"' in block.split("\n[", 1)[0]
    assert "\ninclude METHODS_RATES.md\n" in (
        ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert 'cp METHODS_RATES.md "$WORK/"' in (
        ROOT / "tools" / "make_bundle.sh").read_text(encoding="utf-8")
