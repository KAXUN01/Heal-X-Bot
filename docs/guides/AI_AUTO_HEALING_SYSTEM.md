# 🤖 AI-Powered Auto-Healing System

**Version:** 1.0  
**Status:** ✅ PRODUCTION READY  
**Last Updated:** 2025-10-29

---

## 📊 Overview

The **AI-Powered Auto-Healing System** is the core intelligence of Healing-bot that automatically:
1. **Detects** system errors in real-time
2. **Analyzes** them using Google Gemini AI
3. **Executes** fixes automatically
4. **Verifies** the fix worked
5. **Logs** all healing actions

---

## 🎯 Key Features

### ✅ Automatic Error Detection
- Monitors system logs every 60 seconds
- Detects ERROR and CRITICAL level issues
- Focuses on recent errors (< 5 minutes old)
- Prevents duplicate healing attempts

### 🧠 AI-Powered Analysis
- Uses Google Gemini AI to analyze errors
- Understands root causes
- Generates actionable solutions
- Extracts executable commands

### 🔧 Safe Command Execution
- Only executes pre-approved safe commands
- Requires `sudo` privileges for system operations
- Safety checks before execution
- Timeout protection (30s per command)

### ✅ Automatic Verification
- Checks if error still appears after fix
- Verifies service status
- Marks healing as successful or failed

### 📊 Complete Audit Trail
- Records all healing attempts
- Tracks success/failure rates
- Maintains 100-item history
- Statistics dashboard

---

## 🛠️ Safe Actions Supported

The auto-healer can safely execute these actions:

| Action | Description | Safety Level |
|--------|-------------|--------------|
| **restart_service** | Restart systemd services (docker, apache, nginx, etc.) | ✅ Safe |
| **fix_permissions** | Fix file permissions (`chmod +x`) | ✅ Safe |
| **clear_cache** | Clear system cache | ✅ Safe |
| **rotate_logs** | Rotate log files | ✅ Safe |
| **free_disk_space** | Clean old logs, apt cache, temp files | ✅ Safe |
| **restart_network** | Restart systemd-resolved | ✅ Safe |
| **reload_config** | Reload service configuration | ✅ Safe |
| **kill_zombie_process** | Identify zombie processes | ✅ Safe |

---

## 🔄 How It Works

### Step-by-Step Healing Process:

```
1. Error Detection
   ↓
   System Log Collector finds ERROR in logs
   ↓
2. Eligibility Check
   ↓
   - Error < 5 minutes old?
   - Not healed more than 3 times?
   ↓
3. AI Analysis
   ↓
   Gemini AI analyzes error and suggests solutions
   ↓
4. Command Extraction
   ↓
   Parse AI solution into executable commands
   ↓
5. Safe Execution
   ↓
   Execute commands with safety checks
   ↓
6. Verification
   ↓
   Check if error is resolved
   ↓
7. Record Result
   ↓
   Log healing attempt in history
```

---

## 📡 API Endpoints

### 1. Get Auto-Healer Status
```bash
GET /api/auto-healer/status
```

**Response:**
```json
{
  "status": "success",
  "auto_healer": {
    "enabled": true,
    "auto_execute": true,
    "monitoring": true,
    "max_attempts": 3
  }
}
```

### 2. Get Healing History
```bash
GET /api/auto-healer/history?limit=50
```

**Response:**
```json
{
  "status": "success",
  "count": 15,
  "history": [
    {
      "timestamp": "2025-10-29T15:30:00",
      "error": {...},
      "status": "healed",
      "actions": [...],
      "success": true
    }
  ]
}
```

### 3. Get Healing Statistics
```bash
GET /api/auto-healer/statistics
```

**Response:**
```json
{
  "status": "success",
  "statistics": {
    "total_attempts": 25,
    "successful": 20,
    "failed": 5,
    "pending": 0,
    "success_rate": 80.0
  }
}
```

### 4. Manual Heal (Trigger healing for specific error)
```bash
POST /api/auto-healer/heal
Content-Type: application/json

{
  "service": "apache2",
  "message": "SSL certificate expired",
  "level": "ERROR",
  "timestamp": "2025-10-29T15:00:00"
}
```

