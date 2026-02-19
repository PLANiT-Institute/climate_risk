"""ESG Compliance Page — checklist-based disclosure readiness.

Uses backend assess_framework() and get_disclosure_data().
Shows:
- Framework tabs: TCFD / ISSB / KSSB
- Checklist with status icons
- Regulatory deadlines with D-day countdown
- Disclosure metrics summary
"""

import sys
import os
from datetime import date, datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import streamlit as st

from app.services.esg_compliance import assess_framework, get_disclosure_data

st.set_page_config(page_title="ESG Compliance", page_icon="🏆", layout="wide")

# ── Constants ─────────────────────────────────────────────────────────
STATUS_ICON = {
    "compliant": "✅",
    "partial": "⚠️",
    "non_compliant": "❌",
}
STATUS_KR = {
    "compliant": "Compliant",
    "partial": "Partial",
    "non_compliant": "Non-compliant",
}


def format_currency(val):
    if abs(val) >= 1e9:
        return f"${val/1e9:.1f}B"
    if abs(val) >= 1e6:
        return f"${val/1e6:.1f}M"
    return f"${val:,.0f}"


def format_emissions(val):
    if abs(val) >= 1e6:
        return f"{val/1e6:.1f}M tCO2e"
    if abs(val) >= 1e3:
        return f"{val/1e3:.0f}K tCO2e"
    return f"{val:,.0f} tCO2e"


# ── Page ──────────────────────────────────────────────────────────────
st.title("🏆 ESG Disclosure Readiness")
st.markdown("Checklist-based assessment for **TCFD**, **ISSB (IFRS S2)**, and **KSSB** frameworks.")

# ── Framework Tabs ────────────────────────────────────────────────────
tab_tcfd, tab_issb, tab_kssb = st.tabs(["TCFD", "ISSB (IFRS S2)", "KSSB"])

FRAMEWORKS = {
    "tcfd": ("TCFD", tab_tcfd),
    "issb": ("ISSB (IFRS S2)", tab_issb),
    "kssb": ("KSSB", tab_kssb),
}

for fw_id, (fw_label, tab) in FRAMEWORKS.items():
    with tab:
        with st.spinner(f"Assessing {fw_label}..."):
            assessment = assess_framework(fw_id)
            disclosure = get_disclosure_data(fw_id)

        # ── Checklist Summary Counts ──
        checklist = assessment["checklist"]
        n_compliant = sum(1 for c in checklist if c["status"] == "compliant")
        n_partial = sum(1 for c in checklist if c["status"] == "partial")
        n_non = sum(1 for c in checklist if c["status"] == "non_compliant")
        n_total = len(checklist)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Items", f"{n_total}")
        with col2:
            st.metric("✅ Compliant", f"{n_compliant}")
        with col3:
            st.metric("⚠️ Partial", f"{n_partial}")
        with col4:
            st.metric("❌ Non-compliant", f"{n_non}")

        st.divider()

        # ── Checklist ──
        st.markdown("#### Disclosure Requirements Checklist")
        for item in checklist:
            icon = STATUS_ICON.get(item["status"], "?")
            status_label = STATUS_KR.get(item["status"], "?")
            with st.expander(f"{icon} {item['item']} — **{status_label}**"):
                if item["recommendation"]:
                    st.warning(f"**Action Required:** {item['recommendation']}")
                else:
                    st.success("Requirement is met.")

        st.divider()

        # ── Regulatory Deadlines ──
        st.markdown("#### Regulatory Deadlines")
        deadlines = assessment.get("regulatory_deadlines", [])
        if deadlines:
            for dl in deadlines:
                try:
                    dl_date = datetime.strptime(dl["date"], "%Y-%m-%d").date()
                    days_left = (dl_date - date.today()).days
                    if days_left < 0:
                        badge = f"**D+{abs(days_left)}** (passed)"
                    else:
                        badge = f"**D-{days_left}**"
                except (ValueError, KeyError):
                    badge = "N/A"
                st.markdown(f"- {badge} — **{dl['name']}** ({dl['date']})")
                st.caption(f"  {dl['description']} | Source: {dl.get('source', 'N/A')}")
        else:
            st.info("No registered regulatory deadlines for this framework.")

        st.divider()

        # ── Disclosure Metrics ──
        st.markdown("#### Disclosure Metrics Summary")
        metrics = disclosure["metrics"]

        col_e, col_f, col_t = st.columns(3)
        with col_e:
            em = metrics["emissions"]
            st.markdown("**Emissions**")
            st.metric("Scope 1", format_emissions(em["scope1_tco2e"]))
            st.metric("Scope 2", format_emissions(em["scope2_tco2e"]))
            st.metric("Scope 3", format_emissions(em["scope3_tco2e"]))
            st.metric("Intensity", f'{em["intensity_tco2e_per_revenue"]:.1f} tCO2e/$M')
        with col_f:
            fi = metrics["financial_impact"]
            st.markdown("**Financial Impact**")
            st.metric("Transition Risk NPV", format_currency(fi["transition_risk_npv_net_zero"]))
            st.metric("Facilities", f'{fi["total_facilities"]}')
            st.metric("Total Assets", format_currency(fi["total_assets_at_risk"]))
        with col_t:
            tgt = metrics["targets"]
            st.markdown("**Targets**")
            st.metric("Base Year", str(tgt["base_year"]))
            st.metric("Target Year", str(tgt["target_year"]))
            st.metric("Reduction Target", f'{tgt["reduction_target_pct"]}%')
            st.metric("Science-Based", "Yes" if tgt["science_based"] else "No")
