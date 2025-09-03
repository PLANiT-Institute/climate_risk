"""
Marginal Abatement Cost Curve (MACC) Generator

Creates cost-effectiveness ranking of emission reduction projects to identify
the optimal decarbonization pathway based on economic criteria.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class AbatementProject:
    """Data structure for individual abatement projects"""
    project_id: str
    technology: str
    sector: str                      # Energy, Buildings, Transport, Industry
    capex_per_unit: float           # USD per deployment unit
    opex_delta_annual: float        # Annual OPEX change per unit (negative = savings)
    abatement_per_unit: float       # tCO2e abated per unit per year
    unit_definition: str            # kW, fixture, system, vehicle, etc.
    lifetime_years: int
    max_deployment: float           # Maximum deployable units
    implementation_time: float      # Years required for full deployment
    technology_readiness: int       # TRL scale 1-10
    complexity_score: float         # Implementation complexity (1-10)
    
    # Optional facility-specific constraints
    facility_constraints: Optional[Dict] = None


class MACCGenerator:
    """
    Marginal Abatement Cost Curve Generator
    
    Creates cost-effectiveness ranking and deployment optimization for
    emission reduction projects across corporate portfolio.
    """
    
    def __init__(self, facilities_df: pd.DataFrame, discount_rate: float = 0.06):
        """
        Initialize MACC Generator
        
        Args:
            facilities_df: DataFrame with facility data including coordinates,
                          emissions, energy consumption, asset details
            discount_rate: Discount rate for NPV calculations
        """
        self.facilities = facilities_df
        self.discount_rate = discount_rate
        self.projects = []
        
    def add_project(self, project: AbatementProject):
        """Add abatement project to analysis"""
        self.projects.append(project)
        
    def add_projects_from_catalog(self, projects_df: pd.DataFrame):
        """Load projects from standardized catalog DataFrame"""
        for _, row in projects_df.iterrows():
            project = AbatementProject(
                project_id=row['project_id'],
                technology=row['technology'],
                sector=row['sector'],
                capex_per_unit=row['capex_per_unit'],
                opex_delta_annual=row['opex_delta_annual'],
                abatement_per_unit=row['abatement_per_unit'],
                unit_definition=row['unit_definition'],
                lifetime_years=row['lifetime_years'],
                max_deployment=row['max_deployment'],
                implementation_time=row['implementation_time'],
                technology_readiness=row['technology_readiness'],
                complexity_score=row.get('complexity_score', 5)
            )
            self.add_project(project)
    
    def calculate_levelized_cost_of_abatement(self, project: AbatementProject) -> float:
        """
        Calculate Levelized Cost of Abatement (LCOA) in $/tCO2e
        
        LCOA = (CAPEX + NPV of OPEX changes) / (NPV of lifetime abatement)
        """
        # Present value of OPEX changes over project lifetime
        pv_opex = sum(project.opex_delta_annual / (1 + self.discount_rate)**t 
                     for t in range(1, project.lifetime_years + 1))
        
        # Total present value of costs (negative OPEX = savings)
        total_pv_cost = project.capex_per_unit + pv_opex
        
        # Present value of total CO2 abatement over lifetime
        pv_abatement = sum(project.abatement_per_unit / (1 + self.discount_rate)**t 
                          for t in range(1, project.lifetime_years + 1))
        
        # LCOA (can be negative for net-profitable projects)
        lcoa = total_pv_cost / pv_abatement if pv_abatement > 0 else float('inf')
        
        return lcoa
    
    def calculate_facility_deployment_potential(self, facility: pd.Series, 
                                               project: AbatementProject) -> float:
        """
        Calculate maximum deployment potential for project at specific facility
        
        Uses facility characteristics to determine realistic deployment limits
        based on physical, operational, and economic constraints.
        """
        
        # Technology-specific deployment constraints
        constraints = {
            'Solar PV': self._solar_deployment_limit(facility, project),
            'Wind': self._wind_deployment_limit(facility, project),
            'LED Lighting': self._led_deployment_limit(facility, project),
            'HVAC Efficiency': self._hvac_deployment_limit(facility, project),
            'Electric Vehicles': self._ev_deployment_limit(facility, project),
            'Heat Pumps': self._heat_pump_deployment_limit(facility, project),
            'Battery Storage': self._battery_deployment_limit(facility, project),
            'Process Efficiency': self._process_efficiency_limit(facility, project),
            'Building Insulation': self._insulation_deployment_limit(facility, project)
        }
        
        # Get technology-specific constraint, default to project max if not defined
        tech_limit = constraints.get(project.technology, project.max_deployment)
        
        # Return minimum of technology limit and project maximum
        return min(tech_limit, project.max_deployment)
    
    def _solar_deployment_limit(self, facility: pd.Series, project: AbatementProject) -> float:
        """Calculate solar PV deployment limit based on roof area and energy demand"""
        # Typical solar installation: 10 sqm per kW, 0.2 capacity factor
        roof_area = facility.get('roof_area_sqm', facility.get('floor_area_sqm', 0) * 0.3)
        max_by_area = roof_area / 10  # kW
        
        # Limit by energy consumption (don't exceed 120% of annual consumption)
        annual_electricity_kwh = facility.get('annual_electricity_kwh', 
                                            facility.get('annual_emissions_scope2', 0) / 0.5 * 1000)
        max_by_consumption = annual_electricity_kwh / (8760 * 0.2) * 1.2  # kW
        
        return min(max_by_area, max_by_consumption)
    
    def _led_deployment_limit(self, facility: pd.Series, project: AbatementProject) -> float:
        """Calculate LED lighting retrofit potential"""
        floor_area = facility.get('floor_area_sqm', 1000)
        # Assume 1 fixture per 20 sqm
        return floor_area / 20
    
    def _hvac_deployment_limit(self, facility: pd.Series, project: AbatementProject) -> float:
        """Calculate HVAC efficiency upgrade potential"""
        floor_area = facility.get('floor_area_sqm', 1000)
        # 1 HVAC system per 1000 sqm
        return max(1, floor_area / 1000)
    
    def _ev_deployment_limit(self, facility: pd.Series, project: AbatementProject) -> float:
        """Calculate electric vehicle fleet potential"""
        return facility.get('fleet_size', facility.get('employees', 100) * 0.1)
    
    def _wind_deployment_limit(self, facility: pd.Series, project: AbatementProject) -> float:
        """Calculate wind deployment potential (often site-specific)"""
        # Simplified: based on land area and wind resources
        land_area = facility.get('land_area_hectares', 1)
        return land_area * 0.5  # MW, conservative estimate
    
    def _heat_pump_deployment_limit(self, facility: pd.Series, project: AbatementProject) -> float:
        """Calculate heat pump deployment potential"""
        # Based on heating demand proxy
        floor_area = facility.get('floor_area_sqm', 1000)
        return max(1, floor_area / 500)  # 1 heat pump per 500 sqm
    
    def _battery_deployment_limit(self, facility: pd.Series, project: AbatementProject) -> float:
        """Calculate battery storage deployment potential"""
        # Typically sized relative to renewable generation or peak demand
        peak_demand_kw = facility.get('peak_electricity_demand_kw', 
                                    facility.get('annual_electricity_kwh', 1000000) / 2000)
        return peak_demand_kw * 0.5  # kWh storage capacity
    
    def _process_efficiency_limit(self, facility: pd.Series, project: AbatementProject) -> float:
        """Calculate process efficiency improvement potential"""
        # Based on production volume or energy intensity
        production_units = facility.get('annual_production_units', 1)
        return production_units
    
    def _insulation_deployment_limit(self, facility: pd.Series, project: AbatementProject) -> float:
        """Calculate building insulation upgrade potential"""
        # Based on building age and current efficiency
        floor_area = facility.get('floor_area_sqm', 1000)
        building_age = facility.get('building_age_years', 20)
        
        # Older buildings have more potential
        age_multiplier = min(2.0, building_age / 15)
        return floor_area * age_multiplier
    
    def generate_macc_curve(self) -> pd.DataFrame:
        """
        Generate complete MACC curve with deployment potential and costs
        
        Returns:
            DataFrame with projects ranked by cost-effectiveness
        """
        
        macc_data = []
        
        for project in self.projects:
            # Calculate levelized cost of abatement
            lcoa = self.calculate_levelized_cost_of_abatement(project)
            
            # Calculate total deployment potential across all facilities
            total_deployment = 0
            total_abatement = 0
            total_capex = 0
            facility_breakdown = []
            
            for _, facility in self.facilities.iterrows():
                facility_potential = self.calculate_facility_deployment_potential(facility, project)
                facility_abatement = facility_potential * project.abatement_per_unit
                facility_capex = facility_potential * project.capex_per_unit
                
                if facility_potential > 0:
                    facility_breakdown.append({
                        'facility_id': facility.get('facility_id', facility.name),
                        'deployment_potential': facility_potential,
                        'abatement_potential': facility_abatement,
                        'capex_required': facility_capex
                    })
                
                total_deployment += facility_potential
                total_abatement += facility_abatement
                total_capex += facility_capex
            
            # Calculate additional metrics
            payback_period = self._calculate_payback_period(project)
            roi = self._calculate_roi(project)
            
            macc_data.append({
                'project_id': project.project_id,
                'technology': project.technology,
                'sector': project.sector,
                'lcoa_usd_per_tco2': lcoa,
                'annual_abatement_potential': total_abatement,
                'lifetime_abatement_potential': total_abatement * project.lifetime_years,
                'total_capex_required': total_capex,
                'deployment_units': total_deployment,
                'unit_definition': project.unit_definition,
                'net_negative_cost': lcoa < 0,
                'payback_period_years': payback_period,
                'roi_percent': roi * 100,
                'implementation_complexity': project.complexity_score,
                'technology_readiness': project.technology_readiness,
                'facility_breakdown': facility_breakdown
            })
        
        # Create DataFrame and sort by cost-effectiveness
        macc_df = pd.DataFrame(macc_data)
        macc_df = macc_df.sort_values('lcoa_usd_per_tco2')
        
        # Calculate cumulative abatement potential
        macc_df['cumulative_abatement'] = macc_df['annual_abatement_potential'].cumsum()
        
        # Add rank based on cost-effectiveness
        macc_df['rank'] = range(1, len(macc_df) + 1)
        
        return macc_df
    
    def _calculate_payback_period(self, project: AbatementProject) -> float:
        """Calculate simple payback period in years"""
        if project.opex_delta_annual >= 0:  # No savings, no payback
            return float('inf')
        
        annual_savings = -project.opex_delta_annual  # Convert to positive
        return project.capex_per_unit / annual_savings
    
    def _calculate_roi(self, project: AbatementProject) -> float:
        """Calculate return on investment over project lifetime"""
        total_savings = -project.opex_delta_annual * project.lifetime_years
        if project.capex_per_unit <= 0:
            return float('inf')
        
        return (total_savings - project.capex_per_unit) / project.capex_per_unit
    
    def visualize_macc_curve(self, macc_df: pd.DataFrame, save_path: Optional[str] = None):
        """
        Create visualization of MACC curve
        
        Args:
            macc_df: DataFrame from generate_macc_curve()
            save_path: Optional path to save the plot
        """
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Upper plot: MACC curve
        x_data = macc_df['cumulative_abatement'] / 1000  # Convert to ktCO2e
        y_data = macc_df['lcoa_usd_per_tco2']
        
        # Color-code by net cost vs net savings
        colors = ['green' if cost < 0 else 'red' for cost in y_data]
        
        ax1.bar(x_data, y_data, width=np.diff(np.append(0, x_data)), 
               color=colors, alpha=0.7, edgecolor='black')
        
        ax1.set_xlabel('Cumulative Abatement Potential (ktCO2e/year)')
        ax1.set_ylabel('Levelized Cost of Abatement ($/tCO2e)')
        ax1.set_title('Marginal Abatement Cost Curve (MACC)')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=1)
        
        # Add legend
        ax1.plot([], [], color='green', alpha=0.7, linewidth=10, label='Net Cost Savings')
        ax1.plot([], [], color='red', alpha=0.7, linewidth=10, label='Net Cost')
        ax1.legend()
        
        # Lower plot: CAPEX requirements
        ax2.bar(range(len(macc_df)), macc_df['total_capex_required'] / 1e6,  # Convert to millions
               color='blue', alpha=0.7)
        ax2.set_xlabel('Project Rank (by cost-effectiveness)')
        ax2.set_ylabel('Total CAPEX Required (Million USD)')
        ax2.set_title('CAPEX Requirements by Project')
        ax2.grid(True, alpha=0.3)
        
        # Add project labels
        for i, (_, row) in enumerate(macc_df.head(10).iterrows()):  # Label top 10 projects
            ax2.text(i, row['total_capex_required'] / 1e6 + max(macc_df['total_capex_required']) / 1e6 * 0.02,
                    row['technology'][:8], rotation=45, ha='left', fontsize=8)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def get_investment_priorities(self, macc_df: pd.DataFrame, 
                                budget_limit: Optional[float] = None) -> pd.DataFrame:
        """
        Get prioritized investment recommendations
        
        Args:
            macc_df: DataFrame from generate_macc_curve()
            budget_limit: Optional CAPEX budget constraint (USD)
            
        Returns:
            DataFrame with prioritized projects within budget
        """
        
        # Start with cost-effective projects (sorted by LCOA)
        prioritized = macc_df.copy()
        
        # Apply budget constraint if specified
        if budget_limit:
            cumulative_capex = prioritized['total_capex_required'].cumsum()
            within_budget = cumulative_capex <= budget_limit
            prioritized = prioritized[within_budget]
        
        # Add priority scoring based on multiple factors
        prioritized['priority_score'] = self._calculate_priority_score(prioritized)
        prioritized = prioritized.sort_values('priority_score', ascending=False)
        
        return prioritized[['project_id', 'technology', 'lcoa_usd_per_tco2', 
                          'annual_abatement_potential', 'total_capex_required',
                          'roi_percent', 'priority_score', 'implementation_complexity']]
    
    def _calculate_priority_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate multi-criteria priority score"""
        
        # Normalize metrics to 0-1 scale
        roi_norm = (df['roi_percent'] - df['roi_percent'].min()) / (df['roi_percent'].max() - df['roi_percent'].min())
        abatement_norm = df['annual_abatement_potential'] / df['annual_abatement_potential'].max()
        complexity_norm = 1 - (df['implementation_complexity'] - 1) / 9  # Lower complexity = higher score
        trl_norm = (df['technology_readiness'] - 1) / 9  # Higher TRL = higher score
        
        # Weighted priority score
        priority_score = (
            0.3 * roi_norm +                    # 30% weight on ROI
            0.3 * abatement_norm +              # 30% weight on abatement potential
            0.2 * complexity_norm +             # 20% weight on implementation ease
            0.2 * trl_norm                      # 20% weight on technology readiness
        )
        
        return priority_score