"""
describe.py - what a result column holds, in one sentence.

v1.56.0, BACKLOG 410. John's first live Pro run of 1.55.1 showed a
table of MLDb_ / MLDw_ / MLDsh_ columns, every visible value <Null>,
and nothing on screen to say what the columns meant or why they were
empty. His words: "the w, sh, etc, are not explained what I can see".

WHAT WAS ALREADY THERE, and why this replaces it. The run record had a
describer - a list of regular expressions in meta.py - and measured on
a real run it said "(no definition registered)" for 5 of 7 machine 1
columns, every T_ and R_ group column among them, and for 12 of 19
machine 2 columns. Its Dist_ sentence said "0 = satisfied within the
origin cell", which self-potential (BACKLOG 95) made untrue in 1.29.5,
and called the unit metres where it is map units (BACKLOG 160). A
description nothing checked had rotted exactly as the backlog's own
head once did.

So there is ONE describer now, used by everything that explains a
column - the run record, Pro's field aliases, QGIS's field aliases,
and the legend in the run messages - and a test holds it to the
column PREDICTOR (equipop.doors.fields), so a column a door can
produce and this cannot describe fails the suite.

READ BY NAME, HELPED BY CONTEXT. A name is prefix_field_suffix, and a
field may itself hold underscores and digits: `Mean_inc_2020_100` is
field inc_2020 at k=100, while `Mean_inc_r500_5` is field inc at a
radius of 500.5. Given the field names the run used, the split is
exact; without them, the shortest field that leaves a valid suffix is
taken, which is right for every name EquiPop writes unless a field is
itself named like a radius.
"""

from __future__ import annotations

import re

#: The suffix of a result name: k, a radius (decimal point written as
#: an underscore - BACKLOG 337), or an effort limit.
_SUFFIX = re.compile(r"^(?:(?P<k>\d+)|r(?P<r>\d+(?:_\d+)?)|"
                     r"tau(?P<tau>\d+(?:_\d+)?))$")

#: Families with no field between prefix and suffix.
_BARE = {
    "N": "Number counted {where}",
    "ND": "Decay-weighted number counted {where}",
    "Dist": ("Distance, in map units, needed to reach the {n} nearest "
             "(k={n}); where the point's own cell already holds them it "
             "is estimated inside the cell, or 0 if self-potential is 0"),
    "Rounds": "Effort rounds needed to reach the {n} nearest (k={n})",
}

#: Families of machine 1 whose middle part is a GROUP being counted.
_GROUP = {
    "T": "Number of {g} {where}",
    "R": "Share of {g} {where} (T / N)",
    "TD": "Decay-weighted number of {g} {where}",
    "RD": "Decay-weighted share of {g} {where}",
}

#: Families of machine 2 whose middle part is a VALUE field.
_VALUE = {
    "Nv": "How many {where} have a value of {f}",
    "Mean": "Mean of {f} {where}",
    "Med": "Median of {f} {where}",
    "SD": "Standard deviation of {f} {where}",
    "SE": "Standard error of the mean of {f} {where}",
    "Var": "Variance of {f} {where}",
    "Min": "Smallest value of {f} {where}",
    "Max": "Largest value of {f} {where}",
    "Cnt": "Number of values of {f} {where}",
    "Sum": "Sum of {f} {where}",
    "Rng": "Range of {f} (largest minus smallest) {where}",
    "Gini": "Gini coefficient of {f} {where}; 0 = everyone equal",
    "Ent": "Shannon entropy of {f} {where}, in nats",
    "MLD": ("Mean log deviation (MLD) of {f} {where}; inequality, "
            "0 = everyone equal"),
    "Theil": "Theil index of {f} {where}; inequality, 0 = everyone equal",
}

#: The between/within split (BACKLOG 405). {grp} is the grouping field.
_SPLIT = {
    "Ng": "How many groups of {grp} are present {where}",
    "NgMin": "People in the smallest group of {grp} present {where}",
    "NgN": ("People with a value of {f} AND a group of {grp} {where} - "
            "who the split covers; Nv_ counts everyone with a value"),
    "MLDb": "MLD of {f} BETWEEN the groups of {grp}, {where}",
    "MLDw": "MLD of {f} WITHIN the groups of {grp}, {where}",
    "MLDsh": ("Share of the MLD of {f} that lies between the groups "
              "of {grp}, {where}; 0 to 1"),
    "Theilb": "Theil of {f} BETWEEN the groups of {grp}, {where}",
    "Theilw": "Theil of {f} WITHIN the groups of {grp}, {where}",
    "Theilsh": ("Share of the Theil of {f} that lies between the groups "
                "of {grp}, {where}; 0 to 1"),
}
#: Which split columns are emptied by the minimum-group rule.
_RULED = {"MLDb", "MLDw", "MLDsh", "Theilb", "Theilw", "Theilsh"}

_FIXED = {
    "N_local": "Number in this point's own cell",
}

#: Longest first, so NgMin and NgN are tried before Ng, Ng before N.
_PREFIXES = sorted(set(_BARE) | set(_GROUP) | set(_VALUE) | set(_SPLIT),
                   key=len, reverse=True)


