from __future__ import annotations

"""Simple viscosity helpers for temperature and mixture effects.

Notes
- Keeps deterministic, closed-form correlations with conservative accuracy.
- Provide explicit measured viscosities for specialty systems (e.g., chitosan) when possible
  and use `relative_viscosity` to adjust flux.
"""

import math


def water_viscosity_mPa_s(T_C: float) -> float:
    """Return dynamic viscosity of pure water [mPa·s] at temperature T_C.

    Correlation (valid ~0–100 °C):
        mu [Pa·s] = 2.414e-5 × 10^(247.8 / (T_K - 140))
    where T_K = T_C + 273.15. Returns in mPa·s.
    """
    T_K = float(T_C) + 273.15
    mu_Pa_s = 2.414e-5 * (10.0 ** (247.8 / (T_K - 140.0)))
    return max(mu_Pa_s * 1_000.0, 0.0)


def relative_viscosity(mu_solution_mPa_s: float, mu_reference_mPa_s: float) -> float:
    """Compute relative viscosity (dimensionless), clamped to [1, 1e6]."""
    try:
        mu_s = float(mu_solution_mPa_s)
        mu_r = float(mu_reference_mPa_s)
    except (TypeError, ValueError):
        return 1.0
    if mu_s <= 0.0 or mu_r <= 0.0:
        return 1.0
    ratio = mu_s / mu_r
    return min(max(ratio, 1.0), 1e6)


def apply_viscosity_flux_derate(flux_lmh: float, rel_viscosity: float, min_fraction: float = 0.2) -> float:
    """Derate flux inversely with viscosity; clamp to a minimum fraction of original.

    - flux' = max(flux / rel_viscosity, min_fraction * flux)
    - Use for glycerol/chitosan solutions when measured viscosity is available.
    """
    try:
        flux = float(flux_lmh)
        rv = float(rel_viscosity)
        min_f = float(min_fraction)
    except (TypeError, ValueError):
        return float(flux_lmh)
    if flux <= 0.0:
        return 0.0
    if rv <= 0.0:
        return flux
    return max(flux / rv, min_f * flux)


def glycerol_solution_viscosity_mPa_s(wt_frac: float, T_C: float) -> float:
    """Approximate viscosity of glycerol-water mixtures [mPa·s].

    Uses an Arrhenius-type mixing rule with rough constants that match order-of-magnitude trends:
        ln(mu_mix) ≈ x_gly ln(mu_gly(T)) + (1 - x_gly) ln(mu_water(T))
    where mu_gly(T) ≈ 10^(A + B/(T_K - C)) Pa·s (coarse fit), converted to mPa·s.
    This is intentionally conservative and not for design-critical estimates.
    """
    x = max(min(float(wt_frac), 1.0), 0.0)
    T_K = float(T_C) + 273.15

    # Coarse glycerol correlation: at 20 °C ~ 1.5 Pa·s; at 40 °C ~ 0.3 Pa·s
    A, B, C = -3.7188, 578.919, 137.546  # returns mu in Pa·s (coarse)
    mu_gly_Pa_s = 10.0 ** (A + B / (T_K - C))
    mu_gly = max(mu_gly_Pa_s * 1_000.0, 1.0)  # mPa·s
    mu_w = water_viscosity_mPa_s(T_C)

    ln_mu = x * math.log(mu_gly) + (1.0 - x) * math.log(max(mu_w, 1e-6))
    return max(math.exp(ln_mu), mu_w)

