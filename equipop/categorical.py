"""
categorical.py - one small factory: a categorical column (fclass...)
becomes population mask + treatment 0/1 arrays. Lives in the PACKAGE
so every bridge (ArcGIS, Stata, plain Python) shares one tested
implementation.

Treatment syntax (string form, for dialog boxes):
    "restaurant; cafe"                    -> two variables
    "food: restaurant, cafe, bar; pub"    -> grouped 'food' + 'pub'
"""
import numpy as np


def parse_treat_spec(spec: str) -> dict[str, list[str]]:
    """'food: restaurant, cafe; pub' -> {'food': [...], 'pub': ['pub']}"""
    out = {}
    for part in str(spec or "").split(";"):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            name, vals = part.split(":", 1)
            out[name.strip()] = [v.strip() for v in vals.split(",")
                                 if v.strip()]
        else:
            out[part] = [part]
    return out


def _is_number(v):
    return isinstance(v, (int, float, np.integer, np.floating)) \
        and not isinstance(v, (bool, np.bool_))


def _number_text(v):
    """A number the way a person writes it: 1.0 is '1', 2.5 is '2.5',
    a missing one is ''."""
    f = float(v)
    if f != f:
        return ""
    if f in (float("inf"), float("-inf")):
        return str(f)
    if f == int(f) and abs(f) < 1e15:
        return str(int(f))
    return repr(f)


def _labels(cat):
    """(labels, numeric): the column as the text its values are
    matched by, and whether it is a column of numbers."""
    a = np.asarray(cat)
    if a.dtype.kind in "iu":
        return a.astype(str), True
    if a.dtype.kind == "f":
        out = np.empty(a.shape, dtype=object)
        ok = np.isfinite(a)
        whole = ok & (a == np.floor(np.where(ok, a, 0.0))) \
            & (np.abs(np.where(ok, a, 0.0)) < 1e15)
        out[:] = ""
        out[whole] = a[whole].astype(np.int64).astype(str)
        rest = ok & ~whole
        if rest.any():
            out[rest] = [repr(float(v)) for v in a[rest]]
        odd = ~ok & ~np.isnan(a)                     # +-inf
        if odd.any():
            out[odd] = [str(float(v)) for v in a[odd]]
        return out.astype(str), True
    if a.dtype.kind in "US":
        return np.char.strip(a.astype(str)), False
    # anything else arrives value by value (a GIS attribute list): a
    # number is written as a number, a missing value is no type at all
    flat = list(a.ravel()) if a.dtype == object else list(a.astype(str))
    numbers = [_is_number(v) for v in flat]
    present = [v is not None and not (_is_number(v) and v != v)
               for v in flat]
    numeric = any(present) and all(n for n, here in zip(numbers, present)
                                   if here)
    out = [("" if v is None else _number_text(v) if _is_number(v)
            else str(v).strip()) for v in flat]
    return np.asarray(out, dtype=str), numeric


def labels(cat):
    """A type column as the text its values are matched by.

    Text is matched as text, stripped. NUMBERS are matched the way a
    person writes them: 1.0 is "1", 2.5 is "2.5". A missing value
    (None, NaN) is "" - no type at all, in no group.

    BACKLOG 467. Until 1.63.7 this was `astype(str)`, so a type code
    stored as a number read "1.0", and the "1" a person types - or
    picks from Pro's dropdown, which shows an integer field as "1" -
    matched nothing. QGIS answered with zeros and no message; Pro
    refused, in the name of a dropdown that had offered the value.
    A missing number read "nan" and counted as a type of its own.
    """
    return _labels(cat)[0]


def known(cat):
    """The distinct types a column holds, sorted, without the empty
    one. What a door shows when it refuses a value."""
    return sorted({str(v) for v in np.unique(labels(cat)) if v})


def _typed(value, numeric):
    """A typed value in the form the column's labels have. Quotes are
    optional ('cafe', "cafe" and cafe all mean cafe); against a
    column of numbers, 1, 1.0 and 01 all mean the number one."""
    t = str(value).strip().strip("\"'").strip()
    if numeric and t:
        try:
            f = float(t.replace(",", "."))
        except ValueError:
            return t
        if f == f and abs(f) != float("inf"):
            return _number_text(f)
    return t


def matcher(cat):
    """A function putting a typed value into this column's form - for
    a door that checks its tables against the column before it runs."""
    numeric = _labels(cat)[1]
    return lambda value: _typed(value, numeric)


def unknown(values, cat):
    """Which of the typed values match no row of the column - in the
    column's own form, so that 1 against a number column is found.
    The doors refuse on these BEFORE computing: a value that matches
    nothing gives a column of zeros that looks like a result."""
    lab, numeric = _labels(cat)
    have = set(np.unique(lab))
    out = []
    for v in values:
        t = _typed(v, numeric)
        if t and t not in have and str(v).strip() not in out:
            out.append(str(v).strip())
    return out


