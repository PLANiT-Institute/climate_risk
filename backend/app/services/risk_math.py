"""Centralized financial and statistical math functions.

References:
- Brealey, Myers & Allen, "Principles of Corporate Finance"
- NGFS Technical Documentation (2023), scenario-conditional WACC adjustments
- Coles (2001), "An Introduction to Statistical Modeling of Extreme Values"
- Bass (1969), "A New Product Growth for Model Consumer Durables", Management Science
"""

import math
from typing import Dict, List, Sequence, Tuple


# ── Net Present Value ────────────────────────────────────────────────
def npv(
    cash_flows: Dict[int, float],
    rate: float,
    base_year: int,
) -> float:
    """Year-explicit NPV: discount each (year, cashflow) pair back to base_year.

    Args:
        cash_flows: {year: amount} mapping.
        rate: annual discount rate (e.g. 0.08 for 8%).
        base_year: reference year for discounting.

    Returns:
        Sum of discounted cash flows.

    Reference: Brealey, Myers & Allen, Ch. 2-3.
    """
    total = 0.0
    for year, cf in cash_flows.items():
        t = year - base_year
        if t < 0:
            continue
        total += cf / ((1 + rate) ** t)
    return total


def npv_from_list(
    cash_flows: List[float],
    rate: float,
) -> float:
    """Simple list-based NPV (periods 1, 2, ..., N).

    Reference: Standard DCF, Brealey, Myers & Allen.
    """
    return sum(cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows))


# ── WACC Scenario Adjustment ────────────────────────────────────────
# Climate scenarios increase cost of capital through physical risk premia
# and transition policy uncertainty premia.
# Spread values are model assumptions calibrated to:
# - Bolton & Kacperczyk (2021), J. Financial Economics: ~60bp carbon premium
# - NGFS (2023), Technical Documentation v4, Section 4.3: qualitative
#   risk-premium discussion (no published exact bp values).
# - Battiston et al. (2017), Nature Climate Change: equity risk-premium
#   differentials (used for directional ordering).
# Note: Exact spread values are NOT directly from NGFS published tables.
_SCENARIO_WACC_SPREADS: Dict[str, float] = {
    "net_zero_2050": 0.005,       # +50bp - orderly transition, lowest uncertainty
    "below_2c": 0.0075,           # +75bp
    "delayed_transition": 0.015,  # +150bp - policy uncertainty premium
    "current_policies": 0.020,    # +200bp - highest physical risk premium
}

# High-carbon sectors face additional spread under transition scenarios
_SECTOR_TRANSITION_SPREAD: Dict[str, float] = {
    "oil_gas": 0.015,
    "utilities": 0.012,
    "steel": 0.010,
    "cement": 0.008,
    "petrochemical": 0.008,
    "shipping": 0.006,
    "automotive": 0.004,
    "electronics": 0.002,
    "real_estate": 0.003,
    "financial": 0.001,
}


def wacc_scenario_adjusted(
    base_wacc: float,
    scenario_id: str,
    sector: str = "financial",
) -> float:
    """Adjust WACC for climate scenario risk premia.

    Args:
        base_wacc: baseline WACC (e.g. 0.08).
        scenario_id: NGFS scenario identifier.
        sector: industry sector for transition-specific spread.

    Returns:
        Adjusted WACC.

    Reference: Bolton & Kacperczyk (2021); NGFS Technical Documentation (2023);
    Battiston et al. (2017). See _SCENARIO_WACC_SPREADS for detailed sourcing.
    """
    scenario_spread = _SCENARIO_WACC_SPREADS.get(scenario_id, 0.01)
    sector_spread = _SECTOR_TRANSITION_SPREAD.get(sector, 0.005)

    # Transition spread scales inversely with scenario ambition for high-carbon
    # (net_zero forces transition cost but reduces long-term uncertainty)
    if scenario_id in ("net_zero_2050", "below_2c"):
        adjusted_sector_spread = sector_spread * 0.5
    else:
        adjusted_sector_spread = sector_spread

    return base_wacc + scenario_spread + adjusted_sector_spread


