*! equipop v1.36  -  k-nearest neighbour context variables via EquiPop
*! Machine 1 (Counts and Shares). Adds, per requested k:
*!   N_<k>, Dist_<k>, and per treatment variable v: T_<v>_<k>, R_<v>_<k>
*! row-aligned to the dataset in memory. Radii r() give the same
*! columns named _r<r>. treat() is optional; without it you get the
*! neighbourhood size and reach alone.
*!
*! Requires Stata 17+, Python configured (python query), and the
*! Python package installed in THAT Python. See help equipop.
*!
*! v1.36 makes the command behave like a Stata command: [if] [in],
*! native [fweight=], returned results in r(), and prefix().

program define equipop, rclass
    version 17
    syntax [fweight] [if] [in], X(varname numeric) Y(varname numeric) ///
           [TREAT(varlist numeric) ///
            K(numlist integer >0) R(numlist >0) ///
            Unit(real 100) POP(varname numeric) PREFIX(string) ///
            SELFpot(real 1) REPLACE]

    * ---- the sample -------------------------------------------
    * John's ruling, 1.36: [if] and [in] restrict the ROWS THAT GET
    * RESULTS. They do NOT restrict who counts as a neighbour - that
    * is the reference-population ladder's job and it is a different
    * question. `equipop if urban==1` computes for urban origins,
    * and rural people still fill their neighbourhoods.
    *
    * novarlist matters: without it marksample also drops any row
    * with a missing value among the variables, which would quietly
    * shrink the population. Missing handling is EquiPop's own
    * (BACKLOG 168) and the two must not fight. His rule was: use
    * Stata's own commands where we can, not where it jeopardises
    * our code - this is the seam between the two.
    marksample touse, novarlist

    * ---- weights ----------------------------------------------
    * fweight is the honest Stata reading of an EquiPop weight:
    * "this row stands for N identical observations" IS a population
    * count in a cell. Stata validates it for us. But fweight demands
    * whole numbers and EquiPop supports fractional population on
    * purpose (WorldPop; machine 2 taking part of a cell), so pop()
    * remains for that case.
    local wvar ""
    if "`weight'" != "" {
        if "`pop'" != "" {
            display as error "give either [fweight=varname] or " ///
                "pop(varname), not both - they mean the same thing"
            exit 198
        }
        local wvar = trim(subinstr("`exp'", "=", "", 1))
    }
    else if "`pop'" != "" {
        local wvar "`pop'"
    }

    if `selfpot' < 0 | `selfpot' > 1 {
        display as error "selfpot() must lie between 0 and 1"
        exit 198
    }
    if "`k'" == "" & "`r'" == "" {
        display as error "give k() and/or r()"
        exit 198
    }
    if "`prefix'" != "" {
        capture confirm name `prefix'N_1
        if _rc {
            display as error "prefix() must begin a legal Stata " ///
                "variable name"
            exit 198
        }
    }

    * ---- drop what we are about to write ----------------------
    if "`replace'" != "" {
        if "`k'" != "" {
            foreach kk of numlist `k' {
                capture drop `prefix'N_`kk'
                capture drop `prefix'Dist_`kk'
                foreach v of varlist `treat' {
                    capture drop `prefix'T_`v'_`kk'
                    capture drop `prefix'R_`v'_`kk'
                }
            }
        }
        if "`r'" != "" {
            foreach rr of numlist `r' {
                * BACKLOG 113: `rl' is the underscore-safe name -
                * r=1.5 becomes r1_5, because a dot cannot appear in
                * a Stata variable name.
                local rl : subinstr local rr "." "_", all
                capture drop `prefix'N_r`rl'
                foreach v of varlist `treat' {
                    capture drop `prefix'T_`v'_r`rl'
                    capture drop `prefix'R_`v'_r`rl'
                }
            }
        }
    }

    * BACKLOG 172. Every option is passed BY NAME, and the receiving
    * function is keyword-only. Up to v1.34 this was a positional
    * call, and that is how the door broke for eleven releases: an
    * option was added to the syntax line and to the call, and the
    * def never heard of it. A named call cannot be got wrong by
    * ORDER and names a mistake out loud. Same medicine as 169.
    python: _equipop_machine1(x="`x'", y="`y'", treat="`treat'",     ///
        k="`k'", r="`r'", unit=`unit', weight="`wvar'",              ///
        selfpot=`selfpot', touse="`touse'", prefix="`prefix'")

    * ---- returned results -------------------------------------
    * BACKLOG 174. r(varlist) is the one that changes how the
    * command can be used: -regress y `r(varlist)'- and loops over
    * several k stop needing hand-written variable names.
    local created "`eqp_varlist'"
    quietly count if `touse'
    local n_origins = r(N)
    local n_missing = 0
    if "`created'" != "" {
        local first : word 1 of `created'
        quietly count if missing(`first') & `touse'
        local n_missing = r(N)
    }

    display as result "equipop: done - " ///
        "`: word count `created'' new variables, " ///
        "`n_origins' rows in sample, `n_missing' without results"

    return local cmd     "equipop"
    return local cmdline `"equipop `0'"'
    return local varlist "`created'"
    return local treat   "`treat'"
    return local k       "`k'"
    return local r       "`r'"
    return scalar unit      = `unit'
    return scalar selfpot   = `selfpot'
    return scalar N_origins = `n_origins'
    return scalar N_missing = `n_missing'
end

version 17
python:
# --- thin sfi glue; all computation lives in equipop.stata_bridge ----
# Keep this block as SMALL as possible. Code in here can only be run
# by Stata, so pytest cannot reach it - that is what let BACKLOG 172
# and 173 survive. Everything that can live in the package does.
# What must stay here is READ by tests/test_stata_ado.py.
from sfi import Data, Macro, SFIToolkit
import numpy as np


def _col(v):
    a = np.array(Data.get(v), dtype=float)
    a[a > 8.9e307] = np.nan          # Stata missings arrive huge
    return a


def _equipop_machine1(*, x, y, treat, k="", r="", unit=100.0,
                      weight="", selfpot=1.0, touse="", prefix=""):
    # KEYWORD-ONLY on purpose: a positional call raises TypeError
    # rather than quietly meaning something else.
    try:
        from equipop.stata_bridge import knn_to_rows, to_stata_values
    except ImportError:
        SFIToolkit.errprintln(
            "equipop is not installed in Stata's Python. Check which "
            "Python with -python query-, then install into THAT one. "
            "See help equipop.")
        SFIToolkit.error(198)
        return

    xs, ys = _col(x), _col(y)
    treats = {v: _col(v) for v in treat.split()} if treat.strip() else None
    ks = [int(t) for t in k.split()] or None
    rs = [float(t) for t in r.split()] or None
    w = _col(weight) if weight else None

    res = knn_to_rows(xs, ys, ks, treat=treats, weight=w,
                      unit_size=float(unit), r_values=rs,
                      self_potential=float(selfpot))

    # [if] [in]: computed for everyone, REPORTED for the sample.
    keep = _col(touse) > 0 if touse else None

    existing = [Data.getVarName(i) for i in range(Data.getVarCount())]
    made = []
    for name, arr in res.items():
        name = prefix + name
        if name in existing:
            SFIToolkit.errprintln(
                f"variable {name} already exists - use option replace")
            SFIToolkit.error(110)
            return
        vals = np.asarray(arr, dtype=float)
        if keep is not None:
            vals = np.where(keep, vals, np.nan)
        Data.addVarDouble(name)
        Data.store(name, None, to_stata_values(vals))
        made.append(name)

    Macro.setLocal("eqp_varlist", " ".join(made))
end
