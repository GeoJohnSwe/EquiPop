"""External review of 1.51.0 - nine findings, confirmed and guarded.

The FOURTH time the useful defects arrived from outside the suite.
Every one of the nine was reproduced before any code moved, and none
was dismissed. Four were fixed and tested in the same pass as the
review (F1, F5, F6, F8 - their tests live beside the features they
belong to, in test_dispatch.py, test_selfpot.py, test_labels.py and
test_continental_door.py); this file holds the five that needed
structural changes, plus the two housekeeping items the review named
in passing.

EVERY TEST HERE WAS BROKEN ON PURPOSE FIRST. The standing rule since
BACKLOG 172, and since two of this project's own tests were found to
be unfalsifiable: a test that has never failed has never been tested.
What each one was broken with is recorded in its docstring, because
"I checked" is not evidence a later session can use.

  F2  equipop/stata_bridge.py  fractional weights rounded away
  F3  equipop/bigrun.py        resume identity blind to the data
  F4  equipop/doors/demography.py  cohorts validated as pooled sets
  F7  equipop/doors/fetching.py    manifest lost on transport failure
  F9  qgis/equipop_qgis/base.py    provenance without an output identity
"""

import io
import json
import os
import re
import shutil
import sys
from contextlib import redirect_stdout
from urllib.error import URLError

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "qgis"))

from equipop.stata_bridge import dispatch, validate_weight   # noqa: E402
from equipop.cells import build_cells                        # noqa: E402
from equipop.analysis import run_knn_stats                   # noqa: E402


def _hush(fn, *a, **kw):
    buf = io.StringIO()
    with redirect_stdout(buf):
        out = fn(*a, **kw)
    return out


# =====================================================================
# F2 - FRACTIONAL WEIGHTS
# =====================================================================
# The stats dispatcher implemented "weight by population" by repeating
# each row np.round(weight) times. Exact for whole numbers; WorldPop
# counts are not whole numbers.

def _two_cells(weights, values=(0.0, 10.0)):
    return _hush(dispatch, "stats", [50.0, 150.0], [50.0, 50.0],
                 unit_size=100.0, weight=list(weights),
                 r_values=[500], values={"v": list(values)},
                 stats={"v": ["mean"]})


def test_f2_a_fractional_weight_is_a_weight_not_a_row_count():
    """BROKEN WITH: restoring `rep = np.round(w)` and the row repeat.

    Two cells, values 0 and 10, weights 0.4 and 0.6. The weighted mean
    is 6. Rounding sends 0.4 to nobody and 0.6 to one person, so the
    answer was 10 - the value of whichever row survived.
    """
    got = _two_cells([0.4, 0.6])
    assert got["Mean_v_r500"] == pytest.approx([6.0, 6.0])


def test_f2_a_population_of_fractions_does_not_vanish():
    """BROKEN WITH: the same.

    THE WORLDPOP CASE, and the severe one. Six cells each weighing
    0.4: every weight rounds to zero, so the entire population was
    deleted and every row received N = 0 and a mean of MISSING. This
    is BACKLOG 118 - measured at 50.5% of people lost on John's
    rasters, 39% in Rwanda and 69% in Denmark - reaching the Stata
    door eight versions after the cell engine learned to carry
    fractional weights.
    """
    n = 6
    got = _hush(dispatch, "stats",
                [50.0 + 100 * i for i in range(n)], [50.0] * n,
                unit_size=100.0, weight=[0.4] * n, r_values=[1000],
                values={"v": [float(i) for i in range(n)]},
                stats={"v": ["mean"]})
    assert got["N_r1000"] == pytest.approx([2.4] * n), \
        "the population rounded away"
    assert got["Mean_v_r1000"] == pytest.approx([2.5] * n)
    assert np.isfinite(got["Mean_v_r1000"]).all(), \
        "a present population produced a missing statistic"


def test_f2_the_door_agrees_with_the_engine_it_calls():
    """BROKEN WITH: the same.

    The dispatcher is a row-alignment layer over build_cells +
    run_knn_stats. Driving those two directly with the same weights
    gave 6 while the door gave 10, so the door was not a wrapper - it
    was a second, wrong implementation of the weighting.
    """
    df = pd.DataFrame({"x": [50.0, 150.0], "y": [50.0, 50.0],
                       "v": [0.0, 10.0], "pop": [0.4, 0.6]})
    cd = _hush(build_cells, df, "x", "y", value_vars=["v"],
               unit_size=100.0, weights="pop")
    direct = _hush(run_knn_stats, cd, k_values=[], r_values=[500],
                   stats={"v": ["mean"]})
    door = _two_cells([0.4, 0.6])
    assert door["Mean_v_r500"] == pytest.approx(
        direct["Mean_v_r500"].to_numpy())


def test_f2_weighting_is_scale_invariant():
    """BROKEN WITH: the same.

    The test that distinguishes a WEIGHT from a COUNT. Multiply every
    weight by ten and a weighted mean, median and Gini must not move;
    only N scales. Under row repetition the fractional run and the
    whole-number run disagreed, which is the arithmetic signature of
    counting rows instead of weighting them.
    """
    x = [50.0, 150.0, 250.0, 350.0]
    y = [50.0] * 4
    v = [1.0, 2.0, 3.0, 100.0]
    w = [0.4, 0.6, 2.5, 0.1]
    small = _hush(dispatch, "stats", x, y, unit_size=100.0, weight=w,
                  r_values=[1000], values={"v": v},
                  stats={"v": ["mean", "median", "gini"]})
    big = _hush(dispatch, "stats", x, y, unit_size=100.0,
                weight=[t * 10 for t in w], r_values=[1000],
                values={"v": v},
                stats={"v": ["mean", "median", "gini"]})
    for col in ("Mean_v_r1000", "Med_v_r1000", "Gini_v_r1000"):
        assert small[col] == pytest.approx(big[col]), col
    assert small["N_r1000"] * 10 == pytest.approx(big["N_r1000"])
    # and the mean is the one a hand calculation gives
    assert small["Mean_v_r1000"][0] == pytest.approx(
        float(np.average(v, weights=w)))


