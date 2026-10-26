"""
opportunity.py - theta(k): how much of an outcome's inequality lines
up with the kind of neighbourhood people come from, at each
neighbourhood size k.

v1.62.0, BACKLOG 405 step 4 (and 436). John's rulings for the test
round, 25 October 2026: "let say 10 [groups], low education and yes -
family background is in for individuals that are below ca 40 years
old". v1.62.1 (BACKLOG 440-441): corrected after the external review
of 1.62.0 - see "WHAT 1.62.1 CHANGED" below.

THE STEPS, as John was given them before a line of this was written:

  1. An OUTCOME and the PEOPLE it is measured on - adult income, say,
     for everyone aged 30-40, each placed where they grew up.
  2. One neighbourhood CHARACTER - the share of the k nearest people
     with low education - measured by EquiPop around each person, for
     several k at once.
  3. TYPES. Everyone is lined up by that character and the line is
     cut into equal-sized groups (10 by default). A type is one group:
     "the tenth from the most disadvantaged neighbourhoods at this k".
  4. The outcome's inequality is split exactly into the part BETWEEN
     the types' averages and the part WITHIN them (MLD by default;
     Theil when the outcome has zeros). theta(k) = between / total.
  5. Repeated for each k: the profile shows at which scale the
     neighbourhood lines up most with the outcome.

WHY EQUAL-SIZED GROUPS, AND WHY TEN. Measured on a synthetic town with
the effect planted at 800 people (tests/test_opportunity.py rebuilds
it): the PEAK of the profile was at 800 whichever way the types were
formed, so the choice moves the level, not the scale. Too few groups
understate; fixed cut-offs (10/20/30/50%) lost their outer groups as k
grew (five types at k=25, three from k=3,200), so the k's stopped
being comparable, and are not offered.

WHAT EVERY RUN REPORTS BESIDE theta, and why:
  theta_nogroups - the same share with no groups at all: the
      inequality of the outcome PREDICTED from the character (a
      quadratic in it, fitted to the outcome itself), over the total.
      It is what theta approaches as the groups get finer without
      getting noisier, so it is the check on step 3: if theta is far
      below it, the groups are too coarse.
  noise, noise_p95, p_value - the outcome SHUFFLED among the same
      PEOPLE `shuffles` times (99 by default), the types left where
      they are: the mean and 95th percentile of theta under chance,
      and the permutation p-value (1 + shuffles at or above theta) /
      (1 + shuffles). With no relationship at all theta is not zero:
      noise between group means reads as inequality between them,
      about (groups - 1) / people.
  smallest_group - and, as in machine 2 (John's ruling, 12 October),
      a profile with any type under `min_group` people is EMPTY, not
      reported. `note` says why a row is empty.

ON TOP OF FAMILY (`family=`). "Neighbourhood alone" mixes the place
with who lives there: if families with low-educated parents cluster,
the neighbourhood character lines up with income even where the place
itself does nothing. So with a family field the run also forms types
from neighbourhood group x family category and reports theta_on_top =
theta(both) - theta(family). Its chance distribution shuffles the
outcome WITHIN family categories, which keeps family's part exactly
and removes the neighbourhood's.

THE PERSON'S OWN CELL IS LEFT OUT of their neighbourhood by default
(self_rule="exclude"). Included, a small neighbourhood is largely the
person's own household, and theta at small k would measure family
twice. Other people in the same cell are left out with it.

WHAT 1.62.1 CHANGED (external review of 1.62.0, every point
reproduced first):
  - `weight=` now also weights the neighbourhood when no separate
    context is given (it counted every row as one person there).
  - The shuffles move PEOPLE: a row of weight 5 is five people, not
    one block of five. With fractional weights "people" has no clear
    meaning, so the chance columns are left empty and the run says so.
  - The shuffles are made one at a time: memory no longer grows with
    their number (1.62.0 held all of them, ~320 bytes a person with
    family - 1.6 GB for five million people).
  - The person who completes a group belongs to it: 300 distinct
    values make ten groups of exactly 30 (it was 29 to 31).
  - theta_nogroups fits the outcome, not its log (John, 26 October):
    the log fit is a different quantity and could exceed 1.
  - The 95th percentile and the p-value (John, 26 October); a peak is
    named only where p <= 0.05.
  - A constant outcome, a character with no usable value, and
    fractional or negative settings are refused in words.

AN ECOLOGICAL OBJECT unless the people are individuals with their own
outcome and background - registers, in practice. On gridded census or
WorldPop counts it describes places, not opportunity (PROPOSALS.md).

EX ANTE ONLY (John's ruling 12 October; ex post is later).
"""

