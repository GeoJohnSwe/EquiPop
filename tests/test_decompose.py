# -*- coding: utf-8 -*-
"""test_decompose.py - MLD, Theil, and their between/within split.

v1.55.0, BACKLOG 405.

Every expected number here is either a LITERAL worked out by hand, or
an identity between two INDEPENDENT routes through the code - never
the same function asked twice. The central one: between + within,
assembled from each group's count, mean and index, must equal the
index the engine computes directly over everybody. Those share no
code below run_knn_stats.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
import io
import math
import contextlib

import numpy as np
import pytest

from equipop.stats import VALUE_STATS
from equipop.wstats import weighted_stat
from equipop.stata_bridge import dispatch


# exact arithmetic, worked by hand and written down
MLD_1_3 = 0.1438410362          # (ln 2 + ln 2/3) / 2
MLD_1_3_4_4 = 0.1308120359      # (ln 3 + 2 ln 3/4) / 4
THEIL_1_3 = 0.1308120359        # (0.5 ln 0.5 + 1.5 ln 1.5) / 2
THEIL_0_2_4 = 2 * math.log(2) / 3
# [1, 3] weighted [1, 3] is the sample [1, 3, 3, 3], mean 2.5
MLD_W = 0.0923315154            # (ln 2.5 + 3 ln 2.5/3) / 4
THEIL_W = 0.0724603279          # (0.4 ln 0.4 + 3 x 1.2 ln 1.2) / 4

ONE_CELL = dict(x=np.full(4, 50.0), y=np.full(4, 50.0))


def _quiet(fn, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        res = fn(*a, **kw)
    return res, out.getvalue()


def _stats(values, stats, **kw):
    """dispatch over one cell, so everyone is everyone's neighbour."""
    n = len(next(iter(values.values())))
    res, said = _quiet(dispatch, "stats", np.full(n, 50.0),
                       np.full(n, 50.0), unit_size=100, k_values=[n],
                       values=values, stats=stats, **kw)
    return res, said


# ------------------------------------------------------------ indices
@pytest.mark.parametrize("path", ["expanded", "weighted"])
def test_mld_and_theil_match_hand_arithmetic(path):
    """BROKEN WITH: ln(v / mean) for ln(mean / v) in the weighted MLD
    (the clamp then returns 0); dividing by the number of distinct
    values instead of the people (v.size for n); dropping the r > 0
    mask in Theil, so a zero contributes 0 * ln 0 = nan.

    THE WEIGHTED CASE IS WHAT MAKES THE SECOND CLAIM TRUE. With every
    weight 1 the number of distinct entries IS the number of people,
    so the break survived this test until 1.55.0's own break-check
    said so - the claim was written, and it was not yet true."""
    def f(s, y, w=None):
        y = np.asarray(y, float)
        if path == "expanded":
            return VALUE_STATS[s](y if w is None else np.repeat(y, w))
        return weighted_stat(s, y, np.ones(len(y)) if w is None else w)
    assert f("mld", [1, 3]) == pytest.approx(MLD_1_3, abs=1e-10)
    assert f("mld", [1, 3, 4, 4]) == pytest.approx(MLD_1_3_4_4, abs=1e-10)
    assert f("theil", [1, 3]) == pytest.approx(THEIL_1_3, abs=1e-10)
    assert f("theil", [0, 2, 4]) == pytest.approx(THEIL_0_2_4, abs=1e-12)
    assert f("mld", [1, 3], [1, 3]) == pytest.approx(MLD_W, abs=1e-10)
    assert f("theil", [1, 3], [1, 3]) == pytest.approx(THEIL_W, abs=1e-10)


def test_the_weighted_path_equals_the_expanded_one_for_whole_weights():
    """THE CONSTRAINT THAT MAKES THE WEIGHTED PATH SAFE, as for every
    other statistic since BACKLOG 118: for whole-number weights it
    returns what repeating each person returns.

    BROKEN WITH: np.mean(np.log(mean / v)) in the weighted path - the
    weights ignored, which agrees whenever every weight is 1 and no
    other time."""
    rng = np.random.default_rng(118)
    for _ in range(500):
        n = int(rng.integers(2, 25))
        v = rng.lognormal(5, 1, n).round(1)
        w = rng.integers(1, 7, n)
        for s in ("mld", "theil"):
            e = VALUE_STATS[s](np.repeat(v, w))
            q = weighted_stat(s, v, w)
            assert q == pytest.approx(e, rel=1e-10), (s, v, w)


