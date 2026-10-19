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

RATES AND LIFE EXPECTANCY, v1.60.0 (BACKLOG 416). An age-sex folder
carries stock, not flow, so TFR, CBR, CDR and life expectancy cannot
be MEASURED here. They can be ESTIMATED, model-based: the nation's own
schedules (UN WPP 2024) give the age pattern, and the neighbourhood's
pyramid, read against the nation's, gives the level. That is
doors/vital.py; vital_plan() and apply_vital() below run it over the
same neighbourhoods as the indices, in the same traverse. Life
expectancy from 50, 30 and birth is computed on John's request and
NAMED UNRELIABLE - see vital.py for why.

WORLDPOP AGE BANDS ARE NOT ALL FIVE YEARS (John): 0 is under-one on
its own, 1 covers 1-4, then fives, and the last is open at 90+. Every
selector below works in BAND STARTS for that reason, never in
arithmetic on the age number.
"""

from __future__ import annotations

import re

import numpy as np


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

    top_band = BAND_STARTS[-1]
    # JOHN'S RULING, 8 October 2026 (BACKLOG 363): "fold into 90+ -
    # but note to user in output if found in the run."
    # FOLDED ONLY INTO A SIDE THAT ACTUALLY REACHES THE TOP BAND. A
    # folder's f_95 belongs in an ageing index's numerator, which is
    # 65+ and open-ended; it does NOT belong in a children's
    # numerator, and a fold that ignored that would quietly put
    # centenarians among the under-fives. So the test is whether this
    # SIDE wants the 90+ band, not whether the folder has one.
    fold_here = top_band in wanted
    out, unknown, folded = [], set(), set()
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
        elif age > top_band:
            unknown.add(age)
            if fold_here:
                out.append(lab)
                folded.add(age)
    if unknown and say is not None:
        bands = ", ".join(str(a) for a in sorted(unknown))
        if folded:
            # WHY THE NOTE IS NOT OPTIONAL. Folding is the right
            # answer and it still CHANGES WHAT 90+ MEANS in whatever
            # is published from the run: it is the folder's own top,
            # not WorldPop's. A reader comparing two studies has to be
            # able to find that out, and the only place they will look
            # is the run's own output.
            say("[demography] NOTE: this folder carries age band(s) "
                + bands + f", above the {top_band}+ band this table "
                f"ends at. They are FOLDED INTO the {top_band}+ band "
                "(John's ruling), so nobody is dropped and the "
                f"reference population matches the index - but "
                f"'{top_band}+' in this run means {top_band} and over "
                f"AS THIS FOLDER DEFINES IT, which is open above "
                + str(max(unknown)) + ". Say so wherever the figure "
                "is published.")
        else:
            say("[demography] NOTE: this folder carries age band(s) "
                + bands + f", above the {top_band}+ band this table "
                "ends at. This index does not reach the top band, so "
                "they are not part of it - which is correct here, and "
                "not the same as dropping them: a side that DOES "
                "reach the top band folds them in.")
    return out



def above_top_note(labels, specs, year=None):
    """One sentence about cohorts above the table's top band, or None.

    BACKLOG 363, JOHN'S RULING: fold them into 90+, and note it in the
    output when the run finds them.

    **WHY THIS IS NOT INSIDE columns_for.** The note is a fact about
    the FOLDER, and whether the cohorts end up folded is a fact about
    the INDEX - a side that reaches the top band absorbs them, a side
    that stops below it does not. columns_for sees one side at a time,
    so it can only ever say half of it: 362 wired the note to the
    numerator alone and a user override making the DENOMINATOR the
    open side folded silently. Asked here, where both sides are
    known, there is one message and it is the right one.
    `specs` is the sides, in order; only whether ANY of them reaches
    the top band matters.
    """
    top = BAND_STARTS[-1]
    unknown = set()
    for lab in labels:
        d = _split(lab)
        if d is None:
            continue
        if year is not None and d["year"] != str(year):
            continue
        if int(d["age"]) > top:
            unknown.add(int(d["age"]))
    if not unknown:
        return None
    bands = ", ".join(str(a) for a in sorted(unknown))
    folds = False
    for spec in specs:
        wanted = set(_bands_from(*spec["ages"]))
        if "plus" in spec:
            wanted |= set(_bands_from(*spec["plus"]))
        if top in wanted:
            folds = True
            break
    if folds:
        return (
            f"[demography] NOTE: this folder carries age band(s) {bands}, "
            f"above the {top}+ band this table ends at. They are FOLDED "
            f"INTO the {top}+ band (John's ruling), so nobody is dropped "
            "and the index covers the same people as the reference "
            f"population - but '{top}+' in this run means {top} and over "
            f"AS THIS FOLDER DEFINES IT, open above {max(unknown)}. Say "
            "so wherever the figure is published.")
    return (
        f"[demography] NOTE: this folder carries age band(s) {bands}, "
        f"above the {top}+ band this table ends at, and NEITHER SIDE of "
        "this index reaches the top band - so those people are in the "
        "reference population and not in the index. That is correct for "
        "a measure that stops below them, and worth knowing before the "
        "index is read as covering everybody.")


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

    # BOTH SIDES SPEAK, AND THE DUPLICATES ARE DROPPED.
    # 362 put `say=print` on the numerator alone, reasoning that the
    # note is about the FOLDER so saying it twice per index would say
    # it eight times for four indices. True - and it left a hole that
    # John's ruling (363) turns from cosmetic into substantive: the
    # numerator is the open-ended side in all four built-in indices,
    # but num_spec/den_spec are user-overridable, so an index whose
    # DENOMINATOR reaches the top band would fold cohorts into it and
    # say nothing. A fold that is not announced is the thing the
    # ruling exists to prevent.
    # Collected and de-duplicated instead: both sides folding gives
    # one line, which is the common case and the same volume 362
    # wanted; sides that differ give two, and both are then true.
    top = columns_for(num, labels, year)
    bot = columns_for(den, labels, year)
    _note = above_top_note(labels, (num, den), year)
    if _note:
        print(_note)

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


# ------------------------------------------- rates and life expectancy
VITAL_SEXES = {"both": "B", "women": "F", "men": "M"}


def vital_plan(labels, names, year=None, sex="both") -> dict:
    """Which columns the rates and life expectancies are read from.

    names: keys of vital.MEASURES. sex: 'both', 'women' or 'men' - the
    people the life tables and the CDR are for. TFR and CBR always use
    the women and the children of both sexes.
    Refuses, naming every missing (sex, band), rather than read a
    pyramid with a hole in it: a missing band is read as nobody alive
    at that age.
    """
    from . import vital as V
    names = list(names or [])
    bad = [n for n in names if n not in V.MEASURES]
    if bad:
        raise DemographyError(
            f"No such measure: {', '.join(bad)}. Available: "
            + ", ".join(V.MEASURES))
    if sex not in VITAL_SEXES:
        raise DemographyError(
            f"sex must be one of {', '.join(VITAL_SEXES)}; got {sex!r}.")
    yrs = years_in(labels)
    if year is None:
        if len(yrs) != 1:
            raise DemographyError(
                (f"These points carry {len(yrs)} years "
                 f"({', '.join(yrs)}). Rates are read for ONE year - "
                 "say which.") if yrs else
                "No columns here look like a cohort (sex_age_year).")
        year = yrs[0]
    from ..rasterfolder import normalise_year
    year = normalise_year(year)
    if year not in yrs:
        raise DemographyError(
            f"No cohort here carries the year {year}. These points "
            f"have {', '.join(yrs)}.")

    here = [d for d in (_split(c) for c in labels)
            if d and d["year"] == year]
    present = {(d["sex"], int(d["age"])) for d in here}
    if sex == "both":
        sexes = pick_sex(labels, year)
    else:
        sexes = ({"women": "f", "men": "m"}[sex],)
        if not any(sx == sexes[0] for sx, _a in present):
            raise DemographyError(
                f"Life tables for {sex} need the {sexes[0]}_ files, and "
                f"this folder has none for {year}.")
    oldest = max(a for _sx, a in present)
    top = max(b for b in V.BANDS if b <= min(oldest, V.BANDS[-1]))
    bands = [b for b in V.BANDS if b <= top]

    # the labels as they are spelled in the folder, not as rebuilt
    by_key = {(d["sex"], int(d["age"])): lab for lab, d in
              ((c, _split(c)) for c in labels)
              if d and d["year"] == year}

    def pick(sx_set, band):
        return [by_key[(sx, a)] for sx, a in sorted(present)
                if sx in sx_set and (a == band or (band == top and
                                                   a > top))]
    missing = [f"{sx}_{b:02d}" for sx in sexes for b in bands
               if (sx, b) not in present]
    if missing:
        raise DemographyError(
            "Rates and life expectancy read the WHOLE pyramid, and this "
            f"one has holes for {year}: missing " + ", ".join(missing)
            + ". A missing band would read as nobody alive at that age. "
            "Fetch the missing files (5a lists them).")
    plan_ = {"names": names, "year": year, "sexes": list(sexes),
             "sex": sex, "sexcode": VITAL_SEXES[sex] if sex != "both"
             else "B", "top": top, "bands": bands,
             "band_cols": {b: pick(sexes, b) for b in bands},
             "folded": sorted({a for _sx, a in present if a > top})}
    if any(n in V.NEEDS_WOMEN for n in names):
        gone = [f"f_{a:02d}" for a in V.FERT if ("f", a) not in present]
        if gone:
            raise DemographyError(
                "TFR and CBR are read from the women and the children "
                "under five, so they need the women's files (f_) for "
                f"ages 10-54 - missing for {year}: " + ", ".join(gone)
                + ". A folder of t_ (both sexes) files cannot say how "
                "many of the people are women.")
        route = _child_route(present, year)
        plan_["women_cols"] = {a: pick(("f",), a) for a in V.FERT}
        plan_["child_cols"] = pick(route, 0) + pick(route, 1)
        plan_["child_route"] = list(route)
    return plan_


def _child_route(present, year):
    """WHICH CHILDREN UNDER FIVE TFR AND CBR COUNT - one complete route.

    v1.60.2, external review of 1.60.1 (P1). This summed whatever age-0
    and age-1 files happened to be present, of the sexes pick_sex chose,
    so a folder missing m_00 counted girls under five and boys aged 1-4
    without a word, and a folder of women's files alone counted girls.
    Because each neighbourhood's children are read against the nation's
    children counted the same way, most of that cancelled - but it was
    silent, and it need not have cancelled. Now: girls and boys, or the
    both-sexes files, each COMPLETE for ages 0 and 1; one sex alone only
    when the folder has no files at all for the other (girls against
    the nation's girls is then a fair ratio, and the run says so).
    Anything else is refused by name.
    """
    sexes = {sx for sx, _a in present}
    routes = [r for r in (("f", "m"), ("t",)) if set(r) <= sexes]
    if not routes:
        routes = [(sx,) for sx in ("f", "m") if sx in sexes]
    holes = {}
    for r in routes:
        holes[r] = [f"{sx}_{a:02d}" for sx in r for a in (0, 1)
                    if (sx, a) not in present]
        if not holes[r]:
            return r
    gone = sorted({h for hs in holes.values() for h in hs})
    raise DemographyError(
        "TFR and CBR count the children under five - ages 0 and 1-4 - "
        f"and this folder's are incomplete for {year}: missing "
        + ", ".join(gone) + ". Counting the ones that happen to be there "
        "would read a missing file as no children. Fetch the missing "
        "files (5a lists them).")


def vital_groups(vplan) -> dict:
    """compose= for run_folder: one group per band, per fertility band
    of the women, and the children."""
    out = {f"vb_{b}": cols for b, cols in vplan["band_cols"].items()}
    if "women_cols" in vplan:
        out.update({f"vw_{a}": c for a, c in vplan["women_cols"].items()})
        out["vc"] = list(vplan["child_cols"])
    return out


def vital_references(vplan, pts):
    """{iso3: national schedules + the folder's own national pyramid}.

    THE NATION'S PYRAMID IS THE FOLDER'S OWN TOTAL for that country,
    not WPP's: WorldPop is aligned to WPP's totals, and reading the
    neighbourhood against the same source's national pyramid cancels
    the source's own habits (age heaping, old ages overstated) wherever
    they are national. A folder clipped to part of a country is read
    against that part - which the run says.
    """
    from . import vital as V
    if "iso3" not in pts.columns:
        raise DemographyError(
            "Rates and life expectancy are read against each point's "
            "NATION, and these points carry no country code - WorldPop "
            "file names start with one (bdi_f_00_2020...).")
    groups = vital_groups(vplan)
    refs, absent = {}, []
    for iso, part in pts.groupby("iso3", observed=True):
        iso = str(iso)
        if not iso:
            continue
        tot = {g: float(part[c].to_numpy(float).sum()) for g, c in
               groups.items()}
        try:
            nat = V.national(iso, vplan["year"], vplan["sexcode"],
                             top=vplan["top"])
        except V.VitalError:
            absent.append(iso.upper())
            continue
        i60 = vplan["bands"].index(60) if 60 in vplan["bands"] else None
        P = np.array([tot[f"vb_{b}"] for b in vplan["bands"]])
        refs[iso] = {
            "nat": nat, "P": P,
            # v1.60.2: how much of the country this folder holds,
            # against WPP's national population of the same sex
            "coverage": (float(P.sum() / nat["pop"]) if nat["pop"] > 0
                         else np.nan),
            "e60": (float(nat["L"][i60:].sum() / nat["l"][i60])
                    if i60 is not None else np.nan)}
        if "women_cols" in vplan:
            refs[iso]["C"] = tot["vc"]
            refs[iso]["W"] = np.array([tot[f"vw_{a}"] for a in V.FERT])
    return refs, absent


#: Whose nation a neighbourhood's people are read against (v1.61.0).
#: 'own'  - every person their own country's: a neighbourhood across a
#:          border pools both, each side against its own nation. The
#:          default (John, 19 October).
#: 'cell' - the whole neighbourhood against the country of its cell:
#:          the rule to 1.60.3.
VITAL_REFERENCES = {"own": "each person's own country",
                    "cell": "the country of the neighbourhood's cell"}


def vital_own_groups(vplan, refs) -> dict:
    """compose= specs for 'own': each POINT carries its own country's
    coefficients, so the neighbourhood sums ARE the pooled estimators
    (vital.life_expectancy_own, fertility_own, crude_death_rate_own).

    Within one country these reduce exactly to the 'cell' arithmetic:
      vo_s<a>  people aged a                     (coef 1)
      vo_x<a>  people aged b>=a x (P_a/P_b)(L_b/l_a), their nation's
      vo_c     children 0-4                      (coef 1)
      vo_e     women x f_x, their nation's - births a year predicted
      vo_y     the same x C_nat/E_nat - children predicted
      vo_z     the same x TFR_nat
      vo_n     everybody in the pyramid          (coef 1)
      vo_d0    people below 60 x m_b; vo_d60 the same from 60
      vo_p60   people aged 60+                   (coef 1)
      vo_m<b>  people aged 60+ x m_b of their nation, b = 60 ... top
      vo_r60   people aged 60 x e60 of their nation
    A country with no national table carries zeros: its people are
    left out of every sum rather than read against somebody else's.
    """
    from . import vital as V
    bands = vplan["bands"]
    bc = vplan["band_cols"]
    names = vplan["names"]
    starts = sorted({V.MEASURES[n]["start"] for n in names
                     if V.MEASURES[n]["start"] is not None
                     and V.MEASURES[n]["start"] in bands})
    cdr = "crude_death_rate" in names and 60 in bands
    if cdr and 60 not in starts:
        starts.append(60)

    def cols_of(bs):
        return [c for b in bs for c in bc[b]]

    def band_of(bs):
        return [b for b in bs for _c in bc[b]]

    def spec(bs, per_country):
        """{"cols", "by", "coef"}: per_country(ref) -> {band: coef}."""
        cols, which = cols_of(bs), band_of(bs)
        coef = {}
        for iso, ref in refs.items():
            per = per_country(ref)
            coef[iso] = [float(per.get(b, 0.0)) for b in which]
        return {"cols": cols, "by": "iso3", "coef": coef}

    def ones(_ref):
        return {b: 1.0 for b in bands}

    out = {}
    for a in starts:
        ia = bands.index(a)
        out[f"vo_s{a}"] = spec([a], ones)

        def x_coef(ref, ia=ia):
            nat, P = ref["nat"], ref["P"]
            got = {}
            for j in range(ia, len(bands)):
                if P[j] > 0 and nat["l"][ia] > 0:
                    got[bands[j]] = (P[ia] / P[j]) * nat["L"][j] \
                        / nat["l"][ia]
            return got
        out[f"vo_x{a}"] = spec(bands[ia:], x_coef)
    if any(n in V.NEEDS_WOMEN for n in names):
        wc = vplan["women_cols"]
        fert = [a for a in V.FERT]

        def wspec(scale):
            cols = [c for a in fert for c in wc[a]]
            which = [a for a in fert for _c in wc[a]]
            coef = {}
            for iso, ref in refs.items():
                nat = ref["nat"]
                f = dict(zip(V.FERT, nat["f"]))
                s = scale(ref)
                coef[iso] = [float(f[a] * s) for a in which]
            return {"cols": cols, "by": "iso3", "coef": coef}

        def r_of(ref):
            e_nat = float((np.asarray(ref["W"], float)
                           * np.asarray(ref["nat"]["f"], float)).sum())
            return ref["C"] / e_nat if e_nat > 0 else 0.0
        out["vo_c"] = {"cols": list(vplan["child_cols"]), "by": "iso3",
                       "coef": {iso: [1.0] * len(vplan["child_cols"])
                                for iso in refs}}
        out["vo_e"] = wspec(lambda ref: 1.0)
        out["vo_y"] = wspec(r_of)
        out["vo_z"] = wspec(lambda ref: ref["nat"]["tfr"])
    if cdr:
        i60 = bands.index(60)
        old = bands[i60:]

        def m_of(ref):
            return dict(zip(bands, ref["nat"]["m"]))
        out["vo_n"] = spec(bands, ones)
        out["vo_d0"] = spec(bands[:i60], m_of)
        out["vo_d60"] = spec(old, m_of)
        out["vo_p60"] = spec(old, ones)
        for b in old:
            out[f"vo_m{b}"] = spec(
                old, lambda ref, b=b: {o: m_of(ref)[b] for o in old})
        out["vo_r60"] = spec([60], lambda ref: {60: ref["e60"]})
    return out


def apply_vital_own(frame, k_values, vplan):
    """The rates and life expectancies from the 'own' sums, in place;
    the sums dropped after. The 'own' twin of apply_vital."""
    from . import vital as V
    bands = vplan["bands"]
    names = vplan["names"]

    def T(g, k):
        return frame[f"T_{g}_{k}"].to_numpy(float)
    for k in k_values:
        for n in names:
            a = V.MEASURES[n]["start"]
            if a is not None and a in bands:
                frame[f"{V.MEASURES[n]['code']}_{k}"] = \
                    V.life_expectancy_own(T(f"vo_x{a}", k), T(f"vo_s{a}", k))
        if any(n in V.NEEDS_WOMEN for n in names):
            tfr, cbr = V.fertility_own(T("vo_c", k), T("vo_e", k),
                                       T("vo_y", k), T("vo_z", k),
                                       frame[f"N_{k}"].to_numpy(float))
            if "total_fertility_rate" in names:
                frame[f"TFR_{k}"] = tfr
            if "crude_birth_rate" in names:
                frame[f"CBR_{k}"] = cbr
        if "crude_death_rate" in names and 60 in bands:
            i60 = bands.index(60)
            old = bands[i60:]
            widths = [b2 - b1 for b1, b2 in zip(old, old[1:])] + [None]
            s60 = T("vo_s60", k)
            with np.errstate(divide="ignore", invalid="ignore"):
                e60 = T("vo_x60", k) / s60
                e60_ref = T("vo_r60", k) / s60
            frame[f"CDR_{k}"] = V.crude_death_rate_own(
                T("vo_d0", k), T("vo_d60", k),
                np.column_stack([T(f"vo_m{b}", k) for b in old]),
                T("vo_p60", k), T("vo_n", k), e60, e60_ref, widths)
    machinery = [c for c in frame.columns
                 if re.match(r"^[TR]_vo_[a-z0-9]+_\d+$", c)
                 or re.match(r"^vo_[a-z0-9]+_local$", c)]
    frame.drop(columns=machinery, inplace=True)
    return frame


class CellCountries:
    """Which country each result cell belongs to.

    THE RESULT TABLE DOES NOT CARRY ONE: points become cells, and the
    cell table keeps no country code (build_cells' label_col would put
    it in CellId, which must stay unique). So the points' own codes are
    kept - three small arrays, not the folder - and each cell takes the
    country of the point nearest its centre. A cell straddling a border
    therefore takes the country holding its middle, which is a rule,
    stated, rather than a guess.
    """

    def __init__(self, lon, lat, iso, crs, epsg):
        from pyproj import Transformer
        from scipy.spatial import cKDTree
        tr = Transformer.from_crs(crs or "EPSG:4326", f"EPSG:{epsg}",
                                  always_xy=True)
        x, y = tr.transform(np.asarray(lon, float), np.asarray(lat, float))
        self.iso = np.asarray(iso).astype(str)
        self.tree = cKDTree(np.column_stack([x, y]))

    def __call__(self, frame):
        xy = frame[["EastWest", "NorthSouth"]].to_numpy(float)
        _d, idx = self.tree.query(xy)
        return self.iso[idx]


def apply_vital(frame, k_values, vplan, refs, countries=None):
    """Add the rates and life expectancies to a result frame, in place,
    and drop the band counts they were read from. THE ONE ARITHMETIC,
    for the in-memory run and for each tile of a tiled one.

    countries: a CellCountries, or None when the folder holds one
    country (every cell is then that country's)."""
    from . import vital as V
    bands = vplan["bands"]
    names = vplan["names"]
    if "iso3" in frame.columns:
        iso = frame["iso3"].astype(str).to_numpy()
    elif countries is not None:
        iso = countries(frame)
    elif len(refs) == 1:
        iso = np.array([next(iter(refs))] * len(frame))
    else:
        iso = np.array([""] * len(frame))
    for k in k_values:
        S = np.column_stack([frame[f"T_vb_{b}_{k}"].to_numpy(float)
                             for b in bands])
        out = {n: np.full(len(frame), np.nan) for n in names}
        e60_all = np.full(len(frame), np.nan)
        for code in np.unique(iso):
            ref = refs.get(code)
            if ref is None:
                continue
            rows = iso == code
            nat = ref["nat"]
            for n in names:
                start = V.MEASURES[n]["start"]
                if start is not None and start in bands:
                    out[n][rows] = V.life_expectancy(
                        S[rows], ref["P"], nat["l"], nat["L"],
                        bands.index(start))
            if any(n in V.NEEDS_LE60 for n in names) and 60 in bands:
                e60 = V.life_expectancy(S[rows], ref["P"], nat["l"],
                                        nat["L"], bands.index(60))
                e60_all[rows] = e60
                if "crude_death_rate" in names:
                    out["crude_death_rate"][rows] = V.crude_death_rate(
                        S[rows], S[rows].sum(axis=1), nat, e60,
                        ref["e60"])
            if any(n in V.NEEDS_WOMEN for n in names):
                C = frame[f"T_vc_{k}"].to_numpy(float)[rows]
                W = np.column_stack([frame[f"T_vw_{a}_{k}"].to_numpy(
                    float)[rows] for a in V.FERT])
                N = frame[f"N_{k}"].to_numpy(float)[rows]
                tfr, cbr = V.fertility(C, W, N, nat["f"], nat["tfr"],
                                       ref["C"], ref["W"])
                if "total_fertility_rate" in names:
                    out["total_fertility_rate"][rows] = tfr
                if "crude_birth_rate" in names:
                    out["crude_birth_rate"][rows] = cbr
        for n in names:
            frame[f"{V.MEASURES[n]['code']}_{k}"] = out[n]
    machinery = [c for c in frame.columns
                 if re.match(r"^[TR]_v(b|w)_\d+_\d+$", c)
                 or re.match(r"^[TR]_vc_\d+$", c)
                 or re.match(r"^v(b|w)_\d+_local$|^vc_local$", c)]
    frame.drop(columns=machinery, inplace=True)
    return frame


# ------------------------------------------------------------- running

def index_triples(k_values, out_name, num_group="num", den_group="den"):
    """(result column, numerator column, denominator column) per k.

    BACKLOG 365, v1.53.4. THE COLUMN NAMES IN ONE PLACE. run_index and
    run_indices named these differently and each built them inline -
    `T_num_{k}` against `T_{code}_num_{k}` - so there were already TWO
    copies of the naming and the arithmetic before this release, and
    giving each of them a tiled branch would have made FOUR. That is
    354 (four copies of the measurement rule), 368 (two copies of the
    hint rendering) and 377 (seven copies of the k reader) arriving a
    fourth time, and the only reason it did not is that the count was
    noticed before the code was written.
    """
    return [(f"{out_name}_{k}", f"T_{num_group}_{k}", f"T_{den_group}_{k}")
            for k in k_values]


def apply_index(frame, triples):
    """Add the index columns to a result frame, in place. Returns it.

    THE ONE ARITHMETIC, used by the in-memory branch and by the
    per-tile post-pass, so a tiled continental index and an in-memory
    one agree BY CONSTRUCTION rather than by a test that compares
    them. A denominator of zero gives NaN: nobody in the
    neighbourhood to divide by is a missing answer, not a zero one.
    """
    import numpy as _np
    for out, top, bot in triples:
        if top in frame.columns and bot in frame.columns:
            b = frame[bot].to_numpy(dtype=float)
            # np.where EVALUATES BOTH BRANCHES, so the division runs
            # on the zero denominators too and numpy warns about a
            # value that is then thrown away. Harmless and noisy: a
            # continental run with empty neighbourhoods would print
            # "invalid value encountered in divide" into the user's
            # log once per index, which teaches them to distrust the
            # output for no reason.
            with _np.errstate(divide="ignore", invalid="ignore"):
                frame[out] = _np.where(
                    b > 0, frame[top].to_numpy(dtype=float) / b, _np.nan)
    return frame


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
    # BACKLOG 365, v1.53.4. TILED NOW WORKS - and 364's refusal is
    # gone rather than relaxed. What 364 found was that `out_dir`
    # reached run_folder through **kw, sent machine 3 down its tiled
    # branch, and left this function raising a bare KeyError:
    # 'results' after every neighbourhood had been computed. It
    # refused up front instead, which was the honest state and not a
    # capability.
    # The capability turns out to be small, which is why it is worth
    # having: the index is T_num/T_den PER ORIGIN, and a tiled
    # machine-3 run already writes both columns into every tile -
    # measured, 9 tiles, both halves present in all of them. So the
    # index is a per-tile post-pass with memory bounded at ONE TILE
    # rather than at a continent, which is the whole point of tiling.
    # bigrun.map_tiles does the file discipline; apply_index does the
    # arithmetic, the same call the in-memory branch makes.
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

    triples = index_triples(k_values, name)
    if kw.get("out_dir") is not None:
        from ..bigrun import map_tiles
        map_tiles(kw["out_dir"], lambda df: apply_index(df, triples),
                  what=f"{name} index")
        say(f"The {name} index was added to each of the "
            f"{man['tiles']} tiles in {kw['out_dir']} - column"
            + ("s " if len(k_values) > 1 else " ")
            + ", ".join(o for o, _t, _b in triples)
            + ". Read it back with equipop.bigrun.load_tiled; there is "
            "no single result table for a tiled run, which is what "
            "lets it be bigger than memory.")
    else:
        apply_index(man["results"], triples)
    man["plan"] = p
    say("The index is a ratio of two counts over the SAME "
        "neighbourhood, so it inherits nothing from any administrative "
        "unit - which is the reason to compute it this way.")
    return man


def run_indices(folders, names, *, k_values, unit_size=1000.0, year=None,
                epsg=None, overrides=None, channel=None, vital=None,
                vital_sex="both", vital_reference="own", points=None,
                points_crs=None, **kw):
    """SEVERAL indices in ONE traverse of the data.

    John's preference, and it matters at continental scale: loading
    120 rasters, projecting eleven million points and building the
    tree is most of the cost, and it is identical whichever index you
    want. Four indices one at a time is four of those; this is one.

    overrides: {index_name: {"numerator": [...], "denominator": [...]}}
    so a door can offer the suggested columns and let them be edited.
    vital: keys of vital.MEASURES - life expectancy, TFR, CBR, CDR,
    read from the pyramid against the nation's (v1.60.0), over the
    SAME neighbourhoods in the same traverse. vital_sex: 'both',
    'women' or 'men', for the life tables and the CDR.
    points, points_crs: the point table machine 3 wrote from such a
    folder, used INSTEAD of it (folders is then ignored) - John, 18
    October: the curated points should do as well as the rasters.
    vital_reference: 'own' (each person against their own country, the
    default since 1.61.0) or 'cell' (the neighbourhood against its
    cell's country) - VITAL_REFERENCES.
    """
    import contextlib
    import io

    import numpy as np

    from .continental import check_folders, run_folder
    from ..rasterfolder import load_source

    say = channel.info if channel is not None else print
    # BACKLOG 365, v1.53.4. TILED NOW WORKS, and this is the path
    # that matters most for it: SEVERAL indices in ONE traverse was
    # already John's preference at continental scale, and every one of
    # them is a ratio of two columns the tiles already hold. So all of
    # them are added in a SINGLE read and write per tile, not one pass
    # per index - reading eleven million rows four times to add four
    # columns would undo the reason for tiling.
    if points is None:
        check_folders(folders)  # before we peek at the labels
    names = list(names or [])
    vital = list(vital or [])
    if vital_reference not in VITAL_REFERENCES:
        raise DemographyError(
            f"vital_reference must be one of "
            f"{', '.join(VITAL_REFERENCES)}; got {vital_reference!r}.")
    if not names and not vital:
        from .vital import MEASURES
        raise DemographyError(
            "Nothing chosen. Indices: " + ", ".join(sorted(INDICES))
            + ". Rates and life expectancy: " + ", ".join(MEASURES))

    with contextlib.redirect_stdout(io.StringIO()):
        pts, _m = load_source(folders, points, points_crs,
                              **{k: v for k, v in kw.items()
                                 if k in ("convention", "labels",
                                          "pattern")})
    labels = [c for c in pts.columns if c not in ("lon", "lat", "iso3")]
    vplan = refs = where = None
    if vital:
        # BEFORE the points are let go: the nation's pyramid is the
        # folder's own total per country, and with several countries
        # each cell must learn which one it is in.
        vplan = vital_plan(labels, vital, year=year, sex=vital_sex)
        refs, absent = vital_references(vplan, pts)
        vplan["rule"] = vital_reference
        if vital_reference == "cell" and pts["iso3"].nunique() > 1:
            where = (pts["lon"].to_numpy(), pts["lat"].to_numpy(),
                     pts["iso3"].astype(str).to_numpy())
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

    if vital:
        vg = (vital_own_groups(vplan, refs) if vital_reference == "own"
              else vital_groups(vplan))
        compose.update(vg)
        groups += list(vg)
        _say_vital(say, vplan, refs, absent, k_values)
        if year is None:
            year = vplan["year"]

    sexes = (plans[names[0]]["sexes"] if names
             else list(pick_sex(labels, vplan["year"])))
    man = run_folder(folders, k_values=k_values, unit_size=unit_size,
                     epsg=epsg,
                     weight="sexes" if sexes != ["t"] else "total",
                     # PASS THE YEAR DOWN. Without it the reference
                     # population is summed across EVERY year in the
                     # folder, so analysing 2020 changes once 2030 has
                     # been downloaded (BACKLOG 273).
                     year=year,
                     compose=compose, groups=groups, channel=channel,
                     points=points, points_crs=points_crs, **kw)

    triples = []
    for nm in names:
        code = INDICES[nm]["code"]
        triples += index_triples(k_values, code,
                                 f"{code}_num", f"{code}_den")
    countries = None
    if where is not None:
        countries = CellCountries(*where, man.get("crs"),
                                  (man.get("projection") or {})["epsg"])

    def finish(df):
        apply_index(df, triples)
        if vital and vital_reference == "own":
            apply_vital_own(df, k_values, vplan)
        elif vital:
            apply_vital(df, k_values, vplan, refs, countries)
        return df

    if kw.get("out_dir") is not None:
        from ..bigrun import map_tiles
        tman = map_tiles(kw["out_dir"], finish,
                         what=f"{len(triples)} index and "
                              f"{len(vital) * len(k_values)} rate "
                              "column(s)")
        columns = list(tman.get("columns") or [])
        say(f"{len(triples)} index column(s) added to each of the "
            f"{man['tiles']} tiles in {kw['out_dir']}: "
            + ", ".join(o for o, _t, _b in triples)
            + ". Read it back with equipop.bigrun.load_tiled - a tiled "
            "run has no single result table, which is what lets it be "
            "bigger than memory.")
    else:
        finish(man["results"])
        columns = list(man["results"].columns)
    man["plans"] = plans
    if vital:
        from .vital import citation
        man["vital"] = {k: v for k, v in vplan.items()
                        if k in ("names", "year", "sex", "sexes", "top",
                                 "bands", "folded", "rule")}
        man["vital"]["reference"] = citation()
        man["vital"]["countries"] = sorted(c.upper() for c in refs)
        # the share of WPP's national population each country's folder
        # total is - what the 'nation' was, in the record
        man["vital"]["national_coverage"] = {
            c.upper(): round(r["coverage"], 4) for c, r in refs.items()}
    say("")
    say("WHAT THE FIELDS MEAN:")
    for line in explain_fields(columns, plans,
                               (man.get("projection") or {}).get("epsg"),
                               vital=vplan):
        say(line)
    say("")
    if names:
        say(f"{len(names)} {'index' if len(names) == 1 else 'indices'} "
            "over the SAME neighbourhoods, in one traverse - each is a "
            "ratio of two counts among the k nearest people, so none of "
            "them inherits anything from an administrative unit.")
    if vital:
        say("The rates and life expectancies are MODEL-BASED: read from "
            "each neighbourhood's age pyramid against its nation's, with "
            "the nation's age patterns from UN WPP 2024. Use them as "
            "what they are - predictors - and say so where they are "
            "published.")
    return man


def _say_vital(say, vplan, refs, absent, k_values):
    """What the rates and life expectancies are about to be read from."""
    from . import vital as V
    sx = {"both": "both sexes", "women": "women", "men": "men"}[
        vplan["sex"]]
    rule = vplan.get("rule", "cell")
    say(f"Rates and life expectancy, {vplan['year']} - from each "
        f"neighbourhood's age pyramid ({sx}, bands 0 to "
        f"{vplan['top']}+), read against "
        + ("EACH PERSON'S OWN NATION - a neighbourhood across a border "
           "pools both sides, each against its own country:"
           if rule == "own" else
           "the nation of the neighbourhood's cell:"))
    for n in vplan["names"]:
        mm = V.MEASURES[n]
        say(f"   {mm['code']:5s} {mm['label']}")
    if vplan["folded"]:
        say(f"   NOTE: age band(s) {', '.join(map(str, vplan['folded']))} "
            f"are folded into {vplan['top']}+.")
    route = vplan.get("child_route")
    if route in (["f"], ["m"]):
        who = "girls" if route == ["f"] else "boys"
        say(f"   NOTE: the children under five are counted from the "
            f"{who} alone - the folder holds no files for the other sex. "
            f"They are read against the nation's {who}, so the ratio "
            "holds as long as the sex ratio at birth is the nation's.")
    flagged = [V.MEASURES[n]["code"] for n in vplan["names"]
               if not V.MEASURES[n]["reliable"]]
    if flagged:
        say(f"   {', '.join(flagged)}: UNRELIABLE, computed because they "
            "were asked for. Read from below 60, a neighbourhood growing "
            "faster than the nation, or drawing young migrants, reads as "
            "one with different mortality. Use them as predictors only.")
    if any(V.MEASURES[n]["start"] is not None for n in vplan["names"]) \
            and min(k_values) < V.LE_K_FLOOR:
        say(f"   NOTE: k = {min(k_values):,} is below {V.LE_K_FLOOR:,}. "
            "A life expectancy read from so few people is noisy - the "
            "85-89 and 90+ bands then hold a handful each. 5,000 is the "
            "usual floor for small-area life expectancy.")
    for iso, ref in sorted(refs.items())[:8]:
        nat = ref["nat"]
        bits = []
        if 60 in vplan["bands"]:
            bits.append(f"e60 {ref['e60']:.1f}")
        bits.append(f"e0 {nat['L'].sum():.1f}")
        bits.append(f"TFR {nat['tfr']:.2f}")
        say(f"   national reference, {iso.upper()}: " + ", ".join(bits)
            + f" ({int(ref['P'].sum()):,} people in this folder)")
    if len(refs) > 8:
        say(f"   ... and {len(refs) - 8} more countries")
    # THE NATION IS THE FOLDER'S OWN TOTAL (v1.60.2, John's choice of
    # the review's options): a folder clipped to part of a country
    # reads that part as the nation, silently. WorldPop's totals are
    # matched to the UN's, so a whole country holds about WPP's
    # population; well short of it, the run says so.
    short = sorted((r["coverage"], iso) for iso, r in refs.items()
                   if r["coverage"] < V.WHOLE_COUNTRY)
    if short:
        say("   WARNING: NOT THE WHOLE COUNTRY? " + "; ".join(
            f"{iso.upper()} holds {cov:.0%} of WPP's {vplan['year']} "
            f"population" for cov, iso in short[:8])
            + (f"; and {len(short) - 8} more" if len(short) > 8 else "")
            + ". Each neighbourhood is read against the folder's own "
            "total for its country, so a folder holding part of a "
            "country reads that part as the nation - its rates come "
            "out relative to the region, not the country. Give the "
            "whole country (5a fetches it) for national comparisons.")
    if absent:
        say(f"   NOTE: no national life table for {', '.join(absent)} - "
            "those points are left empty.")
    say(f"   Reference: {V.citation()}")


# ------------------------------------------------------ what it means
def explain_fields(columns, plans=None, epsg=None, vital=None):
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
        # <code>_<k>  - a rate or life expectancy (v1.60.0)
        if vital:
            from .vital import MEASURES
            hit = None
            for nm in vital["names"]:
                mm = MEASURES[nm]
                mk = re.match(rf"^{mm['code']}_(\d+)$", c)
                if mk:
                    hit = (mm, mk.group(1))
                    break
            if hit:
                mm, k = hit
                out.append(f"  {c}: >>> "
                           + ("UNRELIABLE - " if not mm["reliable"]
                              else "")
                           + f"{mm['label']} over the nearest {k} "
                           f"people: {mm['about']}. MODEL-BASED, read "
                           "from the age pyramid against "
                           + ("each person's own nation"
                              if vital.get("rule", "cell") == "own"
                              else "the nation of the cell"))
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
