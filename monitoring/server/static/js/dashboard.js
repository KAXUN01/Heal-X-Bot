// Function to format bytes to human-readable format
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Global charts
let ddosTimelineChart = null;
let networkTrafficChart = null;
let connectionChart = null;

// Global variables for maps and advanced charts
let worldMap = null;
let attackHeatmap = null;
let trafficPatternChart = null;
let websocket = null;

// Initialize WebSocket connection
function initializeWebSocket() {
    websocket = new WebSocket('ws://' + window.location.host + '/ws');
    
    websocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        updateThreatMap(data);
        updateAttackPatterns(data);
        if (data.pattern_detected) {
            showAlert(data);
        }
    };

    websocket.onclose = function() {
        setTimeout(initializeWebSocket, 5000); // Reconnect after 5 seconds
    };
}

// Function to update the dashboard
function updateDashboard() {
    Promise.all([
        fetch('/metrics').then(response => response.text()),
        fetch('/api/metrics_history').then(response => response.json())
    ]).then(([metricsData, historyData]) => {
        const metrics = {};
        metricsData.split('\n').forEach(line => {
            if (!line.startsWith('#') && line.trim()) {
                const [key, value] = line.split(' ');
                metrics[key] = parseFloat(value);
            }
        });

        // Update System Overview
        updateProgressBar('cpuLoad', metrics['cpu_load_simulation'] || 0);
        updateProgressBar('memoryUsage', metrics['memory_usage_percent'] || 0);
        updateProgressBar('systemCpu', metrics['system_cpu_percent'] || 0);

        // Update Memory Info
        document.getElementById('virtualMemory').textContent = formatBytes(metrics['process_virtual_memory_bytes'] || 0);
        document.getElementById('residentMemory').textContent = formatBytes(metrics['process_resident_memory_bytes'] || 0);
        document.getElementById('openFds').textContent = metrics['process_open_fds'] || 0;
        document.getElementById('cpuTime').textContent = (metrics['process_cpu_seconds_total'] || 0).toFixed(2) + ' seconds';

        // Update Network Stats
        document.getElementById('networkIn').textContent = formatBytes(metrics['network_in_bytes'] || 0);
        document.getElementById('networkOut').textContent = formatBytes(metrics['network_out_bytes'] || 0);
        document.getElementById('connections').textContent = metrics['active_connections'] || 0;

        // Update charts with historical data
        updateCharts(historyData);

        // Update last update time
        document.getElementById('lastUpdateTime').textContent = 
            'Last Updated: ' + new Date().toLocaleTimeString();

        // Update System Overview
        updateProgressBar('cpuLoad', metrics['cpu_load_simulation'] || 0);
        updateProgressBar('memoryUsage', metrics['memory_usage_percent'] || 0);
        updateProgressBar('systemCpu', metrics['system_cpu_percent'] || 0);
        
        // Update DDoS Threat Level
        updateDDoSThreatLevel(metrics['ddos_probability'] || 0);
        
        // Update timeline charts
        updateDDoSTimelineChart(historyData);
        updateNetworkTrafficChart(historyData);
        updateConnectionChart(historyData);

            // Update Process Information
            document.getElementById('virtualMemory').textContent = formatBytes(metrics['process_virtual_memory_bytes'] || 0);
            document.getElementById('residentMemory').textContent = formatBytes(metrics['process_resident_memory_bytes'] || 0);
            document.getElementById('openFds').textContent = metrics['process_open_fds'] || 0;
            document.getElementById('cpuTime').textContent = (metrics['process_cpu_seconds_total'] || 0).toFixed(2) + ' seconds';

            // Update charts
            updateGCObjectsChart(metrics);
            updateGCCollectionsChart(metrics);

            // Update Python Info
            updatePythonInfo(metrics);
        });
}

