# -*- coding: utf-8 -*-
"""External review of 1.60.1 - fixed in 1.60.2.

Three P1 findings (the children under five, a projection with no EPSG
code, the point layer's values), two P2 (the older download path's
redirects, guessing degrees) and three P3 (fields left out unnamed,
the WPP table unchecked at load, no third-party notice). Each was
reproduced before any code moved. John decided two things on 18
October: a blank in a point layer counts as nobody ("zero is our way -
also because what is missing in some column will be needed when
compared later"), and a folder far short of its country's WPP total is
warned about.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from equipop.doors import vital as V                   # noqa: E402
from equipop.doors.demography import (DemographyError,  # noqa: E402
                                      vital_plan)

TFR = ["total_fertility_rate"]


def _full(sx, year=2020):
    return [f"{sx}_{b:02d}_{year}" for b in V.BANDS]


# ------------------------------------------------ P1: children under five
@pytest.mark.parametrize("sex", ["both", "women", "men"])
@pytest.mark.parametrize("gone", ["m_00", "m_01", "f_00"])
def test_a_hole_in_the_children_is_refused_whoever_the_tables_are_for(
        sex, gone):
    """The review's case: every band of both sexes but one under-five
    band, TFR with women's life tables - accepted, and the children
    summed from what was there.

    BROKEN WITH: the children summed from whatever ages 0 and 1 were
    present (the 1.60.1 rule)."""
    labels = [c for c in _full("f") + _full("m")
              if not c.startswith(gone + "_")]
    if sex == "both" or gone[0] == {"women": "f", "men": "m"}[sex]:
        # the life tables' own completeness check speaks first
        with pytest.raises(DemographyError):
            vital_plan(labels, TFR, sex=sex)
        return
    with pytest.raises(DemographyError, match=f"under five.*{gone}"):
        vital_plan(labels, TFR, sex=sex)


def test_the_both_sexes_files_stand_in_for_a_broken_pair():
    """f and m with a hole, t complete: t is a complete route of its
    own, so it is used rather than refusing.

    BROKEN WITH: only the first route tried."""
    labels = ([c for c in _full("f") + _full("m")
               if not c.startswith("m_00_")] + _full("t"))
    vp = vital_plan(labels, TFR, sex="women")
    assert vp["child_route"] == ["t"]
    assert vp["child_cols"] == ["t_00_2020", "t_01_2020"]


def test_complete_girls_and_boys_are_both_counted():
    """BROKEN WITH: the route taken as the life tables' sex."""
    vp = vital_plan(_full("f") + _full("m"), TFR, sex="women")
    assert vp["child_route"] == ["f", "m"]
    assert sorted(vp["child_cols"]) == ["f_00_2020", "f_01_2020",
                                        "m_00_2020", "m_01_2020"]


def test_girls_alone_only_when_there_are_no_boys_at_all_and_it_is_said():
    """A folder of women's files only: girls against the nation's girls
    is a fair ratio, and the log says that is what was done.

    BROKEN WITH: the NOTE removed from _say_vital."""
    from equipop.doors.demography import _say_vital
    vp = vital_plan(_full("f"), TFR, sex="women")
    assert vp["child_route"] == ["f"]
    said = []
    _say_vital(said.append, vp, {}, [], [5000])
    assert any("girls alone" in s for s in said)


# ------------------------------------ P1: a projection with no EPSG code
pytest.importorskip("rasterio")
import test_machine4_points as MP                        # noqa: E402

CUSTOM = ("+proj=tmerc +lat_0=0 +lon_0=36.3 +k=0.9996 +x_0=400000 "
          "+y_0=10000000 +ellps=WGS84 +units=m +no_defs")


