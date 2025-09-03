"""
Physical Risk Assessment Page - Climate Risk Assessment Tool
Integrates the Physical Risk Assessment module
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from physical_risk_assessment import PhysicalRiskAssessment

st.set_page_config(page_title="Physical Risk", page_icon="🌪️", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .risk-card {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 5px solid;
    }
    
    .risk-critical {
        background-color: #f8d7da;
        color: #721c24;
        border-left-color: #dc3545;
    }
    
    .risk-high {
        background-color: #fff3cd;
        color: #856404;
        border-left-color: #ffc107;
    }
    
    .risk-medium {
        background-color: #d1ecf1;
        color: #0c5460;
        border-left-color: #17a2b8;
    }
    
    .risk-low {
        background-color: #d4edda;
        color: #155724;
        border-left-color: #28a745;
    }
</style>
""", unsafe_allow_html=True)

def create_risk_distribution_chart(risk_df):
    """Create risk level distribution pie chart"""
    
    risk_counts = risk_df['overall_risk_level'].value_counts()
    colors = ['#dc3545', '#ffc107', '#17a2b8', '#28a745', '#6c757d']
    
    fig = go.Figure(data=[go.Pie(
        labels=risk_counts.index,
        values=risk_counts.values,
        hole=.3,
        marker_colors=colors[:len(risk_counts)]
    )])
    
    fig.update_traces(textinfo='label+percent+value')
    fig.update_layout(
        title="Physical Risk Distribution",
        height=400
    )
    
    return fig

def create_country_risk_chart(risk_df):
    """Create country risk comparison chart"""
    
    country_risk = risk_df.groupby('country').agg({
        'overall_risk_score': 'mean',
        'facility_id': 'count'
    }).rename(columns={'facility_id': 'facility_count'})
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=country_risk.index,
        y=country_risk['overall_risk_score'],
        text=[f"{score:.2f}" for score in country_risk['overall_risk_score']],
        textposition='auto',
        marker_color=px.colors.sequential.Reds_r
    ))
    
    fig.update_layout(
        title="Average Physical Risk by Country",
        xaxis_title="Country",
        yaxis_title="Average Risk Score",
        height=400
    )
    
    return fig

def create_risk_heatmap(risk_df):
    """Create risk heatmap for facilities and hazards"""
    
    # Get hazard columns
    hazard_cols = [col for col in risk_df.columns if col.endswith('_risk_score') and col != 'overall_risk_score']
    hazard_names = [col.replace('_risk_score', '').title() for col in hazard_cols]
    
    if not hazard_cols:
        return None
    
    # Select top 10 highest risk facilities
    top_facilities = risk_df.nlargest(min(10, len(risk_df)), 'overall_risk_score')
    
    # Create heatmap data
    heatmap_data = []
    facility_names = []
    
    for _, facility in top_facilities.iterrows():
        facility_risks = [facility[col] for col in hazard_cols]
        heatmap_data.append(facility_risks)
        facility_names.append(f"{facility['facility_id']} ({facility['country']})")
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=hazard_names,
        y=facility_names,
        colorscale='Reds',
        showscale=True
    ))
    
    fig.update_layout(
        title="Risk Heatmap - Top Risk Facilities",
        xaxis_title="Hazard Type",
        yaxis_title="Facility",
        height=500
    )
    
    return fig

def create_risk_vs_value_scatter(risk_df):
    """Create risk vs asset value scatter plot"""
    
    fig = go.Figure()
    
    # Color by risk level
    risk_colors = {
        'CRITICAL': '#dc3545',
        'HIGH': '#ffc107', 
        'MEDIUM': '#17a2b8',
        'LOW': '#28a745',
        'MINIMAL': '#6c757d'
    }
    
    for risk_level in risk_df['overall_risk_level'].unique():
        subset = risk_df[risk_df['overall_risk_level'] == risk_level]
        
        fig.add_trace(go.Scatter(
            x=subset['overall_risk_score'],
            y=subset['asset_value_usd'] / 1e6,
            mode='markers',
            name=risk_level,
            marker=dict(
                color=risk_colors.get(risk_level, '#6c757d'),
                size=10,
                opacity=0.7
            ),
            text=[f"{row['facility_id']}<br>{row['country']}" for _, row in subset.iterrows()],
            hovertemplate='<b>%{text}</b><br>' +
                          'Risk Score: %{x:.2f}<br>' +
                          'Asset Value: $%{y:.1f}M<extra></extra>'
        ))
    
    fig.update_layout(
        title="Physical Risk vs Asset Value",
        xaxis_title="Overall Risk Score",
        yaxis_title="Asset Value (Million USD)",
        height=500
    )
    
    return fig

