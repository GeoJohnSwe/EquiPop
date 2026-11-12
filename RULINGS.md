# EquiPop rulings

**The method decisions in force: what EquiPop must compute or refuse, and why.**
A ruling is decided by the method lead (today John Östh) and changes only through a method decision. Code that contradicts a ruling is a defect, even when every test passes.

*Started 12 November 2026 at 1.64.1 from BACKLOG.md and the handovers. Each entry names where it was decided.*

---

## How a ruling is made or changed

1. **Open a method-decision issue** (template in `.github/ISSUE_TEMPLATE`). State the rule today, the rule proposed, a worked example, and which numbers change.
2. **The method lead decides.** A decision in a meeting or an email counts once it is written here.
3. **Record it here**, in the same pull request that builds it:
   - give it the next number;
   - name a test that fails if the rule is broken;
   - write the BACKLOG entry for the work.
4. **Never renumber, never delete.**
   - A changed ruling gets an *Amended* line.
   - A replaced ruling gets the status *Superseded by R-nn*.
   - A declined proposal stays as *Ruled out*, so the next person to have the idea finds the answer here instead of raising it again.

`tests/test_rulings_register.py` keeps this file honest. Every ID is unique and in the index below, every status is one of the five listed, every BACKLOG number cited exists, and every test named under *Pinned by* exists.

**Each entry:** *Rule*, what the code does. *Why*, the reason, in the decider's words where we have them. *Source*, where it was decided. *Pinned by*, the test that fails if the rule is broken (*none yet* is a to-do). *Status*, one of:
- **In force**
- **In force, not yet built**
- **Ruled out** (a proposal declined)
- **Superseded by R-nn**
- **To confirm** (the record is unclear and the method lead should look)

## Index

| ID | Ruling | Status |
|---|---|---|
| R-01 | k counts people, so a population is never negative | In force |
| R-02 | The ring that crosses k: proportional share by default | In force |
| R-03 | Self-potential: three choices, the full radius by default | In force |
| R-04 | A place is its own neighbour unless the user says otherwise | In force |
| R-05 | Dist_k is the outer edge of the accepted ring | In force |
| R-06 | A radius run reports no distance | Ruled out |
| R-07 | k or a radius: either may be empty, not both | In force |
| R-08 | Decay does not choose the neighbourhood | In force |
| R-09 | Large runs: correctness before speed | In force |
| R-10 | Missing values: excluded, and the share divides by the observed | In force |
| R-11 | Rows outside the reference count as nobody but still get results | In force |
| R-12 | A treatment holds counts of people | In force |
| R-13 | A group larger than its population is reported, not refused | In force |
| R-14 | Anything may be a weight | In force |
| R-15 | The first population choice counts a filled count field | In force |
| R-16 | k is a whole number of people; "1,000" is refused | In force |
| R-17 | Any positive cell size, fractions included | In force |
| R-18 | Percentiles are interpolated, never stepped | In force |
| R-19 | No warning about few distinct values | Ruled out |
| R-20 | MLD refuses a zero; the group split has a minimum size | In force |
| R-21 | Segregation profiles weigh people by default | In force |
| R-22 | Decay curves use half-life, as published | In force |
| R-23 | "No decay" means no decay | In force |
| R-24 | A diagonal step costs √2 | In force |
| R-25 | An empty friction value means no obstacle | In force |
| R-26 | A barrier is charged once per class, not per feature | In force |
| R-27 | Vectors are converted; rasters and missing systems are refused | In force |
| R-28 | Projection from degrees is for the beginner, and says what it did | In force |
| R-29 | Wide data in one zone gets a note and carries on | In force |
| R-30 | The working frame is chosen by extent | To confirm |
| R-31 | One engine, many doors: a rule lives once | In force |
| R-32 | Existing result fields: overwrite, stop or keep both | In force |
| R-33 | Every run leaves a record where the user can find it | In force |
| R-34 | Words, not numbers, in every door | In force |
| R-35 | One QGIS plugin, 3.38 to 4.x, advanced tools shown on request | In force |
| R-36 | In Stata, if/in choose who gets results, not who counts | In force |
| R-37 | Demographic indices are bare ratios | In force |
| R-38 | Age bands above 90 fold into 90+, and the run says so | In force |
| R-39 | A user's own index is computed as given, its gaps written down | In force |
| R-40 | Mortality from year differences: never clamp the negatives | In force, not yet built |
| R-41 | A decayed denominator reports its effective sample size | In force, not yet built |
| R-42 | Life expectancy below age 60 is built, and flagged unreliable | In force |
| R-43 | No value-statistics door in the main Stata command | Ruled out |
| R-44 | No friction or slope in the main Stata command | Ruled out |
| R-45 | No disclosure-control profile | Ruled out |
| R-46 | Anything that touches the network produces files and stops | In force |
| R-47 | Provider knowledge lives apart from the tool | In force |
| R-48 | Demography as a separate package | To confirm |
| R-49 | A correctness fix ships at once | In force |
| R-50 | Dead code is deleted, not commented out | In force |
| R-51 | The sample data stays as it is until a publication leans on it | In force |