**Response:**
```json
{
  "status": "success",
  "healing_result": {
    "status": "healed",
    "actions": [...],
    "verification": {...}
  }
}
```

---

## 🧪 Testing the Auto-Healer

### Test 1: Inject Test Error
```bash
curl -X POST http://localhost:5000/api/test/inject-error \
  -H "Content-Type: application/json" \
  -d '{
    "service": "cron",
    "message": "Failed to execute backup script /usr/local/bin/backup.sh: Permission denied",
    "level": "ERROR",
    "source": "syslog"
  }'
```

### Test 2: Wait for Auto-Healing
```bash
# Wait 60-120 seconds for auto-healer to detect and fix the error
sleep 120

# Check healing history
curl http://localhost:5000/api/auto-healer/history | jq .
```

### Test 3: Check Statistics
```bash
curl http://localhost:5000/api/auto-healer/statistics | jq .
```

---

## 📊 Example Healing Scenarios

### Scenario 1: Service Restart

**Error Detected:**
```
Service: docker
Message: docker.service: Main process exited, code=exited, status=1/FAILURE
Level: ERROR
```

**AI Analysis:**
```
🔍 WHAT HAPPENED:
Docker service crashed due to resource exhaustion

💡 QUICK FIX:
1. Restart docker service: sudo systemctl restart docker
2. Check logs for root cause
```

**Actions Taken:**
```
✅ restart_service: docker
```

**Verification:**
```
✅ Service status: active
✅ Error no longer in logs
```

**Result:** ✅ HEALED

---

### Scenario 2: Permission Fix

**Error Detected:**
```
Service: cron
Message: Failed to execute backup script /usr/local/bin/backup.sh: Permission denied
Level: ERROR
```

**AI Analysis:**
```
🔍 WHAT HAPPENED:
Backup script lacks execute permissions

💡 QUICK FIX:
Grant execute permissions: sudo chmod +x /usr/local/bin/backup.sh
```

**Actions Taken:**
```
✅ fix_permissions: /usr/local/bin/backup.sh
```

**Verification:**
```
✅ Permissions fixed
✅ Error no longer in logs
```

**Result:** ✅ HEALED

---

### Scenario 3: Disk Space Cleanup

**Error Detected:**
```
Service: systemd-journald
Message: Journal file size limit reached (100MB). Rotating logs.
Level: WARNING
```

**AI Analysis:**
```
🔍 WHAT HAPPENED:
Disk space running low due to log accumulation

💡 QUICK FIX:
Free up space by cleaning old logs and apt cache
```

**Actions Taken:**
```
✅ free_disk_space
   - Cleaned apt cache
   - Removed old logs (>7 days)
   - Cleaned temp files
```

**Verification:**
```
✅ Disk space freed: 2.3 GB
✅ Warning no longer appears
```

**Result:** ✅ HEALED

---

## 🔐 Security & Safety

### Safety Mechanisms:

1. **Whitelisted Commands Only**
   - Only pre-approved safe commands execute
   - Unknown commands are rejected

2. **Path Restrictions**
   - Only safe directories: `/usr/local/bin`, `/var/log`, `/opt`, `/home`
   - System-critical paths are protected

3. **Service Restrictions**
   - Only safe services can be restarted
   - Critical services (e.g., `sshd`) require manual intervention

4. **Timeout Protection**
   - All commands have 30-second timeout
   - Prevents hanging operations

5. **Retry Limits**
   - Maximum 3 healing attempts per error
   - Prevents infinite retry loops

6. **Audit Trail**
   - All actions logged with timestamps
   - Complete traceability

---

## ⚙️ Configuration

### Enable/Disable Auto-Execution

**In `auto_healer.py`:**
```python
self.enabled = True  # Enable/disable auto-healer
self.auto_execute = True  # Auto-execute or require approval
self.max_healing_attempts = 3  # Max retries per error
```

### Monitoring Interval

**In `app.py`:**
```python
auto_healer.start_monitoring(interval_seconds=60)  # Check every 60s
```

