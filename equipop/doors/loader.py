# -*- coding: utf-8 -*-
"""
loader.py - what every door must hand the engines, and the rules
that decide it.

A door (ArcGIS, QGIS, R, SPSS) reads points its own way: arcpy has
FeatureClassToNumPyArray, QGIS has QgsVectorLayer, R hands over a
data frame. That part cannot be shared and should not be. What CAN
be shared is everything around it:

  * the SHAPE of the result            -> PointInput
  * which columns hold the coordinates -> resolve_xy_fields
  * whether the named fields exist     -> check_fields_exist
  * what to suggest when the numbers   -> metric_crs_hint
    turn out to be degrees

All four were written once for ArcGIS in 1.16 and would have been
written again for QGIS. They live here instead.

Errors are raised as DoorError, which carries a finished sentence
for the user. Each door catches it and re-raises it in its own
currency - arcpy.ExecuteError in Pro, QgsProcessingException in
QGIS - without touching the text.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, Optional


class DoorError(Exception):
    """A refusal meant to be READ by the person at the dialog.

    The message is the whole point: it says what is wrong and what to
    do about it. Doors translate the exception type, never the text.
    """


@dataclass
class PointInput:
    """The one thing every door hands the engines.

    kind      "point" (real geometry) or "table" (coordinate columns)
    data      column name -> array, always including "x" and "y"
    id_field  the row identifier the door can write results back to,
              or None for a plain table
    crs_text  the working coordinate system in words, for the
              messages and the run manifest - every distance in the
              run is metres IN THIS system
    note      how the coordinates were found, for the message pane

    Unpacks as (kind, data, id_field) so that doors written before
    this class existed keep working unchanged.
    """

    kind: str
    data: Dict[str, Any]
    id_field: Optional[str] = None
    crs_text: str = "unknown"
    note: str = ""
    extras: Dict[str, Any] = field(default_factory=dict)

    def __iter__(self) -> Iterator[Any]:
        return iter((self.kind, self.data, self.id_field))

    def __len__(self) -> int:
        return 3

    @property
    def n(self) -> int:
        x = self.data.get("x")
        return 0 if x is None else len(x)


def check_fields_exist(available, wanted, context: str) -> None:
    """Every field box must hold a REAL field of this layer.

    Field finding: a k value typed into a field box ('55') produced
    arcpy's bare "Cannot find field", which says nothing about what
    to do. So does a field name left over from a previously chosen
    layer. Both are caught here with advice instead.

    `available` is the list of field names the door read from the
    layer; pass None when the door could not read them, and the
    check is skipped rather than guessed at.
    """
    if available is None:
        return
    have = set(str(a) for a in available)
    bad = [f for f in wanted if f and str(f) not in have]
    if bad:
        raise DoorError(
            f"{context}: {', '.join(repr(b) for b in bad)} "
            f"{'is not a field' if len(bad) == 1 else 'are not fields'}"
            " of this layer - pick from the dropdown. (Numbers like k "
            "or radii belong in their own boxes, not in a field box.)")


def metric_crs_hint(lon, lat) -> str:
    """Name a fitting metric coordinate system from the NUMBERS.

    The table path has no coordinate system object to ask - a table
    of numbers carries none. Field-test gap: degree tables were
    refused without any suggestion of what to project to.
    """
    try:
        lon, lat = float(lon), float(lat)
    except (TypeError, ValueError):
        return "a metric CRS"
    if 10.0 <= lon <= 25.0 and 55.0 <= lat <= 70.0:
        return "SWEREF 99 TM (EPSG:3006)"
    z = min(max(int((lon + 180.0) // 6) + 1, 1), 60)
    return (f"WGS 84 / UTM zone {z}{'N' if lat >= 0 else 'S'} "
            f"(EPSG:{(32600 if lat >= 0 else 32700) + z})")


def resolve_xy_fields(names, xf, yf, context: str,
                      sample_lonlat: Optional[Callable] = None):
    """User choice first; package guess second; loud advice third.
    Never tells the user to rename columns.

    `names` is the layer's field names. `sample_lonlat(xname, yname)`
    is supplied by the door and returns a representative coordinate
    pair, used only to name a fitting projection when the guess turns
    out to be degrees; doors that cannot sample may omit it.

    Returns (x_field, y_field, how) where how is "chosen" or
    "guessed".
    """
    from equipop.io import guess_xy_fields

    if xf and yf:
        return xf, yf, "chosen"
    gx, gy, deg = guess_xy_fields(names, context)
    if deg:
        lon, lat = (sample_lonlat(gx, gy) if sample_lonlat
                    else (None, None))
        raise DoorError(
            f"{context}: '{gx}'/'{gy}' look like DEGREES (lon/lat) - "
            f"EquiPop needs metres. Project the data first - for "
            f"these coordinates {metric_crs_hint(lon, lat)} fits "
            "(add the table as XY layer, then Project). A table "
            "cannot be auto-projected: its numbers carry no CRS.")
    if gx and gy:
        return gx, gy, "guessed"
    raise DoorError(
        f"{context}: could not guess the coordinate columns among "
        f"{list(names)} - pick the X field (easting) and "
        "Y field (northing) in the dialog. No renaming needed.")
