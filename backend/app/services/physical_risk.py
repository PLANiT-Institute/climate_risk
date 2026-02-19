"""Physical risk analytical service (v1) – replacing placeholder with IPCC/KMA-grounded models.

Methodology:
- Flood: Gumbel Type I extreme value distribution (KMA 30yr fit) + USACE depth-damage
- Typhoon: Poisson frequency model (KMA NTC 1951-2023) + HAZUS-MH wind damage
- Heatwave: Chronic productivity loss model (ILO 2019, EPRI)
- Drought: Water stress impact model (K-water)
- Sea level rise: IPCC AR6 cumulative projection
- Compound risk: Variance-covariance approximation for correlated hazards

LIMITATIONS:
- All outputs are point estimates with no confidence intervals or uncertainty bounds.
  Gumbel parameter uncertainty alone can propagate +/-30% into flood EAL.
- Hazard intensification rates use global/continental IPCC defaults, not Korean-
  specific downscaled projections (KMA 2020). See climate_science.py for details.
- No feedback loops between risk domains (e.g., physical damage affecting capital
  availability for transition investment).

References:
- Coles (2001), "An Introduction to Statistical Modeling of Extreme Values"
- IPCC AR6 WG1 Ch.11, weather/climate extremes
- Kim, J. & Lee, S. (2019), "Korean Industrial Depth-Damage Curves"
- Munich Re NatCatSERVICE (2023), business interruption data
"""

import math
from typing import Dict, List, Optional

from ..core.config import (
    FLOOD_GUMBEL_PARAMS,
    TYPHOON_ANNUAL_FREQUENCY,
    TYPHOON_WIND_DAMAGE,
    TYPHOON_CATEGORY_DISTRIBUTION,
    HEATWAVE_BASELINE_DAYS,
    HEATWAVE_DAYS_PER_DEGREE,
    DROUGHT_BASELINE_DAYS,
    DEPTH_DAMAGE_CURVE_INDUSTRIAL,
    RUNOFF_COEFFICIENT,
    BUSINESS_INTERRUPTION_DAYS,
    SECTOR_OUTDOOR_EXPOSURE,
)
from ..data.sample_facilities import get_all_facilities
from .risk_math import (
    gumbel_return_period,
    exceedance_probability,
    piecewise_linear_interpolate,
)
from .climate_science import (
    get_warming_delta,
    get_warming_at_year,
    get_hazard_frequency_multiplier,
    get_hazard_intensity_multiplier,
    get_sea_level_rise_mm,
)
from .open_meteo import get_api_derived_baselines

HAZARD_TYPES = ["flood", "typhoon", "heatwave", "drought", "sea_level_rise"]

_HAZARD_DESCRIPTIONS = {
    "flood": "집중호우 및 하천 범람으로 인한 침수 위험",
    "typhoon": "태풍 및 강풍에 의한 시설물 피해 위험",
    "heatwave": "폭염에 의한 설비 효율 저하 및 근로자 안전 위험",
    "drought": "가뭄으로 인한 용수 부족 및 생산 차질 위험",
    "sea_level_rise": "해수면 상승에 따른 연안 시설 침수 위험",
}

# Return periods for EAL discrete integration (years)
_RETURN_PERIODS = [5, 10, 20, 50, 100, 200, 500]

# Correlation matrix for compound risk (variance-covariance approach).
# Source for methodology: Portfolio risk theory (Markowitz 1952); applied
# to multi-hazard loss aggregation per Wahl et al. (2015), "Increasing
# risk of compound flooding", Nature Climate Change, 5, 1085-1088.
#
# Correlation values are estimated from KMA co-occurrence statistics
# (1991-2020) and IPCC AR6 WG1 Ch.11, Section 11.8 (compound events).
# Flood-typhoon: 0.40 based on ~40% of Korean floods coinciding with
# typhoon landfalls (KMA NTC data). Other pairs are approximate.
# NOTE: These are linear correlation approximations, not copula parameters.
_HAZARD_CORRELATIONS = {
    ("flood", "typhoon"): 0.40,    # Rain-bearing typhoons (KMA 1991-2020)
    ("flood", "heatwave"): -0.15,  # Inverse (monsoon vs dry heat periods)
    ("typhoon", "heatwave"): 0.10, # Weak positive (both summer phenomena)
    ("drought", "heatwave"): 0.35, # Co-occurrence (IPCC AR6 Ch.11, Section 11.8)
    ("flood", "drought"): -0.20,   # Inverse (wet vs dry extremes)
}


