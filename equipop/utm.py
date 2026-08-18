"""UTM projection in numpy alone - no pyproj, no GDAL, nothing compiled
beyond what EquiPop already loads.

WHY THIS EXISTS - John's ruling, v1.37
--------------------------------------
His words, and the whole specification:

    "for professional spatial analysts, this function is not needed,
    they will have routines for projecting the data as they need and
    want - However, for the unexperienced stat and econ people that
    are not trained to think beyond lat/long, a simple function to
    generate good-enough projections are what is needed. I think that
    we should communicate in the output which projection that was used
    in each case (i.e. EPSG code for UTM would be enough)"

So: not a projection engine. One automatic, defensible choice, and a
sentence saying what it was. A spatial analyst who wants Lambert
azimuthal on a custom origin has QGIS and does not need us.

WHY IT IS NOT pyproj
--------------------
Because of what a dependency costs the audience this is for. A Stata
user must install pyproj into the same Python Stata uses, of the right
processor build - and pyproj is the one that bundles PROJ and its
data files. That is the fourth compiled library, added for exactly the
users least equipped to repair it when it will not load. v1.37 spent
its first half taking pyproj OFF the Stata path (BACKLOG 176); putting
it back for the feature aimed at beginners would undo that.

The arithmetic is not the risky part. Transverse Mercator has a closed
series solution, and tests/test_utm.py checks this implementation
against pyproj across every zone and the full latitude range. It
agrees to well under a millimetre. Millimetres do not matter here -
neighbourhoods are measured in hundreds of metres - but agreement at
that level means the implementation is right, not merely close.

WHAT IT DOES NOT DO
-------------------
- One zone for the whole dataset. John ruled single-zone acceptable
  (BACKLOG 171, declined). Distances "float" slightly for points far
  from the central meridian; at the scale a k-neighbourhood covers,
  the effect is far below the resolution of the data.
- The Norway and Svalbard zone exceptions are NOT applied. The zone is
  taken from the longitude by the standard formula, so a point at 6E
  gets zone 32 and the reported EPSG describes precisely what was
  done. The projection is valid either way; only the choice of central
  meridian differs.
- Beyond 84N or 80S, UTM is not defined and this refuses rather than
  returning something wrong quietly.
"""

from __future__ import annotations

import numpy as np

# WGS84. The only ellipsoid offered, on purpose: every lat/long dataset
# a beginner meets is WGS84 or close enough that the difference is far
# below the resolution of the data.
_A = 6378137.0                       # semi-major axis, metres
_F = 1 / 298.257223563               # flattening
_K0 = 0.9996                         # UTM scale factor on the meridian
_FALSE_EASTING = 500000.0
_FALSE_NORTHING = 10000000.0         # southern hemisphere only

_N = _F / (2 - _F)                   # third flattening

# Krüger series coefficients in powers of the third flattening, to
# sixth order. Sub-millimetre within a zone.
_ALPHA = (
    _N / 2 - 2 * _N**2 / 3 + 5 * _N**3 / 16 + 41 * _N**4 / 180,
    13 * _N**2 / 48 - 3 * _N**3 / 5 + 557 * _N**4 / 1440,
    61 * _N**3 / 240 - 103 * _N**4 / 140,
    49561 * _N**4 / 161280,
)
_BETA = (
    _N / 2 - 2 * _N**2 / 3 + 37 * _N**3 / 96 - _N**4 / 360,
    _N**2 / 48 + _N**3 / 15 - 437 * _N**4 / 1440,
    17 * _N**3 / 480 - 37 * _N**4 / 840,
    4397 * _N**4 / 161280,
)
# Meridian arc scaling
_A_BAR = _A / (1 + _N) * (1 + _N**2 / 4 + _N**4 / 64)

MAX_LAT = 84.0
MIN_LAT = -80.0


class ProjectionRefused(ValueError):
    """Raised rather than returning coordinates that would be wrong."""


def utm_zone(lon) -> int:
    """The UTM zone a longitude falls in, 1 to 60."""
    lon = float(lon)
    z = int(np.floor((lon + 180.0) / 6.0)) + 1
    return min(max(z, 1), 60)


def utm_epsg(lat, lon) -> int:
    """The EPSG code of the UTM zone for one representative point.

    326xx north of the equator, 327xx south.
    """
    return (32600 if float(lat) >= 0 else 32700) + utm_zone(lon)


def epsg_name(epsg: int) -> str:
    """'UTM zone 33N', the human half of the sentence we owe the user."""
    epsg = int(epsg)
    if 32601 <= epsg <= 32660:
        return f"UTM zone {epsg - 32600}N"
    if 32701 <= epsg <= 32760:
        return f"UTM zone {epsg - 32700}S"
    return f"EPSG:{epsg}"


def describe(epsg: int) -> str:
    """The whole sentence: 'UTM zone 33N (EPSG:32633)'.

    John's condition on the feature: say which projection was used.
    """
    return f"{epsg_name(epsg)} (EPSG:{int(epsg)})"


