"""
MACC Analysis Page - Climate Risk Assessment Tool
Integrates the MACC (Marginal Abatement Cost Curve) generator
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys
import io

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from generate_macc import MACCGenerator, create_sample_abatement_projects

st.set_page_config(page_title="MACC Analysis", page_icon="💰", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 0.5rem 0;
    }
    
    .success-card {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    
    .warning-card {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def create_interactive_macc_chart(macc_df):
    """Create interactive MACC chart using Plotly"""
    
    # Prepare data
    x_data = macc_df['cumulative_abatement'] / 1000  # Convert to ktCO2e
    y_data = macc_df['lcoa_usd_per_tco2']
    
    # Color based on cost savings vs cost
    colors = ['#28a745' if cost < 0 else '#ffc107' if cost < 100 else '#dc3545' 
             for cost in y_data]
    
    # Create bar chart
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(go.Bar(
        x=x_data,
        y=y_data,
        text=macc_df['technology'],
        textposition='auto',
        marker_color=colors,
        hovertemplate='<b>%{text}</b><br>' +
                      'Cost: $%{y:.0f}/tCO2e<br>' +
                      'Abatement: %{customdata[0]:,.0f} tCO2e/year<br>' +
                      'CAPEX: $%{customdata[1]:.0f}M<extra></extra>',
        customdata=np.column_stack((macc_df['annual_abatement_potential'],
                                   macc_df['total_capex_required'] / 1e6)),
        name='Abatement Projects'
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="black", 
                  annotation_text="Break-even line")
    
    # Update layout
    fig.update_layout(
        title="Marginal Abatement Cost Curve (MACC)",
        xaxis_title="Cumulative Abatement Potential (ktCO2e/year)",
        yaxis_title="Levelized Cost of Abatement ($/tCO2e)",
        showlegend=False,
        height=500,
        hovermode='closest'
    )
    
    return fig

def create_technology_breakdown_chart(macc_df):
    """Create technology breakdown pie chart"""
    
    sector_abatement = macc_df.groupby('sector')['annual_abatement_potential'].sum()
    
    fig = go.Figure(data=[go.Pie(
        labels=sector_abatement.index,
        values=sector_abatement.values,
        hole=.3,
        textinfo='label+percent'
    )])
    
    fig.update_layout(
        title="Abatement Potential by Sector",
        height=400
    )
    
    return fig

def create_cost_vs_abatement_scatter(macc_df):
    """Create cost vs abatement scatter plot"""
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=macc_df['annual_abatement_potential'] / 1000,
        y=macc_df['lcoa_usd_per_tco2'],
        mode='markers',
        marker=dict(
            size=np.sqrt(macc_df['total_capex_required'] / 1e6) * 5,  # Size by CAPEX
            color=macc_df['roi_percent'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="ROI (%)"),
            opacity=0.7
        ),
        text=macc_df['technology'],
        hovertemplate='<b>%{text}</b><br>' +
                      'Abatement: %{x:,.0f} ktCO2e/year<br>' +
                      'Cost: $%{y:.0f}/tCO2e<br>' +
                      'ROI: %{marker.color:.1f}%<extra></extra>'
    ))
    
    # Add quadrant lines
    fig.add_hline(y=0, line_dash="dash", line_color="gray", alpha=0.5)
    fig.add_vline(x=macc_df['annual_abatement_potential'].median() / 1000, 
                  line_dash="dash", line_color="gray", alpha=0.5)
    
    fig.update_layout(
        title="Cost vs Abatement Effectiveness",
        xaxis_title="Annual Abatement Potential (ktCO2e/year)",
        yaxis_title="Levelized Cost of Abatement ($/tCO2e)",
        height=500
    )
    
    return fig

def render_macc_analysis_page():
    """Main MACC analysis page"""
    
    st.title("💰 MACC (Marginal Abatement Cost Curve) Analysis")
    
    # Check if data is uploaded
    if not st.session_state.get('data_uploaded', False):
        st.warning("⚠️ Please upload facilities data first!")
        if st.button("📊 Go to Data Upload"):
            st.switch_page("pages/01_📊_Data_Upload.py")
        return
    
    facilities_df = st.session_state.facilities_df
    
    st.markdown("### 🎯 MACC Configuration")
    
    # Configuration panel
    col1, col2 = st.columns(2)
    
    with col1:
        discount_rate = st.slider(
            "Discount Rate (%)", 
            min_value=2, max_value=12, value=6, step=1,
            help="Discount rate for NPV calculations"
        ) / 100
    
    with col2:
        st.info(f"📊 **Portfolio Summary**\n\n"
               f"• Facilities: {len(facilities_df)}\n"
               f"• Countries: {facilities_df['country'].nunique() if 'country' in facilities_df.columns else 'N/A'}")
    
    # Generate MACC analysis
    if st.button("🚀 Generate MACC Analysis", type="primary"):
        with st.spinner("Generating MACC analysis..."):
            try:
                # Initialize MACC generator
                macc_gen = MACCGenerator(facilities_df, discount_rate=discount_rate)
                
                # Load sample abatement projects
                sample_projects = create_sample_abatement_projects()
                for project in sample_projects:
                    macc_gen.add_project(project)
                
                # Generate MACC curve
                macc_df = macc_gen.generate_macc_curve()
                
                # Store results in session state
                st.session_state.analysis_results['macc'] = {
                    'macc_df': macc_df,
                    'discount_rate': discount_rate,
                    'baseline_emissions': facilities_df.get('annual_emissions_tco2', 
                                        facilities_df.get('annual_emissions_scope1', 0) + 
                                        facilities_df.get('annual_emissions_scope2', 0)).sum()
                }
                
                st.success("✅ MACC analysis completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Error generating MACC analysis: {str(e)}")
                return
    
    # Display results if available
    if st.session_state.analysis_results.get('macc'):
        render_macc_results()

def render_macc_results():
    """Render MACC analysis results"""
    
    macc_data = st.session_state.analysis_results['macc']
    macc_df = macc_data['macc_df']
    baseline_emissions = macc_data.get('baseline_emissions', 0)
    
    st.markdown("---")
    st.markdown("## 📊 MACC Analysis Results")
    
    # Key metrics
    total_abatement = macc_df['annual_abatement_potential'].sum()
    total_capex = macc_df['total_capex_required'].sum()
    net_negative_projects = len(macc_df[macc_df['net_negative_cost']])
    avg_cost = macc_df['lcoa_usd_per_tco2'].mean()
    
    # Metrics dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Abatement Potential", 
            f"{total_abatement:,.0f} tCO2e/year",
            help="Total annual emission reduction potential"
        )
    
    with col2:
        st.metric(
            "Total Investment Required", 
            f"${total_capex/1e6:.1f}M",
            help="Total CAPEX required for all projects"
        )
    
    with col3:
        st.metric(
            "Cost-Saving Projects", 
            f"{net_negative_projects}/{len(macc_df)}",
            help="Projects with negative costs (profitable)"
        )
    
    with col4:
        st.metric(
            "Average Cost", 
            f"${avg_cost:.0f}/tCO2e",
            help="Average levelized cost of abatement"
        )
    
    # Additional insights
    if baseline_emissions > 0:
        reduction_potential = min(100, (total_abatement / baseline_emissions) * 100)
        
        if reduction_potential < 50:
            st.warning(f"⚠️ Current technologies can address {reduction_potential:.1f}% of baseline emissions. "
                      "Additional technologies may be needed for deeper decarbonization.")
        else:
            st.success(f"✅ Current technologies can address {reduction_potential:.1f}% of baseline emissions.")
    
    # Interactive visualizations
    st.markdown("### 📈 Interactive Visualizations")
    
    tab1, tab2, tab3 = st.tabs(["🔄 MACC Curve", "🏭 Sector Breakdown", "💡 Cost-Effectiveness"])
    
    with tab1:
        st.plotly_chart(create_interactive_macc_chart(macc_df), use_container_width=True)
        
        # Interpretation guide
        with st.expander("📖 How to Read the MACC Curve", expanded=False):
            st.markdown("""
            **Green bars (negative cost)**: These projects actually save money while reducing emissions. Prioritize these first!
            
            **Yellow bars (low cost)**: Cost-effective projects under $100/tCO2e. Good investment opportunities.
            
            **Red bars (high cost)**: Expensive projects above $100/tCO2e. Consider for long-term planning.
            
            **X-axis**: Shows cumulative emission reduction potential as you implement projects from left to right.
            
            **Y-axis**: Shows the cost per tonne of CO2 avoided for each project.
            """)
    
    with tab2:
        st.plotly_chart(create_technology_breakdown_chart(macc_df), use_container_width=True)
        
        # Sector analysis
        sector_analysis = macc_df.groupby('sector').agg({
            'annual_abatement_potential': 'sum',
            'total_capex_required': 'sum',
            'lcoa_usd_per_tco2': 'mean'
        }).round(1)
        
        sector_analysis.columns = ['Abatement (tCO2e/year)', 'CAPEX Required ($)', 'Avg Cost ($/tCO2e)']
        st.dataframe(sector_analysis, use_container_width=True)
    
    with tab3:
        st.plotly_chart(create_cost_vs_abatement_scatter(macc_df), use_container_width=True)
        
        st.markdown("""
        **Bubble size** represents CAPEX requirement. **Color** represents ROI.
        
        **Bottom-right quadrant**: High abatement, low cost (sweet spot!)
        **Top-right quadrant**: High abatement, high cost (consider for ambitious targets)
        **Bottom-left quadrant**: Low abatement, low cost (quick wins)
        **Top-left quadrant**: Low abatement, high cost (avoid unless strategic)
        """)
    
    # Project prioritization table
    st.markdown("### 🏆 Project Prioritization")
    
    # Sort by cost-effectiveness
    priority_df = macc_df.copy()
    priority_df['priority_score'] = calculate_priority_score(priority_df)
    priority_df = priority_df.sort_values('priority_score', ascending=False)
    
    # Display top projects
    display_cols = [
        'technology', 'sector', 'lcoa_usd_per_tco2', 'annual_abatement_potential',
        'total_capex_required', 'roi_percent', 'net_negative_cost'
    ]
    
    display_df = priority_df[display_cols].head(10).copy()
    display_df.columns = [
        'Technology', 'Sector', 'Cost ($/tCO2e)', 'Abatement (tCO2e/year)',
        'CAPEX ($)', 'ROI (%)', 'Cost Saving?'
    ]
    
    # Format numbers
    display_df['Cost ($/tCO2e)'] = display_df['Cost ($/tCO2e)'].round(0).astype(int)
    display_df['Abatement (tCO2e/year)'] = display_df['Abatement (tCO2e/year)'].round(0).astype(int)
    display_df['CAPEX ($)'] = (display_df['CAPEX ($)'] / 1e6).round(2).astype(str) + 'M'
    display_df['ROI (%)'] = display_df['ROI (%)'].round(1)
    
    st.dataframe(display_df, use_container_width=True)
    
    # Strategic recommendations
    st.markdown("### 💡 Strategic Recommendations")
    
    quick_wins = macc_df[macc_df['net_negative_cost']].copy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🚀 Quick Wins (Immediate ROI)")
        if not quick_wins.empty:
            for _, project in quick_wins.head(3).iterrows():
                st.markdown(f"""
                **{project['technology']}**
                - Saves ${-project['lcoa_usd_per_tco2']:.0f} per tonne
                - {project['annual_abatement_potential']:,.0f} tCO2e/year reduction
                - ${project['total_capex_required']/1e6:.1f}M investment
                """)
        else:
            st.info("No immediately profitable projects identified.")
    
    with col2:
        st.markdown("#### 🎯 Strategic Investments")
        strategic_projects = macc_df[
            (macc_df['lcoa_usd_per_tco2'] >= 0) & 
            (macc_df['lcoa_usd_per_tco2'] <= 100)
        ].nlargest(3, 'annual_abatement_potential')
        
        for _, project in strategic_projects.iterrows():
            st.markdown(f"""
            **{project['technology']}**
            - ${project['lcoa_usd_per_tco2']:.0f} per tonne
            - {project['annual_abatement_potential']:,.0f} tCO2e/year reduction
            - {project['roi_percent']:.1f}% ROI over lifetime
            """)
    
    # Download results
    st.markdown("### 📥 Download Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download MACC data
        csv = macc_df.to_csv(index=False)
        st.download_button(
            label="📊 Download MACC Data (CSV)",
            data=csv,
            file_name="macc_analysis_results.csv",
            mime="text/csv"
        )
    
    with col2:
        # Download summary report
        summary_report = generate_macc_summary_report(macc_df, baseline_emissions)
        st.download_button(
            label="📑 Download Summary Report",
            data=summary_report,
            file_name="macc_summary_report.md",
            mime="text/markdown"
        )

def calculate_priority_score(df):
    """Calculate priority score based on multiple factors"""
    
    # Normalize metrics
    cost_score = 1 - ((df['lcoa_usd_per_tco2'] + 200) / 400)  # Favor negative costs
    abatement_score = df['annual_abatement_potential'] / df['annual_abatement_potential'].max()
    roi_score = (df['roi_percent'] + 100) / 200  # Normalize ROI
    
    # Weighted priority score
    priority_score = (
        0.4 * cost_score +
        0.4 * abatement_score +
        0.2 * roi_score
    )
    
    return priority_score

def generate_macc_summary_report(macc_df, baseline_emissions):
    """Generate markdown summary report"""
    
    total_abatement = macc_df['annual_abatement_potential'].sum()
    total_capex = macc_df['total_capex_required'].sum()
    net_negative_projects = len(macc_df[macc_df['net_negative_cost']])
    
    report = f"""# MACC Analysis Summary Report

