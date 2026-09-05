"""BACKLOG 258 — provider definitions as DATA, not code.

John's idea: "what if the site specific instructions could be
separated from the tool - so that if the user is running an old tool
and it doesn't work - just retrieving site specific instructions from
GIT would be enough."

The evidence for it is in this project's own history. BACKLOG 211: the
WorldPop naming registry was written from four sample files and failed
on all 120 of John's real ones. It was data baked into code, so fixing
it cost a release, a build, a PyPI upload and three host installs.

Most of what follows guards RULE ONE, which is not negotiable: a
definition is data and may never contain code. EquiPop is installed
inside QGIS and ArcGIS Pro; a tool that executed instructions fetched
over the network would be a remote code execution hole in a research
instrument.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from equipop.doors.fetching import FetchError, PROVIDERS, plan_fetch
from equipop.doors.registry import (BUNDLED, RegistryError, load_one,
                                    load_registry)


def _write(tmp, name, spec):
    p = Path(tmp) / name
    p.write_text(json.dumps(spec), encoding="utf-8")
    return p


def _ok_spec(**over):
    spec = {
        "provider": "demo",
        "label": "A demo",
        "registry_version": "2026-01-01",
        "licence": "CC-BY 4.0",
        "may_redistribute": True,
        "share_alike": False,
        "url": "https://example.org/{product}/{year}.tif",
        "fields": [
            {"name": "product", "label": "Layer", "required": True,
             "options": ["POP", "BUILT"]},
            {"name": "year", "label": "Year", "required": True,
             "options": ["2020", "2025"]},
        ],
    }
    spec.update(over)
    return spec


# ------------------------------------------------- RULE ONE: no code
@pytest.mark.parametrize("poison", [
    {"url": "https://x/{product}/__import__.tif"},
    {"label": "import os"},
    {"licence": "eval(1)"},
    {"label": "lambda x: x"},
    {"citation": "subprocess.run"},
])
def test_anything_resembling_code_is_refused(tmp_path, poison):
    p = _write(tmp_path, "demo.json", _ok_spec(**poison))
    with pytest.raises(RegistryError, match="not allowed|may never"):
        load_one(p)


def test_the_refusal_says_why_a_definition_is_data(tmp_path):
    p = _write(tmp_path, "demo.json", _ok_spec(label="import this"))
    with pytest.raises(RegistryError) as e:
        load_one(p)
    assert "DATA" in str(e.value)


def test_no_bundled_definition_contains_code():
    """The rule applies to what ships, not only to what is loaded."""
    for path in BUNDLED.glob("*.json"):
        load_one(path)          # raises if it does


# ------------------------------------------------------- validation
def test_a_definition_without_a_url_is_refused(tmp_path):
    spec = _ok_spec()
    del spec["url"]
    with pytest.raises(RegistryError, match="needs provider, fields"):
        load_one(_write(tmp_path, "d.json", spec))


def test_a_url_naming_an_undeclared_field_is_refused(tmp_path):
    spec = _ok_spec(url="https://x/{product}/{nonesuch}.tif")
    with pytest.raises(RegistryError, match="no field declares it"):
        load_one(_write(tmp_path, "d.json", spec))


def test_broken_json_says_so_rather_than_crashing(tmp_path):
    p = Path(tmp_path) / "bad.json"
    p.write_text("{ not json", encoding="utf-8")
    with pytest.raises(RegistryError, match="not valid JSON"):
        load_one(p)


def test_one_bad_definition_does_not_stop_the_others(tmp_path):
    _write(tmp_path, "good.json", _ok_spec())
    (Path(tmp_path) / "bad.json").write_text("{ nope", encoding="utf-8")
    said = []
    got = load_registry(tmp_path, say=said.append)
    assert "demo" in got, "the good one must still load"
    assert any("bad.json" in s for s in said), "and the bad one is named"


# ---------------------------------------------------- GHSL, for real
def test_ghsl_is_loaded_from_the_bundled_definition():
    assert "ghsl" in PROVIDERS
    assert "worldpop" in PROVIDERS, "code adapters still work"


def test_ghsl_builds_the_url_confirmed_against_the_real_server():
    """Confirmed 2026-09-02 against
    jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/
    """
    plan = plan_fetch("ghsl", product="POP", year="2020",
                      say=lambda m: None)
    url = plan["entries"][0]["url"]
    assert url == (
        "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/"
        "GHS_POP_GLOBE_R2023A/GHS_POP_E2020_GLOBE_R2023A_4326_30ss/"
        "V1-0/GHS_POP_E2020_GLOBE_R2023A_4326_30ss_V1_0.zip"), url


def test_ghsl_defaults_to_WGS84_so_it_can_share_a_folder_with_worldpop():
    """54009 is Mollweide and WorldPop is 4326. A mixed-CRS folder is
    REFUSED by the loader (BACKLOG 239), so the default must be the
    one that can be combined."""
    plan = plan_fetch("ghsl", product="POP", year="2020",
                      say=lambda m: None)
    assert "_4326_" in plan["entries"][0]["url"]


def test_ghsl_carries_its_provenance_and_its_obligations():
    e = plan_fetch("ghsl", product="POP", year="2020",
                   say=lambda m: None)["entries"][0]
    assert e["doi"].startswith("10.2905/")
    assert "Schiavina" in e["citation"]
    assert e["may_redistribute"] is True
    assert e["share_alike"] is False
    assert e["registry_version"] == "2026-09-05"


def test_a_different_product_carries_a_different_doi():
    a = plan_fetch("ghsl", product="POP", year="2020",
                   say=lambda m: None)["entries"][0]
    b = plan_fetch("ghsl", product="BUILT_S", year="2020",
                   say=lambda m: None)["entries"][0]
    assert a["doi"] != b["doi"]


def test_a_year_is_a_year_and_not_an_index():
    # the field is now called , not  - John was told the
    # setting was "Year" and typed year, and the key disagreed
    """The numbering convenience read '2020' as 'the 2020th option'
    and refused it as out of range. If the value IS one of the
    choices, it is the choice."""
    plan = plan_fetch("ghsl", product="POP", year="2020",
                      say=lambda m: None)
    assert "E2020" in plan["entries"][0]["url"]


def test_an_impossible_year_is_still_refused():
    with pytest.raises(FetchError):
        plan_fetch("ghsl", product="POP", year="1066",
                   say=lambda m: None)


def test_the_registry_version_reaches_the_manifest(tmp_path):
    """RULE THREE: without it, a fetch is unreproducible in a NEW way
    - which rules were in force when this ran?"""
    import hashlib

    from equipop.doors.fetching import run_fetch

    def fake(url, dest, timeout=900):
        with open(dest, "wb") as f:
            f.write(b"x")
        return 1, hashlib.sha256(b"x").hexdigest()

    plan = plan_fetch("ghsl", product="POP", year="2020",
                      say=lambda m: None)
    man = run_fetch(plan, str(tmp_path), get_file=fake,
                    say=lambda m: None)
    assert man["registry_version"] == "2026-09-05"
    assert man["files"][0]["registry_version"] == "2026-09-05"
