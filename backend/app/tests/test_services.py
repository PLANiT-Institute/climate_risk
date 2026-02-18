"""Unit tests for core services – updated for analytical model upgrades."""

import pytest
from ..services.transition_risk import analyse_scenario, get_summary, compare_scenarios
from ..services.physical_risk import assess_physical_risk
from ..services.esg_compliance import assess_framework, get_disclosure_data
from ..services.carbon_pricing import (
    get_carbon_price_trajectory,
    get_marginal_abatement_cost,
    get_kets_price_trajectory,
    calculate_kets_free_allocation,
)
from ..services.risk_math import (
    npv,
    npv_from_list,
    gumbel_return_period,
    exceedance_probability,
    logistic_s_curve,
    wacc_scenario_adjusted,
    piecewise_linear_interpolate,
)
from ..services.climate_science import (
    get_warming_at_year,
    get_warming_delta,
    get_hazard_frequency_multiplier,
)
from ..core.config import SCENARIOS, PROJECTION_YEARS


# ═══════════════════════════════════════════════════════════════════════
# EXISTING TESTS (updated where needed)
# ═══════════════════════════════════════════════════════════════════════

def test_carbon_price_trajectory():
    prices = get_carbon_price_trajectory("net_zero_2050", PROJECTION_YEARS)
    assert prices[2025] == pytest.approx(75.0)
    assert prices[2030] == pytest.approx(130.0)
    assert prices[2050] == pytest.approx(250.0)
    # Monotonically increasing
    sorted_years = sorted(prices.keys())
    for i in range(1, len(sorted_years)):
        assert prices[sorted_years[i]] >= prices[sorted_years[i - 1]]


def test_transition_analysis_structure():
    result = analyse_scenario("net_zero_2050")
    assert result["scenario"] == "net_zero_2050"
    assert result["scenario_name"] == "Net Zero 2050"
    assert len(result["facilities"]) > 0
    assert result["total_npv"] < 0  # costs should be negative
    fac = result["facilities"][0]
    assert "emission_pathway" in fac
    assert "annual_impacts" in fac
    assert fac["risk_level"] in ("High", "Medium", "Low")


def test_transition_summary():
    summary = get_summary("current_policies")
    assert summary["total_facilities"] > 0
    assert summary["high_risk_count"] + summary["medium_risk_count"] + summary["low_risk_count"] == summary["total_facilities"]
    assert "cost_breakdown" in summary


def test_scenario_comparison():
    comp = compare_scenarios()
    assert len(comp["scenarios"]) == 4
    assert len(comp["npv_comparison"]) == 4
    for sid in comp["scenarios"]:
        assert sid in comp["emission_pathways"]
        assert sid in comp["risk_distribution"]
        assert sid in comp["cost_trends"]


def test_physical_risk():
    result = assess_physical_risk()
    assert result["model_status"] == "analytical_v1"
    assert result["total_facilities"] > 0
    for fac in result["facilities"]:
        assert len(fac["hazards"]) > 0
        assert fac["overall_risk_level"] in ("High", "Medium", "Low")


def test_esg_assessment():
    for fw in ("tcfd", "issb", "kssb"):
        result = assess_framework(fw)
        assert result["framework"] == fw
        assert 0 <= result["overall_score"] <= 100
        assert len(result["categories"]) > 0
        assert len(result["checklist"]) > 0


def test_esg_disclosure():
    result = get_disclosure_data("tcfd")
    assert "metrics" in result
    assert "narrative_sections" in result
    assert result["metrics"]["emissions"]["scope1_tco2e"] > 0


# ═══════════════════════════════════════════════════════════════════════
# NEW: RISK MATH UTILITY TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_npv_basic():
    """NPV of equal cash flows should be less than simple sum (discounting)."""
    cfs = {2025: -100, 2026: -100, 2027: -100}
    result = npv(cfs, 0.10, 2024)
    # -100/1.1 + -100/1.21 + -100/1.331 = -248.69
    assert -250 < result < -240
    assert result > -300


