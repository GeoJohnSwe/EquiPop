# Changelog

Earlier history lives in `git log`/`git tag` (one tag per released version,
back to v1.5.1), not reconstructed here. This file starts with the first
release it was added for.

## 1.48.3

- Fixed (`equipop.ado`): a radius-only call combined with `treat()`
  crashed (`invalid numlist has too few elements`) because a
  name-length warning looped over `k()`'s numlist even when `k()` was
  never given. The loop is now skipped when `k()` is empty, matching
  the guard already used everywhere else in the file for exactly this
  situation.
- Fixed (`equipop.ado`): `replace` did not clear previously-created
  decay-mode output variables (`ND_`, `TD_`, `RD_` prefixes), so
  repeating a `decay()` call with `replace` failed, telling the user to
  "use option replace" even though they already had. The existing
  `k()`/`r()` cleanup block now also drops the matching decay outputs
  when `decay()` is given.
- Fixed (`equipop/stata_bridge.py`, `knn_to_rows` and `_map_back`): a
  decimal radius (e.g. `r(1.5)`) crashed with an uncaught Python
  traceback (`ValueError: invalid varname`) instead of a clean error.
  The radius label `f"r{r:g}"` could contain a literal `.`, which is
  not a legal character in a Stata variable name. Output variable names
  are now sanitized (`.` -> `_`) at the point they are handed to Stata,
  matching the `.ado`'s own existing `subinstr "." "_"` convention for
  radius suffixes. Internal lookups into the computed results are
  unaffected - only the final Stata-facing name changes.
  `equipop_run.ado` already sanitized its own output names
  independently and was never actually crashable this way; the
  `_map_back` change is consistency/defense-in-depth, not a fix for an
  observed failure there.
- Fixed (`equipop.sthlp`): examples used variables (`X_local`,
  `HighEdu`, etc.) without ever loading the dataset they match
  (`stata_test_data.dta`, shipped alongside `example.do`); a nonexistent
  `half()` option in two examples (the real option is `halflife()`);
  `selfpot(0)` described as excluding the origin from its own
  neighbourhood, which is what `originrule(exclude)` does, not
  `selfpot()`; `overshoot(sampled)` listed as a normal choice without
  noting it is not available in Stata; and a reference to
  `TESTING_STATA.md`, renamed to `README_STATA.md` before v1.36.
- Known, deliberately unresolved: for radii small or large enough that
  Python's `:g` formatting falls back to scientific notation (e.g.
  `1e-05`), the resulting label still contains a character (`-`) that is
  not legal in a Stata variable name, and two distinct radii that agree
  to `:g`'s six significant digits would still produce the same label.
  Both are a separate, lower-priority issue from the ones fixed here.
- Fixed (`equipop.pkg`): `example.do` and `stata_test_data.dta` were
  missing from the package's `f` lines, so a plain `ssc install equipop`
  would not have actually fetched the files the help file's Examples
  section tells users to use. Added both.
- Not fixed here, pushing this branch/tag to a GitHub fork does not by
  itself update SSC. Users who already have an earlier version
  installed via `ssc install equipop` keep that version until a real
  SSC update is submitted and distributed - that is a separate step
  from anything in this repository.
