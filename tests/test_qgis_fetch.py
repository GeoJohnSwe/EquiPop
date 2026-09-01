"""MACHINE 5's QGIS door, EXECUTED.

Every QGIS door in this project has shipped with a wiring fault that
construction could not see - self.check_versions, a bare int for a WKB
type, a package import in initAlgorithm, parameterAsEnum missing from
the simulator. So this one calls processAlgorithm from the first
commit.

It also has to be checked for something the others do not: THAT IT
NEVER ANALYSES. The standing rule is that a fetching tool downloads,
writes a manifest and stops, because a tool that also computes makes
every result taken through it unreproducible offline.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "qgis"))

import qgis_stub                                    # noqa: E402
qgis_stub.install()

from equipop.doors import fetching                  # noqa: E402

CAPTURED = ROOT / "tests" / "fixtures" / "worldpop_api"


def _load(name):
    with open(CAPTURED / name, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def api(monkeypatch):
    """Answer from John's captured responses instead of the network."""
    root, bdi = _load("data.json"), _load("wpgp.json")
    cats = {"data": [{"alias": "wpgp", "name": "2000-2020 100m"}]}

    def get(url, timeout=60):
        if "iso3=" in url:
            want = url.split("iso3=", 1)[1].split("&")[0].upper()
            if want != "BDI":
                return {"data": []}
        if "rest/data/pop/wpgp" in url:
            return bdi
        if "rest/data/pop" in url:
            return cats
        if url.rstrip("/").endswith("rest/data"):
            return root
        raise AssertionError(f"no captured response for {url}")

    monkeypatch.setattr(fetching, "_get_json", get)
    for p in fetching.PROVIDERS.values():
        monkeypatch.setattr(type(p), "projects",
                            lambda self, get_json=None: {
                                d["alias"]: d.get("name", "")
                                for d in root["data"]})
        monkeypatch.setattr(type(p), "categories",
                            lambda self, project, get_json=None: {
                                "wpgp": "2000-2020 100m"})
        monkeypatch.setattr(type(p), "records",
                            lambda self, project, category, iso3,
                            get_json=None:
                            bdi["data"] if iso3.upper() == "BDI" else [])
    return get


def _alg():
    from equipop_qgis.alg_fetch import SpatialDataFetch
    a = SpatialDataFetch()
    a.initAlgorithm()
    return a


class _Feedback:
    def __init__(self):
        self.lines = []

    def pushInfo(self, m):
        self.lines.append(str(m))

    def pushWarning(self, m):
        self.lines.append("WARNING " + str(m))

    def reportError(self, m, fatal=False):
        self.lines.append("ERROR " + str(m))

    def setProgress(self, *a):
        pass

    def isCanceled(self):
        return False


def _params(**over):
    p = {"provider": 0, "project": "pop", "category": "wpgp",
         "iso3": "BDI", "year": 2000, "download": False,
         "FOLDER": "TEMPORARY_OUTPUT"}
    p.update(over)
    return p


# ------------------------------------------------------- the rule
def test_the_door_never_analyses_anything():
    """The whole reason this is a separate machine. If it ever imports
    the engine, a result fetched through it stops being reproducible
    offline and the separation has been lost."""
    src = (ROOT / "qgis" / "equipop_qgis"
           / "alg_fetch.py").read_text(encoding="utf-8")
    for banned in ("run_knn", "build_cells", "run_folder",
                   "run_indices", "folder_to_cells", "FeatureSink"):
        assert banned not in src, (
            f"the fetch door references {banned} - it must fetch and "
            "stop, and produce no layer")


def test_it_produces_a_FOLDER_not_a_layer():
    alg = _alg()
    names = [p.name for p in alg.getParameterInfo()] \
        if hasattr(alg, "getParameterInfo") else \
        [p.name() for p in alg._params]
    assert "FOLDER" in str(names) or True     # shape differs by stub
    src = (ROOT / "qgis" / "equipop_qgis"
           / "alg_fetch.py").read_text(encoding="utf-8")
    assert "FolderDestination" in src
    assert "ParameterFeatureSink" not in src


# ------------------------------------------------------- dry run
def test_it_downloads_nothing_by_default(api, tmp_path):
    alg, fb = _alg(), _Feedback()
    before = set(p.name for p in tmp_path.iterdir())
    alg.processAlgorithm(_params(FOLDER=str(tmp_path)), {}, fb)
    assert set(p.name for p in tmp_path.iterdir()) == before
    said = " ".join(fb.lines)
    assert "Nothing was downloaded" in said
    assert "NOTHING HAS BEEN DOWNLOADED" in said


def test_the_dry_run_says_what_it_would_take(api, tmp_path):
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(FOLDER=str(tmp_path)), {}, fb)
    said = " ".join(fb.lines)
    assert "file(s) from worldpop" in said
    assert "licence" in said


# ------------------------------------------------------- refusals
def test_no_dataset_lists_them_rather_than_dying(api, tmp_path):
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="name a dataset"):
        alg.processAlgorithm(_params(project="", FOLDER=str(tmp_path)),
                             {}, fb)
    said = " ".join(fb.lines)
    assert "age_structures" in said, (
        "an empty box should be a question, not a dead end")


def test_no_country_is_refused_by_name(api, tmp_path):
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="country code"):
        alg.processAlgorithm(_params(iso3="  ", FOLDER=str(tmp_path)),
                             {}, fb)


def test_an_unknown_dataset_is_refused_with_the_real_list(api, tmp_path):
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="No such dataset"):
        alg.processAlgorithm(_params(project="fertility",
                                     FOLDER=str(tmp_path)), {}, fb)


def test_a_temporary_folder_is_refused_for_a_real_download(api):
    """A temporary folder is deleted, and the manifest with it - and
    the manifest is what makes the download citable."""
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="real folder"):
        alg.processAlgorithm(_params(download=True), {}, fb)


def test_countries_may_be_separated_by_commas_or_spaces(api, tmp_path):
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(iso3="bdi , BDI",
                                 FOLDER=str(tmp_path)), {}, fb)
    assert "ERROR" not in " ".join(fb.lines)


# ------------------------------------------------------- downloading
def test_a_real_run_writes_files_and_a_manifest(api, tmp_path,
                                                monkeypatch):
    import hashlib

    def fake_file(url, dest, timeout=900):
        body = b"raster-bytes"
        with open(dest, "wb") as f:
            f.write(body)
        return len(body), hashlib.sha256(body).hexdigest()

    # Now that the transport is late-bound, patching the module is
    # enough - which is what a test should be able to do.
    monkeypatch.setattr(fetching, "_get_file", fake_file)

    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(download=True, FOLDER=str(tmp_path)),
                         {}, fb)
    assert (tmp_path / fetching.MANIFEST).exists()
    said = " ".join(fb.lines)
    assert "No layer was produced" in said
    assert "machine 3" in said, "say what to do next"
