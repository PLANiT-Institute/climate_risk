"""Smoke test: per-hazard data_source tracking and api_warnings.

Run from repo root:
    python sandbox/test_api_status.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.physical_risk import assess_physical_risk  # noqa: E402

# ── Test facilities ────────────────────────────────────────────────────
FACILITIES = [
    {
        "facility_id": "TEST_SEOUL",
        "name": "Seoul Test Asset",
        "location": "Seoul, South Korea",
        "latitude": 37.5665,
        "longitude": 126.978,
        "assets_value": 100_000_000_000,
        "annual_revenue": 1_000_000_000,
        "sector": "real_estate",
        "employees": 500,
    },
    {
        "facility_id": "TEST_BUSAN",
        "name": "Busan Test Asset",
        "location": "Busan, South Korea",
        "latitude": 35.1796,
        "longitude": 129.0756,
        "assets_value": 100_000_000_000,
        "annual_revenue": 1_000_000_000,
        "sector": "real_estate",
        "employees": 500,
    },
    {
        "facility_id": "TEST_JEJU",
        "name": "Jeju Test Asset",
        "location": "Jeju, South Korea",
        "latitude": 33.4996,
        "longitude": 126.5312,
        "assets_value": 100_000_000_000,
        "annual_revenue": 1_000_000_000,
        "sector": "real_estate",
        "employees": 500,
    },
]

_COL_W = 22


def _header() -> str:
    return (
        f"{'hazard_type':<{_COL_W}}"
        f"{'data_source':<{_COL_W}}"
        f"{'potential_loss':>{_COL_W}}"
        f"{'probability':>{_COL_W}}"
    )


def _row(h: dict) -> str:
    return (
        f"{h['hazard_type']:<{_COL_W}}"
        f"{h['data_source']:<{_COL_W}}"
        f"{h['potential_loss']:>{_COL_W},}"
        f"{h['probability']:>{_COL_W}.4f}"
    )


def _print_result(label: str, result: dict) -> None:
    print(f"\n{'=' * 88}")
    print(f"  {label}")
    print(f"{'=' * 88}")
    for fac_result in result["facilities"]:
        print(f"\n  Facility: {fac_result['facility_name']}  [{fac_result['facility_id']}]")
        print(f"  {'─' * 84}")
        print(f"  {_header()}")
        print(f"  {'─' * 84}")
        for h in fac_result["hazards"]:
            print(f"  {_row(h)}")
        print(f"  {'─' * 84}")
        warnings = fac_result.get("api_warnings", [])
        if warnings:
            print(f"  api_warnings ({len(warnings)}):")
            for w in warnings:
                print(f"    - {w}")
        else:
            print("  api_warnings: none")

    top_warnings = result.get("api_warnings", [])
    print(f"\n  Top-level api_warnings ({len(top_warnings)} unique):")
    for w in top_warnings:
        print(f"    - {w}")


def main() -> None:
    print("\nRunning assess_physical_risk with use_api_data=True ...")
    result_api = assess_physical_risk(
        scenario_id="current_policies",
        year=2030,
        use_api_data=True,
        facilities=FACILITIES,
    )
    _print_result("use_api_data=True  (scenario=current_policies, year=2030)", result_api)

    print("\n\nRunning assess_physical_risk with use_api_data=False ...")
    result_static = assess_physical_risk(
        scenario_id="current_policies",
        year=2030,
        use_api_data=False,
        facilities=FACILITIES,
    )
    _print_result("use_api_data=False (scenario=current_policies, year=2030)", result_static)

    # Verify all data_source == "static_config" when use_api_data=False
    all_static = all(
        h["data_source"] == "static_config"
        for r in result_static["facilities"]
        for h in r["hazards"]
    )
    print(f"\nAll hazards static_config when use_api_data=False: {all_static}")


if __name__ == "__main__":
    main()