def create_geographic_risk_map(risk_df):
    """Create geographic risk distribution map"""
    
    if 'latitude' not in risk_df.columns or 'longitude' not in risk_df.columns:
        return None
    
    # Size by asset value, color by risk score
    fig = go.Figure()
    
    fig.add_trace(go.Scattermapbox(
        lat=risk_df['latitude'],
        lon=risk_df['longitude'],
        mode='markers',
        marker=dict(
            size=np.sqrt(risk_df['asset_value_usd'] / 1e6) * 2 + 5,
            color=risk_df['overall_risk_score'],
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title="Risk Score"),
            opacity=0.8
        ),
        text=[f"{row['facility_id']}<br>{row['country']}<br>Risk: {row['overall_risk_level']}" 
              for _, row in risk_df.iterrows()],
        hovertemplate='<b>%{text}</b><br>' +
                      'Risk Score: %{marker.color:.2f}<br>' +
                      'Asset Value: $%{customdata:.1f}M<extra></extra>',
        customdata=risk_df['asset_value_usd'] / 1e6
    ))
    
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=45, lon=0),
            zoom=2
        ),
        title="Geographic Risk Distribution",
        height=500
    )
    
    return fig

def render_physical_risk_page():
    """Main physical risk analysis page"""
    
    st.title("🌪️ Physical Risk Assessment")
    
    # Check if data is uploaded
    if not st.session_state.get('data_uploaded', False):
        st.warning("⚠️ Please upload facilities data first!")
        if st.button("📊 Go to Data Upload"):
            st.switch_page("pages/01_📊_Data_Upload.py")
        return
    
    facilities_df = st.session_state.facilities_df
    
    st.markdown("### 🎯 Physical Risk Configuration")
    
    # Configuration panel
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"📊 **Portfolio Summary**\n\n"
               f"• Facilities: {len(facilities_df)}\n"
               f"• Countries: {facilities_df['country'].nunique() if 'country' in facilities_df.columns else 'N/A'}\n"
               f"• Total Assets: ${facilities_df['asset_value_usd'].sum()/1e9:.1f}B" if 'asset_value_usd' in facilities_df.columns else "")
    
    with col2:
        st.markdown("""
        **Risk Categories Assessed:**
        - 🌊 Flood Risk
        - 🔥 Heat Stress  
        - 🌵 Water Stress/Drought
        - 🌪️ Storm/Hurricane
        - 🔥 Wildfire
        - 🏗️ Earthquake (where applicable)
        """)
    
    # Generate physical risk analysis
    if st.button("🚀 Generate Physical Risk Assessment", type="primary"):
        with st.spinner("Assessing physical risks..."):
            try:
                # Initialize Physical Risk Assessment
                pra = PhysicalRiskAssessment(facilities_df)
                
                # Calculate risk scores
                risk_df = pra.calculate_risk_scores()
                
                # Generate risk summary
                summary = pra.generate_risk_summary(risk_df)
                
                # Create risk register
                risk_register = pra.create_risk_register(risk_df)
                
                # Store results in session state
                st.session_state.analysis_results['physical_risk'] = {
                    'risk_df': risk_df,
                    'summary': summary,
                    'risk_register': risk_register
                }
                
                st.success("✅ Physical risk assessment completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Error generating physical risk assessment: {str(e)}")
                return
    
    # Display results if available
    if st.session_state.analysis_results.get('physical_risk'):
        render_physical_risk_results()

