# -*- coding: utf-8 -*-
"""test_python_3_15.py - what Python 3.15 and the libraries it brings
change for EquiPop (v1.61.3).

John, 22 October 2026: "a new python version just shipped - what
consequences does it have for EquiPop?" Measured that night: the whole
suite passed on Python 3.15.1, with numpy 2.5, pandas 3.1, scipy 1.18,
pyproj 3.8 and rasterio 1.5 - the versions a 3.15 install gets, since
only they publish 3.15 builds. Three things were still worth fixing,
and this file holds them:

1. PEP 686: from 3.15 a text file opened without an encoding is UTF-8.
   Up to 3.14 it is the system's encoding - cp1252 on a Western Windows
   machine, which cannot write "Şanlıurfa" at all. EquiPop wrote its
   .meta.txt that way, so the bytes depended on the Python under it,
   and on Windows QGIS a Turkish name lost the file (BACKLOG 426).
2. pandas 3.1 deprecates `inplace=True` on drop, and pandas 4 removes
   it; machine 4's rate step used it twice (BACKLOG 427).
3. Python 3.10 reaches its end of life this month: the floor is 3.11,
   the oldest Python any current ArcGIS Pro ships (BACKLOG 429).

(The fourth item of the release, CITATION.cff, is in test_citation.)

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import ast
import builtins
import io
import os
import re
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

# The places EquiPop's own code lives: the package, both GIS doors, the
# release and support tools, and the scripts at the top of the tree.
CODE = ([*sorted((ROOT / "equipop").rglob("*.py")),
         *sorted((ROOT / "qgis").rglob("*.py")),
         *sorted((ROOT / "arcgis").glob("*.pyt")),
         *sorted((ROOT / "arcgis").glob("*.py")),
         *sorted((ROOT / "tools").glob("*.py")),
         *sorted(ROOT.glob("run_*.py")), *sorted(ROOT.glob("demo_*.py"))])
CODE = [p for p in CODE if "__pycache__" not in p.parts]

TURKISH = "C:/Data/T\u00fcrkiye/\u015eanl\u0131urfa_2020.tif"   # Ş and ı


# ------------------------------------------------------ 1. UTF-8 by name
def test_provenance_text_survives_a_windows_encoding(tmp_path,
                                                     monkeypatch):
    """Python up to 3.14 on a Western Windows machine, simulated: every
    text file opened without an encoding is opened as cp1252. A run
    whose input is Şanlıurfa writes its .meta.txt as UTF-8 regardless,
    and the .meta.json reads back.

    BROKEN WITH: the .meta.txt opened without an encoding (meta.py)."""
    real = io.open

    def windows_open(file, mode="r", buffering=-1, encoding=None,
                     *args, **kwargs):
        if "b" not in mode and encoding in (None, "locale"):
            encoding = "cp1252"
        return real(file, mode, buffering, encoding, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", windows_open)
    monkeypatch.setattr(io, "open", windows_open)

    from equipop.meta import RunLog, load_meta
    rl = RunLog({"k": 100})
    rl.add_input(TURKISH, rows=3)
    rl.event("info", f"read {TURKISH}")
    with redirect_stdout(io.StringIO()):
        written = rl.finalize(pd.DataFrame({"a": [1.0, 2.0]}),
                              str(tmp_path / "out.csv"))
    txt = (tmp_path / "out.meta.txt").read_bytes().decode("utf-8")
    assert "\u015eanl\u0131urfa_2020.tif" in txt
    assert load_meta(written)["inputs"][0]["path"].endswith(
        "\u015eanl\u0131urfa_2020.tif")


SCENARIO = r'''
import os, sys, warnings
warnings.filterwarnings("error", category=EncodingWarning,
                        module=r"equipop(\.|$)")
import numpy as np, pandas as pd
out = sys.argv[1]

from equipop.meta import RunLog, load_meta
rl = RunLog({"k": 5})
rl.event("info", "M\u00e4tning i Malm\u00f6")
load_meta(rl.finalize(pd.DataFrame({"a": [1.0]}),
                      os.path.join(out, "o.csv")))

from equipop.bigrun import run_knn_counts_tiled, load_tiled, map_tiles
from equipop.cells import CellData
xx, yy = np.meshgrid(np.arange(20), np.arange(20))
cd = CellData(E=(xx.ravel() * 100 + 50).astype(float),
              N=(yy.ravel() * 100 + 50).astype(float),
              n=np.full(400, 2.0), binary_sums={"t": np.ones(400)},
              value_arrays={}, unit_size=100.0)
d = os.path.join(out, "run")
run_knn_counts_tiled(cd, k_values=[10], out_dir=d, tile_m=1000.0)
run_knn_counts_tiled(cd, k_values=[10], out_dir=d, tile_m=1000.0)
load_tiled(d)
map_tiles(d, lambda f: f)
print("SCENARIO DONE")
'''


def test_nothing_equipop_opens_uses_the_system_encoding(tmp_path):
    """Python's own detector, not a reading of the code: run with
    -X warn_default_encoding, an EncodingWarning raised from inside
    equipop is an error. The scenario writes and reads a provenance
    record and a tiled run - written, resumed (which reads the
    manifest), loaded and post-processed.

    (On 3.15 the default IS UTF-8; the guard matters for the Pythons
    that ArcGIS Pro and QGIS bring, which are older.)

    BROKEN WITH: bigrun's manifest written without an encoding."""
    pytest.importorskip("pyarrow")
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING="utf-8",
               PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-X", "warn_default_encoding",
                        "-c", SCENARIO, str(tmp_path)],
                       cwd=str(tmp_path), env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       timeout=600)
    assert r.returncode == 0 and "SCENARIO DONE" in r.stdout, (
        r.stdout[-1500:] + r.stderr[-2500:])


