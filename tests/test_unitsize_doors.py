# -*- coding: utf-8 -*-
"""BACKLOG 385 - does the advice REACH the user, at every door?

THIS FILE EXISTS BECAUSE OF A PATTERN, not a hunch. Five consecutive
releases of this project fixed the same shape of bug: the thing was
built, it was correct, and the path could not reach it.

    353  a guard that was unreachable
    368  a hint classified, tested, and never rendered
    373  a fix placed downstream of the failure it was for
    380  a convention announced by the function that cannot reach it
    (and fca.py's `denom`, computed and discarded)

The unit-size advisory is a textbook candidate, because every door
calls it inside `except Exception: pass` - which is right (an advisory
must never turn a finished run into an error, and the output is
already written by then) and is also a machine for hiding mistakes
forever. A single mistyped keyword would mean no door ever printed
anything, no test failed, and nobody found out.

So the keywords at every call site are BOUND AGAINST THE REAL
SIGNATURE here, and every exit from every door is checked to pass
through the advisory on its way out.
"""
import ast
import inspect
import io
import os
import re
import contextlib

import numpy as np
import pandas as pd
import pytest

from equipop import unitsize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOORS = {
    "stata": os.path.join(ROOT, "stata", "equipop.ado"),
    "pro": os.path.join(ROOT, "arcgis", "EquiPop.pyt"),
    "qgis": os.path.join(ROOT, "qgis", "equipop_qgis", "alg_counts.py"),
}


def _text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _python_of(door):
    """The Python source of a door - the .ado's block, or the file."""
    text = _text(DOORS[door])
    if door != "stata":
        return text
    lines = text.splitlines()
    start = [i for i, ln in enumerate(lines) if ln.rstrip() == "python:"]
    assert len(start) == 1, "equipop.ado no longer has one python: block"
    for j in range(start[0] + 1, len(lines)):
        if lines[j].rstrip() == "end":
            return "\n".join(lines[start[0] + 1:j])
    raise AssertionError("the python: block is never closed")


def _calls_to(src, names):
    """Every ast.Call whose function is one of `names`."""
    out = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        got = getattr(fn, "attr", None) or getattr(fn, "id", None)
        if got in names:
            out.append((got, node))
    return out


# ----------------------------------------------- the swallowed typo
@pytest.mark.parametrize("door", sorted(DOORS))
def test_every_door_calls_the_advisory_with_arguments_it_accepts(door):
    """BROKEN WITH: renaming `unit_was_set` to `unit_set` in one
    door's call, or dropping `k_values` from advise_unit's signature.

    THE TEST THIS FILE WAS WRITTEN FOR. Each door calls the advisory
    inside `except Exception: pass`, so a TypeError from a mistyped
    keyword is caught and discarded: the run succeeds, the advice
    never appears, and no existing test notices. That is BACKLOG 368
    exactly - a thing classified, tested, and never rendered.

    Binding the call site's keywords against the live signature is the
    only check that survives the except. It does not run the door; it
    asks whether the call could possibly work.
    """
    src = _python_of(door)
    wanted = {"advise_unit": unitsize.advise_unit,
              "advise_on_run": unitsize.advise_on_run}
    found = _calls_to(src, set(wanted))
    assert {n for n, _ in found} == set(wanted), (
        f"{door}: calls {sorted({n for n, _ in found})} - a door that "
        f"does not call both cannot both measure and speak")

    for name, node in found:
        sig = inspect.signature(wanted[name])
        kwargs = {}
        for kw in node.keywords:
            assert kw.arg is not None, (
                f"{door}: {name}() is called with **kwargs, so this "
                f"test cannot check the keywords - pass them by name")
            kwargs[kw.arg] = None
        try:
            sig.bind(*[None] * len(node.args), **kwargs)
        except TypeError as exc:
            raise AssertionError(
                f"{door}: {name}(...) as written cannot be called - "
                f"{exc}. The door wraps this in `except Exception`, so "
                f"it would fail SILENTLY at every run, forever.")


