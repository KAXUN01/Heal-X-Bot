# 🎯 Auto-Healing Demo - Quick Reference Card

## 🚀 Setup (Before Demo)
```bash
# Start all services
./start.sh

# Open dashboard in browser
# URL: http://localhost:5001
```

## 🎬 Run Demo
```bash
# Inject both issues (RECOMMENDED)
python scripts/demo/presentation-demo.py --inject-both
```

## ⏱️ Timeline
- **0:00** - Run script
- **0:15** - Issues injected
- **0:30-0:60** - Issues appear in dashboard (REFRESH PAGE)

## 🎯 Demo Flow

### 1️⃣ Issue #1: Service Crash (Auto-Fix)
- **Type:** Critical - Service Crashed
- **Action:** Click "Fix Issue" button
- **Result:** Service automatically restarted
- **Time:** ~30 seconds to fix

### 2️⃣ Issue #2: Disk Full (Manual Steps)
- **Type:** Warning - Low Disk Space  
- **Action:** Click "Manual Steps" button
- **Result:** Shows step-by-step manual instructions
- **Why:** Requires human judgment

## 💬 Talking Points

### Automatic Healing
- "Zero-touch recovery capability"
- "Detected crash in 30 seconds"
- "Auto-restart without human intervention"
- "Verified service health before resolving"

### Manual Steps
- "Complex issues need human judgment"
- "Provides actionable instructions"
- "Safe recovery for critical operations"
- "Automation + expert guidance"

## 🧹 Cleanup (After Demo)
```bash
python scripts/demo/presentation-demo.py --cleanup
```

## 🆘 Troubleshooting

### Issues not appearing?
1. Wait 60 seconds
2. Refresh dashboard (F5)
3. Check services: `./start.sh status`

### Services not running?
```bash
./start.sh restart
```

## 📍 URLs
- Dashboard: http://localhost:5001
- API: http://localhost:5000

---
**Pro Tip:** Pre-test the demo 5-10 minutes before presentation!
