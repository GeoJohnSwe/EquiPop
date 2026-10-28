# -*- coding: utf-8 -*-
"""The segregation profile at k: whose neighbourhoods, weighted how
(v1.63.0, BACKLOG 443).

Until 1.62.1 each origin CELL's neighbourhood weighed the same (about
k people) while the reference share P counted PEOPLE. On the Stata
test data tertiary-educated people live 24% in the sparser cells and
17% in the densest quarter, so the cells averaged 21% against P = 19%,
and the entropy and Atkinson indices - bounded at zero only against the
units' own average - went negative: H -0.020, -0.029, -0.027.

John's ruling, 26 October 2026: every person's neighbourhood counts
once (the default), with "every place counts once" kept as a choice;
both measured against their units' own weighted mean.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import contextlib
import io
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))

from equipop.segregation import (seg_indices, seg_indices_at_scale,  # noqa: E402
                                 seg_profile)

K = [50, 200, 800]


@pytest.fixture(scope="module")
def run():
    import stata_sim as SS
    from equipop.cells import build_cells
    from equipop.fastcounts import run_knn_counts
    df = SS.load_test_data().dropna(subset=["X_local", "Y_local"])
    with contextlib.redirect_stdout(io.StringIO()):
        cd = build_cells(df, "X_local", "Y_local", binary_vars=["HighEdu"],
                         unit_size=100)
        return run_knn_counts(cd, K, m_neighbors=4096)


def _profile(out, weighting):
    with contextlib.redirect_stdout(io.StringIO()):
        return seg_profile(out, K, n_col="N_{k}", t_col="T_HighEdu_{k}",
                           local_all="N_local", local_grp="HighEdu_local",
                           weighting=weighting)


@pytest.mark.parametrize("weighting", ["people", "cells"])
def test_no_index_goes_below_zero(run, weighting):
    """BROKEN WITH: the reference share back to the global P - under
    "cells" (H and Atkinson negative again, as in 1.62.1). Under
    "people" the test data's mean share at k stays within 0.01 of P,
    so this data cannot show that break; the uniform-town test below
    does."""
    prof = _profile(run, weighting)
    for c in ("D", "Gini", "H", "Atkinson_0.5"):
        assert (prof[c] >= -1e-12).all(), (c, prof[c].tolist())
    assert prof.attrs["weighting"] == weighting


def test_people_is_the_default_and_counts_people(run):
    """The people-weighted mean share at k stays near P; the cells'
    does not - which is the whole finding.

    BROKEN WITH: weighting defaulting to "cells"."""
    with contextlib.redirect_stdout(io.StringIO()):
        prof = seg_profile(run, K, n_col="N_{k}", t_col="T_HighEdu_{k}",
                           local_all="N_local", local_grp="HighEdu_local")
    P = prof.attrs["global_share_P"]
    k = prof[prof.scale != "local"]
    assert (abs(k.P_ref - P) < 0.01).all()
    cells = _profile(run, "cells")
    ck = cells[cells.scale != "local"]
    assert (ck.P_ref - P > 0.01).all()       # 0.21 against 0.19


def test_isolation_at_k_is_SI_when_people_count(run):
    """Every person's neighbourhood once: isolation averages over the
    group's own members, which is the 2015 paper's SI.

    BROKEN WITH: the exposure weights left as the neighbourhoods'
    group counts under "people"."""
    prof = _profile(run, "people")
    assert np.allclose(prof.Isolation, prof.SI, rtol=1e-12)


def test_SI_does_not_depend_on_the_weighting(run):
    """SI was right all along; the change must not touch it.

    BROKEN WITH: SI weighted by the units' weights."""
    a, b = _profile(run, "people"), _profile(run, "cells")
    assert np.allclose(a.SI, b.SI, rtol=1e-12)
    assert np.allclose(a.SI.round(4), [.4036, .2216, .2002, .1930])


def test_the_local_row_is_the_classical_partition(run):
    """The cells themselves partition the people: nothing moves there.

    BROKEN WITH: the local row computed with the k-scale weights."""
    la, lg = run.N_local.to_numpy(float), run.HighEdu_local.to_numpy(float)
    P = lg.sum() / la.sum()
    want = seg_indices_at_scale(la, lg, P)
    for w in ("people", "cells"):
        row = _profile(run, w).iloc[0]
        for key, v in want.items():
            assert row[key] == pytest.approx(v, rel=1e-12), (w, key)


def test_random_units_are_never_below_zero():
    """Against the units' own weighted mean, H and Atkinson cannot go
    negative - whatever the weights. Half the draws tie the weights to
    the shares (w = e^(8p)), so the weighted mean is far from the plain
    one: weights that are merely random leave them close, and a formula
    that drops the weights then passes anyway (the 1.63.0 break-check
    found exactly that).

    BROKEN WITH: Atkinson's inner sum taken without the weights."""
    rng = np.random.default_rng(3)
    for i in range(200):
        n = rng.integers(5, 60)
        p = rng.uniform(0, 1, n)
        w = (np.exp(8 * p) if i % 2 else rng.uniform(0.1, 50, n))
        P = float(np.sum(w * p) / w.sum())
        r = seg_indices(w, p, w * p, P)
        assert r["H"] >= -1e-12 and r["Atkinson_0.5"] >= -1e-12, i


