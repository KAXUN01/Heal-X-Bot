# Model Training - Complete Workflow

## Quick Reference

### Train Model
```bash
# Basic training (synthetic data)
python3 train_xgboost_model.py

# With regression model
python3 train_xgboost_model.py --enable-regression

# With your own data
python3 train_xgboost_model.py --data-path training_data/system_metrics_*.csv --enable-regression
```

### Verify Model
```bash
python3 verify_model.py
```

### Collect Data
```bash
# Collect once
python3 collect_training_data.py --once

# Collect for 24 hours
python3 collect_training_data.py --duration 24 --interval 60
```

### Automated Retraining
```bash
# Check if retraining needed
python3 automated_retraining.py

# Force retraining
python3 automated_retraining.py --force
```

## Complete Workflow

### Step 1: Initial Setup
```bash
cd model
pip install -r requirements.txt
```

### Step 2: Train Initial Model
```bash
# Quick training for testing
python3 train_xgboost_model.py --no-tuning --no-shap

# Full training for production
python3 train_xgboost_model.py --enable-regression
```

### Step 3: Verify Model
```bash
python3 verify_model.py
```

### Step 4: Start Data Collection
```bash
# Background collection
nohup python3 collect_training_data.py --interval 60 > collection.log 2>&1 &
```

### Step 5: Set Up Automated Retraining
```bash
# Weekly retraining via cron
./setup_cron_retraining.sh
```

### Step 6: Monitor Performance
```bash
# Check model health
./health_check.sh

# View metrics
cat artifacts/latest/metrics.json | jq .

# Test predictions
python3 example_usage.py
```

## File Structure

```
model/
├── train_xgboost_model.py      # Main training script
├── collect_training_data.py     # Data collection
├── automated_retraining.py      # Automated retraining
├── verify_model.py              # Model verification
├── example_usage.py             # Usage examples
├── test_training.py             # Quick test
├── test_predictive_model.py     # Unit tests
├── health_check.sh              # Health check script
├── update_dashboard_model.py    # Dashboard update
├── train_model_service.sh       # Service script
├── setup_cron_retraining.sh    # Cron setup
├── artifacts/                   # Trained models
│   ├── latest/                  # Latest model (symlink)
│   └── v{timestamp}/            # Versioned models
├── training_data/               # Collected data
└── docs/                        # Documentation
```

## Common Commands

| Task | Command |
|------|---------|
| Train model | `python3 train_xgboost_model.py --enable-regression` |
| Verify model | `python3 verify_model.py` |
| Collect data | `python3 collect_training_data.py --duration 24` |
| Retrain | `python3 automated_retraining.py` |
| Health check | `./health_check.sh` |
| Test usage | `python3 example_usage.py` |
| Run tests | `python3 test_predictive_model.py` |

## Troubleshooting

See `DEPLOYMENT_GUIDE.md` for detailed troubleshooting.

