# climate_risk_tool/transition_risk.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Dict, List, Union

class TransitionRisk:
    def __init__(self, facilities_xlsx: str, carbon_price_xlsx: str, scenario: str = "NDC", 
                 discount_rate: float = 0.05):
        """
        Initialize the TransitionRisk calculator.
        
        :param facilities_xlsx: Path to Excel with facility data (baseline emissions).
        :param carbon_price_xlsx: Path to Excel with carbon price scenarios.
        :param scenario: "NDC", "Below 2", or "Net-zero".
        :param discount_rate: Annual discount rate for NPV calculations (default: 5%).
        """
        self.facilities_xlsx = facilities_xlsx
        self.carbon_price_xlsx = carbon_price_xlsx
        self.scenario = scenario
        self.discount_rate = discount_rate
        self.transition_results = None
        self.df_fac = None
        self.df_prices = None
        self.npv_results = None
        
        # Configuration parameters that could be moved to settings
        self.start_year = 2025
        self.target_year = 2050
        self.valid_scenarios = ["NDC", "Below 2", "Net-zero"]
        
        # Default annual emission reduction rate (can be overridden)
        self.emission_reduction_rate = 0.02  # 2% annual reduction

    def load_data(self):
        """
        Loads facility and carbon price data from Excel files.
        
        Returns:
            tuple: (facilities_df, carbon_prices_df)
        """
        try:
            self.df_fac = pd.read_excel(self.facilities_xlsx)
            required_columns = ['facility_id', 'baseline_emissions_2024']
            missing = [col for col in required_columns if col not in self.df_fac.columns]
            if missing:
                raise ValueError(f"Facilities data missing required columns: {missing}")
                
            df_prices_raw = pd.read_excel(self.carbon_price_xlsx)
            required_columns = ['scenario', 'year', 'price_usd_per_tCO2e']
            missing = [col for col in required_columns if col not in df_prices_raw.columns]
            if missing:
                raise ValueError(f"Carbon price data missing required columns: {missing}")
                
            self.df_prices = df_prices_raw[df_prices_raw['scenario'] == self.scenario].copy()
            
            if self.df_prices.empty:
                raise ValueError(f"No data found for scenario '{self.scenario}'")
                
            return self.df_fac, self.df_prices
            
        except Exception as e:
            raise IOError(f"Error loading data: {str(e)}")

    def set_emission_reduction_rate(self, rate: float):
        """
        Set the annual emission reduction rate.
        
        :param rate: Annual reduction rate (e.g., 0.02 for 2% reduction per year)
        """
        if not 0 <= rate <= 1:
            raise ValueError("Emission reduction rate must be between 0 and 1")
        self.emission_reduction_rate = rate

    def project_emissions(self, baseline: float, year: int) -> float:
        """
        Project emissions for a given year based on baseline and reduction rate.
        
        :param baseline: Baseline emissions (tCO2e)
        :param year: Target year for projection
        :return: Projected emissions for the target year
        """
        years_from_baseline = year - 2024
        return baseline * (1 - self.emission_reduction_rate) ** years_from_baseline

    def compute_transition_costs(self):
        """
        Computes carbon costs with linearly reducing allowances from start_year to target_year.
        
        Returns:
            DataFrame: Results of transition cost calculations
        """
        if self.df_fac is None or self.df_prices is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        if self.scenario not in self.valid_scenarios:
            raise ValueError(f"Invalid scenario: {self.scenario}. Must be one of {self.valid_scenarios}")

        results_list = []
        for _, fac_row in self.df_fac.iterrows():
            facility_id = fac_row['facility_id']
            baseline_2024 = fac_row['baseline_emissions_2024']

            for _, price_row in self.df_prices.iterrows():
                year = price_row['year']
                price = price_row['price_usd_per_tCO2e']

                if year < self.start_year or year > self.target_year:
                    continue

                # Linear reduction: 100% in start_year to 0% in target_year
                allowance_rate = max(0, 1 - (year - self.start_year) / (self.target_year - self.start_year))
                allowance_tons = baseline_2024 * allowance_rate
                
                # Project actual emissions based on reduction rate
                actual_emissions = self.project_emissions(baseline_2024, year)
                
                excess_emissions = max(0, actual_emissions - allowance_tons)
                cost = excess_emissions * price

                results_list.append({
                    'facility_id': facility_id,
                    'year': year,
                    'allowance_rate': allowance_rate,
                    'allowance_tons': allowance_tons,
                    'carbon_price': price,
                    'actual_emissions': actual_emissions,
                    'excess_emissions': excess_emissions,
                    'ets_cost': cost
                })

        self.transition_results = pd.DataFrame(results_list)
        return self.transition_results

    def calculate_npv(self, base_year: int = 2024):
        """
        Calculate Net Present Value of transition costs.
        
        :param base_year: Base year for NPV calculation
        :return: DataFrame with NPV results
        """
        if self.transition_results is None:
            raise ValueError("Transition costs not calculated. Call compute_transition_costs() first.")
            
        npv_results = []
        
        for facility_id in self.transition_results['facility_id'].unique():
            facility_data = self.transition_results[self.transition_results['facility_id'] == facility_id]
            
            npv = 0
            for _, row in facility_data.iterrows():
                year = row['year']
                cost = row['ets_cost']
                discount_factor = 1 / ((1 + self.discount_rate) ** (year - base_year))
                npv += cost * discount_factor
                
            npv_results.append({
                'facility_id': facility_id,
                'npv_transition_cost': npv,
                'scenario': self.scenario
            })
            
        self.npv_results = pd.DataFrame(npv_results)
        return self.npv_results

    def plot_costs_over_time(self, facility_id: Optional[str] = None, 
                            save_path: Optional[str] = None):
        """
        Plot transition costs over time.
        
        :param facility_id: Optional facility ID to filter results
        :param save_path: Optional path to save the plot
        :return: matplotlib figure
        """
        if self.transition_results is None:
            raise ValueError("Transition costs not calculated. Call compute_transition_costs() first.")
            
        df = self.transition_results
        if facility_id:
            df = df[df['facility_id'] == facility_id]
            if df.empty:
                raise ValueError(f"No data found for facility_id {facility_id}")
                
        # Group by year and sum costs
        yearly_costs = df.groupby('year')['ets_cost'].sum().reset_index()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(yearly_costs['year'], yearly_costs['ets_cost'])
        ax.set_xlabel('Year')
        ax.set_ylabel('Carbon Cost (USD)')
        ax.set_title(f'Carbon Transition Costs - {self.scenario} Scenario')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
        return fig

    def generate_summary_report(self) -> Dict:
        """
        Generate a summary report of transition risk analysis.
        
        :return: Dictionary with summary statistics
        """
        if self.transition_results is None:
            raise ValueError("Transition costs not calculated. Call compute_transition_costs() first.")
            
        if self.npv_results is None:
            self.calculate_npv()
            
        total_cost = self.transition_results['ets_cost'].sum()
        total_npv = self.npv_results['npv_transition_cost'].sum()
        total_emissions = self.transition_results['actual_emissions'].sum()
        total_excess = self.transition_results['excess_emissions'].sum()
        
        # Cost by facility
        facility_costs = self.transition_results.groupby('facility_id')['ets_cost'].sum().reset_index()
        facility_costs = facility_costs.sort_values('ets_cost', ascending=False)
        
        # Cost by year
        yearly_costs = self.transition_results.groupby('year')['ets_cost'].sum().reset_index()
        
        return {
            'scenario': self.scenario,
            'total_cost': total_cost,
            'total_npv': total_npv,
            'total_emissions': total_emissions,
            'total_excess_emissions': total_excess,
            'facility_costs': facility_costs.to_dict('records'),
            'yearly_costs': yearly_costs.to_dict('records'),
            'highest_cost_facility': facility_costs.iloc[0]['facility_id'] if not facility_costs.empty else None,
            'highest_cost_year': yearly_costs.loc[yearly_costs['ets_cost'].idxmax()]['year'] if not yearly_costs.empty else None
        }

    def export_results(self, output_path: str):
        """
        Export transition risk results to Excel.
        
        :param output_path: Path to save the Excel file
        """
        if self.transition_results is None:
            raise ValueError("Transition costs not calculated. Call compute_transition_costs() first.")
            
        if self.npv_results is None:
            self.calculate_npv()
            
        with pd.ExcelWriter(output_path) as writer:
            self.transition_results.to_excel(writer, sheet_name='Transition Costs', index=False)
            self.npv_results.to_excel(writer, sheet_name='NPV Results', index=False)
            
            # Create summary sheet
            summary = self.generate_summary_report()
            summary_df = pd.DataFrame([{
                'Scenario': summary['scenario'],
                'Total Cost (USD)': summary['total_cost'],
                'Total NPV (USD)': summary['total_npv'],
                'Total Emissions (tCO2e)': summary['total_emissions'],
                'Total Excess Emissions (tCO2e)': summary['total_excess_emissions'],
                'Highest Cost Facility': summary['highest_cost_facility'],
                'Highest Cost Year': summary['highest_cost_year']
            }])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

    def print_results(self):
        """
        Print a formatted summary of transition risk results to the console.
        """
        if self.transition_results is None:
            raise ValueError("Transition costs not calculated. Call compute_transition_costs() first.")
            
        if self.npv_results is None:
            self.calculate_npv()
        
        summary = self.generate_summary_report()
        
        print("\n" + "="*80)
        print(f"TRANSITION RISK ANALYSIS SUMMARY - {summary['scenario']} SCENARIO")
        print("="*80)
        
        print(f"\nTotal Carbon Costs (2025-2050): ${summary['total_cost']:,.2f}")
        print(f"Net Present Value (NPV): ${summary['total_npv']:,.2f}")
        print(f"Total Projected Emissions: {summary['total_emissions']:,.2f} tCO2e")
        print(f"Total Excess Emissions: {summary['total_excess_emissions']:,.2f} tCO2e")
        
        print("\nTop 5 Facilities by Cost:")
        for i, facility in enumerate(summary['facility_costs'][:5], 1):
            print(f"  {i}. Facility {facility['facility_id']}: ${facility['ets_cost']:,.2f}")
            
        print("\nCosts by Year (first 5 years):")
        for year_data in summary['yearly_costs'][:5]:
            print(f"  {year_data['year']}: ${year_data['ets_cost']:,.2f}")
            
        print(f"\nHighest Cost Year: {summary['highest_cost_year']} (${max([y['ets_cost'] for y in summary['yearly_costs']]):,.2f})")
        print("="*80)
        
        return summary

    def run(self, export_path: Optional[str] = None, print_summary: bool = True):
        """
        Run the full transition risk analysis.
        
        :param export_path: Optional path to export results
        :param print_summary: Whether to print a summary to console (default: True)
        :return: DataFrame with transition cost results
        """
        self.load_data()
        self.compute_transition_costs()
        self.calculate_npv()
        
        if print_summary:
            self.print_results()
            
        if export_path:
            self.export_results(export_path)
            
        return self.transition_results
    