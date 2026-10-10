"""
unitsize.py - what cell size does this data want? (BACKLOG 385)

John's question, 9 October 2026: every machine assumes a unit size -
100 m in machines 1 and 2, 1000 m in 3 and 4 - and in Stata it has to
be named with `unit()` to change. Is there a cheap way to recommend
one? "This is not an easy task to settle - in many gis cases, you will
have many things close, and others a great distances - knowing the
unit size is a battle between computing time and detail."

THE CRITERION IS NOT NEAREST-NEIGHBOUR SPACING. That tells you when
cells start being EMPTY. It does not tell you when the answer stops
being an answer, and there is a precise threshold for that, named by
BACKLOG 95:

    the whole neighbourhood IS the origin cell, so the radius is not
    zero - it is unmeasured, and K HAS STOPPED BEING A PARAMETER

Once a cell holds >= k people, that origin's entire neighbourhood is
its own cell: Dist_k comes from selfpot.radius_for_k rather than from
the data, and asking for k=200 or k=2000 returns the same answer. The
engine already reports this AFTER a run. This module reports the same
number BEFORE one.

MEASURED, NOT ASSERTED. The claim this module rests on is that

    the number of cells whose own population >= k

equals the count fastcounts later reports as self-potential origins.
Checked against the engine on three shapes - one dense cell among
sparse ones, four cells at different densities, and weighted cells
where population is a WEIGHT rather than a row count - and it agrees
exactly in all of them. See tests/test_unitsize.py, which runs the
real engine and parses its own message rather than trusting this
docstring.

AND IT IS ONLY TRUE UNDER THE `include` ORIGIN RULE, which is the
published default. Under `exclude` the origin's own mass is removed
before the search, so its own cell CANNOT saturate it: measured, this
module predicts 1 and the engine reports 0. The report says which rule
it assumed rather than leaving the reader to find out.

WHY THERE IS NO SINGLE RECOMMENDED NUMBER. John's own objection is the
reason: density is heterogeneous, so one unit cannot be right
everywhere. A single number would hide exactly the variation that
makes the question hard. What this returns is a TABLE - the share
affected at each candidate unit, per k - so the trade-off is visible
and the choice stays the user's.

AND IT NEVER CHANGES A DEFAULT. If EquiPop chose the unit, two runs on
the same data could silently use different ones, the numbers would not
be comparable, and a published figure would depend on a heuristic that
might change between versions. Same rule the project already applies
to a meaningful zero (BACKLOG 116): refused or reported, never
substituted.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

__all__ = ["advise_unit", "fingerprint_points", "CANDIDATES",
           "DEFAULT_TOLERANCE", "format_advice", "advice_matrix",
           "advise_on_run", "pack_advice", "unpack_advice",
           "CACHE_VERSION", "MAX_PACKED", "ORIGIN_RULES", "INCLUDE",
           "EXCLUDE"]

# The two origin rules, named here rather than compared as bare
# strings at four call sites. They match selfrule.py's values; this
# module does not import it, because selfrule is reached through the
# engine and this one has to work before a run.
INCLUDE = "include"
EXCLUDE = "exclude"
ORIGIN_RULES = (INCLUDE, EXCLUDE)

# Bumped whenever the shape of a packed advice changes. A door reading
# a cache written by an older version must MISS rather than
# misinterpret: the version travels inside the string so the check
# cannot be forgotten at a call site.
#
# 2 in 1.54.1: a packed advice now carries `applies`, and the
# per-k fields can be null where the criterion does not hold. A
# version-1 string has neither, so reading one would present an
# exclude run with include-rule numbers - exactly the defect being
# fixed (review F1/F2). Bumped so no stored v1 advice can be read
# back after the change, including one already saved in a .dta.
CACHE_VERSION = 2

# A Stata characteristic holds far more than this; the limit is here so
# a door that caches cannot ever be the reason a run fails. Over it,
# caching is skipped and the advice is simply recomputed.
MAX_PACKED = 60_000

# A fixed ladder rather than one derived from the data, so two runs on
# the same data report comparable rows and a user learns to read it.
# The caller's own unit is always added, so their row is always there.
CANDIDATES = (25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0)

# "fewer than one answer in a hundred is estimated rather than
# measured". A default, named so it can be argued with.
DEFAULT_TOLERANCE = 0.01


def fingerprint_points(x, y, weights=None) -> str:
    """A digest of the coordinates and weights this advice is about.

    BACKLOG 385. The cache key, and it is CONTENT rather than a path or
    a row count: the same filename holding different data is the trap,
    and CellData.fingerprint() exists because counting rows could not
    tell two tables apart (BACKLOG 344). Same idiom - fixed order, raw
    little-endian float64 bytes - so the digest does not depend on how
    the arrays were typed.
    """
    h = hashlib.md5(usedforsecurity=False)
    xa = np.ascontiguousarray(x, dtype="<f8")
    ya = np.ascontiguousarray(y, dtype="<f8")
    h.update(f"equipop-unitsize-1|{xa.size}".encode())
    h.update(xa.tobytes())
    h.update(ya.tobytes())
    if weights is None:
        h.update(b"|unweighted|")
    else:
        h.update(b"|weights|")
        h.update(np.ascontiguousarray(weights, dtype="<f8").tobytes())
    return h.hexdigest()


def _resolve_rule(self_rule) -> str:
    """The origin rule, normalised and checked, in one place.

    `advise_unit` and `request_key` both need it, and two validators
    that disagree are worse than one: break-check found request_key
    accepting a rule the advisory refuses, which would hand a caller
    a perfectly-formed key for a request that can never be answered -
    a cache that silently never hits.
    """
    rule = str(self_rule).strip().lower()
    if rule not in ORIGIN_RULES:
        raise ValueError(
            f"[unitsize] originrule {self_rule!r} is not one of "
            f"{', '.join(ORIGIN_RULES)} - and it is not a label here, "
            "it decides whether this criterion applies at all")
    return rule


def _resolve_tolerance(tolerance) -> float:
    """The tolerance, checked, in one place - see _resolve_rule."""
    tolerance = float(tolerance)
    if not (0.0 < tolerance < 1.0):
        raise ValueError(
            f"[unitsize] tolerance {tolerance:g} is not a share "
            "between 0 and 1 - the default 0.01 means 'fewer than one "
            "answer in a hundred is estimated rather than measured'")
    return tolerance


def _resolve_ks(k_values) -> list:
    """The k values, resolved exactly once, and STRICTLY.

    Shared by advise_unit and request_key so a cache key cannot be
    computed from a differently-resolved request than the advice it
    is meant to validate.

    REVIEW FINDING 3, 1.54.2. This was `int(k)`, which SILENTLY
    TRUNCATES: `k_values=[100.9]` came back as advice labelled k=100
    with nothing said. That contradicts the project's own rule - the
    shared door reader refuses a non-whole k precisely because k
    counts PEOPLE and quietly rounding a count of people produces a
    plausible wrong answer (doors/numbers.py, BACKLOG 320/371) - and
    it contradicts this module's own comment that it validates what
    the engine would refuse.

    `100.0` IS ACCEPTED and `100.9` is not, which is the distinction
    that matters here. A Python caller writing 100.0 means 100; the
    door reader is stricter about the TYPED string "100.0" because a
    decimal point a human typed into a count is a signal about the
    human, and that is a different question from this one.

    A bool is refused rather than read as 0 or 1. `k_values=[True]`
    was being accepted as k=1, which is nobody's intention.
    """
    import math

    out = set()
    for raw in k_values:
        if isinstance(raw, bool):
            raise ValueError(
                f"[unitsize] k is {raw!r} - k counts PEOPLE, and a "
                "true/false value is not a number of them")
        try:
            val = float(raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"[unitsize] k {raw!r} is not a number") from None
        if not math.isfinite(val):
            raise ValueError(
                f"[unitsize] k is {raw!r} - k counts PEOPLE, so it "
                "has to be a finite whole number")
        if val != int(val):
            raise ValueError(
                f"[unitsize] k is {raw!r}, which is a fraction of a "
                "person. k counts PEOPLE in a neighbourhood, so it "
                "has to be a whole number - give "
                f"{int(val)} or {int(val) + 1}, not both.")
        if int(val) <= 0:
            raise ValueError(
                f"[unitsize] k is {raw!r} - a neighbourhood of "
                "nobody has no size, so k has to be 1 or more")
        out.add(int(val))
    if not out:
        raise ValueError("[unitsize] give at least one positive k")
    return sorted(out)


def _resolve_candidates(candidates, current) -> list:
    """The candidate ladder, resolved exactly once.

    `> 0` alone let `inf` through, because inf IS greater than zero -
    it produced a row at an infinite cell size (review F4). isfinite
    is the test that was meant.
    """
    cand = sorted({float(c) for c in (candidates or CANDIDATES)
                   if np.isfinite(float(c)) and float(c) > 0}
                  | ({float(current)} if current
                     and np.isfinite(float(current))
                     and float(current) > 0 else set()))
    if not cand:
        raise ValueError(
            "[unitsize] no usable candidate sizes - they have to be "
            "finite and greater than zero")
    return cand


def request_key(*, fingerprint, k_values, tolerance,
                candidates=None, current=None,
                self_rule=INCLUDE) -> str:
    """One digest of the WHOLE analytical request, for the cache.

    Review F2 fixed structurally rather than by adding arguments. The
    first fix gave `unpack_advice` optional `candidates` and
    `self_rule` parameters - which means a caller that forgets them
    gets no validation and a silent stale hit, and that is this
    project's most repeated defect (353, 368, 373, 380): the check
    exists and the path does not reach it.

    So the request is ONE value, `unpack_advice` REQUIRES it, and
    forgetting it is a TypeError rather than a quiet pass. Both sides
    build it through this function, and the ladder and k list are
    resolved by the same two helpers `advise_unit` uses, so a key
    cannot describe a differently-normalised request than the advice.
    """
    rule = _resolve_rule(self_rule)
    tolerance = _resolve_tolerance(tolerance)
    ks = _resolve_ks(k_values)
    cand = _resolve_candidates(candidates, current)
    h = hashlib.md5(usedforsecurity=False)
    h.update(f"equipop-unitsize-request-{CACHE_VERSION}|".encode())
    h.update(f"{fingerprint}|{rule}|{float(tolerance)!r}|".encode())
    h.update(("k:" + ",".join(str(k) for k in ks) + "|").encode())
    h.update(("c:" + ",".join(repr(c) for c in cand)).encode())
    return h.hexdigest()


def _cell_populations(x, y, w, unit):
    """People per cell at this unit, with no tree and no sort of the
    coordinates themselves.

    A floor division and a group-by. This is the whole reason the
    advice is cheap enough to give on every load: no neighbour search,
    no distance matrix, one pass per candidate.
    """
    gx = np.floor(x / unit).astype(np.int64)
    gy = np.floor(y / unit).astype(np.int64)
    # Pairing two int64 grid indices into one key. np.unique on a
    # 2-column array would sort rows and cost more; this is one pass
    # over a 1-D key.
    #
    # THE SPAN IS MEASURED, NEVER ASSUMED. A fixed multiplier wraps,
    # and not in a corner case: measured on a 120 km by 300 m strip, a
    # multiplier of 1000 merges two distinct cells, so 1,201 cells
    # become 1,200, the largest population reads 2.0 where every real
    # cell holds 1.0, and k=2 goes from 0 saturated cells to 1 - a
    # recommendation off the back of a hash collision. Checked against
    # build_cells, which grids by pandas group-by and pairs nothing.
    span = int(gy.max() - gy.min()) + 1
    key = (gx - gx.min()) * span + (gy - gy.min())
    uniq, inv = np.unique(key, return_inverse=True)
    pop = np.zeros(uniq.size, dtype=float)
    np.add.at(pop, inv, w)
    return pop


def advise_unit(x, y, weights=None, *, k_values=(100,),
                candidates=None, current=None,
                tolerance: float = DEFAULT_TOLERANCE,
                self_rule: str = "include") -> dict:
    """What cell size this data wants, per k. Read-only, no run.

    Returns a dict: `rows` (one per candidate unit), `recommended`
    ({k: unit} or {k: None} when no candidate qualifies), the
    `tolerance` and `self_rule` assumed, and the `fingerprint` of the
    data so a caller can cache it.

    Each row carries:
      unit                  the candidate
      cells                 how many cells the data makes - the cost
      thin_share            share of cells holding <= 1 person; high
                            means the grid is finer than the data and
                            the cost buys nothing
      saturated_cells[k]    cells whose own population >= k. THIS IS
                            THE NUMBER THE ENGINE WILL REPORT.
      share_cells[k]        those as a share of all cells - the share
                            of OUTPUT ROWS whose radius is estimated
      share_people[k]       the share of PEOPLE living in them - the
                            share of the POPULATION whose answer is
                            estimated, which is the larger number
                            because dense cells are where people are

    BOTH SHARES ARE REPORTED ON PURPOSE. They answer different
    questions and they differ a lot: 1% of cells can hold 40% of the
    people. The engine's own message counts origins (cells), so a
    reader has to be able to reconcile the two, and the recommendation
    uses the PEOPLE share because a study is about people.
    """
    # ---- the arguments, validated (BACKLOG 388, review F1 and F4) --
    # THIS IS A PUBLIC FUNCTION and it was taking anything: a
    # tolerance of 5.0, a self_rule of "banana", a candidate size of
    # inf, and a NEGATIVE population - which build_cells has refused
    # since 1.22.2 with a reason. An advisory that accepts inputs the
    # engine refuses is advice about a run that cannot happen.
    rule = _resolve_rule(self_rule)
    tolerance = _resolve_tolerance(tolerance)

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    if weights is None:
        w = np.ones(x.size, dtype=float)
    else:
        w = np.asarray(weights, dtype=float)
        if w.size != x.size:
            raise ValueError(
                f"[unitsize] {w.size} weights for {x.size} points - "
                "they have to be row-aligned")
        ok &= np.isfinite(w)
    # The convention, as everywhere else: a row EquiPop cannot locate
    # is not part of the question (BACKLOG 380).
    x, y, w = x[ok], y[ok], w[ok]
    if x.size == 0:
        raise ValueError("[unitsize] no locatable points to advise on")

    # A NEGATIVE POPULATION, refused for the reason build_cells gives:
    # k counts PEOPLE, so a neighbourhood cannot be grown against a
    # negative one. MEASURED consequence of allowing it - weights
    # [10, -9] in two cells gave a total population of 1, a saturated
    # population of 10, and therefore a share of 1,000%, which was
    # then compared against the tolerance to pick a cell size.
    neg = w < 0.0
    if neg.any():
        raise ValueError(
            f"[unitsize] the population goes down to {w.min():g} at "
            f"{int(neg.sum())} row(s), and k counts PEOPLE, so a "
            "neighbourhood cannot be grown against a negative "
            "population. Blank those rows, or use a column that "
            "treats a loss as a separate variable.")
    if not float(w.sum()) > 0.0:
        raise ValueError(
            "[unitsize] the total population is "
            f"{float(w.sum()):g} - there is no neighbourhood to "
            "advise about, and every share would divide by it")

    ks = _resolve_ks(k_values)

    # BACKLOG 385, FOUND BY RUNNING THIS ON THE PROJECT'S OWN WORLDPOP
    # FIXTURE. Those rasters are EPSG:4326, so the coordinates are
    # DEGREES - and a candidate of "25" is then 25 degrees, which puts
    # a whole country in one cell. The table came back with 1 cell on
    # every row and announced "this population is too dense for that k
    # at any of these sizes", which is a confident, wrong, and
    # perfectly plausible-looking answer.
    #
    # The engine is unit-agnostic on purpose (see cells.py) and this
    # does not change that: the candidates are in whatever unit the
    # coordinates are in, and that is right. What was missing was
    # saying so. `looks_like_degrees` is the project's existing test -
    # stata_bridge.degrees_warning and the GIS doors already use it,
    # so this is a third caller rather than a second copy.
    # It is `maybe_degrees` and not `degrees` because the test CANNOT
    # TELL, and the name has to say so. looks_like_degrees asks only
    # whether every point fits inside the degree envelope, and its own
    # docstring names the case it calls wrongly: "a local metric grid
    # whose origin is inside the data". A campus study in metres looks
    # exactly like Denmark in degrees.
    #
    # Which is why this WARNS AND STILL ADVISES. The first version of
    # this suppressed the recommendation outright, and a test with
    # coordinates 10 to 40 - a perfectly good local metre grid -
    # caught it: refusing to answer is an ACTION, and the engine's own
    # rule for this test is warn, never act. The warning covers both
    # readings and lets the user decide which they are in.
    maybe_degrees = False
    try:
        from .utm import looks_like_degrees
        maybe_degrees = bool(looks_like_degrees(x, y))
    except Exception:
        maybe_degrees = False

    cand = _resolve_candidates(candidates, current)

    # WHETHER THE CRITERION APPLIES AT ALL (review F1, BACKLOG 388).
    # `self_rule` used to be a LABEL: the numbers were computed the
    # same way under either rule and the report then announced which
    # rule it had assumed, so an `exclude` user was shown include-rule
    # counts under an exclude heading, followed by a footnote saying
    # those counts do not apply. Self-contradictory, and the sort of
    # wrong answer that reads as authoritative.
    #
    # MEASURED, and it is stronger than "unreliable": under exclude
    # the engine's saturated count is STRUCTURALLY ZERO. fastcounts
    # drops the origin's whole cell (`keep = idx != oi_range`), so the
    # origin's own cell cannot saturate it on any data at any cell
    # size - checked on four shapes including one where a single cell
    # holds every person, where include reports 1 and exclude 0.
    #
    # So there is nothing to predict, and the honest table omits the
    # columns rather than printing a zero that reads as "no problem
    # here". The cost and resolution-floor columns stay, because they
    # are about the grid and are true under either rule.
    applies = rule == INCLUDE

    total_people = float(w.sum())
    rows = []
    for u in cand:
        pop = _cell_populations(x, y, w, u)
        row = {"unit": u,
               "cells": int(pop.size),
               "thin_share": float((pop <= 1.0).mean()),
               "saturated_cells": {}, "share_cells": {},
               "share_people": {}}
        for k in ks:
            if not applies:
                # NOT ZERO - absent. A zero would be read as a
                # measurement, and the next step would be to pick the
                # coarsest size on the strength of it.
                row["saturated_cells"][k] = None
                row["share_cells"][k] = None
                row["share_people"][k] = None
                continue
            # `>= k - 1e-9`, matching fastcounts' own guard exactly,
            # and load-bearing for TWO separate reasons.
            #
            # In fastcounts it is BACKLOG 304: under `proportional`
            # overshoot the crossing cell contributes a fraction and
            # the sum comes back 99.99999999999999, so a bare `>= k`
            # misses the boundary.
            #
            # HERE it is the accumulation above. A WorldPop pixel
            # carries a FRACTIONAL population, so `pop` is a summed
            # float: measured, 1,000 pixels of 0.1 total
            # 99.9999999999986, short of 100 by 1.4e-12. Without the
            # slack this module would report 0 saturated cells where
            # the engine reports 1 - on exactly the data EquiPop is
            # usually pointed at. The two have to use the same
            # tolerance either way, or the advice is wrong precisely on
            # the boundary.
            hit = pop >= k - 1e-9
            row["saturated_cells"][k] = int(hit.sum())
            row["share_cells"][k] = float(hit.mean())
            row["share_people"][k] = float(
                pop[hit].sum() / total_people) if total_people > 0 else 0.0
        rows.append(row)

    recommended = {}
    for k in ks:
        if not applies:
            # NO RECOMMENDATION UNDER EXCLUDE, and the trap worth
            # naming: with every share structurally zero, `max(good)`
            # would return the COARSEST candidate on the ladder every
            # time - a confident recommendation to use 5,000 m cells,
            # produced by a criterion that measured nothing.
            recommended[k] = None
            continue
        # The COARSEST candidate within tolerance: coarsest is cheapest
        # and the tolerance is what protects the answer. None when the
        # data is too dense for any of them, which is a real answer and
        # not a failure - it means k is too large for this population.
        good = [r["unit"] for r in rows
                if r["share_people"][k] <= tolerance]
        recommended[k] = max(good) if good else None

    return {"rows": rows, "recommended": recommended,
            "tolerance": float(tolerance), "self_rule": rule,
            "applies": applies,
            "k_values": ks, "points": int(x.size),
            "people": total_people, "maybe_degrees": maybe_degrees,
            "fingerprint": fingerprint_points(x, y,
                                              None if weights is None else w)}


def _degrees_note() -> list:
    """The one note, so all four doors say it identically.

    FOUND BY RUNNING THE ADVISORY ON THE PROJECT'S OWN FIXTURE. The
    WorldPop rasters are EPSG:4326, so their coordinates are degrees,
    and the candidate sizes are in whatever unit the coordinates are
    in - which is correct, the engine is unit-agnostic by design, and
    is also a trap. Every row came back `1 cell / 100.0% of people`
    and the verdict read "this population is too dense for that k at
    any of these sizes": confident, specific, plausible, and about a
    different question.

    IT ASKS RATHER THAN DECIDES, because the test cannot tell. Both
    readings are named and the user knows which they are in - a thing
    the software does not.
    """
    return [
        "",
        "  !! EVERY POINT HERE FITS INSIDE THE DEGREE ENVELOPE "
        "(|x|<=180, |y|<=90).",
        "  The candidate sizes are in the SAME UNIT AS YOUR "
        "COORDINATES, so this matters:",
        "    - if these are longitude and latitude, '100' means 100 "
        "DEGREES, the whole",
        "      study area falls into one or two cells, and the table "
        "below is about",
        "      degrees rather than about a metre grid. Project first "
        "- -project- in",
        "      Stata, a projected CRS in QGIS or Pro - and ask again.",
        "    - if these are a local grid already in metres, the table "
        "is correct as it",
        "      stands and you can ignore this.",
        "  EquiPop cannot tell the two apart from the numbers alone, "
        "so it asks.",
    ]


def _exclude_note() -> list:
    """Why there are no k columns under originrule(exclude).

    Review F1. This replaced a label. The numbers were computed the
    same way under either rule, the report announced which rule it had
    assumed, and a footnote then said the counts do not apply - so an
    exclude user was shown `100.0% of people are in a cell that
    already holds k` about a thing that cannot occur for them.

    MEASURED: under exclude fastcounts drops the origin's whole cell,
    so its own cell cannot saturate it on any data at any cell size.
    On four shapes - including one where a single cell holds every
    person - include reports a saturated origin and exclude reports
    none.
    """
    return [
        "  originrule(exclude): THE k COLUMNS ARE NOT SHOWN, because "
        "under this rule they",
        "  would all be zero by construction. The origin's own cell "
        "is removed before the",
        "  search, so it can never be the whole neighbourhood - which "
        "is the thing those",
        "  columns count. k therefore keeps its meaning at every cell "
        "size here, and the",
        "  risk they warn about does not arise. What is left below "
        "still matters: the cost",
        "  of a size, and whether it is finer than your data.",
        "  No size is recommended, because there is no saturation to "
        "recommend against -",
        "  a tolerance applied to a column of zeroes would simply "
        "name the coarsest size",
        "  on the ladder every time.",
    ]


def advice_matrix(advice: dict):
    """The table as (values, colnames, rownames) for `r(advice)`.

    THE SHAPING IS IN THE ENGINE, not in the .ado. Same reason the
    doctor's report is: a door that formats its own numbers is a door
    that can disagree with the other three, and this project has
    shipped that bug five times (BACKLOG 353, 368, 373, 380). Stata
    stores what it is handed and nothing else.

    One row per candidate unit. Columns are fixed in this order so a
    user can index them positionally: unit, cells, thin, then
    sat/cellshare/peopleshare per k in ascending k.
    """
    ks = advice["k_values"]
    cols = ["unit", "cells", "thin"]
    for k in ks:
        cols += [f"sat_k{k}", f"shcells_k{k}", f"shpeople_k{k}"]
    vals, rownames = [], []
    for r in advice["rows"]:
        row = [r["unit"], float(r["cells"]), r["thin_share"]]
        for k in ks:
            # MISSING, not zero, when the criterion does not apply
            # (review F1). nan is what Stata reads back as `.`, and a
            # zero here would be indistinguishable from a measured
            # "no saturated cells at this size" - which is exactly the
            # confusion the exclude rule created in the first place.
            sat = r["saturated_cells"][k]
            row += [float("nan") if sat is None else float(sat),
                    float("nan") if r["share_cells"][k] is None
                    else r["share_cells"][k],
                    float("nan") if r["share_people"][k] is None
                    else r["share_people"][k]]
        vals.append(row)
        rownames.append(f"u{r['unit']:g}")
    return vals, cols, rownames


def advise_on_run(advice: dict, *, unit: float, unit_was_set: bool,
                  k_values=None) -> list:
    """What a door should say on an ORDINARY run. Often nothing.

    John's rule, and the reason this is not just `format_advice`: an
    advisory that prints a nine-row table on every run is noise, and
    noise is how a real warning gets missed. So:

      * the user did NOT set a unit -> tell them a coarser one would
        do, and only if a coarser one actually would. If the default
        is already the coarsest safe size there is nothing to say.
      * the user DID set one, and it saturates more than the tolerance
        -> warn, with their own number, because they chose it and
        nobody will check it again.
      * otherwise -> SILENCE. The common case.

    Returns a list of lines, empty when there is nothing to say.
    """
    rows = {r["unit"]: r for r in advice["rows"]}
    here = rows.get(float(unit))
    tol = advice["tolerance"]
    out = []

    if advice.get("maybe_degrees"):
        # The note comes first and the advice still follows it. This
        # used to return here with no recommendation, which was an
        # ACTION taken on a test that cannot tell degrees from a small
        # local metre grid - see the note in advise_unit.
        out.extend(_degrees_note())

    # EVERY EARLY EXIT FROM HERE ON RETURNS `out`, NEVER `[]` (review
    # F3). Three of them returned a fresh empty list, which silently
    # threw away the degree note built just above: measured, on
    # degree-like coordinates with a safe current unit, the full
    # report carried the note and advise_on_run returned zero lines.
    # The note is the one warning that matters MORE when there is
    # nothing else to say, because then nothing else is printed.
    ks = list(k_values) if k_values else advice["k_values"]
    ks = [k for k in ks if k in advice["recommended"]]
    if not ks:
        return out

    # UNDER `exclude` THERE IS NOTHING TO SAY (review F1). The
    # criterion counts origins whose own cell is the whole
    # neighbourhood, and under exclude that cannot happen - so a
    # warning would be about a risk this run does not carry, and a
    # recommendation would be a tolerance applied to zeroes. The
    # degree note still goes out, because that one is about the
    # coordinates rather than about the rule.
    if not advice.get("applies", True):
        return out

    if unit_was_set:
        # Their choice stands. Speak only about the cost of it, and
        # only per k that is actually hurt - a run with k=50 fine and
        # k=5000 saturating should say so about k=5000 alone.
        if here is None:
            return out
        hurt = [k for k in ks if here["share_people"][k] > tol]
        if not hurt:
            return out
        out.append(f"[unitsize] WARNING: at unit({unit:g}) some answers "
                   "are ESTIMATED rather than measured.")
        for k in hurt:
            rec = advice["recommended"][k]
            tail = (f" A finer {rec:g} m would bring it under "
                    f"{tol:.0%}." if rec is not None and rec < unit
                    else "")
            out.append(
                f"  k={k}: {here['share_people'][k]:.1%} of people are "
                f"in a cell that already holds k, so the whole "
                f"neighbourhood is that one cell and Dist_{k} comes "
                f"from the self-potential formula.{tail}")
        out.append("  This is your unit() and EquiPop has not changed "
                   "it. `equipop unit` shows the whole table.")
        return out

    # They did not choose. Recommend only a CHANGE, never the unit
    # they are already on.
    better = {k: advice["recommended"][k] for k in ks
              if advice["recommended"][k] is not None
              and advice["recommended"][k] != float(unit)}
    too_dense = [k for k in ks if advice["recommended"][k] is None]
    if not better and not too_dense:
        return out
    out.append(f"[unitsize] unit() was not given, so the {unit:g} m "
               "default is in use. This data may want another size:")
    for k in ks:
        rec = advice["recommended"][k]
        if rec is None:
            out.append(
                f"  k={k}: no candidate size keeps the estimated share "
                f"under {tol:.0%} - k is too large for this "
                "population, whatever the grid.")
        elif rec == float(unit):
            out.append(f"  k={k}: {unit:g} m is already the coarsest "
                       f"size within {tol:.0%}.")
        else:
            row = rows[rec]
            how = ("coarser, so cheaper" if rec > unit
                   else "finer, so more exact")
            cost = ""
            if here is not None and here["cells"]:
                cost = (f" - {row['cells']:,} cells against "
                        f"{here['cells']:,}")
            out.append(f"  k={k}: unit({rec:g}) is {how}{cost}.")
    out.append("  NOTHING IS CHANGED BY THIS - set unit() yourself if "
               "you want it. `equipop unit` shows the whole table.")
    return out


def pack_advice(advice: dict) -> str:
    """The advice as one string a door can store as metadata.

    John asked whether it could be "saved (as meta) to shorten the
    runtime in coming sessions". MEASURED: on 10 million rows the
    advisory costs 16 s - nine passes over the data, and `np.add.at`
    is already the fastest of the three groupings tried - while the
    fingerprint that validates a cache costs 0.55 s. So the cache
    earns its place on big data and is pointless on small (0.07 s at
    100,000 rows), which is exactly where it should be.

    THE FINGERPRINT TRAVELS INSIDE THE STRING. A cache keyed on
    anything else - a filename, a row count - is BACKLOG 344 again,
    where a resumed run returned the first run's numbers because
    counting rows could not tell two tables apart.
    """
    # NO `key` FIELD. The reader re-derives the key from the advice
    # itself, which is strictly stronger than trusting one written
    # alongside it, so storing one would be a value nothing reads.
    return json.dumps({"v": CACHE_VERSION, "a": advice},
                      separators=(",", ":"), sort_keys=True)


def unpack_advice(text: str, key: str) -> dict | None:
    """A packed advice back, or None - and None is not an error.

    EVERY WAY THIS CAN BE STALE RETURNS None. A wrong cached table is
    far worse than a recomputed one, so the burden is on the cache to
    prove it still applies - and what it has to match is THE WHOLE
    ANALYTICAL REQUEST, as one `key` from `request_key()`: the cache
    format version, the data's fingerprint, the k values, the
    tolerance, the candidate ladder and the origin rule. A caller
    treats None as "compute it".

    THE LADDER AND THE RULE USED TO BE MISSING (review F2), and the
    1.54.0 release note claimed "every way of being stale returns a
    miss", which was false. Reproduced: advice cached for candidates
    25 and 50 under include was returned, as a reported cache HIT, to
    a request for candidates 1,000 and 5,000 under exclude - the old
    two rows, with the old label, as the answer to a different
    question.

    `key` IS POSITIONAL AND REQUIRED on purpose. The first fix added
    optional keyword arguments, and an optional check is one a caller
    can forget - which would restore the same silent stale hit by a
    different route, and is the defect shape this project has shipped
    five times. Omitting it now raises TypeError.
    """
    if not text:
        return None
    try:
        got = json.loads(text)
    except Exception:
        return None
    if not isinstance(got, dict) or got.get("v") != CACHE_VERSION:
        return None
    a = got.get("a")
    if not isinstance(a, dict) or "rows" not in a or "recommended" not in a:
        return None
    if "applies" not in a:
        # A v2 string always carries it. Belt and braces: an advice
        # without it would be read as applying, which is the F1
        # defect.
        return None
    # THE KEY IS RE-DERIVED FROM THE STORED ADVICE BELOW, and that is
    # the only comparison. An earlier version also compared a `key`
    # field written into the payload - break-check showed that
    # deleting that comparison changed nothing, because re-deriving
    # is strictly stronger: a stored key only says what the writer
    # CLAIMED to answer, while the re-derived one says what the
    # content actually answers. Two checks where one is subsumed is
    # dead code that reads as defence.
    # JSON turns dict keys into strings, so the per-k maps come back
    # keyed "100" rather than 100. Put them back before anybody
    # indexes them with an int and silently gets a KeyError - or, far
    # worse, a .get() default.
    try:
        a["k_values"] = [int(k) for k in a.get("k_values", [])]
        a["recommended"] = {int(k): v for k, v in a["recommended"].items()}
        for r in a["rows"]:
            for field in ("saturated_cells", "share_cells", "share_people"):
                r[field] = {int(k): v for k, v in r[field].items()}
    except Exception:
        return None
    # The key covers the REQUEST: fingerprint, k values, tolerance,
    # ladder and rule, in one comparison a caller cannot half-make.
    # It is re-derived from the stored advice so the payload cannot
    # assert its own identity.
    try:
        mine = request_key(fingerprint=a["fingerprint"],
                           k_values=a["k_values"],
                           tolerance=a["tolerance"],
                           candidates=[r["unit"] for r in a["rows"]],
                           self_rule=a["self_rule"])
    except Exception:
        return None
    if mine != key:
        return None
    # ...AND THE RESULT HAS TO BE CONSISTENT WITH ITSELF (review
    # finding 5, 1.54.2). The key says nothing about the stored
    # ANSWER, so editing `recommended` to 999999, a cell count to
    # -42, or a share to 7.5 was accepted and returned. The worst of
    # those is `applies`: flipped to false under `include`, it
    # delivers the F1 defect out of a cache, which is the thing
    # CACHE_VERSION 2 was bumped to prevent.
    #
    # NOT A SECURITY BOUNDARY, and the 1.54.1 note was wrong to imply
    # one - anybody who can edit the characteristic can recompute
    # whatever we put beside it. This is corruption and
    # version-skew detection, and the honest claim is that a payload
    # which does not describe a coherent answer to the request is
    # refused.
    if not _advice_is_coherent(a):
        return None
    return a


def _advice_is_coherent(a: dict) -> bool:
    """Does this stored advice describe a possible answer?

    Review finding 5. Every check here is something `advise_unit`
    guarantees on the way out, so a payload failing one of them did
    not come from it intact.
    """
    try:
        if a["self_rule"] not in ORIGIN_RULES:
            return False
        applies = a["applies"]
        if not isinstance(applies, bool):
            return False
        # `applies` is DERIVED from the rule, so the two cannot
        # disagree. This is the check that keeps F1 out of the cache.
        if applies != (a["self_rule"] == INCLUDE):
            return False
        ks = [int(k) for k in a["k_values"]]
        units = [float(r["unit"]) for r in a["rows"]]
        if not ks or not units:
            return False
        if sorted(set(ks)) != ks or sorted(set(units)) != units:
            return False
        tol = float(a["tolerance"])
        if not (0.0 < tol < 1.0):
            return False
        if set(a["recommended"]) != set(ks):
            return False
        # NO SEPARATE "is it on the ladder" CHECK. Break-check showed
        # it was subsumed: the follows-from-the-shares check below
        # accepts only `None` or the coarsest qualifying size, and
        # both of those are on the ladder by construction. Two checks
        # where one implies the other means neither is independently
        # tested - each break is caught by the other - so the
        # implied one is gone rather than left as decoration. Same
        # reasoning that removed the stored cache key in 1.54.1.
        for r in a["rows"]:
            if int(r["cells"]) < 1:
                return False
            if not 0.0 <= float(r["thin_share"]) <= 1.0:
                return False
            for field in ("saturated_cells", "share_cells",
                          "share_people"):
                if set(int(k) for k in r[field]) != set(ks):
                    return False
            for k in ks:
                sat = r["saturated_cells"][k]
                sc = r["share_cells"][k]
                sp = r["share_people"][k]
                if not applies:
                    # under exclude they are absent, never numbers
                    if (sat, sc, sp) != (None, None, None):
                        return False
                    continue
                if sat is None or sc is None or sp is None:
                    return False
                if not 0 <= int(sat) <= int(r["cells"]):
                    return False
                for share in (float(sc), float(sp)):
                    if not np.isfinite(share) or not 0.0 <= share <= 1.0:
                        return False
        if applies:
            # and the recommendation has to follow from the shares it
            # was supposedly derived from: the coarsest size within
            # tolerance, or none when no size is.
            by_unit = {float(r["unit"]): r for r in a["rows"]}
            for k in ks:
                good = [u for u in units
                        if float(by_unit[u]["share_people"][k]) <= tol]
                want = max(good) if good else None
                got = a["recommended"][k]
                if want is None:
                    if got is not None:
                        return False
                elif got is None or abs(float(got) - want) > 1e-9:
                    return False
    except Exception:
        return False
    return True


def format_advice(advice: dict, current=None) -> list:
    """The table as lines a door can print. One place, four doors."""
    ks = advice["k_values"]
    out = [
        f"[unitsize] {advice['points']:,} locatable points, "
        f"{advice['people']:,.0f} people. What cell size does this "
        "data want?",
    ]
    if advice.get("maybe_degrees"):
        # FIRST, not in a footnote. If these really are degrees then
        # every number below is wrong in a way that looks right, so
        # the reader has to meet this before the table.
        out.extend(_degrees_note())
    # UNDER `exclude` THE k COLUMNS ARE NOT PRINTED AT ALL (review
    # F1). They used to be printed as include-rule numbers under an
    # exclude heading, with a footnote below saying they do not apply.
    # Omitting them is the only honest shape: the cost and
    # resolution-floor columns are about the GRID and hold under
    # either rule, and the saturation columns are about a thing that
    # cannot happen under exclude.
    applies = advice.get("applies", True)
    W = 24
    if applies:
        # One column pair per k, headed so the label sits over its own
        # numbers. Width is fixed rather than computed because a table
        # whose columns move between runs is harder to read.
        head = (f"  {'unit':>8} {'cells':>10} {'thin':>5}  "
                + "".join(f"{('k=' + format(k, ',')):^{W}}" for k in ks))
        sub = (f"  {'':>8} {'':>10} {'':>5}  "
               + "".join(f"{'cells':>11}{'of people':>13}" for _k in ks))
    else:
        out.append("")
        out.extend(_exclude_note())
        head = f"  {'unit':>8} {'cells':>10} {'thin':>5}"
        sub = ""
    out.append(head.rstrip())
    if sub:
        out.append(sub.rstrip())
    out.append("  " + "-" * (len(head) - 2))
    for r in advice["rows"]:
        mark = (" <- yours" if current
                and abs(r["unit"] - float(current)) < 1e-9 else "")
        line = (f"  {r['unit']:>8,.0f} {r['cells']:>10,} "
                f"{r['thin_share']:>4.0%}  ")
        if applies:
            for k in ks:
                line += (f"{r['saturated_cells'][k]:>11,}"
                         f"{r['share_people'][k]:>12.1%} ")
        out.append(line.rstrip() + mark)
    out.append("")
    if applies:
        out.append("  'k=' columns: cells whose OWN population already "
                   "reaches k, so the whole")
        out.append("  neighbourhood is that cell - Dist_k is then "
                   "ESTIMATED, not measured, and k")
        out.append("  has stopped being a parameter for them. 'of "
                   "people' is the share of PEOPLE")
        out.append("  living in such cells, which is the larger number "
                   "because that is where people are.")
    out.append("  'thin' is cells holding one person or none: high "
               "means the grid is finer")
    out.append("  than the data and the extra cells buy nothing.")
    out.append("")
    if applies:
        for k in ks:
            rec = advice["recommended"][k]
            if rec is None:
                out.append(
                    f"  k={k}: NO candidate keeps the estimated share "
                    f"under {advice['tolerance']:.0%} - this population "
                    "is too dense for that k at any of these sizes, "
                    "which is a fact about k rather than about the "
                    "grid.")
            else:
                row = next(r for r in advice["rows"] if r["unit"] == rec)
                out.append(
                    f"  k={k}: the coarsest size keeping the estimated "
                    f"share under {advice['tolerance']:.0%} is "
                    f"{rec:,.0f} m ({row['cells']:,} cells, "
                    f"{row['share_people'][k]:.1%} of people "
                    "estimated).")
        out.append("")
        out.append(f"  Assumes originrule({advice['self_rule']}), which "
                   "is what you are running. Under")
        out.append("  'exclude' these counts would not apply at all - "
                   "run it again that way to")
        out.append("  see what does.")
    out.append("  NOTHING IS CHANGED BY THIS: the unit stays whatever "
               "you set or defaulted to.")
    return out
