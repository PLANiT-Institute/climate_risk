"""Configuration settings for the climate risk tool."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ScenarioConfig:
    """Configuration for climate scenarios."""
    name: str
    carbon_price_2025: float  # $/tCO2
    carbon_price_2030: float  # $/tCO2
    carbon_price_2050: float  # $/tCO2
    emissions_reduction_target: float  # % reduction by 2030


@dataclass
class ToolConfig:
    """Main configuration for the climate risk tool."""
    
    # Default scenarios aligned with NGFS/IEA pathways
    scenarios: Dict[str, ScenarioConfig] = None
    
    # Financial parameters
    discount_rate: float = 0.08  # 8% WACC
    base_year: int = 2024
    projection_years: List[int] = None
    
    # Default carbon intensity factors by sector (tCO2/revenue)
    sector_intensities: Dict[str, float] = None
    
    def __post_init__(self):
        if self.scenarios is None:
            self.scenarios = {
                "net_zero": ScenarioConfig(
                    name="Net Zero 2050",
                    carbon_price_2025=75.0,
                    carbon_price_2030=130.0,
                    carbon_price_2050=250.0,
                    emissions_reduction_target=0.50
                ),
                "delayed_transition": ScenarioConfig(
                    name="Delayed Transition",
                    carbon_price_2025=50.0,
                    carbon_price_2030=90.0,
                    carbon_price_2050=180.0,
                    emissions_reduction_target=0.30
                ),
                "current_policies": ScenarioConfig(
                    name="Current Policies",
                    carbon_price_2025=25.0,
                    carbon_price_2030=40.0,
                    carbon_price_2050=80.0,
                    emissions_reduction_target=0.15
                )
            }
        
        if self.projection_years is None:
            self.projection_years = [2025, 2030, 2035, 2040, 2045, 2050]
        
        if self.sector_intensities is None:
            self.sector_intensities = {
                "oil_gas": 0.45,
                "utilities": 0.52,
                "steel": 2.1,
                "cement": 0.87,
                "chemicals": 1.3,
                "aviation": 0.63,
                "shipping": 0.41,
                "automotive": 0.18,
                "real_estate": 0.05,
                "financial": 0.001
            }


# Global configuration instance
CONFIG = ToolConfig()