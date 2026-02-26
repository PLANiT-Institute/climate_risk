"""
ESG Compliance and Climate Requirements Module
Links technical analysis to real-world ESG requirements and business applications
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta

class ESGComplianceAssessment:
    """
    Assess compliance with major ESG frameworks and climate requirements
    """
    
    def __init__(self, facilities_df: pd.DataFrame, macc_results: Dict = None, physical_risk_results: Dict = None):
        self.facilities_df = facilities_df
        self.macc_results = macc_results
        self.physical_risk_results = physical_risk_results
        
        # ESG Framework thresholds and requirements
        self.frameworks = {
            'tcfd': self._get_tcfd_requirements(),
            'eu_taxonomy': self._get_eu_taxonomy_requirements(),
            'sbti': self._get_sbti_requirements(),
            'cdp': self._get_cdp_requirements()
        }
    
    def _get_tcfd_requirements(self) -> Dict:
        """TCFD reporting requirements"""
        return {
            'governance': {
                'climate_board_oversight': True,
                'management_responsibility': True,
                'required_score': 80
            },
            'strategy': {
                'climate_risks_identified': True,
                'scenario_analysis_done': True,
                'business_impact_quantified': True,
                'required_score': 75
            },
            'risk_management': {
                'risk_identification_process': True,
                'risk_assessment_process': True,
                'integration_with_overall_risk': True,
                'required_score': 70
            },
            'metrics_targets': {
                'scope1_scope2_disclosed': True,
                'scope3_disclosed': True,
                'climate_targets_set': True,
                'progress_against_targets': True,
                'required_score': 85
            }
        }
    
    def _get_eu_taxonomy_requirements(self) -> Dict:
        """EU Taxonomy alignment requirements"""
        return {
            'substantial_contribution': {
                'climate_change_mitigation': 0.50,  # 50% revenue from eligible activities
                'climate_change_adaptation': 0.20,
                'required_alignment': 0.70
            },
            'do_no_significant_harm': {
                'environmental_objectives': 6,
                'minimum_safeguards': True,
                'technical_screening_criteria': True
            },
            'minimum_social_safeguards': {
                'oecd_guidelines': True,
                'un_global_compact': True,
                'ilo_conventions': True
            }
        }
    
    def _get_sbti_requirements(self) -> Dict:
        """Science Based Targets Initiative requirements"""
        return {
            'target_ambition': {
                'scope1_scope2_reduction': 0.045,  # 4.5% annual reduction for 1.5°C
                'scope3_reduction': 0.025,  # 2.5% annual reduction
                'target_year': 2030,
                'base_year': 2020
            },
            'target_boundary': {
                'scope1_included': True,
                'scope2_included': True,
                'scope3_required_if': 0.40  # If >40% of total emissions
            },
            'validation_criteria': {
                'approved_methods': ['absolute', 'sectoral_decarbonization', 'economic_intensity'],
                'timeframe': '5-15_years'
            }
        }
    
    def _get_cdp_requirements(self) -> Dict:
        """CDP Climate Change scoring criteria"""
        return {
            'disclosure_levels': {
                'A': {'min_score': 80, 'leadership': True},
                'A-': {'min_score': 75, 'management': True},
                'B': {'min_score': 65, 'management': True},
                'B-': {'min_score': 55, 'awareness': True},
                'C': {'min_score': 40, 'awareness': True}
            },
            'scoring_categories': {
                'governance': 0.25,
                'risk_opportunities': 0.30,
                'business_strategy': 0.20,
                'targets_performance': 0.25
            }
        }
    
    def assess_tcfd_compliance(self) -> Dict[str, Any]:
        """Assess TCFD compliance based on available data and analysis"""
        
        assessment = {}
        
        # Strategy pillar - check if scenario analysis done
        strategy_score = 0
        if self.macc_results and self.physical_risk_results:
            strategy_score += 60  # Scenario analysis partially done
            assessment['climate_risks_identified'] = True
            assessment['business_impact_quantified'] = True
        
        # Risk Management pillar
        risk_mgmt_score = 0
        if self.physical_risk_results:
            risk_mgmt_score += 50
            assessment['risk_identification_process'] = True
            assessment['risk_assessment_process'] = True
        
        # Metrics and Targets pillar
        metrics_score = 0
        if 'annual_emissions_scope1' in self.facilities_df.columns:
            metrics_score += 25
            assessment['scope1_disclosed'] = True
        if 'annual_emissions_scope2' in self.facilities_df.columns:
            metrics_score += 25
            assessment['scope2_disclosed'] = True
        if self.macc_results:
            metrics_score += 30
            assessment['climate_targets_feasible'] = True
        
        # Overall TCFD score
        overall_score = (strategy_score + risk_mgmt_score + metrics_score) / 3
        
        assessment.update({
            'overall_tcfd_score': overall_score,
            'strategy_score': strategy_score,
            'risk_management_score': risk_mgmt_score,
            'metrics_targets_score': metrics_score,
            'tcfd_compliance_level': self._get_compliance_level(overall_score),
            'improvement_recommendations': self._get_tcfd_recommendations(overall_score)
        })
        
        return assessment
    
    def assess_sbti_compliance(self) -> Dict[str, Any]:
        """Assess Science Based Targets compliance"""
        
        if not self.macc_results:
            return {'status': 'insufficient_data', 'message': 'MACC analysis required'}
        
        # Current emissions
        total_emissions = self.facilities_df['annual_emissions_tco2'].sum()
        
        # Required reduction for SBTi (4.5% per year for 1.5°C pathway)
        target_year = 2030
        base_year = 2024
        years_to_target = target_year - base_year
        required_annual_reduction = 0.045
        
        required_total_reduction = 1 - (1 - required_annual_reduction) ** years_to_target
        target_emissions = total_emissions * (1 - required_total_reduction)
        
        # Available abatement potential
        macc_df = self.macc_results.get('macc_df', pd.DataFrame())
        available_abatement = macc_df['annual_abatement_potential'].sum()
        
        # Calculate compliance metrics
        abatement_coverage = min(available_abatement / (total_emissions - target_emissions), 1.0) * 100
        
        assessment = {
            'current_emissions_tco2': total_emissions,
            'target_emissions_2030_tco2': target_emissions,
            'required_reduction_tco2': total_emissions - target_emissions,
            'available_abatement_tco2': available_abatement,
            'abatement_coverage_pct': abatement_coverage,
            'sbti_compliant': abatement_coverage >= 100,
            'annual_reduction_rate_required': required_annual_reduction * 100,
            'gap_analysis': max(0, (total_emissions - target_emissions) - available_abatement),
            'investment_required_for_compliance': self._calculate_sbti_investment_required(macc_df, total_emissions - target_emissions)
        }
        
        return assessment
    
    def assess_eu_taxonomy_alignment(self) -> Dict[str, Any]:
        """Assess EU Taxonomy alignment potential"""
        
        if not self.macc_results:
            return {'status': 'insufficient_data'}
        
        macc_df = self.macc_results.get('macc_df', pd.DataFrame())
        
        # Map MACC technologies to EU Taxonomy activities
        taxonomy_eligible_techs = {
            'Solar PV Installation': 'substantial_contribution',
            'Wind Power Installation': 'substantial_contribution', 
            'Energy Efficiency Retrofit': 'substantial_contribution',
            'Electric Vehicle Fleet': 'substantial_contribution',
            'Heat Pump Installation': 'substantial_contribution',
            'Green Hydrogen Production': 'substantial_contribution',
            'LED Lighting Upgrade': 'transitional_activity',
            'Building Insulation': 'substantial_contribution',
            'Waste Heat Recovery': 'enabling_activity',
            'Smart Energy Management': 'enabling_activity'
        }
        
        # Calculate alignment metrics
        eligible_investment = 0
        total_investment = macc_df['total_capex_required'].sum()
        
        for _, row in macc_df.iterrows():
            if row['technology'] in taxonomy_eligible_techs:
                eligible_investment += row['total_capex_required']
        
        alignment_percentage = (eligible_investment / total_investment) * 100 if total_investment > 0 else 0
        
        assessment = {
            'total_capex_million_usd': total_investment / 1e6,
            'taxonomy_eligible_capex_million_usd': eligible_investment / 1e6,
            'taxonomy_alignment_percentage': alignment_percentage,
            'substantial_contribution_activities': len([t for t in taxonomy_eligible_techs.values() if t == 'substantial_contribution']),
            'dnsh_assessment_required': alignment_percentage > 0,
            'minimum_safeguards_required': alignment_percentage > 0,
            'green_financing_eligible': alignment_percentage >= 50
        }
        
        return assessment
    
    def assess_cdp_scoring_potential(self) -> Dict[str, Any]:
        """Assess potential CDP Climate Change score"""
        
        base_score = 40  # Starting point
        
        # Governance points
        governance_score = 50  # Assume basic governance
        
        # Risk and Opportunities (enhanced by our analysis)
        risk_opp_score = 30
        if self.physical_risk_results:
            risk_opp_score += 25
        if self.macc_results:
            risk_opp_score += 20
        
        # Business Strategy
        strategy_score = 20
        if self.macc_results:
            strategy_score += 30
        
        # Targets and Performance
        targets_score = 20
        if 'annual_emissions_tco2' in self.facilities_df.columns:
            targets_score += 20
        if self.macc_results:
            targets_score += 25
        
        # Weighted CDP score
        cdp_requirements = self.frameworks['cdp']['scoring_categories']
        weighted_score = (
            governance_score * cdp_requirements['governance'] +
            risk_opp_score * cdp_requirements['risk_opportunities'] +
            strategy_score * cdp_requirements['business_strategy'] +
            targets_score * cdp_requirements['targets_performance']
        )
        
        # Determine CDP grade
        cdp_grade = self._get_cdp_grade(weighted_score)
        
        assessment = {
            'estimated_cdp_score': weighted_score,
            'estimated_cdp_grade': cdp_grade,
            'governance_score': governance_score,
            'risk_opportunities_score': risk_opp_score,
            'business_strategy_score': strategy_score,
            'targets_performance_score': targets_score,
            'improvement_potential': 100 - weighted_score
        }
        
        return assessment
    
    def calculate_business_benefits(self) -> Dict[str, Any]:
        """Calculate concrete business benefits from ESG compliance"""
        
        total_assets = self.facilities_df['asset_value_usd'].sum() if 'asset_value_usd' in self.facilities_df.columns else 0
        
        benefits = {
            'financing_benefits': {
                'green_bond_potential': total_assets * 0.02,  # 2% cost reduction
                'sustainability_linked_loan_savings': total_assets * 0.015,  # 1.5% cost reduction
                'insurance_premium_reduction': total_assets * 0.005  # 0.5% reduction
            },
            'market_access': {
                'esg_mandated_funds_access': True,
                'sustainable_supply_chain_opportunities': True,
                'government_procurement_preference': True
            },
            'risk_mitigation': {
                'regulatory_compliance': True,
                'reputation_protection': True,
                'investor_confidence': True
            }
        }
        
        # Calculate total financial benefit
        total_benefit = sum(benefits['financing_benefits'].values())
        benefits['total_annual_financial_benefit'] = total_benefit
        
        return benefits
    
    def _get_compliance_level(self, score: float) -> str:
        """Get compliance level based on score"""
        if score >= 80:
            return "Excellent"
        elif score >= 65:
            return "Good"
        elif score >= 50:
            return "Adequate"
        else:
            return "Needs Improvement"
    
    def _get_tcfd_recommendations(self, score: float) -> List[str]:
        """Get TCFD improvement recommendations"""
        recommendations = []
        
        if score < 80:
            recommendations.extend([
                "Enhance scenario analysis with quantitative financial impact assessment",
                "Develop climate risk management processes integrated with enterprise risk management",
                "Set science-based targets aligned with 1.5°C pathway",
                "Improve disclosure of Scope 3 emissions and climate-related governance"
            ])
        
        return recommendations
    
    def _calculate_sbti_investment_required(self, macc_df: pd.DataFrame, required_reduction: float) -> float:
        """Calculate investment required for SBTi compliance"""
        if macc_df.empty:
            return 0
        
        # Sort by cost-effectiveness
        macc_sorted = macc_df.sort_values('lcoa_usd_per_tco2')
        
        cumulative_abatement = 0
        investment_required = 0
        
        for _, row in macc_sorted.iterrows():
            if cumulative_abatement >= required_reduction:
                break
            cumulative_abatement += row['annual_abatement_potential']
            investment_required += row['total_capex_required']
        
        return investment_required
    
    def _get_cdp_grade(self, score: float) -> str:
        """Convert CDP score to letter grade"""
        if score >= 80:
            return "A"
        elif score >= 75:
            return "A-"
        elif score >= 65:
            return "B"
        elif score >= 55:
            return "B-"
        elif score >= 40:
            return "C"
        else:
            return "D"
    
    def generate_comprehensive_assessment(self) -> Dict[str, Any]:
        """Generate comprehensive ESG compliance assessment"""
        
        assessment = {
            'assessment_date': datetime.now().strftime('%Y-%m-%d'),
            'tcfd_assessment': self.assess_tcfd_compliance(),
            'sbti_assessment': self.assess_sbti_compliance(),
            'eu_taxonomy_assessment': self.assess_eu_taxonomy_alignment(),
            'cdp_assessment': self.assess_cdp_scoring_potential(),
            'business_benefits': self.calculate_business_benefits()
        }
        
        # Overall ESG readiness score
        tcfd_score = assessment['tcfd_assessment'].get('overall_tcfd_score', 0)
        sbti_coverage = assessment['sbti_assessment'].get('abatement_coverage_pct', 0) / 100
        taxonomy_alignment = assessment['eu_taxonomy_assessment'].get('taxonomy_alignment_percentage', 0) / 100
        cdp_score = assessment['cdp_assessment'].get('estimated_cdp_score', 0) / 100
        
        overall_esg_score = (tcfd_score + sbti_coverage * 100 + taxonomy_alignment * 100 + cdp_score * 100) / 4
        
        assessment['overall_esg_readiness'] = {
            'score': overall_esg_score,
            'grade': self._get_compliance_level(overall_esg_score),
            'investment_priority': 'High' if overall_esg_score < 70 else 'Medium' if overall_esg_score < 85 else 'Low'
        }
        
        return assessment