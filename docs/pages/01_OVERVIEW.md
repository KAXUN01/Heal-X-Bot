# Overview Page

## Description
The Overview page serves as the main dashboard and central monitoring hub for the Heal-X system. It provides real-time visibility into system health, resource utilization, and key performance metrics at a glance.

## Purpose
- Provide instant visibility into overall system health
- Display real-time CPU, Memory, and Disk usage metrics
- Show quick summary of active issues and alerts
- Act as a navigation starting point for deeper investigation

## Features

### 1. System Health Indicator
- **Location**: Top bar
- **Displays**: Overall system status (Healthy/Warning/Critical)
- **Color coding**: 
  - 🟢 Green = Healthy
  - 🟡 Yellow = Warning
  - 🔴 Red = Critical

### 2. Resource Metrics Cards
Four main metric cards displaying:

| Metric | Description | Threshold Colors |
|--------|-------------|------------------|
| **CPU Usage** | Current processor utilization | Green < 70%, Yellow 70-90%, Red > 90% |
| **Memory Usage** | RAM utilization percentage | Green < 80%, Yellow 80-90%, Red > 90% |
| **Disk Usage** | Storage space utilization | Green < 80%, Yellow 80-95%, Red > 95% |
| **Network I/O** | Bytes sent/received | Informational |

### 3. Quick Statistics
- Total active faults
- Healing success rate
- Services running
- Recent alert count

### 4. Mini Charts
- Real-time CPU trend graph
- Memory usage trend graph
- Network throughput visualization

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stats` | GET | Fetch quick statistics |
| `/api/system/basic-metrics` | GET | Get CPU, Memory, Disk metrics |
| `/api/healing/status` | GET | Get healing system status |

## Technical Implementation

### Data Refresh
- **Interval**: 5 seconds
- **Function**: `updateStatistics()`
- **Metrics Source**: psutil (Python system monitoring)

### JavaScript Functions
```javascript
updateStatistics()      // Refresh all overview metrics
fetchSystemMetrics()    // Get CPU/Memory/Disk data
updateResourceCards()   // Update metric card visuals
```

## User Actions
- Click on any metric card to navigate to detailed view
- Hover over charts for specific data points
- View last update timestamp

## Background Details

### Data Sources
1. **psutil library**: CPU, Memory, Disk metrics
2. **FaultDetector**: Active issues count
3. **Auto-healer**: Healing statistics
4. **Docker API**: Container service count

### Metric Calculation
- CPU: `psutil.cpu_percent(interval=None)` - non-blocking
- Memory: `psutil.virtual_memory().percent`
- Disk: `psutil.disk_usage('/').percent`

## Related Pages
- [Active Alerts](02_ACTIVE_ALERTS.md) - Detailed alert view
- [Processes](05_PROCESSES.md) - CPU/Memory by process
- [Services](04_SERVICES.md) - Service status details
