# 16. EquiPop inside Stata

## The idea

Many researchers live in Stata: the data sits in Stata's memory,
the regressions run there, the co-authors expect do-files. EquiPop
respects that. Rather than asking you to export your data to
Python, run something, and import results back — three chances to
make a mistake — the toolbox reaches *into* Stata. Since version 17,
Stata has been able to talk to Python directly, and EquiPop uses
that channel so your data **never leaves Stata's memory**: a
command reads the coordinate columns, hands them across the bridge,
computes, and returns the results as ordinary new variables, row by
row, ready for `regress` on the very next line. A person whose
coordinates were missing simply gets missing results, exactly as
Stata users expect.

Two commands exist. The first, `equipop_knn`, is the original and
does one thing well: nearest-neighbour counts and shares (the
material of chapters 1 and 4). The second, `equipop_run`, is the
whole toolbox behind one door: an `engine()` option chooses among
counts, value statistics, river-and-hill effort, and the labour-
market competition analysis of chapter 13 — whose outputs A and J
arrive as regression-ready variables, which is precisely how the
accompanying journal work uses them.

## Cook it

One-time setup: tell Stata which Python to use (`python query`
shows the current one) and make sure EquiPop is installed in *that*
Python with `pip install equipop`. Then, with the ado-files from
the repository's `stata/` folder on your adopath:

```stata
* nearest-neighbour shares, two definitions from chapter 4's menu:
equipop_run, engine(counts) x(X) y(Y) treat(HighEdu) ///
    k(200) r(500) replace

* the income statistics of chapter 6, among each person's 400 nearest:
equipop_run, engine(stats) x(X) y(Y) values(Income) ///
    stats(mean gini) k(400) replace

* chapter 13's competition analysis - your data in memory is the
* demand side; the supply (jobs) comes from a file on disk:
equipop_run, engine(fca) x(X) y(Y) demandvar(Workers) ///
    supply("C:\data\jobs.csv") supplycol(Jobs) halflife(3000) replace
regress health_outcome A
```

Reading the last block: every row of your dataset is a worker; the
jobs file provides the workplaces; `halflife(3000)` says a job
three kilometres away counts half; and after the command, two new
variables exist in your data — `A`, the competition-adjusted jobs
per worker at each person's location, and `J`, the competition-
blind potential — so the regression on the next line is not a
metaphor but the actual workflow.

## The dials

Each engine has the options of its chapter: `treat()` for group
variables, `values()` and `stats()` for the statistics engine,
`dem()` and `roundtrip` for terrain effort, `tau()` for effort
isochrones, and the fca options shown above. `replace` overwrites
result variables from an earlier run — without it, the command
politely refuses to destroy anything.

## Under the hood

Both commands are thin: perhaps forty lines of glue whose only job
is moving arrays across the bridge. All mathematics lives in the
Python package, where the automatic test suite covers it — and the
glue itself was validated by running its code, word for word,
against a simulated Stata before shipping. The practical
consequence: when something fails, it is almost always the
environment (Stata pointing at a different Python than the one
where EquiPop was installed) rather than the computation, and
`python query` is the first thing to check.

## Pitfalls

The one genuine trap is having several Pythons on one machine —
Anaconda's, the system's, one inside a project — and installing
EquiPop in a different one than Stata talks to. The symptom is
"module not found" even though `pip install` reported success. The
cure is mechanical: `python query` in Stata shows the path Stata
uses; run `pip install equipop` with *that* Python. Everything else
is ordinary Stata life.
