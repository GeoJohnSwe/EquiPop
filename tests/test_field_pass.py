"""The field pass is a GUARD, so it needs a guard of its own.

BACKLOG 193. Until 1.40.5 `equipop_test_pass.do` stated its invariants
and did not enforce them: a wrong number printed itself and the run
carried on. The repair is only durable if nothing can quietly undo it,
and nothing in pytest can run Stata. So this file READS the do-file the
way tests/test_stata_ado.py reads the .ado files, and refuses:

  - a block that states an expectation and contains no check;
  - a run that is expected to fail and whose return code is never read;
  - a pinned check count that disagrees with the checks actually in the
    file - the count is what catches a block dying half way, so a stale
    number disarms the whole mechanism;
  - a version stamp that has drifted from pyproject.toml.

PARSE, DO NOT SEARCH (BACKLOG finding 3): the first version of this
parser split the file on its separator lines and reported that every
block was unchecked, because the separator appears twice per block and
the headers and the code landed in different chunks. A probe that has
not been verified against a known-good file is worth nothing.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DO_FILE = ROOT / "equipop_test_pass.do"
PYPROJECT = ROOT / "pyproject.toml"


def _text() -> str:
    return DO_FILE.read_text(encoding="utf-8")


def _code_lines() -> list[str]:
    """Every line that Stata will execute - comments dropped."""
    return [ln for ln in _text().splitlines()
            if not ln.strip().startswith("*")]


def _blocks() -> list[tuple[str, str]]:
    """Return (header, code) for each numbered block.

    The file's shape is: separator, comment header, separator, code.
    Splitting on the separator therefore yields the header and the code
    as SEPARATE chunks, and they have to be paired back up. Getting
    this wrong is what made the first parser report 22 empty blocks.
    """
    sep = re.compile(r"^\* ={10,}\s*$", re.M)
    chunks = sep.split(_text())
    out: list[tuple[str, str]] = []
    for i, chunk in enumerate(chunks):
        head = chunk.lstrip()
        m = re.match(r"\*\s*(\d+[^\n]*)", head)
        if not m:
            continue
        # the code for this header is the chunk that follows it
        code = chunks[i + 1] if i + 1 < len(chunks) else ""
        out.append((m.group(1).strip(), code))
    return out


def test_the_do_file_is_present():
    assert DO_FILE.exists(), "the field pass is part of the release"


def test_the_parser_sees_every_block():
    blocks = _blocks()
    assert len(blocks) >= 20, (
        f"expected the full set of blocks, parsed {len(blocks)}. "
        "If the file's separator style changed, fix this parser before "
        "trusting anything else in this module.")


def test_every_block_enforces_something():
    """A block that says EXPECT and never calls eqpcheck is decoration."""
    silent = [head for head, code in _blocks() if "eqpcheck" not in code]
    assert not silent, (
        "these blocks state an expectation but never check it: " +
        "; ".join(s[:60] for s in silent))


def test_every_expected_refusal_reads_its_return_code():
    """`capture equipop ...` with nobody reading _rc is the old defect.

    A refusal that stops refusing is invisible in the output, because
    the answer still looks like an answer.
    """
    lines = _code_lines()
    bad = []
    for i, ln in enumerate(lines):
        if not re.match(r"\s*capture\s+equipop\b", ln):
            continue
        # the return code must be read within a few lines, before any
        # other command can overwrite it
        window = " ".join(lines[i:i + 6])
        if "_rc" not in window:
            bad.append(ln.strip()[:70])
    assert not bad, (
        "these runs are expected to fail but nothing reads _rc: " +
        "; ".join(bad))


def test_the_pinned_check_count_matches_the_file():
    """The pin is what catches a block dying before its checks run."""
    lines = _code_lines()
    calls = [ln.strip() for ln in lines
             if re.search(r"(^|\s)eqpcheck\s", ln)]
    # error traps fire only when a block has already failed
    traps = [c for c in calls if c.startswith("if `rc' eqpcheck")]
    always = [c for c in calls if c not in traps]
    # the engine-version check is an if/else pair: exactly one fires
    exclusive = [c for c in always if "could not read the engine version" in c]
    expected = len(always) - len(exclusive)

    m = re.search(r"global EQP_EXPECT_CHECKS\s*=\s*(\d+)", _text())
    assert m, "the pass must pin how many checks it expects to run"
    pinned = int(m.group(1))
    assert pinned == expected, (
        f"the file pins {pinned} checks but contains {expected} that "
        f"always fire ({len(traps)} further ones are error traps). "
        "A stale pin disarms the incomplete-run detector.")


def test_the_version_stamp_follows_the_package():
    version = re.search(r'^version\s*=\s*"([^"]+)"',
                        PYPROJECT.read_text(encoding="utf-8"),
                        re.M).group(1)
    txt = _text()
    header = re.search(r"^\*! EquiPop ([0-9][^\s]*)", txt, re.M)
    assert header, "the pass must stamp the version it was written for"
    assert header.group(1) == version, (
        f"the do-file header says {header.group(1)}, pyproject says "
        f"{version}")
    pinned = re.search(r'global EQP_EXPECT\s+"([^"]+)"', txt)
    assert pinned, "the pass must pin the version it checks the engine against"
    assert pinned.group(1) == version, (
        f"EQP_EXPECT is {pinned.group(1)}, pyproject says {version}")


def test_the_data_path_is_not_hard_coded_to_one_machine():
    """Umut runs this on a Mac. A Windows path is a wall, not a default."""
    txt = _text()
    assert not re.search(r'global\s+EQP_DATA\s+"[A-Za-z]:\\', txt), (
        "EQP_DATA must ship empty, not pointing at one person's drive")
    assert 'global EQP_DATA ""' in txt, (
        "EQP_DATA must ship empty so the fallback and the file check run")
    assert "confirm file" in txt, (
        "the pass must say plainly that the data is missing, rather than "
        "failing block by block")


def test_the_pass_ends_with_a_verdict_that_can_fail():
    txt = _text()
    assert "exit 9" in txt, (
        "the pass must end non-zero when a check failed - otherwise it "
        "is back to printing a number and carrying on")
    assert "EQP_BAD" in txt and "EQP_RUN" in txt


def test_block_20_does_not_put_a_continuous_measure_in_treat():
    """ValFloat is a magnitude, not a headcount.

    It reached 23,254 against a population of at most 98, so the
    treatment guard refused it - correctly - and the refusal halted the
    pass before blocks 21 and 22 ever ran.
    """
    txt = _text()
    assert not re.search(r"treat\(ValFloat\)", txt), (
        "ValFloat is continuous; a share needs numerator and denominator "
        "in the same units. It belongs in machine 2, not treat().")


@pytest.mark.parametrize("phrase", [
    "power keeps MORE mass",
    "power's ND_300 is the larger",
])
def test_the_corrected_decay_claim_does_not_come_back(phrase):
    """1.40.5 corrected block 17; the old claim was measured false.

    Both curves are 0.5 at the half-life by construction, so that is
    where they cross: power cuts harder INSIDE the bandwidth and softer
    outside it. Which model keeps more mass therefore depends on where
    the neighbourhood sits, and on this data it sits inside.
    """
    assert phrase not in _text()
