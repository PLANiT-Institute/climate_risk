"""Input/Output utilities for the climate risk tool."""

import pandas as pd
from typing import Dict, Any, Optional
import os


class DataValidator:
    """Validates input data for climate risk calculations."""
    
    REQUIRED_COLUMNS = [
        'facility_id',
        'facility_name', 
        'sector',
        'current_emissions_scope1',  # tCO2e
        'current_emissions_scope2',  # tCO2e
        'annual_revenue',           # USD
        'ebitda',                  # USD
        'assets_value',            # USD
        'country'
    ]
    
    OPTIONAL_COLUMNS = [
        'scope3_emissions',
        'capex_annual',
        'opex_annual',
        'carbon_price_exposure',
        'transition_costs_estimated'
    ]
    
    @classmethod
    def validate_input_data(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate input CSV data and return validation results."""
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'summary': {}
        }
        
        # Check required columns
        missing_cols = set(cls.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            results['is_valid'] = False
            results['errors'].append(f"Missing required columns: {missing_cols}")
        
        # Check for null values in required columns
        for col in cls.REQUIRED_COLUMNS:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    results['warnings'].append(f"Column '{col}' has {null_count} null values")
        
        # Validate data types and ranges
        if 'current_emissions_scope1' in df.columns:
            negative_emissions = (df['current_emissions_scope1'] < 0).sum()
            if negative_emissions > 0:
                results['warnings'].append(f"{negative_emissions} facilities have negative Scope 1 emissions")
        
        if 'annual_revenue' in df.columns:
            zero_revenue = (df['annual_revenue'] <= 0).sum()
            if zero_revenue > 0:
                results['warnings'].append(f"{zero_revenue} facilities have zero or negative revenue")
        
        # Summary statistics
        results['summary'] = {
            'total_facilities': len(df),
            'sectors': df['sector'].nunique() if 'sector' in df.columns else 0,
            'countries': df['country'].nunique() if 'country' in df.columns else 0,
            'total_scope1_emissions': df['current_emissions_scope1'].sum() if 'current_emissions_scope1' in df.columns else 0,
            'total_revenue': df['annual_revenue'].sum() if 'annual_revenue' in df.columns else 0
        }
        
        return results


def load_input_data(file_path: str) -> pd.DataFrame:
    """Load and validate input CSV data."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        print(f"Loaded {len(df)} facilities from {file_path}")
        
        # Validate data
        validation = DataValidator.validate_input_data(df)
        
        if not validation['is_valid']:
            raise ValueError(f"Input data validation failed: {validation['errors']}")
        
        if validation['warnings']:
            print("Data validation warnings:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        print(f"Summary: {validation['summary']}")
        
        return df
        
    except Exception as e:
        raise ValueError(f"Error loading input data: {str(e)}")


def save_results(results_df: pd.DataFrame, output_path: str) -> None:
    """Save results to CSV file."""
    try:
        results_df.to_csv(output_path, index=False)
        print(f"Results saved to: {output_path}")
        print(f"Output contains {len(results_df)} facilities with {len(results_df.columns)} columns")
        
    except Exception as e:
        raise ValueError(f"Error saving results: {str(e)}")


def create_output_filename(input_path: str, suffix: str = "_climate_risk_results") -> str:
    """Create output filename based on input filename."""
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_dir = os.path.dirname(input_path) or "."
    return os.path.join(output_dir, f"{base_name}{suffix}.csv")