def test_gumbel_return_period_monotonic():
    """Higher return period should give higher quantile."""
    q10 = gumbel_return_period(200, 50, 10)
    q50 = gumbel_return_period(200, 50, 50)
    q100 = gumbel_return_period(200, 50, 100)
    assert q10 < q50 < q100


def test_exceedance_probability():
    """100-year event over 30 years should have ~26% exceedance probability."""
    p = exceedance_probability(100, 30)
    assert 0.25 < p < 0.27


def test_logistic_s_curve():
    """S-curve should be near 0 before midpoint, near L after."""
    val_early = logistic_s_curve(2020, 1.0, 0.3, 2035)
    val_mid = logistic_s_curve(2035, 1.0, 0.3, 2035)
    val_late = logistic_s_curve(2060, 1.0, 0.3, 2035)
    assert val_early < 0.05
    assert 0.45 < val_mid < 0.55
    assert val_late > 0.95


def test_wacc_scenario_adjusted():
    """Adjusted WACC should always be higher than base."""
    base = 0.08
    for scenario in SCENARIOS:
        adjusted = wacc_scenario_adjusted(base, scenario, "steel")
        assert adjusted > base


def test_piecewise_interpolation():
    """Interpolation between knots should be exact at knots."""
    knots = {2025: 75.0, 2030: 130.0, 2050: 250.0}
    assert piecewise_linear_interpolate(knots, 2025) == 75.0
    assert piecewise_linear_interpolate(knots, 2030) == 130.0
    assert piecewise_linear_interpolate(knots, 2050) == 250.0
    # Midpoint should be between neighbors
    mid = piecewise_linear_interpolate(knots, 2027)
    assert 75.0 < mid < 130.0


# ═══════════════════════════════════════════════════════════════════════
# NEW: CLIMATE SCIENCE TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_warming_projections():
    """Current policies should produce more warming than net zero."""
    cp_2050 = get_warming_at_year("current_policies", 2050)
    nz_2050 = get_warming_at_year("net_zero_2050", 2050)
    assert cp_2050 > nz_2050


def test_warming_delta_positive():
    """Warming delta should be positive for future years."""
    delta = get_warming_delta("current_policies", 2050)
    assert delta > 0


def test_hazard_frequency_multiplier():
    """Climate change should increase hazard frequency."""
    mult = get_hazard_frequency_multiplier("flood", "current_policies", 2050)
    assert mult > 1.0
    # Net zero should have lower multiplier
    mult_nz = get_hazard_frequency_multiplier("flood", "net_zero_2050", 2050)
    assert mult > mult_nz


# ═══════════════════════════════════════════════════════════════════════
# NEW: PHYSICAL RISK ANALYTICAL MODEL TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_physical_risk_scenario_sensitivity():
    """Current policies should have higher EAL than net zero."""
    cp = assess_physical_risk(scenario_id="current_policies", year=2050)
    nz = assess_physical_risk(scenario_id="net_zero_2050", year=2050)

    cp_total_eal = sum(f["total_expected_annual_loss"] for f in cp["facilities"])
    nz_total_eal = sum(f["total_expected_annual_loss"] for f in nz["facilities"])
    assert cp_total_eal > nz_total_eal


def test_physical_risk_coastal_vs_inland_typhoon():
    """Coastal facilities should face higher typhoon risk than inland."""
    result = assess_physical_risk()
    coastal_typhoon_loss = 0
    inland_typhoon_loss = 0
    coastal_count = 0
    inland_count = 0

    for fac in result["facilities"]:
        for h in fac["hazards"]:
            if h["hazard_type"] == "typhoon":
                # Classify based on coordinates (rough)
                if fac["longitude"] > 129.0 or fac["longitude"] < 126.7 or fac["latitude"] < 35.2:
                    coastal_typhoon_loss += h["potential_loss"]
                    coastal_count += 1
                else:
                    inland_typhoon_loss += h["potential_loss"]
                    inland_count += 1

    if coastal_count > 0 and inland_count > 0:
        avg_coastal = coastal_typhoon_loss / coastal_count
        avg_inland = inland_typhoon_loss / inland_count
        assert avg_coastal > avg_inland


