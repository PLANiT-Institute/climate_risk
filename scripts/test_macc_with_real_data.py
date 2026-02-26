"""
Test MACC Generator with Real Facilities Data
Using your existing facilities data from the project
"""

import pandas as pd
import numpy as np
from generate_macc import MACCGenerator, create_sample_abatement_projects
import os

def load_real_facilities_data():
    """Load your existing facilities data"""
    
    # Try to load from different possible locations
    possible_files = [
        'example_facilities.csv',
        'data/input_facilities.xlsx', 
        'example_facilities_climate_risk_results.csv'
    ]
    
    facilities_df = None
    
    for file_path in possible_files:
        if os.path.exists(file_path):
            print(f"📂 Loading facilities data from: {file_path}")
            try:
                if file_path.endswith('.csv'):
                    facilities_df = pd.read_csv(file_path)
                else:
                    facilities_df = pd.read_excel(file_path)
                break
            except Exception as e:
                print(f"❌ Error loading {file_path}: {e}")
                continue
    
    if facilities_df is None:
        print("⚠️ No existing facilities data found, creating sample data...")
        return create_enhanced_sample_data()
    
    print(f"✅ Loaded {len(facilities_df)} real facilities")
    print(f"📊 Columns available: {list(facilities_df.columns)}")
    
    # Standardize column names
    facilities_df = standardize_facilities_data(facilities_df)
    
    return facilities_df

def standardize_facilities_data(df):
    """Standardize column names and add missing fields"""
    
    df_clean = df.copy()
    
    # Standardize column names - handle your specific data structure
    column_mapping = {
        'Facility ID': 'facility_id',
        'facility_name': 'facility_name', 
        'Facility Name': 'facility_name',
        'Country': 'country',
        'Sector': 'sector',
        'Annual Emissions (tCO2)': 'annual_emissions_tco2',
        'current_emissions_scope1': 'annual_emissions_scope1',
        'current_emissions_scope2': 'annual_emissions_scope2', 
        'assets_value': 'asset_value_usd',
        'Asset Value (USD)': 'asset_value_usd',
        'Latitude': 'latitude',
        'Longitude': 'longitude'
    }
    
    # Apply column mapping
    for old_name, new_name in column_mapping.items():
        if old_name in df_clean.columns:
            df_clean = df_clean.rename(columns={old_name: new_name})
    
    # Calculate total emissions if not present
    if 'annual_emissions_tco2' not in df_clean.columns:
        if 'annual_emissions_scope1' in df_clean.columns and 'annual_emissions_scope2' in df_clean.columns:
            df_clean['annual_emissions_tco2'] = df_clean['annual_emissions_scope1'] + df_clean['annual_emissions_scope2']
    
    # Add missing fields with estimates
    if 'floor_area_sqm' not in df_clean.columns:
        # Estimate floor area based on asset value, emissions, or revenue
        if 'asset_value_usd' in df_clean.columns:
            df_clean['floor_area_sqm'] = (df_clean['asset_value_usd'] / 5000).fillna(10000)  # $5000 per sqm
        elif 'annual_emissions_tco2' in df_clean.columns:
            df_clean['floor_area_sqm'] = df_clean['annual_emissions_tco2'] * 5  # 5 sqm per tCO2e
        else:
            df_clean['floor_area_sqm'] = np.random.randint(5000, 50000, len(df_clean))
    
    if 'employees' not in df_clean.columns:
        # Estimate employees based on floor area and sector
        base_employees = (df_clean['floor_area_sqm'] / 50).fillna(200)  # 50 sqm per employee
        # Adjust by sector
        sector_multipliers = {
            'oil_gas': 0.3,      # Capital intensive, fewer employees
            'utilities': 0.4,     # Automated, fewer employees
            'steel': 0.8,         # Manufacturing, more employees
            'chemicals': 0.6,     # Process industry
            'manufacturing': 1.0,  # Standard
            'office': 2.0         # Service sector, more employees per area
        }
        
        if 'sector' in df_clean.columns:
            for sector, multiplier in sector_multipliers.items():
                mask = df_clean['sector'].str.contains(sector, case=False, na=False)
                df_clean.loc[mask, 'employees'] = (base_employees * multiplier).astype(int)
        
        df_clean['employees'] = df_clean['employees'].fillna(200).astype(int)
    
    if 'building_age_years' not in df_clean.columns:
        # Industrial facilities tend to be older
        df_clean['building_age_years'] = np.random.randint(10, 35, len(df_clean))
    
    # Add coordinates if missing (rough estimates by country)
    if 'latitude' not in df_clean.columns or 'longitude' not in df_clean.columns:
        country_coords = {
            'Germany': (51.1657, 10.4515),
            'USA': (39.8283, -98.5795), 
            'UK': (55.3781, -3.4360),
            'Japan': (36.2048, 138.2529),
            'China': (35.8617, 104.1954),
            'France': (46.6034, 1.8883),
            'Brazil': (-14.2350, -51.9253)
        }
        
        if 'country' in df_clean.columns:
            for country, (lat, lon) in country_coords.items():
                mask = df_clean['country'] == country
                if 'latitude' not in df_clean.columns:
                    df_clean.loc[mask, 'latitude'] = lat + np.random.uniform(-2, 2, mask.sum())
                if 'longitude' not in df_clean.columns:
                    df_clean.loc[mask, 'longitude'] = lon + np.random.uniform(-5, 5, mask.sum())
        
        # Fill any remaining missing coordinates
        if 'latitude' not in df_clean.columns:
            df_clean['latitude'] = np.random.uniform(30, 60, len(df_clean))
        if 'longitude' not in df_clean.columns:
            df_clean['longitude'] = np.random.uniform(-120, 120, len(df_clean))
    
    return df_clean

