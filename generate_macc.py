"""
MACC (Marginal Abatement Cost Curve) Generator
Complete implementation with sample data and visualization
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

@dataclass
class AbatementProject:
    """Data structure for individual abatement projects"""
    project_id: str
    technology: str
    sector: str
    capex_per_unit: float           # USD per deployment unit
    opex_delta_annual: float        # Annual OPEX change per unit (negative = savings)
    abatement_per_unit: float       # tCO2e abated per unit per year
    unit_definition: str            # kW, fixture, system, vehicle, etc.
    lifetime_years: int
    max_deployment: float           # Maximum deployable units
    technology_readiness: int       # TRL scale 1-10


class MACCGenerator:
    """
    Marginal Abatement Cost Curve Generator
    Creates cost-effectiveness ranking for emission reduction projects
    """
    
    def __init__(self, facilities_df: pd.DataFrame, discount_rate: float = 0.06):
        """
        Initialize MACC Generator
        
        Args:
            facilities_df: DataFrame with facility data
            discount_rate: Discount rate for NPV calculations
        """
        self.facilities = facilities_df
        self.discount_rate = discount_rate
        self.projects = []
        
    def add_project(self, project: AbatementProject):
        """Add abatement project to analysis"""
        self.projects.append(project)
        
    def calculate_levelized_cost_of_abatement(self, project: AbatementProject) -> float:
        """
        Calculate Levelized Cost of Abatement (LCOA) in $/tCO2e
        """
        # Present value of OPEX changes over project lifetime
        pv_opex = sum(project.opex_delta_annual / (1 + self.discount_rate)**t 
                     for t in range(1, project.lifetime_years + 1))
        
        # Total present value of costs
        total_pv_cost = project.capex_per_unit + pv_opex
        
        # Present value of total CO2 abatement over lifetime
        pv_abatement = sum(project.abatement_per_unit / (1 + self.discount_rate)**t 
                          for t in range(1, project.lifetime_years + 1))
        
        # LCOA (can be negative for profitable projects)
        lcoa = total_pv_cost / pv_abatement if pv_abatement > 0 else float('inf')
        
        return lcoa
    
    def calculate_facility_deployment_potential(self, facility: pd.Series, 
                                               project: AbatementProject) -> float:
        """
        Calculate maximum deployment potential for project at specific facility
        """
        
        # Technology-specific deployment constraints
        if project.technology == 'Solar PV':
            # Based on roof area and energy consumption
            roof_area = facility.get('floor_area_sqm', 1000) * 0.3  # 30% of floor area
            max_by_area = roof_area / 10  # 10 sqm per kW
            annual_electricity = facility.get('annual_emissions_scope2', 1000) / 0.5 * 1000  # Estimate kWh
            max_by_consumption = annual_electricity / (8760 * 0.2) * 1.2  # 120% of consumption
            return min(max_by_area, max_by_consumption, project.max_deployment)
            
        elif project.technology == 'LED Lighting':
            floor_area = facility.get('floor_area_sqm', 1000)
            return min(floor_area / 20, project.max_deployment)  # 1 fixture per 20 sqm
            
        elif project.technology == 'HVAC Efficiency':
            floor_area = facility.get('floor_area_sqm', 1000)
            return min(max(1, floor_area / 1000), project.max_deployment)  # 1 system per 1000 sqm
            
        elif project.technology == 'Electric Vehicles':
            employees = facility.get('employees', 50)
            return min(employees * 0.1, project.max_deployment)  # 10% of employees
            
        elif project.technology == 'Heat Pumps':
            floor_area = facility.get('floor_area_sqm', 1000)
            return min(max(1, floor_area / 500), project.max_deployment)
            
        elif project.technology == 'Building Insulation':
            floor_area = facility.get('floor_area_sqm', 1000)
            building_age = facility.get('building_age_years', 20)
            age_multiplier = min(2.0, building_age / 15)
            return min(floor_area * age_multiplier / 1000, project.max_deployment)
            
        else:
            # Default constraint based on facility size
            return min(project.max_deployment * 0.1, project.max_deployment)
    
    def generate_macc_curve(self) -> pd.DataFrame:
        """
        Generate complete MACC curve
        """
        
        macc_data = []
        
        for project in self.projects:
            # Calculate levelized cost of abatement
            lcoa = self.calculate_levelized_cost_of_abatement(project)
            
            # Calculate total deployment potential across all facilities
            total_deployment = 0
            total_abatement = 0
            total_capex = 0
            
            for _, facility in self.facilities.iterrows():
                facility_potential = self.calculate_facility_deployment_potential(facility, project)
                facility_abatement = facility_potential * project.abatement_per_unit
                facility_capex = facility_potential * project.capex_per_unit
                
                total_deployment += facility_potential
                total_abatement += facility_abatement
                total_capex += facility_capex
            
            # Calculate additional metrics
            payback_period = self._calculate_payback_period(project)
            roi = self._calculate_roi(project)
            
            macc_data.append({
                'project_id': project.project_id,
                'technology': project.technology,
                'sector': project.sector,
                'lcoa_usd_per_tco2': lcoa,
                'annual_abatement_potential': total_abatement,
                'lifetime_abatement_potential': total_abatement * project.lifetime_years,
                'total_capex_required': total_capex,
                'deployment_units': total_deployment,
                'unit_definition': project.unit_definition,
                'net_negative_cost': lcoa < 0,
                'payback_period_years': payback_period,
                'roi_percent': roi * 100,
                'technology_readiness': project.technology_readiness
            })
        
        # Create DataFrame and sort by cost-effectiveness
        macc_df = pd.DataFrame(macc_data)
        macc_df = macc_df.sort_values('lcoa_usd_per_tco2')
        
        # Calculate cumulative abatement potential
        macc_df['cumulative_abatement'] = macc_df['annual_abatement_potential'].cumsum()
        
        # Add rank
        macc_df['rank'] = range(1, len(macc_df) + 1)
        
        return macc_df
    
    def _calculate_payback_period(self, project: AbatementProject) -> float:
        """Calculate simple payback period in years"""
        if project.opex_delta_annual >= 0:
            return float('inf')
        
        annual_savings = -project.opex_delta_annual
        return project.capex_per_unit / annual_savings
    
    def _calculate_roi(self, project: AbatementProject) -> float:
        """Calculate return on investment over project lifetime"""
        total_savings = -project.opex_delta_annual * project.lifetime_years
        if project.capex_per_unit <= 0:
            return float('inf')
        
        return (total_savings - project.capex_per_unit) / project.capex_per_unit
    
    def visualize_macc_curve(self, macc_df: pd.DataFrame, save_path: Optional[str] = None):
        """
        Create comprehensive MACC visualization
        """
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Main MACC Curve
        x_data = macc_df['cumulative_abatement'] / 1000  # Convert to ktCO2e
        y_data = macc_df['lcoa_usd_per_tco2']
        
        # Color-code by cost savings vs cost
        colors = ['darkgreen' if cost < 0 else 'darkred' if cost > 100 else 'orange' 
                 for cost in y_data]
        
        bars = ax1.bar(x_data, y_data, 
                      width=np.diff(np.append(0, x_data)), 
                      color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax1.set_xlabel('Cumulative Abatement Potential (ktCO2e/year)', fontsize=12)
        ax1.set_ylabel('Levelized Cost of Abatement ($/tCO2e)', fontsize=12)
        ax1.set_title('Marginal Abatement Cost Curve (MACC)', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=1)
        
        # Add technology labels for top projects
        for i, (_, row) in enumerate(macc_df.head(8).iterrows()):
            if i < len(bars):
                height = bars[i].get_height()
                ax1.text(bars[i].get_x() + bars[i].get_width()/2, 
                        height + (5 if height > 0 else -15),
                        row['technology'][:10], 
                        ha='center', va='bottom' if height > 0 else 'top',
                        fontsize=8, rotation=45)
        
        # Legend
        ax1.plot([], [], color='darkgreen', alpha=0.8, linewidth=10, label='Net Cost Savings')
        ax1.plot([], [], color='orange', alpha=0.8, linewidth=10, label='Low Cost (<$100/tCO2)')
        ax1.plot([], [], color='darkred', alpha=0.8, linewidth=10, label='High Cost (>$100/tCO2)')
        ax1.legend(loc='upper left')
        
        # CAPEX Requirements
        ax2.bar(range(len(macc_df)), macc_df['total_capex_required'] / 1e6,
               color='steelblue', alpha=0.7)
        ax2.set_xlabel('Project Rank (by cost-effectiveness)', fontsize=12)
        ax2.set_ylabel('Total CAPEX Required (Million USD)', fontsize=12)
        ax2.set_title('CAPEX Requirements by Project', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Abatement by Sector
        sector_abatement = macc_df.groupby('sector')['annual_abatement_potential'].sum()
        ax3.pie(sector_abatement.values, labels=sector_abatement.index, autopct='%1.1f%%')
        ax3.set_title('Abatement Potential by Sector', fontsize=14, fontweight='bold')
        
        # Cost vs Abatement Scatter
        scatter = ax4.scatter(macc_df['annual_abatement_potential'] / 1000, 
                            macc_df['lcoa_usd_per_tco2'],
                            s=macc_df['total_capex_required'] / 1e6 * 10,  # Size by CAPEX
                            c=macc_df['roi_percent'], 
                            cmap='RdYlGn', alpha=0.7)
        
        ax4.set_xlabel('Annual Abatement Potential (ktCO2e)', fontsize=12)
        ax4.set_ylabel('Levelized Cost ($/tCO2e)', fontsize=12)
        ax4.set_title('Cost vs Abatement (bubble size = CAPEX)', fontsize=14, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax4)
        cbar.set_label('ROI (%)', fontsize=10)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"MACC visualization saved to: {save_path}")
        
        plt.show()


def create_sample_facilities_data() -> pd.DataFrame:
    """Create sample facilities data for MACC testing"""
    
    np.random.seed(42)  # For reproducible results
    
    facilities_data = []
    
    # Generate 20 sample facilities
    for i in range(20):
        facility = {
            'facility_id': f'FAC_{i+1:03d}',
            'facility_name': f'Facility {i+1}',
            'country': np.random.choice(['USA', 'Germany', 'Japan', 'Canada', 'UK']),
            'sector': np.random.choice(['Manufacturing', 'Office', 'Warehouse', 'Data Center']),
            'floor_area_sqm': np.random.randint(5000, 50000),
            'employees': np.random.randint(50, 500),
            'annual_emissions_scope1': np.random.randint(500, 5000),  # tCO2e
            'annual_emissions_scope2': np.random.randint(1000, 8000),  # tCO2e
            'building_age_years': np.random.randint(5, 40)
        }
        facilities_data.append(facility)
    
    return pd.DataFrame(facilities_data)


def create_sample_abatement_projects() -> List[AbatementProject]:
    """Create comprehensive sample abatement projects catalog"""
    
    projects = [
        # Energy Generation Projects
        AbatementProject(
            project_id='SOLAR_001',
            technology='Solar PV',
            sector='Energy',
            capex_per_unit=2500,      # USD per kW
            opex_delta_annual=-200,   # USD per kW per year (savings)
            abatement_per_unit=1.8,   # tCO2e per kW per year
            unit_definition='kW',
            lifetime_years=25,
            max_deployment=1000,      # kW max per facility
            technology_readiness=10
        ),
        
        # Building Efficiency Projects
        AbatementProject(
            project_id='LED_001',
            technology='LED Lighting',
            sector='Buildings',
            capex_per_unit=150,       # USD per fixture
            opex_delta_annual=-50,    # USD per fixture per year
            abatement_per_unit=0.5,   # tCO2e per fixture per year
            unit_definition='fixture',
            lifetime_years=10,
            max_deployment=500,       # fixtures max per facility
            technology_readiness=10
        ),
        
        AbatementProject(
            project_id='HVAC_001',
            technology='HVAC Efficiency',
            sector='Buildings',
            capex_per_unit=15000,     # USD per system
            opex_delta_annual=-2000,  # USD per system per year
            abatement_per_unit=20,    # tCO2e per system per year
            unit_definition='system',
            lifetime_years=15,
            max_deployment=5,         # systems max per facility
            technology_readiness=9
        ),
        
        AbatementProject(
            project_id='INSULATION_001',
            technology='Building Insulation',
            sector='Buildings',
            capex_per_unit=50,        # USD per sqm
            opex_delta_annual=-5,     # USD per sqm per year
            abatement_per_unit=0.05,  # tCO2e per sqm per year
            unit_definition='sqm',
            lifetime_years=20,
            max_deployment=10000,     # sqm max per facility
            technology_readiness=10
        ),
        
        # Transport Projects
        AbatementProject(
            project_id='EV_001',
            technology='Electric Vehicles',
            sector='Transport',
            capex_per_unit=45000,     # USD per vehicle
            opex_delta_annual=2000,   # USD per vehicle per year (cost increase)
            abatement_per_unit=4.5,   # tCO2e per vehicle per year
            unit_definition='vehicle',
            lifetime_years=8,
            max_deployment=50,        # vehicles max per facility
            technology_readiness=9
        ),
        
        # Heating/Cooling Projects  
        AbatementProject(
            project_id='HEATPUMP_001',
            technology='Heat Pumps',
            sector='Buildings',
            capex_per_unit=8000,      # USD per heat pump
            opex_delta_annual=-800,   # USD per heat pump per year
            abatement_per_unit=6,     # tCO2e per heat pump per year
            unit_definition='unit',
            lifetime_years=15,
            max_deployment=10,        # units max per facility
            technology_readiness=9
        ),
        
        # High-cost emerging technologies
        AbatementProject(
            project_id='CCUS_001',
            technology='Carbon Capture',
            sector='Industry',
            capex_per_unit=500,       # USD per tCO2 capacity
            opex_delta_annual=50,     # USD per tCO2 per year (operating cost)
            abatement_per_unit=1,     # tCO2e per tCO2 capacity per year
            unit_definition='tCO2/year',
            lifetime_years=20,
            max_deployment=1000,      # tCO2/year max per facility
            technology_readiness=6
        ),
        
        # Process efficiency
        AbatementProject(
            project_id='MOTORS_001',
            technology='Efficient Motors',
            sector='Industry',
            capex_per_unit=5000,      # USD per motor
            opex_delta_annual=-600,   # USD per motor per year
            abatement_per_unit=3,     # tCO2e per motor per year
            unit_definition='motor',
            lifetime_years=12,
            max_deployment=20,        # motors max per facility
            technology_readiness=10
        ),
        
        # Energy storage
        AbatementProject(
            project_id='BATTERY_001',
            technology='Battery Storage',
            sector='Energy',
            capex_per_unit=800,       # USD per kWh
            opex_delta_annual=20,     # USD per kWh per year
            abatement_per_unit=0.3,   # tCO2e per kWh per year (enabling renewables)
            unit_definition='kWh',
            lifetime_years=10,
            max_deployment=500,       # kWh max per facility
            technology_readiness=8
        ),
        
        # Waste heat recovery
        AbatementProject(
            project_id='WHR_001',
            technology='Waste Heat Recovery',
            sector='Industry',
            capex_per_unit=25000,     # USD per system
            opex_delta_annual=-3000,  # USD per system per year
            abatement_per_unit=50,    # tCO2e per system per year
            unit_definition='system',
            lifetime_years=15,
            max_deployment=2,         # systems max per facility
            technology_readiness=8
        )
    ]
    
    return projects


def main():
    """Generate and visualize MACC curve with sample data"""
    
    print("🔄 Generating MACC (Marginal Abatement Cost Curve)...")
    print("=" * 60)
    
    # Create sample data
    print("📊 Creating sample facilities data...")
    facilities_df = create_sample_facilities_data()
    print(f"✅ Created {len(facilities_df)} sample facilities")
    
    # Create sample abatement projects
    print("🔧 Loading abatement projects catalog...")
    sample_projects = create_sample_abatement_projects()
    print(f"✅ Loaded {len(sample_projects)} abatement technologies")
    
    # Initialize MACC generator
    print("⚙️ Initializing MACC generator...")
    macc_gen = MACCGenerator(facilities_df, discount_rate=0.06)
    
    # Add all projects
    for project in sample_projects:
        macc_gen.add_project(project)
    
    # Generate MACC curve
    print("📈 Generating MACC curve...")
    macc_df = macc_gen.generate_macc_curve()
    
    # Display results summary
    print("\n" + "=" * 60)
    print("🎯 MACC ANALYSIS RESULTS")
    print("=" * 60)
    
    # Key statistics
    total_abatement = macc_df['annual_abatement_potential'].sum()
    total_capex = macc_df['total_capex_required'].sum()
    net_negative_projects = len(macc_df[macc_df['net_negative_cost']])
    
    print(f"📊 Total Annual Abatement Potential: {total_abatement:,.0f} tCO2e/year")
    print(f"💰 Total CAPEX Required: ${total_capex/1e6:.1f} Million")
    print(f"💚 Net Cost-Saving Projects: {net_negative_projects}/{len(macc_df)}")
    print(f"📉 Average Cost: ${macc_df['lcoa_usd_per_tco2'].mean():.0f}/tCO2e")
    
    # Top 5 most cost-effective projects
    print(f"\n🏆 TOP 5 MOST COST-EFFECTIVE PROJECTS:")
    print("-" * 40)
    for i, (_, row) in enumerate(macc_df.head(5).iterrows(), 1):
        cost_str = f"${row['lcoa_usd_per_tco2']:.0f}/tCO2e" if row['lcoa_usd_per_tco2'] >= 0 else f"SAVES ${-row['lcoa_usd_per_tco2']:.0f}/tCO2e"
        print(f"{i}. {row['technology']}: {cost_str}")
        print(f"   Abatement: {row['annual_abatement_potential']:,.0f} tCO2e/year")
        print(f"   CAPEX: ${row['total_capex_required']/1e6:.1f}M")
    
    # Net-negative cost opportunities
    if net_negative_projects > 0:
        negative_cost_df = macc_df[macc_df['net_negative_cost']]
        total_savings = -negative_cost_df['lcoa_usd_per_tco2'].sum()
        savings_abatement = negative_cost_df['annual_abatement_potential'].sum()
        
        print(f"\n💰 NET COST-SAVING OPPORTUNITIES:")
        print(f"   Total Projects: {net_negative_projects}")
        print(f"   Total Abatement: {savings_abatement:,.0f} tCO2e/year")
        print(f"   Net Annual Savings: ${total_savings * savings_abatement/1e6:.1f}M/year")
    
    # Sector breakdown
    print(f"\n🏭 ABATEMENT BY SECTOR:")
    sector_breakdown = macc_df.groupby('sector')['annual_abatement_potential'].sum().sort_values(ascending=False)
    for sector, abatement in sector_breakdown.items():
        percentage = abatement / total_abatement * 100
        print(f"   {sector}: {abatement:,.0f} tCO2e/year ({percentage:.1f}%)")
    
    # Save detailed results
    output_path = "outputs/macc_analysis_results.csv"
    macc_df.to_csv(output_path, index=False)
    print(f"\n💾 Detailed results saved to: {output_path}")
    
    # Create visualization
    print("🎨 Creating MACC visualization...")
    macc_gen.visualize_macc_curve(macc_df, save_path="outputs/macc_curve.png")
    
    print("\n✅ MACC Generation Complete!")
    
    return macc_df


if __name__ == "__main__":
    # Create outputs directory if it doesn't exist
    import os
    os.makedirs("outputs", exist_ok=True)
    
    # Generate MACC
    macc_results = main()