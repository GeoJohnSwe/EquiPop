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


def check_mld_input(values, where: str = "this variable") -> None:
    """Refuse a mean log deviation over data holding zero or less.

    v1.55.0, BACKLOG 405, John's ruling. MLD is the mean of
    ln(mean / value), so ONE zero makes it infinite and a negative has
    no logarithm at all.

    WHY NOT REPLACE THE ZEROS WITH A SMALL NUMBER. John asked, and it
    was measured rather than argued. Three people on 167, 176 and 189
    have an MLD of 0.0013; add one person whose zero is replaced by
    10, 1, 0.1, 0.01 or 0.001 and the MLD is 0.45, 1.01, 1.58, 2.16 or
    2.73. The replacement IS the answer - every tenfold step adds
    exactly ln(10)/n. Worse, the same rule ("zero becomes 1") gives
    2.73 in SEK, 1.01 in thousand SEK and 0.34 in million SEK: an
    inequality index whose value depends on the CURRENCY UNIT, which
    MLD by itself never does. And the distortion grows with the share
    of zeros, which is highest exactly where an inequality study looks
    - the same shape as the Gini shift ruled against in BACKLOG 154.

    Theil's T is defined at zero (the limit of y ln y is 0), so it is
    the measure to use on a variable that has zeros, and the message
    says so.
    """
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    if not a.size:
        return
    bad = int((a <= 0).sum())
    if bad:
        raise ValueError(
            f"MLD (mean log deviation) is not defined when a value is "
            f"zero or less, and {where} has {bad} such value(s). It "
            "takes the logarithm of every value, so a single zero "
            "makes it infinite. Use Theil instead - it accepts zeros. "
            "(Replacing the zeros with a small number does not rescue "
            "MLD: the number chosen becomes the answer, and the result "
            "then depends on the currency unit.)")


def check_theil_input(values, where: str = "this variable") -> None:
    """Refuse Theil's T over data holding negative values.

    v1.55.0, BACKLOG 405. Theil's T is (1/n) sum (y/mean) ln(y/mean):
    a ZERO contributes nothing (y ln y tends to 0), which is why it is
    the measure offered when MLD refuses a zero, but a negative value
    has no logarithm. Refused rather than shifted, for the reason
    BACKLOG 154 gives for the Gini: neither index is
    translation-invariant, so one shift moves low-mean neighbourhoods
    most.
    """
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    if not a.size:
        return
    bad = int((a < 0).sum())
    if bad:
        raise ValueError(
            f"Theil is not defined for negative values, and {where} "
            f"has {bad}. Remove Theil, or use a non-negative variable. "
            "(Shifting the values to make them non-negative changes "
            "the answer: Theil is not translation-invariant.)")


def _mld(x) -> float:
    """MLD of an expanded sample - the reference the weighted path in
    equipop/wstats.py is held to."""
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return float("nan")
    m = float(np.mean(x))
    if not m > 0 or float(np.min(x)) <= 0:
        return float("nan")
    if float(np.min(x)) == float(np.max(x)):
        return 0.0                       # one value: no inequality
    return max(float(np.mean(np.log(m / x))), 0.0)


def _theil(x) -> float:
    """Theil's T of an expanded sample. A zero contributes nothing."""
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return float("nan")
    m = float(np.mean(x))
    if not m > 0 or float(np.min(x)) < 0:
        return float("nan")
    if float(np.min(x)) == float(np.max(x)):
        return 0.0
    r = x / m
    pos = r > 0
    return max(float(np.sum(r[pos] * np.log(r[pos])) / len(x)), 0.0)


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
    # ------------------------------------------------- v1.55 additions
    # BACKLOG 405. The two decomposable inequality indices: they split
    # EXACTLY into between-group plus within-group parts, which the
    # Gini does not (it leaves an overlap term). See equipop/decompose.
    "mld":    _mld,       # GE(0), mean log deviation - values > 0
    "theil":  _theil,     # GE(1), Theil's T - values >= 0
}

#: The binary family deliberately has NO mld and NO theil. For a 0/1
#: variable with share p, Theil is exactly -ln p and MLD is infinite
#: (every 0 is the logarithm of zero) - a transform of the share R
#: that machine 1 already reports, dressed as an inequality index.
#: Measured and recorded in BACKLOG 405. A 0/1 field belongs in a
#: decomposition as the GROUP, not as the outcome.
BINARY_REFUSED = {
    "mld": ("for a 0/1 variable MLD is infinite - every 0 is the "
            "logarithm of zero"),
    "theil": ("for a 0/1 variable with share p, Theil is exactly "
              "-ln(p): the share R in disguise, which adds nothing"),
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
    "mld": "MLD", "theil": "Theil",                  # BACKLOG 405
}
