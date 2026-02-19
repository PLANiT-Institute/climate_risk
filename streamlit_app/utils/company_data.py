"""Company-level data utilities for Streamlit — caching, filtering, aggregation."""

import streamlit as st

from app.data.sample_facilities import (
    get_company_list,
    get_facilities_by_company,
    get_company_summary,
)
from app.services.transition_risk import analyse_scenario, compare_scenarios
from app.services.physical_risk import assess_physical_risk
from app.services.esg_compliance import assess_framework, get_disclosure_data


# ── Cached analysis calls ────────────────────────────────────────────

@st.cache_data(ttl=600)
def get_cached_transition(scenario_id: str, pricing_regime: str = "global") -> dict:
    """Cached transition risk analysis (all facilities)."""
    return analyse_scenario(scenario_id, pricing_regime=pricing_regime)


@st.cache_data(ttl=600)
def get_cached_physical(scenario_id: str = "current_policies", year: int = 2030) -> dict:
    """Cached physical risk assessment (all facilities)."""
    return assess_physical_risk(scenario_id=scenario_id, year=year)


@st.cache_data(ttl=600)
def get_cached_comparison(pricing_regime: str = "global") -> dict:
    """Cached scenario comparison (all facilities)."""
    return compare_scenarios(pricing_regime=pricing_regime)


@st.cache_data(ttl=600)
def get_cached_esg(framework_id: str) -> dict:
    """Cached ESG framework assessment."""
    return assess_framework(framework_id)


@st.cache_data(ttl=600)
def get_cached_disclosure(framework_id: str) -> dict:
    """Cached disclosure data."""
    return get_disclosure_data(framework_id)


# ── Company filtering ────────────────────────────────────────────────

def filter_transition_by_company(result: dict, company: str) -> dict:
    """Filter transition risk result to facilities of a specific company.

    Returns a new dict with filtered facilities and recalculated totals.
    """
    company_facs = [f for f in result["facilities"] if f.get("company") == company]
    if not company_facs:
        # Fallback: match by facility name prefix from sample data
        company_facility_ids = {
            f["facility_id"] for f in get_facilities_by_company(company)
        }
        company_facs = [
            f for f in result["facilities"]
            if f.get("facility_id") in company_facility_ids
        ]

    total_npv = sum(f["delta_npv"] for f in company_facs)

    # baseline_emissions is not per-facility in the result; compute from source data
    src_facs = get_facilities_by_company(company)
    total_emissions = sum(
        f["current_emissions_scope1"] + f["current_emissions_scope2"] for f in src_facs
    )

    return {
        **result,
        "facilities": company_facs,
        "total_npv": total_npv,
        "total_baseline_emissions": total_emissions,
    }


def filter_physical_by_company(result: dict, company: str) -> dict:
    """Filter physical risk result to facilities of a specific company."""
    company_facility_ids = {
        f["facility_id"] for f in get_facilities_by_company(company)
    }
    company_facs = [
        f for f in result["facilities"]
        if f.get("facility_id") in company_facility_ids
    ]

    risk_counts = {"High": 0, "Medium": 0, "Low": 0}
    for f in company_facs:
        level = f.get("overall_risk_level", "Low")
        risk_counts[level] = risk_counts.get(level, 0) + 1

    return {
        **result,
        "facilities": company_facs,
        "overall_risk_summary": risk_counts,
    }


def filter_comparison_by_company(result: dict, company: str) -> dict:
    """Filter scenario comparison result to a specific company's facilities."""
    company_facility_ids = {
        f["facility_id"] for f in get_facilities_by_company(company)
    }

    new_npv = []
    new_emission_paths = {}
    new_risk_dist = {}
    new_cost_trends = {}

    for item in result["npv_comparison"]:
        sid = item["scenario"]
        # Re-run filtered analysis for this scenario
        full = get_cached_transition(sid, result.get("pricing_regime", "global"))
        filtered = filter_transition_by_company(full, company)

        risk_levels = [f["risk_level"] for f in filtered["facilities"]]
        high = risk_levels.count("High")
        med = risk_levels.count("Medium")
        low = risk_levels.count("Low")

        new_npv.append({
            **item,
            "total_npv": filtered["total_npv"],
            "avg_risk_level": "High" if high > 0 else ("Medium" if med > 0 else "Low"),
        })
        new_risk_dist[sid] = {"high": high, "medium": med, "low": low}

    # Emission pathways: aggregate company facilities only
    for sid, pathway in result.get("emission_pathways", {}).items():
        full = get_cached_transition(sid, result.get("pricing_regime", "global"))
        filtered_facs = [
            f for f in full["facilities"]
            if f.get("facility_id") in company_facility_ids
        ]
        year_totals = {}
        for fac in filtered_facs:
            for pt in fac.get("emission_pathway", []):
                y = pt["year"]
                if y not in year_totals:
                    year_totals[y] = 0
                year_totals[y] += pt.get("scope1_emissions", 0) + pt.get("scope2_emissions", 0)
        new_emission_paths[sid] = [
            {"year": y, "total_emissions": e} for y, e in sorted(year_totals.items())
        ]

    # Cost trends: aggregate company facilities only
    for sid, trend in result.get("cost_trends", {}).items():
        full = get_cached_transition(sid, result.get("pricing_regime", "global"))
        filtered_facs = [
            f for f in full["facilities"]
            if f.get("facility_id") in company_facility_ids
        ]
        year_costs = {}
        for fac in filtered_facs:
            for imp in fac.get("annual_impacts", []):
                y = imp["year"]
                if y not in year_costs:
                    year_costs[y] = 0
                year_costs[y] += sum(
                    imp.get(k, 0)
                    for k in ["carbon_cost", "energy_cost_increase", "revenue_impact",
                              "transition_opex", "stranded_asset_writedown", "scope3_impact"]
                )
        new_cost_trends[sid] = [
            {"year": y, "total_cost": c} for y, c in sorted(year_costs.items())
        ]

    return {
        **result,
        "npv_comparison": new_npv,
        "emission_pathways": new_emission_paths,
        "risk_distribution": new_risk_dist,
        "cost_trends": new_cost_trends,
    }


def aggregate_company_metrics(facilities: list[dict], metric_key: str = "delta_npv") -> float:
    """Sum a numeric field across a list of facility dicts."""
    return sum(f.get(metric_key, 0) for f in facilities)
