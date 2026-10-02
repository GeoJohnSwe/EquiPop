# EquiPop 1.51.0 — the complete tree

This archive is the whole repository at 1.51.0, in the folder structure
you keep in `C:\Data\EQP\ForGit\`. Unzip it over your copy, or unzip it
beside and diff. 1342 tests pass.

Nothing here is published yet. **Release order, which is now a written
precondition (BACKLOG 331/332): PyPI first, then SSC.**

```
cd C:\Data\EQP\ForGit
python -m build
twine check dist\equipop-1.51.0*
twine upload dist\equipop-1.51.0*
git add -A && git commit && git push
```

Then confirm with `pip index versions equipop`, run `equipop setup` and
`equipop doctor` in Stata, and only then email Baum with the SSC batch.

## What is in it since the last thing you uploaded (1.49.1)

| version | contents |
|---|---|
| 1.49.2 | A CSV input can really become a feature class in ArcGIS Pro — the capability had never existed, only the refusal. |
| 1.49.3 | SSC. Three places called a correct install a fault; the engine floor stopped being a release number; the help's SMCL had been malformed since the generator was written. |
| 1.50.0 | Run provenance, taken from the engine's own arguments. A `no_door` entry in the reachability matrix can now fail. The published test dataset describes itself. |
| 1.51.0 | Marina's four findings, folded in rather than merged — see below. |

## Marina's pull request

All four findings were real and reproduced here. Her fixes for the
radius-only crash and the `replace` decay outputs were taken as they
stand. Her radius diagnosis was right and the remedy is different:
`equipop/labels.py` is one formatter used by the engine *and* by the
field-name prediction, instead of refusing the radius from inside the
engine. **Her PR also caught a bug 1.50.0 shipped** — the `.pkg` used
`g` where `f` was correct, so three files would not have installed.

**Her fixes are now in 1.51.0, not in a 1.49.2 of their own**, so the
version number is not claimed twice. The PR still needs a reply; the
assessment I sent earlier has a draft, with two things left for you:
whether to adopt her `CHANGELOG.md`, and asking her for the
`set varabbrev off` run, which is the one SSC check still open.

## If you want to check my work rather than trust it

```
python -m pytest -q                 # 1342 passed, 19 skipped
python tools/bump_version.py --check 1.51.0
```

Radius names, which is what changed most: every radius anybody has used
keeps the name it had — 50, 100, 500, 800, 2800 are untouched. What
changed is `r(100.5)` → `N_r100_5` rather than the illegal `N_r100.5`,
and `r(1000000)` → `N_r1000000` rather than `N_r1e+06`.
