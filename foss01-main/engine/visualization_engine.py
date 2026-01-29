# engine/visualization_engine.py
"""
InfraSense AI - Visualization Engine
Creates flyover visualizations, traffic flow animations, and before/after comparisons
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class AnimationType(Enum):
    """Types of animations available"""
    FLYOVER_3D = "flyover_3d"
    TRAFFIC_FLOW = "traffic_flow"
    BEFORE_AFTER = "before_after"
    CONSTRUCTION_PROGRESS = "construction_progress"
    HEATMAP_EVOLUTION = "heatmap_evolution"


@dataclass
class VisualizationStyle:
    """Visual style configuration"""
    primary_color: str
    secondary_color: str
    accent_color: str
    line_width: float
    opacity: float
    animation_speed: float


class FlyoverVisualization:
    """
    Generates 3D flyover visualization data for infrastructure projects
    Creates camera paths, cross-sections, and structural elements
    """
    
    # Design standards by country
    DESIGN_STANDARDS = {
        'IN': {
            'lane_width_m': 3.5,
            'median_width_m': 1.2,
            'shoulder_width_m': 1.5,
            'barrier_type': 'new_jersey',
            'lighting_spacing_m': 30,
            'min_vertical_clearance_m': 5.5,
            'max_gradient_percent': 4.0,
            'design_speed_kmh': 80,
            'pier_spacing_m': 30
        },
        'US': {
            'lane_width_m': 3.66,  # 12 feet
            'median_width_m': 1.8,
            'shoulder_width_m': 3.0,  # 10 feet
            'barrier_type': 'concrete_barrier',
            'lighting_spacing_m': 45,
            'min_vertical_clearance_m': 4.9,  # 16 feet
            'max_gradient_percent': 5.0,
            'design_speed_kmh': 110,
            'pier_spacing_m': 40
        },
        'DE': {
            'lane_width_m': 3.75,
            'median_width_m': 1.0,
            'shoulder_width_m': 2.5,
            'barrier_type': 'steel_barrier',
            'lighting_spacing_m': 35,
            'min_vertical_clearance_m': 4.5,
            'max_gradient_percent': 4.5,
            'design_speed_kmh': 130,
            'pier_spacing_m': 35
        },
        'JP': {
            'lane_width_m': 3.5,
            'median_width_m': 0.75,
            'shoulder_width_m': 2.0,
            'barrier_type': 'sound_barrier',
            'lighting_spacing_m': 25,
            'min_vertical_clearance_m': 4.7,
            'max_gradient_percent': 4.0,
            'design_speed_kmh': 100,
            'pier_spacing_m': 25
        },
        'AE': {
            'lane_width_m': 3.65,
            'median_width_m': 2.0,
            'shoulder_width_m': 3.0,
            'barrier_type': 'concrete_barrier',
            'lighting_spacing_m': 40,
            'min_vertical_clearance_m': 5.5,
            'max_gradient_percent': 5.0,
            'design_speed_kmh': 120,
            'pier_spacing_m': 35
        }
    }
    
    def __init__(self):
        self.default_style = VisualizationStyle(
            primary_color='#2563eb',    # Blue
            secondary_color='#64748b',  # Gray
            accent_color='#f59e0b',     # Orange
            line_width=2.0,
            opacity=0.85,
            animation_speed=1.0
        )
    
    def generate_flyover_visualization(self,
                                        route_points: List[Dict[str, float]],
                                        num_lanes: int,
                                        country_code: str,
                                        project_type: str = 'flyover') -> Dict[str, Any]:
        """
        Generate complete flyover visualization data
        """
        standards = self.DESIGN_STANDARDS.get(
            country_code, 
            self.DESIGN_STANDARDS['IN']
        )
        
        # Calculate route geometry
        total_length = self._calculate_route_length(route_points)
        
        # Generate structural elements
        deck_geometry = self._generate_deck_geometry(
            route_points, num_lanes, standards
        )
        
        pier_positions = self._generate_pier_positions(
            route_points, standards['pier_spacing_m']
        )
        
        # Generate camera path for flyover animation
        camera_path = self._generate_camera_path(route_points, total_length)
        
        # Generate cross-sections
        cross_sections = self._generate_cross_sections(
            num_lanes, standards, project_type
        )
        
        # Generate lighting positions
        lighting = self._generate_lighting(route_points, standards)
        
        # Generate barrier/railing geometry
        barriers = self._generate_barriers(route_points, num_lanes, standards)
        
        # Calculate sight distances
        sight_analysis = self._calculate_sight_distances(route_points, standards)
        
        return {
            'metadata': {
                'project_type': project_type,
                'total_length_m': round(total_length, 1),
                'num_lanes': num_lanes,
                'country_code': country_code,
                'design_standards': standards
            },
            'geometry': {
                'deck': deck_geometry,
                'piers': pier_positions,
                'barriers': barriers,
                'lighting': lighting
            },
            'camera_path': camera_path,
            'cross_sections': cross_sections,
            'sight_analysis': sight_analysis,
            'animation_config': self._get_animation_config(),
            'materials': self._get_material_specs(country_code),
            'elevation_profile': self._generate_elevation_profile(route_points),
            'render_settings': self._get_render_settings()
        }
    
    def _calculate_route_length(self, points: List[Dict[str, float]]) -> float:
        """Calculate total route length from points"""
        total = 0
        for i in range(len(points) - 1):
            dx = points[i+1].get('x', 0) - points[i].get('x', 0)
            dy = points[i+1].get('y', 0) - points[i].get('y', 0)
            # Convert lat/lng difference to meters (approximate)
            if 'lat' in points[i]:
                lat1, lng1 = points[i]['lat'], points[i]['lng']
                lat2, lng2 = points[i+1]['lat'], points[i+1]['lng']
                total += self._haversine_distance(lat1, lng1, lat2, lng2)
            else:
                total += math.sqrt(dx**2 + dy**2)
        return total
    
    def _haversine_distance(self, lat1: float, lng1: float, 
                            lat2: float, lng2: float) -> float:
        """Calculate distance between two lat/lng points in meters"""
        R = 6371000  # Earth's radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lng2 - lng1)
        
        a = math.sin(delta_phi/2)**2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _generate_deck_geometry(self, points: List[Dict[str, float]],
                                 num_lanes: int,
                                 standards: Dict) -> Dict[str, Any]:
        """Generate deck/roadway geometry"""
        lane_width = standards['lane_width_m']
        shoulder = standards['shoulder_width_m']
        median = standards['median_width_m']
        
        total_width = (num_lanes * lane_width) + (2 * shoulder) + median
        
        deck_vertices = []
        for i, point in enumerate(points):
            lat = point.get('lat', point.get('y', 0))
            lng = point.get('lng', point.get('x', 0))
            
            # Calculate perpendicular offset for edges
            if i < len(points) - 1:
                next_lat = points[i+1].get('lat', points[i+1].get('y', 0))
                next_lng = points[i+1].get('lng', points[i+1].get('x', 0))
                direction = math.atan2(next_lat - lat, next_lng - lng)
            else:
                prev_lat = points[i-1].get('lat', points[i-1].get('y', 0))
                prev_lng = points[i-1].get('lng', points[i-1].get('x', 0))
                direction = math.atan2(lat - prev_lat, lng - prev_lng)
            
            # Offset for left and right edges
            perp = direction + math.pi / 2
            offset = total_width / 2 / 111000  # Approximate meters to degrees
            
            deck_vertices.append({
                'center': {'lat': lat, 'lng': lng},
                'left_edge': {
                    'lat': lat + offset * math.sin(perp),
                    'lng': lng + offset * math.cos(perp)
                },
                'right_edge': {
                    'lat': lat - offset * math.sin(perp),
                    'lng': lng - offset * math.cos(perp)
                },
                'elevation': point.get('elevation', 8.0)  # Default flyover height
            })
        
        return {
            'vertices': deck_vertices,
            'total_width_m': total_width,
            'deck_thickness_m': 0.35,
            'surface_type': 'bituminous_concrete',
            'lane_markings': self._generate_lane_markings(num_lanes, standards)
        }
    
    def _generate_lane_markings(self, num_lanes: int, standards: Dict) -> Dict:
        """Generate lane marking specifications"""
        return {
            'lane_dividers': {
                'type': 'dashed',
                'width_mm': 150,
                'dash_length_m': 3,
                'gap_length_m': 9,
                'color': 'white'
            },
            'edge_lines': {
                'type': 'solid',
                'width_mm': 150,
                'color': 'white'
            },
            'median_marking': {
                'type': 'double_solid',
                'width_mm': 100,
                'spacing_mm': 100,
                'color': 'yellow'
            },
            'reflectors': {
                'spacing_m': 6,
                'type': 'cat_eye'
            }
        }
    
    def _generate_pier_positions(self, points: List[Dict[str, float]],
                                  spacing_m: float) -> List[Dict[str, Any]]:
        """Generate pier/support positions along route"""
        total_length = self._calculate_route_length(points)
        num_piers = int(total_length / spacing_m) + 1
        
        piers = []
        accumulated_distance = 0
        point_index = 0
        
        for pier_num in range(num_piers):
            target_distance = pier_num * spacing_m
            
            # Find position at target distance
            while point_index < len(points) - 1:
                if 'lat' in points[point_index]:
                    segment_length = self._haversine_distance(
                        points[point_index]['lat'], points[point_index]['lng'],
                        points[point_index + 1]['lat'], points[point_index + 1]['lng']
                    )
                else:
                    dx = points[point_index + 1].get('x', 0) - points[point_index].get('x', 0)
                    dy = points[point_index + 1].get('y', 0) - points[point_index].get('y', 0)
                    segment_length = math.sqrt(dx**2 + dy**2)
                
                if accumulated_distance + segment_length >= target_distance:
                    break
                accumulated_distance += segment_length
                point_index += 1
            
            if point_index < len(points):
                point = points[point_index]
                piers.append({
                    'id': f'P{pier_num + 1}',
                    'position': {
                        'lat': point.get('lat', point.get('y', 0)),
                        'lng': point.get('lng', point.get('x', 0))
                    },
                    'chainage_m': pier_num * spacing_m,
                    'height_m': point.get('elevation', 8.0),
                    'foundation_type': self._determine_foundation_type(point),
                    'pier_type': 'hammer_head' if pier_num % 3 == 0 else 'single_column'
                })
        
        return piers
    
    def _determine_foundation_type(self, point: Dict) -> str:
        """Determine foundation type based on location"""
        # In real implementation, this would check soil data
        soil_type = point.get('soil_type', 'normal')
        if soil_type == 'soft':
            return 'pile_foundation'
        elif soil_type == 'rock':
            return 'shallow_foundation'
        else:
            return 'open_foundation'
    
    def _generate_camera_path(self, points: List[Dict[str, float]],
                               total_length: float) -> Dict[str, Any]:
        """Generate camera path for flyover animation"""
        camera_points = []
        
        for i, point in enumerate(points):
            lat = point.get('lat', point.get('y', 0))
            lng = point.get('lng', point.get('x', 0))
            
            # Calculate camera position (elevated and offset)
            camera_height = point.get('elevation', 8.0) + 15  # 15m above deck
            
            # Calculate look-ahead direction
            if i < len(points) - 1:
                look_at = points[min(i + 3, len(points) - 1)]
            else:
                look_at = points[i]
            
            camera_points.append({
                'position': {
                    'lat': lat,
                    'lng': lng,
                    'altitude': camera_height
                },
                'look_at': {
                    'lat': look_at.get('lat', look_at.get('y', 0)),
                    'lng': look_at.get('lng', look_at.get('x', 0)),
                    'altitude': look_at.get('elevation', 8.0)
                },
                'time_seconds': i * (60 / len(points))  # 60 second flythrough
            })
        
        return {
            'points': camera_points,
            'duration_seconds': 60,
            'easing': 'ease_in_out',
            'loop': True,
            'field_of_view': 60
        }
    
    def _generate_cross_sections(self, num_lanes: int,
                                  standards: Dict,
                                  project_type: str) -> List[Dict[str, Any]]:
        """Generate typical cross-sections"""
        lane_width = standards['lane_width_m']
        shoulder = standards['shoulder_width_m']
        
        cross_sections = []
        
        # At-grade section
        cross_sections.append({
            'type': 'at_grade',
            'description': 'Typical ground-level section',
            'elements': self._build_cross_section_elements(
                num_lanes, standards, 'at_grade'
            )
        })
        
        # Elevated section
        cross_sections.append({
            'type': 'elevated',
            'description': 'Typical elevated/flyover section',
            'elements': self._build_cross_section_elements(
                num_lanes, standards, 'elevated'
            )
        })
        
        # Ramp section
        cross_sections.append({
            'type': 'ramp',
            'description': 'On/off ramp section',
            'elements': self._build_cross_section_elements(
                int(num_lanes / 2), standards, 'ramp'
            )
        })
        
        return cross_sections
    
    def _build_cross_section_elements(self, num_lanes: int,
                                       standards: Dict,
                                       section_type: str) -> List[Dict]:
        """Build elements for a cross-section"""
        lane_width = standards['lane_width_m']
        shoulder = standards['shoulder_width_m']
        median = standards['median_width_m']
        
        elements = []
        current_offset = -((num_lanes * lane_width / 2) + shoulder + median / 2)
        
        # Left barrier
        elements.append({
            'type': 'barrier',
            'offset_m': current_offset,
            'width_m': 0.3,
            'height_m': 1.1,
            'material': 'concrete'
        })
        current_offset += 0.3
        
        # Left shoulder
        elements.append({
            'type': 'shoulder',
            'offset_m': current_offset,
            'width_m': shoulder,
            'surface': 'asphalt'
        })
        current_offset += shoulder
        
        # Lanes (left carriageway)
        for i in range(num_lanes // 2):
            elements.append({
                'type': 'lane',
                'offset_m': current_offset,
                'width_m': lane_width,
                'direction': 'forward'
            })
            current_offset += lane_width
        
        # Median
        elements.append({
            'type': 'median',
            'offset_m': current_offset,
            'width_m': median,
            'barrier_type': standards['barrier_type']
        })
        current_offset += median
        
        # Lanes (right carriageway)
        for i in range(num_lanes - num_lanes // 2):
            elements.append({
                'type': 'lane',
                'offset_m': current_offset,
                'width_m': lane_width,
                'direction': 'reverse'
            })
            current_offset += lane_width
        
        # Right shoulder
        elements.append({
            'type': 'shoulder',
            'offset_m': current_offset,
            'width_m': shoulder,
            'surface': 'asphalt'
        })
        current_offset += shoulder
        
        # Right barrier
        elements.append({
            'type': 'barrier',
            'offset_m': current_offset,
            'width_m': 0.3,
            'height_m': 1.1,
            'material': 'concrete'
        })
        
        return elements
    
    def _generate_lighting(self, points: List[Dict[str, float]],
                           standards: Dict) -> List[Dict[str, Any]]:
        """Generate street lighting positions"""
        spacing = standards['lighting_spacing_m']
        total_length = self._calculate_route_length(points)
        num_lights = int(total_length / spacing) + 1
        
        lights = []
        for i in range(num_lights):
            # Interpolate position
            progress = i / max(num_lights - 1, 1)
            point_index = int(progress * (len(points) - 1))
            point = points[min(point_index, len(points) - 1)]
            
            lights.append({
                'id': f'L{i + 1}',
                'position': {
                    'lat': point.get('lat', point.get('y', 0)),
                    'lng': point.get('lng', point.get('x', 0))
                },
                'chainage_m': i * spacing,
                'pole_height_m': 12,
                'light_type': 'LED_400W',
                'arm_length_m': 2.5,
                'side': 'both' if i % 2 == 0 else 'left'  # Alternate sides
            })
        
        return lights
    
    def _generate_barriers(self, points: List[Dict[str, float]],
                           num_lanes: int,
                           standards: Dict) -> Dict[str, Any]:
        """Generate barrier/railing geometry"""
        return {
            'edge_barriers': {
                'type': standards['barrier_type'],
                'height_m': 1.1,
                'width_m': 0.3,
                'material': 'reinforced_concrete'
            },
            'median_barrier': {
                'type': 'concrete_barrier',
                'height_m': 0.81,  # F-shape barrier
                'width_m': 0.5
            },
            'anti_glare_screen': num_lanes >= 6,  # For wide roads
            'sound_barriers': standards.get('barrier_type') == 'sound_barrier'
        }
    
    def _calculate_sight_distances(self, points: List[Dict[str, float]],
                                    standards: Dict) -> Dict[str, Any]:
        """Calculate stopping and passing sight distances"""
        design_speed = standards['design_speed_kmh']
        
        # Standard sight distance calculations
        stopping_sight_distance = 0.278 * design_speed * 2.5 + \
                                  (design_speed ** 2) / (254 * 0.35)
        
        passing_sight_distance = design_speed * 10  # Simplified formula
        
        return {
            'design_speed_kmh': design_speed,
            'stopping_sight_distance_m': round(stopping_sight_distance, 1),
            'passing_sight_distance_m': round(passing_sight_distance, 1),
            'minimum_curve_radius_m': round((design_speed ** 2) / (127 * 0.15), 1),
            'vertical_clearance_m': standards['min_vertical_clearance_m'],
            'compliance': 'Meets design standards'
        }
    
    def _get_animation_config(self) -> Dict[str, Any]:
        """Get animation configuration"""
        return {
            'frame_rate': 30,
            'quality': 'high',
            'shadows': True,
            'ambient_occlusion': True,
            'anti_aliasing': 'msaa_4x',
            'sky_type': 'procedural',
            'time_of_day': 'afternoon',
            'weather': 'clear'
        }
    
    def _get_material_specs(self, country_code: str) -> Dict[str, Any]:
        """Get material specifications by country"""
        return {
            'concrete': {
                'grade': 'M40' if country_code in ['IN', 'AE'] else 'C40',
                'cover_mm': 50,
                'texture': 'smooth_formwork'
            },
            'asphalt': {
                'type': 'DBM+BC',  # Dense Bituminous Macadam + Bituminous Concrete
                'thickness_mm': 90,
                'texture': 'dense_graded'
            },
            'steel': {
                'grade': 'Fe500D' if country_code == 'IN' else 'Grade 60',
                'coating': 'epoxy_coated' if country_code in ['US', 'AE'] else 'uncoated'
            }
        }
    
    def _generate_elevation_profile(self, points: List[Dict[str, float]]) -> Dict[str, Any]:
        """Generate elevation profile data"""
        elevations = []
        chainage = 0
        
        for i, point in enumerate(points):
            if i > 0:
                if 'lat' in point:
                    chainage += self._haversine_distance(
                        points[i-1]['lat'], points[i-1]['lng'],
                        point['lat'], point['lng']
                    )
                else:
                    dx = point.get('x', 0) - points[i-1].get('x', 0)
                    dy = point.get('y', 0) - points[i-1].get('y', 0)
                    chainage += math.sqrt(dx**2 + dy**2)
            
            elevations.append({
                'chainage_m': round(chainage, 1),
                'elevation_m': point.get('elevation', 0),
                'gradient_percent': point.get('gradient', 0)
            })
        
        return {
            'profile_points': elevations,
            'max_elevation_m': max(e['elevation_m'] for e in elevations),
            'min_elevation_m': min(e['elevation_m'] for e in elevations),
            'total_rise_m': abs(elevations[-1]['elevation_m'] - elevations[0]['elevation_m'])
        }
    
    def _get_render_settings(self) -> Dict[str, Any]:
        """Get rendering settings"""
        return {
            'renderer': 'webgl',
            'resolution': {'width': 1920, 'height': 1080},
            'anti_aliasing': True,
            'shadows': True,
            'reflections': True,
            'atmosphere': True,
            'fog_density': 0.0002,
            'sun_position': {'azimuth': 45, 'altitude': 60}
        }


class TrafficFlowAnimator:
    """
    Creates traffic flow animations showing before/after scenarios
    """
    
    # Traffic parameters by country
    TRAFFIC_PARAMS = {
        'IN': {
            'vehicle_mix': {'car': 0.4, 'two_wheeler': 0.35, 'bus': 0.1, 'truck': 0.15},
            'lane_discipline': 0.5,  # 0-1, 1 being perfect discipline
            'average_speed_factor': 0.7  # Compared to speed limit
        },
        'US': {
            'vehicle_mix': {'car': 0.7, 'suv': 0.15, 'truck': 0.15},
            'lane_discipline': 0.9,
            'average_speed_factor': 0.85
        },
        'DE': {
            'vehicle_mix': {'car': 0.75, 'truck': 0.2, 'motorcycle': 0.05},
            'lane_discipline': 0.95,
            'average_speed_factor': 0.9
        }
    }
    
    def generate_traffic_animation(self,
                                    route_points: List[Dict[str, float]],
                                    before_traffic: Dict[str, Any],
                                    after_traffic: Dict[str, Any],
                                    country_code: str) -> Dict[str, Any]:
        """Generate traffic flow animation data"""
        params = self.TRAFFIC_PARAMS.get(country_code, self.TRAFFIC_PARAMS['IN'])
        
        # Generate vehicle paths for before scenario
        before_vehicles = self._generate_vehicle_paths(
            route_points,
            before_traffic.get('volume', 5000),
            before_traffic.get('speed_kmh', 25),
            params
        )
        
        # Generate vehicle paths for after scenario
        after_vehicles = self._generate_vehicle_paths(
            route_points,
            after_traffic.get('volume', 4500),
            after_traffic.get('speed_kmh', 55),
            params
        )
        
        # Calculate metrics comparison
        metrics_comparison = self._calculate_comparison_metrics(
            before_traffic, after_traffic
        )
        
        return {
            'animation_type': 'traffic_flow',
            'duration_seconds': 30,
            'before': {
                'vehicles': before_vehicles,
                'congestion_level': before_traffic.get('congestion', 0.8),
                'average_speed_kmh': before_traffic.get('speed_kmh', 25),
                'queue_length_m': before_traffic.get('queue', 500)
            },
            'after': {
                'vehicles': after_vehicles,
                'congestion_level': after_traffic.get('congestion', 0.3),
                'average_speed_kmh': after_traffic.get('speed_kmh', 55),
                'queue_length_m': after_traffic.get('queue', 50)
            },
            'metrics_comparison': metrics_comparison,
            'playback_config': {
                'frame_rate': 30,
                'time_scale': 10,  # 10x speed
                'split_view': True,
                'sync_playback': True
            },
            'visual_config': {
                'vehicle_colors': {
                    'car': '#3b82f6',
                    'truck': '#f59e0b',
                    'bus': '#10b981',
                    'two_wheeler': '#8b5cf6'
                },
                'congestion_overlay': True,
                'speed_indicators': True,
                'trail_effect': True
            }
        }
    
    def _generate_vehicle_paths(self,
                                 route_points: List[Dict],
                                 volume: int,
                                 avg_speed: float,
                                 params: Dict) -> List[Dict]:
        """Generate individual vehicle movement paths"""
        vehicles = []
        num_vehicles = min(volume // 100, 50)  # Cap for performance
        
        for i in range(num_vehicles):
            vehicle_type = self._weighted_choice(params['vehicle_mix'])
            
            # Calculate vehicle path with some randomization
            path = []
            for point in route_points:
                lat = point.get('lat', point.get('y', 0))
                lng = point.get('lng', point.get('x', 0))
                
                # Add slight lateral offset based on lane
                lane_offset = (i % 3 - 1) * 0.00003  # Approximate lane width in degrees
                
                path.append({
                    'lat': lat,
                    'lng': lng + lane_offset * params['lane_discipline']
                })
            
            vehicles.append({
                'id': f'v_{i}',
                'type': vehicle_type,
                'path': path,
                'speed_kmh': avg_speed * (0.8 + 0.4 * (i % 10) / 10),  # Vary speed
                'start_delay_seconds': i * 0.5,  # Stagger vehicle starts
                'size': self._get_vehicle_size(vehicle_type)
            })
        
        return vehicles
    
    def _weighted_choice(self, weights: Dict[str, float]) -> str:
        """Make weighted random choice"""
        items = list(weights.keys())
        probs = list(weights.values())
        total = sum(probs)
        probs = [p / total for p in probs]
        
        import random
        return random.choices(items, probs)[0]
    
    def _get_vehicle_size(self, vehicle_type: str) -> Dict[str, float]:
        """Get vehicle dimensions"""
        sizes = {
            'car': {'length': 4.5, 'width': 1.8},
            'suv': {'length': 5.0, 'width': 2.0},
            'truck': {'length': 12.0, 'width': 2.5},
            'bus': {'length': 12.0, 'width': 2.5},
            'two_wheeler': {'length': 2.0, 'width': 0.8},
            'motorcycle': {'length': 2.0, 'width': 0.8}
        }
        return sizes.get(vehicle_type, sizes['car'])
    
    def _calculate_comparison_metrics(self,
                                       before: Dict,
                                       after: Dict) -> Dict[str, Any]:
        """Calculate before/after comparison metrics"""
        speed_improvement = (
            (after.get('speed_kmh', 50) - before.get('speed_kmh', 25)) /
            before.get('speed_kmh', 25) * 100
        )
        
        congestion_reduction = (
            (before.get('congestion', 0.8) - after.get('congestion', 0.3)) /
            before.get('congestion', 0.8) * 100
        )
        
        queue_reduction = (
            (before.get('queue', 500) - after.get('queue', 50)) /
            before.get('queue', 500) * 100
        )
        
        return {
            'speed_improvement': {
                'value': f"+{speed_improvement:.0f}%",
                'label': 'Speed Increase'
            },
            'congestion_reduction': {
                'value': f"-{congestion_reduction:.0f}%",
                'label': 'Congestion Reduction'
            },
            'queue_reduction': {
                'value': f"-{queue_reduction:.0f}%",
                'label': 'Queue Length Reduction'
            },
            'travel_time_saved': {
                'value': self._calculate_time_saved(before, after),
                'label': 'Time Saved per Trip'
            }
        }
    
    def _calculate_time_saved(self, before: Dict, after: Dict) -> str:
        """Calculate travel time saved"""
        # Assuming 5km typical trip
        trip_distance = 5
        time_before = trip_distance / before.get('speed_kmh', 25) * 60  # minutes
        time_after = trip_distance / after.get('speed_kmh', 50) * 60
        saved = time_before - time_after
        return f"{saved:.0f} minutes"


# Singleton instances
flyover_viz = FlyoverVisualization()
traffic_animator = TrafficFlowAnimator()
