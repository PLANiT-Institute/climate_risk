import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, List

# Import core modules
from util.transition_risk import TransitionRisk
from util.physical_risk import PhysicalRisk
from util.net_zero import NetZeroPathway, OptimalEmissionPathway
from util.climate_var import ClimateVaR
from util.report_generator import ReportGenerator

# Constants
DEFAULT_SCENARIOS = ["NDC", "Below2C", "NetZero"]
DEFAULT_DISCOUNT_RATE = 0.03


class ClimateRiskTool:
    """Main class for the Climate Financial Risk Tool."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Climate Risk Tool with configuration.

        Args:
            config: Dictionary with configuration parameters
        """
        self.config = config
        self.output_dir = Path(config.get("output_dir", "outputs"))
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Data containers
        self.facilities_df = None
        self.results = {
            "financial_risk": {},
            "net_zero": {}
        }

        # Load data
        self._load_data()

    def _load_data(self):
        """Load input data from files."""
        print("Loading input data...")
        try:
            self.facilities_df = pd.read_excel(self.config["facilities"])
            print(f"Loaded {len(self.facilities_df)} facilities.")
        except Exception as e:
            print(f"Error loading facilities data: {e}")
            raise

    def run_financial_risk_analysis(self, scenarios: List[str] = None):
        """
        Run the financial risk analysis for transition and physical risks.

        Args:
            scenarios: List of scenarios to analyze (default: DEFAULT_SCENARIOS)
        """
        if scenarios is None:
            scenarios = DEFAULT_SCENARIOS

        print(f"Running financial risk analysis for scenarios: {scenarios}")

        # Container for all scenario results
        transition_results = {}
        physical_results = {}

        for scenario in scenarios:
            print(f"Analyzing scenario: {scenario}")

            # 1. Transition Risk Analysis
            try:
                tr = TransitionRisk(
                    self.config["facilities"],
                    self.config["carbon_prices"],
                    scenario=scenario
                )
                transition_df = tr.run()
                transition_results[scenario] = transition_df

                # Save individual scenario results
                output_path = self.output_dir / f"transition_risk_{scenario}.csv"
                transition_df.to_csv(output_path, index=False)
                print(f"Saved transition risk results to {output_path}")
            except Exception as e:
                print(f"Error in transition risk analysis for {scenario}: {e}")
                continue

            # 2. Physical Risk Analysis (same for all scenarios for now)
            if scenario == scenarios[0]:  # Only run once
                try:
                    pr = PhysicalRisk(self.facilities_df, self.config["hazard"])
                    physical_df = pr.run()
                    physical_results["base"] = physical_df

                    # Save physical risk results
                    output_path = self.output_dir / "physical_risk_results.csv"
                    physical_df.to_csv(output_path, index=False)
                    print(f"Saved physical risk results to {output_path}")
                except Exception as e:
                    print(f"Error in physical risk analysis: {e}")

        # Store results
        self.results["financial_risk"] = {
            "transition": transition_results,
            "physical": physical_results
        }

        # Generate summary
        self._generate_financial_risk_summary()

    def run_net_zero_analysis(self, approaches: List[str] = None):
        """
        Run the net-zero pathway and Climate VaR analysis.

        Args:
            approaches: List of net-zero approaches to analyze (e.g., ['linear', 'optimal'])
        """
        if approaches is None:
            approaches = ["linear", "optimal"]

        print(f"Running net-zero analysis with approaches: {approaches}")

        pathway_results = {}

        for approach in approaches:
            print(f"Analyzing net-zero approach: {approach}")

            try:
                # Basic approach (linear or absolute)
                if approach in ["linear", "absolute"]:
                    nz = NetZeroPathway(self.config["facilities"], approach=approach)
                    netzero_df = nz.run()
                # Advanced cost-optimized approach
                elif approach == "optimal":
                    # This would be a new class that considers cost-effectiveness
                    nz = OptimalEmissionPathway(
                        self.config["facilities"],
                        self.config["carbon_prices"],
                        self.config.get("abatement_costs", "data/abatement_costs.xlsx")
                    )
                    netzero_df = nz.run()
                else:
                    print(f"Unknown approach: {approach}, skipping")
                    continue

                pathway_results[approach] = netzero_df

                # Save pathway results
                output_path = self.output_dir / f"netzero_pathway_{approach}.csv"
                netzero_df.to_csv(output_path, index=False)
                print(f"Saved net-zero pathway results to {output_path}")

            except Exception as e:
                print(f"Error in net-zero analysis for approach {approach}: {e}")
                continue

        # Store results
        self.results["net_zero"]["pathways"] = pathway_results

        # Run Climate VaR if we have both risk and pathway results
        if (self.results["financial_risk"].get("transition") and
                self.results["financial_risk"].get("physical") and
                pathway_results):
            self._run_climate_var_analysis()

    def _run_climate_var_analysis(self):
        """Run Climate VaR analysis using financial risk and net-zero results."""
        print("Running Climate VaR analysis...")

        # Use the first scenario for transition and physical risk
        transition_df = next(iter(self.results["financial_risk"]["transition"].values()))
        physical_df = next(iter(self.results["financial_risk"]["physical"].values()))

        # Use results from each pathway approach
        for approach, netzero_df in self.results["net_zero"]["pathways"].items():
            try:
                # Run Climate VaR
                cvar = ClimateVaR(
                    transition_df,
                    physical_df,
                    netzero_df,
                    discount_rate=self.config.get("discount_rate", DEFAULT_DISCOUNT_RATE)
                )

                # Run standard Monte Carlo
                var_95, sim_dist = cvar.run_deep_monte_carlo(
                    n_sim=self.config.get("n_simulations", 1000),
                    percentile=0.95
                )

                # Store results
                self.results["net_zero"]["climate_var"] = {
                    "approach": approach,
                    "var_95": var_95,
                    "distribution": sim_dist
                }

                # Save distribution
                df_sims = pd.DataFrame({"simulation_total_cost": sim_dist})
                output_path = self.output_dir / f"climate_var_{approach}_distribution.csv"
                df_sims.to_csv(output_path, index=False)
                print(f"Climate VaR (95%): {var_95}")
                print(f"Saved Climate VaR distribution to {output_path}")

                # Visualize
                self._visualize_climate_var(approach, var_95, sim_dist)

            except Exception as e:
                print(f"Error in Climate VaR analysis for {approach}: {e}")

    def _visualize_climate_var(self, approach: str, var_95: float, sim_dist: np.ndarray):
        """
        Create visualization for Climate VaR.

        Args:
            approach: Net-zero approach used
            var_95: 95th percentile VaR value
            sim_dist: Distribution of simulation results
        """
        plt.figure(figsize=(10, 6))
        sns.histplot(sim_dist, kde=True, bins=50)
        plt.title(f"Climate VaR Distribution ({approach} approach)")
        plt.xlabel("Total NPV Cost (USD)")
        plt.ylabel("Frequency")
        plt.axvline(var_95, color='r', linestyle='--',
                    label=f'VaR 95%: ${var_95:,.2f}')
        plt.legend()

        # Add mean and median
        mean_cost = np.mean(sim_dist)
        median_cost = np.median(sim_dist)
        plt.axvline(mean_cost, color='g', linestyle='--',
                    label=f'Mean: ${mean_cost:,.2f}')
        plt.axvline(median_cost, color='b', linestyle=':',
                    label=f'Median: ${median_cost:,.2f}')
        plt.legend()

        output_path = self.output_dir / f"climate_var_{approach}_hist.png"
        plt.savefig(output_path, dpi=300)
        plt.close()

    def _generate_financial_risk_summary(self):
        """Generate summary statistics and visualizations for financial risk."""
        if not self.results["financial_risk"].get("transition"):
            print("No transition risk results to summarize")
            return

        # Create summary DataFrame
        summary_rows = []

        for scenario, trans_df in self.results["financial_risk"]["transition"].items():
            # Get yearly costs
            yearly_costs = trans_df.groupby('year')['ets_cost'].sum()

            # Calculate NPV of costs
            discount_rate = self.config.get("discount_rate", DEFAULT_DISCOUNT_RATE)
            base_year = 2024

            npv_cost = 0
            for year, cost in yearly_costs.items():
                if year > base_year:
                    npv_cost += cost / ((1 + discount_rate) ** (year - base_year))

            # Add to summary
            summary_rows.append({
                "scenario": scenario,
                "total_nominal_cost": yearly_costs.sum(),
                "npv_cost": npv_cost,
                "avg_annual_cost": yearly_costs.mean(),
                "max_annual_cost": yearly_costs.max(),
                "max_cost_year": yearly_costs.idxmax()
            })

        # Create summary DataFrame
        summary_df = pd.DataFrame(summary_rows)

        # Save summary
        output_path = self.output_dir / "financial_risk_summary.csv"
        summary_df.to_csv(output_path, index=False)
        print(f"Saved financial risk summary to {output_path}")

        # Visualize comparison
        self._visualize_scenario_comparison(summary_df)

    def _visualize_scenario_comparison(self, summary_df: pd.DataFrame):
        """
        Create visualization comparing scenarios.

        Args:
            summary_df: DataFrame with scenario summaries
        """
        plt.figure(figsize=(10, 6))
        sns.barplot(x="scenario", y="npv_cost", data=summary_df)
        plt.title("NPV of Transition Costs by Scenario")
        plt.xlabel("Scenario")
        plt.ylabel("NPV Cost (USD)")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()

        output_path = self.output_dir / "scenario_comparison.png"
        plt.savefig(output_path, dpi=300)
        plt.close()

    def generate_reports(self):
        """Generate comprehensive reports for the analysis."""
        print("Generating reports...")

        # Initialize report generator
        report_gen = ReportGenerator(self.results, self.output_dir)

        # Generate reports
        report_gen.generate_financial_risk_report()
        report_gen.generate_net_zero_report()

        print("Reports generated.")


