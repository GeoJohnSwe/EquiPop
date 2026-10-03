"""Every engine x every origin rule x every overshoot mode.

WHY THIS FILE EXISTS. The 1.51 review's finding F1 was that the Stata
bridge accepted `self_rule`, `overshoot_mode` and `seed`, documented
them, RECORDED THEM IN THE PROVENANCE, and did not pass them to the
effort engines. The engines had taken all three for a release. The
test suite had thorough coverage of each option and thorough coverage
of each engine, and nothing that crossed the two - so a run could
report `overshoot_mode: whole` in its own record while the engine it
called had computed `proportional`. BACKLOG 340 (r_values dropped on
the tiled branch) and BACKLOG 345 (five options unreachable through
the same wrapper) are the same defect in two more places.

The lesson is not "add a test for self_rule in friction". It is that
an option and an engine are a PAIR, and the pairs are where these
faults live. So this file enumerates them.

It asserts two things per combination, and deliberately nothing about
the numbers themselves - those belong in the engines' own files:

  1. THE OPTION ARRIVES. Changing it changes a number. A test that an
     option is accepted proves only that no exception was raised, and
     every one of the three faults above passed exactly such a test.
  2. THE DEFAULT IS THE ENGINE'S DEFAULT. Saying nothing must give
     what the engine gives when asked nothing, or a door is offering a
     second opinion on its own run. Checked BY VALUE, never by reading
     a default back out of a dialog - BACKLOG 95's lesson.
"""

import io
import itertools
from contextlib import redirect_stdout

import numpy as np
import pandas as pd
import pytest

from equipop import overshoot, selfrule
from equipop.stata_bridge import dispatch


def _hush(fn, *a, **kw):
    buf = io.StringIO()
    with redirect_stdout(buf):
        return fn(*a, **kw)


# John's own example as a town: a 3x3 of cells 100 m apart holding ten
# people each. k=15 crosses a ring, which is the only situation in
# which the overshoot mode means anything, and the origin holds 10 of
# the 15, which is the only situation in which the origin rule does.
def _town(n=3, step=100.0, people=10.0):
    return ([step * i + 50.0 for i in range(n) for _ in range(n)],
            [step * j + 50.0 for _ in range(n) for j in range(n)],
            [people] * (n * n))


def _dem(x, y, flat=True):
    """A DEM table on the same grid - a hill, so slope has work to do."""
    return pd.DataFrame({"x": x, "y": y,
                         "z": [0.0] * len(x) if flat
                         else [20.0 * i for i in range(len(x))]})


def _barriers(x, y):
    """A friction table: the middle column costs more to enter."""
    return pd.DataFrame({"x": x, "y": y,
                         "friction": [1.0 if xx == 150.0 else 0.0
                                      for xx in x]})


ENGINES = ["counts", "stats", "friction", "slope"]
RULES = sorted(selfrule.CHOICES) if hasattr(selfrule, "CHOICES") \
    else [selfrule.INCLUDE, selfrule.EXCLUDE]
MODES = [overshoot.WHOLE, overshoot.PROPORTIONAL, overshoot.SAMPLED]


def _run(engine, tmp_path, flat=False, **opts):
    x, y, w = _town()
    kw = dict(unit_size=100.0, weight=w, k_values=[15])
    # THE CELLS HAVE TO BE TELLABLE APART, or `sampled` is
    # unobservable. The first version of this file gave every cell ten
    # identical people and no treatment, so WHICHEVER cell the sampled
    # ring admitted, N_15 came out the same - and the seed test passed
    # with the seed deliberately removed. Found by break-checking it
    # rather than by reading it. A varying group count (and, for
    # machine 2, a varying value) makes the choice show in T_15 and in
    # the mean.
    if engine == "stats":
        kw["values"] = {"v": [float(i) for i in range(len(x))]}
        kw["stats"] = {"v": ["mean"]}
    else:
        kw["treat"] = {"g": [float(i) for i in range(len(x))]}
        kw["treat_are_counts"] = True
    if engine == "slope":
        # `flat` exists for the SAMPLED tests only. A hill gives every
        # neighbour a different cost, so the ordering is total and the
        # crossing ring has nothing left to choose - which made the
        # seed test pass for slope with the seed removed. Sampling can
        # only be observed where there is a TIE to break, so the test
        # that is about sampling asks for flat ground and says why.
        p = tmp_path / ("dem_flat.csv" if flat else "dem.csv")
        _dem(x, y, flat=flat).to_csv(p, index=False)
        kw["dem"] = str(p)
    if engine == "friction":
        p = tmp_path / "fr.csv"
        _barriers(x, y).to_csv(p, index=False)
        kw["friction_file"] = str(p)
    kw.update(opts)
    return _hush(dispatch, engine, x, y, **kw)


