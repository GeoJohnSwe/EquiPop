*! equipop_knn v1.0  -  k-nearest neighbour context variables via EquiPop (Python)
*! Adds, per requested k: N_<k>, Dist_<k>, and per treatment variable v:
*! T_<v>_<k>, R_<v>_<k>  -  row-aligned to the dataset in memory.
*! Requires Stata 17+, Python configured (python query), and the Python
*! package installed in that Python:  pip install equipop
*!
*! Syntax:
*!   equipop_knn, x(varname) y(varname) treat(varlist) k(numlist) ///
*!                [unit(#) weight(varname) replace]
*!
*! Example:
*!   use stata_test_data, clear
*!   equipop_knn, x(X_local) y(Y_local) treat(HighEdu) k(50 200) unit(100)
*!   regress ValFloat R_HighEdu_200

program define equipop_knn
    version 17
    syntax , X(varname numeric) Y(varname numeric) ///
             TREAT(varlist numeric) K(numlist integer >0) ///
             [Unit(real 100) Weight(varname numeric) REPLACE]

    * drop pre-existing result variables if replace was asked
    if "`replace'" != "" {
        foreach kk of numlist `k' {
            capture drop N_`kk' Dist_`kk'
            foreach v of varlist `treat' {
                capture drop T_`v'_`kk' R_`v'_`kk'
            }
        }
    }

    python: _equipop_knn("`x'", "`y'", "`treat'", "`k'", `unit', "`weight'")
    display as result "equipop_knn: done - new variables added " ///
        "(N_*, Dist_*, T_*, R_* for k = `k')"
end

version 17
python:
# --- thin sfi glue; all computation lives in equipop.stata_bridge ----
# NOTE: this block is the only part that cannot be tested outside
# Stata; it is kept deliberately minimal.
from sfi import Data, SFIToolkit
import numpy as np

def _equipop_knn(xvar, yvar, treatvars, klist, unit, wvar):
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
    w = col(wvar) if wvar else None

    res = knn_to_rows(x, y, ks, treat=treats, weight=w, unit_size=unit)

    for name, arr in res.items():
        if name in [Data.getVarName(i) for i in range(Data.getVarCount())]:
            SFIToolkit.errprintln(
                f"variable {name} already exists - use option replace")
            SFIToolkit.error(110)
        Data.addVarDouble(name)
        Data.store(name, None,
                   [v if np.isfinite(v) else None for v in arr])
end
