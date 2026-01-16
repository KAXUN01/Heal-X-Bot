# Novelty 10: Discord-Integrated Alerting System

## Overview

Heal-X-Bot implements a sophisticated Discord webhook-based alerting system with intelligent deduplication, severity-based formatting, and real-time notification delivery for all system events.

## Why This Is Novel

| Traditional Approach | Heal-X-Bot Innovation |
|---------------------|----------------------|
| Email alerts (slow) | Instant Discord delivery |
| No deduplication | Smart alert batching |
| Plain text | Rich embeds with emojis |
| Separate tools | Integrated with all features |
| Alert fatigue | Severity-based filtering |

---

## Problem Statement

### Challenges Addressed
1. **Alert Delivery**: Email alerts have delays
2. **Alert Fatigue**: Too many similar alerts
3. **No Context**: Plain text lacks information
4. **Missing Alerts**: Notifications get lost
5. **No Collaboration**: Alerts aren't team-visible

---

## Solution Architecture

### Alert Flow
```
┌─────────────────┐
│   Alert Source  │
│ - Healing       │
│ - DDoS          │
│ - SSH           │
│ - Scaling       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Alert Processor │
│ - Formatting    │
│ - Severity      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Deduplication   │
│ - Message hash  │
│ - Time window   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Discord Webhook │
│ - POST request  │
│ - Rich embed    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Alert Storage   │
│ - Local history │
│ - Dashboard     │
└─────────────────┘
```

---

## Technical Deep Dive

### Discord Alert Function
```python
import requests
from collections import deque
from datetime import datetime, timedelta
import hashlib

# Alert storage and deduplication
discord_alerts_storage = deque(maxlen=500)
recent_alert_hashes = {}  # hash -> timestamp
DEDUP_WINDOW_SECONDS = 300  # 5 minutes

def send_discord_alert(
    message: str,
    severity: str = "info",
    alert_type: str = "general",
    skip_deduplication: bool = False
) -> bool:
    """Send alert to Discord webhook with deduplication"""
    
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    if not webhook_url:
        return False
    
    # Generate message hash for deduplication
    message_hash = hashlib.md5(
        f"{message}:{alert_type}".encode()
    ).hexdigest()
    
    # Check for duplicate (unless skipped)
    if not skip_deduplication:
        now = datetime.now()
        if message_hash in recent_alert_hashes:
            last_sent = recent_alert_hashes[message_hash]
            if (now - last_sent).total_seconds() < DEDUP_WINDOW_SECONDS:
                return False  # Skip duplicate
    
    # Format message based on severity
    embed = format_discord_embed(message, severity, alert_type)
    
    # Send to Discord
    try:
        response = requests.post(
            webhook_url,
            json={"embeds": [embed]},
            timeout=10
        )
        
        if response.status_code == 204:
            # Record for deduplication
            recent_alert_hashes[message_hash] = datetime.now()
            
            # Store in local history
            store_alert(message, severity, alert_type)
            
            return True
            
    except Exception as e:
        logger.error(f"Discord webhook failed: {e}")
    
    return False
```

### Severity-Based Formatting
```python
SEVERITY_CONFIG = {
    'critical': {
        'color': 0xFF0000,  # Red
        'emoji': '🚨',
        'title_prefix': 'CRITICAL ALERT'
    },
    'error': {
        'color': 0xE74C3C,  # Dark Red
        'emoji': '❌',
        'title_prefix': 'ERROR'
    },
    'warning': {
        'color': 0xF39C12,  # Orange
        'emoji': '⚠️',
        'title_prefix': 'WARNING'
    },
    'success': {
        'color': 0x2ECC71,  # Green
        'emoji': '✅',
        'title_prefix': 'SUCCESS'
    },
    'info': {
        'color': 0x3498DB,  # Blue
        'emoji': 'ℹ️',
        'title_prefix': 'INFO'
    }
}

def format_discord_embed(message: str, severity: str, alert_type: str) -> Dict:
    """Format message as Discord embed"""
    
    config = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG['info'])
    
    return {
        'title': f"{config['emoji']} {config['title_prefix']}: {alert_type}",
        'description': message,
        'color': config['color'],
        'timestamp': datetime.utcnow().isoformat(),
        'footer': {
            'text': 'Heal-X Bot',
            'icon_url': 'https://example.com/heal-x-icon.png'
        },
        'fields': [
            {
                'name': 'Alert Type',
                'value': alert_type,
                'inline': True
            },
            {
                'name': 'Severity',
                'value': severity.upper(),
                'inline': True
            }
        ]
    }
```

