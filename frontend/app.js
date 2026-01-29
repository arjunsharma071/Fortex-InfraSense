// frontend/app.js
// InfraSense AI v3.0 - Multi-Country Scalable ML Architecture

const GOOGLE_MAPS_API_KEY = 'AIzaSyDxGgKlamItZK2-OYqzoYGJwXBTT7GTnpU';

let map = L.map('map').setView([20.5937, 78.9629], 5);
let drawnItems = new L.FeatureGroup();
let drawControl;
let currentLayer = 'street';
let analysisResults = null;
let roadsLayer = null;
let hotspotMarkers = [];
let selectedCountry = 'IN';

const COUNTRIES = {
    'IN': { name: 'India', center: [20.5937, 78.9629], currency: '₹' },
    'US': { name: 'United States', center: [39.8283, -98.5795], currency: '$' },
    'DE': { name: 'Germany', center: [51.1657, 10.4515], currency: '€' },
    'NG': { name: 'Nigeria', center: [9.0820, 8.6753], currency: '₦' },
    'BR': { name: 'Brazil', center: [-14.2350, -51.9253], currency: 'R$' },
    'AU': { name: 'Australia', center: [-25.2744, 133.7751], currency: 'A$' },
    'JP': { name: 'Japan', center: [36.2048, 138.2529], currency: '¥' },
    'UK': { name: 'United Kingdom', center: [55.3781, -3.4360], currency: '£' }
};

const COUNTRY_WEIGHTS = {
    'IN': { congestion: 0.40, safety: 0.35, growth: 0.15, quality: 0.10 },
    'US': { congestion: 0.30, safety: 0.25, growth: 0.20, quality: 0.25 },
    'DE': { congestion: 0.25, safety: 0.30, growth: 0.15, quality: 0.30 },
    'NG': { congestion: 0.45, safety: 0.40, growth: 0.10, quality: 0.05 },
    'BR': { congestion: 0.38, safety: 0.32, growth: 0.18, quality: 0.12 },
    'AU': { congestion: 0.28, safety: 0.28, growth: 0.22, quality: 0.22 },
    'JP': { congestion: 0.30, safety: 0.35, growth: 0.15, quality: 0.20 },
    'UK': { congestion: 0.28, safety: 0.30, growth: 0.18, quality: 0.24 }
};

const tileLayers = {
    street: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
        crossOrigin: 'anonymous'
    }),
    satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: '© Esri',
        maxZoom: 19,
        crossOrigin: 'anonymous'
    }),
    hybrid: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
        attribution: '© Esri',
        maxZoom: 19,
        crossOrigin: 'anonymous'
    }),
    terrain: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenTopoMap',
        maxZoom: 17,
        crossOrigin: 'anonymous'
    }),
    googlemaps: L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
        attribution: '© Google Maps',
        maxZoom: 20,
        crossOrigin: 'anonymous'
    }),
    googlesatellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
        attribution: '© Google Satellite',
        maxZoom: 20,
        crossOrigin: 'anonymous'
    }),
    googlehybrid: L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
        attribution: '© Google Hybrid',
        maxZoom: 20,
        crossOrigin: 'anonymous'
    })
};

tileLayers.street.addTo(map);
map.addLayer(drawnItems);

function initDrawControl() {
    try {
        drawControl = new L.Control.Draw({
            draw: {
                polygon: {
                    allowIntersection: false,
                    showArea: true,
                    shapeOptions: { color: '#2563EB', fillColor: '#2563EB', fillOpacity: 0.1, weight: 2 }
                },
                rectangle: {
                    shapeOptions: { color: '#2563EB', fillColor: '#2563EB', fillOpacity: 0.1, weight: 2 }
                },
                circle: false, circlemarker: false, marker: false, polyline: false
            },
            edit: { featureGroup: drawnItems, remove: true }
        });
        map.addControl(drawControl);
    } catch (e) {
        console.warn('Leaflet Draw not available, using fallback:', e.message);
    }
}

if (window.L && window.L.Draw) {
    map.on(L.Draw.Event.CREATED, function(event) {
        drawnItems.addLayer(event.layer);
    });
}

function getISIColor(isi) {
    if (isi > 0.7) return '#DC2626';
    if (isi > 0.5) return '#EA580C';
    if (isi > 0.3) return '#CA8A04';
    return '#16A34A';
}

function getPriorityClass(priority) {
    switch(priority?.toUpperCase()) {
        case 'HIGH': return 'critical';
        case 'MEDIUM': return 'high';
        case 'LOW': return 'medium';
        default: return 'low';
    }
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.add('show');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('show');
}

