"""Climate Risk Disclosure Tool - Main Dashboard.

Entry point for the Streamlit multi-page app.
Global sidebar: company / scenario / pricing regime / year.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Add parent directory to path so we can import backend services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from utils.helpers import (
    format_currency, format_emissions, default_layout,
    SCENARIO_NAMES, COMPANY_NAMES_KR, SECTOR_NAMES_KR,
)
from utils.company_data import (
    get_cached_transition, get_cached_physical,
    filter_transition_by_company, filter_physical_by_company,
)

from app.data.sample_facilities import (
    get_all_facilities, get_company_list, get_facilities_by_company, get_company_summary,
)
from components.sidebar import render_global_sidebar

st.set_page_config(
    page_title="기후리스크 공시 도구",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_global_sidebar()

# ── Read sidebar selections ──────────────────────────────────────────
company = st.session_state.get("global_company", get_company_list()[0])
scenario_id = st.session_state.get("global_scenario", "net_zero_2050")
pricing_regime = st.session_state.get("global_pricing", "kets")
year = st.session_state.get("global_year", 2030)

# ── Company Info ────────────────────────────────────────────────────
summary = get_company_summary(company)
company_facs = get_facilities_by_company(company)

st.title("기후리스크 공시 도구")
st.markdown(
    f"**{COMPANY_NAMES_KR.get(company, company)}** 의 기후리스크를 분석하고, "
    "공시 요건 충족 여부를 평가합니다."
)

st.divider()

# ── KPI Row ──────────────────────────────────────────────────────────
st.subheader("기업 개요")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("시설 수", f"{summary['facility_count']}개")
with col2:
    total_12 = summary["total_scope1"] + summary["total_scope2"]
    st.metric("Scope 1+2 배출량", format_emissions(total_12))
with col3:
    st.metric("Scope 3 배출량", format_emissions(summary["total_scope3"]))
with col4:
    sectors_kr = [SECTOR_NAMES_KR.get(s, s) for s in summary["sectors"]]
    st.metric("업종", " / ".join(sectors_kr))
with col5:
    st.metric("총 자산", format_currency(summary["total_assets"]))

st.divider()

# ── Transition Risk Summary ─────────────────────────────────────────
st.subheader("전환 리스크 요약")

with st.spinner("전환 리스크 분석 중..."):
    tr_full = get_cached_transition(scenario_id, pricing_regime)
    tr = filter_transition_by_company(tr_full, company)

col_t1, col_t2, col_t3 = st.columns(3)
with col_t1:
    st.metric("총 NPV 영향", format_currency(tr["total_npv"]))
with col_t2:
    high = sum(1 for f in tr["facilities"] if f["risk_level"] == "High")
    st.metric("고위험 시설", f"{high}개")
with col_t3:
    st.metric(
        "시나리오",
        SCENARIO_NAMES.get(scenario_id, scenario_id),
    )

if pricing_regime == "kets":
    st.info("K-ETS: 무상할당 초과분에 대해서만 탄소비용 부과")

st.divider()

# ── Facility Map ────────────────────────────────────────────────────
st.subheader("시설 분포 지도")

with st.spinner("물리적 리스크 평가 중..."):
    pr_full = get_cached_physical(scenario_id, year)
    pr = filter_physical_by_company(pr_full, company)

physical_risk_map = {f["facility_id"]: f["overall_risk_level"] for f in pr["facilities"]}

df_fac = pd.DataFrame(company_facs)
df_map = df_fac.copy()
df_map["risk_level"] = df_map["facility_id"].map(physical_risk_map).fillna("Low")
df_map["emissions_total"] = df_map["current_emissions_scope1"] + df_map["current_emissions_scope2"]

fig_map = px.scatter_mapbox(
    df_map,
    lat="latitude",
    lon="longitude",
    hover_name="name",
    hover_data={
        "sector": True, "location": True,
        "emissions_total": ":,.0f",
        "latitude": False, "longitude": False,
    },
    color="risk_level",
    color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"},
    size="emissions_total",
    size_max=25,
    zoom=6,
    center={"lat": df_map["latitude"].mean(), "lon": df_map["longitude"].mean()},
    mapbox_style="carto-positron",
)
default_layout(fig_map, height=500)
fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig_map, use_container_width=True)

# ── Facility Table ──────────────────────────────────────────────────
st.subheader("시설 목록")

df_table = df_fac[["name", "sector", "location"]].copy()
df_table["Scope 1 (tCO2e)"] = df_fac["current_emissions_scope1"].apply(lambda x: f"{x:,.0f}")
df_table["Scope 2 (tCO2e)"] = df_fac["current_emissions_scope2"].apply(lambda x: f"{x:,.0f}")
df_table["매출 (USD)"] = df_fac["annual_revenue"].apply(format_currency)
df_table.columns = ["시설명", "섹터", "위치", "Scope 1", "Scope 2", "매출"]
st.dataframe(df_table, use_container_width=True, hide_index=True)
