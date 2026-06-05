"""Sandbox: verify use_api_data=True default and show API vs static comparison.

Illustrative calculation using assumed facilities: Seoul, Busan, Jeju.
No production data is used. This script is for manual smoke-testing only.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.physical_risk import assess_physical_risk  # noqa: E402

# ---------------------------------------------------------------------------
# Test facilities (illustrative — not real asset data)
# ---------------------------------------------------------------------------
FACILITIES = [
    {
        "facility_id": "sandbox_seoul_01",
        "name": "Seoul Test Asset",
        "location": "Seoul",
        "latitude": 37.5665,
        "longitude": 126.9780,
        "assets_value": 100_000_000_000,
        "annual_revenue": 1_000_000_000,
        "sector": "real_estate",
        "current_emissions_scope1": 0,
        "current_emissions_scope2": 0,
    },
    {
        "facility_id": "sandbox_busan_01",
        "name": "Busan Test Asset",
        "location": "Busan",
        "latitude": 35.1796,
        "longitude": 129.0756,
        "assets_value": 100_000_000_000,
        "annual_revenue": 1_000_000_000,
        "sector": "real_estate",
        "current_emissions_scope1": 0,
        "current_emissions_scope2": 0,
    },
    {
        "facility_id": "sandbox_jeju_01",
        "name": "Jeju Test Asset",
        "location": "Jeju",
        "latitude": 33.4996,
        "longitude": 126.5312,
        "assets_value": 100_000_000_000,
        "annual_revenue": 1_000_000_000,
        "sector": "real_estate",
        "current_emissions_scope1": 0,
        "current_emissions_scope2": 0,
    },
]


def _print_hazard_table(label: str, result: dict) -> None:
    print(f"\n  --- {label} ---")
    header = f"  {'facility':<22} {'hazard':<16} {'data_source':<20} {'potential_loss':>18}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for fac in result["facilities"]:
        for h in fac["hazards"]:
            print(
                f"  {fac['facility_name']:<22} "
                f"{h['hazard_type']:<16} "
                f"{h['data_source']:<20} "
                f"{h['potential_loss']:>18,}"
            )


def main() -> None:
    scenario_id = "current_policies"
    year = 2030

    print("=" * 70)
    print("sandbox/test_api_default.py - API default smoke test")
    print("=" * 70)

    # ── Run 1: API (first call, no cache) ──────────────────────────────
    print("\n[1] assess_physical_risk(use_api_data=True) — first call (no cache)")
    t0 = time.perf_counter()
    result_api_1 = assess_physical_risk(
        scenario_id=scenario_id,
        year=year,
        use_api_data=True,
        facilities=FACILITIES,
    )
    t1 = time.perf_counter()
    first_api_run_s = t1 - t0
    print(f"  Completed in {first_api_run_s:.3f} s")
    _print_hazard_table("API run 1", result_api_1)

    # ── Run 2: API (second call, internal cache in open_meteo should help) ─
    print("\n[2] assess_physical_risk(use_api_data=True) — second call (cached)")
    t2 = time.perf_counter()
    result_api_2 = assess_physical_risk(
        scenario_id=scenario_id,
        year=year,
        use_api_data=True,
        facilities=FACILITIES,
    )
    t3 = time.perf_counter()
    second_api_run_s = t3 - t2
    print(f"  Completed in {second_api_run_s:.3f} s")
    _print_hazard_table("API run 2", result_api_2)

    # ── Run 3: Static ──────────────────────────────────────────────────
    print("\n[3] assess_physical_risk(use_api_data=False) — static config")
    t4 = time.perf_counter()
    result_static = assess_physical_risk(
        scenario_id=scenario_id,
        year=year,
        use_api_data=False,
        facilities=FACILITIES,
    )
    t5 = time.perf_counter()
    static_run_s = t5 - t4
    print(f"  Completed in {static_run_s:.3f} s")
    _print_hazard_table("Static", result_static)

    # ── Summary comparison table ───────────────────────────────────────
    print("\n\n" + "=" * 70)
    print("SUMMARY — API vs Static potential_loss by facility × hazard")
    print("=" * 70)
    header = (
        f"  {'facility':<22} {'hazard':<16} "
        f"{'static_loss':>16} {'api_loss':>16} {'diff_pct':>10}"
    )
    print(header)
    print("  " + "-" * (len(header) - 2))

    # Index static losses for quick lookup
    static_index: dict[tuple[str, str], int] = {}
    for fac in result_static["facilities"]:
        for h in fac["hazards"]:
            static_index[(fac["facility_id"], h["hazard_type"])] = h["potential_loss"]

    for fac in result_api_1["facilities"]:
        for h in fac["hazards"]:
            key = (fac["facility_id"], h["hazard_type"])
            s_loss = static_index.get(key, 0)
            a_loss = h["potential_loss"]
            if s_loss != 0:
                diff_pct = (a_loss - s_loss) / abs(s_loss) * 100
                diff_str = f"{diff_pct:+.1f}%"
            elif a_loss == 0:
                diff_str = "0.0%"
            else:
                diff_str = "n/a"
            print(
                f"  {fac['facility_name']:<22} "
                f"{h['hazard_type']:<16} "
                f"{s_loss:>16,} "
                f"{a_loss:>16,} "
                f"{diff_str:>10}"
            )

    # ── Timing summary ─────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("TIMING SUMMARY")
    print("=" * 70)
    print(f"  first_api_run_s   : {first_api_run_s:.3f} s")
    print(f"  second_api_run_s  : {second_api_run_s:.3f} s  (cached, open_meteo in-process)")
    print(f"  static_run_s      : {static_run_s:.3f} s")

    # ── API warnings ──────────────────────────────────────────────────
    if result_api_1.get("api_warnings"):
        print("\nAPI warnings (run 1):")
        for w in result_api_1["api_warnings"]:
            print(f"  WARNING: {w}")
    else:
        print("\nNo API warnings — all hazards used open_meteo_era5 where applicable.")

    print("\nDone.")


if __name__ == "__main__":
    main()
