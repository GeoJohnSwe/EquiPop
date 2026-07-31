"""The shared core (equipop.doors) - the parts every door reuses.

These tests are deliberately door-BLIND: nothing here imports arcpy
or PyQGIS. That is the point. When the QGIS door arrives it inherits
this file unchanged, and anything it breaks shows up here rather
than in the field.

The one test that does touch the ArcGIS door checks the two halves
still fit: the toolbox declares a contract, the package provides
one, and a mismatch must refuse rather than misbehave.
"""
import importlib
import os
import re
import sys

import pytest

from equipop.doors import CONTRACT, DoorError, require
from equipop.doors import fields as F
from equipop.doors import help as HLP
from equipop.doors import loader as L
from equipop.doors import report as R


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------------- help
def test_help_has_a_real_sentence_for_every_key():
    """Help text is a promise to the person at the dialog: a key
    with an empty or one-word value is worse than no key at all,
    because the box then LOOKS explained."""
    assert HLP.HELP and HLP.SUMMARY and HLP.USAGE
    for name, text in HLP.HELP.items():
        assert len(text.split()) >= 5, f"{name}: help too thin"
    for tool in ("CountsShares", "ValueStatistics"):
        assert len(HLP.summary_for(tool).split()) >= 20
        assert len(HLP.usage_for(tool).split()) >= 20


def test_missing_help_names_exactly_what_is_missing():
    assert HLP.missing_help(["k", "unit"]) == []
    assert HLP.missing_help(["k", "nosuchbox"]) == ["nosuchbox"]
    assert HLP.help_for("nosuchbox", "fallback") == "fallback"


def test_generator_reads_the_package_copy_not_its_own():
    """The whole point of moving the text: one source. If a door
    ever grows a private copy again this fails."""
    src = open(os.path.join(ROOT, "arcgis", "make_help_xml.py")).read()
    assert "from equipop.doors.help import" in src
    assert not re.search(r"^HELP\s*=\s*\{", src, re.M)


# ------------------------------------------------------- report
class _Pane:
    """Stands in for whatever a door gives us."""

    def __init__(self):
        self.info_lines, self.warns, self.errors = [], [], []

    # arcpy shape
    def addMessage(self, t):
        self.info_lines.append(t)

    def addWarningMessage(self, t):
        self.warns.append(t)

    def addErrorMessage(self, t):
        self.errors.append(t)

    # qgis shape
    def pushInfo(self, t):
        self.info_lines.append(t)

    def pushWarning(self, t):
        self.warns.append(t)

    def reportError(self, t):
        self.errors.append(t)


@pytest.mark.parametrize("make", [R.Channel.from_arcpy,
                                  R.Channel.from_qgis])
def test_one_channel_serves_either_door(make):
    pane = _Pane()
    ch = make(pane)
    ch.info("plain")
    ch.warning("careful")
    ch.error("stop")
    assert pane.info_lines == ["plain"]
    assert pane.warns == ["careful"]
    assert pane.errors == ["stop"]


def test_channel_falls_back_when_a_door_lacks_a_level():
    """QGIS gained pushWarning only in 3.16, and a plain console has
    no levels at all. Missing levels must land somewhere, never
    vanish."""
    seen = []
    ch = R.Channel(seen.append)
    ch.info("a")
    ch.warning("b")
    ch.error("c")
    assert seen == ["a", "b", "c"]


def test_a_failing_pane_never_ends_the_run():
    """Field lesson in miniature: the pane is the least important
    thing in a two-hour run. If it throws, the run continues."""
    def broken(_):
        raise RuntimeError("pane closed")
    ch = R.Channel(broken)
    ch.info("this must not raise")


def test_printed_output_reaches_the_pane_line_by_line():
    """The engines print. Pro and QGIS show only what is pushed to
    them. This is the join, and it was a 94-minute silent run that
    revealed it was missing."""
    pane = _Pane()
    with R.speaking(R.Channel.from_arcpy(pane)):
        print("[cells] 192 cells")
        print("[fast] pass with m = 144")
        sys.stdout.write("a trailing line with no newline")
    assert pane.info_lines == ["[cells] 192 cells",
                              "[fast] pass with m = 144",
                              "a trailing line with no newline"]


