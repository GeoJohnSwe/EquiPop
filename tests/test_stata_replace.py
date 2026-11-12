# -*- coding: utf-8 -*-
"""BACKLOG 473 and 474: -replace- deletes what it was asked to
replace and nothing else, and the dataset characteristic is stored.

Found in the code review of 1.63.7 (10 November 2026).

473  -equipop ..., replace- ran -capture drop NAME- for every name it
     was about to write. With -set varabbrev on-, which is Stata's
     default, -drop N_100- deletes N_1000 when there is no N_100: the
     name is read as an abbreviation. A k(100) run with replace could
     so delete the results of a k(1000) run, and a treat() variable
     could take a user's own variables with it. And the dropping came
     BEFORE the computing, so a run that stopped left neither the old
     results nor new ones.
     -equipop_run- did the same from its Python, and wrote its result
     variables one at a time: an existing name half-way through left
     the first few behind.

474  -equipop unit- stores its advice on the dataset with
     Characteristic.getDta / setDta. sfi has getDtaChar / setDtaChar.
     So nothing was ever stored, and every call recounted.

The stand-in (tests/stata_sim.py) now resolves a name as Stata does,
abbreviations included; before, it dropped exact names only and could
not show the fault.
"""
from __future__ import annotations

import contextlib
import io
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stata_sim as SS                                       # noqa: E402

STATA = SS.STATA


def _equipop(df, **kw):
    """`equipop` as the ado calls its Python."""
    ns, st = SS.start(df.assign(__touse=1.0))
    SS.run_block(SS.blocks(os.path.join(STATA, "equipop.ado"))[0], ns)
    args = dict(x="X_local", y="Y_local", treat="", k="", r="",
                unit=100.0, weight="", selfpot=1.0, touse="__touse",
                prefix="", project="", epsg=0, treatmode="", missing="",
                decay="", halflife=0.0, halflifevar="", bins=10,
                overshoot="", originrule="", calibration="",
                unit_was_set=1, replace="")
    args.update(kw)
    with contextlib.redirect_stdout(io.StringIO()):
        ns["_equipop_machine1"](**args)
    return st


def _run(df, engine, **kw):
    """`equipop_run` as its ado calls its Python."""
    ns, st = SS.start(df)
    SS.run_block(SS.blocks(os.path.join(STATA, "equipop_run.ado"))[0], ns)
    a = dict(engine=engine, xv="X_local", yv="Y_local", treatv="",
             valuesv="", statss="", ks="", rs="", taus="", unit=100.0,
             wv="", dem="", model="tobler", rt=0, fricf="", demv="",
             supf="", supcol="supply", supx="x", supy="y", hl=0.0,
             reach="decay", method="2sfca", kfca=0.0, rfca=0.0, rep=0,
             selfpot=1.0, wperm=199)
    a.update(kw)
    with contextlib.redirect_stdout(io.StringIO()):
        ns["_equipop_run"](**a)
    return st


@pytest.fixture(scope="module")
def data():
    return SS.load_test_data()


# ------------------------------------------------- the stand-in itself
def test_the_stand_in_drops_as_stata_does():
    """If this stops holding, the tests below certify nothing: the
    danger must be reproducible here."""
    import pandas as pd
    ns, st = SS.start(pd.DataFrame({"N_1000": [1.0], "Age": [2.0],
                                    "Agegroup": [3.0], "T_Age_250": [4.]}))
    sfi = sys.modules["sfi"]
    sfi.SFIToolkit.stata("capture drop N_100")       # an abbreviation
    assert "N_1000" not in st.df, "Stata would have deleted N_1000"
    sfi.SFIToolkit.stata("capture drop Ag")          # ambiguous: kept
    assert {"Age", "Agegroup"} <= set(st.df.columns)
    sfi.SFIToolkit.stata("capture novarabbrev drop T_Age_25")
    assert "T_Age_250" in st.df                      # exact names only
    with pytest.raises(SS.StataError):
        sfi.SFIToolkit.stata("novarabbrev drop T_Age_25")
    sfi.Data.dropVar(0)                              # by position
    assert list(st.df.columns) == ["Agegroup", "T_Age_250"]
    with pytest.raises(ValueError):
        sfi.Data.dropVar("T_Age_25")                 # sfi: exact or not