# ── Region Classification (6 zones, KMA climate districts) ──────────
def _region_type(lat: float, lon: float) -> str:
    """Classify into 6 Korean climate regions based on coordinates.

    Source: KMA climate district classification.
    """
    # Southern coastal (Busan, Yeosu, Gwangyang)
    if lat < 35.2:
        if lon > 128.5:
            return "coastal_east"
        return "coastal_south"
    # Eastern coastal (Pohang, Ulsan)
    if lon > 129.0:
        return "coastal_east"
    # Western coastal (Incheon, Dangjin, Taean)
    if lon < 126.7:
        return "coastal_west"
    # Mountain (high lat, inland east: Danyang, Yeongwol)
    if lat > 36.5 and lon > 128.0:
        return "mountain"
    # Inland south (Gumi)
    if lat < 36.5 and lon > 127.5:
        return "inland_south"
    # Inland central (Hwaseong, Pyeongtaek, Asan)
    return "inland_central"


def _risk_level(eal_ratio: float) -> str:
    """Classify risk level based on EAL as fraction of asset value."""
    if eal_ratio >= 0.005:  # 0.5%+ of assets
        return "High"
    if eal_ratio >= 0.001:  # 0.1%+
        return "Medium"
    return "Low"


def _daily_revenue(fac: dict) -> float:
    """Approximate daily revenue from annual revenue."""
    return fac["annual_revenue"] / 365.0


