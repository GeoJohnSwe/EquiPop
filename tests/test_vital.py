# -*- coding: utf-8 -*-
"""test_vital.py - life expectancy, TFR, CBR and CDR read from one age
pyramid against the nation's (v1.60.0, BACKLOG 416).

THE TRUTH IS BUILT, NOT ASSUMED. Each test makes a population whose
life table and fertility are KNOWN - Kenya's and Sweden's 2020
schedules from the shipped WPP 2024 table, changed where the test
says - lets it reach the age pyramid those rates produce, and asks the
estimators to find the rates again from the pyramid alone.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import numpy as np
import pytest

from equipop.doors import vital as V

KEN, SWE, YEAR = "KEN", "SWE", 2020
PF = 0.488                       # share of births that are girls


# ------------------------------------------------- building the truth
def widths(bands):
    return [b2 - b1 for b1, b2 in zip(bands, bands[1:])] + [10]


def band_table(m, bands):
    """l at band starts and L per band from band death rates - the same
    rules the estimators assume (half the band lived by those dying;
    the open band lives l/m)."""
    l, L, cur = [], [], 1.0
    for j, n in enumerate(widths(bands)):
        l.append(cur)
        if j == len(bands) - 1:
            L.append(cur / m[j])
            break
        q = min(n * m[j] / (1 + n / 2 * m[j]), 1.0)
        nxt = cur * (1 - q)
        L.append(n / 2 * (cur + nxt))
        cur = nxt
    return np.array(l), np.array(L)


def mids(bands):
    return np.array([b + n / 2 for b, n in zip(bands, widths(bands))])


def stable(L, r, bands):
    """People by band in a population whose births grow at r a year,
    one birth a year now: a cohort aged x was born e^(-r x) as large."""
    return L * np.exp(-r * mids(bands))


def lotka_r(L_f, f, bands):
    """The growth rate the fertility and female survival imply."""
    women = L_f[bands.index(10):bands.index(50) + 1]
    m = mids(bands)[bands.index(10):bands.index(50) + 1]

    def net(r):
        return (PF * women * np.exp(-r * m) * f).sum() - 1
    lo, hi = -0.1, 0.1
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if net(mid) > 0 else (lo, mid)
    return (lo + hi) / 2


def true_e(l, L, start):
    return L[start:].sum() / l[start]


@pytest.fixture(scope="module")
def ken():
    nat = V.national(KEN, YEAR, "B")
    l, L = band_table(nat["m"], nat["bands"])
    fem = V.national(KEN, YEAR, "F")
    lf, Lf = band_table(fem["m"], fem["bands"])
    return {"nat": nat, "l": l, "L": L, "Lf": Lf, "bands": nat["bands"]}


# ------------------------------------------------- the reference table
def test_the_reference_is_wpp_and_says_so():
    """Sweden's both-sexes e0 and TFR as WPP 2024 gives them. (The
    builder itself refuses to write a table whose life tables miss
    WPP's own e0 by more than 0.25 years.)

    BROKEN WITH: national() reading the men's table whatever sex is
    asked for."""
    df, meta = V.reference()
    assert "World Population Prospects 2024" in meta["source"]
    assert "3.0 IGO" in meta["licence"]
    assert meta["countries"] >= 230
    worst = float(meta["check"].split(":")[1].split("years")[0])
    assert worst <= 0.25
    swe = V.national(SWE, YEAR, "B")
    assert 82 < swe["L"].sum() < 84         # Sweden 2020: about 82.4
    assert 1.6 < V.national(SWE, YEAR, "F")["tfr"] < 1.75


def test_an_older_folders_top_band_takes_everyone_above_it():
    """The 2000-2020 series ends at 80+: the reference's 85 and 90+ are
    folded into it, so no person-years go missing.

    BROKEN WITH: the open band taking only its own L."""
    at90 = V.national(KEN, 2010, "B", top=90)
    at80 = V.national(KEN, 2010, "B", top=80)
    assert at80["bands"][-1] == 80
    assert at80["L"].sum() == pytest.approx(at90["L"].sum(), rel=1e-12)


def test_a_year_or_country_it_lacks_is_refused_in_words():
    """BROKEN WITH: the year check removed (a KeyError comes instead)."""
    with pytest.raises(V.VitalError, match="covers 2000-2030"):
        V.national(KEN, 1990, "B")
    with pytest.raises(V.VitalError, match="No national life table"):
        V.national("ZZZ", YEAR, "B")


# --------------------------------------------------- life expectancy
def test_the_nation_read_against_itself_is_the_nation(ken):
    """BROKEN WITH: the national share left out of rho."""
    P = stable(ken["L"], 0.022, ken["bands"])
    for a in (0, 30, 50, 60):
        i = ken["bands"].index(a)
        e = V.life_expectancy(P[None, :], P, ken["l"], ken["L"], i)[0]
        assert e == pytest.approx(true_e(ken["l"], ken["L"], i), rel=1e-9)


def test_a_district_with_worse_mortality_is_found(ken):
    """Death rates 40 % higher at every age, the same birth history as
    the nation: e60 is found to within half a year, and so - here - is
    e0, because nothing but mortality differs.

    BROKEN WITH: the estimator returning the national e(a)."""
    bands = ken["bands"]
    lw, Lw = band_table(ken["nat"]["m"] * 1.4, bands)
    P_nat = stable(ken["L"], 0.022, bands)
    P_loc = stable(Lw, 0.022, bands)
    for a, tol in ((60, 0.5), (0, 1.5)):
        i = bands.index(a)
        got = V.life_expectancy(P_loc[None, :], P_nat, ken["l"],
                                ken["L"], i)[0]
        want = true_e(lw, Lw, i)
        assert abs(got - want) < tol, (a, got, want)
        assert got < true_e(ken["l"], ken["L"], i) - 1


def test_e60_holds_where_growth_differs_and_e0_does_not(ken):
    """WHY e0, e30 AND e50 ARE CALLED UNRELIABLE. National mortality,
    births growing 3.0 % a year against the nation's 2.2 %: e60 stays
    within two years; e0 is out by more than ten.

    BROKEN WITH: the shares normalised at birth whatever the start
    age."""
    bands = ken["bands"]
    P_nat = stable(ken["L"], 0.022, bands)
    P_loc = stable(ken["L"], 0.030, bands)
    i60, i0 = bands.index(60), 0
    e60 = V.life_expectancy(P_loc[None, :], P_nat, ken["l"], ken["L"],
                            i60)[0]
    e0 = V.life_expectancy(P_loc[None, :], P_nat, ken["l"], ken["L"],
                           i0)[0]
    assert abs(e60 - true_e(ken["l"], ken["L"], i60)) < 2
    assert abs(e0 - true_e(ken["l"], ken["L"], i0)) > 10


def test_young_in_migrants_do_not_move_e60(ken):
    """A city drawing people aged 15-34. e60 is untouched.

    BROKEN WITH: the shares normalised on the whole population instead
    of the start band."""
    bands = ken["bands"]
    P_nat = stable(ken["L"], 0.022, bands)
    mig = np.array([1.35 if 15 <= b < 35 else 1.0 for b in bands])
    i60 = bands.index(60)
    e60 = V.life_expectancy((P_nat * mig)[None, :], P_nat, ken["l"],
                            ken["L"], i60)[0]
    assert e60 == pytest.approx(true_e(ken["l"], ken["L"], i60),
                                abs=1e-9)


def test_no_answer_is_nan_never_infinite(ken):
    """Two ways a neighbourhood has no answer: nobody aged 60-64 in it,
    or a band its NATION has nobody in (a neighbourhood at a border can
    take in people from next door). Both give NaN - an infinite life
    expectancy would pass every later step as a number.

    BROKEN WITH: the non-finite guard removed."""
    bands = ken["bands"]
    P = stable(ken["L"], 0.022, bands)
    i60 = bands.index(60)
    S = P.copy()
    S[i60] = 0
    e = V.life_expectancy(S[None, :], P, ken["l"], ken["L"], i60)
    assert np.isnan(e[0])
    P_hole = P.copy()
    P_hole[bands.index(90)] = 0
    e = V.life_expectancy(P[None, :], P_hole, ken["l"], ken["L"], i60)
    assert np.isnan(e[0])


# --------------------------------------------------------- fertility
def _fertile(ken, lam):
    """A population whose rates are lam x Kenya's, at the growth those
    rates and Kenya's survival imply. One birth a year now."""
    bands = ken["bands"]
    f = ken["nat"]["f"] * lam
    r = lotka_r(ken["Lf"], f, bands)
    P = stable(ken["L"], r, bands)
    women = PF * stable(ken["Lf"], r, bands)
    W = women[bands.index(10):bands.index(50) + 1]
    C = P[0] + P[1]
    births = (W * f).sum()
    return {"P": P, "W": W, "C": C, "N": P.sum(), "births": births,
            "tfr": 5 * f.sum(), "r": r}


