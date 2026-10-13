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

HOW: FOUR SUMS PER GROUP (v1.57.0, BACKLOG 409). Both indices are
functions of four quantities a neighbourhood can simply ADD UP over
each group's people, the way it adds up the people themselves:

    W = sum w            (people)
    S = sum w y          (their income)
    L = sum w ln y       (MLD only)
    Q = sum w y ln y     (Theil only)

    mu_g    = S/W
    MLD_g   = ln mu_g - L/W
    Theil_g = Q/S - ln mu_g

Both indices are blind to the unit of income, so y is first divided by
one constant per field - e^c, with c the mean log income - which puts
every mean near 1 and every log near 0. Measured against a reference
free of cancellation, on incomes near e^25 with a 0.1% spread (an MLD
of 4.3e-7): with nothing done, the split was off by about 2e-8 of the
index; with the mean log subtracted from each log, 3.5e-9; rescaled,
2.7e-10 - about 1e-16 absolute, which is as precisely as the incomes
themselves are stored. The direct MLD there is off by 4.9e-10.

1.55 and 1.56 did this differently: each value field was split into
one sub-field per group, and the engine computed a full sorted
statistic for each. Exact, and expensive - measured on 50,000 points
at k=400, one field took 21 s alone, 196 s split into 20 groups, and
three fields split into 20 took 595 s and 1.4 GB. Sums cost one vector
addition per ring of cells, however many groups there are. The engine
is told nothing about groups: it adds up whatever per-cell sums it is
given (CellData.sum_matrix), with a crossing ring contributing the
same share of them as of its people. The neighbourhood is the SAME
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

