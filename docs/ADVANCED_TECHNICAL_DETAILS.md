# 🔧 Heal-X-Bot: Advanced Technical Details

## Table of Contents

1. [System Architecture Deep Dive](#system-architecture-deep-dive)
2. [API Documentation](#api-documentation)
3. [Database Schemas](#database-schemas)
4. [Security Implementation](#security-implementation)
5. [Performance Optimization](#performance-optimization)
6. [Scaling Considerations](#scaling-considerations)
7. [Integration Patterns](#integration-patterns)
8. [Development Guide](#development-guide)
9. [Deployment Strategies](#deployment-strategies)
10. [Monitoring & Observability](#monitoring--observability)

---

## System Architecture Deep Dive

### Component Architecture

#### Healing Dashboard API

**Technology**: FastAPI (Python)

**Architecture**:
```
FastAPI Application
    │
    ├─ REST API Routes
    │   ├─ /api/health
    │   ├─ /api/metrics
    │   ├─ /api/services
    │   └─ /api/blocking
    │
    ├─ WebSocket Routes
    │   └─ /ws/healing
    │
    ├─ Static File Serving
    │   └─ /static/*
    │
    └─ Middleware
        ├─ CORS
        ├─ Error Handling
        └─ Logging
```

**Key Components**:
- `healing_dashboard_api.py`: Main FastAPI application
- `blocked_ips_db.py`: SQLite database interface
- `healing/`: Auto-healing system modules
- `core/`: Core configuration and service management

**Dependencies**:
- FastAPI: Web framework
- WebSockets: Real-time communication
- SQLite: Database
- psutil: System metrics
- asyncio: Async operations

#### ML Model API

**Technology**: FastAPI + TensorFlow/XGBoost

**Architecture**:
```
Model API Server
    │
    ├─ DDoS Detection Model
    │   ├─ TensorFlow/Keras Model
    │   ├─ Feature Extraction
    │   └─ Prediction Engine
    │
    └─ Predictive Maintenance Model
        ├─ XGBoost Classifier
        ├─ XGBoost Regressor
        ├─ Feature Engineering
        └─ Prediction Engine
```

**Model Loading**:
```python
# DDoS Model
model = tf.keras.models.load_model("ddos_model.keras")

# Predictive Model
classifier = joblib.load("artifacts/latest/model.pkl")
regressor = joblib.load("artifacts/latest/regression_model.pkl")
scaler = joblib.load("artifacts/latest/scaler.pkl")
```

**Prediction Pipeline**:
1. Feature extraction from input
2. Feature normalization (StandardScaler)
3. Model prediction
4. Post-processing and formatting
5. Response generation

#### Network Analyzer

**Technology**: FastAPI + Network Analysis Libraries

**Architecture**:
```
Network Analyzer
    │
    ├─ Traffic Analysis
    │   ├─ Packet Capture
    │   ├─ Flow Analysis
    │   └─ Pattern Detection
    │
    ├─ IP Blocking
    │   ├─ iptables Integration
    │   ├─ Firewall Rules
    │   └─ Rule Persistence
    │
    └─ Threat Assessment
        ├─ Threat Level Calculation
        ├─ Risk Scoring
        └─ Auto-Blocking Logic
```

**IP Blocking Implementation**:
```python
def block_ip(ip_address):
    # Add iptables rule
    subprocess.run([
        "iptables", "-A", "INPUT",
        "-s", ip_address,
        "-j", "DROP"
    ])
    
    # Save to database
    blocked_ips_db.add_blocked_ip(ip_address)
    
    # Persist rules
    subprocess.run(["iptables-save"])
```

#### Monitoring Server

**Technology**: FastAPI + psutil + Log Aggregation

**Architecture**:
```
Monitoring Server
    │
    ├─ System Metrics Collection
    │   ├─ CPU Metrics
    │   ├─ Memory Metrics
    │   ├─ Disk Metrics
    │   └─ Network Metrics
    │
    ├─ Log Aggregation
    │   ├─ Centralized Logger
    │   ├─ Log Rotation
    │   └─ Log Analysis
    │
    └─ Service Monitoring
        ├─ Service Health Checks
        ├─ Service Status Tracking
        └─ Service Restart Logic
```

**Metrics Collection**:
```python
def collect_metrics():
    return {
        "cpu": psutil.cpu_percent(interval=1),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
        "network": {
            "bytes_sent": psutil.net_io_counters().bytes_sent,
            "bytes_recv": psutil.net_io_counters().bytes_recv
        }
    }
```

### Data Flow Architecture

#### Real-Time Metrics Flow

```
System (OS)
    │
    ▼ (psutil)
System Metrics Collector
    │
    ▼ (Every 2 seconds)
Metrics Cache (In-Memory)
    │
    ├─ WebSocket Broadcast
    │   └─ Dashboard Clients
    │
    └─ REST API Endpoint
        └─ API Clients
```

#### DDoS Detection Flow

```
Network Traffic
    │
    ▼
Network Analyzer
    │
    ▼ (Feature Extraction)
28 Network Features
    │
    ▼ (Normalization)
StandardScaler
    │
    ▼
DDoS Model (TensorFlow)
    │
    ▼ (Prediction)
Threat Probability (0-1)
    │
    ├─ < 0.5: Legitimate
    ├─ 0.5-0.8: Monitor
    └─ > 0.8: Auto-Block
```

#### Predictive Maintenance Flow

```
System Metrics
    │
    ▼ (Every 60 seconds)
Feature Engineering
    │
    ▼ (145 Features)
Feature Scaling
    │
    ├─ Classification Model
    │   └─ Failure Risk (0-1)
    │
    └─ Regression Model
        └─ Time to Failure (hours)
    │
    ▼
Early Warning System
    │
    └─ Dashboard Alert
```

---

## API Documentation

### REST API Endpoints

#### Base URL

All API endpoints are relative to:
- **Healing Dashboard**: `http://localhost:5001`
- **Monitoring Server**: `http://localhost:5000`
- **Model API**: `http://localhost:8080`
- **Network Analyzer**: `http://localhost:8000`
- **Incident Bot**: `http://localhost:8001`

### Healing Dashboard API

#### Health Check

```http
GET /api/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-19T12:00:00",
  "services": {
    "dashboard": "healthy",
    "monitoring": "healthy",
    "model": "healthy"
  }
}
```

#### System Metrics

```http
GET /api/metrics
```

**Response**:
```json
{
  "cpu": 45.2,
  "memory": 62.8,
  "disk": 58.3,
  "network": {
    "bytes_sent": 1234567,
    "bytes_recv": 7654321,
    "packets_sent": 1234,
    "packets_recv": 5678
  },
  "timestamp": "2025-01-19T12:00:00"
}
```

#### Service Management

```http
GET /api/services
```

**Response**:
```json
{
  "services": [
    {
      "name": "nginx",
      "status": "running",
      "pid": 12345,
      "uptime": 3600,
      "auto_restart": true
    }
  ]
}
```

```http
POST /api/services/{name}/restart
```

**Request Body**: None

**Response**:
```json
{
  "status": "success",
  "message": "Service nginx restarted successfully",
  "timestamp": "2025-01-19T12:00:00"
}
```

#### IP Blocking

```http
GET /api/blocking/ips
```

**Query Parameters**:
- `limit` (optional): Number of results (default: 100)
- `offset` (optional): Pagination offset (default: 0)
- `search` (optional): Search IP address

**Response**:
```json
{
  "ips": [
    {
      "ip": "192.168.1.100",
      "threat_level": 0.9,
      "reason": "DDoS attack",
      "block_type": "auto",
      "blocked_at": "2025-01-19T10:00:00",
      "unblocked_at": null
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

```http
POST /api/blocking/block
Content-Type: application/json

{
  "ip": "192.168.1.100",
  "reason": "Suspicious activity",
  "threat_level": 0.8
}
```

**Response**:
```json
{
  "status": "success",
  "message": "IP 192.168.1.100 blocked successfully",
  "timestamp": "2025-01-19T12:00:00"
}
```

```http
POST /api/blocking/unblock
Content-Type: application/json

{
  "ip": "192.168.1.100"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "IP 192.168.1.100 unblocked successfully",
  "timestamp": "2025-01-19T12:00:00"
}
```

#### Predictive Maintenance

```http
GET /api/predict-failure-risk
```

**Response**:
```json
{
  "timestamp": "2025-01-19T12:00:00",
  "risk_score": 0.75,
  "risk_percentage": 75.0,
  "has_early_warning": true,
  "is_high_risk": true
}
```

```http
GET /api/get-early-warnings
```

**Response**:
```json
{
  "timestamp": "2025-01-19T12:00:00",
  "warning_count": 3,
  "has_warnings": true,
  "warnings": [
    {
      "type": "cpu_high",
      "severity": "high",
      "message": "CPU usage at 92.5%"
    }
  ]
}
```

```http
GET /api/predict-time-to-failure
```

**Response**:
```json
{
  "timestamp": "2025-01-19T12:00:00",
  "hours_until_failure": 4.5,
  "predicted_failure_time": "2025-01-19T16:30:00",
  "confidence": "High"
}
```

### WebSocket API

#### Connection

```javascript
const ws = new WebSocket('ws://localhost:5001/ws/healing');
```

#### Message Format

**Client → Server**:
```json
{
  "type": "subscribe",
  "channel": "metrics"
}
```

**Server → Client**:
```json
{
  "type": "metrics",
  "data": {
    "cpu": 45.2,
    "memory": 62.8,
    "disk": 58.3
  },
  "timestamp": "2025-01-19T12:00:00"
}
```

#### Message Types

- `metrics`: System metrics update
- `alert`: Alert notification
- `service_status`: Service status change
- `blocked_ip`: IP blocking event

---

## Database Schemas

### Blocked IPs Database (SQLite)

#### Schema

```sql
CREATE TABLE blocked_ips (
    ip TEXT PRIMARY KEY,
    threat_level REAL NOT NULL,
    reason TEXT,
    block_type TEXT NOT NULL,  -- 'auto' or 'manual'
    blocked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    unblocked_at TIMESTAMP,
    unblock_reason TEXT
);

CREATE INDEX idx_blocked_at ON blocked_ips(blocked_at);
CREATE INDEX idx_block_type ON blocked_ips(block_type);
CREATE INDEX idx_unblocked_at ON blocked_ips(unblocked_at);
```

#### Example Queries

**Get All Blocked IPs**:
```sql
SELECT * FROM blocked_ips 
WHERE unblocked_at IS NULL 
ORDER BY blocked_at DESC;
```

**Get Blocking Statistics**:
```sql
SELECT 
    block_type,
    COUNT(*) as count,
    AVG(threat_level) as avg_threat_level
FROM blocked_ips
WHERE unblocked_at IS NULL
GROUP BY block_type;
```

### Log Storage

#### Centralized Log Format (JSON)

```json
{
  "timestamp": "2025-01-19T12:00:00",
  "level": "INFO",
  "service": "monitoring",
  "message": "System metrics collected",
  "metadata": {
    "cpu": 45.2,
    "memory": 62.8
  }
}
```

#### Log Rotation

- **Size Limit**: 10MB per log file
- **Rotation**: Automatic when size limit reached
- **Retention**: 7 days (configurable)
- **Compression**: Optional (gzip)

---

## Security Implementation

### Authentication & Authorization

**Current Implementation**: No authentication for local access (development mode)

**Production Recommendations**:
1. Implement API key authentication
2. Use JWT tokens for WebSocket connections
3. Role-based access control (RBAC)
4. Rate limiting per IP/user

### Input Validation

**API Input Validation**:
```python
from pydantic import BaseModel, validator

class BlockIPRequest(BaseModel):
    ip: str
    reason: str
    threat_level: float
    
    @validator('ip')
    def validate_ip(cls, v):
        import ipaddress
        ipaddress.ip_address(v)  # Raises if invalid
        return v
    
    @validator('threat_level')
    def validate_threat_level(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Threat level must be between 0 and 1')
        return v
```

### SQL Injection Prevention

**Parameterized Queries**:
```python
# Safe
cursor.execute(
    "SELECT * FROM blocked_ips WHERE ip = ?",
    (ip_address,)
)

# Unsafe (DO NOT USE)
cursor.execute(
    f"SELECT * FROM blocked_ips WHERE ip = '{ip_address}'"
)
```

### XSS Prevention

**Output Escaping**:
- All user input is escaped before display
- JSON responses use proper serialization
- HTML content is sanitized

### Rate Limiting

**Implementation** (Recommended):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/blocking/block")
@limiter.limit("10/minute")
async def block_ip(request: Request):
    # Endpoint implementation
    pass
```

---

## Performance Optimization

### Caching Strategies

#### In-Memory Caching

```python
from functools import lru_cache
import time

# Cache system metrics for 2 seconds
@lru_cache(maxsize=1)
def get_cached_metrics():
    return collect_metrics()

# Clear cache every 2 seconds
last_cache_clear = time.time()
if time.time() - last_cache_clear > 2:
    get_cached_metrics.cache_clear()
    last_cache_clear = time.time()
```

#### Database Query Optimization

**Indexes**:
```sql
CREATE INDEX idx_blocked_at ON blocked_ips(blocked_at);
CREATE INDEX idx_ip ON blocked_ips(ip);
```

**Query Optimization**:
- Use LIMIT for pagination
- Use WHERE clauses to filter early
- Avoid SELECT * when possible

### Async Operations

**Async Endpoints**:
```python
@app.get("/api/metrics")
async def get_metrics():
    # Async operations
    metrics = await collect_metrics_async()
    return metrics
```

**Concurrent Processing**:
```python
import asyncio

async def process_multiple_ips(ips):
    tasks = [process_ip(ip) for ip in ips]
    results = await asyncio.gather(*tasks)
    return results
```

### Model Optimization

#### Model Quantization

**TensorFlow Model**:
```python
# Quantize model for faster inference
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()
```

#### Batch Processing

```python
# Process multiple predictions in batch
def predict_batch(features_batch):
    predictions = model.predict(features_batch)
    return predictions
```

---

## Scaling Considerations

### Horizontal Scaling

#### Load Balancing

**Architecture**:
```
Load Balancer (nginx/HAProxy)
    │
    ├─ Dashboard Instance 1
    ├─ Dashboard Instance 2
    └─ Dashboard Instance N
```

**Configuration** (nginx):
```nginx
upstream dashboard_backend {
    least_conn;
    server localhost:5001;
    server localhost:5002;
    server localhost:5003;
}

server {
    listen 80;
    location / {
        proxy_pass http://dashboard_backend;
    }
}
```

### Database Scaling

#### Read Replicas

For high-read scenarios:
- Primary database for writes
- Read replicas for queries
- Connection pooling

#### Sharding

For very large datasets:
- Shard by IP address range
- Shard by time period
- Consistent hashing

### Caching Layer

**Redis Integration** (Recommended):
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379)

def get_cached_metrics():
    cached = redis_client.get('metrics')
    if cached:
        return json.loads(cached)
    metrics = collect_metrics()
    redis_client.setex('metrics', 2, json.dumps(metrics))
    return metrics
```

---

## Integration Patterns

### Prometheus Integration

**Metrics Export**:
```python
from prometheus_client import Counter, Gauge, Histogram

# Metrics
ddos_attacks_total = Counter('ddos_attacks_total', 'Total DDoS attacks detected')
blocked_ips_total = Counter('blocked_ips_total', 'Total IPs blocked')
system_cpu = Gauge('system_cpu_percent', 'CPU usage percentage')
prediction_latency = Histogram('prediction_latency_seconds', 'Prediction latency')
```

**Endpoint**:
```python
@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest
    return Response(generate_latest(), media_type="text/plain")
```

### Grafana Integration

**Dashboard Configuration**:
- Import Prometheus as data source
- Create dashboards for:
  - System metrics
  - DDoS attack statistics
  - Predictive maintenance metrics
  - Service health

### External Monitoring Integration

**Health Check Endpoint**:
```python
@app.get("/health")
async def health():
    checks = {
        "database": check_database(),
        "model": check_model(),
        "services": check_services()
    }
    status = "healthy" if all(checks.values()) else "unhealthy"
    return {"status": status, "checks": checks}
```

---

## Development Guide

### Project Structure

```
Heal-X-Bot/
├── model/                 # ML models
│   ├── main.py           # Model API server
│   ├── ddos_detector.py  # DDoS detection
│   └── train_*.py        # Training scripts
├── monitoring/
│   ├── server/           # Monitoring server
│   │   ├── app.py        # Main server
│   │   ├── healing_dashboard_api.py  # Dashboard API
│   │   └── healing/      # Auto-healing
│   └── dashboard/        # Dashboard UI
├── incident-bot/         # Incident response bot
├── config/              # Configuration files
├── docs/                # Documentation
└── tests/               # Test files
```

### Adding New Features

#### 1. Create Feature Module

```python
# monitoring/server/features/new_feature.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/new-feature")

@router.get("/")
async def get_feature():
    return {"feature": "data"}
```

#### 2. Register Router

```python
# monitoring/server/healing_dashboard_api.py
from features.new_feature import router as new_feature_router

app.include_router(new_feature_router)
```

#### 3. Add Tests

```python
# tests/test_new_feature.py
def test_new_feature():
    response = client.get("/api/new-feature/")
    assert response.status_code == 200
```

### Code Style

**Python Style Guide**: PEP 8

**Linting**:
```bash
# Install linter
pip install flake8 black

# Run linter
flake8 .
black .
```

---

## Deployment Strategies

### Single Server Deployment

**Architecture**:
- All services on one server
- SQLite database
- File-based logging
- Simple and cost-effective

**Use Case**: Small to medium deployments

### Docker Deployment

**Architecture**:
- Each service in separate container
- Docker Compose orchestration
- Volume mounts for persistence
- Network isolation

**Use Case**: Development and medium production

### Kubernetes Deployment

**Architecture**:
- Kubernetes pods for each service
- Service discovery
- Auto-scaling
- High availability

**Use Case**: Large-scale production

---

## Monitoring & Observability

### Logging

**Structured Logging**:
```python
import logging
import json

logger = logging.getLogger(__name__)

def log_event(level, message, **kwargs):
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        **kwargs
    }
    logger.log(level, json.dumps(log_data))
```

### Metrics Collection

**Key Metrics**:
- Request latency
- Error rates
- Throughput
- Resource usage
- Model performance

### Distributed Tracing

**Implementation** (Recommended):
- OpenTelemetry integration
- Trace ID propagation
- Span creation for operations

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-19  
**Maintained By**: Heal-X-Bot Development Team

