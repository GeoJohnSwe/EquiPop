# -*- coding: utf-8 -*-
"""
alg_inventory.py - WHAT IS IN A FOLDER, with a door on it at last.

BACKLOG 269 shipped equipop/doors/inventory.py in 1.45.0: it reads a
folder of rasters and vectors and records layers, fields, CRS,
geometry, extent, the distinct values of the columns you would group
on, and - the point of it - WHICH FILES SHARE A LATTICE and can
therefore be joined by integer index without a resample.

It was complete, tested, and reachable from nowhere. No GUI, no
runner, no Stata. Only by writing Python, which the person this
project is built for does not do. It is the first of the five
unreachable things found in session 12 and this door is its answer.

THIN, like machines 3 and 4. Every decision about what an inventory
means lives in the package. What is QGIS's own here: picking a
folder, and turning the result into a table a person can read and
sort.

WHY THE OUTPUT IS A TABLE AND NOT JUST A MESSAGE. The messages pane
scrolls away and cannot be sorted. An inventory of ninety files is
something you look DOWN, grouping by lattice to see which sets go
together - so it comes back as a layer, with the JSON written beside
the folder for the tools that read it.
"""
from qgis.core import (QgsFeature, QgsField, QgsFields,
                       QgsProcessingException,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSink,
                       QgsWkbTypes)
from qgis.PyQt.QtCore import QMetaType

from .base import EquipopAlgorithm

#: The columns the table comes back with, in the order a person reads
#: them: what the file is, then what it holds, then whether it can be
#: joined to its neighbours without a resample.
COLUMNS = [
    ("file", QMetaType.Type.QString),
    ("kind", QMetaType.Type.QString),
    ("layer", QMetaType.Type.QString),
    ("crs", QMetaType.Type.QString),
    ("geometry", QMetaType.Type.QString),
    ("features", QMetaType.Type.LongLong),
    ("lattice", QMetaType.Type.QString),
    ("cell_size", QMetaType.Type.QString),
    ("class_column", QMetaType.Type.QString),
    ("sidecars", QMetaType.Type.QString),
    ("class_values", QMetaType.Type.QString),
    ("problem", QMetaType.Type.QString),
]


