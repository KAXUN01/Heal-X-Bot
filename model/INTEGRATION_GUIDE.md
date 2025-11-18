# Predictive Maintenance Dashboard Integration Guide

## Overview

This guide explains how to integrate the predictive maintenance model with your monitoring dashboard for real-time failure predictions and early warnings.

## API Endpoints

The following endpoints are available in `monitoring/server/healing_dashboard_api.py`:

### 1. Get Failure Risk Score
```http
GET /api/predict-failure-risk
```

Returns current failure risk score (0-1) based on system metrics.

**Response:**
```json
{
  "timestamp": "2024-01-18T12:00:00",
  "risk_score": 0.75,
  "risk_percentage": 75.0,
  "has_early_warning": true,
  "is_high_risk": true
}
```

### 2. Get Early Warnings
```http
GET /api/get-early-warnings
```

Returns list of active early warning indicators.

**Response:**
```json
{
  "timestamp": "2024-01-18T12:00:00",
  "warning_count": 3,
  "has_warnings": true,
  "warnings": [
    {
      "type": "cpu_high",
      "severity": "high",
      "message": "CPU usage at 92.5%"
    },
    {
      "type": "memory_high",
      "severity": "high",
      "message": "Memory usage at 88.0%"
    },
    {
      "type": "ml_prediction",
      "severity": "high",
      "message": "ML model predicts failure risk: 75.0%"
    }
  ]
}
```

### 3. Predict Time to Failure
```http
GET /api/predict-time-to-failure
```

Returns estimated hours until next failure.

**Response:**
```json
{
  "timestamp": "2024-01-18T12:00:00",
  "hours_until_failure": 4.5,
  "predicted_failure_time": "2024-01-18T16:30:00",
  "confidence": "High"
}
```

### 4. Real-time Anomaly Detection
```http
POST /api/predict-anomaly
Content-Type: application/json

{
  "metrics": {
    "cpu_percent": 85.0,
    "memory_percent": 90.0,
    "disk_percent": 75.0,
    ...
  }
}
```

**Response:**
```json
{
  "timestamp": "2024-01-18T12:00:00",
  "is_anomaly": true,
  "anomaly_score": 0.82,
  "risk_level": "High"
}
```

## Frontend Integration

### JavaScript Example

```javascript
// Fetch failure risk
async function getFailureRisk() {
  const response = await fetch('/api/predict-failure-risk');
  const data = await response.json();
  
  // Update UI
  document.getElementById('risk-score').textContent = 
    `${(data.risk_score * 100).toFixed(1)}%`;
  
  // Color code based on risk
  const riskElement = document.getElementById('risk-indicator');
  if (data.is_high_risk) {
    riskElement.className = 'risk-high';
  } else if (data.has_early_warning) {
    riskElement.className = 'risk-medium';
  } else {
    riskElement.className = 'risk-low';
  }
}

// Fetch early warnings
async function getEarlyWarnings() {
  const response = await fetch('/api/get-early-warnings');
  const data = await response.json();
  
  const warningsList = document.getElementById('warnings-list');
  warningsList.innerHTML = '';
  
  if (data.has_warnings) {
    data.warnings.forEach(warning => {
      const item = document.createElement('div');
      item.className = `warning-${warning.severity}`;
      item.textContent = warning.message;
      warningsList.appendChild(item);
    });
  }
}

// Fetch time to failure
async function getTimeToFailure() {
  const response = await fetch('/api/predict-time-to-failure');
  const data = await response.json();
  
  if (data.hours_until_failure) {
    document.getElementById('time-to-failure').textContent = 
      `${data.hours_until_failure.toFixed(1)} hours`;
    document.getElementById('predicted-time').textContent = 
      new Date(data.predicted_failure_time).toLocaleString();
  } else {
    document.getElementById('time-to-failure').textContent = 'No failure predicted';
  }
}

// Update every 30 seconds
setInterval(() => {
  getFailureRisk();
  getEarlyWarnings();
  getTimeToFailure();
}, 30000);
```

