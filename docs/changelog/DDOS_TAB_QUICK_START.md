# DDoS Detection Tab - Quick Start Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Start the Dashboard API

```bash
cd /home/cdrditgis/Documents/Healing-bot
python3 monitoring/server/healing_dashboard_api.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Healing Bot Dashboard API started
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5001
```

### Step 2: Open the Dashboard

Open your browser and navigate to:
```
http://localhost:5001
```

### Step 3: View DDoS Detection

Click on the **"🛡️ DDoS Detection"** tab

You should now see:
- ✅ Total Detections counter
- ✅ DDoS Attacks counter  
- ✅ ML Performance metrics
- ✅ Attack Types chart
- ✅ Top Source IPs table

## 🧪 Test the Endpoints

Run the test script:
```bash
python3 test-ddos-endpoints.py
```

Expected output:
```
============================================================
DDoS Detection Endpoints Test Suite
============================================================

Testing: Health Check
✅ SUCCESS

Testing: ML Metrics
✅ SUCCESS

Testing: Attack Statistics
✅ SUCCESS

... (more tests)

✅ All tests passed!
```

## 📊 What You'll See

### Metric Cards
- **Total Detections**: 127 (sample data)
- **DDoS Attacks**: 23 (sample data)
- **False Positives**: 5 (sample data)
- **Detection Rate**: 18.1% (calculated)

### ML Performance
- **Accuracy**: ~95%
- **Precision**: ~92%
- **Recall**: ~88%
- **F1 Score**: ~90%
- **Prediction Time**: ~5.2ms
- **Throughput**: ~192.3/s

### Charts
1. **ML Performance Metrics** (line chart)
   - Shows accuracy, precision, recall, F1 score over time
   - Last 20 data points

2. **Attack Types Distribution** (pie chart)
   - TCP SYN Flood: 8
   - UDP Flood: 6
   - HTTP Flood: 5
   - ICMP Flood: 3
   - DNS Amplification: 1

### Top Source IPs Table
Shows threatening IPs with:
- IP Address
- Attack Count
- Last Seen timestamp
- Threat Level (Critical/High/Medium/Low)
- Block button

## 🔧 Troubleshooting

### Dashboard shows "Loading..."
**Fix:** Make sure the API is running on port 5001
```bash
curl http://localhost:5001/api/health
```

### All metrics show 0
**Fix:** Restart the dashboard API (sample data loads on startup)

### Charts are empty
**Fix:** 
1. Check browser console (F12) for errors
2. Clear cache and reload
3. Verify Chart.js is loading

### "Cannot connect" errors
**Fix:** Check if port 5001 is already in use:
```bash
sudo netstat -tulpn | grep 5001
```

## 🌐 API Endpoints Reference

All endpoints relative to `http://localhost:5001`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/metrics/ml` | GET | ML performance metrics |
| `/api/metrics/attacks` | GET | Attack statistics |
| `/api/history/ml` | GET | Historical ML data |
| `/api/blocking/block` | POST | Block an IP address |
| `/api/ddos/report` | POST | Report DDoS detection |

## 📝 Sample API Calls

### Get ML Metrics
```bash
curl http://localhost:5001/api/metrics/ml
```

### Get Attack Statistics
```bash
curl http://localhost:5001/api/metrics/attacks
```

### Block an IP
```bash
curl -X POST http://localhost:5001/api/blocking/block \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.0.2.1"}'
```

### Report DDoS Detection
```bash
curl -X POST http://localhost:5001/api/ddos/report \
  -H "Content-Type: application/json" \
  -d '{
    "is_ddos": true,
    "source_ip": "203.0.113.50",
    "attack_type": "TCP SYN Flood",
    "confidence": 0.92
  }'
```

## ⚙️ Configuration

### Change Port
```bash
export HEALING_DASHBOARD_PORT=8000
python3 monitoring/server/healing_dashboard_api.py
```

### Set Model Service URL
```bash
export MODEL_SERVICE_URL="http://localhost:8080"
python3 monitoring/server/healing_dashboard_api.py
```

### Enable Discord Alerts
```bash
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/YOUR_WEBHOOK"
python3 monitoring/server/healing_dashboard_api.py
```

## 🎯 Common Use Cases

### View Real-Time Attack Data
1. Start dashboard
2. Click DDoS Detection tab
3. Watch metrics update every 5 seconds

### Block Suspicious IP
1. Navigate to DDoS Detection tab
2. Find IP in "Top Source IPs" table
3. Click "Block" button
4. Confirm action

### Monitor ML Performance
1. View ML Performance Metrics chart
2. Check accuracy, precision, recall trends
3. Verify prediction times are acceptable

### Generate Test Data
```bash
# Send sample DDoS report
curl -X POST http://localhost:5001/api/ddos/report \
  -H "Content-Type: application/json" \
  -d '{
    "is_ddos": true,
    "source_ip": "198.51.100.42",
    "attack_type": "UDP Flood",
    "confidence": 0.95,
    "prediction": 0.91
  }'

# Refresh dashboard to see updated stats
```

## ✅ Success Indicators

You know it's working when:
- ✅ Dashboard loads without errors
- ✅ Metric cards show non-zero values
- ✅ ML Performance chart displays data
- ✅ Attack Types chart shows distribution
- ✅ Top Source IPs table is populated
- ✅ Block buttons are functional
- ✅ No JavaScript errors in browser console

## 🆘 Need Help?

1. **Check logs**: Look at terminal output where API is running
2. **Browser console**: Press F12 and check Console tab
3. **Network tab**: Press F12 and check Network tab for failed requests
4. **Test endpoints**: Run `python3 test-ddos-endpoints.py`
5. **Read docs**: See `DDOS_TAB_FIX.md` for detailed information

## 📚 Next Steps

After verifying the DDoS tab works:

1. **Integrate with ML Model**: Start the model service on port 8080
2. **Connect Network Analyzer**: Feed real network data
3. **Configure Alerts**: Set up Discord webhook for notifications
4. **Customize Thresholds**: Adjust detection sensitivity
5. **Export Data**: Implement data export features

## 🎉 That's It!

The DDoS Detection tab should now be fully functional and displaying real-time attack detection metrics!

