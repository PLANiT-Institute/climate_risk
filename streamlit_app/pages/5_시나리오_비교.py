"""Page 5: Scenario Comparison — 4 NGFS scenarios side-by-side, company-filtered."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.helpers import (
    SCENARIO_COLORS, SCENARIO_NAMES, COMPANY_NAMES_KR,
    format_currency, default_layout,
)
from utils.company_data import get_cached_comparison, filter_comparison_by_company

st.set_page_config(page_title="시나리오 비교", page_icon="📈", layout="wide")

from components.sidebar import render_global_sidebar
render_global_sidebar()

# ── Read global sidebar state ──
company = st.session_state.get("global_company", "K-Steel Corp")
pricing_regime = st.session_state.get("global_pricing", "kets")

st.title("시나리오 비교 분석")
st.caption(f"{COMPANY_NAMES_KR.get(company, company)} | 4개 NGFS 시나리오 비교")

# ── Run Comparison ──
with st.spinner("4개 시나리오 비교 분석 중..."):
    full_result = get_cached_comparison(pricing_regime)
    result = filter_comparison_by_company(full_result, company)

npv_comp = result["npv_comparison"]
emission_paths = result["emission_pathways"]
risk_dist = result["risk_distribution"]
cost_trends = result["cost_trends"]

st.divider()

# ── NPV Comparison Bar Chart ──
st.subheader("시나리오별 총 NPV 영향")

fig_npv = go.Figure()
for item in npv_comp:
    sid = item["scenario"]
    fig_npv.add_trace(go.Bar(
        x=[SCENARIO_NAMES.get(sid, sid)],
        y=[item["total_npv"]],
        name=SCENARIO_NAMES.get(sid, sid),
        marker_color=SCENARIO_COLORS.get(sid, "#6b7280"),
        text=[format_currency(item["total_npv"])],
        textposition="outside",
    ))
default_layout(fig_npv, title="시나리오별 총 NPV 영향 (USD)", height=400)
fig_npv.update_layout(showlegend=False)
fig_npv.update_yaxes(title="NPV (USD)")
st.plotly_chart(fig_npv, use_container_width=True)

# ── KPI Cards ──
cols = st.columns(4)
for i, item in enumerate(npv_comp):
    with cols[i]:
        sid = item["scenario"]
        st.markdown(f"**{SCENARIO_NAMES.get(sid, sid)}**")
        st.metric("총 NPV", format_currency(item["total_npv"]))
        st.caption(f"평균 위험등급: {item['avg_risk_level']}")

st.divider()

# ── Emission Pathways ──
st.subheader("시나리오별 총 배출 경로")

fig_emit = go.Figure()
for sid, pathway in emission_paths.items():
    if not pathway:
        continue
    years = [p["year"] for p in pathway]
    emissions = [p["total_emissions"] for p in pathway]
    fig_emit.add_trace(go.Scatter(
        x=years,
        y=emissions,
        mode="lines+markers",
        name=SCENARIO_NAMES.get(sid, sid),
        line=dict(color=SCENARIO_COLORS.get(sid, "#6b7280"), width=2.5),
        marker=dict(size=6),
    ))
default_layout(fig_emit, title="시나리오별 총 배출량 (tCO2e)", height=450)
fig_emit.update_xaxes(title="연도")
fig_emit.update_yaxes(title="총 배출량 (tCO2e)")
st.plotly_chart(fig_emit, use_container_width=True)

st.divider()

# ── Cost Trends ──
st.subheader("시나리오별 총 비용 추세")

fig_cost = go.Figure()
for sid, trend in cost_trends.items():
    if not trend:
        continue
    years = [t["year"] for t in trend]
    costs = [t["total_cost"] for t in trend]
    fig_cost.add_trace(go.Scatter(
        x=years,
        y=costs,
        mode="lines+markers",
        name=SCENARIO_NAMES.get(sid, sid),
        line=dict(color=SCENARIO_COLORS.get(sid, "#6b7280"), width=2.5),
        marker=dict(size=6),
    ))
default_layout(fig_cost, title="시나리오별 연간 총 비용 (USD)", height=450)
fig_cost.update_xaxes(title="연도")
fig_cost.update_yaxes(title="연간 총 비용 (USD)")
st.plotly_chart(fig_cost, use_container_width=True)

st.divider()

# ── Risk Distribution ──
st.subheader("시나리오별 위험 등급 분포")

fig_risk = go.Figure()
scenario_ids = [item["scenario"] for item in npv_comp]
scenario_labels = [SCENARIO_NAMES.get(sid, sid) for sid in scenario_ids]

for level, color in [("high", "#ef4444"), ("medium", "#f59e0b"), ("low", "#22c55e")]:
    values = [risk_dist.get(sid, {}).get(level, 0) for sid in scenario_ids]
    level_kr = {"high": "고위험", "medium": "중위험", "low": "저위험"}[level]
    fig_risk.add_trace(go.Bar(
        x=scenario_labels,
        y=values,
        name=level_kr,
        marker_color=color,
        text=values,
        textposition="inside",
    ))

fig_risk.update_layout(barmode="stack")
default_layout(fig_risk, title="시나리오별 위험 등급 분포 (시설 수)", height=400)
fig_risk.update_yaxes(title="시설 수")
st.plotly_chart(fig_risk, use_container_width=True)

# ── Summary Table ──
st.subheader("시나리오 비교 요약")

df_summary = pd.DataFrame([{
    "시나리오": SCENARIO_NAMES.get(item["scenario"], item["scenario"]),
    "총 NPV": format_currency(item["total_npv"]),
    "평균 위험등급": item["avg_risk_level"],
    "고위험": risk_dist.get(item["scenario"], {}).get("high", 0),
    "중위험": risk_dist.get(item["scenario"], {}).get("medium", 0),
    "저위험": risk_dist.get(item["scenario"], {}).get("low", 0),
} for item in npv_comp])
st.dataframe(df_summary, use_container_width=True, hide_index=True)
