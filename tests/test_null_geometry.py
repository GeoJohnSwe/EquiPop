"""BACKLOG 380 - a row EquiPop cannot locate keeps its place.

John, ArcGIS Pro, 8 October 2026, on a layer holding null geometry:

    ValueError: cannot create NumPyArray. geometry type found

raised by `arcpy.da.FeatureClassToNumPyArray` inside `_read_input`.

**THE HANDLING ALREADY EXISTED AND COULD NOT BE REACHED.** Forty lines
below the failing call, in the same function:

    n_missing = int((~(np.isfinite(x) & np.isfinite(y))).sum())
    if n_missing:
        messages.addMessage(f"{n_missing} rows with missing
                              coordinates -> Null results
                              (EquiPop convention).")

and `skip_nulls=False, null_value=np.nan` was passed DELIBERATELY so
those rows would survive as NaN and land there. The QGIS door does the
same thing by hand and gets it right:

    g = f.geometry()
    if g is None or g.isEmpty():
        xs.append(np.nan); ys.append(np.nan)

So the convention was implemented in the engine, announced in its own
message, honoured by one GUI, and unreachable from the other. Fourth
release running of that shape - 353 a guard unreachable from the path
that could trip it, 368 a hint classified and never rendered, 373 a
parse fixed downstream of the parse that breaks.

WHAT THESE TESTS CAN AND CANNOT ESTABLISH. The simulator is this
project's own code, so a test that makes the fast reader raise is
testing **EquiPop's fallback**, not Esri's reader. It cannot prove
arcpy fails where John saw it fail, and it cannot prove the fallback
succeeds against a real geodatabase. It CAN prove that when the fast
reader refuses for any reason, the run completes, the rows survive,
and the convention is applied - which is the part that is ours. The
handover's own rule applies in both directions: when a door looks
broken in a way that makes no sense, suspect the simulator.

Each test's docstring names what it was BROKEN WITH, and each was
actually broken that way.
"""
import os
import re

import numpy as np
import pandas as pd
import pytest

from test_arcgis_stub import _install_fake_arcpy, _load_pyt, _Messages

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFUSAL = "cannot create NumPyArray. geometry type found"


def _points(n=120, nulls=()):
    rng = np.random.default_rng(7)
    t = pd.DataFrame({
        "OBJECTID": np.arange(1, n + 1),
        "SHAPE@X": rng.uniform(0, 3000, n),
        "SHAPE@Y": rng.uniform(0, 3000, n),
        "People": rng.integers(1, 40, n).astype(float),
        "HighEdu": rng.integers(0, 2, n).astype(float),
    })
    for i in nulls:
        t.loc[i, "SHAPE@X"] = np.nan
        t.loc[i, "SHAPE@Y"] = np.nan
    return t


# --------------------------------------------------------- the fix
def test_a_refused_fast_read_falls_back_and_still_answers():
    """BROKEN WITH: removing the try/except from _read_columns, i.e.
    calling the fast reader the way the code did before.

    THE WHOLE FINDING. Before this release the exception left
    `_read_input` and the user got a traceback. One bad row made a
    whole layer unusable - John's workaround was to select the
    non-null features by hand, which works but is not the same answer
    (see the alignment test below).
    """
    state = _install_fake_arcpy(_points(nulls=[3, 4]))
    state["fc_array_raises"] = REFUSAL
    pyt = _load_pyt()
    msg = _Messages()

    pyt._run_tool("counts", "people", msg, weight_field="People",
                  treat_fields=["HighEdu"], k_text="25")

    got = state["table"]
    assert "N_25" in got.columns, (
        "the run did not complete - the fallback is not reached")
    assert got["N_25"].notna().sum() > 100


