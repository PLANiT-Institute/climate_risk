"""Partner API: external companies submit facility data and run analyses."""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ...core.config import SCENARIOS, get_sector_warnings
from ...models.schemas import PartnerSessionCreate, PartnerSessionOut
from ...services import partner_store
from ...services.transition_risk import analyse_scenario, get_summary, compare_scenarios
from ...services.physical_risk import assess_physical_risk
from ...services.esg_compliance import assess_framework, get_disclosure_data

router = APIRouter()

_VALID_PRICING_REGIMES = ("global", "kets")
_VALID_FRAMEWORKS = ("issb", "tcfd", "kssb")


def _validate_scenario(scenario: str) -> None:
    if scenario not in SCENARIOS:
        raise HTTPException(400, f"Unknown scenario: {scenario}. Valid: {list(SCENARIOS.keys())}")


def _validate_pricing_regime(pricing_regime: str) -> None:
    if pricing_regime not in _VALID_PRICING_REGIMES:
        raise HTTPException(400, f"Unknown pricing_regime: {pricing_regime}. Valid: {list(_VALID_PRICING_REGIMES)}")


def _validate_framework(framework: str) -> None:
    if framework not in _VALID_FRAMEWORKS:
        raise HTTPException(400, f"Unknown framework: {framework}. Valid: {list(_VALID_FRAMEWORKS)}")


def _get_partner_facilities(partner_id: str) -> list[dict]:
    """Retrieve facilities for a partner session or raise 404."""
    facilities = partner_store.get_facilities(partner_id)
    if facilities is None:
        raise HTTPException(404, "Partner session not found or expired")
    return facilities


# ── Session Management ────────────────────────────────────────────────

@router.post("/sessions", response_model=PartnerSessionOut, status_code=201)
def create_session(body: PartnerSessionCreate):
    """Create a partner session with facility data."""
    # Convert Pydantic models to dicts for internal storage
    fac_dicts = [f.model_dump() for f in body.facilities]

    # Check for duplicate facility_ids
    ids = [f["facility_id"] for f in fac_dicts]
    if len(ids) != len(set(ids)):
        raise HTTPException(422, "Duplicate facility_id values found")

    session = partner_store.create_session(body.company_name, fac_dicts)
    sectors = sorted({f["sector"] for f in fac_dicts})
    warnings = get_sector_warnings(set(sectors))
    expires_in = int(session["expires_at"] - time.time())

    return PartnerSessionOut(
        partner_id=session["partner_id"],
        company_name=session["company_name"],
        facility_count=len(fac_dicts),
        sectors=sectors,
        sector_warnings=warnings,
        expires_in_seconds=expires_in,
    )


@router.get("/sessions/{partner_id}")
def get_session(partner_id: str):
    """Get partner session info."""
    session = partner_store.get_session(partner_id)
    if session is None:
        raise HTTPException(404, "Partner session not found or expired")
    expires_in = int(session["expires_at"] - time.time())
    sectors = sorted({f["sector"] for f in session["facilities"]})
    return {
        "partner_id": session["partner_id"],
        "company_name": session["company_name"],
        "facility_count": len(session["facilities"]),
        "sectors": sectors,
        "expires_in_seconds": expires_in,
    }


@router.delete("/sessions/{partner_id}", status_code=204)
def delete_session(partner_id: str):
    """Delete a partner session."""
    if not partner_store.delete_session(partner_id):
        raise HTTPException(404, "Partner session not found or expired")
    return None


@router.get("/sessions/{partner_id}/facilities")
def list_facilities(partner_id: str):
    """List facilities in a partner session."""
    facilities = _get_partner_facilities(partner_id)
    return {"facilities": facilities, "count": len(facilities)}


# ── Transition Risk Analysis ──────────────────────────────────────────

@router.get("/sessions/{partner_id}/transition-risk/analysis")
def partner_transition_analysis(
    partner_id: str,
    scenario: str = Query("net_zero_2050"),
    pricing_regime: str = Query("global"),
):
    _validate_scenario(scenario)
    _validate_pricing_regime(pricing_regime)
    facilities = _get_partner_facilities(partner_id)
    return analyse_scenario(scenario, pricing_regime=pricing_regime, facilities=facilities)


@router.get("/sessions/{partner_id}/transition-risk/summary")
def partner_transition_summary(
    partner_id: str,
    scenario: str = Query("net_zero_2050"),
    pricing_regime: str = Query("global"),
):
    _validate_scenario(scenario)
    _validate_pricing_regime(pricing_regime)
    facilities = _get_partner_facilities(partner_id)
    return get_summary(scenario, pricing_regime=pricing_regime, facilities=facilities)


@router.get("/sessions/{partner_id}/transition-risk/comparison")
def partner_transition_comparison(
    partner_id: str,
    pricing_regime: str = Query("global"),
):
    _validate_pricing_regime(pricing_regime)
    facilities = _get_partner_facilities(partner_id)
    return compare_scenarios(pricing_regime=pricing_regime, facilities=facilities)


# ── Physical Risk Analysis ────────────────────────────────────────────

@router.get("/sessions/{partner_id}/physical-risk/assessment")
def partner_physical_risk(
    partner_id: str,
    scenario: Optional[str] = Query(default=None),
    year: Optional[int] = Query(default=None, ge=2025, le=2100),
    use_api_data: bool = Query(default=False),
):
    facilities = _get_partner_facilities(partner_id)
    kwargs: dict = {"facilities": facilities, "use_api_data": use_api_data}
    if scenario is not None:
        _validate_scenario(scenario)
        kwargs["scenario_id"] = scenario
    if year is not None:
        kwargs["year"] = year
    return assess_physical_risk(**kwargs)


# ── ESG Assessment ────────────────────────────────────────────────────

@router.get("/sessions/{partner_id}/esg/assessment")
def partner_esg_assessment(
    partner_id: str,
    framework: str = Query("tcfd"),
):
    _validate_framework(framework)
    facilities = _get_partner_facilities(partner_id)
    return assess_framework(framework, facilities=facilities)


@router.get("/sessions/{partner_id}/esg/disclosure-data")
def partner_esg_disclosure(
    partner_id: str,
    framework: str = Query("tcfd"),
):
    _validate_framework(framework)
    facilities = _get_partner_facilities(partner_id)
    return get_disclosure_data(framework, facilities=facilities)
