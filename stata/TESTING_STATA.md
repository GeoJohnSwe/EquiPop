# Testing the Stata door — a first run, step by step

Written for v1.35, for someone who works in GIS and has not run the
Stata side in a while. Nothing here needs Python knowledge. Every step
says what to type, what you should see, and what it means if you see
something else.

**Please paste back ALL output of steps 2, 3 and 5, including the
lines that look like noise.** Numbers 2 and 3 are the ones that
usually explain a failure in step 5.

---

## Step 0 — what this is testing, in one paragraph

Stata cannot do k-nearest-neighbour work by itself. The `.ado` file is
a thin wrapper: it reads your variables out of Stata's memory, hands
them to the EquiPop **Python package**, and writes the answers back as
ordinary new variables. So three separate things have to be true —
Stata must be able to find a Python, that Python must have `equipop`
installed in it, and the `.ado` files must be somewhere Stata looks.
Each of the steps below establishes one of those.

---

## Step 1 — get the files

Until `net install` lands (planned for 1.38) this is a manual copy.

Download or clone the repository, and note the full path of the
`stata` folder — everything you need is in it:

```
equipop.ado            the command
equipop_knn.ado        the old name, still works, forwards to equipop
equipop_run.ado        the other engines (stats, friction, slope, fca, lisa)
stata_test_data.dta    the test dataset
```

Say the folder is `C:\Data\EQP\stata`. Substitute your own path
everywhere below.

---

## Step 2 — which Python is Stata using?

In Stata:

```stata
python query
```

**What you should see:** a block of text with a line beginning
`Python system information` and, importantly, a line
`Python executable:` followed by a path such as
`C:\Users\john\anaconda3\envs\equipop\python.exe`.

**Copy that path.** Everything in step 3 happens in *that* Python and
nowhere else — a machine usually has several, and installing into the
wrong one is the single commonest reason this door fails.

**If instead you see** `python: no Python installation found`
(r(9)), Stata has not been pointed at one yet. Install Python 3.10 or
newer, then in Stata:

```stata
python set exec "C:\Users\john\anaconda3\envs\equipop\python.exe", perm
```

and run `python query` again.

---

## Step 3 — is EquiPop installed in *that* Python?

Still in Stata, run this as one line:

```stata
python: import equipop; print("equipop", equipop.__version__)
```

**What you should see:**

```
equipop 1.35
```

**If you see `ModuleNotFoundError: No module named 'equipop'`**, the
package is missing from the Python Stata uses. Open a terminal (not
Stata) and run, using the path from step 2:

```
"C:\Users\john\anaconda3\envs\equipop\python.exe" -m pip install --upgrade equipop
```

Then repeat step 3. Note the `-m pip` form with the full path — it
installs into that exact Python, which a bare `pip` may not.

**If you see a version older than 1.35**, upgrade with the same
command. A version mismatch between the package and the `.ado` is
worth knowing about before anything else is diagnosed.

---

## Step 4 — let Stata find the commands

```stata
adopath + "C:\Data\EQP\stata"
which equipop
```

**What you should see:** the full path to `equipop.ado` and its first
line, which begins `*! equipop v1.35`.

**If you see `command equipop not found`**, the path in `adopath` is
wrong — check for a typo, and check that it points at the folder, not
at the file.

`adopath +` lasts for the session. To make it permanent, put the same
line in your `profile.do`.

---

## Step 5 — the actual run

```stata
use "C:\Data\EQP\stata\stata_test_data.dta", clear
describe
equipop, x(X_local) y(Y_local) treat(HighEdu) k(50 200) unit(100)
summarize N_50 Dist_50 T_HighEdu_50 R_HighEdu_50
```

**What you should see:** a line
`equipop: done - new variables added (N_*, Dist_*, T_*, R_* for k = 50 200 r = )`
and then a summarize table with **eight new variables** in total —
`N_50`, `Dist_50`, `T_HighEdu_50`, `R_HighEdu_50` and the same four
for 200.

How to tell the numbers are sane, without checking anything by hand:

- `N_50` should sit at or just above 50, never below. It is the
  population actually gathered, and it overshoots because the last
  cell added is taken whole or in part rather than split at exactly 50.
- `N_200` should sit at or just above 200, and `Dist_200` should be
  larger than `Dist_50` for essentially every row — you must travel
  further to gather more people.
- `R_HighEdu_50` is a share, so it must lie between 0 and 1. If
  anything falls outside that, stop and send me the summarize table.
- `Dist_50` is in **metres**, because `X_local`/`Y_local` are metric.

---

## Step 6 — the three things most likely to go wrong, and what they mean

**`TypeError: _equipop_machine1() got an unexpected keyword argument`**
The `.ado` and the installed package disagree. Almost always an old
`.ado` on the adopath: run `which equipop` and check it says v1.35.

**`variable N_50 already exists - use option replace`**
Exactly what it says. Re-run with `replace` on the end:

```stata
equipop, x(X_local) y(Y_local) treat(HighEdu) k(50) unit(100) replace
```

**Every result variable is missing (`.`)**
Usually missing or non-numeric coordinates. Check with
`summarize X_local Y_local` — if `Obs` is less than the row count, the
rows with missing coordinates correctly receive missing results.

**`equipop_knn is now called -equipop-`**
Not an error. Old do-files still work; that note is the only change.

---

## Step 7 — the old command, and the other engines

Both of these should still work unchanged:

```stata
equipop_knn, x(X_local) y(Y_local) treat(HighEdu) k(50) unit(100) replace
equipop_run, engine(stats) x(X_local) y(Y_local) values(ValFloat) k(50) unit(100) replace
```

The first prints the rename note and then behaves exactly like
`equipop`. The second is the other door — machine 2 and the remaining
engines — which is untouched by this release.

---

## What is NOT in 1.35, so it is not reported as a fault

These are the next release's work, in this order:

1. the two ladders (reference and treatment population selection),
   `keepoutside`, decay, the overshoot box, the self-potential ladder
   and the missing-value codes — 1.36;
2. lat/long projection, so unprojected coordinates work — 1.37. Until
   then, **coordinates must already be metric**;
3. `.sthlp` help files and `net install` from GitHub — 1.38.

1.35 does one thing: it makes the command run at all, under its new
name, and puts the Stata door inside the test suite for the first
time.