from __future__ import annotations

import contextlib
import io
import math
import time

import numpy as np
import pandas as pd

#: John, 25 October 2026: "for a test round - let say 10".
DEFAULT_GROUPS = 10
#: Shuffles behind the chance columns. 99 lets the p-value go down to
#: 0.01; each costs one pass over the people per k, and memory does
#: not grow with them (v1.62.1).
DEFAULT_SHUFFLES = 99
#: As machine 2's split (decompose.DEFAULT_MIN_GROUP): John's ruling.
DEFAULT_MIN_GROUP = 30.0
#: A family field is a circumstance with a few categories.
MAX_FAMILY_LEVELS = 20
INDICES = ("mld", "theil")
#: At or below this, a p-value counts as "above chance" in the
#: messages - so 19 shuffles (smallest p 1/20) can already say so.
ALPHA = 0.05


class OpportunityError(ValueError):
    """A theta_profile input that cannot give a meaningful answer."""


# ----------------------------------------------------------- arithmetic
def _wmean(y, w):
    return float(np.sum(w * y) / np.sum(w))


def _index(y, w, index):
    """MLD or Theil of y with weights w (y already scaled near 1)."""
    mu = _wmean(y, w)
    if index == "mld":
        return float(np.sum(w * np.log(mu / y)) / np.sum(w))
    r = y / mu
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(r > 0, r * np.log(r), 0.0)
    return float(np.sum(w * t) / np.sum(w))


def _between(y, w, codes, index):
    """The between-group part of MLD or Theil: each person given their
    group's mean. Exact for both indices (they decompose additively)."""
    W = np.bincount(codes, weights=w)
    S = np.bincount(codes, weights=w * y)
    ok = W > 0
    s = W[ok] / W[ok].sum()
    mu_g = S[ok] / W[ok]
    mu = float(np.sum(w * y) / np.sum(w))
    if index == "mld":
        return float(np.sum(s * np.log(mu / mu_g)))
    r = mu_g / mu
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(r > 0, r * np.log(r), 0.0)
    return float(np.sum(s * t))


def _equal_groups(c, w, groups):
    """Codes 0..G-1 cutting the people, lined up by c, into `groups`
    groups of equal WEIGHT.

    THE CUT (v1.62.1): a group ends with the person whose weight
    completes it, and everybody with that person's value goes with
    them - so 300 distinct values make ten groups of exactly 30. (1.62.0
    sent the completing person UP, which made 29, 30 ... 30, 31, and a
    profile of 300 people with min_group 30 came out empty.) People
    with the same c always share a group - a cell's people cannot be
    split - so ties at a cut make groups unequal, and heavy ties can
    merge two; the run reports how many were formed and the smallest."""
    order = np.argsort(c, kind="stable")
    cw = np.cumsum(w[order])
    targets = cw[-1] * np.arange(1, groups) / groups
    # a tolerance, so 0.1 + 0.2 reaching 0.3 counts as reaching it
    at = np.searchsorted(cw, targets * (1 - 1e-12))
    edges = c[order][np.minimum(at, c.size - 1)]
    raw = np.searchsorted(edges, c, side="left")
    _u, codes = np.unique(raw, return_inverse=True)
    return codes.astype(np.int64)