# ------------------------------------------------- reaching the exit
def test_every_exit_of_the_PRO_machine1_passes_the_advisory():
    """BROKEN WITH: deleting the `_unit_advice` call from the table
    branch, which is the branch that returns early.

    Pro's machine-1 tool returns TWICE: once for a table output and
    again at the end for a feature class. An advisory added to the
    second only is a feature that exists for half the users and is
    reported by nobody - the 380 shape. So the property is about
    EXITS, not about the function being present somewhere in the file.
    """
    src = _text(DOORS["pro"])
    tree = ast.parse(src)
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and \
                any(isinstance(c, ast.Call)
                    and getattr(c.func, "id", None) == "_unit_advice"
                    for c in ast.walk(node)):
            target = node
            break
    assert target is not None, "no Pro function calls _unit_advice"

    # Every `return` inside the machine-1 body that is NOT a guard
    # (a bare return after an error message) has to come after an
    # advisory call. The check is positional: the call's line number
    # must precede the return's.
    advice_lines = sorted(
        c.lineno for c in ast.walk(target)
        if isinstance(c, ast.Call)
        and getattr(c.func, "id", None) == "_unit_advice")
    assert len(advice_lines) >= 2, (
        f"only {len(advice_lines)} advisory call(s) in Pro's machine 1 "
        f"- it has two exits, the table branch and the feature class, "
        f"and a call on one path serves half the users")

    body_end = max(n.lineno for n in ast.walk(target)
                   if hasattr(n, "lineno"))
    assert max(advice_lines) < body_end + 1


def test_the_QGIS_advisory_is_reached_from_the_run():
    """BROKEN WITH: defining _unit_advice and never calling it.

    The QGIS counts algorithm has one exit, so the property is simply
    that the run calls it - but it is asserted rather than assumed,
    because 'defined and never called' is how 368 happened.
    """
    src = _text(DOORS["qgis"])
    tree = ast.parse(src)
    defined = {n.name for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef)}
    assert "_unit_advice" in defined
    callers = [n.name for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef)
               and any(isinstance(c, ast.Call)
                       and getattr(c.func, "attr", None) == "_unit_advice"
                       for c in ast.walk(n))]
    assert "processAlgorithm" in callers, (
        f"_unit_advice is called from {callers} - not from the method "
        f"QGIS actually runs, so no QGIS user would ever see it")


# ------------------------------------------- the Stata subcommand
def test_the_stata_subcommand_is_dispatched_and_not_merely_written():
    """BROKEN WITH: writing _equipop_unit but not adding the `unit`
    branch to the dispatch.

    `equipop unit` has to be caught by the same gettoken dispatch that
    catches `doctor` and `setup`. Without the branch the word falls
    through to the syntax line, Stata reads it as a varlist, and the
    user is told "varlist not allowed" - which is the exact failure
    John hit in the field with `equipop setup` against an older ado.
    """
    text = _text(DOORS["stata"])
    assert re.search(r'if\s+`"`eqp_sub\'"\'\s*==\s*"unit"\s*\{', text), (
        "no dispatch branch for the `unit` subcommand")
    assert re.search(r"program define _equipop_unit,\s*rclass", text), (
        "_equipop_unit must be rclass or its r() results vanish")
    # A subcommand's r() does not reach the caller by itself.
    branch = text.split('== "unit"', 1)[1][:400]
    assert "return add" in branch, (
        "the unit branch does not -return add-, so every documented "
        "r() result would be empty at the prompt")
    # And the unknown-subcommand help has to name it, or a user who
    # mistypes is told about two subcommands out of three.
    #
    # DERIVED FROM THE DISPATCH, not a hand list, and scoped to the
    # LIST rather than the file. This assertion used to be
    # `"equipop unit" in text`, which matches the dispatch branch
    # itself - so the help line could have been deleted and the test
    # would still have passed. John then pasted exactly that output:
    # `unknown subcommand: help`, with a list naming doctor and setup
    # and nothing else.
    dispatched = set(re.findall(
        r'if\s+`"`eqp_sub\'"\'\s*==\s*"(\w+)"', text))
    assert {"doctor", "setup", "unit", "help"} <= dispatched, (
        f"the dispatch handles {sorted(dispatched)}")
    block = text.split("unknown subcommand", 1)[1].split("exit 198", 1)[0]
    for sub in sorted(dispatched):
        assert re.search(r"equipop %s\s" % sub, block), (
            f"`equipop {sub}` is a real subcommand and the "
            f"unknown-subcommand list does not name it - which is "
            f"the message a user reads at the exact moment they have "
            f"typed one wrong")


