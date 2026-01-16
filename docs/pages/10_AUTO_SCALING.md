# Auto Scaling Page

## Description
The Auto Scaling page provides resource-based automatic scaling capabilities for Docker containers. It monitors system resources and suggests or automatically applies scaling configurations based on predefined templates.

## Purpose
- Monitor CPU and Memory usage in real-time
- Detect critical resource conditions
- Suggest scaling actions with admin approval
- Apply scaling templates to Docker Compose
- Maintain scaling history for audit

## Features

### 1. Current Resource Status
Real-time resource monitoring:

| Metric | Display | Threshold |
|--------|---------|-----------|
| **CPU Usage** | Percentage + progress bar | 90% |
| **Memory Usage** | Percentage + progress bar | 95% |
| **Status Indicator** | Green/Red dot | Based on thresholds |
| **Critical Duration** | Time in critical state | Tracked |

### 2. Pending Scaling Suggestions
When resource thresholds are exceeded:
- Template name suggested
- Reason for suggestion
- Current metrics display
- Creation timestamp
- **Approve** / **Reject** buttons

### 3. Manual Scaling
- Template selection dropdown
- Preview of changes
- Scale Now button
- Confirmation dialog

### 4. Scaling Templates
Pre-defined resource configurations:

| Template | CPU Cores | Memory | Description |
|----------|-----------|--------|-------------|
| **Low** | 1 | 2 GB | Minimal resources |
| **Medium** | 2 | 4 GB | Balanced (default) |
| **High** | 4 | 8 GB | Maximum resources |

### 5. Scaling History
Log of all scaling actions:
- Type (manual/approved/rejected)
- Template used
- Status (completed/failed)
- Triggered by
- Timestamp

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scaling/status` | GET | Get current scaling status |
| `/api/scaling/templates` | GET | List scaling templates |
| `/api/scaling/templates` | POST | Create new template |
| `/api/scaling/templates/{id}` | DELETE | Delete template |
| `/api/scaling/approve` | POST | Approve/reject suggestion |
| `/api/scaling/manual` | POST | Execute manual scaling |
| `/api/scaling/history` | GET | Get scaling history |

## Scaling Templates

### Template Structure
```json
{
  "id": "high",
  "name": "High Resources",
  "description": "Maximum resource allocation",
  "cpu_cores": 4,
  "memory_gb": 8,
  "services": {
    "model": {"cpus": "2", "memory": "4G"},
    "server": {"cpus": "1", "memory": "2G"}
  }
}
```

### Default Templates
```python
default_templates = [
    {
        'id': 'low',
        'name': 'Low Resources',
        'cpu_cores': 1,
        'memory_gb': 2,
        'services': {
            'model': {'cpus': '0.5', 'memory': '1G'},
            'server': {'cpus': '0.5', 'memory': '512M'}
        }
    },
    {
        'id': 'medium',
        'name': 'Medium Resources',
        'cpu_cores': 2,
        'memory_gb': 4,
        'services': {
            'model': {'cpus': '1', 'memory': '2G'},
            'server': {'cpus': '1', 'memory': '1G'}
        }
    },
    {
        'id': 'high',
        'name': 'High Resources',
        'cpu_cores': 4,
        'memory_gb': 8,
        'services': {
            'model': {'cpus': '2', 'memory': '4G'},
            'server': {'cpus': '1', 'memory': '2G'}
        }
    }
]
```

## Scaling Monitor

### Critical Condition Detection
```python
class ScalingMonitor:
    def __init__(self):
        self.cpu_threshold = 90
        self.memory_threshold = 95
        self.critical_duration_threshold = 300  # 5 minutes
        
    def check_critical(self):
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        
        if cpu > self.cpu_threshold or memory > self.memory_threshold:
            if self.critical_start is None:
                self.critical_start = time.time()
            
            duration = time.time() - self.critical_start
            if duration > self.critical_duration_threshold:
                self.trigger_scaling_suggestion()
```

### Auto-Suggestion Logic
When critical for 5+ minutes:
1. Creates scaling suggestion
2. Selects appropriate template based on current usage
3. Sends Discord notification
4. Waits for admin approval

## Docker Compose Manager

### Scaling Execution
```python
class DockerComposeManager:
    def apply_scaling(self, template):
        # Read docker-compose.yml
        compose = yaml.safe_load(open('docker-compose.yml'))
        
        # Update service resources
        for service, resources in template['services'].items():
            if service in compose['services']:
                compose['services'][service]['deploy'] = {
                    'resources': {
                        'limits': {
                            'cpus': resources['cpus'],
                            'memory': resources['memory']
                        }
                    }
                }
        
        # Write and restart
        yaml.dump(compose, open('docker-compose.yml', 'w'))
        subprocess.run(['docker-compose', 'up', '-d'])
```

## Technical Implementation

### JavaScript Functions
```javascript
loadScalingStatus()       // Fetch current status
loadScalingTemplates()    // Load template list
loadScalingHistory()      // Load history
approveScaling(id)        // Approve suggestion
rejectScaling(id)         // Reject suggestion
executeManualScaling()    // Manual scale
deleteTemplate(id)        // Delete template
showCreateTemplateModal() // Create template
startScalingStatusUpdates() // Start polling
```

### Status Updates
- Polling interval: 5 seconds
- Only polls when tab is active
- Updates resource bars in real-time

## Configuration

### Scaling Config (resource_config.json)
```json
{
  "scaling": {
    "enabled": true,
    "auto_approve": false,
    "default_template": "high",
    "thresholds": {
      "cpu": 90,
      "memory": 95
    },
    "critical_duration_minutes": 5
  }
}
```

## User Actions
- View current resource status
- Approve or reject scaling suggestions
- Execute manual scaling
- Create/delete scaling templates
- View scaling history

## Related Pages
- [Overview](01_OVERVIEW.md) - Resource metrics
- [Processes](05_PROCESSES.md) - Process resources
- [Self-Healing](11_SELF_HEALING.md) - Auto remediation
- [Predictive Maintenance](08_PREDICTIVE_MAINTENANCE.md) - Proactive scaling
