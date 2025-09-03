# Streamlit Web Interface Implementation Plan

## 1. Application Architecture

### Multi-Page Application Structure
```
streamlit_app/
├── main.py                    # Main entry point
├── pages/
│   ├── 01_📊_Data_Upload.py  # Data ingestion interface
│   ├── 02_🎯_Analysis_Setup.py # Analysis configuration
│   ├── 03_💰_Transition_Risk.py # Transition risk results
│   ├── 04_🏭_Decarbonization.py # MACC & net-zero pathways
│   ├── 05_⚡_RE100_Strategy.py # RE100 optimization
│   ├── 06_📈_Results_Dashboard.py # Integrated dashboard
│   └── 07_📑_Reports.py       # Report generation & download
├── components/
│   ├── __init__.py
│   ├── data_upload.py         # Upload components
│   ├── visualization.py       # Chart components
│   ├── metrics.py            # Key metrics display
│   └── tables.py             # Data table components
├── utils/
│   ├── __init__.py
│   ├── session_state.py       # Session management
│   ├── data_processing.py     # Background processing
│   └── export_utils.py        # Download functionality
└── assets/
    ├── images/
    └── styles/
```

### Session State Management
```python
# Centralized session state structure
st.session_state = {
    'data': {
        'facilities': pd.DataFrame(),
        'financial': pd.DataFrame(), 
        'emissions': pd.DataFrame(),
        'carbon_prices': pd.DataFrame(),
        'abatement_projects': pd.DataFrame()
    },
    'analysis_config': {
        'scenarios': ['NDC', 'Below2C', 'NetZero'],
        'discount_rate': 0.06,
        'target_year': 2050,
        'n_simulations': 1000
    },
    'results': {
        'transition_risk': {},
        'macc': pd.DataFrame(),
        'pathways': {},
        're100_strategy': {},
        'climate_var': {}
    },
    'ui_state': {
        'current_step': 1,
        'analysis_complete': False,
        'data_uploaded': False
    }
}
```

## 2. Page-by-Page Implementation

### Page 1: Data Upload 📊

**Purpose**: Upload and validate all required data files

**Key Features**:
- Multi-file drag-and-drop interface
- Real-time data validation and quality scoring
- Interactive data preview with filtering
- Column mapping assistance
- Data completeness dashboard

**Implementation**:
```python
def render_data_upload_page():
    st.title("📊 Climate Risk Data Upload")
    
    # Progress indicator
    st.progress(1/7, "Step 1 of 7: Data Upload")
    
    # Upload sections with tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏭 Facilities", "💰 Financial", "🔥 Emissions", 
        "📈 Carbon Prices", "🔧 Abatement Projects"
    ])
    
    with tab1:
        facilities_data = create_upload_interface('facilities')
    
    with tab2:
        financial_data = create_upload_interface('financial')
    
    # Data completeness summary
    render_data_completeness_dashboard()
    
    # Navigation
    if st.button("Continue to Analysis Setup →", disabled=not all_required_data_uploaded()):
        st.session_state.ui_state.current_step = 2
        st.rerun()
```

**Interactive Components**:
- File upload with progress bars
- Data validation summary cards
- Column mapping interface for misnamed columns
- Sample data download links
- Data quality score visualization

### Page 2: Analysis Setup 🎯

**Purpose**: Configure analysis parameters and scenarios

**Key Features**:
- Climate scenario selection with descriptions
- Financial parameter configuration (WACC, discount rates)
- Analysis scope selection (geographic regions, facilities)
- Monte Carlo simulation settings
- Sensitivity analysis configuration

**Implementation**:
```python
def render_analysis_setup():
    st.title("🎯 Analysis Configuration")
    st.progress(2/7, "Step 2 of 7: Analysis Setup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Climate Scenarios")
        scenarios = st.multiselect(
            "Select scenarios to analyze",
            options=['NDC', 'Below2C', 'NetZero'],
            default=['NDC', 'Below2C'],
            help="NDC: Current policies, Below2C: Paris Agreement, NetZero: 1.5°C pathway"
        )
        
        st.subheader("Financial Parameters")
        discount_rate = st.slider("Discount Rate (WACC)", 0.02, 0.12, 0.06, 0.01)
        
    with col2:
        st.subheader("Analysis Scope")
        # Dynamic facility/region selection based on uploaded data
        render_scope_selector()
        
        st.subheader("Simulation Settings")
        n_simulations = st.slider("Monte Carlo Simulations", 1000, 10000, 5000)
```

### Page 3: Transition Risk 💰

**Purpose**: Display transition risk analysis results

