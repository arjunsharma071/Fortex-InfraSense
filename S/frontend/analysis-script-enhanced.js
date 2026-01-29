/**
 * Advanced Analysis Dashboard Script
 * Handles interactive map visualization and real-time analysis
 */

class AdvancedAnalysisDashboard {
    constructor() {
        this.map = null;
        this.analysisData = null;
        this.selectedRoad = null;
        this.currentFilters = {
            timeRange: 30,
            frequencyThreshold: 0.57,  // ~4 days/week
            roadTypes: ['highway', 'primary', 'secondary'],
            interventions: ['widening', 'flyover', 'bridge', 'maintenance', 'signals', 'planning'],
            priorities: ['critical', 'high', 'medium', 'low']
        };
        
        this.charts = {};
        this.roadLayers = {};
    }
    
    async init() {
        console.log('Initializing Advanced Analysis Dashboard...');
        
        // Initialize map
        this.initMap();
        
        // Load analysis data
        await this.loadAnalysisData();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Render initial visualization
        this.renderAnalysis();
    }
    
    initMap() {
        // Create Leaflet map centered on India
        this.map = L.map('analysis-map').setView([20.5937, 78.9629], 12);
        
        // Add base layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);
        
        // Create feature groups for different visualization layers
        this.layers = {
            stress: L.featureGroup(),
            traffic: L.featureGroup(),
            accidents: L.featureGroup(),
            interventions: L.featureGroup()
        };
        
        // Add default layer
        this.layers.stress.addTo(this.map);
        
        // Add layer control
        const overlays = {
            'Stress Heatmap': this.layers.stress,
            'Traffic Flow': this.layers.traffic,
            'Accident Zones': this.layers.accidents,
            'Proposed Interventions': this.layers.interventions
        };
        
        L.control.layers(null, overlays, { position: 'topright' }).addTo(this.map);
    }
    
    async loadAnalysisData() {
        try {
            this.showLoading();
            
            // Get area ID from URL or use default
            const areaId = this.getAreaIdFromURL();
            
            // Fetch analysis data from backend API
            const response = await fetch(`/api/analysis/${areaId}?days=${this.currentFilters.timeRange}`);
            
            if (!response.ok) {
                throw new Error(`API error: ${response.statusText}`);
            }
            
            this.analysisData = await response.json();
            
            if (!this.analysisData.success) {
                console.warn('Analysis returned with warnings', this.analysisData);
            }
            
            // Update statistics
            this.updateStatistics();
            this.hideLoading();
            
        } catch (error) {
            console.error('Failed to load analysis data:', error);
            this.loadSampleData();
            this.hideLoading();
        }
    }
    
    renderAnalysis() {
        if (!this.analysisData || !this.analysisData.roads) return;
        
        // Clear existing layers
        Object.values(this.layers).forEach(layer => layer.clearLayers());
        
        // Render each road segment
        this.analysisData.roads.forEach(road => {
            this.renderRoadSegment(road);
        });
        
        // Render interventions
        this.renderInterventions();
        
        // Update charts and visualizations
        this.updateCharts();
        this.updateInterventionsList();
    }
    
    renderRoadSegment(road) {
        // Skip if road type is filtered out
        if (!this.currentFilters.roadTypes.includes(road.road_type)) {
            return;
        }
        
        // Get color based on priority/frequency
        const color = this.getRoadColor(road);
        const weight = this.getRoadWeight(road);
        
        // Create polyline for the road
        const coordinates = this.convertCoordinates(road.geometry);
        if (coordinates.length < 2) return;
        
        const polyline = L.polyline(coordinates, {
            color: color,
            weight: weight,
            opacity: 0.8,
            lineCap: 'round',
            lineJoin: 'round'
        });
        
        // Bind popup
        const popupText = this.createRoadPopup(road);
        polyline.bindPopup(popupText);
        
        // Add hover effects
        polyline.on('mouseover', (e) => this.onRoadHover(e, road));
        polyline.on('mouseout', (e) => this.onRoadHoverOut(e));
        polyline.on('click', (e) => this.onRoadClick(e, road));
        
        // Add to stress layer
        polyline.addTo(this.layers.stress);
        
        // Store reference
        road.polyline = polyline;
        this.roadLayers[road.road_id] = polyline;
    }
    
