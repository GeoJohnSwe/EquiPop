# -*- coding: utf-8 -*-
"""The raster-and-demography review, 1.53.0 - BACKLOG 353-366.

John asked, with the February exposome deadline in view, for "the
easiest fruits to pick, alternatively the best weeds" in the
demographic machinery and the raster integration. Candidates came from
two subagent reads; EVERY ONE GUARDED HERE WAS REPRODUCED FIRST, on
the real fixture, before a line was changed. The unverified remainder
was deliberately not acted on.

Two parts, and the first is the one with the deadline behind it:

  353  rasterfolder: `arr > 0` made "nobody lives here" the same as
       "this is the sea", and discarded every negative value. One
       pair of lines, three defects: keep_zero was dead, signed
       exposure surfaces lost their sign, and cells.py's own
       negative-weight refusal was unreachable from this path.
  354  the "which columns are measurements" rule, written FOUR times
  355  a float year matched no label: machine 3 silently summed every
       year, machine 4 blamed the filenames
  356  a group equal to the weight column reported a share of 327%
  357  `pattern=` leaked into module-global state for the session
  358  a year the data lacks blamed the user's naming convention
  359  'fmt:' double counted - John's ruling: refuse it
  360  a two-range side reported as one contiguous range
  361  a folder missing one sex passed unflagged
  362  age bands above 90 dropped in silence
  364  a tiled machine-4 run did all the work, then died

Each test's docstring names what it was BROKEN WITH, and each was
actually broken that way.
"""
import io
import os
import shutil
import tempfile
from contextlib import redirect_stdout

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, "tests", "fixtures", "worldpop")

rasterio = pytest.importorskip("rasterio")

from equipop.rasterfolder import (CONVENTIONS, load_folder,  # noqa: E402
                                  folder_to_cells,
                                  measurement_columns, normalise_year,
                                  parse_name)


def _hush(fn, *a, **kw):
    buf = io.StringIO()
    with redirect_stdout(buf):
        out = fn(*a, **kw)
    return out, buf.getvalue()


def _vals(frame):
    cols = [c for c in frame.columns if c not in ("lon", "lat", "iso3")]
    return frame[cols].to_numpy(dtype=float)


@pytest.fixture
def one_raster():
    """The fixture's profile and array, for building test folders."""
    p = os.path.join(FIX, "bdi_f_15_2020_CN_100m_R2025A_v1.tif")
    with rasterio.open(p) as r:
        return r.read(1).astype("float64"), dict(r.profile)


def _folder(prof, named):
    """A temp folder of {filename: array}."""
    d = tempfile.mkdtemp()
    for name, arr in named.items():
        with rasterio.open(os.path.join(d, name), "w", **prof) as w:
            w.write(arr.astype(prof["dtype"]), 1)
    return d


# =====================================================================
# 353 - WHICH PIXELS ARE DATA
# =====================================================================

def test_353_the_default_selection_is_bit_identical():
    """BROKEN WITH: making the default `observed` instead of
    `observed & (arr != 0)`.

    THE SAFETY ARGUMENT FOR THE WHOLE CHANGE, and it is checked against
    the OLD TWO LINES recomputed here from the files rather than
    against a stored number, so it cannot drift with the code it
    guards. Every published raster result came through `arr > 0`.

    THE BREAK-CHECK FOUND SOMETHING WORTH KEEPING: breaking `pick`
    alone does NOT fail this, because the keep_zero=False row filter
    further down catches the extra rows, and breaking the filter alone
    does not fail it either, because `pick` never let them in. The
    identity has TWO independent gates and it takes both to lose it.
    That is defence in depth rather than a gap in the test - but it is
    the kind of thing a later session should know before assuming one
    of the two is redundant and deleting it.
    """
    pts, _ = _hush(load_folder, FIX)
    pts = pts[0]
    px_old, tot_old = 0, 0.0
    for f in sorted(os.listdir(FIX)):
        with rasterio.open(os.path.join(FIX, f)) as r:
            a = r.read(1).astype("float64")
            nod = r.nodata
        a = np.where(np.isfinite(a) & (a != nod), a, 0.0)
        m = a > 0
        px_old += int(m.sum())
        tot_old += float(a[m].sum())
    assert len(pts) == px_old
    assert float(_vals(pts).sum()) == pytest.approx(tot_old, abs=1e-9)


