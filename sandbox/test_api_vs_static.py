"""Comparison test: assess_physical_risk() with use_api_data=False vs True.

Runs each facility (Seoul, Busan, Jeju) through both modes, captures
wall-clock time, and prints a side-by-side table of hazard values and
% differences in potential_loss.

Also monkey-patches httpx.Client to detect whether a real HTTP request
was made during each call.
"""

import sys
import time
import unittest.mock as mock
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.physical_risk import assess_physical_risk  # noqa: E402

# ── Test facility definitions ────────────────────────────────────────────────
FACILITIES = [
    {
        "facility_id": "test_seoul",
        "name": "Seoul Test",
        "location": "Seoul",
        "latitude": 37.5665,
        "longitude": 126.9780,
        "sector": "real_estate",
        "assets_value": 100_000_000_000,
        "annual_revenue": 1_000_000_000,
    },
    {
        "facility_id": "test_busan",
        "name": "Busan Test",
        "location": "Busan",
        "latitude": 35.1796,
        "longitude": 129.0756,
        "sector": "real_estate",
        "assets_value": 100_000_000_000,
        "annual_revenue": 1_000_000_000,
    },
    {
        "facility_id": "test_jeju",
        "name": "Jeju Test",
        "location": "Jeju",
        "latitude": 33.4996,
        "longitude": 126.5312,
        "sector": "real_estate",
        "assets_value": 100_000_000_000,
        "annual_revenue": 1_000_000_000,
    },
]

TARGET_HAZARDS = ["flood", "heatwave", "drought"]
TARGET_FIELDS = ["probability", "potential_loss", "return_period_years", "climate_change_multiplier"]


def _extract_hazard_data(result: dict, facility_id: str) -> dict[str, dict]:
    """Extract target hazard fields for a given facility from assess result."""
    for fac in result["facilities"]:
        if fac["facility_id"] == facility_id:
            return {
                h["hazard_type"]: {f: h[f] for f in TARGET_FIELDS}
                for h in fac["hazards"]
                if h["hazard_type"] in TARGET_HAZARDS
            }
    return {}


def _pct_diff(a: float, b: float) -> str:
    """Percentage difference b relative to a. Returns '---' if a is zero."""
    if a == 0:
        return "---"
    return f"{(b - a) / abs(a) * 100:+.1f}%"


def _run_with_http_spy(use_api_data: bool, facilities: list) -> tuple[dict, float, list[str]]:
    """Run assess_physical_risk, measure wall time, capture HTTP calls."""
    http_calls: list[str] = []

    original_client_init = None

    class SpyClient:
        """Thin httpx.Client wrapper that logs GET calls."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._inner = original_httpx_client(*args, **kwargs)

        def __enter__(self) -> "SpyClient":
            self._inner.__enter__()
            return self

        def __exit__(self, *args: Any) -> None:
            self._inner.__exit__(*args)

        def get(self, url: str, **kwargs: Any) -> Any:
            http_calls.append(url)
            return self._inner.get(url, **kwargs)

    import httpx
    original_httpx_client = httpx.Client

    t0 = time.time()
    with mock.patch("httpx.Client", SpyClient):
        result = assess_physical_risk(
            scenario_id="current_policies",
            year=2030,
            use_api_data=use_api_data,
            facilities=facilities,
        )
    elapsed = time.time() - t0

    return result, elapsed, http_calls


def _divider(char: str = "-", width: int = 100) -> None:
    print(char * width)


def main() -> None:
    print()
    _divider("=")
    print("  assess_physical_risk()  --  API vs Static Comparison Test")
    print("  Scenario: current_policies  |  Year: 2030  |  Facilities: Seoul, Busan, Jeju")
    _divider("=")

    # Collect results for all facilities, both modes
    # Clear the open_meteo cache between runs so the API run actually fetches
    import app.services.open_meteo as om
    om._cache.clear()
    om._cache_ttl.clear()

    results: dict[str, dict] = {}

    print("\nRunning use_api_data=False (static config baselines) ...")
    static_result, static_time, static_http = _run_with_http_spy(
        use_api_data=False, facilities=FACILITIES
    )
    print(f"  Completed in {static_time:.3f}s  |  HTTP calls: {len(static_http)}")

    print("\nRunning use_api_data=True  (Open-Meteo API baselines) ...")
    api_result, api_time, api_http = _run_with_http_spy(
        use_api_data=True, facilities=FACILITIES
    )
    print(f"  Completed in {api_time:.3f}s  |  HTTP calls: {len(api_http)}")

    if api_http:
        print(f"  HTTP endpoints contacted:")
        for url in api_http:
            print(f"    GET {url}")
    else:
        print("  No HTTP requests detected (API may have failed / returned None).")

    # ── Per-facility hazard table ─────────────────────────────────────────
    for fac in FACILITIES:
        fid = fac["facility_id"]
        fname = fac["name"]

        static_hazards = _extract_hazard_data(static_result, fid)
        api_hazards = _extract_hazard_data(api_result, fid)

        print()
        _divider("-")
        print(f"  Facility: {fname}  (lat={fac['latitude']}, lon={fac['longitude']})")
        _divider("-")

        # Wall-clock time is per-run (same for all facilities in this batch),
        # but shown per-facility for reference
        print(f"  Static time (full run): {static_time:.3f}s   API time (full run): {api_time:.3f}s")
        print(f"  HTTP calls during static run: {len(static_http)}   during API run: {len(api_http)}")
        print()

        for hazard in TARGET_HAZARDS:
            s = static_hazards.get(hazard, {})
            a = api_hazards.get(hazard, {})

            if not s and not a:
                continue

            print(f"  [{hazard.upper()}]")
            header = f"    {'Field':<30} {'Static':>18} {'API':>18} {'Diff (loss %)':>16}"
            print(header)
            print(f"    {'-'*28} {'-'*18} {'-'*18} {'-'*16}")

            for field in TARGET_FIELDS:
                sv = s.get(field, "N/A")
                av = a.get(field, "N/A")

                if field == "potential_loss" and isinstance(sv, (int, float)) and isinstance(av, (int, float)):
                    diff_str = _pct_diff(float(sv), float(av))
                    sv_str = f"{sv:,.0f}"
                    av_str = f"{av:,.0f}"
                    print(f"    {field:<30} {sv_str:>18} {av_str:>18} {diff_str:>16}")
                else:
                    print(f"    {field:<30} {str(sv):>18} {str(av):>18} {'':>16}")

            print()

    # ── Summary ───────────────────────────────────────────────────────────
    _divider("=")
    print("  SUMMARY")
    _divider("-")
    print(f"  Static run (use_api_data=False)  -- total time: {static_time:.3f}s")
    print(f"  API run    (use_api_data=True)   -- total time: {api_time:.3f}s")
    print(f"  Speedup factor (static / api):   {api_time / static_time if static_time > 0 else 'N/A':.1f}x slower for API")
    print()
    print(f"  HTTP requests in static run: {len(static_http)}  (expected: 0)")
    print(f"  HTTP requests in API run:    {len(api_http)}  (expected: {len(FACILITIES)})")
    print()
    print(f"  data_source (static): {static_result.get('data_source')}")
    print(f"  data_source (api):    {api_result.get('data_source')}")
    _divider("=")
    print()


if __name__ == "__main__":
    main()