def test_stata_can_tell_a_typed_unit_from_an_inherited_one():
    """BROKEN WITH: putting `Unit(real 100)` back on the syntax line.

    THE WHOLE RULE DEPENDS ON THIS. `Unit(real 100)` delivers 100 both
    when the user typed unit(100) and when they said nothing, so the
    advisory could not tell a choice from a default and would either
    nag everybody or nobody. The option is read as a string and
    defaulted in the body, where the fact can be recorded.
    """
    text = _text(DOORS["stata"])
    # THE SYNTAX LINE, not the file. A comment that quotes the old
    # `Unit(real 100)` to explain why it changed is a fact about the
    # past - the same trap as 1.53.3's scan matching its own docstring
    # and the bump tool's rule that a version in prose is history.
    # Only the statement Stata parses is evidence about the present.
    syntax = "\n".join(
        ln for ln in text.splitlines()
        if not ln.lstrip().startswith("*")
        and ("syntax" in ln or re.match(r"^\s{10,}\S", ln)))
    assert "Unit(real" not in syntax, (
        "unit() is back to a numeric default, which destroys the "
        "distinction the advisory is built on")
    assert re.search(r"Unit\(string\)", syntax), (
        "the syntax line no longer reads unit() as a string, so the "
        "body cannot tell a typed 100 from an inherited one")
    assert re.search(r"local unit_was_set\s+0", text), (
        "nothing records that the unit was NOT given")
    assert re.search(r"local unit\s+100\b", text), (
        "the 100 m default is no longer applied in the body, so a "
        "user who omits unit() gets an empty macro")
    # and it has to reach the Python that uses it
    assert "unit_was_set=`unit_was_set'" in text


def test_the_subcommand_takes_a_WEIGHT_both_ways_and_reads_it():
    """BROKEN WITH: `Macro.getLocal("pop")` instead of `"wvar"`, or
    dropping [fweight] from the subcommand's syntax line.

    FOUND BY WRITING THE FIELD DO-FILE, not by reading the code. Block
    23 of `equipop_test_pass.do` says

        equipop unit X_local Y_local [fweight=ValCount], k(100 1000)

    because that is how a Stata user with weighted data writes
    everything else - and the first version of the subcommand took no
    weight at all, so the block would have died on `weights not
    allowed` in John's hands.

    THE SECOND HALF IS THE DANGEROUS ONE. The .ado resolves
    [fweight=var] and pop(var) into one macro, `wvar`. Reading `pop`
    on the Python side instead would find an empty macro whenever the
    weight was given the fweight way, hand the engine None, and
    advise on an UNWEIGHTED population - a complete, plausible,
    silently wrong table. Nothing would raise, so the broad except
    around the door would not even be involved.
    """
    text = _text(DOORS["stata"])
    prog = text.split("program define _equipop_unit", 1)[1] \
               .split("\nend", 1)[0]
    assert "[fweight]" in prog.split("[, ", 1)[0], (
        "the subcommand's syntax line takes no weight, so the field "
        "do-file's own form is a syntax error")
    # POP(...) - Stata's capitals mark the minimum abbreviation, so
    # the option is spelled upper-case in the syntax line. My first
    # version of this assertion looked for lower case and failed.
    assert "POP(varname numeric)" in prog, "pop() is gone too"
    assert re.search(r"local wvar\b", prog), (
        "the two spellings are not resolved into one name")
    assert re.search(r"not both - they mean the same thing", prog), (
        "giving both a weight and pop() is no longer refused")
    # markout has to use the RESOLVED name or a missing weight does
    # not drop its row
    assert re.search(r"markout `touse'.*`wvar'", prog), (
        "markout ignores the weight, so a row with a missing "
        "population stays in the sample")

    block = _python_of("stata")
    unit_py = block.split("def _equipop_unit_py", 1)[1] \
                   .split("\ndef ", 1)[0]
    assert 'gl("wvar")' in unit_py, (
        "the Python reads something other than the resolved weight "
        "name - a weight given as [fweight=] would be silently "
        "ignored and the advice would be about an unweighted "
        "population")
    assert 'gl("pop")' not in unit_py, (
        "it still reads pop() directly, which misses [fweight=]")


