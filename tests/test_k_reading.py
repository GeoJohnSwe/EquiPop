"""BACKLOG 372-379 - how a door reads the k box, and who checks it.

John, ArcGIS Pro, 7 October 2026:

    ValueError: give k_values and/or r_values

raised from analysis.py after Run, from a dialog that had reported
nothing wrong. He asked "any idea?" and the answer was six separate
defects, one of which had been shipping since 1.35.

THE SHAPE OF THE WHOLE RELEASE: equipop/doors/numbers.py exists so
that "read a number a person typed" is written once. Its docstring
says so. When this release started, reading k was implemented FIVE
times - the shared reader, Pro's `int(round(_numlist()))`, alg_stats'
bare `int()`, and one copy each in alg_continental and alg_demography
- and the shared one, the only correct one, was called by a single
door of four.

So most of the tests here assert PROPERTIES rather than cases. A case
test says "this input gives that output"; a property test says "there
is one reader and every door comes through it", which is the thing
that was false. Testing cases one at a time is what let a fifth copy
appear without anybody noticing.

Each test's docstring names what it was BROKEN WITH, and each was
actually broken that way.
"""
import os
import re

import pytest

from equipop.doors.numbers import (BadNumber, K_OR_R, check_k_and_r,
                                   intlist, is_blank, numlist,
                                   thousands_hint, to_int)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QGIS = os.path.join(ROOT, "qgis", "equipop_qgis")
PYT = os.path.join(ROOT, "arcgis", "EquiPop.pyt")


def _read(path):
    return open(path, encoding="utf-8").read()


# ------------------------------------------------------------ 375
# John's ruling: a separator in a k box is REFUSED, not interpreted.

@pytest.mark.parametrize("typed,meant", [
    ("1,000", "1000"),
    ("1.000", "1000"),
    ("10,000", "10000"),
    ("1,600", "1600"),
])
def test_a_thousands_separator_in_k_is_refused_and_named(typed, meant):
    """BROKEN WITH: dropping the isinstance(text, str) separator block
    from to_int - which is what the code did before.

    MEASURED ON THE REAL DOOR BEFORE THE FIX: k='1.000' ran to
    completion with a neighbourhood of ONE PERSON and wrote
    Mean_income_1. Nothing refused it, nothing warned, and the column
    name is the only evidence there was ever a problem.

    John's ruling, 7 October 2026: "yes - in the next round we should
    refuse 1,000". Refusing is the honest half - interpreting guesses
    at intent, and the message can suggest without deciding.
    """
    with pytest.raises(BadNumber) as caught:
        intlist(typed)
    msg = str(caught.value)
    assert typed in msg, "the refusal must quote what was typed"
    assert meant in msg, (
        "the refusal must say what it thinks you meant - a user who "
        "has to guess twice has not been helped")
    assert "PEOPLE" in msg


def test_a_fraction_of_a_person_gets_a_different_sentence():
    """BROKEN WITH: using _clean() to decide which mistake it was.

    TWO MISTAKES, TWO MESSAGES. '1,000' is a thousands separator;
    '1,6' is a decimal, and one and a half people is not a thing
    either. The first draft of this decided between them by asking
    _clean() what the number was - and _clean is the function that
    MISREADS it, so for '1,000' it concluded the user meant 1 and
    advised "if you meant 1, write 1". The test is the thousands
    PATTERN: three digits after the separator.
    """
    with pytest.raises(BadNumber) as caught:
        intlist("1,6")
    assert "fraction of a person" in str(caught.value)
    with pytest.raises(BadNumber) as caught:
        intlist("1,000")
    assert "thousands separator" in str(caught.value)
    assert "fraction" not in str(caught.value)


def test_a_radius_keeps_its_decimal_comma():
    """BROKEN WITH: routing radii through intlist too.

    THE OTHER HALF OF JOHN'S RULING - "good to keep it for radii".
    500,5 metres is a real distance and a Norwegian keyboard produces
    that comma, which is the whole reason doors/numbers.py exists
    (BACKLOG 320). Refusing a separator is right for a COUNT OF
    PEOPLE and wrong for a measurement, so the two readers must stay
    different.
    """
    assert numlist("500,5") == [500.5]
    assert numlist("500.5") == [500.5]
    assert numlist("500,5 800") == [500.5, 800.0]
    assert numlist("344,5;500") == [344.5, 500.0]


