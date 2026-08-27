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

| prompt | what it is |
|---|---|
| `C:\Something>` | a SHELL — pip commands go here |
| `>>>` | PYTHON — pip commands give `SyntaxError` |

If you see `>>>`, type `exit()` and press Enter. You are then in the
shell.

**A `SyntaxError` mentioning your pip command means you are in Python,
not that anything is wrong with the wheel.**

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

1. In Stata: `python query` — note the **Python executable** path.
2. **Close Stata.** Open an ordinary **Command Prompt**.
3. Install, using that exact path in quotes:
   ```
   "C:\...\python.exe" -m pip install --no-deps --force-reinstall "C:\path\to\equipop-1.41.1-py3-none-any.whl"
   ```
4. Verify, then reopen Stata.

## 3. ArcGIS Pro — NOT VERIFIED BY CLAUDE

**Nothing in this repository has ever run against real ArcGIS Pro.**
There is no arcpy in the development environment, so every instruction
below is read from documentation rather than tested. Treat it as a
hypothesis. If it fails, that is expected, and the failure is
information — send it rather than persevering.

Pro's default environment (`arcgispro-py3`) is **read-only on most
installs**. That is the usual reason a pip install appears to succeed
and Pro then cannot see the package.

**Step 1 — clone the environment (all GUI, no typing).**

1. Open ArcGIS Pro
2. **Project** tab → **Package Manager**
3. Click the **gear icon** beside "Active Environment"
4. Click **Clone** on `arcgispro-py3`, name it `arcgispro-py3-equipop`
5. Wait — it takes several minutes
6. Select the clone → **Activate**
7. **Close and reopen Pro**

**Step 2 — install into the clone.**

Start menu → ArcGIS → **Python Command Prompt**. Check what you got:

```
python -c "import sys; print(sys.executable)"
```

- `SyntaxError` → you are in Python. Type `exit()` and try again.
- A path containing **`arcgispro-py3-equipop`** → correct, continue.
- A path containing plain **`arcgispro-py3`** → the clone is not
  active. Go back to step 1.6.

Then:
```
python -m pip install --no-deps --force-reinstall "C:\path\to\equipop-1.41.1-py3-none-any.whl"
```

Note: **no `--user` here.** Once the environment is a clone it is
writable, and `--user` puts the package somewhere Pro may not look.

**Step 3 — toolbox.** Copy `EquiPop.pyt` anywhere, then in Pro's
Catalog pane: right-click **Toolboxes → Add Toolbox** and select it.

**If the Python Command Prompt cannot be found**, the fallback is
`proenv.bat`, which activates the environment and leaves you in a
shell. Look for it under
`...\ArcGIS\Pro\bin\Python\Scripts\proenv.bat` — the exact path
depends on whether Pro was installed for all users or one user.

---

## Verify — the same line in every host

```
python -c "import equipop, equipop.rasterfolder as r; print(equipop.__version__, r.__file__)"
```

Want the **version** *and* a **path**.

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
