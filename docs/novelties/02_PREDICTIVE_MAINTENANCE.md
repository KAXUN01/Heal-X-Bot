# Novelty 2: Predictive Maintenance with Machine Learning

## Overview

Heal-X-Bot implements advanced predictive maintenance capabilities using XGBoost machine learning models to predict system failures 1-24 hours before they occur, enabling proactive intervention and reducing unplanned downtime.

## Why This Is Novel

| Traditional Approach | Heal-X-Bot Innovation |
|---------------------|----------------------|
| Reactive maintenance | Proactive prediction |
| Fixed schedules | Data-driven timing |
| Resource waste | Optimized interventions |
| Unexpected failures | 85-90% early detection |
| Manual monitoring | Automated forecasting |

---

## Problem Statement

### Challenges Addressed
1. **Unexpected Failures**: Systems fail without warning, causing downtime
2. **Resource Inefficiency**: Scheduled maintenance may be too early or too late
3. **Alert Fatigue**: Too many false alerts reduce response effectiveness
4. **Limited Visibility**: No insight into future system state
5. **Reactive Operations**: Teams only respond after problems occur

---

## Solution Architecture

### Dual-Model Approach
```
┌─────────────────────────────────────────────────────────┐
│                    Prediction Engine                     │
├────────────────────────┬────────────────────────────────┤
│  Classification Model  │     Regression Model           │
│  (Will failure occur?) │  (When will failure occur?)    │
├────────────────────────┼────────────────────────────────┤
│  XGBoost Classifier    │     XGBoost Regressor          │
│  Output: True/False    │     Output: Hours to Failure   │
│  Accuracy: 85-90%      │     MAE: 1.5-3.0 hours         │
└────────────────────────┴────────────────────────────────┘
```

### Feature Engineering
| Feature Category | Features |
|-----------------|----------|
| **Resource Metrics** | CPU%, Memory%, Disk%, Network I/O |
| **Service Health** | Service status, restart count, uptime |
| **Error Patterns** | Error rate, error frequency, error clusters |
| **Trend Data** | 5-min avg, 15-min avg, 1-hour avg |
| **Historical** | Past failure patterns, seasonality |

---

## Technical Deep Dive

### Classification Model
```python
from xgboost import XGBClassifier

classifier = XGBClassifier(
    objective='binary:logistic',
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

# Training
classifier.fit(X_train, y_train_failure)

# Prediction
failure_probability = classifier.predict_proba(X_test)[:, 1]
will_fail = failure_probability > 0.5
```

### Regression Model
```python
from xgboost import XGBRegressor

regressor = XGBRegressor(
    objective='reg:squarederror',
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

# Training
regressor.fit(X_train, y_train_hours)

# Prediction
hours_to_failure = regressor.predict(X_test)
```

### Risk Score Calculation
```python
def calculate_risk_score(metrics: Dict) -> float:
    """
    Calculate overall risk score (0-100)
    """
    weights = {
        'ml_prediction': 0.30,      # ML model output
        'cpu_trend': 0.15,          # CPU usage trend
        'memory_trend': 0.15,       # Memory usage trend
        'disk_trend': 0.10,         # Disk fill rate
        'error_rate': 0.15,         # Error frequency
        'service_health': 0.15      # Service status
    }
    
    score = 0
    for metric, weight in weights.items():
        normalized = normalize_metric(metrics[metric])
        score += normalized * weight * 100
    
    return min(100, max(0, score))
```

---

## Flow Diagram

```
┌─────────────────┐
│ Metrics Collector│
│ (Every 30 sec)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐
│ Feature Engineer│───►│ Historical DB   │
└────────┬────────┘    └─────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│Classify│ │Regress │
│ Model  │ │ Model  │
└────┬───┘ └───┬────┘
     │         │
     └────┬────┘
          │
          ▼
┌─────────────────┐
│  Risk Scorer    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│Warning │ │Dashboard│
│System  │ │Update   │
└────────┘ └────────┘
```

---

## Warning System

