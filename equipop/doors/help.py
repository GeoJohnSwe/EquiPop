# -*- coding: utf-8 -*-
"""
help.py - the explanation beside every box, written once.

Every door has to explain the same parameters, and until now each
one carried its own copy. ArcGIS Pro reads these to build the small
comment beside each box and the panel behind the '?' (through the
sidecar XML files that make_help_xml.py writes). QGIS reads the very
same strings at run time for shortHelpString. R and SPSS will read
them for their own help pages.

Keys are PARAMETER NAMES, and they are the same names in every door.
That is what keeps a dialog and its help from drifting apart: a
parameter with no entry here is caught by the test suite, in both
doors, before release.

Text moved unchanged from arcgis/make_help_xml.py in 1.18.0.
"""

HELP = {
    # BACKLOG 102/42. Stata reached the decay boxes first (1.39);
    # QGIS still has none, and Pro's wording should come from here
    # when 102 is done rather than being written a third time.
    "decaymodel":
        "Weights each neighbour by how far away it is, and reports the "
        "weighted totals alongside the plain ones: ND_ for the "
        "population, TD_ for each group, RD_ for the share. "
        "THE NEIGHBOURHOOD ITSELF IS UNCHANGED. k still means the k "
        "nearest people - ask for 300 and you get the 300 nearest - "
        "and the radius is still the distance you must travel to "
        "reach them. Only the contents are re-weighted, so a person "
        "at the edge counts for less than one standing beside you. "
        "The decayed totals are therefore always smaller than the "
        "plain ones. "
        "negexp halves the weight every half-life and is the usual "
        "choice. power falls quickly and then very slowly, so distant "
        "places never quite stop counting. expnormal, expsqrt and "
        "lognormal shape the curve differently again - see the "
        "manual.",

    # BACKLOG 168. Written here so every door says the same thing;
    # Stata reached it first (1.38), QGIS and Pro still to come.
    "missingcodes":
        "Values that mean NO DATA rather than a number, listed and "
        "separated by spaces. Census and register extracts carry "
        "these: -666666666 for a suppressed median in US ACS data, "
        "-9 or 999 elsewhere. Left undeclared they are arithmetic - a "
        "neighbourhood mean lands near minus forty million, and it "
        "lands there quietly. "
        "A case whose value is declared missing STILL COUNTS AS "
        "PEOPLE towards k, and still receives its own results; only "
        "its value drops out. Shares are then divided by the people "
        "actually observed, never by everybody present: 400 people "
        "with 60 of unknown group gives a denominator of 340.",

    "layer": "The points to analyse - a point layer (coordinates are "
             "read straight from the geometry) or a plain table with "
             "coordinate columns. Coordinates must be metric; degree "
             "data is refused unless auto-projection is ticked.",
    "coordsrc": "Auto uses the geometry when the input has any, and "
                "attribute fields otherwise. Choose Attribute fields "
                "to override, e.g. when a layer carries coordinates "
                "in columns you trust more than its geometry.",
    "xfield": "The easting column - only for tables or attribute "
              "mode. Guessed when the name is recognisable "
              "(X/East/Easting/POINT_X...); no renaming is needed.",
    "yfield": "The northing column - only for tables or attribute "
              "mode.",
    "pop": "How many each point stands for - people, jobs, dwellings, "
           "services, anything countable. Leave empty when every point "
           "counts as one. k counts these, so this field decides how "
           "far the k-search must travel - and in Value Statistics "
           "every statistic is weighted by it, so a point standing for "
           "40 counts 40 times a point standing for one.",
    "treat": "Group counts: persons of the group at this point (use "
             "0/1 when points are individuals). Produces T_<group>_k "
             "(count) and R_<group>_k (share). These columns are "
             "ADDED UP across the neighbourhood, so give TOTALS, "
             "never averages: total income at this point, not mean "
             "income per person here. A per-point average belongs in "
             "tool 2 (Value Statistics), which weights it by the "
             "reference population instead of summing it.",
    "k": "One or more k values, space-separated (200 1600). Each k "
         "gives its own neighbourhood: the nearest k PERSONS, so the "
         "radius floats and Dist_k reports it.",
    "r": "Fixed radii in metres, space-separated. The mirror image of "
         "k: the area is fixed and the population floats (N_r###).",
    "model": "Distance decay weighting. 'no decay' counts every "
             "neighbour equally inside the neighbourhood.",
    "halflife": "The distance in metres at which a neighbour counts "
                "half as much. Only used when a decay model is "
                "chosen.",
    "decayeps": "Where the decayed sum is cut off: neighbours whose "
                "weight falls below this are ignored. A decayed sum "
                "has no natural edge, so this is what bounds the "
                "search. 1e-6 (the default) reaches about 20 "
                "half-lives and is slow; 1e-3 reaches about 10 and "
                "runs roughly four times faster, with a difference "
                "far below any sampling error. The actual distance "
                "in metres is reported in the messages.",
    "restgroup":
        "Optional. Name only the values you care about in the table "
        "above, then type a name here - say 'other' - and EVERY "
        "remaining value of the category field joins that group "
        "automatically. With 130 POI types this is the difference "
        "between five rows and a hundred and thirty.",
    "restinpop":
        "This tick decides what the shares are shares OF, so it is "
        "worth a moment. TICKED: the other values count as "
        "population, so 'fast food' is measured against everything "
        "present - benches and postboxes included. UNTICKED: only "
        "the values you named are population, so 'fast food' is "
        "measured against the eating places you listed. Both are "
        "real questions and they look identical on screen; pick the "
        "denominator you mean.",
    "keepoutside":
        "What happens to a row whose type you did NOT include - a "
        "library, when the reference population is eating places. "
        "'Give them results, counting as zero' (the default): the "
        "library is nobody's neighbour and changes no one else's "
        "numbers, but it still gets its own results, so you can ask "
        "what is around the library. 'Leave their results Null': the "
        "row is dropped from the run entirely. Note that a row you "
        "DID include whose count field is empty behaves like the "
        "first case anyway - zero people, still gets results.",
    "refmode":
        "How the reference population is built, from the simplest "
        "way upward. 'Every point counts as one' needs nothing else - "
        "one row, one thing. 'A field holds the count' is for rows "
        "that stand for several people (or guests, or dwellings). "
        "'Only selected types' is for a layer holding many kinds of "
        "object where only some belong: eating places among all POIs, "
        "say. Boxes that the chosen way does not need are greyed out.",
    "treatmode":
        "How the treatment population is built - the thing you count "
        "inside each neighbourhood. 'Not measuring one' is a real "
        "answer: you then get N and Dist_k alone, which is how far "
        "away the k nearest are. 'One column per group' suits data "
        "with a column of counts per group. 'Types from a type field' "
        "suits a labelled column, and you say which labels form which "
        "group. There is no count field here: k belongs to the "
        "reference population, so the treatment is counted in the "
        "same units and every share sits between 0 and 1.",
    "treatcatfield":
        "The column holding the type of each object, for building "
        "the groups. Usually the same column the reference "
        "population used - choose it here as well, so this section "
        "reads on its own.",
    "reftable":
        "Which values of the category field belong to the REFERENCE "
        "population - the people or places whose k nearest form each "
        "neighbourhood. Leave it EMPTY and every row belongs. This "
        "one choice decides what your shares are shares OF: list the "
        "eating places and 'fast food' is measured against eating "
        "places; leave it empty and the same run measures fast food "
        "against every point in the layer.",
    "treattable":
        "Which values form which GROUP in the treatment population - "
        "the thing you are counting inside each neighbourhood. One "
        "row per value: the value, and the name of the group it "
        "joins. Rows sharing a group name merge, so 'restaurant', "
        "'cafe' and 'pub' can all become 'eating'. You get a T_ "
        "column (the count) and an R_ column (its share of the "
        "reference population) for each group.",
    "treatvalue_RETIRED":
        "How much each row counts in the TREATMENT population. Leave "
        "it empty and the reference population's field is used, which "
        "is almost always what you want: both populations counted in "
        "the same units, so every share sits between 0 and 1. Give a "
        "different field and the R_ columns become a ratio of two "
        "different things - revenue per guest, say - which is a real "
        "measure but not a percentage.",
    "cattable": "One row per category value: which group it joins "
                "(leave blank for none) and whether it counts as "
                "population. Rows sharing a group name merge into "
                "that group - so no separators to remember, and a "
                "value can belong to a group WITHOUT being part of "
                "the population (services near residents).",
    "groupscount": "Whether category groups count PERSONS (weighted "
                   "by the population field, so shares have the same "
                   "denominator as N) or PLACES (rows).",
    "barrierraster":
        "A raster of crossing costs, one number per cell: how much "
        "effort it takes to pass through there. NoData or zero means "
        "free. Use it when the obstacle is continuous - marshland, "
        "rough terrain, a built-up core - rather than a line on a "
        "map.",
    "barrierrasters": "Friction rasters, where each cell value is "
                      "the crossing cost - positive deters, negative "
                      "carries, and -1 is the refused floor. They "
                      "combine with the rows "
                      "of the barrier table by the same overlap "
                      "rule.",
    "barriertable": "One row per barrier source - a point, line or "
                    "polygon layer, or a table of cells - "
                    "with the field holding its friction. Friction is "
                    "a DELAY, not a distance: entering a cell costs "
                    "1 + friction, so 3 is a river (four rounds), 0 "
                    "is open ground, and a NEGATIVE value down to -1 "
                    "is a facilitator - -0.9 makes a cell a tenth of "
                    "a round, which is how a motorway is modelled. "
                    "-1 and below are refused. Several "
                    "sources combine per the overlap rule, so a "
                    "river, a railway and a lake can be given "
                    "together.",
    "hlfield": "A field giving each point its OWN half-life in "
               "metres - an estimated median travel distance, a "
               "group-specific potential, whatever you have "
               "estimated. Rows are grouped into bandwidth bins and "
               "each bin gets its own exact pass.",
    "hlfromdist": "Self-calibrating bandwidth: enter a k, and each "
                  "point's own Dist_k - the radius it needed to "
                  "gather k persons - becomes its half-life. Dense "
                  "places get sharp kernels, thin places broad ones, "
                  "with no external estimate.",
    "hlbins": "How many bandwidth bins to use when the half-life "
              "varies. More bins follow the distribution more "
              "closely and cost more passes; distinct values fewer "
              "than this get an exact pass each.",
    "seed": "Seed for the parts of EquiPop that draw at random. Two "
            "uses. (1) Permutations, so a pseudo-p-value can be "
            "reproduced. (2) From 1.30, the 'sampled' growth model, "
            "where the cells of the ring that crosses k enter in an "
            "order drawn from this seed. Under 'whole' and "
            "'proportional' the counting engines remain fully "
            "deterministic and this seed does not affect them; under "
            "'sampled' it decides the answer. The order depends on "
            "the seed and on each cell's position, not on the row "
            "order of your file, so a re-sorted or re-exported "
            "dataset reproduces the same run. Leave it empty and one "
            "is drawn AND PRINTED, so an unplanned run can still be "
            "repeated afterwards. Recorded in the run manifest.",
    "catfield": "Build population and groups from the VALUES of one "
                "column (codes or names both work) instead of "
                "count fields.",
    "popvalues": "Which category values form the population. Empty "
                 "means all rows. Comma-separated, no quotes needed.",
    "treatvalues": "Which category values form groups: typeA; typeB "
                   "for one group each, or groupname: typeA, typeB "
                   "to merge several values into one named group.",
    "barrier": "Barriers as a DISTANCE INGREDIENT: a point, line or "
               "polygon layer, a table of cells, or a raster. Lines "
               "charge every grid cell they cross, polygons every "
               "cell they cover, rasters are sampled at cell "
               "midpoints.",
    "barrierfield": "The numeric field holding each feature's "
                    "crossing cost in rounds. For rasters the cell "
                    "value is the cost and this box is unused.",
    "barrieragg": "How several barrier features sharing one cell "
                  "combine. Additive (the default) stacks costs - a "
                  "river crossed at a railway costs both. Max/min/"
                  "mean are available when stacking is wrong.",
    "barrierx": "Easting column of a TABULAR barrier input.",
    "barriery": "Northing column of a tabular barrier input.",
    "dem": "Elevation raster: slopes become extra effort, so uphill "
           "neighbours are farther away than flat ones.",
    "tau": "Effort budgets in rounds, space-separated. With barriers "
           "or terrain, N_tau### counts the persons reachable within "
           "that many rounds instead of within a plain radius.",
    "roundtrip": "Count the journey home as well - the budget must "
                 "cover getting there AND back.",
    "existing": "What to do when result fields of the same name are "
                "already present: overwrite them, or stop.",
    "outmode": "Append results to the input layer, or write a new "
               "feature class (recommended for shapefiles: a file "
               "geodatabase has no 10-character field-name limit).",
    "outfc": "Path and name of the new {target}. Put it in "
             "{container} to keep full-length result names - "
             "shapefile field names are capped at 10 "
             "characters.{formatnote}",
    "outtable": "Where a TABLE input's results are written (.csv). "
                "The output carries your coordinates plus the result "
                "columns, in the original row order.",
    "unit": "The grid cell size in metres. Bigger cells mean fewer "
            "origins and much faster runs; smaller cells mean finer "
            "geography. This is the strongest speed control you "
            "have.",
    "selfpot": "Self-potential: how far away what is LOCAL - what "
               "your own cell already holds, the quantity "
               "reported as N_local - is treated as being. Rows "
               "are snapped to a "
               "grid, so everything in the origin's own cell sits at "
               "exactly the origin - distance zero - unless you say "
               "otherwise. That matters wherever one cell already "
               "contains k of whatever you are counting, which "
               "happens in a dense block or at a large cell size: "
               "the radius comes out as zero and k stops making any "
               "difference, so the nearest 100 and the nearest 1000 "
               "give the same answer. Leave this at 1 and the "
               "distance is estimated by spreading the cell's "
               "contents evenly across it, which recovers the radius "
               "you would have measured from individual points to "
               "within a fraction of a percent. Set it to 0.71 for "
               "the median distance instead of the radius, or to 0 "
               "to reproduce results from before this setting "
               "existed.",
    "overshoot": "What happens to the ring of cells that CROSSES k. "
                 "EquiPop grows a neighbourhood outward until it "
                 "holds k people, and the ring that takes it past k "
                 "almost never lands on k exactly. 'Whole ring' takes "
                 "all of it - what EquiPop did before 1.30 - so ask a "
                 "3x3 of cells holding ten each for k=11 and you "
                 "receive 50. That is worst at SMALL k and AT "
                 "BOUNDARIES, which is exactly where segregation is "
                 "measured: on a planted sharp edge the share R_k in "
                 "the boundary cell reads 0.20 whole against 0.02 "
                 "proportional. 'Proportional share' takes the same "
                 "fraction of every cell in that ring, so N_k is "
                 "exactly k; it produces FRACTIONAL PEOPLE, which are "
                 "estimates rather than persons, and value "
                 "statistics refuse it because a quarter of a cell "
                 "has no median, percentile or Gini. 'Sampled' takes "
                 "whole cells one at a time, in an order drawn from "
                 "the seed, until k is reached - this is the original "
                 "EquiPop method from the 2014 C# tool, kept so old "
                 "results can be reproduced and compared. Sampled is "
                 "NOT proportional with the fractions removed: it is "
                 "that answer rounded up to a whole cell, and "
                 "different seeds do not average the difference away. "
                 "Set 'whole ring' to reproduce numbers from before "
                 "1.30 exactly.",
    "autoproj": "When the input is in degrees, project it on the fly "
                "to the metric CRS that fits the data (the UTM zone "
                "is computed from the extent). The stored data is "
                "not modified. Tables cannot be auto-projected.",
    "shortnames": "Allow result names to be shortened to 10 "
                  "characters so they fit a shapefile. Names stay "
                  "unique - no two results ever merge - and the full "
                  "mapping is printed in the messages.",
    "values": "The treatment fields - what you measure among the "
              "neighbours: income, rent, age. One set of result "
              "columns per field. These are AVERAGED over the "
              "reference population, never added up, so give values "
              "per unit: income per person, not the household total. "
              "A column meant to be summed belongs in tool 1.",
    "measures": "Tick the statistics you want; only those are "
                "calculated. Leaving every box unticked means the "
                "classic trio - mean, median and Gini. "
                "Nv_<field>_k always reports how many neighbours "
                "actually had a value.",
    "pcts": "Percentiles as plain numbers, e.g. 10 25 75 90. Used "
            "only when 'percentiles' is ticked; results arrive as "
            "P10_<field>_k and so on.",
}

