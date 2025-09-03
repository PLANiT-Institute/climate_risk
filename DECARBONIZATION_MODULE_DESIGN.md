# Decarbonization & RE100 Strategy Module - Detailed Design

## 1. MACC (Marginal Abatement Cost Curve) Generator

### Purpose
Create cost-effectiveness ranking of emission reduction projects to identify the "cheapest" path to decarbonization.

### Input Data Structure
```python
# Abatement Projects Catalog
abatement_projects = {
    'project_id': ['SOLAR_001', 'LED_001', 'HVAC_001', 'EV_FLEET_001'],
    'technology': ['Solar PV', 'LED Lighting', 'HVAC Efficiency', 'Electric Vehicles'],
    'sector': ['Energy', 'Buildings', 'Buildings', 'Transport'],
    'capex_per_unit': [2500, 150, 5000, 45000],        # USD per unit
    'opex_delta_annual': [-200, -50, -300, 2000],      # USD per unit per year
    'abatement_per_unit': [15, 2, 8, 12],              # tCO2e per unit per year
    'unit_definition': ['kW', 'fixture', 'system', 'vehicle'],
    'lifetime_years': [25, 10, 15, 8],
    'max_deployment': [1000, 5000, 200, 150],          # max units deployable
    'implementation_time': [2, 0.5, 1, 1],             # years to deploy
    'technology_readiness': [9, 10, 9, 8]              # TRL scale 1-10
}

# Facility-specific deployment potential
deployment_constraints = {
    'facility_id': 'FAC_001',
    'available_roof_area': 10000,        # sqm for solar
    'annual_electricity': 5000,          # MWh
    'fleet_size': 50,                    # vehicles
    'building_sqm': 15000                # building area
}
```

### Core MACC Algorithm
```python
class MACCGenerator:
    def __init__(self, facilities_df, abatement_projects_df, discount_rate=0.06):
        self.facilities = facilities_df
        self.projects = abatement_projects_df  
        self.discount_rate = discount_rate
        
    def calculate_levelized_cost(self, project):
        """Calculate levelized cost of abatement (LCOA) in $/tCO2e"""
        # Present value of total costs
        pv_capex = project.capex_per_unit
        pv_opex = sum(project.opex_delta_annual / (1 + self.discount_rate)**t 
                     for t in range(1, project.lifetime_years + 1))
        total_pv_cost = pv_capex + pv_opex
        
        # Present value of total abatement
        pv_abatement = sum(project.abatement_per_unit / (1 + self.discount_rate)**t 
                          for t in range(1, project.lifetime_years + 1))
        
        # LCOA = Total PV Cost / Total PV Abatement
        lcoa = total_pv_cost / pv_abatement
        
        return lcoa
    
    def calculate_facility_deployment_potential(self, facility, project):
        """Calculate maximum deployment potential for each facility"""
        constraints = {
            'Solar PV': min(facility.roof_area_sqm / 10,     # 10 sqm per kW
                           facility.annual_electricity_mwh * 1000 / project.capacity_factor / 8760),
            'LED Lighting': facility.building_sqm / 20,       # 1 fixture per 20 sqm
            'HVAC Efficiency': max(1, facility.building_sqm / 1000),  # 1 system per 1000 sqm
            'Electric Vehicles': facility.fleet_size
        }
        
        return min(project.max_deployment, 
                  constraints.get(project.technology, project.max_deployment))
    
    def generate_macc_curve(self):
        """Generate complete MACC curve with cumulative abatement potential"""
        macc_data = []
        
        for _, project in self.projects.iterrows():
            lcoa = self.calculate_levelized_cost(project)
            
            # Calculate total deployment potential across all facilities
            total_potential = 0
            total_abatement = 0
            total_capex = 0
            
            for _, facility in self.facilities.iterrows():
                facility_potential = self.calculate_facility_deployment_potential(facility, project)
                facility_abatement = facility_potential * project.abatement_per_unit
                facility_capex = facility_potential * project.capex_per_unit
                
                total_potential += facility_potential
                total_abatement += facility_abatement
                total_capex += facility_capex
            
            macc_data.append({
                'technology': project.technology,
                'lcoa': lcoa,                                    # $/tCO2e
                'annual_abatement_potential': total_abatement,   # tCO2e/year
                'total_capex_required': total_capex,             # USD
                'deployment_units': total_potential,
                'net_negative_cost': lcoa < 0,                   # Boolean
                'implementation_complexity': project.technology_readiness,
                'payback_period': self.calculate_payback(project)
            })
        
        # Sort by LCOA (cost-effectiveness)
        macc_df = pd.DataFrame(macc_data).sort_values('lcoa')
        
        # Calculate cumulative abatement
        macc_df['cumulative_abatement'] = macc_df['annual_abatement_potential'].cumsum()
        
        return macc_df
```

## 2. Net-Zero Pathway Optimizer

