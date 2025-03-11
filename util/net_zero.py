import pandas as pd
import numpy as np
import pulp
from typing import Dict, List, Tuple, Optional


class OptimalEmissionPathway:
    """
    Calculates cost-optimal emission reduction pathways using linear programming.

    This class determines the most cost-effective pathway to reach net-zero
    by considering both carbon prices and abatement costs over time.
    """

    def __init__(self,
                 facilities_xlsx: str,
                 carbon_price_xlsx: str,
                 abatement_costs_xlsx: str,
                 target_year: int = 2050,
                 base_year: int = 2024,
                 scenario: str = "NDC"):
        """
        Initialize the optimal emission pathway calculator.

        Args:
            facilities_xlsx: Path to Excel with facility data.
            carbon_price_xlsx: Path to Excel with carbon price scenarios.
            abatement_costs_xlsx: Path to Excel with marginal abatement cost curves.
            target_year: Year to reach net-zero (default: 2050).
            base_year: Base year for emissions (default: 2024).
            scenario: Carbon price scenario to use (default: "NDC").
        """
        self.facilities_xlsx = facilities_xlsx
        self.carbon_price_xlsx = carbon_price_xlsx
        self.abatement_costs_xlsx = abatement_costs_xlsx
        self.target_year = target_year
        self.base_year = base_year
        self.scenario = scenario

        # Data containers
        self.df_fac = None
        self.df_prices = None
        self.df_abatement = None
        self.optimal_pathway = None

        # Load data
        self.load_data()

    def load_data(self):
        """Load facility, carbon price, and abatement cost data."""
        # Load facilities
        self.df_fac = pd.read_excel(self.facilities_xlsx)

        # Load carbon prices for the specified scenario
        df_prices_raw = pd.read_excel(self.carbon_price_xlsx)
        self.df_prices = df_prices_raw[df_prices_raw['scenario'] == self.scenario].copy()

        # Load abatement costs
        self.df_abatement = pd.read_excel(self.abatement_costs_xlsx)

    def _get_abatement_options(self, facility_id: str) -> pd.DataFrame:
        """
        Get abatement options for a specific facility.

        Args:
            facility_id: Facility ID to get options for.

        Returns:
            DataFrame with abatement options.
        """
        return self.df_abatement[self.df_abatement['facility_id'] == facility_id].copy()

    def _optimize_facility_pathway(self,
                                   facility_id: str,
                                   baseline_emissions: float) -> pd.DataFrame:
        """
        Optimize emission reduction pathway for a single facility.

        Args:
            facility_id: Facility ID to optimize for.
            baseline_emissions: Baseline emissions for the facility.

        Returns:
            DataFrame with optimized pathway by year.
        """
        # Get abatement options for this facility
        abatement_options = self._get_abatement_options(facility_id)

        # If no specific abatement options, use default
        if abatement_options.empty:
            print(f"Warning: No specific abatement options for {facility_id}. Using defaults.")
            # Create generic abatement options with different cost bands
            abatement_options = pd.DataFrame({
                'facility_id': [facility_id] * 5,
                'option_id': [f"generic_{i}" for i in range(1, 6)],
                'max_reduction_pct': [0.2, 0.4, 0.6, 0.8, 1.0],
                'cost_per_tCO2e': [20, 50, 80, 120, 200]
            })

        # Get years and carbon prices
        years = range(self.base_year + 1, self.target_year + 1)
        carbon_prices = {}
        for _, row in self.df_prices.iterrows():
            if row['year'] in years:
                carbon_prices[row['year']] = row['price_usd_per_tCO2e']

        # Fill in missing prices with interpolation
        all_years = list(years)
        all_years.sort()
        for year in all_years:
            if year not in carbon_prices:
                # Simple linear interpolation
                prev_years = [y for y in carbon_prices.keys() if y < year]
                next_years = [y for y in carbon_prices.keys() if y > year]

                if prev_years and next_years:
                    prev_year = max(prev_years)
                    next_year = min(next_years)
                    prev_price = carbon_prices[prev_year]
                    next_price = carbon_prices[next_year]

                    # Linear interpolation
                    carbon_prices[year] = prev_price + (next_price - prev_price) * \
                                          (year - prev_year) / (next_year - prev_year)
                elif prev_years:
                    carbon_prices[year] = carbon_prices[max(prev_years)]
                elif next_years:
                    carbon_prices[year] = carbon_prices[min(next_years)]
                else:
                    carbon_prices[year] = 0  # Fallback

        # Create optimization model
        model = pulp.LpProblem(f"OptimalPathway_{facility_id}", pulp.LpMinimize)

        # Decision variables: How much to reduce in each year with each option
        reduction_vars = {}
        for year in years:
            for i, option in abatement_options.iterrows():
                var_name = f"reduce_{year}_{option['option_id']}"
                # Decision variable is the amount (in tCO2e) to reduce using this option
                reduction_vars[(year, option['option_id'])] = pulp.LpVariable(
                    var_name,
                    lowBound=0,
                    upBound=baseline_emissions * option['max_reduction_pct']
                )

        # Remaining emissions variables
        remaining_emissions = {}
        for year in years:
            var_name = f"remaining_{year}"
            remaining_emissions[year] = pulp.LpVariable(var_name, lowBound=0)

        # Objective function: Minimize total cost
        total_cost = 0
        for year in years:
            # Abatement costs
            for i, option in abatement_options.iterrows():
                abatement_cost = option['cost_per_tCO2e'] * reduction_vars[(year, option['option_id'])]
                total_cost += abatement_cost

            # Carbon costs for remaining emissions
            carbon_cost = carbon_prices[year] * remaining_emissions[year]
            total_cost += carbon_cost

        model += total_cost

        # Constraints

        # 1. Emissions balance for each year
        for year in years:
            # Sum of all reductions for this year
            total_reduction = 0
            for i, option in abatement_options.iterrows():
                total_reduction += reduction_vars[(year, option['option_id'])]

            # Remaining emissions = baseline - reductions
            model += remaining_emissions[year] == baseline_emissions - total_reduction

        # 2. Linear progression to net-zero
        for year in years:
            # Calculate allowed emissions for this year based on linear reduction
            years_from_base = year - self.base_year
            total_years = self.target_year - self.base_year
            max_allowed = baseline_emissions * (1 - years_from_base / total_years)

            # Remaining emissions must be less than or equal to max allowed
            model += remaining_emissions[year] <= max_allowed

        # Solve the model
        model.solve(pulp.PULP_CBC_CMD(msg=False))

        # Check solution status
        if pulp.LpStatus[model.status] != 'Optimal':
            print(f"Warning: No optimal solution found for {facility_id}. Status: {pulp.LpStatus[model.status]}")
            # Return a fallback linear reduction
            results = []
            for year in years:
                years_from_base = year - self.base_year
                total_years = self.target_year - self.base_year
                target_em = baseline_emissions * (1 - years_from_base / total_years)
                results.append({
                    'facility_id': facility_id,
                    'year': year,
                    'net_zero_target_emissions': target_em,
                    'is_optimal': False,
                    'abatement_cost': 0,
                    'carbon_cost': 0,
                    'total_cost': 0
                })
            return pd.DataFrame(results)

        # Extract results
        results = []
        for year in years:
            # Get remaining emissions
            remaining = remaining_emissions[year].value()

            # Calculate costs
            abatement_cost = 0
            for i, option in abatement_options.iterrows():
                reduction = reduction_vars[(year, option['option_id'])].value()
                abatement_cost += option['cost_per_tCO2e'] * reduction

            carbon_cost = carbon_prices[year] * remaining
            total_cost = abatement_cost + carbon_cost

            results.append({
                'facility_id': facility_id,
                'year': year,
                'net_zero_target_emissions': remaining,
                'is_optimal': True,
                'abatement_cost': abatement_cost,
                'carbon_cost': carbon_cost,
                'total_cost': total_cost
            })

        return pd.DataFrame(results)

    def calculate_optimal_pathway(self) -> pd.DataFrame:
        """
        Calculate optimal emission reduction pathway for all facilities.

        Returns:
            DataFrame with optimal pathway for all facilities.
        """
        all_results = []

        for _, row in self.df_fac.iterrows():
            facility_id = row['facility_id']
            baseline_emissions = row['baseline_emissions_2024']

            # Optimize for this facility
            facility_results = self._optimize_facility_pathway(facility_id, baseline_emissions)
            all_results.append(facility_results)

        # Combine results
        self.optimal_pathway = pd.concat(all_results, ignore_index=True)
        return self.optimal_pathway

    def run(self) -> pd.DataFrame:
        """
        Run the optimal pathway calculation.

        Returns:
            DataFrame with optimal pathway for all facilities.
        """
        return self.calculate_optimal_pathway()