def _text_mode_without_encoding(call):
    """True for open()/io.open()/codecs.open() in text mode, or a
    Path.read_text()/write_text(), with no encoding given."""
    fn = call.func
    kws = {k.arg for k in call.keywords}
    if "encoding" in kws:
        return False
    is_open = (isinstance(fn, ast.Name) and fn.id == "open") or (
        isinstance(fn, ast.Attribute) and fn.attr == "open"
        and isinstance(fn.value, ast.Name)
        and fn.value.id in ("io", "codecs"))
    if is_open:
        mode = "r"
        if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant):
            mode = call.args[1].value
        for k in call.keywords:
            if k.arg == "mode" and isinstance(k.value, ast.Constant):
                mode = k.value.value
        if isinstance(mode, str) and "b" in mode:
            return False
        return len(call.args) < 4             # encoding given by position
    if isinstance(fn, ast.Attribute) and fn.attr == "read_text":
        return not call.args
    if isinstance(fn, ast.Attribute) and fn.attr == "write_text":
        return len(call.args) < 2
    if isinstance(fn, ast.Attribute) and fn.attr in (
            "run", "Popen", "check_output", "check_call"):
        textual = any(k.arg in ("text", "universal_newlines")
                      for k in call.keywords)
        spread = any(k.arg is None for k in call.keywords)   # **kwargs
        return textual and not spread
    return False


def test_every_text_file_open_names_its_encoding():
    """Every open, read_text, write_text and text-mode subprocess in
    EquiPop's own code names its encoding - including code no test
    reaches. (It cannot see a Path's .open(): rasterio.open and
    urllib's opener.open look the same to it. None is used in text
    mode today.)

    BROKEN WITH: load_tiled's manifest read without an encoding; and
    release_record reading pytest's output without one."""
    assert len(CODE) > 50, "found too few files - the walk is wrong"
    bad = []
    for p in CODE:
        tree = ast.parse(p.read_text(encoding="utf-8"), str(p))
        bad += [f"{p.relative_to(ROOT)}:{n.lineno}"
                for n in ast.walk(tree)
                if isinstance(n, ast.Call) and _text_mode_without_encoding(n)]
    assert not bad, ("text opened in the system's encoding, which "
                     "differs between Python 3.14 and 3.15 and between "
                     f"machines - name encoding='utf-8': {bad}")


@pytest.mark.parametrize("tool", ["release_record.py", "windows_check.py"])
def test_the_release_tools_ask_their_children_for_utf8(tool):
    """Reading a child's output as UTF-8 is half of it; the child, on
    Windows before 3.15, WRITES in the system encoding unless told.

    BROKEN WITH: PYTHONIOENCODING dropped from either tool."""
    src = (ROOT / "tools" / tool).read_text(encoding="utf-8")
    assert re.search(r'PYTHONIOENCODING\s*=\s*"utf-8"', src), tool