### Mathematical Formulation
```
Minimize: Σ(t=2025 to 2050) Σ(i=1 to N) [CAPEX[i] × x[i,t] + OPEX[i] × x[i,t]] / (1+r)^(t-2024)

Subject to:
1. Emission reduction constraint: 
   Σ(i) abatement[i] × x[i,t] ≥ target_reduction[t]
   
2. Annual CAPEX budget constraint:
   Σ(i) CAPEX[i] × x[i,t] ≤ annual_budget[t]
   
3. Technology deployment limits:
   x[i,t] ≤ max_deployment[i]
   
4. Implementation timeline:
   x[i,t] = 0 if t < earliest_deployment[i]
   
5. Net-zero target:
   Σ(t) Σ(i) abatement[i] × x[i,t] ≥ baseline_emissions

Where:
x[i,t] = deployment level of technology i in year t
```

### Implementation
```python
from pulp import *

class NetZeroOptimizer:
    def __init__(self, facilities_df, macc_df, baseline_emissions, target_year=2050):
        self.facilities = facilities_df
        self.macc = macc_df
        self.baseline_emissions = baseline_emissions  # tCO2e
        self.target_year = target_year
        self.start_year = 2025
        self.years = range(self.start_year, self.target_year + 1)
        
    def create_linear_reduction_targets(self):
        """Create linear emission reduction trajectory"""
        total_years = self.target_year - self.start_year
        annual_reduction = self.baseline_emissions / total_years
        
        targets = {}
        for year in self.years:
            years_elapsed = year - self.start_year + 1
            targets[year] = annual_reduction * years_elapsed
            
        return targets
    
    def optimize_deployment_schedule(self, annual_budget_limit=None):
        """Solve optimization problem using linear programming"""
        
        # Decision variables: x[tech, year] = deployment level
        technologies = self.macc['technology'].tolist()
        x = LpVariable.dicts("deployment", 
                           [(tech, year) for tech in technologies for year in self.years],
                           lowBound=0, cat='Continuous')
        
        # Create problem
        prob = LpProblem("NetZero_Pathway", LpMinimize)
        
        # Objective function: minimize total discounted cost
        discount_rate = 0.06
        total_cost = []
        
        for year in self.years:
            year_cost = 0
            discount_factor = 1 / ((1 + discount_rate) ** (year - self.start_year))
            
            for tech in technologies:
                tech_data = self.macc[self.macc['technology'] == tech].iloc[0]
                capex = tech_data['total_capex_required'] / tech_data['deployment_units']  # per unit
                annual_opex = capex * 0.02  # Assume 2% of CAPEX annually
                
                year_cost += (capex + annual_opex) * x[(tech, year)] * discount_factor
                
            total_cost.append(year_cost)
        
        prob += lpSum(total_cost)
        
        # Constraints
        reduction_targets = self.create_linear_reduction_targets()
        
        # 1. Emission reduction constraint for each year
        for year in self.years:
            year_abatement = 0
            for tech in technologies:
                tech_data = self.macc[self.macc['technology'] == tech].iloc[0]
                abatement_per_unit = (tech_data['annual_abatement_potential'] / 
                                    tech_data['deployment_units'])
                
                # Cumulative deployment up to this year
                cumulative_deployment = lpSum([x[(tech, y)] for y in range(self.start_year, year + 1)])
                year_abatement += abatement_per_unit * cumulative_deployment
            
            prob += year_abatement >= reduction_targets[year]
        
        # 2. Annual budget constraint (if specified)
        if annual_budget_limit:
            for year in self.years:
                year_capex = 0
                for tech in technologies:
                    tech_data = self.macc[self.macc['technology'] == tech].iloc[0]
                    capex_per_unit = (tech_data['total_capex_required'] / 
                                    tech_data['deployment_units'])
                    year_capex += capex_per_unit * x[(tech, year)]
                
                prob += year_capex <= annual_budget_limit
        
        # 3. Maximum deployment constraints
        for tech in technologies:
            tech_data = self.macc[self.macc['technology'] == tech].iloc[0]
            max_units = tech_data['deployment_units']
            
            total_deployment = lpSum([x[(tech, year)] for year in self.years])
            prob += total_deployment <= max_units
        
        # Solve
        prob.solve(PULP_CBC_CMD(msg=0))
        
        # Extract results
        results = self.extract_solution(x, technologies)
        return results
    
    def extract_solution(self, x, technologies):
        """Extract optimization results into structured format"""
        deployment_schedule = []
        
        for year in self.years:
            for tech in technologies:
                deployment = x[(tech, year)].varValue or 0
                if deployment > 0:
                    tech_data = self.macc[self.macc['technology'] == tech].iloc[0]
                    
                    deployment_schedule.append({
                        'year': year,
                        'technology': tech,
                        'deployment_units': deployment,
                        'capex': deployment * (tech_data['total_capex_required'] / tech_data['deployment_units']),
                        'annual_abatement': deployment * (tech_data['annual_abatement_potential'] / tech_data['deployment_units']),
                        'lcoa': tech_data['lcoa']
                    })
        
        return pd.DataFrame(deployment_schedule)
```

## 3. RE100 Strategy Optimizer

