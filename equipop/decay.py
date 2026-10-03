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

# ---------------------------------------------------------------------
# TWO MEANINGS OF "HALF-LIFE"  -  BACKLOG 317
#
# Östh, Lyhagen and Reggiani (2016, EJTIR 16(2): 344-363, Appendix D)
# name both, and old EquiPop implemented the first:
#
#   HALF-LIFE          the median m splits the AREA under the decay
#                      curve in half: half the trips are shorter than
#                      m, half longer. THE PAPER ADVOCATES THIS, and it
#                      is what a survey median commute means.
#   HALF-PROBABILITY   the weight is 0.5 at m: a neighbour at distance
#                      m counts half as much as one next door.
#
# They coincide ONLY for the exponential. EquiPop 1.30 to 1.47 used
# half-probability for every model, silently - a departure from the
# published method that nobody chose and nobody recorded. From 1.48
# half-life is the default again, as John ruled in session 12.
#
# THE AREA IS THE 1-D AREA under the curve on an x/y diagram, exactly
# as in the paper. On a DISC the coincidence moves to the Gaussian;
# that is recorded in BACKLOG 317 and deliberately not offered.
# ---------------------------------------------------------------------

CALIBRATIONS = ("half-life", "half-probability")
DEFAULT_CALIBRATION = "half-life"

#: erfinv(0.5), computed by bisection on math.erf so this module needs
#: no scipy. The paper prints 0.47693628.
_ERFINV_HALF = 0.4769362762044698

#: The exp-sqrt constant: s solves (1 + s) e^(-s) = 0.5 exactly. The
#: paper's 1.67835 is this, correctly rounded.
_EXPSQRT_S = 1.6783469900166603

#: HALF-PROBABILITY: w(m) = 0.5. The formula EquiPop used for every
#: model from 1.30 to 1.47, and the only one power has.
HALF_PROBABILITY_BETA = {
    "negexp":    lambda h: math.log(0.5) / h,
    "expnormal": lambda h: math.log(0.5) / (h * h),
    "expsqrt":   lambda h: math.log(0.5) / math.sqrt(h),
    "lognormal": lambda h: math.log(0.5) / (math.log(h + 1.0) ** 2),
    "power":     lambda h: math.log(0.5) / math.log(h + 1.0),
}


def _lognormal_half_life_beta(m):
    """Half-life beta for w(d) = exp(beta * ln(d+1)^2).

    THE PUBLISHED FORMULA WAS WRONG. Östh, Lyhagen and Reggiani (2016)
    Eq. A16 set erf(z) = 0.5, carrying over the exp-normal's logic. But
    there the integral starts at x = 0, the CENTRE of a half-Gaussian,
    so the area share is erf(z) itself. For the log-normal, u = ln(x)
    sends x = 0 to u = -infinity: the integral starts at the FAR LEFT
    of a full Gaussian and the share is (1 + erf(z))/2. erf = 0.5 is
    therefore the THREE-QUARTER point, and the published +/- roots put
    75% and 25% of the area before m. Verified exactly in session 12;
    both roots reproduce the paper's Table 1 to the last digit.

    For ln(d) the half point has one closed-form root, -1/(2 ln m).
    EquiPop uses ln(d+1) - John's choice, since ln(d) puts the weight
    at ZERO when d = 0 - and with the +1 the log-space integral starts
    at u = 0 instead of -infinity. So it is a TRUNCATED Gaussian and
    the closed form is only approximate: 0.94% out at m = 100 m, 0.07%
    at 6010 m. Solved exactly here instead; with u = ln(d+1),
    a = sqrt(-beta) and U = ln(m+1), the share of area before m is

        [erf(a U - 1/(2a)) + erf(1/(2a))] / [1 + erf(1/(2a))]

    which rises monotonically with a, so bisection is safe.
    """
    U = math.log(m + 1.0)

    def share(a):
        c = 1.0 / (2.0 * a)
        return (math.erf(a * U - c) + math.erf(c)) / (1.0 + math.erf(c))

    lo, hi = 1e-6, 50.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if share(mid) < 0.5:
            lo = mid
        else:
            hi = mid
    a = 0.5 * (lo + hi)
    return -(a * a)


#: HALF-LIFE: the median splits the 1-D area in half. POWER HAS NONE -
#: its area diverges for any beta > -1, so no median exists; the paper
#: says so too, and power keeps half-probability only.
HALF_LIFE_BETA = {
    "negexp":    lambda h: math.log(0.5) / h,
    "expnormal": lambda h: -((_ERFINV_HALF / h) ** 2),
    "expsqrt":   lambda h: -_EXPSQRT_S / math.sqrt(h),
    "lognormal": _lognormal_half_life_beta,
}


