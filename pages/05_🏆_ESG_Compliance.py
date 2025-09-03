"""
ESG Compliance Page - Climate Risk Assessment Tool
Links technical analysis to ESG frameworks and business requirements
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from esg_compliance import ESGComplianceAssessment

st.set_page_config(page_title="ESG Compliance", page_icon="🏆", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .compliance-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .framework-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #495057;
        margin-bottom: 0.5rem;
    }
    
    .score-excellent { color: #28a745; font-weight: bold; }
    .score-good { color: #17a2b8; font-weight: bold; }
    .score-adequate { color: #ffc107; font-weight: bold; }
    .score-needs-improvement { color: #dc3545; font-weight: bold; }
    
    .benefit-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def create_esg_readiness_chart(assessment_data):
    """Create ESG readiness spider/radar chart"""
    
    categories = ['TCFD Compliance', 'SBTi Coverage', 'EU Taxonomy', 'CDP Score']
    
    scores = [
        assessment_data['tcfd_assessment'].get('overall_tcfd_score', 0),
        assessment_data['sbti_assessment'].get('abatement_coverage_pct', 0),
        assessment_data['eu_taxonomy_assessment'].get('taxonomy_alignment_percentage', 0),
        assessment_data['cdp_assessment'].get('estimated_cdp_score', 0)
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name='Current Performance',
        line_color='rgb(32, 120, 180)',
        fillcolor='rgba(32, 120, 180, 0.3)'
    ))
    
    # Add target/benchmark line
    target_scores = [85, 100, 70, 80]  # Industry benchmarks
    fig.add_trace(go.Scatterpolar(
        r=target_scores,
        theta=categories,
        fill=None,
        name='Industry Benchmark',
        line_color='rgb(255, 65, 54)',
        line_dash='dash'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="ESG Framework Compliance Overview"
    )
    
    return fig

def create_business_benefits_chart(benefits_data):
    """Create financial benefits waterfall chart"""
    
    financing = benefits_data['financing_benefits']
    categories = ['Green Bonds', 'Sustainability Loans', 'Insurance Savings']
    values = [
        financing['green_bond_potential'],
        financing['sustainability_linked_loan_savings'], 
        financing['insurance_premium_reduction']
    ]
    
    fig = go.Figure(go.Bar(
        x=categories,
        y=[v/1e6 for v in values],  # Convert to millions
        marker_color=['#2E8B57', '#4682B4', '#FF6347'],
        text=[f'${v/1e6:.1f}M' for v in values],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Annual Financial Benefits from ESG Compliance",
        yaxis_title="Annual Savings (Million USD)",
        showlegend=False
    )
    
    return fig

def create_compliance_timeline(assessment_data):
    """Create implementation timeline for compliance"""
    
    # Sample timeline based on assessment gaps
    timeline_data = []
    
    tcfd_score = assessment_data['tcfd_assessment'].get('overall_tcfd_score', 0)
    if tcfd_score < 80:
        timeline_data.append({
            'Task': 'TCFD Full Compliance',
            'Start': '2024-Q1',
            'Duration': 6,
            'Priority': 'High'
        })
    
    sbti_compliant = assessment_data['sbti_assessment'].get('sbti_compliant', False)
    if not sbti_compliant:
        timeline_data.append({
            'Task': 'SBTi Target Setting',
            'Start': '2024-Q2', 
            'Duration': 12,
            'Priority': 'Critical'
        })
    
    taxonomy_alignment = assessment_data['eu_taxonomy_assessment'].get('taxonomy_alignment_percentage', 0)
    if taxonomy_alignment < 50:
        timeline_data.append({
            'Task': 'EU Taxonomy Compliance',
            'Start': '2024-Q3',
            'Duration': 18,
            'Priority': 'Medium'
        })
    
    if timeline_data:
        df_timeline = pd.DataFrame(timeline_data)
        
        # Create Gantt-style chart
        color_map = {'Critical': 'red', 'High': 'orange', 'Medium': 'blue'}
        
        fig = px.timeline(df_timeline, 
                         x_start="Start", 
                         x_end="Duration",
                         y="Task",
                         color="Priority",
                         color_discrete_map=color_map,
                         title="ESG Compliance Implementation Roadmap")
        
        return fig
    
    return None

def render_tcfd_assessment(tcfd_data):
    """Render TCFD assessment section"""
    
    st.markdown("### 📋 TCFD (Task Force on Climate-related Financial Disclosures)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        score = tcfd_data.get('overall_tcfd_score', 0)
        level = tcfd_data.get('tcfd_compliance_level', 'Unknown')
        
        score_class = f"score-{level.lower().replace(' ', '-')}"
        
        st.markdown(f"""
        <div class="compliance-card">
            <div class="framework-header">TCFD Compliance Assessment</div>
            <p><strong>Overall Score:</strong> <span class="{score_class}">{score:.1f}/100</span></p>
            <p><strong>Compliance Level:</strong> <span class="{score_class}">{level}</span></p>
            <p><strong>Strategy Score:</strong> {tcfd_data.get('strategy_score', 0)}/100</p>
            <p><strong>Risk Management:</strong> {tcfd_data.get('risk_management_score', 0)}/100</p>
            <p><strong>Metrics & Targets:</strong> {tcfd_data.get('metrics_targets_score', 0)}/100</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        recommendations = tcfd_data.get('improvement_recommendations', [])
        if recommendations:
            st.markdown("**🎯 Improvement Recommendations:**")
            for rec in recommendations:
                st.markdown(f"• {rec}")

