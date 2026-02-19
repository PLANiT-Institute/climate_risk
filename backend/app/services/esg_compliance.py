"""ESG compliance service – data-driven scoring with CDP-inspired methodology.

Upgraded from hardcoded scores to dynamic computation based on:
- Actual facility data availability
- Model analysis state (physical/transition risk results)
- 5-level maturity model
- Gap analysis with impact×effort prioritization
- Regulatory deadline tracking

References:
- CDP Scoring Methodology (2023)
- ISSB (IFRS S2) Disclosure Requirements
- TCFD Final Report (2017) + Status Report (2023)
- KSSB (한국 지속가능성 기준위원회) Draft Standards (2024)
"""

from datetime import date
from typing import Dict, List, Optional

from ..core.config import REGULATORY_DEADLINES
from ..data.sample_facilities import get_all_facilities
from ..services.transition_risk import analyse_scenario

# ── Framework definitions ────────────────────────────────────────────
_FRAMEWORKS = {
    "issb": {
        "name": "ISSB (IFRS S2)",
        "categories": [
            {"category": "거버넌스", "weight": 0.20},
            {"category": "전략", "weight": 0.25},
            {"category": "리스크 관리", "weight": 0.25},
            {"category": "지표 및 목표", "weight": 0.30},
        ],
    },
    "tcfd": {
        "name": "TCFD",
        "categories": [
            {"category": "거버넌스", "weight": 0.25},
            {"category": "전략", "weight": 0.25},
            {"category": "리스크 관리", "weight": 0.25},
            {"category": "지표 및 목표", "weight": 0.25},
        ],
    },
    "kssb": {
        "name": "KSSB (한국 지속가능성 기준위원회)",
        "categories": [
            {"category": "거버넌스", "weight": 0.20},
            {"category": "전략", "weight": 0.25},
            {"category": "리스크 관리", "weight": 0.20},
            {"category": "지표 및 목표", "weight": 0.25},
            {"category": "산업별 공시", "weight": 0.10},
        ],
    },
}


# ── Data-Driven Score Computation ────────────────────────────────────
def _compute_data_driven_scores(framework_id: str) -> Dict[str, float]:
    """Compute category scores based on actual data availability and model state.

    Inspired by CDP Scoring Methodology (2023):
    - Each category has specific criteria
    - Score depends on what data/analysis is actually available
    - Not hardcoded; reflects the real state of the platform

    IMPORTANT LIMITATION: These scores measure the analytical capabilities
    of this platform (multi-scenario analysis, risk quantification, data
    coverage), NOT the organization's actual governance structure (board
    committees, ESG expertise, management integration). A formal TCFD/ISSB
    assessment would additionally require evidence of:
    - Board-level climate risk oversight committee
    - Management accountability and expertise
    - Integration with enterprise risk management (ERM)
    - External assurance of reported data
    Scores should be interpreted as "analytical readiness" rather than
    full regulatory compliance scores.

    Returns:
        {category_name: score (0-100)}
    """
    facilities = get_all_facilities()

    # Check data availability
    has_scope1 = all(f["current_emissions_scope1"] > 0 for f in facilities)
    has_scope2 = all(f["current_emissions_scope2"] > 0 for f in facilities)
    has_scope3 = all(f["current_emissions_scope3"] > 0 for f in facilities)
    has_revenue = all(f["annual_revenue"] > 0 for f in facilities)
    has_assets = all(f["assets_value"] > 0 for f in facilities)
    total_facilities = len(facilities)

    # Check if transition analysis is available (analytical model)
    try:
        nz_result = analyse_scenario("net_zero_2050")
        has_transition_analysis = nz_result["total_npv"] != 0
        has_multi_scenario = True
    except Exception:
        has_transition_analysis = False
        has_multi_scenario = False

    # Physical risk model state
    from ..services.physical_risk import assess_physical_risk
    try:
        pr = assess_physical_risk()
        has_physical_model = pr.get("model_status") == "analytical_v1"
    except Exception:
        has_physical_model = False

    # ── Governance Score ──
    # NOTE: Governance score reflects analytical infrastructure readiness,
    # not board-level governance structure (see docstring limitation).
    governance = 0
    if has_multi_scenario:
        governance += 25   # Scenario analysis capability supports governance oversight
    if has_transition_analysis:
        governance += 25   # Internal carbon pricing / financial impact quantification
    if total_facilities >= 5:
        governance += 15   # Multi-facility monitoring (organizational breadth)
    # No explicit board committee data → partial (capped below full score)
    governance += 10       # Platform existence = basic climate risk awareness
    governance = min(100, governance)

    # ── Strategy Score ──
    strategy = 0
    if has_transition_analysis:
        strategy += 30     # Transition risk NPV quantification
    if has_multi_scenario:
        strategy += 20     # 4-scenario analysis (NGFS framework)
    if has_physical_model:
        strategy += 25     # Physical risk quantification
    if has_revenue and has_assets:
        strategy += 15     # Financial impact metrics available
    # No formal adaptation strategy documented → gap
    strategy = min(100, strategy)

    # ── Risk Management Score ──
    risk_mgmt = 0
    if has_physical_model:
        risk_mgmt += 30    # Physical risk EAL computation
    if has_transition_analysis:
        risk_mgmt += 30    # Transition risk NPV computation
    if has_multi_scenario:
        risk_mgmt += 20    # Integrated multi-scenario view
    # No explicit ERM integration documentation → gap
    risk_mgmt += 5         # Basic risk identification
    risk_mgmt = min(100, risk_mgmt)

    # ── Metrics & Targets Score ──
    metrics = 0
    if has_scope1:
        metrics += 20      # Scope 1 quantified
    if has_scope2:
        metrics += 20      # Scope 2 quantified
    if has_scope3:
        metrics += 15      # Scope 3 estimated (partially)
    if has_revenue:
        metrics += 10      # Intensity metrics possible
    if has_transition_analysis:
        metrics += 10      # Reduction pathway exists
    # SBTi target not formally set → gap
    metrics += 5           # Basic target awareness (2030 NDC)
    metrics = min(100, metrics)

    # ── Industry-Specific Disclosure (KSSB only) ──
    industry = 0
    sectors_covered = set(f["sector"] for f in facilities)
    if len(sectors_covered) >= 3:
        industry += 30     # Multi-sector coverage
    if has_scope1 and has_scope2:
        industry += 25     # MRV-ready emissions data
    if has_transition_analysis:
        industry += 20     # Sector transition analysis
    # K-ETS specific reporting gap
    industry += 10
    industry = min(100, industry)

    return {
        "거버넌스": governance,
        "전략": strategy,
        "리스크 관리": risk_mgmt,
        "지표 및 목표": metrics,
        "산업별 공시": industry,
    }


