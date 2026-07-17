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
_TESTS = os.path.join(_HERE, "..", "tests", "data")


def load(name: str, **kw):
    if name == "gridby":
        import sys
        sys.path.insert(0, os.path.join(_HERE, "..", "examples"))
        from make_gridby import gridby
        return gridby(**kw)
    if name == "municipality":
        p = pd.read_csv(os.path.join(_TESTS, "people_syn.csv"))
        j = pd.read_csv(os.path.join(_TESTS, "jobs_syn.csv"))
        print("[datasets] anonymised municipality pair (joint isometry; "
              "results identical to the register originals)")
        return p, j
    if name == "berlin":
        return pd.read_excel(os.path.join(_TESTS, "berlin_example.xlsx"))
    if name == "stata_test":
        return pd.read_stata(os.path.join(_HERE, "..", "stata",
                                          "stata_test_data.dta"))
    raise ValueError(f"unknown dataset '{name}': gridby / municipality "
                     "/ berlin / stata_test")