## Executive Summary

- **Total Abatement Potential**: {total_abatement:,.0f} tCO2e/year
- **Total Investment Required**: ${total_capex/1e6:.1f} Million
- **Cost-Saving Projects**: {net_negative_projects} out of {len(macc_df)}
- **Portfolio Coverage**: {min(100, total_abatement/baseline_emissions*100):.1f}% of baseline emissions

## Top 5 Recommended Projects

"""
    
    for i, (_, project) in enumerate(macc_df.head(5).iterrows(), 1):
        cost_desc = f"Saves ${-project['lcoa_usd_per_tco2']:.0f}/tCO2e" if project['lcoa_usd_per_tco2'] < 0 else f"Costs ${project['lcoa_usd_per_tco2']:.0f}/tCO2e"
        report += f"""
### {i}. {project['technology']}
- **Cost**: {cost_desc}
- **Abatement**: {project['annual_abatement_potential']:,.0f} tCO2e/year
- **Investment**: ${project['total_capex_required']/1e6:.1f} Million
- **Sector**: {project['sector']}
- **ROI**: {project['roi_percent']:.1f}% over lifetime

"""
    
    report += f"""
## Strategic Recommendations

1. **Prioritize Quick Wins**: Implement {net_negative_projects} cost-saving projects first
2. **Plan Major Investments**: Budget ${total_capex/1e6:.1f}M for full implementation
3. **Phased Approach**: Start with highest ROI projects and scale up
4. **Technology Focus**: Emphasize building efficiency and renewable energy projects

Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return report

def main():
    """Main function for MACC analysis page"""
    render_macc_analysis_page()

if __name__ == "__main__":
    main()