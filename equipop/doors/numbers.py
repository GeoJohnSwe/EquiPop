"""
numbers.py - reading numbers a person TYPED, whatever their machine
thinks a decimal point is.

BACKLOG 320. Pro has had this since 1.16.7, when a SWEDISH machine
returned '0,000001' from a dialog box and float() refused it. QGIS
never got it: alg_counts read k, radii and tau with bare int() and
float() straight on the typed text, so a Norwegian student entering a
radius as 500,5 - which is what a Norwegian keyboard and a Norwegian
Windows produce - met the raw Python message

    could not convert string to float: '500,5'

with nothing to say that a decimal comma was the problem. Found from
student feedback after the Los Angeles lecture, 22 September 2026.

A DOOR-PARITY GAP THAT test_door_parity DID NOT CATCH, because it
compares which BOXES the doors offer and not how they READ them. The
parsing lives here now so there is one implementation and both doors
call it.

THE RULE FOR A LONE COMMA is that it is a DECIMAL comma: '12,5' is
twelve and a half, not twelve thousand five hundred. That is the
right call for the audience - European - and it is what Pro has done
since 1.16.7. Several commas are thousands separators, and a comma
with a point present is a thousands separator too.
"""

from __future__ import annotations

__all__ = ["to_float", "to_int", "numlist", "intlist", "BadNumber"]


class BadNumber(ValueError):
    """A typed value that is not a number, with a message a door can
    show as it is."""


def _clean(text) -> str:
    t = str(text if text is not None else "").strip()
    # thin and non-breaking spaces are what a spreadsheet pastes in
    for ch in ("\u00a0", "\u202f", "\u2009", " ", "'"):
        t = t.replace(ch, "")
    if "," in t and "." in t:            # 1,234.56 -> 1234.56
        return t.replace(",", "")
    if t.count(",") == 1:                # 12,5 -> 12.5
        return t.replace(",", ".")
    return t.replace(",", "")            # 1,234,567 -> 1234567


def to_float(text, default=None):
    """'12,5', '12.5', '1 234,5' and '1,234.5' all give a float.

    Blank gives `default`. Anything else raises BadNumber with a
    message written for the person who typed it.
    """
    t = _clean(text)
    if not t:
        return default
    try:
        return float(t)
    except ValueError:
        raise BadNumber(
            f"'{text}' is not a number. Use digits only - a decimal "
            "comma or a decimal point both work, so 12,5 and 12.5 are "
            "the same thing here.")


def to_int(text, default=None):
    """As to_float, but the value must be a whole number.

    k is a count of people, so 100.5 is refused rather than quietly
    truncated - a silently rounded k is a wrong answer that looks
    right.
    """
    v = to_float(text, None)
    if v is None:
        return default
    if abs(v - round(v)) > 1e-9:
        raise BadNumber(
            f"'{text}' is not a whole number. k counts people, so it "
            "cannot have a fraction.")
    return int(round(v))


def numlist(text, default=()):
    """A list of numbers separated by spaces, semicolons or newlines.

    NOT by commas: a comma is a decimal separator for half of Europe,
    so '500,5 800' is two numbers and '500,5;800' is the same two.
    """
    out = []
    for tok in str(text or "").replace(";", " ").split():
        v = to_float(tok, None)
        if v is not None:
            out.append(v)
    return out or list(default)


def intlist(text, default=()):
    """numlist, for whole numbers - k values."""
    out = []
    for tok in str(text or "").replace(";", " ").split():
        v = to_int(tok, None)
        if v is not None:
            out.append(v)
    return out or list(default)
