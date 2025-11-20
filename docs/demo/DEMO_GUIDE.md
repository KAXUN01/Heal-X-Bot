# AI Bot Prototype - Demo Guide

## Overview

This guide demonstrates the complete AI Bot prototype that autonomously detects, diagnoses, and heals system faults in a simulated cloud environment.

## Prerequisites

1. **Docker and Docker Compose** installed
2. **Python 3.8+** with required dependencies
3. **Discord Webhook** (optional, for notifications)
4. **Gemini API Key** (optional, for AI analysis)

## Quick Start

### 1. Start the System

```bash
# Start the healing bot system
python3 run-healing-bot.py

# Or start individual services
python3 monitoring/server/healing_dashboard_api.py  # Dashboard API (port 5001)
python3 monitoring/server/app.py                    # Monitoring Server (port 5000)
```

### 2. Start Cloud Simulation

```bash
# Start simulated cloud services (try newer syntax first)
docker compose -f config/docker-compose-cloud-sim.yml up -d

# Or use older syntax
docker-compose -f config/docker-compose-cloud-sim.yml up -d

# Or use the setup script
./scripts/setup/init-cloud-sim.sh
```

### 3. Run Automated Demo

```bash
# Run the complete automated demonstration
python3 run-demo.py
```

This will:
- Start cloud simulation services
- Inject a service crash fault
- Show real-time detection
- Display AI diagnosis
- Demonstrate automatic healing
- Show verification results

## Manual Testing

### Inject Specific Faults

```bash
# Service crash
python3 scripts/demo/manual-fault-trigger.py --type crash --container cloud-sim-api-server

# CPU exhaustion
python3 scripts/demo/manual-fault-trigger.py --type cpu --duration 60

# Memory exhaustion
python3 scripts/demo/manual-fault-trigger.py --type memory --size 2.0

# Disk full
python3 scripts/demo/manual-fault-trigger.py --type disk --size 5.0

# Network issue
python3 scripts/demo/manual-fault-trigger.py --type network --container cloud-sim-api-server --port 8082
```

### Using the Dashboard

1. Open http://localhost:5001
2. Navigate to the **☁️ Cloud Simulation** tab
3. Use the fault injection buttons to inject faults
4. Watch real-time detection, diagnosis, and healing

## Dashboard Visualizations

The Cloud Simulation tab provides 8 comprehensive visualizations:

### 1. Service Status Dashboard
- Grid view of all cloud services
- Color-coded health indicators
- Real-time container status
- Resource usage per service

### 2. Fault Detection Timeline
- Real-time fault detection feed
- Fault type and severity indicators
- Detection timestamps
- Click to view details

### 3. AI Diagnosis Display
- Root cause analysis results
- Confidence scores with progress bars
- Pattern recognition insights
- AI reasoning explanations

### 4. Self-Healing Action Log
- Step-by-step healing actions
- Action status indicators
- Healing attempt history
- Expandable action details

### 5. Discord Notification Status
- Notification history feed
- Sent/received indicators
- Notification content preview
- Link to Discord channel

### 6. Resource Monitoring Charts
- Real-time CPU usage chart
- Memory usage chart
- Disk usage chart
- Network traffic visualization

### 7. Healing Statistics Dashboard
- Success/failure rates
- Average healing time
- Most common fault types
- Healing attempts over time

### 8. Manual Instructions Panel
- Step-by-step healing guides
- Displayed when auto-healing fails
- Copy-to-clipboard functionality
- Visual indicators for manual intervention

## API Endpoints

### Fault Detection
```bash
# Get detected faults
GET /api/cloud/faults?limit=50

# Get fault statistics
GET /api/cloud/faults
```

### Fault Injection
```bash
# Inject service crash
POST /api/cloud/faults/inject
{
  "type": "crash",
  "container": "cloud-sim-api-server"
}

# Inject CPU exhaustion
POST /api/cloud/faults/inject
{
  "type": "cpu",
  "duration": 60
}
```

