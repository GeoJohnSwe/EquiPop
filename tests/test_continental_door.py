"""BACKLOG 38 - the one function both doors sit on.

The rule that decides what a continental run does lives HERE and not
in the doors, because it has drifted three times when it lived in two
places. These tests exercise it without QGIS or arcpy, which is the
point of putting it in the package.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("rasterio")
from equipop.doors.continental import (  # noqa: E402
    ContinentalError, run_folder, TILE_ADVISED_CELLS)

FIX = Path(__file__).resolve().parent / "fixtures" / "worldpop"


class _Channel:
    """Stands in for a door's message pane."""

    def __init__(self):
        self.info_lines, self.warnings = [], []

    def info(self, m):
        self.info_lines.append(str(m))

    def warning(self, m):
        self.warnings.append(str(m))

    # doors.report.speaking() only needs .info
    def __repr__(self):
        return f"<Channel {len(self.info_lines)}i {len(self.warnings)}w>"


def test_a_folder_of_rasters_runs_end_to_end():
    ch = _Channel()
    man = run_folder(FIX, k_values=[500], unit_size=1000.0,
                     epsg=32735, channel=ch)
    assert man["cells"] > 0
    assert len(man["results"]) == man["cells"]
    assert "Dist_500" in man["results"].columns
    assert "N_500" in man["results"].columns
    n = man["results"]["N_500"].to_numpy(float)
    assert np.allclose(n[np.isfinite(n)], 500.0), (
        "k fixes the population; N_k must be exactly k")


def test_the_pane_is_told_what_happened():
    ch = _Channel()
    run_folder(FIX, k_values=[500], unit_size=1000.0, epsg=32735,
               channel=ch)
    said = " ".join(ch.info_lines)
    assert "cells of 1000 m" in said
    assert "points" in said and "people" in said
    # the sentence that stops Dist_k being read as an error
    assert "radius" in said.lower()


def test_a_country_per_folder_tree_is_the_same_as_a_flat_one(tmp_path):
    """John's downloads arrive one folder per country. Keep them.

    Verified rather than assumed: the nested tree and the flat folder
    must give the identical table, to the row.
    """
    for tif in sorted(FIX.glob("*.tif")):
        sub = tmp_path / tif.name[:3]
        sub.mkdir(exist_ok=True)
        shutil.copy(tif, sub / tif.name)
    flat = run_folder(FIX, k_values=[500], unit_size=1000.0, epsg=32735)
    nest = run_folder(tmp_path, k_values=[500], unit_size=1000.0,
                      epsg=32735)
    assert nest["points"] == flat["points"]
    assert nest["cells"] == flat["cells"]
    a = flat["results"].sort_values(["EastWest", "NorthSouth"])
    b = nest["results"].sort_values(["EastWest", "NorthSouth"])
    assert np.allclose(a["Dist_500"].to_numpy(float),
                       b["Dist_500"].to_numpy(float), equal_nan=True)


def test_the_country_never_becomes_a_column():
    """Different countries are different GROUND, so they stack as rows.

    If iso3 leaked into the column name, each country's people would
    sit in a column of their own full of zeros - the back-fill mistake
    in a new costume.
    """
    man = run_folder(FIX, k_values=[500], unit_size=1000.0, epsg=32735)
    assert list(man["labels"]) == ["f_15_2020"], man["labels"]
    assert len(man["labels"]["f_15_2020"]) == 3


def test_a_tiled_run_writes_and_says_where(tmp_path):
    out = tmp_path / "run"
    ch = _Channel()
    man = run_folder(FIX, k_values=[500], unit_size=1000.0, epsg=32735,
                     out_dir=str(out), tile_m=20_000.0, channel=ch)
    assert man["tiles"] >= 1
    assert (out / "manifest.json").exists()
    assert "load_tiled" in " ".join(ch.info_lines)

    from equipop.bigrun import load_tiled
    back = load_tiled(str(out))
    assert len(back) == man["cells"]


def test_tiled_and_untiled_agree(tmp_path):
    """bigrun tiles ORIGINS, not the tree, so there is no seam."""
    from equipop.bigrun import load_tiled
    flat = run_folder(FIX, k_values=[500], unit_size=1000.0, epsg=32735)
    out = tmp_path / "run"
    run_folder(FIX, k_values=[500], unit_size=1000.0, epsg=32735,
               out_dir=str(out), tile_m=20_000.0)
    a = flat["results"].sort_values(["EastWest", "NorthSouth"])
    b = load_tiled(str(out)).sort_values(["EastWest", "NorthSouth"])
    assert len(a) == len(b)
    d = np.abs(a["N_500"].to_numpy(float) - b["N_500"].to_numpy(float))
    assert np.nanmax(d) < 1e-3, "tiling must not move the answer"


