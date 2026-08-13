"""
overshoot.py - what to do with the ring that crosses k (BACKLOG 99).

THE PROBLEM. EquiPop grows a neighbourhood outward from each origin
until it holds k people. The ring that crosses k almost never lands on
k exactly, and EquiPop has always taken that ring WHOLE. Ask a 3x3 of
cells holding ten people each for k=11 and you receive 50.

That is not a rounding nuisance. On a planted sharp boundary - all of
one group west, none east, which is what segregation looks like - the
share R_k in the boundary cell itself reads 0.20 under the whole-ring
rule and 0.02 under a proportional share. A tenfold difference in a
segregation measure, in the exact cell where segregation is being
measured. The damage is concentrated at SMALL k and AT BOUNDARIES,
which is precisely where the value of the method lies; on a smooth
gradient a symmetric ring averages out, which is why it stayed hidden.

John Östh, who wrote the original method, 1.29.5: "the original
EquiPop was developed to counter the overshoot effects so this is not
a wish. We have to manage this."

THREE MODES, his naming:

  whole         take the whole ring, as EquiPop always has
  proportional  every cell in the ring contributes the same fraction,
                so N_k = k exactly
  sampled       cells from the ring enter one at a time, in an order
                drawn from a seed, until k is reached

What 2 and 3 are to each other matters and must be said in the help
rather than discovered. An earlier design note recorded that
proportional is the EXPECTED VALUE of sampled - that sampled is
"proportional with noise". IT IS NOT, and this was measured, not
argued. Sampled is PROPORTIONAL ROUNDED UP TO A WHOLE CELL:

  - the two agree when the shortfall is a whole number of cells;
  - otherwise sampled overshoots to the next cell boundary, and
    averaging many draws does NOT converge on the proportional
    answer, because the overshoot is systematic rather than random;
  - the gap is widest exactly where this work matters - small k, big
    cells, boundaries. On John's own example, cells of ten and k=11,
    proportional lands on N=11 and sampled averages N=20 with R
    0.874 against proportional's 0.977.

So sampled REDUCES the overshoot (50 to 20 here) without removing it.

WHY SAMPLED IS KEPT ANYWAY, and it is not the reason an earlier note
gave. John, 1.30: this is how the ORIGINAL EquiPop estimated it - the
C# tool he wrote himself, first released in 2014, taking one cell at
a time. It is kept for FIDELITY TO THE PUBLISHED METHOD, so the
improvement of the newer modes can be stated as a number rather than
asserted.

BUT NOT BIT-IDENTICAL, and that must not be over-claimed. In the 2012
trial versions John pre-computed the list of next-nearest cells and
stored only a QUARTER of the distances, mirroring NW/SW/NE/SE - so a
step southwest was followed by its three mirror images. The original
within-ring order was therefore DETERMINISTIC AND GEOMETRIC, not
drawn from a seed. `sampled` reproduces the METHOD - whole cells,
one at a time, stopping at k - and cannot reproduce the exact
sequence. The C# tool and its licence generator are lost, so that
order cannot be recovered and the claim cannot be tightened.

Also from John: EquiPop Flow (2018-2020) moved to a breadth-first
search and ALSO recorded the maximum distance, which is why BACKLOG
115's rule has the history it does.

THE ARITHMETIC, for proportional:

    f   = (k - cumulative_before) / ring_total
    N_k = k exactly
    T_k = T_before + f * T_ring
    R_k = T_k / k
    Dist_k = sqrt(d_prev^2 + f * (d_ring^2 - d_prev^2))

The Dist_k line is not new. With d_prev = 0 and the ring being the
origin's own cell it is bit-identical to the self-potential formula
already shipped in selfpot.py - BACKLOG 95, 99 and 100 are one rule
with three uses.

WHAT THIS DOES NOT TOUCH. Radius runs have no k, so no crossing ring.
Same for decay sums and effort budgets (tau). A large part of the
surface is unaffected.

FRACTIONAL PEOPLE. Proportional produces them: a T_k of 0.25 is an
estimate, not a person. Defensible for counts and ratios, and said
plainly in the help. It is also why VALUE STATISTICS REFUSE this mode
- a quarter of a boundary cell has no median, no percentile and no
Gini. That needs weighted statistics with fractional weights, which
is BACKLOG 118.
"""

import numpy as np

# --- the modes -------------------------------------------------------

WHOLE = "whole"
PROPORTIONAL = "proportional"
SAMPLED = "sampled"

MODES = (WHOLE, PROPORTIONAL, SAMPLED)

