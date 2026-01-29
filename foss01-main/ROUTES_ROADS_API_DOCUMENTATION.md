# Routes & Roads Tracing API Documentation

## Overview

The InfraSense Routes & Roads Tracing API provides comprehensive multi-source route and road analysis using:

- **Google Maps API** - Real-time directions, traffic, and road data
- **OpenStreetMap/Overpass API** - Detailed road networks with geometry and properties
- **OpenAI GPT-4** - Intelligent analysis of road conditions and route efficiency
- **Xai Grok API** - Infrastructure impact and real-world implications analysis

All endpoints return **real data with NO N/A values** through intelligent fallback mechanisms.

---

## API Endpoints

### 1. Get Comprehensive Routes

**Endpoint:** `GET /api/routes/comprehensive`

**Description:** Retrieve complete route data from all sources - Google Maps directions, OpenStreetMap roads, and AI analysis.

**Query Parameters:**
```
origin_lat (float) - Origin latitude
origin_lng (float) - Origin longitude
dest_lat (float) - Destination latitude
dest_lng (float) - Destination longitude
```

**Example Request:**
```bash
GET /api/routes/comprehensive?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855
```

**Response:**
```json
{
  "status": "success",
  "routes": {
    "google_maps": {
      "routes": [
        {
          "legs": [
            {
              "distance": {"text": "15 km", "value": 15000},
              "duration": {"text": "25 mins", "value": 1500},
              "duration_in_traffic": {"text": "35 mins", "value": 2100},
              "steps": [...]
            }
          ],
          "overview_polyline": {"points": "..."}
        }
      ]
    },
    "osm_roads": [
      {
        "name": "Rajpath",
        "surface": "asphalt",
        "lanes": 4,
        "speed_limit": 60,
        "length": 15000,
        "coordinates": [[28.6139, 77.2090], ...]
      }
    ],
    "openai_analysis": {
      "route_efficiency": 8.5,
      "recommendations": [
        "Route is efficient with good road conditions",
        "Peak traffic 8-10 AM and 5-7 PM",
        "Prefer morning travel for faster commute"
      ]
    },
    "grok_insights": {
      "economic_impact": "Medium - standard urban route",
      "environmental_impact": "Moderate - mixed traffic",
      "social_impact": "High - connects major commercial areas"
    }
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

---

### 2. Get Comprehensive Roads

**Endpoint:** `GET /api/roads/comprehensive`

**Description:** Get all road network data for a specific location within a radius.

**Query Parameters:**
```
lat (float) - Center latitude
lng (float) - Center longitude
radius (int) - Search radius in meters (default: 5000)
```

**Example Request:**
```bash
GET /api/roads/comprehensive?lat=28.6139&lng=77.2090&radius=5000
```

**Response:**
```json
{
  "status": "success",
  "location": {"lat": 28.6139, "lng": 77.2090},
  "radius_meters": 5000,
  "roads": [
    {
      "id": "way_12345",
      "name": "MG Road",
      "type": "primary",
      "surface": "asphalt",
      "lanes": 4,
      "speed_limit": 60,
      "length": 8500.5,
      "condition": "good",
      "traffic": "moderate",
      "coordinates": [[28.6139, 77.2090], [28.6145, 77.2095], ...],
      "ai_analysis": {
        "status": "Good condition",
        "severity": "Low",
        "assessment": "Well-maintained primary road"
      },
      "grok_insights": {
        "economic_impact": "High - major commercial corridor",
        "recommendations": ["Regular maintenance recommended"]
      }
    }
  ],
  "timestamp": "2024-01-15T10:30:00"
}
```

---

### 3. Trace Route (With Geocoding)

**Endpoint:** `GET /api/routes/trace`

**Description:** Trace a route using address names instead of coordinates. Automatically geocodes addresses.

**Query Parameters:**
```
origin (string) - Origin address (e.g., "Connaught Place, Delhi")
destination (string) - Destination address (e.g., "India Gate, Delhi")
```

**Example Request:**
```bash
GET /api/routes/trace?origin=Connaught%20Place,%20Delhi&destination=India%20Gate,%20Delhi
```

**Response:**
```json
{
  "status": "success",
  "origin": {
    "address": "Connaught Place, Delhi",
    "lat": 28.6139,
    "lng": 77.2090
  },
  "destination": {
    "address": "India Gate, Delhi",
    "lat": 28.5244,
    "lng": 77.0855
  },
  "routes": {...},
  "timestamp": "2024-01-15T10:30:00"
}
```

---

### 4. Get Detailed Roads

**Endpoint:** `GET /api/roads/detailed`

**Description:** Get detailed road information filtered by road type with comprehensive analysis.

**Query Parameters:**
```
lat (float) - Center latitude
lng (float) - Center longitude
road_type (string) - Type filter: all, primary, secondary, tertiary, residential, motorway
```

**Example Request:**
```bash
GET /api/roads/detailed?lat=28.6139&lng=77.2090&road_type=primary
```

**Response:**
```json
{
  "status": "success",
  "location": {"lat": 28.6139, "lng": 77.2090},
  "road_type_filter": "primary",
  "total_found": 15,
  "roads": [
    {
      "name": "Rajpath",
      "type": "primary",
      "surface": "asphalt",
      "lanes": 4,
      "speed_limit": 60,
      "lit": "yes",
      "cycling": "yes",
      "sidewalk": "both",
      "detailed_analysis": {
        "status": "Excellent",
        "severity": "None",
        "assessment": "Well-maintained with modern infrastructure"
      }
    }
  ],
  "timestamp": "2024-01-15T10:30:00"
}
```

---

### 5. Traffic Analysis

**Endpoint:** `GET /api/routes/traffic-analysis`

**Description:** Analyze traffic patterns and congestion predictions for a route.

**Query Parameters:**
```
origin_lat (float) - Origin latitude
origin_lng (float) - Origin longitude
dest_lat (float) - Destination latitude
dest_lng (float) - Destination longitude
```

**Example Request:**
```bash
GET /api/routes/traffic-analysis?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855
```

**Response:**
```json
{
  "status": "success",
  "routes": [
    {
      "route_number": 1,
      "distance": "15 km",
      "duration": "25 mins",
      "duration_in_traffic": "35 mins",
      "polyline": "..."
    }
  ],
  "timestamp": "2024-01-15T10:30:00"
}
```

---

### 6. Route Optimization (Multi-Stop)

**Endpoint:** `GET /api/routes/optimization`

**Description:** Optimize a multi-stop route for shortest distance/time.

**Query Parameters:**
```
waypoints (string) - Comma-separated lat,lng pairs
                    Format: lat1,lng1,lat2,lng2,lat3,lng3,...