@pytest.fixture(scope="module")
def custom(tmp_path_factory):
    """The test folder's points, saved in a transverse Mercator that
    has no EPSG code."""
    from pyproj import CRS, Transformer
    from equipop.doors.continental import run_folder
    d = tmp_path_factory.mktemp("custom")
    with redirect_stdout(io.StringIO()):
        folder = MP.M4.make_folder(d)
        man = run_folder(str(folder), k_values=[])
    t = man["points_table"].rename(columns={"lon": "EastWest",
                                            "lat": "NorthSouth"})
    wkt = CRS.from_proj4(CUSTOM).to_wkt()
    assert CRS.from_wkt(wkt).to_epsg() is None
    tr = Transformer.from_crs(man["crs"], wkt, always_xy=True)
    x, y = tr.transform(t["EastWest"].to_numpy(float),
                        t["NorthSouth"].to_numpy(float))
    return str(folder), t.assign(EastWest=x, NorthSouth=y), wkt


def test_points_in_a_projection_with_no_code_are_reprojected(custom):
    """The review's reproduction: 'Invalid projection: EPSG:None'. Now
    the points go into the suggested projection, as degrees do - and
    give the folder's numbers when the same projection is used.

    BROKEN WITH: to_epsg()'s None taken as the target again."""
    from equipop.doors.demography import run_indices
    folder, table, wkt = custom
    out = io.StringIO()
    with redirect_stdout(out):
        man = run_indices(None, ["child_woman_ratio"], k_values=[3000],
                          unit_size=1000.0, points=table,
                          points_crs=wkt)
    assert "no EPSG code" in out.getvalue()
    assert man["projection"]["epsg"]
    with redirect_stdout(io.StringIO()):
        a = run_indices(folder, ["child_woman_ratio"], k_values=[3000],
                        unit_size=1000.0,
                        epsg=man["projection"]["epsg"])["results"]
    MP._same(a, man["results"], ["cwr_3000", "Dist_3000"])


def test_qgis_sends_a_user_projection_as_its_definition(custom):
    """A QGIS USER: system has no code anything else can look up; its
    WKT travels instead, and the run gives the folder's numbers.

    BROKEN WITH: the authid sent as it stands ('USER:100001')."""
    import qgis_stub
    folder, table, wkt = custom
    lyr = table.rename(columns={"EastWest": "x", "NorthSouth": "y"})
    src = qgis_stub._Source(lyr, crs="USER:100001", geometry=True)
    src._crs._wkt = wkt
    a = MP._qgis_run(folder=folder, rates=[])
    b = MP._qgis_run(points=src, rates=[])
    a = a.sort_values("cwr_3000").reset_index(drop=True)
    b = b.sort_values("cwr_3000").reset_index(drop=True)
    assert np.allclose(a["cwr_3000"], b["cwr_3000"])


def test_pro_sends_a_projection_with_no_code_as_its_definition(custom):
    """arcpy's exportToString is Esri WKT followed by ';'-separated
    tolerances; the WKT alone goes to the engine, which can read it.

    BROKEN WITH: the whole exportToString sent."""
    import types
    from pyproj import CRS
    import test_arcgis_continental as AC
    _folder, _table, wkt = custom
    pyt, _tool, _state = AC._tool("SpatialDemography")
    sr = types.SimpleNamespace(
        factoryCode=0,
        exportToString=lambda: wkt + ";-5120900 -9998100 10000;"
                                     "-100000 10000;0.001;IsHighPrecision")
    got = pyt._pyproj_crs(sr)
    assert got == wkt
    assert CRS.from_user_input(got).is_projected


# ------------------------------------- P1: the point layer's own values
from equipop.rasterfolder import load_points, to_long    # noqa: E402


def _wide(**cols):
    base = {"EastWest": [36.10, 36.11, 36.12], "NorthSouth": [-1.1] * 3,
            "iso3": ["ken"] * 3, "f_00_2020": [3.0, 4.0, 5.0],
            "m_00_2020": [2.0, 2.0, 2.0]}
    base.update(cols)
    return pd.DataFrame(base)


@pytest.mark.parametrize("bad, what", [
    (["3", "abc", "5"], "not a number"),
    ([3.0, -4.0, 5.0], "negative"),
    ([3.0, np.inf, 5.0], "infinite")])
