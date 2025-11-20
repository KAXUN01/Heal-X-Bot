# Predictive Maintenance Training Script - Quick Start Guide

## Overview

The `train_xgboost_model.py` script trains a predictive maintenance model for Ubuntu system anomaly detection. It predicts system failures **BEFORE they occur** using XGBoost (with GradientBoosting fallback).

## Features

- **Predictive Maintenance**: Predicts failures 1-24 hours before they occur
- **Dual Model Approach**: Classification (anomaly detection) + Optional Regression (time-to-failure)
- **Early Warning Indicators**: Resource degradation, error escalation, service failures
- **Real-time Dashboard Integration**: FastAPI-compatible model loader
- **Comprehensive Evaluation**: Early detection rate, lead time distribution, prediction timelines

## Installation

1. **Install Dependencies**:
```bash
cd model
pip install -r requirements.txt
```

2. **Verify Installation**:
```bash
python3 train_xgboost_model.py --help
```

## Quick Start

### Basic Training (Synthetic Data)

Train a model with default settings using synthetic data:

```bash
python3 train_xgboost_model.py
```

This will:
- Generate 10,000 synthetic samples with failure patterns
- Train classification model
- Save artifacts to `model/artifacts/v{timestamp}/`
- Create FastAPI loader at `model/artifacts/latest/model_loader.py`

### Training with Regression Model

Train both classification and regression models:

```bash
python3 train_xgboost_model.py --enable-regression
```

### Custom Prediction Horizon

Predict failures 1, 6, and 24 hours ahead:

```bash
python3 train_xgboost_model.py --prediction-horizon 1 6 24
```

### Using Your Own Data

Train with a CSV file containing system metrics:

```bash
python3 train_xgboost_model.py --data-path /path/to/your/data.csv
```

CSV should contain columns:
- `timestamp` (datetime)
- System metrics: `cpu_percent`, `memory_percent`, `disk_percent`, etc.
- Log patterns: `error_count`, `warning_count`, `service_failures`, etc.

### Skip Hyperparameter Tuning (Faster)

For quick testing without tuning:

```bash
python3 train_xgboost_model.py --no-tuning --no-shap
```

## Command-Line Options

```
--data-path PATH          Path to training data CSV (optional)
--test-size FLOAT         Test set size (default: 0.2)
--n-iter INT              Hyperparameter tuning iterations (default: 20)
--no-tuning               Skip hyperparameter tuning
--no-shap                 Skip SHAP explanations
--target-col STR          Target column name (default: target)
--artifacts-dir PATH      Custom artifacts directory
--prediction-horizon INT  Hours ahead to predict (default: 1 6 24)
--enable-regression       Also train time-to-failure regression model
```

## Output Artifacts

After training, artifacts are saved to `model/artifacts/v{timestamp}/`:

- `model.json` or `model.pkl` - Classification model
- `regression_model.json` or `regression_model.pkl` - Regression model (if enabled)
- `scaler.pkl` - Feature scaler
- `feature_names.json` - Feature names
- `metrics.json` - Evaluation metrics
- `config.json` - Training configuration
- `prediction_thresholds.json` - Optimal thresholds
- `plots/` - Visualization plots:
  - `confusion_matrix.png`
  - `roc_curve.png`
  - `feature_importance.png`
  - `prediction_timeline.png`
- `shap/` - SHAP explanations (if enabled)

A symlink `latest/` points to the most recent version.

## Using the Trained Model

### FastAPI Integration

The script generates a `model_loader.py` in `artifacts/latest/` with functions:

