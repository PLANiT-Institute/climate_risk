import { facilitiesData } from "./facilities";

const REDUCTION_RATES: Record<string, number[]> = {
  net_zero_2050: [0.0485, 0.175, 0.384, 0.565, 0.682, 0.749],
  below_2c: [0.0485, 0.136, 0.286, 0.466, 0.598, 0.680],
  delayed_transition: [0.005, 0.035, 0.203, 0.503, 0.664, 0.732],
  current_policies: [0.0485, 0.080, 0.123, 0.167, 0.211, 0.253],
};

const CARBON_PRICES: Record<string, number[]> = {
  net_zero_2050: [75, 130, 175, 220, 240, 250],
  below_2c: [60, 100, 140, 180, 200, 200],
  delayed_transition: [50, 90, 135, 180, 180, 180],
  current_policies: [25, 40, 52, 64, 72, 80],
};

const YEARS = [2025, 2030, 2035, 2040, 2045, 2050];

const SCENARIO_NAMES: Record<string, string> = {
  net_zero_2050: "Net Zero 2050",
  below_2c: "Below 2°C",
  delayed_transition: "Delayed Transition",
  current_policies: "Current Policies",
};

function generateAnalysis(scenarioId: string) {
  const rates = REDUCTION_RATES[scenarioId];
  const prices = CARBON_PRICES[scenarioId];

  const facilities = facilitiesData.map((f) => {
    const base = f.current_emissions_scope1 + f.current_emissions_scope2;
    const s1Ratio = f.current_emissions_scope1 / base;
    const s2Ratio = f.current_emissions_scope2 / base;

    const emission_pathway = YEARS.map((year, i) => ({
      year,
      scope1_emissions: Math.round(base * s1Ratio * (1 - rates[i])),
      scope2_emissions: Math.round(base * s2Ratio * (1 - rates[i])),
      total_emissions: Math.round(base * (1 - rates[i])),
      reduction_factor: rates[i],
    }));

    const annual_impacts = YEARS.map((year, i) => {
      const emissions = base * (1 - rates[i]);
      const carbonCost = emissions * prices[i];
      const energyCost = f.annual_revenue * 0.002 * (1 - rates[i] * 0.5);
      const revImpact = carbonCost * 0.1;
      const capex = f.assets_value * 0.0001 * (1 + rates[i] * 10);
      const opex = f.assets_value * 0.00003 * (1 + rates[i] * 10);
      return {
        year,
        carbon_cost: Math.round(carbonCost),
        transition_capex: Math.round(capex),
        transition_opex: Math.round(opex),
        energy_cost_increase: Math.round(energyCost),
        revenue_impact: Math.round(revImpact),
        delta_ebitda: Math.round(-(carbonCost + energyCost + revImpact + capex + opex)),
        total_emissions: Math.round(emissions),
        stranded_asset_writedown: 0,
        scope3_impact: Math.round(f.current_emissions_scope3 * 0.001 * prices[i]),
        kets_free_allocation: null as number | null,
        kets_excess_emissions: null as number | null,
        kets_price_krw: null as number | null,
      };
    });

    const totalCost = annual_impacts.reduce((s, imp) => s + Math.abs(imp.delta_ebitda), 0);
    const npv = -Math.round(totalCost * 0.65);

    return {
      facility_id: f.facility_id,
      facility_name: f.name,
      sector: f.sector,
      scenario: scenarioId,
      risk_level: npv < -f.assets_value * 0.1 ? "High" : npv < -f.assets_value * 0.03 ? "Medium" : "Low",
      emission_pathway,
      annual_impacts,
      delta_npv: npv,
      npv_as_pct_of_assets: Math.round((npv / f.assets_value) * 10000) / 100,
    };
  });

  return {
    scenario: scenarioId,
    scenario_name: SCENARIO_NAMES[scenarioId],
    pricing_regime: "global",
    facilities,
    total_npv: facilities.reduce((s, f) => s + f.delta_npv, 0),
    total_baseline_emissions: 207230000,
    avg_risk_level: "High" as string,
  };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const analysisData: Record<string, any> = {
  net_zero_2050: generateAnalysis("net_zero_2050"),
  below_2c: generateAnalysis("below_2c"),
  delayed_transition: generateAnalysis("delayed_transition"),
  current_policies: generateAnalysis("current_policies"),
};

export const summaryData: Record<string, object> = {
  net_zero_2050: {
    scenario: "net_zero_2050",
    scenario_name: "Net Zero 2050",
    total_facilities: 17,
    total_baseline_emissions: 207230000,
    total_npv: -114744876590,
    high_risk_count: 14,
    medium_risk_count: 3,
    low_risk_count: 0,
    top_risk_facilities: [
      { facility_id: "KR-STL-001", name: "포항제철소", sector: "steel", delta_npv: -15894526478, risk_level: "High" },
      { facility_id: "KR-STL-002", name: "광양제철소", sector: "steel", delta_npv: -13688453263, risk_level: "High" },
      { facility_id: "KR-UTL-001", name: "당진화력발전소", sector: "utilities", delta_npv: -9578889237, risk_level: "High" },
      { facility_id: "KR-PCH-001", name: "울산석유화학단지", sector: "petrochemical", delta_npv: -9021325246, risk_level: "High" },
      { facility_id: "KR-OG-001", name: "울산정유공장", sector: "oil_gas", delta_npv: -8107534642, risk_level: "High" },
    ],
    cost_breakdown: { carbon_cost: 25894775452, energy_cost_increase: 1974215625, revenue_impact: 3076737645, transition_opex: 64586199 },
  },
  below_2c: {
    scenario: "below_2c",
    scenario_name: "Below 2°C",
    total_facilities: 17,
    total_baseline_emissions: 207230000,
    total_npv: -107163385498,
    high_risk_count: 14,
    medium_risk_count: 3,
    low_risk_count: 0,
    top_risk_facilities: [
      { facility_id: "KR-STL-001", name: "포항제철소", sector: "steel", delta_npv: -14841236891, risk_level: "High" },
      { facility_id: "KR-STL-002", name: "광양제철소", sector: "steel", delta_npv: -12781673249, risk_level: "High" },
      { facility_id: "KR-UTL-001", name: "당진화력발전소", sector: "utilities", delta_npv: -8941926718, risk_level: "High" },
      { facility_id: "KR-PCH-001", name: "울산석유화학단지", sector: "petrochemical", delta_npv: -8426183259, risk_level: "High" },
      { facility_id: "KR-OG-001", name: "울산정유공장", sector: "oil_gas", delta_npv: -7569873421, risk_level: "High" },
    ],
    cost_breakdown: { carbon_cost: 21894432876, energy_cost_increase: 1674215625, revenue_impact: 2603737645, transition_opex: 54586199 },
  },
  delayed_transition: {
    scenario: "delayed_transition",
    scenario_name: "Delayed Transition",
    total_facilities: 17,
    total_baseline_emissions: 207230000,
    total_npv: -91264637866,
    high_risk_count: 14,
    medium_risk_count: 3,
    low_risk_count: 0,
    top_risk_facilities: [
      { facility_id: "KR-STL-001", name: "포항제철소", sector: "steel", delta_npv: -12641289753, risk_level: "High" },
      { facility_id: "KR-STL-002", name: "광양제철소", sector: "steel", delta_npv: -10883492167, risk_level: "High" },
      { facility_id: "KR-UTL-001", name: "당진화력발전소", sector: "utilities", delta_npv: -7613925489, risk_level: "High" },
      { facility_id: "KR-PCH-001", name: "울산석유화학단지", sector: "petrochemical", delta_npv: -7174892345, risk_level: "High" },
      { facility_id: "KR-OG-001", name: "울산정유공장", sector: "oil_gas", delta_npv: -6443895236, risk_level: "High" },
    ],
    cost_breakdown: { carbon_cost: 18641932876, energy_cost_increase: 1424215625, revenue_impact: 2216737645, transition_opex: 46586199 },
  },
  current_policies: {
    scenario: "current_policies",
    scenario_name: "Current Policies",
    total_facilities: 17,
    total_baseline_emissions: 207230000,
    total_npv: -50875070909,
    high_risk_count: 11,
    medium_risk_count: 3,
    low_risk_count: 3,
    top_risk_facilities: [
      { facility_id: "KR-STL-001", name: "포항제철소", sector: "steel", delta_npv: -7046790643, risk_level: "High" },
      { facility_id: "KR-STL-002", name: "광양제철소", sector: "steel", delta_npv: -6072784954, risk_level: "High" },
      { facility_id: "KR-UTL-001", name: "당진화력발전소", sector: "utilities", delta_npv: -4248577123, risk_level: "High" },
      { facility_id: "KR-PCH-001", name: "울산석유화학단지", sector: "petrochemical", delta_npv: -4001464442, risk_level: "High" },
      { facility_id: "KR-OG-001", name: "울산정유공장", sector: "oil_gas", delta_npv: -3595268294, risk_level: "High" },
    ],
    cost_breakdown: { carbon_cost: 11462775452, energy_cost_increase: 874215625, revenue_impact: 1363737645, transition_opex: 28586199 },
  },
};

export const comparisonData = {
  scenarios: ["net_zero_2050", "below_2c", "delayed_transition", "current_policies"],
  npv_comparison: [
    { scenario: "net_zero_2050", scenario_name: "Net Zero 2050", total_npv: -114744876590, avg_risk_level: "High" },
    { scenario: "below_2c", scenario_name: "Below 2°C", total_npv: -107163385498, avg_risk_level: "High" },
    { scenario: "delayed_transition", scenario_name: "Delayed Transition", total_npv: -91264637866, avg_risk_level: "High" },
    { scenario: "current_policies", scenario_name: "Current Policies", total_npv: -50875070909, avg_risk_level: "High" },
  ],
  emission_pathways: {
    net_zero_2050: [
      { year: 2025, total_emissions: 179347913 }, { year: 2030, total_emissions: 136769296 },
      { year: 2035, total_emissions: 81403633 }, { year: 2040, total_emissions: 44402562 },
      { year: 2045, total_emissions: 29312139 }, { year: 2050, total_emissions: 24445268 },
    ],
    below_2c: [
      { year: 2025, total_emissions: 189440810 }, { year: 2030, total_emissions: 162978597 },
      { year: 2035, total_emissions: 119383459 }, { year: 2040, total_emissions: 76171846 },
      { year: 2045, total_emissions: 50315226 }, { year: 2050, total_emissions: 39238250 },
    ],
    delayed_transition: [
      { year: 2025, total_emissions: 206256098 }, { year: 2030, total_emissions: 200312253 },
      { year: 2035, total_emissions: 167337507 }, { year: 2040, total_emissions: 92393027 },
      { year: 2045, total_emissions: 51361554 }, { year: 2050, total_emissions: 43277404 },
    ],
    current_policies: [
      { year: 2025, total_emissions: 195312925 }, { year: 2030, total_emissions: 187816572 },
      { year: 2035, total_emissions: 177575788 }, { year: 2040, total_emissions: 165481926 },
      { year: 2045, total_emissions: 153428443 }, { year: 2050, total_emissions: 143284693 },
    ],
  } as Record<string, { year: number; total_emissions: number }[]>,
  risk_distribution: {
    net_zero_2050: { high: 14, medium: 3, low: 0 },
    below_2c: { high: 14, medium: 3, low: 0 },
    delayed_transition: { high: 14, medium: 3, low: 0 },
    current_policies: { high: 11, medium: 3, low: 3 },
  } as Record<string, { high: number; medium: number; low: number }>,
  cost_trends: {
    net_zero_2050: [
      { year: 2025, total_cost: 24844861982 }, { year: 2030, total_cost: 31759181141 },
      { year: 2035, total_cost: 27177037737 }, { year: 2040, total_cost: 24033364984 },
      { year: 2045, total_cost: 22073169272 }, { year: 2050, total_cost: 21567810956 },
    ],
    below_2c: [
      { year: 2025, total_cost: 20289604729 }, { year: 2030, total_cost: 27229973465 },
      { year: 2035, total_cost: 27261685771 }, { year: 2040, total_cost: 25010920384 },
      { year: 2045, total_cost: 22735138471 }, { year: 2050, total_cost: 21566360249 },
    ],
    delayed_transition: [
      { year: 2025, total_cost: 14367796256 }, { year: 2030, total_cost: 24159178022 },
      { year: 2035, total_cost: 29527060371 }, { year: 2040, total_cost: 23498076428 },
      { year: 2045, total_cost: 18220689001 }, { year: 2050, total_cost: 17496327104 },
    ],
    current_policies: [
      { year: 2025, total_cost: 7311209742 }, { year: 2030, total_cost: 10503517091 },
      { year: 2035, total_cost: 12318913996 }, { year: 2040, total_cost: 13864369241 },
      { year: 2045, total_cost: 15135617846 }, { year: 2050, total_cost: 15922454919 },
    ],
  } as Record<string, { year: number; total_cost: number }[]>,
};
