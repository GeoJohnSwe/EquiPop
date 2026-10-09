"""
bigrun.py - continental scale (#18a): tile-and-flush for the fast
counting engine.

WHO THIS IS FOR: national/continental runs (millions of coordinates,
Europe-wide 100 m grids) where MEMORY, not time, is the constraint.

THE ARCHITECTURE (and why the seams are exact):
- The cell table and the KD-tree stay GLOBAL - 16M coordinates
  (~10M unique cells) fit comfortably in RAM (a few GB); what does
  NOT fit is holding millions of RESULT rows at once, and what must
  never be built is anything sized like the DOMAIN (Europe at 100 m
  ~ 2.25 billion cells).
- So: origins are processed in SPATIAL TILES; each tile's results are
  written to its own parquet file (float32) and RELEASED from memory;
  a manifest.json records parameters, per-tile md5 and progress.
- Because the tree and the destination mass are global, every
  per-origin result is EXACTLY the untiled result - no halos, no
  seam approximations, nothing to hope about (regression-tested).
  (True domain tiling with density-estimated halos is the >100M-cell
  escalation and stays on the backlog until someone brings that data.)
- resume=True skips tiles already in the manifest: a crashed
  three-day run continues where it stopped.

Usage:
    from equipop.bigrun import run_knn_counts_tiled, load_tiled
    man = run_knn_counts_tiled(cd, k_values=[100, 1600],
                               out_dir="run_eu", tile_m=50_000)
    df  = load_tiled("run_eu")            # or read tiles one by one
"""

import hashlib
import json
import os
import time

import numpy as np
import pandas as pd

from .fastcounts import run_knn_counts


