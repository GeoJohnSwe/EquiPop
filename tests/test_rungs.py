# -*- coding: utf-8 -*-
"""test_rungs.py - BACKLOG 104 (the rung-to-box mapping) and 103 (the
short statistics menu in QGIS machine 2).

104 is not a tidiness item. John, in the field on 1.29.5, chose
treatment rung 1 and filled the box that served rung 2. The run
produced N_100 and Dist_100, no T_, no R_, and NO MESSAGE. Every test
here was checked by breaking its rule on purpose.
"""

import os
import re
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "qgis"))

import qgis_stub                                       # noqa: E402
qgis_stub.install()

from qgis.core import (QgsProcessingException,         # noqa: E402
                       QgsProcessingFeedback)
from equipop_qgis.alg_counts import CountsAndShares    # noqa: E402
from equipop_qgis.alg_stats import ValueStatistics, MEASURES  # noqa: E402


def _source(n=400, seed=104):
    rng = np.random.default_rng(seed)
    t = pd.DataFrame({
        "x": rng.uniform(0, 3000, n), "y": rng.uniform(0, 3000, n),
        "Population": rng.integers(1, 20, n).astype(float),
        "LowInc": rng.integers(0, 12, n).astype(float),
        "Income": rng.lognormal(10, 0.3, n),
        "PlaceType": rng.choice(["dwelling", "shop", "school"], n)})
    return qgis_stub._Source(t, "EPSG:32633")


def _run(alg_cls, **params):
    alg = alg_cls()
    alg.initAlgorithm()
    p = {"layer": _source(), "unit": 100.0, "outfc": "memory:out",
         "k": "100"}
    p.update(params)
    fb = QgsProcessingFeedback()
    alg.processAlgorithm(p, None, fb)
    return p["_sinks"]["outfc"].to_frame(), fb


def _said(fb):
    return " ".join(fb.info) + " " + " ".join(fb.warnings)


# ---------------------------------------------------- 104, the field
def test_johns_1_29_5_field_run_is_now_refused_not_silently_empty():
    """The exact dialog state that produced nothing: treatment rung 1
    ("one column per group"), with box 2b filled instead of 2a."""
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, pop=["Population"], refmode=[1],
             treatmode=[1], treatcatfield=["LowInc"])
    msg = str(e.value)
    assert "box 2a" in msg and "empty" in msg
    assert "one column per group" in msg


def test_the_same_run_with_the_right_box_still_works():
    out, _ = _run(CountsAndShares, pop=["Population"], refmode=[1],
                  treatmode=[1], treat=["LowInc"])
    assert {"T_LowInc_100", "R_LowInc_100"} <= set(out.columns)


# ------------------------------------------- 104, every empty rung
@pytest.mark.parametrize("params,box", [
    (dict(refmode=[1]), "box 1a"),
    (dict(refmode=[2]), "box 1b"),
    (dict(pop=["Population"], refmode=[1], treatmode=[1]), "box 2a"),
])
def test_a_rung_refuses_when_the_box_it_needs_is_empty(params, box):
    with pytest.raises(QgsProcessingException) as e:
        _run(CountsAndShares, **params)
    assert box in str(e.value)


def test_machine_2_refuses_the_same_way():
    """The two doors used to differ: machine 2 read `refmode == 2 and
    catfield` and did nothing at all when the field was missing."""
    with pytest.raises(QgsProcessingException) as e:
        _run(ValueStatistics, refmode=[2], values=["Income"],
             measures=[0])
    assert "box 1b" in str(e.value)


# ------------------------------------------ 104, ignored boxes speak
@pytest.mark.parametrize("params,box", [
    (dict(pop=["Population"], refmode=[1], catfield=["PlaceType"]),
     "Box 1b"),
    (dict(pop=["Population"], refmode=[1], reftable=["dwelling"]),
     "Box 1c"),
    (dict(pop=["Population"], refmode=[1], treatmode=[1],
          treat=["LowInc"], treatcatfield=["PlaceType"]), "Box 2b"),
    (dict(pop=["Population"], refmode=[1], treatmode=[1],
          treat=["LowInc"], restgroup="other"), "Box 2d"),
])
def test_a_box_the_chosen_rung_ignores_says_so(params, box):
    _, fb = _run(CountsAndShares, **params)
    said = _said(fb)
    assert box in said and "IGNORED" in said


def test_a_box_that_is_honoured_off_its_rung_says_that_instead():
    """Box 2a works even on rung 0. Saved models depend on it, so it
    is not taken away - but it stops being silent."""
    out, fb = _run(CountsAndShares, pop=["Population"],
                   refmode=[1], treatmode=[0], treat=["LowInc"])
    assert "T_LowInc_100" in out.columns
    said = _said(fb)
    assert "Box 2a" in said and "IS being used" in said


