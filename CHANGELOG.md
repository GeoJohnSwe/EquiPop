# Changelog

Earlier history lives in `git log`/`git tag` (one tag per released version,
back to v1.5.1), not reconstructed here. This file starts with the first
release it was added for.

## 1.48.3

- Fixed: a decimal radius (e.g. `r(1.5)`) crashed with an uncaught Python
  traceback (`ValueError: invalid varname`) instead of a clean error. The
  radius label `f"r{r:g}"` could contain a literal `.`, which is not a
  legal character in a Stata variable name. Output variable names are now
  sanitized (`.` -> `_`) at the point they are handed to Stata, matching
  the `.ado`'s own existing `subinstr "." "_"` convention for radius
  suffixes. Internal lookups into the computed results are unaffected -
  only the final Stata-facing name changes.
- Known, deliberately unresolved: for radii small or large enough that
  Python's `:g` formatting falls back to scientific notation (e.g.
  `1e-05`), the resulting label still contains a character (`-`) that is
  not legal in a Stata variable name, and two distinct radii that agree
  to `:g`'s six significant digits would still produce the same label.
  Both are a separate, lower-priority issue from the one fixed here.
