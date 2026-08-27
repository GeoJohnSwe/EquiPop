# Push rejected — how to pull first

GitHub has a commit you do not. Usually because you edited
`CITATION.cff` in the browser, which commits straight to GitHub.

## The fix

```
git pull --rebase
git push
```

`--rebase` replays your commits on top of GitHub's, so the history
stays a straight line. Without it you get a merge commit that says
nothing.

## If it stops with a conflict

Git names the file. Open it and look for:

```
<<<<<<< HEAD
what GitHub has
=======
what you have
>>>>>>> your commit
```

Delete the three marker lines and leave the text you want — usually
both parts, one after the other. Then:

```
git add <that file>
git rebase --continue
git push
```

## To back out

```
git rebase --abort
```

Returns you to exactly where you were. Nothing is lost, nothing is
pushed.

## Before pushing, always

```
git status
```

Check no `.venv`, `dist`, `build`, `*.egg-info`, `pytest_tmp` or
`EquiPop_runs` folder is listed. `git add -A` takes everything it
sees.

## The habit that avoids this

**Pull before you start, not after you finish.**

```
git pull --rebase
```

as the first thing each session. A browser edit made last week is
then already in your copy.
