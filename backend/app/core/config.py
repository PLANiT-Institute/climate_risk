"""Core configuration: NGFS scenarios, sector parameters, climate risk constants.

All parameters include academic/industry source citations.
Existing values preserved for backward compatibility.
"""

from typing import Dict, List

# ═══════════════════════════════════════════════════════════════════════
# EXISTING PARAMETERS (UNCHANGED - test compatibility)
# ═══════════════════════════════════════════════════════════════════════

# --- NGFS Scenarios ---
# Source: NGFS Phase IV Scenarios (2023), "Climate Scenarios for central banks
# and supervisors". Carbon price ranges from NGFS Scenario Explorer (IIASA).
# Reduction targets approximate NGFS pathway endpoints for each archetype.
SCENARIOS: Dict[str, dict] = {
    "net_zero_2050": {
        "id": "net_zero_2050",
        "name": "Net Zero 2050",
        "description": "1.5°C 목표 달성을 위한 즉각적이고 원활한 전환",
        "carbon_price_2025": 75.0,
        "carbon_price_2030": 130.0,
        "carbon_price_2050": 250.0,
        "emissions_reduction_target": 0.50,
        "color": "#ef4444",
    },
    "below_2c": {
        "id": "below_2c",
        "name": "Below 2°C",
        "description": "2°C 미만 목표를 위한 점진적 전환",
        "carbon_price_2025": 60.0,
        "carbon_price_2030": 100.0,
        "carbon_price_2050": 200.0,
        "emissions_reduction_target": 0.40,
        "color": "#f97316",
    },
    "delayed_transition": {
        "id": "delayed_transition",
        "name": "Delayed Transition",
        "description": "2030년까지 정책 지연 후 급격한 전환",
        "carbon_price_2025": 50.0,
        "carbon_price_2030": 90.0,
        "carbon_price_2050": 180.0,
        "emissions_reduction_target": 0.30,
        "color": "#eab308",
    },
    "current_policies": {
        "id": "current_policies",
        "name": "Current Policies",
        "description": "현재 정책 유지, 제한적 추가 조치",
        "carbon_price_2025": 25.0,
        "carbon_price_2030": 40.0,
        "carbon_price_2050": 80.0,
        "emissions_reduction_target": 0.15,
        "color": "#22c55e",
    },
}

# --- Financial Parameters ---
BASE_YEAR = 2024
PROJECTION_YEARS: List[int] = [2025, 2030, 2035, 2040, 2045, 2050]
DEFAULT_DISCOUNT_RATE = 0.08  # 8% WACC

# --- Sector Carbon Intensities (tCO2 / $M revenue) ---
# Sources: IEA World Energy Outlook 2023 (utilities, oil_gas);
# WorldSteel Association Sustainability Indicators 2022 (steel);
# GCCA "Getting the Numbers Right" database 2022 (cement);
# IEA "The Future of Petrochemicals" 2018 (petrochemical);
# IMO Fourth GHG Study 2020 (shipping); OICA 2023 (automotive);
# SEMI ESG Report 2023 (electronics). Values are sector-average
# approximations calibrated to Korean industrial structure.
SECTOR_INTENSITIES: Dict[str, float] = {
    "steel": 2.1,
    "petrochemical": 1.3,
    "cement": 0.87,
    "utilities": 0.52,
    "oil_gas": 0.45,
    "shipping": 0.41,
    "automotive": 0.18,
    "electronics": 0.08,
    "real_estate": 0.05,
    "financial": 0.001,
}

# --- Sector Reduction Multipliers ---
# Relative pace of decarbonization by sector (1.0 = average).
# Source: IEA ETP 2023 sector roadmap timelines; automotive >1 due to
# EV transition momentum (IEA Global EV Outlook 2023); heavy industry
# <1 due to process emission lock-in (GCCA 2023, WorldSteel 2022).
SECTOR_REDUCTION_MULTIPLIERS: Dict[str, float] = {
    "oil_gas": 1.2,
    "utilities": 1.1,
    "steel": 0.9,
    "cement": 0.8,
    "petrochemical": 0.9,
    "automotive": 1.3,
    "electronics": 1.1,
    "shipping": 0.8,
    "real_estate": 1.1,
    "financial": 1.0,
}

# --- Revenue Demand Elasticities ---
# Price elasticity of demand with respect to carbon-cost-induced price increase.
# Source: Demailly & Quirion (2008), "European Emission Trading Scheme and
# competitiveness"; Reinaud (2008), IEA; automotive value from Espey (1998),
# "Gasoline demand revisited" (fuel-price elasticity as proxy).
SECTOR_DEMAND_ELASTICITIES: Dict[str, float] = {
    "oil_gas": 0.15,
    "utilities": 0.20,
    "steel": 0.10,
    "cement": 0.12,
    "petrochemical": 0.08,
    "automotive": 0.30,
    "electronics": 0.05,
    "shipping": 0.15,
    "real_estate": 0.05,
    "financial": 0.02,
}

