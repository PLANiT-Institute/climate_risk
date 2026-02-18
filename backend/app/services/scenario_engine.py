"""Scenario engine – returns scenario metadata."""

from typing import List

from ..core.config import SCENARIOS


def list_scenarios() -> List[dict]:
    return list(SCENARIOS.values())


def get_scenario(scenario_id: str) -> dict | None:
    return SCENARIOS.get(scenario_id)
