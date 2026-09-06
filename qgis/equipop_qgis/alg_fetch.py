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

# WHAT THE DROPDOWN SHOWS. The keys are internal and were displayed
# raw - John: "the info in the dropbox looks like spelling errors".
# Quite so: worldpop, ghsl, hdx, geofabrik say nothing about what they
# hold or what they cost you. THE LICENCE BELONGS HERE, because
# Geofabrik's share-alike obligation matters BEFORE the download, not
# after, and it is the one thing that can follow a published result
# home.
PROVIDER_LABELS = [
    "worldpop - population by age and sex, 100 m / 1 km, per country",
    "ghsl - built-up surface and population 1975-2030, global grid (JRC)",
    "hdx - humanitarian datasets by country, many formats",
    "geofabrik - OpenStreetMap extracts (ODbL: SHARE-ALIKE)",
]


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
            options=list(PROVIDER_LABELS), defaultValue=0))
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
        # AN UNTOUCHED CELL IS PyQGIS's NULL, AND str(NULL) IS THE
        # FOUR CHARACTERS 'NULL'. Not an empty string, not None. So
        # stripping and testing for emptiness left a four-character
        # string, the evenness check saw ONE cell, and the invitation
        # printed on the box could never be accepted. John hit this on
        # all four providers TWICE, because the first fix handled the
        # empty string and None and not this.
        from .base import matrix_cells
        flat = matrix_cells(self, parameters,
                            "settings", context)
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
            # QUOTE THE SETTING NAME AND LABEL THE COLUMNS. The
            # old layout leaned on alignment - "product   Which layer
            # (REQUIRED)" - and QGIS's log collapses the spacing, so
            # John could not tell where the Setting column ended and
            # the Value began. Quotes survive any amount of
            # whitespace mangling (BACKLOG 268).
            ch.info(f"{provider} asks for these settings. Put the "
                    "quoted NAME in the Setting column and one of "
                    "the values in the Value column.")
            ch.info("")
            example = []
            for f in fields:
                dflt = f.get("default")
                if dflt is not None:
                    need = f"optional - left out, it uses {dflt}"
                elif f.get("required"):
                    need = "REQUIRED"
                else:
                    need = "optional"
                ch.info(f"  Setting '{f['name']}'  ({need})"
                        f"  - {f['label']}")
                opts = f.get("options") or []
                describe = f.get("describe") or {}
                if opts and describe:
                    for o in opts:
                        note = describe.get(o, "")
                        ch.info(f"      Value '{o}'"
                                + (f"  - {note}" if note else ""))
                elif opts:
                    shown = " | ".join(str(o) for o in opts[:12])
                    more = " | ..." if len(opts) > 12 else ""
                    ch.info(f"      Value: {shown}{more}")
                elif f.get("lists_when_empty"):
                    ch.info("      Value: many - give this setting "
                            "alone and run to see the list")
                if f.get("required") and dflt is None:
                    example.append((
                        f["name"],
                        str(opts[0]) if opts
                        else ("<blank - run to see the list>"
                              if f.get("lists_when_empty")
                              else "<your value>")))
            ch.info("")
            if example:
                ch.info("The smallest table that will work:")
                ch.info("      Setting        Value")
                for k, v in example:
                    ch.info(f"      {k:<14} {v}")
                ch.info("")
            ch.info("Nothing was fetched - you asked what was "
                    "available.")
            return {"FOLDER": folder}

        # A SETTING NAME IS NOT DATA, so its case should not matter.
        # John typed "Product" and was refused for a capital letter.
        by_lower = {f["name"].lower(): f["name"] for f in fields}
        fixed, unknown = {}, []
        for k, v in choices.items():
            real = by_lower.get(k.strip().lower())
            if real:
                fixed[real] = v
            else:
                unknown.append(k)
        choices = fixed
        if unknown:
            # SUGGEST, do not merely refuse. He typed "year" because
            # the field was LABELLED Year, and "1" because the options
            # elsewhere are numbered.
            hints = []
            for bad in unknown:
                b = bad.strip().lower()
                near = [n for n in by_lower.values()
                        if b in n.lower() or n.lower() in b
                        or b in str(next(f["label"] for f in fields
                                         if f["name"] == n)).lower()]
                if near:
                    hints.append(f"{bad!r} - did you mean "
                                 + " or ".join(repr(n) for n in near)
                                 + "?")
                else:
                    hints.append(f"{bad!r}")
            raise QgsProcessingException(
                f"{provider} does not take " + "; ".join(hints)
                + ". It asks for: "
                + ", ".join(f["name"] for f in fields)
                + ". Put the NAME in the left column, the VALUE in "
                  "the right.")

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