# ── Dynamic Checklist Evaluation ─────────────────────────────────────
def _evaluate_checklist(framework_id: str) -> List[dict]:
    """Evaluate compliance checklist dynamically based on actual data state.

    Each item is evaluated against real conditions, not hardcoded.
    """
    facilities = get_all_facilities()

    has_scope1 = all(f["current_emissions_scope1"] > 0 for f in facilities)
    has_scope2 = all(f["current_emissions_scope2"] > 0 for f in facilities)
    has_scope3 = all(f["current_emissions_scope3"] > 0 for f in facilities)

    try:
        nz = analyse_scenario("net_zero_2050")
        has_transition = nz["total_npv"] != 0
    except Exception:
        has_transition = False

    from ..services.physical_risk import assess_physical_risk
    try:
        pr = assess_physical_risk()
        has_physical = pr.get("model_status") == "analytical_v1"
    except Exception:
        has_physical = False

    checklists = {
        "issb": [
            {
                "item": "기후 관련 리스크 및 기회의 거버넌스 공시",
                "status": "partial" if has_transition else "non_compliant",
                "recommendation": "" if has_transition else "이사회 수준의 기후 리스크 감독 체계를 공식화하세요",
            },
            {
                "item": "Scope 1, 2 온실가스 배출량 공시",
                "status": "compliant" if (has_scope1 and has_scope2) else "non_compliant",
                "recommendation": "" if (has_scope1 and has_scope2) else "Scope 1, 2 배출량 산정이 필요합니다",
            },
            {
                "item": "Scope 3 온실가스 배출량 공시",
                "status": "partial" if has_scope3 else "non_compliant",
                "recommendation": "카테고리별 Scope 3 배출량 산정 범위를 확대하세요" if has_scope3 else "Scope 3 배출량 산정이 필요합니다",
            },
            {
                "item": "기후 시나리오 분석 수행",
                "status": "compliant" if has_transition else "non_compliant",
                "recommendation": "" if has_transition else "NGFS 시나리오 기반 분석이 필요합니다",
            },
            {
                "item": "전환 계획 공시",
                "status": "non_compliant",
                "recommendation": "Net Zero 전환 로드맵 수립이 필요합니다",
            },
            {
                "item": "기후 관련 재무 영향 정량화",
                "status": "compliant" if (has_transition and has_physical) else "partial",
                "recommendation": "" if (has_transition and has_physical) else "물리적 리스크와 전환 리스크의 재무 영향 정량화를 완성하세요",
            },
            {
                "item": "내부 탄소가격 적용",
                "status": "partial" if has_transition else "non_compliant",
                "recommendation": "의사결정에 내부 탄소가격($50-100/tCO2e)을 적용하세요",
            },
            {
                "item": "기후 리스크 관리 프로세스 통합",
                "status": "partial",
                "recommendation": "전사 리스크 관리(ERM)에 기후 리스크를 통합하세요",
            },
        ],
        "tcfd": [
            {
                "item": "이사회의 기후 리스크 감독 체계",
                "status": "partial",
                "recommendation": "기후 전담 위원회 설치를 권고합니다",
            },
            {
                "item": "경영진의 기후 리스크 평가/관리 역할",
                "status": "compliant" if has_transition else "partial",
                "recommendation": "" if has_transition else "경영진의 기후 리스크 관리 역할을 명확히 하세요",
            },
            {
                "item": "기후 리스크/기회 식별",
                "status": "compliant" if (has_transition or has_physical) else "non_compliant",
                "recommendation": "",
            },
            {
                "item": "시나리오 분석(2°C 이하 포함)",
                "status": "compliant" if has_transition else "non_compliant",
                "recommendation": "" if has_transition else "2°C 이하 시나리오 분석이 필요합니다",
            },
            {
                "item": "비즈니스 전략 영향 분석",
                "status": "compliant" if has_transition else "partial",
                "recommendation": "" if has_transition else "정량적 재무 영향 분석을 강화하세요",
            },
            {
                "item": "리스크 식별 및 평가 프로세스",
                "status": "compliant" if has_physical else "partial",
                "recommendation": "" if has_physical else "체계적 리스크 평가 프로세스를 구축하세요",
            },
            {
                "item": "Scope 1/2 배출량 공시",
                "status": "compliant" if (has_scope1 and has_scope2) else "non_compliant",
                "recommendation": "",
            },
            {
                "item": "Scope 3 배출량 공시",
                "status": "partial" if has_scope3 else "non_compliant",
                "recommendation": "주요 카테고리 Scope 3 배출량을 공시하세요",
            },
            {
                "item": "기후 관련 목표 설정",
                "status": "partial",
                "recommendation": "SBTi 인증 목표 설정을 권고합니다",
            },
        ],
        "kssb": [
            {
                "item": "기후 관련 거버넌스 공시 (KSSB 제1호)",
                "status": "partial",
                "recommendation": "한국 지속가능성 공시기준에 맞춘 거버넌스 체계 수립",
            },
            {
                "item": "기후 시나리오 분석 (한국 맥락)",
                "status": "compliant" if has_transition else "non_compliant",
                "recommendation": "" if has_transition else "한국 맥락의 기후 시나리오 분석이 필요합니다",
            },
            {
                "item": "K-ETS 배출권거래제 영향 분석",
                "status": "compliant" if has_transition else "non_compliant",
                "recommendation": "" if has_transition else "K-ETS 영향 분석이 필요합니다",
            },
            {
                "item": "Scope 1/2/3 배출량 (한국 MRV 기준)",
                "status": "partial" if (has_scope1 and has_scope2) else "non_compliant",
                "recommendation": "환경부 MRV 가이드라인에 맞춘 배출량 검증 필요",
            },
            {
                "item": "2030 NDC 감축 목표 연계",
                "status": "non_compliant",
                "recommendation": "2030 NDC 40% 감축 목표와의 정합성 분석이 필요합니다",
            },
            {
                "item": "산업별 추가 공시 항목",
                "status": "non_compliant",
                "recommendation": "해당 산업의 추가 공시 요구사항을 확인하세요",
            },
            {
                "item": "기후 적응 전략",
                "status": "partial" if has_physical else "non_compliant",
                "recommendation": "물리적 리스크 대응 적응 전략 수립을 권고합니다",
            },
        ],
    }

    return checklists.get(framework_id, [])


