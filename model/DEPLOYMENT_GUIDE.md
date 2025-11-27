# Predictive Maintenance Model - Deployment Guide

## Production Deployment

### 1. Initial Model Training

```bash
cd model

# Install dependencies
pip install -r requirements.txt

# Train initial model
python3 train_xgboost_model.py --enable-regression

# Verify model
python3 verify_model.py
```

### 2. Set Up Automated Data Collection

```bash
# Collect training data continuously
python3 collect_training_data.py --duration 168 --interval 60
# (Collects for 1 week, every minute)

# Or set up as background service
nohup python3 collect_training_data.py --interval 60 > training_collection.log 2>&1 &
```

### 3. Set Up Automated Retraining

#### Option A: Cron Job (Recommended)

```bash
# Set up weekly retraining (Sundays at 2 AM)
./setup_cron_retraining.sh

# Or manually:
crontab -e
# Add: 0 2 * * 0 cd /path/to/model && python3 automated_retraining.py --no-tuning --no-shap
```

#### Option B: Systemd Timer

```bash
# Copy service file
sudo cp model/predictive-model.service /etc/systemd/system/

# Create timer file
sudo tee /etc/systemd/system/predictive-model.timer << EOF
[Unit]
Description=Weekly Predictive Model Retraining
Requires=predictive-model.service

[Timer]
OnCalendar=Sun *-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable predictive-model.timer
sudo systemctl start predictive-model.timer

# Check status
sudo systemctl status predictive-model.timer
```

### 4. Integration with Existing Services

The model is automatically loaded by the dashboard API. No additional service setup needed.

**Verify Integration:**
```bash
# Check if model is loaded
curl http://localhost:5001/api/predict-failure-risk

# Should return risk score (not error message)
```

### 5. Monitoring

#### Check Model Status
```bash
# Verify model
python3 model/verify_model.py

# Check training logs
tail -f logs/model-training.log

# Check retraining status
python3 model/automated_retraining.py
```

#### Monitor Model Performance
```bash
# View latest metrics
cat model/artifacts/latest/metrics.json | jq .

# Compare model versions
python3 -c "
from pathlib import Path
import json

artifacts = Path('model/artifacts')
versions = sorted([d for d in artifacts.iterdir() if d.is_dir() and d.name.startswith('v')], reverse=True)

for v in versions[:5]:
    metrics_file = v / 'metrics.json'
    if metrics_file.exists():
        with open(metrics_file) as f:
            m = json.load(f)
        print(f\"{v.name}: Accuracy={m.get('accuracy', 0):.4f}, Early Detection={m.get('early_detection_rate', 0):.2%}\")
"
```

## Health Checks

### Model Health Check Script

```bash
#!/bin/bash
# Add to your monitoring system

MODEL_DIR="/path/to/model"
if [ ! -f "$MODEL_DIR/artifacts/latest/model_loader.py" ]; then
    echo "CRITICAL: Model not found"
    exit 2
fi

python3 "$MODEL_DIR/verify_model.py" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "OK: Model is healthy"
    exit 0
else
    echo "WARNING: Model verification failed"
    exit 1
fi
```

## Troubleshooting

### Model Not Loading

1. **Check if model exists:**
   ```bash
   ls -la model/artifacts/latest/
   ```

2. **Train model if missing:**
   ```bash
   python3 model/train_xgboost_model.py --no-tuning --no-shap
   ```

3. **Check permissions:**
   ```bash
   chmod -R 755 model/artifacts/
   ```

### API Returns "Model not available"

1. **Verify model path:**
   ```bash
   python3 model/verify_model.py
   ```

2. **Restart dashboard API:**
   ```bash
   # The API auto-loads from artifacts/latest/
   # Just restart the service
   sudo systemctl restart healing-bot
   ```

### Low Prediction Accuracy

1. **Collect more training data:**
   ```bash
   python3 model/collect_training_data.py --duration 168
   ```

2. **Retrain with new data:**
   ```bash
   python3 model/train_xgboost_model.py --data-path model/training_data/system_metrics_*.csv --enable-regression
   ```

3. **Enable hyperparameter tuning:**
   ```bash
   python3 model/train_xgboost_model.py --enable-regression --n-iter 50
   ```

## Production Checklist

- [ ] Model trained and verified
- [ ] Data collection running
- [ ] Automated retraining scheduled
- [ ] Dashboard API can load model
- [ ] Dashboard widget displaying predictions
- [ ] Health checks configured
- [ ] Monitoring alerts set up
- [ ] Logs being collected
- [ ] Backup strategy for model artifacts

