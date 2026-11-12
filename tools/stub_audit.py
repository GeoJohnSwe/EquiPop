# =====================================================================
# EquiPop - stub audit  (surface brought up to v1.63.8)
#
# WHERE: QGIS -> Plugins -> Python Console, as ONE line:
#   exec(open(r"C:\\Data\\EQP\\stub_audit.py", encoding="utf-8").read())
#
# WHY. tests/qgis_stub.py is a simulated PyQGIS, and 259 tests ran
# green against a call that crashes in real QGIS - p.isAdvanced() -
# because the STUB had invented the method. A stub is safe only where
# it is STRICTER than the real thing; where it is more generous it
# certifies code that cannot run, and no test can catch that, because
# the stub IS the thing under test. Only a real QGIS settles it.
#
# v1.29.1 fixes two faults in the first version of this script: it
# reported the stub's own private attributes as missing from QGIS
# (they were never meant to be there), and it checked only that a
# constant EXISTS, not that it holds the same value. The stub said
# FlagAdvanced = 1 where QGIS says 2.
#
# v1.63.8 (BACKLOG 472): the scoped enums. 1.63.7 moved the plugin
# from QgsProcessing.TypeVectorPoint, ...Number.Double, FlagAdvanced
# and the rest to Qgis.ProcessingSourceType.VectorPoint and its
# siblings, so that one plugin runs on QGIS 3.38 to 4.x - and left
# this list asking QGIS for the OLD names, which the plugin no longer
# uses and QGIS 4 no longer has. The values below are the simulator's
# (class Qgis in tests/qgis_stub.py); tests/test_qgis4_ready.py keeps
# the two lists in step. RUN THIS ON QGIS 4 AS WELL AS ON 3.x.
#
# Reads nothing, changes nothing, needs no EquiPop files.
# =====================================================================
SURFACE = [
    ('FakeRasterLayer', 'QgsRasterLayer', ['dataProvider', 'extent', 'height', 'width'], {}),
    ('QgsCoordinateReferenceSystem', 'QgsCoordinateReferenceSystem', ['authid', 'description', 'isGeographic'], {}),
    ('QgsCoordinateTransform', 'QgsCoordinateTransform', ['transform'], {}),
    ('QgsFeature', 'QgsFeature', ['attribute', 'attributes', 'fields', 'geometry', 'hasGeometry', 'setAttributes', 'setGeometry'], {}),
    ('QgsField', 'QgsField', ['name'], {}),
    ('QgsFields', 'QgsFields', ['append', 'names'], {}),
    ('QgsGeometry', 'QgsGeometry', ['asMultiPolygon', 'asMultiPolyline', 'asPoint', 'asPolygon', 'asPolyline', 'isEmpty', 'isMultipart', 'transform', 'wkbType'], {}),
    ('QgsPointXY', 'QgsPointXY', ['x', 'y'], {}),
    ('QgsProcessingAlgorithm', 'QgsProcessingAlgorithm', ['addParameter', 'parameterAsBool', 'parameterAsDouble', 'parameterAsEnums', 'parameterAsMatrix', 'parameterAsRasterLayer', 'parameterAsSink', 'parameterAsSource', 'parameterAsString', 'parameterDefinitions', 'parameterAsStrings'], {}),
    ('QgsProcessingFeedback', 'QgsProcessingFeedback', ['setProgress'], {}),
    ('QgsProcessingParameterDefinition', 'QgsProcessingParameterDefinition', [], {}),
    # v1.63.8: what the plugin spells its enums as since 1.63.7
    ('Qgis.GeometryType', 'Qgis.GeometryType', [], {'Point': 0, 'Line': 1, 'Polygon': 2, 'Unknown': 3, 'Null': 4}),
    ('Qgis.WkbType', 'Qgis.WkbType', [], {'Point': 1, 'LineString': 2, 'Polygon': 3, 'NoGeometry': 100}),
    ('Qgis.ProcessingSourceType', 'Qgis.ProcessingSourceType', [], {'MapLayer': -2, 'VectorAnyGeometry': -1, 'VectorPoint': 0, 'VectorLine': 1, 'VectorPolygon': 2, 'Raster': 3, 'File': 4, 'Vector': 5}),
    ('Qgis.ProcessingNumberParameterType', 'Qgis.ProcessingNumberParameterType', [], {'Integer': 0, 'Double': 1}),
    ('Qgis.ProcessingFieldParameterDataType', 'Qgis.ProcessingFieldParameterDataType', [], {'Any': -1, 'Numeric': 0, 'String': 1, 'DateTime': 2, 'Binary': 3, 'Boolean': 4}),
    ('Qgis.ProcessingFileParameterBehavior', 'Qgis.ProcessingFileParameterBehavior', [], {'File': 0, 'Folder': 1}),
    ('Qgis.ProcessingParameterFlag', 'Qgis.ProcessingParameterFlag', [], {'Advanced': 2, 'Hidden': 4, 'Optional': 8}),
    # v1.30.2: the twelve parameter classes and four constants the
    # door actually builds its dialogs from. The list had not moved
    # since v1.29.1, so the 1.30 SEED BOX - QgsProcessingParameterNumber
    # and its .Integer constant - was audited by nothing. A surface
    # list that lags the door audits a door nobody is running.
    ('QgsProcessingException', 'QgsProcessingException', ['args'], {}),
    ('QgsProcessingParameterBoolean', 'QgsProcessingParameterBoolean', ['name'], {}),
    ('QgsProcessingParameterEnum', 'QgsProcessingParameterEnum', ['name'], {}),
    ('QgsProcessingParameterFeatureSink', 'QgsProcessingParameterFeatureSink', ['name'], {}),
    ('QgsProcessingParameterFeatureSource', 'QgsProcessingParameterFeatureSource', ['name'], {}),
    ('QgsProcessingParameterField', 'QgsProcessingParameterField', ['name'], {}),
    ('QgsProcessingParameterMatrix', 'QgsProcessingParameterMatrix', ['name'], {}),
    ('QgsProcessingParameterNumber', 'QgsProcessingParameterNumber', ['name'], {}),
    ('QgsProcessingParameterRasterLayer', 'QgsProcessingParameterRasterLayer', ['name'], {}),
    ('QgsApplication', 'QgsApplication', ['processingRegistry'], {}),
    ('QgsProcessingProvider', 'QgsProcessingProvider', ['addAlgorithm'], {}),
    ('QgsProject', 'QgsProject', ['instance', 'transformContext'], {}),
    ('QgsWkbTypes', 'QgsWkbTypes', ['geometryType'], {}),
    ('_Block', 'QgsRasterBlock', ['value'], {}),
    ('_Extent', 'QgsRectangle', ['height', 'width', 'xMinimum', 'yMaximum'], {}),
    ('_Param', 'QgsProcessingParameterString', ['description', 'flags', 'name', 'setFlags', 'setHelp'], {}),
    ('_Provider', 'QgsRasterDataProvider', ['block', 'sourceNoDataValue'], {}),
    ('_Sink', 'QgsFeatureSink', ['addFeature'], {}),
    ('_Source', 'QgsProcessingFeatureSource', ['featureCount', 'fields', 'getFeatures', 'sourceCrs', 'wkbType'], {}),
]

