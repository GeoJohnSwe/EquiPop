"""
qgis_stub.py - a simulated PyQGIS, so the QGIS door can be tested in
CI where qgis.core cannot be pip-installed.

Built to the same doctrine as the fake arcpy in test_arcgis_stub.py,
including its limits, which are worth stating plainly:

    THE SIMULATOR PROVES LOGIC. ONLY THE FIELD PROVES BEHAVIOUR.

Everything the ArcGIS round learned the hard way was invisible to a
simulator - file locks, cached schemas, a parameter type that
crashed the host outright. The QGIS equivalents will be invisible
here too. What this DOES prove: that parameters are declared, that
coordinates are read and reprojected, that the result columns are
built and written in the right order, that refusals are raised as
the host's own exception type, and that the numbers match the
Python core. That is most of a door, and none of its behaviour.

Only the parts of PyQGIS the door actually touches are simulated.
"""
import sys
import types

import numpy as np
import pandas as pd


# --------------------------------------------------------- geometry
class QgsPointXY:
    def __init__(self, x, y):
        self._x, self._y = float(x), float(y)

    def x(self):
        return self._x

    def y(self):
        return self._y


class QgsGeometry:
    def __init__(self, pt=None):
        self._pt = pt

    @staticmethod
    def fromPointXY(pt):
        return QgsGeometry(pt)

    def asPoint(self):
        if self._pt is None:
            raise ValueError("geometry is empty")
        return self._pt

    def isEmpty(self):
        return self._pt is None

    def isNull(self):
        return self._pt is None

    def transform(self, tr):
        self._pt = tr.transform(self._pt)
        return 0


# ----------------------------------------------------------- fields
class QVariant:
    Double, Int, String, Bool = 6, 2, 10, 1


class QgsField:
    def __init__(self, name, type_=QVariant.Double, *a, **kw):
        self._name, self._type = str(name), type_

    def name(self):
        return self._name

    def type(self):
        return self._type


class QgsFields:
    def __init__(self):
        self._f = []

    def append(self, field):
        self._f.append(field)
        return True

    def names(self):
        return [f.name() for f in self._f]

    def indexFromName(self, name):
        n = self.names()
        return n.index(name) if name in n else -1

    def field(self, i):
        return self._f[i]

    def __len__(self):
        return len(self._f)

    def __iter__(self):
        return iter(self._f)


class QgsFeature:
    def __init__(self, fields=None):
        self._fields = fields or QgsFields()
        self._attrs = [None] * len(self._fields)
        self._geom = None
        self._id = 0

    def id(self):
        return self._id

    def fields(self):
        return self._fields

    def geometry(self):
        return self._geom

    def setGeometry(self, g):
        self._geom = g

    def hasGeometry(self):
        return self._geom is not None and not self._geom.isEmpty()

    def attributes(self):
        return list(self._attrs)

    def setAttributes(self, values):
        self._attrs = list(values)

    def attribute(self, name):
        i = self._fields.indexFromName(name)
        return None if i < 0 else self._attrs[i]

    def __getitem__(self, key):
        return self.attribute(key) if isinstance(key, str) \
            else self._attrs[key]


# -------------------------------------------------------------- CRS
class QgsCoordinateReferenceSystem:
    def __init__(self, ident="EPSG:3006"):
        self._id = str(ident)

    def authid(self):
        return self._id

    def isGeographic(self):
        return self._id in ("EPSG:4326", "EPSG:4258")

    def isValid(self):
        return bool(self._id)

    def description(self):
        return {"EPSG:3006": "SWEREF99 TM",
                "EPSG:4326": "WGS 84"}.get(self._id, self._id)

    def mapUnits(self):
        return 6 if self.isGeographic() else 0   # 6 = degrees, 0 = m


class QgsCoordinateTransform:
    """Not a real reprojection - it marks that one happened, so the
    door's LOGIC around reprojection can be tested. Real numbers need
    real QGIS."""

    def __init__(self, src, dst, ctx=None):
        self.src, self.dst = src, dst
        self.calls = 0

    def transform(self, pt):
        self.calls += 1
        if self.src.isGeographic() and not self.dst.isGeographic():
            # a crude but monotonic stand-in for a projection
            return QgsPointXY(pt.x() * 111320.0, pt.y() * 110540.0)
        return pt