def test_the_rows_it_cannot_locate_get_null_results_not_removal():
    """BROKEN WITH: `skip_nulls=True` in the fallback's cursor read, or
    filtering the null rows out of `cols`.

    **THE DIFFERENCE BETWEEN THIS AND JOHN'S WORKAROUND**, and the
    reason the fix is worth having. Selecting the non-null features
    gives an output with FEWER ROWS; the convention gives an output
    with the SAME rows, the unlocatable ones carrying Null.
    That matters for exactly what he wants this for: two scenario runs
    stay row-aligned, so a difference between them is a difference in
    the answer and not a change of denominator. It is the `keep_zero`
    argument from 1.53.0 one layer up - a place that cannot be located
    still holds its slot.
    """
    n, nulls = 120, [3, 4, 77]
    state = _install_fake_arcpy(_points(n, nulls=nulls))
    state["fc_array_raises"] = REFUSAL
    pyt = _load_pyt()

    pyt._run_tool("counts", "people", _Messages(), weight_field="People",
                  k_text="25")

    got = state["table"]
    assert len(got) == n, (
        f"{n - len(got)} rows vanished - the convention is that they "
        "keep their place and get Null")
    assert got.loc[nulls, "N_25"].isna().all(), (
        "a row with no coordinates was given a result")
    others = [i for i in range(n) if i not in nulls]
    assert got.loc[others, "N_25"].notna().all(), (
        "a locatable row lost its result")


def test_the_convention_is_announced_to_the_user():
    """BROKEN WITH: deleting the `n_missing` message block.

    The count is the point. A silent drop of three rows in two million
    is indistinguishable from a correct run, and this project's
    standing rule is that the software says what it did.
    """
    state = _install_fake_arcpy(_points(nulls=[1, 2, 3]))
    state["fc_array_raises"] = REFUSAL
    pyt = _load_pyt()
    msg = _Messages()

    pyt._run_tool("counts", "people", msg, weight_field="People",
                  k_text="25")

    said = "\n".join(msg.log)
    assert "3 rows with missing coordinates" in said
    assert "Null results" in said
    assert "EquiPop convention" in said


def test_the_fallback_says_it_fell_back_and_why():
    """BROKEN WITH: dropping the addWarningMessage from _read_columns.

    A cursor read on a few million rows is noticeably slower than the
    fast path. A user who is not told will think the tool has hung,
    and a user who IS told learns something true about their data.
    """
    state = _install_fake_arcpy(_points(nulls=[5]))
    state["fc_array_raises"] = REFUSAL
    pyt = _load_pyt()
    msg = _Messages()

    pyt._run_tool("counts", "people", msg, weight_field="People",
                  k_text="25")

    said = "\n".join(msg.log)
    assert "row by row" in said, "the slowdown is unexplained"
    assert "ANSWER IS THE SAME" in said, (
        "a user told only that something went wrong will assume the "
        "numbers are suspect")
    assert "NULL GEOMETRY" in said, "the likely cause is not named"
    assert REFUSAL in said, (
        "arcpy's own words must be passed through - they are what a "
        "user will search for")


def test_the_fast_path_is_still_used_when_it_works():
    """BROKEN WITH: making _read_columns always use the cursor.

    The fallback must stay a fallback. FeatureClassToNumPyArray is far
    quicker on a large layer, and a fix that quietly made every run
    slower would be noticed in a teaching session before anybody
    thanked us for it.
    """
    state = _install_fake_arcpy(_points())
    pyt = _load_pyt()
    msg = _Messages()

    pyt._run_tool("counts", "people", msg, weight_field="People",
                  k_text="25")

    said = "\n".join(msg.log)
    assert "row by row" not in said, (
        "the fallback ran on a layer the fast reader could read")
    assert "N_25" in state["table"].columns


def test_the_answer_is_identical_either_way():
    """BROKEN WITH: `_column_array` returning text for a numeric
    column, or losing the OID order.

    THE SAFETY ARGUMENT FOR THE WHOLE CHANGE. Two runs over the same
    locatable rows - one through the fast reader, one forced down the
    fallback - must agree exactly. Asserted against each other rather
    than against stored numbers, which is the same discipline as the
    1.52.0 square-cell identity and the 1.53.0 default-path identity.
    """
    table = _points(nulls=[2, 9])

    state = _install_fake_arcpy(table.copy())
    pyt = _load_pyt()
    pyt._run_tool("counts", "people", _Messages(), weight_field="People",
                  treat_fields=["HighEdu"], k_text="25 50")
    fast = state["table"].copy()

    state = _install_fake_arcpy(table.copy())
    state["fc_array_raises"] = REFUSAL
    pyt = _load_pyt()
    pyt._run_tool("counts", "people", _Messages(), weight_field="People",
                  treat_fields=["HighEdu"], k_text="25 50")
    slow = state["table"].copy()

    cols = [c for c in fast.columns
            if c.startswith(("N_", "R_", "Dist_", "T_"))]
    assert cols, "no result columns to compare - the test is vacuous"
    for c in cols:
        a = fast[c].to_numpy(float)
        b = slow[c].to_numpy(float)
        assert np.array_equal(np.isnan(a), np.isnan(b)), (
            f"{c}: the two readers disagree about WHICH rows are Null")
        m = ~np.isnan(a)
        assert np.allclose(a[m], b[m], rtol=0, atol=0), (
            f"{c}: the fallback changed the answer")


