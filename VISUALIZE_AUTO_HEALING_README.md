# Autonomous Self-Healing Feature Visualization Script

## Overview

The `visualize_auto_healing.py` script provides a comprehensive visualization and verification tool for the autonomous self-healing system. It tests all components, verifies dashboard updates, and demonstrates the complete workflow.

## Features

### ✅ Complete System Verification

The script performs 10 comprehensive steps:

1. **Server Connection Check** - Verifies the dashboard server is running
2. **Auto-Healer Status** - Checks if auto-healer is initialized and configured
3. **Configuration Check** - Retrieves and displays current configuration
4. **Fault Detection** - Lists all detected active faults
5. **Healing History** - Shows recent healing actions and results
6. **Statistics** - Displays healing success rates and metrics
7. **Fault Injection Test** - Tests fault injection capability (if available)
8. **Manual Healing Test** - Tests manual healing trigger (if faults available)
9. **Dashboard Endpoints** - Verifies all dashboard data endpoints
10. **Configuration Update** - Tests configuration update functionality

### 🎨 Visual Output

- Color-coded status indicators (✅ Success, ⚠️ Warning, ❌ Error)
- Step-by-step progress display
- Detailed component status
- Summary report with key findings

## Requirements

```bash
pip install requests colorama
```

Or if colorama is not available, the script will work without colors.

## Usage

### Basic Usage

```bash
python3 visualize_auto_healing.py
```

### Prerequisites

1. **Start the Dashboard Server**
   ```bash
   python3 monitoring/server/healing_dashboard_api.py
   ```
   
   The server should be running on `http://localhost:5001` (default port).
   
   You can override the port by setting the `HEALING_DASHBOARD_PORT` environment variable:
   ```bash
   export HEALING_DASHBOARD_PORT=8000
   python3 visualize_auto_healing.py
   ```

2. **Ensure Auto-Healer is Initialized**
   - The auto-healer should be initialized when the server starts
   - If not initialized, the script will show warnings but continue testing

## Output Example

```
================================================================================
          AUTONOMOUS SELF-HEALING FEATURE VISUALIZATION
================================================================================

[Step 1] Checking Server Connection
ℹ️  Connecting to http://localhost:8000...
✅ Server is running and responding

[Step 2] Checking Auto-Healer Status
✅ Auto-healer is initialized
ℹ️    Enabled: True
ℹ️    Auto-execute: True
ℹ️    Monitoring: True
ℹ️    Max attempts: 3

[Step 3] Checking Auto-Healing Configuration
✅ Configuration retrieved
ℹ️    Enabled: True
ℹ️    Auto-execute: True
ℹ️    Monitoring interval: 60s
ℹ️    Max attempts: 3

[Step 4] Checking Detected Faults
✅ Found 2 active fault(s)
ℹ️    Total faults detected: 5
ℹ️    Active faults: 2
ℹ️    Resolved faults: 3

[Step 5] Checking Healing History
✅ Found 10 healing record(s) in history
ℹ️    Recent Healing Actions:
ℹ️      1. ✅ [healed] service_down - 2025-01-20T10:30:00
ℹ️      2. ✅ [healed] high_cpu - 2025-01-20T10:25:00

[Step 6] Checking Healing Statistics
✅ Statistics retrieved
ℹ️    Total attempts: 25
ℹ️    Successful: 20
ℹ️    Failed: 5
ℹ️    Success rate: 80.0%

[Step 7] Testing Fault Injection
✅ Test fault injected successfully
ℹ️    Fault ID: fault_12345

[Step 8] Testing Manual Healing
✅ Manual healing triggered
ℹ️    Healing status: healed

[Step 9] Verifying Dashboard Data Endpoints
✅ System Metrics: ✅ Working
✅ Services Status: ✅ Working
✅ Critical Issues: ✅ Working
✅ Top Processes: ✅ Working

[Step 10] Testing Configuration Update
✅ Configuration updated successfully
ℹ️    Original configuration restored

================================================================================
                            VISUALIZATION SUMMARY
================================================================================

Component Status:

  ✅ Server Connection: Working
  ✅ Auto-Healer Status: Working
  ✅ Fault Detector: Working
  ✅ Healing History: Working
  ✅ Dashboard Endpoints: Working

Key Findings:

ℹ️  Auto-healer is enabled
ℹ️  Auto-execute is enabled
ℹ️  Active faults detected: 2
ℹ️  Healing history records: 10
ℹ️  Total healing attempts: 25
ℹ️  Success rate: 80.0%

Dashboard Status:

ℹ️  All dashboard endpoints are being monitored
ℹ️  Real-time updates are configured for active tabs
ℹ️  Auto-healing tab refreshes every 10 seconds when active
ℹ️  Configuration refreshes every 30 seconds when active

================================================================================
                        VISUALIZATION COMPLETE
================================================================================
```