# ── Flood Risk Model ────────────────────────────────────────────────
def _flood_risk_model(
    fac: dict,
    region: str,
    scenario_id: str,
    year: int,
    api_baselines: Optional[dict] = None,
) -> dict:
    """Flood risk using Gumbel extreme value + depth-damage curve.

    Method:
    1. Gumbel Type I quantile for each return period → rainfall (mm)
    2. Climate-change intensity multiplier (+5.5%/deg C for extreme
       daily precipitation, IPCC AR6 WG1 Ch.8 range)
    3. Rainfall → flood depth via rational method approximation:
       depth = rainfall × runoff_coeff × accumulation_factor / 10
       where accumulation_factor accounts for local catchment
       concentration. Source: Chow et al. (1988) "Applied Hydrology",
       Ch.15; MOLIT (2019) drainage standard.
    4. Depth → damage fraction via USACE/Kim&Lee curve
    5. EAL = discrete integration over return periods
    6. Business interruption cost added

    Reference: Coles (2001); IPCC AR6 WG1 Ch.8/Ch.11; Kim & Lee (2019).
    """
    # Use API-derived Gumbel params if available, otherwise fall back to config
    if api_baselines and api_baselines.get("gumbel_params"):
        gumbel = api_baselines["gumbel_params"]
    else:
        gumbel = FLOOD_GUMBEL_PARAMS.get(region, FLOOD_GUMBEL_PARAMS["inland_central"])
    mu, sigma = gumbel["location"], gumbel["scale"]

    freq_mult = get_hazard_frequency_multiplier("flood", scenario_id, year)
    intensity_mult = get_hazard_intensity_multiplier("flood", scenario_id, year)
    runoff = RUNOFF_COEFFICIENT["industrial"]

    assets = fac["assets_value"]
    eal = 0.0
    bi_cost = 0.0

    for i in range(len(_RETURN_PERIODS)):
        T = _RETURN_PERIODS[i]
        T_next = _RETURN_PERIODS[i + 1] if i + 1 < len(_RETURN_PERIODS) else T * 3

        # Climate-adjusted return period
        T_adjusted = T / freq_mult

        # Rainfall for T-year event (mm)
        rainfall_mm = gumbel_return_period(mu, sigma, T_adjusted)
        rainfall_mm *= intensity_mult

        # Convert rainfall to approximate flood depth (cm) via rational method.
        # depth = rainfall(mm) × C × F_acc / 10
        # C = runoff coefficient (0.80 for industrial impervious surfaces)
        # F_acc = accumulation factor accounting for upstream catchment
        #         concentration minus drainage capacity. Value of 1.0 assumes
        #         local ponding only (no upstream contribution but also no
        #         effective storm drainage during extreme events).
        # /10 = mm to cm unit conversion.
        # Source: Chow et al. (1988), "Applied Hydrology"; MOLIT (2019).
        # Limitation: Ignores catchment-specific hydrology, terrain slope,
        # and drainage system capacity. For site-specific assessments,
        # replace with SCS Curve Number or hydraulic modeling.
        _ACCUMULATION_FACTOR = 1.0
        flood_depth_cm = rainfall_mm * runoff * _ACCUMULATION_FACTOR / 10.0

        # Damage fraction from depth-damage curve
        damage_frac = piecewise_linear_interpolate(DEPTH_DAMAGE_CURVE_INDUSTRIAL, int(flood_depth_cm))
        damage_frac = max(0.0, min(1.0, damage_frac))

        # Loss for this return period
        loss = assets * damage_frac

        # Business interruption
        bi_days = BUSINESS_INTERRUPTION_DAYS["flood"]
        if flood_depth_cm < 30:
            bi_day_count = bi_days["minor"]
        elif flood_depth_cm < 100:
            bi_day_count = bi_days["moderate"]
        elif flood_depth_cm < 200:
            bi_day_count = bi_days["severe"]
        else:
            bi_day_count = bi_days["catastrophic"]
        bi_loss = _daily_revenue(fac) * bi_day_count

        # Probability band: P(T) - P(T_next)
        prob_band = (1.0 / T) - (1.0 / T_next)
        eal += (loss + bi_loss) * prob_band

    probability = 1.0 / (_RETURN_PERIODS[0] / freq_mult)  # Annual prob of most frequent event

    return {
        "hazard_type": "flood",
        "risk_level": _risk_level(eal / assets if assets else 0),
        "probability": round(min(1.0, probability), 3),
        "potential_loss": round(eal),
        "description": _HAZARD_DESCRIPTIONS["flood"],
        "return_period_years": round(_RETURN_PERIODS[2] / freq_mult, 1),
        "climate_change_multiplier": round(freq_mult * intensity_mult, 3),
        "business_interruption_cost": round(bi_cost),
    }


