const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ── Scenarios ──
export const fetchScenarios = () => fetcher<Scenario[]>("/api/v1/scenarios");

// ── Company ──
export const fetchFacilities = () => fetcher<Facility[]>("/api/v1/company/facilities");
export const fetchSectors = () => fetcher<string[]>("/api/v1/company/sectors");

// ── Transition Risk ──
export const fetchTransitionAnalysis = (scenario: string, pricingRegime: string = "global") =>
  fetcher<TransitionRiskAnalysis>(
    `/api/v1/transition-risk/analysis?scenario=${scenario}&pricing_regime=${pricingRegime}`
  );
export const fetchTransitionSummary = (scenario: string, pricingRegime: string = "global") =>
  fetcher<TransitionRiskSummary>(
    `/api/v1/transition-risk/summary?scenario=${scenario}&pricing_regime=${pricingRegime}`
  );
export const fetchTransitionComparison = (pricingRegime: string = "global") =>
  fetcher<ScenarioComparison>(
    `/api/v1/transition-risk/comparison?pricing_regime=${pricingRegime}`
  );

// ── Physical Risk ──
export const fetchPhysicalRisk = (useApiData: boolean = false) =>
  fetcher<PhysicalRiskAssessment>(
    `/api/v1/physical-risk/assessment?use_api_data=${useApiData}`
  );

export const simulatePhysicalRisk = async (
  payload: {
    scenario: string;
    year: number;
    use_api_data: boolean;
    facilities: Facility[];
  },
  partnerId?: string | null,
) => {
  const url = partnerId
    ? apiUrl(`/api/v1/partner/sessions/${partnerId}/physical-risk/simulate`)
    : apiUrl("/api/v1/physical-risk/simulate");
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("분석 시뮬레이션 중 오류가 발생했습니다.");
  return res.json() as Promise<PhysicalRiskAssessment>;
};

// ── ESG ──
export const fetchESGAssessment = (framework: string) =>
  fetcher<ESGAssessment>(`/api/v1/esg/assessment?framework=${framework}`);
export const fetchESGDisclosure = (framework: string) =>
  fetcher<ESGDisclosureData>(`/api/v1/esg/disclosure-data?framework=${framework}`);
export const fetchESGFrameworks = () =>
  fetcher<ESGFramework[]>("/api/v1/esg/frameworks");

// ── SWR key helpers ──
export const apiUrl = (path: string) => `${API_BASE}${path}`;
export const swrFetcher = (url: string) => fetch(url).then((r) => r.json());

// ── Types ──
export interface Scenario {
  id: string;
  name: string;
  description: string;
  carbon_price_2025: number;
  carbon_price_2030: number;
  carbon_price_2050: number;
  emissions_reduction_target: number;
  color: string;
}

export interface Facility {
  facility_id: string;
  name: string;
  company: string;
  sector: string;
  location: string;
  latitude: number;
  longitude: number;
  current_emissions_scope1: number;
  current_emissions_scope2: number;
  current_emissions_scope3: number;
  annual_revenue: number;
  ebitda: number;
  assets_value: number;
}

export interface EmissionPathwayPoint {
  year: number;
  scope1_emissions: number;
  scope2_emissions: number;
  total_emissions: number;
  reduction_factor: number;
}

export interface AnnualImpact {
  year: number;
  carbon_cost: number;
  transition_capex: number;
  transition_opex: number;
  energy_cost_increase: number;
  revenue_impact: number;
  delta_ebitda: number;
  total_emissions: number;
  kets_free_allocation: number | null;
  kets_excess_emissions: number | null;
  kets_price_krw: number | null;
}

export interface FacilityTransitionRisk {
  facility_id: string;
  facility_name: string;
  sector: string;
  scenario: string;
  risk_level: string;
  emission_pathway: EmissionPathwayPoint[];
  annual_impacts: AnnualImpact[];
  delta_npv: number;
  npv_as_pct_of_assets: number;
}

export interface TransitionRiskAnalysis {
  scenario: string;
  scenario_name: string;
  facilities: FacilityTransitionRisk[];
  total_npv: number;
  total_baseline_emissions: number;
  avg_risk_level: string;
  pricing_regime: string;
}

export interface TransitionRiskSummary {
  scenario: string;
  scenario_name: string;
  total_facilities: number;
  total_baseline_emissions: number;
  total_npv: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  top_risk_facilities: { facility_id: string; name: string; sector: string; delta_npv: number; risk_level: string }[];
  cost_breakdown: { carbon_cost: number; energy_cost_increase: number; revenue_impact: number; transition_opex: number };
}

export interface ScenarioComparison {
  scenarios: string[];
  npv_comparison: { scenario: string; scenario_name: string; total_npv: number; avg_risk_level: string }[];
  emission_pathways: Record<string, { year: number; total_emissions: number }[]>;
  risk_distribution: Record<string, { high: number; medium: number; low: number }>;
  cost_trends: Record<string, { year: number; total_cost: number }[]>;
}

export interface HazardRisk {
  hazard_type: string;
  risk_level: string;
  probability: number;
  potential_loss: number;
  description: string;
  return_period_years: number;
  climate_change_multiplier: number;
  business_interruption_cost: number;
}

export interface FacilityPhysicalRisk {
  facility_id: string;
  facility_name: string;
  location: string;
  latitude: number;
  longitude: number;
  overall_risk_level: string;
  hazards: HazardRisk[];
  total_expected_annual_loss: number;
}

export interface PhysicalRiskAssessment {
  total_facilities: number;
  overall_risk_summary: Record<string, number>;
  facilities: FacilityPhysicalRisk[];
  model_status: string;
  scenario: string;
  assessment_year: number;
  warming_above_preindustrial: number;
  data_source: string;
}

export interface FrameworkScore {
  category: string;
  score: number;
  max_score: number;
  status: string;
}

export interface ChecklistItem {
  item: string;
  status: string;
  recommendation: string;
}

export interface GapAnalysisItem {
  category: string;
  current_score: number;
  target_score: number;
  gap: number;
  impact: number;
  effort: string;
  priority_score: number;
  recommended_actions: string[];
}

export interface RegulatoryDeadline {
  name: string;
  date: string;
  description: string;
  source: string;
}

export interface MaturityLevel {
  level: number;
  name: string;
  description: string;
}

export interface ESGAssessment {
  framework: string;
  framework_name: string;
  overall_score: number;
  compliance_level: string;
  categories: FrameworkScore[];
  checklist: ChecklistItem[];
  recommendations: string[];
  maturity_level?: MaturityLevel;
  gap_analysis?: GapAnalysisItem[];
  regulatory_deadlines?: RegulatoryDeadline[];
}

export interface ESGDisclosureData {
  framework: string;
  company_name: string;
  assessment_date: string;
  metrics: Record<string, Record<string, number | string | boolean>>;
  narrative_sections: Record<string, string>;
}

export interface ESGFramework {
  id: string;
  name: string;
  description: string;
}
