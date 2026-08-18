"""BACKLOG 177, Stata half - projection on the way in, and the warning
for the user who did not know they needed it.

The projection itself is tested in test_utm.py. What is tested here is
the seam: that the Stata door converts before counting, that it says
what it did, and that the user who does NOT ask for it is told rather
than left with a silently wrong answer.
"""

import numpy as np
import pytest

from equipop import stata_bridge


# Bristol County, Rhode Island - the demo dataset's own ground.
BRISTOL_LAT = np.array([41.72, 41.74, 41.68, 41.71])
BRISTOL_LON = np.array([-71.28, -71.26, -71.31, -71.29])


def test_projection_returns_metres_and_names_the_zone():
    east, north, epsg, sentence = stata_bridge.project_for_stata(
        BRISTOL_LON, BRISTOL_LAT)
    assert epsg == 32619
    assert "UTM zone 19N" in sentence and "32619" in sentence
    # Rhode Island in UTM 19N: eastings around 300 km, northings 4620 km
    assert 250_000 < east.mean() < 350_000
    assert 4_500_000 < north.mean() < 4_700_000


def test_an_explicit_epsg_is_obeyed():
    _e, _n, epsg, sentence = stata_bridge.project_for_stata(
        BRISTOL_LON, BRISTOL_LAT, epsg=32618)
    assert epsg == 32618
    assert "18N" in sentence


def test_projection_changes_which_neighbours_are_nearest():
    """The reason the feature exists, stated as an outcome rather than
    as a principle.

    Two candidate neighbours, one due east and one due north, placed so
    that in DEGREES the eastern one looks further away while on the
    ground it is closer. Counting in degrees picks the wrong one.
    """
    lat = np.array([41.70, 41.70, 41.76])
    lon = np.array([-71.30, -71.22, -71.30])

    d_east_deg = abs(lon[1] - lon[0])
    d_north_deg = abs(lat[2] - lat[0])
    assert d_east_deg > d_north_deg          # in degrees, east looks further

    east, north, _epsg, _s = stata_bridge.project_for_stata(lon, lat)
    d_east_m = np.hypot(east[1] - east[0], north[1] - north[0])
    d_north_m = np.hypot(east[2] - east[0], north[2] - north[0])
    assert d_east_m < d_north_m, (
        "on the ground the eastern neighbour is the closer one - which "
        "is the opposite of what the degrees said")


def test_degrees_are_warned_about_when_project_is_not_given():
    msg = stata_bridge.degrees_warning(BRISTOL_LON, BRISTOL_LAT)
    assert msg is not None
    assert "project" in msg
    assert "degree of longitude" in msg


def test_metric_coordinates_are_not_warned_about():
    """The false positive that would matter: nagging a professional who
    projected their data properly, on every single run."""
    east, north, _e, _s = stata_bridge.project_for_stata(
        BRISTOL_LON, BRISTOL_LAT)
    assert stata_bridge.degrees_warning(east, north) is None


def test_the_warning_survives_missing_coordinates():
    """John's field data had 9 rows without coordinates. A warning that
    crashed on them would be worse than no warning."""
    lon = np.array([-71.3, np.nan, -71.2])
    lat = np.array([41.7, 41.8, np.nan])
    assert stata_bridge.degrees_warning(lon, lat) is not None
    east, north, _e, _s = stata_bridge.project_for_stata(lon, lat)
    assert np.isfinite(east[0]) and np.isnan(east[1]) and np.isnan(east[2])


def test_projected_coordinates_still_line_up_row_for_row():
    """The contract with Stata: results are assigned back by position,
    so the projection must not drop, reorder or add a row."""
    lon = np.array([-71.3, np.nan, -71.2, -71.25])
    lat = np.array([41.7, 41.8, np.nan, 41.75])
    east, north, _e, _s = stata_bridge.project_for_stata(lon, lat)
    assert len(east) == len(lon) == len(north) == len(lat)


def test_a_projection_refusal_names_the_problem():
    from equipop.utm import ProjectionRefused
    with pytest.raises(ProjectionRefused):
        stata_bridge.project_for_stata(
            np.array([598000.0, 599000.0]),
            np.array([6598000.0, 6599000.0]))