# THE TOOL NAMES, in one place. BACKLOG 237: the two doors had drifted
# on three of four - Pro still said "3. Continental run from a folder
# of rasters" after QGIS was renamed, and machines 1 and 2 differed in
# their parenthetical. door_parity.py checked parameter NAMES but not
# LABELS, so nothing noticed. A name in two places drifts, exactly like
# a rule in two places.
LABELS = {
    "CountsShares": "1. Counts and Shares (k / radius / decay)",
    "ValueStatistics": "2. Value Statistics (numeric fields among the "
                       "k nearest)",
    "ContinentalRasters": "3. Raster Data Curation",
    "SpatialDemography": "4. Spatial Demographic Analysis",
}


SUMMARY = {
    "CountsShares":
        "Builds an egocentric neighbourhood around EVERY point and "
        "counts what is inside it. Two ways to draw it: k (the "
        "nearest k persons - population fixed, radius floats, "
        "reported as Dist_k) or a radius in metres (area fixed, "
        "population floats). Group fields add counts and shares "
        "(T_ and R_). Barriers and terrain turn plain distance into "
        "EFFORT: rivers, railways, lakes, friction rasters and "
        "slopes make neighbours farther away in rounds, and N_tau### "
        "counts who is reachable within a budget. Inputs may be "
        "point layers (geometry is read directly) or tables with "
        "coordinate columns; coordinates must be metric.",
    "ValueStatistics":
        "Describes TREATMENT fields - income, rent, age - among the "
        "k nearest members of the REFERENCE population around every "
        "point. Tick the measures you need (mean, median, Gini, sd, "
        "variance, se, min, max, count, sum, range, percentiles); "
        "only those are computed. With a count field every statistic "
        "is weighted by it, so a point standing for forty counts "
        "forty times a point standing for one - including the "
        "median, the Gini and every percentile. Nv_<field>_k reports "
        "how many neighbours had a usable value, so thin coverage is "
        "visible rather than hidden.",
    "SpatialDataFetch":
        "Downloads data into a folder, writes a manifest recording "
        "exactly what was fetched and from where, and STOPS. It "
        "produces no layer on purpose: a tool that both downloads and "
        "analyses makes every result computed through it "
        "unreproducible offline, because the same call next year may "
        "return revised estimates or nothing at all. The manifest is "
        "the deliverable rather than the files - it carries the DOI, "
        "the citation, the licence and a checksum per file, taken "
        "from what the provider states - so the folder stays citable "
        "and can be checked years later.",
    "SpatialDemography":
        "Demographic indices computed over the k NEAREST PEOPLE rather "
        "than over an administrative unit. WorldPop publishes a "
        "gridded dependency ratio built from each cell's own age "
        "structure; this describes the population a person is actually "
        "among, and inherits nothing from any boundary. Every index is "
        "a ratio of two groups counted over the same neighbourhood, so "
        "several cost one pass over the data rather than one each. "
        "Rate measures - TFR, ASFR, birth and death rates, life "
        "expectancy - are deliberately absent: they need vital events, "
        "and an age-sex folder carries stock, not flow.",
    "ContinentalRasters":
        "Builds k-neighbourhoods straight from a FOLDER of population "
        "rasters, at the scale of a continent. Subfolders are "
        "searched, so a download that arrives one folder per country "
        "can stay exactly as it is. Filenames are read for the cohort "
        "- sex, age, year - and the COUNTRY is deliberately ignored, "
        "because different countries are different GROUND and stack "
        "as rows, while different cohorts are different COLUMNS on "
        "the same ground. Which is which is decided by measuring "
        "where the rasters actually hold data, never by their names, "
        "so the rule survives any renaming. Population counts are "
        "kept as FRACTIONS: a cell holding 0.4 people stays 0.4, "
        "because rounding them away deleted half the population and "
        "more of it the further north you went.",
}

