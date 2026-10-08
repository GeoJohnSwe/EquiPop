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

BACKLOG 375, v1.53.2 - AND THAT RULE IS RIGHT FOR A DISTANCE AND
WRONG FOR A COUNT. '500,5' metres is a real measurement, so the lone
comma must stay a decimal comma for radii. '1,000' PEOPLE is one
thousand people in every notation anybody types, and reading it as
one person is a wrong answer that completes and writes columns -
`Mean_income_1` instead of `Mean_income_1000`, which looks plausible
unless you are looking for it. John's ruling, 7 October 2026: in a k
box a separator is REFUSED, not interpreted, and radii keep the
decimal comma. Refusing is the honest half - interpreting guesses at
intent, and the alternative reading of '1,6' is one and a half
people.

SO THERE ARE TWO READERS HERE AND THE DIFFERENCE IS DELIBERATE.
to_float/numlist read a MEASUREMENT. to_int/intlist read a COUNT OF
PEOPLE and are stricter. A door must pick the one that matches the
box, and a test fails if a door parses k with the measurement reader.
"""

from __future__ import annotations

import re

__all__ = ["to_float", "to_int", "numlist", "intlist", "BadNumber",
           "is_blank", "thousands_hint", "check_k_and_r", "K_OR_R"]

# BACKLOG 378. The sentence lives WITH the validator rather than in
# doors/help.py, because what makes "one place" true here is that a
# door cannot take the check without the wording or the wording
# without the check. help.py holds text a door RENDERS; this is text a
# door is REQUIRED to show.
K_OR_R = (
    "Give a neighbourhood size (k - a number of people), or a radius "
    "in metres - EquiPop needs one of the two to know what a "
    "neighbourhood is. Either alone is fine; both together is also "
    "fine and gives you both sets of columns.")

# BACKLOG 376. A space means "next value" to numlist and "thousands
# separator" to to_float - both in this file, which is how '1 000'
# became [1.0, 0.0] while to_float('1 000') correctly gave 1000.0.
# THE SPLIT CANNOT BE RESOLVED BY RULE: '200 100' is two k values and
# '1 000' is one number mistyped, and nothing in the text tells them
# apart. So the ambiguity is NOT silently resolved. The list keeps
# splitting on whitespace - that is what the labels promise - and this
# pattern is used to add a suggestion to a refusal that was going to
# happen anyway, which costs nothing when the reading was right.
_THOUSANDS = re.compile(r"(?<!\d)\d{1,3}[    .,]\d{3}(?!\d)")


def is_blank(text) -> bool:
    """True for empty, and for whitespace only.

    BACKLOG 378. Pro's `Required` asks whether a box has A VALUE, and
    a space IS a value - so a k box holding one space satisfied Pro,
    satisfied the dialog's own k-or-r guard (`if not text`), and then
    reached the engine as None. Every door must ask THIS question
    instead of testing the string for truth.

    A separator-only string counts as blank too, because that is what
    it means: ';' and '; ;' yield no values, and both reached the
    engine as None from a box Pro called satisfied.
    """
    return not str(text if text is not None else "").replace(";", " ").strip()


def thousands_hint(text) -> str | None:
    """The sentence to add when typed text looks like 1 000 or 1,000.

    Returns None when it does not, so a caller can append it
    unconditionally.

    A SUGGESTION, NOT A VERDICT, and deliberately loose: '200 100' is
    two perfectly good k values and also matches this pattern, because
    nothing in the text can tell them apart. So every caller gates it
    behind a refusal that is already justified on its own - a zero in
    a k list, or a radius under 10 m - and this never reaches a user
    whose input was fine. A caller that shows it ungated will be
    wrong, which is what the test on this asserts.
    """
    if _THOUSANDS.search(str(text or "")):
        return ("If you meant ONE number, write it with digits only - "
                "1000, not 1 000 or 1,000. In these boxes a space or "
                "a semicolon separates DIFFERENT values, so '1 000' "
                "is read as two of them.")
    return None


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
    """As to_float, but the value must be a whole COUNT OF PEOPLE.

    k is a count of people, so 100.5 is refused rather than quietly
    truncated - a silently rounded k is a wrong answer that looks
    right. That sentence has been in this docstring since 1.47 and
    the rule it describes was reachable from ONE of the project's four
    GUI doors (BACKLOG 377).

    BACKLOG 375, JOHN'S RULING. A decimal separator in a COUNT is
    refused outright, not interpreted. '1,000' and '1.000' are one
    thousand people to the person typing and 1.0 to float(), and the
    run completes with a neighbourhood of one person. There is no
    legitimate k with a decimal separator in it: a fraction of a
    person is not a thing, and a thousands separator is a typing
    convention this box does not accept.

    A number passed FROM CODE is already a number and is not subject
    to the rule - only typed text is, which is where the ambiguity
    lives.
    """
    if isinstance(text, str) and any(ch in text for ch in ".,"):
        shown = text.strip()
        radius_note = (
            " (A decimal comma is fine in a RADIUS box, where 500,5 "
            "metres is a real distance - it is a count of PEOPLE that "
            "cannot have one.)")
        # WHICH MISTAKE WAS IT? Two different errors, two different
        # sentences - "write 1000" is nonsense advice for '1,6'.
        # The test is the THOUSANDS PATTERN, three digits after the
        # separator, and NOT what _clean() makes of it: _clean is the
        # function that misreads this, so asking it what the user
        # meant gives the wrong answer. Writing that mistake into this
        # very message is how the first draft of it suggested "if you
        # meant 1, write 1" for an input of '1,000'.
        if _THOUSANDS.search(shown):
            meant = re.sub(r"[    .,]", "", shown)
            raise BadNumber(
                f"'{shown}' looks like a thousands separator, and k "
                f"counts PEOPLE. If you meant {meant}, write it that "
                f"way - digits only, no comma or point." + radius_note)
        raise BadNumber(
            f"'{shown}' is a fraction of a person. k counts PEOPLE in "
            "a neighbourhood, so it is a whole number of them - write "
            "digits only, with no comma or point." + radius_note)
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
    """numlist, for whole numbers - k values.

    THE ONE READER FOR A k BOX. Every door must come through here, so
    that the refusals above are reachable from all of them rather
    than from whichever one the author happened to be editing
    (BACKLOG 377).

    A non-positive k is refused HERE, with the text still in hand, so
    the message can carry the thousands suggestion. The engine refuses
    it too - that guard stays, because the Python API takes k_values
    directly and never sees this function - but by the time it fires
    the typed text is gone and all it can say is "got [0]", which is
    an answer to a question the user did not ask.
    A COMMA MEANS TWO DIFFERENT THINGS AND BOTH ARE RIGHT. Between
    digits it is a numeric separator - '1,000' is one thousand people
    mistyped, and John's ruling is to refuse it. Anywhere else it
    separates VALUES: machines 3 and 4 have accepted '300, 500' as two
    k values since they were written, with a test saying so, and that
    is a perfectly clear thing to type. So commas that are not between
    digits become spaces here, and the rest reach to_int to be
    refused.
    This is why intlist and numlist differ about commas, which looks
    like an inconsistency and is not: in a RADIUS box '500,5' is one
    number, because half of Europe writes a decimal that way. A count
    of people cannot have a decimal at all, which is exactly what
    frees the comma up to mean something else.
    """
    out = []
    loose = re.sub(r"(?<!\d),|,(?!\d)", " ", str(text or ""))
    for tok in loose.replace(";", " ").split():
        v = to_int(tok, None)
        if v is not None:
            out.append(v)
    bad = [v for v in out if v <= 0]
    if bad:
        hint = thousands_hint(text)
        raise BadNumber(
            f"k must be a positive number of people; got {bad}. "
            + (hint if hint else
               "k counts PEOPLE in a neighbourhood, so it has to be "
               "at least 1."))
    return out or list(default)


def check_k_and_r(k_text, r_text, *, need_one=True, k_required=False):
    """What is wrong with a door's k and r boxes, or None.

    Returns ("k"|"r", message) so a door can attach the message to the
    box it belongs to, in whatever way its host offers - Pro's
    setErrorMessage, QGIS's checkParameterValues, a Stata refusal.

    BACKLOG 378, AND THE REASON THIS IS A FUNCTION RATHER THAN A
    PARAGRAPH IN FOUR DOORS. BACKLOG 305 added "you need k or r" to
    the dialog after John hit the engine's own refusal while teaching.
    It went into Counts & Shares in both GUIs and into NEITHER of the
    other two doors that can reach the same refusal - so machine 2
    still answered with a 40-line traceback naming `k_values`, an
    argument nobody typed, eighteen months later. The guard was also
    written as `if not text`, which a single SPACE defeats, so even
    the door that had it could be walked past.
    One function, four callers, and a test that fails if a door
    reaches the engine without calling it.

    THREE SHAPES, because the four doors genuinely differ and
    flattening them would put a wrong message in front of somebody:
      need_one      - machines 1 and 2: k OR r, either alone is fine.
      k_required    - machine 4: k and no radius box, k compulsory.
      neither       - machine 3: k and no radius box, and BLANK k is
                      a real choice ("leave it blank for the point
                      table"), so only the PARSE is checked.
    A door asking for the wrong one of these is the kind of mistake
    that reads as a fixed bug, so each caller says which it is and a
    test asserts the count of callers.
    """
    if need_one and is_blank(k_text) and is_blank(r_text):
        return ("k", K_OR_R)
    if not is_blank(k_text):
        try:
            intlist(k_text)
        except BadNumber as bad:
            return ("k", str(bad))
    elif k_required:
        # A Required box that the host considers filled because it
        # holds a space. Pro's own validation will not catch that.
        return ("k", "Give a neighbourhood size here - k is a number "
                     "of PEOPLE, written with digits only, e.g. 1000.")
    if not is_blank(r_text):
        try:
            numlist(r_text)
        except BadNumber as bad:
            return ("r", str(bad))
        hint = thousands_hint(r_text)
        if hint and min(numlist(r_text)) < 10:
            # '1 500' metres reads as radii of 1 m and 500 m, and both
            # are positive, so nothing downstream can refuse it. A
            # 1 m radius is not a question anybody asks, so say so
            # here rather than returning a neighbourhood of nobody.
            meant = re.sub(r"[    ]", "", str(r_text).strip())
            return ("r", f"A radius of {min(numlist(r_text)):g} m would "
                         f"hold almost nobody. If you meant {meant} "
                         "metres, write it without the space. " + hint)
    return None