# ----------------------------------------------------------- equipop
def test_replace_leaves_a_longer_name_alone(data):
    """k(100) with replace, on a dataset that holds the results of
    k(1000) and no N_100.
    BROKEN WITH: -capture drop- on the names (1.63.7) - N_1000 and
    Dist_1000 are deleted. Here: SFIToolkit.stata("capture drop " + n)
    in place of _drop_exactly."""
    df = data.assign(N_1000=7.0, Dist_1000=8.0, T_HighEdu_1000=9.0)
    st = _equipop(df, treat="HighEdu", k="100", replace="replace")
    assert (st.df["N_1000"] == 7.0).all()
    assert (st.df["Dist_1000"] == 8.0).all()
    assert (st.df["T_HighEdu_1000"] == 9.0).all()
    assert {"N_100", "Dist_100", "T_HighEdu_100"} <= set(st.df.columns)


def test_replace_replaces_exactly_what_is_written(data):
    df = data.assign(N_100=-1.0, Dist_100=-1.0, Mine=5.0)
    st = _equipop(df, k="100", replace="replace")
    assert (st.df["N_100"].dropna() >= 0).all()      # the new numbers
    assert (st.df["Mine"] == 5.0).all()
    assert list(st.df.columns).count("N_100") == 1


def test_without_replace_an_existing_name_still_stops_the_run(data):
    df = data.assign(N_100=-1.0)
    with pytest.raises(SS.StataError):
        _equipop(df, k="100")
    st = SS._State
    assert any("N_100 already exists - use option replace" in e
               for e in st.err)
    assert (st.df["N_100"] == -1.0).all()            # and nothing changed
    assert "Dist_100" not in st.df


def test_a_run_that_stops_keeps_the_old_results(data):
    """The old results are dropped only once the new ones exist.
    BROKEN WITH: dropping before the engine is called (1.63.7)."""
    df = data.assign(N_100=-1.0, Dist_100=-2.0)
    with pytest.raises(SS.StataError):
        # treatmode(flags) with a variable that is not 0/1 is refused
        _equipop(df, treat="ValCount", k="100", treatmode="flags",
                 replace="replace")
    st = SS._State
    assert (st.df["N_100"] == -1.0).all()
    assert (st.df["Dist_100"] == -2.0).all()


# ------------------------------------------------------- equipop_run
def test_equipop_run_replace_leaves_a_longer_name_alone(data):
    """BROKEN WITH: SFIToolkit.stata(f"capture drop {safe}") - the
    1.63.7 line. N_2000 is deleted by the request to drop N_200."""
    df = data.assign(N_2000=7.0, Dist_2000=8.0)
    st = _run(df, "counts", ks="200", rep=1)
    assert (st.df["N_2000"] == 7.0).all()
    assert (st.df["Dist_2000"] == 8.0).all()
    assert "N_200" in st.df


def test_equipop_run_writes_all_its_variables_or_none(data):
    """Dist_200 exists, replace is not given. Until 1.63.7 N_200 was
    written first and stayed behind when Dist_200 was refused.
    BROKEN WITH: the check inside the writing loop."""
    df = data.assign(Dist_200=-2.0)
    with pytest.raises(SS.StataError):
        _run(df, "counts", ks="200")
    st = SS._State
    assert "N_200" not in st.df, "a partial result set was left behind"
    assert (st.df["Dist_200"] == -2.0).all()
    assert any("Dist_200" in e and "replace" in e for e in st.err)


def test_equipop_run_replace_replaces(data):
    df = data.assign(N_200=-1.0, Dist_200=-2.0)
    st = _run(df, "counts", ks="200", rep=1)
    assert (st.df["N_200"].dropna() >= 0).all()
    assert list(st.df.columns).count("N_200") == 1


