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


def run_knn_counts_tiled(cd, k_values=None, r_values=None, decay=None,
                         out_dir: str = "equipop_tiles",
                         tile_m: float = 50_000.0,
                         dtype: str = "float32",
                         resume: bool = True,
                         m_neighbors: int = 4096,
                         chunk: int = 4096) -> dict:
    """Run the fast engine tile by tile, flushing each tile to
    parquet. Returns the manifest dict (also written progressively to
    out_dir/manifest.json). Results are EXACTLY those of an untiled
    run - only the packaging differs."""
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

    params = {"k_values": k_values, "r_values": r_values,
               "decay": (None if decay is None else
                         {"model": decay.model,
                          "half_life_m": decay.half_life_m,
                          "gamma": decay.gamma}),
               "tile_m": tile_m, "dtype": dtype,
               "unit_size": cd.unit_size,
               "n_cells": int(len(cd.E))}

    if resume and os.path.exists(mpath):
        man = json.load(open(mpath))
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
            lines.append("Use an empty folder, or pass resume=False to "
                         "recompute. The tiles on disk are NOT the "
                         "analysis you requested.")
            raise ValueError("\n".join(lines))
        print(f"[bigrun] resume: manifest found, "
              f"{len(man['tiles'])} tiles already done, "
              "parameters match")
    else:
        man = {"created": time.strftime("%Y-%m-%d %H:%M:%S"),
               "params": params, "tiles": {}}

    t0 = time.time()
    for n_done, ((gx, gy), grp) in enumerate(groups, 1):
        name = f"tile_{gx}_{gy}.parquet"
        fpath = os.path.join(out_dir, name)
        if resume and name in man["tiles"] and os.path.exists(fpath):
            continue
        res = run_knn_counts(cd, k_values, m_neighbors=m_neighbors,
                             chunk=chunk, r_values=r_values,
                             decay=decay, origins=grp["i"].to_numpy())
        num = res.select_dtypes(include=[np.floating]).columns
        res[num] = res[num].astype(dtype)
        res.to_parquet(fpath, index=False)
        man["tiles"][name] = {"rows": int(len(res)),
                              "md5": _md5(fpath)}
        json.dump(man, open(mpath, "w"), indent=1)   # progressive
        print(f"[bigrun] tile {n_done}/{len(groups)} ({gx},{gy}): "
              f"{len(res):,} origins flushed "
              f"[{time.time() - t0:,.0f} s elapsed]")

    man["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    json.dump(man, open(mpath, "w"), indent=1)
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
