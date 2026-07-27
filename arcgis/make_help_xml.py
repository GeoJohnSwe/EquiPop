"""Generate ArcGIS Pro sidecar help for EquiPop.pyt (v1.16.3).

Pro shows two kinds of help in a tool dialog: the small comment
beside each parameter box, and the larger panel behind the '?'.
Both come from metadata XML files that live NEXT TO the toolbox -
EquiPop.<ToolName>.pyt.xml - so nothing is fetched from the web.

Run this file from the repo root to regenerate them:
    python arcgis/make_help_xml.py
The parameter NAMES are read from the toolbox itself (through the
test harness's simulated arcpy), so the help can never drift from
the dialog.
"""
import os
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "tests"))

HELP = {
    "layer": "The points to analyse - a point layer (coordinates are "
             "read straight from the geometry) or a plain table with "
             "coordinate columns. Coordinates must be metric; degree "
             "data is refused unless auto-projection is ticked.",
    "coordsrc": "Auto uses the geometry when the input has any, and "
                "attribute fields otherwise. Choose Attribute fields "
                "to override, e.g. when a layer carries coordinates "
                "in columns you trust more than its geometry.",
    "xfield": "The easting column - only for tables or attribute "
              "mode. Guessed when the name is recognisable "
              "(X/East/Easting/POINT_X...); no renaming is needed.",
    "yfield": "The northing column - only for tables or attribute "
              "mode.",
    "pop": "Persons represented by each point. Leave empty when every "
           "point is one person. k counts PERSONS, so this field "
           "decides how far the k-search must travel.",
    "treat": "Group counts: persons of the group at this point (use "
             "0/1 when points are individuals). Produces T_<group>_k "
             "(count) and R_<group>_k (share).",
    "k": "One or more k values, space-separated (200 1600). Each k "
         "gives its own neighbourhood: the nearest k PERSONS, so the "
         "radius floats and Dist_k reports it.",
    "r": "Fixed radii in metres, space-separated. The mirror image of "
         "k: the area is fixed and the population floats (N_r###).",
    "model": "Distance decay weighting. 'no decay' counts every "
             "neighbour equally inside the neighbourhood.",
    "halflife": "The distance in metres at which a neighbour counts "
                "half as much. Only used when a decay model is "
                "chosen.",
    "decayeps": "Where the decayed sum is cut off: neighbours whose "
                "weight falls below this are ignored. A decayed sum "
                "has no natural edge, so this is what bounds the "
                "search. 1e-6 (the default) reaches about 20 "
                "half-lives and is slow; 1e-3 reaches about 10 and "
                "runs roughly four times faster, with a difference "
                "far below any sampling error. The actual distance "
                "in metres is reported in the messages.",
    "catfield": "Build population and groups from the VALUES of one "
                "column (codes or names both work) instead of "
                "count fields.",
    "popvalues": "Which category values form the population. Empty "
                 "means all rows. Comma-separated, no quotes needed.",
    "treatvalues": "Which category values form groups: typeA; typeB "
                   "for one group each, or groupname: typeA, typeB "
                   "to merge several values into one named group.",
    "barrier": "Barriers as a DISTANCE INGREDIENT: a point, line or "
               "polygon layer, a table of cells, or a raster. Lines "
               "charge every grid cell they cross, polygons every "
               "cell they cover, rasters are sampled at cell "
               "midpoints.",
    "barrierfield": "The numeric field holding each feature's "
                    "crossing cost in rounds. For rasters the cell "
                    "value is the cost and this box is unused.",
    "barrieragg": "How several barrier features sharing one cell "
                  "combine. Additive (the default) stacks costs - a "
                  "river crossed at a railway costs both. Max/min/"
                  "mean are available when stacking is wrong.",
    "barrierx": "Easting column of a TABULAR barrier input.",
    "barriery": "Northing column of a tabular barrier input.",
    "dem": "Elevation raster: slopes become extra effort, so uphill "
           "neighbours are farther away than flat ones.",
    "tau": "Effort budgets in rounds, space-separated. With barriers "
           "or terrain, N_tau### counts the persons reachable within "
           "that many rounds instead of within a plain radius.",
    "roundtrip": "Count the journey home as well - the budget must "
                 "cover getting there AND back.",
    "existing": "What to do when result fields of the same name are "
                "already present: overwrite them, or stop.",
    "outmode": "Append results to the input layer, or write a new "
               "feature class (recommended for shapefiles: a file "
               "geodatabase has no 10-character field-name limit).",
    "outfc": "Path/name of the new feature class. Put it in a file "
             "geodatabase to keep full-length result names.",
    "outtable": "Where a TABLE input's results are written (.csv). "
                "The output carries your coordinates plus the result "
                "columns, in the original row order.",
    "unit": "The grid cell size in metres. Bigger cells mean fewer "
            "origins and much faster runs; smaller cells mean finer "
            "geography. This is the strongest speed control you "
            "have.",
    "autoproj": "When the input is in degrees, project it on the fly "
                "to the metric CRS that fits the data (the UTM zone "
                "is computed from the extent). The stored data is "
                "not modified. Tables cannot be auto-projected.",
    "shortnames": "Allow result names to be shortened to 10 "
                  "characters so they fit a shapefile. Names stay "
                  "unique - no two results ever merge - and the full "
                  "mapping is printed in the messages.",
    "fullpop": "Persons represented by each point. k counts PERSONS, "
               "and every statistic is weighted by this field, so a "
               "place of 40 people counts 40 times a place of one.",
    "values": "The numeric fields to describe - income, rent, age. "
              "One set of result columns per field.",
    "measures": "Tick the statistics you want; only those are "
                "calculated. Nv_<field>_k always reports how many "
                "neighbours actually had a value.",
    "pcts": "Percentiles as plain numbers, e.g. 10 25 75 90. Used "
            "only when 'percentiles' is ticked; results arrive as "
            "P10_<field>_k and so on.",
}

