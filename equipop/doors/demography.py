"""
demography.py - MACHINE 4: demographic indices over k-neighbourhoods.

John's design, and his ruling that it belongs in its own machine:
machine 3 turns rasters into points, machine 4 asks a demographic
question of them.

WHAT THIS IS FOR, and it is not what WorldPop already publishes.
WorldPop ships a gridded Dependency Ratio computed FROM EACH CELL'S
OWN age structure. This computes it over THE k NEAREST THOUSAND
PEOPLE. Those are different measures: theirs describes a cell, ours
describes the population a person is actually among. A ratio over
administrative units inherits the units; a ratio over a bespoke
neighbourhood does not, and that is the whole argument.

WHAT AN INDEX IS HERE. Every one of these is a RATIO OF TWO GROUPS
counted over the same neighbourhood:

    index = (people matching the numerator) / (people matching the
             denominator), both summed over the k nearest people

so the machinery is machine 1's, with two treatment groups and a
division. Nothing new is being computed; what is new is that the
groups are named after demography rather than after columns.

WHAT IS DELIBERATELY ABSENT. TFR, ASFR, CBR, CDR and life expectancy
are NOT here, because they need vital events and an age-sex folder
carries stock, not flow. If a births raster is added to the folder it
becomes an ordinary column and they open up with no new machinery -
see BACKLOG 216, and read the circularity note there first.

WORLDPOP AGE BANDS ARE NOT ALL FIVE YEARS (John): 0 is under-one on
its own, 1 covers 1-4, then fives, and the last is open at 90+. Every
selector below works in BAND STARTS for that reason, never in
arithmetic on the age number.
"""

from __future__ import annotations

import re


class DemographyError(Exception):
    """Refused before anything ran, with the reason in plain words."""


# A label is  {sex}_{age}_{year}  - see rasterfolder.LABEL_FIELDS.
_LABEL = re.compile(r"^(?P<sex>[fmt])_(?P<age>\d+)_(?P<year>\d{4})$")

# The band starts WorldPop actually ships, in order.
BAND_STARTS = [0, 1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60,
               65, 70, 75, 80, 85, 90]


def _bands_from(lo: int, hi: int | None) -> list:
    """Band STARTS whose whole band lies inside [lo, hi].

    hi=None means open-ended. Works in band starts because the bands
    are irregular: asking for "15 to 49" must give 15,20,...,45 and
    must NOT quietly include 50.
    """
    from .. rasterfolder import age_band
    out = []
    for s in BAND_STARTS:
        a, b = age_band(s)
        if a < lo:
            continue
        if hi is not None and (b is None or b > hi):
            continue
        out.append(s)
    return out


# ---------------------------------------------------------------- the
# Each index says which people are on top and which underneath, in
# demographic words. `sexes` of None means every sex present.
INDICES = {
    "child_woman_ratio": {
        "code": "cwr",
        "label": "Child-woman ratio",
        "numerator": {"sexes": None, "ages": (0, 4)},
        "denominator": {"sexes": ("f",), "ages": (15, 49)},
        "about":
            "Children under five per woman of childbearing age. THE "
            "STANDARD FERTILITY PROXY where vital registration is weak "
            "- which is where gridded population data is used. It "
            "needs no births layer, because both parts are stock.",
    },
    "dependency_ratio": {
        "code": "dep",
        "label": "Dependency ratio",
        "numerator": {"sexes": None, "ages": (0, 14), "plus": (65, None)},
        "denominator": {"sexes": None, "ages": (15, 64)},
        "about":
            "People too young or too old to work, per person of "
            "working age. WorldPop publishes this per GRID CELL from "
            "that cell's own age structure; this is over the k nearest "
            "people, which is a different measure.",
    },
    "ageing_index": {
        "code": "age",
        "label": "Ageing index",
        "numerator": {"sexes": None, "ages": (65, None)},
        "denominator": {"sexes": None, "ages": (0, 14)},
        "about":
            "People 65 and over per person under 15. Where the "
            "dependency ratio lumps both ends together, this separates "
            "them - two places can share a dependency ratio and be "
            "demographically opposite.",
    },
    "sex_ratio": {
        "code": "sex",
        "label": "Sex ratio",
        "numerator": {"sexes": ("m",), "ages": (0, None)},
        "denominator": {"sexes": ("f",), "ages": (0, None)},
        "about":
            "Men per woman. Over a k-neighbourhood this reads as "
            "labour migration and institutional population rather than "
            "as anything biological.",
    },
}


