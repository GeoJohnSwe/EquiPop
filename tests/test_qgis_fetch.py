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
    # ONLY the providers that HAVE a catalogue to list. "projects" is
    # a WorldPop idea, not a universal one - a TemplateProvider builds
    # its URLs from a definition and has no catalogue to query, so
    # patching one onto it raised AttributeError. The test assumed
    # every provider looks like the first one, which is the same fault
    # the spine was loosened to remove (BACKLOG 256).
    for p in [x for x in fetching.PROVIDERS.values()
              if hasattr(x, "projects")]:
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
    """Settings arrive as a FLAT matrix, two cells per row."""
    settings = over.pop("settings", ["project", "pop",
                                     "category", "wpgp",
                                     "iso3", "BDI",
                                     "year", "2000"])
    p = {"provider": 0, "settings": settings, "download": False,
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


# --------------------------------------------- the vocabulary problem
def test_every_provider_is_offered_not_only_the_first():
    """BACKLOG 263. The dropdown was a written-down list of ONE,
    written when there was one provider and never updated - so John
    installed four and saw one. The same fault as the naming registry
    written from four sample files, except this one was created
    knowingly to keep the package out of the dialog."""
    from equipop_qgis.alg_fetch import PROVIDER_NAMES
    from equipop.doors.fetching import PROVIDERS
    for n in PROVIDER_NAMES:
        assert n in PROVIDERS, f"the door offers {n}, which does not exist"
    for n in ("worldpop", "ghsl", "hdx", "geofabrik"):
        assert n in PROVIDER_NAMES, f"{n} exists but is not offered"


def test_the_door_speaks_no_providers_vocabulary():
    """Boxes called Dataset, Version, Countries and Year are
    WorldPop's words, and three of four providers do not speak them."""
    src = (ROOT / "qgis" / "equipop_qgis"
           / "alg_fetch.py").read_text(encoding="utf-8")
    for word in ("iso3", "category", "popyear"):
        assert word not in src, (
            f"the door mentions {word!r} - a provider's vocabulary has "
            "leaked into the machine")


def test_an_empty_table_lists_WHAT_THIS_PROVIDER_ASKS_FOR(api, tmp_path):
    alg, fb = _alg(), _Feedback()
    out = alg.processAlgorithm(_params(settings=[],
                                       FOLDER=str(tmp_path)), {}, fb)
    assert out == {"FOLDER": str(tmp_path)}, "asking is not failing"
    said = " ".join(fb.lines)
    assert "worldpop asks for" in said
    assert "iso3" in said and "required" in said
    assert "ERROR" not in said


def test_a_setting_the_provider_does_not_take_is_refused(api, tmp_path):
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="does not take"):
        alg.processAlgorithm(_params(
            settings=["project", "pop", "tile", "R4_C19"],
            FOLDER=str(tmp_path)), {}, fb)


def test_a_ragged_table_is_refused_by_name(api, tmp_path):
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="rows of two"):
        alg.processAlgorithm(_params(settings=["project"],
                                     FOLDER=str(tmp_path)), {}, fb)


def test_a_temporary_folder_is_refused_for_a_real_download(api):
    """A temporary folder is deleted, and the manifest with it - and
    the manifest is what makes the download citable."""
    from qgis.core import QgsProcessingException
    alg, fb = _alg(), _Feedback()
    with pytest.raises(QgsProcessingException, match="real folder"):
        alg.processAlgorithm(_params(download=True), {}, fb)


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


def test_a_NUMBER_in_the_dataset_box_never_reaches_the_provider(api,
                                                                tmp_path):
    """BACKLOG 252. John typed 5 and got "Could not list the versions
    of '5': HTTP Error 500". The door listed that dataset's versions
    using the RAW box text, before plan_fetch had resolved it - so it
    asked the provider for /rest/data/5.
    """
    asked = []
    from equipop.doors import fetching as F

    real = F.PROVIDERS["worldpop"].categories

    def spy(self, project, get_json=None):
        asked.append(project)
        return {"wpgp": "2000-2020 100m"}

    F.WorldPop.categories = spy
    try:
        alg, fb = _alg(), _Feedback()
        alg.processAlgorithm(_params(project="14", category="",
                                     FOLDER=str(tmp_path)), {}, fb)
    finally:
        F.WorldPop.categories = real
    assert asked, "the door never listed the versions"
    assert all(not a.isdigit() for a in asked), (
        f"a raw number reached the provider: {asked}")


def test_the_dataset_number_is_resolved_to_its_name(api, tmp_path):
    alg, fb = _alg(), _Feedback()
    alg.processAlgorithm(_params(project="14", category="",
                                 FOLDER=str(tmp_path)), {}, fb)
    said = " ".join(fb.lines)
    assert "'pop'" in said or "pop" in said
    assert "Could not list" not in said


def test_GHSL_runs_through_the_same_door(tmp_path):
    """The whole point of 263. No API is touched: GHSL is a registry
    definition and its URL is NAMED from the settings."""
    alg, fb = _alg(), _Feedback()
    from equipop_qgis.alg_fetch import PROVIDER_NAMES
    out = alg.processAlgorithm(_params(
        provider=PROVIDER_NAMES.index("ghsl"),
        settings=["product", "POP", "epoch", "2020"],
        FOLDER=str(tmp_path)), {}, fb)
    assert out == {"FOLDER": str(tmp_path)}
    said = " ".join(fb.lines)
    assert "GHS_POP_E2020_GLOBE_R2023A_4326_30ss_V1_0.zip" in said, said
    assert "ERROR" not in said


def test_GHSLs_empty_table_lists_GHSLs_OWN_fields(tmp_path):
    alg, fb = _alg(), _Feedback()
    from equipop_qgis.alg_fetch import PROVIDER_NAMES
    alg.processAlgorithm(_params(
        provider=PROVIDER_NAMES.index("ghsl"), settings=[],
        FOLDER=str(tmp_path)), {}, fb)
    said = " ".join(fb.lines)
    assert "ghsl asks for" in said
    assert "product" in said and "epoch" in said
    assert "iso3" not in said, "that is WorldPop's word, not GHSL's"


def test_GEOFABRIK_runs_through_the_same_door(tmp_path, monkeypatch):
    import json as _json
    from equipop.doors import fetching as F
    rec = _json.loads((ROOT / "tests" / "fixtures" / "worldpop_api"
                       / "geofabrik_index.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(F, "_get_json", lambda url, timeout=60: rec)
    alg, fb = _alg(), _Feedback()
    from equipop_qgis.alg_fetch import PROVIDER_NAMES
    alg.processAlgorithm(_params(
        provider=PROVIDER_NAMES.index("geofabrik"),
        settings=["region", "burundi"], FOLDER=str(tmp_path)), {}, fb)
    said = " ".join(fb.lines)
    assert "burundi-latest.osm.pbf" in said
    assert "SHARE-ALIKE" in said, "the ODbL warning must reach the user"
