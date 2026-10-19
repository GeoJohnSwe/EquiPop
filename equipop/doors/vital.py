"""
vital.py - life expectancy, TFR, CBR and CDR from ONE age pyramid,
read against the nation's (machine 4, v1.60.0, BACKLOG 416).

WHAT THIS IS, AND IS NOT. An age-and-sex folder holds people, not
births or deaths, so none of these is MEASURED here. They are
MODEL-BASED: the nation's own schedules (UN World Population Prospects
2024, shipped as equipop/data/wpp2024_reference.csv.xz) give the AGE
PATTERN, and the neighbourhood's own pyramid gives the LEVEL. John's
use is as predictors - "as a researcher I am not looking for truth but
variables to make better predictions" - and every output says what it
is, so nobody reads one as a register figure.

WHY NOT SIMPLY "NATIONAL RATES x LOCAL AGES". Life expectancy and TFR
do not depend on a population's age structure at all, so national
rates applied to local ages give back the NATIONAL value in every
neighbourhood. Anything that varies locally needs a local signal of
level, and the pyramid is the only one the folder has.

LIFE EXPECTANCY - John's idea, read relative to the nation. If every
cohort started equally large and nobody moved, the pyramid WOULD be
the life table. It is not - births grew, and that reads as death:
simulated, a Kenya-like nation with e0 65.1 reads 32.5 that way. So
the comparison is made against the nation, whose own birth history
then cancels:

    local survival(x) = national survival(x)
                        x (local share at x / local share at a)
                        / (national share at x / national share at a)

    e(a) = sum over bands from a of  national L(band) x that ratio
           / national l(a)

The national shares are the folder's OWN totals for the country, so a
folder's reporting habits (age heaping, old-age exaggeration) cancel
where they are the same nationwide. Simulated on stable populations
(BACKLOG 416): read from 60 the answer stays within about two years
under local growth differences and is untouched by young
in-migration; read from 50, 30 or birth it is not - growth of 3.0 %
against a national 2.2 % reads e0 49 for a true 65. Those three are
computed because John asked for them, and are NAMED UNRELIABLE.

TFR - the child-woman ratio, given the nation's age pattern, and READ
AGAINST THE NATION like life expectancy. Children under five are the
survivors of five years of births to the women here. If local rates
are a multiple lambda of the national ones, the children per birth
expected at national rates, E = sum(women(a) x f_nat(a)), scale with
lambda:

    lambda = (children / E) here  /  (children / E) in the nation
    TFR    = lambda x TFR_nat

With women spread evenly over 15-49 this is the familiar 7 x C/W
(Hauer, Baker & Brown 2013); weighting the women by the national
schedule is the refinement Hauer & Schmertmann (2020, Demography
57:221-241) show recovers TFR from a pyramid to about 0.1 births per
woman. Reading against the nation does what an absolute reading
cannot: child survival, the five-year lag of births behind the women
counted now, and the folder's own counting habits all cancel where
they are national, so the nation's own neighbourhood gives back the
nation's TFR exactly.

CBR = births a year per 1,000 people: lambda x E x 1000 / people.

CDR = deaths a year per 1,000 people: the nation's death rates below
60, and from 60 the nation's scaled by the factor that gives the
neighbourhood's own e60. Below 60 it therefore describes AGE
STRUCTURE only, which is where most deaths are not.
"""

from __future__ import annotations

import functools
import os

import numpy as np

#: The bands WorldPop ships (0 under one, 1 = 1-4, then fives, 90 open).
BANDS = [0, 1] + list(range(5, 91, 5))
FERT = list(range(10, 51, 5))                   # 10-14 ... 50-54
REFERENCE = "wpp2024_reference.csv.xz"