SUMMARY = {
    "CountsShares":
        "Builds an egocentric neighbourhood around EVERY point and "
        "counts what is inside it. Two ways to draw it: k (the "
        "nearest k persons - population fixed, radius floats, "
        "reported as Dist_k) or a radius in metres (area fixed, "
        "population floats). Group fields add counts and shares "
        "(T_ and R_). Barriers and terrain turn plain distance into "
        "EFFORT: rivers, railways, lakes, friction rasters and "
        "slopes make neighbours farther away in rounds, and N_tau### "
        "counts who is reachable within a budget. Inputs may be "
        "point layers (geometry is read directly) or tables with "
        "coordinate columns; coordinates must be metric.",
    "ValueStatistics":
        "Describes numeric fields - income, rent, age - among each "
        "point's k nearest PERSONS. Tick the measures you need "
        "(mean, median, Gini, sd, variance, se, min, max, count, "
        "sum, range, percentiles); only those are computed. With a "
        "full-population field every statistic is weighted by "
        "population, so a block of forty counts forty times a single "
        "household - including the median, the Gini and every "
        "percentile. Nv_<field>_k reports how many neighbours had a "
        "usable value, so thin coverage is visible rather than "
        "hidden.",
}

USAGE = {
    "CountsShares":
        "Start simple: input layer, one k, nothing else. Add group "
        "fields for shares. Add a barrier layer only when barriers "
        "matter - it switches the run to the effort engine and takes "
        "longer. Cell size is the speed control: doubling it "
        "quarters the number of origins. Results are appended to the "
        "input unless you choose a new feature class; shapefile "
        "targets cap field names at 10 characters, so a file "
        "geodatabase is the safer home for long names.",
    "ValueStatistics":
        "Give the value fields, tick the measures, set k. Use the "
        "full-population field whenever a point stands for more than "
        "one person. Gini refuses negative values, and percentiles "
        "need numbers in their box. As with machine 1, cell size "
        "controls the runtime and a file geodatabase avoids the "
        "shapefile name limit.",
}


def build(tool_name, display, params):
    md = ET.Element("metadata", {"xml:lang": "en"})
    esri = ET.SubElement(md, "Esri")
    ET.SubElement(esri, "ArcGISFormat").text = "1.0"
    ET.SubElement(esri, "SyncOnce").text = "TRUE"
    tool = ET.SubElement(md, "tool", {"name": tool_name,
                                      "displayname": display,
                                      "toolboxalias": "equipop"})
    ET.SubElement(tool, "summary").text = SUMMARY[tool_name]
    ps = ET.SubElement(tool, "parameters")
    for name, disp in params:
        p = ET.SubElement(ps, "param", {
            "sync": "true", "name": name, "displayname": disp,
            "type": "Optional", "direction": "Input"})
        ET.SubElement(p, "dialogReference").text = HELP.get(
            name, disp)
    ET.SubElement(tool, "usage").text = USAGE[tool_name]
    idinfo = ET.SubElement(md, "dataIdInfo")
    cit = ET.SubElement(idinfo, "idCitation")
    ET.SubElement(cit, "resTitle").text = display
    ET.SubElement(idinfo, "idAbs").text = SUMMARY[tool_name]
    return md


def main():
    import test_arcgis_stub as H
    import pandas as pd
    t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                      "SHAPE@Y": [0.0]})
    H._install_fake_arcpy(t)
    pyt = H._load_pyt()
    here = os.path.dirname(os.path.abspath(__file__))
    for cls, name in ((pyt.CountsShares, "CountsShares"),
                      (pyt.ValueStatistics, "ValueStatistics")):
        tool = cls()
        params = [(p.name, p.displayName)
                  for p in tool.getParameterInfo()]
        missing = [n for n, _ in params if n not in HELP]
        if missing:
            raise SystemExit(f"[help] no text for parameters: "
                             f"{missing}")
        md = build(name, tool.label, params)
        path = os.path.join(here, f"EquiPop.{name}.pyt.xml")
        ET.ElementTree(md).write(path, encoding="UTF-8",
                                 xml_declaration=True)
        print(f"[help] wrote {path} ({len(params)} parameters)")


if __name__ == "__main__":
    main()
