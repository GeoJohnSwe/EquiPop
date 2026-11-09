# -*- coding: utf-8 -*-
"""EquiPop for QGIS - bespoke k-nearest neighbourhoods."""
__version__ = "1.63.5"


def classFactory(iface):
    from .plugin import EquipopPlugin
    return EquipopPlugin(iface)