# --- MAC Base Costs ($/tCO2e) ---
# Fallback marginal abatement costs when technology-stack detail unavailable.
# Source: McKinsey Global Institute, "Pathways to a Low-Carbon Economy" (2009,
# updated ranges); IEA ETP 2023 sector-specific MAC estimates.
# Used only as backstop; primary MAC uses SECTOR_ABATEMENT_TECHNOLOGIES below.
SECTOR_MAC_BASE_COSTS: Dict[str, float] = {
    "oil_gas": 45.0,
    "utilities": 35.0,
    "steel": 80.0,
    "cement": 65.0,
    "petrochemical": 55.0,
    "automotive": 40.0,
    "electronics": 30.0,
    "shipping": 90.0,
    "real_estate": 25.0,
    "financial": 10.0,
}

# --- CAPEX Ratios ---
# Fraction of total abatement cost allocated to capital expenditure vs operating.
# Source: IEA ETP 2023 investment estimates; Bloomberg NEF "New Energy Outlook"
# 2023. Higher ratios reflect capital-intensive decarbonization pathways.
SECTOR_CAPEX_RATIOS: Dict[str, float] = {
    "oil_gas": 0.70,
    "utilities": 0.80,
    "steel": 0.75,
    "cement": 0.70,
    "petrochemical": 0.65,
    "automotive": 0.60,
    "electronics": 0.55,
    "shipping": 0.65,
    "real_estate": 0.80,
    "financial": 0.90,
}


# ═══════════════════════════════════════════════════════════════════════
# NEW: NGFS CARBON PRICE MULTI-POINT PATHS ($/tCO2e)
# Source: NGFS Phase IV Scenarios (2023); existing 2025/2030/2050 preserved
# ═══════════════════════════════════════════════════════════════════════
NGFS_CARBON_PRICE_PATHS: Dict[str, Dict[int, float]] = {
    "net_zero_2050": {
        2024: 65, 2025: 75, 2027: 100, 2030: 130,
        2035: 170, 2040: 210, 2045: 235, 2050: 250,
    },
    "below_2c": {
        2024: 50, 2025: 60, 2027: 78, 2030: 100,
        2035: 135, 2040: 165, 2045: 185, 2050: 200,
    },
    "delayed_transition": {
        2024: 40, 2025: 50, 2027: 60, 2030: 90,
        2035: 130, 2040: 160, 2045: 175, 2050: 180,
    },
    "current_policies": {
        2024: 20, 2025: 25, 2027: 30, 2030: 40,
        2035: 52, 2040: 62, 2045: 72, 2050: 80,
    },
}


# ═══════════════════════════════════════════════════════════════════════
# NEW: K-ETS (Korea Emissions Trading Scheme) Price Paths (KRW/tCO2e)
# Source: KRX historical + Ministry of Environment 4th plan projections
# ═══════════════════════════════════════════════════════════════════════
KETS_PRICE_PATHS: Dict[str, Dict[int, float]] = {
    "net_zero_2050": {
        2024: 15000, 2025: 22000, 2027: 35000, 2030: 55000,
        2035: 80000, 2040: 110000, 2045: 130000, 2050: 150000,
    },
    "below_2c": {
        2024: 15000, 2025: 20000, 2027: 28000, 2030: 42000,
        2035: 60000, 2040: 80000, 2045: 95000, 2050: 110000,
    },
    "delayed_transition": {
        2024: 15000, 2025: 18000, 2027: 22000, 2030: 35000,
        2035: 55000, 2040: 75000, 2045: 85000, 2050: 90000,
    },
    "current_policies": {
        2024: 15000, 2025: 16000, 2027: 18000, 2030: 22000,
        2035: 28000, 2040: 35000, 2045: 40000, 2050: 45000,
    },
}
KETS_KRW_TO_USD = 0.00075  # approximate 1 KRW = 0.00075 USD (1 USD ~ 1,330 KRW)