USAGE = {
    "SpatialDataFetch":
        "Run it once with DOWNLOAD unticked: it lists what would be "
        "fetched, how many files and under which licence, and takes "
        "nothing. Leave the dataset box empty and it lists the "
        "datasets; leave the version box empty and it lists those. "
        "Give a year - a release covers 2015 to 2030, so without one "
        "a single country offers about 960 files rather than 60. "
        "Nothing is ever overwritten: a file already present is "
        "reused if its checksum matches and the run stops if it does "
        "not.",
    "SpatialDemography":
        "Point it at the same folder machine 3 uses and tick the "
        "indices you want. The suggested columns are shown in the log "
        "before anything is computed, so you can see exactly which "
        "cohorts are being added up; boxes 2c and 2d replace them for "
        "a single ticked index. WorldPop's age bands are not all five "
        "years wide - 0 is under-one alone, 1 covers 1-4, and 90 is "
        "open-ended - and the selection accounts for that, so 15-49 "
        "means 15 to 49 and not 15 to 54.",
    "ContinentalRasters":
        "Start with one folder and one k. Leave the projection blank "
        "and a fitting one is suggested from the data. Cell size is "
        "the analysis grid, not the raster's own resolution - 1000 m "
        "is a sensible continental start and 100 m is a very large "
        "run. For anything bigger than a few hundred thousand cells, "
        "give a tiles folder: the answers are identical, they are "
        "written out as the run goes, and it resumes where it stopped "
        "if it is interrupted.",
    "CountsShares":
        "Start simple: input layer, one k, nothing else. Add group "
        "fields for shares. Add a barrier layer only when barriers "
        "matter - it switches the run to the effort engine and takes "
        "longer. Cell size is the speed control: doubling it "
        "quarters the number of origins. Long result names need a "
        "roomy target: shapefile field names cap at 10 characters, "
        "so {container} is the safer home for them.",
    "ValueStatistics":
        "Give the treatment values, tick the measures, set k. Use the "
        "reference population's count field whenever a point stands "
        "for more than one - people, jobs, dwellings, services. Gini "
        "refuses negative values, and percentiles need numbers in "
        "their box. As with machine 1, cell size controls the "
        "runtime and {container} avoids the shapefile name limit.",
}


