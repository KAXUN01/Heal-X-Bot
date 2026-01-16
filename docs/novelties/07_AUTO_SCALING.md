# Novelty 7: Resource-Based Auto Scaling

## Overview

Heal-X-Bot implements intelligent resource-based auto scaling that monitors CPU and memory usage, creates scaling suggestions when thresholds are exceeded, and applies template-based configurations with administrator approval.

## Why This Is Novel

| Traditional Approach | Heal-X-Bot Innovation |
|---------------------|----------------------|
| Manual scaling | Automatic suggestions |
| Fixed schedules | Resource-driven |
| All-or-nothing | Template-based configs |
| No approval flow | Admin approval workflow |
| No history | Complete audit trail |

---

## Problem Statement

### Challenges Addressed
1. **Reactive Scaling**: Scaling only after performance degradation
2. **Over-provisioning**: Wasting resources with fixed allocations
3. **Under-provisioning**: Insufficient resources during peaks
4. **Manual Intervention**: Requires human action to scale
5. **No Standards**: Ad-hoc resource configurations

---

## Solution Architecture

### Auto Scaling Pipeline
```
┌─────────────────┐
│ Scaling Monitor │
│ (Every 30 sec)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Threshold Check │
│ CPU > 90%?      │
│ Memory > 95%?   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼ Yes     ▼ No
┌────────┐  ┌────────┐
│Critical│  │Continue│
│Duration│  │Monitor │
│Check   │  └────────┘
└────┬───┘
     │
     ▼ (> 5 min)
┌─────────────────┐
│ Create Scaling  │
│ Suggestion      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Wait for Admin  │
│ Approval        │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼ Approve ▼ Reject
┌────────┐  ┌────────┐
│Execute │  │Log     │
│Scaling │  │Reason  │
└────────┘  └────────┘
```

---

## Technical Deep Dive

### Scaling Monitor
```python
class ScalingMonitor:
    """Monitor resources and trigger scaling suggestions"""
    
    def __init__(self):
        self.cpu_threshold = 90
        self.memory_threshold = 95
        self.critical_duration_threshold = 300  # 5 minutes
        self.critical_start = None
    
    def get_current_status(self) -> Dict:
        """Get current resource status"""
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        
        is_critical = cpu > self.cpu_threshold or memory > self.memory_threshold
        
        if is_critical:
            if self.critical_start is None:
                self.critical_start = time.time()
            duration = time.time() - self.critical_start
        else:
            self.critical_start = None
            duration = 0
        
        return {
            'cpu_percent': cpu,
            'memory_percent': memory,
            'is_critical': is_critical,
            'critical_duration_seconds': duration
        }
    
    async def check_and_suggest(self):
        """Check if scaling suggestion should be created"""
        status = self.get_current_status()
        
        if status['critical_duration_seconds'] > self.critical_duration_threshold:
            await self.create_scaling_suggestion(status)
```

### Scaling Templates
```python
default_templates = [
    {
        'id': 'low',
        'name': 'Low Resources',
        'description': 'Minimal allocation for low-load periods',
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
        'description': 'Balanced allocation (recommended)',
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
        'description': 'Maximum allocation for high-load periods',
        'cpu_cores': 4,
        'memory_gb': 8,
        'services': {
            'model': {'cpus': '2', 'memory': '4G'},
            'server': {'cpus': '1', 'memory': '2G'}
        }
    }
]
```

### Docker Compose Manager
```python
class DockerComposeManager:
    """Manage Docker Compose resource configurations"""
    
    def __init__(self, compose_file: str):
        self.compose_file = compose_file
    
    def apply_template(self, template: Dict) -> bool:
        """Apply scaling template to docker-compose.yml"""
        
        # Read current compose file
        with open(self.compose_file, 'r') as f:
            compose = yaml.safe_load(f)
        
        # Update service resources
        for service_name, resources in template['services'].items():
            if service_name in compose['services']:
                if 'deploy' not in compose['services'][service_name]:
                    compose['services'][service_name]['deploy'] = {}
                
                compose['services'][service_name]['deploy']['resources'] = {
                    'limits': {
                        'cpus': resources['cpus'],
                        'memory': resources['memory']
                    }
                }
        
        # Write updated compose file
        with open(self.compose_file, 'w') as f:
            yaml.dump(compose, f, default_flow_style=False)
        
        return True
    
    async def restart_services(self, services: List[str]):
        """Restart services to apply new configuration"""
        for service in services:
            await asyncio.create_subprocess_exec(
                'docker-compose', 'up', '-d', service
            )
```