    createRoadPopup(road) {
        const frequency = (road.traffic_patterns.frequency_score * 100).toFixed(0);
        const congestion = (road.congestion_metrics.avg_congestion * 100).toFixed(0);
        const days = road.traffic_patterns.high_traffic_days_count || 0;
        
        return `
            <div class="road-popup">
                <strong>${road.road_name}</strong>
                <p>Type: ${road.road_type.toUpperCase()}</p>
                <p>Length: ${road.length_km.toFixed(1)} km | Lanes: ${road.lanes}</p>
                <p>Traffic Frequency: <strong>${frequency}%</strong> (${days}/7 days)</p>
                <p>Avg Congestion: <strong>${congestion}%</strong></p>
                <p>Priority: <strong>${road.priority.toUpperCase()}</strong></p>
                <button onclick="dashboard.selectRoad('${road.road_id}')" class="btn-select">
                    View Details
                </button>
            </div>
        `;
    }
    
    getRoadColor(road) {
        // Color based on combined score of frequency and severity
        const frequency = road.traffic_patterns.frequency_score;
        const congestion = road.congestion_metrics.avg_congestion;
        
        // Combined score (weighted)
        const score = (frequency * 0.6) + (congestion * 0.4);
        
        // Return color based on score
        if (score >= 0.8) return '#d32f2f';      // Critical - Dark Red
        if (score >= 0.6) return '#f57c00';      // High - Deep Orange
        if (score >= 0.4) return '#fbc02d';      // Medium - Yellow
        if (score >= 0.2) return '#689f38';      // Low - Light Green
        return '#9e9e9e';                         // Very Low - Gray
    }
    
    getRoadWeight(road) {
        // Weight based on road importance and traffic volume
        const baseWeights = {
            'highway': 6,
            'primary': 5,
            'secondary': 4,
            'tertiary': 3,
            'residential': 2
        };
        
        let weight = baseWeights[road.road_type] || 3;
        
        // Increase weight for high traffic roads
        if (road.traffic_patterns.frequency_score >= 0.7) {
            weight += 2;
        } else if (road.traffic_patterns.frequency_score >= 0.4) {
            weight += 1;
        }
        
        return weight;
    }
    
    renderInterventions() {
        // Clear previous interventions
        this.layers.interventions.clearLayers();
        
        // Add intervention markers
        if (this.analysisData && this.analysisData.roads) {
            this.analysisData.roads.forEach(road => {
                if (road.needs_intervention && road.recommendations) {
                    road.recommendations.forEach(rec => {
                        if (this.currentFilters.interventions.includes(rec.type)) {
                            this.renderIntervention(road, rec);
                        }
                    });
                }
            });
        }
    }
    
    renderIntervention(road, recommendation) {
        // Get center point of road from coordinates
        const coordinates = this.convertCoordinates(road.geometry);
        if (coordinates.length === 0) return;
        
        const centerIndex = Math.floor(coordinates.length / 2);
        const center = coordinates[centerIndex];
        
        // Create icon
        const icon = this.createInterventionIcon(recommendation.type, recommendation.priority);
        
        // Create marker
        const marker = L.marker(center, { icon: icon })
            .bindPopup(this.createInterventionPopup(road, recommendation));
        
        // Add to interventions layer
        marker.addTo(this.layers.interventions);
    }
    
    createInterventionIcon(type, priority) {
        const colors = {
            'widening': '#e74c3c',
            'flyover': '#3498db',
            'bridge': '#9b59b6',
            'maintenance': '#f39c12',
            'signals': '#2ecc71',
            'planning': '#7f8c8d'
        };
        
        const iconClass = this.getInterventionIconClass(type);
        const color = colors[type] || '#9e9e9e';
        
        return L.divIcon({
            html: `<div style="background-color: ${color}" class="intervention-marker-icon">
                   <i class="fas ${iconClass}"></i></div>`,
            className: 'custom-intervention-icon',
            iconSize: [35, 35],
            iconAnchor: [17, 35],
            popupAnchor: [0, -35]
        });
    }
    