```

**Example Request:**
```bash
GET /api/routes/optimization?waypoints=28.6139,77.2090,28.5244,77.0855,28.6500,77.2500
```

**Response:**
```json
{
  "status": "success",
  "waypoints": 3,
  "segments": [
    {
      "from": [28.6139, 77.2090],
      "to": [28.5244, 77.0855],
      "distance_m": 15000,
      "duration_s": 1500,
      "steps": 45
    }
  ],
  "total_distance_km": 45.5,
  "total_duration_min": 65,
  "timestamp": "2024-01-15T10:30:00"
}
```

---

### 7. Safety Assessment

**Endpoint:** `POST /api/routes/safety-assessment`

**Description:** Assess safety of a route using AI and real-world data analysis.

**Query Parameters:**
```
origin_lat (float) - Origin latitude
origin_lng (float) - Origin longitude
dest_lat (float) - Destination latitude
dest_lng (float) - Destination longitude
```

**Example Request:**
```bash
POST /api/routes/safety-assessment?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855
```

**Response:**
```json
{
  "status": "success",
  "safety_score": 8.5,
  "risk_level": "low",
  "recommendations": [
    "Route is generally safe with good road conditions",
    "High traffic during peak hours - consider off-peak travel",
    "Adequate street lighting throughout route",
    "No major accident hotspots detected"
  ],
  "analysis": {...},
  "grok_insights": {...},
  "timestamp": "2024-01-15T10:30:00"
}
```

---

## Data Types

### RoadSegment

```json
{
  "id": "string",                    // Unique road identifier
  "name": "string",                  // Road name
  "type": "string",                  // primary, secondary, tertiary, residential, motorway
  "surface": "string",               // asphalt, concrete, gravel, dirt, etc.
  "lanes": "integer",                // Number of lanes
  "speed_limit": "integer",          // Speed limit in km/h
  "length": "float",                 // Length in meters
  "condition": "string",             // good, fair, poor
  "traffic": "string",               // light, moderate, heavy
  "coordinates": "[[lat, lng], ...]",// Road geometry
  "ai_analysis": {
    "status": "string",
    "severity": "string",
    "assessment": "string"
  },
  "grok_insights": {
    "economic_impact": "string",
    "environmental_impact": "string",
    "social_impact": "string"
  }
}
```

### Route

```json
{
  "legs": [
    {
      "distance": {"text": "string", "value": "integer"},
      "duration": {"text": "string", "value": "integer"},
      "duration_in_traffic": {"text": "string", "value": "integer"},
      "steps": ["array of turn-by-turn directions"]
    }
  ],
  "overview_polyline": {"points": "string"}
}
```

---

## API Integration Details

### Google Maps API
- **Services Used:**
  - Directions API - Route calculation and turn-by-turn directions
  - Distance Matrix API - Multiple route analysis
  - Nearby Search - Finding roads and intersections
  - Geocoding API - Address to coordinates conversion
  - Roads API - Surface and quality information

- **Real Data Provided:**
  - Accurate distances and durations
  - Traffic-aware travel times
  - Multiple route alternatives
  - Turn-by-turn directions
  - Real-time traffic conditions

### OpenStreetMap/Overpass API
- **Services Used:**
  - Overpass QL queries for detailed road networks
  - Way geometry and properties
  - Road classification and tags
  - Surface types and conditions
  - Speed limits and lane counts

- **Real Data Provided:**
  - Complete road networks
  - Detailed road properties
  - Surface and material information
  - Infrastructure tags (lighting, cycling, sidewalks)
  - Comprehensive geometries

### OpenAI GPT-4
- **Analysis Provided:**
  - Road condition assessments
  - Route efficiency scoring
  - Traffic pattern analysis
  - Safety recommendations
  - Infrastructure maintenance insights

- **Fallback Data:**
  - Pre-trained assessments for common road types
  - Historical pattern analysis
  - Industry standard recommendations

### Xai Grok API
- **Analysis Provided:**
  - Economic impact assessment
  - Environmental impact analysis
  - Social implications
  - Real-world infrastructure insights
  - Policy recommendations

- **Fallback Data:**
  - Standard impact categories
  - Common infrastructure patterns
  - Best practice recommendations

---

## Error Handling

All endpoints include intelligent fallback mechanisms to ensure **NO N/A VALUES** are returned:

```json
{
  "status": "partial",
  "message": "Some APIs unavailable, using fallback data",
  "routes": {...},
  "fallback_sources": ["Google Maps", "OpenStreetMap"],
  "timestamp": "2024-01-15T10:30:00"
}
```

---

## Rate Limits

- **Google Maps API**: As per your API plan
- **OpenStreetMap Overpass**: 10 requests per minute per IP
- **OpenAI API**: As per your subscription plan
- **Grok API**: As per your API plan

---

## Environment Variables Required

```bash
# Google Maps
GOOGLE_MAPS_API_KEY=your_api_key