# ── Maturity Level ──────────────────────────────────────────────────
def _maturity_level(score: float) -> dict:
    """5-level maturity model assessment.

    Level 1 (0-30): 인식 - Basic awareness
    Level 2 (31-50): 기초 - Foundation building
    Level 3 (51-70): 개발 - Developing capabilities
    Level 4 (71-85): 관리 - Managed and measured
    Level 5 (86-100): 선도 - Leading practice
    """
    if score >= 86:
        return {"level": 5, "name": "선도", "description": "업계 선도적 기후 리스크 관리 체계 구축"}
    if score >= 71:
        return {"level": 4, "name": "관리", "description": "체계적 기후 리스크 관리 및 측정 수행"}
    if score >= 51:
        return {"level": 3, "name": "개발", "description": "기후 리스크 관리 역량 개발 중"}
    if score >= 31:
        return {"level": 2, "name": "기초", "description": "기초적 기후 리스크 관리 체계 구축 중"}
    return {"level": 1, "name": "인식", "description": "기후 리스크에 대한 기본적 인식 단계"}


# ── Gap Analysis ────────────────────────────────────────────────────
def _gap_analysis(framework_id: str, scores: Dict[str, float]) -> List[dict]:
    """Prioritized gap analysis with impact × effort matrix.

    Returns gaps sorted by priority (high impact, low effort first).
    """
    fw = _FRAMEWORKS[framework_id]
    gaps = []

    for cat in fw["categories"]:
        category = cat["category"]
        score = scores.get(category, 50)
        weight = cat["weight"]
        gap = 100 - score

        if gap <= 10:
            continue  # Near-complete, no significant gap

        # Impact = gap size × category weight
        impact = gap * weight

        # Effort estimation based on category
        effort_map = {
            "거버넌스": "medium",     # Organizational change needed
            "전략": "high",           # Strategic planning required
            "리스크 관리": "medium",   # Process development
            "지표 및 목표": "low",     # Data collection (platform assists)
            "산업별 공시": "high",     # Industry-specific research
        }
        effort = effort_map.get(category, "medium")

        # Priority: high impact + low effort = highest priority
        effort_score = {"low": 1, "medium": 2, "high": 3}[effort]
        priority_score = impact / effort_score

        actions = _get_gap_actions(category, score)

        gaps.append({
            "category": category,
            "current_score": score,
            "target_score": 100,
            "gap": gap,
            "impact": round(impact, 1),
            "effort": effort,
            "priority_score": round(priority_score, 1),
            "recommended_actions": actions,
        })

    # Sort by priority (highest first)
    gaps.sort(key=lambda x: x["priority_score"], reverse=True)
    return gaps


