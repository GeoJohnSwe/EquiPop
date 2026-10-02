# -*- coding: utf-8 -*-
"""make_test_data.py - regenerate stata/equipop_test_data.dta.

BACKLOG 237. John, from the field: "ValFloat is not float and should
be; ValCount holds counts." The names teach the wrong thing, and the
file is the first thing a reader of the paper inspects - it ships to
every SSC user who types `ssc install equipop, all`.

WHAT THIS CHANGES, and what it deliberately does not.

  ValFloat was declared Stata `double` (type 'd') under a name that
  says float. It is now a Stata `float`. VERIFIED LOSSLESS BEFORE
  TOUCHING A PUBLISHED FIXTURE: every one of its 9,166 present values
  is a whole number, the largest is 23,254, and float32 holds integers
  exactly to 16,777,216 - so the round trip is exact and NOT ONE
  PINNED NUMBER MOVES. The showcase's `Nv 167.30 | Mean 1815.23 |
  Med 1248.10 | Gini .5806` stands unchanged, which is what makes this
  safe to do on a published file.

  EVERY VARIABLE GAINS A LABEL. All nine were empty. In Stata the
  label is where meaning lives, and a published teaching dataset
  without labels forces the NAME to carry the whole burden - which is
  how a name that lies does real damage. This is the better cure for
  "misleading" than renaming: a rename would break
  equipop_showcase.do, equipop_test_pass.do, the paper's variable
  list and every student's notes, for a fixture whose own backlog
  item calls the fault minor and not a correctness problem.

  THE VALUES AND THE NAMES ARE UNTOUCHED. Worth stating because the
  tension is real and it is John's to settle: ValFloat exists to
  demonstrate a CONTINUOUS measure - that is the whole point of block
  20, corrected in 1.40.5 after a continuous measure had been put
  through treat() - and every value in it is a whole number. Genuinely
  continuous values would teach the lesson better. They would also
  need `double` storage to be worth having, which is the opposite of
  what John asked for here, and they would change the one pinned
  EXPECT line and diverge from the copy now hosted on SSC. So the
  storage type is fixed as instructed and the pedagogy question is
  recorded in 237 rather than decided here.

Run: python tools/make_test_data.py
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HERE, "stata", "equipop_test_data.dta")

#: What each variable IS, in the words the showcase and the field pass
#: already use for it. Kept here rather than in the .dta alone so the
#: text is reviewable in a diff.
LABELS = {
    "ID": "row identifier, 1..N",
    "X_local": "easting, metres in the local projection",
    "Y_local": "northing, metres in the local projection",
    "LowEdu": "0/1 marker: compulsory education only",
    "HighEdu": "0/1 marker: tertiary education",
    "TheoEdu": "0/1 marker: theoretical upper secondary",
    "VocaEdu": "0/1 marker: vocational upper secondary",
    "ValFloat": "continuous magnitude, missing by design on some rows",
    "ValCount": "a count, 0-98 - not a 0/1 marker and not a magnitude",
}

#: Storage types the file must declare, as Stata's `describe` shows
#: them. The pandas dtype decides this, so it is asserted rather than
#: hoped for.
WANTED = {"ID": "l", "X_local": "d", "Y_local": "d",
          "LowEdu": "l", "HighEdu": "l", "TheoEdu": "l",
          "VocaEdu": "l", "ValFloat": "f", "ValCount": "l"}


def declared_types(path):
    r = pd.io.stata.StataReader(path)
    r.read(1)
    return dict(zip(r._varlist, [str(t) for t in r._typlist]))


def main():
    before = pd.read_stata(PATH)
    df = before.copy()

    # the one storage change, and the reason it is safe
    present = df["ValFloat"].to_numpy(float)
    finite = np.isfinite(present)
    if not (present[finite] % 1 == 0).all():
        sys.exit("[237] ValFloat now holds fractional values, so float "
                 "storage would LOSE precision. Stop and rule on the "
                 "storage type before regenerating.")
    exact = (present[finite].astype(np.float32).astype(np.float64)
             == present[finite]).all()
    if not exact:
        sys.exit("[237] float32 does not round-trip these values "
                 "exactly, so this regeneration would change pinned "
                 "numbers. Stop.")
    df["ValFloat"] = df["ValFloat"].astype(np.float32)

    df.to_stata(PATH, write_index=False, version=118,
                variable_labels=LABELS)

    # ---- prove nothing else moved -----------------------------------
    after = pd.read_stata(PATH)
    assert list(after.columns) == list(before.columns), "column drift"
    assert len(after) == len(before), "row count changed"
    for c in before.columns:
        a = before[c].to_numpy(float)
        b = after[c].to_numpy(float)
        assert np.array_equal(a, b, equal_nan=True), f"{c} changed"
    got = declared_types(PATH)
    bad = {k: (got.get(k), v) for k, v in WANTED.items()
           if got.get(k) != v}
    assert not bad, f"storage types not as intended: {bad}"
    print(f"[237] {PATH}")
    print(f"      {len(after):,} rows, values identical, "
          "ValFloat now Stata `float`, all nine variables labelled.")


if __name__ == "__main__":
    main()