def test_f2_a_valid_n_counts_people_not_rows():
    """BROKEN WITH: the same.

    Nv_ is the denominator John ruled on in BACKLOG 168 - the people
    whose value is OBSERVED. With one of four cells missing its value,
    Nv must be the WEIGHT of the other three (0.4+2.5+0.1 = 3.0) and
    not a count of them.
    """
    got = _hush(dispatch, "stats",
                [50.0, 150.0, 250.0, 350.0], [50.0] * 4,
                unit_size=100.0, weight=[0.4, 0.6, 2.5, 0.1],
                r_values=[1000],
                values={"v": [1.0, np.nan, 3.0, 100.0]},
                stats={"v": ["mean"]})
    assert got["N_r1000"][0] == pytest.approx(3.6)
    assert got["Nv_v_r1000"][0] == pytest.approx(3.0)
    assert got["Mean_v_r1000"][0] == pytest.approx(
        float(np.average([1.0, 3.0, 100.0], weights=[0.4, 2.5, 0.1])))


def test_f2_a_zero_weight_origin_still_gets_its_own_results():
    """BROKEN WITH: removing the _add_empty_origin_cells call.

    FIRST DOCUMENTED with `members = valid`, dropping the > 0 filter -
    and the break-check showed that does NOT break it, which is a fact
    worth keeping rather than hiding. Under the fix a zero-weight row
    contributes a weight of 0.0, so admitting it as a member changes
    nothing: the old row-expansion code needed the member/origin split
    because repeating a row zero times DELETED it, and weighting makes
    that distinction unnecessary for the arithmetic. What still carries
    the rule is _add_empty_origin_cells, so that is what this guards.

    JOHN'S RULE SINCE 1.22.2: a row outside the reference population
    counts as ZERO, is nobody's neighbour, and still receives what is
    around it. The fix must not quietly repeal it.
    """
    got = _hush(dispatch, "stats", [50.0, 150.0, 250.0], [50.0] * 3,
                unit_size=100.0, weight=[0.0, 1.0, 1.0],
                r_values=[500], values={"v": [99.0, 10.0, 20.0]},
                stats={"v": ["mean"]})
    assert got["N_r500"] == pytest.approx([2.0, 2.0, 2.0])
    # 99 belongs to nobody's neighbourhood, including its own
    assert got["Mean_v_r500"] == pytest.approx([15.0, 15.0, 15.0])


def test_f2_an_all_zero_population_is_answered_not_crashed():
    """BROKEN WITH: nothing - this one guards the edge the review
    asked about. Everybody weighs zero: there is no population, so
    N is 0 and a mean is MISSING, which is the truthful answer rather
    than an exception or a zero.
    """
    got = _two_cells([0.0, 0.0])
    assert got["N_r500"] == pytest.approx([0.0, 0.0])
    assert np.isnan(got["Mean_v_r500"]).all()


def test_f2_large_weights_need_no_row_expansion():
    """BROKEN WITH: the row repeat, which took 3.25 s and ~200 MB to
    materialise 5,000,000 rows from two.

    Not a speed test - a CEILING test, and its FIRST VERSION WAS NOT
    ONE: it asserted the mean and N, both of which row expansion gets
    right, just slowly, so it passed against the behaviour its own
    docstring named. The break-check caught that. What distinguishes
    the two implementations is HOW MANY ROWS THE BUILDER SEES, which
    build_cells prints, so that is what this reads. Municipal or
    county totals are ordinary Stata input, and under expansion the
    memory needed grew with the POPULATION rather than with the data.
    """
    buf = io.StringIO()
    with redirect_stdout(buf):
        got = dispatch("stats", [50.0, 150.0], [50.0, 50.0],
                       unit_size=100.0,
                       weight=[2_000_000.0, 3_000_000.0],
                       r_values=[500], values={"v": [0.0, 10.0]},
                       stats={"v": ["mean"]})
    said = buf.getvalue()
    rows = int(re.search(r"\[cells\] (\d+) individuals", said).group(1))
    assert rows == 2, \
        f"the builder was handed {rows:,} rows for 2 of input - the " \
        "population was materialised"
    assert got["Mean_v_r500"] == pytest.approx([6.0, 6.0])
    assert got["N_r500"] == pytest.approx([5_000_000.0] * 2)


def test_f2_a_negative_population_is_refused_by_both_machines():
    """BROKEN WITH: removing the validate_weight() calls.

    A population of minus five is not a quantity, it is an undeclared
    sentinel - the defect BACKLOG 168 closed for TREATMENTS and left
    open for the weight itself. Worse, the two machines disagreed
    about it: machine 1 summed it (N = 5) and machine 2 zeroed it
    (N = 10), so the same file gave two different populations
    depending on which engine read it.
    """
    for engine, kw in (("counts", {}),
                       ("stats", {"values": {"v": [0.0, 10.0]},
                                  "stats": {"v": ["mean"]}})):
        with pytest.raises(ValueError) as e:
            _hush(dispatch, engine, [50.0, 150.0], [50.0, 500.0],
                  unit_size=100.0, weight=[-5.0, 10.0],
                  r_values=[500], **kw)
        # The BEHAVIOUR is the refusal; the message's wording belongs
        # to 351's test below. This used to match the phrase "cannot
        # be negative" and so failed when 351 improved the message
        # while leaving the guard exactly as it was - handover shape 7.
        assert "-5" in str(e.value), \
            f"{engine} refused without naming the offending value"


def test_f2_a_missing_population_is_a_blank_not_an_error():
    """BROKEN WITH: raising on non-finite weights instead of zeroing
    them.

    The other half of the rule, and the reason validate_weight refuses
    ONLY negatives: Stata's missing arrives as a huge float, and a
    blank count means nobody - which still gets its own results.
    """
    validate_weight([np.nan, 1.0, np.inf])           # no raise
    got = _hush(dispatch, "stats", [50.0, 150.0, 250.0], [50.0] * 3,
                unit_size=100.0, weight=[np.nan, 1.0, 1.0],
                r_values=[500], values={"v": [99.0, 10.0, 20.0]},
                stats={"v": ["mean"]})
    assert got["N_r500"] == pytest.approx([2.0, 2.0, 2.0])


