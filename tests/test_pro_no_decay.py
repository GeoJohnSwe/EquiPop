# -*- coding: utf-8 -*-
"""BACKLOG 486: in ArcGIS Pro, "no decay" means no decay.

John's ruling, 11 November 2026, on a finding of the code review of
1.63.7: with 'Distance decay' left on "no decay" - its default - a
filled "half-life from a field" or "self-calibrating" box made the run
decay all the same, as negexp, the curve nobody had chosen. "It should
not - let us block that."

Blocked, not ignored. Ignoring would turn a run that decayed yesterday
into one that does not, without a word; the boxes stay visible, so the
message can be acted on. Stata has always refused the same pair.
"""
import numpy as np
import pandas as pd
import pytest

from test_arcgis_stub import _install_fake_arcpy, _load_pyt, _Messages


def _dialog(**values):
    rng = np.random.default_rng(486)
    n = 120
    t = pd.DataFrame({"OBJECTID": np.arange(1, n + 1),
                      "SHAPE@X": rng.uniform(0, 3000, n),
                      "SHAPE@Y": rng.uniform(0, 3000, n),
                      "Flag": rng.integers(0, 2, n).astype(float),
                      "MedDist": rng.uniform(300, 900, n)})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    tool = pyt.CountsShares()
    ps = tool.getParameterInfo()
    pm = {p.name: p for p in ps}
    pm["layer"].value = "people"
    pm["k"].value = "20"
    pm["treat"].value = "Flag"
    for k, v in values.items():
        pm[k].value = v
    return state, pyt, tool, ps, pm


def _decay_label(pm, name="negexp"):
    return [c for c in pm["model"].filter.list if c.startswith(name)][0]


@pytest.mark.parametrize("box,value,words", [
    ("hlfield", "MedDist", "half-life from a field"),
    ("hlfromdist", 15, "self-calibrating"),
])
def test_no_decay_with_a_half_life_box_filled_is_refused(box, value, words):
    """BROKEN WITH: the guard in execute() removed - the run finishes
    with ND_, TD_ and RD_ columns, decayed as negexp."""
    state, pyt, tool, ps, pm = _dialog(**{box: value})
    assert pm["model"].value == "no decay"          # the default
    with pytest.raises(Exception) as e:
        tool.execute(ps, _Messages())
    said = str(e.value)
    assert "no decay" in said and words in said
    assert "TO DECAY" in said and "FOR NO DECAY" in said
    assert "Nothing was computed" in said
    assert not [c for c in state["table"].columns if c.startswith("N_")]


def test_it_is_said_on_the_box_before_run():
    """In the dialog, as a red message on the box that is filled.
    BROKEN WITH: the loop in updateMessages removed."""
    state, pyt, tool, ps, pm = _dialog(hlfield="MedDist")
    tool.updateMessages(ps)
    errors = {p.name: txt for p in ps for kind, txt in p.messages
              if kind == "ERROR"}
    assert "hlfield" in errors and "no decay" in errors["hlfield"]
    # with a curve chosen the message is gone
    pm["model"].value = _decay_label(pm)
    tool.updateMessages(ps)
    assert "hlfield" not in {p.name for p in ps for kind, _ in p.messages
                             if kind == "ERROR"}


def test_the_same_boxes_with_a_curve_chosen_run_as_before():
    """Choosing negexp gives what the refused combination used to give
    in silence: the decayed columns, from the field's half-lives."""
    state, pyt, tool, ps, pm = _dialog(hlfield="MedDist")
    pm["model"].value = _decay_label(pm)
    msg = _Messages()
    tool.execute(ps, msg)
    got = state["table"]
    assert "ND_20" in got and "RD_Flag_20" in got
    assert np.isfinite(got["ND_20"].to_numpy(float)).all()


def test_no_decay_alone_is_no_decay():
    """Neither box filled: no decayed column, no refusal - and the
    plain half-life box, greyed out on "no decay", is still not read."""
    state, pyt, tool, ps, pm = _dialog(halflife=500.0)
    tool.execute(ps, _Messages())
    got = state["table"]
    assert "N_20" in got and "R_Flag_20" in got
    assert not [c for c in got.columns if c.startswith(("ND_", "TD_", "RD_"))]
