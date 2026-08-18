# EquiPop for Stata

`equipop` builds a bespoke neighbourhood around every point in your
data — the nearest *k* people, rather than the administrative area the
point happens to fall in — and writes what that neighbourhood contains
back into your dataset as new variables.

**This is the only current Stata document besides `help equipop`.**
Anything in `stata/historical/` describes a command that no longer
exists and must not be followed.

---

## 1. Install

Two halves, and **both are needed**. The `.ado` files come from GitHub;
the calculating engine is a Python package, and only `pip` can put it
where Stata will find it. Updating one without the other gives
`ImportError: cannot import name ...`, which looks like a bug in
EquiPop and is not.

**[Stata]**
```stata
net install equipop, from("https://raw.githubusercontent.com/GeoJohnSwe/EquiPop/main/stata") replace
```

**[Stata]** — the engine, into the Python that Stata is actually using
```stata
equipop setup
```

Then **quit Stata completely and start it again.** Python starts once
per Stata session and keeps whatever it loaded first.

## 2. If anything goes wrong, ask the command

**[Stata]**
```stata
equipop doctor
```

It reports which Python Stata is using, which processor that Python is
built for, and the state of every library it needs — present, absent,
or installed but refusing to load. Send that output when reporting a
problem; it answers most questions before they are asked.

### Two known environment failures

**Stata closes when you run something.** This is not a crash in
EquiPop — the window disappears before EquiPop is reached. It happens
when Stata is pointed at an Anaconda Python: Anaconda and Stata each
carry the same maths library, and two copies in one process is fatal.
**Do not point Stata at an Anaconda or Miniconda environment.** Install
a plain Python from python.org, used by Stata and nothing else, and
point Stata at it:

**[Stata]**
```stata
python set exec "PASTE_THE_REAL_PATH_HERE", permanently
```

**A library will not load, and the message mentions an incompatible
architecture.** The package was built for a different processor than
your Python — common on Apple Silicon Macs, where an Intel build sits
in the user folder. `equipop doctor` names this case, and the repair
is one line:

**[Stata]**
```stata
equipop setup, repair
```

then quit Stata and start it again.

## 3. A first run

Your data needs one row per place, with coordinates and a population
count.

**[Stata]**
```stata
equipop [fweight=pop], x(X) y(Y) treat(minority) k(25 50)
```

This adds, for each *k*:

| variable | meaning |
|---|---|
| `N_25` | people in the neighbourhood |
| `Dist_25` | radius needed to reach them |
| `T_minority_25` | people of that group inside it |
| `R_minority_25` | their share of it |

### If your coordinates are longitude and latitude

Add `project`. Distances measured on degrees are not distances — a
degree of longitude is shorter than a degree of latitude everywhere
except the equator — so the *k* nearest neighbours come out wrong.

**[Stata]**
```stata
equipop [fweight=pop], x(lon) y(lat) treat(minority) k(25) project
```

The run reports which projection it used and returns it in `r(epsg)`
and `r(crs)`. If your data is already projected, leave this off.

### What `treat()` contains

By default `treat()` holds the **number of people** of the group at
each point, which is how census and register data normally arrive.
That needs a population, from `pop()` or `[fweight=]`.

If instead your treatment variable is a 0/1 marker on a weighted row,
say so:

**[Stata]**
```stata
equipop [fweight=pop], x(X) y(Y) treat(is_minority) k(25) treatmode(flags)
```

Getting this wrong cannot pass silently. A group larger than the
population containing it is refused, with a message naming which
setting to use.

## 4. Everything else

**[Stata]**
```stata
help equipop
```

The help is generated from the same source the command is built from,
so it cannot drift away from what the command actually accepts.

## 5. Reporting a problem

Send three things: the output of `equipop doctor`, the exact command
line you ran, and the full text of what Stata printed. Then say what
changed between a run that worked and one that did not — that question
resolves more reports than any other.