def test_physical_risk_has_new_fields():
    """New analytical fields should be present in hazard data."""
    result = assess_physical_risk()
    assert result.get("scenario") is not None
    assert result.get("assessment_year") is not None
    assert result.get("warming_above_preindustrial") is not None

    for fac in result["facilities"]:
        for h in fac["hazards"]:
            assert "return_period_years" in h
            assert "climate_change_multiplier" in h
            assert "business_interruption_cost" in h


def test_physical_risk_return_periods_valid():
    """Return periods should be positive finite values."""
    result = assess_physical_risk()
    for fac in result["facilities"]:
        for h in fac["hazards"]:
            rp = h["return_period_years"]
            assert rp > 0
            assert rp < 10000


# ═══════════════════════════════════════════════════════════════════════
# NEW: TRANSITION RISK UPGRADED TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_transition_scurve_nonlinear():
    """S-curve reduction should be nonlinear (more reduction later)."""
    result = analyse_scenario("net_zero_2050")
    fac = result["facilities"][0]
    pathway = fac["emission_pathway"]
    # Early reduction should be less than later reduction
    early_rf = pathway[0]["reduction_factor"]  # 2025
    later_rf = pathway[-1]["reduction_factor"]  # 2050
    assert later_rf > early_rf
    # Difference between adjacent years shouldn't be uniform
    rfs = [p["reduction_factor"] for p in pathway]
    diffs = [rfs[i+1] - rfs[i] for i in range(len(rfs)-1)]
    # Not all diffs are equal (non-linear)
    assert max(diffs) - min(diffs) > 0.001


def test_transition_stranded_assets_utilities():
    """Utilities should have stranded asset writedowns under net zero."""
    result = analyse_scenario("net_zero_2050")
    utilities_facs = [f for f in result["facilities"] if f["sector"] == "utilities"]
    assert len(utilities_facs) > 0
    for fac in utilities_facs:
        stranded_total = sum(
            ai.get("stranded_asset_writedown", 0)
            for ai in fac["annual_impacts"]
        )
        assert stranded_total > 0, "Utilities should have stranded asset writedowns"


def test_transition_wacc_scenario_difference():
    """Different scenarios should produce different NPV due to WACC adjustment."""
    nz = analyse_scenario("net_zero_2050")
    cp = analyse_scenario("current_policies")
    # NPVs should differ (even if both negative)
    assert nz["total_npv"] != cp["total_npv"]


def test_transition_scope3_present():
    """Scope 3 impact should be present in annual impacts."""
    result = analyse_scenario("net_zero_2050")
    fac = result["facilities"][0]
    has_scope3 = any(
        ai.get("scope3_impact", 0) > 0
        for ai in fac["annual_impacts"]
    )
    assert has_scope3, "Scope 3 impact should be > 0 for at least some years"


# ═══════════════════════════════════════════════════════════════════════
# NEW: CARBON PRICING UPGRADED TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_carbon_price_multipoint_smooth():
    """Year-over-year price change should be < 25% (smooth trajectory)."""
    all_years = list(range(2024, 2051))
    prices = get_carbon_price_trajectory("net_zero_2050", all_years)
    for i in range(1, len(all_years)):
        y = all_years[i]
        y_prev = all_years[i - 1]
        if prices[y_prev] > 0:
            change_pct = abs(prices[y] - prices[y_prev]) / prices[y_prev]
            assert change_pct < 0.25, f"Price change at {y}: {change_pct:.1%}"


def test_mac_monotonically_increasing():
    """Higher reduction should require higher (or equal) MAC."""
    sector = "steel"
    reductions = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]
    macs = [get_marginal_abatement_cost(sector, r, 2030) for r in reductions]
    for i in range(1, len(macs)):
        assert macs[i] >= macs[i - 1], f"MAC not monotonic: {macs[i]} < {macs[i-1]} at reduction {reductions[i]}"


