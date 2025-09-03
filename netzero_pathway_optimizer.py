"""
Net-Zero Pathway Optimizer

Creates optimal decarbonization roadmaps using linear programming optimization
to minimize total cost while achieving emission reduction targets.

Uses MACC (Marginal Abatement Cost Curve) results as input to determine
the most cost-effective deployment schedule for abatement technologies.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pulp import *
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


@dataclass
class PathwayScenario:
    """Configuration for different net-zero pathway scenarios"""
    name: str
    target_year: int
    reduction_curve: str          # 'linear', 'exponential', 'delayed_action'
    annual_budget_limit: Optional[float] = None    # USD, None = no limit
    technology_constraints: Optional[Dict] = None   # Technology-specific limits
    discount_rate: float = 0.06
    interim_targets: Optional[Dict] = None          # {year: reduction_percentage}


class NetZeroPathwayOptimizer:
    """
    Optimizes decarbonization pathways using linear programming
    
    Takes MACC results and creates optimal deployment schedules to achieve
    net-zero emissions at minimum cost while respecting budget and technology constraints.
    """
    
    def __init__(self, macc_df: pd.DataFrame, baseline_emissions: float):
        """
        Initialize optimizer with MACC results
        
        Args:
            macc_df: DataFrame from MACC generator with abatement projects
            baseline_emissions: Current annual emissions in tCO2e
        """
        self.macc_df = macc_df.copy()
        self.baseline_emissions = baseline_emissions
        self.scenarios = {}
        self.optimization_results = {}
        
        # Validate MACC data
        required_cols = ['technology', 'lcoa_usd_per_tco2', 'annual_abatement_potential',
                        'total_capex_required', 'deployment_units']
        missing_cols = [col for col in required_cols if col not in macc_df.columns]
        if missing_cols:
            raise ValueError(f"Missing required MACC columns: {missing_cols}")
    
    def add_scenario(self, scenario: PathwayScenario):
        """Add a pathway scenario for optimization"""
        self.scenarios[scenario.name] = scenario
    
    def create_default_scenarios(self):
        """Create standard net-zero pathway scenarios"""
        
        # Aggressive net-zero by 2030 
        aggressive = PathwayScenario(
            name="Aggressive_2030",
            target_year=2030,
            reduction_curve="exponential",
            annual_budget_limit=None,  # No budget limit
            interim_targets={2027: 0.5, 2028: 0.7, 2029: 0.9},  # 50%, 70%, 90% by these years
            discount_rate=0.08  # Higher discount rate for urgency
        )
        
        # Standard net-zero by 2050
        standard = PathwayScenario(
            name="Standard_2050", 
            target_year=2050,
            reduction_curve="linear",
            annual_budget_limit=10e6,  # $10M annual budget
            interim_targets={2030: 0.3, 2040: 0.7},  # 30% by 2030, 70% by 2040
            discount_rate=0.06
        )
        
        # Budget-constrained pathway
        constrained = PathwayScenario(
            name="Budget_Constrained",
            target_year=2045,
            reduction_curve="delayed_action", 
            annual_budget_limit=5e6,   # $5M annual budget
            interim_targets={2035: 0.4, 2040: 0.8},
            discount_rate=0.05
        )
        
        for scenario in [aggressive, standard, constrained]:
            self.add_scenario(scenario)
    
    def generate_reduction_targets(self, scenario: PathwayScenario) -> Dict[int, float]:
        """
        Generate annual emission reduction targets based on scenario parameters
        
        Returns:
            Dictionary mapping years to required cumulative reduction (tCO2e)
        """
        start_year = 2025
        years = list(range(start_year, scenario.target_year + 1))
        total_years = scenario.target_year - start_year
        targets = {}
        
        if scenario.reduction_curve == "linear":
            # Linear reduction to net-zero
            annual_reduction = self.baseline_emissions / total_years
            for i, year in enumerate(years):
                targets[year] = annual_reduction * (i + 1)
                
        elif scenario.reduction_curve == "exponential":
            # Exponential curve - faster reduction early
            for i, year in enumerate(years):
                progress = (i + 1) / total_years
                # Exponential curve: y = 1 - e^(-3x) scaled to reach 100%
                reduction_fraction = 1 - np.exp(-3 * progress)
                targets[year] = reduction_fraction * self.baseline_emissions
                
        elif scenario.reduction_curve == "delayed_action":
            # S-curve - slow start, accelerating later
            for i, year in enumerate(years):
                progress = (i + 1) / total_years
                # Sigmoid curve
                reduction_fraction = 1 / (1 + np.exp(-6 * (progress - 0.5)))
                targets[year] = reduction_fraction * self.baseline_emissions
        
        # Override with interim targets if specified
        if scenario.interim_targets:
            for target_year, reduction_pct in scenario.interim_targets.items():
                if target_year in targets:
                    targets[target_year] = reduction_pct * self.baseline_emissions
        
        # Ensure net-zero by target year
        targets[scenario.target_year] = self.baseline_emissions
        
        return targets
    
    def optimize_pathway(self, scenario_name: str) -> Dict:
        """
        Optimize deployment pathway for specified scenario using linear programming
        
        Args:
            scenario_name: Name of scenario to optimize
            
        Returns:
            Dictionary with optimization results
        """
        
        if scenario_name not in self.scenarios:
            raise ValueError(f"Scenario '{scenario_name}' not found")
        
        scenario = self.scenarios[scenario_name]
        reduction_targets = self.generate_reduction_targets(scenario)
        
        print(f"🎯 Optimizing pathway: {scenario_name}")
        print(f"   Target year: {scenario.target_year}")
        print(f"   Reduction curve: {scenario.reduction_curve}")
        print(f"   Budget limit: ${scenario.annual_budget_limit/1e6:.1f}M/year" if scenario.annual_budget_limit else "   No budget limit")
        
        # Prepare optimization data
        technologies = self.macc_df['technology'].tolist()
        years = list(range(2025, scenario.target_year + 1))
        
        # Create decision variables: deployment[tech, year] = units deployed in that year
        deployment = LpVariable.dicts(
            "deploy",
            [(tech, year) for tech in technologies for year in years],
            lowBound=0,
            cat='Continuous'
        )
        
        # Create optimization problem
        prob = LpProblem(f"NetZero_Pathway_{scenario_name}", LpMinimize)
        
        # Objective: Minimize total present value of costs
        total_cost = []
        base_year = 2025
        
        for year in years:
            year_cost = 0
            discount_factor = 1 / ((1 + scenario.discount_rate) ** (year - base_year))
            
            for tech in technologies:
                tech_data = self.macc_df[self.macc_df['technology'] == tech].iloc[0]
                
                # CAPEX cost (paid in deployment year)
                capex_per_unit = tech_data['total_capex_required'] / tech_data['deployment_units']
                
                # Annual OPEX cost (simplified - assume constant over lifetime)
                # Calculate from LCOA and abatement
                lcoa = tech_data['lcoa_usd_per_tco2']
                abatement_per_unit = tech_data['annual_abatement_potential'] / tech_data['deployment_units']
                
                # If LCOA is negative, there are net savings
                if lcoa < 0:
                    annual_opex_savings = -lcoa * abatement_per_unit
                    opex_impact = -annual_opex_savings  # Negative cost = savings
                else:
                    annual_opex_cost = lcoa * abatement_per_unit - capex_per_unit * 0.06  # Subtract finance cost
                    opex_impact = max(0, annual_opex_cost)  # Can't be negative
                
                # Total cost = CAPEX + discounted OPEX over lifetime (simplified to 10 years)
                lifetime_opex_pv = sum(opex_impact / ((1 + scenario.discount_rate) ** t) for t in range(1, 11))
                total_unit_cost = capex_per_unit + lifetime_opex_pv
                
                year_cost += total_unit_cost * deployment[(tech, year)] * discount_factor
            
            total_cost.append(year_cost)
        
        prob += lpSum(total_cost)
        
        # Constraint 1: Meet emission reduction targets each year
        for year in years:
            cumulative_abatement = 0
            
            # Sum abatement from all deployments up to this year
            for deploy_year in range(2025, year + 1):
                for tech in technologies:
                    tech_data = self.macc_df[self.macc_df['technology'] == tech].iloc[0]
                    abatement_per_unit = tech_data['annual_abatement_potential'] / tech_data['deployment_units']
                    
                    # Abatement continues for lifetime (assume 20 years average)
                    if year - deploy_year < 20:
                        cumulative_abatement += abatement_per_unit * deployment[(tech, deploy_year)]
            
            # Must meet or exceed reduction target
            prob += cumulative_abatement >= reduction_targets.get(year, 0)
        
        # Constraint 2: Annual budget limit (if specified)
        if scenario.annual_budget_limit:
            for year in years:
                year_capex = 0
                for tech in technologies:
                    tech_data = self.macc_df[self.macc_df['technology'] == tech].iloc[0]
                    capex_per_unit = tech_data['total_capex_required'] / tech_data['deployment_units']
                    year_capex += capex_per_unit * deployment[(tech, year)]
                
                prob += year_capex <= scenario.annual_budget_limit
        
        # Constraint 3: Technology deployment limits
        for tech in technologies:
            tech_data = self.macc_df[self.macc_df['technology'] == tech].iloc[0]
            max_total_units = tech_data['deployment_units']
            
            # Total deployment across all years cannot exceed maximum
            total_deployment = lpSum([deployment[(tech, year)] for year in years])
            prob += total_deployment <= max_total_units
        
        # Constraint 4: Technology-specific annual limits (if specified)
        if scenario.technology_constraints:
            for tech, annual_limit in scenario.technology_constraints.items():
                if tech in technologies:
                    for year in years:
                        prob += deployment[(tech, year)] <= annual_limit
        
        # Solve optimization problem
        print("   🔄 Solving optimization problem...")
        solver = PULP_CBC_CMD(msg=0)  # Suppress solver output
        prob.solve(solver)
        
        # Check solution status
        status = LpStatus[prob.status]
        print(f"   📊 Optimization status: {status}")
        
        if status != 'Optimal':
            print(f"   ⚠️ Warning: Solution may not be optimal")
            return {'status': status, 'feasible': False}
        
        # Extract results
        results = self.extract_optimization_results(deployment, technologies, years, scenario, reduction_targets)
        
        # Store results
        self.optimization_results[scenario_name] = results
        
        print(f"   ✅ Optimization complete!")
        print(f"   💰 Total cost: ${results['total_cost_pv']/1e6:.1f}M (present value)")
        print(f"   📈 Total abatement: {results['total_abatement']:,.0f} tCO2e/year")
        
        return results
    
    def extract_optimization_results(self, deployment, technologies, years, scenario, reduction_targets):
        """Extract and structure optimization results"""
        
        results = {
            'scenario': scenario.name,
            'status': 'Optimal',
            'feasible': True,
            'total_cost_pv': 0,
            'total_abatement': 0,
            'deployment_schedule': [],
            'annual_summary': [],
            'technology_summary': [],
            'reduction_trajectory': []
        }
        
        # Extract deployment schedule
        for year in years:
            for tech in technologies:
                deployed_units = deployment[(tech, year)].varValue or 0
                
                if deployed_units > 0.01:  # Only include significant deployments
                    tech_data = self.macc_df[self.macc_df['technology'] == tech].iloc[0]
                    capex_per_unit = tech_data['total_capex_required'] / tech_data['deployment_units']
                    abatement_per_unit = tech_data['annual_abatement_potential'] / tech_data['deployment_units']
                    
                    results['deployment_schedule'].append({
                        'year': year,
                        'technology': tech,
                        'units_deployed': deployed_units,
                        'capex': deployed_units * capex_per_unit,
                        'annual_abatement': deployed_units * abatement_per_unit,
                        'lcoa': tech_data['lcoa_usd_per_tco2'],
                        'unit_definition': tech_data.get('unit_definition', 'units')
                    })
        
        # Calculate annual summaries
        for year in years:
            year_capex = sum(item['capex'] for item in results['deployment_schedule'] if item['year'] == year)
            year_new_abatement = sum(item['annual_abatement'] for item in results['deployment_schedule'] if item['year'] == year)
            
            # Calculate cumulative abatement (including past deployments still operating)
            cumulative_abatement = 0
            for item in results['deployment_schedule']:
                if item['year'] <= year and (year - item['year']) < 20:  # 20-year asset life
                    cumulative_abatement += item['annual_abatement']
            
            results['annual_summary'].append({
                'year': year,
                'capex': year_capex,
                'new_abatement': year_new_abatement,
                'cumulative_abatement': cumulative_abatement,
                'reduction_target': reduction_targets.get(year, 0),
                'target_achievement': min(1.0, cumulative_abatement / reduction_targets.get(year, 1))
            })
        
        # Technology summaries
        for tech in technologies:
            tech_deployments = [item for item in results['deployment_schedule'] if item['technology'] == tech]
            
            if tech_deployments:
                total_units = sum(item['units_deployed'] for item in tech_deployments)
                total_capex = sum(item['capex'] for item in tech_deployments)
                total_abatement = sum(item['annual_abatement'] for item in tech_deployments)
                
                results['technology_summary'].append({
                    'technology': tech,
                    'total_units_deployed': total_units,
                    'total_capex': total_capex,
                    'total_annual_abatement': total_abatement,
                    'first_deployment_year': min(item['year'] for item in tech_deployments),
                    'deployment_years': len(set(item['year'] for item in tech_deployments))
                })
        
        # Calculate totals
        results['total_cost_pv'] = sum(item['capex'] / ((1 + scenario.discount_rate) ** (item['year'] - 2025)) 
                                      for item in results['deployment_schedule'])
        results['total_abatement'] = sum(item['total_annual_abatement'] for item in results['technology_summary'])
        
        return results
    
    def visualize_pathway(self, scenario_name: str, save_path: Optional[str] = None):
        """Create comprehensive visualization of optimized pathway"""
        
        if scenario_name not in self.optimization_results:
            raise ValueError(f"No results found for scenario '{scenario_name}'")
        
        results = self.optimization_results[scenario_name]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Emission Reduction Trajectory
        annual_df = pd.DataFrame(results['annual_summary'])
        
        ax1.plot(annual_df['year'], annual_df['cumulative_abatement']/1000, 'b-', linewidth=3, label='Achieved Abatement')
        ax1.plot(annual_df['year'], annual_df['reduction_target']/1000, 'r--', linewidth=2, label='Target')
        ax1.fill_between(annual_df['year'], 0, annual_df['cumulative_abatement']/1000, alpha=0.3, color='blue')
        
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Cumulative Abatement (ktCO2e/year)')
        ax1.set_title(f'Net-Zero Pathway: {scenario_name}', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add net-zero line
        ax1.axhline(y=self.baseline_emissions/1000, color='green', linestyle=':', linewidth=2, label='Net-Zero Target')
        
        # 2. Annual CAPEX Investment
        ax2.bar(annual_df['year'], annual_df['capex']/1e6, color='steelblue', alpha=0.7)
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Annual CAPEX (Million USD)')
        ax2.set_title('Investment Schedule', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # 3. Technology Deployment Timeline
        deployment_df = pd.DataFrame(results['deployment_schedule'])
        if not deployment_df.empty:
            # Create technology deployment heatmap
            tech_year_matrix = deployment_df.pivot_table(
                index='technology', 
                columns='year', 
                values='capex',
                aggfunc='sum',
                fill_value=0
            )
            
            sns.heatmap(tech_year_matrix/1e6, annot=False, cmap='YlOrRd', ax=ax3, cbar_kws={'label': 'CAPEX ($M)'})
            ax3.set_title('Technology Deployment Heatmap', fontsize=14, fontweight='bold')
            ax3.set_xlabel('Year')
            ax3.set_ylabel('Technology')
        
        # 4. Cumulative Investment by Technology
        tech_df = pd.DataFrame(results['technology_summary'])
        if not tech_df.empty:
            tech_df_sorted = tech_df.sort_values('total_capex', ascending=True)
            
            ax4.barh(tech_df_sorted['technology'], tech_df_sorted['total_capex']/1e6, color='darkgreen', alpha=0.7)
            ax4.set_xlabel('Total CAPEX (Million USD)')
            ax4.set_title('Investment by Technology', fontsize=14, fontweight='bold')
            ax4.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Pathway visualization saved to: {save_path}")
        
        plt.show()
    
    def compare_scenarios(self, save_path: Optional[str] = None):
        """Create comparison visualization of all optimized scenarios"""
        
        if not self.optimization_results:
            print("No optimization results to compare")
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        colors = plt.cm.tab10(np.linspace(0, 1, len(self.optimization_results)))
        
        # 1. Emission reduction trajectories
        for i, (scenario_name, results) in enumerate(self.optimization_results.items()):
            annual_df = pd.DataFrame(results['annual_summary'])
            ax1.plot(annual_df['year'], annual_df['cumulative_abatement']/1000, 
                    linewidth=3, label=scenario_name, color=colors[i])
        
        ax1.axhline(y=self.baseline_emissions/1000, color='red', linestyle='--', alpha=0.7, label='Net-Zero Target')
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Cumulative Abatement (ktCO2e/year)')
        ax1.set_title('Emission Reduction Trajectories', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 2. Total cost comparison
        scenario_names = list(self.optimization_results.keys())
        total_costs = [results['total_cost_pv']/1e6 for results in self.optimization_results.values()]
        
        bars = ax2.bar(scenario_names, total_costs, color=colors[:len(scenario_names)], alpha=0.7)
        ax2.set_ylabel('Total Cost (Million USD, PV)')
        ax2.set_title('Total Investment Comparison', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, cost in zip(bars, total_costs):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(total_costs)*0.01,
                    f'${cost:.0f}M', ha='center', va='bottom', fontweight='bold')
        
        # 3. Annual investment profiles
        for i, (scenario_name, results) in enumerate(self.optimization_results.items()):
            annual_df = pd.DataFrame(results['annual_summary'])
            ax3.plot(annual_df['year'], annual_df['capex']/1e6, 
                    linewidth=2, label=scenario_name, color=colors[i], marker='o', markersize=4)
        
        ax3.set_xlabel('Year')
        ax3.set_ylabel('Annual CAPEX (Million USD)')
        ax3.set_title('Investment Profiles', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # 4. Technology mix comparison
        all_techs = set()
        for results in self.optimization_results.values():
            tech_df = pd.DataFrame(results['technology_summary'])
            all_techs.update(tech_df['technology'].tolist())
        
        tech_comparison = {}
        for tech in all_techs:
            tech_comparison[tech] = []
            for scenario_name, results in self.optimization_results.items():
                tech_df = pd.DataFrame(results['technology_summary'])
                tech_row = tech_df[tech_df['technology'] == tech]
                investment = tech_row['total_capex'].iloc[0]/1e6 if not tech_row.empty else 0
                tech_comparison[tech].append(investment)
        
        # Create stacked bar chart
        bottom = np.zeros(len(scenario_names))
        tech_colors = plt.cm.Set3(np.linspace(0, 1, len(all_techs)))
        
        for i, (tech, investments) in enumerate(tech_comparison.items()):
            ax4.bar(scenario_names, investments, bottom=bottom, label=tech, 
                   color=tech_colors[i], alpha=0.8)
            bottom += np.array(investments)
        
        ax4.set_ylabel('Investment (Million USD)')
        ax4.set_title('Technology Mix by Scenario', fontsize=14, fontweight='bold')
        ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Scenario comparison saved to: {save_path}")
        
        plt.show()
    
    def generate_summary_report(self, scenario_name: str) -> str:
        """Generate text summary report for a scenario"""
        
        if scenario_name not in self.optimization_results:
            return f"No results found for scenario '{scenario_name}'"
        
        results = self.optimization_results[scenario_name]
        scenario = self.scenarios[scenario_name]
        
        report = f"""
