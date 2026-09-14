"""Generate ArcGIS Pro sidecar help for EquiPop.pyt (v1.16.3).

Pro shows two kinds of help in a tool dialog: the small comment
beside each parameter box, and the larger panel behind the '?'.
Both come from metadata XML files that live NEXT TO the toolbox -
EquiPop.<ToolName>.pyt.xml - so nothing is fetched from the web.

Run this file from the repo root to regenerate them:
    python arcgis/make_help_xml.py
    python arcgis/make_help_xml.py --out DIR   # write elsewhere

BACKLOG 45: --out exists because the SUITE used to call this with no
way to say where, so `pytest` left two untracked .pyt.xml files in
`arcgis/` every time it ran. A test that modifies the working tree it
is testing is a test that can hide a change - and these are build
outputs, neither committed nor shipped, so the repo only ever held
them by accident.
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


def as_dialog_html(text):
    """The parameter comment as the escaped HTML Pro expects.

    BACKLOG 34 recorded the suspicion in v1.16.8: "plain text where
    escaped HTML is expected". The text went in as one unbroken
    paragraph - 1,286 characters for the newest entry - which is hard
    to read even when it renders.

    Sentences that START A NEW IDEA get their own paragraph. The cue
    is the house style itself: these entries put the thing that
    matters in CAPITALS at the head of a sentence, so a capitalised
    opening is a reliable break and needs no new markup in help.py.
    """
    import re as _re
    text = " ".join(str(text).split())
    parts, cur = [], []
    for sent in _re.split(r"(?<=[.!?]) +", text):
        head = sent.split(" ")[0].strip("'\":,")
        # >= 3 letters, not > 3: "HOW MUCH THIS MATTERS..." opens a
        # real new idea and a four-letter threshold silently swallowed
        # it. Two-letter openers ("IT", "SO") are left alone - they
        # continue a thought rather than starting one.
        shouty = len(head) >= 3 and head.isupper() and head.isalpha()
        if shouty and cur:
            parts.append(" ".join(cur))
            cur = [sent]
        else:
            cur.append(sent)
    if cur:
        parts.append(" ".join(cur))
    return "".join(f"<p>{escape(p)}</p>" for p in parts if p)


def build(tool_name, display, params, plain=False):
    md = ET.Element("metadata", {"xml:lang": "en"})
    esri = ET.SubElement(md, "Esri")
    ET.SubElement(esri, "ArcGISFormat").text = "1.0"
    # BACKLOG 44, open since v1.18.0 and waiting on exactly one field
    # cycle: SyncOnce=TRUE lets Pro SYNCHRONISE ITS OWN METADATA OVER
    # the authored text the first time the toolbox is opened, which is
    # the suspected cause of 34 (help rendering empty). John supplied
    # the cycle in session 12 - a dialogReference flyout with a
    # correct title and an empty body. FALSE tells Pro the metadata is
    # authored and not to regenerate it.
    # STILL A HYPOTHESIS. It is one of three faults found together and
    # only a run in a real Pro can say which mattered.
    ET.SubElement(esri, "SyncOnce").text = "FALSE"
    tool = ET.SubElement(md, "tool", {"name": tool_name,
                                      "displayname": display,
                                      "toolboxalias": "equipop"})
    ET.SubElement(tool, "summary").text = summary_for(tool_name)
    ps = ET.SubElement(tool, "parameters")
    for name, disp in params:
        p = ET.SubElement(ps, "param", {
            "sync": "true", "name": name, "displayname": disp,
            "type": "Optional", "direction": "Input"})
        txt = help_for(name, disp)
        ET.SubElement(p, "dialogReference").text = (
            txt if plain else as_dialog_html(txt))
    ET.SubElement(tool, "usage").text = usage_for(tool_name)
    idinfo = ET.SubElement(md, "dataIdInfo")
    cit = ET.SubElement(idinfo, "idCitation")
    ET.SubElement(cit, "resTitle").text = display
    ET.SubElement(idinfo, "idAbs").text = summary_for(tool_name)
    return md


def load_toolbox():
    """EquiPop.pyt, loaded whichever way this machine allows.

    TWO CALLERS, TWO WORLDS. A release build runs from the repository
    and has no ArcGIS, so it uses the simulated arcpy in tests/. John
    runs it from a folder holding FIVE FILES AND NO tests/ DIRECTORY,
    inside Pro's Python Command Prompt, where arcpy is real.

    Only the first ever worked. This file has been shipped as one of
    the five since 1.44.4 and, until 1.47.2, could not be run by the
    person it was shipped to - ModuleNotFoundError on
    test_arcgis_stub, immediately, every time. Found when the --plain
    escape hatch offered as insurance turned out to be unusable by
    the one person who might need it.
    """
    try:
        import test_arcgis_stub as H
        import pandas as pd
        t = pd.DataFrame({"OBJECTID": [1], "SHAPE@X": [0.0],
                          "SHAPE@Y": [0.0]})
        H._install_fake_arcpy(t)
        return H._load_pyt()
    except ImportError:
        pass
    try:
        import arcpy                              # noqa: F401
    except ImportError:
        raise SystemExit(
            "[help] cannot load the toolbox. Either run this from the "
            "EquiPop repository root, where tests/ supplies a "
            "simulated arcpy:\n"
            "    python arcgis/make_help_xml.py\n"
            "or run it inside ArcGIS Pro's PYTHON COMMAND PROMPT "
            "(Start menu -> ArcGIS), where arcpy is real:\n"
            "    cd C:\\Data\\EQP\n"
            "    python make_help_xml.py\n"
            "Pro's embedded Python WINDOW is not a command prompt - "
            "typing `python ...` there is a syntax error.")
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "EquiPop.pyt")
    if not os.path.exists(path):
        raise SystemExit(f"[help] no EquiPop.pyt beside {__file__}. "
                         "The toolbox and this script must sit in the "
                         "same folder.")
    spec = importlib.util.spec_from_file_location("EquiPop_pyt", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(out_dir=None, plain=False):
    pyt = load_toolbox()
    here = out_dir or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(here, exist_ok=True)
    # BACKLOG 294. ALL FOUR TOOLS, from v1.47.2. Machines 3 and 4
    # were absent from this list for as long as it has existed - not
    # by choice but because thirteen of their parameters had no help
    # text, and this script refuses to write a sidecar with a gap in
    # it. So rather than a partial file it wrote none, and Pro showed
    # "There is no description for this item" and "There is no
    # explanation for this parameter" against every box, for both
    # tools, in every release.
    # Their summary and usage text existed the whole time. It could
    # not reach Pro for want of a file.
    for cls, name in ((pyt.CountsShares, "CountsShares"),
                      (pyt.ValueStatistics, "ValueStatistics"),
                      (pyt.ContinentalRasters, "ContinentalRasters"),
                      (pyt.SpatialDemography, "SpatialDemography")):
        tool = cls()
        params = [(p.name, p.displayName)
                  for p in tool.getParameterInfo()]
        missing = missing_help([n for n, _ in params])
        if missing:
            raise SystemExit(f"[help] no text for parameters: "
                             f"{missing}")
        md = build(name, tool.label, params, plain=plain)
        path = os.path.join(here, f"EquiPop.{name}.pyt.xml")
        ET.ElementTree(md).write(path, encoding="UTF-8",
                                 xml_declaration=True)
        print(f"[help] wrote {path} ({len(params)} parameters)")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plain", action="store_true",
                    help="write the parameter comments as PLAIN TEXT "
                         "instead of escaped <p> paragraphs. Use this "
                         "if Pro shows literal <p> tags in the flyout "
                         "beside a parameter box - the paragraphs are "
                         "an untested attempt at BACKLOG 34 and this "
                         "switch undoes them in ten seconds without "
                         "waiting for a release.")
    ap.add_argument("--out", default=None,
                    help="directory to write the .pyt.xml files into "
                         "(default: next to EquiPop.pyt, which is "
                         "where Pro looks for them)")
    _a = ap.parse_args()
    main(_a.out, plain=_a.plain)
