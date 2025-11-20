# Predictive Maintenance - Quick Start

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
cd model
pip install -r requirements.txt
```

### Step 2: Train the Model
```bash
# Quick training (no tuning, no SHAP)
python3 train_xgboost_model.py --no-tuning --no-shap

# Full training with regression
python3 train_xgboost_model.py --enable-regression
```

### Step 3: Test the Model
```bash
# Run examples
python3 example_usage.py

# Or test via API (after starting dashboard)
curl http://localhost:5001/api/predict-failure-risk
```

## 📊 What You Get

After training, you'll have:
- ✅ Trained model in `artifacts/latest/`
- ✅ Evaluation metrics and plots
- ✅ FastAPI-compatible model loader
- ✅ Dashboard API endpoints ready to use

## 🔗 Integration

The model is automatically integrated with your dashboard at:
- `GET /api/predict-failure-risk` - Get risk score
- `GET /api/get-early-warnings` - Get warnings
- `GET /api/predict-time-to-failure` - Predict failure time
- `POST /api/predict-anomaly` - Real-time anomaly detection

## 📚 Full Documentation

- **Training Guide**: `PREDICTIVE_MAINTENANCE_README.md`
- **Integration Guide**: `INTEGRATION_GUIDE.md`
- **Data Collection**: `collect_training_data.py --help`

## 🎯 Next Steps

1. **Collect Real Data**: `python3 collect_training_data.py --duration 24`
2. **Retrain with Real Data**: `python3 train_xgboost_model.py --data-path training_data/system_metrics_*.csv`
3. **Monitor Dashboard**: Check `/api/predict-failure-risk` for real-time predictions