def test_a_null_in_a_text_field_is_covered_by_the_same_fallback():
    """BROKEN WITH: catching only ValueError whose text mentions
    geometry.

    arcpy's `null_value` does not apply to TEXT fields, so a null in a
    category column can refuse the same call for an entirely
    different reason. Falling back on ANY failure covers it for free -
    which is the argument for not matching the message.
    """
    t = _points()
    t["Origin"] = ["dk"] * 60 + ["se"] * 60
    t.loc[[7, 8], "Origin"] = None
    state = _install_fake_arcpy(t)
    state["fc_array_raises"] = "some other arcpy complaint entirely"
    pyt = _load_pyt()
    msg = _Messages()

    pyt._run_tool("counts", "people", msg, weight_field="People",
                  cat_field="Origin", k_text="25")

    assert "row by row" in "\n".join(msg.log)
    got = state["table"]
    assert len(got) == len(t)
    assert any(c.startswith("N_") for c in got.columns)


# ------------------------------------------------------ the property
def test_the_fallback_never_triggers_on_the_message_text():
    """BROKEN WITH: `except ValueError as e: if "geometry" in str(e)`.

    1.51.2 was already bitten by tests that matched a PHRASE of the
    messages that release improved: they failed while the guards they
    watched were untouched. Matching a vendor's error text is the same
    mistake with a worse failure mode - it breaks silently, on an
    Esri update, on a user's machine, and the symptom is the original
    traceback coming back.
    """
    import ast

    src = open(os.path.join(ROOT, "arcgis", "EquiPop.pyt"),
               encoding="utf-8").read()
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef)
              and n.name == "_read_columns")

    handlers = [h for h in ast.walk(fn) if isinstance(h, ast.ExceptHandler)]
    assert handlers, "the fallback has no except clause at all"
    assert any(isinstance(h.type, ast.Name) and h.type.id == "BaseException"
               for h in handlers), (
        "the fallback must trigger on ANY failure of the fast reader")

    # SCANNED AS CODE, because this function's own docstring quotes the
    # anti-pattern it is warning against - and a text search finds its
    # own warning and reports the fix as the defect. 1.53.2's property
    # test made exactly this mistake, which is why it is checked this
    # way here rather than being learned twice.
    for node in ast.walk(fn):
        if isinstance(node, ast.Compare) and any(
                isinstance(o, (ast.In, ast.NotIn)) for o in node.ops):
            left = node.left
            if isinstance(left, ast.Constant) and isinstance(left.value, str):
                assert "numpy" not in left.value.lower(), (
                    f"the fallback branches on arcpy's wording "
                    f"({left.value!r}) - it will stop working the day "
                    "Esri rewords it")
                assert "geometry" not in left.value.lower(), (
                    f"the fallback branches on arcpy's wording "
                    f"({left.value!r})")


