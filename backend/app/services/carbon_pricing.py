"""Carbon pricing model with multi-point trajectories and technology-stack MAC curves.

Upgraded from 3-point linear interpolation to 8-point NGFS paths,
and from 4-tier step function MAC to continuous technology-stack based curves.

References:
- NGFS Phase IV Scenarios (2023) for carbon price paths
- IEA ETP 2023, IRENA 2023 for technology costs and learning rates
- Wright's Law for learning curve cost reduction
"""

import math
from typing import Dict, List, Optional

from ..core.config import (
    BASE_YEAR,
    SCENARIOS,
    SECTOR_MAC_BASE_COSTS,
    SECTOR_CAPEX_RATIOS,
    NGFS_CARBON_PRICE_PATHS,
    KETS_PRICE_PATHS,
    KETS_KRW_TO_USD,
    KETS_ALLOCATION_RATIOS,
    SECTOR_ABATEMENT_TECHNOLOGIES,
)
from .risk_math import piecewise_linear_interpolate


def get_carbon_price_trajectory(
    scenario_id: str,
    years: List[int],
    pricing_regime: str = "global",
) -> Dict[int, float]:
    """Multi-point carbon price trajectory using piecewise linear interpolation.

    Args:
        scenario_id: NGFS scenario identifier.
        years: list of years to compute prices for.
        pricing_regime: "global" (default, $/tCO2e), "kets" (K-ETS, converted to USD),
                        "eu_ets" (placeholder, uses global * 1.1).

    Returns:
        {year: price_usd_per_tco2e} mapping.

    Backward compatible: 2025/2030/2050 values match original SCENARIOS config.
    """
    if pricing_regime == "kets":
        return get_kets_price_trajectory(scenario_id, years)

    # Use multi-point paths; fall back to legacy 3-point for unknown scenarios
    if scenario_id in NGFS_CARBON_PRICE_PATHS:
        knots = NGFS_CARBON_PRICE_PATHS[scenario_id]
    else:
        # Legacy fallback
        sc = SCENARIOS.get(scenario_id, SCENARIOS["current_policies"])
        knots = {
            BASE_YEAR: 0.0,
            2025: sc["carbon_price_2025"],
            2030: sc["carbon_price_2030"],
            2050: sc["carbon_price_2050"],
        }

    prices: Dict[int, float] = {}
    for y in years:
        p = piecewise_linear_interpolate(knots, y)
        if pricing_regime == "eu_ets":
            p *= 1.1  # EU ETS premium over global benchmark
        prices[y] = max(0.0, round(p, 2))
    return prices


def get_kets_price_trajectory(
    scenario_id: str,
    years: List[int],
) -> Dict[int, float]:
    """K-ETS specific price trajectory (converted to USD).

    Source: KRX historical + Ministry of Environment projections.
    """
    if scenario_id in KETS_PRICE_PATHS:
        knots_krw = KETS_PRICE_PATHS[scenario_id]
    else:
        knots_krw = KETS_PRICE_PATHS["current_policies"]

    prices: Dict[int, float] = {}
    for y in years:
        p_krw = piecewise_linear_interpolate(knots_krw, y)
        prices[y] = max(0.0, round(p_krw * KETS_KRW_TO_USD, 2))
    return prices


def calculate_kets_free_allocation(
    sector: str,
    baseline_emissions: float,
    year: int,
) -> Dict[str, float]:
    """Calculate K-ETS free allocation for a given sector and year.

    Free allocation decreases over time as Korea tightens its ETS caps.

    Args:
        sector: industry sector.
        baseline_emissions: baseline total emissions (tCO2e).
        year: assessment year.

    Returns:
        {"allocation_ratio": float, "free_allocation_tco2e": float}

    Reference: 환경부, K-ETS Phase 3/4 할당계획.
    """
    params = KETS_ALLOCATION_RATIOS.get(sector)
    if not params:
        # Sector not covered by K-ETS
        return {"allocation_ratio": 0.0, "free_allocation_tco2e": 0.0}

    base_ratio = params["base_ratio"]
    tightening = params["annual_tightening"]
    base_year = params["base_year"]

    years_elapsed = max(0, year - base_year)
    allocation_ratio = max(0.0, base_ratio - tightening * years_elapsed)
    free_allocation = baseline_emissions * allocation_ratio

    return {
        "allocation_ratio": round(allocation_ratio, 4),
        "free_allocation_tco2e": round(free_allocation, 2),
    }