def _split(label):
    m = _LABEL.match(str(label))
    return m.groupdict() if m else None


def columns_for(spec: dict, labels, year=None) -> list:
    """Which of `labels` this half of an index is made of."""
    wanted = set(_bands_from(*spec["ages"]))
    if "plus" in spec:
        wanted |= set(_bands_from(*spec["plus"]))
    sexes = spec["sexes"]

    out = []
    for lab in labels:
        d = _split(lab)
        if d is None:
            continue
        if year is not None and d["year"] != str(year):
            continue
        # 't' is f+m, so mixing it with either double counts. Only use
        # it when the index does not care about sex AND the parts are
        # absent - decided in pick_sex() below, not here.
        if sexes is not None and d["sex"] not in sexes:
            continue
        if int(d["age"]) in wanted:
            out.append(lab)
    return out


def pick_sex(labels, year=None) -> tuple:
    """Which sex columns to use when an index does not care about sex.

    A folder may hold f, m AND t, and t is exactly f+m - John's own
    numbers: bdi age 00 has f 224,972 + m 229,148 and t 454,120. Using
    all three counts everybody twice, so choose ONE route and say
    which.
    """
    have = {d["sex"] for d in (_split(l) for l in labels) if d
            and (year is None or d["year"] == str(year))}
    if {"f", "m"} <= have:
        return ("f", "m")
    if "t" in have:
        return ("t",)
    if have:
        return tuple(sorted(have))
    raise DemographyError(
        "No columns here look like a cohort. Machine 4 needs labels of "
        "the form sex_age_year, such as f_15_2026 - which is what "
        "machine 3 produces from a WorldPop folder.")


def years_in(labels) -> list:
    return sorted({d["year"] for d in (_split(l) for l in labels) if d})


def parse_spec(text):
    """An age range, optionally restricted by sex: 'f:15-49', '65-'.

    John: "we should allow for alterations of the measurement settings
    - please make it possible to accept or edit the measures (for
    instance the age settings)". Typing out eleven column names to
    move a boundary by five years is not editing, it is transcription.
    So a half of an index can be respecified in the terms it is
    actually thought about: WHICH AGES, and WHICH SEX.

        '0-4'      -> ages 0 to 4, whichever sexes the index uses
        'f:15-49'  -> women only
        '65-'      -> 65 and over, open ended
        'm:'       -> men, every age

    Returns {"sexes": tuple|None, "ages": (lo, hi|None)}.
    """
    raw = str(text or "").strip()
    if not raw:
        return None
    sexes = None
    if ":" in raw:
        head, raw = raw.split(":", 1)
        head = head.strip().lower()
        if head:
            bad = [c for c in head if c not in "fmt"]
            if bad:
                raise DemographyError(
                    f"{''.join(bad)!r} is not a sex. Use f, m or t - "
                    "or several, like 'fm:15-49'.")
            sexes = tuple(head)
        raw = raw.strip()
    if not raw:
        return {"sexes": sexes, "ages": (0, None)}
    # TWO RANGES, comma separated: the dependency ratio's numerator is
    # "0-14,65-" - both ends of the pyramid. INDICES expresses that as
    # ages + plus, and a user editing the table must be able to write
    # the same thing.
    if "," in raw:
        chunks = [c.strip() for c in raw.split(",") if c.strip()]
        if len(chunks) != 2:
            raise DemographyError(
                f"{text!r}: give one age range, or two separated by a "
                "comma, as in '0-14,65-'.")
        # JOIN WITH NOTHING, not with '/'. The recursion rebuilds the
        # sex prefix to re-parse each half, and 'f/m:0-14' is not the
        # syntax this function accepts - so 'fm:0-14,65-' was refused
        # with a message naming a '/' the user never typed. Found by
        # the external review of 1.43.
        head = ("".join(sexes) + ":") if sexes else ""
        first = parse_spec(head + chunks[0])
        second = parse_spec(head + chunks[1])
        return {"sexes": sexes, "ages": first["ages"],
                "plus": second["ages"]}

    parts = [q.strip() for q in raw.split("-")]
    if len(parts) > 2 or not parts[0]:
        raise DemographyError(
            f"{text!r} is not an age range. Write it as '15-49', or "
            "'65-' for open ended, optionally with a sex: 'f:15-49'.")
    try:
        lo = int(parts[0])
        hi = int(parts[1]) if len(parts) == 2 and parts[1] else None
    except ValueError:
        raise DemographyError(
            f"{text!r} is not an age range - the ages must be whole "
            "numbers, as in '15-49'.")
    if hi is not None and hi < lo:
        raise DemographyError(
            f"{text!r} runs backwards: {lo} is after {hi}.")
    return {"sexes": sexes, "ages": (lo, hi)}