def test_no_coordinate_read_in_the_pro_door_skips_the_fallback():
    """BROKEN WITH: reverting any of the four reads to a direct call.

    **THE FIRST VERSION OF THIS TEST SCANNED ONLY `_read_input`, AND
    THAT WAS NOT ENOUGH.** An audit of the property across the whole
    codebase found the same defect at two more call sites - the
    barrier table and the barrier point layer - each with a correct
    `isfinite` mask three or four lines BELOW a fast read that dies
    first. Exactly John's bug, in a path the first fix did not touch.
    1.53.2 found seven copies of a k parser the same way. The scan is
    module-wide now, with the exceptions named rather than implied.
    """
    import ast

    src = open(os.path.join(ROOT, "arcgis", "EquiPop.pyt"),
               encoding="utf-8").read()
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)

    # ALLOWED BY PROPERTY, NOT BY NAME. The first draft of this listed
    # function names, and every one of them was a guess that the test
    # then corrected. A name list also goes stale the moment a function
    # is renamed, which is how this project's reachability matrix went
    # wrong (BACKLOG 333). Two real properties make a direct read safe:
    #
    #   * it is inside a try - the caller handles arcpy's refusal
    #     itself and degrades, which _sample_lonlat and
    #     _distinct_values both do and document
    #   * it reads an OBJECTID only, which is never null
    #
    # Anything else is a coordinate or attribute read that must go
    # through _read_columns.
    parent = {}
    for node in ast.walk(tree):
        for kid in ast.iter_child_nodes(node):
            parent[kid] = node

    def _in_try(node):
        cur = node
        while cur in parent:
            cur = parent[cur]
            if isinstance(cur, ast.Try):
                return True
        return False

    def _oid_only(node):
        if len(node.args) < 2:
            return False
        fields = node.args[1]
        if not isinstance(fields, ast.List) or len(fields.elts) != 1:
            return False
        only = fields.elts[0]
        return isinstance(only, ast.Name) and "oid" in only.id.lower()

    def _owner(line):
        best = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.lineno <= line <= getattr(node, "end_lineno",
                                                  node.lineno):
                    best = node.name
        return best

    offenders = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("FeatureClassToNumPyArray",
                                       "TableToNumPyArray")):
            continue
        if _owner(node.lineno) == "_read_columns":
            continue                      # the fast path itself
        if _in_try(node) or _oid_only(node):
            continue
        offenders.append(f"{_owner(node.lineno)}() at line "
                         f"{node.lineno}: "
                         f"{lines[node.lineno - 1].strip()[:56]}")
    assert not offenders, (
        "a coordinate read bypasses _read_columns, so arcpy's refusal "
        "reaches the user instead of the convention:\n  "
        + "\n  ".join(offenders))

    # and the four that matter really do go through it
    assert src.count("_read_columns(") >= 5, (
        "expected the definition plus four call sites; found "
        f"{src.count('_read_columns(')}")


def test_the_qgis_door_keeps_a_null_geometry_row_and_nulls_it():
    r"""BROKEN WITH: `if g is None or g.isEmpty(): continue` in
    qgis/equipop_qgis/base.py - i.e. dropping the row instead of
    NaN-ing it.

    **THE FIRST VERSION OF THIS TEST ASSERTED THE SOURCE TEXT** -
    `re.search(r"g is None or g\.isEmpty\(\)", qgis)` - and a break
    that kept the condition while changing `xs.append(np.nan)` to
    `continue` sailed straight past it. That is 370's finding again:
    the test watched the MECHANISM and had no opinion about the
    CONSEQUENCE. Behavioural now, through the real reader.

    The QGIS door was the correct implementation all along, which is
    what made the Pro gap visible. Nothing was guarding it.
    """
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    sys.path.insert(0, os.path.join(ROOT, "qgis"))
    import qgis_stub
    qgis_stub.install()
    from test_qgis_door import _run
    from equipop_qgis.alg_counts import CountsAndShares

    n = 60
    rng = np.random.default_rng(3)
    tab = pd.DataFrame({"x": rng.uniform(0, 2000, n),
                        "y": rng.uniform(0, 2000, n),
                        "People": rng.integers(1, 30, n).astype(float)})
    tab.loc[[5, 6], ["x", "y"]] = np.nan      # no geometry at all
    src = qgis_stub._Source(tab)

    out, _fb = _run(CountsAndShares, src, pop="People", k="20")

    assert len(out) == n, (
        f"{n - len(out)} rows vanished - the QGIS door must keep them")
    col = next(c for c in out.columns if c.startswith("N_"))
    assert out[col].isna().iloc[[5, 6]].all(), (
        "a row with no geometry was given a result")
    keep = [i for i in range(n) if i not in (5, 6)]
    assert out[col].iloc[keep].notna().all(), (
        "a locatable row lost its result")