### Healing
```bash
# Get healing history
GET /api/cloud/healing/history?limit=50

# Manually trigger healing
POST /api/cloud/faults/{fault_id}/heal
```

### Service Status
```bash
# Get cloud services status
GET /api/cloud/services/status

# Get resource metrics
GET /api/cloud/resources
```

## WebSocket Real-time Updates

Connect to `/ws/faults` for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:5001/ws/faults');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'faults_update') {
        // Update fault detection UI
    } else if (data.type === 'healing_update') {
        // Update healing actions UI
    }
};
```

## Expected Behavior

### Service Crash Scenario

1. **Fault Injection**: Container is stopped
2. **Detection** (within 30 seconds):
   - Fault detector identifies stopped container
   - Discord notification sent immediately
   - Dashboard shows fault in timeline
3. **Diagnosis**:
   - Root cause analyzer identifies cause
   - AI provides analysis with confidence score
   - Dashboard displays diagnosis
4. **Healing**:
   - Auto-healer attempts container restart
   - Discord notification sent for healing attempt
   - Dashboard shows healing actions
5. **Verification**:
   - System verifies container is running
   - Discord notification sent with result
   - Dashboard updates service status

### Resource Exhaustion Scenario

1. **Fault Injection**: CPU/Memory/Disk stress applied
2. **Detection**: Resource monitor detects threshold exceeded
3. **Diagnosis**: AI identifies resource exhaustion cause
4. **Healing**: System kills resource hogs, clears caches
5. **Verification**: Resource usage returns to normal

## Troubleshooting

### Services Not Starting

```bash
# Check Docker
docker ps

# Check logs (try newer syntax first)
docker compose -f config/docker-compose-cloud-sim.yml logs
# Or older syntax
docker-compose -f config/docker-compose-cloud-sim.yml logs

# Restart services
docker compose -f config/docker-compose-cloud-sim.yml restart
# Or
docker-compose -f config/docker-compose-cloud-sim.yml restart
```

### Faults Not Detected

- Check fault detector is running: `GET /api/cloud/faults`
- Verify monitoring interval (default: 30 seconds)
- Check container names match expected patterns

### Healing Not Working

- Check auto-healer is enabled: `GET /api/auto-healer/status`
- Verify Docker permissions (may need sudo)
- Check healing history: `GET /api/cloud/healing/history`

### Dashboard Not Updating

- Check WebSocket connection in browser console
- Verify API endpoints are accessible
- Check browser console for errors

## Configuration

### Enable/Disable Auto-Healing

Edit `monitoring/server/auto_healer.py`:
```python
self.enabled = True  # Enable/disable auto-healer
self.auto_execute = True  # Auto-execute or require approval
```

### Discord Notifications

Set in `.env` file:
```env
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
```

### Monitoring Intervals

Edit in respective files:
- Fault detection: `fault_detector.py` (default: 30s)
- Auto-healing: `auto_healer.py` (default: 60s)

## Success Criteria

✅ System detects faults within 30 seconds  
✅ AI correctly diagnoses root cause (80%+ accuracy)  
✅ System automatically heals 70%+ of faults  
✅ Manual instructions provided when auto-healing fails  
✅ All actions logged and explained in console + dashboard  
✅ Discord notifications sent immediately when service crashes detected  
✅ Dashboard visualizes ALL activities in real-time  
✅ Demo script successfully demonstrates full cycle

## Next Steps

1. **Customize Fault Types**: Add new fault types in `fault_injector.py`
2. **Enhance Healing Actions**: Add new healing methods in `auto_healer.py`
3. **Improve AI Analysis**: Enhance prompts in `gemini_log_analyzer.py`
4. **Add More Services**: Extend `docker-compose-cloud-sim.yml`
5. **Create Custom Dashboards**: Extend visualization components

## Support

For issues or questions:
- Check logs: `logs/monitoring-server.log`
- Review documentation: `docs/` directory
- Check API health: `GET /api/health`

