# Submitting EquiPop to SSC

From C. F. Baum's submission page (repec.org/bocode/s/sscsubmit.html,
rev. 2 May 2022) checked against this package.

---

## Already satisfied

| requirement | EquiPop |
|---|---|
| every ado declares `version n.n` | **yes** — all three say `version 17` |
| help as `.sthlp`, not `.hlp` (v10+) | **yes** — `equipop.sthlp` |
| command names strictly lower case | **yes** |
| not a reserved graphics word | **yes** — none of `color`, `axis`, `style`… |
| documented with a help file | **yes**, and every option is tested against it |

---

## To do before sending — in order

### 1. Check the name is free ⚠️ do this first

Filenames on SSC **must be unique**; a name in use cannot be reused.
In Stata:

```
which equipop
ssc type equipop.ado
ssc describe equipop
```

Any response other than your own file means the name is taken and
everything below changes. Repeat for `equipop_knn` and `equipop_run`
— **all three ado names must be free, not just the package name.**

### 2. Test with variable abbreviation off

Baum singles this out: *"Many errors in user-written programs can be
traced to the assumption that users will allow varabbrev."*

```
set varabbrev off
do equipop_test_pass.do
```

All 57 checks must still pass. Nothing in the repository tests this
today, so it is a genuine unknown.

### 3. Decide what to say about the Python dependency

**This is the unusual part of the submission and the thing most
likely to generate Statalist traffic.** Almost every SSC package is
pure Stata. EquiPop needs Stata 17+ with Python configured, plus
numpy, scipy, pandas and pyproj.

The archive does not forbid it, and the submission form has a place
for dependencies — but it is written for *"my ado needs Tom Jones'
bar.ado"*, not for a PyPI stack. So:

- the abstract must say so in its first two lines, not in the help
- the help must open with the prerequisite and `equipop setup`
- expect questions; answer them on Statalist, not by email

### 4. Do NOT send a .pkg file

Baum: *"It is not necessary nor desirable to generate a Stata-format
package (.pkg) file, since the SSC archive software generates the
package file automatically."*

`stata/equipop.pkg` stays in the repository for `net install` from
GitHub. **Leave it out of the zip.**

### 5. Build the zip

Just the Stata materials — no Python package, no plugins, no tests:

```
equipop.ado
equipop_knn.ado
equipop_run.ado
equipop.sthlp
equipop_showcase.do      (optional, as the sample do-file)
```

### 6. Write the abstract

Two things Baum asks for: a **title line** and an **abstract** for the
listing. Draft:

> **EQUIPOP: Stata module for individualised k-nearest-neighbour
> population statistics**
>
> equipop computes measures over the k nearest people to each
> observation rather than over administrative areas, so results carry
> no boundary effects and are comparable across places and over time.
> Counts, shares, distances, distance decay, value statistics
> (median, Gini, variance, percentiles) and segregation profiles are
> supported, with optional barriers and terrain. Requires Stata 17 or
> later with Python configured; the calculating engine installs with
> `equipop setup`.

### 7. Email it

To **baum@bc.edu**, with the zip attached, stating:

- that this is a **new** submission
- suggested package name: `equipop`
- the title line and abstract above
- that it requires Python and how it is obtained
- your affiliation and email for the RePEc record

### 8. After it appears

Usually available a day after Baum updates the archive. Then announce
on **Statalist** — customary, and how people find it.

---

## Two things worth deciding first

**The version on SSC and the version on PyPI will drift.** SSC holds
the ado files; PyPI holds the engine. A user with old ados and a new
engine, or the reverse, is the failure mode this project already
guards against with `equipop doctor`. Make sure the ado's declared
contract version and the doctor's mismatch message are current
**before** submitting, because SSC updates are manual and slower than
`pip install -U`.

**Submit only when a version is stable.** Every SSC update is an email
to a person. That is a good reason to submit rarely and to treat an
SSC release as more final than a PyPI one.
