# Rates and life expectancy from an age pyramid: the formulas

*EquiPop machine 4, Spatial Demographic Analysis, since 1.60.0. This
document matches 1.61.2. It is kept identical to
`equipop/METHODS_RATES.md` inside the installed package.*

An age-and-sex population raster (WorldPop, for example) counts people.
It holds no births and no deaths, so no rate can be *measured* from it.
Machine 4 **estimates** rates and life expectancy from each
neighbourhood's age pyramid, read against the pyramid of the
neighbourhood's nation. The nation's age patterns of death and birth
come from UN World Population Prospects 2024. The results are
model-based predictors and should be published as such.

This document gives every formula EquiPop uses, the assumptions behind
each, and what the run checks.

---

## 1. Notation

**The neighbourhood** is the *k* nearest people to an origin cell. The
analysis grid groups people into cells first. When the cell that
reaches *k* holds more people than are needed, it contributes only
the fraction needed. That same fraction applies to every count below,
so ratios between counts are unaffected.

**Age bands** are WorldPop's: 0, 1–4, 5–9, 10–14, …, 85–89, 90+.
- *b* is a band and *a* is the band a life expectancy starts from.
- The open top band holds any older bands the folder carries.
- *n_b* is the width of band *b*.

**Counts in the neighbourhood**, for the sex chosen in box 2d (both,
women or men):

| Symbol | Meaning |
|---|---|
| S_b | people in band b |
| W_x | women aged x to x+4, for x = 10, 15, …, 50 |
| C | children aged 0–4, both sexes |
| N | everybody (the neighbourhood's own population) |

**The nation.** Each item is either the folder's own total for that
country or taken from WPP 2024, as marked.

| Symbol | Meaning | Source |
|---|---|---|
| P_b | people in band b | the folder's own total |
| C_nat | children aged 0–4 | the folder's own total |
| W_nat,x | women aged x to x+4 | the folder's own total |
| l_b | survivors to the start of band b, radix 1 | WPP 2024 |
| L_b | person-years lived in band b (all from 90 on in the top band) | WPP 2024 |
| m_b | the band death rate, (l_b − l_{b+1}) / L_b | WPP 2024 |
| f_x | births per woman per year at age x to x+4 | WPP 2024 |
| TFR_nat | the total fertility rate, 5 · Σ_x f_x | WPP 2024 |
| e_nat(a) | life expectancy at a, Σ_{b≥a} L_b / l_a | WPP 2024 |

The national pyramid P is the **folder's own total**, not WPP's.
WorldPop is aligned to the UN's totals, so reading a neighbourhood
against the same source's national pyramid cancels the source's own
habits, such as age heaping or overstated old ages, wherever they are
national. This needs whole countries. Section 6 describes the warning.

---

## 2. Life expectancy at a: e60, and e50, e30 and e0 marked unreliable

If every cohort had started equally large and nobody moved, the
pyramid would be a life table: the people in band *b* would stand to
those in band *a* as L_b stands to L_a. Births have not been constant,
so the local pyramid is read **relative to the nation's**. The
nation's own birth history then cancels out wherever it is shared:

    ρ_b  =  (S_b / S_a) / (P_b / P_a)          for b ≥ a

    e(a) =  Σ_{b≥a}  L_b · ρ_b  /  l_a

A neighbourhood shaped exactly like its nation has ρ_b = 1 and gets
the nation's e(a). A neighbourhood with relatively more old people
gets a longer life expectancy.

**Assumption:** the local and national pyramids differ only through
survival. Migration and local differences in past births also move ρ.
- From 60, both effects are usually small next to survival.
- Below 60 they are not: a growing or in-migrating neighbourhood looks
  like one with high mortality. That is why e50, e30 and e0 carry a
  `u` and are marked UNRELIABLE. Use them as predictors only.

**Why e0 goes furthest wrong.** Write s_b = S_b / P_b, the
neighbourhood's share of the nation's people in band b. Then

    e(0)  =  Σ_b L_b · s_b  /  (s_0 · l_0)

Every band is divided by the neighbourhood's share of the nation's
INFANTS. A neighbourhood with half as large a share of infants as of
everybody else gets twice the national e0, and one with twice as large
a share gets half of it. Fertility, migration of young families and
age reporting move s_0; mortality hardly does. So e0u behaves like the
inverse of a relative birth rate: its map looks like an upside-down
TFR map. From 60 the bands compared are neighbours, so survival
dominates the ratio.

**Worked example, Turkey 2020.** The WPP life table and a whole-country
folder's totals are real; the neighbourhood counts are made up: 200,
170, 110, 70, 40, 18 and 6 people aged 60–64 … 90+, out of k = 5,000.

| Band | 60–64 | 65–69 | 70–74 | 75–79 | 80–84 | 85–89 | 90+ | Sum |
|---|---|---|---|---|---|---|---|---|
| L_b / l_60 | 4.86 | 4.46 | 3.90 | 3.14 | 2.10 | 1.04 | 0.40 | 19.89 = national e60 |
| ρ_b | 1.000 | 1.018 | 0.996 | 0.934 | 0.840 | 0.742 | 0.609 | |
| L_b ρ_b / l_60 | 4.86 | 4.55 | 3.88 | 2.93 | 1.77 | 0.77 | 0.24 | 19.0 = local e60 |

---

## 3. Total fertility rate and crude birth rate

The children under five, set against the births the neighbourhood's
women would have had at the nation's rates:

    E     =  Σ_x  W_x · f_x                       (births a year predicted)
    E_nat =  Σ_x  W_nat,x · f_x

    λ     =  (C / E) / (C_nat / E_nat)

    TFR   =  λ · TFR_nat
    CBR   =  1000 · λ · E / N                      (births a year per 1,000)

λ is the neighbourhood's fertility relative to the nation's. It
assumes the same age pattern of fertility and the same survival of
children under five as the nation. Reading C_nat / E_nat from the same
folder cancels national under-counting of young children.

---

## 4. Crude death rate

Below 60, the nation's death rates are used. From 60, they are scaled
by θ so that the band life table from 60 gives the neighbourhood's own
e60 relative to the nation's:

    e60(θ)  =  the life expectancy at 60 of the band table with rates θ·m_b, b ≥ 60
               (a = n_b/2 in each band, the open band lives l/m)

    θ solves  e60(θ) = (e(60) / e_nat(60)) · e60(1)        (by bisection)

    m*_b  =  m_b        for b < 60
          =  θ · m_b    for b ≥ 60

    CDR   =  1000 · Σ_b S_b · m*_b  /  Σ_b S_b

---

## 5. Whose nation: each person's own (the default since 1.61.0)

A neighbourhood near a border holds people of two or more countries.
There are two rules (box 2e, `vital_reference=`):

- **`own` (the default): each person against their own country.**
  Each pixel carries its own country's figures (iso3 from the WorldPop
  file name).
