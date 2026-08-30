"""BACKLOG 220 - the lattice join.

QGIS already counts points in cells and does it well. THE HARD PART IS
THE LATTICE: EquiPop knows the exact grid the demographic points sit
on and QGIS does not, so a join done outside is a spatial join with
tolerances and at a cell boundary you cannot say where a supermarket
landed. Here the answer is exact, because the grid is ours - and these
tests are mostly about proving that word.

AND THE POINT IS NOT THE COUNT. "How many supermarkets in this cell"
is almost always zero. The question is how many among the k nearest
people, which is 2SFCA - already in equipop/fca.py and never yet
driven at continental scale. So the output here is shaped to be fca()'s
supply frame.
"""
from __future__ import annotations

import contextlib
import io
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("rasterio")

from equipop.latticejoin import (  # noqa: E402
    LatticeError, join_to_points, lattice_of, snap_to_lattice)
from equipop.rasterfolder import load_folder  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "worldpop"


@pytest.fixture(scope="module")
def points():
    with contextlib.redirect_stdout(io.StringIO()):
        pts, _ = load_folder(FIX, keep_index=True)
    return pts


def _snap(*a, **kw):
    with contextlib.redirect_stdout(io.StringIO()):
        return snap_to_lattice(*a, **kw)


# ------------------------------------------------------- the lattice
def test_the_lattice_comes_from_the_rasters_themselves():
    L = lattice_of(FIX)
    assert L["crs"] == "EPSG:4326"
    assert abs(L["a"] - 1.0 / 1200) < 1e-9, "3 arc-seconds"


def test_no_rasters_means_no_lattice_and_it_says_so():
    with pytest.raises(LatticeError, match="no lattice"):
        lattice_of("/no/such/folder")


def test_the_points_can_carry_their_index(points):
    """Without it the join can only be by distance, which is the thing
    this module exists to avoid."""
    assert {"gx", "gy"} <= set(points.columns)


def test_the_index_is_off_by_default():
    with contextlib.redirect_stdout(io.StringIO()):
        pts, _ = load_folder(FIX)
    assert "gx" not in pts.columns, "machinery should not leak by default"


# ----------------------------------------------------- exactness
def test_a_point_lands_on_the_cell_it_came_from(points):
    """THE WHOLE CLAIM. Take 40 real cell centres, snap them, and
    every one must return to its own cell - not a nearby one."""
    take = points.sample(40, random_state=1)
    got = _snap(take["lon"].to_numpy(), take["lat"].to_numpy(),
                like=FIX, name="shops")
    assert set(zip(got.gx, got.gy)) == set(zip(take.gx, take.gy))


def test_points_anywhere_inside_a_cell_land_together():
    L = lattice_of(FIX)
    y = L["f"] + (-200 + 0.5) * L["e"]
    xs = L["c"] + (100 + np.array([0.01, 0.25, 0.5, 0.75, 0.99])) * L["a"]
    got = _snap(xs, np.full(5, y), like=FIX, name="n")
    assert len(got) == 1 and got["n"].iloc[0] == 5.0


def test_adjacent_cells_stay_distinct():
    L = lattice_of(FIX)
    y = L["f"] + (-200 + 0.5) * L["e"]
    xs = L["c"] + (100 + np.array([0.5, 1.5])) * L["a"]
    got = _snap(xs, np.full(2, y), like=FIX, name="n").sort_values("gx")
    assert len(got) == 2
    assert got.gx.iloc[1] - got.gx.iloc[0] == 1


def test_a_coordinate_ON_a_boundary_is_not_guaranteed_either_way():
    """The honest limit, and it is not fixable.

    A coordinate built as origin + 100*pixel, divided back, gives
    99.999999999999 - because adding a small offset to a number near
    29 degrees and subtracting it again loses bits. So a point within
    one floating-point ulp of an edge may fall either side, whatever
    rounding rule is used. Real coordinates are never on an edge; this
    test exists so nobody later "fixes" it and believes they have.
    """
    L = lattice_of(FIX)
    edge = L["c"] + 100 * L["a"]
    back = (edge - L["c"]) / L["a"]
    assert abs(back - 100.0) < 1e-9, "still the same cell to any sane test"
    assert back != 100.0, (
        "if this ever becomes exact the caveat can go - but check WHY "
        "before removing the warning")


# ---------------------------------------------------------- joining
def test_the_join_is_on_indices_and_changes_no_rows(points):
    take = points.sample(30, random_state=2)
    got = _snap(take["lon"].to_numpy(), take["lat"].to_numpy(),
                like=FIX, name="shops")
    out = join_to_points(points, got, "shops")
    assert len(out) == len(points)
    assert out["shops"].sum() == pytest.approx(30.0)


def test_cells_the_layer_never_touched_are_a_real_zero(points):
    take = points.sample(10, random_state=3)
    got = _snap(take["lon"].to_numpy(), take["lat"].to_numpy(),
                like=FIX, name="shops")
    out = join_to_points(points, got, "shops")
    assert out["shops"].notna().all(), "0.0, not an absence"
    assert (out["shops"] == 0).sum() == len(points) - len(got)