---

## 📈 Performance Impact

| Metric | Value |
|--------|-------|
| **CPU Usage** | ~2-5% during healing |
| **Memory** | ~50-100 MB |
| **Disk I/O** | Minimal (log writes only) |
| **Network** | API calls to Gemini (~10 KB per analysis) |
| **Healing Time** | 2-30 seconds per error |

---

## 🚨 Troubleshooting

### Issue: Auto-Healer Not Working

**Check 1: Is it running?**
```bash
curl http://localhost:5000/api/auto-healer/status
```

**Check 2: Are there errors to heal?**
```bash
curl http://localhost:5000/api/system-logs/recent?level=ERROR
```

**Check 3: Check logs**
```bash
tail -f logs/monitoring-server.log | grep -i "healer\|healing"
```

### Issue: Healing Fails

**Possible Causes:**
1. **Missing sudo permissions**
   - Solution: Ensure app runs with `sudo` or configure sudoers
2. **AI analysis failed**
   - Solution: Check GEMINI_API_KEY is valid
3. **Command not recognized**
   - Solution: Review AI solution and add to safe_commands

---

## 📊 Metrics & Monitoring

### Key Metrics to Track:

1. **Success Rate** - Target: > 80%
2. **Average Healing Time** - Target: < 30 seconds
3. **Retry Count** - Monitor for patterns
4. **Most Common Errors** - Identify systemic issues

### Prometheus Metrics (Future):
```
healing_attempts_total
healing_success_total
healing_failure_total
healing_duration_seconds
```

---

## 🎯 Best Practices

1. **Monitor Healing History Regularly**
   - Review healing attempts daily
   - Identify patterns in failures
   - Adjust safe_commands as needed

2. **Test Before Production**
   - Use `auto_execute = False` for manual approval
   - Test each healing scenario
   - Verify safety mechanisms

3. **Keep AI Prompt Updated**
   - Improve extraction logic for new error types
   - Add more safe commands as validated

4. **Maintain Audit Trail**
   - Export healing history monthly
   - Review for compliance/security
   - Analyze success/failure trends

---

## 🔮 Future Enhancements

- [ ] Machine learning for command extraction
- [ ] Rollback capability if healing fails
- [ ] Integration with alerting (Slack, PagerDuty)
- [ ] Dashboard UI for healing history
- [ ] Advanced pattern recognition
- [ ] Multi-step healing workflows
- [ ] Health score per service

---

## 📝 Example Use Cases

### Use Case 1: DevOps Automation
**Scenario:** Production service crashes at 3 AM  
**Without Auto-Healer:** Engineer woken up, manually fixes in 30 mins  
**With Auto-Healer:** Service auto-restarted in 60 seconds, engineer sleeps  

### Use Case 2: Disk Space Management
**Scenario:** Disk fills up with logs, service fails  
**Without Auto-Healer:** Manual cleanup required, downtime  
**With Auto-Healer:** Auto-cleanup, service restored, no downtime  

### Use Case 3: Permission Issues
**Scenario:** Cron job fails due to permission error  
**Without Auto-Healer:** Wait for manual investigation  
**With Auto-Healer:** Permissions fixed automatically, job runs  

---

## 🤝 Contributing

To add a new safe command:

1. Add handler function in `auto_healer.py`:
```python
def _my_new_command(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
    # Implementation
    return True, "Success message"
```

2. Add to `safe_commands` dict:
```python
self.safe_commands = {
    'my_new_command': self._my_new_command,
    # ... other commands
}
```

3. Add extraction logic in `_extract_commands()`:
```python
if 'keyword' in message:
    commands.append({
        'type': 'my_new_command',
        'description': 'My new command description'
    })
```

4. Test thoroughly before enabling in production

---

## 📞 Support

**Documentation:** `/docs/guides/AI_AUTO_HEALING_SYSTEM.md`  
**API Reference:** `http://localhost:5000/api/auto-healer/*`  
**Logs:** `/logs/monitoring-server.log`

---

**Last Updated:** 2025-10-29  
**Version:** 1.0  
**Status:** ✅ Production Ready