def test_f2_build_cells_refuses_a_negative_weight_column():
    """BROKEN WITH: removing the neg check in build_cells.

    The guard at the door AND at the engine, because build_cells has
    its own callers - rasterfolder passes a raster's weight column
    straight in, and a raster's NoData is frequently -9999.
    """
    df = pd.DataFrame({"x": [50.0, 150.0], "y": [50.0, 50.0],
                       "v": [1.0, 2.0], "pop": [-9999.0, 5.0]})
    with pytest.raises(ValueError) as e:
        _hush(build_cells, df, "x", "y", value_vars=["v"],
              unit_size=100.0, weights="pop")
    assert "-9999" in str(e.value) and "'pop'" in str(e.value), \
        "the refusal names neither the column nor the value"


def test_f2_the_empty_origin_helper_grows_every_parallel_array():
    """BROKEN WITH: deleting the value_weights loop in
    _add_empty_origin_cells, which raises IndexError in the engine.

    The helper extended E, N, n, value_arrays and binary_sums and left
    value_weights and binary_valid short. It was correct by ACCIDENT:
    both were always empty until F2's fix populated one of them. A
    zero-weight origin plus fractional weights is the combination that
    finds it.
    """
    from equipop.stata_bridge import _add_empty_origin_cells
    df = pd.DataFrame({"x": [50.0, 150.0], "y": [50.0, 50.0],
                       "v": [1.0, 2.0], "pop": [0.4, 0.6]})
    cd = _hush(build_cells, df, "x", "y", value_vars=["v"],
               unit_size=100.0, weights="pop")
    cd = _hush(_add_empty_origin_cells, cd,
               np.array([50, 150, 950]), np.array([50, 50, 950]), ["v"])
    assert len(cd.value_weights["v"]) == len(cd.value_arrays["v"]) \
        == len(cd.n)
    # and it still computes
    out = _hush(run_knn_stats, cd, k_values=[], r_values=[500],
                stats={"v": ["mean"]})
    assert len(out) == len(cd.n)


# =====================================================================
# F3 - WHAT MAKES TWO RUNS THE SAME RUN
# =====================================================================

pytest.importorskip("pyarrow", reason="bigrun writes parquet")

from equipop.bigrun import run_knn_counts_tiled, load_tiled  # noqa: E402
from equipop.decay import Decay                              # noqa: E402


def _grid_cells(pop):
    df = pd.DataFrame([(i * 100 + 50.0, j * 100 + 50.0, pop)
                       for i in range(3) for j in range(3)],
                      columns=["x", "y", "pop"])
    return _hush(build_cells, df, "x", "y", unit_size=100.0,
                 weights="pop")


def test_f3_the_same_geometry_with_different_people_is_a_different_run(
        tmp_path):
    """BROKEN WITH: dropping "cells_md5" from the params dict.

    THE FAULT. The resume identity recorded n_cells and unit_size and
    nothing about the DATA, so a folder of finished tiles was reused
    for a different population: nine cells either way, so the counts
    matched, and the earlier run's answers came back reported as
    success. Measured below - the radii genuinely differ - and a
    three-day continental run is exactly where nobody would notice.
    """
    out = str(tmp_path / "run")
    _hush(run_knn_counts_tiled, _grid_cells(10.0), k_values=[20],
          out_dir=out, tile_m=100_000.0)
    with pytest.raises(ValueError, match="DIFFERENT run"):
        _hush(run_knn_counts_tiled, _grid_cells(20.0), k_values=[20],
              out_dir=out, tile_m=100_000.0)


def test_f3_the_stale_answers_really_were_wrong(tmp_path):
    """BROKEN WITH: nothing - this establishes the stakes, so the test
    above is not guarding a difference that does not matter.

    Ten people per cell and twenty give different radii for the same
    k, so a resume that returned the first run's tiles returned WRONG
    numbers, not merely stale ones.
    """
    got = []
    for pop in (10.0, 20.0):
        out = str(tmp_path / f"run{pop}")
        _hush(run_knn_counts_tiled, _grid_cells(pop), k_values=[20],
              out_dir=out, tile_m=100_000.0)
        got.append(_hush(load_tiled, out)["Dist_20"].to_numpy())
    assert not np.allclose(got[0], got[1])


def test_f3_the_calibration_is_part_of_the_identity(tmp_path):
    """BROKEN WITH: recording only model / half_life_m / gamma, as the
    manifest used to.

    `calibration` is the setting that turns a half-life into a beta.
    The same half_life_m under half-life and half-probability gives
    different weights and different answers, and resume called the two
    the same run.
    """
    out = str(tmp_path / "run")
    cd = _grid_cells(10.0)
    _hush(run_knn_counts_tiled, cd, k_values=[20], out_dir=out,
          tile_m=100_000.0,
          decay=Decay(half_life_m=200, calibration="half-life"))
    with pytest.raises(ValueError, match="DIFFERENT run"):
        _hush(run_knn_counts_tiled, cd, k_values=[20], out_dir=out,
              tile_m=100_000.0,
              decay=Decay(half_life_m=200,
                          calibration="half-probability"))


def test_f3_a_hash_mismatch_explains_itself(tmp_path):
    """BROKEN WITH: deleting the cells_md5 branch of the message.

    Two hex strings tell a user nothing. The refusal has to say what
    differed in words they can act on.
    """
    out = str(tmp_path / "run")
    _hush(run_knn_counts_tiled, _grid_cells(10.0), k_values=[20],
          out_dir=out, tile_m=100_000.0)
    with pytest.raises(ValueError) as e:
        _hush(run_knn_counts_tiled, _grid_cells(20.0), k_values=[20],
              out_dir=out, tile_m=100_000.0)
    assert "CELL DATA differs" in str(e.value)


