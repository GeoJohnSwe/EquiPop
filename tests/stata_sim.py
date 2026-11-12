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
    chars: dict = {}
    varabbrev: bool = True      # Stata's default: -set varabbrev on-


def _resolve(name, columns, abbrev):
    """Which variable a NAME means to Stata.

    BACKLOG 473. The exact name if there is one. Otherwise, with
    -set varabbrev on- (the default), the ONE variable the name is the
    beginning of. That second rule is how -drop N_100- deletes N_1000.
    This stand-in used to drop exact names only, so it could not show
    the fault the real thing has.
    """
    cols = list(columns)
    if name in cols:
        return name
    if not abbrev:
        raise StataError(111)                 # variable not found
    hits = [c for c in cols if c.startswith(name)]
    if len(hits) == 1:
        return hits[0]
    raise StataError(111)                     # not found / ambiguous


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
        def dropVar(var):
            """By position or by exact name; anything else is refused,
            as sfi refuses a variable it cannot find."""
            if isinstance(var, (int, np.integer)):
                if not 0 <= int(var) < st.df.shape[1]:
                    raise ValueError(f"variable {var} out of range")
                name = st.df.columns[int(var)]
            elif var in st.df.columns:
                name = var
            else:
                raise ValueError(f"variable {var} not found")
            # not inplace=: pandas 3.1 deprecates it (BACKLOG 427, 496)
            st.df = st.df.drop(columns=[name])

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
            """-drop-, as Stata runs it: -capture- swallows the error,
            -novarabbrev- switches abbreviation off for the command,
            and without it a name is resolved by Stata's own rule."""
            words = cmd.split()
            capture = words[:1] == ["capture"]
            if capture:
                words = words[1:]
            abbrev = st.varabbrev
            if words[:1] == ["novarabbrev"]:
                abbrev, words = False, words[1:]
            if words[:1] != ["drop"]:
                raise NotImplementedError(cmd)
            try:
                gone = [_resolve(w, st.df.columns, abbrev)
                        for w in words[1:]]
            except StataError:
                if capture:
                    return
                raise
            st.df = st.df.drop(columns=sorted(set(gone)))

    class Characteristic:
        """The four names sfi has - and no others. The shipped code
        called getDta and setDta, which do not exist (BACKLOG 474);
        nothing stood in for the class, so nothing noticed."""

        @staticmethod
        def getDtaChar(name):
            return st.chars.get(("_dta", name), "")

        @staticmethod
        def setDtaChar(name, value):
            st.chars[("_dta", name)] = str(value)

        @staticmethod
        def getVariableChar(var, name):
            return st.chars.get((var, name), "")

        @staticmethod
        def setVariableChar(var, name, value):
            st.chars[(var, name)] = str(value)

    mod = types.ModuleType("sfi")
    mod.Data, mod.Macro, mod.SFIToolkit = Data, Macro, SFIToolkit
    mod.Characteristic = Characteristic
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
    _State.chars, _State.varabbrev = {}, True
    sys.modules["sfi"] = _sfi()
    return {"__name__": "__stata__"}, _State


def run_block(code, ns):
    exec(compile(code, "<stata python block>", "exec"), ns)
    return ns