def test_a_number_from_code_is_not_typed_text():
    """BROKEN WITH: applying the separator rule to any value, not
    only to str.

    to_int(800.0) must stay 800. str(800.0) contains a point, so a
    rule written without the isinstance check refuses the engine's
    own values and the package stops importing cleanly.
    """
    assert to_int(800) == 800
    assert to_int(800.0) == 800
    assert to_int("800") == 800


def test_a_comma_between_values_still_separates_them():
    """BROKEN WITH: `loose = str(text or "")`, i.e. treating every
    comma as numeric.

    A COMMA MEANS TWO THINGS AND BOTH ARE RIGHT. Machines 3 and 4
    have accepted '300, 500' as two k values since they were written
    and test_qgis_continental asserts it. That test is what caught
    this when the shared reader first went in - the fix for one real
    defect would have removed a real documented capability.
    A count of people cannot have a decimal at all, which is exactly
    what frees the comma to mean "next value" here while it stays a
    decimal point in a radius box.
    """
    assert intlist("300, 500") == [300, 500]
    assert intlist("300 ,500") == [300, 500]
    assert intlist("300;500") == [300, 500]
    with pytest.raises(BadNumber):
        intlist("300,500")          # between digits: ambiguous, refused


# ------------------------------------------------------------ 376
def test_the_module_no_longer_contradicts_itself_about_a_space():
    """BROKEN WITH: removing the thousands_hint call from intlist.

    to_float('1 000') is 1000.0 - the space is a thousands separator.
    numlist('1 000') is [1.0, 0.0] - the space is a list separator.
    BOTH IN ONE FILE, which is how '1 000' in a k box became k=1 and
    k=0 and then refused with "got [0]", a sentence about a number
    the user never typed.
    The ambiguity is real and cannot be resolved by rule - '200 100'
    IS two k values. So it is not resolved silently: the split stays,
    and the refusal that was going to happen anyway now carries the
    suggestion.
    """
    assert thousands_hint("1 000")
    assert thousands_hint("1,000")
    assert thousands_hint("200 1600") is None, (
        "two legitimate k values must not be read as a typo")
    # '200 100' DOES match the pattern, because nothing in the text
    # distinguishes it from '1 000'. That is why the hint is a
    # suggestion gated behind an independent refusal - and THIS is
    # the property that matters: it never reaches a user whose input
    # was fine.
    assert thousands_hint("200 100") is not None
    assert intlist("200 100") == [200, 100]
    assert check_k_and_r("200 100", "") is None, (
        "a loose hint leaked to a user whose k values were correct")

    with pytest.raises(BadNumber) as caught:
        intlist("1 000")
    msg = str(caught.value)
    assert "1000" in msg and "two of them" in msg
    assert intlist("200 100") == [200, 100]


# ------------------------------------------------------------ 378
def test_whitespace_and_separators_count_as_an_empty_box():
    """BROKEN WITH: `return not str(text).strip()` without the
    semicolon, or testing the string for truth as the old guard did.

    THIS IS THE ONE THAT PRODUCED JOHN'S TRACEBACK. Pro's `Required`
    asks whether a box has A VALUE, and a space IS a value - so a k
    box holding one space satisfied Pro, satisfied the dialog's own
    `if not _txt(pm, "k")` guard, and reached the engine as None.
    """
    for blank in ("", " ", " ", "\t", ";", "; ;", "  ;  "):
        assert is_blank(blank), f"{blank!r} should count as empty"
    for filled in ("1000", "0", "200 1600"):
        assert not is_blank(filled)


