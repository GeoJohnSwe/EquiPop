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


def columns_for(spec: dict, labels, year=None, say=None) -> list:
    """Which of `labels` this half of an index is made of.

    BACKLOG 362. A BAND THE TABLE DOES NOT KNOW WAS DROPPED IN
    SILENCE. BAND_STARTS stops at 90, where 90 means "90 and over" -
    true of WorldPop, not of every product. A folder carrying f_95 or
    f_100 had those cohorts excluded from every index while
    `weight='sexes'` still counted them in the reference population,
    because that picks columns by the f_/m_ PREFIX alone. So the
    ageing index came out biased down by exactly the oldest cohorts,
    with `restricted` reporting None, and the module docstring's "the
    last is open at 90+" asserted as a fact about the data rather than
    checked against it.
    What SHOULD happen to them - folded into 90+, selected as further
    bands, or refused - is a demographic ruling and is John's; it is
    BACKLOG 363 and deliberately not decided here. What this release
    fixes is the SILENCE, because a cohort that is present in the
    folder, counted in N_k, and absent from the index is the worst of
    the three outcomes whichever way the ruling goes.
    """
    wanted = set(_bands_from(*spec["ages"]))
    if "plus" in spec:
        wanted |= set(_bands_from(*spec["plus"]))
    sexes = spec["sexes"]

    out, unknown = [], set()
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
        age = int(d["age"])
        if age in wanted:
            out.append(lab)
        elif age > BAND_STARTS[-1]:
            unknown.add(age)
    if unknown and say is not None:
        say("[demography] NOTE: this folder carries age band(s) "
            + ", ".join(str(a) for a in sorted(unknown))
            + f", above the {BAND_STARTS[-1]}+ band this table ends "
            "at. They are NOT in this index, and they ARE in the "
            "reference population, so the index is computed over a "
            "younger group than the neighbourhood. See BACKLOG 363.")
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
            # BACKLOG 359, JOHN'S RULING: "fmt should not be accepted."
            # 't' IS f+m, so naming it alongside either counts those
            # people twice. The rule was written down at columns_for()
            # - "mixing it with either double counts" - and enforced
            # nowhere: 'fmt:0-14,65-' was accepted, gave 30 numerator
            # columns where 'fm:' gives 20, and the SUM came out at
            # exactly 2x the truth because t repeats f+m. Nothing
            # flagged it: every sex carried every band, so the
            # completeness grid saw a perfect side. The error message
            # even advertised multi-sex specs.
            # 't' ALONE stays fine - a t-only folder is ordinary.
            if "t" in head and ({"f", "m"} & set(head)):
                raise DemographyError(
                    f"{head!r} names 't' together with f or m, and 't' "
                    "IS f plus m - so those people would be counted "
                    "twice and the index would come out at about "
                    "double. Use 'fm:' for the two sexes separately, "
                    "or 't:' for the combined column, not both.")
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


def expected_bands(spec_side):
    """The band starts a side SHOULD cover.

    USES _bands_from, THE SAME FUNCTION columns_for USES. Claude first
    wrote this rule out a second time and the two disagreed - 0-17
    gave [0,1,5,10,15] here and [0,1,5,10] there, so the completeness
    check would have demanded a band the selector never picks. One
    rule written twice is how BACKLOG 272 happened three weeks ago.
    """
    want = set(_bands_from(*spec_side["ages"]))
    if spec_side.get("plus"):
        want |= set(_bands_from(*spec_side["plus"]))
    return sorted(want)


def _band_end(start):
    nxt = [b for b in BAND_STARTS if b > start]
    return (nxt[0] - 1) if nxt else None