function updateProgressBar(id, value) {
    const progressBar = document.getElementById(id);
    const textElement = document.getElementById(id + 'Text');
    const percentage = Math.min(Math.max(value, 0), 100);
    
    progressBar.style.width = `${percentage}%`;
    textElement.textContent = `${percentage.toFixed(1)}%`;

    if (percentage < 60) {
        progressBar.className = 'progress-bar bg-success';
    } else if (percentage < 80) {
        progressBar.className = 'progress-bar bg-warning';
    } else {
        progressBar.className = 'progress-bar bg-danger';
    }
}

let gcObjectsChart = null;
function updateGCObjectsChart(metrics) {
    const ctx = document.getElementById('gcObjectsChart');
    const data = {
        labels: ['Generation 0', 'Generation 1', 'Generation 2'],
        datasets: [
            {
                label: 'Objects Collected',
                data: [
                    metrics['python_gc_objects_collected_total{generation="0"}'] || 0,
                    metrics['python_gc_objects_collected_total{generation="1"}'] || 0,
                    metrics['python_gc_objects_collected_total{generation="2"}'] || 0
                ],
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            },
            {
                label: 'Objects Uncollectable',
                data: [
                    metrics['python_gc_objects_uncollectable_total{generation="0"}'] || 0,
                    metrics['python_gc_objects_uncollectable_total{generation="1"}'] || 0,
                    metrics['python_gc_objects_uncollectable_total{generation="2"}'] || 0
                ],
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }
        ]
    };

    if (!gcObjectsChart) {
        gcObjectsChart = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } else {
        gcObjectsChart.data = data;
        gcObjectsChart.update();
    }
}

let gcCollectionsChart = null;
function updateGCCollectionsChart(metrics) {
    const ctx = document.getElementById('gcCollectionsChart');
    const data = {
        labels: ['Generation 0', 'Generation 1', 'Generation 2'],
        datasets: [{
            label: 'Collections',
            data: [
                metrics['python_gc_collections_total{generation="0"}'] || 0,
                metrics['python_gc_collections_total{generation="1"}'] || 0,
                metrics['python_gc_collections_total{generation="2"}'] || 0
            ],
            backgroundColor: 'rgba(75, 192, 192, 0.5)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1
        }]
    };

    if (!gcCollectionsChart) {
        gcCollectionsChart = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } else {
        gcCollectionsChart.data = data;
        gcCollectionsChart.update();
    }
}