#: What EquiPop does unless told otherwise.
#:
#: RULED BY JOHN, 1.30: proportional. It answers the question the
#: user actually asked, and leaving the overshoot on by default would
#: mean most users keep receiving the answer BACKLOG 99 exists to
#: correct - a tenfold error in R_k at a boundary at small k.
#:
#: An earlier session shipped `whole` here instead, on two arguments.
#: Both were weighed and neither survived. (1) "Flipping the default
#: in the release that introduces the rule regenerates the
#: conformance answer key, so a wrong implementation certifies
#: itself." The protection against that was never the default: it is
#: whether proportional can be checked against truth derived
#: INDEPENDENTLY of any key. It can - John's hand example (N=11,
#: Dist=15.81), the identity that share=1 reproduces the whole-ring
#: answer exactly, and the fact that `radius` is bit-identical to the
#: shipped self-potential formula. (2) "A user comparing 1.29.9 with
#: 1.30 would see 139 and this change tangled together." They would
#: not: all three modes ship, so isolating 139 is one parameter,
#: overshoot="whole". The default only decides what happens when
#: nobody chooses.
#:
#: THE HONEST COST: every k-based number EquiPop has ever produced
#: changes. The way back is one setting and it is named in the
#: release note.
DEFAULT = PROPORTIONAL

#: Kept because code and doors refer to it, and because the direction
#: of travel is now history rather than intention.
INTENDED_DEFAULT = PROPORTIONAL

#: Continental runs should choose proportional AND PRINT THE REASON.
#: The reason is not speed. WorldPop counts are fractional modelled
#: estimates, so sampled has no whole people to preserve and buys
#: only noise. Sampled is NOT forbidden there - a machine that
#: answers differently from its neighbour for convenience is the
#: "two doors disagree" family of defect.
CONTINENTAL_DEFAULT = PROPORTIONAL

CHOICES = {
    WHOLE: (
        "Whole ring - take every cell lying at the same distance "
        "(or, in an effort run, at the same effort) as the cell that "
        "reached k. This is what EquiPop has always done. N_k "
        "overshoots k, sometimes greatly."),
    PROPORTIONAL: (
        "Proportional share - every cell in that ring contributes the "
        "same fraction of its people, so N_k equals k exactly. "
        "Produces fractional people, which are estimates rather than "
        "persons; not available with value statistics."),
    SAMPLED: (
        "Sampled, seeded - cells from that ring enter one at a time, "
        "in an order drawn from the seed, until k is reached. THIS IS "
        "THE ORIGINAL EQUIPOP METHOD, as implemented in C# and first "
        "released in 2014, and it is kept so that results from the "
        "old tool can be reproduced and compared. Whole people, and "
        "the overshoot is at most one cell. It is NOT the "
        "proportional answer with the fractions removed: it is that "
        "answer rounded up to a whole cell, and repeating with "
        "different seeds does not average the difference away."),
}


def resolve(mode):
    """Normalise and check a mode name. None means the default."""
    if mode is None:
        return DEFAULT
    m = str(mode).strip().lower()
    if m not in MODES:
        raise ValueError(
            f"[overshoot] '{mode}' is not one of {', '.join(MODES)}. "
            "This decides what happens to the ring of cells that "
            "crosses k - see the manual. Nothing was computed.")
    return m


# --- the proportional arithmetic ------------------------------------