def test_a_unit_of_weight_two_is_two_units_of_weight_one():
    """Weights mean what they say: every index is the same whether a
    place of two people is entered once with weight 2 or twice with
    weight 1.

    BROKEN WITH: Atkinson's inner sum taken without the weights."""
    w2, p2 = np.array([2.0, 1.0, 3.0]), np.array([.7, .1, .4])
    w1 = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    p1 = np.array([.7, .7, .1, .4, .4, .4])
    P = float(np.sum(w2 * p2) / w2.sum())
    a = seg_indices(w2, p2, w2 * p2, P)
    b = seg_indices(w1, p1, w1 * p1, P)
    for key in a:
        assert a[key] == pytest.approx(b[key], rel=1e-12), key


@pytest.mark.parametrize("weighting", ["people", "cells"])
def test_a_town_mixed_alike_everywhere_has_no_segregation(weighting):
    """If every neighbourhood at k has the same share, there is no
    segregation at k, whatever the cells hold locally: every evenness
    index is 0. One person of the group lives alone; 99 others live
    together; at k everyone sees half and half.

    BROKEN WITH: the reference share back to the global P (P = 0.01
    against the 0.5 everybody sees: D far above 1, H far below 0)."""
    out = pd.DataFrame({"N_local": [1.0, 99.0], "G_local": [1.0, 0.0],
                        "N_10": [10.0, 10.0], "T_G_10": [5.0, 5.0]})
    with contextlib.redirect_stdout(io.StringIO()):
        prof = seg_profile(out, [10], n_col="N_{k}", t_col="T_G_{k}",
                           local_all="N_local", local_grp="G_local",
                           weighting=weighting)
    row = prof[prof.scale == 10].iloc[0]
    assert row.P_ref == pytest.approx(0.5)
    for c in ("D", "Gini", "H", "Atkinson_0.5"):
        assert row[c] == pytest.approx(0.0, abs=1e-9), c


def test_an_unknown_weighting_is_refused(run):
    """BROKEN WITH: the check removed (anything not "people" ran as
    cells)."""
    with pytest.raises(ValueError, match="people, cells"):
        _profile(run, "persons")


# ===================================================================
# The review of 1.63.0 (BACKLOG 448-450, 452)
# ===================================================================

def _small(df, k=(10,), weighting="people"):
    with contextlib.redirect_stdout(io.StringIO()):
        return seg_profile(df, list(k), n_col="N_{k}", t_col="T_{k}",
                           local_all="la", local_grp="lg",
                           weighting=weighting)


def test_cells_counts_every_place_once():
    """Review P1, worked by hand. Two places whose neighbourhoods hold
    20% and 80% of the group, one neighbourhood of 10 people and one of
    1,000. Every place once: P_ref = 0.5, D = 0.6, H = 1 - e(0.2)/ln 2
    = 0.2781, isolation = (0.2^2 + 0.8^2) / (0.2 + 0.8) = 0.68. 1.63.0
    weighted by the neighbourhood's size and gave P_ref 0.7941, D 0.0360
    and H 0.0160 under the same name.

    BROKEN WITH: "cells" weighted by N_k again (1.63.0)."""
    df = pd.DataFrame({"la": [10.0, 10.0], "lg": [5.0, 5.0],
                       "N_10": [10.0, 1000.0], "T_10": [2.0, 800.0]})
    r = _small(df, weighting="cells").iloc[1]
    e2 = 0.2 * np.log(5) + 0.8 * np.log(1.25)
    assert r.P_ref == pytest.approx(0.5, abs=1e-12)
    assert r.D == pytest.approx(0.6, abs=1e-12)
    assert r.H == pytest.approx(1 - e2 / np.log(2), abs=1e-12)
    assert r.Isolation == pytest.approx(0.68, abs=1e-12)


def test_cells_did_not_move_where_every_neighbourhood_holds_k(run):
    """Under the default proportional overshoot every N_k is exactly k,
    so 1.63.0's size weights were equal weights, and its "cells" numbers
    stand: the fix changes that option only under whole or sampled
    overshoot, where N_k varies.

    BROKEN WITH: "cells" weighted by the people living in the origin."""
    from equipop.segregation import seg_indices as si
    prof = _profile(run, "cells")
    for k in K:
        t = run[f"N_{k}"].to_numpy(float)
        x = run[f"T_HighEdu_{k}"].to_numpy(float)
        assert np.allclose(t, k, rtol=1e-12)
        p = x / t
        ref = si(t, p, x, float(np.sum(t * p) / t.sum()))
        row = prof[prof.scale == k].iloc[0]
        for key, v in ref.items():
            assert row[key] == pytest.approx(v, rel=1e-9, abs=1e-12), \
                (k, key)


