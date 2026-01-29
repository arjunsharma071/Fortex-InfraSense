# Routes & Roads Tracing - Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Verify Service Files

Check that these files exist:
- ✅ `backend/routes_roads_service.py` - Main service implementation
- ✅ `backend/server.py` - API endpoints (updated)
- ✅ `frontend/routes-roads-demo.html` - Interactive demo
- ✅ `backend/test_routes_service.py` - Test suite

### 2. Set API Keys

Add these to your `.env` file or system environment variables:

```bash
# Required for Google Maps
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Required for OpenAI GPT-4
OPENAI_API_KEY=your_openai_api_key

# Required for Grok
GROK_API_KEY=your_grok_api_key

# Optional: OpenStreetMap (public API, no key needed)
OVERPASS_API_URL=https://overpass-api.de/api/interpreter
```

### 3. Test the Service

```bash
# Run the test suite
cd backend
python test_routes_service.py
```

Expected output:
```
============================================================
TESTING GOOGLE MAPS SERVICE
============================================================
✅ Google Maps Service: ALL TESTS PASSED

✅ OpenStreetMap Service: ALL TESTS PASSED
✅ OpenAI Service: ALL TESTS PASSED
✅ Grok Service: ALL TESTS PASSED
✅ Comprehensive Service: ALL TESTS PASSED

============================================================
TEST SUMMARY
============================================================
✅ Google Maps API: WORKING
✅ OpenStreetMap API: WORKING
✅ OpenAI GPT-4: WORKING
✅ Grok API: WORKING
✅ Comprehensive Service: WORKING
```

### 4. Start the Server

```bash
# From project root
python -m uvicorn foss01-main.backend.server:app --reload --host 0.0.0.0 --port 8000
```

Or use the existing run script:
```bash
./run.sh
```

### 5. Access the Demo

Open your browser:
```
http://localhost:8000/routes-roads-demo.html
```

---

## 🚀 Quick API Calls

### Test Routes Endpoint

```bash
curl -X GET "http://localhost:8000/api/routes/comprehensive?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855"
```

### Test Roads Endpoint

```bash
curl -X GET "http://localhost:8000/api/roads/comprehensive?lat=28.6139&lng=77.2090&radius=5000"
```

### Test Traffic Analysis

```bash
curl -X GET "http://localhost:8000/api/routes/traffic-analysis?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855"
```

### Test Route Tracing

```bash
curl -X GET "http://localhost:8000/api/routes/trace?origin=Connaught%20Place,%20Delhi&destination=India%20Gate,%20Delhi"
```

---

## 📊 What You Get

### 1. **Google Maps Integration**
- Real-time directions
- Traffic-aware travel times
- Multiple route options
- Turn-by-turn directions
- Road surface information

### 2. **OpenStreetMap Integration**
- Complete road networks
- Detailed road properties
- Surface types (asphalt, concrete, etc.)
- Lane counts
- Speed limits
- Street lighting info

### 3. **OpenAI GPT-4 Integration**
- Road condition analysis
- Route efficiency scoring
- Traffic pattern insights
- Safety recommendations
- Infrastructure assessment

### 4. **Xai Grok Integration**
- Economic impact analysis
- Environmental impact assessment
- Social implications
- Real-world infrastructure insights
- Policy recommendations

---

## 🎯 Common Use Cases

### Case 1: Route Planning with Traffic
```bash
GET /api/routes/comprehensive?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855
```

Returns:
- Multiple route options from Google Maps
- Road details from OpenStreetMap
- Traffic conditions
- AI efficiency analysis

### Case 2: Road Network Analysis
```bash
GET /api/roads/comprehensive?lat=28.6139&lng=77.2090&radius=5000
```

Returns:
- All roads in 5km radius
- Surface types and conditions
- Traffic levels
- AI-based condition assessment

### Case 3: Traffic Prediction
```bash
GET /api/routes/traffic-analysis?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855
```

Returns:
- Current traffic conditions
- Predicted congestion levels
- Alternative routes
- Time savings estimates

### Case 4: Multi-Stop Route
```bash
GET /api/routes/optimization?waypoints=28.6139,77.2090,28.5244,77.0855,28.6500,77.2500
```

Returns:
- Optimized route order
- Total distance and time
- Individual segment analysis

### Case 5: Safety Assessment
```bash
POST /api/routes/safety-assessment?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855
```

Returns:
- Safety score (0-10)
- Risk assessment
- Detailed recommendations
- Infrastructure concerns

---

## 🔧 Advanced Configuration

### Custom Bounding Boxes

For road analysis with custom areas:
```bash
# Get roads in specific bounding box
GET /api/roads/detailed?lat=28.6139&lng=77.2090&road_type=primary
```

### Filter by Road Type

```bash
# Primary roads only
GET /api/roads/detailed?lat=28.6139&lng=77.2090&road_type=primary

# Secondary roads
GET /api/roads/detailed?lat=28.6139&lng=77.2090&road_type=secondary

# All roads
GET /api/roads/detailed?lat=28.6139&lng=77.2090&road_type=all
```

### Adjust Search Radius

