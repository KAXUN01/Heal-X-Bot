# Heal-X-Bot API Reference

Complete API documentation for all Heal-X-Bot services.

## Table of Contents

- [Healing Dashboard API (Port 5001) - PRIMARY](#healing-dashboard-api-port-5001)
- [Monitoring Server API (Port 5000)](#monitoring-server-api-port-5000) 
- [ML Model API (Port 8080)](#ml-model-api-port-8080)
- [Network Analyzer API (Port 8000)](#network-analyzer-api-port-8000)

---

## Healing Dashboard API (Port 5001)

**Base URL**: `http://localhost:5001`

The primary API for system monitoring, auto-healing, IP management, and AI log analysis.

### Health & Status

#### `GET /api/health`
Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-17T10:00:00Z"
}
```

#### `GET /metrics`
Prometheus metrics endpoint.

**Response**: Prometheus-formatted metrics

---

### AI Log Analysis (Gemini/Groq)

#### `POST /api/gemini/analyze-log`
Analyze a single log entry using AI (Gemini or Groq).

**Request Body**:
```json
{
  "log_entry": {
    "service": "nginx",
    "level": "ERROR",
    "message": "Connection timeout to database",
    "timestamp": "2025-12-17T10:00:00Z"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "why": "Database connection timeout occurred",
  "how": "Restart nginx service or check database connectivity",
  "root_cause": "Database server may be down or network issue",
  "analysis_provider": "gemini"
}
```

#### `POST /api/gemini/analyze-pattern`
Analyze multiple logs for patterns.

**Request Body**:
```json
{
  "logs": [...],
  "limit": 10
}
```

**Response**: Pattern analysis with correlations

#### `GET /api/gemini/analyze-service/{service_name}`
Analyze overall health of a specific service.

**Parameters**:
- `service_name` (path): Name of service to analyze
- `limit` (query, optional): Number of logs to analyze (default: 50)

**Response**: Service health assessment

#### `GET /api/gemini/status`
Check AI analyzer status and configuration.

**Response**:
```json
{
  "api_key_configured": true,
  "analyzer_initialized": true,
  "model_available": true,
  "analyzer_type": "gemini",
  "model_name": "gemini-2.5-flash-lite-preview-09-2025",
  "message": "Gemini analyzer is ready"
}
```

---

### Auto-Healing System

#### `GET /api/auto-healer/status`
Get auto-healer status and configuration.

**Response**:
```json
{
  "enabled": true,
  "auto_execute": true,
  "max_attempts": 3,
  "cooldown_minutes": 5,
  "monitoring_interval": 60,
  "active": true
}
```

#### `POST /api/auto-healer/config`
Update auto-healer configuration.

**Request Body**:
```json
{
  "enabled": true,
  "auto_execute": true,
  "max_attempts": 3,
  "cooldown_minutes": 5,
  "monitoring_interval": 60
}
```

#### `POST /api/auto-healer/heal`
Manually trigger healing for a service.

**Request Body**:
```json
{
  "service_name": "nginx",
  "issue_type": "high_cpu"
}
```

**Response**: Healing attempt result with actions taken

#### `GET /api/auto-healer/history`
Get healing history.

**Parameters**:
- `limit` (query, optional): Number of records (default: 50)

**Response**: List of healing attempts with outcomes

---

### IP Blocking & DDoS Protection

####  `GET /api/blocked-ips`
Get list of blocked IPs.

**Parameters**:
- `active_only` (query, optional): Return only active blocks (default: true)

**Response**:
```json
{
  "success": true,
  "blocked_ips": [
    {
      "ip": "192.168.1.100",
      "reason": "DDoS Attack - HTTP Flood",
      "threat_level": "High",
      "block_time": "2025-12-17T09:00:00Z",
      "unblock_time": null,
      "auto_blocked": true
    }
  ]
}
```

#### `POST /api/blocking/block`
Block an IP address.

**Request Body**:
```json
{
  "ip": "192.168.1.100",
  "reason": "Suspicious activity",
  "threat_level": "Medium",
  "attack_type": "Port Scan",
  "blocked_by": "admin"
}
```

#### `POST /api/blocking/unblock`
Unblock an IP address.

**Request Body**:
```json
{
  "ip": "192.168.1.100"
}
```

#### `GET /api/blocked-ips/statistics`
Get IP blocking statistics.

**Response**:
```json
{
  "total_blocks": 150,
  "auto_blocks": 120,
  "manual_blocks": 30,
  "total_unblocks": 45,
  "active_blocks": 105
}
```

---

### System Monitoring

#### `GET /api/metrics/system`
Get current system metrics.

**Response**:
```json
{
  "cpu_usage": 45.2,
  "memory_usage": 68.5,
  "disk_usage": 55.0,
  "network_throughput": {
    "incoming": 1250000,
    "outgoing": 850000
  },
  "timestamp": "2025-12-17T10:00:00Z"
}
```

#### `GET /api/system-logs/recent`
Get recent system logs.

**Parameters**:
- `limit` (query, optional): Number of logs (default: 100)
- `level` (query, optional): Filter by level (ERROR, WARNING, INFO)
- `source` (query, optional): Filter by source (docker, systemd, etc.)

#### `GET /api/system-logs/statistics`
Get log statistics.

**Response**: Log counts by level, source, and time period

---

### Critical Services Monitoring

#### `GET /api/critical-services`
Get status of all critical services.

**Response**:
```json
{
  "services": [
    {
      "name": "docker",
      "status": "running",
      "health": "healthy",
      "uptime": 86400
    }
  ]
}
```

#### `GET /api/critical-services/logs`
Get logs from critical services.

**Parameters**:
- `limit` (query): Number of logs
- `level` (query, optional): Filter by level
- `service` (query, optional): Filter by service name

#### `GET /api/critical-services/issues`
Get critical issues from monitored services.

**Response**: List of detected issues with severity and recommendations

---

### Cloud Simulation & Fault Injection

#### `POST /api/cloud/faults/inject`
Inject a fault for testing.

**Request Body**:
```json
{
  "type": "crash",
  "container": "cloud-sim-api-server",
  "duration": 60
}
```

**Fault Types**:
- `crash`: Service crash
- `cpu`: CPU spike
- `memory`: Memory leak
- `disk`: Disk full
- `network`: Network issues

#### `GET /api/cloud/faults`
Get detected faults.

**Parameters**:
- `limit` (query, optional): Number of faults (default: 50)

**Response**:
```json
{
  "faults": [
    {
      "id": 1,
      "type": "service_down",
      "service": "nginx",
      "detected_at": "2025-12-17T09:00:00Z",
      "severity": "high"
    }
  ],
  "statistics": {
    "total": 45,
    "by_type": {
      "service_down": 20,
      "high_cpu": 15,
      "memory_leak": 10
    }
  }
}
```

#### `POST /api/cloud/faults/{fault_id}/analyze`
Analyze a fault using AI to get healing instructions.

**Response**: AI analysis with root cause and fix suggestions

#### `POST /api/cloud/faults/cleanup`
Clean up all injected faults.

---

### Service Discovery

#### `GET /api/services/discover`
Discover all services (Docker, systemd, Kubernetes).

**Response**:
```json
{
  "services": [
    {
      "name": "nginx",
      "type": "docker",
      "status": "running",
      "active": true
    }
  ]
}
```

---

### Discord Configuration

#### `GET /api/discord/status`
Get Discord webhook configuration status.

**Response**:
```json
{
  "configured": true,
  "has_env_var": true,
  "webhook_length": 120
}
```

#### `POST /api/discord/test`
Test Discord webhook.

**Request Body**:
```json
{
  "message": "Test notification"
}
```

---

### Scaling Management

#### `GET /api/scaling/status`
Get scaling status and pending suggestions.

**Response**: Current scaling state and recommendations

#### `POST /api/scaling/execute`
Execute a scaling suggestion.

**Request Body**:
```json
{
  "suggestion_id": "scale-up-web-1"
}
```

---

### WebSocket Events

#### `WS /ws`
WebSocket connection for real-time events.

**Event Types**:
- `system_metric`: System metrics update
- `service_status`: Service status change
- `fault_detected`: New fault detected
- `healing_action`: Healing action executed
- `ip_blocked`: IP blocked event

**Example Message**:
```json
{
  "event": "ip_blocked",
  "data": {
    "ip": "192.168.1.100",
    "reason": "DDoS Attack",
    "timestamp": "2025-12-17T10:00:00Z"
  }
}
```

---

## Monitoring Server API (Port 5000)

**Base URL**: `http://localhost:5000`

Flask-based monitoring server with similar endpoints to healing dashboard.

### Key Endpoints

- `GET /health`: Health check
- `GET /metrics`: Prometheus metrics
- `GET /api/logs`: Recent system logs
- `GET /api/services`: Service status

---

## ML Model API (Port 8080)

**Base URL**: `http://localhost:8080`

### DDoS Detection

#### `POST /predict`
Predict if traffic is a DDoS attack.

**Request Body**:
```json
{
  "features": {
    "request_rate": 1500,
    "unique_ips": 50,
    "error_rate": 0.15,
    "avg_response_time": 250
  }
}
```

**Response**:
```json
{
  "prediction": "DDoS",
  "confidence": 0.95,
  "threat_level": 0.92,
  "attack_type": "HTTP Flood",
  "recommendation": "Block source IPs immediately"
}
```

### Predictive Maintenance

#### `POST /predict/failure`
Predict system failure probability.

**Request Body**:
```json
{
  "features": {
    "cpu_usage": 85.0,
    "memory_usage": 90.0,
    "disk_usage": 78.0,
    "error_rate": 0.05
  }
}
```

**Response**:
```json
{
  "failure_probability": 0.75,
  "time_to_failure_hours": 6,
  "risk_level": "high",
  "recommendations": [
    "Reduce load",
    "Clear disk space",
    "Investigate memory leaks"
  ]
}
```

### Model Status

#### `GET /health`
Model service health check.

#### `GET /metrics`
Model performance metrics.

#### `GET /model/status`
Detailed model information.

**Response**:
```json
{
  "model_name": "ddos_detector",
  "version": "2.0",
  "accuracy": 0.96,
  "last_updated": "2025-12-15T00:00:00Z"
}
```

---

## Network Analyzer API (Port 8000)

**Base URL**: `http://localhost:8000`

### Attack Analysis

#### `GET /attack-patterns`
Get historical attack patterns from last 24 hours.

**Response**:
```json
{
  "hits": {
    "total": 45
  },
  "aggregations": {
    "attack_types": [
      {"key": "HTTP_FLOOD", "doc_count": 25},
      {"key": "SYN_FLOOD", "doc_count": 15}
    ]
  }
}
```

#### `GET /active-threats`
Get currently active threats.

**Response**:
```json
{
  "threats": [
    {
      "ip": "192.168.1.100",
      "attack_type": "HTTP_FLOOD",
      "threat_level": 0.88,
      "start_time": "2025-12-17T09:30:00Z"
    }
  ]
}
```

### IP Management

#### `GET /blocked-ips`
Get list of blocked IPs.

#### `POST /block-ip`
Block an IP address.

**Request Body**:
```json
{
  "ip": "192.168.1.100",
  "reason": "DDoS Attack",
  "threat_level": 0.9,
  "attack_type": "HTTP_FLOOD"
}
```

#### `POST /unblock-ip`
Unblock an IP address.

**Request Body**:
```json
{
  "ip": "192.168.1.100"
}
```

#### `GET /blocked-ips/stats`
Get IP blocking statistics.

#### `GET /is-blocked/{ip}`
Check if specific IP is blocked.

---

## Authentication

Currently, all APIs are unauthenticated and intended for internal use only.

> [!WARNING]
> **Security Notice**: These APIs should not be exposed to the public internet without proper authentication and authorization.

## Rate Limiting

No rate limiting is currently enforced on API endpoints.

## Error Responses

All APIs follow this error response format:

```json
{
  "status": "error",
  "message": "Description of error",
  "error": "Detailed technical error (if available)"
}
```

## WebSocket Protocol

WebSocket connections use JSON message format:

```json
{
  "event": "event_type",
  "data": { ... },
  "timestamp": "ISO 8601 timestamp"
}
```

---

## Quick Reference

| Service | Port | Purpose |
|---------|------|---------|
| Healing Dashboard | 5001 | Primary UI and API |
| Monitoring Server | 5000 | Legacy Flask API |
| ML Model | 8080 | DDoS detection |
| Network Analyzer | 8000 | IP blocking & attack analysis |
| Prometheus | 9090 | Metrics collection |

---

## Next Steps

- See [Features Documentation](../docs/features/) for detailed feature guides
- See [Configuration Guide](../docs/guides/CONFIGURATION.md) for setup
- See [Troubleshooting](../docs/guides/TROUBLESHOOTING.md) for common issues
