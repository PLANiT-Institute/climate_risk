"""
Results Dashboard Page - Climate Risk Assessment Tool
Integrated dashboard combining all analysis results
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
import sys

st.set_page_config(page_title="Results Dashboard", page_icon="📑", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .dashboard-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-big {
        font-size: 2rem;
        font-weight: bold;
        color: #007bff;
        text-align: center;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        text-align: center;
        margin-top: 0.5rem;
    }
    
    .section-header {
        color: #495057;
        border-bottom: 2px solid #dee2e6;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def create_executive_summary_metrics():
    """Create executive summary metrics dashboard"""
    
    # Check what analyses are available
    macc_results = st.session_state.analysis_results.get('macc')
    physical_risk_results = st.session_state.analysis_results.get('physical_risk')
    esg_results = st.session_state.analysis_results.get('esg_compliance')
    physical_risk_results = st.session_state.analysis_results.get('physical_risk')
    
    if not macc_results and not physical_risk_results:
        st.warning("⚠️ No analysis results available. Please run MACC or Physical Risk analysis first.")
        return
    
    st.markdown('<h3 class="section-header">🎯 Executive Summary</h3>', unsafe_allow_html=True)
    
    # Portfolio overview
    facilities_df = st.session_state.facilities_df
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-big">{len(facilities_df)}</div>
        <div class="metric-label">Total Facilities</div>
        """, unsafe_allow_html=True)
    
    with col2:
        countries = facilities_df['country'].nunique() if 'country' in facilities_df.columns else 0
        st.markdown(f"""
        <div class="metric-big">{countries}</div>
        <div class="metric-label">Countries</div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_assets = facilities_df['asset_value_usd'].sum() if 'asset_value_usd' in facilities_df.columns else 0
        st.markdown(f"""
        <div class="metric-big">${total_assets/1e9:.1f}B</div>
        <div class="metric-label">Total Assets</div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_emissions = facilities_df['annual_emissions_tco2'].sum() if 'annual_emissions_tco2' in facilities_df.columns else 0
        st.markdown(f"""
        <div class="metric-big">{total_emissions:,.0f}</div>
        <div class="metric-label">tCO2e/year</div>
        """, unsafe_allow_html=True)
    
    with col5:
        # Analysis completion status
        completed_analyses = sum([macc_results is not None, physical_risk_results is not None, esg_results is not None])
        st.markdown(f"""
        <div class="metric-big">{completed_analyses}/3</div>
        <div class="metric-label">Analyses Complete</div>
        """, unsafe_allow_html=True)

def create_risk_opportunity_matrix():
    """Create risk vs opportunity strategic matrix"""
    
    macc_results = st.session_state.analysis_results.get('macc')
    physical_risk_results = st.session_state.analysis_results.get('physical_risk')
    esg_results = st.session_state.analysis_results.get('esg_compliance')
    physical_risk_results = st.session_state.analysis_results.get('physical_risk')
    
    if not macc_results or not physical_risk_results:
        return None
    
    # Combine data by facility
    macc_df = macc_results['macc_df']
    risk_df = physical_risk_results['risk_df']
    
    # Calculate facility-level metrics
    facility_metrics = []
    
    for facility_id in risk_df['facility_id'].unique():
        # Get risk data
        facility_risk = risk_df[risk_df['facility_id'] == facility_id].iloc[0]
        
        # Get corresponding facility data
        facility_data = st.session_state.facilities_df[
            st.session_state.facilities_df['facility_id'] == facility_id
        ]
        
        if facility_data.empty:
            continue
            
        facility_data = facility_data.iloc[0]
        
        facility_metrics.append({
            'facility_id': facility_id,
            'risk_score': facility_risk['overall_risk_score'],
            'asset_value': facility_data.get('asset_value_usd', 0) / 1e6,  # Convert to millions
            'country': facility_data.get('country', 'Unknown'),
            'sector': facility_data.get('sector', 'Unknown')
        })
    
    metrics_df = pd.DataFrame(facility_metrics)
    
    if metrics_df.empty:
        return None
    
    # Create scatter plot
    fig = go.Figure()
    
    # Color by sector
    sectors = metrics_df['sector'].unique()
    colors = px.colors.qualitative.Set1[:len(sectors)]
    
    for i, sector in enumerate(sectors):
        sector_data = metrics_df[metrics_df['sector'] == sector]
        
        fig.add_trace(go.Scatter(
            x=sector_data['risk_score'],
            y=sector_data['asset_value'],
            mode='markers',
            name=sector,
            marker=dict(
                color=colors[i],
                size=12,
                opacity=0.7
            ),
            text=[f"{row['facility_id']}<br>{row['country']}" for _, row in sector_data.iterrows()],
            hovertemplate='<b>%{text}</b><br>' +
                          'Risk Score: %{x:.2f}<br>' +
                          'Asset Value: $%{y:.1f}M<extra></extra>'
        ))
    
    # Add quadrant lines
    risk_median = metrics_df['risk_score'].median()
    value_median = metrics_df['asset_value'].median()
    
    fig.add_hline(y=value_median, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=risk_median, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Add quadrant labels
    fig.add_annotation(x=risk_median*0.5, y=metrics_df['asset_value'].max()*0.9,
                      text="Low Risk<br>High Value", showarrow=False,
                      bgcolor="rgba(40, 167, 69, 0.3)", bordercolor="green")
    
    fig.add_annotation(x=risk_median*1.5, y=metrics_df['asset_value'].max()*0.9,
                      text="High Risk<br>High Value", showarrow=False,
                      bgcolor="rgba(255, 193, 7, 0.3)", bordercolor="orange")
    
    fig.update_layout(
        title="Risk vs Value Strategic Matrix",
        xaxis_title="Physical Risk Score",
        yaxis_title="Asset Value (Million USD)",
        height=500
    )
    
    return fig

def create_financial_impact_waterfall():
    """Create financial impact waterfall chart"""
    
    macc_results = st.session_state.analysis_results.get('macc')
    physical_risk_results = st.session_state.analysis_results.get('physical_risk')
    esg_results = st.session_state.analysis_results.get('esg_compliance')
    physical_risk_results = st.session_state.analysis_results.get('physical_risk')
    
    if not macc_results or not physical_risk_results:
        return None
    
    # Calculate components
    baseline_value = st.session_state.facilities_df['asset_value_usd'].sum() / 1e6
    
    # Physical risk potential loss
    physical_loss = physical_risk_results['summary']['total_potential_loss'] / 1e6
    
    # MACC investment required
    macc_investment = macc_results['macc_df']['total_capex_required'].sum() / 1e6
    
    # Net cost savings from MACC
    cost_saving_projects = macc_results['macc_df'][macc_results['macc_df']['net_negative_cost']]
    annual_savings = 0
    if not cost_saving_projects.empty:
        for _, project in cost_saving_projects.iterrows():
            annual_savings += abs(project['lcoa_usd_per_tco2']) * project['annual_abatement_potential']
    annual_savings = annual_savings / 1e6  # Convert to millions
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        name="Financial Impact",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Current Asset Value", "Physical Risk Exposure", "MACC Investment", "Annual Cost Savings", "Net Position"],
        textposition="outside",
        text=[f"${baseline_value:.0f}M", f"-${physical_loss:.0f}M", f"-${macc_investment:.0f}M", 
              f"+${annual_savings:.0f}M/year", f"${baseline_value - physical_loss - macc_investment:.0f}M"],
        y=[baseline_value, -physical_loss, -macc_investment, annual_savings*10, 0],  # Scale annual savings for visibility
        connector={"line":{"color":"rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title="Financial Impact Analysis",
        showlegend=False,
        height=400
    )
    
    return fig

def create_implementation_timeline():
    """Create implementation timeline visualization"""
    
    macc_results = st.session_state.analysis_results.get('macc')
    physical_risk_results = st.session_state.analysis_results.get('physical_risk')
    esg_results = st.session_state.analysis_results.get('esg_compliance')
    
    if not macc_results:
        return None
    
    # Create simple timeline based on MACC priorities
    macc_df = macc_results['macc_df'].copy()
    
    # Sort by cost-effectiveness and assign implementation years
    macc_df['implementation_year'] = 2025 + (macc_df['rank'] - 1) // 2  # 2 projects per year
    macc_df['cumulative_investment'] = macc_df['total_capex_required'].cumsum() / 1e6
    
    # Group by year
    timeline_data = macc_df.groupby('implementation_year').agg({
        'total_capex_required': 'sum',
        'annual_abatement_potential': 'sum',
        'technology': lambda x: ', '.join(x[:2])  # Show first 2 technologies
    }).reset_index()
    
    timeline_data['annual_investment'] = timeline_data['total_capex_required'] / 1e6
    timeline_data['cumulative_investment'] = timeline_data['annual_investment'].cumsum()
    
    # Create dual-axis chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Annual investment bars
    fig.add_trace(
        go.Bar(x=timeline_data['implementation_year'], y=timeline_data['annual_investment'],
               name="Annual Investment", marker_color='lightblue'),
        secondary_y=False
    )
    
    # Cumulative abatement line
    fig.add_trace(
        go.Scatter(x=timeline_data['implementation_year'], y=timeline_data['annual_abatement_potential']/1000,
                  mode='lines+markers', name="Annual Abatement", line=dict(color='red', width=3)),
        secondary_y=True
    )
    
    fig.update_xaxes(title_text="Implementation Year")
    fig.update_yaxes(title_text="Annual Investment (Million USD)", secondary_y=False)
    fig.update_yaxes(title_text="Annual Abatement (ktCO2e/year)", secondary_y=True)
    fig.update_layout(title="Implementation Timeline", height=400)
    
    return fig

def render_results_dashboard():
    """Main results dashboard"""
    
    st.title("📑 Results Dashboard")
    st.markdown("Comprehensive overview of your climate risk assessment and decarbonization strategy.")
    
    # Check if any analyses are complete
    macc_results = st.session_state.analysis_results.get('macc')
    physical_risk_results = st.session_state.analysis_results.get('physical_risk')
    esg_results = st.session_state.analysis_results.get('esg_compliance')
    physical_risk_results = st.session_state.analysis_results.get('physical_risk')
    
    if not macc_results and not physical_risk_results:
        st.warning("⚠️ No analysis results available yet.")
        st.markdown("### 🚀 Get Started")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💰 Run MACC Analysis", use_container_width=True):
                st.switch_page("pages/03_💰_MACC_Analysis.py")
        
        with col2:
            if st.button("🌪️ Run Physical Risk Assessment", use_container_width=True):
                st.switch_page("pages/04_🌪️_Physical_Risk.py")
        
        return
    
    # Executive summary
    create_executive_summary_metrics()
    
    # Analysis status
    st.markdown("---")
    st.markdown('<h3 class="section-header">📊 Analysis Status</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if macc_results:
            st.success("✅ **MACC Analysis Complete**")
            macc_df = macc_results['macc_df']
            st.markdown(f"""
            - **Projects Analyzed**: {len(macc_df)}
            - **Total Abatement**: {macc_df['annual_abatement_potential'].sum():,.0f} tCO2e/year
            - **Investment Required**: ${macc_df['total_capex_required'].sum()/1e6:.1f}M
            - **Cost-Saving Projects**: {len(macc_df[macc_df['net_negative_cost']])}
            """)
        else:
            st.info("⏳ **MACC Analysis Pending**")
            if st.button("🚀 Run MACC Analysis"):
                st.switch_page("pages/03_💰_MACC_Analysis.py")
    
    with col2:
        if physical_risk_results:
            st.success("✅ **Physical Risk Assessment Complete**")
            summary = physical_risk_results['summary']
            st.markdown(f"""
            - **Facilities Assessed**: {summary['total_facilities']}
            - **High Risk Facilities**: {summary['high_risk_facilities']}
            - **Total Potential Loss**: ${summary['total_potential_loss']/1e6:.0f}M
            - **Top Risk Country**: {summary['highest_risk_country']}
            """)
        else:
            st.info("⏳ **Physical Risk Assessment Pending**")
            if st.button("🚀 Run Physical Risk Assessment"):
                st.switch_page("pages/04_🌪️_Physical_Risk.py")
    
    # Strategic visualizations (only if both analyses are complete)
    if macc_results and physical_risk_results:
        st.markdown("---")
        st.markdown('<h3 class="section-header">📈 Strategic Analysis</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            risk_opportunity_fig = create_risk_opportunity_matrix()
            if risk_opportunity_fig:
                st.plotly_chart(risk_opportunity_fig, use_container_width=True)
        
        with col2:
            waterfall_fig = create_financial_impact_waterfall()
            if waterfall_fig:
                st.plotly_chart(waterfall_fig, use_container_width=True)
    
    # Implementation timeline
    if macc_results:
        st.markdown("---")
        st.markdown('<h3 class="section-header">🛣️ Implementation Roadmap</h3>', unsafe_allow_html=True)
        
        timeline_fig = create_implementation_timeline()
        if timeline_fig:
            st.plotly_chart(timeline_fig, use_container_width=True)
    
    # Key insights and recommendations
    st.markdown("---")
    st.markdown('<h3 class="section-header">💡 Key Insights & Recommendations</h3>', unsafe_allow_html=True)
    
    insights_col1, insights_col2 = st.columns(2)
    
    with insights_col1:
        st.markdown("#### 🎯 Strategic Priorities")
        
        priorities = []
        
        if macc_results:
            macc_df = macc_results['macc_df']
            cost_saving_projects = len(macc_df[macc_df['net_negative_cost']])
            if cost_saving_projects > 0:
                priorities.append(f"✅ Implement {cost_saving_projects} cost-saving technologies immediately")
            
            high_impact_low_cost = len(macc_df[(macc_df['lcoa_usd_per_tco2'] < 100) & 
                                              (macc_df['annual_abatement_potential'] > macc_df['annual_abatement_potential'].median())])
            if high_impact_low_cost > 0:
                priorities.append(f"📈 Focus on {high_impact_low_cost} high-impact, low-cost projects")
        
        if physical_risk_results:
            summary = physical_risk_results['summary']
            if summary['high_risk_facilities'] > 0:
                priorities.append(f"🚨 Address {summary['high_risk_facilities']} high-risk facilities urgently")
            
            # Check for geographic concentration
            facilities_df = st.session_state.facilities_df
            if 'country' in facilities_df.columns:
                country_concentration = facilities_df['country'].value_counts().iloc[0] / len(facilities_df)
                if country_concentration > 0.5:
                    priorities.append(f"🌍 Consider geographic diversification (currently {country_concentration*100:.0f}% in one country)")
        
        if not priorities:
            priorities.append("📊 Complete additional analyses for specific recommendations")
        
        for priority in priorities[:5]:  # Show top 5 priorities
            st.markdown(f"- {priority}")
    
    with insights_col2:
        st.markdown("#### 💰 Financial Summary")
        
        financial_summary = []
        
        if macc_results and physical_risk_results:
            total_investment = macc_results['macc_df']['total_capex_required'].sum()
            total_risk_exposure = physical_risk_results['summary']['total_potential_loss']
            
            financial_summary.append(f"💸 **Risk Exposure**: ${total_risk_exposure/1e6:.0f}M potential loss")
            financial_summary.append(f"💰 **Investment Needed**: ${total_investment/1e6:.0f}M for decarbonization")
            
            # Calculate potential savings
            cost_saving_projects = macc_results['macc_df'][macc_results['macc_df']['net_negative_cost']]
            if not cost_saving_projects.empty:
                annual_savings = 0
                for _, project in cost_saving_projects.iterrows():
                    annual_savings += abs(project['lcoa_usd_per_tco2']) * project['annual_abatement_potential']
                financial_summary.append(f"💚 **Annual Savings**: ${annual_savings/1e6:.0f}M from profitable projects")
            
            # ROI calculation
            if total_investment > 0:
                roi_years = total_investment / annual_savings if annual_savings > 0 else float('inf')
                if roi_years < 10:
                    financial_summary.append(f"📊 **Payback Period**: {roi_years:.1f} years for profitable projects")
        
        if not financial_summary:
            financial_summary.append("📊 Complete analyses to view financial summary")
        
        for summary_item in financial_summary:
            st.markdown(f"- {summary_item}")
    
    # Download comprehensive report
    st.markdown("---")
    st.markdown('<h3 class="section-header">📥 Export Results</h3>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Download Executive Summary", use_container_width=True):
            executive_summary = generate_executive_summary()
            st.download_button(
                label="💾 Download Summary (PDF)",
                data=executive_summary,
                file_name="climate_risk_executive_summary.md",
                mime="text/markdown",
                use_container_width=True
            )
    
    with col2:
        if macc_results:
            macc_csv = macc_results['macc_df'].to_csv(index=False)
            st.download_button(
                label="💰 Download MACC Results",
                data=macc_csv,
                file_name="macc_results.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        if physical_risk_results:
            risk_csv = physical_risk_results['risk_df'].to_csv(index=False)
            st.download_button(
                label="🌪️ Download Risk Assessment",
                data=risk_csv,
                file_name="physical_risk_results.csv",
                mime="text/csv",
                use_container_width=True
            )

def generate_executive_summary():
    """Generate comprehensive executive summary"""
    
    facilities_df = st.session_state.facilities_df
    macc_results = st.session_state.analysis_results.get('macc')
    physical_risk_results = st.session_state.analysis_results.get('physical_risk')
    esg_results = st.session_state.analysis_results.get('esg_compliance')
    physical_risk_results = st.session_state.analysis_results.get('physical_risk')
    
    report = f"""# Climate Risk Assessment - Executive Summary

## Portfolio Overview

- **Total Facilities**: {len(facilities_df)}
- **Countries**: {facilities_df['country'].nunique() if 'country' in facilities_df.columns else 'N/A'}
- **Total Asset Value**: ${facilities_df['asset_value_usd'].sum()/1e9:.1f} Billion
- **Annual Emissions**: {facilities_df['annual_emissions_tco2'].sum():,.0f} tCO2e

## Analysis Results

"""
    
    if macc_results:
        macc_df = macc_results['macc_df']
        report += f"""### MACC Analysis
- **Technologies Analyzed**: {len(macc_df)}
- **Total Abatement Potential**: {macc_df['annual_abatement_potential'].sum():,.0f} tCO2e/year
- **Investment Required**: ${macc_df['total_capex_required'].sum()/1e6:.1f} Million
- **Cost-Saving Opportunities**: {len(macc_df[macc_df['net_negative_cost']])} projects

"""
    
    if physical_risk_results:
        summary = physical_risk_results['summary']
        report += f"""### Physical Risk Assessment
- **High Risk Facilities**: {summary['high_risk_facilities']} ({summary['high_risk_percentage']:.1f}%)
- **Total Risk Exposure**: ${summary['total_potential_loss']/1e6:.0f} Million
- **Highest Risk Country**: {summary['highest_risk_country']}

"""
    
    report += f"""## Strategic Recommendations

1. **Immediate Actions**: Focus on cost-saving decarbonization projects
2. **Risk Mitigation**: Address high-risk facilities with targeted investments
3. **Financial Planning**: Budget for comprehensive climate strategy implementation
4. **Monitoring**: Establish regular climate risk assessment updates

Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return report

def main():
    """Main function for results dashboard"""
    render_results_dashboard()

if __name__ == "__main__":
    main()