def test_values_that_cannot_be_people_are_refused_by_field(bad, what):
    """1.60.1 coerced every cohort and filled the failures with 0.

    BROKEN WITH: _check_counts emptied (the 1.60.1 rule)."""
    with pytest.raises(ValueError, match=f"f_00_2020: 1 {what}"):
        load_points(_wide(f_00_2020=bad), "EPSG:4326")


@pytest.mark.parametrize("blank", [None, np.nan, "", "  "])
def test_a_blank_is_nobody_and_is_said_and_recorded(blank):
    """John: "zero is our way". A blank - what a join leaves where it
    found nothing - is read as no people, and the run says so per field
    and keeps the count.

    BROKEN WITH: the blanks message and record removed; and with
    blanks refused like text."""
    out = io.StringIO()
    t = _wide(f_00_2020=pd.Series([3.0, blank, 5.0], dtype=object))
    with redirect_stdout(out):
        pts, man = load_points(t, "EPSG:4326")
    assert pts["f_00_2020"].tolist() == [3.0, 0.0, 5.0]
    assert man["blanks_as_zero"] == {"f_00_2020": 1}
    assert "BLANKS COUNTED AS NOBODY" in out.getvalue()
    assert "f_00_2020 1" in out.getvalue()


def test_the_long_shape_checks_and_counts_its_values_too():
    """In the long shape the faults are named by cohort; a blank
    population and a cohort no row was given for are both blanks.

    BROKEN WITH: the long shape's population column not checked (text
    then reached the sum); and with sum() in place of
    sum(min_count=1), which hides the blank population."""
    long = to_long(_wide().rename(columns={"EastWest": "lon",
                                           "NorthSouth": "lat"}))
    bad = long.copy()
    bad["population"] = bad["population"].astype(object)
    bad.loc[bad["cohort"] == "m_00_2020", "population"] = "x"
    with pytest.raises(ValueError, match="m_00_2020: 3 not a number"):
        load_points(bad, "EPSG:4326")
    gap = long.copy()
    gap["population"] = gap["population"].astype(object)
    gap.loc[0, "population"] = None                 # a blank
    gap = gap.drop(index=gap.index[-1])             # a missing row
    out = io.StringIO()
    with redirect_stdout(out):
        pts, man = load_points(gap, "EPSG:4326")
    assert sum(man["blanks_as_zero"].values()) == 2
    assert np.isfinite(pts[["f_00_2020", "m_00_2020"]].to_numpy()).all()


def test_qgis_says_where_a_join_left_blanks(tmp_path):
    """Through the door: a layer with NULLs runs, and the log says how
    many blanks were read as nobody.

    BROKEN WITH: the blanks message removed."""
    import qgis_stub
    folder, table, crs = MP_made(tmp_path)
    lyr = table.rename(columns={"EastWest": "x", "NorthSouth": "y"})
    lyr["f_15_2020"] = lyr["f_15_2020"].astype(object)
    lyr.loc[lyr.index[:5], "f_15_2020"] = None
    src = qgis_stub._Source(lyr, crs=crs, geometry=True)
    _out, lines = _qgis_lines(points=src, rates=[])
    assert any("BLANKS COUNTED AS NOBODY" in s and "f_15_2020 5" in s
               for s in lines)


def MP_made(tmp_path):
    from equipop.doors.continental import run_folder
    with redirect_stdout(io.StringIO()):
        folder = MP.M4.make_folder(tmp_path)
        man = run_folder(str(folder), k_values=[])
    t = man["points_table"].rename(columns={"lon": "EastWest",
                                            "lat": "NorthSouth"})
    return str(folder), t, man["crs"]