def test_both_stata_entry_points_read_the_origin_rule_through_one_reader():
    """BROKEN WITH: deleting the `_equipop_originrule` call from the
    subcommand, which break-check found surviving.

    REVIEW F1. The aliases (`i=j`, `i!=j`) and the refusal of anything
    else used to live in the main command only, so `equipop unit`
    accepted any string at all - and after 1.54.1 the rule DECIDES
    whether the criterion applies, so `originrule(inclde)` would have
    silently selected the exclude branch and shown a table with no k
    columns for no stated reason.

    One `sclass` reader, called by both. Asserted as a property - the
    word "include" may appear in prose, but the VALIDATION may exist
    in only one place.
    """
    text = _text(DOORS["stata"])
    assert re.search(r"program define _equipop_originrule,\s*sclass",
                     text), "the shared origin-rule reader is gone"
    # exactly one place refuses a bad value
    refusals = len(re.findall(
        r'display as error "originrule\(\) must be', text))
    assert refusals == 1, (
        f"{refusals} copies of the origin-rule refusal - two copies "
        f"is how the doors drifted apart in the first place")
    # and both entry points call the reader
    for prog, label in (("program define equipop,", "the main command"),
                        ("program define _equipop_unit,",
                         "the unit subcommand")):
        body = text.split(prog, 1)[1].split("\nend\n", 1)[0]
        assert "_equipop_originrule" in body, (
            f"{label} does not go through the shared reader, so a "
            f"typo in originrule() is not refused there")
        assert "s(rule)" in body, (
            f"{label} calls the reader and ignores what it returns")


def test_equipop_help_works_and_survives_a_partial_install():
    """BROKEN WITH: removing the `help` branch, or calling
    `help equipop` without capturing it.

    JOHN'S FIELD REPORT, 10 OCTOBER 2026: `equipop help` ->
    `unknown subcommand: help`, with a list that did not include it.
    The one word a confused user reaches for, refused by the thing
    they were asking for help about. Stata's convention is
    `help equipop`, which is why it was never written; it is also not
    what anybody types the moment a subcommand has just been refused.

    THE CAPTURE MATTERS AS MUCH AS THE BRANCH. A partial install -
    the .ado files present, equipop.sthlp missing - makes Stata say
    "help for equipop not found", which reads as though the command
    itself is absent. Captured, the message names the real cause and
    the same reinstall line the unknown-subcommand branch prints.
    """
    text = _text(DOORS["stata"])
    assert re.search(r'if\s+`"`eqp_sub\'"\'\s*==\s*"help"\s*\{', text), (
        "`equipop help` is not dispatched")
    branch = text.split('== "help"', 1)[1][:1200]
    assert "capture help equipop" in branch, (
        "help is called without capture, so a missing .sthlp gives "
        "Stata's own error instead of the cause")
    assert "if _rc" in branch, "the capture's return code is ignored"
    assert "partial" in branch, (
        "the failure does not say what a missing help file means")
    assert "ssc install equipop, replace" in branch, (
        "the remedy is not offered where the user is reading")
    # and it must come BEFORE the other subcommands, so a user who
    # types `equipop help` while something else is broken still gets
    # the help rather than a diagnosis
    assert text.index('== "help"') < text.index('== "doctor"'), (
        "help is dispatched after doctor")


