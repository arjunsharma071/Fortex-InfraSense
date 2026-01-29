# engine/google_maps_client.py
"""
Google Maps API Client for InfraSense AI
Fetches real road data, traffic, and places information
"""

import requests
import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import time

# Google Maps API Key
GOOGLE_MAPS_API_KEY = "AIzaSyDxGgKlamItZK2-OYqzoYGJwXBTT7GTnpU"

@dataclass
class RoadSegment:
    """Represents a road segment with all its attributes"""
    segment_id: str
    name: str
    road_type: str
    coordinates: List[List[float]]
    length_km: float
    lanes: int
    speed_limit: int
    surface: str
    width_meters: float
    one_way: bool
    
@dataclass
class TrafficData:
    """Traffic information for a location"""
    current_speed: float  # km/h
    free_flow_speed: float  # km/h
    congestion_level: float  # 0-1
    travel_time_minutes: float
    delay_minutes: float

@dataclass
class PlaceResult:
    """Result from Places API"""
    place_id: str
    name: str
    location: Tuple[float, float]
    types: List[str]
    rating: Optional[float]


class GoogleMapsClient:
    """
    Client for Google Maps APIs
    - Roads API for road data
    - Directions API for traffic
    - Places API for points of interest
    - Geocoding API for location data
    """
    
    def __init__(self, api_key: str = GOOGLE_MAPS_API_KEY):
        self.api_key = api_key
        self.base_urls = {
            'directions': 'https://maps.googleapis.com/maps/api/directions/json',
            'places': 'https://maps.googleapis.com/maps/api/place/nearbysearch/json',
            'geocode': 'https://maps.googleapis.com/maps/api/geocode/json',
            'roads': 'https://roads.googleapis.com/v1/snapToRoads',
            'distance_matrix': 'https://maps.googleapis.com/maps/api/distancematrix/json',
            'elevation': 'https://maps.googleapis.com/maps/api/elevation/json'
        }
        self.request_count = 0
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Implement rate limiting to avoid API quota issues"""
        current_time = time.time()
        if current_time - self.last_request_time < 0.1:  # 10 requests per second max
            time.sleep(0.1)
        self.last_request_time = time.time()
        self.request_count += 1
        
    def _make_request(self, url: str, params: Dict) -> Dict:
        """Make API request with error handling"""
        self._rate_limit()
        params['key'] = self.api_key
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Request Error: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def get_roads_in_polygon(self, polygon_coords: List[List[float]]) -> List[Dict]:
        """
        Get road network within a polygon using Directions API
        to trace routes between grid points
        """
        # Calculate bounding box
        lngs = [c[0] for c in polygon_coords]
        lats = [c[1] for c in polygon_coords]
        min_lng, max_lng = min(lngs), max(lngs)
        min_lat, max_lat = min(lats), max(lats)
        
        # Create grid of sample points
        grid_size = 5  # 5x5 grid
        lat_step = (max_lat - min_lat) / grid_size
        lng_step = (max_lng - min_lng) / grid_size
        
        roads = []
        road_id = 0
        
        # Sample routes between grid points to discover roads
        for i in range(grid_size):
            for j in range(grid_size - 1):
                origin_lat = min_lat + (i + 0.5) * lat_step
                origin_lng = min_lng + (j + 0.5) * lng_step
                dest_lat = min_lat + (i + 0.5) * lat_step
                dest_lng = min_lng + (j + 1.5) * lng_step
                
                route_data = self.get_route(
                    f"{origin_lat},{origin_lng}",
                    f"{dest_lat},{dest_lng}"
                )
                
                if route_data and 'routes' in route_data and route_data['routes']:
                    route = route_data['routes'][0]
                    for leg in route.get('legs', []):
                        for step in leg.get('steps', []):
                            road_id += 1
                            roads.append({
                                'segment_id': f'road_{road_id:04d}',
                                'name': step.get('html_instructions', 'Unknown Road').replace('<b>', '').replace('</b>', '').replace('<div style="font-size:0.9em">', ' ').replace('</div>', ''),
                                'distance_meters': step.get('distance', {}).get('value', 0),
                                'duration_seconds': step.get('duration', {}).get('value', 0),
                                'start_location': step.get('start_location', {}),
                                'end_location': step.get('end_location', {}),
                                'polyline': step.get('polyline', {}).get('points', ''),
                                'maneuver': step.get('maneuver', 'straight'),
                                'travel_mode': step.get('travel_mode', 'DRIVING')
                            })
        
        return roads
    
    def get_route(self, origin: str, destination: str, 
                  departure_time: str = "now", 
                  traffic_model: str = "best_guess") -> Dict:
        """
        Get route between two points with traffic data
        """
        params = {
            'origin': origin,
            'destination': destination,
            'departure_time': departure_time,
            'traffic_model': traffic_model,
            'alternatives': 'false'
        }
        
        return self._make_request(self.base_urls['directions'], params)
    
    def get_traffic_data(self, origin: str, destination: str) -> TrafficData:
        """
        Get real-time traffic data between two points
        Returns congestion level, travel times, delays
        """
        # Get route with traffic
        route_data = self.get_route(origin, destination)
        
        if not route_data or 'routes' not in route_data or not route_data['routes']:
            return TrafficData(
                current_speed=40,
                free_flow_speed=60,
                congestion_level=0.5,
                travel_time_minutes=10,
                delay_minutes=2
            )
        
        route = route_data['routes'][0]
        leg = route['legs'][0]
        
        # Get distance and duration
        distance_meters = leg.get('distance', {}).get('value', 1000)
        duration_seconds = leg.get('duration', {}).get('value', 60)
        duration_in_traffic = leg.get('duration_in_traffic', {}).get('value', duration_seconds)
        
        # Calculate speeds
        distance_km = distance_meters / 1000
        travel_time_hours = duration_in_traffic / 3600
        free_flow_hours = duration_seconds / 3600
        
        current_speed = distance_km / travel_time_hours if travel_time_hours > 0 else 40
        free_flow_speed = distance_km / free_flow_hours if free_flow_hours > 0 else 60
        
        # Calculate congestion level (0 = free flow, 1 = heavily congested)
        if free_flow_speed > 0:
            congestion_level = max(0, min(1, 1 - (current_speed / free_flow_speed)))
        else:
            congestion_level = 0.5
        
        delay_minutes = (duration_in_traffic - duration_seconds) / 60
        
        return TrafficData(
            current_speed=current_speed,
            free_flow_speed=free_flow_speed,
            congestion_level=congestion_level,
            travel_time_minutes=duration_in_traffic / 60,
            delay_minutes=max(0, delay_minutes)
        )
    
    def get_nearby_places(self, location: Tuple[float, float], 
                          radius: int = 1000,
                          place_type: str = None,
                          keyword: str = None) -> List[PlaceResult]:
        """
        Search for places near a location
        """
        params = {
            'location': f"{location[0]},{location[1]}",
            'radius': radius
        }
        
        if place_type:
            params['type'] = place_type
        if keyword:
            params['keyword'] = keyword
            
        result = self._make_request(self.base_urls['places'], params)
        
        places = []
        for place in result.get('results', []):
            loc = place.get('geometry', {}).get('location', {})
            places.append(PlaceResult(
                place_id=place.get('place_id', ''),
                name=place.get('name', ''),
                location=(loc.get('lat', 0), loc.get('lng', 0)),
                types=place.get('types', []),
                rating=place.get('rating')
            ))
        
        return places
    
    def search_accident_hotspots(self, polygon_coords: List[List[float]]) -> List[Dict]:
        """
        Search for accident-related locations within polygon
        Uses Places API with accident-related keywords
        """
        # Calculate center of polygon
        center_lat = sum(c[1] for c in polygon_coords) / len(polygon_coords)
        center_lng = sum(c[0] for c in polygon_coords) / len(polygon_coords)
        
        # Calculate approximate radius
        max_dist = 0
        for coord in polygon_coords:
            dist = self._haversine_distance(center_lat, center_lng, coord[1], coord[0])
            max_dist = max(max_dist, dist)
        
        radius = int(max_dist * 1000)  # Convert to meters
        
        accident_keywords = ['accident', 'hospital', 'police station', 'traffic signal']
        hotspots = []
        
        for keyword in accident_keywords:
            places = self.get_nearby_places(
                (center_lat, center_lng),
                radius=min(radius, 50000),  # Max 50km
                keyword=keyword
            )
            
            for place in places:
                if self._point_in_polygon(place.location[1], place.location[0], polygon_coords):
                    hotspots.append({
                        'location': place.location,
                        'name': place.name,
                        'type': keyword,
                        'risk_factor': 0.3 if 'hospital' in keyword else 0.5
                    })
        
        return hotspots
    
    def get_elevation_data(self, locations: List[Tuple[float, float]]) -> List[float]:
        """Get elevation data for multiple locations"""
        if not locations:
            return []
            
        # Format locations for API
        locations_str = '|'.join([f"{lat},{lng}" for lat, lng in locations])
        
        params = {
            'locations': locations_str
        }
        
        result = self._make_request(self.base_urls['elevation'], params)
        
        elevations = []
        for r in result.get('results', []):
            elevations.append(r.get('elevation', 0))
        
        return elevations
    
    def get_distance_matrix(self, origins: List[str], destinations: List[str]) -> Dict:
        """
        Get travel times and distances between multiple origins and destinations
        """
        params = {
            'origins': '|'.join(origins),
            'destinations': '|'.join(destinations),
            'departure_time': 'now',
            'traffic_model': 'best_guess'
        }
        
        return self._make_request(self.base_urls['distance_matrix'], params)
    
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to coordinates"""
        params = {'address': address}
        result = self._make_request(self.base_urls['geocode'], params)
        
        if result.get('results'):
            location = result['results'][0]['geometry']['location']
            return (location['lat'], location['lng'])
        return None
    
    def reverse_geocode(self, lat: float, lng: float) -> str:
        """Convert coordinates to address"""
        params = {'latlng': f"{lat},{lng}"}
        result = self._make_request(self.base_urls['geocode'], params)
        
        if result.get('results'):
            return result['results'][0].get('formatted_address', 'Unknown Location')
        return 'Unknown Location'
    
    def _haversine_distance(self, lat1: float, lon1: float, 
                            lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km"""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _point_in_polygon(self, x: float, y: float, 
                          polygon: List[List[float]]) -> bool:
        """Check if point is inside polygon using ray casting"""
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


class OSMDataFetcher:
    """
    Fetch road data from OpenStreetMap Overpass API
    More detailed road geometry than Google Maps
    """
    
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
    
    def get_roads_in_bbox(self, min_lat: float, min_lng: float, 
                          max_lat: float, max_lng: float) -> List[Dict]:
        """
        Fetch all roads within a bounding box from OSM
        """
        # Overpass QL query for roads
        query = f"""
        [out:json][timeout:60];
        (
          way["highway"]["highway"!~"footway|path|cycleway|pedestrian|steps"]
            ({min_lat},{min_lng},{max_lat},{max_lng});
        );
        out body;
        >;
        out skel qt;
        """
        
        try:
            response = requests.post(self.overpass_url, data={'data': query}, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            return self._parse_osm_data(data)
        except Exception as e:
            print(f"OSM API Error: {e}")
            return []
    
    def _parse_osm_data(self, data: Dict) -> List[Dict]:
        """Parse OSM response into road segments"""
        nodes = {}
        roads = []
        
        # First pass: collect all nodes
        for element in data.get('elements', []):
            if element['type'] == 'node':
                nodes[element['id']] = {
                    'lat': element['lat'],
                    'lon': element['lon']
                }
        
        # Second pass: build roads from ways
        for element in data.get('elements', []):
            if element['type'] == 'way':
                tags = element.get('tags', {})
                node_ids = element.get('nodes', [])
                
                # Get coordinates for all nodes in way
                coords = []
                for node_id in node_ids:
                    if node_id in nodes:
                        coords.append([nodes[node_id]['lon'], nodes[node_id]['lat']])
                
                if len(coords) >= 2:
                    road = {
                        'segment_id': f"osm_{element['id']}",
                        'name': tags.get('name', tags.get('highway', 'Unnamed Road')),
                        'road_type': tags.get('highway', 'unclassified'),
                        'coordinates': coords,
                        'lanes': self._parse_lanes(tags.get('lanes', '2')),
                        'speed_limit': self._parse_speed(tags.get('maxspeed', '50')),
                        'surface': tags.get('surface', 'asphalt'),
                        'width': self._parse_width(tags.get('width', '7')),
                        'one_way': tags.get('oneway', 'no') == 'yes',
                        'length_km': self._calculate_length(coords)
                    }
                    roads.append(road)
        
        return roads
    
    def _parse_lanes(self, lanes_str: str) -> int:
        """Parse lanes from OSM tags"""
        try:
            return int(lanes_str.split(';')[0])
        except:
            return 2
    
    def _parse_speed(self, speed_str: str) -> int:
        """Parse speed limit from OSM tags"""
        try:
            # Remove 'mph' or 'km/h' suffix
            speed = ''.join(filter(str.isdigit, speed_str.split()[0]))
            return int(speed) if speed else 50
        except:
            return 50
    
    def _parse_width(self, width_str: str) -> float:
        """Parse road width from OSM tags"""
        try:
            return float(''.join(filter(lambda x: x.isdigit() or x == '.', width_str)))
        except:
            return 7.0
    
    def _calculate_length(self, coords: List[List[float]]) -> float:
        """Calculate total length of road segment in km"""
        total = 0
        for i in range(len(coords) - 1):
            lat1, lon1 = coords[i][1], coords[i][0]
            lat2, lon2 = coords[i+1][1], coords[i+1][0]
            
            # Haversine formula
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = (math.sin(dlat/2)**2 + 
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                 math.sin(dlon/2)**2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            total += R * c
        
        return total


class PopulationDataFetcher:
    """
    Fetch population density data from WorldPop or other sources
    """
    
    def __init__(self):
        self.worldpop_url = "https://api.worldpop.org/v1/services/stats"
    
    def get_population_density(self, lat: float, lng: float, radius_km: float = 1) -> float:
        """
        Get approximate population density for a location
        Returns people per square km
        """
        # For demo purposes, use estimation based on location
        # In production, integrate with WorldPop API or government census data
        
        # Estimate based on typical urban/rural patterns
        # This would be replaced with actual API calls
        base_density = 5000  # Average urban density
        
        # Adjust based on coordinates (rough estimation)
        # Higher density in major metropolitan areas
        
        return base_density
    
    def get_growth_rate(self, region_code: str) -> float:
        """
        Get population growth rate for a region
        Returns annual growth rate (e.g., 0.02 for 2%)
        """
        # Default growth rate - would be replaced with actual data
        return 0.015  # 1.5% annual growth


# Create singleton instances
google_maps_client = GoogleMapsClient()
osm_fetcher = OSMDataFetcher()
population_fetcher = PopulationDataFetcher()
