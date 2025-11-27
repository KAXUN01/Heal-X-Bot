# Model Performance Monitoring

## Overview

Monitor the performance of your predictive maintenance model over time and track prediction accuracy.

## Monitoring Scripts

### 1. Automated Retraining (`automated_retraining.py`)

Automatically retrains the model when:
- Model is older than specified days (default: 7)
- Model accuracy drops below threshold (default: 0.85)
- New training data is available

**Usage:**
```bash
# Check if retraining is needed
python3 automated_retraining.py

# Force retraining
python3 automated_retraining.py --force

# Custom thresholds
python3 automated_retraining.py --min-accuracy 0.90 --days-since-training 3
```

**Setup as Cron Job:**
```bash
# Weekly retraining (Sundays at 2 AM)
./setup_cron_retraining.sh

# Or manually add to crontab
crontab -e
# Add: 0 2 * * 0 cd /path/to/model && python3 automated_retraining.py
```

### 2. Model Performance Tracking

Track model metrics over time:

```python
from pathlib import Path
import json
import pandas as pd

def track_model_performance(artifacts_dir):
    """Track model performance across versions"""
    artifacts_dir = Path(artifacts_dir)
    versions = sorted([d for d in artifacts_dir.iterdir() if d.is_dir() and d.name.startswith('v')])
    
    performance_data = []
    for version_dir in versions:
        metrics_path = version_dir / "metrics.json"
        config_path = version_dir / "config.json"
        
        if metrics_path.exists() and config_path.exists():
            with open(metrics_path) as f:
                metrics = json.load(f)
            with open(config_path) as f:
                config = json.load(f)
            
            performance_data.append({
                'version': version_dir.name,
                'timestamp': config.get('timestamp'),
                'accuracy': metrics.get('accuracy', 0),
                'precision': metrics.get('precision', 0),
                'recall': metrics.get('recall', 0),
                'f1_score': metrics.get('f1_score', 0),
                'roc_auc': metrics.get('roc_auc', 0),
                'early_detection_rate': metrics.get('early_detection_rate', 0)
            })
    
    return pd.DataFrame(performance_data)
```

## Model Comparison

Compare different model versions:

```bash
# List all model versions
ls -la model/artifacts/

# Compare metrics
python3 -c "
from model.MODEL_MONITORING import track_model_performance
df = track_model_performance('model/artifacts')
print(df.to_string())
"
```

## Performance Metrics to Monitor

1. **Accuracy**: Overall prediction accuracy
2. **Early Detection Rate**: % of failures predicted >1 hour before
3. **False Positive Rate**: Minimize false alarms
4. **Lead Time**: Average hours before failure that prediction is made
5. **Model Drift**: Performance degradation over time

## Alerting on Model Degradation

Set up alerts when model performance drops:

```python
# In your monitoring script
metrics = get_latest_model_metrics()
if metrics.get('accuracy', 1.0) < 0.80:
    send_alert("Model accuracy dropped below 80% - retraining recommended")
```

## Best Practices

1. **Retrain Weekly**: Keep model current with latest data patterns
2. **Monitor Metrics**: Track accuracy, early detection rate, false positives
3. **A/B Testing**: Compare new models before full deployment
4. **Version Control**: Keep all model versions for rollback if needed
5. **Data Quality**: Ensure training data is clean and representative