def render_sbti_assessment(sbti_data):
    """Render Science Based Targets assessment"""
    
    if sbti_data.get('status') == 'insufficient_data':
        st.warning("⚠️ MACC Analysis required for SBTi assessment")
        return
    
    st.markdown("### 🎯 SBTi (Science Based Targets Initiative)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_emissions = sbti_data.get('current_emissions_tco2', 0)
        st.metric("Current Emissions", f"{current_emissions:,.0f} tCO2e")
    
    with col2:
        target_emissions = sbti_data.get('target_emissions_2030_tco2', 0)
        st.metric("2030 Target", f"{target_emissions:,.0f} tCO2e")
    
    with col3:
        coverage = sbti_data.get('abatement_coverage_pct', 0)
        st.metric("Abatement Coverage", f"{coverage:.1f}%")
    
    # Compliance status
    compliant = sbti_data.get('sbti_compliant', False)
    if compliant:
        st.success("✅ **SBTi Compliant** - Available abatement technologies can meet science-based targets")
    else:
        gap = sbti_data.get('gap_analysis', 0)
        investment = sbti_data.get('investment_required_for_compliance', 0)
        st.error(f"❌ **Gap Identified** - Additional {gap:,.0f} tCO2e abatement needed")
        st.info(f"💰 **Investment Required**: ${investment/1e6:.1f}M for full compliance")

def render_eu_taxonomy_assessment(taxonomy_data):
    """Render EU Taxonomy assessment"""
    
    if taxonomy_data.get('status') == 'insufficient_data':
        st.warning("⚠️ MACC Analysis required for EU Taxonomy assessment")
        return
    
    st.markdown("### 🇪🇺 EU Taxonomy for Sustainable Activities")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        alignment = taxonomy_data.get('taxonomy_alignment_percentage', 0)
        st.metric("Taxonomy Alignment", f"{alignment:.1f}%")
    
    with col2:
        eligible_capex = taxonomy_data.get('taxonomy_eligible_capex_million_usd', 0)
        st.metric("Eligible Investment", f"${eligible_capex:.1f}M")
    
    with col3:
        green_financing = taxonomy_data.get('green_financing_eligible', False)
        status = "✅ Eligible" if green_financing else "❌ Not Eligible"
        st.metric("Green Financing", status)
    
    # Detailed breakdown
    if alignment > 0:
        st.success("🎉 **EU Taxonomy Opportunities Identified**")
        
        substantial_activities = taxonomy_data.get('substantial_contribution_activities', 0)
        st.info(f"📊 **{substantial_activities}** technologies qualify for substantial contribution to climate objectives")
        
        if taxonomy_data.get('dnsh_assessment_required', False):
            st.warning("⚠️ **Next Steps**: DNSH (Do No Significant Harm) assessment required for full compliance")

def render_cdp_assessment(cdp_data):
    """Render CDP scoring assessment"""
    
    st.markdown("### 🌍 CDP (Carbon Disclosure Project) Climate Change")
    
    col1, col2 = st.columns(2)
    
    with col1:
        score = cdp_data.get('estimated_cdp_score', 0)
        grade = cdp_data.get('estimated_cdp_grade', 'D')
        
        grade_colors = {'A': '#2E8B57', 'A-': '#4682B4', 'B': '#FFD700', 'B-': '#FFA500', 'C': '#FF6347', 'D': '#DC143C'}
        grade_color = grade_colors.get(grade, '#666')
        
        st.markdown(f"""
        <div class="compliance-card">
            <div class="framework-header">CDP Assessment</div>
            <p><strong>Estimated Score:</strong> {score:.1f}/100</p>
            <p><strong>Projected Grade:</strong> <span style="color: {grade_color}; font-size: 2rem; font-weight: bold;">{grade}</span></p>
            <p><strong>Improvement Potential:</strong> {cdp_data.get('improvement_potential', 0):.1f} points</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("**📊 Scoring Breakdown:**")
        categories = ['Governance', 'Risk & Opportunities', 'Business Strategy', 'Targets & Performance']
        scores = [
            cdp_data.get('governance_score', 0),
            cdp_data.get('risk_opportunities_score', 0),
            cdp_data.get('business_strategy_score', 0),
            cdp_data.get('targets_performance_score', 0)
        ]
        
        for cat, score in zip(categories, scores):
            st.metric(cat, f"{score}/100")

def render_business_benefits(benefits_data):
    """Render business benefits section"""
    
    st.markdown("### 💰 Business Benefits from ESG Compliance")
    
    # Financial benefits
    financing = benefits_data['financing_benefits']
    total_benefit = benefits_data.get('total_annual_financial_benefit', 0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="benefit-box">
            <h4>💚 Green Financing</h4>
            <p><strong>${financing['green_bond_potential']/1e6:.1f}M</strong> annual savings</p>
            <p>Green bonds & sustainability-linked loans</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="benefit-box">
            <h4>🛡️ Insurance Savings</h4>
            <p><strong>${financing['insurance_premium_reduction']/1e6:.1f}M</strong> annual reduction</p>
            <p>Lower climate risk premiums</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="benefit-box">
            <h4>📈 Market Access</h4>
            <p><strong>Enhanced</strong> opportunities</p>
            <p>ESG funds, sustainable procurement</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.success(f"💡 **Total Annual Financial Benefit**: ${total_benefit/1e6:.1f} Million")

def main():
    """Main ESG Compliance page"""
    
    st.title("🏆 ESG Compliance & Climate Requirements")
    st.markdown("Link your climate analysis to real-world ESG frameworks and business requirements.")
    
    # Check if required analysis is available
    macc_results = st.session_state.analysis_results.get('macc')
    physical_risk_results = st.session_state.analysis_results.get('physical_risk')
    
    if not st.session_state.data_uploaded:
        st.warning("⚠️ Please upload facilities data first.")
        return
    
    # Initialize ESG assessment
    esg_assessment = ESGComplianceAssessment(
        st.session_state.facilities_df,
        macc_results,
        physical_risk_results
    )
    
    # Generate comprehensive assessment
    with st.spinner("Analyzing ESG compliance and requirements..."):
        assessment_data = esg_assessment.generate_comprehensive_assessment()
    
    # Store results for dashboard
    st.session_state.analysis_results['esg_compliance'] = assessment_data
    
    # Executive Summary
    st.markdown("## 📊 ESG Readiness Overview")
    
    overall_readiness = assessment_data['overall_esg_readiness']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall ESG Score", f"{overall_readiness['score']:.1f}/100")
    with col2:
        st.metric("Readiness Grade", overall_readiness['grade'])
    with col3:
        st.metric("Investment Priority", overall_readiness['investment_priority'])
    
    # ESG Readiness Chart
    readiness_fig = create_esg_readiness_chart(assessment_data)
    st.plotly_chart(readiness_fig, use_container_width=True)
    
    # Framework Assessments
    st.markdown("## 🎯 Framework-Specific Assessments")
    
    # Create tabs for different frameworks
    tab1, tab2, tab3, tab4 = st.tabs(["TCFD", "SBTi", "EU Taxonomy", "CDP"])
    
    with tab1:
        render_tcfd_assessment(assessment_data['tcfd_assessment'])
    
    with tab2:
        render_sbti_assessment(assessment_data['sbti_assessment'])
    
    with tab3:
        render_eu_taxonomy_assessment(assessment_data['eu_taxonomy_assessment'])
    
    with tab4:
        render_cdp_assessment(assessment_data['cdp_assessment'])
    
    # Business Benefits
    st.markdown("---")
    render_business_benefits(assessment_data['business_benefits'])
    
    # Business Benefits Chart
    benefits_fig = create_business_benefits_chart(assessment_data['business_benefits'])
    st.plotly_chart(benefits_fig, use_container_width=True)
    
    # Implementation Timeline
    st.markdown("## 🛣️ Implementation Roadmap")
    timeline_fig = create_compliance_timeline(assessment_data)
    if timeline_fig:
        st.plotly_chart(timeline_fig, use_container_width=True)
    else:
        st.success("🎉 **Excellent ESG Compliance Status** - No immediate implementation gaps identified!")
    
    # Export Results
    st.markdown("---")
    st.markdown("## 📥 Export ESG Assessment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Download ESG Report"):
            # Generate ESG report summary
            report_data = pd.DataFrame([{
                'Framework': 'TCFD',
                'Score': assessment_data['tcfd_assessment'].get('overall_tcfd_score', 0),
                'Status': assessment_data['tcfd_assessment'].get('tcfd_compliance_level', 'Unknown')
            }, {
                'Framework': 'SBTi', 
                'Score': assessment_data['sbti_assessment'].get('abatement_coverage_pct', 0),
                'Status': 'Compliant' if assessment_data['sbti_assessment'].get('sbti_compliant', False) else 'Gap Identified'
            }, {
                'Framework': 'EU Taxonomy',
                'Score': assessment_data['eu_taxonomy_assessment'].get('taxonomy_alignment_percentage', 0),
                'Status': 'Eligible' if assessment_data['eu_taxonomy_assessment'].get('green_financing_eligible', False) else 'Needs Enhancement'
            }, {
                'Framework': 'CDP',
                'Score': assessment_data['cdp_assessment'].get('estimated_cdp_score', 0),
                'Status': assessment_data['cdp_assessment'].get('estimated_cdp_grade', 'D')
            }])
            
            csv = report_data.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name="esg_compliance_assessment.csv",
                mime="text/csv"
            )
    
    with col2:
        total_benefit = assessment_data['business_benefits'].get('total_annual_financial_benefit', 0)
        st.info(f"💡 **Business Case**: ${total_benefit/1e6:.1f}M annual financial benefits from improved ESG compliance")

if __name__ == "__main__":
    main()