def test_stdout_is_restored_even_when_the_run_fails():
    pane = _Pane()
    before = sys.stdout
    with pytest.raises(ValueError):
        with R.speaking(R.Channel.from_arcpy(pane)):
            raise ValueError("engine gave up")
    assert sys.stdout is before


def test_stage_reports_and_records_where_the_time_went():
    pane = _Pane()
    store = []
    ch = R.Channel.from_arcpy(pane)
    with R.stage(ch, "reading input", store):
        pass
    assert store and store[0][0] == "reading input"
    assert pane.info_lines[0].startswith("[time] reading input:")


@pytest.mark.parametrize("sec,shown", [
    (0.4, "0.4 s"), (59.9, "59.9 s"), (90, "1 min 30 s"),
    (3661, "1 h 01 min 01 s")])
def test_durations_read_as_a_person_would_say_them(sec, shown):
    assert R.hms(sec) == shown


# ------------------------------------------------------- fields
def test_predicted_names_match_what_the_counts_engine_makes():
    got = F.predict_result_fields(
        "counts", "400", "", "", ["HighEdu"], [], [],
        decaying=False, efforting=False)
    assert got == ["N_400", "T_HighEdu_400", "R_HighEdu_400",
                   "Dist_400"]


def test_predicted_names_cover_effort_and_decay():
    eff = F.predict_result_fields(
        "counts", "400", "", "3", [], [], [],
        decaying=False, efforting=True)
    assert "Rounds_400" in eff and "N_tau3" in eff
    dec = F.predict_result_fields(
        "counts", "400", "", "", ["A"], [], [],
        decaying=True, efforting=False)
    assert {"ND_inf", "TD_A_inf", "RD_A_inf"} <= set(dec)


def test_shortening_never_merges_two_different_results():
    """The named danger: P25_income_400 and P75_income_400 must not
    collapse into one column and silently overwrite each other."""
    names = ["P25_income_400", "P75_income_400", "P25_income_1600",
             "MEAN_income_400", "GINI_income_400"]
    short = F.shorten_names(names)
    assert len(set(short.values())) == len(names)
    assert all(len(v) <= 10 for v in short.values())


def test_shortening_is_stable_for_a_single_name():
    assert F.shorten_names(["Dist_400"])["Dist_400"] == "Dist400"


def test_a_roomy_target_is_never_refused():
    assert F.refuse_short_target("C:/data/city.gdb/people",
                                 ["A_very_long_result_name"]) is None
    assert F.refuse_short_target("", ["A_very_long_result_name"]) is None


def test_a_shapefile_target_is_refused_with_the_fix_named():
    txt = F.refuse_short_target("C:/data/people.shp",
                                ["MEAN_income_1600", "N_400"])
    assert txt and "MEAN_income_1600" in txt
    assert "10 characters" in txt and "geodatabase" in txt
    assert "N_400" not in txt          # short names are not the problem


def test_the_roomy_container_is_named_per_door():
    """Same rule, different neighbour: a GeoPackage plays in QGIS the
    role a file geodatabase plays in Pro."""
    txt = F.refuse_short_target("/data/people.shp",
                                ["MEAN_income_1600"],
                                container="a GeoPackage")
    assert "GeoPackage" in txt and "geodatabase" not in txt


def test_field_names_are_made_safe_the_same_way_everywhere():
    assert F.safe_field_name("mean income (SEK)") == "mean_income__SEK_"
    assert F.safe_field_name("") == "X"
    assert len(F.safe_field_name("x" * 200)) == 60


# ------------------------------------------------------- loader
def test_the_contract_unpacks_like_the_tuple_it_replaced():
    """Doors written before PointInput existed keep working."""
    pi = L.PointInput("point", {"x": [1, 2], "y": [3, 4]}, "OBJECTID",
                      crs_text="SWEREF 99 TM (EPSG:3006)")
    kind, data, oid = pi
    assert (kind, oid) == ("point", "OBJECTID")
    assert data["x"] == [1, 2]
    assert pi.n == 2 and len(pi) == 3


