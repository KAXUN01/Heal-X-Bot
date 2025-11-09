# 🧪 Critical Errors Test Scripts

## Overview

These scripts generate critical errors by crashing services and verify that the errors appear in the "Critical Errors Only" section of the dashboard.

## 📋 Available Scripts

### 1. **`test-critical-errors-complete.sh`** (Recommended)
**Comprehensive bash script** with full testing and verification.

**Features:**
- ✅ Stops actual services (nginx, docker, dbus, etc.) to generate real errors
- ✅ Generates CRITICAL priority logs via `logger` and `systemd-cat`
- ✅ Waits for monitor to collect logs (15 seconds)
- ✅ Verifies errors appear in API response
- ✅ Shows detailed summary of results
- ✅ Optionally restarts stopped services

**Usage:**
```bash
./test-critical-errors-complete.sh
```

**What it does:**
1. Checks if API is accessible
2. Gets baseline issue count
3. Stops services and generates CRITICAL logs
4. Waits 15 seconds for monitor collection
5. Verifies errors appear in API
6. Shows detailed summary
7. Optionally restarts stopped services

---

### 2. **`test-critical-errors-quick.sh`**
**Fast bash script** for quick testing without stopping services.

**Features:**
- ✅ Quick execution (no service stopping)
- ✅ Generates CRITICAL logs only
- ✅ Minimal waiting time
- ✅ Basic verification

**Usage:**
```bash
./test-critical-errors-quick.sh
```

**What it does:**
1. Checks API accessibility
2. Gets baseline
3. Generates 15+ CRITICAL logs quickly
4. Waits 15 seconds
5. Shows results

---

### 3. **`test-critical-errors-python.py`**
**Python script** with detailed verification and reporting.

**Features:**
- ✅ Python-based (better error handling)
- ✅ Stops services if needed
- ✅ Detailed API response parsing
- ✅ Service-by-service verification
- ✅ Shows severity breakdown
- ✅ Better formatting and colors

**Usage:**
```bash
python3 test-critical-errors-python.py
```

**What it does:**
1. Checks API with proper error handling
2. Gets baseline count
3. Optionally stops services
4. Generates CRITICAL logs
5. Waits and verifies each service
6. Shows detailed summary with severity breakdown
7. Optionally restarts services

---

## 🚀 Quick Start

### Prerequisites
1. Dashboard server must be running on port 5001
2. Monitor must be running (collects logs every 10 seconds)

### Run the Test
```bash
# Make scripts executable (if needed)
chmod +x test-critical-errors-*.sh
chmod +x test-critical-errors-*.py

# Run the complete test (recommended)
./test-critical-errors-complete.sh

# Or run the quick test
./test-critical-errors-quick.sh

# Or run the Python version
python3 test-critical-errors-python.py
```

---

## 📊 What to Expect

### During Test
1. **Service Stopping**: Scripts will stop services like nginx, docker, etc.
   - This generates real CRITICAL errors in systemd journal
   - Services can be restarted after testing

2. **Log Generation**: Multiple CRITICAL priority logs are written
   - Via `logger -p 2` (CRITICAL priority)
   - Via `systemd-cat -p crit`
   - With various service names (nginx, docker, test-service, etc.)

3. **Waiting Period**: Scripts wait 15 seconds
   - Monitor collects logs every 10 seconds
   - This ensures logs are picked up

4. **Verification**: Scripts check API endpoint
   - `GET /api/critical-services/issues`
   - Verifies errors appear in response
   - Checks for CRITICAL severity

### Expected Results

**✅ Success:**
- New issues detected in API
- CRITICAL severity issues found
- Errors appear in dashboard "Critical Errors Only" section

**⚠️ If No New Issues:**
- Monitor may need more time (wait another 10 seconds)
- Check server logs for errors
- Verify monitor is running
- Check if services were actually stopped

---

## 🔍 Manual Verification

After running the test, verify in the dashboard:

1. **Open Dashboard**: http://localhost:5001
2. **Scroll to "Critical Errors Only" section**
3. **Check for errors from:**
   - nginx (if installed)
   - docker (if installed)
   - dbus (if installed)
   - test-critical-service
   - test-system

