"""
segregation.py - aggregate segregation indices from k-NN output
(backlog item 6; formulas per the US Census formulary and
Östh, Clark & Malmberg 2015, Geographical Analysis 47:34-49).

POST-ANALYSIS design: the functions consume a run_knn/run_knn_stats
output DataFrame - one row per origin i with per-k population counts
N_k and treatment counts T_k (or ratios R_k) - and return ONE ROW PER
SCALE with the index values. No engine involvement.

Unit convention: at scale k, each origin's bespoke neighbourhood is
treated as the unit, with p_i = R_k(i). Its WEIGHT is the people
living in the origin cell (weighting="people", the default since
1.63.0: every person's neighbourhood counts once) or 1 for every
populated origin ("cells": every place counts once, since 1.63.1).
Every index is measured against the units' own weighted mean share,
P_ref (BACKLOG 443). The row labelled 'local' uses the origin cells
themselves (CountAllLocal / CountGroupLocal) - the aspatial baseline,
where P_ref is the global share P.

Every row says what it describes, in columns that survive a CSV
(BACKLOG 452): weighting, global_share_P, valid_origins, valid_people,
excluded_people and a note.

Indices (evenness): Dissimilarity D, Gini (segregation form),
Entropy/Theil H, Atkinson(b).
Indices (exposure): Isolation xPx, Interaction xPy, Correlation ratio
V = (I-P)/(1-P), and SI - the population-weighted k-share isolation of
the 2015 paper: SI_k = sum_i(x_i,local * p_ik) / sum_i(x_i,local).
Concentration/delta family is NOT included: it requires an areal term
whose bespoke-neighbourhood definition is a methodological choice
still to be made (see backlog).
"""

import numpy as np
import pandas as pd


def _weighted_gini_of_p(p, t, P):
    """Segregation Gini: sum_ij t_i t_j |p_i - p_j| / (2 T^2 P(1-P)),
    computed in O(n log n) via sorting."""
    order = np.argsort(p)
    p, t = p[order], t[order]
    T = t.sum()
    cw = np.cumsum(t) - t                 # weight strictly below i
    cwp = np.cumsum(t * p) - t * p        # weighted p strictly below i
    total = 2.0 * np.sum(t * (p * cw - cwp))
    return total / (2.0 * T * T * P * (1 - P))


#: v1.63.0, BACKLOG 443 (John, 26 October 2026: "do as suggested",
#: with the place-based view kept as a choice). Who a k-scale index
#: describes:
#:   people - every person's neighbourhood counts once: each origin
#:            cell's neighbourhood is weighted by the people LIVING in
#:            that cell, and isolation averages over the group's own
#:            members - so isolation at k IS the 2015 paper's SI.
#:   cells  - every place counts once: each populated origin cell's
#:            neighbourhood weighs 1, and isolation weighs each place
#:            by its group share - what the classical formula gives
#:            when every unit has the same size.
#: To 1.62.1 the weights were the neighbourhoods' sizes but the
#: reference share was the PEOPLE's, P. Where the group lives at a
#: different density than everybody else the two disagree, and the
#: entropy and Atkinson indices - which are bounded at zero only when
#: the reference IS the units' own average - went below zero: H -0.020,
#: -0.029, -0.027 at k = 50, 200, 800 on the Stata test data, where
#: tertiary-educated people live 24% in the sparser cells and 17% in
#: the densest quarter. Now every index is measured against its units'
#: own weighted mean, P_ref, reported beside it.
#:
#: v1.63.1, BACKLOG 448 (review of 1.63.0, P1). 1.63.0's "cells" kept
#: the neighbourhood size N_k as the weight and said "every place
#: counts once". Under the default proportional overshoot every N_k IS
#: k, so the two agree to 1e-14; under whole or sampled overshoot N_k
#: varies (50 to 309 at k = 50 on the test data) and the option
#: answered a different question from the one it named. The weight is
#: now 1 for every populated place, which is what John chose.
WEIGHTINGS = ("people", "cells")
DEFAULT_WEIGHTING = "people"

#: How much a group count may exceed its total before it is refused:
#: fractional (modelled) populations carry rounding, nothing more.
_TOL = 1e-9


class SegregationError(ValueError):
    """The profile is undefined for this input, or the input is
    impossible. Said in words, naming the field and the scale (BACKLOG
    449) - never a ZeroDivisionError, and never a table of NaN that
    looks like a result."""


