# 🛡️ Healing Bot Dashboard - Complete Guide

## Overview

The Healing Bot Dashboard is a comprehensive web-based interface for real-time system monitoring, automated healing, and AI-powered log analysis.

---

## ✨ Features

### 1. **Real-time Monitoring** 📊
- Live CPU, Memory, Disk, and Network usage
- Color-coded health indicators (🟢 Healthy, 🟡 Warning, 🔴 Critical)
- Interactive real-time charts
- WebSocket-based instant updates

### 2. **Service Auto-Restart** ⚙️
- Automatic detection of failed services
- One-click service restart
- Monitored services:
  - nginx
  - MySQL
  - SSH
  - Docker
  - PostgreSQL
- Manual override toggle

### 3. **Resource Hog Detection** 💀
- Real-time process monitoring
- CPU and memory usage tracking
- One-click process termination
- Configurable thresholds
- Automatic alerts for resource hogs

### 4. **SSH Intrusion Detection** 🔐
- Real-time SSH login monitoring
- Failed login attempt tracking
- Automatic IP blocking after 5 failed attempts
- Geographic location display
- Manual IP block/unblock

### 5. **Disk Cleanup Automation** 🧹
- Automatic cleanup when disk > threshold
- Cleans:
  - APT cache
  - Journal logs (7 days retention)
  - Old log files
- Real-time freed space reporting
- Schedulable cleanups

### 6. **Discord Alerts** 📡
- Real-time Discord notifications
- Configurable alert channels
- Severity-based formatting:
  - ℹ️ Info (Blue)
  - ✅ Success (Green)
  - ⚠️ Warning (Yellow)
  - ❌ Error (Red)
  - 🚨 Critical (Purple)
- Test notification button

### 7. **AI Log Analysis** 🤖
- TF-IDF-based keyword extraction
- Anomaly detection
- "Explain this log" feature
- Visual keyword frequency charts
- Error clustering

### 8. **CLI Terminal** ⚡
- Integrated command execution
- Command history tracking
- Whitelisted safe commands:
  - `help` - Show available commands
  - `status` - System status
  - `services` - List services
  - `processes` - Top processes
  - `disk` - Disk usage
  - `logs` - Recent logs
  - `restart <service>` - Restart service

---

## 🚀 Quick Start

### 1. Installation

```bash
# Navigate to the project directory
cd /home/cdrditgis/Documents/Healing-bot

# Install dependencies
pip install -r monitoring/server/healing_requirements.txt

# Set up environment variables
cp config/env.template .env
nano .env  # Add your Discord webhook
```

### 2. Configuration

Edit `.env`:

```bash
# Discord Integration
DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL

# Dashboard Port
HEALING_DASHBOARD_PORT=5001

# Monitoring Thresholds
CPU_THRESHOLD=90.0
MEMORY_THRESHOLD=85.0
DISK_THRESHOLD=80.0
```

### 3. Launch Dashboard

```bash
# Start the dashboard server
python monitoring/server/healing_dashboard_api.py

# Or use uvicorn for production
uvicorn monitoring.server.healing_dashboard_api:app --host 0.0.0.0 --port 5001
```

### 4. Access Dashboard

Open your browser and navigate to:
```
http://localhost:5001
```

---

## 📖 Usage Guide

### Dashboard Tabs

#### 📊 Overview
- Real-time system metrics
- Live performance charts
- Recent activity log
- Quick health status

#### ⚙️ Services
- Service status list
- Auto-restart toggle
- Manual service restart
- Service health indicators

#### 🔍 Processes
- Top CPU/Memory processes
- Process termination
- Threshold configuration
- Resource usage graphs

#### 🔐 SSH Security
- Failed login attempts
- IP blocking/unblocking
- Geographic data
- Suspicious IP alerts

#### 💿 Disk Management
- Disk usage monitoring
- Threshold configuration
- Manual/automatic cleanup
- Cleanup history and logs

#### 📝 Logs & AI
- Real-time log streaming
- Log search and filtering
- AI-powered analysis
- Keyword frequency visualization

#### 🔔 Alerts
- Discord webhook configuration
- Module-specific alerts
- Test notifications
- Alert history

#### ⚡ CLI Terminal
- Execute safe commands
- View command history
- Real-time output
- Command suggestions

---

## 🔧 Advanced Configuration

### Service Monitoring

Add services to monitor in `healing_dashboard_api.py`:

```python
CONFIG = {
    "services_to_monitor": [
        "nginx",
        "mysql", 
        "ssh",
        "docker",
        "postgresql",
        "redis",  # Add your service
    ]
}
```

### Threshold Configuration

Adjust thresholds via API or configuration:

```python
CONFIG = {
    "auto_restart": True,
    "cpu_threshold": 90.0,      # Kill processes above 90% CPU
    "memory_threshold": 85.0,    # Alert at 85% memory
    "disk_threshold": 80.0,      # Cleanup at 80% disk
}
```

