"""
meta.py - the per-run metadata log (backlog item 2, design as agreed).

One immutable JSON sidecar per run, same basename as the output
(out.csv + out.meta.json), containing SIX sections: run, environment,
inputs (with md5 hashes), settings (structured as function parameters),
data, events - plus, per decision, the full output column list with
one-line definitions. Written progressively: the file exists from
start_run onward, so a crashed run still leaves a record.

    from equipop.meta import RunLog
    rl = RunLog(settings={"engine": "stats", "k_values": [12, 25],
                          "unit_size": 100, "tie_mode": "ring"})
    rl.add_input("malta.gpkg", rows=8730, crs_in="EPSG:4326",
                 crs_used="EPSG:32633")
    rl.event("warning", "6 malformed rows dropped", n=6)
    rl.finalize(result_df, "malta_poi.csv")   # writes .meta.json + .meta.txt
"""

import hashlib
import json
import platform
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def _md5(path, chunk=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def _versions():
    out = {"python": sys.version.split()[0], "os": platform.platform()}
    for pkg in ("pandas", "numpy", "scipy", "pyproj", "geopandas",
                "rasterio", "equipop"):
        # BACKLOG 293. FOR OUR OWN PACKAGE, __version__ IS THE
        # AUTHORITY AND THE DIST METADATA IS NOT. They disagree
        # whenever the source has moved since the last `pip install`,
        # which is the normal state of an editable install and of any
        # machine where the toolbox was copied in by hand - and
        # measured here: dist-info said 1.49.1 while __version__ said
        # 1.49.3, so the record would have named a version that did
        # not produce it. __version__ is also the string the doctor
        # and the .ado compare against, so using anything else here
        # would make the provenance record disagree with the rest of
        # the package about which engine ran.
        if pkg == "equipop":
            try:
                out[pkg] = __import__(pkg).__version__
                continue
            except Exception:                        # pragma: no cover
                pass
        try:
            from importlib.metadata import version
            out[pkg] = version(pkg)
        except Exception:
            try:                       # local package without dist-info
                out[pkg] = __import__(pkg).__version__
            except Exception:
                pass
    return out


# one-line definitions, matched by regex against output column names
_COLUMN_DOCS = [
    (r"^Id$|^CellId$", "identifier carried from the in-data / cell label"),
    (r"^EastWest$", "cell/hexagon centre easting (m)"),
    (r"^NorthSouth$", "cell/hexagon centre northing (m)"),
    (r"^N_local$|^CountAllLocal$", "population at the origin cell itself"),
    (r"^CountGroupLocal$", "treatment count at the origin cell itself"),
    (r"^SumN$|^SumCountAll$", "population when the search ended"),
    (r"^SumCountGroup$", "treatment count when the search ended"),
    (r"^Ratio$", "final treatment/population ratio"),
    (r"^MaxDistance$", "straight-line m to the last counted cell"),
    (r"^N_(\d+)$", "factual population count when k={0} was reached"),
    (r"^T_(\d+)$", "treatment count at k={0}"),
    (r"^R_(\d+)$", "ratio T/N at k={0}"),
    (r"^Dist_(\d+)$", "straight-line m to the cell where k={0} was reached "
                      "(0 = satisfied within the origin cell)"),
    (r"^Rounds_(\d+)$", "friction-adjusted round at which k={0} was reached"),
    (r"^ND_(\d+)$", "decay-weighted population count at k={0}"),
    (r"^TD_(\d+)$", "decay-weighted treatment count at k={0}"),
    (r"^RD_(\d+)$", "decay-weighted ratio at k={0}"),
    (r"^Nv_(.+)_(\d+)$", "valid (non-missing) values of {0} behind its "
                         "statistics at k={1}"),
    (r"^Mean_(.+)_(\d+)$", "mean of {0} among the k={1} nearest"),
    (r"^Med_(.+)_(\d+)$", "median of {0} among the k={1} nearest"),
    (r"^SD_(.+)_(\d+)$", "standard deviation (ddof=1) of {0} at k={1}"),
    (r"^SE_(.+)_(\d+)$", "standard error of {0} at k={1}"),
    (r"^Ent_(.+)_(\d+)$", "Shannon entropy (nats) of {0} at k={1}"),
    (r"^Gini_(.+)_(\d+)$", "Gini coefficient of {0} at k={1}"),
]


def _describe_columns(cols):
    out = {}
    for c in cols:
        for pat, doc in _COLUMN_DOCS:
            m = re.match(pat, c)
            if m:
                out[c] = doc.format(*m.groups())
                break
        else:
            out[c] = "(no definition registered)"
    return out


class RunLog:
    """Progressive per-run metadata writer. See module docstring."""

    def __init__(self, settings: dict, path: str | None = None):
        self._t0 = time.time()
        self.doc = {
            "run": {
                "id": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-")
                      + uuid.uuid4().hex[:4],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "running",
            },
            "environment": _versions(),
            "inputs": [],
            "settings": settings,
            "data": {},
            "events": [],
            "columns": {},
        }
        self._path = Path(path) if path else None
        self._flush()

    # -------------------------------------------------------- recording
    def add_input(self, path: str, rows: int | None = None,
                  dropped_rows: int = 0, crs_in=None, crs_used=None):
        p = Path(path)
        self.doc["inputs"].append({
            "path": str(p), "md5": _md5(p) if p.exists() else None,
            "bytes": p.stat().st_size if p.exists() else None,
            "rows": rows, "dropped_rows": dropped_rows,
            "crs_in": crs_in, "crs_used": crs_used})
        self._flush()

    def event(self, level: str, msg: str, n: int = 1, detail=None):
        self.doc["events"].append(
            {"level": level, "msg": msg, "n": n, "detail": detail})
        self._flush()

    def set_data(self, **kw):
        self.doc["data"].update(kw)
        self._flush()

    # -------------------------------------------------------- finishing
    def finalize(self, df, output_path: str,
                 write_txt: bool = True) -> str:
        """`df` is a DataFrame or a plain {column: array} mapping.

        BACKLOG 293: the mapping form is what the GIS doors actually
        hold - `dispatch` returns a dict of columns, and requiring a
        DataFrame here would have meant every door building one just
        to be allowed to record its own run. A record nobody can
        reach is how this class came to sit unused for forty
        releases.
        """
        out = Path(output_path)
        if hasattr(df, "columns"):
            cols, rows = list(df.columns), len(df)
        else:
            cols = list(df)
            first = next(iter(df.values()), ())
            rows = len(first)
        self.doc["run"]["duration_s"] = round(time.time() - self._t0, 2)
        self.doc["run"]["status"] = "completed"
        self.doc["data"].setdefault("output_rows", rows)
        self.doc["columns"] = _describe_columns(cols)
        self._path = out.with_suffix(out.suffix + ".meta.json") \
            if out.suffix != ".json" else out
        self._path = out.parent / (out.stem + ".meta.json")
        self._flush()
        if write_txt:
            txt = out.parent / (out.stem + ".meta.txt")
            with open(txt, "w") as f:
                f.write(self.render_txt())
        print(f"[meta] wrote {self._path.name}"
              + (f" + {out.stem}.meta.txt" if write_txt else ""))
        return str(self._path)

    def _flush(self):
        if self._path:
            self._path.write_text(json.dumps(self.doc, indent=1,
                                             default=str))

    def render_txt(self):
        d = self.doc
        lines = [f"EquiPop Pangea run {d['run']['id']}",
                 f"finished: {d['run'].get('duration_s', '?')} s, "
                 f"status {d['run']['status']}", "", "SETTINGS:"]
        lines += [f"  {k} = {v}" for k, v in d["settings"].items()]
        lines += ["", "INPUTS:"]
        lines += [f"  {i['path']}  md5={i['md5']}  rows={i['rows']}"
                  for i in d["inputs"]]
        lines += ["", "DATA:"]
        lines += [f"  {k} = {v}" for k, v in d["data"].items()]
        lines += ["", "EVENTS:"]
        lines += [f"  [{e['level']}] x{e['n']}: {e['msg']}"
                  for e in d["events"]] or ["  (none)"]
        return "\n".join(lines) + "\n"


def load_meta(path: str) -> dict:
    """Read a .meta.json back (first step of the planned rerun())."""
    return json.loads(Path(path).read_text())


# --------------------------------------------------------------------
# BACKLOG 293. THE RECORD IS TAKEN FROM WHAT THE ENGINE RECEIVED, not
# from what a door remembers to list.
#
# This is the whole point of the item, and the reason RunLog sat
# unused for forty releases while ArcGIS Pro grew a second, parallel
# provenance system of its own - a hand-written list of rows in
# _manifest_rows(). Two implementations of one job, which is BACKLOG
# 103's shape, and the hand-written one drifted exactly as a
# hand-written list does:
#
#   `overshoot` has moved every k-based number since 1.30 and was
#   recorded nowhere until 1.47, because nobody added it to the list.
#   BACKLOG 148 is the same story: the manifest recorded k, cell size,
#   decay and barriers and NONE of the settings that DEFINE the
#   numbers, so two runs could carry identical manifests and different
#   answers. Claude tried to use two of John's to settle which of his
#   runs had differed, and could not.
#
# A record built from the engine's own keyword arguments cannot drift
# that way: a new engine parameter appears in the record the day it
# appears in the engine, with no door touched. That is the property
# worth having, and it is why this lives here and not in a door.
# --------------------------------------------------------------------

#: Keywords whose VALUE is data rather than a setting. Dumping these
#: would put a population column into a JSON sidecar - megabytes of
#: numbers that are already in the input file, and a privacy question
#: nobody asked for. They are SUMMARISED instead.
_DATA_KEYS = ("weight", "demand_arr", "treat", "values")


def _summarise(value):
    """An array or a dict of arrays, described rather than copied."""
    if isinstance(value, dict):
        return {k: _summarise(v) for k, v in value.items()}
    try:
        import numpy as _np
        a = _np.asarray(value)
        if a.ndim == 0:
            return a.item()
        finite = int(_np.isfinite(a).sum()) if a.dtype.kind in "fc" \
            else int(a.size)
        return {"n": int(a.size), "dtype": str(a.dtype),
                "present": finite,
                "min": (float(_np.nanmin(a)) if a.size and
                        a.dtype.kind in "fiu" else None),
                "max": (float(_np.nanmax(a)) if a.size and
                        a.dtype.kind in "fiu" else None)}
    except Exception:                                # pragma: no cover
        return f"<{type(value).__name__}>"


def settings_from_engine(kw: dict) -> dict:
    """The engine's keyword arguments, as a record of the run.

    Everything is kept except the DATA - a population column is not a
    setting, and a sidecar is not the place to copy one. Those are
    summarised: how many values, which dtype, how many present, and
    the range, which is enough to tell two runs apart without
    reproducing the input.

    `None` is kept rather than dropped, deliberately. "overshoot_mode
    was not passed" and "overshoot_mode was 'whole'" are different
    runs, and a record that omits the first cannot say which happened
    - which is how a door that named no mode came to be impossible to
    measure against an answer key (BACKLOG 99).
    """
    out = {}
    for name, value in sorted(kw.items()):
        if name in _DATA_KEYS and value is not None:
            out[name] = _summarise(value)
        elif isinstance(value, (str, int, float, bool, type(None))):
            out[name] = value
        elif isinstance(value, (list, tuple)):
            out[name] = (list(value) if len(value) <= 64
                         else _summarise(value))
        elif isinstance(value, dict):
            out[name] = {k: (v if isinstance(
                v, (str, int, float, bool, type(None), list))
                else _summarise(v)) for k, v in value.items()}
        else:
            out[name] = _summarise(value)
    return out


def record(engine: str, n_rows: int, kw: dict, path: str | None = None,
           source: str | None = None) -> "RunLog":
    """Open a RunLog for one engine call. The door supplies the output
    path when it has one; `source` is the data analysed, which the
    engine never sees - it receives arrays, not files."""
    rl = RunLog(settings=settings_from_engine(kw), path=path)
    rl.doc["run"]["engine"] = engine
    rl.set_data(input_rows=int(n_rows))
    if source:
        rl.doc["run"]["source"] = str(source)
    return rl


def render_settings(doc: dict, width: int = 68) -> list:
    """The settings that were actually in force, compactly, for a log.

    BACKLOG 293, John's ruling on Stata provenance: a PRINTED NOTE
    rather than a sidecar, because a Stata run writes variables into
    memory and may produce no file at all - and because `log using` is
    where a Stata user's reproducibility already lives.

    WHICH SETTINGS: every one that is not None, plus the data
    summaries, with nothing hand-picked. A list of "the ones that
    matter" is what BACKLOG 148 already proved cannot be maintained -
    the manifest recorded k and cell size and none of the settings
    that define the numbers, so two runs could carry identical records
    and different answers. A None is omitted here, and only here,
    because the JSON keeps it: on screen "the thing you did not set"
    is noise, in a record it is evidence.
    """
    out = [f"equipop run {doc['run'].get('id', '?')}"
           f"  engine {doc['run'].get('engine', '?')}"]
    for k, v in sorted(doc.get("settings", {}).items()):
        if v is None or v == {} or v == []:
            continue
        if isinstance(v, dict):
            inner = ", ".join(
                f"{k2}={v2.get('n', v2) if isinstance(v2, dict) else v2}"
                for k2, v2 in sorted(v.items()))
            if "n" in v:                     # a summarised array
                inner = (f"{v['n']} values, {v.get('present')} present"
                         + (f", {v['min']:g}..{v['max']:g}"
                            if v.get("min") is not None else ""))
            out.append(f"  {k} = {inner}"[:width])
        else:
            out.append(f"  {k} = {v}"[:width])
    for k, v in sorted(doc.get("data", {}).items()):
        out.append(f"  {k} = {v}")
    env = doc.get("environment", {})
    out.append("  engine version = " + str(env.get("equipop", "?"))
               + ", python " + str(env.get("python", "?")))
    return out


def flat_rows(doc: dict) -> list:
    """The record as (item, value) pairs - the shape ArcGIS Pro's
    _EquiPop_run.csv has always used, so one record can serve both a
    JSON sidecar and that CSV instead of the two being assembled
    separately. Nested settings are flattened with a dotted key."""
    rows = []
    for k, v in sorted(doc.get("run", {}).items()):
        rows.append((f"run_{k}", v))
    for k, v in sorted(doc.get("settings", {}).items()):
        if isinstance(v, dict):
            for k2, v2 in sorted(v.items()):
                rows.append((f"{k}.{k2}", v2))
        else:
            rows.append((k, v))
    for k, v in sorted(doc.get("data", {}).items()):
        rows.append((f"data_{k}", v))
    for k, v in sorted(doc.get("environment", {}).items()):
        rows.append((f"env_{k}", v))
    return rows
