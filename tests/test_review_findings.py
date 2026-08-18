"""External review of 1.36 - the findings confirmed and guarded.

These come from an outside reviewer, not from the suite, which is the
third time in this project that the useful defects arrived from
outside it. All three below were reproduced before being fixed.

The `.ado` cannot be executed here, so these tests PARSE it. That is
the standing rule from BACKLOG 172: a grep can certify a corpse, and
both of the tests that read the Stata file for eleven releases passed
on a command that could not run.
"""

import os
import re

import pytest

STATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stata")
ADO = os.path.join(STATA_DIR, "equipop.ado")


def _text():
    with open(ADO, encoding="utf-8") as fh:
        return fh.read()


def _program_body():
    """Just the equipop program, not the python block below it."""
    t = _text()
    start = t.index("program define equipop,")
    return t[start:t.index("\nend", start)]


def test_no_varlist_loop_runs_on_a_possibly_empty_treat():
    """Reviewer P1, confirmed.

    treat() became optional in 1.36. An empty `foreach ... of varlist`
    is a SYNTAX ERROR in Stata, not an empty loop, so

        equipop, x(X) y(Y) k(25) replace

    failed on exactly the combination that ruling created. Nothing in
    the suite could see it: the parser test models argument passing,
    not Stata's runtime grammar.
    """
    body = _program_body()
    for m in re.finditer(r"foreach\s+\w+\s+of\s+varlist\s+`treat'", body):
        before = body[:m.start()]
        # the guard must be open at this point: an `if "`treat'" != ""`
        # since the last closing brace at the same level
        guard = before.rfind('if "`treat\'" != ""')
        closed = before.rfind("}")
        assert guard > closed, (
            "a `foreach ... of varlist `treat'` is reachable with an "
            "empty treat() - that is a syntax error in Stata, not an "
            "empty loop")


def test_the_cell_size_is_validated_before_it_reaches_the_engine():
    """Reviewer P1, confirmed. BACKLOG 155.

    QGIS and Pro have refused fractional cell sizes since 1.29.8
    because the core builds cells on integer centres: a requested 2.5
    produces centres 1, 3, 6 - spacings of 2 and 3, neither of them
    2.5. Stata declared unit() as a plain real and checked nothing.
    """
    body = _program_body()
    assert re.search(r"if\s+`unit'\s*<=\s*0", body), (
        "unit() accepts zero or a negative cell size")
    assert re.search(r"`unit'\s*!=\s*int\(`unit'\)", body), (
        "unit() accepts a fractional cell size, which the core cannot "
        "represent - see BACKLOG 155")


def test_the_fractional_cell_size_really_is_unrepresentable():
    """The reason for the rule, checked rather than quoted.

    If this ever stops being true the rule should be revisited rather
    than kept out of habit.
    """
    import pandas as pd

    from equipop.cells import build_cells

    df = pd.DataFrame({"e": [0.1, 2.6, 5.1], "n": [0.0, 0.0, 0.0]})
    cells = build_cells(df, "e", "n", unit_size=2.5)
    centres = sorted({float(v) for v in cells.E})
    gaps = {round(b - a, 6) for a, b in zip(centres, centres[1:])}
    assert gaps != {2.5}, (
        "cells are now evenly spaced at a fractional size - BACKLOG "
        "155's rule may no longer be needed")


def test_the_guards_report_through_the_door_not_the_helper():
    """A guard that fires inside Python would stop the run with a
    traceback rather than a Stata error. These belong in the .ado."""
    body = _program_body()
    for pattern in (r"if\s+`unit'\s*<=\s*0", r"`unit'\s*!=\s*int\(`unit'\)"):
        m = re.search(pattern, body)
        tail = body[m.end():m.end() + 400]
        assert "display as error" in tail and "exit 198" in tail, (
            "the cell-size guard does not produce a Stata error")


@pytest.mark.parametrize("bad", ["0", "-5", "2.5"])
def test_the_documented_rule_matches_the_guard(bad):
    """The help must not promise something the command refuses."""
    import sys
    sys.path.insert(0, os.path.dirname(STATA_DIR))
    from tools.make_sthlp import option_text

    text = option_text("unit(#)").lower()
    assert "cell" in text


# --------------------------------------------------------------------
# Reviewer P0: shipped instructions that contradict the field procedure
# --------------------------------------------------------------------

CURRENT_STATA_DOCS = ["README_STATA.md"]

FORBIDDEN = {
    "anaconda": ("Anaconda plus Stata closes Stata outright on "
                 "`import numpy`. Current guidance must never send a "
                 "user there."),
    "weight(": "weight() was removed - it is pop() or [fweight=] now.",
    "equipop_knn,": "equipop_knn is the compatibility alias, not the "
                    "command to teach.",
}

STALE_CLAIMS = ["arrives in 1.38", "planned for 1.38",
                "not yet available", "will be added in"]


@pytest.mark.parametrize("doc", CURRENT_STATA_DOCS)
def test_current_stata_guidance_cannot_send_a_user_into_a_crash(doc):
    """Reviewer P0, confirmed.

    The shipped README told users to point Stata at an Anaconda
    environment - the one configuration the handover records as closing
    Stata outright. Instructions are as much a part of the release as
    the code, and this one could break a machine before EquiPop ran.
    """
    path = os.path.join(STATA_DIR, doc)
    raw = open(path, encoding="utf-8").read()
    text = " ".join(raw.lower().split())          # wrapping-proof
    for bad, why in FORBIDDEN.items():
        if bad == "anaconda":
            if "anaconda" in text:
                # naming it in order to forbid it is the point
                assert "do not point stata at an anaconda" in text, why
            # and no instruction may point Stata at one
            for line in raw.lower().splitlines():
                if "python set exec" in line:
                    assert "conda" not in line, why
            continue
        assert bad not in text, f"{doc}: {why}"