def test_a_fraction_of_a_person_is_a_fraction_of_a_person():
    """A crossing ring contributes 0.4 of a cell; its terms must count
    0.4. Halving every weight changes nothing - only proportions
    matter - and weights 1 and 3 are the sample [1, 3, 3, 3].

    BROKEN WITH: weights rounded to whole people before use."""
    a = weighted_stat("mld", [1, 3], [1, 3])
    assert a == pytest.approx(VALUE_STATS["mld"](
        np.array([1.0, 3, 3, 3])), rel=1e-12)
    assert weighted_stat("mld", [1, 3], [0.5, 1.5]) == pytest.approx(
        a, rel=1e-12)
    assert weighted_stat("theil", [1, 3], [0.3, 0.9]) == pytest.approx(
        weighted_stat("theil", [1, 3], [1, 3]), rel=1e-12)


def test_one_distinct_value_has_no_inequality_exactly():
    """Fifty-five copies of one income have an MLD of ZERO, not of
    1e-17: the mean of 55 copies can miss the value in its last bit,
    and the log of that ratio is noise. BACKLOG 118 pinned the same
    for the SD.

    BROKEN WITH: the one-value early return removed from
    _weighted_ge - 0.1 x 55 at weight 0.3 then gives 1.1e-16."""
    v = np.full(55, 0.1)
    w = np.full(55, 0.3)
    for s in ("mld", "theil"):
        assert weighted_stat(s, v, w) == 0.0
        assert VALUE_STATS[s](np.full(55, 0.1)) == 0.0


# ---------------------------------------------------------- refusals
def test_mld_refuses_a_zero_and_names_theil():
    """John's question, measured: replacing zeros with a small number
    makes the number the answer and the unit of currency decisive. So
    a zero is refused, and the refusal names the measure that works.

    BROKEN WITH: the check_mld_input call removed from run_knn_stats
    (the zero then yields NaN everywhere, silently)."""
    with pytest.raises(ValueError, match="Theil instead"):
        _stats({"inc": np.array([0.0, 10, 20, 30])}, {"inc": ["mld"]})
    with pytest.raises(ValueError, match="zero or less"):
        _stats({"inc": np.array([-5.0, 10, 20, 30])}, {"inc": ["mld"]})


def test_theil_accepts_a_zero_and_refuses_a_negative():
    """BROKEN WITH: check_theil_input testing <= 0 rather than < 0."""
    res, _ = _stats({"inc": np.array([0.0, 2, 4])}, {"inc": ["theil"]})
    assert res["Theil_inc_3"][0] == pytest.approx(THEIL_0_2_4, abs=1e-12)
    with pytest.raises(ValueError, match="negative"):
        _stats({"inc": np.array([-1.0, 2, 4])}, {"inc": ["theil"]})


def test_a_zero_one_variable_is_the_share_in_disguise():
    """The answer to John's question about binary variables, pinned:
    for a 0/1 variable with share p, Theil is exactly -ln p and the
    Gini exactly 1 - p, and MLD is infinite. Each is a transform of
    the share - which is why the binary family does not offer them.

    BROKEN WITH: a Theil that gives a zero the term -ln(mean) instead
    of nothing."""
    for t, n in ((1, 4), (3, 10), (7, 10)):
        y = np.r_[np.ones(t), np.zeros(n - t)]
        p = t / n
        assert weighted_stat("theil", y, np.ones(n)) == pytest.approx(
            -math.log(p), rel=1e-12)
        assert weighted_stat("gini", y, np.ones(n)) == pytest.approx(
            1 - p, rel=1e-12)


def test_the_binary_family_refuses_both_and_says_why():
    """Not "unknown statistic" - DELIBERATELY absent, and the reason
    is the useful part.

    BROKEN WITH: the BINARY_REFUSED branch removed - the generic
    'Unknown binary statistic' error then fires, which still raises
    and says nothing about why."""
    import pandas as pd
    from equipop.cells import build_cells
    from equipop.analysis import run_knn_stats
    df = pd.DataFrame({"x": [50.0, 150], "y": [50.0, 50], "b": [0, 1]})
    cd, _ = _quiet(build_cells, df, "x", "y", binary_vars=["b"],
                   unit_size=100)
    with pytest.raises(ValueError, match=r"-ln\(p\)"):
        _quiet(run_knn_stats, cd, [2], {"b": ["theil"]})
    with pytest.raises(ValueError, match="logarithm of zero"):
        _quiet(run_knn_stats, cd, [2], {"b": ["mld"]})