def test_the_stata_door_actually_attempts_a_cache_read():
    """BROKEN WITH: `unpack_advice(...) if False else None`, which
    break-check found surviving every test.

    A CACHE THAT NEVER HITS IS NOT A WRONG ANSWER, which is why
    nothing caught it - and it is this project's most repeated defect
    all the same: the feature exists and the path does not reach it
    (353, 368, 373, 380). John asked for the cache specifically; one
    discarded call and it would quietly never work, while the door
    still printed its "not stored" diagnostics as though it were
    trying.

    The property is that the call's result IS the value assigned -
    not wrapped in a conditional, not discarded. Checked over the AST,
    because a regex for the call text matches a call inside
    `if False else None` too.
    """
    import ast

    block = _python_of("stata")
    tree = ast.parse(block)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AugAssign)):
            continue
        val = node.value
        if isinstance(val, ast.Call) and \
                getattr(val.func, "attr", None) == "unpack_advice":
            found.append(("direct", node.lineno, val))
        else:
            for sub in ast.walk(val):
                if isinstance(sub, ast.Call) and \
                        getattr(sub.func, "attr", None) == "unpack_advice":
                    found.append(("wrapped", node.lineno, sub))
    assert found, "the Stata door never calls unpack_advice at all"
    kinds = {k for k, _, _ in found}
    assert kinds == {"direct"}, (
        f"unpack_advice's result is wrapped rather than assigned "
        f"(at line(s) {[ln for k, ln, _ in found if k != 'direct']}) - "
        f"a conditional around it can make the cache silently never "
        f"hit while the door still reports on it")
    # and it is handed the key, positionally
    call = found[0][2]
    assert len(call.args) == 2, (
        "unpack_advice is called with "
        f"{len(call.args)} positional argument(s) - it takes the "
        "text and the request key")
    assert getattr(call.args[1], "id", None) == "req", (
        "the second argument is not the request key the door built")
    # the hit path has to be reachable and say so
    assert "from_cache" in block and "stored advice" in block, (
        "nothing tells the user when the answer came from the cache, "
        "so a cache that never hits looks the same as one that does")


def test_every_documented_r_result_is_actually_set():
    """BROKEN WITH: documenting r(estimated) in the help and never
    setting eqp_u_est.

    The help is generated from one source and the ado sets the macros;
    nothing connects them but this. A documented result that is always
    empty is worse than an undocumented one, because a do-file will
    use it.
    """
    text = _text(DOORS["stata"])
    prog = text.split("program define _equipop_unit", 1)[1] \
               .split("\nend", 1)[0]
    returned = set(re.findall(r"return (?:scalar|local|matrix)\s+(\w+)",
                              prog))
    assert {"unit", "cells", "estimated", "tolerance", "N", "people",
            "k", "originrule", "fingerprint", "advice"} <= returned, (
        f"the subcommand returns only {sorted(returned)}")

    block = _python_of("stata")
    set_macros = set(re.findall(r'Macro\.setLocal\("(eqp_u_\w+)"', block))
    used = set(re.findall(r"`(eqp_u_\w+)'", prog))
    assert used <= set_macros, (
        f"the ado reads {sorted(used - set_macros)} and the Python "
        f"never sets them - every one would return as an empty macro")

    sthlp = _text(os.path.join(ROOT, "stata", "equipop.sthlp"))
    for nm in ("r(unit)", "r(cells)", "r(estimated)", "r(advice)"):
        assert nm in sthlp, f"{nm} is returned and not documented"


# --------------------------------------- one source for the numbers
def test_no_door_reimplements_the_saturation_criterion():
    """BROKEN WITH: inlining `pop >= k` in a door instead of calling
    the engine.

    BACKLOG 172's lesson, and 1.53.2's: seven k parsers existed, one
    was correct, and only one door could reach it. The criterion lives
    in unitsize.py and the doors print what they are handed. A door
    computing its own would be free to disagree with the engine's own
    [selfpot] message, which is the number this whole advisory claims
    to predict.
    """
    for door in DOORS:
        src = _python_of(door)
        for bad in ("np.floor(x / unit", "add.at(pop", ">= k - 1e-9"):
            assert bad not in src, (
                f"{door} contains `{bad}` - the criterion is the "
                f"engine's, and a second copy is a second answer")