def _fitted_share(y, w, X, index):
    """Inequality of the outcome PREDICTED from X, over the total - the
    no-groups reading.

    v1.62.1 (John, 26 October): the prediction is of the OUTCOME, a
    weighted least-squares fit of y on X - the conditional mean that
    theta's group means approach as the groups get finer. 1.62.0 fitted
    log y for MLD, which predicts a geometric mean instead: a different
    quantity, and the review measured it at 1.04 of the total. Empty if
    any prediction is not positive (neither index is defined there)."""
    sw = np.sqrt(w)
    b, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    pred = X @ b
    if not np.all(pred > 0):
        return np.nan
    tot = _index(y, w, index)
    return _index(pred, w, index) / tot if tot > 0 else np.nan


def _design(c, fam_codes=None, fam_levels=0):
    cols = [np.ones_like(c), c, c * c]
    if fam_codes is not None:
        cols += [(fam_codes == j).astype(float) for j in range(1, fam_levels)]
    return np.column_stack(cols)


def _family_design(fam_codes, fam_levels, n):
    return np.column_stack([np.ones(n)] + [
        (fam_codes == j).astype(float) for j in range(1, fam_levels)])


class _Chance:
    """The outcome shuffled among PEOPLE, one shuffle at a time.

    v1.62.1. Rows are expanded to people (a row of weight 5 is five
    people) once per k; each shuffle then permutes the people's
    outcomes IN PLACE and adds them up by group - so memory is a few
    arrays of one value per person, whatever the number of shuffles.
    1.62.0 moved a weighted row as one block and kept every
    permutation.

    The total inequality is the same in every shuffle (the same people
    and values, in another order), and so - within family - is
    family's own between part. Only the grouped part is recomputed,
    from group sizes that do not change either."""

    def __init__(self, y, w, index):
        self.index = index
        self.count = np.asarray(w).astype(np.int64)
        self.y = np.repeat(y, self.count)
        self.mu = float(self.y.mean())
        self.total = _index(self.y, np.ones_like(self.y), index)

    def _between(self, y, codes, size):
        S = np.bincount(codes, weights=y, minlength=size.size)
        ok = size > 0
        s = size[ok] / size[ok].sum()
        mu_g = S[ok] / size[ok]
        if self.index == "mld":
            return float(np.sum(s * np.log(self.mu / mu_g)))
        r = mu_g / self.mu
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(r > 0, r * np.log(r), 0.0)
        return float(np.sum(s * t))

    def anywhere(self, rng, shuffles, codes):
        """theta for each shuffle, the outcome moved among everybody."""
        g = np.repeat(codes, self.count)
        size = np.bincount(g).astype(float)
        work = self.y.copy()
        out = np.empty(shuffles)
        for i in range(shuffles):
            rng.shuffle(work)
            out[i] = self._between(work, g, size) / self.total
        return out

    def within(self, rng, shuffles, both, fam):
        """theta(both) - theta(family) for each shuffle, the outcome
        moved only among people of the same family category."""
        gf = np.repeat(fam, self.count)
        order = np.argsort(gf, kind="stable")
        gb = np.repeat(both, self.count)[order]
        gf = gf[order]
        work = self.y[order]                 # a new array: y is kept
        size_b = np.bincount(gb).astype(float)
        fam_part = self._between(work, gf, np.bincount(gf).astype(float))
        cuts = np.flatnonzero(np.diff(gf)) + 1
        bounds = list(zip(np.r_[0, cuts], np.r_[cuts, gf.size]))
        del gf, order
        out = np.empty(shuffles)
        for i in range(shuffles):
            for a, z in bounds:
                if z - a > 1:
                    rng.shuffle(work[a:z])   # a view: shuffled in place
            out[i] = (self._between(work, gb, size_b) - fam_part) \
                / self.total
        return out


def _chance_columns(draws, observed):
    """mean, 95th percentile and permutation p-value of `observed`."""
    if draws is None or draws.size == 0 or not np.isfinite(observed):
        return np.nan, np.nan, np.nan
    p = (1 + int(np.sum(draws >= observed - 1e-15))) / (1 + draws.size)
    return float(draws.mean()), float(np.quantile(draws, 0.95)), p


