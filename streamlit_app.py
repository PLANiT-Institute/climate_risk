"""Climate Risk Assessment Tool — Streamlit Home Page.

Portfolio overview using backend data (no upload required).
Navigation hub for analysis pages.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import streamlit as st

from app.data.sample_facilities import get_all_facilities

st.set_page_config(
    page_title="Climate Risk Assessment Tool",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load Data ─────────────────────────────────────────────────────────
facilities = get_all_facilities()

SECTOR_NAMES_KR = {
    "steel": "Steel",
    "petrochemical": "Petrochemical",
    "automotive": "Automotive",
    "electronics": "Electronics",
    "utilities": "Utilities",
    "cement": "Cement",
    "shipping": "Shipping",
    "oil_gas": "Oil & Gas",
}

# ── Header ────────────────────────────────────────────────────────────
st.title("🌍 Climate Risk Assessment Tool")
st.markdown("NGFS scenario-based climate risk analysis platform for Korean industrial facilities.")

st.divider()

# ── Portfolio KPIs ────────────────────────────────────────────────────
st.subheader("Portfolio Overview")

total_s1 = sum(f["current_emissions_scope1"] for f in facilities)
total_s2 = sum(f["current_emissions_scope2"] for f in facilities)
total_assets = sum(f["assets_value"] for f in facilities)
total_revenue = sum(f["annual_revenue"] for f in facilities)
sectors = set(f["sector"] for f in facilities)
companies = set(f["company"] for f in facilities)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Facilities", len(facilities))
with col2:
    st.metric("Companies", len(companies))
with col3:
    st.metric("Sectors", len(sectors))
with col4:
    st.metric("Scope 1+2", f"{(total_s1 + total_s2) / 1e6:.1f}M tCO2e")
with col5:
    st.metric("Total Assets", f"${total_assets / 1e9:.0f}B")

st.divider()

# ── Sector Breakdown ──────────────────────────────────────────────────
st.subheader("Sector Breakdown")

sector_data = {}
for f in facilities:
    s = f["sector"]
    if s not in sector_data:
        sector_data[s] = {"count": 0, "emissions": 0, "assets": 0}
    sector_data[s]["count"] += 1
    sector_data[s]["emissions"] += f["current_emissions_scope1"] + f["current_emissions_scope2"]
    sector_data[s]["assets"] += f["assets_value"]

import pandas as pd

df_sectors = pd.DataFrame([
    {
        "Sector": SECTOR_NAMES_KR.get(s, s),
        "Facilities": d["count"],
        "Emissions (MtCO2e)": f'{d["emissions"] / 1e6:.1f}',
        "Assets ($B)": f'${d["assets"] / 1e9:.1f}',
    }
    for s, d in sorted(sector_data.items(), key=lambda x: x[1]["emissions"], reverse=True)
])
st.dataframe(df_sectors, use_container_width=True, hide_index=True)

st.divider()

# ── Navigation ────────────────────────────────────────────────────────
st.subheader("Analysis Pages")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    **🔄 Transition Risk**

    NGFS scenario analysis, carbon pricing impact, facility-level NPV
    """)

with col2:
    st.markdown("""
    **🌪️ Physical Risk**

    5-hazard assessment, EAL, risk maps
    """)

with col3:
    st.markdown("""
    **🏆 ESG Compliance**

    TCFD / ISSB / KSSB checklist-based readiness
    """)

with col4:
    st.markdown("""
    **📑 Results Dashboard**

    Comprehensive summary + PPT export
    """)

# ── Footer ────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Climate Risk Assessment Tool v3.0 | Built with Streamlit + FastAPI Backend")