# ------------------------------------------------------- refusals
def test_no_k_gives_the_POINT_TABLE_rather_than_a_refusal():
    """John: "what are we generating - if the answer is a point-file
    with the coordinates and values listed we are at a good place".

    It used to refuse. That was the tool imposing a shape his data
    does not have: with sixty cohorts there is no single population,
    so demanding a k - and therefore a weight - before producing
    anything made the useful first step impossible.
    """
    ch = _Channel()
    man = run_folder(FIX, unit_size=1000.0, channel=ch)
    pts = man["points_table"]
    assert {"lon", "lat"} <= set(pts.columns)
    assert len(pts) == man["points"]
    assert "results" not in man, "nothing should have been computed"
    said = " ".join(ch.info_lines)
    assert "point table" in said and "Give a k" in said


def test_the_point_table_needs_no_weight():
    """The refusal John hit cannot arise on this path at all."""
    man = run_folder(FIX, unit_size=1000.0)
    assert len(man["points_table"]) > 0


@pytest.mark.parametrize("word", ["total", "sexes"])
def test_a_weight_can_be_a_WORD_not_a_column_name(word, tmp_path):
    """With sixty cohorts the population is a SUM, not a column."""
    import shutil
    import rasterio
    from rasterio.transform import from_origin
    import numpy as np
    px = 1.0 / 1200
    for sex, v in (("f", 2.0), ("m", 3.0), ("t", 5.0)):
        a = np.full((4, 4), v, dtype="float32")
        with rasterio.open(
                tmp_path / f"bdi_{sex}_15_2026_CN_1km_R2025A_UA_v1.tif",
                "w", driver="GTiff", height=4, width=4, count=1,
                dtype="float32", crs="EPSG:4326", nodata=-99999.0,
                transform=from_origin(30.0, -2.0 + 4 * px, px, px)) as d:
            d.write(a, 1)
    man = run_folder(tmp_path, k_values=[10], unit_size=1000.0,
                     weight=word, epsg=32735)
    # t is 5 per cell; f+m is also 5 per cell. Either route, same people.
    assert man["weight_column"] == "_people"
    assert man["results"]["N_10"].notna().any()


def test_the_refusal_names_the_choices_rather_than_the_columns():
    """The old message listed sixty column names and no way forward."""
    from equipop.rasterfolder import folder_to_cells
    import shutil
    with pytest.raises(ValueError) as e:
        # two cohorts, so no single column can be assumed
        folder_to_cells(FIX, unit_size=1000.0, epsg=32735,
                        labels={p.stem: f"c{i}" for i, p in
                                enumerate(sorted(FIX.glob("*.tif")))})
    msg = str(e.value)
    assert "weight='total'" in msg and "weight='sexes'" in msg
    assert "number of PEOPLE" in msg


@pytest.mark.parametrize("bad", [0, -5, None])
def test_a_useless_k_is_refused_by_name(bad):
    with pytest.raises(ContinentalError, match="positive number of people"):
        run_folder(FIX, k_values=[bad], unit_size=1000.0)


@pytest.mark.parametrize("bad", [0, -100])
def test_a_useless_cell_size_is_refused_by_name(bad):
    with pytest.raises(ContinentalError, match="positive number of metres"):
        run_folder(FIX, k_values=[500], unit_size=bad)


def test_a_folder_that_is_not_there_says_so_and_says_what_to_point_at():
    with pytest.raises(ContinentalError) as e:
        run_folder("/no/such/folder/anywhere", k_values=[500],
                   unit_size=1000.0)
    assert "Not a folder" in str(e.value)
    assert "subfolders" in str(e.value), (
        "the refusal should tell the user their country-per-folder "
        "layout is fine")


def test_the_large_run_advice_is_a_warning_not_a_refusal(monkeypatch):
    """A big untiled run is a bad idea, not an illegal one."""
    monkeypatch.setattr("equipop.doors.continental.TILE_ADVISED_CELLS", 10)
    ch = _Channel()
    man = run_folder(FIX, k_values=[500], unit_size=1000.0, epsg=32735,
                     channel=ch)
    assert "results" in man, "it must still run"
    assert any("tile" in w.lower() for w in ch.warnings)


def test_the_advice_is_quiet_when_the_run_is_small():
    ch = _Channel()
    run_folder(FIX, k_values=[500], unit_size=1000.0, epsg=32735,
               channel=ch)
    assert not any("large untiled" in w for w in ch.warnings)
    assert TILE_ADVISED_CELLS > 1000