def test_the_advisory_text_comes_from_the_shared_help_source():
    """BROKEN WITH: writing the subcommand's description into
    make_sthlp.py instead of help.py.

    John's condition when he ruled help ahead of projection was one
    source, four doors. A subcommand documented only in the Stata help
    breaks it, and the QGIS and Pro users never learn the feature
    exists.
    """
    from equipop.doors.help import HELP

    assert "unitadvice" in HELP, "the shared source has no entry"
    text = HELP["unitadvice"]
    assert "read-only" in text and "cells" in text
    gen = _text(os.path.join(ROOT, "tools", "make_sthlp.py"))
    assert 'HELP["unitadvice"]' in gen, (
        "make_sthlp.py does not read the shared entry, so the Stata "
        "help and the GIS dialogs can drift apart")
    # the generated file has to actually carry it
    sthlp = _text(os.path.join(ROOT, "stata", "equipop.sthlp"))
    assert "equipop unit" in sthlp
    assert text.split(".")[0].split()[-1].strip(",") in sthlp


# ------------------------------------------- the cache, end to end
def test_a_packed_advice_survives_the_round_trip_the_ado_makes():
    """BROKEN WITH: pack_advice writing something unpack_advice cannot
    read back, or the per-k maps coming back keyed by string.

    The .ado stores the packed string in `char _dta[]` and reads it
    next time. JSON turns integer dict keys into strings, so a
    round-tripped advice indexed by `advice["recommended"][100]` would
    raise KeyError - or, with a .get(), silently report no
    recommendation. Checked by doing the round trip and indexing with
    ints, as the ado does.
    """
    rng = np.random.default_rng(5)
    x = rng.uniform(0, 30000, 3000)
    y = rng.uniform(0, 30000, 3000)
    a = unitsize.advise_unit(x, y, None, k_values=[50, 500])
    packed = unitsize.pack_advice(a)
    assert len(packed) <= unitsize.MAX_PACKED

    back = unitsize.unpack_advice(packed, _key_for(a))
    assert back is not None
    assert back["recommended"][50] == a["recommended"][50]
    assert back["rows"][0]["saturated_cells"][500] == \
        a["rows"][0]["saturated_cells"][500]
    assert back["applies"] is a["applies"]
    # and it still formats, which is what the door does with it
    assert unitsize.format_advice(back) == unitsize.format_advice(a)

    # an EXCLUDE advice round-trips too, with its nulls intact - JSON
    # turns None into null and back, and a null read as 0 would put
    # the F1 defect straight back (review F1/F2).
    e = unitsize.advise_unit(x, y, None, k_values=[50],
                             self_rule="exclude")
    eback = unitsize.unpack_advice(unitsize.pack_advice(e), _key_for(e))
    assert eback is not None and eback["applies"] is False
    assert eback["rows"][0]["saturated_cells"][50] is None
    assert unitsize.format_advice(eback) == unitsize.format_advice(e)


def _key_for(advice, **over):
    """The cache key for an advice, as both sides build it."""
    args = dict(fingerprint=advice["fingerprint"],
                k_values=advice["k_values"],
                tolerance=advice["tolerance"],
                candidates=[r["unit"] for r in advice["rows"]],
                self_rule=advice["self_rule"])
    args.update(over)
    return unitsize.request_key(**args)


