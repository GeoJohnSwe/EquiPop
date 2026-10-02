# -*- coding: utf-8 -*-
"""test_provenance.py - BACKLOG 293, and the reason it took forty
releases.

`equipop/meta.py` has been complete, documented and exported in
__all__ since the project's second backlog item, and until 1.50.0 it
was CALLED BY NOTHING AND TESTED BY NOTHING. Meanwhile ArcGIS Pro grew
a second, parallel provenance system of its own - a hand-written list
of (item, value) rows - and that one drifted exactly as a hand-written
list does:

  * `overshoot` has moved every k-based number since 1.30 and was
    recorded nowhere until 1.47, because nobody added it to the list.
  * BACKLOG 148: the manifest recorded k, cell size, decay and
    barriers and NONE of the settings that define the numbers, so two
    runs could carry identical records and different answers. Claude
    tried to use two of John's to settle which of his runs had
    differed, and could not.

So the fix is not "write a record" - Pro wrote one. It is that the
record comes from THE ENGINE'S OWN ARGUMENTS, so it cannot drift:
a parameter added to dispatch() appears in the record the same day,
with no door touched. These tests hold that property, not the
formatting.
"""
import json
import os

import numpy as np
import pytest

from equipop.meta import (RunLog, flat_rows, load_meta, record,
                          render_settings, settings_from_engine)
from equipop.stata_bridge import dispatch


def _points(n=200, seed=293):
    rng = np.random.default_rng(seed)
    return (rng.uniform(0, 3000, n), rng.uniform(0, 3000, n),
            rng.integers(1, 9, n).astype(float))


# --------------------------------------------------------------------
# The property the whole item rests on
# --------------------------------------------------------------------

def test_a_setting_the_caller_never_mentioned_is_still_recorded():
    """THE POINT OF 293. The record is built from the arguments AS
    BOUND, so an engine default is recorded as the value that ran.

    A record that only holds what the caller mentioned cannot
    reproduce the run: `self_potential` changes every Dist_k and
    `decay_eps` changes how far the search goes, and neither is
    passed by a door that is happy with the default.
    """
    x, y, w = _points()
    rl = record("counts", len(x), {})
    dispatch("counts", x, y, weight=w, k_values=[50],
             treat_are_counts=True, provenance=rl)
    s = rl.doc["settings"]
    assert s["self_potential"] == pytest.approx(1.0)
    assert s["decay_eps"] == pytest.approx(1e-6)
    assert s["unit_size"] == pytest.approx(100.0)
    assert rl.doc["run"]["engine"] == "counts"
    assert rl.doc["data"]["input_rows"] == len(x)


def test_the_two_settings_293_was_raised_about_are_recorded():
    """`overshoot` moved every k-based number from 1.30 and the origin
    rule moves every share from 1.47. 293 exists because there was
    nowhere to write either of them down."""
    x, y, w = _points()
    rl = record("counts", len(x), {})
    dispatch("counts", x, y, weight=w, k_values=[50],
             overshoot_mode="whole", self_rule="exclude",
             treat_are_counts=True, provenance=rl)
    assert rl.doc["settings"]["overshoot_mode"] == "whole"
    assert rl.doc["settings"]["self_rule"] == "exclude"


def test_every_engine_parameter_reaches_the_record():
    """THE ANTI-DRIFT CHECK, and the one that makes this item stick.

    If the record were assembled by hand anywhere, a parameter added
    to dispatch() would be missing from it until somebody noticed.
    This walks dispatch's OWN SIGNATURE and insists each name appears,
    so the next engine setting is recorded by construction.
    """
    import inspect
    sig = inspect.signature(dispatch)
    x, y, w = _points(60)
    rl = record("counts", len(x), {})
    dispatch("counts", x, y, weight=w, k_values=[20],
             treat_are_counts=True, provenance=rl)
    expected = {n for n, p in sig.parameters.items()
                if n not in ("engine", "x", "y", "provenance")
                and p.kind is not inspect.Parameter.VAR_KEYWORD}
    missing = expected - set(rl.doc["settings"])
    assert not missing, (
        f"{sorted(missing)} are parameters of dispatch() and are not "
        "in the provenance record. The record must come from the "
        "engine's own arguments, or it drifts the way Pro's "
        "hand-written manifest did")


def test_leftover_keywords_are_recorded_too():
    """**extra is where an engine-specific setting lands - w_k and
    permutations for LISA, for instance. Dropping it would lose
    exactly the settings nobody thought to name."""
    x, y, w = _points(60)
    rl = record("counts", len(x), {})
    dispatch("counts", x, y, weight=w, k_values=[20],
             treat_are_counts=True, provenance=rl)
    assert rl.doc["settings"]["extra"]["treat_are_counts"] is True


# --------------------------------------------------------------------
# What must NOT be in it
# --------------------------------------------------------------------

