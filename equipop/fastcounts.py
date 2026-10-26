"""
fastcounts.py - vectorised counts-only k-NN engine (the fast path).

For the common case - aggregated counts, ratio output, no value
arrays - this engine replaces the per-origin Python loop with
KD-tree neighbour queries and cumulative sums over whole chunks of
origins at once. Same mathematics and the SAME ring-atomic tie
convention as run_knn_stats (verified by regression test); one to
two orders of magnitude faster on large datasets.

Use run_knn_stats when you need median/Gini/etc. of value variables;
use run_knn_counts for counts and ratios at scale.
"""

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from . import overshoot, selfpot, selfrule
from .cells import CellData

#: Solve whole chunks of origins at once where the settings allow
#: (v1.61.1) - see _solve_batch. False forces the per-origin path; the
#: tests run both and require the same table, bit for bit.
BATCHED = True

#: Up to this many cells a ring's sum is reproduced in numpy's order
#: across the whole chunk (rowsum_like_numpy); a longer row - rare -
#: is handed to np.sum itself, row by row.
_BATCH_RING_MAX = 128


def _ratio(num, den, guard):
    """num / den where guard > 0, else NaN - the per-origin path's
    `num / den if guard > 0 else np.nan`, a column at a time."""
    num, den, guard = (np.asarray(x, float) for x in (num, den, guard))
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(guard > 0, num / np.where(guard > 0, den, 1.0),
                        np.nan)


def rowsum_like_numpy(P, L):
    """Each row's sum of its first L[i] entries, ADDED IN THE ORDER
    np.sum adds a contiguous float64 array of that length.

    v1.61.1. The per-origin path sums a crossing ring with
    `(ring * w).sum()`. To give John the SAME numbers, not numbers
    that agree to fifteen digits, the batched path adds them in the
    same order: numpy sums fewer than 8 values left to right from 0.0,
    and 8 to 128 values in eight running sums combined as
    ((r0+r1)+(r2+r3))+((r4+r5)+(r6+r7)) with the remainder added after.
    Rows longer than 128 are summed by np.sum itself, one at a time -
    numpy's pairwise split above 128 is recursive, and such rings are
    rare. tests/test_batched_engine.py checks all of it against np.sum.
    """
    P = np.asarray(P, float)
    L = np.asarray(L)
    C, W = P.shape
    out = np.zeros(C)
    small = L < 8
    if small.any():
        acc = np.zeros(int(small.sum()))
        Ps, Ls = P[small], L[small]
        for t in range(min(8, W)):
            acc = acc + np.where(t < Ls, Ps[:, t], 0.0)
        out[small] = acc
    mid = (L >= 8) & (L <= _BATCH_RING_MAX)
    if mid.any():
        Pm, Lm = P[mid], L[mid]
        nb = Lm // 8
        r = Pm[:, 0:8].copy()
        for b in range(1, int(nb.max())):
            use = (b < nb)[:, None]
            r = np.where(use, r + Pm[:, 8 * b:8 * b + 8], r)
        res = ((r[:, 0] + r[:, 1]) + (r[:, 2] + r[:, 3])) + \
              ((r[:, 4] + r[:, 5]) + (r[:, 6] + r[:, 7]))
        start = nb * 8
        rows = np.arange(len(Pm))
        for t in range(7):
            i = start + t
            ok = i < Lm
            res = np.where(ok, res + Pm[rows, np.minimum(i, W - 1)], res)
        out[mid] = res
    for i in np.flatnonzero(L > _BATCH_RING_MAX):   # rare: numpy itself
        out[i] = P[i, :int(L[i])].sum()
    return out


def _lab(x) -> str:
    """Compact numeric label: 500 -> '500', 2.5 -> '2_5'.

    BACKLOG 337: `f"{x:g}"` until 1.51.0, which carried six
    significant digits and switched to scientific notation - so
    r(1000000) became the illegal 'r1e+06' and two radii agreeing to
    six digits silently became ONE column. equipop/labels.py holds the
    one formatter now; the dot is already an underscore when it
    arrives here.
    """
    from .labels import numeric_tag
    return numeric_tag(x)