def seg_indices(w, p, wg, P, atkinson_b=0.5):
    """All indices for one scale.

    w  - each unit's weight (people, or 1 per place)
    p  - each unit's group share
    wg - each unit's weight in the EXPOSURE indices: the group members
         whose experience isolation averages
    P  - the reference share. Evenness indices are bounded at zero only
         when it is the units' own weighted mean, sum(w p) / sum(w).
    """
    w = np.asarray(w, float); p = np.asarray(p, float)
    wg = np.asarray(wg, float)
    ok = (w > 0) & np.isfinite(p)
    w, p, wg = w[ok], p[ok], wg[ok]
    T = w.sum()
    # BACKLOG 449: the domain, in words
    if not T > 0:
        raise SegregationError(
            "[segregation] no unit has a positive weight, so there is "
            "nobody to describe")
    if not 0.0 < float(P) < 1.0:
        raise SegregationError(
            f"[segregation] the reference share is {float(P):g}: "
            "segregation is undefined when the group is nobody (0) or "
            "everybody (1)")
    D = np.sum(w * np.abs(p - P)) / (2 * T * P * (1 - P))
    gini = _weighted_gini_of_p(p, w, P)

    def _e(q):
        q = np.clip(q, 1e-12, 1 - 1e-12)
        return q * np.log(1 / q) + (1 - q) * np.log(1 / (1 - q))
    E = _e(P)
    H = np.sum(w * (E - _e(p))) / (E * T)
    b = atkinson_b
    inner = np.sum((1 - p) ** (1 - b) * p ** b * w) / (P * T)
    atk = 1 - (P / (1 - P)) * np.abs(inner) ** (1 / (1 - b))
    G = wg.sum()
    isolation = np.sum(wg * p) / G if G > 0 else np.nan        # xPx
    interaction = np.sum(wg * (1 - p)) / G if G > 0 else np.nan  # xPy
    V = (isolation - P) / (1 - P)
    return {"D": D, "Gini": gini, "H": H, f"Atkinson_{b}": atk,
            "Isolation": isolation, "Interaction": interaction,
            "CorrelationV": V}


def seg_indices_at_scale(t, x, P, atkinson_b=0.5):
    """All indices for one scale whose units PARTITION the population:
    t = unit totals, x = unit group counts, P their overall share. The
    classical form, kept for that case (the 'local' row is one)."""
    t = np.asarray(t, float); x = np.asarray(x, float)
    ok = t > 0
    p = np.divide(x, t, out=np.zeros_like(x), where=ok)
    return seg_indices(np.where(ok, t, 0.0), p, x, P, atkinson_b)


def _rows(n):
    return f"{n} row" + ("" if n == 1 else "s")


def _counts(df, all_col, grp_col, where):
    """Two count columns as floats, checked: present, numeric, finite
    where given, never negative, the group never above the total.
    Missing values are returned as NaN for the caller to rule on."""
    missing = [c for c in (all_col, grp_col) if c not in df.columns]
    if missing:
        raise SegregationError(
            f"[segregation] {where}: no column {', '.join(missing)} "
            f"(the output has {', '.join(map(str, df.columns[:12]))}"
            f"{' ...' if len(df.columns) > 12 else ''})")
    out = []
    for c in (all_col, grp_col):
        try:
            v = pd.to_numeric(df[c], errors="raise").to_numpy(float)
        except (TypeError, ValueError):
            raise SegregationError(
                f"[segregation] {where}: {c} is not numeric") from None
        if np.isinf(v).any():
            raise SegregationError(
                f"[segregation] {where}: {c} holds an infinite count")
        if (v < 0).any():
            raise SegregationError(
                f"[segregation] {where}: {c} holds a negative count "
                f"({_rows(int((v < 0).sum()))})")
        out.append(v)
    a, g = out
    over = np.isfinite(a) & np.isfinite(g) & (g > a * (1 + _TOL) + _TOL)
    if over.any():
        raise SegregationError(
            f"[segregation] {where}: {grp_col} exceeds {all_col} in "
            f"{_rows(int(over.sum()))} - more of the group than there are "
            "people; were the columns swapped, or the counts mixed with "
            "shares?")
    return a, g


def _undefined(scale, note, base):
    """A row for a scale with nothing to describe: every index NaN, and
    the reason in words."""
    nan = float("nan")
    r = {"scale": scale, "D": nan, "Gini": nan, "H": nan,
         "Isolation": nan, "Interaction": nan, "CorrelationV": nan,
         "SI": nan, "P_ref": nan}
    r.update(base)
    r["note"] = note
    return r


