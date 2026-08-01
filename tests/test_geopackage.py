"""GeoPackage, as Malta taught us (v1.20.1).

Three separate failures in one evening of John's testing, all from
one .gpkg file, none of them reproducible before this file existed:

  1. The category dropdown stayed empty. The dialog turns the layer
     into a path to read its values, and a GeoPackage's own
     dataSource is a connection description arcpy will not reopen:
     "Instance=...,Dataset=main.%gis_osm_pois_free". Swallowed
     silently, so the box simply looked broken.
  2. Writing new fields raised "The operation is not supported by
     this implementation." ExtendTable is a geodatabase habit;
     GeoPackage does not have it.
  3. Writing to a NEW feature class raised KeyError 'OBJECTID'. A
     GeoPackage names its row identifier `fid`; the copy in the
     geodatabase names it `OBJECTID`, and the values were read
     under the old name.

The common cause is one assumption: that every target behaves like a
file geodatabase. The simulator now knows better, so this class of
bug is catchable here instead of in Malta.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_arcgis_stub as H                        # noqa: E402


GPKG = (r"Instance=C:\Data\EQP\malta.gpkg,"
        r"Dataset=main.%gis_osm_pois_free")


class _Msg:
    def __init__(self):
        self.info, self.warn, self.err = [], [], []

    def addMessage(self, t):
        self.info.append(str(t))

    def addWarningMessage(self, t):
        self.warn.append(str(t))

    def addErrorMessage(self, t):
        self.err.append(str(t))

    def all(self):
        return " ".join(self.info + self.warn + self.err)


def _malta(n=60, with_nulls=True):
    """A layer shaped like John's: POI types, mostly-NULL numbers,
    `fid` for the identifier, and a dataSource arcpy cannot reopen."""
    rng = np.random.default_rng(11)
    kinds = ["cafe", "bar", "bakery", "restaurant", "supermarket",
             "library", "atm", "artwork"]
    t = pd.DataFrame({
        "fid": np.arange(1, n + 1),
        "SHAPE@X": rng.uniform(0, 4000, n),
        "SHAPE@Y": rng.uniform(0, 4000, n),
        "fclass": rng.choice(kinds, n),
        "income": rng.normal(300, 50, n)})
    if with_nulls:
        t.loc[t.index % 3 != 0, "income"] = np.nan   # mostly missing
    state = H._install_fake_arcpy(t)
    state["oid_names"] = {"poi": "fid"}
    state["no_extend"] = {"poi"}
    state["catalog_paths"] = {"poi": GPKG}
    return state, H._load_pyt()


class _GpkgLayer:
    """What Pro hands the dialog: an object whose dataSource is the
    unusable connection string, and whose str() is the layer name."""

    def __init__(self, name="poi"):
        self.name = name
        self.dataSource = GPKG

    def __str__(self):
        return self.name


# ------------------------------------------- 1. the dropdown
def test_the_category_dropdown_fills_from_a_geopackage_layer():
    """John's first report: selecting `fclass` did nothing. The
    dialog is handed a Layer OBJECT, not a name - and the object's
    dataSource cannot be reopened, so the values never arrived."""
    state, pyt = _malta()
    tool = pyt.CountsShares()
    ps = tool.getParameterInfo()
    pm = {p.name: p for p in ps}
    pm["layer"].value = _GpkgLayer()
    pm["catfield"].value = "fclass"
    tool.updateParameters(ps)
    offered = pm["cattable"].filters[0].list
    assert offered, "the category value dropdown is still empty"
    assert "cafe" in offered and "library" in offered


def test_unreadable_values_are_reported_rather_than_swallowed():
    """Loud by design. Silence is what turned a small bug into a
    whole testing session."""
    state, pyt = _malta()
    msg = _Msg()

    class _Unreadable:
        """Every route to it is a connection string arcpy refuses -
        the worst case, where nothing can be offered."""
        dataSource = GPKG

        def __str__(self):
            return GPKG

    vals = pyt._distinct_values(_Unreadable(), "fclass", messages=msg)
    assert vals == []
    said = msg.all()
    assert "fclass" in said and "cannot open" in said
    assert "file geodatabase" in said, "the message must name a way out"


def test_reading_the_values_is_reported_when_it_works():
    state, pyt = _malta()
    msg = _Msg()
    vals = pyt._distinct_values(_GpkgLayer(), "fclass", messages=msg)
    assert "cafe" in vals
    assert "8 distinct values" in msg.all()


# ------------------------------------- 2. the unsupported write
def test_new_fields_are_written_even_without_the_bulk_call():
    """A GeoPackage has no ExtendTable. Fall back to adding the
    fields and filling them row by row - slower, works everywhere -
    and say so rather than showing a traceback."""
    state, pyt = _malta()
    msg = _Msg()
    pyt._run_tool("counts", "poi", msg, weight_field=None,
                  k_text="10", unit=100.0)
    cols = set(state["table"].columns)
    assert "N_10" in cols and "Dist_10" in cols
    said = msg.all().lower()
    assert "row by row" in said or "slower" in said


def test_the_bulk_call_is_still_used_where_it_works():
    """The fallback must not become the default: it is slower, and
    on a geodatabase there is no reason to pay for it."""
    rng = np.random.default_rng(3)
    t = pd.DataFrame({"OBJECTID": np.arange(1, 41),
                      "SHAPE@X": rng.uniform(0, 900, 40),
                      "SHAPE@Y": rng.uniform(0, 900, 40)})
    state = H._install_fake_arcpy(t)
    pyt = H._load_pyt()
    msg = _Msg()
    pyt._run_tool("counts", "people", msg, k_text="10", unit=100.0)
    assert "N_10" in state["table"].columns
    assert not state.get("added_fields"), \
        "the slow path was used on a geodatabase, which supports the " \
        "fast one"


# --------------------------------- 3. the renamed identifier
def test_a_copy_that_renames_the_identifier_still_gets_results():
    """John's KeyError 'OBJECTID': values read from the GeoPackage
    under `fid`, then looked up under the geodatabase's `OBJECTID`."""
    state, pyt = _malta()
    msg = _Msg()
    pyt._run_tool("counts", "poi", msg, k_text="10", unit=100.0,
                  out_mode="New feature class",
                  out_fc=r"C:\Data\work.gdb\poi_eqp")
    out = state["copies"][r"C:\Data\work.gdb\poi_eqp"]
    assert "N_10" in out.columns
    assert len(out) == 60
    assert out["N_10"].notna().all()


# ------------------------------------------- missing data
def test_a_missing_value_leaves_the_person_in_the_neighbourhood():
    """John's rule for machine 2, confirmed: k is still reached over
    everyone, the statistic is computed over those who HAVE a value,
    and Nv_ reports how many that was. (k=500 with 200 incomes ->
    the statistics of those 200.)"""
    state, pyt = _malta()
    msg = _Msg()
    pyt._run_tool("stats", "poi", msg, value_fields=["income"],
                  k_text="20", stats_list=["mean"], unit=100.0)
    t = state["table"]
    assert "Nv_income_20" in t.columns and "Mean_income_20" in t.columns
    # two thirds of the incomes are missing, so the valid count must
    # be well below the neighbourhood size but not zero
    assert (t["Nv_income_20"] < t["N_20"]).any()
    assert (t["Nv_income_20"] > 0).any()
    assert t["Mean_income_20"].notna().any()
