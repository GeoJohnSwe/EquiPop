# -*- coding: utf-8 -*-
"""test_decompose.py - MLD, Theil, and their between/within split.

v1.55.0, BACKLOG 405; the split rebuilt on additive sums in v1.57.0,
BACKLOG 409.

Every expected number here is either a LITERAL worked out by hand, or
an identity between two INDEPENDENT routes through the code - never
the same function asked twice. The central one: between + within,
assembled from each group's four additive sums, must equal the index
the engine computes directly over everybody from the sorted values.
Those share no code below run_knn_stats.

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
    computed directly over everybody from the sorted values, against
    between + within assembled from each group's additive sums.
    Fractional weights, a radius as well as two k, every overshoot
    mode, and neighbourhoods where one of three groups is absent.

    BROKEN WITH: the s_g factor dropped from MLD's within part;
    Theil's between part weighted by people (s_g) instead of income
    (v_g); the crossing ring's share not applied to the sums (every
    ring cell whole - only `proportional` can see that); an absent
    group counted as present (`W >= 0`)."""
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
    Dist_k, same Nv_ with and without it - including the people who
    have an income and no group.

    BROKEN WITH: the cells built from the rows that HAVE a group."""
    rng = np.random.default_rng(3)
    n = 300
    x, y = rng.uniform(0, 2000, n), rng.uniform(0, 2000, n)
    v = {"inc": rng.lognormal(5, .5, n)}
    g = rng.integers(0, 2, n).astype(float)
    g[::7] = np.nan
    a, _ = _quiet(dispatch, "stats", x, y, unit_size=100, k_values=[40],
                  values=v, stats={"inc": ["mld"]})
    b, _ = _quiet(dispatch, "stats", x, y, unit_size=100, k_values=[40],
                  values=v, stats={"inc": ["mld"]},
                  decompose_by={"g": g})
    for c in ("N_40", "Dist_40", "Nv_inc_40", "MLD_inc_40"):
        np.testing.assert_array_equal(np.asarray(a[c]), np.asarray(b[c]))


def test_the_scaffolding_never_reaches_the_output_or_the_log():
    """The per-group sums are machinery. Their columns must not leak,
    and nothing the run says may name them.

    Two guards keep them out, and either alone suffices: assemble()
    drops them, and dispatch keeps only columns with a known prefix.
    The first is pinned on its own by the next test.

    BROKEN WITH: dispatch's prefix filter removed TOGETHER with the
    drop in assemble()."""
    g = np.array([0, 0, 1, 1])
    res, said = _stats({"inc": np.array([1.0, 3, 4, 4])},
                       {"inc": ["mld", "theil"]}, decompose_by={"grp": g},
                       min_group=0)
    assert not [c for c in res if "[" in c or "#" in c]
    assert "[grp]" not in said and "#0" not in said


def test_the_split_is_assembled_from_hand_computed_sums():
    """Plan.assemble alone, fed the sums of the hand example by hand -
    A = [1, 3], B = [4, 4], everyone weighing 1, no rescaling:
        W = 2, 2   S = 4, 8   L = ln 3, 2 ln 4   Q = 3 ln 3, 8 ln 4
    No engine, no cells: this is the arithmetic of the module
    docstring, and nothing else. It must also take its sums away.

    BROKEN WITH: the drop in assemble() removed."""
    import pandas as pd
    from equipop.decompose import Plan
    plan = Plan("grp", ["0", "1"], ["inc"], {"inc": ["mld", "theil"]}, 0.0)
    sums = {"W": (2, 2), "S": (4, 8),
            "L": (math.log(3), 2 * math.log(4)),
            "Q": (3 * math.log(3), 8 * math.log(4))}
    st = pd.DataFrame({f"{plan.sum_name('inc', q, i)}_4": [float(v[i])]
                       for q, v in sums.items() for i in (0, 1)})
    st["N_4"] = [4.0]
    out = plan.assemble(st)
    assert out["MLDb_inc_4"][0] == pytest.approx(0.0588915178, abs=1e-10)
    assert out["MLDw_inc_4"][0] == pytest.approx(0.0719205181, abs=1e-10)
    assert out["MLDsh_inc_4"][0] == pytest.approx(0.4501995356, abs=1e-9)
    # Theil of [1, 3, 4, 4], mean 3: (1/3 ln 1/3 + ln 1 + 2 x 4/3 ln 4/3)/4
    theil = (math.log(1 / 3) / 3 + 2 * 4 / 3 * math.log(4 / 3)) / 4
    assert out["Theilb_inc_4"][0] + out["Theilw_inc_4"][0] == \
        pytest.approx(theil, abs=1e-12)
    assert list(out["Ng_inc_4"]) == [2] and list(out["NgMin_inc_4"]) == [2]
    assert list(out["NgN_inc_4"]) == [4]
    assert sorted(out) == sorted(
        ["N_4", "Ng_inc_4", "NgMin_inc_4", "NgN_inc_4"]
        + [f"{P}{p}_inc_4" for P in ("MLD", "Theil") for p in ("b", "w", "sh")])


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

    The sub-fields are gone (409); the codes still decide the groups.

    BROKEN WITH: _codes keying a float by its ten-digit format, as the
    1.55.0 names did - the two codes then read as ONE group."""
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