#: name -> what the door shows, the output column stem, and whether the
#: measure is to be trusted. Column stems are short so that a k of
#: 10,000 still fits a shapefile's ten-character field names.
MEASURES = {
    "life_expectancy_60": {
        "code": "e60", "start": 60, "reliable": True,
        "label": "Life expectancy at 60",
        "about": "years a person aged 60 here would still live, if the "
                 "nation's age pattern of death applied at the level "
                 "this neighbourhood's own pyramid implies"},
    "life_expectancy_50": {
        "code": "e50u", "start": 50, "reliable": False,
        "label": "Life expectancy at 50 (UNRELIABLE)",
        "about": "as at 60, from 50 - local differences in growth and "
                 "migration read as mortality, so treat as a predictor, "
                 "not a life expectancy"},
    "life_expectancy_30": {
        "code": "e30u", "start": 30, "reliable": False,
        "label": "Life expectancy at 30 (UNRELIABLE)",
        "about": "as at 60, from 30 - young adults move, and that "
                 "movement reads as survival; a predictor, not a life "
                 "expectancy"},
    "life_expectancy_0": {
        "code": "e0u", "start": 0, "reliable": False,
        "label": "Life expectancy at birth (UNRELIABLE)",
        "about": "as at 60, from birth - a place with more births than "
                 "the nation reads as one with more deaths; in "
                 "simulation, 3.0 % growth against 2.2 % gave 49 for a "
                 "true 65. A predictor, not a life expectancy"},
    "total_fertility_rate": {
        "code": "TFR", "start": None, "reliable": True,
        "label": "Total fertility rate",
        "about": "children per woman over a lifetime, from the "
                 "child-woman ratio and the nation's age pattern of "
                 "fertility and child survival"},
    "crude_birth_rate": {
        "code": "CBR", "start": None, "reliable": True,
        "label": "Crude birth rate",
        "about": "births a year per 1,000 people, from the children "
                 "under five and the nation's child survival"},
    "crude_death_rate": {
        "code": "CDR", "start": None, "reliable": True,
        "label": "Crude death rate",
        "about": "deaths a year per 1,000 people: the nation's death "
                 "rates below 60, and from 60 the level this "
                 "neighbourhood's e60 implies"},
}

#: Which measures need which parts of the pyramid.
NEEDS_WOMEN = ("total_fertility_rate", "crude_birth_rate")
NEEDS_LE60 = ("crude_death_rate",)

#: k below which a life expectancy is noisy: the 85-89 and 90+ bands
#: then hold a handful of people. 5,000 is the usual floor for
#: small-area life expectancy (Eayres & Williams 2004).
LE_K_FLOOR = 5000


class VitalError(Exception):
    """Refused, with the reason in plain words."""


# ------------------------------------------------------- the reference
#: Below this share of WPP's national population, a folder is not the
#: whole country, and the run says so (v1.60.2). WorldPop's totals are
#: matched to the UN's, so a whole country lands close to 100%; 90%
#: leaves room for a revision between the two.
WHOLE_COUNTRY = 0.90


def _data_dir():
    return os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "data")


@functools.lru_cache(maxsize=1)
def reference():
    """The national table, read once per session - and CHECKED once.

    v1.60.2, external review of 1.60.1 (P3): the record beside the
    table carries its SHA-256, and nothing compared them, so a damaged
    or mis-assembled installation would have been read as UN data.
    Now the checksum, the columns, one row per country-year-sex, the
    years and the signs are checked before anything is read from it.
    """
    import hashlib
    import json

    import pandas as pd
    path = os.path.join(_data_dir(), REFERENCE)
    with open(path.replace(".csv.xz", ".json"), encoding="utf-8") as f:
        meta = json.load(f)
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    if digest != meta.get("sha256"):
        raise VitalError(
            f"The national reference table shipped with EquiPop "
            f"({REFERENCE}) does not match its own record: SHA-256 "
            f"{digest[:12]}... where the record says "
            f"{str(meta.get('sha256'))[:12]}... The installation is "
            "damaged or was assembled from mismatched files - "
            "reinstall EquiPop.")
    df = pd.read_csv(path)
    need = (["iso3", "year", "sex", "pop", "tfr"]
            + [f"{x}_{b}" for x in "lL" for b in BANDS]
            + [f"f_{a}" for a in FERT])
    gone = [c for c in need if c not in df.columns]
    lo, hi = meta["years"]
    num = df.drop(columns=["iso3", "sex"])
    faults = (([f"columns missing: {', '.join(gone)}"] if gone else [])
              + (["a country-year-sex appears twice"]
                 if df.duplicated(["iso3", "year", "sex"]).any() else [])
              + ([f"years outside {lo}-{hi}"]
                 if not df["year"].between(lo, hi).all() else [])
              + (["negative values"] if (num < 0).any().any() else []))
    if faults:
        raise VitalError(
            f"The national reference table shipped with EquiPop is not "
            f"what it should be ({'; '.join(faults)}). Reinstall "
            "EquiPop.")
    df["iso3"] = df["iso3"].str.upper()
    return df.set_index(["iso3", "year", "sex"]).sort_index(), meta


def citation():
    _df, meta = reference()
    return f"{meta['source']}. Licence: {meta['licence']}."


