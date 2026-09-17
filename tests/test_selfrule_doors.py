# -*- coding: utf-8 -*-
"""test_selfrule_doors.py - BACKLOG 290, the DOOR half.

The engine half is in test_selfrule.py. This file asks what that one
cannot: does the box in the dialog actually decide anything?

That question is not rhetorical here. BACKLOG 169's failure was an
option added to the Stata syntax line and to the call while the
Python def never heard of it - eleven releases of a box that did
nothing. And this box is the worst possible candidate for that bug,
because the AVERAGES BARELY MOVE under either rule: a door that
silently dropped the setting would produce entirely plausible
numbers. Nobody would notice. So every test here goes in through the
door the way a user does and compares NUMBERS.

Each was checked by breaking it on purpose:

  * dropping `self_rule` from the QGIS counts kw dict    -> 1, 2 fail
  * dropping it from the QGIS stats kw dict              -> 3 fails
  * dropping `if originrule is not None` in Pro's
    _run_tool                                            -> 4 fails
  * hard-coding ORIGIN_VALUES[0] in either door          -> 1, 3, 4 fail
  * removing "originrule" from door_parity.CORE          -> 5 fails
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "qgis"))

import qgis_stub                                        # noqa: E402
qgis_stub.install()

from qgis.core import QgsProcessingFeedback             # noqa: E402
from equipop_qgis.alg_counts import (CountsAndShares,   # noqa: E402
                                     ORIGIN_VALUES)
from equipop_qgis.alg_stats import ValueStatistics      # noqa: E402

INCLUDE = ORIGIN_VALUES.index("include")
EXCLUDE = ORIGIN_VALUES.index("exclude")


def _towns():
    """Isolated blocks, each one cell of 40 people holding all of the
    group, ringed by four cells of 40 holding none.

    Chosen so the rule cannot hide. Ask k=40 at the centre: with the
    origin counted the share is 1.0, without it the share is 0.0. No
    other setting in either door can produce that pair.
    """
    rows = []
    for b in range(12):
        ox, oy = (b % 4) * 20000.0, (b // 4) * 20000.0
        rows.append((ox, oy, 40.0, 40.0))           # centre: all group
        for dx, dy in ((100, 0), (-100, 0), (0, 100), (0, -100)):
            rows.append((ox + dx, oy + dy, 40.0, 0.0))
    t = pd.DataFrame(rows, columns=["x", "y", "Population", "Grp"])
    return qgis_stub._Source(t, "EPSG:32633")


def _run(alg_cls, **params):
    alg = alg_cls()
    alg.initAlgorithm()
    p = {"layer": _towns(), "unit": 100.0, "outfc": "memory:out",
         "k": "40"}
    p.update(params)
    fb = QgsProcessingFeedback()
    alg.processAlgorithm(p, None, fb)
    return p["_sinks"]["outfc"].to_frame(), fb


def _centres(df):
    """The twelve town centres - the rows holding the whole group."""
    return df[df["Grp_local"] > 0] if "Grp_local" in df.columns else df


# ============================================================ QGIS
def test_1_the_qgis_box_changes_the_answer():
    """The whole item in one assertion. Same data, same k, one box
    moved: every neighbour or every neighbour but yourself."""
    inc, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                  treatmode=[1], treat=["Grp"], originrule=[INCLUDE])
    exc, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                  treatmode=[1], treat=["Grp"], originrule=[EXCLUDE])
    assert inc["R_Grp_40"].max() == pytest.approx(1.0)
    assert exc["R_Grp_40"].min() == pytest.approx(0.0)
    assert not np.allclose(inc["R_Grp_40"].to_numpy(),
                           exc["R_Grp_40"].to_numpy(), equal_nan=True)


def test_2_the_qgis_default_is_the_engines_default():
    """A box left alone must give what the engine gives when asked
    nothing, or the dialog is offering a second opinion on its own
    run. Checked BY VALUE, not by reading defaultValue back - the
    published literature depends on this one."""
    left_alone, _ = _run(CountsAndShares, pop=["Population"],
                         refmode=[1], treatmode=[1], treat=["Grp"])
    named, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                    treatmode=[1], treat=["Grp"], originrule=[INCLUDE])
    assert left_alone["R_Grp_40"].to_numpy() == \
        pytest.approx(named["R_Grp_40"].to_numpy())


def test_3_machine_2_has_the_same_box_and_it_works():
    """Two machines that disagree about who a neighbour is would be
    BACKLOG 117 all over again."""
    inc, _ = _run(ValueStatistics, pop=["Population"], values=["Grp"],
                  measures=[0], originrule=[INCLUDE])
    exc, _ = _run(ValueStatistics, pop=["Population"], values=["Grp"],
                  measures=[0], originrule=[EXCLUDE])
    col = [c for c in inc.columns if c.endswith("_40")
           and c.split("_")[0] not in ("N", "Nv", "Dist")]
    assert col, f"no statistic column found in {list(inc.columns)}"
    a = inc[col[0]].to_numpy()
    b = exc[col[0]].to_numpy()
    assert not np.allclose(a, b, equal_nan=True), (
        "machine 2's box did not change anything")


def _pro():
    """The same towns, handed to Pro's fake arcpy."""
    import test_arcgis_stub as H
    rows = []
    for b in range(12):
        ox, oy = (b % 4) * 20000.0, (b // 4) * 20000.0
        rows.append((ox, oy, 40.0, 40.0))
        for dx, dy in ((100, 0), (-100, 0), (0, 100), (0, -100)):
            rows.append((ox + dx, oy + dy, 40.0, 0.0))
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


def _pro_run(rule_index):
    pyt, state = _pro()
    tool = pyt.CountsShares()
    ps = tool.getParameterInfo()
    pm = {p.name: p for p in ps}
    pm["layer"].value = "lyr"
    pm["pop"].value = "Population"
    pm["treat"].value = "Grp"
    pm["k"].value = "40"
    pm["unit"].value = 100.0
    pm["refmode"].value = pyt.REF_MODES[1]
    pm["treatmode"].value = pyt.TREAT_MODES[1]
    pm["originrule"].value = pyt.ORIGIN_MODES[rule_index]
    tool.execute(ps, _Quiet())
    return state["table"]


def test_4_the_pro_dialog_changes_the_answer_through_execute():
    """Through execute(), not _run_tool. BACKLOG 95's lesson: a guard
    that drives the shortest path may skip the danger - there, a
    dialog hop where `or 1.0` ate a deliberate 0. Here the danger is
    _mode() matching on leading words and `if originrule is not None`
    in the shared runner."""
    inc = _pro_run(INCLUDE)
    exc = _pro_run(EXCLUDE)
    assert inc["R_Grp_40"].max() == pytest.approx(1.0)
    assert exc["R_Grp_40"].min() == pytest.approx(0.0)
    assert not np.allclose(inc["R_Grp_40"].to_numpy(),
                           exc["R_Grp_40"].to_numpy(), equal_nan=True)


def test_4b_the_two_doors_agree_under_both_rules():
    """Pro and QGIS, same data, same rules, same numbers."""
    for idx in (INCLUDE, EXCLUDE):
        pro = _pro_run(idx)["R_Grp_40"].to_numpy()
        qg, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                     treatmode=[1], treat=["Grp"], originrule=[idx])
        assert np.allclose(np.sort(pro),
                           np.sort(qg["R_Grp_40"].to_numpy()),
                           equal_nan=True), (
            f"the two doors disagree under rule index {idx}")


