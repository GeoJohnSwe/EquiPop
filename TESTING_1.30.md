# Testing 1.30 before you publish it

**1.30 CHANGES NUMBERS.** Every k-based number EquiPop has ever
produced moves, unless you set one box back. That is the release, not
a side effect — so most of this manual is about seeing the change and
proving you can undo it.

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
python -m pip install --force-reinstall --no-deps equipop-1.30-py3-none-any.whl
```

**`--no-deps` matters.** Without it, `--force-reinstall` also
reinstalls pandas, numpy, scipy and pyproj — the four libraries QGIS
itself is built on. You already have them; they should not be touched.

### 2. The plugin

QGIS → **Plugins → Manage and Install Plugins → Install from ZIP** →
`equipop_qgis-1.30.zip` → Install. **Restart QGIS.**

### 3. Confirm both halves moved

QGIS Python Console (it compiles a paste as ONE statement, hence the
semicolons):

```python
import equipop; print("package:", equipop.__version__); import equipop_qgis; print("plugin:", equipop_qgis.__version__)
```

Both must read **1.30**. If only one moved, stop and say so.

### 4. ArcGIS Pro

Copy `arcgis/EquiPop.pyt` and BOTH `.pyt.xml` files together — the XML
files are the help pages and they have been regenerated for this
release. Install the package into Pro's Python as before.

---

## The new box

Both machines, both doors, gain **"The ring that crosses k"** with
three choices. In QGIS it is under **Advanced parameters**; in Pro it
is in the **Neighbourhood** section, because it changes every k-based
number and burying it seemed wrong.

| choice | what it does |
|---|---|
| **whole ring** | every cell at that distance — what EquiPop did before 1.30 |
| **proportional share** | each cell gives the same fraction, so N_k is exactly k — **the default in machine 1** |
| **sampled, seeded** | whole cells one at a time until k is reached — the original 2014 C# method |

Machine 2 (Value Statistics) defaults to **whole ring** instead, and
says so on every run. That is not an oversight: a quarter of a
boundary cell has no median, no percentile and no Gini.

---

## Test 1 — the point of the release, on your own data

Run **Counts and Shares** on a dataset you know, with a **small k**
(k=25 or k=50 — the effect is largest at small k and at boundaries).
Run it three times, changing only the new box:

1. whole ring
2. proportional share
3. sampled, seeded — put **1848** in the Seed box

**What to check:**

- Under **proportional**, `N_k` should be **exactly k in every row**.
  Sort the column and look at the top and bottom.
- Under **whole**, `N_k` is k or more, sometimes much more.
- Under **sampled**, `N_k` is k or more but never as far past it as
  whole, and it is always a whole number of people.
- `R_k` — the share — is where the difference matters. Look at cells
  on a boundary between two areas. That is where I expect the largest
  disagreement, and it is the thing you raised the item for.

**Please report:** the maximum `N_k` under whole against k, and
whether the `R_k` differences look right to you where you know the
geography. Your eye on a real boundary is worth more than any test I
can write here.

## Test 2 — the way back

Set the box to **whole ring** and run the same job you ran under
1.29.9.

**Every number must be identical.** Not close — identical. If
anything differs, that is a defect in this release and I want to know
before anything else.

## Test 3 — the seed actually seeds

With **sampled, seeded**:

1. Run with the Seed box **empty**. The messages must say
   `no seed given; drew NNNNN. Enter that number to repeat this exact
   run.`
2. Run again with that number typed into the Seed box. The messages
   must say `sampled order from seed NNNNN`, and **the results must be
   identical to run 1**.
3. Run with a different seed. `N_k` may differ in some rows — that is
   the mode working, not a fault.

This is the box QGIS has never had, and Pro's Value Statistics has
never had. It is untested outside the simulator.

## Test 4 — machine 2 says the machines differ

Run **Value Statistics** on anything. The messages must carry one
line beginning `[overshoot]` that names the mode it used and says
Counts and Shares defaults to a different one.

Then set machine 2's box to **proportional share** deliberately. It
must **refuse**, naming median/percentile/Gini and saying nothing was
computed. It must not produce numbers.

**Is that one line worth it, or is it noise?** It fires on every
machine-2 run. You said it was the right call; I would still like
your eye on it once it is in front of you.

## Test 5 — the run manifest

After any Pro run, open the `..._EquiPop_run.csv` beside the output.

It should now carry rows that were **missing from every manifest
before this release**: `overshoot`, `overshoot_seed`,
`self_potential`, `reference_rung`, `treatment_rung`,
`reference_count_field`, `rows_outside_reference` and
`source_analysed`.

This is BACKLOG 148, which was marked done in 1.29.6 and was not —
the argument existed and nothing ever passed it. If two of your runs
ever disagree again, this file should now be enough to tell us why.

## Test 6 — the stub audit (BACKLOG 80)

In a live QGIS Python Console, as every release that touches the QGIS
door:

```
python tools/stub_audit.py
```

I cannot run this. Result goes in the MANUAL validation row.

## Test 7 — carried over, still unfinished

From 1.29.5's manual, never completed: **the population field
surviving both keepoutside routes, run into two FRESH feature classes
in a geodatabase.** Everything else from that round passed.

---

## What I have NOT verified

Said plainly, because it is the part that matters:

- **Nothing in 1.30 has been run in a real QGIS or a real Pro.** The
  simulator proves the wiring and the arithmetic; it cannot prove a
  dropdown reads well or that Pro places the box where I think it
  does.
- **`sampled` has never run on real data through either door.** The
  within-ring order is seeded and order-independent by construction,
  and that is tested — but on a simulator.
- The two doors are proved to agree under all three modes on the
  teaching town, and against two shipped answer keys. They have not
  been compared on your data.