# ------------------------------------------------- 103, the menu
def _literal_list(path, name):
    """Read a module-level list out of a source file WITHOUT importing
    it. Neither door may be imported to get at these - see
    test_menu_wording_is_pinned_not_shared for why."""
    src = open(os.path.join(ROOT, path), encoding="utf-8").read()
    body = re.search(rf"^{name}\s*=\s*\[(.*?)\]", src,
                     re.S | re.M).group(1)
    return [x.strip().strip('"\'') for x in
            re.findall(r'"([^"]*)"|\'([^\']*)\'', body)
            for x in x if x] or [
        x.strip().strip('"\'') for x in body.split(",") if x.strip()]


def _joined(path, name):
    """Same, but re-joining strings that were wrapped across lines."""
    src = open(os.path.join(ROOT, path), encoding="utf-8").read()
    body = re.search(rf"^{name}\s*=\s*\[(.*?)\]", src,
                     re.S | re.M).group(1)
    out, cur = [], ""
    for piece in re.split(r",\s*(?=[\"\'])", body):
        parts = re.findall(r'"([^"]*)"', piece) or \
            re.findall(r"'([^']*)'", piece)
        if parts:
            out.append("".join(parts))
    return out


def test_menu_wording_is_pinned_not_shared():
    """BACKLOG 105, and the reason it is a TEST rather than an import.

    Both doors keep their own copy of every menu, and they had already
    drifted: Pro said "additive (sum)" where QGIS said "additive
    (costs add up)", and QGIS offered six statistics where Pro offered
    twelve - which was BACKLOG 103. door_parity.py compares the NAMES
    of boxes, and both doors have a box called "measures", so nothing
    could see it.

    The obvious fix - import the wording from equipop/doors/rungs.py -
    WAS TRIED AND REVERTED. It broke BACKLOG 78: QGIS imports a plugin
    at STARTUP, so a module-level `import equipop` kills the entire
    plugin when the package is missing or old, before there is any
    algorithm to attach an explanatory message to. Pro learned the
    same thing in 1.16. Neither door may reach into the package to
    find out what its own dropdowns say.

    So the duplication is permanent and this test is the pin. The
    canonical copy is equipop/doors/rungs.py; change it there.
    """
    from equipop.doors import rungs

    qgis_ref = _joined("qgis/equipop_qgis/alg_counts.py", "REF_MODES")
    qgis_tre = _joined("qgis/equipop_qgis/alg_counts.py", "TREAT_MODES")
    pro_ref = _joined("arcgis/EquiPop.pyt", "REF_MODES")
    pro_tre = _joined("arcgis/EquiPop.pyt", "TREAT_MODES")

    # Pro must match the canonical wording exactly
    assert pro_ref == rungs.REFERENCE, "Pro's reference ladder drifted"
    assert pro_tre == rungs.TREATMENT, "Pro's treatment ladder drifted"
    assert _joined("arcgis/EquiPop.pyt", "OUTSIDE_MODES") == rungs.OUTSIDE
    assert _joined("arcgis/EquiPop.pyt", "_AGG_CHOICES") == \
        rungs.AGGREGATION

    # QGIS may add "(fill 2a)" hints and nothing else, because QGIS
    # cannot grey a box out (BACKLOG 104)
    strip = lambda xs: [re.sub(r"\s*\(fill [^)]*\)$", "", x) for x in xs]
    assert strip(qgis_ref) == rungs.REFERENCE, \
        f"QGIS reference ladder drifted: {strip(qgis_ref)}"
    assert strip(qgis_tre) == rungs.TREATMENT, \
        f"QGIS treatment ladder drifted: {strip(qgis_tre)}"
    assert _joined("qgis/equipop_qgis/alg_counts.py",
                   "OUTSIDE_MODES") == rungs.OUTSIDE
    assert _joined("qgis/equipop_qgis/alg_counts.py",
                   "AGG_MODES") == rungs.AGGREGATION


def test_qgis_machine_2_offers_every_statistic_pro_does():
    """BACKLOG 103, the menu that started this. Pro adds
    "percentiles" as a toggle for its own percentile box; QGIS takes
    percentiles as free text in box 2b and needs no toggle. That is
    the only difference either door may have."""
    from equipop.doors import rungs
    pro = [m for m in _joined("arcgis/EquiPop.pyt", "_MEASURES")
           if m != "percentiles"]
    qgis = _joined("qgis/equipop_qgis/alg_stats.py", "MEASURES")
    assert pro == rungs.MEASURES, "Pro's measures menu drifted"
    assert qgis == rungs.MEASURES, "QGIS's measures menu drifted"
    assert set(qgis) == set(MEASURES)


def test_every_offered_measure_is_one_the_engine_can_compute():
    from equipop.doors.__init__ import __name__ as _  # noqa: F401
    from equipop.stats import VALUE_STATS
    from equipop_qgis.alg_stats import MEASURE_KEY
    for m in MEASURES:
        assert MEASURE_KEY.get(m, m) in VALUE_STATS, (
            f"the menu offers '{m}' but the engine has no such "
            "statistic - a box that is filled and then ignored")