def national(iso3, year, sex, top=90):
    """The nation's schedules in the folder's bands.

    sex: 'B' both, 'F' women, 'M' men. top: the folder's open band
    (90 for R2025A, 80 for the 2000-2020 series) - the reference's
    bands above it are folded into it.
    Returns {bands, l, L, m, f, tfr} - l, L, m per band; f the
    fertility rates for 10-14 ... 50-54 (women's table).
    """
    df, meta = reference()
    key = (str(iso3).upper(), int(year), sex)
    lo, hi = meta["years"]
    if not lo <= int(year) <= hi:
        raise VitalError(
            f"The national reference covers {lo}-{hi}; this folder is "
            f"{year}. Rates and life expectancies cannot be read "
            "against a year it does not have.")
    if key not in df.index:
        raise VitalError(
            f"No national life table for {str(iso3).upper()} in the "
            "reference (UN WPP 2024 covers 236 countries and areas). "
            "Those points are left empty.")
    row = df.loc[key]
    keep = [b for b in BANDS if b <= top]
    l = np.array([row[f"l_{b}"] for b in keep], float)
    L = np.array([row[f"L_{b}"] for b in keep], float)
    L[-1] = sum(row[f"L_{b}"] for b in BANDS if b >= top)
    nxt = np.append(l[1:], 0.0)
    m = (l - nxt) / L
    out = {"bands": keep, "l": l, "L": L, "m": m,
           "pop": float(row["pop"])}
    w = df.loc[(key[0], key[1], "F")]
    out["f"] = np.array([w[f"f_{a}"] for a in FERT], float)
    out["tfr"] = float(w["tfr"])
    return out


