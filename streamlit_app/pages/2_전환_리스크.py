"""Page 2: Transition Risk Analysis — company-filtered NPV, emission pathways, cost structure."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.helpers import (
    SCENARIO_COLORS, SCENARIO_NAMES, RISK_COLORS, COMPANY_NAMES_KR,
    format_currency, format_emissions, default_layout,
)
from utils.company_data import get_cached_transition, filter_transition_by_company

st.set_page_config(page_title="전환 리스크", page_icon="🔄", layout="wide")

from components.sidebar import render_global_sidebar
render_global_sidebar()

# ── Read global sidebar state ──
company = st.session_state.get("global_company", "K-Steel Corp")
scenario_id = st.session_state.get("global_scenario", "net_zero_2050")
pricing_regime = st.session_state.get("global_pricing", "kets")

st.title("전환 리스크 분석")
st.caption(f"{COMPANY_NAMES_KR.get(company, company)} | {SCENARIO_NAMES.get(scenario_id, scenario_id)}")

# ── Run Analysis ──
with st.spinner("전환 리스크 분석 중..."):
    full_result = get_cached_transition(scenario_id, pricing_regime)
    result = filter_transition_by_company(full_result, company)

facs = result["facilities"]

if not facs:
    st.warning("선택된 기업에 해당하는 시설이 없습니다.")
    st.stop()

# ── Summary KPIs ──
st.subheader(f"{SCENARIO_NAMES[scenario_id]} — 요약")
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

# ── Facility NPV Distribution ──
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
default_layout(fig_npv, title="시설별 전환 리스크 NPV", height=max(300, len(facs) * 50))
st.plotly_chart(fig_npv, use_container_width=True)

# ── Facility Table ──
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

# ── Selected Facility Deep-Dive ──
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
    default_layout(fig_path, title=f"{selected_name} — 배출 경로 (tCO2e)", height=400)
    fig_path.update_xaxes(title="연도")
    fig_path.update_yaxes(title="배출량 (tCO2e)")
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
    fig_cost.update_layout(barmode="stack")
    default_layout(fig_cost, title=f"{selected_name} — 연간 비용 구조", height=400)
    fig_cost.update_xaxes(title="연도")
    fig_cost.update_yaxes(title="비용 (USD)")
    st.plotly_chart(fig_cost, use_container_width=True)

with tab3:
    df_detail = pd.DataFrame(impacts)
    st.dataframe(df_detail, use_container_width=True, hide_index=True)