# ------------------------------------- 2. no in-place drop (pandas 3.1)
def test_no_inplace_keyword_anywhere():
    """pandas 3.1 deprecates `inplace=True` (PDEP-8) and pandas 4
    removes it; pandas 3.1 is what a Python 3.15 install gets, and its
    warning was the only one the 3.15 run raised from EquiPop's code.

    BROKEN WITH: machine 4's drop of the band counts made in place
    again."""
    bad = []
    for p in CODE:
        tree = ast.parse(p.read_text(encoding="utf-8"), str(p))
        bad += [f"{p.relative_to(ROOT)}:{n.lineno}"
                for n in ast.walk(tree) if isinstance(n, ast.Call)
                for k in n.keywords
                if k.arg == "inplace" and isinstance(k.value, ast.Constant)
                and k.value.value is True]
    assert not bad, f"inplace=True: {bad}"


@pytest.mark.parametrize("rule", ["own", "cell"])
def test_the_rate_machinery_still_leaves_the_output(tmp_path, rule):
    """The drop now RETURNS the trimmed frame, so both callers - the
    in-memory result and each tile - must take it. Under either rule
    the output carries the measure and none of the sums it was read
    from.

    BROKEN WITH: run_indices calling finish() without keeping its
    return value (the machinery came back)."""
    pytest.importorskip("rasterio")
    import test_vital_machine4 as M4
    from equipop.doors.demography import run_indices
    folder = M4.make_folder(tmp_path)
    with redirect_stdout(io.StringIO()):
        man = run_indices(str(folder), [], vital=["life_expectancy_60",
                                                  "total_fertility_rate"],
                          k_values=[5000], unit_size=1000.0, epsg=32737,
                          vital_reference=rule)
    cols = list(man["results"].columns)
    assert "e60_5000" in cols and "TFR_5000" in cols
    left = [c for c in cols if re.match(r"^([TR]_)?v[bwco]", c)]
    assert not left, f"{rule}: machinery in the output: {left[:6]}"


# ------------------------------------------------- 3. the floor is 3.11
FLOOR_STATEMENTS = {
    "MANUAL.md": r"Requires Python ≥ (\d+\.\d+)",
    "MANUAL_TOPICS.md": r"Requires Python ≥ (\d+\.\d+)",
    "REVIEWER_BRIEF.md": r"Python (\d+\.\d+)\+",
    "stata/equipop.ado": r"Python is (\d+\.\d+) or newer",
}


def test_the_python_floor_is_3_11_and_said_the_same_everywhere():
    """3.10 reaches its end of life in October 2026, and ArcGIS Pro's
    oldest current Python is 3.11. pyproject says so, and every place
    that tells a person the minimum says the same.

    BROKEN WITH: the Stata door's advice left at "3.10 or newer"."""
    py = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    floor = re.search(r'requires-python\s*=\s*">=(\d+\.\d+)"', py).group(1)
    assert floor == "3.11"
    for name, pat in FLOOR_STATEMENTS.items():
        said = re.findall(pat, (ROOT / name).read_text(encoding="utf-8"))
        assert said, f"{name} no longer states the minimum Python"
        assert set(said) == {floor}, f"{name} says {said}, pyproject {floor}"


def test_the_classifiers_start_at_the_floor_and_have_no_gaps():
    """PyPI's "supported Python" labels (v1.61.4). They change nothing
    pip does - EquiPop is one pure-Python wheel - but a reader trusts
    them. So they start at requires-python, run without a gap, and are
    every one a version the release record tests on.

    BROKEN WITH: 3.11 dropped from the list; and the floor raised to
    3.12 with the list left alone."""
    py = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    floor = re.search(r'requires-python\s*=\s*">=(\d+\.\d+)"', py).group(1)
    listed = re.findall(r'"Programming Language :: Python :: 3\.(\d+)"', py)
    minors = sorted(int(m) for m in listed)
    assert minors, "no Python version classifiers"
    assert minors[0] == int(floor.split(".")[1]), (floor, minors)
    assert minors == list(range(minors[0], minors[-1] + 1)), minors
    assert '"Programming Language :: Python :: 3 :: Only"' in py