# OpenAI
OPENAI_API_KEY=your_api_key

# Grok
GROK_API_KEY=your_api_key

# Optional: Overpass API (public, no key needed)
OVERPASS_API_URL=https://overpass-api.de/api/interpreter
```

---

## Example Usage

### Python Client

```python
import httpx
import asyncio

async def get_routes():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/routes/comprehensive",
            params={
                "origin_lat": 28.6139,
                "origin_lng": 77.2090,
                "dest_lat": 28.5244,
                "dest_lng": 77.0855
            }
        )
        return response.json()

asyncio.run(get_routes())
```

### JavaScript/Frontend

```javascript
async function getRoutes() {
    const params = new URLSearchParams({
        origin_lat: 28.6139,
        origin_lng: 77.2090,
        dest_lat: 28.5244,
        dest_lng: 77.0855
    });
    
    const response = await fetch(`/api/routes/comprehensive?${params}`);
    const data = await response.json();
    console.log(data);
}

getRoutes();
```

### cURL

```bash
curl -X GET "http://localhost:8000/api/routes/comprehensive?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855"
```

---

## Testing

Run the comprehensive test suite:

```bash
python backend/test_routes_service.py
```

This will test:
- ✅ Google Maps Service
- ✅ OpenStreetMap Service
- ✅ OpenAI Analysis Service
- ✅ Grok Analysis Service
- ✅ Comprehensive Service

---

## Frontend Demo

Access the interactive demo at:
```
http://localhost:8000/routes-roads-demo.html
```

Features:
- 🗺️ Interactive Leaflet map
- 📍 Route planning with multiple sources
- 🛣️ Road network visualization
- 🚗 Traffic analysis
- 📊 Detailed road information
- ✏️ Region drawing for filtering
- 🤖 AI-powered analysis display

---

## Support

For issues or questions:
1. Check API key configuration
2. Verify network connectivity
3. Review error messages in server logs
4. Check API status pages for outages
5. Review fallback data mechanisms

---

## Version History

- **v1.0** (2024-01-15) - Initial release with 4 API integrations
  - Google Maps API for directions and roads
  - OpenStreetMap Overpass API for detailed networks
  - OpenAI GPT-4 for intelligent analysis
  - Xai Grok for infrastructure impact assessment
  - Comprehensive fallback mechanisms
  - No N/A values in responses

---

## License

InfraSense Routes & Roads API is part of the FOSS01 infrastructure analysis project.
