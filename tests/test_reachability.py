# -*- coding: utf-8 -*-
"""test_reachability.py - the matrix in reachability.py must be TRUE.

A written table goes stale. This project has the proof: the backlog's
"what next" list stopped at item 164 and nobody noticed for eleven
releases, item 257's "STILL NEEDED" asked for samples that had
already been supplied, item 43 sat open five releases after it was
done, and item 45 described a symptom that had gone while missing one
that had not.

So every claim in the matrix is checked against the files it names,
and the package is checked against the matrix. Neither can drift
without the suite saying so.

Verified by breaking things on purpose:

  * a door's evidence symbol deleted from its file      -> 1 fails
  * a capability given neither a door nor a reason      -> 2 fails
  * a no_door entry left with an empty reason           -> 3 fails
  * a GAP whose door has since been built               -> 3b fails
  * a new module added and not declared anywhere        -> 4 fails
  * a backlog number cited that does not exist          -> 5 fails

BACKLOG 333 added 3b, and it is the one that closes the asymmetry:
every other check verifies a POSITIVE claim. A missing door used to
assert nothing at all, so the matrix could only ever be caught being
pessimistic about itself - never optimistic. It had already been wrong
that way for three releases.
"""
import os
import re

import pytest

import reachability as R

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve(cap, which):
    """Follow a same_as reference to the reason it points at."""
    seen = set()
    entry = R.MATRIX[cap][which]
    while entry[0] == "same":
        target = entry[1]
        assert target not in seen, (
            f"{cap!r}/{which} is a circular same_as reference")
        seen.add(target)
        assert target in R.MATRIX[cap], (
            f"{cap!r}/{which} points at a {target!r} door that this "
            "capability does not list")
        entry = R.MATRIX[cap][target]
    # A same_as that lands on a DOOR is a contradiction: it says
    # "there is no door here, for the same reason as over there",
    # where over there has one. Caught on the matrix's first run,
    # showing as `yesno:SpatialDemography` in the report.
    assert not seen or entry[0] == "none", (
        f"{cap!r}/{which} points at a door that EXISTS - a missing "
        "door cannot borrow its reason from a present one")
    # BACKLOG 333. A reference may borrow a REASON and never a
    # WITNESS. A witness names one door's file, so Pro borrowing
    # QGIS's would assert something about a QGIS file and prove
    # nothing about Pro - which is precisely how the lattice join came
    # to claim a missing Pro door while Pro had one.
    assert not (seen and len(entry) > 3 and entry[3]), (
        f"{cap!r}/{which} points at a GAP, whose witness names "
        f"another door's file. Give {which} its own not_yet() with "
        "its own witness, or make the target a ruled_out()")
    return entry


def _read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8",
              errors="replace") as f:
        return f.read()


# --- 1: the evidence must still be there -----------------------------

@pytest.mark.parametrize("cap", sorted(R.MATRIX))
def test_1_every_door_named_still_exists(cap):
    """The matrix says machine 1 is reachable from QGIS because
    alg_counts.py mentions `dispatch`. If someone rewires the door,
    that stops being true and the matrix must not keep saying it.

    This is the check the priority list never had.
    """
    for which, entry in R.MATRIX[cap].items():
        if entry[0] != "door":
            continue
        _, path, symbol = entry
        full = os.path.join(ROOT, path)
        assert os.path.exists(full), (
            f"{cap!r} claims a {which} door in {path}, which is gone")
        assert symbol in _read(path), (
            f"{cap!r} claims a {which} door because {path} mentions "
            f"{symbol!r}. It does not any more - either the door "
            "moved, in which case update the matrix, or it was "
            "removed, in which case the capability is now unreachable "
            "from there and the matrix must say so")


# --- 2, 3: silence is what is forbidden ------------------------------

@pytest.mark.parametrize("cap", sorted(R.MATRIX))
def test_2_every_capability_is_reachable_or_explains_itself(cap):
    """NO_DOOR IS NOT A FAILURE. John ruled that machine 2 needs no
    Stata door, and he was right. What is not allowed is a capability
    with no door and no sentence saying why - which is exactly the
    state inventory.py, vectorjoin.py and RunLog were all in."""
    row = R.MATRIX[cap]
    assert row, f"{cap!r} names no doors at all"
    unknown = set(row) - set(R.DOORS)
    assert not unknown, f"{cap!r} names unknown doors {sorted(unknown)}"
    reachable = [d for d, e in row.items() if e[0] == "door"]
    for d in row:
        _resolve(cap, d)                 # every reference must land
    assert reachable, (
        f"{cap!r} is reachable from NOWHERE - not even Python. That "
        "is either wrong or a capability that should not have been "
        "built")


@pytest.mark.parametrize("cap", sorted(R.MATRIX))
def test_3_a_missing_door_gives_a_reason_worth_reading(cap):
    for which in R.MATRIX[cap]:
        entry = _resolve(cap, which)
        if entry[0] != "none":
            continue
        # BACKLOG 333: a ruling is (none, why, item, None) and a gap
        # is (none, why, item, witness), so unpack the first three and
        # leave the rest. Hard-coding three is what broke when the
        # witness was added.
        why, item = entry[1], entry[2]
        assert why and len(why.strip()) > 25, (
            f"{cap!r} has no {which} door and the reason is "
            f"{why!r} - too short to tell a future session whether "
            "this was a decision or an oversight")


# --- 3b: a GAP must be able to announce its own obsolescence ---------

