# -*- coding: utf-8 -*-
"""plugin.py - registers the provider when QGIS loads the plugin."""
from qgis.core import QgsApplication

from .provider import EquipopProvider


class EquipopPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initGui(self):
        self.provider = EquipopProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(
                self.provider)
            self.provider = None
