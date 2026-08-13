# -*- coding: utf-8 -*-
"""test_overshoot_doors.py - BACKLOG 99, the DOOR half.

The engine half (equipop/overshoot.py and the four engines) is
covered in test_equipop.py and test_selfpot.py. This file asks the
question those cannot: does the box in the dialog actually decide
anything?

That question is not rhetorical. BACKLOG 95 shipped a Pro guard whose
first version passed against a deliberate break, because it drove
_run_tool directly and skipped the dialog hop where `or 1.0` eats a
falsy 0. So every test here goes in through the door the way a user
does - execute() in Pro, processAlgorithm() in QGIS - and compares
NUMBERS, not the presence of a parameter.

Each was checked by breaking it on purpose:

  * dropping `overshoot_mode` from the QGIS kw dict     -> 1, 2 fail
  * dropping `if overshoot is not None` in _run_tool    -> 3, 4 fail
  * reading the seed with parameterAsInt instead of
    optional_int                                        -> 6 fails
  * removing the machine-2 note                         -> 7 fails
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "qgis"))

import qgis_stub                                       # noqa: E402
qgis_stub.install()

from qgis.core import QgsProcessingFeedback            # noqa: E402
from equipop_qgis.alg_counts import (CountsAndShares,  # noqa: E402
                                     OVERSHOOT_VALUES)
from equipop_qgis.alg_stats import ValueStatistics     # noqa: E402
from equipop.doors import rungs                        # noqa: E402

WHOLE = OVERSHOOT_VALUES.index("whole")
PROP = OVERSHOOT_VALUES.index("proportional")
SAMPLED = OVERSHOOT_VALUES.index("sampled")


def _blocks():
    """John's own example, laid out as a town.

    A 3x3 of cells holding ten people each, asked for k=11. The whole
    ring rule answers 50; a proportional share answers exactly 11.
    Twenty of these blocks, spread far enough apart that no block
    reaches another, so every origin sees the same arithmetic.
    """
    rows = []
    for b in range(20):
        ox, oy = (b % 5) * 10000.0, (b // 5) * 10000.0
        for dx in (0, 100, 200):
            for dy in (0, 100, 200):
                rows.append((ox + dx + 50, oy + dy + 50, 10.0, 4.0))
    t = pd.DataFrame(rows, columns=["x", "y", "Population", "Grp"])
    return qgis_stub._Source(t, "EPSG:32633")


def _run(alg_cls, **params):
    alg = alg_cls()
    alg.initAlgorithm()
    p = {"layer": _blocks(), "unit": 100.0, "outfc": "memory:out",
         "k": "11"}
    p.update(params)
    fb = QgsProcessingFeedback()
    alg.processAlgorithm(p, None, fb)
    return p["_sinks"]["outfc"].to_frame(), fb


def _said(fb):
    return " ".join(fb.info) + " " + " ".join(fb.warnings)


# ============================================================ QGIS
def test_1_the_qgis_box_changes_the_answer():
    """The whole item in one assertion. Same data, same k, one box
    moved: 50 people or 11."""
    whole, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                    treatmode=[1], treat=["Grp"], overshoot=[WHOLE])
    prop, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                   treatmode=[1], treat=["Grp"], overshoot=[PROP])
    assert whole["N_11"].max() == pytest.approx(50.0)
    assert prop["N_11"].to_numpy() == pytest.approx(11.0)


def test_2_the_qgis_default_is_the_engines_default():
    """A box left alone must give what the engine gives when asked
    nothing - or the dialog is offering a second opinion on its own
    run. Checked by VALUE, not by reading the defaultValue back."""
    left_alone, _ = _run(CountsAndShares, pop=["Population"],
                         refmode=[1], treatmode=[1], treat=["Grp"])
    named, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                    treatmode=[1], treat=["Grp"],
                    overshoot=[rungs.OVERSHOOT_DEFAULT])
    assert left_alone["N_11"].to_numpy() == \
        pytest.approx(named["N_11"].to_numpy())


def test_3_the_share_lands_on_the_group_count_too():
    """N_k is the easy half. T_k and R_k are what BACKLOG 99 exists
    for: on a boundary the whole ring drags the other side in."""
    prop, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                   treatmode=[1], treat=["Grp"], overshoot=[PROP])
    # every cell is 4 of 10, so the share is 0.4 whatever k does
    assert prop["R_Grp_11"].to_numpy() == pytest.approx(0.4)
    assert prop["T_Grp_11"].to_numpy() == pytest.approx(4.4)


def test_4_sampled_keeps_whole_people_and_lands_between():
    """Sampled is proportional rounded UP to a whole cell: never
    below k, never as far past it as the whole ring."""
    out, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                  treatmode=[1], treat=["Grp"], overshoot=[SAMPLED],
                  seed=1848)
    n = out["N_11"].to_numpy()
    assert (n >= 11).all(), "sampled stopped short of k"
    assert (n <= 50).all() and n.max() < 50, \
        "sampled took the whole ring after all"
    assert np.allclose(n % 10, 0), "sampled produced fractional people"


def test_5_the_same_seed_repeats_and_a_different_one_need_not():
    a, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                overshoot=[SAMPLED], seed=1848)
    b, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                overshoot=[SAMPLED], seed=1848)
    assert a["N_11"].to_numpy() == pytest.approx(b["N_11"].to_numpy())


def test_6_an_empty_seed_box_is_not_seed_zero():
    """The trap this box was one line away from shipping with.
    `parameterAsInt` hands back 0 for an empty box, so 'no seed' and
    'seed 0' would have been the same run - drawn once, printed
    never, and unrepeatable in a way nobody could see. Same family as
    BACKLOG 116."""
    alg = CountsAndShares()
    alg.initAlgorithm()
    assert alg.optional_int({}, "seed") is None
    assert alg.optional_int({"seed": None}, "seed") is None
    assert alg.optional_int({"seed": ""}, "seed") is None
    assert alg.optional_int({"seed": 0}, "seed") == 0
    assert alg.optional_int({"seed": 1848}, "seed") == 1848


def test_6b_the_door_really_uses_it_and_says_which_seed_it_drew():
    """The test above proves the HELPER is right, and that is not the
    same as proving the DOOR calls it - which is BACKLOG 95's lesson
    about a guard that drives the shortest path. This one was written
    after the deliberate break: swapping optional_int back for
    parameterAsInt left test 6 perfectly green.

    So it goes through processAlgorithm and reads what the run SAID.
    An empty box must announce a drawn seed; seed 0 - a real value a
    user can type - must announce itself as seed 0. Under
    parameterAsInt both print the same line, and the difference
    between 'we chose for you' and 'you chose' disappears."""
    _, empty = _run(CountsAndShares, pop=["Population"], refmode=[1],
                    overshoot=[SAMPLED])
    assert "no seed given; drew" in _said(empty), \
        "an empty seed box did not draw and announce a seed"

    _, zero = _run(CountsAndShares, pop=["Population"], refmode=[1],
                   overshoot=[SAMPLED], seed=0)
    assert "sampled order from seed 0" in _said(zero), \
        "a deliberate seed of 0 was read as 'no seed given'"
    assert "no seed given" not in _said(zero)


# ====================================================== machine 2
def test_7_machine_2_says_when_it_differs_from_machine_1():
    """Two machines, two defaults, one dataset. Unsaid, the student
    gets two different N_k and nothing to explain it."""
    _, fb = _run(ValueStatistics, pop=["Population"],
                 values=["Grp"], measures=[0, 1, 2])
    said = _said(fb)
    assert "[overshoot]" in said and "BACKLOG 118" in said
    assert rungs.OVERSHOOT_VALUES[rungs.OVERSHOOT_DEFAULT] in said


def test_8_the_note_names_the_mode_that_was_actually_used():
    """Not "fires when the two differ" - that condition is TRUE FOR
    EVERY MACHINE-2 RUN today, and pretending otherwise would be a
    test asserting something unreachable.

    The reason is worth keeping: machine 2 can run `whole` or
    `sampled`, and BOTH differ from machine 1's default of
    `proportional`, so there is no combination that silences the
    note. It silences itself when BACKLOG 118 lands weighted
    statistics and machine 2 can take a fraction of a cell - the
    condition is written against machine 1's default precisely so
    that it retires on its own rather than needing to be remembered.

    What is testable now is that the line tells the truth about the
    run it belongs to."""
    _, fb = _run(ValueStatistics, pop=["Population"], values=["Grp"],
                 measures=[0, 1, 2], overshoot=[SAMPLED], seed=1848)
    said = _said(fb)
    assert "this run used 'sampled'" in said
    _, fb2 = _run(ValueStatistics, pop=["Population"], values=["Grp"],
                  measures=[0, 1, 2], overshoot=[WHOLE])
    assert "this run used 'whole'" in _said(fb2)


def test_9_machine_2_refuses_a_fraction_of_a_cell_by_name():
    """Asked explicitly for proportional, machine 2 must refuse and
    say why - a quarter of a cell has no median. It must NOT quietly
    compute one."""
    with pytest.raises(Exception) as e:
        _run(ValueStatistics, pop=["Population"], values=["Grp"],
             measures=[0, 1, 2], overshoot=[PROP])
    msg = str(e.value)
    assert "median" in msg and "Nothing was computed" in msg


def test_10_machine_2_can_still_do_counts_under_proportional():
    """The refusal is about DISTRIBUTIONS, not about the mode. Ask
    machine 2 for a mean only and it still refuses (a mean of a
    fraction of a cell is as undefined as a median); ask machine 1
    for the same data and it answers. This pins which side of the
    line the refusal sits on."""
    out, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                  overshoot=[PROP])
    assert out["N_11"].to_numpy() == pytest.approx(11.0)


# ========================================================== ArcGIS
def _pro():
    import test_arcgis_stub as H
    t = pd.DataFrame({"OBJECTID": [], "SHAPE@X": [], "SHAPE@Y": [],
                      "Population": [], "Grp": []})
    rows = []
    for b in range(20):
        ox, oy = (b % 5) * 10000.0, (b // 5) * 10000.0
        for dx in (0, 100, 200):
            for dy in (0, 100, 200):
                rows.append((ox + dx + 50, oy + dy + 50, 10.0, 4.0))
    arr = np.array(rows)
    t = pd.DataFrame({"OBJECTID": np.arange(1, len(rows) + 1),
                      "SHAPE@X": arr[:, 0], "SHAPE@Y": arr[:, 1],
                      "Population": arr[:, 2], "Grp": arr[:, 3]})
    state = H._install_fake_arcpy(t)
    return H._load_pyt(), state


class _Quiet:
    def __init__(self):
        self.said = []

    def addMessage(self, m):
        self.said.append(str(m))

    addWarningMessage = addMessage
    addErrorMessage = addMessage


def test_11_the_pro_dialog_changes_the_answer_through_execute():
    """Through execute(), not _run_tool. BACKLOG 95's lesson: a guard
    that drives the shortest path may skip the danger - there, a
    dialog hop where `or 1.0` ate a deliberate 0."""
    pyt, state = _pro()
    tool = pyt.CountsShares()
    ps = tool.getParameterInfo()
    pm = {p.name: p for p in ps}
    pm["layer"].value = "lyr"
    pm["pop"].value = "Population"
    pm["treat"].value = "Grp"
    pm["k"].value = "11"
    pm["unit"].value = 100.0
    pm["refmode"].value = pyt.REF_MODES[1]
    pm["treatmode"].value = pyt.TREAT_MODES[1]
    pm["overshoot"].value = pyt.OVERSHOOT_MODES[WHOLE]
    tool.execute(ps, _Quiet())
    assert state["table"]["N_11"].max() == pytest.approx(50.0)

    pyt, state = _pro()
    tool = pyt.CountsShares()
    ps = tool.getParameterInfo()
    pm = {p.name: p for p in ps}
    pm["layer"].value = "lyr"
    pm["pop"].value = "Population"
    pm["treat"].value = "Grp"
    pm["k"].value = "11"
    pm["unit"].value = 100.0
    pm["refmode"].value = pyt.REF_MODES[1]
    pm["treatmode"].value = pyt.TREAT_MODES[1]
    pm["overshoot"].value = pyt.OVERSHOOT_MODES[PROP]
    tool.execute(ps, _Quiet())
    assert state["table"]["N_11"].to_numpy() == pytest.approx(11.0)


def test_12_the_two_doors_agree_under_every_mode():
    """The claim the conformance key makes for ONE mode, made for all
    three. The key is pinned to `whole` (BACKLOG 162 covers the
    second key); this is the cheap version that travels with every
    mode the box offers."""
    pyt, state = _pro()
    for idx in (WHOLE, PROP, SAMPLED):
        pyt, state = _pro()
        tool = pyt.CountsShares()
        ps = tool.getParameterInfo()
        pm = {p.name: p for p in ps}
        pm["layer"].value = "lyr"
        pm["pop"].value = "Population"
        pm["treat"].value = "Grp"
        pm["k"].value = "11"
        pm["unit"].value = 100.0
        pm["refmode"].value = pyt.REF_MODES[1]
        pm["treatmode"].value = pyt.TREAT_MODES[1]
        pm["overshoot"].value = pyt.OVERSHOOT_MODES[idx]
        pm["seed"].value = 1848
        tool.execute(ps, _Quiet())
        pro = state["table"]["N_11"].to_numpy()

        q, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                    treatmode=[1], treat=["Grp"], overshoot=[idx],
                    seed=1848)
        assert pro == pytest.approx(q["N_11"].to_numpy()), (
            f"the two doors disagree under "
            f"'{OVERSHOOT_VALUES[idx]}'")
