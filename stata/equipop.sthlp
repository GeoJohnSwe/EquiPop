{smcl}
{* *! version 1.36}{...}
{vieweralsosee "[R] regress" "help regress"}{...}
{viewerjumpto "Syntax" "equipop##syntax"}{...}
{viewerjumpto "Description" "equipop##description"}{...}
{viewerjumpto "Options" "equipop##options"}{...}
{viewerjumpto "Stored results" "equipop##results"}{...}
{viewerjumpto "Examples" "equipop##examples"}{...}

{title:Title}

{phang}
{bf:equipop} {hline 2} k-nearest neighbour context variables (EquiPop 1.36)

{marker syntax}{...}
{title:Syntax}

{p 8 17 2}
{cmd:equipop}
{weight}
{ifin}
{cmd:,} {opt x(varname)} {opt y(varname)}
[{it:options}]

{synoptset 24 tabbed}{...}
{synopthdr}
{synoptline}
{syntab:Required}
{synopt:{opt x(varname)}}The easting.{p_end}
{synopt:{opt y(varname)}}The northing, on the same metric system as x().{p_end}
{syntab:Neighbourhood}
{synopt:{opt k(numlist)}}One or more k values, space-separated (200 1600).{p_end}
{synopt:{opt r(numlist)}}Fixed radii in metres, space-separated.{p_end}
{synopt:{opt unit(#)}}The grid cell size in metres.{p_end}
{synopt:{opt selfpot(#)}}Self-potential: how far away what is LOCAL - what your...{p_end}
{syntab:Population}
{synopt:{opt treat(varlist)}}Group counts: persons of the group at this point (use...{p_end}
{synopt:{opt pop(varname)}}How many each point stands for - people, jobs,...{p_end}
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
{opt x(varname)} The easting. Must be metric - projected coordinates, not degrees. Rows with a missing coordinate receive missing results rather than stopping the command.
{p_end}

{phang}
{opt y(varname)} The northing, on the same metric system as x().
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

{marker examples}{...}
{title:Examples}

{phang}{cmd:. equipop, x(X_local) y(Y_local) k(50)}{p_end}
{phang}{cmd:. equipop, x(X_local) y(Y_local) treat(HighEdu) k(25 50 200) unit(100)}{p_end}
{phang}{cmd:. equipop if urban==1, x(X) y(Y) treat(HighEdu) k(50) replace}{p_end}
{phang}{cmd:. equipop [fweight=pop], x(X) y(Y) treat(HighEdu) k(50)}{p_end}
{phang}{cmd:. regress income `r(varlist)'}{p_end}

{marker author}{...}
{title:Author}

{pstd}John Osth, OsloMet. {browse "https://github.com/GeoJohnSwe/EquiPop"}{p_end}
