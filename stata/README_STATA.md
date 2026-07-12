# EquiPop from Stata (17+)

One-time setup: in Stata run `python query` to see which Python Stata
uses. Point it at the environment where equipop is installed (or will
be): `python set exec "C:\...\anaconda3\envs\equipop\python.exe", perm`
then, in a terminal for that environment, `pip install equipop`.

Per session: put `equipop_knn.ado` somewhere on the adopath (the
example.do adds the current folder). Then:

    equipop_knn, x(X_local) y(Y_local) treat(HighEdu) k(50 200) unit(100)

adds N_50, Dist_50, T_HighEdu_50, R_HighEdu_50 (etc.) as ordinary
variables in the dataset in memory - regress immediately, modify data,
rerun with `replace`, regress again. Options: `weight(varname)` when a
row represents more than one person; `unit(#)` grid size in metres.

Rows with missing coordinates receive missing results (and a note).
Coordinates must be METRIC (project first if in lat/long).

HONESTY NOTE: the computational core (equipop.stata_bridge) is fully
tested by the package's pytest suite; the ~25 sfi glue lines inside the
ado can only be exercised inside Stata and await your first run. If
anything errors, the message text plus `python query` output is enough
to diagnose.
