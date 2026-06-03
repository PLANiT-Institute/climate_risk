"""Page 7: Comprehensive Dashboard — company-filtered transition + physical + ESG summary + PPT download."""

import sys
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.helpers import (
    SCENARIO_COLORS, SCENARIO_NAMES, RISK_COLORS, COMPANY_NAMES_KR,
    format_currency, format_emissions, compliance_icon, default_layout,
)
from utils.company_data import (
    get_cached_transition, get_cached_physical, get_cached_comparison,
    get_cached_esg, filter_transition_by_company,
    filter_physical_by_company, filter_comparison_by_company,
)
from app.data.sample_facilities import get_company_summary

st.set_page_config(page_title="종합 대시보드", page_icon="📊", layout="wide")

from components.sidebar import render_global_sidebar
render_global_sidebar()

# ── Read global sidebar state ──
company = st.session_state.get("global_company", "K-Steel Corp")
scenario_id = st.session_state.get("global_scenario", "net_zero_2050")
pricing_regime = st.session_state.get("global_pricing", "kets")
year = st.session_state.get("global_year", 2030)

company_kr = COMPANY_NAMES_KR.get(company, company)
regime_label = "K-ETS" if pricing_regime == "kets" else "글로벌"

st.title("종합 대시보드")
st.caption(f"{company_kr} | {SCENARIO_NAMES.get(scenario_id, scenario_id)} | {regime_label} | {year}년")

# ── Load All Data ──────────────────────────────────────────────────
with st.spinner("종합 분석 중..."):
    summary = get_company_summary(company)

    tr_full = get_cached_transition(scenario_id, pricing_regime)
    tr = filter_transition_by_company(tr_full, company)

    comp_full = get_cached_comparison(pricing_regime)
    comp = filter_comparison_by_company(comp_full, company)

    pr_full = get_cached_physical(scenario_id, year)
    pr = filter_physical_by_company(pr_full, company)

    esg_data = {fw: get_cached_esg(fw) for fw in ["tcfd", "issb", "kssb"]}

# ── Summary KPIs ──────────────────────────────────────────────────
st.subheader("핵심 지표")

total_eal = sum(f["total_expected_annual_loss"] for f in pr["facilities"])
high_phys = pr["overall_risk_summary"].get("High", 0)
high_tr = sum(1 for f in tr["facilities"] if f["risk_level"] == "High")

# ESG compliance rate
esg_compliant = 0
esg_total = 0
for fw_data in esg_data.values():
    cl = fw_data["checklist"]
    esg_compliant += sum(1 for c in cl if c["status"] == "compliant")
    esg_total += len(cl)
esg_rate = (esg_compliant / esg_total * 100) if esg_total else 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("전환 리스크 NPV", format_currency(tr["total_npv"]))
with col2:
    st.metric("물리적 리스크 EAL", format_currency(total_eal))
with col3:
    st.metric("ESG 준수율", f"{esg_rate:.0f}%")
with col4:
    st.metric("전환 고위험", f"{high_tr}개 시설")
with col5:
    st.metric("물리적 고위험", f"{high_phys}개 시설")

st.divider()

# ── Two-Column: Transition + Physical ──────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("전환 리스크 — 시나리오 비교")

    npv_comp = comp["npv_comparison"]
    fig_npv = go.Figure()
    for item in npv_comp:
        sid = item["scenario"]
        fig_npv.add_trace(go.Bar(
            x=[SCENARIO_NAMES.get(sid, sid)],
            y=[abs(item["total_npv"])],
            name=SCENARIO_NAMES.get(sid, sid),
            marker_color=SCENARIO_COLORS.get(sid, "#6b7280"),
            text=[format_currency(item["total_npv"])],
            textposition="outside",
        ))
    default_layout(fig_npv, title="시나리오별 NPV 영향", height=380)
    fig_npv.update_layout(showlegend=False)
    fig_npv.update_yaxes(title="NPV (USD)")
    st.plotly_chart(fig_npv, use_container_width=True)

    # Top 5 transition risk facilities
    st.markdown("**전환 고위험 시설 Top 5**")
    top_tr = sorted(tr["facilities"], key=lambda x: x["delta_npv"])[:5]
    if top_tr:
        df_tr = pd.DataFrame([{
            "시설명": f["facility_name"],
            "섹터": f["sector"],
            "Delta NPV": format_currency(f["delta_npv"]),
            "위험등급": f["risk_level"],
        } for f in top_tr])
        st.dataframe(df_tr, use_container_width=True, hide_index=True)

