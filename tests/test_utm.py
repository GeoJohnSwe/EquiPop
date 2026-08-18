"""BACKLOG 177 - UTM in numpy alone.

John's specification, v1.37:

    "for professional spatial analysts, this function is not needed,
    they will have routines for projecting the data as they need and
    want - However, for the unexperienced stat and econ people that
    are not trained to think beyond lat/long, a simple function to
    generate good-enough projections are what is needed. I think that
    we should communicate in the output which projection that was used
    in each case (i.e. EPSG code for UTM would be enough)"

Two things follow, and both are tested here: the arithmetic has to be
RIGHT, because a beginner cannot check it; and the EPSG code has to
come back with the answer, because a projection nobody can name is not
reproducible.

The reference test compares against pyproj. pyproj is not needed to
RUN this - that is the entire point of writing it - but where it is
installed it is the right thing to be judged against.
"""

import numpy as np
import pytest

from equipop import utm


def test_it_agrees_with_pyproj_across_every_zone():
    """120 zones, 200 points each, north and south.

    Neighbourhoods are measured in hundreds of metres, so millimetres
    are far below anything that matters. Agreement at this level is
    not about precision - it is evidence the implementation is right
    rather than merely plausible.
    """
    Transformer = pytest.importorskip("pyproj").Transformer

    rng = np.random.default_rng(7)
    worst = 0.0
    for zone in range(1, 61):
        lon0 = (zone - 1) * 6 - 180 + 3
        for south in (False, True):
            epsg = (32700 if south else 32600) + zone
            lat = (rng.uniform(-79, -1, 200) if south
                   else rng.uniform(0, 83, 200))
            lon = rng.uniform(lon0 - 3, lon0 + 3, 200)
            e, n, _ = utm.to_utm(lat, lon, epsg)
            E, N = Transformer.from_crs(
                4326, epsg, always_xy=True).transform(lon, lat)
            worst = max(worst, float(np.hypot(e - E, n - N).max()))
    assert worst < 1e-3, f"worst disagreement {worst * 1000:.4f} mm"


def test_the_round_trip_returns_the_original_degrees():
    """Independent of pyproj: the inverse must undo the forward."""
    rng = np.random.default_rng(11)
    lat = rng.uniform(-70, 80, 500)
    lon = rng.uniform(-6, 6, 500)
    e, n, epsg = utm.to_utm(lat, lon)
    back_lat, back_lon = utm.from_utm(e, n, epsg)
    assert np.abs(back_lat - lat).max() < 1e-9
    assert np.abs(back_lon - lon).max() < 1e-9


def test_a_known_point_lands_where_it_should():
    """One hand-checkable case, so a broken series cannot pass by
    agreeing with a broken inverse. On the central meridian the
    easting is exactly the false easting."""
    e, n, epsg = utm.to_utm([0.0], [3.0], 32631)
    assert abs(e[0] - 500000.0) < 1e-6
    assert abs(n[0] - 0.0) < 1e-6
    assert epsg == 32631


def test_the_zone_and_epsg_follow_the_longitude():
    assert utm.utm_zone(-180) == 1
    assert utm.utm_zone(179.9) == 60
    assert utm.utm_zone(0.0) == 31
    assert utm.utm_epsg(59.9, 10.7) == 32632        # Oslo
    assert utm.utm_epsg(-33.9, 18.4) == 32734       # Cape Town
    assert utm.utm_epsg(41.7, -71.3) == 32619       # Bristol County, RI


def test_the_projection_says_what_it_was():
    """John's condition on the whole feature."""
    assert utm.describe(32633) == "UTM zone 33N (EPSG:32633)"
    assert utm.describe(32734) == "UTM zone 34S (EPSG:32734)"
    assert "32619" in utm.describe(32619)


def test_the_zone_is_chosen_by_the_median_not_the_mean():
    """A fringe of far-away points must not drag the whole dataset
    into a zone that holds none of it - the failure suggest_projection
    was written for."""
    lat = np.array([41.7] * 100 + [41.7] * 3)
    lon = np.array([-71.3] * 100 + [120.0, 121.0, 119.0])
    assert utm.choose_epsg(lat, lon) == 32619
    # and the mean really would have chosen differently, which is the
    # whole reason the median is used
    assert utm.utm_epsg(41.7, float(np.mean(lon))) != 32619


def test_missing_coordinates_stay_missing_and_keep_their_row():
    """Row alignment is the contract with Stata: a row without a
    position must not acquire one, and must not vanish either."""
    lat = np.array([41.7, np.nan, 41.8])
    lon = np.array([-71.3, -71.2, np.nan])
    e, n, _ = utm.to_utm(lat, lon)
    assert len(e) == 3 and len(n) == 3
    assert np.isfinite(e[0]) and np.isfinite(n[0])
    assert np.isnan(e[1]) and np.isnan(n[1])
    assert np.isnan(e[2]) and np.isnan(n[2])


def test_already_projected_data_is_refused_not_mangled():
    """Metres passed as degrees would silently produce nonsense."""
    with pytest.raises(utm.ProjectionRefused) as exc:
        utm.to_utm([6598000.0, 6599000.0], [598000.0, 599000.0])
    assert "not degrees" in str(exc.value)


def test_polar_data_is_refused_by_name():
    with pytest.raises(utm.ProjectionRefused) as exc:
        utm.to_utm([86.0, 87.0], [10.0, 11.0])
    assert "84" in str(exc.value)


def test_all_missing_is_refused_with_a_usable_message():
    with pytest.raises(utm.ProjectionRefused) as exc:
        utm.choose_epsg([np.nan, np.nan], [np.nan, np.nan])
    assert "no usable coordinates" in str(exc.value)