4. **Verify:**
   - Errors have "CRITICAL" severity
   - Timestamps are recent
   - Messages match test patterns

### Check Log File
```bash
# View log file (user location)
tail -n 50 ~/critical_monitor.log

# Or system location (if using sudo)
sudo tail -n 50 /var/log/critical_monitor.log
```

### Check API Directly
```bash
# Get issues count
curl -s http://localhost:5001/api/critical-services/issues | jq '.count'

# Get all issues
curl -s http://localhost:5001/api/critical-services/issues | jq '.issues[] | {service, severity, message}'

# Filter by service
curl -s http://localhost:5001/api/critical-services/issues | jq '.issues[] | select(.service == "nginx")'
```

---

## 🛠️ Troubleshooting

### Issue: "Cannot connect to API"
**Solution:**
- Make sure dashboard server is running on port 5001
- Check: `curl http://localhost:5001/api/health`

### Issue: "No new errors detected"
**Solutions:**
1. Wait longer (monitor runs every 10 seconds)
2. Check if monitor is actually running
3. Verify services were stopped
4. Check server logs for errors
5. Manually check API: `curl http://localhost:5001/api/critical-services/issues`

### Issue: "Services won't restart"
**Solution:**
```bash
# Manually restart services
sudo systemctl start nginx
sudo systemctl start docker
sudo systemctl start dbus
```

### Issue: "Permission denied"
**Solution:**
- Scripts use `logger` which doesn't need sudo
- `systemd-cat` may need permissions
- Service stopping needs sudo (scripts handle this)

---

## 📝 Script Details

### Services Tested
- **nginx**: Web server (if installed)
- **docker**: Container runtime (if installed)
- **dbus**: Message bus (system service)
- **systemd-journald**: Logging daemon (system service)
- **test-critical-service**: Generic test service
- **test-system**: Generic system test

### Log Priorities
All logs use **priority 2 (CRITICAL)**:
- `logger -p 2` = CRITICAL priority
- `systemd-cat -p crit` = CRITICAL priority

### API Endpoint
- **URL**: `http://localhost:5001/api/critical-services/issues`
- **Method**: GET
- **Response**: JSON with `status`, `issues[]`, `count`

---

## 🎯 Success Criteria

Test is successful if:
1. ✅ API is accessible
2. ✅ New issues are detected (count increases)
3. ✅ CRITICAL severity issues are found
4. ✅ Errors appear in dashboard "Critical Errors Only" section
5. ✅ Errors match generated test patterns

---

## 🔄 Cleanup

After testing:
1. **Restart stopped services** (if prompted by script)
2. **Verify services are running**:
   ```bash
   systemctl status nginx
   systemctl status docker
   systemctl status dbus
   ```

3. **Check dashboard** to see errors are displayed
4. **Check log file** to verify logs were written

---

## 📚 Related Files

- `critical_services_monitor.py`: The monitor that collects logs
- `healing_dashboard_api.py`: API endpoint that serves issues
- `CRITICAL_LOG_FILE_FEATURE.md`: Documentation on file logging
- `test-nginx-crash.sh`: Simple nginx crash test (existing)

---

## 💡 Tips

1. **Run during development** to verify dashboard works
2. **Use quick test** for frequent verification
3. **Use complete test** for thorough testing
4. **Check server logs** if issues aren't appearing
5. **Monitor file logging** to see logs being written in real-time:
   ```bash
   tail -f ~/critical_monitor.log
   ```

---

## ⚠️ Warnings

- Scripts will **stop services** (they can be restarted)
- Don't run on **production** without caution
- Services may take a moment to fully stop
- Some services may not exist (scripts handle this)

---

## ✅ Verification Checklist

After running a test, verify:
- [ ] API responds with issues
- [ ] Issue count increased
- [ ] CRITICAL severity issues found
- [ ] Dashboard shows errors in "Critical Errors Only"
- [ ] Log file contains entries
- [ ] Services can be restarted (if stopped)

If all items are checked ✅, the "Critical Errors Only" section is working correctly!

