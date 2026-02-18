"""Open-Meteo Historical Weather API client + statistical derivation.

Fetches 30-year daily weather data and derives climate baselines for
physical risk models (Gumbel params, heatwave days, drought days, wind speed).

API: https://archive-api.open-meteo.com/v1/archive
Reference: Open-Meteo (2024), open-source weather API.
"""

import math
import time
import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────
_API_BASE = "https://archive-api.open-meteo.com/v1/archive"
_START_DATE = "1994-01-01"
_END_DATE = "2023-12-31"
_DAILY_VARS = "temperature_2m_max,precipitation_sum,wind_speed_10m_max"
_TIMEZONE = "Asia/Seoul"
_TIMEOUT = 30.0  # seconds
_MIN_YEARS = 5  # minimum years of data required
_HEATWAVE_THRESHOLD_C = 33.0  # KMA heatwave definition

# ── In-Memory Cache (1-hour TTL, ~1km grouping) ──────────────────────
_cache: Dict[str, dict] = {}
_cache_ttl: Dict[str, float] = {}
_CACHE_TTL_SECONDS = 3600.0  # 1 hour


def _cache_key(lat: float, lon: float) -> str:
    """Round to 2 decimals (~1km grouping) for cache key."""
    return f"{round(lat, 2)},{round(lon, 2)}"


def _cache_get(key: str) -> Optional[dict]:
    if key in _cache and (time.time() - _cache_ttl.get(key, 0)) < _CACHE_TTL_SECONDS:
        return _cache[key]
    # Expired — remove
    _cache.pop(key, None)
    _cache_ttl.pop(key, None)
    return None


def _cache_set(key: str, value: dict) -> None:
    _cache[key] = value
    _cache_ttl[key] = time.time()