def test_theil_on_a_zero_one_value_field_says_so_but_still_runs():
    """Warn, never act: a 0/1 field given as a VALUE gets its Theil,
    and a note that the number is the share in disguise.

    BROKEN WITH: the note removed."""
    res, said = _stats({"x01": np.array([0.0, 1, 1, 0])},
                       {"x01": ["theil"]})
    assert "holds only 0 and 1" in said
    assert res["Theil_x01_4"][0] == pytest.approx(-math.log(0.5))


# ------------------------------------------------------ decomposition
def test_the_hand_example():
    """Two groups in one cell: A = [1, 3], B = [4, 4]. Worked by hand:
    between = 0.5 ln(3/2) + 0.5 ln(3/4) = 0.0588915178
    within  = 0.5 MLD(A) + 0.5 x 0     = 0.0719205181
    share   = 0.0588915178 / 0.1308120359 = 0.4501995356

    BROKEN WITH: ln(mu_g / mu) for ln(mu / mu_g) in the MLD between
    term - the between part comes out negative."""
    res, _ = _stats({"inc": np.array([1.0, 3, 4, 4])}, {"inc": ["mld"]},
                    decompose_by={"grp": np.array([0, 0, 1, 1])},
                    min_group=0)
    assert res["MLDb_inc_4"][0] == pytest.approx(0.0588915178, abs=1e-10)
    assert res["MLDw_inc_4"][0] == pytest.approx(0.0719205181, abs=1e-10)
    assert res["MLDsh_inc_4"][0] == pytest.approx(0.4501995356, abs=1e-9)
    assert res["Ng_inc_4"][0] == 2 and res["NgMin_inc_4"][0] == 2


@pytest.fixture(scope="module")
def town():
    rng = np.random.default_rng(405)
    n = 1200
    # three groups, CLUSTERED, so some neighbourhoods lack one
    x = rng.uniform(0, 4000, n)
    y = rng.uniform(0, 4000, n)
    g = np.where(x < 1300, "a", np.where(rng.random(n) < 0.4, "b", "c"))
    inc = rng.lognormal(10, 0.6, n) * np.select(
        [g == "a", g == "b"], [0.6, 0.9], 1.0)
    w = rng.uniform(0.3, 2.5, n)                 # fractional people
    return x, y, g.astype(object), inc, w


@pytest.mark.parametrize("mode", ["proportional", "whole", "sampled"])
def test_between_plus_within_is_the_index_itself(town, mode):
    """THE identity, through two independent routes: MLD and Theil
    computed directly over everybody, against between + within
    assembled from each group's count, mean and index. Fractional
    weights, a radius as well as two k, every overshoot mode, and
    neighbourhoods where one of three groups is absent.

    BROKEN WITH: group shares from the number of distinct values
    instead of the weighted count Nv_; the s_g factor dropped from the
    within part; the (mu_g / mu) factor dropped from Theil's between
    part; an absent group's missing mean treated as 0."""
    x, y, g, inc, w = town
    res, _ = _quiet(dispatch, "stats", x, y, unit_size=100, weight=w,
                    k_values=[100, 500], r_values=[400],
                    values={"inc": inc}, stats={"inc": ["mld", "theil"]},
                    decompose_by={"g": g}, min_group=0,
                    overshoot_mode=mode, seed=7)
    checked = 0
    for suf in ("100", "500", "r400"):
        two = np.asarray(res[f"Ng_inc_{suf}"], float) >= 2
        for P in ("MLD", "Theil"):
            tot = np.asarray(res[f"{P}_inc_{suf}"], float)
            bw = (np.asarray(res[f"{P}b_inc_{suf}"], float)
                  + np.asarray(res[f"{P}w_inc_{suf}"], float))
            # with no minimum, EVERY neighbourhood holding two groups
            # must have a split - and it must be the index itself
            assert np.isfinite(bw[two]).all()
            np.testing.assert_allclose(bw[two], tot[two], rtol=1e-11)
            # and one holding a single group has none
            assert np.isnan(bw[~two]).all()
            checked += int(two.sum())
    ng = np.asarray(res["Ng_inc_100"], float)
    assert (ng == 2).any() and (ng == 3).any(), \
        "the fixture no longer has neighbourhoods missing a group"
    assert checked > 5000


