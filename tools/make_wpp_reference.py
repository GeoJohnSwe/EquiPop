#!/usr/bin/env python3
"""
make_wpp_reference.py - build EquiPop's national reference table from
the UN World Population Prospects 2024.

v1.60.0, BACKLOG 416. Machine 4's life expectancy, TFR, CBR and CDR
read a LOCAL age pyramid against the NATION's: the national life table
gives the age pattern of survival, the national fertility schedule the
age pattern of births. Those national schedules come from here.

SOURCE. The `wpp2024` R package (United Nations Population Division,
version 1.1-3, 2024-11-26; https://github.com/PPgp/wpp2024), whose
data are licensed Creative Commons Attribution 3.0 IGO - which permits
redistribution with attribution. Used:
    mx1dt.rda          death rates by single year of age 0-100+,
                       women, men, both, 1950-2100 (medium variant)
    percentASFR1dt.rda the age pattern of fertility, ages 10-54
    tfr1dt.rda         total fertility 1950-2023
    tfrproj1dt.rda     total fertility 2024-2100, medium variant
    e01dt.rda, e0proj1dt.rda   WPP's own life expectancy, used ONLY
                       to check the life tables built here
    popAge1dt.rda      population by single year of age to 2023, and
    popproj1dt.rda     population 2024-2100, medium variant - summed
                       to the national total (v1.60.2), so machine 4
                       can warn when a folder is far short of its
                       country
    UNlocations.txt    which codes are countries (location_type 4)

WHAT IS WRITTEN, one row per country, year 2000-2030 and sex (B both,
F women, M men), in WorldPop's age bands - 0, 1-4, then fives, 90+:
    l_<age>   survivors to the start of the band, radix 1
    L_<age>   person-years lived in the band (the open 90+ band: all
              person-years from 90 on)
    and, on the F row only:
    f_<age>   age-specific fertility, births per woman per year, for
              the bands 10-14 ... 50-54
    tfr       5 x the sum of f_<age> (equals WPP's TFR)
    and on every row (v1.60.2):
    pop       WPP's national population of that sex, in people

THE LIFE TABLE. From single-year death rates: q = m / (1 + (1-a) m),
a = 0.5 except at age 0, where a0 follows Andreev & Kingkade (2015),
the rule the Human Mortality Database uses (for both sexes, the mean
of the women's and men's rules). The open 100+ interval lives l/m.
Checked here against WPP's published e0: the build REFUSES if any
country-year-sex differs by more than 0.25 years.

Run (needs pyreadr and pycountry, at build time only - neither is a
dependency of EquiPop):
    python tools/make_wpp_reference.py <path to wpp2024/data>
Writes equipop/data/wpp2024_reference.csv.xz and its .json record.
Five significant digits, xz-compressed: about 2 MB for 236 countries
x 31 years x 3 sexes; the rounding moves no life expectancy by more
than a few thousandths of a year.
"""

from __future__ import annotations

import hashlib
import json
import lzma
import os
import sys

import numpy as np
import pandas as pd

YEARS = range(2000, 2031)
BANDS = [0, 1] + list(range(5, 91, 5))          # WorldPop band starts
FERT = list(range(10, 51, 5))                    # 10-14 ... 50-54
OUT = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "equipop", "data")
TOLERANCE = 0.25                                  # years of e0

# WPP codes that are not ISO 3166 numeric, or that WorldPop spells
# its own way.
EXTRA_ISO3 = {412: "XKX"}                         # Kosovo


def a0(m0, sex):
    """Andreev & Kingkade (2015) average age at death in year 0."""
    if sex == "M":
        return np.where(m0 >= 0.08307, 0.29915,
                        np.where(m0 >= 0.023, 0.02832 + 3.26201 * m0,
                                 0.14929 - 1.99545 * m0))
    if sex == "F":
        return np.where(m0 >= 0.06891, 0.31411,
                        np.where(m0 >= 0.01724, 0.04667 + 3.88089 * m0,
                                 0.14903 - 2.05527 * m0))
    return (a0(m0, "M") + a0(m0, "F")) / 2


