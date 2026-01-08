# 🎯 Auto-Healing Presentation Demo Guide

## Overview

This demonstration script showcases the **complete auto-healing mechanism** for your Google Cloud VM presentation. It demonstrates two healing scenarios:

1. **✅ Automatic Healing** - Service crash that is automatically fixed
2. **📋 Manual Steps** - Disk full issue that requires manual intervention

---

## 🚀 Quick Start

### Prerequisites

1. **Services Running:**
   ```bash
   # Start all Heal-X-Bot services
   ./start.sh
   # OR
   python run-healing-bot.py
   ```

2. **Dashboard Accessible:**
   - Open http://localhost:5001 in your browser

### Run the Demo

```bash
# Full presentation demo (both issues)
python scripts/demo/presentation-demo.py --inject-both
```

---

## 📋 Demo Scenarios

### Scenario 1: Automatic Healing ✅

**Issue Type:** Service Crash  
**Can be fixed:** Yes (automatic)  
**Button to click:** "Fix Issue"

**What happens:**
1. Script injects a service crash fault
2. Fault detector identifies the crashed service (~30 seconds)
3. Issue appears in the auto-healing dashboard page
4. Click "Fix Issue" button
5. Auto-healer restarts the service
6. Verification confirms the service is running
7. Success message appears

**Technical Details:**
- Crashes a Docker container (e.g., `cloud-sim-api-server`)
- Auto-healer executes: `docker restart <container>`
- Verification checks container health status

### Scenario 2: Manual Steps Required 📋

**Issue Type:** Disk Full  
**Can be fixed:** Partially (requires manual steps)  
**Button to click:** "Manual Steps"

**What happens:**
1. Script creates a large test file to simulate disk full
2. Fault detector identifies low disk space (~30 seconds)
3. Issue appears in the auto-healing dashboard page
4. Auto-healer attempts automatic cleanup but cannot fully resolve
5. Click "Manual Steps" button
6. Dashboard displays detailed manual recovery instructions
7. Follow the instructions to resolve the issue

**Manual Instructions Shown:**
- Identify large files/directories consuming disk space
- Clean up temporary files and logs
- Remove unused Docker images and containers
- Expand disk volume if needed

---

## 🎬 Presentation Flow

### Step-by-Step for Your Demo

1. **Prepare (Before Presentation)**
   ```bash
   # Ensure services are running
   ./start.sh
   
   # Open dashboard in browser
   # URL: http://localhost:5001
   ```

2. **Start Presentation**
   ```bash
   # Run the demo script
   python scripts/demo/presentation-demo.py --inject-both
   ```

3. **Wait for Issues to Appear (30-60 seconds)**
   - Refresh the auto-healing page in the dashboard
   - You should see 2 issues listed

4. **Demonstrate Automatic Healing**
   - Click on the **Service Crash** issue
   - Click the "Fix Issue" button
   - Watch the automatic healing process
   - See the success confirmation

5. **Demonstrate Manual Steps**
   - Click on the **Disk Full** issue
   - Click the "Manual Steps" button
   - Show the detailed manual instructions
   - Explain why this requires human intervention

6. **Cleanup (After Presentation)**
   ```bash
   python scripts/demo/presentation-demo.py --cleanup
   ```

---

## 💻 Command Reference

### Full Demo (Recommended)
```bash
python scripts/demo/presentation-demo.py --inject-both
```
Injects both fixable and manual issues for complete demonstration.

### Individual Scenarios

**Only Automatic Healing:**
```bash
python scripts/demo/presentation-demo.py --inject-fixable
```

**Only Manual Steps:**
```bash
python scripts/demo/presentation-demo.py --inject-manual
```

### Monitoring

**Watch Healing Process:**
```bash
python scripts/demo/presentation-demo.py --monitor
```
Monitors and displays healing events in real-time.

### Cleanup

**Remove All Injected Faults:**
```bash
python scripts/demo/presentation-demo.py --cleanup
```

### Help

**Show All Options:**
```bash
python scripts/demo/presentation-demo.py --help
```

---

## 🎨 What You'll See

### Console Output

The script provides **colorized, step-by-step output**:

```
================================================================================
🎯 AUTO-HEALING MECHANISM - PRESENTATION DEMO
================================================================================

📍 Dashboard URL: http://localhost:5001
📍 API URL: http://localhost:5000

────────────────────────────────────────────────────────────────────────────────
🔍 STEP 0: Checking Services
────────────────────────────────────────────────────────────────────────────────
✅ Dashboard API is running
✅ Monitoring API is running

✅ All required services are running!

────────────────────────────────────────────────────────────────────────────────
💥 STEP 1: Injecting Fixable Issue (Service Crash)
────────────────────────────────────────────────────────────────────────────────
ℹ️  Attempting to crash container: cloud-sim-api-server
✅ Service crash injected: cloud-sim-api-server
✅ Container stopped successfully

================================================================================
✨ FIXABLE ISSUE INJECTED SUCCESSFULLY!
================================================================================

📋 What happens next:
   1️⃣  The fault detector will detect the crashed service (~30 seconds)
   2️⃣  Issue appears in auto-healing page at http://localhost:5001
   3️⃣  Click 'Fix Issue' button in the dashboard
   4️⃣  Auto-healer restarts the service automatically
   5️⃣  Verification confirms the fix worked
```