def _qgis_lines(**params):
    sys.path.insert(0, str(ROOT / "qgis"))
    import qgis_stub
    qgis_stub.install()
    from equipop_qgis.alg_demography import SpatialDemography
    import test_vital_doors as VD
    alg = SpatialDemography()
    alg.initAlgorithm()
    p = {"folder": "", "indices": [1], "rates": [0], "ratesex": 0,
         "k": "3000", "unit": 1000.0, "year": "", "crs": None,
         "outcrs": None, "settings": [], "OUTPUT": "memory:"}
    p.update(params)
    fb = VD._Feedback()
    alg.processAlgorithm(p, {}, fb)
    return p["_sinks"]["OUTPUT"].to_frame(), fb.lines


# ---------------------------------------- P2: guessing degrees, by name
def test_plain_x_y_without_a_crs_are_refused_even_inside_180_90():
    """A local grid near its origin fits inside +-180/+-90. Only names
    that promise degrees are read as degrees.

    BROKEN WITH: the name check removed (x/y inside the range read as
    degrees again)."""
    t = pd.DataFrame({"x": [12.0, 40.0], "y": [8.0, 30.0],
                      "f_00_2020": [3.0, 4.0]})
    with pytest.raises(ValueError, match="'x' and 'y'"):
        load_points(t, None)
    with redirect_stdout(io.StringIO()):
        _p, man = load_points(t.rename(columns={"x": "lon", "y": "lat"}),
                              None)
    assert man["crs"] == "EPSG:4326"


# ------------------------------------------- P3: fields left out, named
def test_the_long_shape_names_what_the_pivot_drops():
    """BROKEN WITH: the dropped names taken after the pivot (the 1.60.1
    order - by then they are gone)."""
    long = to_long(_wide().rename(columns={"EastWest": "lon",
                                           "NorthSouth": "lat"}))
    long["OBJECTID"] = range(len(long))
    long["joined_name"] = "Kibera"
    out = io.StringIO()
    with redirect_stdout(out):
        _p, man = load_points(long, "EPSG:4326")
    assert {"OBJECTID", "joined_name"} <= set(man["fields_not_used"])
    assert "joined_name" in out.getvalue()


def test_qgis_names_the_fields_it_did_not_read(tmp_path):
    """The door reads only what it needs; the engine names the rest.

    BROKEN WITH: the door's fields_not_used not set."""
    import qgis_stub
    folder, table, crs = MP_made(tmp_path)
    lyr = table.rename(columns={"EastWest": "x", "NorthSouth": "y"})
    lyr["district"] = "Nairobi"
    src = qgis_stub._Source(lyr, crs=crs, geometry=True)
    _out, lines = _qgis_lines(points=src, rates=[])
    assert any("not used" in s and "district" in s for s in lines)


def test_pro_names_the_fields_it_did_not_read(tmp_path):
    """BROKEN WITH: the door's fields_not_used not set."""
    import test_arcgis_continental as AC
    folder, table, crs = MP_made(tmp_path)
    pyt, tool, state = AC._tool("SpatialDemography")
    lyr = table.rename(columns={"EastWest": "SHAPE@X",
                                "NorthSouth": "SHAPE@Y"})
    lyr["iso3"] = lyr["iso3"].astype(str)
    lyr["district"] = "Nairobi"
    state.setdefault("layers", {})["m3points"] = lyr
    state.setdefault("crs_codes", {})["m3points"] = 4326
    msg = AC._Messages()
    tool.execute(AC._params(tool, points="m3points", indices="Child-"
                            "woman ratio", k="3000", unit=1000.0,
                            out=str(tmp_path / "o.shp")), msg)
    assert any("not used" in str(m) and "district" in str(m)
               for m in msg.log)


# --------------------------- P2: redirects on fetch() and the older path
import importlib                                         # noqa: E402
F = importlib.import_module("equipop.fetch")   # the module, not fetch()
from equipop.doors import fetching as FE                 # noqa: E402

WP = "https://data.worldpop.org/GIS/x.tif"


@pytest.fixture
def web(monkeypatch):
    """The https transport answering from a table, as in
    test_download_limits - put in front of the real opener."""
    import test_download_limits as DL

    def install(answers):
        h = DL._Https(answers)
        monkeypatch.setattr(F, "_TEST_HANDLERS", (h,))
        return h
    return install


