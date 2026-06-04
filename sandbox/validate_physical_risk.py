"""Headless validation of physical risk service for Client RE Fund facilities.

Runs 8 programmatic checks without starting a browser:
  1. Import checks
  2. assess_physical_risk executes without error
  3. Required fields present (api_warnings, data_source)
  4. data_source values correct per hazard type
  5. api_warnings present for typhoon and sea_level_rise
  6. Top-level api_warnings present
  7. Cache effectiveness (second call < 1s)
  8. Static mode returns static_config for all hazards
"""

import sys
import os
import time

# backend must precede streamlit_app so that 'app' resolves to backend/app,
# not to streamlit_app/app.py (which is a module, not a package).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "streamlit_app"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# ── Check 1: Import checks ────────────────────────────────────────────
print("CHECK 1: Import checks")
from app.services.physical_risk import assess_physical_risk
from app.data.sample_facilities import get_all_facilities, get_facilities_by_company
print("  PASS -imports successful")

# ── Check 2: Run assess_physical_risk with Client RE Fund facilities ──
print("\nCHECK 2: assess_physical_risk with Client RE Fund facilities")
facilities = get_facilities_by_company("Client RE Fund")
assert len(facilities) > 0, "No Client RE Fund facilities found in sample_facilities"
print(f"  Facilities found: {[f['name'] for f in facilities]}")
result = assess_physical_risk("current_policies", 2030, use_api_data=True, facilities=facilities)
assert "facilities" in result
assert len(result["facilities"]) == len(facilities)
print(f"  PASS -assessed {len(result['facilities'])} facility(ies)")

# ── Check 3: Required fields present ──────────────────────────────────
print("\nCHECK 3: Required fields (api_warnings, data_source)")
for fac in result["facilities"]:
    assert "api_warnings" in fac, f"Missing api_warnings in {fac['facility_name']}"
    for h in fac["hazards"]:
        assert "data_source" in h, f"Missing data_source in {h['hazard_type']}"
        assert h["data_source"] in ("open_meteo_era5", "static_config"), (
            f"Invalid data_source value '{h['data_source']}' in {h['hazard_type']}"
        )
print("  PASS -all required fields present with valid values")

# ── Check 4: data_source values correct per hazard type ───────────────
print("\nCHECK 4: data_source values per hazard type")
EXPECTED_API = {"flood", "heatwave", "drought"}
EXPECTED_STATIC = {"typhoon", "sea_level_rise"}

# Note: API hazards fall back to static_config when Open-Meteo is unavailable.
# The assertion below verifies the INTENT: typhoon and sea_level_rise are
# always static_config (no API path exists for them); flood/heatwave/drought
# are open_meteo_era5 when API succeeds, static_config when it falls back.
for fac in result["facilities"]:
    for h in fac["hazards"]:
        ht = h["hazard_type"]
        ds = h["data_source"]
        if ht in EXPECTED_STATIC:
            assert ds == "static_config", (
                f"{fac['facility_name']} {ht}: expected static_config, got {ds}"
            )
        # API hazards: accept both (open_meteo_era5 if API up, static_config if down)
        if ht in EXPECTED_API:
            assert ds in ("open_meteo_era5", "static_config"), (
                f"{fac['facility_name']} {ht}: unexpected data_source '{ds}'"
            )
        print(f"  {fac['facility_name']:<25} {ht:<20} data_source={ds}")
print("  PASS -data_source values consistent with hazard type")

# ── Check 5: api_warnings for typhoon and sea_level_rise ─────────────
print("\nCHECK 5: api_warnings for typhoon and sea_level_rise")
for fac in result["facilities"]:
    warnings = fac.get("api_warnings", [])
    warning_hazards = {w.split(":")[0] for w in warnings}
    assert "typhoon" in warning_hazards, (
        f"{fac['facility_name']} missing typhoon api_warning. Got: {warnings}"
    )
    assert "sea_level_rise" in warning_hazards, (
        f"{fac['facility_name']} missing sea_level_rise api_warning. Got: {warnings}"
    )
    print(f"  {fac['facility_name']}: warnings={warnings}")
print("  PASS -typhoon and sea_level_rise warnings present for all facilities")

# ── Check 6: Top-level api_warnings ───────────────────────────────────
print("\nCHECK 6: Top-level api_warnings")
assert "api_warnings" in result, "Missing top-level api_warnings key"
assert len(result["api_warnings"]) > 0, (
    f"Top-level api_warnings is empty: {result['api_warnings']}"
)
print(f"  Top-level api_warnings ({len(result['api_warnings'])} entries):")
for w in result["api_warnings"]:
    print(f"    {w}")
print("  PASS")

# ── Check 7: Cache effectiveness ──────────────────────────────────────
print("\nCHECK 7: Cache effectiveness (second call < 1.0s)")
t0 = time.time()
result2 = assess_physical_risk("current_policies", 2030, use_api_data=True, facilities=facilities)
elapsed = time.time() - t0
print(f"  Second call elapsed: {elapsed:.3f}s")
assert elapsed < 1.0, (
    f"Second call took {elapsed:.3f}s -open_meteo cache not working"
)
print("  PASS")

# ── Check 8: Static mode ──────────────────────────────────────────────
print("\nCHECK 8: Static mode (use_api_data=False)")
result_static = assess_physical_risk("current_policies", 2030, use_api_data=False, facilities=facilities)
for fac in result_static["facilities"]:
    for h in fac["hazards"]:
        assert h["data_source"] == "static_config", (
            f"Static mode returned non-static for {fac['facility_name']} {h['hazard_type']}: "
            f"data_source={h['data_source']}"
        )
        print(f"  {fac['facility_name']:<25} {h['hazard_type']:<20} data_source={h['data_source']}")
print("  PASS -all hazards use static_config in static mode")

print("\n" + "=" * 60)
print("ALL 8 CHECKS PASSED")
print("=" * 60)
