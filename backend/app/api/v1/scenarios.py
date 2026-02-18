"""Scenario endpoints."""

from fastapi import APIRouter, HTTPException

from ...services.scenario_engine import list_scenarios, get_scenario

router = APIRouter()


@router.get("/scenarios")
def get_scenarios():
    return list_scenarios()


@router.get("/scenarios/{scenario_id}")
def get_scenario_detail(scenario_id: str):
    sc = get_scenario(scenario_id)
    if not sc:
        raise HTTPException(404, "Scenario not found")
    return sc
