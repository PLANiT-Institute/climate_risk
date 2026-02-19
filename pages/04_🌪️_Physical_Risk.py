"""Physical Risk Assessment Page — backend assess_physical_risk() integration.

Shows:
- Sidebar: scenario + year selection
- KPI row: total EAL, high/medium risk counts, warming level
- Mapbox map: facilities by risk level and EAL size
- EAL table: sorted by expected annual loss
- Facility detail: per-hazard analysis (flood/typhoon/heatwave/drought/sea_level_rise)
- Aggregate hazard chart
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app.services.physical_risk import assess_physical_risk
from app.core.config import SCENARIOS

st.set_page_config(page_title="Physical Risk", page_icon="🌪️", layout="wide")

# ── Constants ─────────────────────────────────────────────────────────
SCENARIO_NAMES = {
    "net_zero_2050": "Net Zero 2050",
    "below_2c": "Below 2°C",
    "delayed_transition": "Delayed Transition",
    "current_policies": "Current Policies",
}

RISK_COLORS = {"High": "#ef4444", "Medium": "#f97316", "Low": "#22c55e"}

HAZARD_NAMES_KR = {
    "flood": "홍수",
    "typhoon": "태풍",
    "heatwave": "폭염",
    "drought": "가뭄",
    "sea_level_rise": "해수면 상승",
}

HAZARD_COLORS = ["#3b82f6", "#8b5cf6", "#ef4444", "#f59e0b", "#06b6d4"]


def format_currency(val):
    if abs(val) >= 1e9:
        return f"${val/1e9:.1f}B"
    if abs(val) >= 1e6:
        return f"${val/1e6:.1f}M"
    if abs(val) >= 1e3:
        return f"${val/1e3:.0f}K"
    return f"${val:,.0f}"


# ── Sidebar ───────────────────────────────────────────────────────────
st.sidebar.header("Physical Risk Settings")

scenario_id = st.sidebar.selectbox(
    "Scenario",
    list(SCENARIOS.keys()),
    format_func=lambda x: SCENARIO_NAMES.get(x, x),
    index=0,
)

year = st.sidebar.slider("Assessment Year", 2030, 2100, 2030, step=10)

# ── Run Assessment ────────────────────────────────────────────────────
st.title("🌪️ Physical Risk Assessment")
st.caption(f"{SCENARIO_NAMES[scenario_id]} | {year}년")

with st.spinner("Assessing physical risks..."):
    result = assess_physical_risk(scenario_id=scenario_id, year=year)

facs = result["facilities"]
risk_summary = result["overall_risk_summary"]

if not facs:
    st.warning("No facility data available.")
    st.stop()

# ── KPI Row ───────────────────────────────────────────────────────────
total_eal = sum(f["total_expected_annual_loss"] for f in facs)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total EAL", format_currency(total_eal))
with col2:
    st.metric("High Risk", f'{risk_summary.get("High", 0)} facilities')
with col3:
    st.metric("Medium Risk", f'{risk_summary.get("Medium", 0)} facilities')
with col4:
    st.metric("Warming", f'+{result["warming_above_preindustrial"]:.1f}°C')

st.divider()

# ── Risk Map ──────────────────────────────────────────────────────────
st.subheader("Facility Risk Map")

df_map = pd.DataFrame([{
    "name": f["facility_name"],
    "latitude": f["latitude"],
    "longitude": f["longitude"],
    "location": f["location"],
    "risk_level": f["overall_risk_level"],
    "total_eal": f["total_expected_annual_loss"],
} for f in facs])

fig_map = px.scatter_mapbox(
    df_map,
    lat="latitude",
    lon="longitude",
    hover_name="name",
    hover_data={"location": True, "total_eal": ":,.0f", "latitude": False, "longitude": False},
    color="risk_level",
    color_discrete_map=RISK_COLORS,
    size="total_eal",
    size_max=25,
    zoom=6,
    center={"lat": df_map["latitude"].mean(), "lon": df_map["longitude"].mean()},
    mapbox_style="carto-positron",
)
fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=500)
st.plotly_chart(fig_map, use_container_width=True)

# ── EAL Table ─────────────────────────────────────────────────────────
st.subheader("Expected Annual Loss by Facility")

df_eal = pd.DataFrame([{
    "Facility": f["facility_name"],
    "Location": f["location"],
    "Total EAL": format_currency(f["total_expected_annual_loss"]),
    "Risk Level": f["overall_risk_level"],
    "eal_raw": f["total_expected_annual_loss"],
} for f in facs]).sort_values("eal_raw", ascending=False)

st.dataframe(
    df_eal[["Facility", "Location", "Total EAL", "Risk Level"]],
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ── Selected Facility Detail ──────────────────────────────────────────
st.subheader("Facility Detail — Hazard Breakdown")

fac_names = [f["facility_name"] for f in facs]
selected_name = st.selectbox("Select Facility", fac_names)
selected = next(f for f in facs if f["facility_name"] == selected_name)

hazards = selected["hazards"]

# Hazard bar chart
haz_names = [HAZARD_NAMES_KR.get(h["hazard_type"], h["hazard_type"]) for h in hazards]
haz_losses = [h["potential_loss"] for h in hazards]

fig_haz = go.Figure()
fig_haz.add_trace(go.Bar(
    x=haz_names,
    y=haz_losses,
    marker_color=HAZARD_COLORS[:len(haz_names)],
    text=[format_currency(v) for v in haz_losses],
    textposition="outside",
))
fig_haz.update_layout(
    title=f"{selected_name} — Hazard EAL Breakdown",
    xaxis_title="Hazard Type",
    yaxis_title="EAL (USD)",
    height=400,
)
st.plotly_chart(fig_haz, use_container_width=True)

# Hazard detail table
df_hazard = pd.DataFrame([{
    "Hazard": HAZARD_NAMES_KR.get(h["hazard_type"], h["hazard_type"]),
    "Risk Level": h["risk_level"],
    "Probability": f'{h["probability"]:.3f}',
    "EAL": format_currency(h["potential_loss"]),
    "Return Period (yr)": h["return_period_years"],
    "Climate Multiplier": f'{h["climate_change_multiplier"]:.2f}x',
    "Description": h["description"],
} for h in hazards])
st.dataframe(df_hazard, use_container_width=True, hide_index=True)

st.divider()

# ── Aggregate Hazard Chart ────────────────────────────────────────────
st.subheader("Portfolio — Total EAL by Hazard Type")

hazard_types = ["flood", "typhoon", "heatwave", "drought", "sea_level_rise"]
agg = {ht: 0 for ht in hazard_types}
for f in facs:
    for h in f["hazards"]:
        if h["hazard_type"] in agg:
            agg[h["hazard_type"]] += h["potential_loss"]

fig_agg = go.Figure()
fig_agg.add_trace(go.Bar(
    x=[HAZARD_NAMES_KR.get(ht, ht) for ht in hazard_types],
    y=[agg[ht] for ht in hazard_types],
    marker_color=HAZARD_COLORS,
    text=[format_currency(agg[ht]) for ht in hazard_types],
    textposition="outside",
))
fig_agg.update_layout(
    title="Total EAL by Hazard Type (All Facilities)",
    yaxis_title="Total EAL (USD)",
    height=400,
)
st.plotly_chart(fig_agg, use_container_width=True)
