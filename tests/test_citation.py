"""CITATION.cff must be valid CFF, not merely valid YAML.

BACKLOG 233. John edited this file in the GitHub browser - which is
the right way to add a paper and needs no tools - and the result
parsed as YAML while being INVALID CFF in two ways:

  type: presentation   is not in the CFF 1.2.0 enum at all
  conference: "..."    conference is an ENTITY, like location, and
                       cannot be a bare string

Neither shows up as an error anywhere. GitHub simply stops rendering
the "Cite this repository" button, and nobody notices until somebody
tries to cite the software. So the suite checks the schema, not just
the syntax.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CFF = ROOT / "CITATION.cff"


def _text():
    return CFF.read_text(encoding="utf-8")


def test_the_file_is_there():
    assert CFF.exists(), "the citation file is how the software is cited"


def test_it_is_valid_yaml():
    yaml = pytest.importorskip("yaml")
    assert isinstance(yaml.safe_load(_text()), dict)


def test_it_is_valid_CFF_not_merely_valid_yaml():
    """The check that would have caught John's edit."""
    cffconvert = pytest.importorskip(
        "cffconvert", reason="pip install cffconvert to check the schema")
    from cffconvert import Citation
    Citation(_text()).validate()


def test_every_reference_type_is_in_the_schema():
    """Runs WITHOUT cffconvert, so it protects a bare install too.

    The enum is from CFF 1.2.0. 'presentation' is a natural word and
    is not in it; 'slides' and 'conference-paper' are.
    """
    yaml = pytest.importorskip("yaml")
    allowed = {
        "art", "article", "audiovisual", "bill", "blog", "book",
        "catalogue", "conference", "conference-paper", "data",
        "database", "dictionary", "edited-work", "encyclopedia",
        "film-broadcast", "generic", "government-document", "grant",
        "hearing", "historical-work", "legal-case", "legal-rule",
        "magazine-article", "manual", "map", "multimedia", "music",
        "newspaper-article", "pamphlet", "patent",
        "personal-communication", "proceedings", "report", "serial",
        "slides", "software", "software-code", "software-container",
        "software-executable", "software-virtual-machine",
        "sound-recording", "standard", "statute", "thesis",
        "unpublished", "video", "website",
    }
    d = yaml.safe_load(_text())
    bad = [(r.get("type"), r.get("title", "")[:50])
           for r in d.get("references", [])
           if r.get("type") not in allowed]
    assert not bad, f"reference types not in the CFF schema: {bad}"


def test_conference_and_institution_are_entities_not_strings():
    """CFF models an organisation as an object with a `name`."""
    yaml = pytest.importorskip("yaml")
    d = yaml.safe_load(_text())
    entries = list(d.get("references", []))
    pref = d.get("preferred-citation")
    if pref:
        entries.append(pref)
    for r in entries:
        for key in ("conference", "institution", "location", "publisher"):
            if key in r:
                assert isinstance(r[key], dict), (
                    f"{r.get('title', '?')[:40]}: {key} must be an "
                    f"object with a name, not {r[key]!r}")
                assert "name" in r[key]


def test_the_version_still_matches_the_package():
    """It is the eighth place a version lives. A browser edit is the
    easiest place to get it wrong, so say so loudly."""
    import re
    ver = re.search(r'^version\s*=\s*"([^"]+)"',
                    (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
                    re.M).group(1)
    got = re.search(r"^version:\s*(\S+)", _text(), re.M)
    assert got, "CITATION.cff no longer declares a version"
    assert got.group(1) == ver, (
        f"CITATION.cff says {got.group(1)}, the package says {ver}. "
        "This line moves only when a release is cut - do not edit it "
        "by hand.")


def test_the_software_report_is_still_the_preferred_citation():
    yaml = pytest.importorskip("yaml")
    pref = yaml.safe_load(_text()).get("preferred-citation")
    assert pref and pref["year"] == 2014, (
        "the 2014 report is what people should cite for the software; "
        "it does not move with the version")
