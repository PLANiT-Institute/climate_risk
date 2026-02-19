"""Page 6: Disclosure Report — assembles all analysis into framework structure.

Sections: Governance / Strategy / Risk Management / Metrics & Targets
Per-section: requirement checklist + analysis results.
CSV download at the bottom.
"""

import io
import streamlit as st
import pandas as pd
from datetime import date, datetime

from utils.helpers import (
    format_currency, format_emissions, compliance_icon,
    SCENARIO_NAMES, COMPANY_NAMES_KR, SECTOR_NAMES_KR,
)
from utils.company_data import (
    get_cached_transition, get_cached_physical, get_cached_esg,
    get_cached_disclosure, filter_transition_by_company,
    filter_physical_by_company,
)

from app.data.sample_facilities import get_company_summary, get_facilities_by_company

st.set_page_config(page_title="공시 보고서", page_icon="📑", layout="wide")

# ── Read global sidebar state ──
company = st.session_state.get("global_company", "K-Steel Corp")
scenario_id = st.session_state.get("global_scenario", "net_zero_2050")
pricing_regime = st.session_state.get("global_pricing", "kets")
year = st.session_state.get("global_year", 2030)

company_kr = COMPANY_NAMES_KR.get(company, company)

st.title("공시 보고서")
st.caption(f"{company_kr}")

# ── Framework selector (page-local) ──
framework_id = st.selectbox(
    "공시 프레임워크",
    options=["tcfd", "issb", "kssb"],
    format_func=lambda x: {"tcfd": "TCFD", "issb": "ISSB (IFRS S2)", "kssb": "KSSB"}[x],
)

st.divider()

# ── Load data ──
summary = get_company_summary(company)
assessment = get_cached_esg(framework_id)
disclosure = get_cached_disclosure(framework_id)

tr_full = get_cached_transition(scenario_id, pricing_regime)
tr = filter_transition_by_company(tr_full, company)

pr_full = get_cached_physical(scenario_id, year)
pr = filter_physical_by_company(pr_full, company)

checklist = assessment["checklist"]
metrics = disclosure["metrics"]

_STATUS_KR = {"compliant": "충족", "partial": "부분충족", "non_compliant": "미충족"}
_FW_NAMES = {"tcfd": "TCFD", "issb": "ISSB (IFRS S2)", "kssb": "KSSB"}

# ── Header ──
st.markdown(f"### {_FW_NAMES[framework_id]} 공시 보고서")
col_h1, col_h2, col_h3 = st.columns(3)
with col_h1:
    st.markdown(f"**기업명:** {company_kr}")
with col_h2:
    st.markdown(f"**평가일:** {date.today().isoformat()}")
with col_h3:
    scenario_label = SCENARIO_NAMES.get(scenario_id, scenario_id)
    regime_label = "K-ETS" if pricing_regime == "kets" else "글로벌"
    st.markdown(f"**시나리오:** {scenario_label} ({regime_label})")

st.divider()

# ── Category mapping for checklist items ──
_CATEGORY_MAP = {
    "tcfd": {
        "거버넌스": [0, 1],      # indices into checklist
        "전략": [2, 3, 4],
        "리스크 관리": [5],
        "지표 및 목표": [6, 7, 8],
    },
    "issb": {
        "거버넌스": [0],
        "전략": [3, 4, 5],
        "리스크 관리": [6, 7],
        "지표 및 목표": [1, 2],
    },
    "kssb": {
        "거버넌스": [0],
        "전략": [1, 2],
        "리스크 관리": [6],
        "지표 및 목표": [3, 4, 5],
    },
}

cat_map = _CATEGORY_MAP.get(framework_id, {})


def _render_checklist_items(category: str):
    """Render checklist items for a given category."""
    indices = cat_map.get(category, [])
    for i in indices:
        if i < len(checklist):
            item = checklist[i]
            icon = compliance_icon(item["status"])
            status_kr = _STATUS_KR.get(item["status"], "?")
            st.markdown(f"  {icon} **{item['item']}** — {status_kr}")
            if item["recommendation"]:
                st.caption(f"    → {item['recommendation']}")


# ── 1. Governance ──
st.markdown("---")
st.markdown("## 1. 거버넌스")
_render_checklist_items("거버넌스")
st.markdown("")
st.info(
    "기후 리스크는 이사회 산하 ESG 위원회에서 분기별 검토하며, "
    "최고지속가능경영책임자(CSO)가 일상 관리를 담당합니다."
)

# ── 2. Strategy ──
st.markdown("---")
st.markdown("## 2. 전략")
_render_checklist_items("전략")
st.markdown("")

st.markdown("#### 시나리오 분석 결과")
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.metric("전환 리스크 NPV", format_currency(tr["total_npv"]))
with col_s2:
    high = sum(1 for f in tr["facilities"] if f["risk_level"] == "High")
    st.metric("고위험 시설", f"{high}개 / {len(tr['facilities'])}개")
with col_s3:
    st.metric("평가 시나리오", scenario_label)