def test_the_nation_gives_back_its_own_tfr_and_cbr(ken):
    """BROKEN WITH: TFR read absolutely (no division by the nation's
    own children per expected birth)."""
    nat = _fertile(ken, 1.0)
    f = ken["nat"]["f"]
    tfr, cbr = V.fertility([nat["C"]], [nat["W"]], [nat["N"]], f,
                           ken["nat"]["tfr"], nat["C"], nat["W"])
    assert tfr[0] == pytest.approx(ken["nat"]["tfr"], rel=1e-9)
    assert cbr[0] == pytest.approx(1000 * nat["births"] / nat["N"],
                                   rel=1e-9)


@pytest.mark.parametrize("lam", [0.7, 1.3])
def test_higher_and_lower_fertility_are_found(ken, lam):
    """Rates 30 % above or below Kenya's, with the growth they imply:
    TFR and CBR found to within 4 %.

    BROKEN WITH: the women weighted equally instead of by the national
    schedule."""
    nat = _fertile(ken, 1.0)
    loc = _fertile(ken, lam)
    f = ken["nat"]["f"]
    tfr, cbr = V.fertility([loc["C"]], [loc["W"]], [loc["N"]], f,
                           ken["nat"]["tfr"], nat["C"], nat["W"])
    assert tfr[0] == pytest.approx(loc["tfr"], rel=0.04)
    assert cbr[0] == pytest.approx(1000 * loc["births"] / loc["N"],
                                   rel=0.04)