# --------------------------------------------------------------- 474
def test_the_unit_advice_is_stored_on_the_dataset(data):
    """BROKEN WITH: Characteristic.getDta / setDta (1.63.7) - sfi has
    neither, so nothing is stored and the reason is printed instead."""
    ns, st = SS.start(data)
    SS.run_block(SS.blocks(os.path.join(STATA, "equipop.ado"))[0], ns)
    assert ns["_unit_cache_get"]() == ("", "")
    assert ns["_unit_cache_put"]("advice") == ""
    assert ns["_unit_cache_get"]() == ("advice", "")
    assert st.chars == {("_dta", "equipop_unitsize"): "advice"}


def test_no_bare_drop_is_left_in_the_stata_half():
    """Every -drop- a shipped ado still runs in Stata's own language
    must be -novarabbrev-. (None is left in 1.63.8; this keeps the
    next one honest.)"""
    import re
    for name in ("equipop.ado", "equipop_run.ado", "equipop_knn.ado"):
        text = open(os.path.join(STATA, name), encoding="utf-8").read()
        stata_half = text.split("\npython:\n")[0]
        for line in stata_half.splitlines():
            code = line.strip()
            if code.startswith("*") or code.startswith("//"):
                continue
            if re.search(r"(^|\s)drop\s", code):
                assert "novarabbrev" in code, f"{name}: {code}"
        py_half = text[len(stata_half):]
        assert "capture drop" not in py_half, name


# --------------------------------------------------------------- 475
def _weighted(data):
    """Rows that stand for several people: Pop of them, of whom Grp
    are in the group. Grp is a COUNT (0 to Pop), not a flag."""
    rng = np.random.default_rng(475)
    pop = rng.integers(1, 9, len(data)).astype(float)
    grp = np.floor(pop * rng.uniform(0, 1, len(data)))
    return data.assign(Pop=pop, Grp=grp, Flag=(grp > 0).astype(float))


def test_the_two_commands_read_treat_the_same_way(data):
    """-equipop_run, engine(counts) treat() weight()- against -equipop
    [fw=], treat()-: the same shares. The help has always said so.

    BROKEN WITH: treat_are_counts not passed to dispatch (1.63.7) -
    the engine multiplies Grp by Pop, and R is several times too
    large (the bridge then refuses it as impossible, or, with a 0/1
    variable, hands back a different share without a word)."""
    df = _weighted(data)
    e = _equipop(df, treat="Grp", k="200", weight="Pop").df
    c = _run(df, "counts", treatv="Grp", ks="200", wv="Pop").df
    assert np.allclose(c["N_200"], e["N_200"], equal_nan=True)
    assert np.allclose(c["T_Grp_200"], e["T_Grp_200"], equal_nan=True)
    assert np.allclose(c["R_Grp_200"], e["R_Grp_200"], equal_nan=True)
    assert e["R_Grp_200"].max() <= 1.0


def test_a_flag_and_a_count_are_two_different_questions(data):
    """With a 0/1 variable both readings are possible numbers, which
    is what made the disagreement silent: 'one person of the group in
    this row' against 'everybody in this row'. counts is the default
    in both commands; flags is there by name in both."""
    df = _weighted(data)
    e = _equipop(df, treat="Flag", k="200", weight="Pop").df
    c = _run(df, "counts", treatv="Flag", ks="200", wv="Pop").df
    assert np.allclose(c["R_Flag_200"], e["R_Flag_200"], equal_nan=True)
    ef = _equipop(df, treat="Flag", k="200", weight="Pop",
                  treatmode="flags").df
    cf = _run(df, "counts", treatv="Flag", ks="200", wv="Pop",
              treatmode="flags").df
    assert np.allclose(cf["R_Flag_200"], ef["R_Flag_200"], equal_nan=True)
    # and the two readings really are different numbers
    assert np.nanmean(cf["R_Flag_200"]) > 2 * np.nanmean(c["R_Flag_200"])


