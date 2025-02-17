# climate_risk_tool/transition_risk.py
import pandas as pd
import numpy as np


class TransitionRisk:
    def __init__(self,
                 facilities_xlsx: str,
                 carbon_price_xlsx: str,
                 allowance_rates_xlsx: str = None,
                 scenario: str = "NDC"):
        """
        :param facilities_xlsx: Path to Excel with facility data (including baseline emissions).
        :param carbon_price_xlsx: Path to Excel with carbon price data by year & scenario.
        :param allowance_rates_xlsx: (Optional) Path to Excel with allowance rates by year.
        :param scenario: e.g., "NDC", "Below2", "Net-zero".
        """
        self.facilities_xlsx = facilities_xlsx
        self.carbon_price_xlsx = carbon_price_xlsx
        self.allowance_rates_xlsx = allowance_rates_xlsx
        self.scenario = scenario
        self.transition_results = None

    def load_data(self):
        """Loads the facility and carbon price data from Excel."""
        # 1. Facilities
        self.df_fac = pd.read_excel(self.facilities_xlsx)

        # 2. Carbon prices
        df_prices_raw = pd.read_excel(self.carbon_price_xlsx)
        self.df_prices = df_prices_raw[df_prices_raw['scenario'] == self.scenario].copy()

        # 3. Allowance rates (optional)
        if self.allowance_rates_xlsx:
            self.df_allowance = pd.read_excel(self.allowance_rates_xlsx)
        else:
            self.df_allowance = None

    def compute_transition_costs(self):
        """
        Computes the ETS-based carbon costs from 2025 to 2050,
        assuming a linear reduction from 100% allowance in 2025 to 0% by 2050
        (if no allowance file is provided).
        """
        if self.df_fac is None or self.df_prices is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        results_list = []

        for _, fac_row in self.df_fac.iterrows():
            facility_id = fac_row['facility_id']
            baseline_2024 = fac_row['baseline_emissions_2024']

            # (You could also read actual projected emissions if available)

            for _, price_row in self.df_prices.iterrows():
                year = price_row['year']
                price = price_row['price_usd_per_tCO2e']

                # Only process 2025–2050
                if year < 2025 or year > 2050:
                    continue

                # Determine allowance
                if self.df_allowance is not None:
                    row_allw = self.df_allowance[(self.df_allowance['year'] == year)]
                    if not row_allw.empty:
                        allowance_rate = row_allw.iloc[0]['allowance_rate']
                    else:
                        allowance_rate = 0.0
                else:
                    # Linear formula: 100% in 2025 → 0% in 2050
                    allowance_rate = max(0, 1 - (year - 2025) / (2050 - 2025))

                allowance_tons = baseline_2024 * allowance_rate
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

        df_results = pd.DataFrame(results_list)
        self.transition_results = df_results
        return df_results

    def run(self):
        """Main method to orchestrate the transition risk calculation."""
        self.load_data()
        return self.compute_transition_costs()
