"""The treatment contract - external review of 1.36, P0.

REPRODUCED BEFORE IT WAS FIXED. The help and both GIS doors said
treat() holds the group's person count at each point. The Stata bridge
applied the legacy rule, in which treat is a 0/1 flag multiplied by the
population. A user who followed the help, with a population of 100 and
a group count of 30, received:

    N_100 = 100     T_group_100 = 3000     R_group_100 = 30.0

A group three times larger than the neighbourhood containing it, and a
share of 3000%. Nothing stopped. unit() is the cell size and does not
scale R, so there is no reading of those numbers that is correct.

John's ruling, v1.37.1: counts are the default, matching the help and
the GIS doors; the flag rule stays available by name; and a group
larger than its own population is refused rather than reported.
"""

import numpy as np
import pytest

from equipop.stata_bridge import (check_results_are_possible,
                                  knn_to_rows,
                                  validate_treatment)


X = np.array([0.0, 1000.0, 2000.0, 3000.0, 4000.0])
Y = np.zeros(5)


def _run(**kw):
    return knn_to_rows(X, Y, [100], unit_size=100.0, **kw)


def test_the_reviewers_case_now_gives_the_arithmetic_the_help_promises():
    """Population 100, group count 30, k=100.

    This is the exact configuration from the review, and the shape of
    the Bristol demonstration data: race counts from B02001 alongside a
    population column.
    """
    res = _run(treat={"group": np.full(5, 30.0)},
               weight=np.full(5, 100.0), treat_are_counts=True)
    assert res["N_100"][0] == pytest.approx(100.0)
    assert res["T_group_100"][0] == pytest.approx(30.0)
    assert res["R_group_100"][0] == pytest.approx(0.30)


def test_the_old_rule_still_works_when_asked_for_by_name():
    """Nothing already written should break. A 0/1 marker on weighted
    rows is a legitimate way to hold this data and stays available."""
    res = _run(treat={"group": np.ones(5)}, weight=np.full(5, 100.0),
               treat_are_counts=False)
    assert res["T_group_100"][0] == pytest.approx(100.0)
    assert res["R_group_100"][0] == pytest.approx(1.0)


def test_counts_sent_through_the_flag_rule_are_refused():
    """The defect itself, at the door the user meets."""
    with pytest.raises(ValueError) as exc:
        _run(treat={"group": np.full(5, 30.0)},
             weight=np.full(5, 100.0), treat_are_counts=False)
    text = str(exc.value)
    assert "treatmode(counts)" in text
    assert "0 or 1" in text


def test_counts_without_a_population_are_refused():
    """N would count ROWS while T summed PEOPLE - shares above 1 with
    no weight in sight. Previously a printed hint that scrolled past."""
    with pytest.raises(ValueError) as exc:
        _run(treat={"group": np.full(5, 30.0)}, weight=None,
             treat_are_counts=True)
    text = str(exc.value)
    assert "pop(" in text or "fweight" in text
    assert "treatmode(flags)" in text


def test_a_group_larger_than_its_population_is_refused():
    with pytest.raises(ValueError) as exc:
        _run(treat={"group": np.full(5, 130.0)},
             weight=np.full(5, 100.0), treat_are_counts=True)
    text = str(exc.value)
    assert "cannot be bigger" in text
    assert "5 of 5 points" in text


def test_the_refusal_names_how_many_and_by_how_much():
    """A user has to be able to tell one bad row from a wrong variable."""
    treat = {"group": np.array([10.0, 10.0, 10.0, 10.0, 300.0])}
    with pytest.raises(ValueError) as exc:
        _run(treat=treat, weight=np.full(5, 100.0), treat_are_counts=True)
    assert "1 of 5 points" in str(exc.value)


def test_a_flag_outside_zero_and_one_is_refused():
    with pytest.raises(ValueError) as exc:
        validate_treatment({"g": np.array([0.0, 1.0, 2.0])},
                           np.full(3, 10.0), treat_are_counts=False)
    assert "0 or 1" in str(exc.value)


def test_a_legitimate_fractional_flag_is_allowed():
    """A row that is 30% of one group is a share, not an error - the
    legacy rule's own arithmetic depends on it."""
    validate_treatment({"g": np.array([0.0, 0.3, 1.0])},
                       np.full(3, 10.0), treat_are_counts=False)


def test_missing_values_do_not_trip_the_guards():
    """John's field data had rows with no coordinates and blanked
    incomes. A guard that fires on missing data would be useless."""
    treat = {"g": np.array([10.0, np.nan, 10.0, 10.0, 10.0])}
    w = np.array([100.0, 100.0, np.nan, 100.0, 100.0])
    validate_treatment(treat, w, treat_are_counts=True)


def test_no_treatment_at_all_is_fine():
    validate_treatment({}, np.full(3, 10.0), treat_are_counts=True)
    validate_treatment(None, None, treat_are_counts=True)


# --------------------------------------------------------------------
# The backstop on the way OUT
# --------------------------------------------------------------------

def test_the_backstop_catches_an_impossible_result():
    """Independent of how the input was checked. A guard on the input
    can be defeated by an engine change; this one reads the number the
    user is about to be handed."""
    with pytest.raises(ValueError) as exc:
        check_results_are_possible({
            "N_100": np.array([100.0, 100.0]),
            "T_g_100": np.array([30.0, 3000.0]),
        })
    text = str(exc.value)
    assert "T_g_100" in text and "N_100" in text
    assert "impossible" in text


def test_the_backstop_passes_a_correct_result():
    check_results_are_possible({
        "N_100": np.array([100.0, 100.0]),
        "T_g_100": np.array([30.0, 100.0]),
        "Dist_100": np.array([56.4, 56.4]),
    })


def test_the_backstop_tolerates_floating_point_but_not_real_excess():
    """Summation of many weights drifts in the last bits. A guard that
    fired on 1e-12 would be noise; one that missed 0.5 people would be
    useless."""
    check_results_are_possible({
        "N_100": np.array([100.0]),
        "T_g_100": np.array([100.0 + 1e-10]),
    })
    with pytest.raises(ValueError):
        check_results_are_possible({
            "N_100": np.array([100.0]),
            "T_g_100": np.array([100.5]),
        })


def test_the_backstop_ignores_missing_and_unmatched_columns():
    check_results_are_possible({
        "N_100": np.array([100.0, np.nan]),
        "T_g_100": np.array([np.nan, 50.0]),
        "T_g_r500": np.array([1e9, 1e9]),      # no N_r500 to compare
    })