@dataclass
class Decay:
    """
    Decay specification passed to run_knn(decay=...).

    Give EITHER beta directly OR half_life_m. half_life_m is usually
    the natural choice for a researcher, and `calibration` says what it
    MEANS:

      "half-life"         (default) half the trips are shorter than
                          half_life_m. Use for a survey median.
      "half-probability"  a neighbour at half_life_m counts half as much.

    The two coincide for negexp. For power only half-probability
    exists, and asking for half-life on power uses half-probability
    and says so. See BACKLOG 317.

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
    calibration: str = DEFAULT_CALIBRATION

    def __post_init__(self):
        if self.model not in MODELS:
            raise ValueError(
                f"Unknown decay model '{self.model}'. "
                f"Available: {list(MODELS)}. "
                f"Add your own to equipop.decay.MODELS."
            )
        cal = str(self.calibration or DEFAULT_CALIBRATION).strip().lower()
        cal = {"hl": "half-life", "halflife": "half-life",
               "life": "half-life", "median": "half-life",
               "hp": "half-probability", "halfprob": "half-probability",
               "probability": "half-probability",
               "value": "half-probability"}.get(cal, cal)
        if cal not in CALIBRATIONS:
            raise ValueError(
                f"calibration must be one of {CALIBRATIONS}, "
                f"got {self.calibration!r}")
        #: What was ASKED for, kept so a forced change is on the record
        self.calibration_requested = cal
        if self.model == "power" and cal == "half-life":
            # POWER HAS NO HALF-LIFE: its area diverges for any
            # beta > -1, so no median exists. John, session 12: "the
            # power model will of course stay (but only as
            # half-probability)". Used, not refused - the default is
            # half-life, and refusing would break every power run
            # that did not think to change it.
            cal = "half-probability"
            if self.half_life_m is not None and self.beta is None:
                print("[decay] power has no half-life - its area never "
                      "converges, so no median exists. Using "
                      "HALF-PROBABILITY: the weight is 0.5 at "
                      f"{self.half_life_m:g} m.")
        self.calibration = cal
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
            table = (HALF_LIFE_BETA if self.calibration == "half-life"
                     else HALF_PROBABILITY_BETA)
            self.beta = table[self.model](self.half_life_m)
        if self.beta > 0:
            print("[decay] WARNING: beta is positive - weights will GROW "
                  "with distance. For decay, beta should be negative "
                  "(ln(0.5)/half_life).")

    def weight(self, dist_m: float) -> float:
        if self.model == "power" and self.gamma is not None:
            return (1.0 + self._pw_scale * dist_m) ** (-self.gamma)
        """Weight for a neighbour at dist_m metres from the origin."""
        return MODELS[self.model](dist_m, self.beta)

    def fingerprint(self) -> dict:
        """Everything that decides a weight, normalised for comparison.

        BACKLOG 344, external review of 1.51 (F3). A resumable run
        recorded model, half_life_m and gamma - and NOT `calibration`,
        which is the setting that turns a half-life into a beta. Two
        runs at the same half-life under the two calibrations have
        different betas and different answers, and resume called them
        the same run. `beta` goes in because it is what the weight
        function actually uses, whichever route produced it, and
        because a caller may give it directly; `_pw_scale` goes in
        because for power+gamma it, not beta, carries the half-life.
        """
        fp = {"model": self.model,
              "beta": None if self.beta is None else float(self.beta),
              "half_life_m": (None if self.half_life_m is None
                              else float(self.half_life_m)),
              "gamma": None if self.gamma is None else float(self.gamma),
              "calibration": self.calibration,
              "calibration_requested": getattr(
                  self, "calibration_requested", self.calibration)}
        scale = getattr(self, "_pw_scale", None)
        if scale is not None:
            fp["pw_scale"] = float(scale)
        return fp

    def describe(self) -> str:
        hl = (f", {self.calibration} {self.half_life_m:g} m"
              if self.half_life_m else "")
        return f"{self.model} (beta = {self.beta:.6g}{hl})"

    def both_betas(self):
        """(half-life beta, half-probability beta) for this model and
        distance - the half-life one is None for power, which has none.

        BACKLOG 317: every run reports BOTH, so the difference between
        the two readings is visible even to a user who kept the
        default and never saw the choice.
        """
        if self.half_life_m is None:
            return None, None
        h = float(self.half_life_m)
        hl = (HALF_LIFE_BETA[self.model](h)
              if self.model in HALF_LIFE_BETA else None)
        return hl, HALF_PROBABILITY_BETA[self.model](h)


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