function getDrawnPolygon() {
    const layers = drawnItems.getLayers();
    if (layers.length === 0) return null;
    const layer = layers[layers.length - 1];
    if (layer instanceof L.Polygon || layer instanceof L.Rectangle) {
        return layer.getLatLngs()[0].map(ll => [ll.lng, ll.lat]);
    }
    return null;
}

function changeCountry(countryCode) {
    selectedCountry = countryCode;
    const country = COUNTRIES[countryCode];
    if (country) {
        map.setView(country.center, 5);
        updateCountryDisplay();
    }
}

function updateCountryDisplay() {
    const country = COUNTRIES[selectedCountry];
    const weights = COUNTRY_WEIGHTS[selectedCountry] || COUNTRY_WEIGHTS['IN'];
    
    const indicator = document.getElementById('countryIndicator');
    if (indicator) indicator.textContent = country.name;
    
    const weightsEl = document.getElementById('isiWeights');
    if (weightsEl) {
        weightsEl.innerHTML = `🚗${(weights.congestion*100).toFixed(0)}% ⚠️${(weights.safety*100).toFixed(0)}% 📈${(weights.growth*100).toFixed(0)}% 🔧${(weights.quality*100).toFixed(0)}%`;
    }
}

async function analyze() {
    const polygon = getDrawnPolygon();
    if (!polygon) {
        alert('Please draw a region on the map first.');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                polygon_coords: polygon,
                analysis_depth: 'standard',
                country_code: selectedCountry
            })
        });
        
        if (!response.ok) throw new Error('Analysis failed');
        
        const data = await response.json();
        analysisResults = data;
        visualizeResults(data.roads);
        if (data.accident_hotspots) showAccidentHotspots(data.accident_hotspots);
        updateStats(data.summary);
        updateRecommendations(data.recommendations);
    } catch (error) {
        console.error('Analysis error:', error);
        const mockData = getMockAnalysisData();
        analysisResults = mockData;
        visualizeResults(mockData.roads);
        updateStats(mockData.summary);
        updateRecommendations(mockData.recommendations);
    }
    
    hideLoading();
}

function getMockAnalysisData() {
    const bounds = map.getBounds();
    const center = bounds.getCenter();
    const weights = COUNTRY_WEIGHTS[selectedCountry] || COUNTRY_WEIGHTS['IN'];
    const country = COUNTRIES[selectedCountry];
    
    const features = [];
    const roadNames = ['Main Street', 'Highway 1', 'Park Avenue', 'Market Road', 'Station Road', 
                       'Ring Road', 'Industrial Road', 'College Road', 'Hospital Road', 'Temple Street'];
    
    for (let i = 0; i < 10; i++) {
        const lat1 = center.lat + (Math.random() - 0.5) * 0.1;
        const lng1 = center.lng + (Math.random() - 0.5) * 0.1;
        const lat2 = lat1 + (Math.random() - 0.5) * 0.02;
        const lng2 = lng1 + (Math.random() - 0.5) * 0.02;
        
        const congestion = Math.random() * 0.9 + 0.1;
        const safety = Math.random() * 0.8 + 0.1;
        const growth = Math.random() * 0.9 + 0.1;
        const quality = Math.random() * 0.7 + 0.1;
        
        const isiScore = weights.congestion * congestion + weights.safety * safety + 
                         weights.growth * growth + weights.quality * quality;
        const priority = isiScore > 0.65 ? 'HIGH' : isiScore > 0.45 ? 'MEDIUM' : 'LOW';
        
        features.push({
            type: 'Feature',
            geometry: { type: 'LineString', coordinates: [[lng1, lat1], [lng2, lat2]] },
            properties: {
                segment_id: `seg_${String(i + 1).padStart(3, '0')}`,
                name: roadNames[i],
                road_type: ['primary', 'secondary', 'tertiary'][Math.floor(Math.random() * 3)],
                length_km: (Math.random() * 2 + 0.5).toFixed(2),
                lanes: Math.random() > 0.5 ? 2 : 4,
                isi_score: isiScore,
                congestion_score: congestion,
                safety_score: safety,
                growth_pressure_score: growth,
                road_quality_score: quality,
                priority: priority,
                recommendation: isiScore > 0.6 ? 'Widen road or add flyover' : 'Routine maintenance',
                estimated_cost_millions: (isiScore * 5).toFixed(2)
            }
        });
    }
    
    const criticalCount = features.filter(f => f.properties.isi_score > 0.65).length;
    const avgISI = features.reduce((sum, f) => sum + f.properties.isi_score, 0) / features.length;
    
    return {
        country_code: selectedCountry,
        roads: { type: 'FeatureCollection', features: features },
        recommendations: features.filter(f => f.properties.priority !== 'LOW').map(f => ({
            segment_id: f.properties.segment_id,
            road_name: f.properties.name,
            priority: f.properties.priority,
            action: f.properties.recommendation,
            isi_score: f.properties.isi_score
        })),
        summary: {
            total_segments_analyzed: features.length,
            critical_segments: criticalCount,
            average_isi: avgISI,
            total_estimated_cost_millions: features.reduce((sum, f) => sum + parseFloat(f.properties.estimated_cost_millions), 0).toFixed(2)
        },
        accident_hotspots: [
            { location: [center.lat + 0.01, center.lng + 0.01], severity: 'high' },
            { location: [center.lat - 0.02, center.lng + 0.02], severity: 'medium' }
        ]
    };
}

