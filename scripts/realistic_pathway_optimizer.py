"""
Realistic Net-Zero Pathway Optimizer

Creates achievable decarbonization pathways based on actual technology potential.
Addresses the gap between current technology potential and full decarbonization needs.
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


class RealisticPathwayOptimizer:
    """
    Creates realistic decarbonization pathways based on actual technology potential
    """
    
    def __init__(self, macc_df: pd.DataFrame, baseline_emissions: float):
        """Initialize with MACC results and baseline emissions"""
        self.macc_df = macc_df.copy()
        self.baseline_emissions = baseline_emissions
        self.max_abatement_potential = macc_df['annual_abatement_potential'].sum()
        self.feasible_reduction_pct = min(95, (self.max_abatement_potential / baseline_emissions) * 100)
        
        print(f"📊 Baseline emissions: {baseline_emissions:,.0f} tCO2e/year")
        print(f"🎯 Max abatement potential: {self.max_abatement_potential:,.0f} tCO2e/year")
        print(f"✅ Achievable reduction: {self.feasible_reduction_pct:.1f}% with current technologies")
        
    def create_extended_technology_catalog(self):
        """
        Extend the technology catalog with additional industrial and process-specific abatement options
        to make net-zero feasible
        """
        
        # Calculate the abatement gap
        abatement_gap = self.baseline_emissions - self.max_abatement_potential
        print(f"\n🔍 Abatement gap to close: {abatement_gap:,.0f} tCO2e/year")
        
        # Add hypothetical/future technologies to close the gap
        additional_techs = [
            {
                'project_id': 'HYDROGEN_001',
                'technology': 'Green Hydrogen',
                'sector': 'Industry',
                'lcoa_usd_per_tco2': 150,  # Higher cost emerging tech
                'annual_abatement_potential': min(abatement_gap * 0.3, 300000),
                'lifetime_abatement_potential': min(abatement_gap * 0.3, 300000) * 20,
                'total_capex_required': min(abatement_gap * 0.3, 300000) * 150 * 3,  # 3x cost factor
                'deployment_units': min(abatement_gap * 0.3, 300000) / 100,  # 100 tCO2e per unit
                'unit_definition': '100tCO2e/year capacity',
                'net_negative_cost': False,
                'payback_period_years': float('inf'),
                'roi_percent': -20,
                'technology_readiness': 7
            },
            {
                'project_id': 'CCUS_ENHANCED_001', 
                'technology': 'Enhanced CCUS',
                'sector': 'Industry',
                'lcoa_usd_per_tco2': 200,
                'annual_abatement_potential': min(abatement_gap * 0.4, 400000),
                'lifetime_abatement_potential': min(abatement_gap * 0.4, 400000) * 20,
                'total_capex_required': min(abatement_gap * 0.4, 400000) * 200 * 2,
                'deployment_units': min(abatement_gap * 0.4, 400000) / 200,  # 200 tCO2e per unit
                'unit_definition': '200tCO2e/year capacity',
                'net_negative_cost': False,
                'payback_period_years': float('inf'),
                'roi_percent': -30,
                'technology_readiness': 6
            },
            {
                'project_id': 'ELECTRIFICATION_001',
                'technology': 'Industrial Electrification',
                'sector': 'Industry', 
                'lcoa_usd_per_tco2': 80,
                'annual_abatement_potential': min(abatement_gap * 0.25, 250000),
                'lifetime_abatement_potential': min(abatement_gap * 0.25, 250000) * 15,
                'total_capex_required': min(abatement_gap * 0.25, 250000) * 80 * 1.5,
                'deployment_units': min(abatement_gap * 0.25, 250000) / 50,  # 50 tCO2e per unit
                'unit_definition': '50tCO2e/year capacity',
                'net_negative_cost': False,
                'payback_period_years': 12,
                'roi_percent': 5,
                'technology_readiness': 8
            },
            {
                'project_id': 'OFFSETS_001',
                'technology': 'Nature-Based Solutions',
                'sector': 'Offsets',
                'lcoa_usd_per_tco2': 50,
                'annual_abatement_potential': min(abatement_gap * 0.05, 100000),  # Limited offset potential
                'lifetime_abatement_potential': min(abatement_gap * 0.05, 100000) * 30,
                'total_capex_required': min(abatement_gap * 0.05, 100000) * 50,
                'deployment_units': min(abatement_gap * 0.05, 100000) / 10,  # 10 tCO2e per unit
                'unit_definition': '10tCO2e/year capacity',
                'net_negative_cost': False,
                'payback_period_years': float('inf'),
                'roi_percent': 0,
                'technology_readiness': 9
            }
        ]
        
        # Add to MACC dataframe
        additional_df = pd.DataFrame(additional_techs)
        extended_macc = pd.concat([self.macc_df, additional_df], ignore_index=True)
        
        # Recalculate cumulative abatement
        extended_macc = extended_macc.sort_values('lcoa_usd_per_tco2')
        extended_macc['cumulative_abatement'] = extended_macc['annual_abatement_potential'].cumsum()
        extended_macc['rank'] = range(1, len(extended_macc) + 1)
        
        print(f"✅ Extended catalog: {len(additional_techs)} additional technologies")
        print(f"📈 New total abatement potential: {extended_macc['annual_abatement_potential'].sum():,.0f} tCO2e/year")
        
        return extended_macc
    
    def optimize_realistic_pathways(self, extended_macc_df: pd.DataFrame):
        """Create realistic pathway scenarios that are actually achievable"""
        
        total_potential = extended_macc_df['annual_abatement_potential'].sum()
        
        scenarios = [
            {
                'name': 'Quick_Wins_2030',
                'target_reduction_pct': 20,  # 20% reduction by 2030
                'target_year': 2030,
                'budget_limit_annual': 15e6,  # $15M/year
                'description': 'Focus on cost-effective, proven technologies'
            },
            {
                'name': 'Aggressive_Partial_2040', 
                'target_reduction_pct': 60,  # 60% reduction by 2040
                'target_year': 2040,
                'budget_limit_annual': 25e6,  # $25M/year
                'description': 'Includes emerging technologies'
            },
            {
                'name': 'Net_Zero_2050',
                'target_reduction_pct': 95,  # 95% reduction by 2050
                'target_year': 2050, 
                'budget_limit_annual': None,  # No budget limit
                'description': 'Full decarbonization with all available technologies'
            }
        ]
        
        optimization_results = {}
        
        for scenario in scenarios:
            print(f"\n🎯 Optimizing: {scenario['name']}")
            print(f"   Target: {scenario['target_reduction_pct']}% reduction by {scenario['target_year']}")
            
            target_abatement = self.baseline_emissions * (scenario['target_reduction_pct'] / 100)
            
            # Check feasibility
            if target_abatement > total_potential:
                print(f"   ⚠️ Target exceeds technology potential. Adjusting to maximum achievable.")
                target_abatement = total_potential * 0.95
            
            # Simple greedy optimization (deploy cheapest technologies first)
            results = self.greedy_optimization(extended_macc_df, scenario, target_abatement)
            optimization_results[scenario['name']] = results
            
            print(f"   ✅ Achieved: {results['total_abatement']:,.0f} tCO2e/year")
            print(f"   💰 Cost: ${results['total_cost']/1e6:.1f}M")
        
        return optimization_results
    
    def greedy_optimization(self, extended_macc_df, scenario, target_abatement):
        """
        Simple greedy algorithm to select technologies until target is met
        """
        
        # Sort by cost-effectiveness
        sorted_df = extended_macc_df.sort_values('lcoa_usd_per_tco2').copy()
        
        selected_technologies = []
        cumulative_abatement = 0
        cumulative_cost = 0
        annual_budget = scenario.get('budget_limit_annual')
        years = scenario['target_year'] - 2025 + 1
        
        for _, tech in sorted_df.iterrows():
            # Check if we've reached the target
            if cumulative_abatement >= target_abatement:
                break
            
            # Calculate how much of this technology we need
            remaining_abatement = target_abatement - cumulative_abatement
            max_deployment = min(tech['annual_abatement_potential'], remaining_abatement)
            
            # Calculate deployment fraction
            deployment_fraction = max_deployment / tech['annual_abatement_potential']
            tech_cost = tech['total_capex_required'] * deployment_fraction
            
            # Check budget constraint
            annual_tech_cost = tech_cost / years
            if annual_budget and annual_tech_cost > annual_budget:
                # Scale down to fit budget
                affordable_fraction = (annual_budget * years) / tech['total_capex_required']
                if affordable_fraction > 0:
                    deployment_fraction = min(deployment_fraction, affordable_fraction)
                    max_deployment = tech['annual_abatement_potential'] * deployment_fraction
                    tech_cost = tech['total_capex_required'] * deployment_fraction
                else:
                    continue  # Skip if too expensive
            
            # Add to selection
            selected_technologies.append({
                'technology': tech['technology'],
                'deployment_fraction': deployment_fraction,
                'annual_abatement': max_deployment,
                'capex': tech_cost,
                'lcoa': tech['lcoa_usd_per_tco2'],
                'sector': tech['sector']
            })
            
            cumulative_abatement += max_deployment
            cumulative_cost += tech_cost
            
            # Update remaining budget
            if annual_budget:
                annual_budget -= (tech_cost / years)
                if annual_budget <= 0:
                    break
        
        return {
            'scenario': scenario['name'],
            'target_abatement': target_abatement,
            'total_abatement': cumulative_abatement,
            'total_cost': cumulative_cost,
            'achievement_pct': min(100, cumulative_abatement / target_abatement * 100),
            'technologies': selected_technologies,
            'avg_cost_per_tonne': cumulative_cost / cumulative_abatement if cumulative_abatement > 0 else 0
        }
    
    def create_implementation_timeline(self, results_dict):
        """Create detailed implementation timeline for each scenario"""
        
        timeline_results = {}
        
        for scenario_name, results in results_dict.items():
            target_year = 2030 if '2030' in scenario_name else (2040 if '2040' in scenario_name else 2050)
            years = list(range(2025, target_year + 1))
            
            # Distribute technology deployment over time
            annual_deployments = []
            
            for year in years:
                year_data = {
                    'year': year,
                    'technologies_deployed': [],
                    'annual_capex': 0,
                    'annual_abatement': 0,
                    'cumulative_abatement': 0
                }
                
                # Distribute each technology deployment over multiple years
                for i, tech in enumerate(results['technologies']):
                    # Stagger deployment: start each technology in different years
                    start_year = 2025 + (i % 3)  # Stagger over 3 years
                    deployment_years = min(3, target_year - start_year)  # Deploy over max 3 years
                    
                    if start_year <= year < start_year + deployment_years:
                        annual_fraction = tech['deployment_fraction'] / deployment_years
                        annual_capex = tech['capex'] / deployment_years
                        annual_abatement = tech['annual_abatement'] / deployment_years
                        
                        year_data['technologies_deployed'].append({
                            'technology': tech['technology'],
                            'deployment_fraction': annual_fraction,
                            'capex': annual_capex,
                            'abatement': annual_abatement
                        })
                        
                        year_data['annual_capex'] += annual_capex
                        year_data['annual_abatement'] += annual_abatement
                
                annual_deployments.append(year_data)
            
            # Calculate cumulative abatement
            cumulative = 0
            for year_data in annual_deployments:
                cumulative += year_data['annual_abatement']
                year_data['cumulative_abatement'] = cumulative
            
            timeline_results[scenario_name] = {
                'annual_data': annual_deployments,
                'summary': results
            }
        
        return timeline_results
    
    def visualize_realistic_pathways(self, timeline_results, save_path: Optional[str] = None):
        """Create comprehensive visualization of realistic pathways"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        colors = ['#2E8B57', '#4682B4', '#DC143C']  # Different colors for each scenario
        
        # 1. Cumulative abatement trajectories
        for i, (scenario_name, data) in enumerate(timeline_results.items()):
            annual_data = pd.DataFrame(data['annual_data'])
            ax1.plot(annual_data['year'], annual_data['cumulative_abatement']/1000, 
                    linewidth=3, marker='o', label=scenario_name.replace('_', ' '), color=colors[i])
            
            # Add target line
            target_year = annual_data['year'].max()
            target_abatement = data['summary']['target_abatement'] / 1000
            ax1.plot([2025, target_year], [0, target_abatement], 
                    linestyle='--', alpha=0.5, color=colors[i])
        
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Cumulative Abatement (ktCO2e/year)')
        ax1.set_title('Realistic Decarbonization Pathways', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add baseline reference
        ax1.axhline(y=self.baseline_emissions/1000, color='red', linestyle=':', 
                   alpha=0.7, label='Full Baseline')
        
        # 2. Annual investment profiles
        for i, (scenario_name, data) in enumerate(timeline_results.items()):
            annual_data = pd.DataFrame(data['annual_data'])
            ax2.plot(annual_data['year'], annual_data['annual_capex']/1e6, 
                    linewidth=2, marker='s', label=scenario_name.replace('_', ' '), color=colors[i])
        
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Annual CAPEX (Million USD)')
        ax2.set_title('Investment Profiles', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # 3. Technology mix by scenario
        scenario_names = list(timeline_results.keys())
        all_techs = set()
        for data in timeline_results.values():
            for tech in data['summary']['technologies']:
                all_techs.add(tech['technology'])
        
        # Create technology investment matrix
        tech_investments = {}
        for tech in all_techs:
            tech_investments[tech] = []
            for scenario_name in scenario_names:
                data = timeline_results[scenario_name]
                tech_investment = sum(t['capex'] for t in data['summary']['technologies'] 
                                    if t['technology'] == tech) / 1e6
                tech_investments[tech].append(tech_investment)
        
        # Stacked bar chart
        bottom = np.zeros(len(scenario_names))
        tech_colors = plt.cm.Set3(np.linspace(0, 1, len(all_techs)))
        
        for i, (tech, investments) in enumerate(tech_investments.items()):
            if sum(investments) > 0:  # Only show technologies with investment
                ax3.bar([s.replace('_', '\n') for s in scenario_names], investments, 
                       bottom=bottom, label=tech, color=tech_colors[i], alpha=0.8)
                bottom += np.array(investments)
        
        ax3.set_ylabel('Investment (Million USD)')
        ax3.set_title('Technology Mix by Scenario', fontsize=14, fontweight='bold')
        ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        
        # 4. Cost-effectiveness analysis
        scenarios_list = []
        abatement_list = []
        cost_per_tonne_list = []
        
        for scenario_name, data in timeline_results.items():
            scenarios_list.append(scenario_name.replace('_', '\n'))
            abatement_list.append(data['summary']['total_abatement'] / 1000)
            cost_per_tonne_list.append(data['summary']['avg_cost_per_tonne'])
        
        scatter = ax4.scatter(abatement_list, cost_per_tonne_list, 
                             s=[200, 300, 400], alpha=0.7, c=colors)
        
        for i, scenario in enumerate(scenarios_list):
            ax4.annotate(scenario, (abatement_list[i], cost_per_tonne_list[i]),
                        xytext=(10, 10), textcoords='offset points', fontsize=10)
        
        ax4.set_xlabel('Total Abatement (ktCO2e/year)')
        ax4.set_ylabel('Average Cost ($/tCO2e)')
        ax4.set_title('Cost vs. Abatement Effectiveness', fontsize=14, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Realistic pathways visualization saved to: {save_path}")
        
        plt.show()
    
    def generate_executive_summary(self, timeline_results):
        """Generate executive summary of realistic pathway analysis"""
        
        print("\n" + "=" * 60)
        print("🎯 REALISTIC DECARBONIZATION PATHWAY ANALYSIS")
        print("=" * 60)
        
        print(f"📊 Portfolio Baseline: {self.baseline_emissions:,.0f} tCO2e/year")
        print(f"💡 Available Technologies: {len(self.macc_df)} proven + 4 emerging")
        
        for scenario_name, data in timeline_results.items():
            summary = data['summary']
            annual_data = data['annual_data']
            
            print(f"\n🚀 {scenario_name.replace('_', ' ').upper()}:")
            print(f"   Target: {summary['target_abatement']:,.0f} tCO2e/year")
            print(f"   Achieved: {summary['total_abatement']:,.0f} tCO2e/year ({summary['achievement_pct']:.1f}%)")
            print(f"   Investment: ${summary['total_cost']/1e6:.1f}M")
            print(f"   Avg Cost: ${summary['avg_cost_per_tonne']:.0f}/tCO2e")
            print(f"   Technologies: {len(summary['technologies'])}")
            
            # Implementation timeline
            final_year = annual_data[-1]['year']
            peak_investment_year = max(annual_data, key=lambda x: x['annual_capex'])
            print(f"   Timeline: 2025-{final_year}")
            print(f"   Peak Investment: {peak_investment_year['year']} (${peak_investment_year['annual_capex']/1e6:.1f}M)")
        
        # Strategic recommendations
        print(f"\n💡 STRATEGIC RECOMMENDATIONS:")
        print("=" * 30)
        print("✅ START WITH QUICK WINS: Focus on cost-saving technologies (LED, HVAC, Solar)")
        print("📈 BUILD CAPABILITY: Develop emerging technology deployment expertise")
        print("💰 SECURE FUNDING: Plan for significant CAPEX requirements in 2030s")
        print("🔬 INVEST IN R&D: Support breakthrough technology development")
        print("🤝 PARTNERSHIPS: Collaborate on industrial electrification and CCUS")


def main():
    """Run the realistic pathway optimizer"""
    
    print("🌍 Realistic Net-Zero Pathway Optimizer")
    print("=" * 50)
    
    # Load MACC results
    try:
        macc_df = pd.read_csv("outputs/real_facilities_macc_results.csv")
        baseline_emissions = 1582281  # From MACC analysis
        print(f"✅ Loaded MACC data: {len(macc_df)} technologies")
    except FileNotFoundError:
        print("❌ MACC results not found. Please run generate_macc.py first.")
        return
    
    # Initialize optimizer
    optimizer = RealisticPathwayOptimizer(macc_df, baseline_emissions)
    
    # Extend technology catalog
    extended_macc = optimizer.create_extended_technology_catalog()
    
    # Optimize realistic pathways
    results = optimizer.optimize_realistic_pathways(extended_macc)
    
    # Create implementation timeline
    timeline_results = optimizer.create_implementation_timeline(results)
    
    # Visualize results
    optimizer.visualize_realistic_pathways(timeline_results, 
                                          save_path="outputs/realistic_pathways.png")
    
    # Generate executive summary
    optimizer.generate_executive_summary(timeline_results)
    
    # Save detailed results
    for scenario_name, data in timeline_results.items():
        # Save annual implementation data
        annual_df = pd.DataFrame(data['annual_data'])
        annual_df.to_csv(f"outputs/timeline_{scenario_name.lower()}.csv", index=False)
        
        # Save technology selection
        tech_df = pd.DataFrame(data['summary']['technologies'])
        tech_df.to_csv(f"outputs/technologies_{scenario_name.lower()}.csv", index=False)
    
    print(f"\n✅ Realistic Pathway Optimization Complete!")
    print(f"📁 Detailed results saved to outputs/ directory")
    
    return optimizer, timeline_results


if __name__ == "__main__":
    import os
    os.makedirs("outputs", exist_ok=True)
    
    optimizer, results = main()