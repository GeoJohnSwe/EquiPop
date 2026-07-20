# EquiPop for ArcGIS Pro - setup and first run

*Pro only (Python 3). Ten minutes the first time, zero thereafter.*

## 1. One-time: give Pro's Python the EquiPop package

ArcGIS Pro ships its own Python inside a conda environment, and the
default one is locked. The supported route is a clone:

1. In Pro: **Project -> Package Manager** (older versions: Python tab)
   -> **Environment Manager** -> select `arcgispro-py3` -> **Clone**.
   Name it e.g. `arcgispro-equipop`. (A few minutes.)
2. **Activate** the clone in the same dialog, restart Pro when asked.
3. Start menu -> ArcGIS -> **Python Command Prompt** (it opens inside
   the ACTIVE environment) and run:

       pip install equipop

4. Check: `python -c "import equipop; print(equipop.__version__)"`

## 2. Add the toolbox to a project

Copy the `arcgis/EquiPop.pyt` file anywhere convenient (it can live
in the project folder). In Pro's **Catalog** pane: right-click
**Toolboxes -> Add Toolbox** -> pick the .pyt. Three tools appear
under "EquiPop".

## 3. First run (Counts and Shares)

Open **1. Counts and Shares**, pick your point layer of people,
choose a 0/1 group field, type `200 1600` under k, optionally a
decay half-life like `3000`, and run. New double fields appear on
the layer: `N_200`, `R_<group>_200`, `Dist_200`, ... and `ND_inf`
if decay was on - ready for **Symbology** or a join. Rows without
geometry get Null, as they should.

Tool 2 does income: pick numeric fields, statistics `mean median
gini`, k - fields like `Med_income_400` and `Gini_income_400`
appear. Tool 3 takes a barrier csv (`x,y,friction` in the SAME
metric coordinate system as the layer) and returns `Rounds_k` and
`N_tau...` isochrone counts.

## 4. Three things worth knowing

- **File geodatabase beats shapefile**: shapefiles truncate field
  names to 10 characters; the tool warns, but a gdb layer is the
  honest home for `Gini_income_400`.
- **Metric coordinates required** (metres - SWEREF 99, UTM...), the
  book's chapter 3 rule; reproject with Pro's Project tool first if
  needed.
- **Re-running**: results are appended; re-running with the same
  parameters overwrites those fields via the join. Different k
  values simply add more fields.

## 5. When something fails

"No module named equipop" -> Pro is not using your clone: Package
Manager, activate the clone, restart. Anything else -> the message
window shows the package's own loud diagnostics; copy them to the
maintainers (or to Claude) verbatim.


## 6. Troubleshooting - the field-tested ladder (v1.14)

Every step below was walked in a real failing installation; walk it
in order.

1. **Which Python is Pro using?** Python window:
   `import sys; print(sys.exec_prefix)` - NOT sys.executable, which
   in Pro's embedded window is ArcGISPro.exe itself (using it for
   pip LAUNCHES A SECOND PRO - do not ask how we know). The prefix
   must end in your CLONE's name; `arcgispro-py3` means the clone is
   not active: Environment Manager -> activate -> full Pro restart.
2. **The stowaway check.** `pip show equipop` may claim the package
   exists while Pro cannot import it: read the **Location** line. If
   it says `AppData\Roaming\Python\...` the package was stranded by
   pip's silent "user installation" fallback in a folder Pro NEVER
   READS. Evict and reinstall with the fallback disabled:

       import sys, os, subprocess
       py = os.path.join(sys.exec_prefix, "python.exe")
       env = dict(os.environ, PYTHONNOUSERSITE="1")
       subprocess.run([py, "-m", "pip", "uninstall", "-y", "equipop"])
       subprocess.run([py, "-m", "pip", "install", "equipop"],
                      env=env)

   Restart Pro (it binds packages at startup).
3. **Version check.** `import equipop; print(equipop.__version__)` -
   the toolbox needs >= 1.14.0 for the category mode and output
   options.

## 7. Reading the results honestly

- `Dist_k` is in METRES and that is the point: it is the radius each
  point needed to gather its k persons - k fixes the population, the
  geography floats. The tool prints this reminder whenever the
  column appears.
- If a share exceeds 1 or N looks smaller than T, the group field
  holds COUNTS while the Population field was left empty - the tool
  now prints a hint the moment it sees that pattern. Set Population
  to the total-persons field.
- Category mode: rows outside the population filter get Null in
  every result column - they were not part of the analysis, and
  Null says so.
