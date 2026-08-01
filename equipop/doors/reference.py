# -*- coding: utf-8 -*-
"""
reference.py - the answer every door is measured against.

Gridby's planted truths (seed 1848) prove that ONE door is sane: the
west-east gradient comes out, the river bites, the hill is where it
was put. They cannot prove that TWO doors AGREE, because both can sit
comfortably inside those bounds and still return different numbers.
A student in QGIS and a student in ArcGIS Pro would then get
different answers from the same town, and neither would be wrong
enough to notice.

So: one documented run, executed by the Python core - the engine the
test suite already trusts - and stored as a CSV that ships inside the
package. A door is finished when it reproduces that table.

WHY A CSV. Every door reads and writes one without help: ArcGIS Pro,
QGIS, Stata, SPSS. A student can open it in Excel and look at it. It
diffs in git. The format is pinned so it cannot drift: UTF-8, a DOT
for the decimal mark (a Swedish machine writes commas and would
silently produce an unreadable reference), comma between fields,
fixed column order.

WHAT IS COMPARED, AND HOW STRICTLY. Counts are whole people and must
match EXACTLY - a door that finds 406 neighbours where the core finds
407 is wrong, not imprecise. Distances and ratios are continuous and
are compared within a tolerance, because a door may reach them
through a different order of operations.
"""

import os

import numpy as np
import pandas as pd

_DATA = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "data")
REFERENCE_CSV = os.path.join(_DATA, "gridby_reference.csv")

# The conformance run, in full. Changing anything here changes the
# answer, so it is written down rather than passed around.
SPEC = {
    "dataset": "gridby",
    "seed": 1848,
    "unit_size": 100.0,
    "weight": "count_all",          # people represented by each row
    # Named by the FIELD, because that is what a door produces: both
    # the ArcGIS toolbox and the QGIS plugin pass {field_name: values}
    # to the engine. A prettier label here would make a reference no
    # door could ever match - which is exactly what happened in
    # 1.19.0 and was caught by building the second door.
    "treat": {"count_group": "count_group"},
    "treat_are_counts": True,       # weighted rows, so these are counts
    "k_values": [400],
    "r_values": [800.0],
    "values": {"count_group": ["mean", "median", "gini"]},
}

KEY = ["x", "y"]
# Whole people: these must match exactly. Everything else is
# continuous (Dist_, R_, Mean_, Med_, Gini_, percentiles) and is
# compared within a tolerance.
EXACT_PREFIXES = ("N_", "T_", "Nv_", "Rounds_")


def _gridby_inputs():
    from equipop.datasets import load
    p = load(SPEC["dataset"])["people"]
    return p


def generate() -> pd.DataFrame:
    """Run the conformance spec through the Python core."""
    from equipop.stata_bridge import dispatch
    p = _gridby_inputs()
    x, y = p.x.values.astype(float), p.y.values.astype(float)
    common = dict(unit_size=SPEC["unit_size"], k_values=SPEC["k_values"])

    counts = dispatch("counts", x, y,
                      weight=p[SPEC["weight"]].values,
                      treat={n: p[c].values
                             for n, c in SPEC["treat"].items()},
                      treat_are_counts=SPEC["treat_are_counts"],
                      r_values=SPEC["r_values"], **common)

    stats = dispatch("stats", x, y,
                     weight=p[SPEC["weight"]].values,
                     values={c: p[c].values for c in SPEC["values"]},
                     stats=SPEC["values"], **common)

    out = pd.DataFrame({"x": x, "y": y})
    for src in (counts, stats):
        for col, arr in src.items():
            if col not in out:
                out[col] = np.asarray(arr, dtype=float)
    return out[KEY + sorted(c for c in out.columns if c not in KEY)]


def write(path: str = REFERENCE_CSV) -> str:
    """Write the reference with the format pinned."""
    df = generate()
    df.to_csv(path, index=False, encoding="utf-8",
              float_format="%.10g", lineterminator="\n")
    return path


