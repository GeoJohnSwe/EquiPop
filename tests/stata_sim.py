# -*- coding: utf-8 -*-
"""stata_sim.py - the Python half of the shipped Stata files, run
without Stata (v1.62.1, for the SSC submission).

Stata reaches EquiPop through `sfi`, its Python bridge. Everything the
.ado and .do files do in Python goes through five sfi calls: read a
variable, add one, store into it, read or set a local, print. This
stands in for exactly those, over a pandas frame, so the blocks can be
exec'd as SHIPPED - the text between `python:` and `end` - against the
shipped test data.

What it cannot check, stated so nobody mistakes its reach: Stata's own
half - syntax parsing, macro expansion, marksample. tests/
test_stata_ado.py reads the .ado for those. This proves that what the
Python half computes is what the help and the showcase say it is.
"""
from __future__ import annotations

import os
import sys
import types

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATA = os.path.join(ROOT, "stata")
#: What sfi hands Python for a missing numeric value.
SYSMISS = 8.98846567431158e307


class StataError(Exception):
    """SFIToolkit.error(rc) - Stata would stop the command here."""


class _State:
    df: pd.DataFrame = pd.DataFrame()
    locals: dict = {}
    out: list = []
    err: list = []


def _sfi():
    st = _State

    class Data:
        @staticmethod
        def get(var, obs=None, selectvar=None, valuelabel=False,
                missingval=None):
            a = st.df[var].to_numpy(float)
            v = np.where(np.isnan(a), SYSMISS if missingval is None
                         else missingval, a)
            return v.tolist()

        @staticmethod
        def getVarCount():
            return st.df.shape[1]

        @staticmethod
        def getVarName(i):
            return st.df.columns[i]

        @staticmethod
        def addVarDouble(name):
            if name in st.df.columns:
                raise ValueError(f"variable {name} already defined")
            st.df[name] = np.nan

        @staticmethod
        def store(var, obs, val):
            assert obs is None, "the shipped code stores whole columns"
            v = np.asarray(val, dtype=object)
            if any(x is None for x in v):
                # what Stata does - BACKLOG 173
                raise ValueError("the specified value should be a "
                                 "numeric value")
            a = v.astype(float)
            st.df[var] = np.where(a >= SYSMISS, np.nan, a)

    class Macro:
        @staticmethod
        def getLocal(name):
            return st.locals.get(name, "")

        @staticmethod
        def setLocal(name, value):
            st.locals[name] = str(value)

    class SFIToolkit:
        @staticmethod
        def displayln(s=""):
            st.out.append(str(s))

        @staticmethod
        def display(s=""):
            st.out.append(str(s))

        @staticmethod
        def errprintln(s=""):
            st.err.append(str(s))

        @staticmethod
        def error(rc):
            raise StataError(rc)

        @staticmethod
        def stata(cmd):
            words = cmd.split()
            if words[:2] == ["capture", "drop"]:
                st.df.drop(columns=[w for w in words[2:]
                                    if w in st.df.columns], inplace=True)
                return
            raise NotImplementedError(cmd)

    mod = types.ModuleType("sfi")
    mod.Data, mod.Macro, mod.SFIToolkit = Data, Macro, SFIToolkit
    return mod


def load_test_data():
    """stata/equipop_test_data.dta, as Stata would have it in memory."""
    return pd.read_stata(os.path.join(STATA, "equipop_test_data.dta"),
                         convert_categoricals=False)


def blocks(path):
    """Every `python:` ... `end` block in a Stata file, as text."""
    lines = open(path, encoding="utf-8").read().splitlines()
    out, i = [], 0
    while i < len(lines):
        if lines[i].strip().startswith("python:") and \
                lines[i].strip() == "python:":
            j = i + 1
            while lines[j].rstrip() != "end":
                j += 1
            out.append("\n".join(lines[i + 1:j]))
            i = j
        i += 1
    return out


def start(df):
    """A fresh session over `df`; returns (namespace, state)."""
    _State.df = df.copy()
    _State.locals, _State.out, _State.err = {}, [], []
    sys.modules["sfi"] = _sfi()
    return {"__name__": "__stata__"}, _State


def run_block(code, ns):
    exec(compile(code, "<stata python block>", "exec"), ns)
    return ns
