# -*- coding: utf-8 -*-
"""theta(k) - the scale profile of inequality of opportunity by
neighbourhood type (v1.62.0, BACKLOG 405 step 4 and 436).

A synthetic town with PLANTED truths, rebuilt here so the claims in
equipop/opportunity.py are checked, not quoted: low-educated parents
clustered in districts, and three worlds of incomes on the same people
- the neighbourhood matters at a planted scale (A), only family
matters (B), nothing matters (C).

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import contextlib
import io

import numpy as np
import pandas as pd
import pytest

import equipop
from equipop.opportunity import OpportunityError, theta_profile

PLANTED = 400
K = [50, 100, 200, 400, 800, 1600]


def _town(seed=2026, n_side=70):
    rng = np.random.default_rng(seed)
    gx, gy = np.meshgrid(np.arange(n_side), np.arange(n_side),
                         indexing="ij")
    gx, gy = gx.ravel().astype(float), gy.ravel().astype(float)
    c0 = n_side / 2
    dens = 1.0 + 9 * np.exp(-((gx - c0) ** 2 + (gy - c0) ** 2)
                            / (2 * (n_side / 5) ** 2))
    pop = rng.poisson(dens * 0.8)
    z = -1.4 + 1.0 * gx / n_side
    for cx, cy, h, s in [(0.6, 0.45, 2.2, 0.08), (0.25, 0.3, 1.8, 0.06),
                         (0.8, 0.8, 2.0, 0.09)]:
        z = z + h * np.exp(-((gx - cx * n_side) ** 2
                             + (gy - cy * n_side) ** 2)
                           / (2 * (s * n_side) ** 2))
    z = z + rng.normal(0, 0.5, z.size)
    p_low = 1 / (1 + np.exp(-z))
    live = np.flatnonzero(pop > 0)
    cell_of = np.repeat(live, pop[live])
    low = (rng.random(cell_of.size) < p_low[cell_of]).astype(float)
    df = pd.DataFrame({
        "x": gx[cell_of] * 100 + 20 + 60 * rng.random(cell_of.size),
        "y": gy[cell_of] * 100 + 20 + 60 * rng.random(cell_of.size),
        "low_edu": low,
        "family": np.where(low > 0, "low", "not low")})
    # the character at the PLANTED scale, by EquiPop itself
    from equipop.cells import build_cells
    import equipop.fastcounts as FC
    with contextlib.redirect_stdout(io.StringIO()):
        cd = build_cells(df, "x", "y", binary_vars=["low_edu"],
                         unit_size=100.0)
        r = FC.run_knn_counts(cd, k_values=[PLANTED], self_rule="exclude",
                              seed=1)
    look = dict(zip(zip(r["EastWest"].round().astype(int),
                        r["NorthSouth"].round().astype(int)),
                    r[f"R_low_edu_{PLANTED}"]))
    sx = (np.floor(df.x / 100) * 100 + 50).astype(int)
    sy = (np.floor(df.y / 100) * 100 + 50).astype(int)
    c = np.array([look[k] for k in zip(sx, sy)])
    eps = rng.normal(0, 0.55, len(df))
    df["inc_A"] = np.exp(10 - 0.3 * low - 1.2 * c + eps)
    df["inc_B"] = np.exp(10 - 0.6 * low + eps)
    df["inc_C"] = np.exp(10 + eps)
    return df


@pytest.fixture(scope="module")
def town():
    return _town()


def _run(df, **kw):
    kw.setdefault("k_values", K)
    kw.setdefault("character", "low_edu")
    with contextlib.redirect_stdout(io.StringIO()) as f:
        out = theta_profile(df, **kw)
    return out, f.getvalue()


def _mld(y):
    return float(np.mean(np.log(y.mean() / y)))


# ------------------------------------------------------- the planted truths
def test_the_profile_peaks_at_the_planted_scale(town):
    """Town A: the neighbourhood acts at 400 people. The profile's
    peak is there, for the groups and for the no-groups check alike.

    And with a real relationship the shuffled noise floor sits far
    below theta - the floor is chance, not the answer again.

    BROKEN WITH: the character read from the wrong k's column (the
    first k for all); the groups cut on the outcome instead of the
    character; and the floor computed without shuffling (it then
    equals theta)."""
    out, msg = _run(town, outcome="inc_A", shuffles=19)
    assert (out.noise < out.theta / 20).all()
    assert (out.noise_p95 >= out.noise).all()
    assert (out.p_value == 1 / 20).all()          # no shuffle reaches it
    assert int(out.loc[out.theta.idxmax(), "k"]) == PLANTED
    assert int(out.loc[out.theta_nogroups.idxmax(), "k"]) == PLANTED
    assert f"peaks at k = {PLANTED}" in msg


def test_ten_groups_come_close_to_no_groups_and_fewer_fall_short(town):
    """The finding behind John's default: coarse groups understate.
    At the peak, 3 groups < 5 < 10, and 10 is within 5% of the
    no-groups value.

    BROKEN WITH: `groups` ignored (always 10)."""
    th = {g: _run(town, outcome="inc_A", groups=g, shuffles=0,
                  k_values=[PLANTED])[0].iloc[0] for g in (3, 5, 10)}
    assert th[3].theta < th[5].theta < th[10].theta
    assert th[10].theta > 0.95 * th[10].theta_nogroups
    assert th[10].groups == 10


def test_between_plus_within_is_the_whole(town):
    """The split is EXACT: the between part from the run, plus a
    within part computed here independently from each group's own
    MLD, is the MLD over everybody. Two routes, no shared code.

    BROKEN WITH: the between part using unweighted group shares."""
    out, _ = _run(town, outcome="inc_A", k_values=[200], shuffles=0)
    from equipop.opportunity import _equal_groups
    import equipop.fastcounts as FC
    from equipop.cells import build_cells
    with contextlib.redirect_stdout(io.StringIO()):
        cd = build_cells(town, "x", "y", binary_vars=["low_edu"],
                         unit_size=100.0)
        r = FC.run_knn_counts(cd, k_values=[200], self_rule="exclude",
                              seed=1)
    look = dict(zip(zip(r["EastWest"].round().astype(int),
                        r["NorthSouth"].round().astype(int)),
                    r["R_low_edu_200"]))
    sx = (np.floor(town.x / 100) * 100 + 50).astype(int)
    sy = (np.floor(town.y / 100) * 100 + 50).astype(int)
    c = np.array([look[k] for k in zip(sx, sy)])
    y = town.inc_A.to_numpy()
    g = _equal_groups(c, np.ones_like(c), 10)
    within = sum((g == j).mean() * _mld(y[g == j]) for j in np.unique(g))
    row = out.iloc[0]
    assert row["between"] + within == pytest.approx(_mld(y), rel=1e-10)
    assert row["total"] == pytest.approx(_mld(y), rel=1e-10)


def test_only_family_gives_nothing_on_top_of_family(town):
    """Town B: families with low-educated parents cluster, so the
    neighbourhood "alone" lines up with income though the place does
    nothing - and on top of family it adds nothing beyond its own
    noise floor. Town A adds well above it.

    BROKEN WITH: on-top computed as theta(both) - theta(groups) (the
    neighbourhood's own share subtracted instead of family's)."""
    b, _ = _run(town, outcome="inc_B", family="family")
    assert (b.theta > 3 * b.noise).all()                  # "alone" > 0
    assert (b.theta_on_top < 4 * b.noise_on_top).all()
    assert (b.theta_on_top.abs() < 0.002).all()
    a, _ = _run(town, outcome="inc_A", family="family")
    peak = a.set_index("k").loc[PLANTED]
    assert peak.theta_on_top > 10 * peak.noise_on_top
    assert peak.theta_on_top < peak.theta                 # family took some
    assert b.theta_family.iloc[0] == pytest.approx(
        b.theta_family.iloc[-1])                          # one number


def test_with_nothing_there_theta_is_its_noise_floor(town):
    """Town C, incomes unrelated to anything: theta is not zero - noise
    between group means reads as inequality - and the shuffled floor
    measures it. About (groups - 1) / people.

    A profile of pure noise has a highest point too; the run must not
    call it a peak.

    BROKEN WITH: a peak named among k's that do not stand above the
    floor. (The floor computed WITHOUT shuffling passes here - in this
    world chance and theta are the same size - and is caught by the
    planted-scale test, where they are not.)"""
    small = town.sample(2000, random_state=3)
    out, msg = _run(small, outcome="inc_C", groups=20, shuffles=99,
                    k_values=[100, 400])
    guide = 19 / 2000
    for r in out.itertuples():
        assert 0.4 * guide < r.noise < 2.5 * guide
        assert r.theta < 4 * r.noise
        assert r.p_value > 0.05
    assert "not clearly above chance" in msg
    assert "peaks at" not in msg


# ----------------------------------------------------------- the inputs
def test_a_separate_context_population(town):
    """The neighbourhood is made of one population (all adults) and the
    outcome measured on another (people aged 30-40, here a random
    third). With the context equal to the people it is the plain run.

    BROKEN WITH: the character computed from the people instead of the
    context."""
    same, _ = _run(town, outcome="inc_A", k_values=[400], shuffles=0)
    as_ctx, _ = _run(town, outcome="inc_A", k_values=[400], shuffles=0,
                     context=town)
    assert as_ctx.theta.iloc[0] == pytest.approx(same.theta.iloc[0],
                                                 rel=1e-12)
    young = town.sample(frac=1 / 3, random_state=5)
    sub, _ = _run(young, outcome="inc_A", k_values=[400], shuffles=0,
                  context=town)
    alone, _ = _run(young, outcome="inc_A", k_values=[400], shuffles=0)
    assert sub.people.iloc[0] == len(young)
    # a third of the people, so their own neighbourhoods are three
    # times wider: a different (and weaker) character
    assert sub.theta.iloc[0] > alone.theta.iloc[0]


def test_a_cell_with_people_and_no_context_still_gets_a_neighbourhood(
        town):
    """A person whose 100 m cell holds nobody of the context population
    is still a neighbourhood's centre.

    BROKEN WITH: such people dropped (the assertion on the count)."""
    lone = pd.DataFrame({"x": [-5000.0], "y": [-5000.0], "low_edu": [0.0],
                         "family": ["low"], "inc_A": [30000.0]})
    people = pd.concat([town.iloc[:3000], lone], ignore_index=True)
    out, _ = _run(people, outcome="inc_A", k_values=[100], shuffles=0,
                  context=town)
    assert out.people.iloc[0] == 3001
    assert out.no_neighbourhood.iloc[0] == 0


def test_a_weight_counts_as_that_many_people(town):
    """A row of weight 3 is three identical rows. The weights must
    DIFFER between rows: with one weight for everybody, a grouping
    that ignores them cuts the same groups, and proves nothing - the
    break-check found the first version of this test, with every
    weight 2, passing over exactly that fault.

    BROKEN WITH: the weight ignored in the groups' sizes."""
    part = town.iloc[:4000].copy()
    part["w"] = 1.0 + (part["low_edu"] > 0) * 2.0      # 1 or 3
    copies = part.loc[part.index.repeat(part["w"].astype(int))]
    copies = copies.reset_index(drop=True)
    a, _ = _run(copies, outcome="inc_A", k_values=[200], shuffles=0)
    b, _ = _run(part, outcome="inc_A", k_values=[200], shuffles=0,
                weight="w", context=copies)
    assert b.people.iloc[0] == a.people.iloc[0] == len(copies)
    assert b.theta.iloc[0] == pytest.approx(a.theta.iloc[0], rel=1e-9)


