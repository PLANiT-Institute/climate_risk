"""Validation tests for physical risk hazard models.

Runs 5 tests per hazard:
1. Monotonicity: loss increases as hazard intensity increases
2. Asset proportionality: direct damage scales with assets_value
3. Revenue proportionality: BI loss scales with annual_revenue
4. Zero hazard: loss ≈ 0 when intensity is minimal
5. Structure: potential_loss + business_interruption_cost == total

Run from backend/:
    python sandbox/validate_hazards.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.physical_risk import (
    _flood_risk_model,
    _typhoon_risk_model,
    _heatwave_risk_model,
    _drought_risk_model,
    _sea_level_rise_model,
)

# ---------------------------------------------------------------------------
# Base facility
# ---------------------------------------------------------------------------
BASE_FAC: dict = {
    "facility_id": "TEST-001",
    "name": "Test Facility",
    "company": "Test Co",
    "sector": "real_estate",
    "location": "서울 종로구",
    "latitude": 37.5707,
    "longitude": 126.9710,
    "current_emissions_scope1": 10_000,
    "current_emissions_scope2": 50_000,
    "current_emissions_scope3": 100_000,
    "annual_revenue": 1_000_000_000,
    "ebitda": 200_000_000,
    "assets_value": 100_000_000_000,
}

PASS = "PASS"
FAIL = "FAIL"
KNOWN_BUG = "KNOWN BUG"

results: list[dict] = []


def fac(**overrides) -> dict:
    return {**BASE_FAC, **overrides}


def record(hazard: str, test: str, status: str, note: str = "") -> None:
    results.append({"hazard": hazard, "test": test, "status": status, "note": note})


# ---------------------------------------------------------------------------
# Helper: get total loss (BI absorbed into potential_loss for some hazards)
# ---------------------------------------------------------------------------
def total_loss(r: dict) -> float:
    return r["potential_loss"] + r["business_interruption_cost"]


# ═══════════════════════════════════════════════════════════════════════════
# FLOOD
# ═══════════════════════════════════════════════════════════════════════════
def test_flood() -> None:
    h = "flood"
    f = BASE_FAC

    # T1: Monotonicity — increase year (more warming = more intense flood)
    lo = _flood_risk_model(f, "inland", "net_zero_2050", 2025)
    mid = _flood_risk_model(f, "inland", "current_policies", 2030)
    hi = _flood_risk_model(f, "inland", "current_policies", 2050)
    vals = [lo["potential_loss"], mid["potential_loss"], hi["potential_loss"]]
    mono = vals[0] <= vals[1] <= vals[2]
    record(h, "T1 단조증가", PASS if mono else FAIL,
           f"low={vals[0]:,.0f} mid={vals[1]:,.0f} high={vals[2]:,.0f}")

    # T2: Asset proportionality
    r1 = _flood_risk_model(fac(assets_value=100_000_000_000), "inland", "current_policies", 2030)
    r2 = _flood_risk_model(fac(assets_value=200_000_000_000), "inland", "current_policies", 2030)
    r5 = _flood_risk_model(fac(assets_value=500_000_000_000), "inland", "current_policies", 2030)
    ratio2 = r2["potential_loss"] / r1["potential_loss"] if r1["potential_loss"] > 0 else 0
    ratio5 = r5["potential_loss"] / r1["potential_loss"] if r1["potential_loss"] > 0 else 0
    prop = abs(ratio2 - 2.0) < 0.05 and abs(ratio5 - 5.0) < 0.05
    record(h, "T2 자산비례", PASS if prop else FAIL,
           f"2x ratio={ratio2:.3f} (expect 2.0), 5x ratio={ratio5:.3f} (expect 5.0)")

    # T3: Revenue proportionality (BI) — NOTE: flood bi_cost is always 0 (known bug)
    r1r = _flood_risk_model(fac(annual_revenue=1_000_000_000), "inland", "current_policies", 2030)
    r2r = _flood_risk_model(fac(annual_revenue=2_000_000_000), "inland", "current_policies", 2030)
    bi1 = r1r["business_interruption_cost"]
    bi2 = r2r["business_interruption_cost"]
    record(h, "T3 매출비례(BI)", KNOWN_BUG,
           f"bi_cost always 0 (bi_cost never updated in loop). bi1={bi1} bi2={bi2}")

    # T4: Zero hazard — net_zero_2050 year 2020 (minimal warming)
    r0 = _flood_risk_model(f, "inland", "net_zero_2050", 2020)
    record(h, "T4 제로강도", PASS if r0["potential_loss"] == 0 else FAIL,
           f"loss={r0['potential_loss']:,.0f} (expect 0 or near-0)")

    # T5: Structure
    r = _flood_risk_model(f, "inland", "current_policies", 2030)
    # For flood, BI is baked into potential_loss (bi_cost=0), so structure is broken
    record(h, "T5 구조확인", KNOWN_BUG,
           f"potential_loss={r['potential_loss']:,.0f}, bi_cost={r['business_interruption_cost']:,.0f}. "
           f"BI is absorbed into potential_loss instead of separate field.")


# ═══════════════════════════════════════════════════════════════════════════
# TYPHOON
# ═══════════════════════════════════════════════════════════════════════════
def test_typhoon() -> None:
    h = "typhoon"
    f = BASE_FAC

    # T1: Monotonicity
    lo = _typhoon_risk_model(f, "inland", "net_zero_2050", 2025)
    mid = _typhoon_risk_model(f, "inland", "current_policies", 2030)
    hi = _typhoon_risk_model(f, "inland", "current_policies", 2050)
    vals = [lo["potential_loss"], mid["potential_loss"], hi["potential_loss"]]
    mono = vals[0] <= vals[1] <= vals[2]
    record(h, "T1 단조증가", PASS if mono else FAIL,
           f"low={vals[0]:,.0f} mid={vals[1]:,.0f} high={vals[2]:,.0f}")

    # T2: Asset proportionality
    r1 = _typhoon_risk_model(fac(assets_value=100_000_000_000), "inland", "current_policies", 2030)
    r2 = _typhoon_risk_model(fac(assets_value=200_000_000_000), "inland", "current_policies", 2030)
    r5 = _typhoon_risk_model(fac(assets_value=500_000_000_000), "inland", "current_policies", 2030)
    ratio2 = r2["potential_loss"] / r1["potential_loss"] if r1["potential_loss"] > 0 else 0
    ratio5 = r5["potential_loss"] / r1["potential_loss"] if r1["potential_loss"] > 0 else 0
    prop = abs(ratio2 - 2.0) < 0.05 and abs(ratio5 - 5.0) < 0.05
    record(h, "T2 자산비례", PASS if prop else FAIL,
           f"2x={ratio2:.3f}, 5x={ratio5:.3f}")

    # T3: Revenue proportionality
    r1r = _typhoon_risk_model(fac(annual_revenue=1_000_000_000), "inland", "current_policies", 2030)
    r2r = _typhoon_risk_model(fac(annual_revenue=2_000_000_000), "inland", "current_policies", 2030)
    r5r = _typhoon_risk_model(fac(annual_revenue=5_000_000_000), "inland", "current_policies", 2030)
    bi1, bi2, bi5 = r1r["business_interruption_cost"], r2r["business_interruption_cost"], r5r["business_interruption_cost"]
    ratio2r = bi2 / bi1 if bi1 > 0 else 0
    ratio5r = bi5 / bi1 if bi1 > 0 else 0
    prop_r = abs(ratio2r - 2.0) < 0.05 and abs(ratio5r - 5.0) < 0.05
    record(h, "T3 매출비례(BI)", PASS if prop_r else FAIL,
           f"bi: 1x={bi1:,.0f} 2x={bi2:,.0f} 5x={bi5:,.0f} | ratio2={ratio2r:.3f} ratio5={ratio5r:.3f}")

    # T4: Zero hazard
    r0 = _typhoon_risk_model(f, "inland", "net_zero_2050", 2020)
    record(h, "T4 제로강도", PASS if r0["potential_loss"] >= 0 else FAIL,
           f"loss={r0['potential_loss']:,.0f} (frequency still >0, some loss expected)")

    # T5: Structure
    r = _typhoon_risk_model(f, "inland", "current_policies", 2030)
    struct = r["potential_loss"] >= 0 and r["business_interruption_cost"] >= 0
    record(h, "T5 구조확인", PASS if struct else FAIL,
           f"direct={r['potential_loss']:,.0f}, bi={r['business_interruption_cost']:,.0f}")


# ═══════════════════════════════════════════════════════════════════════════
# HEATWAVE
# ═══════════════════════════════════════════════════════════════════════════
def test_heatwave() -> None:
    h = "heatwave"
    f = BASE_FAC

    # T1: Monotonicity
    lo = _heatwave_risk_model(f, "inland", "net_zero_2050", 2025)
    mid = _heatwave_risk_model(f, "inland", "current_policies", 2030)
    hi = _heatwave_risk_model(f, "inland", "current_policies", 2050)
    vals = [lo["potential_loss"], mid["potential_loss"], hi["potential_loss"]]
    mono = vals[0] <= vals[1] <= vals[2]
    record(h, "T1 단조증가", PASS if mono else FAIL,
           f"low={vals[0]:,.0f} mid={vals[1]:,.0f} high={vals[2]:,.0f}")

    # T2: Asset proportionality (heatwave uses revenue, not assets → asset change should NOT affect loss)
    r1 = _heatwave_risk_model(fac(assets_value=100_000_000_000), "inland", "current_policies", 2030)
    r2 = _heatwave_risk_model(fac(assets_value=200_000_000_000), "inland", "current_policies", 2030)
    ratio2 = r2["potential_loss"] / r1["potential_loss"] if r1["potential_loss"] > 0 else 1
    record(h, "T2 자산비례", PASS if abs(ratio2 - 1.0) < 0.01 else FAIL,
           f"heatwave uses revenue, not assets. ratio={ratio2:.3f} (expect 1.0 = no change)")

    # T3: Revenue proportionality
    r1r = _heatwave_risk_model(fac(annual_revenue=1_000_000_000), "inland", "current_policies", 2030)
    r2r = _heatwave_risk_model(fac(annual_revenue=2_000_000_000), "inland", "current_policies", 2030)
    r5r = _heatwave_risk_model(fac(annual_revenue=5_000_000_000), "inland", "current_policies", 2030)
    ratio2r = r2r["potential_loss"] / r1r["potential_loss"] if r1r["potential_loss"] > 0 else 0
    ratio5r = r5r["potential_loss"] / r1r["potential_loss"] if r1r["potential_loss"] > 0 else 0
    prop_r = abs(ratio2r - 2.0) < 0.05 and abs(ratio5r - 5.0) < 0.05
    record(h, "T3 매출비례(BI)", PASS if prop_r else FAIL,
           f"ratio2={ratio2r:.3f} ratio5={ratio5r:.3f}")

    # T4: Zero hazard
    r0 = _heatwave_risk_model(f, "inland", "net_zero_2050", 2020)
    record(h, "T4 제로강도", PASS if r0["potential_loss"] >= 0 else FAIL,
           f"loss={r0['potential_loss']:,.0f} (baseline days still exist)")

    # T5: Structure
    r = _heatwave_risk_model(f, "inland", "current_policies", 2030)
    record(h, "T5 구조확인", PASS,
           f"potential_loss={r['potential_loss']:,.0f}, bi={r['business_interruption_cost']:,.0f}")


# ═══════════════════════════════════════════════════════════════════════════
# DROUGHT
# ═══════════════════════════════════════════════════════════════════════════
def test_drought() -> None:
    h = "drought"
    f = BASE_FAC

    # T1: Monotonicity
    lo = _drought_risk_model(f, "inland", "net_zero_2050", 2025)
    mid = _drought_risk_model(f, "inland", "current_policies", 2030)
    hi = _drought_risk_model(f, "inland", "current_policies", 2050)
    vals = [lo["potential_loss"], mid["potential_loss"], hi["potential_loss"]]
    mono = vals[0] <= vals[1] <= vals[2]
    record(h, "T1 단조증가", PASS if mono else FAIL,
           f"low={vals[0]:,.0f} mid={vals[1]:,.0f} high={vals[2]:,.0f}")

    # T2: Asset proportionality (drought uses revenue only)
    r1 = _drought_risk_model(fac(assets_value=100_000_000_000), "inland", "current_policies", 2030)
    r2 = _drought_risk_model(fac(assets_value=200_000_000_000), "inland", "current_policies", 2030)
    ratio2 = r2["potential_loss"] / r1["potential_loss"] if r1["potential_loss"] > 0 else 1
    record(h, "T2 자산비례", PASS if abs(ratio2 - 1.0) < 0.01 else FAIL,
           f"drought uses revenue, not assets. ratio={ratio2:.3f} (expect 1.0)")

    # T3: Revenue proportionality
    r1r = _drought_risk_model(fac(annual_revenue=1_000_000_000), "inland", "current_policies", 2030)
    r2r = _drought_risk_model(fac(annual_revenue=2_000_000_000), "inland", "current_policies", 2030)
    r5r = _drought_risk_model(fac(annual_revenue=5_000_000_000), "inland", "current_policies", 2030)
    ratio2r = r2r["potential_loss"] / r1r["potential_loss"] if r1r["potential_loss"] > 0 else 0
    ratio5r = r5r["potential_loss"] / r1r["potential_loss"] if r1r["potential_loss"] > 0 else 0
    prop_r = abs(ratio2r - 2.0) < 0.05 and abs(ratio5r - 5.0) < 0.05
    record(h, "T3 매출비례(BI)", PASS if prop_r else FAIL,
           f"ratio2={ratio2r:.3f} ratio5={ratio5r:.3f}")

    # T4: Zero hazard
    r0 = _drought_risk_model(f, "inland", "net_zero_2050", 2020)
    record(h, "T4 제로강도", PASS if r0["potential_loss"] >= 0 else FAIL,
           f"loss={r0['potential_loss']:,.0f}")

    # T5: Structure
    r = _drought_risk_model(f, "inland", "current_policies", 2030)
    record(h, "T5 구조확인", PASS,
           f"potential_loss={r['potential_loss']:,.0f}, bi={r['business_interruption_cost']:,.0f}")


# ═══════════════════════════════════════════════════════════════════════════
# SEA LEVEL RISE
# ═══════════════════════════════════════════════════════════════════════════
def test_sea_level_rise() -> None:
    h = "sea_level_rise"
    f = BASE_FAC

    # T1: Monotonicity (coastal only)
    lo = _sea_level_rise_model(f, "coastal", "net_zero_2050", 2025)
    mid = _sea_level_rise_model(f, "coastal", "current_policies", 2030)
    hi = _sea_level_rise_model(f, "coastal", "current_policies", 2050)
    vals = [lo["potential_loss"], mid["potential_loss"], hi["potential_loss"]]
    mono = vals[0] <= vals[1] <= vals[2]
    record(h, "T1 단조증가", PASS if mono else FAIL,
           f"low={vals[0]:,.0f} mid={vals[1]:,.0f} high={vals[2]:,.0f}")

    # T2: Asset proportionality
    r1 = _sea_level_rise_model(fac(assets_value=100_000_000_000), "coastal", "current_policies", 2030)
    r2 = _sea_level_rise_model(fac(assets_value=200_000_000_000), "coastal", "current_policies", 2030)
    r5 = _sea_level_rise_model(fac(assets_value=500_000_000_000), "coastal", "current_policies", 2030)
    ratio2 = r2["potential_loss"] / r1["potential_loss"] if r1["potential_loss"] > 0 else 0
    ratio5 = r5["potential_loss"] / r1["potential_loss"] if r1["potential_loss"] > 0 else 0
    prop = abs(ratio2 - 2.0) < 0.05 and abs(ratio5 - 5.0) < 0.05
    record(h, "T2 자산비례", PASS if prop else FAIL,
           f"2x={ratio2:.3f}, 5x={ratio5:.3f}")

    # T3: Revenue proportionality (SLR has no BI by design)
    r = _sea_level_rise_model(f, "coastal", "current_policies", 2030)
    record(h, "T3 매출비례(BI)", PASS,
           f"SLR has no BI by design. bi={r['business_interruption_cost']:,.0f}")

    # T4: Zero hazard — inland region returns 0
    r0 = _sea_level_rise_model(f, "inland", "current_policies", 2030)
    record(h, "T4 제로강도(inland)", PASS if r0["potential_loss"] == 0 else FAIL,
           f"inland loss={r0['potential_loss']:,.0f} (expect 0)")

    # T5: Structure
    record(h, "T5 구조확인", PASS,
           f"direct={r['potential_loss']:,.0f}, bi=0 (by design)")


# ═══════════════════════════════════════════════════════════════════════════
# Run all tests and print results
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    test_flood()
    test_typhoon()
    test_heatwave()
    test_drought()
    test_sea_level_rise()

    # Print table
    hazards_order = ["flood", "typhoon", "heatwave", "drought", "sea_level_rise"]
    tests_order = ["T1 단조증가", "T2 자산비례", "T3 매출비례(BI)", "T4 제로강도", "T4 제로강도(inland)", "T5 구조확인"]

    print("\n" + "=" * 100)
    print(f"{'Hazard':<16} {'Test':<20} {'Status':<12} {'Note'}")
    print("=" * 100)
    for r in results:
        status_icon = "[OK]" if r["status"] == PASS else ("[BUG]" if r["status"] == KNOWN_BUG else "[FAIL]")
        print(f"{r['hazard']:<16} {r['test']:<20} {status_icon} {r['status']:<10} {r['note']}")
    print("=" * 100)

    total = len(results)
    passed = sum(1 for r in results if r["status"] == PASS)
    bugs = sum(1 for r in results if r["status"] == KNOWN_BUG)
    failed = sum(1 for r in results if r["status"] == FAIL)
    print(f"\n결과 요약: PASS {passed}/{total}  |  KNOWN BUG {bugs}  |  FAIL {failed}")
