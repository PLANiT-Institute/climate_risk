import { facilitiesData } from "./facilities";

function generateHazards(f: typeof facilitiesData[0]) {
  return [
    {
      hazard_type: "flood",
      risk_level: "High",
      probability: 0.224,
      potential_loss: Math.round(f.assets_value * 0.018),
      description: "집중호우 및 하천 범람으로 인한 침수 위험",
      return_period_years: 17.9,
      climate_change_multiplier: 1.151,
      business_interruption_cost: 0,
    },
    {
      hazard_type: "typhoon",
      risk_level: "High",
      probability: 1.0,
      potential_loss: Math.round(f.assets_value * 0.214),
      description: "태풍 및 강풍에 의한 시설물 피해 위험",
      return_period_years: 0.8,
      climate_change_multiplier: 1.02,
      business_interruption_cost: Math.round(f.annual_revenue * 0.03),
    },
    {
      hazard_type: "heatwave",
      risk_level: "High",
      probability: 0.032,
      potential_loss: Math.round(f.assets_value * 0.05),
      description: "폭염에 의한 설비 효율 저하 및 근로자 안전 위험",
      return_period_years: 1.0,
      climate_change_multiplier: 1.16,
      business_interruption_cost: Math.round(f.annual_revenue * 0.004),
    },
    {
      hazard_type: "drought",
      risk_level: "High",
      probability: 0.062,
      potential_loss: Math.round(f.assets_value * 0.016),
      description: "가뭄으로 인한 용수 부족 및 생산 차질 위험",
      return_period_years: 17.2,
      climate_change_multiplier: 1.06,
      business_interruption_cost: Math.round(f.annual_revenue * 0.004),
    },
    {
      hazard_type: "sea_level_rise",
      risk_level: "Low",
      probability: 0.044,
      potential_loss: 3000000,
      description: "해수면 상승에 따른 연안 시설 침수 위험",
      return_period_years: 1.0,
      climate_change_multiplier: 1.0,
      business_interruption_cost: 0,
    },
  ];
}

export const physicalRiskData = {
  total_facilities: 17,
  overall_risk_summary: { High: 17, Medium: 0, Low: 0 } as Record<string, number>,
  facilities: facilitiesData.map((f) => {
    const hazards = generateHazards(f);
    return {
      facility_id: f.facility_id,
      facility_name: f.name,
      location: f.location,
      latitude: f.latitude,
      longitude: f.longitude,
      overall_risk_level: "High",
      hazards,
      total_expected_annual_loss: hazards.reduce((s, h) => s + h.potential_loss, 0),
    };
  }),
  model_status: "analytical_v1",
  scenario: "current_policies",
  assessment_year: 2030,
  warming_above_preindustrial: 1.5,
  data_source: "hardcoded_config",
};