### Discord Webhook Setup

1. Go to Discord Server Settings
2. Integrations → Webhooks
3. Create New Webhook
4. Copy Webhook URL
5. Add to `.env` or dashboard configuration

---

## 🔒 Security Considerations

### 1. **Sudo Access**
The dashboard requires sudo access for:
- Service restarts
- IP blocking (iptables)
- Disk cleanup
- Process termination

Configure sudoers:
```bash
sudo visudo
# Add line:
your_user ALL=(ALL) NOPASSWD: /bin/systemctl, /sbin/iptables, /usr/bin/apt-get, /usr/bin/journalctl
```

### 2. **CLI Command Whitelist**
Only whitelisted commands can be executed. Never add dangerous commands like `rm -rf`.

### 3. **Authentication** (Recommended)
For production, add authentication:
```bash
# Install fastapi-users
pip install fastapi-users

# Implement authentication in healing_dashboard_api.py
```

### 4. **HTTPS** (Production)
Use reverse proxy with SSL:
```bash
# nginx configuration
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 🔍 API Documentation

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/metrics` | GET | System metrics |
| `/api/services` | GET | Service statuses |
| `/api/services/{name}/restart` | POST | Restart service |
| `/api/processes/top` | GET | Top processes |
| `/api/processes/kill` | POST | Kill process |
| `/api/ssh/attempts` | GET | SSH intrusion attempts |
| `/api/ssh/block` | POST | Block IP |
| `/api/ssh/unblock` | POST | Unblock IP |
| `/api/disk/status` | GET | Disk usage |
| `/api/disk/cleanup` | POST | Run cleanup |
| `/api/logs` | GET | Get logs |
| `/api/logs/analyze` | POST | AI log analysis |
| `/api/cli/execute` | POST | Execute CLI command |
| `/api/discord/test` | POST | Test Discord alert |
| `/api/config` | GET/POST | Configuration |

### WebSocket

**Endpoint:** `/ws/healing`

Real-time system metrics broadcast every 2 seconds:
```json
{
    "cpu": 45.2,
    "memory": 62.8,
    "disk": 58.3,
    "network": {
        "bytes_sent": 1234567,
        "bytes_recv": 7654321
    },
    "timestamp": "2025-10-30T12:00:00"
}
```

---

## 📊 Monitoring Best Practices

### 1. **Set Appropriate Thresholds**
- CPU: 85-90%
- Memory: 80-85%
- Disk: 75-80%

### 2. **Regular Cleanup**
- Schedule daily disk cleanup
- Keep logs < 7 days
- Monitor cleanup effectiveness

### 3. **Alert Configuration**
- Enable critical alerts
- Test Discord notifications
- Set up alert rotation

### 4. **Service Monitoring**
- Monitor critical services only
- Set auto-restart for production services
- Manual restart for dev services

---

## 🐛 Troubleshooting

### Dashboard Won't Start
```bash
# Check port availability
netstat -tlnp | grep 5001

# Check dependencies
pip install -r monitoring/server/healing_requirements.txt

# Check logs
python monitoring/server/healing_dashboard_api.py --log-level debug
```

### Services Won't Restart
```bash
# Check sudo permissions
sudo systemctl restart nginx

# Verify service name
systemctl list-units --type=service | grep nginx

# Check service logs
journalctl -u nginx -n 50
```

### Discord Alerts Not Working
```bash
# Test webhook manually
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test message"}'

# Verify webhook in dashboard config
# Check firewall/network restrictions
```

### WebSocket Connection Issues
```bash
# Check WebSocket support
# Verify reverse proxy configuration
# Check browser console for errors
```

---

## 🎯 Performance Tips

1. **Optimize Monitoring Interval**
   - Default: 2 seconds
   - Reduce for better performance
   - Increase for more frequent updates

2. **Limit Log Buffer**
   - Default: 1000 logs
   - Adjust based on RAM availability

3. **Process Monitoring**
   - Monitor top 10-20 processes
   - Avoid scanning all processes

4. **Disk I/O**
   - Cache service statuses
   - Batch log reads
   - Use async operations

---

## 📚 Further Reading

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [psutil Documentation](https://psutil.readthedocs.io/)
- [Discord Webhooks](https://discord.com/developers/docs/resources/webhook)
- [TF-IDF Explanation](https://en.wikipedia.org/wiki/Tf%E2%80%93idf)

---

## 🤝 Support

For issues or questions:
- GitHub Issues: [KAXUN01/Heal-X-Bot](https://github.com/KAXUN01/Heal-X-Bot)
- Documentation: `/docs/guides/`

---

**Last Updated:** October 30, 2025  
**Version:** 1.0.0  
**Status:** ✅ Production Ready

