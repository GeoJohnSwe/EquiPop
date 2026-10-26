"""
toolset.py - which EquiPop tools a GIS toolbox SHOWS.

v1.62.0, BACKLOG 438. John, 25 October 2026: one plugin, identical in
every detail but one - whether tools 3 to 6 are shown - "and let us
make the default to hide - but please indicate in help etc., how it
can be lifted".

So: tools 1 and 2 (the published method) are the STANDARD set and are
always shown. Tools 3 to 6 - raster curation, spatial demography, the
downloads, the folder inventory - are the EXTENDED set, hidden until a
person runs tool 0 and chooses to show them. Hiding changes what the
toolbox LISTS and nothing else:

  QGIS  every tool stays registered and runnable - saved models,
        scripts and processing.run() find a hidden tool as before. It
        is only left out of the toolbox tree.
  Pro   a Python toolbox has no hidden state, so a hidden tool is not
        in the toolbox's list until shown; tool 0 says to refresh the
        toolbox afterwards.

ONE SETTING FOR BOTH GIS on a machine, in a small JSON file in the
user's own settings folder, so the choice survives upgrades and both
doors agree. EQUIPOP_SHOW_ALL_TOOLS=1 (or 0) in the environment
overrides it - for a classroom image, or for the tests.

If anything here fails - an unreadable file, an older package - the
doors SHOW everything: a tool shown that might have been hidden costs
nothing, and a tool hidden by an error could not be found at all.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

#: Always shown. Door-neutral names: the Pro classes, and each QGIS
#: algorithm's EQP_TOOL.
STANDARD = ("ShowTools", "CountsShares", "ValueStatistics")
#: Hidden until shown. SpatialDataFetch (5d) is QGIS's older fetch.
EXTENDED = ("ContinentalRasters", "SpatialDemography",
            "WorldPopCatalogue", "OsmCatalogue", "FetchSelected",
            "SpatialDataFetch", "FolderInventory")
ENV = "EQUIPOP_SHOW_ALL_TOOLS"
KEY = "show_all_tools"
#: John's ruling: hidden unless chosen.
DEFAULT = False

#: The two answers tool 0 offers, in this order in both doors.
CHOICES = ("Only tools 1 and 2 (the standard set)",
           "All tools, 1 to 6")

_cache: dict = {}


def settings_path() -> Path:
    """%APPDATA%\\EquiPop\\settings.json on Windows; elsewhere
    $XDG_CONFIG_HOME/equipop/settings.json (~/.config by default)."""
    if os.name == "nt" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "EquiPop" / "settings.json"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home()
                                                    / ".config")
    return Path(base) / "equipop" / "settings.json"


def _env_choice():
    v = os.environ.get(ENV, "").strip().lower()
    if v in ("1", "true", "yes", "on", "all"):
        return True
    if v in ("0", "false", "no", "off", "standard"):
        return False
    return None


def _read() -> dict:
    p = settings_path()
    try:
        stamp = p.stat().st_mtime_ns
    except OSError:
        return {}
    if _cache.get("stamp") == (str(p), stamp):
        return _cache["doc"]
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
        doc = doc if isinstance(doc, dict) else {}
    except (OSError, ValueError):
        doc = {}
    _cache.update(stamp=(str(p), stamp), doc=doc)
    return doc


def show_all() -> bool:
    """True when tools 3 to 6 should be shown."""
    env = _env_choice()
    if env is not None:
        return env
    v = _read().get(KEY, DEFAULT)
    return v if isinstance(v, bool) else DEFAULT


def set_show_all(value: bool) -> Path:
    """Save the choice; returns the file it was saved in."""
    p = settings_path()
    doc = dict(_read())
    doc[KEY] = bool(value)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    # the one swap every writer uses: tried again while a virus
    # scanner or a sync client holds the file (equipop.atomic)
    from ..atomic import swap_in
    try:
        swap_in(str(tmp), str(p))
    finally:
        if tmp.exists():
            tmp.unlink()
    _cache.clear()
    return p


def is_shown(tool: str) -> bool:
    """Whether a tool (by its door-neutral name) is listed."""
    return tool not in EXTENDED or show_all()


def state_sentence() -> str:
    """What the toolbox shows now, and why - for tool 0's messages."""
    env = _env_choice()
    shown = show_all()
    what = ("all tools, 1 to 6" if shown
            else "only tools 1 and 2 (3 to 6 are hidden)")
    if env is not None:
        return (f"The toolbox shows {what}: the environment variable "
                f"{ENV} says so, and it overrides the saved choice.")
    return f"The toolbox shows {what}. Saved in {settings_path()}."
