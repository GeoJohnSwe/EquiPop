"""
decay.py - distance decay models.

Design goal: EASY TO EXTEND. All decay models live in the MODELS
dictionary below. To add your own model later, you only need one line:

    MODELS["power"] = lambda dist_m, beta: (dist_m + 1) ** beta

and it becomes available as Decay(model="power", beta=...).

Sign convention (important!)
----------------------------
We follow the half-life formulation from the EquiPop papers:

    beta = ln(0.5) / half_life_m          (beta is NEGATIVE)
    weight(dist) = exp(dist * beta)

so that weight(0) = 1, weight(half_life) = 0.5, weight(2*half_life) = 0.25.
Example: half_life_m = 8000  ->  beta = -0.0000866...
"""

import math
from dataclasses import dataclass


# --- all available decay models: name -> f(dist_m, beta) -> weight -------
# The five models of the original EquiPop (Östh, Lyhagen & Reggiani 2016).
# All are parameterised so that beta can be derived from a HALF-LIFE
# distance (weight = 0.5 at half_life_m); see HALF_LIFE_BETA below.
MODELS = {
    "negexp":    lambda d, b: math.exp(d * b),                    # exp(b*d)
    "expnormal": lambda d, b: math.exp(d * d * b),                # exp(b*d^2)
    "expsqrt":   lambda d, b: math.exp(math.sqrt(d) * b),         # exp(b*sqrt(d))
    "lognormal": lambda d, b: math.exp(math.log(d + 1.0) ** 2 * b),
    "power":     lambda d, b: (d + 1.0) ** b,
}

# beta = f(half_life_m) such that weight(half_life) = 0.5 for each model
HALF_LIFE_BETA = {
    "negexp":    lambda h: math.log(0.5) / h,
    "expnormal": lambda h: math.log(0.5) / (h * h),
    "expsqrt":   lambda h: math.log(0.5) / math.sqrt(h),
    "lognormal": lambda h: math.log(0.5) / (math.log(h + 1.0) ** 2),
    "power":     lambda h: math.log(0.5) / math.log(h + 1.0),
}


@dataclass
class Decay:
    """
    Decay specification passed to run_knn(decay=...).

    Give EITHER beta directly OR half_life_m (the distance at which
    the weight should be 0.5); half_life_m is usually the natural
    choice for a researcher.

    Examples
    --------
    Decay(half_life_m=8000)                    # negexp, p=0.5 at 8 km
    Decay(model="power", half_life_m=2000, gamma=1.0)   # 1/(1+d/h)
    Decay(model="negexp", beta=-0.0000866)     # same thing, explicit beta
    """
    model: str = "negexp"
    beta: float | None = None
    half_life_m: float | None = None
    gamma: float | None = None

    def __post_init__(self):
        if self.model not in MODELS:
            raise ValueError(
                f"Unknown decay model '{self.model}'. "
                f"Available: {list(MODELS)}. "
                f"Add your own to equipop.decay.MODELS."
            )
        if self.beta is None:
            if self.half_life_m is None:
                raise ValueError("Give either beta or half_life_m.")
            if self.model == "power" and self.gamma is not None:
                # gamma-parameterised SHIFTED power (v1.4.0):
                #   w(d) = (1 + (2**(1/gamma)-1) * d/h) ** (-gamma)
                # EXACT half-life at h for ANY tail exponent gamma;
                # gamma=1 is w = 1/(1+d/h). The legacy +1m form
                # (gamma=None) is kept reproducible.
                self.beta = -float(self.gamma)   # stored for the record
                self._pw_scale = (2.0 ** (1.0 / self.gamma) - 1.0) \
                    / self.half_life_m
                print(f"[decay] power, gamma = {self.gamma:g}, exact "
                      f"half-life {self.half_life_m:g} m (shifted form)")
                return
            self.beta = HALF_LIFE_BETA[self.model](self.half_life_m)
        if self.beta > 0:
            print("[decay] WARNING: beta is positive - weights will GROW "
                  "with distance. For decay, beta should be negative "
                  "(ln(0.5)/half_life).")

    def weight(self, dist_m: float) -> float:
        if self.model == "power" and self.gamma is not None:
            return (1.0 + self._pw_scale * dist_m) ** (-self.gamma)
        """Weight for a neighbour at dist_m metres from the origin."""
        return MODELS[self.model](dist_m, self.beta)

    def describe(self) -> str:
        hl = f", half-life {self.half_life_m} m" if self.half_life_m else ""
        return f"{self.model} (beta = {self.beta:.6g}{hl})"


# ---- vectorised weights + truncation radius (for unbounded decayed sums)
import numpy as _np

_MODELS_VEC = {
    "negexp":    lambda d, b: _np.exp(d * b),
    "expnormal": lambda d, b: _np.exp(d * d * b),
    "expsqrt":   lambda d, b: _np.exp(_np.sqrt(d) * b),
    "lognormal": lambda d, b: _np.exp(_np.log(d + 1.0) ** 2 * b),
    "power":     lambda d, b: (d + 1.0) ** b,
}


def _weight_vec(self, dist_m):
    """Vectorised weight for an array of distances (same maths as
    weight(); used by the decayed-sum mode)."""
    d = _np.asarray(dist_m, dtype=float)
    if self.model == "power" and self.gamma is not None:
        return (1.0 + self._pw_scale * d) ** (-self.gamma)
    return _MODELS_VEC[self.model](d, self.beta)


def _truncation_radius(self, eps: float = 1e-6) -> float:
    """Distance beyond which weight < eps (bisection; every model is
    monotone decreasing for negative beta). The unbounded decayed sum
    is truncated here - the neglected tail mass is below eps per unit."""
    lo, hi = 0.0, 1.0
    while self.weight(hi) >= eps and hi < 1e12:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if self.weight(mid) >= eps:
            lo = mid
        else:
            hi = mid
    return hi


Decay.weight_vec = _weight_vec
Decay.truncation_radius = _truncation_radius