def test_353_keep_zero_keeps_the_places_that_emptied():
    """BROKEN WITH: `pick = observed & (arr != 0.0)` unconditionally,
    i.e. ignoring keep_zero - which is what the code did before.

    John's case, and his own rule from 1.22.2: "if we have an instance
    where we used to have populations some years ago, and we want to
    compare how these places are doing now - we should have zeros in
    the deck. Then they add nothing to reference or treatment but they
    hold a place for results."

    Both branches used to be DEAD. A pixel zero everywhere was never
    created, so keep_zero=True could not bring it back; and every row
    that existed had a positive value, so keep_zero=False dropped
    nothing. The option was documented as working and exposed at the
    continental door. dnk_f_15_2020 carries 1,201 observed zeros.
    """
    a, _ = _hush(load_folder, FIX)
    b, _ = _hush(load_folder, FIX, keep_zero=True)
    a, b = a[0], b[0]
    assert len(b) > len(a), "keep_zero still does nothing"
    added = len(b) - len(a)
    allzero = int((_vals(b) == 0).all(axis=1).sum())
    assert allzero == added, \
        "the extra rows are not the all-zero ones"
    # they hold a slot and contribute nothing
    assert _vals(b).sum() == pytest.approx(_vals(a).sum())


def test_353_nodata_is_not_a_zero(one_raster):
    """BROKEN WITH: `observed = np.isfinite(arr)` alone, dropping the
    `arr != nod` term.

    The distinction is IN THE FILE - WorldPop ships nodata=-99999.0 -
    and line 284 used to destroy it by turning NoData into 0.0 before
    anything could look. If NoData became a kept zero, keep_zero would
    return the whole bounding box: for the fixture that is 874,800
    rows against 268,833 observed, most of them sea.
    """
    arr, prof = one_raster
    nod = prof["nodata"]
    assert nod is not None, "the fixture lost its nodata tag"
    d = _folder(prof, {"bdi_f_15_2020_CN_100m_R2025A_v1.tif": arr})
    try:
        pts, _ = _hush(load_folder, d, keep_zero=True)
        observed = int((np.isfinite(arr) & (arr != nod)).sum())
        assert len(pts[0]) == observed
        assert len(pts[0]) < arr.size, \
            "NoData was kept - the whole bounding box came back"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_353_a_signed_surface_keeps_its_sign(one_raster):
    """BROKEN WITH: `pick = observed & (arr > 0.0)`.

    THE FINDING THAT MATTERS FOR THE EXPOSOME CASE. PROPOSALS.md said
    climate rasters through machine 3 might need "nothing new"; this is
    what it needed. Measured before the fix on a temperature-anomaly
    field: a true mean of -0.0046 degC came back as +1.19, because
    every cooling pixel was discarded, and nothing said so. A
    zero-floored PM2.5 surface came back 9.9% high for the same reason.
    """
    _, prof = one_raster
    prof = dict(prof, dtype="float32", nodata=None)
    rng = np.random.default_rng(1)
    anom = rng.normal(0.0, 1.5, (prof["height"], prof["width"]))
    d = _folder(prof, {"bdi_f_15_2020_CN_100m_R2025A_v1.tif": anom})
    try:
        (pts, _), log = _hush(load_folder, d, keep_zero=True)
        assert len(pts) == anom.size, "pixels were dropped"
        assert pts["f_15_2020"].mean() == pytest.approx(anom.mean(),
                                                        abs=1e-4)
        assert pts["f_15_2020"].min() < 0, "the negatives are gone"
        assert "negative values" in log, \
            "a signed raster passed without a word - silence here is " \
            "what let the sign flip go unnoticed"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_353_an_undeclared_sentinel_now_reaches_the_refusal(one_raster):
    """BROKEN WITH: the same.

    cells.py's negative-weight guard says, in its own comment, that it
    exists because "rasterfolder hands a raster's own column straight
    in, and a raster's NoData is frequently -9999". It could never fire
    on this path, because the negatives were dropped before
    build_cells saw them. The guard and the hole were forty lines apart
    in one package.
    """
    _, prof = one_raster
    prof = dict(prof, dtype="float32", nodata=None)
    arr = np.full((prof["height"], prof["width"]), -9999.0)
    arr[:50, :50] = 7.0
    d = _folder(prof, {"bdi_f_15_2020_CN_100m_R2025A_v1.tif": arr})
    try:
        with pytest.raises(ValueError, match="cannot be negative|"
                                            "cannot be grown"):
            _hush(folder_to_cells, d, unit_size=1000.0, epsg=32735,
                  weight="f_15_2020")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_353_the_row_filter_does_not_eat_a_negative_row(one_raster):
    """BROKEN WITH: restoring `pts[vals].sum(axis=1) > 0` as the
    keep_zero=False filter.

    THE TWO CHANGES INTERACT, and fixing only the first would have
    been undone eight lines later. That filter dropped rows whose
    measures SUM to zero or less - which for a headcount is "zero
    everywhere" and for a signed surface is not: a pixel holding a
    single -1.2 degC anomaly sums negative and was deleted immediately
    after being rescued. The docstring always said "zero in EVERY
    layer", so that is what it now asks.
    """
    _, prof = one_raster
    prof = dict(prof, dtype="float32", nodata=None)
    h, w = prof["height"], prof["width"]
    arr = np.full((h, w), -1.2)          # every pixel negative
    d = _folder(prof, {"bdi_f_15_2020_CN_100m_R2025A_v1.tif": arr})
    try:
        pts, _ = _hush(load_folder, d)   # keep_zero=False, the default
        assert len(pts[0]) == arr.size, \
            "the default filter deleted rows that are not zero"
    finally:
        shutil.rmtree(d, ignore_errors=True)