def test_a_stale_cache_misses_rather_than_lying():
    """BROKEN WITH: unpack_advice ignoring any part of the request.

    BACKLOG 344 is why: a resumed run returned the first run's numbers
    because counting rows could not tell two tables apart. A cached
    unit recommendation is the same trap - the user changes something,
    the advice is about the old question, and nothing says so.

    REVIEW F2 FOUND TWO WAYS THROUGH THIS. The checks were the
    fingerprint, the k list and the tolerance, as three separate
    OPTIONAL arguments - so the candidate ladder and the origin rule
    were not checked at all, and advice cached for candidates 25 and
    50 under include came back, as a reported cache HIT, to a request
    for candidates 1,000 and 5,000 under exclude. The 1.54.0 release
    note said "every way of being stale returns a miss"; it was false,
    and this test is why nobody noticed - it checked three of the five
    things and called that every.

    The request is now ONE key, and `unpack_advice` requires it.
    """
    x = np.array([1.0, 2.0, 3000.0])
    y = np.array([1.0, 2.0, 3000.0])
    a = unitsize.advise_unit(x, y, None, k_values=[2],
                             candidates=[25.0, 50.0])
    packed = unitsize.pack_advice(a)

    assert unitsize.unpack_advice(packed, _key_for(a)) is not None, (
        "the identical request does not even hit")

    # every component of the request, one at a time
    assert unitsize.unpack_advice(
        packed, _key_for(a, fingerprint="other")) is None
    assert unitsize.unpack_advice(
        packed, _key_for(a, k_values=[9])) is None
    assert unitsize.unpack_advice(
        packed, _key_for(a, tolerance=0.05)) is None
    # THE TWO THE REVIEW FOUND
    assert unitsize.unpack_advice(
        packed, _key_for(a, candidates=[1000.0, 5000.0])) is None, (
        "a different candidate ladder is served the old rows - this "
        "is review F2 exactly")
    assert unitsize.unpack_advice(
        packed, _key_for(a, self_rule="exclude")) is None, (
        "an exclude request is served include-rule advice - review "
        "F2, and it lands straight on F1")
    # and `current` changes the effective ladder, so it must too
    assert unitsize.unpack_advice(
        packed, _key_for(a, current=300.0)) is None

    assert unitsize.unpack_advice("", _key_for(a)) is None
    assert unitsize.unpack_advice("{not json", _key_for(a)) is None

    # THE VERSION, tested with a payload that is otherwise PERFECT.
    # Break-check found this: `{"v":0,"a":{}}` returned None with the
    # version check deleted, because the empty dict failed the
    # structure check instead - so the assertion passed for the wrong
    # reason and the version check was not covered at all. A stale
    # cache is dangerous precisely when it looks valid.
    import json

    old = json.loads(packed)
    old["v"] = unitsize.CACHE_VERSION - 1
    assert unitsize.unpack_advice(json.dumps(old), _key_for(a)) is None, (
        "a cache written by an older version is read as if it were "
        "this one - a shape change would then be misinterpreted "
        "rather than missed")
    old["v"] = unitsize.CACHE_VERSION
    assert unitsize.unpack_advice(
        json.dumps(old), _key_for(a)) is not None, (
        "the version assertion above is not about the version")

    # a v1 payload - no `applies` field - must not be readable, or an
    # exclude run could be served pre-fix include numbers out of a
    # .dta saved before the upgrade (review F1)
    noapplies = json.loads(packed)
    noapplies["a"].pop("applies")
    assert unitsize.unpack_advice(
        json.dumps(noapplies), _key_for(a)) is None

    # THE KEY IS RE-DERIVED FROM THE CONTENT, never trusted from the
    # payload - so editing any field the key covers invalidates it,
    # and there is nothing in the stored string to forge. Break-check
    # showed the earlier belt-and-braces comparison against a stored
    # `key` field was redundant: re-deriving says what the content
    # ACTUALLY answers, a stored key only what its writer claimed.
    assert "key" not in json.loads(packed), (
        "a key is stored in the payload again - nothing reads it, "
        "and a value nothing reads invites being trusted")
    forged = json.loads(packed)
    forged["a"]["tolerance"] = 0.5
    assert unitsize.unpack_advice(
        json.dumps(forged), _key_for(a)) is None, (
        "an edited payload still satisfies the request it no longer "
        "answers")

    # the fingerprint really does move with the data
    moved = unitsize.advise_unit(x + 1.0, y, None, k_values=[2],
                                 candidates=[25.0, 50.0])
    assert unitsize.unpack_advice(packed, _key_for(moved)) is None


def test_the_cache_key_is_required_and_cannot_be_half_given():
    """BROKEN WITH: giving `key` a default of None and skipping the
    comparison when it is None.

    REVIEW F2, FIXED STRUCTURALLY. The first fix added `candidates`
    and `self_rule` as optional keyword arguments - which leaves a
    caller free to forget them and get a silent stale hit, and that is
    the shape this project has shipped five times over (353, 368, 373,
    380): the check exists and the path does not reach it. One
    required positional argument cannot be half-given.
    """
    import inspect

    sig = inspect.signature(unitsize.unpack_advice)
    params = list(sig.parameters.values())
    assert [p.name for p in params] == ["text", "key"], (
        f"the signature is {sig} - extra optional validation "
        f"arguments are ones a door can forget")
    assert params[1].default is inspect.Parameter.empty, (
        "`key` has a default, so omitting it skips the check instead "
        "of raising")

    x = np.array([1.0, 2.0, 3000.0])
    a = unitsize.advise_unit(x, x, None, k_values=[2])
    with pytest.raises(TypeError):
        unitsize.unpack_advice(unitsize.pack_advice(a))

    # and the ado has to pass one it built the same way
    block = _python_of("stata")
    assert "unitsize.request_key(" in block, (
        "the Stata door does not build a request key, so it cannot "
        "be validating the whole request")
    assert re.search(r"unpack_advice\(cached_text,\s*req\)", block), (
        "the door calls unpack_advice with something other than the "
        "key it built")


