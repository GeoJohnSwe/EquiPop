# -*- coding: utf-8 -*-
"""
equipop.doors - the shared parts of every door.

A "door" is a way into EquiPop that is not Python: the ArcGIS Pro
toolbox, the QGIS Processing plugin, the Stata bridge, R, SPSS.
None of them compute anything - the engines in the package do that,
where the test suite guards them. A door only moves data in and
results out, and explains itself while doing so.

Doing that well takes four things, and until 1.18.0 each door was
building its own:

    help    the explanation beside every box
    report  getting the package's printed voice into the door's pane
    fields  the result column names, and refusing a target too
            narrow to hold them
    loader  what a door must hand the engines, and the rules for
            finding the coordinates

They are shared from here.

THE VERSION CATCH
-----------------
The toolbox file and the installed package are now two halves of one
thing, and they can be upgraded separately - ArcGIS Pro in
particular caches toolboxes hard enough that an old one can outlive
the package it was written for. So a door states which contract it
was built against, and require() refuses loudly, with the fix, if
the halves no longer match.

Bump CONTRACT only when a door file must be replaced alongside the
package - that is, when something here changes shape rather than
merely gaining an addition.
"""

CONTRACT = 1

from .loader import DoorError  # noqa: E402  (needed by require below)


def require(contract, door: str = "this door",
            files: str = "the door's files") -> None:
    """Refuse when the door and the installed package are from
    releases that no longer fit together.

    Called once by each door as it starts work. The message names
    both versions and both halves of the fix, because being told
    only that something mismatches leaves a person nowhere.
    """
    from equipop import __version__
    if int(contract) == CONTRACT:
        return
    older = int(contract) < CONTRACT
    raise DoorError(
        f"{door} was built for EquiPop door contract "
        f"{int(contract)}, but the installed equipop package "
        f"{__version__} provides contract {CONTRACT}. "
        + ("The package is newer than the door: replace "
           f"{files} with the copies from this release. "
           if older else
           "The package is older than the door: run "
           "'pip install --upgrade equipop' in this environment. ")
        + "In ArcGIS Pro, remove and re-add the toolbox afterwards - "
        "Pro caches toolboxes and will otherwise keep the old one.")


__all__ = ["CONTRACT", "DoorError", "require"]
