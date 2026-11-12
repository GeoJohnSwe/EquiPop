# -*- coding: utf-8 -*-
"""BACKLOG 467 and 468, the ArcGIS Pro side.

467  The types dropdown shows an integer type field as 1, 2, 3; the
     run held the same field as 1.0, 2.0, 3.0 and compared text with
     text. So a value PICKED FROM THE DROPDOWN was refused as "not in
     the type field", by a message that ends "Pick from the dropdown".
     (Read from the code: the stand-in arcpy cannot show Pro's
     dropdown. What is tested is that 1 and 1.0 are both accepted.)
468  Reference types from one type field, groups from another: every
     group was zero. The same fault as in the QGIS door, and tested
     against the same numbers (tests/test_qgis_types_and_counts.py).
"""
import numpy as np
import pandas as pd
import pytest

from test_arcgis_stub import _install_fake_arcpy, _load_pyt, _Messages


def _places():
    return pd.DataFrame({
        "OBJECTID": [1, 2, 3, 4, 5, 6],
        "SHAPE@X": [0., 300., 600., 900., 1200., 1500.],
        "SHAPE@Y": [0.] * 6,
        "One": [1.] * 6,
        "Type": ["cafe", "bar", "cafe", "cafe", "bar", "shop"],
        "Code": [1., 2., 1., 1., 2., 3.],
        "Country": ["SE", "SE", "SE", "NO", "NO", "NO"]})


def _run(**kw):
    state = _install_fake_arcpy(_places())
    pyt = _load_pyt()
    msg = _Messages()
    pyt._run_tool("counts", "people", msg, **kw)
    return state["table"], "\n".join(str(m) for m in msg.log)


def test_reference_from_one_type_field_groups_from_another():
    """Cafes among the places in Sweden.
    BROKEN WITH: pop_values=pop_vals in the grouped call of _run_tool
    - T_cafes_3 is 0 on every row."""
    got, said = _run(k_text="3", ref_mode=2, weight_field="One",
                     cat_field="Country", ref_rows=[["SE"]],
                     treat_mode=2, treat_cat_field="Type",
                     treat_rows=[["cafe", "cafes"]])
    assert list(got["N_3"]) == [3.0] * 6
    assert list(got["T_cafes_3"]) == [2.0] * 6
    assert np.allclose(got["R_cafes_3"], 2.0 / 3.0)


@pytest.mark.parametrize("typed", ["1", "1.0"])
def test_a_number_type_field_takes_the_number_as_typed(typed):
    """BROKEN WITH: known = sorted({str(v) ...}) and no norm - "1" is
    refused: 'These values are not in the type field 'Code''."""
    by_text, _ = _run(k_text="2", treat_mode=2, treat_cat_field="Type",
                      treat_rows=[["cafe", "sel"]])
    by_code, _ = _run(k_text="2", treat_mode=2, treat_cat_field="Code",
                      treat_rows=[[typed, "sel"]])
    assert by_text["T_sel_2"].sum() > 0
    assert np.allclose(by_code["T_sel_2"], by_text["T_sel_2"])
    # and as a reference type
    ref_text, _ = _run(k_text="2", ref_mode=2, weight_field="One",
                       cat_field="Type", ref_rows=[["cafe"]])
    ref_code, _ = _run(k_text="2", ref_mode=2, weight_field="One",
                       cat_field="Code", ref_rows=[[typed]])
    assert np.allclose(ref_code["Dist_2"], ref_text["Dist_2"])


def test_a_number_the_field_does_not_hold_is_still_refused():
    with pytest.raises(Exception) as e:
        _run(k_text="2", treat_mode=2, treat_cat_field="Code",
             treat_rows=[["7", "sel"]])
    assert "the type field 'Code'" in str(e.value) and "7" in str(e.value)
