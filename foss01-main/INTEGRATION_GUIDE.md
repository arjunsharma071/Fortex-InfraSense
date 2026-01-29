# Integration Guide - Advanced Analysis Dashboard

## Quick Start

### Step 1: Update your HTML landing page (index.html)

Add a link to the analysis page:

```html
<!-- In your navigation or features section -->
<a href="frontend/analysis-page.html?area=default" class="btn btn-primary" target="_blank">
    <i class="fas fa-chart-line"></i> Advanced Analysis
</a>

<!-- Or in a demo section -->
<div class="analysis-link">
    <h3>Infrastructure Analysis</h3>
    <p>View detailed traffic frequency analysis and intervention recommendations</p>
    <a href="frontend/analysis-page.html" class="btn">Open Analysis Dashboard</a>
</div>
```

### Step 2: Update server.py to add API endpoint

```python
# backend/server.py

from flask import Flask, request, jsonify
from backend.advanced_analysis import get_analysis_engine

app = Flask(__name__)

# Initialize analysis engine (with database connection if available)
analysis_engine = get_analysis_engine(db_connection=None)  # Pass DB connection if you have one

# ========== NEW ENDPOINT ==========
@app.route('/api/analysis/<area_id>', methods=['GET'])
def get_area_analysis(area_id):
    """
    Advanced analysis endpoint
    
    Query params:
    - days: int (7, 30, 90, 365) - Default: 30
    
    Returns: Detailed road analysis with frequency-based recommendations
    """
    try:
        days = request.args.get('days', 30, type=int)
        
        # Validate days parameter
        if days not in [7, 30, 90, 365]:
            days = 30
        
        # Run analysis
        result = analysis_engine.analyze_area(area_id, days)
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'roads': [],
            'area_insights': {},
            'summary': {}
        }), 500


@app.route('/api/analysis/<area_id>/road/<road_id>', methods=['GET'])
def get_road_analysis(area_id, road_id):
    """
    Detailed analysis for a single road
    """
    try:
        days = request.args.get('days', 30, type=int)
        result = analysis_engine.analyze_road_segment(road_id, days)
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
```

### Step 3: Verify Frontend Files

Ensure these files exist in your `frontend/` directory:

```
frontend/
├── analysis-page.html
├── analysis-script-enhanced.js      (or analysis-script.js)
└── analysis-styles-enhanced.css     (or analysis-styles.css)
```

If you have existing files, either:
- **Option A**: Replace them with the enhanced versions
- **Option B**: Rename old files and use the new ones:
  ```
  analysis-script.js → analysis-script-old.js
  analysis-styles.css → analysis-styles-old.css
  ```

### Step 4: Update HTML Script/Link References

In `analysis-page.html`, ensure correct file references:

```html
<!-- In <head> -->
<link rel="stylesheet" href="analysis-styles-enhanced.css">

<!-- At end of <body> -->
<script src="analysis-script-enhanced.js"></script>
```

Or if you're replacing the existing files:

```html
<link rel="stylesheet" href="analysis-styles.css">
<script src="analysis-script.js"></script>
```

## Features Implementation Checklist

### Core Frequency-Based Logic
- [x] Traffic frequency scoring (days/week with high congestion)
- [x] Decision matrix for intervention needs
- [x] Priority calculation algorithm
- [x] Cost estimation for interventions

### Frontend Visualization
- [x] Interactive Leaflet map with road segments
- [x] Color coding by frequency + severity
- [x] Intervention markers with type icons
- [x] Detailed road information panel
- [x] Statistics dashboard
- [x] Charts (trend, hourly patterns)
- [x] Responsive layout (desktop, tablet, mobile)

### User Interactions
- [x] Filter by road type
- [x] Filter by intervention type
- [x] Filter by priority level
- [x] Adjust frequency threshold slider
- [x] Select time range (7/30/90/365 days)
- [x] Click roads to view details
- [x] Export analysis report

