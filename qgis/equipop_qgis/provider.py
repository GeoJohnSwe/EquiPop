# -*- coding: utf-8 -*-
"""provider.py - the EquiPop group in the QGIS Processing toolbox."""
from qgis.core import QgsProcessingProvider

from .alg_continental import ContinentalRasters
from .alg_demography import SpatialDemography
from .alg_counts import CountsAndShares
from .alg_stats import ValueStatistics


class EquipopProvider(QgsProcessingProvider):

    def loadAlgorithms(self):
        for alg in (CountsAndShares(), ValueStatistics(),
                    ContinentalRasters(),
                    SpatialDemography()):
            self.addAlgorithm(alg)

    def id(self):
        return "equipop"

    def name(self):
        return "EquiPop"

    def longName(self):
        return "EquiPop - bespoke neighbourhoods (k-nearest)"
