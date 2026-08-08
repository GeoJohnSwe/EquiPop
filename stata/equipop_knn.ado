*! equipop_knn v1.0  -  k-nearest neighbour context variables via EquiPop (Python)
*! Adds, per requested k: N_<k>, Dist_<k>, and per treatment variable v:
*! T_<v>_<k>, R_<v>_<k>  -  row-aligned to the dataset in memory.
*! Requires Stata 17+, Python configured (python query), and the Python
*! package installed in that Python:  pip install equipop
*!
*! Syntax:
*!   equipop_knn, x(varname) y(varname) treat(varlist) ///
*!                [k(numlist) r(numlist) unit(#) weight(varname) replace]
*! Give k() and/or r(): r() are metric radii -> N_r<r>, T_<v>_r<r>, R_<v>_r<r>.
*!
*! Example:
*!   use stata_test_data, clear
*!   equipop_knn, x(X_local) y(Y_local) treat(HighEdu) k(50 200) unit(100)
*!   regress ValFloat R_HighEdu_200

program define equipop_knn
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

    python: _equipop_knn("`x'", "`y'", "`treat'", "`k'", `unit', "`weight'", "`r'", `selfpot')
    display as result "equipop_knn: done - new variables added " ///
        "(N_*, Dist_*, T_*, R_* for k = `k' r = `r')"
end

version 17
python:
# --- thin sfi glue; all computation lives in equipop.stata_bridge ----
# NOTE: this block is the only part that cannot be tested outside
# Stata; it is kept deliberately minimal.
from sfi import Data, SFIToolkit
import numpy as np

def _equipop_knn(xvar, yvar, treatvars, klist, unit, wvar, rlist=""):
    try:
        from equipop.stata_bridge import knn_to_rows
    except ImportError:
        SFIToolkit.errprintln(
            "equipop is not installed in Stata's Python. In a terminal "
            "for that Python run: pip install equipop  "
            "(check which Python with -python query- in Stata).")
        SFIToolkit.error(198)

    def col(v):
        a = np.array(Data.get(v), dtype=float)
        a[a > 8.9e307] = np.nan          # Stata missings arrive huge
        return a

    x, y = col(xvar), col(yvar)
    treats = {v: col(v) for v in treatvars.split()}
    ks = [int(t) for t in klist.split()]
    rs = [float(t) for t in rlist.split()]
    w = col(wvar) if wvar else None

    res = knn_to_rows(x, y, ks, treat=treats, weight=w, unit_size=unit,
                      r_values=rs, self_potential=float(selfpot))

    for name, arr in res.items():
        if name in [Data.getVarName(i) for i in range(Data.getVarCount())]:
            SFIToolkit.errprintln(
                f"variable {name} already exists - use option replace")
            SFIToolkit.error(110)
        Data.addVarDouble(name)
        Data.store(name, None,
                   [v if np.isfinite(v) else None for v in arr])
end