def test_a_missing_field_is_named_with_advice():
    with pytest.raises(DoorError) as e:
        L.check_fields_exist(["pop", "income"], ["pop", "55"],
                             "The input")
    msg = str(e.value)
    assert "'55'" in msg and "is not a field" in msg
    assert "own boxes" in msg          # the k-in-a-field-box lesson


def test_several_missing_fields_read_as_plural():
    with pytest.raises(DoorError) as e:
        L.check_fields_exist(["pop"], ["a", "b"], "The input")
    assert "are not fields" in str(e.value)


def test_unreadable_field_list_skips_the_check_instead_of_guessing():
    L.check_fields_exist(None, ["anything"], "The input")


def test_chosen_columns_win_over_any_guess():
    assert L.resolve_xy_fields(["east", "north"], "MyX", "MyY",
                               "The input") == ("MyX", "MyY", "chosen")


def test_recognisable_columns_are_guessed():
    x, y, how = L.resolve_xy_fields(["East_RT90", "North_RT90", "pop"],
                                    None, None, "The input")
    assert (x, y, how) == ("East_RT90", "North_RT90", "guessed")


def test_degree_columns_are_refused_with_a_projection_named():
    with pytest.raises(DoorError) as e:
        L.resolve_xy_fields(["lon", "lat"], None, None, "The input",
                            sample_lonlat=lambda a, b: (13.0, 57.7))
    msg = str(e.value)
    assert "DEGREES" in msg and "SWEREF 99 TM (EPSG:3006)" in msg
    assert "cannot be auto-projected" in msg


def test_degree_refusal_still_works_without_a_sampler():
    with pytest.raises(DoorError) as e:
        L.resolve_xy_fields(["lon", "lat"], None, None, "The input")
    assert "a metric CRS" in str(e.value)


def test_unguessable_columns_ask_rather_than_demand_renaming():
    with pytest.raises(DoorError) as e:
        L.resolve_xy_fields(["a", "b"], None, None, "The input")
    msg = str(e.value)
    assert "pick the X field" in msg
    assert "rename" not in msg.lower()


@pytest.mark.parametrize("lon,lat,expect", [
    (13.0, 57.7, "SWEREF 99 TM (EPSG:3006)"),      # Sweden
    (-0.1, 51.5, "UTM zone 30N"),                  # London
    (18.0, -33.9, "UTM zone 34S"),                 # Cape Town
    (None, None, "a metric CRS")])
def test_a_fitting_projection_is_named_from_the_numbers(lon, lat,
                                                        expect):
    assert expect in L.metric_crs_hint(lon, lat)


# ----------------------------------------------------- contract
def test_a_matching_contract_passes_quietly():
    require(CONTRACT)


def test_an_old_door_is_told_to_replace_its_files():
    with pytest.raises(DoorError) as e:
        require(CONTRACT - 1, door="the ArcGIS toolbox",
                files="EquiPop.pyt")
    msg = str(e.value)
    assert "EquiPop.pyt" in msg
    assert "remove and re-add the toolbox" in msg


def test_a_new_door_is_told_to_upgrade_the_package():
    with pytest.raises(DoorError) as e:
        require(CONTRACT + 1, door="the ArcGIS toolbox")
    assert "pip install --upgrade equipop" in str(e.value)


def test_the_arcgis_door_declares_a_contract_this_package_provides():
    """The two halves must fit. Read as text so this test needs no
    arcpy - it is checking a declaration, not behaviour."""
    src = open(os.path.join(ROOT, "arcgis", "EquiPop.pyt")).read()
    m = re.search(r"^_CONTRACT\s*=\s*(\d+)", src, re.M)
    assert m, "EquiPop.pyt no longer declares _CONTRACT"
    assert int(m.group(1)) == CONTRACT