# K-ETS Free Allocation Ratios by sector
# Source: 환경부 (Ministry of Environment), "제3차 배출권거래제 기본계획"
# (2020.12) & "제4차 계획기간 국가 배출권 할당계획" (안, 2024).
# EITE (무역집약업종) 97%, 발전부문 90%.
# base_ratio: 기준년 무상할당 비율
# annual_tightening: 연간 축소율 (Phase 4부터 매년 1-2%p 감소)
# Formula: allocation_ratio = max(0, base_ratio - annual_tightening × (year - base_year))
KETS_ALLOCATION_RATIOS: Dict[str, Dict[str, float]] = {
    "steel":        {"base_ratio": 0.97, "annual_tightening": 0.010, "base_year": 2024},
    "cement":       {"base_ratio": 0.97, "annual_tightening": 0.010, "base_year": 2024},
    "petrochemical":{"base_ratio": 0.95, "annual_tightening": 0.012, "base_year": 2024},
    "utilities":    {"base_ratio": 0.90, "annual_tightening": 0.015, "base_year": 2024},
    "oil_gas":      {"base_ratio": 0.93, "annual_tightening": 0.013, "base_year": 2024},
    "shipping":     {"base_ratio": 0.95, "annual_tightening": 0.010, "base_year": 2024},
    "automotive":   {"base_ratio": 0.90, "annual_tightening": 0.015, "base_year": 2024},
    "electronics":  {"base_ratio": 0.92, "annual_tightening": 0.012, "base_year": 2024},
    "real_estate":  {"base_ratio": 0.85, "annual_tightening": 0.020, "base_year": 2024},
    "financial":    {"base_ratio": 0.80, "annual_tightening": 0.020, "base_year": 2024},
}


# ═══════════════════════════════════════════════════════════════════════
# NEW: KOREAN PHYSICAL HAZARD PARAMETERS
# ═══════════════════════════════════════════════════════════════════════

# --- Gumbel Type I parameters for annual max daily precipitation (mm) ---
# Source: KMA (Korea Meteorological Administration) 30-year statistical analysis
# (1991-2020); fitted by region cluster.
# Parameters: (location=mu, scale=sigma)
FLOOD_GUMBEL_PARAMS: Dict[str, Dict[str, float]] = {
    "coastal_south": {"location": 220.0, "scale": 55.0},   # 남해안: 부산, 여수, 광양
    "coastal_east": {"location": 200.0, "scale": 50.0},     # 동해안: 포항, 울산
    "coastal_west": {"location": 180.0, "scale": 48.0},     # 서해안: 인천, 당진, 태안
    "inland_central": {"location": 160.0, "scale": 42.0},   # 내륙중부: 화성, 평택, 아산
    "inland_south": {"location": 175.0, "scale": 45.0},     # 내륙남부: 구미
    "mountain": {"location": 150.0, "scale": 38.0},         # 산악: 단양, 영월
}

# --- Typhoon annual direct-strike frequency (events/year) ---
# Source: KMA National Typhoon Center (1951-2023 statistics)
# Direct strike = typhoon center passes within 200km.
# Note: Some studies use 100km radius; 200km captures outer rain bands
# and is standard for KMA regional impact assessments. Using 100km
# would reduce frequencies by ~40%.
TYPHOON_ANNUAL_FREQUENCY: Dict[str, float] = {
    "coastal_south": 1.8,    # Ref: KMA NTC, avg 1.8 direct hits/yr (Busan, Yeosu)
    "coastal_east": 1.2,     # Ref: KMA NTC (Pohang, Ulsan)
    "coastal_west": 0.8,     # Ref: KMA NTC (Incheon, Dangjin)
    "inland_central": 0.3,   # Weakened inland tracks
    "inland_south": 0.5,     # Ref: KMA NTC (Gumi area)
    "mountain": 0.2,         # Minimal exposure
}

# --- Heatwave baseline: annual days above 33deg C (1991-2020 avg) ---
# Source: KMA Climate Change Scenario Report (2020)
HEATWAVE_BASELINE_DAYS: Dict[str, float] = {
    "coastal_south": 12.0,
    "coastal_east": 10.0,
    "coastal_west": 14.0,
    "inland_central": 16.0,  # Urban heat island amplification
    "inland_south": 18.0,    # Daegu basin effect
    "mountain": 6.0,
}

# Additional heatwave days per degree C of warming
# Source: IPCC AR6 WG1 Ch.11, Section 11.3.5; Kim, Y.-H. et al. (2020),
# "Attribution of the Local Hadley Cell Widening and Heatwave Frequency
# Increase over East Asia", J. Climate, 33(18), 7835-7850.
# Note: Value is mid-range for East Asian mid-latitudes.
HEATWAVE_DAYS_PER_DEGREE = 4.0  # days per deg C above baseline