# ── Typhoon Risk Model ──────────────────────────────────────────────
def _typhoon_risk_model(
    fac: dict,
    region: str,
    scenario_id: str,
    year: int,
    api_baselines: Optional[dict] = None,
) -> dict:
    """Typhoon risk using Poisson frequency + HAZUS wind damage.

    Method:
    1. Regional annual strike frequency (KMA NTC)
    2. Climate-adjusted frequency multiplier
    3. Category distribution × damage rate
    4. Cat 4-5 ratio increase per IPCC AR6
    5. EAL = frequency × expected damage

    Reference: KMA NTC; HAZUS-MH; IPCC AR6 WG1.
    """
    base_freq = TYPHOON_ANNUAL_FREQUENCY.get(region, 0.3)

    # Adjust base frequency using API wind speed data (±20% correction)
    if api_baselines and api_baselines.get("wind_speed_annual_max_ms"):
        # Reference: typical Korean annual max ~25 m/s
        wind_ratio = api_baselines["wind_speed_annual_max_ms"] / 25.0
        adjustment = max(0.8, min(1.2, wind_ratio))  # Clamp to ±20%
        base_freq = base_freq * adjustment
    freq_mult = get_hazard_frequency_multiplier("typhoon", scenario_id, year)
    delta_T = get_warming_delta(scenario_id, year)

    adjusted_freq = base_freq * freq_mult
    assets = fac["assets_value"]

    # Adjust category distribution for climate change (more intense storms)
    # IPCC AR6 WG1 Ch.11: +13% per deg C in Cat 4-5 proportion
    # Method: shift probability from Cat 1-2 to Cat 4-5, preserving sum = 1.0
    # Source for 0.6/0.4 split: proportional to baseline Cat 4 vs Cat 5 ratio
    cat45_boost = 0.13 * delta_T
    cat_dist = dict(TYPHOON_CATEGORY_DISTRIBUTION)

    # Shift probability toward higher categories
    low_cat_total = cat_dist["category_1"] + cat_dist["category_2"]
    high_cat_total = cat_dist["category_3"] + cat_dist["category_4"] + cat_dist["category_5"]
    shift = min(cat45_boost * high_cat_total, low_cat_total * 0.3)

    cat_dist["category_1"] -= shift * 0.6
    cat_dist["category_2"] -= shift * 0.4
    cat_dist["category_4"] += shift * 0.6
    cat_dist["category_5"] += shift * 0.4

    # Normalize to ensure probabilities sum to 1.0 (guards against rounding)
    total_prob = sum(cat_dist.values())
    if total_prob > 0 and abs(total_prob - 1.0) > 1e-9:
        cat_dist = {k: v / total_prob for k, v in cat_dist.items()}

    # Expected damage per strike
    expected_damage_rate = 0.0
    for cat_name, cat_prob in cat_dist.items():
        wind_data = TYPHOON_WIND_DAMAGE.get(cat_name, {})
        expected_damage_rate += cat_prob * wind_data.get("damage_rate", 0.0)

    # Direct asset damage EAL
    direct_eal = adjusted_freq * expected_damage_rate * assets

    # Business interruption
    bi_days_config = BUSINESS_INTERRUPTION_DAYS["typhoon"]
    expected_bi_days = sum(
        cat_dist[cat] * bi_days_config.get(cat, 5.0)
        for cat in cat_dist
    )
    bi_eal = adjusted_freq * expected_bi_days * _daily_revenue(fac)

    total_eal = direct_eal + bi_eal

    return {
        "hazard_type": "typhoon",
        "risk_level": _risk_level(total_eal / assets if assets else 0),
        "probability": round(min(1.0, adjusted_freq), 3),
        "potential_loss": round(total_eal),
        "description": _HAZARD_DESCRIPTIONS["typhoon"],
        "return_period_years": round(1.0 / adjusted_freq if adjusted_freq > 0 else 999, 1),
        "climate_change_multiplier": round(freq_mult, 3),
        "business_interruption_cost": round(bi_eal),
    }


