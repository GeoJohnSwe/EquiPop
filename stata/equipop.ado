*! equipop v1.35.1  -  k-nearest neighbour context variables via EquiPop
*! Machine 1 (Counts and Shares). Adds, per requested k:
*!   N_<k>, Dist_<k>, and per treatment variable v: T_<v>_<k>, R_<v>_<k>
*! row-aligned to the dataset in memory. Radii r() give the same
*! columns named _r<r>.
*!
*! Requires Stata 17+, Python configured (python query), and the
*! Python package installed in that Python:  pip install equipop
*!
*! Syntax:
*!   equipop, x(varname) y(varname) treat(varlist) ///
*!            [k(numlist) r(numlist) unit(#) weight(varname) ///
*!             selfpot(#) replace]
*! Give k() and/or r().
*!
*! Example:
*!   use stata_test_data, clear
*!   equipop, x(X_local) y(Y_local) treat(HighEdu) k(50 200) unit(100)
*!   regress ValFloat R_HighEdu_200
*!
*! The command was called equipop_knn up to v1.34. That name still
*! works and forwards here (equipop_knn.ado), because radius runs
*! exist and asking for a radius under a _knn name reads oddly.

program define equipop
    version 17
    syntax , X(varname numeric) Y(varname numeric) ///
             TREAT(varlist numeric) ///
             [K(numlist integer >0) R(numlist >0) ///
              Unit(real 100) Weight(varname numeric) ///
              SELFpot(real 1) REPLACE]

    * BACKLOG 113. Stata inherited the 1.29.5 self-potential
    * default of 1.0 with no way to reach 0 - and Stata is the
    * door published work goes through, so it was the one door
    * that could not reproduce a pre-1.29.5 result. selfpot(0)
    * restores the old numbers exactly.
    if `selfpot' < 0 | `selfpot' > 1 {
        display as error "selfpot() must lie between 0 and 1"
        exit 198
    }

    if "`k'" == "" & "`r'" == "" {
        display as error "give k() and/or r()"
        exit 198
    }

    * drop pre-existing result variables if replace was asked
    if "`replace'" != "" {
        if "`k'" != "" {
            foreach kk of numlist `k' {
                capture drop N_`kk' Dist_`kk'
                foreach v of varlist `treat' {
                    capture drop T_`v'_`kk' R_`v'_`kk'
                }
            }
        }
        if "`r'" != "" {
            foreach rr of numlist `r' {
                * BACKLOG 113: `rl' is the underscore-safe name -
                * r=1.5 becomes r1_5, because a dot cannot appear in
                * a Stata variable name. It was computed here and
                * then never used, so `replace` silently failed to
                * drop anything for any DECIMAL radius.
                local rl : subinstr local rr "." "_", all
                capture drop N_r`rl'
                foreach v of varlist `treat' {
                    capture drop T_`v'_r`rl' R_`v'_r`rl'
                }
            }
        }
    }

    * BACKLOG 172. Every option is passed BY NAME. Up to v1.34 this
    * was a positional call, and that is how the door broke: v1.29.5
    * added selfpot() to the syntax line and to the call and left the
    * Python def with seven parameters, so an eight-argument call
    * raised TypeError before EquiPop was ever reached. A named call
    * cannot be got wrong by adding a box, cannot be got wrong by
    * ORDER, and names a mistake out loud instead of shifting every
    * later argument one place. Same medicine as BACKLOG 169.
    python: _equipop_machine1(x="`x'", y="`y'", treat="`treat'",     ///
        k="`k'", r="`r'", unit=`unit', weight="`weight'",            ///
        selfpot=`selfpot')

    display as result "equipop: done - new variables added " ///
        "(N_*, Dist_*, T_*, R_* for k = `k' r = `r')"
end

version 17
python:
# --- thin sfi glue; all computation lives in equipop.stata_bridge ----
# NOTE: this block is the only part that cannot be tested inside
# Stata, so it is kept deliberately minimal. What CAN be checked
# outside Stata is checked, by tests/test_stata_ado.py: that this
# block parses, that the call above matches this signature, that no
# name is read here that nothing defines, and that the keywords
# handed to knn_to_rows still exist in the package.
from sfi import Data, SFIToolkit
import numpy as np


def _col(v):
    a = np.array(Data.get(v), dtype=float)
    a[a > 8.9e307] = np.nan          # Stata missings arrive huge
    return a


def _equipop_machine1(*, x, y, treat, k="", r="", unit=100.0,
                      weight="", selfpot=1.0):
    # KEYWORD-ONLY on purpose: a positional call raises TypeError
    # rather than quietly meaning something else.
    try:
        from equipop.stata_bridge import knn_to_rows, to_stata_values
    except ImportError:
        SFIToolkit.errprintln(
            "equipop is not installed in Stata's Python. In a terminal "
            "for that Python run: pip install equipop  "
            "(check which Python with -python query- in Stata).")
        SFIToolkit.error(198)
        return

    xs, ys = _col(x), _col(y)
    treats = {v: _col(v) for v in treat.split()}
    ks = [int(t) for t in k.split()] or None
    rs = [float(t) for t in r.split()] or None
    w = _col(weight) if weight else None

    res = knn_to_rows(xs, ys, ks, treat=treats, weight=w,
                      unit_size=float(unit), r_values=rs,
                      self_potential=float(selfpot))

    existing = [Data.getVarName(i) for i in range(Data.getVarCount())]
    for name, arr in res.items():
        if name in existing:
            SFIToolkit.errprintln(
                f"variable {name} already exists - use option replace")
            SFIToolkit.error(110)
            return
        Data.addVarDouble(name)
        # BACKLOG 173: to_stata_values, not a list comprehension here.
        # Stata refuses None for a missing number, and the conversion
        # belongs where the suite can test it.
        Data.store(name, None, to_stata_values(arr))
end