- **`cell`: the whole neighbourhood against the country of its cell.**
  The cell takes the country of the input point nearest its centre.
  This was EquiPop's rule up to 1.60.3, and it is sections 2–4 with
  one nation.

Under `own`, let *c* index countries, and S_{b,c}, W_{x,c}, C_c the
neighbourhood's people of country *c*. Every national quantity carries
its country. The pooled estimators are:

**Life expectancy**

    e(a)  =  Σ_c Σ_{b≥a}  S_{b,c} · (P_{a,c} / P_{b,c}) · (L_{b,c} / l_{a,c})
             ─────────────────────────────────────────────────────────────
                               Σ_c  S_{a,c}

**TFR and CBR**

    E_c  =  Σ_x  W_{x,c} · f_{x,c}          r_c  =  C_nat,c / E_nat,c

    λ    =  C  /  Σ_c E_c · r_c              (children there / children their own
                                              nations' rates lead one to expect)

    TFR  =  λ · Σ_c E_c · TFR_nat,c  /  Σ_c E_c
    CBR  =  1000 · λ · Σ_c E_c / N

**CDR**

    m_mix(b) =  Σ_c S⁶⁰⁺_c · m_{b,c}  /  Σ_c S⁶⁰⁺_c       for b ≥ 60
                (S⁶⁰⁺_c: the people of country c aged 60 and over)

    e_ref(60) =  Σ_c S_{60,c} · e_nat,c(60)  /  Σ_c S_{60,c}

    θ solves  e60(θ · m_mix) = (e(60) / e_ref(60)) · e60(m_mix)

    CDR  =  1000 · [ Σ_c Σ_{b<60} S_{b,c} m_{b,c}  +  θ · Σ_c Σ_{b≥60} S_{b,c} m_{b,c} ]
            ───────────────────────────────────────────────────────────────────────
                                   Σ_c Σ_b S_{b,c}

**Three properties, each tested:**
1. **Within one country, `own` is exactly `cell`.** Each pooled formula
   reduces to the one in sections 2–4, so nothing changes away from a
   border.
2. **People shaped like their own nation are read as their own
   nation.** If each country's people in a neighbourhood follow that
   country's pyramid, then:
   - e(a) is the S_a-weighted average of the national e(a);
   - TFR is the exposure-weighted average of the national TFR;
   - the CDR counts the deaths at each nation's own rates.

   A border neighbourhood therefore lands *between* the nations, never
   outside them. Under `cell` it can land outside: people of the
   neighbouring country are read as an oddly shaped pyramid of the
   cell's country.
3. **Every quantity is a sum over people**, so each pixel carries its
   country's coefficients and the neighbourhood sums are the pooled
   estimators. There is no per-country bookkeeping and no extra cost.

A country with no WPP table contributes to none of the sums: its
people are left out rather than read against another nation.

---

## 6. What the run checks and says

**The national life tables (WPP 2024).**
- They are built from WPP's single-year death rates:
  q = m / (1 + (1 − a)m), with a = ½ except in the first year of life.
  There a0 follows Andreev & Kingkade (2015), the Human Mortality
  Database rule (for both sexes, the mean of the women's and men's
  rules).
- The open 100+ interval lives l/m, and the table is then summed into
  WorldPop's bands.
- The result is checked against WPP's own e0 and differs by at most
  0.05 years.
- The table ships with its SHA-256, which is checked when it first
  loads.

**The size of k.**
- Below k = 5,000 the oldest bands hold a handful of people, so the
  log warns. 5,000 is the usual floor for small-area life expectancy
  (Eayres & Williams 2004).
- TFR and CBR are steadier at small k.
- **Why one neighbourhood for every band, and not k people per age
  band** (the usual design when deaths are counted):
  - This method has no deaths. All its information is in the MIX of
    ages within one neighbourhood, so every band must come from the
    same people.
  - If each band had its own k nearest, every band would hold exactly
    k people and every ratio would be 1. The information would sit in
    how far one had to go to find them.
  - So the single neighbourhood must be large enough that its thinnest
    band is not one or two people. Aged 90 and over is about 0.2% of
    Turkey: about 10 people at k = 5,000, and 1 at k = 500.

**Whole countries.** The log warns when a country's folder total is
under 90% of WPP's population for it. The run's record keeps every
share as `vital.national_coverage`. A folder clipped to a region reads
that region as "the nation", so its rates are relative to the region.

**Complete pyramids.**
- A missing band is refused by name rather than read as nobody alive
  at that age.
- TFR and CBR count the children under five from one complete set:
  girls plus boys, or the both-sexes files. One sex alone is used only
  when the folder holds no files for the other sex.

**Point layers.** A blank cohort value is read as nobody, counted per
field and kept in the record. Text and negative values are refused.

---

## 7. How well it does on populations with known answers (1.60.0)

The test populations were built from WPP's Kenya 2020 schedules,
changed where stated, and the measures were recovered from the
pyramid alone:

| Measure | Test | Result |
|---|---|---|
| e60 | death rates 40% higher | 13.2 years, against a true 12.8 (the nation's is 15.6) |
| TFR and CBR | fertility 30% above or below Kenya's | within 4% |
| CDR | death rates from 60 half again as high | within 3% |
| e0 (unreliable) | births growing 3.0% a year against the nation's 2.2% | misses by more than ten years |

The e0 result is why e0 carries the flag. Validation against observed
small-area rates (Swedish municipalities, SCB) is open.

---

## 8. References

**Data.** United Nations, Department of Economic and Social Affairs,
Population Division (2024). *World Population Prospects 2024.* CC BY
3.0 IGO. Taken via the `wpp2024` R package 1.1-3. EquiPop's derived
table and how it was built are described in `THIRD_PARTY_NOTICES.md`.

**Methods.**
- Andreev, E. M. and Kingkade, W. W. (2015). Average age at death in
  infancy and infant mortality level: Reconsidering the Coale-Demeny
  formulas at current levels of low mortality. *Demographic Research*
  33(13), 363–390.
- Eayres, D. and Williams, E. S. (2004). Evaluation of methodologies
  for small area life expectancy estimation. *Journal of Epidemiology
  and Community Health* 58(3), 243.

**The code.** `equipop/doors/vital.py` holds the estimators,
`equipop/doors/demography.py` holds the pooling (`vital_own_groups`),
and `tools/make_wpp_reference.py` builds the national table.
