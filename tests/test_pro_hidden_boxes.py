# -*- coding: utf-8 -*-
"""BACKLOG 462: a box Pro greys out is not read by the run.

John, 8 November 2026, on a Polish OSM POI layer. He wanted every POI
as the reference population and a few types as the group, so he chose
"every point counts as one". Pro greyed out the reference type field
and the reference table - which still held types from an earlier
attempt - and the run said

    These boxes hold values that the rungs you chose do NOT read, so
    they are IGNORED: catfield, reftable ...

and then died on that very table: "These values are not in the
category field, so the reference population would be empty". He could
not empty the table, because Pro had hidden it.

_boxes_for_rungs was lifted out in 1.29.6 (BACKLOG 146) "so the run
can consult the same map the dialog does", and nothing in the run ever
consulted it: execute() handed every box to _run_tool. The six type
boxes are now passed empty off their rungs, as the QGIS door has
always done. The count field and the group count fields are still
used off their rungs, as in both doors before - the warning now says
so instead of calling them ignored.
"""
import pandas as pd
import pytest

from test_arcgis_stub import _install_fake_arcpy, _load_pyt, _Messages

EVERY = "every point counts as one"
COUNT = "a field holds the count"
ONLY = "only selected types, with a count field"
NONE = "not measuring one - distances and counts only"
GROUPED = "types from a type field, grouped"


def _dialog(tool="CountsShares", **values):
    """The dialog as John fills it. Points 300 m apart, so a restricted
    population changes the answer."""
    t = pd.DataFrame({"OBJECTID": [1, 2, 3, 4, 5, 6],
                      "SHAPE@X": [0., 300., 600., 900., 1200., 1500.],
                      "SHAPE@Y": [0.] * 6,
                      "Pop": [4., 1., 7., 9., 2., 3.],
                      "Flag": [1., 0., 1., 0., 1., 0.],
                      "Income": [10., 20., 30., 40., 50., 60.],
                      "Type": ["a", "a", "b", "b", "c", "c"]})
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    # The fake arcpy describes ANY string as a dataset, so a value
    # table's "a" would come back as "memory/a". Real Pro hands back
    # the strings; _vt_rows' path handling is not what is tested here.
    pyt._vt_rows = lambda prm: [[str(c) for c in row]
                                for row in (prm.value or [])]
    tool_obj = getattr(pyt, tool)()
    ps = tool_obj.getParameterInfo()
    pm = {p.name: p for p in ps}
    pm["layer"].value = "people"
    for k, v in values.items():
        pm[k].value = v
    return state, tool_obj, ps


def _run(tool="CountsShares", **values):
    state, tool_obj, ps = _dialog(tool, **values)
    msg = _Messages()
    tool_obj.execute(ps, msg)
    return state["table"], "\n".join(msg.log)


def test_johns_dialog_runs_with_the_hidden_reference_table_full():
    """The 8 November dialog: every point, a few types grouped, and a
    hidden reference table holding values the field does not have.
    BROKEN WITH: execute() passing _vt_rows(pm["reftable"]) whatever
    the rung - the 1.63.4 code. Raises "not in the category field"."""
    got, said = _run(k="2", refmode=EVERY, catfield="Type",
                     reftable=[["castle"], ["windmill"]],
                     treatmode=GROUPED, treatcatfield="Type",
                     treattable=[["a", "sel"], ["c", "sel"]])
    assert "R_sel_2" in got
    assert "IGNORED: catfield, reftable." in said


def test_a_hidden_reference_table_does_not_restrict_the_population():
    """Even when its values DO exist, a greyed-out table must not
    narrow 'every point counts as one' to the types in it.
    BROKEN WITH: the 1.63.4 code - the population becomes type a."""
    clean, _ = _run(k="2", refmode=EVERY)
    hidden, said = _run(k="2", refmode=EVERY, catfield="Type",
                        reftable=[["a"]])
    pd.testing.assert_series_equal(clean["N_2"], hidden["N_2"])
    pd.testing.assert_series_equal(clean["Dist_2"], hidden["Dist_2"])
    assert "IGNORED" in said
    # and the rung that reads it does restrict - the test can tell
    only, _ = _run(k="2", refmode=ONLY, pop="Pop", catfield="Type",
                   reftable=[["a"]])
    assert not only["Dist_2"].equals(clean["Dist_2"])


