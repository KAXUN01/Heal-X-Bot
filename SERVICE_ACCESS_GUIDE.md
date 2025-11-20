# Service Access Guide

## 🔍 Service Status

All services are bound to `0.0.0.0` which means they should be accessible from:
- `localhost` / `127.0.0.1` (local machine)
- Your machine's IP address (from other machines on the network)

## 🌐 Access URLs

### ✅ Working Services

1. **Monitoring Server**
   - URL: http://localhost:5000
   - API Docs: http://localhost:5000/
   - Health: http://localhost:5000/health
   - Status: ✅ Working

2. **Network Analyzer**
   - URL: http://localhost:8000
   - Health: http://localhost:8000/active-threats
   - Status: ✅ Working

3. **Incident Bot**
   - URL: http://localhost:8001
   - Root: http://localhost:8001/
   - Status: ✅ Working (no /health endpoint, use /)

4. **Healing Dashboard API**
   - URL: http://localhost:5001
   - Health: http://localhost:5001/api/health
   - Dashboard: http://localhost:5001/static/healing-dashboard.html
   - Status: ✅ Working

### ⚠️ Issue Found

5. **Model API (Port 8080)**
   - URL: http://localhost:8080
   - Status: ❌ **Not responding** - Protobuf version conflict
   - Error: `ImportError: cannot import name 'runtime_version' from 'google.protobuf'`
   - Fix: Update protobuf (see below)

## 🔧 Troubleshooting Browser Access

### If you can't access services in browser:

1. **Check if services are running:**
   ```bash
   ss -tlnp | grep -E ":(5000|8080|8000|8001|5001)"
   ```

2. **Test with curl first:**
   ```bash
   curl http://localhost:5000/health
   curl http://localhost:8000/active-threats
   curl http://localhost:5001/api/health
   ```

3. **Try different browser addresses:**
   - http://localhost:5000
   - http://127.0.0.1:5000
   - http://0.0.0.0:5000 (might not work)

4. **Check firewall:**
   ```bash
   sudo ufw status
   # If firewall is active, allow the ports
   sudo ufw allow 5000/tcp
   sudo ufw allow 8080/tcp
   sudo ufw allow 8000/tcp
   sudo ufw allow 8001/tcp
   sudo ufw allow 5001/tcp
   ```

5. **Check browser console:**
   - Open browser developer tools (F12)
   - Check Console tab for errors
   - Check Network tab to see if requests are being made

## 🔨 Fixing Model API (Port 8080)

The Model API has a protobuf version conflict. To fix:

```bash
cd /home/kasun/Documents/Heal-X-Bot
source .venv/bin/activate

# Install correct protobuf version for TensorFlow
pip install "protobuf>=5.28.0,<6.0.0" --upgrade

# Restart the model service
pkill -f "model/main.py"
cd model
python3 main.py &
```

## 📋 Quick Access Checklist

- [ ] Services are running (check `ps aux | grep python3`)
- [ ] Ports are listening (check `ss -tlnp | grep -E ":(5000|8080|8000|8001|5001)"`)
- [ ] Can access via curl (test each URL)
- [ ] Firewall allows connections
- [ ] Browser can access http://localhost:5000
- [ ] Model API protobuf is fixed

## 🎯 Recommended Access Points

**For Monitoring & Management:**
- **Main Dashboard**: http://localhost:5001/static/healing-dashboard.html
- **Monitoring API**: http://localhost:5000

**For Testing:**
- **Network Analyzer**: http://localhost:8000
- **Incident Bot**: http://localhost:8001
- **Model API**: http://localhost:8080 (after fixing protobuf)