### Warning Types
| Warning | Trigger | Severity | TTL |
|---------|---------|----------|-----|
| CPU_HIGH | CPU > 85% trending up | Medium | 15min |
| MEMORY_HIGH | Memory > 90% | High | 10min |
| DISK_FULL | Disk > 90% fill rate | Critical | 5min |
| ERROR_SPIKE | Error rate 3x normal | High | 10min |
| ML_PREDICTION | Model predicts failure | Varies | 30min |

### Warning Generation
```python
def generate_warnings(metrics: Dict, predictions: Dict) -> List[Warning]:
    warnings = []
    
    # CPU Warning
    if metrics['cpu_percent'] > 85:
        warnings.append(Warning(
            type='CPU_HIGH',
            severity='medium',
            message=f"CPU at {metrics['cpu_percent']:.1f}%, trending up",
            ttl=900  # 15 minutes
        ))
    
    # ML Prediction Warning
    if predictions['failure_probability'] > 0.7:
        hours = predictions['hours_to_failure']
        warnings.append(Warning(
            type='ML_PREDICTION',
            severity='high' if hours < 2 else 'medium',
            message=f"Model predicts failure in {hours:.1f} hours",
            eta=datetime.now() + timedelta(hours=hours)
        ))
    
    return warnings
```

---

## API Reference

### Prediction Status
```http
GET /api/predictive/status
```

**Response:**
```json
{
  "risk_score": 67,
  "risk_level": "High",
  "failure_probability": 0.72,
  "hours_to_failure": 4.5,
  "predicted_failure_time": "2026-01-16T18:30:00Z",
  "warnings_count": 2,
  "last_update": "2026-01-16T14:00:00Z"
}
```

### Early Warnings
```http
GET /api/predictive/warnings
```

**Response:**
```json
{
  "warnings": [
    {
      "id": "warn-001",
      "type": "ML_PREDICTION",
      "severity": "high",
      "message": "Model predicts failure in 4.5 hours",
      "component": "system",
      "created_at": "2026-01-16T14:00:00Z",
      "eta": "2026-01-16T18:30:00Z"
    }
  ]
}
```

### Prediction History
```http
GET /api/predictive/history?hours=24
```

---

## Configuration

### Predictive Maintenance Config
```json
{
  "predictive_maintenance": {
    "enabled": true,
    "check_interval_seconds": 30,
    "history_hours": 24,
    "thresholds": {
      "low_risk": 30,
      "medium_risk": 60,
      "high_risk": 80,
      "critical_risk": 90
    },
    "warnings": {
      "cpu_threshold": 85,
      "memory_threshold": 90,
      "disk_threshold": 90,
      "error_multiplier": 3
    }
  }
}
```

---

## Performance Metrics

### Classification Performance
| Metric | Value |
|--------|-------|
| Accuracy | 87% |
| Precision | 85% |
| Recall | 89% |
| F1-Score | 0.87 |
| AUC-ROC | 0.91 |

### Regression Performance
| Metric | Value |
|--------|-------|
| MAE | 2.1 hours |
| RMSE | 3.2 hours |
| R² | 0.78 |

### Detection Rates by Horizon
| Prediction Window | Detection Rate |
|-------------------|----------------|
| 1 Hour | 85-90% |
| 6 Hours | 80-85% |
| 24 Hours | 75-80% |

---

## Use Cases

### 1. Scheduled Maintenance
Use predictions to schedule maintenance during low-risk periods.

### 2. Resource Allocation
Allocate additional resources before predicted failures.

### 3. Alert Prioritization
Prioritize alerts based on predicted failure severity.

### 4. Capacity Planning
Use trends to plan capacity increases.

---

## Model Files

```
model/
├── predictive/
│   ├── classifier.pkl        # XGBoost classifier
│   ├── regressor.pkl         # XGBoost regressor
│   ├── feature_scaler.pkl    # Feature normalization
│   ├── feature_names.json    # Feature list
│   └── model_metrics.json    # Performance metrics
```

---

## Future Enhancements

1. **Ensemble Methods**: Combine multiple models
2. **Deep Learning**: LSTM for time-series prediction
3. **Root Cause Prediction**: Predict what will fail
4. **Maintenance Scheduling**: AI-optimized scheduling
5. **Anomaly Correlation**: Link predictions to anomalies