def get_technology_cost_projection(
    tech_mac_base: float,
    learning_rate: float,
    available_year: int,
    target_year: int,
    reference_year: int = 2020,
) -> float:
    """Project technology cost using experience-curve decay.

    cost(t) = mac_base * (1 - learning_rate) ^ (t - reference_year)

    METHODOLOGICAL NOTE: True Wright's Law (1936) relates cost to
    cumulative production volume, not to elapsed time. The time-based
    formulation used here is a simplification that assumes approximately
    constant annual deployment growth, making elapsed years a rough proxy
    for cumulative doublings. This is standard practice in IEA/IRENA
    screening models (e.g., IRENA 2023 Fig. 3.7) but overstates cost
    reduction when deployment stalls and understates it during boom periods.

    The "learning_rate" parameter here is an annual cost reduction rate,
    NOT the traditional Wright's Law learning rate (% cost reduction per
    doubling of cumulative production).

    Args:
        tech_mac_base: base MAC at reference year ($/tCO2e).
        learning_rate: annual cost reduction rate (0-1).
        available_year: first year technology is commercially available.
        target_year: year to project cost for.
        reference_year: base year for learning curve.

    Returns:
        Projected MAC ($/tCO2e).

    Reference: Wright (1936); IRENA Renewable Power Generation Costs 2023;
    Way et al. (2022), "Empirically grounded technology forecasts and the
    energy transition", Joule, 6(9), 2057-2082.
    """
    if target_year < available_year:
        return float("inf")  # Not yet available

    years_of_learning = target_year - reference_year
    if years_of_learning <= 0:
        return tech_mac_base

    return tech_mac_base * ((1 - learning_rate) ** years_of_learning)


def get_marginal_abatement_cost(
    sector: str,
    reduction_pct: float,
    year: int = 2030,
) -> float:
    """Technology-stack based marginal abatement cost.

    Sorts available technologies by MAC (ascending), accumulates
    max_reduction until the target reduction_pct is reached.
    Returns the MAC of the marginal technology needed.

    For reductions beyond the technology stack capacity, applies
    exponential penalty (backstop technology).

    Args:
        sector: industry sector.
        reduction_pct: target emission reduction fraction (0 to 1).
        year: assessment year (affects technology availability and learning costs).

    Returns:
        Marginal abatement cost ($/tCO2e).

    Reference: McKinsey MAC curve methodology; IEA ETP 2023 sector roadmaps.
    """
    if reduction_pct <= 0:
        return 0.0

    techs = SECTOR_ABATEMENT_TECHNOLOGIES.get(sector)
    if not techs:
        # Fallback to legacy step function for sectors without tech stack
        base = SECTOR_MAC_BASE_COSTS.get(sector, 50.0)
        if reduction_pct <= 0.2:
            return base
        elif reduction_pct <= 0.5:
            return base * 1.5
        elif reduction_pct <= 0.8:
            return base * 2.5
        else:
            return base * 4.0

    # Sort by projected MAC at target year
    available_techs = []
    for t in techs:
        if year >= t["available_year"]:
            projected_mac = get_technology_cost_projection(
                t["mac"], t["learning_rate"], t["available_year"], year
            )
            available_techs.append({
                "tech": t["tech"],
                "mac": projected_mac,
                "max_reduction": t["max_reduction"],
            })

    if not available_techs:
        # No technologies available yet; use base cost with penalty
        return SECTOR_MAC_BASE_COSTS.get(sector, 50.0) * 3.0

    # Sort by MAC ascending (cheapest first)
    available_techs.sort(key=lambda x: x["mac"])

    cumulative_reduction = 0.0
    marginal_mac = available_techs[0]["mac"]

    for tech in available_techs:
        if cumulative_reduction >= reduction_pct:
            break
        cumulative_reduction += tech["max_reduction"]
        marginal_mac = tech["mac"]

    # If target reduction exceeds technology stack, apply exponential backstop
    if reduction_pct > cumulative_reduction and cumulative_reduction > 0:
        overshoot = (reduction_pct - cumulative_reduction) / cumulative_reduction
        # Exponential penalty: cost rises sharply beyond available technology
        backstop_multiplier = 1.0 + 3.0 * (math.exp(overshoot) - 1.0)
        marginal_mac = marginal_mac * backstop_multiplier

    return round(marginal_mac, 2)


def calculate_transition_costs(
    current_emissions: float,
    target_emissions: float,
    sector: str,
    timeframe_years: int = 5,
    year: int = 2030,
) -> Dict[str, float]:
    """Calculate transition CAPEX and OPEX with learning-curve adjusted technology costs.

    Args:
        current_emissions: current annual emissions (tCO2e).
        target_emissions: target annual emissions (tCO2e).
        sector: industry sector.
        timeframe_years: period over which OPEX is annualized.
        year: assessment year (affects technology costs via learning curves).

    Returns:
        {"capex": ..., "opex": ..., "total": ...}
    """
    reduction = current_emissions - target_emissions
    if reduction <= 0:
        return {"capex": 0.0, "opex": 0.0, "total": 0.0}

    reduction_pct = reduction / current_emissions if current_emissions > 0 else 0
    mac = get_marginal_abatement_cost(sector, reduction_pct, year)
    capex_ratio = SECTOR_CAPEX_RATIOS.get(sector, 0.70)
    total = reduction * mac
    capex = total * capex_ratio
    opex = total * (1 - capex_ratio) / max(timeframe_years, 1)
    return {"capex": round(capex, 2), "opex": round(opex, 2), "total": round(total, 2)}
