"""BACKLOG 42/99/102 in Stata - the last of the analytical boxes.

These are menu work: the engine has taken decay, a variable bandwidth,
the overshoot mode and the self-potential since well before Stata could
ask for any of them. What is tested here is the DOOR - that each box
reaches the engine, that the refusals are refusals, and that the words
mean what the GIS doors mean by them.

The `.ado` cannot be executed here, so the door half is PARSED. The
engine half is exercised directly.
"""

import os
import re

import numpy as np
import pytest

from equipop.doors import rungs
from equipop.stata_bridge import knn_to_rows

STATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stata")


def _ado():
    with open(os.path.join(STATA_DIR, "equipop.ado"), encoding="utf-8") as f:
        return f.read()


def _program():
    t = _ado()
    start = t.index("program define equipop,")
    return t[start:t.index("\nend", start)]


# --------------------------------------------------------------------
# The overshoot - BACKLOG 99
# --------------------------------------------------------------------

def test_sampled_is_refused_by_name_not_ignored():
    """John's ruling, and his reason: sampled exists only to reproduce
    older versions of EquiPop, so it is not a Stata concern.

    Refusing it BY NAME matters. Silently ignoring an option the user
    typed changes the numbers without telling them, and this is the one
    mode whose numbers differ from proportional in a way that is not
    noise - proportional is not the expected value of sampled, which
    was measured, not assumed.
    """
    body = _program()
    assert '"`overshoot\'" == "sampled"' in body, (
        "sampled is not detected by name")
    hit = body[body.index('"`overshoot\'" == "sampled"'):][:900]
    assert "exit 198" in hit, "sampled is detected but not refused"
    assert "QGIS" in hit or "ArcGIS" in hit, (
        "the refusal should point at the doors that do offer it")


def test_the_sampled_refusal_explains_why_rather_than_just_refusing():
    body = _program()
    hit = body[body.index('"`overshoot\'" == "sampled"'):][:900]
    assert "random" in hit and "seed" in hit, (
        "a user told only 'not available' will assume it is an "
        "oversight and ask for it")


def test_only_the_two_supported_modes_are_accepted():
    body = _program()
    assert 'inlist("`overshoot\'", "", "whole", "proportional")' in body


def test_the_two_modes_reach_the_engine_and_change_the_answer():
    """A box that does not change the answer is not wired up.

    The overshoot is the ring of cells that crosses k, so the modes can
    only differ where k falls inside a ring rather than on a boundary.
    """
    rng = np.random.default_rng(5)
    n = 300
    x = rng.uniform(0, 3000, n)
    y = rng.uniform(0, 3000, n)
    w = rng.integers(1, 20, n).astype(float)
    treat = {"g": np.floor(w * rng.uniform(0, 1, n))}

    whole = knn_to_rows(x, y, [250], treat=treat, weight=w,
                        treat_are_counts=True, unit_size=100.0,
                        overshoot_mode="whole")
    prop = knn_to_rows(x, y, [250], treat=treat, weight=w,
                       treat_are_counts=True, unit_size=100.0,
                       overshoot_mode="proportional")
    assert not np.allclose(whole["N_250"], prop["N_250"],
                           equal_nan=True), (
        "both overshoot modes produced identical counts - the option "
        "is not reaching the engine")


# --------------------------------------------------------------------
# Decay - BACKLOG 42/102
# --------------------------------------------------------------------

def test_decay_needs_a_bandwidth_and_says_which_boxes_give_one():
    body = _program()
    assert '"negexp", "expnormal", "expsqrt"' in body
    assert "halflife" in body and "halflifevar" in body
    hit = body[body.index("decay() needs a half-life"):][:600]
    assert "halflife(#)" in hit and "halflifevar(var)" in hit, (
        "the refusal must name both ways of supplying a bandwidth")


def test_a_bandwidth_without_decay_is_refused():
    """The other direction, which is the easier mistake: setting a
    half-life and forgetting the model, then wondering why nothing
    changed."""
    body = _program()
    assert "halflife() sets the bandwidth" in body


def test_both_bandwidths_at_once_are_refused():
    body = _program()
    assert "not both" in body