# ── Heatwave Risk Model ─────────────────────────────────────────────
def _heatwave_risk_model(
    fac: dict,
    region: str,
    scenario_id: str,
    year: int,
    api_baselines: Optional[dict] = None,
) -> dict:
    """Heatwave (chronic) risk: productivity loss + equipment efficiency.

    Method:
    1. Baseline heatwave days + climate-change increment
    2. Outdoor/indoor split by sector
    3. Productivity loss per heatwave day (ILO 2019)
    4. Equipment efficiency loss for power/heavy industry (EPRI)

    Reference: ILO (2019); EPRI; KMA Climate Change Scenarios (2020).
    """
    if api_baselines and api_baselines.get("heatwave_days") is not None:
        base_days = api_baselines["heatwave_days"]
    else:
        base_days = HEATWAVE_BASELINE_DAYS.get(region, 12.0)
    delta_T = get_warming_delta(scenario_id, year)
    hw_days = base_days + HEATWAVE_DAYS_PER_DEGREE * delta_T

    sector = fac["sector"]
    outdoor_frac = SECTOR_OUTDOOR_EXPOSURE.get(sector, 0.15)
    indoor_frac = 1.0 - outdoor_frac

    # Productivity loss
    bi_config = BUSINESS_INTERRUPTION_DAYS["heatwave"]
    daily_loss_outdoor = bi_config["per_day_outdoor"]  # days lost per HW day
    daily_loss_indoor = bi_config["per_day_indoor"]

    effective_days_lost = hw_days * (
        outdoor_frac * daily_loss_outdoor + indoor_frac * daily_loss_indoor
    )
    productivity_loss = effective_days_lost * _daily_revenue(fac)

    # Equipment efficiency loss for applicable sectors
    # Source: EPRI (2011), "Climate Change and Power Plant Efficiency".
    # Original finding: ~0.5% output loss per deg C above 30°C.
    # Conversion to per-day basis: heatwave days average ~3°C above threshold
    # (33°C threshold, ~36°C average), so per-day loss ≈ 0.5% × 3 ≈ 1.5%.
    # We use a conservative 0.3% per heatwave day, accounting for adaptive
    # measures (cooling systems, load management). This represents a lower
    # bound compared to the raw EPRI temperature-based estimate.
    equipment_loss = 0.0
    if sector in ("utilities", "steel", "petrochemical", "cement"):
        efficiency_drop_per_day = 0.003  # 0.3% per heatwave day (conservative)
        equipment_loss = hw_days * efficiency_drop_per_day * fac["annual_revenue"]

    total_eal = productivity_loss + equipment_loss
    assets = fac["assets_value"]

    return {
        "hazard_type": "heatwave",
        "risk_level": _risk_level(total_eal / assets if assets else 0),
        "probability": round(min(1.0, hw_days / 365), 3),
        "potential_loss": round(total_eal),
        "description": _HAZARD_DESCRIPTIONS["heatwave"],
        "return_period_years": 1.0,  # Chronic, annual occurrence
        "climate_change_multiplier": round(hw_days / max(base_days, 1), 3),
        "business_interruption_cost": round(productivity_loss),
    }


# ── Drought Risk Model ──────────────────────────────────────────────
def _drought_risk_model(
    fac: dict,
    region: str,
    scenario_id: str,
    year: int,
    api_baselines: Optional[dict] = None,
) -> dict:
    """Drought risk: water stress impact on production.

    Water-intensive sectors face production curtailment risk.

    Reference: K-water assessment; IPCC AR6 WG2.
    """
    if api_baselines and api_baselines.get("drought_days") is not None:
        base_days = api_baselines["drought_days"]
    else:
        base_days = DROUGHT_BASELINE_DAYS.get(region, 18.0)
    freq_mult = get_hazard_frequency_multiplier("drought", scenario_id, year)
    drought_days = base_days * freq_mult

    sector = fac["sector"]
    # Water intensity factor by sector
    water_intensity = {
        "steel": 0.15, "petrochemical": 0.12, "cement": 0.05,
        "utilities": 0.20, "oil_gas": 0.10, "shipping": 0.03,
        "automotive": 0.06, "electronics": 0.18, "real_estate": 0.03,
        "financial": 0.01,
    }
    w_factor = water_intensity.get(sector, 0.05)

    # Revenue at risk = drought_days / 365 * water_intensity * revenue
    revenue_at_risk = (drought_days / 365) * w_factor * fac["annual_revenue"]

    # BI: severity classification
    bi_config = BUSINESS_INTERRUPTION_DAYS["drought"]
    if drought_days < 20:
        bi_days = bi_config["minor"]
    elif drought_days < 35:
        bi_days = bi_config["moderate"]
    else:
        bi_days = bi_config["severe"]

    bi_cost = bi_days * _daily_revenue(fac) * w_factor
    total_eal = revenue_at_risk + bi_cost
    assets = fac["assets_value"]

    return {
        "hazard_type": "drought",
        "risk_level": _risk_level(total_eal / assets if assets else 0),
        "probability": round(min(1.0, drought_days / 365 * freq_mult), 3),
        "potential_loss": round(total_eal),
        "description": _HAZARD_DESCRIPTIONS["drought"],
        "return_period_years": round(365 / max(drought_days, 1), 1),
        "climate_change_multiplier": round(freq_mult, 3),
        "business_interruption_cost": round(bi_cost),
    }