def share(k, cumulative_before, ring_total):
    """The fraction of the crossing ring that is taken.

    f = (k - cumulative_before) / ring_total, held inside [0, 1].

    A ring total of zero means an empty ring - nobody lives there -
    and no fraction of nobody reaches k, so the whole ring is taken
    and the growth continues outward. Returning 1.0 says exactly that
    without a special case at the call site.
    """
    total = np.asarray(ring_total, dtype=float)
    need = np.asarray(k, dtype=float) - np.asarray(cumulative_before,
                                                   dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        f = np.where(total > 0, need / total, 1.0)
    return np.clip(f, 0.0, 1.0)


def radius(d_prev, d_ring, f):
    """Dist_k when only a share f of the crossing ring is taken.

        r = sqrt(d_prev^2 + f * (d_ring^2 - d_prev^2))

    Area-linear between the inner and outer edge of the ring, which
    is the same rule selfpot.py already uses for the origin's own
    cell. With f = 1 it returns d_ring exactly, so the whole-ring
    answer is the f = 1 case of this formula and not a separate path.
    """
    a = np.asarray(d_prev, dtype=float) ** 2
    b = np.asarray(d_ring, dtype=float) ** 2
    return np.sqrt(a + np.asarray(f, dtype=float) * (b - a))


# --- the sampled order ----------------------------------------------

_GOLDEN = np.uint64(0x9E3779B97F4A7C15)
_MIX_A = np.uint64(0xBF58476D1CE4E5B9)
_MIX_B = np.uint64(0x94D049BB133111EB)


def _mix64(x):
    """splitmix64 finaliser: scramble an integer into a well-spread
    64-bit key. Pure arithmetic, vectorised, no RNG object to build
    per ring - which matters because this runs once per origin per k
    and the continental machine has millions of origins."""
    x = np.asarray(x, dtype=np.uint64).copy()
    with np.errstate(over="ignore"):
        x ^= x >> np.uint64(30)
        x *= _MIX_A
        x ^= x >> np.uint64(27)
        x *= _MIX_B
        x ^= x >> np.uint64(31)
    return x


def order_within_ring(cell_ids, seed, origin_id):
    """The order in which cells of the crossing ring enter, under
    `sampled`. Returns positions into `cell_ids`.

    John ruled the order RANDOM, from a seed, and his reasoning is
    the important part: in a sampled growth model there is no true
    "next best" cell. Nearest-first, clockwise-from-north or
    densest-first would each introduce a systematic direction into
    the result and dress it as a rule. The seed exists so that an
    exact replica of a run can be decomposed - not to make the choice
    meaningful.

    TWO PROPERTIES THIS MUST HAVE, and both are load-bearing.

    ORDER-INDEPENDENCE. Each cell's key depends only on the seed, the
    origin and the cell's own identity - never on the position it
    happened to occupy in the list handed in. The two radial engines
    assemble a ring differently (one walks lattice offsets in
    geometric order, the other takes whatever the neighbour search
    returned) and a plain seeded shuffle of those two lists gives two
    different answers from one seed. Keying on identity removes the
    disagreement by construction rather than by convention.

    PER-ORIGIN. The key mixes in the origin, so the draw differs from
    origin to origin. One shuffle order reused everywhere would
    favour the same direction at every origin - a spatial artefact
    worse than the overshoot it was meant to fix.

    Reproducibility is tied to the FILE, not to the geography: cells
    are identified by their position in the data as supplied, so
    re-sorting the input changes the draw. John ruled this acceptable
    and it matches ordinary practice - a bootstrap in any statistical
    package behaves the same way - but it is stated here and in the
    help rather than left to be discovered.
    """
    ids = np.asarray(cell_ids, dtype=np.uint64)
    with np.errstate(over="ignore"):
        base = _mix64(np.uint64(seed) ^ (np.uint64(origin_id) * _GOLDEN))
        key = _mix64(ids * _GOLDEN ^ base)
    return np.argsort(key, kind="stable")


#: How close two distances must be to count as the same ring. The
#: radial engines already used this; it is named here so the effort
#: engines cannot quietly pick a different one.
RING_TOL = 1e-6


def ring_bounds(dd, pos, tol=RING_TOL):
    """First and last index of the ring containing position `pos`.

    A ring is a set of cells at the SAME distance - or, in an effort
    run, at the same effort. The engines already walked FORWARD from
    the crossing cell to find the ring's end (the atomic-tie rule).
    Taking a share of that ring needs its START as well, because the
    share is measured against what the ring holds and against what
    had already accumulated before it began.
    """
    lo = hi = int(pos)
    n = len(dd)
    while hi + 1 < n and dd[hi + 1] - dd[hi] < tol:
        hi += 1
    while lo > 0 and dd[lo] - dd[lo - 1] < tol:
        lo -= 1
    return lo, hi


def ring_weights(mode, k, cumulative_before, ring_pop, ring_ids,
                 seed=None, origin_id=0):
    """How much of each cell in the crossing ring is taken.

    Returns (weights, taken) where `weights` runs parallel to
    `ring_pop` and `taken` is the number of people it accounts for.
    One contract covers all three modes, so the four engines share a
    single decision instead of three copies of it:

        whole         every weight 1.0
        proportional  every weight f, the same fraction
        sampled       weight 1.0 for the cells drawn, 0.0 for the rest

    The caller applies the weights to the ring's population AND to
    every group count, then reads the share of the ring taken from
    `taken / ring_pop.sum()` for the Dist_k interpolation. That share
    is a POPULATION share used as an AREA share, which is exact when
    density is even across the ring and an approximation otherwise -
    the same assumption selfpot.py already makes for the origin cell.

    John ruled this good enough, 1.30, with the context that makes it
    easy to accept: the FIRST versions of EquiPop simply stored the
    MAXIMUM distance from the origin. Against that, interpolating by
    area between the ring's inner and outer edge is already a
    considerable refinement. The loosest case is `sampled` on unequal
    cells, where whole cells are taken and one large cell can stand
    for a large share of the annulus.
    """
    m = resolve(mode)
    pop = np.asarray(ring_pop, dtype=float)
    total = float(pop.sum())

    if m == WHOLE or total <= 0.0:
        return np.ones(len(pop)), total

    if m == PROPORTIONAL:
        f = float(share(k, cumulative_before, total))
        return np.full(len(pop), f), f * total

    # sampled: whole cells, in an order that depends only on the
    # seed, the origin and each cell's own identity
    order = order_within_ring(ring_ids, seed, origin_id)
    run = np.cumsum(pop[order]) + float(cumulative_before)
    j = int(np.searchsorted(run, float(k)))
    j = min(j, len(order) - 1)
    w = np.zeros(len(pop))
    w[order[:j + 1]] = 1.0
    return w, float(pop[order[:j + 1]].sum())


def cell_identity(e_grid, n_grid):
    """A stable identity for a cell, from WHERE IT IS.

    The seeded order needs to name cells, and the two radial engines
    name them differently: the fast engine knows a cell by its row in
    the input, the ring engine knows it only by its grid position and
    never sees a row number at all. Keyed on either engine's private
    notion, one seed gives two answers - which is BACKLOG 99's
    unresolved `sampled` disagreement.

    Grid position is the one identity BOTH already hold, so it is used
    here. John ruled it acceptable for a re-sorted file to give a
    different draw; this is stronger than he asked for and costs
    nothing - the draw now depends on the geography, so re-exporting
    or re-sorting the same study reproduces it exactly.
    """
    e = np.asarray(e_grid, dtype=np.int64).astype(np.uint64)
    n = np.asarray(n_grid, dtype=np.int64).astype(np.uint64)
    with np.errstate(over="ignore"):
        return _mix64(e * _GOLDEN) ^ _mix64(n)


def draw_seed():
    """A seed when the user gave none. It is always PRINTED - John,
    1.30: 'print always'. An unrepeatable run is a small loss; an
    unrepeatable run the user cannot even identify afterwards is a
    larger one, and the cost is a single line of output."""
    return int(np.random.SeedSequence().generate_state(1)[0])


def seed_message(seed, given):
    """The line the doors print, so a run can always be repeated."""
    if given:
        return f"[overshoot] sampled order from seed {seed}"
    return (f"[overshoot] no seed given; drew {seed}. Enter that "
            "number to repeat this exact run.")


# --- the guard machine 2 needs --------------------------------------

def fallback_for_value_statistics(mode, wanted, chosen):
    """Value statistics cannot take a fraction of a cell - but from
    1.30 `proportional` is the DEFAULT, so refusing outright would
    break every median, percentile and Gini workflow that never asked
    for it, until BACKLOG 118 lands weighted statistics.

    The rule: an EXPLICIT request gets an explicit refusal; an
    inherited default falls back to `whole` and SAYS SO. Machine 1 and
    machine 2 then still agree whenever both can answer, and where
    they cannot the user is told rather than left to wonder.

    Returns the mode to use. `chosen` is True when the user named the
    mode themselves.
    """
    if mode != PROPORTIONAL or not wanted:
        return mode
    if chosen:
        refuse_value_statistics(mode, wanted)
    print(f"[overshoot] value statistics cannot take a fraction of a "
          f"cell ({', '.join(wanted)}), so the default "
          f"'{PROPORTIONAL}' does not apply here - using '{WHOLE}' "
          f"for this run. Counts and shares are unaffected. Name a "
          f"mode explicitly to override. See BACKLOG 118.")
    return WHOLE


def refuse_value_statistics(mode, wanted):
    """Value statistics cannot take a fraction of a cell.

    A median, a percentile or a Gini needs the PEOPLE, and a quarter
    of a boundary cell is not a quarter of a person - it is an
    estimate with no distribution behind it. Weighted statistics with
    fractional weights are BACKLOG 118, which is also the continental
    blocker. Until then this raises rather than returns a number that
    looks fine and is not.
    """
    if mode != PROPORTIONAL or not wanted:
        return
    raise ValueError(
        "[overshoot] 'proportional' takes a FRACTION of each cell in "
        "the ring that crosses k, and a fraction of a cell has no "
        f"median, percentile or Gini. Asked for: {', '.join(wanted)}. "
        f"Use '{WHOLE}' or '{SAMPLED}', which keep whole cells, or "
        "ask for counts and shares instead. Nothing was computed.")
