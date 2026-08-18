"""
stata_bridge.py - the pure-Python side of the Stata integration.

Design: everything computable lives HERE (tested by pytest, no Stata
required); the .ado file's python block only moves arrays across the
sfi boundary and calls knn_to_rows(). That keeps the untestable-
outside-Stata surface to a few lines.

The contract that makes the Stata round trip work: results come back
ROW-ALIGNED to the input observations (one value per individual, the
spec's "disaggregated outfile"), so the ado can store them straight
into the dataset in memory and the user can `regress` immediately.
Rows with missing coordinates receive missing values.

BACKLOG 136: this module is the SHARED dispatch that every door
funnels through - QGIS, ArcGIS Pro, Stata and the Python API - so its
messages are read by all of them. It used to prefix them "[stata]",
which John found in an ArcGIS Pro log: "[stata] returning 4 new
variables". A Pro user reading their own log had no idea why Stata was
involved, and it quietly contradicted the one architectural claim the
project makes about itself. The prefix is now "[equipop]". The MODULE
NAME is the same problem in slower motion and is left for 120, when
this file is being moved anyway - anyone writing the R or SPSS door of
133 will still open stata_bridge.py to find dispatch().
"""

import numpy as np
import pandas as pd

from .cells import build_cells
from . import selfpot
from .fastcounts import run_knn_counts


def _binned_decay_counts(cd, cells, k_values, r_values, decay,
                         half_life, n_bins, decay_eps, m_neighbors,
                         n_rows, valid, self_potential=1.0,
                         overshoot_mode=None, seed=None):
    """VARIABLE-BANDWIDTH decay (v1.17): each row carries its own
    half-life - an estimated median travel distance, a group
    potential, or the row's own Dist_k (urban form setting the
    bandwidth).

    A cell may hold people with different bandwidths, so the pass is
    run once per QUANTILE BIN of the half-life, restricted to the
    cells that actually contain that bin's people (`origins=`), with
    the bin's own Decay. Destination mass and the tree stay global,
    so every pass is exact; only the kernel differs. Cost is
    dominated by the widest bin, because the truncation radius
    scales with the half-life.
    """
    from .decay import Decay
    h = np.asarray(half_life, float)
    hv = h[np.asarray(valid)]
    if not np.isfinite(hv).all() or (hv <= 0).any():
        raise ValueError("[decay] the half-life field holds missing, "
                         "zero or negative values - every row needs a "
                         "positive bandwidth in metres")
    n_bins = max(1, int(n_bins))
    uniq = np.unique(hv)
    if len(uniq) <= n_bins:
        # few distinct bandwidths (a group potential, say): each one
        # gets its OWN pass - no approximation at all
        idx = np.searchsorted(uniq, hv)
    else:
        cuts = np.unique(np.quantile(
            hv, np.linspace(0.0, 1.0, n_bins + 1)[1:-1]))
        idx = np.searchsorted(cuts, hv, side="right")
    # quantile cuts can skip labels; make the bins consecutive so
    # row -> frame alignment cannot slip
    _, idx = np.unique(idx, return_inverse=True)
    cell_e = np.asarray(cells["_E"])
    cell_n = np.asarray(cells["_N"])
    key_to_pos = {(e, n): i for i, (e, n) in
                  enumerate(zip(cd.E, cd.N))}
    frames = []
    print(f"[decay] variable bandwidth: {len(np.unique(idx))} bins "
          f"over half-lives {hv.min():,.0f}-{hv.max():,.0f} m")
    for b in range(idx.max() + 1):
        sel = idx == b
        hb = float(np.median(hv[sel]))
        origins = sorted({key_to_pos[(e, n)] for e, n in
                          zip(cell_e[sel], cell_n[sel])
                          if (e, n) in key_to_pos})
        # build a FRESH Decay: beta is derived in __post_init__, so
        # mutating half_life_m on a copy would leave the old kernel
        dec_b = Decay(model=decay.model, half_life_m=hb,
                      gamma=getattr(decay, "gamma", None))
        print(f"[decay]   bin {int(b) + 1}: half-life {hb:,.0f} m, "
              f"{int(sel.sum())} rows, {len(origins)} origin cells")
        part = run_knn_counts(cd, k_values, decay_eps=decay_eps,
                              m_neighbors=m_neighbors,
                              r_values=r_values, decay=dec_b,
                              overshoot_mode=overshoot_mode, seed=seed,
                              origins=np.asarray(origins, int),
                              self_potential=self_potential,
                              report=False)
        part = part.set_index(["EastWest", "NorthSouth"])
        frames.append((sel, part))
    # Rows of a bin read THAT bin's pass. A cell holding people of
    # two bandwidths legitimately yields two different decayed sums -
    # one per person - which a single cell-indexed frame cannot say,
    # so the bins travel separately to the row mapping.
    row_bin = np.asarray(idx, int)
    parts = [f[1] for f in frames]
    # non-decay columns (N, Dist, T, R) are identical across bins -
    # the union of the passes covers every cell, so any occurrence
    # serves as the base frame
    base = pd.concat(parts)
    base = base[~base.index.duplicated(keep="first")]
    return parts, row_bin, base