def test_kets_price_trajectory():
    """K-ETS prices should be available and positive."""
    prices = get_kets_price_trajectory("net_zero_2050", PROJECTION_YEARS)
    assert len(prices) == len(PROJECTION_YEARS)
    for y, p in prices.items():
        assert p > 0


# ═══════════════════════════════════════════════════════════════════════
# NEW: ESG DATA-DRIVEN TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_esg_data_driven_metrics_score():
    """Metrics score should be >= 70 given full facility data."""
    result = assess_framework("issb")
    metrics_cat = [c for c in result["categories"] if c["category"] == "지표 및 목표"]
    assert len(metrics_cat) == 1
    assert metrics_cat[0]["score"] >= 70


def test_esg_maturity_level_present():
    """Maturity level should be present in assessment."""
    for fw in ("tcfd", "issb", "kssb"):
        result = assess_framework(fw)
        assert "maturity_level" in result
        assert "level" in result["maturity_level"]
        assert 1 <= result["maturity_level"]["level"] <= 5


def test_esg_gap_analysis():
    """Gap analysis should identify actionable items."""
    result = assess_framework("issb")
    assert "gap_analysis" in result
    gaps = result["gap_analysis"]
    assert len(gaps) > 0
    for gap in gaps:
        assert "category" in gap
        assert "priority_score" in gap
        assert "recommended_actions" in gap
        assert len(gap["recommended_actions"]) > 0


def test_esg_regulatory_deadlines():
    """KSSB framework should have Korean regulatory deadlines."""
    result = assess_framework("kssb")
    assert "regulatory_deadlines" in result
    deadlines = result["regulatory_deadlines"]
    assert len(deadlines) > 0
    assert any("KSSB" in dl.get("name", "") for dl in deadlines)


# ═══════════════════════════════════════════════════════════════════════
# NEW: K-ETS FREE ALLOCATION TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_kets_free_allocation_steel():
    """Steel sector should get 97% free allocation in base year."""
    result = calculate_kets_free_allocation("steel", 100000, 2024)
    assert result["allocation_ratio"] == pytest.approx(0.97)
    assert result["free_allocation_tco2e"] == pytest.approx(97000.0)


def test_kets_free_allocation_tightening():
    """Allocation should decrease over time due to annual tightening."""
    result_2024 = calculate_kets_free_allocation("steel", 100000, 2024)
    result_2030 = calculate_kets_free_allocation("steel", 100000, 2030)
    assert result_2030["allocation_ratio"] < result_2024["allocation_ratio"]
    # Steel: 0.97 - 0.01 * 6 = 0.91
    assert result_2030["allocation_ratio"] == pytest.approx(0.91)


def test_kets_free_allocation_floor_at_zero():
    """Allocation ratio should never go below zero."""
    # Financial sector: 0.80 - 0.02 * 50 = -0.20 → should clamp to 0
    result = calculate_kets_free_allocation("financial", 100000, 2074)
    assert result["allocation_ratio"] == 0.0
    assert result["free_allocation_tco2e"] == 0.0


def test_kets_pricing_regime_reduces_carbon_cost():
    """K-ETS free allocation should reduce total NPV impact vs global."""
    global_result = analyse_scenario("net_zero_2050", pricing_regime="global")
    kets_result = analyse_scenario("net_zero_2050", pricing_regime="kets")
    # K-ETS should have less negative NPV (free allocation reduces carbon cost)
    assert kets_result["total_npv"] > global_result["total_npv"]


def test_kets_analysis_has_allocation_fields():
    """K-ETS analysis should include allocation fields in annual impacts."""
    result = analyse_scenario("net_zero_2050", pricing_regime="kets")
    fac = result["facilities"][0]
    ai = fac["annual_impacts"][0]
    assert "kets_free_allocation" in ai
    assert "kets_excess_emissions" in ai
    assert "kets_price_krw" in ai
    assert ai["kets_free_allocation"] is not None
    assert ai["kets_price_krw"] is not None


def test_global_regime_no_kets_fields():
    """Global pricing regime should have None for K-ETS fields."""
    result = analyse_scenario("net_zero_2050", pricing_regime="global")
    fac = result["facilities"][0]
    ai = fac["annual_impacts"][0]
    assert ai["kets_free_allocation"] is None
    assert ai["kets_excess_emissions"] is None
    assert ai["kets_price_krw"] is None


