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

The TEXT itself lives in the package, in equipop.doors.help, because
QGIS, R and SPSS need the very same sentences. This file only turns
it into the XML that Pro expects (v1.18.0).
"""
import os
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "tests"))

from equipop.doors.help import (HELP, help_for, missing_help,
                                summary_for, usage_for)


def build(tool_name, display, params):
    md = ET.Element("metadata", {"xml:lang": "en"})
    esri = ET.SubElement(md, "Esri")
    ET.SubElement(esri, "ArcGISFormat").text = "1.0"
    ET.SubElement(esri, "SyncOnce").text = "TRUE"
    tool = ET.SubElement(md, "tool", {"name": tool_name,
                                      "displayname": display,
                                      "toolboxalias": "equipop"})
    ET.SubElement(tool, "summary").text = summary_for(tool_name)
    ps = ET.SubElement(tool, "parameters")
    for name, disp in params:
        p = ET.SubElement(ps, "param", {
            "sync": "true", "name": name, "displayname": disp,
            "type": "Optional", "direction": "Input"})
        ET.SubElement(p, "dialogReference").text = help_for(
            name, disp)
    ET.SubElement(tool, "usage").text = usage_for(tool_name)
    idinfo = ET.SubElement(md, "dataIdInfo")
    cit = ET.SubElement(idinfo, "idCitation")
    ET.SubElement(cit, "resTitle").text = display
    ET.SubElement(idinfo, "idAbs").text = summary_for(tool_name)
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
        missing = missing_help([n for n, _ in params])
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