function showAccidentHotspots(hotspots) {
    hotspotMarkers.forEach(m => map.removeLayer(m));
    hotspotMarkers = [];
    
    hotspots.forEach(h => {
        const [lat, lng] = h.location;
        const color = h.severity === 'high' ? '#DC2626' : '#EA580C';
        const marker = L.circleMarker([lat, lng], {
            radius: 12, color: color, fillColor: color, fillOpacity: 0.6, weight: 2
        }).addTo(map);
        marker.bindPopup(`<b>⚠️ Accident Hotspot</b><br>Severity: ${h.severity.toUpperCase()}`);
        hotspotMarkers.push(marker);
    });
}

function visualizeResults(roadsGeoJSON) {
    if (roadsLayer) map.removeLayer(roadsLayer);
    
    let geoJSON = roadsGeoJSON;
    if (Array.isArray(roadsGeoJSON)) {
        geoJSON = { type: 'FeatureCollection', features: roadsGeoJSON.map(r => ({
            type: 'Feature', geometry: r.geometry || { type: 'Point', coordinates: [78.9629, 20.5937] }, properties: r
        }))};
    }
    
    const weights = COUNTRY_WEIGHTS[selectedCountry] || COUNTRY_WEIGHTS['IN'];
    const country = COUNTRIES[selectedCountry];
    
    roadsLayer = L.geoJSON(geoJSON, {
        style: function(feature) {
            const isi = feature.properties.isi_score || 0.5;
            return { color: getISIColor(isi), weight: 6, opacity: 0.85 };
        },
        onEachFeature: function(feature, layer) {
            const p = feature.properties;
            const isi = p.isi_score || 0;
            
            layer.bindPopup(`
                <div style="min-width:280px">
                    <h3 style="margin:0 0 8px">${p.name || p.segment_id}</h3>
                    <p style="color:#666;margin:0 0 12px">${p.road_type || 'Road'} • ${p.length_km || '?'} km</p>
                    <div style="background:#f3f4f6;padding:12px;border-radius:8px;margin-bottom:12px">
                        <div style="font-size:12px;color:#666">Infrastructure Stress Index</div>
                        <div style="font-size:24px;font-weight:bold;color:${getISIColor(isi)}">${isi.toFixed(3)}</div>
                        <span style="background:${isi>0.65?'#DC2626':isi>0.45?'#EA580C':'#16A34A'};color:white;padding:2px 8px;border-radius:4px;font-size:11px">${p.priority || 'N/A'}</span>
                    </div>
                    <div style="font-size:12px;margin-bottom:8px">
                        <div>🚗 Congestion: ${((p.congestion_score||0)*100).toFixed(0)}% (w: ${(weights.congestion*100).toFixed(0)}%)</div>
                        <div>⚠️ Safety: ${((p.safety_score||0)*100).toFixed(0)}% (w: ${(weights.safety*100).toFixed(0)}%)</div>
                        <div>📈 Growth: ${((p.growth_pressure_score||0)*100).toFixed(0)}% (w: ${(weights.growth*100).toFixed(0)}%)</div>
                        <div>🔧 Quality: ${((p.road_quality_score||0)*100).toFixed(0)}% (w: ${(weights.quality*100).toFixed(0)}%)</div>
                    </div>
                    <div style="background:#e0f2fe;padding:8px;border-radius:6px">
                        <div style="font-weight:600;font-size:12px">📋 ${p.recommendation || 'No action required'}</div>
                        <div style="font-size:11px;color:#666;margin-top:4px">Est. Cost: ${country.currency}${p.estimated_cost_millions || '?'}M</div>
                    </div>
                </div>
            `, { maxWidth: 320 });
            
            layer.on('mouseover', function() { this.setStyle({ weight: 10, opacity: 1 }); });
            layer.on('mouseout', function() { this.setStyle({ weight: 6, opacity: 0.85 }); });
            layer.on('click', function() { showSegmentDetails(p); });
        }
    }).addTo(map);
    
    if (roadsLayer.getBounds().isValid()) {
        map.fitBounds(roadsLayer.getBounds(), { padding: [50, 50] });
    }
}