def run_knn_counts(cd: CellData, k_values: list[int] | None = None,
                   m_neighbors: int | None = None,
                   chunk: int = 4096,
                   r_values: list[float] | None = None,
                   decay=None, decay_eps: float = 1e-6,
                   origins=None,
                   self_potential: float = selfpot.DEFAULT_SELF_POTENTIAL,
                   report: bool = True,
                   report_label: str = "",
                   overshoot_mode: str | None = None,
                   self_rule: str | None = None,
                   seed: int | None = None) -> pd.DataFrame:
    """
    k-NN counts/ratios for every cell in cd, vectorised.

    origins : optional array of CELL indices - compute results only
        for these origins; the tree and destination mass stay GLOBAL,
        so per-origin results are exactly those of a full run (the
        tile-and-flush substrate, #18).
    self_potential : how far away your OWN cell's people are, 0 to 1
        (v1.29.5, BACKLOG 95). 0 reproduces every release up to
        1.29.3, where a cell that already held k people reported
        Dist_k = 0 and k stopped being a parameter. 1 (the default)
        uses the equal-area radius. See equipop/selfpot.py.
    self_rule : whether the origin cell is its own neighbour
        (1.47, BACKLOG 290). "include" (the default, and what every
        published EquiPop result used) or "exclude" for the w_ii = 0
        convention that spatial regression requires. Under "exclude"
        the origin cell contributes no people, self_potential has
        nothing to act on, and an origin with no populated neighbour
        within reach reports N_k = 0 with undefined shares rather
        than an invented number. N_local and <var>_local describe THE
        CELL and are unchanged either way. See equipop/selfrule.py.
    m_neighbors : how many nearest CELLS are fetched per origin in the
        fast pass. Origins whose cumulative population within
        m_neighbors cells does not reach max(k) are automatically
        re-run against all cells (exact, slower) - the parameter
        affects speed only, never results.

    Output columns: CellId, EastWest, NorthSouth, N_local,
    <var>_local, and per k: N_k, T_<var>_k, R_<var>_k, Dist_k,
    plus SumN and MaxDistance.
    """
    k_values = sorted(k_values or [])
    r_values = sorted(r_values or [])
    sp = selfpot.check(self_potential)
    # BACKLOG 99: what happens to the ring that crosses k.
    osm = overshoot.resolve(overshoot_mode)
    # BACKLOG 290: is the origin its own neighbour? Resolved BEFORE
    # anything is computed, so a bad name costs nothing.
    srule = selfrule.resolve(self_rule)
    drop_self = srule == selfrule.EXCLUDE
    if report:
        print(selfrule.message(srule, self_potential if drop_self else None))
    seed_given = seed is not None
    os_seed = int(seed) if seed_given else overshoot.draw_seed()
    if osm == overshoot.SAMPLED and report:
        print(overshoot.seed_message(os_seed, seed_given))
    # BACKLOG 95 / 94: counted, not assumed. A run must be able to say
    # how much of its Dist_k was estimated inside one cell, and how far
    # N_k overshot the k that was asked for.
    tally = {"selfpot": {k: 0 for k in k_values},
             "over": {k: 0 for k in k_values}, "origins": 0}
    kmax = k_values[-1] if k_values else 0
    rmax = r_values[-1] if r_values else 0.0
    trunc = decay.truncation_radius(decay_eps) if decay is not None else 0.0
    if not (k_values or r_values):
        raise ValueError(
            "give k_values and/or r_values"
            + (". A decay on its own no longer produces anything: "
               "since BACKLOG 185 the decayed totals are reported AT "
               "each k or radius, on the raw threshold, so there has "
               "to be one" if decay is not None else ""))
    bad = [k for k in k_values if k <= 0]
    if bad:
        raise ValueError(
            f"[k] k must be a POSITIVE number of people; got {bad}. "
            "k=0 asks for nobody, and every mode then answers "
            "differently about a neighbourhood that does not exist - "
            "the whole-ring rule returns the origin cell, a "
            "proportional share returns zero people and an undefined "
            "R. Found by John's hand check, 1.30. Nothing was "
            "computed.")
    n_cells = len(cd)
    if m_neighbors is None:            # auto-tuned (v1.16.3/.6)
        from .cells import auto_m_neighbors
        m_neighbors = auto_m_neighbors(cd, k_values, r_values,
                                       trunc_m=trunc)
    m = min(m_neighbors, n_cells)
    pts = np.c_[cd.E.astype(float), cd.N.astype(float)]
    tree = cKDTree(pts)
    bvars = list(cd.binary_sums)
    pop = cd.n.astype(float)
    grp = {v: cd.binary_sums[v].astype(float) for v in bvars}
    # BACKLOG 168. A parallel population per variable: the people
    # whose value for it is usable. Identical to `pop` unless missing
    # codes were declared, so this changes nothing for anyone who
    # does not use them.
    okp = {v: np.asarray(cd.valid_for(v), dtype=float) for v in bvars}

    modes = []
    if k_values: modes.append(f"k = {k_values}")
    if r_values: modes.append(f"r = {r_values} m")
    if decay is not None:
        modes.append("decayed sums at each k, on the raw k threshold")
    print(f"[fast] {n_cells} cells, {' | '.join(modes)}, "
          f"fast pass with m = {m} neighbour cells")
    rows_by_oi: dict = {}
    stragglers = 0

    def _solve(dist, idx, oi_range):
        """Fill in every origin this neighbourhood can settle; hand
        back the ones that need a WIDER search (v1.16.4 ladder - see
        the loop below)."""
        unsat = []
        # dist, idx: (C, m) sorted by distance (self included at 0)
        #
        # BACKLOG 290. Under i!=j the ORIGIN CELL CONTRIBUTES NOTHING.
        # Masked here, once, so every downstream step - the cumulative
        # sums, the ring bounds, the decay weights, the overshoot
        # share - sees a neighbourhood the origin is simply not in.
        # Nothing below this point needs to know about the rule.
        #
        # MATCHED ON THE INDEX, NOT ON POSITION 0. cKDTree returns the
        # origin at distance 0 so position 0 is almost always self -
        # but two cells may share coordinates, and then "almost
        # always" silently drops somebody else's people instead.
        keep = (idx != np.asarray(oi_range)[:, None]) if drop_self else None

        def _mass(a):
            """The per-neighbour mass this rule allows to be counted."""
            m = a[idx]
            return m if keep is None else np.where(keep, m, 0.0)

        cpop = np.cumsum(_mass(pop), axis=1)
        cgrp = {v: np.cumsum(_mass(grp[v]), axis=1) for v in bvars}
        cok = {v: np.cumsum(_mass(okp[v]), axis=1) for v in bvars}

        # BACKLOG 185. Decay does NOT choose the neighbourhood - the
        # RAW count does. John's rule, and the original EquiPop's:
        # "if k=300 is requested, the 300 nearest population is the
        # right call - the decayed populations should be reported and
        # are always ... smaller than k".
        #
        # So the decayed totals are cumulated exactly like the raw
        # ones and read at the SAME position. Nothing about which
        # cells are in the neighbourhood, or how far away its edge is,
        # depends on the decay.
        cpopd = cgrpd = cokd = None
        if decay is not None:
            dwm = dist.astype(float, copy=True)
            if sp > 0.0:
                # Your own cell's people are not standing on you.
                # Without this they keep weight 1.0 - the largest in
                # the calculation - on the mass we know least about
                # (BACKLOG 95). Same adjustment the old unbounded sum
                # made, kept because the reason has not changed.
                own = dwm[:, 0] <= 0.0
                dwm[own, 0] = selfpot.decay_distance(
                    cd.unit_size, sp, shape=cd.cell_shape)
            wdec = decay.weight_vec(dwm.ravel()).reshape(dwm.shape)
            # Masked mass, not raw mass (BACKLOG 290): a decayed run
            # under i!=j must not weight people the rule removed.
            cpopd = np.cumsum(_mass(pop) * wdec, axis=1)
            cgrpd = {v: np.cumsum(_mass(grp[v]) * wdec, axis=1)
                     for v in bvars}
            cokd = {v: np.cumsum(_mass(okp[v]) * wdec, axis=1)
                    for v in bvars}
        for r, oi in enumerate(oi_range):
            covered = dist[r, -1]
            # BACKLOG 185: `covered < trunc` used to be part of this
            # test, because the unbounded sum genuinely needed every
            # cell out to the truncation radius. Nothing reads past k
            # any more, so requiring it only forced a decay run to
            # scan the whole map - 283 neighbour cells where 64 would
            # do, on the measurement that found this.
            # BACKLOG 430 (external review of 1.61.3). `covered <= rmax`,
            # NOT `<`. A radius takes every cell at distance <= r, and the
            # cells not fetched are at distance >= covered - so when the
            # window ENDS ON the radius, the rest of that ring may lie
            # outside it. Six cells in a cross gave N_r100 = 3 with a
            # three-cell window and 5 exhaustively. The same rule as the
            # k ring cut below: a window that may have sliced the
            # boundary is widened, never trusted.
            if ((cpop[r, -1] < kmax or (r_values and covered <= rmax))
                    and dist.shape[1] < n_cells):
                unsat.append(oi)
                continue

            # BACKLOG 207. A RING CUT BY THE WINDOW EDGE IS NOT A RING.
            # The test above defers an origin that failed to REACH k.
            # It does not notice one that reached k through a crossing
            # ring the window sliced in half - and ring_bounds() cannot
            # notice either, because it walks `while hi + 1 < n` where
            # n is the WINDOW, not the ring. The ring is then treated
            # as complete, its share is measured against the part that
            # happened to fit, and the radius and every group share
            # come out wrong while N_k stays exactly k - so no guard
            # fires and nothing looks amiss.
            #
            # Measured before this was written: on a lattice of one
            # person per cell, a four-cell ring seen two cells wide put
            # Dist_11 at 200.0 m against a true 173.2; on Burundi +
            # Rwanda at 1 km, 249 of 46,317 origins moved by up to
            # 168.8 m, and a cross-border share read 0.043 where it
            # should read 0.065.
            #
            # So: if the ring that crosses ANY requested k reaches the
            # last fetched cell, the ring may continue past it. Hand
            # the origin to the ladder, which already exists for the
            # other reason. Cost is a wider retry for those origins;
            # John's ruling for the continental run was correctness
            # over speed.
            if dist.shape[1] < n_cells:
                edge = dist.shape[1] - 1
                cut = False
                for k in k_values:
                    pos_k = int(np.searchsorted(cpop[r], k))
                    if pos_k >= dist.shape[1]:
                        continue                  # partial: handled above
                    _, hi_k = overshoot.ring_bounds(dist[r], pos_k)
                    if hi_k >= edge:
                        cut = True
                        break
                if cut:
                    tally["ring_cut"] = tally.get("ring_cut", 0) + 1
                    unsat.append(oi)
                    continue
            rec = {"CellId": cd.labels[oi] if cd.labels else oi,
                   "EastWest": round(float(cd.E[oi]), 2),
                   "NorthSouth": round(float(cd.N[oi]), 2),
                   "N_local": float(pop[oi])}
            for v in bvars:
                rec[f"{v}_local"] = float(grp[v][oi])
            dd, cp = dist[r], cpop[r]
            last = 0
            tally["origins"] += 1
            for k in k_values:
                pos = int(np.searchsorted(cp, k))
                partial = pos >= len(cp)
                if partial:
                    pos = len(cp) - 1          # unreached: partial
                    lo = hi = pos
                else:                          # ring-atomic extension
                    lo, hi = overshoot.ring_bounds(dd, pos)
                    pos = hi
                nd_k = None
                if partial or osm == overshoot.WHOLE:
                    n_k = cp[pos]
                    grp_k = {v: cgrp[v][r][pos] for v in bvars}
                    den_k = {v: float(cok[v][r][pos]) for v in bvars}
                    d_k = float(dd[pos])
                    if decay is not None:
                        nd_k = float(cpopd[r][pos])
                        grpd_k = {v: float(cgrpd[v][r][pos])
                                  for v in bvars}
                        dend_k = {v: float(cokd[v][r][pos])
                                  for v in bvars}
                else:
                    # BACKLOG 99: take only part of the crossing ring.
                    # `lo` is what the atomic-tie rule never needed and
                    # a share cannot do without.
                    before = float(cp[lo - 1]) if lo > 0 else 0.0
                    cells_i = idx[r, lo:hi + 1]
                    # BACKLOG 290: the crossing ring can contain the
                    # origin, and a share of the origin is still the
                    # origin. Masked with the same rule as the sums
                    # above, or the ring path would quietly reinstate
                    # what i!=j removed.
                    ring_keep = (keep[r, lo:hi + 1] if keep is not None
                                 else None)

                    def _ring(a):
                        m = a[cells_i]
                        return (m if ring_keep is None
                                else np.where(ring_keep, m, 0.0))

                    rpop = _ring(pop)
                    ids = overshoot.cell_identity(
                        np.round(cd.E[cells_i] / cd.unit_size),
                        np.round(cd.N[cells_i] / cd.unit_size))
                    w, taken = overshoot.ring_weights(
                        osm, k, before, rpop, ids,
                        seed=os_seed,
                        origin_id=int(overshoot.cell_identity(
                            round(cd.E[oi] / cd.unit_size),
                            round(cd.N[oi] / cd.unit_size))))
                    n_k = before + taken
                    grp_k, den_k = {}, {}
                    for v in bvars:
                        t_before = (float(cgrp[v][r][lo - 1])
                                    if lo > 0 else 0.0)
                        grp_k[v] = t_before + float(
                            (_ring(grp[v]) * w).sum())
                        o_before = (float(cok[v][r][lo - 1])
                                    if lo > 0 else 0.0)
                        den_k[v] = o_before + float(
                            (_ring(okp[v]) * w).sum())
                    if decay is not None:
                        wd_ring = wdec[r, lo:hi + 1]
                        nd_before = (float(cpopd[r][lo - 1])
                                     if lo > 0 else 0.0)
                        nd_k = nd_before + float(
                            (rpop * wd_ring * w).sum())
                        grpd_k, dend_k = {}, {}
                        for v in bvars:
                            tb = (float(cgrpd[v][r][lo - 1])
                                  if lo > 0 else 0.0)
                            grpd_k[v] = tb + float(
                                (_ring(grp[v]) * wd_ring * w).sum())
                            ob = (float(cokd[v][r][lo - 1])
                                  if lo > 0 else 0.0)
                            dend_k[v] = ob + float(
                                (_ring(okp[v]) * wd_ring * w).sum())
                    ring_all = float(rpop.sum())
                    f = taken / ring_all if ring_all > 0 else 1.0
                    d_prev = float(dd[lo - 1]) if lo > 0 else 0.0
                    if lo > 0 and d_prev <= 0.0 and sp > 0.0:
                        # BACKLOG 191. Everything counted so far is the
                        # origin's OWN cell, and its people are not
                        # standing at distance zero - they are spread
                        # through the cell, reached by the equal-area
                        # radius s*unit/sqrt(pi). Starting the
                        # interpolation from 0 instead made Dist_k fall
                        # as k ROSE: on John's field data, Dist_50 came
                        # back as 51.1 m and Dist_100 as 35.8 m for the
                        # same origin, because the second one was
                        # measured 36% of the way out from the cell
                        # CENTRE while the first was a real radius
                        # inside the cell.
                        #
                        # This is the value the in-cell formula reaches
                        # at k = n, so the two conventions now meet
                        # continuously at the cell boundary instead of
                        # stepping back to zero.
                        d_prev = min(
                            selfpot.radius_for_k(cd.unit_size, 1.0, 1.0, sp,
                                                 shape=cd.cell_shape),
                            float(dd[hi]))
                    d_k = float(overshoot.radius(d_prev, float(dd[hi]), f))
                rec[f"N_{k}"] = n_k
                for v in bvars:
                    rec[f"T_{v}_{k}"] = grp_k[v]
                    rec[f"R_{v}_{k}"] = (grp_k[v] / den_k[v]
                                         if den_k[v] > 0 else np.nan)
                if nd_k is not None:
                    rec[f"ND_{k}"] = nd_k
                    for v in bvars:
                        rec[f"TD_{v}_{k}"] = grpd_k[v]
                        rec[f"RD_{v}_{k}"] = (grpd_k[v] / dend_k[v]
                                              if dend_k[v] > 0
                                              else np.nan)