with col_right:
    st.subheader("물리적 리스크 — 재해별 EAL")

    hazard_types = ["flood", "typhoon", "heatwave", "drought", "sea_level_rise"]
    hazard_labels = {
        "flood": "홍수", "typhoon": "태풍", "heatwave": "폭염",
        "drought": "가뭄", "sea_level_rise": "해수면",
    }
    hazard_colors = ["#3b82f6", "#8b5cf6", "#ef4444", "#f59e0b", "#06b6d4"]

    agg = {ht: 0 for ht in hazard_types}
    for f in pr["facilities"]:
        for h in f["hazards"]:
            if h["hazard_type"] in agg:
                agg[h["hazard_type"]] += h["potential_loss"]

    fig_haz = go.Figure()
    fig_haz.add_trace(go.Bar(
        x=[hazard_labels.get(ht, ht) for ht in hazard_types],
        y=[agg[ht] for ht in hazard_types],
        marker_color=hazard_colors,
        text=[format_currency(agg[ht]) for ht in hazard_types],
        textposition="outside",
    ))
    default_layout(fig_haz, title="재해 유형별 총 EAL", height=380)
    fig_haz.update_yaxes(title="EAL (USD)")
    st.plotly_chart(fig_haz, use_container_width=True)

    # Top 5 physical risk facilities
    st.markdown("**물리적 고위험 시설 Top 5**")
    top_pr = sorted(pr["facilities"],
                    key=lambda x: x["total_expected_annual_loss"], reverse=True)[:5]
    if top_pr:
        df_pr = pd.DataFrame([{
            "시설명": f["facility_name"],
            "위치": f["location"],
            "총 EAL": format_currency(f["total_expected_annual_loss"]),
            "위험등급": f["overall_risk_level"],
        } for f in top_pr])
        st.dataframe(df_pr, use_container_width=True, hide_index=True)

st.divider()

# ── ESG Compliance Summary ──────────────────────────────────────────
st.subheader("ESG 준수 현황")

esg_cols = st.columns(3)
for i, (fw_id, fw_data) in enumerate(esg_data.items()):
    with esg_cols[i]:
        cl = fw_data["checklist"]
        n_c = sum(1 for c in cl if c["status"] == "compliant")
        n_p = sum(1 for c in cl if c["status"] == "partial")
        n_n = sum(1 for c in cl if c["status"] == "non_compliant")

        st.markdown(f"**{fw_data['framework_name']}**")
        st.metric("점수", f"{fw_data['overall_score']:.0f}/100")
        st.caption(f"✅ {n_c}  |  ⚠️ {n_p}  |  ❌ {n_n}  (총 {len(cl)}항목)")

st.divider()

# ── PPT Download ──────────────────────────────────────────────────
st.subheader("보고서 다운로드")

# Add project root to path for generate_ppt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from generate_ppt import generate_report

    if st.button("PPT 보고서 생성", type="primary"):
        with st.spinner("PPT 생성 중..."):
            filepath = generate_report(
                scenario_id=scenario_id,
                pricing_regime=pricing_regime,
                year=year,
            )
        with open(filepath, "rb") as f:
            st.download_button(
                label="PPT 다운로드 (.pptx)",
                data=f.read(),
                file_name="climate_risk_report.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
        st.success(f"PPT 생성 완료 (3슬라이드)")
except ImportError:
    st.warning("PPT 생성 모듈을 불러올 수 없습니다. (python-pptx 설치 확인)")
