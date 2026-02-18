"""Transition risk analysis service – upgraded with S-curve, stranded assets, Scope 3.

Methodology upgrades:
- Linear reduction → Logistic S-curve (Bass 1969)
- Fixed energy proxy → Sector-specific energy cost model
- No stranded assets → Carbon Tracker-based forced writedown
- No Scope 3 → CDP-based Scope 3 exposure estimation
- Fixed WACC → Scenario-adjusted WACC (NGFS 2023)
- Revenue cap 30% → 50% (bankruptcy threshold)

References:
- Bass (1969), "A New Product Growth for Model Consumer Durables"
- Carbon Tracker Initiative (2023), "Unburnable Carbon"
- CDP Supply Chain Report (2023)
- NGFS Technical Documentation (2023)
- Demailly & Quirion (2008), cost pass-through analysis
"""

from typing import Dict, List

from ..core.config import (
    BASE_YEAR,
    PROJECTION_YEARS,
    DEFAULT_DISCOUNT_RATE,
    SCENARIOS,
    SECTOR_REDUCTION_MULTIPLIERS,
    SECTOR_DEMAND_ELASTICITIES,
    SECTOR_ENERGY_COST_SHARE,
    SECTOR_COST_PASSTHROUGH,
    SECTOR_SCOPE3_EXPOSURE,
    SCENARIO_SCURVE_PARAMS,
    STRANDED_ASSET_SCHEDULES,
)
from ..core.config import KETS_KRW_TO_USD
from ..data.sample_facilities import get_all_facilities
from ..services.carbon_pricing import (
    get_carbon_price_trajectory,
    calculate_transition_costs,
    calculate_kets_free_allocation,
)
from .risk_math import logistic_s_curve, npv_from_list, wacc_scenario_adjusted


# ── Emission Reduction (S-Curve) ────────────────────────────────────
def _reduction_factor(scenario_id: str, sector: str, year: int) -> float:
    """Logistic S-curve emission reduction factor.

    factor = L / (1 + exp(-k * (year - t0)))

    Replaces the old linear ramp to 2030 then flat approach.

    Args:
        scenario_id: NGFS scenario.
        sector: industry sector.
        year: projection year.

    Returns:
        Reduction fraction [0, ~0.95].

    Reference: Bass (1969); calibrated to NGFS pathway endpoints.
    """
    params = SCENARIO_SCURVE_PARAMS.get(scenario_id)
    if not params:
        # Fallback to simple linear for unknown scenarios
        target = SCENARIOS[scenario_id]["emissions_reduction_target"]
        years_to_2030 = 2030 - BASE_YEAR
        yf = year - BASE_YEAR
        if yf <= 0:
            return 0.0
        base = target * min(yf / years_to_2030, 1.0)
        mult = SECTOR_REDUCTION_MULTIPLIERS.get(sector, 1.0)
        return min(0.95, base * mult)

    k = params["k"]
    t0 = params["t0"]
    L_max = params["L_max"]

    # Sector-specific adjustment: some sectors transition faster/slower
    sector_mult = SECTOR_REDUCTION_MULTIPLIERS.get(sector, 1.0)
    # Adjust midpoint: fast sectors shift left, slow sectors shift right
    adjusted_t0 = t0 - (sector_mult - 1.0) * 5  # +/- up to ~1.5 years
    adjusted_L = min(0.95, L_max * sector_mult)

    if year <= BASE_YEAR:
        return 0.0

    return logistic_s_curve(year, adjusted_L, k, adjusted_t0)


# ── Energy Cost Model ───────────────────────────────────────────────
def _energy_cost_model(
    sector: str,
    year: int,
    scenario_id: str,
    baseline_revenue: float,
    reduction_achieved: float,
) -> float:
    """Sector-specific energy cost increase from transition.

    Method:
    - Base: sector energy share × revenue = energy spend
    - Green premium: transitioning to clean energy costs more initially
    - Premium declines 2.5% per year (learning/scale effects)
    - Net increase = energy_share × revenue × green_premium × (1 - cost_pass_through)

    Args:
        sector: industry sector.
        year: projection year.
        scenario_id: NGFS scenario.
        baseline_revenue: facility annual revenue.
        reduction_achieved: fraction of emissions already reduced.

    Returns:
        Annual energy cost increase (USD).

    Reference: IEA Energy Efficiency Indicators (2023); WorldSteel 2022.
    """
    energy_share = SECTOR_ENERGY_COST_SHARE.get(sector, 0.10)
    cost_passthrough = SECTOR_COST_PASSTHROUGH.get(sector, 0.50)

    # Green premium: starts at 30%, declines 2.5% per year from 2024
    years_from_base = max(0, year - BASE_YEAR)
    green_premium = max(0.05, 0.30 - 0.025 * years_from_base)

    # The more you've transitioned, the more you pay the premium
    energy_increase = baseline_revenue * energy_share * green_premium * reduction_achieved

    # Net cost after passing through to customers
    net_increase = energy_increase * (1 - cost_passthrough)

    return net_increase


