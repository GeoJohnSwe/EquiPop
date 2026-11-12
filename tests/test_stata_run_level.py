# -*- coding: utf-8 -*-
"""BACKLOG 487: equipop_run brought level with equipop.

John's ruling, 11 November 2026, on a finding of the code review of
1.63.7: "bring it up to level with equipop". What -equipop- had and
this command did not:

  * [if] [in] - with -equipop-'s rule: they choose the rows that GET
    results; everybody still counts as a neighbour;
  * returned results - r(varlist) above all;
  * overshoot() and originrule(), the two settings that move every
    k-based number;
  * refusals in the words of its own options. The engine used to
    answer "give k_values and/or r_values", a slope run without dem()
    died inside the raster library, fca without demandvar() was a
    KeyError, and stats without values() ran and returned counts.

The Python half is RUN here, against -equipop- itself where the two
overlap. The Stata half cannot be run without Stata: its new lines are
read, and its braces and line continuations are checked mechanically.
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stata_sim as SS                                       # noqa: E402

STATA = SS.STATA


def _equipop(df, **kw):
    ns, st = SS.start(df.assign(__touse=1.0) if "__touse" not in df
                      else df)
    SS.run_block(SS.blocks(os.path.join(STATA, "equipop.ado"))[0], ns)
    args = dict(x="X_local", y="Y_local", treat="", k="", unit=100.0,
                touse="__touse", unit_was_set=1)
    args.update(kw)
    with contextlib.redirect_stdout(io.StringIO()):
        ns["_equipop_machine1"](**args)
    return st


def _run(df, engine, **kw):
    ns, st = SS.start(df)
    SS.run_block(SS.blocks(os.path.join(STATA, "equipop_run.ado"))[0], ns)
    a = dict(engine=engine, xv="X_local", yv="Y_local")
    a.update(kw)
    with contextlib.redirect_stdout(io.StringIO()):
        ns["_equipop_run"](**a)
    return st


@pytest.fixture(scope="module")
def data():
    return SS.load_test_data().iloc[:3000].reset_index(drop=True)


# ------------------------------------------------------------ if / in
def test_if_chooses_who_gets_results_not_who_is_a_neighbour(data):
    """BROKEN WITH: `keep` not applied when storing - every row gets
    a result; or the rows outside the sample dropped before computing
    - the results inside it change."""
    everyone = _run(data, "counts", treatv="HighEdu", ks="100").df
    sample = (np.arange(len(data)) % 3 == 0).astype(float)
    some = _run(data.assign(__touse=sample), "counts", treatv="HighEdu",
                ks="100", touse="__touse").df
    inside = sample > 0
    for col in ("N_100", "Dist_100", "T_HighEdu_100", "R_HighEdu_100"):
        a = everyone[col].to_numpy(float)
        b = some[col].to_numpy(float)
        assert np.allclose(a[inside], b[inside], equal_nan=True), col
        assert np.isnan(b[~inside]).all(), col
    assert np.isfinite(some["N_100"].to_numpy(float)[inside]).any()


def test_if_is_the_same_rule_as_equipop(data):
    sample = (data["HighEdu"].to_numpy(float) == 1).astype(float)
    d = data.assign(__touse=sample)
    e = _equipop(d, treat="HighEdu", k="100").df
    c = _run(d, "counts", treatv="HighEdu", ks="100", touse="__touse").df
    for col in ("N_100", "T_HighEdu_100", "R_HighEdu_100"):
        assert np.allclose(c[col], e[col], equal_nan=True), col


@pytest.mark.parametrize("engine,kw,first", [
    ("stats", dict(valuesv="ValFloat", ks="50"), "N_50"),
    ("lisa", dict(valuesv="ValFloat", ks="8"), "LISA_ValFloat_Ii"),
])
def test_if_reaches_the_other_engines(data, engine, kw, first):
    sample = (np.arange(len(data)) < 500).astype(float)
    st = _run(data.assign(__touse=sample), engine, touse="__touse", **kw)
    made = st.locals["eqp_run_varlist"].split()
    assert first in made
    for v in made:
        assert np.isnan(st.df[v].to_numpy(float)[500:]).all(), v
    assert np.isfinite(st.df[first].to_numpy(float)[:500]).any()


# ----------------------------------------------------- returned results
def test_the_names_of_what_was_made_are_handed_back(data):
    """r(varlist) is built from this. BROKEN WITH: the setLocal left
    out - -summarize `r(varlist)'- then summarizes everything."""
    st = _run(data, "counts", treatv="HighEdu", ks="50 100")
    made = st.locals["eqp_run_varlist"].split()
    assert made == [c for c in st.df.columns if c not in data.columns]
    assert {"N_50", "N_100", "R_HighEdu_100"} <= set(made)
    assert st.locals["eqp_run_overshoot"] == "proportional"
    assert st.locals["eqp_run_originrule"] == "include"
    # the two engines that do not count a neighbourhood name no rule
    st = _run(data, "lisa", valuesv="ValFloat", ks="8")
    assert "eqp_run_overshoot" not in st.locals


# ------------------------------------------------- the two rules
def test_originrule_and_overshoot_are_equipops(data):
    """The same option, the same numbers as -equipop-.
    BROKEN WITH: self_rule / overshoot_mode not passed to dispatch -
    exclude gives the include numbers."""
    for rule in ("include", "exclude"):
        for over in ("whole", "proportional"):
            e = _equipop(data, treat="HighEdu", k="100",
                         originrule=rule, overshoot=over).df
            st = _run(data, "counts", treatv="HighEdu", ks="100",
                      originrule=rule, overshoot=over)
            c = st.df
            for col in ("N_100", "Dist_100", "R_HighEdu_100"):
                assert np.allclose(c[col], e[col], equal_nan=True), (
                    rule, over, col)
            assert st.locals["eqp_run_originrule"] == rule
            assert st.locals["eqp_run_overshoot"] == over
    inc = _run(data, "counts", treatv="HighEdu", ks="100").df
    exc = _run(data, "counts", treatv="HighEdu", ks="100",
               originrule="exclude").df
    assert not np.allclose(inc["R_HighEdu_100"], exc["R_HighEdu_100"],
                           equal_nan=True)


def test_the_rules_reach_value_statistics(data):
    inc = _run(data, "stats", valuesv="ValFloat", ks="50",
               statss="mean").df
    exc = _run(data, "stats", valuesv="ValFloat", ks="50",
               statss="mean", originrule="exclude").df
    col = [c for c in inc.columns if c.startswith("Mean_")][0]
    assert not np.allclose(inc[col], exc[col], equal_nan=True)


def test_a_rule_the_engine_does_not_know_is_a_message(data):
    with pytest.raises(SS.StataError) as e:
        _run(data, "counts", ks="50", overshoot="half")
    assert e.value.args == (198,)
    assert any("half" in line for line in SS._State.err)


# ------------------------------------------- the Stata half, read
def _stata_half():
    text = open(os.path.join(STATA, "equipop_run.ado"),
                encoding="utf-8").read()
    return text.split("\npython:\n")[0]


def _code_lines(stata):
    """Statements of the Stata half: comments out, continuation lines
    joined, quoted text blanked - enough to count braces by."""
    joined, buf = [], ""
    for raw in stata.splitlines():
        line = raw.rstrip()
        if line.lstrip().startswith(("*", "//")) and not buf:
            continue
        if line.endswith("///"):
            buf += line[:-3] + " "
            continue
        joined.append(buf + line)
        buf = ""
    assert buf == "", "a line ends in /// with nothing after it"
    out = []
    for line in joined:
        line = re.sub(r'`"[^\n]*?"\'', '""', line)       # compound
        line = re.sub(r'"[^"\n]*"', '""', line)          # plain
        out.append(line)
    return out


