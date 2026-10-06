# -*- coding: utf-8 -*-
"""BACKLOG 158 and 159 - two claims the software made about itself.

They look unrelated and they are the same defect: a module stating a
property it did not have.

  158  selfpot.radius_for_k's docstring said "cells are square by
       construction" while hex.py handed it a hexagon's width, so the
       area was 10,000 m2 where the cell holds 8,660.
  159  meta.py's docstring said "written progressively: the file
       exists from start_run onward, so a crashed run still leaves a
       record". Nothing was written until finalize(), and both GUI
       doors used the constructor that writes nothing.

Every test here was broken on purpose first; what each was broken with
is in its docstring, because "I checked" is not evidence a later
session can use.
"""
import io
import json
import math
import os
from contextlib import redirect_stdout

import numpy as np
import pandas as pd
import pytest

from equipop import selfpot
from equipop.cells import CellData, build_cells
from equipop.fastcounts import run_knn_counts
from equipop.hex import build_hex_cells
from equipop.meta import RunLog, record, sidecar_for


def _hush(fn, *a, **kw):
    buf = io.StringIO()
    with redirect_stdout(buf):
        return fn(*a, **kw)


# =====================================================================
# 158 - THE CELL'S SHAPE DECIDES ITS AREA
# =====================================================================

def test_158_the_square_path_is_an_exact_identity():
    """BROKEN WITH: changing SHAPES["square"] away from exactly 1.0.

    THE WHOLE SAFETY ARGUMENT FOR THIS CHANGE. Every published EquiPop
    result used square cells, so if the square factor is anything but
    exactly 1.0 a number moves somewhere. Checked against the formula
    as it stood before 1.52, not against a stored expectation, so this
    cannot drift with the code it guards.
    """
    for u in (10.0, 100.0, 1000.0, 37.5):
        for k, n in ((1, 1), (5, 10), (50, 100), (99, 100), (1, 1000)):
            for s in (0.0, 0.5, 1.0):
                pre_152 = (0.0 if s <= 0 else
                           s * math.sqrt(u ** 2 * min(k, n)
                                         / (n * math.pi)))
                assert selfpot.radius_for_k(u, k, n, s) == pre_152
        for s in (0.0, 1.0):
            assert selfpot.decay_distance(u, s) == \
                s * selfpot.MEAN_INTRACELL * u


def test_158_the_hexagon_constants_are_derived_not_guessed():
    """BROKEN WITH: perturbing either constant by 1e-6.

    Both are closed forms and both are checked against numerical
    integration here, because a constant nobody can re-derive is a
    constant nobody can correct. The mean-distance one is the integral
    of r over the hexagon divided by its area, taken in polar
    coordinates over one of the twelve congruent sectors where the
    boundary is r(theta) = h / cos(theta).
    """
    quad = pytest.importorskip("scipy.integrate").quad
    h = 0.5                       # apothem of a hexagon of width 1
    num, _ = quad(lambda t: (h / math.cos(t)) ** 3 / 3.0,
                  0, math.pi / 6, epsabs=1e-14)
    den, _ = quad(lambda t: (h / math.cos(t)) ** 2 / 2.0,
                  0, math.pi / 6, epsabs=1e-14)
    assert selfpot.HEX_MEAN_INTRACELL == pytest.approx(num / den,
                                                       abs=1e-12)
    # area: twelve sectors of the same integrand
    assert selfpot.HEX_AREA_FACTOR == pytest.approx(den * 12, abs=1e-12)
    # and the review's own numbers, which is what was reported
    assert selfpot.cell_area(100.0, "hex") == pytest.approx(8660.25,
                                                            abs=0.01)
    assert selfpot.radius_for_k(100.0, 50.0, 100.0) == \
        pytest.approx(39.89, abs=0.01)
    assert selfpot.radius_for_k(100.0, 50.0, 100.0, shape="hex") == \
        pytest.approx(37.13, abs=0.01)


def test_158_the_decay_distance_uses_the_shapes_own_constant():
    """BROKEN WITH: pointing the hex entry at MEAN_INTRACELL.

    The SECOND half of 158, and the one easiest to fix halfway. The
    radius is area-based; the intra-cell decay distance is a mean
    distance, a different constant with a different derivation. Fixing
    the area and leaving 0.3826 in place would have left the decay
    weight on the origin cell 9% out - on the mass the run knows least
    about, carrying the largest single weight in the calculation.
    """
    assert selfpot.decay_distance(100.0) == pytest.approx(38.26,
                                                          abs=0.01)
    assert selfpot.decay_distance(100.0, shape="hex") == \
        pytest.approx(35.10, abs=0.01)
    assert selfpot.decay_distance(100.0, shape="hex") < \
        selfpot.decay_distance(100.0)