def test_f3_speed_only_settings_are_not_part_of_the_identity(tmp_path):
    """BROKEN WITH: adding m_neighbors or chunk to the params dict.

    The other half of a good guard: no correct configuration may trip
    it. Both of these are documented and regression-tested as
    affecting SPEED ONLY, so a user who raises chunk to go faster must
    not be told their finished run is a different analysis.
    """
    out = str(tmp_path / "run")
    cd = _grid_cells(10.0)
    _hush(run_knn_counts_tiled, cd, k_values=[20], out_dir=out,
          tile_m=100_000.0, m_neighbors=4096, chunk=4096)
    _hush(run_knn_counts_tiled, cd, k_values=[20], out_dir=out,
          tile_m=100_000.0, m_neighbors=64, chunk=7)   # no raise


@pytest.mark.parametrize("opt,a,b,col", [
    ("self_rule", "include", "exclude", "Dist_20"),
    ("overshoot_mode", "whole", "proportional", "N_20"),
])
def test_f3_the_engine_options_reach_the_engine(tmp_path, opt, a, b, col):
    """BROKEN WITH: dropping the option from the kw dict in the tile
    loop.

    FOUND WHILE FIXING F3, not by the review. run_knn_counts accepts
    self_potential, overshoot_mode, self_rule, seed and decay_eps; the
    tiled wrapper accepted NONE of them, so a continental run silently
    took the defaults and the origin rule a spatial regression needs
    was unreachable. Same shape as the r_values gap Marina's pull
    request found on the same branch (BACKLOG 340), and as the effort
    engines' missing overshoot (BACKLOG 341). Fingerprinting an option
    that cannot be varied would have been theatre.
    """
    cd = _grid_cells(10.0)
    vals = []
    for v in (a, b):
        out = str(tmp_path / f"run_{v}")
        _hush(run_knn_counts_tiled, cd, k_values=[20], out_dir=out,
              tile_m=100_000.0, **{opt: v})
        vals.append(_hush(load_tiled, out)[col].to_numpy())
    assert not np.allclose(vals[0], vals[1]), \
        f"{opt} did not change {col} - the wrapper is swallowing it"


def test_f3_the_manifest_is_replaced_not_truncated(tmp_path):
    """BROKEN WITH: `json.dump(man, open(mpath, "w"))`, the original.

    Opening a file "w" empties it before anything is written, so a
    crash in that window leaves a fragment and the whole finished run
    unresumable - the one failure this module exists to survive. The
    temp file must be gone and the manifest must parse.
    """
    out = str(tmp_path / "run")
    _hush(run_knn_counts_tiled, _grid_cells(10.0), k_values=[20],
          out_dir=out, tile_m=100.0)
    leftovers = [f for f in os.listdir(out) if ".tmp." in f]
    assert leftovers == []
    with open(os.path.join(out, "manifest.json")) as fh:
        man = json.load(fh)
    assert man["tiles"] and man["params"]["cells_md5"]


def test_f3_the_cell_fingerprint_sees_each_field_it_claims_to():
    """BROKEN WITH: hashing only E and N, or only the dict values
    without their keys.

    A digest is only as good as what it reads. Every field the
    counting engine uses must move it: the coordinates, the
    population, and each treatment's totals and observed denominators.
    """
    df = pd.DataFrame({"x": [50.0, 150.0], "y": [50.0, 250.0],
                       "g": [1.0, 0.0], "pop": [3.0, 7.0]})
    base = _hush(build_cells, df, "x", "y", binary_vars=["g"],
                 unit_size=100.0, weights="pop")
    seen = {base.fingerprint()}
    for mutate in (
            lambda c: setattr(c, "E", np.asarray(c.E) + 1),
            lambda c: setattr(c, "N", np.asarray(c.N) + 1),
            lambda c: setattr(c, "n", np.asarray(c.n, float) + 1),
            lambda c: c.binary_sums.__setitem__(
                "g", np.asarray(c.binary_sums["g"]) + 1),
            lambda c: c.binary_valid.__setitem__(
                "g", np.asarray(c.binary_valid["g"]) + 1),
    ):
        cd = _hush(build_cells, df, "x", "y", binary_vars=["g"],
                   unit_size=100.0, weights="pop")
        mutate(cd)
        fp = cd.fingerprint()
        assert fp not in seen, "a change the engine reads left the " \
                               "fingerprint untouched"
        seen.add(fp)


def test_f3_the_fingerprint_does_not_depend_on_dtype_or_dict_order():
    """BROKEN WITH: hashing `arr.tobytes()` without forcing a dtype,
    or iterating the binary dicts unsorted.

    A digest that changes for a reason the answers do not is as bad as
    one that does not change when they do: it would refuse every
    legitimate resume.
    """
    df = pd.DataFrame({"x": [50.0, 150.0], "y": [50.0, 250.0],
                       "a": [1.0, 0.0], "b": [0.0, 1.0],
                       "pop": [3.0, 7.0]})
    one = _hush(build_cells, df, "x", "y", binary_vars=["a", "b"],
                unit_size=100.0, weights="pop")
    two = _hush(build_cells, df, "x", "y", binary_vars=["b", "a"],
                unit_size=100.0, weights="pop")
    two.E = np.asarray(two.E, dtype=np.int32)
    two.n = np.asarray(two.n, dtype=np.float32)
    assert one.fingerprint() == two.fingerprint()


# =====================================================================
# F4 - COHORTS ARE PAIRS, NOT TWO SETS
# =====================================================================

from equipop.doors import demography as demo               # noqa: E402


def _labels(sexes, bands, year="2026"):
    return [f"{s}_{b:02d}_{year}" for s in sexes for b in bands]


def _all_bands(index):
    spec = demo.INDICES[index]
    return sorted(set(demo.expected_bands(spec["numerator"]))
                  | set(demo.expected_bands(spec["denominator"])))