@pytest.mark.parametrize("cap", sorted(R.MATRIX))
def test_3b_a_gap_stops_being_true_when_the_door_is_built(cap):
    """BACKLOG 333. THE CHECK THIS FILE DID NOT HAVE, and the only one
    that can catch the matrix going stale in the direction it exists
    to watch.

    test_1 walks `entry[0] == "door"`, so a door that DISAPPEARS is
    caught. Before this, a missing door named no file and no symbol,
    so a door that APPEARS was never noticed - and the matrix went on
    saying the capability was unreachable. It only had to be wrong one
    way, and it was: "vector to lattice join" declared no QGIS door
    while `joinlayer` had sat in alg_continental.py since 1.47.6, the
    same release that wrote the claim. Three releases later it reached
    the backlog's own "what next" head as "the two finished engines
    with NO DOOR", and that is a wasted release waiting to happen.

    So a GAP now carries a witness - the file and symbol that must
    stay absent while the gap is real - and this fails the moment the
    door is built. A RULING carries none, because a decision is not a
    thing that goes stale on its own.
    """
    for which in R.MATRIX[cap]:
        entry = _resolve(cap, which)
        if entry[0] != "none" or len(entry) < 4 or not entry[3]:
            continue
        path, symbol = entry[3]
        full = os.path.join(ROOT, path)
        assert os.path.exists(full), (
            f"{cap!r}/{which} watches {path} for {symbol!r} and that "
            "file is gone - pick a witness that still exists, or the "
            "gap is unwatched again")
        assert symbol not in _read(path), (
            f"{cap!r} claims NO {which} door, and {path} now mentions "
            f"{symbol!r}. EITHER THE DOOR WAS BUILT - in which case "
            "say so with door(), and strike the backlog item - or the "
            "witness has become ambiguous and needs replacing. What "
            "must not happen is the matrix going on saying this is "
            "unreachable: that is how a future session comes to "
            "build something that already exists.")


# --- 4: the package cannot grow a capability in silence --------------

def test_4_every_module_is_either_a_capability_or_declared_internal():
    """THE CHECK THAT WOULD HAVE CAUGHT ALL FIVE. inventory.py landed
    in 1.45.0, vectorjoin.py in 1.46.0, and nothing anywhere asked
    which door they were reachable from. A new module now forces a
    choice: name its doors in the matrix, or say in INTERNAL that it
    is machinery.
    """
    found = set()
    for sub in ("", "doors"):
        d = os.path.join(ROOT, "equipop", sub)
        for f in os.listdir(d):
            if not f.endswith(".py") or f.startswith("_"):
                continue
            name = f[:-3] if not sub else f"{sub}.{f[:-3]}"
            found.add(name)
    undeclared = sorted(found - R.INTERNAL)
    assert not undeclared, (
        f"{undeclared} are new since the reachability matrix was "
        "written. Add each to R.INTERNAL in tests/reachability.py - "
        "every module goes there, which is what this check reads. If "
        "it is a capability somebody would ASK for rather than "
        "machinery, give it a MATRIX row naming its four doors as "
        "well; a row on its own does not satisfy this test. "
        "This is the step that was missing when inventory.py and "
        "vectorjoin.py shipped with no way to reach them")


# --- 5: a cited backlog item must exist ------------------------------

def test_5_every_backlog_number_cited_is_real():
    """A reason that points at an item nobody can find is a reason
    nobody can act on."""
    backlog = _read("BACKLOG.md")
    for cap, row in R.MATRIX.items():
        for which, entry in row.items():
            entry = _resolve(cap, which)
            if entry[0] != "none" or entry[2] is None:
                continue
            n = entry[2]
            assert re.search(rf"^- ~*{n}~*\s*\|", backlog, re.M), (
                f"{cap!r}/{which} cites BACKLOG {n}, which has no "
                "entry")


# --- the report, so the matrix is readable without reading the code --

def test_the_matrix_prints_a_readable_report(capsys):
    """Not an assertion so much as a way to SEE the thing. Run with
    -s to read it: `pytest tests/test_reachability.py -s -k report`"""
    doors = ("python", "qgis", "pro", "stata", "runner")
    print(f"\n{'capability':<46}" + "".join(f"{d:>8}" for d in doors))
    print("-" * 86)
    gaps = rulings = 0
    for cap in sorted(R.MATRIX):
        row = R.MATRIX[cap]
        cells = []
        for d in doors:
            e = row.get(d)
            if e is None:
                cells.append("")
            elif e[0] == "door":
                cells.append("yes")
            else:
                r = _resolve(cap, d)
                # BACKLOG 333: show WHICH KIND of absence. A ruling is
                # a decision and will not change on its own; a gap is
                # watched and will announce itself when it closes.
                # Reading "no" 26 times told you nothing about which
                # of those two you were looking at.
                watched = len(r) > 3 and r[3]
                mark = "gap" if watched else "-"
                cells.append(f"{mark}:{r[2]}" if r[2] else mark)
                if watched:
                    gaps += 1
                else:
                    rulings += 1
        print(f"{cap:<46}" + "".join(f"{c:>8}" for c in cells))
    print(f"\n{gaps} GAPS - watched: each names a file and a symbol "
          "that must stay absent,")
    print(f"      so the entry fails the day somebody builds the "
          "door (BACKLOG 333).")
    print(f"{rulings} rulings - a decision, not a gap. Nothing to "
          "watch; '-' in the table.")
    assert True
