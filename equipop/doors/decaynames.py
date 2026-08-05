# -*- coding: utf-8 -*-
"""
decaynames.py - the decay models, named once for every door.

v1.28, John's field finding: the QGIS dropdown offered "gauss" and
"linear". Neither exists. They were written from memory rather than
read from the engine, and a door that offers a model the engine has
never heard of either crashes or silently substitutes another - both
worse than having fewer choices.

So the list is BUILT from equipop.decay.MODELS. A model added to the
engine appears in both dialogs; a name that is not in the engine
cannot appear at all. The gloss is the plain-words half of the
project's naming rule: say what the curve DOES before naming what it
IS.
"""

NO_DECAY = "no decay"

# what each curve actually does, in words a first-year can hold
GLOSS = {
    "negexp": "steady decline - the classic; each extra kilometre "
              "costs the same proportion",
    "expnormal": "flat nearby, then falls away - a Gaussian; good "
                 "when everything within a short walk counts equally",
    "expsqrt": "steep at first, then a long tail - punishes the "
               "first metres hardest",
    "lognormal": "a shoulder, then a tail - little effect very "
                 "close, then a steady fall",
    "power": "inverse distance - a very long tail; distant people "
             "never quite stop counting",
}


def model_names():
    """Every model the ENGINE has, in a stable order."""
    from equipop.decay import MODELS
    order = ["negexp", "expnormal", "expsqrt", "lognormal", "power"]
    known = list(MODELS)
    return ([m for m in order if m in known]
            + [m for m in known if m not in order])


def choices(include_none=True):
    """What a dropdown should offer: 'negexp (steady decline - ...)'."""
    out = [NO_DECAY] if include_none else []
    for m in model_names():
        g = GLOSS.get(m)
        out.append(f"{m} ({g})" if g else m)
    return out


def model_from_choice(text):
    """The engine's name back out of a dropdown label. None means no
    decay."""
    t = str(text or "").strip()
    if not t or t.lower().startswith("no decay"):
        return None
    first = t.split(" (")[0].strip()
    return first if first in model_names() else None


def curve_in_plain_numbers(model, half_life_m):
    """What this curve DOES, in metres and percentages - the naming
    pass John asked for: 'at 500 m 50%, at 1 km 25%'."""
    from equipop.decay import Decay
    try:
        d = Decay(model=model, half_life_m=float(half_life_m))
        pts = [half_life_m, 2 * half_life_m, 3 * half_life_m]
        parts = [f"at {p:,.0f} m {100 * d.weight(p):.0f}%"
                 for p in pts]
        return (f"Decay '{model}': " + ", ".join(parts)
                + " of full weight.")
    except Exception:
        return f"Decay '{model}' with a half-life of {half_life_m:g} m."
