# config/data_sources.py
DATA_SOURCES = {
    "road_network": {
        "source": "OpenStreetMap",
        "parser": "osmnx",
        "attributes": ["highway", "lanes", "maxspeed", "surface", "width"]
    },
    "accidents": {
        "india": "https://data.gov.in/dataset/road-accidents",
        "usa": "NHTSA Fatality Analysis Reporting System",
        "europe": "European Road Safety Observatory"
    },
    "population": {
        "high_res": "WorldPop (100m resolution)",
        "growth": "Global Human Settlement Layer",
        "night_lights": "VIIRS Nighttime Lights (proxy for activity)"
    },
    "traffic": {
        "google_maps_historical": "Free tier (100 requests/day)",
        "tomtom_traffic_api": "Free developer account",
        "osm_historical_traffic": "Using Way Counts"
    }
}

# Google Maps API Configuration
GOOGLE_MAPS_API_KEY = "AIzaSyDxGgKlamItZK2-OYqzoYGJwXBTT7GTnpU"
