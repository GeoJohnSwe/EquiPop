* ============================================================
* equipop_example.do - EquiPop from Stata, the full round trip
* in one do-file
* ------------------------------------------------------------
* The name carries the equipop_ prefix because SSC's filename
* space is flat and global: C. F. Baum renamed this file from
* example.do on the archive, rightly, and the repository follows
* so that one file has one name everywhere. Same for the data,
* which was stata_test_data.dta and is now equipop_test_data.dta.
* Variables in the test data: ID, X_local, Y_local (metric
* coordinates), LowEdu, HighEdu, TheoEdu, VocaEdu (binary),
* ValFloat (continuous), ValCount (count).
* ============================================================

* --- one-time setup (uncomment and adapt on first use) -------
* python query                          // which Python does Stata see?
* python set exec "C:\Users\you\anaconda3\envs\equipop\python.exe", perm
* shell pip install equipop             // into THAT python

* --- make the command visible this session -------------------
* (not needed after `ssc install equipop` - the command is already
*  on the ado-path then. Harmless either way.)
adopath + "`c(pwd)'"

* --- load data and compute k-NN context variables ------------
* findfile searches the ado-path, so this line works whether you
* installed from SSC - where the data sits in Stata's PLUS folder and
* not in your working directory - or are sitting in the repository's
* stata/ folder. BACKLOG 330: `use equipop_test_data` alone only
* worked in the second case, which is not how most people arrive.
findfile equipop_test_data.dta
use "`r(fn)'", clear
equipop, x(X_local) y(Y_local) treat(HighEdu) ///
             k(50 200 800) unit(100) replace

* --- results are ordinary Stata variables: analyse away ------
summarize R_HighEdu_*
regress ValFloat R_HighEdu_200 ValCount
* ...change something, rerun equipop with replace, regress again:
* the promised back-and-forth between Stata and EquiPop.