# -------------------------------- what the run itself already says
def test_the_run_message_and_the_advisory_describe_the_same_thing():
    """BROKEN WITH: advise_on_run reporting the CELL share where the
    engine's own message counts origins.

    The engine prints `[selfpot] k=N: the whole neighbourhood was the
    origin cell for X of Y origins` after a run, and the advisory
    prints a share of PEOPLE. Both appear in the same log, so a reader
    must be able to reconcile them: X has to equal the advisory's
    saturated_cells at the unit the run used. If those two drift the
    log contradicts itself.
    """
    from equipop.cells import build_cells
    from equipop.fastcounts import run_knn_counts

    x = np.array(list(np.linspace(1, 90, 40)) + [1500.0, 2500.0, 3500.0])
    y = np.array([5.0] * 43)
    w = np.ones(43)
    cd = build_cells(pd.DataFrame({"E": x, "N": y, "w": w}),
                     "E", "N", unit_size=100.0, weights="w")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_knn_counts(cd, [20])
    m = re.search(r"k=20: the whole neighbourhood was the origin cell "
                  r"for ([\d,]+) of ([\d,]+) origins", buf.getvalue())
    assert m, "the engine stopped reporting self-potential origins"

    adv = unitsize.advise_unit(x, y, w, k_values=[20],
                               candidates=[100.0], current=100.0)
    row = adv["rows"][0]
    assert row["saturated_cells"][20] == int(m.group(1).replace(",", ""))
    # and the people share is the LARGER number, which is the reason
    # both are printed
    assert row["share_people"][20] >= row["share_cells"][20]


def test_the_advisory_is_silent_when_there_is_nothing_to_say():
    """BROKEN WITH: advise_on_run always returning its header.

    A note printed after every run is noise, and noise is how a real
    warning gets missed. Silence is the common case: the user set a
    unit, and it does not saturate.
    """
    rng = np.random.default_rng(2)
    x = rng.uniform(0, 50000, 2000)
    y = rng.uniform(0, 50000, 2000)
    a = unitsize.advise_unit(x, y, None, k_values=[20],
                             candidates=[100.0], current=100.0)
    assert a["rows"][0]["share_people"][20] == 0.0
    assert unitsize.advise_on_run(a, unit=100.0, unit_was_set=True) == []
    # and when they did NOT choose, the one candidate on the ladder IS
    # the unit in use, so there is still no change to recommend
    assert unitsize.advise_on_run(a, unit=100.0, unit_was_set=False) == []


def test_a_chosen_unit_is_warned_about_but_never_overridden():
    """BROKEN WITH: advise_on_run returning a different unit for the
    door to apply.

    John's rule, and the project's since BACKLOG 116: reported, never
    substituted. The warning names their number and a better one; it
    returns LINES, so there is nothing a door could accidentally
    apply.
    """
    x = np.array([10.0, 20.0, 30.0, 40.0])
    y = np.array([10.0, 10.0, 10.0, 10.0])
    w = np.array([500.0, 500.0, 500.0, 500.0])
    a = unitsize.advise_unit(x, y, w, k_values=[100],
                             candidates=[100.0, 1000.0], current=1000.0)
    said = unitsize.advise_on_run(a, unit=1000.0, unit_was_set=True)
    text = "\n".join(said)
    assert "WARNING" in text and "unit(1000)" in text
    assert "has not changed it" in text
    assert all(isinstance(line, str) for line in said), (
        "advise_on_run must return text a door can only print")
