"""
Transition Risk Analysis Page - Climate Risk Assessment Tool
Uses the backend analytical model (S-curve, NGFS scenarios, K-ETS)
"""

import sys
import os
from pathlib import Path

# Add backend to path so we can import services directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app.services.transition_risk import analyse_scenario, compare_scenarios
from app.data.sample_facilities import get_all_facilities
from app.core.config import SCENARIOS

st.set_page_config(page_title="Transition Risk", page_icon="🔄", layout="wide")

# ── Constants ─────────────────────────────────────────────────────────

SCENARIO_NAMES = {
    "net_zero_2050": "Net Zero 2050",
    "below_2c": "Below 2°C",
    "delayed_transition": "Delayed Transition",
    "current_policies": "Current Policies",
}

SCENARIO_COLORS = {
    "net_zero_2050": "#ef4444",
    "below_2c": "#f97316",
    "delayed_transition": "#eab308",
    "current_policies": "#22c55e",
}

RISK_COLORS = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}


def format_currency(value: float) -> str:
    if abs(value) >= 1e9:
        return f"${value / 1e9:,.1f}B"
    if abs(value) >= 1e6:
        return f"${value / 1e6:,.1f}M"
    return f"${value:,.0f}"


def format_emissions(value: float) -> str:
    if value >= 1e6:
        return f"{value / 1e6:,.1f}M tCO2e"
    if value >= 1e3:
        return f"{value / 1e3:,.0f}k tCO2e"
    return f"{value:,.0f} tCO2e"


# ── Sidebar Configuration ─────────────────────────────────────────────

st.sidebar.header("분석 설정")

scenario_id = st.sidebar.selectbox(
    "시나리오",
    options=list(SCENARIOS.keys()),
    format_func=lambda x: SCENARIO_NAMES.get(x, x),
    index=0,
)

pricing_regime = st.sidebar.radio(
    "탄소가격 체계",
    options=["global", "kets"],
    format_func=lambda x: "글로벌 (USD)" if x == "global" else "K-ETS (KRW)",
    index=1,
)

show_comparison = st.sidebar.checkbox("시나리오 비교 보기", value=False)

# ── Page Title ─────────────────────────────────────────────────────────

st.title("🔄 전환 리스크 분석")
st.caption(
    f"NGFS {SCENARIO_NAMES[scenario_id]} 시나리오 | "
    f"{'K-ETS' if pricing_regime == 'kets' else '글로벌'} 탄소가격 체계"
)

# ── Run Analysis ───────────────────────────────────────────────────────

with st.spinner("전환 리스크 분석 중..."):
    result = analyse_scenario(scenario_id, pricing_regime=pricing_regime)

facs = result["facilities"]

# ── Summary KPIs ───────────────────────────────────────────────────────

st.subheader("요약")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("총 NPV 영향", format_currency(result["total_npv"]))
with col2:
    high = sum(1 for f in facs if f["risk_level"] == "High")
    st.metric("고위험 시설", f"{high}개")
with col3:
    med = sum(1 for f in facs if f["risk_level"] == "Medium")
    st.metric("중위험 시설", f"{med}개")
with col4:
    st.metric("총 배출량", format_emissions(result["total_baseline_emissions"]))

if pricing_regime == "kets":
    st.info("K-ETS 모드: 무상할당 초과분에 대해서만 탄소비용이 부과됩니다.")

st.divider()

# ── Facility NPV Distribution ──────────────────────────────────────────

st.subheader("시설별 NPV 영향")

df_npv = pd.DataFrame([{
    "시설명": f["facility_name"],
    "섹터": f["sector"],
    "delta_npv": f["delta_npv"],
    "risk_level": f["risk_level"],
    "npv_pct": f["npv_as_pct_of_assets"],
} for f in facs])

fig_npv = px.bar(
    df_npv.sort_values("delta_npv"),
    x="delta_npv",
    y="시설명",
    orientation="h",
    color="risk_level",
    color_discrete_map=RISK_COLORS,
    hover_data={"npv_pct": ":.1f", "섹터": True},
    labels={"delta_npv": "Delta NPV (USD)", "risk_level": "위험등급"},
)
fig_npv.update_layout(height=max(400, len(facs) * 35), showlegend=True)
st.plotly_chart(fig_npv, use_container_width=True)

# ── Facility Table ──────────────────────────────────────────────────────

st.subheader("시설별 상세")
df_table = pd.DataFrame([{
    "시설명": f["facility_name"],
    "섹터": f["sector"],
    "Delta NPV": format_currency(f["delta_npv"]),
    "NPV/자산 (%)": f"{f['npv_as_pct_of_assets']:.1f}%",
    "위험등급": f["risk_level"],
} for f in sorted(facs, key=lambda x: x["delta_npv"])])
st.dataframe(df_table, use_container_width=True, hide_index=True)

