# Third-party notices

EquiPop's own code is released under the MIT licence (see `LICENSE`).
EquiPop also carries third-party data that has a licence of its own.
That data is listed here, so anyone who redistributes EquiPop, or
publishes with it, can see what the data is and how to credit it.

This file travels at the top of the source archive and inside the
installed package (`equipop/THIRD_PARTY_NOTICES.md`). A test keeps the
two copies identical.

## UN World Population Prospects 2024: the national reference table

**Files**
- `equipop/data/wpp2024_reference.csv.xz`
- `equipop/data/wpp2024_reference.json`, which records the table's
  source, licence, method and SHA-256.

**Used for:** machine 4's rates and life expectancy (since 1.60.0) and
the whole-country check (since 1.60.2). The table holds national life
tables by WorldPop age band, fertility schedules and national
population, for 236 countries and areas, 2000–2030.

**Source.** United Nations, Department of Economic and Social Affairs,
Population Division (2024). *World Population Prospects 2024.* Taken
from the `wpp2024` R package, version 1.1-3 (2024-11-26),
<https://github.com/PPgp/wpp2024>. Estimates run to 2023, and the
medium variant is used from 2024.

**Licence.** Creative Commons Attribution 3.0 IGO (CC BY 3.0 IGO),
<https://creativecommons.org/licenses/by/3.0/igo/>.

**What EquiPop changed.** The table is derived from WPP rather than
copied from it. `tools/make_wpp_reference.py` builds it, the same
build always gives the same bytes, and the record holds the checksum.
The script:
- builds life tables from WPP's single-year death rates and sums them
  into WorldPop's age bands;
- groups the fertility pattern into five-year bands;
- sums national population over age;
- rounds every value to five significant digits.

The life tables agree with WPP's own life expectancy at birth to
within 0.05 years.

**Attribution when you publish results that use these measures:**

> United Nations, Department of Economic and Social Affairs, Population
> Division (2024). World Population Prospects 2024. Licensed under
> CC BY 3.0 IGO. National schedules as derived by EquiPop.

The United Nations has not reviewed or endorsed EquiPop or anything
EquiPop computes from this data.

## Methods named in the code

These are methods EquiPop uses, not third-party material it contains.
They are listed so the references are in one place. `CITATION.cff`
carries them as well.
- Andreev, E. M. and Kingkade, W. W. (2015). Average age at death in
  infancy and infant mortality level: Reconsidering the Coale-Demeny
  formulas at current levels of low mortality. *Demographic Research*
  33(13), 363–390. EquiPop uses it for the infant life-table factor
  a0.
- Eayres, D. and Williams, E. S. (2004). Evaluation of methodologies
  for small area life expectancy estimation. *Journal of Epidemiology
  and Community Health* 58(3), 243. EquiPop follows its population
  floor of 5,000 for small-area life expectancy.
