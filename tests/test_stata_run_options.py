# -*- coding: utf-8 -*-
"""BACKLOG 490: equipop_run refuses an option the engine does not read.

Found by the independent review of 1.64.0 (11 November 2026).
equipop_run declares every engine's options in one syntax line, and
1.64.0 checked only that each engine got what it NEEDS. What it does
not read was accepted and dropped: model(linear) with engine(counts),
halflife(500) with engine(counts) - no decay, no word - and r(500)
with engine(friction), which counts by k and tau only. Each ran with
a clean log. John ruled against exactly that in ArcGIS Pro the same
day (486).

The Stata half records the options TYPED, before any default is filled
in; the Python half holds the table and refuses. Both are tested: the
table and the refusal are RUN, the Stata half is READ - and the two
are checked against the syntax line, so an option added to it without
an entry in the table fails here.
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stata_sim as SS                                       # noqa: E402

ADO = os.path.join(SS.STATA, "equipop_run.ado")
ENGINES = ("counts", "stats", "friction", "slope", "fca", "lisa")


@pytest.fixture(scope="module")
def data():
    return SS.load_test_data().iloc[:400].reset_index(drop=True)


def _block(df):
    ns, st = SS.start(df)
    SS.run_block(SS.blocks(ADO)[0], ns)
    return ns, st


@pytest.fixture(scope="module")
def table(data):
    ns, _ = _block(data)
    return ns["_RUN_OPTIONS"], ns["_run_options_not_read"]


# ------------------------------------------------------ the table
@pytest.mark.parametrize("engine", ENGINES)
def test_every_option_an_engine_reads_is_accepted(table, engine):
    options, unread = table
    own = [o for o, readers in options.items() if engine in readers]
    if engine in options["treatmode"]:
        assert "treat" in own              # treatmode() comes with it
    assert unread(engine, own) == []


@pytest.mark.parametrize("engine,option,words", [
    ("counts", "model", "only engine(slope) reads it"),
    ("counts", "halflife", "no distance decay"),
    ("counts", "tau", "budget of effort"),
    ("friction", "r", "count by k() and tau(), not by distance"),
    ("slope", "r", "not by distance"),
    ("friction", "dem", "terrain is engine(slope)"),
    ("friction", "model", "engine(slope)"),
    ("stats", "treat", "engine(counts), engine(friction) and "
                       "engine(slope) read it"),
    ("fca", "weight", "demandvar()"),
    ("fca", "k", "reach(k) kfca(#)"),
    ("fca", "selfpot", "Leave it out"),
    ("lisa", "weight", "Leave it out"),
    ("counts", "wperm", "only engine(lisa) reads it"),
])
def test_an_option_the_engine_does_not_read_is_named(table, engine,
                                                     option, words):
    """BROKEN WITH: the option missing from the table, or its engine
    list too wide - the run goes ahead without it, as in 1.64.0."""
    _, unread = table
    lines = unread(engine, [option])
    assert len(lines) == 1, lines
    assert lines[0].startswith(f"{option}() does nothing with "
                               f"engine({engine})")
    assert words in lines[0]


def test_treatmode_without_treat_is_named(table):
    _, unread = table
    assert "no treat() was given" in " ".join(unread("counts",
                                                     "treatmode"))
    assert unread("counts", "treat treatmode") == []


# ------------------------------------------- the Python half, run
def _run(df, engine, **kw):
    ns, st = _block(df)
    a = dict(engine=engine, xv="X_local", yv="Y_local")
    a.update(kw)
    with contextlib.redirect_stdout(io.StringIO()):
        ns["_equipop_run"](**a)
    return st


def test_a_refused_option_stops_the_run_before_anything_is_made(data):
    before = list(data.columns)
    with pytest.raises(SS.StataError) as e:
        _run(data, "counts", ks="50", model="linear", given="k model")
    assert e.value.args == (198,)
    said = " ".join(SS._State.err)
    assert "nothing was computed" in said
    assert "model() does nothing with engine(counts)" in said
    assert list(SS._State.df.columns) == before


def test_the_options_typed_are_read_from_the_stata_half(data):
    """No given= from the caller: the Python reads the macro the Stata
    half filled - here halflife(), which counts never read."""
    ns, st = _block(data)
    st.locals["eqp_given"] = " k halflife"
    with pytest.raises(SS.StataError):
        with contextlib.redirect_stdout(io.StringIO()):
            ns["_equipop_run"](engine="counts", xv="X_local",
                               yv="Y_local", ks="50", hl=500.0)
    assert any("halflife() does nothing" in line for line in st.err)


def test_options_that_are_read_still_run(data):
    st = _run(data, "counts", ks="50", treatv="HighEdu",
              given="k treat")
    assert "N_50" in st.locals["eqp_run_varlist"].split()


# ---------------------------------------------- the Stata half, read
def _stata_half():
    text = open(ADO, encoding="utf-8").read().split("\npython:\n")[0]
    return re.sub(r"///\s*\n\s*", " ", text)        # join continuations


def _syntax_options(stata):
    line = re.search(r"syntax \[if\] \[in\],(.*?)\n", stata).group(1)
    words = re.sub(r"\([^)]*\)", "", line)           # drop (real 100) ...
    return {w.lower() for w in re.findall(r"\b[A-Z][A-Za-z]*\b", words)}


def _defaults(stata):
    line = re.search(r"syntax \[if\] \[in\],(.*?)\n", stata).group(1)
    return {m.group(1).lower(): float(m.group(2)) for m in
            re.finditer(r"\b([A-Z][A-Za-z]*)\(real (-?[\d.]+)\)", line)}


def test_the_table_covers_every_option_of_the_syntax_line(table):
    """BROKEN WITH: an option added to the syntax line and not to the
    table - accepted, recorded, and never checked."""
    options, _ = table
    stata = _stata_half()
    syntax = _syntax_options(stata) - {"engine", "x", "y", "unit",
                                       "replace"}
    assert syntax == set(options), (syntax ^ set(options))


def test_the_stata_half_records_every_option_with_its_own_default(table):
    """The list the Stata half walks, and the defaults it compares the
    numbers with, are the syntax line's own.
    BROKEN WITH: an option missing from the foreach list, or a default
    copied wrongly (wperm 199, selfpot 1)."""
    options, _ = table
    stata = _stata_half()
    listed = re.search(r"foreach eqp_o in (.*?)\{", stata).group(1).split()
    numeric = re.findall(r"if `(\w+)' != (-?[\d.]+)\s+local eqp_given",
                         stata)
    assert set(listed) | {n for n, _ in numeric} == set(options)
    assert not set(listed) & {n for n, _ in numeric}
    defaults = _defaults(stata)
    for name, value in numeric:
        assert defaults[name] == float(value), name
    # recorded BEFORE the first default is filled in
    assert stata.index("local eqp_given") < stata.index(
        'local treatmode "counts"')
    assert stata.index("local eqp_given") < stata.index(
        'local model "tobler"')