# --------------------------------------------------------------- input
def _numeric(df, col, what):
    if col not in df.columns:
        raise OpportunityError(
            f"[opportunity] {what} '{col}' is not a column - found "
            f"{list(df.columns)}")
    return pd.to_numeric(df[col], errors="coerce").to_numpy(float)


def _whole(value, what, least):
    """A whole number of at least `least`, or a refusal in words. A
    fractional value is REFUSED, never truncated (v1.62.1: k = 10.9
    ran as 10) - the project's rule for k and cell sizes everywhere."""
    if isinstance(value, (bool, np.bool_)):
        raise OpportunityError(
            f"[opportunity] {what} must be a whole number, not "
            f"{value!r}.")
    try:
        v = float(value)
    except (TypeError, ValueError, OverflowError):
        raise OpportunityError(
            f"[opportunity] {what} must be a whole number; got "
            f"{value!r}.") from None
    if not math.isfinite(v) or v != math.floor(v):
        raise OpportunityError(
            f"[opportunity] {what} must be a whole number; got "
            f"{value!r} - it is refused rather than rounded.")
    if v < least:
        raise OpportunityError(
            f"[opportunity] {what} must be {least} or more; got "
            f"{value!r}.")
    return int(v)


def _family_codes(series):
    """Whole-number codes for the family field, missing as -1."""
    miss = series.isna() | (series.astype(str).str.strip() == "")
    levels = sorted(series[~miss].unique(), key=lambda v: (str(type(v)),
                                                           str(v)))
    if len(levels) > MAX_FAMILY_LEVELS:
        raise OpportunityError(
            f"[opportunity] the family field has {len(levels)} distinct "
            f"values; a circumstance has a few categories (at most "
            f"{MAX_FAMILY_LEVELS}). Is it an identifier, or a number "
            "that should be grouped first?")
    lut = {v: i for i, v in enumerate(levels)}
    codes = np.array([lut.get(v, -1) if not m else -1
                      for v, m in zip(series.tolist(), miss.tolist())],
                     dtype=np.int64)
    return codes, [str(v) for v in levels]


