{smcl}
{* *! version 1.44.6}{...}
{vieweralsosee "[R] regress" "help regress"}{...}
{viewerjumpto "Syntax" "equipop##syntax"}{...}
{viewerjumpto "Description" "equipop##description"}{...}
{viewerjumpto "Options" "equipop##options"}{...}
{viewerjumpto "Stored results" "equipop##results"}{...}
{viewerjumpto "Diagnostics" "equipop##diagnostics"}{...}
{viewerjumpto "Examples" "equipop##examples"}{...}

{title:Title}

{phang}
{bf:equipop} {hline 2} k-nearest neighbour context variables (EquiPop 1.44.6)

{marker syntax}{...}
{title:Syntax}

{p 8 17 2}
{cmd:equipop}
{weight}
{ifin}
{cmd:,} {opt x(varname)} {opt y(varname)}
[{it:options}]

{pstd}
Report on the Python this Stata is using, and on the libraries EquiPop needs. Reads nothing and changes nothing.

{p 8 17 2}
{cmd:equipop doctor}

{pstd}
Install or update the calculating engine, into the Python this Stata is using. Add {cmd:repair} when a library is present but will not load.

{p 8 17 2}
{cmd:equipop setup} [{cmd:, repair}]

{synoptset 24 tabbed}{...}
{synopthdr}
{synoptline}
{syntab:Required}
{synopt:{opt x(varname)}}The easting, in metres or another metric unit.{p_end}
{synopt:{opt y(varname)}}The northing, on the same system as x();{p_end}
{syntab:Neighbourhood}
{synopt:{opt k(numlist)}}One or more k values, space-separated (200 1600).{p_end}
{synopt:{opt r(numlist)}}Fixed radii in metres, space-separated.{p_end}
{synopt:{opt unit(#)}}The grid cell size in metres.{p_end}
{synopt:{opt selfpot(#)}}Self-potential: how far away what is LOCAL - what your...{p_end}
{syntab:Population}
{synopt:{opt treat(varlist)}}Group counts: persons of the group at this point (use...{p_end}
{synopt:{opt pop(varname)}}How many each point stands for - people, jobs,...{p_end}
{synopt:{opt treatmode(string)}}What the treat() variables contain.{p_end}
{synopt:{opt missing(numlist)}}Values that mean NO DATA rather than a number, listed...{p_end}
{syntab:Distance weighting}
{synopt:{opt decay(string)}}Weights each neighbour by how far away it is, and...{p_end}
{synopt:{opt halflife(#)}}The distance at which a neighbour counts half as much,...{p_end}
{synopt:{opt halflifevar(varname)}}A variable holding each place's own half-life, so...{p_end}
{synopt:{opt bins(#)}}How many bands of similar bandwidth halflifevar() is...{p_end}
{synopt:{opt overshoot(string)}}What happens to the ring of cells that CROSSES k.{p_end}
{synopt:{opt selfpotname(string)}}How far a place is from itself - the same three choices...{p_end}
{syntab:Coordinates}
{synopt:{opt project}}Projects x() and y() from longitude and latitude in...{p_end}
{synopt:{opt epsg(#)}}Chooses the projection -project- uses, instead of...{p_end}
{syntab:Output}
{synopt:{opt prefix(string)}}Prepends a string to every new variable name, so several...{p_end}
{synopt:{opt replace}}Drops the result variables this run is about to create...{p_end}
{synoptline}
{p2colreset}{...}
{p 4 6 2}
{cmd:fweight}s are allowed; see {help weight}. A weight says how many people the row stands for.
{p_end}

{marker description}{...}
{title:Description}

{pstd}
equipop builds, for every observation, the neighbourhood of its k
nearest neighbours measured in PEOPLE rather than in rows, and reports
what that neighbourhood contains. Neighbourhoods are individual and
overlapping, so they cut across administrative boundaries instead of
being bound by them.

{pstd}
For each k it adds N_k, the population actually gathered, and Dist_k,
the distance travelled to gather it. For each variable in treat() it
adds T_var_k, the count of that group inside the neighbourhood, and
R_var_k, that count as a share of the observed population. Radii in r()
give the same columns, named _r<radius>. treat() is optional: without it
you get neighbourhood size and reach alone.

{pstd}
Coordinates must be metric. Rows with missing coordinates receive
missing results rather than stopping the command. if and in restrict
which rows RECEIVE results; every row still counts as a neighbour to
others.

{pstd}
equipop needs Python. See {c -({c )-}help python{c )-} and, for the
installation, the file TESTING_STATA.md in the EquiPop distribution.
Note that Stata and Anaconda do not mix: use a plain python.org Python
for Stata.

{marker options}{...}
{title:Options}

{phang}
{opt x(varname)} The easting, in metres or another metric unit. Longitude in degrees is accepted with the -project- option, which converts it first. Rows with a missing coordinate receive missing results rather than stopping the command.
{p_end}

{phang}
{opt y(varname)} The northing, on the same system as x(); or latitude in degrees, with -project-.
{p_end}

{phang}
{opt treat(varlist)} Group counts: persons of the group at this point (use 0/1 when points are individuals). Produces T_<group>_k (count) and R_<group>_k (share). These columns are ADDED UP across the neighbourhood, so give TOTALS, never averages: total income at this point, not mean income per person here. A per-point average belongs in tool 2 (Value Statistics), which weights it by the reference population instead of summing it.
{p_end}

{phang}
{opt k(numlist)} One or more k values, space-separated (200 1600). Each k gives its own neighbourhood: the nearest k PERSONS, so the radius floats and Dist_k reports it.
{p_end}

{phang}
{opt r(numlist)} Fixed radii in metres, space-separated. The mirror image of k: the area is fixed and the population floats (N_r###).
{p_end}

{phang}
{opt unit(#)} The grid cell size in metres. Bigger cells mean fewer origins and much faster runs; smaller cells mean finer geography. This is the strongest speed control you have.
{p_end}

{phang}
{opt pop(varname)} How many each point stands for - people, jobs, dwellings, services, anything countable. Leave empty when every point counts as one. k counts these, so this field decides how far the k-search must travel - and in Value Statistics every statistic is weighted by it, so a point standing for 40 counts 40 times a point standing for one.
{p_end}

{phang}
{opt prefix(string)} Prepends a string to every new variable name, so several runs can live side by side in one dataset. prefix(a_) turns N_25 into a_N_25.
{p_end}

{phang}
{opt selfpot(#)} Self-potential: how far away what is LOCAL - what your own cell already holds, the quantity reported as N_local - is treated as being. Rows are snapped to a grid, so everything in the origin's own cell sits at exactly the origin - distance zero - unless you say otherwise. That matters wherever one cell already contains k of whatever you are counting, which happens in a dense block or at a large cell size: the radius comes out as zero and k stops making any difference, so the nearest 100 and the nearest 1000 give the same answer. Leave this at 1 and the distance is estimated by spreading the cell's contents evenly across it, which recovers the radius you would have measured from individual points to within a fraction of a percent. Set it to 0.71 for the median distance instead of the radius, or to 0 to reproduce results from before this setting existed.
{p_end}

{phang}
{opt treatmode(string)} What the treat() variables contain. counts (the default) means each one holds the NUMBER OF PEOPLE of that group at the point, which is how census and register data normally arrive, and how the GIS versions of EquiPop read it - it needs a population, from pop() or [fweight=]. flags means each one holds 0 or 1, a share of the row's own population, which is the older Stata convention. Getting this wrong cannot pass silently: a group larger than the population containing it is refused, with a message naming which setting to use.
{p_end}

{phang}
{opt missing(numlist)} Values that mean NO DATA rather than a number, listed and separated by spaces. Census and register extracts carry these: -666666666 for a suppressed median in US ACS data, -9 or 999 elsewhere. Left undeclared they are arithmetic - a neighbourhood mean lands near minus forty million, and it lands there quietly. A case whose value is declared missing STILL COUNTS AS PEOPLE towards k, and still receives its own results; only its value drops out. Shares are then divided by the people actually observed, never by everybody present: 400 people with 60 of unknown group gives a denominator of 340.
{p_end}

{phang}
{opt decay(string)} Weights each neighbour by how far away it is, and reports the weighted totals alongside the plain ones: ND_ for the population, TD_ for each group, RD_ for the share. THE NEIGHBOURHOOD ITSELF IS UNCHANGED. k still means the k nearest people - ask for 300 and you get the 300 nearest - and the radius is still the distance you must travel to reach them. Only the contents are re-weighted, so a person at the edge counts for less than one standing beside you. The decayed totals are therefore always smaller than the plain ones. negexp halves the weight every half-life and is the usual choice. power falls quickly and then very slowly, so distant places never quite stop counting. expnormal, expsqrt and lognormal shape the curve differently again - see the manual.
{p_end}

{phang}
{opt halflife(#)} The distance at which a neighbour counts half as much, in the same units as your coordinates. Required by decay(), unless halflifevar() gives one per place instead.
{p_end}

{phang}
{opt halflifevar(varname)} A variable holding each place's own half-life, so bandwidth varies across the map - wide in the countryside, tight in a city. Places are grouped into bins() bands of similar bandwidth and each band is run once, because running every distinct value separately would be needlessly slow.
{p_end}

{phang}
{opt bins(#)} How many bands of similar bandwidth halflifevar() is grouped into. More bands follow the variation more closely and take longer. Ignored without halflifevar(). Default 10.
{p_end}

{phang}
{opt selfpotname(string)} How far a place is from itself - the same three choices the QGIS and ArcGIS versions offer, by name rather than by number. none means no distance at all, and Dist_k can then come out as zero. median means half of what your own cell holds is nearer than this. full is the radius at which the cell's own people are reached, and is the default. selfpot(#) still takes any number between 0 and 1 if you want one.
{p_end}

{phang}
{opt overshoot(string)} What happens to the ring of cells that CROSSES k. EquiPop grows a neighbourhood outward until it holds k people, and the ring that takes it past k almost never lands on k exactly. 'Whole ring' takes all of it - what EquiPop did before 1.30 - so ask a 3x3 of cells holding ten each for k=11 and you receive 50. That is worst at SMALL k and AT BOUNDARIES, which is exactly where segregation is measured: on a planted sharp edge the share R_k in the boundary cell reads 0.20 whole against 0.02 proportional. 'Proportional share' takes the same fraction of every cell in that ring, so N_k is exactly k; it produces FRACTIONAL PEOPLE, which are estimates rather than persons, and value statistics refuse it because a quarter of a cell has no median, percentile or Gini. 'Sampled' takes whole cells one at a time, in an order drawn from the seed, until k is reached - this is the original EquiPop method from the 2014 C# tool, kept so old results can be reproduced and compared. Sampled is NOT proportional with the fractions removed: it is that answer rounded up to a whole cell, and different seeds do not average the difference away. Set 'whole ring' to reproduce numbers from before 1.30 exactly.
{p_end}

{phang}
{opt project} Projects x() and y() from longitude and latitude in degrees to metres, using the UTM zone the data sits in, before anything is counted. The run reports which zone it used and returns it in r(epsg) and r(crs). Distances computed on unprojected degrees are not distances: a degree of longitude is shorter than a degree of latitude everywhere except the equator - by a quarter at 41 degrees, by half at 60 - so neighbourhoods come out stretched and the k nearest neighbours are not the nearest k. Without this option, coordinates that look like degrees raise a warning and are otherwise left alone. One zone is used for the whole dataset. If you already project your own data, you do not need this: pass the projected coordinates and leave it off.
{p_end}

{phang}
{opt epsg(#)} Chooses the projection -project- uses, instead of letting it pick the zone from the data. WGS84 UTM only: 32601-32660 north of the equator, 32701-32760 south. Requires -project-.
{p_end}

{phang}
{opt replace} Drops the result variables this run is about to create before creating them. Without it the command stops rather than overwriting silently.
{p_end}

{marker results}{...}
{title:Stored results}

{pstd}{cmd:equipop} stores the following in {cmd:r()}:

{synoptset 20 tabbed}{...}
{p2col 5 20 24 2: Scalars}{p_end}
{synopt:{cmd:r(unit)}}cell size in metres{p_end}
{synopt:{cmd:r(selfpot)}}self-potential used{p_end}
{synopt:{cmd:r(N_origins)}}rows in the sample{p_end}
{synopt:{cmd:r(N_missing)}}rows that received no result{p_end}
{p2col 5 20 24 2: Macros}{p_end}
{synopt:{cmd:r(cmd)}}equipop{p_end}
{synopt:{cmd:r(cmdline)}}command as typed{p_end}
{synopt:{cmd:r(varlist)}}names of the variables created{p_end}
{synopt:{cmd:r(treat)}}treatment variables used{p_end}
{synopt:{cmd:r(k)}}k values requested{p_end}
{synopt:{cmd:r(r)}}radii requested{p_end}
{p2colreset}{...}

{pstd}
r(varlist) is the useful one: it hands back the names just created, so a
regression or a loop need not repeat them.

{marker diagnostics}{...}
{title:Diagnostics}

{pstd}
equipop runs its calculations in Python, so it depends on the Python
that Stata is configured to use and on three libraries inside it: numpy,
pandas and scipy. When something is wrong there, the failure happens
before any EquiPop code is reached and the error message will not
mention EquiPop.

{phang}{cmd:. equipop setup}{p_end}

{pstd}
installs the engine into the Python Stata is using, so it cannot land in
a different one. Add {c -({c )-}cmd:repair{c )-} - {c -({c
)-}cmd:equipop setup, repair{c )-} - to reinstall numpy, scipy and
pandas as well, which is the fix when a library is installed but refuses
to load. Restart Stata afterwards: Stata starts Python once per session
and keeps what it first loaded.

{phang}{cmd:. equipop doctor}{p_end}

{pstd}
prints which Python is in use, which processor it is built for, and the
state of every library - present, absent, or installed but refusing to
load. Two cases it names directly: a library built for a different
processor than the Python loading it (common on Apple Silicon, where an
Intel package sits in the user folder), and a package installed into a
different Python than the one Stata uses.

{pstd}
Install into the Python whose path the report prints, and restart Stata
afterwards: Stata starts Python once per session and keeps the packages
it first loaded.

{pstd}
See also {c -({c )-}help python{c )-}, and {c -({c )-}cmd:python query{c
)-}, which reports Stata's own view of the same interpreter.

{marker examples}{...}
{title:Examples}

{phang}{cmd:. equipop setup}{p_end}
{phang}{cmd:. equipop doctor}{p_end}
{phang}{cmd:. equipop, x(X_local) y(Y_local) k(50)}{p_end}
{phang}{cmd:. equipop, x(X_local) y(Y_local) treat(HighEdu) k(25 50 200) unit(100)}{p_end}
{phang}{cmd:. equipop if urban==1, x(X) y(Y) treat(HighEdu) k(50) replace}{p_end}
{phang}{cmd:. equipop [fweight=pop], x(X) y(Y) treat(HighEdu) k(50)}{p_end}
{phang}{cmd:. regress income `r(varlist)'}{p_end}

{marker author}{...}
{title:Author}

{pstd}John Östh, OsloMet. {browse "https://github.com/GeoJohnSwe/EquiPop"}{p_end}
