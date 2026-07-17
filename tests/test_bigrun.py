"""#18a bigrun: tiled == untiled EXACTLY, resume, integrity."""
import json
import os

import numpy as np
import pandas as pd

from equipop.cells import CellData
from equipop.decay import Decay
from equipop.fastcounts import run_knn_counts
from equipop.bigrun import run_knn_counts_tiled, load_tiled


def _cd(n=3000, seed=13):
    rng = np.random.default_rng(seed)
    E = rng.integers(0, 200, n) * 100.0 + 50
    N = rng.integers(0, 200, n) * 100.0 + 50
    pop = rng.integers(1, 7, n)
    g = pd.DataFrame({"E": E, "N": N, "n": pop.astype(float),
                      "t": rng.binomial(pop, 0.3).astype(float)}
                     ).groupby(["E", "N"], as_index=False).sum()
    return CellData(E=g.E.to_numpy(), N=g.N.to_numpy(),
                    n=g.n.to_numpy(), binary_sums={"t": g.t.to_numpy()},
                    value_arrays={}, unit_size=100.0)


def test_origins_subset_exact():
    cd = _cd(800, seed=2)
    full = run_knn_counts(cd, [40], r_values=[700.0])
    idx = np.array([3, 77, 200, 411])
    sub = run_knn_counts(cd, [40], r_values=[700.0], origins=idx)
    for c in ["N_40", "R_t_40", "N_r700", "Dist_40"]:
        assert np.allclose(sub[c].to_numpy(), full[c].to_numpy()[idx])


def test_tiled_equals_untiled_exactly(tmp_path):
    """THE golden validation: same numbers, different packaging."""
    cd = _cd()
    dec = Decay(model="negexp", half_life_m=1500.0)
    out = str(tmp_path / "run")
    run_knn_counts_tiled(cd, k_values=[50, 400], r_values=[900.0],
                         decay=dec, out_dir=out, tile_m=5000.0)
    tiled = (load_tiled(out)
             .sort_values(["EastWest", "NorthSouth"])
             .reset_index(drop=True))
    ref = (run_knn_counts(cd, [50, 400], r_values=[900.0], decay=dec)
           .sort_values(["EastWest", "NorthSouth"])
           .reset_index(drop=True))
    assert len(tiled) == len(ref)
    for c in ["N_50", "N_400", "T_t_400", "R_t_400", "Dist_400",
              "N_r900", "ND_inf", "RD_t_inf"]:
        assert np.allclose(tiled[c].to_numpy(dtype=float),
                           ref[c].to_numpy(dtype=float),
                           rtol=2e-7), c        # float32 packaging


def test_resume_skips_done_and_repairs_missing(tmp_path):
    cd = _cd(1200, seed=5)
    out = str(tmp_path / "run")
    man1 = run_knn_counts_tiled(cd, k_values=[30], out_dir=out,
                                tile_m=6000.0)
    victim = sorted(man1["tiles"])[0]
    os.remove(os.path.join(out, victim))
    man = json.load(open(os.path.join(out, "manifest.json")))
    del man["tiles"][victim]
    json.dump(man, open(os.path.join(out, "manifest.json"), "w"))
    man2 = run_knn_counts_tiled(cd, k_values=[30], out_dir=out,
                                tile_m=6000.0, resume=True)
    assert set(man2["tiles"]) == set(man1["tiles"])
    df = load_tiled(out)                     # md5-verified
    ref = run_knn_counts(cd, [30])
    assert len(df) == len(ref)
    a = df.sort_values(["EastWest", "NorthSouth"]).N_30.to_numpy(float)
    b = ref.sort_values(["EastWest", "NorthSouth"]).N_30.to_numpy(float)
    assert np.allclose(a, b)