@pytest.mark.parametrize("to, words", [
    ("https://elsewhere.example.com/x.tif", "not at worldpop.org"),
    ("http://data.worldpop.org/GIS/x.tif", "not https"),
    ("https://worldpop.org.example.com/x.tif", "not at worldpop.org")])
def test_the_older_download_path_refuses_a_redirect_elsewhere(
        web, tmp_path, to, words):
    """5a/5d's _get_file followed a redirect wherever it pointed.

    BROKEN WITH: _open back on urllib.request.urlopen; and with the
    domain check removed from checked_opener."""
    https = web({WP: to, to: "BYTES"})
    dest = str(tmp_path / "x.tif")
    with pytest.raises(F.RedirectRefused, match=words) as e:
        FE._get_file(WP, dest)
    assert to in str(e.value)
    assert https.asked == [WP]
    assert os.listdir(tmp_path) == []          # nothing kept, no .part


def test_the_older_path_follows_a_redirect_within_the_provider(web,
                                                               tmp_path):
    """BROKEN WITH: every redirect refused."""
    other = "https://hub.worldpop.org/files/x.tif"
    web({WP: other, other: "BYTES"})
    n, _sha, _md5 = FE._get_file(WP, str(tmp_path / "x.tif"))
    assert n == 5 and (tmp_path / "x.tif").read_bytes() == b"BYTES"


def test_the_sidecars_go_the_same_way(web):
    """The .md5 sidecar and the API's JSON: the same opener.

    BROKEN WITH: _get_text and _get_json on urlopen."""
    to = "https://elsewhere.example.com/x"
    web({WP + ".md5": to, WP + ".json": to, to: "{}"})
    with pytest.raises(F.RedirectRefused):
        FE._get_text(WP + ".md5")
    with pytest.raises(F.RedirectRefused):
        FE._get_json(WP + ".json")


def test_fetch_follows_other_sites_but_never_down_to_http(web, tmp_path):
    """fetch() takes any http(s) address, so another site is fine - but
    not a step down from https to http.

    BROKEN WITH: fetch() back on urlopen."""
    a, b = "https://one.example.org/a.csv", "https://two.example.net/a.csv"
    web({a: b, b: "x,y\n1,2\n"})
    path = F.fetch(a, str(tmp_path / "w"))
    assert open(path).read() == "x,y\n1,2\n"
    c, d = "https://one.example.org/c.csv", "http://one.example.org/c.csv"
    web({c: d, d: "x"})
    with pytest.raises(ConnectionError, match="not https"):
        F.fetch(c, str(tmp_path / "w2"))
    assert not os.path.exists(tmp_path / "w2" / "c.csv")


# --------------------------------------- P3: the WPP table, checked at load
@pytest.fixture
def copied(tmp_path, monkeypatch):
    """The shipped table and its record, copied where a test may spoil
    them; the cache cleared before and after."""
    import shutil
    src = V._data_dir()
    for n in (V.REFERENCE, V.REFERENCE.replace(".csv.xz", ".json")):
        shutil.copy(os.path.join(src, n), tmp_path / n)
    monkeypatch.setattr(V, "_data_dir", lambda: str(tmp_path))
    V.reference.cache_clear()
    yield tmp_path
    V.reference.cache_clear()


def test_the_shipped_table_passes_its_own_check():
    """BROKEN WITH: the record's sha256 not matching (refreshed table,
    stale record) - which is what the check is for."""
    V.reference.cache_clear()
    df, meta = V.reference()
    assert len(df) == 21948 and meta["countries"] == 236
    assert df.loc[("SWE", 2020, "B"), "pop"] > 9e6


def test_a_damaged_table_is_refused(copied):
    """One byte changed: refused before a value is read.

    BROKEN WITH: the checksum comparison removed."""
    p = copied / V.REFERENCE
    b = bytearray(p.read_bytes())
    b[-10] ^= 0xFF
    p.write_bytes(bytes(b))
    with pytest.raises(V.VitalError, match="does not match its own record"):
        V.reference()