# ── API Fetch ─────────────────────────────────────────────────────────
def fetch_historical_weather(
    lat: float, lon: float,
) -> Optional[Dict[str, List]]:
    """Fetch 30-year daily weather data from Open-Meteo Archive API.

    Returns:
        {"temperature_2m_max": [...], "precipitation_sum": [...],
         "wind_speed_10m_max": [...], "time": [...]}
        or None on failure.
    """
    params = {
        "latitude": round(lat, 2),
        "longitude": round(lon, 2),
        "start_date": _START_DATE,
        "end_date": _END_DATE,
        "daily": _DAILY_VARS,
        "timezone": _TIMEZONE,
    }

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(_API_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()

        daily = data.get("daily")
        if not daily:
            logger.warning("Open-Meteo returned no daily data for (%s, %s)", lat, lon)
            return None

        return {
            "temperature_2m_max": daily.get("temperature_2m_max", []),
            "precipitation_sum": daily.get("precipitation_sum", []),
            "wind_speed_10m_max": daily.get("wind_speed_10m_max", []),
            "time": daily.get("time", []),
        }

    except (httpx.HTTPError, httpx.TimeoutException, Exception) as e:
        logger.warning("Open-Meteo API error for (%s, %s): %s", lat, lon, e)
        return None


# ── Statistical Derivation Functions ──────────────────────────────────
def derive_gumbel_params(daily_precip: List[Optional[float]]) -> Optional[Dict[str, float]]:
    """Fit Gumbel Type I parameters from daily precipitation data.

    Method: Extract annual maxima, then Method of Moments.
    μ = mean - 0.5772 * σ_gumbel
    σ_gumbel = std * sqrt(6) / π

    Reference: Coles (2001), An Introduction to Statistical Modeling of Extreme Values.
    """
    if not daily_precip:
        return None

    # Group into years (365/366 days per year)
    annual_maxima = []
    year_data: List[float] = []
    day_count = 0

    for val in daily_precip:
        if val is not None and val >= 0:
            year_data.append(val)
        day_count += 1

        if day_count >= 365:
            if year_data:
                annual_maxima.append(max(year_data))
            year_data = []
            day_count = 0

    # Last partial year
    if year_data:
        annual_maxima.append(max(year_data))

    if len(annual_maxima) < _MIN_YEARS:
        return None

    mean_am = sum(annual_maxima) / len(annual_maxima)
    variance = sum((x - mean_am) ** 2 for x in annual_maxima) / len(annual_maxima)
    std_am = math.sqrt(variance) if variance > 0 else 1.0

    # Method of Moments for Gumbel Type I
    sigma_gumbel = std_am * math.sqrt(6) / math.pi
    mu_gumbel = mean_am - 0.5772 * sigma_gumbel

    return {"location": round(mu_gumbel, 1), "scale": round(sigma_gumbel, 1)}


def derive_heatwave_days(daily_tmax: List[Optional[float]]) -> Optional[float]:
    """Count average annual heatwave days (days above 33°C threshold).

    Reference: KMA heatwave warning criteria.
    """
    if not daily_tmax:
        return None

    total_hw_days = 0
    year_hw = 0
    day_count = 0
    year_count = 0

    for val in daily_tmax:
        if val is not None and val > _HEATWAVE_THRESHOLD_C:
            year_hw += 1
        day_count += 1

        if day_count >= 365:
            total_hw_days += year_hw
            year_count += 1
            year_hw = 0
            day_count = 0

    # Last partial year
    if day_count > 180:  # More than half a year
        total_hw_days += year_hw
        year_count += 1

    if year_count < _MIN_YEARS:
        return None

    return round(total_hw_days / year_count, 1)


def derive_drought_days(daily_precip: List[Optional[float]]) -> Optional[float]:
    """Derive average annual drought days (longest consecutive dry spell).

    A dry day is defined as precipitation < 1mm.

    Reference: K-water drought assessment methodology.
    """
    if not daily_precip:
        return None

    max_dry_spells: List[int] = []
    current_dry = 0
    max_dry = 0
    day_count = 0

    for val in daily_precip:
        if val is not None and val < 1.0:
            current_dry += 1
        else:
            max_dry = max(max_dry, current_dry)
            current_dry = 0
        day_count += 1

        if day_count >= 365:
            max_dry = max(max_dry, current_dry)
            max_dry_spells.append(max_dry)
            current_dry = 0
            max_dry = 0
            day_count = 0

    # Last partial year
    if day_count > 180:
        max_dry = max(max_dry, current_dry)
        max_dry_spells.append(max_dry)

    if len(max_dry_spells) < _MIN_YEARS:
        return None

    return round(sum(max_dry_spells) / len(max_dry_spells), 1)


def derive_wind_speed_baseline(daily_wind: List[Optional[float]]) -> Optional[float]:
    """Derive average annual maximum wind speed (m/s).

    Used for typhoon frequency adjustment.
    """
    if not daily_wind:
        return None

    annual_maxima: List[float] = []
    year_data: List[float] = []
    day_count = 0

    for val in daily_wind:
        if val is not None and val >= 0:
            year_data.append(val)
        day_count += 1

        if day_count >= 365:
            if year_data:
                annual_maxima.append(max(year_data))
            year_data = []
            day_count = 0

    if year_data:
        annual_maxima.append(max(year_data))

    if len(annual_maxima) < _MIN_YEARS:
        return None

    return round(sum(annual_maxima) / len(annual_maxima), 1)


# ── Integrated Baseline Derivation ───────────────────────────────────
def get_api_derived_baselines(lat: float, lon: float) -> Optional[dict]:
    """Fetch weather data and derive all baselines for physical risk models.

    Returns:
        {
            "gumbel_params": {"location": μ, "scale": σ},
            "heatwave_days": float,
            "drought_days": float,
            "wind_speed_annual_max_ms": float,
        }
        or None if API fails or insufficient data.
    """
    key = _cache_key(lat, lon)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    weather = fetch_historical_weather(lat, lon)
    if weather is None:
        return None

    gumbel = derive_gumbel_params(weather["precipitation_sum"])
    heatwave = derive_heatwave_days(weather["temperature_2m_max"])
    drought = derive_drought_days(weather["precipitation_sum"])
    wind = derive_wind_speed_baseline(weather["wind_speed_10m_max"])

    # If any critical derivation failed, return None to trigger fallback
    if gumbel is None:
        return None

    result = {
        "gumbel_params": gumbel,
        "heatwave_days": heatwave,
        "drought_days": drought,
        "wind_speed_annual_max_ms": wind,
    }

    _cache_set(key, result)
    return result
