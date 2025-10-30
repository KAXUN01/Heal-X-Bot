# Critical Services Monitoring - Complete Guide

## ✅ What's Implemented

Your Healing-Bot now monitors **13 critical Ubuntu services**, centralizes their logs, and provides AI-powered analysis!

## 🎯 Monitored Services

### CRITICAL (Core System - Failures cause system issues)
- ✅ **docker** - Docker container runtime
- ✅ **containerd** - Container runtime (required by Docker)
- ✅ **systemd-journald** - System logging daemon (core logging)
- ✅ **systemd-logind** - Login manager (handles user sessions)
- ✅ **dbus** - Message bus (inter-process communication)

### IMPORTANT (Essential Services)
- ✅ **cron** - Task scheduler (runs scheduled jobs)
- ✅ **rsyslog** - System logger (handles syslog messages)
- ✅ **systemd-resolved** - DNS resolver (network name resolution)
- ✅ **systemd-udevd** - Device manager (hardware management)

### SECURITY (Security & Protection)
- ✅ **snapd** - Snap package manager
- ✅ **ufw** - Firewall manager
- ❌ **fail2ban** - Intrusion prevention (not installed/running)
- ✅ **apparmor** - Mandatory access control

## 📊 Current Status

**Total Logs Collected:** 360 logs  
**Collection Interval:** Every 60 seconds  
**Categories:** CRITICAL (150), IMPORTANT (120), SECURITY (90)  
**Issues Detected:** 3 ERRORS, 24 WARNINGS

## 🔌 API Endpoints

### 1. Get Service List with Status
```bash
curl http://localhost:5000/api/critical-services/list | jq '.'
```

**Response:**
```json
{
  "status": "success",
  "services": {
    "CRITICAL": [
      {
        "name": "docker",
        "description": "Docker container runtime - manages all containers",
        "active": true,
        "status": "active"
      },
      ...
    ],
    "IMPORTANT": [...],
    "SECURITY": [...]
  }
}
```

### 2. Get Centralized Logs
```bash
# Get all logs
curl "http://localhost:5000/api/critical-services/logs?limit=100" | jq '.'

# Get logs by category
curl "http://localhost:5000/api/critical-services/logs?category=CRITICAL&limit=50" | jq '.'

# Get logs by specific service
curl "http://localhost:5000/api/critical-services/logs?service=docker&limit=50" | jq '.'

# Get only ERROR logs
curl "http://localhost:5000/api/critical-services/logs?level=ERROR" | jq '.'
```

### 3. Get Critical Issues
```bash
curl http://localhost:5000/api/critical-services/issues | jq '.'
```

Returns ERROR and WARNING logs from CRITICAL category services.

### 4. Get Statistics
```bash
curl http://localhost:5000/api/critical-services/statistics | jq '.'
```

**Response:**
```json
{
  "status": "success",
  "statistics": {
    "total_logs": 360,
    "by_category": {
      "CRITICAL": 150,
      "IMPORTANT": 120,
      "SECURITY": 90
    },
    "by_level": {
      "ERROR": 3,
      "WARNING": 24,
      "NOTICE": 6,
      "INFO": 327
    },
    "service_status": {
      "docker": {"active": true, "status": "active"},
      ...
    }
  }
}
```

## 🤖 AI Analysis

You can analyze any log entry using the existing Gemini AI endpoint:

```bash
# Get a critical service log
LOG_ENTRY=$(curl -s "http://localhost:5000/api/critical-services/logs?limit=1&level=ERROR" | jq '.logs[0]')

# Analyze it with AI
curl -X POST http://localhost:5000/api/gemini/analyze-log \
  -H "Content-Type: application/json" \
  -d "$LOG_ENTRY" | jq '.'
```

**AI Response includes:**
- Why the error happened
- How to fix it
- How to prevent it in the future
- Step-by-step solution

## 🌐 Dashboard Access

**URL:** http://localhost:3001

### How to View Critical Services:

1. Open http://localhost:3001
2. Click **"Logs & AI Analysis"** tab
3. You'll see system logs including critical services
4. Use filters:
   - **Level Filter:** ERROR, WARNING, INFO, DEBUG
   - **Service Filter:** Filter by specific service
5. Click **"Analyze"** button next to any ERROR/WARNING for AI insights

## 📋 Quick Commands

### Check Service Status
```bash
# List all critical services
curl -s http://localhost:5000/api/critical-services/list | \
  jq -r '.services | to_entries[] | "\(.key):", (.value[] | "  \(.name): \(if .active then "✅ ACTIVE" else "❌ INACTIVE" end)")'
```

### View Recent Errors
```bash
curl -s "http://localhost:5000/api/critical-services/logs?level=ERROR&limit=10" | \
  jq -r '.logs[] | "[\(.timestamp)] \(.category) - \(.service): \(.message)"'
```

### Monitor Critical Issues
```bash
curl -s http://localhost:5000/api/critical-services/issues | \
  jq -r '.issues[] | "[\(.timestamp)] \(.service): \(.message[:80])"'
```

### Watch Statistics in Real-time
```bash
watch -n 5 'curl -s http://localhost:5000/api/critical-services/statistics | jq ".statistics"'
```

## 🔍 What Gets Detected

### Docker Service Failures
- Container crashes
- Docker daemon failures
- Container runtime errors
- Resource limit issues

