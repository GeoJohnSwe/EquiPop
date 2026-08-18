"""BACKLOG 185 - what decay is FOR.

John, on reading 1.39:

    "The decay uses distances to decay reference and treatment
    population, it doesn't affect distance. So there is no need for an
    extra distance measure - what is interesting is ... the decayed sum
    of reference and treatment populations at k. However - and just to
    be clear - the k-values should aim for a NON-DECAYED k. i.e. if
    k=300 is requested, the 300 nearest population is the right call -
    the decayed populations should be reported and are always (as long
    as the beta has the right sign) be smaller than k"

Three separable claims, and each one is a test below:

  1. decay does not choose the neighbourhood - the raw count does;
  2. decay does not move the radius;
  3. the decayed totals are reported at that same k, and are smaller.

The third is an INVARIANT, not a sample: with a decreasing decay,
ND_k <= N_k and TD <= T everywhere, always. No correct run can trip
it, which is what makes it worth asserting rather than illustrating.

Until v1.40 the fast engine did something else entirely: it summed out
to the DECAY TRUNCATION radius and emitted ND_inf, a decayed potential
over everybody in the study area. A real measure, but not this
method's. The classic engine had been right all along - its docstring
quotes the original EquiPop for the rule - so this was the two engines
disagreeing, not a missing feature.
"""

import io
import contextlib

import numpy as np
import pytest

from equipop.decay import Decay
from equipop.stata_bridge import knn_to_rows


def _data(n=400, seed=9):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, 5000, n)
    y = rng.uniform(0, 5000, n)
    w = rng.integers(1, 20, n).astype(float)
    treat = {"g": np.floor(w * rng.uniform(0, 1, n))}
    return x, y, w, treat


def _run(**kw):
    x, y, w, treat = _data()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = knn_to_rows(x, y, [300], treat=treat, weight=w,
                          treat_are_counts=True, unit_size=100.0, **kw)
    return out


def _both(**kw):
    return _run(), _run(decay=Decay(model="negexp", half_life_m=800),
                        **kw)


# --------------------------------------------------------------------
# 1 and 2: decay changes neither the neighbourhood nor the radius
# --------------------------------------------------------------------

def test_the_k_neighbourhood_is_chosen_on_the_raw_count():
    """"if k=300 is requested, the 300 nearest population is the right
    call". The decay must not pull the threshold in."""
    plain, faded = _both()
    assert np.allclose(plain["N_300"], faded["N_300"], equal_nan=True), (
        "the decay moved the k threshold - the neighbourhood must be "
        "chosen on the raw count")


def test_the_radius_is_unchanged_by_decay():
    """"it doesn't affect distance". Dist_k answers how far you must go
    to reach k people, which has nothing to do with how their
    contribution is weighted once you are there."""
    plain, faded = _both()
    assert np.allclose(plain["Dist_300"], faded["Dist_300"],
                       equal_nan=True)


def test_the_raw_columns_are_untouched():
    plain, faded = _both()
    for col in ("N_300", "Dist_300", "T_g_300", "R_g_300"):
        assert np.allclose(plain[col], faded[col], equal_nan=True), (
            f"{col} changed when a decay was added")


# --------------------------------------------------------------------
# 3: the decayed totals, at that same k
# --------------------------------------------------------------------

def test_the_decayed_totals_are_reported_at_k():
    _plain, faded = _both()
    for col in ("ND_300", "TD_g_300", "RD_g_300"):
        assert col in faded, f"{col} is missing"
        assert np.isfinite(faded[col]).any(), f"{col} is all missing"


def test_no_decay_means_no_decayed_columns():
    plain, _faded = _both()
    assert not [c for c in plain if c.startswith(("ND_", "TD_", "RD_"))]


def test_the_decayed_population_is_always_smaller_than_k():
    """John's invariant. Not a sample - everywhere, always."""
    _plain, faded = _both()
    ok = np.isfinite(faded["ND_300"]) & np.isfinite(faded["N_300"])
    assert ok.any()
    assert (faded["ND_300"][ok] <= faded["N_300"][ok] + 1e-9).all(), (
        "a decayed total exceeded its raw total, which a decreasing "
        "decay cannot produce")


def test_the_decayed_group_is_always_smaller_than_the_raw_group():
    _plain, faded = _both()
    ok = np.isfinite(faded["TD_g_300"]) & np.isfinite(faded["T_g_300"])
    assert (faded["TD_g_300"][ok] <= faded["T_g_300"][ok] + 1e-9).all()


def test_the_decayed_total_is_strictly_smaller_somewhere():
    """The other half of the invariant: equality everywhere would mean
    the weights were all 1 and the decay never applied."""
    _plain, faded = _both()
    ok = np.isfinite(faded["ND_300"]) & np.isfinite(faded["N_300"])
    assert (faded["ND_300"][ok] < faded["N_300"][ok] - 1e-6).any(), (
        "no row was decayed at all - the weights are not reaching the "
        "sums")