def seg_profile(knn_out: pd.DataFrame, k_values: list[int],
                atkinson_b: float = 0.5,
                n_col: str = "N_{k}", t_col: str = "T_{k}",
                local_all: str = "CountAllLocal",
                local_grp: str = "CountGroupLocal",
                weighting: str = DEFAULT_WEIGHTING) -> pd.DataFrame:
    """
    Segregation profile across scales: one row per k (plus 'local').

    weighting : "people" (default) - every person's neighbourhood counts
        once, so the indices describe the average person, and
        Isolation at k equals SI; or "cells" - every populated place
        counts once (see WEIGHTINGS). Every index is measured against
        its units' own weighted mean share, given as P_ref.

    Adds SI (Östh-Clark-Malmberg 2015): the average k-share experienced
    by a minority member, weighting each origin's p_ik by the origin's
    own LOCAL minority count. SI does not depend on `weighting`.

    ORIGINS WITHOUT A NEIGHBOURHOOD at a scale (N_k missing or zero, or
    T_k missing) are left out of EVERY index at that scale, SI included,
    and counted: valid_origins, valid_people, excluded_people, with a
    note (BACKLOG 450). Impossible input is refused with
    SegregationError (449).
    """
    if weighting not in WEIGHTINGS:
        raise SegregationError(f"[segregation] weighting must be one of "
                               f"{', '.join(WEIGHTINGS)}; got {weighting!r}")
    la, lg = _counts(knn_out, local_all, local_grp, "the local counts")
    if np.isnan(la).any() or np.isnan(lg).any():
        raise SegregationError(
            "[segregation] the local counts have missing values "
            f"({_rows(int((np.isnan(la) | np.isnan(lg)).sum()))}): every "
            "origin must say how many people, and how many of the "
            "group, live in it")
    total = float(la.sum())
    if not total > 0:
        raise SegregationError(
            "[segregation] nobody lives in any origin cell "
            f"({local_all} sums to {total:g})")
    P = float(lg.sum()) / total
    if not 0.0 < P < 1.0:
        raise SegregationError(
            f"[segregation] {'nobody' if P <= 0 else 'everybody'} "
            f"belongs to the group ({local_grp} / {local_all} = {P:g}): "
            "segregation is undefined, because there is no one to be "
            "separated from")
    populated = la > 0
    base = {"global_share_P": P, "weighting": weighting}
    rows = []

    p_loc = np.divide(lg, la, out=np.zeros_like(lg), where=populated)
    r = seg_indices(la, p_loc, lg, P, atkinson_b)
    r["SI"] = np.sum(lg[populated] * p_loc[populated]) / lg.sum()
    r["P_ref"] = P
    rows.append({"scale": "local", **r, **base,
                 "valid_origins": int(populated.sum()),
                 "valid_people": total, "excluded_people": 0.0,
                 "note": ""})

    excluded_any = []
    for k in k_values:
        where = f"scale {k}"
        t, x = _counts(knn_out, n_col.format(k=k), t_col.format(k=k),
                       where)
        valid = populated & np.isfinite(t) & (t > 0) & np.isfinite(x)
        p_ik = np.divide(x, t, out=np.zeros_like(x),
                         where=valid)
        counts = {"valid_origins": int(valid.sum()),
                  "valid_people": float(la[valid].sum()),
                  "excluded_people": float(la[populated & ~valid].sum())}
        note = ""
        if counts["excluded_people"] > 0:
            n_ex = int((populated & ~valid).sum())
            note = (f"{counts['excluded_people']:g} people in "
                    f"{n_ex} origin{'' if n_ex == 1 else 's'} have no "
                    "neighbourhood at this scale and are left out of "
                    "every index here, SI included")
            excluded_any.append(k)
        if not valid.any():
            rows.append(_undefined(k, "no origin has a neighbourhood at "
                                   "this scale", {**base, **counts}))
            continue
        if weighting == "people":
            w = np.where(valid, la, 0.0)
            wg = np.where(valid, lg, 0.0)
        else:
            w = valid.astype(float)
            wg = np.where(valid, p_ik, 0.0)
        P_ref = float(np.sum(w * p_ik) / np.sum(w))
        if not 0.0 < P_ref < 1.0:
            rows.append(_undefined(
                k, f"every neighbourhood here holds "
                f"{'none' if P_ref <= 0 else 'only members'} of the "
                "group, so there is nothing to compare"
                + (f"; {note}" if note else ""), {**base, **counts}))
            continue
        r = seg_indices(w, p_ik, wg, P_ref, atkinson_b)
        g_valid = float(lg[valid].sum())
        r["SI"] = (float(np.sum(lg[valid] * p_ik[valid])) / g_valid
                   if g_valid > 0 else np.nan)
        r["P_ref"] = P_ref
        rows.append({"scale": k, **r, **base, **counts, "note": note})

    out = pd.DataFrame(rows)
    out.attrs["global_share_P"] = P
    out.attrs["weighting"] = weighting
    print(f"[segregation] profile over {len(k_values)} scales + local "
          f"(P = {P:.4f}; every "
          f"{'person' if weighting == 'people' else 'place'}"
          f"'s neighbourhood counted once)")
    if excluded_any:
        print("[segregation] NOTE: at k = "
              + ", ".join(map(str, excluded_any))
              + " some origins have no neighbourhood; they are left out "
              "of every index there - see excluded_people and note")
    return out