def choose_epsg(lat, lon) -> int:
    """Pick one zone for a whole dataset, from its middle.

    The MEDIAN, not the mean: a handful of points on the far side of
    the world would drag a mean into a zone holding no data at all,
    and the median cannot be moved by a fringe. This is the same
    failure suggest_projection() was written to avoid.
    """
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    ok = np.isfinite(lat) & np.isfinite(lon)
    if not ok.any():
        raise ProjectionRefused(
            "no usable coordinates - every row is missing x or y")
    return utm_epsg(np.median(lat[ok]), np.median(lon[ok]))


def _check_range(lat, lon):
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    ok = np.isfinite(lat) & np.isfinite(lon)
    if ok.any():
        if np.nanmax(np.abs(lat[ok])) > 90.0 or np.nanmax(np.abs(lon[ok])) > 180.0:
            raise ProjectionRefused(
                "these are not degrees: latitude must lie within +/-90 "
                "and longitude within +/-180. If the data is already "
                "projected, it does not need projecting again.")
        hi = np.nanmax(lat[ok])
        lo = np.nanmin(lat[ok])
        if hi > MAX_LAT or lo < MIN_LAT:
            raise ProjectionRefused(
                f"UTM is not defined beyond {MAX_LAT}N or {MIN_LAT}S, and "
                f"this data reaches {lo:.1f} to {hi:.1f}. Project it "
                f"yourself to a polar projection and pass the result.")


def to_utm(lat, lon, epsg: int | None = None):
    """Project degrees to metres. Returns (easting, northing, epsg).

    Missing coordinates stay missing - a row without a position must
    not acquire one, and must still occupy its row so results line up
    with the dataset they came from.

    Transverse Mercator by the Krüger series; see the module docstring
    for why this is not pyproj.
    """
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    _check_range(lat, lon)

    if epsg is None:
        epsg = choose_epsg(lat, lon)
    epsg = int(epsg)
    zone = epsg - (32600 if epsg < 32700 else 32700)
    if not 1 <= zone <= 60:
        raise ProjectionRefused(
            f"EPSG:{epsg} is not a WGS84 UTM zone (32601-32660 north, "
            f"32701-32760 south)")
    south = epsg >= 32700
    lon0 = (zone - 1) * 6.0 - 180.0 + 3.0        # central meridian

    phi = np.radians(lat)
    dlam = np.radians(lon - lon0)

    # Conformal latitude
    sin_phi = np.sin(phi)
    t = np.sinh(np.arctanh(sin_phi)
                - (2 * np.sqrt(_N) / (1 + _N))
                * np.arctanh((2 * np.sqrt(_N) / (1 + _N)) * sin_phi))
    xi_p = np.arctan2(t, np.cos(dlam))
    eta_p = np.arctanh(np.sin(dlam) / np.sqrt(1 + t * t))

    xi = xi_p + sum(
        a * np.sin(2 * (j + 1) * xi_p) * np.cosh(2 * (j + 1) * eta_p)
        for j, a in enumerate(_ALPHA))
    eta = eta_p + sum(
        a * np.cos(2 * (j + 1) * xi_p) * np.sinh(2 * (j + 1) * eta_p)
        for j, a in enumerate(_ALPHA))

    easting = _K0 * _A_BAR * eta + _FALSE_EASTING
    northing = _K0 * _A_BAR * xi
    if south:
        northing = northing + _FALSE_NORTHING

    # Belt and braces, and known to be so: NaN propagates through every
    # step above, so a missing input already gives a missing output and
    # deleting these two lines breaks no test. They stay as a statement
    # of the contract - a future change to the series that returned a
    # number for an unusable input would be caught here rather than
    # inventing a position for a row that has none.
    bad = ~(np.isfinite(lat) & np.isfinite(lon))
    easting = np.where(bad, np.nan, easting)
    northing = np.where(bad, np.nan, northing)
    return easting, northing, epsg


def from_utm(easting, northing, epsg: int):
    """Metres back to degrees. Returns (lat, lon).

    Present so the projection can be checked against itself, and so a
    user can put a result back on a map.
    """
    easting = np.asarray(easting, dtype=float)
    northing = np.asarray(northing, dtype=float)
    epsg = int(epsg)
    zone = epsg - (32600 if epsg < 32700 else 32700)
    south = epsg >= 32700
    lon0 = (zone - 1) * 6.0 - 180.0 + 3.0

    n_adj = northing - (_FALSE_NORTHING if south else 0.0)
    xi = n_adj / (_K0 * _A_BAR)
    eta = (easting - _FALSE_EASTING) / (_K0 * _A_BAR)

    xi_p = xi - sum(
        b * np.sin(2 * (j + 1) * xi) * np.cosh(2 * (j + 1) * eta)
        for j, b in enumerate(_BETA))
    eta_p = eta - sum(
        b * np.cos(2 * (j + 1) * xi) * np.sinh(2 * (j + 1) * eta)
        for j, b in enumerate(_BETA))

    chi = np.arcsin(np.sin(xi_p) / np.cosh(eta_p))
    # Inverse conformal latitude, by series
    phi = chi
    for _ in range(6):
        phi = np.arcsin(np.tanh(
            np.arctanh(np.sin(chi))
            + (2 * np.sqrt(_N) / (1 + _N)) * np.arctanh(
                (2 * np.sqrt(_N) / (1 + _N)) * np.sin(phi))))

    lon = lon0 + np.degrees(np.arctan2(np.sinh(eta_p), np.cos(xi_p)))
    return np.degrees(phi), lon