# =====================================================================
# 354 - ONE RULE FOR WHAT A MEASUREMENT IS
# =====================================================================

def test_354_compose_is_not_counted_twice():
    """BROKEN WITH: `measurement_columns(pts)` without `derived=` at
    the sum_cohorts site.

    A composed column is a SUM OF OTHER COLUMNS, so it is a
    measurement to a reader and must never enter a total. Measured
    before the fix at exactly 2.0000x, with the composed column not
    even visible in the output. John's documented use is
    compose={"under5": [...]} with sum_cohorts=True, which counted
    every child under five twice.
    """
    base, _ = _hush(load_folder, FIX)
    truth = float(base[0]["f_15_2020"].sum())
    got, _ = _hush(load_folder, FIX, compose={"copy": ["f_15_2020"]},
                   sum_cohorts=True)
    assert float(got[0]["pop"].sum()) == pytest.approx(truth)


def test_354_compose_is_not_prefix_matched_into_the_weight():
    """BROKEN WITH: the same, at the `value_cols` site in
    folder_to_cells.

    THE SAME DEFECT THROUGH A SECOND PATH, which is why one shared
    helper was the fix rather than one patched line: weight='sexes'
    sums every column starting f_ or m_, and "f_copy".startswith("f_")
    is True. Measured at 182,509 people against a true 91,255.
    """
    cd, _ = _hush(folder_to_cells, FIX, unit_size=1000.0, epsg=32735,
                  weight="sexes")
    plain = float(np.asarray(cd[0].n, float).sum())
    cd2, _ = _hush(folder_to_cells, FIX, unit_size=1000.0, epsg=32735,
                   compose={"f_copy": ["f_15_2020"]}, weight="sexes")
    assert float(np.asarray(cd2[0].n, float).sum()) == \
        pytest.approx(plain)


def test_354_keep_index_does_not_turn_grid_indices_into_people():
    """BROKEN WITH: restoring `[c for c in pts.columns if c not in
    ("lon","lat","iso3")]` in folder_to_cells.

    THE FOURTH COPY, in the one function that INFERS THE WEIGHT - so
    the copy nobody updated was the copy that decides whether a run
    happens at all. A single-cohort folder that loads fine became
    un-runnable with keep_index=True: "this folder holds 3 population
    columns", two of them gx and gy, presented to the user as people.
    """
    cd, _ = _hush(folder_to_cells, FIX, unit_size=1000.0, epsg=32735,
                  keep_index=True)
    assert len(cd[0]) > 0


