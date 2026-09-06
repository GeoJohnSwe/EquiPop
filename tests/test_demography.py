"""MACHINE 4 - demographic indices over k-neighbourhoods.

The arithmetic is machine 1's; what is new is that the groups are
named after demography. So most of what can go wrong here is CHOOSING
THE WRONG COLUMNS, and that is what these tests are about.

THE TRAP THROUGHOUT IS THAT WORLDPOP'S AGE BANDS ARE NOT ALL FIVE
YEARS (John): 0 is under-one alone, 1 covers 1-4, then fives, and 90
is open-ended. Any selector doing arithmetic on the age NUMBER rather
than working in band starts gets "15 to 49" wrong at both ends.
"""
from __future__ import annotations

import numpy as np
import pytest

from equipop.doors.demography import (
    BAND_STARTS, DemographyError, INDICES, columns_for, parse_spec,
    pick_sex, plan, run_indices, years_in)


def _labels(year=2026, sexes="fmt"):
    return [f"{s}_{a:02d}_{year}" for s in sexes for a in BAND_STARTS]


# ------------------------------------------------- the bands themselves
def test_the_child_woman_denominator_stops_at_49_not_54():
    """15-49 must give 15,20,...,45. Sliding into 50 would put women
    past childbearing age into the denominator and depress the ratio
    everywhere, plausibly."""
    got = plan("child_woman_ratio", _labels())
    ages = sorted(int(c.split("_")[1]) for c in got["denominator"])
    assert ages == [15, 20, 25, 30, 35, 40, 45], ages


def test_children_under_five_are_TWO_bands_not_one():
    """0 is under-one on its own and 1 covers 1-4. Taking only '0'
    would miss four fifths of the children."""
    got = plan("child_woman_ratio", _labels())
    ages = sorted({int(c.split("_")[1]) for c in got["numerator"]})
    assert ages == [0, 1], ages


def test_the_dependency_numerator_is_both_ends():
    got = plan("dependency_ratio", _labels())
    ages = sorted({int(c.split("_")[1]) for c in got["numerator"]})
    assert ages == [0, 1, 5, 10, 65, 70, 75, 80, 85, 90], ages


def test_the_dependency_denominator_stops_at_64():
    got = plan("dependency_ratio", _labels())
    ages = sorted({int(c.split("_")[1]) for c in got["denominator"]})
    assert ages == [15, 20, 25, 30, 35, 40, 45, 50, 55, 60], ages
    assert 65 not in ages, "65+ is a dependant, not a worker"


def test_the_open_band_is_included_where_it_belongs():
    """90+ has no last year. It must still count as 65-and-over."""
    got = plan("ageing_index", _labels())
    assert any(c.startswith(("f_90", "m_90", "t_90"))
               for c in got["numerator"])


def test_an_open_band_is_never_swept_into_a_closed_range():
    """15-64 must not collect 90+, which has no upper bound at all."""
    got = plan("dependency_ratio", _labels())
    assert not any("_90_" in c for c in got["denominator"])


# --------------------------------------------------- f, m and t again
def test_the_totals_are_not_used_when_the_parts_are_there():
    """t is exactly f+m - using all three counts everybody twice.

    John's own numbers: bdi age 00 has f 224,972 + m 229,148 and t
    454,120.
    """
    assert pick_sex(_labels(sexes="fmt")) == ("f", "m")
    got = plan("dependency_ratio", _labels(sexes="fmt"))
    assert not any(c.startswith("t_") for c in got["numerator"])
    assert not any(c.startswith("t_") for c in got["denominator"])


def test_the_totals_ARE_used_when_the_parts_are_absent():
    assert pick_sex(_labels(sexes="t")) == ("t",)
    got = plan("dependency_ratio", _labels(sexes="t"))
    assert all(c.startswith("t_") for c in got["numerator"])


def test_a_sex_specific_index_ignores_the_choice():
    """The child-woman denominator is women whatever else is present."""
    got = plan("child_woman_ratio", _labels(sexes="fmt"))
    assert all(c.startswith("f_") for c in got["denominator"])


def test_the_sex_ratio_is_men_over_women():
    got = plan("sex_ratio", _labels())
    assert all(c.startswith("m_") for c in got["numerator"])
    assert all(c.startswith("f_") for c in got["denominator"])


# ---------------------------------------------------------- refusals
def test_two_years_are_refused_rather_than_mixed():
    labs = _labels(2020) + _labels(2026)
    assert years_in(labs) == ["2020", "2026"]
    with pytest.raises(DemographyError, match="carry 2 years"):
        plan("child_woman_ratio", labs)


def test_naming_the_year_resolves_it():
    labs = _labels(2020) + _labels(2026)
    got = plan("child_woman_ratio", labs, year=2026)
    assert got["year"] == "2026"
    assert all(c.endswith("2026") for c in got["numerator"])


