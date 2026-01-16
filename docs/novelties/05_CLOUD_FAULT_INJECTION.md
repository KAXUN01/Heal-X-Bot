# Novelty 5: Cloud Fault Injection & Chaos Engineering

## Overview

Heal-X-Bot includes built-in chaos engineering capabilities that allow operators to inject faults into the system to test and validate self-healing mechanisms in a controlled environment.

## Why This Is Novel

| Traditional Approach | Heal-X-Bot Innovation |
|---------------------|----------------------|
| Wait for real failures | Simulate failures |
| Hope healing works | Verify healing works |
| Production testing | Safe testing environment |
| Manual fault creation | Automated injection |
| Unpredictable outcomes | Controlled experiments |

---

## Problem Statement

### Challenges Addressed
1. **Untested Healing**: Auto-healing rarely tested before real incidents
2. **Confidence Gap**: Teams unsure if healing will work
3. **Edge Cases**: Real failures have unique characteristics
4. **Training**: New team members lack incident experience
5. **Validation**: No way to verify healing effectiveness

---

## Solution Architecture

### Fault Injection Framework
```
┌─────────────────────────────────────────────────────────┐
│                 Chaos Engineering Dashboard              │
│              (Built into Self-Healing Page)              │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   Fault Injector      │
                │   - Type selection    │
                │   - Duration config   │
                │   - Intensity setting │
                └───────────┬───────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ CPU Spike    │    │ Memory Leak  │    │ Service Crash│
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   Fault Detector      │
                │   Monitors injected   │
                │   and real faults     │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   Self-Healing        │
                │   Responds to fault   │
                └───────────────────────┘
```

---

## Supported Fault Types

### 1. CPU Stress
```python
fault_types['cpu_stress'] = {
    'name': 'CPU Stress',
    'description': 'Simulate high CPU usage',
    'parameters': {
        'intensity': {'min': 50, 'max': 100, 'default': 90},
        'duration_seconds': {'min': 10, 'max': 300, 'default': 60}
    },
    'command': 'stress-ng --cpu {cores} --timeout {duration}s'
}
```

### 2. Memory Pressure
```python
fault_types['memory_leak'] = {
    'name': 'Memory Leak Simulation',
    'description': 'Simulate memory exhaustion',
    'parameters': {
        'size_mb': {'min': 100, 'max': 4000, 'default': 1000},
        'duration_seconds': {'min': 10, 'max': 300, 'default': 60}
    },
    'command': 'stress-ng --vm 1 --vm-bytes {size}M --timeout {duration}s'
}
```

### 3. Disk Fill
```python
fault_types['disk_fill'] = {
    'name': 'Disk Space Exhaustion',
    'description': 'Fill disk space temporarily',
    'parameters': {
        'size_mb': {'min': 100, 'max': 10000, 'default': 1000},
        'target_path': '/tmp/fault_injection_test'
    },
    'command': 'fallocate -l {size}M {path}'
}
```

### 4. Network Latency
```python
fault_types['network_latency'] = {
    'name': 'Network Latency Injection',
    'description': 'Add artificial network delay',
    'parameters': {
        'delay_ms': {'min': 50, 'max': 5000, 'default': 500},
        'interface': 'eth0',
        'duration_seconds': {'min': 10, 'max': 300, 'default': 60}
    },
    'command': 'tc qdisc add dev {interface} root netem delay {delay}ms'
}
```

### 5. Service Crash
```python
fault_types['service_crash'] = {
    'name': 'Service Crash Simulation',
    'description': 'Stop a Docker container',
    'parameters': {
        'service_name': 'test-service',
        'restart_delay_seconds': {'min': 0, 'max': 300, 'default': 0}
    },
    'command': 'docker stop {service}'
}
```

### 6. Port Block
```python
fault_types['port_block'] = {
    'name': 'Port Unavailability',
    'description': 'Block access to a port',
    'parameters': {
        'port': {'min': 1, 'max': 65535, 'default': 80},
        'duration_seconds': {'min': 10, 'max': 300, 'default': 60}
    },
    'command': 'iptables -A INPUT -p tcp --dport {port} -j DROP'
}
```

---

## Technical Deep Dive

### Fault Injector Class
```python
class FaultInjector:
    """Inject faults for chaos engineering testing"""
    
    def __init__(self):
        self.active_faults = {}
        self.fault_history = []
    
    async def inject_fault(self, fault_type: str, **params) -> Fault:
        """Inject a fault into the system"""
        
        # Validate fault type
        if fault_type not in SUPPORTED_FAULTS:
            raise ValueError(f"Unknown fault type: {fault_type}")
        
        # Create fault record
        fault = Fault(
            id=str(uuid.uuid4()),
            type=fault_type,
            parameters=params,
            injected_at=datetime.now(),
            status='active'
        )
        
        # Execute fault injection
        result = await self._execute_injection(fault)
        
        # Track active fault
        self.active_faults[fault.id] = fault
        
        # Schedule cleanup if duration specified
        if 'duration_seconds' in params:
            asyncio.create_task(
                self._cleanup_after_delay(fault, params['duration_seconds'])
            )
        
        return fault
    
    async def cleanup_fault(self, fault_id: str) -> bool:
        """Remove an injected fault"""
        
        if fault_id not in self.active_faults:
            return False
        
        fault = self.active_faults[fault_id]
        
        # Execute cleanup command
        await self._execute_cleanup(fault)
        
        # Update records
        fault.status = 'cleaned'
        fault.cleaned_at = datetime.now()
        del self.active_faults[fault_id]
        self.fault_history.append(fault)
        
        return True
```

