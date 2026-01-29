# models/explainable_ai.py
"""
Explainable AI module for infrastructure recommendations
Provides human-understandable explanations using SHAP and natural language
"""

from typing import Dict, List, Any, Tuple
import numpy as np


class ExplainableRecommender:
    """
    Provide human-understandable explanations for recommendations
    """
    
    def __init__(self):
        self.feature_names = [
            'traffic_flow', 'accident_risk', 'road_condition',
            'bottleneck_score', 'growth_pressure', 'junction_density',
            'population_density', 'commercial_activity', 'school_proximity',
            'hospital_proximity', 'peak_congestion', 'night_traffic'
        ]
    
    def explain_recommendation(self, road_segment: Dict, recommendation: Dict) -> str:
        """
        Generate natural language explanation
        """
        features = road_segment.get('features', {})
        
        # Calculate feature contributions (simplified SHAP-like values)
        shap_values = self._calculate_feature_contributions(features)
        
        # Top 3 contributing factors
        top_factors = sorted(
            zip(self.feature_names[:len(shap_values)], shap_values),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:3]
        
        # Generate explanation
        explanation = f"""
Recommendation: {recommendation.get('action', 'N/A')}

Why this is needed:
1. {top_factors[0][0]}: {self._format_factor_explanation(top_factors[0])}
2. {top_factors[1][0]}: {self._format_factor_explanation(top_factors[1])}
3. {top_factors[2][0]}: {self._format_factor_explanation(top_factors[2])}

Expected Impact:
• Congestion reduction: {recommendation.get('congestion_improvement', 'N/A')}%
• Safety improvement: {recommendation.get('safety_improvement', 'N/A')}%
• Cost: ${recommendation.get('cost', 'N/A'):,}
• ROI: {recommendation.get('roi', 'N/A')}x

Alternative considered: {recommendation.get('alternative', 'None')}
Why not chosen: {recommendation.get('alternative_reason', 'Primary recommendation is optimal')}
        """
        
        return explanation.strip()
    
    def _calculate_feature_contributions(self, features: Dict) -> List[float]:
        """
        Calculate feature contributions (simplified SHAP-like values)
        """
        # Simplified contribution calculation
        contributions = []
        
        default_features = {
            'traffic_flow': 0.5,
            'accident_risk': 0.3,
            'road_condition': 0.4,
            'bottleneck_score': 0.6,
            'growth_pressure': 0.5,
            'junction_density': 0.4
        }
        
        for name in self.feature_names[:6]:
            value = features.get(name, default_features.get(name, 0.5))
            # Contribution is deviation from average (0.5)
            contribution = value - 0.5
            contributions.append(contribution)
        
        return contributions
    
    def _format_factor_explanation(self, factor: Tuple[str, float]) -> str:
        """
        Convert feature contribution to natural language
        """
        name, value = factor
        
        explanations = {
            'traffic_flow': f"Traffic volume is {abs(value)*100:.0f}% above optimal level",
            'accident_risk': f"Accident risk is {abs(value)*100:.0f}% higher than city average",
            'road_condition': f"Road condition scores {abs(value)*100:.0f}% below acceptable standard",
            'bottleneck_score': f"Causes {abs(value)*100:.0f}% of network congestion",
            'growth_pressure': f"Area population growth requires {abs(value)*100:.0f}% more capacity",
            'junction_density': f"Junction complexity is {abs(value)*100:.0f}% above threshold"
        }
        
        return explanations.get(name, f"Significant factor ({value:.3f})")
    
    def generate_summary(self, recommendations: List[Dict]) -> str:
        """Generate executive summary of all recommendations"""
        total_cost = sum(r.get('cost', 0) for r in recommendations)
        high_priority = len([r for r in recommendations if r.get('priority') == 'HIGH'])
        
        summary = f"""
EXECUTIVE SUMMARY
=================
Total Recommendations: {len(recommendations)}
High Priority: {high_priority}
Estimated Total Investment: ${total_cost:,.0f}M

Key Actions Required:
"""
        
        for i, rec in enumerate(recommendations[:5], 1):
            summary += f"\n{i}. {rec.get('action', 'N/A')} - {rec.get('location', 'N/A')} ({rec.get('priority', 'N/A')})"
        
        return summary