# BACKLOG 304. `>= k` IS A FLOATING-POINT TRAP HERE.
                # Under `proportional` the crossing cell contributes a
                # FRACTION, and the sum comes back 99.99999999999999
                # for k=100 - so the guard was False, the
                # self-potential never fired, and Dist_k stayed 0.
                # That is BACKLOG 191's defect returning through a
                # different door: a distance of zero, which makes k
                # stop distinguishing origins.
                # Found on John's LA County teaching data: 1,213 of
                # 75,109 blocks, all of them dense enough that the
                # whole neighbourhood sits inside one cell. No test
                # fixture was dense enough to produce the rounding.
                if d_k <= 0.0 and n_k >= k - 1e-9:
                    # BACKLOG 290. Under i!=j this CANNOT be the origin
                    # cell - its mass was removed. A zero radius here
                    # means a DIFFERENT cell sharing the origin's
                    # coordinates, which is a real and separate thing.
                    # The arithmetic is the same either way: mass at
                    # distance zero needs the equal-area radius or
                    # Dist_k comes back 0 and k stops distinguishing
                    # origins (BACKLOG 191). What must NOT be the same
                    # is the report, which would otherwise announce
                    # "the whole neighbourhood was the origin cell"
                    # about a rule that excluded it.
                    #
                    # the whole neighbourhood IS the origin cell, so
                    # the radius is not zero - it is unmeasured, and
                    # k has stopped being a parameter (BACKLOG 95).
                    # The equal-area radius needs the people actually
                    # STANDING in the cell, not the share reported:
                    # under `proportional` n_k is k exactly, and
                    # passing it turned the radius into a constant.
                    # Invisible under `whole`, where the two are equal.
                    d_k = selfpot.radius_for_k(cd.unit_size, k,
                                               float(cp[pos]), sp,
                                               shape=cd.cell_shape)
                    if drop_self:
                        tally.setdefault("colocated", {})
                        tally["colocated"][k] = (
                            tally["colocated"].get(k, 0) + 1)
                    else:
                        tally["selfpot"][k] += 1
                if n_k >= 2 * k:               # BACKLOG 94
                    tally["over"][k] += 1
                rec[f"Dist_{k}"] = d_k
                last = pos
            for rv in r_values:            # radius: all cells within rv,
                pos = int(np.searchsorted(dd, rv, side="right")) - 1
                lab = _lab(rv)             # included wholly (no ties by
                rec[f"N_r{lab}"] = cp[pos]  # construction)
                for v in bvars:
                    rec[f"T_{v}_r{lab}"] = cgrp[v][r][pos]
                    # Guarded on the share's OWN denominator (BACKLOG
                    # 431): people present but none with a usable value
                    # is 0/0 - NaN either way, but tested on cp it was
                    # computed, and warned about, 37 times a suite run.
                    rec[f"R_{v}_r{lab}"] = (cgrp[v][r][pos]
                                            / cok[v][r][pos]
                                            if cok[v][r][pos] > 0
                                            else np.nan)
                if decay is not None:
                    rec[f"ND_r{lab}"] = float(cpopd[r][pos])
                    for v in bvars:
                        td = float(cgrpd[v][r][pos])
                        od = float(cokd[v][r][pos])
                        rec[f"TD_{v}_r{lab}"] = td
                        rec[f"RD_{v}_r{lab}"] = (td / od if od > 0
                                                 else np.nan)
                last = max(last, pos)
            # BACKLOG 185: the UNBOUNDED decayed sum (ND_inf,
            # TD_<v>_inf, RD_<v>_inf) was removed here in v1.40. It
            # accumulated out to the truncation radius instead of to
            # k, so it answered a different question - a decayed
            # potential over everybody rather than the decayed content
            # of the k-neighbourhood. John: "it doesn't solve any
            # problem I know of - and it risks becoming an orphan or
            # picked up in a later session with unknown consequences."
            # Deleted rather than commented out: dead code rots, and
            # git remembers it. The decayed totals are now recorded in
            # the k and radius branches above, at the raw threshold.
            rec["SumN"] = cp[last]
            rec["MaxDistance"] = float(dd[last])
            rows_by_oi[oi] = rec
        return unsat

    # ---------------------------------------- v1.61.1 BATCHED SOLVING
    # John, 19 October, Turkey at 700 m with k = 5,000 and 9,000: the
    # search above is vectorised, but _solve then walked every origin
    # in Python - about 0.4 ms each, so 661,567 cells took minutes and
    # said nothing. _solve_batch does the SAME arithmetic for a whole
    # chunk at once: the positions, the ring bounds, the share of the
    # crossing ring, the radius and every group total, with the ring
    # sums added in numpy's own order (rowsum_like_numpy) so the table
    # is identical, not merely close. It covers the settings machines
    # 1, 3 and 4 run with - k values, whole or proportional overshoot,
    # either self rule, no decay, no radii. Anything else, and any
    # origin whose crossing ring is longer than 128 cells, still goes
    # through _solve.
    # v1.61.2, John: "Please add the speed up for the other run types
    # as well" - decay, radii, `sampled` and the longest rings are
    # batched too, so every setting this engine has takes this path.
    batched = BATCHED
    batch_parts = []
    rk1 = selfpot.radius_for_k(cd.unit_size, 1.0, 1.0, sp,
                               shape=cd.cell_shape)

    def _solve_batch(dist, idx, oi_range):
        oi_range = np.asarray(oi_range)
        C, M = dist.shape
        keep = (idx != oi_range[:, None]) if drop_self else None

        def _mass(a):
            mm = a[idx]
            return mm if keep is None else np.where(keep, mm, 0.0)

        cpop = np.cumsum(_mass(pop), axis=1)
        cgrp = {v: np.cumsum(_mass(grp[v]), axis=1) for v in bvars}
        cok = {v: np.cumsum(_mass(okp[v]), axis=1) for v in bvars}
        wdec = cpopd = cgrpd = cokd = None
        if decay is not None:
            dwm = dist.astype(float, copy=True)
            if sp > 0.0:
                own = dwm[:, 0] <= 0.0
                dwm[own, 0] = selfpot.decay_distance(
                    cd.unit_size, sp, shape=cd.cell_shape)
            wdec = decay.weight_vec(dwm.ravel()).reshape(dwm.shape)
            cpopd = np.cumsum(_mass(pop) * wdec, axis=1)
            cgrpd = {v: np.cumsum(_mass(grp[v]) * wdec, axis=1)
                     for v in bvars}
            cokd = {v: np.cumsum(_mass(okp[v]) * wdec, axis=1)
                    for v in bvars}
        jj = np.arange(M)
        if M > 1:
            same = (dist[:, 1:] - dist[:, :-1]) < overshoot.RING_TOL
        else:
            same = np.zeros((C, 0), bool)
        end = np.ones((C, M), bool)
        end[:, :-1] = ~same
        begin = np.ones((C, M), bool)
        begin[:, 1:] = ~same
        ring_last = np.minimum.accumulate(
            np.where(end, jj, M)[:, ::-1], axis=1)[:, ::-1]
        ring_first = np.maximum.accumulate(np.where(begin, jj, -1),
                                           axis=1)
        pos_k = {k: (cpop < k).sum(axis=1) for k in k_values}
        window = M < n_cells
        unsat = np.zeros(C, bool)
        if window:
            unsat |= cpop[:, -1] < kmax
            if r_values:                 # <=, not <: BACKLOG 430, as _solve
                unsat |= dist[:, -1] <= rmax
            cut = np.zeros(C, bool)
            for k in k_values:
                p = pos_k[k]
                ok = p < M
                hi_k = ring_last[np.arange(C), np.minimum(p, M - 1)]
                cut |= ok & (hi_k >= M - 1)
            cut &= ~unsat
            if cut.any():
                tally["ring_cut"] = tally.get("ring_cut", 0) + int(cut.sum())
            unsat |= cut
        handed_back = list(oi_range[unsat])
        S = np.flatnonzero(~unsat)
        if not len(S):
            return handed_back
        oi_s = oi_range[S]
        cols = {"CellId": ([cd.labels[o] for o in oi_s] if cd.labels
                           else oi_s.copy()),
                "EastWest": np.array([round(float(e), 2)
                                      for e in cd.E[oi_s]]),
                "NorthSouth": np.array([round(float(n_), 2)
                                        for n_ in cd.N[oi_s]]),
                "N_local": pop[oi_s].astype(float)}
        for v in bvars:
            cols[f"{v}_local"] = grp[v][oi_s].astype(float)
        # every origin settled (the usual case): the chunk's own arrays,
        # not copies of them
        if len(S) == C:
            def sub_(a):
                return a
        else:
            def sub_(a):
                return a[S]
        dd, cp = sub_(dist), sub_(cpop)
        cgS = {v: sub_(cgrp[v]) for v in bvars}
        coS = {v: sub_(cok[v]) for v in bvars}
        idxS = sub_(idx)
        keepS = sub_(keep) if keep is not None else None
        if decay is not None:
            wdS, cpdS = sub_(wdec), sub_(cpopd)
            cgdS = {v: sub_(cgrpd[v]) for v in bvars}
            codS = {v: sub_(cokd[v]) for v in bvars}
        ns = len(S)
        rows = np.arange(ns)
        last = np.zeros(ns, dtype=np.int64)
        tally["origins"] += ns

        def at(mat, where_):
            return mat[rows, where_].copy()

        def before_of(mat, rr, lo_r):
            return np.where(lo_r > 0, mat[rr, np.maximum(lo_r - 1, 0)], 0.0)

        for k in k_values:
            p = pos_k[k][S]
            partial = p >= M
            pc = np.where(partial, M - 1, p)
            lo = np.where(partial, pc, ring_first[S, pc])
            hi = np.where(partial, pc, ring_last[S, pc])
            pos = hi
            whole = partial | (osm == overshoot.WHOLE)
            n_k = at(cp, pos)
            grp_k = {v: at(cgS[v], pos) for v in bvars}
            den_k = {v: at(coS[v], pos) for v in bvars}
            d_k = at(dd, pos)
            if decay is not None:
                nd_k = at(cpdS, pos)
                grpd_k = {v: at(cgdS[v], pos) for v in bvars}
                dend_k = {v: at(codS[v], pos) for v in bvars}
            ring = ~whole
            if ring.any():
                rr = np.flatnonzero(ring)
                lo_r, hi_r = lo[rr], hi[rr]
                L = hi_r - lo_r + 1
                width = int(L.max())
                before = before_of(cp, rr, lo_r)
                col = np.minimum(lo_r[:, None] + np.arange(width), M - 1)
                inside = np.arange(width)[None, :] < L[:, None]
                cells = idxS[rr[:, None], col]
                kept = inside if keepS is None else (
                    inside & keepS[rr[:, None], col])

                def ring_of(a):
                    return np.where(kept, a[cells], 0.0)
                rpop = ring_of(pop)
                total = rowsum_like_numpy(rpop, L)
                pos_t = total > 0.0
                if osm == overshoot.SAMPLED:
                    # the seeded order within each ring, keyed on the
                    # cells' identities and the origin's, exactly as
                    # overshoot.ring_weights draws it
                    oi_r = oi_s[rr]
                    ids = overshoot.cell_identity(
                        np.round(cd.E[cells] / cd.unit_size),
                        np.round(cd.N[cells] / cd.unit_size))
                    org = overshoot.cell_identity(
                        np.round(cd.E[oi_r] / cd.unit_size),
                        np.round(cd.N[oi_r] / cd.unit_size))
                    with np.errstate(over="ignore"):
                        base = overshoot._mix64(
                            np.uint64(os_seed) ^ (org * overshoot._GOLDEN))
                        key = overshoot._mix64(
                            ids * overshoot._GOLDEN ^ base[:, None])
                    key = np.where(inside, key,
                                   np.iinfo(np.uint64).max)
                    order = np.argsort(key, axis=1, kind="stable")
                    sorted_pop = np.take_along_axis(rpop, order, axis=1)
                    run = np.cumsum(sorted_pop, axis=1) + before[:, None]
                    # (run < k) counts the entries short of k -
                    # searchsorted's 'left' on a non-decreasing run -
                    # and the masked tail beyond L must not count
                    j = np.minimum(
                        np.where(inside, run < k, False).sum(axis=1), L - 1)
                    taken_s = rowsum_like_numpy(sorted_pop, j + 1)
                    sel = np.zeros_like(inside)
                    np.put_along_axis(
                        sel, order,
                        np.arange(width)[None, :] <= j[:, None], axis=1)
                    w = np.where(pos_t[:, None], sel.astype(float), 1.0)
                    taken = np.where(pos_t, taken_s, total)
                else:
                    f0 = overshoot.share(k, before, total)
                    w = np.where(pos_t, f0, 1.0)[:, None] * np.ones(
                        (1, width))
                    taken = np.where(pos_t, f0 * total, total)
                n_k[rr] = before + taken
                for v in bvars:
                    grp_k[v][rr] = before_of(cgS[v], rr, lo_r) + \
                        rowsum_like_numpy(ring_of(grp[v]) * w, L)
                    den_k[v][rr] = before_of(coS[v], rr, lo_r) + \
                        rowsum_like_numpy(ring_of(okp[v]) * w, L)
                if decay is not None:
                    wd = np.where(inside, wdS[rr[:, None], col], 0.0)
                    nd_k[rr] = before_of(cpdS, rr, lo_r) + \
                        rowsum_like_numpy(rpop * wd * w, L)
                    for v in bvars:
                        grpd_k[v][rr] = before_of(cgdS[v], rr, lo_r) + \
                            rowsum_like_numpy(ring_of(grp[v]) * wd * w, L)
                        dend_k[v][rr] = before_of(codS[v], rr, lo_r) + \
                            rowsum_like_numpy(ring_of(okp[v]) * wd * w, L)
                with np.errstate(divide="ignore", invalid="ignore"):
                    f = np.where(pos_t, taken / np.where(pos_t, total, 1.0),
                                 1.0)
                d_prev = np.where(lo_r > 0,
                                  dd[rr, np.maximum(lo_r - 1, 0)], 0.0)
                fix = (lo_r > 0) & (d_prev <= 0.0) & (sp > 0.0)
                d_prev = np.where(fix, np.minimum(rk1, dd[rr, hi_r]),
                                  d_prev)
                d_k[rr] = overshoot.radius(d_prev, dd[rr, hi_r], f)
            fire = np.flatnonzero((d_k <= 0.0) & (n_k >= k - 1e-9))
            for i in fire:
                d_k[i] = selfpot.radius_for_k(cd.unit_size, k,
                                              float(cp[i, pos[i]]), sp,
                                              shape=cd.cell_shape)
            if len(fire):
                if drop_self:
                    tally.setdefault("colocated", {})
                    tally["colocated"][k] = (
                        tally["colocated"].get(k, 0) + len(fire))
                else:
                    tally["selfpot"][k] += len(fire)
            tally["over"][k] += int((n_k >= 2 * k).sum())
            cols[f"N_{k}"] = n_k
            for v in bvars:
                cols[f"T_{v}_{k}"] = grp_k[v]
                cols[f"R_{v}_{k}"] = _ratio(grp_k[v], den_k[v], den_k[v])
            if decay is not None:
                cols[f"ND_{k}"] = nd_k
                for v in bvars:
                    cols[f"TD_{v}_{k}"] = grpd_k[v]
                    cols[f"RD_{v}_{k}"] = _ratio(grpd_k[v], dend_k[v],
                                                 dend_k[v])
            cols[f"Dist_{k}"] = d_k
            last = pos
        for rv in r_values:
            pos = (dd <= rv).sum(axis=1) - 1
            lab = _lab(rv)
            npos = at(cp, pos)
            cols[f"N_r{lab}"] = npos
            for v in bvars:
                t = at(cgS[v], pos)
                cols[f"T_{v}_r{lab}"] = t
                den = at(coS[v], pos)          # BACKLOG 431, as _solve
                cols[f"R_{v}_r{lab}"] = _ratio(t, den, den)
            if decay is not None:
                cols[f"ND_r{lab}"] = at(cpdS, pos)
                for v in bvars:
                    td, od = at(cgdS[v], pos), at(codS[v], pos)
                    cols[f"TD_{v}_r{lab}"] = td
                    cols[f"RD_{v}_r{lab}"] = _ratio(td, od, od)
            last = np.maximum(last, pos)
        cols["SumN"] = at(cp, last)
        cols["MaxDistance"] = at(dd, last).astype(float)
        batch_parts.append(pd.DataFrame(cols, index=oi_s))
        return handed_back

    origins = np.arange(n_cells) if origins is None \
        else np.asarray(origins)
    # --------------------------------------------- v1.16.4 the LADDER
    # Thin-population origins cannot reach k inside the neighbourhood
    # the density suggested. Until now each one was re-solved against
    # ALL cells - and in a country with both cities and wilderness
    # that single cliff dominated the run (a field run: 64,966 such
    # origins, 1 h 46 min of the 1 h 51 min total). Now the search
    # widens x8 at a time for exactly those origins, which is a few
    # thousand cells rather than half a million, and only the last
    # step - if it is ever reached - is the full set. Results are
    # unchanged either way: the walk still ends inside a complete
    # neighbourhood.
    todo = origins
    m_now = m
    solve = _solve_batch if batched else _solve
    import time as _time
    while len(todo):
        nxt = []
        c_now = max(1, min(chunk, int(4e6 // max(m_now, 1))))
        # PROGRESS (v1.61.1, John: "a progress line would make wonder").
        # A long pass said nothing between its first line and its last,
        # which looks the same as a hung one. One line per tenth of the
        # origins, only when the pass is big enough to wait for.
        said, t_pass = 0, _time.time()
        loud = report and len(todo) >= 20000
        for start in range(0, len(todo), c_now):
            sel = todo[start:min(start + c_now, len(todo))]
            dist, idx = tree.query(pts[sel], k=m_now, workers=-1)
            if m_now == 1:
                dist, idx = dist[:, None], idx[:, None]
            nxt.extend(solve(dist, idx, sel))
            done = min(start + c_now, len(todo))
            tenth = done * 10 // len(todo)
            if loud and tenth > said and done < len(todo):
                said = tenth
                el = _time.time() - t_pass
                print(f"[fast] {done:,} of {len(todo):,} origins "
                      f"({100 * done // len(todo)}%) in {el:,.0f} s - "
                      f"about {el * (len(todo) - done) / done:,.0f} s "
                      "to go in this pass", flush=True)
        if not nxt or m_now >= n_cells:
            break
        stragglers += len(nxt)
        m_now = int(min(n_cells, max(m_now * 8, 64)))
        print(f"[fast] {len(nxt)} sparse origins need a wider search "
              f"- retrying those with m = {m_now}"
              + (" (all cells)" if m_now >= n_cells else ""))
        todo = np.asarray(nxt)
    if stragglers:
        print(f"[fast] {stragglers} widened searches in total "
              "(results identical, only the route differs)")
    if report:                 # the binned decay pass runs this
        report_selfpot(tally, k_values, sp,   # once per BIN, which is
                       report_label)
    if not batch_parts:
        return pd.DataFrame([rows_by_oi[o] for o in origins])  # only noise
    out = pd.concat(batch_parts)
    if rows_by_oi:
        old = pd.DataFrame.from_dict(rows_by_oi, orient="index")
        out = pd.concat([out, old[out.columns]])
    out = out.loc[origins].reset_index(drop=True)
    if not cd.labels:
        out["CellId"] = out["CellId"].astype(np.int64)
    return out


def report_selfpot(tally: dict, k_values, sp: float,
                   label: str = "") -> None:
    """Say out loud how much of the answer came from inside one cell
    (BACKLOG 95) and how far N_k overshot k (BACKLOG 94). Shared with
    the slow engine so the two cannot describe themselves differently.
    """
    tot = tally.get("origins", 0)
    if not tot:
        return
    for k in k_values:
        nsp = tally["selfpot"].get(k, 0)
        if nsp:
            how = (f"Dist_{k} ESTIMATED inside the cell "
                   f"(self-potential {sp:g})" if sp > 0 else
                   f"Dist_{k} reported as 0 - self-potential is OFF, "
                   f"so k is not distinguishing these origins")
            print(f"[selfpot]{label} k={k}: the whole neighbourhood "
                  f"was the origin cell for {nsp:,} of {tot:,} origins "
                  f"- {how}")
        # BACKLOG 290: same arithmetic, different fact. Under i!=j the
        # origin's own people were removed, so mass at distance zero
        # is a DIFFERENT cell standing on the same coordinates. Saying
        # "the whole neighbourhood was the origin cell" there would be
        # false, and it is exactly the kind of false that survives
        # because it sounds familiar.
        ncl = tally.get("colocated", {}).get(k, 0)
        if ncl:
            print(f"[selfpot]{label} k={k}: {ncl:,} of {tot:,} origins "
                  f"reached k entirely from cells sharing their own "
                  f"coordinates - the origin itself was excluded "
                  f"(i!=j), so Dist_{k} is the equal-area radius of "
                  f"those cells, not of the origin's")
        nov = tally["over"].get(k, 0)
        if nov:
            # BACKLOG 142: this said "the k YOU asked for" even when
            # the pass was EquiPop's own - John ran k=400 with
            # self-calibration on Dist_500 and was told about a k he
            # had never typed.
            asked = "the k asked for" if label else "the k you asked for"
            print(f"[selfpot]{label} k={k}: N_{k} is at least twice "
                  f"{asked} in {nov:,} of {tot:,} origins - cells are "
                  f"counted whole, so N_k >= k always")
