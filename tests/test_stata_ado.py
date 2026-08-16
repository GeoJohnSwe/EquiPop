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
    """
    text = _read(ado)
    block = _python_block(text)
    if block is None:
        pytest.skip(f"{ado} has no python: block")
    tree = ast.parse(block)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if getattr(node.func, "attr", None) != "store":
            continue
        assert len(node.args) >= 3, f"{ado}: odd Data.store call"
        values = node.args[2]
        for sub in ast.walk(values):
            assert not (isinstance(sub, ast.Constant) and sub.value is None), (
                f"{ado}: Data.store is handed None among its VALUES - "
                f"Stata refuses it with 'the specified value should be "
                f"a numeric value'. Use to_stata_values().")


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
    assert any(f.endswith(".sthlp") for f in listed), (
        "the package ships no help file")
    assert "p equipop" in open(toc, encoding="utf-8").read(), (
        "stata.toc does not offer the equipop package")