def test_a_table_without_its_columns_is_refused(copied):
    """A table whose record was refreshed with it but which lacks a
    column the estimators read.

    BROKEN WITH: the column check removed."""
    import hashlib
    import json
    import lzma
    p = copied / V.REFERENCE
    df = pd.read_csv(p).drop(columns=["pop"])
    p.write_bytes(lzma.compress(df.to_csv(index=False).encode()))
    j = copied / V.REFERENCE.replace(".csv.xz", ".json")
    meta = json.loads(j.read_text(encoding="utf-8"))
    meta["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
    j.write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(V.VitalError, match="columns missing: pop"):
        V.reference()


# ------------------------------------------------- the whole-country warning
def test_coverage_is_the_folder_total_against_wpp():
    """A folder holding exactly WPP's Kenya reads 100%; half of it 50%.

    BROKEN WITH: coverage computed against the women's population for
    a both-sexes run. (The first version of this test read WPP's
    figure through national() - the function the break changes - so
    the break moved the expected value with it and survived. WPP's
    number is now read from the table itself.)"""
    from equipop.doors.demography import vital_references
    labels = _full("f") + _full("m")
    vp = vital_plan(labels, ["life_expectancy_60"])
    nat = float(V.reference()[0].loc[("KEN", 2020, "B"), "pop"])
    per = nat / len(labels)
    pts = pd.DataFrame({c: [per / 2, per / 2] for c in labels})
    pts["iso3"] = "ken"
    refs, _absent = vital_references(vp, pts)
    assert refs["ken"]["coverage"] == pytest.approx(1.0, rel=1e-6)
    refs, _absent = vital_references(vp, pts.iloc[:1])
    assert refs["ken"]["coverage"] == pytest.approx(0.5, rel=1e-6)


@pytest.mark.parametrize("cov, warned", [(0.97, False), (0.41, True)])
def test_a_folder_short_of_its_country_is_warned_about(cov, warned):
    """John's choice: a folder far short of WPP's national population
    is warned about, by country and share.

    BROKEN WITH: the warning removed from _say_vital."""
    from equipop.doors.demography import _say_vital
    vp = vital_plan(_full("f") + _full("m"), ["life_expectancy_60"])
    nat = V.national("KEN", 2020, "B")
    refs = {"ken": {"nat": nat, "P": np.ones(len(vp["bands"])),
                    "coverage": cov, "e60": 15.0}}
    said = []
    _say_vital(said.append, vp, refs, [], [5000])
    hit = [s for s in said if "NOT THE WHOLE COUNTRY" in s]
    assert bool(hit) == warned
    if warned:
        assert "KEN holds 41% of WPP's 2020 population" in hit[0]


def test_the_run_records_how_much_of_each_country_it_held(tmp_path):
    """BROKEN WITH: national_coverage left out of the record."""
    from equipop.doors.demography import run_indices
    folder, _t, _crs = MP_made(tmp_path)
    with redirect_stdout(io.StringIO()):
        man = run_indices(folder, [], vital=["life_expectancy_60"],
                          k_values=[3000], unit_size=1000.0, epsg=32737)
    cov = man["vital"]["national_coverage"]
    assert set(cov) == {"KEN"} and 0 < cov["KEN"] < V.WHOLE_COUNTRY


# --------------------------------------- P3: the data's licence, shipped
def test_the_third_party_notice_travels_in_both_archives():
    """At the top of the source archive and inside the package, the
    same words; and the citation file names WPP 2024.

    BROKEN WITH: the package copy edited alone; and with the notice
    left out of package-data."""
    top = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    inside = (ROOT / "equipop" / "THIRD_PARTY_NOTICES.md").read_text(
        encoding="utf-8")
    assert top == inside
    assert "CC BY 3.0 IGO" in top and "wpp2024_reference.csv.xz" in top
    toml = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    block = toml.split("[tool.setuptools.package-data]", 1)[1]
    assert '"THIRD_PARTY_NOTICES.md"' in block.split("\n[", 1)[0]
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert "\ninclude THIRD_PARTY_NOTICES.md\n" in manifest
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    entry = cff.split('title: "World Population Prospects 2024"', 1)
    # v1.61.3 (BACKLOG 428): the licence is named in the entry's notes,
    # because CFF 1.2.0's `license:` list does not contain CC-BY-3.0-IGO.
    assert len(entry) == 2 and "Licence CC BY 3.0 IGO" in \
        entry[1].split("  - type:", 1)[0]


# ------------------- 1.60.3: an old package under a new toolbox, in Pro
def test_every_pro_tool_refuses_a_package_older_than_the_toolbox():
    """John, 19 October: "run_folder() got an unexpected keyword
    argument 'vital'" - the 1.60.2 toolbox over the 1.59.2 package.
    Every machine now stops before it starts, names both versions and
    says how to install the right wheel.

    BROKEN WITH: the older-package refusal removed (machines 1-2 then
    only warn and 3-6 run on); and with the call left out of machine
    4's execute."""
    import equipop
    import test_arcgis_continental as AC
    pyt = AC._pyt()
    real = equipop.__version__
    equipop.__version__ = "1.59.2"
    try:
        for cls in pyt.Toolbox().all_tools:
            tool = cls()
            with pytest.raises(pyt.arcpy.ExecuteError,
                               match="OLDER THAN THIS TOOLBOX") as e:
                tool.execute(tool.getParameterInfo(), AC._Messages())
            assert "package 1.59.2" in str(e.value), cls.__name__
            assert f"equipop-{pyt.TOOLBOX_VERSION}-py3-none-any.whl" in \
                str(e.value)
    finally:
        equipop.__version__ = real


def test_a_package_newer_than_the_toolbox_only_warns():
    """A newer package is most often a toolbox Pro has cached
    (BACKLOG 314); the run can work, so it is a warning.

    BROKEN WITH: the refusal made to cover any mismatch."""
    import equipop
    import test_arcgis_continental as AC
    pyt = AC._pyt()
    real = equipop.__version__
    equipop.__version__ = "99.0.0"
    try:
        m = AC._Messages()
        pyt._announce_version(m)
        assert any("DIFFERENT VERSIONS" in str(x) for x in m.log)
    finally:
        equipop.__version__ = real


def test_qgis_refuses_a_package_older_than_the_plugin():
    """The same rule in QGIS, at machine 4's door.

    BROKEN WITH: check_versions only warning again."""
    import equipop
    import equipop_qgis
    from qgis.core import QgsProcessingException
    real = equipop.__version__
    equipop.__version__ = "1.59.2"
    try:
        with pytest.raises(QgsProcessingException,
                           match="OLDER than this plugin"):
            _qgis_lines(folder="x")
    finally:
        equipop.__version__ = real
    assert equipop_qgis.__version__ != "1.59.2"


# ------------- 1.60.3: build_cells in one pass, answers unchanged
def _old_aggregate(df, binary_vars, value_vars, weights, label_col):
    """build_cells' per-cell loop as it was to 1.60.2, kept here as the
    answer key for the vectorised pass."""
    out = {"E": [], "N": [], "n": [], "bs": {v: [] for v in binary_vars},
           "bv": {v: [] for v in binary_vars},
           "va": {v: [] for v in value_vars},
           "vw": {v: [] for v in value_vars}, "lab": []}
    for (e, nn), g in df.groupby(["_E", "_N"], sort=True):
        out["E"].append(e)
        out["N"].append(nn)
        out["n"].append(float(g[weights].sum()) if weights else len(g))
        for v in binary_vars:
            if weights is None:
                out["bs"][v].append(g[v].sum())
                out["bv"][v].append(int(g[v].notna().sum()))
            else:
                w = g[weights]
                out["bs"][v].append(float((g[v].fillna(0) * w).sum()))
                out["bv"][v].append(float(w[g[v].notna()].sum()))
        for v in value_vars:
            keep = g[v].notna()
            out["va"][v].append(g.loc[keep, v].to_numpy(dtype=float))
            if weights:
                out["vw"][v].append(g.loc[keep, weights].to_numpy(float))
        if label_col:
            out["lab"].append("|".join(sorted(
                g[label_col].astype(str).unique())))
    return out


@pytest.mark.parametrize("weighted", [False, True])
def test_build_cells_in_one_pass_gives_the_loops_answers(weighted):
    """Sums, valid counts, the value arrays in their row order, and the
    labels - against the loop it replaced, with blanks, an infinity,
    several rows per cell and mixed labels.

    BROKEN WITH: the valid count taken from every row (blanks counted
    as valid); and with the value arrays split without the stable
    sort (rows out of order within a cell)."""
    from equipop.cells import build_cells
    rng = np.random.default_rng(7)
    n = 3000
    df = pd.DataFrame({"x": rng.integers(0, 40, n) * 100.0 + 3,
                       "y": rng.integers(0, 30, n) * 100.0 + 7,
                       "w": rng.random(n) * 9,
                       "lab": rng.choice(["a", "b", "c"], n, p=[.8, .15, .05])})
    for v in ("g1", "g2", "v1"):
        df[v] = rng.random(n)
        df.loc[rng.random(n) < 0.1, v] = np.nan
    df.loc[5, "g2"] = np.inf
    with redirect_stdout(io.StringIO()):
        cd = build_cells(df, "x", "y", binary_vars=["g1", "g2"],
                         value_vars=["v1"], unit_size=100.0,
                         label_col="lab", weights="w" if weighted else None)
    d = df.copy()
    d["_E"] = (np.floor(d["x"] / 100) * 100 + 50).astype(int)
    d["_N"] = (np.floor(d["y"] / 100) * 100 + 50).astype(int)
    old = _old_aggregate(d, ["g1", "g2"], ["v1"], "w" if weighted else None,
                         "lab")
    assert np.array_equal(cd.E, old["E"]) and np.array_equal(cd.N, old["N"])
    assert np.allclose(cd.n, old["n"], rtol=1e-12, atol=0)
    for v in ("g1", "g2"):
        assert np.allclose(cd.binary_sums[v], old["bs"][v], rtol=1e-12,
                           atol=1e-12, equal_nan=True)
        assert np.allclose(cd.binary_valid[v], old["bv"][v], rtol=1e-12)
    assert len(cd.value_arrays["v1"]) == len(old["va"]["v1"])
    for a, b in zip(cd.value_arrays["v1"], old["va"]["v1"]):
        assert np.array_equal(a, b)
    if weighted:
        for a, b in zip(cd.value_weights["v1"], old["vw"]["v1"]):
            assert np.array_equal(a, b)
    assert cd.labels == old["lab"]
    assert any("|" in s for s in cd.labels)


def test_build_cells_is_fast_enough_for_a_country():
    """32 groups over 20,000 cells: the loop took about 0.3 ms per cell
    and group here - over three minutes; one pass takes a second or
    two.

    BROKEN WITH: the per-cell loop put back."""
    import time
    from equipop.cells import build_cells
    rng = np.random.default_rng(0)
    n = 30000
    df = pd.DataFrame({"x": rng.integers(0, 20000, n) * 1000.0 + 500,
                       "y": np.full(n, 500.0), "w": rng.random(n) * 50})
    gs = [f"g{i}" for i in range(32)]
    for g in gs:
        df[g] = rng.random(n)
    t = time.time()
    with redirect_stdout(io.StringIO()):
        cd = build_cells(df, "x", "y", binary_vars=gs, unit_size=1000.0,
                         weights="w")
    assert len(cd) > 15000
    assert time.time() - t < 30
