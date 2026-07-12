"""
viz.py - quick-look maps of k-NN output (backlog item 8).

Deliberately simple: QGIS remains the real GIS (save_output(..., .gpkg)
gets you there); this is quality-control cartography with the basics -
class legend, scale bar, north arrow, and export.

    from equipop.viz import map_output
    map_output(res, "R_VM_1600", cell="square", unit_size=100,
               classing="jenks", n_classes=6, save="map.png")

classing : 'quantiles' | 'equal' | 'sd' | 'jenks'
cell     : 'square' (grid) | 'hex' (pointy-top) | 'point'
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle, RegularPolygon


def class_bounds(v: np.ndarray, classing: str, n: int) -> np.ndarray:
    v = v[np.isfinite(v)]
    if classing == "quantiles":
        b = np.quantile(v, np.linspace(0, 1, n + 1))
    elif classing == "equal":
        b = np.linspace(v.min(), v.max(), n + 1)
    elif classing == "sd":
        m, s = v.mean(), v.std()
        half = (n // 2)
        b = m + s * np.arange(-half, n - half + 1)
        b[0], b[-1] = min(b[0], v.min()), max(b[-1], v.max())
    elif classing == "jenks":
        try:
            import jenkspy
            b = np.array(jenkspy.jenks_breaks(v, n_classes=n))
        except ImportError:
            print("[viz] jenkspy not installed - falling back to "
                  "quantiles (pip install jenkspy).")
            return class_bounds(v, "quantiles", n)
    else:
        raise ValueError(f"Unknown classing '{classing}'")
    return np.unique(b)


def map_output(df: pd.DataFrame, column: str,
               x_col: str = "EastWest", y_col: str = "NorthSouth",
               cell: str = "square", unit_size: float = 100.0,
               classing: str = "quantiles", n_classes: int = 5,
               cmap: str = "viridis", title: str | None = None,
               save: str | None = None, dpi: int = 150,
               figsize=(9, 9)):
    """Draw a classed map of one output column. Returns (fig, ax);
    save='map.png'/'.svg'/'.pdf' exports it."""
    x = df[x_col].to_numpy(float)
    y = df[y_col].to_numpy(float)
    v = df[column].to_numpy(float)
    b = class_bounds(v, classing, n_classes)
    n = len(b) - 1
    cls = np.clip(np.digitize(v, b[1:-1]), 0, n - 1)
    colors = plt.get_cmap(cmap)(np.linspace(0.05, 0.95, n))

    fig, ax = plt.subplots(figsize=figsize)
    if cell == "point":
        ax.scatter(x, y, c=colors[cls], s=3, linewidths=0)
    else:
        patches, u = [], unit_size
        if cell == "square":
            for xi, yi in zip(x, y):
                patches.append(Rectangle((xi - u / 2, yi - u / 2), u, u))
        else:  # hex, pointy-top; radius = width/sqrt(3)
            r = u / np.sqrt(3)
            for xi, yi in zip(x, y):
                patches.append(RegularPolygon((xi, yi), 6, radius=r))
        pc = PatchCollection(patches, linewidths=0)
        pc.set_facecolor(colors[cls])
        ax.add_collection(pc)
        ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title or f"{column} ({classing}, {n} classes)")

    # legend with class bounds
    from matplotlib.patches import Patch
    fmt = (lambda a: f"{a:.3g}")
    handles = [Patch(facecolor=colors[i],
                     label=f"{fmt(b[i])} \u2013 {fmt(b[i+1])}")
               for i in range(n)]
    ax.legend(handles=handles, loc="lower right", fontsize=8,
              title=column, framealpha=0.9)

    # scale bar (nice round length ~ 1/5 of width) + north arrow
    span = x.max() - x.min()
    L = 10 ** np.floor(np.log10(span / 5))
    L *= max(1, round(span / 5 / L))
    x0 = x.min() + 0.05 * span
    y0 = y.min() + 0.03 * (y.max() - y.min())
    ax.plot([x0, x0 + L], [y0, y0], color="k", lw=3)
    lab = f"{L/1000:g} km" if L >= 1000 else f"{L:g} m"
    ax.text(x0 + L / 2, y0, "\n" + lab, ha="center", va="top", fontsize=8)
    ax.annotate("N", xy=(0.97, 0.97), xycoords="axes fraction",
                ha="center", fontsize=12, fontweight="bold")
    ax.annotate("", xy=(0.97, 0.965), xytext=(0.97, 0.925),
                xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="k"))

    if save:
        fig.savefig(save, dpi=dpi, bbox_inches="tight")
        print(f"[viz] saved {save}")
    return fig, ax
