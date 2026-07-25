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


def categories_to_binary(cat, treat_spec, pop_values=None):
    """
    cat        : array-like of category labels (any dtype; str-compared)
    treat_spec : dict {name: [values]} or the string syntax above
    pop_values : optional list of values forming the POPULATION -
                 rows outside it are excluded entirely (mask False)
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

    if pop_values:
        pv = [_clean(v) for v in pop_values]
        pop = np.isin(c, pv)
    else:
        pop = np.ones(len(c), bool)
    treats = {}
    for name, vals in treat_spec.items():
        vv = [_clean(v) for v in vals]
        arr = (np.isin(c, vv) & pop).astype(float)
        treats[name] = arr
        if arr.sum() == 0:
            print(f"[categorical] treatment '{name}' matched ZERO rows "
                  f"- check spelling against the column's values")
    print(f"[categorical] population {int(pop.sum())}/{len(c)} rows"
          + ("" if pop_values is None else f" (filter: {pop_values})")
          + f"; treatments: "
          + ", ".join(f"{k}={int(v.sum())}" for k, v in treats.items()))
    return pop, treats