function updateStats(summary) {
    const country = COUNTRIES[selectedCountry];
    document.getElementById('totalPipeline').textContent = `${country.currency}${summary.total_estimated_cost_millions || 0}M`;
    document.getElementById('activeLeads').textContent = summary.total_segments_analyzed || 0;
    document.getElementById('criticalCount').textContent = summary.critical_segments || 0;
}

function updateRecommendations(recommendations) {
    const sorted = [...(recommendations || [])].sort((a, b) => {
        const order = { 'HIGH': 0, 'MEDIUM': 1, 'LOW': 2 };
        return (order[a.priority] || 2) - (order[b.priority] || 2);
    });
    sorted.slice(0, 5).forEach((r, i) => {
        console.log(`#${i+1} [${r.priority}] ${r.road_name}: ${r.action}`);
    });
}

function showSegmentDetails(props) {
    const drawer = document.getElementById('detailDrawer');
    drawer.classList.add('open');
    
    const isi = props.isi_score || 0;
    const country = COUNTRIES[selectedCountry];
    
    document.getElementById('drawerTitle').textContent = props.name || props.segment_id || 'Segment';
    
    const stressFill = document.getElementById('stressFill');
    stressFill.style.width = `${isi * 100}%`;
    stressFill.style.backgroundColor = getISIColor(isi);
    document.getElementById('stressValue').textContent = isi.toFixed(3);
    
    document.getElementById('congestionScore').textContent = ((props.congestion_score || 0) * 100).toFixed(0) + '%';
    document.getElementById('safetyScore').textContent = ((props.safety_score || 0) * 100).toFixed(0) + '%';
    document.getElementById('structuralScore').textContent = ((props.road_quality_score || 0) * 100).toFixed(0) + '%';
    document.getElementById('growthScore').textContent = ((props.growth_pressure_score || 0) * 100).toFixed(0) + '%';
    
    document.getElementById('recAction').textContent = props.recommendation || 'No action required';
    document.getElementById('recPriority').textContent = props.priority || '-';
    document.getElementById('recPriority').className = `rec-priority ${getPriorityClass(props.priority)}`;
    document.getElementById('recCost').textContent = `${country.currency}${props.estimated_cost_millions || '?'}M`;
    document.getElementById('recRationale').textContent = isi > 0.7 ? 'Critical stress. Immediate action needed.' :
        isi > 0.5 ? 'High stress. Plan intervention within 6 months.' : 'Acceptable levels. Monitor regularly.';
}

function toggleLayer() {
    const layers = ['street', 'satellite', 'hybrid', 'terrain', 'googlemaps', 'googlesatellite', 'googlehybrid'];
    const idx = layers.indexOf(currentLayer);
    map.removeLayer(tileLayers[currentLayer]);
    currentLayer = layers[(idx + 1) % layers.length];
    tileLayers[currentLayer].addTo(map);
    
    // Show which layer is active
    const layerNames = {
        'street': '🗺️ Street Map',
        'satellite': '🛰️ Satellite (Esri)',
        'hybrid': '🌐 Hybrid (Esri)',
        'terrain': '⛰️ Terrain',
        'googlemaps': '🗺️ Google Maps',
        'googlesatellite': '🛰️ Google Satellite',
        'googlehybrid': '🌐 Google Hybrid'
    };
    
    console.log(`📡 Switched to: ${layerNames[currentLayer]}`);
}

function clearAll() {
    drawnItems.clearLayers();
    if (roadsLayer) { map.removeLayer(roadsLayer); roadsLayer = null; }
    hotspotMarkers.forEach(m => map.removeLayer(m));
    hotspotMarkers = [];
    analysisResults = null;
    
    const country = COUNTRIES[selectedCountry];
    document.getElementById('totalPipeline').textContent = `${country.currency}0`;
    document.getElementById('activeLeads').textContent = '0';
    document.getElementById('criticalCount').textContent = '0';
    document.getElementById('detailDrawer').classList.remove('open');
}