def test_mld_refuses_a_zero_and_theil_takes_it(town):
    """MLD is not defined at zero, and replacing it makes the answer
    the replacement's (BACKLOG 405). Theil admits zeros.

    BROKEN WITH: the zero check removed (MLD becomes inf/NaN quietly)."""
    df = town.iloc[:3000].copy()
    df.loc[df.index[:5], "inc_A"] = 0.0
    with pytest.raises(OpportunityError, match="index='theil'"):
        _run(df, outcome="inc_A", k_values=[100])
    out, _ = _run(df, outcome="inc_A", k_values=[100], index="theil",
                  shuffles=0)
    assert np.isfinite(out.theta.iloc[0])


def test_a_type_under_the_minimum_empties_the_profile(town):
    """As machine 2 (John's ruling): under min_group people in any type
    the share is EMPTY, and the run says why.

    BROKEN WITH: the minimum not applied."""
    df = town.sample(600, random_state=1)
    out, msg = _run(df, outcome="inc_A", k_values=[100], groups=30,
                    shuffles=0)
    assert np.isnan(out.theta.iloc[0])
    assert "EMPTY at k = 100" in msg


@pytest.mark.parametrize("kw, match", [
    (dict(groups=1), "2 or more"),
    (dict(index="gini"), "mld, theil"),
    (dict(self_rule="maybe"), "exclude"),
    (dict(k_values=[0]), "1 or more"),
    (dict(character="nope"), "not a column"),
])
def test_bad_settings_are_refused_in_words(town, kw, match):
    """BROKEN WITH: the groups check removed (a single group returned
    theta 0 rather than an error)."""
    with pytest.raises(OpportunityError, match=match):
        _run(town.iloc[:500], outcome="inc_A", **kw)


