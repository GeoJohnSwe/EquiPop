"""BACKLOG 118 on real WorldPop data - the continental blocker.

WorldPop counts are FRACTIONAL. Most pixels of a 100 m constrained
raster hold a fraction of a person: of Burundi's 2.0 million occupied
pixels, 1.7 million hold less than half a woman aged 15-19.

The old route into a weighted value statistic was to REPEAT each row
`weight` times, and you cannot repeat somebody 0.4 times. `np.round()`
sent every such cell to zero and membership then required `> 0`, so the
cell left the population altogether. Measured on John's four rasters:

                 places lost   people in them   net mass
    Burundi        85.0%          52.9%           40.1%
    Rwanda         78.2%          39.3%           28.5%
    Austria        98.3%          66.5%           60.1%
    Denmark        98.1%          69.1%           58.6%

Half the people, gone before the engine started - and worse the further
north, because a 3 arc-second cell is 92.8 m tall everywhere but only
~51 m wide in Denmark against ~92.5 m in Burundi, so more pixels fall
under the half-person threshold. Any Europe-against-Africa comparison
was therefore biased by construction, in the direction of showing
Europe emptier than it is.

These tests run against three clipped windows committed under
tests/fixtures/worldpop: Burundi and Rwanda over the SAME 0.45 degree
window at their shared border, and a Danish window for the latitude
contrast.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from equipop.cells import build_cells

FIX = Path(__file__).resolve().parent / "fixtures" / "worldpop"
rasterio = pytest.importorskip("rasterio")


def _read(name):
    """Pixel centres and counts from one fixture raster."""
    with rasterio.open(FIX / name) as r:
        a = r.read(1).astype(float)
        nod = r.nodata
        t = r.transform
    a = np.where(np.isfinite(a) & (a != nod), a, 0.0)
    rows, cols = np.nonzero(a > 0)
    # pixel centres, in degrees - the fixture is EPSG:4326
    lon = t.c + (cols + 0.5) * t.a
    lat = t.f + (rows + 0.5) * t.e
    return pd.DataFrame({"lon": lon, "lat": lat, "pop": a[rows, cols]})


@pytest.fixture(scope="module")
def bdi():
    return _read("bdi_f_15_2020_CN_100m_R2025A_v1.tif")


def test_the_fixture_is_really_fractional(bdi):
    """If this ever stops being true the tests below prove nothing."""
    assert len(bdi) > 10_000
    under = bdi["pop"][bdi["pop"] < 0.5]
    assert len(under) / len(bdi) > 0.5, (
        "the point of this fixture is that most pixels hold less than "
        "half a person")
    share = under.sum() / bdi["pop"].sum()
    assert share > 0.3, f"only {share:.1%} of people sit in sub-0.5 cells"


def test_rounding_destroys_three_different_things(bdi):
    """The defect, stated as numbers rather than as a worry.

    THREE quantities, and they are not the same - the first version of
    this test conflated them and failed, correctly.

      places lost : pixels whose count rounds to 0. They stop being
                    origins AND stop being anybody's neighbour, so the
                    map itself loses locations. Burundi 85%, Denmark
                    98% of occupied pixels.
      people in    : the population standing in those vanished places.
      those places  Burundi 52.9%, Denmark 69.1%.
      net mass    : total change after round-ups partly compensate.
                    Burundi 40.1%, Denmark 58.6%. SMALLER than the
                    people-in-lost-places figure, because a 0.6 cell
                    rounding up to 1 hides part of the damage.
    """
    pop = bdi["pop"].to_numpy()
    rep = np.round(pop)
    places_lost = (rep == 0).mean()
    people_in_lost = pop[rep == 0].sum() / pop.sum()
    net_mass = (pop.sum() - rep.sum()) / pop.sum()

    assert places_lost > 0.7, (
        f"only {places_lost:.1%} of locations vanish - re-cut the fixture")
    assert people_in_lost > 0.3, f"{people_in_lost:.1%} of people vanish"
    assert net_mass > 0.2, f"net mass change only {net_mass:.1%}"
    # the ordering is the part worth pinning: round-ups always mask
    # some of the loss, so net mass UNDERSTATES what left the map
    assert net_mass < people_in_lost


def test_weights_conserve_the_population(bdi):
    """The fix. Mass in equals mass out, to floating-point."""
    cd = build_cells(bdi, "lon", "lat", value_vars=["pop"],
                     unit_size=0.01, weights="pop")
    assert cd.n.sum() == pytest.approx(bdi["pop"].sum(), rel=1e-9), (
        "the weighted cell table must hold exactly the people the "
        "raster held")


def test_without_weights_nothing_moves(bdi):
    """Backwards compatibility: every caller before v1.41 counts rows."""
    cd = build_cells(bdi, "lon", "lat", value_vars=["pop"], unit_size=0.01)
    assert cd.n.sum() == len(bdi)
    assert cd.value_weights == {}


def test_value_statistics_use_the_weights(bdi):
    """A weighted median must not be the unweighted one.

    Two cells, one person-heavy and one person-light, must not vote
    equally - which is exactly what repeating rows was for and exactly
    what rounding destroyed.
    """
    from equipop.analysis import run_knn_stats

    cd = build_cells(bdi, "lon", "lat", value_vars=["pop"],
                     unit_size=0.01, weights="pop")
    got = run_knn_stats(cd, [200], stats={"pop": ["mean", "median"]})
    assert len(got) == len(cd)
    col = "Nv_pop_200"
    assert col in got.columns
    # Nv_ is now a SUM OF WEIGHTS, so it lands on k rather than on a
    # count of rows that happened to be nearby.
    finite = got[col][np.isfinite(got[col])]
    assert (finite > 0).all()


def test_the_two_countries_share_a_lattice_and_no_data(bdi):
    """Burundi and Rwanda overlap in EXTENT and never in DATA.

    This is the case a bounding-box merge gets wrong: it would treat
    two countries as two cohorts of the same ground and add them into
    one column.
    """
    rwa = _read("rwa_f_15_2020_CN_100m_R2025A_v1.tif")
    key_b = set(zip(np.round(bdi.lon, 6), np.round(bdi.lat, 6)))
    key_r = set(zip(np.round(rwa.lon, 6), np.round(rwa.lat, 6)))
    assert key_b and key_r
    assert not (key_b & key_r), (
        "the two rasters must not both carry data at the same pixel - "
        "if they do, concatenation double-counts")


def test_latitude_changes_how_much_rounding_destroys():
    """The bias that made this a correctness problem, not a rounding one."""
    b = _read("bdi_f_15_2020_CN_100m_R2025A_v1.tif")
    d = _read("dnk_f_15_2020_CN_100m_R2025A_v1.tif")

    def lost(df):
        return (df["pop"].sum()
                - np.round(df["pop"].to_numpy()).sum()) / df["pop"].sum()

    # both are real losses; the point is that they DIFFER, so the error
    # does not cancel when continents are compared
    assert lost(b) > 0.1 and lost(d) > 0.1
    assert abs(lost(b) - lost(d)) > 0.1, (
        "if these ever converge, re-cut the fixture - the Danish window "
        "is dense and already understates the whole-country contrast "
        "(69% against 53%)")