# ── Sea Level Rise Model ────────────────────────────────────────────
def _sea_level_rise_model(
    fac: dict,
    region: str,
    scenario_id: str,
    year: int,
) -> dict:
    """Sea level rise: chronic coastal inundation risk.

    Only applies meaningfully to coastal regions.

    Reference: IPCC AR6 WG1 Ch.9.
    """
    slr_mm = get_sea_level_rise_mm(scenario_id, year)
    assets = fac["assets_value"]

    # Only coastal regions face significant SLR risk
    is_coastal = region.startswith("coastal")
    if not is_coastal:
        return {
            "hazard_type": "sea_level_rise",
            "risk_level": "Low",
            "probability": round(slr_mm / 10000, 3),  # Very low inland
            "potential_loss": 0,
            "description": _HAZARD_DESCRIPTIONS["sea_level_rise"],
            "return_period_years": 999.0,
            "climate_change_multiplier": 1.0,
            "business_interruption_cost": 0,
        }

    # Coastal exposure: SLR increases baseline flood probability
    # and permanently reduces usable land value
    slr_cm = slr_mm / 10.0
    # Chronic damage: fraction of assets at risk from permanent inundation
    damage_frac = piecewise_linear_interpolate(DEPTH_DAMAGE_CURVE_INDUSTRIAL, int(slr_cm))
    damage_frac = max(0.0, min(0.5, damage_frac * 0.3))  # SLR is slower, partial adaptation

    # Annualized over remaining useful life (~30 years)
    annual_loss = assets * damage_frac / 30.0

    return {
        "hazard_type": "sea_level_rise",
        "risk_level": _risk_level(annual_loss / assets if assets else 0),
        "probability": round(min(1.0, slr_cm / 100), 3),
        "potential_loss": round(annual_loss),
        "description": _HAZARD_DESCRIPTIONS["sea_level_rise"],
        "return_period_years": 1.0,  # Chronic
        "climate_change_multiplier": round(slr_mm / max(1, get_sea_level_rise_mm("current_policies", year)), 3) if get_sea_level_rise_mm("current_policies", year) > 0 else 1.0,
        "business_interruption_cost": 0,
    }


# ── Compound Risk ────────────────────────────────────────────────────
def _compound_risk_adjusted_eal(hazard_eals: Dict[str, float]) -> float:
    """Adjust total EAL for compound (correlated) hazard risks.

    Uses variance-covariance approach from portfolio risk theory:
    joint_EAL = sum(individual) + sum(rho_ij * sqrt(EAL_i * EAL_j))

    The geometric-mean coupling term sqrt(EAL_i * EAL_j) approximates
    the covariance contribution when individual loss distributions are
    not fully characterized. This is a first-order approximation, not
    a full copula model.

    Reference:
    - Methodology: Markowitz (1952), "Portfolio Selection", adapted for
      multi-hazard loss aggregation per Wahl et al. (2015), Nature
      Climate Change, and Zscheischler et al. (2020), "A typology of
      compound weather and climate events", Nature Reviews Earth &
      Environment, 1, 333-347 (for conceptual framework).
    - Correlation values: see _HAZARD_CORRELATIONS above.
    """
    total = sum(hazard_eals.values())

    # Add correlation terms
    hazards = list(hazard_eals.keys())
    for i in range(len(hazards)):
        for j in range(i + 1, len(hazards)):
            key = (hazards[i], hazards[j])
            rho = _HAZARD_CORRELATIONS.get(key, _HAZARD_CORRELATIONS.get(
                (hazards[j], hazards[i]), 0.0
            ))
            if rho != 0 and hazard_eals[hazards[i]] > 0 and hazard_eals[hazards[j]] > 0:
                total += rho * math.sqrt(
                    hazard_eals[hazards[i]] * hazard_eals[hazards[j]]
                )

    return max(total, 0.0)


