# System Monitoring - Quick Reference

## ✅ What's Configured

Your Healing-Bot now monitors **SYSTEM SERVICES ONLY** for failures and crashes.

### What Is Monitored
- ✅ **Docker containers** - Crashes, restarts, errors
- ✅ **systemd services** - Service failures, daemon crashes
- ✅ **System logs** - syslog, auth, kernel messages
- ✅ **Web servers** - Apache, nginx errors
- ✅ **Security** - Authentication failures, unauthorized access

### What Is NOT Monitored
- ❌ Healing-Bot application logs (saves disk space)
- ❌ Dashboard logs
- ❌ Model API logs
- ❌ Internal service logs

## 🎯 Disk Space

| Item | Before | After | Savings |
|------|--------|-------|---------|
| Centralized logs | 348 MB | 4 KB | **348 MB** |
| Memory usage | 10,000 logs | 1,000 logs | **90%** |
| Collection rate | 50 lines/container | 10 lines/container | **80%** |

**Result:** Minimal disk usage, only essential monitoring

## 🚀 How to Use

### Dashboard
1. Open **http://localhost:3001**
2. Click **"Logs & AI Analysis"** tab
3. View system service logs
4. Filter by level (ERROR, WARNING, INFO, DEBUG)
5. Click **"Analyze"** on errors for AI insights

### Command Line
```bash
# View recent system logs
curl http://localhost:5000/api/system-logs/recent?limit=20 | jq '.'

# View only errors
curl "http://localhost:5000/api/system-logs/recent?level=ERROR" | jq '.'

# Check statistics
curl http://localhost:5000/api/system-logs/statistics | jq '.'

# Check active sources
curl http://localhost:5000/api/system-logs/sources | jq '.'
```

## 🔍 What You'll Detect

### Docker Issues
- Container crashes
- Container restarts
- Application errors in containers
- Resource limits hit

### systemd Services
- Service failures
- Daemon crashes
- Automatic restarts
- Service dependencies issues

### Security Events
- Failed login attempts (auth.log)
- Unauthorized access attempts
- Suspicious activity
- SSH brute force attempts

### System Errors
- Kernel panics
- Hardware failures
- Driver issues
- Out of memory (OOM) events

## 📊 Current Status

System is collecting logs every **30 seconds** from:
- Docker daemon
- systemd journal
- System logs (if `adm` group access granted)

**Logs in memory:** Max 1,000 (auto-rotates, keeps recent)  
**Disk usage:** Minimal (~10 MB max)

## 🔧 Optional: Full Access

To monitor **all** system logs (syslog, auth.log, kern.log):

```bash
# Add your user to the 'adm' group
sudo usermod -a -G adm $USER

# Then log out and log back in
```

Current access without `adm` group:
- ✅ Docker logs
- ✅ systemd journal
- ⚠️  syslog (requires `adm`)
- ⚠️  auth.log (requires `adm`)
- ⚠️  kern.log (requires `adm`)

## 💡 Examples

### Detect Docker Container Crash
1. Container crashes
2. System logs it to Docker daemon
3. Healing-Bot collects the log (next 30s cycle)
4. Dashboard shows ERROR log
5. Click "Analyze" for AI-powered fix suggestions

### Detect systemd Service Failure
1. systemd service fails (e.g., nginx crash)
2. systemd logs the failure to journal
3. Healing-Bot collects it immediately
4. Dashboard shows the failure
5. AI analysis explains why and how to fix

### Detect Security Issue
1. Failed SSH login attempt
2. Logged to auth.log
3. Healing-Bot collects it (if `adm` group)
4. Shows as WARNING in dashboard
5. AI analysis detects brute force attempt

## 🎯 Key Benefits

✅ **Zero application log bloat** - Only system services  
✅ **Crash detection** - Know when services fail  
✅ **AI analysis** - Instant fix recommendations  
✅ **Minimal disk usage** - ~10 MB max  
✅ **Real-time monitoring** - 30-second intervals  
✅ **Security alerts** - Authentication failures detected  

## 📞 Quick Commands

```bash
# Check disk usage
du -sh logs/
du -sh monitoring/server/logs/centralized/

# View monitoring server status
tail -f logs/monitoring-server.log

# Restart monitoring server
cd /home/cdrditgis/Documents/Healing-bot
lsof -ti:5000 | xargs kill -9
source venv/bin/activate
cd monitoring/server
python app.py > ../../logs/monitoring-server.log 2>&1 &

# Check what's being monitored
curl http://localhost:5000/api/system-logs/sources | jq '.sources[].name'
```

## 📖 Full Guides

- **SYSTEM_LOG_MONITORING_GUIDE.md** - Complete monitoring guide
- **LOG_MANAGEMENT_GUIDE.md** - Disk space optimization
- **GEMINI_API_KEY_SETUP.md** - AI analysis setup

---

**Focus:** System service failures & crashes only  
**Disk:** Minimal usage (~10 MB)  
**Updates:** Every 30 seconds  
**AI:** Powered by Google Gemini  

🎊 **Your system is now lean and focused!** 🎊

