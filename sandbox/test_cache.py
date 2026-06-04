"""Cache hit/miss and timing test for Open-Meteo baselines.

Run from repo root:
    python sandbox/test_cache.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")

from app.services.open_meteo import get_api_derived_baselines, get_cache_stats

ASSETS = [
    ("Seoul",  37.5665, 126.9780),
    ("Busan",  35.1796, 129.0756),
    ("Jeju",   33.4996, 126.5312),
]

SEP = "-" * 72

def run_pass(label: str) -> list[dict]:
    print(f"\n{'='*72}")
    print(f"  {label}")
    print('='*72)
    rows = []
    for name, lat, lon in ASSETS:
        t0 = time.time()
        result = get_api_derived_baselines(lat, lon)
        elapsed = time.time() - t0

        if result is None:
            cache_hit = "N/A (API failed)"
            source = "FAILED"
        else:
            meta = result.get("_cache_meta", {})
            cache_hit = "HIT" if meta.get("cache_hit") else "MISS"
            source = "open_meteo_era5"

        rows.append({"asset": name, "cache": cache_hit, "source": source, "time_s": elapsed})
        print(f"  {name:<8}  cache={cache_hit:<25}  source={source:<18}  time={elapsed:.3f}s")
    return rows


# ── Pass 1: cold cache (all misses expected) ─────────────────────────
stats_before = get_cache_stats()
rows1 = run_pass("Pass 1 - Cold cache (expect all MISS, API calls)")
stats_after1 = get_cache_stats()

# -- Pass 2: warm cache (all hits expected) ---------------------------
rows2 = run_pass("Pass 2 - Warm cache (expect all HIT, no API calls)")
stats_after2 = get_cache_stats()

# ── Summary ──────────────────────────────────────────────────────────
print(f"\n{'='*72}")
print("  SUMMARY")
print('='*72)
print(f"  {'Asset':<8}  {'Pass1 time':>12}  {'Pass2 time':>12}  {'Speedup':>10}  {'Pass1 cache':>12}  {'Pass2 cache':>12}")
print(f"  {SEP}")
for r1, r2 in zip(rows1, rows2):
    speedup = r1["time_s"] / r2["time_s"] if r2["time_s"] > 0 else float("inf")
    print(
        f"  {r1['asset']:<8}  {r1['time_s']:>11.3f}s  {r2['time_s']:>11.3f}s  "
        f"{speedup:>9.0f}x  {r1['cache']:>12}  {r2['cache']:>12}"
    )

print()
print(f"  Cache stats after Pass 1: hits={stats_after1['hits']}  misses={stats_after1['misses']}")
print(f"  Cache stats after Pass 2: hits={stats_after2['hits']}  misses={stats_after2['misses']}")
print(f"  Expected: Pass2 hits = {len(ASSETS)}  (one per asset)")
print()
all_hit_pass2 = all(r["cache"] == "HIT" for r in rows2)
print(f"  All Pass2 cache=HIT: {all_hit_pass2}")
