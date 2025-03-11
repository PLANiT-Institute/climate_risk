# climate_risk_tool/transition_risk.py
import pandas as pd
import numpy as np

class TransitionRisk:
    def __init__(self, facilities_xlsx: str, carbon_price_xlsx: str, scenario: str = "NDC"):
        """
        :param facilities_xlsx: Path to Excel with facility data (baseline emissions).
        :param carbon_price_xlsx: Path to Excel with carbon price scenarios.
        :param scenario: "NDC", "Below 2", or "Net-zero".
        """
        self.facilities_xlsx = facilities_xlsx
        self.carbon_price_xlsx = carbon_price_xlsx
        self.scenario = scenario
        self.transition_results = None
        self.df_fac = None
        self.df_prices = None
        
        # Configuration parameters that could be moved to settings
        self.start_year = 2025
        self.target_year = 2050

    def load_data(self):
        """Loads facility and carbon price data."""
        self.df_fac = pd.read_excel(self.facilities_xlsx)
        df_prices_raw = pd.read_excel(self.carbon_price_xlsx)
        self.df_prices = df_prices_raw[df_prices_raw['scenario'] == self.scenario].copy()

    def compute_transition_costs(self):
        """Computes carbon costs with linearly reducing allowances from 2025 to 2050."""
        if self.df_fac is None or self.df_prices is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        valid_scenarios = ["NDC", "Below 2", "Net-zero"]
        if self.scenario not in valid_scenarios:
            raise ValueError(f"Invalid scenario: {self.scenario}. Must be one of {valid_scenarios}")

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
                
                # TODO: Replace with actual emissions model if available
                actual_emissions = baseline_2024  # Simplified assumption
                
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

    def run(self):
        self.load_data()
        return self.compute_transition_costs()