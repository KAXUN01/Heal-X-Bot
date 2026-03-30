# DDoS Detection Page

## Description
The DDoS Detection page provides AI-powered distributed denial-of-service attack detection and mitigation. It uses machine learning models trained on network traffic patterns to identify and block malicious traffic in real-time.

## Purpose
- Detect DDoS attacks using ML classification
- Visualize attack patterns and blocked IPs
- Provide real-time traffic analysis
- Enable manual and automatic IP blocking

## Features

### 1. Attack Detection Status
- **ML Model Status**: Active/Inactive indicator
- **Detection Mode**: Passive monitoring or Active blocking
- **Last Update**: Timestamp of latest analysis
- **Model Accuracy**: Current model performance metrics

### 2. Traffic Analysis Panel
- Real-time network traffic visualization
- Packets per second metrics
- Bandwidth utilization
- Protocol distribution (TCP/UDP/ICMP)

### 3. Threat Detection
- Attack type classification
- Confidence score display
- Source IP identification
- Attack pattern visualization

### 4. IP Blocking Controls

| Action | Description | Scope |
|--------|-------------|-------|
| **Auto-Block** | Automatically block detected attackers | System-wide |
| **Manual Block** | Add IP to blocklist manually | Custom |
| **Whitelist** | Exempt IPs from blocking | Trusted |
| **Unblock** | Remove IP from blocklist | Specific IP |

### 5. Attack History
- Historical attack log
- Attack patterns over time
- Blocked IP statistics
- False positive tracking

## Machine Learning Model

### Model Architecture
```
Input Layer: 12 features
├── Hidden Layer 1: 64 neurons (ReLU)
├── Hidden Layer 2: 32 neurons (ReLU)
├── Dropout: 0.3
└── Output Layer: 9 classes (Softmax)
```

### Detection Classes
| Class | Label | Description |
|-------|-------|-------------|
| 0 | BENIGN | Normal traffic |
| 1 | DDoS-UDP | UDP flood attack |
| 2 | DDoS-TCP | TCP flood attack |
| 3 | DDoS-HTTP | HTTP flood attack |
| 4 | DDoS-ICMP | ICMP flood attack |
| 5 | DDoS-SYN | SYN flood attack |
| 6 | DDoS-ACK | ACK flood attack |
| 7 | DDoS-PSH+ACK | PSH+ACK flood attack |
| 8 | OTHER | Unclassified attack |

### Feature Extraction
12 network features used for classification:
1. Flow duration
2. Total forward packets
3. Total backward packets
4. Forward packet length (mean, max)
5. Backward packet length (mean, max)
6. Flow bytes/second
7. Flow packets/second
8. Protocol type
9. Destination port
10. Flag counts

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ddos/status` | GET | Get detection system status |
| `/api/ddos/predict` | POST | Run prediction on traffic data |
| `/api/ddos/history` | GET | Get attack history |
| `/api/ddos/block` | POST | Block specific IP |
| `/api/ddos/unblock` | POST | Unblock specific IP |
| `/api/ddos/blocked` | GET | List blocked IPs |
| `/api/ddos/model/info` | GET | Get model information |

## Technical Implementation

### Model Files
```
model/
├── ddos_model.h5           # Trained Keras model
├── scaler.pkl              # Feature scaler
├── label_encoder.pkl       # Label encoder
└── feature_names.pkl       # Feature column names
```

### Prediction Flow
```python
1. Extract features from network packet
2. Scale features using StandardScaler
3. Run inference through Keras model
4. Get classification and confidence
5. Apply blocking if attack detected
```

### Configuration
```json
{
  "detection": {
    "threshold": 0.75,
    "block_duration": 3600,
    "auto_block": true,
    "whitelist": ["192.168.1.1"]
  }
}
```

## User Actions
- Enable/disable auto-blocking
- Manually block/unblock IPs
- View attack details
- Export attack logs
- Configure detection thresholds

## IP History & Analytics
- Track block/unblock events per IP
- View attack frequency patterns
- Analyze geographic distribution
- Generate threat reports

## Background Details

### Network Analyzer
- Captures network packets using scapy
- Extracts features in real-time
- Sends features to ML model API
- Receives classification results

### Blocking Mechanism
- Uses iptables on Linux
- Maintains persistent blocklist
- Supports time-based auto-unblock
- Integrates with firewall rules

## Related Pages
- [Active Alerts](02_ACTIVE_ALERTS.md) - DDoS alerts
- [Logs & AI](07_LOGS_AI.md) - Network logs
- [Overview](01_OVERVIEW.md) - Attack summary