---

## A. The neighbourhood

### R-01 · k counts people, so a population is never negative
**Rule.** A neighbourhood is grown outward from its origin until it holds k of the population (the weight column), not k points. A negative population is refused by every machine.
**Why.** With a negative weight the running total can rise, fall and cross k several times, so "the radius at which k was reached" has no answer. John: "negative population is refused and for a good reason."
**Source.** BACKLOG 351 (v1.51.2).
**Pinned by.** `tests/test_review_1_51.py::test_f2_a_negative_population_is_refused_by_both_machines`
**Status.** In force.

### R-02 · The ring that crosses k: proportional share by default
**Rule.** The ring of cells that crosses k is taken in one of three ways:
- *whole*: the whole ring, as before 1.30;
- *proportional*: the same fraction of each cell, so N_k is exactly k. This is **the default**, in every door and for effort runs too;
- *sampled*: whole cells drawn one at a time in seeded order. It reproduces the original 2014 method, and is for the point estimate, not for a spread. Stata refuses it by name.

**Why.** John: "the original EquiPop was developed to counter the overshoot effects so this is not a wish. We have to manage this." At a sharp group boundary the whole ring gave a share of 0.20 where the proportional share gives 0.02.
**Source.** BACKLOG 99 (v1.30); HANDOVER_7; HANDOVER_11 §3.
**Pinned by.** `tests/test_overshoot_doors.py::test_2_the_qgis_default_is_the_engines_default`, `tests/test_stata_boxes.py::test_sampled_is_refused_by_name_not_ignored`
**Status.** In force.

