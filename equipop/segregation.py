"""
segregation.py - aggregate segregation indices from k-NN output
(backlog item 6; formulas per the US Census formulary and
Östh, Clark & Malmberg 2015, Geographical Analysis 47:34-49).

POST-ANALYSIS design: the functions consume a run_knn/run_knn_stats
output DataFrame - one row per origin i with per-k population counts
N_k and treatment counts T_k (or ratios R_k) - and return ONE ROW PER
SCALE with the index values. No engine involvement.

Unit convention: at scale k, each origin's bespoke neighbourhood is
treated as the unit, with t_i = N_k(i) (total), x_i = T_k(i)
(minority), p_i = R_k(i). The row labelled 'local' uses the origin
cells themselves (CountAllLocal / CountGroupLocal) - the aspatial
baseline. P is the global minority share (constant across scales).

Indices (evenness): Dissimilarity D, Gini (segregation form),
Entropy/Theil H, Atkinson(b).
Indices (exposure): Isolation xPx, Interaction xPy, Correlation ratio
V = (I-P)/(1-P), and SI - the population-weighted k-share isolation of
the 2015 paper: SI_k = sum_i(x_i,local * p_ik) / sum_i(x_i,local).
Concentration/delta family is NOT included: it requires an areal term
whose bespoke-neighbourhood definition is a methodological choice
still to be made (see backlog).
"""

import numpy as np
import pandas as pd


def _weighted_gini_of_p(p, t, P):
    """Segregation Gini: sum_ij t_i t_j |p_i - p_j| / (2 T^2 P(1-P)),
    computed in O(n log n) via sorting."""
    order = np.argsort(p)
    p, t = p[order], t[order]
    T = t.sum()
    cw = np.cumsum(t) - t                 # weight strictly below i
    cwp = np.cumsum(t * p) - t * p        # weighted p strictly below i
    total = 2.0 * np.sum(t * (p * cw - cwp))
    return total / (2.0 * T * T * P * (1 - P))


def seg_indices_at_scale(t, x, P, atkinson_b=0.5):
    """All indices for one scale. t = unit totals, x = unit minority."""
    t = np.asarray(t, float); x = np.asarray(x, float)
    ok = t > 0
    t, x = t[ok], x[ok]
    T, X = t.sum(), x.sum()
    p = x / t
    D = np.sum(t * np.abs(p - P)) / (2 * T * P * (1 - P))
    gini = _weighted_gini_of_p(p, t, P)
    # entropy index H (Theil): E - E_i weighted
    def _e(q):
        q = np.clip(q, 1e-12, 1 - 1e-12)
        return q * np.log(1 / q) + (1 - q) * np.log(1 / (1 - q))
    E = _e(P)
    H = np.sum(t * (E - _e(p))) / (E * T)
    b = atkinson_b
    inner = np.sum((1 - p) ** (1 - b) * p ** b * t) / (P * T)
    atk = 1 - (P / (1 - P)) * np.abs(inner) ** (1 / (1 - b))
    isolation = np.sum((x / X) * p)                    # xPx
    interaction = np.sum((x / X) * ((t - x) / t))      # xPy (majority)
    V = (isolation - P) / (1 - P)
    return {"D": D, "Gini": gini, "H": H, f"Atkinson_{b}": atk,
            "Isolation": isolation, "Interaction": interaction,
            "CorrelationV": V}


def seg_profile(knn_out: pd.DataFrame, k_values: list[int],
                atkinson_b: float = 0.5,
                n_col: str = "N_{k}", t_col: str = "T_{k}",
                local_all: str = "CountAllLocal",
                local_grp: str = "CountGroupLocal") -> pd.DataFrame:
    """
    Segregation profile across scales: one row per k (plus 'local').

    Adds SI (Östh-Clark-Malmberg 2015): the average k-share experienced
    by a minority member, weighting each origin's p_ik by the origin's
    own LOCAL minority count.
    """
    la = knn_out[local_all].to_numpy(float)
    lg = knn_out[local_grp].to_numpy(float)
    P = lg.sum() / la.sum()
    rows = []

    r = seg_indices_at_scale(la, lg, P, atkinson_b)
    ok = la > 0
    r["SI"] = np.sum(lg[ok] * (lg[ok] / la[ok])) / lg.sum()
    rows.append({"scale": "local", **r})

    for k in k_values:
        t = knn_out[n_col.format(k=k)].to_numpy(float)
        x = knn_out[t_col.format(k=k)].to_numpy(float)
        r = seg_indices_at_scale(t, x, P, atkinson_b)
        p_ik = np.divide(x, t, out=np.zeros_like(x), where=t > 0)
        r["SI"] = np.sum(lg * p_ik) / lg.sum()
        rows.append({"scale": k, **r})

    out = pd.DataFrame(rows)
    out.attrs["global_share_P"] = P
    print(f"[segregation] profile over {len(k_values)} scales + local "
          f"(P = {P:.4f})")
    return out
