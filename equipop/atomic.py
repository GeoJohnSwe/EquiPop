"""
atomic.py - put a finished file in place, even on Windows.

Every file EquiPop writes to keep - a fetch manifest, a recipe, a
catalogue, a download, a GeoPackage, a tile of a long run - is written
beside its destination and then swapped in with os.replace, so a
reader sees the old version or the new one and never half of one.

ON WINDOWS THE SWAP CAN BE REFUSED FOR A MOMENT. A virus scanner, a
cloud-sync client (OneDrive, Dropbox) or the search indexer opens a
file that has just been written in order to look at it, and while it
holds the file Windows will not move or replace it: PermissionError,
"Access is denied" (WinError 5) or "being used by another process"
(WinError 32). The external review of 1.59.1 met it on the fetch
manifest, intermittently, on an ordinary Windows machine. It lasts from
milliseconds to a second or two, so the swap is tried again a few times
with short waits - and only then reported, in words that say what to
do. Nothing else is retried: a missing folder or a full disk is not a
moment's lock, and waiting cannot change it.

v1.59.2. One function, used at every swap, so the rule cannot drift
between the places that write.
"""

from __future__ import annotations

import os
import time

#: Seconds to wait before each new try - about four seconds in all,
#: longer than a scanner normally holds a small file.
WAITS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.0)


class LockedError(PermissionError):
    """The file was held open through every try."""


def _locked(exc):
    """Is this Windows refusing because something has the file open?
    (PermissionError covers WinError 5, 32 and 33 on Windows; the
    winerror test is for the rare build that raises plain OSError.)"""
    return (isinstance(exc, PermissionError)
            or getattr(exc, "winerror", None) in (5, 32, 33))


def swap_in(tmp, dest, waits=None, sleep=time.sleep):
    """os.replace(tmp, dest), tried again while the file is locked.

    `tmp` is left where it is if every try fails, so the caller's own
    clean-up (which every caller has) decides what happens to it.
    """
    waits = WAITS if waits is None else tuple(waits)
    for i in range(len(waits) + 1):
        try:
            os.replace(tmp, dest)
            return dest
        except OSError as exc:
            if not _locked(exc):
                raise
            if i == len(waits):
                where = os.path.dirname(os.path.abspath(dest))
                raise LockedError(
                    f"could not put {os.path.basename(dest)} in place in "
                    f"{where}: Windows refused {len(waits) + 1} times over "
                    f"{sum(waits):g} s ({exc.strerror or exc}). Something "
                    "is holding the file open - most often a virus "
                    "scanner, a cloud-sync client such as OneDrive, or "
                    "the file open in another program - or you may not "
                    "be allowed to write there. Close that program, or "
                    "use a folder that is not synced, and run again."
                ) from exc
            sleep(waits[i])
    return dest                                        # pragma: no cover


__all__ = ["swap_in", "LockedError", "WAITS"]