@pytest.mark.parametrize("name", ["equipop_run.ado", "equipop.ado",
                                  "equipop_knn.ado"])
def test_the_stata_half_is_bracketed(name):
    """Not run - there is no Stata here - but every block that opens
    closes, and no statement is left hanging on a ///.
    BROKEN WITH: one closing brace removed from any of the new
    blocks."""
    stata = open(os.path.join(STATA, name),
                 encoding="utf-8").read().split("\npython:\n")[0]
    depth = 0
    for line in _code_lines(stata):
        depth += line.count("{") - line.count("}")
        assert depth >= 0, line
    assert depth == 0


def test_the_command_is_rclass_takes_if_in_and_marks_the_sample():
    s = _stata_half()
    assert "program define equipop_run, rclass" in s
    assert re.search(r"syntax \[if\] \[in\],", s)
    assert "marksample touse, novarlist" in s
    assert 'touse="`touse' + "'" + '"' in s
    for name in ("cmd", "cmdline", "engine", "varlist", "treat",
                 "values", "k", "r", "tau", "overshoot", "originrule"):
        assert re.search(r"return local %s\s" % name, s), name
    for name in ("unit", "selfpot", "N_origins", "N_missing"):
        assert re.search(r"return scalar %s\s*=" % name, s), name
    # the names the Python hands back are the names the Stata reads
    assert '"`eqp_run_varlist' + "'" + '"' in s
    py = open(os.path.join(STATA, "equipop_run.ado"),
              encoding="utf-8").read().split("\npython:\n")[1]
    for name in ("eqp_run_varlist", "eqp_run_overshoot",
                 "eqp_run_originrule"):
        assert f'Macro.setLocal("{name}"' in py and name in s, name


@pytest.mark.parametrize("words", [
    'engine() must be counts, stats, friction, " ///',
    "needs k(), r() or both",
    "engine(stats) needs values()",
    "needs k(), tau() or both",
    "engine(slope) needs dem()",
    "engine(lisa) needs exactly one variable",
    "engine(fca) needs demandvar()",
    "engine(fca) needs supply()",
    "reach() must be decay, r or k",
    "needs halflife(#)",
    "reach(r) needs rfca(#)",
    "reach(k) needs kfca(#)",
    "method() must be 2sfca or 3sfca",
    "overshoot() does not apply to engine(",
    "originrule() does not apply to engine(",
    "overshoot(sampled) is not available in Stata",
])
def test_each_refusal_is_in_the_commands_own_words(words):
    """Read, not run. Each of these used to arrive in the engine's
    words, as a traceback, or not at all."""
    assert words in _stata_half(), words


def test_a_catchment_needs_no_half_life_unless_it_decays(data, tmp_path):
    """reach(r) and reach(k) run without halflife(); the default,
    reach(decay), does not - and the Stata half says so before Python
    is reached (the line is among the refusals above)."""
    import pandas as pd
    pts = data.dropna(subset=["X_local"]).sample(20, random_state=1)
    sup = tmp_path / "supply.csv"
    pd.DataFrame({"x": pts.X_local, "y": pts.Y_local,
                  "supply": np.arange(1, 21)}).to_csv(sup, index=False)
    for kw in (dict(reach="r", rfca=2000.0), dict(reach="k", kfca=5.0)):
        st = _run(data, "fca", demv="ValCount", supf=str(sup), **kw)
        assert st.locals["eqp_run_varlist"].split() == ["A", "J"]
        assert np.isfinite(st.df["A"].to_numpy(float)).any()
    with pytest.raises(SS.StataError):
        _run(data, "fca", demv="ValCount", supf=str(sup))