# ── Piecewise Linear Interpolation ──────────────────────────────────
def piecewise_linear_interpolate(
    knots: Dict[int, float],
    target: int,
) -> float:
    """Multi-point piecewise linear interpolation.

    Args:
        knots: {x: y} sorted control points.
        target: x-value to interpolate at.

    Returns:
        Interpolated y-value; extrapolates linearly beyond endpoints.
    """
    sorted_knots: List[Tuple[int, float]] = sorted(knots.items())
    if not sorted_knots:
        raise ValueError("Empty knots dictionary")

    # Below first knot: extrapolate from first two points (or constant)
    if target <= sorted_knots[0][0]:
        if len(sorted_knots) == 1:
            return sorted_knots[0][1]
        x0, y0 = sorted_knots[0]
        x1, y1 = sorted_knots[1]
        if x0 == x1:
            return y0
        return y0 + (y1 - y0) * (target - x0) / (x1 - x0)

    # Above last knot: extrapolate from last two points
    if target >= sorted_knots[-1][0]:
        if len(sorted_knots) == 1:
            return sorted_knots[-1][1]
        x0, y0 = sorted_knots[-2]
        x1, y1 = sorted_knots[-1]
        if x0 == x1:
            return y1
        return y0 + (y1 - y0) * (target - x0) / (x1 - x0)

    # Find bracketing interval
    for i in range(len(sorted_knots) - 1):
        x0, y0 = sorted_knots[i]
        x1, y1 = sorted_knots[i + 1]
        if x0 <= target <= x1:
            if x0 == x1:
                return y0
            return y0 + (y1 - y0) * (target - x0) / (x1 - x0)

    return sorted_knots[-1][1]  # fallback


# ── Extreme Value Distribution ──────────────────────────────────────
def gumbel_return_period(
    location: float,
    scale: float,
    return_period: float,
) -> float:
    """Gumbel Type I (maxima) quantile for a given return period.

    Args:
        location (mu): location parameter.
        scale (sigma): scale parameter (> 0).
        return_period (T): return period in years (e.g. 100).

    Returns:
        Quantile value (e.g. rainfall in mm for T-year event).

    Reference: Coles (2001), "An Introduction to Statistical Modeling of
    Extreme Values", Ch. 3.
    """
    if scale <= 0:
        raise ValueError("Gumbel scale parameter must be positive")
    if return_period <= 1:
        raise ValueError("Return period must be > 1")
    # Quantile: x_T = mu - sigma * ln(-ln(1 - 1/T))
    p = 1.0 - 1.0 / return_period
    return location - scale * math.log(-math.log(p))


def exceedance_probability(
    return_period: float,
    horizon: int,
) -> float:
    """Probability of at least one exceedance within horizon years.

    P = 1 - (1 - 1/T)^n

    Args:
        return_period: T-year event.
        horizon: number of years.

    Returns:
        Exceedance probability [0, 1].

    Reference: Standard actuarial/insurance mathematics.
    """
    if return_period <= 0:
        return 1.0
    annual_prob = 1.0 / return_period
    return 1.0 - (1.0 - annual_prob) ** horizon


# ── Logistic S-Curve ────────────────────────────────────────────────
def logistic_s_curve(
    t: float,
    L: float,
    k: float,
    t0: float,
) -> float:
    """Logistic (sigmoidal) function for technology adoption / emission reduction.

    f(t) = L / (1 + exp(-k * (t - t0)))

    Args:
        t: time (e.g. year).
        L: supremum (maximum value, e.g. max reduction fraction).
        k: steepness (higher = faster transition).
        t0: midpoint (year of 50% adoption).

    Returns:
        Value at time t.

    Reference: Bass (1969), "A New Product Growth for Model Consumer Durables".
    """
    exponent = -k * (t - t0)
    # Clamp to avoid overflow
    exponent = max(-500, min(500, exponent))
    return L / (1.0 + math.exp(exponent))