def life_table(mx, sex):
    """Single-year mx (ages 0..100, 100 open) -> lx, Lx (radix 1)."""
    mx = np.asarray(mx, float)
    ax = np.full(mx.shape, 0.5)
    ax[0] = a0(mx[0], sex)
    qx = np.minimum(mx / (1 + (1 - ax) * mx), 1.0)
    qx[-1] = 1.0
    lx = np.concatenate([[1.0], np.cumprod(1 - qx[:-1])])
    dx = lx * qx
    Lx = lx - (1 - ax) * dx
    Lx[-1] = lx[-1] / mx[-1] if mx[-1] > 0 else 0.0
    return lx, Lx


def bands(lx, Lx):
    l_b, L_b = [], []
    for i, s in enumerate(BANDS):
        hi = BANDS[i + 1] if i + 1 < len(BANDS) else len(Lx)
        l_b.append(lx[s])
        L_b.append(Lx[s:hi].sum())
    return l_b, L_b


def _iso3(code):
    if code in EXTRA_ISO3:
        return EXTRA_ISO3[code]
    import pycountry
    c = pycountry.countries.get(numeric=f"{int(code):03d}")
    return c.alpha_3 if c else None


def build(src):
    import pyreadr

    def rda(name):
        return next(iter(pyreadr.read_r(os.path.join(src, name)).values()))

    loc = pd.read_csv(os.path.join(src, "UNlocations.txt"), sep="\t")
    countries = loc[loc["location_type"] == 4][["country_code", "name"]]
    iso = {int(c): _iso3(c) for c in countries["country_code"]}
    unmapped = sorted(n for c, n in zip(countries["country_code"],
                                        countries["name"])
                      if not iso[int(c)])
    keep = {c for c, v in iso.items() if v}

    mx = rda("mx1dt.rda")
    mx = mx[mx["country_code"].isin(keep) & mx["year"].isin(YEARS)]
    pasfr = rda("percentASFR1dt.rda")
    pasfr = pasfr[pasfr["country_code"].isin(keep)
                  & pasfr["year"].isin(YEARS)]
    tfr = pd.concat([rda("tfr1dt.rda")[["country_code", "year", "tfr"]],
                     rda("tfrproj1dt.rda")[["country_code", "year",
                                            "tfr"]]])
    tfr = tfr[tfr["country_code"].isin(keep) & tfr["year"].isin(YEARS)]
    e0 = pd.concat([rda("e01dt.rda")[["country_code", "year", "e0M",
                                      "e0F", "e0B"]],
                    rda("e0proj1dt.rda")[["country_code", "year", "e0M",
                                          "e0F", "e0B"]]])
    e0 = e0.set_index(["country_code", "year"])
    tfr = tfr.set_index(["country_code", "year"])["tfr"]
    # v1.60.2: the national total, for the whole-country warning. WPP
    # gives thousands; the age table is summed over ages to 2023, the
    # projection table is already a total from 2024.
    est = rda("popAge1dt.rda")
    est = (est[est["country_code"].isin(keep) & est["year"].isin(YEARS)]
           .groupby(["country_code", "year"])[["popF", "popM"]].sum())
    proj = rda("popproj1dt.rda")
    proj = (proj[proj["country_code"].isin(keep)
                 & proj["year"].isin(YEARS)]
            .set_index(["country_code", "year"])[["popF", "popM"]])
    pop = pd.concat([est, proj])
    if pop.index.duplicated().any():
        raise SystemExit("a country-year in both population tables")

    rows, worst = [], (0.0, None)
    for (code, year), g in mx.groupby(["country_code", "year"]):
        g = g.sort_values("age")
        if list(g["age"]) != list(range(101)):
            raise SystemExit(f"{code} {year}: ages are not 0..100")
        fert = None
        p = pasfr[(pasfr["country_code"] == code)
                  & (pasfr["year"] == year)].set_index("age")["pasfr"]
        if len(p):
            t = float(tfr.loc[(code, year)])
            single = {a: t * float(p.get(a, 0.0)) / 100 for a in
                      range(10, 55)}
            fert = [np.mean([single[a] for a in range(s, s + 5)])
                    for s in FERT]
        for sex, col in (("B", "mxB"), ("F", "mxF"), ("M", "mxM")):
            lx, Lx = life_table(g[col].to_numpy(), sex)
            ours = Lx.sum()
            theirs = float(e0.loc[(code, year), f"e0{sex}"])
            if abs(ours - theirs) > worst[0]:
                worst = (abs(ours - theirs),
                         f"{iso[code]} {int(year)} {sex}: {ours:.3f} "
                         f"against WPP's {theirs:.3f}")
            l_b, L_b = bands(lx, Lx)
            row = {"iso3": iso[code], "year": int(year), "sex": sex}
            f_, m_ = (1000 * float(v) for v in pop.loc[(code, year)])
            row["pop"] = {"B": f_ + m_, "F": f_, "M": m_}[sex]
            row.update({f"l_{s}": v for s, v in zip(BANDS, l_b)})
            row.update({f"L_{s}": v for s, v in zip(BANDS, L_b)})
            if sex == "F" and fert is not None:
                row.update({f"f_{s}": v for s, v in zip(FERT, fert)})
                row["tfr"] = 5 * sum(fert)
            rows.append(row)
    if worst[0] > TOLERANCE:
        raise SystemExit(f"life tables disagree with WPP's e0 by "
                         f"{worst[0]:.3f} years at {worst[1]} - "
                         "refusing to write")
    df = pd.DataFrame(rows).sort_values(["iso3", "year", "sex"])
    return df, worst, unmapped


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        raise SystemExit(__doc__)
    src = argv[0]
    df, worst, unmapped = build(src)
    csv_path = os.path.join(OUT, "wpp2024_reference.csv.xz")
    text = df.to_csv(index=False, float_format="%.5g")
    # xz carries no timestamp: the same table always gives the same bytes
    with open(csv_path, "wb") as f:
        f.write(lzma.compress(text.encode("utf-8"), preset=9))
    digest = hashlib.sha256(open(csv_path, "rb").read()).hexdigest()
    record = {
        "what": "National life tables (by WorldPop age band) and "
                "fertility schedules, for machine 4's life expectancy, "
                "TFR, CBR and CDR",
        "source": "United Nations, Department of Economic and Social "
                  "Affairs, Population Division (2024). World "
                  "Population Prospects 2024. Via the wpp2024 R package "
                  "1.1-3 (2024-11-26), https://github.com/PPgp/wpp2024",
        "licence": "Creative Commons Attribution 3.0 IGO "
                   "(https://creativecommons.org/licenses/by/3.0/igo/)",
        "variant": "estimates to 2023, medium variant from 2024",
        "years": [min(YEARS), max(YEARS)],
        "countries": int(df["iso3"].nunique()),
        "bands": BANDS, "fertility_bands": FERT,
        "life_table": "single-year mx -> q = m/(1+(1-a)m), a = 0.5, a0 "
                      "Andreev & Kingkade 2015 (both sexes: mean of the "
                      "women's and men's rule), open 100+ lives l/m; "
                      "aggregated to bands",
        "population": "pop: WPP 2024's national population of that sex "
                      "(popAge1dt summed over ages to 2023, popproj1dt "
                      "medium from 2024), in people",
        "check": f"largest difference from WPP's own e0: "
                 f"{worst[0]:.3f} years ({worst[1]})",
        "not_mapped_to_iso3": unmapped,
        "sha256": digest,
    }
    with open(os.path.join(OUT, "wpp2024_reference.json"), "w",
              encoding="utf-8") as f:
        json.dump(record, f, indent=1, ensure_ascii=False)
    print(f"wrote {csv_path}: {len(df)} rows, "
          f"{df['iso3'].nunique()} countries, "
          f"{os.path.getsize(csv_path) / 1e6:.2f} MB; {record['check']}")
    if unmapped:
        print("not mapped to ISO3 (left out):", ", ".join(unmapped))


if __name__ == "__main__":
    main()