### Suggestion Workflow
```python
class ScalingManager:
    """Manage scaling suggestions and execution"""
    
    def __init__(self):
        self.pending_suggestions = {}
        self.history = ScalingHistory()
    
    def create_suggestion(self, template_id: str, reason: str, metrics: Dict):
        """Create a scaling suggestion for admin approval"""
        
        suggestion = {
            'id': str(uuid.uuid4()),
            'template_id': template_id,
            'reason': reason,
            'metrics': metrics,
            'created_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        self.pending_suggestions[suggestion['id']] = suggestion
        
        # Send Discord notification
        send_discord_alert(
            f"⚡ Scaling Suggestion: {reason}",
            severity="warning",
            alert_type="scaling"
        )
        
        return suggestion
    
    async def approve_suggestion(self, suggestion_id: str) -> Dict:
        """Approve and execute scaling suggestion"""
        
        suggestion = self.pending_suggestions.get(suggestion_id)
        if not suggestion:
            raise ValueError("Suggestion not found")
        
        # Execute scaling
        result = await self.execute_scaling(suggestion['template_id'])
        
        # Update suggestion status
        suggestion['status'] = 'approved'
        suggestion['executed_at'] = datetime.now().isoformat()
        
        # Move to history
        del self.pending_suggestions[suggestion_id]
        self.history.add(suggestion)
        
        return result
```

---

## API Reference

### Get Scaling Status
```http
GET /api/scaling/status
```

**Response:**
```json
{
  "available": true,
  "monitor": {
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "is_critical": false,
    "critical_duration_seconds": 0
  },
  "pending_suggestions": []
}
```

### Get Templates
```http
GET /api/scaling/templates
```

### Create Template
```http
POST /api/scaling/templates
Content-Type: application/json

{
  "name": "Custom Template",
  "description": "Custom resource allocation",
  "cpu_cores": 3,
  "memory_gb": 6,
  "services": {
    "model": {"cpus": "1.5", "memory": "3G"},
    "server": {"cpus": "1", "memory": "1.5G"}
  }
}
```

### Approve/Reject Suggestion
```http
POST /api/scaling/approve
Content-Type: application/json

{
  "suggestion_id": "sugg-001",
  "action": "approve"
}
```

### Manual Scaling
```http
POST /api/scaling/manual
Content-Type: application/json

{
  "template_id": "high"
}
```

---

## Configuration

### Scaling Configuration (resource_config.json)
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
    "critical_duration_minutes": 5,
    "cooldown_minutes": 10
  }
}
```

---

## Dashboard Features

### Current Resource Status
- Real-time CPU/Memory bars
- Threshold indicators
- Critical status badge
- Duration counter

### Pending Suggestions
- Template name
- Reason for suggestion
- Current metrics
- Approve/Reject buttons

### Manual Scaling
- Template dropdown
- Preview changes
- Execute button

### Scaling History
- All scaling events
- Type (manual/approved/rejected)
- Timestamp and details

---

## Use Cases

### 1. Peak Load Handling
Automatically suggest scaling up during high traffic.

### 2. Cost Optimization
Scale down during low-usage periods.

### 3. Compliance
Approval workflow ensures controlled changes.

### 4. Audit Trail
Complete history of all scaling decisions.

---

## Future Enhancements

1. **Predictive Scaling**: Scale before load increases
2. **Auto-Approval**: Trusted thresholds for auto-scaling
3. **Multi-Container**: Scale individual containers
4. **Cloud Integration**: AWS/GCP auto-scaling
5. **Cost Tracking**: Resource cost optimization
