"""BACKLOG 168 in Stata, and the name preflight from the 1.36 review.

The missing-code case is not hypothetical. John's Bristol County
extract - the conference demonstration data - carries the US Census
sentinel -666666666 in 64 of its 1,074 rows for median household
income, and 64 more top-coded at 250001. Undeclared, that sentinel is
just a number: a neighbourhood mean lands near minus forty million and
lands there quietly.
"""

import io
import os
import re
import contextlib

import numpy as np
import pytest

from equipop.stata_bridge import blank_missing_codes, knn_to_rows

CENSUS_SENTINEL = -666666666.0

STATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stata")


def _quiet(fn, *a, **kw):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = fn(*a, **kw)
    return out, buf.getvalue()


# --------------------------------------------------------------------
# The blanking itself
# --------------------------------------------------------------------

def test_a_declared_code_becomes_missing():
    bag = {"inc": np.array([100.0, CENSUS_SENTINEL, 300.0])}
    out, hits = _quiet(blank_missing_codes, bag, [CENSUS_SENTINEL])
    new, n = out
    assert n == 1
    assert np.isnan(new["inc"][1])
    assert new["inc"][0] == 100.0 and new["inc"][2] == 300.0


def test_the_input_is_not_modified():
    """The caller's array must survive - Stata reads columns once and
    may use them again."""
    original = np.array([100.0, CENSUS_SENTINEL])
    bag = {"inc": original}
    _quiet(blank_missing_codes, bag, [CENSUS_SENTINEL])
    assert original[1] == CENSUS_SENTINEL


def test_several_codes_at_once():
    bag = {"inc": np.array([1.0, -9.0, 999.0, 5.0])}
    (new, n), _ = _quiet(blank_missing_codes, bag, [-9, 999])
    assert n == 2
    assert np.isnan(new["inc"][1]) and np.isnan(new["inc"][2])


def test_no_codes_declared_changes_nothing():
    bag = {"inc": np.array([1.0, CENSUS_SENTINEL])}
    (new, n), _ = _quiet(blank_missing_codes, bag, None)
    assert n == 0
    assert new["inc"][1] == CENSUS_SENTINEL


def test_the_user_is_told_how_many_were_blanked():
    bag = {"inc": np.array([1.0, -9.0, -9.0])}
    _out, printed = _quiet(blank_missing_codes, bag, [-9])
    assert "2 values matched" in printed
    assert "still count as people" in printed


# --------------------------------------------------------------------
# John's ruling: a blanked case is still a person, and the denominator
# is the OBSERVED part
# --------------------------------------------------------------------

def _six_cells(group_values):
    x = np.arange(6) * 1000.0
    y = np.zeros(6)
    w = np.full(6, 100.0)
    return x, y, w, {"grp": np.asarray(group_values, dtype=float)}


def test_a_blanked_case_still_counts_as_people_towards_k():
    """His words: it 'could still be the placeholder for results - it
    just doesn't contribute self'."""
    x, y, w, treat = _six_cells(
        [30, 30, CENSUS_SENTINEL, 30, CENSUS_SENTINEL, 30])
    res, _ = _quiet(knn_to_rows, x, y, [600], treat=treat, weight=w,
                    treat_are_counts=True, unit_size=100.0,
                    missing_codes=[CENSUS_SENTINEL])
    assert res["N_600"][0] == pytest.approx(600.0), (
        "the two blanked cells stopped being people - they should "
        "still count towards k")


def test_the_share_divides_by_the_observed_part():
    """John's ruling: 400 people, 60 of unknown group -> denominator
    340, never 400.

    Four observed cells of 100 people, each 30 of the group; two cells
    blanked. The share is 120/400, not 120/600.
    """
    x, y, w, treat = _six_cells(
        [30, 30, CENSUS_SENTINEL, 30, CENSUS_SENTINEL, 30])
    res, _ = _quiet(knn_to_rows, x, y, [600], treat=treat, weight=w,
                    treat_are_counts=True, unit_size=100.0,
                    missing_codes=[CENSUS_SENTINEL])
    assert res["T_grp_600"][0] == pytest.approx(120.0)
    assert res["R_grp_600"][0] == pytest.approx(0.30), (
        "the share used everybody present as the denominator instead "
        "of the people actually observed")


