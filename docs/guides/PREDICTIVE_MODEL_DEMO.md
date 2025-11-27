# Predictive Model Demo Guide

## Overview

This guide explains how to use the automated demo script to demonstrate the predictive maintenance model's capabilities. The demo script cycles through predefined scenarios showing how the model responds to different system health conditions.

## Prerequisites

1. **Dashboard must be running**: The healing dashboard API must be accessible
   ```bash
   python3 monitoring/server/healing_dashboard_api.py
   ```
   Or use the unified startup:
   ```bash
   # Start only dashboard and model
   cd /home/kasun/Documents/Heal-X-Bot
   source .venv/bin/activate
   cd monitoring/server && python3 -m uvicorn healing_dashboard_api:app --host 0.0.0.0 --port 5001 &
   cd ../../model && python3 main.py &
   ```

2. **Model must be loaded**: Ensure the predictive model is available and loaded

3. **Dashboard accessible**: Open the dashboard at http://localhost:5001

## Quick Start

### Step 1: Enable Demo Mode in Dashboard

1. Open the dashboard: http://localhost:5001
2. Navigate to the **🔮 Predictive Maintenance** tab
3. **Enable "Demo Mode"** checkbox (top right)

### Step 2: Run the Demo Script

**Basic usage (runs all scenarios once):**
```bash
python3 scripts/demo-predictive-model.py
```

**Continuous loop:**
```bash
python3 scripts/demo-predictive-model.py --loop
```

**Interactive mode (choose scenarios manually):**
```bash
python3 scripts/demo-predictive-model.py --interactive
```

**Run specific scenario:**
```bash
python3 scripts/demo-predictive-model.py --scenario low
python3 scripts/demo-predictive-model.py --scenario medium
python3 scripts/demo-predictive-model.py --scenario high
python3 scripts/demo-predictive-model.py --scenario extreme
```

**Custom delay between scenarios:**
```bash
python3 scripts/demo-predictive-model.py --delay 10  # 10 seconds between scenarios
```

## Demo Scenarios

The script includes four predefined scenarios that demonstrate different risk levels:

### 1. Low Risk - Healthy System

**Metrics:**
- CPU: 15.5%
- Memory: 35.2%
- Disk: 42.8%
- Errors: 0
- Warnings: 1
- Service Failures: 0

**Expected Behavior:**
- Risk Score: Very Low (< 5%)
- No failure predicted
- Minimal or no early warnings
- System appears healthy

**Use Case:** Demonstrates normal operation

### 2. Medium Risk - Elevated Load

**Metrics:**
- CPU: 68.3%
- Memory: 75.6%
- Disk: 80.2%
- Errors: 3
- Warnings: 8
- Service Failures: 0

**Expected Behavior:**
- Risk Score: Low to Medium (10-30%)
- Possible early warnings for resource usage
- System requires monitoring
- Time-to-failure may be estimated (if risk > 50%)

**Use Case:** Shows how model detects elevated load conditions

### 3. High Risk - Critical Conditions

**Metrics:**
- CPU: 89.7%
- Memory: 92.3%
- Disk: 93.5%
- Errors: 15
- Warnings: 32
- Service Failures: 2

**Expected Behavior:**
- Risk Score: High (50-80%)
- Multiple early warnings
- Time-to-failure prediction likely
- Immediate attention required

**Use Case:** Demonstrates critical system stress detection

### 4. Extreme Risk - Near Failure

**Metrics:**
- CPU: 97.8%
- Memory: 98.5%
- Disk: 99.1%
- Errors: 45
- Warnings: 89
- Service Failures: 5

**Expected Behavior:**
- Risk Score: Critical (> 80%)
- Multiple high-severity warnings
- Time-to-failure prediction (short hours)
- System near failure point

**Use Case:** Shows near-failure conditions and urgent predictions

## What to Observe

When running the demo, watch for:

### 1. Risk Score Changes
- **Dashboard**: Risk percentage updates in real-time
- **Progress Bar**: Visual indicator fills based on risk level
- **Risk Level**: Text changes (Very Low → Low → Medium → High)

### 2. Time-to-Failure Predictions
- **Hours Until Failure**: Shows estimated time (or "--" if no failure predicted)
- **Predicted Failure Time**: Date/time when failure is expected
- **Confidence Level**: High/Medium/Low confidence in prediction

### 3. Early Warnings
- **Warning Count**: Number increases with higher risk scenarios
- **Warning List**: Details of specific issues detected
- **Severity Levels**: High/Medium severity warnings

### 4. Model Details Section
- Click "Show Details" to see:
  - Full API responses (JSON formatted)
  - System metrics used for prediction
  - Model status and mode
  - All prediction data

### 5. Scenario Name Display
- In demo mode, the current scenario name appears above the cards
- Updates automatically as scenarios change

## Demo Flow

1. **Script sends metrics** → Dashboard API (`/api/predict-failure-risk-custom`)
2. **Dashboard receives metrics** → Stores for demo mode
3. **Dashboard polls metrics** → Refreshes predictions every second
4. **Predictions update** → Risk score, time-to-failure, warnings
5. **Model Details section** → Shows all API responses

## Troubleshooting

### Dashboard not responding