def test_f4_a_band_present_for_one_sex_only_is_a_hole():
    """BROKEN WITH: restoring the pooled check -
    `got = {int(c.split("_")[1]) for c in have}` plus the separate
    per-sex `any(c.startswith(sx + "_"))`.

    THE FAULT. f and m across every band except m_65. The pooled age
    set was complete, because f supplied 65; both sexes appeared,
    because m was in the other bands; no gap was reported, and
    "People 65 and over per person under 15" was published with men
    aged 65-69 absent from the numerator. Two complete sets, no
    complete pair.
    """
    bands = _all_bands("ageing_index")
    labels = _labels(["f", "m"], bands)
    labels.remove("m_65_2026")
    with pytest.raises(demo.DemographyError, match="under its own name"):
        _hush(demo.plan, "ageing_index", labels)


def test_f4_the_refusal_names_the_missing_pair():
    """BROKEN WITH: reporting bare band numbers, as the pooled version
    did.

    "the numerator is incomplete" is not something a user can act on.
    "missing m_65" is a shopping list.
    """
    bands = _all_bands("ageing_index")
    labels = _labels(["f", "m"], bands)
    labels.remove("m_65_2026")
    with pytest.raises(demo.DemographyError) as e:
        _hush(demo.plan, "ageing_index", labels)
    assert "m_65" in str(e.value)


def test_f4_a_deliberate_restriction_is_still_allowed_and_recorded():
    """BROKEN WITH: raising regardless of allow_incomplete.

    BACKLOG 279's rule, unchanged: a restricted study is legitimate
    when it is CHOSEN. What must not happen is arriving at one by
    absence.
    """
    bands = _all_bands("ageing_index")
    labels = _labels(["f", "m"], bands)
    labels.remove("m_65_2026")
    p = _hush(demo.plan, "ageing_index", labels, allow_incomplete=True)
    assert p["restricted"] == {"numerator": ["m_65"]}


@pytest.mark.parametrize("index", sorted(demo.INDICES))
def test_f4_a_complete_grid_is_accepted_unchanged(index):
    """BROKEN WITH: comparing against every sex PRESENT rather than
    every sex the side COVERS - which refuses the sex ratio, whose
    numerator is men only.

    The other half of a good guard. All four indices, on a full f/m
    grid, must pass with nothing recorded as restricted.
    """
    p = _hush(demo.plan, index, _labels(["f", "m"], _all_bands(index)))
    assert p["restricted"] is None


@pytest.mark.parametrize("sexes", [("f",), ("t",)])
def test_f4_a_single_sex_folder_is_not_a_gap(sexes):
    """BROKEN WITH: making pick_sex() return ("f", "m") regardless.

    FIRST DOCUMENTED as broken by the pair check itself, and the
    break-check showed no break there reaches it: the pair check
    compares against `want["sexes"]`, which pick_sex() has already
    narrowed, so by the time this code runs an f-only folder wants
    only f. The guarantee lives in pick_sex(), and that is where the
    break has to go - which is the useful thing the break-check
    established, because it says which function this test is really
    about.

    pick_sex() narrows an index that does not care about sex to
    whatever the folder holds - one sex, or the combined 't'.
    """
    p = _hush(demo.plan, "ageing_index",
              _labels(list(sexes), _all_bands("ageing_index")))
    assert p["sexes"] == list(sexes)
    assert p["restricted"] is None