def test_the_check_covers_the_three_shapes_a_door_can_have():
    """BROKEN WITH: `k_required` and `need_one` collapsed into one
    flag.

    The four doors genuinely differ, and flattening them puts a wrong
    message in front of somebody:
      machines 1, 2 - k OR r, either alone is fine
      machine 4     - k, no radius box, k compulsory
      machine 3     - k, no radius box, and BLANK k is a real choice
                      (it means the point table)
    A door asking for the wrong shape reads as a fixed bug.
    """
    # machines 1 and 2
    assert check_k_and_r("", "")[1] == K_OR_R
    assert check_k_and_r(" ", "")[1] == K_OR_R
    assert check_k_and_r("1000", "") is None
    assert check_k_and_r("", "500") is None
    # machine 4: k compulsory, no radius
    bad = check_k_and_r(" ", "", need_one=False, k_required=True)
    assert bad and bad[0] == "k" and "digits only" in bad[1]
    # machine 3: blank k is a legitimate choice
    assert check_k_and_r("", "", need_one=False) is None
    assert check_k_and_r(" ", "", need_one=False) is None
    # but an unparseable k is refused everywhere
    for kw in ({}, {"need_one": False},
               {"need_one": False, "k_required": True}):
        got = check_k_and_r("1,000", "", **kw)
        assert got and got[0] == "k" and "thousands" in got[1]


def test_a_one_metre_radius_from_a_mistyped_thousand_is_caught():
    """BROKEN WITH: dropping the thousands branch from the r check.

    '1 500' in a radius box reads as radii of 1 m and 500 m. Both are
    positive, so no downstream guard can refuse it, and a 1 m
    neighbourhood holds almost nobody - the same silent wrong answer
    as k=1, by the same typo, in the box John's ruling deliberately
    left permissive.
    """
    got = check_k_and_r("", "1 500")
    assert got and got[0] == "r"
    assert "almost nobody" in got[1] and "1500" in got[1]
    assert check_k_and_r("", "500,5") is None, (
        "a decimal comma in a radius must still be fine")
    assert check_k_and_r("", "500 1000") is None


# --------------------------------------------- 377, 379: PROPERTIES
def test_no_door_reads_k_with_its_own_parser():
    """BROKEN WITH: putting `int(round(v)) for v in _numlist(k_text)`
    back into the .pyt, or `int(float(piece))` back into either
    continental or demography.

    THE PROPERTY THAT WAS FALSE. Five implementations of "read k from
    a box" existed when this release started, and the only correct
    one was reached from one door of four. Every one of the other four
    truncated silently, which is the behaviour
    doors.numbers.to_int was written to refuse - its docstring has
    said "a silently rounded k is a wrong answer that looks right"
    since 1.47.
    A per-door test cannot catch a FIFTH copy appearing. This can.
    """
    import ast

    def _calls(src):
        """int(round(..)) and int(float(..)) in CODE, not in prose.

        Scanned with ast rather than a regex because the comments
        added by this release QUOTE the old lines - a text search
        finds its own description of the bug and reports the fix as
        the defect. The first draft of this test did exactly that.
        """
        found = []
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "int" and node.args):
                continue
            inner = node.args[0]
            if (isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Name)
                    and inner.func.id in ("round", "float")):
                found.append((node.lineno, f"int({inner.func.id}(...))"))
        # AND THE BARE FORM, which the first draft of this test let
        # through: `[int(v) for v in k_text.split()]` has a plain name
        # as its argument, so a scan looking for a nested call misses
        # it - and that is the exact shape alg_stats had. Restoring it
        # broke nothing, which is how a test passes while the defect
        # it was written for is back.
        for node in ast.walk(tree):
            if not isinstance(node, (ast.ListComp, ast.GeneratorExp,
                                     ast.SetComp)):
                continue
            splits = any(
                isinstance(g.iter, ast.Call)
                and isinstance(g.iter.func, ast.Attribute)
                and g.iter.func.attr == "split"
                for g in node.generators)
            if not splits:
                continue
            for sub in ast.walk(node.elt):
                if (isinstance(sub, ast.Call)
                        and isinstance(sub.func, ast.Name)
                        and sub.func.id in ("int", "float")):
                    found.append((node.lineno,
                                  f"{sub.func.id}() over a .split()"))
        return found

    # The one deliberate exception, declared here so it is visible:
    # _intlist's fallback for a package too old to have the shared
    # reader. A toolbox that will not open is worse than one that
    # truncates, and that branch is unreachable from a current
    # install.
    ALLOWED = {("EquiPop.pyt", "_intlist")}

    def _owner(src, line):
        tree = ast.parse(src)
        best = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", node.lineno)
                if node.lineno <= line <= end:
                    best = node.name
        return best

    offenders = []
    files = [(PYT, _read(PYT))] + [
        (os.path.join(QGIS, f), _read(os.path.join(QGIS, f)))
        for f in sorted(os.listdir(QGIS)) if f.startswith("alg_")]
    for path, src in files:
        name = os.path.basename(path)
        for line, what in _calls(src):
            if (name, _owner(src, line)) in ALLOWED:
                continue
            offenders.append(f"{name}:{line} {what} in "
                             f"{_owner(src, line)}()")
    assert not offenders, (
        "a door is parsing k itself again instead of calling "
        "equipop.doors.numbers.intlist:\n  " + "\n  ".join(offenders))


