# -*- coding: utf-8 -*-
"""Tools 3 to 6 hidden until shown (v1.62.0, BACKLOG 438).

John, 25 October 2026: one plugin, the same in every detail except
whether tools 3 to 6 are listed - "let us make the default to hide -
but please indicate in help etc., how it can be lifted".

Hiding must change the LIST and nothing else: in QGIS every tool stays
registered (a flag hides it from the toolbox tree), in Pro the list is
filtered and a refresh re-reads it. Anything that fails while deciding
shows the tool.

conftest.py gives the suite a settings folder of its own, so these
tests never read or overwrite the developer's real choice.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from equipop.doors import toolset
from equipop.doors.help import LABELS, VOCAB, VOCAB_QGIS, usage_for

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "qgis"))


@pytest.fixture
def fresh(tmp_path, monkeypatch):
    """A settings folder nobody has written to, and no override."""
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv(toolset.ENV, raising=False)
    toolset._cache.clear()
    yield tmp_path
    toolset._cache.clear()


# ------------------------------------------------------------- the rule
def test_hidden_by_default(fresh):
    """John's ruling: hidden unless chosen.

    BROKEN WITH: DEFAULT = True."""
    assert toolset.show_all() is False
    for t in toolset.STANDARD:
        assert toolset.is_shown(t)
    for t in toolset.EXTENDED:
        assert not toolset.is_shown(t)


def test_the_choice_is_saved_and_read_back(fresh):
    """Saved in the user's settings folder, kept between sessions.

    BROKEN WITH: the value not saved (DEFAULT written instead)."""
    where = toolset.set_show_all(True)
    assert where.is_file() and fresh in where.parents
    assert json.loads(where.read_text(encoding="utf-8")) == {
        "show_all_tools": True}
    assert toolset.show_all() is True
    toolset.set_show_all(False)
    assert toolset.show_all() is False


def test_the_environment_overrides_the_saved_choice(fresh, monkeypatch):
    """For a classroom image: EQUIPOP_SHOW_ALL_TOOLS=1 or 0.

    BROKEN WITH: the environment read after the file."""
    toolset.set_show_all(False)
    monkeypatch.setenv(toolset.ENV, "1")
    assert toolset.show_all() is True
    assert "environment variable" in toolset.state_sentence()
    toolset.set_show_all(True)
    monkeypatch.setenv(toolset.ENV, "0")
    assert toolset.show_all() is False


def test_an_unreadable_settings_file_means_the_default(fresh):
    """A damaged file is not an error that stops a toolbox opening.

    BROKEN WITH: json.loads unguarded."""
    p = toolset.settings_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{not json", encoding="utf-8")
    assert toolset.show_all() is False
    p.write_text('{"show_all_tools": "yes"}', encoding="utf-8")
    assert toolset.show_all() is False          # not a bool: the default


# --------------------------------------------------- the doors agree
def _qgis_provider():
    import qgis_stub
    qgis_stub.install()
    from equipop_qgis.provider import EquipopProvider
    prov = EquipopProvider()
    prov.loadAlgorithms()
    return prov


def _pro():
    import test_arcgis_continental as AC
    return AC._pyt(), AC


def test_every_tool_of_both_doors_is_classified_and_numbered_so():
    """Standard = tool 0 and tools 1-2; extended = everything numbered
    3 or more. A new tool must be put in one set or the other.

    BROKEN WITH: SpatialDemography left out of EXTENDED."""
    prov = _qgis_provider()
    pyt, _AC = _pro()
    names = ({a.EQP_TOOL: a.displayName() for a in prov.algorithms()}
             | {c.__name__: c().label for c in pyt.Toolbox().all_tools})
    for tool, label in names.items():
        number = int(label.split(".")[0][0])
        assert tool in toolset.STANDARD + toolset.EXTENDED, tool
        assert (tool in toolset.EXTENDED) == (number >= 3), (tool, label)


def test_tool_0_has_the_same_name_and_choices_in_both_doors():
    """BROKEN WITH: Pro's second choice reworded."""
    prov = _qgis_provider()
    pyt, _AC = _pro()
    from equipop_qgis import alg_show
    q = [a for a in prov.algorithms() if a.EQP_TOOL == "ShowTools"][0]
    assert q.displayName() == LABELS["ShowTools"] == pyt.ShowTools().label
    assert list(toolset.CHOICES) == alg_show.CHOICES == pyt.SHOW_CHOICES


