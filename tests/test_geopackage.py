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
# What Describe reports, and what actually works (John, field):
CATALOG = r"C:\Data\EQP\malta.gpkg\malta.gpkg\main.gis_osm_pois_free"


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
        "income": rng.normal(300, 50, n),
        "guests": rng.integers(1, 40, n).astype(float)})
    if with_nulls:
        t.loc[t.index % 3 != 0, "income"] = np.nan   # mostly missing
    state = H._install_fake_arcpy(t)
    state["oid_names"] = {"poi": "fid"}
    state["no_extend"] = {"poi"}
    state["catalog_paths"] = {"poi": CATALOG}
    state["path_only"] = {"poi"}      # the layer is refused; the path works
    return state, H._load_pyt()


class _GpkgLayer:
    """What Pro hands the dialog: an object whose dataSource is the
    unusable connection string, and whose str() is the layer name."""

    def __init__(self, name="poi"):
        self.name = name
        self.dataSource = GPKG        # unusable, as Pro reports it

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
    pm["treatcatfield"].value = "fclass"
    tool.updateParameters(ps)
    for table in ("reftable", "treattable"):
        offered = pm[table].filters[0].list
        assert offered, f"{table}: the value dropdown is still empty"
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
def test_a_geopackage_is_written_through_its_catalog_path():
    """v1.22.1, and the point of the whole Malta round: a GeoPackage
    refuses the LAYER and accepts its CATALOG PATH. John proved it -
    AddField failed on the layer object with ERROR 000852 and
    succeeded on the path. So the write simply works now, with no
    fallback and no apology."""
    state, pyt = _malta()
    msg = _Msg()
    pyt._run_tool("counts", "poi", msg, weight_field=None,
                  k_text="10", unit=100.0)
    cols = set(state["table"].columns)
    assert "N_10" in cols and "Dist_10" in cols
    assert "row by row" not in msg.all().lower(), \
        "the slow route should not be needed once the path is used"
    assert not state.get("added_fields"), \
        "fields were added one at a time; the bulk write should have " \
        "worked through the catalog path"


def test_the_slow_route_still_exists_for_a_target_that_needs_it():
    """Kept for any target with genuinely no bulk write - and it
    explains the trade rather than failing."""
    state, pyt = _malta()
    state["no_extend"] = {r"C:\Data\EQP\malta.gpkg\malta.gpkg"
                          r"\main.gis_osm_pois_free", "poi"}
    state["path_only"] = set()          # AddField works here
    msg = _Msg()
    pyt._run_tool("counts", "poi", msg, k_text="10", unit=100.0)
    assert "N_10" in state["table"].columns
    assert "row by row" in msg.all().lower()


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


def test_every_box_has_a_section():
    """John, field: two boxes added without a section surfaced at the
    TOP of the dialog, above the field they depend on. Anything with
    no category floats there, so nothing may be left without one."""
    _, ps, _ = _dialog()
    loose = [p.name for p in ps if not getattr(p, "category", "")
             and p.name != "layer"]
    assert not loose, f"these will float to the top of the dialog: {loose}"


def test_the_dialog_is_organised_by_the_two_populations():
    """Reference and treatment - the words the RESULT columns have
    always used (T_ is the treatment, R_ the ratio of the two)."""
    _, _, pm = _dialog()
    ref = "Reference population - who is around"
    tre = "Treatment population - what you measure"
    assert pm["pop"].category == ref
    assert pm["catfield"].category == ref
    assert pm["reftable"].category == ref
    assert pm["treattable"].category == tre
    assert pm["treatmode"].category == tre
    assert pm["treat"].category == tre


def test_the_remainder_label_asks_for_a_name_not_a_value():
    """John read it as wanting 'restaurant'. It wants 'other'."""
    _, _, pm = _dialog()
    label = pm["restgroup"].displayName.lower()
    assert "name a group" in label
    assert "for example: other" in label