# ------------------------------------------------------ the estimators
def life_expectancy(S, P, l, L, start):
    """e(start) per row, read relative to the nation.

    S: (rows, bands) people by band in each neighbourhood
    P: (bands,) people by band in the nation (the folder's own total)
    l, L: the nation's life table in the same bands
    start: index of the band the expectancy is from
    """
    S = np.asarray(S, float)
    P = np.asarray(P, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        local = S / S[:, [start]]
        nat = P / P[start]
        rho = local[:, start:] / nat[start:]
        e = (L[start:] * rho).sum(axis=1) / l[start]
    e[~np.isfinite(e)] = np.nan
    return e


def fertility(C, W, N, f, tfr_nat, C_nat, W_nat):
    """(TFR, CBR) per row from the child-woman ratio, read against the
    nation's.

    C: children 0-4; W: (rows, 9) women 10-14 ... 50-54; N: everybody;
    C_nat, W_nat: the same for the whole nation (the folder's total).
    """
    C = np.asarray(C, float)
    W = np.asarray(W, float)
    N = np.asarray(N, float)
    E = (W * f).sum(axis=1)                 # births a year at national rates
    E_nat = float((np.asarray(W_nat, float) * f).sum())
    with np.errstate(divide="ignore", invalid="ignore"):
        lam = (C / E) / (float(C_nat) / E_nat)
        tfr = lam * tfr_nat
        cbr = 1000 * lam * E / N
    tfr[~np.isfinite(tfr)] = np.nan
    cbr[~np.isfinite(cbr)] = np.nan
    return tfr, cbr


def _e_from(m, widths, start):
    """e(start) from band death rates (a = half the band), vectorised:
    m is (rows, bands from start); the last band is open."""
    rows = m.shape[0]
    l = np.ones(rows)
    total = np.zeros(rows)
    for j in range(m.shape[1]):
        if j == m.shape[1] - 1:
            total += l / m[:, j]
            break
        n = widths[j]
        q = np.minimum(n * m[:, j] / (1 + n / 2 * m[:, j]), 1.0)
        nxt = l * (1 - q)
        total += n / 2 * (l + nxt)
        l = nxt
    return total


def crude_death_rate(S, N, nat, e60_local, e60_nat):
    """CDR per row: national rates below 60, scaled from 60 so the
    band life table gives the neighbourhood's own e60 relative to the
    nation's."""
    S = np.asarray(S, float)
    bands = nat["bands"]
    i60 = bands.index(60)
    widths = [b2 - b1 for b1, b2 in zip(bands, bands[1:])] + [None]
    m_old = nat["m"][i60:]
    base = _e_from(m_old[None, :], widths[i60:], 0)[0]
    target = np.asarray(e60_local, float) / e60_nat * base
    # e falls as theta rises: bisect log(theta) row by row, together
    lo = np.full(target.shape, np.log(0.02))
    hi = np.full(target.shape, np.log(50.0))
    ok = np.isfinite(target)
    for _ in range(60):
        mid = (lo + hi) / 2
        e = _e_from(np.exp(mid)[:, None] * m_old[None, :], widths[i60:], 0)
        too_long = e > target
        lo = np.where(too_long, mid, lo)
        hi = np.where(too_long, hi, mid)
    theta = np.exp((lo + hi) / 2)
    m = np.tile(nat["m"], (S.shape[0], 1))
    m[:, i60:] *= theta[:, None]
    with np.errstate(divide="ignore", invalid="ignore"):
        cdr = 1000 * (S * m).sum(axis=1) / np.asarray(N, float)
    cdr[~ok | ~np.isfinite(cdr)] = np.nan
    return cdr


# ------------------------------------- each person against their own
#                                         country (v1.60.1 -> 1.61.0)
#
# John, 19 October: a neighbourhood that crosses a border should not be
# read wholly against the country of its cell; "bring the destination
# cell values from its country and weight the results accordingly".
# Every estimator above is a sum over the neighbourhood's people, so
# each POINT can carry its own country's coefficients before the sums
# are taken (demography.vital_own_groups builds them). The functions
# below then read the pooled sums. Within one country every one of
# them reduces EXACTLY to the function above it - tested.

def life_expectancy_own(X, Sa):
    """e(a) = sum over people aged b>=a of (P_a/P_b)(L_b/l_a) of their
    own country, over the people aged a: X / S_a."""
    with np.errstate(divide="ignore", invalid="ignore"):
        e = np.asarray(X, float) / np.asarray(Sa, float)
    e[~np.isfinite(e)] = np.nan
    return e


def fertility_own(C, E, Y, Z, N):
    """(TFR, CBR) from the pooled sums: C children 0-4; E the births a
    year each woman's own country's rates predict; Y = E x that
    country's children per predicted birth (C_nat / E_nat); Z = E x
    that country's TFR; N everybody.

    lambda = C / Y - the children there are, over the children each
    woman's own country would lead one to expect; TFR = lambda x the
    E-weighted national TFR; CBR = 1000 lambda E / N."""
    C, E, Y, Z, N = (np.asarray(v, float) for v in (C, E, Y, Z, N))
    with np.errstate(divide="ignore", invalid="ignore"):
        lam = C / Y
        tfr = lam * Z / E
        cbr = 1000 * lam * E / N
    tfr[~np.isfinite(tfr)] = np.nan
    cbr[~np.isfinite(cbr)] = np.nan
    return tfr, cbr


def crude_death_rate_own(D0, D60, MM, S60p, N, e60_local, e60_ref,
                         widths60):
    """CDR from the pooled sums: D0 the deaths below 60 at each person's
    own country's rates; D60 the same from 60; MM (rows, bands from 60)
    the people aged 60+ times their country's rate in each band - so
    MM / S60p is the neighbourhood's own MIX of national schedules from
    60; e60_ref the e60 the people aged 60 would have at their own
    nations' tables. The mix is scaled by theta so its e60 stands to
    the base as the local e60 stands to e60_ref; deaths from 60 are
    then theta x D60."""
    MM = np.asarray(MM, float)
    S60p = np.asarray(S60p, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        m_mix = MM / S60p[:, None]
        ok_m = np.isfinite(m_mix).all(axis=1) & (m_mix > 0).all(axis=1)
        m_mix[~ok_m] = 1.0                       # placeholder, masked
        base = _e_from(m_mix, widths60, 0)
        target = (np.asarray(e60_local, float)
                  / np.asarray(e60_ref, float) * base)
    ok = ok_m & np.isfinite(target)
    lo = np.full(target.shape, np.log(0.02))
    hi = np.full(target.shape, np.log(50.0))
    for _ in range(60):
        mid = (lo + hi) / 2
        e = _e_from(np.exp(mid)[:, None] * m_mix, widths60, 0)
        too_long = e > np.where(ok, target, 0.0)
        lo = np.where(too_long, mid, lo)
        hi = np.where(too_long, hi, mid)
    theta = np.exp((lo + hi) / 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        cdr = 1000 * (np.asarray(D0, float)
                      + theta * np.asarray(D60, float)) / np.asarray(N, float)
    cdr[~ok | ~np.isfinite(cdr)] = np.nan
    return cdr


__all__ = ["MEASURES", "BANDS", "FERT", "VitalError", "reference",
           "national", "life_expectancy", "fertility",
           "crude_death_rate", "citation", "life_expectancy_own",
           "fertility_own", "crude_death_rate_own"]
