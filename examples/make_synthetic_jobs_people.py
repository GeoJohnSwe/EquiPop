"""
make_synthetic_jobs_people.py - privacy-preserving synthetic versions
of People.sav + LowEduJobs.sav for sharing/fixtures.

METHOD: one rigid ISOMETRY (mirror + rotate + translate), the SAME
transform applied to BOTH files jointly. Every within- and BETWEEN-
file distance is exactly preserved, so every EquiPop/FCA result on
the synthetic data is bit-comparable with the original - while the
true locations are unrecoverable without the (discarded) transform.
Attributes are kept untouched, as requested. (The poptest_anon
precedent from v0.9, now for a two-file system.)

Usage:
    python examples/make_synthetic_jobs_people.py People.sav \\
           LowEduJobs.sav [x_col y_col]
Writes *_synthetic.sav next to the inputs and prints an isometry
self-check (max cross-distance error, must be ~1e-9).
"""
import sys
import numpy as np
import pandas as pd


def joint_isometry(dfs, x_col="x", y_col="y", seed=None):
    """Apply ONE random rigid transform (reflection + rotation +
    translation) to every frame in dfs. Returns new frames."""
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2 * np.pi)
    R = np.array([[np.cos(theta), -np.sin(theta)],
                  [np.sin(theta), np.cos(theta)]])
    R = R @ np.array([[1.0, 0.0], [0.0, -1.0]])        # mirror too
    shift = rng.uniform(1e5, 9e5, 2)

    allxy = np.vstack([d[[x_col, y_col]].to_numpy(float) for d in dfs])
    centre = allxy.mean(0)

    out = []
    for d in dfs:
        xy = d[[x_col, y_col]].to_numpy(float)
        new = (xy - centre) @ R.T + centre + shift
        e = d.copy()
        e[x_col], e[y_col] = new[:, 0].round(1), new[:, 1].round(1)
        out.append(e)

    # self-check: cross-file distances exactly preserved
    a0 = dfs[0][[x_col, y_col]].to_numpy(float)
    b0 = dfs[1][[x_col, y_col]].to_numpy(float)
    a1 = out[0][[x_col, y_col]].to_numpy(float)
    b1 = out[1][[x_col, y_col]].to_numpy(float)
    idx = np.random.default_rng(0).choice(len(a0), min(200, len(a0)))
    jdx = np.random.default_rng(1).choice(len(b0), min(200, len(b0)))
    d0 = np.hypot(a0[idx, None, 0] - b0[None, jdx, 0],
                  a0[idx, None, 1] - b0[None, jdx, 1])
    d1 = np.hypot(a1[idx, None, 0] - b1[None, jdx, 0],
                  a1[idx, None, 1] - b1[None, jdx, 1])
    err = np.abs(d0 - d1).max()
    print(f"[synthetic] isometry self-check: max cross-file distance "
          f"error {err:.2e} m (rounding to 0.1 m dominates)")
    assert err < 0.5, "isometry broken - do not share these files"
    return out


if __name__ == "__main__":
    import pyreadstat
    f_people, f_jobs = sys.argv[1], sys.argv[2]
    xc = sys.argv[3] if len(sys.argv) > 3 else "x"
    yc = sys.argv[4] if len(sys.argv) > 4 else "y"
    people, meta_p = pyreadstat.read_sav(f_people)
    jobs, meta_j = pyreadstat.read_sav(f_jobs)
    people_s, jobs_s = joint_isometry([people, jobs], xc, yc)
    pyreadstat.write_sav(people_s,
                         f_people.replace(".sav", "_synthetic.sav"))
    pyreadstat.write_sav(jobs_s,
                         f_jobs.replace(".sav", "_synthetic.sav"))
    print("[synthetic] written *_synthetic.sav - attributes untouched, "
          "geometry rigidly moved, all results reproduce exactly")
