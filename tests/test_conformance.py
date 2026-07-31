"""The cross-door conformance reference.

Gridby's planted truths prove one door is sane. This proves two
doors AGREE - which matters for teaching, because a student in QGIS
and a student in ArcGIS Pro should get the same numbers out of the
same town, and small disagreements are exactly the kind neither
would notice.

Note what test_the_shipped_reference_still_matches_the_core does: it
is a REGRESSION LOCK. Any deliberate change to an engine will fail
it, and the fix is to regenerate the reference on purpose - never to
loosen the test.
"""
import os

import numpy as np
import pandas as pd
import pytest

import equipop
from equipop.doors import reference as R


@pytest.fixture(scope="module")
def fresh():
    return R.generate()


# ------------------------------------------------- the stored answer
def test_the_reference_ships_inside_the_package():
    pkg = os.path.dirname(os.path.abspath(equipop.__file__))
    assert os.path.abspath(R.REFERENCE_CSV).startswith(pkg + os.sep)
    assert os.path.exists(R.REFERENCE_CSV)


def test_the_reference_is_written_in_the_pinned_format():
    """A Swedish machine writes decimal COMMAS. If the reference were
    ever regenerated into that locale it would still look fine and
    would silently stop being readable elsewhere."""
    raw = open(R.REFERENCE_CSV, encoding="utf-8").read()
    head, first = raw.split("\n")[0], raw.split("\n")[1]
    assert head.count(",") == first.count(","), \
        "field count differs between header and first row - decimal " \
        "commas have crept in"
    assert "." in first, "no decimal points found - wrong locale?"
    assert "\r" not in raw, "line endings are not plain \\n"


def test_the_reference_covers_both_tools():
    """Counts & Shares AND Value Statistics - a door is not finished
    if only half of it is judged."""
    cols = set(R.load_reference().columns)
    assert {"N_400", "T_minority_400", "R_minority_400",
            "Dist_400"} <= cols                       # counts engine
    assert {"Mean_count_group_400", "Gini_count_group_400",
            "Nv_count_group_400"} <= cols             # stats engine
    assert {"N_r800", "T_minority_r800"} <= cols      # radius path


def test_the_shipped_reference_still_matches_the_core(fresh):
    """REGRESSION LOCK. If this fails, either an engine changed or
    the reference is stale. Regenerate deliberately with
    `python -m equipop.doors.reference` and say so in the release -
    do not relax the tolerance."""
    rep = R.compare(fresh)
    assert rep["ok"], R.explain(rep)
    assert rep["rows_compared"] == 2360


# ------------------------------------------------- the comparison
def test_the_truth_passes(fresh):
    assert R.compare(fresh)["ok"] is True


def test_one_miscounted_person_is_caught_and_located(fresh):
    """Counts are whole people: 407 where the core says 406 is
    wrong, not imprecise."""
    bad = fresh.copy()
    bad.loc[100, "N_400"] += 1
    rep = R.compare(bad)
    assert not rep["ok"]
    d = rep["columns_differing"]["N_400"]
    assert d["rule"] == "exact" and d["n_rows_differing"] == 1
    assert d["worst_row"]["door"] - d["worst_row"]["reference"] == 1
    assert "N_400" in R.explain(rep)


def test_harmless_floating_point_drift_is_tolerated(fresh):
    """A door may reach the same distance by a different order of
    operations. That is not a disagreement."""
    drift = fresh.copy()
    drift["Dist_400"] = drift["Dist_400"] * (1 + 1e-12)
    assert R.compare(drift)["ok"]


def test_rounding_distances_is_not_tolerated(fresh):
    """A door that reports whole metres has changed the answer."""
    rough = fresh.copy()
    rough["Dist_400"] = rough["Dist_400"].round(0)
    rep = R.compare(rough)
    assert not rep["ok"] and "Dist_400" in rep["columns_differing"]


def test_row_order_does_not_matter(fresh):
    """Doors are free to return rows in their own order; matching is
    on the coordinates."""
    shuffled = fresh.sample(frac=1, random_state=3)
    assert R.compare(shuffled)["ok"]


def test_a_missing_column_is_named(fresh):
    rep = R.compare(fresh.drop(columns=["Gini_count_group_400"]))
    assert not rep["ok"]
    assert "Gini_count_group_400" in rep["missing_columns"]
    assert "Gini_count_group_400" in R.explain(rep)


def test_a_short_table_is_caught_before_anything_else(fresh):
    rep = R.compare(fresh.iloc[:100])
    assert not rep["ok"] and rep["row_mismatch"] == (2360, 100)
    assert "do not line up" in R.explain(rep)


def test_a_door_that_loses_the_coordinates_is_told_so(fresh):
    rep = R.compare(fresh.drop(columns=["x"]))
    assert not rep["ok"] and rep["missing_columns"] == ["x"]


def test_the_report_reads_as_sentences(fresh):
    """A door shows this in its message pane, so it has to be
    readable by the person running it, not only by a developer."""
    bad = fresh.copy()
    bad.loc[7, "R_minority_400"] += 0.5
    text = R.explain(R.compare(bad))
    assert text.startswith("Conformance FAILED")
    assert "Worst at x=" in text and "reference" in text


# ------------------------------------------------- the spec itself
def test_the_spec_is_written_down_not_passed_around():
    """Changing any of this changes the answer, so it lives in one
    documented place."""
    assert R.SPEC["seed"] == 1848
    assert R.SPEC["treat_are_counts"] is True, (
        "Gridby rows are weighted cells, so the treatment values are "
        "COUNTS - without this flag the minority total exceeds the "
        "population and shares climb above 1")


def test_the_reference_recovers_gridbys_planted_gradient():
    """A sanity floor under the whole thing: if the stored table did
    not show the west-east gradient that was planted in the town, it
    would be the wrong table however self-consistent it was."""
    ref = R.load_reference()
    west = ref.loc[ref.x < 1000, "R_minority_400"].mean()
    east = ref.loc[ref.x > 5000, "R_minority_400"].mean()
    assert west < 0.18 and east > 0.50 and east - west > 0.3