### Alert Storage
```python
def store_alert(message: str, severity: str, alert_type: str):
    """Store alert in local history for dashboard display"""
    
    alert = {
        'id': str(uuid.uuid4()),
        'message': message,
        'severity': severity,
        'type': alert_type,
        'timestamp': datetime.now().isoformat(),
        'acknowledged': False
    }
    
    discord_alerts_storage.append(alert)
    
    # Also emit WebSocket event for real-time dashboard
    emit_websocket('new_alert', alert)
```

---

## Alert Types

### System Alerts
| Alert Type | Trigger | Severity |
|------------|---------|----------|
| `healing_success` | Successful auto-heal | success |
| `healing_failed` | Failed healing attempt | error |
| `service_down` | Service stopped | critical |
| `resource_critical` | CPU/Memory > 95% | critical |

### Security Alerts
| Alert Type | Trigger | Severity |
|------------|---------|----------|
| `ddos_detected` | DDoS attack detected | critical |
| `ip_blocked` | IP auto-blocked | warning |
| `ssh_intrusion` | SSH brute force | warning |

### Scaling Alerts
| Alert Type | Trigger | Severity |
|------------|---------|----------|
| `scaling_suggestion` | Resources critical | warning |
| `scaling_executed` | Scaling completed | success |
| `template_created` | New template | info |

### Maintenance Alerts
| Alert Type | Trigger | Severity |
|------------|---------|----------|
| `prediction_warning` | High failure risk | warning |
| `disk_cleanup` | Disk cleanup executed | info |
| `log_rotation` | Logs rotated | info |

---

## API Reference

### Get Discord Alerts
```http
GET /api/discord/alerts?limit=100
```

**Response:**
```json
{
  "alerts": [
    {
      "id": "alert-001",
      "message": "Service nginx restarted successfully",
      "severity": "success",
      "type": "healing_success",
      "timestamp": "2026-01-16T15:30:00Z",
      "acknowledged": false
    }
  ],
  "total": 1
}
```

### Get Unread Count
```http
GET /api/alerts/unread
```

### Test Webhook
```http
POST /api/discord/test
```

---

## Configuration

### Discord Settings
```bash
# .env file
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
```

### Alert Configuration
```json
{
  "discord": {
    "enabled": true,
    "webhook_url": "${DISCORD_WEBHOOK}",
    "deduplication_window_seconds": 300,
    "max_alerts_per_minute": 10,
    "severity_filter": ["critical", "error", "warning"],
    "alert_types": {
      "healing": true,
      "security": true,
      "scaling": true,
      "maintenance": true
    }
  }
}
```

---

## Deduplication Logic

### How It Works
```
1. Generate hash: MD5(message + alert_type)
2. Check recent_alert_hashes for match
3. If match AND within 5-minute window:
   - Skip sending (return False)
4. If no match OR outside window:
   - Send alert
   - Store hash with timestamp
   - Clean old hashes periodically
```

### Skip Deduplication
Certain alerts should always be sent:
```python
# Force send without deduplication
send_discord_alert(
    "Manual scaling to HIGH template completed",
    severity="success",
    alert_type="scaling_manual",
    skip_deduplication=True  # Always send
)
```

---

## Dashboard Integration

### Active Alerts Page
- All Discord alerts displayed
- Severity color coding
- Acknowledge button
- Filter by type/severity

### Real-Time Updates
- WebSocket push for new alerts
- Badge counter in sidebar
- Toast notifications

---

## Rich Embed Features

### Standard Embed
```json
{
  "title": "⚠️ WARNING: Service Alert",
  "description": "nginx service restarted after failure detection",
  "color": 16750848,
  "timestamp": "2026-01-16T15:30:00Z",
  "fields": [
    {"name": "Service", "value": "nginx", "inline": true},
    {"name": "Action", "value": "Restart", "inline": true}
  ],
  "footer": {"text": "Heal-X Bot"}
}
```

### With Additional Context
```json
{
  "title": "🚨 CRITICAL: DDoS Attack Detected",
  "description": "High-confidence DDoS attack detected from 192.168.1.100",
  "color": 16711680,
  "fields": [
    {"name": "Attack Type", "value": "HTTP Flood", "inline": true},
    {"name": "Confidence", "value": "94%", "inline": true},
    {"name": "Action Taken", "value": "IP Blocked", "inline": true}
  ],
  "thumbnail": {"url": "https://example.com/alert-icon.png"}
}
```

---

## Use Cases

### 1. Team Awareness
Entire team sees alerts in shared Discord channel.

### 2. Mobile Notifications
Discord mobile app delivers push notifications.

### 3. Incident Documentation
Alert history serves as incident timeline.

### 4. Escalation
Critical alerts trigger immediate attention.

---

## Future Enhancements

1. **Slack Integration**: Add Slack webhook support
2. **PagerDuty**: On-call integration
3. **Alert Routing**: Send to different channels
4. **Scheduled Digests**: Daily/weekly summaries
5. **Alert Acknowledgment**: Mark resolved in Discord