# ---------------------------------------------------------------
# Words that MUST differ per door (v1.29.1)
#
# Almost every box means the same thing in both doors and therefore
# takes the same sentence - that is the whole point of this file, and
# 1.29.0 was spent proving it. A handful of words are the exception:
# only the door knows what a roomy output container is called on its
# own side. Pro writes a feature class into a file geodatabase; QGIS
# writes a layer into a GeoPackage and refuses a name with no
# extension at all.
#
# So the texts carry a TOKEN and the door fills it in - the same
# mechanism fields.py has used for the refusal message since 1.18.0,
# rather than a second dictionary of QGIS wording. One text per box
# stays true, which is what 1.29.0 was for.
#
# Found by John in the field (1.29.0): the Results tooltip told a
# QGIS user to "put it in a file geodatabase", which does not exist
# there, and he reasonably read it as "you must save into a database
# first".
VOCAB = {
    "target": "feature class",
    "container": "a file geodatabase",
    "formatnote": "",
}
VOCAB_QGIS = {
    "target": "layer",
    "container": "a GeoPackage (.gpkg)",
    "formatnote": (" QGIS reads the format from the file extension, "
                   "so end the name with .gpkg or .shp - a bare name "
                   "is refused."),
}


def fill(text: str, vocab: dict | None = None) -> str:
    """Put the door's own words into a shared sentence.

    An unknown token is LEFT ALONE rather than blanked, so a typo
    shows up as {like_this} in the dialog instead of vanishing - and
    a test refuses to ship any text still holding one.
    """
    words = dict(VOCAB)
    if vocab:
        words.update(vocab)
    for key, value in words.items():
        text = text.replace("{" + key + "}", value)
    return text


def help_for(name: str, default: str = "",
             vocab: dict | None = None) -> str:
    """The explanation for one parameter, or `default` if none."""
    return fill(HELP.get(name, default), vocab)


def summary_for(tool: str, vocab: dict | None = None) -> str:
    """What this tool does, in one paragraph."""
    return fill(SUMMARY[tool], vocab)


def usage_for(tool: str, vocab: dict | None = None) -> str:
    """How to approach it - the advice a first-time user needs."""
    return fill(USAGE[tool], vocab)


def missing_help(names) -> list:
    """Parameter names with no explanation. Empty list = ready to
    ship; anything else is a release blocker in every door."""
    return [n for n in names if n not in HELP]
