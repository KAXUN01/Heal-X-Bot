# 🌐 Browser Access Guide

## ✅ All Services are Running and Accessible!

### Quick Access URLs (Copy & Paste in Browser)

**1. Healing Dashboard (Main UI)**
```
http://localhost:5001/static/healing-dashboard.html
```
This is the **recommended main entry point** with full dashboard UI.

**2. Monitoring Server (API)**
```
http://localhost:5000
http://localhost:5000/health
```
API-only server. Shows JSON response.

**3. Network Analyzer**
```
http://localhost:8000
http://localhost:8000/active-threats
```

**4. Incident Bot**
```
http://localhost:8001
http://localhost:8001/
```

**5. Healing Dashboard API**
```
http://localhost:5001
http://localhost:5001/api/health
```

**6. Model API** (May need restart)
```
http://localhost:8080
http://localhost:8080/health
```

## 🔍 Troubleshooting Browser Access

### If you can't access services:

1. **Verify services are responding:**
   ```bash
   curl http://localhost:5000/health
   curl http://localhost:5001/api/health
   ```

2. **Check if ports are listening:**
   ```bash
   ss -tlnp | grep -E ":(5000|8080|8000|8001|5001)"
   ```
   Should show services bound to `0.0.0.0` (all interfaces)

3. **Try alternative addresses:**
   - http://localhost:5001
   - http://127.0.0.1:5001
   - http://0.0.0.0:5001 (might not work in browser)

4. **Check browser console:**
   - Press `F12` to open developer tools
   - Check Console tab for JavaScript errors
   - Check Network tab to see if requests are being made

5. **Try different browser:**
   - Firefox
   - Chrome
   - Edge

6. **Check firewall:**
   ```bash
   sudo ufw status
   sudo ufw allow 5001/tcp
   sudo ufw allow 5000/tcp
   ```

## 🎯 Recommended Entry Points

**For Full Dashboard Experience:**
```
http://localhost:5001/static/healing-dashboard.html
```

**For API Testing:**
```
http://localhost:5000/
http://localhost:5001/api/health
```

**For Quick Status Check:**
```
http://localhost:8001/
http://localhost:8000/active-threats
```

## 📊 Service Status

All services are bound to `0.0.0.0` which means they accept connections from:
- ✅ `localhost` / `127.0.0.1` (same machine)
- ✅ Your machine's IP address (from other machines on network)

## 🔧 If Services Still Don't Work

1. **Restart all services:**
   ```bash
   ./stop-services.sh
   ./start.sh
   ```

2. **Check service logs:**
   ```bash
   tail -f logs/*.log
   ```

3. **Verify environment:**
   ```bash
   python3 -m healx status
   ```