# ---------------------------------------------------------------- QGIS
def test_qgis_hides_3_to_6_from_the_toolbox_but_keeps_them(fresh):
    """Hidden by a FLAG: still registered, so models and scripts that
    use them run. Shown once tool 0 says so.

    BROKEN WITH: the hide flag applied to every tool (standard ones
    vanish); and flags() not consulting the saved choice."""
    from qgis.core import Qgis
    hide = Qgis.ProcessingAlgorithmFlag.HideFromToolbox
    prov = _qgis_provider()
    algs = {a.EQP_TOOL: a for a in prov.algorithms()}
    assert set(algs) == set(toolset.STANDARD) | set(toolset.EXTENDED)
    for t, a in algs.items():
        assert bool(a.flags() & hide) == (t in toolset.EXTENDED), t
    toolset.set_show_all(True)
    assert not any(a.flags() & hide for a in algs.values())


def test_qgis_tool_0_saves_the_choice_and_refreshes_the_toolbox(fresh):
    """It runs in the main thread (refreshing a provider from a worker
    thread is not safe), saves the choice, and reloads the provider so
    the toolbox changes at once.

    BROKEN WITH: the refresh call removed."""
    from qgis.core import Qgis, QgsApplication
    prov = _qgis_provider()
    QgsApplication.registry.providers["equipop"] = prov
    try:
        from equipop_qgis.alg_show import ShowTools
        import test_vital_doors as VD
        alg = ShowTools()
        assert alg.flags() & Qgis.ProcessingAlgorithmFlag.NoThreading
        alg.initAlgorithm()
        before = prov.refreshed
        alg.processAlgorithm({"show": 1}, {}, VD._Feedback())
        assert toolset.show_all() is True
        assert prov.refreshed == before + 1
        alg.processAlgorithm({"show": 0}, {}, VD._Feedback())
        assert toolset.show_all() is False
        # the dialog opens on the current choice
        toolset.set_show_all(True)
        alg2 = ShowTools()
        alg2.initAlgorithm()
        assert alg2.parameterDefinitions()[0].defaultValue() == 1
    finally:
        QgsApplication.registry.providers.pop("equipop", None)


# ----------------------------------------------------------------- Pro
def test_pro_lists_0_1_and_2_until_shown(fresh):
    """BROKEN WITH: `self.tools = self.all_tools` (nothing hidden)."""
    pyt, _AC = _pro()
    names = [t.__name__ for t in pyt.Toolbox().tools]
    assert names == ["ShowTools", "CountsShares", "ValueStatistics"]
    toolset.set_show_all(True)
    assert [t.__name__ for t in pyt.Toolbox().tools] == [
        t.__name__ for t in pyt.Toolbox().all_tools]


def test_pro_tool_0_saves_the_choice_and_says_to_refresh(fresh):
    """BROKEN WITH: the refresh sentence removed."""
    pyt, AC = _pro()
    tool = pyt.ShowTools()
    m = AC._Messages()
    tool.execute(AC._params(tool, show=pyt.SHOW_CHOICES[1]), m)
    assert toolset.show_all() is True
    assert any("Refresh" in str(x) for x in m.log), m.log
    tool.execute(AC._params(tool, show=pyt.SHOW_CHOICES[0]),
                 AC._Messages())
    assert toolset.show_all() is False
    with pytest.raises(pyt.arcpy.ExecuteError, match="two choices"):
        tool.execute(AC._params(tool, show="Everything"), AC._Messages())


def test_pro_lists_everything_when_the_rule_cannot_be_read(fresh,
                                                          monkeypatch):
    """An older package has no toolset module. The toolbox must still
    open - and show every tool, whose own version check then explains.

    BROKEN WITH: _shown_tools without its try."""
    pyt, _AC = _pro()
    monkeypatch.setitem(sys.modules, "equipop.doors.toolset", None)
    assert len(pyt.Toolbox().tools) == len(pyt.Toolbox().all_tools)


# ---------------------------------------------------- how to lift it
@pytest.mark.parametrize("vocab, where", [(VOCAB, "Refresh"),
                                          (VOCAB_QGIS, "Processing")])
def test_tools_1_and_2_say_how_to_show_the_rest(vocab, where):
    """John: "please indicate in help etc., how it can be lifted".
    Both always-shown tools' help says it, in each door's own words.

    BROKEN WITH: the sentence left out of tool 2's usage."""
    for tool in ("CountsShares", "ValueStatistics"):
        text = usage_for(tool, vocab)
        assert "0. Show or hide tools 3-6" in text, tool
        assert where in text, tool


@pytest.mark.parametrize("doc", ["arcgis/ARCGIS_GUIDE.md",
                                 "qgis/README_QGIS.md", "INSTALL.md"])
def test_the_guides_say_how_to_show_the_rest(doc):
    """BROKEN WITH: the QGIS readme still listing two tools only."""
    text = (ROOT / doc).read_text(encoding="utf-8")
    assert "0. Show or hide tools 3-6" in text
    assert "hidden" in text