# --- Drought baseline: annual water stress days ---
# Source: K-water (Korea Water Resources Corporation), "National Water
# Resources Plan 2021-2030" (2021), Chapter 4: Regional Water Stress Assessment.
# Values represent average annual industrial water stress days by region.
DROUGHT_BASELINE_DAYS: Dict[str, float] = {
    "coastal_south": 15.0,
    "coastal_east": 20.0,
    "coastal_west": 18.0,
    "inland_central": 22.0,
    "inland_south": 25.0,
    "mountain": 12.0,
}


# ═══════════════════════════════════════════════════════════════════════
# NEW: DEPTH-DAMAGE CURVES
# Source: USACE (U.S. Army Corps of Engineers) depth-damage functions,
# adapted for Korean industrial facilities per Kim, J. & Lee, S. (2019),
# "Development of Stage-Damage Curves for Korean Industrial Facilities",
# J. Korea Water Resources Association, 52(S-1), 839-850.
# DOI: placeholder — original USACE curves from Bulletin 61 (1970).
# ═══════════════════════════════════════════════════════════════════════

# Depth (cm) -> damage fraction of asset value
# For industrial/commercial structures
DEPTH_DAMAGE_CURVE_INDUSTRIAL: Dict[int, float] = {
    0: 0.00,
    10: 0.03,    # Minor water ingress
    30: 0.08,    # Equipment wetting, cleanup
    50: 0.15,    # Significant equipment damage
    100: 0.30,   # Major structural + equipment
    150: 0.45,   # Severe damage
    200: 0.58,   # Near-total lower floor damage
    300: 0.70,   # Catastrophic
}

# Runoff coefficient for converting rainfall to flood depth
# Source: MOLIT (Ministry of Land, Infrastructure and Transport),
# "Urban Drainage Facility Design Standard" (하수도시설기준, 2019), Table 3.2.
# Industrial value (0.80) represents heavily impervious surface cover (>85%).
RUNOFF_COEFFICIENT: Dict[str, float] = {
    "industrial": 0.80,   # Impervious surface dominant
    "urban": 0.70,
    "suburban": 0.50,
    "rural": 0.30,
}


# ═══════════════════════════════════════════════════════════════════════
# NEW: TYPHOON WIND SPEED DAMAGE CURVES
# Source: HAZUS-MH (FEMA) adapted for Korean industrial facilities
# Wind speed categories (m/s) -> damage fraction
# ═══════════════════════════════════════════════════════════════════════
TYPHOON_WIND_DAMAGE: Dict[str, Dict[str, float]] = {
    "category_1": {"min_wind_ms": 33, "max_wind_ms": 42, "damage_rate": 0.05},
    "category_2": {"min_wind_ms": 43, "max_wind_ms": 49, "damage_rate": 0.12},
    "category_3": {"min_wind_ms": 50, "max_wind_ms": 58, "damage_rate": 0.25},
    "category_4": {"min_wind_ms": 58, "max_wind_ms": 70, "damage_rate": 0.45},
    "category_5": {"min_wind_ms": 70, "max_wind_ms": 999, "damage_rate": 0.65},
}

# Probability distribution of typhoon categories at landfall (Korea)
# Source: KMA NTC (1951-2023), conditional on direct strike
TYPHOON_CATEGORY_DISTRIBUTION: Dict[str, float] = {
    "category_1": 0.45,
    "category_2": 0.30,
    "category_3": 0.18,
    "category_4": 0.06,
    "category_5": 0.01,
}