def blank_missing_codes(bag, codes):
    """Turn declared missing codes into real missing values.

    Returns (new_bag, how_many_blanked). The input dict is not changed.

    BACKLOG 168, and it is not cosmetic. John's Bristol County extract
    carries the Census sentinel -666666666 in 64 of 1,074 rows for
    median household income. Left alone, a neighbourhood mean lands
    near minus forty million, and it lands there quietly.

    John's ruling on what a blanked case IS: the cause does not matter,
    the ability to exclude does. Such a case "could still be the
    placeholder for results - it just doesn't contribute self". So it
    stays a person towards k, and still receives its own row of
    answers; only its VALUE drops out. Any share it helps form is
    divided by the people actually OBSERVED, never by everybody
    present - 400 people with 60 of unknown group gives a denominator
    of 340.
    """
    if not codes or not bag:
        return dict(bag or {}), 0
    arr_codes = np.asarray([float(c) for c in codes], dtype=float)
    out, hits = {}, 0
    for name, arr in bag.items():
        a = np.asarray(arr, dtype=float).copy()
        hit = np.isin(a, arr_codes)
        n = int(hit.sum())
        if n:
            a[hit] = np.nan
            hits += n
            print(f"[equipop] '{name}': {n} values matched a declared "
                  f"missing code - those cases still count as people "
                  f"towards k and still receive results, but "
                  f"contribute nothing of their own.")
        out[name] = a
    return out, hits


def validate_treatment(treat, weight, treat_are_counts):
    """Refuse a treatment specification that cannot be true.

    Returns None, or raises ValueError with a sentence a non-programmer
    can act on.

    THE DEFECT THIS CLOSES (external review of 1.36, confirmed):
    the help and both GIS doors say treat() holds the group's PERSON
    COUNT at each point; the Stata bridge applied the legacy rule, in
    which treat is a 0/1 flag multiplied by the population. A user
    following the help with a population of 100 and a group count of
    30 received T = 3000 - a group three times larger than the
    neighbourhood containing it - and a share of 30.0, meaning 3000%.
    Nothing stopped, nothing warned loudly enough, and the numbers look
    like numbers.

    John's ruling, v1.37.1: counts are the default, the flag rule stays
    available by name, and a group larger than its own population is
    refused rather than reported. No correct configuration can trip
    this, which is the test of a good guard.
    """
    if not treat:
        return

    if not treat_are_counts:
        # Flag rule: the value multiplies the population, so anything
        # outside 0-1 silently invents or destroys people.
        for name, arr in treat.items():
            a = np.asarray(arr, dtype=float)
            fin = a[np.isfinite(a)]
            if len(fin) and (fin.min() < 0 or fin.max() > 1):
                raise ValueError(
                    f"treatmode(flags) means '{name}' holds 0 or 1 - a "
                    f"share of each row's population - but it ranges "
                    f"from {fin.min():g} to {fin.max():g}. If it holds "
                    f"the number of PEOPLE in the group, use "
                    f"treatmode(counts), which is the default.")
        return

    # Count rule: the group at a point cannot exceed the population at
    # that point, and without a population there is nothing to compare
    # it against - N would count ROWS while T summed PEOPLE.
    if weight is None:
        for name, arr in treat.items():
            a = np.asarray(arr, dtype=float)
            fin = a[np.isfinite(a)]
            if len(fin) and fin.max() > 1:
                raise ValueError(
                    f"'{name}' holds counts of people (it reaches "
                    f"{fin.max():g}), but no population was given, so "
                    f"every row would count as one person while the "
                    f"group summed many. Add pop(varname) or "
                    f"[fweight=varname]. If '{name}' is really a 0/1 "
                    f"marker, use treatmode(flags).")
        return

    w = np.asarray(weight, dtype=float)
    for name, arr in treat.items():
        a = np.asarray(arr, dtype=float)
        # A NEGATIVE count is impossible too, and the check for "bigger
        # than the population" cannot see it - a sentinel of
        # -666666666 is comfortably SMALLER than any population. Found
        # in 1.38 by a test that expected the undeclared Census
        # sentinel to be refused and watched it sail through.
        fin = a[np.isfinite(a)]
        if len(fin) and fin.min() < 0:
            raise ValueError(
                f"'{name}' goes down to {fin.min():g}, and a number of "
                f"people cannot be negative. If that value means NO "
                f"DATA rather than a count - census extracts use codes "
                f"like -666666666, -9 or 999 - declare it with "
                f"missing({fin.min():g}) and it will be excluded "
                f"properly.")
        both = np.isfinite(a) & np.isfinite(w)
        over = int(np.count_nonzero(a[both] > w[both]))
        if over:
            worst = float(np.max(a[both] - w[both]))
            raise ValueError(
                f"'{name}' is larger than the population at {over} "
                f"of {int(both.sum())} points - by up to {worst:g} "
                f"people. A group cannot be bigger than the population "
                f"containing it. Either the two variables are the wrong "
                f"way round, or '{name}' is a 0/1 marker and needs "
                f"treatmode(flags).")


