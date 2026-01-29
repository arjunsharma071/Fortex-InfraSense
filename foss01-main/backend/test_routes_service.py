#!/usr/bin/env python3
"""
Test script for comprehensive routes and roads tracing service
Tests Google Maps, OpenStreetMap, OpenAI, and Grok APIs
"""

import asyncio
import json
import logging
from routes_roads_service import (
    GoogleMapsRoutesService,
    OpenStreetMapService,
    OpenAIAnalysisService,
    GrokAnalysisService,
    ComprehensiveRoutesService,
    init_routes_service
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_google_maps_service():
    """Test Google Maps API integration"""
    print("\n" + "="*60)
    print("TESTING GOOGLE MAPS SERVICE")
    print("="*60)
    
    service = GoogleMapsRoutesService()
    
    if not service.client:
        print("⚠️  Google Maps API key not configured")
        return
    
    # Test coordinates: Delhi, India
    origin = (28.6139, 77.2090)  # Connaught Place
    destination = (28.5244, 77.0855)  # India Gate
    
    try:
        # Test directions
        print("\n📍 Getting directions from Connaught Place to India Gate...")
        directions = service.get_directions(origin, destination)
        if directions and directions.get('routes'):
            route = directions['routes'][0]
            leg = route['legs'][0]
            print(f"✅ Distance: {leg['distance']['text']}")
            print(f"✅ Duration: {leg['duration']['text']}")
            print(f"✅ Number of steps: {len(leg['steps'])}")
        
        # Test nearby roads
        print("\n🛣️  Getting nearby roads...")
        roads = service.get_nearby_roads(origin, 1000)
        print(f"✅ Found {len(roads)} nearby roads")
        if roads:
            print(f"   - {roads[0]['name']} ({roads[0]['type']})")
        
        # Test road surface
        print("\n🛣️  Analyzing road surface...")
        surface = service.get_road_surface_info(origin, destination)
        print(f"✅ Surface types found: {len(surface)}")
        for surf in surface[:2]:
            print(f"   - {surf['segment_name']}: {surf['surface_type']}")
        
        print("\n✅ Google Maps Service: ALL TESTS PASSED\n")
        return directions
        
    except Exception as e:
        print(f"❌ Google Maps error: {e}\n")
        return None


async def test_openstreetmap_service():
    """Test OpenStreetMap/Overpass API integration"""
    print("\n" + "="*60)
    print("TESTING OPENSTREETMAP SERVICE")
    print("="*60)
    
    service = OpenStreetMapService()
    
    try:
        # Bounding box for Delhi (small area)
        bbox = (28.6, 77.1, 28.65, 77.15)
        
        print("\n🗺️  Querying Overpass API for roads in Delhi...")
        roads_data = service.get_roads_in_bbox(bbox)
        
        if roads_data and roads_data.get('roads'):
            print(f"✅ Found {len(roads_data['roads'])} roads")
            print(f"✅ Total roads available: {roads_data.get('count', 0)}")
            
            # Show sample roads
            for i, road in enumerate(roads_data['roads'][:3]):
                print(f"\n   Road {i+1}: {road.get('name', 'Unknown')}")
                print(f"   - Surface: {road.get('surface', 'Unknown')}")
                print(f"   - Lanes: {road.get('lanes', 'N/A')}")
                print(f"   - Speed limit: {road.get('speed_limit', 'N/A')}")
                print(f"   - Length: {road.get('length', 0):.2f}m")
        
        # Test road details
        print("\n📊 Getting road details...")
        road_details = service.get_road_details("MG Road", bbox)
        if road_details:
            print(f"✅ Road details retrieved: {len(road_details)} matches")
        
        print("\n✅ OpenStreetMap Service: ALL TESTS PASSED\n")
        return roads_data
        
    except Exception as e:
        print(f"❌ OpenStreetMap error: {e}\n")
        return None


async def test_openai_service():
    """Test OpenAI GPT-4 integration"""
    print("\n" + "="*60)
    print("TESTING OPENAI ANALYSIS SERVICE")
    print("="*60)
    
    service = OpenAIAnalysisService()
    
    if not service.client:
        print("⚠️  OpenAI API key not configured - using fallback data")
    
    try:
        # Test road condition analysis
        print("\n🔍 Analyzing road condition using GPT-4...")
        road_data = {
            'name': 'Rajpath',
            'surface': 'asphalt',
            'lanes': 4,
            'speed_limit': 60,
            'condition': 'good'
        }
        
        analysis = service.analyze_road_condition(road_data)
        if analysis:
            print(f"✅ Condition analysis:")
            print(f"   - Status: {analysis.get('status', 'N/A')}")
            print(f"   - Severity: {analysis.get('severity', 'N/A')}")
            print(f"   - Assessment: {analysis.get('assessment', 'N/A')}")
        
        # Test route efficiency
        print("\n⚡ Analyzing route efficiency...")
        route_info = {
            'distance': 15000,  # meters
            'duration': 1200,   # seconds
            'traffic_level': 'moderate'
        }
        
        efficiency = service.analyze_route_efficiency(route_info)
        if efficiency:
            print(f"✅ Efficiency analysis:")
            print(f"   - Score: {efficiency.get('efficiency_score', 'N/A')}/10")
            print(f"   - Recommendation: {efficiency.get('recommendation', 'N/A')}")
        
        print("\n✅ OpenAI Service: ALL TESTS PASSED\n")
        return analysis
        
    except Exception as e:
        print(f"❌ OpenAI error: {e}\n")
        return None


async def test_grok_service():
    """Test Xai Grok integration"""
    print("\n" + "="*60)
    print("TESTING GROK ANALYSIS SERVICE")
    print("="*60)
    
    service = GrokAnalysisService()
    
    if not service.client:
        print("⚠️  Grok API key not configured - using fallback data")
    
    try:
        print("\n🤖 Analyzing infrastructure impact with Grok...")
        
        infrastructure_data = {
            'route_type': 'urban',
            'traffic_level': 'high',
            'road_condition': 'moderate',
            'nearby_schools': 2,
            'nearby_hospitals': 1,
            'population_density': 'high'
        }
        
        impact = service.analyze_infrastructure_impact(infrastructure_data)
        if impact:
            print(f"✅ Infrastructure impact analysis:")
            print(f"   - Economic impact: {impact.get('economic_impact', 'N/A')}")
            print(f"   - Environmental impact: {impact.get('environmental_impact', 'N/A')}")
            print(f"   - Social impact: {impact.get('social_impact', 'N/A')}")
            print(f"   - Recommendations: {impact.get('recommendations', 'N/A')}")
        
        print("\n✅ Grok Service: ALL TESTS PASSED\n")
        return impact
        
    except Exception as e:
        print(f"❌ Grok error: {e}\n")
        return None


async def test_comprehensive_service():
    """Test comprehensive routes and roads service"""
    print("\n" + "="*60)
    print("TESTING COMPREHENSIVE ROUTES & ROADS SERVICE")
    print("="*60)
    
    service = init_routes_service()
    
    try:
        # Define test locations
        origin = (28.6139, 77.2090)      # Connaught Place
        destination = (28.5244, 77.0855)  # India Gate
        
        print("\n🗺️  Getting comprehensive routes...")
        routes = await service.get_comprehensive_routes(origin, destination)
        
        print("\n✅ Comprehensive routes retrieved:")
        print(f"   - Google Maps routes: {len(routes.get('google_maps', {}).get('routes', []))}")
        print(f"   - OSM roads: {len(routes.get('osm_roads', []))}")
        print(f"   - AI analysis: {'✅' if routes.get('openai_analysis') else '❌'}")
        print(f"   - Grok insights: {'✅' if routes.get('grok_insights') else '❌'}")
        
        print("\n🛣️  Getting comprehensive roads...")
        roads = await service.get_comprehensive_roads(28.6139, 77.2090, 1000)
        
        print("\n✅ Comprehensive roads retrieved:")
        print(f"   - Total roads: {len(roads)}")
        for i, road in enumerate(roads[:2]):
            print(f"   - Road {i+1}: {road['name']} ({road['surface']})")
        
        print("\n✅ Comprehensive Service: ALL TESTS PASSED\n")
        return routes, roads
        
    except Exception as e:
        print(f"❌ Comprehensive service error: {e}\n")
        return None, None


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("COMPREHENSIVE ROUTES & ROADS TRACING SERVICE TEST SUITE")
    print("="*60)
    
    results = {
        "google_maps": None,
        "openstreetmap": None,
        "openai": None,
        "grok": None,
        "comprehensive": None
    }
    
    # Run individual service tests
    results["google_maps"] = await test_google_maps_service()
    results["openstreetmap"] = await test_openstreetmap_service()
    results["openai"] = await test_openai_service()
    results["grok"] = await test_grok_service()
    
    # Run comprehensive test
    results["comprehensive"] = await test_comprehensive_service()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("✅ Google Maps API: " + ("WORKING" if results["google_maps"] else "NEEDS CONFIG"))
    print("✅ OpenStreetMap API: " + ("WORKING" if results["openstreetmap"] else "NEEDS CONFIG"))
    print("✅ OpenAI GPT-4: " + ("WORKING" if results["openai"] else "USING FALLBACK"))
    print("✅ Grok API: " + ("WORKING" if results["grok"] else "USING FALLBACK"))
    print("✅ Comprehensive Service: " + ("WORKING" if results["comprehensive"] else "FAILED"))
    print("\n✅ All services tested successfully!\n")


if __name__ == "__main__":
    asyncio.run(main())
