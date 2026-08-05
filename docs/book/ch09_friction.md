# 9. Friction: when straight lines lie

## The idea

Every distance so far has been drawn with a ruler — the straight
line from square to square. Towns are not rulers. A river without
a bridge makes two squares 200 metres apart effectively distant; a
railway yard, a motorway cutting, a fenced industrial estate do the
same. This chapter introduces the machinery that lets the map push
back: **friction**.

The mental model is walking. Imagine standing on your square and
spreading outward one step — one square — at a time; call each
sweep of steps a **round**. On an open plain, three rounds reach
everything within three squares, a tidy diamond. Now declare some
squares *costly*: entering a river square costs not one round but
seven (one for the step, six for the friction you assigned it).
The spreading walk now flows around the river, squeezes across the
bridge, and the shape of "what I can reach in three rounds" stops
being a diamond and starts being the truth. The software computes
this spreading exactly — the algorithm underneath is the classic
shortest-path method of computer science (Dijkstra's, for the
curious), run from every inhabited square.

Friction changes the *questions* you can ask, and two new column
families appear to answer them. `Rounds_200` answers "how much
walking effort until I have gathered my 200 nearest people?" — the
effort twin of `Dist_200`, and the two disagreeing is exactly
where the ruler was lying. And `tau` — chapter 4's third menu
item — turns the question around: `N_tau3` counts the people
reachable within an effort budget of three rounds, the honest
version of "who lives within fifteen minutes of me".

