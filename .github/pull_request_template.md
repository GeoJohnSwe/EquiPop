<!-- Answer each heading; "none" is an answer, an empty heading is not.
     CONTRIBUTING.md section 4 says how a change gets in. -->

## What this solves
<!-- the problem, in a sentence or two; the issue or BACKLOG number -->

## Numbers that change
<!-- which outputs, in which doors, by how much (measured, not guessed);
     or "none". A change to a method rule needs a method-decision issue
     and a RULINGS.md entry - see RULINGS.md. -->

## Runs that now stop
<!-- what a user ran before and is now refused; or "none" -->

## Doors affected
- [ ] Python engine / API
- [ ] QGIS plugin
- [ ] ArcGIS Pro toolbox
- [ ] Stata
- [ ] documents / teaching only

## Tested
- [ ] a test that fails without this change (broken on purpose, seen red)
- [ ] the full suite locally, or CI green
- [ ] in a real program where it matters: QGIS ___ / ArcGIS Pro ___ / Stata ___ (version, OS)

## Written down
- [ ] BACKLOG entry
- [ ] MANUAL row (if released)
- [ ] RULINGS.md (if a method rule was made or changed)
- [ ] help texts regenerated (`python tools/make_sthlp.py`) if a Stata option changed