# ── Revenue Impact ──────────────────────────────────────────────────
def _revenue_impact(
    baseline_revenue: float,
    carbon_cost: float,
    sector: str,
    scenario_id: str,
) -> float:
    """Enhanced revenue impact: pass-through + structural demand shift.

    Method:
    1. Carbon cost as fraction of revenue
    2. Demand elasticity effect (price increase → demand drop)
    3. Cost pass-through reduces effective burden
    4. Structural demand shift for fossil-dependent sectors under ambitious scenarios

    Reference: Demailly & Quirion (2008); Reinaud (2008).
    """
    if baseline_revenue <= 0:
        return 0.0

    elasticity = SECTOR_DEMAND_ELASTICITIES.get(sector, 0.15)
    cost_passthrough = SECTOR_COST_PASSTHROUGH.get(sector, 0.50)

    # Price increase effect: higher costs passed to consumers → demand drop
    cost_ratio = carbon_cost / baseline_revenue
    # Only the passed-through portion affects demand
    price_effect = baseline_revenue * (cost_ratio * cost_passthrough) * elasticity

    # Residual cost burden (not passed through)
    cost_burden = carbon_cost * (1 - cost_passthrough) * 0.1  # 10% margin impact

    # Structural demand shift: fossil sectors lose market share under transition
    structural_shift = 0.0
    if scenario_id in ("net_zero_2050", "below_2c"):
        shift_rates = {
            "oil_gas": 0.02, "utilities": 0.015, "shipping": 0.01,
            "petrochemical": 0.008, "steel": 0.005,
        }
        annual_shift = shift_rates.get(sector, 0.0)
        structural_shift = baseline_revenue * annual_shift

    total = price_effect + cost_burden + structural_shift
    return min(total, baseline_revenue * 0.50)  # 50% cap (bankruptcy threshold)


# ── Stranded Asset Writedown ────────────────────────────────────────
def _stranded_asset_writedown(
    sector: str,
    scenario_id: str,
    year: int,
    assets: float,
) -> float:
    """Calculate forced asset writedown due to stranding.

    Applies to sectors with scheduled phase-outs (utilities, oil_gas).

    Reference: Carbon Tracker Initiative (2023); IEA WEO 2023.
    """
    schedules = STRANDED_ASSET_SCHEDULES.get(sector)
    if not schedules:
        return 0.0

    schedule = schedules.get(scenario_id)
    if not schedule:
        return 0.0

    phase_out_year = schedule["phase_out_year"]
    annual_rate = schedule["annual_writedown_rate"]
    at_risk_fraction = schedule["asset_fraction_at_risk"]

    if year < BASE_YEAR:
        return 0.0

    # Writedown begins now and accelerates toward phase-out
    years_until_phase_out = max(1, phase_out_year - year)
    if year >= phase_out_year:
        # All at-risk assets written down
        return assets * at_risk_fraction * 0.1  # Residual cleanup cost

    # Progressive writedown
    at_risk_value = assets * at_risk_fraction
    writedown = at_risk_value * annual_rate

    return writedown


# ── Scope 3 Impact ──────────────────────────────────────────────────
def _scope3_impact_estimate(
    sector: str,
    scope3_emissions: float,
    scenario_id: str,
    year: int,
    carbon_price: float,
) -> float:
    """Estimate Scope 3 financial impact (supply/value chain carbon cost).

    Method:
    - Scope 3 exposure rate by sector (CDP 2023)
    - Applied to carbon price × scope 3 emissions
    - Represents pass-through costs from supply chain

    Reference: CDP Supply Chain Report 2023.
    """
    exposure = SECTOR_SCOPE3_EXPOSURE.get(sector, 0.05)

    # Scope 3 cost: only a fraction actually impacts the company
    scope3_cost = scope3_emissions * carbon_price * exposure

    return scope3_cost