# ------------------------------------------------------------ the run
def theta_profile(people: pd.DataFrame, *, outcome: str, character: str,
                  k_values, x: str = "x", y: str = "y",
                  family: str | None = None,
                  context: pd.DataFrame | None = None,
                  context_x: str | None = None,
                  context_y: str | None = None,
                  context_weight: str | None = None,
                  weight: str | None = None,
                  groups: int = DEFAULT_GROUPS, index: str = "mld",
                  unit_size: float = 100.0, self_rule: str = "exclude",
                  shuffles: int = DEFAULT_SHUFFLES,
                  min_group: float = DEFAULT_MIN_GROUP,
                  seed: int = 1, report: bool = True) -> pd.DataFrame:
    """theta(k), one row per k. See the module docstring for the method.

    people : one row per person (or per group of people, with
        `weight` - a whole number of people per row for the chance
        columns): METRIC coordinates `x`, `y`, the `outcome`, and
        `family` if given.
    character : the column whose neighbourhood SHARE (a 0/1 field) or
        MEAN (any number) defines the types - e.g. low_edu.
    context : the population the neighbourhood is made of, if not the
        people themselves - all adults, say, around people aged 30-40.
        Its own coordinates (`context_x`, `context_y`, default `x`,
        `y`), the `character` column, and `context_weight` (people per
        row) if rows are not single persons. Without `context`, the
        neighbourhood is made of the people, weighted by `weight`.
    family : a categorical column of the people - parents' education,
        say. Adds the columns on top of family.
    groups : equal-sized groups per k (default 10).
    index : "mld" (default; the outcome must be above zero) or
        "theil" (zeros allowed).
    self_rule : "exclude" (default: a person's own cell is not their
        neighbourhood) or "include".
    shuffles : draws behind noise, noise_p95 and p_value (default 99;
        0 for none).

    Columns: k, people, no_neighbourhood, groups, smallest_group,
    total, between, theta, theta_nogroups, noise, noise_p95, p_value -
    with `family` also family_categories, theta_family, smallest_both,
    theta_both, theta_on_top, theta_nogroups_on_top, noise_on_top,
    noise_on_top_p95, p_value_on_top - and note, which says why a row
    is empty. theta values are SHARES (0.06 = 6%).
    """
    from .cells import build_cells, grid_midpoints
    from . import fastcounts as FC
    say = print if report else (lambda *a, **k: None)

    # --- the settings, refused in words rather than coerced
    if index not in INDICES:
        raise OpportunityError(
            f"[opportunity] index must be one of {', '.join(INDICES)}; "
            f"got {index!r}.")
    groups = _whole(groups, "groups", 2)
    ks = sorted({_whole(k, "every k", 1)
                 for k in np.atleast_1d(np.asarray(k_values, dtype=object))})
    if not ks:
        raise OpportunityError("[opportunity] k_values is empty - give "
                               "one or more whole numbers of people.")
    shuffles = _whole(shuffles, "shuffles", 0)
    seed = _whole(seed, "seed", 0)
    try:
        min_group = float(min_group)
        unit = float(unit_size)
    except (TypeError, ValueError, OverflowError):
        raise OpportunityError(
            "[opportunity] min_group and unit_size must be numbers; got "
            f"{min_group!r} and {unit_size!r}.") from None
    if not math.isfinite(min_group) or min_group < 0:
        raise OpportunityError(
            f"[opportunity] min_group must be zero or more people; got "
            f"{min_group!r}.")
    if not math.isfinite(unit) or unit <= 0:
        raise OpportunityError(
            f"[opportunity] unit_size must be a positive number of "
            f"metres; got {unit_size!r}.")
    if self_rule not in ("exclude", "include"):
        raise OpportunityError(
            f"[opportunity] self_rule must be 'exclude' or 'include'; "
            f"got {self_rule!r}.")

    # --- the people: who has everything the split needs
    px, py = _numeric(people, x, "x"), _numeric(people, y, "y")
    out_v = _numeric(people, outcome, "outcome")
    w = (_numeric(people, weight, "weight") if weight is not None
         else np.ones(len(people)))
    keep = np.isfinite(px) & np.isfinite(py) & np.isfinite(out_v) \
        & np.isfinite(w) & (w > 0)
    fam = None
    if family is not None:
        if family not in people.columns:
            raise OpportunityError(
                f"[opportunity] family '{family}' is not a column - "
                f"found {list(people.columns)}")
        fam, fam_labels = _family_codes(people[family])
        keep &= fam >= 0
    if index == "mld":
        bad = keep & ~(out_v > 0)
        if bad.any():
            raise OpportunityError(
                f"[opportunity] '{outcome}' is zero or below for "
                f"{int(bad.sum()):,} people, and MLD is not defined "
                "there (a zero's contribution is infinite, and replacing "
                "it with a small number makes the answer depend on that "
                "number - BACKLOG 405). Use index='theil', which admits "
                "zeros, or leave those people out deliberately.")
    elif (keep & (out_v < 0)).any():
        raise OpportunityError(
            f"[opportunity] '{outcome}' is negative for "
            f"{int((keep & (out_v < 0)).sum()):,} people; neither index "
            "is defined for a negative outcome.")
    left_out = int((~keep).sum())
    if left_out:
        say(f"[opportunity] {left_out:,} of {len(people):,} rows left out: "
            "missing coordinates, outcome, weight"
            + (" or family" if family is not None else "") + ".")
    px, py, yv, w = px[keep], py[keep], out_v[keep], w[keep]
    if fam is not None:
        fam = fam[keep]
        _u, fam = np.unique(fam, return_inverse=True)
        fam_labels = [fam_labels[i] for i in _u]
        n_fam = len(fam_labels)
        if n_fam < 2:
            raise OpportunityError(
                f"[opportunity] the family field has {n_fam} category "
                "among the people kept - there is nothing to be on top "
                "of. Leave family out, or check the field.")
    if yv.size < 2:
        raise OpportunityError("[opportunity] fewer than two people "
                               "with everything the split needs.")
    if _index(yv / _wmean(yv, w), w, index) <= 1e-15:
        raise OpportunityError(
            f"[opportunity] '{outcome}' is the same for everybody kept - "
            "there is no inequality to split, so theta is not defined.")
    yv = yv / _wmean(yv, w)          # both indices are unit-free
    whole_w = bool(np.all(w == np.round(w)))
    if shuffles and not whole_w:
        say("[opportunity] NOTE: the weights are not whole numbers of "
            "people, so the outcome cannot be shuffled among people - "
            "noise, noise_p95 and p_value are left empty. Give whole "
            "numbers (people per row) to have them.")

    # --- the neighbourhood character, from the context population.
    # v1.62.1: with no separate context the context IS the people, so
    # it carries their weight too (1.62.0 counted each row once there
    # while the outcome counted it `weight` times).
    ctx = people if context is None else context
    cw_col = context_weight
    if context is None and cw_col is None:
        cw_col = weight
    cx = context_x or x
    cy = context_y or y
    for col, what in ((cx, "context x"), (cy, "context y"),
                      (character, "character")):
        if col not in ctx.columns:
            raise OpportunityError(
                f"[opportunity] {what} '{col}' is not a column of the "
                f"{'people' if context is None else 'context'} - found "
                f"{list(ctx.columns)}")
    usable = np.isfinite(pd.to_numeric(ctx[character], errors="coerce")
                         .to_numpy(float))
    if not usable.any():
        raise OpportunityError(
            f"[opportunity] the character '{character}' has no usable "
            f"value in the {'people' if context is None else 'context'}"
            " - no neighbourhood can be described, so no types can be "
            "formed.")
    with contextlib.redirect_stdout(io.StringIO()) as quiet:
        cd = build_cells(ctx, cx, cy, binary_vars=[character],
                         unit_size=unit, weights=cw_col)
    for line in quiet.getvalue().splitlines():
        if "WARNING" in line or "note" in line:
            say(line)
    # people's cells, by the same exact midpoints as the context's
    # (cells.grid_midpoints - v1.62.1); a cell with people and no
    # context is added EMPTY so it still has a neighbourhood
    pe = np.asarray(grid_midpoints(px, unit), float)
    pn = np.asarray(grid_midpoints(py, unit), float)
    known = {(float(e), float(nn)): i for i, (e, nn) in
             enumerate(zip(cd.E, cd.N))}
    keys = list(zip(pe.tolist(), pn.tolist()))
    new = sorted({kk for kk in keys if kk not in known})
    if new:
        from .cells import CellData
        add_e = np.array([kk[0] for kk in new], float)
        add_n = np.array([kk[1] for kk in new], float)
        z = np.zeros(len(new))
        cd = CellData(
            E=np.r_[np.asarray(cd.E, float), add_e],
            N=np.r_[np.asarray(cd.N, float), add_n],
            n=np.r_[np.asarray(cd.n, float), z],
            binary_sums={character: np.r_[cd.binary_sums[character], z]},
            binary_valid={character: np.r_[
                np.asarray(cd.binary_valid[character], float), z]},
            unit_size=unit)
        for kk in new:
            known[kk] = len(known)
    cell = np.array([known[kk] for kk in keys], dtype=np.int64)
    origins = np.unique(cell)
    with contextlib.redirect_stdout(io.StringIO()):
        res = FC.run_knn_counts(cd, k_values=ks, origins=origins,
                                self_rule=self_rule, seed=seed,
                                report=False)
    rkey = dict(zip(zip(res["EastWest"].to_numpy(float).tolist(),
                        res["NorthSouth"].to_numpy(float).tolist()),
                    range(len(res))))
    row_of_cell = np.full(len(known), -1, dtype=np.int64)
    for kk, ci in known.items():
        row_of_cell[ci] = rkey.get(kk, -1)
    prow = row_of_cell[cell]
    assert (prow >= 0).all(), "a person's cell has no result row"

    say(f"[opportunity] theta(k) of '{outcome}' ({index.upper()}) over "
        f"{w.sum():,.0f} people, types from the neighbourhood "
        f"{'share' if _is_binary(ctx[character]) else 'mean'} of "
        f"'{character}' in {groups} equal groups; own cell "
        f"{'left out' if self_rule == 'exclude' else 'included'}; "
        f"{shuffles} shuffles.")

    draw = bool(shuffles) and whole_w
    rows, emptied = [], []
    for k in ks:
        t0 = time.time()
        c_all = res[f"R_{character}_{k}"].to_numpy(float)[prow]
        ok = np.isfinite(c_all)
        row = {"k": k, "people": float(w[ok].sum()),
               "no_neighbourhood": float(w[~ok].sum()),
               "note": ""}
        if not ok.any():
            row["note"] = "nobody has a neighbourhood at this k"
            rows.append(row)
            emptied.append((k, row["note"]))
            continue
        c, yk, wk = c_all[ok], yv[ok], w[ok]
        tot = _index(yk, wk, index)
        if tot <= 1e-15:
            row.update(total=tot, note="no inequality among the people "
                                       "with a neighbourhood")
            rows.append(row)
            emptied.append((k, row["note"]))
            continue
        codes = _equal_groups(c, wk, groups)
        sizes = np.bincount(codes, weights=wk)
        b = _between(yk, wk, codes, index)
        th = b / tot
        # THE CHANCE COLUMNS: one generator per k, so a profile is
        # reproducible k by k whatever else is in the list
        rng = np.random.default_rng([seed, k])
        chance = _Chance(yk, wk, index) if draw else None
        draws = chance.anywhere(rng, shuffles, codes) if draw else None
        noise, p95, pval = _chance_columns(draws, th)
        row.update(groups=int(sizes.size), smallest_group=float(sizes.min()),
                   total=tot, between=b, theta=th,
                   theta_nogroups=_fitted_share(yk, wk, _design(c), index),
                   noise=noise, noise_p95=p95, p_value=pval)
        if not np.isfinite(row["theta_nogroups"]):
            row["note"] = ("the no-groups check is empty: the fit "
                           "predicts an outcome of zero or below "
                           "somewhere")
        if sizes.min() < min_group:
            why = (f"a group under min_group ({sizes.min():,.0f} "
                   "people)")
            row.update(between=np.nan, theta=np.nan, noise=np.nan,
                       noise_p95=np.nan, p_value=np.nan,
                       note="; ".join(x for x in (row["note"], why) if x))
            emptied.append((k, why))
        if fam is not None:
            fk = fam[ok]
            both = codes * n_fam + fk
            _ub, both = np.unique(both, return_inverse=True)
            bsz = np.bincount(both, weights=wk)
            b_f = _between(yk, wk, fk, index)
            b_both = _between(yk, wk, both, index)
            top = (b_both - b_f) / tot
            fit_both = _fitted_share(yk, wk, _design(c, fk, n_fam), index)
            fit_f = _fitted_share(yk, wk, _family_design(fk, n_fam,
                                                         yk.size), index)
            tdraws = (chance.within(rng, shuffles, both, fk) if draw
                      else None)
            tnoise, tp95, tp = _chance_columns(tdraws, top)
            row.update(family_categories=n_fam,
                       theta_family=b_f / tot,
                       smallest_both=float(bsz.min()),
                       theta_both=b_both / tot,
                       theta_on_top=top,
                       theta_nogroups_on_top=fit_both - fit_f,
                       noise_on_top=tnoise, noise_on_top_p95=tp95,
                       p_value_on_top=tp)
            if bsz.min() < min_group:
                row.update(theta_both=np.nan, theta_on_top=np.nan,
                           noise_on_top=np.nan, noise_on_top_p95=np.nan,
                           p_value_on_top=np.nan)
                why = (f"a group x family type under min_group "
                       f"({bsz.min():,.0f} people)")
                row["note"] = "; ".join(x for x in (row["note"], why) if x)
                emptied.append((k, why))
        rows.append(row)
        if report and draw and time.time() - t0 > 5:
            say(f"[opportunity] k = {k:,}: {time.time() - t0:,.0f} s")
    out = pd.DataFrame(rows)
    every = ["groups", "smallest_group", "total", "between", "theta",
             "theta_nogroups", "noise", "noise_p95", "p_value"]
    if fam is not None:
        every += ["family_categories", "theta_family", "smallest_both",
                  "theta_both", "theta_on_top", "theta_nogroups_on_top",
                  "noise_on_top", "noise_on_top_p95", "p_value_on_top"]
    for col in every:
        if col not in out.columns:
            out[col] = np.nan
    lead = ["k", "people", "no_neighbourhood", "groups", "smallest_group",
            "total", "between", "theta", "theta_nogroups", "noise",
            "noise_p95", "p_value"]
    out = out[lead + [c for c in out.columns if c not in lead + ["note"]]
              + ["note"]]
    _say_profile(say, out, family is not None, emptied, shuffles if draw
                 else 0, fam_labels if fam is not None else None)
    return out


