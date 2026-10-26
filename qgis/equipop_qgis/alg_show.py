# -*- coding: utf-8 -*-
"""
alg_show.py - tool 0: show or hide tools 3 to 6.

v1.62.0, BACKLOG 438. John, 25 October 2026: the same plugin for
everybody, with one difference - whether tools 3 to 6 are listed -
"let us make the default to hide - but please indicate in help etc.,
how it can be lifted". This is the lifting.

The rule and the saved choice live in equipop.doors.toolset, shared
with ArcGIS Pro. Here: one box, the choice saved, and the toolbox
refreshed so the change is visible at once. The tool runs in QGIS's
main thread (NoThreading), because refreshing the provider from a
worker thread is not safe.
"""
from qgis.core import (QgsProcessingException,
                       QgsProcessingParameterEnum)

from .base import EquipopAlgorithm, algorithm_flag

#: WRITTEN DOWN, not imported (displayName runs while QGIS builds the
#: toolbox; BACKLOG 218). The same words as toolset.CHOICES - a test
#: pins it.
CHOICES = ["Only tools 1 and 2 (the standard set)",
           "All tools, 1 to 6"]


class ShowTools(EquipopAlgorithm):
    """Choose whether the toolbox lists tools 3 to 6."""

    EQP_TOOL = "ShowTools"
    EQP_LABEL = "0. Show or hide tools 3-6"

    def name(self):
        return "showtools"

    def displayName(self):
        return self.EQP_LABEL

    def flags(self):
        f = super().flags()
        nothread = algorithm_flag("NoThreading")
        return f | nothread if nothread is not None else f

    def initAlgorithm(self, config=None):
        try:
            from equipop.doors.toolset import show_all
            now = 1 if show_all() else 0
        except Exception:
            now = 0
        self.add(QgsProcessingParameterEnum(
            "show", "Which tools the toolbox shows",
            options=list(CHOICES), defaultValue=now))

    def processAlgorithm(self, parameters, context, feedback):
        from .base import check_versions
        ch = self.channel(feedback)
        check_versions(ch)
        from equipop.doors.toolset import set_show_all, state_sentence
        pick = self.parameterAsEnum(parameters, "show", context)
        if pick not in (0, 1):
            raise QgsProcessingException(
                "Choose one of the two: only tools 1 and 2, or all "
                "tools.")
        try:
            where = set_show_all(pick == 1)
        except OSError as exc:
            raise QgsProcessingException(
                f"The choice could not be saved ({exc}). Nothing has "
                "changed.")
        ch.info(f"Saved in {where}.")
        ch.info(state_sentence())
        self._refreshed = _refresh_toolbox()
        if not self._refreshed:
            ch.info("If the Processing Toolbox has not changed, restart "
                    "QGIS.")
        return {}


def _refresh_toolbox():
    """Ask the EquiPop provider to reload, so the toolbox re-reads
    which tools are hidden. True if that was done."""
    try:
        from qgis.core import QgsApplication
        prov = QgsApplication.processingRegistry().providerById("equipop")
        if prov is None:
            return False
        prov.refreshAlgorithms()
        return True
    except Exception:
        return False