class QgsProject:
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def transformContext(self):
        return None


# --------------------------------------------------------- feedback
class QgsProcessingFeedback:
    def __init__(self):
        self.info, self.warnings, self.errors = [], [], []
        self.progress = []
        self._cancelled = False

    def pushInfo(self, text):
        self.info.append(str(text))

    def pushWarning(self, text):
        self.warnings.append(str(text))

    def reportError(self, text, fatal=False):
        self.errors.append(str(text))

    def setProgress(self, p):
        self.progress.append(p)

    def isCanceled(self):
        return self._cancelled

    def cancel(self):
        self._cancelled = True


class QgsProcessingException(Exception):
    pass


# ------------------------------------------------------ the source
class _Source:
    """What parameterAsSource hands back: features, fields, CRS."""

    def __init__(self, table: pd.DataFrame, crs="EPSG:3006",
                 geometry=True):
        self._t = table.reset_index(drop=True)
        self._crs = QgsCoordinateReferenceSystem(crs)
        self._geometry = geometry
        self._fields = QgsFields()
        for c in self._t.columns:
            if c in ("x", "y") and geometry:
                continue
            kind = (QVariant.Double
                    if pd.api.types.is_numeric_dtype(self._t[c])
                    else QVariant.String)
            self._fields.append(QgsField(c, kind))

    def fields(self):
        return self._fields

    def sourceCrs(self):
        return self._crs

    def wkbType(self):
        return 1 if self._geometry else 100      # Point / NoGeometry

    def featureCount(self):
        return len(self._t)

    def getFeatures(self, *a):
        names = self._fields.names()
        for i, row in self._t.iterrows():
            f = QgsFeature(self._fields)
            f._id = int(i)
            f.setAttributes([row[c] for c in names])
            if self._geometry:
                f.setGeometry(QgsGeometry.fromPointXY(
                    QgsPointXY(row["x"], row["y"])))
            yield f


class _Sink:
    """Collects what the door writes, so a test can read it back."""

    def __init__(self, fields, wkb=None, crs=None):
        self._fields = fields
        self.features = []

    def addFeature(self, feature, flags=None):
        self.features.append(feature)
        return True

    def addFeatures(self, feats, flags=None):
        for f in feats:
            self.addFeature(f)
        return True

    def to_frame(self) -> pd.DataFrame:
        names = self._fields.names()
        rows = [dict(zip(names, f.attributes())) for f in self.features]
        df = pd.DataFrame(rows, columns=names)
        if self.features and self.features[0].hasGeometry():
            df["x"] = [f.geometry().asPoint().x() for f in self.features]
            df["y"] = [f.geometry().asPoint().y() for f in self.features]
        return df


class QgsFeatureSink:
    FastInsert = 1


# ------------------------------------------------------- parameters
class _Param:
    def __init__(self, name, description="", *a, **kw):
        self.name_, self.description_ = name, description
        self.optional = kw.get("optional", False)
        self.defaultValue_ = kw.get("defaultValue", None)
        self.parentLayerParameterName = kw.get(
            "parentLayerParameterName", None)
        self.options = kw.get("options", None)
        self.allowMultiple = kw.get("allowMultiple", False)
        self.extra = kw

    def name(self):
        return self.name_

    def description(self):
        return self.description_

    def setHelp(self, text):
        self.help_ = text


class QgsProcessingParameterFeatureSource(_Param):
    pass


class QgsProcessingParameterField(_Param):
    Any, Numeric, String = 0, 1, 2


class QgsProcessingParameterString(_Param):
    pass


class QgsProcessingParameterNumber(_Param):
    Integer, Double = 0, 1


class QgsProcessingParameterBoolean(_Param):
    pass


class QgsProcessingParameterEnum(_Param):
    pass


class QgsProcessingParameterMatrix(_Param):
    pass


class QgsProcessingParameterFeatureSink(_Param):
    pass


