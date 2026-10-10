"""BACKLOG 385 - what cell size does this data want?

John, 9 October 2026: every machine assumes a unit size, in Stata it
has to be named with `unit()` to change, and "knowing the unit size is
a battle between computing time and detail".

THE CLAIM THE WHOLE ADVISORY RESTS ON, and the reason this file runs
the real engine rather than trusting a formula:

    the number of cells whose own population >= k
      ==
    the count fastcounts reports as self-potential origins

If that is false the advisory is worthless, so it is checked by
RUNNING THE ENGINE and parsing its own message - not by comparing two
expressions of the same idea. That distinction is this session's own
lesson from 1.53.4: an identity test between two users of one function
proves consistency and nothing about correctness.

Each test's docstring names what it was BROKEN WITH, and each was
actually broken that way.
"""
import io
import contextlib
import re

import numpy as np
import pandas as pd
import pytest

from equipop import unitsize
from equipop.cells import build_cells
from equipop.fastcounts import run_knn_counts


def _engine_saturated(cd, ks, **kw):
    """What the engine itself reports, per k, from its own message."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_knn_counts(cd, list(ks), **kw)
    said = buf.getvalue()
    got = {}
    for k in ks:
        m = re.search(rf"k={k}: the whole neighbourhood was the origin "
                      rf"cell for ([\d,]+) of ([\d,]+) origins", said)
        got[k] = int(m.group(1).replace(",", "")) if m else 0
    return got


def _predicted_saturated(x, y, w, unit, ks):
    """What the advisory predicts, read off its own table."""
    a = unitsize.advise_unit(x, y, w, k_values=ks, candidates=[unit])
    row = a["rows"][0]
    return {k: row["saturated_cells"][k] for k in ks}


# ------------------------------------------------- the central claim
@pytest.mark.parametrize("name,xs,ys,ws,unit,ks", [
    # one dense cell among sparse ones
    ("one dense cell",
     list(np.linspace(1, 90, 15)) + [1500.0, 2500.0, 3500.0],
     [5.0] * 15 + [5.0, 5.0, 5.0],
     [1.0] * 18, 100.0, (5, 10, 20)),
    # four cells at four densities - the boundary cases matter
    ("four densities",
     ([10.0] * 3 + [1010.0] * 8 + [2010.0] * 25 + [3010.0] * 60),
     ([10.0] * 96),
     [1.0] * 96, 100.0, (3, 8, 25, 60, 61)),
    # population as a WEIGHT, not a row count - the case a row-count
    # version of this would get wrong
    ("weighted cells",
     [50.0, 1050.0, 2050.0], [50.0, 50.0, 50.0],
     [200.0, 50.0, 7.0], 100.0, (7, 10, 50, 100, 200, 201)),
])
def test_the_prediction_equals_what_the_engine_reports(name, xs, ys, ws,
                                                       unit, ks):
    """BROKEN WITH: `pop > k` instead of `pop >= k - 1e-9` in
    advise_unit.

    THE ONE THING THAT MAKES THIS FEATURE HONEST. The advisory claims
    to predict, before a run, a number the engine will report after
    it. So it is checked against the ENGINE, on three shapes, with the
    exact boundary values of k in each - including k equal to a cell's
    population exactly, which is where a `>` and a `>=` part company.
    The 1e-9 is not decoration: BACKLOG 304 found that a bare `>= k`
    is a floating-point trap in fastcounts, because under
    `proportional` the crossing cell contributes a fraction and the
    sum comes back 99.99999999999999. The two tests have to use the
    same tolerance or the advice is wrong exactly on the boundary.
    """
    x = np.array(xs, dtype=float)
    y = np.array(ys, dtype=float)
    w = np.array(ws, dtype=float)
    cd = build_cells(pd.DataFrame({"E": x, "N": y, "w": w}),
                     "E", "N", unit_size=unit, weights="w")
    got = _engine_saturated(cd, ks)
    pred = _predicted_saturated(x, y, w, unit, ks)
    assert pred == got, (
        f"{name}: the advisory predicts {pred} and the engine reports "
        f"{got} - the advice is not about the thing it claims")


def test_fractional_weights_land_just_under_k_and_the_slack_catches_it():
    """BROKEN WITH: `pop >= k` with no 1e-9 slack.

    MEASURED, AND IT IS THE PROJECT'S MAIN RASTER INPUT. A WorldPop
    pixel carries a FRACTIONAL population, so a cell's total is an
    accumulated float sum - and 1000 pixels of 0.1 sum to
    99.9999999999986, short of 100 by 1.4e-12. Without the slack the
    advisory reports 0 saturated cells where the engine reports 1, and
    it would get that wrong on exactly the data EquiPop is usually
    pointed at.

    This is a SECOND reason for the slack, not the one the module
    docstring first gave: BACKLOG 304's trap is in fastcounts, where
    `proportional` overshoot makes the crossing cell contribute a
    fraction. This one is in the advisory's own arithmetic and would
    bite even with whole-person overshoot.
    """
    n = 1000
    x = np.concatenate([np.full(n, 50.0), [5000.0]])
    y = np.concatenate([np.full(n, 50.0), [50.0]])
    w = np.concatenate([np.full(n, 0.1), [1.0]])

    pop = unitsize._cell_populations(x, y, w, 100.0)
    assert pop.max() < 100.0, (
        "the float sum no longer falls short - if numpy changed, this "
        "test has stopped exercising the thing it is about")
    assert pop.max() >= 100.0 - 1e-9

    cd = build_cells(pd.DataFrame({"E": x, "N": y, "w": w}),
                     "E", "N", unit_size=100.0, weights="w")
    assert _predicted_saturated(x, y, w, 100.0, (100,)) == \
        _engine_saturated(cd, (100,)) == {100: 1}


def test_the_grid_agrees_with_the_ENGINE_grid_on_a_tall_extent():
    """BROKEN WITH: `span = 1000` instead of the measured span.

    THE KEY COLLISION, and it needs an answer key from outside this
    module. Two int64 grid indices are paired into one 1-D key so the
    group-by is a single pass; the multiplier has to come from the
    data, because a fixed one wraps. Measured on a 120 km by 300 m
    strip - an ordinary study extent - a multiplier of 1000 merges two
    distinct cells: 1,201 cells become 1,200, the largest population
    becomes 2.0 where every real cell holds 1.0, and the k=2 count goes
    from 0 saturated cells to 1. A recommendation off the back of a
    hash collision.

    The key is `build_cells`, which grids with a pandas group-by on two
    SEPARATE columns and pairs nothing - a different implementation of
    the same question, so agreeing with it is evidence rather than
    consistency (the 1.53.4 lesson).
    """
    ys = np.arange(1200) * 100.0 + 50.0
    x = np.concatenate([np.full(1200, 50.0), [150.0]])
    y = np.concatenate([ys, [50.0]])
    w = np.ones(x.size)

    cd = build_cells(pd.DataFrame({"E": x, "N": y, "w": w}),
                     "E", "N", unit_size=100.0, weights="w")
    pop = unitsize._cell_populations(x, y, w, 100.0)

    assert pop.size == cd.n.size, (
        f"the advisory makes {pop.size} cells and the engine "
        f"{cd.n.size} - the grids disagree")
    assert sorted(pop.tolist()) == sorted(cd.n.tolist()), (
        "the cell counts match but the populations do not")
    assert pop.max() == 1.0, "every cell in this strip holds one person"


def test_the_callers_own_unit_is_always_on_the_ladder():
    """BROKEN WITH: dropping `| ({float(current)} if current else set())`.

    Whatever the user set has to have a row, or the table cannot show
    them where they are standing: the '<- yours' marker never renders
    and a warning cannot quote their own number back to them. The fixed
    ladder is for comparability between runs; their own unit is why the
    table is about them.
    """
    x = np.array([10.0, 2000.0, 4000.0])
    y = np.array([10.0, 10.0, 10.0])
    for u in (300.0, 137.0, 100.0):
        a = unitsize.advise_unit(x, y, None, k_values=[2], current=u)
        units = [r["unit"] for r in a["rows"]]
        assert u in units, f"unit({u:g}) has no row"
        assert units == sorted(units), "the ladder is out of order"
        assert "<- yours" in "\n".join(
            unitsize.format_advice(a, current=u)), \
            f"unit({u:g}) is not marked as theirs"


@pytest.mark.parametrize("name,xs,ys,ws,ks", [
    ("one dense cell", list(np.linspace(1, 90, 15)) + [1500.0, 2500.0],
     [5.0] * 17, [1.0] * 17, (5, 10)),
    ("four densities",
     [10.0] * 3 + [1010.0] * 8 + [2010.0] * 25 + [3010.0] * 60,
     [10.0] * 96, [1.0] * 96, (3, 8, 25, 60)),
    ("weighted cells", [50.0, 1050.0, 2050.0], [50.0] * 3,
     [200.0, 50.0, 7.0], (7, 50, 200)),
    ("one cell holds everybody", [50.0] * 40, [50.0] * 40,
     [100.0] * 40, (10, 100, 1000)),
])
def test_under_exclude_the_engine_NEVER_saturates_an_origin(
        name, xs, ys, ws, ks):
    """BROKEN WITH: `applies = True` regardless of the rule, which is
    what 1.54.0 shipped.

    REVIEW F1, AND THE MEASUREMENT IS STRONGER THAN THE REVIEW SAID.
    1.54.0 took `self_rule` and used it only as a LABEL: the numbers
    were computed identically under either rule, the report announced
    which rule it had assumed, and a footnote then said the counts do
    not apply. So an `exclude` user was shown "100.0% of people are in
    a cell that already holds k" about something that cannot happen to
    them, and - worse - a recommendation derived from it.

    Measured here on four shapes: fastcounts drops the origin's WHOLE
    CELL under exclude (`keep = idx != oi_range`), so the saturated
    count is STRUCTURALLY ZERO. Not approximate, not usually - zero,
    including on a shape where one cell holds every single person and
    include reports a saturated origin.

    That is why the fix omits the columns rather than relabelling
    them: there is no number to print.
    """
    x = np.array(xs, dtype=float)
    y = np.array(ys, dtype=float)
    w = np.array(ws, dtype=float)
    cd = build_cells(pd.DataFrame({"E": x, "N": y, "w": w}),
                     "E", "N", unit_size=100.0, weights="w")

    include = _engine_saturated(cd, ks)
    exclude = _engine_saturated(cd, ks, self_rule="exclude")
    pred = _predicted_saturated(x, y, w, 100.0, ks)

    assert pred == include, f"{name}: the include case is not predicted"
    assert all(v == 0 for v in exclude.values()), (
        f"{name}: the engine now reports {exclude} under exclude. If "
        f"the engine changed, this advisory's whole premise has to "
        f"change with it - it currently prints NO k columns under "
        f"exclude on the grounds that they would all be zero")
    assert any(v > 0 for v in include.values()), (
        f"{name}: nothing saturates under include either, so this "
        f"shape proves nothing about the difference")


def test_the_exclude_table_omits_the_columns_it_cannot_fill():
    """BROKEN WITH: printing the k columns under exclude, or filling
    them with 0 instead of leaving them out.

    REVIEW F1, the output half. A zero would be read as a measurement
    - "no saturated cells at this size, good" - and the next step
    would be to pick the coarsest size on the strength of it. So the
    columns are absent, the recommendation is absent, and the reason
    is stated. The cost and resolution-floor columns stay, because
    they are about the GRID and hold under either rule.
    """
    x = np.array([10.0, 20.0, 30.0, 40.0])
    y = np.array([10.0] * 4)
    w = np.array([500.0] * 4)
    kw = dict(k_values=[100], candidates=[100.0, 1000.0], current=1000.0)

    inc = unitsize.advise_unit(x, y, w, self_rule="include", **kw)
    exc = unitsize.advise_unit(x, y, w, self_rule="exclude", **kw)

    assert inc["applies"] is True and exc["applies"] is False
    assert exc["recommended"][100] is None, (
        "a size was recommended under exclude - with every share "
        "structurally zero, max(good) names the COARSEST size on the "
        "ladder every time")
    assert inc["recommended"][100] != exc["recommended"][100] or \
        inc["recommended"][100] is None
    for r in exc["rows"]:
        assert r["saturated_cells"][100] is None, "a zero, not absent"
        assert r["share_people"][100] is None
        assert r["cells"] > 0, "the cost column is still real"

    said = "\n".join(unitsize.format_advice(exc, current=1000.0))
    assert "originrule(exclude)" in said
    assert "NOT SHOWN" in said and "zero by construction" in said
    assert "No size is recommended" in said
    # and none of the include wording may survive into it
    assert "% of people" not in said
    assert "coarsest size keeping" not in said
    # the include table is unaffected
    inc_said = "\n".join(unitsize.format_advice(inc, current=1000.0))
    assert "of people" in inc_said and "NOT SHOWN" not in inc_said


def test_an_exclude_run_says_nothing_about_saturation():
    """BROKEN WITH: letting advise_on_run reach its warning under
    exclude.

    REVIEW F1 at the three ordinary-run doors, which all pass the
    user's real origin rule in. Under exclude the warning would be
    about a risk the run does not carry, so the only thing that may
    still come out is the degree note - which is about the
    coordinates, not the rule.
    """
    x = np.array([10.0, 20.0, 30.0, 40.0])
    y = np.array([10.0] * 4)
    w = np.array([500.0] * 4)
    exc = unitsize.advise_unit(x, y, w, k_values=[100],
                               candidates=[100.0, 1000.0],
                               current=1000.0, self_rule="exclude")
    for was_set in (True, False):
        said = "\n".join(unitsize.advise_on_run(
            exc, unit=1000.0, unit_was_set=was_set))
        assert "WARNING" not in said
        assert "ESTIMATED" not in said
        assert "already holds k" not in said
    # the include run on the same data DOES warn, so the assertions
    # above are about the rule and not about the data
    inc = unitsize.advise_unit(x, y, w, k_values=[100],
                               candidates=[100.0, 1000.0],
                               current=1000.0, self_rule="include")
    assert "WARNING" in "\n".join(unitsize.advise_on_run(
        inc, unit=1000.0, unit_was_set=True))


def test_a_nonsense_origin_rule_is_refused_not_labelled():
    """BROKEN WITH: `applies = self_rule == "include"` with no
    validation, so any unknown string silently selects exclude.

    REVIEW F1. The rule now decides whether the criterion applies, so
    a typo is not a cosmetic problem: `originrule(inclde)` would have
    quietly produced the exclude behaviour, and `originrule(exclude )`
    the include one. Validated and normalised instead.
    """
    x = np.array([1.0, 2.0, 5000.0])
    y = np.array([1.0, 2.0, 5000.0])
    for bad in ("banana", "inclde", "i=j=k", "both", ""):
        with pytest.raises(ValueError, match="originrule"):
            unitsize.advise_unit(x, y, None, k_values=[2],
                                 self_rule=bad)
    # case and surrounding space are normalised, not refused
    for ok in ("include", "INCLUDE", " Include "):
        assert unitsize.advise_unit(x, y, None, k_values=[2],
                                    self_rule=ok)["self_rule"] == "include"
    assert unitsize.advise_unit(x, y, None, k_values=[2],
                                self_rule="EXCLUDE")["self_rule"] == "exclude"


# -------------------------------------------- what the table is for
def test_the_recommendation_is_the_COARSEST_size_within_tolerance():
    """BROKEN WITH: `min(good)` instead of `max(good)`.

    Coarsest is cheapest, and the tolerance is what protects the
    answer - so the recommendation is the largest unit that still
    keeps the estimated share acceptable. Recommending the finest
    would be safe, useless and exactly what the 100 m default already
    does.
    """
    rng = np.random.default_rng(1)
    x = rng.uniform(0, 20000, 4000)
    y = rng.uniform(0, 20000, 4000)
    w = np.ones(4000)
    a = unitsize.advise_unit(x, y, w, k_values=[20],
                             candidates=[100, 250, 500, 1000, 2500])
    rec = a["recommended"][20]
    rows = {r["unit"]: r for r in a["rows"]}
    assert rec is not None
    assert rows[rec]["share_people"][20] <= a["tolerance"]
    bigger = [u for u in rows if u > rec]
    assert all(rows[u]["share_people"][20] > a["tolerance"]
               for u in bigger), (
        "a coarser size was also within tolerance and was not chosen")


def test_a_k_no_size_can_serve_says_so_rather_than_guessing():
    """BROKEN WITH: `max(good) if good else min(rows)`, i.e. falling
    back to the finest candidate.

    If every candidate leaves most people with an estimated radius,
    the honest answer is that k is too large for this population - a
    fact about k, not about the grid. Substituting the finest size
    would report a recommendation that does not work.
    """
    x = np.array([10.0, 20.0, 30.0, 40.0])
    y = np.array([10.0, 10.0, 10.0, 10.0])
    w = np.array([1000.0, 1000.0, 1000.0, 1000.0])
    a = unitsize.advise_unit(x, y, w, k_values=[5],
                             candidates=[100, 250, 500])
    assert a["recommended"][5] is None
    said = "\n".join(unitsize.format_advice(a))
    assert "NO candidate" in said and "too" in said


def test_both_shares_are_reported_because_they_differ():
    """BROKEN WITH: reporting only share_cells, or only share_people.

    They answer different questions and the gap between them is the
    point: a handful of dense cells is a small share of OUTPUT ROWS
    and a large share of PEOPLE, because dense cells are where people
    are. The engine's own message counts origins, so a reader needs
    both numbers to reconcile it with this table.
    """
    x = np.array(list(np.linspace(1, 90, 500)) + [1500.0, 2500.0, 3500.0])
    y = np.array([5.0] * 503)
    w = np.ones(503)
    a = unitsize.advise_unit(x, y, w, k_values=[100],
                             candidates=[100.0])
    row = a["rows"][0]
    assert row["share_cells"][100] < 0.3, "the dense cells are few"
    assert row["share_people"][100] > 0.9, "and hold nearly everybody"
    said = "\n".join(unitsize.format_advice(a))
    assert "of people" in said and "cells" in said


def test_the_thin_column_finds_a_grid_finer_than_the_data():
    """BROKEN WITH: removing thin_share.

    The lower bound, and the half of John's nearest-neighbour instinct
    that survives: below the data's own spacing, cells are mostly
    empty and the extra cells buy nothing. Measured on the project's
    own 100 m fixture, 25 m and 50 m produce the SAME cell count as
    the source resolution, because each pixel simply gets its own
    cell - which is the table telling the user where the floor is.
    """
    x = np.arange(0, 100) * 100.0
    y = np.zeros(100)
    w = np.ones(100)
    a = unitsize.advise_unit(x, y, w, k_values=[10],
                             candidates=[25, 50, 100, 1000])
    rows = {r["unit"]: r for r in a["rows"]}
    assert rows[25]["cells"] == rows[50]["cells"] == 100, (
        "below the data's own spacing the cell count must stop falling")
    assert rows[25]["thin_share"] == 1.0
    assert rows[1000]["thin_share"] < 1.0


# ------------------------------------------------------- the caching
def test_the_fingerprint_is_of_the_CONTENT():
    """BROKEN WITH: hashing len(x) and the bounding box instead of the
    arrays.

    The cache key. A path or a row count is the trap - BACKLOG 344
    exists because counting cells could not tell two tables apart, and
    a resumed run returned the first run's numbers. Same data must
    give the same digest; ANY change to a coordinate or a weight must
    change it.
    """
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([4.0, 5.0, 6.0])
    w = np.array([1.0, 1.0, 1.0])
    base = unitsize.fingerprint_points(x, y, w)
    assert base == unitsize.fingerprint_points(x, y, w)
    assert base == unitsize.fingerprint_points(list(x), list(y), list(w)), (
        "the digest must not depend on how the arrays were typed")

    moved = x.copy(); moved[1] += 1e-6
    assert unitsize.fingerprint_points(moved, y, w) != base
    heavier = w.copy(); heavier[0] = 2.0
    assert unitsize.fingerprint_points(x, y, heavier) != base
    assert unitsize.fingerprint_points(x, y, None) != base, (
        "unweighted and all-ones-weighted are different questions")
    # same bounding box, same count, different data
    other = np.array([1.0, 2.5, 3.0])
    assert unitsize.fingerprint_points(other, y, w) != base


# ------------------------------------------------- it changes nothing
def test_the_advisory_is_read_only_and_changes_no_default():
    """BROKEN WITH: having advise_unit write to cells.build_cells'
    default, or return a unit a caller might apply silently.

    THE RULE THAT MATTERS MOST. If EquiPop chose the unit, two runs on
    the same data could use different ones, the numbers would not be
    comparable, and a published figure would depend on a heuristic
    that might change between versions. Same rule the project applies
    to a meaningful zero (BACKLOG 116): reported, never substituted.
    """
    import inspect

    from equipop import cells as cells_mod

    before = inspect.signature(cells_mod.build_cells) \
        .parameters["unit_size"].default
    x = np.array([1.0, 2.0, 1000.0])
    y = np.array([1.0, 2.0, 1000.0])
    unitsize.advise_unit(x, y, None, k_values=[2])
    after = inspect.signature(cells_mod.build_cells) \
        .parameters["unit_size"].default
    assert before == after == 100.0, "the default moved"

    # AND IT HAS TO SAY SO IN WHAT IT PRINTS, not merely contain the
    # words somewhere. This asserted `"NOTHING IS CHANGED BY THIS" in
    # inspect.getsource(unitsize)`, and break-check showed that
    # deleting the line from the TABLE left the suite green - because
    # the same phrase appears in advise_on_run's own closing line, so
    # the source scan still found it. A grep over source is the
    # weakest kind of assertion and this project already knows it:
    # the 1.48.2 ensurepip test passed while asserting nothing.
    # Rendered output is the thing the user sees.
    a = unitsize.advise_unit(np.array([1.0, 2.0, 5000.0]),
                             np.array([1.0, 2.0, 5000.0]), None,
                             k_values=[2], candidates=[100.0, 5000.0],
                             current=100.0)
    table = "\n".join(unitsize.format_advice(a, current=100.0))
    assert "NOTHING IS CHANGED BY THIS" in table, (
        "the TABLE no longer tells the user it changed nothing")
    run = "\n".join(unitsize.advise_on_run(a, unit=100.0,
                                           unit_was_set=False))
    assert "NOTHING IS CHANGED BY THIS" in run, (
        "the run advisory no longer tells the user it changed nothing")


def test_an_unlocatable_row_is_not_part_of_the_question():
    """BROKEN WITH: dropping the isfinite mask from advise_unit.

    The convention from 1.53.3 (BACKLOG 380), applied here too: a row
    EquiPop cannot locate is not part of the question. Without the
    mask, np.floor(nan) raises on the cast and the advisory dies on
    ordinary data - the very data the advisory exists to describe.
    """
    x = np.array([1.0, 2.0, np.nan, 1000.0, np.inf])
    y = np.array([1.0, 2.0, 5.0, 1000.0, 5.0])
    w = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    a = unitsize.advise_unit(x, y, w, k_values=[2], candidates=[100.0])
    assert a["points"] == 3
    assert a["people"] == 3.0

    with pytest.raises(ValueError, match="no locatable points"):
        unitsize.advise_unit(np.array([np.nan]), np.array([np.nan]),
                             None, k_values=[2])


def test_coordinates_inside_the_degree_envelope_get_a_note_first():
    """BROKEN WITH: dropping the looks_like_degrees check, or putting
    the note after the table.

    FOUND BY RUNNING THE ADVISORY ON THE PROJECT'S OWN FIXTURE, which
    is how the whole thing should be checked. The WorldPop rasters are
    EPSG:4326, so their coordinates are DEGREES - and the candidate
    sizes are in whatever unit the coordinates are in, which is right
    (the engine is unit-agnostic by design) and is also a trap. '25'
    then means 25 degrees, the whole of Denmark falls into ONE cell,
    every row read `1 cell / 100.0% of people`, and the verdict came
    back "this population is too dense for that k at any of these
    sizes". Confident, specific, plausible, and about a completely
    different question - the worst kind of wrong answer.

    Projected to UTM the same data gives 44,529 cells at 100 m and
    8,322 at 250 m, which is the answer somebody can use.
    """
    rng = np.random.default_rng(4)
    lon = rng.uniform(8.0, 12.5, 3000)
    lat = rng.uniform(54.5, 57.5, 3000)
    w = np.ones(3000)

    a = unitsize.advise_unit(lon, lat, w, k_values=[100], current=100.0)
    assert a["maybe_degrees"] is True, "the envelope was not noticed"
    said = "\n".join(unitsize.format_advice(a, current=100.0))
    assert "DEGREE ENVELOPE" in said
    # BEFORE the table, not after the numbers it would invalidate.
    # Anchored on the separator rule rather than on the word "unit",
    # which appears in "[unitsize]" on line one - my first version of
    # this assertion compared against position 1 and failed.
    assert said.index("DEGREE ENVELOPE") < said.index("----"), (
        "the note sits below the numbers it is about")
    assert "DEGREE ENVELOPE" in "\n".join(
        unitsize.advise_on_run(a, unit=100.0, unit_was_set=False))

    # projected metres on the same places say nothing about it
    x = rng.uniform(440_000, 900_000, 3000)
    y = rng.uniform(6_040_000, 6_380_000, 3000)
    b = unitsize.advise_unit(x, y, w, k_values=[100], current=100.0)
    assert b["maybe_degrees"] is False
    assert "DEGREE ENVELOPE" not in "\n".join(unitsize.format_advice(b))


def test_the_degree_note_WARNS_and_still_advises():
    """BROKEN WITH: returning early from advise_on_run on
    maybe_degrees, which is exactly what the first version did.

    THE TEST THAT CAUGHT MY OWN OVERREACH. `looks_like_degrees` asks
    only whether every point fits inside the degree envelope, and its
    own docstring names the case it calls wrongly: "a local metric
    grid whose origin is inside the data". A campus study measured in
    metres from a corner of the site looks exactly like Denmark in
    degrees.

    So suppressing the recommendation is an ACTION taken on a guess,
    and the engine's rule for this test is warn, never act - the same
    rule that forbids silently projecting. The note names both
    readings and the advice still follows, because the user knows
    which one they are in and the software does not.
    """
    # coordinates 10 to 40: a perfectly good local metre grid, and
    # inside the degree envelope. This is the data the first version
    # refused to advise on.
    x = np.array([10.0, 20.0, 30.0, 40.0])
    y = np.array([10.0, 10.0, 10.0, 10.0])
    w = np.array([500.0, 500.0, 500.0, 500.0])
    a = unitsize.advise_unit(x, y, w, k_values=[100],
                             candidates=[100.0, 1000.0], current=1000.0)
    assert a["maybe_degrees"] is True

    said = unitsize.advise_on_run(a, unit=1000.0, unit_was_set=True)
    text = "\n".join(said)
    assert "DEGREE ENVELOPE" in text, "the note is missing"
    assert "WARNING" in text and "unit(1000)" in text, (
        "the note replaced the advice instead of preceding it - a "
        "heuristic that cannot tell must not decide")
    assert "EquiPop cannot tell the two apart" in text


@pytest.mark.parametrize("case,k,unit,was_set", [
    # every branch of advise_on_run that returns early
    ("the chosen unit does not saturate", 5000, 100.0, True),
    ("nothing better to recommend", 5000, 100.0, False),
    ("the chosen unit is not on the ladder", 20, 7.0, True),
])
def test_the_degree_note_survives_every_early_exit(case, k, unit,
                                                   was_set):
    """BROKEN WITH: `return []` instead of `return out` in any of
    advise_on_run's early exits - which is what 1.54.0 shipped, in
    three places.

    REVIEW F3. The note is appended to `out` at the top and three
    later branches returned a FRESH EMPTY LIST, throwing it away:
    measured, degree-like coordinates with a safe current unit gave a
    full report that carried the warning and an `advise_on_run` that
    returned zero lines.

    THE NOTE MATTERS MOST IN EXACTLY THOSE BRANCHES. They are the
    quiet ones - nothing else is printed - so the degree warning is
    not competing with other output, it is the only output there
    would have been.
    """
    rng = np.random.default_rng(4)
    lon = rng.uniform(8.0, 12.5, 200)
    lat = rng.uniform(54.5, 57.5, 200)
    a = unitsize.advise_unit(lon, lat, None, k_values=[k],
                             candidates=[100.0], current=100.0)
    assert a["maybe_degrees"] is True, f"{case}: not in the envelope"
    said = unitsize.advise_on_run(a, unit=unit, unit_was_set=was_set)
    assert said, f"{case}: advise_on_run returned nothing at all"
    assert "DEGREE ENVELOPE" in "\n".join(said), (
        f"{case}: the degree note was built and then discarded by an "
        f"early return")


def test_a_fractional_k_is_refused_not_quietly_rounded():
    """BROKEN WITH: `int(k)` in _resolve_ks, which is what 1.54.1
    shipped.

    REVIEW FINDING 3, 1.54.2. `k_values=[100.9]` came back as advice
    labelled k=100 with nothing said. The project's own door reader
    refuses a non-whole k for exactly this reason - k counts PEOPLE,
    and quietly rounding a count of people gives a plausible wrong
    answer (doors/numbers.py, BACKLOG 320/371) - so the public
    function was undoing a rule the typed doors enforce.

    `100.0` IS ACCEPTED and `100.9` is not. A Python caller writing
    100.0 means 100; the door reader is stricter about the typed
    STRING "100.0" because a decimal point a human put in a count is
    a fact about the human, which is a different question.

    A BOOL IS REFUSED. `k_values=[True]` was accepted as k=1, because
    bool is an int subclass - nobody's intention, and the sort of
    thing that arrives from a mis-indexed array.
    """
    x = np.array([1.0, 5000.0])
    y = np.array([1.0, 5000.0])

    def ask(k):
        return unitsize.advise_unit(x, y, None, k_values=[k],
                                    candidates=[100.0])

    # integral values, however spelled
    for good in (100, 100.0, np.int64(100), np.float64(100.0), "100"):
        assert ask(good)["k_values"] == [100], f"{good!r} was refused"

    for bad, why in ((100.9, "fraction"), (0.5, "fraction"),
                     (True, "true/false"), (False, "true/false"),
                     (0, "1 or more"), (-5, "1 or more"),
                     (float("nan"), "finite"), (float("inf"), "finite")):
        with pytest.raises(ValueError, match=why):
            ask(bad)
    # and a non-number is a refusal, not a TypeError from numpy
    for junk in ("abc", None, [1]):
        with pytest.raises(ValueError, match="not a number"):
            ask(junk)

    # the request key agrees - 100 and 100.0 are the SAME request
    fp = unitsize.fingerprint_points(x, y)
    same = dict(fingerprint=fp, tolerance=0.01, candidates=[100.0],
                self_rule="include")
    assert unitsize.request_key(k_values=[100], **same) == \
        unitsize.request_key(k_values=[100.0], **same)
    with pytest.raises(ValueError, match="fraction"):
        unitsize.request_key(k_values=[100.9], **same)


def test_a_cached_answer_has_to_be_consistent_with_itself():
    """BROKEN WITH: dropping the _advice_is_coherent call, or any one
    of its checks.

    REVIEW FINDING 5, 1.54.2. The request key says what question the
    advice answers and NOTHING about the answer, so editing the
    stored result passed: `recommended` to 999999, a cell count to
    -42, a share to 7.5 (750%), all accepted and returned.

    THE WORST ONE IS `applies`. Flipped to False under `include` it
    delivers the F1 defect straight out of a cache - the exact thing
    CACHE_VERSION 2 was bumped to keep out - and flipped to True
    under `exclude` it puts include-rule columns back on an exclude
    report.

    NOT A SECURITY BOUNDARY, and the 1.54.1 note was wrong to imply
    one: anybody who can edit the characteristic can recompute
    whatever we store beside it. This is corruption and version-skew
    detection. The honest claim, and the one the note now makes, is
    that a payload which does not describe a coherent answer to the
    request is refused.
    """
    import json

    # DATA CHOSEN SO EVERY CHECK IS REACHABLE, which break-check had
    # to teach me twice. The first fixture gave `recommended = None`
    # at every size, so the "does the recommendation follow from the
    # shares" branch was never entered and a break of it survived;
    # and its first row had one saturated cell, so editing the cell
    # count to zero was caught by `0 <= sat <= cells` instead of by
    # the cell-count check. Here 100 m qualifies and its row has no
    # saturated cells, so both are live.
    rng = np.random.default_rng(9)
    x = rng.uniform(0, 40000, 400)
    y = rng.uniform(0, 40000, 400)
    a = unitsize.advise_unit(x, y, None, k_values=[2],
                             candidates=[100.0, 1000.0, 5000.0])
    assert a["recommended"][2] == 100.0, (
        "the fixture no longer has a qualifying size, so the "
        "follows-from-the-shares check is unreachable from here")
    assert a["rows"][0]["saturated_cells"][2] == 0, (
        "the first row now has a saturated cell, so a cell-count "
        "edit would be caught by the sat/cells check instead")
    packed = unitsize.pack_advice(a)
    key = unitsize.request_key(
        fingerprint=a["fingerprint"], k_values=a["k_values"],
        tolerance=a["tolerance"],
        candidates=[r["unit"] for r in a["rows"]],
        self_rule=a["self_rule"])
    assert unitsize.unpack_advice(packed, key) is not None, (
        "the untouched payload does not even round-trip")

    def edited(fn):
        got = json.loads(packed)
        fn(got["a"])
        return unitsize.unpack_advice(json.dumps(got), key)

    def setrec(adv, v):
        adv["recommended"][str(a["k_values"][0])] = v

    # EACH CASE ISOLATES ONE CHECK. Break-check found four of these
    # surviving at first, not because the checks were missing but
    # because they overlapped: flipping `applies` also broke the
    # per-k shape, a recommendation of 999999 was also off the
    # ladder, a cell count of -42 also broke `0 <= sat <= cells`. So
    # each break was caught by a DIFFERENT check and none of them was
    # independently tested. The cases below are built to fail exactly
    # one check each.
    ladder = [float(r["unit"]) for r in a["rows"]]
    right = a["recommended"][2]
    wrong_on_ladder = next(u for u in ladder
                           if right is None or abs(u - right) > 1e-9)

    def flip_applies_and_blank(adv):
        """applies disagrees with the rule, and the per-k shape is
        made to MATCH the flipped value - so only the applies/rule
        check can object."""
        adv["applies"] = not adv["applies"]
        for r in adv["rows"]:
            for f in ("saturated_cells", "share_cells", "share_people"):
                r[f] = {k: None for k in r[f]}

    cases = {
        "a recommendation on the ladder that the shares do not support":
            lambda adv: setrec(adv, wrong_on_ladder),
        "a recommendation where no size qualifies":
            lambda adv: setrec(adv, ladder[0]) if right is None
            else setrec(adv, None),
        # cells AND sat set together, so `0 <= sat <= cells` still
        # holds and only the cell-count check can object
        "a cell count of zero":
            lambda adv: (adv["rows"][0].__setitem__("cells", 0),
                         adv["rows"][0]["saturated_cells"]
                         .__setitem__("2", 0)),
        "applies disagreeing with the rule, shape made to match":
            flip_applies_and_blank,
        # share_CELLS, because share_people feeds the
        # follows-from-the-shares check and an out-of-range value
        # there is caught by that instead - subsumption again, found
        # by break-check. share_cells is reported and nothing else
        # depends on it, so only the range check can object.
        "a cell share above 1":
            lambda adv: adv["rows"][0]["share_cells"].__setitem__("2", 7.5),
        "a negative cell share":
            lambda adv: adv["rows"][0]["share_cells"].__setitem__("2", -0.5),
        "a non-finite cell share":
            lambda adv: adv["rows"][0]["share_cells"].__setitem__(
                "2", float("inf")),
        "a people share above 1":
            lambda adv: adv["rows"][0]["share_people"].__setitem__("2", 7.5),
        "saturated cells exceeding the cell count":
            lambda adv: adv["rows"][0]["saturated_cells"].__setitem__(
                "2", 10 ** 9),
        "applies flipped against the rule":
            lambda adv: adv.__setitem__("applies", not adv["applies"]),
        "a tolerance outside 0-1":
            lambda adv: adv.__setitem__("tolerance", 5.0),
        "an unknown origin rule":
            lambda adv: adv.__setitem__("self_rule", "banana"),
        "a k map that does not match k_values":
            lambda adv: adv["rows"][0]["share_people"].__setitem__(
                "99", 0.0),
        "no rows at all":
            lambda adv: adv.__setitem__("rows", []),
    }
    for why, fn in cases.items():
        assert edited(fn) is None, (
            f"a cached payload with {why} was accepted and returned")

    # AND THE EXCLUDE SHAPE: numbers where there should be absences
    e = unitsize.advise_unit(x, y, None, k_values=[2],
                             candidates=[25.0, 50.0],
                             self_rule="exclude")
    epacked = unitsize.pack_advice(e)
    ekey = unitsize.request_key(
        fingerprint=e["fingerprint"], k_values=e["k_values"],
        tolerance=e["tolerance"],
        candidates=[r["unit"] for r in e["rows"]],
        self_rule=e["self_rule"])
    assert unitsize.unpack_advice(epacked, ekey) is not None
    got = json.loads(epacked)
    got["a"]["rows"][0]["saturated_cells"]["2"] = 0
    assert unitsize.unpack_advice(json.dumps(got), ekey) is None, (
        "an exclude payload carrying a measured-looking ZERO was "
        "accepted - which is how the F1 defect would come back")


def test_the_cache_key_accepts_exactly_what_the_advisory_accepts():
    """BROKEN WITH: removing request_key's own rule check, which
    break-check found surviving.

    TWO VALIDATORS THAT DISAGREE ARE WORSE THAN ONE. `advise_unit`
    refuses an unknown origin rule; `request_key` was accepting one
    and hashing it, so a caller could hold a perfectly-formed key for
    a request that can never be answered - and the symptom would be a
    cache that silently never hits, not an error. Same for a tolerance
    outside 0-1, an empty k list and an unusable ladder.

    ASSERTED AS A RELATION, not as two lists of bad values. Listing
    them twice is how the two come to disagree in the first place:
    this feeds the same inputs to both and requires them to agree
    about which are acceptable.
    """
    x = np.array([1.0, 2.0, 5000.0])
    y = np.array([1.0, 2.0, 5000.0])
    fp = unitsize.fingerprint_points(x, y)

    cases = [
        dict(self_rule="banana"),
        dict(self_rule="inclde"),
        dict(self_rule=""),
        dict(tolerance=5.0),
        dict(tolerance=0.0),
        dict(k_values=[0]),
        dict(k_values=[]),
        dict(candidates=[0.0, -1.0]),
        dict(candidates=[float("inf")]),
    ]
    for bad in cases:
        args = dict(k_values=[100], tolerance=0.01, self_rule="include")
        args.update(bad)
        advisory_refused = key_refused = None
        try:
            unitsize.advise_unit(x, y, None, **args)
        except ValueError as exc:
            advisory_refused = str(exc)
        try:
            unitsize.request_key(fingerprint=fp, **args)
        except ValueError as exc:
            key_refused = str(exc)
        assert (advisory_refused is None) == (key_refused is None), (
            f"{bad}: advise_unit "
            f"{'refused' if advisory_refused else 'accepted'} it and "
            f"request_key "
            f"{'refused' if key_refused else 'accepted'} it - a key "
            f"for a request that cannot be answered is a cache that "
            f"never hits and never says why")

    # and they agree on the ACCEPTED ones too: the same request,
    # spelled differently, must give the same key
    a = unitsize.request_key(fingerprint=fp, k_values=[100, 200],
                             tolerance=0.01, candidates=[100.0, 50.0],
                             self_rule="include")
    b = unitsize.request_key(fingerprint=fp, k_values=[200, 100],
                             tolerance=0.01, candidates=[50.0, 100.0],
                             self_rule="  INCLUDE ")
    assert a == b, (
        "the same request spelled differently gives two keys, so a "
        "cache would miss on a reordered numlist")


def test_the_degree_note_survives_a_k_the_advice_does_not_cover():
    """BROKEN WITH: `return []` in advise_on_run's `if not ks` branch.

    REVIEW F3's fourth exit, and the one my own first tests missed -
    break-check found it surviving. `ks` is filtered against the
    advice's own recommendations, so it empties only when a caller
    asks about a k the advice was not computed for: a door looping
    over several k values and reusing one cached advice does exactly
    that. The note must still come out.
    """
    rng = np.random.default_rng(4)
    lon = rng.uniform(8.0, 12.5, 200)
    lat = rng.uniform(54.5, 57.5, 200)
    a = unitsize.advise_unit(lon, lat, None, k_values=[20],
                             candidates=[100.0], current=100.0)
    assert a["maybe_degrees"] is True
    said = unitsize.advise_on_run(a, unit=100.0, unit_was_set=False,
                                  k_values=[999])
    assert said, "no k survived the filter and the note went with it"
    assert "DEGREE ENVELOPE" in "\n".join(said)
    # and nothing is invented about the k it knows nothing about
    assert "k=999" not in "\n".join(said)


def test_a_negative_population_is_refused_as_build_cells_refuses_it():
    """BROKEN WITH: dropping the negative-weight check.

    REVIEW F4. build_cells has refused a negative population since
    1.22.2 with a reason - k counts PEOPLE, so a neighbourhood cannot
    be grown against one - and this public function accepted it.

    MEASURED consequence, which is why it is not merely untidy:
    weights [10, -9] in two cells gave a total population of 1 and a
    saturated population of 10, so `share_people` came out as 10.0 -
    ONE THOUSAND PERCENT - and that number was then compared against
    the tolerance to choose a cell size.
    """
    x = np.array([10.0, 500.0])
    y = np.array([10.0, 10.0])
    with pytest.raises(ValueError, match="negative population"):
        unitsize.advise_unit(x, y, np.array([10.0, -9.0]),
                             k_values=[5], candidates=[100.0])
    # the same input, refused by the engine, in the same terms
    with pytest.raises(ValueError, match="negative population"):
        build_cells(pd.DataFrame({"E": x, "N": y, "w": [10.0, -9.0]}),
                    "E", "N", unit_size=100.0, weights="w")
    # a total of zero divides every share by nothing
    with pytest.raises(ValueError, match="total population"):
        unitsize.advise_unit(x, y, np.array([0.0, 0.0]), k_values=[5],
                             candidates=[100.0])
    # and a positive total still works, including fractional weights
    ok = unitsize.advise_unit(x, y, np.array([0.4, 0.6]), k_values=[1],
                              candidates=[100.0])
    assert ok["people"] == pytest.approx(1.0)


def test_a_tolerance_outside_zero_to_one_is_refused():
    """BROKEN WITH: dropping the tolerance range check.

    REVIEW F4. A tolerance is a SHARE. At 5.0 every candidate passes,
    so `max(good)` names the coarsest size on the ladder - a confident
    recommendation to use 5,000 m cells, from a threshold that can
    never bind. At 0 or below, nothing passes and the answer is always
    "too dense".
    """
    x = np.array([1.0, 2.0, 5000.0])
    y = np.array([1.0, 2.0, 5000.0])
    for bad in (5.0, 1.0, 0.0, -0.1, 100.0):
        with pytest.raises(ValueError, match="tolerance"):
            unitsize.advise_unit(x, y, None, k_values=[2],
                                 tolerance=bad)
    assert unitsize.advise_unit(x, y, None, k_values=[2],
                                tolerance=0.5)["tolerance"] == 0.5


def test_an_infinite_candidate_size_is_not_a_candidate():
    """BROKEN WITH: filtering candidates on `> 0` alone.

    REVIEW F4, found while checking it. `float("inf") > 0` is True, so
    inf passed the filter and produced a table row at an INFINITE cell
    size - which formats, sorts last, and would be recommended as the
    coarsest size within tolerance, because one infinite cell holding
    everybody has a saturated share of... whatever the arithmetic
    says. isfinite is the test that was meant. Zero, negative and nan
    were already filtered.
    """
    x = np.array([1.0, 2.0, 5000.0])
    y = np.array([1.0, 2.0, 5000.0])
    for bad in (float("inf"), float("-inf"), float("nan"), 0.0, -50.0):
        units = [r["unit"] for r in unitsize.advise_unit(
            x, y, None, k_values=[2], candidates=[bad, 100.0])["rows"]]
        assert units == [100.0], f"{bad} survived as a candidate"
        assert all(np.isfinite(u) for u in units)
    # current gets the same treatment
    units = [r["unit"] for r in unitsize.advise_unit(
        x, y, None, k_values=[2], candidates=[100.0],
        current=float("inf"))["rows"]]
    assert units == [100.0]
    # and a ladder with nothing usable left is a refusal, not an
    # empty table
    with pytest.raises(ValueError, match="candidate"):
        unitsize.advise_unit(x, y, None, k_values=[2],
                             candidates=[0.0, -1.0, float("nan")])


def test_row_misaligned_weights_are_refused():
    """BROKEN WITH: dropping the size check.

    Silently truncating or broadcasting would compute a real-looking
    table about a population that does not exist.
    """
    with pytest.raises(ValueError, match="row-aligned"):
        unitsize.advise_unit(np.arange(5.0), np.arange(5.0),
                             np.ones(4), k_values=[2])