def create_enhanced_sample_data():
    """Create more realistic sample data based on typical facility characteristics"""
    
    np.random.seed(42)
    
    # More realistic facility types and their characteristics
    facility_types = [
        {'type': 'Manufacturing Plant', 'sector': 'Manufacturing', 'size_range': (10000, 50000), 'emissions_range': (2000, 10000)},
        {'type': 'Distribution Center', 'sector': 'Logistics', 'size_range': (20000, 80000), 'emissions_range': (500, 3000)}, 
        {'type': 'Office Building', 'sector': 'Commercial', 'size_range': (5000, 25000), 'emissions_range': (200, 1500)},
        {'type': 'Data Center', 'sector': 'Technology', 'size_range': (2000, 10000), 'emissions_range': (1000, 8000)},
        {'type': 'Retail Store', 'sector': 'Retail', 'size_range': (1000, 5000), 'emissions_range': (100, 800)}
    ]
    
    countries = ['USA', 'Germany', 'Japan', 'Canada', 'UK', 'France', 'Australia', 'Netherlands']
    
    facilities_data = []
    
    # Generate 50 facilities for more comprehensive analysis
    for i in range(50):
        facility_type = np.random.choice(facility_types)
        country = np.random.choice(countries)
        
        floor_area = np.random.randint(*facility_type['size_range'])
        annual_emissions = np.random.randint(*facility_type['emissions_range'])
        
        # Generate realistic coordinates based on country
        lat_ranges = {
            'USA': (30, 48), 'Germany': (47, 55), 'Japan': (31, 46),
            'Canada': (42, 60), 'UK': (50, 59), 'France': (42, 51),
            'Australia': (-40, -12), 'Netherlands': (51, 54)
        }
        
        lat_range = lat_ranges.get(country, (30, 60))
        latitude = np.random.uniform(*lat_range)
        longitude = np.random.uniform(-180, 180)
        
        facility = {
            'facility_id': f'REAL_{i+1:03d}',
            'facility_name': f'{facility_type["type"]} {i+1}',
            'country': country,
            'sector': facility_type['sector'],
            'latitude': latitude,
            'longitude': longitude,
            'floor_area_sqm': floor_area,
            'employees': int(floor_area / 25),  # ~25 sqm per employee
            'annual_emissions_tco2': annual_emissions,
            'annual_emissions_scope1': annual_emissions * 0.4,
            'annual_emissions_scope2': annual_emissions * 0.6,
            'asset_value_usd': floor_area * np.random.uniform(1500, 3000),
            'building_age_years': np.random.randint(5, 40)
        }
        
        facilities_data.append(facility)
    
    return pd.DataFrame(facilities_data)

