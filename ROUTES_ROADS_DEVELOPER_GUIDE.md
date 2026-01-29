# Routes & Roads Tracing - Developer Integration Guide

## 🔧 Integration for Developers

This guide explains how to integrate the Routes & Roads API into your own applications.

---

## 📦 Installation & Setup

### 1. Ensure Dependencies Are Installed

```bash
cd foss01-main
pip install -r requirements.txt
```

Required packages:
```
requests>=2.28.0
aiohttp>=3.8.0
python-dotenv>=0.20.0
fastapi>=0.95.0
uvicorn>=0.21.0
```

### 2. Start the Backend Server

```bash
cd backend
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

Or use the provided script:
```bash
./run.sh
```

### 3. Verify API Is Running

```bash
curl http://localhost:8000/api/routes/comprehensive?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855
```

---

## 🐍 Python Integration

### Basic Usage

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Get comprehensive routes
def get_routes(origin_lat, origin_lng, dest_lat, dest_lng):
    response = requests.get(
        f"{BASE_URL}/api/routes/comprehensive",
        params={
            "origin_lat": origin_lat,
            "origin_lng": origin_lng,
            "dest_lat": dest_lat,
            "dest_lng": dest_lng
        }
    )
    return response.json()

# Get comprehensive roads
def get_roads(lat, lng, radius=5000):
    response = requests.get(
        f"{BASE_URL}/api/roads/comprehensive",
        params={
            "lat": lat,
            "lng": lng,
            "radius": radius
        }
    )
    return response.json()

# Usage
routes = get_routes(28.6139, 77.2090, 28.5244, 77.0855)
roads = get_roads(28.6139, 77.2090, 5000)

print(json.dumps(routes, indent=2))
```

### Async Usage

```python
import aiohttp
import asyncio

async def get_routes_async(origin_lat, origin_lng, dest_lat, dest_lng):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/routes/comprehensive",
            params={
                "origin_lat": origin_lat,
                "origin_lng": origin_lng,
                "dest_lat": dest_lat,
                "dest_lng": dest_lng
            }
        ) as response:
            return await response.json()

# Usage
routes = asyncio.run(get_routes_async(28.6139, 77.2090, 28.5244, 77.0855))
```

### Using the Service Class Directly

```python
from backend.routes_roads_service import init_routes_service
import asyncio

async def main():
    # Initialize service
    service = init_routes_service()
    
    # Get comprehensive routes
    origin = (28.6139, 77.2090)
    destination = (28.5244, 77.0855)
    
    routes = await service.get_comprehensive_routes(origin, destination)
    
    print(f"Google Maps routes: {len(routes['google_maps']['routes'])}")
    print(f"OSM roads: {len(routes['osm_roads'])}")
    print(f"AI analysis available: {bool(routes['openai_analysis'])}")
    
    # Get comprehensive roads
    roads = await service.get_comprehensive_roads(28.6139, 77.2090, 5000)
    
    for road in roads[:3]:
        print(f"Road: {road['name']} - {road['surface']}")

asyncio.run(main())
```

---

## 🌐 JavaScript Integration

### Vanilla JavaScript

```javascript
// Helper function for API calls
async function callAPI(endpoint, params = {}) {
    const url = new URL(`http://localhost:8000${endpoint}`);
    Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
    });
    
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
}

// Get routes
async function getRoutes(originLat, originLng, destLat, destLng) {
    return callAPI('/api/routes/comprehensive', {
        origin_lat: originLat,
        origin_lng: originLng,
        dest_lat: destLat,
        dest_lng: destLng
    });
}

// Get roads
async function getRoads(lat, lng, radius = 5000) {
    return callAPI('/api/roads/comprehensive', {
        lat: lat,
        lng: lng,
        radius: radius
    });
}

// Usage
async function main() {
    try {
        const routes = await getRoutes(28.6139, 77.2090, 28.5244, 77.0855);
        console.log('Routes:', routes);
        
        const roads = await getRoads(28.6139, 77.2090, 5000);
        console.log('Roads:', roads);
    } catch (error) {
        console.error('Error:', error);
    }
}

main();
```

### Axios

```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000'
});

