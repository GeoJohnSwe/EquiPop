# -*- coding: utf-8 -*-
"""BACKLOG 463: an existing result field is found whatever its case,
and whatever Pro's view of the layer says.

John, 9 November 2026, Gdansk.gdb/CombinedPoints, Output = append to
the input, group "pharma", k = 200:

    TypeError: field 'T_pharma_200' exist
    ... Could not add the result fields ... The target refused the
    change.

The writer asked the LAYER which fields existed, by exact name, and
wrote through the CATALOG PATH. A geodatabase ignores case, so an
earlier T_Pharma_200 is the same field; and the layer keeps its own
cached schema (BACKLOG 309), which can lag the file. Either way the
field counted as new, ExtendTable refused it, the refusal was retried
twice as if it were a lock, and the message said "refused the change".

The fake arcpy is made to behave as a geodatabase does here: its
ExtendTable refuses a name already present, ignoring case.
"""
import numpy as np
import pandas as pd
import pytest

from test_arcgis_stub import _install_fake_arcpy, _load_pyt, _Messages

GROUPED = "types from a type field, grouped"
KEEP_BOTH = "Keep both - add a new column (b, c, d...)"


def _setup(extra=None, stale_layer=()):
    """A layer whose table already holds `extra` columns. Names in
    `stale_layer` are missing from the LAYER's field list but present
    in the dataset - Pro's cached view (BACKLOG 309)."""
    t = pd.DataFrame({"OBJECTID": [1, 2, 3, 4, 5, 6],
                      "SHAPE@X": [0., 300., 600., 900., 1200., 1500.],
                      "SHAPE@Y": [0.] * 6,
                      "Type": ["pharmacy", "cafe", "pharmacy", "bar",
                               "cafe", "pharmacy"]})
    for name, values in (extra or {}).items():
        t[name] = values
    state = _install_fake_arcpy(t)
    import arcpy
    calls = {"extend": 0, "cursor_on": []}

    real_extend = arcpy.da.ExtendTable

    def extend(target, key, array, akey):
        calls["extend"] += 1
        have = {c.lower() for c in state["table"].columns}
        for name in array.dtype.names:
            if name != akey and name.lower() in have:
                raise TypeError(f"field '{name}' exist")
        return real_extend(target, key, array, akey)

    real_list = arcpy.ListFields

    def list_fields(target):
        got = real_list(target)
        if str(target) == "people":            # the layer object
            got = [f for f in got if f.name not in stale_layer]
        return got

    real_cursor = arcpy.da.UpdateCursor

    class Cursor(real_cursor):
        def __init__(self, target, fields):
            calls["cursor_on"].append(str(target))
            missing = [f for f in fields
                       if f not in state["table"].columns]
            if missing:
                raise RuntimeError(f"Cannot find field {missing[0]}")
            if str(target) == "people":
                seen = {f.name for f in list_fields(target)}
                if any(f not in seen for f in fields):
                    raise RuntimeError("Cannot find field (layer view)")
            super().__init__(target, fields)

    arcpy.da.ExtendTable = extend
    arcpy.ListFields = list_fields
    arcpy.da.UpdateCursor = Cursor
    pyt = _load_pyt()
    pyt._vt_rows = lambda prm: [[str(c) for c in row]
                                for row in (prm.value or [])]
    return state, pyt, calls


def _execute(pyt, **values):
    tool = pyt.CountsShares()
    ps = tool.getParameterInfo()
    pm = {p.name: p for p in ps}
    pm["layer"].value = "people"
    settings = dict(k="2", treatmode=GROUPED, treatcatfield="Type",
                    treattable=[["pharmacy", "pharma"]])
    settings.update(values)
    for k, v in settings.items():
        pm[k].value = v
    msg = _Messages()
    tool.execute(ps, msg)
    return "\n".join(msg.log)


def test_an_existing_field_in_another_case_is_updated_in_place():
    """BROKEN WITH: the exact-name clash check of 1.63.5 - ExtendTable
    refuses 'T_pharma_200' because T_Pharma_200 is there."""
    old = {"T_Pharma_2": [9.] * 6, "R_Pharma_2": [9.] * 6}
    state, pyt, calls = _setup(old)
    said = _execute(pyt, existing="Overwrite")
    t = state["table"]
    assert "T_pharma_2" not in t and "R_pharma_2" not in t
    assert (t["R_Pharma_2"] != 9.).all()       # the new numbers
    assert np.allclose(t["R_Pharma_2"].to_numpy(),
                       t["T_Pharma_2"].to_numpy() / t["N_2"].to_numpy())
    assert "Updating 2 existing EquiPop fields in place" in said
    assert "NOT in the target" not in said


def test_a_field_the_layer_cannot_see_is_found_in_the_dataset():
    """The layer's cached view lacks a field the file has.
    BROKEN WITH: the clash check reading the layer only."""
    old = {"T_pharma_2": [9.] * 6}
    state, pyt, calls = _setup(old, stale_layer={"T_pharma_2"})
    _execute(pyt, existing="Overwrite")
    t = state["table"]
    assert (t["T_pharma_2"] != 9.).all()
    # and the update went through the dataset, which can see it
    assert calls["cursor_on"] and calls["cursor_on"][-1] != "people"


def test_the_layer_is_still_used_when_it_sees_every_field():
    """The catalog path is the fallback, not the new default."""
    old = {"T_pharma_2": [9.] * 6}
    state, pyt, calls = _setup(old)
    _execute(pyt, existing="Overwrite")
    assert calls["cursor_on"] == ["people"]


def test_stop_with_a_message_sees_a_field_in_another_case():
    """'Stop with a message' must stop on T_Pharma_2 too - before,
    it waved the run through to the refusal."""
    state, pyt, calls = _setup({"T_Pharma_2": [9.] * 6})
    with pytest.raises(Exception) as e:
        _execute(pyt, existing="Stop with a message")
    assert "Result fields already exist" in str(e.value)
    assert calls["extend"] == 0


def test_keep_both_moves_aside_from_a_field_in_another_case():
    state, pyt, calls = _setup({"T_Pharma_2": [9.] * 6,
                                "R_Pharma_2": [9.] * 6})
    _execute(pyt, existing=KEEP_BOTH)
    t = state["table"]
    assert (t["T_Pharma_2"] == 9.).all()       # left alone
    assert "T_pharma_2b" in t and "R_pharma_2b" in t


def test_keep_both_itself_ignores_case():
    from equipop.doors.fields import keep_both
    out, renamed = keep_both({"T": "T_pharma_200"}, {"T_Pharma_200"})
    assert out == {"T": "T_pharma_200b"}
    assert renamed == {"T_pharma_200": "T_pharma_200b"}
    out, _ = keep_both({"T": "T_pharma_200"},
                       {"t_pharma_200", "T_PHARMA_200B"})
    assert out == {"T": "T_pharma_200c"}


def test_the_refusal_is_a_field_refusal_not_a_lock():
    """'field ... exist' was matched only for names starting with N,
    so this one was retried twice and reported as a refused change.
    BROKEN WITH: the 1.63.5 _is_field_refusal."""
    _install_fake_arcpy(pd.DataFrame({"OBJECTID": [1]}))
    pyt = _load_pyt()
    exc = TypeError("field 'T_pharma_200' exist")
    assert pyt._is_field_refusal(exc)
    text = str(pyt._write_failure(exc, "add the result fields",
                                  "C:/Kartdata/PL/Gdansk.gdb/X"))
    assert "refused one of the result fields by name" in text
    assert "upper/lower case" in text
