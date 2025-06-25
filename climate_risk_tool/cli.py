"""Command-line interface for the climate risk tool."""

import argparse
import sys
import os
from typing import Dict, Any
import pandas as pd

from .io import load_input_data, save_results, create_output_filename
from .transition import TransitionRiskCalculator
from .reporting import ClimateRiskReporter
from .config import CONFIG


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Climate Transition Risk Assessment Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis with all scenarios
  python -m climate_risk_tool.cli input_facilities.csv
  
  # Analysis with specific scenarios
  python -m climate_risk_tool.cli input_facilities.csv --scenarios net_zero delayed_transition
  
  # Custom output file
  python -m climate_risk_tool.cli input_facilities.csv -o custom_results.csv
  
  # Generate detailed emissions pathways
  python -m climate_risk_tool.cli input_facilities.csv --emissions-detail
        """
    )
    
    parser.add_argument(
        'input_file',
        help='Path to input CSV file with facility data'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output CSV file path (default: auto-generated based on input filename)'
    )
    
    parser.add_argument(
        '--scenarios',
        nargs='+',
        choices=['net_zero', 'delayed_transition', 'current_policies'],
        default=['net_zero', 'delayed_transition', 'current_policies'],
        help='Climate scenarios to analyze (default: all scenarios)'
    )
    
    parser.add_argument(
        '--emissions-detail',
        action='store_true',
        help='Generate detailed emissions pathways output file'
    )
    
    parser.add_argument(
        '--summary-json',
        action='store_true',
        help='Generate JSON summary report'
    )
    
    parser.add_argument(
        '--discount-rate',
        type=float,
        default=CONFIG.discount_rate,
        help=f'Discount rate for NPV calculations (default: {CONFIG.discount_rate})'
    )
    
    parser.add_argument(
        '--confidence-level',
        type=float,
        default=0.95,
        help='Confidence level for Carbon VaR calculation (default: 0.95)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress console output except errors'
    )
    
    args = parser.parse_args()
    
    try:
        # Update configuration
        CONFIG.discount_rate = args.discount_rate
        
        if not args.quiet:
            print("Climate Transition Risk Assessment Tool")
            print("=" * 40)
        
        # Load input data
        if not args.quiet:
            print(f"Loading data from: {args.input_file}")
        
        facilities_df = load_input_data(args.input_file)
        
        # Initialize calculator and reporter
        calculator = TransitionRiskCalculator()
        reporter = ClimateRiskReporter()
        
        # Run analysis for each scenario
        if not args.quiet:
            print(f"Analyzing scenarios: {', '.join(args.scenarios)}")
        
        emissions_pathways = {}
        financial_impacts = {}
        
        for scenario in args.scenarios:
            if not args.quiet:
                print(f"  Processing scenario: {scenario}")
            
            # Calculate emissions pathways
            emissions_df = calculator.calculate_emissions_pathways(
                facilities_df, scenario
            )
            emissions_pathways[scenario] = emissions_df
            
            # Calculate financial impacts
            impacts_df = calculator.calculate_financial_impacts(
                facilities_df, emissions_df, scenario
            )
            financial_impacts[scenario] = impacts_df
        
        # Calculate Carbon VaR
        if not args.quiet:
            print("Calculating Carbon Value at Risk...")
        
        carbon_var_df = calculator.calculate_carbon_var(
            facilities_df, financial_impacts, args.confidence_level
        )
        
        # Generate reports
        if not args.quiet:
            print("Generating reports...")
        
        summary_report = reporter.generate_summary_report(
            facilities_df, emissions_pathways, financial_impacts, carbon_var_df
        )
        
        detailed_output = reporter.create_detailed_output(
            facilities_df, emissions_pathways, financial_impacts, carbon_var_df
        )
        
        # Save main results
        output_file = args.output or create_output_filename(args.input_file)
        save_results(detailed_output, output_file)
        
        # Save optional outputs
        if args.emissions_detail:
            emissions_output = reporter.create_emissions_pathways_output(emissions_pathways)
            emissions_file = create_output_filename(args.input_file, "_emissions_pathways")
            save_results(emissions_output, emissions_file)
        
        if args.summary_json:
            json_file = create_output_filename(args.input_file, "_summary").replace('.csv', '.json')
            reporter.export_summary_json(summary_report, json_file)
        
        # Print executive summary
        if not args.quiet:
            reporter.print_executive_summary(summary_report)
            print(f"\nAnalysis complete! Results saved to: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())