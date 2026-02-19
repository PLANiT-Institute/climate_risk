"""Pydantic v2 schemas for the Climate Risk Platform API."""

from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ───────────────────────── Scenario ─────────────────────────
class ScenarioOut(BaseModel):
    id: str
    name: str
    description: str
    carbon_price_2025: float
    carbon_price_2030: float
    carbon_price_2050: float
    emissions_reduction_target: float
    color: str


# ───────────────────────── Facility / Company ─────────────────────────
class FacilityOut(BaseModel):
    facility_id: str
    name: str
    company: str
    sector: str
    location: str
    latitude: float
    longitude: float
    current_emissions_scope1: float  # tCO2e
    current_emissions_scope2: float
    current_emissions_scope3: float
    annual_revenue: float  # USD
    ebitda: float
    assets_value: float


class FacilityIn(BaseModel):
    facility_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    company: str = Field(..., min_length=1, max_length=200)
    sector: str = Field(..., min_length=1, max_length=50)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    current_emissions_scope1: float = Field(..., gt=0)
    current_emissions_scope2: float = Field(..., gt=0)
    annual_revenue: float = Field(..., gt=0)
    ebitda: float  # 음수 가능
    assets_value: float = Field(..., gt=0)
    current_emissions_scope3: float = Field(default=0.0, ge=0)
    location: str = Field(default="")


class PartnerSessionCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    facilities: list[FacilityIn] = Field(..., min_length=1, max_length=200)


class PartnerSessionOut(BaseModel):
    partner_id: str
    company_name: str
    facility_count: int
    sectors: list[str]
    sector_warnings: list[str]
    expires_in_seconds: int


# ───────────────────────── Transition Risk ─────────────────────────
class EmissionPathwayPoint(BaseModel):
    year: int
    scope1_emissions: float
    scope2_emissions: float
    total_emissions: float
    reduction_factor: float


class AnnualImpact(BaseModel):
    year: int
    carbon_cost: float
    transition_capex: float
    transition_opex: float
    energy_cost_increase: float
    revenue_impact: float
    delta_ebitda: float
    total_emissions: float
    stranded_asset_writedown: Optional[float] = None
    scope3_impact: Optional[float] = None


class FacilityTransitionRisk(BaseModel):
    facility_id: str
    facility_name: str
    sector: str
    scenario: str
    risk_level: str  # High / Medium / Low
    emission_pathway: List[EmissionPathwayPoint]
    annual_impacts: List[AnnualImpact]
    delta_npv: float
    npv_as_pct_of_assets: float


class TransitionRiskAnalysis(BaseModel):
    scenario: str
    scenario_name: str
    facilities: List[FacilityTransitionRisk]
    total_npv: float
    total_baseline_emissions: float
    avg_risk_level: str


class TransitionRiskSummary(BaseModel):
    scenario: str
    scenario_name: str
    total_facilities: int
    total_baseline_emissions: float
    total_npv: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    top_risk_facilities: List[dict]
    cost_breakdown: dict


class ScenarioComparison(BaseModel):
    scenarios: List[str]
    npv_comparison: List[dict]
    emission_pathways: Dict[str, List[dict]]
    risk_distribution: Dict[str, dict]
    cost_trends: Dict[str, List[dict]]


# ───────────────────────── Physical Risk ─────────────────────────
class HazardRisk(BaseModel):
    hazard_type: str
    risk_level: str
    probability: float
    potential_loss: float
    description: str
    return_period_years: Optional[float] = None
    climate_change_multiplier: Optional[float] = None
    business_interruption_cost: Optional[float] = None


class FacilityPhysicalRisk(BaseModel):
    facility_id: str
    facility_name: str
    location: str
    latitude: float
    longitude: float
    overall_risk_level: str
    hazards: List[HazardRisk]
    total_expected_annual_loss: float


class PhysicalRiskAssessment(BaseModel):
    total_facilities: int
    overall_risk_summary: dict
    facilities: List[FacilityPhysicalRisk]
    model_status: str  # "analytical_v1" | "placeholder"
    scenario: Optional[str] = None
    assessment_year: Optional[int] = None
    warming_above_preindustrial: Optional[float] = None


# ───────────────────────── ESG ─────────────────────────
class FrameworkScore(BaseModel):
    category: str
    score: float
    max_score: float
    status: str


class ChecklistItem(BaseModel):
    item: str
    status: str  # "compliant" | "partial" | "non_compliant"
    recommendation: str


class ESGFrameworkAssessment(BaseModel):
    framework: str
    framework_name: str
    overall_score: float
    compliance_level: str
    categories: List[FrameworkScore]
    checklist: List[ChecklistItem]
    recommendations: List[str]
    maturity_level: Optional[dict] = None
    gap_analysis: Optional[List[dict]] = None
    regulatory_deadlines: Optional[List[dict]] = None


class ESGDisclosureData(BaseModel):
    framework: str
    company_name: str
    assessment_date: str
    metrics: Dict[str, dict]
    narrative_sections: Dict[str, str]


# ───────────────────────── Dashboard KPI ─────────────────────────
class DashboardKPI(BaseModel):
    total_emissions: float
    total_facilities: int
    transition_npv_net_zero: float
    transition_npv_current: float
    esg_readiness_score: float
    high_risk_facilities: int