### HTML Dashboard Widget

```html
<div class="predictive-maintenance-widget">
  <h3>Predictive Maintenance</h3>
  
  <div class="risk-indicator">
    <div id="risk-score">0%</div>
    <div id="risk-indicator" class="risk-low"></div>
  </div>
  
  <div class="time-to-failure">
    <label>Predicted Failure:</label>
    <div id="time-to-failure">Calculating...</div>
    <div id="predicted-time"></div>
  </div>
  
  <div class="early-warnings">
    <h4>Early Warnings</h4>
    <div id="warnings-list"></div>
  </div>
</div>
```

## Python Client Example

```python
import requests
import time

def monitor_system():
    """Monitor system with predictive maintenance"""
    base_url = "http://localhost:5001"  # Healing dashboard API
    
    while True:
        try:
            # Get failure risk
            risk_response = requests.get(f"{base_url}/api/predict-failure-risk")
            risk_data = risk_response.json()
            
            print(f"Risk Score: {risk_data.get('risk_percentage', 0):.1f}%")
            
            # Get early warnings
            warnings_response = requests.get(f"{base_url}/api/get-early-warnings")
            warnings_data = warnings_response.json()
            
            if warnings_data.get('has_warnings'):
                print(f"⚠️  {warnings_data['warning_count']} active warnings:")
                for warning in warnings_data['warnings']:
                    print(f"  - {warning['message']}")
            
            # Get time to failure
            time_response = requests.get(f"{base_url}/api/predict-time-to-failure")
            time_data = time_response.json()
            
            if time_data.get('hours_until_failure'):
                print(f"⏰ Predicted failure in {time_data['hours_until_failure']:.1f} hours")
            
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    monitor_system()
```

## WebSocket Integration

For real-time updates, you can extend the existing WebSocket in `healing_dashboard_api.py`:

```python
@app.websocket("/ws/predictive-maintenance")
async def predictive_maintenance_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Get predictions
            risk = await predict_failure_risk()
            warnings = await get_early_warnings()
            time_to_failure = await predict_time_to_failure()
            
            # Send to client
            await websocket.send_json({
                "type": "predictive_update",
                "risk": risk,
                "warnings": warnings,
                "time_to_failure": time_to_failure
            })
            
            await asyncio.sleep(30)  # Update every 30 seconds
    except WebSocketDisconnect:
        pass
```

## Alerting Integration

### Discord Webhook Example

```python
import requests
import json

def send_predictive_alert(risk_data, warnings_data):
    """Send alert to Discord when high risk detected"""
    if not risk_data.get('is_high_risk'):
        return
    
    webhook_url = os.getenv('DISCORD_WEBHOOK')
    if not webhook_url:
        return
    
    message = {
        "embeds": [{
            "title": "⚠️ High Failure Risk Detected",
            "description": f"Risk Score: {risk_data['risk_percentage']:.1f}%",
            "color": 15158332,  # Red
            "fields": [
                {
                    "name": "Early Warnings",
                    "value": "\n".join([w['message'] for w in warnings_data.get('warnings', [])])
                }
            ]
        }]
    }
    
    requests.post(webhook_url, json=message)
```

## Model Updates

When you retrain the model:

1. Train new model:
```bash
python3 model/train_xgboost_model.py --enable-regression
```

2. The new model will be saved to `model/artifacts/v{timestamp}/`

3. The `latest/` symlink will automatically point to the new model

4. Restart the dashboard API to load the new model:
```bash
# The model loader will automatically use the latest version
```

## Troubleshooting

### Model Not Found
If you get "Predictive model not available":
1. Train the model first: `python3 train_xgboost_model.py`
2. Check that `model/artifacts/latest/model_loader.py` exists
3. Restart the dashboard API

### Import Errors
Make sure all dependencies are installed:
```bash
pip install -r model/requirements.txt
```

### Low Prediction Accuracy
- Collect more training data
- Retrain with `--enable-regression` for time-to-failure
- Adjust prediction thresholds in `prediction_thresholds.json`

