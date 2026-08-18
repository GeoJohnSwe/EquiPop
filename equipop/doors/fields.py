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
    f = float(v)
    return str(int(f)) if f == int(f) else str(f)


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
