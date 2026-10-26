# -*- coding: utf-8 -*-
"""provider.py - the EquiPop group in the QGIS Processing toolbox."""
from qgis.core import QgsProcessingProvider

from .alg_catalogue import (FetchSelected, OsmCatalogue,
                            WorldPopCatalogue)
from .alg_continental import ContinentalRasters
from .alg_demography import SpatialDemography
from .alg_fetch import SpatialDataFetch
from .alg_inventory import FolderInventory
from .alg_counts import CountsAndShares
from .alg_show import ShowTools
from .alg_stats import ValueStatistics


class EquipopProvider(QgsProcessingProvider):

    def loadAlgorithms(self):
        # v1.62.0, BACKLOG 438: EVERY tool is registered; 3 to 6 are
        # only hidden from the toolbox until tool 0 shows them (see
        # EquipopAlgorithm.flags), so models that use them still run.
        for alg in (ShowTools(), CountsAndShares(), ValueStatistics(),
                    ContinentalRasters(),
                    SpatialDemography(),
                    WorldPopCatalogue(), OsmCatalogue(),
                    FetchSelected(), SpatialDataFetch(),
                    FolderInventory()):
            self.addAlgorithm(alg)

    def id(self):
        return "equipop"

    def name(self):
        return "EquiPop"

    def longName(self):
        return "EquiPop - bespoke neighbourhoods (k-nearest)"
