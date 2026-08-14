# -*- coding: utf-8 -*-
"""test_projection_order.py - BACKLOG 169.

suggest_projection() says (lat, lon). Every other module in EquiPop
says (x, y), which is (lon, lat) - the other way round. Called
positionally in the codebase's own order on John's Bristol County
data it returned EPSG:32737, UTM zone 37 SOUTH, and reported
"single-zone projection is safe (distortion < 0.1%)" while doing it.

Nothing downstream could have caught it. The output is metres, the
metres are plausible, every distance is wrong by a factor nobody can
see. And the shipped book taught the mistake:
docs/book/ch03_data_in.md printed suggest_projection(df, "lon",
"lat"), which is swapped.

This matters more now than it did: projection is about to become a
MUST-HAVE on the Stata door, where John's stated reason is that most
Stata users are not GIS people - "forcing them to project may be a
big usage blocker". The users least able to spot a wrong CRS are
exactly the ones being handed this.

Range checks cannot rescue the Rhode Island case: -71.3 is a
perfectly legal latitude. So the argument ORDER is removed as a thing
a caller can get wrong.
"""
import numpy as np
import pandas as pd
import pytest

from equipop.projection import (assign_zones, suggest_projection,
                                suggest_projection_xy)

# Bristol County, Rhode Island - the real case, small enough to inline
LAT = np.linspace(41.64, 41.773, 60)
LON = np.linspace(-71.353, -71.224, 60)
RI_UTM19N = 32619


def _xy():
    return pd.DataFrame({"x": LON, "y": LAT})


def _latlon():
    return pd.DataFrame({"lat": LAT, "lon": LON})


def test_the_named_call_is_right():
    got = suggest_projection(_latlon(), lat_col="lat", lon_col="lon")
    assert got.epsg == RI_UTM19N


def test_the_xy_helper_takes_equipops_usual_order():
    """x is EASTING is longitude; y is NORTHING is latitude. This is
    the call every other part of the codebase would naturally make."""
    assert suggest_projection_xy(_xy(), "x", "y").epsg == RI_UTM19N


def test_a_positional_call_can_no_longer_be_made_at_all():
    """The whole fix in one assertion. Before, this returned
    EPSG:32737 - zone 37 SOUTH, for Rhode Island - confidently."""
    with pytest.raises(TypeError):
        suggest_projection(_xy(), "x", "y")
    with pytest.raises(TypeError):
        assign_zones(_latlon(), 20000, "lat", "lon")


def test_the_book_no_longer_teaches_the_swap():
    """docs/book/ch03_data_in.md shipped `suggest_projection(df,
    "lon", "lat")` - swapped, and positional. A reader following it
    got the wrong CRS."""
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    book = open(os.path.join(root, "docs", "book",
                             "ch03_data_in.md"), encoding="utf-8").read()
    assert 'suggest_projection(df, "lon", "lat")' not in book
    assert "lat_col=" in book and "lon_col=" in book


def test_projected_metres_are_refused_by_name():
    """The commonest version of this mistake: handing a metric grid
    to a function that wants degrees. It must not be answered
    politely - the answer would be a projection for somewhere in the
    Gulf of Guinea."""
    metres = pd.DataFrame({"lat": [6_580_000.0, 6_581_000.0],
                           "lon": [320_000.0, 321_000.0]})
    with pytest.raises(ValueError, match="not a latitude in degrees"):
        suggest_projection(metres, lat_col="lat", lon_col="lon")


def test_a_longitude_beyond_180_is_refused_by_name():
    bad = pd.DataFrame({"lat": [41.7, 41.8], "lon": [200.0, 201.0]})
    with pytest.raises(ValueError, match="not a longitude in degrees"):
        suggest_projection(bad, lat_col="lat", lon_col="lon")


def test_nothing_usable_is_refused_rather_than_guessed():
    empty = pd.DataFrame({"lat": [np.nan, np.nan],
                          "lon": [np.nan, np.nan]})
    with pytest.raises(ValueError, match="no usable coordinates"):
        suggest_projection(empty, lat_col="lat", lon_col="lon")


def test_the_swap_would_still_be_wrong_which_is_why_it_is_blocked():
    """Stated so the reasoning is not lost: the swapped call is not
    caught by range checks, because -71.3 IS a legal latitude. Asked
    the wrong question, the function still answers - just about
    somewhere else entirely. That is why the ORDER is the thing that
    had to go, not the validation."""
    swapped = suggest_projection(_latlon(), lat_col="lon",
                                 lon_col="lat")
    assert swapped.epsg != RI_UTM19N
    assert swapped.epsg == 32737          # zone 37 SOUTH, as found
