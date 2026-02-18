"""Transition risk endpoints."""

from fastapi import APIRouter, HTTPException, Query

from ...core.config import SCENARIOS
from ...services.transition_risk import analyse_scenario, get_summary, compare_scenarios

router = APIRouter()

_VALID_PRICING_REGIMES = ("global", "kets")


def _validate_scenario(scenario: str) -> None:
    if scenario not in SCENARIOS:
        raise HTTPException(400, f"Unknown scenario: {scenario}. Valid: {list(SCENARIOS.keys())}")


def _validate_pricing_regime(pricing_regime: str) -> None:
    if pricing_regime not in _VALID_PRICING_REGIMES:
        raise HTTPException(400, f"Unknown pricing_regime: {pricing_regime}. Valid: {list(_VALID_PRICING_REGIMES)}")


@router.get("/analysis")
def transition_risk_analysis(
    scenario: str = Query("net_zero_2050"),
    pricing_regime: str = Query("global", description="Pricing regime: global or kets"),
):
    _validate_scenario(scenario)
    _validate_pricing_regime(pricing_regime)
    return analyse_scenario(scenario, pricing_regime=pricing_regime)


@router.get("/summary")
def transition_risk_summary(
    scenario: str = Query("net_zero_2050"),
    pricing_regime: str = Query("global", description="Pricing regime: global or kets"),
):
    _validate_scenario(scenario)
    _validate_pricing_regime(pricing_regime)
    return get_summary(scenario, pricing_regime=pricing_regime)


@router.get("/comparison")
def transition_risk_comparison(
    pricing_regime: str = Query("global", description="Pricing regime: global or kets"),
):
    _validate_pricing_regime(pricing_regime)
    return compare_scenarios(pricing_regime=pricing_regime)
