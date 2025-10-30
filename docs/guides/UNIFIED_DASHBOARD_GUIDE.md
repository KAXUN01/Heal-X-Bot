# 🛡️ Unified Healing Bot Dashboard

## Overview

The Unified Dashboard combines **TWO powerful systems**:
1. **ML Model Performance Monitoring** (Original Dashboard)
2. **System Health Management** (New Healing Features)

---

## 🚀 Quick Start

### Start the Unified Dashboard

```bash
# Navigate to project
cd /home/cdrditgis/Documents/Healing-bot

# Launch unified dashboard
./start-unified-dashboard.sh
```

### Access Points

| Dashboard | URL | Features |
|-----------|-----|----------|
| **ML Monitoring** | http://localhost:3001 | Attack detection, IP blocking, ML metrics |
| **Healing Dashboard** | http://localhost:3001/static/healing-dashboard.html | Services, SSH, Disk, CLI, Discord |

---

## 📊 Features

### From Original Dashboard (ML Monitoring)

✅ **ML Model Performance**
- Real-time accuracy, precision, recall metrics
- F1-score tracking
- Prediction time monitoring
- Model throughput analysis

✅ **Attack Detection**
- DDoS attack monitoring
- Attack type classification
- Hourly attack statistics
- Detection rate tracking

✅ **IP Blocking Management**
- View blocked IPs
- Manual block/unblock
- Blocking statistics
- Auto-blocking rules

✅ **Geographic Analysis**
- Attack source mapping
- Country-based statistics
- City-level tracking

✅ **Analytics Dashboard**
- Historical data analysis
- Trend visualization
- Performance metrics

### From New Healing Dashboard

✅ **Service Auto-Restart**
- nginx, MySQL, SSH, Docker, PostgreSQL
- Automatic failure detection
- One-click restart

✅ **Resource Hog Detection**
- Top CPU/Memory processes
- Process termination
- Threshold configuration

✅ **SSH Intrusion Detection**
- Failed login monitoring
- Auto-block after 5 attempts
- IP management

✅ **Disk Cleanup**
- Automatic cleanup
- Threshold-based triggers
- Space reporting

✅ **Discord Alerts**
- Real-time notifications
- Severity-based formatting
- Test notifications

✅ **AI Log Analysis**
- TF-IDF keyword extraction
- Anomaly detection
- Log explanations

✅ **CLI Terminal**
- Web-based command execution
- Command history
- Safe command whitelist

---

## 🔌 Unified API Endpoints

### ML Monitoring Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/metrics/ml` | GET | ML model metrics |
| `/api/metrics/attacks` | GET | Attack statistics |
| `/api/history/ml` | GET | ML metrics history |
| `/api/blocking/stats` | GET | Blocking statistics |
| `/api/blocking/ips` | GET | Blocked IPs list |
| `/api/blocking/block` | POST | Block IP |
| `/api/blocking/unblock` | POST | Unblock IP |

### System Healing Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/services` | GET | Service statuses |
| `/api/services/{name}/restart` | POST | Restart service |
| `/api/processes/top` | GET | Top processes |
| `/api/processes/kill` | POST | Kill process |
| `/api/ssh/attempts` | GET | SSH attempts |
| `/api/ssh/block` | POST | Block SSH attacker |
| `/api/disk/status` | GET | Disk usage |
| `/api/disk/cleanup` | POST | Run cleanup |
| `/api/discord/test` | POST | Test Discord |
| `/api/cli/execute` | POST | Execute CLI command |

### Shared Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/metrics` | GET | System metrics |
| `/api/metrics/system` | GET | System metrics |
| `/api/logs` | GET | Recent logs |
| `/api/config` | GET/POST | Configuration |
| `/ws` | WebSocket | Real-time updates |

---

## 🎨 Dashboard Usage

### ML Monitoring Dashboard (Main)

**Tabs:**
1. **Overview** - System status and key metrics
2. **Attacks** - Attack detection and statistics
3. **Blocking** - IP blocking management
4. **Geographic** - Attack source mapping
5. **Analytics** - Historical data analysis
6. **Logs** - System and AI logs

**Features:**
- Real-time WebSocket updates
- Interactive charts with Chart.js
- Export capabilities
- Mobile-responsive design

### Healing Dashboard

**Tabs:**
1. **📊 Overview** - Real-time system metrics
2. **⚙️ Services** - Service management
3. **🔍 Processes** - Resource monitoring
4. **🔐 SSH Security** - Intrusion detection
5. **💿 Disk Management** - Cleanup automation
6. **📝 Logs & AI** - AI analysis
7. **🔔 Alerts** - Discord configuration
8. **⚡ CLI Terminal** - Command execution

**Features:**
- Dark theme interface
- Color-coded health indicators
- Real-time charts
- Discord integration

---

## ⚙️ Configuration

### Environment Variables

```bash
# .env file
DASHBOARD_PORT=3001
MODEL_URL=http://localhost:8080
MONITORING_SERVER_URL=http://localhost:5000
NETWORK_ANALYZER_URL=http://localhost:8000

# Discord Integration
DISCORD_WEBHOOK=your_webhook_url

# Thresholds
CPU_THRESHOLD=90.0
MEMORY_THRESHOLD=85.0
DISK_THRESHOLD=80.0
```