    getInterventionIconClass(type) {
        const iconMap = {
            'widening': 'fa-arrows-alt-h',
            'flyover': 'fa-bridge',
            'bridge': 'fa-archway',
            'maintenance': 'fa-tools',
            'signals': 'fa-traffic-light',
            'planning': 'fa-calendar-plus'
        };
        
        return iconMap[type] || 'fa-hard-hat';
    }
    
    createInterventionPopup(road, recommendation) {
        return `
            <div class="intervention-popup">
                <h4>${road.road_name}</h4>
                <div class="intervention-type-badge ${recommendation.priority}">
                    ${recommendation.type.toUpperCase()} - ${recommendation.priority.toUpperCase()} PRIORITY
                </div>
                <p><strong>${recommendation.title || recommendation.description}</strong></p>
                <p><em>${recommendation.reason}</em></p>
                ${recommendation.estimated_cost ? `<p><strong>Cost:</strong> ${recommendation.estimated_cost}</p>` : ''}
                ${recommendation.impact ? `<p><strong>Impact:</strong> ${recommendation.impact}</p>` : ''}
                <p><strong>Timeline:</strong> ${recommendation.timeline || 'To be determined'}</p>
            </div>
        `;
    }
    
    onRoadHover(e, road) {
        // Highlight the road
        e.target.setStyle({
            weight: e.target.options.weight + 2,
            opacity: 1
        });
        
        // Show tooltip with key metrics
        const tooltip = `
            <strong>${road.road_name}</strong><br>
            Frequency: ${(road.traffic_patterns.frequency_score * 100).toFixed(0)}%<br>
            Congestion: ${(road.congestion_metrics.avg_congestion * 100).toFixed(0)}%<br>
            Priority: ${road.priority.toUpperCase()}
        `;
        
        // Bring to front
        if (e.target.bringToFront) {
            e.target.bringToFront();
        }
    }
    
    onRoadHoverOut(e) {
        // Reset style
        if (e.target.options.weight >= 2) {
            e.target.setStyle({
                weight: e.target.options.weight - 2,
                opacity: 0.8
            });
        }
    }
    
    onRoadClick(e, road) {
        // Select this road
        this.selectRoad(road.road_id);
        
        // Zoom to road bounds
        if (e.target.getBounds) {
            this.map.fitBounds(e.target.getBounds(), { padding: [50, 50] });
        }
    }
    
    selectRoad(roadId) {
        // Find the road
        if (!this.analysisData || !this.analysisData.roads) return;
        
        const road = this.analysisData.roads.find(r => r.road_id === roadId);
        if (!road) return;
        
        this.selectedRoad = road;
        
        // Update UI
        this.updateRoadDetails(road);
        this.updateTrafficPatterns(road);
        
        // Highlight selected road
        this.highlightSelectedRoad(road);
    }
    
    highlightSelectedRoad(road) {
        // Reset all roads
        this.analysisData.roads.forEach(r => {
            if (r.polyline) {
                r.polyline.setStyle({
                    color: this.getRoadColor(r),
                    opacity: 0.8,
                    weight: this.getRoadWeight(r)
                });
            }
        });
        
        // Highlight selected
        if (road.polyline) {
            road.polyline.setStyle({
                color: '#2196f3',
                weight: road.polyline.options.weight + 3,
                opacity: 1
            });
            road.polyline.bringToFront();
        }
    }
    
