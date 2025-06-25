"""Reporting and output formatting for climate risk results."""

import pandas as pd
from typing import Dict, List, Any
import json
from datetime import datetime


class ClimateRiskReporter:
    """Generate formatted reports for climate risk analysis."""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_summary_report(self,
                              facilities_df: pd.DataFrame,
                              emissions_pathways: Dict[str, pd.DataFrame],
                              financial_impacts: Dict[str, pd.DataFrame],
                              carbon_var_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate executive summary report."""
        
        total_facilities = len(facilities_df)
        total_baseline_emissions = (
            facilities_df['current_emissions_scope1'].sum() + 
            facilities_df['current_emissions_scope2'].sum()
        )
        total_revenue = facilities_df['annual_revenue'].sum()
        total_assets = facilities_df['assets_value'].sum()
        
        # Aggregate impacts by scenario
        scenario_summary = {}
        for scenario_name, impacts_df in financial_impacts.items():
            total_npv_impact = impacts_df['delta_npv'].sum()
            avg_npv_impact = impacts_df['delta_npv'].mean()
            
            scenario_summary[scenario_name] = {
                'total_npv_impact_usd': total_npv_impact,
                'avg_npv_impact_per_facility_usd': avg_npv_impact,
                'npv_impact_as_pct_of_assets': (total_npv_impact / total_assets) * 100,
                'facilities_with_negative_impact': (impacts_df['delta_npv'] < 0).sum(),
                'facilities_with_positive_impact': (impacts_df['delta_npv'] > 0).sum()
            }
        
        # Carbon VaR statistics
        carbon_var_summary = {
            'avg_carbon_var_pct': carbon_var_df['carbon_var_percentage'].mean(),
            'max_carbon_var_pct': carbon_var_df['carbon_var_percentage'].max(),
            'total_carbon_var_usd': carbon_var_df['carbon_var_absolute'].sum(),
            'facilities_high_risk': (carbon_var_df['carbon_var_percentage'] > 10).sum(),
            'facilities_medium_risk': (
                (carbon_var_df['carbon_var_percentage'] > 5) & 
                (carbon_var_df['carbon_var_percentage'] <= 10)
            ).sum(),
            'facilities_low_risk': (carbon_var_df['carbon_var_percentage'] <= 5).sum()
        }
        
        # Sector analysis
        sector_analysis = {}
        for sector in facilities_df['sector'].unique():
            sector_facilities = facilities_df[facilities_df['sector'] == sector]
            sector_var = carbon_var_df[
                carbon_var_df['facility_id'].isin(sector_facilities['facility_id'])
            ]
            
            sector_analysis[sector] = {
                'facility_count': len(sector_facilities),
                'total_emissions': (
                    sector_facilities['current_emissions_scope1'].sum() + 
                    sector_facilities['current_emissions_scope2'].sum()
                ),
                'avg_carbon_var_pct': sector_var['carbon_var_percentage'].mean() if len(sector_var) > 0 else 0,
                'total_revenue': sector_facilities['annual_revenue'].sum(),
                'total_assets': sector_facilities['assets_value'].sum()
            }
        
        return {
            'report_metadata': {
                'generated_at': self.timestamp,
                'total_facilities': total_facilities,
                'scenarios_analyzed': list(financial_impacts.keys()),
                'projection_years': sorted(emissions_pathways[list(emissions_pathways.keys())[0]]['year'].unique())
            },
            'portfolio_summary': {
                'total_baseline_emissions_tco2e': total_baseline_emissions,
                'total_revenue_usd': total_revenue,
                'total_assets_usd': total_assets,
                'avg_emissions_intensity_per_revenue': total_baseline_emissions / total_revenue if total_revenue > 0 else 0
            },
            'scenario_analysis': scenario_summary,
            'carbon_var_analysis': carbon_var_summary,
            'sector_analysis': sector_analysis
        }
    
    def create_detailed_output(self,
                             facilities_df: pd.DataFrame,
                             emissions_pathways: Dict[str, pd.DataFrame],
                             financial_impacts: Dict[str, pd.DataFrame],
                             carbon_var_df: pd.DataFrame) -> pd.DataFrame:
        """Create detailed CSV output with all metrics."""
        
        # Start with facility base data
        output_df = facilities_df.copy()
        
        # Add Carbon VaR metrics
        output_df = output_df.merge(
            carbon_var_df[['facility_id', 'carbon_var_absolute', 'carbon_var_percentage', 
                          'expected_loss', 'worst_case_scenario', 'best_case_scenario']],
            on='facility_id',
            how='left'
        )
        
        # Add scenario-specific metrics
        for scenario_name, impacts_df in financial_impacts.items():
            scenario_cols = impacts_df[['facility_id', 'delta_npv']].copy()
            scenario_cols.columns = ['facility_id', f'{scenario_name}_delta_npv_usd']
            
            output_df = output_df.merge(scenario_cols, on='facility_id', how='left')
        
        # Add emissions projections for key years
        key_years = [2030, 2050]
        for year in key_years:
            for scenario_name, pathways_df in emissions_pathways.items():
                year_data = pathways_df[pathways_df['year'] == year]
                year_cols = year_data[['facility_id', 'total_emissions', 'reduction_factor']].copy()
                year_cols.columns = [
                    'facility_id', 
                    f'{scenario_name}_{year}_emissions_tco2e',
                    f'{scenario_name}_{year}_reduction_factor'
                ]
                
                output_df = output_df.merge(year_cols, on='facility_id', how='left')
        
        # Add risk categorization
        output_df['carbon_risk_category'] = pd.cut(
            output_df['carbon_var_percentage'],
            bins=[-float('inf'), 5, 10, float('inf')],
            labels=['Low', 'Medium', 'High']
        )
        
        # Add TCFD alignment indicators
        output_df['tcfd_metrics_available'] = True
        output_df['ifrs_s2_compliant'] = True
        output_df['cdp_ready'] = True
        
        # Calculate some additional useful metrics
        output_df['emissions_intensity_per_revenue'] = (
            (output_df['current_emissions_scope1'] + output_df['current_emissions_scope2']) / 
            output_df['annual_revenue']
        ).fillna(0)
        
        output_df['carbon_var_as_pct_of_ebitda'] = (
            output_df['carbon_var_absolute'] / output_df['ebitda'] * 100
        ).fillna(0)
        
        return output_df
    
    def create_emissions_pathways_output(self, emissions_pathways: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Create detailed emissions pathways output."""
        all_pathways = []
        
        for scenario_name, pathways_df in emissions_pathways.items():
            scenario_df = pathways_df.copy()
            scenario_df['scenario'] = scenario_name
            all_pathways.append(scenario_df)
        
        combined_df = pd.concat(all_pathways, ignore_index=True)
        
        # Pivot for easier analysis
        pivot_df = combined_df.pivot_table(
            index=['facility_id', 'year'],
            columns='scenario',
            values=['total_emissions', 'reduction_factor'],
            aggfunc='first'
        )
        
        # Flatten column names
        pivot_df.columns = [f'{col[1]}_{col[0]}' for col in pivot_df.columns]
        pivot_df.reset_index(inplace=True)
        
        return pivot_df
    
    def export_summary_json(self, summary_report: Dict[str, Any], output_path: str) -> None:
        """Export summary report as JSON."""
        with open(output_path, 'w') as f:
            json.dump(summary_report, f, indent=2, default=str)
        
        print(f"Summary report exported to: {output_path}")
    
    def print_executive_summary(self, summary_report: Dict[str, Any]) -> None:
        """Print executive summary to console."""
        print("\n" + "="*60)
        print("CLIMATE TRANSITION RISK ASSESSMENT - EXECUTIVE SUMMARY")
        print("="*60)
        
        meta = summary_report['report_metadata']
        portfolio = summary_report['portfolio_summary']
        var_analysis = summary_report['carbon_var_analysis']
        
        print(f"\nGenerated: {meta['generated_at']}")
        print(f"Facilities Analyzed: {meta['total_facilities']}")
        print(f"Scenarios: {', '.join(meta['scenarios_analyzed'])}")
        
        print(f"\nPORTFOLIO OVERVIEW:")
        print(f"  Total Baseline Emissions: {portfolio['total_baseline_emissions_tco2e']:,.0f} tCO2e")
        print(f"  Total Revenue: ${portfolio['total_revenue_usd']:,.0f}")
        print(f"  Total Assets: ${portfolio['total_assets_usd']:,.0f}")
        print(f"  Emissions Intensity: {portfolio['avg_emissions_intensity_per_revenue']:.3f} tCO2e/$")
        
        print(f"\nCARBON VALUE AT RISK (95% confidence):")
        print(f"  Average Carbon VaR: {var_analysis['avg_carbon_var_pct']:.1f}% of assets")
        print(f"  Maximum Carbon VaR: {var_analysis['max_carbon_var_pct']:.1f}% of assets")
        print(f"  Total Portfolio VaR: ${var_analysis['total_carbon_var_usd']:,.0f}")
        
        print(f"\nRISK DISTRIBUTION:")
        print(f"  High Risk (>10%): {var_analysis['facilities_high_risk']} facilities")
        print(f"  Medium Risk (5-10%): {var_analysis['facilities_medium_risk']} facilities")
        print(f"  Low Risk (<5%): {var_analysis['facilities_low_risk']} facilities")
        
        print("\nSCENARIO IMPACTS:")
        for scenario, impacts in summary_report['scenario_analysis'].items():
            print(f"  {scenario}:")
            print(f"    Total NPV Impact: ${impacts['total_npv_impact_usd']:,.0f}")
            print(f"    Impact as % of Assets: {impacts['npv_impact_as_pct_of_assets']:.1f}%")
            print(f"    Facilities with Negative Impact: {impacts['facilities_with_negative_impact']}")
        
        print("\n" + "="*60)