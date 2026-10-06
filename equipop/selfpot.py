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

# --- CELL SHAPE, BACKLOG 158 -----------------------------------------
# The formula above is AREA-based and correct. It was being handed the
# wrong area: hex.py sets `unit_size = hex_size`, the width across
# flats, and this module squared it. A hexagon 100 m across the flats
# holds 8,660 m2, not 10,000 - so the radius came out 7.46% too large
# (39.89 m where 37.13 m is right at k=50 of 100) and the intra-cell
# decay distance 9.0% too large (38.26 m against 35.10 m), because
# that used the SQUARE's mean-distance constant too.
#
# Found by an external review of 1.29.6 and open ever since. It is why
# tests/reachability.py refuses hex cells at every door: "it should not
# be offered at a door until that is fixed."
#
# THE SHAPE IS THE ONE NEW FACT, and everything else is derived from
# it, so an area cannot be set that disagrees with the geometry it
# came from. `unit_size` keeps its per-shape meaning - a square's SIDE,
# a hexagon's WIDTH ACROSS FLATS - which is what hex.py already
# documents as "the natural analogue of unit_size".
#
# The square factors are exactly 1.0 and the existing constant, so
# every square run is an IDENTITY and no published number can move.
# That is the point of doing it this way rather than by changing what
# CellData stores.

# Regular hexagon, width across flats w: circumradius a = w/sqrt(3),
# area = (3*sqrt(3)/2)*a^2 = (sqrt(3)/2)*w^2.
HEX_AREA_FACTOR = math.sqrt(3.0) / 2.0                     # 0.8660

# Mean distance from the centre of a regular hexagon to a uniform point
# in it, as a fraction of the width across flats. Derived in polar
# coordinates over one of the twelve congruent sectors, where the
# boundary is r(theta) = h / cos(theta) with h the apothem = w/2:
#
#   mean = [ (h^3/3) * int_0^(pi/6) sec^3 ] / [ (h^2/2) * int_0^(pi/6) sec^2 ]
#        = (w/2) * (2*sqrt(3)/3) * (1/3 + ln(3)/4)
#        = w * (1/sqrt(3)) * (1/3 + ln(3)/4)
#
# = 0.3510220..., confirmed by Monte Carlo over 2.6M points (0.3510).
HEX_MEAN_INTRACELL = (1.0 / math.sqrt(3.0)) * (1.0 / 3.0
                                               + math.log(3.0) / 4.0)

#: shape -> (area as a multiple of unit_size^2,
#:           mean centre-to-point distance as a multiple of unit_size)
SHAPES = {
    "square": (1.0, MEAN_INTRACELL),
    "hex": (HEX_AREA_FACTOR, HEX_MEAN_INTRACELL),
}


def _factors(shape):
    try:
        return SHAPES[str(shape or "square").lower()]
    except KeyError:
        raise ValueError(
            f"unknown cell shape {shape!r} - known shapes are "
            f"{sorted(SHAPES)}. The shape decides a cell's AREA and "
            "the mean distance to a person inside it, so it cannot be "
            "guessed.")


def cell_area(unit_size: float, shape: str = "square") -> float:
    """A cell's area in m2, from its size and its shape."""
    return _factors(shape)[0] * float(unit_size) ** 2


def mean_intracell(unit_size: float, shape: str = "square") -> float:
    """Mean distance from a cell's centre to a uniform point in it."""
    return _factors(shape)[1] * float(unit_size)

# Where the circle stops fitting: the radius reaches the square's
# half-side exactly at k/n = pi/4 = 0.785, and at k = n it would be
# 0.564c - outside the cell. That is the corner the docstring warns
# about, and why radius_for_k() never extrapolates past k = n.
DEFAULT_SELF_POTENTIAL = 1.0


def radius_for_k(unit_size: float, k: float, n_reached: float,
                 s: float = DEFAULT_SELF_POTENTIAL, *,
                 shape: str = "square") -> float:
    """The distance at which k of a cell's n people are reached.

    unit_size : cell SIZE in metres - a square's side, a hexagon's
                width across flats. What that size means geometrically
                is `shape`'s business, not this argument's.
    k         : how many people were asked for
    n_reached : how many the cell actually holds
    s         : self-potential, 0 = old behaviour, 1 = equal-area
    shape     : "square" (default) or "hex" - BACKLOG 158. The default
                reproduces every pre-1.52 result exactly, because the
                square's area factor is 1.0.

    Returns 0.0 when the setting is off, so the caller can stay
    branch-free.
    """
    if s <= 0.0 or k <= 0.0 or n_reached <= 0.0 or unit_size <= 0.0:
        return 0.0
    # never extrapolate past the people the cell actually has: asking
    # for more than n is not a question this cell can answer.
    k = min(float(k), float(n_reached))
    return float(s) * math.sqrt(
        cell_area(unit_size, shape) * k / (float(n_reached) * math.pi))


def decay_distance(unit_size: float,
                   s: float = DEFAULT_SELF_POTENTIAL, *,
                   shape: str = "square") -> float:
    """The distance to charge a person in your OWN cell when weighting
    by distance decay. No k here, so it is the mean centre-to-point
    distance rather than a radius - and that constant is the SHAPE's,
    not a universal one (BACKLOG 158): 0.3826 of a square's side,
    0.3510 of a hexagon's width across flats."""
    if s <= 0.0 or unit_size <= 0.0:
        return 0.0
    return float(s) * mean_intracell(unit_size, shape)


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