def test_every_qgis_door_with_a_k_box_validates_before_run():
    """BROKEN WITH: deleting checkParameterValues from base.py, or
    removing NEEDS_A_NEIGHBOURHOOD from alg_stats.

    BACKLOG 305 added "you need k or r" to the dialog in 1.47.11,
    BY HAND, in one algorithm. The other three that reach the same
    engine refusal went without it until John hit one of them
    eighteen months later. The check lives in EquipopAlgorithm now,
    so a NEW door gets it by existing rather than by somebody
    remembering.
    """
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    sys.path.insert(0, os.path.join(ROOT, "qgis"))
    import qgis_stub
    qgis_stub.install()
    from equipop_qgis.base import EquipopAlgorithm

    assert "def checkParameterValues" in _read(
        os.path.join(QGIS, "base.py")), (
        "the shared check is gone; four doors will drift again")

    for f in sorted(os.listdir(QGIS)):
        if not f.startswith("alg_"):
            continue
        src = _read(os.path.join(QGIS, f))
        if '"k"' not in src:
            continue
        assert "def checkParameterValues" not in src, (
            f"{f} has its own copy of the check - it must inherit the "
            "one in base.py, which is the whole point of 378")
    # and the base class really routes to the shared rule
    import inspect
    body = inspect.getsource(EquipopAlgorithm.checkParameterValues)
    assert "check_k_and_r" in body

    # THE PART THE FIRST DRAFT OF THIS TEST MISSED, found by breaking
    # it: inheriting the hook is not enough, a door with BOTH boxes
    # has to DECLARE that one of them is compulsory. Deleting
    # `NEEDS_A_NEIGHBOURHOOD = True` from alg_stats reproduced John's
    # bug exactly and the whole suite stayed green. So this runs the
    # real hook with both boxes empty and insists on a refusal.
    from equipop_qgis.alg_counts import CountsAndShares
    from equipop_qgis.alg_stats import ValueStatistics
    from equipop_qgis.alg_demography import SpatialDemography
    for cls in (CountsAndShares, ValueStatistics):
        alg = cls()
        alg.initAlgorithm()
        ok, why = alg.checkParameterValues({"k": "", "r": ""}, {})
        assert ok is False, (
            f"{cls.__name__} accepts a run with neither k nor r - this "
            "is BACKLOG 305 and 378 coming back")
        assert "neighbourhood" in why
        # and a space must not buy its way past
        ok, why = alg.checkParameterValues({"k": " ", "r": ""}, {})
        assert ok is False, f"{cls.__name__} is fooled by a space"
    # machine 4: k compulsory, and whitespace is not a k
    alg = SpatialDemography()
    alg.initAlgorithm()
    ok, why = alg.checkParameterValues({"k": " "}, {})
    assert ok is False and "PEOPLE" in why


def test_every_pro_door_with_a_k_box_validates_before_run():
    """BROKEN WITH: removing the _k_or_r_message call from any of the
    four doors' updateMessages.

    Pro has no base class to inherit from - each tool is its own
    class, which is exactly why the hand-written guard reached one of
    them. So the property is asserted against the source: a door with
    a k box has an updateMessages, and it calls the shared helper.
    """
    src = _read(PYT)
    classes = [(m.start(), m.group(1)) for m in
               re.finditer(r"^class (\w+):", src, re.M)]
    classes.append((len(src), "EOF"))
    checked = []
    for (a, name), (b, _) in zip(classes, classes[1:]):
        body = src[a:b]
        if '_p("k"' not in body:
            continue
        assert "def updateMessages" in body, (
            f"{name} has a k box and no updateMessages, so nothing "
            "can be said about it until after Run")
        assert "_k_or_r_message(" in body, (
            f"{name} does not call the shared k/r check")
        checked.append(name)
    assert sorted(checked) == ["ContinentalRasters", "CountsShares",
                              "SpatialDemography", "ValueStatistics"], (
        f"expected all four engine doors, got {sorted(checked)}")


