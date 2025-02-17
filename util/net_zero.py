# climate_risk_tool/net_zero.py
import pandas as pd
import numpy as np


class NetZeroPathway:
    def __init__(self, facilities_xlsx: str, approach='linear'):
        """
        :param facilities_xlsx: Excel with baseline emissions data
        :param approach: 'linear' or 'absolute'
        """
        self.facilities_xlsx = facilities_xlsx
        self.approach = approach
        self.netzero_df = None

    def load_data(self):
        self.df_fac = pd.read_excel(self.facilities_xlsx)

    def calculate_pathway(self):
        results = []
        for _, row in self.df_fac.iterrows():
            fac_id = row['facility_id']
            base_em = row['baseline_emissions_2024']

            for year in range(2025, 2051):
                if self.approach == 'linear':
                    total_years = 2050 - 2024
                    done_years = year - 2024
                    fraction = max(0, 1 - done_years / total_years)
                    target_em = base_em * fraction
                else:
                    # Example absolute approach
                    if year <= 2030:
                        target_em = base_em * 0.5
                    elif year <= 2040:
                        target_em = base_em * 0.2
                    else:
                        target_em = 0

                results.append({
                    'facility_id': fac_id,
                    'year': year,
                    'net_zero_target_emissions': target_em
                })

        self.netzero_df = pd.DataFrame(results)
        return self.netzero_df

    def run(self):
        self.load_data()
        return self.calculate_pathway()