def _signature(got):
    """The numbers a reader would compare, as a flat tuple."""
    out = []
    for key in sorted(got):
        arr = np.asarray(got[key], float)
        out.append((key, tuple(np.round(np.nan_to_num(arr, nan=-1.0), 6))))
    return tuple(out)


# =====================================================================
# 1. THE OPTION ARRIVES
# =====================================================================

@pytest.mark.parametrize("engine", ENGINES)
def test_the_origin_rule_reaches_every_engine(engine, tmp_path):
    """BROKEN WITH: dropping `self_rule=self_rule` from that engine's
    dispatch call - which is exactly what review finding F1 was, for
    friction and slope, in released code.

    EXCLUDE sets w_ii = 0 by dropping the origin's whole CELL, so with
    ten people at the origin and k=15 the search has to reach further.
    If the rule arrives, SOMETHING moves.
    """
    inc = _run(engine, tmp_path, self_rule=selfrule.INCLUDE)
    exc = _run(engine, tmp_path, self_rule=selfrule.EXCLUDE)
    assert _signature(inc) != _signature(exc), \
        f"self_rule changed nothing in the {engine} engine - the " \
        "option is being accepted and discarded"


@pytest.mark.parametrize("engine", ENGINES)
def test_the_overshoot_mode_reaches_every_engine(engine, tmp_path):
    """BROKEN WITH: dropping `overshoot_mode=overshoot_mode` from that
    engine's dispatch call - the other half of F1.

    Ten people per cell and k=15: the whole ring admits 50, a
    proportional share admits exactly 15. There is no reading of the
    data under which those agree.
    """
    whole = _run(engine, tmp_path, overshoot_mode=overshoot.WHOLE)
    prop = _run(engine, tmp_path, overshoot_mode=overshoot.PROPORTIONAL)
    assert _signature(whole) != _signature(prop), \
        f"overshoot_mode changed nothing in the {engine} engine"


@pytest.mark.parametrize("engine", ENGINES)
def test_a_seed_reaches_every_engine_that_samples(engine, tmp_path):
    """BROKEN WITH: dropping `seed=seed`, which is the fault that made
    a sampled run unrepeatable while reporting a seed (F5's relative).

    Under `sampled` the seed decides which cells of the crossing ring
    are admitted. The same seed must repeat exactly; that is the whole
    contract of the mode.

    FLAT GROUND, deliberately. Sampling can only be observed where
    there is a TIE to break, and the hill this file uses elsewhere
    gives every neighbour a distinct cost - so with a hill this test
    passed for the slope engine with `seed=` deliberately removed, and
    the break-check is what said so. The two runs are also required to
    DISAGREE when the seeds differ, or "repeats exactly" would be
    satisfied by an engine that ignores the seed entirely.
    """
    kw = dict(flat=True, overshoot_mode=overshoot.SAMPLED)
    a = _run(engine, tmp_path, seed=1848, **kw)
    b = _run(engine, tmp_path, seed=1848, **kw)
    assert _signature(a) == _signature(b), \
        f"the same seed gave two answers in the {engine} engine"
    # A seed that is ignored also "repeats". Somewhere in a hundred
    # draws a different seed has to produce a different answer, or the
    # engine is not sampling at all.
    assert any(_signature(_run(engine, tmp_path, seed=s, **kw))
               != _signature(a) for s in range(1, 101)), \
        f"no seed changed the {engine} engine's answer - it is not " \
        "sampling, or the seed never arrives"


# =====================================================================
# 2. THE DEFAULT IS THE ENGINE'S DEFAULT
# =====================================================================