def test_an_unknown_index_lists_the_real_ones():
    with pytest.raises(DemographyError, match="No such index"):
        plan("total_fertility_rate", _labels())


def test_columns_that_are_not_cohorts_are_refused_in_plain_words():
    with pytest.raises(DemographyError, match="sex_age_year"):
        plan("child_woman_ratio", ["pop", "density", "iso3"])


def test_an_index_whose_ages_are_absent_says_which_it_wanted():
    """A folder of only working-age cohorts cannot give an ageing index."""
    labs = [f"f_{a}_2026" for a in (15, 20, 25, 30)]
    with pytest.raises(DemographyError, match="nothing to put on top"):
        plan("ageing_index", labs)


# ------------------------------------------------- what is NOT offered
@pytest.mark.parametrize("absent", ["total_fertility_rate", "asfr",
                                    "crude_birth_rate",
                                    "crude_death_rate",
                                    "life_expectancy"])
def test_rate_measures_are_deliberately_absent(absent):
    """They need VITAL EVENTS and an age-sex folder carries stock.

    Offering a dropdown entry called TFR that quietly computed
    something else would be worse than not offering it. If a births
    raster joins the folder it becomes an ordinary column and these
    open up - see BACKLOG 216, and its circularity note.
    """
    assert absent not in INDICES


def test_every_index_explains_itself():
    for name, spec in INDICES.items():
        assert spec["about"].strip(), name
        assert spec["label"].strip(), name


def test_the_plan_can_be_seen_before_anything_runs():
    """John: "suggested fields loaded, but with option to add/remove".

    A door has to be able to show the columns and let them be edited,
    so planning must be separable from running.
    """
    got = plan("child_woman_ratio", _labels())
    assert set(got) >= {"numerator", "denominator", "year", "label",
                        "about"}
    assert isinstance(got["numerator"], list)


# ---------------------------------------------------------------------
# END TO END, and the conversion that nearly went wrong.
#
# build_cells MULTIPLIES a group column by the weight, because a group
# is normally a 0/1 marker and the weight turns it into people. A
# COMPOSED group is already a headcount, so handing it over as it
# stands would have multiplied children by the total population - a
# number roughly 500x too large, and plausible-looking.
# ---------------------------------------------------------------------
import os                                                    # noqa: E402
import tempfile                                              # noqa: E402

import rasterio                                              # noqa: E402
from rasterio.transform import from_origin                   # noqa: E402

from equipop.doors.demography import run_index               # noqa: E402


@pytest.fixture(scope="module")
def pyramid_folder():
    """Two countries, a real-shaped age pyramid, fractional counts."""
    px = 1.0 / 1200
    d = tempfile.mkdtemp()
    rng = np.random.default_rng(7)
    shape = (60, 60)
    for iso, off in (("bdi", 0.0), ("rwa", 0.06)):
        for sex in ("f", "m"):
            for age in BAND_STARTS:
                a = (rng.random(shape)
                     * max(0.2, 3.0 - age / 30.0)).astype("float32")
                with rasterio.open(
                        os.path.join(d, f"{iso}_{sex}_{age:02d}_2026"
                                        "_CN_1km_R2025A_UA_v1.tif"),
                        "w", driver="GTiff", height=shape[0],
                        width=shape[1], count=1, dtype="float32",
                        crs="EPSG:4326", nodata=-99999.0,
                        transform=from_origin(30.0 + off,
                                              -2.0 + shape[0] * px,
                                              px, px)) as o:
                    o.write(a, 1)
    return d


def _run(folder, name="child_woman_ratio", k=500):
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return run_index(folder, name, k_values=[k], unit_size=1000.0,
                         epsg=32735)


def test_the_index_is_computed_and_named(pyramid_folder):
    man = _run(pyramid_folder)
    r = man["results"]
    assert "child_woman_ratio_500" in r.columns
    v = r["child_woman_ratio_500"].to_numpy(float)
    v = v[np.isfinite(v)]
    assert len(v) > 0 and (v > 0).all()


def test_the_index_is_exactly_the_two_counts_divided(pyramid_folder):
    r = _run(pyramid_folder)["results"]
    num = r["T_num_500"].to_numpy(float)
    den = r["T_den_500"].to_numpy(float)
    got = r["child_woman_ratio_500"].to_numpy(float)
    ok = np.isfinite(num) & np.isfinite(den) & (den > 0)
    assert np.allclose(num[ok] / den[ok], got[ok])


