# -*- coding: utf-8 -*-
"""test_missing_codes.py - BACKLOG 168.

John, field, 1.31, on the Census sentinel -666666666 sitting in 64 of
his 1074 Bristol County rows:

    "The sentinels are likely what I would refer to as missing values
    that have representations (usually different depending on the
    cause for missing) - the cause is unimportant, but the
    possibility to dismiss/exclude those values would be of
    importance. ... when a case with this kind of value is reached
    the treatment value is not included (it could still be the
    placeholder for results - it just doesn't contribute self)"

Three claims follow from that, and each has a test here:

  1. the value drops out of the arithmetic
  2. the case STILL counts as a person towards k, and still receives
     its own results - it is not deleted, it just contributes nothing
  3. a SHARE is divided by the people actually observed. John's
     ruling on the worked example: of 400 people with 60 whose group
     is unknown, the denominator is 340, never 400. Dividing by 400
     quietly assumes those 60 were not in the group.
"""
import numpy as np
import pytest

from equipop.stata_bridge import dispatch

SENTINEL = -666666666.0


def _line(vals, pop=10):
    x = np.repeat(np.arange(len(vals)) * 100.0 + 50.0, pop)
    y = np.full(len(vals) * pop, 50.0)
    v = np.repeat(np.asarray(vals, dtype=float), pop)
    return x, y, v


def test_a_sentinel_left_undeclared_still_wrecks_the_answer():
    """The thing being protected against, stated first. This is not
    EquiPop misbehaving - it is arithmetic doing what it is told - and
    it is why the feature exists rather than a warning."""
    x, y, v = _line([100, SENTINEL, 300, 500])
    got = dispatch("stats", x, y, unit_size=100.0, k_values=[40],
                   values={"inc": v}, stats={"inc": ["mean"]},
                   overshoot_mode="whole")
    assert got["Mean_inc_40"][0] < -1e8


def test_declaring_it_removes_the_value_and_nothing_else():
    x, y, v = _line([100, SENTINEL, 300, 500])
    got = dispatch("stats", x, y, unit_size=100.0, k_values=[40],
                   values={"inc": v}, stats={"inc": ["mean"]},
                   overshoot_mode="whole", missing_codes=[SENTINEL])
    # mean of 100, 300, 500 - the sentinel gone, the rest untouched
    assert got["Mean_inc_40"][0] == pytest.approx(300.0)
    # every ORIGIN still gets an answer, including the blanked cell
    assert len(got["Mean_inc_40"]) == 40
    assert np.isfinite(got["Mean_inc_40"]).all()


def test_the_case_still_counts_as_a_person_towards_k():
    """The half of John's ruling that is easy to get wrong: dropping
    the VALUE must not drop the PERSON. If it did, k would be reached
    further out and every distance would change."""
    x, y, v = _line([100, SENTINEL, 300, 500])
    kw = dict(unit_size=100.0, k_values=[40], values={"inc": v},
              stats={"inc": ["mean"]}, overshoot_mode="whole")
    plain = dispatch("stats", x, y, **kw)
    coded = dispatch("stats", x, y, **dict(kw, missing_codes=[SENTINEL]))
    assert coded["N_40"] == pytest.approx(plain["N_40"]), \
        "declaring a missing code changed who is in the neighbourhood"
    assert coded["Dist_40"] == pytest.approx(plain["Dist_40"]), \
        "declaring a missing code moved the neighbourhood's radius"
    # but the evidence behind the statistic is smaller, and says so
    assert coded["Nv_inc_40"][0] == 30.0
    assert plain["Nv_inc_40"][0] == 40.0


def test_a_share_divides_by_the_observed_part_not_by_everybody():
    """John's ruling, on his own worked example: 400 people, 60 of
    unknown group, denominator 340.

    Here: 40 people, 10 of unknown group, 10 in the group. Dividing
    by the observed 30 gives 1/3; dividing by all 40 gives 1/4. The
    second silently counts the unknown ten as not-in-the-group.
    """
    x, y, _ = _line([0, 0, 0, 0])
    grp = np.concatenate([np.full(10, 1.0),        # in the group
                          np.full(10, SENTINEL),   # unknown
                          np.full(20, 0.0)])       # not in the group
    got = dispatch("counts", x, y, unit_size=100.0, k_values=[40],
                   treat={"grp": grp}, treat_are_counts=True,
                   overshoot_mode="whole", missing_codes=[SENTINEL])
    assert got["R_grp_40"][0] == pytest.approx(1.0 / 3.0), (
        f"got {got['R_grp_40'][0]:.4f}; 0.25 means the denominator "
        "was everybody rather than the people observed")


def test_the_denominator_is_unchanged_when_nothing_is_declared():
    """The whole feature must be invisible to everyone not using it -
    this is what lets it ship without moving a single published
    number."""
    rng = np.random.default_rng(168)
    x = rng.uniform(0, 900, 400)
    y = rng.uniform(0, 900, 400)
    grp = rng.integers(0, 2, 400).astype(float)
    kw = dict(unit_size=100.0, k_values=[50], treat={"grp": grp},
              treat_are_counts=True, overshoot_mode="whole")
    a = dispatch("counts", x, y, **kw)
    b = dispatch("counts", x, y, **dict(kw, missing_codes=[-999999]))
    assert a["R_grp_50"] == pytest.approx(b["R_grp_50"])


def test_several_codes_can_be_declared_at_once():
    """Different causes of missingness carry different codes - John's
    point - so the list takes more than one."""
    x, y, v = _line([100, -666666666, 300, -999999999])
    got = dispatch("stats", x, y, unit_size=100.0, k_values=[40],
                   values={"inc": v}, stats={"inc": ["mean"]},
                   overshoot_mode="whole",
                   missing_codes=[-666666666, -999999999])
    assert got["Mean_inc_40"][0] == pytest.approx(200.0)


def test_a_code_that_matches_nothing_is_harmless():
    x, y, v = _line([100, 200, 300, 400])
    got = dispatch("stats", x, y, unit_size=100.0, k_values=[40],
                   values={"inc": v}, stats={"inc": ["mean"]},
                   overshoot_mode="whole", missing_codes=[-1])
    assert got["Mean_inc_40"][0] == pytest.approx(250.0)


def test_missing_codes_survive_a_proportional_run():
    """The two 1.31 features have to work together: a fraction of a
    cell whose value is missing contributes neither value nor
    denominator."""
    x, y, v = _line([100, SENTINEL, 300, 500])
    got = dispatch("stats", x, y, unit_size=100.0, k_values=[25],
                   values={"inc": v}, stats={"inc": ["mean"]},
                   overshoot_mode="proportional",
                   missing_codes=[SENTINEL])
    assert np.isfinite(got["Mean_inc_25"]).all()
    assert got["Nv_inc_25"][0] < 25.0, \
        "a blanked cell still contributed to the evidence count"