### R-03 · Self-potential: three choices, the full radius by default
**Rule.** The people in the origin's own cell are placed at a distance. There are three choices: 0; 0.71 (the median, 2^-0.5); and 1, the radius at which the cell's own people reach k. The default is 1. Choice 0 reproduces pre-1.29.5 numbers exactly.
**Why.** Without it, Dist_k is 0 wherever a cell alone holds k, and the distance says nothing.
**Source.** HANDOVER_6 (v1.29.5); HANDOVER_11 §3 (three choices, John's correction).
**Pinned by.** `tests/test_rungs.py::test_the_middle_choice_really_is_the_median`
**Status.** In force.

### R-04 · A place is its own neighbour unless the user says otherwise
**Rule.** Two rules: *include* (i = j), the default, and *exclude* (i ≠ j), chosen by name (`originrule()` in Stata, a dropdown in the GIS doors).
**Why.** Include is what the 2014 software did. On John's Los Angeles data, 78,208 blocks, EquiPop 1.47 matched the 2014 file to seven decimals, with a mean share of 0.2752264.
**Source.** BACKLOG 290 (v1.47.6).
**Pinned by.** `tests/test_selfrule.py::test_the_default_is_to_include_the_origin`
**Status.** In force.

### R-05 · Dist_k is the outer edge of the accepted ring
**Rule.** Dist_k is the maximum straight-line distance to the accepted ring, in effort runs too, and does not depend on the order of the input rows. A median distance would be a column of its own (MedDist_k, ruled in and not built, BACKLOG 100), never folded into Dist_k.
**Why.** One column meaning two things is the silence this project keeps catching.
**Source.** BACKLOG 115 (v1.29.5), 100.
**Pinned by.** `tests/test_selfpot.py::test_effort_distance_does_not_depend_on_row_order`
**Status.** In force.

### R-06 · A radius run reports no distance
**Rule.** A run by radius reports N_r and shares, and no distance: not the radius itself, not the mean distance, not the furthest neighbour.
**Why.** John: "radius is radius and good enough so let us not persue neither (a) or (b)". The radius is the neighbourhood's definition, so a run owes no second description of it.
**Source.** BACKLOG 203 (session 12).
**Pinned by.** none yet
**Status.** Ruled out (a mean or furthest distance for radius runs).

### R-07 · k or a radius: either may be empty, not both
**Rule.** Both boxes are optional; a run needs one of the two and is refused, before it starts, with neither.
**Why.** John: "no need to restrict missing k, think that there may be only r".
**Source.** BACKLOG 305 (v1.47.8).
**Pinned by.** `tests/test_arcgis_stub.py::test_pro_refuses_a_run_with_neither_k_nor_r`
**Status.** In force.

### R-08 · Decay does not choose the neighbourhood
**Rule.** k is counted without decay; decay then weights the people found. The decayed totals are reported and are never larger than k. Decay alone, without k or a radius, is not a run.
**Why.** John: "the k-values should aim for a NON-DECAYED k. i.e. if k=300 is requested, the 300 nearest population is the right call - the decayed populations should be reported and are always ... smaller than k".
**Source.** HANDOVER_11 §3 (v1.40); BACKLOG 186.
**Pinned by.** `tests/test_decay_at_k.py::test_the_decayed_population_is_always_smaller_than_k`
**Status.** In force.

### R-09 · Large runs: correctness before speed
**Rule.** In tiled and continental runs, a ring cut by the edge of the fetched window is completed by widening the window. It is never treated as a whole ring.
**Why.** John: "continental and possibly global, so correctness over speed."
**Source.** BACKLOG 207; HANDOVER_13.
**Pinned by.** none yet
**Status.** In force.

## B. Who counts, and how much

### R-10 · Missing values: excluded, and the share divides by the observed
**Rule.** A declared missing code becomes ordinary missing; why a value is missing does not matter. For a group, a missing value counts as zero in T, and the share divides by the people whose value is usable: of 400 people with 60 unknown, R divides by 340, never by 400. N_k and Dist_k are unchanged. A blanked case still counts towards k and still gets its own row of results. A missing continuous value is left out, and Nv_ says how many values were used.
**Why.** John: "the cause is unimportant, but the possibility to dismiss/exclude those values would be of importance ... it could still be the placeholder for results - it just doesn't contribute self". Dividing by 400 quietly assumes the 60 were not in the group.
**Source.** BACKLOG 168 (v1.32), 480 (effort engines, v1.63.8); BACKLOG.md's v1.21.0 notes.
**Pinned by.** `tests/test_missing_codes.py::test_a_share_divides_by_the_observed_part_not_by_everybody`, `tests/test_missing_codes_stata.py::test_a_blanked_case_still_counts_as_people_towards_k`
**Status.** In force.

### R-11 · Rows outside the reference count as nobody but still get results
**Rule.** A row outside the reference population counts as zero people: it is nobody's neighbour. It still gets its own results, unless the user chooses "leave their results Null". The same holds for a place with zero weight in Stata's `[fweight=]`.
**Why.** John's rule since 1.22.2, made "an active choice". On zero weights: "they shall have results".
**Source.** BACKLOG 83 (v1.29.2), 192 (v1.40.4); BACKLOG.md's v1.22.2 notes.
**Pinned by.** `tests/test_geopackage.py::test_rows_outside_the_reference_still_get_their_own_results`, `tests/test_geopackage.py::test_a_row_outside_the_reference_is_nobody_s_neighbour`
**Status.** In force.

### R-12 · A treatment holds counts of people
**Rule.** A treatment column holds the number of people of the group at that point, in every door. The old reading, a 0/1 flag multiplied by the population, is available by name (`treatmode(flags)`). Impossible combinations are refused: a flag outside 0 to 1, or counts with no population.
**Why.** It matches the help and both GIS doors. Counts read by the flag rule gave a share of 3000%.
**Source.** BACKLOG 179 (v1.37.1), 475 (`equipop_run`, v1.63.8); HANDOVER_11 §3.
**Pinned by.** `tests/test_treatment_contract.py::test_the_reviewers_case_now_gives_the_arithmetic_the_help_promises`, `tests/test_treatment_contract.py::test_counts_without_a_population_are_refused`
**Status.** In force.

### R-13 · A group larger than its population is reported, not refused
**Rule.** T_k may exceed N_k. The run reports it, with the ratio, and carries on.
**Why.** John: "not a cause for reject - it is the choice of the user - we should be able to have ratios on the basis of say 77/66". R = T/N is a ratio, and its numerator was never required to be a subset of its denominator. An example is economically active persons per household.
**Source.** BACKLOG 328 (v1.49.1).
**Pinned by.** `tests/test_treatment_contract.py::test_a_group_larger_than_its_population_is_reported_not_refused`
**Status.** In force.

### R-14 · Anything may be a weight
**Rule.** No restriction on what column is the population; the run says which column it used.
**Why.** John: "there might be rasters that have an odd composition that still are valid to run - users of EquiPop are mostly academics, and would understand the problems".
**Source.** BACKLOG 219.
**Pinned by.** none yet
**Status.** In force.

### R-15 · The first population choice counts a filled count field
**Rule.** The first reference choice reads "every point counts as one - or as the value in the count field, if filled", in both GIS doors. Pro shows the count box on it.
**Why.** John: "let us state not that each point counts as one but each point counts as one or as the value stated below". This moves nobody's numbers.
**Source.** BACKLOG 485 (v1.64.0).
**Pinned by.** `tests/test_pro_hidden_boxes.py::test_a_count_field_on_the_first_rung_is_said_plainly`
**Status.** In force.

### R-16 · k is a whole number of people; "1,000" is refused
**Rule.** A k typed with a thousands separator ("1,000", "1.000") is refused and named, never read as 1. A radius keeps its decimal comma ("500,5" metres).
**Why.** John: "yes - in the next round we should refuse 1,000 - and good to keep it for radii". A wrong answer that completes is worse than an error.
**Source.** BACKLOG 375 (v1.53.2), 320.
**Pinned by.** `tests/test_k_reading.py::test_a_thousands_separator_in_k_is_refused_and_named`, `tests/test_k_reading.py::test_a_radius_keeps_its_decimal_comma`
**Status.** In force.

### R-17 · Any positive cell size, fractions included
**Rule.** The cell size may be any number above zero, 2.5 m or 0.1 m included, in every door. A suspicious size is warned about, never reinterpreted.
**Why.** John: "as determined earlier". Fractions were refused only while integer cell centres made the spacing uneven, and that reason is gone.
**Source.** BACKLOG 445 (v1.63.0), replacing 155.
**Pinned by.** `tests/test_fractional_cells.py::test_effort_potential_and_fca_scale`
**Status.** In force.

## C. Statistics

### R-18 · Percentiles are interpolated, never stepped
**Rule.** A median or percentile is the average value of one person's width of the population, sorted by value, at position (n − 1)q. For whole people that is the usual interpolated percentile; it holds for fractions of a person too.
**Why.** John's reason: EquiPop already averages the two middle values for an even count, which is linear interpolation, so interpolating everywhere is the consistent rule. The 1.64.0 repair keeps it for gridded populations.
**Source.** BACKLOG 118 (v1.31), 484 (v1.64.0); HANDOVER_8.
**Pinned by.** `tests/test_wstats.py::test_the_median_moves_smoothly_as_a_ring_is_swallowed`
**Status.** In force. *Amended 11 November 2026 (484): repaired for rows of less than one person.*

### R-19 · No warning about few distinct values
**Rule.** A value statistic over data with few distinct values (block-group incomes copied onto blocks) runs without a warning.
**Why.** John: "no need, the users will either know what they test or understand statistics better than using it with too few distinct values." The observation stays true: a Gini over copied values measures dispersion between areas.
**Source.** BACKLOG 170 (declined at v1.34).
**Pinned by.** none yet
**Status.** Ruled out (the warning).

### R-20 · MLD refuses a zero; the group split has a minimum size
**Rule.** MLD refuses a zero value and names Theil, which is defined at zero. The between/within split is reported only for groups of at least the minimum size (30 by default, settable). Below it, or with one group, the split columns are empty, not zero. The split is ex ante only for now.
**Why.** Replacing zeros makes the replacement the answer: MLD then depends on the currency unit. Between-group inequality is biased upward in small groups.
**Source.** BACKLOG 405 (v1.55.0).
**Pinned by.** `tests/test_decompose.py::test_mld_refuses_a_zero_and_names_theil`
**Status.** In force.

### R-21 · Segregation profiles weigh people by default
**Rule.** `seg_profile` weighs every person's neighbourhood once, so isolation at k is the 2015 paper's SI. Weighing every place once is an option.
**Why.** John: "should 1|2 be an option for the user to decide, with 1 as default?" - yes.
**Source.** BACKLOG 443 (v1.63.0).
**Pinned by.** `tests/test_segregation_weighting.py::test_people_is_the_default_and_counts_people`
**Status.** In force.

## D. Distance, decay and effort

### R-22 · Decay curves use half-life, as published
**Rule.** A decay distance is a half-life: the median splits the area under the curve. This is the method of Östh, Lyhagen & Reggiani (2016) and of old EquiPop. The choice of reading appears only for curves where the two readings differ (expnormal, expsqrt, lognormal); for negexp they coincide.
**Why.** It is what the paper advocates, it matches what users hold (a survey median), and it restores the published method.
**Source.** BACKLOG 317 (v1.48.0).
**Pinned by.** `tests/test_equipop.py::test_decay_half_life_splits_the_area`
**Status.** In force.

### R-23 · "No decay" means no decay
**Rule.** With no decay curve chosen, a filled half-life field or self-calibration box stops the run; it is not quietly run as negexp. In Stata, `equipop_run` refuses `halflife()` outside fca.
**Why.** John: "it should not - let us block that".
**Source.** BACKLOG 486 (v1.64.0), 490 (v1.64.1).
**Pinned by.** `tests/test_pro_no_decay.py::test_no_decay_with_a_half_life_box_filled_is_refused`, `tests/test_stata_run_options.py::test_an_option_the_engine_does_not_read_is_named`
**Status.** In force.

### R-24 · A diagonal step costs √2
**Rule.** On an effort grid a diagonal move costs √2 times a straight one, so open ground measures octile distance, not Chebyshev.
**Why.** John: "a step is a step" was never a considered choice. He ruled it a clean break, with a loud MANUAL row, rather than a setting.
**Source.** BACKLOG 139 (released with v1.30).
**Pinned by.** `tests/test_menu.py::test_tau_flat_grid_is_octile_disc`
**Status.** In force.

### R-25 · An empty friction value means no obstacle
**Rule.** A cell costs 1 + friction. An empty friction value is 0, and the run says how many features carried each value. A friction field empty everywhere is refused.
**Why.** John, after 735,098 OSM roads: "perhaps we should allow missing values and assign these the default = 0 value automatically." An all-empty field is the forgotten field, not a landscape.
**Source.** BACKLOG 312 (v1.47.12).
**Pinned by.** none yet
**Status.** In force.

### R-26 · A barrier is charged once per class, not per feature
**Rule.** A cell crossed by several features of the same class is charged once for that class.
**Why.** OSM cuts one street into a new record wherever a tag changes, so charging per feature charges one street many times.
**Source.** BACKLOG 298, 306 (v1.49.0).
**Pinned by.** none yet
**Status.** In force.

## E. Coordinates

### R-27 · Vectors are converted; rasters and missing systems are refused
**Rule.**
- Vector layers are converted into the analysis's coordinate system as they are read.
- A raster (elevation or barrier) in another system is refused, never resampled.
- A barrier or raster with no coordinate system is refused, never assumed. A table of coordinates with none declared runs, and says so in capitals (NO COORDINATE SYSTEM).

**Why.** John: "vector projected on read, DEM should not, add a loud error to that; no crs should not be silent - a loud error there". Transforming a coordinate is exact; resampling a raster is an analytical choice that belongs to the user.
**Source.** BACKLOG 313 (v1.47.12), 466 (v1.63.8).
**Pinned by.** `tests/test_pro_crs_per_run.py::test_a_barrier_raster_in_another_system_is_refused`, `tests/test_pro_crs_per_run.py::test_a_barrier_with_no_coordinate_system_is_refused`
**Status.** In force.

### R-28 · Projection from degrees is for the beginner, and says what it did
**Rule.** Stata's `project` option turns degree coordinates into one UTM zone, without a new dependency. The output names the EPSG code. The projection refuses rather than guesses outside the degree envelope or beyond 84°N/80°S. Coordinates that look like degrees get a warning when no projection was asked for, never an automatic projection.
**Why.** John: "for professional spatial analysts, this function is not needed ... However, for the unexperienced stat and econ people that are not trained to think beyond lat/long, a simple function to generate good-enough projections are what is needed ... (i.e. EPSG code for UTM would be enough)".
**Source.** BACKLOG 177 (v1.37); HANDOVER_11 §3.
**Pinned by.** `tests/test_stata_projection.py::test_projection_returns_metres_and_names_the_zone`, `tests/test_stata_projection.py::test_degrees_are_warned_about_when_project_is_not_given`
**Status.** In force.

### R-29 · Wide data in one zone gets a note and carries on
**Rule.** Data wider than one UTM zone is still projected to one zone, with a note saying so; it is never refused. The help mentions single-zone distortion briefly.
**Why.** John: "the bespoke neighbourhood departs from the nearest k-neighbours, it becomes almost impossible to find a situation where an erroneous nearest neighbour is selected before the true nearest ... (i.e. for me it is the risk of counting the wrong cafe in Lyon/France from Oslo)".
**Source.** BACKLOG 178 (v1.37), 171.
**Pinned by.** none yet
**Status.** In force.

### R-30 · The working frame is chosen by extent
**Rule.** The GIS doors choose the working frame by the data's extent, not by its file format:
- under 6° of longitude, auto-project;
- 6° to 20°, project with a warning giving the measured scale error;
- beyond 20°, WGS84 with great-circle distances in metres.

**Why.** A great-circle distance gives true metres from degrees, so k, radii and Dist_k keep their meaning.
**Source.** BACKLOG 93 (v1.29.3).
**Pinned by.** none yet
**Status.** To confirm. It was ruled in 1.29.3 and not built as written. R-29 later settled the single-zone case for Stata. Does R-30 still stand for the GIS doors?

## F. What the doors do

### R-31 · One engine, many doors: a rule lives once
**Rule.** Every decision a door would otherwise make lives once, in the package (`equipop/doors/`), and every door uses it. The Stata help is generated from the same sentences the GIS doors show.
**Why.** John: "one ring to rule them all, and different doors that can use it". The doors drifted every time a rule lived in two places.
**Source.** BACKLOG 38, 175 (v1.36), 320.
**Pinned by.** none yet
**Status.** In force.

### R-32 · Existing result fields: overwrite, stop or keep both
**Rule.** When result fields already exist, the user chooses: overwrite them, stop with a message, or keep both. Keeping both gives the new columns letter suffixes (b, c, … aa), added before any shortening. There is no run-label box. Overwriting is never decided by inference.
**Why.** John: "it might be that we are running several - walk, it may be very complex quickly, user that calls the option will be sure to take note, and the log would tell the story".
**Source.** BACKLOG 316 (v1.49.0).
**Pinned by.** `tests/test_qgis_door.py::test_the_letter_suffixes_run_b_c_then_aa`
**Status.** In force.

### R-33 · Every run leaves a record where the user can find it
**Rule.**
- A GIS run writes a manifest beside its output.
- For a geodatabase or GeoPackage, the manifest goes in an `EquiPop_runs` folder beside the container, never inside it.
- Stata prints the record in the log and returns the settings in r().
- CSVs are comma-separated UTF-8 with a byte-order mark.

**Why.** On the folder, John's ruling: "a manifest per run would otherwise scatter through the project folder". On the comma: Excel's import covers it, and the encoding was the real fault. In Stata, `log using` is where reproducibility already lives.
**Source.** BACKLOG 166 (v1.30.2), 293 (v1.50.0), 320 (v1.48.1).
**Pinned by.** `tests/test_arcgis_stub.py::test_sidecars_never_land_inside_a_geodatabase`, `tests/test_packaging.py::test_the_run_manifests_carry_a_bom_for_excel`
**Status.** In force.

### R-34 · Words, not numbers, in every door
**Rule.**
- Every Stata option is chosen by a word (`overshoot(proportional)`, `selfpot(median)`).
- Dropdown labels are short, and their explanations live in the help.
- The vocabulary is neutral: a point may stand for people, jobs, dwellings or services.

**Why.** A do-file read six months later has to say what it did.
**Source.** HANDOVER_11 §3; BACKLOG 91; BACKLOG.md's v1.29.0 notes.
**Pinned by.** none yet
**Status.** In force.

### R-35 · One QGIS plugin, 3.38 to 4.x, advanced tools shown on request
**Rule.**
- One plugin covers QGIS 3.38 to 4.x. The minimum was raised rather than writing fallbacks for deprecated calls.
- Tools 3 to 6 are hidden until tool 0 shows them, in QGIS and Pro alike. They are not a separate plugin.

**Why.** John: one plugin for everybody, "the same except for ONE detail - the visualisation of the 3 and up tools".
**Source.** BACKLOG 84 (v1.29.3), 438 (v1.62.0), 464 (v1.63.7).
**Pinned by.** none yet
**Status.** In force.

### R-36 · In Stata, if/in choose who gets results, not who counts
**Rule.** `if` and `in` restrict the rows that receive results. Everybody still counts as a neighbour. This holds in `equipop` and `equipop_run` alike.
**Why.** That is the question a subsample asks; who counts as reference population is a separate option.
**Source.** BACKLOG 118 (Stata conventions), 487 (v1.64.0); HANDOVER_11 §3.
**Pinned by.** `tests/test_stata_run_level.py::test_if_chooses_who_gets_results_not_who_is_a_neighbour`
**Status.** In force.

## G. Demography

### R-37 · Demographic indices are bare ratios
**Rule.** The indices are bare ratios (per one person). The field guide states the convention, since a sex ratio is usually given per 100 women and a child-woman ratio per 1,000.
**Why.** John: "keep the bare ratios."
**Source.** BACKLOG 366 (v1.53.0).
**Pinned by.** `tests/test_raster_review.py::test_366_the_field_guide_states_the_units`
**Status.** In force.

### R-38 · Age bands above 90 fold into 90+, and the run says so
**Rule.** Bands above 90 fold into 90+, only into a side of an index that reaches the top band, and the run says so. Naming t (everybody) together with f or m is refused, since it counts people twice.
**Why.** John: "I think we should fold into 90+ - but note to user in output if found in the run." And: "fmt should not be accepted."
**Source.** BACKLOG 363 (v1.53.4), 359 (v1.53.0).
**Pinned by.** `tests/test_raster_review.py::test_363_the_fold_only_reaches_a_side_that_wants_the_top_band`, `tests/test_raster_review.py::test_359_t_with_f_or_m_is_refused`
**Status.** In force.

### R-39 · A user's own index is computed as given, its gaps written down
**Rule.** An index a user specifies is not altered. If the data lacks part of it, a sex for instance, the index is computed and the restriction recorded, not refused.
**Why.** John's position: experienced users' choices are not to be altered.
**Source.** BACKLOG 361 (v1.53.0).
**Pinned by.** `tests/test_raster_review.py::test_361_a_folder_missing_a_sex_records_it_without_refusing`
**Status.** In force.

### R-40 · Mortality from year differences: never clamp the negatives
**Rule.** Deaths estimated by differencing two modelled population years keep their negative cells.
**Why.** The raw difference is unbiased; clamping to zero inflates mortality 1.7 to 11.8 times, worst where the data is weakest.
**Source.** BACKLOG 98 (v1.29.5).
**Pinned by.** none yet
**Status.** In force, not yet built.

### R-41 · A decayed denominator reports its effective sample size
**Rule.** A rate on a decayed denominator computes its standard error from n_eff = (Σw)² / Σw², not from Σw.
**Why.** Σw understates the uncertainty, silently, and worst where the cohort is thinnest.
**Source.** BACKLOG 97 (v1.29.5).
**Pinned by.** none yet
**Status.** In force, not yet built.

### R-42 · Life expectancy below age 60 is built, and flagged unreliable
**Rule.** e60, TFR, CBR and CDR are built; so are e50, e30 and e0, flagged unreliable.
**Why.** John: "as a researcher I am not looking for truth but variables to make better predictions." He validates against Swedish data.
**Source.** BACKLOG 416 (v1.60.0).
**Pinned by.** none yet
**Status.** In force.

## H. What EquiPop does not do

### R-43 · No value-statistics door in the main Stata command
**Rule.** `equipop` in Stata computes counts and shares only. (`equipop_run, engine(stats)` exists for those who want the engine's statistics.)
**Why.** John: "machine 2 door from stata is not necessary (at least for now) since stata is a statistics software we can rely on the built in functions instead."
**Source.** BACKLOG 205 (session 12).
**Pinned by.** none yet
**Status.** Ruled out.

### R-44 · No friction or slope in the main Stata command
**Rule.** Barriers and terrain are not in `equipop`. (`equipop_run` reaches the effort engines.)
**Why.** John: "stata doors for friction and slope is not needed - those are GIS features, and not needed in statistics". EquiPop builds neighbourhoods, GIS handles geography, Stata handles statistics.
**Source.** BACKLOG 296 (session 12).
**Pinned by.** none yet
**Status.** Ruled out.

### R-45 · No disclosure-control profile
**Rule.** No minimum k and no suppression of thin results for register data.
**Why.** John: "access to restricted or sensitive data means having agreed to ethical protocols already - so no need for extra caution".
**Source.** BACKLOG 122 (v1.29.5).
**Pinned by.** none yet
**Status.** Ruled out.

### R-46 · Anything that touches the network produces files and stops
**Rule.** A tool that downloads writes files and a manifest, and stops; it never analyses. No analysis tool touches the network.
**Why.** John's ruling, as HANDOVER_13 records it: a connector would make the toolbox inconsistent "unless the network is kept out of every analysis tool". The analysis tools give the same answer offline, forever; a downloader cannot.
**Source.** HANDOVER_13 §3c; BACKLOG 240.
**Pinned by.** `tests/test_fetching.py::test_the_fetcher_never_analyses_anything`
**Status.** In force.

### R-47 · Provider knowledge lives apart from the tool
**Rule.** What a data site looks like (URLs, file naming, fields) is data, kept apart from the fetching code, so a site change needs an update of that data, not a release.
**Why.** John: "what if the site specific instructions could be separated from the tool". The WorldPop naming registry, baked into code, failed on all 120 real files.
**Source.** BACKLOG 258.
**Pinned by.** none yet
**Status.** In force.

### R-48 · Demography as a separate package
**Rule.** Machines 3 and 4 were to ship as a separate package, `equipop-demography`, for access control during development.
**Why.** "Alternative A", 1.29.2 session.
**Source.** BACKLOG 82 (v1.29.2).
**Pinned by.** none yet
**Status.** To confirm. The tools now ship in the one plugin, hidden until shown (R-35). Is this superseded?

## I. How the project works

### R-49 · A correctness fix ships at once
**Rule.** A fix for a wrong number is not held behind feature work. It goes into the next release that John will test; releases are batched to his test rounds, not made per message.
**Why.** He had ruled the opposite for 1.37 and overruled himself the moment the defect was a wrong number.
**Source.** HANDOVER_11 §3; BACKLOG 288.
**Pinned by.** none yet
**Status.** In force.

### R-50 · Dead code is deleted, not commented out
**Rule.** Code that is no longer used is removed.
**Why.** John: "it risks becoming an orphan or picked up in a later session with unknown consequences".
**Source.** HANDOVER_11 §3; BACKLOG 186.
**Pinned by.** none yet
**Status.** In force.

### R-51 · The sample data stays as it is until a publication leans on it
**Rule.** `people_syn.csv`, `jobs_syn.csv` and the Stata test data are left as they are. Their description must be settled before any publication, course or SSC text leans on them.
**Why.** John: "it is not an ethical issue as of now, but it could become if we push in publications etc."
**Source.** BACKLOG 482 (11 November 2026).
**Pinned by.** none yet
**Status.** In force.
