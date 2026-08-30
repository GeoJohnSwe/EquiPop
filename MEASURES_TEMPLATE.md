# Adding a demographic measure — fill one block per measure

Machine 4 computes **a ratio of two groups over the same
k-neighbourhood**. To add a measure, that is all you have to specify:
who is on top, who is underneath, and what it means.

Fill in the blocks below and hand the file back. Anything you leave
blank I will ask about rather than guess.

---

## How to write the two halves

**Ages as a range**, optionally restricted by sex:

| you write | it means |
|---|---|
| `0-4` | ages 0 to 4, whichever sexes the folder has |
| `f:15-49` | women aged 15 to 49 |
| `65-` | 65 and over, open ended |
| `m:` | men, every age |
| `fm:20-39` | both sexes, 20 to 39 |

**WorldPop's bands are not all five years wide** — 0 is under-one
alone, 1 covers 1–4, then fives, and 90 is open. Write the ages you
mean and the selection takes care of it: `15-49` gives 15,20…45 and
does **not** reach into 50.

**Two ranges on one side** — as the dependency ratio needs — separate
them with a **comma**: `0-14,65-`, or `fm:0-14,65-` with a sex.

*(An earlier version of this file said to write `0-14 plus 65-`. That
was never supported. The comma form is.)*

---

## The four that exist

```
NAME:        child_woman_ratio
LABEL:       Child-woman ratio
NUMERATOR:   0-4
DENOMINATOR: f:15-49
```

```
NAME:        dependency_ratio
LABEL:       Dependency ratio
NUMERATOR:   0-14 plus 65-
DENOMINATOR: 15-64
```

```
NAME:        ageing_index
LABEL:       Ageing index
NUMERATOR:   65-
DENOMINATOR: 0-14
```

```
NAME:        sex_ratio
LABEL:       Sex ratio
NUMERATOR:   m:
DENOMINATOR: f:
```

---

## New measures — fill these in

```
NAME:        (lower case, underscores, e.g. old_age_dependency)
LABEL:       (what appears in the tick-box, e.g. Old-age dependency ratio)
NUMERATOR:   
DENOMINATOR: 
ABOUT:       (one or two sentences: what it measures, and what a
              reader should NOT conclude from it. This is printed in
              the log before the numbers, so it is where a caveat
              belongs.)
MULTIPLY BY: (blank = a plain ratio. Put 100 for "per hundred", 1000
              for "per thousand" — say which, because a dependency
              ratio is conventionally per 100 and a sex ratio per 100
              males, and the convention differs by measure.)
```

```
NAME:        
LABEL:       
NUMERATOR:   
DENOMINATOR: 
ABOUT:       
MULTIPLY BY: 
```

```
NAME:        
LABEL:       
NUMERATOR:   
DENOMINATOR: 
ABOUT:       
MULTIPLY BY: 
```

---

## Candidates worth considering

Computable from age–sex structure alone, so they need no new data:

- **Old-age dependency** — `65-` over `15-64`, separating the two ends
  the dependency ratio lumps together
- **Child dependency** — `0-14` over `15-64`, the other half
- **Potential support ratio** — `15-64` over `65-`, the dependency
  ratio inverted; demographers often prefer it because it does not
  divide by a small number in young populations
- **Sex ratio at working age** — `m:15-64` over `f:15-64`, which reads
  as labour migration rather than anything biological
- **Reproductive-age share** — `f:15-49` over everybody, the
  denominator of most fertility work in its own right
- **Youth bulge** — `15-24` over `15-64`, standard in political
  demography

---

## What still cannot be done, and why

**TFR, ASFR, crude birth and death rates, life expectancy.** They need
**vital events** — births, deaths — and an age–sex folder holds stock,
not flow. Adding them as tick-boxes that quietly computed something
else would be worse than their absence.

Two routes open them, and both are real:

- **A births raster in the folder.** It becomes an ordinary column and
  the machinery already works. But read the circularity note first:
  WorldPop *derives* births from the population surfaces using
  age-specific fertility rates, so births ÷ women partly reproduces
  its own input, and the spatial variation is largely where women of
  childbearing age live.
- **Two years of the same cohorts**, which already works — `f_15_2020`
  and `f_15_2026` are two columns on the same points. Cohort change
  carries real census information about survivorship, which is why it
  is the stronger route.

If you want either, say so and it becomes a different kind of measure
— a change between two columns rather than a ratio within one year —
which needs a small extension, not a new machine.
