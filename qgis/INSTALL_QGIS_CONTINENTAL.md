# Installing the continental tool in QGIS

For John, on Windows with OSGeo4W. Two halves to install — the
**engine** (a Python package) and the **plugin** (the QGIS tool that
calls it) — and one trap that must be dealt with first.

---

## ⚠️ READ THIS FIRST: do NOT install the engine from PyPI

You published **1.40.7** to PyPI. The working tree is **also called
1.40.7**, and it is not the same code.

| | on PyPI | in the working tree |
|---|---|---|
| `equipop/rasterfolder.py` | **absent** | present |
| `equipop/doors/continental.py` | **absent** | present |
| BACKLOG 207 (radius moved with the search window) | **present** | fixed |
| fractional WorldPop weights | rounds them away | kept |

So `pip install equipop` in OSGeo4W gives you an engine the new tool
**cannot run against** — and `equipop doctor` will report `1.40.7`
against `1.40.7` and look perfectly healthy, because the version
string is the one thing that did not change.

**Install the engine from the folder, not from PyPI.** Everything
below does that.

*(This is a one-off. Once the next release is cut and uploaded, the
ordinary `pip install --upgrade equipop` route works again.)*

---

## 1. Open the OSGeo4W Shell

Start menu → **OSGeo4W Shell**. Not a normal Command Prompt: this one
has QGIS's own Python on its path, and that is the Python the plugin
will use.

Check you are in the right shell:

**[OSGeo4W Shell]**
```
python -c "import sys; print(sys.executable)"
```

The path it prints should sit inside your QGIS installation — usually
under `C:\OSGeo4W\`. If it points at
`C:\Users\joost307\AppData\Local\Programs\Python\...` you are in the
wrong shell; that is your Stata Python and installing there will not
help QGIS.

---

## 2. Install the two extra libraries

The continental tool reads GeoTIFFs and writes tiles, which QGIS's
Python does not ship for.

**[OSGeo4W Shell]**
```
python -m pip install --user rasterio pyarrow
```

**Do not add `--force-reinstall`.** Without `--no-deps` it would also
reinstall numpy, pandas, scipy and pyproj inside QGIS's managed stack,
which is a well-known way to break a working QGIS. It is the same
mistake that broke your Stata `pyproj` last week.

---

## 3. Install the engine from the folder

**[OSGeo4W Shell]**
```
python -m pip install --user --no-deps "C:\Data\EQP\Sides\BigRun_Aug21\equipop_working_tree\EquiPop"
```

Change the path if you unzipped elsewhere. It must be the folder that
**contains `pyproject.toml`** — the middle one of the three
similarly-named folders.

`--no-deps` is deliberate: everything EquiPop needs is already in
QGIS, and this stops pip touching the rest of the stack.

Then check it took:

**[OSGeo4W Shell]**
```
python -c "import equipop, equipop.rasterfolder; print(equipop.__version__, 'rasterfolder OK')"
```

If it prints `1.40.7 rasterfolder OK` you have the right one. If it
says `No module named 'equipop.rasterfolder'`, pip found the PyPI copy
instead — go back to step 3 and check the path.

---

## 4. Install the plugin

In QGIS: **Plugins → Manage and Install Plugins → Install from ZIP**,
choose `equipop_qgis-1.40.7.zip`, **Install Plugin**.

Then **restart QGIS**. The plugin reads the engine once at startup.

---

## 5. Check it arrived

**Processing → Toolbox**, open the **EquiPop** group. You should see
three tools:

```
1. Counts and Shares (k / radius / decay)
2. Value Statistics
3. Continental run from a folder of rasters      <- the new one
```

If the third is missing, the plugin did not install; if it is there but
refuses on opening, the engine is the PyPI one.

---

# Loading your rasters

## Keep your folders exactly as they are

Your downloads arrive **one folder per country**, each holding every
age and sex. **Point the tool at the folder above them and leave the
structure alone.** Subfolders are searched, so this works as it stands:

```
C:\Data\WorldPop\
    Africa\
        bdi\  bdi_f_15_2020_CN_100m_R2025A_v1.tif
              bdi_m_15_2020_CN_100m_R2025A_v1.tif
              ...
        rwa\  rwa_f_15_2020_CN_100m_R2025A_v1.tif
              ...
    Europe\
        dnk\  ...