class QgsProcessing:
    TypeVectorPoint, TypeVector, TypeVectorAnyGeometry = 0, 1, 2


# ------------------------------------------------------- algorithm
class QgsProcessingAlgorithm:
    """The base QGIS calls. The parameterAs* helpers read from the
    plain dict a test passes in, which is how QGIS works too."""

    def __init__(self):
        self._params = []

    def addParameter(self, p):
        self._params.append(p)
        return True

    def parameterDefinitions(self):
        return list(self._params)

    def initAlgorithm(self, config=None):
        pass

    # -- readers -------------------------------------------------
    def parameterAsSource(self, parameters, name, context):
        return parameters.get(name)

    def parameterAsString(self, parameters, name, context):
        v = parameters.get(name)
        return "" if v is None else str(v)

    def parameterAsDouble(self, parameters, name, context):
        v = parameters.get(name)
        return 0.0 if v in (None, "") else float(v)

    def parameterAsInt(self, parameters, name, context):
        v = parameters.get(name)
        return 0 if v in (None, "") else int(v)

    def parameterAsBool(self, parameters, name, context):
        return bool(parameters.get(name, False))

    def parameterAsFields(self, parameters, name, context):
        v = parameters.get(name)
        if v in (None, ""):
            return []
        return list(v) if isinstance(v, (list, tuple)) else [str(v)]

    def parameterAsMatrix(self, parameters, name, context):
        return parameters.get(name) or []

    def parameterAsEnums(self, parameters, name, context):
        v = parameters.get(name)
        return list(v) if isinstance(v, (list, tuple)) else (
            [] if v is None else [int(v)])

    def parameterAsSink(self, parameters, name, context, fields,
                        wkb=None, crs=None):
        sink = _Sink(fields, wkb, crs)
        parameters.setdefault("_sinks", {})[name] = sink
        return sink, f"memory:{name}"


class QgsProcessingProvider:
    def __init__(self):
        self._algs = []

    def addAlgorithm(self, alg):
        self._algs.append(alg)
        return True

    def algorithms(self):
        return list(self._algs)

    def loadAlgorithms(self):
        pass


# ------------------------------------------------------- installer
_NAMES = [
    "QgsPointXY", "QgsGeometry", "QgsField", "QgsFields", "QgsFeature",
    "QgsCoordinateReferenceSystem", "QgsCoordinateTransform",
    "QgsProject", "QgsProcessingFeedback", "QgsProcessingException",
    "QgsFeatureSink", "QgsProcessing", "QgsProcessingAlgorithm",
    "QgsProcessingProvider", "QgsProcessingParameterFeatureSource",
    "QgsProcessingParameterField", "QgsProcessingParameterString",
    "QgsProcessingParameterNumber", "QgsProcessingParameterBoolean",
    "QgsProcessingParameterEnum", "QgsProcessingParameterMatrix",
    "QgsProcessingParameterFeatureSink",
]


def install():
    """Put the simulated qgis.core and qgis.PyQt on sys.path."""
    core = types.ModuleType("qgis.core")
    g = globals()
    for n in _NAMES:
        setattr(core, n, g[n])

    qgis = types.ModuleType("qgis")
    qgis.core = core
    pyqt = types.ModuleType("qgis.PyQt")
    qtcore = types.ModuleType("qgis.PyQt.QtCore")
    qtcore.QVariant = QVariant
    pyqt.QtCore = qtcore
    qgis.PyQt = pyqt

    sys.modules.update({"qgis": qgis, "qgis.core": core,
                        "qgis.PyQt": pyqt,
                        "qgis.PyQt.QtCore": qtcore})
    return core


def source_from(table: pd.DataFrame, crs="EPSG:3006", geometry=True):
    """A feature source over a DataFrame with x/y columns."""
    return _Source(table, crs=crs, geometry=geometry)


def gridby_source():
    """Gridby as a QGIS layer would present it - the conformance
    input, so the door is fed exactly what the reference was made
    from."""
    from equipop.datasets import load
    p = load("gridby")["people"].copy()
    return source_from(p[["x", "y", "count_all", "count_group"]])