def test_a_blanked_case_still_receives_its_own_results():
    x, y, w, treat = _six_cells(
        [30, 30, CENSUS_SENTINEL, 30, CENSUS_SENTINEL, 30])
    res, _ = _quiet(knn_to_rows, x, y, [600], treat=treat, weight=w,
                    treat_are_counts=True, unit_size=100.0,
                    missing_codes=[CENSUS_SENTINEL])
    assert np.isfinite(res["N_600"][2]), (
        "the blanked row lost its own answers - it is a placeholder "
        "for results, not an absent case")


def test_an_undeclared_sentinel_is_refused_and_points_at_the_option():
    """The safety net beneath the option.

    A user who does not know about missing() should not receive a
    quietly poisoned mean. Found in 1.38: the "bigger than the
    population" check could not see this, because -666666666 is
    comfortably SMALLER than any population. A count that is negative
    is impossible on its own terms.
    """
    x, y, w, treat = _six_cells(
        [30, 30, CENSUS_SENTINEL, 30, CENSUS_SENTINEL, 30])
    with pytest.raises(ValueError) as exc:
        _quiet(knn_to_rows, x, y, [600], treat=treat, weight=w,
               treat_are_counts=True, unit_size=100.0)
    text = str(exc.value)
    assert "cannot be negative" in text
    assert "missing(" in text, (
        "the refusal must name the option that fixes it - a user who "
        "did not know missing() exists is exactly who trips this")


def test_blanking_happens_before_the_treatment_guard():
    """Order matters. A sentinel judged as a group count is refused for
    being negative, and the user is told to check their treatment
    variable when what they actually needed was missing()."""
    x, y, w, treat = _six_cells(
        [30, 30, CENSUS_SENTINEL, 30, CENSUS_SENTINEL, 30])
    res, _ = _quiet(knn_to_rows, x, y, [600], treat=treat, weight=w,
                    treat_are_counts=True, unit_size=100.0,
                    missing_codes=[CENSUS_SENTINEL])
    assert res["T_grp_600"][0] == pytest.approx(120.0)


# --------------------------------------------------------------------
# The door
# --------------------------------------------------------------------

def _ado():
    with open(os.path.join(STATA_DIR, "equipop.ado"), encoding="utf-8") as f:
        return f.read()


def test_the_door_offers_the_option_and_passes_it_on():
    t = _ado()
    assert "MISSing(numlist)" in t, "no missing() box on the syntax line"
    assert 'missing="`missing\'"' in t, "missing() is not passed through"
    assert "missing_codes=" in t, "the bridge is never told"


def test_the_names_are_all_checked_before_any_variable_is_created():
    """External review of 1.36, P1.

    The check used to live inside the writing loop, so a collision on
    the tenth variable left nine already in the dataset - a run that
    errored and changed the data anyway.
    """
    t = _ado()
    block = t[t.index("existing = [Data.getVarName"):]
    preflight = block.index("problems")
    creation = block.index("Data.addVarDouble")
    assert preflight < creation, (
        "a variable is created before every intended name has been "
        "checked")


def test_the_preflight_checks_the_stata_name_limit():
    """prefix() was only tested against N_1, which proves nothing about
    T_<longvariablename>_100."""
    t = _ado()
    assert re.search(r"len\(name\)\s*>\s*32", t), (
        "nothing checks Stata's 32-character variable name limit")


def test_the_preflight_reports_every_problem_not_just_the_first():
    t = _ado()
    assert "problems[:10]" in t and "more" in t, (
        "the user should learn about all the clashes at once, not one "
        "per run")
