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
        self._parts = []
        self._wkb = 1

    @staticmethod
    def fromPointXY(pt):
        return QgsGeometry(pt)

    def asPoint(self):
        if self._pt is None:
            raise ValueError("geometry is empty")
        return self._pt

    def centroid(self):
        """Real PyQGIS has this on every geometry; the simulator did
        not, so a door taking the centroid of an input feature - which
        is how a POLYGON layer joins to a point lattice - failed here
        while being correct in QGIS. Another gap of the same family as
        the discarded sink CRS.
        """
        if self._pt is None:
            raise ValueError("geometry is empty")
        return QgsGeometry(self._pt)

    def isEmpty(self):
        return self._pt is None and not self._parts

    def isEmpty(self):
        return self._pt is None and not self._parts

    def isNull(self):
        return self.isEmpty()

    def transform(self, tr):
        if self._pt is not None:
            self._pt = tr.transform(self._pt)
        if self._parts:
            self._parts = [[tr.transform(p) for p in part]
                           for part in self._parts]
        return 0

    # -- lines and polygons --------------------------------------
    def isMultipart(self):
        return len(self._parts) > 1

    def wkbType(self):
        return self._wkb

    def asPolyline(self):
        return self._parts[0] if self._parts else []

    def asMultiPolyline(self):
        return self._parts

    def asPolygon(self):
        return self._parts[:1]

    def asMultiPolygon(self):
        return [[p] for p in self._parts]

    @staticmethod
    def fromPolygonXY(rings):
        """Real PyQGIS has this; the stub did not, which is why no
        test ever built a polygon barrier - and the polygon path
        crashed the first time John pointed it at a lake (v1.29.3).
        A stub that is too SPARSE is safe but silently narrows what
        can be asked."""
        g = QgsGeometry()
        g._parts = [list(r) for r in rings]
        g._wkb = 3                       # polygon
        return g

    @staticmethod
    def fromPolylineXY(points):
        g = QgsGeometry()
        g._parts = [list(points)]
        g._wkb = 2                       # line
        return g

    @staticmethod
    def fromParts(parts, wkb=2):
        g = QgsGeometry()
        g._parts = [[QgsPointXY(x, y) for x, y in part]
                    for part in parts]
        g._wkb = wkb
        return g


# ----------------------------------------------------------- fields
class QVariant:
    Double, Int, String, Bool = 6, 2, 10, 1


class _MetaTypes:
    Double, Int, QString, Bool = 6, 2, 10, 1


class _Null:
    """PyQGIS's NULL. str(NULL) is the four characters 'NULL'.

    THIS IS THE FIFTH TIME this simulator has been kinder than QGIS.
    An untouched matrix cell is a QVariant null, and code that strips
    it and tests for emptiness sees a four-character string instead.
    The stub returned '' and then [], so a door that handled BOTH of
    those still failed on John's machine.
    """

    def __str__(self):
        return "NULL"

    def __repr__(self):
        return "NULL"

    def __bool__(self):
        return False

    def __eq__(self, other):
        return other is self or other is None or other == ""

    def __hash__(self):
        return hash("")


NULL = _Null()


class QMetaType:
    """v1.29.3: QGIS 3.38 moved field types from QVariant::Type to
    QMetaType::Type and deprecated the old QgsField constructor."""
    Type = _MetaTypes


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
        # A REAL LAYER RETURNS A Qgis.WkbType, and base.py rightly
        # passes it straight to parameterAsSink. Returning a bare int
        # here made the stub reject its own correct callers the moment
        # the sink was tightened - the simulator being wrong in the
        # opposite direction. NoGeometry is 100 in PyQGIS.
        return QgsWkbTypes.Point if self._geometry else _WkbType(100)

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
        # KEEP THE CRS AND THE GEOMETRY TYPE. They used to be accepted
        # and dropped, so no test could check which projection a door
        # stamped on its output - and a layer written with the wrong
        # one lands in the wrong part of the world while looking
        # perfectly healthy. John found exactly that: a Burundi result
        # rendered north of Sweden.
        self._fields = fields
        self.wkb = wkb
        self.crs = crs
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
class QgsProcessingParameterDefinition:
    # 2, not 1 - the value real QGIS uses (John, 3.42.1,
    # v1.29.1). Harmless in practice, since the flag is only
    # ever ANDed against itself, but a stub that holds a value
    # QGIS never produces is a stub telling a small lie, and
    # this file's whole job is to tell the truth about QGIS.
    FlagAdvanced = 2
    FlagOptional = 2


class _Param:
    def __init__(self, name, description="", *a, **kw):
        self._flags = 0
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

    def flags(self):
        return self._flags

    def setFlags(self, f):
        self._flags = f

    # NO isAdvanced() - real PyQGIS has no such method (v1.29.1).
    # This stub had one, so every test passed over a call that
    # crashes in QGIS. A stub may be STRICTER than the real thing;
    # where it is more generous it certifies code that cannot run.


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


class QgsProcessingParameterRasterLayer(_Param):
    pass


# BACKLOG 38: the continental door asks for a FOLDER of rasters, its
# own projection, and a folder to write tiles into. These behave like
# every other parameter here - the simulator's job is to let the door
# be constructed and read, not to reproduce QGIS.
class QgsProcessingParameterFile(_Param):
    File, Folder = 0, 1


class QgsProcessingParameterCrs(_Param):
    pass


class QgsProcessingParameterFolderDestination(_Param):
    pass


