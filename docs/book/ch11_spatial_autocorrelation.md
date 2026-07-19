# 11. Spatial autocorrelation: clusters, hot spots, and one loud warning

## The idea

Earlier chapters ask *how unevenly* something is spread across a
town. This chapter asks a different, complementary question: *does
the map cluster?* Imagine cutting the map into tiles and looking at
each tile together with its immediate surroundings. Do high values
tend to sit next to other high values, forming patches — the way
house prices usually do? Do high and low alternate like a
checkerboard? Or, if you shuffled all the tiles randomly, would the
map look just the same?

The classic single-number answer is **Moran's I**, which runs from
roughly −1 to +1. A strongly positive I says "like sits with like":
the map is patchy, clustered. A strongly negative I says values
alternate — rare in social data, but it is what a perfect
checkerboard produces. An I near zero says the arrangement is
indistinguishable from shuffled tiles. Because a single global
number can hide a lot, Moran's I also comes in a **local** version,
usually called LISA (for *Local Indicators of Spatial Association*):
one value per square, telling you whether *that* square sits in a
patch of high values surrounded by high (labelled HH), low
surrounded by low (LL), or is a lonely outlier — a high square in
low surroundings (HL) or the reverse (LH). A close cousin, the
**Getis–Ord Gi\*** statistic, ranks every square on a hot-to-cold
scale, which is where "hot spot map" comes from.

All of these statistics need one ingredient decided in advance: a
formal answer to *"who counts as whose neighbour?"* — in the jargon,
a **weights matrix**. EquiPop's contribution is that this answer
comes from the same menu as everything else in the book: the k
nearest squares (with chapter 1's fair treatment of equal
distances), everyone within a radius, or distance-decay weights
where nearer squares count more. And, in the family style, every
statistic can be computed as a **profile across scales**.

![LISA clusters of the context share, and Moran's I by k](figs/ch11_lisa.png)

On Gridby, the LISA map finds exactly what the town was built with:
a red High-High cluster filling the east (where the planted minority
share is high, surrounded by more of the same), a blue Low-Low
cluster filling the west, and the boundary between them riding the
planted gradient, with the river visible as an edge. The grey
squares are those whose local pattern could plausibly be an accident
of shuffling — they fail the significance test explained below. The
right panel shows the scale profile of the global I, and it is the
doorway to this chapter's most important warning, saved for the
Pitfalls section.

## Cook it

Three calls cover the whole toolkit. The first builds the "who is
whose neighbour" matrix — here, each square's eight nearest squares.
The second computes the global Moran's I with a significance test.
The third computes the local version, one row per square.

```python
from equipop.autocorr import (build_weights, morans_i,
                              local_morans, local_g)

W = build_weights(out.EastWest, out.NorthSouth, mode="knn", k=8)
glob = morans_i(out.R_g_400, W, permutations=999, name="R_g_400")
lisa = local_morans(out.R_g_400, W, permutations=999)
gi   = local_g(out.R_g_400, W, star=True)
```

About that significance test: the p-values here come from
**permutation** — the computer literally shuffles the values across
the map hundreds of times and asks how often pure chance produces a
pattern as strong as the observed one. It is the "would shuffled
tiles look the same?" question, answered by actually shuffling. The
`lisa` table gives each square its local statistic `Ii`, its
quadrant label (HH, LL, HL or LH), and its shuffle-based p-value;
join it back to your results and map the significant quadrants, and
you have drawn the classic LISA cluster map.

## The dials

`mode` (knn / r / decay) and its size parameter; `row_standardize`
(on by default, meaning each square's neighbours share one unit of
influence between them; switch it off for the G statistics, which
prefer plain 0/1 weights); `permutations` and `seed` (the shuffling
is reproducible); and `autocorr_profile(df, cols)` for one I per
scale in a single call.

## Under the hood

For readers who compare software: the local Moran here uses the same
variance convention as the widely used PySAL `esda` library — the
module is cross-checked against it down to the ninth decimal for
LISA and the eighth for Gi\*, with one documented difference: our
k-nearest weights include equal-distance ties as a whole ring
(chapter 1's convention), where most libraries cut at exactly k.
Housekeeping is loud in the usual way: missing values are replaced
by the mean for the global statistic *with a printed count*, and a
square with no neighbours at all gets an honest NaN rather than a
silent zero.

## Pitfalls

**The loud warning, in full — please read this one.** Suppose you
feed a context share such as `R_g_1600` into Moran's I. Think about
what that column is: every square's value is an average over its
1,600 nearest people, and two squares a hundred metres apart share
almost all of those 1,600. Their values are therefore nearly
identical *by construction* — not because the town clusters, but
because the two neighbourhoods overlap. Smoothing a map always
makes it look clustered. On Gridby, the global I rises from 0.947
at k = 50 to 0.998 at k = 1,600; that rise is the smoothing, not
the town. The software detects context-share columns by their name
and prints a caution automatically. Measuring the autocorrelation
of a smoothed surface is perfectly legitimate — it answers "how far
does the smoothed structure reach?" — but it is a different question
from "does the raw residential pattern cluster?" For the latter,
analyse raw local shares instead. The entire pitfall is knowing
which of the two questions you are asking; the software makes sure
you cannot fail to ask it.
