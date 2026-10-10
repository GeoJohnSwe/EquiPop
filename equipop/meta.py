"""
meta.py - the per-run metadata log (backlog item 2, design as agreed).

One immutable JSON sidecar per run, same basename as the output
(out.csv + out.meta.json), containing SIX sections: run, environment,
inputs (with md5 hashes), settings (structured as function parameters),
data, events - plus, per decision, the full output column list with
one-line definitions.

WRITTEN PROGRESSIVELY WHEN THERE IS SOMEWHERE TO WRITE. The file
exists from the moment the destination is known, and every recording
call updates it, so a run that dies half way still leaves a record
saying what it was doing. BACKLOG 159, open since 1.29.6: this
paragraph used to promise that unconditionally and the class did not
deliver it. With the default constructor `_path` is None, so every
_flush() was a no-op and nothing reached disk until finalize() - and
BOTH GUI DOORS used the default constructor, so a QGIS or Pro run that
crashed mid-analysis left nothing at all. The claim was in the
docstring, the test suite, and the manual; it was never in the code.

Where there is genuinely no file - a QGIS temporary layer, which is
QGIS's own default destination, or a Stata run that writes variables
into memory - there is nowhere to put a sidecar, and the record is
PRINTED instead. That is a real limit and is now stated rather than
papered over.

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
import os
import platform
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


# --- WHERE A RECORD GOES, decided once (BACKLOG 159) ------------------
# A GIS door's "destination" is not a path. It may carry a layer -
# "out.gpkg|layername=k100" - or be one of the in-memory forms, which
# have no folder to write beside. Turning one into a sidecar path was
# done inside write_provenance, which meant the DOOR owned a rule the
# RECORD depends on; and now that the record must be opened before the
# run rather than after it, two places would have needed the same rule.
# One place, and both callers read it.

def sidecar_for(destination) -> str | None:
    """The .meta.json path for a door's output destination.

    None when there is nowhere to put one - an in-memory or temporary
    layer, or a folder that does not exist. The caller then prints the
    record instead, which is what a QGIS user's log is for.

    The layer name goes INTO the stem (out.gpkg|layername=k100 ->
    out.k100.meta.json), because every layer of one GeoPackage
    otherwise shares a single sidecar and each run overwrites the last
    one's provenance - BACKLOG 348, and the rule travels with this
    function rather than being reimplemented beside it.
    """
    path, _, rest = str(destination or "").partition("|")
    if (not path
            or path.startswith(("memory:", "ogr:"))
            or path.upper().startswith("TEMPORARY")):
        return None
    folder = os.path.dirname(path) or "."
    if not os.path.isdir(folder):
        return None
    layer = ""
    for part in rest.split("|"):
        if part.lower().startswith("layername="):
            layer = part.split("=", 1)[1]
    base, ext = os.path.splitext(path)
    if layer:
        safe = "".join(c if (c.isalnum() or c in "-_") else "_"
                       for c in layer)
        base = f"{base}.{safe}"
    return base + ".meta.json"


def _md5(path, chunk=1 << 20):
    h = hashlib.md5(usedforsecurity=False)
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


def _describe_columns(cols, under=None):
    """Definitions for `cols`, matched on the engine's own names.

    BACKLOG 348. `under` maps a column's name IN THE FILE to the
    result key the engine produced it under, for the case where a door
    had to rename it - QGIS renames a result that clashes with one of
    the input's own fields (BACKLOG 316). The definition belongs to
    the QUANTITY, not to the string: these patterns describe EquiPop's
    naming convention, so `N_20b` matches nothing and was documented
    as "(no definition registered)" the moment the record started
    naming fields as the file holds them. Looked up under the original
    and reported under the new one, the record both names what is
    there and says what it means.
    """
    under = under or {}
    out = {}
    for c in cols:
        key = under.get(c, c)
        for pat, doc in _COLUMN_DOCS:
            m = re.match(pat, key)
            if m:
                out[c] = doc.format(*m.groups())
                if key != c:
                    out[c] += f" [renamed from {key}]"
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

    def set_output(self, destination=None, layer=None,
                   renamed_fields=None, carried_fields=None):
        """WHICH artefact this record describes.

        BACKLOG 348, external review of 1.51 (finding F9). The record
        said what the run DID and never what it produced, which is
        half an identity. Two consequences, both reproduced in QGIS:
        a GeoPackage holding `out.gpkg|layername=k20` and
        `out.gpkg|layername=k800` got ONE sidecar, out.meta.json,
        because the layer name was split off and thrown away - the
        second run silently overwrote the first run's provenance, and
        nothing in the surviving file said which layer it was about.
        And the FIELD NAMES documented were the engine's result keys,
        while the layer on disk may hold renamed ones: with a source
        that already carried an N_20, the output held N_20 and N_20b
        and the record defined only `N_20` - the SOURCE's column -
        so a reader looking up the run's own result found the
        definition of somebody else's field.

        `renamed_fields` is {result key: name in the file} for the
        ones that moved; `carried_fields` is the input's own fields,
        passed through untouched and named here so the record accounts
        for every column a reader will see.
        """
        out = self.doc["run"].setdefault("output", {})
        if destination is not None:
            out["destination"] = str(destination)
        if layer is not None:
            out["layer"] = str(layer)
        if renamed_fields:
            out["renamed_fields"] = dict(renamed_fields)
        if carried_fields is not None:
            out["carried_fields"] = list(carried_fields)
        self._flush()
        return out

    # -------------------------------------------------------- finishing
    def finalize(self, df, output_path: str,
                 write_txt: bool = True, under=None) -> str:
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
        # BACKLOG 348. `under` lets a renamed column keep its meaning;
        # it defaults to the mapping this record already holds, so a
        # door that called set_output() needs no second argument.
        if under is None:
            renamed = ((self.doc["run"].get("output") or {})
                       .get("renamed_fields") or {})
            under = {new: was for was, new in renamed.items()}
        self.doc["columns"] = _describe_columns(cols, under)
        # BACKLOG 159. KEEP THE PATH THE RECORD WAS OPENED AT. A door
        # that knew its destination before the run has been writing
        # there all along, and recomputing here would leave that file
        # frozen at "running" while a second one claimed success -
        # which is half of what item 159 described. (The other half,
        # that a different path at finalize leaves the first marked
        # running forever, did NOT reproduce when checked: both files
        # said "completed", so the entry was wrong about the symptom
        # while right about the cause.)
        derived = out.parent / (out.stem + ".meta.json")
        if self._path is None:
            self._path = derived
        elif Path(self._path).resolve() != derived.resolve():
            # Two destinations for one run. Say so in the record rather
            # than silently leaving a stale file beside the output.
            self.doc["run"]["moved_from"] = str(self._path)
            self._path = derived
        self._flush()
        if write_txt:
            txt = out.parent / (out.stem + ".meta.txt")
            with open(txt, "w") as f:
                f.write(self.render_txt())
        print(f"[meta] wrote {self._path.name}"
              + (f" + {out.stem}.meta.txt" if write_txt else ""))
        return str(self._path)

    def _flush(self):
        """Write the record, replacing it rather than truncating it.

        BACKLOG 159. `write_text` opens the file for writing, which
        EMPTIES IT, and then fills it - so for the whole of that window
        the record on disk is neither the old one nor the new one. A
        progressive record is written many times per run, so it is
        exposed to that window many times, and the thing it exists to
        survive is a crash. Written beside and renamed, the file is
        always one complete version or the other. Exactly the fix
        BACKLOG 344 made to bigrun's manifest a release earlier, for
        the same reason, which is why it is the same shape here.

        IT NEVER RAISES. A provenance write that loses a finished
        analysis would be worse than having no provenance, which is the
        state this replaces - the QGIS door already says so in
        write_provenance. The failure is remembered on the doc so a
        caller that wants to report it can.
        """
        if not self._path:
            return
        tmp = self._path.with_name(self._path.name + f".tmp.{os.getpid()}")
        try:
            tmp.write_text(json.dumps(self.doc, indent=1, default=str))
            os.replace(tmp, self._path)
        except Exception as exc:                      # pragma: no cover
            self._write_error = f"{exc.__class__.__name__}: {exc}"
            try:
                tmp.unlink()
            except OSError:
                pass

    def render_txt(self):
        d = self.doc
        lines = [f"EquiPop Pangea run {d['run']['id']}",
                 f"finished: {d['run'].get('duration_s', '?')} s, "
                 f"status {d['run']['status']}", "", "SETTINGS:"]
        lines += [f"  {k} = {v}" for k, v in d["settings"].items()]
        lines += ["", "INPUTS:"]
        lines += [f"  {i['path']}  md5={i['md5']}  rows={i['rows']}"
                  for i in d["inputs"]] or ["  (none recorded)"]
        # BACKLOG 348. WHICH ARTEFACT THIS DESCRIBES - the .txt is what
        # a QGIS user actually reads, so a record that names its own
        # output only in the JSON names it only for programs.
        out = d["run"].get("output") or {}
        if out:
            lines += ["", "OUTPUT:"]
            if out.get("destination"):
                lines.append(f"  destination = {out['destination']}")
            if out.get("layer"):
                lines.append(f"  layer = {out['layer']}")
            for was, now in (out.get("renamed_fields") or {}).items():
                lines.append(f"  field renamed: {was} -> {now} "
                             "(the input already had that name)")
            if out.get("carried_fields"):
                lines.append("  input fields carried through: "
                             + ", ".join(out["carried_fields"]))
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
           source: str | None = None,
           destination: str | None = None) -> "RunLog":
    """Open a RunLog for one engine call.

    `path` is the sidecar file itself, when a caller has one.
    `destination` is a GIS door's OUTPUT - possibly with a layer, and
    possibly in-memory - from which the sidecar path is derived by
    sidecar_for(). BACKLOG 159: passing it is what makes the record
    progressive, because the record then exists from here rather than
    from finalize(), and a run that dies in between leaves it behind
    saying `"status": "running"`. Both GIS doors know their
    destination before the engine starts; neither was passing it.

    `source` is the data analysed, which the engine never sees - it
    receives arrays, not files.
    """
    if path is None and destination is not None:
        path = sidecar_for(destination)
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