class _WkbType(int):
    """A WKB type, distinguishable from a bare int.

    Real PyQGIS hands parameterAsSink a Qgis.WkbType enum and REFUSES
    an int - "argument 5 has unexpected type 'int'". This simulator
    used to accept anything, so both continental doors passed their
    tests while carrying a call QGIS rejects, and John found it after
    a 10.8 second continental run had already succeeded. A simulator
    that is MORE PERMISSIVE than the thing it simulates certifies the
    wrong code.
    """

    __slots__ = ()


class QgsWkbTypes:
    """Two different numberings live here, which is the trap.

    GEOMETRY types:  Point = 0, Line = 1, Polygon = 2
    WKB types:       Point = 1, LineString = 2, Polygon = 3

    parameterAsSink wants the WKB one. Passing 2 meaning "point"
    silently means POLYGON.
    """
    PointGeometry, LineGeometry, PolygonGeometry = 0, 1, 2
    Point = _WkbType(1)
    LineString = _WkbType(2)
    Polygon = _WkbType(3)

    @staticmethod
    def geometryType(wkb):
        return {1: 0, 2: 1, 3: 2, 100: 0}.get(int(wkb), 0)


class _Block:
    def __init__(self, arr):
        self.a = arr

    def value(self, r, c):
        return float(self.a[r][c])


class _Extent:
    def __init__(self, x0, y0, x1, y1):
        self._v = (x0, y0, x1, y1)

    def xMinimum(self):
        return self._v[0]

    def yMaximum(self):
        return self._v[3]

    def width(self):
        return self._v[2] - self._v[0]

    def height(self):
        return self._v[3] - self._v[1]


class _Provider:
    def __init__(self, arr, nodata=None):
        self.arr, self._nd = arr, nodata

    def block(self, band, extent, w, h):
        return _Block(self.arr)

    def sourceNoDataValue(self, band):
        return self._nd


class FakeRasterLayer:
    """Enough of QgsRasterLayer for the friction and slope paths."""

    def __init__(self, arr, xmin=0.0, ymax=1000.0, cw=100.0,
                 ch=100.0, nodata=None):
        import numpy as _np
        self.arr = _np.asarray(arr, float)
        self._p = _Provider(self.arr, nodata)
        h, w = self.arr.shape
        self._ext = _Extent(xmin, ymax - h * ch, xmin + w * cw, ymax)

    def dataProvider(self):
        return self._p

    def extent(self):
        return self._ext

    def width(self):
        return self.arr.shape[1]

    def height(self):
        return self.arr.shape[0]


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

    def parameterAsFile(self, parameters, name, context):
        """BACKLOG 38. A path, handed back as the string it is."""
        v = parameters.get(name)
        return "" if v is None else str(v)

    def parameterAsCrs(self, parameters, name, context):
        """None when the box is empty, which is the common case - the
        continental door then lets suggest_projection choose."""
        v = parameters.get(name)
        if v in (None, ""):
            return None
        return v if hasattr(v, "authid") else QgsCoordinateReferenceSystem(v)

    def parameterAsStrings(self, parameters, name, context):
        """v1.29.3: the replacement for parameterAsFields, which QGIS
        deprecated in 3.40. The old name is deliberately NOT defined
        here - a stub is safe when it is STRICTER than the real
        thing, so removing it means no code can quietly go back to
        the deprecated call and still pass its tests."""
        v = parameters.get(name)
        if v in (None, ""):
            return []
        return list(v) if isinstance(v, (list, tuple)) else [str(v)]

    def parameterAsMatrix(self, parameters, name, context):
        """AN EMPTY MATRIX IS [NULL], AND str(NULL) IS 'NULL'.

        Real QGIS 3.42 returns a list holding one empty string for an
        untouched table - and None for the parameter comes back the
        same way. This returned [] instead, so a door that checked the
        cell count for evenness passed every test and refused every
        real empty table. Third time this simulator has been more
        forgiving than the thing it simulates (221 the bare int, 223
        the discarded CRS, 231 the missing reader).
        """
        v = parameters.get(name)
        if v is None or v == [] or v == [""]:
            return [NULL]
        return list(v)

    def parameterAsRasterLayer(self, parameters, name, context):
        return parameters.get(name)

    def parameterAsEnum(self, parameters, name, context):
        """The SINGULAR form. Real PyQGIS has both - parameterAsEnum
        for a single choice and parameterAsEnums for allowMultiple -
        and this simulator had only the plural, so a door using the
        ordinary single-choice reader failed here while being correct
        in QGIS. The same incompleteness as the sink's CRS.
        """
        v = parameters.get(name, 0)
        if isinstance(v, (list, tuple)):
            return int(v[0]) if v else 0
        return int(v or 0)

    def parameterAsEnums(self, parameters, name, context):
        v = parameters.get(name)
        return list(v) if isinstance(v, (list, tuple)) else (
            [] if v is None else [int(v)])

    def parameterAsSink(self, parameters, name, context, fields,
                        wkb=None, crs=None):
        # Mirror PyQGIS, which refuses a bare int here. See _WkbType.
        if wkb is not None and not isinstance(wkb, _WkbType):
            raise TypeError(
                "QgsProcessingAlgorithm.parameterAsSink(): argument 5 "
                f"has unexpected type '{type(wkb).__name__}' - pass "
                "QgsWkbTypes.Point, not a number.")
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
    "QgsProcessingParameterDefinition",
    "QgsProcessingParameterRasterLayer", "QgsWkbTypes",
    "QgsProcessingParameterFile", "QgsProcessingParameterCrs",
    "QgsProcessingParameterFolderDestination",
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
    qtcore.QMetaType = QMetaType
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