# ------------------------------- the door with no package behind it
_NO_PACKAGE_PROBE = r'''
import sys, types, importlib.util, importlib.machinery, os

class _Block:
    """Nothing named equipop exists in this interpreter."""
    def find_module(self, name, path=None):
        return self.find_spec(name, path) and self
    def find_spec(self, name, path=None, target=None):
        if name == "equipop" or name.startswith("equipop."):
            raise ImportError("No module named 'equipop'")
        return None

for m in [m for m in sys.modules if m.split(".")[0] == "equipop"]:
    del sys.modules[m]
sys.meta_path.insert(0, _Block())

sys.path.insert(0, os.path.join(r"{root}", "tests"))
import pandas as pd, numpy as np
import test_arcgis_stub as H
H._install_fake_arcpy(pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                                    "SHAPE@Y": [0.0]}))
pyt = H._load_pyt()

# 1. the toolbox OPENS: both tools build their dialogs
for cls in (pyt.CountsShares, pyt.ValueStatistics):
    tool = cls()
    ps = tool.getParameterInfo()
    assert len(ps) > 10, "dialog did not build"

# 2. dialog-time checks degrade quietly rather than breaking the box
assert pyt._predict_result_fields("counts", "400", "", "", [], [], [],
                                  False, False) == []
assert pyt._refuse_shp_overflow("x.shp", ["MEAN_income_1600"]) is None

# 3. but RUNNING says what is wrong and how to fix it
try:
    pyt._doors()
    raise AssertionError("a missing package must refuse")
except Exception as e:
    assert "pip install equipop" in str(e), str(e)

print("OK")
'''


def test_the_toolbox_still_opens_when_the_package_is_missing():
    """Pro validates a toolbox at OPEN. If the door imported the
    package up front, an uninstalled package would mean no toolbox at
    all - and no dialog left to explain why. So: the dialogs must
    build with nothing behind them, the pre-checks go quiet, and the
    explanation arrives when the person presses Run.

    Run in a separate interpreter because it has to make `equipop`
    genuinely unimportable.
    """
    import subprocess
    out = subprocess.run(
        [sys.executable, "-c",
         _NO_PACKAGE_PROBE.replace("{root}", ROOT)],
        capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr[-2000:]
    assert "OK" in out.stdout


_OLD_PACKAGE_PROBE = r'''
import sys, types, os

# A package that IS installed, but predates equipop.doors - exactly
# what a Pro machine looks like when the toolbox files were replaced
# and pip was not run.
for m in [m for m in sys.modules if m.split(".")[0] == "equipop"]:
    del sys.modules[m]

class _Old:
    def find_spec(self, name, path=None, target=None):
        if name == "equipop.doors" or name.startswith("equipop.doors."):
            raise ImportError("No module named 'equipop.doors'")
        return None

sys.meta_path.insert(0, _Old())
fake = types.ModuleType("equipop")
fake.__version__ = "1.17.3"
fake.__path__ = []
sys.modules["equipop"] = fake

sys.path.insert(0, os.path.join(r"{root}", "tests"))
import pandas as pd
import test_arcgis_stub as H
H._install_fake_arcpy(pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                                    "SHAPE@Y": [0.0]}))
pyt = H._load_pyt()

try:
    pyt._doors()
    raise AssertionError("an outdated package must refuse")
except Exception as e:
    msg = str(e)
    assert "1.17.3" in msg, msg
    assert "pip install --upgrade equipop" in msg, msg
    assert "is not installed" not in msg, "wrong diagnosis: " + msg

print("OK")
'''


def test_an_outdated_package_is_told_apart_from_a_missing_one():
    """The two have different fixes, and the wrong message sends
    someone hunting for a package that is sitting right there.

    This is the LIKELY half of version skew, not the exotic one: the
    package is upgraded by pip, the toolbox files are replaced by
    hand, and the two steps are easy to do in the wrong order or in
    the wrong environment.
    """
    import subprocess
    out = subprocess.run(
        [sys.executable, "-c",
         _OLD_PACKAGE_PROBE.replace("{root}", ROOT)],
        capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr[-2000:]
    assert "OK" in out.stdout
