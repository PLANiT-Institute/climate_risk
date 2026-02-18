export const frameworksData = [
  { id: "tcfd", name: "TCFD", description: "Task Force on Climate-related Financial Disclosures" },
  { id: "issb", name: "ISSB (IFRS S2)", description: "International Sustainability Standards Board" },
  { id: "kssb", name: "KSSB", description: "한국 지속가능성 기준위원회 (Korea Sustainability Standards Board)" },
];

export const assessmentData: Record<string, object> = {
  tcfd: {
    framework: "tcfd",
    framework_name: "TCFD",
    overall_score: 82.5,
    compliance_level: "우수",
    categories: [
      { category: "거버넌스", score: 75, max_score: 100, status: "양호" },
      { category: "전략", score: 90, max_score: 100, status: "우수" },
      { category: "리스크 관리", score: 85, max_score: 100, status: "우수" },
      { category: "지표 및 목표", score: 80, max_score: 100, status: "우수" },
    ],
    checklist: [
      { item: "이사회의 기후 리스크 감독 체계", status: "partial", recommendation: "기후 전담 위원회 설치를 권고합니다" },
      { item: "경영진의 기후 리스크 평가/관리 역할", status: "compliant", recommendation: "" },
      { item: "기후 리스크/기회 식별", status: "compliant", recommendation: "" },
      { item: "시나리오 분석(2°C 이하 포함)", status: "compliant", recommendation: "" },
      { item: "비즈니스 전략 영향 분석", status: "compliant", recommendation: "" },
      { item: "리스크 식별 및 평가 프로세스", status: "compliant", recommendation: "" },
      { item: "Scope 1/2 배출량 공시", status: "compliant", recommendation: "" },
      { item: "Scope 3 배출량 공시", status: "partial", recommendation: "주요 카테고리 Scope 3 배출량을 공시하세요" },
      { item: "기후 관련 목표 설정", status: "partial", recommendation: "SBTi 인증 목표 설정을 권고합니다" },
    ],
    recommendations: [
      "기후 전담 위원회 설치를 권고합니다",
      "주요 카테고리 Scope 3 배출량을 공시하세요",
      "SBTi 인증 목표 설정을 권고합니다",
    ],
    maturity_level: { level: 4, name: "관리", description: "체계적 기후 리스크 관리 및 측정 수행" },
    gap_analysis: [
      { category: "지표 및 목표", current_score: 80, target_score: 100, gap: 20, impact: 5.0, effort: "low", priority_score: 5.0, recommended_actions: ["목표 달성 이행 모니터링 강화"] },
      { category: "거버넌스", current_score: 75, target_score: 100, gap: 25, impact: 6.2, effort: "medium", priority_score: 3.1, recommended_actions: ["기후 리스크 감독 프로세스 고도화"] },
      { category: "리스크 관리", current_score: 85, target_score: 100, gap: 15, impact: 3.8, effort: "medium", priority_score: 1.9, recommended_actions: ["리스크 관리 프로세스 고도화"] },
    ],
    regulatory_deadlines: [
      { name: "ISSB (IFRS S1/S2) 발효", date: "2025-01-01", description: "글로벌 지속가능성 공시 기준 발효", source: "ISSB" },
      { name: "EU CBAM 본격 시행", date: "2026-01-01", description: "EU 탄소국경조정제도 본격 시행", source: "EU Commission" },
    ],
  },
  issb: {
    framework: "issb",
    framework_name: "ISSB (IFRS S2)",
    overall_score: 82.8,
    compliance_level: "우수",
    categories: [
      { category: "거버넌스", score: 75, max_score: 100, status: "양호" },
      { category: "전략", score: 90, max_score: 100, status: "우수" },
      { category: "리스크 관리", score: 85, max_score: 100, status: "우수" },
      { category: "지표 및 목표", score: 80, max_score: 100, status: "우수" },
    ],
    checklist: [
      { item: "기후 관련 리스크 및 기회의 거버넌스 공시", status: "partial", recommendation: "" },
      { item: "Scope 1, 2 온실가스 배출량 공시", status: "compliant", recommendation: "" },
      { item: "Scope 3 온실가스 배출량 공시", status: "partial", recommendation: "카테고리별 Scope 3 배출량 산정 범위를 확대하세요" },
      { item: "기후 시나리오 분석 수행", status: "compliant", recommendation: "" },
      { item: "전환 계획 공시", status: "non_compliant", recommendation: "Net Zero 전환 로드맵 수립이 필요합니다" },
      { item: "기후 관련 재무 영향 정량화", status: "compliant", recommendation: "" },
      { item: "내부 탄소가격 적용", status: "partial", recommendation: "의사결정에 내부 탄소가격($50-100/tCO2e)을 적용하세요" },
      { item: "기후 리스크 관리 프로세스 통합", status: "partial", recommendation: "전사 리스크 관리(ERM)에 기후 리스크를 통합하세요" },
    ],
    recommendations: [
      "카테고리별 Scope 3 배출량 산정 범위를 확대하세요",
      "Net Zero 전환 로드맵 수립이 필요합니다",
      "의사결정에 내부 탄소가격($50-100/tCO2e)을 적용하세요",
      "전사 리스크 관리(ERM)에 기후 리스크를 통합하세요",
    ],
    maturity_level: { level: 4, name: "관리", description: "체계적 기후 리스크 관리 및 측정 수행" },
    gap_analysis: [
      { category: "지표 및 목표", current_score: 80, target_score: 100, gap: 20, impact: 6.0, effort: "low", priority_score: 6.0, recommended_actions: ["목표 달성 이행 모니터링 강화"] },
      { category: "거버넌스", current_score: 75, target_score: 100, gap: 25, impact: 5.0, effort: "medium", priority_score: 2.5, recommended_actions: ["기후 리스크 감독 프로세스 고도화"] },
      { category: "리스크 관리", current_score: 85, target_score: 100, gap: 15, impact: 3.8, effort: "medium", priority_score: 1.9, recommended_actions: ["리스크 관리 프로세스 고도화"] },
    ],
    regulatory_deadlines: [
      { name: "ISSB (IFRS S1/S2) 발효", date: "2025-01-01", description: "글로벌 지속가능성 공시 기준 발효", source: "ISSB" },
      { name: "EU CBAM 본격 시행", date: "2026-01-01", description: "EU 탄소국경조정제도 본격 시행", source: "EU Commission" },
    ],
  },
  kssb: {
    framework: "kssb",
    framework_name: "KSSB (한국 지속가능성 기준위원회)",
    overall_score: 83.0,
    compliance_level: "우수",
    categories: [
      { category: "거버넌스", score: 75, max_score: 100, status: "양호" },
      { category: "전략", score: 90, max_score: 100, status: "우수" },
      { category: "리스크 관리", score: 85, max_score: 100, status: "우수" },
      { category: "지표 및 목표", score: 80, max_score: 100, status: "우수" },
      { category: "산업별 공시", score: 85, max_score: 100, status: "우수" },
    ],
    checklist: [
      { item: "기후 관련 거버넌스 공시 (KSSB 제1호)", status: "partial", recommendation: "한국 지속가능성 공시기준에 맞춘 거버넌스 체계 수립" },
      { item: "기후 시나리오 분석 (한국 맥락)", status: "compliant", recommendation: "" },
      { item: "K-ETS 배출권거래제 영향 분석", status: "compliant", recommendation: "" },
      { item: "Scope 1/2/3 배출량 (한국 MRV 기준)", status: "partial", recommendation: "환경부 MRV 가이드라인에 맞춘 배출량 검증 필요" },
      { item: "2030 NDC 감축 목표 연계", status: "non_compliant", recommendation: "2030 NDC 40% 감축 목표와의 정합성 분석이 필요합니다" },
      { item: "산업별 추가 공시 항목", status: "non_compliant", recommendation: "해당 산업의 추가 공시 요구사항을 확인하세요" },
      { item: "기후 적응 전략", status: "partial", recommendation: "물리적 리스크 대응 적응 전략 수립을 권고합니다" },
    ],
    recommendations: [
      "한국 지속가능성 공시기준에 맞춘 거버넌스 체계 수립",
      "환경부 MRV 가이드라인에 맞춘 배출량 검증 필요",
      "2030 NDC 40% 감축 목표와의 정합성 분석이 필요합니다",
      "해당 산업의 추가 공시 요구사항을 확인하세요",
      "물리적 리스크 대응 적응 전략 수립을 권고합니다",
    ],
    maturity_level: { level: 4, name: "관리", description: "체계적 기후 리스크 관리 및 측정 수행" },
    gap_analysis: [
      { category: "지표 및 목표", current_score: 80, target_score: 100, gap: 20, impact: 5.0, effort: "low", priority_score: 5.0, recommended_actions: ["목표 달성 이행 모니터링 강화"] },
      { category: "거버넌스", current_score: 75, target_score: 100, gap: 25, impact: 5.0, effort: "medium", priority_score: 2.5, recommended_actions: ["기후 리스크 감독 프로세스 고도화"] },
      { category: "리스크 관리", current_score: 85, target_score: 100, gap: 15, impact: 3.0, effort: "medium", priority_score: 1.5, recommended_actions: ["리스크 관리 프로세스 고도화"] },
      { category: "산업별 공시", current_score: 85, target_score: 100, gap: 15, impact: 1.5, effort: "high", priority_score: 0.5, recommended_actions: ["산업별 공시 항목 완성도 제고"] },
    ],
    regulatory_deadlines: [
      { name: "KSSB 의무 공시", date: "2025-01-01", description: "자산 2조원 이상 상장사 의무 공시", source: "금융위원회 ESG 공시 로드맵" },
      { name: "K-ETS 4기", date: "2026-01-01", description: "배출권거래제 4기 시행 (강화된 할당)", source: "환경부" },
      { name: "KSSB 전면 적용", date: "2027-01-01", description: "전 상장사 의무 공시 확대", source: "금융위원회" },
    ],
  },
};