# ------------------------------------------------ v1.57.0, BACKLOG 409
# The split rebuilt on four additive sums per group. Measured on 50,000
# points at k=400: one field in 20 groups 196 s -> 28 s, three fields
# in 20 groups 595 s and 1.4 GB -> 59 s and 0.4 GB.

def test_a_group_is_not_a_value_field():
    """What made the split expensive: each group was a value field of
    its own, sorted for every neighbourhood. The engine's own line
    says which fields it sorts; the groups must not be among them.

    BROKEN WITH: the per-group quantities passed as value_vars as
    well - every number still right, at the old cost."""
    g = np.array([0, 1, 2, 3, 0, 1, 2, 3])
    _, said = _stats({"inc": np.linspace(1, 8, 8)}, {"inc": ["mld"]},
                     decompose_by={"grp": g}, min_group=0)
    line = [ln for ln in said.splitlines()
            if ln.startswith("[stats] binary vars")]
    assert line == ["[stats] binary vars: [] | value vars: ['inc']"]


def test_one_income_everywhere_has_nothing_to_split():
    """Where everybody in a neighbourhood has the same income there is
    no inequality: between and within are 0, and the share is EMPTY -
    0/0 is not a share. Measured on 1.56.0 with fractional weights:
    282 of 600 such neighbourhoods reported a share (mostly 1.0, "all
    of it between groups") or a between part of -2e-16, from rounding
    alone.

    BROKEN WITH: the NO_INEQUALITY floor removed."""
    rng = np.random.default_rng(9)
    for _ in range(40):
        n = int(rng.integers(20, 90))
        v = float(rng.choice([0.1, 1 / 3, 31000.7, 7e-5]))
        na = int(rng.integers(5, n - 5))
        w = rng.uniform(0.1, 3, n)
        res, _ = _quiet(dispatch, "stats", np.full(n, 50.0),
                        np.full(n, 50.0), unit_size=100,
                        k_values=[float(w.sum()) * 0.97], weight=w,
                        values={"inc": np.full(n, v)},
                        stats={"inc": ["mld", "theil"]},
                        decompose_by={"g": np.r_[np.zeros(na),
                                                 np.ones(n - na)]},
                        min_group=0)
        for P in ("MLD", "Theil"):
            got = {p: [res[c][0] for c in res
                       if c.startswith(f"{P}{p}_")][0]
                   for p in ("b", "w", "sh")}
            assert got["b"] == 0.0 and got["w"] == 0.0, (P, v, got)
            assert np.isnan(got["sh"]), (P, v, n, na, got)


def test_large_incomes_with_a_small_spread_keep_their_digits():
    """Both indices ignore the unit of income, so each field is divided
    by e^(its mean log) before it is summed, which puts every mean
    near 1 where its log loses nothing. Incomes near e^25 with a 0.1%
    spread, against a reference that never subtracts two large logs.

    BROKEN WITH: the rescaling removed (centre 0)."""
    rng = np.random.default_rng(12)
    n = 400
    inc = rng.lognormal(25, 0.001, n)
    w = rng.uniform(0.3, 2, n)
    g = rng.integers(0, 3, n)
    k = float(w.sum())
    res, _ = _quiet(dispatch, "stats", np.full(n, 50.0), np.full(n, 50.0),
                    unit_size=100, k_values=[k], weight=w,
                    values={"inc": inc}, stats={"inc": ["mld", "theil"]},
                    decompose_by={"g": g}, min_group=0)
    r = inc / (np.sum(w * inc) / w.sum())                 # y / mu
    ref = {"MLD": np.sum(w * -np.log1p(r - 1)) / w.sum(),
           "Theil": np.sum(w * r * np.log1p(r - 1)) / w.sum()}
    for P in ("MLD", "Theil"):
        b = [res[c][0] for c in res if c.startswith(f"{P}b_")][0]
        wi = [res[c][0] for c in res if c.startswith(f"{P}w_")][0]
        assert ref[P] < 1e-6                     # the hard case, really
        # abs=0: pytest.approx otherwise adds an absolute 1e-12, which
        # on an index of 4e-7 is a RELATIVE 2.5e-6 - and the break
        # this test names (2.3e-8 off) passed. Break-check said so.
        assert (b + wi) == pytest.approx(ref[P], rel=1e-9, abs=0), P