# ── Risk Level Classification ───────────────────────────────────────
def _risk_level(npv_pct: float) -> str:
    if npv_pct <= -15:
        return "High"
    if npv_pct <= -5:
        return "Medium"
    return "Low"


# ── Public API ──────────────────────────────────────────────────────
def analyse_scenario(scenario_id: str, pricing_regime: str = "global") -> dict:
    """Full transition-risk analysis for one scenario.

    Args:
        scenario_id: NGFS scenario identifier.
        pricing_regime: "global" (default) or "kets" (K-ETS with free allocation).
    """
    facilities = get_all_facilities()
    carbon_prices = get_carbon_price_trajectory(
        scenario_id, PROJECTION_YEARS, pricing_regime=pricing_regime,
    )
    sc = SCENARIOS[scenario_id]

    results = []
    total_npv = 0.0
    total_baseline = 0.0

    for fac in facilities:
        fid = fac["facility_id"]
        sector = fac["sector"]
        baseline_s1 = fac["current_emissions_scope1"]
        baseline_s2 = fac["current_emissions_scope2"]
        baseline_s3 = fac["current_emissions_scope3"]
        baseline_total = baseline_s1 + baseline_s2
        baseline_rev = fac["annual_revenue"]
        baseline_ebitda = fac["ebitda"]
        assets = fac["assets_value"]

        total_baseline += baseline_total

        # Scenario-adjusted discount rate
        discount_rate = wacc_scenario_adjusted(DEFAULT_DISCOUNT_RATE, scenario_id, sector)

        pathway: list = []
        annual_impacts: list = []

        for year in PROJECTION_YEARS:
            rf = _reduction_factor(scenario_id, sector, year)
            s1 = baseline_s1 * (1 - rf)
            s2 = baseline_s2 * (1 - rf)
            total_e = s1 + s2
            pathway.append({
                "year": year,
                "scope1_emissions": round(s1),
                "scope2_emissions": round(s2),
                "total_emissions": round(total_e),
                "reduction_factor": round(rf, 4),
            })

            cp = carbon_prices[year]

            # K-ETS free allocation: only excess emissions are charged
            kets_alloc = None
            kets_excess = None
            if pricing_regime == "kets":
                kets_alloc = calculate_kets_free_allocation(sector, baseline_total, year)
                kets_excess = max(0.0, total_e - kets_alloc["free_allocation_tco2e"])
                carbon_cost = kets_excess * cp
            else:
                carbon_cost = total_e * cp

            tc = calculate_transition_costs(baseline_total, total_e, sector, year=year)
            energy_increase = _energy_cost_model(
                sector, year, scenario_id, baseline_rev, rf
            )
            rev_impact = _revenue_impact(baseline_rev, carbon_cost, sector, scenario_id)
            stranded = _stranded_asset_writedown(sector, scenario_id, year, assets)
            scope3_cost = _scope3_impact_estimate(
                sector, baseline_s3, scenario_id, year, cp
            )

            delta_ebitda = -(
                carbon_cost + tc["opex"] + energy_increase +
                rev_impact + stranded + scope3_cost
            )

            annual_impacts.append({
                "year": year,
                "carbon_cost": round(carbon_cost),
                "transition_capex": round(tc["capex"] / 5),
                "transition_opex": round(tc["opex"]),
                "energy_cost_increase": round(energy_increase),
                "revenue_impact": round(rev_impact),
                "delta_ebitda": round(delta_ebitda),
                "total_emissions": round(total_e),
                "stranded_asset_writedown": round(stranded),
                "scope3_impact": round(scope3_cost),
                "kets_free_allocation": round(kets_alloc["free_allocation_tco2e"]) if kets_alloc else None,
                "kets_excess_emissions": round(kets_excess) if kets_excess is not None else None,
                "kets_price_krw": round(cp / KETS_KRW_TO_USD) if pricing_regime == "kets" else None,
            })

        cash_flows = [ai["delta_ebitda"] for ai in annual_impacts]
        d_npv = npv_from_list(cash_flows, discount_rate)
        npv_pct = (d_npv / assets * 100) if assets else 0
        total_npv += d_npv

        results.append({
            "facility_id": fid,
            "facility_name": fac["name"],
            "sector": sector,
            "scenario": scenario_id,
            "risk_level": _risk_level(npv_pct),
            "emission_pathway": pathway,
            "annual_impacts": annual_impacts,
            "delta_npv": round(d_npv),
            "npv_as_pct_of_assets": round(npv_pct, 2),
        })

    # risk distribution
    levels = [r["risk_level"] for r in results]
    high = levels.count("High")
    med = levels.count("Medium")
    low = levels.count("Low")
    avg = "High" if high > med and high > low else ("Medium" if med >= low else "Low")

    return {
        "scenario": scenario_id,
        "scenario_name": sc["name"],
        "pricing_regime": pricing_regime,
        "facilities": results,
        "total_npv": round(total_npv),
        "total_baseline_emissions": round(total_baseline),
        "avg_risk_level": avg,
    }