def test_354_the_rule_exists_once():
    """BROKEN WITH: pasting any of the four copies back.

    The comment above the old code said "decided ONCE" and sat above
    three copies; by 1.52 there were four. An exclusion list is a
    promise about every column that will ever exist, and it cannot be
    kept by copying it.
    """
    import re
    src = open(os.path.join(ROOT, "equipop", "rasterfolder.py"),
               encoding="utf-8").read()
    copies = re.findall(r"c not in \(\"lon\", \"lat\", \"iso3\"",
                        src)
    assert not copies, f"{len(copies)} open-coded copies are back"
    assert src.count("NOT_MEASUREMENTS = (") == 1
    # and the helper is what the module actually uses
    assert src.count("measurement_columns(") >= 4


def test_354_a_derived_column_still_reaches_the_output():
    """BROKEN WITH: excluding `derived` at the output-columns site.

    The other half of the rule: a composed column must stay OUT of
    totals and IN the table, because the user asked for it.
    """
    got, _ = _hush(load_folder, FIX, compose={"copy": ["f_15_2020"]})
    assert "copy" in got[0].columns


# =====================================================================
# 355, 358 - THE YEAR
# =====================================================================

@pytest.mark.parametrize("year", [2020, "2020", 2020.0, "2020.0"])
def test_355_every_spelling_of_a_year_means_the_same_year(year, one_raster):
    """BROKEN WITH: comparing against `str(year)` instead of
    normalise_year(year).

    A label's year is text. `str(2020.0)` is "2020.0", which no label
    equals - so machine 3 fell through to KEEPING EVERY YEAR, with no
    message, and the reference population doubled: 29,685 people
    became 59,369. That is BACKLOG 273's defect reachable by passing a
    float, which is what a spin box, a pandas value or read_csv hands
    over.
    """
    arr, prof = one_raster
    d = _folder(prof, {
        "bdi_f_15_2020_CN_100m_R2025A_v1.tif": arr,
        "bdi_f_15_2030_CN_100m_R2025A_v1.tif": arr})
    try:
        cd, log = _hush(folder_to_cells, d, unit_size=1000.0,
                        epsg=32735, weight="sexes", year=year)
        people = float(np.asarray(cd[0].n, float).sum())
        both, _ = _hush(folder_to_cells, d, unit_size=1000.0,
                        epsg=32735, weight="sexes")
        assert people == pytest.approx(float(
            np.asarray(both[0].n, float).sum()) / 2.0), \
            f"year={year!r} did not confine the reference population"
        assert "confined to" in log
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_355_a_fractional_year_is_refused_not_truncated():
    """BROKEN WITH: `int(float(year))` without the equality check.

    2020.5 is not a typo it is safe to guess at.
    """
    assert normalise_year(2020.0) == "2020"
    assert normalise_year("2020") == "2020"
    assert normalise_year(None) is None
    with pytest.raises(ValueError, match="not a whole year"):
        normalise_year(2020.5)


def test_355_a_year_the_folder_lacks_is_an_error(one_raster):
    """BROKEN WITH: restoring `if same_year:` - the silent fallback.

    Asking for a year that is not there was answered by summing EVERY
    year. That is a different question, and answering it quietly is
    the non-reproducibility 273 was raised about.
    """
    arr, prof = one_raster
    d = _folder(prof, {"bdi_f_15_2020_CN_100m_R2025A_v1.tif": arr})
    try:
        with pytest.raises(ValueError, match="year 2030"):
            _hush(folder_to_cells, d, unit_size=1000.0, epsg=32735,
                  weight="sexes", year=2030)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_358_machine_4_blames_the_year_and_not_the_filenames():
    """BROKEN WITH: removing the `year not in yrs` check from plan().

    The check only ran when `year is None`, so asking for 2030 on a
    2020 folder fell through to pick_sex, found nothing, and raised
    "No columns here look like a cohort ... Machine 4 needs labels of
    the form sex_age_year" - about labels that are perfectly well
    formed. It sent the user to check their naming convention instead
    of their year box, and `years_in` had the right answer six lines
    above.
    """
    from equipop.doors import demography as demo
    labels = [f"{s}_{a:02d}_2020" for s in ("f", "m")
              for a in demo.BAND_STARTS]
    with pytest.raises(demo.DemographyError) as e:
        demo.plan("ageing_index", labels, year=2030)
    msg = str(e.value)
    assert "2030" in msg and "2020" in msg
    assert "look like a cohort" not in msg
    assert "labels themselves are fine" in msg