def render_physical_risk_results():
    """Render physical risk assessment results"""
    
    risk_data = st.session_state.analysis_results['physical_risk']
    risk_df = risk_data['risk_df']
    summary = risk_data['summary']
    risk_register = risk_data['risk_register']
    
    st.markdown("---")
    st.markdown("## 📊 Physical Risk Assessment Results")
    
    # Executive summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "High Risk Facilities",
            f"{summary['high_risk_facilities']}/{summary['total_facilities']}",
            f"{summary['high_risk_percentage']:.1f}%",
            help="Facilities with HIGH or CRITICAL risk levels"
        )
    
    with col2:
        st.metric(
            "Total Potential Loss",
            f"${summary['total_potential_loss']/1e6:.0f}M",
            f"{summary['loss_as_percent_assets']:.1f}% of assets",
            help="Maximum potential financial loss from physical risks"
        )
    
    with col3:
        st.metric(
            "Highest Risk Country",
            summary['highest_risk_country'],
            help="Country with highest average risk score"
        )
    
    with col4:
        most_critical_hazard = max(summary['top_risks_by_hazard'], 
                                 key=lambda x: summary['top_risks_by_hazard'][x]['total_exposure'])
        st.metric(
            "Top Risk Category",
            most_critical_hazard.title(),
            f"${summary['top_risks_by_hazard'][most_critical_hazard]['total_exposure']/1e6:.0f}M exposure",
            help="Risk category with highest financial exposure"
        )
    
    # Risk level distribution
    risk_distribution = summary['risk_distribution']
    if risk_distribution:
        st.markdown("### 📊 Risk Level Distribution")
        
        # Display risk cards
        cols = st.columns(len(risk_distribution))
        risk_colors = {
            'CRITICAL': ('risk-critical', '🔴'),
            'HIGH': ('risk-high', '🟡'),
            'MEDIUM': ('risk-medium', '🔵'),
            'LOW': ('risk-low', '🟢'),
            'MINIMAL': ('risk-low', '⚪')
        }
        
        for i, (level, count) in enumerate(risk_distribution.items()):
            color_class, emoji = risk_colors.get(level, ('', '⚪'))
            with cols[i]:
                st.markdown(f"""
                <div class="risk-card {color_class}">
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem;">{emoji}</div>
                        <div style="font-size: 1.2rem; font-weight: bold;">{level}</div>
                        <div style="font-size: 2rem; font-weight: bold;">{count}</div>
                        <div style="font-size: 0.9rem;">facilities</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Interactive visualizations
    st.markdown("### 📈 Risk Analysis Visualizations")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Risk Distribution", "🗺️ Geographic Risk", "🔥 Risk Heatmap", "💰 Risk vs Value"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_risk_distribution_chart(risk_df), use_container_width=True)
        
        with col2:
            st.plotly_chart(create_country_risk_chart(risk_df), use_container_width=True)
    
    with tab2:
        geo_map = create_geographic_risk_map(risk_df)
        if geo_map:
            st.plotly_chart(geo_map, use_container_width=True)
        else:
            st.info("Geographic coordinates not available for mapping.")
    
    with tab3:
        heatmap = create_risk_heatmap(risk_df)
        if heatmap:
            st.plotly_chart(heatmap, use_container_width=True)
        else:
            st.info("Risk heatmap data not available.")
    
    with tab4:
        st.plotly_chart(create_risk_vs_value_scatter(risk_df), use_container_width=True)
    
    # Top risks table
    st.markdown("### 🔥 Top 10 Highest Risks")
    
    if not risk_register.empty:
        # Format the risk register for display
        display_register = risk_register.head(10).copy()
        
        # Format columns for better display
        display_register['Potential Loss'] = (display_register['potential_loss_usd'] / 1e6).round(1).astype(str) + 'M'
        display_register['Mitigation Cost'] = (display_register['mitigation_cost_usd'] / 1e6).round(1).astype(str) + 'M'
        display_register['ROI'] = display_register['roi_mitigation'].round(1).astype(str) + 'x'
        
        display_cols = ['facility_id', 'country', 'hazard_type', 'risk_level', 
                       'Potential Loss', 'Mitigation Cost', 'ROI']
        display_names = ['Facility', 'Country', 'Hazard', 'Risk Level', 
                        'Potential Loss ($)', 'Mitigation Cost ($)', 'Mitigation ROI']
        
        display_df = display_register[display_cols]
        display_df.columns = display_names
        
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No significant risks identified.")
    
    # Hazard-specific analysis
    st.markdown("### 🌊 Risk by Hazard Type")
    
    hazard_summary = []
    for hazard, data in summary['top_risks_by_hazard'].items():
        hazard_summary.append({
            'Hazard': hazard.title(),
            'Total Exposure ($M)': f"{data['total_exposure']/1e6:.1f}",
            'Top Facility': data['top_facility'],
            'Max Facility Loss ($M)': f"{data['top_facility_loss']/1e6:.1f}"
        })
    
    hazard_df = pd.DataFrame(hazard_summary)
    st.dataframe(hazard_df, use_container_width=True)
    
    # Strategic recommendations
    st.markdown("### 💡 Risk Management Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🚨 Immediate Actions")
        
        critical_risks = risk_register[risk_register['risk_level'] == 'CRITICAL'].head(3)
        if not critical_risks.empty:
            for _, risk in critical_risks.iterrows():
                st.markdown(f"""
                **{risk['facility_id']} - {risk['hazard_type']} Risk**
                - Potential loss: ${risk['potential_loss_usd']/1e6:.1f}M
                - Recommended: {risk['mitigation_description']}
                - Investment: ${risk['mitigation_cost_usd']/1e6:.1f}M (ROI: {risk['roi_mitigation']:.1f}x)
                """)
        else:
            st.success("✅ No critical risks requiring immediate action.")
    
    with col2:
        st.markdown("#### 📊 Portfolio Insights")
        
        # Calculate insights
        total_mitigation_cost = risk_register['mitigation_cost_usd'].sum()
        avg_roi = risk_register['roi_mitigation'].mean()
        high_roi_projects = len(risk_register[risk_register['roi_mitigation'] > 5])
        
        st.markdown(f"""
        - **Total Mitigation Investment**: ${total_mitigation_cost/1e6:.1f}M
        - **Average ROI**: {avg_roi:.1f}x return on mitigation investment
        - **High-ROI Opportunities**: {high_roi_projects} projects with >5x ROI
        - **Risk Concentration**: {len(risk_df[risk_df['country'] == summary['highest_risk_country']])} facilities in highest-risk country
        """)
        
        # Country diversification recommendation
        country_concentration = len(risk_df[risk_df['country'] == summary['highest_risk_country']]) / len(risk_df)
        if country_concentration > 0.5:
            st.warning(f"⚠️ High geographic concentration risk: {country_concentration*100:.0f}% of facilities in {summary['highest_risk_country']}")
    
    # Download results
    st.markdown("### 📥 Download Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download risk scores
        csv = risk_df.to_csv(index=False)
        st.download_button(
            label="📊 Risk Scores (CSV)",
            data=csv,
            file_name="physical_risk_scores.csv",
            mime="text/csv"
        )
    
    with col2:
        # Download risk register
        csv = risk_register.to_csv(index=False)
        st.download_button(
            label="📋 Risk Register (CSV)",
            data=csv,
            file_name="physical_risk_register.csv",
            mime="text/csv"
        )
    
    with col3:
        # Download summary report
        summary_report = generate_physical_risk_report(summary, risk_register)
        st.download_button(
            label="📑 Summary Report",
            data=summary_report,
            file_name="physical_risk_report.md",
            mime="text/markdown"
        )

def generate_physical_risk_report(summary, risk_register):
    """Generate markdown summary report"""
    
    report = f"""# Physical Risk Assessment Report

## Executive Summary

- **Total Facilities Assessed**: {summary['total_facilities']}
- **Total Asset Value**: ${summary['total_asset_value']/1e9:.1f} Billion
- **High/Critical Risk Facilities**: {summary['high_risk_facilities']} ({summary['high_risk_percentage']:.1f}%)
- **Total Potential Loss**: ${summary['total_potential_loss']/1e6:.1f} Million ({summary['loss_as_percent_assets']:.1f}% of assets)

## Geographic Risk Profile

- **Highest Risk Country**: {summary['highest_risk_country']}
- **Risk Distribution**: 
"""
    
    for level, count in summary['risk_distribution'].items():
        report += f"  - {level}: {count} facilities\n"
    
    report += f"""
## Top Risk Categories

"""
    
    for hazard, data in summary['top_risks_by_hazard'].items():
        report += f"""
### {hazard.title()} Risk
- **Total Exposure**: ${data['total_exposure']/1e6:.1f} Million
- **Highest Risk Facility**: {data['top_facility']}
- **Maximum Facility Loss**: ${data['top_facility_loss']/1e6:.1f} Million

"""
    
    report += f"""
## Top 10 Critical Risks

"""
    
    for i, (_, risk) in enumerate(risk_register.head(10).iterrows(), 1):
        report += f"""
### {i}. {risk['facility_id']} - {risk['hazard_type']} Risk
- **Risk Level**: {risk['risk_level']}
- **Potential Loss**: ${risk['potential_loss_usd']/1e6:.1f} Million
- **Recommended Mitigation**: {risk['mitigation_description']}
- **Mitigation Cost**: ${risk['mitigation_cost_usd']/1e6:.1f} Million
- **ROI on Mitigation**: {risk['roi_mitigation']:.1f}x

"""
    
    report += f"""
## Strategic Recommendations

1. **Immediate Action Required**: Focus on {len(risk_register[risk_register['risk_level']=='CRITICAL'])} critical risks
2. **Mitigation Investment**: Budget ${risk_register['mitigation_cost_usd'].sum()/1e6:.1f}M for risk mitigation measures  
3. **Geographic Diversification**: Consider risk concentration in {summary['highest_risk_country']}
4. **Insurance Review**: Evaluate coverage for ${summary['total_potential_loss']/1e6:.1f}M potential loss exposure

Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return report

def main():
    """Main function for physical risk page"""
    render_physical_risk_page()

if __name__ == "__main__":
    main()