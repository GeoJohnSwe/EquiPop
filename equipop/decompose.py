"""
decompose.py - inequality within each bespoke neighbourhood, split
into the part BETWEEN groups and the part WITHIN them.

v1.55.0, BACKLOG 405. John's design and rulings, 12 October 2026.

WHAT IT ANSWERS. Among the k people nearest each place: how much of
the income inequality lies between the groups of some grouping field
(born abroad or not, parental education), and how much within them?
The answer is the between-group SHARE, theta = between / total.

WHY ONLY MLD AND THEIL. Both are members of the generalised-entropy
family and both split EXACTLY:

    MLD   = sum_g s_g ln(mu / mu_g)              (between)
          + sum_g s_g MLD_g                      (within)

    Theil = sum_g s_g (mu_g/mu) ln(mu_g / mu)    (between)
          + sum_g s_g (mu_g/mu) Theil_g          (within)

with s_g the group's share of the people and mu_g its mean. The Gini
does not split this way - it leaves an overlap term - so a "between-
group Gini" is not a clean share of anything. Verified to 1e-17 with
fractional weights before a line of this was written.

HOW, WITHOUT TOUCHING THE ENGINE. The engine already computes
statistics for a subgroup: a value present only for the group's
members and missing for everybody else "counts towards k but not
towards the statistic" - its own words, printed since 1.31. So each
value field is split into one sub-field per group, the engine is run
as usual, and the pieces - each group's count, mean and index - are
assembled here into the three columns. The neighbourhood is the SAME
neighbourhood: k still counts everybody.

THE RELIABILITY RULE (John's ruling: a minimum group size, default 30,
user-settable). Between-group inequality is biased UPWARD when a group
is small - a group of three people has a noisy mean, and noise between
means reads as inequality between groups. So all three columns are
reported only where at least two groups are present AND every group
present has at least `min_group` people (weighted, fractions
included). Otherwise they are ABSENT - never zero. Two columns are
always written so the reader can see why: Ng_, how many groups are
present, and NgMin_, the size of the smallest.

WHAT IT IS NOT CALLED. Not "inequality of opportunity". Whether a
between-group share measures OPPORTUNITY depends on whether the
grouping field is a circumstance beyond a person's control - a
normative cut the reader makes, not the tool. The columns are named
for what they compute.

EX ANTE ONLY, for now (John's ruling). The ex-post reading - ranking
each person within their own neighbourhood's distribution - is later.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .stats import PREFIX

#: John's ruling, 12 October 2026: thirty people per group by default.
DEFAULT_MIN_GROUP = 30.0
#: A grouping field is a circumstance with a few categories. More than
#: this many distinct values is an identifier or a continuous field.
MAX_LEVELS = 20
#: The decomposable indices, in the order their columns are written.
INDICES = ("mld", "theil")
#: The columns written once per value field and suffix, whatever the
#: index: how many groups are present, and the smallest of them.
GROUP_COLUMNS = ("Ng", "NgMin")
#: The three columns written per index: between, within, share.
PARTS = ("b", "w", "sh")

_STATA_MISSING = 8.9e307


def resolve_min_group(value) -> float:
    """The minimum group size, checked. None means the default."""
    if value is None:
        return DEFAULT_MIN_GROUP
    if isinstance(value, bool):
        raise ValueError(
            f"[decompose] the minimum group size must be a number of "
            f"people, not {value!r}.")
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"[decompose] the minimum group size must be a number of "
            f"people; got {value!r}.") from None
    if not math.isfinite(v) or v < 0:
        raise ValueError(
            f"[decompose] the minimum group size must be zero or more "
            f"people; got {value!r}. Zero means no minimum - every "
            "group present is used, however small.")
    return v


def prefixes(indices) -> set:
    """Every column prefix a decomposition can write."""
    out = set(GROUP_COLUMNS)
    for s in indices:
        out |= {PREFIX[s] + p for p in PARTS}
    return out


def _gcol(c: str, f: str, suf: str) -> str:
    """Ng_inc_400 / NgMin_inc_400 - the ONE place these are named."""
    return f"{c}_{f}_{suf}"


def _pcol(idx: str, part: str, f: str, suf: str) -> str:
    """MLDb_inc_400 / Theilsh_inc_r500 - the ONE place these are named."""
    return f"{PREFIX[idx]}{part}_{f}_{suf}"


def column_names(value_fields, suffixes, stats_wanted) -> list:
    """The columns a decomposition WILL write - level-independent by
    design, so a door can predict them before reading the data. Used
    by equipop.doors.fields.predict_result_fields and by assemble(),
    so the prediction and the result cannot disagree."""
    idx = [s for s in INDICES if s in stats_wanted]
    names = []
    for f in value_fields:
        for suf in suffixes:
            names += [_gcol(c, f, suf) for c in GROUP_COLUMNS]
            for s in idx:
                names += [_pcol(s, p, f, suf) for p in PARTS]
    return names


def _label(v) -> str:
    """A group value as it appears in a MESSAGE, never in a name.

    v1.55.1, BACKLOG 407 (external review of 1.55.0, finding 1). This
    used to format a float to ten significant digits, and the result
    was ALSO the sub-field's name - so 1.0 and 1.00000000001, two
    distinct codes, both became "1", the second sub-field overwrote
    the first, and a total MLD of 0.1308 was reported as between 0
    and within 0. Two fixes: sub-fields are now named by a stable
    internal NUMBER (see Plan), and a label is written at full
    round-trip precision, so two distinct codes can never even LOOK
    alike in a message.
    """
    if isinstance(v, (float, np.floating)):
        f = float(v)
        return str(int(f)) if f.is_integer() and abs(f) < 1e15 \
            else repr(f)
    return str(v)


def _is_missing(x) -> bool:
    """None, NaN, pandas' NA and NaT, and Stata's missing (> 8.9e307).

    v1.55.1, BACKLOG 407. This read `x is None` and a float NaN, and
    pandas' pd.NA is neither - so A, A, <NA>, B, B came out as THREE
    groups, missingness became a real analytical group, and Ng_,
    NgMin_, the minimum-size rule and the split all changed. pd.isna
    knows every missing marker pandas and numpy have.
    """
    if x is None:
        return True
    try:
        if pd.api.types.is_scalar(x) and pd.isna(x):
            return True
    except (TypeError, ValueError):
        pass
    if isinstance(x, (float, np.floating, int, np.integer)) \
            and not isinstance(x, (bool, np.bool_)):
        return float(x) > _STATA_MISSING
    return False


def _codes(arr, name: str):
    """(labels, codes): codes[i] indexes labels, or -1 where missing.

    Numbers or text. Missing is anything _is_missing says, or an empty
    / blank string. Whole numbers stay INTEGERS, so two distinct large
    codes cannot round into one float; 1 and 1.0 are still one group,
    because Python compares and hashes them as equal.
    """
    a = np.asarray(arr, dtype=object).ravel()
    keys = []
    for x in a:
        if _is_missing(x):
            keys.append(None)
            continue
        if isinstance(x, (int, np.integer)) \
                and not isinstance(x, (bool, np.bool_)):
            keys.append(int(x))
            continue
        if isinstance(x, (float, np.floating)):
            keys.append(float(x))
            continue
        t = str(x).strip()
        keys.append(t if t else None)
    present = [k for k in keys if k is not None]
    if not present:
        raise ValueError(
            f"[decompose] the grouping field '{name}' is empty - "
            "every row is missing a group.")
    kinds = {str if isinstance(k, str) else float for k in present}
    if len(kinds) > 1:
        # numbers stored as text in some rows: compare as text
        keys = [None if k is None else _label(k) for k in keys]
        present = [k for k in keys if k is not None]
    labels = sorted(set(present))
    if len(labels) > MAX_LEVELS:
        raise ValueError(
            f"[decompose] the grouping field '{name}' has "
            f"{len(labels)} distinct values. A decomposition group is "
            "a circumstance with a few categories - born abroad or "
            "not, parental education - and more than "
            f"{MAX_LEVELS} looks like an identifier or a continuous "
            "field. Recode it into groups first.")
    if len(labels) < 2:
        raise ValueError(
            f"[decompose] the grouping field '{name}' holds only one "
            f"group ({_label(labels[0])}), so there is nothing to "
            "split between groups.")
    pos = {k: i for i, k in enumerate(labels)}
    codes = np.array([-1 if k is None else pos[k] for k in keys],
                     dtype=int)
    return [_label(k) for k in labels], codes


class Plan:
    """How a decomposition is split before the engine runs, and how
    the pieces are put back together after it."""

    def __init__(self, group_name, labels, value_fields, indices,
                 min_group):
        self.group_name = group_name
        self.labels = labels
        self.value_fields = list(value_fields)
        # v1.55.1, BACKLOG 407 (review finding 4): PER FIELD. This was
        # one list, the union over every field, so asking MLD of
        # income and Theil of rent wrote a Theil split for income and
        # an MLD split for rent - and when rent held a zero, the run
        # was REFUSED, naming a scaffolding field, for an MLD nobody
        # had asked of rent.
        self.indices = {f: list(indices[f]) for f in self.value_fields}
        self.min_group = min_group
        # one engine sub-field per value field and group, named by a
        # stable NUMBER, never by the group's value (407: two values
        # formatting alike made two sub-fields one). Brackets cannot
        # occur in a GIS field name, so these cannot collide with
        # anything the user has.
        self.subs = {f: [f"{f}[{group_name}#{i}]"
                         for i in range(len(labels))]
                     for f in self.value_fields}
        self.sub_columns = {}

    @property
    def sub_names(self) -> list:
        return [s for f in self.value_fields for s in self.subs[f]]

    @property
    def sub_stats(self) -> dict:
        """What the engine must compute per sub-field: the mean, and
        each index. The count (Nv_) is always written."""
        return {s: ["mean"] + self.indices[f]
                for f in self.value_fields for s in self.subs[f]}

    @property
    def prefixes(self) -> set:
        return prefixes({i for f in self.value_fields
                         for i in self.indices[f]})

    def assemble(self, st: pd.DataFrame) -> pd.DataFrame:
        """Add the decomposition columns and REMOVE the sub-fields'
        own columns, which are scaffolding and never reach a user."""
        st = st.copy()
        new = {}
        for f in self.value_fields:
            subs = self.subs[f]
            head = f"Nv_{subs[0]}_"
            sufs = [c[len(head):] for c in st.columns
                    if c.startswith(head)]
            for suf in sufs:
                n = np.column_stack([
                    st[f"Nv_{s}_{suf}"].to_numpy(float) for s in subs])
                n = np.where(np.isfinite(n), n, 0.0)
                m = np.column_stack([
                    st[f"Mean_{s}_{suf}"].to_numpy(float) for s in subs])
                present = n > 0
                ng = present.sum(axis=1).astype(float)
                with np.errstate(invalid="ignore"):
                    ngmin = np.where(present, n, np.inf).min(axis=1)
                ngmin = np.where(ng > 0, ngmin, np.nan)
                new[_gcol("Ng", f, suf)] = ng
                new[_gcol("NgMin", f, suf)] = ngmin
                ok = (ng >= 2) & (ngmin >= self.min_group)
                tot_n = n.sum(axis=1)
                with np.errstate(invalid="ignore", divide="ignore"):
                    s_g = n / tot_n[:, None]
                    mu = np.nansum(np.where(present, s_g * m, 0.0),
                                   axis=1)
                    for idx in self.indices[f]:
                        ig = np.column_stack([
                            st[f"{PREFIX[idx]}_{s}_{suf}"].to_numpy(float)
                            for s in subs])
                        b, w = self._parts(idx, present, s_g, m, ig, mu)
                        tot = b + w
                        good = ok & np.isfinite(b) & np.isfinite(w)
                        share = np.where(good & (tot > 0), b / tot,
                                         np.nan)
                        new[_pcol(idx, "b", f, suf)] = np.where(good, b,
                                                                np.nan)
                        new[_pcol(idx, "w", f, suf)] = np.where(good, w,
                                                                np.nan)
                        new[_pcol(idx, "sh", f, suf)] = share
        drop = [c for c in st.columns
                if any(f"_{s}_" in c for s in self.sub_names)]
        st = st.drop(columns=drop)
        for k, v in new.items():
            st[k] = v
        return st

    @staticmethod
    def _parts(idx, present, s_g, m, ig, mu):
        """(between, within) per row. A group that is absent from the
        neighbourhood contributes nothing to either."""
        mu_c = mu[:, None]
        if idx == "mld":
            bterm = np.where(present, s_g * np.log(mu_c / m), 0.0)
            wterm = np.where(present, s_g * ig, 0.0)
        else:
            r = m / mu_c
            # a group whose mean is zero contributes nothing: r ln r
            # tends to 0, and its own Theil is multiplied by r = 0.
            pos = present & (r > 0)
            safe = np.where(pos, r, 1.0)
            bterm = np.where(pos, s_g * safe * np.log(safe), 0.0)
            wterm = np.where(pos, s_g * safe * ig, 0.0)
        # a group with people but no computable index (NaN) makes the
        # row's decomposition unknown, not smaller
        bad_w = (present & ~np.isfinite(np.where(present, ig, 0.0))
                 & ((idx == "mld") | (m > 0)))
        b = bterm.sum(axis=1)
        w = wterm.sum(axis=1)
        w = np.where(bad_w.any(axis=1), np.nan, w)
        b = np.where(np.isfinite(mu) & (mu > 0), b, np.nan)
        return b, w


def make_plan(df: pd.DataFrame, value_fields, stats_wanted: dict,
              decompose_by: dict, min_group, members) -> Plan:
    """Validate a decomposition request and split the value fields.

    `df` holds the value columns (full length, row-aligned) and gains
    one sub-column per value field and group. `members` is the
    reference population: rows outside it are nobody's neighbour, so
    they are not counted when reporting missing groups.
    """
    if not isinstance(decompose_by, dict) or len(decompose_by) != 1:
        raise ValueError(
            "[decompose] give exactly one grouping field, as "
            "{name: values}; a decomposition splits by one grouping "
            "at a time.")
    (gname, garr), = decompose_by.items()
    gname = str(gname)
    if len(np.asarray(garr, dtype=object).ravel()) != len(df):
        raise ValueError(
            f"[decompose] the grouping field '{gname}' has "
            f"{len(np.asarray(garr, dtype=object).ravel())} values "
            f"for {len(df)} rows - they must be row-aligned.")
    mg = resolve_min_group(min_group)
    fields = list(value_fields)
    # PER FIELD (407): each field is split by exactly the indices
    # asked of IT - and its own index's domain is the only one it is
    # held to.
    idx = {f: [s for s in INDICES if s in stats_wanted.get(f, [])]
           for f in fields}
    if not any(idx.values()):
        raise ValueError(
            "[decompose] a decomposition needs MLD or Theil among the "
            "measures - they are the inequality indices that split "
            "exactly into a between-group and a within-group part. "
            "Tick one of them, or leave the grouping field empty.")
    missing = [f for f in fields if not idx[f]]
    if missing:
        raise ValueError(
            f"[decompose] {missing} would be decomposed without MLD "
            "or Theil asked for them. Ask for one of the two on every "
            "value field, or decompose them in separate runs.")
    labels, codes = _codes(garr, gname)
    plan = Plan(gname, labels, fields, idx, mg)
    mem = np.asarray(members, dtype=bool)
    no_group = codes < 0
    for f in fields:
        base = df[f].to_numpy(float)
        lost = int((mem & np.isfinite(base) & no_group).sum())
        if lost:
            print(f"[decompose] {lost} row(s) have a value of '{f}' "
                  f"but no '{gname}': they are left out of the "
                  f"decomposition, and stay in every other statistic "
                  f"of '{f}'.")
        for i, sub in enumerate(plan.subs[f]):
            col = np.where(codes == i, base, np.nan)
            df[sub] = col
            plan.sub_columns[sub] = col
    rule = (f"each holds at least {mg:g} people" if mg > 0
            else "no minimum group size")
    used = [s for s in INDICES if any(s in idx[f] for f in fields)]
    print(f"[decompose] '{gname}' splits {', '.join(fields)} into "
          f"{len(labels)} groups ({', '.join(labels)}); "
          f"{' and '.join(PREFIX[s] for s in used)} reported where at "
          f"least two groups are present and {rule}.")
    return plan
