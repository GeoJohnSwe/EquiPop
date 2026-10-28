*! equipop_run v1.63.1  -  ONE command, the whole toolbox (since EquiPop 1.6).
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
         KFCA(real 0) RFCA(real 0) WPERM(real 199) ///
         SELFpot(real 1) REPLACE]

    * See equipop_knn.ado. selfpot(0) reproduces
    * pre-1.29.5 numbers exactly, in every engine.
    if `selfpot' < 0 | `selfpot' > 1 {
        display as error "selfpot() must lie between 0 and 1"
        exit 198
    }
    * BACKLOG 451, v1.63.1 (review of 1.63.0). unit(-1) reached the
    * engine and came back as a plausible table on a grid that does not
    * exist; unit(0) and unit(.) stopped inside Python. -equipop- has
    * refused these since 1.29.8; this command never did. missing()
    * first: Stata's . compares GREATER than every number, so a bare
    * <= 0 lets it through.
    if missing(`unit') | `unit' <= 0 {
        display as error "unit() is the cell size and must be a " ///
            "number greater than zero"
        exit 198
    }
    * wperm() is a COUNT of permutations: refused, not truncated, when
    * it is not a whole number of at least one (the same rule theta(k)
    * applies to its shuffles since 1.62.1). Zero would report p = 1
    * for every cell, which is not a p-value of anything.
    if missing(`wperm') | `wperm' < 1 | `wperm' != int(`wperm') {
        display as error "wperm() is the number of permutations for " ///
            "the LISA p-values and must be a whole number of 1 or " ///
            "more (default 199)"
        exit 198
    }

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
        `rfca', `rep', `selfpot', `wperm')
end

python:
from sfi import Data, SFIToolkit
import numpy as np
from equipop.stata_bridge import dispatch, to_stata_values

def _col(v):
    a = np.array(Data.get(v), dtype=float)
    a[a > 8.9e307] = np.nan
    return a

def _engine_takes_unit(unit):
    """BACKLOG 445, v1.63.0. A FRACTIONAL unit() needs engine 1.63.0 or
    newer: an older one rounds it somewhere (output coordinates, the
    effort engines' grid) and either stops with a lookup error or runs
    at the rounded size. eqp_min_engine stays where it is - a whole
    size loses nothing on an older engine (BACKLOG 331/385) - so the
    one case that needs the newer engine is refused here, in words.
    tests/test_fractional_cells.py runs this against a stand-in old
    engine. The same function is in equipop.ado."""
    u = float(unit)
    if u == int(u):
        return True
    try:
        from equipop import __version__ as eng
    except Exception:
        eng = "unknown"
    # leading digits of the first three parts; no regex, because a
    # backslash in an ado's python block is one more thing to escape
    nums = []
    for part in str(eng).split(".")[:3]:
        d = ""
        for ch in part:
            if not ch.isdigit():
                break
            d += ch
        nums.append(int(d) if d else -1)
    if len(nums) == 3 and tuple(nums) >= (1, 63, 0):
        return True
    SFIToolkit.errprintln(
        f"unit({u:g}): a fractional cell size needs the EquiPop engine "
        f"1.63.0 or newer, and this Python has {eng}. Run -equipop "
        "setup- to update it, or give a whole number.")
    return False


def _equipop_run(engine, xv, yv, treatv, valuesv, statss, ks, rs,
                 taus, unit, wv, dem, model, rt, fricf, demv, supf,
                 supcol, supx, supy, hl, reach, method, kfca, rfca,
                 rep, selfpot=1.0, wperm=199):
    if not _engine_takes_unit(unit):
        SFIToolkit.error(198)
        return
    kw = dict(unit_size=float(unit),
              self_potential=float(selfpot))
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
        # Stata refuses
        # None for a missing number. It had simply never been reached
        # here either, because it needs a missing RESULT to appear.
        Data.store(safe, None, to_stata_values(arr))
    SFIToolkit.displayln(
        f"equipop_run: engine {engine}, {len(res)} variables stored")
end
