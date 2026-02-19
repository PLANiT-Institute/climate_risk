"""Climate science calculations grounded in IPCC AR6.

References:
- IPCC AR6 WG1, Table SPM.1 - Global surface temperature change projections
- IPCC AR6 WG1, Chapter 11 - Weather and Climate Extreme Events
- Clausius-Clapeyron relation: ~7% increase in atmospheric moisture per 1 deg C
- Fischer & Knutti (2015), "Anthropogenic contribution to global occurrence of
  heavy-precipitation and high-temperature extremes", Nature Climate Change
"""

from typing import Dict

from .risk_math import piecewise_linear_interpolate


# ── Scenario-to-SSP Mapping ─────────────────────────────────────────
# Maps internal NGFS-style scenario IDs to IPCC SSP pathways.
# NOTE: NGFS and SSP/RCP are independent frameworks. This mapping is a
# reasonable approximation based on radiative forcing alignment, but is
# NOT an officially published correspondence. Alternative mappings exist
# (e.g., NGFS uses its own integrated assessment models). Physical risk
# results are sensitive to this choice.
# Reference: NGFS (2023) Technical Documentation, Table 2.1 (scenario archetypes).
SCENARIO_TO_SSP: Dict[str, str] = {
    "net_zero_2050": "SSP1-1.9",        # Very low emissions
    "below_2c": "SSP1-2.6",             # Low emissions
    "delayed_transition": "SSP2-4.5",   # Intermediate emissions
    "current_policies": "SSP3-7.0",     # High emissions
}

# ── SSP Warming Projections (deg C above pre-industrial) ────────────
# Source: IPCC AR6 WG1 Table SPM.1 (best estimates)
# Values represent global mean surface temperature change relative to 1850-1900
SSP_WARMING_PROJECTIONS: Dict[str, Dict[int, float]] = {
    "SSP1-1.9": {
        2020: 1.1, 2025: 1.2, 2030: 1.4, 2035: 1.5, 2040: 1.5,
        2045: 1.5, 2050: 1.4, 2060: 1.3, 2070: 1.3, 2080: 1.3, 2100: 1.0,
    },
    "SSP1-2.6": {
        2020: 1.1, 2025: 1.2, 2030: 1.4, 2035: 1.6, 2040: 1.7,
        2045: 1.8, 2050: 1.8, 2060: 1.8, 2070: 1.8, 2080: 1.8, 2100: 1.8,
    },
    "SSP2-4.5": {
        2020: 1.1, 2025: 1.3, 2030: 1.5, 2035: 1.7, 2040: 1.9,
        2045: 2.0, 2050: 2.1, 2060: 2.3, 2070: 2.5, 2080: 2.6, 2100: 2.7,
    },
    "SSP3-7.0": {
        2020: 1.1, 2025: 1.3, 2030: 1.5, 2035: 1.8, 2040: 2.1,
        2045: 2.3, 2050: 2.5, 2060: 2.9, 2070: 3.3, 2080: 3.6, 2100: 3.6,
    },
}

# ── Hazard Intensification per degree C of warming ──────────────────
# Source: IPCC AR6 WG1 Chapter 11, Table 11.1; Fischer & Knutti (2015);
#         Knutson et al. (2020), "Tropical Cyclones and Climate Change
#         Assessment", BAMS, 100(10), 1987-2007.
#
# IMPORTANT LIMITATION: These are global/continental aggregate rates.
# Korean-specific rates may differ. KMA "한국 기후변화 평가보고서 2020"
# provides downscaled projections but is not yet integrated.
# Users should treat outputs as screening-level estimates, not site-specific
# engineering values.
#
# Values represent fractional increase per 1 deg C of warming above baseline.
HAZARD_INTENSIFICATION_PER_DEGREE: Dict[str, Dict[str, float]] = {
    "flood": {
        "frequency": 0.30,   # +30% per deg C (IPCC AR6 Table 11.1, global)
        "intensity": 0.055,  # +5.5% per deg C extreme daily precipitation
                              # (IPCC AR6 WG1 Ch.8: 5-7% range for daily extremes;
                              # 7% is theoretical CC maximum for hourly events only)
    },
    "typhoon": {
        "frequency": 0.10,   # +10% per deg C (Knutson et al. 2020, Western Pacific
                              # basin estimate; global average ~5% but WP is higher)
        "intensity": 0.05,   # +5% per deg C in peak wind speed (Knutson et al. 2020)
        "cat45_ratio": 0.13, # +13% per deg C in Cat 4-5 proportion (IPCC AR6)
    },
    "heatwave": {
        "frequency": 0.80,   # +80% per deg C (frequency of days above threshold)
                              # IPCC AR6 Table 11.1: 2-3x at 2°C globally;
                              # ~80% per deg C for East Asian mid-latitudes per
                              # Fischer & Knutti (2015), Table 1. Prior value of
                              # 130% was global tropical/subtropical aggregate.
        "intensity": 1.0,    # +1.0 deg C per deg C global warming (amplification)
    },
    "drought": {
        "frequency": 0.15,   # +15% per deg C in drought occurrence (IPCC AR6 Ch.11)
        "intensity": 0.10,   # +10% severity per deg C
    },
    "sea_level_rise": {
        "rate_mm_per_year_per_degree": 3.0,  # ~3mm/yr/deg C (IPCC AR6 Ch.9)
    },
}