def test_a_family_field_with_too_many_values_is_refused(town):
    """A circumstance has a few categories; an identifier is not one.

    BROKEN WITH: MAX_FAMILY_LEVELS not checked."""
    df = town.iloc[:500].assign(fid=np.arange(500))
    with pytest.raises(OpportunityError, match="identifier"):
        _run(df, outcome="inc_A", family="fid", k_values=[50])


def test_it_is_published_and_documented():
    """The Python door: equipop.theta_profile, with the method in the
    topics manual."""
    assert equipop.theta_profile is theta_profile
    assert "theta_profile" in equipop.__all__
    from pathlib import Path
    topics = (Path(__file__).resolve().parents[1]
              / "MANUAL_TOPICS.md").read_text(encoding="utf-8")
    assert "theta_profile" in topics


# ===================== v1.62.1 - the external review of 1.62.0 (BACKLOG 440-441)
def _grouped(n=80, seed=4):
    """Rows standing for 1-5 people each, and the same people one per
    row, in the same order."""
    rng = np.random.default_rng(seed)
    g = pd.DataFrame({"x": rng.uniform(0, 3000, n),
                      "y": rng.uniform(0, 3000, n),
                      "low_edu": (rng.random(n) < .4).astype(float),
                      "w": rng.integers(1, 6, n).astype(float)})
    g["family"] = np.where(rng.random(n) < .5, "low", "not low")
    g["inc"] = np.exp(10 - 0.8 * g.low_edu + rng.normal(0, .5, n))
    people = g.loc[g.index.repeat(g.w.astype(int))].reset_index(drop=True)
    return g, people


