{smcl}
{* *! version 1.63.1}{...}
{vieweralsosee "equipop" "help equipop"}{...}
{viewerjumpto "Syntax" "equipop_run##syntax"}{...}
{viewerjumpto "Engines" "equipop_run##engines"}{...}
{viewerjumpto "Examples" "equipop_run##examples"}{...}

{title:Title}

{phang}
{bf:equipop_run} {hline 2} EquiPop's other engines from Stata (EquiPop 1.63.1)

{marker syntax}{...}
{title:Syntax}

{p 8 17 2}
{cmd:equipop_run} {cmd:,} {opt engine(name)} {opt x(varname)} {opt y(varname)} [{it:engine options}] [{opt unit(#)} {opt weight(varname)} {opt selfpot(#)} {opt replace}]

{pstd}{it:name} is one of {cmd:counts}, {cmd:stats}, {cmd:friction}, {cmd:slope}, {cmd:fca} or {cmd:lisa}.{p_end}

{marker description}{...}
{title:Description}

{pstd}{cmd:equipop_run} builds the same bespoke neighbourhoods as {help equipop}, the k nearest people around every observation, and hands them to one of EquiPop's engines. The results come back as new variables, one value per observation.{p_end}

{pstd}It uses EVERY observation: there is no {it:if} or {it:in}, and no {cmd:prefix()}. For counts and shares with those, with frequency weights, distance decay or projection from degrees, use {help equipop}. Variable names that would contain a full stop have it replaced by an underscore. Without {cmd:replace}, a result variable that already exists stops the command.{p_end}

{pstd}Requires Stata 17 or later and the equipop Python package in the Python Stata uses: run {cmd:equipop doctor} to check and {cmd:equipop setup} to install.{p_end}

{marker engines}{...}
{title:Engines and their options}

{phang}{cmd:counts} {hline 2} {opt treat(varlist)} {opt k(numlist)} {opt r(numlist)}. Neighbourhood size, reach and the count and share of each treatment, as {help equipop}: N_{it:k}, Dist_{it:k}, T_{it:v}_{it:k}, R_{it:v}_{it:k}.{p_end}

{phang}{cmd:stats} {hline 2} {opt values(varlist)} {opt k(numlist)} {opt r(numlist)} [{opt stats(string)}]. Statistics of numeric variables among the k nearest; {cmd:stats()} lists them (default {cmd:mean median gini}). Nv_ is the number of neighbours with a value.{p_end}

{phang}{cmd:friction} {hline 2} {opt treat(varname)} {opt k(numlist)} {opt tau(numlist)} [{opt friction(path)}]. Neighbourhoods grown through barriers that cost effort to cross; {cmd:friction()} names a table of cells and their cost.{p_end}

{phang}{cmd:slope} {hline 2} {opt treat(varname)} {opt k(numlist)} {opt tau(numlist)} {opt dem(path)} [{opt model(tobler|linear)} {opt roundtrip}]. As {cmd:friction}, with climbing cost from an elevation raster.{p_end}

{phang}{cmd:fca} {hline 2} {opt demandvar(varname)} {opt supply(path)} [{opt supplycol(name)} {opt supplyx(name)} {opt supplyy(name)} {opt halflife(#)} {opt reach(decay|r|k)} {opt kfca(#)} {opt rfca(#)} {opt method(2sfca|3sfca)}]. Floating catchment accessibility: the observations are the demand, the supply comes from a .csv, .dta or .sav file. Returns {cmd:A} (accessibility) and {cmd:J} (the supply side's ratio).{p_end}

{phang}{cmd:lisa} {hline 2} {opt values(varname)} [{opt k(#)} {opt wperm(#)}]. Local Moran's I on cell means, with the {cmd:k()} nearest cells as neighbours (default 8) and {cmd:wperm()} permutations, a whole number of 1 or more (default 199): LISA_{it:v}_Ii, LISA_{it:v}_quad (1 HH, 2 LL, 3 HL, 4 LH) and LISA_{it:v}_p.{p_end}

{phang}Common to all: {opt unit(#)} is the cell size in metres, any number above zero (default 100); {opt weight(varname)} the number of people a row stands for; {opt selfpot(#)}, between 0 and 1, how far away an observation's own cell counts (default 1); {opt replace} replaces result variables that exist.{p_end}

{marker examples}{...}
{title:Examples}

{phang}{cmd:. findfile equipop_test_data.dta}{p_end}
{phang}{cmd:. use "`r(fn)'", clear}{p_end}
{phang}{cmd:. equipop_run, engine(stats) x(X_local) y(Y_local) values(ValFloat) k(200)}{p_end}
{phang}{cmd:. equipop_run, engine(lisa) x(X_local) y(Y_local) values(ValFloat) k(8)}{p_end}

{marker references}{...}
{title:References}

{phang}Östh, J., W. A. V. Clark, and B. Malmberg. 2015. Measuring the scale of segregation using k-nearest neighbor aggregates. {it:Geographical Analysis} 47: 34-49.{p_end}

{phang}Östh, J., J. Lyhagen, and A. Reggiani. 2016. A new way of determining distance decay parameters in spatial interaction models with application to job accessibility analysis in Sweden. {it:European Journal of Transport and Infrastructure Research} 16: 344-363.{p_end}

{marker author}{...}
{title:Author}

{pstd}John Östh{break}
OsloMet - Oslo Metropolitan University, Norway; Lund University and Uppsala University, Sweden{break}
{browse "mailto:johnosth@oslomet.no":johnosth@oslomet.no}{break}
{browse "https://github.com/GeoJohnSwe/EquiPop"}{p_end}
