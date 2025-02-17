# climate_risk_tool/climate_var.py
import pandas as pd
import numpy as np
from scipy.stats import norm, t


class ClimateVaR:
    def __init__(self,
                 transition_df: pd.DataFrame,
                 physical_df: pd.DataFrame,
                 netzero_df: pd.DataFrame):
        """
        :param transition_df: Year-by-year ETS cost data
        :param physical_df: Could be year-by-year or scenario-based EAL
        :param netzero_df: Year-by-year net-zero target
        """
        self.transition_df = transition_df
        self.physical_df = physical_df
        self.netzero_df = netzero_df

    def generate_correlated_shocks(self, n_sim, years, corr_matrix):
        """
        Example function to create correlated random shocks for each year.
        :param n_sim: number of simulations
        :param years: list or range of years (e.g. 2025->2050)
        :param corr_matrix: NxN correlation matrix
        Return: A dictionary of shocks keyed by year
        """
        # Suppose we have two main factors: F1 (carbon price shock), F2 (hazard intensity shock).
        # corr_matrix = [[1, 0.3],
        #                [0.3, 1]]  # Example correlation
        # We'll draw from a Student-t distribution (fat-tailed).

        from numpy.linalg import cholesky

        L = cholesky(corr_matrix)
        # We'll create Nx number_of_factors random draws for each year
        # For simplicity, let's assume 2 factors for all years
        shocks = {}
        for y in years:
            # Generate random draws from t-distribution
            # e.g., df=5 => heavier tails than normal
            raw_draws = t.rvs(df=5, size=(n_sim, 2))
            # Correlate them
            correlated = raw_draws @ L.T
            # We store them
            shocks[y] = correlated
        return shocks

    def run_deep_monte_carlo(self, n_sim=1000, percentile=0.95):
        """
        A more advanced multi-year approach, factoring in correlations
        and returning a distribution of total NPV or cumulative cost.
        """
        # Identify years
        years = range(2025, 2051)

        # Prepare correlation matrix for 2 factors: carbon price shock, hazard shock
        # In a real model, you'd have more factors or a user-defined matrix
        corr_matrix = np.array([
            [1.0, 0.3],
            [0.3, 1.0]
        ])

        # Generate correlated shocks
        shocks_dict = self.generate_correlated_shocks(n_sim, years, corr_matrix)

        # We might want to discount future cash flows. Suppose discount rate = 3%
        discount_rate = 0.03

        # Collect total present value of costs per simulation
        total_costs_array = np.zeros(n_sim)

        for i in range(n_sim):
            # For each simulation, we accumulate discounted cost from 2025->2050
            pv_cost = 0.0
            for y in years:
                # Extract the relevant shock draws for this year
                # shocks_dict[y][i,0] -> carbon price shock
                # shocks_dict[y][i,1] -> hazard shock
                cp_shock = shocks_dict[y][i, 0]  # carbon price shock
                hz_shock = shocks_dict[y][i, 1]  # hazard shock

                # 1. Transition cost
                df_yr = self.transition_df[self.transition_df['year'] == y]
                base_trans_cost = df_yr['ets_cost'].sum()
                # Adjust by shock. We can define a transformation
                # e.g. final = base * exp(0.1 * cp_shock)
                # meaning if cp_shock=1, we have e^(0.1)=1.105 => ~10% increase
                trans_cost_sim = base_trans_cost * np.exp(0.1 * cp_shock)

                # 2. Physical cost
                # If your physical_df has year-by-year data, filter it similarly
                # If not, assume 1 for all years or a single scenario
                # We'll just do a single scenario approach:
                base_phys_cost = self.physical_df['annual_flood_loss'].sum()
                # Adjust with hazard shock
                phys_cost_sim = base_phys_cost * np.exp(0.2 * hz_shock)

                # 3. Net-zero penalty (if actual > target)
                # For demonstration, let's do a quick approach:
                df_nz_yr = self.netzero_df[self.netzero_df['year'] == y]
                # Compare baseline vs target
                penalty_sum = 0
                for _, row_nz in df_nz_yr.iterrows():
                    fac_id = row_nz['facility_id']
                    target_em = row_nz['net_zero_target_emissions']
                    # We find the actual from transition (or from baseline)
                    df_base = self.transition_df[
                        (self.transition_df['facility_id'] == fac_id) &
                        (self.transition_df['year'] == 2024)
                        ]
                    if not df_base.empty:
                        actual_2024 = df_base.iloc[0]['actual_emissions']
                    else:
                        actual_2024 = target_em
                    diff = max(0, actual_2024 - target_em)
                    # Let's assume a random carbon price for penalty
                    # scaled by shock
                    penalty_price = 40.0 * np.exp(0.1 * cp_shock)  # 40 base
                    penalty_sum += diff * penalty_price
                nz_penalty = penalty_sum

                # Sum costs for this year
                year_cost = trans_cost_sim + phys_cost_sim + nz_penalty
                # Discount to present (assuming year 2024 as present)
                years_from_2024 = y - 2024
                year_pv = year_cost / ((1 + discount_rate) ** years_from_2024)
                pv_cost += year_pv

            total_costs_array[i] = pv_cost

        # Now we have a distribution of total costs (NPV) for n_sim runs
        sorted_costs = np.sort(total_costs_array)
        idx = int(np.ceil(percentile * n_sim)) - 1
        var_value = sorted_costs[idx]

        # Return the VaR and the entire distribution
        return var_value, total_costs_array
