# -*- coding: utf-8 -*-
"""test_manual_split.py - the manual's chapter on the between/within
split is the code's own answer.

v1.57.0. The external reviewer of 1.55.0 asked for a manual chapter
with one worked neighbourhood (BACKLOG 407). It is MANUAL_TOPICS.md
section 10, and every number it prints is read FROM the chapter here
and checked against a run, to the digits printed - so a number changed
in either place, the text or the code, fails this file.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
import io
import re
import pathlib
import contextlib

import numpy as np
import pytest

from equipop.stata_bridge import dispatch

ROOT = pathlib.Path(__file__).resolve().parents[1]
HEAD = "## 10. Inequality between and within groups"


def _chapter() -> str:
    text = (ROOT / "MANUAL_TOPICS.md").read_text(encoding="utf-8")
    assert text.count(HEAD) == 1, "the chapter's heading moved"
    return text.split(HEAD, 1)[1].split("\n## ", 1)[0]


def _quiet(fn, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        res = fn(*a, **kw)
    return res, out.getvalue()


def _close(value, printed: str) -> bool:
    """`value` rounds to `printed`, at the digits printed."""
    dec = len(printed.split(".")[1]) if "." in printed else 0
    return abs(float(value) - float(printed)) <= 0.5 * 10 ** -dec + 1e-12


def test_the_worked_neighbourhood_is_the_codes_answer():
    """The chapter's Python block is RUN as printed, and each row of
    its table must be that run's number. So must the sums and the two
    shares the bullets quote.

    BROKEN WITH: the manual's MLDw_ written 0.0791, a transposition."""
    ch = _chapter()
    code = re.findall(r"```python\n(.*?)```", ch, re.S)
    assert len(code) == 1
    ns: dict = {}
    _quiet(exec, code[0], ns)
    res = ns["res"]
    rows = re.findall(r"^\| `(\w+)` \| ([\d.]+) \|", ch, re.M)
    assert len(rows) == 12, rows
    got = {c: float(res[c][0]) for c, _ in rows}
    bad = [(c, t, got[c]) for c, t in rows if not _close(got[c], t)]
    assert not bad, bad
    printed = dict(rows)
    for a, b, tot in re.findall(r"(\d\.\d{4}) \+ (\d\.\d{4}) = (\d\.\d{4})",
                                ch):
        assert abs(float(a) + float(b) - float(tot)) < 1.5e-4
        assert tot in (printed["MLD_income_4"], printed["Theil_income_4"])
    shares = re.findall(r"(\d+)% and (\d+)% here", ch)
    assert shares == [(str(round(100 * got["MLDsh_income_4"])),
                       str(round(100 * got["Theilsh_income_4"])))]


def _town():
    """5,000 people; one in five born abroad, concentrated towards the
    eastern edge; 3% with no country recorded."""
    rng = np.random.default_rng(2026)
    n = 5000
    x, y = rng.uniform(0, 5000, n), rng.uniform(0, 5000, n)
    p_abroad = 0.02 + 0.6 / (1 + np.exp(-(x - 3500) / 300))
    cob = np.where(rng.random(n) < p_abroad, "abroad", "Sweden")
    cob = cob.astype(object)
    inc = rng.lognormal(10, 0.5, n) * np.where(cob == "abroad", 0.8, 1.0)
    cob[rng.random(n) < 0.03] = None
    return x, y, cob, inc


@pytest.fixture(scope="module")
def town_run():
    x, y, cob, inc = _town()
    res, said = _quiet(dispatch, "stats", x, y, unit_size=100,
                       k_values=[100, 400, 1600], values={"income": inc},
                       stats={"income": ["mld"]},
                       decompose_by={"cob": cob})
    return cob, res, said


def test_the_town_is_the_one_the_chapter_describes(town_run):
    """The prose's own claims about the town - so the description
    cannot drift from the data under it.

    BROKEN WITH: the 3% of unrecorded countries dropped from _town()
    (the chapter's run line then no longer appears)."""
    cob, res, said = town_run
    ch = _chapter()
    assert "5,000 people, one in five" in ch and "with 3% whose" in ch
    assert len(res["N_100"]) == 5000
    assert 0.18 <= np.mean(cob == "abroad") <= 0.22
    assert 0.025 <= np.mean([c is None for c in cob]) <= 0.035
    quoted = re.findall(r"^(\[decompose\] income, k=100: .*)$", ch, re.M)
    assert len(quoted) == 1 and quoted[0] in said.splitlines(), quoted


def test_the_empty_area_shrinks_as_the_chapter_says(town_run):
    """Each row of the chapter's table - the share a group must reach
    (30 / k), and the places empty for each reason - from the run.

    BROKEN WITH: the k=400 row's empty count written 2,529; and the
    k=1,600 share written 1.8% - 30/1,600 is 1.875. (Written 2% it
    PASSES, rightly: 1.875 rounds to 2 at the digits printed. The
    first break-check of this claimed otherwise.)"""
    _, res, _ = town_run
    rows = re.findall(r"^\| ([\d,]+) \| ([\d.]+)% \| ([\d,]+) \| ([\d,]+) "
                      r"\| ([\d,]+) \|$", _chapter(), re.M)
    assert [r[0] for r in rows] == ["100", "400", "1,600"]
    for k_txt, pct, empty, one, small in rows:
        k = int(k_txt.replace(",", ""))
        assert _close(100 * 30 / k, pct), (k, pct)
        ng = np.asarray(res[f"Ng_income_{k}"], float)
        ngmin = np.asarray(res[f"NgMin_income_{k}"], float)
        b = np.asarray(res[f"MLDb_income_{k}"], float)
        assert (ng > 0).all()                     # nobody-with-a-value: none
        assert int((~np.isfinite(b)).sum()) == int(empty.replace(",", ""))
        assert int((ng == 1).sum()) == int(one.replace(",", ""))
        assert int(((ng >= 2) & (ngmin < 30)).sum()) == \
            int(small.replace(",", ""))
