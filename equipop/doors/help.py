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
    "seed": "Seed for the parts of EquiPop that use permutations. "
            "The counting engines are deterministic; this is "
            "recorded in the run manifest so a pseudo-p-value can be "
            "reproduced.",
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
    "outfc": "Path/name of the new feature class. Put it in a file "
             "geodatabase to keep full-length result names.",
    "outtable": "Where a TABLE input's results are written (.csv). "
                "The output carries your coordinates plus the result "
                "columns, in the original row order.",
    "unit": "The grid cell size in metres. Bigger cells mean fewer "
            "origins and much faster runs; smaller cells mean finer "
            "geography. This is the strongest speed control you "
            "have.",
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
}

USAGE = {
    "CountsShares":
        "Start simple: input layer, one k, nothing else. Add group "
        "fields for shares. Add a barrier layer only when barriers "
        "matter - it switches the run to the effort engine and takes "
        "longer. Cell size is the speed control: doubling it "
        "quarters the number of origins. Results are appended to the "
        "input unless you choose a new feature class; shapefile "
        "targets cap field names at 10 characters, so a file "
        "geodatabase is the safer home for long names.",
    "ValueStatistics":
        "Give the value fields, tick the measures, set k. Use the "
        "full-population field whenever a point stands for more than "
        "one person. Gini refuses negative values, and percentiles "
        "need numbers in their box. As with machine 1, cell size "
        "controls the runtime and a file geodatabase avoids the "
        "shapefile name limit.",
}


def help_for(name: str, default: str = "") -> str:
    """The explanation for one parameter, or `default` if none."""
    return HELP.get(name, default)


def summary_for(tool: str) -> str:
    """What this tool does, in one paragraph."""
    return SUMMARY[tool]


def usage_for(tool: str) -> str:
    """How to approach it - the advice a first-time user needs."""
    return USAGE[tool]


def missing_help(names) -> list:
    """Parameter names with no explanation. Empty list = ready to
    ship; anything else is a release blocker in every door."""
    return [n for n in names if n not in HELP]