def test_kets_pricing_regime_field_in_response():
    """Response should include pricing_regime field."""
    for regime in ("global", "kets"):
        result = analyse_scenario("net_zero_2050", pricing_regime=regime)
        assert result["pricing_regime"] == regime


# ═══════════════════════════════════════════════════════════════════════
# NEW: OPEN-METEO / PHYSICAL RISK API DATA TESTS
# ═══════════════════════════════════════════════════════════════════════

from ..services.open_meteo import (
    derive_gumbel_params,
    derive_heatwave_days,
    derive_drought_days,
    get_api_derived_baselines,
    _cache, _cache_ttl, _cache_set, _cache_key,
)
from unittest.mock import patch
import random


def test_derive_gumbel_params_from_data():
    """Gumbel fitting on synthetic data should return reasonable params."""
    random.seed(42)
    # Simulate 10 years of daily precipitation (3650 days)
    daily_precip = []
    for year_idx in range(10):
        for day in range(365):
            # Mostly low, occasional high
            val = random.expovariate(1 / 5.0)  # mean 5mm
            daily_precip.append(val)

    result = derive_gumbel_params(daily_precip)
    assert result is not None
    assert result["location"] > 0
    assert result["scale"] > 0


def test_derive_heatwave_days():
    """Synthetic temperature data with known hot days should count correctly."""
    # 10 years, with exactly 10 days above 33°C per year
    daily_tmax = []
    for year_idx in range(10):
        for day in range(365):
            if day < 10:
                daily_tmax.append(35.0)  # heatwave
            else:
                daily_tmax.append(25.0)  # normal

    result = derive_heatwave_days(daily_tmax)
    assert result is not None
    assert result == pytest.approx(10.0, abs=0.5)


def test_derive_drought_days():
    """Synthetic precip data with known dry spells should count correctly."""
    # 10 years: 30 consecutive dry days per year, rest rainy
    daily_precip = []
    for year_idx in range(10):
        for day in range(365):
            if day < 30:
                daily_precip.append(0.0)  # dry
            else:
                daily_precip.append(10.0)  # wet

    result = derive_drought_days(daily_precip)
    assert result is not None
    assert result == pytest.approx(30.0, abs=1.0)


def test_api_baselines_returns_none_on_failure():
    """API failure should return None."""
    with patch("app.services.open_meteo.fetch_historical_weather", return_value=None):
        result = get_api_derived_baselines(99.0, 99.0)
        assert result is None


def test_physical_risk_fallback_when_api_off():
    """use_api_data=False should produce same result as before (hardcoded config)."""
    result = assess_physical_risk(use_api_data=False)
    assert result["data_source"] == "hardcoded_config"
    assert result["model_status"] == "analytical_v1"
    assert result["total_facilities"] > 0


def test_physical_risk_with_api_data_flag():
    """use_api_data=True should run without errors (API may fail → fallback)."""
    # Mock the API to return None so we test fallback behavior
    with patch("app.services.physical_risk.get_api_derived_baselines", return_value=None):
        result = assess_physical_risk(use_api_data=True)
        assert result["data_source"] == "open_meteo_api"
        assert result["total_facilities"] > 0
        # Should still produce valid results via fallback
        for fac in result["facilities"]:
            assert len(fac["hazards"]) == 5


def test_open_meteo_cache():
    """Cache should store and retrieve results."""
    key = _cache_key(35.18, 129.08)
    test_data = {"gumbel_params": {"location": 200, "scale": 50}, "heatwave_days": 12.0, "drought_days": 20.0, "wind_speed_annual_max_ms": 25.0}
    _cache_set(key, test_data)
    from ..services.open_meteo import _cache_get
    cached = _cache_get(key)
    assert cached is not None
    assert cached["gumbel_params"]["location"] == 200
    # Cleanup
    _cache.pop(key, None)
    _cache_ttl.pop(key, None)
