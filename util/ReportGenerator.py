import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Any, List
import json


class ReportGenerator:
    """
    Generates comprehensive reports for climate financial risk analysis.
    """

    def __init__(self, results: Dict[str, Any], output_dir: Path):
        """
        Initialize the report generator.

        Args:
            results: Dictionary with analysis results
            output_dir: Output directory for reports
        """
        self.results = results
        self.output_dir = Path(output_dir)
        self.report_dir = self.output_dir / "reports"
        self.report_dir.mkdir(exist_ok=True, parents=True)

    def generate_financial_risk_report(self):
        """
        Generate a comprehensive report on climate financial risks.

        This covers transition and physical risks.
        """
        if not self.results.get("financial_risk"):
            print("No financial risk results to report")
            return

        # Create report directory
        risk_dir = self.report_dir / "financial_risk"
        risk_dir.mkdir(exist_ok=True, parents=True)

        # Create summary information
        summary = self._generate_financial_risk_summary()

        # Save summary as JSON
        with open(risk_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        # Generate visualizations
        self._create_financial_risk_visualizations(risk_dir)

        # Create markdown report
        self._create_financial_risk_markdown(risk_dir, summary)

        print(f"Financial risk report generated in {risk_dir}")

    def _generate_financial_risk_summary(self) -> Dict[str, Any]:
        """
        Generate summary statistics for financial risk.

        Returns:
            Dictionary with summary information
        """
        summary = {
            "transition_risk": {},
            "physical_risk": {}
        }

        # Transition risk summary
        for scenario, trans_df in self.results["financial_risk"].get("transition", {}).items():
            # Get yearly costs
            yearly_costs = trans_df.groupby('year')['ets_cost'].sum()

            # Summary stats
            summary["transition_risk"][scenario] = {
                "total_cost": yearly_costs.sum(),
                "average_annual_cost": yearly_costs.mean(),
                "max_annual_cost": yearly_costs.max(),
                "max_cost_year": int(yearly_costs.idxmax()),
                "yearly_costs": yearly_costs.to_dict()
            }

        # Physical risk summary
        for scenario, phys_df in self.results["financial_risk"].get("physical", {}).items():
            if "annual_flood_loss" in phys_df.columns:
                total_loss = phys_df["annual_flood_loss"].sum()
                avg_loss = phys_df["annual_flood_loss"].mean()
                max_loss = phys_df["annual_flood_loss"].max()

                summary["physical_risk"][scenario] = {
                    "total_annual_loss": total_loss,
                    "average_facility_loss": avg_loss,
                    "max_facility_loss": max_loss
                }

        return summary

    def _create_financial_risk_visualizations(self, output_dir: Path):
        """
        Create visualizations for financial risk.

        Args:
            output_dir: Directory to save visualizations
        """
        # Create transition risk charts
        if self.results["financial_risk"].get("transition"):
            # Yearly costs by scenario
            plt.figure(figsize=(12, 6))

            for scenario, trans_df in self.results["financial_risk"]["transition"].items():
                yearly_costs = trans_df.groupby('year')['ets_cost'].sum()
                plt.plot(yearly_costs.index, yearly_costs.values, marker='o', label=scenario)

            plt.title("Annual Transition Costs by Scenario")
            plt.xlabel("Year")
            plt.ylabel("Cost (USD)")
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()

            plt.savefig(output_dir / "transition_costs_by_scenario.png", dpi=300)
            plt.close()

            # Facility-level costs (for first scenario)
            scenario = next(iter(self.results["financial_risk"]["transition"]))
            trans_df = self.results["financial_risk"]["transition"][scenario]

            facility_costs = trans_df.groupby('facility_id')['ets_cost'].sum().sort_values(ascending=False)

            plt.figure(figsize=(12, 6))
            facility_costs.head(10).plot(kind='bar')
            plt.title(f"Top 10 Facilities by Transition Cost ({scenario} scenario)")
            plt.xlabel("Facility ID")
            plt.ylabel("Total Cost (USD)")
            plt.grid(True, axis='y', alpha=0.3)
            plt.tight_layout()

            plt.savefig(output_dir / "top_facilities_transition_cost.png", dpi=300)
            plt.close()

        # Create physical risk charts
        if self.results["financial_risk"].get("physical"):
            scenario = next(iter(self.results["financial_risk"]["physical"]))
            phys_df = self.results["financial_risk"]["physical"][scenario]

            if "annual_flood_loss" in phys_df.columns:
                # Facility-level physical risk
                facility_losses = phys_df.sort_values("annual_flood_loss", ascending=False)

                plt.figure(figsize=(12, 6))
                facility_losses.head(10).plot(x="facility_id", y="annual_flood_loss", kind='bar')
                plt.title("Top 10 Facilities by Physical Risk (Annual Expected Loss)")
                plt.xlabel("Facility ID")
                plt.ylabel("Annual Expected Loss (USD)")
                plt.grid(True, axis='y', alpha=0.3)
                plt.tight_layout()

                plt.savefig(output_dir / "top_facilities_physical_risk.png", dpi=300)
                plt.close()

    def _create_financial_risk_markdown(self, output_dir: Path, summary: Dict[str, Any]):
        """
        Create markdown report for financial risk.

        Args:
            output_dir: Directory to save report
            summary: Summary information dictionary
        """
        report = []

        # Header
        report.append("# Climate Financial Risk Report\n")
        report.append("## Executive Summary\n")

        # Transition risk summary
        if summary.get("transition_risk"):
            report.append("### Transition Risk\n")

            # Table header
            report.append("| Scenario | Total Cost ($) | Avg Annual Cost ($) | Max Annual Cost ($) | Max Cost Year |")
            report.append("|----------|---------------|---------------------|---------------------|--------------|")

            for scenario, stats in summary["transition_risk"].items():
                report.append(
                    f"| {scenario} | {stats['total_cost']:,.2f} | {stats['average_annual_cost']:,.2f} | {stats['max_annual_cost']:,.2f} | {stats['max_cost_year']} |")

            report.append("\n")

        # Physical risk summary
        if summary.get("physical_risk"):
            report.append("### Physical Risk\n")

            # Table header
            report.append("| Scenario | Total Annual Loss ($) | Avg Facility Loss ($) | Max Facility Loss ($) |")
            report.append("|----------|---------------------|----------------------|----------------------|")

            for scenario, stats in summary["physical_risk"].items():
                report.append(
                    f"| {scenario} | {stats['total_annual_loss']:,.2f} | {stats['average_facility_loss']:,.2f} | {stats['max_facility_loss']:,.2f} |")

            report.append("\n")

        # Visualizations
        report.append("## Key Visualizations\n")

        report.append("### Transition Risk Over Time\n")
        report.append("![Transition Costs by Scenario](transition_costs_by_scenario.png)\n")

        report.append("### Top Facilities by Transition Risk\n")
        report.append("![Top Facilities by Transition Cost](top_facilities_transition_cost.png)\n")

        report.append("### Top Facilities by Physical Risk\n")
        report.append("![Top Facilities by Physical Risk](top_facilities_physical_risk.png)\n")

        # Detailed analysis
        report.append("## Detailed Analysis\n")

        # Transition risk details
        if summary.get("transition_risk"):
            report.append("### Transition Risk Detailed Analysis\n")

            for scenario, stats in summary["transition_risk"].items():
                report.append(f"#### {scenario} Scenario\n")
                report.append(f"- Total cost across all facilities: ${stats['total_cost']:,.2f}")
                report.append(f"- Average annual cost: ${stats['average_annual_cost']:,.2f}")
                report.append(f"- Highest annual cost: ${stats['max_annual_cost']:,.2f} in {stats['max_cost_year']}")
                report.append("\n")

                # Cost evolution
                report.append("##### Cost Evolution\n")
                report.append("| Year | Annual Cost ($) |")
                report.append("|------|----------------|")

                for year, cost in sorted(stats["yearly_costs"].items()):
                    report.append(f"| {year} | {cost:,.2f} |")

                report.append("\n")

        # Physical risk details
        if summary.get("physical_risk"):
            report.append("### Physical Risk Detailed Analysis\n")

            for scenario, stats in summary["physical_risk"].items():
                report.append(f"#### {scenario} Scenario\n")
                report.append(f"- Total annual expected loss: ${stats['total_annual_loss']:,.2f}")
                report.append(f"- Average loss per facility: ${stats['average_facility_loss']:,.2f}")
                report.append(f"- Maximum facility loss: ${stats['max_facility_loss']:,.2f}")
                report.append("\n")

        # Write report
        with open(output_dir / "financial_risk_report.md", "w") as f:
            f.write("\n".join(report))

    def generate_net_zero_report(self):
        """
        Generate a comprehensive report on net-zero pathways and Climate VaR.
        """
        if not self.results.get("net_zero"):
            print("No net-zero results to report")
            return

        # Create report directory
        nz_dir = self.report_dir / "net_zero"
        nz_dir.mkdir(exist_ok=True, parents=True)

        # Create summary information
        summary = self._generate_net_zero_summary()

        # Save summary as JSON
        with open(nz_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        # Generate visualizations
        self._create_net_zero_visualizations(nz_dir)

        # Create markdown report
        self._create_net_zero_markdown(nz_dir, summary)

        print(f"Net-zero report generated in {nz_dir}")

    def _generate_net_zero_summary(self) -> Dict[str, Any]:
        """
        Generate summary statistics for net-zero pathways and Climate VaR.

        Returns:
            Dictionary with summary information
        """
        summary = {
            "pathways": {},
            "climate_var": {}
        }

        # Pathway summary
        for approach, nz_df in self.results["net_zero"].get("pathways", {}).items():
            # Get yearly targets
            yearly_targets = nz_df.groupby('year')['net_zero_target_emissions'].sum()

            # Calculate reduction over time
            first_year_emissions = yearly_targets.iloc[0] if not yearly_targets.empty else 0
            last_year_emissions = yearly_targets.iloc[-1] if not yearly_targets.empty else 0

            total_reduction = first_year_emissions - last_year_emissions
            percent_reduction = (total_reduction / first_year_emissions * 100) if first_year_emissions > 0 else 0

            # Summary stats
            summary["pathways"][approach] = {
                "first_year_emissions": float(first_year_emissions),
                "last_year_emissions": float(last_year_emissions),
                "total_reduction": float(total_reduction),
                "percent_reduction": float(percent_reduction),
                "yearly_targets": yearly_targets.to_dict()
            }

            # Add cost data if available
            if "total_cost" in nz_df.columns:
                yearly_costs = nz_df.groupby('year')['total_cost'].sum()
                total_cost = yearly_costs.sum()

                summary["pathways"][approach].update({
                    "total_cost": float(total_cost),
                    "yearly_costs": yearly_costs.to_dict()
                })

        # Climate VaR summary
        climate_var = self.results["net_zero"].get("climate_var", {})
        if climate_var:
            approach = climate_var.get("approach", "unknown")
            var_95 = climate_var.get("var_95", 0)

            # Basic stats on distribution
            distribution = climate_var.get("distribution", np.array([]))
            if len(distribution) > 0:
                summary["climate_var"] = {
                    "approach": approach,
                    "var_95": float(var_95),
                    "mean": float(np.mean(distribution)),
                    "median": float(np.median(distribution)),
                    "std_dev": float(np.std(distribution)),
                    "min": float(np.min(distribution)),
                    "max": float(np.max(distribution))
                }

        return summary

    def _create_net_zero_visualizations(self, output_dir: Path):
        """
        Create visualizations for net-zero pathways and Climate VaR.

        Args:
            output_dir: Directory to save visualizations
        """
        # Create pathway charts
        if self.results["net_zero"].get("pathways"):
            # Emissions pathway by approach
            plt.figure(figsize=(12, 6))

            for approach, nz_df in self.results["net_zero"]["pathways"].items():
                yearly_targets = nz_df.groupby('year')['net_zero_target_emissions'].sum()
                plt.plot(yearly_targets.index, yearly_targets.values, marker='o', label=approach)

            plt.title("Net-Zero Emission Pathways by Approach")
            plt.xlabel("Year")
            plt.ylabel("Total Emissions (tCO2e)")
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()

            plt.savefig(output_dir / "emission_pathways.png", dpi=300)
            plt.close()

            # Cost comparison if available
            has_costs = any("total_cost" in nz_df.columns for nz_df in self.results["net_zero"]["pathways"].values())

            if has_costs:
                plt.figure(figsize=(12, 6))

                for approach, nz_df in self.results["net_zero"]["pathways"].items():
                    if "total_cost" in nz_df.columns:
                        yearly_costs = nz_df.groupby('year')['total_cost'].sum()
                        plt.plot(yearly_costs.index, yearly_costs.values, marker='o', label=approach)

                plt.title("Net-Zero Pathway Costs by Approach")
                plt.xlabel("Year")
                plt.ylabel("Annual Cost (USD)")
                plt.grid(True, alpha=0.3)
                plt.legend()
                plt.tight_layout()

                plt.savefig(output_dir / "pathway_costs.png", dpi=300)
                plt.close()

        # Create Climate VaR visualization
        climate_var = self.results["net_zero"].get("climate_var", {})
        if climate_var:
            distribution = climate_var.get("distribution", np.array([]))
            var_95 = climate_var.get("var_95", 0)

            if len(distribution) > 0:
                plt.figure(figsize=(12, 6))

                # Histogram with kernel density
                sns.histplot(distribution, kde=True, bins=50)

                # Add lines for VaR, mean, median
                mean_val = np.mean(distribution)
                median_val = np.median(distribution)

                plt.axvline(var_95, color='r', linestyle='--',
                            label=f'VaR 95%: ${var_95:,.2f}')
                plt.axvline(mean_val, color='g', linestyle='--',
                            label=f'Mean: ${mean_val:,.2f}')
                plt.axvline(median_val, color='b', linestyle=':',
                            label=f'Median: ${median_val:,.2f}')

                plt.title("Climate Value at Risk Distribution")
                plt.xlabel("Total NPV Cost (USD)")
                plt.ylabel("Frequency")
                plt.grid(True, alpha=0.3)
                plt.legend()
                plt.tight_layout()

                plt.savefig(output_dir / "climate_var_distribution.png", dpi=300)
                plt.close()

    def _create_net_zero_markdown(self, output_dir: Path, summary: Dict[str, Any]):
        """
        Create markdown report for net-zero pathways and Climate VaR.

        Args:
            output_dir: Directory to save report
            summary: Summary information dictionary
        """
        report = []

        # Header
        report.append("# Net-Zero Pathway and Climate Value at Risk Report\n")
        report.append("## Executive Summary\n")

        # Pathway summary
        if summary.get("pathways"):
            report.append("### Net-Zero Pathways\n")

            # Table header
            has_costs = any("total_cost" in pathway for pathway in summary["pathways"].values())

            if has_costs:
                report.append(
                    "| Approach | Initial Emissions (tCO2e) | Final Emissions (tCO2e) | Reduction (%) | Total Cost ($) |")
                report.append(
                    "|----------|---------------------------|-------------------------|--------------|---------------|")

                for approach, stats in summary["pathways"].items():
                    report.append(
                        f"| {approach} | {stats['first_year_emissions']:,.2f} | {stats['last_year_emissions']:,.2f} | {stats['percent_reduction']:,.1f}% | {stats.get('total_cost', 0):,.2f} |")
            else:
                report.append("| Approach | Initial Emissions (tCO2e) | Final Emissions (tCO2e) | Reduction (%) |")
                report.append("|----------|---------------------------|-------------------------|--------------|")

                for approach, stats in summary["pathways"].items():
                    report.append(
                        f"| {approach} | {stats['first_year_emissions']:,.2f} | {stats['last_year_emissions']:,.2f} | {stats['percent_reduction']:,.1f}% |")

            report.append("\n")

        # Climate VaR summary
        if summary.get("climate_var"):
            report.append("### Climate Value at Risk\n")

            stats = summary["climate_var"]

            report.append(f"- Approach: {stats['approach']}")
            report.append(f"- VaR (95%): ${stats['var_95']:,.2f}")
            report.append(f"- Mean cost: ${stats['mean']:,.2f}")
            report.append(f"- Median cost: ${stats['median']:,.2f}")
            report.append(f"- Standard deviation: ${stats['std_dev']:,.2f}")
            report.append(f"- Range: ${stats['min']:,.2f} to ${stats['max']:,.2f}")

            report.append("\n")

        # Visualizations
        report.append("## Key Visualizations\n")

        report.append("### Emission Reduction Pathways\n")
        report.append("![Emission Pathways by Approach](emission_pathways.png)\n")

        if any("total_cost" in pathway for pathway in summary.get("pathways", {}).values()):
            report.append("### Pathway Costs\n")
            report.append("![Pathway Costs by Approach](pathway_costs.png)\n")

        if summary.get("climate_var"):
            report.append("### Climate Value at Risk Distribution\n")
            report.append("![Climate VaR Distribution](climate_var_distribution.png)\n")

        # Detailed analysis
        report.append("## Detailed Analysis\n")

        # Pathway details
        if summary.get("pathways"):
            report.append("### Net-Zero Pathway Detailed Analysis\n")

            for approach, stats in summary["pathways"].items():
                report.append(f"#### {approach} Approach\n")
                report.append(f"- Initial emissions (2025): {stats['first_year_emissions']:,.2f} tCO2e")
                report.append(f"- Final emissions (2050): {stats['last_year_emissions']:,.2f} tCO2e")
                report.append(
                    f"- Total reduction: {stats['total_reduction']:,.2f} tCO2e ({stats['percent_reduction']:,.1f}%)")

                if "total_cost" in stats:
                    report.append(f"- Total pathway cost: ${stats['total_cost']:,.2f}")

                report.append("\n")

                # Emissions trajectory
                report.append("##### Emissions Trajectory\n")
                report.append("| Year | Target Emissions (tCO2e) |")
                report.append("|------|--------------------------|")

                for year, emissions in sorted(stats["yearly_targets"].items()):
                    report.append(f"| {year} | {emissions:,.2f} |")

                report.append("\n")

                # Cost trajectory if available
                if "yearly_costs" in stats:
                    report.append("##### Cost Trajectory\n")
                    report.append("| Year | Annual Cost ($) |")
                    report.append("|------|----------------|")

                    for year, cost in sorted(stats["yearly_costs"].items()):
                        report.append(f"| {year} | {cost:,.2f} |")

                    report.append("\n")

        # Climate VaR details
        if summary.get("climate_var"):
            report.append("### Climate Value at Risk Detailed Analysis\n")

            stats = summary["climate_var"]

            report.append(
                "The Climate Value at Risk (VaR) represents the potential financial impact of climate-related risks under a specific confidence level. In this analysis, we consider a 95% confidence level, meaning there is a 95% probability that losses will not exceed the VaR value.\n")

            report.append(f"#### Key VaR Statistics\n")
            report.append(f"- VaR (95%): ${stats['var_95']:,.2f}")
            report.append(f"- Expected cost (mean): ${stats['mean']:,.2f}")
            report.append(f"- Median cost: ${stats['median']:,.2f}")
            report.append(f"- Standard deviation: ${stats['std_dev']:,.2f}")
            report.append(f"- Minimum simulated cost: ${stats['min']:,.2f}")
            report.append(f"- Maximum simulated cost: ${stats['max']:,.2f}")
            report.append("\n")

            report.append("#### Interpretation\n")
            report.append(
                f"With 95% confidence, the climate-related financial losses will not exceed ${stats['var_95']:,.2f}. However, in the remaining 5% of scenarios, losses could be significantly higher.")
            report.append("\n")

            # Calculate and display tail risk
            tail_ratio = stats['var_95'] / stats['mean']
            report.append(
                f"The tail risk ratio (VaR/Mean) is {tail_ratio:.2f}, indicating the severity of worst-case scenarios relative to the expected outcome.")
            report.append("\n")

        # Write report
        with open(output_dir / "net_zero_report.md", "w") as f:
            f.write("\n".join(report))