def test_variance_actually_arrives_under_the_engines_name():
    i = MEASURES.index("variance")
    out, _ = _run(ValueStatistics, values=["Income"], measures=[i])
    assert any(c.startswith("Var_") or "var" in c.lower()
               for c in out.columns), sorted(out.columns)


# ------------------------------------------------- 108, the weights
@pytest.mark.parametrize("keepoutside", [0, 1])
def test_the_population_field_survives_both_keepoutside_routes(keepoutside):
    """BACKLOG 108, and the most expensive silence found so far.

    The "leave their results Null" route set the weight to the
    Boolean MASK rather than count * mask, so every included row
    counted as ONE and the population field was thrown away without
    a word. Entered in 1.21; published from 1.21 to 1.29.3.

    It survived eight releases because no test drove this
    combination: restricted reference types, a NON-UNIFORM population
    field, and both keepoutside routes. door_parity compares names,
    LADDER_CASES compares column families, and neither can see a
    number. Found by an external review, not by this suite.
    """
    t = pd.DataFrame({"x": [0., 10., 20., 30., 40.], "y": [0.] * 5,
                      "Pop": [10., 1., 7., 7., 7.],
                      "Type": ["in", "in", "out", "out", "out"]})
    src = qgis_stub._Source(t, "EPSG:32633")
    alg = CountsAndShares()
    alg.initAlgorithm()
    p = {"layer": src, "unit": 100.0, "outfc": "memory:out", "k": "5",
         "pop": ["Pop"], "refmode": [2], "catfield": ["Type"],
         "reftable": ["in"], "keepoutside": [keepoutside]}
    alg.processAlgorithm(p, None, QgsProcessingFeedback())
    out = p["_sinks"]["outfc"].to_frame()
    got = out.loc[out["Type"] == "in", "N_5"].tolist()
    assert got == [11.0, 11.0], (
        f"included rows carry 10 and 1 people, so N_5 must be 11 - "
        f"got {got}. If this reads [2, 2] the population field has "
        "been replaced by a Boolean mask.")


def test_the_two_keepoutside_routes_agree_on_the_included_rows():
    """The same fault stated as an invariant: what happens to rows
    OUTSIDE the reference population must not change the numbers for
    rows inside it."""
    t = pd.DataFrame({"x": [0., 10., 20., 30.], "y": [0.] * 4,
                      "Pop": [10., 1., 7., 7.],
                      "Type": ["in", "in", "out", "out"]})
    src = qgis_stub._Source(t, "EPSG:32633")

    def run(ko):
        alg = CountsAndShares()
        alg.initAlgorithm()
        p = {"layer": src, "unit": 100.0, "outfc": "memory:out",
             "k": "5", "pop": ["Pop"], "refmode": [2],
             "catfield": ["Type"], "reftable": ["in"],
             "keepoutside": [ko]}
        alg.processAlgorithm(p, None, QgsProcessingFeedback())
        d = p["_sinks"]["outfc"].to_frame()
        return d.loc[d["Type"] == "in", ["N_5", "Dist_5"]].to_numpy()

    assert np.allclose(run(0), run(1))


# ------------------------------------------------- 116, the idiom
@pytest.mark.parametrize("alg,extra", [
    (CountsAndShares, {}),
    (ValueStatistics, {"values": ["Income"], "measures": [0]}),
])
def test_a_cell_size_of_zero_is_refused_not_replaced(alg, extra):
    """BACKLOG 116. Both machines read `parameterAsDouble(...) or
    100.0`, so a cell size of ZERO - a real thing a user can type -
    was silently replaced by 100 m and the run went ahead at a scale
    nobody chose. The same idiom nearly ate a deliberate
    self-potential of 0 in Pro, where 0 is MEANINGFUL.
    """
    with pytest.raises(QgsProcessingException, match="greater than 0"):
        _run(alg, unit=0.0, **extra)


def test_the_or_default_idiom_is_gone_from_the_doors():
    """The narrow sweep, kept honest. `X or DEFAULT` reads as
    harmless and silently rewrites any falsy value, which for a
    number means ZERO. It is banned on the parameters where zero is
    either meaningful or nonsense."""
    banned = [
        ('qgis/equipop_qgis/alg_counts.py', 'parameterAsDouble(parameters, "unit", context) or'),
        ('qgis/equipop_qgis/alg_stats.py', 'parameterAsDouble(parameters, "unit", context) or'),
        ('arcgis/EquiPop.pyt', '_num(pm, "unit", 100.0) or'),
        ('arcgis/EquiPop.pyt', '_num(pm, "hlbins", 10) or'),
        ('arcgis/EquiPop.pyt', '_num(pm, "selfpot", 1.0) or'),
    ]
    found = []
    for path, needle in banned:
        src = open(os.path.join(ROOT, path), encoding="utf-8").read()
        if needle in src:
            found.append(f"{path}: {needle}...")
    assert not found, (
        "the `or default` idiom is back on a parameter whose zero "
        f"matters: {found}")
