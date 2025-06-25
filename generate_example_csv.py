"""Generate example CSV data for testing the climate risk tool."""

import pandas as pd
import numpy as np
from typing import List, Dict
import random


def generate_example_facilities(num_facilities: int = 20) -> pd.DataFrame:
    """Generate example facility data for climate risk analysis."""
    
    np.random.seed(42)  # For reproducible results
    random.seed(42)
    
    # Define realistic sectors and their characteristics
    sectors = {
        'oil_gas': {
            'count': 3,
            'emissions_range': (50000, 200000),  # High emissions
            'revenue_range': (500e6, 2e9),
            'ebitda_margin': 0.25,
            'asset_multiplier': 3.0
        },
        'utilities': {
            'count': 4,
            'emissions_range': (80000, 300000),  # Very high emissions
            'revenue_range': (1e9, 5e9),  
            'ebitda_margin': 0.20,
            'asset_multiplier': 4.0
        },
        'steel': {
            'count': 2,
            'emissions_range': (40000, 120000),
            'revenue_range': (200e6, 800e6),
            'ebitda_margin': 0.15,
            'asset_multiplier': 2.5
        },
        'cement': {
            'count': 2,
            'emissions_range': (30000, 100000),
            'revenue_range': (150e6, 600e6),
            'ebitda_margin': 0.18,
            'asset_multiplier': 2.8
        },
        'chemicals': {
            'count': 3,
            'emissions_range': (20000, 80000),
            'revenue_range': (300e6, 1.2e9),
            'ebitda_margin': 0.22,
            'asset_multiplier': 2.2
        },
        'automotive': {
            'count': 3,
            'emissions_range': (5000, 25000),
            'revenue_range': (800e6, 3e9),
            'ebitda_margin': 0.12,
            'asset_multiplier': 1.8
        },
        'real_estate': {
            'count': 2,
            'emissions_range': (1000, 8000),
            'revenue_range': (50e6, 300e6),
            'ebitda_margin': 0.35,
            'asset_multiplier': 5.0
        },
        'financial': {
            'count': 1,
            'emissions_range': (500, 3000),
            'revenue_range': (1e9, 4e9),
            'ebitda_margin': 0.40,
            'asset_multiplier': 15.0
        }
    }
    
    countries = ['USA', 'Germany', 'China', 'Japan', 'UK', 'Canada', 'Australia', 'France']
    
    facilities = []
    facility_id = 1
    
    for sector, config in sectors.items():
        for i in range(config['count']):
            # Generate emissions (Scope 1 typically 70-80% of total)
            total_emissions = np.random.uniform(*config['emissions_range'])
            scope1_emissions = total_emissions * np.random.uniform(0.7, 0.8)
            scope2_emissions = total_emissions - scope1_emissions
            
            # Generate financial data
            revenue = np.random.uniform(*config['revenue_range'])
            ebitda = revenue * config['ebitda_margin'] * np.random.uniform(0.8, 1.2)
            assets = revenue * config['asset_multiplier'] * np.random.uniform(0.8, 1.3)
            
            # Add some realistic variation
            country = random.choice(countries)
            
            facility = {
                'facility_id': f'FAC_{facility_id:03d}',
                'facility_name': f'{sector.title().replace("_", " ")} Facility {i+1} ({country})',
                'sector': sector,
                'current_emissions_scope1': round(scope1_emissions, 1),
                'current_emissions_scope2': round(scope2_emissions, 1),
                'annual_revenue': round(revenue, 0),
                'ebitda': round(ebitda, 0),
                'assets_value': round(assets, 0),
                'country': country,
                'scope3_emissions': round(total_emissions * np.random.uniform(2.0, 5.0), 1),
                'capex_annual': round(revenue * 0.05 * np.random.uniform(0.5, 2.0), 0),
                'opex_annual': round(revenue * 0.6 * np.random.uniform(0.8, 1.2), 0),
                'carbon_price_exposure': round(np.random.uniform(0.1, 0.8), 2),
                'transition_costs_estimated': round(scope1_emissions * np.random.uniform(50, 150), 0)
            }
            
            facilities.append(facility)
            facility_id += 1
    
    return pd.DataFrame(facilities)


def main():
    """Generate and save example data."""
    print("Generating example facility data...")
    
    # Generate data
    facilities_df = generate_example_facilities()
    
    # Save to CSV
    output_file = 'example_facilities.csv'
    facilities_df.to_csv(output_file, index=False)
    
    print(f"Generated {len(facilities_df)} facilities")
    print(f"Saved to: {output_file}")
    
    # Print summary
    print("\nDataset Summary:")
    print(f"Total facilities: {len(facilities_df)}")
    print(f"Sectors: {facilities_df['sector'].nunique()}")
    print(f"Countries: {facilities_df['country'].nunique()}")
    print(f"Total Scope 1+2 emissions: {(facilities_df['current_emissions_scope1'] + facilities_df['current_emissions_scope2']).sum():,.0f} tCO2e")
    print(f"Total revenue: ${facilities_df['annual_revenue'].sum():,.0f}")
    print(f"Total assets: ${facilities_df['assets_value'].sum():,.0f}")
    
    print("\nBy Sector:")
    sector_summary = facilities_df.groupby('sector').agg({
        'facility_id': 'count',
        'current_emissions_scope1': 'sum',
        'current_emissions_scope2': 'sum',
        'annual_revenue': 'sum'
    }).round(0)
    sector_summary.columns = ['Facilities', 'Scope1 (tCO2e)', 'Scope2 (tCO2e)', 'Revenue ($)']
    print(sector_summary)
    
    print(f"\nExample file ready for analysis!")
    print(f"Run: python -m climate_risk_tool.cli {output_file}")


if __name__ == "__main__":
    main()