def test_young_women_count_more_than_old_ones(ken):
    """The same number of women, all aged 25-29 or all aged 45-49, with
    the same children: the older group implies the higher TFR, because
    women of 45 have few births to show.

    BROKEN WITH: the women weighted equally instead of by the national
    schedule."""
    nat = _fertile(ken, 1.0)
    f = ken["nat"]["f"]
    young = np.zeros(9)
    young[3] = 1000
    old = np.zeros(9)
    old[7] = 1000
    tfr, _ = V.fertility([300, 300], [young, old], [5000, 5000], f,
                         ken["nat"]["tfr"], nat["C"], nat["W"])
    assert tfr[1] > 3 * tfr[0]


# -------------------------------------------------------- death rate
def test_cdr_follows_old_age_mortality(ken):
    """Death rates from 60 half again the nation's, the same births:
    CDR found to within 3 %, and higher than the nation's.

    BROKEN WITH: theta fixed at 1 (national rates at every age)."""
    bands = ken["bands"]
    i60 = bands.index(60)
    m_loc = ken["nat"]["m"].copy()
    m_loc[i60:] *= 1.5
    lw, Lw = band_table(m_loc, bands)
    P_nat = stable(ken["L"], 0.022, bands)
    P_loc = stable(Lw, 0.022, bands)
    nat = dict(ken["nat"], m=np.array(ken["nat"]["m"]))
    e60 = V.life_expectancy(P_loc[None, :], P_nat, ken["l"], ken["L"],
                            i60)
    e60_nat = true_e(ken["l"], ken["L"], i60)
    cdr = V.crude_death_rate(P_loc[None, :], [P_loc.sum()], nat, e60,
                             e60_nat)[0]
    truth = 1000 * (P_loc * m_loc).sum() / P_loc.sum()
    national = 1000 * (P_nat * ken["nat"]["m"]).sum() / P_nat.sum()
    assert cdr == pytest.approx(truth, rel=0.03)
    assert cdr > national


def test_cdr_of_the_nation_is_the_nations(ken):
    """The nation's own neighbourhood gets the nation's death rates at
    every age: theta comes out 1.

    BROKEN WITH: the bisection turned the wrong way (theta then runs to
    the end of its bracket)."""
    bands = ken["bands"]
    i60 = bands.index(60)
    P = stable(ken["L"], 0.022, bands)
    e60 = true_e(ken["l"], ken["L"], i60)
    cdr = V.crude_death_rate(P[None, :], [P.sum()], ken["nat"], [e60],
                             e60)[0]
    assert cdr == pytest.approx(
        1000 * (P * ken["nat"]["m"]).sum() / P.sum(), rel=1e-4)


def test_the_unreliable_ones_say_so_in_their_names():
    """John's ruling: e50, e30 and e0 are computed AND FLAGGED.

    BROKEN WITH: e0's code without its 'u'."""
    for name, mm in V.MEASURES.items():
        if name.startswith("life_expectancy") and name != \
                "life_expectancy_60":
            assert not mm["reliable"]
            assert mm["code"].endswith("u")
            assert "UNRELIABLE" in mm["label"]
        else:
            assert mm["reliable"]
        assert len(f"{mm['code']}_10000") <= 10      # shapefile names