def test_a_bad_epsg_is_refused():
    with pytest.raises(utm.ProjectionRefused):
        utm.to_utm([41.7], [-71.3], 4326)


def test_degree_detection_is_conservative():
    """It only ever warns, so a false positive costs a sentence. A
    false NEGATIVE costs a silently wrong answer, which is why the
    envelope test is the one used."""
    assert utm.looks_like_degrees([-71.3, -71.2], [41.7, 41.8])
    assert not utm.looks_like_degrees([598000.0], [6598000.0])
    assert not utm.looks_like_degrees([np.nan], [np.nan])


def test_distances_in_degrees_are_wrong_by_the_amount_we_claim():
    """Why the warning exists at all, in numbers.

    At Bristol County's latitude a degree of longitude is cos(41.7)
    times a degree of latitude - about 75%. Treating degrees as a plane
    therefore stretches the neighbourhood north-south relative to the
    truth, and it is not a rounding error: it changes which cells fall
    inside a k-neighbourhood.
    """
    lat0, lon0 = 41.7, -71.3
    e, n, _ = utm.to_utm([lat0, lat0, lat0 + 1.0], [lon0, lon0 + 1.0, lon0])
    east_metres = abs(e[1] - e[0])
    north_metres = abs(n[2] - n[0])
    ratio = east_metres / north_metres
    assert 0.72 < ratio < 0.78, ratio      # ~cos(41.7 degrees)


def test_zone_span_counts_the_zones_covered():
    assert utm.zone_span([41.7, 41.8], [-71.3, -71.2]) == 1
    # Oslo (zone 32) to Lyon (zone 31) - two, which is ordinary
    assert utm.zone_span([59.9, 45.8], [10.7, 4.8]) == 2
    # add Warsaw (zone 34)
    assert utm.zone_span([59.9, 45.8, 52.2], [10.7, 4.8, 21.0]) == 4
    assert utm.zone_span([np.nan], [np.nan]) == 0


def test_one_or_two_zones_pass_without_a_word():
    """A dataset near a boundary straddles two zones as a matter of
    course. Saying so every time would be noise."""
    assert utm.zone_span_note([41.7, 41.8], [-71.3, -71.2]) is None
    assert utm.zone_span_note([59.9, 45.8], [10.7, 4.8]) is None


def test_three_zones_get_a_note_that_does_not_refuse():
    """John's ruling: inform, never block.

    The note is honesty about what was done, not a warning of a defect.
    """
    note = utm.zone_span_note([59.9, 45.8, 52.2], [10.7, 4.8, 21.0],
                              epsg=32632)
    assert note is not None
    assert "4 UTM zones" in note
    assert "32632" in note
    assert "continues" in note
    assert "%" in note, "the note should carry the figure for THIS data"
    # and the projection itself still works on the same data
    e, n, epsg = utm.to_utm([59.9, 45.8, 52.2], [10.7, 4.8, 21.0])
    assert np.isfinite(e).all() and np.isfinite(n).all()


def test_the_note_explains_the_ORDER_argument_not_just_the_distance():
    """The reason the run may continue is that neighbourhoods depend on
    the rank of neighbours rather than on absolute distance. If the
    sentence loses that, it reads as an unexplained risk."""
    note = utm.zone_span_note([59.9, 45.8, 52.2], [10.7, 4.8, 21.0])
    assert "ORDER" in note or "order" in note
    assert "rank" in note


def test_the_single_zone_stretch_is_the_size_we_claim():
    """Measured, not asserted: how wrong is a distance three zones from
    the central meridian?

    The note tells the user 'well under one percent'. That number
    should come from arithmetic, not from confidence.
    """
    Geod = pytest.importorskip("pyproj").Geod
    geod = Geod(ellps="WGS84")

    epsg = 32633                      # central meridian 15E
    lat0 = 50.0
    worst = 0.0
    for lon in (15.0, 18.0, 21.0, 24.0):        # 0 to 9 degrees out
        lat_pair = [lat0, lat0 + 0.05]
        lon_pair = [lon, lon]
        e, n, _ = utm.to_utm(lat_pair, lon_pair, epsg)
        projected = float(np.hypot(e[1] - e[0], n[1] - n[0]))
        _az, _baz, true_m = geod.inv(lon_pair[0], lat_pair[0],
                                     lon_pair[1], lat_pair[1])
        worst = max(worst, abs(projected - true_m) / true_m)
    assert worst < 0.01, f"stretch reached {worst * 100:.3f}%"


def test_the_stretch_figure_matches_a_measured_geodesic():
    """The formula in worst_stretch() against pyproj's geodesic.

    A number quoted to two decimals in a user-facing note has to be
    right, not indicative.
    """
    Geod = pytest.importorskip("pyproj").Geod
    geod = Geod(ellps="WGS84")

    epsg, lat0 = 32633, 50.0
    for lon in (18.0, 21.0, 24.0):
        predicted = utm.worst_stretch([lat0], [lon], epsg)
        e, n, _ = utm.to_utm([lat0, lat0 + 0.05], [lon, lon], epsg)
        projected = float(np.hypot(e[1] - e[0], n[1] - n[0]))
        *_rest, true_m = geod.inv(lon, lat0, lon, lat0 + 0.05)
        measured = abs(projected - true_m) / true_m
        assert abs(predicted - measured) < 5e-5, (
            f"at {lon}E predicted {predicted:.5f}, measured {measured:.5f}")


def test_the_stretch_grows_away_from_the_central_meridian():
    epsg = 32633
    near = utm.worst_stretch([50.0], [15.5], epsg)
    far = utm.worst_stretch([50.0], [24.0], epsg)
    assert far > near


def test_the_stretch_survives_data_it_cannot_use():
    assert utm.worst_stretch([np.nan], [np.nan]) is None
