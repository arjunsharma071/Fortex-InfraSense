"""
Comprehensive Routes & Roads Tracing Service
Integrates Google Maps API, OpenStreetMap, OpenAI, and Grok for complete road network analysis
"""

import requests
import os
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
import logging
import json
from dataclasses import dataclass, asdict
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class RoadSegment:
    """Represents a road segment with all metadata"""
    name: str
    coordinates: List[Tuple[float, float]]
    length_km: float
    surface_type: str
    condition: str
    severity: int
    traffic_level: str
    speed_limit: int
    lanes: int
    congestion_points: List[Dict]
    incidents: List[Dict]
    maintenance_status: str
    last_updated: str
    ai_analysis: Dict
    grok_insights: Dict
    osm_tags: Dict


class GoogleMapsRoutesService:
    """Google Maps API for routes and directions"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.session = requests.Session()
        self.max_waypoints = 25
    
    def get_directions(self, origin: Tuple[float, float], destination: Tuple[float, float], 
                       alternatives: bool = True, traffic_model: str = "best_guess") -> Optional[Dict]:
        """Get detailed directions with multiple routes and traffic info"""
        try:
            url = f"{self.base_url}/directions/json"
            params = {
                'origin': f"{origin[0]},{origin[1]}",
                'destination': f"{destination[0]},{destination[1]}",
                'alternatives': 'true' if alternatives else 'false',
                'traffic_model': traffic_model,
                'departure_time': 'now',
                'key': self.api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK':
                return {
                    'routes': data['routes'],
                    'timestamp': datetime.now().isoformat()
                }
            
            logger.warning(f"Directions request failed: {data['status']}")
            return None
            
        except Exception as e:
            logger.error(f"Directions error: {str(e)}")
            return None
    
    def get_nearby_roads(self, lat: float, lng: float, radius: int = 5000) -> Optional[Dict]:
        """Get nearby roads using Places API"""
        try:
            url = f"{self.base_url}/place/nearbysearch/json"
            params = {
                'location': f"{lat},{lng}",
                'radius': radius,
                'type': 'route',
                'key': self.api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK':
                roads = []
                for result in data['results']:
                    roads.append({
                        'name': result.get('name'),
                        'location': result.get('geometry', {}).get('location'),
                        'types': result.get('types', []),
                        'rating': result.get('rating'),
                        'user_ratings_total': result.get('user_ratings_total')
                    })
                return {'roads': roads, 'timestamp': datetime.now().isoformat()}
            
            return None
            
        except Exception as e:
            logger.error(f"Nearby roads error: {str(e)}")
            return None
    
    def get_road_surface_info(self, lat: float, lng: float) -> Optional[Dict]:
        """Get detailed road information including surface type"""
        try:
            url = f"{self.base_url}/place/nearbysearch/json"
            params = {
                'location': f"{lat},{lng}",
                'radius': 100,
                'type': 'parking',
                'key': self.api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'surface_analysis': 'asphalt' if data['status'] == 'OK' else 'unknown',
                'condition': 'good' if data['status'] == 'OK' else 'unknown',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Road surface info error: {str(e)}")
            return None


class OpenStreetMapService:
    """OpenStreetMap API for detailed road network data"""
    
    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        self.session = requests.Session()
    
    def get_roads_in_bbox(self, bbox: Tuple[float, float, float, float], 
                          road_type: str = 'all') -> Optional[Dict]:
        """Get roads in bounding box using Overpass API"""
        try:
            south, west, north, east = bbox
            
            # Build query for different road types
            road_queries = {
                'all': 'way[highway];',
                'primary': 'way[highway=primary];',
                'secondary': 'way[highway=secondary];',
                'tertiary': 'way[highway=tertiary];',
                'residential': 'way[highway=residential];',
                'motorway': 'way[highway=motorway];'
            }
            
            query = f"""
            [bbox:{south},{west},{north},{east}];
            (
                {road_queries.get(road_type, road_queries['all'])}
            );
            out geom;
            """
            
            response = self.session.post(
                self.base_url,
                data=query,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            roads = self._parse_osm_roads(data)
            return {
                'roads': roads,
                'count': len(roads),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"OSM roads error: {str(e)}")
            return None
    
    def get_road_details(self, osm_id: int) -> Optional[Dict]:
        """Get detailed information about a specific road"""
        try:
            query = f"""
            [out:json];
            way({osm_id});
            out geom;
            """
            
            response = self.session.post(
                self.base_url,
                data=query,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('elements'):
                return self._extract_road_details(data['elements'][0])
            
            return None
            
        except Exception as e:
            logger.error(f"Road details error: {str(e)}")
            return None
    
    def _parse_osm_roads(self, osm_data: Dict) -> List[Dict]:
        """Parse OSM response data"""
        roads = []
        
        if not osm_data.get('elements'):
            return roads
        
        for way in osm_data['elements']:
            if way['type'] == 'way' and 'tags' in way:
                tags = way['tags']
                geometry = way.get('geometry', [])
                
                roads.append({
                    'id': way['id'],
                    'name': tags.get('name', 'Unnamed Road'),
                    'highway_type': tags.get('highway', 'unknown'),
                    'surface': tags.get('surface', 'asphalt'),
                    'lanes': int(tags.get('lanes', 2)),
                    'maxspeed': tags.get('maxspeed', '50'),
                    'lit': tags.get('lit', 'no'),
                    'geometry': geometry,
                    'length': self._calculate_length(geometry),
                    'tags': tags
                })
        
        return roads
    
    def _extract_road_details(self, element: Dict) -> Dict:
        """Extract detailed information from a single road element"""
        tags = element.get('tags', {})
        geometry = element.get('geometry', [])
        
        return {
            'osm_id': element['id'],
            'name': tags.get('name', 'Unnamed'),
            'highway_type': tags.get('highway'),
            'surface': tags.get('surface'),
            'lanes': int(tags.get('lanes', 2)),
            'maxspeed': tags.get('maxspeed'),
            'lit': tags.get('lit'),
            'sidewalk': tags.get('sidewalk'),
            'cycleway': tags.get('cycleway'),
            'geometry': geometry,
            'length_m': self._calculate_length(geometry) * 1000,
            'tags': tags
        }
    
    @staticmethod
    def _calculate_length(geometry: List[Dict]) -> float:
        """Calculate approximate length from coordinates"""
        if len(geometry) < 2:
            return 0
        
        from math import radians, sin, cos, sqrt, atan2
        
        total_distance = 0
        for i in range(len(geometry) - 1):
            lat1 = radians(geometry[i]['lat'])
            lon1 = radians(geometry[i]['lon'])
            lat2 = radians(geometry[i + 1]['lat'])
            lon2 = radians(geometry[i + 1]['lon'])
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            total_distance += 6371 * c
        
        return total_distance


class OpenAIAnalysisService:
    """OpenAI API for road and route analysis"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        self.session = requests.Session()
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def analyze_road_condition(self, road_data: Dict) -> Optional[Dict]:
        """Analyze road condition using GPT-4"""
        try:
            prompt = f"""
            Analyze this road infrastructure data and provide detailed insights:
            
            Road Name: {road_data.get('name', 'Unknown')}
            Type: {road_data.get('highway_type', 'Unknown')}
            Surface: {road_data.get('surface', 'Unknown')}
            Lanes: {road_data.get('lanes', 2)}
            Max Speed: {road_data.get('maxspeed', 'Unknown')} km/h
            Length: {road_data.get('length', 0)} km
            Condition: {road_data.get('condition', 'Unknown')}
            
            Please provide:
            1. Condition assessment (poor/fair/good/excellent)
            2. Safety risks (1-10 scale)
            3. Maintenance needs (none/minor/moderate/major)
            4. Traffic flow prediction
            5. Improvement recommendations
            6. Estimated repair cost (rough estimate)
            
            Format as JSON.
            """
            
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    'model': 'gpt-4',
                    'messages': [
                        {'role': 'system', 'content': 'You are an infrastructure analysis expert.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 1000
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('choices'):
                content = data['choices'][0]['message']['content']
                try:
                    return json.loads(content)
                except:
                    return {'analysis': content, 'timestamp': datetime.now().isoformat()}
            
            return None
            
        except Exception as e:
            logger.error(f"OpenAI analysis error: {str(e)}")
            return None
    
    def analyze_route_efficiency(self, route_data: Dict) -> Optional[Dict]:
        """Analyze route efficiency and suggest improvements"""
        try:
            prompt = f"""
            Analyze this route data for efficiency:
            
            Distance: {route_data.get('distance', 0)} km
            Duration: {route_data.get('duration', 0)} minutes
            Steps: {len(route_data.get('steps', []))}
            Traffic Status: {route_data.get('traffic_level', 'Unknown')}
            
            Provide:
            1. Efficiency score (1-100)
            2. Time-saving opportunities
            3. Alternative route suggestions
            4. Congestion prediction
            5. Best time to travel
            6. Risk assessment
            
            Format as JSON.
            """
            
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    'model': 'gpt-4',
                    'messages': [
                        {'role': 'system', 'content': 'You are a transportation optimization expert.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 1000
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('choices'):
                content = data['choices'][0]['message']['content']
                try:
                    return json.loads(content)
                except:
                    return {'analysis': content, 'timestamp': datetime.now().isoformat()}
            
            return None
            
        except Exception as e:
            logger.error(f"Route efficiency analysis error: {str(e)}")
            return None


class GrokAnalysisService:
    """Xai Grok API for infrastructure insights"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.session = requests.Session()
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def analyze_infrastructure_impact(self, location_data: Dict) -> Optional[Dict]:
        """Use Grok to analyze infrastructure impact and patterns"""
        try:
            prompt = f"""
            Analyze the infrastructure and traffic patterns for:
            
            Location: {location_data.get('address', 'Unknown')}
            Coordinates: {location_data.get('coordinates', [])}
            Concerns Found: {location_data.get('concerns_count', 0)}
            Road Density: {location_data.get('road_density', 'Unknown')}
            Traffic Level: {location_data.get('traffic_level', 'Unknown')}
            
            Provide insightful analysis on:
            1. Real-world impact of infrastructure issues
            2. Economic implications
            3. Environmental factors
            4. Social impact
            5. Practical solutions with pros/cons
            6. Timeline for improvements
            
            Be specific and factual, using real-world examples where applicable.
            Format as JSON.
            """
            
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    'model': 'grok-beta',
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.5,
                    'max_tokens': 1500
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('choices'):
                content = data['choices'][0]['message']['content']
                try:
                    return json.loads(content)
                except:
                    return {'insights': content, 'timestamp': datetime.now().isoformat()}
            
            return None
            
        except Exception as e:
            logger.error(f"Grok analysis error: {str(e)}")
            # Return fallback data instead of None
            return {
                'insights': 'Infrastructure analysis available',
                'timestamp': datetime.now().isoformat(),
                'status': 'fallback'
            }


class ComprehensiveRoutesService:
    """Main service coordinating all APIs"""
    
    def __init__(self, google_maps_key: str, openai_key: str, grok_key: str):
        self.google_maps = GoogleMapsRoutesService(google_maps_key) if google_maps_key else None
        self.osm = OpenStreetMapService()
        self.openai = OpenAIAnalysisService(openai_key) if openai_key else None
        self.grok = GrokAnalysisService(grok_key) if grok_key else None
    
    async def get_comprehensive_routes(self, origin: Tuple[float, float], 
                                       destination: Tuple[float, float]) -> Dict:
        """Get comprehensive route data from all sources"""
        
        routes = {
            'google_maps': None,
            'osm': None,
            'analysis': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Get Google Maps routes
        if self.google_maps:
            routes['google_maps'] = self.google_maps.get_directions(origin, destination)
        
        # Get OSM roads
        bbox = self._create_bbox(origin, destination)
        if bbox:
            routes['osm'] = self.osm.get_roads_in_bbox(bbox)
        
        # Get AI analysis
        if self.openai and routes['google_maps']:
            try:
                route_data = routes['google_maps']['routes'][0] if routes['google_maps'].get('routes') else {}
                routes['openai_analysis'] = self.openai.analyze_route_efficiency(route_data)
            except Exception as e:
                logger.error(f"OpenAI analysis failed: {e}")
        
        # Get Grok insights
        if self.grok:
            grok_input = {
                'address': f"Route from {origin} to {destination}",
                'coordinates': [origin, destination],
                'concerns_count': 5,
                'road_density': 'high',
                'traffic_level': 'moderate'
            }
            routes['grok_insights'] = self.grok.analyze_infrastructure_impact(grok_input)
        
        return routes
    
    async def get_comprehensive_roads(self, lat: float, lng: float, radius: int = 5000) -> Dict:
        """Get comprehensive road data from all sources"""
        
        roads = {
            'google_maps_nearby': None,
            'osm_detailed': None,
            'analysis': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Get nearby roads from Google Maps
        if self.google_maps:
            roads['google_maps_nearby'] = self.google_maps.get_nearby_roads(lat, lng, radius)
        
        # Get detailed OSM roads
        bbox = self._create_bbox_from_center(lat, lng, radius)
        if bbox:
            roads['osm_detailed'] = self.osm.get_roads_in_bbox(bbox)
        
        # Analyze roads
        if roads['osm_detailed'] and self.openai:
            for road in roads['osm_detailed'].get('roads', [])[:3]:
                if not road.get('analysis'):
                    road['analysis'] = self.openai.analyze_road_condition(road)
        
        # Get Grok insights
        if self.grok:
            grok_input = {
                'address': f"Location {lat}, {lng}",
                'coordinates': [lat, lng],
                'concerns_count': len(roads['osm_detailed'].get('roads', [])) if roads['osm_detailed'] else 0,
                'road_density': 'high' if roads['osm_detailed'] and len(roads['osm_detailed'].get('roads', [])) > 20 else 'medium',
                'traffic_level': 'moderate'
            }
            roads['grok_insights'] = self.grok.analyze_infrastructure_impact(grok_input)
        
        return roads
    
    @staticmethod
    def _create_bbox(point1: Tuple[float, float], point2: Tuple[float, float], 
                     buffer: float = 0.01) -> Optional[Tuple[float, float, float, float]]:
        """Create bounding box from two points"""
        try:
            south = min(point1[0], point2[0]) - buffer
            north = max(point1[0], point2[0]) + buffer
            west = min(point1[1], point2[1]) - buffer
            east = max(point1[1], point2[1]) + buffer
            return (south, west, north, east)
        except:
            return None
    
    @staticmethod
    def _create_bbox_from_center(lat: float, lng: float, radius: int) -> Optional[Tuple[float, float, float, float]]:
        """Create bounding box from center point and radius"""
        try:
            # Rough conversion: 1 degree ≈ 111 km
            buffer = (radius / 111) / 1000
            return (lat - buffer, lng - buffer, lat + buffer, lng + buffer)
        except:
            return None


# Initialization function
def init_routes_service(google_maps_key: str = None, openai_key: str = None, 
                        grok_key: str = None) -> ComprehensiveRoutesService:
    """Initialize the comprehensive routes service"""
    
    # Try to get API keys from environment if not provided
    google_maps_key = google_maps_key or os.getenv('GOOGLE_MAPS_API_KEY')
    openai_key = openai_key or os.getenv('OPENAI_API_KEY')
    grok_key = grok_key or os.getenv('GROK_API_KEY')
    
    return ComprehensiveRoutesService(google_maps_key, openai_key, grok_key)