### Data Analysis
- [x] Historical traffic data querying
- [x] Daily congestion calculation
- [x] Weekly pattern analysis
- [x] Peak hour identification
- [x] Trend analysis (increasing/decreasing/stable)
- [x] Hotspot identification
- [x] Implementation phasing suggestions

## Database Setup (Optional)

If you want to use real traffic data instead of sample data:

### Create traffic_history table

```sql
CREATE TABLE traffic_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    road_id VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    speed FLOAT NOT NULL,
    free_flow_speed FLOAT DEFAULT 60,
    vehicle_count INT,
    congestion FLOAT GENERATED ALWAYS AS (
        IF(free_flow_speed > 0, 
           LEAST(1, GREATEST(0, 1 - (speed / free_flow_speed))), 
           0)
    ) STORED,
    date DATE GENERATED ALWAYS AS (DATE(timestamp)) STORED,
    INDEX idx_road_timestamp (road_id, timestamp),
    INDEX idx_date (date)
);

-- Sample data (last 30 days for testing)
INSERT INTO traffic_history (road_id, timestamp, speed, free_flow_speed, vehicle_count)
VALUES 
('road_mg', '2024-01-20 08:00:00', 25, 60, 450),
('road_mg', '2024-01-20 09:00:00', 20, 60, 550),
('road_mg', '2024-01-20 17:00:00', 15, 60, 600),
-- ... more data
```

### Create roads table

```sql
CREATE TABLE roads (
    id VARCHAR(50) PRIMARY KEY,
    area_id VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(20) DEFAULT 'secondary',  -- highway, primary, secondary, tertiary, residential
    length_km FLOAT NOT NULL,
    lanes INT DEFAULT 2,
    geometry JSON,  -- GeoJSON format
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_area (area_id)
);

-- Sample roads
INSERT INTO roads (id, area_id, name, type, length_km, lanes, geometry)
VALUES 
('road_mg', 'bangalore', 'MG Road', 'primary', 8, 2, '{"type":"LineString","coordinates":[[78.44,17.35],[78.48,17.38]]}'),
('road_brigade', 'bangalore', 'Brigade Road', 'primary', 6, 2, '{"type":"LineString","coordinates":[[78.43,17.37],[78.46,17.39]]}');
```

### Update Database Connection

```python
# backend/advanced_analysis.py

import mysql.connector
from mysql.connector import Error

class DatabaseConnection:
    def __init__(self, host='localhost', user='root', password='', database='infrasense'):
        self.connection = None
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
    
    def query(self, sql, params=None):
        """Execute SELECT query and return results"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchall()
        except Error as e:
            print(f"Query error: {e}")
            return None

# In server.py
db = DatabaseConnection(
    host='localhost',
    user='root',
    password='your_password',
    database='infrasense'
)

analysis_engine = get_analysis_engine(db_connection=db)
```

## Configuration Options

### Adjust Decision Thresholds

In `backend/advanced_analysis.py`:

```python
class AdvancedAnalysisEngine:
    def __init__(self, db_connection=None):
        self.db = db_connection
        
        # Adjust these thresholds
        self.traffic_threshold = 0.7      # Congestion >= 70% counts as "high traffic day"
        self.frequency_threshold = 0.57   # ~4 days/week (0.57 = 4/7)
```

### Customize Cost Estimates

```python
self.cost_estimates = {
    'widening_per_km': 8.5,          # ₹8.5 Cr per km
    'flyover_per_km': 45.0,          # ₹45 Cr per km
    'bridge_per_km': 35.0,           # ₹35 Cr per km
    'signal_per_intersection': 0.15, # ₹15 Lakh
    'maintenance_per_km': 2.0        # ₹2 Cr per km
}
```

### Update Recommended Lanes

```python
def _get_recommended_lanes(self, road_type: str) -> int:
    recommendations = {
        'highway': 6,      # 6 lanes
        'primary': 4,      # 4 lanes
        'secondary': 3,    # 3 lanes
        'tertiary': 2,     # 2 lanes
        'residential': 2   # 2 lanes
    }
    return recommendations.get(road_type, 2)
```

## Troubleshooting

