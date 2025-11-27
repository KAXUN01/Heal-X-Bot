# Quick Start - Cloud Simulation & Auto-Healing

## 🚀 Quick Start (3 Steps)

### Step 1: Start the System
```bash
python3 run-healing-bot.py
```

### Step 2: Start Cloud Simulation
```bash
# Try newer syntax first (recommended)
docker compose -f config/docker-compose-cloud-sim.yml up -d

# Or use older syntax
docker-compose -f config/docker-compose-cloud-sim.yml up -d

# Or use the setup script
./scripts/setup/init-cloud-sim.sh
```

### Step 3: Open Dashboard
Open http://localhost:5001 and navigate to **☁️ Cloud Simulation** tab

## 💥 Test the System

### Option A: Automated Demo
```bash
python3 run-demo.py
```

### Option B: Manual Testing via Dashboard
1. Go to http://localhost:5001
2. Click **☁️ Cloud Simulation** tab
3. Click **💥 Inject Service Crash** button
4. Watch the system:
   - Detect the fault (within 30 seconds)
   - Analyze with AI
   - Automatically heal
   - Show results in dashboard

### Option C: Command Line
```bash
# Inject a service crash
python3 scripts/demo/manual-fault-trigger.py --type crash --container cloud-sim-api-server

# Wait 30-60 seconds, then check:
curl http://localhost:5001/api/cloud/faults
curl http://localhost:5001/api/cloud/healing/history
```

## 📊 What You'll See

### In Console:
- Step-by-step fault detection
- AI diagnosis with confidence scores
- Healing actions with explanations
- Verification results

### In Dashboard:
- **Service Status**: All containers with health indicators
- **Fault Detection**: Real-time fault timeline
- **AI Diagnosis**: Root cause analysis results
- **Healing Actions**: Step-by-step healing log
- **Discord Notifications**: Notification history
- **Resource Charts**: CPU, memory, disk, network
- **Statistics**: Success rates and metrics
- **Manual Instructions**: When auto-healing fails

### In Discord (if configured):
- Immediate notification when service crashes
- Healing attempt notifications
- Success/failure notifications with details

## 🔧 Configuration

### Discord Notifications
Add to `.env`:
```env
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
```

### Gemini AI (Optional)
Add to `.env`:
```env
GEMINI_API_KEY=your_key_here
```

## ✅ Success Indicators

- ✅ Faults detected within 30 seconds
- ✅ AI diagnosis shows confidence > 80%
- ✅ Auto-healing attempts recovery
- ✅ Discord notifications sent
- ✅ Dashboard updates in real-time
- ✅ Manual instructions provided when needed

## 🐛 Troubleshooting

**Services not starting?**
```bash
docker ps
# Try newer syntax first
docker compose -f config/docker-compose-cloud-sim.yml logs
# Or older syntax
docker-compose -f config/docker-compose-cloud-sim.yml logs
```

**Faults not detected?**
- Check fault detector is running
- Verify container names match
- Check monitoring interval (30s default)

**Healing not working?**
- Check Docker permissions
- Verify auto-healer is enabled
- Check healing history: `GET /api/cloud/healing/history`

## 📚 Full Documentation

See `docs/demo/DEMO_GUIDE.md` for complete documentation.

