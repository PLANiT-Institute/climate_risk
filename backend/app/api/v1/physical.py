"""Physical risk endpoints with scenario/year parameters."""

from typing import Optional, List
from fastapi import APIRouter, Query
from pydantic import BaseModel

from ...services.physical_risk import assess_physical_risk
from ...models.schemas import FacilityIn

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

class SimulateRequest(BaseModel):
    scenario: Optional[str] = "current_policies"
    year: Optional[int] = 2030
    use_api_data: bool = True
    facilities: List[FacilityIn]

@router.post("/simulate")
def physical_risk_simulate(payload: SimulateRequest):
    kwargs = {
        "scenario_id": payload.scenario,
        "year": payload.year,
        "use_api_data": payload.use_api_data,
        "facilities": [f.model_dump() for f in payload.facilities]
    }
    return assess_physical_risk(**kwargs)
