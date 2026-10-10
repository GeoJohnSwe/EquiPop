# -*- coding: utf-8 -*-
"""test_stata_ado.py - the Stata door, read as a file.

BACKLOG 172. Why this file exists.

`stata/equipop_knn.ado` could not run at all between v1.29.5 and
v1.34 - eleven releases. v1.29.5 added `SELFpot(real 1)` to the
syntax line and added `selfpot` to the call site, and left the Python
def with seven parameters. An eight-argument call raises TypeError
before EquiPop is reached, so EVERY invocation of the command failed,
and the body also read a name (`selfpot`) that nothing defined.

435 tests were green throughout. None of them opened an .ado. Stata
sat outside `door_parity.py` and outside the suite, so the only
detector was John running it, and he had not - which is exactly the
kind of gap that survives longest.

Stata's `python:` block cannot be EXECUTED here: it imports `sfi`,
which exists only inside Stata. But it can be READ, and everything
that broke was readable:

  1. the block parses at all;
  2. every `python: f(...)` call in the ado matches the `def f(...)`
     in the same file - by arity AND by keyword name;
  3. no name is loaded in the glue that nothing defines;
  4. every option declared on the `syntax` line is used somewhere in
     the program - a box declared and never read is BACKLOG 148's
     failure, in Stata;
  5. the keywords the glue hands to equipop.stata_bridge still exist
     in the package's own signatures.

A stub is safe only where it is stricter than the real thing
(HANDOVER 8). This file is not a stub - it never pretends to run
Stata. It only refuses to let the two halves of a file disagree.
"""
import ast
import builtins
import inspect
import os
import re
import sys

import pytest

STATA_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "stata")

ADOS = sorted(f for f in os.listdir(STATA_DIR) if f.endswith(".ado"))

# Names the glue may read without defining: supplied by Stata's own
# python environment, or by the imports at the top of the block.
SFI_NAMES = {"Data", "SFIToolkit", "Macro", "Scalar", "Matrix"}


