# Predictive Maintenance Dashboard Demo Guide

## Quick Start

### 1. Start the Dashboard
```bash
cd /home/kasun/Documents/Heal-X-Bot/monitoring/server
python3 -m uvicorn healing_dashboard_api:app --host 0.0.0.0 --port 5001
```

### 2. Open Dashboard
Open browser: **http://localhost:5001**
Navigate to: **Predictive Maintenance** tab

### 3. Run Demo Script

**Best for Visualization:**
```bash
cd /home/kasun/Documents/Heal-X-Bot/model
python3 continuous_demo.py
```

This continuously cycles through scenarios every 8 seconds.

**For Step-by-Step Demo:**
```bash
python3 demo_with_dashboard.py
```

This guides you through scenarios with pauses.

## What You'll See

The dashboard shows:
- **Failure Risk Score**: Updates from 2% → 80% → 99% based on scenarios
- **Risk Level**: Very Low → Low → Medium → High
- **Progress Bar**: Visual indicator filling up as risk increases
- **Early Warnings**: Appears when system stress is high
- **Time to Failure**: Shows predicted hours (if applicable)

## Demo Scripts Available

1. **continuous_demo.py** - Continuous cycling (best for visualization)
2. **demo_with_dashboard.py** - Interactive step-by-step demo
3. **show_predictions.py** - Quick test of current predictions
4. **test_predictions.py** - Full test suite

## Troubleshooting

### If predictions don't show:
1. Click the **🔄 Refresh** button in dashboard
2. Check browser console (F12) for errors
3. Verify dashboard is running: `curl http://localhost:5001/api/health`
4. Restart dashboard to pick up JavaScript changes

### If you see "Model not available":
- Model should be at: `model/artifacts/latest/model.json`
- Train model: `python3 train_xgboost_model.py --enable-regression`

## Expected Behavior

- **Normal**: Risk ~2-5% (Green)
- **Moderate**: Risk ~50-70% (Yellow)  
- **High Load**: Risk ~80-90% (Orange)
- **Critical**: Risk ~99% (Red) with warnings

The dashboard auto-refreshes every 30 seconds, or click Refresh for immediate update.

