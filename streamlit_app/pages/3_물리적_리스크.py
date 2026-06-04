"""Page 3: Physical Risk Assessment — company-filtered hazard map, EAL, hazard details."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.helpers import (
    RISK_COLORS, SCENARIO_NAMES, COMPANY_NAMES_KR,
    format_currency, default_layout,
)
from utils.company_data import get_cached_physical, filter_physical_by_company

st.set_page_config(page_title="물리적 리스크", page_icon="🌊", layout="wide")

# ── Read global sidebar state ──
company = st.session_state.get("global_company", "K-Steel Corp")
scenario_id = st.session_state.get("global_scenario", "net_zero_2050")
year = st.session_state.get("global_year", 2030)

st.title("물리적 리스크 평가")
st.caption(f"{COMPANY_NAMES_KR.get(company, company)} | {SCENARIO_NAMES.get(scenario_id, scenario_id)} | {year}년")

# ── Run Assessment ──
with st.spinner("물리적 리스크 평가 중..."):
    full_result = get_cached_physical(scenario_id, year)
    result = filter_physical_by_company(full_result, company)

facs = result["facilities"]
risk_summary = result["overall_risk_summary"]

if not facs:
    st.warning("선택된 기업에 해당하는 시설이 없습니다.")
    st.stop()

# ── Summary KPIs ──
st.subheader(f"평가 결과 — {SCENARIO_NAMES[scenario_id]} ({year}년)")
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_eal = sum(f["total_expected_annual_loss"] for f in facs)
    st.metric("총 EAL", format_currency(total_eal))
with col2:
    st.metric("고위험", f'{risk_summary.get("High", 0)}개')
with col3:
    st.metric("중위험", f'{risk_summary.get("Medium", 0)}개')
with col4:
    st.metric("온난화", f'+{result["warming_above_preindustrial"]:.1f}°C')

st.info(
    "**데이터 소스 안내** | "
    "홍수·폭염·가뭄: 자산 좌표 기반 ERA5 기후 데이터 (Open-Meteo) 사용 — "
    "태풍·해수면 상승: 정적 권역 기반 모델 사용 (API 경로 미구현). "
    "두 유형은 데이터 출처가 다르므로 결과 비교 시 유의하세요.",
    icon="ℹ️",
)

st.divider()

# ── Risk Map ──
st.subheader("시설별 위험도 지도")

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
default_layout(fig_map, height=500)
fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig_map, use_container_width=True)

# ── EAL Table ──
st.subheader("시설별 예상연간손실(EAL)")

df_eal = pd.DataFrame([{
    "시설명": f["facility_name"],
    "위치": f["location"],
    "총 EAL": format_currency(f["total_expected_annual_loss"]),
    "위험등급": f["overall_risk_level"],
    "eal_raw": f["total_expected_annual_loss"],
} for f in facs]).sort_values("eal_raw", ascending=False)

st.dataframe(
    df_eal[["시설명", "위치", "총 EAL", "위험등급"]],
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ── Selected Facility Detail ──
st.subheader("시설 상세 — 재해별 분석")
fac_names = [f["facility_name"] for f in facs]
selected_name = st.selectbox("시설 선택", fac_names)
selected = next(f for f in facs if f["facility_name"] == selected_name)

# Strip any internal bookkeeping keys that the API layer may attach to hazard
# dicts (e.g. _cache_meta, _api_status from open_meteo.get_api_derived_baselines).
# These should not be present in hazard dicts per the current backend, but this
# guard ensures backward and forward compatibility if the schema ever drifts.
_INTERNAL_KEYS = {"_cache_meta", "_api_status"}

def _clean_hazard(h: dict) -> dict:
    """Return a copy of hazard dict with internal underscore keys removed."""
    return {k: v for k, v in h.items() if k not in _INTERNAL_KEYS}

hazards = [_clean_hazard(h) for h in selected["hazards"]]

# ── API Warnings ──────────────────────────────────────────────────────
_fac_warnings = selected.get("api_warnings", [])
if _fac_warnings:
    for _w in _fac_warnings:
        st.warning(f"데이터 소스 주의: {_w}", icon="⚠️")

# ── Hazard summary bar chart ──────────────────────────────────────────
_HAZARD_KO = {
    "flood": "홍수", "typhoon": "태풍", "heatwave": "폭염",
    "drought": "가뭄", "sea_level_rise": "해수면 상승",
}
haz_names = [_HAZARD_KO.get(h["hazard_type"], h["hazard_type"]) for h in hazards]
haz_losses = [h["potential_loss"] for h in hazards]
haz_colors = ["#3b82f6", "#8b5cf6", "#ef4444", "#f59e0b", "#06b6d4"]

fig_haz = go.Figure()
fig_haz.add_trace(go.Bar(
    x=haz_names,
    y=haz_losses,
    marker_color=haz_colors[:len(haz_names)],
    text=[format_currency(v) for v in haz_losses],
    textposition="outside",
))
default_layout(fig_haz, title=f"{selected_name} — 재해별 예상연간손실", height=400)
fig_haz.update_xaxes(title="재해 유형")
fig_haz.update_yaxes(title="EAL (USD)")
st.plotly_chart(fig_haz, use_container_width=True)

# ── Hazard detail table ───────────────────────────────────────────────
_SOURCE_LABEL = {
    "open_meteo_era5": "좌표 기반 (ERA5)",
    "static_config":   "정적 권역 기반",
}

df_hazard = pd.DataFrame([{
    "재해 유형": _HAZARD_KO.get(h["hazard_type"], h["hazard_type"]),
    "데이터 소스": _SOURCE_LABEL.get(h.get("data_source", "static_config"), h.get("data_source", "-")),
    "위험등급": h["risk_level"],
    "발생확률": f'{h["probability"]:.3f}',
    "예상손실": format_currency(h["potential_loss"]),
    "재현기간(년)": h["return_period_years"],
    "기후변화 배율": f'{h["climate_change_multiplier"]:.2f}x',
} for h in hazards])
st.dataframe(df_hazard, use_container_width=True, hide_index=True)

# ── Developer expander: cache metadata ───────────────────────────────
with st.expander("개발자 정보 — 데이터 소스 상세", expanded=False):
    st.caption("각 hazard의 원본 data_source 값과 캐시 히트 여부")
    dev_rows = []
    for h in hazards:
        raw_source = h.get("data_source", "unknown")
        dev_rows.append({
            "hazard_type": h["hazard_type"],
            "data_source (raw)": raw_source,
        })
    st.dataframe(pd.DataFrame(dev_rows), use_container_width=True, hide_index=True)

    # Top-level API warnings from the full result
    all_warnings = full_result.get("api_warnings", [])
    if all_warnings:
        st.caption("전체 api_warnings (전 시설 합산):")
        for w in all_warnings:
            st.code(w)
    else:
        st.caption("api_warnings: 없음 (모든 hazard가 정상 소스 사용)")

st.divider()

# ── Aggregate Hazard Chart (company level) ──
st.subheader("기업 전체 — 재해 유형별 총 EAL")

hazard_types = ["flood", "typhoon", "heatwave", "drought", "sea_level_rise"]
hazard_labels = {
    "flood": "홍수", "typhoon": "태풍", "heatwave": "폭염",
    "drought": "가뭄", "sea_level_rise": "해수면 상승",
}

agg = {ht: 0 for ht in hazard_types}
for f in facs:
    for h in f["hazards"]:
        h = _clean_hazard(h)
        if h["hazard_type"] in agg:
            agg[h["hazard_type"]] += h["potential_loss"]

fig_agg = go.Figure()
fig_agg.add_trace(go.Bar(
    x=[hazard_labels.get(ht, ht) for ht in hazard_types],
    y=[agg[ht] for ht in hazard_types],
    marker_color=haz_colors,
    text=[format_currency(agg[ht]) for ht in hazard_types],
    textposition="outside",
))
default_layout(fig_agg, title="재해 유형별 총 EAL (기업 합계)", height=400)
fig_agg.update_yaxes(title="총 EAL (USD)")
st.plotly_chart(fig_agg, use_container_width=True)