# =====================================================================
# 356 - A GROUP THAT IS THE POPULATION
# =====================================================================

def test_356_a_group_equal_to_the_weight_is_a_share_of_one():
    """BROKEN WITH: restoring `if gname in pts.columns and gname !=
    weight`, which skipped the conversion.

    The guard was there to avoid dividing a column by itself, but the
    correct value in that case is a share of 1.0 - the group IS the
    population - not the raw headcount. Left raw, build_cells computes
    sum(v * w), the SUM OF SQUARES of the population, and the reported
    share came out between 0.0002 and 3.27 where the truth is 1.0
    everywhere. A share of 327% is not a number anybody reads as a
    loader bug.
    """
    cd, _ = _hush(folder_to_cells, FIX, unit_size=1000.0, epsg=32735,
                  groups=["f_15_2020"])
    cd = cd[0]
    n = np.asarray(cd.n, float)
    ok = n > 0
    share = cd.binary_sums["f_15_2020"][ok] / n[ok]
    assert share == pytest.approx(np.ones(int(ok.sum())))


def test_356_a_group_the_folder_lacks_is_named():
    """BROKEN WITH: restoring the silent `if gname in pts.columns`
    skip.

    A group that is not a column was skipped here and then met
    build_cells' `pd.to_numeric(df[c])`, which raises a bare KeyError
    naming nothing the user chose.
    """
    with pytest.raises(ValueError, match="groups names"):
        _hush(folder_to_cells, FIX, unit_size=1000.0, epsg=32735,
              groups=["f_99_1999"])


# =====================================================================
# 357 - THE PATTERN THAT OUTLIVED ITS CALL
# =====================================================================

def test_357_a_pattern_does_not_outlive_its_call():
    """BROKEN WITH: `CONVENTIONS["_user"] = pattern`, the original.

    The registry is module-global and `_user` was never removed, so in
    QGIS, Pro or Stata's embedded Python - where the interpreter
    outlives the run - a second load_folder on a DIFFERENT folder got
    its labels from the first call's regex, and the answer depended on
    call history. Verified before the fix: after one patterned load,
    parse_name('zzz_whatever') with no arguments returned
    {'sex': 'zzz', '_convention': '_user'}. It leaked between tests in
    one session too.
    """
    before = sorted(CONVENTIONS)
    _hush(load_folder, FIX, pattern=r"^(?P<sex>[a-z]{3}).*$")
    assert sorted(CONVENTIONS) == before, "the registry was mutated"
    assert parse_name("zzz_whatever")["_convention"] is None


def test_357_a_pattern_is_tried_before_the_registry_not_instead_of_it():
    """BROKEN WITH: making `convention` exclusive again, as the old
    `parse_name(stem, "_user" if pattern else convention)` did.

    load_folder's docstring has always promised "tried before the
    registry". The code made it exclusive, so giving a pattern for ONE
    oddly-named file silently turned WorldPop parsing off for the
    other 119 - every iso3 gone, every label changed.
    """
    # a pattern that matches nothing must leave the registry working
    d = parse_name("bdi_f_15_2020_CN_100m_R2025A_v1",
                   pattern=r"^NEVER_MATCHES_(?P<sex>x)$")
    assert d["_convention"] == "worldpop_r2025a"
    assert d["sex"] == "f"
    # and one that matches wins
    d2 = parse_name("odd_name", pattern=r"^(?P<sex>[a-z]+)_name$")
    assert d2["_convention"] == "_pattern" and d2["sex"] == "odd"


def test_357_an_unknown_convention_does_not_raise():
    """BROKEN WITH: `re.match(CONVENTIONS[nm], stem)` on a name that is
    not in the registry.

    parse_name's docstring says "Never raises; degrades to the stem",
    and `convention="worldpop_2026"` raised a bare KeyError.
    """
    d = parse_name("bdi_f_15_2020_CN_100m_R2025A_v1",
                   convention="worldpop_2026")
    assert d["_convention"] is None
    assert d.get("_unknown_convention") == "worldpop_2026"