def test_the_effort_engine_reads_treat_the_same_way(data):
    """The friction engine with no barriers is the plain count, so its
    T must be the plain engine's T - not Grp times Pop.
    BROKEN WITH: treat_are_counts only passed for engine(counts)."""
    df = _weighted(data).iloc[:600]
    c = _run(df, "counts", treatv="Grp", ks="100", wv="Pop").df
    f = _run(df, "friction", treatv="Grp", ks="100", wv="Pop").df
    ok = np.isfinite(c["T_Grp_100"]) & np.isfinite(f["T_Grp_100"])
    assert ok.sum() > 400
    assert (f["T_Grp_100"][ok] <= f["N_100"][ok] + 1e-9).all(), (
        "a group larger than the neighbourhood that holds it")


def test_the_ado_says_which_reading_it_uses():
    """Numbers change for anybody who used treat() with weight() in
    this command, so the command says so - once per run, and only when
    treatmode() was not given."""
    text = open(os.path.join(STATA, "equipop_run.ado"),
                encoding="utf-8").read().split("\npython:\n")[0]
    assert "TREATMODE(string)" in text
    assert 'treatmode="`treatmode' + "'" + '"' in text
    assert "Until 1.63.7 this command multiplied" in text
    assert "say treatmode(flags)" in text


# --------------------------------------------------------------- 476
WINDOWS_PATHS = [r"C:\data\new\supply.csv", r"C:\temp\table.csv",
                 r"C:\Users\john\barriers.csv", "C:\\dir with space\\x.csv"]


def _the_call(name):
    """The python: statement, as far as its continuation lines go."""
    text = open(os.path.join(STATA, name), encoding="utf-8").read()
    lines = text[text.index("python: _equipop_run("):].split("\n")
    out = []
    for line in lines:
        out.append(line)
        if not line.rstrip().endswith("///"):
            break
    return "\n".join(out)


def test_no_file_name_is_pasted_into_the_python_line():
    """BROKEN WITH: dem="`dem'" (or friction, supply) in the call -
    the 1.63.7 line. C:\\temp arrives with a tab in it, C:\\Users is a
    SyntaxError."""
    call = _the_call("equipop_run.ado")
    for macro in ("dem", "friction", "supply"):
        assert "`" + macro + "'" not in call, macro
    # and, as Stata would build it, the line is valid Python whatever
    # the three options hold
    import ast
    import re
    line = " ".join(part.rstrip("/").rstrip()
                    for part in call.split("\n")).replace("python: ", "")
    for path in WINDOWS_PATHS:
        macros = {"dem": path, "friction": path, "supply": path,
                  "unit": "100", "rt": "0", "halflife": "0", "kfca": "0",
                  "rfca": "0", "rep": "0", "selfpot": "1", "wperm": "199"}
        built = re.sub(r"`(\w+)'", lambda m: macros.get(m.group(1), "v"),
                       line)
        ast.parse(built)                    # raises on a broken line


@pytest.mark.parametrize("path", WINDOWS_PATHS)
def test_the_file_names_arrive_as_typed(data, path, monkeypatch):
    """The Python reads the three macros itself, so what was typed is
    what the engine is handed - backslashes and all."""
    ns, st = SS.start(data)
    SS.run_block(SS.blocks(os.path.join(STATA, "equipop_run.ado"))[0], ns)
    st.locals.update(dem=path + ".dem", friction=path + ".fr",
                     supply=path)
    seen = {}

    def dispatch(engine, x, y, **kw):
        seen.update(kw)
        return {}

    import equipop.stata_bridge as bridge
    monkeypatch.setattr(bridge, "dispatch", dispatch)
    with contextlib.redirect_stdout(io.StringIO()):
        ns["_equipop_run"](engine="fca", xv="X_local", yv="Y_local",
                           demv="ValCount", hl=1000.0)
    assert seen["supply_file"] == path
    with contextlib.redirect_stdout(io.StringIO()):
        ns["_equipop_run"](engine="slope", xv="X_local", yv="Y_local",
                           ks="50")
    assert seen["dem"] == path + ".dem"
    assert seen["friction_file"] == path + ".fr"