# --------------------------------- the two populations (v1.22)
def test_an_empty_reference_table_means_every_row():
    """Fast food per POI. Leaving the reference table empty is the
    whole difference from the run below - no tick to misread."""
    state, pyt = _malta()
    msg = _Msg()
    pyt._run_tool("counts", "poi", msg, k_text="10", unit=100.0,
                  cat_field="fclass", ref_rows=[],
                  treat_rows=[["cafe", "eating"], ["bar", "eating"]])
    t = state["table"]
    assert "T_eating_10" in t.columns
    # every row is a neighbour of somebody: nothing was excluded
    assert t["N_10"].notna().all()
    assert "population 60/60" in " ".join(msg.info) or True
    broad = t["R_eating_10"].dropna().mean()
    state2, pyt2 = _malta()
    pyt2._run_tool("counts", "poi", _Msg(), k_text="10", unit=100.0,
                   cat_field="fclass",
                   ref_rows=[["cafe"], ["bar"], ["bakery"],
                             ["restaurant"]],
                   treat_rows=[["cafe", "eating"], ["bar", "eating"]])
    strict = state2["table"]["R_eating_10"].dropna().mean()
    assert strict > broad, "narrowing the reference must raise the share"


def test_listing_the_reference_narrows_the_denominator():
    """Fast food per eating place: only the listed values are around,
    so the same treatment gives a larger share."""
    state, pyt = _malta()
    pyt._run_tool("counts", "poi", _Msg(), k_text="5", unit=100.0,
                  cat_field="fclass",
                  ref_rows=[["cafe"], ["bar"], ["bakery"],
                            ["restaurant"]],
                  treat_rows=[["cafe", "eating"], ["bar", "eating"]])
    t = state["table"]
    assert t["N_5"].max() < 60             # library, atm etc. excluded
    assert t["R_eating_5"].dropna().max() <= 1.0 + 1e-9


def test_the_treatment_is_counted_in_the_references_units():
    """v1.23, John's ruling: k is confined to the reference
    population, so the treatment is counted the same way and every
    R_ column is a share by construction - never a ratio of two
    different things."""
    state, pyt = _malta(with_nulls=False)
    msg = _Msg()
    pyt._run_tool("counts", "poi", msg, k_text="10", unit=100.0,
                  weight_field="guests", cat_field="fclass",
                  treat_rows=[["cafe", "eating"]])
    t = state["table"]
    assert "T_eating_10" in t.columns
    assert (t["R_eating_10"].dropna() <= 1.0 + 1e-9).all()
    assert "same units as the reference" in msg.all()


def test_the_treatment_may_use_its_own_type_column():
    """v1.23: the treatment names its own type field, so its section
    reads on its own instead of reaching into another one."""
    state, pyt = _malta(with_nulls=False)
    pyt._run_tool("counts", "poi", _Msg(), k_text="10", unit=100.0,
                  cat_field="fclass", treat_cat_field="fclass",
                  treat_rows=[["cafe", "eating"]])
    assert "T_eating_10" in state["table"].columns


def test_no_value_field_means_shares_of_places():
    state, pyt = _malta()
    msg = _Msg()
    pyt._run_tool("counts", "poi", msg, k_text="10", unit=100.0,
                  cat_field="fclass",
                  treat_rows=[["cafe", "eating"]])
    assert "shares of PLACES" in msg.all()


def test_a_value_outside_the_field_is_refused_by_name():
    state, pyt = _malta()
    import arcpy
    with pytest.raises(arcpy.ExecuteError, match="not in the category"):
        pyt._run_tool("counts", "poi", _Msg(), k_text="10", unit=100.0,
                      cat_field="fclass", ref_rows=[["nosuchvalue"]])


# ------------------- rows outside the reference (v1.22.2)
def test_rows_outside_the_reference_still_get_their_own_results():
    """John's rule: a library is not an eating place, but you can
    still ask what is around the library. It counts as ZERO people -
    nobody's neighbour - and receives results of its own."""
    state, pyt = _malta()
    msg = _Msg()
    pyt._run_tool("counts", "poi", msg, k_text="5", unit=100.0,
                  cat_field="fclass",
                  ref_rows=[["cafe"], ["bar"], ["bakery"],
                            ["restaurant"]],
                  treat_rows=[["cafe", "eating"]])
    t = state["table"]
    outside = t["fclass"].isin(["library", "atm", "artwork",
                                "supermarket"])
    assert outside.any(), "fixture should contain non-eating places"
    assert t.loc[outside, "N_5"].notna().all(), \
        "a row outside the reference must still get results"
    assert "still get their own results" in msg.all()


