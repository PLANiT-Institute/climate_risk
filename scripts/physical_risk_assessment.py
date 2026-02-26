"""
Simplified Physical Risk Assessment Module

A practical approach to physical climate risk assessment without complex climate modeling.
Uses geographic risk indices, asset characteristics, and business impact models to 
assess climate-related physical risks for facilities.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


@dataclass
class RiskFactor:
    """Individual risk factor definition"""
    name: str
    weight: float           # Importance weight (0-1)
    probability: float      # Likelihood (0-1)
    impact_multiplier: float # Financial impact multiplier
    description: str


@dataclass
class AssetVulnerability:
    """Asset-specific vulnerability characteristics"""
    facility_id: str
    building_age: int
    construction_type: str  # "modern", "standard", "old"
    flood_protection: str   # "high", "medium", "low", "none"
    backup_systems: bool    # Has backup power/water
    supply_chain_deps: int  # Number of critical suppliers
    recovery_time_days: int # Estimated recovery time
    criticality_score: float # Business criticality (1-10)


class PhysicalRiskAssessment:
    """
    Simplified Physical Risk Assessment Engine
    
    Assesses climate-related physical risks using geographic risk indices,
    asset characteristics, and business impact modeling.
    """
    
    def __init__(self, facilities_df: pd.DataFrame):
        """
        Initialize with facilities data
        
        Args:
            facilities_df: DataFrame with facility information including coordinates,
                          asset values, and operational characteristics
        """
        self.facilities_df = facilities_df.copy()
        self.risk_database = self._initialize_risk_database()
        self.vulnerability_profiles = {}
        
        # Validate required columns
        required_cols = ['facility_id', 'country', 'latitude', 'longitude', 'asset_value_usd']
        missing_cols = [col for col in required_cols if col not in facilities_df.columns]
        if missing_cols:
            print(f"⚠️ Missing columns: {missing_cols}. Will use defaults where possible.")
    
    def _initialize_risk_database(self) -> Dict:
        """
        Initialize geographic risk database with country-level risk indices
        
        Based on global risk indices and climate data from various sources:
        - World Risk Index, INFORM Risk Index, Climate Risk Index
        - Simplified for practical implementation
        """
        
        risk_db = {
            # Format: country: {risk_type: {probability, severity, trend}}
            'Germany': {
                'flood': {'probability': 0.3, 'severity': 0.4, 'trend': 'increasing'},
                'heat': {'probability': 0.6, 'severity': 0.5, 'trend': 'increasing'}, 
                'drought': {'probability': 0.4, 'severity': 0.3, 'trend': 'stable'},
                'storm': {'probability': 0.5, 'severity': 0.4, 'trend': 'increasing'},
                'wildfire': {'probability': 0.2, 'severity': 0.2, 'trend': 'stable'}
            },
            'USA': {
                'flood': {'probability': 0.4, 'severity': 0.6, 'trend': 'increasing'},
                'heat': {'probability': 0.7, 'severity': 0.7, 'trend': 'increasing'},
                'drought': {'probability': 0.6, 'severity': 0.6, 'trend': 'increasing'}, 
                'storm': {'probability': 0.6, 'severity': 0.8, 'trend': 'increasing'},
                'wildfire': {'probability': 0.5, 'severity': 0.7, 'trend': 'increasing'}
            },
            'UK': {
                'flood': {'probability': 0.6, 'severity': 0.5, 'trend': 'increasing'},
                'heat': {'probability': 0.4, 'severity': 0.4, 'trend': 'increasing'},
                'drought': {'probability': 0.3, 'severity': 0.3, 'trend': 'stable'},
                'storm': {'probability': 0.7, 'severity': 0.5, 'trend': 'stable'},
                'wildfire': {'probability': 0.1, 'severity': 0.2, 'trend': 'stable'}
            },
            'Japan': {
                'flood': {'probability': 0.7, 'severity': 0.8, 'trend': 'increasing'},
                'heat': {'probability': 0.6, 'severity': 0.6, 'trend': 'increasing'},
                'drought': {'probability': 0.3, 'severity': 0.4, 'trend': 'stable'},
                'storm': {'probability': 0.8, 'severity': 0.9, 'trend': 'increasing'},
                'wildfire': {'probability': 0.2, 'severity': 0.3, 'trend': 'stable'},
                'earthquake': {'probability': 0.9, 'severity': 0.9, 'trend': 'stable'}
            },
            'China': {
                'flood': {'probability': 0.6, 'severity': 0.7, 'trend': 'increasing'},
                'heat': {'probability': 0.7, 'severity': 0.6, 'trend': 'increasing'},
                'drought': {'probability': 0.5, 'severity': 0.6, 'trend': 'increasing'},
                'storm': {'probability': 0.4, 'severity': 0.6, 'trend': 'stable'},
                'wildfire': {'probability': 0.3, 'severity': 0.4, 'trend': 'stable'}
            },
            'France': {
                'flood': {'probability': 0.4, 'severity': 0.4, 'trend': 'increasing'},
                'heat': {'probability': 0.7, 'severity': 0.6, 'trend': 'increasing'},
                'drought': {'probability': 0.5, 'severity': 0.4, 'trend': 'increasing'},
                'storm': {'probability': 0.4, 'severity': 0.4, 'trend': 'stable'},
                'wildfire': {'probability': 0.4, 'severity': 0.5, 'trend': 'increasing'}
            },
            'Brazil': {
                'flood': {'probability': 0.5, 'severity': 0.6, 'trend': 'increasing'},
                'heat': {'probability': 0.8, 'severity': 0.7, 'trend': 'increasing'},
                'drought': {'probability': 0.7, 'severity': 0.8, 'trend': 'increasing'},
                'storm': {'probability': 0.3, 'severity': 0.5, 'trend': 'stable'},
                'wildfire': {'probability': 0.6, 'severity': 0.7, 'trend': 'increasing'}
            }
        }
        
        # Default risk profile for countries not in database
        default_risk = {
            'flood': {'probability': 0.3, 'severity': 0.4, 'trend': 'stable'},
            'heat': {'probability': 0.5, 'severity': 0.5, 'trend': 'increasing'},
            'drought': {'probability': 0.4, 'severity': 0.4, 'trend': 'stable'},
            'storm': {'probability': 0.3, 'severity': 0.4, 'trend': 'stable'},
            'wildfire': {'probability': 0.2, 'severity': 0.3, 'trend': 'stable'}
        }
        
        return {'countries': risk_db, 'default': default_risk}
    
    def add_vulnerability_profile(self, profile: AssetVulnerability):
        """Add vulnerability profile for a specific facility"""
        self.vulnerability_profiles[profile.facility_id] = profile
    
    def create_default_vulnerability_profiles(self):
        """Create default vulnerability profiles based on facility characteristics"""
        
        for _, facility in self.facilities_df.iterrows():
            # Estimate characteristics from available data
            building_age = facility.get('building_age_years', 20)
            asset_value = facility.get('asset_value_usd', 10e6)
            sector = facility.get('sector', 'unknown')
            
            # Infer construction type from age and sector
            if building_age < 10:
                construction_type = "modern"
            elif building_age < 25:
                construction_type = "standard" 
            else:
                construction_type = "old"
            
            # Infer flood protection from sector and asset value
            if sector in ['utilities', 'oil_gas'] or asset_value > 100e6:
                flood_protection = "high"
            elif asset_value > 50e6:
                flood_protection = "medium"
            else:
                flood_protection = "low"
            
            # Estimate backup systems based on sector
            backup_systems = sector in ['utilities', 'oil_gas', 'data_center']
            
            # Estimate supply chain dependencies
            supply_chain_deps = {'manufacturing': 15, 'oil_gas': 10, 'utilities': 5, 'office': 3}.get(sector, 8)
            
            # Estimate recovery time based on sector and construction
            base_recovery = {'manufacturing': 30, 'oil_gas': 21, 'utilities': 14, 'office': 7}.get(sector, 14)
            age_multiplier = 1.5 if construction_type == "old" else 1.0
            recovery_time = int(base_recovery * age_multiplier)
            
            # Business criticality based on asset value and sector
            criticality_score = min(10, (asset_value / 50e6) * 5 + 
                                   ({'utilities': 4, 'oil_gas': 3, 'manufacturing': 2}.get(sector, 1)))
            
            profile = AssetVulnerability(
                facility_id=facility['facility_id'],
                building_age=building_age,
                construction_type=construction_type,
                flood_protection=flood_protection,
                backup_systems=backup_systems,
                supply_chain_deps=supply_chain_deps,
                recovery_time_days=recovery_time,
                criticality_score=criticality_score
            )
            
            self.add_vulnerability_profile(profile)
    
    def calculate_risk_scores(self) -> pd.DataFrame:
        """
        Calculate comprehensive risk scores for all facilities
        
        Returns:
            DataFrame with risk scores by facility and hazard type
        """
        
        if not self.vulnerability_profiles:
            self.create_default_vulnerability_profiles()
        
        risk_results = []
        
        for _, facility in self.facilities_df.iterrows():
            facility_id = facility['facility_id']
            country = facility['country']
            
            # Get country risk profile
            country_risks = self.risk_database['countries'].get(country, self.risk_database['default'])
            
            # Get vulnerability profile
            vulnerability = self.vulnerability_profiles.get(facility_id)
            if not vulnerability:
                continue
            
            # Calculate risk for each hazard type
            facility_risks = {'facility_id': facility_id, 'country': country}
            
            for hazard, risk_data in country_risks.items():
                # Base risk from geographic location
                base_probability = risk_data['probability']
                base_severity = risk_data['severity']
                
                # Adjust for facility-specific vulnerability
                adjusted_probability = self._adjust_probability(hazard, base_probability, vulnerability, facility)
                adjusted_impact = self._calculate_financial_impact(hazard, base_severity, vulnerability, facility)
                
                # Risk score = Probability × Impact (normalized)
                risk_score = adjusted_probability * (adjusted_impact / facility.get('asset_value_usd', 1e6))
                risk_score = min(1.0, risk_score)  # Cap at 1.0
                
                facility_risks[f'{hazard}_probability'] = adjusted_probability
                facility_risks[f'{hazard}_impact_usd'] = adjusted_impact
                facility_risks[f'{hazard}_risk_score'] = risk_score
                facility_risks[f'{hazard}_risk_level'] = self._categorize_risk(risk_score)
            
            # Calculate overall risk score
            individual_risks = [facility_risks[f'{h}_risk_score'] for h in country_risks.keys()]
            facility_risks['overall_risk_score'] = np.sqrt(np.mean(np.square(individual_risks)))  # RMS average
            facility_risks['overall_risk_level'] = self._categorize_risk(facility_risks['overall_risk_score'])
            
            # Add facility characteristics for analysis
            facility_risks['asset_value_usd'] = facility.get('asset_value_usd', 0)
            facility_risks['sector'] = facility.get('sector', 'unknown')
            facility_risks['latitude'] = facility.get('latitude', 0)
            facility_risks['longitude'] = facility.get('longitude', 0)
            
            risk_results.append(facility_risks)
        
        return pd.DataFrame(risk_results)
    
    def _adjust_probability(self, hazard: str, base_prob: float, vulnerability: AssetVulnerability, 
                          facility: pd.Series) -> float:
        """Adjust base probability based on facility-specific factors"""
        
        adjusted_prob = base_prob
        
        # Age adjustment
        if vulnerability.construction_type == "old":
            adjusted_prob *= 1.3
        elif vulnerability.construction_type == "modern":
            adjusted_prob *= 0.8
        
        # Hazard-specific adjustments
        if hazard == 'flood':
            protection_multipliers = {'high': 0.3, 'medium': 0.6, 'low': 1.2, 'none': 2.0}
            adjusted_prob *= protection_multipliers.get(vulnerability.flood_protection, 1.0)
            
            # Coastal vs inland (rough approximation)
            latitude = abs(facility.get('latitude', 45))
            if latitude < 10:  # Tropical regions - higher flood risk
                adjusted_prob *= 1.4
                
        elif hazard == 'heat':
            # Backup systems reduce heat risk
            if vulnerability.backup_systems:
                adjusted_prob *= 0.7
                
        elif hazard == 'storm':
            # Modern buildings more resistant
            if vulnerability.construction_type == "modern":
                adjusted_prob *= 0.6
        
        return min(1.0, adjusted_prob)
    
    def _calculate_financial_impact(self, hazard: str, base_severity: float, vulnerability: AssetVulnerability,
                                   facility: pd.Series) -> float:
        """Calculate potential financial impact in USD"""
        
        asset_value = facility.get('asset_value_usd', 10e6)
        annual_revenue = facility.get('annual_revenue', asset_value * 0.5)  # Estimate if missing
        
        # Base damage as percentage of asset value
        damage_ratios = {
            'flood': 0.25,      # 25% of asset value
            'heat': 0.05,       # 5% (mainly operational)
            'drought': 0.10,    # 10% (water-dependent operations)
            'storm': 0.30,      # 30% (structural damage)
            'wildfire': 0.80,   # 80% (potential total loss)
            'earthquake': 0.60  # 60% (structural damage)
        }
        
        base_damage = asset_value * damage_ratios.get(hazard, 0.15) * base_severity
        
        # Business interruption cost
        daily_revenue = annual_revenue / 365
        interruption_days = vulnerability.recovery_time_days
        
        # Adjust interruption based on backup systems
        if vulnerability.backup_systems:
            interruption_days *= 0.5
        
        business_interruption = daily_revenue * interruption_days
        
        # Supply chain impact
        supply_chain_cost = vulnerability.supply_chain_deps * daily_revenue * 2  # 2 days per supplier on average
        
        # Total financial impact
        total_impact = base_damage + business_interruption + supply_chain_cost
        
        # Apply criticality multiplier
        criticality_multiplier = 1 + (vulnerability.criticality_score - 5) * 0.1  # ±50% based on criticality
        total_impact *= max(0.5, criticality_multiplier)
        
        return total_impact
    
    def _categorize_risk(self, risk_score: float) -> str:
        """Categorize risk score into risk levels"""
        if risk_score >= 0.7:
            return "CRITICAL"
        elif risk_score >= 0.5:
            return "HIGH"
        elif risk_score >= 0.3:
            return "MEDIUM"
        elif risk_score >= 0.1:
            return "LOW"
        else:
            return "MINIMAL"
    
    def generate_risk_summary(self, risk_df: pd.DataFrame) -> Dict:
        """Generate executive summary of physical risk assessment"""
        
        total_facilities = len(risk_df)
        total_asset_value = risk_df['asset_value_usd'].sum()
        
        # Risk level distribution
        risk_distribution = risk_df['overall_risk_level'].value_counts()
        high_risk_facilities = len(risk_df[risk_df['overall_risk_level'].isin(['HIGH', 'CRITICAL'])])
        
        # Top risks by hazard type
        hazard_types = ['flood', 'heat', 'drought', 'storm', 'wildfire']
        if 'earthquake_risk_score' in risk_df.columns:
            hazard_types.append('earthquake')
        
        top_risks = {}
        total_potential_loss = 0
        
        for hazard in hazard_types:
            impact_col = f'{hazard}_impact_usd'
            if impact_col in risk_df.columns:
                hazard_loss = risk_df[impact_col].sum()
                total_potential_loss += hazard_loss
                top_facility = risk_df.loc[risk_df[impact_col].idxmax()]
                top_risks[hazard] = {
                    'total_exposure': hazard_loss,
                    'top_facility': top_facility['facility_id'],
                    'top_facility_loss': top_facility[impact_col]
                }
        
        # Geographic concentration
        country_risk = risk_df.groupby('country').agg({
            'overall_risk_score': 'mean',
            'asset_value_usd': 'sum',
            'facility_id': 'count'
        }).rename(columns={'facility_id': 'facility_count'})
        
        highest_risk_country = country_risk['overall_risk_score'].idxmax()
        
        return {
            'total_facilities': total_facilities,
            'total_asset_value': total_asset_value,
            'high_risk_facilities': high_risk_facilities,
            'high_risk_percentage': high_risk_facilities / total_facilities * 100,
            'total_potential_loss': total_potential_loss,
            'loss_as_percent_assets': total_potential_loss / total_asset_value * 100,
            'risk_distribution': risk_distribution.to_dict(),
            'top_risks_by_hazard': top_risks,
            'highest_risk_country': highest_risk_country,
            'country_risk_summary': country_risk.to_dict()
        }
    
    def visualize_physical_risk(self, risk_df: pd.DataFrame, save_path: Optional[str] = None):
        """Create comprehensive physical risk visualization"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Risk Level Distribution
        risk_counts = risk_df['overall_risk_level'].value_counts()
        colors = {'CRITICAL': '#d62728', 'HIGH': '#ff7f0e', 'MEDIUM': '#ffbb78', 
                 'LOW': '#2ca02c', 'MINIMAL': '#98df8a'}
        
        wedges, texts, autotexts = ax1.pie(risk_counts.values, labels=risk_counts.index, 
                                          autopct='%1.1f%%', startangle=90,
                                          colors=[colors.get(level, '#gray') for level in risk_counts.index])
        ax1.set_title('Physical Risk Distribution', fontsize=14, fontweight='bold')
        
        # 2. Risk by Country
        country_risk = risk_df.groupby('country')['overall_risk_score'].mean().sort_values(ascending=True)
        
        bars = ax2.barh(country_risk.index, country_risk.values, 
                       color=plt.cm.RdYlGn_r(country_risk.values))
        ax2.set_xlabel('Average Risk Score')
        ax2.set_title('Physical Risk by Country', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')
        
        # Add risk level indicators
        for i, (country, risk) in enumerate(country_risk.items()):
            risk_level = self._categorize_risk(risk)
            ax2.text(risk + 0.02, i, f'{risk_level}', va='center', fontsize=8, fontweight='bold')
        
        # 3. Hazard-specific risks (heatmap)
        hazard_cols = [col for col in risk_df.columns if col.endswith('_risk_score') and col != 'overall_risk_score']
        hazard_names = [col.replace('_risk_score', '').title() for col in hazard_cols]
        
        if hazard_cols:
            # Create heatmap data
            heatmap_data = []
            for _, facility in risk_df.iterrows():
                facility_risks = [facility[col] for col in hazard_cols]
                heatmap_data.append(facility_risks)
            
            heatmap_df = pd.DataFrame(heatmap_data, columns=hazard_names, 
                                    index=risk_df['facility_id'])
            
            # Show top 10 highest risk facilities
            top_facilities = risk_df.nlargest(min(10, len(risk_df)), 'overall_risk_score')
            heatmap_subset = heatmap_df.loc[top_facilities['facility_id']]
            
            sns.heatmap(heatmap_subset, annot=True, fmt='.2f', cmap='Reds', ax=ax3, cbar_kws={'label': 'Risk Score'})
            ax3.set_title('Risk Heatmap - Top Risk Facilities', fontsize=14, fontweight='bold')
            ax3.set_xlabel('Hazard Type')
            ax3.set_ylabel('Facility')
        
        # 4. Financial Impact vs Risk Score
        scatter = ax4.scatter(risk_df['overall_risk_score'], risk_df['asset_value_usd']/1e6,
                             c=risk_df['overall_risk_score'], s=80, cmap='Reds', alpha=0.7)
        
        ax4.set_xlabel('Overall Risk Score')
        ax4.set_ylabel('Asset Value (Million USD)')
        ax4.set_title('Risk vs Asset Value', fontsize=14, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        # Add facility labels for highest risk/value facilities
        for _, facility in risk_df.nlargest(3, 'overall_risk_score').iterrows():
            ax4.annotate(facility['facility_id'], 
                        (facility['overall_risk_score'], facility['asset_value_usd']/1e6),
                        xytext=(10, 10), textcoords='offset points', fontsize=8,
                        bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7))
        
        plt.colorbar(scatter, ax=ax4, label='Risk Score')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Physical risk visualization saved to: {save_path}")
        
        plt.show()
    
    def create_risk_register(self, risk_df: pd.DataFrame) -> pd.DataFrame:
        """Create a detailed risk register for risk management"""
        
        risk_register = []
        
        hazard_types = ['flood', 'heat', 'drought', 'storm', 'wildfire']
        if 'earthquake_risk_score' in risk_df.columns:
            hazard_types.append('earthquake')
        
        for _, facility in risk_df.iterrows():
            vulnerability = self.vulnerability_profiles.get(facility['facility_id'])
            
            for hazard in hazard_types:
                risk_score_col = f'{hazard}_risk_score'
                impact_col = f'{hazard}_impact_usd'
                
                if risk_score_col in facility and facility[risk_score_col] >= 0.1:  # Only include significant risks
                    
                    # Risk mitigation recommendations
                    mitigation_cost, mitigation_desc = self._suggest_risk_mitigation(hazard, vulnerability, facility)
                    
                    risk_entry = {
                        'facility_id': facility['facility_id'],
                        'country': facility['country'],
                        'hazard_type': hazard.title(),
                        'risk_score': facility[risk_score_col],
                        'risk_level': self._categorize_risk(facility[risk_score_col]),
                        'potential_loss_usd': facility[impact_col],
                        'probability': facility[f'{hazard}_probability'],
                        'asset_value_usd': facility['asset_value_usd'],
                        'sector': facility['sector'],
                        'mitigation_cost_usd': mitigation_cost,
                        'mitigation_description': mitigation_desc,
                        'roi_mitigation': (facility[impact_col] - mitigation_cost) / mitigation_cost if mitigation_cost > 0 else float('inf')
                    }
                    
                    risk_register.append(risk_entry)
        
        risk_register_df = pd.DataFrame(risk_register)
        
        # Sort by risk score descending
        if not risk_register_df.empty:
            risk_register_df = risk_register_df.sort_values('risk_score', ascending=False)
        
        return risk_register_df
    
    def _suggest_risk_mitigation(self, hazard: str, vulnerability: AssetVulnerability, 
                               facility: pd.Series) -> Tuple[float, str]:
        """Suggest risk mitigation measures and estimate costs"""
        
        asset_value = facility.get('asset_value_usd', 10e6)
        
        mitigation_options = {
            'flood': {
                'cost_pct': 0.03,  # 3% of asset value
                'description': 'Flood barriers, elevated equipment, drainage systems, flood insurance'
            },
            'heat': {
                'cost_pct': 0.015,  # 1.5% of asset value
                'description': 'Enhanced cooling systems, heat-resistant equipment, backup power'
            },
            'drought': {
                'cost_pct': 0.02,  # 2% of asset value
                'description': 'Water storage systems, alternative water sources, water recycling'
            },
            'storm': {
                'cost_pct': 0.025,  # 2.5% of asset value
                'description': 'Structural reinforcement, storm shutters, emergency generators'
            },
            'wildfire': {
                'cost_pct': 0.04,  # 4% of asset value
                'description': 'Fire-resistant landscaping, sprinkler systems, firebreaks'
            },
            'earthquake': {
                'cost_pct': 0.08,  # 8% of asset value (most expensive)
                'description': 'Seismic retrofitting, flexible connections, base isolation'
            }
        }
        
        option = mitigation_options.get(hazard, {'cost_pct': 0.02, 'description': 'General resilience measures'})
        
        # Adjust cost based on current vulnerability
        cost_multiplier = 1.0
        if vulnerability:
            if vulnerability.construction_type == "old":
                cost_multiplier = 1.5  # More expensive to retrofit old buildings
            elif vulnerability.construction_type == "modern":
                cost_multiplier = 0.7  # Cheaper to upgrade modern buildings
        
        mitigation_cost = asset_value * option['cost_pct'] * cost_multiplier
        
        return mitigation_cost, option['description']


def main():
    """Test the Physical Risk Assessment with real facilities data"""
    
    print("🌪️ Physical Risk Assessment Module")
    print("=" * 50)
    
    # Load facilities data
    try:
        facilities_df = pd.read_csv("example_facilities.csv")
        print(f"✅ Loaded facilities data: {len(facilities_df)} facilities")
        
        # Standardize column names (same as in MACC analysis)
        facilities_df = facilities_df.rename(columns={
            'current_emissions_scope1': 'annual_emissions_scope1',
            'current_emissions_scope2': 'annual_emissions_scope2',
            'assets_value': 'asset_value_usd'
        })
        
        # Add missing coordinates and other fields
        if 'latitude' not in facilities_df.columns:
            country_coords = {
                'Germany': (51.1657, 10.4515), 'USA': (39.8283, -98.5795), 
                'UK': (55.3781, -3.4360), 'Japan': (36.2048, 138.2529),
                'China': (35.8617, 104.1954), 'France': (46.6034, 1.8883),
                'Brazil': (-14.2350, -51.9253)
            }
            
            for country, (lat, lon) in country_coords.items():
                mask = facilities_df['country'] == country
                facilities_df.loc[mask, 'latitude'] = lat + np.random.uniform(-2, 2, mask.sum())
                facilities_df.loc[mask, 'longitude'] = lon + np.random.uniform(-5, 5, mask.sum())
        
        # Add building age estimates
        if 'building_age_years' not in facilities_df.columns:
            facilities_df['building_age_years'] = np.random.randint(10, 35, len(facilities_df))
            
    except FileNotFoundError:
        print("❌ Facilities data not found. Please ensure example_facilities.csv exists.")
        return
    
    # Initialize Physical Risk Assessment
    pra = PhysicalRiskAssessment(facilities_df)
    
    # Calculate risk scores
    print("🔍 Calculating risk scores...")
    risk_df = pra.calculate_risk_scores()
    
    # Generate risk summary
    summary = pra.generate_risk_summary(risk_df)
    
    # Display results
    print("\n" + "=" * 60)
    print("🎯 PHYSICAL RISK ASSESSMENT RESULTS")
    print("=" * 60)
    
    print(f"📊 Portfolio Overview:")
    print(f"   Total Facilities: {summary['total_facilities']}")
    print(f"   Total Asset Value: ${summary['total_asset_value']/1e9:.1f} Billion")
    print(f"   High/Critical Risk Facilities: {summary['high_risk_facilities']} ({summary['high_risk_percentage']:.1f}%)")
    
    print(f"\n💥 Financial Exposure:")
    print(f"   Total Potential Loss: ${summary['total_potential_loss']/1e6:.1f} Million")
    print(f"   Loss as % of Assets: {summary['loss_as_percent_assets']:.1f}%")
    
    print(f"\n🌍 Geographic Risk:")
    print(f"   Highest Risk Country: {summary['highest_risk_country']}")
    
    print(f"\n📋 Risk Distribution:")
    for level, count in summary['risk_distribution'].items():
        print(f"   {level}: {count} facilities")
    
    print(f"\n🌊 Top Risks by Hazard:")
    for hazard, data in summary['top_risks_by_hazard'].items():
        print(f"   {hazard.title()}: ${data['total_exposure']/1e6:.1f}M exposure")
        print(f"      Top facility: {data['top_facility']} (${data['top_facility_loss']/1e6:.1f}M)")
    
    # Create risk register
    print(f"\n📝 Creating risk register...")
    risk_register = pra.create_risk_register(risk_df)
    
    print(f"\n🔥 TOP 10 HIGHEST RISKS:")
    print("-" * 45)
    for i, (_, risk) in enumerate(risk_register.head(10).iterrows(), 1):
        print(f"{i}. {risk['facility_id']} - {risk['hazard_type']} Risk")
        print(f"   Level: {risk['risk_level']} (Score: {risk['risk_score']:.2f})")
        print(f"   Potential Loss: ${risk['potential_loss_usd']/1e6:.1f}M")
        print(f"   Mitigation Cost: ${risk['mitigation_cost_usd']/1e6:.1f}M (ROI: {risk['roi_mitigation']:.1f}x)")
    
    # Create visualizations
    print(f"\n🎨 Creating risk visualizations...")
    pra.visualize_physical_risk(risk_df, save_path="outputs/physical_risk_assessment.png")
    
    # Save detailed results
    risk_df.to_csv("outputs/physical_risk_scores.csv", index=False)
    risk_register.to_csv("outputs/physical_risk_register.csv", index=False)
    
    print(f"\n✅ Physical Risk Assessment Complete!")
    print(f"📁 Results saved to outputs/ directory")
    
    return pra, risk_df, risk_register


if __name__ == "__main__":
    import os
    os.makedirs("outputs", exist_ok=True)
    
    pra, risk_df, risk_register = main()