### Demo Mode
```python
class DemoMode:
    """Automated fault injection demo for testing"""
    
    async def run_demo(self):
        """Run a full healing demonstration"""
        
        # Step 1: Inject fault
        fault = await self.injector.inject_fault(
            'service_crash',
            service_name='demo-service'
        )
        
        # Step 2: Wait for detection
        await asyncio.sleep(5)
        
        # Step 3: Trigger healing
        result = await self.healer.heal(fault)
        
        # Step 4: Verify
        verified = await self.verify_healing(fault)
        
        return {
            'fault': fault,
            'healing_result': result,
            'verified': verified,
            'demo_completed': True
        }
```

---

## API Reference

### Inject Fault
```http
POST /api/cloud/faults/inject
Content-Type: application/json

{
  "fault_type": "cpu_stress",
  "intensity": 90,
  "duration_seconds": 60
}
```

**Response:**
```json
{
  "success": true,
  "fault": {
    "id": "fault-inject-001",
    "type": "cpu_stress",
    "status": "active",
    "injected_at": "2026-01-16T15:00:00Z",
    "auto_cleanup_at": "2026-01-16T15:01:00Z"
  }
}
```

### List Active Faults
```http
GET /api/cloud/faults
```

### Cleanup Fault
```http
POST /api/cloud/faults/{fault_id}/cleanup
```

### Start Demo Mode
```http
POST /api/cloud/demo/start
```

---

## Configuration

### Fault Injection Settings
```json
{
  "fault_injection": {
    "enabled": true,
    "require_confirmation": true,
    "max_active_faults": 3,
    "auto_cleanup_timeout_seconds": 300,
    "allowed_fault_types": [
      "cpu_stress",
      "memory_leak",
      "service_crash",
      "network_latency"
    ],
    "blocked_in_production": true
  }
}
```

### Safety Guardrails
```json
{
  "safety": {
    "max_cpu_stress_percent": 95,
    "max_memory_usage_mb": 4000,
    "max_disk_fill_mb": 5000,
    "protected_services": ["healing-dashboard", "systemd"],
    "emergency_cleanup_on_threshold": true
  }
}
```

---

## Demo Mode Workflow

```
┌─────────────────────────────────────────────────────────┐
│                    START DEMO                            │
│              "Toggle Demo Mode" button                   │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│           STEP 1: INJECT DEMO FAULT                      │
│    Create simulated service_failure fault                │
│    Visual: Step 1 indicator turns YELLOW                 │
└───────────────────────────┬─────────────────────────────┘
                            │ (5 seconds)
                            ▼
┌─────────────────────────────────────────────────────────┐
│           STEP 2: FAULT DETECTION                        │
│    FaultDetector identifies the injected fault           │
│    Visual: Step 1 → GREEN, Step 2 → YELLOW               │
└───────────────────────────┬─────────────────────────────┘
                            │ (5 seconds)
                            ▼
┌─────────────────────────────────────────────────────────┐
│           STEP 3: AI ANALYSIS                            │
│    Gemini/Groq analyzes root cause                       │
│    Visual: Step 2 → GREEN, Step 3 → YELLOW               │
└───────────────────────────┬─────────────────────────────┘
                            │ (10 seconds)
                            ▼
┌─────────────────────────────────────────────────────────┐
│           STEP 4: HEALING APPLIED                        │
│    Execute remediation commands                          │
│    Visual: Step 3 → GREEN, Step 4 → YELLOW               │
└───────────────────────────┬─────────────────────────────┘
                            │ (5 seconds)
                            ▼
┌─────────────────────────────────────────────────────────┐
│           STEP 5: VERIFICATION                           │
│    Confirm fault is resolved                             │
│    Visual: All steps → GREEN                             │
│    Discord notification sent                             │
└─────────────────────────────────────────────────────────┘
```

---

## Use Cases

### 1. Healing Validation
Test that self-healing works before relying on it in production.

### 2. Runbook Testing
Validate that documented remediation steps are correct.

### 3. Team Training
Train incident responders on system behavior during failures.

### 4. Resilience Quantification
Measure system resilience metrics.

---

## Future Enhancements

1. **Scheduled Chaos**: Randomly inject faults on schedule
2. **Blast Radius Control**: Limit fault impact
3. **A/B Testing**: Compare healing strategies
4. **Game Days**: Organized chaos engineering events
5. **Automated Resilience Reports**: Generate resilience scores