# ── Main Assessment Function ────────────────────────────────────────
def assess_physical_risk(
    scenario_id: str = "current_policies",
    year: int = 2030,
    use_api_data: bool = False,
    facilities: list | None = None,
) -> dict:
    """Comprehensive physical risk assessment using analytical models.

    Args:
        scenario_id: NGFS scenario (default "current_policies" for backward compat).
        year: assessment year (default 2030).
        use_api_data: if True, fetch climate baselines from Open-Meteo API.
        facilities: optional facility list; defaults to sample_facilities.

    Returns:
        Same structure as before, with enhanced hazard data.
        model_status changed from "placeholder" to "analytical_v1".
    """
    facilities = facilities if facilities is not None else get_all_facilities()
    results: List[dict] = []
    risk_counts = {"High": 0, "Medium": 0, "Low": 0}

    warming = get_warming_at_year(scenario_id, year)

    for fac in facilities:
        region = _region_type(fac["latitude"], fac["longitude"])
        assets = fac["assets_value"]

        # Fetch API-derived baselines if requested
        api_baselines = None
        if use_api_data:
            api_baselines = get_api_derived_baselines(fac["latitude"], fac["longitude"])

        # Run each hazard model
        flood = _flood_risk_model(fac, region, scenario_id, year, api_baselines=api_baselines)
        typhoon = _typhoon_risk_model(fac, region, scenario_id, year, api_baselines=api_baselines)
        heatwave = _heatwave_risk_model(fac, region, scenario_id, year, api_baselines=api_baselines)
        drought = _drought_risk_model(fac, region, scenario_id, year, api_baselines=api_baselines)
        slr = _sea_level_rise_model(fac, region, scenario_id, year)

        hazards = [flood, typhoon, heatwave, drought, slr]

        # Compound risk adjustment
        hazard_eals = {h["hazard_type"]: h["potential_loss"] for h in hazards}
        total_eal = _compound_risk_adjusted_eal(hazard_eals)

        overall = _risk_level(total_eal / assets if assets else 0)
        risk_counts[overall] = risk_counts.get(overall, 0) + 1

        results.append({
            "facility_id": fac["facility_id"],
            "facility_name": fac["name"],
            "location": fac["location"],
            "latitude": fac["latitude"],
            "longitude": fac["longitude"],
            "overall_risk_level": overall,
            "hazards": hazards,
            "total_expected_annual_loss": round(total_eal),
        })

    return {
        "total_facilities": len(results),
        "overall_risk_summary": risk_counts,
        "facilities": results,
        "model_status": "analytical_v1",
        "scenario": scenario_id,
        "assessment_year": year,
        "warming_above_preindustrial": round(warming, 2),
        "data_source": "open_meteo_api" if use_api_data else "hardcoded_config",
        "methodology_notes": {
            "uncertainty": (
                "All outputs are point estimates. No confidence intervals "
                "or Monte Carlo uncertainty propagation is performed. "
                "Gumbel parameter uncertainty alone can propagate +/-30% "
                "into flood EAL values."
            ),
            "regional_limitation": (
                "Hazard intensification rates use global/continental IPCC "
                "AR6 defaults, not Korean-specific downscaled projections. "
                "KMA (2020) Korean Climate Change Assessment Report data "
                "is not yet integrated."
            ),
            "interactions": (
                "No feedback loops between physical and transition risk "
                "domains are modeled."
            ),
        },
    }