function updatePythonInfo(metrics) {
    const pythonInfo = document.getElementById('pythonInfo');
    const version = `${metrics['python_info{implementation="CPython",major="3",minor="9",patchlevel="23",version="3.9.23"}'] ? '3.9.23' : 'Unknown'}`;
    pythonInfo.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <strong>Implementation:</strong> CPython
            </div>
            <div class="col-md-6">
                <strong>Version:</strong> ${version}
            </div>
        </div>
    `;
}

function updateDDoSThreatLevel(probability) {
    const threatLevel = document.getElementById('ddosThreatLevel');
    const threatBar = document.getElementById('ddosThreatBar');
    const percentage = probability * 100;

    threatBar.style.width = `${percentage}%`;
    threatBar.className = `progress-bar ${percentage > 80 ? 'bg-danger' : percentage > 50 ? 'bg-warning' : 'bg-success'}`;
    
    // Update threat level text
    let threatText = percentage > 80 ? 'Critical' : percentage > 50 ? 'Warning' : 'Normal';
    document.getElementById('ddosThreatText').textContent = `${threatText} (${percentage.toFixed(1)}%)`;
}

function updateDDoSTimelineChart(data) {
    const ctx = document.getElementById('ddosTimelineChart');
    const chartData = {
        labels: data.timestamps,
        datasets: [{
            label: 'DDoS Probability',
            data: data.ddos_prob,
            borderColor: 'rgb(255, 99, 132)',
            backgroundColor: 'rgba(255, 99, 132, 0.5)',
            fill: true
        }]
    };

    if (!ddosTimelineChart) {
        ddosTimelineChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1
                    }
                },
                animation: false
            }
        });
    } else {
        ddosTimelineChart.data = chartData;
        ddosTimelineChart.update('none');
    }
}

function updateNetworkTrafficChart(data) {
    const ctx = document.getElementById('networkTrafficChart');
    const chartData = {
        labels: data.timestamps,
        datasets: [{
            label: 'Network In (bytes)',
            data: data.network_in,
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.5)'
        }, {
            label: 'Network Out (bytes)',
            data: data.network_out,
            borderColor: 'rgb(153, 102, 255)',
            backgroundColor: 'rgba(153, 102, 255, 0.5)'
        }]
    };

    if (!networkTrafficChart) {
        networkTrafficChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                animation: false
            }
        });
    } else {
        networkTrafficChart.data = chartData;
        networkTrafficChart.update('none');
    }
}

function updateConnectionChart(data) {
    const ctx = document.getElementById('connectionChart');
    const chartData = {
        labels: data.timestamps,
        datasets: [{
            label: 'Active Connections',
            data: data.connections,
            borderColor: 'rgb(255, 159, 64)',
            backgroundColor: 'rgba(255, 159, 64, 0.5)',
            fill: true
        }]
    };

    if (!connectionChart) {
        connectionChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                animation: false
            }
        });
    } else {
        connectionChart.data = chartData;
        connectionChart.update('none');
    }
}

function updateThreatMap(data) {
    if (!worldMap) {
        worldMap = L.map('worldMap').setView([0, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(worldMap);
    }

    if (data.location) {
        const { latitude, longitude, country } = data.location;
        const color = data.pattern_detected ? 'red' : 'blue';
        
        L.circleMarker([latitude, longitude], {
            color: color,
            fillColor: color,
            fillOpacity: 0.5,
            radius: 8
        }).addTo(worldMap)
        .bindPopup(`
            <b>${country}</b><br>
            IP: ${data.ip}<br>
            ${data.pattern_detected ? `Attack Type: ${data.attack_type}<br>
            Confidence: ${(data.confidence * 100).toFixed(1)}%` : 'Normal Traffic'}
        `);
    }
}

function updateAttackPatterns(data) {
    if (!attackHeatmap) {
        const ctx = document.getElementById('attackHeatmap');
        attackHeatmap = new Chart(ctx, {
            type: 'heatmap',
            data: {
                datasets: [{
                    data: [],
                    backgroundColor: 'rgba(255, 99, 132, 0.5)'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        type: 'time',
                        time: {
                            unit: 'hour'
                        }
                    }
                }
            }
        });
    }

    if (data.pattern_detected) {
        attackHeatmap.data.datasets[0].data.push({
            x: data.attack_type,
            y: new Date(),
            v: data.confidence
        });
        attackHeatmap.update('none');
    }
}

function showAlert(data) {
    const alertsContainer = document.getElementById('alertsContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${data.confidence > 0.8 ? 'danger' : 'warning'} alert-dismissible fade show`;
    alert.innerHTML = `
        <strong>${data.attack_type} Detected!</strong><br>
        IP: ${data.ip}<br>
        Location: ${data.location.country}<br>
        Confidence: ${(data.confidence * 100).toFixed(1)}%
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertsContainer.prepend(alert);

    // Remove alert after 10 seconds
    setTimeout(() => alert.remove(), 10000);
}

function updateThreatSummary(threats) {
    const summaryElement = document.getElementById('threatSummary');
    const activeThreats = threats.length;
    const criticalThreats = threats.filter(t => t.confidence > 0.8).length;
    
    summaryElement.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <div class="card bg-warning text-white">
                    <div class="card-body">
                        <h5>Active Threats</h5>
                        <h2>${activeThreats}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card bg-danger text-white">
                    <div class="card-body">
                        <h5>Critical Threats</h5>
                        <h2>${criticalThreats}</h2>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Initialize everything when the document loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Leaflet map
    worldMap = L.map('worldMap').setView([0, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(worldMap);

    // Initialize WebSocket connection
    initializeWebSocket();

    // Start regular dashboard updates
    updateDashboard();
    setInterval(updateDashboard, 5000);
});