NET-ZERO PATHWAY OPTIMIZATION REPORT
=====================================

Scenario: {scenario_name}
Target Year: {scenario.target_year}
Reduction Strategy: {scenario.reduction_curve}
Budget Constraint: ${scenario.annual_budget_limit/1e6:.1f}M/year" if scenario.annual_budget_limit else "No limit"

EXECUTIVE SUMMARY
-----------------
✓ Optimization Status: {results['status']}
✓ Total Investment Required: ${results['total_cost_pv']/1e6:.1f} Million (present value)
✓ Total Abatement Achieved: {results['total_abatement']:,.0f} tCO2e/year
✓ Baseline Emissions: {self.baseline_emissions:,.0f} tCO2e/year
✓ Net Reduction: {results['total_abatement']/self.baseline_emissions*100:.1f}%

TECHNOLOGY DEPLOYMENT SUMMARY
-----------------------------
"""
        
        tech_df = pd.DataFrame(results['technology_summary'])
        tech_df_sorted = tech_df.sort_values('total_capex', ascending=False)
        
        for _, tech in tech_df_sorted.iterrows():
            report += f"""
{tech['technology']}:
  - Investment: ${tech['total_capex']/1e6:.1f}M
  - Abatement: {tech['total_annual_abatement']:,.0f} tCO2e/year
  - First Deployment: {tech['first_deployment_year']}
  - Units: {tech['total_units_deployed']:.1f}