# Baseline warming at 2020 (above pre-industrial)
_BASELINE_WARMING = 1.1  # deg C, IPCC AR6


def get_warming_at_year(scenario_id: str, year: int) -> float:
    """Get projected global mean warming (deg C above pre-industrial) for scenario/year.

    Args:
        scenario_id: internal scenario identifier (e.g. 'net_zero_2050').
        year: projection year.

    Returns:
        Warming in deg C above 1850-1900 baseline.

    Reference: IPCC AR6 WG1 Table SPM.1.
    """
    ssp = SCENARIO_TO_SSP.get(scenario_id)
    if ssp is None:
        # Default to intermediate pathway for unknown scenarios
        ssp = "SSP2-4.5"
    projections = SSP_WARMING_PROJECTIONS[ssp]
    return piecewise_linear_interpolate(projections, year)


def get_warming_delta(scenario_id: str, year: int) -> float:
    """Additional warming above current (2020) baseline.

    This is the *incremental* warming that drives hazard intensification.
    """
    return max(0.0, get_warming_at_year(scenario_id, year) - _BASELINE_WARMING)


def get_hazard_frequency_multiplier(
    hazard: str,
    scenario_id: str,
    year: int,
) -> float:
    """Multiplicative factor for hazard event frequency under climate change.

    A multiplier of 1.5 means 50% more frequent than baseline.

    Args:
        hazard: hazard type (flood, typhoon, heatwave, drought).
        scenario_id: NGFS scenario.
        year: projection year.

    Returns:
        Frequency multiplier (>= 1.0).

    Reference: IPCC AR6 WG1 Ch.11, Table 11.1.
    """
    delta_T = get_warming_delta(scenario_id, year)
    params = HAZARD_INTENSIFICATION_PER_DEGREE.get(hazard, {})
    freq_rate = params.get("frequency", 0.0)
    return 1.0 + freq_rate * delta_T


def get_hazard_intensity_multiplier(
    hazard: str,
    scenario_id: str,
    year: int,
) -> float:
    """Multiplicative factor for hazard intensity under climate change.

    For precipitation: based on Clausius-Clapeyron (+7%/deg C).
    For wind: based on IPCC AR6 projected intensification.

    Args:
        hazard: hazard type.
        scenario_id: NGFS scenario.
        year: projection year.

    Returns:
        Intensity multiplier (>= 1.0).

    Reference: Clausius-Clapeyron relation; IPCC AR6 WG1 Ch.11.
    """
    delta_T = get_warming_delta(scenario_id, year)
    params = HAZARD_INTENSIFICATION_PER_DEGREE.get(hazard, {})
    intensity_rate = params.get("intensity", 0.0)
    return 1.0 + intensity_rate * delta_T


def adjust_return_period(
    base_return_period: float,
    freq_multiplier: float,
) -> float:
    """Adjust return period for climate change effect on frequency.

    If a 100-year event becomes 1.5x more frequent, its new return period
    is 100/1.5 = ~67 years.

    Args:
        base_return_period: historical return period in years.
        freq_multiplier: climate-adjusted frequency multiplier.

    Returns:
        Climate-adjusted return period (shorter = more frequent).
    """
    if freq_multiplier <= 0:
        return base_return_period
    return base_return_period / freq_multiplier


def get_sea_level_rise_mm(scenario_id: str, year: int, base_year: int = 2020) -> float:
    """Cumulative sea level rise in mm from base_year to target year.

    Simple linear accumulation based on warming-dependent rate.

    Reference: IPCC AR6 WG1 Ch.9 (simplified).
    """
    if year <= base_year:
        return 0.0
    # Integrate over years using average warming
    total_mm = 0.0
    slr_params = HAZARD_INTENSIFICATION_PER_DEGREE.get("sea_level_rise", {})
    rate_per_degree = slr_params.get("rate_mm_per_year_per_degree", 3.0)
    base_rate = 3.7  # mm/yr baseline rate (2006-2018 observed, IPCC AR6)

    for y in range(base_year + 1, year + 1):
        delta_T = get_warming_delta(scenario_id, y)
        annual_rate = base_rate + rate_per_degree * delta_T
        total_mm += annual_rate
    return total_mm