def plan(name, labels, year=None, num_spec=None,
         den_spec=None) -> dict:
    """Work out an index's two halves WITHOUT running anything.

    Separated so a door can show the user exactly which columns are
    about to be added up, and let them edit it - John: "suggested
    fields loaded, but with option to add/remove".
    """
    if name not in INDICES:
        raise DemographyError(
            f"No such index: {name!r}. Available: "
            + ", ".join(sorted(INDICES)))
    spec = INDICES[name]

    yrs = years_in(labels)
    if year is None:
        if len(yrs) > 1:
            raise DemographyError(
                f"These points carry {len(yrs)} years ({', '.join(yrs)}). "
                "An index is computed for ONE year - say which, or run "
                "it once per year.")
        if not yrs:
            raise DemographyError(
                "No columns here look like a cohort. Machine 4 needs "
                "labels of the form sex_age_year, such as f_15_2026.")
        year = yrs[0]

    # NORMALISE THE YEAR. Labels carry it as text; a door may hand in
    # an int from a spin box. Returning whichever type the caller
    # happened to pass made the plan's own year not comparable with
    # the labels it selected - caught by a test, not by reading.
    year = str(year)
    sexes = pick_sex(labels, year)
    num = dict(num_spec or spec["numerator"])
    den = dict(den_spec or spec["denominator"])
    if num["sexes"] is None:
        num["sexes"] = sexes
    if den["sexes"] is None:
        den["sexes"] = sexes

    top = columns_for(num, labels, year)
    bot = columns_for(den, labels, year)
    if not top:
        raise DemographyError(
            f"{spec['label']}: nothing to put on top. Wanted ages "
            f"{num['ages']} for {'/'.join(num['sexes'])} in {year}, "
            f"and the points carry none of them.")
    if not bot:
        raise DemographyError(
            f"{spec['label']}: nothing to divide by. Wanted ages "
            f"{den['ages']} for {'/'.join(den['sexes'])} in {year}, "
            f"and the points carry none of them.")
    return {"index": name, "label": spec["label"], "about": spec["about"],
            "year": year, "sexes": list(sexes),
            "numerator": top, "denominator": bot}


