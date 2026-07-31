"""
datasets.py - one-line data for every example in the Book (#19).

    from equipop.datasets import load
    g = load("gridby")          # the synthetic teaching city (dict)
    people, jobs = load("municipality")   # anonymised register pair
    berlin = load("berlin")     # the historical validation table
"""
import os
import numpy as np
import pandas as pd

_HERE = os.path.dirname(__file__)
_DATA = os.path.join(_HERE, "data")   # ships in the wheel


def load(name: str, **kw):
    if name == "gridby":
        from equipop.gridby import gridby
        return gridby(**kw)
    if name == "municipality":
        p = pd.read_csv(os.path.join(_DATA, "people_syn.csv"))
        j = pd.read_csv(os.path.join(_DATA, "jobs_syn.csv"))
        print("[datasets] anonymised municipality pair (joint isometry; "
              "results identical to the register originals)")
        return p, j
    if name == "berlin":
        try:
            return pd.read_excel(os.path.join(_DATA,
                                              "berlin_example.xlsx"))
        except ImportError:
            raise ImportError(
                "The Berlin table is an Excel file and pandas needs "
                "openpyxl to read one. Run:  pip install openpyxl  "
                "(EquiPop does not require it, because this is the "
                "only dataset that needs it.)")
    if name == "stata_test":
        p = os.path.join(_HERE, "..", "stata", "stata_test_data.dta")
        if not os.path.exists(p):
            raise FileNotFoundError(
                "stata_test_data.dta belongs to the Stata door and is "
                "not shipped in the pip package - it comes with the "
                "source archive (the .tar.gz on GitHub) and with the "
                "repository, in stata/. The other datasets - gridby, "
                "municipality, berlin - are installed with the "
                "package and need no files.")
        return pd.read_stata(p)
    raise ValueError(f"unknown dataset '{name}': gridby / municipality "
                     "/ berlin / stata_test")