# ═══════════════════════════════════════════════════════════════════════
# NEW: SECTOR ABATEMENT TECHNOLOGY STACKS
# Source: IEA ETP 2023, IRENA Power Sector 2023, GCCA Roadmap 2050,
#         WorldSteel Association, IMO GHG Strategy 2023
# Each technology: MAC ($/tCO2e), max_reduction (fraction), available_year
# ═══════════════════════════════════════════════════════════════════════
SECTOR_ABATEMENT_TECHNOLOGIES: Dict[str, List[dict]] = {
    "steel": [
        {"tech": "energy_efficiency", "mac": 15, "max_reduction": 0.10, "available_year": 2020,
         "learning_rate": 0.02, "source": "IEA ETP 2023"},
        {"tech": "scrap_eaf", "mac": 35, "max_reduction": 0.20, "available_year": 2022,
         "learning_rate": 0.03, "source": "WorldSteel 2022"},
        {"tech": "dri_natural_gas", "mac": 55, "max_reduction": 0.15, "available_year": 2025,
         "learning_rate": 0.04, "source": "IEA ETP 2023"},
        {"tech": "dri_hydrogen", "mac": 100, "max_reduction": 0.30, "available_year": 2028,
         "learning_rate": 0.08, "source": "HYBRIT project; IEA 2023"},
        {"tech": "ccus", "mac": 80, "max_reduction": 0.20, "available_year": 2027,
         "learning_rate": 0.05, "source": "Global CCS Institute 2023"},
    ],
    "utilities": [
        {"tech": "efficiency_upgrade", "mac": 10, "max_reduction": 0.08, "available_year": 2020,
         "learning_rate": 0.02, "source": "IEA WEO 2023"},
        {"tech": "coal_to_gas", "mac": 25, "max_reduction": 0.25, "available_year": 2020,
         "learning_rate": 0.01, "source": "IEA WEO 2023"},
        {"tech": "solar_wind", "mac": 35, "max_reduction": 0.30, "available_year": 2020,
         "learning_rate": 0.10, "source": "IRENA Power Sector 2023"},
        {"tech": "battery_storage", "mac": 60, "max_reduction": 0.10, "available_year": 2025,
         "learning_rate": 0.15, "source": "BNEF 2023"},
        {"tech": "ccs_power", "mac": 80, "max_reduction": 0.20, "available_year": 2028,
         "learning_rate": 0.05, "source": "Global CCS Institute 2023"},
    ],
    "cement": [
        {"tech": "energy_efficiency", "mac": 12, "max_reduction": 0.10, "available_year": 2020,
         "learning_rate": 0.02, "source": "GCCA Roadmap 2050"},
        {"tech": "alternative_fuels", "mac": 30, "max_reduction": 0.15, "available_year": 2020,
         "learning_rate": 0.03, "source": "GCCA Roadmap 2050"},
        {"tech": "clinker_substitution", "mac": 25, "max_reduction": 0.15, "available_year": 2022,
         "learning_rate": 0.02, "source": "GCCA Roadmap 2050"},
        {"tech": "novel_cement", "mac": 70, "max_reduction": 0.15, "available_year": 2030,
         "learning_rate": 0.06, "source": "IEA ETP 2023"},
        {"tech": "ccus_cement", "mac": 90, "max_reduction": 0.30, "available_year": 2028,
         "learning_rate": 0.05, "source": "Global CCS Institute 2023"},
    ],
    "petrochemical": [
        {"tech": "energy_efficiency", "mac": 15, "max_reduction": 0.08, "available_year": 2020,
         "learning_rate": 0.02, "source": "IEA ETP 2023"},
        {"tech": "feedstock_optimization", "mac": 30, "max_reduction": 0.12, "available_year": 2020,
         "learning_rate": 0.02, "source": "IEA Future of Petrochemicals 2018"},
        {"tech": "electrification", "mac": 50, "max_reduction": 0.15, "available_year": 2025,
         "learning_rate": 0.06, "source": "IEA ETP 2023"},
        {"tech": "bio_feedstock", "mac": 75, "max_reduction": 0.15, "available_year": 2027,
         "learning_rate": 0.05, "source": "IEA ETP 2023"},
        {"tech": "ccus_chemical", "mac": 85, "max_reduction": 0.25, "available_year": 2028,
         "learning_rate": 0.05, "source": "Global CCS Institute 2023"},
    ],
    "oil_gas": [
        {"tech": "methane_abatement", "mac": 10, "max_reduction": 0.10, "available_year": 2020,
         "learning_rate": 0.02, "source": "IEA Methane Tracker 2023"},
        {"tech": "energy_efficiency", "mac": 20, "max_reduction": 0.10, "available_year": 2020,
         "learning_rate": 0.02, "source": "IEA WEO 2023"},
        {"tech": "electrification", "mac": 45, "max_reduction": 0.15, "available_year": 2025,
         "learning_rate": 0.05, "source": "IEA Net Zero Roadmap 2023"},
        {"tech": "hydrogen_integration", "mac": 80, "max_reduction": 0.15, "available_year": 2030,
         "learning_rate": 0.07, "source": "IEA Hydrogen 2023"},
        {"tech": "ccus_refinery", "mac": 70, "max_reduction": 0.25, "available_year": 2027,
         "learning_rate": 0.05, "source": "Global CCS Institute 2023"},
    ],
    "automotive": [
        {"tech": "ice_efficiency", "mac": 15, "max_reduction": 0.10, "available_year": 2020,
         "learning_rate": 0.02, "source": "ICCT 2023"},
        {"tech": "hybrid_transition", "mac": 25, "max_reduction": 0.15, "available_year": 2020,
         "learning_rate": 0.04, "source": "IEA Global EV Outlook 2023"},
        {"tech": "bev_production", "mac": 40, "max_reduction": 0.35, "available_year": 2022,
         "learning_rate": 0.12, "source": "BNEF EVO 2023"},
        {"tech": "green_manufacturing", "mac": 55, "max_reduction": 0.15, "available_year": 2025,
         "learning_rate": 0.06, "source": "IEA ETP 2023"},
        {"tech": "circular_economy", "mac": 35, "max_reduction": 0.10, "available_year": 2025,
         "learning_rate": 0.03, "source": "Ellen MacArthur Foundation 2023"},
    ],
    "electronics": [
        {"tech": "energy_efficiency", "mac": 10, "max_reduction": 0.15, "available_year": 2020,
         "learning_rate": 0.03, "source": "IEA ETP 2023"},
        {"tech": "renewable_ppa", "mac": 20, "max_reduction": 0.30, "available_year": 2020,
         "learning_rate": 0.08, "source": "RE100 Technical Criteria"},
        {"tech": "process_gas_abatement", "mac": 45, "max_reduction": 0.15, "available_year": 2023,
         "learning_rate": 0.04, "source": "SEMI Sustainability Report 2023"},
        {"tech": "green_hydrogen", "mac": 70, "max_reduction": 0.10, "available_year": 2028,
         "learning_rate": 0.07, "source": "IEA Hydrogen 2023"},
    ],
    "shipping": [
        {"tech": "speed_optimization", "mac": 8, "max_reduction": 0.10, "available_year": 2020,
         "learning_rate": 0.01, "source": "IMO GHG Strategy 2023"},
        {"tech": "energy_efficiency", "mac": 20, "max_reduction": 0.10, "available_year": 2020,
         "learning_rate": 0.02, "source": "IMO MEPC 80"},
        {"tech": "lng_dual_fuel", "mac": 45, "max_reduction": 0.15, "available_year": 2022,
         "learning_rate": 0.03, "source": "DNV Maritime Forecast 2050"},
        {"tech": "methanol_ammonia", "mac": 90, "max_reduction": 0.30, "available_year": 2028,
         "learning_rate": 0.06, "source": "IMO GHG Strategy 2023"},
        {"tech": "wind_assist", "mac": 35, "max_reduction": 0.10, "available_year": 2025,
         "learning_rate": 0.04, "source": "IWSA 2023"},
    ],
    "real_estate": [
        {"tech": "building_efficiency", "mac": 10, "max_reduction": 0.20, "available_year": 2020,
         "learning_rate": 0.03, "source": "IEA Buildings 2023"},
        {"tech": "heat_pump", "mac": 25, "max_reduction": 0.25, "available_year": 2020,
         "learning_rate": 0.08, "source": "IEA Heat Pumps 2023"},
        {"tech": "onsite_solar", "mac": 30, "max_reduction": 0.15, "available_year": 2020,
         "learning_rate": 0.10, "source": "IRENA 2023"},
        {"tech": "smart_building", "mac": 40, "max_reduction": 0.10, "available_year": 2023,
         "learning_rate": 0.05, "source": "IEA Buildings 2023"},
    ],
    "financial": [
        {"tech": "operational_efficiency", "mac": 5, "max_reduction": 0.20, "available_year": 2020,
         "learning_rate": 0.03, "source": "GHG Protocol Scope 1/2 guidance"},
        {"tech": "renewable_procurement", "mac": 15, "max_reduction": 0.40, "available_year": 2020,
         "learning_rate": 0.08, "source": "RE100"},
        {"tech": "green_data_centers", "mac": 30, "max_reduction": 0.20, "available_year": 2023,
         "learning_rate": 0.06, "source": "IEA Data Centres and Networks 2023"},
    ],
}