```python
from model.artifacts.latest.model_loader import (
    predict_anomaly,
    predict_failure_risk,
    predict_time_to_failure,
    get_early_warnings
)

# Example: Get failure risk score
metrics = {
    'cpu_percent': 85.0,
    'memory_percent': 90.0,
    'disk_percent': 75.0,
    'error_count': 5,
    # ... other metrics
}

risk = predict_failure_risk(metrics)
print(f"Failure Risk: {risk['risk_percentage']:.1f}%")

# Get early warnings
warnings = get_early_warnings(metrics)
if warnings['has_warnings']:
    for warning in warnings['warnings']:
        print(f"{warning['severity']}: {warning['message']}")

# Predict time to failure
time_pred = predict_time_to_failure(metrics)
if time_pred.get('hours_until_failure'):
    print(f"Predicted failure in {time_pred['hours_until_failure']:.1f} hours")
```

### Dashboard Integration

Add endpoints to your FastAPI dashboard:

```python
from fastapi import FastAPI
from model.artifacts.latest.model_loader import (
    predict_failure_risk,
    get_early_warnings
)

app = FastAPI()

@app.get("/api/predict-failure-risk")
async def get_failure_risk(metrics: dict):
    return predict_failure_risk(metrics)

@app.get("/api/get-early-warnings")
async def get_warnings(metrics: dict):
    return get_early_warnings(metrics)
```

## Metrics Explained

### Classification Metrics
- **Accuracy**: Overall prediction accuracy
- **Precision**: % of predicted failures that actually failed
- **Recall**: % of actual failures that were predicted
- **F1 Score**: Harmonic mean of precision and recall
- **ROC-AUC**: Area under ROC curve
- **PR-AUC**: Area under precision-recall curve

### Predictive Performance
- **Early Detection Rate**: % of failures predicted >1 hour before occurrence
- **Mean Lead Time**: Average hours before failure that prediction was made
- **Median Lead Time**: Median hours before failure

### Regression Metrics (if enabled)
- **MAE**: Mean absolute error in hours
- **RMSE**: Root mean squared error in hours
- **Accuracy within 1 hour**: % of predictions within ±1 hour

## Example Training Output

```
================================================================================
XGBoost Training Pipeline for Predictive Maintenance & Proactive Intelligence
================================================================================
Step 1: Loading data with predictive labeling...
Generated 10000 synthetic samples with failure patterns
Step 2: Feature engineering with predictive indicators...
Created 145 features including 28 predictive indicators
Step 3: Time-based train/test split...
Train set: 8000 samples (400 positive)
Test set: 2000 samples (100 positive)
Step 4: Training classification model...
...
Step 6: Calculating metrics including predictive performance...
Early Detection Rate: 85.0%
Mean Lead Time: 4.2 hours
...
================================================================================
Training Summary - Predictive Maintenance
================================================================================
Model Type: xgboost
Regression Model: Yes
Features: 145
Train Samples: 8000
Test Samples: 2000
Accuracy: 0.9234
Precision: 0.8901
Recall: 0.8500
F1 Score: 0.8695
ROC-AUC: 0.9456
PR-AUC: 0.9123
Early Detection Rate: 85.00%
Mean Lead Time: 4.20 hours
Time-to-Failure MAE: 2.15 hours
Accuracy within 1 hour: 78.50%
Artifacts saved to: model/artifacts/v20250118_120000
================================================================================
```

## Troubleshooting

### Import Errors
If you get `ModuleNotFoundError`, install dependencies:
```bash
pip install -r requirements.txt
```

### XGBoost Not Available
The script automatically falls back to GradientBoosting if XGBoost is not installed.

### SHAP Errors
SHAP is optional. Use `--no-shap` to skip if it causes issues.

### Memory Issues
For large datasets, reduce `--n-iter` or use `--no-tuning` to save memory.

## Next Steps

1. **Train the model**: Run with default settings to generate a baseline model
2. **Integrate with dashboard**: Use the generated `model_loader.py` in your monitoring dashboard
3. **Collect real data**: Replace synthetic data with actual system metrics
4. **Retrain periodically**: Retrain the model as you collect more data

## Support

For issues or questions, check:
- Training logs in console output
- Artifact directory for saved models and metrics
- `metrics.json` for detailed evaluation results

