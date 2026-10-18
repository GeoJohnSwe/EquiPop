# -*- coding: utf-8 -*-
"""test_atomic.py - a finished file is put in place even while Windows
holds it for a moment, and a fetch that cannot record a file says so.

v1.59.2, external review of 1.59.1. On Windows a virus scanner or a
cloud-sync client opens a file just written, and while it does,
os.replace is refused ("Access is denied"). The review met it on the
fetch manifest. Here os.replace is made to refuse, which is how it
fails there; the waits are set to zero so nothing sleeps.

Each test's docstring names what it was BROKEN WITH, and each was.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import fakeweb                                       # noqa: E402
from equipop import atomic                           # noqa: E402
from equipop.doors import catalogue as cat          # noqa: E402
from equipop.doors import fetchrows as fr           # noqa: E402
from equipop.doors.fetching import (FetchError, MANIFEST,  # noqa: E402
                                    run_fetch)


def mute(*_a):
    return None


@pytest.fixture
def no_wait(monkeypatch):
    monkeypatch.setattr(atomic, "WAITS", (0,) * 6)


def lock(monkeypatch, ending, first=1, last=None):
    """os.replace refuses, as Windows does, for a destination ending in
    `ending` - from its `first`-th swap there to its `last` (None: for
    good). Returns the count of swaps asked for."""
    real = os.replace
    seen = {"n": 0}

    def refuse(src, dst):
        if str(dst).endswith(ending):
            seen["n"] += 1
            if seen["n"] >= first and (last is None or seen["n"] <= last):
                raise PermissionError(13, "Access is denied", str(dst))
        return real(src, dst)
    monkeypatch.setattr(os, "replace", refuse)
    return seen


def _pair(tmp_path):
    tmp, dest = tmp_path / "x.json.part", tmp_path / "x.json"
    tmp.write_text("new")
    dest.write_text("old")
    return str(tmp), str(dest)


# ------------------------------------------------------------- swap_in
def test_a_moments_lock_is_waited_out(tmp_path, monkeypatch):
    """Refused three times, then let through: the new file is in place,
    after the first three waits.

    BROKEN WITH: atomic._locked answering False (no retry)."""
    tmp, dest = _pair(tmp_path)
    lock(monkeypatch, "x.json", 1, 3)
    slept = []
    atomic.swap_in(tmp, dest, sleep=slept.append)
    assert open(dest).read() == "new" and not os.path.exists(tmp)
    assert slept == list(atomic.WAITS[:3])


def test_a_lock_that_does_not_lift_is_reported_in_words(tmp_path,
                                                        monkeypatch):
    """Every try refused: a PermissionError still (callers that catch
    one keep working), saying what usually holds a file and what to
    do. The old file is untouched; the new one is left for the
    caller's clean-up.

    BROKEN WITH: the last refusal re-raised bare instead of as
    LockedError."""
    tmp, dest = _pair(tmp_path)
    lock(monkeypatch, "x.json")
    slept = []
    with pytest.raises(atomic.LockedError) as e:
        atomic.swap_in(tmp, dest, sleep=slept.append)
    assert isinstance(e.value, PermissionError)
    msg = str(e.value)
    for words in ("x.json", "virus scanner", "OneDrive", "run again",
                  f"{len(atomic.WAITS) + 1} times"):
        assert words in msg, words
    assert open(dest).read() == "old" and os.path.exists(tmp)
    assert len(slept) == len(atomic.WAITS)


def test_a_failure_that_is_not_a_lock_is_not_waited_for(tmp_path):
    """A missing file is not a moment's lock: raised at once.

    BROKEN WITH: atomic._locked answering True for any OSError."""
    slept = []
    with pytest.raises(FileNotFoundError):
        atomic.swap_in(str(tmp_path / "absent"), str(tmp_path / "x"),
                       sleep=slept.append)
    assert slept == []


def test_windows_sharing_violation_counts_as_a_lock(tmp_path,
                                                    monkeypatch):
    """WinError 32, 'being used by another process', when it arrives
    as a plain OSError rather than PermissionError.

    BROKEN WITH: the winerror test removed from atomic._locked."""
    tmp, dest = _pair(tmp_path)
    real, n = os.replace, {"i": 0}

    def busy(src, dst):
        n["i"] += 1
        if n["i"] == 1:
            e = OSError(16, "The process cannot access the file because "
                            "it is being used by another process")
            e.winerror = 32
            raise e
        return real(src, dst)
    monkeypatch.setattr(os, "replace", busy)
    atomic.swap_in(tmp, dest, sleep=lambda s: None)
    assert open(dest).read() == "new"


# ------------------------------------------------- the fetch manifest
@pytest.fixture
def three(tmp_path):
    web = fakeweb.captured(bodies=True)
    net = cat.Net(opener=web, pause=0, waits=(0,))
    rows = cat.browse_worldpop("age_sex", "Burundi", "2020", net=net,
                               say=mute)[:3]
    return rows, net, str(tmp_path / "f")


def _recorded(folder):
    with open(os.path.join(folder, MANIFEST), encoding="utf-8") as f:
        return {x["name"] for x in json.load(f)["files"]}


def test_a_manifest_locked_mid_fetch_does_not_stop_it(three, monkeypatch,
                                                      no_wait):
    """The review's case: the manifest refused for a moment while the
    fetch is writing it. The fetch carries on and records all three.

    BROKEN WITH: run_fetch's commit using os.replace directly."""
    rows, net, folder = three
    lock(monkeypatch, MANIFEST, 2, 4)
    fr.fetch_rows(rows, folder, net=net, say=mute)
    assert _recorded(folder) == {r["file"] for r in rows}


