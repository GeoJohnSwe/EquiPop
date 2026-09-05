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
                       QgsProcessingParameterMatrix,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString)

from .base import EquipopAlgorithm

# Written down, not read from the package: getParameterInfo runs while
# QGIS builds the dialog, and the plugin must still LOAD when equipop
# is absent (BACKLOG 218, which this door would otherwise repeat). A
# test pins this against the package's own list.
PROVIDER_NAMES = ["worldpop", "ghsl", "hdx", "geofabrik"]


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
        # ONE TABLE, NOT FOUR NAMED BOXES. Boxes called Dataset,
        # Version, Countries and Year are WORLDPOP'S VOCABULARY, and
        # three of the four providers do not speak it: GHSL asks for
        # product, release, epoch, crs and resolution; Geofabrik for a
        # region; HDX for a country group and a dataset. Every adapter
        # already DECLARES its fields, so the tool can ask for them by
        # name instead of guessing in advance - leave the table empty
        # and it lists exactly what the chosen provider wants.
        self.add(QgsProcessingParameterMatrix(
            "settings",
            "1b. Settings - one row per choice. Leave EMPTY and run to "
            "see what this provider asks for.",
            headers=["Setting", "Value"], optional=True))
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
        download = self.parameterAsBool(parameters, "download", context)
        folder = self.parameterAsString(parameters, "FOLDER", context)

        # THE TABLE IS THE PROVIDER'S OWN VOCABULARY. Rows arrive flat,
        # two cells at a time.
        flat = [str(v).strip() for v in
                (self.parameterAsMatrix(parameters, "settings", context)
                 or [])]
        if len(flat) % 2:
            raise QgsProcessingException(
                f"Box 1b has {len(flat)} cells, which is not a whole "
                "number of rows of two (setting, value).")
        choices = {}
        for k, v in zip(flat[0::2], flat[1::2]):
            if k:
                choices[k] = v

        try:
            from equipop.doors.fetching import PROVIDERS
            fields = list(getattr(PROVIDERS[provider], "FIELDS", []))
        except Exception as exc:
            raise QgsProcessingException(
                f"Could not read what {provider} asks for: {exc}")

        # AN EMPTY TABLE IS A QUESTION. Answer it and finish cleanly -
        # asking what a provider wants is not a failure (BACKLOG 248).
        if not choices:
            ch.info(f"{provider} asks for:")
            for f in fields:
                need = "required" if f.get("required") else "optional"
                ch.info(f"   {f['name']:<12} {f['label']}  ({need})")
            ch.info("")
            ch.info("Put those names in the left column of box 1b and "
                    "your values on the right, then run again. Nothing "
                    "was fetched - you asked what was available.")
            return {"FOLDER": folder}

        known = {f["name"] for f in fields}
        unknown = sorted(k for k in choices if k not in known)
        if unknown:
            raise QgsProcessingException(
                f"{provider} does not take {', '.join(unknown)}. It "
                "asks for: " + ", ".join(sorted(known)) + ".")

        try:
            plan = plan_fetch(provider, say=ch.info,
                              will_download=download, **choices)
        except (FetchError, ValueError) as exc:
            # The spine and the adapters refuse in plain words, and
            # their refusals carry the lists of valid choices.
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
