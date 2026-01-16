# Processes Page (Resource Hog Detection)

## Description
The Processes page provides real-time monitoring of system processes with a focus on detecting and managing resource-intensive "hog" processes that consume excessive CPU, memory, or other system resources.

## Purpose
- Identify resource-hogging processes
- Monitor CPU and memory usage per process
- Kill or limit problematic processes
- Configure resource thresholds

## Features

### 1. Process List
Displays all running processes sorted by resource consumption:

| Column | Description |
|--------|-------------|
| **Process Name** | Executable name |
| **CPU %** | Current CPU utilization |
| **Memory %** | Current memory usage |
| **PID** | Process identifier |
| **Actions** | Kill/Limit buttons |

### 2. Resource Threshold Configuration
- **CPU Threshold**: Default 80%
- **Memory Threshold**: Default 75%
- Processes exceeding thresholds are highlighted

### 3. Process Actions
- **Refresh**: Update process list
- **Configure**: Set resource thresholds
- **Kill**: Terminate a process
- **Priority**: Adjust process priority (nice value)

### 4. Visual Indicators

| Usage Level | CPU | Memory | Indicator |
|-------------|-----|--------|-----------|
| Normal | < 50% | < 50% | Green bar |
| Elevated | 50-80% | 50-75% | Yellow bar |
| Critical | > 80% | > 75% | Red bar |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/processes` | GET | List all processes |
| `/api/processes/hogs` | GET | Get resource hogs |
| `/api/processes/{pid}/kill` | POST | Kill a process |
| `/api/processes/config` | GET/POST | Threshold settings |

## Process Detection

### Resource Hog Detection
```python
def get_resource_hogs(cpu_threshold=80, mem_threshold=75):
    hogs = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        if proc.info['cpu_percent'] > cpu_threshold or \
           proc.info['memory_percent'] > mem_threshold:
            hogs.append(proc.info)
    return hogs
```

### Sorting Options
- By CPU usage (descending)
- By Memory usage (descending)
- By PID
- By Name (alphabetical)

## Technical Implementation

### Process Monitoring
```python
import psutil

for proc in psutil.process_iter():
    try:
        info = proc.as_dict(attrs=['pid', 'name', 'cpu_percent', 
                                    'memory_percent', 'status'])
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue
```

### Kill Process
```python
def kill_process(pid):
    try:
        proc = psutil.Process(pid)
        proc.terminate()  # Graceful termination
        proc.wait(timeout=5)
    except psutil.TimeoutExpired:
        proc.kill()  # Force kill
```

### JavaScript Functions
```javascript
refreshProcesses()        // Update process list
openThresholdConfig()     // Open configuration modal
killProcess(pid)          // Terminate a process
sortProcesses(column)     // Sort by column
```

## Configuration Modal

### Threshold Settings
```json
{
  "cpu_threshold": 80,
  "memory_threshold": 75,
  "auto_kill": false,
  "whitelist": ["systemd", "kernel"],
  "refresh_interval": 5000
}
```

### Whitelisted Processes
Certain system-critical processes are protected from being killed:
- init, systemd
- kernel threads
- Docker daemon
- System monitoring agents

## User Actions
- Refresh process list manually
- Configure CPU/Memory thresholds
- Kill problematic processes
- Sort and filter process list
- View process details

## Alerts Integration
When a resource hog is detected:
1. Process is highlighted in red
2. Alert is created
3. Discord notification sent
4. Auto-healing may be triggered

## Related Pages
- [Overview](01_OVERVIEW.md) - System resource summary
- [Services](04_SERVICES.md) - Service-level view
- [Self-Healing](11_SELF_HEALING.md) - Automatic remediation
- [Auto Scaling](10_AUTO_SCALING.md) - Resource scaling