def test_hidden_groups_make_no_shares():
    """Treatment rung 'not measuring one' with a group table left in
    the greyed-out boxes: no T_ or R_ columns.
    BROKEN WITH: the 1.63.4 code - T_sel_2 and R_sel_2 appear."""
    got, said = _run(k="2", refmode=EVERY, treatmode=NONE,
                     treatcatfield="Type", treattable=[["a", "sel"]],
                     restgroup="other")
    assert not [c for c in got if c.startswith(("T_", "R_"))]
    assert "restgroup, treatcatfield, treattable" in said


def test_the_statistics_tool_ignores_its_hidden_reference_boxes():
    clean, _ = _run("ValueStatistics", k="2", refmode=EVERY,
                    values="Income")
    hidden, said = _run("ValueStatistics", k="2", refmode=EVERY,
                        values="Income", catfield="Type",
                        reftable=[["nowhere"]])
    stat = [c for c in clean if c.startswith(("mean", "M_", "Mean"))
            or "_2" in c and c not in ("N_2", "Dist_2")]
    assert stat
    for c in stat:
        pd.testing.assert_series_equal(clean[c], hidden[c])
    assert "IGNORED: catfield, reftable." in said


def test_the_grouped_rung_without_its_type_field_is_refused():
    """With the reference type field no longer read off its rung, a
    grouped treatment that leaned on it would give distances and no
    shares in silence. Refused instead, in the rung's own words.
    BROKEN WITH: the guard in _guard_rungs removed."""
    state, tool_obj, ps = _dialog(k="2", refmode=EVERY, catfield="Type",
                                  treatmode=GROUPED,
                                  treattable=[["a", "sel"]])
    with pytest.raises(Exception) as e:
        tool_obj.execute(ps, _Messages())
    assert "the type field for the groups" in str(e.value)


def test_the_grouped_rung_may_borrow_a_visible_reference_type_field():
    got, _ = _run(k="2", refmode=ONLY, pop="Pop", catfield="Type",
                  treatmode=GROUPED, treattable=[["a", "sel"]])
    assert "R_sel_2" in got


def test_a_count_field_off_its_rung_is_said_to_be_used():
    """Box 1a is greyed out on 'every point counts as one' but used,
    as in both doors before - so the warning says USED, not IGNORED.
    BROKEN WITH: 'pop' put back among the ignored names."""
    plain, _ = _run(k="2", refmode=EVERY)
    got, said = _run(k="2", refmode=EVERY, pop="Pop")
    assert "the count IS used" in said
    assert "IGNORED" not in said
    assert not got["Dist_2"].equals(plain["Dist_2"])


def test_group_count_fields_off_their_rung_are_said_to_be_used():
    got, said = _run(k="2", refmode=EVERY, treat="Flag")
    assert "R_Flag_2" in got
    assert "those columns ARE used" in said
    assert "IGNORED" not in said


def test_the_default_outside_choice_is_not_reported_as_ignored():
    """'Rows whose type is NOT included' always holds its default, so
    it was named IGNORED on every run of the first rung - noise that
    trains people to skip the warning that matters."""
    _, said = _run(k="2", refmode=EVERY)
    assert "IGNORED" not in said


def test_the_refusal_names_the_field_it_looked_in():
    """John could not tell which field 'the category field' was."""
    state, tool_obj, ps = _dialog(k="2", refmode=ONLY, pop="Pop",
                                  catfield="Type",
                                  reftable=[["castle"]])
    with pytest.raises(Exception) as e:
        tool_obj.execute(ps, _Messages())
    assert "the type field 'Type'" in str(e.value)
    assert "castle" in str(e.value)


def test_a_group_refusal_names_the_field_too():
    state, tool_obj, ps = _dialog(k="2", refmode=EVERY,
                                  treatmode=GROUPED, treatcatfield="Type",
                                  treattable=[["castle", "sel"]])
    with pytest.raises(Exception) as e:
        tool_obj.execute(ps, _Messages())
    assert "the type field 'Type'" in str(e.value)
