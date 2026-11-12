{smcl}
{* *! version 1.64.1}{...}
{vieweralsosee "equipop" "help equipop"}{...}
{viewerjumpto "Syntax" "equipop_run##syntax"}{...}
{viewerjumpto "Engines" "equipop_run##engines"}{...}
{viewerjumpto "Examples" "equipop_run##examples"}{...}
{viewerjumpto "Stored results" "equipop_run##results"}{...}

{title:Title}

{phang}
{bf:equipop_run} {hline 2} EquiPop's other engines from Stata (EquiPop 1.64.1)

{marker syntax}{...}
{title:Syntax}

{p 8 17 2}
{cmd:equipop_run} {ifin} {cmd:,} {opt engine(name)} {opt x(varname)} {opt y(varname)} [{it:engine options}] [{opt unit(#)} {opt weight(varname)} {opt treatmode(counts|flags)} {opt over:shoot(whole|proportional)} {opt origin:rule(include|exclude)} {opt selfpot(#)} {opt replace}]

{pstd}{it:name} is one of {cmd:counts}, {cmd:stats}, {cmd:friction}, {cmd:slope}, {cmd:fca} or {cmd:lisa}.{p_end}

{marker description}{...}
{title:Description}

{pstd}{cmd:equipop_run} builds the same bespoke neighbourhoods as {help equipop}, the k nearest people around every observation, and hands them to one of EquiPop's engines. The results come back as new variables, one value per observation.{p_end}

{pstd}{it:if} and {it:in} choose the observations that GET results, exactly as in {help equipop}: everybody still counts as a neighbour, so {cmd:equipop_run if urban==1, ...} computes for urban rows among neighbours of every kind. To leave people out of the neighbourhoods themselves, drop them first.{p_end}

{pstd}What it still lacks beside {help equipop}: {cmd:prefix()}, {cmd:[fweight]} (use {cmd:weight()}), distance decay and projection from degrees. Variable names that would contain a full stop have it replaced by an underscore. Without {cmd:replace}, a result variable that already exists stops the command before any variable is made.{p_end}

{pstd}Requires Stata 17 or later and the equipop Python package in the Python Stata uses: run {cmd:equipop doctor} to check and {cmd:equipop setup} to install.{p_end}

{marker engines}{...}
{title:Engines and their options}

{phang}{cmd:counts} {hline 2} {opt treat(varlist)} {opt k(numlist)} {opt r(numlist)}. Neighbourhood size, reach and the count and share of each treatment, as {help equipop}: N_{it:k}, Dist_{it:k}, T_{it:v}_{it:k}, R_{it:v}_{it:k}.{p_end}

{phang}{cmd:stats} {hline 2} {opt values(varlist)} {opt k(numlist)} {opt r(numlist)} [{opt stats(string)}]. Statistics of numeric variables among the k nearest; {cmd:stats()} lists them (default {cmd:mean median gini}). Nv_ is the number of neighbours with a value. A median or percentile ({cmd:p10}, {cmd:p90}, ...) is the average value of one person's width of the sorted neighbourhood at that position: for whole numbers of people the usual interpolated percentile, and well defined when {cmd:weight()} holds fractions of a person. {cmd:weight()} must hold numbers of people, not shares that sum to one.{p_end}

{phang}{cmd:friction} {hline 2} {opt treat(varname)} {opt k(numlist)} {opt tau(numlist)} [{opt friction(path)}]. Neighbourhoods grown through barriers that cost effort to cross; {cmd:friction()} names a table of cells and their cost.{p_end}

{phang}{cmd:slope} {hline 2} {opt treat(varname)} {opt k(numlist)} {opt tau(numlist)} {opt dem(path)} [{opt model(tobler|linear)} {opt roundtrip}]. As {cmd:friction}, with climbing cost from an elevation raster.{p_end}

{phang}{cmd:fca} {hline 2} {opt demandvar(varname)} {opt supply(path)} [{opt supplycol(name)} {opt supplyx(name)} {opt supplyy(name)} {opt halflife(#)} {opt reach(decay|r|k)} {opt kfca(#)} {opt rfca(#)} {opt method(2sfca|3sfca)}]. Floating catchment accessibility: the observations are the demand, the supply comes from a .csv, .dta or .sav file. Returns {cmd:A} (accessibility) and {cmd:J} (the supply side's ratio). The catchment is ONE of three, each with its own option: {cmd:reach(decay)}, the default, needs {cmd:halflife(#)}, the distance in metres at which a facility counts half; {cmd:reach(r)} needs {cmd:rfca(#)}, a radius in metres; {cmd:reach(k)} needs {cmd:kfca(#)}, how much supply the catchment grows to hold. Only the first uses a half-life.{p_end}

{phang}{cmd:lisa} {hline 2} {opt values(varname)} [{opt k(#)} {opt wperm(#)}]. Local Moran's I on cell means, with the {cmd:k()} nearest cells as neighbours (default 8) and {cmd:wperm()} permutations, a whole number of 1 or more (default 199): LISA_{it:v}_Ii, LISA_{it:v}_quad (1 HH, 2 LL, 3 HL, 4 LH) and LISA_{it:v}_p.{p_end}

{phang}Common to all: {opt unit(#)} is the cell size in metres, any number above zero (default 100); {opt replace} replaces result variables that exist - exactly the ones this run writes, once the new results are ready. Without it the command stops before creating any variable if one of them exists.{p_end}

{phang}For {cmd:counts}, {cmd:stats}, {cmd:friction} and {cmd:slope}: {opt weight(varname)} is the number of people a row stands for; {opt selfpot(#)}, between 0 and 1, how far away an observation's own cell counts (default 1).{p_end}

{phang}{bf:An option the engine does not read is refused}, naming the engines that do read it - for example {cmd:model()} with {cmd:engine(counts)}, {cmd:halflife()} outside {cmd:fca} (only {cmd:fca} has a distance decay here; {help equipop} has one for counts), or {cmd:r()} with {cmd:friction}, which counts by {cmd:k()} and {cmd:tau()}. Until 1.64.0 such an option was accepted and did nothing.{p_end}

{phang}{opt over:shoot(whole|proportional)} and {opt origin:rule(include|exclude)} are {help equipop}'s, with the same meaning and the same defaults (proportional; include), for {cmd:counts}, {cmd:stats}, {cmd:friction} and {cmd:slope}. {cmd:overshoot()} says how much of the ring that crosses {it:k} is taken; {cmd:originrule(exclude)} leaves the observation's own cell out of its neighbourhood. On {cmd:fca} and {cmd:lisa} they are refused.{p_end}

{phang}{opt treatmode(counts|flags)} says what {cmd:treat()} holds, for {cmd:counts}, {cmd:friction} and {cmd:slope}. {cmd:counts}, the default, is the NUMBER OF PEOPLE of the group at the row, as in {help equipop}. {cmd:flags} is 0 or 1, a share of the row's {cmd:weight()}. Without {cmd:weight()} the two are the same. Until 1.63.7 this command applied the flags rule whatever was meant, so {cmd:treat()} with {cmd:weight()} gave other shares than {help equipop} did; results made that way are reproduced with {cmd:treatmode(flags)}.{p_end}

{marker examples}{...}
{title:Examples}

{phang}{cmd:. findfile equipop_test_data.dta}{p_end}
{phang}{cmd:. use "`r(fn)'", clear}{p_end}
{phang}{cmd:. equipop_run, engine(stats) x(X_local) y(Y_local) values(ValFloat) k(200)}{p_end}
{phang}{cmd:. equipop_run, engine(lisa) x(X_local) y(Y_local) values(ValFloat) k(8)}{p_end}

{pstd}Results for some rows only, with the origin left out of its own neighbourhood, and the new variables by name:{p_end}
{phang}{cmd:. equipop_run if HighEdu == 1, engine(stats) x(X_local) y(Y_local) values(ValFloat) k(200) originrule(exclude) replace}{p_end}
{phang}{cmd:. summarize `r(varlist)'}{p_end}

{marker results}{...}
{title:Stored results}

{pstd}{cmd:equipop_run} stores the following in {cmd:r()}:{p_end}

{synoptset 20 tabbed}{...}
{p2col 5 20 24 2: Scalars}{p_end}
{synopt:{cmd:r(N_origins)}}observations in the sample{p_end}
{synopt:{cmd:r(N_missing)}}of those, without a result in the first new variable{p_end}
{synopt:{cmd:r(unit)}}cell size in metres{p_end}
{synopt:{cmd:r(selfpot)}}self-potential used{p_end}
{p2col 5 20 24 2: Macros}{p_end}
{synopt:{cmd:r(cmd)}}{cmd:equipop_run}{p_end}
{synopt:{cmd:r(cmdline)}}the command as typed{p_end}
{synopt:{cmd:r(engine)}}the engine that ran{p_end}
{synopt:{cmd:r(varlist)}}the variables created, in order{p_end}
{synopt:{cmd:r(treat)}}treat() as given{p_end}
{synopt:{cmd:r(values)}}values() as given{p_end}
{synopt:{cmd:r(k)}}k() as given{p_end}
{synopt:{cmd:r(r)}}r() as given{p_end}
{synopt:{cmd:r(tau)}}tau() as given{p_end}
{synopt:{cmd:r(overshoot)}}the overshoot rule that ran (counts, stats, friction, slope){p_end}
{synopt:{cmd:r(originrule)}}the origin rule that ran (the same four engines){p_end}
{p2colreset}{...}

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