def categories_to_binary(cat, treat_spec, pop_values=None,
                         rest_group=None, rest_in_population=True,
                         pop_mask=None):
    """
    cat        : array-like of category labels (any dtype; str-compared)
    treat_spec : dict {name: [values]} or the string syntax above
    pop_values : optional list of values forming the POPULATION -
                 rows outside it are excluded entirely (mask False)
    pop_mask   : the population as a True/False array instead, for
                 when it was decided from ANOTHER column (BACKLOG
                 468). pop_values names values of `cat`; a reference
                 population picked by country cannot be handed in as
                 values of a column of shop types - it matched nothing
                 there, and every group came out zero.
    rest_group : optional name for EVERY value not named above -
                 "name the few you care about, the rest fall here"
    rest_in_population : whether those remaining values count as
                 population. Pass None when the population is decided
                 SOMEWHERE ELSE - which is the case from v1.22, where
                 a separate reference table names the population and
                 the remainder is purely a way of grouping what is
                 left over. Otherwise it decides the DENOMINATOR:

                   True  - the share is "of everything present"
                           (fastfood per POI: benches and postboxes
                           are in the denominator too)
                   False - the share is "of what you named"
                           (fastfood per eating place)

                 Both are real questions and they look identical on
                 screen, which is why the dialog asks rather than
                 choosing (John, v1.20 - his Europe-wide fastfood run
                 was the first form).

    Returns (pop_mask, {name: 0/1 float array}) - treatments are 0
    outside the population by construction.
    """
    # BACKLOG 467: one form for the column and for what is typed
    # against it - see labels(). Was `astype(str)`: 1.0 against "1".
    c, numeric = _labels(cat)
    if isinstance(treat_spec, str):
        treat_spec = parse_treat_spec(treat_spec)
    treat_spec = {str(k).strip().strip("\"'").strip(): v
                  for k, v in treat_spec.items()}

    def _clean(v):
        # quotes are OPTIONAL in typed value lists: 'cafe', "cafe"
        # and cafe all mean cafe (asked in the v1.16 field test)
        return _typed(v, numeric)

    named = {_clean(v) for vals in treat_spec.values() for v in vals}
    rest = sorted({v for v in np.unique(c) if v and v not in named})

    if rest_group and rest:
        treat_spec = dict(treat_spec)
        treat_spec[str(rest_group).strip()] = rest

    if pop_mask is not None:
        pop = np.asarray(pop_mask, bool)
        if pop.shape != c.shape:
            raise ValueError(
                f"pop_mask has {pop.shape[0] if pop.ndim else 0} rows, "
                f"the type column {len(c)}")
        if pop_values:
            raise ValueError("give pop_values or pop_mask, not both")
    elif pop_values:
        pv = [_clean(v) for v in pop_values]
        if rest_group and rest_in_population is True:
            pv = sorted(set(pv) | set(rest))
        pop = np.isin(c, pv)
    else:
        pop = np.ones(len(c), bool)
    if (rest_group and rest and rest_in_population is False
            and not pop_values and pop_mask is None):
        # "the rest are NOT population" only means something when a
        # population was named; otherwise everything is population
        # anyway and the tick would silently do nothing.
        pop = np.isin(c, sorted(named))
    treats = {}
    for name, vals in treat_spec.items():
        vv = [_clean(v) for v in vals]
        arr = (np.isin(c, vv) & pop).astype(float)
        treats[name] = arr
        if arr.sum() == 0 and not (rest_group
                                   and name == str(rest_group).strip()
                                   and rest_in_population is False):
            # a deliberately excluded remainder group is EXPECTED to
            # be zero - that is what "not in the population" means,
            # and warning about it would be noise
            print(f"[categorical] treatment '{name}' matched ZERO rows "
                  f"- check spelling against the column's values")
    if rest_group:
        where = ("as a treatment group; the reference table decides "
                 "the population"
                 if rest_in_population is None else
                 "IN the population (shares are of everything present)"
                 if rest_in_population else
                 "OUTSIDE the population (shares are of the values you "
                 "named)")
        print(f"[categorical] '{rest_group}' collected {len(rest)} "
              f"remaining value(s), {where}")
    print(f"[categorical] population {int(pop.sum())}/{len(c)} rows"
          + (" (the reference population)" if pop_mask is not None
             else "" if pop_values is None
             else f" (filter: {pop_values})")
          + f"; treatments: "
          + ", ".join(f"{k}={int(v.sum())}" for k, v in treats.items()))
    return pop, treats
