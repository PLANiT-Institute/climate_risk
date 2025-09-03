"""
Climate Risk Assessment Tool - Streamlit Web Interface
Main application entry point for deployment
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Configure page
st.set_page_config(
    page_title="Climate Risk Assessment Tool",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/climate-risk-tool',
        'Report a bug': 'https://github.com/your-repo/climate-risk-tool/issues',
        'About': "# Climate Risk Assessment Tool\nComprehensive climate risk analysis platform"
    }
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'data_uploaded' not in st.session_state:
        st.session_state.data_uploaded = False
    
    if 'facilities_df' not in st.session_state:
        st.session_state.facilities_df = pd.DataFrame()
    
    if 'analysis_config' not in st.session_state:
        st.session_state.analysis_config = {
            'discount_rate': 0.06,
            'target_year': 2050,
            'scenarios': ['NDC', 'Below2C', 'NetZero'],
            'approaches': ['linear', 'optimal']
        }
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {
            'macc': None,
            'physical_risk': None,
            'pathways': None
        }

def render_sidebar():
    """Render navigation sidebar"""
    st.sidebar.markdown("## 🧭 Navigation")
    
    # Progress indicator
    progress_data = {
        'Data Upload': st.session_state.data_uploaded,
        'MACC Analysis': st.session_state.analysis_results['macc'] is not None,
        'Physical Risk': st.session_state.analysis_results['physical_risk'] is not None,
        'Pathways': st.session_state.analysis_results['pathways'] is not None
    }
    
    st.sidebar.markdown("### 📊 Progress")
    for step, completed in progress_data.items():
        status = "✅" if completed else "⏳"
        st.sidebar.markdown(f"{status} {step}")
    
    # Quick stats if data is loaded
    if st.session_state.data_uploaded:
        st.sidebar.markdown("### 📈 Portfolio Summary")
        df = st.session_state.facilities_df
        
        if not df.empty:
            st.sidebar.metric("Facilities", len(df))
            
            if 'country' in df.columns:
                st.sidebar.metric("Countries", df['country'].nunique())
            
            if 'asset_value_usd' in df.columns:
                total_assets = df['asset_value_usd'].sum()
                st.sidebar.metric("Total Assets", f"${total_assets/1e9:.1f}B")
            
            if 'annual_emissions_tco2' in df.columns:
                total_emissions = df['annual_emissions_tco2'].sum()
                st.sidebar.metric("Total Emissions", f"{total_emissions:,.0f} tCO2e")

def render_main_dashboard():
    """Render main dashboard content"""
    
    # Header
    st.markdown('<h1 class="main-header">🌍 Climate Risk Assessment Tool</h1>', unsafe_allow_html=True)
    
    # Welcome message
    st.markdown("""
    Welcome to the **Climate Risk Assessment Platform** - your comprehensive solution for analyzing 
    climate-related financial risks and developing strategic decarbonization pathways.
    """)
    
    # Feature overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 💰 MACC Analysis
        - Cost-effective decarbonization
        - Technology prioritization  
        - Investment optimization
        - Quick win identification
        """)
    
    with col2:
        st.markdown("""
        ### 🌪️ Physical Risk
        - Climate hazard assessment
        - Asset vulnerability analysis
        - Financial impact quantification
        - Mitigation recommendations
        """)
    
    with col3:
        st.markdown("""
        ### 🛣️ Net-Zero Pathways
        - Strategic roadmaps
        - Timeline optimization
        - Budget planning
        - Scenario analysis
        """)
    
    # Getting started section
    st.markdown("---")
    st.markdown("## 🚀 Getting Started")
    
    if not st.session_state.data_uploaded:
        st.markdown("""
        <div class="warning-box">
        <strong>📤 Step 1:</strong> Upload your facilities data to begin analysis.<br>
        Navigate to <strong>Data Upload</strong> page to get started.
        </div>
        """, unsafe_allow_html=True)
        
        # Sample data download
        st.markdown("### 📥 Need Sample Data?")
        col1, col2 = st.columns(2)
        
        with col1:
            col1a, col1b = st.columns(2)
            with col1a:
                if st.button("📊 Download Sample Data"):
                    sample_data = create_sample_facilities_data()
                    csv = sample_data.to_csv(index=False)
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv,
                        file_name="sample_facilities.csv",
                        mime="text/csv"
                    )
            with col1b:
                if st.button("⚡ Use Sample Data Now"):
                    sample_data = create_sample_facilities_data()
                    st.session_state.facilities_df = sample_data
                    st.session_state.data_uploaded = True
                    st.success("🎉 Sample data loaded successfully!")
                    st.rerun()
        
        with col2:
            st.info("Sample data includes 10 facilities across different sectors with all required fields.")
    
    else:
        st.markdown("""
        <div class="success-box">
        <strong>✅ Data Loaded Successfully!</strong><br>
        Your facilities data is ready for analysis. Explore the analysis pages to generate insights.
        </div>
        """, unsafe_allow_html=True)
        
        # Quick overview of loaded data
        render_data_overview()

def render_data_overview():
    """Render overview of loaded data"""
    
    df = st.session_state.facilities_df
    
    st.markdown("### 📊 Data Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Facilities", len(df))
    
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
    
    # Data preview
    with st.expander("🔍 Data Preview", expanded=False):
        st.dataframe(df.head(10), use_container_width=True)
    
    # Analysis status
    st.markdown("### 🎯 Analysis Status")
    
    analysis_status = [
        ("MACC Analysis", st.session_state.analysis_results['macc'] is not None, "Identify cost-effective decarbonization opportunities"),
        ("Physical Risk", st.session_state.analysis_results['physical_risk'] is not None, "Assess climate-related physical risks"), 
        ("Net-Zero Pathways", st.session_state.analysis_results['pathways'] is not None, "Generate strategic decarbonization roadmaps")
    ]
    
    for analysis_name, completed, description in analysis_status:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            status_icon = "✅" if completed else "⏳"
            st.markdown(f"{status_icon} **{analysis_name}**: {description}")
        
        with col2:
            if completed:
                st.success("Complete")
            else:
                st.info("Pending")

def create_sample_facilities_data():
    """Create sample facilities data for download"""
    
    np.random.seed(42)
    
    sample_data = {
        'facility_id': [f'FAC_{i+1:03d}' for i in range(10)],
        'facility_name': [f'Facility {i+1}' for i in range(10)],
        'country': np.random.choice(['USA', 'Germany', 'Japan', 'UK', 'France'], 10),
        'sector': np.random.choice(['Manufacturing', 'Office', 'Warehouse', 'Utilities'], 10),
        'latitude': np.random.uniform(30, 60, 10).round(4),
        'longitude': np.random.uniform(-120, 20, 10).round(4),
        'asset_value_usd': np.random.randint(10_000_000, 100_000_000, 10),
        'annual_emissions_scope1': np.random.randint(1000, 10000, 10),
        'annual_emissions_scope2': np.random.randint(2000, 15000, 10),
        'annual_revenue': np.random.randint(50_000_000, 500_000_000, 10),
        'employees': np.random.randint(50, 500, 10),
        'floor_area_sqm': np.random.randint(5000, 50000, 10)
    }
    
    # Calculate total emissions
    df = pd.DataFrame(sample_data)
    df['annual_emissions_tco2'] = df['annual_emissions_scope1'] + df['annual_emissions_scope2']
    
    return df

def main():
    """Main application function"""
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render main content
    render_main_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8rem;'>
    Climate Risk Assessment Tool v2.0 | Built with Streamlit | 
    <a href='https://github.com/your-repo'>GitHub</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()