def test_the_prediction_and_the_engine_agree_about_k():
    """BROKEN WITH: `ks = [t for t in (k_text or "").split()]` in
    predict_result_fields - the line as it stood.

    BACKLOG 337 made the field-name PREDICTION and the engine share
    one formatter, and its comment says so. It covered the radius and
    left k using raw text, so for k='1.000' the prediction promised
    N_1_000 while the engine made N_1 - and the shapefile overflow
    check, the "fields already exist" check and the user's own
    preview all named columns the run would not produce.
    Parsing through the engine's own reader makes them agree by
    construction, which is stronger than a test comparing them.
    """
    from equipop.doors.fields import predict_result_fields
    names = predict_result_fields("counts", "1000", "", "", ["X"], [],
                                  [], False, False)
    assert "N_1000" in names
    # and a separator cannot reach a column name at all any more
    for typed in ("1.000", "1,000"):
        with pytest.raises(BadNumber):
            predict_result_fields("counts", typed, "", "", ["X"], [],
                                  [], False, False)


def test_field_prediction_no_longer_raises_raw_python_at_a_dialog():
    """BROKEN WITH: `rs = [_fmt_num(t) for t in (r_text or "").split()]`,
    i.e. handing raw text to numeric_tag.

    THE WORST OF THE SIX, AND THE ONE THAT EXPLAINS THE PATTERN.
    BACKLOG 320 added a locale-proof parse to alg_counts at line 445.
    Field-name prediction, at line 395, had ALREADY touched the same
    text with a bare float() - so a radius of '500,5' produced

        ValueError: could not convert string to float: '500,5'

    the exact raw message 320 exists to prevent, from 50 lines ABOVE
    320's fix, in both QGIS doors. In Pro it was worse: prediction
    runs inside updateMessages, so the DIALOG'S VALIDATION CRASHED
    while the user typed.
    THE FIX WAS PLACED AFTER THE FAILURE. 353 was a guard unreachable
    from the path that could trip it; 368 was a hint classified and
    never rendered; this is the third in three releases. When a fix
    goes in, follow the input from the EARLIEST point a door touches
    it, not from the line you happen to be reading.
    """
    from equipop.doors.fields import predict_result_fields
    names = predict_result_fields("counts", "", "500,5", "", ["X"], [],
                                  [], False, False)
    assert any("500_5" in n for n in names), (
        "a decimal-comma radius must now reach a column name")
    with pytest.raises(BadNumber):
        predict_result_fields("counts", "", "oops", "", ["X"], [],
                              [], False, False)


def test_numeric_tag_cannot_resurrect_the_raw_message():
    """BROKEN WITH: `v = float(value)` unconditionally in
    labels.numeric_tag.

    The callers are fixed, so nothing should hand this text any more.
    It is locale-proof anyway because it is the LAST common point
    before a column name: a future caller must not be able to bring
    that message back. Belt and braces, deliberately.
    """
    from equipop.labels import numeric_tag
    assert numeric_tag(500.5) == "500_5"
    assert numeric_tag("500,5") == "500_5"
    assert numeric_tag("500.5") == "500_5"
    with pytest.raises((BadNumber, ValueError)) as caught:
        numeric_tag("oops")
    assert "could not convert string to float" not in str(caught.value), (
        "the raw Python message is back")


def test_the_engines_own_refusal_is_still_there():
    """BROKEN WITH: deleting the `if not (k_values or r_values)` raise
    from analysis.run_knn_stats.

    The doors refuse earlier and better now, but the Python API takes
    k_values directly and never passes a dialog. The engine's guard is
    the one that protects a script, so improving the door must not be
    taken as licence to remove it - which is how 353's negative-value
    guard became unreachable in the first place.
    """
    import numpy as np
    from equipop.analysis import run_knn_stats
    from equipop.cells import CellData
    cd = CellData(E=np.array([0.0, 100.0]), N=np.array([0.0, 100.0]),
                  n=np.array([1.0, 1.0]))
    with pytest.raises(ValueError, match="give k_values and/or r_values"):
        run_knn_stats(cd, k_values=None, stats={"v": ["mean"]})