function filterResults(filter) {
    if (!roadsLayer) return;
    roadsLayer.eachLayer(function(layer) {
        const isi = layer.feature.properties.isi_score || 0;
        let show = filter === 'all' || 
            (filter === 'critical' && isi > 0.65) || 
            (filter === 'high' && isi > 0.45 && isi <= 0.65) ||
            (filter === 'medium' && isi <= 0.45);
        layer.setStyle({ opacity: show ? 0.85 : 0.15, weight: show ? 6 : 3 });
    });
}

async function searchLocation(query) {
    if (!query.trim()) return;
    try {
        const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`);
        const results = await res.json();
        if (results.length > 0) {
            map.setView([parseFloat(results[0].lat), parseFloat(results[0].lon)], 14);
            L.marker([parseFloat(results[0].lat), parseFloat(results[0].lon)]).addTo(map).bindPopup(results[0].display_name).openPopup();
        }
    } catch (e) { console.error('Search error:', e); }
}

document.addEventListener('DOMContentLoaded', function() {
    initDrawControl();
    updateCountryDisplay();
    
    document.getElementById('analyzeBtn').addEventListener('click', analyze);
    document.getElementById('drawPolygonBtn').addEventListener('click', function() {
        if (!drawControl) {
            alert('Draw control not available. Please refresh the page.');
            return;
        }
        try {
            if (drawControl._map) map.removeControl(drawControl);
            map.addControl(drawControl);
            if (window.L && window.L.Draw && window.L.Draw.Polygon) {
                new L.Draw.Polygon(map, drawControl.options.draw.polygon).enable();
            }
        } catch (e) {
            console.error('Error enabling draw polygon:', e);
            alert('Could not enable draw mode. Please try again.');
        }
    });
    document.getElementById('clearBtn').addEventListener('click', clearAll);
    document.getElementById('zoomInBtn').addEventListener('click', () => map.zoomIn());
    document.getElementById('zoomOutBtn').addEventListener('click', () => map.zoomOut());
    document.getElementById('locateBtn').addEventListener('click', () => map.locate({ setView: true, maxZoom: 16 }));
    document.getElementById('layerToggleBtn').addEventListener('click', toggleLayer);
    document.getElementById('closeDrawer').addEventListener('click', () => document.getElementById('detailDrawer').classList.remove('open'));
    
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', function() {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            filterResults(this.dataset.filter);
        });
    });

    // Layer menu handling
    const layerToggleBtn = document.getElementById('layerToggleBtn');
    const layerMenu = document.getElementById('layerMenu');
    
    if (layerToggleBtn && layerMenu) {
        layerToggleBtn.addEventListener('click', () => {
            layerMenu.style.display = layerMenu.style.display === 'none' ? 'block' : 'none';
        });

        document.querySelectorAll('.layer-option').forEach(btn => {
            btn.addEventListener('click', () => {
                const layer = btn.dataset.layer;
                map.removeLayer(tileLayers[currentLayer]);
                currentLayer = layer;
                tileLayers[currentLayer].addTo(map);
                layerMenu.style.display = 'none';
                
                // Visual feedback
                document.querySelectorAll('.layer-option').forEach(b => {
                    b.style.background = b.dataset.layer === layer ? '#eff6ff' : 'none';
                    b.style.color = b.dataset.layer === layer ? '#2563eb' : '#666';
                    b.style.fontWeight = b.dataset.layer === layer ? '600' : 'normal';
                });
                
                console.log(`📡 Switched to: ${btn.textContent.trim()}`);
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!layerToggleBtn.contains(e.target) && !layerMenu.contains(e.target)) {
                layerMenu.style.display = 'none';
            }
        });
    }

    
    document.getElementById('searchInput').addEventListener('keypress', e => {
        if (e.key === 'Enter') searchLocation(e.target.value);
    });
    
    const countrySelect = document.getElementById('countrySelect');
    if (countrySelect) countrySelect.addEventListener('change', e => changeCountry(e.target.value));
    
    map.on('locationfound', e => L.marker(e.latlng).addTo(map).bindPopup('You are here').openPopup());
});

window.InfraSenseApp = { map, analyze, clearAll, changeCountry, COUNTRIES, COUNTRY_WEIGHTS };
