# =====================================================================
# EquiPop - stub audit  (surface regenerated for v1.30.2)
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
# Reads nothing, changes nothing, needs no EquiPop files.
# =====================================================================
SURFACE = [
    ('FakeRasterLayer', 'QgsRasterLayer', ['dataProvider', 'extent', 'height', 'width'], {}),
    ('QgsCoordinateReferenceSystem', 'QgsCoordinateReferenceSystem', ['authid', 'description', 'isGeographic'], {}),
    ('QgsCoordinateTransform', 'QgsCoordinateTransform', ['transform'], {}),
    ('QgsFeature', 'QgsFeature', ['attributes', 'fields', 'geometry', 'hasGeometry', 'setAttributes', 'setGeometry'], {}),
    ('QgsField', 'QgsField', ['name'], {}),
    ('QgsFields', 'QgsFields', ['append', 'names'], {}),
    ('QgsGeometry', 'QgsGeometry', ['asMultiPolygon', 'asMultiPolyline', 'asPoint', 'asPolygon', 'asPolyline', 'isEmpty', 'isMultipart', 'transform', 'wkbType'], {}),
    ('QgsPointXY', 'QgsPointXY', ['x', 'y'], {}),
    ('QgsProcessingAlgorithm', 'QgsProcessingAlgorithm', ['addParameter', 'parameterAsBool', 'parameterAsDouble', 'parameterAsEnums', 'parameterAsFields', 'parameterAsMatrix', 'parameterAsRasterLayer', 'parameterAsSink', 'parameterAsSource', 'parameterAsString', 'parameterDefinitions', 'parameterAsStrings'], {}),
    ('QgsProcessingFeedback', 'QgsProcessingFeedback', ['setProgress'], {}),
    ('QgsProcessingParameterDefinition', 'QgsProcessingParameterDefinition', [], {'FlagAdvanced': 2}),
    # v1.30.2: the twelve parameter classes and four constants the
    # door actually builds its dialogs from. The list had not moved
    # since v1.29.1, so the 1.30 SEED BOX - QgsProcessingParameterNumber
    # and its .Integer constant - was audited by nothing. A surface
    # list that lags the door audits a door nobody is running.
    ('QgsProcessing', 'QgsProcessing', [], {'TypeVectorAnyGeometry': 2}),
    ('QgsProcessingException', 'QgsProcessingException', ['args'], {}),
    ('QgsProcessingParameterBoolean', 'QgsProcessingParameterBoolean', ['name'], {}),
    ('QgsProcessingParameterEnum', 'QgsProcessingParameterEnum', ['name'], {}),
    ('QgsProcessingParameterFeatureSink', 'QgsProcessingParameterFeatureSink', ['name'], {}),
    ('QgsProcessingParameterFeatureSource', 'QgsProcessingParameterFeatureSource', ['name'], {}),
    ('QgsProcessingParameterField', 'QgsProcessingParameterField', ['name'], {'Numeric': 1}),
    ('QgsProcessingParameterMatrix', 'QgsProcessingParameterMatrix', ['name'], {}),
    ('QgsProcessingParameterNumber', 'QgsProcessingParameterNumber', ['name'], {'Integer': 0, 'Double': 1}),
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
for stub_name, real_name, methods, constants in SURFACE:
    real = getattr(C, real_name, None)
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
            same = int(real_value) == int(stub_value)
        except Exception:
            same = real_value == stub_value
        if not same:
            gaps.append(label)
            print("\n  %s\n      VALUE DIFFERS: %s is %r here but %r in "
                  "the stub" % (label, name, real_value, stub_value))

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