    updateRoadDetails(road) {
        const container = document.getElementById('problems-content') || document.getElementById('problems-tab');
        if (!container) return;
        
        let html = `
            <div class="road-details-container">
                <div class="road-header">
                    <h4>${road.road_name}</h4>
                    <span class="road-type-badge ${road.road_type}">${road.road_type.toUpperCase()}</span>
                    <span class="priority-badge ${road.priority}">${road.priority.toUpperCase()}</span>
                </div>
                
                <div class="road-metrics-grid">
                    <div class="metric-box">
                        <span class="metric-label">Road Length</span>
                        <span class="metric-value">${road.length_km.toFixed(1)} km</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Current Lanes</span>
                        <span class="metric-value">${road.lanes}</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Traffic Frequency</span>
                        <span class="metric-value ${road.traffic_patterns.frequency_score >= 0.6 ? 'high' : 'low'}">
                            ${(road.traffic_patterns.frequency_score * 100).toFixed(0)}%
                        </span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Avg. Congestion</span>
                        <span class="metric-value ${road.congestion_metrics.avg_congestion >= 0.7 ? 'high' : 'low'}">
                            ${(road.congestion_metrics.avg_congestion * 100).toFixed(0)}%
                        </span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Peak Congestion</span>
                        <span class="metric-value">
                            ${(road.congestion_metrics.max_congestion * 100).toFixed(0)}%
                        </span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">High Traffic Days</span>
                        <span class="metric-value">
                            ${road.traffic_patterns.high_traffic_days_count || 0}/7
                        </span>
                    </div>
                </div>
        `;
        
        if (road.needs_intervention && road.recommendations && road.recommendations.length > 0) {
            html += `
                <div class="interventions-needed">
                    <h5><i class="fas fa-exclamation-circle"></i> Interventions Required (${road.recommendations.length})</h5>
                    <div class="interventions-list-detailed">
            `;
            
            road.recommendations.forEach((rec, idx) => {
                html += `
                    <div class="intervention-card ${rec.priority}">
                        <div class="intervention-card-header">
                            <div class="intervention-icon-badge ${rec.type}">
                                <i class="fas ${this.getInterventionIconClass(rec.type)}"></i>
                            </div>
                            <div class="intervention-card-title">
                                <h6>${rec.title || rec.description}</h6>
                                <span class="intervention-priority-badge ${rec.priority}">
                                    ${rec.priority.toUpperCase()} PRIORITY
                                </span>
                            </div>
                        </div>
                        <div class="intervention-card-body">
                            <p><strong>What:</strong> ${rec.description}</p>
                            <p><strong>Why:</strong> ${rec.reason}</p>
                            <p><strong>Cost:</strong> ${rec.estimated_cost || 'N/A'}</p>
                            <p><strong>Timeline:</strong> ${rec.timeline || 'N/A'}</p>
                            ${rec.impact ? `<p><strong>Impact:</strong> ${rec.impact}</p>` : ''}
                            ${rec.implementation_phases ? `
                                <details>
                                    <summary>Implementation Phases</summary>
                                    <ul>
                                        ${rec.implementation_phases.map(p => `<li>${p}</li>`).join('')}
                                    </ul>
                                </details>
                            ` : ''}
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="no-intervention-notice">
                    <p><i class="fas fa-check-circle"></i> No major intervention needed at this time.</p>
                    <p>Traffic patterns are within acceptable limits (frequency < 4 days/week).</p>
                    <p><strong>Recommendation:</strong> Continue monitoring traffic patterns and re-evaluate in 3 months.</p>
                </div>
            `;
        }
        
        html += `</div>`;
        
        container.innerHTML = html;
    }
    
    updateTrafficPatterns(road) {
        // Update daily frequency display
        const daysWithTraffic = road.traffic_patterns.high_traffic_days_count || 0;
        const totalDays = Object.keys(road.traffic_patterns.daily_patterns || {}).length || 30;
        
        const freqPercent = (daysWithTraffic / totalDays) * 100;
        document.getElementById('daily-frequency').textContent = `${daysWithTraffic}/${totalDays} days`;
        document.getElementById('frequency-bar').style.width = `${freqPercent}%`;
        
        // Update peak duration
        const peakHours = road.traffic_patterns.peak_hours || [];
        const durationBar = document.getElementById('duration-bar');
        if (durationBar) {
            durationBar.style.width = `${(peakHours.length / 24) * 100}%`;
        }
        document.getElementById('peak-duration').textContent = `${peakHours.length} hrs/day`;
        
        // Update hourly pattern chart
        this.updateHourlyPatternChart(road);
    }
    
    updateHourlyPatternChart(road) {
        // Create hourly congestion pattern based on peak hours
        const peakHours = road.traffic_patterns.peak_hours || [];
        const hourlyData = new Array(24).fill(0.2);  // Base level
        
        // Set peaks
        peakHours.forEach(hour => {
            hourlyData[hour] = 0.7 + Math.random() * 0.2;
        });
        
        // Render chart using Chart.js
        const chartElement = document.getElementById('hourly-pattern-chart');
        if (!chartElement) return;
        
        if (this.charts.hourly) {
            this.charts.hourly.destroy();
        }
        
        const ctx = chartElement.getContext('2d');
        this.charts.hourly = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({length: 24}, (_, i) => `${i}:00`),
                datasets: [{
                    label: 'Congestion Level',
                    data: hourlyData,
                    borderColor: '#d32f2f',
                    backgroundColor: 'rgba(211, 47, 47, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointBackgroundColor: hourlyData.map(v => v > 0.6 ? '#d32f2f' : '#7c7c7c')
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => `Congestion: ${(context.raw * 100).toFixed(0)}%`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: { callback: (value) => `${(value * 100).toFixed(0)}%` }
                    }
                }
            }
        });
    }
    
    updateStatistics() {
        if (!this.analysisData || !this.analysisData.roads) return;
        
        const roads = this.analysisData.roads;
        
        // Count by priority
        const priorityCounts = { critical: 0, high: 0, medium: 0, low: 0, monitor: 0 };
        roads.forEach(road => {
            const priority = road.priority || 'monitor';
            if (priority in priorityCounts) {
                priorityCounts[priority]++;
            }
        });
        
        // Update UI
        const el = (id) => document.getElementById(id);
        el('critical-roads').textContent = priorityCounts.critical;
        el('high-priority-roads').textContent = priorityCounts.high;
        el('medium-priority-roads').textContent = priorityCounts.medium;
        el('low-priority-roads').textContent = priorityCounts.low + priorityCounts.monitor;
        
        // Update total cost
        const totalCost = this.analysisData.area_insights?.total_estimated_cost || 0;
        const totalCostDisplay = el('total-cost');
        if (totalCostDisplay) {
            totalCostDisplay.textContent = `₹${(totalCost / 10).toFixed(1)} Cr`;
        }
        
        // Update decision summary
        let needsChangeCount = 0;
        let needsFlyoverCount = 0;
        let needsWideningCount = 0;
        
        roads.forEach(road => {
            if (road.recommendations) {
                road.recommendations.forEach(rec => {
                    if (rec.type === 'widening') needsWideningCount++;
                    if (rec.type === 'flyover') needsFlyoverCount++;
                    if (rec.priority === 'high' || rec.priority === 'critical') needsChangeCount++;
                });
            }
        });
        
        el('needs-change-count').textContent = needsChangeCount;
        el('needs-flyover-count').textContent = needsFlyoverCount;
        el('needs-widening-count').textContent = needsWideningCount;
        el('monitor-count').textContent = roads.length - (needsChangeCount);
        
        // Update trend metrics
        const areaInsights = this.analysisData.area_insights;
        if (areaInsights) {
            const avgCong = areaInsights.area_metrics?.average_congestion || 0;
            el('avg-congestion').textContent = `${(avgCong * 100).toFixed(0)}%`;
            el('peak-hours').textContent = areaInsights.area_metrics?.peak_congestion_hour || 'N/A';
        }
    }
    
    updateInterventionsList() {
        const container = document.getElementById('interventions-list');
        if (!container || !this.analysisData) return;
        
        // Get all interventions
        let allInterventions = [];
        (this.analysisData.roads || []).forEach(road => {
            if (road.recommendations) {
                road.recommendations.forEach(rec => {
                    allInterventions.push({
                        ...rec,
                        road_name: road.road_name,
                        road_id: road.road_id,
                        frequency: road.traffic_patterns.frequency_score
                    });
                });
            }
        });
        
        // Sort by priority then frequency
        const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
        allInterventions.sort((a, b) => {
            const p = priorityOrder[a.priority] - priorityOrder[b.priority];
            return p !== 0 ? p : b.frequency - a.frequency;
        });
        
        // Render
        let html = '';
        allInterventions.slice(0, 10).forEach(intervention => {
            html += `
                <div class="intervention-list-item ${intervention.priority}" 
                     onclick="dashboard.selectRoad('${intervention.road_id}')">
                    <div class="intervention-icon-small">
                        <i class="fas ${this.getInterventionIconClass(intervention.type)}"></i>
                    </div>
                    <div class="intervention-info">
                        <div class="intervention-title">${intervention.road_name}</div>
                        <div class="intervention-desc">${intervention.title || intervention.description}</div>
                        <div class="intervention-priority ${intervention.priority}">
                            ${intervention.priority.toUpperCase()} PRIORITY
                        </div>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html || '<p>No interventions needed in this area.</p>';
    }
    
    updateCharts() {
        this.updateTrendChart();
    }
    
    updateTrendChart() {
        const chartElement = document.getElementById('trend-chart');
        if (!chartElement || !this.analysisData) return;
        
        // Create sample weekly trend
        const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const roads = this.analysisData.roads || [];
        
        const congestionByDay = [0, 0, 0, 0, 0, 0, 0];
        const countByDay = [0, 0, 0, 0, 0, 0, 0];
        
        roads.forEach((road, idx) => {
            const dayIndex = idx % 7;
            congestionByDay[dayIndex] += road.congestion_metrics?.avg_congestion || 0;
            countByDay[dayIndex]++;
        });
        
        const avgCongestionByDay = congestionByDay.map((val, i) => 
            countByDay[i] > 0 ? val / countByDay[i] : 0
        );
        
        if (this.charts.trend) {
            this.charts.trend.destroy();
        }
        
        const ctx = chartElement.getContext('2d');
        this.charts.trend = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: days,
                datasets: [{
                    label: 'Average Congestion',
                    data: avgCongestionByDay,
                    backgroundColor: avgCongestionByDay.map(val =>
                        val >= 0.7 ? '#d32f2f' :
                        val >= 0.5 ? '#f57c00' :
                        val >= 0.3 ? '#fbc02d' : '#689f38'
                    ),
                    borderWidth: 1,
                    borderColor: '#333'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => `Congestion: ${(context.raw * 100).toFixed(0)}%`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: { callback: (value) => `${(value * 100).toFixed(0)}%` }
                    }
                }
            }
        });
    }
    
    setupEventListeners() {
        // Time range selector
        const timeRangeEl = document.getElementById('time-range');
        if (timeRangeEl) {
            timeRangeEl.addEventListener('change', (e) => {
                this.currentFilters.timeRange = parseInt(e.target.value);
                this.reloadAnalysis();
            });
        }
        
        // Frequency threshold slider
        const thresholdSlider = document.getElementById('frequency-threshold');
        if (thresholdSlider) {
            thresholdSlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                this.currentFilters.frequencyThreshold = value / 7;
                document.getElementById('threshold-value').textContent = `≥${value} days/week`;
            });
        }
        
        // Road type filters
        document.querySelectorAll('input[name="road-type"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateRoadTypeFilters();
                this.renderAnalysis();
            });
        });
        
        // Intervention filters
        document.querySelectorAll('input[name="intervention"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateInterventionFilters();
                this.renderInterventions();
            });
        });
        
        // Priority filters
        document.querySelectorAll('.priority-badge').forEach(badge => {
            badge.addEventListener('click', (e) => {
                e.currentTarget.classList.toggle('active');
                this.updatePriorityFilters();
                this.renderAnalysis();
            });
        });
        
        // Apply filters button
        const applyBtn = document.getElementById('apply-filters');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => this.reloadAnalysis());
        }
        
        // Tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                e.currentTarget.classList.add('active');
                const tabId = `${e.currentTarget.dataset.tab}-tab`;
                const tabContent = document.getElementById(tabId);
                if (tabContent) {
                    tabContent.classList.add('active');
                }
            });
        });
        
        // Layer buttons
        document.querySelectorAll('.layer-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.layer-btn').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
                this.switchMapLayer(e.currentTarget.dataset.layer);
            });
        });
        
        // Export button
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportReport());
        }
    }
    
    updateRoadTypeFilters() {
        const checkboxes = document.querySelectorAll('input[name="road-type"]:checked');
        this.currentFilters.roadTypes = Array.from(checkboxes).map(cb => cb.value);
    }
    
    updateInterventionFilters() {
        const checkboxes = document.querySelectorAll('input[name="intervention"]:checked');
        this.currentFilters.interventions = Array.from(checkboxes).map(cb => cb.value);
    }
    
    updatePriorityFilters() {
        const activeBadges = document.querySelectorAll('.priority-badge.active');
        this.currentFilters.priorities = Array.from(activeBadges).map(badge => badge.dataset.priority);
    }
    
    async reloadAnalysis() {
        this.showLoading();
        try {
            await this.loadAnalysisData();
            this.renderAnalysis();
        } catch (error) {
            console.error('Failed to reload analysis:', error);
        } finally {
            this.hideLoading();
        }
    }
    
    switchMapLayer(layerName) {
        // Remove all layers
        Object.values(this.layers).forEach(layer => {
            this.map.removeLayer(layer);
        });
        
        // Add selected layer
        if (this.layers[layerName]) {
            this.layers[layerName].addTo(this.map);
        }
    }
    
    exportReport() {
        if (!this.analysisData) return;
        
        const report = {
            title: 'InfraSense AI - Advanced Analysis Report',
            generated: new Date().toISOString(),
            summary: this.analysisData.summary,
            areaInsights: this.analysisData.area_insights,
            roads: this.analysisData.roads.map(r => ({
                name: r.road_name,
                type: r.road_type,
                priority: r.priority,
                frequency: `${(r.traffic_patterns.frequency_score * 100).toFixed(0)}%`,
                recommendations: r.recommendations
            }))
        };
        
        const json = JSON.stringify(report, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analysis-report-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    showLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'flex';
    }
    
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';
    }
    
    getAreaIdFromURL() {
        const params = new URLSearchParams(window.location.search);
        return params.get('area') || 'default';
    }
    
    convertCoordinates(geometry) {
        if (!geometry) return [];
        
        if (geometry.type === 'LineString' && geometry.coordinates) {
            return geometry.coordinates.map(coord => [coord[1], coord[0]]);  // [lat, lng]
        }
        return [];
    }
    
    loadSampleData() {
        // Sample data for demonstration
        this.analysisData = {
            roads: [
                {
                    road_id: 'road_mg',
                    road_name: 'MG Road',
                    road_type: 'primary',
                    length_km: 8,
                    lanes: 2,
                    geometry: { type: 'LineString', coordinates: [[78.44, 17.35], [78.48, 17.38]] },
                    needs_intervention: true,
                    priority: 'high',
                    traffic_patterns: {
                        frequency_score: 0.8,
                        high_traffic_days: new Array(6).fill(0),
                        high_traffic_days_count: 6,
                        peak_hours: [8, 9, 17, 18, 19],
                        trend: 'increasing',
                        daily_patterns: {}
                    },
                    congestion_metrics: {
                        avg_congestion: 0.75,
                        max_congestion: 0.92,
                        peak_congestion: 0.92
                    },
                    recommendations: [
                        {
                            type: 'widening',
                            priority: 'high',
                            title: 'Widen from 2 to 4 lanes',
                            description: 'Expand road width to handle peak hour traffic',
                            reason: 'Congestion occurs 80% of days',
                            estimated_cost: '₹8.5 Cr',
                            cost_value: 8.5,
                            impact: '100% increase in capacity',
                            timeline: '12-18 months'
                        }
                    ]
                }
            ],
            area_insights: {
                total_roads_analyzed: 15,
                roads_needing_intervention: 5,
                intervention_rate: 33.3,
                total_estimated_cost: 45.2,
                area_metrics: {
                    average_frequency: 0.65,
                    average_congestion: 0.58,
                    peak_congestion_hour: '18:00'
                }
            },
            summary: {
                analysis_date: new Date().toISOString().split('T')[0],
                key_findings: {
                    critical_issues: 1,
                    high_priority_issues: 3,
                    total_interventions_needed: 5,
                    estimated_total_cost_value: 45.2
                }
            },
            success: true
        };
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new AdvancedAnalysisDashboard();
    window.dashboard.init();
});
