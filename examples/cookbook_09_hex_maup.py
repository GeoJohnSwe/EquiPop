"""cookbook_09 - squares vs hexagons: the MAUP experiment (Book ch. 8)."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from equipop.datasets import load
from equipop.cells import build_cells
from equipop.hex import build_hex_cells
from equipop.fastcounts import run_knn_counts

g = load("gridby"); p = g["people"]
# expand the pre-aggregated squares to one row per person (both
# builders take individuals; deterministic expansion, no randomness)
import pandas as pd
rows = p.loc[p.index.repeat(p.count_all.astype(int))].reset_index(drop=True)
within = rows.groupby(level=0).cumcount() if False else None
rows["g"] = (rows.groupby(["x", "y"]).cumcount()
             < rows["count_group"]).astype(int)
sq = build_cells(rows, "x", "y", binary_vars=["g"], unit_size=100)
hx = build_hex_cells(rows, "x", "y", binary_vars=["g"],
                     hex_size=107)   # ~equal area to a 100 m square
out_s = run_knn_counts(sq, [400])
out_h = run_knn_counts(hx, [400])
fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.2))
for a, (o, t) in zip(ax, [(out_s, "100 m squares"),
                          (out_h, "hexagons (equal area)")]):
    s = a.scatter(o.EastWest/1000, o.NorthSouth/1000, c=o.R_g_400,
                  s=6, cmap="viridis", vmin=0, vmax=0.8)
    a.set_title(f"context share, k = 400 - {t}")
    a.set_aspect("equal"); a.set_xlabel("km")
    plt.colorbar(s, ax=a, shrink=.85)
    a.spines[["top","right"]].set_visible(False)
fig.tight_layout(); fig.savefig("docs/book/figs/ch08_hex.png", dpi=140)
r = np.corrcoef  # report stability
print("ch08 figure saved | share ranges:",
      round(out_s.R_g_400.min(),3), "-", round(out_s.R_g_400.max(),3),
      "(sq) vs", round(out_h.R_g_400.min(),3), "-",
      round(out_h.R_g_400.max(),3), "(hex)")