# ═══════════════════════════════════════════════════════════════════════
# NEW: STRANDED ASSET SCHEDULES
# Source: Carbon Tracker Initiative (2023), "Unburnable Carbon";
#         IEA WEO 2023 phase-out timelines
# ═══════════════════════════════════════════════════════════════════════
STRANDED_ASSET_SCHEDULES: Dict[str, Dict[str, dict]] = {
    "utilities": {
        "net_zero_2050": {
            "phase_out_year": 2035,     # Coal-fired power phase-out
            "annual_writedown_rate": 0.10,  # 10% per year from 2025
            "asset_fraction_at_risk": 0.60,  # 60% of assets are coal-related
            "source": "Carbon Tracker 2023; IEA NZE 2023",
        },
        "below_2c": {
            "phase_out_year": 2040,
            "annual_writedown_rate": 0.07,
            "asset_fraction_at_risk": 0.50,
            "source": "Carbon Tracker 2023",
        },
        "delayed_transition": {
            "phase_out_year": 2045,
            "annual_writedown_rate": 0.08,  # Delayed but sharper
            "asset_fraction_at_risk": 0.45,
            "source": "Carbon Tracker 2023",
        },
        "current_policies": {
            "phase_out_year": 2055,
            "annual_writedown_rate": 0.03,
            "asset_fraction_at_risk": 0.30,
            "source": "Carbon Tracker 2023",
        },
    },
    "oil_gas": {
        "net_zero_2050": {
            "phase_out_year": 2040,
            "annual_writedown_rate": 0.067,  # ~15 year wind-down
            "asset_fraction_at_risk": 0.50,
            "source": "Carbon Tracker 2023; IEA NZE 2023",
        },
        "below_2c": {
            "phase_out_year": 2045,
            "annual_writedown_rate": 0.05,
            "asset_fraction_at_risk": 0.40,
            "source": "Carbon Tracker 2023",
        },
        "delayed_transition": {
            "phase_out_year": 2048,
            "annual_writedown_rate": 0.055,
            "asset_fraction_at_risk": 0.35,
            "source": "Carbon Tracker 2023",
        },
        "current_policies": {
            "phase_out_year": 2060,
            "annual_writedown_rate": 0.02,
            "asset_fraction_at_risk": 0.15,
            "source": "Carbon Tracker 2023",
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════
# NEW: SCENARIO WACC SPREADS (basis points)
# Rationale: Climate scenarios increase cost of capital through physical
# risk premia and transition policy uncertainty premia. Magnitudes are
# calibrated estimates informed by:
# - Battiston et al. (2017), Nature Climate Change: equity risk-premium
#   differentials across climate-policy scenarios (used for directional
#   ordering, NOT as direct source of these bp values).
# - NGFS (2023), "Climate Scenarios: Technical Documentation v4":
#   qualitative risk-premium discussion (Section 4.3).
# - Bolton & Kacperczyk (2021), "Do investors care about carbon risk?",
#   J. Financial Economics: ~60bp carbon premium in equities.
# Note: Exact spread values are model assumptions, not published figures.
# ═══════════════════════════════════════════════════════════════════════
SCENARIO_WACC_SPREADS: Dict[str, float] = {
    "net_zero_2050": 0.005,       # +50bp - orderly transition, lowest uncertainty
    "below_2c": 0.0075,           # +75bp
    "delayed_transition": 0.015,  # +150bp - policy uncertainty premium
    "current_policies": 0.020,    # +200bp - highest physical risk premium
}


# ═══════════════════════════════════════════════════════════════════════
# NEW: BUSINESS INTERRUPTION PARAMETERS
# Source: Munich Re NatCatSERVICE (2023 Annual Report, Table A3);
# Swiss Re sigma 1/2023, "Natural catastrophes in 2022", Appendix.
# Downtime days are typical ranges for industrial facilities; actual
# recovery times vary significantly by facility preparedness.
# ═══════════════════════════════════════════════════════════════════════
BUSINESS_INTERRUPTION_DAYS: Dict[str, Dict[str, float]] = {
    "flood": {
        "minor": 5,      # < 30cm inundation
        "moderate": 15,   # 30-100cm
        "severe": 45,     # 100-200cm
        "catastrophic": 90,  # > 200cm
    },
    "typhoon": {
        "category_1": 3,
        "category_2": 7,
        "category_3": 15,
        "category_4": 30,
        "category_5": 60,
    },
    "heatwave": {
        "per_day_outdoor": 0.3,   # 0.3 days lost per heatwave day (outdoor work)
        "per_day_indoor": 0.05,   # 0.05 days lost per heatwave day (indoor)
    },
    "drought": {
        "minor": 3,
        "moderate": 10,
        "severe": 25,
    },
}

# Sector classification for heatwave exposure
# Source: ILO (2019), "Working on a Warmer Planet"
SECTOR_OUTDOOR_EXPOSURE: Dict[str, float] = {
    "steel": 0.30,          # Partial outdoor (blast furnace area)
    "petrochemical": 0.25,
    "cement": 0.35,
    "utilities": 0.40,      # Power plant outdoor operations
    "oil_gas": 0.35,
    "shipping": 0.50,       # Port operations
    "automotive": 0.15,     # Mostly indoor assembly
    "electronics": 0.05,    # Cleanroom (indoor)
    "real_estate": 0.20,    # Construction/maintenance
    "financial": 0.02,      # Office
}


# ═══════════════════════════════════════════════════════════════════════
# NEW: TRANSITION RISK SECTOR PARAMETERS
# ═══════════════════════════════════════════════════════════════════════

# Energy cost as fraction of total operating cost
# Source: IEA Energy Efficiency Indicators (2023)
SECTOR_ENERGY_COST_SHARE: Dict[str, float] = {
    "steel": 0.25,          # Ref: WorldSteel 2022
    "petrochemical": 0.20,  # Ref: IEA Petrochemicals 2018
    "cement": 0.30,         # Ref: GCCA 2023
    "utilities": 0.40,      # Fuel is primary input
    "oil_gas": 0.15,        # Ref: IEA WEO 2023
    "shipping": 0.35,       # Bunker fuel dominant
    "automotive": 0.08,     # Ref: OICA 2023
    "electronics": 0.10,    # Electricity for fabs
    "real_estate": 0.12,    # HVAC + operations
    "financial": 0.03,      # Office energy
}

# Cost pass-through rate (fraction of cost increase passed to customers)
# Source: Demailly & Quirion (2008); Reinaud (2008), IEA
SECTOR_COST_PASSTHROUGH: Dict[str, float] = {
    "steel": 0.40,          # Import-competing, limited pass-through
    "petrochemical": 0.45,
    "cement": 0.60,         # Regional, higher pass-through
    "utilities": 0.80,      # Regulated, high pass-through
    "oil_gas": 0.50,        # Global commodity pricing
    "shipping": 0.35,       # Competitive, low pass-through
    "automotive": 0.30,     # Consumer price sensitivity
    "electronics": 0.25,    # Global competition
    "real_estate": 0.70,    # Can pass to tenants
    "financial": 0.60,      # Fee adjustments
}

# Scope 3 exposure as fraction of carbon cost
# Source: CDP Supply Chain Report 2023
SECTOR_SCOPE3_EXPOSURE: Dict[str, float] = {
    "oil_gas": 0.25,        # Downstream combustion
    "automotive": 0.20,     # Use-phase emissions
    "petrochemical": 0.15,
    "shipping": 0.10,       # Supply chain
    "steel": 0.08,
    "cement": 0.06,
    "utilities": 0.05,
    "electronics": 0.08,
    "real_estate": 0.04,
    "financial": 0.03,      # Financed emissions (limited scope)
}


# ═══════════════════════════════════════════════════════════════════════
# NEW: S-CURVE PARAMETERS FOR EMISSION REDUCTION
# Source: Bass (1969) diffusion model calibrated to NGFS pathways
# ═══════════════════════════════════════════════════════════════════════
SCENARIO_SCURVE_PARAMS: Dict[str, Dict[str, float]] = {
    "net_zero_2050": {
        "k": 0.25,    # Steepness: moderate (orderly early start)
        "t0": 2032,   # Midpoint: early
        "L_max": 0.95, # Maximum reduction achievable
    },
    "below_2c": {
        "k": 0.22,
        "t0": 2035,
        "L_max": 0.85,
    },
    "delayed_transition": {
        "k": 0.40,    # Steepness: high (sudden catch-up)
        "t0": 2038,   # Midpoint: late
        "L_max": 0.80,
    },
    "current_policies": {
        "k": 0.12,    # Steepness: low (gradual)
        "t0": 2040,
        "L_max": 0.40,
    },
}


# ═══════════════════════════════════════════════════════════════════════
# NEW: REGULATORY DEADLINES
# ═══════════════════════════════════════════════════════════════════════
REGULATORY_DEADLINES: Dict[str, dict] = {
    "kssb_mandatory": {
        "name": "KSSB 의무 공시",
        "date": "2025-01-01",
        "description": "자산 2조원 이상 상장사 의무 공시",
        "source": "금융위원회, 'ESG 공시 제도 도입 방안' (2023.02.16 보도자료)",
    },
    "issb_effective": {
        "name": "ISSB (IFRS S1/S2) 발효",
        "date": "2024-01-01",
        "description": "글로벌 지속가능성 공시 기준 발효 (IFRS S1/S2, 2024-01-01 이후 회계연도)",
        "source": "ISSB, IFRS S1 para. C1; Korean mandatory adoption from 2025",
    },
    "kets_phase4": {
        "name": "K-ETS 4기",
        "date": "2026-01-01",
        "description": "배출권거래제 4기 시행 (강화된 할당)",
        "source": "환경부, '배출권거래제 제4차 계획기간 기본계획' (2024)",
    },
    "eu_cbam_full": {
        "name": "EU CBAM 본격 시행",
        "date": "2026-01-01",
        "description": "EU 탄소국경조정제도 본격 시행",
        "source": "EU Regulation 2023/956, Official Journal L 130/52",
    },
    "kssb_full_scope": {
        "name": "KSSB 전면 적용",
        "date": "2027-01-01",
        "description": "전 상장사 의무 공시 확대",
        "source": "금융위원회, 'ESG 공시 제도 도입 방안' (2023.02.16)",
    },
}