def test_the_halves_are_HEADCOUNTS_not_shares(pyramid_folder):
    """The conversion that nearly went wrong, in one assertion.

    A composed group arriving unconverted would be multiplied by the
    weight, giving a numerator hundreds of times too large. Both
    halves must be counts of people inside a 500-person
    neighbourhood, so both must sit strictly between 0 and k.
    """
    r = _run(pyramid_folder)["results"]
    for col in ("T_num_500", "T_den_500"):
        v = r[col].to_numpy(float)
        v = v[np.isfinite(v)]
        assert (v > 1).any(), f"{col} looks like a share, not a count"
        assert (v < 500).all(), (
            f"{col} exceeds k - the group was multiplied by the weight")


def test_the_neighbourhood_still_holds_exactly_k(pyramid_folder):
    r = _run(pyramid_folder)["results"]
    n = r["N_500"].to_numpy(float)
    assert np.allclose(n[np.isfinite(n)], 500.0)


def test_a_second_index_uses_the_same_machinery(pyramid_folder):
    r = _run(pyramid_folder, "dependency_ratio")["results"]
    v = r["dependency_ratio_500"].to_numpy(float)
    v = v[np.isfinite(v)]
    assert len(v) > 0 and (v > 0).all()


def test_the_plan_is_reported_before_the_arithmetic(pyramid_folder):
    class Ch:
        def __init__(self):
            self.lines = []

        def info(self, m):
            self.lines.append(str(m))

        def warning(self, m):
            self.lines.append(str(m))

    import contextlib
    import io
    ch = Ch()
    with contextlib.redirect_stdout(io.StringIO()):
        run_index(pyramid_folder, "child_woman_ratio", k_values=[500],
                  unit_size=1000.0, epsg=32735, channel=ch)
    said = " ".join(ch.lines)
    assert "on top" in said and "divided by" in said
    assert "f_15_2026" in said, "the user must see which columns were used"


# ---------------------------------------------------------------------
# BACKLOG 228, John: "we should allow for alterations of the
# measurement settings - please make it possible to accept or edit the
# measures (for instance the age settings)".
#
# Editing a measure by typing eleven column names is transcription,
# not editing. A half of an index can now be respecified in the terms
# it is thought about: which ages, and which sex.
# ---------------------------------------------------------------------
from equipop.doors.demography import parse_spec          # noqa: E402


@pytest.mark.parametrize("text,sexes,ages", [
    ("0-4", None, (0, 4)),
    ("f:15-49", ("f",), (15, 49)),
    ("65-", None, (65, None)),
    ("m:", ("m",), (0, None)),
    ("fm:20-39", ("f", "m"), (20, 39)),
    ("  f : 15 - 44 ", ("f",), (15, 44)),
])
def test_a_measure_can_be_written_the_way_it_is_spoken(text, sexes, ages):
    got = parse_spec(text)
    assert got["sexes"] == sexes and got["ages"] == ages


def test_blank_means_leave_the_measure_alone():
    assert parse_spec("") is None and parse_spec(None) is None


def test_the_edited_range_still_respects_the_irregular_bands():
    """15-44 must stop at band 40, not reach into 45-49."""
    got = plan("child_woman_ratio", _labels(),
               den_spec=parse_spec("f:15-44"))
    ages = sorted(int(c.split("_")[1]) for c in got["denominator"])
    assert ages == [15, 20, 25, 30, 35, 40], ages


def test_an_edit_can_change_the_sex_as_well_as_the_ages():
    got = plan("ageing_index", _labels(), num_spec=parse_spec("f:65-"))
    assert all(c.startswith("f_") for c in got["numerator"])


@pytest.mark.parametrize("bad,why", [
    ("15 to 49", "not an age range"),
    ("x:15-49", "not a sex"),
    ("49-15", "runs backwards"),
    ("a-b", "whole numbers"),
])
def test_a_malformed_measure_is_refused_by_name(bad, why):
    with pytest.raises(DemographyError, match=why):
        parse_spec(bad)


def test_the_refusal_shows_the_form_that_works():
    with pytest.raises(DemographyError) as e:
        parse_spec("fifteen to forty-nine")
    assert "'15-49'" in str(e.value)


# ---------------------------------------------------------------------
# BACKLOG 238. External review of 1.43: "a small Machine 4 age-setting
# parser defect affecting a combined-sex, two-range expression such as
# fm:0-14,65-".
#
# Correct. The recursion that re-parses each half rebuilt the sex
# prefix with '/'.join(sexes), producing 'f/m:0-14' - and '/' is not a
# sex, so the user was refused with a message naming a character they
# never typed. A comma range worked WITHOUT a sex and failed WITH one.
# ---------------------------------------------------------------------
@pytest.mark.parametrize("spec,sexes", [
    ("0-14,65-", None),
    ("f:0-14,65-", ("f",)),
    ("m:0-14,65-", ("m",)),
    ("fm:0-14,65-", ("f", "m")),
    ("t:0-14,65-", ("t",)),
])
def test_two_ranges_work_with_and_without_a_sex(spec, sexes):
    got = parse_spec(spec)
    assert got["sexes"] == sexes
    assert got["ages"] == (0, 14) and got["plus"] == (65, None)


