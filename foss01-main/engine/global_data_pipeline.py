# engine/global_data_pipeline.py
"""
InfraSense AI - Global Data Pipeline
Multi-country data aggregation for infrastructure analysis
Integrates OSM, traffic, accidents, population, and economic data
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import math


class DataSource(Enum):
    """Available data sources"""
    OSM = "openstreetmap"
    GOOGLE_MAPS = "google_maps"
    GOVERNMENT_OPEN_DATA = "government_open_data"
    TRAFFIC_SENSORS = "traffic_sensors"
    ACCIDENT_REGISTRY = "accident_registry"
    CENSUS = "census_data"
    SATELLITE = "satellite_imagery"
    WEATHER = "weather_service"


@dataclass
class DataQuality:
    """Data quality metrics"""
    completeness: float  # 0-1
    accuracy: float      # 0-1
    freshness_days: int
    coverage_percent: float
    source: DataSource


class GlobalDataPipeline:
    """
    Multi-country data aggregation pipeline
    Provides unified interface to various data sources
    """
    
    # Data source availability by country
    DATA_AVAILABILITY = {
        'IN': {
            'osm': DataQuality(0.85, 0.90, 30, 95, DataSource.OSM),
            'traffic': DataQuality(0.75, 0.85, 1, 70, DataSource.TRAFFIC_SENSORS),
            'accidents': DataQuality(0.60, 0.80, 7, 60, DataSource.ACCIDENT_REGISTRY),
            'population': DataQuality(0.95, 0.90, 365, 99, DataSource.CENSUS),
        },
        'US': {
            'osm': DataQuality(0.95, 0.95, 7, 99, DataSource.OSM),
            'traffic': DataQuality(0.90, 0.95, 0.1, 90, DataSource.TRAFFIC_SENSORS),  # Real-time
            'accidents': DataQuality(0.95, 0.95, 1, 95, DataSource.ACCIDENT_REGISTRY),
            'population': DataQuality(0.99, 0.98, 365, 100, DataSource.CENSUS),
        },
        'DE': {
            'osm': DataQuality(0.98, 0.98, 7, 99, DataSource.OSM),
            'traffic': DataQuality(0.92, 0.95, 0.1, 85, DataSource.TRAFFIC_SENSORS),
            'accidents': DataQuality(0.95, 0.95, 1, 98, DataSource.ACCIDENT_REGISTRY),
            'population': DataQuality(0.99, 0.99, 365, 100, DataSource.CENSUS),
        },
        'NG': {
            'osm': DataQuality(0.60, 0.75, 60, 70, DataSource.OSM),
            'traffic': DataQuality(0.30, 0.60, 7, 30, DataSource.TRAFFIC_SENSORS),
            'accidents': DataQuality(0.25, 0.50, 30, 25, DataSource.ACCIDENT_REGISTRY),
            'population': DataQuality(0.80, 0.75, 365, 90, DataSource.CENSUS),
        },
        'BR': {
            'osm': DataQuality(0.80, 0.85, 30, 90, DataSource.OSM),
            'traffic': DataQuality(0.70, 0.80, 1, 65, DataSource.TRAFFIC_SENSORS),
            'accidents': DataQuality(0.75, 0.80, 7, 70, DataSource.ACCIDENT_REGISTRY),
            'population': DataQuality(0.95, 0.90, 365, 99, DataSource.CENSUS),
        }
    }
    
    # Country-specific API endpoints (simulation)
    COUNTRY_APIS = {
        'IN': {
            'traffic': 'https://api.traffic.gov.in/v1/',
            'accidents': 'https://morth.gov.in/open-data/',
            'roads': 'https://nhai.gov.in/api/'
        },
        'US': {
            'traffic': 'https://api.tomtom.com/traffic/',
            'accidents': 'https://www.nhtsa.gov/api/',
            'roads': 'https://datahub.transportation.gov/api/'
        },
        'DE': {
            'traffic': 'https://autobahn.api.bund.dev/',
            'accidents': 'https://unfallatlas.statistikportal.de/',
            'roads': 'https://www.bast.de/api/'
        }
    }
    
    # Road classification mappings
    ROAD_CLASSIFICATIONS = {
        'IN': {
            'national_highway': ['NH', 'National Highway'],
            'state_highway': ['SH', 'State Highway'],
            'district_road': ['MDR', 'ODR'],
            'urban_road': ['MC Road', 'City Road']
        },
        'US': {
            'interstate': ['I-', 'Interstate'],
            'us_highway': ['US-', 'US Route'],
            'state_route': ['SR-', 'State Route'],
            'county_road': ['CR-', 'County Road']
        },
        'DE': {
            'autobahn': ['A', 'Bundesautobahn'],
            'bundesstrasse': ['B', 'Bundesstraße'],
            'landesstrasse': ['L', 'Landesstraße'],
            'kreisstrasse': ['K', 'Kreisstraße']
        }
    }
    
    def __init__(self, cache_ttl_hours: int = 24):
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self._cache = {}
        self._last_fetch = {}
    
    def fetch_comprehensive_data(self,
                                  lat: float,
                                  lng: float,
                                  radius_km: float,
                                  country_code: str) -> Dict[str, Any]:
        """
        Fetch all available data for a location
        """
        cache_key = f"{lat:.4f}_{lng:.4f}_{radius_km}_{country_code}"
        
        # Check cache
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        # Fetch from all sources
        road_network = self._fetch_road_network(lat, lng, radius_km, country_code)
        traffic_data = self._fetch_traffic_data(lat, lng, radius_km, country_code)
        accident_data = self._fetch_accident_data(lat, lng, radius_km, country_code)
        population_data = self._fetch_population_data(lat, lng, radius_km, country_code)
        economic_data = self._fetch_economic_data(lat, lng, radius_km, country_code)
        infrastructure_data = self._fetch_existing_infrastructure(lat, lng, radius_km, country_code)
        
        # Aggregate and normalize
        result = {
            'location': {
                'lat': lat,
                'lng': lng,
                'radius_km': radius_km,
                'country_code': country_code
            },
            'fetch_timestamp': datetime.now().isoformat(),
            'data_quality': self._assess_data_quality(country_code),
            'road_network': road_network,
            'traffic': traffic_data,
            'accidents': accident_data,
            'population': population_data,
            'economic': economic_data,
            'infrastructure': infrastructure_data,
            'derived_metrics': self._calculate_derived_metrics(
                road_network, traffic_data, accident_data, population_data
            )
        }
        
        # Cache result
        self._cache[cache_key] = result
        self._last_fetch[cache_key] = datetime.now()
        
        return result
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache:
            return False
        if cache_key not in self._last_fetch:
            return False
        return datetime.now() - self._last_fetch[cache_key] < self.cache_ttl
    
    def _fetch_road_network(self, lat: float, lng: float,
                            radius_km: float, country_code: str) -> Dict[str, Any]:
        """Fetch road network data from OSM and government sources"""
        # In production, this would call actual APIs
        # Here we simulate comprehensive road data
        
        road_classes = self.ROAD_CLASSIFICATIONS.get(
            country_code, 
            self.ROAD_CLASSIFICATIONS['US']
        )
        
        # Simulated road network data
        roads = []
        road_types = ['primary', 'secondary', 'tertiary', 'residential']
        
        for i, road_type in enumerate(road_types):
            roads.append({
                'id': f'road_{i}',
                'type': road_type,
                'name': f'Sample {road_type.title()} Road',
                'length_km': 2.5 + i * 0.5,
                'lanes': 4 - i if i < 3 else 2,
                'surface': 'asphalt' if i < 2 else 'concrete',
                'condition': 'good' if i < 2 else 'fair',
                'speed_limit_kmh': 80 - i * 10,
                'geometry': self._generate_sample_geometry(lat, lng, i)
            })
        
        # Calculate network metrics
        total_length = sum(r['length_km'] for r in roads)
        
        return {
            'roads': roads,
            'total_length_km': total_length,
            'network_density_km_per_sqkm': total_length / (math.pi * radius_km ** 2),
            'junction_count': len(roads) * 2,
            'road_classification': road_classes,
            'connectivity_index': 0.75,  # Simulated
            'pavement_condition': {
                'good': 0.6,
                'fair': 0.3,
                'poor': 0.1
            }
        }
    
    def _generate_sample_geometry(self, lat: float, lng: float, 
                                   index: int) -> List[Dict[str, float]]:
        """Generate sample road geometry"""
        offset = 0.01 * (index + 1)
        return [
            {'lat': lat - offset, 'lng': lng - offset},
            {'lat': lat, 'lng': lng},
            {'lat': lat + offset, 'lng': lng + offset}
        ]
    
    def _fetch_traffic_data(self, lat: float, lng: float,
                            radius_km: float, country_code: str) -> Dict[str, Any]:
        """Fetch real-time and historical traffic data"""
        
        # Simulate traffic data based on country patterns
        traffic_patterns = {
            'IN': {'peak_hours': [9, 18], 'congestion_factor': 0.75},
            'US': {'peak_hours': [8, 17], 'congestion_factor': 0.60},
            'DE': {'peak_hours': [8, 17], 'congestion_factor': 0.45},
            'NG': {'peak_hours': [8, 18], 'congestion_factor': 0.85},
            'BR': {'peak_hours': [7, 18], 'congestion_factor': 0.70}
        }
        
        pattern = traffic_patterns.get(country_code, traffic_patterns['US'])
        
        # Generate hourly traffic profile
        hourly_volume = []
        base_volume = 3000  # Vehicles per hour
        
        for hour in range(24):
            if hour in pattern['peak_hours']:
                volume = base_volume * 2.5
            elif 7 <= hour <= 20:
                volume = base_volume * 1.5
            else:
                volume = base_volume * 0.3
            
            hourly_volume.append({
                'hour': hour,
                'volume': int(volume),
                'speed_kmh': 60 - (volume / base_volume) * 20,
                'congestion_level': min(volume / (base_volume * 3), 1.0)
            })
        
        return {
            'current': {
                'volume_per_hour': int(base_volume * 1.5),
                'average_speed_kmh': 35,
                'congestion_level': pattern['congestion_factor'],
                'delay_minutes': int(pattern['congestion_factor'] * 20),
                'timestamp': datetime.now().isoformat()
            },
            'historical': {
                'daily_pattern': hourly_volume,
                'peak_hours': pattern['peak_hours'],
                'aadt': base_volume * 24 * 0.8,  # Annual Average Daily Traffic
                'growth_rate_percent': 5.5
            },
            'segments': [
                {
                    'id': f'seg_{i}',
                    'congestion': pattern['congestion_factor'] + (i - 1) * 0.1,
                    'speed_kmh': 40 - i * 5
                }
                for i in range(3)
            ]
        }
    
    def _fetch_accident_data(self, lat: float, lng: float,
                             radius_km: float, country_code: str) -> Dict[str, Any]:
        """Fetch accident/crash data"""
        
        # Accident rates by country (per billion vehicle-km)
        accident_rates = {
            'IN': {'fatal': 150, 'serious': 450, 'minor': 800},
            'US': {'fatal': 7.3, 'serious': 50, 'minor': 200},
            'DE': {'fatal': 4.1, 'serious': 35, 'minor': 150},
            'NG': {'fatal': 210, 'serious': 500, 'minor': 700},
            'BR': {'fatal': 90, 'serious': 300, 'minor': 600}
        }
        
        rates = accident_rates.get(country_code, accident_rates['US'])
        
        # Generate sample accident hotspots
        hotspots = [
            {
                'id': f'hotspot_{i}',
                'location': {'lat': lat + 0.005 * i, 'lng': lng + 0.003 * i},
                'severity_score': 0.8 - i * 0.2,
                'accident_count_yearly': 15 - i * 3,
                'primary_cause': ['speeding', 'red_light_running', 'wrong_way'][i % 3],
                'time_pattern': 'evening_peak' if i % 2 == 0 else 'morning_peak'
            }
            for i in range(3)
        ]
        
        return {
            'statistics': {
                'total_accidents_yearly': int(rates['fatal'] + rates['serious'] + rates['minor']),
                'fatal_rate': rates['fatal'],
                'serious_injury_rate': rates['serious'],
                'minor_injury_rate': rates['minor'],
                'trend': 'decreasing' if country_code in ['DE', 'US'] else 'stable'
            },
            'hotspots': hotspots,
            'causes': {
                'speeding': 0.30,
                'drunk_driving': 0.15,
                'wrong_overtaking': 0.20,
                'pedestrian_fault': 0.10,
                'vehicle_defect': 0.05,
                'road_condition': 0.10,
                'weather': 0.10
            },
            'vulnerable_users': {
                'pedestrian_percent': 25 if country_code == 'IN' else 15,
                'cyclist_percent': 5 if country_code == 'IN' else 10,
                'two_wheeler_percent': 35 if country_code == 'IN' else 5
            }
        }
    
    def _fetch_population_data(self, lat: float, lng: float,
                               radius_km: float, country_code: str) -> Dict[str, Any]:
        """Fetch population and demographic data"""
        
        # Density estimates by country (people per sq km for urban areas)
        densities = {
            'IN': {'urban': 11000, 'suburban': 4000, 'rural': 400},
            'US': {'urban': 4500, 'suburban': 1500, 'rural': 35},
            'DE': {'urban': 4000, 'suburban': 1000, 'rural': 180},
            'NG': {'urban': 20000, 'suburban': 5000, 'rural': 200},
            'BR': {'urban': 7500, 'suburban': 2500, 'rural': 25}
        }
        
        density = densities.get(country_code, densities['US'])
        area = math.pi * radius_km ** 2
        
        # Simulate urban area in radius
        urban_fraction = 0.4
        population = int(
            density['urban'] * area * urban_fraction +
            density['suburban'] * area * (1 - urban_fraction)
        )
        
        return {
            'total_population': population,
            'density_per_sqkm': int(population / area),
            'growth_rate_percent': 2.5 if country_code in ['IN', 'NG'] else 0.8,
            'urbanization_level': urban_fraction,
            'demographics': {
                'working_age_percent': 65,
                'vehicle_ownership_per_1000': 180 if country_code == 'IN' else 800,
                'commuter_percent': 45
            },
            'employment_centers': [
                {
                    'type': 'commercial',
                    'location': {'lat': lat + 0.01, 'lng': lng + 0.01},
                    'employee_count': 5000
                },
                {
                    'type': 'industrial',
                    'location': {'lat': lat - 0.01, 'lng': lng + 0.02},
                    'employee_count': 3000
                }
            ]
        }
    
    def _fetch_economic_data(self, lat: float, lng: float,
                             radius_km: float, country_code: str) -> Dict[str, Any]:
        """Fetch economic and land use data"""
        
        # GDP per capita by country (USD)
        gdp_per_capita = {
            'IN': 2500, 'US': 65000, 'DE': 51000, 'NG': 2200, 'BR': 8900
        }
        
        gdp = gdp_per_capita.get(country_code, 10000)
        
        return {
            'gdp_per_capita_usd': gdp,
            'economic_growth_percent': 6.5 if country_code == 'IN' else 2.5,
            'land_use': {
                'residential': 0.35,
                'commercial': 0.25,
                'industrial': 0.15,
                'green_space': 0.15,
                'infrastructure': 0.10
            },
            'property_values': {
                'commercial_per_sqm_usd': gdp * 0.5,
                'residential_per_sqm_usd': gdp * 0.3,
                'industrial_per_sqm_usd': gdp * 0.15
            },
            'economic_zones': [
                {
                    'type': 'special_economic_zone',
                    'distance_km': 3.5,
                    'impact': 'high'
                }
            ]
        }
    
    def _fetch_existing_infrastructure(self, lat: float, lng: float,
                                       radius_km: float, country_code: str) -> Dict[str, Any]:
        """Fetch existing infrastructure data"""
        return {
            'utilities': {
                'electricity_coverage': 0.95,
                'water_coverage': 0.90,
                'sewer_coverage': 0.85,
                'fiber_coverage': 0.60 if country_code in ['US', 'DE'] else 0.30
            },
            'transport': {
                'bus_routes': 5,
                'metro_stations': 2 if country_code in ['IN', 'BR'] else 0,
                'railway_stations': 1,
                'airports_within_50km': 1
            },
            'social': {
                'hospitals_within_5km': 3,
                'schools_within_2km': 8,
                'emergency_services': {
                    'police_response_min': 8,
                    'ambulance_response_min': 12,
                    'fire_response_min': 10
                }
            }
        }
    
    def _assess_data_quality(self, country_code: str) -> Dict[str, Any]:
        """Assess overall data quality for the country"""
        availability = self.DATA_AVAILABILITY.get(
            country_code, 
            self.DATA_AVAILABILITY.get('IN')
        )
        
        if not availability:
            return {'overall': 'low', 'score': 0.5}
        
        avg_completeness = sum(dq.completeness for dq in availability.values()) / len(availability)
        avg_accuracy = sum(dq.accuracy for dq in availability.values()) / len(availability)
        
        overall_score = (avg_completeness + avg_accuracy) / 2
        
        return {
            'overall': 'high' if overall_score > 0.85 else ('medium' if overall_score > 0.65 else 'low'),
            'score': round(overall_score, 2),
            'by_source': {
                source: {
                    'completeness': dq.completeness,
                    'accuracy': dq.accuracy,
                    'freshness_days': dq.freshness_days,
                    'coverage_percent': dq.coverage_percent
                }
                for source, dq in availability.items()
            },
            'recommendations': self._get_data_recommendations(availability)
        }
    
    def _get_data_recommendations(self, availability: Dict) -> List[str]:
        """Get recommendations for improving data quality"""
        recommendations = []
        
        for source, dq in availability.items():
            if dq.completeness < 0.7:
                recommendations.append(f"Improve {source} data collection coverage")
            if dq.freshness_days > 30:
                recommendations.append(f"Update {source} data more frequently")
            if dq.accuracy < 0.8:
                recommendations.append(f"Validate {source} data accuracy")
        
        return recommendations if recommendations else ["Data quality is adequate"]
    
    def _calculate_derived_metrics(self,
                                    road_network: Dict,
                                    traffic: Dict,
                                    accidents: Dict,
                                    population: Dict) -> Dict[str, Any]:
        """Calculate derived infrastructure metrics"""
        
        # Road km per capita
        road_per_capita = (
            road_network['total_length_km'] * 1000 / 
            max(population['total_population'], 1)
        )
        
        # Congestion cost (estimated annual)
        congestion_cost = (
            traffic['current']['delay_minutes'] *
            population['demographics']['commuter_percent'] / 100 *
            population['total_population'] *
            250 *  # Working days
            0.5    # Value of time ($/minute) - simplified
        )
        
        # Safety index
        accident_rate = accidents['statistics']['total_accidents_yearly']
        road_length = road_network['total_length_km']
        safety_index = 1 - min(accident_rate / (road_length * 100), 1)
        
        # Infrastructure Sufficiency Index
        isi = self._calculate_isi(road_network, traffic, population)
        
        return {
            'road_km_per_1000_pop': round(road_per_capita * 1000, 2),
            'annual_congestion_cost_million_usd': round(congestion_cost / 1_000_000, 2),
            'safety_index': round(safety_index, 2),
            'infrastructure_sufficiency_index': round(isi, 2),
            'priority_score': round((1 - isi) * 100, 1),
            'improvement_potential': {
                'capacity_gap_percent': round((1 - road_network['connectivity_index']) * 100, 1),
                'safety_improvement_needed': round((1 - safety_index) * 100, 1),
                'congestion_relief_priority': 'high' if traffic['current']['congestion_level'] > 0.6 else 'medium'
            }
        }
    
    def _calculate_isi(self, road_network: Dict, traffic: Dict, 
                       population: Dict) -> float:
        """Calculate Infrastructure Sufficiency Index"""
        # Simplified ISI calculation
        connectivity = road_network['connectivity_index']
        congestion = 1 - traffic['current']['congestion_level']
        density_factor = min(road_network['network_density_km_per_sqkm'] / 5, 1)
        
        return (connectivity * 0.4 + congestion * 0.4 + density_factor * 0.2)
    
    def aggregate_multi_region(self, regions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate data across multiple regions for comparison"""
        results = []
        
        for region in regions:
            data = self.fetch_comprehensive_data(
                region['lat'],
                region['lng'],
                region.get('radius_km', 5),
                region['country_code']
            )
            results.append({
                'region_name': region.get('name', f"Region {len(results)+1}"),
                'data': data
            })
        
        # Calculate comparative metrics
        comparison = {
            'regions': results,
            'rankings': self._calculate_rankings(results),
            'summary': {
                'total_regions': len(results),
                'avg_isi': sum(
                    r['data']['derived_metrics']['infrastructure_sufficiency_index'] 
                    for r in results
                ) / len(results),
                'highest_priority': max(
                    results, 
                    key=lambda x: x['data']['derived_metrics']['priority_score']
                )['region_name']
            }
        }
        
        return comparison
    
    def _calculate_rankings(self, results: List[Dict]) -> Dict[str, List]:
        """Calculate rankings across regions"""
        # Sort by different metrics
        by_priority = sorted(
            results, 
            key=lambda x: x['data']['derived_metrics']['priority_score'],
            reverse=True
        )
        
        by_safety = sorted(
            results,
            key=lambda x: x['data']['derived_metrics']['safety_index'],
            reverse=True
        )
        
        by_congestion = sorted(
            results,
            key=lambda x: x['data']['traffic']['current']['congestion_level'],
            reverse=True
        )
        
        return {
            'by_priority': [r['region_name'] for r in by_priority],
            'by_safety': [r['region_name'] for r in by_safety],
            'by_congestion': [r['region_name'] for r in by_congestion]
        }


# Singleton instance
global_pipeline = GlobalDataPipeline()
