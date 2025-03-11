import pandas as pd
import numpy as np
from scipy.stats import norm, t, multivariate_normal, norm, skewnorm
from typing import Dict, List, Tuple, Optional, Union
import matplotlib.pyplot as plt
import seaborn as sns





class ClimateVaR:
    """
    Enhanced Climate Value at Risk (VaR) implementation with improved correlation structure
    and risk factor modeling.
    """

    def __init__(self,
                 transition_df: pd.DataFrame,
                 physical_df: pd.DataFrame,
                 netzero_df: pd.DataFrame,
                 discount_rate: float = 0.03,
                 correlation_config: Optional[Dict[str, float]] = None):
        """
        Initialize Climate VaR calculator.

        Args:
            transition_df: Year-by-year ETS cost data
            physical_df: Physical risk data, could be year-by-year or scenario-based EAL
            netzero_df: Year-by-year net-zero target
            discount_rate: Discount rate for future cash flows (default: 0.03)
            correlation_config: Dictionary with correlation parameters
        """
        self.transition_df = transition_df
        self.physical_df = physical_df
        self.netzero_df = netzero_df
        self.discount_rate = discount_rate

        # Set up correlation config
        self.correlation_config = correlation_config or {
            # Correlation between carbon price and physical hazard
            'carbon_hazard': 0.3,
            # Correlation between carbon price and policy stringency
            'carbon_policy': 0.7,
            # Correlation between hazard and policy stringency
            'hazard_policy': 0.2,
            # Year-to-year correlation (persistency)
            'year_persistency': 0.8
        }

    def _generate_correlated_risk_factors(self,
                                          n_sim: int,
                                          years: List[int],
                                          n_factors: int = 3) -> Dict[int, np.ndarray]:
        """
        Generate correlated risk factors for simulation.

        Args:
            n_sim: Number of simulations
            years: List of years to simulate
            n_factors: Number of risk factors (default: 3)
                1. Carbon price shock
                2. Hazard intensity shock
                3. Policy stringency shock

        Returns:
            Dictionary mapping years to arrays of shape (n_sim, n_factors)
        """
        # Define base correlation matrix
        corr_matrix = np.array([
            [1.0, self.correlation_config['carbon_hazard'], self.correlation_config['carbon_policy']],
            [self.correlation_config['carbon_hazard'], 1.0, self.correlation_config['hazard_policy']],
            [self.correlation_config['carbon_policy'], self.correlation_config['hazard_policy'], 1.0]
        ])

        # Check if matrix is positive semi-definite
        # If not, adjust to nearest PSD matrix
        min_eig = np.min(np.linalg.eigvals(corr_matrix))
        if min_eig < 0:
            corr_matrix -= min_eig * np.eye(len(corr_matrix)) * 1.1
            # Renormalize
            d = np.sqrt(np.diag(corr_matrix))
            corr_matrix = corr_matrix / np.outer(d, d)

        # Cholesky decomposition for generating correlated variables
        L = np.linalg.cholesky(corr_matrix)

        # Year-to-year correlation factor
        year_persistency = self.correlation_config['year_persistency']

        # Generate risk factors
        risk_factors = {}

        # Previous year's shocks (start with zeros)
        prev_shocks = np.zeros((n_sim, n_factors))

        for y in years:
            # Generate raw draws from t-distribution (heavier tails than normal)
            raw_draws = t.rvs(df=5, size=(n_sim, n_factors))

            # Apply correlation structure within the year
            correlated = raw_draws @ L.T

            # Apply temporal correlation (year-to-year persistency)
            if y == min(years):
                # First year has no previous year
                year_shocks = correlated
            else:
                # Mix previous year's shocks with new ones
                year_shocks = year_persistency * prev_shocks + np.sqrt(1 - year_persistency ** 2) * correlated

            # Store and update previous shocks
            risk_factors[y] = year_shocks
            prev_shocks = year_shocks

        return risk_factors

    def _apply_carbon_price_shock(self,
                                  base_price: float,
                                  shock: float,
                                  year: int) -> float:
        """
        Apply shock to carbon price.

        Args:
            base_price: Base carbon price
            shock: Shock value (from risk factor simulation)
            year: Simulation year

        Returns:
            Adjusted carbon price
        """
        # Progressive shock impact - earlier years have less volatility
        current_year = min(max(2025, year), 2050)
        years_from_2025 = current_year - 2025
        max_years = 2050 - 2025

        # Shock multiplier increases over time
        # Starts at 0.05 and grows to 0.2
        shock_mult = 0.05 + (0.15 * years_from_2025 / max_years)

        # Apply shock: base * exp(shock_mult * shock)
        return base_price * np.exp(shock_mult * shock)

    def _apply_hazard_shock(self,
                            base_hazard: float,
                            shock: float,
                            year: int) -> float:
        """
        Apply shock to physical hazard intensity.

        Args:
            base_hazard: Base hazard intensity/cost
            shock: Shock value (from risk factor simulation)
            year: Simulation year

        Returns:
            Adjusted hazard intensity/cost
        """
        # Progressive intensity - later years have more volatility
        current_year = min(max(2025, year), 2050)
        years_from_2025 = current_year - 2025
        max_years = 2050 - 2025

        # Shock multiplier increases over time
        # Starts at 0.1 and grows to 0.3
        shock_mult = 0.1 + (0.2 * years_from_2025 / max_years)

        # Apply shock: base * exp(shock_mult * shock)
        return base_hazard * np.exp(shock_mult * shock)

    def _apply_policy_shock(self,
                            emissions_gap: float,
                            shock: float,
                            year: int) -> float:
        """
        Apply shock to policy stringency (affecting net-zero penalties).

        Args:
            emissions_gap: Gap between actual and target emissions
            shock: Shock value (from risk factor simulation)
            year: Simulation year

        Returns:
            Adjusted penalty multiplier
        """
        # Progressive stringency - later years have more strict enforcement
        current_year = min(max(2025, year), 2050)
        years_from_2025 = current_year - 2025
        max_years = 2050 - 2025

        # Base multiplier increases over time from 0.5 to 2.0
        base_mult = 0.5 + (1.5 * years_from_2025 / max_years)

        # Shock effect ranges from 0.5 to 2.0
        shock_effect = np.exp(0.25 * shock)

        return base_mult * shock_effect

    def _calculate_year_costs(self,
                              year: int,
                              risk_factors: np.ndarray,
                              sim_idx: int) -> Dict[str, float]:
        """
        Calculate costs for a specific year in a simulation.

        Args:
            year: Simulation year
            risk_factors: Risk factors array for this year and sim
            sim_idx: Simulation index

        Returns:
            Dictionary with costs by category
        """
        # Extract risk factors
        carbon_shock = risk_factors[0]
        hazard_shock = risk_factors[1]
        policy_shock = risk_factors[2]

        # 1. Calculate transition cost
        year_transition = self.transition_df[self.transition_df['year'] == year]
        base_trans_cost = year_transition['ets_cost'].sum() if not year_transition.empty else 0

        # Apply carbon price shock
        trans_cost_sim = self._apply_carbon_price_shock(
            base_trans_cost, carbon_shock, year
        )

        # 2. Calculate physical cost
        # Get base physical risk cost
        if 'year' in self.physical_df.columns:
            # If we have year-specific data
            year_physical = self.physical_df[self.physical_df['year'] == year]
            base_phys_cost = year_physical['annual_flood_loss'].sum() if not year_physical.empty else 0
        else:
            # Otherwise use the total as a constant
            base_phys_cost = self.physical_df[
                'annual_flood_loss'].sum() if 'annual_flood_loss' in self.physical_df.columns else 0

        # Apply hazard shock
        phys_cost_sim = self._apply_hazard_shock(
            base_phys_cost, hazard_shock, year
        )

        # 3. Calculate net-zero penalty
        # Get net-zero targets for this year
        year_netzero = self.netzero_df[self.netzero_df['year'] == year]

        # Initialize penalty
        nz_penalty = 0

        for _, row_nz in year_netzero.iterrows():
            fac_id = row_nz['facility_id']
            target_em = row_nz['net_zero_target_emissions']

            # Get actual emissions from transition data
            df_trans_fac = self.transition_df[
                (self.transition_df['facility_id'] == fac_id) &
                (self.transition_df['year'] == year)
                ]

            if not df_trans_fac.empty:
                actual_em = df_trans_fac.iloc[0]['actual_emissions']
                emissions_gap = max(0, actual_em - target_em)

                # Get carbon price
                carbon_price_row = df_trans_fac.iloc[0]
                base_carbon_price = carbon_price_row['carbon_price'] if 'carbon_price' in carbon_price_row else 40.0

                # Apply shocks
                carbon_price = self._apply_carbon_price_shock(
                    base_carbon_price, carbon_shock, year
                )

                # Apply policy stringency shock to penalty
                policy_mult = self._apply_policy_shock(
                    emissions_gap, policy_shock, year
                )

                # Calculate penalty: gap * price * policy multiplier
                facility_penalty = emissions_gap * carbon_price * policy_mult
                nz_penalty += facility_penalty

        # Total cost for the year
        total_cost = trans_cost_sim + phys_cost_sim + nz_penalty

        return {
            'year': year,
            'transition_cost': trans_cost_sim,
            'physical_cost': phys_cost_sim,
            'netzero_penalty': nz_penalty,
            'total_cost': total_cost
        }

    def run_deep_monte_carlo(self,
                             n_sim: int = 1000,
                             percentile: float = 0.95,
                             save_details: bool = False) -> Tuple[float, np.ndarray, Optional[pd.DataFrame]]:
        """
        Run enhanced Monte Carlo simulation for Climate VaR.

        Args:
            n_sim: Number of simulations
            percentile: Percentile for VaR calculation
            save_details: Whether to save detailed results

        Returns:
            Tuple of (VaR value, distribution array, detailed DataFrame)
        """
        # Identify simulation years
        years = range(2025, 2051)

        # Generate correlated risk factors
        risk_factors_dict = self._generate_correlated_risk_factors(n_sim, years)

        # Initialize cost arrays
        total_costs_array = np.zeros(n_sim)

        # Detailed results container
        detailed_results = [] if save_details else None

        # Run simulations
        for i in range(n_sim):
            # For each simulation, accumulate discounted cost
            pv_cost = 0.0
            annual_costs = []

            for y in years:
                # Get risk factors for this year and simulation
                year_factors = risk_factors_dict[y][i]

                # Calculate costs for this year
                year_costs = self._calculate_year_costs(y, year_factors, i)
                annual_costs.append(year_costs)

                # Discount to present value
                years_from_base = y - 2024  # Assuming 2024 is base year
                year_pv = year_costs['total_cost'] / ((1 + self.discount_rate) ** years_from_base)
                pv_cost += year_pv

            # Store total PV cost for this simulation
            total_costs_array[i] = pv_cost

            # Store detailed results if requested
            if save_details:
                for cost_dict in annual_costs:
                    cost_dict['simulation'] = i
                    cost_dict['npv_total'] = pv_cost
                    detailed_results.append(cost_dict)

        # Calculate VaR
        sorted_costs = np.sort(total_costs_array)
        idx = int(np.ceil(percentile * n_sim)) - 1
        var_value = sorted_costs[idx]

        # Create detailed DataFrame if requested
        detailed_df = pd.DataFrame(detailed_results) if save_details else None

        return var_value, total_costs_array, detailed_df

    def analyze_var_components(self, n_sim: int = 1000, percentile: float = 0.95) -> Dict[str, float]:
        """
        Analyze the composition of Climate VaR by risk component.

        Args:
            n_sim: Number of simulations
            percentile: Percentile for VaR calculation

        Returns:
            Dictionary with VaR components
        """
        # Run full simulation with details
        _, _, detailed_df = self.run_deep_monte_carlo(n_sim, percentile, save_details=True)

        if detailed_df is None:
            return {}

        # Get the simulation IDs that are at or near the VaR threshold
        total_costs = detailed_df.groupby('simulation')['npv_total'].first()
        sorted_sims = total_costs.sort_values()
        var_idx = int(np.ceil(percentile * n_sim)) - 1
        var_sim_id = sorted_sims.index[var_idx]

        # Get data for the VaR simulation
        var_sim_data = detailed_df[detailed_df['simulation'] == var_sim_id]

        # Calculate total NPV by category
        transition_npv = 0
        physical_npv = 0
        netzero_npv = 0

        for _, row in var_sim_data.iterrows():
            year = row['year']
            years_from_base = year - 2024
            discount_factor = 1 / ((1 + self.discount_rate) ** years_from_base)

            transition_npv += row['transition_cost'] * discount_factor
            physical_npv += row['physical_cost'] * discount_factor
            netzero_npv += row['netzero_penalty'] * discount_factor

        total_npv = transition_npv + physical_npv + netzero_npv

        # Calculate percentages
        result = {
            'var_value': total_npv,
            'transition_cost': transition_npv,
            'transition_pct': transition_npv / total_npv * 100 if total_npv > 0 else 0,
            'physical_cost': physical_npv,
            'physical_pct': physical_npv / total_npv * 100 if total_npv > 0 else 0,
            'netzero_penalty': netzero_npv,
            'netzero_pct': netzero_npv / total_npv * 100 if total_npv > 0 else 0
        }

        return result

    def analyze_temporal_risk_profile(self, n_sim: int = 1000, percentile: float = 0.95) -> pd.DataFrame:
        """
        Analyze how risks distribute over time.

        Args:
            n_sim: Number of simulations
            percentile: Percentile for VaR calculation

        Returns:
            DataFrame with temporal risk profile
        """
        # Run full simulation with details
        _, _, detailed_df = self.run_deep_monte_carlo(n_sim, percentile, save_details=True)

        if detailed_df is None:
            return pd.DataFrame()

        # Get the simulation IDs that are at or near the VaR threshold
        total_costs = detailed_df.groupby('simulation')['npv_total'].first()
        sorted_sims = total_costs.sort_values()
        var_idx = int(np.ceil(percentile * n_sim)) - 1
        var_sim_id = sorted_sims.index[var_idx]

        # Get data for the VaR simulation
        var_sim_data = detailed_df[detailed_df['simulation'] == var_sim_id]

        # Calculate NPV for each year
        year_profile = []
        for _, row in var_sim_data.iterrows():
            year = row['year']
            years_from_base = year - 2024
            discount_factor = 1 / ((1 + self.discount_rate) ** years_from_base)

            year_profile.append({
                'year': year,
                'transition_cost': row['transition_cost'],
                'transition_npv': row['transition_cost'] * discount_factor,
                'physical_cost': row['physical_cost'],
                'physical_npv': row['physical_cost'] * discount_factor,
                'netzero_penalty': row['netzero_penalty'],
                'netzero_npv': row['netzero_penalty'] * discount_factor,
                'total_cost': row['total_cost'],
                'total_npv': row['total_cost'] * discount_factor,
                'discount_factor': discount_factor
            })

        return pd.DataFrame(year_profile)

    def plot_var_distribution(self, sim_dist: np.ndarray, var_95: float) -> plt.Figure:
        """
        Create a plot of the VaR distribution.

        Args:
            sim_dist: Distribution of simulation results
            var_95: 95th percentile VaR value

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Create histogram with KDE
        sns.histplot(sim_dist, kde=True, bins=50, ax=ax)

        # Add VaR line
        ax.axvline(var_95, color='r', linestyle='--',
                   label=f'VaR 95%: ${var_95:,.2f}')

        # Add mean and median
        mean_cost = np.mean(sim_dist)
        median_cost = np.median(sim_dist)
        ax.axvline(mean_cost, color='g', linestyle='--',
                   label=f'Mean: ${mean_cost:,.2f}')
        ax.axvline(median_cost, color='b', linestyle=':',
                   label=f'Median: ${median_cost:,.2f}')

        # Add labels
        ax.set_title('Climate VaR Distribution')
        ax.set_xlabel('Total NPV Cost (USD)')
        ax.set_ylabel('Frequency')
        ax.legend()

        # Add summary statistics textbox
        textstr = '\n'.join((
            f'VaR (95%): ${var_95:,.2f}',
            f'Mean: ${mean_cost:,.2f}',
            f'Median: ${median_cost:,.2f}',
            f'Min: ${np.min(sim_dist):,.2f}',
            f'Max: ${np.max(sim_dist):,.2f}',
            f'Std Dev: ${np.std(sim_dist):,.2f}'
        ))
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=props)

        return fig