```

Point box 1a at `C:\Data\WorldPop\Africa`, or at `C:\Data\WorldPop` to
take both continents at once.

Verified rather than assumed: the same files nested in country folders
and laid out flat gave **267,632 points either way, identical to the
row**.

## What the tool does with the names

The filename is read for the cohort — **sex, age, year** — and the
**country is deliberately ignored**. That is not an oversight:

- **Different countries are different GROUND.** They do not overlap, so
  they stack as **rows** in one column.
- **Different cohorts are the SAME ground.** They do overlap, so they
  become **separate columns** on the same points.

Which is which is decided by **measuring where the rasters actually
hold data**, never by their names — so it still works when WorldPop
renames everything. Burundi and Rwanda share a bounding box and not one
single pixel with data in both, which is exactly the case a
name-based or extent-based rule gets wrong.

**Zeros are kept.** A pixel with no women aged 15–19 but three men
survives, with a real `0.0` in the women's column.

---

# Filling in the boxes

| box | what to put | why |
|---|---|---|
| **1a. Folder** | the folder above your country folders | subfolders are searched |
| **1b. Neighbourhood sizes** | `1000` to start; `100 1000 5000` for several | these are **people**, not metres |
| **1c. Cell size** | `1000` | the **analysis** grid in metres, *not* the raster's own resolution |

Advanced, and usually leave alone:

| box | leave blank unless |
|---|---|
| **2a. Projection** | blank lets the data suggest one. It will refuse a projection in degrees — neighbourhood work needs metres |
| **2b. People column** | only needed when the folder yields more than one cohort |
| **2c. Add all cohorts** | tick to collapse every cohort into one population |
| **2d. Filename pattern** | only when WorldPop's naming changes and the tool says it could not read the names |
| **3a. Tiles folder** | give one for anything large — see below |

## Cell size, and why 1000 is the sensible start

`1c` is the grid the analysis is done on, and it is independent of the
100 m rasters. **Match it to your rasters, and never set it just above them.**
WorldPop "1 km" is 30 arc-seconds — about **927 m** near the equator,
not 1000. A 1000 m grid then puts ONE source pixel in most cells and
TWO in every thirteenth, and those cells hold twice the population.
`Dist_k` follows density, so the result is regular stripes across the
whole map every 12 km or so. Use the source spacing **or finer** — for
1 km WorldPop, 100 m. The tool now warns when the two beat against
each other, but the safe habit is to look at the raster first. 100 m over a
continent is a very large run: Burundi + Rwanda alone is 3.9 million
points, and one cohort of four countries was 11.5 million.

## When to give a tiles folder

If the run is bigger than a few hundred thousand cells, put a folder in
**3a**. Then:

- the answers are **identical** — tiling splits the *origins*, never the
  data, so there are no seams;
- results are written as the run goes, instead of being held in memory;
- **it resumes** — point it at the same folder again after an
  interruption and it continues where it stopped.

The tool warns you when a run is large enough to want this. It is
advice, not a refusal.

---

# Reading the output

One point per analysis cell, carrying:

- **`N_1000`** — people in the neighbourhood. Exactly 1000 by
  construction: **k fixes the population**.
- **`Dist_1000`** — the **radius that origin needed** to gather its
  1000 people. This is the one people misread. It is not an error term
  and not a parameter: **the variation in it IS the density of the
  place.** Tight in a town, wide in the countryside.
- **`T_<group>_1000` / `R_<group>_1000`** — group count and share, when
  cohorts are carried as groups.

---

# If something goes wrong

**"No module named 'equipop.rasterfolder'"** — the engine came from
PyPI. Redo step 3 with the folder path.

**"That projection is in degrees"** — clear box 2a and let the tool
choose.

**"which column holds the people?"** — the folder yielded more than one
cohort. Either name one in 2b, or tick 2c to add them together.

**"Not a folder"** — the path in 1a is wrong. Remember it wants the
folder, not a `.tif`.

**QGIS itself misbehaves after installing** — you almost certainly used
`--force-reinstall` and replaced QGIS's numpy or pyproj. Reinstall
QGIS; it is faster than unpicking it.
