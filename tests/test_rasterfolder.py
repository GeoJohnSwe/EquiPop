"""BACKLOG 206 - the folder loader, tested on the real fixture.

The rule under test is John's, and it is about GEOMETRY:
    different ground does not overlap -> ROWS
    same ground does overlap          -> COLUMNS
so the merge survives any renaming. Filenames only label the columns.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("rasterio")
from equipop.rasterfolder import (  # noqa: E402
    load_folder, parse_name, age_band, band_width, CONVENTIONS)

FIX = Path(__file__).resolve().parent / "fixtures" / "worldpop"


@pytest.fixture(scope="module")
def loaded():
    return load_folder(FIX)


def test_the_fixture_folder_is_there():
    tifs = sorted(FIX.glob("*.tif"))
    assert len(tifs) == 3, f"expected three fixture rasters, found {len(tifs)}"


def test_mass_is_conserved(loaded):
    """People in equals people out. Everything else is decoration."""
    pts, man = loaded
    into = sum(f["total"] for f in man["files"].values())
    out = pts[[c for c in pts.columns
               if c not in ("lon", "lat", "iso3")]].to_numpy().sum()
    assert out == pytest.approx(into, rel=1e-9)


def test_same_cohort_different_countries_becomes_ONE_column(loaded):
    """bdi, rwa and dnk are all f_15_2020 - one cohort, three grounds.

    They must stack as ROWS under a single column. If iso3 leaked into
    the label there would be three columns and each country's people
    would sit in a column of their own, full of zeros elsewhere.
    """
    pts, man = loaded
    value_cols = [c for c in pts.columns
                  if c not in ("lon", "lat", "iso3")]
    assert value_cols == ["f_15_2020"], value_cols
    assert len(man["labels"]["f_15_2020"]) == 3


def test_the_countries_do_not_overlap(loaded):
    """Rows, not columns - so the row count is the sum of the parts."""
    pts, man = loaded
    assert len(pts) == sum(f["pixels"] for f in man["files"].values())


def test_zeros_are_kept_where_another_layer_has_data():
    """John's rule, and the defect it replaces.

    Build a second column from the same ground so every pixel exists in
    one layer and not the other. Nothing may be dropped.
    """
    import rasterio
    bdi = FIX / "bdi_f_15_2020_CN_100m_R2025A_v1.tif"
    dnk = FIX / "dnk_f_15_2020_CN_100m_R2025A_v1.tif"
    # label them as two different cohorts on their own ground
    pts, man = load_folder(FIX, labels={
        bdi.stem: "cohort_a", dnk.stem: "cohort_b",
        (FIX / "rwa_f_15_2020_CN_100m_R2025A_v1.tif").stem: "cohort_a"})
    assert {"cohort_a", "cohort_b"} <= set(pts.columns)
    # every Danish pixel must survive with a real 0.0 in cohort_a
    danish = pts[pts["cohort_b"] > 0]
    assert len(danish) > 10_000
    assert (danish["cohort_a"] == 0.0).all()
    assert not danish["cohort_a"].isna().any(), "zeros, not absences"


def _tiny(path, west, south, vals):
    """A 3x3 raster on the WorldPop lattice, for constructing cases."""
    import rasterio
    from rasterio.transform import from_origin
    px = 1.0 / 1200
    a = np.asarray(vals, dtype="float32")
    with rasterio.open(path, "w", driver="GTiff", height=a.shape[0],
                       width=a.shape[1], count=1, dtype="float32",
                       crs="EPSG:4326", nodata=-99999.0,
                       transform=from_origin(west, south + a.shape[0] * px,
                                             px, px)) as d:
        d.write(a, 1)


def test_disjoint_rasters_sharing_a_label_are_ALLOWED(tmp_path):
    """The legitimate case: one cohort, several countries.

    The three fixture rasters really are disjoint, so labelling them
    alike is concatenation and must be permitted. An earlier version of
    this test expected a refusal here and was wrong about the data.
    """
    pts, man = load_folder(FIX, labels={
        "bdi_f_15_2020_CN_100m_R2025A_v1": "same",
        "rwa_f_15_2020_CN_100m_R2025A_v1": "same",
        "dnk_f_15_2020_CN_100m_R2025A_v1": "same"})
    assert [c for c in pts.columns
            if c not in ("lon", "lat", "iso3")] == ["same"]
    assert len(pts) == sum(f["pixels"] for f in man["files"].values())


def test_overlapping_rasters_sharing_a_label_are_REFUSED(tmp_path):
    """The safety net: same label + same pixel = silent double counting.

    Constructed rather than borrowed, because the fixture has no such
    pair - the condition has to be built to be tested.
    """
    _tiny(tmp_path / "a_f_15_2020.tif", 30.0, -2.0, [[1., 2.], [3., 4.]])
    _tiny(tmp_path / "b_f_15_2020.tif", 30.0, -2.0, [[5., 0.], [0., 6.]])
    with pytest.raises(ValueError, match="carry data in TWO rasters"):
        load_folder(tmp_path, labels={"a_f_15_2020": "same",
                                      "b_f_15_2020": "same"})


def test_overlapping_rasters_with_DIFFERENT_labels_become_columns(tmp_path):
    """The same two rasters, correctly labelled, are two cohorts."""
    _tiny(tmp_path / "a_f_15_2020.tif", 30.0, -2.0, [[1., 2.], [3., 4.]])
    _tiny(tmp_path / "b_m_15_2020.tif", 30.0, -2.0, [[5., 0.], [0., 6.]])
    pts, _ = load_folder(tmp_path, labels={"a_f_15_2020": "women",
                                           "b_m_15_2020": "men"})
    assert len(pts) == 4                      # one row per pixel
    assert pts["women"].sum() == pytest.approx(10.0)
    assert pts["men"].sum() == pytest.approx(11.0)
    # and the zeros survived where one cohort was empty
    assert (pts["men"] == 0.0).sum() == 2


def test_sum_cohorts_is_opt_in(loaded):
    pts, _ = loaded
    summed, _ = load_folder(FIX, sum_cohorts=True)
    assert list(summed.columns) == ["lon", "lat", "iso3", "pop"]
    assert summed["pop"].sum() == pytest.approx(
        pts[[c for c in pts.columns
             if c not in ("lon", "lat", "iso3")]].to_numpy().sum(), rel=1e-9)


# ------------------------------------------------------------- naming
def test_the_worldpop_convention_parses():
    d = parse_name("bdi_f_15_2020_CN_100m_R2025A_v1")
    assert d["iso3"] == "bdi" and d["sex"] == "f"
    assert d["age"] == "15" and d["year"] == "2020"
    assert d["_convention"] == "worldpop_r2025a"


def test_an_unknown_name_degrades_instead_of_guessing():
    d = parse_name("something_nobody_planned_for")
    assert d["_convention"] is None


def test_a_user_regex_overrides_the_registry(tmp_path):
    """The escape hatch for when the convention moves on."""
    got = parse_name("bdi_f_15_2020_CN_100m_R2025A_v1")
    assert got["_convention"] == "worldpop_r2025a"
    CONVENTIONS["_probe"] = r"^(?P<iso3>[a-z]{3})_(?P<sex>[fmt])_.*$"
    try:
        d = parse_name("bdi_f_15_2020_CN_100m_R2025A_v1", "_probe")
        assert d["iso3"] == "bdi" and d["_convention"] == "_probe"
    finally:
        CONVENTIONS.pop("_probe")


# --------------------------------------------------------- age bands
@pytest.mark.parametrize("start,expected,width", [
    (0, (0, 0), 1),        # under one, on its own
    (1, (1, 4), 4),        # four years, not five
    (5, (5, 9), 5),
    (15, (15, 19), 5),
    (85, (85, 89), 5),
    (90, (90, None), None),   # open-ended: refuse rather than guess
])
def test_age_bands_are_not_all_five_years(start, expected, width):
    assert age_band(start) == expected
    assert band_width(start) == width


def test_an_open_band_has_no_width():
    """90+ has no last year, so a rate across it cannot be formed.

    Cohorts can always be SUMMED - people are people. Averaging or
    differencing across bands needs the width, and here there isn't
    one. None means refuse, not guess.
    """
    assert band_width(90) is None
    assert band_width(95) is None


# ---------------------------------------------------------------------
# BACKLOG 211 - names and cohorts from JOHN'S REAL DOWNLOAD.
#
# The registry was built from the four sample files Claude had, all of
# them "..._CN_100m_R2025A_v1". His actual bulk download is
# "..._CN_1km_R2025A_UA_v1" and ALL 120 NAMES FELL THROUGH: the pattern
# demanded \d+m where the file said 1km, and had no slot for UA. Every
# file then got its own column INCLUDING THE COUNTRY, so bdi_f_15 and
# rwa_f_15 became two columns instead of one.
# ---------------------------------------------------------------------
REAL = [  # verbatim from John's QGIS log, 2026-08-23
    "bdi_f_00_2026_CN_1km_R2025A_UA_v1",
    "bdi_m_15_2026_CN_1km_R2025A_UA_v1",
    "bdi_t_90_2026_CN_1km_R2025A_UA_v1",
    "rwa_f_45_2026_CN_1km_R2025A_UA_v1",
    "rwa_t_01_2026_CN_1km_R2025A_UA_v1",
]
SAMPLE = ["bdi_f_15_2020_CN_100m_R2025A_v1",
          "dnk_f_15_2020_CN_100m_R2025A_v1"]


@pytest.mark.parametrize("stem", REAL + SAMPLE)
def test_both_the_real_download_and_the_sample_parse(stem):
    d = parse_name(stem)
    assert d["_convention"] == "worldpop_r2025a", (
        f"{stem} fell through the registry")
    assert d["iso3"] == stem[:3]
    assert d["sex"] in ("f", "m", "t")
    assert d["age"].isdigit() and d["year"].isdigit()


def test_the_country_is_never_part_of_the_label():
    """The failure that made 120 columns out of 60 cohorts."""
    a = _label_of("bdi_f_15_2026_CN_1km_R2025A_UA_v1")
    b = _label_of("rwa_f_15_2026_CN_1km_R2025A_UA_v1")
    assert a == b == "f_15_2026", (a, b)


def _label_of(stem):
    from equipop.rasterfolder import _label
    return _label(stem, parse_name(stem))


def test_the_provenance_tail_is_not_pinned():
    """WorldPop varies everything after the year. Pinning it is what
    broke this; only the four label fields are the contract."""
    for tail in ("_CN_100m_R2025A_v1", "_UN_1km_R2026B_UA_v3",
                 "_something_nobody_has_invented_yet", ""):
        d = parse_name("bdi_f_15_2026" + tail)
        assert d["_convention"] == "worldpop_r2025a", tail


def test_constrained_and_adjusted_of_the_same_cohort_collide(tmp_path):
    """They take the SAME label, so the overlap guard refuses them.

    That is correct - constrained and UN-adjusted are two estimates of
    the same people and must not be mixed in one run.
    """
    _tiny(tmp_path / "bdi_f_15_2026_CN_1km_R2025A_v1.tif", 30.0, -2.0,
          [[1., 2.], [3., 4.]])
    _tiny(tmp_path / "bdi_f_15_2026_CN_1km_R2025A_UA_v1.tif", 30.0, -2.0,
          [[5., 6.], [7., 8.]])
    with pytest.raises(ValueError, match="carry data in TWO rasters"):
        load_folder(tmp_path)


# ------------------------------------------------- the double count
def test_totals_alongside_their_parts_are_spotted():
    from equipop.rasterfolder import totals_overlap_parts
    labels = ["f_00_2026", "m_00_2026", "t_00_2026",
              "f_15_2026", "m_15_2026", "t_15_2026"]
    assert totals_overlap_parts(labels) == ["t_00_2026", "t_15_2026"]


def test_a_total_without_its_parts_is_not_a_clash():
    from equipop.rasterfolder import totals_overlap_parts
    assert totals_overlap_parts(["t_00_2026", "t_15_2026"]) == []
    assert totals_overlap_parts(["f_00_2026", "m_00_2026"]) == []


def test_summing_a_folder_that_holds_totals_AND_parts_is_refused(tmp_path):
    """John's folder: f + m + t. Summing would count everybody twice.

    Measured from his log - bdi age 00: f 224,972 + m 229,148 =
    454,120, and t is exactly 454,120.
    """
    for sex, vals in (("f", [[1., 2.], [3., 4.]]),
                      ("m", [[5., 6.], [7., 8.]]),
                      ("t", [[6., 8.], [10., 12.]])):
        _tiny(tmp_path / f"bdi_{sex}_00_2026_CN_1km_R2025A_UA_v1.tif",
              30.0, -2.0, vals)
    # loading is fine - they are three honest columns
    pts, _ = load_folder(tmp_path)
    assert {"f_00_2026", "m_00_2026", "t_00_2026"} <= set(pts.columns)
    # adding them together is not
    with pytest.raises(ValueError, match="TOTALS as well as their parts"):
        load_folder(tmp_path, sum_cohorts=True)


def test_summing_is_fine_when_only_the_parts_are_present(tmp_path):
    for sex, vals in (("f", [[1., 2.], [3., 4.]]),
                      ("m", [[5., 6.], [7., 8.]])):
        _tiny(tmp_path / f"bdi_{sex}_00_2026_CN_1km_R2025A_UA_v1.tif",
              30.0, -2.0, vals)
    pts, _ = load_folder(tmp_path, sum_cohorts=True)
    assert list(pts.columns) == ["lon", "lat", "iso3", "pop"]
    assert pts["pop"].sum() == pytest.approx(36.0)


# ---------------------------------------------------------------------
# BACKLOG 215, John: "the iso/country identifier should be ROW and not
# column ... since the user can choose to load one country or load
# several to treat as one geography (Iso can then be a matter for
# selection in Q and eventually Pro)".
#
# Countries were ALREADY rows - that part was right. But the country
# did not survive to the point table at all, so it could not be
# selected on. It is well defined per point because countries share no
# data pixel.
# ---------------------------------------------------------------------
def test_every_point_carries_the_country_it_came_from(loaded):
    pts, man = loaded
    assert "iso3" in pts.columns
    assert pts["iso3"].astype(str).ne("").all(), "a point with no country"
    assert set(pts["iso3"].astype(str)) == {"bdi", "rwa", "dnk"}


def test_the_country_counts_match_the_files(loaded):
    pts, man = loaded
    per_file = {f["iso3"]: f["pixels"] for f in man["files"].values()}
    got = pts.groupby("iso3", observed=True).size().to_dict()
    assert {str(k): v for k, v in got.items()} == per_file


def test_the_country_is_a_LABEL_and_never_a_population_column(loaded):
    """Everything that walks the columns must skip it - the keep-zero
    filter tried to SUM it and raised TypeError before this was fixed.
    """
    pts, _ = loaded
    from equipop.rasterfolder import folder_to_cells
    # a single cohort plus iso3 must still count as ONE value column,
    # so no weight has to be named
    cd, man = folder_to_cells(FIX, unit_size=1000.0, epsg=32735)
    assert man["weight_column"] == "f_15_2020"


def test_iso3_costs_almost_nothing(loaded):
    """Categorical, because a continental run is tens of millions of
    rows and a plain string column would be hundreds of megabytes."""
    import pandas as pd
    pts, _ = loaded
    assert isinstance(pts["iso3"].dtype, pd.CategoricalDtype)


def test_summing_cohorts_keeps_the_country():
    pts, _ = load_folder(FIX, sum_cohorts=True)
    assert list(pts.columns) == ["lon", "lat", "iso3", "pop"]


def test_keep_zero_still_works_with_a_label_column():
    a, _ = load_folder(FIX)
    b, _ = load_folder(FIX, keep_zero=True)
    assert len(b) >= len(a)
    assert "iso3" in b.columns


# ---------------------------------------------------------------------
# BACKLOG 225 - the analysis grid beating against the source lattice.
# John mapped Dist_k at k=1000, 2000 and 4000 and every one carried
# regular stripes. WorldPop "1 km" is 30 arc-seconds, which at 2 S is
# 927 m, not 1000. Binning that onto a 1000 m grid gives most cells ONE
# source pixel and every ~13th TWO - twice the population - and Dist_k
# is driven by density, so the doubles band across a continent.
# Neither a data fault nor an arithmetic one: the re-binning.
# ---------------------------------------------------------------------
def _lattice_points(deg=1/120, lat=-2.0, n=300):
    lon = 30.0 + np.arange(n) * deg
    return pd.DataFrame({"lon": np.tile(lon, 2),
                         "lat": np.repeat([lat, lat - 0.01], n)})


def _warned(unit, **kw):
    from equipop.rasterfolder import _warn_aliasing
    import contextlib
    import io
    b = io.StringIO()
    with contextlib.redirect_stdout(b):
        _warn_aliasing(_lattice_points(**kw), unit)
    return b.getvalue()


def test_the_case_that_striped_johns_maps_is_warned_about():
    got = _warned(1000.0)
    assert "WARNING" in got
    assert "927 m" in got, "name the source spacing so it can be acted on"
    assert "REGULAR BANDS" in got
    assert "km" in got, "give the beat period - it is what he SAW"


def test_the_advice_names_a_cell_size_that_works():
    got = _warned(1000.0)
    assert "or less" in got and "927" in got


@pytest.mark.parametrize("unit", [100.0, 500.0, 927.0])
def test_a_grid_at_or_below_the_source_is_quiet(unit):
    """No merging happens, so there is nothing to alias."""
    assert _warned(unit) == ""


def test_a_much_coarser_grid_is_quiet():
    """10 or 11 sources per cell is a 10% swing - not visible."""
    assert _warned(5000.0) == ""


def test_an_exact_multiple_is_quiet():
    """A whole number of sources per cell cannot alternate."""
    src = 1 / 120 * np.pi / 180 * 6378137.0 * np.cos(np.radians(-2.0))
    assert _warned(round(src * 3, 3)) == ""


def test_the_warning_survives_a_single_point():
    from equipop.rasterfolder import _warn_aliasing
    import contextlib
    import io
    b = io.StringIO()
    with contextlib.redirect_stdout(b):
        _warn_aliasing(pd.DataFrame({"lon": [30.0], "lat": [-2.0]}), 1000.0)
    assert b.getvalue() == "", "one point has no spacing to measure"


# ---------------------------------------------------------------------
# BACKLOG 239 - RELEASE BLOCKER, found by the external review of 1.43.
#
# The lattice check compares pixel size and origin. Both are PURE
# NUMBERS and say nothing about which world those numbers describe.
# Two rasters whose transforms agree numerically were merged as if they
# occupied the same ground - and the manifest then reported ONE crs, so
# the run's own provenance record hid it.
#
# 30.0 in EPSG:4326 is a longitude in Burundi. 30.0 in EPSG:3857 is
# thirty METRES from Greenwich. About 3,300 km apart, stacked into one
# cell, silently.
# ---------------------------------------------------------------------
def _one(tmp, name, crs, off=0.0, px=1.0 / 1200):
    import rasterio
    from rasterio.transform import from_origin
    with rasterio.open(str(tmp / (name + ".tif")), "w", driver="GTiff",
                       height=10, width=10, count=1, dtype="float32",
                       crs=crs, nodata=-99999.0,
                       transform=from_origin(30.0 + off, -2.0 + 10 * px,
                                             px, px)) as o:
        o.write(np.full((10, 10), 5.0, dtype="float32"), 1)


def test_two_crs_in_one_folder_are_refused(tmp_path):
    _one(tmp_path, "bdi_f_15_2026_CN_1km_R2025A_UA_v1", "EPSG:4326")
    _one(tmp_path, "bdi_m_15_2026_CN_1km_R2025A_UA_v1", "EPSG:3857", 0.05)
    with pytest.raises(ValueError, match="DIFFERENT WORLDS"):
        load_folder(tmp_path)


def test_the_refusal_names_BOTH_files_and_BOTH_systems(tmp_path):
    """A user with 120 rasters needs to know WHICH one is the odd
    one out, and what it is against."""
    _one(tmp_path, "bdi_f_15_2026_CN_1km_R2025A_UA_v1", "EPSG:4326")
    _one(tmp_path, "bdi_m_15_2026_CN_1km_R2025A_UA_v1", "EPSG:3857", 0.05)
    with pytest.raises(ValueError) as e:
        load_folder(tmp_path)
    msg = str(e.value)
    assert "bdi_m_15_2026" in msg and "bdi_f_15_2026" in msg
    assert "EPSG:3857" in msg and "EPSG:4326" in msg
    assert "Reproject" in msg, "say what to do, not only what is wrong"


def test_the_check_fires_BEFORE_the_lattice_check(tmp_path):
    """A different CRS AND a different pixel size must report the CRS.

    Pixel size is the symptom; the coordinate system is the cause, and
    a user told only about pixel size will resample and make it worse.
    """
    _one(tmp_path, "bdi_f_15_2026_CN_1km_R2025A_UA_v1", "EPSG:4326")
    _one(tmp_path, "bdi_m_15_2026_CN_1km_R2025A_UA_v1", "EPSG:3857",
         0.05, px=1.0 / 600)
    with pytest.raises(ValueError, match="DIFFERENT WORLDS"):
        load_folder(tmp_path)


def test_one_crs_throughout_still_loads(tmp_path):
    _one(tmp_path, "bdi_f_15_2026_CN_1km_R2025A_UA_v1", "EPSG:4326")
    _one(tmp_path, "bdi_m_15_2026_CN_1km_R2025A_UA_v1", "EPSG:4326", 0.05)
    pts, man = load_folder(tmp_path)
    assert len(pts) == 200
    assert man["crs"] == "EPSG:4326"


def test_a_projected_folder_is_fine_as_long_as_it_agrees(tmp_path):
    """The rule is CONSISTENCY, not geographic coordinates."""
    _one(tmp_path, "bdi_f_15_2026_CN_1km_R2025A_UA_v1", "EPSG:32735")
    _one(tmp_path, "bdi_m_15_2026_CN_1km_R2025A_UA_v1", "EPSG:32735", 0.05)
    pts, man = load_folder(tmp_path)
    assert man["crs"] == "EPSG:32735"