![The river's shadow on Gridby](figs/ch09_friction.png)

The figure lets Gridby's planted river (friction 6, one bridge)
speak. In the left panel, the colour is `N_tau3` — how many people
each square can reach in three rounds. Away from the water the
values follow simple density; along the river a dark seam appears
on both banks: for those squares, half the world sits behind a
six-round wall, and only the bridge's neighbourhood escapes the
shadow. In the right panel the same story is told in the other
currency — `Rounds_200`, the effort to gather 200 people — and the
seam brightens instead of darkens: river-hugging squares need more
rounds for the same crowd. Same wall, two shadows. In chapter 11
this seam reappeared, uninvited, as the edge of the LISA clusters
— planted geography echoing through every layer of analysis, which
is precisely what Gridby is for.

## Cook it

Friction arrives as a small table of costly squares — coordinates
plus a friction value — and everything else is one call:

```python
from equipop.datasets import load
from equipop.friction import run_knn_friction

g = load("gridby")
res = run_knn_friction(g["people"], k_values=[200],
                       fr=g["friction"], unit_size=100,
                       tau_values=[3])
# columns: N_200, Rounds_200, T_/R_ as usual, and N_tau3, R_tau3
```

The friction table's convention deserves one careful sentence:
squares *not listed* in the table cost the default, and the
default is zero extra — so the natural way to use the file is as a
**list of barriers**, naming only the rivers, the cuttings, the
fences. (If you prefer the opposite — listing the *passable*
squares in a world of walls — set `default_friction` high and list
the roads; the machinery is indifferent.)

## What the number actually means

A friction value is not a distance, and it is not a multiplier. It
is a **delay, counted in rounds**.

Every square costs one round to enter. Friction is what gets added
to that one. So:

| friction | the square costs | what it is |
|---|---|---|
| 3 | 4 rounds | a river |
| 1 | 2 rounds | a busy road |
| 0 | 1 round | open ground |
| −0.5 | half a round | a fast road |
| −0.9 | a tenth of a round | a motorway |
| −1 | nothing at all | refused |

Read the top row again, because it is the whole idea: at friction
three, one square costs four rounds — *as if the river were four
squares wide*. That is why crossing it twice costs eight, and why a
river given friction fifty is not a river anyone crosses.

Negative values run the same argument backwards. If friction adds
to the cost of entering a square, a negative value subtracts from
it, and a square becomes cheaper than open ground. That is a road:
not something that stops you, but something that carries you. A
value of −0.9 makes a square cost a tenth of a round, so ten
squares of motorway cost what one square of field costs.

The floor is −1, and it is a hard floor rather than a cautious one.
At −1 a square costs nothing, and a network of free squares is not
a neighbourhood: the nearest four hundred people could be gathered
from anywhere at no cost at all, and the question stops meaning
anything. EquiPop refuses −1 and below, and says so.

**Barriers and facilitators are one dial, not two.** Positive
deters, negative carries, zero is ordinary ground. A single column
of numbers can hold a river at 4, a footbridge at 0 and a tram line
at −0.6, and the walk will sort them out.

## What happens to Dist_k when effort is on

Something worth pausing over, because it surprises most people the
first time and it is not a bug.

Turn a barrier on and `Dist_k` **changes** — not because the world
moved, but because *your neighbours did*. The neighbourhood is
gathered in order of effort, not of metres. A café a hundred metres
away across a river may cost more rounds than a café three hundred
metres away along the near bank, so the second one joins your four
hundred and the first one does not. `Dist_k` then reports the
straight-line distance to whoever completed the count — and that is
now somebody else.

Which means `Dist_k` under effort is **not a radius**. With plain
distance the neighbourhood is a disc and `Dist_k` is its edge. With
a cost surface the neighbourhood is a shape moulded by the
barriers — long down an open valley, blunt against a river — and
`Dist_k` is simply how far away, as the crow flies, the last person
you reached happened to be.

That makes it useful in a way it is not otherwise. Run the same
question twice, once with barriers and once without, and compare
the two `Dist_k` columns. Where they agree, the barrier is
irrelevant. Where the effort run reaches *further* in metres, the
barrier has pushed your neighbourhood sideways — it has rearranged
who is near whom. That difference is arguably the most interesting
single number the effort engine produces, and it costs one extra
run to obtain.

## The dials

`fr` (the friction table) and `default_friction`; and since
version 1.15 the table need not be typed at all —
`features_to_friction` rasterizes your river and railway *line or
polygon features* onto the grid, with overlapping features stacking
their costs additively (a river and a railway in one square cost
both); `k_values` and
`tau_values` from the shared menu; and `origins=`, which computes
results for a subset of squares against the full population — the
same key that chapter 17 uses at national scale, available here
because effort computations are the expensive ones.

## Under the hood

Costs attach to the square being *entered* — friction is a
property of the destination step, added on arrival — and diagonal
steps count one-and-a-half, so that effort approximates true
walking distance rather than chessboard distance. The `Rounds`
reported are *flat-equivalent*: a value of 5 means "as much effort
as five open squares", whatever mixture of walking and wall-
climbing produced it, which keeps the number comparable across a
map. The engine was validated the way this book prefers: on real
Stockholm water barriers, where the correlation between beeline
and effort results decays with distance from the water in exactly
the pattern theory predicts. And a promise for the next chapter:
the machinery here treats all costly squares alike, whichever
direction you cross them — hills, where *direction matters*, get
their own chapter and their own mathematics, built on this same
spreading walk.

## Pitfalls

Friction values are model choices wearing numeric clothes. "The
river costs six" is a statement about how much that river deters,
not a measurement — so, as with half-lives in chapter 7, report
sensitivity (does the seam survive at friction three? at ten?)
rather than false precision. And keep the two uses of the table
conceptually separate: a *barrier* (high friction, rarely crossed)
and a *slowdown* (mild friction, routinely crossed) are different
claims about the world; a value of 2 says people cross constantly
at modest cost, a value of 50 says essentially never — make the
number say what you mean.

The same caution applies with the sign reversed, and rather more
sharply. A facilitator says "people move along here more cheaply
than across open ground", which is a claim about *behaviour*, not
about tarmac. A motorway is a facilitator for a driver and a
barrier for a pedestrian, and the same map of roads will therefore
need different numbers depending on whose neighbourhood you are
measuring. Say which, in the paper.

And beware of covering the map. If every road carries a
facilitator and roads reach everywhere, you have not modelled a
transport network — you have made the whole world cheaper by the
same amount, which changes almost nothing except the runtime.
Effort measures are about *contrast*: what is dear next to what is
cheap. A dial applied uniformly has no contrast left to measure.