"""
        
        annual_df = pd.DataFrame(results['annual_summary'])
        
        report += f"""

IMPLEMENTATION TIMELINE
-----------------------
Peak Investment Year: {annual_df.loc[annual_df['capex'].idxmax(), 'year']} (${annual_df['capex'].max()/1e6:.1f}M)
Net-Zero Achievement: {annual_df.loc[annual_df['cumulative_abatement'].idxmax(), 'year']}
Average Annual Investment: ${annual_df['capex'].mean()/1e6:.1f}M

KEY MILESTONES
--------------
"""
        
        for _, year_data in annual_df.iterrows():
            if year_data['target_achievement'] >= 0.95:  # 95% of target achieved
                report += f"{int(year_data['year'])}: {year_data['cumulative_abatement']/1000:.0f} ktCO2e abated\n"
        
        return report


def main():
    """Test the Net-Zero Pathway Optimizer with real MACC data"""
    
    print("🌍 Net-Zero Pathway Optimizer")
    print("=" * 50)
    
    # Load MACC results (from previous step)
    try:
        macc_df = pd.read_csv("outputs/real_facilities_macc_results.csv")
        baseline_emissions = 1582281  # From previous MACC analysis
        print(f"✅ Loaded MACC data: {len(macc_df)} technologies")
    except FileNotFoundError:
        print("❌ MACC results not found. Please run generate_macc.py first.")
        return
    
    # Initialize optimizer
    optimizer = NetZeroPathwayOptimizer(macc_df, baseline_emissions)
    
    # Create default scenarios
    optimizer.create_default_scenarios()
    
    # Optimize each scenario
    for scenario_name in optimizer.scenarios.keys():
        print(f"\n🎯 Optimizing scenario: {scenario_name}")
        try:
            results = optimizer.optimize_pathway(scenario_name)
            
            if results['feasible']:
                # Generate visualization
                optimizer.visualize_pathway(scenario_name, 
                                           save_path=f"outputs/pathway_{scenario_name.lower()}.png")
                
                # Save detailed results
                pd.DataFrame(results['deployment_schedule']).to_csv(
                    f"outputs/deployment_schedule_{scenario_name.lower()}.csv", index=False)
                
                # Generate summary report
                report = optimizer.generate_summary_report(scenario_name)
                with open(f"outputs/pathway_report_{scenario_name.lower()}.txt", 'w') as f:
                    f.write(report)
                
                print(f"✅ {scenario_name} optimization complete")
            else:
                print(f"❌ {scenario_name} optimization failed - infeasible")
                
        except Exception as e:
            print(f"❌ Error optimizing {scenario_name}: {str(e)}")
    
    # Create scenario comparison
    if len(optimizer.optimization_results) > 1:
        print(f"\n📊 Creating scenario comparison...")
        optimizer.compare_scenarios(save_path="outputs/pathway_comparison.png")
    
    print(f"\n✅ Net-Zero Pathway Optimization Complete!")
    print(f"📁 Results saved to outputs/ directory")
    
    return optimizer


if __name__ == "__main__":
    import os
    os.makedirs("outputs", exist_ok=True)
    
    # Install PuLP if not available
    try:
        import pulp
    except ImportError:
        print("Installing PuLP for linear programming...")
        os.system("pip install pulp")
        import pulp
    
    optimizer = main()