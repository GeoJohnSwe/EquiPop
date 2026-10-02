# -*- coding: utf-8 -*-
"""
fields.py - the names a run will produce, and what to do when the
target cannot hold them.

Every door needs these three before the engines start:

  predict_result_fields  what columns this run WILL create
  shorten_names          collision-free short forms, when asked for
  refuse_short_target    stop now, with the fix, if they will not fit

ArcGIS needs them to refuse a shapefile target BEFORE the
computation rather than after minutes of it (field finding A4).
QGIS needs them for the same reason and for one more: a Processing
algorithm must DECLARE its output columns before it runs.

The ten-character limit is not an ArcGIS quirk. It belongs to the
dBASE table inside a shapefile, so it follows the shapefile into
QGIS - where a GeoPackage plays the roomy role a file geodatabase
plays in Pro. Hence the container argument: the rule is shared, only
the name of the recommended alternative changes.
"""


def safe_field_name(name) -> str:
    """A field name every door will accept."""
    out = "".join(ch if ch.isalnum() else "_" for ch in str(name))
    return (out[:60] or "X")


def _fmt_num(v) -> str:
    """BACKLOG 337. THE PREDICTION AND THE ENGINE NOW USE ONE
    FORMATTER. This was `str(int(f)) if f == int(f) else str(f)` while
    the engine used `f"{x:g}"`, so for r(1000000) this promised
    N_r1000000 and the engine made N_r1e+06 - and the docstring below
    claims this function is validated against the real dispatch. It
    was not, for radii of that shape."""
    from equipop.labels import numeric_tag
    return numeric_tag(v)


def predict_result_fields(engine, k_text, r_text, tau_text,
                          treat_names, value_fields, stats_wanted,
                          decaying, efforting):
    """The columns a run WILL produce - validated against the real
    dispatch in the simulator suite, so this stays a prediction and
    does not drift into a guess."""
    from equipop.stats import stat_prefix
    ks = [t for t in (k_text or "").split()]
    rs = [_fmt_num(t) for t in (r_text or "").split()]
    taus = [_fmt_num(t) for t in (tau_text or "").split()]
    names = []
    if engine == "counts":
        sufs = [k for k in ks] + [f"r{r}" for r in rs]
        if efforting:
            sufs = [k for k in ks] + [f"tau{t}" for t in taus]
            names += [f"Rounds_{k}" for k in ks]
        for suf in sufs:
            names.append(f"N_{suf}")
            for f in treat_names:
                names += [f"T_{f}_{suf}", f"R_{f}_{suf}"]
        names += [f"Dist_{k}" for k in ks]
        if decaying:
            # BACKLOG 185: one decayed total per k and per radius, on
            # the SAME suffixes as the plain counts - not a single
            # unbounded ND_inf. The decayed neighbourhood is the plain
            # neighbourhood, so its columns follow the plain ones.
            for suf in sufs:
                names.append(f"ND_{suf}")
                for f in treat_names:
                    names += [f"TD_{f}_{suf}", f"RD_{f}_{suf}"]
    else:
        sufs = [k for k in ks] + [f"r{r}" for r in rs]
        names += [f"N_{s}" for s in sufs] + ["N_local"]
        names += [f"Dist_{k}" for k in ks]
        for f in value_fields:
            for s in sufs:
                names.append(f"Nv_{f}_{s}")
                for st in stats_wanted:
                    names.append(f"{stat_prefix(st)}_{f}_{s}")
    return [safe_field_name(n) for n in names]


def shorten_names(names, cap: int = 10):
    """Collision-free abbreviation for shapefile targets (opt-in).

    Keeps the statistic prefix and the suffix (k or radius) - the
    parts that distinguish results - and uniquifies by construction,
    so P25_income_400 and P75_income_400 can never collapse into one
    field. Returns {original: short}.
    """
    # BACKLOG 144: `used` is compared in LOWER CASE, because GIS field
    # names are case-insensitive - shapefile and file geodatabase
    # alike. Until 1.29.6 this checked `cand in used` case-sensitively
    # and cheerfully certified "collision-free" for T_Bar_400 ->
    # TBa400 and T_bar_400 -> Tba400, which are one name to a .dbf.
    # John's Pro run died on it: "cannot add field: 'Tba400'".
    # Note that shortening was never the cause - the FULL names
    # t_bar_400 and t_bar_400 already collide - so the doors must
    # refuse such group names outright (also 144). This only stops
    # the shortener from making a promise it cannot keep.
    out, used = {}, set()
    for n in names:
        parts = n.split("_")
        head = parts[0][:4]
        tail = parts[-1][:4] if len(parts) > 1 else ""
        mid = "".join(p[:2] for p in parts[1:-1])[:cap]
        base = (head + mid + tail)[:cap] or "F"
        cand, i = base, 0
        while cand.lower() in used:
            i += 1
            suf = str(i)
            cand = (base[:cap - len(suf)] + suf)
        used.add(cand.lower())
        out[n] = cand
    return out


def refuse_short_target(target, names, cap: int = 10,
                        container: str = "a file geodatabase"):
    """Return the refusal text when the target cannot hold these
    names, or None when it can.

    dBASE (shapefile) field names cap at ten characters. Refusing
    here means refusing with the fix, instead of failing after
    minutes of compute.
    """
    if not (target and str(target).lower().endswith(".shp")):
        return None
    bad = sorted({n for n in names if len(n) > cap})
    if not bad:
        return None
    return (f"The target is a SHAPEFILE and shapefile field names are "
            f"capped at {cap} characters - these results cannot fit: "
            f"{', '.join(bad[:5])}{'...' if len(bad) > 5 else ''}. "
            f"Write to a NEW feature class in {container} "
            "(unlimited names) or, for tables, a .csv output.")