def _get_gap_actions(category: str, score: float) -> List[str]:
    """Get specific recommended actions based on category and score level."""
    actions_map = {
        "거버넌스": {
            "low": [
                "이사회 내 기후 리스크 전담 위원회 설치",
                "최고지속가능경영책임자(CSO) 임명",
                "기후 리스크 정기 보고 체계 수립",
            ],
            "high": [
                "기후 리스크 감독 프로세스 고도화",
            ],
        },
        "전략": {
            "low": [
                "NGFS 4개 시나리오 기반 전략적 영향 분석",
                "기후 적응 전략 수립",
                "전환 계획(Transition Plan) 공식화",
            ],
            "high": [
                "시나리오별 재무 영향 정량화 고도화",
            ],
        },
        "리스크 관리": {
            "low": [
                "물리적 리스크 평가 체계 구축",
                "전사 리스크 관리(ERM)에 기후 리스크 통합",
                "리스크 모니터링 대시보드 구축",
            ],
            "high": [
                "리스크 관리 프로세스 고도화",
            ],
        },
        "지표 및 목표": {
            "low": [
                "Scope 3 배출량 산정 범위 확대",
                "SBTi 인증 감축 목표 설정",
                "탄소 원단위 지표 개발",
            ],
            "high": [
                "목표 달성 이행 모니터링 강화",
            ],
        },
        "산업별 공시": {
            "low": [
                "해당 산업 KSSB 추가 공시 요구사항 파악",
                "산업별 핵심 성과지표(KPI) 설정",
                "2030 NDC 정합성 분석",
            ],
            "high": [
                "산업별 공시 항목 완성도 제고",
            ],
        },
    }

    level = "high" if score >= 70 else "low"
    return actions_map.get(category, {}).get(level, ["추가 분석 필요"])


# ── Compliance Level ────────────────────────────────────────────────
def _compliance_level(score: float) -> str:
    if score >= 80:
        return "우수"
    if score >= 65:
        return "양호"
    if score >= 50:
        return "보통"
    return "미흡"


