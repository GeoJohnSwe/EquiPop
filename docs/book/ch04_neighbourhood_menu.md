# 4. The neighbourhood definition menu

## The idea

The word "neighbourhood" quietly hides a decision, and this chapter
puts that decision in plain view. Whenever you draw a neighbourhood
around a person, you are choosing to hold *something* constant and
to let everything else vary. EquiPop makes the choice explicit and,
rather than forcing one answer, offers the entire menu — all
computable in the same run, side by side:

- **k fixes the POPULATION.** "Your neighbourhood is your 400
  nearest people, wherever they happen to live." Everyone gets the
  same number of neighbours; how much ground that takes floats.
- **r fixes the GEOMETRY.** "Your neighbourhood is everyone within
  500 metres, however many that is." Everyone gets the same circle;
  how many people it contains floats.
- **tau fixes the EFFORT.** "Your neighbourhood is everyone you can
  reach within eight rounds of walking" — where hills, rivers and
  bridges make some directions cheaper than others (chapters 9
  and 10 build this machinery).
- **the unbounded decayed sum fixes NOTHING.** Every person in the
  data counts, but distant ones count less, faded by a distance-
  decay weight (chapter 7). No boundary at all — just a horizon of
  fading relevance.
- **area fixes the ADMINISTRATION.** The municipality is the
  neighbourhood, as in the classical statistics — included in the
  menu so the old and the new can be compared inside one system.

None of these is the "correct" definition. They answer different
questions, and asking how their answers differ is often an analysis
in itself.

![What floats: the k/r duality on Gridby](figs/ch04_duality.png)

The figure makes the first two menu items argue with each other,
using the same town. In the left panel, k = 400 is held fixed and
the colour shows `Dist_400` — how far each square's search had to
travel to gather its 400 people. In the dense centre the search
stops within a few hundred metres; at the town's edge it must reach
far. The *radius* is what floats. In the right panel the choice is
reversed: r = 500 metres is held fixed, and the colour shows
`N_r500` — how many people that circle contains, from a handful at
the edge to over a thousand in the centre. Now the *count* is what
floats. Neither map is wrong; each is the shadow of the other's
choice.

## Cook it

The menu items combine freely in one call, and the columns they
produce follow the naming system of chapter 1 with a small twist:
radius-based columns carry the radius in their name, so `N_r500`
means "the count within 500 metres" while plain `N_400` still means
"the count at k = 400".

```python
out = run_knn_counts(cd, k_values=[400], r_values=[500])
# columns: N_400, R_g_400, Dist_400  AND  N_r500, R_g_r500
```

The administrative member of the menu has its own small function,
because it needs one extra piece of information — which area each
person belongs to (here a column named `Kommun`):

```python
from equipop.area import area_stats
per_area = area_stats(df, area_col="Kommun",
                      binary_vars=["hi"], value_vars=["income"])
```

The result is the familiar one-row-per-municipality table — counts,
shares, and value statistics — produced from exactly the same
variable declarations as the egocentric analyses, so switching
between worlds costs one line.

## The dials

Any mix of `k_values` and `r_values` in one call; `tau_values` on
the effort engines of chapters 9–10; `decay=` for the unbounded
sum; and `area_stats` for the administrative family, which also
accepts survey-style weights for its counts and shares.

## Under the hood

A design principle governs which columns exist in which mode, and
once you see it, the output tables explain themselves: **a column
exists only where it measures something.** `Dist_` exists only for
k — when the radius is fixed at 500 metres, "how far did the search
go" has a trivial answer (500 metres), so no column pretends
otherwise. `Rounds_`, the effort analogue, exists only on the graph
engines. Area mode has neither, because an administrative area does
not grow outward — there is no search whose length could be
measured. Columns are honestly absent, never filled with a
placeholder. A pleasant bonus of the radius world: the equal-
distance tie problem of chapter 1 simply **vanishes**, because
every square within the radius is included wholly by definition —
there is no "last neighbour" whose ties need arbitrating.

## Pitfalls

Radius users inherit the mirror image of chapter 1's warning: the
count `N_r500` varies enormously across space — that is precisely
the point, geometry fixed and population floating — which means
that a *share* like `R_g_r500` may rest on twelve people in a
sparse square and on twelve hundred in a dense one. Twelve people
make a fragile percentage. The `N_` columns always show you the
basis a share stands on; reporting shares without their basis is
how honest maps mislead.