def effective_range(spec_side):
    """What a requested range ACTUALLY covers, in whole bands.

    Asking for 0-17 selects ages 0 to 14; 15, 16 and 17 are dropped.
    Whole bands are the right rule for banded data, but the REQUESTED
    and EFFECTIVE definitions must be distinguished (BACKLOG 279,
    review finding 3).

    BACKLOG 346. THIS FUNCTION WAS DEFINED TWICE, forty lines apart,
    and Python kept whichever came last - so one of the two was dead
    and nothing said which. They were not identical in source: the
    dead one guarded the open-ended top band with an extra branch.
    Checked rather than assumed, over all 25,650 (lo, hi, plus)
    combinations the band table admits: ZERO differing results,
    because _band_end() already returns None for the last band start,
    which is all that branch computed. The simpler one is kept. The
    lesson is the one BACKLOG 272 and expected_bands() above already
    record - one rule, written once - and a second copy that happens
    to agree is still a second copy waiting to stop agreeing.
    """
    bands = expected_bands(spec_side)
    if not bands:
        return None
    lo, hi = spec_side.get("ages", (None, None))
    plus = spec_side.get("plus")

    # BACKLOG 360. A SIDE MAY BE TWO RANGES AND THIS REPORTED IT AS
    # ONE. The dependency numerator is "0-14 AND 65 and over"; with
    # `plus` set, this function forced hi = None and returned
    # covers = (0, None) - which reads as EVERY AGE, and every age is
    # also its own denominator's range. A demographer reading the plan
    # (it is attached to the manifest as man["plans"]) would conclude
    # the two halves overlap. Worse, forcing hi = None made `exact`
    # unconditionally True, which switched OFF the moved-boundary note
    # for the one index that uses `plus`: asking for "0-17,65-" lost
    # ages 15, 16 and 17 and still claimed to be exact.
    #
    # The columns selected were right all along - this was a reporting
    # fault, not an arithmetic one. `ranges` is now the honest answer
    # and `covers`/`asked` keep their old shape for the FIRST range,
    # so nothing that reads them breaks.
    main = [b for b in bands if plus is None or b < plus[0]]
    tail = [b for b in bands if plus is not None and b >= plus[0]]
    ranges = []
    if main:
        ranges.append({"asked": (lo, hi),
                       "covers": (main[0], _band_end(main[-1])),
                       "bands": main,
                       "exact": main[0] == lo
                       and (hi is None or _band_end(main[-1]) == hi)})
    if tail:
        ranges.append({"asked": (plus[0], plus[1]),
                       "covers": (tail[0], _band_end(tail[-1])),
                       "bands": tail,
                       "exact": tail[0] == plus[0]})
    first = ranges[0] if ranges else None
    top = _band_end(bands[-1])
    return {"asked": (lo, hi if not plus else None),
            "covers": (bands[0], top),
            "bands": bands,
            # EVERY range, each with its own asked/covers/exact.
            "ranges": ranges,
            # and `exact` is now true only when EVERY range is, so the
            # note fires for a dropped boundary in either half.
            "exact": bool(ranges) and all(r["exact"] for r in ranges)}


