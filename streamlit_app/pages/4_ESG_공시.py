"""Page 4: ESG Disclosure Readiness — checklist-based (no scores/gauges/radar).

Shows:
- Framework tabs (TCFD / ISSB / KSSB)
- Per-requirement checklist: compliant / partial / non_compliant
- Disclosure metric summary (Scope 1/2/3, intensity, NPV)
- Regulatory timeline (D-day)
"""

import streamlit as st
from datetime import date, datetime

from utils.helpers import (
    format_currency, format_emissions, compliance_icon, COMPANY_NAMES_KR,
)
from utils.company_data import get_cached_esg, get_cached_disclosure

st.set_page_config(page_title="ESG 공시", page_icon="📋", layout="wide")

# ── Read global sidebar state ──
company = st.session_state.get("global_company", "K-Steel Corp")

st.title("공시 준비도 체크리스트")
st.caption(f"{COMPANY_NAMES_KR.get(company, company)}")
st.markdown("TCFD, ISSB(IFRS S2), KSSB 기준의 공시 요건 **충족 여부**를 체크리스트로 평가합니다.")

# ── Framework Tabs ──
tab_tcfd, tab_issb, tab_kssb = st.tabs(["TCFD", "ISSB (IFRS S2)", "KSSB"])

_STATUS_KR = {
    "compliant": "충족",
    "partial": "부분충족",
    "non_compliant": "미충족",
}

FRAMEWORKS = {
    "tcfd": ("TCFD", tab_tcfd),
    "issb": ("ISSB (IFRS S2)", tab_issb),
    "kssb": ("KSSB", tab_kssb),
}

for fw_id, (fw_label, tab) in FRAMEWORKS.items():
    with tab:
        assessment = get_cached_esg(fw_id)
        disclosure = get_cached_disclosure(fw_id)

        # ── Checklist Summary Counts ──
        checklist = assessment["checklist"]
        n_compliant = sum(1 for c in checklist if c["status"] == "compliant")
        n_partial = sum(1 for c in checklist if c["status"] == "partial")
        n_non = sum(1 for c in checklist if c["status"] == "non_compliant")
        n_total = len(checklist)

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.metric("총 항목", f"{n_total}개")
        with col_s2:
            st.metric("충족", f"{n_compliant}개")
        with col_s3:
            st.metric("부분충족", f"{n_partial}개")
        with col_s4:
            st.metric("미충족", f"{n_non}개")

        st.divider()

        # ── Checklist ──
        st.markdown("#### 공시 요건 체크리스트")
        for item in checklist:
            icon = compliance_icon(item["status"])
            status_kr = _STATUS_KR.get(item["status"], "?")
            with st.expander(f"{icon} {item['item']} — **{status_kr}**"):
                if item["recommendation"]:
                    st.warning(f"**필요 조치:** {item['recommendation']}")
                else:
                    st.success("요구사항을 충족합니다.")

        st.divider()

        # ── Regulatory Deadlines ──
        st.markdown("#### 규제 일정")
        deadlines = assessment.get("regulatory_deadlines", [])
        if deadlines:
            for dl in deadlines:
                try:
                    dl_date = datetime.strptime(dl["date"], "%Y-%m-%d").date()
                    days_left = (dl_date - date.today()).days
                    if days_left < 0:
                        badge = f"**D+{abs(days_left)}** (경과)"
                    else:
                        badge = f"**D-{days_left}**"
                except (ValueError, KeyError):
                    badge = "N/A"
                st.markdown(f"- {badge} — **{dl['name']}** ({dl['date']})")
                st.caption(f"  {dl['description']} | 출처: {dl.get('source', 'N/A')}")
        else:
            st.info("해당 프레임워크에 등록된 규제 일정이 없습니다.")

        st.divider()

        # ── Disclosure Metrics ──
        st.markdown("#### 공시 지표 요약")
        metrics = disclosure["metrics"]

        col_e, col_f, col_t = st.columns(3)
        with col_e:
            em = metrics["emissions"]
            st.markdown("**배출량**")
            st.metric("Scope 1", format_emissions(em["scope1_tco2e"]))
            st.metric("Scope 2", format_emissions(em["scope2_tco2e"]))
            st.metric("Scope 3", format_emissions(em["scope3_tco2e"]))
            st.metric("배출 원단위", f'{em["intensity_tco2e_per_revenue"]:.1f} tCO2e/$M')
        with col_f:
            fi = metrics["financial_impact"]
            st.markdown("**재무 영향**")
            st.metric("전환 리스크 NPV", format_currency(fi["transition_risk_npv_net_zero"]))
            st.metric("총 시설 수", f'{fi["total_facilities"]}개')
            st.metric("총 자산", format_currency(fi["total_assets_at_risk"]))
        with col_t:
            tgt = metrics["targets"]
            st.markdown("**감축 목표**")
            st.metric("기준연도", str(tgt["base_year"]))
            st.metric("목표연도", str(tgt["target_year"]))
            st.metric("감축 목표", f'{tgt["reduction_target_pct"]}%')
            st.metric("SBTi 기반", "예" if tgt["science_based"] else "아니오")