export const disclosureData: Record<string, object> = {
  tcfd: {
    framework: "tcfd",
    company_name: "K-Holdings Group (Sample)",
    assessment_date: "2026-02-18",
    metrics: {
      emissions: { scope1_tco2e: 159950000, scope2_tco2e: 47280000, scope3_tco2e: 141900000, total_tco2e: 349130000, intensity_tco2e_per_revenue: 337.78 },
      financial_impact: { transition_risk_npv_net_zero: -114744876590, total_facilities: 17, total_assets_at_risk: 359000000000 },
      targets: { base_year: 2024, target_year: 2030, reduction_target_pct: 40, science_based: true },
    },
    narrative_sections: {
      governance: "기후 리스크는 이사회 산하 ESG 위원회에서 분기별 검토하며, 최고지속가능경영책임자(CSO)가 일상 관리를 담당합니다.",
      strategy: "NGFS 4개 시나리오 분석 결과, Net Zero 2050 시나리오에서 전환 비용 NPV는 약 114.7십억 달러로 산정됩니다. 주요 리스크 요인은 배출권 비용 증가와 에너지 전환 투자 부담입니다.",
      risk_management: "기후 리스크를 전사 리스크 관리(ERM) 프레임워크에 통합하여 관리하고 있으며, 시나리오 분석을 통해 재무 영향을 정기적으로 평가합니다.",
      metrics_and_targets: "Scope 1+2 배출량 207.2백만 tCO2e, Scope 3 배출량 141.9백만 tCO2e. 2030년까지 Scope 1+2 40% 감축 목표 설정.",
    },
  },
  issb: {
    framework: "issb",
    company_name: "K-Holdings Group (Sample)",
    assessment_date: "2026-02-18",
    metrics: {
      emissions: { scope1_tco2e: 159950000, scope2_tco2e: 47280000, scope3_tco2e: 141900000, total_tco2e: 349130000, intensity_tco2e_per_revenue: 337.78 },
      financial_impact: { transition_risk_npv_net_zero: -114744876590, total_facilities: 17, total_assets_at_risk: 359000000000 },
      targets: { base_year: 2024, target_year: 2030, reduction_target_pct: 40, science_based: true },
    },
    narrative_sections: {
      governance: "기후 리스크는 이사회 산하 ESG 위원회에서 분기별 검토하며, 최고지속가능경영책임자(CSO)가 일상 관리를 담당합니다.",
      strategy: "NGFS 4개 시나리오 분석 결과, Net Zero 2050 시나리오에서 전환 비용 NPV는 약 114.7십억 달러로 산정됩니다. 주요 리스크 요인은 배출권 비용 증가와 에너지 전환 투자 부담입니다.",
      risk_management: "기후 리스크를 전사 리스크 관리(ERM) 프레임워크에 통합하여 관리하고 있으며, 시나리오 분석을 통해 재무 영향을 정기적으로 평가합니다.",
      metrics_and_targets: "Scope 1+2 배출량 207.2백만 tCO2e, Scope 3 배출량 141.9백만 tCO2e. 2030년까지 Scope 1+2 40% 감축 목표 설정.",
    },
  },
  kssb: {
    framework: "kssb",
    company_name: "K-Holdings Group (Sample)",
    assessment_date: "2026-02-18",
    metrics: {
      emissions: { scope1_tco2e: 159950000, scope2_tco2e: 47280000, scope3_tco2e: 141900000, total_tco2e: 349130000, intensity_tco2e_per_revenue: 337.78 },
      financial_impact: { transition_risk_npv_net_zero: -114744876590, total_facilities: 17, total_assets_at_risk: 359000000000 },
      targets: { base_year: 2024, target_year: 2030, reduction_target_pct: 40, science_based: true },
    },
    narrative_sections: {
      governance: "기후 리스크는 이사회 산하 ESG 위원회에서 분기별 검토하며, 최고지속가능경영책임자(CSO)가 일상 관리를 담당합니다.",
      strategy: "NGFS 4개 시나리오 분석 결과, Net Zero 2050 시나리오에서 전환 비용 NPV는 약 114.7십억 달러로 산정됩니다. 주요 리스크 요인은 배출권 비용 증가와 에너지 전환 투자 부담입니다.",
      risk_management: "기후 리스크를 전사 리스크 관리(ERM) 프레임워크에 통합하여 관리하고 있으며, 시나리오 분석을 통해 재무 영향을 정기적으로 평가합니다.",
      metrics_and_targets: "Scope 1+2 배출량 207.2백만 tCO2e, Scope 3 배출량 141.9백만 tCO2e. 2030년까지 Scope 1+2 40% 감축 목표 설정.",
    },
  },
};