def test_5_both_doors_name_the_box_the_same_way():
    """The contract in tests/door_parity.py, checked from this side
    too so a reader of this file sees the requirement."""
    from door_parity import CORE, CORE_M2
    assert "originrule" in CORE
    assert "originrule" in CORE_M2
    for cls in (CountsAndShares, ValueStatistics):
        alg = cls()
        alg.initAlgorithm()
        names = {p.name() for p in alg.parameterDefinitions()}
        assert "originrule" in names, f"{cls.__name__} lost the box"


def test_6_the_run_says_which_rule_it_used():
    """The averages barely move, so the log is the only place a
    reader can learn which rule produced a table."""
    _, fb = _run(CountsAndShares, pop=["Population"], refmode=[1],
                 treatmode=[1], treat=["Grp"], originrule=[EXCLUDE])
    said = " ".join(fb.info) + " " + " ".join(fb.warnings)
    assert "EXCLUDED" in said or "i!=j" in said, said[:400]


# ---------------- BACKLOG 291: a refused row is not a smaller answer
def test_7_a_row_the_destination_refuses_stops_the_run():
    """`addFeature()` returns False when the sink rejects a feature -
    a shapefile's 255-field or 10-character limits, a full disk - and
    the return value was discarded. The log then reported the
    INTENDED row count, so a run that wrote fewer rows than it was
    given announced complete success.

    The simulator always returned True, which is exactly why this
    went unnoticed: the one thing that could have caught it agreed
    with the code.
    """
    from qgis.core import QgsProcessingException
    alg = CountsAndShares()
    alg.initAlgorithm()
    p = {"layer": _towns(), "unit": 100.0, "outfc": "memory:out",
         "k": "40", "pop": ["Population"], "refmode": [1],
         "treatmode": [1], "treat": ["Grp"]}
    fb = QgsProcessingFeedback()
    # make the destination refuse the third row
    qgis_stub._Sink.refuse_rows = (2,)
    try:
        with pytest.raises(QgsProcessingException,
                           match="(?i)kept only|refused"):
            alg.processAlgorithm(p, None, fb)
    finally:
        qgis_stub._Sink.refuse_rows = ()


def test_7b_a_run_that_keeps_every_row_still_reports_normally():
    """The guard must not fire on a healthy run."""
    out, fb = _run(CountsAndShares, pop=["Population"], refmode=[1],
                   treatmode=[1], treat=["Grp"])
    said = " ".join(fb.info)
    assert "Wrote 60 rows" in said, said[:300]


# ---------- BACKLOG 305: refuse before Run, not after -----------------
def test_8_neither_k_nor_r_is_refused_in_the_dialog():
    """John hit this teaching Exercise 1: his k values vanished while
    he worked down Pro's dialog, Pro was content to run, and the
    failure arrived forty lines into a traceback saying "give k_values
    and/or r_values" - words naming ENGINE ARGUMENTS, not boxes.

    NEITHER BOX IS REQUIRED and that is his ruling: a radius-only run
    is a perfectly good question. What is required is one of the two.
    """
    alg = CountsAndShares()
    alg.initAlgorithm()
    ctx = None
    ok, msg = alg.checkParameterValues(
        {"layer": _towns(), "unit": 100.0, "k": "", "r": ""}, ctx)
    assert ok is False
    assert "neighbourhood size" in msg and "radius" in msg, msg

    for good in ({"k": "100", "r": ""}, {"k": "", "r": "500"},
                 {"k": "100", "r": "500"}):
        p = {"layer": _towns(), "unit": 100.0}
        p.update(good)
        res = alg.checkParameterValues(p, ctx)
        assert res[0] is True, (good, res)
