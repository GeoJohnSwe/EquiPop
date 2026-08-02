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


def categories_to_binary(cat, treat_spec, pop_values=None,
                         rest_group=None, rest_in_population=True):
    """
    cat        : array-like of category labels (any dtype; str-compared)
    treat_spec : dict {name: [values]} or the string syntax above
    pop_values : optional list of values forming the POPULATION -
                 rows outside it are excluded entirely (mask False)
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
    c = np.asarray(cat).astype(str)
    c = np.char.strip(c)
    if isinstance(treat_spec, str):
        treat_spec = parse_treat_spec(treat_spec)
    treat_spec = {str(k).strip().strip("\"'").strip(): v
                  for k, v in treat_spec.items()}
    def _clean(v):
        # quotes are OPTIONAL in typed value lists: 'cafe', "cafe"
        # and cafe all mean cafe (asked in the v1.16 field test)
        return str(v).strip().strip("\"'").strip()

    named = {_clean(v) for vals in treat_spec.values() for v in vals}
    rest = sorted({v for v in np.unique(c) if v and v not in named})

    if rest_group and rest:
        treat_spec = dict(treat_spec)
        treat_spec[str(rest_group).strip()] = rest

    if pop_values:
        pv = [_clean(v) for v in pop_values]
        if rest_group and rest_in_population is True:
            pv = sorted(set(pv) | set(rest))
        pop = np.isin(c, pv)
    else:
        pop = np.ones(len(c), bool)
    if (rest_group and rest and rest_in_population is False
            and not pop_values):
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
          + ("" if pop_values is None else f" (filter: {pop_values})")
          + f"; treatments: "
          + ", ".join(f"{k}={int(v.sum())}" for k, v in treats.items()))
    return pop, treats