st.divider()

# ── Selected Facility Deep-Dive ────────────────────────────────────────

st.subheader("시설 상세 분석")
fac_names = [f["facility_name"] for f in facs]
selected_name = st.selectbox("시설 선택", fac_names)
selected = next(f for f in facs if f["facility_name"] == selected_name)

tab1, tab2, tab3 = st.tabs(["배출 경로", "연간 비용 구조", "상세 데이터"])

with tab1:
    pathway = selected["emission_pathway"]
    df_path = pd.DataFrame(pathway)
    fig_path = go.Figure()
    fig_path.add_trace(go.Scatter(
        x=df_path["year"], y=df_path["scope1_emissions"],
        name="Scope 1", mode="lines+markers", stackgroup="one",
        line=dict(color="#ef4444"),
    ))
    fig_path.add_trace(go.Scatter(
        x=df_path["year"], y=df_path["scope2_emissions"],
        name="Scope 2", mode="lines+markers", stackgroup="one",
        line=dict(color="#f97316"),
    ))
    fig_path.update_layout(
        title=f"{selected_name} — 배출 경로 (tCO2e)",
        xaxis_title="연도", yaxis_title="배출량 (tCO2e)", height=400,
    )
    st.plotly_chart(fig_path, use_container_width=True)

with tab2:
    impacts = selected["annual_impacts"]
    df_imp = pd.DataFrame(impacts)
    fig_cost = go.Figure()
    for col_name, label, color in [
        ("carbon_cost", "탄소비용", "#ef4444"),
        ("energy_cost_increase", "에너지비용", "#f97316"),
        ("revenue_impact", "매출영향", "#eab308"),
        ("transition_opex", "전환 OPEX", "#3b82f6"),
        ("stranded_asset_writedown", "좌초자산", "#8b5cf6"),
        ("scope3_impact", "Scope 3", "#6b7280"),
    ]:
        if col_name in df_imp.columns:
            fig_cost.add_trace(go.Bar(
                x=df_imp["year"], y=df_imp[col_name],
                name=label, marker_color=color,
            ))
    fig_cost.update_layout(
        barmode="stack",
        title=f"{selected_name} — 연간 비용 구조",
        xaxis_title="연도", yaxis_title="비용 (USD)", height=400,
    )
    st.plotly_chart(fig_cost, use_container_width=True)

with tab3:
    df_detail = pd.DataFrame(impacts)
    st.dataframe(df_detail, use_container_width=True, hide_index=True)

# ── Scenario Comparison (Optional) ────────────────────────────────────

if show_comparison:
    st.divider()
    st.subheader("시나리오 비교")

    with st.spinner("4개 시나리오 비교 분석 중..."):
        comp = compare_scenarios(pricing_regime=pricing_regime)

    # NPV Comparison Bar Chart
    df_comp = pd.DataFrame(comp["npv_comparison"])
    df_comp["color"] = df_comp["scenario"].map(SCENARIO_COLORS)
    fig_comp = px.bar(
        df_comp,
        x="scenario_name",
        y="total_npv",
        color="scenario",
        color_discrete_map=SCENARIO_COLORS,
        labels={"total_npv": "Total NPV (USD)", "scenario_name": "시나리오"},
    )
    fig_comp.update_layout(title="시나리오별 총 NPV 영향", showlegend=False, height=400)
    st.plotly_chart(fig_comp, use_container_width=True)

    # Risk Distribution
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**위험 등급 분포**")
        risk_data = []
        for sid, dist in comp["risk_distribution"].items():
            for level in ["high", "medium", "low"]:
                risk_data.append({
                    "scenario": SCENARIO_NAMES.get(sid, sid),
                    "level": level.capitalize(),
                    "count": dist[level],
                })
        df_risk = pd.DataFrame(risk_data)
        fig_risk = px.bar(
            df_risk, x="scenario", y="count", color="level",
            color_discrete_map=RISK_COLORS,
            barmode="stack",
            labels={"count": "시설 수", "scenario": "시나리오", "level": "위험등급"},
        )
        fig_risk.update_layout(height=350)
        st.plotly_chart(fig_risk, use_container_width=True)

    with col2:
        st.markdown("**총 배출 경로**")
        fig_ep = go.Figure()
        for sid, pathway_data in comp["emission_pathways"].items():
            df_ep = pd.DataFrame(pathway_data)
            fig_ep.add_trace(go.Scatter(
                x=df_ep["year"], y=df_ep["total_emissions"],
                name=SCENARIO_NAMES.get(sid, sid),
                mode="lines+markers",
                line=dict(color=SCENARIO_COLORS.get(sid)),
            ))
        fig_ep.update_layout(
            xaxis_title="연도", yaxis_title="총 배출량 (tCO2e)", height=350,
        )
        st.plotly_chart(fig_ep, use_container_width=True)