def test_the_three_models_are_the_engine_s_three():
    from equipop.decay import MODELS
    body = _program()
    for model in MODELS:
        assert f'"{model}"' in body, (
            f"the engine offers {model} and the door does not")


def test_decay_adds_a_column_and_leaves_the_k_results_alone():
    """What decay actually DOES here, established by measurement.

    It does not reweight the k-neighbourhood. It adds a distance-
    weighted total over everybody - a column beginning ND_ - and N_k
    and Dist_k come back identical. The two answer different questions
    and sit side by side.

    This was written the other way round first, assuming decay would
    move Dist_k, and the test failed. The help text had to be
    corrected, not the code.
    """
    rng = np.random.default_rng(9)
    n = 300
    x = rng.uniform(0, 5000, n)
    y = rng.uniform(0, 5000, n)
    w = rng.integers(1, 20, n).astype(float)

    from equipop.decay import Decay
    plain = knn_to_rows(x, y, [200], weight=w, unit_size=100.0)
    faded = knn_to_rows(x, y, [200], weight=w, unit_size=100.0,
                        decay=Decay(model="negexp", half_life_m=500))

    new = set(faded) - set(plain)
    assert new, "decay produced no extra column - the option is not wired"
    assert any(c.startswith("ND_") for c in new), (
        f"expected a decayed total beginning ND_, got {sorted(new)}")
    assert np.allclose(plain["N_200"], faded["N_200"], equal_nan=True)
    assert np.allclose(plain["Dist_200"], faded["Dist_200"],
                       equal_nan=True)


def test_the_help_states_johns_rule_about_k():
    """The wording has been wrong twice now, in opposite directions.

    It must say that k still means the k nearest people, that the
    radius is unchanged, and that the decayed totals are therefore
    smaller - which is the whole of the rule.
    """
    from equipop.doors import help as door_help
    text = door_help.HELP["decaymodel"]
    assert "ND_" in text and "TD_" in text and "RD_" in text
    assert "UNCHANGED" in text
    assert "always smaller" in text


# --------------------------------------------------------------------
# Self-potential - three rungs, not two
# --------------------------------------------------------------------

def test_the_ladder_has_the_same_three_rungs_as_the_gis_doors():
    """John corrected this directly: there are three, not two."""
    assert len(rungs.SELF_POTENTIAL_VALUES) == 3
    assert rungs.SELF_POTENTIAL_VALUES == [0.0, 2 ** -0.5, 1.0]


def test_all_three_rung_names_are_accepted_by_the_door():
    body = _program()
    for name in ("none", "median", "full"):
        assert f'"{name}"' in body, f"rung {name} is missing"


def test_the_rung_names_carry_the_engine_s_own_numbers():
    """A name that resolved to a different number than the GIS doors
    use would be parity of vocabulary without parity of behaviour -
    the exact failure door_parity cannot see."""
    body = _program()
    assert "local selfpot = 0" in body
    assert "1/sqrt(2)" in body
    assert "local selfpot = 1" in body


def test_the_free_number_still_works():
    """The escape hatch. Anything already written keeps running, and
    the engine parameter stays a float either way."""
    body = _program()
    assert "SELFpot(real 1)" in body
    assert "`selfpot' < 0 | `selfpot' > 1" in body


def test_a_bad_rung_name_lists_the_real_ones():
    body = _program()
    hit = body[body.index("selfpotname() must be"):][:700]
    for name in ("none", "median", "full"):
        assert name in hit


# --------------------------------------------------------------------
# Every new box is passed on, not just accepted
# --------------------------------------------------------------------

@pytest.mark.parametrize("box,engine", [
    ("decay", "decay="),
    ("halflifevar", "decay_half_life="),
    ("bins", "decay_bins="),
    ("overshoot", "overshoot_mode="),
])
def test_each_box_reaches_the_engine(box, engine):
    """BACKLOG 148's lesson: a parameter no call site passes is a
    feature that silently does not exist."""
    t = _ado()
    assert f'{box}="`{box}\'"' in t or f"{box}=`{box}'" in t, (
        f"{box} is never passed out of the .ado")
    assert engine in t, f"{box} never reaches the engine as {engine}"
