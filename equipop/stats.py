"""
stats.py - statistical functions for k-nearest neighbourhoods.

THE THREE-TIER DESIGN (as agreed):

Tier 1 - binary treatments: every statistic is EXACT from the two
         running counts (n, t) alone. No individual data needed.
Tier 2 - continuous mean/SD/SE: exact from running moments
         (handled through the value arrays here, since tier 3 data
         is present anyway; a pure-moments path can be added for
         aggregated-only data later).
Tier 3 - continuous median/Gini: require the individual values
         encountered during the search - the reason individual-level
         in-data exists.

EXTENSIBILITY: both registries below map a short statistic name to a
plain function. To add a statistic later, add one entry:

    VALUE_STATS["p90"] = lambda x: float(np.percentile(x, 90))

and request "p90" in the stats specification of run_knn_stats().

Conventions (documented, easy to change here in one place):
  - continuous SD uses the sample formula (ddof=1); SE = SD/sqrt(nv)
  - binary SD is the Bernoulli sqrt(p(1-p)); SE = sqrt(p(1-p)/n)
  - entropy is Shannon entropy in NATURAL units (nats); divide by
    ln(2) for bits
  - binary Gini reduces mathematically to 1 - p (equality when
    everyone has the attribute; see README note)
  - Gini is undefined (NaN) when the mean is 0 or nv < 2
"""

import math
import numpy as np


# ---------------------------------------------------------------- helpers
def check_gini_input(values, where: str = "this variable") -> None:
    """Refuse a Gini over data containing negative values.

    BACKLOG 154, RULED by John. The rank formula is only bounded in
    [0, 1] for non-negative data: gini_sorted([-5, 10]) returns 1.5,
    which reads as a conventional Gini and is not one.

    ArcGIS Pro has refused this since it gained the measure; the core
    and the QGIS path did not - and QGIS has Gini in its DEFAULT
    statistics list, so the same data was refused through one door
    and silently accepted through another. This is Pro's rule,
    promoted, so every door and the Python API agree.

    WHY NOT REPAIR IT INSTEAD. John proposed shifting every value so
    the minimum becomes zero, first per neighbourhood and then - much
    better - once across the whole reference population. The global
    version does remove the incomparability of a local shift, but the
    Gini is NOT translation-invariant: adding c multiplies it by
    mean/(mean + c), so one shift compresses LOW-MEAN neighbourhoods
    hardest. Measured on two areas with true Ginis 0.400 (poor) and
    0.131 (rich), a single debt of -80 anywhere in the country
    REVERSES the ranking. That is a sign error on the finding, and
    worst exactly where it matters.
    Generalised definitions for negative data exist (Raffinetti and
    colleagues, among others). EquiPop is not an inequality toolkit,
    and adopting one from memory would be worse than refusing.
    """
    a = np.asarray(values, dtype=float)
    if not np.isfinite(a).any():
        return
    if float(np.nanmin(a)) < 0:
        raise ValueError(
            f"Gini is not defined for negative values and {where} has "
            "some. Remove the Gini, or use a non-negative variable. "
            "(Shifting the values to make them non-negative changes "
            "the answer: the Gini is not translation-invariant, and a "
            "single shift compresses low-mean neighbourhoods hardest.)")


def gini_sorted(x: np.ndarray) -> float:
    """
    Gini coefficient of a 1-D array (will be sorted internally).
    Uses the standard rank formula:
        G = (2 * sum(i * x_i) / (n * sum(x))) - (n + 1) / n
    with i = 1..n over ascending-sorted values.

    Callers must screen the variable with check_gini_input() first
    (BACKLOG 154); this is the per-neighbourhood inner loop and is
    not the place to raise.
    """
    nv = len(x)
    if nv < 2:
        return float("nan")
    s = float(x.sum())
    if s <= 0:
        return float("nan")
    xs = np.sort(x)
    i = np.arange(1, nv + 1)
    return float((2.0 * np.dot(i, xs)) / (nv * s) - (nv + 1) / nv)