def _where(suffix: str):
    """'among the 100 nearest (k=100)' / 'within 500.5 map units
    (r=500.5)' - or None if the suffix is not one EquiPop writes."""
    m = _SUFFIX.match(suffix)
    if not m:
        return None, None
    if m["k"] is not None:
        return f"among the {m['k']} nearest (k={m['k']})", m["k"]
    if m["r"] is not None:
        r = m["r"].replace("_", ".")
        return f"within {r} map units (r={r})", None
    t = m["tau"].replace("_", ".")
    return f"within an effort of {t} (tau={t})", None


def _ordinal(txt: str) -> str:
    if "." in txt:
        return f"{txt}th"
    n = int(txt)
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def _split_field(rest: str, fields):
    """(field, suffix) for 'income_obs_100', using the run's field
    names when they are known."""
    for f in sorted(fields or (), key=len, reverse=True):
        if rest.startswith(f + "_") and _SUFFIX.match(rest[len(f) + 1:]):
            return f, rest[len(f) + 1:]
    m = re.match(r"^(.+?)_(\d+|r\d+(?:_\d+)?|tau\d+(?:_\d+)?)$", rest)
    return (m.group(1), m.group(2)) if m else (None, None)


def describe(name: str, fields=(), split_by: str | None = None,
             min_group: float | None = None) -> str | None:
    """One sentence for one EquiPop result column, or None if the name
    is not one EquiPop writes.

    `fields` - the value fields and group names the run used, which
    makes the split of a name exact; `split_by` - the grouping field of
    a between/within split; `min_group` - its minimum group size, which
    the split's columns mention because it is why they can be empty.
    """
    if name in _FIXED:
        return _FIXED[name]
    pm = re.match(r"^P(\d+(?:_\d+)?)_(.+)$", name)
    if pm:
        f, suf = _split_field(pm.group(2), fields)
        where, _ = _where(suf) if suf else (None, None)
        if not where:
            return None
        pct = pm.group(1).replace("_", ".")
        return f"{_ordinal(pct)} percentile of {f} {where}"
    for p in _PREFIXES:
        if not name.startswith(p + "_"):
            continue
        rest = name[len(p) + 1:]
        if p in _BARE:
            where, k = _where(rest)
            if not where or ("{n}" in _BARE[p] and k is None):
                return None
            return _BARE[p].format(where=where, n=k)
        f, suf = _split_field(rest, fields)
        if f is None:
            return None
        where, _ = _where(suf)
        if p in _GROUP:
            return _GROUP[p].format(g=f, where=where)
        if p in _VALUE:
            return _VALUE[p].format(f=f, where=where)
        grp = split_by or "the grouping field"
        text = _SPLIT[p].format(f=f, grp=grp, where=where)
        if p in _RULED:
            text += " - " + _rule(min_group)
        return text
    return None


def _rule(min_group) -> str:
    """Why a split column can be empty - said in one place."""
    return ("EMPTY where only one group is present"
            + (f" or a group present holds fewer than {min_group:g} "
               "people" if min_group else ""))


def context_from(kw: dict) -> dict:
    """describe()'s context from the arguments a door passed to
    dispatch - the one place a door's request is turned into it."""
    fields = list((kw.get("values") or {}).keys()) \
        + list((kw.get("treat") or {}).keys())
    ctx = {"fields": fields, "split_by": None, "min_group": None}
    dec = kw.get("decompose_by")
    if dec:
        from .decompose import resolve_min_group
        ctx["split_by"] = str(next(iter(dec)))
        ctx["min_group"] = resolve_min_group(kw.get("min_group"))
    return ctx


def describe_all(names, kw: dict | None = None) -> dict:
    """{name: sentence} for every name EquiPop can describe; names it
    cannot are left out, so a caller never writes a wrong alias."""
    ctx = context_from(kw or {})
    out = {}
    for n in names:
        d = describe(n, **ctx)
        if d:
            out[n] = d
    return out


def legend(names, kw: dict | None = None) -> list:
    """The lines a run prints: one per FAMILY of column, shown on its
    first instance, so ten k values do not make ten lines."""
    ctx = context_from(kw or {})
    seen, lines, ruled = set(), [], False
    tail = " - " + _rule(ctx["min_group"])
    for n in names:
        fam = _family(n)
        if fam is None or fam in seen:
            continue
        d = describe(n, **ctx)
        if not d:
            continue
        seen.add(fam)
        # the rule is said ONCE, below, not on six lines in a row
        if fam in _RULED and d.endswith(tail):
            d, ruled = d[:-len(tail)], True
        lines.append(f"  {n:<24} {d}")
    if not lines:
        return []
    out = (["[columns] what the result columns hold - one line per "
            "kind, shown on its first instance; each repeats for "
            "every field and every k or radius:"] + lines)
    if ruled:
        out.append(f"  The between/within columns are {_rule(ctx['min_group'])}"
                   " - the [decompose] lines below say how many places "
                   "that was, and why.")
    return out


def _family(name: str):
    if name in _FIXED:
        return name
    if re.match(r"^P\d+(?:_\d+)?_", name):
        return "P"
    for p in _PREFIXES:
        if name.startswith(p + "_"):
            return p
    return None