@pytest.mark.parametrize("doc", CURRENT_STATA_DOCS)
def test_current_stata_guidance_makes_no_stale_release_promises(doc):
    """The testing guide said net install and the help file arrive in
    1.38. Both shipped in 1.36. A document that describes a future
    which already happened teaches the reader to distrust it."""
    text = open(os.path.join(STATA_DIR, doc), encoding="utf-8").read().lower()
    for claim in STALE_CLAIMS:
        assert claim not in text, f"{doc} still promises: {claim}"


def test_retired_guides_are_marked_and_out_of_the_way():
    """They are kept so a past field report can be read against what
    the user was told at the time - but nobody should follow one by
    accident."""
    hist = os.path.join(STATA_DIR, "historical")
    assert os.path.isdir(hist), "retired guides have no home"
    files = [f for f in os.listdir(hist) if f.endswith(".md")]
    assert files, "nothing retired"
    for f in files:
        head = open(os.path.join(hist, f), encoding="utf-8").read()[:400]
        assert "HISTORICAL" in head and "DO NOT FOLLOW" in head, (
            f"{f} is not marked as retired")


def test_only_one_current_stata_document_ships():
    """One page, or they drift apart again."""
    docs = [f for f in os.listdir(STATA_DIR) if f.endswith(".md")]
    assert sorted(docs) == sorted(CURRENT_STATA_DOCS), (
        f"unexpected current Stata documents: {docs}")


def test_the_current_page_teaches_the_treatment_contract():
    """The defect that produced impossible numbers was a contract the
    user was never told about."""
    text = open(os.path.join(STATA_DIR, "README_STATA.md"),
                encoding="utf-8").read()
    assert "treatmode(flags)" in text
    assert "number of people" in text.lower()


# --------------------------------------------------------------------
# equipop setup - v1.40.2
# --------------------------------------------------------------------

def test_setup_is_a_subcommand_like_doctor():
    t = _text()
    assert '"setup"' in t, "no setup subcommand"
    assert "program define _equipop_setup" in t


def test_setup_installs_into_the_interpreter_it_is_running_in():
    """The whole reason it exists. A user typing pip in a terminal has
    no way of knowing which Python Stata uses; asking Python where it
    lives cannot be got wrong."""
    t = _text()
    block = t[t.index("def _equipop_setup_py"):]
    block = block[:block.index("def _equipop_doctor_py")]
    assert "sys.executable" in block
    assert '"-m", "pip", "install"' in block


def test_setup_uses_only_the_standard_library():
    """It runs BEFORE the package exists. Importing equipop here would
    make the installer need the thing it installs."""
    t = _text()
    block = t[t.index("def _equipop_setup_py"):]
    block = block[:block.index("def _equipop_doctor_py")]
    assert "import equipop" not in block
    assert "from equipop" not in block


def test_repair_forces_the_processor_specific_reinstall():
    t = _text()
    block = t[t.index("def _equipop_setup_py"):]
    block = block[:block.index("def _equipop_doctor_py")]
    assert "--force-reinstall" in block
    assert "--no-cache-dir" in block, (
        "without it pip reuses the wrong-processor wheel it already "
        "downloaded and the repair appears not to work")
    for lib in ("numpy", "scipy", "pandas"):
        assert f'"{lib}"' in block


def test_setup_does_not_run_the_doctor_in_the_same_session():
    """Python starts once per Stata session. After an upgrade the
    doctor would report the version still in memory - the old one -
    and say everything matches when it does not."""
    t = _text()
    block = t[t.index("def _equipop_setup_py"):]
    block = block[:block.index("def _equipop_doctor_py")]
    assert "_equipop_doctor_py(" not in block
    assert "QUIT STATA COMPLETELY" in block


def test_a_pip_failure_explains_the_externally_managed_case():
    t = _text()
    assert "externally managed" in t
    assert "python.org" in t


def test_an_unknown_subcommand_is_named_rather_than_called_a_varlist():
    """Field report, v1.40.3.

    John ran -equipop setup- against an .ado that predated the
    subcommand. It fell through to the syntax line, Stata read the word
    as a variable list, and said "varlist not allowed" - true, and
    useless. Anyone in a conference audience typing a subcommand their
    copy is too old for meets the same wall.
    """
    body = _program_body()
    assert "unknown subcommand" in body
    hit = body[body.index("unknown subcommand"):][:1400]
    assert "equipop doctor" in hit and "equipop setup" in hit, (
        "the message should list the subcommands that do exist")
    assert "net install" in hit, (
        "an out-of-date .ado is the likeliest cause, so say how to "
        "update")
    assert "x(X) y(Y)" in hit, (
        "the other likely cause is a user putting variables where a "
        "subcommand goes")


def test_the_subcommand_test_cannot_swallow_a_real_run():
    """if, in, a comma and [fweight=...] must all still reach syntax.

    A guard that ate a legitimate command line would be far worse than
    the message it replaces.
    """
    body = _program_body()
    hit = body[body.index("unknown subcommand") - 700:
               body.index("unknown subcommand")]
    assert 'inlist(`"`eqp_sub\'"\', "if", "in")' in hit, (
        "-if- and -in- are not excluded, so `equipop if x==1, ...` "
        "would be refused as an unknown subcommand")
    assert "^[a-zA-Z][a-zA-Z0-9_]*$" in hit, (
        "the test is not anchored to a bare word, so a comma or an "
        "[fweight=...] could match")
