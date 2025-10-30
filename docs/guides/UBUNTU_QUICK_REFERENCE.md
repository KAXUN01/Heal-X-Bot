# 🚀 Ubuntu Quick Reference - Healing-bot

Quick command reference for Ubuntu deployment.

---

## ⚡ Quick Start

### First Time Setup
```bash
# 1. Install dependencies
sudo ./quick-start-ubuntu.sh --first-time

# 2. Configure .env (add your Gemini API key)
python3 setup_env.py

# 3. Start system
./quick-start-ubuntu.sh
```

### Regular Start
```bash
./quick-start-ubuntu.sh
```

---

## 📋 Common Commands

### Service Control
```bash
# Start all services
./start-healing-bot-ubuntu.sh

# Start in development mode (separate terminals)
./start-healing-bot-ubuntu.sh --dev

# Stop all services
./start-healing-bot-ubuntu.sh --stop

# Check status
./start-healing-bot-ubuntu.sh --status

# View logs
./start-healing-bot-ubuntu.sh --logs

# Help
./start-healing-bot-ubuntu.sh --help
```

### Individual Services
```bash
# Model API
cd model && python3 main.py

# Network Analyzer
cd monitoring/server && python3 network_analyzer.py

# Monitoring Server
cd monitoring/server && python3 app.py

# Dashboard
cd monitoring/dashboard && python3 app.py

# Incident Bot
cd incident-bot && python3 main.py
```

---

## 🔍 Monitoring

### Check Status
```bash
# Service status
./start-healing-bot-ubuntu.sh --status

# Check ports
sudo netstat -tulpn | grep -E '8080|8000|8001|3001|5000'

# Check processes
ps aux | grep python3 | grep -E 'main.py|app.py|network_analyzer.py'
```

### View Logs
```bash
# All logs
tail -f logs/*.log

# Specific service
tail -f logs/dashboard.log
tail -f logs/model.log
tail -f logs/monitoring-server.log
tail -f logs/network-analyzer.log
tail -f logs/incident-bot.log

# Last 50 lines
tail -n 50 logs/dashboard.log

# Search errors
grep -i error logs/*.log
grep -i warning logs/*.log
```

---

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Find process on port 3001 (example)
sudo lsof -i :3001

# Kill process
kill -9 <PID>

# Or kill all healing-bot processes
pkill -f "python3.*main.py"
pkill -f "python3.*app.py"
pkill -f "python3.*network_analyzer.py"
```

### Restart Services
```bash
# Stop
./start-healing-bot-ubuntu.sh --stop

# Start
./start-healing-bot-ubuntu.sh
```

### Reinstall Dependencies
```bash
# All dependencies
pip3 install -r requirements.txt
pip3 install -r monitoring/server/requirements.txt
pip3 install -r monitoring/dashboard/requirements.txt
pip3 install -r incident-bot/requirements.txt
pip3 install -r model/requirements.txt

# Specific package
pip3 install <package-name>
```

### Fix .env Issues
```bash
# Check .env exists
ls -la .env

# Check Gemini API key
grep GEMINI_API_KEY .env

# Re-run setup wizard
python3 setup_env.py

# Manually edit
nano .env
```

---

## 🌐 Access Points

After starting the system:

- **Dashboard**: http://localhost:3001
- **Model API**: http://localhost:8080
- **Network Analyzer**: http://localhost:8000
- **Monitoring Server**: http://localhost:5000
- **Incident Bot**: http://localhost:8001

---

## 🔧 System Management

### Resource Monitoring
```bash
# CPU and memory
htop
# or
top

# Disk usage
df -h

# Memory usage
free -h

