"""
Advanced Analysis Engine for InfraSense AI
Performs comprehensive traffic pattern analysis with frequency-based decision making
Key Intelligence: Uses traffic frequency (days/week) to make smart intervention decisions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrafficPattern:
    """Traffic pattern analysis for a road segment"""
    road_id: str
    daily_patterns: Dict[str, float]  # Date -> congestion score
    weekly_average: float
    high_traffic_days: List[str]
    frequency_score: float  # 0-1, frequency of high traffic
    peak_hours: List[int]
    trend: str  # "increasing", "decreasing", "stable"
    seasonality: Optional[Dict[str, float]] = None


@dataclass
class CongestionMetrics:
    """Congestion metrics for a road segment"""
    avg_congestion: float
    max_congestion: float
    peak_congestion: float


@dataclass 
class Problem:
    """Identified problem on a road segment"""
    type: str
    severity: str
    description: str
    impact: str


@dataclass
class Recommendation:
    """Intervention recommendation"""
    type: str
    priority: str
    description: str
    reason: str
    estimated_cost: float
    timeline: str
    impact: str = ""


@dataclass
class RoadAnalysis:
    """Complete analysis for a road segment"""
    road_id: str
    name: str
    road_type: str
    length_km: float
    lanes: int
    geometry: List[List[float]]
    traffic_patterns: TrafficPattern
    congestion_metrics: CongestionMetrics
    needs_intervention: bool
    priority: str
    problems: List[Problem]
    recommendations: List[Recommendation]

class AdvancedAnalysisEngine:
    """
    Advanced analysis engine for infrastructure assessment.
    Uses traffic frequency logic to determine intervention needs.
    """
    
    def __init__(self):
        self.congestion_threshold = 0.7  # 70% congestion threshold
        self.frequency_threshold = 4  # Default: 4 days/week
        
        # Cost estimates by intervention type (in Crores INR)
        self.cost_estimates = {
            'flyover': {'min': 50, 'max': 200},
            'widening': {'min': 20, 'max': 100},
            'bridge': {'min': 30, 'max': 150},
            'signals': {'min': 2, 'max': 10},
            'maintenance': {'min': 5, 'max': 30},
            'planning': {'min': 1, 'max': 5}
        }
        
        # Timeline estimates
        self.timeline_estimates = {
            'flyover': '18-24 months',
            'widening': '12-18 months',
            'bridge': '15-24 months',
            'signals': '2-4 weeks',
            'maintenance': '3-6 months',
            'planning': '6-12 months'
        }
    
    def analyze_area(
        self, 
        area_polygon: List[List[float]], 
        time_range_days: int = 30,
        frequency_threshold: int = 4
    ) -> Dict:
        """
        Comprehensive analysis of an area.
        Returns detailed analysis with traffic frequency logic.
        """
        self.frequency_threshold = frequency_threshold
        
        # Generate road network analysis
        roads = self._generate_road_analysis(area_polygon, time_range_days)
        
        # Calculate summary statistics
        summary = self._generate_summary(roads)
        
        # Calculate area-wide metrics
        area_metrics = self._calculate_area_metrics(roads)
        
        return {
            'roads': [self._road_to_dict(r) for r in roads],
            'summary': summary,
            'area_metrics': area_metrics,
            'filters_applied': {
                'time_range_days': time_range_days,
                'frequency_threshold': frequency_threshold
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_road_analysis(
        self, 
        area_polygon: List[List[float]], 
        time_range_days: int
    ) -> List[RoadAnalysis]:
        """Generate analysis for roads in the area"""
        
        road_names = [
            'NH-48 Delhi-Gurgaon Highway', 'Ring Road Junction', 'MG Road Corridor',
            'Outer Ring Road Sector 21', 'Dwarka Expressway', 'Sohna Road',
            'Golf Course Extension Road', 'Sector 56 Main Road', 'Cyber City Road',
            'Old Delhi Road', 'Mehrauli-Gurgaon Road', 'Palam Vihar Road',
            'Hero Honda Chowk', 'IFFCO Chowk Junction', 'Huda City Centre Road',
            'Sikanderpur Metro Road', 'Bristol Chowk', 'Vatika Chowk Junction',
            'Subhash Chowk', 'Rajiv Chowk'
        ]
        
        road_types = ['highway', 'primary', 'secondary', 'tertiary']
        
        # Calculate center of polygon
        if area_polygon and len(area_polygon) > 0:
            center_lat = sum(p[0] for p in area_polygon) / len(area_polygon)
            center_lng = sum(p[1] for p in area_polygon) / len(area_polygon)
        else:
            center_lat, center_lng = 28.4595, 77.0266  # Default: Gurgaon
        
        roads = []
        
        for i, name in enumerate(road_names[:15]):
            # Generate road geometry
            lat1 = center_lat + (random.random() - 0.5) * 0.15
            lng1 = center_lng + (random.random() - 0.5) * 0.15
            lat2 = lat1 + (random.random() - 0.5) * 0.03
            lng2 = lng1 + (random.random() - 0.5) * 0.03
            
            # Generate traffic patterns
            traffic_days = random.randint(1, 7)
            frequency_score = traffic_days / 7
            
            # Generate congestion metrics
            avg_congestion = random.random() * 0.7 + 0.2
            max_congestion = min(avg_congestion + random.random() * 0.3, 1.0)
            
            # Determine if intervention needed based on frequency
            needs_intervention = traffic_days >= self.frequency_threshold
            
            # Calculate priority
            priority = self._calculate_priority(frequency_score, avg_congestion, needs_intervention)
            
            # Generate problems
            problems = self._generate_problems(
                traffic_days, avg_congestion, max_congestion, needs_intervention
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                traffic_days, frequency_score, avg_congestion, max_congestion, 
                needs_intervention, priority
            )
            
            road_type = road_types[i % len(road_types)]
            lanes = random.choice([2, 4, 6])
            
            traffic_patterns = TrafficPattern(
                road_id=f'road_{i+1}',
                traffic_days_per_week=traffic_days,
                frequency_score=frequency_score,
                high_traffic_percentage=frequency_score * 100,
                peak_hours=[8, 9, 17, 18, 19],
                trend=random.choice(['increasing', 'stable', 'decreasing']),
                weekly_pattern={
                    'Monday': random.random() * 0.5 + 0.5,
                    'Tuesday': random.random() * 0.5 + 0.4,
                    'Wednesday': random.random() * 0.5 + 0.4,
                    'Thursday': random.random() * 0.5 + 0.5,
                    'Friday': random.random() * 0.3 + 0.7,
                    'Saturday': random.random() * 0.4 + 0.3,
                    'Sunday': random.random() * 0.3 + 0.2
                }
            )
            
            congestion_metrics = CongestionMetrics(
                avg_congestion=avg_congestion,
                max_congestion=max_congestion,
                peak_congestion=max_congestion
            )
            
            roads.append(RoadAnalysis(
                road_id=f'road_{i+1}',
                name=name,
                road_type=road_type,
                length_km=round(random.random() * 5 + 1, 1),
                lanes=lanes,
                geometry=[[lat1, lng1], [lat2, lng2]],
                traffic_patterns=traffic_patterns,
                congestion_metrics=congestion_metrics,
                needs_intervention=needs_intervention,
                priority=priority,
                problems=problems,
                recommendations=recommendations
            ))
        
        return roads
    
    def _calculate_priority(
        self, 
        frequency_score: float, 
        avg_congestion: float,
        needs_intervention: bool
    ) -> str:
        """Calculate priority level based on frequency and congestion"""
        
        if not needs_intervention:
            return 'monitor'
        
        score = (frequency_score * 0.6) + (avg_congestion * 0.4)
        
        if score >= 0.8:
            return 'critical'
        elif score >= 0.6:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _generate_problems(
        self,
        traffic_days: int,
        avg_congestion: float,
        max_congestion: float,
        needs_intervention: bool
    ) -> List[Problem]:
        """Generate identified problems based on metrics"""
        
        problems = []
        
        if not needs_intervention:
            return problems
        
        # Congestion problem
        if avg_congestion >= 0.6:
            severity = 'critical' if avg_congestion >= 0.8 else 'high' if avg_congestion >= 0.7 else 'medium'
            problems.append(Problem(
                type='congestion',
                severity=severity,
                description=f'Traffic congestion occurs {traffic_days} days per week with {avg_congestion*100:.0f}% average load',
                impact=f'Average delay of {int(avg_congestion * 30)} minutes during peak hours'
            ))
        
        # Capacity problem
        if traffic_days >= 5 and avg_congestion >= 0.7:
            problems.append(Problem(
                type='capacity',
                severity='high',
                description='Road capacity insufficient for current traffic volume',
                impact='Bottleneck causing delays throughout the corridor'
            ))
        
        # Safety concern (random for demo)
        if random.random() > 0.7:
            problems.append(Problem(
                type='safety',
                severity='medium',
                description='Multiple conflict points identified at intersections',
                impact='Increased accident risk during peak hours'
            ))
        
        return problems
    
    def _generate_recommendations(
        self,
        traffic_days: int,
        frequency_score: float,
        avg_congestion: float,
        max_congestion: float,
        needs_intervention: bool,
        priority: str
    ) -> List[Recommendation]:
        """Generate intervention recommendations based on analysis"""
        
        recommendations = []
        
        if not needs_intervention:
            return recommendations
        
        # Flyover recommendation for severe congestion at junctions
        if max_congestion >= 0.8 and traffic_days >= 5:
            cost = random.randint(
                self.cost_estimates['flyover']['min'],
                self.cost_estimates['flyover']['max']
            )
            recommendations.append(Recommendation(
                type='flyover',
                priority='high' if priority in ['critical', 'high'] else 'medium',
                description='Construct grade-separated flyover at major junction',
                reason=f'Peak congestion at {max_congestion*100:.0f}% occurring {traffic_days} days/week requires grade separation',
                estimated_cost=cost,
                timeline=self.timeline_estimates['flyover'],
                impact='Reduce intersection delays by 60-70%'
            ))
        
        # Road widening for capacity issues
        if avg_congestion >= 0.65 and traffic_days >= 4:
            cost = random.randint(
                self.cost_estimates['widening']['min'],
                self.cost_estimates['widening']['max']
            )
            recommendations.append(Recommendation(
                type='widening',
                priority='high' if avg_congestion >= 0.75 else 'medium',
                description='Widen road from 4 to 6 lanes',
                reason=f'Average congestion of {avg_congestion*100:.0f}% on {traffic_days} days/week indicates capacity shortage',
                estimated_cost=cost,
                timeline=self.timeline_estimates['widening'],
                impact='Increase road capacity by 50%'
            ))
        
        # Signal optimization for moderate congestion
        if avg_congestion >= 0.5 and traffic_days >= 3:
            cost = random.randint(
                self.cost_estimates['signals']['min'],
                self.cost_estimates['signals']['max']
            )
            recommendations.append(Recommendation(
                type='signals',
                priority='medium',
                description='Install smart traffic signal system with adaptive timing',
                reason='Optimize signal cycles to reduce delays during peak hours',
                estimated_cost=cost,
                timeline=self.timeline_estimates['signals'],
                impact='Reduce average wait time by 20-30%'
            ))
        
        # Maintenance if random condition is poor
        if random.random() > 0.6:
            cost = random.randint(
                self.cost_estimates['maintenance']['min'],
                self.cost_estimates['maintenance']['max']
            )
            recommendations.append(Recommendation(
                type='maintenance',
                priority='medium',
                description='Major road surface rehabilitation',
                reason='Road condition deteriorating due to heavy traffic',
                estimated_cost=cost,
                timeline=self.timeline_estimates['maintenance'],
                impact='Improve ride quality and reduce vehicle damage'
            ))
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        return recommendations
    
    def _generate_summary(self, roads: List[RoadAnalysis]) -> Dict:
        """Generate summary statistics"""
        
        critical_count = sum(1 for r in roads if r.priority == 'critical')
        high_count = sum(1 for r in roads if r.priority == 'high')
        medium_count = sum(1 for r in roads if r.priority == 'medium')
        low_count = sum(1 for r in roads if r.priority == 'low')
        monitor_count = sum(1 for r in roads if r.priority == 'monitor')
        
        intervention_roads = [r for r in roads if r.needs_intervention]
        
        flyovers_needed = sum(1 for r in intervention_roads 
                            if any(rec.type == 'flyover' for rec in r.recommendations))
        widening_needed = sum(1 for r in intervention_roads 
                            if any(rec.type == 'widening' for rec in r.recommendations))
        
        total_cost = 0
        for r in roads:
            for rec in r.recommendations:
                total_cost += rec.estimated_cost
        
        return {
            'totalRoads': len(roads),
            'criticalRoads': critical_count,
            'highPriorityRoads': high_count,
            'mediumPriorityRoads': medium_count,
            'lowPriorityRoads': low_count,
            'monitorOnly': monitor_count,
            'interventionsNeeded': len(intervention_roads),
            'flyoversNeeded': flyovers_needed,
            'wideningNeeded': widening_needed,
            'totalEstimatedCost': round(total_cost, 2)
        }
    
    def _calculate_area_metrics(self, roads: List[RoadAnalysis]) -> Dict:
        """Calculate area-wide metrics"""
        
        if not roads:
            return {
                'avgFrequency': 0,
                'avgCongestion': 0,
                'peakHour': 18
            }
        
        avg_frequency = sum(r.traffic_patterns.frequency_score for r in roads) / len(roads)
        avg_congestion = sum(r.congestion_metrics.avg_congestion for r in roads) / len(roads)
        
        return {
            'avgFrequency': round(avg_frequency, 2),
            'avgCongestion': round(avg_congestion, 2),
            'peakHour': 18
        }
    
    def _road_to_dict(self, road: RoadAnalysis) -> Dict:
        """Convert RoadAnalysis to dictionary"""
        return {
            'id': road.road_id,
            'name': road.name,
            'roadType': road.road_type,
            'lengthKm': road.length_km,
            'lanes': road.lanes,
            'geometry': road.geometry,
            'trafficPatterns': {
                'trafficDaysPerWeek': road.traffic_patterns.traffic_days_per_week,
                'frequencyScore': road.traffic_patterns.frequency_score,
                'highTrafficPercentage': road.traffic_patterns.high_traffic_percentage,
                'peakHours': road.traffic_patterns.peak_hours,
                'trend': road.traffic_patterns.trend,
                'weeklyPattern': road.traffic_patterns.weekly_pattern
            },
            'congestionMetrics': {
                'avgCongestion': road.congestion_metrics.avg_congestion,
                'maxCongestion': road.congestion_metrics.max_congestion,
                'peakCongestion': road.congestion_metrics.peak_congestion
            },
            'needsIntervention': road.needs_intervention,
            'priority': road.priority,
            'problems': [
                {
                    'type': p.type,
                    'severity': p.severity,
                    'description': p.description,
                    'impact': p.impact
                } for p in road.problems
            ],
            'recommendations': [
                {
                    'type': r.type,
                    'priority': r.priority,
                    'description': r.description,
                    'reason': r.reason,
                    'estimatedCost': r.estimated_cost,
                    'timeline': r.timeline,
                    'impact': r.impact
                } for r in road.recommendations
            ]
        }


# Create singleton instance
analysis_engine = AdvancedAnalysisEngine()


def analyze_traffic_frequency(road_id: str, days: int = 30) -> Dict:
    """
    Analyze traffic frequency for a specific road.
    
    Returns decision on whether intervention is needed based on:
    - Traffic frequency (how many days per week has congestion)
    - Traffic severity (how bad is the congestion)
    """
    # Simulated historical data
    traffic_days = random.randint(1, 7)
    avg_congestion = random.random() * 0.8 + 0.2
    
    # Decision logic
    # If traffic < 4 days/week -> Monitor only
    # If traffic >= 4 days/week -> Needs intervention
    needs_intervention = traffic_days >= 4
    
    return {
        'road_id': road_id,
        'analysis_period_days': days,
        'traffic_days_per_week': traffic_days,
        'frequency_percentage': (traffic_days / 7) * 100,
        'average_congestion': avg_congestion * 100,
        'decision': 'NEEDS_INTERVENTION' if needs_intervention else 'MONITOR_ONLY',
        'reason': f'Traffic congestion occurs {traffic_days}/7 days per week' + 
                  (f' (above threshold of 4 days)' if needs_intervention else ' (below threshold of 4 days)'),
        'recommended_action': 'Evaluate for infrastructure improvement' if needs_intervention 
                             else 'Continue monitoring, no immediate action required'
    }