def test_the_cells_carry_each_groups_sums():
    """By hand: cell A holds codes 0, 1, 0 with q = 1, 2, 4 weighing
    1, 0.5, 2; cell B holds a row in no group (code -1, q = 8) and a
    row with no q. Group 0 in A: 1x1 + 4x2 = 9; group 1: 2x0.5 = 1.

    BROKEN WITH: the bincount slot as code x cells + cell - groups and
    cells transposed."""
    import pandas as pd
    from equipop.cells import build_cells, split_sum_name
    df = pd.DataFrame({"x": [50.0, 50, 50, 150, 150], "y": [50.0] * 5,
                       "q": [1.0, 2, 4, 8, np.nan], "c": [0, 1, 0, -1, 1],
                       "w": [1.0, 0.5, 2, 1, 3]})
    cd, _ = _quiet(build_cells, df, "x", "y", unit_size=100, weights="w",
                   sum_vars=["q"], sum_by="c", sum_levels=2)
    assert cd.sum_names == [split_sum_name("q", 0), split_sum_name("q", 1)]
    np.testing.assert_array_equal(cd.sum_matrix, [[9.0, 1.0], [0.0, 0.0]])
    for bad in ([0, 1, 0, -1, 2], [0, 1, 0.5, -1, 1]):
        with pytest.raises(ValueError, match="whole codes from -1 to 1"):
            _quiet(build_cells, df.assign(c=bad), "x", "y", unit_size=100,
                   sum_vars=["q"], sum_by="c", sum_levels=2)


def test_an_origin_with_nobody_in_its_cell_still_gets_its_split():
    """John's rule since 1.22.2: a row outside the reference
    population is nobody's neighbour, and still gets its own results.
    Its cell holds no one, so one is added for it - and every per-cell
    array has to grow with it (343's lesson), the sums included.

    BROKEN WITH: the sum matrix not grown in _add_empty_origin_cells."""
    rng = np.random.default_rng(5)
    n = 200
    x = np.r_[rng.uniform(0, 1000, n), 5050.0]
    y = np.r_[rng.uniform(0, 1000, n), 5050.0]
    w = np.r_[np.ones(n), 0.0]
    res, said = _quiet(dispatch, "stats", x, y, unit_size=100, weight=w,
                       k_values=[60], values={"inc": rng.lognormal(
                           5, .5, n + 1)}, stats={"inc": ["mld"]},
                       decompose_by={"g": rng.integers(0, 2, n + 1)},
                       min_group=0)
    assert "hold no population" in said
    assert res["Ng_inc_60"][n] == 2
    assert np.isfinite(res["MLDsh_inc_60"][n])


