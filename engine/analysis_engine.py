# engine/analysis_engine.py
"""
InfraSense AI - Real Infrastructure Analysis Engine
Implements actual ISI (Infrastructure Stress Index) calculations
using real data from Google Maps, OSM, and other sources
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import math

# Import our data clients
try:
    from .google_maps_client import (
        google_maps_client, 
        osm_fetcher, 
        population_fetcher,
        GoogleMapsClient,
        OSMDataFetcher
    )
except ImportError:
    from google_maps_client import (
        google_maps_client, 
        osm_fetcher, 
        population_fetcher,
        GoogleMapsClient,
        OSMDataFetcher
    )


@dataclass
class RoadMetrics:
    """Complete metrics for a road segment"""
    segment_id: str
    name: str
    road_type: str
    length_km: float
    lanes: int
    coordinates: List[List[float]]
    
    # Calculated scores (0-1 scale)
    congestion_score: float
    safety_score: float
    growth_pressure_score: float
    road_quality_score: float
    isi_score: float  # Infrastructure Stress Index
    
    # Raw metrics
    current_traffic_volume: int
    road_capacity: int
    peak_hour_factor: float
    accident_count_3yr: int
    dangerous_junctions: int
    poor_visibility_segments: int
    population_growth_rate: float
    new_construction_permits: int
    pavement_condition_index: float
    bridge_age_years: Optional[int]
    
    # Derived
    priority: str  # HIGH, MEDIUM, LOW
    recommendation: str
    recommendation_reason: str
    estimated_cost: float
    expected_impact: str


class InfraSenseEngine:
    """
    Main analysis engine for InfraSense AI
    Calculates real Infrastructure Stress Index (ISI) using:
    
    ISI = 0.35 * Congestion_Score
        + 0.30 * Safety_Score
        + 0.25 * Growth_Pressure_Score
        + 0.10 * Road_Quality_Score
    """
    
    def __init__(self):
        self.google_client = google_maps_client
        self.osm_client = osm_fetcher
        self.population_client = population_fetcher
        
        # ISI Weights
        self.weights = {
            'congestion': 0.35,
            'safety': 0.30,
            'growth_pressure': 0.25,
            'road_quality': 0.10
        }
        
        # Road type capacities (vehicles per hour per lane)
        self.road_capacities = {
            'motorway': 2200,
            'trunk': 1800,
            'primary': 1500,
            'secondary': 1200,
            'tertiary': 900,
            'residential': 600,
            'unclassified': 500
        }
        
        # Standard widths per road type (meters)
        self.standard_widths = {
            'motorway': 14.0,
            'trunk': 12.0,
            'primary': 10.5,
            'secondary': 9.0,
            'tertiary': 7.5,
            'residential': 6.0,
            'unclassified': 5.5
        }
        
    def analyze_area(self, polygon_coords: List[List[float]], 
                     analysis_depth: str = "standard") -> Dict[str, Any]:
        """
        Main analysis entry point
        Returns complete analysis with scored roads and recommendations
        """
        print(f"Starting analysis for polygon with {len(polygon_coords)} vertices...")
        
        # 1. Get bounding box
        min_lng, max_lng, min_lat, max_lat = self._get_bounding_box(polygon_coords)
        
        # 2. Fetch road network from OSM (more detailed than Google)
        print("Fetching road network from OpenStreetMap...")
        osm_roads = self.osm_client.get_roads_in_bbox(min_lat, min_lng, max_lat, max_lng)
        
        # 3. Enrich with Google Maps traffic data
        print(f"Found {len(osm_roads)} road segments. Enriching with traffic data...")
        enriched_roads = self._enrich_with_traffic_data(osm_roads, polygon_coords)
        
        # 4. Get accident hotspots
        print("Searching for accident hotspots...")
        accident_hotspots = self.google_client.search_accident_hotspots(polygon_coords)
        
        # 5. Calculate scores for each road
        print("Calculating Infrastructure Stress Index scores...")
        scored_roads = []
        for road in enriched_roads:
            metrics = self._calculate_road_metrics(road, accident_hotspots, polygon_coords)
            if metrics:
                scored_roads.append(metrics)
        
        # 6. Generate recommendations
        print("Generating recommendations...")
        recommendations = self._generate_all_recommendations(scored_roads)
        
        # 7. Create summary
        summary = self._generate_summary(scored_roads, recommendations)
        
        return {
            'roads': self._metrics_to_geojson(scored_roads),
            'recommendations': recommendations,
            'summary': summary,
            'accident_hotspots': accident_hotspots,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _get_bounding_box(self, polygon_coords: List[List[float]]) -> Tuple[float, float, float, float]:
        """Get bounding box from polygon coordinates"""
        lngs = [c[0] for c in polygon_coords]
        lats = [c[1] for c in polygon_coords]
        return min(lngs), max(lngs), min(lats), max(lats)
    
    def _enrich_with_traffic_data(self, roads: List[Dict], 
                                   polygon_coords: List[List[float]]) -> List[Dict]:
        """Add real traffic data to road segments"""
        enriched = []
        
        for i, road in enumerate(roads):
            # Skip roads outside polygon
            if not self._road_in_polygon(road, polygon_coords):
                continue
            
            # Get traffic data for road segment
            coords = road.get('coordinates', [])
            if len(coords) >= 2:
                start = coords[0]
                end = coords[-1]
                
                # Get traffic from Google Maps
                traffic = self.google_client.get_traffic_data(
                    f"{start[1]},{start[0]}",
                    f"{end[1]},{end[0]}"
                )
                
                road['traffic_data'] = {
                    'current_speed': traffic.current_speed,
                    'free_flow_speed': traffic.free_flow_speed,
                    'congestion_level': traffic.congestion_level,
                    'delay_minutes': traffic.delay_minutes
                }
            else:
                road['traffic_data'] = {
                    'current_speed': 40,
                    'free_flow_speed': 50,
                    'congestion_level': 0.3,
                    'delay_minutes': 1
                }
            
            enriched.append(road)
            
            # Limit to avoid API quota issues
            if i >= 50:
                break
        
        return enriched
    
    def _road_in_polygon(self, road: Dict, polygon_coords: List[List[float]]) -> bool:
        """Check if road's center point is within polygon"""
        coords = road.get('coordinates', [])
        if not coords:
            return False
        
        # Check center point
        center_lng = sum(c[0] for c in coords) / len(coords)
        center_lat = sum(c[1] for c in coords) / len(coords)
        
        return self._point_in_polygon(center_lng, center_lat, polygon_coords)
    
    def _point_in_polygon(self, x: float, y: float, 
                          polygon: List[List[float]]) -> bool:
        """Ray casting algorithm for point-in-polygon test"""
        n = len(polygon)
        inside = False
        
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i][0], polygon[i][1]
            xj, yj = polygon[j][0], polygon[j][1]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        return inside
    
    def _calculate_road_metrics(self, road: Dict, 
                                 accident_hotspots: List[Dict],
                                 polygon_coords: List[List[float]]) -> Optional[RoadMetrics]:
        """
        Calculate all metrics for a road segment
        Implements the real ISI formula
        """
        try:
            segment_id = road.get('segment_id', 'unknown')
            name = road.get('name', 'Unnamed Road')
            road_type = road.get('road_type', 'unclassified')
            length_km = road.get('length_km', 0.5)
            lanes = road.get('lanes', 2)
            coords = road.get('coordinates', [])
            traffic = road.get('traffic_data', {})
            
            # Get road center for location-based calculations
            if coords:
                center_lat = sum(c[1] for c in coords) / len(coords)
                center_lng = sum(c[0] for c in coords) / len(coords)
            else:
                return None
            
            # ========================================
            # 1. CONGESTION SCORE
            # Congestion = (Traffic Volume / Capacity) * Peak_Hour_Factor
            # ========================================
            
            # Estimate traffic volume from speed reduction
            base_capacity = self.road_capacities.get(road_type, 800)
            road_capacity = base_capacity * lanes
            
            # Estimate current traffic from congestion level
            congestion_level = traffic.get('congestion_level', 0.3)
            current_volume = int(road_capacity * (0.3 + congestion_level * 0.7))
            
            # Peak hour factor (1.0-1.5 based on time of day)
            hour = datetime.now().hour
            if 7 <= hour <= 9 or 17 <= hour <= 19:
                peak_hour_factor = 1.4
            elif 10 <= hour <= 16:
                peak_hour_factor = 1.1
            else:
                peak_hour_factor = 1.0
            
            # Calculate congestion score
            volume_capacity_ratio = current_volume / max(road_capacity, 1)
            congestion_score = min(1.0, volume_capacity_ratio * peak_hour_factor)
            
            # ========================================
            # 2. SAFETY SCORE
            # Safety = (Accidents * 0.4) + (Dangerous_Junctions * 0.3) + (Poor_Visibility * 0.3)
            # ========================================
            
            # Count nearby accident hotspots
            accident_count = 0
            for hotspot in accident_hotspots:
                hotspot_lat, hotspot_lng = hotspot['location']
                dist = self._haversine_distance(center_lat, center_lng, hotspot_lat, hotspot_lng)
                if dist < 0.5:  # Within 500m
                    accident_count += 1
            
            # Estimate dangerous junctions (intersections)
            junction_density = self._estimate_junction_density(road, coords)
            dangerous_junctions = max(0, junction_density - 2)  # More than 2 per km is dangerous
            
            # Poor visibility based on road characteristics
            poor_visibility = 0
            if road_type in ['motorway', 'trunk']:
                poor_visibility = 0
            elif length_km > 1 and lanes < 3:
                poor_visibility = 1
            
            # Calculate safety score (higher = more dangerous)
            accident_factor = min(1.0, accident_count * 0.3)
            junction_factor = min(1.0, dangerous_junctions * 0.2)
            visibility_factor = poor_visibility * 0.3
            
            safety_score = (accident_factor * 0.4 + 
                          junction_factor * 0.3 + 
                          visibility_factor * 0.3)
            
            # ========================================
            # 3. GROWTH PRESSURE SCORE
            # Growth = (Pop_Growth * 0.5) + (Construction * 0.3) + (Transit_Usage * 0.2)
            # ========================================
            
            # Get population data
            pop_density = self.population_client.get_population_density(center_lat, center_lng)
            pop_growth_rate = self.population_client.get_growth_rate("default")
            
            # Estimate construction activity (based on population density)
            construction_activity = min(1.0, pop_density / 10000)  # Normalize
            
            # Transit usage estimate
            transit_usage = 0.3 if road_type in ['primary', 'secondary'] else 0.1
            
            # Calculate growth pressure
            growth_pressure_score = (
                min(1.0, pop_growth_rate * 20) * 0.5 +  # 5% growth = 1.0
                construction_activity * 0.3 +
                transit_usage * 0.2
            )
            
            # ========================================
            # 4. ROAD QUALITY SCORE
            # Quality = (Pavement_Condition * 0.6) + (Bridge_Age * 0.4)
            # ========================================
            
            # Estimate pavement condition based on road type
            surface = road.get('surface', 'asphalt')
            pavement_scores = {
                'asphalt': 0.2,
                'concrete': 0.15,
                'paved': 0.3,
                'unpaved': 0.8,
                'gravel': 0.7,
                'dirt': 0.9
            }
            pavement_condition = pavement_scores.get(surface, 0.4)
            
            # Check for bridges (would need actual bridge data)
            bridge_age_years = None  # Not available from basic OSM data
            bridge_score = 0.3  # Default assumption
            
            road_quality_score = (pavement_condition * 0.6 + bridge_score * 0.4)
            
            # ========================================
            # 5. CALCULATE ISI (Infrastructure Stress Index)
            # ========================================
            
            isi_score = (
                self.weights['congestion'] * congestion_score +
                self.weights['safety'] * safety_score +
                self.weights['growth_pressure'] * growth_pressure_score +
                self.weights['road_quality'] * road_quality_score
            )
            
            # ========================================
            # 6. DETERMINE PRIORITY AND RECOMMENDATION
            # ========================================
            
            priority, recommendation, reason, cost, impact = self._determine_recommendation(
                isi_score=isi_score,
                congestion_score=congestion_score,
                safety_score=safety_score,
                growth_pressure_score=growth_pressure_score,
                road_quality_score=road_quality_score,
                road_type=road_type,
                lanes=lanes,
                length_km=length_km,
                dangerous_junctions=dangerous_junctions
            )
            
            return RoadMetrics(
                segment_id=segment_id,
                name=name,
                road_type=road_type,
                length_km=length_km,
                lanes=lanes,
                coordinates=coords,
                congestion_score=congestion_score,
                safety_score=safety_score,
                growth_pressure_score=growth_pressure_score,
                road_quality_score=road_quality_score,
                isi_score=isi_score,
                current_traffic_volume=current_volume,
                road_capacity=road_capacity,
                peak_hour_factor=peak_hour_factor,
                accident_count_3yr=accident_count * 12,  # Estimate 3-year from current
                dangerous_junctions=dangerous_junctions,
                poor_visibility_segments=poor_visibility,
                population_growth_rate=pop_growth_rate,
                new_construction_permits=int(construction_activity * 100),
                pavement_condition_index=1 - pavement_condition,
                bridge_age_years=bridge_age_years,
                priority=priority,
                recommendation=recommendation,
                recommendation_reason=reason,
                estimated_cost=cost,
                expected_impact=impact
            )
            
        except Exception as e:
            print(f"Error calculating metrics for road: {e}")
            return None
    
    def _estimate_junction_density(self, road: Dict, coords: List[List[float]]) -> float:
        """Estimate number of junctions per km"""
        length = road.get('length_km', 1)
        road_type = road.get('road_type', 'secondary')
        
        # Estimate based on road type
        base_density = {
            'motorway': 0.5,
            'trunk': 1.0,
            'primary': 2.0,
            'secondary': 3.0,
            'tertiary': 4.0,
            'residential': 5.0
        }
        
        return base_density.get(road_type, 3.0)
    
    def _determine_recommendation(self, isi_score: float, congestion_score: float,
                                   safety_score: float, growth_pressure_score: float,
                                   road_quality_score: float, road_type: str,
                                   lanes: int, length_km: float,
                                   dangerous_junctions: int) -> Tuple[str, str, str, float, str]:
        """
        Intelligent recommendation engine based on decision matrix
        Returns: (priority, recommendation, reason, estimated_cost, expected_impact)
        """
        
        standard_lanes = {'motorway': 6, 'trunk': 4, 'primary': 4, 'secondary': 2, 'tertiary': 2}
        expected_lanes = standard_lanes.get(road_type, 2)
        
        # Cost estimates per km (in millions $)
        cost_per_km = {
            'road_widening': 2.5,
            'flyover': 15.0,
            'bridge': 25.0,
            'resurfacing': 0.8,
            'traffic_management': 0.3,
            'maintenance': 0.2
        }
        
        # ========================================
        # DECISION MATRIX
        # ========================================
        
        # 1. ROAD WIDENING
        # When: Congestion > 0.7 AND lanes < standard
        if congestion_score > 0.7 and lanes < expected_lanes:
            priority = "HIGH"
            lanes_to_add = expected_lanes - lanes
            recommendation = f"Widen road from {lanes} to {lanes + lanes_to_add} lanes"
            reason = f"Peak hour congestion at {int(congestion_score * 100)}% capacity. Current {lanes} lanes insufficient for traffic volume."
            cost = cost_per_km['road_widening'] * length_km
            impact = f"Reduce congestion by {int(congestion_score * 40)}%, handle {2030} projected traffic"
            return priority, recommendation, reason, cost, impact
        
        # 2. FLYOVER/JUNCTION REDESIGN
        # When: Safety > 0.6 AND dangerous junctions > 4
        if safety_score > 0.6 and dangerous_junctions > 2:
            priority = "HIGH"
            recommendation = f"Build flyover or redesign {dangerous_junctions} junctions"
            reason = f"Safety risk score at {int(safety_score * 100)}%. {dangerous_junctions} conflict points identified."
            cost = cost_per_km['flyover'] * min(length_km, 2)
            impact = f"Reduce accidents by {int(safety_score * 50)}%, eliminate {dangerous_junctions} conflict points"
            return priority, recommendation, reason, cost, impact
        
        # 3. FUTURE CAPACITY PLANNING
        # When: Growth > 0.8 AND Congestion < 0.5
        if growth_pressure_score > 0.6 and congestion_score < 0.5:
            priority = "MEDIUM"
            recommendation = "Plan capacity expansion for future growth"
            reason = f"High growth pressure ({int(growth_pressure_score * 100)}%) with current adequate capacity. Proactive planning needed."
            cost = cost_per_km['road_widening'] * length_km * 0.5  # Planning cost
            impact = f"Prevent future congestion, support {int(growth_pressure_score * 30)}% more development"
            return priority, recommendation, reason, cost, impact
        
        # 4. ROAD RESURFACING
        # When: Road Quality < 0.4
        if road_quality_score > 0.6:
            priority = "MEDIUM"
            recommendation = "Road resurfacing and drainage improvement"
            reason = f"Pavement condition below standard. Quality score: {int((1-road_quality_score) * 100)}%"
            cost = cost_per_km['resurfacing'] * length_km
            impact = f"Extend road life by 10 years, improve safety by 15%"
            return priority, recommendation, reason, cost, impact
        
        # 5. TRAFFIC MANAGEMENT
        # When: Congestion > 0.5 but < 0.7
        if congestion_score > 0.5:
            priority = "MEDIUM"
            recommendation = "Install smart traffic signals and management system"
            reason = f"Moderate congestion ({int(congestion_score * 100)}%). Can be managed with ITS solutions."
            cost = cost_per_km['traffic_management'] * length_km
            impact = f"Reduce travel time by 20%, improve flow efficiency"
            return priority, recommendation, reason, cost, impact
        
        # 6. ROUTINE MAINTENANCE
        if isi_score > 0.3:
            priority = "LOW"
            recommendation = "Schedule routine maintenance"
            reason = f"ISI score {isi_score:.2f} indicates minor attention needed."
            cost = cost_per_km['maintenance'] * length_km
            impact = "Maintain current performance levels"
            return priority, recommendation, reason, cost, impact
        
        # 7. NO ACTION NEEDED
        priority = "LOW"
        recommendation = "No immediate action required"
        reason = f"Road performing well. ISI score: {isi_score:.2f}"
        cost = 0
        impact = "Continue monitoring"
        
        return priority, recommendation, reason, cost, impact
    
    def _generate_all_recommendations(self, scored_roads: List[RoadMetrics]) -> List[Dict]:
        """Generate prioritized list of recommendations"""
        recommendations = []
        
        for road in scored_roads:
            if road.priority in ["HIGH", "MEDIUM"]:
                recommendations.append({
                    'segment_id': road.segment_id,
                    'road_name': road.name,
                    'road_type': road.road_type,
                    'length_km': road.length_km,
                    'priority': road.priority,
                    'action': road.recommendation,
                    'reason': road.recommendation_reason,
                    'isi_score': road.isi_score,
                    'congestion_score': road.congestion_score,
                    'safety_score': road.safety_score,
                    'estimated_cost_millions': road.estimated_cost,
                    'expected_impact': road.expected_impact,
                    'coordinates': road.coordinates
                })
        
        # Sort by priority and ISI score
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        recommendations.sort(key=lambda x: (priority_order[x['priority']], -x['isi_score']))
        
        return recommendations
    
    def _generate_summary(self, scored_roads: List[RoadMetrics], 
                         recommendations: List[Dict]) -> Dict:
        """Generate executive summary of analysis"""
        if not scored_roads:
            return {
                'total_segments_analyzed': 0,
                'critical_segments': 0,
                'high_priority_segments': 0,
                'average_isi': 0,
                'total_road_length_km': 0,
                'total_estimated_cost_millions': 0,
                'top_issues': []
            }
        
        high_priority = [r for r in recommendations if r['priority'] == 'HIGH']
        medium_priority = [r for r in recommendations if r['priority'] == 'MEDIUM']
        
        total_cost = sum(r['estimated_cost_millions'] for r in recommendations)
        avg_isi = sum(r.isi_score for r in scored_roads) / len(scored_roads)
        total_length = sum(r.length_km for r in scored_roads)
        
        # Identify top issues
        congestion_issues = len([r for r in scored_roads if r.congestion_score > 0.7])
        safety_issues = len([r for r in scored_roads if r.safety_score > 0.6])
        quality_issues = len([r for r in scored_roads if r.road_quality_score > 0.6])
        
        top_issues = []
        if congestion_issues > 0:
            top_issues.append(f"{congestion_issues} segments with severe congestion")
        if safety_issues > 0:
            top_issues.append(f"{safety_issues} segments with safety concerns")
        if quality_issues > 0:
            top_issues.append(f"{quality_issues} segments needing maintenance")
        
        return {
            'total_segments_analyzed': len(scored_roads),
            'critical_segments': len(high_priority),
            'high_priority_segments': len(medium_priority),
            'average_isi': round(avg_isi, 3),
            'max_isi': round(max(r.isi_score for r in scored_roads), 3),
            'total_road_length_km': round(total_length, 2),
            'total_estimated_cost_millions': round(total_cost, 2),
            'estimated_roi': f"{round(total_cost * 3.5, 1)}x",  # Estimated 3.5x ROI
            'top_issues': top_issues,
            'breakdown': {
                'congestion_critical': congestion_issues,
                'safety_critical': safety_issues,
                'quality_critical': quality_issues
            }
        }
    
    def _metrics_to_geojson(self, scored_roads: List[RoadMetrics]) -> Dict:
        """Convert scored roads to GeoJSON format"""
        features = []
        
        for road in scored_roads:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': road.coordinates
                },
                'properties': {
                    'segment_id': road.segment_id,
                    'name': road.name,
                    'road_type': road.road_type,
                    'length_km': road.length_km,
                    'lanes': road.lanes,
                    'isi_score': round(road.isi_score, 3),
                    'congestion_score': round(road.congestion_score, 3),
                    'safety_score': round(road.safety_score, 3),
                    'growth_pressure_score': round(road.growth_pressure_score, 3),
                    'road_quality_score': round(road.road_quality_score, 3),
                    'traffic_volume': road.current_traffic_volume,
                    'road_capacity': road.road_capacity,
                    'priority': road.priority,
                    'recommendation': road.recommendation,
                    'recommendation_reason': road.recommendation_reason,
                    'estimated_cost_millions': round(road.estimated_cost, 2),
                    'expected_impact': road.expected_impact
                }
            }
            features.append(feature)
        
        return {
            'type': 'FeatureCollection',
            'features': features
        }
    
    def _haversine_distance(self, lat1: float, lon1: float, 
                            lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km"""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c


# Backwards compatibility
def fetch_osm_roads(polygon_coords):
    """Legacy function for backwards compatibility"""
    engine = InfraSenseEngine()
    min_lng, max_lng, min_lat, max_lat = engine._get_bounding_box(polygon_coords)
    return osm_fetcher.get_roads_in_bbox(min_lat, min_lng, max_lat, max_lng)


def enrich_road_data(roads_gdf):
    """Legacy function for backwards compatibility"""
    return roads_gdf


def calculate_all_scores(enriched_roads):
    """Legacy function for backwards compatibility"""
    return enriched_roads


def generate_recommendations(scored_roads):
    """Legacy function for backwards compatibility"""
    return []