_BAD = {
    "nobody in the group": ({"lg": [0.0, 0.0], "T_10": [0.0, 0.0]},
                            "nobody belongs"),
    "everybody in the group": ({"lg": [10.0, 10.0], "T_10": [10.0, 10.0]},
                               "everybody belongs"),
    "nobody at all": ({"la": [0.0, 0.0], "lg": [0.0, 0.0]},
                      "nobody lives"),
    "group above total": ({"lg": [12.0, 3.0]}, "exceeds"),
    "negative people": ({"la": [10.0, -10.0]}, "negative"),
    "missing local count": ({"la": [10.0, np.nan]}, "missing values"),
    "infinite count": ({"la": [10.0, np.inf]}, "infinite"),
    "text for a count": ({"la": ["10", "ten"]}, "not numeric"),
    "group above total at k": ({"T_10": [11.0, 2.0]}, "scale 10"),
    "negative N_k": ({"N_10": [-10.0, 10.0]}, "negative"),
}


@pytest.mark.parametrize("case", sorted(_BAD))
def test_impossible_or_undefined_input_is_refused_in_words(case):
    """Review P2: no group gave warnings and NaN rows; everybody in the
    group a ZeroDivisionError; no people warnings and NaN; a group above
    its total, negative and missing counts went through. Each is now a
    SegregationError naming the problem - and nothing on the way warns.

    BROKEN WITH: the 0 < P < 1 check removed (the first three), the
    group-above-total check removed, the negative check removed."""
    import warnings
    from equipop.segregation import SegregationError
    base = {"la": [10.0, 10.0], "lg": [5.0, 2.0], "N_10": [10.0, 10.0],
            "T_10": [5.0, 3.0]}
    change, words = _BAD[case]
    df = pd.DataFrame({**base, **change})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(SegregationError, match=words):
            _small(df)


def test_a_missing_column_is_named():
    """BROKEN WITH: the column check removed (a KeyError from pandas)."""
    from equipop.segregation import SegregationError
    df = pd.DataFrame({"la": [10.0], "lg": [5.0], "N_10": [10.0]})
    with pytest.raises(SegregationError, match="no column T_10"):
        _small(df)


def test_a_scale_with_nothing_to_compare_is_an_empty_row_that_says_so():
    """Defined overall, undefined at k: every neighbourhood at k holds
    none of the group (possible with the origin excluded). The row is
    there, empty, with the reason - no warning, no error.

    BROKEN WITH: the per-scale 0 < P_ref < 1 check removed."""
    import warnings
    df = pd.DataFrame({"la": [10.0, 10.0], "lg": [5.0, 0.0],
                       "N_10": [10.0, 10.0], "T_10": [0.0, 0.0]})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        row = _small(df).iloc[1]
    assert np.isnan(row.D) and np.isnan(row.H) and np.isnan(row.SI)
    assert "none" in row.note


@pytest.mark.parametrize("weighting", ["people", "cells"])
def test_an_origin_without_a_neighbourhood_is_left_out_of_everything(
        weighting):
    """Review P2, reproduced: two origins of 10 people, 5 of the group
    each; one has a half-and-half neighbourhood, the other none
    (N_k = 0). Isolation said 0.50 and SI 0.25 - SI kept the second
    origin's five in its denominator. Now both leave it out, and the
    row says who was left out.

    BROKEN WITH: SI's denominator over every origin again."""
    df = pd.DataFrame({"la": [10.0, 10.0], "lg": [5.0, 5.0],
                       "N_10": [10.0, 0.0], "T_10": [5.0, 0.0]})
    row = _small(df, weighting=weighting).iloc[1]
    assert row.SI == pytest.approx(0.5)
    if weighting == "people":
        assert row.Isolation == pytest.approx(row.SI, rel=1e-12)
    assert (row.valid_origins, row.valid_people, row.excluded_people) \
        == (1, 10.0, 10.0)
    assert "left out" in row.note


def test_a_shared_csv_says_what_it_describes(run, tmp_path):
    """Review P2: the weighting lived only in DataFrame.attrs, which a
    CSV drops - and the showcase writes a CSV. Every row now carries it.

    BROKEN WITH: the weighting and global_share_P columns left out of
    the rows (attrs only, as in 1.63.0)."""
    for w in ("people", "cells"):
        p = tmp_path / f"prof_{w}.csv"
        _profile(run, w).to_csv(p, index=False)
        back = pd.read_csv(p)
        assert (back.weighting == w).all()
        assert np.allclose(back.global_share_P, back.P_ref.iloc[0])
        for c in ("valid_origins", "valid_people", "excluded_people",
                  "note"):
            assert c in back.columns, c
        assert (back.excluded_people == 0).all()