def test_a_shorter_half_life_decays_harder():
    """Direction, not just magnitude. A tighter bandwidth must leave
    less of the neighbourhood standing."""
    x, y, w, treat = _data()
    got = {}
    for hl in (400, 3000):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            got[hl] = knn_to_rows(
                x, y, [300], treat=treat, weight=w,
                treat_are_counts=True, unit_size=100.0,
                decay=Decay(model="negexp", half_life_m=hl))["ND_300"]
    ok = np.isfinite(got[400]) & np.isfinite(got[3000])
    assert (got[400][ok] <= got[3000][ok] + 1e-9).all()
    assert (got[400][ok] < got[3000][ok] - 1e-6).any()


def test_the_decayed_share_is_a_share():
    _plain, faded = _both()
    rd = faded["RD_g_300"]
    ok = np.isfinite(rd)
    assert ((rd[ok] >= 0) & (rd[ok] <= 1)).all()


# --------------------------------------------------------------------
# The overshoot ring - where raw and decayed could silently diverge
# --------------------------------------------------------------------

@pytest.mark.parametrize("mode", ["whole", "proportional"])
def test_the_invariant_holds_under_both_overshoot_modes(mode):
    """The care point of the whole change.

    When the ring that crosses k is split, the decayed sum has to take
    the SAME per-cell fractions the raw counts take. If it does not,
    raw and decayed describe different neighbourhoods and nothing says
    so - the numbers stay plausible.
    """
    _plain, faded = _both(overshoot_mode=mode)
    ok = np.isfinite(faded["ND_300"]) & np.isfinite(faded["N_300"])
    assert (faded["ND_300"][ok] <= faded["N_300"][ok] + 1e-9).all()
    ok2 = np.isfinite(faded["TD_g_300"]) & np.isfinite(faded["T_g_300"])
    assert (faded["TD_g_300"][ok2] <= faded["T_g_300"][ok2] + 1e-9).all()


def test_proportional_takes_less_than_whole_in_both_raw_and_decayed():
    """The two must move TOGETHER. A split ring contributes less to the
    raw count; it must contribute less to the decayed one too."""
    whole = _run(decay=Decay(model="negexp", half_life_m=800),
                 overshoot_mode="whole")
    prop = _run(decay=Decay(model="negexp", half_life_m=800),
                overshoot_mode="proportional")
    ok = np.isfinite(whole["ND_300"]) & np.isfinite(prop["ND_300"])
    assert (prop["N_300"][ok] <= whole["N_300"][ok] + 1e-9).all()
    assert (prop["ND_300"][ok] <= whole["ND_300"][ok] + 1e-9).all(), (
        "the decayed sum did not follow the raw one through the ring "
        "split - they are describing different neighbourhoods")

    # STRICTNESS, and it is the point. A first version of this test
    # asserted only <=, and a deliberate break that made the decayed
    # sum take the WHOLE ring while the raw count took a fraction
    # passed it - by being equal. Both must actually MOVE where the
    # ring is genuinely split, or the assertion proves nothing.
    raw_moved = (prop["N_300"][ok] < whole["N_300"][ok] - 1e-6)
    dec_moved = (prop["ND_300"][ok] < whole["ND_300"][ok] - 1e-6)
    assert raw_moved.any(), (
        "no ring was split in this fixture - the test cannot see "
        "anything and needs different data")
    assert dec_moved.any(), (
        "the raw count changed with the overshoot mode and the "
        "decayed sum did not - the ring fractions are not being "
        "applied to the decayed totals")
    assert (raw_moved == dec_moved).all(), (
        "raw and decayed disagree about WHICH origins had a split "
        "ring")


# --------------------------------------------------------------------
# The removed measure
# --------------------------------------------------------------------

def test_the_unbounded_decayed_sum_is_gone():
    """John: "it doesn't solve any problem I know of - and it risks
    becoming an orphan or picked up in a later session with unknown
    consequences"."""
    _plain, faded = _both()
    assert not [c for c in faded if c.endswith("_inf")], (
        "the unbounded decayed potential is back")


def test_a_radius_run_with_decay_is_not_a_silent_hole():
    """Removing ND_inf would have left r() + decay() producing no
    decayed output at all."""
    x, y, w, treat = _data()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = knn_to_rows(x, y, None, r_values=[900], treat=treat,
                          weight=w, treat_are_counts=True,
                          unit_size=100.0,
                          decay=Decay(model="negexp", half_life_m=800))
    nd = [c for c in res if c.startswith("ND_r")]
    assert nd, f"no decayed total for a radius run, got {sorted(res)}"
    col = nd[0]
    raw = col.replace("ND_", "N_")
    ok = np.isfinite(res[col]) & np.isfinite(res[raw])
    assert (res[col][ok] <= res[raw][ok] + 1e-9).all()
