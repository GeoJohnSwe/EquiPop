# -*- coding: utf-8 -*-
"""test_everybody.py - a blank population box means EVERYBODY, but only
when the folder settles who that is.

v1.59.2. John, after his first Pro run of machine 3 (16 October): the
folder 5a fetched held every age band of women and men, and the run
stopped to ask which people define the neighbourhood. For such a
folder there is one answer. The rule (external review of 1.59.1, with
one change, see rasterfolder.infer_everybody):

  * 'sexes' when the year has every age band for women and for men,
    the same bands for both - with or without the t_ files beside them;
  * 'total' when it has every band of the t_ files;
  * refused when a band is missing, women and men differ, more than one
    year is present and none chosen, or a layer is not age-and-sex.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from equipop.rasterfolder import infer_everybody   # noqa: E402

R25 = ["bdi_f_00_2020_CN_1km_R2025A_UA_v1"]        # an R2025A file stem
BANDS90 = [0, 1] + list(range(5, 91, 5))
BANDS80 = [0, 1] + list(range(5, 81, 5))


def labels(sexes, bands, year="2020"):
    return [f"{s}_{a:02d}_{year}" for s in sexes for a in bands]


# ------------------------------------------------------------- the rule
def test_every_band_of_women_and_men_is_everybody():
    """5a's default download: f_ and m_, 0 to 90+.

    BROKEN WITH: infer_everybody always answering None."""
    word, why = infer_everybody(labels("fm", BANDS90), stems=R25)
    assert word == "sexes"
    assert "every age band for women and for men in 2020" in why


def test_the_t_files_beside_them_are_the_same_people_not_a_rival():
    """With 1e ticked the folder holds both routes to everybody. They
    are the same people, so f_ plus m_ is taken and the t_ files are
    said to be left out - not refused as competing.

    BROKEN WITH: refusing when both sets are complete."""
    word, why = infer_everybody(labels("fmt", BANDS90), stems=R25)
    assert word == "sexes" and "not added as well" in why


def test_every_band_of_the_totals_is_everybody():
    """The t_ files alone - and with a few f_ cohorts beside them, which
    are groups to study, not a second population.

    BROKEN WITH: the 'total' branch removed."""
    assert infer_everybody(labels("t", BANDS90), stems=R25)[0] == "total"
    cols = labels("t", BANDS90) + ["f_15_2020", "f_20_2020"]
    assert infer_everybody(cols, stems=R25)[0] == "total"


def test_the_older_series_ends_at_80():
    """WorldPop's 2000-2020 series has 80+ as its open band.

    BROKEN WITH: the top band fixed at 90."""
    assert infer_everybody(labels("fm", BANDS80))[0] == "sexes"


def test_an_r2025a_folder_that_stops_at_80_is_missing_its_old():
    """The same bands from an R2025A folder are NOT complete: 85 and
    90+ are missing, and everybody without the old is not everybody.

    BROKEN WITH: the R2025A top band not read from the file names."""
    word, why = infer_everybody(labels("fm", BANDS80), stems=R25)
    assert word is None and "85, 90" in why


@pytest.mark.parametrize("cols, words", [
    (labels("fm", BANDS90)[:-1], "men (m_) lack the band 90"),
    ([c for c in labels("fm", BANDS90) if c != "f_45_2020"],
     "women (f_) lack the band 45"),
    (labels("f", BANDS90), "not both women's and men's files"),
    (labels("fm", [0, 15]), "lack the bands 1, 5, 10"),
    (labels("fm", BANDS90) + ["ppp_2020"], "'ppp_2020' is not an age"),
    (labels("fm", BANDS90) + labels("fm", BANDS90, "2025"),
     "2 years (2020, 2025)")])
def test_anything_less_is_refused_and_says_why(cols, words):
    """A gap, one sex only, a layer that is not age-and-sex, or two
    years with none chosen: refused, saying which.

    BROKEN WITH: `full` accepting any band set that starts at 0."""
    word, why = infer_everybody(cols, stems=R25)
    assert word is None and words in why, why


def test_a_chosen_year_settles_a_folder_of_two():
    """BROKEN WITH: the chosen year ignored (two years always refused)."""
    cols = labels("fm", BANDS90) + labels("fm", BANDS90, "2025")
    word, why = infer_everybody(cols, year="2025", stems=R25)
    assert word == "sexes" and "2025" in why


# -------------------------------------------------- a folder on disk
def _folder(tmp_path, sexes, bands, drop=()):
    import rasterio
    from rasterio.transform import from_origin
    px = 1.0 / 1200
    value = {"f": 2.0, "m": 3.0, "t": 5.0}
    for s in sexes:
        for a in bands:
            name = f"bdi_{s}_{a:02d}_2020_CN_1km_R2025A_UA_v1"
            if name in drop:
                continue
            with rasterio.open(
                    tmp_path / f"{name}.tif", "w", driver="GTiff",
                    height=3, width=3, count=1, dtype="float32",
                    crs="EPSG:4326", nodata=-99999.0,
                    transform=from_origin(30.0, -2.0 + 3 * px, px,
                                          px)) as d:
                d.write(np.full((3, 3), value[s], dtype="float32"), 1)
    return tmp_path


def test_a_blank_box_runs_a_full_folder_and_says_so(tmp_path, capsys):
    """John's case end to end: 5a's folder, k given, the box blank. It
    runs, counts women plus men, says so in the log, and the run's
    record says the choice was automatic and lists the columns.

    BROKEN WITH: folder_to_cells not calling infer_everybody."""
    from equipop.doors.continental import run_folder
    man = run_folder(_folder(tmp_path, "fm", BANDS90), k_values=[10],
                     unit_size=1000.0, epsg=32735)
    said = capsys.readouterr().out
    assert "No population was named, so EVERYBODY - weight='sexes'" in said
    rp = man["reference_population"]
    assert rp["weight"] == "sexes" and rp["chosen"] == "automatically"
    assert len(rp["columns"]) == 2 * len(BANDS90)
    assert "every age band" in rp["why"]
    asked = run_folder(tmp_path, k_values=[10], unit_size=1000.0,
                       epsg=32735, weight="sexes")
    assert asked["reference_population"]["chosen"] == "as asked"
    assert man["results"].equals(asked["results"])


def test_a_folder_missing_one_band_is_still_refused(tmp_path):
    """BROKEN WITH: the refusal skipped whenever every sex is present."""
    from equipop.doors.continental import run_folder
    folder = _folder(tmp_path, "fm", BANDS90,
                     drop=("bdi_m_90_2020_CN_1km_R2025A_UA_v1",))
    with pytest.raises(ValueError) as e:
        run_folder(folder, k_values=[10], unit_size=1000.0, epsg=32735)
    msg = str(e.value)
    assert "cannot be taken as everybody" in msg
    assert "men (m_) lack the band 90" in msg
    assert "weight='sexes'" in msg


def test_pro_shows_the_refusal_as_a_message_not_a_traceback(tmp_path):
    """John's 16 October traceback: Pro let the loader's ValueError
    through as Python's own error. It now arrives as a tool message,
    as it has in QGIS since 1.43.

    BROKEN WITH: Pro's ContinentalRasters catching ContinentalError
    only."""
    import pandas as pd
    import test_arcgis_stub as H
    H._install_fake_arcpy(pd.DataFrame({"x": [0.0]}))
    pyt = H._load_pyt()
    import arcpy
    folder = _folder(tmp_path, "fm", [0, 15])
    tool = pyt.ContinentalRasters()
    params = tool.getParameterInfo()
    for p in params:
        if p.name == "folder":
            p.value = str(folder)
        elif p.name == "k":
            p.value = "10"
    with pytest.raises(arcpy.ExecuteError, match="cannot be taken as "
                                                 "everybody"):
        tool.execute(params, H._Messages())
