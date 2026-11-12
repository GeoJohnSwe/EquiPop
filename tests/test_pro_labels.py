# -*- coding: utf-8 -*-
"""BACKLOG 465: every choice in a Pro dropdown runs as itself.

Found in the code review of 1.63.7 (10 November 2026). The toolbox
turned a dropdown's text into a position with "the first label whose
leading words the text starts with". The self-potential labels lead
with "0", "0.71" and "1" - and "0.71 - the median ..." starts with
"0". So the middle choice ran as the first one, in tools 1 and 2,
and the log printed the label the user had picked.

The test that guarded the box (test_arcgis_stub, BACKLOG 95) tried
the first and the last choice. The middle one is tried here, and so
is every label of every list, so that the next label somebody adds
cannot be swallowed by a shorter neighbour.
"""
import numpy as np
import pandas as pd
import pytest

from test_arcgis_stub import _install_fake_arcpy, _load_pyt, _Messages

LISTS = ["REF_MODES", "TREAT_MODES", "OUTSIDE_MODES", "SELFPOT_MODES",
         "OVERSHOOT_MODES", "ORIGIN_MODES", "JOIN_MODES", "JOIN_COMBINE"]


def _pyt():
    _install_fake_arcpy(pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                                      "SHAPE@Y": [0.0]}))
    return _load_pyt()


def test_the_lists_checked_here_are_all_the_lists_there_are():
    """A new dropdown must be added to LISTS, or it is not guarded.
    Every list handed to _mode in the toolbox is named in it."""
    import re
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "arcgis"
           / "EquiPop.pyt").read_text(encoding="utf-8")
    used = set(re.findall(r"_mode\(pm,\s*\"\w+\",\s*(\w+)", src))
    assert used and used <= set(LISTS), sorted(used - set(LISTS))


@pytest.mark.parametrize("name", LISTS)
def test_every_label_is_its_own_choice(name):
    """BROKEN WITH: the 1.63.7 _mode - SELFPOT_MODES[1] comes back as
    choice 0."""
    pyt = _pyt()
    modes = getattr(pyt, name)
    for i, label in enumerate(modes):
        assert pyt._mode_index(label, modes) == i, label
        # and whatever the case or the padding Pro hands it back in
        assert pyt._mode_index("  " + label.upper() + " ", modes) == i


@pytest.mark.parametrize("name", LISTS)
def test_no_label_hides_behind_the_leading_words_of_another(name):
    """The older-wording route: a text that is NOT today's label is
    matched on its leading words - by the longest that fit.
    BROKEN WITH: "first match wins" in _mode_index."""
    pyt = _pyt()
    modes = getattr(pyt, name)
    for i, label in enumerate(modes):
        reworded = label + " (an older or a newer wording)"
        assert pyt._mode_index(reworded, modes) == i, label


def test_an_empty_box_takes_the_default_it_was_given():
    pyt = _pyt()
    assert pyt._mode_index("", pyt.JOIN_MODES, 1) == 1
    assert pyt._mode_index(None, pyt.REF_MODES) == 0


def _dense_cell():
    rng = np.random.default_rng(465)
    n_dense, n_spread = 200, 400
    t = pd.DataFrame({
        "OBJECTID": np.arange(1, n_dense + n_spread + 1),
        "SHAPE@X": np.concatenate([rng.uniform(1, 99, n_dense),
                                   rng.uniform(500, 4000, n_spread)]),
        "SHAPE@Y": np.concatenate([rng.uniform(1, 99, n_dense),
                                   rng.uniform(500, 4000, n_spread)]),
        "Income": rng.uniform(10, 90, n_dense + n_spread)})
    dense = ((t["SHAPE@X"] < 100) & (t["SHAPE@Y"] < 100)).to_numpy()
    return t, dense, n_dense


@pytest.mark.parametrize("tool,extra", [("CountsShares", {}),
                                        ("ValueStatistics",
                                         {"values": "Income"})])
def test_the_three_self_potentials_give_three_distances(tool, extra):
    """Through the dialog, in both tools, against the closed form:
    200 people in one 100 m cell, k = 100. The radius at which 100 of
    them are reached is the equal-area radius R; the choices are
    0, R / sqrt(2) and R.

    BROKEN WITH: the 1.63.7 _mode - the middle choice gives 0.0."""
    t, dense, n_dense = _dense_cell()
    radius = np.sqrt(100.0 ** 2 * 100 / (n_dense * np.pi))
    got = []
    pyt = None
    for choice in range(3):
        state = _install_fake_arcpy(t.copy())
        pyt = _load_pyt()
        obj = getattr(pyt, tool)()
        ps = obj.getParameterInfo()
        pm = {p.name: p for p in ps}
        pm["layer"].value = "people"
        pm["k"].value = "100"
        pm["selfpot"].value = pyt.SELFPOT_MODES[choice]
        for k, v in extra.items():
            pm[k].value = v
        obj.execute(ps, _Messages())
        got.append(state["table"]["Dist_100"].to_numpy()[dense])
    assert (got[0] == 0.0).all()
    assert np.allclose(got[1], radius / np.sqrt(2.0), rtol=1e-9), got[1][0]
    assert np.allclose(got[2], radius, rtol=1e-9), got[2][0]
    assert pyt.SELFPOT_VALUES == [0.0, 2 ** -0.5, 1.0]