def test_both_guis_agree_about_an_unlocatable_row():
    """BROKEN WITH: either door's handling, independently.

    THE PROPERTY, across the two GUIs. The convention is engine-level,
    so the two doors must not merely each be defensible - they must
    give the SAME answer for the same input. Pro reaching the
    convention through a fallback and QGIS reaching it directly is an
    implementation difference that must not be a behavioural one.
    """
    n, nulls = 60, [5, 6]
    rng = np.random.default_rng(3)
    tab = pd.DataFrame({"x": rng.uniform(0, 2000, n),
                        "y": rng.uniform(0, 2000, n),
                        "People": rng.integers(1, 30, n).astype(float)})
    tab.loc[nulls, ["x", "y"]] = np.nan

    import sys
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    sys.path.insert(0, os.path.join(ROOT, "qgis"))
    import qgis_stub
    qgis_stub.install()
    from test_qgis_door import _run
    from equipop_qgis.alg_counts import CountsAndShares
    q, _ = _run(CountsAndShares, qgis_stub._Source(tab.copy()),
                pop="People", k="20")
    qcol = next(c for c in q.columns if c.startswith("N_"))

    pro_tab = pd.DataFrame({
        "OBJECTID": np.arange(1, n + 1),
        "SHAPE@X": tab["x"].to_numpy(),
        "SHAPE@Y": tab["y"].to_numpy(),
        "People": tab["People"].to_numpy()})
    state = _install_fake_arcpy(pro_tab)
    state["fc_array_raises"] = REFUSAL        # force the fallback
    pyt = _load_pyt()
    pyt._run_tool("counts", "people", _Messages(), weight_field="People",
                  k_text="20")
    pro = state["table"]

    a = q[qcol].to_numpy(float)
    b = pro["N_20"].to_numpy(float)
    assert np.array_equal(np.isnan(a), np.isnan(b)), (
        "the two GUIs disagree about WHICH rows are unlocatable")
    m = ~np.isnan(a)
    assert np.allclose(a[m], b[m]), (
        "the two GUIs disagree about the answer for the rows they "
        "can locate")


def test_the_engine_itself_gives_null_for_an_unlocatable_row():
    """BROKEN WITH: dropping the finite-coordinate mask in the engine.

    The doors are where the convention is reached; the engine is where
    it is DEFINED. Tested directly, because a door fix must not be
    mistaken for the rule it honours - which is how 353's negative
    guard came to be unreachable.
    """
    from equipop.cells import build_cells

    df = pd.DataFrame({
        "E": [0.0, 100.0, np.nan, 300.0],
        "N": [0.0, 100.0, 200.0, np.nan],
        "w": [5.0, 5.0, 5.0, 5.0],
    })
    cd = build_cells(df, "E", "N", unit_size=100.0, weights="w")
    total = float(np.nansum(cd.n))
    assert total == 10.0, (
        f"an unlocatable row reached the cell grid (total {total}, "
        "expected the 10 people in the two locatable rows)")
    assert np.isfinite(cd.E).all() and np.isfinite(cd.N).all(), (
        "a cell was created with a non-finite position")


# ------------------------- 381: whose voice refuses a non-finite one
def test_an_infinite_coordinate_is_dropped_in_equipops_voice():
    """BROKEN WITH: `bad = df[e_col].isna() | df[n_col].isna()`, the
    predicate cells.py used before.

    `.isna()` is True only for NaN and None. An INFINITE coordinate
    passed it and reached `.astype(int)` twelve lines later, where
    pandas refuses with "Cannot convert non-finite values (NA or inf)
    to integer ... cast to Int64" - a sentence about pandas dtypes,
    shown to somebody who typed a coordinate.
    THE ANSWER WAS NEVER WRONG. The voice was not EquiPop's, which is
    the same complaint John's original traceback made about arcpy.
    The right predicate was already in this function, eight lines
    above, on the weight column: `blank = ~np.isfinite(wv)`.
    """
    from equipop.cells import build_cells

    df = pd.DataFrame({"E": [0.0, 100.0, np.inf, 300.0],
                       "N": [0.0, 100.0, 0.0, -np.inf],
                       "w": [5.0, 5.0, 5.0, 5.0]})
    cd = build_cells(df, "E", "N", unit_size=100.0, weights="w")
    assert float(np.nansum(cd.n)) == 10.0, (
        "the two infinite rows were not dropped")
    assert np.isfinite(cd.E).all() and np.isfinite(cd.N).all()


def test_a_non_numeric_coordinate_is_dropped_too():
    """BROKEN WITH: `if False:` around the drop in cells.py.

    **THIS TEST DOES NOT COVER THIS RELEASE'S CHANGE, AND ITS FIRST
    DOCSTRING CLAIMED IT DID.** Text in a coordinate column - a real
    thing in a CSV - was already handled, by the to_numeric loop at
    the TOP of build_cells, long before the predicate this release
    touched. The break-check is what caught the false claim: removing
    the coercion I had added changed nothing, because it was
    redundant.
    Kept, because the behaviour is worth pinning and nothing else
    pinned it. Re-labelled, because a test that takes credit for a
    change it cannot see is how a suite comes to look more thorough
    than it is - and that is this project's recurring defect, in the
    tests rather than the code.
    """
    from equipop.cells import build_cells

    df = pd.DataFrame({"E": [0.0, 100.0, "not a number"],
                       "N": [0.0, 100.0, 0.0],
                       "w": [5.0, 5.0, 5.0]})
    cd = build_cells(df, "E", "N", unit_size=100.0, weights="w")
    assert float(np.nansum(cd.n)) == 10.0