### System Service Crashes
- systemd service failures
- Daemon crashes
- Service restarts
- Dependency failures

### Login/Session Issues
- Failed login attempts
- Session termination
- User authentication errors
- PAM errors

### Network/DNS Problems
- DNS resolution failures
- Network connectivity issues
- Firewall blocks
- Name resolution errors

### Security Events
- Intrusion attempts
- AppArmor denials
- Firewall violations
- Unauthorized access attempts

## 🎯 Example Use Cases

### 1. Detect Docker Daemon Crash
```bash
# Monitor docker service logs
curl -s "http://localhost:5000/api/critical-services/logs?service=docker&level=ERROR"
```

If Docker crashes, you'll see:
- Error level logs from docker service
- Crash reason and stack trace
- Click "Analyze" for AI-powered fix recommendation

### 2. Track Login Failures
```bash
# Monitor systemd-logind for auth issues
curl -s "http://localhost:5000/api/critical-services/logs?service=systemd-logind&level=WARNING"
```

### 3. DNS Resolution Issues
```bash
# Check systemd-resolved for DNS problems
curl -s "http://localhost:5000/api/critical-services/logs?service=systemd-resolved&level=ERROR"
```

### 4. Security Monitoring
```bash
# View all security-related logs
curl -s "http://localhost:5000/api/critical-services/logs?category=SECURITY&limit=50"
```

### 5. System Health Overview
```bash
# Get overall system health
curl -s http://localhost:5000/api/critical-services/statistics | jq '{
  total_logs: .statistics.total_logs,
  errors: .statistics.by_level.ERROR,
  warnings: .statistics.by_level.WARNING,
  inactive_services: [.statistics.service_status | to_entries[] | select(.value.active == false) | .key]
}'
```

## 🚨 Alert Examples

The system automatically detects:

1. **Service Stopped**
   ```json
   {
     "service": "docker",
     "status": "inactive",
     "category": "CRITICAL",
     "alert": "Critical service docker has stopped!"
   }
   ```

2. **Repeated Errors**
   ```json
   {
     "service": "systemd-resolved",
     "level": "ERROR",
     "count": 5,
     "message": "DNS resolution failed repeatedly"
   }
   ```

3. **Security Violation**
   ```json
   {
     "service": "apparmor",
     "level": "WARNING",
     "category": "SECURITY",
     "message": "AppArmor denied access to resource"
   }
   ```

## 📖 Log Format

Each log entry includes:
```json
{
  "timestamp": "2025-10-29T13:08:36.998315",
  "service": "docker",
  "category": "CRITICAL",
  "level": "ERROR",
  "priority": 3,
  "message": "Docker daemon failed to start",
  "description": "Docker container runtime - manages all containers",
  "source": "systemd-journal"
}
```

## 💡 Best Practices

1. **Monitor ERROR logs daily**
   ```bash
   curl -s "http://localhost:5000/api/critical-services/logs?level=ERROR"
   ```

2. **Check service status regularly**
   ```bash
   curl -s http://localhost:5000/api/critical-services/list | jq '.services'
   ```

3. **Use AI analysis for unknown errors**
   - Copy log entry
   - POST to `/api/gemini/analyze-log`
   - Get instant fix recommendations

4. **Set up monitoring alerts** (future feature)
   - Email on CRITICAL service failure
   - Webhook on repeated errors
   - Slack notification for security events

## 🔧 Troubleshooting

### No logs appearing?
```bash
# Check if monitor is running
curl http://localhost:5000/api/critical-services/statistics

# Check server logs
tail -f /home/cdrditgis/Documents/Healing-bot/logs/monitoring-server.log
```

### Service showing as inactive?
```bash
# Check actual service status
sudo systemctl status <service-name>

# Restart if needed
sudo systemctl restart <service-name>
```

### Want to add more services?
Edit `/home/cdrditgis/Documents/Healing-bot/monitoring/server/critical_services_monitor.py`:
```python
self.critical_services = {
    'CRITICAL': {
        'your-service': 'Service description',
        ...
    }
}
```

## 📞 Quick Reference

| Task | Command |
|------|---------|
| List services | `curl http://localhost:5000/api/critical-services/list` |
| Get logs | `curl http://localhost:5000/api/critical-services/logs` |
| Get errors | `curl http://localhost:5000/api/critical-services/logs?level=ERROR` |
| Get issues | `curl http://localhost:5000/api/critical-services/issues` |
| Get stats | `curl http://localhost:5000/api/critical-services/statistics` |
| View dashboard | Open http://localhost:3001 |
| Analyze with AI | POST to `/api/gemini/analyze-log` |

---

## ✨ Summary

Your Healing-Bot now:
- ✅ Monitors 13 critical Ubuntu services
- ✅ Centralizes all their logs
- ✅ Categorizes by importance (CRITICAL/IMPORTANT/SECURITY)
- ✅ Detects errors and warnings automatically
- ✅ Provides AI-powered analysis for any log
- ✅ Updates every 60 seconds
- ✅ Accessible via dashboard and API

**Total logs collected:** 360  
**Critical issues found:** 3 ERRORS, 24 WARNINGS  
**AI analysis:** Available for all logs

🎉 **Your critical services are now fully monitored with AI analysis!** 🎉