class CounterfactualAnalyzer:
    """
    Analyze "what-if" scenarios
    """
    
    def __init__(self):
        self.intervention_effects = {
            'road_widening': {'congestion': -0.35, 'safety': 0.10, 'capacity': 0.50},
            'flyover': {'congestion': -0.45, 'safety': 0.20, 'capacity': 0.70},
            'traffic_signals': {'congestion': -0.15, 'safety': 0.25, 'capacity': 0.10},
            'resurfacing': {'congestion': -0.05, 'safety': 0.15, 'capacity': 0.05},
            'junction_redesign': {'congestion': -0.25, 'safety': 0.35, 'capacity': 0.20}
        }
    
    def analyze_scenarios(self, road_segment: Dict, interventions: List[str]) -> List[Dict]:
        """
        Compare different intervention scenarios
        """
        scenarios = []
        
        for intervention in interventions:
            # Simulate intervention effect
            simulated_state = self._simulate_intervention(road_segment, intervention)
            
            # Calculate metrics
            metrics = {
                'cost': self._estimate_cost(intervention, road_segment.get('length', 1)),
                'time': self._estimate_construction_time(intervention),
                'congestion_reduction': self._calculate_congestion_reduction(
                    road_segment, simulated_state
                ),
                'safety_improvement': self._calculate_safety_improvement(
                    road_segment, simulated_state
                ),
                'economic_impact': self._calculate_economic_impact(
                    road_segment, simulated_state
                )
            }
            
            scenarios.append({
                'intervention': intervention,
                'metrics': metrics,
                'net_benefit': self._calculate_net_benefit(metrics)
            })
        
        # Rank scenarios
        ranked_scenarios = sorted(
            scenarios, 
            key=lambda x: x['net_benefit'], 
            reverse=True
        )
        
        return ranked_scenarios
    
    def _simulate_intervention(self, road_segment: Dict, intervention: str) -> Dict:
        """Simulate the effect of an intervention"""
        effects = self.intervention_effects.get(intervention, {})
        
        simulated = road_segment.copy()
        simulated['congestion_score'] = max(0, road_segment.get('congestion_score', 0.5) + effects.get('congestion', 0))
        simulated['safety_score'] = min(1, road_segment.get('safety_score', 0.5) + effects.get('safety', 0))
        
        return simulated
    
    def _estimate_cost(self, intervention: str, length_km: float) -> float:
        """Estimate intervention cost in millions"""
        cost_per_km = {
            'road_widening': 2.5,
            'flyover': 15.0,
            'traffic_signals': 0.3,
            'resurfacing': 0.8,
            'junction_redesign': 3.0
        }
        return cost_per_km.get(intervention, 1.0) * length_km
    
    def _estimate_construction_time(self, intervention: str) -> int:
        """Estimate construction time in months"""
        times = {
            'road_widening': 12,
            'flyover': 24,
            'traffic_signals': 3,
            'resurfacing': 2,
            'junction_redesign': 8
        }
        return times.get(intervention, 6)
    
    def _calculate_congestion_reduction(self, before: Dict, after: Dict) -> float:
        """Calculate percentage congestion reduction"""
        before_score = before.get('congestion_score', 0.5)
        after_score = after.get('congestion_score', 0.5)
        if before_score == 0:
            return 0
        return (before_score - after_score) / before_score * 100
    
    def _calculate_safety_improvement(self, before: Dict, after: Dict) -> float:
        """Calculate percentage safety improvement"""
        before_score = before.get('safety_score', 0.5)
        after_score = after.get('safety_score', 0.5)
        if before_score == 0:
            return 0
        return (after_score - before_score) / (1 - before_score) * 100
    
    def _calculate_economic_impact(self, road_segment: Dict, simulated: Dict) -> float:
        """Calculate economic impact in millions per year"""
        # Simplified calculation
        traffic_volume = road_segment.get('traffic_volume', 10000)
        congestion_reduction = (
            road_segment.get('congestion_score', 0.5) - 
            simulated.get('congestion_score', 0.5)
        )
        
        # Time saved * traffic * value of time
        time_saved_hours = congestion_reduction * 0.5  # 30 min max saving
        annual_impact = traffic_volume * time_saved_hours * 365 * 15 / 1000000  # $15/hour value
        
        return annual_impact
    
    def _calculate_net_benefit(self, metrics: Dict) -> float:
        """Calculate net benefit score"""
        # Multi-year benefit (10 years) minus cost
        annual_benefit = metrics['economic_impact']
        total_benefit = annual_benefit * 10
        cost = metrics['cost']
        
        return total_benefit - cost