// Get routes with Axios
async function getRoutes(originLat, originLng, destLat, destLng) {
    try {
        const response = await api.get('/api/routes/comprehensive', {
            params: {
                origin_lat: originLat,
                origin_lng: originLng,
                dest_lat: destLat,
                dest_lng: destLng
            }
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching routes:', error);
        throw error;
    }
}

// Usage
const routes = await getRoutes(28.6139, 77.2090, 28.5244, 77.0855);
console.log(routes);
```

### React Integration

```javascript
import React, { useState, useEffect } from 'react';

export function RoutesComponent() {
    const [routes, setRoutes] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    async function fetchRoutes() {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(
                '/api/routes/comprehensive?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855'
            );
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            setRoutes(data);
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    }
    
    return (
        <div>
            <button onClick={fetchRoutes}>Get Routes</button>
            
            {loading && <p>Loading...</p>}
            {error && <p style={{ color: 'red' }}>Error: {error}</p>}
            
            {routes && (
                <div>
                    <h3>Routes Found</h3>
                    <pre>{JSON.stringify(routes, null, 2)}</pre>
                </div>
            )}
        </div>
    );
}
```

### Vue Integration

```javascript
<template>
    <div class="routes-component">
        <button @click="fetchRoutes">Get Routes</button>
        
        <div v-if="loading">Loading...</div>
        <div v-if="error" style="color: red;">Error: {{ error }}</div>
        
        <div v-if="routes">
            <h3>Routes Found</h3>
            <pre>{{ JSON.stringify(routes, null, 2) }}</pre>
        </div>
    </div>
</template>

<script>
import { ref } from 'vue';

export default {
    setup() {
        const routes = ref(null);
        const loading = ref(false);
        const error = ref(null);
        
        const fetchRoutes = async () => {
            loading.value = true;
            error.value = null;
            
            try {
                const response = await fetch(
                    '/api/routes/comprehensive?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855'
                );
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                routes.value = await response.json();
            } catch (err) {
                error.value = err.message;
            } finally {
                loading.value = false;
            }
        };
        
        return { routes, loading, error, fetchRoutes };
    }
};
</script>
```

---

## 🗺️ Map Visualization Integration

### Leaflet Integration

```javascript
// Initialize map
const map = L.map('map').setView([28.6139, 77.2090], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Fetch and display routes
async function displayRoutes() {
    const routes = await fetch('/api/routes/comprehensive?...');
    const data = await routes.json();
    
    // Plot origin and destination
    L.circleMarker([28.6139, 77.2090], {
        radius: 8,
        fillColor: '#48bb78',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(map).bindPopup('Origin');
    
    L.circleMarker([28.5244, 77.0855], {
        radius: 8,
        fillColor: '#f56565',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(map).bindPopup('Destination');
    
    // Plot route
    if (data.routes.google_maps?.routes?.[0]?.overview_polyline?.points) {
        const encoded = data.routes.google_maps.routes[0].overview_polyline.points;
        const decoded = L.PolylineUtil.decode(encoded);
        
        L.polyline(decoded, {
            color: '#667eea',
            weight: 3,
            opacity: 0.8
        }).addTo(map);
    }
}
```

### Google Maps Integration

```javascript
// Initialize map
const map = new google.maps.Map(document.getElementById('map'), {
    zoom: 12,
    center: { lat: 28.6139, lng: 77.2090 }
});

// Fetch and display routes
async function displayRoutesGoogleMaps() {
    const response = await fetch('/api/routes/comprehensive?...');
    const data = await response.json();
    
    // Add origin marker
    new google.maps.Marker({
        position: { lat: 28.6139, lng: 77.2090 },
        map: map,
        title: 'Origin'
    });
    
    // Add destination marker
    new google.maps.Marker({
        position: { lat: 28.5244, lng: 77.0855 },
        map: map,
        title: 'Destination'
    });
    
    // Draw route using Google Maps polyline
    if (data.routes.google_maps?.routes) {
        const route = data.routes.google_maps.routes[0];
        const path = [];
        
        route.legs.forEach(leg => {
            leg.steps.forEach(step => {
                const points = google.maps.geometry.encoding
                    .decodePath(step.polyline.points);
                path.push(...points);
            });
        });
        
        new google.maps.Polyline({
            path: path,
            geodesic: true,
            strokeColor: '#667eea',
            strokeOpacity: 0.8,
            strokeWeight: 3,
            map: map
        });
    }
}
```

---

## 🔗 CORS Considerations

### Development Setup

For local development with CORS issues:

```javascript
// If backend is at http://localhost:8000
const API_BASE = 'http://localhost:8000';

// Or use proxy in development
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

### Production Setup

For production, ensure CORS headers are configured in server.py:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📝 Common Use Cases

### Use Case 1: Daily Commute Planning

```python
def plan_daily_commute():
    # Home to office
    home = (28.6139, 77.2090)
    office = (28.5244, 77.0855)
    
    routes = requests.get(
        "http://localhost:8000/api/routes/comprehensive",
        params={
            "origin_lat": home[0],
            "origin_lng": home[1],
            "dest_lat": office[0],
            "dest_lng": office[1]
        }
    ).json()
    
    # Find fastest route
    fastest = min(
        routes['routes']['google_maps']['routes'],
        key=lambda r: r['legs'][0]['duration']['value']
    )
    
    return {
        "distance": fastest['legs'][0]['distance']['text'],
        "duration": fastest['legs'][0]['duration']['text'],
        "traffic_duration": fastest['legs'][0].get('duration_in_traffic', {}).get('text')
    }
```

### Use Case 2: City Infrastructure Analysis

```python
def analyze_city_roads(city_center, radius_km=10):
    roads = requests.get(
        "http://localhost:8000/api/roads/comprehensive",
        params={
            "lat": city_center[0],
            "lng": city_center[1],
            "radius": radius_km * 1000
        }
    ).json()
    
    # Group by road type
    by_type = {}
    for road in roads['roads']:
        road_type = road['type']
        if road_type not in by_type:
            by_type[road_type] = []
        by_type[road_type].append(road)
    
    # Calculate statistics
    stats = {
        road_type: {
            "count": len(roads_list),
            "avg_condition": sum(r['condition'] == 'good' for r in roads_list) / len(roads_list),
            "total_length_km": sum(r['length'] for r in roads_list) / 1000
        }
        for road_type, roads_list in by_type.items()
    }
    
    return stats
```

### Use Case 3: Multi-Stop Delivery Route

```python
def optimize_delivery_route(stops):
    # stops = [(lat1, lng1), (lat2, lng2), (lat3, lng3), ...]
    waypoints = ','.join([f"{lat},{lng}" for lat, lng in stops])
    
    optimized = requests.get(
        "http://localhost:8000/api/routes/optimization",
        params={"waypoints": waypoints}
    ).json()
    
    total_distance = optimized['total_distance_km']
    total_time = optimized['total_duration_min']
    
    return {
        "total_distance": f"{total_distance:.2f} km",
        "total_time": f"{total_time:.0f} minutes",
        "segments": optimized['segments']
    }
```

### Use Case 4: Safety Assessment

```python
def check_route_safety(origin, destination):
    safety = requests.post(
        "http://localhost:8000/api/routes/safety-assessment",
        params={
            "origin_lat": origin[0],
            "origin_lng": origin[1],
            "dest_lat": destination[0],
            "dest_lng": destination[1]
        }
    ).json()
    
    return {
        "score": safety['safety_score'],
        "risk_level": safety['risk_level'],
        "recommendations": safety['recommendations']
    }
```

---

## 🧪 Testing Your Integration

### Test Script

```python
import requests
import time

BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    """Test all API endpoints"""
    
    test_cases = [
        {
            "name": "Comprehensive Routes",
            "endpoint": "/api/routes/comprehensive",
            "params": {
                "origin_lat": 28.6139,
                "origin_lng": 77.2090,
                "dest_lat": 28.5244,
                "dest_lng": 77.0855
            }
        },
        {
            "name": "Comprehensive Roads",
            "endpoint": "/api/roads/comprehensive",
            "params": {
                "lat": 28.6139,
                "lng": 77.2090,
                "radius": 5000
            }
        },
        {
            "name": "Traffic Analysis",
            "endpoint": "/api/routes/traffic-analysis",
            "params": {
                "origin_lat": 28.6139,
                "origin_lng": 77.2090,
                "dest_lat": 28.5244,
                "dest_lng": 77.0855
            }
        }
    ]
    
    for test in test_cases:
        print(f"\n🧪 Testing: {test['name']}")
        print(f"   Endpoint: {test['endpoint']}")
        
        start = time.time()
        response = requests.get(f"{BASE_URL}{test['endpoint']}", params=test['params'])
        elapsed = time.time() - start
        
        print(f"   Status: {response.status_code}")
        print(f"   Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success")
            print(f"   Response keys: {list(data.keys())}")
        else:
            print(f"   ❌ Failed: {response.text}")

if __name__ == "__main__":
    test_api_endpoints()
```

---

## 🔍 Debugging

### Enable Detailed Logging

```python
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Make request with logging
logger.debug("Fetching routes from API...")
response = requests.get('http://localhost:8000/api/routes/comprehensive?...')
logger.debug(f"Response status: {response.status_code}")
logger.debug(f"Response body: {response.text}")
```

### Check Network Issues

```bash
# Test connectivity
curl -v http://localhost:8000/api/routes/comprehensive?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855

# Check response headers
curl -i http://localhost:8000/api/routes/comprehensive?...

# Test with timeout
curl --max-time 10 http://localhost:8000/api/routes/comprehensive?...
```

---

## 📊 Performance Tips

1. **Cache Results**: Cache API responses to reduce load
2. **Batch Requests**: Use optimization endpoint for multiple stops
3. **Filter on Client**: Retrieve once, filter locally
4. **Lazy Load**: Load data as needed
5. **Compress**: Enable gzip compression
6. **CDN**: Cache static map tiles

---

## 🎯 Next Steps

1. Choose your framework (React, Vue, Angular, etc.)
2. Follow the integration examples above
3. Test with the provided demo page
4. Deploy to production
5. Monitor performance and API usage

---

**Happy integrating! 🚀**