# =====================================================================
# 359, 360, 361, 362, 364 - MACHINE 4
# =====================================================================

from equipop.doors import demography as demo                 # noqa: E402


def _labels(sexes, bands, year="2020"):
    return [f"{s}_{b:02d}_{year}" for s in sexes for b in bands]


_ALL = sorted(set(demo.expected_bands(
    demo.INDICES["dependency_ratio"]["numerator"]))
    | set(demo.expected_bands(
        demo.INDICES["dependency_ratio"]["denominator"])))


def test_359_t_with_f_or_m_is_refused():
    """BROKEN WITH: removing the `"t" in head and {"f","m"} & set(head)`
    check from parse_spec.

    JOHN'S RULING: "fmt should not be accepted." 't' IS f+m, so naming
    it alongside either counts those people twice. The rule was
    written down at columns_for - "mixing it with either double
    counts" - and enforced nowhere: 'fmt:0-14,65-' was accepted, gave
    30 numerator columns where 'fm:' gives 20, and because t repeats
    f+m the SUM came out at about twice the truth. Nothing flagged it,
    because every sex carried every band so the completeness grid saw
    a perfect side. The error message even advertised multi-sex specs.
    """
    for bad in ("fmt:0-14", "ft:15-49", "tm:"):
        with pytest.raises(demo.DemographyError, match="counted"):
            demo.parse_spec(bad)


def test_359_t_alone_and_fm_together_are_still_fine():
    """BROKEN WITH: refusing any spec that mentions 't'.

    The other half of a good guard: no correct configuration may trip
    it. A t-only folder is ordinary, and 'fm:' is the normal way to
    ask for both sexes separately.
    """
    assert demo.parse_spec("t:0-14")["sexes"] == ("t",)
    assert demo.parse_spec("fm:0-14")["sexes"] == ("f", "m")
    assert demo.parse_spec("0-14")["sexes"] is None


def test_360_a_two_range_side_reports_both_ranges():
    """BROKEN WITH: restoring `if spec_side.get("plus"): hi = None` and
    the single-range return.

    The dependency numerator is "0-14 AND 65 and over". It was
    reported as ONE range, covers (0, None) - which reads as EVERY
    AGE, and every age is also its own denominator's range. A
    demographer reading the plan (it is attached to the manifest as
    man["plans"]) would conclude the two halves overlap. The columns
    selected were right; this was a reporting fault.
    """
    p = _hush(demo.plan, "dependency_ratio", _labels("fm", _ALL))[0]
    eff = p["effective"]["numerator"]
    assert "ranges" in eff and len(eff["ranges"]) == 2
    assert eff["ranges"][0]["covers"] == (0, 14)
    assert eff["ranges"][1]["covers"] == (65, None)


def test_360_a_dropped_boundary_in_either_half_is_not_exact():
    """BROKEN WITH: the same - forcing hi = None made `exact`
    unconditionally True whenever `plus` was set.

    That switched OFF the moved-boundary note for the one index that
    uses `plus`: asking for "0-17,65-" lost ages 15, 16 and 17 and
    still claimed to be exact.
    """
    p = _hush(demo.plan, "dependency_ratio", _labels("fm", _ALL),
              num_spec=demo.parse_spec("0-17,65-"))[0]
    eff = p["effective"]["numerator"]
    assert eff["exact"] is False, \
        "ages 15-17 were dropped and the plan called itself exact"
    assert eff["ranges"][0]["asked"] == (0, 17)
    assert eff["ranges"][0]["covers"] == (0, 14)
    # the untouched default is still exact
    q = _hush(demo.plan, "dependency_ratio", _labels("fm", _ALL))[0]
    assert q["effective"]["numerator"]["exact"] is True


