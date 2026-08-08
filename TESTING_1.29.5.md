# Testing 1.29.5 before you publish it

Install, run, look. Nothing here needs code.

---

## Install

### 1. The Python package, into QGIS's own Python

**Close QGIS first.** On Windows pip cannot overwrite files a running
process holds open, and it often fails quietly enough to look like it
worked.

Open the **OSGeo4W Shell** (Start menu, under QGIS):

```
cd /d C:\path\to\the\files
python -m pip install --force-reinstall --no-deps equipop-1.29.5-py3-none-any.whl
```

**`--no-deps` matters.** Without it, `--force-reinstall` also reinstalls
pandas, numpy, scipy and pyproj — the four libraries QGIS itself is
built on. Replacing those from PyPI is a well-known way to break a
working QGIS. You already have them; they should not be touched.

`cd` first so there is no long path to mistype. Run `dir` to check the
wheel is where you think it is.

If pip complains about permissions, reopen the shell as Administrator.

### 2. The plugin

QGIS → **Plugins → Manage and Install Plugins → Install from ZIP** →
`equipop_qgis-1.29.5.zip` → Install. **Restart QGIS.**

### 3. Confirm both halves moved

QGIS Python Console:

```python
import equipop; print("package:", equipop.__version__); import equipop_qgis; print("plugin:", equipop_qgis.__version__)
```

Both must read **1.29.5**. If only one moved, stop and say so.

If the package still reads 1.29.3, pip installed into a different
Python than QGIS uses. This prints the right one:

```python
import sys, os; print(os.path.join(sys.prefix, "python.exe"))
```

### 4. Pro

Open the **Python Command Prompt** that ships with ArcGIS Pro and
install the same wheel the way you installed equipop there originally,
adding `--force-reinstall --no-deps`. Then point Pro at `EquiPop.pyt`.

### Rolling back

```
python -m pip install --force-reinstall --no-deps equipop==1.29.3
```

and install the 1.29.3 plugin zip from ZIP again.

---

## What to test

### Test 1 — self-potential *(already passed on 1.29.4's build)*

You have done this one and the numbers matched to nine decimals. Worth
one repeat only to confirm nothing moved in the renumbering: **Counts
and Shares**, cell size **1000**, k **400**, self-potential **1** then
**0**. Rows in dense cells should read `Dist_400 = 302.11...` and
`0` respectively; `N_`, `T_` and `R_` identical between the two.

### Test 2 — the boxes that bit you *(new)*

The thing that cost you a run now refuses instead of going quiet.

- **2 ▸ TREATMENT POPULATION** = `one column per group, counts inside (fill 2a)`
- leave everything under it empty → **Run**

It should **refuse**, naming box 2a. Then fill **2a ▸ group count
fields** = `LowInc` and it should run, giving `T_LowInc_` and `R_LowInc_`.

Notice the boxes have moved: **2a is now the group count fields**, and
the type-field boxes are 2b/2c/2d. Each rung names its own box.

Then the other half: with rung 1 chosen and 2a filled, also fill **2b**
(the type field). The Log tab should say box 2b is **IGNORED**.

Machine 2 got the same treatment — **Value Statistics** with the
reference population on `only selected types` and box 1b empty should
refuse, where before it silently did nothing.

### Test 3 — the statistics menu *(new)*

**Value Statistics → 2a ▸ measures.** It should now offer eleven:
mean, median, gini, sd, variance, se, min, max, count, sum, range.
It used to offer six. Tick `variance` and confirm a variance column
arrives.

### Test 4 — the icon *(new)*

**Plugins → Manage and Install Plugins**, find EquiPop. It should have
an icon now rather than a blank square. Tell me if it reads badly at
that size — it is easy to redraw.

### Test 5 — the self-calibrating bandwidth, **Pro only**

This is the one that cannot be seen from QGIS, because QGIS has no such
box (BACKLOG 102).

**Counts and Shares** in Pro, under **Neighbourhood**:

- **k** = `100`
- **distance decay** = negative exponential
- **"OR: self-calibrating - use each point's own Dist_k as its half-life"** = `100`
- **Self-potential** = `0`

Read the messages. Expect a `[decay] WARNING:` naming a count and a
percentage of rows given the median bandwidth. Then run again with
**Self-potential = 1** — the warning should shrink sharply or vanish,
and the bandwidth range should start much lower.

**Those two message blocks side by side are the most valuable thing you
can send back.**

### Test 6 — the population field, in your own data *(new, and the important one)*

This is the defect the external review found, and it has been in every
published release since 1.21.

**Counts and Shares**, with a reference population restricted by type:

- **1 ▸ REFERENCE POPULATION** = `only selected types, with a count field (fill 1a, 1b and 1c)`
- **1a ▸ count field** = a real population column, not all ones
- **1b ▸ type field** and **1c** = pick a subset of types
- **1d ▸ rows whose type is NOT included** = `give them results, counting as zero`

Run. Then run again with **1d** = `leave their results Null`.

**The `N_` values for the included rows must be identical between the
two runs.** Before this release the second run threw away your
population field and counted every row as one person. If you have any
saved output from a run that used "leave their results Null", it is
wrong and worth redoing.

### Test 7 — a cell size of zero

Type `0` into the cell size box. It should now **refuse and say why**,
where before it silently used 100 m.

### Test 8 — the stub audit *(BACKLOG 80, and always yours)*

From the OSGeo4W Shell, in the repository folder:

```
python tools/stub_audit.py
```

It now explains itself if run in the wrong place instead of throwing a
traceback. Record the result in the MANUAL validation row.

---

## What to send back

1. Whether Test 6 gives identical `N_` values on both routes — this
   matters more than everything else here.
2. Whether Test 2 refuses as described, and whether the new box order
   reads better than the old one.
3. The measures list from Test 3.
4. The two Pro message blocks from Test 5.
5. The stub audit result.
6. Anything that read oddly, however small.

All of the output as it comes, please, rather than the part that looks
relevant. The useful line is often the one before.