# Process tree
pstree -p
```

### Log Management
```bash
# Clear old logs
rm logs/*.log

# Archive logs
tar -czf logs-$(date +%Y%m%d).tar.gz logs/

# Rotate logs (keep last 10 days)
find logs/ -name "*.log" -mtime +10 -delete
```

### Permissions
```bash
# Make scripts executable
chmod +x start-healing-bot-ubuntu.sh
chmod +x quick-start-ubuntu.sh

# Set .env permissions (secure)
chmod 600 .env

# Fix all permissions
chmod +x *.sh
chmod 600 .env
```

---

## 🐛 Debug Mode

### Verbose Logging
```bash
# Run services with debug output
cd monitoring/server
python3 -u app.py 2>&1 | tee debug.log
```

### Check Python Environment
```bash
# Python version
python3 --version

# Installed packages
pip3 list

# Check specific package
pip3 show fastapi

# Virtual environment (if used)
which python3
```

### Network Debugging
```bash
# Check all listening ports
sudo netstat -tulpn

# Check specific port
sudo lsof -i :3001

# Test connection
curl http://localhost:3001
curl http://localhost:8080/health
```

---

## 📦 Updates

### Update Code
```bash
# Pull latest code
git pull origin main

# Reinstall dependencies
pip3 install -r requirements.txt --upgrade

# Restart services
./start-healing-bot-ubuntu.sh --stop
./start-healing-bot-ubuntu.sh
```

### Update System Packages
```bash
# Update package list
sudo apt update

# Upgrade packages
sudo apt upgrade -y

# Update Python packages
pip3 list --outdated
pip3 install --upgrade <package>
```

---

## 🔄 Backup & Restore

### Backup
```bash
# Backup .env file
cp .env .env.backup

# Backup entire project
tar -czf healing-bot-backup-$(date +%Y%m%d).tar.gz \
    --exclude='logs' \
    --exclude='.pids' \
    --exclude='__pycache__' \
    .
```

### Restore
```bash
# Restore .env
cp .env.backup .env

# Restore project
tar -xzf healing-bot-backup-YYYYMMDD.tar.gz
```

---

## 🚦 Systemd Service (Optional)

### Create Service
```bash
sudo nano /etc/systemd/system/healing-bot.service
```

Content:
```ini
[Unit]
Description=Automatic Self-Healing Bot
After=network.target

[Service]
Type=forking
User=your-username
WorkingDirectory=/path/to/healing-bot
ExecStart=/path/to/healing-bot/start-healing-bot-ubuntu.sh
ExecStop=/path/to/healing-bot/start-healing-bot-ubuntu.sh --stop
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Manage Service
```bash
# Enable (start on boot)
sudo systemctl enable healing-bot

# Start
sudo systemctl start healing-bot

# Stop
sudo systemctl stop healing-bot

# Restart
sudo systemctl restart healing-bot

# Status
sudo systemctl status healing-bot

# Logs
sudo journalctl -u healing-bot -f
```

---

## 📚 File Locations

### Scripts
- `start-healing-bot-ubuntu.sh` - Main startup script
- `quick-start-ubuntu.sh` - Quick start wrapper
- `setup_env.py` - Environment setup wizard

### Configuration
- `.env` - Environment variables (API keys)
- `env.template` - Template for .env

### Logs
- `logs/*.log` - Service logs
- `.pids/*.pid` - Process IDs

### Documentation
- `README.md` - Main documentation
- `UBUNTU_DEPLOYMENT_GUIDE.md` - Full Ubuntu guide
- `ENV_SETUP_GUIDE.md` - Environment setup
- `UBUNTU_QUICK_REFERENCE.md` - This file

---

## ⚙️ Environment Variables

### Required
```env
GEMINI_API_KEY=your_key_here  # Required for AI analysis
```

### Optional
```env
SLACK_WEBHOOK=...            # Slack notifications
AWS_ACCESS_KEY_ID=...        # AWS S3 uploads
AWS_SECRET_ACCESS_KEY=...    # AWS S3 uploads
AWS_REGION=us-east-1         # AWS region
S3_BUCKET_NAME=...           # S3 bucket name
MODEL_PORT=8080              # Custom ports
DASHBOARD_PORT=3001
```

---

## 🆘 Emergency Commands

### Kill Everything
```bash
# Force stop all services
./start-healing-bot-ubuntu.sh --stop

# If that doesn't work:
pkill -9 -f "python3.*healing-bot"
pkill -9 -f "model/main.py"
pkill -9 -f "network_analyzer.py"
pkill -9 -f "monitoring.*app.py"
pkill -9 -f "incident-bot/main.py"
```

### Reset Everything
```bash
# Stop all
./start-healing-bot-ubuntu.sh --stop

# Clear logs
rm logs/*.log

# Clear PIDs
rm .pids/*.pid

# Reinstall dependencies
pip3 install -r requirements.txt --force-reinstall

# Start fresh
./start-healing-bot-ubuntu.sh
```

### Check Everything
```bash
# System status
./start-healing-bot-ubuntu.sh --status

# Detailed check
ps aux | grep python3
sudo netstat -tulpn | grep python3
ls -la logs/
cat logs/*.log | grep -i error
```

---

## 📞 Quick Help

### Common Issues

| Issue | Solution |
|-------|----------|
| Port in use | `sudo lsof -i :PORT` then `kill -9 PID` |
| Module not found | `pip3 install <module>` |
| Permission denied | `chmod +x script.sh` |
| .env not found | `python3 setup_env.py` |
| Service won't start | Check logs: `tail -f logs/*.log` |
| Can't access dashboard | Check firewall, verify port 3001 |

### Get Help
```bash
# Script help
./start-healing-bot-ubuntu.sh --help

# Check logs
./start-healing-bot-ubuntu.sh --logs

# Check status
./start-healing-bot-ubuntu.sh --status
```

---

## 🎯 Tips

1. **Always check logs first** when troubleshooting
2. **Use development mode** (`--dev`) for easier debugging
3. **Keep .env secure** with `chmod 600 .env`
4. **Backup .env** before making changes
5. **Monitor resources** with `htop` during operation
6. **Use systemd** for production deployments
7. **Set up log rotation** to prevent disk filling
8. **Test in dev** before deploying to production

---

## 🔗 Useful Links

- **Gemini API**: https://makersuite.google.com/app/apikey
- **Documentation**: See `UBUNTU_DEPLOYMENT_GUIDE.md`
- **Environment Setup**: See `ENV_SETUP_GUIDE.md`
- **GitHub**: [Your repo URL]

---

**📖 For detailed information, see `UBUNTU_DEPLOYMENT_GUIDE.md`**

**🚀 Happy Healing-bot-ing on Ubuntu!**