def test_a_manifest_that_stays_locked_names_what_it_could_not_record(
        three, monkeypatch, no_wait):
    """Locked from the third file's record onward. 1.59.1 said the
    files 'listed above' had no provenance - the unrecorded one had
    never been listed - and then that what arrived 'IS recorded', so
    a retry would recognise it. The retry refused it.

    Now the unrecorded file is named, the stop line no longer claims
    it is recorded, the lock is what is raised, and doing what the
    message says lets the next run finish.

    BROKEN WITH: the 1.59.1 ending (the success line said whatever
    the manifest write did)."""
    rows, net, folder = three
    lock(monkeypatch, MANIFEST, 3)
    said = []
    with pytest.raises(atomic.LockedError):
        fr.fetch_rows(rows, folder, net=net, say=said.append)
    third = rows[2]["file"]
    assert _recorded(folder) == {rows[0]["file"], rows[1]["file"]}
    told = "\n".join(said)
    assert f"NOT RECORDED, though on disk: {third}" in told
    assert "IS recorded" not in told
    assert "Everything else that arrived is recorded" in told
    monkeypatch.undo()
    with pytest.raises(FetchError, match="not in equipop_fetch.json"):
        fr.fetch_rows(rows, folder, net=net, say=mute)
    os.remove(os.path.join(folder, third))          # as the message says
    fr.fetch_rows(rows, folder, net=net, say=mute)
    assert _recorded(folder) == {r["file"] for r in rows}


def test_a_lock_that_lifts_by_the_last_write_says_all_is_recorded(
        three, monkeypatch):
    """Refused for longer than swap_in waits, but lifted by the time
    the run records its stop: then everything IS recorded, and saying
    so is true. (No waits here, so 7 refusals outlast one swap.)

    BROKEN WITH: the stop line made to say NOT RECORDED always."""
    rows, net, folder = three
    monkeypatch.setattr(atomic, "WAITS", (0,) * 6)
    lock(monkeypatch, MANIFEST, 3, 9)
    said = []
    with pytest.raises(atomic.LockedError):
        fr.fetch_rows(rows, folder, net=net, say=said.append)
    assert _recorded(folder) == {r["file"] for r in rows}
    told = "\n".join(said)
    assert "IS recorded" in told and "NOT RECORDED" not in told
    fr.fetch_rows(rows, folder, net=net, say=mute)     # a retry: fine


class _Stop(BaseException):
    """What a door's Cancel looks like from inside the engine."""


def test_a_file_not_yet_checked_is_removed_when_the_run_stops(tmp_path):
    """A .pbf arrives; its .md5 is being asked for when the run stops.
    The file is on disk, unchecked and unrecorded - left there, the
    next run would refuse it as of unknown origin. It is removed, and
    the run says so.

    BROKEN WITH: the removal of `unverified` taken out of run_fetch."""
    def get_file(url, dest):
        import hashlib
        body = b"PBF" * 100
        with open(dest, "wb") as f:
            f.write(body)
        return len(body), hashlib.sha256(body).hexdigest()

    def get_text(url):
        raise _Stop()

    said = []
    plan = {"provider": "Geofabrik", "entries": [
        {"url": "https://download.geofabrik.de/x.osm.pbf",
         "name": "x.osm.pbf",
         "md5_url": "https://download.geofabrik.de/x.osm.pbf.md5"}]}
    with pytest.raises(_Stop):
        run_fetch(plan, str(tmp_path), get_file=get_file,
                  get_text=get_text, say=said.append)
    assert not (tmp_path / "x.osm.pbf").exists()
    assert any("x.osm.pbf was removed" in s for s in said)
    assert _recorded(str(tmp_path)) == set()
    run_fetch(plan, str(tmp_path), get_file=get_file,
              get_text=lambda u: None, say=mute)        # a retry: fine


# ------------------------------------------------- every swap uses it
SWAPS = {
    "equipop/doors/catalogue.py": 1, "equipop/doors/fetching.py": 2,
    "equipop/doors/fetchrows.py": 4, "equipop/bigrun.py": 2,
    "equipop/meta.py": 1}


def test_every_swap_goes_through_swap_in():
    """No os.replace left outside atomic.py in the package, so a new
    swap cannot quietly skip the wait.

    BROKEN WITH: catalogue.write_csv put back on os.replace."""
    for p in (ROOT / "equipop").rglob("*.py"):
        if p.name == "atomic.py":
            continue
        code = [ln for ln in p.read_text(encoding="utf-8").splitlines()
                if not ln.lstrip().startswith("#")]
        assert not any("os.replace(" in ln and '"""' not in ln
                       for ln in code), p
    for rel, n in SWAPS.items():
        src = (ROOT / rel).read_text(encoding="utf-8")
        assert src.count("swap_in(") == n, rel