def test_weight_also_weights_the_neighbourhood(town):
    """No separate context: the neighbourhood is made of the people,
    and a row of weight 3 is three of them there too. The review
    measured 0.136 against 0.085 for the same people.

    BROKEN WITH: the context weight not taken from `weight`."""
    g, people = _grouped()
    kw = dict(outcome="inc", k_values=[20, 60], groups=4, shuffles=0,
              min_group=0)
    a, _ = _run(people, **kw)
    b, _ = _run(g, weight="w", **kw)
    for c in ("people", "theta", "theta_nogroups", "smallest_group"):
        assert np.allclose(a[c], b[c], rtol=1e-12), c


def test_weighted_rows_are_shuffled_as_people():
    """The chance columns from weighted rows are those of the same
    people one per row - exactly, shuffle for shuffle - with family as
    well. The review measured a noise floor seven times too high, and
    the verdict on chance reversed.

    BROKEN WITH: each row shuffled as one block (the weight moving with
    it), as in 1.62.0."""
    g, people = _grouped()
    kw = dict(outcome="inc", k_values=[20, 60], groups=4, shuffles=40,
              min_group=0, family="family")
    a, _ = _run(people, **kw)
    b, _ = _run(g, weight="w", **kw)
    for c in ("noise", "noise_p95", "p_value", "noise_on_top",
              "noise_on_top_p95", "p_value_on_top"):
        assert np.allclose(a[c], b[c], rtol=1e-12), c


def test_fractional_weights_leave_chance_empty_and_say_so():
    """"Shuffle the people" has no meaning for 1.5 people.

    BROKEN WITH: fractional weights truncated into counts."""
    g, _people = _grouped()
    out, msg = _run(g.assign(w=g.w + 0.5), outcome="inc", weight="w",
                    k_values=[20], groups=4, min_group=0, shuffles=10)
    assert np.isnan(out.noise.iloc[0]) and np.isnan(out.p_value.iloc[0])
    assert np.isfinite(out.theta.iloc[0])
    assert "not whole numbers of people" in msg


def test_memory_does_not_grow_with_the_shuffles():
    """1.62.0 kept every permutation: 8 bytes a person a shuffle, twice
    with family - 1.6 GB for five million people at 20 shuffles. Now
    one shuffle at a time: 60 shuffles cost what 2 do.

    Measured on the shuffling itself. The whole run's peak is set by
    the neighbourhood engine, and the break-check showed a run-level
    measurement could not see 60 kept permutations underneath it.

    BROKEN WITH: every shuffle kept (a copy appended per draw)."""
    import tracemalloc
    from equipop.opportunity import _Chance
    rng = np.random.default_rng(1)
    n = 200_000
    y = np.exp(rng.normal(0, .5, n))
    codes = rng.integers(0, 10, n)
    fam = rng.integers(0, 2, n)
    both = codes * 2 + fam

    def peak(shuffles):
        ch = _Chance(y, np.ones(n), "mld")
        r = np.random.default_rng(2)
        tracemalloc.start()
        ch.anywhere(r, shuffles, codes)
        ch.within(r, shuffles, both, fam)
        _cur, top = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return top
    peak(2)
    grew = peak(60) - peak(2)
    assert grew < 0.1 * (n * 8 * 58), grew