def test_f4_effective_range_is_defined_once():
    """BROKEN WITH: pasting the second definition back in.

    The review's housekeeping item. The function was defined TWICE,
    forty lines apart, so one was dead and nothing said which. They
    were not identical in source - the dead one guarded the top band
    with an extra branch - and over all 25,650 (lo, hi, plus)
    combinations the band table admits they gave ZERO differing
    results, because _band_end() already returns None for the last
    band start. The simpler one was kept. A second copy that happens
    to agree is still a second copy waiting to stop agreeing
    (BACKLOG 272's lesson, and expected_bands() carries the same note).
    """
    import ast
    src = os.path.join(ROOT, "equipop", "doors", "demography.py")
    with open(src, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    defs = [n for n in tree.body
            if isinstance(n, ast.FunctionDef)
            and n.name == "effective_range"]
    assert len(defs) == 1, \
        f"effective_range is defined {len(defs)} times; one shadows " \
        "the other and nothing says which runs"


# =====================================================================
# F7 - A FAILED FETCH MUST NOT LOSE WHAT SUCCEEDED
# =====================================================================

from equipop.doors import fetching as fetch                # noqa: E402

_TIF = b"II*\x00" + b"x" * 2000        # enough magic for the format check


def _plan(n):
    return {"provider": "fake", "iso3": "xxx",
            "planned_utc": "2026-10-03T00:00:00Z",
            "entries": [{"name": f"pop_{i}.tif",
                         "url": f"https://example.invalid/pop_{i}.tif"}
                        for i in range(n)]}


def _transport(fail_at, exc):
    import hashlib
    seen = {"n": 0}

    def get_file(url, dest, timeout=900):
        seen["n"] += 1
        if seen["n"] == fail_at:
            raise exc
        with open(dest, "wb") as fh:
            fh.write(_TIF)
        return (len(_TIF), hashlib.sha256(_TIF).hexdigest(),
                hashlib.md5(_TIF).hexdigest())
    return get_file


@pytest.mark.parametrize("exc", [
    URLError("connection reset by peer"),
    OSError(28, "No space left on device"),
    KeyboardInterrupt(),
    fetch.FetchError("a declared check failed"),
])
def test_f7_whatever_kills_a_fetch_the_provenance_survives(tmp_path, exc):
    """BROKEN WITH: `except FetchError as exc` and no per-asset
    commit() - the original.

    THE FAULT. The wrapper caught only the error this module raises
    about its OWN checks, so every way a download actually dies went
    past it: a reset connection or DNS failure (URLError), a full disk
    or read-only folder (OSError), a malformed response, the user's
    Ctrl-C. Reproduced with URLError on entry 2 of 3: file 1
    downloaded, verified, and left on disk with NO manifest at all.
    """
    folder = str(tmp_path / "dl")
    os.makedirs(folder)
    with pytest.raises(type(exc)):
        _hush(fetch.run_fetch, _plan(3), folder,
              get_file=_transport(2, exc), say=lambda *a: None)
    man = fetch.read_manifest(folder)
    assert man is not None, "a verified file was left with no provenance"
    assert [f["name"] for f in man["files"]] == ["pop_0.tif"]
    assert man["fetches"][-1]["status"] == "incomplete"


def test_f7_the_failure_is_recorded_by_class_and_message(tmp_path):
    """BROKEN WITH: `"error": str(failure)`, which is EMPTY for
    several transport errors, and omits the class for all of them.

    "timed out" and "no space left on device" are different problems
    with different answers for the user.
    """
    folder = str(tmp_path / "dl")
    os.makedirs(folder)
    with pytest.raises(OSError):
        _hush(fetch.run_fetch, _plan(3), folder,
              get_file=_transport(2, OSError(28, "No space left on device")),
              say=lambda *a: None)
    err = fetch.read_manifest(folder)["fetches"][-1]["error"]
    assert "OSError" in err and "No space left" in err


def test_f7_the_original_exception_is_not_dressed_as_a_fetcherror(tmp_path):
    """BROKEN WITH: `raise FetchError(...) from exc` in the handler.

    A transport failure and a failed EquiPop check call for different
    things from the user - retry versus investigate - so the type must
    survive the handler that records it.
    """
    folder = str(tmp_path / "dl")
    os.makedirs(folder)
    with pytest.raises(URLError):
        _hush(fetch.run_fetch, _plan(2), folder,
              get_file=_transport(1, URLError("reset")),
              say=lambda *a: None)


def test_f7_a_retry_recognises_what_arrived(tmp_path):
    """BROKEN WITH: the original, where the retry raised FetchError
    about "a file nobody fetched".

    THE CONSEQUENCE that made the lost manifest unrecoverable. With no
    record of where pop_0.tif came from, the retry refused to continue
    rather than attribute bytes it had not observed - correctly - so
    the user was stuck: unable to resume and unable to repeat without
    moving files aside by hand.
    """
    folder = str(tmp_path / "dl")
    os.makedirs(folder)
    with pytest.raises(URLError):
        _hush(fetch.run_fetch, _plan(3), folder,
              get_file=_transport(2, URLError("reset")),
              say=lambda *a: None)
    man = _hush(fetch.run_fetch, _plan(3), folder,
                get_file=_transport(99, URLError("x")),
                say=lambda *a: None)
    assert man["fetches"][-1]["status"] == "complete"
    assert sorted(f["name"] for f in man["files"]) == \
        ["pop_0.tif", "pop_1.tif", "pop_2.tif"]


def test_f7_one_fetch_log_entry_per_run_not_per_file(tmp_path):
    """BROKEN WITH: appending to man["fetches"] inside commit()
    instead of rebuilding from `prior`.

    The manifest is now written after every verified asset. Done
    naively that turns one 50-file download into 50 recorded fetches,
    and the fetch log is how BACKLOG 275 keeps track of which run
    brought which file.
    """
    folder = str(tmp_path / "dl")
    os.makedirs(folder)
    man = _hush(fetch.run_fetch, _plan(3), folder,
                get_file=_transport(99, URLError("x")),
                say=lambda *a: None)
    assert len(man["fetches"]) == 1
    assert man["fetches"][0]["status"] == "complete"
    assert [f for f in os.listdir(folder) if ".part" in f] == []


# =====================================================================
# F9 - A PROVENANCE RECORD WITHOUT AN OUTPUT IDENTITY
# =====================================================================

import qgis_stub                                           # noqa: E402
qgis_stub.install()

from qgis.core import QgsProcessingFeedback                # noqa: E402
from equipop_qgis.alg_counts import CountsAndShares        # noqa: E402


def _qgis_run(dest, folder, extra=None):
    t = pd.DataFrame([(i * 100 + 50.0, j * 100 + 50.0, 10.0)
                      for i in range(3) for j in range(3)],
                     columns=["x", "y", "Population"])
    for k, v in (extra or {}).items():
        t[k] = v
    src = qgis_stub._Source(t, "EPSG:32633",
                            source=os.path.join(folder,
                                                "in.gpkg|layername=pts"),
                            name="my points")
    alg = CountsAndShares()
    alg.initAlgorithm()
    p = {"layer": src, "unit": 100.0, "outfc": dest, "k": "20",
         "pop": ["Population"], "refmode": [1]}
    _hush(alg.processAlgorithm, p, None, QgsProcessingFeedback())
    return p["_sinks"]["outfc"].to_frame()


def _sidecars(folder):
    return sorted(f for f in os.listdir(folder)
                  if f.endswith(".meta.json"))


def test_f9_two_layers_in_one_geopackage_get_two_records(tmp_path):
    """BROKEN WITH: `path = str(dest).split("|", 1)[0]` and
    `finalize(result, path)` - the original.

    THE FAULT. A QGIS destination may carry a layer -
    "out.gpkg|layername=k20" - and the layer was split off and thrown
    away, so every layer in one GeoPackage shared out.meta.json and
    each run OVERWROTE the previous run's provenance. Nothing in the
    survivor said which layer it described. Writing several result
    layers into one container is the ordinary way to use a GeoPackage.
    """
    folder = str(tmp_path)
    _qgis_run(os.path.join(folder, "out.gpkg|layername=k20"), folder)
    _qgis_run(os.path.join(folder, "out.gpkg|layername=k800"), folder)
    assert _sidecars(folder) == ["out.k20.meta.json",
                                 "out.k800.meta.json"]
    ids, layers = set(), set()
    for name in _sidecars(folder):
        with open(os.path.join(folder, name)) as fh:
            doc = json.load(fh)
        ids.add(doc["run"]["id"])
        layers.add(doc["run"]["output"]["layer"])
        assert "layername=" in doc["run"]["output"]["destination"]
    assert layers == {"k20", "k800"}
    assert len(ids) == 2, "two runs share one run id"


def test_f9_a_plain_file_destination_is_unchanged(tmp_path):
    """BROKEN WITH: appending the layer suffix unconditionally.

    Most QGIS outputs are a bare path. The sidecar beside out.shp must
    still be out.meta.json, or every existing instruction and
    screenshot is wrong.
    """
    folder = str(tmp_path)
    _qgis_run(os.path.join(folder, "out.shp"), folder)
    assert _sidecars(folder) == ["out.meta.json"]


def test_f9_the_record_names_the_fields_the_file_holds(tmp_path):
    """BROKEN WITH: `finalize(result, ...)` instead of the renamed
    mapping.

    write() renames a result column that clashes with one of the
    input's own fields (BACKLOG 316) and DISCARDED the mapping, so the
    record documented the engine's result keys. With a source already
    carrying an N_20 the layer held N_20 and N_20b while the record
    defined only `N_20` - the SOURCE's column - so a reader looking up
    the run's own result found somebody else's field described.
    """
    folder = str(tmp_path)
    out = _qgis_run(os.path.join(folder, "out.shp"), folder,
                    extra={"N_20": 1.0})
    assert "N_20b" in out.columns and "N_20" in out.columns
    with open(os.path.join(folder, "out.meta.json")) as fh:
        doc = json.load(fh)
    assert "N_20b" in doc["columns"]
    assert doc["run"]["output"]["renamed_fields"] == {"N_20": "N_20b"}
    assert doc["run"]["output"]["carried_fields"] == ["Population", "N_20"]


def test_f9_a_renamed_field_keeps_its_definition(tmp_path):
    """BROKEN WITH: `_describe_columns(cols)` without `under`.

    FOUND BY FIXING THE TEST ABOVE. Naming the field as the file holds
    it broke its definition: the patterns in _COLUMN_DOCS describe
    EquiPop's naming convention, so `N_20b` matched nothing and was
    documented as "(no definition registered)". The definition belongs
    to the QUANTITY, so it is looked up under the original name and
    reported under the new one.
    """
    folder = str(tmp_path)
    _qgis_run(os.path.join(folder, "out.shp"), folder,
              extra={"N_20": 1.0})
    with open(os.path.join(folder, "out.meta.json")) as fh:
        doc = json.load(fh)
    doc_text = doc["columns"]["N_20b"]
    assert "k=20" in doc_text
    assert "renamed from N_20" in doc_text


def test_f9_the_input_is_identified_by_its_data_source(tmp_path):
    """BROKEN WITH: `getattr(source, "sourceName", lambda: "")()` -
    the original.

    sourceName() is the label in the layers panel ("my points"), not a
    path, so add_input() found nothing to measure. On the stub, which
    had no sourceName at all, it recorded the EMPTY STRING: Path("")
    resolves to the current directory, _md5 raised IsADirectoryError,
    and `except Exception: pass` swallowed it - so every QGIS
    provenance record in this suite carried "inputs": [] and no test
    asked. A simulator that omits a method cannot fail the code that
    needs it, which is why _Source now has both.
    """
    folder = str(tmp_path)
    _qgis_run(os.path.join(folder, "out.shp"), folder)
    with open(os.path.join(folder, "out.meta.json")) as fh:
        doc = json.load(fh)
    assert doc["inputs"], "the record identifies no input at all"
    got = doc["inputs"][0]
    assert got["path"].endswith("in.gpkg|layername=pts")
    assert got["rows"] == 9
    assert got["crs_in"] == "EPSG:32633"


def test_f9_the_text_record_names_its_own_output(tmp_path):
    """BROKEN WITH: dropping the OUTPUT block from render_txt().

    The .txt is what a QGIS user reads; the .json is what a program
    reads. A record that names its output only in the JSON names it
    only for programs.
    """
    folder = str(tmp_path)
    _qgis_run(os.path.join(folder, "out.shp"), folder,
              extra={"N_20": 1.0})
    with open(os.path.join(folder, "out.meta.txt")) as fh:
        txt = fh.read()
    assert "OUTPUT:" in txt
    assert "destination = " in txt
    assert "N_20 -> N_20b" in txt


def test_f9_a_memory_destination_still_reports_its_settings(tmp_path):
    """BROKEN WITH: removing the render_txt() loop from the in-memory
    branch of write_provenance.

    FIRST WRITTEN as `assert _sidecars(folder) == []`, which the
    break-check showed cannot fail for the right reason: forcing the
    file branch writes `memory:out.meta.json` into the WORKING
    DIRECTORY, not into the folder being inspected, so the assertion
    held while the behaviour was wrong - and it littered the repo,
    which is BACKLOG 101's complaint. It now reads what the branch
    exists to do.

    The DEFAULT destination in QGIS is a temporary layer, which has
    nowhere to put a sidecar, so the record is PRINTED to the log -
    where a QGIS user's reproducibility already lives. The settings
    must still arrive, and the layer identity with them.
    """
    t = pd.DataFrame([(i * 100 + 50.0, j * 100 + 50.0, 10.0)
                      for i in range(3) for j in range(3)],
                     columns=["x", "y", "Population"])
    src = qgis_stub._Source(t, "EPSG:32633",
                            source=str(tmp_path / "in.gpkg"),
                            name="my points")
    alg = CountsAndShares()
    alg.initAlgorithm()
    p = {"layer": src, "unit": 100.0, "outfc": "memory:out", "k": "20",
         "pop": ["Population"], "refmode": [1]}
    fb = QgsProcessingFeedback()
    _hush(alg.processAlgorithm, p, None, fb)
    said = " ".join(fb.info)
    assert "no provenance sidecar" in said
    assert "SETTINGS:" in said, \
        "the in-memory branch stopped printing the record"
    assert "OUTPUT:" in said and "memory:out" in said
    assert _sidecars(str(tmp_path)) == []


# =====================================================================
# 351 - JOHN'S QUESTION ON THE 343 RELEASE
# =====================================================================
# "What if a negative population represented the n the local has lost
# - I realize that would clash with some stats but not all. Should
# there be a warning rather than refusal?"
#
# His ruling after the reasoning below: refused, and for a good reason.
# What was wrong was the MESSAGE, which offered one cause and one
# remedy and never named the route that works.

def test_351_a_signed_quantity_works_as_a_value_variable():
    """BROKEN WITH: nothing in the guards - this is the FACT the
    refusal rests on, so it is pinned rather than asserted in prose.

    If this stopped being true, refusing a negative population would
    leave a real research question with no route at all, and the
    refusal would have to be revisited. A change or net-migration
    variable is a MEASUREMENT: it goes in values(), weighted by the
    actual headcount in pop(), and comes back as a population-weighted
    mean, median and SD per neighbourhood.

    THE WEIGHTS ARE DELIBERATELY UNEVEN. The first version gave every
    cell ten people, which made the answer the same whatever the
    weighting did - so a break that flattened every weight to 1 left
    it passing, and the break-check said so. Uneven weights plus a k
    that forces a PROPORTIONAL SHARE of the crossing cell is what
    makes this sensitive to both halves at once: that the value may be
    negative, and that it is weighted by people rather than by rows.
    """
    got = _hush(dispatch, "stats", [50.0, 150.0, 250.0], [50.0] * 3,
                unit_size=100.0, weight=[10.0, 30.0, 10.0],
                k_values=[30], values={"chg": [-50.0, 20.0, -5.0]},
                stats={"chg": ["mean", "median", "sd"]})
    # Origin 0 takes all 10 of its own cell and 20 of cell 1's 30, so
    # the mean is weighted by a FRACTION of a cell as well as by
    # population - the two things 343 made work together.
    assert got["N_30"][0] == pytest.approx(30.0)
    assert got["Mean_chg_30"][0] == pytest.approx(
        (-50.0 * 10 + 20.0 * 20) / 30.0)
    assert got["Mean_chg_30"][0] == pytest.approx(-3.333333, abs=1e-5)
    assert np.isfinite(got["SD_chg_30"]).all()
    assert np.isfinite(got["Med_chg_30"]).all()


@pytest.mark.parametrize("field", ["weight", "treat"])
def test_351_the_refusal_names_both_causes_and_the_route(field):
    """BROKEN WITH: restoring either message's single-cause form.

    The guard was right and its message was not. It named ONE cause -
    an undeclared sentinel - and one remedy, missing(). For a genuine
    change variable both are wrong advice, and the user is left with a
    refusal and nowhere to go. 1.44.3's rule: if the code knows the
    right answer, a refusal that only names the problem is a wasted
    trip.
    """
    kw = ({"weight": [-5.0, 10.0]} if field == "weight"
          else {"weight": [10.0, 10.0],
                "treat": {"chg": [-5.0, 10.0]},
                "treat_are_counts": True})
    with pytest.raises(ValueError) as e:
        _hush(dispatch, "counts", [50.0, 150.0], [50.0, 50.0],
              unit_size=100.0, k_values=[15], **kw)
    msg = str(e.value)
    assert "cannot be negative" in msg or "cannot be grown" in msg
    assert "NO DATA" in msg, "the sentinel cause stopped being named"
    assert "missing(" in msg, "the sentinel remedy stopped being named"
    assert "CHANGE" in msg, "the signed-quantity cause is not named"
    assert "values()" in msg, \
        "the message refuses without naming the route that works"


def test_351_the_weight_message_says_why_not_merely_that():
    """BROKEN WITH: dropping the clause about k and the radius.

    John's question was whether this could be a warning. It cannot,
    because the failure is in growing the neighbourhood and not in any
    statistic - so the message has to say that, or the next person
    asks the same question and gets the same non-answer.
    """
    with pytest.raises(ValueError) as e:
        _hush(dispatch, "counts", [50.0, 150.0], [50.0, 50.0],
              unit_size=100.0, k_values=[15], weight=[-5.0, 10.0])
    msg = str(e.value)
    assert "k counts PEOPLE" in msg
    assert "radius" in msg


def test_351_the_origin_rule_figure_is_the_same_in_every_copy():
    """BROKEN WITH: putting 13.4% back in selfrule.CHOICES.

    THE FIGURE EXISTED IN THREE PLACES AND ONE WAS THE RETRACTED ONE.
    selfrule.py's header explicitly supersedes an earlier 13.4% - a
    bench run with the neighbour search capped at 48 cells, which
    never reached k for remote blocks - and selfrule.CHOICES, nineteen
    lines below that correction, still said 13.4% until 1.51.2.
    Nothing rendered it, so no user saw it; the doors read
    doors/help.py, which has always said 13.6%. A third copy that
    disagrees with the other two is the defect 105 and 338 are about,
    and it had already propagated into a backlog entry and a handover
    before anybody compared them.

    This pins the copies to each other rather than to a literal, so
    the next correction has to move them together or fail here.
    """
    import re
    from equipop import selfrule
    from equipop.doors import help as doorhelp

    def figures(text):
        return set(re.findall(r"(\d+\.\d)%\s+for African", text))

    in_choices = figures(selfrule.CHOICES["exclude"])
    in_header = figures(selfrule.__doc__ or "")
    blob = "\n".join(
        v if isinstance(v, str) else str(v)
        for v in vars(doorhelp).values() if isinstance(v, (str, dict)))
    in_doors = figures(blob) or figures(str(vars(doorhelp)))

    assert in_choices, "selfrule.CHOICES no longer states the figure"
    assert in_doors, "the door help no longer states the figure"
    assert in_choices == in_doors, (
        f"the origin-rule figure disagrees between copies: "
        f"selfrule.CHOICES says {in_choices}, the door help says "
        f"{in_doors}")
    # and it must not be the number the header retracts
    assert "13.4" not in "".join(in_choices), \
        "selfrule.CHOICES states the figure its own file retracts"
