# -*- coding: utf-8 -*-
"""test_describe.py - every result column says what it holds.

v1.56.0, BACKLOG 410. John's first live Pro run of the between/within
split: a table header of MLDb_ / MLDw_ / MLDsh_, <Null> in every
visible row, and nothing on screen to say what the columns were or
why they were empty.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
import io
import contextlib

import numpy as np
import pytest

from equipop.describe import describe, describe_all, legend
from equipop.stata_bridge import dispatch


def _quiet(fn, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        res = fn(*a, **kw)
    return res, out.getvalue()


# ---------------------------------------------- the describer itself
REQUESTS = [
    # (engine, k text, r text, tau, treat names, value fields, stats,
    #  decaying, efforting, decomposing)
    ("counts", "100 400", "500.5 800", "", ["LowInc", "born_1990"],
     [], [], False, False, False),
    ("counts", "50", "", "", ["g"], [], [], True, False, False),
    ("counts", "50", "", "3 4.5", ["g"], [], [], False, True, False),
    ("stats", "100 1600", "250.25", "", [], ["income_obs", "inc_2020"],
     ["mean", "median", "sd", "se", "var", "min", "max", "count", "sum",
      "range", "gini", "mld", "theil", "p1", "p2", "p10", "p97.5"],
     False, False, True),
]


@pytest.mark.parametrize("req", REQUESTS)
def test_every_column_a_door_can_predict_is_described(req):
    """THE TIE THAT KEEPS THE DESCRIBER HONEST. A door predicts its
    columns before it runs; every one of them must have a sentence.
    A family added to the predictor and not here fails this.

    BROKEN WITH: the "Var" family deleted from describe._VALUE."""
    from equipop.doors.fields import predict_result_fields
    eng, k, r, tau, treat, vals, stats, dec, eff, split = req
    names = predict_result_fields(eng, k, r, tau, treat, vals, stats,
                                  dec, eff, decomposing=split)
    fields = list(treat) + list(vals)
    missing = [n for n in names
               if not describe(n, fields=fields, split_by="cob",
                               min_group=30)]
    assert not missing, missing


def test_the_run_record_describes_what_it_used_to_call_undefined(
        tmp_path):
    """Measured before 410: the run record said "(no definition
    registered)" for 5 of 7 machine 1 columns - every T_ and R_ group
    column - and 12 of 19 machine 2 columns.

    BROKEN WITH: meta._describe_columns not consulting describe()."""
    from equipop.meta import record
    rng = np.random.default_rng(1)
    n = 300
    x, y = rng.uniform(0, 3000, n), rng.uniform(0, 3000, n)
    for eng, kw in (
        ("counts", dict(treat={"LowInc": rng.integers(0, 2, n)},
                        k_values=[100], r_values=[500.5])),
        ("stats", dict(k_values=[100],
                       values={"income_obs": rng.lognormal(10, .5, n)},
                       stats={"income_obs": ["mean", "p10", "var", "mld",
                                             "theil"]},
                       decompose_by={"cob": rng.integers(0, 2, n)})),
    ):
        log = record(eng, n, {})
        res, _ = _quiet(dispatch, eng, x, y, unit_size=100,
                        provenance=log, **kw)
        # THROUGH finalize(), where the record describes its columns.
        # The first version called set_output(columns) - whose first
        # argument is the DESTINATION - so the record held no columns
        # and "none undefined" was trivially true. Break-check said so.
        log.finalize(res, str(tmp_path / f"{eng}.csv"))
        cols = log.doc["columns"]
        assert set(cols) == set(res), "the record did not see the columns"
        blank = [c for c, v in cols.items() if "no definition" in v]
        assert not blank, (eng, blank)


def test_dist_says_map_units_and_no_longer_claims_zero():
    """The old record said Dist_k was "straight-line m ... (0 =
    satisfied within the origin cell)". Self-potential estimates it
    inside the cell since 1.29.5, and the unit is the map's (160).

    BROKEN WITH: the 1.55 sentence restored."""
    d = describe("Dist_400")
    assert "map units" in d and "(k=400)" in d
    assert "estimated inside the cell" in d
    assert "0 = satisfied" not in d


def test_a_name_is_split_by_the_fields_the_run_used():
    """A field may hold underscores and digits; a radius's decimal
    point is written as an underscore. Without context the SHORTEST
    field that leaves a valid suffix is taken; with the run's fields
    the split is exact.

    BROKEN WITH: a greedy field pattern `(.+)_` - Mean_inc_r500_5 then
    reads as field inc_r500 at k=5."""
    assert describe("Mean_inc_2020_100") == \
        "Mean of inc_2020 among the 100 nearest (k=100)"
    assert describe("Mean_inc_r500_5") == \
        "Mean of inc within 500.5 map units (r=500.5)"
    assert describe("Mean_inc_r500_5", fields=["inc_r500"]) == \
        "Mean of inc_r500 among the 5 nearest (k=5)"
    assert describe("R_born_1990_r800") == \
        "Share of born_1990 within 800 map units (r=800) (T / N)"


@pytest.mark.parametrize("name, said", [
    ("P1_v_10", "1st percentile"), ("P2_v_10", "2nd percentile"),
    ("P3_v_10", "3rd percentile"), ("P11_v_10", "11th percentile"),
    ("P21_v_10", "21st percentile"), ("P97_5_v_10", "97.5th percentile"),
])
def test_percentiles_read_as_people_say_them(name, said):
    """BROKEN WITH: every ordinal written "th"."""
    assert describe(name).startswith(said)


def test_a_name_equipop_does_not_write_gets_no_sentence():
    """A wrong alias is worse than none, so an unknown name is left
    undescribed rather than guessed.

    BROKEN WITH: _where() accepting any suffix."""
    for n in ("Population", "N_20b", "Mean_inc", "Dist_r500", "N_abc"):
        assert describe(n) is None, n
    assert describe_all(["N_100", "Population"]) == {
        "N_100": "Number counted among the 100 nearest (k=100)"}


def test_split_columns_say_why_they_can_be_empty():
    """The column that John saw empty must say why it can be.

    BROKEN WITH: min_group not carried into the context."""
    kw = {"values": {"inc": None}, "decompose_by": {"cob": None},
          "min_group": 12}
    d = describe_all(["MLDsh_inc_100", "Ng_inc_100"], kw)
    assert "only one group is present" in d["MLDsh_inc_100"]
    assert "fewer than 12 people" in d["MLDsh_inc_100"]
    assert "groups of cob" in d["MLDsh_inc_100"]
    assert "EMPTY" not in d["Ng_inc_100"]


def test_the_legend_has_one_line_per_kind_and_the_rule_once():
    """Ten k values must not make ten lines, and the emptiness rule
    must not be repeated on six lines in a row.

    BROKEN WITH: the rule not stripped from the family lines."""
    names = [f"{p}_inc_{k}" for k in (100, 400, 1600)
             for p in ("Nv", "MLD", "Ng", "NgMin", "MLDb", "MLDw",
                       "MLDsh")] + ["N_100", "N_400", "N_1600"]
    kw = {"values": {"inc": None}, "decompose_by": {"cob": None}}
    lines = legend(names, kw)
    body = [ln for ln in lines if ln.startswith("  ")]
    assert len([ln for ln in body if "_inc_" in ln
                or ln.lstrip().startswith("N_")]) == 8
    assert "\n".join(lines).count("EMPTY") == 1
    assert "fewer than 30 people" in lines[-1]


# ------------------------------------------------ the run's messages
def test_both_machines_print_the_legend():
    """Printed by dispatch, so every door that relays the engine's
    voice says it in the same words.

    BROKEN WITH: the _say_columns call removed from the counts branch."""
    rng = np.random.default_rng(2)
    x, y = rng.uniform(0, 1000, 100), rng.uniform(0, 1000, 100)
    _, said = _quiet(dispatch, "counts", x, y, unit_size=100,
                     treat={"g": rng.integers(0, 2, 100)}, k_values=[20])
    assert "[columns]" in said and "R_g_20" in said
    _, said = _quiet(dispatch, "stats", x, y, unit_size=100,
                     k_values=[20], values={"v": rng.lognormal(3, .4, 100)},
                     stats={"v": ["mean"]})
    assert "[columns]" in said and "Mean_v_20" in said


def test_a_legend_that_fails_never_fails_the_run(monkeypatch):
    """The numbers are computed before the legend is written; losing
    the explanation must not lose them. And it must SAY it failed: a
    silent except is how a feature here once became unreachable.

    BROKEN WITH: the try around legend() removed."""
    import equipop.describe as D

    def boom(*a, **k):
        raise RuntimeError("describer down")
    monkeypatch.setattr(D, "legend", boom)
    rng = np.random.default_rng(3)
    x, y = rng.uniform(0, 1000, 60), rng.uniform(0, 1000, 60)
    res, said = _quiet(dispatch, "counts", x, y, unit_size=100,
                       treat={"g": rng.integers(0, 2, 60)}, k_values=[10])
    assert "R_g_10" in res
    assert "could not be written" in said and "describer down" in said


def test_the_summary_counts_rows_and_says_why():
    """Four places, eighty people each, every one its own neighbourhood
    at k=80, laid out so each reason occurs exactly once:
      A - 80 born in Sweden                -> only one group present
      B - 70 Sweden, 10 abroad             -> a group below 30 people
      C - 40 and 40                        -> reported
      D - 80 people with no income at all  -> nobody with a value
    Counted in ROWS, which is what the table shows.

    BROKEN WITH: `ng == 1` written `ng < 2`, which counts the people
    with no value twice - as one group AND as nobody."""
    n = 80
    xs = np.repeat([50.0, 20050.0, 40050.0, 60050.0], n)
    ys = np.full(4 * n, 50.0)
    cob = np.array(["Sweden"] * n + ["Sweden"] * 70 + ["abroad"] * 10
                   + ["Sweden"] * 40 + ["abroad"] * 40
                   + ["Sweden"] * 40 + ["abroad"] * 40, dtype=object)
    rng = np.random.default_rng(4)
    inc = rng.lognormal(10, .5, 4 * n)
    inc[3 * n:] = np.nan
    _, said = _quiet(dispatch, "stats", xs, ys, unit_size=100,
                     k_values=[n], values={"inc": inc},
                     stats={"inc": ["mld"]}, decompose_by={"cob": cob})
    line = [ln for ln in said.splitlines()
            if ln.startswith("[decompose] inc, k=80")]
    assert line == ["[decompose] inc, k=80: split reported in 80 of 320 "
                    "places; empty in 240 - only one group present: 80; "
                    "a group below 30 people: 80; nobody with a value: "
                    "80."], said