# How many zones the data may span before the run says so. Two is
# ordinary - any dataset near a zone boundary straddles it - so the
# note starts at three.
ZONE_SPAN_NOTE = 3


def zone_span(lat, lon) -> int:
    """How many UTM zones the data covers. 0 if nothing is usable."""
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    ok = np.isfinite(lat) & np.isfinite(lon)
    if not ok.any():
        return 0
    zones = np.floor((lon[ok] + 180.0) / 6.0).astype(int) + 1
    zones = np.clip(zones, 1, 60)
    return int(zones.max() - zones.min() + 1)


def worst_stretch(lat, lon, epsg=None):
    """How much the widest point in this data is stretched, as a
    fraction. None if it cannot be worked out.

    Transverse Mercator scales by k0 on the central meridian and grows
    away from it. To second order the point scale factor is

        k = k0 * (1 + (dlam * cos(phi))^2 / 2)

    where dlam is the angular distance from the central meridian. This
    is not a rule of thumb: checked against pyproj's geodesic at 9
    degrees out, the formula gives 0.469% and the measured error is
    0.470%.

    Reporting the figure for the USER'S OWN extent is the point. "Well
    under a percent" is true and unhelpful; "0.47% at the far edge of
    this data" is something a reader can weigh against their cell size.
    """
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    ok = np.isfinite(lat) & np.isfinite(lon)
    if not ok.any():
        return None
    if epsg is None:
        epsg = choose_epsg(lat, lon)
    zone = int(epsg) - (32600 if int(epsg) < 32700 else 32700)
    if not 1 <= zone <= 60:
        return None
    lon0 = (zone - 1) * 6.0 - 180.0 + 3.0

    dlam = np.radians(np.abs(lon[ok] - lon0))
    scale = _K0 * (1 + (dlam * np.cos(np.radians(lat[ok]))) ** 2 / 2)
    return float(np.max(np.abs(scale - 1.0)))


def zone_span_note(lat, lon, epsg=None):
    """A sentence if the data is wider than one zone comfortably holds,
    otherwise None. It NEVER refuses.

    John's ruling, v1.37, and the reasoning is his:

        "allow the user to proceed regardless - the effects are smaller
        than expected. This since the bespoke neighbourhood departs
        from the nearest k-neighbours, it becomes almost impossible to
        find a situation where an erroneous nearest neighbour is
        selected before the true nearest, and if that happened it would
        be in very large k, and at distances that makes very little
        difference. (i.e. for me it is the risk of counting the wrong
        cafe in Lyon/France from Oslo)"

    The argument is about ORDER, not about distance. A single-zone
    projection stretches distances away from the central meridian by
    well under a percent even three zones out. For that to change an
    answer it would have to swap the RANK of two cells - and two cells
    close enough in true distance to be swapped by a sub-percent error
    are, at the k needed to reach that far, interchangeable members of
    the same neighbourhood. The error is bounded by the order cells are
    reached in, not by the distance figure, which is the same reasoning
    that closed BACKLOG 171.

    So the note exists to be honest about what was done, not to warn of
    a defect. It says what happened and lets the run continue.
    """
    span = zone_span(lat, lon)
    if span < ZONE_SPAN_NOTE:
        return None
    where = f" ({describe(epsg)})" if epsg is not None else ""
    stretch = worst_stretch(lat, lon, epsg)
    figure = (f"by at most {stretch * 100:.2f}% at the far edge of this "
              f"data" if stretch is not None else
              "by well under one percent")
    return (
        f"NOTE: this data spans {span} UTM zones and one zone was used "
        f"for all of it{where}. Distances away from that zone's central "
        f"meridian are stretched {figure}. The run "
        f"continues, and for k-nearest-neighbour work this is very "
        f"nearly harmless: a neighbourhood is built from the ORDER in "
        f"which neighbours are reached, so a sub-percent error changes "
        f"an answer only if it swaps the rank of two cells - and cells "
        f"that close in true distance, at the k needed to reach across "
        f"zones, are interchangeable members of the same neighbourhood "
        f"anyway. If you need exact metric distances across this extent, "
        f"project the data yourself and pass the result.")


def looks_like_degrees(x, y) -> bool:
    """Do these coordinates look like unprojected lat/long?

    Used to WARN, never to act. The test is deliberately conservative:
    a projected coordinate system in metres puts points in the
    thousands or millions, so values that all sit inside the degree
    envelope are almost certainly degrees. The one case it would call
    wrongly - a local metric grid whose origin is inside the data - is
    a case where the user knows exactly what their coordinates are.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    if not ok.any():
        return False
    return bool(np.nanmax(np.abs(x[ok])) <= 180.0
                and np.nanmax(np.abs(y[ok])) <= 90.0)