def test_the_minimum_empties_all_three_and_keeps_the_counts():
    """John's ruling: a user-set minimum, default 30. Between-group
    inequality is biased upward in small groups, so below the minimum
    nothing is reported - and the two count columns stay, so the
    reader sees why.

    BROKEN WITH: `ngmin > min_group` for `>=`; only the share
    emptied, leaving the biased between part on the map."""
    kw = dict(decompose_by={"grp": np.array([0, 0, 1, 1])})
    v = {"inc": np.array([1.0, 3, 4, 4])}
    res, _ = _stats(v, {"inc": ["mld"]}, min_group=3, **kw)
    for part in ("b", "w", "sh"):
        assert np.isnan(res[f"MLD{part}_inc_4"][0])
    assert res["Ng_inc_4"][0] == 2 and res["NgMin_inc_4"][0] == 2
    res, _ = _stats(v, {"inc": ["mld"]}, min_group=2, **kw)
    assert res["MLDsh_inc_4"][0] == pytest.approx(0.4501995356, abs=1e-9)


def test_the_default_minimum_is_thirty():
    """BROKEN WITH: DEFAULT_MIN_GROUP changed, or None not resolved to
    it. 29 and 31 people either side of the line."""
    from equipop.decompose import DEFAULT_MIN_GROUP, resolve_min_group
    assert DEFAULT_MIN_GROUP == 30.0 and resolve_min_group(None) == 30.0
    for n_small, present in ((29, False), (30, True)):
        n = n_small + 40
        v = {"inc": np.r_[np.full(n_small, 2.0), np.linspace(1, 5, 40)]}
        g = np.r_[np.zeros(n_small), np.ones(40)]
        res, _ = _stats(v, {"inc": ["mld"]}, decompose_by={"g": g})
        assert np.isfinite(res[f"MLDsh_inc_{n}"][0]) == present


def test_one_group_present_is_absent_not_zero():
    """A neighbourhood holding one group has no between-group
    inequality to MEASURE. Zero would read as a finding.

    BROKEN WITH: `ng >= 1` for `ng >= 2`."""
    res, _ = _quiet(dispatch, "stats", np.r_[50.0, 50, 9950, 9950],
                    np.r_[50.0, 50, 9950, 9950], unit_size=100,
                    k_values=[2], values={"inc": np.array([1.0, 3, 4, 5])},
                    stats={"inc": ["mld"]},
                    decompose_by={"g": np.array([0, 0, 1, 1])},
                    min_group=0)
    assert list(res["Ng_inc_2"]) == [1, 1, 1, 1]
    assert np.isnan(np.asarray(res["MLDsh_inc_2"], float)).all()
    assert np.isnan(np.asarray(res["MLDb_inc_2"], float)).all()


def test_rows_without_a_group_are_left_out_and_said():
    """A row with an income but no group cannot be placed on either
    side of the split. It is left out of the split, stays in every
    other statistic, and the run says how many.

    BROKEN WITH: the missing code counted as a group of its own."""
    v = {"inc": np.array([1.0, 3, 5, 4, 4])}
    g = np.array(["A", "A", "", "B", "B"], dtype=object)
    res, said = _stats(v, {"inc": ["mld"]}, decompose_by={"cob": g},
                       min_group=0)
    assert "1 row(s) have a value of 'inc' but no 'cob'" in said
    assert res["Ng_inc_5"][0] == 2
    # the split is the split of the four people WITH a group...
    b_w = res["MLDb_inc_5"][0] + res["MLDw_inc_5"][0]
    assert b_w == pytest.approx(MLD_1_3_4_4, abs=1e-10)
    # ...while the field's own MLD still includes the fifth
    assert res["MLD_inc_5"][0] == pytest.approx(
        VALUE_STATS["mld"](v["inc"]), rel=1e-12)