def main():
    """Main entry point for the Climate Financial Risk Tool."""
    parser = argparse.ArgumentParser(description="Climate Financial Risk Tool")
    parser.add_argument("--facilities", default="data/input_facilities.xlsx",
                        help="Path to facilities Excel")
    parser.add_argument("--carbon_prices", default="data/carbon_prices.xlsx",
                        help="Path to carbon prices Excel")
    parser.add_argument("--hazard", default="data/flood_hazard.nc",
                        help="Path to flood hazard netCDF file")
    parser.add_argument("--abatement_costs", default="data/abatement_costs.xlsx",
                        help="Path to abatement costs Excel (for optimal pathway)")
    parser.add_argument("--output_dir", default="outputs",
                        help="Output directory")
    parser.add_argument("--scenarios", nargs="+", default=DEFAULT_SCENARIOS,
                        help="Scenarios to analyze")
    parser.add_argument("--approaches", nargs="+", default=["linear", "optimal"],
                        help="Net-zero approaches to analyze")
    parser.add_argument("--discount_rate", type=float, default=DEFAULT_DISCOUNT_RATE,
                        help="Discount rate for NPV calculations")
    parser.add_argument("--n_simulations", type=int, default=1000,
                        help="Number of Monte Carlo simulations")

    args = parser.parse_args()

    # Create configuration dictionary
    config = {
        "facilities": args.facilities,
        "carbon_prices": args.carbon_prices,
        "hazard": args.hazard,
        "abatement_costs": args.abatement_costs,
        "output_dir": args.output_dir,
        "discount_rate": args.discount_rate,
        "n_simulations": args.n_simulations
    }

    # Initialize and run the tool
    tool = ClimateRiskTool(config)

    # Run analysis
    tool.run_financial_risk_analysis(scenarios=args.scenarios)
    tool.run_net_zero_analysis(approaches=args.approaches)

    # Generate reports
    tool.generate_reports()

    print("Analysis complete.")


if __name__ == "__main__":
    main()