import sys

try:
    import qgis.core as C
except ModuleNotFoundError:                       # BACKLOG 80
    # This tool exists to catch the simulator flattering itself, so it
    # is worthless anywhere the REAL PyQGIS is absent - and it used to
    # say so with a bare traceback, which reads like a broken tool
    # rather than a tool used in the wrong place.
    sys.stderr.write(
        "\n  stub_audit needs the REAL PyQGIS, and there is none here.\n"
        "  That is the whole point of it: it compares the simulator in\n"
        "  tests/qgis_stub.py against what QGIS actually offers, so\n"
        "  running it outside QGIS would only compare the simulator\n"
        "  with itself.\n\n"
        "  Run it INSIDE QGIS, which is the only place PyQGIS lives:\n"
        "      QGIS -> Plugins -> Python Console, then paste\n"
        "      exec(open(r\"<path>\\tools\\stub_audit.py\",\n"
        "                encoding=\"utf-8\").read())\n\n"
        "  NOT the OSGeo4W Shell: its plain `python` has no PyQGIS\n"
        "  unless the QGIS environment has been initialised first.\n"
        "  (1.29.6 said the shell. That was wrong, and it contradicted\n"
        "  this file's own header.)\n\n"
        "  BACKLOG 80 asks for this on every release that touches the\n"
        "  QGIS door, with the result recorded in the MANUAL\n"
        "  validation row. 1.29.1 exists because nothing did.\n\n")
    raise SystemExit(2)

print("=" * 68)
print("Auditing the simulator against QGIS",
      getattr(getattr(C, "Qgis", None), "QGIS_VERSION", "?"))
print("=" * 68)
gaps, checked, skipped = [], 0, []


def _find(dotted):
    """Qgis.GeometryType -> the class, or None where QGIS has none."""
    obj = C
    for part in dotted.split("."):
        obj = getattr(obj, part, None)
        if obj is None:
            return None
    return obj


def _number(v):
    """An enum member's number. Under QGIS 4 (PyQt6) an enum is a real
    enum and int() refuses it; .value is the number on both."""
    v = getattr(v, "value", v)
    return int(v)


for stub_name, real_name, methods, constants in SURFACE:
    real = _find(real_name)
    if real is None:
        skipped.append("%s -> %s" % (stub_name, real_name))
        continue
    label = (stub_name if stub_name == real_name
             else "%s (stands in for %s)" % (stub_name, real_name))
    checked += len(methods) + len(constants)
    for m in methods:
        if not hasattr(real, m):
            gaps.append(label)
            print("\n  %s\n      INVENTED: .%s() - QGIS has no such method"
                  % (label, m))
    for name, stub_value in constants.items():
        if not hasattr(real, name):
            gaps.append(label)
            print("\n  %s\n      INVENTED: %s - QGIS has no such constant"
                  % (label, name))
            continue
        real_value = getattr(real, name)
        try:
            same = _number(real_value) == int(stub_value)
        except Exception:
            same = real_value == stub_value
        if not same:
            gaps.append(label)
            print("\n  %s\n      VALUE DIFFERS: %s is %r here but %r in "
                  "the stub" % (label, name, real_value, stub_value))

# v1.63.8: NULL. base.type_column reads it to tell a missing type
# from a type; it is an object in QGIS 3 and None in QGIS 4.
print("\nqgis.core.NULL :", ("present, %r" % (C.NULL,))
      if hasattr(C, "NULL") else "ABSENT (the plugin then treats only "
      "None as missing)")

print("\n" + "-" * 68)
print("methods and constants checked :", checked)
print("classes skipped               :", skipped if skipped else "none")
print("-" * 68)
if gaps:
    print("*** %d PROBLEM(S). The simulator promises things this QGIS"
          % len(gaps))
    print("*** does not have, so tests using them prove nothing.")
else:
    print("No gaps: everything the plugin relies on exists here, with")
    print("the same values. The simulator is not flattering itself.")
print("=" * 68)