**Key Features**:
- Scenario comparison charts
- Facility-level risk heat maps
- ΔEBITDA and ΔOPEX analysis
- Sensitivity analysis tornado charts
- Time series projections

**Implementation**:
```python
def render_transition_risk_page():
    if not st.session_state.results.get('transition_risk'):
        run_transition_risk_analysis()
    
    st.title("💰 Transition Risk Analysis")
    
    # Key metrics dashboard
    render_transition_metrics_dashboard()
    
    # Interactive visualizations
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "🗺️ Geographic Risk", "📈 Sensitivity"])
    
    with tab1:
        # Scenario comparison
        fig_scenarios = create_scenario_comparison_chart()
        st.plotly_chart(fig_scenarios, use_container_width=True)
        
        # Top risk facilities table
        render_top_risk_facilities_table()
    
    with tab2:
        # Geographic risk map
        render_geographic_risk_map()
        
    with tab3:
        # Sensitivity analysis
        render_sensitivity_analysis()
```

### Page 4: Decarbonization Strategy 🏭

**Purpose**: MACC analysis and net-zero pathway optimization

**Key Features**:
- Interactive MACC curve visualization
- Project prioritization matrix
- Net-zero pathway comparison
- Investment timeline optimization
- Technology deployment scenarios

**Implementation**:
```python
def render_decarbonization_page():
    st.title("🏭 Decarbonization Strategy")
    
    # MACC Analysis Section
    st.subheader("Marginal Abatement Cost Curve (MACC)")
    
    # Interactive MACC chart with hover details
    macc_chart = create_interactive_macc_chart()
    st.plotly_chart(macc_chart, use_container_width=True)
    
    # Project selection interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Project prioritization table with selection
        selected_projects = render_project_selection_table()
    
    with col2:
        # Investment summary
        render_investment_summary(selected_projects)
    
    # Net-zero pathway optimization
    st.subheader("Net-Zero Pathways")
    pathway_results = run_pathway_optimization(selected_projects)
    
    # Pathway visualization
    fig_pathway = create_pathway_visualization(pathway_results)
    st.plotly_chart(fig_pathway, use_container_width=True)
```

### Page 5: RE100 Strategy ⚡

**Purpose**: Renewable energy procurement optimization

**Key Features**:
- Renewable energy mix optimization
- LCOE comparison across technologies
- PPA vs. on-site generation analysis
- Implementation timeline and CAPEX schedule
- Regional renewable resource assessment

**Implementation**:
```python
def render_re100_strategy_page():
    st.title("⚡ RE100 Strategy Optimization")
    
    # Strategy configuration
    col1, col2 = st.columns(2)
    
    with col1:
        target_pct = st.slider("Renewable Energy Target", 0, 100, 100, 5, "%")
        target_year = st.slider("Target Year", 2025, 2050, 2030)
    
    with col2:
        procurement_preferences = st.multiselect(
            "Preferred Procurement Methods",
            ["On-site Solar", "Wind PPAs", "Solar PPAs", "RECs", "Community Solar"],
            default=["On-site Solar", "Solar PPAs"]
        )
    
    # Run optimization
    if st.button("Optimize RE100 Strategy"):
        with st.spinner("Optimizing renewable energy strategy..."):
            re100_results = run_re100_optimization(target_pct, target_year, procurement_preferences)
            st.session_state.results['re100_strategy'] = re100_results
    
    # Display results
    if st.session_state.results.get('re100_strategy'):
        render_re100_results()
```

### Page 6: Results Dashboard 📈

**Purpose**: Integrated dashboard with all results

**Key Features**:
- Executive summary metrics
- Multi-scenario comparison
- Risk vs. opportunity matrix
- Financial impact waterfall charts
- Implementation roadmap timeline

**Implementation**:
```python
def render_results_dashboard():
    st.title("📈 Climate Risk & Strategy Dashboard")
    
    # Executive summary cards
    render_executive_summary_cards()
    
    # Risk-Opportunity Matrix
    fig_matrix = create_risk_opportunity_matrix()
    st.plotly_chart(fig_matrix, use_container_width=True)
    
    # Financial impact waterfall
    fig_waterfall = create_financial_impact_waterfall()
    st.plotly_chart(fig_waterfall, use_container_width=True)
    
    # Implementation roadmap
    st.subheader("Implementation Roadmap")
    fig_timeline = create_implementation_timeline()
    st.plotly_chart(fig_timeline, use_container_width=True)
```

### Page 7: Reports & Export 📑

**Purpose**: Generate and download comprehensive reports

**Key Features**:
- Automated report generation (PDF, Word, Excel)
- Customizable report templates
- Data export in multiple formats
- Email delivery options
- Regulatory compliance formatting

