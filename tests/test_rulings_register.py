# -*- coding: utf-8 -*-
"""RULINGS.md keeps its own rules (BACKLOG 495).

The register is only useful if it can be trusted: an index that lists
what is there, statuses from a fixed list, sources that exist, and
tests under "Pinned by" that exist. A ruling pinned by a test that was
renamed or deleted is a ruling nothing guards - so a rename fails here.
"""
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = open(os.path.join(ROOT, "RULINGS.md"), encoding="utf-8").read()
BACKLOG = open(os.path.join(ROOT, "BACKLOG.md"), encoding="utf-8").read()

STATUSES = ("In force, not yet built", "In force", "Ruled out",
            "Superseded by R-", "On ice", "To confirm")
FIELDS = ("Rule", "Why", "Source", "Pinned by", "Status")


def _entries():
    parts = re.split(r"^### (R-\d\d) · (.+)$", TEXT, flags=re.M)
    out = []
    for i in range(1, len(parts), 3):
        rid, title, body = parts[i], parts[i + 1].strip(), parts[i + 2]
        body = body.split("\n## ")[0]
        fields = {m.group(1): m.group(2).strip() for m in re.finditer(
            r"^\*\*(Rule|Why|Source|Pinned by|Status)\.\*\*(.*)$", body,
            flags=re.M)}
        out.append((rid, title, fields, body))
    return out


def _index():
    rows = re.findall(r"^\| (R-\d\d) \| (.+?) \| (.+?) \|$", TEXT, flags=re.M)
    return {rid: (title.strip(), status.strip()) for rid, title, status in rows}


ENTRIES = _entries()
IDS = [rid for rid, _, _, _ in ENTRIES]


def _status_word(text):
    for s in STATUSES:
        if text.startswith(s):
            return s
    return None


def test_ids_are_unique_and_never_skip():
    """A number is never reused or renumbered; the next one is next."""
    assert IDS, "no rulings found - has the heading format changed?"
    assert len(IDS) == len(set(IDS))
    assert IDS == [f"R-{n:02d}" for n in range(1, len(IDS) + 1)]


def test_the_index_lists_every_ruling_as_written():
    index = _index()
    assert sorted(index) == sorted(IDS)
    for rid, title, fields, _ in ENTRIES:
        assert index[rid][0] == title, f"{rid}: index title differs"
        assert _status_word(index[rid][1]) == _status_word(
            fields["Status"]), f"{rid}: index status differs"


@pytest.mark.parametrize("rid,title,fields,body", ENTRIES, ids=IDS)
def test_every_ruling_has_its_five_fields(rid, title, fields, body):
    missing = [f for f in FIELDS if f not in fields]
    assert not missing, f"{rid} lacks {missing}"
    assert _status_word(fields["Status"]), (
        f"{rid}: status must start with one of {STATUSES}")


@pytest.mark.parametrize("rid,title,fields,body", ENTRIES, ids=IDS)
def test_the_sources_exist(rid, title, fields, body):
    src = fields["Source"]
    for group in re.findall(r"BACKLOG ((?:\d+[a-z]?(?: \([^)]*\))?(?:, )?)+)",
                            src):
        for n in re.findall(r"\b(\d+[a-z]?)\b(?![^(]*\))", group):
            assert re.search(rf"^\s*- (?:~~)?{n}(?:~~)? \|", BACKLOG,
                             flags=re.M), f"{rid}: BACKLOG {n} not found"
    # the handovers live in the repository, not in the source archive
    if any(f.startswith("HANDOVER_") for f in os.listdir(ROOT)):
        for h in re.findall(r"HANDOVER_(\d+)", src):
            assert os.path.exists(os.path.join(ROOT, f"HANDOVER_{h}.md")), (
                f"{rid}: HANDOVER_{h}.md not found")
    assert "BACKLOG" in src or "HANDOVER" in src, (
        f"{rid}: say where it was decided")


@pytest.mark.parametrize("rid,title,fields,body", ENTRIES, ids=IDS)
def test_the_pinning_tests_exist(rid, title, fields, body):
    """BROKEN WITH: a pinning test renamed or deleted."""
    pins = re.findall(r"`([\w/]+\.py)::(\w+)`", fields["Pinned by"])
    if not pins:
        assert fields["Pinned by"].startswith("none yet"), (
            f"{rid}: name a test as `path::function`, or write 'none yet'")
    for path, func in pins:
        full = os.path.join(ROOT, path)
        assert os.path.exists(full), f"{rid}: {path} does not exist"
        src = open(full, encoding="utf-8").read()
        assert re.search(rf"^def {func}\(", src, flags=re.M), (
            f"{rid}: {path} has no test {func}")


def test_a_superseded_ruling_points_at_one_that_exists():
    for rid, _, fields, _ in ENTRIES:
        for target in re.findall(r"Superseded by (R-\d\d)", fields["Status"]):
            assert target in IDS and target != rid


def test_the_guide_and_the_templates_point_here():
    """New contributors find the register from the guide, and a method
    decision ends in it."""
    if not os.path.isdir(os.path.join(ROOT, ".github")):
        pytest.skip("a source archive: .github/ lives in the repository")
    guide = open(os.path.join(ROOT, "CONTRIBUTING.md"), encoding="utf-8").read()
    issue = open(os.path.join(ROOT, ".github", "ISSUE_TEMPLATE",
                              "method-decision.md"), encoding="utf-8").read()
    pr = open(os.path.join(ROOT, ".github", "pull_request_template.md"),
              encoding="utf-8").read()
    for text in (guide, issue, pr):
        assert "RULINGS.md" in text
