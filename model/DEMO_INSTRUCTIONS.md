# Predictive Maintenance Dashboard Demo Instructions

## Quick Start

### Step 1: Start the Dashboard
```bash
cd /home/kasun/Documents/Heal-X-Bot/monitoring/server
python3 -m uvicorn healing_dashboard_api:app --host 0.0.0.0 --port 5001
```

### Step 2: Open Dashboard
Open your browser and go to: **http://localhost:5001**

Navigate to: **Predictive Maintenance** tab

### Step 3: Run Demo Script

#### Option A: Continuous Demo (Recommended)
```bash
cd /home/kasun/Documents/Heal-X-Bot/model
python3 continuous_demo.py
```

This will continuously cycle through different scenarios:
- Normal operation (low risk)
- Moderate load (medium risk)
- High load (high risk)
- Critical failure (very high risk)

**Watch the dashboard update in real-time!**

#### Option B: Interactive Demo
```bash
cd /home/kasun/Documents/Heal-X-Bot/model
python3 demo_dashboard_predictions.py
```

This will guide you through scenarios step by step.

#### Option C: Quick Test
```bash
cd /home/kasun/Documents/Heal-X-Bot/model
python3 show_predictions.py
```

Shows current predictions and tests scenarios.

## What You Should See

### In the Dashboard:
1. **Failure Risk Score** - Updates from 2% (normal) to 99% (critical)
2. **Risk Level** - Changes: Very Low → Low → Medium → High
3. **Early Warnings** - Appears when system stress increases
4. **Time to Failure** - Shows predicted hours until failure (if applicable)
5. **Progress Bar** - Visual indicator of risk level

### Expected Behavior:
- **Normal Operation**: Risk ~2-5% (Green)
- **Moderate Load**: Risk ~50-70% (Yellow)
- **High Load**: Risk ~80-90% (Orange/Red)
- **Critical**: Risk ~99% (Red) with warnings

## Troubleshooting

### If predictions don't update:
1. Click the **🔄 Refresh** button in the dashboard
2. Check browser console (F12) for errors
3. Verify dashboard is running: `curl http://localhost:5001/api/health`
4. Check if model is loaded: `curl http://localhost:5001/api/predict-failure-risk`

### If you see "Model not available":
- The model should be at: `model/artifacts/latest/model.json`
- If missing, train the model: `python3 train_xgboost_model.py --enable-regression`

## Files Created

1. **test_predictions.py** - Full test suite (10/10 tests)
2. **show_predictions.py** - Quick view of current predictions
3. **demo_dashboard_predictions.py** - Interactive demo
4. **continuous_demo.py** - Continuous cycling demo (best for visualization)

## Tips

- Keep the dashboard open in one browser tab
- Run `continuous_demo.py` in a terminal
- Watch the predictions update every 8 seconds
- The dashboard auto-refreshes every 30 seconds
- Use the Refresh button for immediate updates