def test_joining_without_indices_is_refused_with_the_fix_named(points):
    bare = points.drop(columns=["gx", "gy"])
    got = _snap(points["lon"].to_numpy()[:5],
                points["lat"].to_numpy()[:5], like=FIX, name="s")
    with pytest.raises(LatticeError, match="keep_index"):
        join_to_points(bare, got, "s")


def test_only_occupied_cells_are_returned(points):
    """A supermarket layer touches a vanishing fraction of a continent.
    Listing every empty cell would be tens of millions of rows saying
    nothing."""
    take = points.sample(5, random_state=4)
    got = _snap(take["lon"].to_numpy(), take["lat"].to_numpy(),
                like=FIX, name="s")
    assert len(got) == 5 <= len(points)


# ------------------------------------------------------ sum and count
def test_summing_a_field_instead_of_counting(points):
    take = points.sample(6, random_state=5)
    vals = np.arange(1.0, 7.0)
    got = _snap(take["lon"].to_numpy(), take["lat"].to_numpy(),
                like=FIX, values=vals, name="beds", how="sum")
    assert got["beds"].sum() == pytest.approx(vals.sum())


def test_several_points_in_one_cell_add_up():
    L = lattice_of(FIX)
    y = L["f"] + (-200 + 0.5) * L["e"]
    xs = L["c"] + (100 + np.array([0.2, 0.4, 0.6])) * L["a"]
    got = _snap(xs, np.full(3, y), like=FIX, values=[2.0, 3.0, 5.0],
                name="beds", how="sum")
    assert len(got) == 1 and got["beds"].iloc[0] == pytest.approx(10.0)


# ---------------------------------------------------------- refusals
def test_sum_without_values_is_refused_by_name():
    with pytest.raises(LatticeError, match="needs a value per point"):
        _snap([30.0], [-2.0], like=FIX, how="sum")


def test_an_unknown_how_is_refused():
    with pytest.raises(LatticeError, match="count.*sum"):
        _snap([30.0], [-2.0], like=FIX, how="average")


def test_mismatched_coordinates_are_refused():
    with pytest.raises(LatticeError, match="against"):
        _snap([30.0, 31.0], [-2.0], like=FIX)


def test_no_lattice_named_is_refused_with_the_fix():
    with pytest.raises(LatticeError, match="Which lattice"):
        _snap([30.0], [-2.0])


def test_all_missing_coordinates_are_refused():
    with pytest.raises(LatticeError, match="No usable coordinates"):
        _snap([np.nan, np.nan], [np.nan, np.nan], like=FIX)


def test_some_missing_coordinates_are_dropped_and_counted():
    L = lattice_of(FIX)
    y = L["f"] + (-200 + 0.5) * L["e"]
    x = L["c"] + 100.5 * L["a"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        got = snap_to_lattice([x, np.nan], [y, y], like=FIX, name="s")
    assert got["s"].sum() == 1.0
    assert "no usable coordinate" in buf.getvalue()


# ------------------------------------------------- shaped for the FCA
def test_the_output_is_what_fca_wants_as_supply(points):
    """fca(demand, supply, ...) takes x, y and a supply column. The
    demand side is machine 3's points; this is the supply side; the
    neighbourhood is the same k in both."""
    take = points.sample(8, random_state=6)
    got = _snap(take["lon"].to_numpy(), take["lat"].to_numpy(),
                like=FIX, name="shops")
    assert {"lon", "lat", "shops"} <= set(got.columns)
    supply = got.rename(columns={"lon": "x", "lat": "y"})
    assert {"x", "y", "shops"} <= set(supply.columns)
    assert len(supply) == 8


def test_the_lattice_reports_the_crs_the_caller_must_honour():
    """BACKLOG 239, one level up: a coordinate is a pair of numbers and
    carries no world with it. Passing metres to a degree lattice puts
    everything in one cell near the origin without complaint, so the
    CRS has to be available for the caller to check."""
    L = lattice_of(FIX)
    assert L["crs"] == "EPSG:4326"
    assert "from" in L, "say WHICH raster defined the grid"


def test_metres_against_a_degree_lattice_give_absurd_indices():
    """The failure this cannot prevent, pinned so it is documented.

    Nothing here can know what the caller's numbers mean. What it CAN
    do is report its own CRS, which it does.

    Claude PREDICTED these would collapse into one cell. They do not -
    they produce lattice indices in the hundreds of millions, because
    166,500 metres read as degrees is 166,500 degrees. That is the
    LOUDER failure and the better one, but the prediction was wrong
    and the test now records what actually happens.
    """
    L = lattice_of(FIX)
    got = _snap(np.array([166500.0, 166600.0, 166700.0]),
                np.array([9778500.0, 9778600.0, 9778700.0]),
                like=FIX, name="n")
    assert len(got) == 3
    assert got["gx"].abs().min() > 1_000_000, (
        "indices this large mean the coordinates were not in the "
        "lattice's CRS - a sanity check a caller can apply")
    assert abs(got["lon"]).max() > 180, (
        "and the resulting 'longitude' is off the planet")
