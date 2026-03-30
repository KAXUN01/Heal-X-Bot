# Active Alerts Page

## Description
The Active Alerts page displays real-time system alerts and notifications from various monitoring sources including Discord webhook alerts, fault detection events, and system health warnings.

## Purpose
- Centralize all system alerts in one view
- Provide quick access to alert details and context
- Enable alert acknowledgment and management
- Track alert history and patterns

## Features

### 1. Alert Categories
Alerts are categorized by severity:

| Level | Icon | Description | Priority |
|-------|------|-------------|----------|
| **CRITICAL** | 🔴 | System-impacting issues requiring immediate action | Highest |
| **ERROR** | 🟠 | Significant problems that need attention | High |
| **WARNING** | 🟡 | Potential issues or degraded performance | Medium |
| **INFO** | 🔵 | Informational notifications | Low |

### 2. Alert List
Each alert displays:
- Timestamp
- Severity indicator
- Alert type/category
- Source (service/component)
- Message content
- Action buttons

### 3. Alert Actions
- **View Details**: Expand alert for full context
- **Acknowledge**: Mark alert as seen
- **Auto-Heal**: Trigger automatic remediation (if available)
- **AI Analyze**: Get AI-powered root cause analysis

### 4. Filtering & Search
- Filter by severity level
- Filter by source/service
- Text search across alert messages
- Time range filtering

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/alerts` | GET | Fetch all active alerts |
| `/api/alerts/unread` | GET | Get unread alert count |
| `/api/discord/alerts` | GET | Get Discord webhook alerts |
| `/api/alerts/{id}/acknowledge` | POST | Acknowledge an alert |

## Alert Sources

### 1. Discord Webhook Alerts
```python
send_discord_alert(message, severity, alert_type)
```
- Sent to Discord channel
- Stored in `discord_alerts_storage` deque
- Maximum 500 alerts retained

### 2. FaultDetector Alerts
- Service failures
- Resource threshold exceeded
- Network connectivity issues
- Container crashes

### 3. System Monitors
- Critical services monitor
- Resource alert monitor
- Container health monitor

## Technical Implementation

### Alert Storage
```python
discord_alerts_storage = deque(maxlen=500)
```

### Alert Structure
```json
{
  "id": "unique-uuid",
  "timestamp": "ISO-8601 datetime",
  "severity": "critical|error|warning|info",
  "type": "service_failure|resource_alert|network_issue",
  "source": "component_name",
  "message": "Alert description",
  "acknowledged": false,
  "metadata": {}
}
```

### JavaScript Functions
```javascript
loadAlerts()           // Fetch and display alerts
filterAlerts()         // Apply filters
acknowledgeAlert(id)   // Mark alert as seen
analyzeAlert(id)       // Trigger AI analysis
```

## Alert Type Details

### Service Failure Alerts
- **Trigger**: Service stops responding
- **Content**: Service name, last known state
- **Suggested Action**: Service restart

### Resource Alerts
- **Trigger**: CPU > 90%, Memory > 95%, Disk > 90%
- **Content**: Current value, threshold exceeded
- **Suggested Action**: Resource cleanup or scaling

### Network Alerts
- **Trigger**: Port unreachable, connection timeout
- **Content**: Target host/port, error details
- **Suggested Action**: Network troubleshooting

### DDoS Alerts
- **Trigger**: ML model detects attack pattern
- **Content**: Attack type, source IPs, confidence
- **Suggested Action**: IP blocking, traffic analysis

## Related Pages
- [Overview](01_OVERVIEW.md) - Alert count summary
- [Self-Healing](11_SELF_HEALING.md) - Automatic remediation
- [Logs & AI](07_LOGS_AI.md) - Detailed log analysis