def test_a_refusal_from_the_engine_is_a_message(data):
    """Not a Python traceback: the sentence, and r(198)."""
    with pytest.raises(SS.StataError) as e:
        _run(data, "lisa", valuesv="", ks="8")     # no value variable
    assert e.value.args == (198,)
    assert any("exactly one value" in line for line in SS._State.err)


# --------------------------------------------------------- 477, 478
def test_nobody_to_measure_is_said_in_words(data):
    """Every coordinate missing. Until 1.63.7: KeyError "None of
    ['EastWest', 'NorthSouth'] are in the columns", a traceback.
    BROKEN WITH: the `if not valid.any()` refusal in knn_to_rows."""
    df = data.iloc[:200].assign(X_local=np.nan, Y_local=np.nan)
    with pytest.raises(SS.StataError) as e:
        _equipop(df, k="50")
    assert e.value.args == (198,)
    said = " ".join(SS._State.err)
    assert "usable" in said and "coordinates" in said
    with pytest.raises(SS.StataError):
        _run(df, "counts", ks="50")
    assert "coordinates" in " ".join(SS._State.err)
    # and straight from Python it is a ValueError, not a KeyError
    from equipop.stata_bridge import knn_to_rows
    with pytest.raises(ValueError, match="usable coordinates"):
        knn_to_rows(np.array([np.nan, np.nan]), np.array([1.0, np.nan]),
                    k_values=[5])
    with pytest.raises(ValueError, match="no observations at all"):
        knn_to_rows(np.array([]), np.array([]), k_values=[5])


def test_the_messages_name_commands_that_exist():
    """BACKLOG 477. "equipop stats, values()" is no command, and
    -equipop setup- takes -repair- and nothing else.
    BROKEN WITH: either old sentence put back."""
    import re
    import equipop.stata_bridge as bridge
    src = open(bridge.__file__, encoding="utf-8").read()
    assert "equipop stats," not in src
    assert "equipop_run, engine(stats)" in src
    ado = open(os.path.join(STATA, "equipop.ado"), encoding="utf-8").read()
    i = ado.index("program define _equipop_setup")
    takes = re.search(r"syntax \[, ([A-Za-z ]+)\]", ado[i:i + 400]).group(1)
    allowed = {w.lower() for w in takes.split()}
    for text in (ado, src):
        for opt in re.findall(r"equipop setup, (\w+)", text):
            assert opt.lower() in allowed, f"-equipop setup, {opt}-"


def test_the_help_does_not_say_selfpot_drops_the_origin():
    """BACKLOG 477. The help's own example taught selfpot(0) as the
    way to leave the origin out. That is originrule(exclude)."""
    help_text = open(os.path.join(STATA, "equipop.sthlp"),
                     encoding="utf-8").read()
    flat = " ".join(help_text.split())
    assert "selfpot(0)} drops it" not in flat
    assert "originrule(exclude)} leaves the origin's own cell out" in flat
    assert "never who is counted" in flat


@pytest.mark.parametrize("ado,helper", [("equipop.ado", "_drop_exactly"),
                                        ("equipop_run.ado",
                                         "_run_drop_exactly")])
def test_replace_still_works_where_sfi_cannot_drop(data, ado, helper,
                                                   monkeypatch):
    """No test here can reach a real Stata, so the helper does not
    rest on one sfi call: without Data.dropVar it asks Stata, and it
    still drops exactly the names it was given."""
    ns, st = SS.start(data.iloc[:50].assign(N_100=1.0, N_1000=2.0))
    SS.run_block(SS.blocks(os.path.join(STATA, ado))[0], ns)
    sfi = sys.modules["sfi"]
    monkeypatch.delattr(sfi.Data, "dropVar")
    said = []
    real = sfi.SFIToolkit.stata
    monkeypatch.setattr(sfi.SFIToolkit, "stata",
                        staticmethod(lambda c: (said.append(c), real(c))[1]))
    ns[helper](["N_100", "Nobody"])
    assert "N_100" not in st.df and "N_1000" in st.df
    assert said == ["novarabbrev drop N_100"]