def check_results_are_possible(result):
    """The backstop, on the way OUT.

    Everything above checks the INPUT. This checks the answer: a
    neighbourhood's group count cannot exceed its population, whatever
    route produced it. John ruled it in independently of the treatment
    contract, on the reasoning that no correct run can trip it.

    A guard on the input can be defeated by an engine change; a guard
    on the output cannot, because it reads the number the user is
    about to be given.
    """
    counts = {n: a for n, a in result.items() if n.startswith("N_")}
    for name, arr in result.items():
        if not name.startswith("T_"):
            continue
        suffix = name.split("_")[-1]
        pop = counts.get(f"N_{suffix}")
        if pop is None:
            continue
        t = np.asarray(arr, dtype=float)
        n = np.asarray(pop, dtype=float)
        both = np.isfinite(t) & np.isfinite(n)
        # A hair of tolerance for floating-point summation only.
        over = int(np.count_nonzero(t[both] > n[both] * (1 + 1e-9) + 1e-6))
        if over:
            worst = float(np.max(t[both] - n[both]))
            raise ValueError(
                f"{name} exceeds {'N_' + suffix} at {over} places - by "
                f"up to {worst:g} people. A neighbourhood cannot hold "
                f"more people of one group than it holds in total, so "
                f"this result would be impossible. Check whether the "
                f"treatment variable holds counts of people "
                f"(treatmode(counts), the default) or a 0/1 marker "
                f"(treatmode(flags)).")


def project_for_stata(x, y, epsg=None):
    """Project a Stata run's coordinates from degrees to metres.

    Returns (easting, northing, epsg, sentence).

    Projection is NOT a parameter of the counting engine - it is a
    conversion that happens before the count, on the way in. Keeping it
    here rather than in the `python:` block means the suite can reach
    it; keeping it out of knn_to_rows() means the engine still receives
    plain metric coordinates and knows nothing about degrees.

    John's condition on the feature was that the run must say which
    projection it used, so the sentence comes back with the numbers
    rather than being assembled by the caller.
    """
    from .utm import to_utm, describe

    east, north, code = to_utm(lat=y, lon=x, epsg=epsg)
    return east, north, code, describe(code)


def degrees_warning(x, y):
    """A sentence if these coordinates look like unprojected lat/long,
    otherwise None.

    Warn, never act. Silently projecting data the user did not ask to
    project would change every number in the output with no record of
    why; silently counting in degrees - which is what happened before
    1.37 - gives a wrong answer with no signal at all. A sentence
    naming the option is the only honest option of the three.
    """
    from .utm import looks_like_degrees

    if not looks_like_degrees(x, y):
        return None
    return ("WARNING: x() and y() look like longitude and latitude in "
            "degrees. Distances computed on degrees are not distances: "
            "a degree of longitude is shorter than a degree of latitude "
            "everywhere except the equator, so neighbourhoods come out "
            "stretched and the k nearest neighbours are not the nearest "
            "k. Add the option -project- to project to UTM first, or "
            "pass coordinates that are already in metres.")


def zone_span_warning(x, y, epsg=None):
    """A sentence if a Stata run's data is wider than one UTM zone
    comfortably holds, otherwise None. Never refuses - see
    equipop.utm.zone_span_note for John's reasoning.
    """
    from .utm import zone_span_note

    try:
        return zone_span_note(lat=y, lon=x, epsg=epsg)
    except Exception:                       # noqa: BLE001
        # A note about the data must never be the thing that stops a
        # run. If it cannot be computed, there is simply no note.
        return None


