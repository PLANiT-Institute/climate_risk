"""
Corporate Data Models

Comprehensive data models for internal corporate data including:
- Financial statements and metrics
- Physical assets and operational data  
- Business interruption valuations
- WACC and financial parameters
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from datetime import datetime
import pandas as pd
import numpy as np


@dataclass
class FinancialDataModel:
    """Annual financial statements and key metrics"""
    company_id: str
    year: int
    revenue: float                    # USD
    ebitda: float                    # USD  
    opex: float                      # USD
    capex: float                     # USD
    total_assets: float              # USD
    debt: float                      # USD
    equity: float                    # USD
    wacc: float                      # Weighted Average Cost of Capital (decimal)
    tax_rate: float                  # Corporate tax rate (decimal)
    currency: str = "USD"
    
    def calculate_financial_ratios(self) -> Dict[str, float]:
        """Calculate key financial ratios"""
        return {
            'debt_to_equity': self.debt / self.equity if self.equity > 0 else np.nan,
            'asset_turnover': self.revenue / self.total_assets if self.total_assets > 0 else np.nan,
            'ebitda_margin': self.ebitda / self.revenue if self.revenue > 0 else np.nan,
            'capex_intensity': self.capex / self.revenue if self.revenue > 0 else np.nan,
            'roe': (self.ebitda * (1 - self.tax_rate)) / self.equity if self.equity > 0 else np.nan
        }


@dataclass
class AssetDataModel:
    """Physical assets and operational data"""
    asset_id: str
    facility_id: str
    asset_name: str
    asset_type: str                  # "factory", "office", "data_center", "warehouse"
    latitude: float
    longitude: float
    country: str
    region: str
    asset_value: float               # USD valuation
    annual_revenue: float            # USD revenue attributed to this asset
    daily_revenue: float             # USD revenue per day (for business interruption)
    employees: int                   # Number of employees at this location
    floor_area_sqm: float           # Total floor area in square meters
    operational_status: str          # "operational", "under_construction", "decommissioned"
    criticality_score: float        # Business criticality (1-10 scale)
    
    # Operational data
    annual_production_units: Optional[float] = None    # Units produced annually
    capacity_utilization: Optional[float] = None       # % of theoretical max capacity
    shutdown_risk_days: Optional[int] = None           # Days per year at risk of shutdown
    
    def calculate_business_interruption_value(self, disruption_days: int) -> float:
        """Calculate potential loss from business disruption"""
        daily_loss = self.daily_revenue
        fixed_cost_continuation = daily_loss * 0.3  # Assume 30% of costs continue during shutdown
        
        total_interruption_loss = (daily_loss + fixed_cost_continuation) * disruption_days
        return total_interruption_loss
    
    def get_geographic_risk_factors(self) -> Dict[str, str]:
        """Identify geographic risk categories"""
        # This would integrate with external hazard databases
        risk_factors = {
            'flood_zone': 'unknown',      # 'high', 'medium', 'low'
            'seismic_zone': 'unknown',    # 'high', 'medium', 'low'  
            'wildfire_zone': 'unknown',   # 'high', 'medium', 'low'
            'water_stress': 'unknown',    # 'high', 'medium', 'low'
            'political_stability': 'unknown'  # 'stable', 'moderate', 'unstable'
        }
        
        return risk_factors


@dataclass  
class CorporateDataModel:
    """Complete corporate data aggregation"""
    company_id: str
    company_name: str
    primary_sector: str              # GICS or similar classification
    headquarters_country: str
    employees_total: int
    market_cap: Optional[float] = None      # USD market capitalization
    
    # Time series data containers
    financial_data: List[FinancialDataModel] = None
    asset_data: List[AssetDataModel] = None
    
    def __post_init__(self):
        if self.financial_data is None:
            self.financial_data = []
        if self.asset_data is None:
            self.asset_data = []
    
    def get_latest_financial_data(self) -> Optional[FinancialDataModel]:
        """Get most recent financial data"""
        if not self.financial_data:
            return None
        return max(self.financial_data, key=lambda x: x.year)
    
    def get_total_asset_value(self) -> float:
        """Calculate total physical asset value"""
        return sum(asset.asset_value for asset in self.asset_data)
    
    def get_assets_by_country(self) -> Dict[str, List[AssetDataModel]]:
        """Group assets by country"""
        country_assets = {}
        for asset in self.asset_data:
            if asset.country not in country_assets:
                country_assets[asset.country] = []
            country_assets[asset.country].append(asset)
        
        return country_assets
    
    def calculate_geographic_concentration_risk(self) -> float:
        """Calculate concentration risk based on asset geographic distribution"""
        if not self.asset_data:
            return 0.0
        
        country_values = {}
        total_value = self.get_total_asset_value()
        
        for asset in self.asset_data:
            if asset.country not in country_values:
                country_values[asset.country] = 0
            country_values[asset.country] += asset.asset_value
        
        # Calculate Herfindahl-Hirschman Index for concentration
        hhi = sum((value / total_value) ** 2 for value in country_values.values())
        
        return hhi  # Ranges from 1/n to 1, higher = more concentrated
    
    def to_dataframes(self) -> Dict[str, pd.DataFrame]:
        """Convert to pandas DataFrames for analysis"""
        dfs = {}
        
        # Financial data
        if self.financial_data:
            financial_dicts = []
            for fin_data in self.financial_data:
                fin_dict = {
                    'company_id': fin_data.company_id,
                    'year': fin_data.year,
                    'revenue': fin_data.revenue,
                    'ebitda': fin_data.ebitda,
                    'opex': fin_data.opex,
                    'capex': fin_data.capex,
                    'total_assets': fin_data.total_assets,
                    'debt': fin_data.debt,
                    'equity': fin_data.equity,
                    'wacc': fin_data.wacc,
                    'tax_rate': fin_data.tax_rate,
                    'currency': fin_data.currency
                }
                # Add calculated ratios
                fin_dict.update(fin_data.calculate_financial_ratios())
                financial_dicts.append(fin_dict)
            
            dfs['financial'] = pd.DataFrame(financial_dicts)
        
        # Asset data
        if self.asset_data:
            asset_dicts = []
            for asset in self.asset_data:
                asset_dict = {
                    'asset_id': asset.asset_id,
                    'facility_id': asset.facility_id,
                    'asset_name': asset.asset_name,
                    'asset_type': asset.asset_type,
                    'latitude': asset.latitude,
                    'longitude': asset.longitude,
                    'country': asset.country,
                    'region': asset.region,
                    'asset_value': asset.asset_value,
                    'annual_revenue': asset.annual_revenue,
                    'daily_revenue': asset.daily_revenue,
                    'employees': asset.employees,
                    'floor_area_sqm': asset.floor_area_sqm,
                    'operational_status': asset.operational_status,
                    'criticality_score': asset.criticality_score,
                    'annual_production_units': asset.annual_production_units,
                    'capacity_utilization': asset.capacity_utilization,
                    'shutdown_risk_days': asset.shutdown_risk_days
                }
                asset_dicts.append(asset_dict)
            
            dfs['assets'] = pd.DataFrame(asset_dicts)
        
        return dfs


# Utility functions for data validation and processing

def validate_financial_data(financial_data: FinancialDataModel) -> List[str]:
    """Validate financial data for consistency and reasonableness"""
    issues = []
    
    # Basic validation
    if financial_data.revenue <= 0:
        issues.append("Revenue must be positive")
    
    if financial_data.ebitda > financial_data.revenue:
        issues.append("EBITDA cannot exceed revenue")
    
    if not 0 <= financial_data.wacc <= 1:
        issues.append("WACC should be between 0 and 1 (as decimal)")
    
    if not 0 <= financial_data.tax_rate <= 1:
        issues.append("Tax rate should be between 0 and 1 (as decimal)")
    
    # Advanced validation
    if financial_data.debt + financial_data.equity == 0:
        issues.append("Debt + Equity cannot be zero")
    
    ebitda_margin = financial_data.ebitda / financial_data.revenue
    if ebitda_margin < -1 or ebitda_margin > 1:
        issues.append(f"EBITDA margin ({ebitda_margin:.2%}) seems unreasonable")
    
    return issues


def validate_asset_data(asset_data: AssetDataModel) -> List[str]:
    """Validate asset data for consistency and reasonableness"""
    issues = []
    
    # Geographic validation
    if not -90 <= asset_data.latitude <= 90:
        issues.append("Latitude must be between -90 and 90")
    
    if not -180 <= asset_data.longitude <= 180:
        issues.append("Longitude must be between -180 and 180")
    
    # Financial validation
    if asset_data.asset_value <= 0:
        issues.append("Asset value must be positive")
    
    if asset_data.annual_revenue < 0:
        issues.append("Annual revenue cannot be negative")
    
    if asset_data.daily_revenue * 365 > asset_data.annual_revenue * 2:
        issues.append("Daily revenue seems inconsistent with annual revenue")
    
    # Operational validation
    if asset_data.capacity_utilization and not 0 <= asset_data.capacity_utilization <= 1:
        issues.append("Capacity utilization should be between 0 and 1")
    
    if not 1 <= asset_data.criticality_score <= 10:
        issues.append("Criticality score should be between 1 and 10")
    
    return issues