def _md5(path, blocksize=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            b = f.read(blocksize)
            if not b:
                return h.hexdigest()
            h.update(b)


# --- crash-safe writing, BACKLOG 344 ---------------------------------
# A three-day run has to survive being interrupted at any instant,
# which is the whole reason this module writes as it goes. Truncating a
# file open and then filling it is the one pattern that cannot: the
# window between the two is a window in which the file on disk is
# neither the old content nor the new. Write beside it, flush it to the
# platter, then rename - os.replace() is atomic within a filesystem, so
# a reader (or the next resume) sees one complete version or the other.

def _atomic_write_json(obj, path):
    tmp = f"{path}.tmp.{os.getpid()}"
    try:
        with open(tmp, "w") as fh:
            json.dump(obj, fh, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        # A failed write must not leave litter behind that the next
        # run has to reason about.
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _atomic_write_parquet(df, path):
    """Same contract for a tile. A HALF-WRITTEN TILE IS WORSE THAN A
    MISSING ONE: the resume check asks only whether the file exists,
    so a truncated parquet left by a kill would be skipped as finished
    and then fail - or silently short-change - every later read. With
    the rename, the file appears complete or not at all, and `_md5`
    then records what was actually stored.
    """
    tmp = f"{path}.tmp.{os.getpid()}"
    try:
        df.to_parquet(tmp, index=False)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _engine_version():
    from . import __version__
    return str(__version__)


def _norm_list(v):
    """Plain Python numbers in a plain list.

    Two reasons, and the first is not cosmetic: json.dump REFUSES a
    numpy scalar, so a k list that arrived as np.int64 - which is what
    a numpy-built door hands over - would raise TypeError while
    writing the manifest, after the tile was already computed. The
    second is that the comparison has to be on what comes BACK from
    JSON, where a tuple returns as a list and would differ from
    itself forever.
    """
    if not v:
        return []
    out = []
    for x in v:
        f = float(x)
        out.append(int(f) if f.is_integer() else f)
    return out


def _norm_str(v):
    return None if v is None else str(v)


def run_knn_counts_tiled(cd, k_values=None, r_values=None, decay=None,
                         out_dir: str = "equipop_tiles",
                         tile_m: float = 50_000.0,
                         dtype: str = "float32",
                         resume: bool = True,
                         m_neighbors: int = 4096,
                         chunk: int = 4096,
                         decay_eps: float = 1e-6,
                         self_potential=None,
                         overshoot_mode: str | None = None,
                         self_rule: str | None = None,
                         seed: int | None = None) -> dict:
    """Run the fast engine tile by tile, flushing each tile to
    parquet. Returns the manifest dict (also written progressively to
    out_dir/manifest.json). Results are EXACTLY those of an untiled
    run - only the packaging differs.

    BACKLOG 345, external review of 1.51. The engine options below -
    self_potential, overshoot_mode, self_rule, seed, decay_eps - were
    accepted by run_knn_counts and NOT by this wrapper, so a tiled
    continental run silently took the defaults and there was no way to
    ask it for the origin rule a spatial regression needs. Same shape
    as BACKLOG 340 (r_values dropped on the tiled branch) and BACKLOG
    341 (the effort engines never told which overshoot mode to use):
    an option honoured on one path and unreachable on another.
    """
    try:
        import pyarrow  # noqa: F401 - parquet engine for the tiles
    except ImportError:
        raise ImportError("[bigrun] tile-and-flush writes parquet and "
                          "needs pyarrow: pip install pyarrow")
    os.makedirs(out_dir, exist_ok=True)
    mpath = os.path.join(out_dir, "manifest.json")

    tx = np.floor(cd.E / tile_m).astype(np.int64)
    ty = np.floor(cd.N / tile_m).astype(np.int64)
    tiles = pd.DataFrame({"tx": tx, "ty": ty, "i": np.arange(len(cd.E))})
    groups = list(tiles.groupby(["tx", "ty"]))
    print(f"[bigrun] {len(cd.E):,} cells -> {len(groups)} tiles of "
          f"{tile_m / 1000:g} km; out: {out_dir}/ ({dtype})")

    # WHAT MAKES TWO RUNS THE SAME RUN (BACKLOG 344, review finding
    # F3). The rule for this dict: a key belongs here if changing it
    # changes a NUMBER, and must stay out if it changes only the
    # speed - otherwise a user who raises `chunk` to go faster is told
    # their finished three-day run is a different analysis. So
    # m_neighbors and chunk are deliberately absent: both are
    # documented as speed-only and regression-tested as such.
    #
    # Everything else that reaches the engine is here, normalised so
    # the comparison is on values and not on object identity or dict
    # order, and JSON-round-trippable because that is how it comes
    # back from the manifest: int/float/str/None/list only, no tuples
    # (a tuple returns as a list and would differ from itself).
    params = {
        "schema": 2,                 # bump when a column's MEANING moves
        "equipop": _engine_version(),
        "k_values": _norm_list(k_values),
        "r_values": _norm_list(r_values),
        "decay": None if decay is None else decay.fingerprint(),
        "decay_eps": float(decay_eps),
        "self_potential": (None if self_potential is None
                           else float(self_potential)),
        "overshoot_mode": _norm_str(overshoot_mode),
        "self_rule": _norm_str(self_rule),
        "seed": None if seed is None else int(seed),
        "tile_m": float(tile_m),
        "dtype": str(dtype),
        "unit_size": float(cd.unit_size),
        "n_cells": int(len(cd.E)),
        # THE DATA ITSELF, not a count of it. See
        # CellData.fingerprint(): identical geometry with a different
        # population used to resume happily and return the earlier
        # run's answers.
        "cells_md5": cd.fingerprint(),
    }

    if resume and os.path.exists(mpath):
        with open(mpath) as fh:
            man = json.load(fh)
        # DOES THE FINISHED WORK ANSWER THE QUESTION BEING ASKED?
        # Resume skipped tiles on FILENAME AND EXISTENCE ALONE, never
        # comparing what they contain to what was requested. Running
        # k=100 and then k=200 into the same folder reported success
        # and returned N_100, with no N_200 column and no warning -
        # the manifest even RECORDED the old parameters and nobody
        # read them. A run that silently answers an earlier question
        # is the worst kind of wrong (BACKLOG 276).
        was = man.get("params") or {}
        differ = [k for k in sorted(set(was) | set(params))
                  if was.get(k) != params.get(k)]
        if differ:
            lines = [f"{out_dir} already holds a DIFFERENT run, and "
                     "resuming it would return that one's answers:"]
            for k in differ:
                lines.append(f"  {k}: finished run has "
                             f"{was.get(k)!r}, you asked for "
                             f"{params.get(k)!r}")
                # A HASH IS NOT A SENTENCE. The other keys name
                # themselves; this one has to say what it means, or
                # the user reads two hex strings and learns nothing
                # (BACKLOG 344).
                if k == "cells_md5":
                    lines.append(
                        "      -> the CELL DATA differs: same folder, "
                        "different coordinates, populations or group "
                        "totals. The geometry and the cell count can "
                        "match and the people still be different "
                        "numbers.")
                elif k in ("schema", "equipop"):
                    lines.append(
                        "      -> a different EquiPop built those "
                        "tiles. Finish a run with the version that "
                        "started it, or recompute.")
            lines.append("Use an empty folder, or pass resume=False to "
                         "recompute. The tiles on disk are NOT the "
                         "analysis you requested.")
            # Raised BEFORE the loop below, so nothing is computed and
            # nothing on disk is touched - a refused resume leaves the
            # earlier run intact and still resumable by its own caller.
            raise ValueError("\n".join(lines))
        print(f"[bigrun] resume: manifest found, "
              f"{len(man['tiles'])} tiles already done, "
              "parameters and cell data match "
              f"(cells {params['cells_md5'][:8]})")
    else:
        man = {"created": time.strftime("%Y-%m-%d %H:%M:%S"),
               "params": params, "tiles": {}}

    t0 = time.time()
    for n_done, ((gx, gy), grp) in enumerate(groups, 1):
        name = f"tile_{gx}_{gy}.parquet"
        fpath = os.path.join(out_dir, name)
        if resume and name in man["tiles"] and os.path.exists(fpath):
            continue
        kw = dict(m_neighbors=m_neighbors, chunk=chunk,
                  r_values=r_values, decay=decay, decay_eps=decay_eps,
                  overshoot_mode=overshoot_mode, self_rule=self_rule,
                  seed=seed, origins=grp["i"].to_numpy(),
                  # One tile's banner is the whole run's banner
                  # repeated once per tile; a continental run has
                  # thousands of them.
                  report=(n_done == 1))
        if self_potential is not None:
            kw["self_potential"] = self_potential
        res = run_knn_counts(cd, k_values, **kw)
        num = res.select_dtypes(include=[np.floating]).columns
        res[num] = res[num].astype(dtype)
        # The TILE first, then the manifest entry that claims it - and
        # each write replaced into place rather than truncated open.
        # BACKLOG 344: `json.dump(man, open(mpath, "w"))` truncates the
        # manifest before it writes, so a crash, a full disk or a
        # kill in that window leaves a half-written file and the whole
        # finished run unresumable - which is the one failure this
        # module exists to survive. os.replace is atomic within a
        # filesystem, so a reader sees the old manifest or the new one
        # and never a fragment.
        _atomic_write_parquet(res, fpath)
        man["tiles"][name] = {"rows": int(len(res)),
                              "md5": _md5(fpath)}
        _atomic_write_json(man, mpath)               # progressive
        print(f"[bigrun] tile {n_done}/{len(groups)} ({gx},{gy}): "
              f"{len(res):,} origins flushed "
              f"[{time.time() - t0:,.0f} s elapsed]")

    man["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _atomic_write_json(man, mpath)
    print(f"[bigrun] complete: {sum(t['rows'] for t in man['tiles'].values()):,} "
          f"rows in {len(man['tiles'])} tiles")
    return man


def load_tiled(out_dir: str, columns=None,
               verify: bool = True) -> pd.DataFrame:
    """Concatenate all tiles (optionally selected columns only - at
    16M rows, load only what you need). verify=True checks md5s."""
    man = json.load(open(os.path.join(out_dir, "manifest.json")))
    parts = []
    for name, info in man["tiles"].items():
        p = os.path.join(out_dir, name)
        if verify and _md5(p) != info["md5"]:
            raise IOError(f"[bigrun] {name} fails md5 - re-run that "
                          "tile (delete it + its manifest entry, "
                          "resume=True)")
        parts.append(pd.read_parquet(p, columns=columns))
    df = pd.concat(parts, ignore_index=True)
    print(f"[bigrun] loaded {len(df):,} rows from "
          f"{len(man['tiles'])} verified tiles")
    return df


def map_tiles(out_dir: str, fn, *, what: str = "column") -> dict:
    """Apply `fn(frame) -> frame` to every tile IN PLACE.

    BACKLOG 365, v1.53.4. The primitive a tiled machine-4 run needs: a
    demographic index is a RATIO OF TWO COLUMNS THE TILES ALREADY
    CARRY, so it can be added per tile, with memory bounded at one
    tile rather than at a continent.

    THE MANIFEST IS UPDATED PER TILE, NOT AT THE END, and that is the
    whole discipline of this module repeated. `load_tiled(verify=True)`
    checks every md5, so a pass that rewrote all the tiles and then
    wrote one manifest would, if interrupted, leave a run whose every
    tile fails its checksum - the finished continental run unreadable
    because a post-pass was killed. Progressive, so an interrupt
    leaves a run that still READS and is merely missing the new
    column on the tiles not yet reached.

    AND THE md5 IS VERIFIED BEFORE READING, which matters more here
    than in load_tiled. Rewriting a tile computes a FRESH checksum, so
    a post-pass over an already-corrupt tile would launder the
    corruption into a manifest that then agrees with it forever. The
    one chance to notice is before the read.
    """
    mpath = os.path.join(out_dir, "manifest.json")
    if not os.path.exists(mpath):
        raise IOError(f"[bigrun] no manifest.json in {out_dir} - this "
                      "is not a tiled run directory")
    man = json.load(open(mpath))
    names = sorted(man.get("tiles") or {})
    if not names:
        raise IOError(f"[bigrun] {out_dir} holds no tiles to work on")
    dtype = (man.get("params") or {}).get("dtype")
    t0 = time.time()
    cols = []
    for n_done, name in enumerate(names, 1):
        p = os.path.join(out_dir, name)
        if not os.path.exists(p):
            raise IOError(f"[bigrun] {name} is in the manifest and not "
                          "on disk - re-run that tile (resume=True)")
        if _md5(p) != man["tiles"][name]["md5"]:
            raise IOError(
                f"[bigrun] {name} fails md5 BEFORE this pass touched "
                "it, so the tile was already wrong. Refusing rather "
                "than rewriting it, because a rewrite would give the "
                "corrupt tile a fresh checksum and the manifest would "
                "agree with it from then on. Delete that tile and its "
                "manifest entry, then re-run with resume=True.")
        df = pd.read_parquet(p)
        out = fn(df)
        if out is None:
            out = df
        # THE MANIFEST DECLARES THE RUN'S STORAGE dtype, so a column
        # added afterwards has to honour it or the manifest becomes a
        # lie about its own tiles. Measured on the first version of
        # this: the counts were float32 as declared and the index
        # column came out float64, because np.where on float64 inputs
        # returns float64. The manifest's honesty is a property of the
        # RUN DIRECTORY rather than of whoever is calling, which is
        # why it is enforced here and not left to the caller.
        if dtype is not None:
            fcols = out.select_dtypes(include=[np.floating]).columns
            out[fcols] = out[fcols].astype(dtype)
        _atomic_write_parquet(out, p)
        man["tiles"][name] = {"rows": int(len(out)), "md5": _md5(p)}
        _atomic_write_json(man, mpath)               # progressive
        cols = list(out.columns)
        print(f"[bigrun] {what} on tile {n_done}/{len(names)} "
              f"({name}): {len(out):,} rows "
              f"[{time.time() - t0:,.0f} s elapsed]")
    man["columns"] = cols
    _atomic_write_json(man, mpath)
    print(f"[bigrun] {what} written to {len(names)} tiles; read it "
          "back with equipop.bigrun.load_tiled")
    return man