AND WHO IT COVERS (v1.57.0, BACKLOG 407a). A third: NgN_, the people
the split is computed over - those with a value AND a group. Beside
Nv_, everybody with a value, it shows where rows with no group were
left out, in the result itself rather than only in the run's messages.

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
#: index: how many groups are present, the smallest of them, and how
#: many people the split covers (407a - appended, so the older two
#: keep their places).
GROUP_COLUMNS = ("Ng", "NgMin", "NgN")
#: The three columns written per index: between, within, share.
PARTS = ("b", "w", "sh")
#: Below this a total index is rounding noise around zero: everybody
#: in the neighbourhood has (to about six significant digits) the same
#: value. Between and within are then 0, and the share is EMPTY -
#: there is no inequality to split, and 0/0 is not a share. Before
#: 1.57 the share there came out as whatever the noise divided to.
NO_INEQUALITY = 1e-12

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
    """Ng_inc_400 / NgMin_inc_400 / NgN_inc_400 - the ONE place these
    are named."""
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
    """How a decomposition is prepared before the engine runs, and how
    its sums are turned into columns after it."""

    def __init__(self, group_name, labels, value_fields, indices,
                 min_group, centre=None):
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
        #: the log of each field's rescaling constant (see the module
        #: docstring) - recorded, not needed again: the sums are built
        #: from the rescaled values, and both indices ignore scale
        self.centre = {f: float((centre or {}).get(f, 0.0))
                       for f in self.value_fields}
        # The per-person quantities, one column each, named with
        # brackets - which cannot occur in a GIS field name, so they
        # cannot collide with anything the user has. Groups are told
        # apart by a stable NUMBER, never by their value (407: two
        # values formatting alike once made two groups one).
        self.code_column = f"[{group_name}]"
        self.quantities = {f: self._quantities(f) for f in self.value_fields}

    def _quantities(self, f) -> dict:
        """{letter: column} for field f: W and S always, L for MLD,
        Q for Theil."""
        want = ["W", "S"] + (["L"] if "mld" in self.indices[f] else []) \
            + (["Q"] if "theil" in self.indices[f] else [])
        return {q: f"{f}[{self.group_name}]{q}" for q in want}

    @property
    def sum_vars(self) -> list:
        """The per-person columns build_cells sums, split by group."""
        return [c for f in self.value_fields
                for c in self.quantities[f].values()]

    def sum_name(self, f, q, i) -> str:
        from .cells import split_sum_name
        return split_sum_name(self.quantities[f][q], i)

    @property
    def prefixes(self) -> set:
        return prefixes({i for f in self.value_fields
                         for i in self.indices[f]})

    def assemble(self, st: pd.DataFrame) -> pd.DataFrame:
        """Add the decomposition columns and REMOVE the sums, which are
        scaffolding and never reach a user."""
        st = st.copy()
        new = {}
        n_lev = len(self.labels)
        for f in self.value_fields:
            head = self.sum_name(f, "W", 0) + "_"
            sufs = [c[len(head):] for c in st.columns
                    if c.startswith(head)]
            for suf in sufs:
                def get(q):
                    return np.column_stack([
                        st[f"{self.sum_name(f, q, i)}_{suf}"].to_numpy(float)
                        for i in range(n_lev)])
                W, S = get("W"), get("S")
                present = W > 0
                ng = present.sum(axis=1).astype(float)
                with np.errstate(invalid="ignore"):
                    ngmin = np.where(present, W, np.inf).min(axis=1)
                ngmin = np.where(ng > 0, ngmin, np.nan)
                new[_gcol("Ng", f, suf)] = ng
                new[_gcol("NgMin", f, suf)] = ngmin
                new[_gcol("NgN", f, suf)] = W.sum(axis=1)       # 407a
                ok = (ng >= 2) & (ngmin >= self.min_group)
                for idx in self.indices[f]:
                    A = get("L" if idx == "mld" else "Q")
                    b, w = split_from_sums(idx, W, S, A)
                    good = ok & np.isfinite(b) & np.isfinite(w)
                    tot = b + w
                    flat = good & (tot < NO_INEQUALITY)
                    with np.errstate(invalid="ignore", divide="ignore"):
                        share = np.where(good & ~flat, b / tot, np.nan)
                    new[_pcol(idx, "b", f, suf)] = np.where(
                        good, np.where(flat, 0.0, b), np.nan)
                    new[_pcol(idx, "w", f, suf)] = np.where(
                        good, np.where(flat, 0.0, w), np.nan)
                    new[_pcol(idx, "sh", f, suf)] = share
        heads = tuple(f"{self.sum_name(f, q, i)}_"
                      for f in self.value_fields
                      for q in self.quantities[f]
                      for i in range(n_lev))
        st = st.drop(columns=[c for c in st.columns if c.startswith(heads)])
        for k, v in new.items():
            st[k] = v
        return st

    def report(self, res) -> list:
        """One line per field and k (or radius): where the split was
        reported, and WHY it is empty everywhere else.

        v1.56.0, BACKLOG 410. John's first live run showed <Null> in
        every visible row and nothing to say whether that was the
        minimum-group rule or a fault. Counted in ROWS - what the user
        sees in the table - and only rows that have a position.
        """
        from .describe import _SUFFIX
        lines = []
        for f in self.value_fields:
            head = f"Ng_{f}_"
            for c in list(res):
                if not c.startswith(head):
                    continue
                suf = c[len(head):]
                m = _SUFFIX.match(suf)
                if not m:
                    continue
                at = (f"k={m['k']}" if m["k"] is not None else
                      f"r={m['r'].replace('_', '.')}" if m["r"] is not None
                      else f"tau={m['tau'].replace('_', '.')}")
                ng = np.asarray(res[c], dtype=float)
                ngmin = np.asarray(res[_gcol("NgMin", f, suf)], dtype=float)
                idx = self.indices[f][0]
                b = np.asarray(res[_pcol(idx, "b", f, suf)], dtype=float)
                placed = np.isfinite(ng)
                total = int(placed.sum())
                shown = int((placed & np.isfinite(b)).sum())
                nobody = int((placed & (ng == 0)).sum())
                one = int((placed & (ng == 1)).sum())
                small = int((placed & (ng >= 2)
                             & (ngmin < self.min_group)).sum())
                other = total - shown - nobody - one - small
                why = [f"only one group present: {one:,}"]
                if self.min_group > 0:
                    why.append(f"a group below {self.min_group:g} people: "
                               f"{small:,}")
                if nobody:
                    why.append(f"nobody with a value: {nobody:,}")
                if other > 0:
                    why.append(f"no computable index: {other:,}")
                line = (f"[decompose] {f}, {at}: split reported in "
                        f"{shown:,} of {total:,} places" + (
                            "." if shown == total else
                            f"; empty in {total - shown:,} - "
                            + "; ".join(why) + "."))
                # 407a: where people with a value but no group were
                # left out, say so - the column shows where
                # v1.57.1, external review (BACKLOG 411): the margin
                # SCALES. NgN_ and Nv_ add the same people in different
                # orders, so they differ by rounding in proportion to
                # the total - measured, 7.8e-7 at 420 million people,
                # where an absolute 1e-9 told a run with every row
                # grouped that 1,268 places left people out.
                nv = res.get(f"Nv_{f}_{suf}")
                if nv is not None:
                    ngn = np.asarray(res[_gcol("NgN", f, suf)], dtype=float)
                    nv = np.asarray(nv, dtype=float)
                    margin = 1e-9 + 1e-12 * np.abs(nv)
                    short = int((placed & (ngn < nv - margin)).sum())
                    if short:
                        line += (f" In {short:,} place"
                                 f"{'' if short == 1 else 's'} the split "
                                 f"leaves out people with a value but "
                                 f"no '{self.group_name}' (NgN_ below "
                                 f"Nv_).")
                lines.append(line)
        return lines