class FolderInventory(EquipopAlgorithm):
    """Describe a folder's contents. Reads; changes nothing."""

    EQP_TOOL = "FolderInventory"

    def name(self):
        return "folderinventory"

    # WRITTEN DOWN, NOT IMPORTED - displayName runs while QGIS builds
    # the toolbox, and a module-level `import equipop` there kills the
    # whole plugin when the package is missing (BACKLOG 218, 78).
    EQP_LABEL = "6. What is in this folder? (reads, changes nothing)"

    def displayName(self):
        return self.EQP_LABEL

    # NO shortHelpString HERE. The base class builds it from
    # equipop.doors.help - one text for every door - AND falls back
    # to an install sentence when the package is missing, which is
    # BACKLOG 78's contract and a test enforces it. The first draft
    # of this door overrode the method with a fixed string and broke
    # that contract: a user with no package would have got a cheerful
    # description of a tool that could not run.

    def initAlgorithm(self, config=None):
        self.add(QgsProcessingParameterFile(
            "folder", "1. The folder to look at (subfolders included)",
            behavior=QgsProcessingParameterFile.Folder))
        self.add(QgsProcessingParameterBoolean(
            "deep", "2. Also list the distinct values of class columns "
                    "(fclass, highway, landuse...) - slower on large "
                    "vector files",
            defaultValue=True))
        self.add(QgsProcessingParameterBoolean(
            "write", "3. Save equipop_inventory.json in the folder, so "
                     "other tools can read it",
            defaultValue=True))
        self.add(QgsProcessingParameterFeatureSink(
            "OUTPUT", "Folder inventory"))

    # -----------------------------------------------------------------
    def processAlgorithm(self, parameters, context, feedback):
        from equipop.doors.inventory import inventory

        from .base import check_versions

        ch = self.channel(feedback)
        check_versions(ch)

        folder = self.parameterAsFile(parameters, "folder", context)
        deep = self.parameterAsBool(parameters, "deep", context)
        write = self.parameterAsBool(parameters, "write", context)
        if not folder:
            raise QgsProcessingException(
                "Box 1: choose a folder to look at.")

        got = inventory(folder, say=ch.info, deep=deep, write=write)

        fields = QgsFields()
        for nm, typ in COLUMNS:
            fields.append(QgsField(nm, typ))
        sink, dest = self.parameterAsSink(
            parameters, "OUTPUT", context, fields,
            QgsWkbTypes.NoGeometry)
        if sink is None:
            raise QgsProcessingException(
                "No output was created - choose a destination for the "
                "inventory table.")

        rows = _rows(got)
        written = 0
        for r in rows:
            f = QgsFeature(fields)
            f.setAttributes([r.get(nm) for nm, _ in COLUMNS])
            ok = sink.addFeature(f)
            if ok is not False:
                written += 1
        if written != len(rows):
            # BACKLOG 291's lesson, applied here from the start: count
            # what the sink TOOK, never what was offered.
            raise QgsProcessingException(
                f"The output kept only {written} of {len(rows)} rows. "
                "Try a GeoPackage destination.")

        lattices = {r["lattice"] for r in rows if r.get("lattice")}
        ch.info(f"{len(rows)} file(s) listed, {len(lattices)} distinct "
                f"lattice(s).")
        if write:
            # John, session 12: say that the file is not just a record
            # of this run but an INPUT to the next one. A user who does
            # not know that has no reason to keep it.
            ch.info(
                "equipop_inventory.json written into the folder. IT IS "
                "READ BY THE OTHER TOOLS: machine 3 fills its class "
                "and grouping lists from it, so you never type class "
                "names. Keep it with the data.")
        if len(lattices) > 1:
            ch.warning(
                f"THE FOLDER HOLDS {len(lattices)} DIFFERENT LATTICES. "
                "Files on different lattices cannot be merged by index "
                "without a resample - sort the table by the lattice "
                "column to see which sets go together.")
        return {"OUTPUT": dest}


def _rows(got):
    """One row per record, exactly as the package returns them.

    THE FIRST VERSION OF THIS FUNCTION INVENTED A SHAPE. It assumed
    files holding nested layers and flattened them; the package
    already returns one FLAT record per file-or-layer, with the class
    values under `classes` as {column: {distinct, values}} and the
    pixel size as a two-element `pixel_size` list. Written from memory
    of what an inventory ought to look like rather than from the
    function, and caught by reading it. The engine is thirty lines
    away - read it.
    """
    out = []
    for rec in got.get("files", []):
        classes = rec.get("classes") or {}
        col = next(iter(classes), "")
        info = classes.get(col) or {}
        vals = info.get("values") or []
        note = info.get("note") or ""
        px = rec.get("pixel_size") or []
        out.append({
            "file": rec.get("file") or "",
            "kind": rec.get("kind") or "",
            "layer": rec.get("layer") or "",
            "crs": rec.get("crs") or "",
            "geometry": rec.get("geometry") or "",
            "features": _int(rec.get("features")),
            "lattice": rec.get("lattice") or "",
            "cell_size": (f"{abs(float(px[0])):g} x "
                          f"{abs(float(px[1])):g}") if len(px) == 2 else "",
            "class_column": col,
            # A shapefile is ONE thing in five files. John's Swedish
            # OSM folder listed 109 rows of which 91 were sidecars.
            "sidecars": (", ".join(rec["sidecars"])
                         if rec.get("sidecars") else ""),
            # Truncated on purpose: an OSM extract holds dozens of
            # fclass values and a table cell is not where you read
            # them. The JSON keeps every one.
            "class_values": (note if note else
                             ", ".join(map(str, vals[:12]))
                             + (" ..." if len(vals) > 12 else "")),
            "problem": rec.get("error") or "",
        })
    return out


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
