"""Carbon pricing models and cost curves for transition risk assessment."""

import numpy as np
from typing import Dict, List, Tuple
from ..config import CONFIG, ScenarioConfig


class CarbonPricingModel:
    """Models carbon pricing evolution under different scenarios."""
    
    def __init__(self):
        self.base_year = CONFIG.base_year
        self.scenarios = CONFIG.scenarios
    
    def get_carbon_price_trajectory(self, scenario_name: str, years: List[int]) -> Dict[int, float]:
        """Get carbon price trajectory for a given scenario."""
        if scenario_name not in self.scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.scenarios[scenario_name]
        prices = {}
        
        for year in years:
            if year <= 2025:
                price = self._interpolate_price(
                    self.base_year, 2025,
                    0, scenario.carbon_price_2025,
                    year
                )
            elif year <= 2030:
                price = self._interpolate_price(
                    2025, 2030,
                    scenario.carbon_price_2025, scenario.carbon_price_2030,
                    year
                )
            else:  # year > 2030
                price = self._interpolate_price(
                    2030, 2050,
                    scenario.carbon_price_2030, scenario.carbon_price_2050,
                    year
                )
            
            prices[year] = max(0, price)  # Ensure non-negative prices
        
        return prices
    
    def _interpolate_price(self, year1: int, year2: int, price1: float, price2: float, target_year: int) -> float:
        """Linear interpolation between two price points."""
        if year1 == year2:
            return price1
        
        # Linear interpolation
        slope = (price2 - price1) / (year2 - year1)
        return price1 + slope * (target_year - year1)
    
    def get_marginal_abatement_cost(self, sector: str, reduction_percentage: float) -> float:
        """
        Estimate marginal abatement cost for a given sector and reduction level.
        Returns cost in $/tCO2e.
        """
        # Simplified sector-specific marginal abatement cost curves
        # Based on McKinsey Global GHG Abatement Cost Curve
        base_costs = {
            'oil_gas': 45.0,
            'utilities': 35.0,
            'steel': 80.0,
            'cement': 65.0,
            'chemicals': 55.0,
            'aviation': 120.0,
            'shipping': 90.0,
            'automotive': 40.0,
            'real_estate': 25.0,
            'financial': 10.0
        }
        
        base_cost = base_costs.get(sector, 50.0)  # Default cost
        
        # Cost increases exponentially with reduction percentage
        # Easy reductions first, then more expensive
        if reduction_percentage <= 0.2:  # 0-20% reduction
            multiplier = 1.0
        elif reduction_percentage <= 0.5:  # 20-50% reduction
            multiplier = 1.5
        elif reduction_percentage <= 0.8:  # 50-80% reduction
            multiplier = 2.5
        else:  # 80%+ reduction
            multiplier = 4.0
        
        return base_cost * multiplier
    
    def calculate_transition_costs(self, 
                                 current_emissions: float,
                                 target_emissions: float,
                                 sector: str,
                                 timeframe_years: int = 5) -> Dict[str, float]:
        """
        Calculate transition costs for moving from current to target emissions.
        
        Returns:
            Dict with 'capex', 'opex', and 'total' costs in USD
        """
        emissions_reduction = current_emissions - target_emissions
        if emissions_reduction <= 0:
            return {'capex': 0.0, 'opex': 0.0, 'total': 0.0}
        
        reduction_percentage = emissions_reduction / current_emissions
        
        # Get marginal abatement cost
        mac = self.get_marginal_abatement_cost(sector, reduction_percentage)
        
        # Estimate capex and opex split (sector-dependent)
        capex_ratio = self._get_capex_ratio(sector)
        
        total_cost = emissions_reduction * mac
        capex = total_cost * capex_ratio
        opex = total_cost * (1 - capex_ratio) / timeframe_years  # Annual opex
        
        return {
            'capex': capex,
            'opex': opex,
            'total': total_cost
        }
    
    def _get_capex_ratio(self, sector: str) -> float:
        """Get the typical ratio of capex to total transition costs by sector."""
        ratios = {
            'oil_gas': 0.7,
            'utilities': 0.8,
            'steel': 0.75,
            'cement': 0.7,
            'chemicals': 0.65,
            'aviation': 0.6,
            'shipping': 0.65,
            'automotive': 0.6,
            'real_estate': 0.8,
            'financial': 0.9
        }
        return ratios.get(sector, 0.7)  # Default 70% capex