def test_the_stata_counts_path_uses_the_same_predicate_as_dispatch():
    """BROKEN WITH: `valid = df["_x"].notna() & df["_y"].notna()`, as
    knn_to_rows had it.

    `dispatch()` has used `np.isfinite(x) & np.isfinite(y)` for
    releases, and the COUNTS branch is the one path that does not go
    through it - it re-derived its own weaker mask. So the correct
    predicate existed in the same file and this path could not reach
    it, which is BACKLOG 380's shape inside 380's own release.
    The row must survive and come back missing, not raise.
    """
    from equipop.stata_bridge import knn_to_rows

    out = knn_to_rows(np.array([0.0, 100.0, np.inf]),
                      np.array([0.0, 100.0, 0.0]), [2],
                      weight=np.array([5.0, 5.0, 5.0]))
    col = next(c for c in out if c.startswith("N_"))
    got = list(out[col])
    assert len(got) == 3, "the row lost its slot"
    assert np.isfinite(got[0]) and np.isfinite(got[1])
    assert not np.isfinite(got[2]), (
        "the unlocatable row was given an answer")


# ------------------------------- 382: the engine guards itself too
def test_the_stats_engine_refuses_a_cell_with_no_position():
    """BROKEN WITH: removing the _bad_xy block from run_knn_stats.

    Every door masks before calling, so this is reachable only from
    the Python API - and reached, it printed "[stats] 3 cells", built
    an all-NaN distance vector, sorted it in whatever order numpy
    produced, and died on `int(nan)` with a bare numpy message.
    fastcounts is already strict by accident (scipy's cKDTree refuses
    non-finite input). This is 353's lesson applied deliberately: a
    convention honoured at four doors is still worth guarding in the
    engine, because the engine is what a script calls.
    """
    from equipop.analysis import run_knn_stats
    from equipop.cells import CellData

    cd = CellData(E=np.array([0.0, 100.0, np.nan]),
                  N=np.array([0.0, 100.0, 0.0]),
                  n=np.array([5.0, 5.0, 5.0]))
    with pytest.raises(ValueError) as caught:
        run_knn_stats(cd, k_values=[2], stats={})
    msg = str(caught.value)
    assert "no position" in msg and "1 of 3" in msg
    assert "np.isfinite" in msg, (
        "a refusal that does not say what to do is half a refusal")
    assert "cannot convert float NaN" not in msg, (
        "numpy is still speaking for EquiPop")


# ------------------------------- 383: a silent drop is still a drop
def test_a_join_layer_feature_with_no_geometry_is_counted():
    """BROKEN WITH: putting the bare `continue` back in
    alg_continental's centroid reader.

    The drop was silent, so the feature count reported afterwards
    could not be reconciled with the layer's own count. Two lines
    further on in the same function an UNSUPPORTED geometry type is
    counted - so one kind of drop was reported and another hidden.
    """
    src = open(os.path.join(ROOT, "qgis", "equipop_qgis",
                            "alg_continental.py"), encoding="utf-8").read()
    body = src[src.index("xs, ys, vals = [], [], []"):]
    assert "no_geom += 1" in body, "the drop is silent again"
    assert "have no" in body and "geometry" in body, (
        "nothing reports the count to the user")


def test_a_barrier_point_with_no_geometry_reaches_the_counting_mask():
    """BROKEN WITH: the bare `continue` in barriers.py's point branch.

    The mask below it is correct and its warning counts - the features
    were being dropped before either could see them, so the warning
    undercounted. NaN instead, and the code that was already right
    does the work.
    """
    src = open(os.path.join(ROOT, "qgis", "equipop_qgis", "barriers.py"),
               encoding="utf-8").read()
    pts = src[src.index("if _is_kind(source, 0):"):]
    head = pts[:pts.index("ok = np.isfinite")]
    assert "xs.append(np.nan)" in head, (
        "a null-geometry barrier point is dropped before the isfinite "
        "mask can count it")
    assert "ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(v)" in pts