def test_groups_can_be_text_codes_or_carry_stata_missing():
    """BROKEN WITH: _codes reading only numbers (text becomes all
    missing) or treating Stata's missing (> 8.9e307) as a group."""
    v = {"inc": np.array([1.0, 3, 4, 4])}
    for g in (np.array(["abroad", "abroad", "Sweden", "Sweden"],
                       dtype=object),
              np.array([1.0, 1, 2, 2]),
              np.array([1, 1, 2, 2])):
        res, _ = _stats(v, {"inc": ["mld"]}, decompose_by={"g": g},
                        min_group=0)
        assert res["MLDsh_inc_4"][0] == pytest.approx(0.4501995356,
                                                      abs=1e-9)
    res, said = _stats(v, {"inc": ["mld"]}, min_group=0,
                       decompose_by={"g": np.array([1.0, 1, 2, 9e307])})
    assert "no 'g'" in said and res["Ng_inc_4"][0] == 2


def test_k_still_counts_everybody():
    """The split must not change the neighbourhood: same N_k, same
    Dist_k, same Nv_ with and without it.

    BROKEN WITH: the cells built from the sub-fields' members only."""
    rng = np.random.default_rng(3)
    n = 300
    x, y = rng.uniform(0, 2000, n), rng.uniform(0, 2000, n)
    v = {"inc": rng.lognormal(5, .5, n)}
    g = rng.integers(0, 2, n).astype(float)
    a, _ = _quiet(dispatch, "stats", x, y, unit_size=100, k_values=[40],
                  values=v, stats={"inc": ["mld"]})
    b, _ = _quiet(dispatch, "stats", x, y, unit_size=100, k_values=[40],
                  values=v, stats={"inc": ["mld"]},
                  decompose_by={"g": g})
    for c in ("N_40", "Dist_40", "Nv_inc_40", "MLD_inc_40"):
        np.testing.assert_array_equal(np.asarray(a[c]), np.asarray(b[c]))


def test_the_scaffolding_never_reaches_the_output_or_the_log():
    """The per-group sub-fields are machinery. Their columns must not
    leak, and their missing values - there by construction - must not
    produce one note each.

    BROKEN WITH: quiet_missing not passed to build_cells (a note per
    sub-field appears); the drop in assemble() removed."""
    g = np.array([0, 0, 1, 1])
    res, said = _stats({"inc": np.array([1.0, 3, 4, 4])},
                       {"inc": ["mld"]}, decompose_by={"grp": g},
                       min_group=0)
    assert not [c for c in res if "[" in c]
    notes = [ln for ln in said.splitlines() if "missing values" in ln]
    assert not [ln for ln in notes if "[grp=" in ln], notes


def test_the_prediction_is_the_result():
    """A door predicts its columns BEFORE reading the layer, so the
    decomposition's names must not depend on the groups - and the
    prediction and the engine use one naming function.

    BROKEN WITH: predict_result_fields ignoring `decomposing`."""
    from equipop.doors.fields import predict_result_fields
    rng = np.random.default_rng(2)
    n = 300
    x, y = rng.uniform(0, 2000, n), rng.uniform(0, 2000, n)
    want = ["mean", "mld", "theil", "p10"]
    res, _ = _quiet(dispatch, "stats", x, y, unit_size=100,
                    k_values=[50, 200], r_values=[300.5],
                    values={"inc": rng.lognormal(5, .5, n),
                            "rent": rng.lognormal(4, .3, n)},
                    stats={"inc": want, "rent": want},
                    decompose_by={"g": rng.integers(0, 3, n)})
    pred = predict_result_fields("stats", "50 200", "300.5", "", [],
                                 ["inc", "rent"], want, False, False,
                                 decomposing=True)
    assert set(res) == set(pred)


@pytest.mark.parametrize("kw, words", [
    (dict(stats={"inc": ["mean"]}, decompose_by={"g": [0, 0, 1, 1]}),
     "needs MLD or Theil"),
    (dict(stats={"inc": ["mld"]}, decompose_by={"g": [0, 0, 0, 0]}),
     "only one group"),
    (dict(stats={"inc": ["mld"]}, decompose_by={"g": [0, 0, 1, 1],
                                                "h": [0, 1, 0, 1]}),
     "exactly one grouping"),
    (dict(stats={"inc": ["mld"]}, decompose_by={"g": [0, 1, 1]}),
     "row-aligned"),
    (dict(stats={"inc": ["mld"]}, decompose_by={"g": [0, 0, 1, 1]},
          min_group=-1), "zero or more"),
    (dict(stats={"inc": ["mld"]}, decompose_by={"g": [0, 0, 1, 1]},
          min_group=True), "number of people"),
    (dict(stats={"inc": ["mld"]}, min_group=float("nan")),
     "zero or more"),
])
def test_a_bad_request_is_refused_with_words_a_person_can_use(kw, words):
    """BROKEN WITH: each corresponding check in decompose.py removed -
    the run then goes ahead, or fails later with a bare traceback."""
    with pytest.raises(ValueError, match=words):
        _stats({"inc": np.array([1.0, 3, 4, 4])}, **kw)