def test_158_the_shape_travels_on_the_data():
    """BROKEN WITH: dropping cell_shape="hex" from hex.py.

    The engines cannot ask a length what shape it is. Before this, the
    only thing build_hex_cells told them was `unit_size = hex_size`,
    which is a number that looks exactly like a square's side - which
    is why the defect survived from 1.29.6 to 1.52 without anyone
    seeing it in a diff.
    """
    pts = pd.DataFrame({"x": [50.0, 150.0, 250.0, 120.0],
                        "y": [50.0, 50.0, 50.0, 180.0]})
    hx = _hush(build_hex_cells, pts, "x", "y", hex_size=100.0)
    assert hx.cell_shape == "hex"
    assert build_cells(pd.DataFrame({"x": [50.0], "y": [50.0]}),
                       "x", "y").cell_shape == "square"
    assert CellData(E=np.array([0]), N=np.array([0]),
                    n=np.array([1])).cell_shape == "square"


def test_158_a_hex_run_differs_from_a_square_one_by_the_right_factor():
    """BROKEN WITH: not threading shape= into fastcounts.

    The engine half. Driving selfpot correctly is not the same as the
    ENGINE driving it correctly - BACKLOG 95's lesson about a guard
    whose test took the shortest path. So this goes through
    run_knn_counts and compares the numbers, and the factor is exactly
    1/sqrt(sqrt(3)/2) wherever the origin cell decides the radius.
    """
    rng = np.random.default_rng(3)
    pts = pd.DataFrame({"x": rng.uniform(0, 600, 1200),
                        "y": rng.uniform(0, 600, 1200)})
    hx = _hush(build_hex_cells, pts, "x", "y", hex_size=100.0)
    import copy
    as_square = copy.deepcopy(hx)
    as_square.cell_shape = "square"
    d_hex = _hush(run_knn_counts, hx, [5])["Dist_5"].to_numpy()
    d_sq = _hush(run_knn_counts, as_square, [5])["Dist_5"].to_numpy()
    inside = d_hex > 0
    assert inside.any(), "no origin resolved k inside its own cell"
    ratio = d_sq[inside] / d_hex[inside]
    assert ratio == pytest.approx(1.0 / math.sqrt(math.sqrt(3) / 2))
    assert (d_hex[inside] < d_sq[inside]).all(), \
        "the hex radius must be SMALLER - a hexagon holds less"


def test_158_an_unknown_shape_is_refused_rather_than_assumed():
    """BROKEN WITH: `SHAPES.get(shape, SHAPES["square"])`.

    The tempting line, and the defect this item IS: silently treating
    an unknown shape as a square is exactly how a hexagon came to be
    charged 10,000 m2 for eight years. A shape decides an area; it
    cannot be guessed.
    """
    with pytest.raises(ValueError, match="unknown cell shape"):
        selfpot.radius_for_k(100.0, 5.0, 10.0, 1.0, shape="triangle")
    with pytest.raises(ValueError, match="unknown cell shape"):
        selfpot.decay_distance(100.0, shape="octagon")


# =====================================================================
# 159 - A RECORD THAT SURVIVES THE RUN THAT WROTE IT
# =====================================================================

def test_159_the_record_exists_before_the_run_finishes(tmp_path):
    """BROKEN WITH: `self._path = Path(path) if path else None`
    followed by no flush - i.e. removing the _flush() from __init__,
    or having record() ignore `destination`.

    THE FAULT. The module docstring promised "the file exists from
    start_run onward, so a crashed run still leaves a record", and
    nothing was written until finalize().
    """
    dest = str(tmp_path / "out.gpkg|layername=k100")
    rl = record("counts", 1234, {}, destination=dest)
    side = tmp_path / "out.k100.meta.json"
    assert side.exists(), "nothing on disk before the run finished"
    doc = json.loads(side.read_text())
    assert doc["run"]["status"] == "running"
    assert doc["data"]["input_rows"] == 1234
    assert rl is not None


def test_159_every_recording_call_reaches_disk(tmp_path):
    """BROKEN WITH: removing any single _flush() from the recording
    methods.

    "Progressive" is not one write at the start. A record whose events
    and settings only appear at the end tells a crashed run's reader
    nothing about what it was doing.
    """
    dest = str(tmp_path / "out.shp")
    rl = record("counts", 10, {}, destination=dest)
    side = tmp_path / "out.meta.json"

    rl.doc["settings"].update({"k_values": [100]})
    rl.set_data(rows_seen=10)
    assert json.loads(side.read_text())["settings"] == {"k_values": [100]}

    rl.event("warning", "6 malformed rows dropped", n=6)
    assert len(json.loads(side.read_text())["events"]) == 1

    rl.set_output(destination=dest, layer=None)
    assert "output" in json.loads(side.read_text())["run"]

    rl.add_input(str(tmp_path / "in.gpkg"), rows=10)
    assert len(json.loads(side.read_text())["inputs"]) == 1