def main():
    """Test MACC generator with real facilities data"""
    
    print("🏭 Testing MACC Generator with Real Facilities Data")
    print("=" * 60)
    
    # Load real facilities data
    facilities_df = load_real_facilities_data()
    
    # Display data summary
    print(f"\n📊 FACILITIES DATA SUMMARY:")
    print(f"   Total Facilities: {len(facilities_df)}")
    if 'country' in facilities_df.columns:
        print(f"   Countries: {facilities_df['country'].nunique()} ({', '.join(facilities_df['country'].unique()[:5])})")
    if 'sector' in facilities_df.columns:
        print(f"   Sectors: {facilities_df['sector'].nunique()} ({', '.join(facilities_df['sector'].unique()[:3])})")
    
    # Total emissions
    if 'annual_emissions_tco2' in facilities_df.columns:
        total_emissions = facilities_df['annual_emissions_tco2'].sum()
        print(f"   Total Annual Emissions: {total_emissions:,.0f} tCO2e")
    elif 'annual_emissions_scope1' in facilities_df.columns:
        total_emissions = (facilities_df['annual_emissions_scope1'] + facilities_df['annual_emissions_scope2']).sum()
        print(f"   Total Annual Emissions: {total_emissions:,.0f} tCO2e")
    
    # Asset value
    if 'asset_value_usd' in facilities_df.columns:
        total_asset_value = facilities_df['asset_value_usd'].sum()
        print(f"   Total Asset Value: ${total_asset_value/1e9:.1f} Billion")
    
    # Initialize MACC generator with real data
    print(f"\n⚙️ Initializing MACC generator with real facilities...")
    macc_gen = MACCGenerator(facilities_df, discount_rate=0.06)
    
    # Load abatement projects
    sample_projects = create_sample_abatement_projects()
    for project in sample_projects:
        macc_gen.add_project(project)
    
    print(f"🔧 Added {len(sample_projects)} abatement technologies")
    
    # Generate MACC curve
    print(f"📈 Generating MACC curve for real facilities...")
    macc_df = macc_gen.generate_macc_curve()
    
    # Display enhanced results
    print(f"\n" + "=" * 60)
    print(f"🎯 REAL FACILITIES MACC ANALYSIS")
    print("=" * 60)
    
    # Key statistics
    total_abatement = macc_df['annual_abatement_potential'].sum()
    total_capex = macc_df['total_capex_required'].sum()
    net_negative_projects = len(macc_df[macc_df['net_negative_cost']])
    # Calculate baseline emissions safely
    if 'annual_emissions_tco2' in facilities_df.columns:
        baseline_emissions = facilities_df['annual_emissions_tco2'].sum()
    elif 'annual_emissions_scope1' in facilities_df.columns and 'annual_emissions_scope2' in facilities_df.columns:
        baseline_emissions = facilities_df['annual_emissions_scope1'].sum() + facilities_df['annual_emissions_scope2'].sum()
    else:
        # Estimate from available data
        baseline_emissions = 100000  # Default estimate
    
    print(f"📊 Baseline Annual Emissions: {baseline_emissions:,.0f} tCO2e")
    print(f"📈 Total Abatement Potential: {total_abatement:,.0f} tCO2e/year ({total_abatement/baseline_emissions*100:.1f}% of baseline)")
    print(f"💰 Total CAPEX Required: ${total_capex/1e6:.1f} Million")
    print(f"💚 Net Cost-Saving Projects: {net_negative_projects}/{len(macc_df)}")
    print(f"📉 Average Abatement Cost: ${macc_df['lcoa_usd_per_tco2'].mean():.0f}/tCO2e")
    
    # Net-zero pathway analysis
    if total_abatement >= baseline_emissions:
        print(f"🎯 NET-ZERO ACHIEVABLE: Abatement potential exceeds baseline emissions")
        net_zero_capex = macc_df[macc_df['cumulative_abatement'] <= baseline_emissions]['total_capex_required'].sum()
        print(f"   CAPEX for Net-Zero: ${net_zero_capex/1e6:.1f} Million")
    else:
        print(f"⚠️ Additional abatement needed: {baseline_emissions - total_abatement:,.0f} tCO2e")
    
    # Investment priorities
    print(f"\n🏆 TOP 5 INVESTMENT PRIORITIES:")
    print("-" * 45)
    for i, (_, row) in enumerate(macc_df.head(5).iterrows(), 1):
        cost_str = f"${row['lcoa_usd_per_tco2']:.0f}/tCO2e" if row['lcoa_usd_per_tco2'] >= 0 else f"SAVES ${-row['lcoa_usd_per_tco2']:.0f}/tCO2e"
        print(f"{i}. {row['technology']}")
        print(f"   Cost: {cost_str}")
        print(f"   Abatement: {row['annual_abatement_potential']:,.0f} tCO2e/year")
        print(f"   CAPEX: ${row['total_capex_required']/1e6:.1f}M")
        print(f"   Payback: {row['payback_period_years']:.1f} years" if row['payback_period_years'] != float('inf') else "   No payback (net cost)")
        print()
    
    # Sector analysis
    if 'sector' in facilities_df.columns:
        print(f"🏭 FACILITY PORTFOLIO BY SECTOR:")
        sector_stats = facilities_df.groupby('sector').agg({
            'facility_id': 'count',
            'annual_emissions_tco2': 'sum' if 'annual_emissions_tco2' in facilities_df.columns else lambda x: 0,
            'floor_area_sqm': 'sum'
        }).round(0)
        
        for sector, stats in sector_stats.iterrows():
            print(f"   {sector}: {int(stats['facility_id'])} facilities, {int(stats['annual_emissions_tco2']):,} tCO2e")
    
    # Save results
    output_path = "outputs/real_facilities_macc_results.csv"
    macc_df.to_csv(output_path, index=False)
    print(f"\n💾 Results saved to: {output_path}")
    
    # Create visualization
    print("🎨 Creating MACC visualization for real facilities...")
    macc_gen.visualize_macc_curve(macc_df, save_path="outputs/real_facilities_macc_curve.png")
    
    # Summary recommendations
    print(f"\n📋 STRATEGIC RECOMMENDATIONS:")
    print("=" * 30)
    
    # Quick wins
    quick_wins = macc_df[(macc_df['net_negative_cost']) & (macc_df['payback_period_years'] <= 5)]
    if not quick_wins.empty:
        print(f"⚡ QUICK WINS ({len(quick_wins)} projects):")
        quick_wins_abatement = quick_wins['annual_abatement_potential'].sum()
        quick_wins_capex = quick_wins['total_capex_required'].sum()
        print(f"   Abatement: {quick_wins_abatement:,.0f} tCO2e/year")
        print(f"   Investment: ${quick_wins_capex/1e6:.1f}M")
        print(f"   Top technology: {quick_wins.iloc[0]['technology']}")
    
    # Medium-term opportunities  
    medium_term = macc_df[(macc_df['lcoa_usd_per_tco2'] >= 0) & (macc_df['lcoa_usd_per_tco2'] <= 100)]
    if not medium_term.empty:
        print(f"🎯 MEDIUM-TERM (<$100/tCO2): {len(medium_term)} projects")
        print(f"   Additional abatement: {medium_term['annual_abatement_potential'].sum():,.0f} tCO2e/year")
    
    print(f"\n✅ Real Facilities MACC Analysis Complete!")
    
    return macc_df, facilities_df

if __name__ == "__main__":
    # Create outputs directory
    os.makedirs("outputs", exist_ok=True)
    
    # Run analysis
    macc_results, facilities_data = main()