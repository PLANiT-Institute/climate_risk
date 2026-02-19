"""Page 1: NGFS Scenario Overview — carbon price paths and scenario descriptions."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.helpers import SCENARIO_COLORS, SCENARIO_NAMES, format_currency, default_layout

from app.core.config import SCENARIOS, NGFS_CARBON_PRICE_PATHS

st.set_page_config(page_title="시나리오 개요", page_icon="📋", layout="wide")

st.title("NGFS 시나리오 개요")
st.markdown("NGFS(Network for Greening the Financial System) 4대 기후 시나리오별 주요 파라미터와 탄소가격 경로입니다.")
st.divider()

# ── Scenario Cards ──
st.subheader("4대 시나리오")
cols = st.columns(4)
for i, (sid, sc) in enumerate(SCENARIOS.items()):
    with cols[i]:
        color = sc.get("color", "#6b7280")
        st.markdown(
            f'<div style="border-left:4px solid {color};padding:8px 12px;margin-bottom:8px;">'
            f'<strong>{sc["name"]}</strong></div>',
            unsafe_allow_html=True,
        )
        st.caption(sc["description"])
        st.metric("탄소가격 2030", f"${sc['carbon_price_2030']}/tCO2e")
        st.metric("탄소가격 2050", f"${sc['carbon_price_2050']}/tCO2e")
        st.metric("감축 목표", f"{sc['emissions_reduction_target']*100:.0f}%")

st.divider()

# ── Carbon Price Path Chart ──
st.subheader("탄소가격 경로 비교")

fig = go.Figure()
for sid, path in NGFS_CARBON_PRICE_PATHS.items():
    years = sorted(path.keys())
    prices = [path[y] for y in years]
    fig.add_trace(go.Scatter(
        x=years,
        y=prices,
        mode="lines+markers",
        name=SCENARIO_NAMES.get(sid, sid),
        line=dict(color=SCENARIO_COLORS.get(sid, "#6b7280"), width=2.5),
        marker=dict(size=6),
    ))
default_layout(fig, title="NGFS 탄소가격 경로 ($/tCO2e)", height=450)
fig.update_xaxes(title="연도", dtick=5)
fig.update_yaxes(title="탄소가격 ($/tCO2e)")
st.plotly_chart(fig, use_container_width=True)

# ── Summary Table ──
st.subheader("시나리오 파라미터 비교")

rows = []
for sid, sc in SCENARIOS.items():
    path = NGFS_CARBON_PRICE_PATHS[sid]
    rows.append({
        "시나리오": sc["name"],
        "탄소가격 2025": f"${sc['carbon_price_2025']}",
        "탄소가격 2030": f"${sc['carbon_price_2030']}",
        "탄소가격 2050": f"${sc['carbon_price_2050']}",
        "감축 목표": f"{sc['emissions_reduction_target']*100:.0f}%",
        "설명": sc["description"],
    })
df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)