def test_361_a_folder_missing_a_sex_records_it_without_refusing():
    """BROKEN WITH: putting the sex restriction into `gaps` instead of
    `noted` - which REFUSES the run.

    John's ruling on user-entered specs decides the remedy: compute
    and record, do not refuse. A women-only folder produced an "Ageing
    index" labelled "People 65 and over per person under 15" with
    restricted = None - nothing saying the denominator was girls. That
    is 1.45.4's defect surviving in the one dimension 346's grid
    cannot see, because the sexes a side "covers" is itself derived
    from what is present.
    """
    p = _hush(demo.plan, "ageing_index", _labels("f", _ALL))[0]
    assert p["sexes"] == ["f"]
    assert p["restricted"] == {"sexes": ["m"]}


def test_361_a_real_band_gap_still_refuses():
    """BROKEN WITH: routing the band gaps through `noted` too.

    346's refusal must survive 361. `noted` records; `gaps` refuses,
    and a band present for one sex and absent for the other is still a
    hole.
    """
    labels = _labels("fm", _ALL)
    labels.remove("m_65_2020")
    with pytest.raises(demo.DemographyError, match="under its own name"):
        demo.plan("ageing_index", labels)


def test_362_a_band_above_the_table_is_not_dropped_in_silence(capsys):
    """BROKEN WITH: removing the `elif age > BAND_STARTS[-1]` branch.

    BAND_STARTS stops at 90, where 90 means "90 and over" - true of
    WorldPop, not of every product. A folder carrying f_95 or f_100
    had those cohorts excluded from every index while weight='sexes'
    still counted them in the reference population, because that picks
    columns by the f_/m_ PREFIX alone. So the ageing index came out
    biased down by exactly the oldest cohorts, with restricted = None.
    What SHOULD happen to them is a demographic ruling and is John's -
    BACKLOG 363. What this fixes is the silence.
    """
    labels = _labels("fm", _ALL) + [f"{s}_{a}_2020"
                                    for s in ("f", "m")
                                    for a in (95, 100)]
    demo.plan("sex_ratio", labels)
    said = capsys.readouterr().out
    assert "95" in said and "100" in said
    assert "NOT in this index" in said
    assert "reference population" in said


def test_362_an_ordinary_folder_says_nothing(capsys):
    """BROKEN WITH: printing the note unconditionally.

    The other half: a WorldPop folder ends at 90 and must produce no
    such line, or the note becomes noise nobody reads.
    """
    demo.plan("sex_ratio", _labels("fm", _ALL))
    assert "above the 90+ band" not in capsys.readouterr().out


def test_364_a_tiled_machine_4_run_is_refused_before_the_work():
    """BROKEN WITH: removing the out_dir guard from run_index /
    run_indices.

    `out_dir` reaches run_folder through **kw, which sends machine 3
    down its TILED branch - and that branch sets man["tiles"], never
    man["results"]. So the rasters loaded, the cells were built, every
    neighbourhood was computed, the parquet tiles were written, and
    THEN this raised a bare KeyError: 'results', having never computed
    the index. Reproduced on a 40-raster folder: 2 tiles on disk,
    holding T_num_/T_den_ with no index column.

    A refusal after the expensive part is the one kind that costs the
    user something.
    """
    d = tempfile.mkdtemp()
    try:
        for fn in (demo.run_index, demo.run_indices):
            arg = "sex_ratio" if fn is demo.run_index else ["sex_ratio"]
            with pytest.raises(demo.DemographyError,
                               match="cannot be run TILED"):
                fn(FIX, arg, k_values=[50], unit_size=1000.0,
                   epsg=32735, out_dir=d)
        assert not [f for f in os.listdir(d) if f.endswith(".parquet")], \
            "it did the work before refusing"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_366_the_field_guide_states_the_units():
    """BROKEN WITH: dropping the PER ONE clause.

    John's ruling is to KEEP the bare ratio, so this changes no
    number - it says which number it is. Conventionally a sex ratio is
    men per 100 women and a child-woman ratio is children per 1,000,
    so a column reading 0.97 will be read as 1% by anyone expecting
    97. The `about` text implies per-one and never reaches the
    attribute table.
    """
    plans = {"sex_ratio": _hush(demo.plan, "sex_ratio",
                                _labels("fm", _ALL))[0]}
    lines = demo.explain_fields(["sex_200"], plans=plans)
    text = "\n".join(lines)
    assert "PER ONE" in text
    assert "per 100 or per 1,000" in text