# ------------------------------------------------------------- running
def run_index(folders, name, *, k_values, unit_size=1000.0, year=None,
              epsg=None, numerator=None, denominator=None,
              channel=None, **kw):
    """A folder of rasters to a demographic index over k-neighbourhoods.

    numerator/denominator override the plan, so a door can offer the
    suggested fields and let the user add or remove - John's design.

    Returns the manifest with 'results' carrying the index column.
    """
    from .continental import check_folders, run_folder
    from ..rasterfolder import load_folder

    say = channel.info if channel is not None else print
    check_folders(folders)      # before we peek at the labels

    # Look at the labels first, so the plan can be shown and refused
    # before any of the arithmetic starts.
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        pts, _man = load_folder(folders, **{k: v for k, v in kw.items()
                                            if k in ("convention",
                                                     "labels",
                                                     "pattern")})
    labels = [c for c in pts.columns if c not in ("lon", "lat", "iso3")]
    del pts

    p = plan(name, labels, year=year)
    if numerator:
        p["numerator"] = list(numerator)
    if denominator:
        p["denominator"] = list(denominator)

    say(f"{p['label']}, {p['year']}.")
    say(f"  on top    : {' + '.join(p['numerator'])}")
    say(f"  divided by: {' + '.join(p['denominator'])}")
    say(f"  {p['about']}")

    # The neighbourhood is defined by EVERYBODY - John's ruling that
    # constant k is enough. The two halves ride along as groups.
    # The two halves are COMPOSED into one column each, then carried
    # as groups. compose= makes the sums; groups= counts them over the
    # neighbourhood. The neighbourhood itself is defined by everybody,
    # which is John's ruling that constant k is enough.
    man = run_folder(folders, k_values=k_values, unit_size=unit_size,
                     epsg=epsg,
                     weight="sexes" if p["sexes"] != ["t"] else "total",
                     # PASS THE YEAR DOWN. Without it the reference
                     # population is summed across EVERY year in the
                     # folder, so analysing 2020 changes once 2030 has
                     # been downloaded (BACKLOG 273).
                     year=year,
                     compose={"num": p["numerator"],
                              "den": p["denominator"]},
                     groups=["num", "den"],
                     channel=channel, **kw)

    res = man["results"]
    for k in k_values:
        top, bot = f"T_num_{k}", f"T_den_{k}"
        if top in res.columns and bot in res.columns:
            import numpy as np
            b = res[bot].to_numpy(dtype=float)
            res[f"{name}_{k}"] = np.where(
                b > 0, res[top].to_numpy(dtype=float) / b, np.nan)
    man["plan"] = p
    say("The index is a ratio of two counts over the SAME "
        "neighbourhood, so it inherits nothing from any administrative "
        "unit - which is the reason to compute it this way.")
    return man


def run_indices(folders, names, *, k_values, unit_size=1000.0, year=None,
                epsg=None, overrides=None, channel=None, **kw):
    """SEVERAL indices in ONE traverse of the data.

    John's preference, and it matters at continental scale: loading
    120 rasters, projecting eleven million points and building the
    tree is most of the cost, and it is identical whichever index you
    want. Four indices one at a time is four of those; this is one.

    overrides: {index_name: {"numerator": [...], "denominator": [...]}}
    so a door can offer the suggested columns and let them be edited.
    """
    import contextlib
    import io

    import numpy as np

    from .continental import check_folders, run_folder
    from ..rasterfolder import load_folder

    say = channel.info if channel is not None else print
    check_folders(folders)      # before we peek at the labels
    names = list(names)
    if not names:
        raise DemographyError(
            "No index chosen. Available: " + ", ".join(sorted(INDICES)))

    with contextlib.redirect_stdout(io.StringIO()):
        pts, _m = load_folder(folders, **{k: v for k, v in kw.items()
                                          if k in ("convention", "labels",
                                                   "pattern")})
    labels = [c for c in pts.columns if c not in ("lon", "lat", "iso3")]
    del pts

    plans, compose, groups = {}, {}, []
    for nm in names:
        ov = (overrides or {}).get(nm, {})
        pl = plan(nm, labels, year=year,
                  num_spec=parse_spec(ov.get("numerator_ages")),
                  den_spec=parse_spec(ov.get("denominator_ages")))
        for half in ("numerator", "denominator"):
            got = ov.get(half)
            if got:
                pl[half] = list(got)
        code = INDICES[nm]["code"]
        compose[f"{code}_num"] = pl["numerator"]
        compose[f"{code}_den"] = pl["denominator"]
        groups += [f"{code}_num", f"{code}_den"]
        plans[nm] = pl
        say(f"{pl['label']}, {pl['year']}:")
        say(f"   on top    : {' + '.join(pl['numerator'])}")
        say(f"   divided by: {' + '.join(pl['denominator'])}")

    sexes = plans[names[0]]["sexes"]
    man = run_folder(folders, k_values=k_values, unit_size=unit_size,
                     epsg=epsg,
                     weight="sexes" if sexes != ["t"] else "total",
                     # PASS THE YEAR DOWN. Without it the reference
                     # population is summed across EVERY year in the
                     # folder, so analysing 2020 changes once 2030 has
                     # been downloaded (BACKLOG 273).
                     year=year,
                     compose=compose, groups=groups, channel=channel,
                     **kw)

    res = man["results"]
    for nm in names:
        code = INDICES[nm]["code"]
        for k in k_values:
            top, bot = f"T_{code}_num_{k}", f"T_{code}_den_{k}"
            if top in res.columns and bot in res.columns:
                b = res[bot].to_numpy(dtype=float)
                res[f"{code}_{k}"] = np.where(
                    b > 0, res[top].to_numpy(dtype=float) / b, np.nan)
    man["plans"] = plans
    say("")
    say("WHAT THE FIELDS MEAN:")
    for line in explain_fields(list(res.columns), plans,
                               (man.get("projection") or {}).get("epsg")):
        say(line)
    say("")
    say(f"{len(names)} {'index' if len(names) == 1 else 'indices'} over "
        "the SAME neighbourhoods, in one traverse - each is a ratio of "
        "two counts among the k nearest people, so none of them "
        "inherits anything from an administrative unit.")
    return man


