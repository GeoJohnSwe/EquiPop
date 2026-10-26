# -*- coding: utf-8 -*-
"""The Stata files as SSC will ship them (v1.62.1).

John, 26 October 2026: "please also make sure that we have the latest
version to submit to ssc - so spend some extra time with controlling
that the stata files are correct". What that found, and what holds it:

  - `help equipop_run` and `help equipop_knn` found NOTHING: two
    commands shipped without help since they shipped. Both now have a
    help file, generated like equipop's, listed in equipop.pkg - and
    the archives are built FROM the pkg's list, not a written one.
  - The showcase called itself "EquiPop 1.46.4" and told users to
    point Stata at Anaconda, which the package description says closes
    Stata. The example did the same.
  - The help gave no contact address and offered "[R] regress" as its
    only see-also.
  - Every number the showcase tells a user to EXPECT was re-derived
    here by running the shipped Python - the ado's own block and the
    showcase's three - against the shipped test data. All held.

stata_sim.py says what this can and cannot reach: the Python half,
exactly as shipped; not Stata's own parsing.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
import stata_sim as SS                                       # noqa: E402

STATA = SS.STATA


def _text(name):
    return open(os.path.join(STATA, name), encoding="utf-8").read()


def _version():
    py = open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8").read()
    return re.search(r'^version\s*=\s*"([^"]+)"', py, re.M).group(1)


@pytest.fixture(scope="module")
def data():
    return SS.load_test_data()


def _equipop(df, **kw):
    """`equipop` as the ado calls its Python: the shipped block, the
    keyword call with the ado's defaults for every option left out."""
    ns, st = SS.start(df.assign(__touse=1.0))
    SS.run_block(SS.blocks(os.path.join(STATA, "equipop.ado"))[0], ns)
    args = dict(x="X_local", y="Y_local", treat="", k="", r="",
                unit=100.0, weight="", selfpot=1.0, touse="__touse",
                prefix="", project="", epsg=0, treatmode="", missing="",
                decay="", halflife=0.0, halflifevar="", bins=10,
                overshoot="", originrule="", calibration="",
                unit_was_set=1)
    args.update(kw)
    with contextlib.redirect_stdout(io.StringIO()):
        ns["_equipop_machine1"](**args)
    return st


def _expect(value):
    """The showcase must still SAY the number the test checks."""
    assert value in _text("equipop_showcase.do"), value


# ------------------------------------------------- the showcase's EXPECTs
def test_sections_1_to_5_give_what_the_showcase_says(data):
    """BROKEN WITH: the default overshoot changed to `whole` in the
    bridge (N_200 is then no longer exactly 200)."""
    assert int((data.X_local.isna() | data.Y_local.isna()).sum()) == 9
    _expect("EXPECT: 9.")
    d = _equipop(data, treat="HighEdu", k="50 200 800").df
    got = {c: round(float(d[c].mean()), 4) for c in
           ("N_200", "Dist_200", "R_HighEdu_50", "R_HighEdu_200",
            "R_HighEdu_800")}
    assert got == {"N_200": 200.0, "Dist_200": 1142.4042,
                   "R_HighEdu_50": .1882, "R_HighEdu_200": .1849,
                   "R_HighEdu_800": .1871}
    _expect("N_200 200.00 | Dist_200 1142.40 | R_HighEdu_50 .1882")
    w = _equipop(data, treat="HighEdu", k="200", weight="ValCount",
                 treatmode="flags").df
    assert round(float(w.R_HighEdu_200.mean()), 4) == .2089
    _expect("mean approx .2089")
    u = _equipop(data, treat="HighEdu", k="200", unit=400.0).df
    ok = d.R_HighEdu_200.notna() & u.R_HighEdu_200.notna()
    r = np.corrcoef(d.R_HighEdu_200[ok], u.R_HighEdu_200[ok])[0, 1]
    assert round(float(r), 3) == .912
    _expect("r approx 0.912")


def test_sections_6_to_8_give_what_the_showcase_says(data, tmp_path,
                                                     monkeypatch):
    """The showcase's own Python blocks, as shipped.

    BROKEN WITH: the ring engine's decay weight dropped (RD then equals
    R, and ND equals N)."""
    blocks = SS.blocks(os.path.join(STATA, "equipop_showcase.do"))
    assert len(blocks) == 3
    base = _equipop(data, treat="HighEdu", k="200").df
    ns, st = SS.start(base)
    monkeypatch.chdir(tmp_path)
    with contextlib.redirect_stdout(io.StringIO()):
        SS.run_block(blocks[0], ns)
        SS.run_block(blocks[1], ns)
    d = st.df
    assert round(float(d.Nv_ValFloat_200.mean()), 2) == 167.30
    assert round(float(d.Mean_ValFloat_200.mean()), 2) == 1815.23
    assert round(float(d.Med_ValFloat_200.mean()), 2) == 1248.10
    assert round(float(d.Gini_ValFloat_200.mean()), 4) == .5806
    _expect("Nv 167.30 | Mean 1815.23 | Med 1248.10 | Gini .5806")
    assert round(float(d.RD_HighEdu_200.mean()), 4) == .1860
    assert round(float(d.ND_200.mean()), 2) == 126.01
    _expect("RD_HighEdu_200 .1860")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        SS.run_block(blocks[2], ns)
    import pandas as pd
    prof = pd.read_csv(tmp_path / "segregation_profile_HighEdu.csv")
    si = dict(zip(prof.scale.astype(str), prof.SI.round(4)))
    assert si == {"local": .4036, "50": .2216, "200": .2002, "800": .1930}
    _expect("local .4036 | k=50 .2216 | k=200 .2002 | k=800 .1930")


