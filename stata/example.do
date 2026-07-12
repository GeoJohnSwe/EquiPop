* ============================================================
* EquiPop from Stata - the full round trip in one do-file
* Variables in the test data: ID, X_local, Y_local (metric
* coordinates), LowEdu, HighEdu, TheoEdu, VocaEdu (binary),
* ValFloat (continuous), ValCount (count).
* ============================================================

* --- one-time setup (uncomment and adapt on first use) -------
* python query                          // which Python does Stata see?
* python set exec "C:\Users\you\anaconda3\envs\equipop\python.exe", perm
* shell pip install equipop             // into THAT python

* --- make the command visible this session -------------------
adopath + "`c(pwd)'"

* --- load data and compute k-NN context variables ------------
use stata_test_data, clear
equipop_knn, x(X_local) y(Y_local) treat(HighEdu) ///
             k(50 200 800) unit(100) replace

* --- results are ordinary Stata variables: analyse away ------
summarize R_HighEdu_*
regress ValFloat R_HighEdu_200 ValCount
* ...change something, rerun equipop_knn with replace, regress again:
* the promised back-and-forth between Stata and EquiPop.