# --------------------------------------------- tier 1: binary, from (n, t)
def _p(n, t):
    return t / n if n else float("nan")

BINARY_STATS = {
    "ratio":   lambda n, t: _p(n, t),
    "sd":      lambda n, t: math.sqrt(_p(n, t) * (1 - _p(n, t))) if n else float("nan"),
    "se":      lambda n, t: math.sqrt(_p(n, t) * (1 - _p(n, t)) / n) if n else float("nan"),
    "entropy": lambda n, t: (
        0.0 if n == 0 or t in (0, n)
        else -(_p(n, t) * math.log(_p(n, t))
               + (1 - _p(n, t)) * math.log(1 - _p(n, t)))
    ),
    "gini":    lambda n, t: (1.0 - _p(n, t)) if (n and t > 0) else float("nan"),
}

# ------------------------------------- tiers 2+3: continuous, from values
VALUE_STATS = {
    "mean":   lambda x: float(np.mean(x)) if len(x) else float("nan"),
    "median": lambda x: float(np.median(x)) if len(x) else float("nan"),
    "sd":     lambda x: float(np.std(x, ddof=1)) if len(x) > 1 else float("nan"),
    "se":     lambda x: (float(np.std(x, ddof=1)) / math.sqrt(len(x))
                         if len(x) > 1 else float("nan")),
    "gini":   gini_sorted,
    # ------------------------------------------------- v1.16 additions
    "var":    lambda x: float(np.var(x, ddof=1)) if len(x) > 1 else float("nan"),
    "min":    lambda x: float(np.min(x)) if len(x) else float("nan"),
    "max":    lambda x: float(np.max(x)) if len(x) else float("nan"),
    "count":  lambda x: float(len(x)),
    "sum":    lambda x: float(np.sum(x)) if len(x) else 0.0,
    "range":  lambda x: (float(np.max(x) - np.min(x)) if len(x)
                         else float("nan")),
}


def is_percentile(s: str) -> bool:
    """A dynamic value statistic: 'p10', 'p25', 'p97.5', ...
    (documented convention: LINEAR interpolation, numpy default)."""
    if not (isinstance(s, str) and len(s) > 1 and s[0] in "pP"):
        return False
    try:
        q = float(s[1:])
    except ValueError:
        return False
    return 0.0 <= q <= 100.0


def value_stat(s: str, x) -> float:
    """One value statistic by name - registry entries plus dynamic
    percentiles pNN. Raises KeyError for unknown names (validated
    upstream with a loud list)."""
    if is_percentile(s):
        return (float(np.percentile(x, float(s[1:]), method="linear"))
                if len(x) else float("nan"))
    return VALUE_STATS[s](x)


def stat_prefix(s: str) -> str:
    """Column prefix for a statistic name, percentiles included
    (p25 -> P25, p97.5 -> P97_5).

    BACKLOG 152. This used to end with .rstrip("_0"), and rstrip
    removes any run of those CHARACTERS rather than one exact suffix.
    So p1, p10.0 and p100.0 all became "P1", and p50.0 became "P5" -
    three different percentiles sharing one column, the last one
    silently overwriting the others. The run completed and the labels
    lied. It bit exactly the round percentiles people ask for most,
    while p97.5 and p99.9 were fine, which is why it survived.

    Now the number is normalised ONCE and a trailing ".0" is removed
    as a whole, never character by character.
    """
    if is_percentile(s):
        v = float(s[1:])
        # 10.0 -> "10", 97.5 -> "97.5", and no float noise
        txt = f"{v:.10f}".rstrip("0").rstrip(".")
        return "P" + txt.replace(".", "_")
    return PREFIX[s]

# short column prefixes per statistic (edit here to rename output)
PREFIX = {
    "ratio": "R", "mean": "Mean", "median": "Med", "sd": "SD",
    "se": "SE", "entropy": "Ent", "gini": "Gini",
    "var": "Var", "min": "Min", "max": "Max", "count": "Cnt",
    "sum": "Sum", "range": "Rng",
}
