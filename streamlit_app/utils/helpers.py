"""Common formatting and chart utilities for the Streamlit app."""

import sys
import os

# Add backend to path so we can import services directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

import plotly.graph_objects as go

# Color palette
RISK_COLORS = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}
SCENARIO_COLORS = {
    "net_zero_2050": "#ef4444",
    "below_2c": "#f97316",
    "delayed_transition": "#eab308",
    "current_policies": "#22c55e",
}
SCENARIO_NAMES = {
    "net_zero_2050": "Net Zero 2050",
    "below_2c": "Below 2°C",
    "delayed_transition": "Delayed Transition",
    "current_policies": "Current Policies",
}


COMPANY_NAMES_KR = {
    "K-Steel Corp": "K-스틸 (포스코형)",
    "K-Petrochem Inc": "K-석유화학 (SK이노베이션형)",
    "K-Motors Co": "K-모터스 (현대차형)",
    "K-Electronics Ltd": "K-전자 (삼성형)",
    "K-Display Corp": "K-디스플레이 (LG형)",
    "K-Power Corp": "K-발전 (한전형)",
    "K-Cement Corp": "K-시멘트",
    "K-Shipping Lines": "K-해운 (HMM형)",
    "K-Refinery Corp": "K-정유 (SK에너지형)",
}

SECTOR_NAMES_KR = {
    "steel": "철강",
    "petrochemical": "석유화학",
    "automotive": "자동차",
    "electronics": "전자",
    "utilities": "발전",
    "cement": "시멘트",
    "shipping": "해운",
    "oil_gas": "정유",
}


def format_currency(value: float, prefix: str = "$") -> str:
    """Format large currency values with B/M suffixes."""
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1e9:
        return f"{sign}{prefix}{abs_val / 1e9:.1f}B"
    if abs_val >= 1e6:
        return f"{sign}{prefix}{abs_val / 1e6:.1f}M"
    if abs_val >= 1e3:
        return f"{sign}{prefix}{abs_val / 1e3:.0f}K"
    return f"{sign}{prefix}{abs_val:.0f}"


def format_emissions(value: float) -> str:
    """Format emissions in MtCO2e or ktCO2e."""
    if value >= 1e6:
        return f"{value / 1e6:.1f}M tCO2e"
    if value >= 1e3:
        return f"{value / 1e3:.0f}K tCO2e"
    return f"{value:.0f} tCO2e"


def risk_badge(level: str) -> str:
    """Return colored risk badge as HTML."""
    color = RISK_COLORS.get(level, "#6b7280")
    return f'<span style="background-color:{color};color:white;padding:2px 8px;border-radius:4px;font-size:0.85em;">{level}</span>'


def compliance_color(status: str) -> str:
    """Return color for compliance status."""
    return {
        "compliant": "#22c55e",
        "partial": "#f59e0b",
        "non_compliant": "#ef4444",
    }.get(status, "#6b7280")


def compliance_icon(status: str) -> str:
    """Return icon for compliance status."""
    return {
        "compliant": "✅",
        "partial": "⚠️",
        "non_compliant": "❌",
    }.get(status, "❓")


def default_layout(fig: go.Figure, title: str = "", height: int = 400) -> go.Figure:
    """Apply consistent layout to plotly figures."""
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=40, r=40, t=50, b=40),
        font=dict(family="sans-serif"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig
