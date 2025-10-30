# System-Wide Log Monitoring Guide

## Overview

Your Healing-Bot now has **system-wide log monitoring** capabilities! It can collect and analyze logs from your entire Ubuntu system, not just the Healing-Bot services.

## What Logs Are Monitored?

The system automatically collects logs from:

### ✅ Currently Active Sources
- **Docker**: Logs from all running Docker containers
- **systemd**: System service logs via journalctl
- **syslog**: General system logs (`/var/log/syslog`)
- **auth**: Authentication logs (`/var/log/auth.log`)
- **kernel**: Kernel logs (`/var/log/kern.log`)
- **Apache**: Apache web server logs (`/var/log/apache2/`)
- **nginx**: Nginx web server logs (`/var/log/nginx/`)

### Log Collection Details
- **Collection Interval**: Every 30 seconds
- **Log Retention**: Last 10,000 logs in memory
- **Automatic Parsing**: Different formats for each log source
- **Level Detection**: Automatically detects ERROR, WARNING, INFO, DEBUG

## How to Access System Logs

### 1. Via Dashboard UI

1. Open the dashboard: **http://localhost:3001**
2. Navigate to the **"Logs & AI Analysis"** tab
3. Click on the **"System (Docker, syslog, etc.)"** tab
4. View logs from all system services
5. Use filters to:
   - Filter by service
   - Filter by log level (ERROR, WARNING, INFO, DEBUG)
   - Click "Analyze" on any ERROR/WARNING for AI insights

### 2. Via API Endpoints

#### Get Recent System Logs
```bash
# Get last 100 system logs
curl http://localhost:5000/api/system-logs/recent?limit=100

# Filter by level
curl "http://localhost:5000/api/system-logs/recent?limit=100&level=ERROR"

# Filter by source
curl "http://localhost:5000/api/system-logs/recent?limit=100&source=docker"
```

#### Get Statistics
```bash
curl http://localhost:5000/api/system-logs/statistics | jq '.'
```

#### Get Available Sources
```bash
curl http://localhost:5000/api/system-logs/sources | jq '.'
```

## Example Use Cases

### 1. Monitor Docker Containers
See logs from all your Docker containers in one place, with automatic error detection.

### 2. Track Authentication Events
Monitor login attempts, SSH connections, and sudo usage from `auth.log`.

### 3. Detect Kernel Issues
Catch kernel panics, driver errors, and hardware issues early.

### 4. Web Server Monitoring
Track Apache/nginx errors and access patterns.

### 5. systemd Service Health
Monitor all systemd services for failures and restarts.

## Log Format

Each log entry includes:
- `timestamp`: ISO 8601 format
- `service`: Service name (e.g., `docker-mycontainer`, `systemd-nginx.service`)
- `level`: ERROR, WARNING, INFO, or DEBUG
- `message`: The log message
- `source`: Origin (docker, systemd, syslog, etc.)
- Additional metadata depending on source

Example:
```json
{
  "timestamp": "2025-10-29T12:31:21.785438",
  "service": "systemd-kernel",
  "level": "INFO",
  "message": "audit: type=1400 apparmor...",
  "source": "systemd",
  "priority": 5
}
```

## AI Analysis

You can analyze any system log using Gemini AI:
1. Click the "Analyze" button next to ERROR or WARNING logs
2. Get AI-powered insights on:
   - What caused the error
   - How to fix it
   - How to prevent it in the future

## Permissions

Some system logs require elevated permissions:

### Current User Permissions
Without sudo, you can access:
- ✅ Docker logs (if in `docker` group)
- ✅ systemd journal (via `journalctl`)
- ❌ `/var/log/syslog` (requires `adm` group)
- ❌ `/var/log/auth.log` (requires `adm` group)
- ❌ `/var/log/kern.log` (requires `adm` group)

### To Enable Full Access

**Option 1: Add your user to the `adm` group (recommended)**
```bash
sudo usermod -a -G adm $USER
# Log out and log back in for changes to take effect
```

**Option 2: Run monitoring server as root (NOT recommended for security)**
```bash
sudo -E env PATH=$PATH python monitoring/server/app.py
```

## Configuration

### Adjust Collection Interval

Edit `monitoring/server/app.py`:
```python
# Change from 30 seconds to 60 seconds
system_log_collector.start_collection(interval_seconds=60)
```

### Enable/Disable Specific Sources

Edit `monitoring/server/system_log_collector.py`:
```python
self.log_sources = {
    'docker': {'enabled': True, 'parser': self.parse_docker_logs},
    'syslog': {'enabled': False, 'parser': self.parse_syslog},  # Disabled
    # ...
}
```

### Increase Log Retention

Edit `monitoring/server/system_log_collector.py`:
```python
self.max_logs = 50000  # Increase from 10,000 to 50,000
```

## Statistics

The system tracks:
- **Total logs collected**
- **Logs by level** (ERROR, WARNING, INFO, DEBUG)
- **Logs by source** (docker, systemd, syslog, etc.)
- **Logs by service** (specific services/containers)

View statistics:
- Dashboard: See real-time counts on the Logs tab
- API: `GET /api/system-logs/statistics`

## Troubleshooting

### No System Logs Appearing

1. **Wait 30 seconds** - First collection happens after initial interval
2. **Check permissions** - Some logs require `adm` group membership
3. **Verify services are running**:
   ```bash
   systemctl status docker
   systemctl status rsyslog
   ```
4. **Check collector status**:
   ```bash
   curl http://localhost:5000/api/system-logs/sources
   ```

### Permission Denied Errors

Add user to `adm` group:
```bash
sudo usermod -a -G adm $USER
# Then log out and log back in
```

### Docker Logs Not Showing

Ensure user is in `docker` group:
```bash
sudo usermod -a -G docker $USER
# Then log out and log back in
```

### Check Collector Logs

```bash
tail -f logs/monitoring-server.log | grep system_log_collector
```

## Architecture

```
┌─────────────────────────────────────────────┐
│         System Log Collector                │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Docker  │  │ systemd  │  │  syslog  │ │
│  │  Logs    │  │ Journal  │  │ /var/log │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │             │              │        │
│       └─────────────┼──────────────┘        │
│                     │                        │
│         ┌───────────▼───────────┐           │
│         │   Log Parser          │           │
│         │   - Level Detection   │           │
│         │   - Format Parsing    │           │
│         │   - Timestamp Norma-  │           │
│         │     lization          │           │
│         └───────────┬───────────┘           │
│                     │                        │
│         ┌───────────▼───────────┐           │
│         │   In-Memory Store     │           │
│         │   (10,000 logs max)   │           │
│         └───────────┬───────────┘           │
└─────────────────────┼─────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
   ┌────▼────┐              ┌───────▼────────┐
   │   API   │              │   Dashboard    │
   │ Endpoint│              │   (Web UI)     │
   └─────────┘              └────────────────┘
```

## Next Steps

1. **Add user to `adm` group** for full system log access
2. **Monitor your system** via the dashboard
3. **Use AI analysis** on system errors for instant solutions
4. **Set up alerts** (future feature) for critical system events

## Benefits

✅ **Centralized Monitoring**: All system logs in one place  
✅ **AI-Powered Analysis**: Instant insights on system errors  
✅ **Real-time Updates**: Logs collected every 30 seconds  
✅ **Multi-Source Support**: Docker, systemd, syslog, and more  
✅ **Intelligent Filtering**: By level, service, or source  
✅ **Security Monitoring**: Track authentication and access logs  
✅ **Performance Insights**: Identify system bottlenecks  

## API Reference

### GET /api/system-logs/recent
Get recent system logs with optional filtering.

**Parameters:**
- `limit` (int): Number of logs to return (default: 100)
- `level` (string): Filter by level (ERROR, WARNING, INFO, DEBUG)
- `source` (string): Filter by source (docker, systemd, syslog, etc.)

**Response:**
```json
{
  "status": "success",
  "logs": [...],
  "count": 100
}
```

### GET /api/system-logs/statistics
Get statistics about collected logs.

**Response:**
```json
{
  "status": "success",
  "statistics": {
    "total_logs": 400,
    "by_level": {...},
    "by_source": {...},
    "by_service": {...}
  }
}
```

### GET /api/system-logs/sources
Get list of available log sources.

**Response:**
```json
{
  "status": "success",
  "sources": [
    {
      "name": "docker",
      "enabled": true,
      "description": "Docker logs"
    },
    ...
  ]
}
```

---

**Enjoy comprehensive system monitoring with your Healing-Bot! 🛡️**