def test_159_a_failed_write_does_not_destroy_the_record(tmp_path):
    """BROKEN WITH: `self._path.write_text(...)`, the original.

    FIRST VERSION OF THIS TEST COULD NOT FAIL. It looped, re-read the
    file and asserted it parsed - which it does under `write_text` too,
    because a single-threaded reader never observes the window between
    truncating and filling. The break-check said so: putting
    `write_text` back failed nothing. "It is atomic" is not observable
    from one thread; what IS observable is the consequence, so that is
    what this asserts.

    `write_text` opens for writing, which EMPTIES THE FILE, and only
    then serialises. If serialising raises - an object json cannot
    handle, a full disk - the previous record is already gone and the
    new one was never written. Written beside and renamed, a failed
    write leaves the last good record exactly where it was. Same fix as
    BACKLOG 344 made to bigrun's manifest, for the same reason.
    """
    side = tmp_path / "out.meta.json"
    rl = record("counts", 10, {}, destination=str(tmp_path / "out.shp"))
    rl.event("info", "a step worth keeping")
    good = side.read_text()
    assert json.loads(good)["events"]

    class Unserialisable:
        def __repr__(self):
            raise RuntimeError("and repr fails too, so default=str cannot")

    rl.doc["events"].append({"detail": Unserialisable()})
    rl._flush()                       # must not raise, must not destroy

    assert side.exists(), "the record was destroyed by a failed write"
    assert side.read_text() == good, \
        "a failed write left something other than the last good record"
    assert json.loads(side.read_text())["events"]
    assert [f for f in os.listdir(tmp_path) if ".tmp." in f] == [], \
        "a failed write left a temp file behind"


def test_159_one_run_leaves_one_record(tmp_path):
    """BROKEN WITH: changing EITHER naming rule so the two disagree -
    the sidecar_for() layer branch, or finalize's `out.stem`.

    FIRST WRITTEN as "finalize keeps the file the run was writing",
    broken with "make finalize recompute the path" - and the
    break-check showed that does not fail it, because the two rules
    AGREE: sidecar_for("out.gpkg|layername=k100") and finalize's
    derivation from "out.k100.gpkg" are the same file. That agreement
    is the design working, so it is what this test should assert; the
    docstring was describing a different test.

    The agreement is what keeps one run to one record now that the log
    is opened before the run and closed after it. If the two rules ever
    drift, the record is opened at one path and finalized at another,
    and the first is left frozen at "running" beside a second that
    claims success.
    """
    dest = str(tmp_path / "out.gpkg|layername=k100")
    rl = record("counts", 10, {}, destination=dest)
    side = tmp_path / "out.k100.meta.json"
    assert json.loads(side.read_text())["run"]["status"] == "running"

    rl.set_output(destination=dest, layer="k100")
    rl.finalize({"N_100": [1, 2, 3]}, str(tmp_path / "out.k100.gpkg"))

    sidecars = sorted(f for f in os.listdir(tmp_path)
                      if f.endswith(".meta.json"))
    assert sidecars == ["out.k100.meta.json"], \
        f"one run left {len(sidecars)} records: {sidecars}"
    assert json.loads(side.read_text())["run"]["status"] == "completed"
    assert "moved_from" not in json.loads(side.read_text())["run"], \
        "the two naming rules disagreed about where this run's " \
        "record belongs"


def test_159_a_second_destination_is_recorded_not_hidden(tmp_path):
    """BROKEN WITH: dropping the `moved_from` branch.

    The honest handling of the case the entry warned about: if finalize
    really is handed a different output, the record follows it AND says
    where it was being written before, so a stale file beside the first
    destination is explained rather than mysterious.
    """
    rl = record("counts", 10, {},
                destination=str(tmp_path / "first.shp"))
    rl.finalize({"N_100": [1]}, str(tmp_path / "second.shp"))
    doc = json.loads((tmp_path / "second.meta.json").read_text())
    assert doc["run"]["status"] == "completed"
    assert doc["run"]["moved_from"].endswith("first.meta.json")


@pytest.mark.parametrize("dest", [
    "memory:out", "TEMPORARY_OUTPUT", "", "ogr:dbname=x",
    "/no/such/folder/out.shp",
])
def test_159_no_file_destination_means_no_sidecar(tmp_path, dest):
    """BROKEN WITH: returning a path for any of these.

    QGIS's OWN DEFAULT is a temporary layer, so this is the common
    case, not the edge. There is nowhere to put a sidecar and the
    record is printed to the log instead - which is a real limit, and
    the point of 159 is that it is now stated rather than disguised by
    a docstring promising otherwise.
    """
    assert sidecar_for(dest) is None
    rl = record("counts", 10, {}, destination=dest)
    assert rl._path is None
    assert [f for f in os.listdir(tmp_path) if f.endswith(".json")] == []


def test_159_the_layer_rule_is_the_one_write_provenance_uses(tmp_path):
    """BROKEN WITH: changing either copy of the naming rule.

    BACKLOG 348 gave each layer of a GeoPackage its own sidecar, with
    the rule written inside write_provenance. 159 needed the SAME
    answer before the run, to open the log at the right file. A rule
    two places need is a rule that belongs in one, so write_provenance
    now calls sidecar_for() too - and if they ever disagree, the record
    is opened at one path and finalized at another.
    """
    for dest, want in (
            ("out.gpkg|layername=k20", "out.k20.meta.json"),
            ("out.gpkg|layername=k800", "out.k800.meta.json"),
            ("out.shp", "out.meta.json"),
            ("out.gpkg|layername=odd name/x", "out.odd_name_x.meta.json"),
    ):
        got = sidecar_for(str(tmp_path / dest))
        assert os.path.basename(got) == want, dest