def get_summary(scenario_id: str, pricing_regime: str = "global") -> dict:
    analysis = analyse_scenario(scenario_id, pricing_regime=pricing_regime)
    facs = analysis["facilities"]
    levels = [f["risk_level"] for f in facs]

    # cost breakdown (sum of last-year impacts across all facilities)
    total_carbon = sum(f["annual_impacts"][-1]["carbon_cost"] for f in facs)
    total_energy = sum(f["annual_impacts"][-1]["energy_cost_increase"] for f in facs)
    total_rev = sum(f["annual_impacts"][-1]["revenue_impact"] for f in facs)
    total_opex = sum(f["annual_impacts"][-1]["transition_opex"] for f in facs)

    top_risk = sorted(facs, key=lambda x: x["delta_npv"])[:5]
    return {
        "scenario": scenario_id,
        "scenario_name": analysis["scenario_name"],
        "total_facilities": len(facs),
        "total_baseline_emissions": analysis["total_baseline_emissions"],
        "total_npv": analysis["total_npv"],
        "high_risk_count": levels.count("High"),
        "medium_risk_count": levels.count("Medium"),
        "low_risk_count": levels.count("Low"),
        "top_risk_facilities": [
            {"facility_id": f["facility_id"], "name": f["facility_name"],
             "sector": f["sector"], "delta_npv": f["delta_npv"],
             "risk_level": f["risk_level"]}
            for f in top_risk
        ],
        "cost_breakdown": {
            "carbon_cost": round(total_carbon),
            "energy_cost_increase": round(total_energy),
            "revenue_impact": round(total_rev),
            "transition_opex": round(total_opex),
        },
    }


def compare_scenarios(pricing_regime: str = "global") -> dict:
    """Compare all four NGFS scenarios side-by-side."""
    scenario_ids = list(SCENARIOS.keys())
    analyses = {sid: analyse_scenario(sid, pricing_regime=pricing_regime) for sid in scenario_ids}

    npv_comparison = []
    emission_pathways: Dict[str, list] = {}
    risk_distribution: Dict[str, dict] = {}
    cost_trends: Dict[str, list] = {}

    for sid, a in analyses.items():
        npv_comparison.append({
            "scenario": sid,
            "scenario_name": a["scenario_name"],
            "total_npv": a["total_npv"],
            "avg_risk_level": a["avg_risk_level"],
        })

        # aggregate emission pathway
        yearly: Dict[int, float] = {}
        for fac in a["facilities"]:
            for pt in fac["emission_pathway"]:
                yearly[pt["year"]] = yearly.get(pt["year"], 0) + pt["total_emissions"]
        emission_pathways[sid] = [{"year": y, "total_emissions": round(e)} for y, e in sorted(yearly.items())]

        levels = [f["risk_level"] for f in a["facilities"]]
        risk_distribution[sid] = {
            "high": levels.count("High"),
            "medium": levels.count("Medium"),
            "low": levels.count("Low"),
        }

        # aggregate cost trends per year
        year_costs: Dict[int, float] = {}
        for fac in a["facilities"]:
            for ai in fac["annual_impacts"]:
                year_costs[ai["year"]] = year_costs.get(ai["year"], 0) + abs(ai["delta_ebitda"])
        cost_trends[sid] = [{"year": y, "total_cost": round(c)} for y, c in sorted(year_costs.items())]

    return {
        "scenarios": scenario_ids,
        "npv_comparison": npv_comparison,
        "emission_pathways": emission_pathways,
        "risk_distribution": risk_distribution,
        "cost_trends": cost_trends,
    }