## What It Verifies

### 1. Server Connectivity
- Checks if the dashboard server is running
- Verifies API endpoints are accessible

### 2. Auto-Healer Components
- Initialization status
- Configuration settings
- Monitoring status

### 3. Fault Detection System
- Active faults
- Fault statistics
- Fault injection capability

### 4. Healing System
- Healing history
- Success/failure rates
- Manual healing triggers

### 5. Dashboard Integration
- All data endpoints
- Real-time update mechanisms
- Configuration management

## Troubleshooting

### Server Not Running

**Error:** `Connection refused - Is the server running on port 5001?`

**Solution:**
```bash
python3 monitoring/server/healing_dashboard_api.py
```

### Auto-Healer Not Initialized

**Warning:** `Auto-healer is not initialized`

**Solution:**
- This is normal if auto-healer hasn't been started
- The script will continue testing other components
- Check server logs for initialization errors

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
- Check if another instance is running: `lsof -i :5001`
- Kill the process or use a different port
- Set `HEALING_DASHBOARD_PORT` environment variable if using a different port

## Integration with Dashboard

The script verifies that:

1. **Dashboard Updates Correctly**
   - All endpoints return valid data
   - Real-time updates are configured
   - Periodic refreshes are working

2. **Auto-Healing Tab Works**
   - Status cards display correctly
   - Configuration form is functional
   - Healing history timeline updates
   - Active faults are displayed

3. **Data Flow**
   - Backend → Frontend data transfer
   - WebSocket updates (if enabled)
   - Error handling and fallbacks

## Next Steps

After running the visualization script:

1. **Open the Dashboard**
   ```
   http://localhost:5001/static/healing-dashboard.html
   ```

2. **Navigate to Auto-Healing Tab**
   - Click on "Autonomous Self-Healing" tab
   - Verify all components match script output

3. **Monitor Real-Time Updates**
   - Watch for periodic refreshes (every 10 seconds)
   - Check healing history for new entries
   - Monitor active faults list

4. **Test Configuration Changes**
   - Toggle auto-healing enabled/disabled
   - Change monitoring interval
   - Update max attempts

## Script Configuration

You can modify these variables in the script:

The script automatically detects the port from the `HEALING_DASHBOARD_PORT` environment variable (defaults to 5001).

You can override it:
```bash
export HEALING_DASHBOARD_PORT=8000
python3 visualize_auto_healing.py
```

Or modify the script:
```python
DEFAULT_PORT = 8000  # Change this if needed
```

## Exit Codes

- `0` - Success (all checks completed)
- `1` - Server not running or critical error

## Notes

- The script is non-destructive (doesn't modify system state)
- Configuration changes are tested and then restored
- Fault injection tests are optional and safe
- All tests are read-only except configuration update test (which is restored)

## Support

For issues or questions:
1. Check server logs: `logs/Healing Dashboard API.log`
2. Verify server is running: `curl http://localhost:5001/api/metrics`
3. Check auto-healer initialization in server startup logs
4. Check which port the server is using: `lsof -i :5001` or check server startup logs