@pytest.mark.parametrize("n", [100, 300, 1000])
def test_distinct_values_make_exactly_equal_groups(n):
    """The person who completes a group belongs to it.

    BROKEN WITH: the completing person sent up (side="right"), which
    made 29, 30 ... 31 and emptied a 300-person profile."""
    from equipop.opportunity import _equal_groups
    rng = np.random.default_rng(n)
    c = rng.permutation(np.arange(n, dtype=float))
    sizes = np.bincount(_equal_groups(c, np.ones(n), 10))
    assert sizes.tolist() == [n // 10] * 10
    # weights that complete each group exactly
    w = np.full(n, 2.0)
    assert np.bincount(_equal_groups(c, w, 10), weights=w).tolist() == \
        [2.0 * n / 10] * 10
    # ties stay together, and go with the person completing the group
    tied = np.r_[np.zeros(15), np.arange(1, 86)].astype(float)
    t = np.bincount(_equal_groups(tied, np.ones(100), 10))
    assert t[0] == 15 and t.sum() == 100


def test_a_constant_outcome_is_refused_in_words(town):
    """No inequality, so no share of it. It was a ZeroDivisionError.

    BROKEN WITH: the check removed."""
    with pytest.raises(OpportunityError, match="no inequality"):
        _run(town.iloc[:500].assign(inc_A=7.0), outcome="inc_A",
             k_values=[50])


def test_a_character_with_no_usable_value_is_refused_in_words(town):
    """It was an IndexError after two RuntimeWarnings.

    BROKEN WITH: the check removed."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        with pytest.raises(OpportunityError, match="no usable value"):
            _run(town.iloc[:500].assign(low_edu=np.nan), outcome="inc_A",
                 k_values=[50])


def test_nobody_with_a_neighbourhood_gives_empty_rows_not_errors():
    """Everybody in one 100 m cell, own cell left out: nobody has a
    neighbourhood. Rows come back empty, saying why.

    BROKEN WITH: the empty-k guard removed (IndexError)."""
    import warnings
    rng = np.random.default_rng(2)
    one = pd.DataFrame({"x": 50.0 + rng.random(40), "y": 50.0,
                        "low_edu": (rng.random(40) < .5) * 1.0,
                        "inc": np.exp(rng.normal(10, .5, 40))})
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        out, msg = _run(one, outcome="inc", k_values=[5, 10], min_group=0)
    assert out.theta.isna().all()
    assert (out.note == "nobody has a neighbourhood at this k").all()
    assert "EMPTY at k = 5" in msg


@pytest.mark.parametrize("kw, match", [
    (dict(k_values=[10.9]), "refused rather than rounded"),
    (dict(k_values=[float("nan")]), "whole number"),
    (dict(groups=2.9), "refused rather than rounded"),
    (dict(groups=float("inf")), "whole number"),
    (dict(groups=True), "not True"),
    (dict(shuffles=-2), "0 or more"),
    (dict(min_group=-1), "zero or more"),
    (dict(unit_size=0), "positive"),
    (dict(seed=1.5), "refused rather than rounded"),
    (dict(k_values=[]), "empty"),
])
def test_settings_are_refused_not_coerced(town, kw, match):
    """k = 10.9 ran as 10, groups = 2.9 as 2, a negative minimum
    switched the guard off. Refused now, as k is everywhere else.

    BROKEN WITH: int() put back on groups (2.9 ran as 2)."""
    with pytest.raises(OpportunityError, match=match):
        kw.setdefault("k_values", [20])
        _run(town.iloc[:300], outcome="inc_A", **kw)


def test_the_no_groups_check_fits_the_outcome_and_stays_a_share():
    """Income exactly a straight line in the character: everything is
    between types, so the no-groups share is 1. Fitted on the log, as
    1.62.0 did, it came out 1.046 - more than the whole.

    BROKEN WITH: the fit on log y restored."""
    from equipop.opportunity import _design, _fitted_share
    c = np.linspace(0.001, 1, 300)
    y = c / c.mean()
    share = _fitted_share(y, np.ones_like(y), _design(c), "mld")
    assert share == pytest.approx(1.0, abs=1e-9)
