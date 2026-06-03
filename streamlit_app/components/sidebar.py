"""Global sidebar component shared across all pages."""

import sys
import os

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from app.data.sample_facilities import get_company_list
from utils.helpers import COMPANY_NAMES_KR, SCENARIO_NAMES


def render_global_sidebar() -> None:
    """Render the global sidebar with company/scenario/pricing/year selectors."""
    companies = get_company_list()
    with st.sidebar:
        st.markdown("### 기후리스크 공시 도구")
        st.divider()
        st.selectbox(
            "기업 선택",
            options=companies,
            format_func=lambda c: COMPANY_NAMES_KR.get(c, c),
            key="global_company",
        )
        st.selectbox(
            "NGFS 시나리오",
            options=["net_zero_2050", "below_2c", "delayed_transition", "current_policies"],
            format_func=lambda x: SCENARIO_NAMES.get(x, x),
            key="global_scenario",
        )
        st.radio(
            "탄소가격 체계",
            options=["kets", "global"],
            format_func=lambda x: "K-ETS (한국 배출권거래제)" if x == "kets" else "글로벌 탄소가격",
            key="global_pricing",
        )
        st.slider(
            "평가 연도",
            min_value=2025, max_value=2050, value=2030, step=5,
            key="global_year",
        )
        st.divider()
        st.caption("Backend: FastAPI analytical services (direct import)")
        st.caption("Model: analytical_v1")