## 3. Interactive Components Library

### Chart Components (using Plotly)

```python
def create_interactive_macc_chart(macc_df):
    """Interactive MACC curve with hover details and selection"""
    
    fig = go.Figure()
    
    # Add bars for each abatement option
    fig.add_trace(go.Bar(
        x=macc_df['cumulative_abatement'],
        y=macc_df['lcoa_usd_per_tco2'],
        text=macc_df['technology'],
        textposition='auto',
        hovertemplate='<b>%{text}</b><br>' +
                      'Cost: $%{y:.0f}/tCO2e<br>' +
                      'Abatement: %{customdata:.0f} tCO2e/year<br>' +
                      'CAPEX: $%{customdata2:.0f}M<extra></extra>',
        customdata=macc_df['annual_abatement_potential'],
        customdata2=macc_df['total_capex_required'] / 1e6,
        marker_color=['green' if x < 0 else 'red' for x in macc_df['lcoa_usd_per_tco2']]
    ))
    
    fig.update_layout(
        title="Marginal Abatement Cost Curve",
        xaxis_title="Cumulative Abatement Potential (tCO2e/year)",
        yaxis_title="Levelized Cost of Abatement ($/tCO2e)",
        hovermode='closest'
    )
    
    return fig

def create_geographic_risk_map(facilities_df, risk_df):
    """Interactive map showing geographic risk distribution"""
    
    fig = px.scatter_mapbox(
        facilities_df.merge(risk_df, on='facility_id'),
        lat='latitude',
        lon='longitude',
        color='risk_score',
        size='annual_emissions_tco2',
        hover_data=['facility_name', 'country', 'annual_cost'],
        color_continuous_scale='RdYlGn_r',
        mapbox_style='open-street-map',
        zoom=2
    )
    
    fig.update_layout(height=600)
    return fig
```

### Data Table Components

```python
def render_project_selection_table(macc_df):
    """Interactive table for project selection with filtering"""
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        max_cost = st.slider("Max Cost ($/tCO2e)", 0, 500, 200)
    with col2:
        min_abatement = st.slider("Min Abatement (tCO2e)", 0, 10000, 1000)
    with col3:
        sectors = st.multiselect("Sectors", macc_df['sector'].unique())
    
    # Apply filters
    filtered_df = macc_df[
        (macc_df['lcoa_usd_per_tco2'] <= max_cost) &
        (macc_df['annual_abatement_potential'] >= min_abatement) &
        (macc_df['sector'].isin(sectors) if sectors else True)
    ]
    
    # Selection interface
    selected_projects = st.data_editor(
        filtered_df[['project_id', 'technology', 'sector', 'lcoa_usd_per_tco2', 
                    'annual_abatement_potential', 'total_capex_required']],
        column_config={
            "select": st.column_config.CheckboxColumn("Select", default=False)
        },
        hide_index=True
    )
    
    return selected_projects
```

## 4. Real-time Processing & Caching

### Background Processing
```python
@st.cache_data
def run_transition_risk_analysis(facilities_df, carbon_prices_df, scenarios):
    """Cached transition risk analysis"""
    # Implementation with progress tracking
    pass

@st.cache_data  
def run_macc_analysis(facilities_df, abatement_projects_df):
    """Cached MACC generation"""
    # Implementation
    pass

# Progress tracking for long operations
def run_analysis_with_progress(analysis_func, *args, **kwargs):
    """Run analysis with progress bar"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Simulate progress updates (replace with actual progress tracking)
    for i in range(100):
        progress_bar.progress((i + 1) / 100)
        status_text.text(f'Progress: {i+1}%')
        time.sleep(0.01)
    
    result = analysis_func(*args, **kwargs)
    
    progress_bar.empty()
    status_text.empty()
    
    return result
```

## 5. Deployment Strategy

### Development Environment
```bash
# Local development setup
pip install streamlit plotly pandas numpy openpyxl
streamlit run main.py --server.port 8501
```

### Production Deployment Options

1. **Streamlit Community Cloud** (Easiest)
   - Connect GitHub repository
   - Automatic deployment on push
   - Free tier available

2. **Docker Containerization**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

3. **Cloud Platforms**
   - AWS ECS/Fargate
   - Google Cloud Run  
   - Azure Container Instances

### Performance Optimization
- Implement caching for expensive computations
- Use session state efficiently
- Optimize DataFrame operations
- Implement lazy loading for large datasets
- Add connection pooling for database access

This implementation plan provides a comprehensive, professional web interface that transforms your climate risk tool into an accessible, interactive application suitable for enterprise use.