def test_twenty_one_groups_is_an_identifier_not_a_circumstance():
    """BROKEN WITH: MAX_LEVELS raised past the 21 used here."""
    n = 42
    with pytest.raises(ValueError, match="21 distinct values"):
        _stats({"inc": np.linspace(1, 9, n)}, {"inc": ["mld"]},
               decompose_by={"g": np.repeat(np.arange(21.0), 2)})


def test_the_record_names_the_grouping_and_the_minimum():
    """BACKLOG 293: the run record is taken from dispatch's bound
    arguments, so a setting in the signature is recorded with nothing
    else touched. The grouping is recorded BY NAME, summarised.

    BROKEN WITH: decompose_by taken through **extra instead of the
    signature."""
    from equipop.meta import record
    log = record("stats", 4, {})
    _quiet(dispatch, "stats", ONE_CELL["x"], ONE_CELL["y"],
           unit_size=100, k_values=[4], provenance=log,
           values={"inc": np.array([1.0, 3, 4, 4])},
           stats={"inc": ["mld"]},
           decompose_by={"cob": np.array([0, 0, 1, 1])}, min_group=12)
    st = log.doc["settings"]
    assert "cob" in st["decompose_by"]
    assert st["min_group"] == 12


# ------------------------------- v1.55.1, external review of 1.55.0
# BACKLOG 407. Four findings, all reproduced before they were fixed.

@pytest.mark.parametrize("label, missing", [
    ("pd.NA in a string array", "string-NA"),
    ("pd.NA in an object array", "object-NA"),
    ("pd.NaT", "NaT"),
    ("nullable Int64 with NA", "Int64-NA"),
    ("None", "None"),
    ("NaN", "nan"),
    ("a blank string", "blank"),
    ("Stata's missing", "stata"),
])
def test_every_missing_marker_is_missing_not_a_group(label, missing):
    """Review finding 1, reproduced: A, A, <NA>, B, B came out as
    THREE groups, so missingness became an analytical group.

    BROKEN WITH: _is_missing reduced to `x is None` plus a float NaN -
    the reader as 1.55.0 shipped it."""
    import pandas as pd
    groups = {
        "string-NA": pd.array(["A", "A", pd.NA, "B", "B"], dtype="string"),
        "object-NA": np.array(["A", "A", pd.NA, "B", "B"], dtype=object),
        "NaT": np.array(["A", "A", pd.NaT, "B", "B"], dtype=object),
        "Int64-NA": pd.array([1, 1, None, 2, 2], dtype="Int64"),
        "None": np.array(["A", "A", None, "B", "B"], dtype=object),
        "nan": np.array([1.0, 1, np.nan, 2, 2]),
        "blank": np.array(["A", "A", "  ", "B", "B"], dtype=object),
        "stata": np.array([1.0, 1, 8.99e307, 2, 2]),
    }
    res, said = _stats({"inc": np.array([1.0, 3, 5, 4, 4])},
                       {"inc": ["mld"]},
                       decompose_by={"g": groups[missing]}, min_group=0)
    assert res["Ng_inc_5"][0] == 2, label
    assert "1 row(s) have a value of 'inc' but no 'g'" in said, label
    b_w = res["MLDb_inc_5"][0] + res["MLDw_inc_5"][0]
    assert b_w == pytest.approx(MLD_1_3_4_4, abs=1e-10), label


def test_two_codes_that_print_alike_stay_two_groups():
    """Review finding 1, second half, reproduced: 1.0 and
    1.00000000001 both formatted as "1", their sub-fields shared a
    name, one overwrote the other, and a total MLD of 0.1308 was
    reported as between 0 and within 0.

    BROKEN WITH: sub-fields named by the group's LABEL with the old
    ten-digit format (`f"{f}[{group_name}={lab}]"` and `.10g`)."""
    g = np.array([1.0, 1.0, 1.0 + 1e-11, 1.0 + 1e-11])
    res, _ = _stats({"inc": np.array([1.0, 3, 4, 4])}, {"inc": ["mld"]},
                    decompose_by={"g": g}, min_group=0)
    assert res["Ng_inc_4"][0] == 2
    assert res["MLDb_inc_4"][0] == pytest.approx(0.0588915178, abs=1e-10)
    assert res["MLDb_inc_4"][0] + res["MLDw_inc_4"][0] == pytest.approx(
        res["MLD_inc_4"][0], rel=1e-12)


