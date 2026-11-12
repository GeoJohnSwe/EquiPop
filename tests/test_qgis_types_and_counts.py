# -*- coding: utf-8 -*-
"""BACKLOG 467-471: the QGIS door answered wrong, silently, in five
ways. Found in the code review of 1.63.7 (10 November 2026); 468 was
found while fixing 467.

467  A typed type the field does not hold gave columns of zeros and no
     message. A type code stored as a number never matched at all: the
     field was read as 1.0 and the "1" in the table matched nothing. A
     text field of codes was turned into numbers whenever one of them
     read as a number ("3a" became missing, "010" became 10).
468  Reference types picked from ONE type field and groups from
     ANOTHER: every group was zero (both doors - the reference types
     were looked for in the groups' field).
469  A count field left in box 1a on "every point counts as one" was
     used when no groups were asked for and dropped when they were.
470  Tool 2 took an untouched types table for one type called "NULL",
     so "only selected types" selected nobody.
471  The first feature decided whether the layer had geometry.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "qgis"))

import qgis_stub                                    # noqa: E402

qgis_stub.install()

from qgis.core import (QgsProcessingException,      # noqa: E402
                       QgsProcessingFeedback)
from equipop_qgis.alg_counts import CountsAndShares  # noqa: E402
from equipop_qgis.alg_stats import ValueStatistics   # noqa: E402

EVERY, COUNT, ONLY = [0], [1], [2]
NO_GROUPS, GROUPED = [0], [2]


def _run(alg_cls, table, geometry=True, **params):
    alg = alg_cls()
    alg.initAlgorithm()
    p = {"layer": qgis_stub.source_from(table, geometry=geometry),
         "unit": 100.0, "outfc": "memory:out"}
    p.update(params)
    fb = QgsProcessingFeedback()
    alg.processAlgorithm(p, None, fb)
    return p["_sinks"]["outfc"].to_frame(), fb


def _places(**extra):
    """Six places 300 m apart: far enough that who is counted shows in
    the distances."""
    t = pd.DataFrame({"x": [0., 300., 600., 900., 1200., 1500.],
                      "y": [0.] * 6,
                      "Pop": [4., 1., 7., 9., 2., 3.],
                      "Income": [10., 20., 30., 40., 50., 60.],
                      "Type": ["cafe", "bar", "cafe", "cafe", "bar",
                               "shop"],
                      "Country": ["SE", "SE", "SE", "NO", "NO", "NO"]})
    for k, v in extra.items():
        t[k] = v
    return t


# ------------------------------------------------------------- 467
def test_a_reference_type_the_field_does_not_hold_is_refused():
    """BROKEN WITH: refuse_unknown_types not called in alg_counts -
    the run finishes, and N_2 counts nobody."""
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, _places(), k="2", refmode=ONLY,
             catfield="Type", reftable=["cafe", "castle"])
    said = str(e.value)
    assert "castle" in said and "'Type'" in said
    assert "Box 1c" in said
    assert "bar, cafe, shop" in said          # what the field DOES hold
    assert "cafe, castle" not in said         # only the unknown one


def test_a_group_type_the_field_does_not_hold_is_refused():
    """BROKEN WITH: the group-table check removed - T_food_2 and
    R_food_2 are written, all zero."""
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, _places(), k="2", refmode=EVERY,
             treatmode=GROUPED, treatcatfield="Type",
             treattable=["Cafe", "food"])     # the capital C
    said = str(e.value)
    assert "Box 2c" in said and "Cafe" in said and "'Type'" in said
    assert "capital letters" in said


def test_tool_2_refuses_an_unknown_reference_type_too():
    with pytest.raises(QgsProcessingException) as e:
        _run(ValueStatistics, _places(), k="2", values=["Income"],
             refmode=ONLY, catfield="Type", reftable=["castle"])
    assert "castle" in str(e.value) and "'Type'" in str(e.value)


@pytest.mark.parametrize("typed", ["1", "1.0", " 1 "])
def test_a_type_code_stored_as_a_number_is_matched(typed):
    """Codes 1, 2, 3 in a NUMBER field. The answer must be the one a
    text field of the same types gives.
    BROKEN WITH: pts.data[catfield] in place of type_column() - the
    field is 1.0, the typed 1 matches nothing."""
    code = {"cafe": 1.0, "bar": 2.0, "shop": 3.0}
    t = _places()
    t["Code"] = [code[v] for v in t["Type"]]
    by_text, _ = _run(CountsAndShares, t, k="2", refmode=EVERY,
                      treatmode=GROUPED, treatcatfield="Type",
                      treattable=["cafe", "sel"])
    by_code, _ = _run(CountsAndShares, t, k="2", refmode=EVERY,
                      treatmode=GROUPED, treatcatfield="Code",
                      treattable=[typed, "sel"])
    assert by_text["T_sel_2"].sum() > 0
    pd.testing.assert_series_equal(by_code["T_sel_2"], by_text["T_sel_2"])
    pd.testing.assert_series_equal(by_code["R_sel_2"], by_text["R_sel_2"])


def test_a_text_field_of_codes_stays_text():
    """Codes "1", "010", "10", "3a" in a TEXT field. Until 1.63.7 the
    column was turned into numbers because some of it reads as
    numbers: "3a" became missing, and "010" and "10" both became 10.
    BROKEN WITH: pts.data[...] in place of type_column()."""
    t = _places(Code=["1", "010", "10", "3a", "3a", "010"])
    out, _ = _run(CountsAndShares, t, k="6", refmode=EVERY,
                  treatmode=GROUPED, treatcatfield="Code",
                  treattable=["3a", "a", "010", "b", "10", "c"])
    # k = 6 reaches everybody: the T_ columns are the group sizes
    assert set(out["T_a_6"]) == {2.0}
    assert set(out["T_b_6"]) == {2.0}
    assert set(out["T_c_6"]) == {1.0}
    # and a code the field does not hold is refused, not read as 10
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, t, k="6", refmode=EVERY,
             treatmode=GROUPED, treatcatfield="Code",
             treattable=["0010", "c"])
    assert "0010" in str(e.value)


def test_a_missing_type_is_no_type():
    """NULL in QGIS 3 is an object whose text is "NULL"; in QGIS 4 it
    is None; a missing number is NaN. None of them is a type: such a
    row is in no group, the 'every other type' group included.
    BROKEN WITH: labels() giving "nan" / "NULL" for them."""
    alg = CountsAndShares()
    feats = []
    for v in ("cafe", qgis_stub.NULL, None, float("nan"), " bar ", 2.0,
              3):
        f = qgis_stub.QgsFeature(qgis_stub.QgsFields())
        f.attribute = lambda name, _v=v: _v
        feats.append(f)
    alg._features = feats
    from equipop.categorical import labels
    raw = alg.type_column("Type")
    assert raw[1] is None and raw[2] is None     # NULL and None alike
    assert list(labels(raw)) == ["cafe", "", "", "", "bar", "2", "3"]
    # through the tool: the row with no type is not 'other'
    t = _places(Type=["cafe", None, "cafe", "bar", "bar", "shop"])
    out, _ = _run(CountsAndShares, t, k="6", refmode=EVERY,
                  treatmode=GROUPED, treatcatfield="Type",
                  treattable=["cafe", "food"], restgroup="other")
    assert set(out["T_food_6"]) == {2.0}
    assert set(out["T_other_6"]) == {3.0}        # bar, bar, shop


def test_the_engine_says_who_was_counted():
    """The engine's own line about the population reaches the QGIS
    log; it was printed where QGIS shows nothing."""
    _, fb = _run(CountsAndShares, _places(), k="2", refmode=ONLY,
                 catfield="Type", reftable=["cafe"])
    assert any("population 3/6 rows" in m for m in fb.info), fb.info


# ------------------------------------------------------------- 468
def test_reference_from_one_type_field_groups_from_another():
    """Cafes among the places in Sweden. Reference: Country = SE (rows
    0, 1, 2). Group: Type = cafe (rows 0, 2 in Sweden; row 3 is a cafe
    in Norway and must not count).

    BROKEN WITH: pop_values=pop_vals in the grouped call - "SE" is
    looked for in Type, nothing matches, T_cafes_3 is 0 everywhere."""
    out, _ = _run(CountsAndShares, _places(), k="3", refmode=ONLY,
                  catfield="Country", reftable=["SE"],
                  treatmode=GROUPED, treatcatfield="Type",
                  treattable=["cafe", "cafes"])
    # the three nearest Swedish places of every row are rows 0, 1, 2
    assert list(out["N_3"]) == [3.0] * 6
    assert list(out["T_cafes_3"]) == [2.0] * 6
    assert np.allclose(out["R_cafes_3"], 2.0 / 3.0)


def test_the_engine_takes_the_population_as_a_mask():
    """The piece 468 rests on, on its own - and the old call still
    works for one shared column."""
    from equipop.categorical import categories_to_binary
    types = np.array(["cafe", "bar", "cafe", "cafe"])
    mask = np.array([True, True, False, False])
    pop, treats = categories_to_binary(types, {"c": ["cafe"]},
                                       pop_mask=mask,
                                       rest_group="other",
                                       rest_in_population=None)
    assert list(pop) == list(mask)
    assert list(treats["c"]) == [1.0, 0.0, 0.0, 0.0]
    assert list(treats["other"]) == [0.0, 1.0, 0.0, 0.0]
    same, t2 = categories_to_binary(types, {"c": ["cafe"]},
                                    pop_values=["cafe"])
    assert list(t2["c"]) == [1.0, 0.0, 1.0, 1.0]
    with pytest.raises(ValueError, match="not both"):
        categories_to_binary(types, {}, pop_values=["cafe"],
                             pop_mask=mask)
    with pytest.raises(ValueError, match="rows"):
        categories_to_binary(types, {}, pop_mask=mask[:2])


# ------------------------------------------------------------- 469
def test_a_count_field_on_the_first_rung_means_one_thing():
    """'Every point counts as one' with box 1a still filled. Without
    groups the field was used; with groups it was dropped. One dialog
    must mean one thing: N_k is the same number on both routes, and
    the run says the field is used.

    BROKEN WITH: `if refmode == 0: pop = None` put back - N_2 is 2 on
    the grouped route and the Pop-weighted count on the other."""
    plain, fb1 = _run(CountsAndShares, _places(), k="2", refmode=EVERY,
                      pop="Pop")
    grouped, fb2 = _run(CountsAndShares, _places(), k="2", refmode=EVERY,
                        pop="Pop", treatmode=GROUPED,
                        treatcatfield="Type",
                        treattable=["cafe", "sel"])
    pd.testing.assert_series_equal(plain["N_2"], grouped["N_2"])
    pd.testing.assert_series_equal(plain["Dist_2"], grouped["Dist_2"])
    # and the groups are counted in the same units: people, not places
    assert grouped["T_sel_2"].max() > 1.0
    # BACKLOG 485 (John's ruling, 11 November): the rung now SAYS a
    # filled count field counts, so this is a plain line in the log -
    # in 1.63.8 it was a warning about a box "used anyway"
    for fb in (fb1, fb2):
        assert any("Each row counts as its value in 'Pop'" in m
                   for m in fb.info), fb.info
        assert not any("count field" in m for m in fb.warnings)
    # with the box empty every point counts as one, and nothing is said
    one, fb3 = _run(CountsAndShares, _places(), k="2", refmode=EVERY)
    assert set(one["N_2"]) == {2.0}
    assert not any("Each row counts" in m for m in fb3.info)


def test_tool_2_says_it_too():
    _, fb = _run(ValueStatistics, _places(), k="2", values=["Income"],
                 refmode=EVERY, pop="Pop")
    assert any("Each row counts as its value in 'Pop'" in m
               for m in fb.info), fb.info
    assert not any("count field" in m for m in fb.warnings)


def test_the_first_rung_says_what_it_does():
    """BACKLOG 485: one wording in both doors (test_rungs pins that),
    and it names the count field."""
    from equipop.doors import rungs
    from equipop_qgis.alg_counts import REF_MODES
    assert REF_MODES[0] == rungs.REFERENCE[0]
    assert REF_MODES[0].startswith("every point counts as one")
    assert "count field" in REF_MODES[0]


def test_the_two_doors_agree_on_that_dialog():
    """The same dialog in ArcGIS Pro: same numbers. This is the reason
    469 was settled as 'used' - the doors must not disagree."""
    from test_arcgis_stub import _install_fake_arcpy, _load_pyt, _Messages
    q, _ = _run(CountsAndShares, _places(), k="2", refmode=EVERY,
                pop="Pop", treatmode=GROUPED, treatcatfield="Type",
                treattable=["cafe", "sel"])
    t = _places().rename(columns={"x": "SHAPE@X", "y": "SHAPE@Y"})
    t.insert(0, "OBJECTID", np.arange(1, len(t) + 1))
    state = _install_fake_arcpy(t)
    pyt = _load_pyt()
    pyt._run_tool("counts", "people", _Messages(), k_text="2",
                  ref_mode=0, weight_field="Pop", treat_mode=2,
                  treat_cat_field="Type", treat_rows=[["cafe", "sel"]])
    a = state["table"]
    for col in ("N_2", "Dist_2", "T_sel_2", "R_sel_2"):
        assert np.allclose(a[col].to_numpy(float), q[col].to_numpy(float)), col


# ------------------------------------------------------------- 470
def test_tool_2_takes_an_untouched_types_table_as_everybody():
    """'Only selected types' with the types table never touched: an
    empty table means EVERY type, as in tool 1 and in Pro.
    BROKEN WITH: parameterAsMatrix read directly in alg_stats - the
    table is [NULL], read as one type called "NULL", and the run is
    refused (before 467: every statistic came out empty)."""
    everybody, _ = _run(ValueStatistics, _places(), k="2",
                        values=["Income"], refmode=COUNT, pop="Pop")
    untouched, fb = _run(ValueStatistics, _places(), k="2",
                         values=["Income"], refmode=ONLY, pop="Pop",
                         catfield="Type")              # no reftable
    cols = [c for c in everybody.columns if c.endswith("_2")]
    assert len(cols) > 2
    for c in cols:
        pd.testing.assert_series_equal(everybody[c], untouched[c])


def test_tool_2_does_not_call_an_empty_table_filled():
    """BROKEN WITH: the same - "Box 1c ... is filled ... IGNORED" on a
    run where box 1c was never touched."""
    _, fb = _run(ValueStatistics, _places(), k="2", values=["Income"],
                 refmode=EVERY)
    assert not any("Box 1c" in m for m in fb.info + fb.warnings)


# ------------------------------------------------------------- 471
def test_the_first_feature_does_not_decide_the_geometry():
    """A point layer whose FIRST feature has lost its geometry, and
    which carries leftover X/Y columns in other units. The run must
    use the geometry of the rows that have one - and leave the first
    row without a result - not switch to the columns for everybody.

    BROKEN WITH: has_geom = feats[0].hasGeometry() - the run reads
    'X' and 'Y' (kilometres here), so every Dist_2 is 1000 times too
    small."""
    clean = _places()
    clean.loc[0, ["x", "y"]] = np.nan
    want, _ = _run(CountsAndShares, clean, k="2", refmode=EVERY)
    t = clean.copy()
    t["X"] = _places()["x"] / 1000.0
    t["Y"] = _places()["y"] / 1000.0
    out, fb = _run(CountsAndShares, t, k="2", refmode=EVERY)
    got = out["Dist_2"].to_numpy(float)
    assert np.isnan(got[0])                 # no geometry, no result
    assert (got[1:] > 200.0).all(), got     # metres, not kilometres
    assert np.allclose(got[1:], want["Dist_2"].to_numpy(float)[1:])
    assert any("feature geometry" in m for m in fb.info)


def test_a_table_without_geometry_still_reads_its_columns():
    want, _ = _run(CountsAndShares, _places(), k="2", refmode=EVERY)
    out, fb = _run(CountsAndShares, _places(), geometry=False, k="2",
                   refmode=EVERY)
    assert np.allclose(out["Dist_2"].to_numpy(float),
                       want["Dist_2"].to_numpy(float))
    assert any("attribute fields" in m for m in fb.info)