def knn_to_rows(x, y, k_values=None, treat: dict | None = None,
                weight=None, unit_size: float = 100.0,
                m_neighbors: int | None = None,
                decay_eps: float = 1e-6,
                r_values=None, decay=None,
                treat_are_counts: bool = False,
                strict_treatment: bool = True,
                missing_codes=None,
                decay_half_life=None, decay_bins: int = 10,
                self_potential: float = 1.0,
                overshoot_mode: str | None = None,
                seed: int | None = None,
                report_label: str = "") -> dict:
    """
    k-NN counts/ratios for individual-level rows, returned row-aligned.

    Parameters
    ----------
    x, y      : 1-D arrays of metric coordinates (one row = one
                individual or one weighted record).
    k_values  : list of k thresholds (optional if r_values given).
    r_values  : optional metric radii -> N_r<r>, T_<v>_r<r>, R_<v>_r<r>.
    treat     : {name: 1-D array} of numeric treatment variables
                (0/1 per individual, or counts if weighted rows).
    weight    : optional 1-D array - population represented by each
                row (default 1 per row).
    unit_size : grid size in metres.

    Returns
    -------
    dict {column_name: 1-D float array, same length as x} with, per k:
      N_<k>, Dist_<k>, and per treatment v: T_<v>_<k>, R_<v>_<k>.
    Rows with missing coordinates get NaN throughout.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n_rows = len(x)
    treat = treat or {}
    w = (np.ones(n_rows) if weight is None
         else np.asarray(weight, dtype=float))

    # BACKLOG 168. Blank the declared codes FIRST, before anything
    # looks at the numbers - otherwise a sentinel like -666666666 is
    # judged by validate_treatment() as a group count, and refused for
    # being negative rather than recognised as absent.
    treat, _blanked = blank_missing_codes(treat, missing_codes)

    df = pd.DataFrame({"_x": x, "_y": y, "_w": w})
    for name, arr in treat.items():
        df[name] = np.asarray(arr, dtype=float)
    # Two conventions, explicit since v1.14.1 (the ArcGIS field-test
    # bug): treat_are_counts=False (legacy, Stata) -> treat is a 0/1
    # FLAG on a weighted row, contribution = flag * weight.
    # treat_are_counts=True (GIS door) -> treat IS the group's person
    # COUNT at the point; weight is the TOTAL count; no multiplication.
    # Refuse what cannot be true BEFORE doing the work - see
    # validate_treatment() for the defect this closes.
    if strict_treatment:
        validate_treatment(treat, weight, treat_are_counts)
    for name in treat:
        if not treat_are_counts:
            df[name] = df[name] * df["_w"]
    if treat_are_counts and weight is not None:
        for name in treat:
            over = int((df[name] > df["_w"]).sum())
            if over:
                print(f"[bridge] WARNING: '{name}' exceeds the "
                      f"population at {over} points - group counts "
                      "larger than totals is a data error.")

    valid = df["_x"].notna() & df["_y"].notna()
    dv = df[valid]

    # individuals -> cells (weights become cell population)
    cells = dv.copy()
    half = unit_size / 2.0
    cells["_E"] = (np.floor(cells["_x"] / unit_size) * unit_size
                   + half).astype(np.int64)
    cells["_N"] = (np.floor(cells["_y"] / unit_size) * unit_size
                   + half).astype(np.int64)
    # BACKLOG 168. Alongside each treatment total, the WEIGHT of the
    # rows whose value for it is usable. Not the count of rows: with
    # aggregated input a row stands for many people, and the
    # denominator John ruled on counts PEOPLE. Identical to `_w`
    # unless missing codes blanked something, so nothing moves for a
    # run that declares none.
    for v in treat:
        cells[f"__ok__{v}"] = np.where(cells[v].notna(),
                                       cells["_w"], 0.0)
    agg = {"_w": "sum", **{v: "sum" for v in treat},
           **{f"__ok__{v}": "sum" for v in treat}}
    g = cells.groupby(["_E", "_N"], as_index=False).agg(agg)

    from .cells import CellData
    cd = CellData(E=g["_E"].to_numpy(), N=g["_N"].to_numpy(),
                  n=g["_w"].to_numpy(),
                  binary_sums={v: g[v].to_numpy(float) for v in treat},
                  binary_valid={v: g[f"__ok__{v}"].to_numpy(float)
                                for v in treat},
                  value_arrays={}, unit_size=unit_size)
    k_values = sorted(k_values or [])
    r_values = sorted(r_values or [])
    if treat and weight is None and not treat_are_counts:
        for _v, _a in treat.items():
            _fin = _a[np.isfinite(_a)]
            if len(_fin) and np.nanmax(_fin) > 1:
                print(f"[bridge] HINT: group '{_v}' holds COUNTS "
                      "(values > 1) but no population/weight field is "
                      "set - N will count ROWS while T sums persons, "
                      "so shares can exceed 1. Set the Population "
                      "field (weight) to the total-persons column.")
                break
    bin_frames = bin_of_row = None
    if decay is not None and decay_half_life is not None:
        bin_frames, bin_of_row, base = _binned_decay_counts(
            cd, cells, k_values, r_values, decay, decay_half_life,
            decay_bins, decay_eps, m_neighbors, n_rows, valid,
            self_potential=self_potential,
            overshoot_mode=overshoot_mode, seed=seed)
        res = base.reset_index()
    else:
        res = run_knn_counts(cd, k_values, decay_eps=decay_eps,
                             m_neighbors=m_neighbors,
                             r_values=r_values, decay=decay,
                             self_potential=self_potential,
                             overshoot_mode=overshoot_mode, seed=seed,
                             report_label=report_label)

    # map cell results back to every individual row
    res = res.set_index(["EastWest", "NorthSouth"])
    keys = list(zip(cells["_E"], cells["_N"]))
    labs = [f"r{r:g}" for r in r_values]
    out_cols = ([f"N_{k}" for k in k_values + labs]
                + [f"Dist_{k}" for k in k_values]
                + [f"T_{v}_{k}" for v in treat for k in k_values + labs]
                + [f"R_{v}_{k}" for v in treat for k in k_values + labs])
    if decay is not None:                    # BACKLOG 185: at k, not
        out_cols += [c for c in                      # unbounded
                     tuple(f"ND_{k}" for k in k_values + labs)
                     + tuple(f"TD_{v}_{k}" for v in treat
                             for k in k_values + labs)
                     + tuple(f"RD_{v}_{k}" for v in treat
                             for k in k_values + labs)
                     if c in res.columns]
    out = {}
    vidx = np.flatnonzero(valid.to_numpy())
    decay_cols = {c for c in out_cols
                  if c.startswith(("ND_", "TD_", "RD_"))}
    for c in out_cols:
        col = np.full(n_rows, np.nan)
        if bin_frames is not None and c in decay_cols:
            # each row reads the pass run with ITS OWN bandwidth
            vals = np.full(len(vidx), np.nan)
            for b, frame in enumerate(bin_frames):
                m = bin_of_row == b
                if not m.any():
                    continue
                kk = [keys[i] for i in np.flatnonzero(m)]
                vals[m] = frame.loc[kk, c].to_numpy(dtype=float)
            col[vidx] = vals
        else:
            col[vidx] = res.loc[keys, c].to_numpy(dtype=float)
        out[c] = col
    n_miss = n_rows - len(vidx)
    if n_miss:
        print(f"[equipop] {n_miss} rows with missing coordinates -> "
              f"missing results")
    print(f"[equipop] returning {len(out)} new variables for "
          f"{n_rows} observations")
    # The backstop, on the way out. A guard on the input can be
    # defeated by an engine change; this one reads the number the user
    # is about to be handed.
    if strict_treatment:
        check_results_are_possible(out)
    return out


# =====================================================================
# #17 - THE DISPATCHER: one row-alignment layer for every engine.
# dispatch(engine, x, y, ...) -> dict of row-aligned arrays, so the
# single ado equipop_run.ado can expose the whole toolbox to Stata.
# =====================================================================

def _snap(x, y, unit):
    half = unit / 2.0
    E = (np.floor(np.asarray(x, float) / unit) * unit + half)
    N = (np.floor(np.asarray(y, float) / unit) * unit + half)
    return E.astype(np.int64), N.astype(np.int64)


def _add_empty_origin_cells(cd, E, N, value_vars):
    """Cells that are ORIGINS but hold no population (v1.29.2).

    A row outside the reference population weighs zero, so it
    contributes no individuals and its cell never appears in the
    grid - yet it is still entitled to ask what is around it
    (John's rule, 1.22.2). The k-search copes with an empty cell
    perfectly well: it simply reaches outward until it has k
    persons, which is exactly the intended meaning.
    """
    have = set(zip(np.asarray(cd.E).tolist(), np.asarray(cd.N).tolist()))
    want = [p for p in dict.fromkeys(zip(np.asarray(E).tolist(),
                                         np.asarray(N).tolist()))
            if p not in have]
    if not want:
        return cd
    ex, ny = zip(*want)
    cd.E = np.append(np.asarray(cd.E, float), np.asarray(ex, float))
    cd.N = np.append(np.asarray(cd.N, float), np.asarray(ny, float))
    cd.n = np.append(np.asarray(cd.n), np.zeros(len(want), dtype=cd.n.dtype))
    for v in value_vars:
        cd.value_arrays[v] = list(cd.value_arrays[v]) + \
            [np.array([], float) for _ in want]
    for v, arr in list(cd.binary_sums.items()):
        cd.binary_sums[v] = np.append(np.asarray(arr, float),
                                      np.zeros(len(want), float))
    if cd.labels is not None:
        cd.labels = list(cd.labels) + [None] * len(want)
    print(f"[cells] {len(want)} origin cell(s) hold no population - "
          "they are nobody's neighbour but still get their own "
          "results")
    return cd


def _map_back(res, keys, cols, valid, n_rows):
    """Cell-level frame -> row-aligned dict (NaN for invalid rows)."""
    res = res.set_index(["EastWest", "NorthSouth"]) \
        if "EastWest" in res.columns else res.set_index(["x", "y"])
    vidx = np.flatnonzero(valid)
    out = {}
    for c in cols:
        col = np.full(n_rows, np.nan)
        col[vidx] = res.loc[keys, c].to_numpy(dtype=float)
        out[c] = col
    return out


def dispatch(engine: str, x, y, unit_size: float = 100.0,
             treat: dict | None = None, weight=None,
             k_values=None, r_values=None, tau_values=None,
             # stats engine:
             values: dict | None = None, stats: dict | None = None,
             # slope / friction:
             dem: str | None = None, model: str = "tobler",
             roundtrip: bool = False, friction_file: str | None = None,
             # fca:
             supply_file: str | None = None, demand_arr=None,
             supply_x: str = "x", supply_y: str = "y",
             supply_col: str = "supply", half_life_m: float | None = None,
             reach: str = "decay", method: str = "2sfca",
             k_fca: float | None = None, r_fca: float | None = None,
             decay_eps: float = 1e-6,
             half_life_field=None, half_life_from_dist=None,
             decay_bins: int = 10,
             self_potential: float = selfpot.DEFAULT_SELF_POTENTIAL,
             overshoot_mode: str | None = None,
             seed: int | None = None,
             missing_codes=None,
             **extra) -> dict:
    """
    One entry point, five engines, row-aligned results:

    engine="counts"   -> knn_to_rows (k/r, multiple treatments, weight)
    engine="stats"    -> run_knn_stats (values+stats dicts, k/r)
    engine="friction" -> run_knn_friction (k/tau, one treat, fr file)
    engine="slope"    -> run_knn_slope (k/tau, DEM, model, roundtrip)
    engine="fca"      -> fca (demand = the rows; supply from a FILE;
                         returns A and J mapped to rows)

    Everything computable is here (pytest-covered); the ado only moves
    arrays over sfi and calls this.
    """
    x = np.asarray(x, float); y = np.asarray(y, float)
    n_rows = len(x)
    valid = np.isfinite(x) & np.isfinite(y)

    # BACKLOG 168, John's ruling: declared codes ARE missing.
    #
    # Done HERE, once, rather than inside each engine. Every door and
    # the Python API reach the engines through this function, so one
    # conversion covers counts, stats, friction, slope and fca - and
    # no engine learns a new concept. Same reasoning as the Gini
    # guard of BACKLOG 154, which sits here for the same reason.
    #
    # The effect, in his words: such a case "could still be the
    # placeholder for results - it just doesn't contribute self". It
    # stays a person towards k and still receives its own row of
    # answers; only its VALUE drops out, and any share it helps form
    # is divided by the people actually observed, never by everybody
    # present.
    if missing_codes:
        _codes = np.asarray([float(c) for c in missing_codes],
                            dtype=float)
        _hits = 0
        for _bag in (values, treat):
            if isinstance(_bag, dict):
                for _name, _arr in list(_bag.items()):
                    _a = np.asarray(_arr, dtype=float).copy()
                    _hit = np.isin(_a, _codes)
                    if _hit.any():
                        _a[_hit] = np.nan
                        _hits += int(_hit.sum())
                    _bag[_name] = _a
        if _hits:
            print(f"[equipop] {_hits} values matched a declared "
                  "missing code - those cases still count as people "
                  "towards k and still receive results, but "
                  "contribute nothing of their own, and shares are "
                  "divided by the people actually observed.")

    if engine == "counts":
        dec = None
        if half_life_m or half_life_field is not None \
                or half_life_from_dist:
            from .decay import Decay
            # with a variable bandwidth the half-life here is only a
            # placeholder - every bin builds its own kernel
            dec = Decay(model=extra.get("decay_model", "negexp"),
                        half_life_m=float(half_life_m or 1000.0),
                        gamma=extra.get("gamma"))
        hl = half_life_field
        if hl is None and half_life_from_dist and dec is not None:
            # SELF-CALIBRATING bandwidth (v1.17): each row's own
            # Dist_k - the radius it needed to gather k persons -
            # becomes its half-life, so urban form sets the
            # bandwidth instead of an assumed distance. Computed by a
            # plain k-run first, then fed back as the kernel.
            k0 = int(half_life_from_dist)
            first = knn_to_rows(x, y, [k0], weight=weight,
                                unit_size=unit_size,
                                self_potential=self_potential,
                                # BACKLOG 142: EquiPop's own pass,
                                # not the user's run
                                report_label=" calibration pass,",
                                treat_are_counts=extra.get(
                                    "treat_are_counts", False))
            hl = first[f"Dist_{k0}"]
            good = np.isfinite(hl) & (hl > 0)
            if not good.any():
                raise ValueError(
                    f"[decay] self-calibration needs Dist_{k0}, but no "
                    "row got a usable radius")
            # BACKLOG 96. Rows with no usable Dist_k borrow the median
            # bandwidth of everyone else. That is a reasonable last
            # resort and a TERRIBLE silence: before 1.29.5 a dense
            # cell reported Dist_k = 0, so the whole urban core - the
            # very place this feature exists to serve - was handed a
            # median kernel and nothing said so. The range printed
            # below used to be the range AFTER substitution, which
            # hid it completely. Now both numbers are shown.
            n_sub = int((~good).sum())
            lo, hi = float(np.nanmin(hl[good])), float(np.nanmax(hl[good]))
            med = float(np.nanmedian(hl[good]))
            hl = np.where(good, hl, med)
            print(f"[decay] self-calibrated bandwidth from Dist_{k0}: "
                  f"{lo:,.0f}-{hi:,.0f} m (median {med:,.0f} m) "
                  f"over {int(good.sum()):,} rows")
            if n_sub:
                print(f"[decay] WARNING: {n_sub:,} of {len(hl):,} rows "
                      f"({100.0 * n_sub / len(hl):.1f}%) had no usable "
                      f"Dist_{k0} and were given the MEDIAN bandwidth "
                      f"({med:,.0f} m) instead of their own. Their "
                      "bandwidth is not self-calibrated."
                      + (" Self-potential is off (0), which forces this "
                         "for every row whose own cell already holds "
                         f"{k0} - see BACKLOG 95."
                         if selfpot.check(self_potential) <= 0 else ""))
        return knn_to_rows(x, y, k_values, treat=treat, weight=weight,
                           overshoot_mode=overshoot_mode, seed=seed,
                           unit_size=unit_size, r_values=r_values,
                           decay=dec, decay_eps=decay_eps,
                           decay_half_life=hl, decay_bins=decay_bins,
                           self_potential=self_potential,
                           treat_are_counts=extra.get(
                               "treat_are_counts", False))

    if engine == "stats":
        from .analysis import run_knn_stats
        values = values or {}
        df = pd.DataFrame({"_x": x, "_y": y})
        for v, arr in values.items():
            a = np.asarray(arr, float)
            a = np.where(a > 8.9e307, np.nan, a)
            df[v] = a
        members = valid
        if weight is not None:
            # v1.16 FULL-POPULATION field: each row carries this many
            # persons; k is measured against PERSONS, and every value
            # statistic weights by population - implemented EXACTLY by
            # expanding rows to persons (median/Gini/percentiles come
            # out weighted by construction).
            #
            # v1.29.2, BACKLOG 83: a row with no count is not a
            # MEMBER, but it is still an ORIGIN. John's rule since
            # 1.22.2 - a row outside the reference population counts
            # as ZERO, is nobody's neighbour, and STILL GETS ITS OWN
            # RESULTS. Machine 1 has always done this; machine 2
            # dropped such rows entirely, because expanding by the
            # count makes a zero-count row vanish. So ORIGIN and
            # MEMBER are now separate sets. A door that wants Null
            # instead says so by NaN-ing the coordinates, which is
            # how `keepoutside` has always worked.
            w = np.asarray(weight, float)
            w = np.where(w > 8.9e307, np.nan, w)
            rep = np.where(np.isfinite(w) & (w > 0),
                           np.round(w), 0).astype(np.int64)
            members = valid & (rep > 0)
            df["_rep"] = rep
        dv = df[valid]
        E, N = _snap(dv["_x"], dv["_y"], unit_size)   # per INPUT row
        pop = df[members]
        if weight is not None:
            n_persons = int(pop["_rep"].sum())
            outside = int(valid.sum() - members.sum())
            print(f"[equipop] full population: {len(pop)} of {len(df)} "
                  f"rows carry a usable count -> {n_persons} persons "
                  f"(k counts PERSONS)")
            if outside:
                print(f"[equipop] {outside} row(s) have no count (empty "
                      "or zero): they count as ZERO and are nobody's "
                      "neighbour, but they still get their own "
                      "results - what is around THEM.")
            pop = pop.loc[pop.index.repeat(pop["_rep"])] \
                     .drop(columns="_rep").reset_index(drop=True)
        dv = pop
        cd = build_cells(dv, "_x", "_y", value_vars=list(values),
                         unit_size=unit_size)
        cd = _add_empty_origin_cells(cd, E, N, list(values))
        st = run_knn_stats(cd, k_values=k_values, r_values=r_values,
                           self_potential=self_potential,
                           overshoot_mode=overshoot_mode, seed=seed,
                           stats=stats or {v: ["mean", "median", "gini"]
                                           for v in values})
        from .stats import stat_prefix
        req = stats or {v: ["mean", "median", "gini"] for v in values}
        allowed = {"N", "Nv", "Dist"} | {
            stat_prefix(s) for ss in req.values() for s in ss}
        cols = [c for c in st.columns
                if c.split("_")[0] in allowed]
        return _map_back(st, list(zip(E, N)), cols, valid, n_rows)

    if engine in ("friction", "slope"):
        from .io import read_table, resolve_xy_columns
        w = np.ones(n_rows) if weight is None else np.asarray(weight,
                                                              float)
        counts_mode = extra.pop("treat_are_counts", False)
        fr = friction_file
        if isinstance(fr, str) and fr:
            fr = read_table(fr)
        if fr is not None:
            fr = resolve_xy_columns(fr, context="barrier table")
            if "friction" not in fr.columns:
                cand = [c for c in fr.columns
                        if c.lower().startswith("frict")
                        or c.lower() in ("cost", "value", "weight")]
                if not cand:
                    raise ValueError(
                        "[bridge] barrier table needs a friction "
                        f"value column - found {list(fr.columns)}")
                print(f"[bridge] barrier table: using '{cand[0]}' "
                      "as friction")
                fr = fr.rename(columns={cand[0]: "friction"})
        groups = (list(treat.items()) if treat
                  else [(None, np.zeros(n_rows))])
        E = N = None
        merged = None
        for gname, garr in groups:
            tr = np.asarray(garr, float)
            cg = np.where(tr > 8.9e307, 0, tr)
            if not counts_mode:
                cg = cg * w
            df = pd.DataFrame({"x": x, "y": y, "count_all": w,
                               "count_group": cg})
            dv = df[valid]
            if E is None:
                E, N = _snap(dv["x"], dv["y"], unit_size)
            pop = (dv.assign(x=E.astype(float), y=N.astype(float))
                   .groupby(["x", "y"], as_index=False).sum())
            if engine == "slope":
                from .slope import run_knn_slope
                res = run_knn_slope(pop, k_values or [],
                                    self_potential=self_potential,
                                    altitude=dem,
                                    model=model, fr=fr,
                                    unit_size=unit_size,
                                    tau_values=tau_values,
                                    roundtrip=roundtrip, **extra)
            else:
                from .friction import run_knn_friction
                res = run_knn_friction(pop, k_values or [], fr=fr,
                                       self_potential=self_potential,
                                       unit_size=unit_size,
                                       tau_values=tau_values)
            if gname is not None:
                res = res.rename(columns={
                    c: (f"T_{gname}_{c[2:]}" if c.startswith("T_")
                        else f"R_{gname}_{c[2:]}")
                    for c in res.columns
                    if c.startswith(("T_", "R_"))})
            if merged is None:
                merged = res
            else:
                # v1.26.1: a run with NO treatment produces no T_/R_
                # columns at all, so take only what is actually there
                keep = [c for c in res.columns
                        if c.startswith(("T_", "R_"))
                        and c in res.columns]
                key = res.columns[:2].tolist()
                if keep:
                    merged = merged.merge(res[key + keep], on=key)
        cols = [c for c in merged.columns if c.split("_")[0]
                in ("N", "T", "R", "Dist", "Rounds")]
        return _map_back(merged, list(zip(E, N)), cols, valid, n_rows)

    if engine == "fca":
        from .fca import fca
        from .decay import Decay
        try:
            from .io import read_table
            sup = read_table(supply_file)
        except Exception:
            sup = (pd.read_csv(supply_file) if supply_file.endswith(".csv")
                   else pd.read_stata(supply_file))
        sup = sup.rename(columns={supply_x: "x", supply_y: "y"})
        d_arr = np.asarray(demand_arr, float)
        d_arr = np.where(d_arr > 8.9e307, np.nan, d_arr)
        df = pd.DataFrame({"x": x, "y": y, "_D": d_arr})
        ok = valid & np.isfinite(df["_D"])
        dv = df[ok]
        E, N = _snap(dv["x"], dv["y"], unit_size)
        dem_cells = (dv.assign(x=E.astype(float), y=N.astype(float))
                     .groupby(["x", "y"], as_index=False).sum())
        dec = (Decay(model="negexp", half_life_m=half_life_m)
               if half_life_m else None)
        d_out, _ = fca(dem_cells, sup, "_D", supply_col, decay=dec,
                       reach=reach, method=method, k=k_fca, r=r_fca)
        return _map_back(d_out, list(zip(E, N)), ["A", "J"],
                         ok.to_numpy() if hasattr(ok, "to_numpy") else ok,
                         n_rows)

    if engine == "lisa":
        from .autocorr import build_weights, local_morans
        vals = values or {}
        if len(vals) != 1:
            raise ValueError("engine='lisa' wants exactly one value "
                             "column in values=")
        vname, arr = next(iter(vals.items()))
        a = np.asarray(arr, float)
        a = np.where(a > 8.9e307, np.nan, a)
        df = pd.DataFrame({"x": x, "y": y, "v": a})
        ok = valid & np.isfinite(df["v"])
        dv = df[ok]
        E, N = _snap(dv["x"], dv["y"], unit_size)
        cells = (dv.assign(E=E, N=N).groupby(["E", "N"], as_index=False)
                 .agg(v=("v", "mean"), n=("v", "size")))
        if (cells["n"] > 1).any():
            print(f"[equipop] {int((cells.n > 1).sum())} cells hold "
                  "several rows - LISA runs on CELL MEANS (loudly)")
        W = build_weights(cells["E"], cells["N"], mode="knn",
                          k=int(extra.get("w_k", 8)))
        res = local_morans(cells["v"], W,
                           permutations=int(extra.get("permutations",
                                                      199)))
        res["quadcode"] = res["quad"].map(
            {"HH": 1, "LL": 2, "HL": 3, "LH": 4}).astype(float)
        res["EastWest"] = cells["E"].to_numpy()
        res["NorthSouth"] = cells["N"].to_numpy()
        out = _map_back(res, list(zip(E, N)),
                        ["Ii", "quadcode", "p"], ok.to_numpy()
                        if hasattr(ok, "to_numpy") else ok, n_rows)
        return {f"LISA_{vname}_Ii": out["Ii"],
                f"LISA_{vname}_quad": out["quadcode"],
                f"LISA_{vname}_p": out["p"]}

    raise ValueError(f"unknown engine '{engine}' - use counts / stats "
                     "/ friction / slope / fca / lisa")


# --------------------------------------------------------------------
# Handing values BACK to Stata.  BACKLOG 173.
# --------------------------------------------------------------------
# Stata has no NaN. A missing number in a Stata double is stored as
# 2**1023, and anything larger encodes .a through .z - which is why
# every reader in this file treats `> 8.9e307` as missing on the way
# IN. What follows is the same convention on the way OUT, and it lives
# here rather than in the .ado for one reason: code inside a `python:`
# block can only be run by Stata, so nothing in the test suite can
# reach it. Moving the conversion into the package moves it inside the
# suite. The .ado keeps the sfi calls and nothing else.
#
# What went wrong before: the glue passed Python's None for a missing
# result, and Stata's sfi refuses it - "the specified value should be
# a numeric value". It only ever appeared when a result WAS missing,
# so a dataset with complete coordinates ran fine for eleven releases
# and John's first real run - 9 rows without coordinates - did not.

STATA_MISSING = 8.98846567431158e+307   # 2**1023, Stata's system `.`


def to_stata_values(arr):
    """A numpy array as a list Stata's `Data.store` will accept.

    Plain Python floats, never numpy scalars, and NaN or infinity
    rendered as Stata's own system missing rather than None.
    """
    out = np.asarray(arr, dtype=float)
    return [float(v) if np.isfinite(v) else STATA_MISSING for v in out]