# ------------------------------------------------------------ equipop_run
def _run(df, engine, **kw):
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
        ns["_equipop_run"](*a.values())
    return st.df


def test_equipop_run_reaches_every_engine(data, tmp_path):
    """Its counts are equipop's counts, and stats, lisa, friction and
    fca each store their variables.

    BROKEN WITH: the lisa branch skipped (no value reaches the engine,
    which refuses)."""
    import pandas as pd
    c = _run(data, "counts", treatv="HighEdu", ks="200")
    e = _equipop(data, treat="HighEdu", k="200").df
    assert np.allclose(c.R_HighEdu_200, e.R_HighEdu_200, equal_nan=True)
    s = _run(data, "stats", valuesv="ValFloat", statss="mean", ks="200")
    assert "Mean_ValFloat_200" in s
    lisa = _run(data, "lisa", valuesv="ValFloat", ks="8", wperm=49)
    assert {"LISA_ValFloat_Ii", "LISA_ValFloat_quad",
            "LISA_ValFloat_p"} <= set(lisa.columns)
    assert set(lisa.LISA_ValFloat_quad.dropna()) <= {1.0, 2.0, 3.0, 4.0}
    f = _run(data, "friction", treatv="HighEdu", ks="200")
    assert {"N_200", "R_HighEdu_200", "Dist_200"} <= set(f.columns)
    sup = tmp_path / "supply.csv"
    pts = data.dropna(subset=["X_local"]).sample(30, random_state=1)
    pd.DataFrame({"x": pts.X_local, "y": pts.Y_local,
                  "supply": np.arange(1, 31)}).to_csv(sup, index=False)
    a = _run(data, "fca", demv="ValCount", supf=str(sup), hl=1000.0)
    assert {"A", "J"} <= set(a.columns) and a.A.notna().any()


# --------------------------------------------- what SSC will put on disk
def test_every_command_has_a_help_file_and_the_pkg_carries_both():
    """`help equipop_run` found nothing for as long as it shipped.

    BROKEN WITH: equipop_run.sthlp left out of equipop.pkg."""
    pkg = _text("equipop.pkg")
    listed = re.findall(r"^f (\S+)$", pkg, re.M)
    for f in listed:
        assert os.path.isfile(os.path.join(STATA, f)), f
    ados = sorted(f for f in os.listdir(STATA) if f.endswith(".ado"))
    assert len(ados) == 3
    for ado in ados:
        assert ado in listed, ado
        assert ado.replace(".ado", ".sthlp") in listed, ado


def test_every_help_file_is_current_versioned_and_says_who_to_ask():
    """BROKEN WITH: the author line without an address."""
    v = _version()
    for name in ("equipop.sthlp", "equipop_run.sthlp", "equipop_knn.sthlp"):
        h = _text(name)
        assert h.startswith("{smcl}\n{* *! version %s}" % v), name
        for i, line in enumerate(h.splitlines(), 1):
            assert line.count("{") == line.count("}"), (name, i, line)
        assert "johnosth@oslomet.no" in h, name
    assert "help regress" not in _text("equipop.sthlp")


def test_equipop_run_help_documents_every_option():
    """BROKEN WITH: wperm() left out of the lisa paragraph."""
    ado = _text("equipop_run.ado")
    syn = re.search(r"syntax\s*,(.*?)\n\n", ado, re.S).group(1)
    opts = {re.sub(r"[^A-Za-z]", "", o).lower()
            for o in re.findall(r"([A-Za-z]+)\s*(?:\(|\s|\]|$)", syn)}
    opts -= {"varname", "varlist", "numeric", "numlist", "integer",
             "string", "real"}
    h = _text("equipop_run.sthlp")
    for o in sorted(opts):
        assert re.search(r"\{(opt |cmd:)%s[\(\}]" % o, h), o


def test_the_do_files_name_no_old_release_and_no_anaconda_python():
    """The showcase announced itself as "EquiPop 1.46.4", and both
    do-files told users to point Stata at Anaconda - which the package
    description says closes Stata.

    BROKEN WITH: the showcase's old title line restored."""
    for name in ("equipop_showcase.do", "equipop_example.do"):
        t = _text(name)
        first = "\n".join(t.splitlines()[:3])
        assert not re.search(r"EquiPop \d+\.\d+", first), name
        assert not re.search(r'set exec ".*anaconda', t, re.I), name
        assert "equipop setup" in t, name
    assert not re.search(r'display .*EquiPop \d+\.\d+',
                         _text("equipop_showcase.do"))


def test_the_archives_are_built_from_the_pkg_list():
    """Two written lists in make_bundle.sh would have left the new
    help files out of both Stata archives.

    BROKEN WITH: the SSC copy back on a written list."""
    sh = open(os.path.join(ROOT, "tools", "make_bundle.sh"),
              encoding="utf-8").read()
    assert "sed -n 's/^f \\(.*\\)$/\\1/p' stata/equipop.pkg" in sh
    assert 'for f in $PKGFILES; do\n    cp "stata/$f" "$STAGE/ssc/"' in sh
    assert "stata/equipop_run.ado stata/equipop_showcase.do" not in sh
