"""
Data Upload Page - Climate Risk Assessment Tool
Handles file upload, validation, and data preprocessing
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import io

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="Data Upload", page_icon="📊", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .upload-box {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
    }
    
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def validate_facilities_data(df: pd.DataFrame) -> tuple[bool, list, pd.DataFrame]:
    """
    Validate and clean facilities data
    
    Returns:
        (is_valid, validation_messages, cleaned_df)
    """
    
    messages = []
    is_valid = True
    cleaned_df = df.copy()
    
    # Required columns
    required_columns = {
        'facility_id': 'Facility identifier',
        'country': 'Country location',
        'latitude': 'Latitude coordinate',
        'longitude': 'Longitude coordinate'
    }
    
    # Check required columns
    missing_required = []
    for col, description in required_columns.items():
        if col not in cleaned_df.columns:
            # Try common alternative names
            alternatives = {
                'facility_id': ['id', 'facility_name', 'name'],
                'country': ['Country', 'nation'],
                'latitude': ['lat', 'Latitude'], 
                'longitude': ['lon', 'lng', 'Longitude']
            }
            
            found = False
            for alt in alternatives.get(col, []):
                if alt in cleaned_df.columns:
                    cleaned_df = cleaned_df.rename(columns={alt: col})
                    messages.append(f"✅ Mapped '{alt}' to '{col}'")
                    found = True
                    break
            
            if not found:
                missing_required.append(f"{col} ({description})")
    
    if missing_required:
        is_valid = False
        messages.append(f"❌ Missing required columns: {', '.join(missing_required)}")
    
    # Recommended columns
    recommended_columns = {
        'asset_value_usd': 'Asset value in USD',
        'annual_emissions_tco2': 'Annual emissions in tCO2e',
        'sector': 'Industry sector',
        'employees': 'Number of employees',
        'floor_area_sqm': 'Floor area in square meters'
    }
    
    missing_recommended = []
    for col, description in recommended_columns.items():
        if col not in cleaned_df.columns:
            # Try alternatives for emissions
            if col == 'annual_emissions_tco2':
                alt_found = False
                for alt in ['current_emissions_scope1', 'current_emissions_scope2']:
                    if alt in cleaned_df.columns:
                        alt_found = True
                
                if 'current_emissions_scope1' in cleaned_df.columns and 'current_emissions_scope2' in cleaned_df.columns:
                    cleaned_df['annual_emissions_tco2'] = (
                        cleaned_df['current_emissions_scope1'] + cleaned_df['current_emissions_scope2']
                    )
                    messages.append("✅ Calculated total emissions from Scope 1 + 2")
                    alt_found = True
                
                if not alt_found:
                    missing_recommended.append(f"{col} ({description})")
            
            elif col == 'asset_value_usd' and 'assets_value' in cleaned_df.columns:
                cleaned_df = cleaned_df.rename(columns={'assets_value': 'asset_value_usd'})
                messages.append("✅ Mapped 'assets_value' to 'asset_value_usd'")
            
            else:
                missing_recommended.append(f"{col} ({description})")
    
    if missing_recommended:
        messages.append(f"⚠️ Missing recommended columns: {', '.join(missing_recommended[:3])}...")
    
    # Data quality checks
    if is_valid:
        # Check coordinate validity
        if 'latitude' in cleaned_df.columns and 'longitude' in cleaned_df.columns:
            invalid_coords = (
                (cleaned_df['latitude'] < -90) | (cleaned_df['latitude'] > 90) |
                (cleaned_df['longitude'] < -180) | (cleaned_df['longitude'] > 180)
            ).sum()
            
            if invalid_coords > 0:
                messages.append(f"⚠️ {invalid_coords} rows have invalid coordinates")
        
        # Check for duplicates
        if 'facility_id' in cleaned_df.columns:
            duplicates = cleaned_df['facility_id'].duplicated().sum()
            if duplicates > 0:
                messages.append(f"⚠️ {duplicates} duplicate facility IDs found")
        
        # Check data completeness
        missing_data_pct = (cleaned_df.isnull().sum().sum() / (len(cleaned_df) * len(cleaned_df.columns))) * 100
        if missing_data_pct > 20:
            messages.append(f"⚠️ High missing data: {missing_data_pct:.1f}%")
        else:
            messages.append(f"✅ Data completeness: {100-missing_data_pct:.1f}%")
        
        messages.append(f"✅ Successfully validated {len(cleaned_df)} facilities")
    
    return is_valid, messages, cleaned_df

def create_sample_data_download():
    """Create downloadable sample data"""
    
    sample_data = {
        'facility_id': ['FAC_001', 'FAC_002', 'FAC_003', 'FAC_004', 'FAC_005'],
        'facility_name': ['Manufacturing Plant A', 'Office Building B', 'Warehouse C', 'Power Plant D', 'Steel Mill E'],
        'country': ['USA', 'Germany', 'UK', 'Japan', 'China'],
        'sector': ['Manufacturing', 'Office', 'Logistics', 'Utilities', 'Steel'],
        'latitude': [40.7128, 52.5200, 51.5074, 35.6762, 39.9042],
        'longitude': [-74.0060, 13.4050, -0.1278, 139.6503, 116.4074],
        'asset_value_usd': [50_000_000, 25_000_000, 15_000_000, 200_000_000, 100_000_000],
        'annual_emissions_scope1': [5000, 200, 800, 50000, 75000],
        'annual_emissions_scope2': [3000, 800, 1200, 25000, 45000],
        'annual_revenue': [100_000_000, 50_000_000, 30_000_000, 150_000_000, 200_000_000],
        'employees': [200, 150, 50, 100, 300],
        'floor_area_sqm': [10000, 5000, 20000, 15000, 25000]
    }
    
    df = pd.DataFrame(sample_data)
    df['annual_emissions_tco2'] = df['annual_emissions_scope1'] + df['annual_emissions_scope2']
    
    return df

def render_upload_interface():
    """Main upload interface"""
    
    st.title("📊 Data Upload")
    st.markdown("Upload your facilities data to begin climate risk analysis.")
    
    # Upload tabs
    tab1, tab2, tab3 = st.tabs(["🏭 Facilities Data", "📋 Data Requirements", "📥 Sample Data"])
    
    with tab1:
        render_facilities_upload()
    
    with tab2:
        render_data_requirements()
        
    with tab3:
        render_sample_data_section()

def render_facilities_upload():
    """Facilities data upload section"""
    
    st.markdown("### 🏭 Upload Facilities Data")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose your facilities data file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload a CSV or Excel file containing your facilities information"
    )
    
    if uploaded_file is not None:
        try:
            # Display file info
            st.info(f"📁 File: {uploaded_file.name} ({uploaded_file.size:,} bytes)")
            
            # Load data based on file type
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ File loaded successfully: {len(df)} rows, {len(df.columns)} columns")
            
            # Validate data
            with st.spinner("Validating data..."):
                is_valid, messages, cleaned_df = validate_facilities_data(df)
            
            # Display validation results
            st.markdown("### 🔍 Validation Results")
            
            for message in messages:
                if message.startswith("✅"):
                    st.success(message)
                elif message.startswith("⚠️"):
                    st.warning(message)
                elif message.startswith("❌"):
                    st.error(message)
                else:
                    st.info(message)
            
            # Data preview
            if is_valid:
                st.markdown("### 📋 Data Preview")
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Facilities", len(cleaned_df))
                
                with col2:
                    if 'country' in cleaned_df.columns:
                        st.metric("Countries", cleaned_df['country'].nunique())
                
                with col3:
                    if 'asset_value_usd' in cleaned_df.columns:
                        total_assets = cleaned_df['asset_value_usd'].sum()
                        st.metric("Total Assets", f"${total_assets/1e9:.1f}B")
                
                with col4:
                    if 'annual_emissions_tco2' in cleaned_df.columns:
                        total_emissions = cleaned_df['annual_emissions_tco2'].sum()
                        st.metric("Total Emissions", f"{total_emissions:,.0f} tCO2e")
                
                # Data table preview
                st.dataframe(cleaned_df.head(10), use_container_width=True)
                
                # Column information
                with st.expander("📊 Column Information", expanded=False):
                    col_info = pd.DataFrame({
                        'Column': cleaned_df.columns,
                        'Data Type': cleaned_df.dtypes.astype(str),
                        'Non-Null Count': cleaned_df.count(),
                        'Missing %': ((cleaned_df.isnull().sum() / len(cleaned_df)) * 100).round(1)
                    })
                    st.dataframe(col_info, use_container_width=True)
                
                # Save to session state
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Use This Data", type="primary", use_container_width=True):
                        st.session_state.facilities_df = cleaned_df
                        st.session_state.data_uploaded = True
                        st.success("🎉 Data uploaded successfully! You can now proceed to analysis.")
                        st.balloons()
                
                with col2:
                    # Download cleaned data
                    csv = cleaned_df.to_csv(index=False)
                    st.download_button(
                        label="💾 Download Cleaned Data",
                        data=csv,
                        file_name=f"cleaned_{uploaded_file.name}",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            else:
                st.error("❌ Data validation failed. Please fix the issues above and try again.")
                
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")

def render_data_requirements():
    """Data requirements documentation"""
    
    st.markdown("### 📋 Data Requirements")
    
    st.markdown("""
    To perform comprehensive climate risk analysis, your facilities data should include the following information:
    """)
    
    # Required fields
    st.markdown("#### ✅ Required Fields")
    required_fields = pd.DataFrame([
        {"Field": "facility_id", "Description": "Unique identifier for each facility", "Example": "FAC_001, FAC_002"},
        {"Field": "country", "Description": "Country where facility is located", "Example": "USA, Germany, Japan"},
        {"Field": "latitude", "Description": "Latitude coordinate (decimal degrees)", "Example": "40.7128, 52.5200"},
        {"Field": "longitude", "Description": "Longitude coordinate (decimal degrees)", "Example": "-74.0060, 13.4050"}
    ])
    st.table(required_fields)
    
    # Recommended fields
    st.markdown("#### 🔶 Recommended Fields")
    recommended_fields = pd.DataFrame([
        {"Field": "asset_value_usd", "Description": "Asset value in USD", "Example": "50000000, 25000000"},
        {"Field": "annual_emissions_tco2", "Description": "Total annual emissions in tCO2e", "Example": "8000, 1000"},
        {"Field": "sector", "Description": "Industry sector", "Example": "Manufacturing, Office"},
        {"Field": "employees", "Description": "Number of employees", "Example": "200, 150"},
        {"Field": "floor_area_sqm", "Description": "Floor area in square meters", "Example": "10000, 5000"}
    ])
    st.table(recommended_fields)
    
    # Optional fields
    with st.expander("🔷 Optional Fields (for enhanced analysis)", expanded=False):
        optional_fields = pd.DataFrame([
            {"Field": "annual_emissions_scope1", "Description": "Direct emissions (tCO2e)", "Example": "5000"},
            {"Field": "annual_emissions_scope2", "Description": "Indirect emissions from energy (tCO2e)", "Example": "3000"},
            {"Field": "annual_revenue", "Description": "Annual revenue in USD", "Example": "100000000"},
            {"Field": "building_age_years", "Description": "Age of building/facility", "Example": "15"},
            {"Field": "backup_systems", "Description": "Has backup power/systems", "Example": "Yes, No"}
        ])
        st.table(optional_fields)

def render_sample_data_section():
    """Sample data download section"""
    
    st.markdown("### 📥 Sample Data")
    
    st.markdown("""
    Download our sample dataset to understand the expected data format and test the tool functionality.
    """)
    
    # Create and display sample data
    sample_df = create_sample_data_download()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Sample data includes:**")
        st.markdown("""
        - 5 example facilities
        - All required and recommended fields
        - Multiple sectors and countries
        - Realistic data values
        """)
    
    with col2:
        # Download button
        csv = sample_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Sample Data",
            data=csv,
            file_name="sample_facilities_data.csv",
            mime="text/csv",
            type="primary"
        )
    
    # Preview sample data
    with st.expander("👀 Preview Sample Data", expanded=True):
        st.dataframe(sample_df, use_container_width=True)

def main():
    """Main function for data upload page"""
    
    # Check if already uploaded
    if st.session_state.get('data_uploaded', False):
        st.success("✅ Data already uploaded!")
        
        # Show current data summary
        df = st.session_state.facilities_df
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Facilities", len(df))
        with col2:
            if 'country' in df.columns:
                st.metric("Countries", df['country'].nunique())
        with col3:
            if 'asset_value_usd' in df.columns:
                total_assets = df['asset_value_usd'].sum()
                st.metric("Total Assets", f"${total_assets/1e9:.1f}B")
        with col4:
            if 'annual_emissions_tco2' in df.columns:
                total_emissions = df['annual_emissions_tco2'].sum()
                st.metric("Total Emissions", f"{total_emissions:,.0f} tCO2e")
        
        # Option to upload new data
        if st.button("🔄 Upload New Data"):
            st.session_state.data_uploaded = False
            st.session_state.facilities_df = pd.DataFrame()
            st.rerun()
        
        st.markdown("---")
    
    # Render upload interface
    render_upload_interface()

if __name__ == "__main__":
    main()