def load_reference() -> pd.DataFrame:
    if not os.path.exists(REFERENCE_CSV):
        raise FileNotFoundError(
            "gridby_reference.csv is missing from the package. "
            "Regenerate it with:  python -m equipop.doors.reference")
    return pd.read_csv(REFERENCE_CSV, encoding="utf-8")


def compare(table, rtol: float = 1e-6, atol: float = 1e-9) -> dict:
    """Measure a door's output against the reference.

    `table` is anything pandas can turn into a DataFrame - a door's
    result written to CSV, or its arrays handed over directly. Rows
    are matched on the coordinates, not on row order, because doors
    are free to return rows in their own order.

    Returns a report: ok, plus what is missing, what is extra, and
    every column that disagrees with the worst offending row named.
    A door is finished when ok is True.
    """
    ref = load_reference()
    got = pd.DataFrame(table).copy()

    report = {"ok": False, "missing_columns": [], "extra_columns": [],
              "row_mismatch": None, "columns_differing": {},
              "rows_compared": 0}

    for k in KEY:
        if k not in got.columns:
            report["missing_columns"] = [k]
            return report
        got[k] = np.round(got[k].astype(float), 3)
        ref[k] = np.round(ref[k].astype(float), 3)

    if len(got) != len(ref):
        report["row_mismatch"] = (len(ref), len(got))
        return report

    merged = ref.merge(got, on=KEY, how="inner", suffixes=("_ref", "_got"))
    if len(merged) != len(ref):
        report["row_mismatch"] = (len(ref), len(merged))
        return report
    report["rows_compared"] = len(merged)

    want = [c for c in ref.columns if c not in KEY]
    report["missing_columns"] = [c for c in want if c not in got.columns]
    report["extra_columns"] = [c for c in got.columns
                               if c not in ref.columns and c not in KEY]

    for c in want:
        if c not in got.columns:
            continue
        a = merged[f"{c}_ref"].to_numpy(float)
        b = merged[f"{c}_got"].to_numpy(float)
        if c.startswith(EXACT_PREFIXES):
            bad = ~np.isclose(a, b, rtol=0, atol=1e-9, equal_nan=True)
            rule = "exact"
        else:
            bad = ~np.isclose(a, b, rtol=rtol, atol=atol, equal_nan=True)
            rule = f"rtol={rtol:g}"
        if bad.any():
            i = int(np.argmax(np.abs(np.nan_to_num(a - b))))
            report["columns_differing"][c] = {
                "rule": rule, "n_rows_differing": int(bad.sum()),
                "worst_row": {"x": float(merged[KEY[0]][i]),
                              "y": float(merged[KEY[1]][i]),
                              "reference": float(a[i]), "door": float(b[i])}}

    report["ok"] = (not report["missing_columns"]
                    and not report["columns_differing"]
                    and report["row_mismatch"] is None)
    return report


def explain(report: dict) -> str:
    """The report as sentences, for a door's message pane."""
    if report["ok"]:
        return (f"Conformance PASSED: {report['rows_compared']} rows "
                "match the Gridby reference on every column.")
    lines = ["Conformance FAILED."]
    if report["row_mismatch"]:
        want, got = report["row_mismatch"]
        lines.append(f"  Rows: reference has {want}, this door "
                     f"matched {got} - the coordinates do not line up.")
    for c in report["missing_columns"]:
        lines.append(f"  Missing column: {c}")
    for c, d in report["columns_differing"].items():
        w = d["worst_row"]
        lines.append(
            f"  {c}: {d['n_rows_differing']} rows differ ({d['rule']}). "
            f"Worst at x={w['x']:g} y={w['y']:g} - reference "
            f"{w['reference']:.6g}, this door {w['door']:.6g}")
    return "\n".join(lines)


if __name__ == "__main__":
    p = write()
    df = load_reference()
    print(f"[reference] wrote {p}")
    print(f"[reference] {len(df)} rows x {len(df.columns)} columns")
    print(f"[reference] columns: {', '.join(df.columns)}")
