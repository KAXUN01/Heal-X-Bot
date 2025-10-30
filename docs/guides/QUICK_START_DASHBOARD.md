# 🚀 Quick Start - Healing Bot Dashboard

## One-Command Launch

```bash
./start-healing-dashboard.sh
```

That's it! The dashboard will start at **http://localhost:5001**

---

## What You'll See

### 1. **System Health Cards** (Top)
- 🔥 CPU Usage
- 💾 Memory Usage  
- 💿 Disk Usage
- ⚙️ Running Services
- 🚨 Active Alerts
- 🧹 Last Cleanup

### 2. **Interactive Tabs**

| Tab | Purpose |
|-----|---------|
| 📊 Overview | Real-time charts and activity |
| ⚙️ Services | Service management & auto-restart |
| 🔍 Processes | Resource hog detection |
| 🔐 SSH Security | Intrusion detection & IP blocking |
| 💿 Disk Management | Automated cleanup |
| 📝 Logs & AI | AI-powered log analysis |
| 🔔 Alerts | Discord notification config |
| ⚡ CLI Terminal | Execute commands |

---

## First-Time Setup (2 Minutes)

### 1. Configure Discord (Optional)

```bash
# Edit .env file
nano .env

# Add your Discord webhook
DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
```

### 2. Configure Sudo (For Full Features)

```bash
sudo visudo

# Add this line:
your_username ALL=(ALL) NOPASSWD: /bin/systemctl, /sbin/iptables, /usr/bin/apt-get
```

### 3. Restart Dashboard

```bash
# Stop with Ctrl+C
# Start again
./start-healing-dashboard.sh
```

---

## Quick Actions

### Test Everything Works

1. **Open Dashboard**: http://localhost:5001
2. **Check System Status**: Should show 🟢 Healthy
3. **View Services Tab**: See all monitored services
4. **Test Discord**: Alerts → Test Notification
5. **Try CLI**: Type `help` in CLI Terminal

### Common Commands

```bash
# In CLI Terminal tab:
status          # System overview
services        # List all services
processes       # Top CPU/memory processes
disk            # Disk usage
logs            # Recent logs
restart nginx   # Restart a service
```

---

## Features At A Glance

✅ **Real-time monitoring** (2-second updates)  
✅ **Auto-restart failed services**  
✅ **Kill resource hogs**  
✅ **Block SSH attackers**  
✅ **Auto disk cleanup**  
✅ **Discord alerts**  
✅ **AI log analysis**  
✅ **CLI terminal**

---

## Troubleshooting

### Dashboard Won't Start?

```bash
# Install dependencies manually
pip3 install -r monitoring/server/healing_requirements.txt

# Check if port is available
netstat -tlnp | grep 5001

# Use different port
export HEALING_DASHBOARD_PORT=8080
./start-healing-dashboard.sh
```

### Can't Restart Services?

```bash
# Test sudo access
sudo systemctl restart nginx

# If it fails, configure sudoers (see Setup above)
```

### Discord Not Working?

1. Check webhook URL is correct
2. Test webhook manually:
```bash
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test"}'
```

---

## Next Steps

📖 **Full Documentation**: `docs/guides/HEALING_DASHBOARD_GUIDE.md`  
🔧 **Advanced Config**: Edit `CONFIG` in `healing_dashboard_api.py`  
🚀 **Production Deploy**: Use systemd service (see guide)

---

## Need Help?

- 📚 Read the [Full Guide](HEALING_DASHBOARD_GUIDE.md)
- 🐛 Report issues on GitHub
- 💡 Check `/api/health` for API status

**Happy Monitoring! 🛡️**

