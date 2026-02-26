import os
import sys

# Add backend to path so we can import internal services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.transition_risk import get_summary as get_transition_risk_summary
from app.services.physical_risk import assess_physical_risk as get_physical_risk_assessment
from app.data.sample_facilities import get_all_facilities

import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def create_chart(summary):
    # Create a nice cost waterfall or emission breakdown chart
    fig, ax = plt.subplots(figsize=(6, 4))
    
    costs = summary["cost_breakdown"]
    labels = ["Carbon Cost", "Energy Increase", "Revenue Impact", "Transition OPEX"]
    values = [
        costs["carbon_cost"] / 1e9, 
        costs["energy_cost_increase"] / 1e9, 
        costs["revenue_impact"] / 1e9, 
        costs["transition_opex"] / 1e9
    ]
    
    ax.bar(labels, values, color=['#ef4444', '#f97316', '#eab308', '#3b82f6'])
    ax.set_ylabel("Billion USD")
    ax.set_title("Transition Cost Breakdown (NPV by Category)")
    
    plt.tight_layout()
    chart_path = "temp_chart.png"
    plt.savefig(chart_path, dpi=150)
    plt.close()
    return chart_path

def generate_pdf():
    print("Loading sample data and analyzing risks...")
    facilities = get_all_facilities()
    
    # 1. Transition Risk Analysis
    tr_summary = get_transition_risk_summary("net_zero_2050", "global", facilities)
    
    # 2. Physical Risk Analysis (Analytical v1)
    pr_summary = get_physical_risk_assessment("net_zero_2050", 2030, False, facilities)
    
    # Generate Chart
    chart_path = create_chart(tr_summary)
    
    # Create PDF Report
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "sample_climate_risk_report.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    h2_style = styles['Heading2']
    h3_style = styles['Heading3']
    normal_style = styles['Normal']
    
    story = []
    
    # Header
    story.append(Paragraph("Climate Risk Assessment - Executive Summary", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("This is an automatically generated sample report analyzing 17 Korean industrial facilities under the NGFS Net Zero 2050 scenario.", normal_style))
    story.append(Spacer(1, 20))
    
    # Transition Risk
    story.append(Paragraph("1. Transition Risk (Net Zero 2050)", h2_style))
    story.append(Paragraph(f"Total Facilities Evaluated: {tr_summary['total_facilities']}", normal_style))
    story.append(Paragraph(f"Total Financial Impact (NPV): ${tr_summary['total_npv']:,.0f}", normal_style))
    story.append(Spacer(1, 10))
    
    # Insert Chart
    story.append(Image(chart_path, width=400, height=266))
    story.append(Spacer(1, 10))
    
    # Top Risk Facilities Table
    story.append(Paragraph("Highest Transition Risk Facilities", h3_style))
    
    table_data = [["Facility Name", "Sector", "Risk Level", "NPV Impact ($)"]]
    for f in tr_summary["top_risk_facilities"][:5]:
        table_data.append([
            f["name"], 
            f["sector"].capitalize(), 
            f["risk_level"], 
            f"${f['delta_npv']:,.0f}"
        ])
        
    t = Table(table_data, colWidths=[150, 100, 80, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1"))
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    
    # Physical Risk
    story.append(Paragraph("2. Physical Risk Assessment (Analytical v1)", h2_style))
    story.append(Paragraph("Analyzing multi-hazard exposure including flood, typhoon, heatwave, drought, and sea-level rise.", normal_style))
    story.append(Spacer(1, 10))
    
    risk_dist = pr_summary["overall_risk_summary"]
    story.append(Paragraph(f"Risk Distribution: {risk_dist.get('High', 0)} High | {risk_dist.get('Medium', 0)} Medium | {risk_dist.get('Low', 0)} Low", normal_style))
    
    # EAL Table
    story.append(Spacer(1, 10))
    story.append(Paragraph("Top Facilities by Expected Annual Loss (EAL)", h3_style))
    pr_table_data = [["Facility Name", "Location", "Overall Risk", "EAL ($)"]]
    
    # Sort PR by EAL
    sorted_pr = sorted(pr_summary["facilities"], key=lambda x: x["total_expected_annual_loss"], reverse=True)
    for f in sorted_pr[:5]:
        pr_table_data.append([
            f["facility_name"], 
            f["location"], 
            f["overall_risk_level"], 
            f"${f['total_expected_annual_loss']:,.0f}"
        ])
    
    t2 = Table(pr_table_data, colWidths=[150, 100, 80, 120])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0284c7")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f0f9ff")),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#bae6fd"))
    ]))
    story.append(t2)
    
    # Generate Doc
    doc.build(story)
    
    # Cleanup
    if os.path.exists(chart_path):
        os.remove(chart_path)
        
    print(f"✅ Successfully generated PDF at: {pdf_path}")

if __name__ == "__main__":
    generate_pdf()
