# EquiPop 1.5.1 — The Function Matrix

*Who uses whom, who replaces whom, and where the dials live.*

## Table 1 — Grand functions: the dependency matrix

Read **row uses column** (consumes its output or calls it). `•` = uses,
`(•)` = optional. The pipeline reads top-left to bottom-right.

| uses → | IO | PR | CE | HX | DC | DE | RK | ST | FC | FR | SL | PS | EP | FA | SG | AR | AG | MP | RL | SB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **IO** read_table/save/fetch | – | | | | | | | | | | | | | | | | | | | |
| **PR** project+snap+zones | • | – | | | | | | | | | | | | | | | | | | |
| **CE** build_cells | (•) | • | – | | | | | | | | | | | | | | | | | |
| **HX** build_hex_cells | (•) | • | | – | | | | | | | | | | | | | | | | |
| **DC** Decay | | | | | – | | | | | | | | | | | | | | | |
| **DE** dem_to_cell_altitude | | | | | | – | | | | | | | | | | | | | | |
| **RK** run_knn (ring) | | | • | (•) | (•) | | – | | | | | | | | | | | | | |
| **ST** run_knn_stats | | | • | (•) | | | | – | | | | | | | | | | | | |
| **FC** run_knn_counts (fast) | | | • | (•) | (•) | | | | – | | | | | | | | | | | |
| **FR** run_knn_friction | (•) | • | | | | | | | | – | | | | | | | | | | |
| **SL** run_knn_slope | (•) | • | | | | • | | | | • | – | | | | | | | | | |
| **PS** potential_surface | | | | | • | | | | | | | – | | | | | | | | |
| **EP** effort_potential | | | | | • | • | | | | | • | | – | | | | | | | |
| **FA** fca / fca_segments | | (•) | | | (•) | (•) | | | | | (•) | | | – | | | | | | |
| **SG** seg_profile | | | | | | | (•) | | • | (•) | (•) | | | | – | | | | | |
| **AR** area_stats | | (•) | | | | | | | | | | | | | | – | | | | |
| **AG** aggregate_output | (•) | | | | | | (•) | (•) | • | (•) | (•) | | | | | | – | | | |
| **MP** map_output | | | | | | | (•) | (•) | • | (•) | (•) | (•) | (•) | (•) | | | (•) | – | | |
| **RL** RunLog | • | • | • | • | • | • | • | • | • | • | • | • | • | • | • | • | • | • | – | |
| **SB** stata_bridge / ado | (•) | | • | | (•) | (•) | | • | • | • | • | | | • | | | | | | – |

Notes: RL (RunLog) wraps anything — every • in its row means "can log
it". SG consumes the *output tables* of the engines (any table with
N/T columns, local + per-scale). MP maps any table with x/y + a value.

## Table 2 — Alternatives: same question, different answer

| Question | Interchangeable choices | Chooses between |
|---|---|---|
| Which counting engine? | **FC** (fast) vs **ST** (stats) vs **RK** (ring) | speed/counts · value statistics · decay-at-k & legacy |
| Which graph engine? | **FR** (friction) vs **SL** (slope) | barriers only · barriers + terrain (SL ⊃ FR: flat DEM ≡ FR exactly) |
| Which neighbourhood definition? | **k** vs **r** vs **tau** vs **decayed-sum (ND_inf)** vs **area** | fixes population · geometry · effort · nothing (all, weighted) · administration |
| Which access measure? | **PS** (Euclidean, FFT) vs **EP** (effort, Dijkstra) | flat-map reach · terrain/round-trip reach |
| Competition accounting? | **FA** method=2sfca vs 3sfca vs balance= | one-pass pressure (your steps 1–4) · demand-splitting · market clearing |
| Which geometry? | **CE** (squares) vs **HX** (hexagons) | MAUP experiment in one swap; engines unchanged |
| Which decay family? | negexp · expnormal · expsqrt · lognormal · power(γ) | tail shape; all half-life anchored; horizons differ (∞ for power γ≤1) |
| Individual vs area statistics? | engines + **AG** vs **AR** | individualised-then-summarised · classic per-area |

## Table 3 — The small functions: dials inside the grand ones

**DC Decay** — `model` (5 families) · `half_life_m` (the anchor) ·
`gamma` (power tail; γ≤1 ⇒ infinite horizon) · `beta` (expert direct) ·
derived: `weight_vec`, `truncation_radius(eps)`, `opportunity_horizon`.

**Engines RK/ST/FC** — `k_values` · `r_values` · `unit_size` ·
`tie_mode`/`seed` (ring: legacy C# order) · FC: `decay=`+`decay_eps`
(ND_inf) · ST: `stats={var: [mean, sd, se, median, gini, ratio]}`
(the registries — extend by dict entry) · missing handling: `Nv_`
basis columns.

**Graph engines FR/SL** — `fr=` friction table + `default_friction`
(0 = file lists barriers) · `tau_values` (isochrones) · `origins=`
(subset, full destination mass) · SL: `altitude` (DEM path / frame /
array) · `model` ∈ {tobler, linear} · `lambda_up/lambda_down` ·
`roundtrip` (per-leg average) · `chunk`.

**Access PS/EP** — `eps` kernel truncation · `pad_cells` · mass frame
= opportunities (access) OR population (new-POI surplus) · EP:
half-life in ROUNDS.

**FA fca/fca_segments** — `reach` ∈ {decay, r, k, effort} · `method`
∈ {2sfca, 3sfca} · `balance=n` (+ gauge convention) · `segments=`
match table (per-segment overrides win) · outputs `A`, `J` (step-1
potential; J/A = effective competitor mass), `R` or `C`.

**Post SG/AR/AG/MP** — SG: index set (D, Gini, H, Atkinson(b),
Isolation, Interaction, V, SI) + mixed k/r labels · AR: `weight_col`
(N and T/R only — loud), stats registry reuse · AG: belonging-ID /
polygon sjoin / supergrid · MP: `classes` ∈ {quantile, equal, sd,
jenks}, scale bar, north arrow.

**Infrastructure IO/PR/RL/SB** — IO: separator/BOM sniffing, layers,
zip/pbf/sav/xlsx · PR: `suggest_projection`, `assign_zones` A/B ·
RL: md5 hashes, progressive writes, column definitions · SB:
`equipop_knn` options x/y/treat/k/r/unit/weight/replace.
