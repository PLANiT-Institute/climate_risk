"""Results Dashboard — aggregates transition + physical + ESG from backend services.

Shows:
- Sidebar: scenario, pricing regime selection
- Summary KPI row: total NPV, total EAL, ESG compliance, high-risk count
- Two-column layout: transition risk summary + physical risk summary
- ESG compliance summary across frameworks
- PPT download button
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.services.transition_risk import analyse_scenario, compare_scenarios
from app.services.physical_risk import assess_physical_risk
from app.services.esg_compliance import assess_framework
from app.core.config import SCENARIOS

st.set_page_config(page_title="Results Dashboard", page_icon="📑", layout="wide")

# ── Constants ─────────────────────────────────────────────────────────
SCENARIO_NAMES = {
    "net_zero_2050": "Net Zero 2050",
    "below_2c": "Below 2°C",
    "delayed_transition": "Delayed Transition",
    "current_policies": "Current Policies",
}


def format_currency(val):
    if abs(val) >= 1e9:
        return f"${val/1e9:.1f}B"
    if abs(val) >= 1e6:
        return f"${val/1e6:.1f}M"
    return f"${val:,.0f}"


# ── Sidebar ───────────────────────────────────────────────────────────
st.sidebar.header("Dashboard Settings")

scenario_id = st.sidebar.selectbox(
    "Scenario",
    list(SCENARIOS.keys()),
    format_func=lambda x: SCENARIO_NAMES.get(x, x),
    index=0,
)

pricing_regime = st.sidebar.radio(
    "Pricing Regime",
    ["global", "kets"],
    format_func=lambda x: "Global" if x == "global" else "K-ETS",
)

year = st.sidebar.slider("Physical Risk Year", 2030, 2100, 2030, step=10)

# ── Page Title ────────────────────────────────────────────────────────
st.title("📑 Results Dashboard")
st.caption(f"{SCENARIO_NAMES[scenario_id]} | {'K-ETS' if pricing_regime == 'kets' else 'Global'} | {year}")

# ── Run All Services ──────────────────────────────────────────────────
with st.spinner("Running comprehensive analysis..."):
    transition = analyse_scenario(scenario_id, pricing_regime=pricing_regime)
    comparison = compare_scenarios(pricing_regime=pricing_regime)
    physical = assess_physical_risk(scenario_id=scenario_id, year=year)
    esg_results = {fw: assess_framework(fw) for fw in ["tcfd", "issb", "kssb"]}

# ── Summary KPIs ──────────────────────────────────────────────────────
st.subheader("Portfolio Summary")

total_npv = transition["total_npv"]
total_eal = sum(f["total_expected_annual_loss"] for f in physical["facilities"])
high_risk = physical["overall_risk_summary"].get("High", 0)

# Average ESG compliance rate across frameworks
esg_compliant_total = 0
esg_items_total = 0
for fw_data in esg_results.values():
    checklist = fw_data["checklist"]
    esg_compliant_total += sum(1 for c in checklist if c["status"] == "compliant")
    esg_items_total += len(checklist)
esg_rate = (esg_compliant_total / esg_items_total * 100) if esg_items_total else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Transition NPV", format_currency(total_npv))
with col2:
    st.metric("Physical EAL", format_currency(total_eal))
with col3:
    st.metric("ESG Compliance", f"{esg_rate:.0f}%")
with col4:
    st.metric("High-Risk Facilities", f"{high_risk}")

st.divider()

# ── Two-Column Layout ─────────────────────────────────────────────────
col_left, col_right = st.columns(2)

# Left: Transition Risk Summary
with col_left:
    st.subheader("Transition Risk — Scenario Comparison")

    npv_data = comparison["npv_comparison"]
    scenario_names = [d["scenario_name"] for d in npv_data]
    scenario_npvs = [abs(d["total_npv"]) for d in npv_data]
    scenario_colors = [SCENARIOS[d["scenario"]].get("color", "#3b82f6") for d in npv_data]

    fig_npv = go.Figure()
    fig_npv.add_trace(go.Bar(
        x=scenario_names,
        y=scenario_npvs,
        marker_color=scenario_colors,
        text=[format_currency(v) for v in scenario_npvs],
        textposition="outside",
    ))
    fig_npv.update_layout(
        title="Total NPV Impact by Scenario",
        yaxis_title="NPV (USD)",
        height=400,
    )
    st.plotly_chart(fig_npv, use_container_width=True)

    # Top 5 facilities table
    st.markdown("**Top 5 Facilities by NPV Impact**")
    top_facs = sorted(transition["facilities"], key=lambda x: x["delta_npv"])[:5]
    df_top = pd.DataFrame([{
        "Facility": f["facility_name"],
        "Sector": f["sector"],
        "Delta NPV": format_currency(f["delta_npv"]),
        "Risk Level": f["risk_level"],
    } for f in top_facs])
    st.dataframe(df_top, use_container_width=True, hide_index=True)

# Right: Physical Risk Summary
with col_right:
    st.subheader("Physical Risk — Hazard Breakdown")

    hazard_types = ["flood", "typhoon", "heatwave", "drought", "sea_level_rise"]
    hazard_labels = {
        "flood": "Flood", "typhoon": "Typhoon", "heatwave": "Heatwave",
        "drought": "Drought", "sea_level_rise": "Sea Level Rise",
    }
    hazard_colors = ["#3b82f6", "#8b5cf6", "#ef4444", "#f59e0b", "#06b6d4"]

    agg = {ht: 0 for ht in hazard_types}
    for f in physical["facilities"]:
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
    fig_haz.update_layout(
        title="Total EAL by Hazard Type",
        yaxis_title="EAL (USD)",
        height=400,
    )
    st.plotly_chart(fig_haz, use_container_width=True)

    # Top 5 physical risk facilities
    st.markdown("**Top 5 Facilities by EAL**")
    top_phys = sorted(physical["facilities"],
                      key=lambda x: x["total_expected_annual_loss"], reverse=True)[:5]
    df_phys = pd.DataFrame([{
        "Facility": f["facility_name"],
        "Location": f["location"],
        "Total EAL": format_currency(f["total_expected_annual_loss"]),
        "Risk Level": f["overall_risk_level"],
    } for f in top_phys])
    st.dataframe(df_phys, use_container_width=True, hide_index=True)

st.divider()

# ── ESG Compliance Summary ────────────────────────────────────────────
st.subheader("ESG Compliance Summary")

esg_cols = st.columns(3)
for i, (fw_id, fw_data) in enumerate(esg_results.items()):
    with esg_cols[i]:
        checklist = fw_data["checklist"]
        n_c = sum(1 for c in checklist if c["status"] == "compliant")
        n_p = sum(1 for c in checklist if c["status"] == "partial")
        n_n = sum(1 for c in checklist if c["status"] == "non_compliant")
        total = len(checklist)

        st.markdown(f"**{fw_data['framework_name']}**")
        st.metric("Score", f"{fw_data['overall_score']:.0f}/100")
        st.caption(f"✅ {n_c}  |  ⚠️ {n_p}  |  ❌ {n_n}  (of {total})")

st.divider()

# ── PPT Download ──────────────────────────────────────────────────────
st.subheader("Export Report")

try:
    from generate_ppt import generate_report

    if st.button("Download PPT Report", type="primary"):
        with st.spinner("Generating PPT..."):
            filepath = generate_report(
                scenario_id=scenario_id,
                pricing_regime=pricing_regime,
                year=year,
            )
        with open(filepath, "rb") as f:
            st.download_button(
                label="Download .pptx",
                data=f.read(),
                file_name="climate_risk_report.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
except ImportError:
    st.info("PPT generation module not available.")