def test_a_two_range_edit_selects_both_ends_of_the_pyramid():
    got = plan("dependency_ratio", _labels(),
               num_spec=parse_spec("fm:0-14,65-"))
    ages = sorted({int(c.split("_")[1]) for c in got["numerator"]})
    assert ages == [0, 1, 5, 10, 65, 70, 75, 80, 85, 90], ages


def test_a_refusal_never_names_a_character_the_user_did_not_type():
    """The shape of the defect, not just the instance. A message that
    quotes something absent from the input sends the reader hunting
    for a typo they did not make."""
    for spec in ("fm:0-14,65-", "f:0-4", "65-", "0-14,65-"):
        try:
            parse_spec(spec)
        except DemographyError as e:
            for ch in str(e):
                if ch in "'\"":
                    continue
            assert "/" not in str(e), (f"{spec}: {e}")


def test_three_ranges_are_refused_with_the_form_that_works():
    with pytest.raises(DemographyError, match="two separated by a comma"):
        parse_spec("0-4,15-49,65-")


# ---------------------------------------------------------------------
# BACKLOG 273 - A RESULT THAT DEPENDS ON WHICH OTHER FILES ARE PRESENT.
# External review of 1.44.10, reproduced here: the selected year
# filtered the numerator and denominator, but the REFERENCE POPULATION
# summed the f_ and m_ columns of EVERY year in the folder. So
# analysing 2020 changed once 2030 had also been downloaded - the
# neighbourhood was drawn through twice as many people.
#
# Measured before the fix: mean Dist 34.60 m against 24.37 m, a 30%
# change in the neighbourhood, with the selected year's data
# identical. The review's own run moved radii by up to 55 m.
#
# The review asks for this as a PERMANENT regression test, and it is
# right to: it is the only kind of defect that makes a published
# comparison wrong for a reason nobody can see in the output.
# ---------------------------------------------------------------------
def _silent():
    class _C:
        def info(self, *a): pass
        def warning(self, *a): pass
    return _C()


def _year_folder(tmp, years, n=10):
    import rasterio
    from rasterio.transform import from_origin
    px = 1.0 / 1200
    rng = np.random.default_rng(3)
    for y in years:
        for sex in "fm":
            for age in BAND_STARTS:
                a = (rng.random((n, n)) * 8 + 1).astype("float32")
                f = tmp / (f"bdi_{sex}_{age:02d}_{y}"
                           "_CN_1km_R2025A_UA_v1.tif")
                with rasterio.open(str(f), "w", driver="GTiff",
                                   height=n, width=n, count=1,
                                   dtype="float32", crs="EPSG:4326",
                                   nodata=-99999.0,
                                   transform=from_origin(
                                       30.0, -2.0 + n * px, px, px)) as o:
                    o.write(a, 1)
    return tmp


@pytest.mark.parametrize("index", ["sex_ratio", "ageing_index"])
def test_an_unrelated_year_leaves_this_years_answer_unchanged(
        tmp_path, index):
    rasterio = pytest.importorskip("rasterio")
    one = _year_folder(tmp_path / "one", [2020]) \
        if (tmp_path / "one").mkdir() is None else None
    two = _year_folder(tmp_path / "two", [2020, 2030]) \
        if (tmp_path / "two").mkdir() is None else None
    got = []
    for folder in (tmp_path / "one", tmp_path / "two"):
        man = run_indices(str(folder), [index], k_values=[100],
                          unit_size=100.0, year="2020", epsg=32735,
                          channel=_silent())
        r = man["results"]
        got.append((r["Dist_100"].mean(),
                    r[[c for c in r.columns
                       if c.startswith(INDICES[index]["code"])][0]].mean()))
    assert got[0][0] == pytest.approx(got[1][0], abs=1e-9), (
        "the neighbourhood changed because another year exists")
    assert got[0][1] == pytest.approx(got[1][1], abs=1e-9), (
        "the measure changed because another year exists")


def test_the_reference_population_says_when_it_confines_a_year(tmp_path):
    """Leaving columns out of the reference population is a decision
    the user must see, not a silent correction."""
    pytest.importorskip("rasterio")
    (tmp_path / "two").mkdir()
    _year_folder(tmp_path / "two", [2020, 2030])

    said = []

    class Ch:
        def info(self, m):
            said.append(str(m))

        def warning(self, m):
            said.append(str(m))

    run_indices(str(tmp_path / "two"), ["sex_ratio"], k_values=[100],
                unit_size=100.0, year="2020", epsg=32735, channel=Ch())
    assert any("confined to 2020" in s for s in said), said[-6:]
