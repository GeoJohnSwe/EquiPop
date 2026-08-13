# -*- coding: utf-8 -*-
"""test_conformance_proportional.py - BACKLOG 162.

The shipped conformance key is pinned to `whole`, and has to be: it
asks for a mean, a median and a Gini, and `proportional` refuses
those until weighted statistics land (BACKLOG 118).

But from 1.30 the DEFAULT is proportional. So until this file
existed, both doors were certified under a mode most runs will never
use, and the mode nearly every run WILL use was checked by nothing at
all. That is not a theoretical gap: BACKLOG 108 was a silent
corruption that survived eight published releases because the
reference and treatment logic is written twice and only one copy was
ever exercised.

This key asks only for what proportional can compute - counts, shares
and distances - and holds both doors to it.

Each test was checked by breaking it on purpose:

  * dropping `overshoot_mode` from the QGIS kw dict      -> 2 fails
  * `if False:` around _run_tool's overshoot line        -> 3 fails
  * regenerating the key under `whole`                   -> 1,2,3 fail
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "qgis"))

import qgis_stub                                       # noqa: E402
qgis_stub.install()

from qgis.core import QgsProcessingFeedback            # noqa: E402
from equipop_qgis.alg_counts import (CountsAndShares,  # noqa: E402
                                     OVERSHOOT_VALUES)
from equipop.doors import reference as R               # noqa: E402

SPEC = R.SPEC_PROPORTIONAL
IDX = OVERSHOOT_VALUES.index(SPEC["overshoot"])


# ------------------------------------------------- the stored answer
def test_the_second_key_ships_inside_the_package():
    import equipop
    pkg = os.path.dirname(os.path.abspath(equipop.__file__))
    path = R.REFERENCE_PROPORTIONAL_CSV
    assert os.path.abspath(path).startswith(pkg + os.sep)
    assert os.path.exists(path)


def test_the_second_key_is_written_in_the_same_pinned_format():
    """A Swedish machine writes decimal COMMAS. The first key has
    been guarded against that since 1.19; a second key that is not is
    a second way for the same fault to arrive."""
    raw = open(R.REFERENCE_PROPORTIONAL_CSV, encoding="utf-8").read()
    head, first = raw.split("\n")[0], raw.split("\n")[1]
    assert head.count(",") == first.count(",")
    assert "." in first and "\r" not in raw


def test_1_the_shipped_second_key_still_matches_the_core():
    """REGRESSION LOCK, the same doctrine as the first key: if this
    fails, either an engine changed or the key is stale. Regenerate
    deliberately with `python -m equipop.doors.reference` and say so
    in the release - do not relax the tolerance."""
    rep = R.compare(R.generate("proportional"), key="proportional")
    assert rep["ok"], R.explain(rep)
    assert rep["rows_compared"] == 2360


def test_the_two_keys_really_are_different_answers():
    """A second key that happened to equal the first would prove
    nothing while looking like coverage. Under `whole` the ring is
    taken entire and N_400 overshoots; under `proportional` it is
    exactly 400 everywhere, which is the mode's defining property and
    is worth asserting rather than assuming."""
    whole = R.load_reference("whole")
    prop = R.load_reference("proportional")
    assert (prop["N_400"] == 400).all(), \
        "proportional did not make N_k exactly k"
    assert whole["N_400"].max() > 400, \
        "the whole-ring key shows no overshoot at all - wrong key?"
    # and the difference reaches the measure the item is ABOUT
    assert not np.allclose(whole["R_count_group_400"],
                           prop["R_count_group_400"])


def test_the_second_key_carries_no_column_no_door_can_produce():
    """`proportional` refuses medians, percentiles and Ginis. A key
    that listed them would be a promise no door could keep, and the
    door would be reported as broken for obeying the rule."""
    cols = set(R.load_reference("proportional").columns)
    forbidden = [c for c in cols
                 if c.split("_")[0] in ("Med", "Gini", "Mean", "Nv")]
    assert not forbidden, (
        f"the proportional key carries {forbidden}, which the mode "
        "itself refuses to compute")
    assert {"N_400", "Dist_400", "T_count_group_400",
            "R_count_group_400", "N_r800"} <= cols


def test_what_counts_as_exact_follows_the_mode():
    """Under `whole`, T_k is a number of PEOPLE and must match
    exactly. Under `proportional` it is a FRACTION of people reached
    by multiplying, so bit-equality would assert something the
    mathematics does not claim. N_k stays exact either way."""
    assert "T_" in R.EXACT_PREFIXES
    assert "T_" not in SPEC["exact_prefixes"]
    assert "N_" in SPEC["exact_prefixes"]
    # and the rule is really applied, not merely declared
    drifted = R.generate("proportional")
    drifted["T_count_group_400"] *= (1 + 1e-12)
    assert R.compare(drifted, key="proportional")["ok"]
    drifted["N_400"] += 1
    assert not R.compare(drifted, key="proportional")["ok"]


# ------------------------------------------------------- the doors
@pytest.fixture(scope="module")
def qgis_output():
    alg = CountsAndShares()
    alg.initAlgorithm()
    p = {"layer": qgis_stub.gridby_source(), "outfc": "memory:out",
         "refmode": [1], "pop": SPEC["weight"],
         "treatmode": [1], "treat": ["count_group"],
         "k": "400", "r": "800", "unit": SPEC["unit_size"],
         "overshoot": [IDX]}
    alg.processAlgorithm(p, None, QgsProcessingFeedback())
    return p["_sinks"]["outfc"].to_frame()


def test_2_the_qgis_door_matches_the_proportional_key(qgis_output):
    rep = R.compare(qgis_output, key="proportional")
    assert rep["ok"], R.explain(rep)
    assert rep["rows_compared"] == 2360


def test_3_the_arcgis_door_matches_the_proportional_key():
    import test_arcgis_stub as H
    from equipop.datasets import load

    p = load("gridby")["people"]
    table = pd.DataFrame({"OBJECTID": np.arange(1, len(p) + 1),
                          "SHAPE@X": p.x.values, "SHAPE@Y": p.y.values,
                          "count_all": p.count_all.values,
                          "count_group": p.count_group.values})
    state = H._install_fake_arcpy(table)
    pyt = H._load_pyt()

    class _Quiet:
        def addMessage(self, _): pass
        addWarningMessage = addErrorMessage = addMessage

    pyt._run_tool("counts", "lyr", _Quiet(),
                  treat_fields=["count_group"],
                  weight_field=SPEC["weight"], k_text="400",
                  r_text="800", unit=SPEC["unit_size"],
                  overshoot=SPEC["overshoot"])

    out = state["table"].rename(columns={"SHAPE@X": "x",
                                         "SHAPE@Y": "y"})
    rep = R.compare(out, key="proportional")
    assert rep["ok"], R.explain(rep)
    assert rep["rows_compared"] == 2360


def test_a_named_key_that_does_not_exist_is_refused_by_name():
    with pytest.raises(ValueError, match="no conformance key"):
        R.compare(pd.DataFrame({"x": [], "y": []}), key="sampled")