@pytest.mark.parametrize("engine", ENGINES)
def test_saying_nothing_gives_what_the_published_default_gives(
        engine, tmp_path):
    """BROKEN WITH: changing either default in the dispatcher without
    changing it in the engine.

    Two doors, one answer. An option left alone must give exactly what
    naming its documented default gives - checked by VALUE, because
    reading the default back out proves only that two strings match.
    """
    quiet = _run(engine, tmp_path)
    named = _run(engine, tmp_path,
                 self_rule=selfrule.INCLUDE,
                 overshoot_mode=overshoot.PROPORTIONAL)
    assert _signature(quiet) == _signature(named), \
        f"the {engine} engine's default is not include + proportional"


# =====================================================================
# 3. EVERY COMBINATION RUNS AND ANSWERS SOMETHING POSSIBLE
# =====================================================================

@pytest.mark.parametrize("engine,rule,mode",
                         list(itertools.product(ENGINES, RULES, MODES)))
def test_every_combination_produces_a_possible_answer(
        engine, rule, mode, tmp_path):
    """BROKEN WITH: any engine that refuses a combination, or returns
    one that cannot be true.

    The cross-product proper. Not an assertion about particular
    numbers - those live in each engine's own file - but about the
    three things that must hold for all of them: N_15 is at least k
    under every mode but proportional, which hits it exactly; a
    distance is finite and non-negative; and no NaN appears where a
    neighbourhood was resolvable.
    """
    got = _run(engine, tmp_path, self_rule=rule, overshoot_mode=mode,
               seed=1848 if mode == overshoot.SAMPLED else None)
    n = np.asarray(got["N_15"], float)
    assert np.isfinite(n).all(), f"{engine}/{rule}/{mode} left N missing"
    if mode == overshoot.PROPORTIONAL:
        assert n == pytest.approx([15.0] * len(n)), \
            "proportional must land on k exactly"
    else:
        assert (n >= 15.0 - 1e-9).all(), \
            f"{mode} stopped short of k"
    d = np.asarray(got["Dist_15"], float)
    assert np.isfinite(d).all() and (d >= 0).all()


@pytest.mark.parametrize("engine", ENGINES)
def test_excluding_the_origin_never_shrinks_the_reach(engine, tmp_path):
    """BROKEN WITH: an engine that drops the origin from the COUNT but
    not from the SEARCH, or the reverse.

    The invariant that says EXCLUDE means what it says. Removing the
    origin's own people cannot make the neighbourhood that satisfies k
    any smaller, so its radius is greater or equal at every origin.
    This is the shape of the error a one-sided fix produces, and it is
    invisible in a test that only compares two signatures.
    """
    inc = np.asarray(_run(engine, tmp_path,
                          self_rule=selfrule.INCLUDE)["Dist_15"], float)
    exc = np.asarray(_run(engine, tmp_path,
                          self_rule=selfrule.EXCLUDE)["Dist_15"], float)
    assert (exc >= inc - 1e-9).all(), \
        f"{engine}: excluding the origin REDUCED the radius at " \
        f"{int((exc < inc - 1e-9).sum())} origin(s)"


def test_the_origins_own_cell_is_reported_either_way(tmp_path):
    """BROKEN WITH: zeroing N_local under EXCLUDE, or dropping it from
    the dispatcher's allowed prefixes.

    FIRST WRITTEN parametrised over all four engines with a skip for
    whichever lacked the column - and every one of the four skipped,
    including the only engine that has it, because the skip was on
    `stats` by mistake. Four green skips read as coverage and were
    nothing, which is the same defect as an unfalsifiable assertion
    wearing different clothes. Through the dispatcher only machine 2
    returns a `_local` column (counts gives N_15/Dist_15, the effort
    engines add Rounds_15), so this is a machine-2 invariant and says
    so.

    The `_local` columns are FACTS ABOUT THE CELL - how many people
    live there - not part of the neighbourhood sum, so the origin rule
    must not touch them. A reader needs them under EXCLUDE most of
    all, because that is the run where those people are not in the
    total.
    """
    for rule in (selfrule.INCLUDE, selfrule.EXCLUDE):
        got = _run("stats", tmp_path, self_rule=rule)
        assert "N_local" in got, \
            "machine 2 stopped reporting the origin cell's own count"
        assert np.asarray(got["N_local"], float) == \
            pytest.approx([10.0] * 9), \
            f"{rule} moved the origin cell's own count"