### Services to Monitor

Edit `unified_app.py`:

```python
CONFIG = {
    "services_to_monitor": [
        "nginx",
        "mysql",
        "ssh",
        "docker",
        "postgresql",
        # Add your services here
    ]
}
```

### Sudo Permissions

For full functionality:

```bash
sudo visudo
# Add:
your_user ALL=(ALL) NOPASSWD: /bin/systemctl, /sbin/iptables, /usr/bin/apt-get, /usr/bin/journalctl
```

---

## 🔄 WebSocket Data Format

```json
{
  "timestamp": "2025-10-30T12:00:00",
  "ml_metrics": {
    "accuracy": 0.95,
    "precision": 0.93,
    "recall": 0.94,
    "f1_score": 0.935,
    "prediction_time_ms": 45.2,
    "throughput": 22.5
  },
  "system_metrics": {
    "cpu": 45.2,
    "memory": 62.8,
    "disk": 58.3
  },
  "attack_statistics": {
    "total_detections": 150,
    "ddos_attacks": 12,
    "detection_rate": 8.0
  },
  "blocking_statistics": {
    "total_blocked": 45,
    "currently_blocked": 12
  },
  "ml_history": {...},
  "system_history": {...}
}
```

---

## 🐛 Troubleshooting

### Dashboard Won't Start

```bash
# Check dependencies
pip install -r monitoring/dashboard/requirements.txt
pip install -r monitoring/server/healing_requirements.txt

# Check port
netstat -tlnp | grep 3001

# Use different port
export DASHBOARD_PORT=8080
./start-unified-dashboard.sh
```

### Features Not Working

| Issue | Solution |
|-------|----------|
| Services won't restart | Configure sudo permissions |
| IP blocking fails | Check iptables permissions |
| Discord not working | Verify webhook URL in .env |
| Disk cleanup fails | Check apt-get permissions |
| SSH logs empty | Check /var/log/auth.log exists |

### API Connection Issues

```bash
# Test API endpoints
curl http://localhost:3001/api/health
curl http://localhost:3001/api/metrics
curl http://localhost:3001/api/services

# Check logs
tail -f monitoring/logs/unified_dashboard.log
```

---

## 📈 Performance

### Resource Usage

| Component | CPU | Memory | Disk |
|-----------|-----|--------|------|
| Unified API | < 5% | ~100 MB | Minimal |
| ML Dashboard | < 1% | ~50 MB | Minimal |
| Healing Dashboard | < 1% | ~50 MB | Minimal |
| WebSocket (per client) | < 1% | ~2 MB | N/A |

### Monitoring Frequency

- System metrics: Every 2 seconds
- ML metrics: Every 2 seconds
- Service checks: Every 10 seconds
- SSH log parsing: On demand
- Disk checks: Every 60 seconds

---

## 🔒 Security

### Best Practices

1. **Use HTTPS** in production
2. **Add authentication** for API endpoints
3. **Restrict sudo** to specific commands only
4. **Whitelist IPs** for dashboard access
5. **Rotate Discord** webhook periodically
6. **Review logs** regularly
7. **Update dependencies** frequently

### Recommended nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Basic auth (optional)
    auth_basic "Healing Bot Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;
}
```

---

## 🚀 Advanced Usage

### Custom Commands

Add to `unified_app.py`:

```python
# In execute_cli_endpoint function
allowed_commands = [
    "help", "status", "services", 
    "processes", "disk", "logs", "restart",
    "your_custom_command"  # Add here
]

# Then handle the command
elif cmd_parts[0] == "your_custom_command":
    # Your logic here
    output = "Custom command output"
```

### Custom Alerts

```python
# Send custom Discord alert
send_discord_alert("Your message here", "warning")
```

### Custom Thresholds

```python
# In monitoring_loop function
if metrics.get('cpu', 0) > 95:
    send_discord_alert("Critical CPU usage!", "critical")
```

---

## 📚 Documentation

- **Old Dashboard Features**: See original `dashboard.html`
- **New Healing Features**: `HEALING_DASHBOARD_GUIDE.md`
- **API Reference**: `/api/health` endpoint returns all routes
- **Quick Start**: `QUICK_START_DASHBOARD.md`

---

## ✅ Feature Checklist

### ML Monitoring (Original)
- [x] ML model metrics
- [x] Attack detection
- [x] IP blocking management
- [x] Geographic analysis
- [x] Analytics dashboard
- [x] Historical data

### System Healing (New)
- [x] Service auto-restart
- [x] Resource hog detection
- [x] SSH intrusion detection
- [x] Disk cleanup automation
- [x] Discord alerts
- [x] AI log analysis
- [x] CLI terminal integration

### Unified Features
- [x] Combined API
- [x] Shared WebSocket
- [x] Unified logging
- [x] Single configuration
- [x] Both dashboards accessible
- [x] No conflicts

---

## 🎉 Summary

**The Unified Dashboard provides:**
- ✅ All original ML monitoring features
- ✅ All new healing management features
- ✅ Single API backend
- ✅ Dual dashboard access
- ✅ Real-time updates for both
- ✅ Comprehensive monitoring solution

**Access both dashboards from one server on port 3001!**

---

**Last Updated:** October 30, 2025  
**Version:** 2.0.0  
**Status:** ✅ Production Ready