def test_distinct_codes_are_named_distinctly_in_the_message():
    """BROKEN WITH: the ten-digit label alone (sub-fields still by
    number) - the split is right and the message then says
    "(1, 1)", which no reader can act on."""
    g = np.array([1.0, 1.0, 1.0 + 1e-11, 1.0 + 1e-11])
    _, said = _stats({"inc": np.array([1.0, 3, 4, 4])}, {"inc": ["mld"]},
                     decompose_by={"g": g}, min_group=0)
    assert "(1, 1.00000000001)" in said


def test_large_integer_codes_are_not_rounded_together():
    """Found while fixing finding 1, the same class by another road:
    two distinct int64 codes above 2**53 become ONE float. Codes that
    are whole numbers stay integers now.

    BROKEN WITH: integer codes stored as float()."""
    # 2**53 and 2**53 + 1 are the SAME float. The first version of
    # this test used 2**53 + 1 and 2**53 + 3, which round to two
    # different floats, so the break it names could not show - and
    # break-check said so.
    assert float(2**53) == float(2**53 + 1)
    big = np.array([2**53, 2**53, 2**53 + 1, 2**53 + 1],
                   dtype=np.int64)
    res, _ = _stats({"inc": np.array([1.0, 3, 4, 4])}, {"inc": ["mld"]},
                    decompose_by={"g": big}, min_group=0)
    assert res["Ng_inc_4"][0] == 2
    assert res["MLDsh_inc_4"][0] == pytest.approx(0.4501995356, abs=1e-9)


def test_each_field_is_split_by_the_index_asked_of_it():
    """Review finding 4, reproduced - and worse than reported. Asking
    MLD of income and Theil of rent wrote a Theil split for income and
    an MLD split for rent; and when rent held a zero, the run was
    REFUSED, naming the scaffolding field 'rent[g=0]', for an MLD no
    one asked of rent.

    BROKEN WITH: the per-field indices replaced by their union."""
    v = {"income": np.array([1.0, 3, 4, 4]),
         "rent": np.array([0.0, 5, 6, 8])}            # rent has a zero
    res, _ = _stats(v, {"income": ["mld"], "rent": ["theil"]},
                    decompose_by={"g": np.array([0, 0, 1, 1])},
                    min_group=0)
    split = {c.rsplit("_", 1)[0] for c in res
             if c.startswith(("MLDb", "MLDw", "MLDsh", "Theilb",
                              "Theilw", "Theilsh"))}
    assert split == {"MLDb_income", "MLDw_income", "MLDsh_income",
                     "Theilb_rent", "Theilw_rent", "Theilsh_rent"}


def test_the_overshoot_help_no_longer_claims_a_refusal():
    """Review finding 2: the shared overshoot help - shown in both
    dialogs and shipped in Pro's sidecars - said value statistics
    REFUSE proportional mode. That ended in 1.31. The claim is checked
    against the behaviour it describes: machine 2 under proportional,
    with a median, a Gini and an MLD, over a fractional ring.

    BROKEN WITH: the 1.55.0 sentence restored to HELP["overshoot"]."""
    from equipop.doors.help import HELP
    assert "refuse" not in HELP["overshoot"].lower()
    assert "weight by them" in HELP["overshoot"]
    rng = np.random.default_rng(9)
    x, y = rng.uniform(0, 1000, 200), rng.uniform(0, 1000, 200)
    res, _ = _quiet(dispatch, "stats", x, y, unit_size=100,
                    k_values=[7], values={"v": rng.lognormal(3, .4, 200)},
                    stats={"v": ["median", "gini", "mld"]},
                    overshoot_mode="proportional")
    for c in ("Med_v_7", "Gini_v_7", "MLD_v_7"):
        assert np.isfinite(np.asarray(res[c], float)).all(), c
    assert np.allclose(np.asarray(res["N_7"], float), 7)