def _read(name):
    with open(os.path.join(STATA_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def _join_continuations(text):
    """Stata's /// joins the next line onto this one."""
    return re.sub(r"///[^\n]*\n\s*", " ", text)


def _python_block(text):
    """The text between a line `python:` and its closing `end`."""
    m = re.search(r"^python:\s*$(.*?)^end\s*$", text,
                  re.M | re.S)
    return m.group(1) if m else None


def _defs(tree):
    return {n.name: n for n in tree.body
            if isinstance(n, ast.FunctionDef)}


def _module_names(tree):
    """Top-level names the block itself provides."""
    out = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                out.add(a.asname or a.name.split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out.add(t.id)
    return out


def _bound_in(fn):
    """Every name a function body defines for itself."""
    a = fn.args
    out = {p.arg for p in
           a.posonlyargs + a.args + a.kwonlyargs}
    if a.vararg:
        out.add(a.vararg.arg)
    if a.kwarg:
        out.add(a.kwarg.arg)
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            out.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            out.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for al in node.names:
                out.add(al.asname or al.name.split(".")[0])
        elif isinstance(node, ast.arg):
            out.add(node.arg)
    return out


def _loaded_in(fn):
    return {n.id for n in ast.walk(fn)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def _call_sites(text):
    """Every `python: f(...)` line, as a parsed Python Call.

    Stata macros are replaced by the literal 1 first, which keeps the
    expression valid Python in both string and numeric position and
    changes neither the argument COUNT nor the keyword NAMES - the
    only two things this file asks about.
    """
    joined = _join_continuations(text)
    out = []
    for m in re.finditer(r"^[^\S\n]*python:[^\S\n]*(\S.*)$", joined,
                         re.M):
        expr = re.sub(r"`[^'\n]*'", "1", m.group(1)).strip()
        try:
            node = ast.parse(expr, mode="eval").body
        except SyntaxError as exc:                     # pragma: no cover
            pytest.fail(f"unparseable python: line {expr!r}: {exc}")
        if isinstance(node, ast.Call):
            out.append((expr, node))
    return out


def _signature_of(fn):
    """An inspect.Signature for an ast.FunctionDef."""
    a = fn.args
    P = inspect.Parameter
    params = []
    n_def = len(a.defaults)
    pos = a.posonlyargs + a.args
    first_default = len(pos) - n_def
    for i, p in enumerate(a.posonlyargs):
        params.append(P(p.arg, P.POSITIONAL_ONLY,
                        default=(P.empty if i < first_default else 0)))
    for j, p in enumerate(a.args):
        i = len(a.posonlyargs) + j
        params.append(P(p.arg, P.POSITIONAL_OR_KEYWORD,
                        default=(P.empty if i < first_default else 0)))
    if a.vararg:
        params.append(P(a.vararg.arg, P.VAR_POSITIONAL))
    for p, d in zip(a.kwonlyargs, a.kw_defaults):
        params.append(P(p.arg, P.KEYWORD_ONLY,
                        default=(P.empty if d is None else 0)))
    if a.kwarg:
        params.append(P(a.kwarg.arg, P.VAR_KEYWORD))
    return inspect.Signature(params)


@pytest.mark.parametrize("ado", ADOS)
def test_python_block_parses(ado):
    """A .ado whose python: block does not compile is dead on arrival."""
    text = _read(ado)
    block = _python_block(text)
    if block is None:
        pytest.skip(f"{ado} has no python: block")
    ast.parse(block)


@pytest.mark.parametrize("ado", ADOS)
def test_call_sites_match_their_definitions(ado):
    """THE 1.29.5 BUG. Eight arguments into a seven-parameter def."""
    text = _read(ado)
    block = _python_block(text)
    if block is None:
        pytest.skip(f"{ado} has no python: block")
    tree = ast.parse(block)
    defs = _defs(tree)

    for expr, call in _call_sites(text):
        name = getattr(call.func, "id", None)
        if name is None:
            continue
        assert name in defs, (
            f"{ado}: `python: {name}(...)` but no def {name} in the "
            f"file's python: block")
        sig = _signature_of(defs[name])
        args = [0] * len(call.args)
        kwargs = {kw.arg: 0 for kw in call.keywords if kw.arg}
        try:
            sig.bind(*args, **kwargs)
        except TypeError as exc:
            pytest.fail(
                f"{ado}: the ado calls {name}{sig} with "
                f"{len(args)} positional and keywords {sorted(kwargs)} "
                f"- Stata would stop with: TypeError: {exc}")


@pytest.mark.parametrize("ado", ADOS)
def test_glue_reads_no_undefined_name(ado):
    """THE SECOND HALF OF THE 1.29.5 BUG.

    `selfpot` was read inside the function and was not a parameter of
    it. Even with the arity fixed, that is a NameError at run time.
    """
    text = _read(ado)
    block = _python_block(text)
    if block is None:
        pytest.skip(f"{ado} has no python: block")
    tree = ast.parse(block)
    known = (_module_names(tree) | SFI_NAMES | set(dir(builtins)))

    for fn in _defs(tree).values():
        free = _loaded_in(fn) - _bound_in(fn) - known
        assert not free, (
            f"{ado}: {fn.name}() reads {sorted(free)}, which nothing "
            f"in the file defines - NameError inside Stata")


# Stata's own declarations, which are not options and are not read
# as macros of their own name. A weight sets `weight` and `exp`;
# [if] and [in] are consumed by marksample, which builds `touse`.
SYNTAX_TYPES = {"varname", "varlist", "numlist", "real", "integer",
                "string", "numeric", "or", "min", "max", "str"}
WEIGHT_TYPES = {"fweight", "aweight", "pweight", "iweight", "weight"}
SAMPLE_TYPES = {"if", "in"}


@pytest.mark.parametrize("ado", ADOS)
def test_every_syntax_option_is_used(ado):
    """A box declared and never read.

    BACKLOG 148 shipped a `population` parameter no call site passed.
    The Stata shape of that failure is an option on the syntax line
    whose macro is never referenced in the program.

    v1.36: Stata's own declarations are checked differently, because
    they do not set a macro of their own name. Declaring a weight and
    never reading `exp` is the same defect wearing different clothes -
    the user types [fweight=pop] and it silently does nothing.
    """
    text = _read(ado)
    m = re.search(r"^\s*syntax\s(.*?)$",
                  _join_continuations(text), re.M)
    if not m:
        pytest.skip(f"{ado} declares no syntax line")
    decl = m.group(1)
    body = text.split("\nend", 1)[0]

    # Stata's grammar: everything BEFORE the first comma declares the
    # varlist, [if], [in] and any weight; everything AFTER it is
    # options. `Weight(varname)` after the comma is an ordinary
    # option that happens to be named weight - not a weight clause.
    pre, _, post = decl.partition(",")
    declared = {t.lower() for t in
                re.findall(r"(?<![\w(])([A-Za-z_]{2,})(?![\w(])", pre)}

    opts = {tok.lower() for tok in re.findall(r"([A-Za-z_]+)\s*\(", post)}
    for tok in re.findall(r"(?<![\w(])([A-Za-z_]{2,})(?![\w(])", post):
        opts.add(tok.lower())
    opts -= SYNTAX_TYPES

    if declared & WEIGHT_TYPES:
        assert re.search(r"`exp'", body), (
            f"{ado}: a weight is declared and `exp' is never read - "
            f"[fweight=var] would be accepted and ignored")

    if declared & SAMPLE_TYPES:
        assert "marksample" in body, (
            f"{ado}: [if]/[in] are declared but marksample is never "
            f"called - they would be accepted and ignored")

    for opt in sorted(opts):
        assert re.search(r"`" + re.escape(opt) + r"'", body), (
            f"{ado}: option {opt}() is declared on the syntax line "
            f"and never read - it does nothing")


def test_glue_keywords_exist_in_the_package():
    """Parity between the ado and the package it calls.

    door_parity.py holds Pro and QGIS to one vocabulary; Stata has
    never been in it. This is the narrow version: whatever the glue
    hands to equipop.stata_bridge must still be a parameter there.
    Renaming a bridge parameter now breaks a test instead of a user.
    """
    from equipop import stata_bridge

    for ado in ADOS:
        block = _python_block(_read(ado))
        if block is None:
            continue
        tree = ast.parse(block)
        for call in [n for n in ast.walk(tree)
                     if isinstance(n, ast.Call)]:
            fname = getattr(call.func, "id", None)
            target = getattr(stata_bridge, fname, None) if fname else None
            if target is None or not inspect.isfunction(target):
                continue
            sig = inspect.signature(target)
            takes_kwargs = any(
                p.kind is inspect.Parameter.VAR_KEYWORD
                for p in sig.parameters.values())
            if takes_kwargs:
                continue
            for kw in call.keywords:
                if kw.arg is None:
                    continue
                assert kw.arg in sig.parameters, (
                    f"{ado}: passes {kw.arg}= to "
                    f"stata_bridge.{fname}(), which has no such "
                    f"parameter")


# ---------------------------------------------------------------
# BACKLOG 173. What crosses back INTO Stata.
# ---------------------------------------------------------------
# John's first real Stata run: the engine finished, all sixteen
# columns were computed, and the command then died handing them over,
# with "TypeError: the specified value should be a numeric value".
# The glue passed Python's None for a missing result. It needed a
# missing RESULT to appear at all - his data had 9 rows without
# coordinates - so eleven releases of complete-coordinate testing
# never reached it.
#
# The conversion now lives in the package, so these run for real
# rather than reading the .ado as text.

def test_missing_becomes_stata_missing_not_none():
    import numpy as np
    from equipop.stata_bridge import to_stata_values, STATA_MISSING

    out = to_stata_values(np.array([1.5, np.nan, 3.0, np.inf, -np.inf]))
    assert None not in out, "None is what Stata refused"
    assert all(type(v) is float for v in out), (
        "numpy scalars are not plain floats; sfi type-checks the value")
    assert out[1] == STATA_MISSING and out[3] == STATA_MISSING
    assert out[0] == 1.5 and out[2] == 3.0


def test_the_missing_sentinel_survives_the_round_trip():
    """Out and back in must agree.

    Every reader in stata_bridge treats `> 8.9e307` as missing on the
    way in. What we write out must be caught by that same rule, or a
    result would return from Stata as an enormous number rather than
    as a full stop.
    """
    import numpy as np
    from equipop.stata_bridge import to_stata_values

    back = np.asarray(to_stata_values(np.array([2.0, np.nan])))
    assert not back[0] > 8.9e307
    assert back[1] > 8.9e307
    assert np.isnan(np.where(back > 8.9e307, np.nan, back)[1])


@pytest.mark.parametrize("ado", ADOS)
def test_no_ado_hands_none_to_stata(ado):
    """The written form of the same fault, in case it is re-typed.

    Data.store(variable, observation, VALUES). A None in the SECOND
    position is correct and means every observation; a None anywhere
    in the THIRD is the fault that killed the first field run.

    DISPATCHED ON THE OBJECT, not on the method name alone. sfi has
    more than one `store`: Matrix.store(name, VALUES) takes two
    arguments, and matching every `.store` by name meant a legitimate
    Matrix.store (BACKLOG 385's r(advice)) tripped a rule about
    Data.store. Narrowing by name alone would have let an unknown
    third `store` through silently, so every `.store` is still
    examined and each known object gets its own shape - with the
    position of the VALUES argument recorded per object.
    """
    text = _read(ado)
    block = _python_block(text)
    if block is None:
        pytest.skip(f"{ado} has no python: block")
    # object name -> (minimum args, index of the VALUES argument)
    shapes = {"Data": (3, 2), "Matrix": (2, 1)}
    tree = ast.parse(block)
    seen = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if getattr(node.func, "attr", None) != "store":
            continue
        obj = getattr(node.func.value, "id", None)
        assert obj in shapes, (
            f"{ado}: {obj}.store() is a `store` this test does not "
            f"know the shape of - say how many arguments it takes and "
            f"which one holds the VALUES, or a None among them goes "
            f"unnoticed")
        need, vi = shapes[obj]
        seen.add(obj)
        assert len(node.args) >= need, f"{ado}: odd {obj}.store call"
        values = node.args[vi]
        for sub in ast.walk(values):
            assert not (isinstance(sub, ast.Constant) and sub.value is None), (
                f"{ado}: {obj}.store is handed None among its VALUES - "
                f"Stata refuses it with 'the specified value should be "
                f"a numeric value'. Use to_stata_values().")
    assert "Data" in seen, (
        f"{ado}: no Data.store call found at all - either the glue "
        f"stopped writing variables, or it writes them under another "
        f"name and this test has stopped guarding anything")


# ---------------------------------------------------------------
# BACKLOG 174 and 175. The command as a STATA command, and its help.
# ---------------------------------------------------------------

def _ado_text():
    return _read("equipop.ado")


def test_if_and_in_reach_the_engine():
    """John's ruling: [if]/[in] restrict the rows that RECEIVE
    results, never who counts as a neighbour. So `touse` must be
    declared, built by marksample, AND handed to the glue - a
    marksample whose answer is never used is the same as no if at
    all, and would silently compute for everyone."""
    text = _ado_text()
    assert "marksample touse" in text
    assert 'touse="`touse\'"' in text, (
        "touse is built and never passed - [if] would be ignored")


def test_a_weight_reaches_the_engine_under_either_name():
    """[fweight=var] is the conventional form; pop() is ours, for
    the fractional counts fweight refuses. Both must arrive."""
    text = _ado_text()
    assert "`exp'" in text and "`pop'" in text
    assert 'weight="`wvar\'"' in text, "neither weight form is passed"


def test_returns_include_the_useful_ones():
    """r(varlist) is the one that changes how the command is used."""
    text = _ado_text()
    assert re.search(r"program define equipop, rclass", text), (
        "a command that returns results must be declared rclass")
    for want in ("r(varlist)", "r(cmd)", "r(k)", "r(N_missing)",
                 "r(N_origins)", "r(unit)"):
        name = want[2:-1]
        assert re.search(r"return (local|scalar) %s\b" % name, text), (
            f"{want} is documented in the help and never set")


def test_the_help_file_exists_and_is_current():
    """`help equipop` failed until 1.36 - the first thing a Stata
    user types. The file is GENERATED from equipop/doors/help.py, so
    it cannot drift from what the other doors say."""
    import subprocess
    import sys
    sthlp = os.path.join(STATA_DIR, "equipop.sthlp")
    assert os.path.exists(sthlp), "no help file - `help equipop` fails"
    root = os.path.dirname(STATA_DIR)
    r = subprocess.run(
        [sys.executable, os.path.join(root, "tools", "make_sthlp.py"),
         "--check"], capture_output=True, text=True)
    assert r.returncode == 0, (
        "stata/equipop.sthlp is out of date - "
        "run python tools/make_sthlp.py\n" + r.stdout + r.stderr)


def test_every_help_paragraph_survives_into_the_file_as_PROSE():
    """REVIEW FINDING 1, 1.54.2. THE RELEASE-BLOCKING ONE.

    BROKEN WITH: `for line in _wrap(text): add(line)` anywhere in
    make_sthlp.py.

    `_wrap()` returns ONE STRING of joined lines. Iterating it yields
    CHARACTERS, so that loop wrote the unit-advice paragraph one
    character per line: 746 consecutive one-character lines, and
    `help equipop` unreadable from that point on, in both the SSC and
    net-install archives.

    NOTHING CAUGHT IT, and each reason is worth knowing:
      * `make_sthlp.py --check` compares the malformed output against
        the malformed generator and reports the file current.
      * test_the_help_file_holds_no_broken_smcl counts braces per
        line, and a line holding one letter has none.
      * I inspected the generated file by GREPPING for the strings I
        expected. A grep cannot tell that a paragraph has been spread
        one character per line, because every character is still
        there.

    So the property is about PROSE: each paragraph this file takes
    from the shared help source must appear in the output as
    contiguous words. Whitespace-normalising both sides is what makes
    it work - "What" split one letter per line normalises to "W h a t"
    and does not match. General over every HELP entry used, not just
    the one that broke.
    """
    sys.path.insert(0, os.path.dirname(STATA_DIR))
    from equipop.doors.help import HELP
    from tools.make_sthlp import _smcl_escape

    h = _read("equipop.sthlp")
    flat = " ".join(h.split())

    used = [k for k in HELP
            if re.search(r'HELP\[[\'"]%s[\'"]\]' % re.escape(k),
                         open(os.path.join(os.path.dirname(STATA_DIR),
                                           "tools", "make_sthlp.py"),
                              encoding="utf-8").read())]
    assert used, (
        "make_sthlp.py no longer takes any paragraph from HELP by "
        "name - this test has stopped guarding anything")
    for key in used:
        want = " ".join(_smcl_escape(HELP[key]).split())
        assert want in flat, (
            f"HELP[{key!r}] does not appear in equipop.sthlp as "
            f"continuous prose. Either it is not written out, or it "
            f"is written one character per line - which is what "
            f"`for line in _wrap(...)` does, because _wrap returns a "
            f"string and not a list.")

    # AND THE SHAPE, directly: a run of single-character lines is not
    # something any correct generator produces.
    # NO ESCAPED MARKUP IN PROSE. `_wrap` escapes braces by design,
    # so SMCL written inside a wrapped paragraph reaches the user as
    # the literal text `{c -(}cmd:equipop unit{c )-}`. Found by
    # inspecting the SHIPPED file rather than the generator - the
    # paragraph was well-formed and read wrong.
    for i, line in enumerate(h.splitlines(), 1):
        assert "{c -(}cmd:" not in line and "{c -(}opt " not in line, (
            f"line {i} of equipop.sthlp shows escaped SMCL as text: "
            f"{line.strip()[:70]!r}. _wrap() is for prose; markup has "
            f"to be written outside it.")

    runs, run = [], 0
    for line in h.splitlines():
        if len(line.strip()) == 1:
            run += 1
        else:
            if run:
                runs.append(run)
            run = 0
    if run:
        runs.append(run)
    worst = max(runs) if runs else 0
    assert worst <= 3, (
        f"equipop.sthlp has a run of {worst} consecutive "
        f"one-character lines - a paragraph is being written out "
        f"character by character")


def test_the_cell_size_help_says_HOW_to_ask_the_data():
    """JOHN, 10 OCTOBER 2026, reading `help equipop` on a working
    1.54.3 install: "can you reformulate the help around the unit(#)
    description - it doesn't indicate how to ask the data (i.e. run
    and rerun with information described in output)".

    BROKEN WITH: removing the two-run loop from HELP["unit"], or the
    Stata command from STATA_EXTRA.

    He was exactly right, and the defect is a kind worth naming: the
    old text said the unit-size report EXISTS and never said how to
    see it. **A fact where an instruction was needed.** It read as
    documentation of a feature rather than advice to a person with a
    dataset and no idea what to type.

    So the shared text now describes the LOOP, which is door-neutral:
    leave the size unset, run, read the note the run prints, set the
    size, run again. The Stata spelling cannot live in the shared
    text - the same paragraph is read in QGIS and Pro, where there is
    no command to type - so it is appended through STATA_EXTRA, the
    mechanism BACKLOG 338 added for exactly this.
    """
    sys.path.insert(0, os.path.dirname(STATA_DIR))
    from tools.make_sthlp import option_text

    text = option_text("unit(#)")
    flat = " ".join(text.split())

    # the loop, in the shared half
    assert "run as usual" in flat and "run again" in flat, (
        "the help still does not say how to ask the data - it has to "
        "describe the two-run loop, not merely report that an "
        "advisory exists")
    assert "Leave the size unset" in flat, (
        "nothing tells the user that NOT setting it is how to be "
        "asked")
    # the Stata way of asking without a run, in the door-specific half
    assert "equipop unit xvar yvar" in flat, (
        "the Stata help does not name the command that answers the "
        "question without running the analysis")
    assert "changes nothing" in flat, (
        "a user about to try an unfamiliar subcommand on real data "
        "is not told it is safe")
    # and it still promises nothing is applied for them
    assert "Nothing is ever changed for you" in flat

    # the shared half must stay door-neutral: no Stata syntax in the
    # text QGIS and Pro also show
    from equipop.doors.help import HELP

    shared = " ".join(HELP["unit"].split())
    for stata_only in ("equipop unit", "fweight", "r(", "-help "):
        assert stata_only not in shared, (
            f"{stata_only!r} is in the SHARED cell-size help, which "
            f"QGIS and ArcGIS Pro also display - door-specific facts "
            f"belong in STATA_EXTRA")

    # and it reaches the generated file as more than one paragraph
    h = _read("equipop.sthlp")
    # ANCHORED AT LINE START. `{opt unit(#)}` appears first inside
    # `{synopt:{opt unit(#)}}` in the summary table, which comes
    # BEFORE the options section - so an unanchored index sliced
    # backwards and gave an empty string. The options entry is the
    # one that BEGINS a line.
    start = h.index("\n{opt unit(#)} ") + 1
    block = h[start:h.index("\n{opt pop(varname)} ", start)]
    assert block.count("{p_end}") >= 2, (
        "the cell-size help is emitted as one paragraph - a blank "
        "line in the shared text has to become its own SMCL block, "
        "or the second paragraph renders outside the option's indent")
    assert "{phang2}" in block, (
        "a continuation paragraph is not indented under the option")


def test_every_subcommand_appears_in_the_HELP_as_well():
    """BROKEN WITH: dispatching a subcommand and not documenting it.

    JOHN'S FIELD REPORT, 10 OCTOBER 2026, generalised. He typed
    `equipop help` and the command refused it; the fix added the
    branch and named it in the unknown-subcommand list. Break-check
    then showed the HELP FILE was a third place the same omission can
    live: deleting `equipop help` from the generated syntax section
    changed nothing, because the test that derives the list from the
    dispatch only checks the ado.

    DERIVED FROM THE DISPATCH, so a fourth subcommand is covered the
    day it is written - in the ado's own list by the companion test in
    test_unitsize_doors.py, and in `help equipop` by this one.
    """
    ado = _ado_text()
    dispatched = set(re.findall(
        r'if\s+`"`eqp_sub\'"\'\s*==\s*"(\w+)"', ado))
    assert {"doctor", "setup", "unit", "help"} <= dispatched, (
        f"the dispatch handles {sorted(dispatched)} - if one was "
        f"renamed, this test and the help both need to know")

    h = _read("equipop.sthlp")
    for sub in sorted(dispatched):
        assert "{cmd:equipop %s}" % sub in h, (
            f"`equipop {sub}` is dispatched by the ado and does not "
            f"appear in the help's syntax section, so a user reading "
            f"`help equipop` cannot discover it")


def test_the_unit_subcommands_own_options_are_explained():
    """REVIEW FINDING 1's second half.

    BROKEN WITH: removing the unit-only options paragraph from
    make_sthlp.py.

    `candidates()`, `tolerance()` and `nocache` appeared in the
    `equipop unit` syntax line and were explained NOWHERE. The
    existing option test walks OPTION_HELP, which is the RUN's option
    list, so an option belonging only to the subcommand had no route
    into it and no test noticed its absence.

    Read off the generated syntax line rather than from a list here,
    so a new subcommand option is covered the moment it is offered.
    """
    h = _read("equipop.sthlp")
    i = h.index("{cmd:equipop unit}")
    syntax = h[i:h.index("{synoptset", i)]
    opts = {o.lower() for o in re.findall(r"\{opt ([a-zA-Z_:]+)\(", syntax)}
    opts |= {o.lower() for o in re.findall(r"\{opt ([a-zA-Z_]+)\}", syntax)}
    # {opt cand:idates(...)} - the colon marks the abbreviation
    opts = {o.replace(":", "") for o in opts}
    assert {"candidates", "tolerance", "nocache"} <= opts, (
        f"the unit syntax line no longer offers them: {sorted(opts)}")

    body = h[h.index("{cmd:equipop unit}"):]
    for opt in sorted(opts):
        assert re.search(r"\b%s\b" % re.escape(opt), body), (
            f"`{opt}` is offered in the equipop unit syntax line and "
            f"explained nowhere in the help")


def test_the_help_documents_every_r_result_the_SUBCOMMAND_returns():
    """REVIEW FINDING 1's third half, and the strongest of the three.

    BROKEN WITH: removing r(applies) from the generated scalar table.

    `r(applies)` exists SO a script can tell "no candidate size
    serves this k" from "the criterion does not apply to your origin
    rule" - both of which arrive as a missing `r(unit)`. It was
    returned by the ado and documented nowhere, which makes it
    unusable for the single job it has.

    DERIVED FROM THE ADO, not from a list kept here. A result added
    to `_equipop_unit` and not documented now fails this test, which
    is the only arrangement that cannot go stale.
    """
    ado = _ado_text()
    prog = ado.split("program define _equipop_unit,", 1)[1] \
              .split("\nend", 1)[0]
    returned = set(re.findall(
        r"return (?:scalar|local|matrix)\s+(\w+)", prog))
    assert returned, "the subcommand returns nothing - or it moved"

    h = _read("equipop.sthlp")
    # BOUNDED at the end of the subcommand's own table. Running the
    # slice to end-of-file swept in later prose about r(varlist) and
    # the reverse check reported it as documented-but-not-returned -
    # which was the test's fault, not the help's.
    start = h.index("{cmd:equipop unit} stores")
    section = h[start:h.index("{p2colreset}", start)]
    for name in sorted(returned):
        assert "r(%s)" % name in section, (
            f"equipop unit returns r({name}) and the help's own "
            f"stored-results list for the subcommand does not "
            f"mention it")
    # and nothing is documented that is not returned
    documented = set(re.findall(r"\{cmd:r\((\w+)\)\}", section))
    extra = documented - returned
    assert not extra, (
        f"the help documents r() results the subcommand does not "
        f"set: {sorted(extra)}")


def test_every_option_is_documented_in_the_help():
    """The Stata shape of door drift: an option the user can type
    and the help has never heard of."""
    sys.path.insert(0, os.path.dirname(STATA_DIR))
    from tools.make_sthlp import OPTION_HELP, option_text

    text = _ado_text()
    m = re.search(r"^\s*syntax\s(.*?)$", _join_continuations(text), re.M)
    _, _, post = m.group(1).partition(",")
    declared = {t.lower() for t in re.findall(r"([A-Za-z_]+)\s*\(", post)}
    for tok in re.findall(r"(?<![\w(])([A-Za-z_]{2,})(?![\w(])", post):
        declared.add(tok.lower())
    declared -= SYNTAX_TYPES

    documented = {o.split("(")[0].lower() for o in OPTION_HELP}
    missing = declared - documented
    assert not missing, (
        f"options with no help: {sorted(missing)} - add them to "
        f"OPTION_HELP in tools/make_sthlp.py")
    for opt in OPTION_HELP:
        assert option_text(opt).strip(), f"{opt} has empty help"


def test_net_install_manifest_lists_files_that_exist():
    """`net install` fails at the user's end, not ours, when the
    .pkg names a file that was never committed."""
    pkg = os.path.join(STATA_DIR, "equipop.pkg")
    toc = os.path.join(STATA_DIR, "stata.toc")
    assert os.path.exists(pkg) and os.path.exists(toc)
    listed = [ln.split(None, 1)[1].strip()
              for ln in open(pkg, encoding="utf-8")
              if ln.startswith("f ")]
    assert listed, "the package lists no files"
    for f in listed:
        assert os.path.exists(os.path.join(STATA_DIR, f)), (
            f"equipop.pkg lists {f}, which is not in stata/")

    # BACKLOG 334. `g` IS NOT THE ANCILLARY KEYWORD, and 330 shipped
    # for one release believing it was. `g` is PLATFORM-SPECIFIC, and
    # its syntax is `g PLATFORMNAME sourcefile targetfile` - so
    # `g equipop_example.do` reads "equipop_example.do" as a platform
    # name with no files after it, and the file does not install.
    #
    # THE PREVIOUS VERSION OF THIS TEST VALIDATED THE BUG. It walked
    # the `g` lines and checked the named file existed in stata/ -
    # which it did - so a malformed manifest passed. Found by Marina's
    # pull request, which had used `f` all along. A test written beside
    # a change tends to encode the change's assumption; this one
    # encoded a wrong one.
    PLATFORMS = {"WIN", "WIN64", "WIN64A", "MACINTEL", "MACINTEL64",
                 "MACARM64", "LINUX", "LINUX64", "SUNOS", "HP9000"}
    for ln in open(pkg, encoding="utf-8"):
        if not ln.startswith("g "):
            continue
        parts = ln.split()
        assert len(parts) >= 3 and parts[1] in PLATFORMS, (
            f"malformed `g` line in equipop.pkg: {ln.strip()!r}. "
            "`g` is the PLATFORM-SPECIFIC directive - "
            "`g PLATFORMNAME sourcefile targetfile` - and not the "
            "ancillary keyword. An ancillary .do or .dta is an "
            "ordinary `f` line; Stata decides what to do with a file "
            "from its EXTENSION, installing .ado and .sthlp into the "
            "ado path and fetching .do and .dta with `net get`, which "
            "is what the `all` option performs")

    # and the ancillary material must be declared, as `f`
    for name in os.listdir(STATA_DIR):
        if name.endswith((".do", ".dta")):
            assert name in listed, (
                f"stata/{name} is not an `f` line in equipop.pkg, so "
                "`net install equipop, all` does not bring it - which "
                "is the gap BACKLOG 330 was raised on")
    assert any(f.endswith(".sthlp") for f in listed), (
        "the package ships no help file")
    assert "p equipop" in open(toc, encoding="utf-8").read(), (
        "stata.toc does not offer the equipop package")


# ---------------------------------------------------------------------
def test_no_numlist_loop_runs_over_a_macro_that_may_be_empty():
    r"""BACKLOG 335, MARINA'S PULL REQUEST (GitHub lizardie).

    `foreach ... of numlist \`x'` with an EMPTY \`x' is a SYNTAX
    ERROR in Stata, not an empty loop. The name-length warning looped
    over k() unguarded, so a radius-only run with a treatment -
    `equipop, x() y() r(500) treat(HighEdu)` - died with "invalid
    numlist has too few elements" before computing anything.

    k() and r() are each optional and either will do (BACKLOG 305), so
    EVERY numlist loop over one of them needs the guard. The guard
    already existed forty lines above the fault, with a comment
    explaining the property - which is why this test walks the file
    rather than trusting that the lesson stuck.
    """
    import re
    src = _ado_text()
    lines = src.splitlines()
    bad = []
    for i, line in enumerate(lines):
        m = re.search(r"foreach\s+\w+\s+of\s+numlist\s+`(\w+)'", line)
        if not m:
            continue
        macro = m.group(1)
        # look back for an `if "`macro'" != ""` that encloses this
        guarded = any(
            f'if "`{macro}\'" != ""' in lines[j]
            for j in range(max(0, i - 12), i))
        if not guarded:
            bad.append((i + 1, macro, line.strip()))
    assert not bad, (
        "these numlist loops are not guarded against an empty macro, "
        "which is a Stata SYNTAX ERROR rather than an empty loop:\n"
        + "\n".join(f"  line {n}: {macro} in {text}"
                     for n, macro, text in bad))


def test_replace_drops_every_column_the_run_will_create():
    """BACKLOG 336, MARINA'S PULL REQUEST. -replace- cleared N_, Dist_,
    T_ and R_ and NOT the decay outputs ND_, TD_, RD_ - so repeating a
    decay() run with replace failed, telling the user to "use option
    replace" when they already had.

    The prefixes are read from the ENGINE rather than listed here, so
    a new output family added to the engine fails this test instead of
    quietly escaping the drop list, which is how these three did.
    """
    import re
    from equipop.analysis import NAMES
    src = _ado_text()
    block = src[src.index("drop what we are about to write"):
                src.index("WARN ABOUT LONG NAMES")]
    # the SHORT naming scheme is the one the Stata door uses
    families = {tpl.split("{")[0].rstrip("_")
                for tpl in NAMES["short"].values()}
    # BOTH HALVES, SEPARATELY. The first version of this test searched
    # the whole block, so deleting the decay drop from the k half
    # still passed - the radius half's `drop `prefix'ND_r`rl'` matched
    # the same pattern. Caught by breaking it; a family has to be
    # dropped for k AND for r, because a run can ask for either.
    k_half = block[block.index('if "`k' + chr(39) + '" != ""'):
                   block.index('if "`r' + chr(39) + '" != ""')]
    r_half = block[block.index('if "`r' + chr(39) + '" != ""'):]
    #: Dist_ is the one exception, and a RULING not an oversight: a
    #: radius run reports no distance, because the radius IS the
    #: distance (BACKLOG 203, John's ruling). So the engine never
    #: makes Dist_r500 and nothing should drop it.
    for half, name, skip in ((k_half, "k()", set()),
                             (r_half, "r()", {"Dist"})):
        missing = sorted(f for f in families - skip
                         if not re.search(rf"drop `prefix'{f}_", half))
        assert not missing, (
            f"-replace- never drops {missing} in the {name} branch, "
            "which the engine produces there, so a second run with "
            "replace stops on 'already defined' and tells the user to "
            "use the option they used. The families come from "
            f"equipop.analysis.NAMES: {sorted(families)}")


def test_a_literal_brace_is_escaped_once_and_only_once():
    """BACKLOG 330. Every escaped brace in the shipped help was
    malformed, and had been since the generator was written.

    _smcl_escape did `.replace("{", "{c -(}").replace("}", "{c )-}")`,
    and the second replace ate the first one's OUTPUT: the `}` of
    `{c -(}` became `{c )-}`, so a literal brace shipped as
    `{c -({c )-}`. Then the line wrapper, which knows nothing about
    SMCL, was free to break the wreckage across a newline. Five of
    them were in the file Kit Baum read for the SSC submission.

    THIS TEST EXISTS BECAUSE THE OUTPUT CHECK BELOW CANNOT FAIL ANY
    MORE. Once the five paragraphs that carried markup were moved to
    _smcl, nothing in the generator reached _smcl_escape with a brace
    in it, so breaking the function again changed no shipped byte -
    the output check passed over the restored bug. _smcl_escape is
    still live for option text out of help.py, so it is pinned here,
    on its own, where a break has to show.
    """
    from tools.make_sthlp import _smcl_escape
    assert _smcl_escape("{help python}") == "{c -(}help python{c )-}"
    assert _smcl_escape("r{k}") == "r{c -(}k{c )-}"
    assert _smcl_escape("no braces") == "no braces"


def test_the_help_file_holds_no_broken_smcl():
    """The same fault seen from the OUTPUT side, which is the side a
    user meets. It cannot catch a regression in _smcl_escape today
    (see above) and it can catch the other two ways this breaks: a new
    _wrap call given markup, and a directive split across a line."""
    h = _read("equipop.sthlp")
    assert "{c -({c )-}" not in h, (
        "malformed brace escape in the help file: the escape "
        "sequence has been escaped again")
    for i, line in enumerate(h.splitlines(), 1):
        # a directive must open and close on ONE line - Stata reads
        # `{cmd:python\nquery}` as markup that never closes
        assert line.count("{") == line.count("}"), (
            f"line {i} of equipop.sthlp leaves an SMCL directive "
            f"open across the line break: {line!r}")


# BACKLOG 285/286 - the help's examples, and names that are too long.
# ---------------------------------------------------------------------
def test_every_option_in_every_example_exists():
    """Claude wrote overshoot(shares) from memory. The real values are
    `whole` and `proportional`, and `sampled` is not offered by the
    Stata door at all - so a user copying the help would have been
    refused by the command the help documents."""
    import re
    h = _read("equipop.sthlp")
    ado = _ado_text()
    ex = h[h.index("{title:Examples}"):h.index("{marker author}")]
    i = ado.index("    syntax ")
    syn = ado[i:ado.index("\n\n", i)].lower()
    for cmd in re.findall(r"\{cmd:\. (equipop[^}]*)\}", ex):
        for opt in re.findall(r"(\w+)\(", cmd):
            assert opt.lower() in syn, (
                f"the help shows {opt}() and the syntax line has no "
                f"such option: {cmd}")


def test_every_VALUE_in_the_examples_is_accepted():
    """decay(negexp) and overshoot(proportional) must be words the
    command actually takes."""
    import re
    h = _read("equipop.sthlp")
    ado = _ado_text()
    ex = h[h.index("{title:Examples}"):h.index("{marker author}")]
    for opt in ("decay", "overshoot"):
        i = ado.index(f'inlist("`{opt}\'')
        allowed = set(re.findall(r'"([a-z]+)"', ado[i:i + 260]))
        for cmd in re.findall(r"\{cmd:\. (equipop[^}]*)\}", ex):
            for used in re.findall(rf"{opt}\((\w+)\)", cmd):
                assert used in allowed, (
                    f"{opt}({used}) is in the help; the command takes "
                    + ", ".join(sorted(allowed - {""})))


def test_the_examples_cover_what_john_asked_for():
    h = _read("equipop.sthlp")
    ex = h[h.index("{title:Examples}"):h.index("{marker author}")]
    for want in ("pop(", "selfpot(", "decay(", "overshoot("):
        assert want in ex, f"no example uses {want}"


def test_pop_and_fweight_are_explained_as_the_same_thing():
    """John asked what [fweight=] is for when pop() exists. They mean
    the same; fweight demands whole numbers and pop() does not."""
    h = _read("equipop.sthlp")
    ex = h[h.index("{title:Examples}"):h.index("{marker author}")]
    assert "same thing" in ex and "never both" in ex
    assert "FRACTIONAL" in ex


def test_long_names_are_shortened_rather_than_refused():
    """John's run finished 646,766 cells, three widened passes and two
    k values, and THEN stopped because a name was 33 characters. The
    arithmetic was done; only the label was too long."""
    ado = _ado_text()
    assert "SHORTEN RATHER THAN REFUSE" in ado
    assert "_shorten" in ado
    assert "were shortened" in ado, "every rename must be announced"


def test_the_length_warning_comes_BEFORE_the_computation():
    """A ten-minute run must not die at the labelling step."""
    ado = _ado_text()
    warn = ado.index("names will exceed Stata's 32")
    run = ado.index("python: _equipop_machine1(")
    assert warn < run, "the warning is after the run again"


# ---------------------------------------------------------------------
# BACKLOG 287 - THE RENAME WAS ANNOUNCED AND NOT APPLIED. The names
# were shortened, printed to John correctly, and then the writing loop
# rebuilt each name from `res` and created the ORIGINAL - so Stata
# refused with "invalid varname" AFTER the rename had been shown. The
# names were right on screen and wrong in the data.
#
# These tests EXECUTE the shipped naming block rather than reading it,
# because the previous version passed every reading test it had.
# ---------------------------------------------------------------------
def _naming_block():
    import re
    import textwrap
    s = _ado_text()
    i = s.index("    wanted = [prefix + name for name in res]")
    j = s.index("    problems = []", i)
    block = textwrap.dedent(s[i:j])
    return re.sub(r"SFIToolkit\.displayln\(", "(lambda *a: None)(",
                  block)


def _run_naming(res, prefix, existing=()):
    ns = {"res": res, "prefix": prefix, "existing": set(existing)}
    exec(_naming_block(), ns)
    return ns["use"], ns["wanted"]


JOHNS = {f"{v}_{k}": None
         for v in ("h72003_whitealone", "h72004_africanamericanalone",
                   "h72006_asianalone")
         for k in (25, 50, 100, 200, 400, 800, 1600, 3200)}


@pytest.mark.parametrize("prefix", ["N_", "T_", "R_"])
def test_every_written_name_fits_stata(prefix):
    use, _ = _run_naming(JOHNS, prefix)
    over = {k: v for k, v in use.items() if len(v) > 32}
    assert not over, over


@pytest.mark.parametrize("prefix", ["N_", "T_", "R_"])
def test_the_names_stay_distinct(prefix):
    use, _ = _run_naming(JOHNS, prefix)
    assert len(set(use.values())) == len(use)


def test_the_MAPPING_is_what_the_writer_uses():
    """The fault: `use` was never built, so the writer rebuilt the
    long name from res. A test that only read the announcement would
    still have passed."""
    ado = _ado_text()
    assert "name = use[key]" in ado, (
        "the writing loop must take the shortened name")
    assert "name = prefix + name" not in ado, (
        "the writing loop is rebuilding the original name again")


def test_a_short_name_is_left_exactly_alone():
    use, _ = _run_naming({"h72003_whitealone_100": None}, "T_")
    assert use["h72003_whitealone_100"] == "T_h72003_whitealone_100"


def test_the_k_survives_shortening():
    """The tail says which k and the prefix says which measure - both
    carry meaning, so only the middle may be cut."""
    use, _ = _run_naming(JOHNS, "T_")
    for key, name in use.items():
        assert name.endswith("_" + key.rsplit("_", 1)[1]), name
        assert name.startswith("T_"), name


def test_two_names_that_truncate_alike_are_disambiguated():
    res = {"averyverylongvariablenamehere_100": None,
           "averyverylongvariablenamehero_100": None}
    use, _ = _run_naming(res, "T_")
    assert len(set(use.values())) == 2
    assert all(len(v) <= 32 for v in use.values())
