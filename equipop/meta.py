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
    def finalize(self, df: pd.DataFrame, output_path: str,
                 write_txt: bool = True) -> str:
        out = Path(output_path)
        self.doc["run"]["duration_s"] = round(time.time() - self._t0, 2)
        self.doc["run"]["status"] = "completed"
        self.doc["data"].setdefault("output_rows", len(df))
        self.doc["columns"] = _describe_columns(df.columns)
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