def refuse_case_clashes(names, what: str) -> None:
    """Refuse names that differ only in case (BACKLOG 144).

    GIS field names are CASE-INSENSITIVE - shapefile and file
    geodatabase alike - so two groups called "Bar" and "bar" cannot
    both become columns. John hit this in the field: the run computed
    for eight seconds, produced T_Bar_400 and T_bar_400, and died in
    the write with "cannot add field: 'Tba400'".

    Shortening was never the cause; the full names collide too. So
    this must be refused where the names are CHOSEN - in the dialog,
    before any computing - and that is what this is for.

    Raises ValueError naming the offenders; silent otherwise.
    """
    seen: dict[str, str] = {}
    clash: list[tuple[str, str]] = []
    for n in names:
        key = str(n).strip().lower()
        if not key:
            continue
        if key in seen and seen[key] != str(n).strip():
            clash.append((seen[key], str(n).strip()))
        else:
            seen.setdefault(key, str(n).strip())
    if clash:
        pairs = "; ".join(f"'{a}' and '{b}'" for a, b in clash)
        raise ValueError(
            f"{what} differ only in upper/lower case: {pairs}. GIS "
            "field names ignore case, so these cannot both become "
            "columns - a shapefile and a geodatabase would each "
            "refuse the second one. Rename one of them.")


# ---------------------------------------------------------------------
# BACKLOG 316 - KEEP BOTH
#
# John's design, session 12. The choice existed only as Overwrite or
# Stop, so running the same k twice with two different friction fields
# - walk and drive, which is the whole point of exercise 4 - could not
# be done in one file: the second run destroyed the first.
#
# IT LIVES HERE BECAUSE BOTH DOORS NEED IT, and that is the lesson of
# 320: Pro had a locale-proof number reader from 1.16.7 and QGIS never
# got one, because the code sat in the .pyt instead of in the package.
# The two doors reach the SAME implementation now.
#
# THE SHAPES OF THE PROBLEM DIFFER, though:
#   Pro appends to the input layer, so a repeated name means
#   overwriting a column that is already there - a choice the user
#   makes on the dialog.
#   QGIS writes a NEW layer each run, copying the source's fields and
#   appending the results. A repeated name there means TWO FIELDS OF
#   ONE NAME in the output, which OGR resolves however it likes. There
#   is no overwrite to choose, so keeping both is simply correct and
#   QGIS needs no box.
# ---------------------------------------------------------------------

def letter_suffix(n: int) -> str:
    """0 -> "", 1 -> "b", 2 -> "c", ... 25 -> "z", 26 -> "aa", 27 -> "ab".

    The FIRST column keeps its canonical name, so a single run is
    unchanged and every published result still reads the same. Only a
    second column of the same name takes a letter - the unsuffixed
    name IS the "a".

    PAST z IT IS aa, then ab. John: "aa is a good solution". No
    ceiling and no refusal: it costs nothing and removes a wall
    somebody would otherwise meet at the least convenient moment.

    NOT the digit the shortener appends for over-length collisions
    (1.46.3, h72004_africanamericanalo1_100). Letters here keep the
    two schemes distinguishable, which was John's own argument for
    letters.
    """
    if n <= 0:
        return ""
    n += 1                      # shift past the unsuffixed "a"
    out = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        out = chr(ord("a") + r) + out
    return out


def keep_both(names, taken):
    """Rename any result whose field name is already in `taken`.

    `names` maps result column -> wanted field name; `taken` is the
    set of names already present. Returns (new_names, renamed), where
    `renamed` maps wanted -> written for everything that moved.

    MUST RUN BEFORE ANY SHORTENING, and that ordering is the whole of
    the shapefile question John raised. shorten_names() already
    resolves over-length collisions with a disambiguating digit, so
    R_black_alone_333 and R_black_alone_333b truncating to the same
    ten characters is a case it knows how to handle - PROVIDED it is
    handed the suffixed name. Shorten first and the suffix is cut away
    into a silent collision.
    """
    out, used, renamed = {}, set(taken), {}
    for col, want in names.items():
        if want not in used:
            out[col] = want
            used.add(want)
            continue
        i = 1
        # BOUNDED ON PURPOSE. This was `while True`, which is correct
        # only as long as letter_suffix keeps producing NEW names -
        # and a break-check that made it return a constant turned the
        # loop into a HANG rather than a failure. A hang inside
        # ArcGIS Pro is a force-quit and lost work, which is worse
        # than any error message. The ceiling is far above the 26
        # columns John expects and the loop cannot spin.
        for i in range(1, 100000):
            cand = want + letter_suffix(i)
            if cand not in used:
                break
        else:                                        # pragma: no cover
            raise ValueError(
                f"could not find a free name for '{want}' - "
                "letter_suffix is not producing new names")
        out[col] = cand
        used.add(cand)
        renamed[want] = cand
    return out, renamed


def keep_both_message(renamed, limit: int = 6) -> str:
    """One line naming what moved, or "" when nothing did.

    SAYING SO IS NOT OPTIONAL. A user who looks for their column, does
    not find it and concludes the run failed is the pattern of
    BACKLOG 309, 310 and 311 - a silent rename is that same failure
    wearing a different coat.
    """
    if not renamed:
        return ""
    shown = list(renamed.items())[:limit]
    more = len(renamed) - len(shown)
    return ("Keeping both: these names were already taken, so new "
            "columns were written beside them - "
            + "; ".join(f"{k} -> {v}" for k, v in shown)
            + (f" (+{more} more)" if more > 0 else ""))