def plan(name, labels, year=None, num_spec=None,
         den_spec=None, allow_incomplete=False) -> dict:
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

    # NORMALISE THE YEAR, through the SAME helper machine 3 uses.
    # BACKLOG 355: this said `year = str(year)`, which is right for an
    # int and wrong for a float - str(2020.0) is "2020.0" and no label
    # equals that. The two machines then failed DIFFERENTLY on one
    # input: machine 3 silently summed every year in the folder,
    # machine 4 refused with the message below about malformed labels.
    # One normaliser, so there is nothing left to disagree about.
    from ..rasterfolder import normalise_year
    year = normalise_year(year)

    # BACKLOG 358. A YEAR THE DATA DOES NOT CARRY WAS BLAMED ON THE
    # FILENAMES. This check only ran when `year is None`, so asking
    # for 2030 on a 2020 folder fell through to pick_sex(), found no
    # cohort for that year, and raised "No columns here look like a
    # cohort ... Machine 4 needs labels of the form sex_age_year" -
    # about labels that are perfectly well formed. It sent the user to
    # check their naming convention instead of their year box.
    # `yrs` is computed six lines above and had the right answer all
    # along.
    if year is not None and yrs and year not in yrs:
        raise DemographyError(
            f"No cohort here carries the year {year}. These points "
            f"have {', '.join(yrs)}. An index is computed for ONE "
            "year, so name one of those - the labels themselves are "
            "fine.")
    sexes = pick_sex(labels, year)
    num = dict(num_spec or spec["numerator"])
    den = dict(den_spec or spec["denominator"])
    if num["sexes"] is None:
        num["sexes"] = sexes
    if den["sexes"] is None:
        den["sexes"] = sexes

    # `say=print` only on the numerator: the note is about the FOLDER,
    # so saying it twice per index would say it eight times for four
    # indices (BACKLOG 362).
    top = columns_for(num, labels, year, say=print)
    bot = columns_for(den, labels, year)

    # IS THE MEASURE ENTITLED TO ITS NAME? Having ONE matching column
    # was enough, so f_00 + f_65 over f_15 was published as a
    # "Dependency ratio". A deliberately restricted study is
    # legitimate - allow=True says so explicitly - but it must be
    # CHOSEN, not arrived at by absence (BACKLOG 279).
    # BACKLOG 346, external review of 1.51 (finding F4). THE CHECK USED
    # TO POOL. It gathered the band numbers of whatever columns were
    # selected, compared that SET against the bands it needed, and then
    # - separately - asked whether each sex appeared anywhere on the
    # side. Both sets can be complete while no pair is: reproduced on
    # the ageing index with f and m across every band except m_65, where
    # f supplied 65 to the pooled age set, m appeared in the other
    # bands, no gap was reported, and "People 65 and over per person
    # under 15" was published while men aged 65-69 were simply absent
    # from the numerator. The error is not loud: it biases the index by
    # roughly the size of one cohort of one sex, in the direction the
    # hole happens to lie, and nothing in the output says so.
    #
    # What is needed is the GRID - every (sex, band) the side claims to
    # cover - because that is what the sum actually ranges over. A
    # missing PAIR is now named as a pair, which is also the only form
    # a user can act on: "fetch m_65" is a instruction, "the numerator
    # is incomplete" is not.
    gaps = {}
    # BACKLOG 361. A FOLDER MISSING ONE SEX PASSED UNFLAGGED, because
    # the sexes a side "covers" is itself derived from what is PRESENT
    # (pick_sex), so the absence of a sex could never be a gap. A
    # women-only folder produced an "Ageing index", labelled "People 65
    # and over per person under 15", with restricted = None - nothing
    # saying the denominator was girls. That is 1.45.4's defect ("an
    # incomplete measure wore a complete measure's name") surviving in
    # the one dimension 346's grid cannot see, because 346 closed the
    # BAND dimension and took the sex set as given.
    #
    # JOHN'S RULING on user-entered specs - experienced users, do not
    # alter their choice - is what decides the remedy here: the index
    # is COMPUTED, not refused, and the restriction is WRITTEN DOWN.
    # That overrides nothing; it records what was done, which is the
    # same principle as every run saying which origin rule it used. A
    # 't'-only folder is NOT restricted: t is everybody.
    # KEPT OUT OF `gaps` DELIBERATELY: gaps is what REFUSES a run, and
    # the ruling is to compute and record, not refuse. `noted` is
    # recorded in the plan and printed; it never stops anything.
    noted = {}
    if set(sexes) in ({"f"}, {"m"}):
        noted["sexes"] = sorted({"f", "m"} - set(sexes))
    for side, want, have in (("numerator", num, top),
                             ("denominator", den, bot)):
        need = expected_bands(want)
        got = {(d["sex"], int(d["age"]))
               for d in (_split(c) for c in have) if d is not None}
        sexes_wanted = list(want["sexes"] or [])
        missing = [f"{sx}_{b:02d}" for sx in sexes_wanted
                   for b in need if (sx, b) not in got]
        if missing:
            gaps[side] = missing
    if gaps and not allow_incomplete:
        lines = [f"{spec['label']}: the data cannot support this "
                 "measure under its own name."]
        for where, missing in gaps.items():
            lines.append(f"  {where}: missing "
                         + ", ".join(str(m) for m in missing))
        lines.append(f"  (cohort labels for {year}; a side is complete "
                     "only when EVERY sex it covers carries EVERY band "
                     "it covers - a band present for one sex and absent "
                     "for the other is a hole, not a cohort.)")
        lines.append("What would be computed is a DIFFERENT quantity "
                     "wearing this one's label.")
        lines.append("Fetch the missing cohorts, choose an index the "
                     "data supports, or pass allow_incomplete=True to "
                     "say the restriction is deliberate - it is then "
                     "recorded in the plan.")
        raise DemographyError("\n".join(lines))
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
            "numerator": top, "denominator": bot,
            # WHAT WAS ASKED FOR AND WHAT IT COVERS. 0-17 selects
            # whole bands 0 to 14, and the three missing years must be
            # visible rather than inferred (review finding 3).
            "effective": {"numerator": effective_range(num),
                          "denominator": effective_range(den)},
            # A DELIBERATE RESTRICTION IS RECORDED, so a reader of the
            # output can see the measure is not the general one.
            # BACKLOG 361: `noted` joins it - a sex absent from the
            # whole folder restricts the measure just as much as a
            # missing band, and it is recorded for the same reason,
            # without refusing the run.
            "restricted": ({**noted, **gaps}
                           if (noted or gaps) else None)}


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
    # BACKLOG 364. A TILED RUN DID ALL THE WORK AND THEN DIED. `out_dir`
    # reaches run_folder through **kw, which sends machine 3 down its
    # TILED branch - and that branch sets man["tiles"], never
    # man["results"]. So the rasters loaded, the cells were built,
    # every neighbourhood was computed, the parquet tiles were written
    # - and then this function raised a bare KeyError: 'results',
    # having never computed the index. Reproduced: 40 rasters, 2 tiles
    # on disk, and tiles holding T_num_*/T_den_* with no index column
    # in them.
    # Refused UP FRONT instead, because a refusal after the expensive
    # part is the one kind that costs the user something. Machine 3's
    # own advice ("giving an output folder would tile it") does not
    # apply to machine 4 yet, and that is BACKLOG 365 rather than
    # something to half-do here.
    if kw.get("out_dir") is not None:
        raise DemographyError(
            "A demographic index cannot be run TILED yet: the index is "
            "computed from the whole result table, and a tiled run "
            "writes its parts to parquet without one. Drop out_dir to "
            "run it in memory, or compute the index yourself from the "
            "T_num_/T_den_ columns a tiled machine-3 run leaves. This "
            "is a missing capability, not a broken setting - see "
            "BACKLOG 365.")
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
    # SAY WHEN THE BOUNDARY MOVED. Asking for 0-17 and getting 0-14
    # is the right behaviour for banded data and the wrong thing to
    # discover in a footnote (review finding 3).
    for side, r in (p.get("effective") or {}).items():
        if r and not r["exact"]:
            a, c = r["asked"], r["covers"]
            say(f"  NOTE: {side} asked for "
                f"{a[0]}-{a[1] if a[1] is not None else ''} and covers "
                f"{c[0]}-{c[1] if c[1] is not None else ''} - whole "
                "bands only, so the boundary moved.")
    if p.get("restricted"):
        say("  NOTE: this is a RESTRICTED version of the measure - "
            + "; ".join(f"{k} missing {v}" for k, v
                        in p["restricted"].items()))
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
    # BACKLOG 364. A TILED RUN DID ALL THE WORK AND THEN DIED. `out_dir`
    # reaches run_folder through **kw, which sends machine 3 down its
    # TILED branch - and that branch sets man["tiles"], never
    # man["results"]. So the rasters loaded, the cells were built,
    # every neighbourhood was computed, the parquet tiles were written
    # - and then this function raised a bare KeyError: 'results',
    # having never computed the index. Reproduced: 40 rasters, 2 tiles
    # on disk, and tiles holding T_num_*/T_den_* with no index column
    # in them.
    # Refused UP FRONT instead, because a refusal after the expensive
    # part is the one kind that costs the user something. Machine 3's
    # own advice ("giving an output folder would tile it") does not
    # apply to machine 4 yet, and that is BACKLOG 365 rather than
    # something to half-do here.
    if kw.get("out_dir") is not None:
        raise DemographyError(
            "A demographic index cannot be run TILED yet: the index is "
            "computed from the whole result table, and a tiled run "
            "writes its parts to parquet without one. Drop out_dir to "
            "run it in memory, or compute the index yourself from the "
            "T_num_/T_den_ columns a tiled machine-3 run leaves. This "
            "is a missing capability, not a broken setting - see "
            "BACKLOG 365.")
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
                # BACKLOG 366. SAY THE UNITS. John's ruling is to keep
                # the bare ratio, and this changes no number - it says
                # which number it is. Conventionally a sex ratio is
                # men per 100 women and a child-woman ratio is children
                # per 1,000 women, so a column reading 0.97 will be
                # read as 1% by anyone who expects 97. The `about` text
                # implies per-one ("per woman", "per person of working
                # age") and never reaches the attribute table.
                out.append(f"  {c}: >>> {pl['label']} over the nearest "
                           f"{mm.group(1)} people. This is the answer; "
                           "the T_ and R_ columns are its parts. "
                           "PER ONE, not per 100 or per 1,000 - "
                           "multiply if you want the conventional "
                           "scale")
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
