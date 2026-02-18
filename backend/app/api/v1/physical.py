"""Physical risk endpoints with scenario/year parameters."""

from typing import Optional
from fastapi import APIRouter, Query

from ...services.physical_risk import assess_physical_risk

router = APIRouter()


@router.get("/assessment")
def physical_risk_assessment(
    scenario: Optional[str] = Query(
        default=None,
        description="NGFS scenario ID (net_zero_2050, below_2c, delayed_transition, current_policies)",
    ),
    year: Optional[int] = Query(
        default=None,
        description="Assessment year (2025-2100)",
        ge=2025,
        le=2100,
    ),
    use_api_data: bool = Query(
        default=False,
        description="Open-Meteo API 기반 기후 데이터 사용",
    ),
):
    kwargs = {}
    if scenario is not None:
        kwargs["scenario_id"] = scenario
    if year is not None:
        kwargs["year"] = year
    kwargs["use_api_data"] = use_api_data
    return assess_physical_risk(**kwargs)
