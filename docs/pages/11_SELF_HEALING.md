# Self-Healing Page (Autonomous Healing System)

## Description
The Self-Healing page showcases the autonomous fault detection and resolution system. It automatically detects system issues, analyzes root causes using AI, and applies remediation actions without human intervention.

## Purpose
- Automatically detect system faults
- Analyze issues using AI (Gemini/Groq)
- Apply remediation actions
- Visualize healing process
- Track healing history and statistics

## Features

### 1. Demo Mode Toggle
- Enable/disable demo mode for testing
- Triggers simulated faults
- Demonstrates healing workflow

### 2. Healing Process Visualization
Five-step process flow:

| Step | Icon | Description | Status Colors |
|------|------|-------------|---------------|
| 1. Fault Detected | ⚠️ | Issue identified | Gray → Yellow → Green |
| 2. AI Analysis | 🧠 | Root cause analysis | Gray → Blue → Green |
| 3. Solution Generated | 💡 | Fix determined | Gray → Purple → Green |
| 4. Healing Applied | 🔧 | Action executed | Gray → Orange → Green |
| 5. Verified | ✅ | Success confirmed | Gray → Green |

### 3. Active Faults Panel
Current issues detected:
- Fault type and severity
- Affected service/component
- Detection timestamp
- Status (detected/analyzing/healing/healed)
- AI Analysis button
- Auto-Heal button

### 4. Healing Statistics
- Total issues healed
- Success rate percentage
- Average healing time
- Failed healings count

### 5. Healing History
Log of all healing actions:
- Fault description
- Resolution applied
- Duration
- Status (success/failed)
- Timestamp

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cloud/faults` | GET | Get active faults |
| `/api/cloud/faults/{id}/analyze` | POST | AI analyze fault |
| `/api/cloud/faults/{id}/heal` | POST | Apply healing |
| `/api/healing/status` | GET | Get healing status |
| `/api/healing/history` | GET | Get healing history |
| `/api/healing/config` | GET/POST | Configuration |

## Fault Detection

### Supported Fault Types
```python
fault_types = [
    'service_failure',      # Service stopped/crashed
    'cpu_exhaustion',       # High CPU usage
    'memory_exhaustion',    # High memory usage
    'disk_space_critical',  # Low disk space
    'network_issue',        # Connectivity problems
    'container_crash',      # Docker container failures
    'process_hang',         # Unresponsive processes
    'port_unavailable',     # Service port not responding
]
```

### Detection Sources
1. **FaultDetector**: Monitors services and resources
2. **ContainerMonitor**: Docker container health
3. **ServiceMonitor**: Systemd service status
4. **ResourceAlerts**: Threshold-based detection

## AI Analysis

### Gemini/Groq Integration
```python
async def analyze_fault(fault_data):
    prompt = f"""
    Analyze this system fault and provide:
    1. Root cause analysis
    2. Step-by-step remediation commands
    3. Prevention recommendations
    
    Fault: {fault_data['type']}
    Service: {fault_data['service']}
    Message: {fault_data['message']}
    Metrics: {fault_data['metrics']}
    """
    
    response = await ai_analyzer.analyze(prompt)
    return {
        'root_cause': response.root_cause,
        'commands': response.commands,
        'explanation': response.explanation
    }
```

### Analysis Output
```json
{
  "root_cause": "Service container ran out of memory due to memory leak",
  "confidence": 0.85,
  "commands": [
    "docker restart healing-dashboard",
    "docker stats --no-stream"
  ],
  "explanation": "The container exceeded its memory limit...",
  "prevention": "Configure memory limits and implement health checks"
}
```

## Healing Actions

### Supported Actions
```python
healing_actions = {
    'service_restart': 'docker restart {service}',
    'container_restart': 'docker restart {container}',
    'process_kill': 'kill -9 {pid}',
    'cache_clear': 'sync; echo 3 > /proc/sys/vm/drop_caches',
    'disk_cleanup': 'apt-get clean && journalctl --vacuum-time=1d',
    'service_start': 'systemctl start {service}',
    'port_free': 'fuser -k {port}/tcp',
}
```

### Healing Execution
```python
async def execute_healing(fault, commands):
    results = []
    for cmd in commands:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True)
            results.append({
                'command': cmd,
                'success': result.returncode == 0,
                'output': result.stdout.decode()
            })
        except Exception as e:
            results.append({'command': cmd, 'success': False, 'error': str(e)})
    
    # Verify healing
    verified = await verify_healing(fault)
    
    return {
        'success': all(r['success'] for r in results) and verified,
        'results': results
    }
```

## Technical Implementation

### Process Flow
```
1. Fault Detection
   └── FaultDetector monitors services/resources
   
2. Fault Classification
   └── Categorize by type and severity
   
3. AI Analysis (if enabled)
   └── Gemini/Groq provides root cause and commands
   
4. Healing Execution
   └── Execute remediation commands
   
5. Verification
   └── Check if issue is resolved
   
6. Notification
   └── Send Discord alert with results
```

### JavaScript Functions
```javascript
updateActiveFaults()         // Fetch active faults
autoHealFault(faultId)       // Trigger auto-healing
analyzeFaultWithAI(faultId)  // Get AI analysis
toggleAutoHealingDemo()      // Toggle demo mode
activateStep(stepId)         // Animate process step
showHealingResult(result)    // Display result modal
```

### Demo Mode
```javascript
function startDemoMode() {
    // Create simulated fault
    const demoFault = {
        id: 'demo-' + Date.now(),
        type: 'service_failure',
        service: 'demo-service',
        message: 'Demo fault for testing'
    };
    
    // Animate through healing steps
    animateHealingProcess(demoFault);
}
```

## Configuration

### Healing Config
```json
{
  "auto_healing": {
    "enabled": true,
    "auto_execute": false,
    "require_approval": true,
    "max_attempts": 3,
    "cooldown_seconds": 300,
    "ai_analysis": true
  }
}
```

## User Actions
- Toggle demo mode
- View active faults
- Analyze faults with AI
- Trigger auto-healing
- View healing history
- Configure healing settings

## Related Pages
- [Active Alerts](02_ACTIVE_ALERTS.md) - Fault alerts
- [Services](04_SERVICES.md) - Service management
- [Logs & AI](07_LOGS_AI.md) - AI analysis
- [Predictive Maintenance](08_PREDICTIVE_MAINTENANCE.md) - Failure prediction
