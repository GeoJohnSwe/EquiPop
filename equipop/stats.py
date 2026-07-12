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
def gini_sorted(x: np.ndarray) -> float:
    """
    Gini coefficient of a 1-D array (will be sorted internally).
    Uses the standard rank formula:
        G = (2 * sum(i * x_i) / (n * sum(x))) - (n + 1) / n
    with i = 1..n over ascending-sorted values.
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
}

# short column prefixes per statistic (edit here to rename output)
PREFIX = {
    "ratio": "R", "mean": "Mean", "median": "Med", "sd": "SD",
    "se": "SE", "entropy": "Ent", "gini": "Gini",
}