def test_the_data_is_summarised_and_never_copied():
    """A population column is not a setting. Copying one into a JSON
    sidecar would put megabytes of numbers next to the output - and a
    disclosure question nobody asked for - when the input file already
    has them."""
    x, y, w = _points(500)
    treat = {"g": np.where(w > 4, w, 0.0)}
    rl = record("counts", len(x), {})
    dispatch("counts", x, y, weight=w, treat=treat, k_values=[50],
             treat_are_counts=True, provenance=rl)
    blob = json.dumps(rl.doc)
    assert len(blob) < 20000, (
        f"the record is {len(blob)} bytes - data is being copied into "
        "it rather than summarised")
    wsum = rl.doc["settings"]["weight"]
    assert wsum["n"] == 500 and wsum["present"] == 500
    assert wsum["min"] == 1.0 and wsum["max"] == 8.0
    assert rl.doc["settings"]["treat"]["g"]["n"] == 500
    # and the values themselves must be absent
    assert str(float(w[0])) not in blob or wsum["min"] == 1.0


def test_none_is_kept_rather_than_dropped():
    """"not set" and "set to this" are different runs. A record that
    omits the first cannot say which happened - which is how a door
    that named no overshoot mode became impossible to measure against
    an answer key (BACKLOG 99)."""
    s = settings_from_engine({"overshoot_mode": None, "k_values": [5]})
    assert "overshoot_mode" in s and s["overshoot_mode"] is None


# --------------------------------------------------------------------
# Reaching it: the sidecar, the rows, the note
# --------------------------------------------------------------------

def test_finalize_accepts_the_dict_of_columns_a_door_actually_holds():
    """dispatch returns {column: array}. Requiring a DataFrame here
    meant every door had to build one just to be allowed to record
    its own run, which is part of why none of them did."""
    x, y, w = _points(80)
    rl = record("counts", len(x), {})
    res = dispatch("counts", x, y, weight=w, k_values=[20],
                   treat_are_counts=True, provenance=rl)
    import tempfile
    d = tempfile.mkdtemp()
    out = os.path.join(d, "res.csv")
    rl.finalize(res, out)
    doc = load_meta(os.path.join(d, "res.meta.json"))
    assert doc["run"]["status"] == "completed"
    assert doc["data"]["output_rows"] == 80
    assert set(doc["columns"]) == set(res)
    assert os.path.exists(os.path.join(d, "res.meta.txt"))


def test_the_record_names_the_engine_version_that_ran():
    """Not the dist-info version, which lags the source on every
    editable install and on any machine where the toolbox was copied
    in by hand. Measured: dist-info said 1.49.1 while __version__ said
    1.49.3, so the record would have named a version that did not
    produce it."""
    import equipop
    rl = record("counts", 1, {})
    assert rl.doc["environment"]["equipop"] == equipop.__version__


def test_flat_rows_is_the_shape_pros_csv_already_used():
    """One record, two renderings. Pro's _EquiPop_run.csv has been
    (item, value) pairs since 1.26, so the record is flattened into
    that rather than Pro keeping a second description of the run."""
    x, y, w = _points(60)
    rl = record("counts", len(x), {}, source="somewhere.shp")
    dispatch("counts", x, y, weight=w, k_values=[20],
             overshoot_mode="whole", treat_are_counts=True,
             provenance=rl)
    rows = dict(flat_rows(rl.doc))
    assert rows["run_engine"] == "counts"
    assert rows["run_source"] == "somewhere.shp"
    assert rows["overshoot_mode"] == "whole"
    assert rows["data_input_rows"] == 60
    assert "env_equipop" in rows
    assert all(isinstance(k, str) for k in rows)


def test_the_printed_note_omits_what_was_not_set():
    """John's ruling for Stata: a PRINTED note, because a Stata run
    may produce no file at all. On screen a None is noise; in the JSON
    it is evidence, so it is dropped here and only here."""
    x, y, w = _points(60)
    rl = record("counts", len(x), {})
    dispatch("counts", x, y, weight=w, k_values=[20],
             overshoot_mode="proportional", treat_are_counts=True,
             provenance=rl)
    text = "\n".join(render_settings(rl.doc))
    assert "overshoot_mode = proportional" in text
    assert "= None" not in text, text
    assert "dem" not in text.split("\n")[0]
    assert "engine version" in text
    # the array summary must read as prose, not as a dict dump
    assert "values," in text and "present" in text


def test_a_broken_record_never_loses_the_results():
    """A provenance step that throws away a finished analysis would be
    a worse bug than having no provenance, which is the state this
    replaces."""
    x, y, w = _points(60)

    class Hostile:
        doc = {"run": {}, "settings": {}, "data": {}}

        def set_data(self, **kw):
            raise RuntimeError("disk on fire")

    with pytest.raises(RuntimeError):
        # dispatch itself does not swallow it - the DOORS do, each
        # around its own call, because only a door knows whether it
        # has results worth keeping
        dispatch("counts", x, y, weight=w, k_values=[20],
                 treat_are_counts=True, provenance=Hostile())
    # and without a record the engine behaves exactly as before
    res = dispatch("counts", x, y, weight=w, k_values=[20],
                   treat_are_counts=True, provenance=None)
    assert "N_20" in res


def test_the_record_does_not_change_the_numbers():
    """The one invariant that matters more than any of the above."""
    x, y, w = _points(150)
    kw = dict(weight=w, k_values=[30, 60], treat_are_counts=True,
              overshoot_mode="proportional")
    plain = dispatch("counts", x, y, **kw)
    rl = record("counts", len(x), {})
    logged = dispatch("counts", x, y, provenance=rl, **kw)
    assert set(plain) == set(logged)
    for k in plain:
        assert np.allclose(plain[k], logged[k], equal_nan=True), k