```bash
# 1km radius
GET /api/roads/comprehensive?lat=28.6139&lng=77.2090&radius=1000

# 10km radius
GET /api/roads/comprehensive?lat=28.6139&lng=77.2090&radius=10000
```

---

## 📱 Frontend Integration

### Python with Requests

```python
import requests

# Get comprehensive routes
response = requests.get(
    'http://localhost:8000/api/routes/comprehensive',
    params={
        'origin_lat': 28.6139,
        'origin_lng': 77.2090,
        'dest_lat': 28.5244,
        'dest_lng': 77.0855
    }
)

routes = response.json()
print(f"Found {len(routes['routes'])} routes")
```

### JavaScript with Fetch

```javascript
async function getRoutes(originLat, originLng, destLat, destLng) {
    const params = new URLSearchParams({
        origin_lat: originLat,
        origin_lng: originLng,
        dest_lat: destLat,
        dest_lng: destLng
    });
    
    const response = await fetch(`/api/routes/comprehensive?${params}`);
    const data = await response.json();
    return data;
}

const routes = await getRoutes(28.6139, 77.2090, 28.5244, 77.0855);
console.log(routes);
```

### React Component Example

```javascript
import { useState, useEffect } from 'react';

export function RouteTracer() {
    const [routes, setRoutes] = useState(null);
    const [loading, setLoading] = useState(false);
    
    async function traceRoute() {
        setLoading(true);
        try {
            const response = await fetch('/api/routes/comprehensive?origin_lat=28.6139&origin_lng=77.2090&dest_lat=28.5244&dest_lng=77.0855');
            const data = await response.json();
            setRoutes(data);
        } finally {
            setLoading(false);
        }
    }
    
    return (
        <div>
            <button onClick={traceRoute}>Trace Route</button>
            {loading && <p>Loading...</p>}
            {routes && <pre>{JSON.stringify(routes, null, 2)}</pre>}
        </div>
    );
}
```

---

## 🐛 Troubleshooting

### Issue: API returns "API key not configured"

**Solution:**
1. Check if environment variables are set
2. Run: `echo $GOOGLE_MAPS_API_KEY`
3. If empty, set: `export GOOGLE_MAPS_API_KEY=your_key`
4. Restart server

### Issue: Routes endpoint returns empty results

**Solution:**
1. Verify coordinates are valid
2. Check internet connectivity
3. Verify API key has correct permissions
4. Check quota limits on Google Maps API

### Issue: OpenStreetMap returns no roads

**Solution:**
1. Increase search radius
2. Check if area has OpenStreetMap coverage
3. Try different road types
4. Verify coordinates

### Issue: AI analysis returns generic text

**Solution:**
1. Check OpenAI API key
2. Verify API credit/quota
3. Check if GPT-4 model is available
4. Review OpenAI API status

---

## 📈 Performance Tips

### 1. Cache Results
```javascript
const routeCache = new Map();

async function getRoutesCached(origin, dest) {
    const key = `${origin}-${dest}`;
    if (routeCache.has(key)) {
        return routeCache.get(key);
    }
    
    const data = await fetch(`/api/routes/comprehensive?...`);
    routeCache.set(key, data);
    return data;
}
```

### 2. Batch Requests
```bash
# Instead of multiple calls, use optimization endpoint
GET /api/routes/optimization?waypoints=loc1,loc2,loc3,loc4
```

### 3. Filter on Frontend
```javascript
// Get roads once, filter client-side
const allRoads = await fetch('/api/roads/comprehensive?...');
const primaryOnly = allRoads.filter(r => r.type === 'primary');
```

---

## 📚 Documentation Files

- 📖 [Full API Documentation](ROUTES_ROADS_API_DOCUMENTATION.md)
- 🧪 [Test Suite](backend/test_routes_service.py)
- 🖥️ [Service Implementation](backend/routes_roads_service.py)
- 🎨 [Demo HTML](frontend/routes-roads-demo.html)
- 🔌 [Server Endpoints](backend/server.py)

---

## ✅ Verification Checklist

- [ ] API keys configured in environment
- [ ] Test suite passes all tests
- [ ] Server starts without errors
- [ ] Demo page loads at `http://localhost:8000/routes-roads-demo.html`
- [ ] Can retrieve routes for test coordinates
- [ ] Can retrieve roads for test location
- [ ] Traffic analysis returns real data
- [ ] No "N/A" values in responses
- [ ] All 4 APIs integrated and functional

---

## 🎓 Next Steps

1. **Customize coordinates** - Use your own origin/destination
2. **Integrate with frontend** - Add route visualization
3. **Optimize routes** - Use multi-stop endpoint
4. **Analyze safety** - Get route safety assessments
5. **Plan networks** - Analyze road infrastructure

---

## 📞 Support

For detailed information about each API:
- [Google Maps Documentation](https://developers.google.com/maps)
- [OpenStreetMap Wiki](https://wiki.openstreetmap.org)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [Grok API Documentation](https://grok.x.com/api)

---

## 🎉 You're Ready!

The Routes & Roads Tracing API is now fully configured and ready to use. Start with the demo page and explore the endpoints!
