import sys
# backend must come first so 'app' resolves to backend/app, not streamlit_app/app.py
sys.path.insert(0, 'backend')
# streamlit_app appended last to avoid shadowing backend packages
sys.path.append('streamlit_app')

from app.services.physical_risk import assess_physical_risk
from app.data.sample_facilities import get_facilities_by_company, get_all_facilities
import pandas as pd

company = "Client RE Fund"
scenario_id = "current_policies"
year = 2030

# Simulate get_cached_physical (which now calls use_api_data=True by default)
full_result = assess_physical_risk(scenario_id, year, use_api_data=True)

# Simulate filter_physical_by_company
company_facility_ids = {f["facility_id"] for f in get_facilities_by_company(company)}
facs = [f for f in full_result["facilities"] if f.get("facility_id") in company_facility_ids]

print("=== Facility keys ===")
print(list(facs[0].keys()))

print("\n=== Hazard keys (first hazard) ===")
print(list(facs[0]["hazards"][0].keys()))

print("\n=== Map DataFrame build ===")
try:
    df_map = pd.DataFrame([{
        "name": f["facility_name"],
        "latitude": f["latitude"],
        "longitude": f["longitude"],
        "location": f["location"],
        "risk_level": f["overall_risk_level"],
        "total_eal": f["total_expected_annual_loss"],
    } for f in facs])
    print("OK")
    print(df_map)
except Exception as e:
    print(f"ERROR: {e}")

print("\n=== Hazard table build ===")
_HAZARD_KO = {
    "flood": "홍수", "typhoon": "태풍", "heatwave": "폭염",
    "drought": "가뭄", "sea_level_rise": "해수면 상승",
}
_SOURCE_LABEL = {
    "open_meteo_era5": "좌표 기반 (ERA5)",
    "static_config": "정적 권역 기반",
}
selected = facs[0]
hazards = selected["hazards"]
try:
    df_hazard = pd.DataFrame([{
        "재해 유형": _HAZARD_KO.get(h["hazard_type"], h["hazard_type"]),
        "데이터 소스": _SOURCE_LABEL.get(h.get("data_source", "static_config"), h.get("data_source", "-")),
        "위험등급": h["risk_level"],
        "발생확률": f'{h["probability"]:.3f}',
        "예상손실": h["potential_loss"],
        "재현기간(년)": h["return_period_years"],
        "기후변화 배율": f'{h["climate_change_multiplier"]:.2f}x',
    } for h in hazards])
    print("OK")
    print(df_hazard)
except Exception as e:
    print(f"ERROR: {e}")

print("\n=== api_warnings render ===")
try:
    warnings = selected.get("api_warnings", [])
    for w in warnings:
        print(f"WARNING: {w}")
    print("OK")
except Exception as e:
    print(f"ERROR: {e}")

print("\n=== EAL table build ===")
try:
    df_eal = pd.DataFrame([{
        "시설명": f["facility_name"],
        "위치": f["location"],
        "총 EAL": f["total_expected_annual_loss"],
        "위험등급": f["overall_risk_level"],
        "eal_raw": f["total_expected_annual_loss"],
    } for f in facs]).sort_values("eal_raw", ascending=False)
    print("OK")
    print(df_eal)
except Exception as e:
    print(f"ERROR: {e}")
