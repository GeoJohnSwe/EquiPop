

def test_a_decay_run_does_not_fetch_neighbours_it_will_never_read():
    """BACKLOG 307, found by John. A decayed run's TIME should not
    depend on the half-life: since BACKLOG 185 removed the unbounded
    sums in v1.40, the decayed totals are accumulated to THE RAW k,
    exactly like the plain ones, so nothing reads past k.

    auto_m_neighbors still sized the fetch window from the decay
    TRUNCATION RADIUS, on a comment that had been true until 1.40.
    On LA County at half-life 2000 m and eps 1e-3 that is a 20 km
    disc: 11,159 cells fetched where 697 satisfied k=800, and 138
    seconds against 14 - all of it reading neighbours nobody would
    look at.

    The deferral test in fastcounts was corrected when 185 landed.
    THIS WAS NOT, and nothing compared the two.
    """
    import numpy as np

    from equipop.cells import CellData, auto_m_neighbors
    from equipop.decay import Decay

    rng = np.random.default_rng(4)
    n = 4000
    E = rng.uniform(0, 20000, n)
    N = rng.uniform(0, 20000, n)
    pop = rng.integers(20, 200, n).astype(float)
    cd = CellData(E=E, N=N, n=pop, binary_sums={}, unit_size=100.0)

    short = Decay("negexp", half_life_m=200.0).truncation_radius(1e-3)
    long = Decay("negexp", half_life_m=4000.0).truncation_radius(1e-3)
    assert long > short * 10, "the fixture must span real half-lives"

    m_short = auto_m_neighbors(cd, [800], None, trunc_m=short)
    m_long = auto_m_neighbors(cd, [800], None, trunc_m=long)
    assert m_short == m_long, (
        f"the window grew from {m_short} to {m_long} cells because the "
        "half-life grew - it is sized for a distance the run will "
        "never read")


def test_the_decayed_total_is_measured_at_the_raw_threshold():
    """John's model, and the one BACKLOG 185 settled: the
    neighbourhood is fixed by PLAIN k - reach 800 actual people - and
    only the sums inside it are weighted. N_k must stay exactly k;
    ND_k is the decayed sum over those same people and can never
    exceed it."""
    import numpy as np

    from equipop.cells import CellData
    from equipop.decay import Decay
    from equipop.fastcounts import run_knn_counts

    rng = np.random.default_rng(9)
    n = 1500
    E = rng.uniform(0, 8000, n)
    N = rng.uniform(0, 8000, n)
    pop = rng.integers(20, 200, n).astype(float)
    grp = np.minimum(pop, rng.integers(0, 120, n).astype(float))
    cd = CellData(E=E, N=N, n=pop, binary_sums={"g": grp},
                  unit_size=100.0)
    d = run_knn_counts(cd, k_values=[400], report=False,
                       decay=Decay("negexp", half_life_m=300.0),
                       decay_eps=1e-3)
    assert np.allclose(d["N_400"].values, 400.0), (
        "the k threshold must be RAW - decay weights what is inside "
        "the neighbourhood, it does not redefine it")
    assert (d["ND_400"].values <= d["N_400"].values + 1e-6).all()
    assert (d["TD_g_400"].values <= d["T_g_400"].values + 1e-6).all()