### Issue: Analysis page shows "No data available"

**Solution**: Ensure backend API is running and accessible:
```javascript
// In browser console, test:
fetch('/api/analysis/default?days=30')
    .then(r => r.json())
    .then(data => console.log(data))
```

### Issue: Map doesn't load

**Solution**: Verify Leaflet scripts and CSS are loaded:
```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

### Issue: Sample data loads but no backend data

**Solution**: Update API endpoint URL in JavaScript:
```javascript
// In analysis-script-enhanced.js, line ~80
const apiUrl = window.location.origin + `/api/analysis/${areaId}?days=${this.currentFilters.timeRange}`;
const response = await fetch(apiUrl);
```

### Issue: Charts not displaying correctly

**Solution**: Ensure Chart.js and Plotly are loaded:
```html
<script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

## Performance Optimization

### For Large Road Networks (100+ roads)

1. **Pagination**: 
   ```python
   # In analyze_area(), limit analysis to top roads by score
   analysis_results = analysis_results[:50]  # Top 50 roads
   ```

2. **Caching**:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=10)
   def analyze_area(self, area_id, days):
       # Analysis is cached for 1 hour
   ```

3. **Async Processing**:
   ```python
   from celery import Celery
   
   celery = Celery(app.name)
   
   @celery.task
   def analyze_area_async(area_id, days):
       return analysis_engine.analyze_area(area_id, days)
   ```

## Testing

### Manual Testing Steps

1. **Open analysis page**:
   - Navigate to `http://localhost:5000/frontend/analysis-page.html?area=default`

2. **Test filters**:
   - Change time range slider
   - Toggle road type checkboxes
   - Adjust frequency threshold slider
   - Click "Apply Filters"

3. **Test map interactions**:
   - Click roads to select
   - Hover over roads to see metrics
   - Switch between map layers

4. **Test data export**:
   - Click "Export Report" button
   - Verify JSON file downloaded with correct data

### Unit Tests (Python)

```python
# test_advanced_analysis.py
import unittest
from backend.advanced_analysis import AdvancedAnalysisEngine

class TestAnalysisEngine(unittest.TestCase):
    def setUp(self):
        self.engine = AdvancedAnalysisEngine()
    
    def test_frequency_scoring(self):
        """Test frequency score calculation"""
        daily_patterns = {
            f'2024-01-{i:02d}': 0.75 if i <= 22 else 0.3
            for i in range(1, 31)
        }
        high_days = sum(1 for v in daily_patterns.values() if v >= 0.7)
        frequency = high_days / len(daily_patterns)
        
        self.assertAlmostEqual(frequency, 0.73, places=2)
    
    def test_priority_calculation(self):
        """Test priority assignment logic"""
        road_analysis = {
            'traffic_patterns': {
                'frequency_score': 0.8,
                'trend': 'increasing'
            },
            'congestion_metrics': {
                'avg_congestion': 0.75,
                'max_congestion': 0.92
            }
        }
        priority = self.engine.calculate_priority(road_analysis)
        self.assertEqual(priority, 'critical')

if __name__ == '__main__':
    unittest.main()
```

## Deployment Checklist

- [ ] Backend API endpoint implemented in server.py
- [ ] Frontend files (HTML, JS, CSS) in correct location
- [ ] Database tables created (if using real data)
- [ ] Sample data loaded (if using sample data)
- [ ] File paths verified in HTML/JS
- [ ] API URLs correct (localhost vs production)
- [ ] CORS headers configured (if needed)
- [ ] Error handling tested
- [ ] Performance acceptable (< 2s load time)
- [ ] Mobile responsiveness verified
- [ ] Export functionality working

## Support & Documentation

- **Main Documentation**: [ADVANCED_ANALYSIS_GUIDE.md](ADVANCED_ANALYSIS_GUIDE.md)
- **API Reference**: See `backend/advanced_analysis.py` docstrings
- **Frontend Examples**: See `analysis-script-enhanced.js` methods

---

**Last Updated**: January 25, 2026  
**Version**: 1.0
