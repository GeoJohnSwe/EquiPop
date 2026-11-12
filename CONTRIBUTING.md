# Working on EquiPop

**For anyone changing the code, the documents or the teaching material.**
Read this first, then [RULINGS.md](RULINGS.md), the method decisions you must not change by accident.
*Written 12 November 2026, at 1.64.1.*

---

## 1. How the code is laid out

EquiPop is **one engine with four doors**. A number is computed once, in the engine; each door only collects the question in its own program and shows the answer.

| Folder | What it is |
|---|---|
| `equipop/` | The engine: k-nearest neighbourhoods, counts and shares, value statistics, friction and slope, FCA, LISA, demography. **This is also the Python door**: `import equipop`. |
| `equipop/doors/` | Logic the doors share: dropdown wordings (`rungs.py`), help texts (`help.py`), result field names (`fields.py`), typed numbers (`numbers.py`). **A decision two doors make lives here, once.** |
| `equipop/stata_bridge.py` | `dispatch()`: the one entry point the GIS doors and Stata call. |
| `qgis/equipop_qgis/` | The QGIS plugin (QGIS 3.38 to 4.x). |
| `arcgis/EquiPop.pyt` | The ArcGIS Pro toolbox. |
| `stata/` | The Stata commands. The `.sthlp` help files are **generated**: edit `tools/make_sthlp.py`, never the `.sthlp`. |
| `tests/` | The test suite (about 2,900 tests). It runs anywhere, using three stand-ins for programs CI cannot have: `tests/qgis_stub.py` (PyQGIS), `tests/test_arcgis_stub.py` (arcpy), `tests/stata_sim.py` (Stata's Python interface). |
| `tests_real_qgis/` | The plugin run inside a **real** QGIS, numbers compared with the engine's. |
| `tools/` | Release tools: version bump, help generator, bundle builder. |
| `docs/book/` | The teaching book. |

## 2. Set up and run the tests

```
git clone https://github.com/GeoCalista/EquiPop
cd equipop
python -m venv .venv
.venv\Scripts\activate          (Windows)   or   source .venv/bin/activate
python -m pip install -e ".[test,geo,io]" matplotlib
python -m pytest -q -p no:cacheprovider tests        (about 6 minutes)
```

`-e` installs the checkout itself, so a change takes effect without reinstalling. Run one file while working (`python -m pytest tests/test_wstats.py`), and the whole suite before you open a pull request.

**In a real QGIS** (optional locally; CI always does it). With [micromamba](https://mamba.readthedocs.io) or conda:

```
micromamba create -n qgis -c conda-forge qgis pytest pandas scipy pyproj
micromamba activate qgis
QT_QPA_PLATFORM=offscreen python -m pytest tests_real_qgis     (Windows: set QT_QPA_PLATFORM=offscreen first)
```

**ArcGIS Pro and Stata** cannot run on CI: both need a licence. The stand-ins cover what they can, and every release gets a short list of hand checks, kept in its row of MANUAL.md.

## 3. Automatic tests

`.github/workflows/tests.yml` runs on every pull request and every push to `main`. Results are on the pull request and in the repository's **Actions** tab.

| Job | Question it answers |
|---|---|
| **suite** | Does the full suite pass on Windows and Linux on Python 3.11 and 3.14, and on macOS on 3.14? (Python 3.15 runs too, but does not block: its packages lag.) If GitHub has no Mac free ("not acquired by Runner"), re-run the job; it is not a test failure. |
| **qgis** | Does the plugin run in a real QGIS: 3.38 (the oldest we promise), 3.44 (LTR) and 4.x on Linux, and 4.x on Windows? |
| **bundle** | Can a complete release be built from this commit? Its files are a **download** on the run's page for 14 days. Use that download for the hand checks in Pro and Stata. |

A red check is a stop: fix it, or say in the pull request why it is not yours. Which checks **block** a merge is set under *Settings → Rules*: start with the Linux suite and Linux QGIS, and add the others once they have run green.

## 4. How a change gets in

1. **Start from an issue**, or open one. Anything that can move a number starts as a **method decision** issue (template provided): the rule today, the rule proposed, an example, and which numbers change.
2. **Work on a branch** from `main`: `fix/empty-group-columns`, `docs/teaching-week-3`. Nobody pushes to `main` directly, the maintainers included.
3. **Open a pull request early**, as a draft if unfinished. The template asks what problem it solves, what numbers change, which doors are affected, and what was tested where.
4. **Review.** Checks green and one approving review. A change to a method rule also needs the method lead (John). Releases, packaging and credentials need two approvals.
5. **Merge** with *Squash and merge*, and delete the branch.

## 5. House rules

Each was learned from a fault that reached users. The number is the BACKLOG entry.

1. **Every fix comes with a test that fails without it.** Break the fix on purpose and watch the test go red. If it stays green, the test is not testing the fix (BACKLOG 406).
2. **Say what moves.** Every pull request and every MANUAL row states *Numbers that change* and *Runs that now stop*. "None" is an answer; silence is not.
3. **Read RULINGS.md before changing a rule**, and read where the rule was laid down before proposing to change it (484).
4. **Refuse, don't ignore.** A box or option that would do nothing stops the run with one sentence naming it. An option that is accepted and dropped gives a wrong analysis a clean log (486, 490).
5. **Decide from what the user asked, not from what the data holds.** Faults have come from inferring a choice from what a field happened to hold (485, 488).
6. **One rule, one place.** If two doors need it, it goes in `equipop/doors/`. Copies drift; the crossing-ring arithmetic in five copies is the standing example (38, 320, 483).
7. **Speak the door's language.** A message names the box or the option the user sees, never an engine argument (305).
8. **A stand-in must be stricter than the real program, never kinder.** When a stand-in and the real program differ, fix the stand-in first, then the code (80, 288).
9. **Stata's Python blocks**: no backticks, no `$`, no backslashes, and nothing heavy imported at the top. Stata expands macros on every line and runs the block when it loads the command (459, 460). After changing a Stata option, run `python tools/make_sthlp.py`.
10. **Dead code is deleted, not commented out.** Git remembers it.
11. **Never commit a credential.** Tokens live in your own user folder (`.pypirc`) or a keyring, never in the repository, a chat or a screenshot.

## 6. Releases

Today John makes the releases. The steps, in order:

1. `python tools/bump_version.py X.Y.Z`, then `python tools/make_sthlp.py`.
2. A new row in MANUAL.md's version table and the BACKLOG entries for the release. Update the stamps at the top of TEACHING.md and PROPOSALS.md.
3. The full suite green, and the CI run green.
4. `bash tools/make_bundle.sh X.Y.Z <folder outside the repository>`, or take CI's bundle download.
5. The hand checks in the MANUAL row: ArcGIS Pro and Stata on Windows, Stata on macOS.
6. **PyPI, with no token:** on GitHub, *Releases → Draft a new release*, a new tag `vX.Y.Z` (exactly the version in `pyproject.toml`), *Publish release*. The `release` workflow checks the tag, builds, tests the wheel, and waits for a maintainer to approve the upload (*Actions → the release run → Review deployments*). Then the QGIS plugin repository, and SSC by email.

**Version numbers.** A correction is a patch release (1.63.8), even when it moves a number. A ruling or a new capability starts a minor release (1.64.0), and HANDOVER_15.md must then say so; a test checks.

## 7. Where things are written down

| File | What it holds |
|---|---|
| `RULINGS.md` | Method decisions in force: what the code must do and why. |
| `BACKLOG.md` | Every finding and change, numbered, newest first. A number is never reused. |
| `MANUAL.md` | The user manual, and one row per release saying what changed. |
| `HANDOVER_15.md` | Notes from one working session to the next. Its section 0 is the latest. |
| `TEACHING.md`, `PROPOSALS.md` | What each release means for courses and for funding texts. |
| `CITATION.cff` | How to cite EquiPop. |

## 8. AI-assisted work

Much of EquiPop was written with an AI assistant, and that will continue. Its work follows the same rules as anyone's: a test for every fix, a review, and the numbers that change stated. The person who opens the pull request answers for it. Name the assistant in the commit (a `Co-Authored-By:` line), so the history shows how a change was made.
