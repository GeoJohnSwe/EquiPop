# -*- coding: utf-8 -*-
"""
alg_fetch.py - MACHINE 5's QGIS door: bring data in, and STOP.

THE STANDING RULE, HANDOVER 13 section 3c. This tool downloads into a
folder, writes a manifest, and ends. It produces NO LAYER, on purpose:
the moment a fetching tool also analyses, every result computed
through it stops being reproducible offline.

So the output is a FOLDER, not a feature sink - which is unusual for a
Processing algorithm and is the point. Machine 3 reads that folder
afterwards, exactly as it reads any other.

AND IT ASKS BEFORE IT ACTS. "Download" is off by default. Run it once
to see what WOULD be fetched - how many files, from where, under which
licence - and only then tick the box. The download leg has never run
in EquiPop's development environment, because every WorldPop host is
blocked there, so the first thing a user meets must be inspectable.
"""
from qgis.core import (QgsProcessingException,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString)

from .base import EquipopAlgorithm

# Written down, not read from the package: getParameterInfo runs while
# QGIS builds the dialog, and the plugin must still LOAD when equipop
# is absent (BACKLOG 218, which this door would otherwise repeat). A
# test pins this against the package's own list.
PROVIDER_NAMES = ["worldpop"]


class SpatialDataFetch(EquipopAlgorithm):
    """Fetch data into a folder, with a manifest. Analyses nothing."""

    EQP_TOOL = "SpatialDataFetch"

    def name(self):
        return "spatialdatafetch"

    def displayName(self):
        return "5. Fetch data (downloads only, analyses nothing)"

    def initAlgorithm(self, config=None):
        self.add(QgsProcessingParameterEnum(
            "provider", "1a. Where from",
            options=list(PROVIDER_NAMES), defaultValue=0))
        self.add(QgsProcessingParameterString(
            "project", "1b. Dataset, e.g. age_structures, pop, births "
                       "(leave blank to list them)",
            optional=True))
        self.add(QgsProcessingParameterString(
            "category", "1c. Which version of it, e.g. "
                        "G2_CN_Age_R25A_1km (blank lists the choices)",
            optional=True))
        self.add(QgsProcessingParameterString(
            "iso3", "1d. Countries, space separated, e.g. BDI RWA"))
        self.add(QgsProcessingParameterNumber(
            "year", "1e. Year (blank takes every year the release "
                    "covers - R2025A spans 2015-2030, so that is a "
                    "lot of files)",
            type=QgsProcessingParameterNumber.Integer,
            optional=True, minValue=1900, maxValue=2100))
        self.add(QgsProcessingParameterBoolean(
            "download", "2a. DOWNLOAD. Leave unticked to see what "
                        "would be fetched without fetching it",
            defaultValue=False))
        self.add(QgsProcessingParameterFolderDestination(
            "FOLDER", "Folder to fetch into"))

    # -----------------------------------------------------------------
    def processAlgorithm(self, parameters, context, feedback):
        from equipop.doors.fetching import (FetchError, plan_fetch,
                                            run_fetch)

        from .base import check_versions

        ch = self.channel(feedback)
        check_versions(ch)

        provider = PROVIDER_NAMES[
            self.parameterAsEnum(parameters, "provider", context)]
        project = (self.parameterAsString(parameters, "project",
                                          context) or "").strip()
        category = (self.parameterAsString(parameters, "category",
                                           context) or "").strip()
        iso3 = [c.strip().upper() for c in
                (self.parameterAsString(parameters, "iso3", context)
                 or "").replace(",", " ").split() if c.strip()]
        year = self.parameterAsInt(parameters, "year", context) or None
        download = self.parameterAsBool(parameters, "download", context)
        folder = self.parameterAsString(parameters, "FOLDER", context)

        if not project:
            self._show_datasets(provider, ch)
            raise QgsProcessingException(
                "Box 1b: name a dataset. The available ones are listed "
                "in the log above.")
        if not iso3:
            raise QgsProcessingException(
                "Box 1d: give at least one country code, such as BDI.")

        try:
            plan = plan_fetch(provider, project=project,
                              category=category or None, iso3=iso3,
                              year=year, say=ch.info,
                              will_download=download)
        except FetchError as exc:
            # The spine refuses in plain words, and its refusals carry
            # the list of valid choices. Do not add to them.
            raise QgsProcessingException(str(exc))

        if not download:
            ch.info("")
            ch.info("Nothing was downloaded. Tick box 2a to fetch "
                    "these files, then point machine 3 at the folder.")
            return {"FOLDER": folder}

        if not folder or folder.upper() == "TEMPORARY_OUTPUT":
            raise QgsProcessingException(
                "Choose a real folder to fetch into. A temporary one "
                "would be deleted, and the manifest with it - and the "
                "manifest is what makes the download citable.")
        try:
            run_fetch(plan, folder, say=ch.info)
        except FetchError as exc:
            raise QgsProcessingException(str(exc))
        except Exception as exc:
            raise QgsProcessingException(
                f"The download failed: {type(exc).__name__}: {exc}. "
                "Nothing partial was kept. If this is a network error "
                "the request never reached the provider - try the URL "
                "in a browser.")

        ch.info("")
        ch.info("No layer was produced, and that is deliberate: a tool "
                "that both downloads and analyses makes every result "
                "computed through it unreproducible offline. Run "
                "machine 3 on this folder next.")
        return {"FOLDER": folder}

    # -----------------------------------------------------------------
    def _show_datasets(self, provider, ch):
        """List what is on offer, so an empty box is a question rather
        than a dead end."""
        try:
            from equipop.doors.fetching import PROVIDERS
            for k, v in sorted(PROVIDERS[provider].projects().items()):
                ch.info(f"   {k:24s} {v}")
        except Exception as exc:                     # network, mostly
            ch.warning(f"Could not reach {provider} to list its "
                       f"datasets: {exc}")