### Dashboard View

**Auto-Healing Page will show:**

| Issue | Type | Status | Actions |
|-------|------|--------|---------|
| Service Crash | Critical | Detected | [Fix Issue] [Manual Steps] |
| Disk Low Space | Warning | Detected | [Fix Issue] [Manual Steps] |

---

## ⚙️ Configuration

### Dashboard URL
Default: `http://localhost:5001`

To change:
```python
# Edit presentation-demo.py
DASHBOARD_URL = "http://your-vm-ip:5001"
API_URL = "http://your-vm-ip:5000"
```

### Container Names
The script tries multiple container names automatically:
- `cloud-sim-api-server`
- `heal-x-bot-model-1`
- `heal-x-bot_model_1`
- `model`

### Disk Test File Size
Default: 500MB

To change:
```python
# Edit inject_manual_issue() function
size_gb = 0.5  # Change to desired size
```

---

## 🔧 Troubleshooting

### "Services are not running"
```bash
# Check service status
./start.sh status

# Start services
./start.sh

# Or use Python launcher
python run-healing-bot.py
```

### "Could not find suitable container"
```bash
# List running containers
docker ps

# Start cloud simulation services
docker compose -f config/docker-compose-cloud-sim.yml up -d
```

### "Issues not appearing in dashboard"
1. Wait 30-60 seconds for fault detection
2. Refresh the dashboard page (F5)
3. Check fault detector is running:
   ```bash
   # Check logs
   tail -f logs/fault_detector.log
   ```

### "Cleanup doesn't remove all files"
```bash
# Manual cleanup
rm -f /tmp/heal-x-test-*
docker compose restart
```

---

## 📊 Expected Timeline

| Time | Event |
|------|-------|
| 0:00 | Run demo script |
| 0:05 | Fixable issue injected |
| 0:15 | Manual issue injected |
| 0:30 | First issue detected |
| 0:45 | Both issues visible in dashboard |
| 1:00 | Ready for presentation |

**Total setup time:** ~1-2 minutes

---

## 🎓 Talking Points for Presentation

### When Showing Automatic Healing:
- "This demonstrates our **zero-touch recovery** capability"
- "The system detected the crash within 30 seconds"
- "Auto-healing restarted the service without human intervention"
- "Verified the service is healthy before marking as resolved"

### When Showing Manual Steps:
- "Some issues require **human judgment and decision-making**"
- "The system provides **actionable, step-by-step instructions**"
- "This ensures **safe recovery** for complex issues"
- "Combines **automation with expert guidance**"

---

## 🧪 Testing the Demo

### Before Presentation

**Test Run:**
```bash
# 1. Full test
python scripts/demo/presentation-demo.py --inject-both

# 2. Open dashboard
# http://localhost:5001

# 3. Wait for issues to appear

# 4. Test "Fix Issue" button

# 5. Test "Manual Steps" button

# 6. Cleanup
python scripts/demo/presentation-demo.py --cleanup
```

---

## 🔐 Security Notes

- Demo runs in **controlled environment** only
- Only affects **test containers and files**
- Cleanup removes all injected faults
- No production impact

---

## 📝 Additional Files

### Related Scripts:
- `auto-demo-healing.py` - Original automated healing demo
- `manual-fault-trigger.py` - Manual fault injection CLI
- `ddos_simulation.py` - DDoS attack simulation

### Related Documentation:
- `docs/guides/AUTO_HEALING_GUIDE.md` - Auto-healing documentation
- `monitoring/server/healing/` - Healing implementation
- `monitoring/server/fault_injector.py` - Fault injection code

---

## 💡 Tips for Successful Demo

1. **Pre-test Everything** - Run the demo once before the actual presentation
2. **Keep Dashboard Open** - Have the dashboard ready in a browser tab
3. **Colorful Terminal** - Use a terminal with good color support for impact
4. **Timing** - Allow 30-60 seconds for issues to propagate
5. **Backup Plan** - Know how to manually trigger issues if script fails
6. **Cleanup** - Always cleanup after demo to reset state

---

## 🆘 Support

If issues occur during the demo:

1. **Check Service Health:**
   ```bash
   curl http://localhost:5001/api/health
   curl http://localhost:5000/health
   ```

2. **View Real-time Logs:**
   ```bash
   tail -f logs/healing_dashboard.log
   ```

3. **Restart Services:**
   ```bash
   ./start.sh restart
   ```

---

**Last Updated:** January 8, 2026  
**Version:** 1.0  
**For:** Google Cloud VM Presentation

**Good luck with your demonstration! 🎉**