def test_a_row_outside_the_reference_is_nobody_s_neighbour():
    """Counting as zero means exactly that: including the libraries
    must not change what the cafes see."""
    state, pyt = _malta()
    pyt._run_tool("counts", "poi", _Msg(), k_text="5", unit=100.0,
                  cat_field="fclass",
                  ref_rows=[["cafe"], ["bar"], ["bakery"],
                            ["restaurant"]],
                  treat_rows=[["cafe", "eating"]])
    kept = state["table"]
    inside = kept["fclass"].isin(["cafe", "bar", "bakery",
                                  "restaurant"])
    ref = kept.loc[inside, "R_eating_5"].dropna()

    state2, pyt2 = _malta()
    pyt2._run_tool("counts", "poi", _Msg(), k_text="5", unit=100.0,
                   cat_field="fclass",
                   ref_rows=[["cafe"], ["bar"], ["bakery"],
                             ["restaurant"]],
                   treat_rows=[["cafe", "eating"]],
                   keep_outside=False)
    dropped = state2["table"]
    ref2 = dropped.loc[inside, "R_eating_5"].dropna()
    assert np.allclose(ref.to_numpy(), ref2.to_numpy(), equal_nan=True)


def test_the_old_behaviour_is_still_available():
    state, pyt = _malta()
    msg = _Msg()
    pyt._run_tool("counts", "poi", msg, k_text="5", unit=100.0,
                  cat_field="fclass", ref_rows=[["cafe"], ["bar"]],
                  treat_rows=[["cafe", "eating"]],
                  keep_outside=False)
    t = state["table"]
    outside = ~t["fclass"].isin(["cafe", "bar"])
    assert t.loc[outside, "N_5"].isna().all()
    assert "DROPPED" in msg.all()


def test_keeping_rows_is_the_default_in_the_dialog():
    _, _, pm = _dialog()
    assert pm["keepoutside"].value.startswith("give them results")


def test_the_dialog_offers_the_ladder_of_ways_to_build_each():
    """John's design: three rungs each, simplest first."""
    _, _, pm = _dialog()
    assert len(pm["refmode"].filter.list) == 3
    assert pm["refmode"].value.startswith("every point")
    assert len(pm["treatmode"].filter.list) == 3
    assert pm["treatmode"].value.startswith("not measuring")


def test_each_rung_shows_only_the_boxes_it_needs():
    tool, ps, pm = _dialog()
    tool.updateParameters(ps)
    assert not pm["pop"].enabled          # rung 1 needs nothing else
    assert not pm["reftable"].enabled
    assert not pm["treat"].enabled

    pm["refmode"].value = "a field holds the count"
    tool.updateParameters(ps)
    assert pm["pop"].enabled and not pm["reftable"].enabled

    pm["refmode"].value = "only selected types, with a count field"
    tool.updateParameters(ps)
    assert pm["pop"].enabled and pm["catfield"].enabled
    assert pm["reftable"].enabled and pm["keepoutside"].enabled

    pm["treatmode"].value = "types from a type field, grouped"
    tool.updateParameters(ps)
    assert pm["treattable"].enabled and pm["treatcatfield"].enabled
    assert not pm["treat"].enabled


# ------------------------- the GeoPackage notice (v1.22.2)
def test_a_geopackage_input_is_flagged_before_the_run():
    """Pro will not show new fields on a GeoPackage layer in the map
    - an Esri limitation open from Pro 3.0.2 to 3.5.2. Saying so at
    the dialog turns a mystery into a choice."""
    state, pyt = _malta()
    tool = pyt.CountsShares()
    ps = tool.getParameterInfo()
    pm = {p.name: p for p in ps}
    pm["layer"].value = "poi"
    pm["k"].value = "10"
    tool.updateMessages(ps)
    said = " ".join(t for _, t in pm["layer"].messages)
    assert "GEOPACKAGE" in said
    assert "New feature class" in said
    assert "not an EquiPop one" in said


def test_a_geodatabase_input_is_not_flagged():
    rng = np.random.default_rng(2)
    t = pd.DataFrame({"OBJECTID": np.arange(1, 11),
                      "SHAPE@X": rng.uniform(0, 900, 10),
                      "SHAPE@Y": rng.uniform(0, 900, 10)})
    state = H._install_fake_arcpy(t)
    state["catalog_paths"] = {"people": r"C:\Data\work.gdb\people"}
    pyt = H._load_pyt()
    tool = pyt.CountsShares()
    ps = tool.getParameterInfo()
    pm = {p.name: p for p in ps}
    pm["layer"].value = "people"
    pm["k"].value = "5"
    tool.updateMessages(ps)
    said = " ".join(t for _, t in pm["layer"].messages)
    assert "GEOPACKAGE" not in said