# ── Public API ──────────────────────────────────────────────────────
def assess_framework(framework_id: str) -> dict:
    """Assess ESG compliance for a given framework with data-driven scoring."""
    fw = _FRAMEWORKS[framework_id]

    # Compute scores dynamically
    scores = _compute_data_driven_scores(framework_id)

    categories = []
    weighted_total = 0.0

    for cat in fw["categories"]:
        score = scores.get(cat["category"], 50)
        weighted_total += score * cat["weight"]
        status = _compliance_level(score)
        categories.append({
            "category": cat["category"],
            "score": score,
            "max_score": 100,
            "status": status,
        })

    overall = round(weighted_total, 1)
    checklist = _evaluate_checklist(framework_id)
    compliant = sum(1 for c in checklist if c["status"] == "compliant")
    total_items = len(checklist)

    recommendations = [c["recommendation"] for c in checklist if c["recommendation"]]

    # New: maturity level
    maturity = _maturity_level(overall)

    # New: gap analysis
    gaps = _gap_analysis(framework_id, scores)

    # New: regulatory deadlines
    deadlines = _get_relevant_deadlines(framework_id)

    return {
        "framework": framework_id,
        "framework_name": fw["name"],
        "overall_score": overall,
        "compliance_level": _compliance_level(overall),
        "categories": categories,
        "checklist": checklist,
        "recommendations": recommendations,
        "maturity_level": maturity,
        "gap_analysis": gaps,
        "regulatory_deadlines": deadlines,
    }


def _get_relevant_deadlines(framework_id: str) -> List[dict]:
    """Get regulatory deadlines relevant to the framework."""
    relevance_map = {
        "issb": ["issb_effective", "eu_cbam_full"],
        "tcfd": ["issb_effective", "eu_cbam_full"],
        "kssb": ["kssb_mandatory", "kets_phase4", "kssb_full_scope"],
    }
    relevant_keys = relevance_map.get(framework_id, [])
    deadlines = []
    for key in relevant_keys:
        dl = REGULATORY_DEADLINES.get(key)
        if dl:
            deadlines.append(dl)
    return deadlines


def get_disclosure_data(framework_id: str) -> dict:
    facilities = get_all_facilities()
    total_s1 = sum(f["current_emissions_scope1"] for f in facilities)
    total_s2 = sum(f["current_emissions_scope2"] for f in facilities)
    total_s3 = sum(f["current_emissions_scope3"] for f in facilities)
    total_revenue = sum(f["annual_revenue"] for f in facilities)

    # Get transition risk summary for Net Zero scenario
    try:
        nz = analyse_scenario("net_zero_2050")
        npv = nz["total_npv"]
    except Exception:
        npv = 0

    metrics = {
        "emissions": {
            "scope1_tco2e": total_s1,
            "scope2_tco2e": total_s2,
            "scope3_tco2e": total_s3,
            "total_tco2e": total_s1 + total_s2 + total_s3,
            "intensity_tco2e_per_revenue": round((total_s1 + total_s2) / total_revenue * 1_000_000, 2) if total_revenue else 0,
        },
        "financial_impact": {
            "transition_risk_npv_net_zero": npv,
            "total_facilities": len(facilities),
            "total_assets_at_risk": sum(f["assets_value"] for f in facilities),
        },
        "targets": {
            "base_year": 2024,
            "target_year": 2030,
            "reduction_target_pct": 40,
            "science_based": True,
        },
    }

    narrative = {
        "governance": "기후 리스크는 이사회 산하 ESG 위원회에서 분기별 검토하며, "
                       "최고지속가능경영책임자(CSO)가 일상 관리를 담당합니다.",
        "strategy": f"NGFS 4개 시나리오 분석 결과, Net Zero 2050 시나리오에서 전환 비용 NPV는 "
                     f"약 {abs(npv)/1e9:.1f}십억 달러로 산정됩니다. 주요 리스크 요인은 "
                     f"배출권 비용 증가와 에너지 전환 투자 부담입니다.",
        "risk_management": "기후 리스크를 전사 리스크 관리(ERM) 프레임워크에 통합하여 관리하고 있으며, "
                           "시나리오 분석을 통해 재무 영향을 정기적으로 평가합니다.",
        "metrics_and_targets": f"Scope 1+2 배출량 {(total_s1+total_s2)/1e6:.1f}백만 tCO2e, "
                               f"Scope 3 배출량 {total_s3/1e6:.1f}백만 tCO2e. "
                               f"2030년까지 Scope 1+2 40% 감축 목표 설정.",
    }

    return {
        "framework": framework_id,
        "company_name": "K-Holdings Group (Sample)",
        "assessment_date": date.today().isoformat(),
        "metrics": metrics,
        "narrative_sections": narrative,
    }
