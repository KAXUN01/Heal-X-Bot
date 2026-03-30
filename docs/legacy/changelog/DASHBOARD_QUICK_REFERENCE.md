# 🛡️ Dashboard Quick Reference

## 🚀 Start Dashboard

```bash
./start-unified-dashboard.sh
```

## 🌐 Access URLs

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| **ML Monitoring** | http://localhost:3001 | DDoS detection, IP blocking, ML metrics |
| **Healing Dashboard** | http://localhost:3001/static/healing-dashboard.html | Services, SSH, Disk, CLI |

## 🧪 Test Everything Works

```bash
python3 test-unified-dashboard.py
```

## ⚡ Quick Commands

### Via CLI Terminal Tab
```bash
help              # Show commands
status            # System overview
services          # List all services
processes         # Top processes
disk              # Disk usage
logs              # Recent logs
restart nginx     # Restart service
```

### Via curl (API)
```bash
# Get system metrics
curl http://localhost:3001/api/metrics

# Get ML metrics
curl http://localhost:3001/api/metrics/ml

# Get services
curl http://localhost:3001/api/services

# Block IP
curl -X POST http://localhost:3001/api/ssh/block \
  -H "Content-Type: application/json" \
  -d '{"ip":"192.168.1.100"}'

# Test Discord
curl -X POST http://localhost:3001/api/discord/test \
  -H "Content-Type: application/json" \
  -d '{"webhook":"YOUR_WEBHOOK_URL"}'
```

## 🔧 Configuration

### Set Discord Webhook
```bash
# Option 1: Via .env file
echo "DISCORD_WEBHOOK=your_webhook_url" >> .env

# Option 2: Via dashboard (Alerts tab)
# Paste webhook URL and click Test
```

### Enable Sudo (for full features)
```bash
sudo visudo
# Add:
your_username ALL=(ALL) NOPASSWD: /bin/systemctl, /sbin/iptables, /usr/bin/apt-get
```

### Change Port
```bash
export DASHBOARD_PORT=8080
./start-unified-dashboard.sh
```

## 📊 Features At A Glance

### ML Monitoring Dashboard
- ✅ Model accuracy/precision/recall
- ✅ Attack type detection
- ✅ IP blocking management
- ✅ Geographic attack mapping
- ✅ Historical analytics

### Healing Dashboard  
- ✅ Service auto-restart (nginx, MySQL, SSH, etc.)
- ✅ Kill resource hogs
- ✅ SSH intrusion blocking
- ✅ Automatic disk cleanup
- ✅ Discord notifications
- ✅ AI log analysis
- ✅ CLI terminal

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port in use | `export DASHBOARD_PORT=8080` |
| Can't restart services | Configure sudoers (see above) |
| Discord not working | Check webhook URL in .env |
| Dashboard won't start | `pip3 install -r monitoring/dashboard/requirements.txt` |
| WebSocket errors | Check firewall, use correct URL |

## 📚 Full Documentation

- **Unified Guide**: [docs/guides/UNIFIED_DASHBOARD_GUIDE.md](docs/guides/UNIFIED_DASHBOARD_GUIDE.md)
- **Healing Features**: [docs/guides/HEALING_DASHBOARD_GUIDE.md](docs/guides/HEALING_DASHBOARD_GUIDE.md)
- **Quick Start**: [docs/guides/QUICK_START_DASHBOARD.md](docs/guides/QUICK_START_DASHBOARD.md)

## ✅ Feature Checklist

```bash
# Run test suite
python3 test-unified-dashboard.py

# Should show:
# ✅ All ML monitoring features working
# ✅ All healing features working
# ✅ API endpoints responding
# ✅ WebSocket connected
```

---

**Need Help?** Check logs: `monitoring/logs/unified_dashboard.log`