def split_from_sums(idx, W, S, A):
    """(between, within) per row, from each group's sums.

    W, S, A have one row per neighbourhood and one column per group:
    people, income, and L (for "mld") or Q (for "theil"). A group with
    nobody in a neighbourhood contributes nothing to either part. Each
    group's own index, and the between part, are never below zero
    (Jensen); what rounding puts below it is set to zero.
    """
    W, S, A = (np.asarray(a, dtype=float) for a in (W, S, A))
    present = W > 0
    w_tot = W.sum(axis=1)
    s_tot = S.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = s_tot / w_tot
        ln_mu = np.log(mu)[:, None]
        safe_w = np.where(present, W, 1.0)
        if idx == "mld":
            # every value is positive - a zero is refused upstream - so
            # every group present has a positive mean
            ln_mu_g = np.log(np.where(present, S / safe_w, 1.0))
            own = np.maximum(ln_mu_g - A / safe_w, 0.0)
            s_g = W / w_tot[:, None]
            bterm = np.where(present, s_g * (ln_mu - ln_mu_g), 0.0)
            wterm = np.where(present, s_g * own, 0.0)
        else:
            # Theil weights by INCOME share: a group whose income is
            # all zero contributes nothing to either part
            has = present & (S > 0)
            safe_s = np.where(has, S, 1.0)
            ln_mu_g = np.log(np.where(has, S / safe_w, 1.0))
            own = np.maximum(A / safe_s - ln_mu_g, 0.0)
            v_g = S / s_tot[:, None]
            bterm = np.where(has, v_g * (ln_mu_g - ln_mu), 0.0)
            wterm = np.where(has, v_g * own, 0.0)
        b = np.maximum(bterm.sum(axis=1), 0.0)
        w = wterm.sum(axis=1)
    defined = np.isfinite(mu) & (mu > 0)
    return np.where(defined, b, np.nan), np.where(defined, w, np.nan)


def make_plan(df: pd.DataFrame, value_fields, stats_wanted: dict,
              decompose_by: dict, min_group, members) -> Plan:
    """Validate a decomposition request and prepare its sums.

    `df` holds the value columns (full length, row-aligned) and gains
    the group codes (plan.code_column) and two to four per-person
    quantities per value field (plan.sum_vars) - see the module
    docstring. `members` is the reference population: rows outside it
    are nobody's neighbour, so they are not counted when reporting
    missing groups, nor in the centring constant.
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
    mem = np.asarray(members, dtype=bool)
    no_group = codes < 0
    # the rescaling constant, as a log: the mean log of the values that
    # will be summed. Any constant is exact; this one keeps every mean
    # near 1, where its log loses nothing.
    centre = {}
    for f in fields:
        base = df[f].to_numpy(float)
        use = mem & ~no_group & np.isfinite(base) & (base > 0)
        centre[f] = float(np.log(base[use]).mean()) if use.any() else 0.0
    plan = Plan(gname, labels, fields, idx, mg, centre)
    df[plan.code_column] = codes
    for f in fields:
        base = df[f].to_numpy(float)
        lost = int((mem & np.isfinite(base) & no_group).sum())
        if lost:
            print(f"[decompose] {lost} row(s) have a value of '{f}' "
                  f"but no '{gname}': they are left out of the "
                  f"decomposition, and stay in every other statistic "
                  f"of '{f}'.")
        have = np.isfinite(base)
        pos = have & (base > 0)
        y = np.where(have, base * math.exp(-centre[f]), 0.0)
        # ln y where it exists. A zero under MLD is refused by the
        # engine before any of this is read; under Theil y ln y is 0
        # at y = 0, which is the limit.
        lny = np.zeros(len(base))
        lny[pos] = np.log(y[pos])
        q = plan.quantities[f]
        df[q["W"]] = have.astype(float)
        df[q["S"]] = y
        if "L" in q:
            df[q["L"]] = lny
        if "Q" in q:
            df[q["Q"]] = y * lny
    rule = (f"each holds at least {mg:g} people" if mg > 0
            else "no minimum group size")
    used = [s for s in INDICES if any(s in idx[f] for f in fields)]
    print(f"[decompose] '{gname}' splits {', '.join(fields)} into "
          f"{len(labels)} groups ({', '.join(labels)}); "
          f"{' and '.join(PREFIX[s] for s in used)} reported where at "
          f"least two groups are present and {rule}.")
    return plan
