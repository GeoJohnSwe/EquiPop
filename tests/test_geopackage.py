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


# ------------------------------------------- the Groups dialog
def _dialog():
    state, pyt = _malta()
    tool = pyt.CountsShares()
    ps = tool.getParameterInfo()
    return tool, ps, {p.name: p for p in ps}


def test_the_new_boxes_live_under_a_heading_not_at_the_top():
    """John, field: they surfaced directly under the input layer -
    ABOVE the category field they depend on - because a parameter
    with no section lands at the top level. Placement is not cosmetic
    when a box sits above the thing that gives it meaning."""
    _, _, pm = _dialog()
    for name in ("restgroup", "restinpop"):
        assert getattr(pm[name], "category", ""), \
            f"{name} has no section and will float to the top"
        assert pm[name].category == "Groups: from a category field"


def test_the_two_grouping_routes_read_as_alternatives():
    """Three headings, not one flat list of seven boxes."""
    _, _, pm = _dialog()
    assert pm["pop"].category == "Groups"
    assert pm["treat"].category == "Groups: from number columns"
    assert pm["catfield"].category == "Groups: from a category field"
    assert pm["cattable"].category == "Groups: from a category field"


def test_the_remainder_box_waits_for_a_category_field():
    """It asks for a GROUP NAME, and there is nothing to collect
    until a category field is chosen - so it should not invite an
    answer before then."""
    tool, ps, pm = _dialog()
    tool.updateParameters(ps)
    assert not pm["restgroup"].enabled
    assert not pm["restinpop"].enabled
    pm["catfield"].value = "fclass"
    tool.updateParameters(ps)
    assert pm["restgroup"].enabled and pm["restinpop"].enabled


def test_choosing_one_route_dims_the_other():
    tool, ps, pm = _dialog()
    pm["catfield"].value = "fclass"
    tool.updateParameters(ps)
    assert not pm["treat"].enabled, \
        "number-column groups should dim once a category field is set"

    tool, ps, pm = _dialog()
    pm["treat"].value = "income"
    tool.updateParameters(ps)
    assert not pm["catfield"].enabled
    assert not pm["cattable"].enabled


def test_the_population_field_belongs_to_both_routes():
    """It is persons-per-row, not one of the alternatives - it is
    also what makes category groups count PERSONS rather than places
    (the 1.17 rule), so dimming it would be wrong."""
    tool, ps, pm = _dialog()
    pm["catfield"].value = "fclass"
    tool.updateParameters(ps)
    assert pm["pop"].enabled
    tool, ps, pm = _dialog()
    pm["treat"].value = "income"
    tool.updateParameters(ps)
    assert pm["pop"].enabled


def test_the_remainder_label_asks_for_a_name_not_a_value():
    """John read it as wanting 'restaurant'. It wants 'other'."""
    _, _, pm = _dialog()
    label = pm["restgroup"].displayName.lower()
    assert "name a group" in label
    assert "for example: other" in label