# ----------------------------------------------- v1.57.0, BACKLOG 407a
def test_the_split_says_who_it_covers():
    """The external reviewer's coverage column: the people left out of
    the split for having no group must travel WITH the result, not
    only in the run's messages. NgN_ is the people the split covers;
    beside Nv_ it shows the gap, row by row.

    Five incomes, one with no group, everyone weighing 1.5 - so 7.5
    people in one cell - and k = 5: the cell is two-thirds inside the
    neighbourhood, and the split's people take the same share as
    everybody else's. Nv = 7.5 x 2/3 = 5; NgN = 6 x 2/3 = 4.

    BROKEN WITH: NgN_ written as the largest group (W.max) instead of
    the sum over groups."""
    v = {"inc": np.array([1.0, 3, 5, 4, 4])}
    g = np.array(["A", "A", "", "B", "B"], dtype=object)
    res, said = _stats(v, {"inc": ["mld"]}, decompose_by={"cob": g},
                       min_group=0, weight=np.full(5, 1.5))
    k = [c for c in res if c.startswith("NgN_inc_")][0][len("NgN_inc_"):]
    assert res[f"Nv_inc_{k}"][0] == pytest.approx(5.0, abs=1e-12)
    assert res[f"NgN_inc_{k}"][0] == pytest.approx(4.0, abs=1e-12)
    # five rows in one cell: five places, all of them short
    assert ("[decompose] inc, k=5: split reported in 5 of 5 places. In 5 "
            "places the split leaves out people with a value but no "
            "'cob' (NgN_ below Nv_).") in said
    # and ONE short place is one place: four people with groups in one
    # cell, one without in another a kilometre off. At k=4 only the
    # lone row's neighbourhood reaches across to include him.
    res, said = _quiet(dispatch, "stats", np.r_[np.full(4, 50.0), 1050.0],
                       np.full(5, 50.0), unit_size=100, k_values=[4],
                       values=v, stats={"inc": ["mld"]},
                       decompose_by={"cob": g[[0, 1, 3, 4, 2]]},
                       min_group=0)
    assert list(res["NgN_inc_4"]) == [4, 4, 4, 4, 3]
    assert "In 1 place the split leaves out" in said


def test_full_coverage_says_nothing_more():
    """Where everybody with a value has a group, NgN_ equals Nv_ and
    the summary line gains nothing.

    BROKEN WITH: the shortfall test without its rounding margin and
    with `<=` (ngn <= nv), so every fully covered place reads as
    short. (`<=` alone, margin kept, is the same test - the first
    break-check of this named that, and it could not fail.)"""
    res, said = _stats({"inc": np.array([1.0, 3, 4, 4])}, {"inc": ["mld"]},
                       decompose_by={"g": np.array([0, 0, 1, 1])},
                       min_group=0)
    assert res["NgN_inc_4"][0] == res["Nv_inc_4"][0] == 4
    line = [ln for ln in said.splitlines() if ln.startswith("[decompose] inc")]
    assert line and "leaves out" not in line[0], line


# ------------------------------- v1.57.1, external review of 1.57.0
def test_the_coverage_margin_scales_with_the_population():
    """The reviewer's precautionary point, and it was not only
    precautionary. NgN_ and Nv_ add the same people in different
    orders, so at WorldPop scale they differ by rounding: 300 points
    weighing about a million each, EVERY row in a group, and 1.57.0
    said "In 87 places the split leaves out people with a value but no
    'g'". The margin is now 1e-9 plus 1e-12 of the total.

    BROKEN WITH: the absolute margin alone (`margin = 1e-9`)."""
    rng = np.random.default_rng(100)
    n = 300
    w = rng.uniform(0.3, 2.5, n) * 1e6
    x, y = rng.uniform(0, 10000, n), rng.uniform(0, 10000, n)
    res, said = _quiet(dispatch, "stats", x, y, unit_size=100, weight=w,
                       k_values=[int(w.sum() * 0.5)],
                       values={"inc": rng.lognormal(10, .5, n)},
                       stats={"inc": ["theil"]},
                       decompose_by={"g": rng.integers(0, 3, n)},
                       min_group=0)
    line = [ln for ln in said.splitlines() if ln.startswith("[decompose] inc,")]
    assert line and "leaves out" not in line[0], line
    # ...and the rounding the margin absorbs is really there
    k = [c for c in res if c.startswith("NgN_")][0][len("NgN_"):]
    gap = np.abs(np.asarray(res[f"NgN_{k}"], float)
                 - np.asarray(res[f"Nv_{k}"], float))
    assert gap.max() > 1e-9


def test_a_real_shortfall_is_still_reported_at_scale():
    """The margin must not swallow people. At 200 million, half a
    person left out is still reported; rounding of 5e-7 is not.

    BROKEN WITH: a relative margin of 1e-8 (2 people at this total)."""
    from equipop.decompose import Plan
    plan = Plan("g", ["0", "1"], ["inc"], {"inc": ["theil"]}, 0.0)
    nv = np.full(3, 2e8)
    res = {"Ng_inc_100": np.full(3, 2.0), "NgMin_inc_100": np.full(3, 5e7),
           "Theilb_inc_100": np.full(3, 0.01), "Nv_inc_100": nv,
           "NgN_inc_100": nv - np.array([0.0, 5e-7, 0.5])}
    line = plan.report(res)[0]
    assert "In 1 place the split leaves out" in line, line
