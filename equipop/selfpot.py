"""
selfpot.py - SELF-POTENTIAL: how far away your own cell's people are.

The name is John's, from accessibility research, and the setting is
not new - EquiPop has always had it, fixed at zero and invisible.

THE PROBLEM IT NAMES. Every origin is a cell midpoint and so is every
member, so a person in your own cell sits at distance 0. When your
own cell already holds k people, Dist_k is therefore 0 - and worse,
k stops being a parameter: 3,002 people in one 100 m cell gave
N_100 = N_1000 = 3,002 and Dist_100 = Dist_1000 = 0.0 m, with no
message. Two different questions, one answer. (BACKLOG 95.)

THE RULE. Spread the cell's people evenly across it and ask how far
you must go to reach k of them:

    d = s * sqrt(A * k / (n * pi))          s in [0, 1]

s = 0     the old behaviour, everyone at the centre with you
s = 0.71  (1/sqrt 2) the MEDIAN - half of them are nearer than this
s = 1.0   the EQUAL-AREA RADIUS, and the default

WHY 1.0 IS THE DEFAULT AND NOT A GUESS. For points scattered evenly
at density lambda the expected distance to the k-th nearest is
sqrt(k / (lambda * pi)) - which is this formula exactly. So it does
not substitute for the measurement, it estimates it. Measured against
truth on a uniform field: 0.49% out at k=25, 0.18% at k=100, 0.10% at
k=400, 0.09% at k=1000. An order of magnitude tighter than the
sphere-against-ellipsoid error of BACKLOG 93.

AND THE CIRCLE FITS. At s = 1 the radius is 0.399c against a half-side
of 0.5c, so the circle lies ENTIRELY INSIDE the square: nothing is
clipped and no corner is missed. The circle assumption only begins to
cost anything above pi/4 = 78.5% of a cell's people, by which point
the neighbourhood is leaving the cell anyway.

DECAY NEEDS THE SAME SETTING ON A DIFFERENT SCALE, because a decay
has no k. There the question is "how far is a typical person in my own
cell", which is the mean distance from a square's centre to a uniform
point in it - 0.3826c exactly (0.3761c for the equal-area disc: close
enough that the choice does not matter, but the square is the truth
here). Without it the origin cell keeps weight 1.0, the single largest
weight in the whole calculation, on the mass we know least about.

BOTH ENGINES USE THIS MODULE. run_knn_counts and run_knn_stats agree
by regression test, so the rule lives once or it drifts.
"""

import math

# Mean distance from the centre of a unit square to a uniform random
# point inside it: (sqrt(2) + ln(1 + sqrt(2))) / 6. Verified against
# numerical integration (0.3826).
MEAN_INTRACELL = (math.sqrt(2.0) + math.log(1.0 + math.sqrt(2.0))) / 6.0

# Where the circle stops fitting: the radius reaches the square's
# half-side exactly at k/n = pi/4 = 0.785, and at k = n it would be
# 0.564c - outside the cell. That is the corner the docstring warns
# about, and why radius_for_k() never extrapolates past k = n.
DEFAULT_SELF_POTENTIAL = 1.0


def radius_for_k(unit_size: float, k: float, n_reached: float,
                 s: float = DEFAULT_SELF_POTENTIAL) -> float:
    """The distance at which k of a cell's n people are reached.

    unit_size : cell side in metres (cells are square by construction)
    k         : how many people were asked for
    n_reached : how many the cell actually holds
    s         : self-potential, 0 = old behaviour, 1 = equal-area

    Returns 0.0 when the setting is off, so the caller can stay
    branch-free.
    """
    if s <= 0.0 or k <= 0.0 or n_reached <= 0.0 or unit_size <= 0.0:
        return 0.0
    # never extrapolate past the people the cell actually has: asking
    # for more than n is not a question this cell can answer.
    k = min(float(k), float(n_reached))
    return float(s) * math.sqrt(
        (float(unit_size) ** 2) * k / (float(n_reached) * math.pi))


def decay_distance(unit_size: float,
                   s: float = DEFAULT_SELF_POTENTIAL) -> float:
    """The distance to charge a person in your OWN cell when weighting
    by distance decay. No k here, so it is the mean centre-to-point
    distance rather than a radius."""
    if s <= 0.0 or unit_size <= 0.0:
        return 0.0
    return float(s) * MEAN_INTRACELL * float(unit_size)


def check(s) -> float:
    """Validate and return the setting. Refuses loudly rather than
    clamping, because a silently corrected parameter is exactly the
    failure this module exists to end."""
    if s is None:
        return DEFAULT_SELF_POTENTIAL
    try:
        v = float(s)
    except (TypeError, ValueError):
        raise ValueError(
            f"self-potential must be a number between 0 and 1, got {s!r}")
    if not (0.0 <= v <= 1.0):
        raise ValueError(
            "self-potential must lie between 0 (everyone in your own "
            "cell is at the centre with you) and 1 (the equal-area "
            f"radius); got {v:g}")
    return v
