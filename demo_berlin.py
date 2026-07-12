"""
demo_berlin.py - runs the full Phase 1 pipeline on the Berlin example
and VALIDATES the result against the original EquiPop output.

Run from the folder that contains both this file and the Excel file:
    python demo_berlin.py
"""

import pandas as pd
from equipop import project_to_metric, snap_to_grid, run_knn
from equipop.transform import aggregate_to_cells

XLSX = "EquiPop_IN_and_out_example.xlsx"
K_VALUES = [50, 100, 200, 400, 800]
UNIT = 100.0  # metres

# ---------------------------------------------------------------- 1. load
# header row is the SECOND row of the sheet (first row holds the
# Mandatory/Optional colour labels)
indata = pd.read_excel(XLSX, sheet_name="Indata_and_generated_data", header=1)
print(f"Loaded {len(indata)} records")

# ------------------------------------------------------- 2. project + snap
df = project_to_metric(indata, target_epsg=25832)
df = snap_to_grid(df, unit_size=UNIT)

# validate projection against the pre-computed columns in the file
proj_err = (df["easting_m"] - df["easting_epsg25832_m"]).abs().max()
snap_ok = ((df["E_grid"] == df["E25832_100m"]) &
           (df["N_grid"] == df["N25832_100m"])).all()
print(f"Projection max abs error vs file: {proj_err:.4f} m")
print(f"Grid snapping matches file:      {snap_ok}")

# -------------------------------------------------------------- 3. analyse
cells = aggregate_to_cells(df, value_cols=["FullPop", "Treatment"], id_col="id")
result = run_knn(cells, k_values=K_VALUES,
                 unit_size=UNIT, max_radius_units=400, id_col="id")

# ----------------------------------------------- 4. compare with original
expected = pd.read_excel(XLSX, sheet_name="EquiPop_output")

# join on grid coordinates (ids match 1:1 in this example anyway)
merged = expected.merge(result, on=["EastWest", "NorthSouth"],
                        suffixes=("_orig", "_new"))
print(f"\nMatched {len(merged)} of {len(expected)} cells")

print("\n=== Validation: original EquiPop vs this implementation ===")
for k in K_VALUES:
    for var, tol in [(f"IntervalSumCountAll_{k}", 0.5),
                     (f"IntervalRatio_{k}", 1e-4),
                     (f"IntervalDistance_{k}", 0.5)]:
        diff = (merged[f"{var}_orig"] - merged[f"{var}_new"]).abs()
        n_bad = (diff > tol).sum()
        print(f"{var:32s} max diff = {diff.max():12.4f}   "
              f"mismatches (> {tol}): {n_bad}")

result.to_csv("berlin_knn_output.csv", index=False)
print("\nSaved: berlin_knn_output.csv")