# Facility NPV table
if tr["facilities"]:
    st.markdown("**시설별 재무 영향:**")
    df_strat = pd.DataFrame([{
        "시설명": f["facility_name"],
        "섹터": f["sector"],
        "Delta NPV (USD)": format_currency(f["delta_npv"]),
        "NPV/자산 (%)": f"{f['npv_as_pct_of_assets']:.1f}%",
        "위험등급": f["risk_level"],
    } for f in sorted(tr["facilities"], key=lambda x: x["delta_npv"])])
    st.dataframe(df_strat, use_container_width=True, hide_index=True)

# ── 3. Risk Management ──
st.markdown("---")
st.markdown("## 3. 리스크 관리")
_render_checklist_items("리스크 관리")
st.markdown("")

st.markdown("#### 물리적 리스크 요약")
total_eal = sum(f["total_expected_annual_loss"] for f in pr["facilities"])
risk_summary = pr["overall_risk_summary"]

col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    st.metric("총 EAL", format_currency(total_eal))
with col_r2:
    st.metric("고위험 시설", f'{risk_summary.get("High", 0)}개')
with col_r3:
    st.metric("평가연도", f"{year}년")

st.markdown("#### 전환 리스크 비용 구조")
# Aggregate cost categories across company facilities
cost_categories = {}
for fac in tr["facilities"]:
    for imp in fac.get("annual_impacts", []):
        for key in ["carbon_cost", "energy_cost_increase", "revenue_impact",
                     "transition_opex", "stranded_asset_writedown", "scope3_impact"]:
            cost_categories[key] = cost_categories.get(key, 0) + imp.get(key, 0)

cost_labels = {
    "carbon_cost": "탄소비용",
    "energy_cost_increase": "에너지비용 증가",
    "revenue_impact": "매출영향",
    "transition_opex": "전환 OPEX",
    "stranded_asset_writedown": "좌초자산",
    "scope3_impact": "Scope 3",
}
if cost_categories:
    df_costs = pd.DataFrame([{
        "비용 항목": cost_labels.get(k, k),
        "누적 총액 (USD)": format_currency(v),
    } for k, v in cost_categories.items() if v != 0])
    st.dataframe(df_costs, use_container_width=True, hide_index=True)

# ── 4. Metrics & Targets ──
st.markdown("---")
st.markdown("## 4. 지표 및 목표")
_render_checklist_items("지표 및 목표")
st.markdown("")

st.markdown("#### 배출량 현황")
em = metrics["emissions"]
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Scope 1", format_emissions(em["scope1_tco2e"]))
with col_m2:
    st.metric("Scope 2", format_emissions(em["scope2_tco2e"]))
with col_m3:
    st.metric("Scope 3", format_emissions(em["scope3_tco2e"]))
with col_m4:
    st.metric("배출 원단위", f'{em["intensity_tco2e_per_revenue"]:.1f} tCO2e/$M')

st.markdown("#### 감축 목표")
tgt = metrics["targets"]
col_t1, col_t2, col_t3 = st.columns(3)
with col_t1:
    st.metric("기준연도 → 목표연도", f"{tgt['base_year']} → {tgt['target_year']}")
with col_t2:
    st.metric("감축 목표", f"{tgt['reduction_target_pct']}%")
with col_t3:
    st.metric("SBTi 기반", "예" if tgt["science_based"] else "아니오")

if pricing_regime == "kets":
    st.markdown("#### K-ETS 할당 현황")
    st.info("K-ETS 무상할당 초과분에 대해서만 탄소비용이 부과됩니다. "
            "무상할당 비율은 업종별로 차등 적용되며 매년 축소됩니다.")

# ── Regulatory Deadlines ──
st.markdown("---")
st.markdown("## 규제 일정")
deadlines = assessment.get("regulatory_deadlines", [])
if deadlines:
    for dl in deadlines:
        try:
            dl_date = datetime.strptime(dl["date"], "%Y-%m-%d").date()
            days_left = (dl_date - date.today()).days
            badge = f"**D+{abs(days_left)}** (경과)" if days_left < 0 else f"**D-{days_left}**"
        except (ValueError, KeyError):
            badge = "N/A"
        st.markdown(f"- {badge} — **{dl['name']}** ({dl['date']})")
        st.caption(f"  {dl['description']}")

# ── CSV Download ──
st.markdown("---")
st.markdown("## 데이터 다운로드")

# Build comprehensive CSV
rows = []
for fac in tr["facilities"]:
    fac_pr = next(
        (f for f in pr["facilities"] if f["facility_id"] == fac.get("facility_id")),
        {},
    )
    rows.append({
        "기업": company,
        "시설명": fac["facility_name"],
        "섹터": fac["sector"],
        "시나리오": scenario_id,
        "가격체계": pricing_regime,
        "Delta NPV (USD)": fac["delta_npv"],
        "NPV/자산 (%)": fac["npv_as_pct_of_assets"],
        "전환 위험등급": fac["risk_level"],
        "총 EAL (USD)": fac_pr.get("total_expected_annual_loss", ""),
        "물리적 위험등급": fac_pr.get("overall_risk_level", ""),
    })

df_download = pd.DataFrame(rows)
csv_buffer = io.StringIO()
df_download.to_csv(csv_buffer, index=False, encoding="utf-8-sig")

st.download_button(
    label="CSV 다운로드 (전체 분석 데이터)",
    data=csv_buffer.getvalue(),
    file_name=f"climate_disclosure_{company}_{scenario_id}.csv",
    mime="text/csv",
)
