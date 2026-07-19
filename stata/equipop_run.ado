*! equipop_run.ado - EquiPop 1.6: ONE command, the whole toolbox.
*! Syntax:
*!   equipop_run, engine(counts|stats|friction|slope|fca|lisa) x() y() [...]
*! Engines and their options:
*!   counts   : treat(varlist) k(numlist) r(numlist) [weight()]
*!   stats    : values(varlist) k(numlist) r(numlist) [stats(string)]
*!   friction : treat(varname) k(numlist) tau(numlist) [friction(path)]
*!   slope    : treat(varname) k(numlist) tau(numlist) dem(path)
*!              [model(tobler|linear) roundtrip]
*!   fca      : demandvar(varname) supply(path.csv/.dta/.sav)
*!              supplycol(name) halflife(#) [reach(decay|r|k)
*!              kfca(#) rfca(#) method(2sfca|3sfca)] -> A, J
*!   lisa     : values(varname) [k(#) = weight-knn, wperm(#)]
*!              -> LISA_<v>_Ii, LISA_<v>_quad (1=HH 2=LL 3=HL 4=LH),
*!                 LISA_<v>_p  (on cell means, loud)
*! Common: unit(#) weight(varname) replace
*! All results come back ROW-ALIGNED as new variables.

program define equipop_run
    version 17
    syntax , ENGINE(string) X(varname numeric) Y(varname numeric) ///
        [TREAT(varlist numeric) VALUES(varlist numeric) ///
         STATS(string) K(numlist integer >0) R(numlist >0) ///
         TAU(numlist >0) Unit(real 100) Weight(varname numeric) ///
         DEM(string) MODEL(string) ROUNDtrip FRICTION(string) ///
         DEMANDvar(varname numeric) SUPPLY(string) ///
         SUPPLYCOL(string) SUPPLYX(string) SUPPLYY(string) ///
         HALFlife(real 0) REACH(string) METHOD(string) ///
         KFCA(real 0) RFCA(real 0) WPERM(real 199) REPLACE]

    if "`model'" == ""     local model "tobler"
    if "`reach'" == ""     local reach "decay"
    if "`method'" == ""    local method "2sfca"
    if "`supplyx'" == ""   local supplyx "x"
    if "`supplyy'" == ""   local supplyy "y"
    if "`supplycol'" == "" local supplycol "supply"
    local rt = cond("`roundtrip'" != "", "1", "0")
    local rep = cond("`replace'" != "", "1", "0")

    python: _equipop_run("`engine'", "`x'", "`y'", "`treat'",       ///
        "`values'", "`stats'", "`k'", "`r'", "`tau'", `unit',       ///
        "`weight'", "`dem'", "`model'", `rt', "`friction'",         ///
        "`demandvar'", "`supply'", "`supplycol'", "`supplyx'",      ///
        "`supplyy'", `halflife', "`reach'", "`method'", `kfca',     ///
        `rfca', `rep', `wperm')
end

python:
from sfi import Data, SFIToolkit
import numpy as np
from equipop.stata_bridge import dispatch

def _col(v):
    a = np.array(Data.get(v), dtype=float)
    a[a > 8.9e307] = np.nan
    return a

def _equipop_run(engine, xv, yv, treatv, valuesv, statss, ks, rs,
                 taus, unit, wv, dem, model, rt, fricf, demv, supf,
                 supcol, supx, supy, hl, reach, method, kfca, rfca,
                 rep, wperm=199):
    kw = dict(unit_size=float(unit))
    kw["k_values"] = [int(t) for t in ks.split()] or None
    kw["r_values"] = [float(t) for t in rs.split()] or None
    kw["tau_values"] = [float(t) for t in taus.split()] or None
    if treatv:
        kw["treat"] = {v: _col(v) for v in treatv.split()}
    if wv:
        kw["weight"] = _col(wv)
    if engine == "lisa":
        vals = {v: _col(v) for v in valuesv.split()}
        kw["values"] = vals
        kw["w_k"] = int(ks.split()[0]) if ks.split() else 8
        kw["k_values"] = None
        kw["permutations"] = int(wperm)
    if engine == "stats":
        vals = {v: _col(v) for v in valuesv.split()}
        kw["values"] = vals
        wanted = statss.split() if statss else ["mean", "median", "gini"]
        kw["stats"] = {v: wanted for v in vals}
    if engine in ("friction", "slope"):
        kw["friction_file"] = fricf or None
        if engine == "slope":
            kw["dem"] = dem
            kw["model"] = model
            kw["roundtrip"] = bool(rt)
    if engine == "fca":
        kw["demand_arr"] = _col(demv)
        kw["supply_file"] = supf
        kw["supply_col"] = supcol
        kw["supply_x"], kw["supply_y"] = supx, supy
        kw["half_life_m"] = hl if hl > 0 else None
        kw["reach"], kw["method"] = reach, method
        kw["k_fca"] = kfca if kfca > 0 else None
        kw["r_fca"] = rfca if rfca > 0 else None

    res = dispatch(engine, _col(xv), _col(yv), **kw)
    for name, arr in res.items():
        safe = name.replace(".", "_")
        if rep:
            SFIToolkit.stata(f"capture drop {safe}")
        Data.addVarDouble(safe)
        Data.store(safe, None,
                   [v if np.isfinite(v) else None for v in arr])
    SFIToolkit.displayln(
        f"equipop_run: engine {engine}, {len(res)} variables stored")
end
