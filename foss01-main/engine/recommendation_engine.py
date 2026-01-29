# engine/recommendation_engine.py
from typing import List, Dict, Any

class RecommendationEngine:
    """
    Rule-based recommendation engine for infrastructure improvements
    """
    
    def __init__(self):
        self.intervention_costs = {
            'minor_repairs': 0.5,        # Million $ per km
            'road_widening': 2.0,
            'flyover_construction': 15.0,
            'bridge_construction': 25.0,
            'traffic_management': 0.2
        }
    
    def generate_recommendation(self, scores: Dict[str, float]) -> Dict[str, Any]:
        """Generate recommendation based on scores"""
        if scores['congestion'] > 0.8:
            return {
                'action': 'Road Widening',
                'priority': 'HIGH',
                'rationale': 'Severe congestion detected',
                'estimated_cost': 'Medium-High',
                'expected_improvement': '35% congestion reduction'
            }
        elif scores['safety'] > 0.7:
            return {
                'action': 'Junction Redesign / Flyover',
                'priority': 'HIGH',
                'rationale': 'Safety risk above threshold',
                'estimated_cost': 'High',
                'expected_improvement': '40% accident reduction'
            }
        elif scores['structural'] > 0.6:
            return {
                'action': 'Road Resurfacing',
                'priority': 'MEDIUM',
                'rationale': 'Structural degradation detected',
                'estimated_cost': 'Medium',
                'expected_improvement': 'Extended road life by 10 years'
            }
        elif scores['growth'] > 0.7:
            return {
                'action': 'Capacity Expansion',
                'priority': 'MEDIUM',
                'rationale': 'High growth pressure',
                'estimated_cost': 'Medium-High',
                'expected_improvement': 'Support 50% more traffic'
            }
        else:
            return {
                'action': 'Routine Maintenance',
                'priority': 'LOW',
                'rationale': 'Preventive maintenance recommended',
                'estimated_cost': 'Low',
                'expected_improvement': 'Maintain current performance'
            }
    
    def prioritize_projects(self, recommendations: List[Dict]) -> List[Dict]:
        """Prioritize projects based on impact and cost"""
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        
        sorted_recommendations = sorted(
            recommendations,
            key=lambda x: priority_order.get(x['priority'], 3)
        )
        
        return sorted_recommendations
    
    def estimate_budget(self, recommendations: List[Dict]) -> Dict[str, float]:
        """Estimate total budget for recommendations"""
        budget = {
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'total': 0
        }
        
        cost_map = {
            'Road Widening': 2.5,
            'Junction Redesign / Flyover': 5.0,
            'Road Resurfacing': 1.0,
            'Capacity Expansion': 3.0,
            'Routine Maintenance': 0.3
        }
        
        for rec in recommendations:
            cost = cost_map.get(rec['action'], 1.0)
            budget[rec['priority']] += cost
            budget['total'] += cost
        
        return budget