def _is_binary(series):
    v = pd.to_numeric(series, errors="coerce").dropna().unique()
    return bool(len(v)) and set(np.round(v, 12)) <= {0.0, 1.0}


def _say_profile(say, out, with_family, emptied, shuffles, fam_labels):
    def pct(v):
        return "      -" if not np.isfinite(v) else f"{100 * v:6.2f}%"

    def pv(v):
        return "    -" if not np.isfinite(v) else f"{v:5.3f}"
    say("   k        people  groups  smallest   theta  no-groups   noise"
        "      p" + ("    on top of family (p)" if with_family else ""))
    for r in out.itertuples():
        g = "-" if not np.isfinite(r.groups) else f"{int(r.groups)}"
        sm = ("-" if not np.isfinite(r.smallest_group)
              else f"{r.smallest_group:,.0f}")
        line = (f"   {r.k:<7,} {r.people:>9,.0f}  {g:>6}  {sm:>8} "
                f"{pct(r.theta)}   {pct(r.theta_nogroups)} "
                f"{pct(r.noise)}  {pv(r.p_value)}")
        if with_family:
            top = getattr(r, "theta_on_top", np.nan)
            line += (f"    {pct(top)} "
                     f"({pv(getattr(r, 'p_value_on_top', np.nan)).strip()})")
        say(line)
    if with_family and "theta_family" in out and \
            out["theta_family"].notna().any():
        say(f"   family alone ({', '.join(fam_labels)}): "
            f"{100 * out['theta_family'].dropna().iloc[0]:.2f}% of the "
            "inequality.")
    th = out["theta"].to_numpy(float)
    if shuffles:
        p = out["p_value"].to_numpy(float)
        clear = np.isfinite(th) & (p <= ALPHA)
        say(f"   p: the share of {shuffles} shuffles of the outcome among "
            "the same people that reach theta (1/(shuffles+1) is the "
            "smallest possible).")
    else:
        clear = np.isfinite(th)
    if clear.any():
        # a peak is named only among the k's that stand above chance:
        # a profile of pure noise has a highest point too
        best = int(out["k"].iloc[int(np.nanargmax(np.where(clear, th,
                                                           np.nan)))])
        say(f"   the profile peaks at k = {best:,}.")
    if shuffles:
        near = out[np.isfinite(th) & ~(out["p_value"].to_numpy(float)
                                       <= ALPHA)]
        if len(near):
            say("   NOTE: at k = " + ", ".join(f"{k:,}" for k in near["k"])
                + f" theta is not clearly above chance (p > {ALPHA}). "
                "Fewer groups, or more people, lower the chance level.")
        if with_family:
            tp = out["p_value_on_top"].to_numpy(float)
            top = out["theta_on_top"].to_numpy(float)
            low = out[np.isfinite(top) & ~(tp <= ALPHA)]
            if len(low):
                say("   NOTE: on top of family, at k = "
                    + ", ".join(f"{k:,}" for k in low["k"])
                    + f" the neighbourhood adds nothing clearly above "
                    f"chance (p > {ALPHA}).")
    for k, why in emptied:
        say(f"   EMPTY at k = {k:,}: {why}.")
