# -*- coding: utf-8 -*-
"""
labels.py - the numeric part of a result column's name, ONCE.

BACKLOG 337, from Marina's pull request (GitHub lizardie), which found
one quarter of this and proposed to fix it by refusing the run.

WHAT WAS WRONG. A radius or an effort budget becomes part of a column
name - N_r500, Rounds_tau3 - and FOUR PLACES formatted that number,
three of them one way and one another:

    equipop/fastcounts.py    _lab()          f"{x:g}"
    equipop/analysis.py      suffix=         f"r{rv:g}"
    equipop/stata_bridge.py  labs =          f"r{r:g}"
    equipop/doors/fields.py  _fmt_num()      str(int(f)) if whole else str(f)

`:g` carries SIX SIGNIFICANT DIGITS and switches to scientific
notation outside a narrow range, and the three consequences were all
live:

  TWO RADII COLLAPSING INTO ONE. r(100.000001 100.000002) both
  formatted to "r100", and the engine's output is a dict, so the
  second silently OVERWROTE the first. One column where the user asked
  for two, no error, no warning.

  AN ILLEGAL NAME. r(1000000) - 1000 km, an ordinary continental
  radius - formatted to "r1e+06". In Stata that reaches
  Data.addVarDouble("N_r1e+06"), which is refused; in ArcGIS Pro the
  field sanitiser turned it into the unreadable "N_r1e_06"; in Python
  it stayed "N_r1e+06". FOUR DOORS, FOUR ANSWERS for one radius.

  A DOT IN A NAME. r(100.5) produced "N_r100.5", which no Stata
  variable and no shapefile field may be called - while the .ado's own
  `replace` drop list already built "N_r100_5" with a subinstr. The two
  halves of one file disagreed: somebody knew the dot was a problem
  and fixed only the consuming side.

AND THE PREDICTION DISAGREED WITH THE ENGINE. doors/fields.py told
ArcGIS Pro to expect N_r1000000 while the engine made N_r1e+06, so
Pro's shapefile-name check and its "names will be shortened" warning
were computed against a field that never appears - and that function's
docstring claims it is "validated against the real dispatch in the
simulator suite, so this stays a prediction and does not drift into a
guess". It had drifted.

WHY NOT MARINA'S FIX. Hers raises ValueError for a label that is not
a legal STATA name, inside knn_to_rows and dispatch - so every door,
including Python and both GIS doors, is refused r(1000000) because of
a Stata naming rule. tests/test_menu.py uses 1e6 deliberately and
calls it the whole-world radius. The project's own rule, written in
dispatch for missing codes, is that no engine learns a door's
concepts. Her DIAGNOSIS was right and is why this module exists.

WHAT THIS DOES INSTEAD. Formats so the label is always legal and
always distinct, and fixes it AT THE SOURCE rather than sanitising at
the output boundary - so the engine never produces a name that needs
repairing, and the prediction and the engine agree by construction.

  * SIX DECIMAL PLACES, never scientific notation. Micrometre
    precision on a radius in metres, which distinguishes anything a
    person would type, and 1000000 stays 1000000.
  * Trailing zeros removed, so 500.0 is "500" and the existing column
    names are unchanged. THIS IS THE COMPATIBILITY PROPERTY THAT
    MATTERS: every radius anybody has actually used - whole numbers,
    and decimals like 100.5 - gets exactly the name it got before,
    minus the dot. No pinned number in this project moves.
  * The decimal point becomes an underscore here rather than three
    steps later.
  * A COLLISION IS STILL REFUSED, as Marina has it, because silently
    merging two columns is the fault being fixed. At six decimal
    places two radii only collide when they are the same radius.

No numpy, no pandas: doors/fields.py predicts names before any engine
is imported, and this has to be importable there.
"""

from __future__ import annotations

__all__ = ["numeric_tag", "radius_suffix", "tau_suffix",
           "radius_suffixes", "LabelCollision", "DECIMALS"]

#: Decimal places kept. Six is micrometres on a metre radius - finer
#: than any survey, and finer than any radius a person types. Raising
#: it would lengthen names for no gain; lowering it would reintroduce
#: the collision this module exists to stop.
DECIMALS = 6


class LabelCollision(ValueError):
    """Two values that cannot be told apart in a column name."""


def numeric_tag(value) -> str:
    """The number as it appears INSIDE a column name.

    500 -> '500', 100.5 -> '100_5', 1000000 -> '1000000',
    0.00005 -> '0_00005', 100.000001 -> '100_000001'.

    Never scientific notation, never a dot, never a sign character -
    so the result is safe in a Stata variable name, a shapefile field
    name and a GeoPackage column alike.
    """
    # BACKLOG 373, v1.53.2. `float(value)` here was reachable from a
    # dialog with a user's typed text in hand, and produced the raw
    # `could not convert string to float: '500,5'`. The callers are
    # fixed to parse first, and this stays locale-proof anyway: this
    # function is the LAST common point before a column name, so a
    # future caller handing it text must not be able to resurrect that
    # message. A number arriving from code takes the fast path.
    if isinstance(value, str):
        from equipop.doors.numbers import to_float
        v = to_float(value)
        if v is None:
            raise LabelCollision(
                "an empty value cannot become part of a column name.")
    else:
        v = float(value)
    if v != v or v in (float("inf"), float("-inf")):
        raise LabelCollision(
            f"{value!r} is not a finite number, so it cannot become "
            "part of a column name.")
    if v < 0:
        # A negative radius or effort budget is not a thing. Refused
        # here rather than producing a name with a minus in it, which
        # is what `:g` did and which no door can store.
        raise LabelCollision(
            f"{v:g} is negative - a radius and an effort budget are "
            "both distances and cannot be less than zero.")
    text = f"{v:.{DECIMALS}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if not text:                                     # 0.0
        text = "0"
    # A value large enough to need more characters than Stata allows
    # in a whole variable name is refused here, where the number is,
    # rather than thirty lines later where the name is assembled.
    if len(text) > 20:
        raise LabelCollision(
            f"{v:g} needs {len(text)} characters as part of a column "
            "name, which leaves no room for the rest of the name. Use "
            "a smaller value, or scale your coordinates.")
    return text.replace(".", "_")


def radius_suffix(value) -> str:
    """'r500', 'r100_5' - the suffix a radius contributes."""
    return "r" + numeric_tag(value)


def tau_suffix(value) -> str:
    """'tau3', 'tau3_5' - the suffix an effort budget contributes.

    The same exposure as a radius and found with it: friction.py
    formatted these with `:g` too, so tau(3.5) produced the illegal
    'Rounds_tau3.5' and two budgets agreeing to six significant
    digits would have collided in the same way.
    """
    return "tau" + numeric_tag(value)


def radius_suffixes(values, what: str = "radius") -> list:
    """Suffixes for several values, refusing a true collision.

    Marina's rule, kept: two values that cannot be told apart in a
    column name must stop the run, because the alternative is one
    column quietly holding the answer to a different question. What
    changes is WHEN it fires - at six decimal places, only when the
    two values really are the same.
    """
    seen, out = {}, []
    for v in values:
        tag = numeric_tag(v)
        if tag in seen and float(seen[tag]) != float(v):
            raise LabelCollision(
                f"{what} {float(v):g} and {float(seen[tag]):g} both "
                f"become '{tag}' in a column name and could not be "
                f"told apart in the output - one result would silently "
                f"overwrite the other. They differ by less than "
                f"{10 ** -DECIMALS:g}, which is below the precision a "
                f"column name can carry; use values that differ by "
                f"more than that.")
        seen[tag] = v
        out.append(tag)
    return out