**Error:** `❌ Cannot connect to dashboard API`

**Solution:**
```bash
# Check if dashboard is running
curl http://localhost:5001/

# Start dashboard if not running
cd monitoring/server
python3 -m uvicorn healing_dashboard_api:app --host 0.0.0.0 --port 5001
```

### Demo Mode not working

**Issue:** Predictions don't update when running script

**Solution:**
1. Ensure "Demo Mode" checkbox is enabled in dashboard
2. Check browser console for errors
3. Verify script is sending metrics (check script output)
4. Check dashboard logs: `logs/Healing Dashboard API.log`

### Predictions not changing

**Issue:** Risk score stays the same across scenarios

**Possible causes:**
1. Model not loaded correctly
2. Metrics not reaching the API
3. Dashboard not polling for demo metrics

**Solution:**
1. Check Model Details section - verify model status is "Active"
2. Check browser console for API errors
3. Verify `/api/get-last-demo-metrics` returns metrics
4. Manually refresh dashboard predictions

### Wrong scenario detected

**Issue:** Scenario name doesn't match actual metrics

**Solution:**
- Scenario detection is automatic based on metrics thresholds
- CPU/Memory/Disk > 95% = Extreme
- CPU/Memory/Disk > 85%/90% = High
- CPU/Memory/Disk > 60%/70%/75% = Medium
- Otherwise = Low

## Command Line Options

```
--interactive, -i      Run in interactive mode (manual scenario selection)
--loop, -l             Continuously loop through all scenarios
--scenario SCENARIO    Run a specific scenario (low/medium/high/extreme)
--delay DELAY, -d      Delay between scenarios in seconds (default: 5.0)
--url URL              Dashboard URL (default: http://localhost:5001)
```

## Examples

**Full automated demo with 10-second delays:**
```bash
python3 scripts/demo-predictive-model.py --delay 10
```

**Continuous loop for extended demonstration:**
```bash
python3 scripts/demo-predictive-model.py --loop --delay 7
```

**Quick test of high-risk scenario:**
```bash
python3 scripts/demo-predictive-model.py --scenario high --delay 0
```

**Custom dashboard URL:**
```bash
python3 scripts/demo-predictive-model.py --url http://192.168.1.100:5001
```

## Interpreting Results

### Risk Scores

- **0-10% (Very Low)**: System healthy, no action needed
- **10-30% (Low)**: Monitor conditions, no immediate risk
- **30-50% (Medium)**: Elevated risk, review system resources
- **50-70% (Medium-High)**: High risk, proactive action recommended
- **70-100% (High/Critical)**: Critical risk, immediate intervention needed

### Time-to-Failure

- **No prediction (null)**: Risk too low to predict failure
- **24+ hours**: System stable, plenty of time to address issues
- **12-24 hours**: Moderate urgency, plan intervention soon
- **1-12 hours**: High urgency, take action within hours
- **< 1 hour**: Critical urgency, immediate action required

### Early Warnings

- **0 warnings**: System healthy
- **1-3 warnings**: Minor issues, monitor
- **4-10 warnings**: Multiple concerns, investigate
- **10+ warnings**: Critical issues, immediate attention

## Best Practices

1. **Always enable Demo Mode** in dashboard before running script
2. **Start with a single scenario** to verify everything works
3. **Watch the dashboard** while script runs to see real-time updates
4. **Use Model Details section** to verify API responses
5. **Run in loop mode** for continuous demonstrations
6. **Adjust delays** based on audience - longer delays give more time to observe

## Integration with Presentations

For presentations or demos:

1. **Prepare dashboard** - Open in full screen, navigate to Predictive Maintenance tab
2. **Enable Demo Mode** - Toggle the checkbox
3. **Show Model Details** - Click "Show Details" to display technical information
4. **Run script in loop** - Use `--loop --delay 8` for smooth transitions
5. **Explain each scenario** as it appears on screen
6. **Highlight changes** in risk score, warnings, and predictions

## Technical Details

**API Endpoints Used:**
- `POST /api/predict-failure-risk-custom` - Sends metrics and gets risk prediction
- `GET /api/predict-time-to-failure` - Gets time-to-failure prediction
- `GET /api/get-early-warnings` - Gets early warning indicators
- `GET /api/get-last-demo-metrics` - Dashboard polls this for demo metrics

**Metrics Format:**
```json
{
  "cpu_percent": 68.3,
  "memory_percent": 75.6,
  "disk_percent": 80.2,
  "error_count": 3,
  "warning_count": 8,
  "service_failures": 0,
  "network_in_mbps": 45.8,
  "network_out_mbps": 32.4
}
```

**Dashboard Polling:**
- When Demo Mode is enabled, dashboard polls `/api/get-last-demo-metrics` every 1 second
- This ensures real-time updates as script sends new metrics

## Support

For issues or questions:
- Check dashboard logs: `logs/Healing Dashboard API.log`
- Check script output for error messages
- Verify API endpoints are accessible
- Ensure model is loaded correctly

## Next Steps

After running the demo:
1. Review the Model Details section to see all predictions
2. Understand how metrics affect risk scores
3. Experiment with custom scenarios by modifying the script
4. Use this knowledge to interpret real-world predictions