# ------------------------------------------------------ what it means
def explain_fields(columns, plans=None, epsg=None):
    """One line per output field, in plain words.

    John, on his first real result: "I have no explanation to what the
    field names are representing". Quite right - a table with
    T_age_num_1000 and R_age_den_1000 and SumN in it is unreadable
    unless you wrote the code. So the run now says.
    """
    out = []
    if epsg:
        out.append(f"THE LAYER IS IN EPSG:{epsg}. Coordinates are "
                   "METRES in that projection, not degrees. If it "
                   "draws in the wrong part of the world, the QGIS "
                   "PROJECT is in a different CRS - check Layer "
                   "Properties > Information.")
    known = {
        "CellId": "which analysis cell this row is",
        "EastWest": "cell centre, easting, in the projection above",
        "NorthSouth": "cell centre, northing",
        "iso3": "the country the point came from",
        "N_local": "people in THIS CELL ALONE - not a neighbourhood",
        "SumN": "people in the whole search window; a diagnostic of "
                "the search, not an answer",
        "MaxDistance": "distance to the furthest cell the search "
                       "fetched; also a diagnostic",
    }
    groups = {}
    for nm, pl in (plans or {}).items():
        code = INDICES[nm]["code"]
        groups[f"{code}_num"] = (pl["label"], "numerator",
                                 pl["numerator"])
        groups[f"{code}_den"] = (pl["label"], "denominator",
                                 pl["denominator"])

    for c in columns:
        if c in known:
            out.append(f"  {c}: {known[c]}")
            continue
        # N_<k>, Dist_<k>
        m = re.match(r"^N_(\d+)$", c)
        if m:
            out.append(f"  {c}: people in the neighbourhood - exactly "
                       f"{m.group(1)} by construction, because k fixes "
                       "the population")
            continue
        m = re.match(r"^Dist_(\d+)$", c)
        if m:
            out.append(f"  {c}: the RADIUS this place needed to reach "
                       f"{m.group(1)} people. It varies, and that "
                       "variation is the density of the place")
            continue
        # T_<group>_<k>, R_<group>_<k>
        m = re.match(r"^([TR])_(.+)_(\d+)$", c)
        if m and m.group(2) in groups:
            lab, half, parts = groups[m.group(2)]
            k = m.group(3)
            if m.group(1) == "T":
                out.append(f"  {c}: {lab} {half} - HOW MANY PEOPLE "
                           f"among the nearest {k}, adding up "
                           f"{len(parts)} cohorts")
            else:
                out.append(f"  {c}: {lab} {half} as a SHARE of the "
                           f"{k} - the same count divided by {k}")
            continue
        # <code>_<k>  - the index itself
        for nm, pl in (plans or {}).items():
            code = INDICES[nm]["code"]
            mm = re.match(rf"^{code}_(\d+)$", c)
            if mm:
                out.append(f"  {c}: >>> {pl['label']} over the nearest "
                           f"{mm.group(1)} people. This is the answer; "
                           "the T_ and R_ columns are its parts")
                break
        else:
            if c.endswith("_local") and plans:
                base = c[:-6]
                if base in groups:
                    lab, half, _ = groups[base]
                    out.append(f"  {c}: {lab} {half} in THIS CELL "
                               "ALONE - not a neighbourhood")
                    continue
            out.append(f"  {c}")
    return out