### Multi-criteria Decision Framework
```python
class RE100StrategyOptimizer:
    def __init__(self, facilities_df, renewable_options_df):
        self.facilities = facilities_df
        self.renewable_options = renewable_options_df
        
    def calculate_procurement_mix(self, target_renewable_pct=100, target_year=2030):
        """
        Optimize renewable energy procurement mix across:
        - On-site generation (solar, wind)
        - Power Purchase Agreements (PPAs) 
        - Renewable Energy Certificates (RECs)
        """
        
        strategies = {
            'onsite_solar': self.optimize_onsite_solar(),
            'ppa_contracts': self.optimize_ppa_portfolio(),
            'rec_purchases': self.optimize_rec_strategy(),
            'energy_storage': self.optimize_storage_systems()
        }
        
        # Multi-criteria optimization considering:
        # 1. Cost (LCOE)
        # 2. Risk (price volatility, contract terms)
        # 3. Sustainability (additionality, local impact)
        # 4. Operational complexity
        
        optimal_mix = self.solve_multicriteria_optimization(strategies)
        return optimal_mix
    
    def optimize_onsite_solar(self):
        """Calculate optimal on-site solar deployment"""
        solar_results = []
        
        for _, facility in self.facilities.iterrows():
            # Available roof area constraint
            max_capacity_kw = facility.roof_area_sqm / 8  # 8 sqm per kW
            
            # Economic analysis
            capex_per_kw = 1500  # USD/kW installed
            annual_generation = max_capacity_kw * facility.solar_irradiance * 365 * 24 * 0.2  # kWh
            
            # Financial metrics
            lcoe = self.calculate_solar_lcoe(capex_per_kw, annual_generation, 25)  # 25-year lifetime
            npv = self.calculate_solar_npv(max_capacity_kw, annual_generation, facility.electricity_rate)
            
            solar_results.append({
                'facility_id': facility.facility_id,
                'max_solar_capacity_kw': max_capacity_kw,
                'annual_generation_kwh': annual_generation,
                'capex_required': max_capacity_kw * capex_per_kw,
                'lcoe': lcoe,
                'npv_25_years': npv,
                'co2_avoided_annually': annual_generation * facility.grid_emission_factor / 1000  # tCO2
            })
            
        return pd.DataFrame(solar_results)
    
    def calculate_solar_lcoe(self, capex_per_kw, annual_generation_kwh, lifetime_years):
        """Calculate Levelized Cost of Energy for solar"""
        discount_rate = 0.06
        annual_opex = capex_per_kw * 0.015  # 1.5% of CAPEX annually
        
        # Present value of costs
        pv_costs = capex_per_kw + sum(annual_opex / (1 + discount_rate)**t 
                                     for t in range(1, lifetime_years + 1))
        
        # Present value of energy generation  
        pv_generation = sum(annual_generation_kwh / (1 + discount_rate)**t 
                           for t in range(1, lifetime_years + 1))
        
        lcoe = pv_costs / pv_generation  # $/kWh
        return lcoe
```

## 4. Investment Timeline & Financial Optimization

### CAPEX Scheduling Algorithm
```python
class CapexScheduler:
    def __init__(self, projects_df, financial_constraints):
        self.projects = projects_df
        self.constraints = financial_constraints
        
    def optimize_investment_timeline(self):
        """
        Optimize timing of investments considering:
        - Cash flow smoothing
        - Technology learning curves (cost reductions over time)
        - Urgency of emission reductions
        - Implementation capacity constraints
        """
        
        # Dynamic programming approach
        years = range(2025, 2051)
        optimal_schedule = {}
        
        for year in years:
            year_projects = self.select_year_projects(year)
            optimal_schedule[year] = {
                'total_capex': sum(p.capex for p in year_projects),
                'projects': year_projects,
                'cumulative_abatement': self.calculate_cumulative_abatement(year),
                'cash_flow_impact': self.calculate_cash_flow_impact(year_projects)
            }
            
        return optimal_schedule
    
    def calculate_technology_learning_curves(self):
        """Model technology cost reductions over time"""
        learning_rates = {
            'Solar PV': 0.20,        # 20% cost reduction per doubling of deployment
            'Battery Storage': 0.18,  # 18% learning rate
            'Wind': 0.12,            # 12% learning rate
            'Heat Pumps': 0.15       # 15% learning rate
        }
        
        # Apply Wright's Law: Cost = Initial_Cost × (Cumulative_Production)^(-learning_rate)
        projected_costs = {}
        
        for tech, learning_rate in learning_rates.items():
            costs_over_time = []
            for year in range(2025, 2051):
                # Estimate global cumulative deployment
                years_elapsed = year - 2025
                deployment_growth = 1.15 ** years_elapsed  # 15% annual growth
                cost_reduction = deployment_growth ** (-learning_rate)
                costs_over_time.append(cost_reduction)
            
            projected_costs[tech] = costs_over_time
            
        return projected_costs
```

This comprehensive design provides the foundation for implementing sophisticated decarbonization and RE100 strategies with financial optimization, making your tool industry-leading in its analytical capabilities.