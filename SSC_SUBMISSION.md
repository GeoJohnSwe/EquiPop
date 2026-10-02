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

## 0. THE ENGINE FLOOR, AND WHY THE ORDER STILL MATTERS ⚠️

`equipop setup` asks pip for **`equipop>=<eqp_min_engine>`** — a
constant in `stata/equipop.ado`, maintained **by hand**, holding *the
oldest engine that satisfies the calls the commands make*. It is
deliberately **not** the ado's own version. `bump_version.py` does not
touch it, and a test fails if it ever does.

So the rule is a floor rule, not a release rule:

> **Raise `eqp_min_engine` only when the commands start calling
> something new, and only after that engine is on PyPI.**

Keep to that and the hard failure is impossible: the floor can never
name an engine that does not exist. When you do raise it, say in the
comment beside it *which call* forced the change — the comment carries
the list, newest requirement last.

**The order still matters, for a second and separate reason.** Much of
what an SSC release fixes lives in the engine, not the commands:
`equipop doctor`'s entire report comes from `equipop/doctor.py`, and
the ado only calls `from equipop.doctor import run`. Ship a doctor
correction as an ado update and **nothing the reporter can see
changes** — they run the new commands against their old engine, read
the same message, and reasonably conclude it was not fixed.

So: **PyPI first, then SSC**, every time. Before emailing Baum:

```
pip index versions equipop            # newest on PyPI
grep 'local eqp_min_engine' stata/equipop.ado
```

PyPI's newest must be **at least** the floor. And if the release fixes
anything in `equipop/`, publish it before the email or the fix does
not exist for the person who asked for it.

*History: until 1.49.3 the floor WAS the ado's version, so 1.49.2 —
which touched only the ArcGIS toolbox — silently raised the Stata
engine requirement, and any release reaching SSC ahead of PyPI made
`equipop setup` fail outright with "No matching distribution found".
If that does somehow happen again, setup now recognises its own floor
in pip's message and says the mistake is ours rather than sending the
user to check their network. BACKLOG 331 and 332.*

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

Note that block 0 used to check the engine version for **equality**
with the release the pass was written for, which fails on a correct
SSC installation: `equipop setup` asks pip for `equipop>=<version>`,
so the engine is normally *ahead* of the archive. It now checks that
the engine is at least that version and says so when it is newer.
Same correction in `equipop doctor` — see BACKLOG 330.

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
equipop_example.do       ancillary — the short round trip
equipop_showcase.do      ancillary — every function, with expected numbers
equipop_test_data.dta    ancillary — what both of those run on
```

**Every filename carries the `equipop` prefix, including the `.do` and
the `.dta`.** Learned the hard way on the first submission, from
Baum's reply:

> We obviously cannot host a file named `example.do` on the archive,
> so I have renamed that file to `equipop_example.do`. Likewise
> `stata_test_data.dta` is not a workable name (as it could be used by
> many package authors), so I renamed that to `equipop_test_data.dta`.

SSC's filename space is **flat and global** — every file from every
package shares it, and a name in use cannot be reused. So a generic
name is not a style preference, it is a name the archive cannot take,
and the repository now uses his names so that one file has one name
everywhere. A test enforces the prefix on everything in `stata/`.

Two consequences worth knowing before the next submission:

- **A renamed data file breaks the do-files that `use` it.** Both
  sample do-files opened with `use stata_test_data, clear`, which
  could not work once the file was renamed on the archive. They now
  locate it with `findfile`, which also fixes the separate problem
  that ancillary files install into Stata's PLUS folder and not into
  the user's working directory — so `use equipop_test_data` would not
  have found it even under the right name.
- **Ancillary files need `g`, not `f`, in `equipop.pkg`.** They were
  in neither for eleven releases, so `net install` from GitHub gave
  the commands without the examples while SSC — whose `.pkg` is
  generated by the archive, from whatever was in the zip — gave both.
  Two install routes offering different files.

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
