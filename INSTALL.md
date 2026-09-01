# Installing EquiPop locally — QGIS, Stata, ArcGIS Pro

**One method, every session.** Each release ships four files. Install
from those, never from a folder and never from PyPI while testing.

| file | what it is |
|---|---|
| `equipop-<ver>-py3-none-any.whl` | the engine |
| `equipop-<ver>.tar.gz` | source, for PyPI |
| `equipop_qgis-<ver>.zip` | the QGIS plugin |
| `EquiPop.pyt` | the ArcGIS Pro toolbox |

---

## The three rules that break installs

1. **`--no-deps`, always.** Without it pip upgrades the host's numpy,
   scipy or pyproj. That is what broke QGIS's scipy and Stata's pyproj.
2. **`--force-reinstall` only alongside `--no-deps`.** Same version
   number can mean different code; without force, pip skips the
   install and you test the old one.
3. **Close the host program first.** Windows memory-maps the DLLs.

---

## ⚠️ Shell or Python? Check before typing anything

Every host has a "Python prompt" that may be either a **shell** or the
**Python interpreter**, and they look similar.

| prompt | what it is | a wrong command gives |
|---|---|---|
| `C:\Something>` | a **shell** — pip goes here | `'x' is not recognized...` |
| `>>>` | **Python** | `SyntaxError` |
| `.` at the left edge | **Stata** | `command C is unrecognized` |

**None of those three errors means anything is wrong with the wheel.**
Each means the command went to the wrong program. Both hosts that
failed — Pro and Stata — failed this way, not on the package.

If you see `>>>`, type `exit()`. If you are in Stata, see the `shell`
route in section 2.

---

## 1. QGIS — verified working

1. Start menu → **OSGeo4W Shell**
2. Confirm the shell and the interpreter:
   ```
   python -c "import sys; print(sys.executable)"
   ```
   Must print a path under `C:\OSGeo4W\`.
3. Install:
   ```
   python -m pip install --user --no-deps --force-reinstall "C:\path\to\equipop-1.41.1-py3-none-any.whl"
   ```
4. Verify (see below), then **restart QGIS**.
5. Plugin: **Plugins → Manage and Install Plugins → Install from ZIP**,
   choose `equipop_qgis-1.41.1.zip`, then restart QGIS again.

Rasterio and pyarrow are needed once, for the raster tools:
```
python -m pip install --user --no-deps rasterio==1.4.4 affine
```
**Not `rasterio` unpinned** — 1.5+ demands numpy≥2 and will drag a
numpy into your user folder that shadows QGIS's own and breaks scipy.

## 2. Stata — verified working

1. In Stata: `python query`. Note the **Python executable** path, and
   check **`initialized`**.

**If `initialized: no` — stay in Stata, no prompt switching.** Python
is not loaded, so nothing is memory-mapped. Prefix with `shell`:

```
shell C:\Users\...\python.exe -m pip install --no-deps --force-reinstall C:\path\to\equipop-1.41.1-py3-none-any.whl
```

**No quotes** if the paths have no spaces — Stata mangles them. If a
path does contain a space, close Stata and use a Command Prompt
instead.

Verify, still in Stata:
```
python: import equipop, equipop.rasterfolder as r; print(equipop.__version__, r.__file__)
```

**If `initialized: yes`** — Python is loaded and the DLL is
memory-mapped. Close Stata, open a **Command Prompt**, and run the
same command there without the `shell` prefix, quoting the paths.

## 3. ArcGIS Pro — JOHN'S METHOD, verified on his machine

**No shell at all.** Use Pro's own Python window, which is docked in
Pro: **View → Python** (or the Python pane at the bottom of the
Geoprocessing view).

Paste these four lines, one at a time:

```python
import sys, os, subprocess
py = os.path.join(sys.exec_prefix, "python.exe")
env = dict(os.environ, PYTHONNOUSERSITE="1")
subprocess.run([py, "-m", "pip", "install", "--no-deps",
                "--force-reinstall",
                r"C:\path\to\equipop-1.44.0-py3-none-any.whl"], env=env)
```

Then **restart Pro** and check, in the same window:

```python
import equipop; print(equipop.__version__)
```

**Why this works where a shell did not**, and it is worth knowing:

- **Pro's Python window cannot be the wrong interpreter.** Every shell
  route depends on finding the right one, and that is what failed
  repeatedly.
- **`sys.exec_prefix`** locates the interpreter without anyone having
  to know the path, so it survives any install layout.
- **`PYTHONNOUSERSITE="1"`** is the crucial one. Without it pip may
  install into `%APPDATA%\Python\...`, which **Pro does not read** —
  so the install succeeds and Pro still cannot see the package.
- `subprocess.run` spawns a child process, so the running interpreter
  is not writing over its own loaded DLLs.

To take a release from PyPI instead of a local wheel, replace the path
with `"equipop==1.44.0"` and drop `--no-deps --force-reinstall`.

**If Pro still cannot see it**, the environment is read-only: Project
→ Package Manager → gear → **Clone**, activate the clone, restart Pro,
and repeat. Cloning is entirely GUI.

## Verify — the same line in every host

```
python -c "import equipop, equipop.doors.demography as d; print(equipop.__version__, d.__file__)"
```

Want the **version** *and* a **path**.

`doors.demography` is used on purpose: it is new in 1.41 and needs no
optional library, so it proves the local build arrived without
demanding rasterio. The earlier version of this line used
`rasterfolder`, which DID need rasterio — so a correct Stata install
reported a traceback and looked broken.

**The version alone proves nothing.** PyPI's 1.40.7 and the working
tree's 1.40.7 were different code, which cost a full round trip.
`rasterfolder` importing is what proves the local build arrived; if it
raises `ModuleNotFoundError`, pip found an older release instead.

---

## What to send when it fails

Three things, and they diagnose almost everything:

1. `python -c "import sys; print(sys.executable)"`
2. the full pip output, including the last line
3. the verify line above

Pasted as **text**, not a screenshot — attachments have arrived empty
three times.
