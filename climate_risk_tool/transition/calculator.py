"""Core calculator for transition risk metrics."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from ..config import CONFIG
from .cost_curves import CarbonPricingModel


class TransitionRiskCalculator:
    """Main calculator for climate transition risk metrics."""
    
    def __init__(self):
        self.config = CONFIG
        self.carbon_model = CarbonPricingModel()
        
    def calculate_emissions_pathways(self, 
                                   facilities_df: pd.DataFrame,
                                   scenario_name: str) -> pd.DataFrame:
        """
        Calculate emissions pathways for each facility under a given scenario.
        
        Returns DataFrame with emissions projections for each year.
        """
        scenario = self.config.scenarios[scenario_name] 
        years = self.config.projection_years
        
        results = []
        
        for _, facility in facilities_df.iterrows():
            facility_id = facility['facility_id']
            sector = facility['sector']
            baseline_scope1 = facility['current_emissions_scope1']
            baseline_scope2 = facility['current_emissions_scope2']
            
            # Calculate reduction pathway based on scenario
            for year in years:
                years_from_base = year - self.config.base_year
                reduction_factor = self._calculate_reduction_factor(
                    scenario, sector, years_from_base
                )
                
                projected_scope1 = baseline_scope1 * (1 - reduction_factor)
                projected_scope2 = baseline_scope2 * (1 - reduction_factor)
                total_emissions = projected_scope1 + projected_scope2
                
                results.append({
                    'facility_id': facility_id,
                    'scenario': scenario_name,
                    'year': year,
                    'scope1_emissions': projected_scope1,
                    'scope2_emissions': projected_scope2,
                    'total_emissions': total_emissions,
                    'reduction_factor': reduction_factor
                })
        
        return pd.DataFrame(results)
    
    def calculate_financial_impacts(self,
                                  facilities_df: pd.DataFrame,
                                  emissions_df: pd.DataFrame,
                                  scenario_name: str) -> pd.DataFrame:
        """
        Calculate financial impacts (ΔEBITDA, ΔNPV) for each facility.
        """
        carbon_prices = self.carbon_model.get_carbon_price_trajectory(
            scenario_name, self.config.projection_years
        )
        
        results = []
        
        for _, facility in facilities_df.iterrows():
            facility_id = facility['facility_id']
            sector = facility['sector']
            baseline_ebitda = facility['ebitda']
            baseline_revenue = facility['annual_revenue']
            
            # Get emissions pathway for this facility
            facility_emissions = emissions_df[
                (emissions_df['facility_id'] == facility_id) & 
                (emissions_df['scenario'] == scenario_name)
            ]
            
            annual_impacts = []
            
            for _, emission_row in facility_emissions.iterrows():
                year = emission_row['year']
                total_emissions = emission_row['total_emissions']
                carbon_price = carbon_prices[year]
                
                # Calculate direct carbon costs
                annual_carbon_cost = total_emissions * carbon_price
                
                # Calculate transition costs
                baseline_emissions = facility['current_emissions_scope1'] + facility['current_emissions_scope2']
                transition_costs = self.carbon_model.calculate_transition_costs(
                    baseline_emissions,
                    total_emissions,
                    sector,
                    timeframe_years=5
                )
                
                # Calculate revenue impact (demand destruction from higher costs)
                revenue_impact = self._calculate_revenue_impact(
                    baseline_revenue, annual_carbon_cost, sector
                )
                
                # Calculate EBITDA impact
                ebitda_impact = -(annual_carbon_cost + transition_costs['opex'] + revenue_impact)
                delta_ebitda = ebitda_impact
                
                annual_impacts.append({
                    'year': year,
                    'carbon_cost': annual_carbon_cost,
                    'transition_capex': transition_costs['capex'] / 5,  # Amortized
                    'transition_opex': transition_costs['opex'],
                    'revenue_impact': revenue_impact,
                    'delta_ebitda': delta_ebitda,
                    'total_emissions': total_emissions
                })
            
            # Calculate NPV
            cash_flows = [impact['delta_ebitda'] for impact in annual_impacts]
            npv = self._calculate_npv(cash_flows, self.config.discount_rate)
            
            results.append({
                'facility_id': facility_id,
                'scenario': scenario_name,
                'delta_npv': npv,
                'annual_impacts': annual_impacts
            })
        
        return pd.DataFrame(results)
    
    def calculate_carbon_var(self,
                           facilities_df: pd.DataFrame,
                           financial_impacts: Dict[str, pd.DataFrame],
                           confidence_level: float = 0.95) -> pd.DataFrame:
        """
        Calculate Carbon Value at Risk (VaR) across scenarios.
        """
        results = []
        
        for _, facility in facilities_df.iterrows():
            facility_id = facility['facility_id']
            assets_value = facility['assets_value']
            
            # Collect NPV impacts across all scenarios
            scenario_impacts = []
            for scenario_name, impacts_df in financial_impacts.items():
                facility_impact = impacts_df[impacts_df['facility_id'] == facility_id]
                if not facility_impact.empty:
                    delta_npv = facility_impact.iloc[0]['delta_npv']
                    scenario_impacts.append(delta_npv)
            
            if scenario_impacts:
                # Calculate VaR (worst-case loss at confidence level)
                scenario_impacts = np.array(scenario_impacts)
                var_absolute = np.percentile(scenario_impacts, (1 - confidence_level) * 100)
                var_percentage = (var_absolute / assets_value) * 100 if assets_value > 0 else 0
                
                # Expected loss (mean of negative scenarios)
                negative_impacts = scenario_impacts[scenario_impacts < 0]
                expected_loss = np.mean(negative_impacts) if len(negative_impacts) > 0 else 0
                
                results.append({
                    'facility_id': facility_id,
                    'carbon_var_absolute': abs(var_absolute),
                    'carbon_var_percentage': abs(var_percentage),
                    'expected_loss': abs(expected_loss),
                    'worst_case_scenario': np.min(scenario_impacts),
                    'best_case_scenario': np.max(scenario_impacts),
                    'scenarios_count': len(scenario_impacts)
                })
        
        return pd.DataFrame(results)
    
    def _calculate_reduction_factor(self, scenario, sector: str, years_from_base: int) -> float:
        """Calculate emissions reduction factor based on scenario and time."""
        # Linear reduction pathway to meet scenario target by 2030
        target_year = 2030
        years_to_target = target_year - self.config.base_year
        
        if years_from_base <= 0:
            return 0.0
        
        if years_from_base >= years_to_target:
            # Full target reduction achieved
            base_reduction = scenario.emissions_reduction_target
        else:
            # Linear interpolation
            base_reduction = scenario.emissions_reduction_target * (years_from_base / years_to_target)
        
        # Sector-specific adjustment
        sector_multipliers = {
            'oil_gas': 1.2,  # Higher reduction pressure
            'utilities': 1.1,
            'steel': 0.9,    # Harder to abate
            'cement': 0.8,   # Very hard to abate
            'chemicals': 0.9,
            'aviation': 0.7,  # Limited alternatives
            'shipping': 0.8,
            'automotive': 1.3,  # Electrification opportunity
            'real_estate': 1.1,
            'financial': 1.0
        }
        
        multiplier = sector_multipliers.get(sector, 1.0)
        return min(0.95, base_reduction * multiplier)  # Cap at 95% reduction
    
    def _calculate_revenue_impact(self, baseline_revenue: float, carbon_cost: float, sector: str) -> float:
        """Calculate revenue impact from carbon costs (demand destruction)."""
        # Sector-specific demand elasticity to carbon cost pass-through
        elasticities = {
            'oil_gas': 0.15,     # Can pass through most costs
            'utilities': 0.20,   # Regulated, limited pass-through
            'steel': 0.10,       # Commodity, price-sensitive
            'cement': 0.12,
            'chemicals': 0.08,
            'aviation': 0.25,    # Demand sensitive to price
            'shipping': 0.15,
            'automotive': 0.30,  # Consumer discretionary
            'real_estate': 0.05, # Less sensitive
            'financial': 0.02
        }
        
        elasticity = elasticities.get(sector, 0.15)
        
        # Revenue loss = carbon_cost * elasticity * revenue_sensitivity
        cost_ratio = carbon_cost / baseline_revenue if baseline_revenue > 0 else 0
        revenue_loss = baseline_revenue * cost_ratio * elasticity
        
        return min(revenue_loss, baseline_revenue * 0.3)  # Cap at 30% revenue loss
    
    def _calculate_npv(self, cash_flows: List[float], discount_rate: float) -> float:
        """Calculate Net Present Value of cash flows."""
        npv = 0.0
        for i, cf in enumerate(cash_flows):
            npv += cf / ((1 + discount_rate) ** (i + 1))
        return npv